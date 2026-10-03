# Automation and documentation workflow

## Operational automation

The lab uses Linux tooling to reduce repetitive maintenance:

| Automation | Function |
| --- | --- |
| Scheduled Proxmox workload backups | Create VM and LXC recovery archives |
| Host-configuration systemd timer | Capture rebuild information and checksums |
| LXC administration-profile synchronization | Configure named SSH administration and maintain workstation SSH/Remmina entries |
| Hermes specialist profiles | Separate documentation, Proxmox inspection, and publication workflows |

The administration-profile synchronization tooling handles Debian/Ubuntu and Alpine containers, installs required SSH/sudo components, adds public keys, and preserves manually maintained workstation profiles. Stopped workloads are skipped. The operational scripts are maintained privately.

## Hermes access model

Specialist profiles run under a shared Linux account, with separate configuration, credentials, and working state for each task. Proxmox inspection uses read-only access. Documentation integration uses a dedicated unprivileged SSH identity with filesystem permissions scoped to the vault.

Publication follows a separate review workflow for selected, sanitized documentation. The vault and infrastructure backups remain private.

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
