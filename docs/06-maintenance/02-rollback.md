# Emergency Rollback Procedures

Brief description: Procedures for emergency recovery and rollback.

## VM Rollback

From Proxmox:

1. Select VM
2. Go to Snapshots
3. Select snapshot to restore
4. Click Rollback
5. Confirm

## ZFS Rollback

```bash
# List snapshots
zfs list -t snapshot

# Rollback to specific snapshot
zfs rollback rpool/vm-101-disk-0@snapshot-name
```

## Service Recovery

### Rocket.Chat

```bash
ssh admin@10.0.0.101
sudo snap restart rocketchat
```

### Nextcloud

```bash
sudo snap restart nextcloud
```

### Keycloak

```bash
sudo systemctl restart keycloak
```

## Full System Recovery

1. Boot from rescue mode
2. Restore from backup:
```bash
gunzip -c vm-101-backup.gz | zfs receive rpool/vm-101-disk-0
```

## Verification

- [ ] Rollback procedures tested
- [ ] Snapshot restore tested
- [ ] Backup restoration verified

