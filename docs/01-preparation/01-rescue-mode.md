# Rescue mode

Three different rescue environments exist in this stack. They are not
interchangeable, and confusing them is the single most common cause of a
server that cannot be reached.

| Environment | Where it runs | What it is for |
|---|---|---|
| **Hetzner Rescue System** | A Debian live environment booted over the network, running entirely in RAM | Preparing the disks before the install; running the Proxmox installer under QEMU; reaching a host that does not boot |
| **Proxmox: Rescue Boot** | The Proxmox ISO boot menu | Booting an *existing* installation using the ISO's kernel, when the bootloader is broken |
| **Proxmox: Debug Mode** | The Proxmox ISO boot menu | A live Linux with all tools available, for repairing a degraded ZFS pool or the bootloader |

!!! danger "The Hetzner Rescue System does not touch the disks"
    It boots over PXE and runs from RAM. The activation is valid for **one
    boot** and expires **60 minutes** after it is requested. Neither fact is
    a problem, but both are surprising if you did not expect them.

## Choosing an environment

| Situation | Use |
|---|---|
| The server is new and its disks still carry Hetzner's software RAID | Hetzner Rescue System |
| The Proxmox installer has to run | Hetzner Rescue System, with QEMU — see [Proxmox VE installation](03-proxmox-installation.md) |
| The host booted but has no network, or the ZFS pool did not import | Hetzner Rescue System, or Proxmox Debug Mode |
| The bootloader is broken but the data is intact | Proxmox Rescue Boot, or the Hetzner Rescue System |
| A ZFS pool is degraded and needs a scrub or a resilver | Proxmox Debug Mode |

## Activating the Hetzner Rescue System

1. In Robot, open the server and go to the **Rescue** tab.
2. Choose **Rescue System** and press **Activate rescue system**.
3. Copy the temporary root password that Robot displays. It is valid for this
   boot only.
4. **Reboot the server.** The activation does not interrupt the running
   system — it only schedules the next boot.
5. Connect over SSH:

    ```console
    $ ssh root@203.0.113.10
    ```

The login banner identifies the environment, so confirm you are where you
think you are:

```console
root@rescue ~ # cat /etc/issue
Debian GNU/Linux 12 (bookworm) \n \l rescue
```

If the machine still boots the installed system instead, the rescue
activation was not scheduled — return to Robot and repeat step 4.

## Surveying the hardware

Do this before changing anything. Every decision in the rest of this phase
depends on what these commands print.

```console
# The block devices, their sizes and their connection type
root@rescue ~ # lsblk -o NAME,SIZE,TYPE,MODEL,TRAN

# Any Linux software RAID that Hetzner pre-configured
root@rescue ~ # cat /proc/mdstat

# Any ZFS pool left over from a previous installation
root@rescue ~ # zpool status
zpool: no pools available

# The physical uplink and its MAC address
root@rescue ~ # ip -br link
lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>
enp34s0          UP             00:00:00:00:00:00 <BROADCAST,MULTICAST,UP,LOWER_UP>

# The firmware mode, which decides how the installer is booted
root@rescue ~ # [ -d /sys/firmware/efi ] && echo UEFI || echo Legacy
UEFI
```

!!! warning "Record the uplink name now"
    `enp34s0` above is the name the *hardware* uses. The Proxmox installer
    running under QEMU sees a different, virtualised name for the same
    adapter, and writes that name into the configuration it leaves behind.
    This is the cause of the failure described in
    [Recovering from rescue mode](05-recover-from-rescue.md), and it is much
    cheaper to record the name here than to repair it later.

## Removing Hetzner's software RAID

!!! warning "This is the decision that cannot be undone casually"
    A server ordered with two drives **and** an operating system is
    pre-configured with a Linux software RAID 1 across both disks. The
    installer then sees a single block device, not two.

    ZFS cannot see through a software RAID. A pool built on top of one has
    no redundancy as far as ZFS is concerned, no ability to scrub the
    underlying device, and no self-healing — the redundancy exists one layer
    down, where ZFS cannot reason about it.

The archive server for this project wants a **real** ZFS mirror over both
NVMe devices. That means the software RAID has to go.

Check for it first:

```console
root@rescue ~ # cat /proc/mdstat
Personalities : [raid1]
md0 : active raid1 nvme0n1p1[0] nvme1n1p1[1]
      1046528 blocks super 1.2 [2/2] [UU]
...
```

If the output lists no arrays, there is nothing to remove — Hetzner has not
configured any, and the drives are already raw. Continue.

If arrays are present, stop them and wipe their metadata. This destroys all
data on both drives, which is acceptable on a server that has never been
used, and unacceptable on anything else:

```console
root@rescue ~ # mdadm --stop --scan
root@rescue ~ # mdadm --zero-superblock --scan
mdadm: zeroing superblock on /dev/nvme0n1 ...
mdadm: zeroing superblock on /dev/nvme1n1 ...
```

Verify that the drives are now plain and empty:

```console
root@rescue ~ # cat /proc/mdstat
Personalities : [raid1]
unused devices: <none>

root@rescue ~ # lsblk -o NAME,SIZE,TYPE,MODEL
NAME        SIZE TYPE MODEL
nvme0n1   476.9G disk Samsung SSD 980 PRO 512GB
nvme1n1   476.9G disk Samsung SSD 980 PRO 512GB
```

Two independent 477 GB devices. That is the shape the rest of this phase
assumes.

!!! note "You do not need this for the ISO method"
    The ISO method in [Proxmox VE installation](03-proxmox-installation.md)
    passes both drives to the installer directly. The RAID has to be gone in
    either case, but the removal is what makes the mirror possible rather
    than merely tidy.

## Booting the Proxmox installer

Hetzner dedicated servers **cannot boot an arbitrary ISO** on their own. The
boot order is fixed to the internal drives and the network. Three workarounds
exist, and they are not equally good.

| Method | Needs | ZFS root | Sees real hardware |
|---|---|---|---|
| **A — KVM Virtual Media** | The "Remote console / KVM" add-on, requested free of charge from Robot support; an SMB share holding the ISO | Yes | Yes |
| **B — QEMU in the Rescue System** | Nothing beyond SSH | Yes | Only the disks and the NIC are passed through |
| **C — Debian, then upgrade to Proxmox** | Nothing beyond SSH | No, the root stays on ext4/LVM | Yes |

**Method A** is the cleanest. The installer runs on the real machine, sees
the real NIC under its real name, and sees the real NVMe devices. The costs
are a support request and an ISO mount over SMB, which is slow but only has
to happen once.

**Method B** is the fallback when the KVM add-on is not available. QEMU runs
inside the Rescue System with the two NVMe drives passed through as raw
block devices and the installer ISO attached as a CD-ROM. It is fully
scriptable and needs no KVM. Its one real drawback is the network interface
name, described below.

**Method C** is the simplest of all — `installimage` with Debian 13, then
the official Debian-to-Proxmox upgrade. It produces a working Proxmox node
with the real interface names and no virtualisation anywhere. What it does
**not** produce is a ZFS root: the root filesystem stays on ext4/LVM, and
the ZFS pool becomes a data pool for virtual machines rather than the pool
the system boots from. Snapshots of the host filesystem are then unavailable.

!!! tip "Method B and the interface name"
    Under QEMU the guest sees a virtio network adapter, and the installer
    writes its predictable name — typically `enp0s31f6` — into
    `/etc/network/interfaces`. After the physical reboot that file names an
    interface that does not exist on the hardware, and the host comes up with
    no network at all.

    `predict-check` shows the mapping between the old and the new name:

    ```console
    root@rescue ~ # predict-check
    eth0 -> enp0s31f6
    ```

    Two ways to avoid the problem:

    - Install with the answer file and interface pinning, which
      `proxmox-auto-install-assistant` supports. See
      [Proxmox VE installation](03-proxmox-installation.md).
    - Fix `/etc/network/interfaces` from the Rescue System before the first
      physical reboot. See
      [Recovering from rescue mode](05-recover-from-rescue.md).

    Both are covered there in full.

## Checklist

- [ ] Rescue System activated in Robot, temporary password saved
- [ ] Server rebooted into the Rescue System, SSH access confirmed
- [ ] `lsblk` shows the expected block devices
- [ ] `cat /proc/mdstat` checked; software RAID removed if present
- [ ] `lsblk` confirms two independent NVMe devices
- [ ] Physical uplink name and MAC recorded
- [ ] Firmware mode recorded (`UEFI` or `Legacy`)

## Related pages

- [ZFS pool layout](02-zfs-pool.md)
- [Proxmox VE installation](03-proxmox-installation.md)
- [Network configuration](04-network-configuration.md)
- [Recovering from rescue mode](05-recover-from-rescue.md)
