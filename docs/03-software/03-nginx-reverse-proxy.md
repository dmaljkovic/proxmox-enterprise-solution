# Nginx Reverse Proxy and SSL

Brief description: Install Nginx, configure reverse proxy for all services, and obtain SSL certificates.

## What You'll Learn

- How to install Nginx and Certbot
- How to configure port forwarding on Proxmox host
- How to configure reverse proxy for backend services
- How to obtain and configure SSL certificates

## Prerequisites

- [ ] VM-103 (nginx-proxy) created with IP 10.0.0.20
- [ ] All backend VMs installed (Rocket.Chat, Nextcloud, etc.)
- [ ] Domain names pointing to your server IP
- [ ] Ports 80 and 443 forwarded to nginx-proxy VM

## Estimated Time

1-2 hours

## Step-by-Step Instructions

### Step 1: Install Nginx and Certbot

SSH to nginx-proxy VM:

```bash
ssh admin@10.0.0.20
```

Update and install:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install nginx certbot python3-certbot-nginx -y
sudo systemctl enable --now nginx
```

Verify:

```bash
nginx -v
```

Test:

```bash
curl http://localhost
```

Should show "Welcome to nginx!"

### Step 2: Port Forwarding on Proxmox Host

On the Proxmox host (SSH in), set up port forwarding so internet traffic reaches the nginx-proxy VM:

```bash
# Forward public 80 → Nginx VM port 80
iptables -t nat -A PREROUTING -i vmbr0 -p tcp --dport 80  -j DNAT --to-destination 10.0.0.20:80
iptables -t nat -A PREROUTING -i vmbr0 -p tcp --dport 443 -j DNAT --to-destination 10.0.0.20:443

# Allow the forwarded traffic
iptables -A FORWARD -p tcp -d 10.0.0.20 --dport 80  -j ACCEPT
iptables -A FORWARD -p tcp -d 10.0.0.20 --dport 443 -j ACCEPT
```

Make persistent (create script):

```bash
sudo nano /etc/network/if-pre-up.d/iptables-nat-forward
```

Add the 4 iptables lines above, save, then:

```bash
sudo chmod +x /etc/network/if-pre-up.d/iptables-nat-forward
```

Test from remote computer:

```bash
curl http://<your-public-ip>
```

Should show the default Nginx welcome page.

### Step 3: DNS Setup

You need real domains/subdomains pointed to your server IP. Examples:

| Domain | A Record |
|--------|----------|
| nextcloud.yourdomain.com | YOUR_PUBLIC_IP |
| chat.yourdomain.com | YOUR_PUBLIC_IP |
| auth.yourdomain.com | YOUR_PUBLIC_IP |
| docs.yourdomain.com | YOUR_PUBLIC_IP |

!!! warning "DNS Required for Let's Encrypt"
    Without domains pointing to your server, Let's Encrypt won't work (HTTP-01 challenge needs public port 80 open and domain resolving correctly).

Use `dig` or online DNS checker to verify DNS propagation.

### Step 4: Obtain Let's Encrypt Certificates

Run Certbot to get certificates:

```bash
sudo certbot --nginx -d nextcloud.yourdomain.com -d chat.yourdomain.com
```

Follow prompts:
- Enter email (for renewal reminders)
- Agree to terms of service
- Choose redirect (recommended: yes → auto-redirect HTTP to HTTPS)

Certbot will create/update `/etc/nginx/sites-available/` with SSL configuration.

### Step 5: Configure Nginx Server Blocks

Certbot creates basic configs, but you may need to refine them for proper proxying.

#### Nextcloud Configuration

Edit or create:

```bash
sudo nano /etc/nginx/sites-available/nextcloud.yourdomain.com
```

```nginx
server {
    listen 80;
    server_name nextcloud.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name nextcloud.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/nextcloud.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/nextcloud.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 10G;
    client_body_timeout 300s;

    # Proxy to Nextcloud VM (snap uses port 80 internally)
    location / {
        proxy_pass http://10.0.0.102:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_read_timeout 3600s;
        proxy_redirect off;
    }

    # Handle .well-known for CalDAV/CardDAV
    location /.well-known/carddav { return 301 $scheme://$host/remote.php/dav; }
    location /.well-known/caldav  { return 301 $scheme://$host/remote.php/dav; }
    location ^~ /.well-known       { return 301 $scheme://$host/index.php$uri; }
}
```

#### Rocket.Chat Configuration

```bash
sudo nano /etc/nginx/sites-available/chat.yourdomain.com
```

```nginx
server {
    listen 80;
    server_name chat.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name chat.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/chat.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chat.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Rocket.Chat runs on port 3000 by default
    location / {
        proxy_pass http://10.0.0.101:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_redirect off;
    }
}
```

#### Keycloak Configuration (if using)

```bash
sudo nano /etc/nginx/sites-available/auth.yourdomain.com
```

```nginx
server {
    listen 80;
    server_name auth.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name auth.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/auth.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/auth.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://10.0.0.106:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### MkDocs Configuration (if using)

```bash
sudo nano /etc/nginx/sites-available/docs.yourdomain.com
```

```nginx
server {
    listen 80;
    server_name docs.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name docs.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/docs.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/docs.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://10.0.0.104:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Step 6: Enable Configs and Test

```bash
sudo ln -s /etc/nginx/sites-available/nextcloud.yourdomain.com /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/chat.yourdomain.com /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/auth.yourdomain.com /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/docs.yourdomain.com /etc/nginx/sites-enabled/

sudo nginx -t
sudo systemctl reload nginx
```

### Step 7: Configure Backend Firewall (if UFW enabled)

On each backend VM, allow traffic from nginx-proxy:

```bash
# On Rocket.Chat VM
sudo ufw allow from 10.0.0.20 to any port 3000

# On Nextcloud VM  
sudo ufw allow from 10.0.0.20 to any port 80

# On Keycloak VM
sudo ufw allow from 10.0.0.20 to any port 8080

# On MkDocs VM
sudo ufw allow from 10.0.0.20 to any port 8000
```

## Verification

- [ ] Nginx installed and running
- [ ] Port forwarding working (curl public IP shows nginx page)
- [ ] DNS pointing to server IP
- [ ] SSL certificates obtained for all domains
- [ ] All server blocks enabled
- [ ] HTTPS access working for all services

## Next Steps

- [Firewall Configuration](../04-security/01-firewall.md)
- [Keycloak & OIDC](05-keycloak-oidc.md)
