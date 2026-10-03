"""Synthetic fixtures only: no private lab values or real credentials."""

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_public_content.py"
SPEC = importlib.util.spec_from_file_location("public_content", SCRIPT)
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class ContentTests(unittest.TestCase):
    def test_illustrative_address_is_allowed(self):
        self.assertEqual([], CHECK.inspect_text("note.md", "Use 10.77.50.12."))

    def test_other_address_is_rejected(self):
        value = "192." + "0.2.15"
        self.assertIn("IPv4 address outside the illustrative range", CHECK.inspect_text("note.md", value))

    def test_invalid_address_is_rejected(self):
        value = "999." + "999.999.999"
        self.assertIn("invalid IPv4-shaped value", CHECK.inspect_text("note.md", value))

    def test_private_key_header_is_rejected(self):
        value = "-----BEGIN " + "PRIVATE KEY-----"
        self.assertIn("private-key header", CHECK.inspect_text("note.md", value))

    def test_credential_assignment_is_rejected(self):
        value = "api_" + "key=" + "fixture" * 5
        self.assertIn("credential-like assignment", CHECK.inspect_text("note.md", value))

    def test_mac_is_rejected(self):
        value = ":".join(["ab"] * 6)
        self.assertIn("MAC address", CHECK.inspect_text("note.md", value))

    def test_email_is_rejected(self):
        value = "fixture" + "@" + "example.com"
        self.assertIn("email address", CHECK.inspect_text("note.md", value))

    def test_educational_secret_names_are_allowed(self):
        self.assertEqual([], CHECK.inspect_text("note.md", "Keep passwords, API keys, and TOTP seeds private."))

    def test_unclosed_fence_is_rejected(self):
        self.assertIn("unclosed Markdown code fence", CHECK.inspect_text("note.md", "```sh\nexample\n"))

    def test_closed_fence_is_allowed(self):
        self.assertEqual([], CHECK.inspect_text("note.md", "```sh\nexample\n```\n"))

    def test_obsidian_link_is_rejected(self):
        value = "[" + "[Private note]]"
        self.assertIn("Obsidian link needs a GitHub-compatible replacement", CHECK.inspect_text("note.md", value))

    def test_relative_file_link_is_allowed(self):
        errors = CHECK.local_link_findings("docs/page.md", "[Home](../README.md)", {"README.md"})
        self.assertEqual([], errors)

    def test_missing_file_link_is_rejected(self):
        self.assertIn("missing local link destination", CHECK.local_link_findings("README.md", "[Missing](missing.md)", set()))

    def test_external_and_fragment_links_are_skipped(self):
        self.assertEqual([], CHECK.local_link_findings("README.md", "[Web](https://example.com) [Part](#part)", set()))

    def test_escape_link_is_rejected(self):
        self.assertIn("local link escapes the repository", CHECK.local_link_findings("README.md", "[Outside](../private.md)", set()))

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "README.md").symlink_to("absent")
            _, errors = CHECK.read_worktree(root)
            self.assertIn(("README.md", "symlinks are not approved"), errors)

    def test_unapproved_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "export.xml").touch()
            _, errors = CHECK.read_worktree(root)
            self.assertIn(("export.xml", "file is not on the public allowlist"), errors)

    def test_staged_version_not_worktree_is_checked(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            page = root / "README.md"
            page.write_text("192." + "0.2.15", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            page.write_text("10.77.50.12", encoding="utf-8")
            contents, errors = CHECK.read_index(root)
            self.assertEqual([], errors)
            self.assertIn("IPv4 address outside the illustrative range", CHECK.inspect_text("README.md", contents["README.md"]))

    def test_parent_repository_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            nested = root / "nested"
            nested.mkdir()
            with self.assertRaises(ValueError):
                CHECK.read_index(nested)


if __name__ == "__main__":
    unittest.main()
