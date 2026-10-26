# Documentation Update Guide

Brief description: How to update this MkDocs documentation.

## Local Development

### Setup

```bash
# Clone repository
git clone https://github.com/dmaljkovic/proxmox-enterprise-solution.git
cd proxmox-enterprise-solution

# Install dependencies
pip install -r requirements.txt

# Serve locally
mkdocs serve
```

### Making Changes

1. Edit files in `docs/` directory
2. Preview at http://localhost:8000
3. Build: `mkdocs build`

### Publishing

```bash
# Commit changes
git add .
git commit -m "Update documentation"
git push origin master
```

GitHub Actions will automatically deploy to GitHub Pages.

## Adding New Pages

1. Create `.md` file in appropriate `docs/` subdirectory
2. Add entry to `mkdocs.yml` nav section
3. Follow existing format

## Verification

- [ ] Local development setup working
- [ ] Can build site locally
- [ ] GitHub Actions deploying successfully

