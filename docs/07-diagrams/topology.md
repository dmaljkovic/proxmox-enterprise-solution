# Network Topology

## Infrastructure Diagram

```mermaid
%%{init: {'theme': 'dark'}}%%
graph TB
    Internet([Internet]) -->|443| Nginx[Nginx Reverse Proxy\nVM-103\n<nginx-ip>]
    
    subgraph Proxmox[Proxmox Host\n<proxmox-ip>]
        subgraph Network[vmbr0 Network]
            Nginx -->|3000| RC[Rocket.Chat\nVM-101\n<rocketchat-ip>]
            Nginx -->|80| NC[Nextcloud\nVM-102\n<nextcloud-ip>]
            Nginx -->|8080| KC[Keycloak SSO\nVM-106\n<keycloak-ip>]
            Nginx -->|8000| MD[MkDocs\nVM-104\n<mkdocs-ip>]
            
            KC -->|389| LDAP[OpenLDAP\nVM-105\n<ldap-ip>]
        end
        
        Prometheus[Prometheus\nPort 9090]
        Grafana[Grafana\nPort 3000]
    end
    
    Prometheus -.->|9100| RC
    Prometheus -.->|9100| NC
    Prometheus -.->|9100| Nginx
    Prometheus -.->|9100| MD
    Prometheus -.->|9100| LDAP
    Prometheus -.->|9100| KC
    
    Grafana --> Prometheus
    
    User([User]) -.->|HTTPS| Nginx
    
    style Internet fill:#2d3748,stroke:#4a5568,color:#fff
    style User fill:#2d3748,stroke:#4a5568,color:#fff
    style Nginx fill:#1a365d,stroke:#2b6cb0,color:#fff
    style RC fill:#276749,stroke:#38a169,color:#fff
    style NC fill:#276749,stroke:#38a169,color:#fff
    style KC fill:#744210,stroke:#d69e2e,color:#fff
    style LDAP fill:#744210,stroke:#d69e2e,color:#fff
    style MD fill:#2d3748,stroke:#4a5568,color:#fff
    style Prometheus fill:#742a2a,stroke:#e53e3e,color:#fff
    style Grafana fill:#742a2a,stroke:#e53e3e,color:#fff
```

## Service Port Map

| Service | VM | Internal Port | External Access |
|---------|-----|---------------|-----------------|
| Rocket.Chat | 101 | 3000 | Via Nginx HTTPS |
| Nextcloud | 102 | 80 | Via Nginx HTTPS |
| Nginx Proxy | 103 | 80/443 | Direct Internet |
| MkDocs | 104 | 8000 | Via Nginx HTTPS |
| OpenLDAP | 105 | 389/636 | Keycloak only |
| Keycloak | 106 | 8080 | Via Nginx HTTPS |
| Prometheus | Host | 9090 | Internal only |
| Grafana | Host | 3000 | Via Nginx HTTPS |

## Traffic Flow

1. User connects to `https://*.example.com`
2. DNS resolves to Proxmox host public IP
3. Nginx receives HTTPS request
4. Nginx terminates SSL
5. Nginx proxies to appropriate backend VM
6. Backend service processes request
7. Response flows back through Nginx to user

