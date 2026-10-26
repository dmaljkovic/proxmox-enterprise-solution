# Rescue Mode and Initial Access

Brief description: Access your Hetzner server in rescue mode to prepare for Proxmox installation.

## What You'll Learn

- How to activate rescue mode in Hetzner Robot
- How to SSH into the rescue environment
- How to identify NVMe storage devices

## Prerequisites

- [ ] Hetzner EX44 server ordered and delivered
- [ ] Access to Hetzner Robot portal (https://robot.hetzner.com)
- [ ] SSH client installed on your local machine
- [ ] Server IP address from Hetzner

## Estimated Time

30-45 minutes

## Step-by-Step Instructions

### Step 1: Access Hetzner Robot Portal

1. Open your web browser
2. Navigate to https://robot.hetzner.com
3. Log in with your credentials
4. Click on your server in the server list

### Step 2: Activate Rescue Mode

1. Click the **"Rescue"** tab in the server details
2. Select **"Linux 64-bit"** from the operating system dropdown
3. Click **"Activate rescue mode"** button
4. A root password will be displayed - copy this to a secure location
5. Click **"Send CTRL+ALT+DEL to reset"** or power cycle the server
6. Wait 2-3 minutes for the server to boot into rescue mode

### Step 3: SSH into Rescue Mode

Open your terminal and connect:

```bash
ssh root@<your-server-ip>
```

When prompted for password, enter the rescue password from Step 2.

You should see output similar to:
```
Rescue System 6.0.1
root@rescue ~ #
```

### Step 4: Verify NVMe Devices

List available storage devices:

```bash
lsblk
```

Expected output:
```
NAME        MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
nvme0n1     259:0    0 476.9G  0 disk 
nvme1n1     259:1    0 476.9G  0 disk
```

Verify device details:

```bash
fdisk -l | grep nvme
```

Expected output:
```
Disk /dev/nvme0n1: 476.94 GiB, 512110190592 bytes, 1000215216 sectors
Disk /dev/nvme1n1: 476.94 GiB, 512110190592 bytes, 1000215216 sectors
```

!!! warning "Device Verification"
    Ensure you see exactly two NVMe devices (`/dev/nvme0n1` and `/dev/nvme1n1`) before proceeding. If you see different devices, stop and verify your server configuration.

### Step 5: Update Rescue System

Update package lists:

```bash
apt update
```

Install essential tools:

```bash
apt install -y wget curl vim
```

## Verification

- [ ] Successfully accessed Hetzner Robot portal
- [ ] Rescue mode activated successfully
- [ ] SSH connection established to rescue environment
- [ ] Both NVMe devices identified (`/dev/nvme0n1` and `/dev/nvme1n1`)
- [ ] Rescue system updated

## Next Steps

Proceed to [ZFS Setup](02-proxmox-installation.md) to create your storage pool.
