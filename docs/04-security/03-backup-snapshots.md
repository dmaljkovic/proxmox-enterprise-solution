# Backup and ZFS Snapshots

Brief description: Configure ZFS snapshots and remote backups for all VMs.

## Prerequisites

- [ ] Proxmox host access
- [ ] ZFS pool healthy
- [ ] Storage box or remote server for backups

## Step 1: Install Sanoid

On Proxmox host:

```bash
apt install -y sanoid
```

## Step 2: Configure Snapshot Policy

```bash
nano /etc/sanoid/sanoid.conf
```

Add:

```ini
[rpool/vm-101-disk-0]
use_template = production

[rpool/vm-102-disk-0]
use_template = production

[rpool/vm-103-disk-0]
use_template = production

[rpool/vm-104-disk-0]
use_template = production

[rpool/vm-105-disk-0]
use_template = production

[rpool/vm-106-disk-0]
use_template = production

[template_production]
frequently = 0
hourly = 24
daily = 7
weekly = 4
monthly = 3
yearly = 0
autosnap = yes
autoprune = yes
```

## Step 3: Enable Sanoid

```bash
systemctl enable sanoid.timer
systemctl start sanoid.timer
```

## Step 4: Create Backup Script

```bash
cat > /root/backup-replication.sh << 'EOF'
#!/bin/bash
STORAGE_BOX="u12345@u12345.your-storagebox.de"
BACKUP_PATH="/backup/proxmox"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p /tmp/zfs-backup-$DATE

for vm in 101 102 103 104 105 106; do
    echo "Backing up VM $vm..."
    zfs send rpool/vm-${vm}-disk-0@autosnap_$(date +%Y-%m-%d) | \
    gzip > /tmp/zfs-backup-$DATE/vm-${vm}.gz
    scp /tmp/zfs-backup-$DATE/vm-${vm}.gz ${STORAGE_BOX}:${BACKUP_PATH}/
done

rm -rf /tmp/zfs-backup-$DATE
echo "Backup completed: $DATE"
EOF

chmod +x /root/backup-replication.sh
```

## Step 5: Schedule Weekly Backups

```bash
crontab -e
```

Add:

```
0 2 * * 0 /root/backup-replication.sh >> /var/log/backup.log 2>&1
```

## Verification

- [ ] Sanoid installed
- [ ] Snapshot policy configured
- [ ] Timer enabled
- [ ] Backup script created
- [ ] Weekly backup scheduled
- [ ] Test backup completed

## Next Steps

- [CIS Hardening](04-cis-hardening.md)
