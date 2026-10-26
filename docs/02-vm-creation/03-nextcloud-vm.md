# Nextcloud VM Creation (VM-102)

Brief description: Create VM-102 for Nextcloud with 2 vCPU, 6GB RAM, and 50GB storage.

## VM Specifications

- **VM ID**: 102
- **Name**: nextcloud
- **CPU**: 2 vCPU
- **RAM**: 6 GiB (6144 MiB)
- **Disk**: 50 GiB (ZFS)
- **OS**: Ubuntu Server 24.04 LTS
- **Network**: vmbr2 (private internal network)
- **Static IP**: 10.0.0.102/24
- **Gateway**: 10.0.0.5
- **Purpose**: Nextcloud file sync and share

## Prerequisites

- [ ] Proxmox Web UI accessible
- [ ] Ubuntu 24.04 LTS ISO available
- [ ] ZFS storage pool available
- [ ] IP address planned from overview

## Step-by-Step Instructions

### Step 1: Create VM in Proxmox

1. In Proxmox Web UI, select your node
2. Click **Create VM** button

### Step 2: General Tab

- **VM ID**: 102
- **Name**: nextcloud

Click **Next**

### Step 3: OS Tab

- **ISO image**: ubuntu-24.04-live-server-amd64.iso
- **Type**: Linux
- **Version**: 6.x - 2.6 Kernel

Click **Next**

### Step 4: System Tab

- **Graphic card**: Default
- **SCSI Controller**: VirtIO SCSI
- Accept other defaults

Click **Next**

### Step 5: Disks Tab

- **Storage**: rpool
- **Disk size (GiB)**: 50
- **Format**: qcow2
- **Cache**: Write back

!!! tip "Storage Consideration"
    Nextcloud requires more storage than other VMs because user files will be stored here. 50GB provides room for initial use and growth.

Click **Next**

### Step 6: CPU Tab

- **Sockets**: 1
- **Cores**: 2

Click **Next**

### Step 7: Memory Tab

- **Memory (MiB)**: 6146
- **Ballooning Device**: Optional

!!! note "Memory Requirements"
    Nextcloud benefits from extra RAM for file caching and database operations. 6GB provides good performance for 10-50 users.

Click **Next**

### Step 8: Network Tab

- **Bridge**: vmbr2
- **Model**: VirtIO (paravirtualized)

Click **Next**

!!! note "vmbr2 Configuration"
    This VM uses the internal private network (vmbr2) with NAT. The Nginx Proxy will handle external access to Nextcloud.

### Step 9: Confirm

Review settings:
- Name: nextcloud
- VM ID: 102
- CPU: 2 cores
- Memory: 6144 MiB
- Disk: 50 GiB on rpool

Click **Finish**

### Step 10: Install Ubuntu

1. Start VM 102
2. Open Console
3. Boot from ISO

### Step 11: Ubuntu Installation Wizard

**Language**: English

**Keyboard Layout**: Your layout

**Network Configuration**:
- Select the network interface (ens18)
- Choose **Configure network manually**
- Enter the following:
  - **IP Address**: 10.0.0.102
  - **Netmask**: 255.255.255.0 (/24)
  - **Gateway**: 10.0.0.5
  - **Name servers**: 8.8.8.8, 1.1.1.1

**Proxy**: (none)

**Mirror**: Default

**Storage**:
- Use entire disk
- Accept defaults

**Profile**:
- Your name: Administrator
- Server name: nextcloud
- Username: admin
- Password: <password>
- Confirm password

**SSH**:
- [x] Install OpenSSH server

**Server Snaps**:
- Select **nextcloud** snap for easy installation (recommended)
- Or skip and install manually (see [Nextcloud Installation](../03-software/02-nextcloud.md))

**Complete** and reboot

### Step 12: Post-Installation

After reboot:

1. Login as your user
2. Check IP address:
   ```bash
   ip addr show
   ```
3. Verify gateway:
   ```bash
   ip route show
   ```
4. Verify connectivity:
   ```bash
   ping google.com
   ```
5. Update system:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

### Step 13: Record IP Address

!!! important "Update IP Inventory"
    The static IP 10.0.0.102 has been configured. Add to your documentation:
    ```
    nextcloud | 102 | vmbr2 | 10.0.0.102 | cloud.example.com | Nextcloud Port 80/443
    ```

## Verification

- [ ] VM 102 created with correct specs
- [ ] Ubuntu 24.04 LTS installed
- [ ] Console access working
- [ ] IP address assigned
- [ ] Internet connectivity verified
- [ ] System packages updated
- [ ] IP address documented

## Optimization for Nextcloud

### Create Additional Storage (Optional)

If you want to separate Nextcloud data:

1. In Proxmox, add additional disk to VM 102:
   - Hardware → Add → Hard Disk
   - Storage: rpool
   - Size: 100GB or more
   - Format: qcow2

2. In VM, format and mount:
   ```bash
   # Find new disk (likely /dev/sdb)
   lsblk
   
   # Format
   sudo mkfs.ext4 /dev/sdb
   
   # Create mount point
   sudo mkdir /mnt/nextcloud-data
   
   # Mount
   sudo mount /dev/sdb /mnt/nextcloud-data
   
   # Add to fstab
   echo '/dev/sdb /mnt/nextcloud-data ext4 defaults 0 2' | sudo tee -a /etc/fstab
   ```

### Enable Swap (Optional)

For systems with limited RAM:

```bash
# Create 2GB swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Add to fstab
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## Next Steps

Proceed to:
- [Nginx Proxy VM](04-nginx-proxy-vm.md) - VM-103
- Or continue with [Nextcloud Installation](../03-software/02-nextcloud.md)
