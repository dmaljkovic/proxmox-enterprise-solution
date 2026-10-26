# Proxmox Installation (QEMU Method)

Brief description: Install Proxmox VE on your Hetzner server using the QEMU-based ISO installation method from rescue mode.

## What You'll Learn

- How to boot Proxmox installer in a virtual machine from rescue mode
- How to pass NVMe drives through to the installer
- How to access the installer via VNC
- How to configure Proxmox with ZFS during installation

## Prerequisites

- [ ] Rescue mode activated and SSH connected
- [ ] Both NVMe devices identified (`/dev/nvme0n1` and `/dev/nvme1n1`)
- [ ] VNC client installed on your local machine
- [ ] At least 4GB free space for ISO download

## Estimated Time

45-60 minutes

!!! warning "Data Destruction Warning"
    This installation will erase all data on your NVMe drives. Ensure you have no important data. This is a fresh server setup.

## Step-by-Step Instructions

### Step 1: Check Boot Mode (UEFI/BIOS)

Determine if your server uses UEFI or legacy BIOS:

```bash
[ -d "/sys/firmware/efi" ] && echo "UEFI" || echo "BIOS"
```

Note the result - you'll need it for the QEMU commands.

### Step 2: Forward VNC Port

Forward a local port to access the virtual machine's VNC console:

```bash
ssh -L 5900:localhost:5900 root@<your-server-ip>
```

Keep this SSH session open during the entire installation process.

### Step 3: Download Proxmox VE ISO

Download the Proxmox VE ISO from the official source:

```bash
cd /tmp
wget https://enterprise.proxmox.com/iso/proxmox-ve_9.0-1.iso
```

Verify the download:

```bash
ls -lh proxmox-ve_9.0-1.iso
```

Expected size: ~1.1GB

### Step 4: Start Proxmox Installer in QEMU

Start a virtual machine with the Proxmox ISO and pass your NVMe drives through:

#### UEFI Mode (with OVMF BIOS)

```bash
qemu-system-x86_64 \
  -enable-kvm \
  -bios /usr/share/ovmf/OVMF.fd \
  -k en-us \
  -cpu host \
  -smp 4 \
  -m 4096 \
  -boot d \
  -cdrom ./pve.iso \
  -drive file=/dev/nvme0n1,format=raw,media=disk,if=virtio \
  -drive file=/dev/nvme1n1,format=raw,media=disk,if=virtio \
  -vnc :0
```

#### Legacy BIOS Mode (without OVMF)

```bash
qemu-system-x86_64 \
  -enable-kvm \
  -k en-us \
  -cpu host \
  -smp 4 \
  -m 4096 \
  -boot d \
  -cdrom ./pve.iso \
  -drive file=/dev/nvme0n1,format=raw,media=disk,if=virtio \
  -drive file=/dev/nvme1n1,format=raw,media=disk,if=virtio \
  -vnc :0
```

!!! note "Drive Naming"
    If you have SATA drives instead of NVMe, use `/dev/sda` and `/dev/sdb` instead of `/dev/nvme0n1` and `/dev/nvme1n1`.

### Step 5: Connect via VNC

Connect your VNC client to:

```
127.0.0.1:5900
```

You should see the Proxmox installer boot menu.

!!! caution "VNC Timeout"
    The VNC connection may timeout after you press "Install". Simply reconnect to `127.0.0.1:5900` if this happens.

### Step 6: Complete Proxmox Installation

Follow the on-screen installer steps:

1. Select **"Install Proxmox VE"**
2. Choose your target disks (both NVMe drives should be visible)
3. Select **"ZFS - RAID1"** for the filesystem (the installer handles ZFS setup)
4. Configure:
   - Location/Timezone
   - Password
   - Network (temporary - we'll configure properly later)
5. Wait for installation to complete

### Step 7: Stop QEMU and Prepare for Boot

Once installation shows "Finished", stop QEMU by pressing `Ctrl+C` in your SSH terminal.

Before rebooting the server, you need to identify the correct network interface name.

### Step 8: Identify Network Interface Name

Run the predict-check command to find the actual interface name:

```bash
predict-check
```

Example output:
```
eth0 -> enp0s31f6
```

In this example, `enp0s31f6` is the true interface name.

Check the current network configuration in rescue mode:

```bash
netdata
```

Example output:
```
Network data:
   eth0  LINK: yes
         MAC:  aa:bb:cc:dd:cc:ff
         IP:   10.0.0.100/24
         IPv6: (none)
         Intel(R) PRO/1000 Network Driver
```

Note the MAC address and IP configuration.

### Step 9: Boot into Proxmox

Start Proxmox without the ISO to boot from the installed system:

#### UEFI Mode (with OVMF BIOS)

```bash
qemu-system-x86_64 \
  -enable-kvm \
  -bios /usr/share/ovmf/OVMF.fd \
  -cpu host \
  -k en-us \
  -device virtio-net,netdev=net0 \
  -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2222-:22 \
  -smp 4 \
  -m 4096 \
  -drive file=/dev/nvme0n1,format=raw,media=disk,if=virtio \
  -drive file=/dev/nvme1n1,format=raw,media=disk,if=virtio \
  -vnc :0
```

#### Legacy BIOS Mode (without OVMF)

```bash
qemu-system-x86_64 \
  -enable-kvm \
  -cpu host \
  -k en-us \
  -device virtio-net,netdev=net0 \
  -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2222-:22 \
  -smp 4 \
  -m 4096 \
  -drive file=/dev/nvme0n1,format=raw,media=disk,if=virtio \
  -drive file=/dev/nvme1n1,format=raw,media=disk,if=virtio \
  -vnc :0
```

This command includes network forwarding, allowing SSH access to the VM via `ssh -p 2222 root@127.0.0.1`.

### Step 10: Configure Network

Connect via VNC again. Log in to the Proxmox console and edit the network configuration:

```bash
nano /etc/network/interfaces
```

Adjust the interface name to match what you found in Step 8. See [Network Configuration](03-network-configuration.md) for the complete network setup.

### Step 11: Reboot into Production

Power cycle the server or use the Proxmox console to reboot:

```bash
reboot
```

Your SSH session will disconnect. The server will boot directly into Proxmox.

### Step 12: Access Proxmox Web UI

After 5 minutes, access the Proxmox Web UI:

```
https://<your-server-ip>:8006
```

!!! danger "SSL Certificate Warning"
    You will see a browser warning about an untrusted certificate. This is normal. Click "Advanced" and proceed.

Login credentials:
- **Username**: root
- **Password**: (set during installation)

## Verification

- [ ] Proxmox VE ISO downloaded successfully
- [ ] QEMU virtual machine started with NVMe drives passed through
- [ ] VNC connection established to installer
- [ ] Proxmox installed on ZFS RAID1
- [ ] Network interface configured correctly
- [ ] Web UI accessible on port 8006
- [ ] Successfully logged in as root

## Next Steps

Proceed to [Network Configuration](03-network-configuration.md) to configure your network setup.
