# Nextcloud Installation

Brief description: Install Nextcloud on VM-102 using Snap and configure for reverse proxy.

## What You'll Learn

- How to install Nextcloud via Snap
- How to configure trusted domains and proxies
- How to verify the installation

## Prerequisites

- [ ] VM-102 created with Ubuntu 24.04 LTS
- [ ] Nextcloud snap selected during Ubuntu installation (or install manually below)
- [ ] IP address: 10.0.0.102
- [ ] Nginx Proxy VM (10.0.0.20) installed
- [ ] Domain: cloud.yourdomain.com

## Estimated Time

30-45 minutes

!!! note "Snap Already Installed"
    If you selected Nextcloud during Ubuntu installation, the snap is already installed. Skip Steps 2-4 if already done.

## Step-by-Step Instructions

### Step 1: SSH to Nextcloud VM

```bash
ssh admin@10.0.0.102
```

### Step 2: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 3: Install Snap (if needed)

```bash
sudo apt install -y snapd
```

Verify:

```bash
snap version
```

### Step 4: Install Nextcloud

```bash
sudo snap install nextcloud
```

This will take 10-15 minutes. Monitor progress:

```bash
sudo snap changes
```

Wait until status shows "Done".

### Step 5: Create Admin Account

```bash
sudo nextcloud.manual-install admin <strong-password>
```

Replace `<strong-password>` with a secure password.

### Step 6: Configure for Reverse Proxy

Configure trusted domains and trusted proxies:

```bash
# Add your domain
sudo nextcloud.occ config:system:set trusted_domains 1 --value=cloud.yourdomain.com

# Add nginx-proxy IP as trusted proxy
sudo nextcloud.occ config:system:set trusted_proxies 0 --value=10.0.0.20

# Set URL overwrite
sudo nextcloud.occ config:system:set overwrite.cli.url --value=https://cloud.yourdomain.com/

# Set protocol overwrite
sudo nextcloud.occ config:system:set overwriteprotocol --value=https
```

Restart Nextcloud:

```bash
sudo snap restart nextcloud
```

Verify configuration:

```bash
sudo nextcloud.occ config:system:get trusted_domains
sudo nextcloud.occ config:system:get trusted_proxies
```

### Step 7: Verify Installation

Check Nextcloud status:

```bash
sudo nextcloud.occ status
```

Expected output:
```
  - installed: true
  - version: 28.0.x.x
  - versionstring: 28.0.x
  - edition: 
```

### Step 8: Configure Background Jobs

Set cron for background tasks:

```bash
sudo nextcloud.occ background:cron
```

Add cron job:

```bash
echo "*/5 * * * * root /snap/bin/nextcloud.occ background:cron" | sudo tee /etc/cron.d/nextcloud
```

### Step 9: Configure Memory Caching

Enable APCu for better performance:

```bash
sudo nextcloud.occ config:system:set memcache.local --value='\OC\Memcache\APCu'
```

### Step 10: Adjust PHP Memory Limit

```bash
sudo snap set nextcloud php.memory-limit=512M
```

### Step 11: Test Access

After configuring Nginx reverse proxy:

1. Open browser: `https://cloud.yourdomain.com`

2. Login with:
   - Username: admin
   - Password: <password> (the one set in Step 5)

3. You should see the Nextcloud dashboard

## Verification

- [ ] Nextcloud snap installed
- [ ] Admin account created
- [ ] Trusted domains configured
- [ ] Trusted proxies configured (nginx-proxy IP)
- [ ] SSL certificates obtained
- [ ] Access via domain working

(End of file
## Next Steps

- [Nginx Reverse Proxy & SSL](03-nginx-reverse-proxy.md)
- [Firewall Configuration](../04-security/01-firewall.md)
