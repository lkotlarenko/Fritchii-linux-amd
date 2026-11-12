#!/usr/bin/env python3
"""Regression tests for the unpacked Linux release privacy check."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ReleasePrivacyTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        self.private = self.root / "private-marker"

    def audit(self):
        return subprocess.run(
            [sys.executable, str(Path(__file__).with_name("audit_linux_release.py")),
             str(self.bundle), "--private-root", str(self.private)],
            capture_output=True, text=True,
        )

    def test_clean_binary(self):
        (self.bundle / "program").write_bytes(b"ELF\0public source\0")
        self.assertEqual(self.audit().returncode, 0)

    def test_marker_crossing_read_boundary(self):
        marker = os.fsencode(self.private)
        (self.bundle / "program").write_bytes(b"x" * (1024 * 1024 - 4) + marker)
        result = self.audit()
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(str(self.private), result.stdout + result.stderr)

    def test_user_data_filename(self):
        (self.bundle / "prod.keys").write_text("placeholder")
        self.assertEqual(self.audit().returncode, 1)

    def test_private_symlink(self):
        (self.bundle / "link").symlink_to(self.private)
        self.assertEqual(self.audit().returncode, 1)

    def test_does_not_read_external_symlink_contents(self):
        outside = self.root / "outside"
        outside.write_bytes(os.fsencode(self.private))
        (self.bundle / "link").symlink_to(outside)
        self.assertEqual(self.audit().returncode, 0)


if __name__ == "__main__":
    unittest.main()
