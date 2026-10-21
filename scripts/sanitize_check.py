#!/usr/bin/env python3
"""Sanitization gate for the proxmox-enterprise-solution repository.

Blocks any commit that would publish infrastructure details which are specific
to a real deployment: the previous Hetzner server's public address, the retired
private subnet, credentials, private keys, or any IPv4 literal outside the
documented placeholder ranges.

Usage
-----
    python scripts/sanitize_check.py --scan-all        # whole worktree
    python scripts/sanitize_check.py FILE [FILE ...]   # specific files
    python scripts/sanitize_check.py --list-rules      # print the rule table

Exit codes
----------
    0  no violations
    1  at least one violation
    2  bad invocation

Escape hatch
------------
Append ``sanitize:allow`` to a line to suppress the generic IPv4 rule for that
line only. It is intentionally not available for the credential and private-key
rules: those must never be committed, even as a placeholder.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# Credential and private-material rules. These are absolute: no escape hatch.
# --------------------------------------------------------------------------

CREDENTIAL_RULES: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "github-token",
        "GitHub personal access / OAuth / server token",
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{16,}|\bgithub_pat_[A-Za-z0-9_]{20,}"),
    ),
    (
        "aws-access-key",
        "AWS access key id",
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ),
    (
        "google-api-key",
        "Google API key",
        re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    ),
    (
        "private-key",
        "Private key material",
        re.compile(r"-----BEGIN\s+(?:RSA|DSA|EC|OPENSSH|PGP|ENCRYPTED)?\s*PRIVATE KEY-----"),
    ),
    (
        "git-credential",
        "Stored git credential helper blob",
        re.compile(r"https?://[^/\s:]+:[^@\s]+@"),
    ),
]

# --------------------------------------------------------------------------
# Deployment-specific values.
#
# These are stored as SHA-256 digests rather than as literals. The repository
# is public, so writing the blocked values down here would publish them and
# defeat the purpose of blocking them. A digest cannot be reversed, but it
# still matches the exact value, which is what matters here.
#
# Matching is case-insensitive: candidates are lowercased before hashing.
# --------------------------------------------------------------------------

DENY_DIGESTS: dict[str, str] = {
    # Public address of the retired deployment
    "95657b2532c46d15f960b9a3e0cebb4270c1fe6709a2c6674f00661a2f29c8e9": "legacy-public-ip",
    # Gateway address of the retired deployment
    "b23d2a3bc149fa3d3ec3c2f7536df513582d112fe170f1e163a3eecdcaa5ca42": "legacy-gateway",
    # Domain owned by an unrelated project
    "ea1cd092a6192308fa32ff186687a65102ee97bfa23e03c9c5f01b2c461ddfb4": "unrelated-domain",
    # Hardware identifiers belonging to an unrelated project
    "e04937fd7eefbf0e0989ff6897af65a754f36b13e104e73c2d4c53dbfb1df974": "unrelated-hardware",
    "bacebd7c0ea242412344aa3035c25d7b669f976709f175076c674abbe86938d1": "unrelated-hardware",
}

DENY_RULE_DESCRIPTIONS = {
    "legacy-public-ip": "Public address of the retired deployment",
    "legacy-gateway": "Gateway address of the retired deployment",
    "unrelated-domain": "Domain owned by an unrelated project",
    "unrelated-hardware": "Hardware identifier belonging to an unrelated project",
}

# --------------------------------------------------------------------------
# Password-style assignments. Values that are clearly placeholders are fine.
# --------------------------------------------------------------------------

PASSWORD_ASSIGNMENT = re.compile(
    r"(?i)\b(?:pass(?:word|wd)|secret)\b\s*[:=]\s*[\"']?([^\s\"'`]{4,})[\"']?"
)

PASSWORD_PLACEHOLDERS = {
    "changeme",
    "change_me",
    "change-me",
    "changethis",
    "placeholder",
    "example",
    "redacted",
    "secret",
    "password",
    "letmein",
    "yourpassword",
    "your_password",
    "your-password",
    "notset",
    "unset",
    "todo",
    "fixme",
    "xxxxxxxx",
    "********",
    "<password>",
    "${password}",
    "{{password}}",
    "$password",
    "%password%",
    "null",
    "none",
}

# --------------------------------------------------------------------------
# Generic IPv4 rule. Anything not inside the documented placeholder ranges
# is treated as a potential leak of real infrastructure addressing.
# --------------------------------------------------------------------------

IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")

ALLOWED_IPV4 = [
    # Placeholder lab network: 10.0.0.0/24
    (re.compile(r"^10\.0\.0\.\d{1,3}$"), "placeholder lab network (10.0.0.0/24)"),
    # Loopback
    (re.compile(r"^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$"), "loopback"),
    # RFC 5737 documentation ranges
    (re.compile(r"^192\.0\.2\.\d{1,3}$"), "RFC 5737 TEST-NET-1"),
    (re.compile(r"^198\.51\.100\.\d{1,3}$"), "RFC 5737 TEST-NET-2"),
    (re.compile(r"^203\.0\.113\.\d{1,3}$"), "RFC 5737 TEST-NET-3"),
    # Well-known public resolvers (not sensitive)
    (re.compile(r"^1\.1\.1\.1$"), "public resolver"),
    (re.compile(r"^9\.9\.9\.9$"), "public resolver"),
    (re.compile(r"^8\.8\.8\.8$"), "public resolver"),
    # Special-use
    (re.compile(r"^0\.0\.0\.0$"), "unspecified address"),
    (re.compile(r"^255\.255\.255\.255$"), "broadcast address"),
    (re.compile(r"^255\.\d{1,3}\.\d{1,3}\.\d{1,3}$"), "netmask"),
    (re.compile(r"^224\.\d{1,3}\.\d{1,3}\.\d{1,3}$"), "multicast"),
]

# Only 10.0.0.0/24 is used for private addressing in these documents. Every
# other RFC 1918 range is rejected, so a retired subnet cannot return by
# accident. Adding a range here requires a deliberate, documented change.

SKIP_DIRS = {".git", "site", ".venv", "venv", "__pycache__", ".cache", "node_modules"}
BINARY_SNIFF_BYTES = 8192


def is_allowed_ip(ip: str) -> tuple[bool, str]:
    """Return (allowed, reason)."""
    for pattern, reason in ALLOWED_IPV4:
        if pattern.match(ip):
            return True, reason
    return False, "not inside a documented placeholder range"


def is_placeholder_password(value: str) -> bool:
    stripped = value.strip().strip("\"'`")
    return stripped.lower() in PASSWORD_PLACEHOLDERS


def digest_candidates(line: str) -> list[str]:
    """Words and adjacent word pairs from a line, normalised for hashing."""
    tokens = [t.strip("\"'`.,;:()[]{}<>").lower() for t in line.split()]
    candidates = [t for t in tokens if t]
    candidates += [
        f"{tokens[i]} {tokens[i + 1]}"
        for i in range(len(tokens) - 1)
        if tokens[i] and tokens[i + 1]
    ]

    # Addresses are often written with a prefix length or a port, and a
    # trailing dot. Strip those so "addr/26" still matches "addr".
    extended: list[str] = []
    for candidate in candidates:
        for part in (candidate.split("/")[0], candidate.split(":")[0]):
            part = part.strip(".")
            if part and part not in candidates:
                extended.append(part)
    candidates += extended

    return candidates


def match_digest(line: str) -> list[tuple[str, str]]:
    """Return (rule_name, matched_tokens) for any denied digest found in the line."""
    hits: dict[str, list[str]] = {}
    for candidate in digest_candidates(line):
        digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
        rule = DENY_DIGESTS.get(digest)
        if rule:
            tokens = hits.setdefault(rule, [])
            if candidate not in tokens:
                tokens.append(candidate)
    return [(rule, ", ".join(tokens)) for rule, tokens in hits.items()]


def read_text(path: Path) -> str | None:
    """Return file contents, or None for binary / unreadable files."""
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw[:BINARY_SNIFF_BYTES]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def scan_text(path: Path, text: str) -> list[tuple[int, str, str]]:
    """Return a list of (line_number, rule_name, message) violations."""
    violations: list[tuple[int, str, str]] = []

    for lineno, line in enumerate(text.splitlines(), start=1):
        allow_ip = "sanitize:allow" in line

        for name, description, pattern in CREDENTIAL_RULES:
            match = pattern.search(line)
            if match:
                violations.append((lineno, name, f"{description}: {match.group(0)[:40]}"))

        for rule, token in match_digest(line):
            violations.append(
                (
                    lineno,
                    rule,
                    f"{DENY_RULE_DESCRIPTIONS.get(rule, rule)}: {token[:40]}",
                )
            )

        for match in PASSWORD_ASSIGNMENT.finditer(line):
            if not is_placeholder_password(match.group(1)):
                violations.append(
                    (
                        lineno,
                        "literal-password",
                        "password/secret assigned a literal value; use a placeholder",
                    )
                )

        if not allow_ip:
            for match in IPV4.finditer(line):
                ip = match.group(0)
                allowed, reason = is_allowed_ip(ip)
                if not allowed:
                    violations.append(
                        (lineno, "unexpected-ipv4", f"{ip} is {reason}")
                    )

    return violations


def git_tracked_files() -> list[Path]:
    """Files git would consider part of the worktree (tracked + untracked, ignored excluded)."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [REPO_ROOT / line for line in result.stdout.splitlines() if line]


def walk_worktree() -> list[Path]:
    """Every non-ignored file in the worktree, without relying on git."""
    files: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(REPO_ROOT).parts):
            continue
        files.append(path)
    return files


def list_rules() -> None:
    print("Credential rules (no escape hatch):")
    for name, description, _ in CREDENTIAL_RULES:
        print(f"  {name:22} {description}")
    print("Value rules:")
    print(f"  {'literal-password':22} password/secret with a literal (non-placeholder) value")
    print(f"  {'unexpected-ipv4':22} any IPv4 literal outside the placeholder ranges")
    print("Deployment rules (matched by SHA-256 digest, values not stored):")
    for rule, description in DENY_RULE_DESCRIPTIONS.items():
        count = sum(1 for value in DENY_DIGESTS.values() if value == rule)
        print(f"  {rule:22} {description} ({count} value(s))")
    print()
    print("Allowed IPv4 ranges:")
    for pattern, reason in ALLOWED_IPV4:
        print(f"  {pattern.pattern:40} {reason}")
    print()
    print("Note: the two RFC 1918 ranges other than 10.0.0.0/24 are")
    print("      deliberately not allowed. Only 10.0.0.0/24 is used for")
    print("      private addressing in these documents.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="files to scan")
    parser.add_argument("--scan-all", action="store_true", help="scan the whole worktree")
    parser.add_argument("--list-rules", action="store_true", help="print the rule table")
    args = parser.parse_args()

    if args.list_rules:
        list_rules()
        return 0

    if args.scan_all:
        targets = git_tracked_files() or walk_worktree()
    elif args.paths:
        targets = [Path(p).resolve() for p in args.paths]
    else:
        parser.print_help()
        return 2

    total = 0
    for path in sorted(set(targets)):
        if not path.is_file():
            continue
        text = read_text(path)
        if text is None:
            continue
        violations = scan_text(path, text)
        if violations:
            rel = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
            print(f"\n{rel}")
            for lineno, name, message in violations:
                print(f"  line {lineno:<5} [{name}] {message}")
            total += len(violations)

    if total:
        print(f"\n{total} sanitization violation(s) found.")
        print("See docs/00-prerequisites/04-sanitization-rules.md for the allow-list and the manual review checklist.")
        return 1

    scanned = len([p for p in set(targets) if p.is_file()])
    print(f"Sanitization check passed ({scanned} file(s) scanned).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
