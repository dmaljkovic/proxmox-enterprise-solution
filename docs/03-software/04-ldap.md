# LDAP Installation

## 1. Install OpenLDAP

Update the system and install the required packages.

```bash
sudo apt update
sudo apt install slapd ldap-utils
```

During installation Ubuntu may ask for the LDAP admin password.

If the wizard does not appear, run it manually:

```bash
sudo dpkg-reconfigure slapd
```

Recommended configuration

| Setting | Value |
|---------|-------|
| DNS domain name | example.com |
| Organization | Example |
| Admin password | choose strong password |
| Database backend | MDB |
| Remove database when purged | No |
| Move old database | Yes |

After configuration your base DN becomes:

```
dc=example,dc=com
```

Admin DN becomes:

```
cn=admin,dc=example,dc=com
```

## 2. Test LDAP locally

Run:

```bash
ldapsearch -x -LLL -H ldap://localhost -b dc=example,dc=com
```

If LDAP works, you should see output containing:

```
dn: dc=example,dc=com
objectClass: top
objectClass: dcObject
objectClass: organization
```

## 3. Enable TLS for LDAP

Create a directory for certificates.

```bash
sudo mkdir /etc/ldap/certs
```

Generate a self-signed certificate.

```bash
sudo openssl req -new -x509 -nodes -days 3650 \
-out /etc/ldap/certs/ldap.crt \
-keyout /etc/ldap/certs/ldap.key
```

Set permissions:

```bash
sudo chown openldap:openldap /etc/ldap/certs/*
sudo chmod 600 /etc/ldap/certs/ldap.key
```

Configure OpenLDAP to use TLS

Create a file:

```bash
nano tls.ldif
```

Add:

```
dn: cn=config
changetype: modify
add: olcTLSCertificateFile
olcTLSCertificateFile: /etc/ldap/certs/ldap.crt
-
add: olcTLSCertificateKeyFile
olcTLSCertificateKeyFile: /etc/ldap/certs/ldap.key
```

Apply it:

```bash
sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f tls.ldif
```

Restart LDAP:

```bash
sudo systemctl restart slapd
```

## 4. Import Sample LDIF (OU + test user)

Create a file:

```bash
nano base.ldif
```

Add this:

```
dn: ou=people,dc=example,dc=com
objectClass: organizationalUnit
ou: people

dn: uid=testuser,ou=people,dc=example,dc=com
objectClass: inetOrgPerson
sn: User
givenName: Test
cn: Test User
uid: testuser
mail: testuser@example.com
userPassword: testpassword
```

Import it:

```bash
ldapadd -x -D "cn=admin,dc=example,dc=com" -W -f base.ldif
```

Enter the admin password.

## 5. Verify the user exists

Run:

```bash
ldapsearch -x -LLL -H ldap://localhost \
-b dc=example,dc=com \
uid=testuser
```

Expected output should include:

```
dn: uid=testuser,ou=people,dc=example,dc=com
cn: Test User
uid: testuser
mail: testuser@example.com
```

## 6. Test login bind

```bash
ldapwhoami -x \
-D "uid=testuser,ou=people,dc=example,dc=com" \
-W
```

Enter password:

```
testpassword
```

If successful you will see:

```
dn:uid=testuser,ou=people,dc=example,dc=com
```
