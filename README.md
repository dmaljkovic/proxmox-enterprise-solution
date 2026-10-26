# Proxmox Enterprise Solution

A complete, reproducible build of a nine-VM enterprise estate on a single
Hetzner EX44 dedicated server, documented end to end.

**Documentation:** <https://dmaljkovic.github.io/proxmox-enterprise-solution/>

## Overview

| | |
|---|---|
| Host | Hetzner EX44 — Intel Core i5-13500, 64 GB DDR4, 2 × 512 GB NVMe mirrored |
| Hypervisor | Proxmox VE 9.2, ZFS on the mirrored pair |
| Guests | Nine VMs, Ubuntu 26.04 LTS (Rocket.Chat on 24.04 LTS) |
| Published | Rocket.Chat, Nextcloud, Keycloak, Grafana and the docs, behind one Nginx proxy with TLS |
| Identity | OpenLDAP directory with Keycloak 26.8.1 as the OIDC provider |
| Observability | Prometheus and Grafana with node_exporter across the estate |

## Documentation structure

```
docs/
├── index.md                       Entry point and design decisions
├── 00-prerequisites/              Hardware, account, DNS, inventory
├── 01-preparation/                Rescue, ZFS, install, network, recovery
├── 02-vm-creation/                One page per guest
├── 03-software/                   One page per service
├── 04-security/                   Firewalls, Fail2Ban, CIS, backups, audit
├── 05-monitoring/                 Prometheus, Grafana, Hetzner checks
├── 06-maintenance/                Updates, restore, doc maintenance
└── 07-diagrams/                   Topology, auth flow, backup flow
```

The [lab inventory](docs/00-prerequisites/03-lab-inventory.md) is the single
source of truth for every address, port and version. Other pages link to it
rather than repeating values.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/sanitize_check.py --scan-all   # must exit 0
mkdocs build --strict                          # must exit 0
mkdocs serve                                   # preview on http://127.0.0.1:8000
```

Enable the pre-commit sanitization gate once per clone:

```bash
git config core.hooksPath .githooks
```

## Deployment

The `Deploy to GitHub Pages` workflow builds with `mkdocs build --strict`,
runs the sanitization gate, and publishes through `actions/deploy-pages`. The
site requires the repository's Pages source to be set to **GitHub Actions**.

## Sanitization

This repository is public. The [sanitization rules](docs/00-prerequisites/04-sanitization-rules.md)
define the placeholder convention and the values that must never appear.
`scripts/sanitize_check.py` enforces them in the pre-commit hook and in CI.
