# Keycloak VM Creation (VM-106)

Brief description: Create VM-106 for Keycloak SSO server with 2 vCPU, 4GB RAM, and 20GB storage.

## VM Specifications

- **VM ID**: 106
- **Name**: keycloak
- **CPU**: 2 vCPU
- **RAM**: 4 GiB
- **Disk**: 20 GiB (ZFS)
- **OS**: Ubuntu Server 24.04 LTS
- **Network**: vmbr2 (private internal network)
- **Static IP**: 10.0.0.106/24
- **Gateway**: 10.0.0.5
- **Purpose**: SSO and Identity Provider (IdP)

## Prerequisites

- [ ] Proxmox Web UI accessible
- [ ] Ubuntu 24.04 LTS ISO available
- [ ] ZFS storage pool available

## Step-by-Step Instructions

### Step 1: Create VM

Click **Create VM** in Proxmox UI

### Step 2: General

- **VM ID**: 106
- **Name**: keycloak

Click **Next**

### Step 3: OS

- **ISO image**: ubuntu-24.04-live-server-amd64.iso

Click **Next**

### Step 4: System

Accept defaults

Click **Next**

### Step 5: Disks

- **Storage**: rpool
- **Disk size**: 20 GiB
- **Format**: qcow2

!!! note "Java Application Storage"
    Keycloak requires Java and has additional libraries. 20GB provides comfortable space for the application and logs.

Click **Next**

### Step 6: CPU

- **Sockets**: 1
- **Cores**: 2

Click **Next**

### Step 7: Memory

- **Memory**: 4096 MiB

!!! note "Java Memory Requirements"
    Keycloak runs on Java and benefits from 4GB RAM for optimal performance, especially with LDAP integration.

Click **Next**

### Step 8: Network

- **Bridge**: vmbr2 (private internal network)
- **Model**: VirtIO

Click **Next**

!!! note "vmbr2 Configuration"
    This VM uses the internal private network (vmbr2) with NAT. The Nginx Proxy will handle external access to Keycloak.

### Step 9: Confirm

Review:
- Name: keycloak
- VM ID: 106
- CPU: 2 cores
- Memory: 4096 MiB
- Disk: 20 GiB

Click **Finish**

### Step 10: Install Ubuntu

1. Start VM 106
2. Open Console
3. Install Ubuntu:

**Network Configuration**:
- Select the network interface (ens18)
- Choose **Configure network manually**
- Enter:
  - **IP Address**: 10.0.0.106
  - **Netmask**: 255.255.255.0 (/24)
  - **Gateway**: 10.0.0.5
  - **Name servers**: 8.8.8.8, 1.1.1.1

**Profile**:
- Server name: keycloak
- Username: admin
- Password: <password>

**SSH**: Install OpenSSH server

**Complete** installation

### Step 11: Post-Installation

```bash
# Verify IP
ip addr show

# Verify gateway
ip route show

# Update system
sudo apt update && sudo apt upgrade -y

# Install Java (required for Keycloak)
sudo apt install -y openjdk-17-jdk

# Verify Java installation
java -version
```

Expected output:
```
openjdk version "17.0.x" 202x-xx-xx
OpenJDK Runtime Environment (build 17.0.x+xx-Ubuntu-xx)
OpenJDK 64-Bit Server VM (build 17.0.x+xx-Ubuntu-xx, mixed mode, sharing)
```

### Step 12: Document IP

Add to inventory:
```
keycloak | 106 | vmbr2 | 10.0.0.106 | auth.example.com | Keycloak Port 8080
```

## Verification

- [ ] VM 106 created with correct specs
- [ ] Ubuntu 24.04 LTS installed
- [ ] OpenJDK 17 installed
- [ ] IP address assigned and recorded
- [ ] System updated

## Next Steps

All VMs are now created! Proceed to software installation:
- [Rocket.Chat Installation](../03-software/01-rocketchat.md)
- [Nextcloud Installation](../03-software/02-nextcloud.md)
- [Nginx Installation](../03-software/03-nginx-reverse-proxy.md)
- [Keycloak & OIDC](../03-software/05-keycloak-oidc.md)

Or return to [VM Overview](01-overview.md) to verify all IPs are documented.
