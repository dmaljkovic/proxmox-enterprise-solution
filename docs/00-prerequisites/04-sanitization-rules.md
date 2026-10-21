# Sanitization rules

This repository is **public**. Everything committed here is readable by anyone,
and Git history is permanent — a leaked value stays in the history even if you
later delete it from `master`.

This document defines what may and may not appear in the repository. The rules
are enforced automatically by `scripts/sanitize_check.py`, which runs:

- on every commit, via the `.githooks/pre-commit` hook, and
- on every push and pull request, via the `Sanitization check` step in
  `.github/workflows/deploy.yml`.

Enable the local hook once per clone:

```bash
git config core.hooksPath .githooks
```

## Why this exists

The previous deployment of this project ran on a real Hetzner server. Notes
kept alongside the documentation contained that server's public address, its
gateway, and the private subnet used by the VMs. Copy-pasting those values into
a public repository would expose live infrastructure.

The rewrite replaces every one of those values with documented placeholders, and
this gate exists to stop them from creeping back in.

## Placeholder convention

| Concept | Placeholder | Notes |
|---|---|---|
| Domain | `example.com` | RFC 2606 reserved. Subdomains: `chat.example.com`, `cloud.example.com`, `auth.example.com`, `docs.example.com`, `grafana.example.com` |
| Public host address | `203.0.113.10` | RFC 5737 TEST-NET-3, with a `/26` prefix |
| Private lab network | `10.0.0.0/24` | Host gateway `10.0.0.5`, VMs `10.0.0.101`–`10.0.0.109` |
| Credentials | `changeme`, `<password>` | Never a realistic value |

`10.0.0.0/24` is the only private network used in these documents. The private
subnet of the retired deployment is rejected by the gate.

## Deny list

### Never committable

These rules have **no escape hatch**. A match is always a blocking error.

| Rule | Blocks |
|---|---|
| `github-token` | `ghp_…`, `gho_…`, `ghu_…`, `ghs_…`, `ghr_…`, `github_pat_…` |
| `aws-access-key` | `AKIA…`, `ASIA…` |
| `google-api-key` | `AIza…` |
| `private-key` | `-----BEGIN … PRIVATE KEY-----` blocks |
| `git-credential` | URLs that embed a username and a password, as a credential helper stores them |

### Deployment-specific

| Rule | Blocks |
|---|---|
| `legacy-public-ip` | The retired server's public address |
| `legacy-gateway` | The retired server's gateway address |
| `unrelated-domain` | Domains owned by other projects |
| `unrelated-hardware` | Hardware identifiers belonging to other projects |

!!! note "The blocked values are not written down here on purpose"
    This document is published. Spelling out the retired addresses would defeat
    the purpose of blocking them, and would publish a description of the
    previous topology to anyone reading the repository.

    The values are therefore matched by **SHA-256 digest** rather than by
    literal comparison. The digests live in `scripts/sanitize_check.py`, in the
    `DENY_DIGESTS` table. A digest cannot be reversed, so the values cannot be
    recovered from the repository, but the gate still matches the exact value.
    Run `python scripts/sanitize_check.py --list-rules` to print the table
    locally.

    The retired private subnet needs no digest at all: the generic IPv4 rule
    below rejects every address outside `10.0.0.0/24`, which covers it.

### Value rules

| Rule | Behaviour |
|---|---|
| `literal-password` | A `password`/`passwd`/`secret` assignment whose value is not in the placeholder list. Use `changeme` or `<password>`. |
| `unexpected-ipv4` | Any IPv4 literal outside the allow list below. Suppress a single line with a `sanitize:allow` comment. |

## IPv4 allow list

| Range | Purpose |
|---|---|
| `10.0.0.0/24` | Placeholder lab network — the only private range used here |
| `127.0.0.0/8` | Loopback |
| `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` | RFC 5737 documentation ranges |
| `1.1.1.1`, `9.9.9.9`, `8.8.8.8` | Public resolvers |
| `0.0.0.0`, `255.255.255.255`, `255.x.x.x`, `224.x.x.x` | Special-use addresses |

The other two RFC 1918 ranges are **deliberately not allowed**. Only
`10.0.0.0/24` is used for private addressing, so a retired subnet cannot
return by accident. Adding another range is a deliberate, documented change.

When a real-looking address is genuinely needed to explain a concept, keep it
inside the ranges above. If that is impossible, add an inline
`# sanitize:allow` comment on that line and justify it in the pull request.

## Files that must never be committed

These are covered by `.gitignore`, and several of them live outside the
repository directory on purpose:

| File | Why |
|---|---|
| `github_token.txt` | GitHub credential |
| `RESCU_FIX.docx` | Contains the retired server's real address |
| `Edukacija_proxmox_zfs.pdf` | Generated artefact derived from the above |
| `*.pem`, `*.key`, `id_rsa`, `id_ed25519` | Private key material |
| `.env` | Runtime secrets |

## Manual review checklist

Before opening a pull request:

1. `python scripts/sanitize_check.py --scan-all` — must exit `0`.
2. `mkdocs build --strict` — must exit `0` with no warnings.
3. Re-read any page that was copied from another project; check the network
   values, the domain names and the hardware specs.
4. Confirm every address on every page is inside the allow list above. The
   generic IPv4 rule enforces this, but read the rendered page as well — a
   value can reach the site through a diagram, a code block or a table cell.
5. Confirm the rendered site shows placeholders, not real values — the
   deployment directory `site/` is served verbatim by GitHub Pages.
