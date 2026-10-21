# Old Pages URL stub

This directory holds the content for the **stub repository** that can keep the
old documentation URL working after the rename.

## Current state

**The stub is not published.** The repository `dmaljkovic/proxmox-lab` was
deleted, so `https://dmaljkovic.github.io/proxmox-lab/` returns 404 and the
only live URL is:

```
https://dmaljkovic.github.io/proxmox-enterprise-solution/
```

The content in this directory is kept so the stub can be restored in one
command if the old URL is wanted:

```bash
tools/publish.sh --with-old-url-stub
```

## Why it exists

GitHub Pages project URLs contain the repository name. Renaming
`proxmox-lab` to `proxmox-enterprise-solution` changes the published URL to:

```
https://dmaljkovic.github.io/proxmox-enterprise-solution/
```

GitHub does **not** redirect the old URL. Requests to
`https://dmaljkovic.github.io/proxmox-lab/` return 404 until a repository with
the old name serves a site of its own.

Renaming releases the name `proxmox-lab`, so a small stub repository can claim
it and serve a single redirect page. The old URL then lands on the new
documentation.

## Contents

| File | Purpose |
|---|---|
| `index.html` | Served at the root of the old URL. Redirects to the new site via a meta refresh and a script. |
| `404.html` | Served for any path under the old URL that does not exist, so deep links such as `/proxmox-lab/04-security/01-firewall/` also land on the new site. |
| `.nojekyll` | Empty. Stops GitHub Pages from running Jekyll over the content. |

## Publishing it

`tools/publish.sh --with-old-url-stub` does all of it. The steps it performs,
for reference:

```bash
# 1. Create the stub repository with the old name.
gh repo create dmaljkovic/proxmox-lab --public --description \
  "Redirect to proxmox-enterprise-solution"

# 2. Publish the stub content to the gh-pages branch.
cd tools/old-pages-stub
git init --initial-branch=gh-pages
git add .
git commit -m "Redirect to the renamed documentation site"
git remote add origin https://github.com:dmaljkovic/proxmox-lab.git
git push -u origin gh-pages

# 3. Enable Pages from the gh-pages branch.
gh api --method POST repos/dmaljkovic/proxmox-lab/pages \
  -f source[branch]=gh-pages \
  -f source[path]=/

# 4. Verify.
curl -sI https://dmaljkovic.github.io/proxmox-lab/ | head -1
```

!!! note "The name may not be free straight away"
    GitHub releases a renamed repository's name asynchronously. The publish
    script retries for a minute before giving up and telling you to create
    the repository by hand at https://github.com/new.

The stub repository is intentionally empty of content. It holds nothing but the
redirect, so the old URL resolves and no stale documentation is republished.

