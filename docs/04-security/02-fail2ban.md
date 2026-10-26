# Fail2Ban Configuration

Brief description: Install and configure Fail2Ban on all VMs for intrusion prevention.

## Prerequisites

- [ ] Firewall configured on all VMs
- [ ] SSH access confirmed

## Installation

On each VM:

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Configuration

### Basic SSH Protection

Create jail configuration:

```bash
sudo nano /etc/fail2ban/jail.local
```

Add:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
```

Restart:

```bash
sudo systemctl restart fail2ban
```

### Nginx Proxy Additional Rules

```bash
sudo nano /etc/fail2ban/jail.local
```

Add:

```ini
[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2
```

## Verification

- [ ] Fail2Ban installed on all VMs
- [ ] SSH jail enabled
- [ ] Nginx jails enabled (on proxy VM)
- [ ] Service running
- [ ] Status checked with: sudo fail2ban-client status

## Next Steps

- [Backup and Snapshots](03-backup-snapshots.md)
