# Recovering from rescue mode

The procedure for a host whose network configuration was lost after a ZFS
pool import, and the general repair path for a Proxmox installation that
will not boot.

## The failure this addresses

After a Proxmox installation under QEMU, the host reboots into the physical
hardware and has no network. The cause is almost always the interface name:

- The installer ran on a virtual machine and wrote the virtio adapter's
  predictable name — typically `enp0s31f6` — into
  `/etc/network/interfaces`.
- The physical NIC on the hardware is called something else.
- The host boots, the bridge comes up with a port that does not exist, and
  the address is configured on a network with no carrier.

The symptom is a host that answers nothing at all: no SSH, no web
interface, no ping.

## Choosing the environment

| Situation | Environment |
|---|---|
| The host boots but has no network | Hetzner Rescue System |
| The host does not boot at all | Proxmox **Debug Mode** from the ISO |
| The bootloader is broken, the data is fine | Proxmox **Rescue Boot** from the ISO |

The Hetzner Rescue System is the right choice for the first case, because
it has a full Debian userland and a working network stack — it can reach
the machine over SSH while the installed system cannot.

## Procedure

### Step 1 — Activate the rescue system

In Robot, open the server, go to the **Rescue** tab, activate the Rescue
System, and reboot. The activation is valid for one boot and expires after
60 minutes.

```console
root@rescue ~ # cat /etc/issue
Debian GNU/Linux 12 (bookworm) \n \l rescue
```

### Step 2 — Import the pool without mounting it

Export anything that is already imported, so the import below starts from a
known state:

```console
root@rescue ~ # zpool export rpool 2>/dev/null
```

Import the pool with `-N`, which imports it **without mounting any
dataset**:

```console
root@rescue ~ # zpool import -f -N rpool
   pool: rpool
     id: 1
  status: The pool is cleanly imported.
   scan: scrub repaired 0B in 00:00:00 with 0 errors on ...
  config:

	NAME        STATE     READ WRITE CKSUM
	rpool       ONLINE       0     0     0
	  mirror-0  ONLINE       0     0     0
	    nvme0n1 ONLINE       0     0     0
	    nvme1n1 ONLINE       0     0     0
```

!!! tip "Why `-N` matters"
    Without `-N`, importing mounts the datasets at their recorded
    mountpoints. On a system whose root filesystem is the dataset you are
    trying to repair, that is exactly the wrong thing: the rescue
    system's own root gets shadowed and the shell disappears. `-N` imports
    the pool and leaves every dataset unmounted, so nothing can go wrong.

    The `-f` flag is needed when the pool was not cleanly exported — after
    a hard reset, which is the common case.

### Step 3 — Find the real root dataset

```console
root@rescue ~ # zfs list
NAME               USED  AVAIL  REFER  MOUNTPOINT
rpool             4.94G  7.68T    96K  -
rpool/ROOT         702M  7.68T    96K  -
rpool/ROOT/pve-1   702M  7.68T   702M  -
rpool/data          96K  7.68T    96K  -
rpool/swap        4.25G  7.69T    64K  -
```

The dataset that holds the operating system is the one whose name contains
the node name — `rpool/ROOT/pve-1` for a host called `pve-01`. Confirm it
is the right one by checking its size: it should be several hundred
megabytes, matching what the root filesystem used.

### Step 4 — Mount it

Mount it at a temporary path, **without changing the mountpoint property**:

```console
root@rescue ~ # zfs mount -o mountpoint=/mnt rpool/ROOT/pve-1
```

!!! danger "`zfs set mountpoint=` changes the pool permanently"
    The tempting shortcut is `zfs set mountpoint=/mnt rpool/ROOT/pve-1`
    followed by `zfs mount`. The first command **writes the property into
    the pool**, and it stays that way. The next time the pool imports — on
    the next boot — the root dataset mounts at `/mnt` instead of `/`, and
    the host does not come up.

    `zfs mount -o mountpoint=/mnt` changes nothing about the dataset. It is
    a mount-time override and it disappears when the dataset is unmounted.

Check that the right thing got mounted:

```console
root@rescue ~ # ls /mnt
bin  boot  dev  etc  home  lib  lib64  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var
```

`bin`, `boot`, `etc`, `lib`, `root`, `sbin`, `usr` and `var` must be
present. If they are not, stop — the wrong dataset was mounted.

### Step 5 — Find the real interface name

This has to be done **outside** the mounted root, because the rescue
system's own interfaces are not the installed system's:

```console
root@rescue ~ # ip -br link
lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>
enp34s0          UP             00:00:00:00:00:00 <BROADCAST,MULTICAST,UP,LOWER_UP>
```

The interface with `UP` and a MAC address is the uplink. Write it down.

### Step 6 — Edit the real network configuration

```console
root@rescue ~ # nano /mnt/etc/network/interfaces
```

Replace its contents with the configuration from
[Network configuration](04-network-configuration.md), using the interface
name from step 5:

```text
auto lo
iface lo inet loopback

iface enp34s0 inet manual

auto vmbr0
iface vmbr0 inet static
        address 203.0.113.10/26
        gateway 203.0.113.1
        bridge-ports enp34s0
        bridge-stp off
        bridge-fd 0

auto vmbr2
iface vmbr2 inet static
        address 10.0.0.5/24
        bridge-ports none
        bridge-stp off
        bridge-fd 0

        post-up   echo 1 > /proc/sys/net/ipv4/ip_forward
        post-up   iptables -t nat -A POSTROUTING -s '10.0.0.0/24' -o vmbr0 -j MASQUERADE
        post-down iptables -t nat -D POSTROUTING -s '10.0.0.0/24' -o vmbr0 -j MASQUERADE
```

!!! tip "If the file is empty"
    Some installations keep the bridge configuration in a drop-in
    directory instead:

    ```console
    root@rescue ~ # ls -la /mnt/etc/network/
    root@rescue ~ # ls -la /mnt/etc/network/interfaces.d/
    ```

    Proxmox normally writes the bridges directly into
    `/etc/network/interfaces`, so an empty file there means the
    configuration was lost rather than relocated.

### Step 7 — Clean up and reboot

Unmount the dataset, export the pool, and let the host boot on its own:

```console
root@rescue ~ # zfs unmount /mnt
root@rescue ~ # zpool export rpool
```

Disable the rescue activation in Robot — it is valid for one boot only, but
leaving it armed means the next reboot lands in the rescue system instead
of Proxmox.

```console
root@rescue ~ # reboot
```

!!! warning "One command in the initramfs may still be needed"
    If the pool was created by a different installation than the one now
    booting it, the `hostid` in the pool does not match the `hostid` of the
    new boot loader, and the host stops at the initramfs with a message
    about the pool refusing to import.

    Boot into the initramfs and import the pool once, explicitly:

    ```console
    # At the initramfs prompt
    zpool import -f rpool
    zpool export rpool
    ```

    The initramfs then writes the correct `hostid` and the next boot works
    normally. This is documented in the
    [Proxmox wiki on recovering from a bootloader failure](https://pve.proxmox.com/wiki/Recover_From_Grub_Failure).

## The full repair path

When more than the network file is broken — the bootloader, or a degraded
pool — the configuration has to be edited inside the installed system
rather than on a single mounted dataset.

The Proxmox wiki documents this as the standard procedure:

```console
root@rescue ~ # mkdir -p /media/RESCUE
root@rescue ~ # zpool import -f -R /media/RESCUE rpool
root@rescue ~ # mount -o rbind /proc /media/RESCUE/proc
root@rescue ~ # mount -o rbind /sys  /media/RESCUE/sys
root@rescue ~ # mount -o rbind /dev  /media/RESCUE/dev
root@rescue ~ # mount -o rbind /run  /media/RESCUE/run
root@rescue ~ # chroot /media/RESCUE
```

Inside the chroot the installed system is available at its own paths:

```console
root@rescue:/# nano /etc/network/interfaces
root@rescue:/# proxmox-boot-tool status
root@rescue:/# apt update && apt full-upgrade
```

Leave the chroot and shut down cleanly, so the pool is exported properly:

```console
root@rescue:/# exit
root@rescue ~ # zpool export rpool
root@rescue ~ # reboot
```

!!! note "The `-R` flag replaces the manual mount"
    `zpool import -f -R /media/RESCUE rpool` imports the pool and sets the
    alternate root, which mounts every dataset beneath `/media/RESCUE` with
    the correct relative paths. It needs ZFS 2.1.3 or newer, which Proxmox
    9.2 has. It is simpler and less error-prone than mounting each dataset
    by hand.

## Verifying the recovery

After the reboot, from outside:

```console
$ ping -c 3 203.0.113.10
$ ssh root@203.0.113.10
```

On the host:

```console
root@pve-01:~# ip -br addr
lo               UNKNOWN        127.0.0.1/8 ::1/128
enp34s0          UP             <no address>
vmbr0            UP             203.0.113.10/26
vmbr2            UP             10.0.0.5/24

root@pve-01:~# zpool status
  pool: rpool
 state: ONLINE
```

If `zpool status` reports the pool as `DEGRADED` or `FAULTED`, the repair
did not finish — go back to [ZFS pool layout](02-zfs-pool.md) for the disk
replacement procedure.

## Checklist

- [ ] Rescue System activated in Robot, and disabled again after the repair
- [ ] `zpool import -f -N rpool` used, with `-N`
- [ ] `rpool/ROOT/pve-1` confirmed as the root dataset
- [ ] `zfs mount -o mountpoint=/mnt` used, not `zfs set mountpoint=`
- [ ] The real uplink name confirmed with `ip -br link` from the rescue system
- [ ] `/etc/network/interfaces` rewritten with the correct interface name
- [ ] Dataset unmounted and the pool exported before rebooting
- [ ] `ip_forward` present in the configuration
- [ ] Host reachable over SSH after the reboot

## Related pages

- [Rescue mode](01-rescue-mode.md)
- [ZFS pool layout](02-zfs-pool.md)
- [Proxmox VE installation](03-proxmox-installation.md)
- [Network configuration](04-network-configuration.md)
