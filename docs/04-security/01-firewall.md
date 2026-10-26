# Firewall Configuration

Brief description: Configure UFW firewall on all VMs with appropriate rules for each service.

## What You'll Learn

- How to configure UFW firewall
- How to set up firewall rules for each VM role
- How to prevent SSH lockout

## Prerequisites

- [ ] All VMs created and Ubuntu installed
- [ ] IP addresses documented
- [ ] SSH access to all VMs confirmed

## VM Firewall Rules Overview

| VM | Incoming Allowed | From |
|----|------------------|------|
| rocketchat | 3000 | nginx-proxy |
| nextcloud | 80, 443 | nginx-proxy |
| nginx-proxy | 80, 443 | Internet |
| mkdocs | 8000 | nginx-proxy |
| openldap | 389, 636 | keycloak |
| keycloak | 8080 | nginx-proxy |
| ALL VMs | 22 | Admin IPs only |

## Rocket.Chat VM (VM-101)

SSH to VM:

```bash
ssh admin@10.0.0.101
```

Configure UFW:

```bash
# Install UFW
sudo apt install -y ufw

# Default deny
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (be careful!)
sudo ufw allow from <your-admin-ip> to any port 22

# Allow Rocket.Chat from Nginx Proxy only
sudo ufw allow from 10.0.0.20 to any port 3000

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

## Nextcloud VM (VM-102)

```bash
ssh admin@10.0.0.102

sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from <your-admin-ip> to any port 22
sudo ufw allow from 10.0.0.20 to any port 80
sudo ufw enable
sudo ufw status verbose
```

## Nginx Proxy VM (VM-103)

```bash
ssh admin@10.0.0.20

sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from <your-admin-ip> to any port 22

# Allow HTTP/HTTPS from anywhere
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

sudo ufw enable
sudo ufw status verbose
```

## MkDocs VM (VM-104)

```bash
ssh admin@10.0.0.104

sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from <your-admin-ip> to any port 22
sudo ufw allow from 10.0.0.20 to any port 8000
sudo ufw enable
sudo ufw status verbose
```

## OpenLDAP VM (VM-105)

```bash
ssh admin@10.0.0.105

sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from <your-admin-ip> to any port 22

# LDAP ports - only from Keycloak
sudo ufw allow from 10.0.0.106 to any port 389
sudo ufw allow from 10.0.0.106 to any port 636

sudo ufw enable
sudo ufw status verbose
```

## Keycloak VM (VM-106)

```bash
ssh admin@10.0.0.106

sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from <your-admin-ip> to any port 22
sudo ufw allow from 10.0.0.20 to any port 8080
sudo ufw enable
sudo ufw status verbose
```

## Verification

- [ ] UFW installed on all VMs
- [ ] Default deny incoming configured
- [ ] SSH allowed from admin IP only
- [ ] Service ports allowed from appropriate sources
- [ ] Firewall enabled on all VMs
- [ ] Status verified on all VMs

## Next Steps

- [Fail2Ban Configuration](02-fail2ban.md)
