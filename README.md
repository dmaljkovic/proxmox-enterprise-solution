# Proxmox Enterprise Solution

A complete, reproducible build of a six-VM Proxmox estate on a single Hetzner
EX44 dedicated server, written as a hands-on training project.

**Documentation:** <https://dmaljkovic.github.io/proxmox-enterprise-solution/>

## Overview

| | |
|---|---|
| Host | Hetzner EX44 — Intel Core i5-13500, 64 GB DDR4, 2 × 512 GB NVMe mirrored |
| Hypervisor | Proxmox VE 8.2, ZFS on the mirrored pair |
| Guests | Six VMs, Ubuntu Server 24.04 LTS |
| Published | Rocket.Chat, Nextcloud, Keycloak, MkDocs and the proxy, behind one Nginx instance with TLS |
| Identity | OpenLDAP directory with Keycloak as the OIDC provider |
| Observability | Prometheus and Grafana on the Proxmox host |

## Documentation structure

```
docs/
├── index.md                       Entry point and training timeline
├── 01-preparation/                Rescue mode, Proxmox install, networking
├── 02-vm-creation/                One page per guest
├── 03-software/                   One page per service
├── 04-security/                   Firewall, Fail2Ban, backups, CIS hardening
├── 05-monitoring/                 Prometheus, Grafana, Hetzner checks
├── 06-maintenance/                Updates, rollback, doc maintenance
└── 07-diagrams/                   Topology and authentication flow
```

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

This repository is public. [SANITIZATION_RULES.md](SANITIZATION_RULES.md)
defines the placeholder convention and the values that must never appear.
`scripts/sanitize_check.py` enforces them in the pre-commit hook and in CI.
