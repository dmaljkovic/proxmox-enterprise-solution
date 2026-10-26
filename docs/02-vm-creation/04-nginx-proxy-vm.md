# Nginx Proxy VM Creation (VM-103)

Brief description: Create VM-103 for Nginx reverse proxy with 1 vCPU, 2GB RAM, and 10GB storage.

## VM Specifications

- **VM ID**: 103
- **Name**: nginx-proxy
- **CPU**: 1 vCPU
- **RAM**: 2 GiB
- **Disk**: 10 GiB (ZFS)
- **OS**: Ubuntu Server 24.04 LTS
- **Network**: vmbr2 (private internal network with port forwarding)
- **Static IP**: 10.0.0.20/24
- **Gateway**: 10.0.0.5
- **Purpose**: Reverse proxy and SSL termination

## Prerequisites

- [ ] Proxmox Web UI accessible
- [ ] Ubuntu 24.04 LTS ISO available
- [ ] ZFS storage pool available
- [ ] IP address planned

## Step-by-Step Instructions

### Step 1: Create VM in Proxmox

1. Click **Create VM** in Proxmox UI

### Step 2: General Tab

- **VM ID**: 103
- **Name**: nginx-proxy

Click **Next**

### Step 3: OS Tab

- **ISO image**: ubuntu-24.04-live-server-amd64.iso
- **Type**: Linux
- **Version**: 6.x - 2.6 Kernel

Click **Next**

### Step 4: System Tab

Accept defaults

Click **Next**

### Step 5: Disks Tab

- **Storage**: rpool
- **Disk size (GiB)**: 10
- **Format**: qcow2
- **Cache**: Write back

!!! note "Minimal Storage"
    Nginx proxy requires minimal storage as it only handles configuration files and certificates. 10GB is sufficient.

Click **Next**

### Step 6: CPU Tab

- **Sockets**: 1
- **Cores**: 1

Click **Next**

### Step 7: Memory Tab

- **Memory (MiB)**: 2048

Click **Next**

### Step 8: Network Tab

- **Bridge**: vmbr2 (private internal network)
- **Model**: VirtIO

Click **Next**

!!! note "vmbr2 Configuration with Port Forwarding"
    This VM uses the internal private network (vmbr2). Port forwarding from vmbr0 (host) will forward ports 80/443 to this VM. See [Network Configuration](../01-preparation/03-network-configuration.md) for the iptables rules.

### Step 9: Confirm

Review:
- Name: nginx-proxy
- VM ID: 103
- CPU: 1 core
- Memory: 2048 MiB
- Disk: 10 GiB

Click **Finish**

### Step 10: Install Ubuntu

1. Start VM 103
2. Open Console
3. Boot from ISO
4. Follow installation wizard:

**Language**: English

**Keyboard Layout**: Your layout

**Network Configuration**:
- Select the network interface (ens18)
- Choose **Configure network manually**
- Enter:
  - **IP Address**: 10.0.0.20
  - **Netmask**: 255.255.255.0 (/24)
  - **Gateway**: 10.0.0.5
  - **Name servers**: 8.8.8.8, 1.1.1.1

**Profile**:
- Server name: nginx-proxy
- Username: admin
- Password: <password>

**SSH**: Install OpenSSH server

**Complete** and reboot

### Step 11: Post-Installation

After reboot:

```bash
# Verify IP
ip addr show

# Verify gateway
ip route show

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl vim htop
```

### Step 12: Document IP

Add to inventory:
```
nginx-proxy | 103 | vmbr2 | 10.0.0.20 | proxy.example.com | Nginx Port 80/443
```

## Verification

- [ ] VM 103 created with correct specs
- [ ] Ubuntu installed
- [ ] IP address assigned and recorded
- [ ] System updated
- [ ] SSH accessible

## Special Configuration

### Enable IP Forwarding

For proper reverse proxy functionality:

```bash
# Edit sysctl
sudo nano /etc/sysctl.conf
```

Uncomment or add:
```
net.ipv4.ip_forward=1
```

Apply:
```bash
sudo sysctl -p
```

## Next Steps

- [MkDocs VM](05-mkdocs-vm.md) - VM-104
- Or [Nginx Installation](../03-software/03-nginx-reverse-proxy.md)
