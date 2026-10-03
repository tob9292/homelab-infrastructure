#!/usr/bin/env python3
"""Review current or staged portfolio files without printing matched values.

Checks the file allowlist, sensitive-data patterns, local Markdown links,
and fingerprints of manually reviewed, metadata-free PNG screenshots.
Image fingerprints do not replace visual review of a new or changed image.
Run alongside Gitleaks and manual review. Uses Python's standard library.
"""

import argparse
import hashlib
import ipaddress
import re
import struct
import subprocess
import sys
import zlib
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit


APPROVED_TEXT_FILES = frozenset({
    ".gitignore",
    "README.md",
    "docs/architecture.md",
    "docs/network-and-security.md",
    "docs/dns-and-https.md",
    "docs/monitoring.md",
    "docs/backup-and-recovery.md",
    "docs/android-vpn.md",
    "docs/automation-and-documentation.md",
    "docs/runbooks/firewall-change.md",
    "docs/runbooks/dns-troubleshooting.md",
    "scripts/check_public_content.py",
    "tests/test_public_content.py",
})
# Each fingerprint belongs to the final cropped/redacted PNG, not its source.
# Changing an image requires visual review before approving a new fingerprint.
APPROVED_IMAGES = {
    "assets/screenshots/proxmox-overview.png": "c7568c3a2110c5bf582dcd148b0814e8764b5b8f9004aa784a9a5fdc17ba09f9",
    "assets/screenshots/opnsense-dashboard.png": "070ced4f39e356018f12bdc47dda0c7ea92bfcc13180458a9e24c8da844d3e76",
    "assets/screenshots/opnsense-iot-rules.png": "4883a3180d8f31ab8883f344d3ce4e161f93c2be2cfb0d26d30f15f81a16f94e",
    "assets/screenshots/unifi-networks.png": "aeb860fea8ad894fb87552d2110b800543174592431ffdd137e4ced9879bd38b",
    "assets/screenshots/unifi-devices.png": "1f8c2c8349d5f02a0af560b525dfba358b21ffd16d1664e5c27ce6781f6aede0",
    "assets/screenshots/unifi-switch-ports.png": "b56ab9f75c17bfffd7748bd72e420d6bb27727560ed2345c2a57d3b8dc21e5e1",
    "assets/screenshots/adguard-dashboard.png": "7a5999680719d15902775b5724a4ac2b793f3d4065c34b64698b7ab4d754a4c4",
    "assets/screenshots/npmplus-proxy-hosts.png": "d9fee7fe3a06c446f7d15bfcefbd33eb12bc62de055cfafc4a19d11c33e55fbb",
    "assets/screenshots/npmplus-certificates.png": "114adc6f1dd9add6e35c7ea4241faa2b20c9dc8088c452b617d66a3fdf1d927b",
    "assets/screenshots/uptime-kuma.png": "4cc619db27eddeaff1030324c8dbf80a1def2804fc4c335475045f0ba64db1fc",
    "assets/screenshots/proxmox-backup-job.png": "21c0e3076380a528a140aa9f6e24ebd768b4f106546d6c217b96a1aa58d29b3a",
    "assets/screenshots/proxmox-backup-retention.png": "0d47c01b0091a80f5e36b468c9060309bf93b0951f50fcc8435e2ce3cad5dd6b",
}
APPROVED_FILES = APPROVED_TEXT_FILES | APPROVED_IMAGES.keys()
ILLUSTRATIVE_NETWORK = ipaddress.ip_network("10.77.0.0/16")
MAX_FILE_BYTES = 128 * 1024
MAX_IMAGE_BYTES = 4 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
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


def inspect_image(name, data):
    """Validate the PNG container and the exact visually reviewed fingerprint."""
    findings = []
    if len(data) > MAX_IMAGE_BYTES:
        return ["image exceeds the size limit"]
    if not data.startswith(PNG_SIGNATURE):
        return ["image is not a PNG"]
    offset, chunks = len(PNG_SIGNATURE), []
    while offset < len(data):
        if offset + 12 > len(data):
            return ["truncated PNG"]
        size = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + size
        if end > len(data):
            return ["truncated PNG"]
        payload = data[offset + 8:offset + 8 + size]
        crc = struct.unpack_from(">I", data, end - 4)[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            return ["invalid PNG chunk checksum"]
        if kind not in {b"IHDR", b"IDAT", b"IEND"}:
            findings.append("PNG contains unexpected or metadata chunks")
        if kind == b"IHDR":
            if chunks or size != 13:
                return ["invalid PNG header"]
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if not (0 < width <= 4096 and 0 < height <= 4096):
                findings.append("PNG dimensions are outside the approved limits")
            if depth != 8 or color not in {2, 6} or (compression, filtering, interlace) != (0, 0, 0):
                findings.append("PNG encoding is not approved")
        chunks.append(kind)
        offset = end
        if kind == b"IEND":
            if size != 0 or offset != len(data):
                findings.append("PNG has an invalid end or trailing data")
            break
    if not chunks or chunks[0] != b"IHDR" or chunks[-1] != b"IEND" or b"IDAT" not in chunks:
        findings.append("PNG is missing required chunks")
    if hashlib.sha256(data).hexdigest() != APPROVED_IMAGES.get(name):
        findings.append("image differs from the visually reviewed version")
    return sorted(set(findings))


def decode_approved(name, data):
    """Use an empty text value for valid images so file-link checks include them."""
    if name in APPROVED_IMAGES:
        findings = inspect_image(name, data)
        return (None if findings else ""), findings
    if len(data) > MAX_FILE_BYTES:
        return None, ["file exceeds the size limit"]
    try:
        return data.decode("utf-8"), []
    except UnicodeDecodeError:
        return None, ["file is not UTF-8 text"]


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
        content, findings = decode_approved(name, data)
        errors.extend((name, label) for label in findings)
        if content is not None:
            contents[name] = content
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
            errors.append((name, "only ordinary, conflict-free files are approved"))
            continue
        if name in APPROVED_IMAGES and mode != "100644":
            errors.append((name, "images must not be executable"))
            continue
        data = subprocess.check_output(["git", "show", f":{name}"], cwd=root)
        content, findings = decode_approved(name, data)
        errors.extend((name, label) for label in findings)
        if content is not None:
            contents[name] = content
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
    print(f"PASS: {len(contents)} {scope} files; allowlist, text, local links, and approved PNG fingerprints checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
