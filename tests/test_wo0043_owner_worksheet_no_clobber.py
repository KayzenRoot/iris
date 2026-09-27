"""WO0043: avoid replacing directories created concurrently by users."""
from __future__ import annotations

import os
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from scripts.scaffold_m09_h03_owner_drafts import (
    FILES, ScaffoldError, build, write,
)
from scripts.verify_m09_h03_owner_routes import (
    PRIOR, ROOT, ROUTES, read,
)


class WO0043OwnerWorksheetNoClobberTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = build(read(ROOT, PRIOR), read(ROOT, ROUTES))

    def test_01_complete_nine_file_bundle_still_works(self):
        with TemporaryDirectory() as temp:
            target = Path(temp) / "forms"
            write(target, self.bundle)
            self.assertEqual({item.name for item in target.iterdir()}, FILES)
            self.assertIn("NOT APPROVED",
                          (target / "OWNER-DRAFTS-README.md").read_text())

    def test_02_preexisting_empty_directory_never_replaced(self):
        with TemporaryDirectory() as temp:
            target = Path(temp) / "empty"
            target.mkdir()
            before = target.stat()
            with self.assertRaisesRegex(ScaffoldError, "never overwrite"):
                write(target, self.bundle)
            after = target.stat()
            self.assertEqual((before.st_dev, before.st_ino),
                             (after.st_dev, after.st_ino))
            self.assertEqual(list(target.iterdir()), [])

    def test_03_preexisting_nonempty_directory_preserves_content(self):
        with TemporaryDirectory() as temp:
            target = Path(temp) / "existing"
            target.mkdir()
            sentinel = target / "original.txt"
            sentinel.write_text("real user data", encoding="utf-8")
            with self.assertRaisesRegex(ScaffoldError, "never overwrite"):
                write(target, self.bundle)
            self.assertEqual(sentinel.read_text(), "real user data")

    def test_04_racing_empty_directory_creation_is_rejected(self):
        with TemporaryDirectory() as temp:
            target = Path(temp) / "race"
            original_mkdir = Path.mkdir
            owned = {}
            def racing_mkdir(path, *args, **kwargs):
                if path == target:
                    original_mkdir(path)
                    owned["stat"] = target.stat()
                return original_mkdir(path, *args, **kwargs)
            with patch.object(Path, "mkdir", racing_mkdir):
                with self.assertRaisesRegex(ScaffoldError,
                                            "appeared during exclusive"):
                    write(target, self.bundle)
            now = target.stat()
            self.assertEqual((now.st_dev, now.st_ino),
                             (owned["stat"].st_dev, owned["stat"].st_ino))
            self.assertEqual(list(target.iterdir()), [])

    def test_05_racing_nonempty_directory_and_file_are_preserved(self):
        with TemporaryDirectory() as temp:
            target = Path(temp) / "race"
            original_mkdir = Path.mkdir
            def racing_mkdir(path, *args, **kwargs):
                if path == target:
                    original_mkdir(path)
                    (target / "external.txt").write_text("untouched")
                return original_mkdir(path, *args, **kwargs)
            with patch.object(Path, "mkdir", racing_mkdir):
                with self.assertRaisesRegex(ScaffoldError,
                                            "never overwrite"):
                    write(target, self.bundle)
            self.assertEqual((target / "external.txt").read_text(),
                             "untouched")

    def test_06_mid_write_failure_rolls_back_only_our_own_files(self):
        with TemporaryDirectory() as temp:
            target = Path(temp) / "forms"
            actual_open = Path.open
            calls = {"n": 0}
            def intermittent_open(path, *args, **kwargs):
                if path.parent == target:
                    calls["n"] += 1
                    if calls["n"] == 4:
                        raise OSError("injected disk write failure")
                return actual_open(path, *args, **kwargs)
            with patch.object(Path, "open", intermittent_open):
                with self.assertRaisesRegex(OSError, "injected"):
                    write(target, self.bundle)
            self.assertGreaterEqual(calls["n"], 4)
            self.assertFalse(target.exists())

    def test_07_concurrent_unexpected_file_survives_failed_write(self):
        with TemporaryDirectory() as temp:
            target = Path(temp) / "forms"
            actual_open = Path.open
            calls = {"n": 0}
            def intermittent_open(path, *args, **kwargs):
                if path.parent == target:
                    calls["n"] += 1
                    if calls["n"] == 4:
                        (target / "external.txt").write_text(
                            "preserve other writer", encoding="utf-8")
                        raise OSError("injected failure after external write")
                return actual_open(path, *args, **kwargs)
            with patch.object(Path, "open", intermittent_open):
                with self.assertRaisesRegex(OSError, "injected"):
                    write(target, self.bundle)
            self.assertTrue(target.exists())
            self.assertEqual({p.name for p in target.iterdir()},
                             {"external.txt"})
            self.assertEqual((target / "external.txt").read_text(),
                             "preserve other writer")

    def test_08_symlink_destination_does_not_modify_real_directory(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlink unavailable")
        with TemporaryDirectory() as temp:
            original = Path(temp) / "original"
            original.mkdir()
            sentinel = original / "unchanged.txt"
            sentinel.write_text("keep")
            link = Path(temp) / "forms"
            try:
                link.symlink_to(original, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            with self.assertRaisesRegex(ScaffoldError, "never overwrite"):
                write(link, self.bundle)
            self.assertEqual(sentinel.read_text(), "keep")
            self.assertTrue(link.is_symlink())

    def test_09_private_local_permissions_and_manifest_precheck(self):
        with TemporaryDirectory() as temp:
            target = Path(temp) / "forms"
            injected = dict(self.bundle)
            injected["../../foreign.txt"] = injected.pop("M54-draft.json")
            with self.assertRaisesRegex(ScaffoldError, "manifest"):
                write(target, injected)
            self.assertFalse(target.exists())
            write(target, self.bundle)
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(target.stat().st_mode) & 0o077, 0)
                self.assertTrue(all(
                    stat.S_IMODE(p.stat().st_mode) & 0o077 == 0
                    for p in target.iterdir()))


if __name__ == "__main__":
    unittest.main()
