"""Prove that retired source-only audits survive as exact immutable Git objects."""
from __future__ import annotations

import hashlib
import subprocess
import unittest
from pathlib import Path

from scripts.historical_git_snapshot import (
    ORIGINAL_MAIN, ORIGINAL_TREE, ROOT, trusted_original_root,
)

ORIGINAL_INDEX = "19c8ff6126748cb89e53108bdff8289322071970"
ORIGINAL_LOCK = "abc9abf4195107db45809494fcfb309a1e85d233"
ORIGINAL_EVIDENCE = "722280c6f8faf38f14bac821d4a8b03d029e1f14"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


class OriginalSourceProvenanceTests(unittest.TestCase):
    """None of these proofs needs an installed external memory/runtime service."""

    def test_01_original_commit_is_exact_and_accessible(self):
        sha = git("rev-parse", f"{ORIGINAL_MAIN}^{{commit}}").decode().strip()
        tree = git("rev-parse", f"{ORIGINAL_MAIN}^{{tree}}").decode().strip()
        self.assertEqual(sha, ORIGINAL_MAIN)
        self.assertEqual(tree, ORIGINAL_TREE)

    def test_02_original_historical_index_git_blob_is_intact(self):
        original = git("cat-file", "blob", ORIGINAL_INDEX)
        oid = hashlib.sha1(b"blob " + str(len(original)).encode() + b"\0" + original).hexdigest()
        self.assertEqual(oid, ORIGINAL_INDEX)

    def test_03_original_signed_scope_and_author_time_artifacts_remain_immutable(self):
        for oid in (ORIGINAL_LOCK, ORIGINAL_EVIDENCE):
            with self.subTest(object=oid):
                self.assertEqual(git("cat-file", "-t", oid).strip(), b"blob")

    def test_04_retired_archive_materialization_is_exactly_source_bound(self):
        root = trusted_original_root()
        self.assertNotEqual(root, ROOT)
        path = root / "planning/MASTER-MODULE-INDEX.md"
        self.assertTrue(path.is_file())
        raw = path.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        self.assertEqual(actual, ORIGINAL_INDEX)
        self.assertTrue((root / "docs/project-brain/13-CHECKPOINT.md").is_file())


if __name__ == "__main__":
    unittest.main()
