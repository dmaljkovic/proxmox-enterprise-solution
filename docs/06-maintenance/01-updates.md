# System Updates

Brief description: Procedures for keeping all systems updated and secure.

## Proxmox Host Updates

```bash
# Update package lists
apt update

# Check for upgrades
apt list --upgradable

# Perform upgrade
apt full-upgrade -y

# Check if reboot required
if [ -f /var/run/reboot-required ]; then
    echo "Reboot required"
fi
```

## VM Updates

Script to update all VMs:

```bash
for ip in 10.0.0.101 10.0.0.102 10.0.0.20 10.0.0.104 10.0.0.105 10.0.0.106; do
    echo "Updating $ip..."
    ssh admin@$ip "sudo apt update && sudo apt upgrade -y"
done
```

## Snap Updates (Rocket.Chat & Nextcloud)

### Rocket.Chat

```bash
ssh admin@10.0.0.101
sudo snap refresh rocketchat
```

### Nextcloud

```bash
ssh admin@10.0.0.102
sudo snap refresh nextcloud
```

## Verification

- [ ] Update procedures documented
- [ ] Scripts created
- [ ] Tested on one VM

## Schedule

- **Security updates**: Weekly
- **Regular updates**: Monthly
- **Major upgrades**: Quarterly

