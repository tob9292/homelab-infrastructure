"""Synthetic fixtures only: no private lab values or real credentials."""

import importlib.util
import hashlib
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_public_content.py"
SPEC = importlib.util.spec_from_file_location("public_content", SCRIPT)
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


IMAGE_NAME = "assets/screenshots/proxmox-overview.png"


def png_chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def synthetic_png(extra_chunk=None, width=1):
    """A synthetic black pixel, with no real screenshot or identifying data."""
    header = png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, 1, 8, 2, 0, 0, 0))
    extra = png_chunk(*extra_chunk) if extra_chunk else b""
    pixels = png_chunk(b"IDAT", zlib.compress(b"\0\0\0\0"))
    return CHECK.PNG_SIGNATURE + header + extra + pixels + png_chunk(b"IEND", b"")


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


class ImageTests(unittest.TestCase):
    def test_reviewed_png_is_allowed(self):
        data = synthetic_png()
        with patch.dict(CHECK.APPROVED_IMAGES, {IMAGE_NAME: hashlib.sha256(data).hexdigest()}):
            self.assertEqual([], CHECK.inspect_image(IMAGE_NAME, data))
            self.assertEqual(("", []), CHECK.decode_approved(IMAGE_NAME, data))

    def test_changed_image_is_rejected(self):
        self.assertIn("image differs from the visually reviewed version", CHECK.inspect_image(IMAGE_NAME, synthetic_png()))

    def test_non_png_is_rejected(self):
        self.assertEqual(["image is not a PNG"], CHECK.inspect_image(IMAGE_NAME, b"not an image"))

    def test_png_metadata_is_rejected_even_with_matching_fingerprint(self):
        data = synthetic_png((b"tEXt", b"Comment\0fixture"))
        with patch.dict(CHECK.APPROVED_IMAGES, {IMAGE_NAME: hashlib.sha256(data).hexdigest()}):
            self.assertIn("PNG contains unexpected or metadata chunks", CHECK.inspect_image(IMAGE_NAME, data))

    def test_truncated_png_is_rejected(self):
        self.assertIn("truncated PNG", CHECK.inspect_image(IMAGE_NAME, synthetic_png()[:-1]))

    def test_bad_chunk_checksum_is_rejected(self):
        data = bytearray(synthetic_png())
        data[-1] ^= 1
        self.assertIn("invalid PNG chunk checksum", CHECK.inspect_image(IMAGE_NAME, bytes(data)))

    def test_trailing_data_is_rejected(self):
        data = synthetic_png() + b"fixture"
        self.assertIn("PNG has an invalid end or trailing data", CHECK.inspect_image(IMAGE_NAME, data))

    def test_missing_pixel_chunk_is_rejected(self):
        data = CHECK.PNG_SIGNATURE + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + png_chunk(b"IEND", b"")
        self.assertIn("PNG is missing required chunks", CHECK.inspect_image(IMAGE_NAME, data))

    def test_oversized_image_is_rejected(self):
        self.assertEqual(["image exceeds the size limit"], CHECK.inspect_image(IMAGE_NAME, b"\0" * (CHECK.MAX_IMAGE_BYTES + 1)))

    def test_oversized_dimensions_are_rejected(self):
        self.assertIn("PNG dimensions are outside the approved limits", CHECK.inspect_image(IMAGE_NAME, synthetic_png(width=4097)))

    def test_markdown_image_link_is_checked(self):
        link = f"![Overview]({IMAGE_NAME})"
        self.assertEqual([], CHECK.local_link_findings("README.md", link, {IMAGE_NAME}))
        self.assertIn("missing local link destination", CHECK.local_link_findings("README.md", link, set()))

    def test_binary_image_is_included_in_worktree_link_destinations(self):
        data = synthetic_png()
        with tempfile.TemporaryDirectory() as folder, patch.dict(CHECK.APPROVED_IMAGES, {IMAGE_NAME: hashlib.sha256(data).hexdigest()}):
            root = Path(folder)
            image = root / IMAGE_NAME
            image.parent.mkdir(parents=True)
            image.write_bytes(data)
            contents, errors = CHECK.read_worktree(root)
            self.assertEqual([], errors)
            self.assertEqual("", contents[IMAGE_NAME])

    def test_unapproved_binary_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "unreviewed.png").write_bytes(synthetic_png())
            _, errors = CHECK.read_worktree(root)
            self.assertIn(("unreviewed.png", "file is not on the public allowlist"), errors)

    def test_staged_image_is_checked_instead_of_worktree(self):
        approved = synthetic_png()
        with tempfile.TemporaryDirectory() as folder, patch.dict(CHECK.APPROVED_IMAGES, {IMAGE_NAME: hashlib.sha256(approved).hexdigest()}):
            root = Path(folder)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            image = root / IMAGE_NAME
            image.parent.mkdir(parents=True)
            image.write_bytes(approved + b"fixture")
            subprocess.run(["git", "add", IMAGE_NAME], cwd=root, check=True)
            image.write_bytes(approved)
            contents, errors = CHECK.read_index(root)
            self.assertNotIn(IMAGE_NAME, contents)
            self.assertIn((IMAGE_NAME, "image differs from the visually reviewed version"), errors)

    def test_executable_staged_image_is_rejected(self):
        data = synthetic_png()
        with tempfile.TemporaryDirectory() as folder, patch.dict(CHECK.APPROVED_IMAGES, {IMAGE_NAME: hashlib.sha256(data).hexdigest()}):
            root = Path(folder)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            image = root / IMAGE_NAME
            image.parent.mkdir(parents=True)
            image.write_bytes(data)
            subprocess.run(["git", "add", IMAGE_NAME], cwd=root, check=True)
            subprocess.run(["git", "update-index", "--chmod=+x", IMAGE_NAME], cwd=root, check=True)
            _, errors = CHECK.read_index(root)
            self.assertIn((IMAGE_NAME, "images must not be executable"), errors)


if __name__ == "__main__":
    unittest.main()
