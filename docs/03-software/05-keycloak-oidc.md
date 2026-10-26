# Keycloak Installation and OIDC Configuration

Brief description: Install Keycloak 26.5.5 and set up OIDC for SSO.

## What You'll Learn

- How to install Keycloak 26.5.5
- How to create OIDC clients for SSO
- How to integrate with Rocket.Chat and Nextcloud

## Prerequisites

- [ ] VM-106 created and Ubuntu 24.04 LTS installed
- [ ] OpenJDK 17 installed on Keycloak VM
- [ ] IP addresses documented
- [ ] Nginx reverse proxy configured

## Estimated Time

2-3 hours

## Part 1: Keycloak Installation

### Step 1: Update System and Install Java

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y openjdk-17-jdk
```

Verify:

```bash
java -version   # Should show openjdk 17.x
```

### Step 2: Download and Install Keycloak (Standalone Tarball Method)

No official APT package exists from Keycloak project → use the recommended tar.gz distribution.

```bash
cd /tmp
wget https://github.com/keycloak/keycloak/releases/download/26.5.5/keycloak-26.5.5.tar.gz
sudo tar -xzf keycloak-26.5.5.tar.gz -C /opt/
sudo mv /opt/keycloak-26.5.5 /opt/keycloak
```

### Step 3: Create Dedicated Keycloak User/Group and Set Permissions

```bash
sudo groupadd keycloak
sudo useradd -r -g keycloak -d /opt/keycloak -s /sbin/nologin keycloak

sudo chown -R keycloak:keycloak /opt/keycloak
sudo chmod -R u+rwX /opt/keycloak

sudo mkdir -p /opt/keycloak/data /var/log/keycloak
sudo chown -R keycloak:keycloak /opt/keycloak/data /var/log/keycloak
```

### Step 4: Build Optimized Image (Production Recommendation)

```bash
cd /opt/keycloak
sudo -u keycloak bin/kc.sh build
```

### Step 5: Create Systemd Service File

```bash
sudo nano /etc/systemd/system/keycloak.service
```

Paste (customize hostname, password, and internal listening):

```ini
[Unit]
Description=Keycloak Identity and Access Management
After=network.target

[Service]
Type=simple
User=keycloak
Group=keycloak
WorkingDirectory=/opt/keycloak
ExecStart=/opt/keycloak/bin/kc.sh start --optimized \
  --hostname=auth.example.com \
  --http-port=8080 \
  --http-host=0.0.0.0 \
  --proxy-headers=xforwarded \
  --log=console,file --log-file=/var/log/keycloak/keycloak.log

Restart=always
RestartSec=10

Environment="JAVA_OPTS=-Xms1024m -Xmx2048m -Djava.security.egd=file:/dev/./urandom"

# ONLY for FIRST start – remove these lines after initial setup!
Environment="KC_BOOTSTRAP_ADMIN_USERNAME=admin"
Environment="KC_BOOTSTRAP_ADMIN_PASSWORD=<very-strong-password-here>"

[Install]
WantedBy=multi-user.target
```

- `--hostname=...`: Your public domain (Keycloak enforces redirects/URIs).
- `--proxy-headers=xforwarded`: Trusts headers from Nginx proxy.

Remove the two `KC_BOOTSTRAP_ADMIN_*` lines after first successful start (edit file → sudo systemctl daemon-reload → restart).

### Step 6: Start and Enable Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable keycloak
sudo systemctl start keycloak
```

Check:

```bash
sudo systemctl status keycloak
sudo journalctl -u keycloak -f   # Wait for "Listening on: http://0.0.0.0:8080"
```

### Step 7: Initial Access & Admin Console (Temporary – via Internal)

From another internal VM (or Proxmox console forwarding):

`http://<keycloak-internal-ip>:8080/admin`

Login: admin / <password from service file>

After first login → remove bootstrap env vars from service file, reload & restart.

## Part 2: OIDC Client Configuration

This section covers connecting Keycloak to your OpenLDAP directory and creating OIDC clients for single sign-on.

### Step 1: Connect Keycloak to OpenLDAP

Keycloak can authenticate users against your existing LDAP directory.

1. Open the Keycloak Admin Console: `https://auth.example.com`
2. Login with your admin credentials
3. Select the **example** realm
4. Navigate to **User Federation** → **Add provider** → **ldap**

Configure the LDAP federation settings:

| Setting | Value |
|---------|-------|
| Vendor | Other |
| Connection URL | `ldap://LDAP_VM_IP:389` |
| Bind DN | `cn=admin,dc=example,dc=com` |
| Bind Credential | LDAP_ADMIN_PASSWORD |
| Users DN | `ou=people,dc=example,dc=com` |
| Username LDAP attribute | uid |
| RDN LDAP attribute | uid |
| UUID LDAP attribute | entryUUID |
| User Object Classes | inetOrgPerson |

Under **Sync Settings**, enable:
- Import Users: ON
- Edit Mode: READ_ONLY

5. Click **Save**
6. Click **Test connection** to verify connectivity
7. Click **Test authentication** to verify bind credentials
8. Click **Synchronize all users** to import existing users

Verify users appear under **Users** → **View all users**.

### Step 2: Create OIDC Clients

OIDC clients allow applications to authenticate users through Keycloak.

#### Rocket.Chat

1. Go to **Clients** → **Create client**
2. Configure:

| Setting | Value |
|---------|-------|
| Client type | OpenID Connect |
| Client ID | rocketchat |
| Name | Rocket.Chat |

3. Click **Next**
4. Enable capability config:

| Setting | Value |
|---------|-------|
| Client authentication | ON |
| Authorization | OFF |
| Standard flow | ON |

5. Click **Next**
6. Configure login settings:

| Setting | Value |
|---------|-------|
| Root URL | `https://chat.example.com` |
| Home URL | `https://chat.example.com` |
| Valid redirect URIs | `https://chat.example.com/*` |
| Web origins | `https://chat.example.com` |

7. Click **Save**

#### Nextcloud

1. Go to **Clients** → **Create client**
2. Configure:

| Setting | Value |
|---------|-------|
| Client type | OpenID Connect |
| Client ID | nextcloud |
| Name | Nextcloud |

3. Click **Next**
4. Use default capability config
5. Configure login settings:

| Setting | Value |
|---------|-------|
| Root URL | `https://cloud.example.com` |
| Valid redirect URIs | `https://cloud.example.com/*` |
| Web origins | `https://cloud.example.com` |

6. Click **Save**

#### LDAP Admin UI

1. Go to **Clients** → **Create client**
2. Configure:

| Setting | Value |
|---------|-------|
| Client type | OpenID Connect |
| Client ID | ldap-admin |
| Name | LDAP Admin UI |

3. Click **Next**
4. Configure login settings:

| Setting | Value |
|---------|-------|
| Valid redirect URIs | `https://ldap.example.com/*` |

5. Click **Save**

### Step 3: Retrieve Client Secrets

Each OIDC client requires a secret for authentication.

1. Go to **Clients** → select client → **Credentials** tab
2. Copy the **Client Secret**

Store secrets in a password manager:

- Rocket.Chat: `<generated-in-keycloak>`
- Nextcloud: `<generated-in-keycloak>`

### Authentication Flow

```
User → Application (Rocket.Chat/Nextcloud) → Keycloak (OIDC) → OpenLDAP
```

| Component | Role |
|-----------|------|
| OpenLDAP | Identity storage |
| Keycloak | Authentication provider |
| Applications | OIDC clients |
