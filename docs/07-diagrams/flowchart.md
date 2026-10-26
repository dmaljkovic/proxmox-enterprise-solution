# SSO Authentication Flow

## OIDC Authentication Sequence

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    participant User as User/Browser
    participant App as Application<br/>(Rocket.Chat/Nextcloud)
    participant Nginx as Nginx Proxy
    participant Keycloak as Keycloak SSO
    participant LDAP as OpenLDAP
    
    User->>App: Access application
    App->>User: Redirect to Keycloak
    User->>Nginx: Request auth.example.com
    Nginx->>Keycloak: Forward to Keycloak
    Keycloak->>User: Show login page
    
    User->>Keycloak: Enter credentials
    Keycloak->>LDAP: Authenticate user
    LDAP->>Keycloak: Auth success + user info
    Keycloak->>Keycloak: Create session
    Keycloak->>User: Redirect to app with code
    
    User->>App: Send auth code
    App->>Nginx: Request token
    Nginx->>Keycloak: Exchange code for token
    Keycloak->>App: Return ID token
    
    App->>App: Validate token
    App->>User: Grant access
    
    Note over User,LDAP: Subsequent requests use session cookie
```

## Login Flow Steps

1. **User Access**: User navigates to application URL
2. **Redirect**: Application redirects to Keycloak
3. **Login Page**: Keycloak presents authentication form
4. **Credential Validation**: Keycloak validates against LDAP
5. **Session Creation**: Keycloak creates authenticated session
6. **Token Exchange**: Application exchanges code for tokens
7. **Access Granted**: User can access application

## Token Types

| Token | Purpose | Lifetime |
|-------|---------|----------|
| Authorization Code | Temporary code for token exchange | 1 minute |
| ID Token | Contains user identity information | Session |
| Access Token | Grants access to resources | 5-15 minutes |
| Refresh Token | Obtains new access tokens | 30 days |

## Security Features

- **HTTPS Only**: All communication encrypted
- **PKCE**: Proof Key for Code Exchange (prevents interception)
- **Short-lived codes**: Authorization codes expire quickly
- **Token validation**: Applications validate token signatures
- **Session management**: Centralized logout via Keycloak

