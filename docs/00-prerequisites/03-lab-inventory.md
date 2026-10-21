# Lab inventory

!!! info "Single source of truth"
    Every address, port and version in this project is defined here once and
    referenced from the other pages. If a procedure elsewhere needs an address
    or a port, it links back to this page rather than repeating the value.

## Host

| Property | Value |
|---|---|
| Provider | Hetzner, dedicated server (Robot) |
| Product | EX44 |
| CPU | Intel Core i5-13500 — 6 Performance cores + 8 Efficiency cores, 14 cores / 20 threads |
| Memory | 64 GB DDR4 |
| Storage | 2 × 512 GB NVMe, mirrored |
| Network | 1 × 1 Gbit/s port, 1 Gbit/s guaranteed bandwidth |
| Location | FSN 1 (Falkenstein) or HEL 1 (Helsinki) |
| Public address | `203.0.113.10/26` — placeholder, see [Account, network and domain](02-account-network-domain.md) |
| Hostname | `pve-01.example.com` |

!!! warning "Single network port"
    The EX44 has exactly one 1 Gbit/s port. There is no second interface to
    bond, bridge or fail over. The consequences are structural:

    - `vmbr0` is the only bridge with a physical uplink.
    - `vmbr2` is an internal-only NAT network with no physical port.
    - The host cannot survive a NIC failure without a migration to another
      host, which is out of scope for this project.

## Address plan

Two networks, both carried by the single physical port.

| Network | Bridge | Range | Purpose |
|---|---|---|---|
| Public | `vmbr0` | `203.0.113.10/26` | Host management, DNAT target, TLS termination origin |
| Private | `vmbr2` | `10.0.0.0/24` | All nine VMs, NATed outbound through `vmbr0` |

The host holds `10.0.0.5` on `vmbr2`. That address is the default gateway for
every VM.

## Virtual machines

| ID | Name | Guest OS | vCPU | RAM | Disk | Address |
|---|---|---|---|---|---|---|
| 101 | `rocketchat` | Ubuntu 24.04 LTS | 2 | 4 GB | 30 GB | `10.0.0.101` |
| 102 | `nextcloud` | Ubuntu 26.04 LTS | 2 | 6 GB | 50 GB | `10.0.0.102` |
| 103 | `nginx-proxy` | Ubuntu 26.04 LTS | 1 | 2 GB | 10 GB | `10.0.0.103` |
| 104 | `mkdocs` | Ubuntu 26.04 LTS | 1 | 2 GB | 10 GB | `10.0.0.104` |
| 105 | `openldap` | Ubuntu 26.04 LTS | 1 | 2 GB | 10 GB | `10.0.0.105` |
| 106 | `keycloak` | Ubuntu 26.04 LTS | 2 | 4 GB | 20 GB | `10.0.0.106` |
| 107 | `postgres` | Ubuntu 26.04 LTS | 2 | 4 GB | 30 GB | `10.0.0.107` |
| 108 | `prometheus` | Ubuntu 26.04 LTS | 2 | 4 GB | 30 GB | `10.0.0.108` |
| 109 | `grafana` | Ubuntu 26.04 LTS | 1 | 4 GB | 20 GB | `10.0.0.109` |

**Totals:** 14 vCPU, 32 GB RAM, 210 GB of guest disk.

The host has 14 physical cores, so the guest total is exactly 1 vCPU per
physical core — no oversubscription of cores. 32 GB of 64 GB is left for the
host, the ZFS ARC and burst headroom.

### Why one VM runs Ubuntu 24.04

The Rocket.Chat guest is the single exception to "Ubuntu 26.04 LTS everywhere".

MongoDB 8.0 and later refuse to start on kernels 6.19 through 7.0.13, and
Ubuntu 26.04 ships a `7.0.0` kernel whose release string never matches the
upstream `7.0.14+` exemption. The issue is tracked upstream as
[MongoDB SERVER-136848](https://jira.mongodb.org/browse/SERVER-136848) and was
still open when this document was written. MongoDB 7.0 is unaffected, but
pinning the whole Rocket.Chat stack to a two-year-old database major version
to stay on a newer operating system is the worse trade.

Running the Rocket.Chat guest on Ubuntu 24.04 LTS — the release Rocket.Chat
itself documents — removes the constraint entirely and keeps the rest of the
estate on a current LTS.

## Port matrix

Nothing on `vmbr2` is reachable from the internet. Traffic arrives at the
public address and is forwarded to `10.0.0.103`, the Nginx proxy.

### Published services

| Source | Destination | Port | Purpose |
|---|---|---|---|
| Internet | `10.0.0.103` | 80/tcp | TLS redirect to 443 |
| Internet | `10.0.0.103` | 443/tcp | TLS termination, all five hostnames |

### Host management

| Source | Destination | Port | Purpose |
|---|---|---|---|
| Admin network | `203.0.113.10` | 22/tcp | SSH — restricted to the admin address |
| Admin network | `203.0.113.10` | 8006/tcp | Proxmox web UI — restricted to the admin address |
| `10.0.0.0/24` | `203.0.113.10` | 8006/tcp | Guest API calls from the private network |

### Proxmox internal

Required between the host and its own cluster components, and by guests that
use the QEMU guest agent.

| Port | Protocol | Purpose |
|---|---|---|
| 8006 | tcp | `pveproxy` — web UI and API |
| 8007 | tcp | `pvedaemon` — management API |
| 3128 | tcp | `pveproxy` worker, SPICE proxy |
| 6800–6804 | udp | SPICE proxy |
| 6789 | tcp | Corosync `pmxcfs` |
| 5405 | tcp/udp | Corosync vote and `rsession` |

### Internal service traffic

Each entry is the only permitted source for that port. Anything not listed
here is blocked by the VM firewall.

| Destination | Port | Allowed source | Purpose |
|---|---|---|---|
| `10.0.0.101` | 3000/tcp | `10.0.0.103` | Rocket.Chat HTTP |
| `10.0.0.101` | 27017/tcp | `10.0.0.101` | MongoDB — loopback inside the guest only |
| `10.0.0.102` | 80/tcp | `10.0.0.103` | Nextcloud HTTP |
| `10.0.0.103` | 80, 443 | `203.0.113.10` | Nginx front end |
| `10.0.0.104` | 8000/tcp | `10.0.0.103` | MkDocs preview server |
| `10.0.0.105` | 636/tcp | `10.0.0.106` | LDAPS — consumed by Keycloak only |
| `10.0.0.106` | 8443/tcp | `10.0.0.103` | Keycloak HTTPS |
| `10.0.0.106` | 8080/tcp | `10.0.0.0/24` | Keycloak HTTP, used for internal redirects |
| `10.0.0.107` | 5432/tcp | `10.0.0.106` | PostgreSQL — Keycloak database only |
| `10.0.0.108` | 9090/tcp | `10.0.0.103`, `10.0.0.109` | Prometheus API |
| `10.0.0.109` | 3000/tcp | `10.0.0.103` | Grafana HTTP |
| `10.0.0.0/24` | 9100/tcp | `10.0.0.108` | node_exporter scrape |

## Domain map

All names use the `example.com` placeholder domain.

| Hostname | Target | Service |
|---|---|---|
| `chat.example.com` | `10.0.0.101:3000` | Rocket.Chat |
| `cloud.example.com` | `10.0.0.102:80` | Nextcloud |
| `auth.example.com` | `10.0.0.106:8443` | Keycloak |
| `docs.example.com` | `10.0.0.104:8000` | This documentation |
| `grafana.example.com` | `10.0.0.109:3000` | Grafana |

OpenLDAP has **no** public hostname. It is reachable only from Keycloak on
`10.0.0.105:636`.

## Version matrix

Pinned versions for the whole estate. These were current when this document was
written; check the upstream release notes before reusing this build.

### Host

| Component | Version | Notes |
|---|---|---|
| Proxmox VE | 9.2 (ISO `proxmox-ve_9.2-1.iso`) | Debian 13, kernel 7.0, ZFS 2.4 |
| Guest OS | Ubuntu 26.04 LTS | Except the Rocket.Chat guest, on 24.04 LTS |

### Services

| Component | Version | Notes |
|---|---|---|
| Nginx | 1.28.3 | From the Ubuntu 26.04 archive |
| Certbot | 4.0.0 | ACME client, Let's Encrypt |
| Keycloak | 26.8.1 | Java 21 |
| Rocket.Chat | 8.9.0 LTS | Docker Compose, supported to 2027-10-31 |
| MongoDB | 8.0 | Only on the Rocket.Chat guest, which runs Ubuntu 24.04 |
| Nextcloud | 35.0.2 | Docker Compose |
| PostgreSQL | 18 | From the Ubuntu 26.04 archive |
| Prometheus | 3.15.1 | 3.13.5 is the LTS alternative |
| node_exporter | 1.12.1 | |
| Grafana | 13.2.4 | |
| OpenLDAP | 2.6 | From the Ubuntu 26.04 archive |

### Toolchain

| Component | Version |
|---|---|
| Python | 3.14 (Ubuntu 26.04) |
| Docker Engine | 29.1 |
| MkDocs | 1.6.1 |
| MkDocs Material | 9.7.7 |

## Related pages

- [Hardware and budget](01-hardware-and-budget.md)
- [Account, network and domain](02-account-network-domain.md)
- [Proxmox VE installation](../01-preparation/03-proxmox-installation.md)
- [Network configuration](../01-preparation/04-network-configuration.md)
- [VM estate overview](../02-vm-creation/01-overview.md)
