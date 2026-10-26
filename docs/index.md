# Proxmox Enterprise Solution

A complete, reproducible build of a nine-VM enterprise estate on a single
Hetzner EX44 dedicated server, documented end to end.

## What this is

| | |
|---|---|
| Host | Hetzner EX44 — Intel Core i5-13500, 64 GB DDR4, 2 × 512 GB NVMe mirrored |
| Hypervisor | Proxmox VE 9.2, ZFS on the mirrored pair |
| Guests | Nine VMs, Ubuntu 26.04 LTS (Rocket.Chat on 24.04 LTS) |
| Published | Rocket.Chat, Nextcloud, Keycloak, Grafana and this documentation, all behind one Nginx proxy with TLS |
| Identity | OpenLDAP directory with Keycloak 26.8.1 as the OIDC provider |
| Observability | Prometheus and Grafana, with node_exporter across the estate |
| Documentation | This site, built with MkDocs and deployed to GitHub Pages |

## Start here

1. **[Lab inventory](00-prerequisites/03-lab-inventory.md)** — the address plan,
   the port matrix, the version matrix. Read this first; every other page
   refers back to it.
2. **[Hardware and budget](00-prerequisites/01-hardware-and-budget.md)** — what
   the server is, what it costs, and what the cost does not cover.
3. **[Account, network and domain](00-prerequisites/02-account-network-domain.md)**
   — Robot, the server firewall, DNS and the six credentials to generate.

## Structure

| Section | Contents |
|---|---|
| Prerequisites | Hardware, account setup, DNS, and the inventory that drives everything else |
| Preparation | Rescue mode, the ZFS pool, the Proxmox install, networking, and recovery from a lost configuration |
| VM Creation | One page per guest, in build order |
| Software Installation | Rocket.Chat, Nextcloud, Nginx and TLS, OpenLDAP, Keycloak, PostgreSQL, OIDC, MkDocs, Prometheus, Grafana |
| Security | Host firewall, VM firewall matrix, Fail2Ban, CIS hardening, backups, audit |
| Monitoring | The Prometheus and Grafana stack, and Hetzner-level checks |
| Maintenance | Updates, backup and restore, maintaining this site |
| Diagrams | Topology, authentication flow, backup flow |
