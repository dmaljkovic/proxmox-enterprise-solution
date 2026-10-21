# ZFS pool layout

The host boots from a ZFS pool of two mirrored NVMe devices. This page
describes what the installer creates, how to verify it, and the three
tuning steps that matter on this hardware.

## Why ZFS

| Property | What it buys on a hypervisor |
|---|---|
| Copy-on-write snapshots | A snapshot of a running virtual machine is instantaneous and takes no extra space until it changes |
| Checksummed data | Silent corruption is detected on read, not discovered months later |
| Compression | `lz4` on the VM store returns roughly 20–30 % of the space for typical workloads, at negligible CPU cost |
| Native checksums and self-healing | A mirror detects a bad sector on one device, reads the correct copy from the other, and repairs the first in place |

The alternative — ext4 or LVM on a software RAID 1 — gives none of these.
For a host whose entire purpose is running nine virtual machines, snapshots
alone justify the choice.

!!! warning "ZFS on top of a hardware RAID is not supported"
    Proxmox is explicit about this, and it is why
    [Rescue mode](01-rescue-mode.md) has to remove Hetzner's software RAID
    before the install. A pool built on a device that hides its own
    redundancy cannot reason about that redundancy: it cannot tell a healthy
    mirror from a degraded one, it cannot schedule a scrub of the underlying
    device, and a device-level failure can take the whole pool down without
    the pool ever reporting it.

## The layout the installer creates

Proxmox 9.2 creates the pool `rpool` and lays it out like this:

```text
rpool                  the mirror over both NVMe devices
├── ROOT               the system datasets
│   └── pve-1          the root filesystem
├── data               the virtual machine store
└── swap               a swap zvol
```

Two entries in `/etc/pve/storage.cfg` come with it:

```text
zfspool: local-zfs
        pool rpool/data
        sparse
        content images,rootdir
```

`local-zfs` is where virtual machine disks and container root filesystems
live. `local` — the directory-backed storage on the root filesystem — is
kept for ISO images and container templates.

The root dataset is a ZFS dataset, not a directory on a partition, which is
what makes host-level snapshots possible.

### ashift

`ashift` is the pool's sector size, expressed as a power of two. Modern NVMe
devices use 4 KiB sectors, so `ashift=12` is correct:

```console
root@pve-01 ~ # zpool get ashift rpool
name: 'rpool'
 property: ashift
 value: 12
```

The installer asks for it in the ZFS options step. The value must be at
least the sector size of the underlying disks, and it cannot be changed
afterwards without recreating the pool. Getting it right at install time is
the whole point of the step.

### Swap

The installer creates `rpool/swap` as a swap zvol. Proxmox's own guidance
is to prefer a physical swap partition over a zvol, because a zvol swap can
block on I/O under memory pressure and push the whole host into a stall.

There is not enough room on two 512 GB drives to have both a generous pool
and a separate swap partition, so the zvol stays. Two mitigations apply:
the pool is a mirror, so a zvol swap does not reduce the redundancy of the
data datasets, and `vm.swappiness` is lowered so the host prefers to page
its own anonymous memory rather than thrash on swap.

## Verifying the pool

Immediately after the install, before anything else is configured:

```console
root@pve-01 ~ # zpool status
  pool: rpool
 state: ONLINE
status: One or more devices could not be opened.  Sufficient replicas exist for
        the pool to continue functioning in a degraded state.
action: Attach the missing device and online it using 'zpool online'.
   scan: scrub repaired 0B in 00:00:00 with 0 errors on Sun ...
 config:

	NAME        STATE     READ WRITE CKSUM
	rpool       ONLINE       0     0     0
	  mirror-0  ONLINE       0     0     0
	    nvme0n1 ONLINE       0     0     0
	    nvme1n1 ONLINE       0     0     0

errors: No known data errors
```

Both devices must be present under `mirror-0` and both must say `ONLINE`.
A pool with only one device in the mirror is not a mirror, and the host
will lose every dataset on it the next time that device fails.

The same information in a wider format:

```console
root@pve-01 ~ # zpool list -v
```

and the datasets with their mount points:

```console
root@pve-01 ~ # zfs list
NAME               USED  AVAIL  REFER  MOUNTPOINT
rpool             4.94G  7.68T    96K  /rpool
rpool/ROOT         702M  7.68T    96K  /rpool/ROOT
rpool/ROOT/pve-1   702M  7.68T   702M  /
rpool/data          96K  7.68T    96K  /rpool/data
rpool/swap        4.25G  7.69T    64K  -
```

The final `zfs list` line — `rpool/swap` with a `-` in the mount point
column — confirms the swap zvol is in place.

## Tuning

### Limit the ARC

The ZFS Adaptive Replacement Cache uses memory to cache dataset data. By
default it is allowed 10 % of the host's memory, clamped at 16 GiB. On a
64 GB host that is 6.4 GiB, which is a reasonable default and is the number
Proxmox writes into `/etc/modprobe.d/zfs.conf` during the install:

```console
root@pve-01 ~ # cat /etc/modprobe.d/zfs.conf
options zfs zfs_arc_max=6871947673
```

Two things share that 64 GB: the ARC and the virtual machines, which ask for
32 GB between them. An ARC that grows to fill the host will evict guest
memory under pressure and make the guests slow for no benefit.

Pinning the ARC to 8 GiB — a quarter of the host — leaves the remaining
memory for the guests and for burst headroom:

```console
root@pve-01 ~ # nano /etc/modprobe.d/zfs.conf
options zfs zfs_arc_max=8589934592
```

The limit only takes effect after a rebuild of the initramfs and a reboot,
because the module parameter is read at load time:

```console
root@pve-01 ~ # update-initramfs -u -k all
root@pve-01 ~ # reboot
```

After the reboot, confirm the running value:

```console
root@pve-01 ~ # cat /sys/module/zfs/parameters/zfs_arc_max
8589934592
```

!!! warning "The ARC minimum has a floor"
    `zfs_arc_min` defaults to 1/32 of RAM, which on 64 GB is 2 GiB. As long
    as `zfs_arc_max` is above that value the two are consistent. Setting a
    maximum *below* the minimum leaves ZFS unable to allocate the minimum
    and it logs an error on every load.

### Lower swappiness

The kernel default of 60 is high for a host that runs a ZFS pool, because
ZFS already manages its own memory pressure:

```console
root@pve-01 ~ # sysctl -w vm.swappiness=10
```

and make it permanent:

```console
root@pve-01 ~ # nano /etc/sysctl.d/99-swappiness.conf
vm.swappiness = 10
```

### Enable TRIM

NVMe drives need periodic TRIM so the controller can reclaim blocks. ZFS
does this on its own for whole-pool TRIM, and the host needs it enabled:

```console
root@pve-01 ~ # nano /etc/modprobe.d/zfs.conf
options zfs zfs_trim_on=auto
```

Rebuild the initramfs and reboot as above if you change this after the
install.

## Scrubbing

Proxmox does not document a scrub schedule for ZFS pools, so this is a
decision the operator has to make rather than a default to accept. A weekly
scrub is the common practice and is what this project uses.

```console
root@pve-01 ~ # zpool scrub rpool
root@pve-01 ~ # zpool status
  pool: rpool
 state: ONLINE
  scan: scrub in progress since Sun Oct 18 03:00:00 2026
	1.21T scanned at 1.2G/s, 1.30T issued at 1.2G/s, 1.30T total
	1.21T scanned, 1.30T issued at 1.2G/s, 1.30T total
	0B repaired, 100.00% done
```

Schedule it with a systemd timer rather than a cron entry, so it survives
the same way the rest of the host configuration does:

```ini
# /etc/systemd/system/zfs-scrub.service
[Unit]
Description=Weekly ZFS scrub

[Service]
Type=oneshot
ExecStart=/usr/sbin/zpool scrub rpool
```

```ini
# /etc/systemd/system/zfs-scrub.timer
[Unit]
Description=Run the ZFS scrub every Sunday at 03:00

[Timer]
OnCalendar=Sun *-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```console
root@pve-01 ~ # systemctl daemon-reload
root@pve-01 ~ # systemctl enable --now zfs-scrub.timer
```

`Persistent=true` matters: it makes the timer catch up after a reboot that
was scheduled during a maintenance window, instead of silently skipping the
scrub.

## Replacing a failed disk

The mirror is what makes a disk failure a scheduled task rather than an
outage. When a device fails, ZFS marks it `FAULTED` and the pool continues
on the surviving member:

```console
root@pve-01 ~ # zpool status
  pool: rpool
 state: DEGRADED
status: One or more devices has experienced an unrecoverable error.
action: Replace the affected device with a new device of the same type.
   scan: scrub repaired 0B in 00:00:00 with 0 errors on Sun ...
 config:

	NAME             STATE     READ WRITE CKSUM
	rpool            DEGRADED      0     0     0
	  mirror-0       DEGRADED      0     0     0
	    nvme0n1      ONLINE       0     0     0
	    nvme1n1      FAULTED      0     0     0

errors: 1 data error(s) in use at the last resync
```

Replace the failed device:

```console
root@pve-01 ~ # zpool replace rpool nvme1n1 /dev/nvme1n1
root@pve-01 ~ # zpool status
```

The resilver runs in the background and the pool returns to `ONLINE` once it
completes. Monitor it with `zpool status`.

!!! note "The bootloader is a separate concern"
    The EFI system partition lives on the disks, and `proxmox-boot-tool`
    manages the boot configuration. After a disk replacement, check that the
    boot configuration is still intact:

    ```console
    root@pve-01 ~ # proxmox-boot-tool status
    ```

    See the [Proxmox wiki on the host bootloader](https://pve.proxmox.com/pve-docs/chapter-sysadmin.html#sysboot)
    for the full procedure.

## Checklist

- [ ] `zpool status` shows `rpool` `ONLINE` with both NVMe devices in `mirror-0`
- [ ] `zpool get ashift rpool` returns `12`
- [ ] `zfs list` shows `rpool/data`, `rpool/ROOT/pve-1` and `rpool/swap`
- [ ] `zfs_arc_max` set to 8 GiB in `/etc/modprobe.d/zfs.conf`
- [ ] `update-initramfs -u -k all` run after changing the module options
- [ ] `vm.swappiness` set to 10 in `/etc/sysctl.d/99-swappiness.conf`
- [ ] `zfs-scrub.timer` enabled and listed in `systemctl list-timers`

## Related pages

- [Rescue mode](01-rescue-mode.md)
- [Proxmox VE installation](03-proxmox-installation.md)
- [Backup strategy](../04-security/05-backup-strategy.md)
