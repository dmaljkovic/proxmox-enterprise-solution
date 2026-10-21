# Proxmox Enterprise Solution

A complete, reproducible build of a nine-VM enterprise estate on a single
Hetzner EX44 dedicated server, documented end to end.

Everything in this documentation is built to be followed literally. Each page
states the exact version, the exact command and the exact expected result. The
placeholders — `example.com` and `10.0.0.0/24` — are defined once in the
[lab inventory](00-prerequisites/03-lab-inventory.md) and reused everywhere.

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

## Design decisions worth knowing

- **One server, one failure domain.** There is no failover. Recovery is
  restore-from-backup, and the [backup strategy](04-security/05-backup-strategy.md)
  is written around that reality rather than around an imaginary HA setup.
- **Only one machine is public.** Traffic arrives at the Nginx proxy and goes
  nowhere else. Every other VM sits behind the private network and its own
  firewall rules.
- **One documented exception.** The Rocket.Chat guest runs Ubuntu 24.04 LTS
  because MongoDB does not start on Ubuntu 26.04's kernel. The reasoning is in
  the [lab inventory](00-prerequisites/03-lab-inventory.md).
- **The monitoring stack is not on the host.** Prometheus and Grafana are
  ordinary VMs, so a host compromise does not hand over the metrics, and
  neither is exposed to the internet.
- **The old deployment's addresses are gone.** Every address in these pages is
  a placeholder. The [sanitization rules](00-prerequisites/04-sanitization-rules.md) explain the
  convention and the automated gate that enforces it.

## Build status

This documentation is being rebuilt in phases. Pages still carrying the
"Under construction" notice are placeholders for content that is being
rewritten, not finished procedures. The build history of the previous version
is preserved on the `archive/pre-rewrite` branch.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/sanitize_check.py --scan-all   # must exit 0
mkdocs build --strict                          # must exit 0
mkdocs serve                                   # preview on http://127.0.0.1:8000
```

Enable the pre-commit gate once per clone:

```bash
git config core.hooksPath .githooks
```

## License

MIT — see [LICENSE](https://github.com/dmaljkovic/proxmox-enterprise-solution/blob/master/LICENSE).
