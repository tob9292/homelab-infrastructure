# Publication policy

## Public content

This repository contains selected, rewritten infrastructure documentation. The Obsidian vault and infrastructure exports remain private.

Publish roles, relationships, design decisions, and original procedures. Replace real internal addresses with the documented illustrative range, registered service domains with `example.com` names, and operational identities with generic names.

Keep these private:

- raw OPNsense, Proxmox, UniFi, and application exports;
- authentication databases, tokens, password hashes, TOTP seeds, and recovery codes;
- WireGuard QR codes and private keys;
- DNS-provider credentials and certificate private keys;
- backup archives, installers, logs, and workstation configuration;
- screenshots containing live identifiers or sensitive settings;
- the full vault, course material, copied vendor text, and its historical content.

Illustrative addresses keep the documentation focused on the architecture while preserving the privacy of live endpoint details.

## Before each commit

Run these commands **from this repository**, not from the parent infrastructure folder:

```sh
python3 scripts/check_public_content.py
python3 -B -m unittest discover -s tests -v
gitleaks dir --redact --no-banner .
git add .
python3 scripts/check_public_content.py --staged
git diff --cached --check
git diff --cached
```

Review the complete staged diff for sensitive information, accuracy, and formatting before committing. Use repository-local Git author settings with the no-reply email shown in your GitHub account settings if you want to keep your email private.

The public file allowlist is defined in `.gitignore` and the checker. Add each new public page to both lists after review. Use the staged check and manual review for every commit, including changes to previously tracked files.

Before pushing existing history, also run:

```sh
gitleaks git --redact --no-banner .
```

The custom checker inspects the current files or Git index. Gitleaks scans history for supported secret patterns. Manual review covers contextual details such as live identifiers, screenshots, and configuration information.

## First publication

Start with a new, empty repository and clean history containing the selected public files. Use private visibility for the initial upload and review, then make it public after approval. Retain the vault's history privately.

Select and add a license if you want to grant reuse permissions.

For the upload workflow, see [GitHub's locally hosted project guide](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).

## If a secret is exposed

Revoke or rotate the credential first. Then coordinate cleanup of the repository history and any retained copies, and review dependent credentials. See [GitHub's sensitive-data removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
