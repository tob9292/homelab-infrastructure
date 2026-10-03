#!/usr/bin/env python3
"""Review current or staged portfolio files without printing matched values.

Checks the file allowlist, sensitive-data patterns, and local Markdown links.
Run alongside Gitleaks and manual review. Uses Python's standard library.
"""

import argparse
import ipaddress
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit


APPROVED_FILES = frozenset({
    ".gitignore",
    "README.md",
    "docs/architecture.md",
    "docs/network-and-security.md",
    "docs/dns-and-https.md",
    "docs/backup-and-recovery.md",
    "docs/android-vpn.md",
    "docs/automation-and-documentation.md",
    "docs/publication-policy.md",
    "docs/runbooks/firewall-change.md",
    "docs/runbooks/dns-troubleshooting.md",
    "scripts/check_public_content.py",
    "tests/test_public_content.py",
})
ILLUSTRATIVE_NETWORK = ipaddress.ip_network("10.77.0.0/16")
MAX_FILE_BYTES = 128 * 1024
IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
LINK = re.compile(r"!?\[[^\]\n]*\]\(([^\s)]+)\)")
SENSITIVE_PATTERNS = (
    ("private-key header", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
    ("MAC address", re.compile(r"(?i)\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b")),
    ("email address", re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")),
    ("personal filesystem path", re.compile(r"/(?:var/home|home|run/media)/[\w.-]+/")),
    ("credential-like assignment", re.compile(
        r"(?im)\b(?:password|passwd|api[_-]?key|api[_-]?secret|access[_-]?token|"
        r"otp[_-]?seed|private[_-]?key|presharedkey)\s*[:=]\s*[\"']?"
        r"[A-Za-z0-9/+_.=-]{12,}"
    )),
)


def inspect_text(name, content):
    """Return finding labels only; never return captured sensitive values."""
    findings = []
    for label, pattern in SENSITIVE_PATTERNS:
        if pattern.search(content):
            findings.append(label)
    for match in IPV4.finditer(content):
        try:
            address = ipaddress.ip_address(match.group())
        except ValueError:
            findings.append("invalid IPv4-shaped value")
            continue
        if address not in ILLUSTRATIVE_NETWORK:
            findings.append("IPv4 address outside the illustrative range")
    if name.endswith(".md"):
        if "[[" in content:
            findings.append("Obsidian link needs a GitHub-compatible replacement")
        fence = None
        for line in content.splitlines():
            match = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
            if not match:
                continue
            marker, remainder = match.groups()
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence) and not remainder.strip():
                fence = None
        if fence is not None:
            findings.append("unclosed Markdown code fence")
    return sorted(set(findings))


def local_link_findings(name, content, available):
    """Check file destinations for the inline links used in these pages."""
    findings = []
    for match in LINK.finditer(content):
        destination = match.group(1)
        parsed = urlsplit(destination)
        if parsed.scheme or destination.startswith("#"):
            continue
        if parsed.netloc or destination.startswith("/"):
            findings.append("nonportable local link")
            continue
        parts = list(PurePosixPath(name).parent.parts)
        for part in PurePosixPath(unquote(parsed.path)).parts:
            if part == "..":
                if not parts:
                    findings.append("local link escapes the repository")
                    break
                parts.pop()
            elif part != ".":
                parts.append(part)
        else:
            if "/".join(parts) not in available:
                findings.append("missing local link destination")
    return sorted(set(findings))


def read_worktree(root):
    contents, errors = {}, []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        name = relative.as_posix()
        if path.is_symlink():
            errors.append((name, "symlinks are not approved"))
            continue
        if path.is_dir():
            continue
        if name not in APPROVED_FILES:
            errors.append((name, "file is not on the public allowlist"))
            continue
        data = path.read_bytes()
        if len(data) > MAX_FILE_BYTES:
            errors.append((name, "file exceeds the size limit"))
            continue
        try:
            contents[name] = data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append((name, "file is not UTF-8 text"))
    return contents, errors


def read_index(root):
    contents, errors = {}, []
    # Ensure a parent repository can never be mistaken for this portfolio repo.
    top = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=root, text=True)
    if Path(top.strip()).resolve() != root:
        raise ValueError("the selected folder is not this Git repository's root")
    entries = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=root)
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        metadata, raw_name = entry.split(b"\t", 1)
        mode, _, stage = metadata.decode("ascii").split()
        name = raw_name.decode("utf-8")
        if name not in APPROVED_FILES:
            errors.append((name, "staged file is not on the public allowlist"))
            continue
        if mode not in {"100644", "100755"} or stage != "0":
            errors.append((name, "only ordinary, conflict-free text files are approved"))
            continue
        data = subprocess.check_output(["git", "show", f":{name}"], cwd=root)
        if len(data) > MAX_FILE_BYTES:
            errors.append((name, "staged file exceeds the size limit"))
            continue
        try:
            contents[name] = data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append((name, "staged file is not UTF-8 text"))
    return contents, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--staged", action="store_true", help="inspect the entire Git index")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        contents, errors = read_index(root) if args.staged else read_worktree(root)
        for name in sorted(APPROVED_FILES - contents.keys()):
            errors.append((name, "required approved file is missing"))
        for name, content in contents.items():
            errors.extend((name, label) for label in inspect_text(name, content))
            if name.endswith(".md"):
                errors.extend((name, label) for label in local_link_findings(name, content, contents))
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        # Do not echo arbitrary command output or file content on failure.
        print(f"Cannot complete publication checks ({type(exc).__name__}).", file=sys.stderr)
        return 2
    if errors:
        for name, label in sorted(set(errors)):
            print(f"FAIL {name}: {label}")
        return 1
    scope = "staged" if args.staged else "current"
    print(f"PASS: {len(contents)} {scope} files; allowlist, content, and local links checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
