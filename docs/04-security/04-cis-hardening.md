# CIS Benchmark Hardening

Brief description: Apply CIS benchmark security hardening to Proxmox host and all VMs.

## Proxmox Host Hardening

### SSH Hardening

```bash
nano /etc/ssh/sshd_config
```

Set:

```
PermitRootLogin prohibit-password
PasswordAuthentication no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 0
Protocol 2
X11Forwarding no
```

Restart:

```bash
systemctl restart sshd
```

### Password Policy

```bash
apt install -y libpam-pwquality

nano /etc/security/pwquality.conf
```

Set:

```
minlen = 14
minclass = 4
maxrepeat = 2
dcredit = -1
ucredit = -1
ocredit = -1
lcredit = -1
```

### Kernel Parameters

```bash
nano /etc/sysctl.conf
```

Add:

```
net.ipv4.ip_forward = 0
net.ipv4.conf.all.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.tcp_syncookies = 1
kernel.randomize_va_space = 2
```

Apply:

```bash
sysctl -p
```

### Auditd

```bash
apt install -y auditd audispd-plugins
systemctl enable auditd
systemctl start auditd
```

## VM Hardening Script

Apply to all VMs:

```bash
cat > /root/harden-vm.sh << 'EOF'
#!/bin/bash
VM_IP=$1

ssh admin@$VM_IP << 'REMOTE'
sudo apt install -y libpam-pwquality ufw fail2ban

# SSH hardening
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Password policy
echo "minlen = 14
minclass = 3
dcredit = -1
ucredit = -1
lcredit = -1
ocredit = -1" | sudo tee /etc/security/pwquality.conf

# Enable UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw enable

# Enable fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Secure permissions
sudo chmod 600 /etc/shadow
sudo chmod 600 /etc/gshadow

REMOTE
EOF

chmod +x /root/harden-vm.sh
```

Run for each VM:

```bash
for ip in <rocketchat-ip> <nextcloud-ip> <nginx-ip> <mkdocs-ip> <ldap-ip> <keycloak-ip>; do
    /root/harden-vm.sh $ip
done
```

## Verification

- [ ] SSH hardened on all systems
- [ ] Password policy enforced
- [ ] Kernel parameters set
- [ ] Auditd installed and running
- [ ] VMs hardened with script
- [ ] Permissions secured

## Next Steps

- [Prometheus & Grafana](../05-monitoring/01-prometheus-grafana.md)
