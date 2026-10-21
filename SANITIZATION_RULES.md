# Sanitization rules

This repository is **public**. The full rules live in the documentation, where
they are published alongside the pages they protect:

**→ [`docs/00-prerequisites/04-sanitization-rules.md`](docs/00-prerequisites/04-sanitization-rules.md)**

The gate itself is `scripts/sanitize_check.py`. Run it with:

```bash
python scripts/sanitize_check.py --scan-all      # whole worktree
python scripts/sanitize_check.py --list-rules    # print the rule table
```

It runs automatically in the pre-commit hook (`.githooks/pre-commit`) and in
the `Sanitization check` step of `.github/workflows/deploy.yml`.

Enable the local hook once per clone:

```bash
git config core.hooksPath .githooks
```
