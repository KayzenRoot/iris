"""WO0065: exact-Git file-mode hardening for original-base sources and new locks."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.verify_context_lock import (
    ContextLockError, MANDATORY_SOURCE_PATHS, verify_current_pr, verify_lock,
)

AUTHORITY = "docs/project-brain/13-CHECKPOINT.md"
LOCK = ".engineering/context-locks/IRIS-WO-0065-TEST.json"
LINK_TARGET = "untrusted-canonical-source.md"


class ContextLockRealGitModeTests(unittest.TestCase):
    @staticmethod
    def git(root: Path, *args: str, payload: bytes | None = None) -> str:
        result = subprocess.run(
            ["git", *args], cwd=root, input=payload, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=True,
        )
        return result.stdout.decode("utf-8").strip()

    def fixture(self, root: Path, *, source_mode: str = "100644",
                lock_mode: str = "100644") -> tuple[str, str]:
        self.git(root, "init", "-q")
        self.git(root, "config", "user.email", "fixture@example.invalid")
        self.git(root, "config", "user.name", "Mode Fixture")
        for path in sorted(MANDATORY_SOURCE_PATHS):
            file = root / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("# Canonical original authority: " + path + "\n", encoding="utf-8")
        self.git(root, "add", "-A")
        if source_mode == "100755":
            self.git(root, "update-index", "--chmod=+x", AUTHORITY)
        elif source_mode == "120000":
            oid = self.git(root, "hash-object", "-w", "--stdin", payload=LINK_TARGET.encode())
            self.git(root, "update-index", "--add", "--cacheinfo", f"120000,{oid},{AUTHORITY}")
        self.git(root, "commit", "-q", "-m", "mode-controlled trusted original base")
        base = self.git(root, "rev-parse", "HEAD")
        base_tree = self.git(root, "rev-parse", "HEAD^{tree}")
        rows = [
            {"path": path, "gitBlobSha1": self.git(root, "rev-parse", f"{base}:{path}")}
            for path in sorted(MANDATORY_SOURCE_PATHS)
        ]
        lock = {
            "schemaVersion": "iris-context-lock-v1", "workOrder": "IRIS-WO-0065",
            "issue": 186, "baseSha": base, "baseTreeSha": base_tree,
            "sourceSnapshot": {
                "algorithm": "Git blob SHA-1", "expected": len(rows),
                "checked": len(rows), "matched": len(rows), "mismatches": 0,
            },
            "criticalSources": rows, "authorizedChangedFiles": [LOCK],
        }
        file = root / LOCK
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(lock), encoding="utf-8")
        self.git(root, "add", "--", LOCK)
        if lock_mode == "100755":
            self.git(root, "update-index", "--chmod=+x", LOCK)
        elif lock_mode == "120000":
            oid = self.git(root, "hash-object", "-w", "--stdin", payload=b"other-lock.json")
            self.git(root, "update-index", "--add", "--cacheinfo", f"120000,{oid},{LOCK}")
        self.git(root, "commit", "-q", "-m", "mode-controlled proposed Context Lock")
        return base, self.git(root, "rev-parse", "HEAD")

    def test_01_all_regular_exact_git_sources_and_lock_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root)
            self.assertEqual(verify_current_pr(root, base_sha=base, head_sha=head), [LOCK])

    def test_02_base_canonical_symlink_rejected_even_with_correct_git_blob_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root, source_mode="120000")
            with self.assertRaisesRegex(ContextLockError, "pinned critical source.*mode 100644"):
                verify_current_pr(root, base_sha=base, head_sha=head)

    def test_03_base_executable_canonical_document_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root, source_mode="100755")
            with self.assertRaisesRegex(ContextLockError, "pinned critical source.*mode 100644"):
                verify_current_pr(root, base_sha=base, head_sha=head)

    def test_04_head_executable_lock_rejected_before_json_parse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root, lock_mode="100755")
            with self.assertRaisesRegex(ContextLockError, "changed Context Lock.*mode 100644"):
                verify_current_pr(root, base_sha=base, head_sha=head)

    def test_05_head_symlink_lock_rejected_before_json_parse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root, lock_mode="120000")
            with self.assertRaisesRegex(ContextLockError, "changed Context Lock.*mode 100644"):
                verify_current_pr(root, base_sha=base, head_sha=head)

    def test_06_pure_optional_mode_argument_rejects_executable(self):
        paths = sorted(MANDATORY_SOURCE_PATHS)
        pins = {path: f"{index + 1:040x}" for index, path in enumerate(paths)}
        lock = {
            "schemaVersion": "iris-context-lock-v1", "workOrder": "IRIS-WO-0065",
            "issue": 186, "baseSha": "a" * 40, "baseTreeSha": "b" * 40,
            "sourceSnapshot": {
                "algorithm": "Git blob SHA-1", "expected": len(paths),
                "checked": len(paths), "matched": len(paths), "mismatches": 0,
            },
            "criticalSources": [{"path": p, "gitBlobSha1": pins[p]} for p in paths],
            "authorizedChangedFiles": [LOCK],
        }
        modes = {path: "100644" for path in paths}
        modes[AUTHORITY] = "100755"
        with self.assertRaisesRegex(ContextLockError, "pinned critical source.*mode 100644"):
            verify_lock(
                lock, base_sha="a" * 40, base_tree_sha="b" * 40,
                base_blobs=pins, changed_paths={LOCK}, lock_path=LOCK, base_modes=modes,
            )


if __name__ == "__main__":
    unittest.main()
