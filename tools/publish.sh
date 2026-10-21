#!/usr/bin/env bash
#
# Phase 8: rename the repository, publish the rewritten site, and stand up
# the stub that keeps the old documentation URL working.
#
# Usage:
#   tools/publish.sh            # run it
#   tools/publish.sh --dry-run  # show what would happen, change nothing
#
# Requires:
#   - gh authenticated            (gh auth status)
#   - a working SSH key           (ssh -T git@github.com)
#
# Git operations use SSH, so no token is needed for them. The token in gh is
# only used for the API calls: renaming the repository, switching the Pages
# source, and creating the stub repository.

set -euo pipefail

OLD_NAME="proxmox-lab"
NEW_NAME="proxmox-enterprise-solution"
OWNER="dmaljkovic"
STUB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/old-pages-stub" && pwd)"

DRY_RUN=0
WITH_OLD_URL_STUB=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --with-old-url-stub) WITH_OLD_URL_STUB=1 ;;
        -h|--help)
            cat <<'EOF'
Usage: tools/publish.sh [--dry-run] [--with-old-url-stub]

  --dry-run             print what would happen without changing anything
  --with-old-url-stub   also create the redirect stub repository that keeps
                        the old proxmox-lab URL working. It is opt-in because
                        the stub is a second repository on the account, and
                        the old URL is not worth one unless it is wanted.
EOF
            exit 0
            ;;
        *)
            echo "unknown option: $arg" >&2
            exit 1
            ;;
    esac
done

run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  would run: %s\n' "$*"
    else
        printf '  running  : %s\n' "$*"
        "$@"
    fi
}

say() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }

# --------------------------------------------------------------------------
say "Preflight"

command -v gh >/dev/null || { echo "gh is not installed"; exit 1; }

if ! gh auth status >/dev/null 2>&1; then
    cat <<'EOF'
gh is not authenticated. Run:

    gh auth login -h github.com -p https -w

and complete the browser flow. Then re-run this script.
EOF
    exit 1
fi
echo "  gh authenticated as $(gh api user --jq .login)"

# GitHub's SSH endpoint always exits non-zero, even on a successful
# authentication, so the greeting in the output is what has to be checked.
SSH_GREETING="$(ssh -o BatchMode=yes -T git@github.com 2>&1 || true)"
if ! printf '%s' "$SSH_GREETING" | grep -q "successfully authenticated"; then
    echo "  SSH authentication to github.com failed"
    printf '%s\n' "$SSH_GREETING" | head -3
    exit 1
fi
echo "  SSH authentication to github.com works"

if [ ! -d .git ]; then
    echo "  run this from inside the repository"
    exit 1
fi
git fetch origin --quiet 2>/dev/null || echo "  note: could not fetch origin yet (expected before the rename)"

# --------------------------------------------------------------------------
say "Rename $OWNER/$OLD_NAME -> $OWNER/$NEW_NAME"

if gh repo view "$OWNER/$NEW_NAME" >/dev/null 2>&1; then
    echo "  $OWNER/$NEW_NAME already exists, skipping rename"
else
    run gh repo rename "$NEW_NAME" --repo "$OWNER/$OLD_NAME" --yes
fi

# --------------------------------------------------------------------------
say "Point origin at the new name"

run git remote set-url origin "git@github.com:$OWNER/$NEW_NAME.git"
git remote -v

# --------------------------------------------------------------------------
say "Switch the Pages source to the GitHub Actions workflow"

# The rewritten workflow deploys through actions/deploy-pages, which only
# works when the Pages source is the workflow rather than the gh-pages branch.
if gh api "repos/$OWNER/$NEW_NAME/pages" >/dev/null 2>&1; then
    echo "  Pages site already exists, updating its source"
    run gh api --method PUT "repos/$OWNER/$NEW_NAME/pages" -f build_type=workflow
else
    echo "  no Pages site yet, creating one with the workflow source"
    run gh api --method POST "repos/$OWNER/$NEW_NAME/pages" \
        -f source[branch]=master \
        -f source[path]=/ \
        -f build_type=workflow
fi

# --------------------------------------------------------------------------
say "Publish master"

if [ "$DRY_RUN" -eq 1 ]; then
    echo "  would push master to origin"
else
    if [ "$(git rev-parse --abbrev-ref HEAD)" != "master" ]; then
        git checkout master
    fi
    git pull --ff-only origin master || git reset --hard origin/master

    # "rewrite" was the working branch while the old site was still on
    # master. It is still merged in when it has something the master branch
    # does not, so work committed on either branch ends up published.
    if git rev-parse --verify --quiet rewrite >/dev/null; then
        if ! git merge-base --is-ancestor rewrite master; then
            git merge --no-ff rewrite \
                -m "Merge the rewrite branch into master" || {
                echo "  the rewrite branch could not be merged, resolve it by hand"
                exit 1
            }
        fi
    fi
fi

echo "  validating before push"
python3 scripts/sanitize_check.py --scan-all
if [ -d .venv ]; then
    .venv/bin/mkdocs build --strict
else
    python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt
    .venv/bin/mkdocs build --strict
fi

run git push origin master

# --------------------------------------------------------------------------
say "Publish the stub for the old URL"

# A renamed repository keeps answering under its old name through a GitHub
# redirect, so "gh repo view" succeeding does not mean the name is taken.
# The API reports the canonical full_name, which is what has to be compared.
name_is_free() {
    local canonical
    canonical="$(gh api "repos/$OWNER/$OLD_NAME" --jq .full_name 2>/dev/null || true)"
    [ -z "$canonical" ] || [ "$canonical" != "$OWNER/$OLD_NAME" ]
}

if [ "$WITH_OLD_URL_STUB" -eq 0 ]; then
    echo "  skipped, pass --with-old-url-stub to publish it"
elif ! name_is_free; then
    echo "  $OWNER/$OLD_NAME already exists, skipping stub creation"
else
    # GitHub releases the old name asynchronously after a rename, so give it
    # a moment before trying to claim it again.
    created=0
    for attempt in 1 2 3 4 5 6 7 8 9 10; do
        if gh repo create "$OWNER/$OLD_NAME" --public \
            --description "Redirect to $NEW_NAME" \
            --disable-issues --disable-wiki 2>/dev/null; then
            created=1
            break
        fi
        echo "  the name is not free yet, retrying in 5s (attempt $attempt)"
        sleep 5
    done
    if [ "$created" -eq 0 ]; then
        echo "  could not create $OWNER/$OLD_NAME"
        echo "  create it manually at https://github.com/new, then run:"
        echo "    tools/publish.sh --with-old-url-stub"
        exit 1
    fi
fi

if [ "$WITH_OLD_URL_STUB" -eq 1 ] && [ "$DRY_RUN" -eq 0 ]; then
    TMP="$(mktemp -d)"
    cp "$STUB_DIR/index.html" "$STUB_DIR/404.html" "$TMP"/
    touch "$TMP/.nojekyll"
    (
        cd "$TMP"
        git init --quiet --initial-branch=gh-pages
        git add -A
        git -c user.name="$OWNER" -c user.email="$OWNER@users.noreply.github.com" \
            commit --quiet -m "Redirect to the renamed documentation site"
        git remote add origin "git@github.com:$OWNER/$OLD_NAME.git"
        git push --quiet --force -u origin gh-pages
    )
    rm -rf "$TMP"

    run gh api --method POST "repos/$OWNER/$OLD_NAME/pages" \
        -f source[branch]=gh-pages \
        -f source[path]=/ || true
fi

# --------------------------------------------------------------------------
say "Verify"

if [ "$WITH_OLD_URL_STUB" -eq 1 ]; then
    OLD_URL_LINE="  Old URL       https://$OWNER.github.io/$OLD_NAME/   (redirect stub)"
else
    OLD_URL_LINE="  Old URL       not published, run with --with-old-url-stub to restore it"
fi

cat <<EOF

  New site      https://$OWNER.github.io/$NEW_NAME/
$OLD_URL_LINE
  Repository    https://github.com/$OWNER/$NEW_NAME

  The first deployment takes a minute or two. Watch it with:

    gh run watch --repo $OWNER/$NEW_NAME

EOF
