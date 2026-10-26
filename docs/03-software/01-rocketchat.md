# Rocket.Chat Installation

Brief description: Install and configure Rocket.Chat on VM-101 using Snap.

## What You'll Learn

- How to verify Rocket.Chat snap is installed
- How to configure Rocket.Chat
- How to set up Nginx reverse proxy
- How to verify the installation

## Prerequisites

- [ ] VM-101 created and Ubuntu 24.04 LTS installed
- [ ] Rocket.Chat snap selected during Ubuntu installation (or install manually below)
- [ ] IP address assigned and documented (10.0.0.101)
- [ ] SSH access to VM-101 working
- [ ] 4GB RAM and 30GB disk available
- [ ] Nginx Proxy VM (VM-103) installed and accessible

## Estimated Time

30-45 minutes

!!! note "Snap Already Installed"
    If you selected Rocket.Chat during Ubuntu installation, the snap is already installed. Skip Step 2 if already done.

## Step-by-Step Instructions

### Step 1: SSH to Rocket.Chat VM

```bash
ssh admin@10.0.0.101
```

### Step 2: Verify Rocket.Chat Snap

Check if Rocket.Chat snap is installed:

```bash
snap list rocketchat
```

If not installed, install it:

```bash
sudo snap install rocketchat
```

### Step 3: Configure Rocket.Chat

Enable HTTPS (required for Rocket.Chat):

```bash
sudo snap set rocketchat port=3000
sudo snap set rocketchat https=enabled
sudo snap set rocketchat ssl-certs=enabled
```

Start Rocket.Chat:

```bash
sudo snap start rocketchat
```

Check status:

```bash
sudo snap services rocketchat
```

### Step 4: Wait for Initial Setup

Rocket.Chat takes a few minutes to initialize on first boot. Wait 2-3 minutes then check:

```bash
sudo snap logs rocketchat -n 50
```

Look for messages indicating the server is ready.

### Step 5: Access Rocket.Chat

Open your browser and navigate to:

```
http://10.0.0.101:3000
```

Or if HTTPS is configured:

```
https://10.0.0.101
```

### Step 6: Initial Admin Setup

1. Follow the on-screen wizard to create the first admin user
2. Configure your organization details
3. Complete the setup

### Step 7: Configure Nginx Reverse Proxy

On the Nginx Proxy VM (10.0.0.20), create a configuration file:

```bash
ssh admin@10.0.0.20
sudo nano /etc/nginx/sites-available/rocketchat
```

Add the following configuration:

```nginx
upstream rocketchat {
    server 10.0.0.101:3000;
}

server {
    listen 80;
    server_name chat.example.com;

    location / {
        proxy_pass http://rocketchat;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forward-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forward-Proto http;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/rocketchat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 8: Update Firewall (if enabled)

On the Rocket.Chat VM, allow traffic from nginx-proxy:

```bash
sudo ufw allow from 10.0.0.20 to any port 3000
sudo ufw reload
```

### Step 9: Verify Access via Domain

After DNS propagation, access Rocket.Chat via your domain:

```
https://chat.example.com
```

## Configuration Commands

### Common Snap Commands

```bash
# Stop Rocket.Chat
sudo snap stop rocketchat

# Start Rocket.Chat
sudo snap start rocketchat

# Restart Rocket.Chat
sudo snap restart rocketchat

# View logs
sudo snap logs rocketchat -f

# Check status
snap services rocketchat
```

### Environment Variables

To set custom environment variables:

```bash
sudo snap set rocketchat root-url=https://chat.example.com
sudo snap restart rocketchat
```

## Verification

- [ ] Rocket.Chat snap is installed
- [ ] Service is running
- [ ] Accessible at http://10.0.0.101:3000
- [ ] Nginx proxy configured
- [ ] Accessible via domain (chat.example.com)
- [ ] Admin account created

## Next Steps

Proceed to [Nextcloud Installation](02-nextcloud.md) if not already installed.
