# Automation and documentation workflow

## Operational automation

The lab uses Linux tooling to reduce repetitive maintenance:

| Automation | Function |
| --- | --- |
| Scheduled Proxmox workload backups | Create nightly Zstandard snapshot archives of both VMs and all five LXCs |
| Host-configuration systemd timer | Capture daily Proxmox host rebuild configuration, systemd units, `udev` rules, and SHA-256 checksums |
| Weekly LXC `pct-fstrim.timer` | Trim all running LXC filesystems so freed blocks are reclaimed in LVM-thin storage |
| Weekly Paperless-ngx backup timer | Run `document_exporter` and atomic `pg_dump` on Docker01 ahead of the nightly VM backup |
| Public-portfolio sanitization checks | Enforce allowlist, secret/IP/link scanning, unit tests, and PNG fingerprint verification locally and in GitHub Actions CI |

The operational backup scripts and systemd timers are maintained directly on the Proxmox and Docker01 hosts.

## Publication boundary

Operational configuration and recovery material stay in the private Obsidian vault and host backup archives. Publication follows a separate review workflow that rewrites selected architecture and procedures into sanitized Markdown using illustrative `10.77.0.0/16` addresses and `example.com` domains before running automated checks.

## Documentation structure

The private Obsidian vault distinguishes:

- **Platform notes:** current architecture, ownership, and configuration.
- **Runbooks:** repeatable procedures, validation steps, and recovery paths.
- **Troubleshooting notes:** symptoms, diagnosis, and known resolutions.
- **Projects and learning:** changes in progress and personal study material.

Each note has one primary purpose. Related topics link to their owning notes, avoiding duplicated configuration tables that drift apart.

The public repository presents selected infrastructure documentation using GitHub-compatible links and Mermaid diagrams. Course notes, vendor-document copies, personal archives, and operational exports remain private.

## Repository tooling

[The public-content checker](../scripts/check_public_content.py) is implemented in this repository. It checks the approved file list, common sensitive-data patterns, illustrative IPv4 addressing, local Markdown links, and fingerprints of the reviewed PNG screenshots. [Unit tests](../tests/test_public_content.py) exercise its behavior.
