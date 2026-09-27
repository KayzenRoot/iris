from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.verify_context_lock import (
    ContextLockError,
    reject_duplicate_json_keys,
    safe_path,
    verify_current_pr,
    verify_lock,
)


BASE = "a" * 40
TREE = "b" * 40
LOCK_PATH = ".engineering/context-locks/IRIS-WO-0018.json"
SOURCE_PATH = ".engineering/SOURCE-HIERARCHY.md"
BLOB = "c" * 40


def fixture():
    lock = {
        "schemaVersion": "iris-context-lock-v1",
        "workOrder": "IRIS-WO-0018",
        "issue": 120,
        "baseSha": BASE,
        "baseTreeSha": TREE,
        "sourceSnapshot": {
            "algorithm": "Git blob SHA-1",
            "baseSha": BASE,
            "baseTreeSha": TREE,
            "expected": 1,
            "checked": 1,
            "matched": 1,
            "mismatches": 0,
        },
        "criticalSources": [{"path": SOURCE_PATH, "gitBlobSha1": BLOB}],
        "authorizedChangedFiles": [LOCK_PATH, "scripts/verify_context_lock.py"],
    }
    return lock, {SOURCE_PATH: BLOB}, {LOCK_PATH, "scripts/verify_context_lock.py"}


class ContextLockPureTests(unittest.TestCase):
    def check(self, lock, sources, changed):
        verify_lock(lock, base_sha=BASE, base_tree_sha=TREE, base_blobs=sources, changed_paths=changed, lock_path=LOCK_PATH)

    def test_valid_exact_lock_and_scope(self):
        self.check(*fixture())

    def test_forged_source_sha_fails_closed(self):
        lock, sources, changed = fixture()
        lock["criticalSources"][0]["gitBlobSha1"] = "d" * 40
        with self.assertRaisesRegex(ContextLockError, "Git blob mismatch"):
            self.check(lock, sources, changed)

    def test_missing_source_fails_closed(self):
        lock, sources, changed = fixture()
        with self.assertRaisesRegex(ContextLockError, "mismatch or absent"):
            self.check(lock, {}, changed)

    def test_duplicate_source_fails_closed(self):
        lock, sources, changed = fixture()
        lock["criticalSources"].append(deepcopy(lock["criticalSources"][0]))
        with self.assertRaisesRegex(ContextLockError, "duplicate critical source"):
            self.check(lock, sources, changed)

    def test_false_count_fails_closed(self):
        lock, sources, changed = fixture()
        lock["sourceSnapshot"]["matched"] = 0
        with self.assertRaisesRegex(ContextLockError, "count matched mismatch"):
            self.check(lock, sources, changed)

    def test_stale_base_fails_closed(self):
        lock, sources, changed = fixture()
        lock["baseSha"] = "d" * 40
        with self.assertRaisesRegex(ContextLockError, "stale/mismatched"):
            self.check(lock, sources, changed)

    def test_wrong_base_tree_fails_closed(self):
        lock, sources, changed = fixture()
        lock["baseTreeSha"] = "d" * 40
        with self.assertRaisesRegex(ContextLockError, "base tree mismatch"):
            self.check(lock, sources, changed)

    def test_unauthorized_pr_path_fails_closed(self):
        lock, sources, changed = fixture()
        changed.add("iris_resource_twin/recovery.py")
        with self.assertRaisesRegex(ContextLockError, "unauthorized PR diff"):
            self.check(lock, sources, changed)

    def test_lock_itself_must_be_changed_and_authorized(self):
        lock, sources, changed = fixture()
        with self.assertRaisesRegex(ContextLockError, "new lock must itself"):
            self.check(lock, sources, {"scripts/verify_context_lock.py"})

    def test_duplicate_allowlist_entry_fails_closed(self):
        lock, sources, changed = fixture()
        lock["authorizedChangedFiles"].append(LOCK_PATH)
        with self.assertRaisesRegex(ContextLockError, "duplicate authorized"):
            self.check(lock, sources, changed)

    def test_source_path_traversal_fails_closed(self):
        lock, sources, changed = fixture()
        lock["criticalSources"][0]["path"] = "../secrets"
        with self.assertRaisesRegex(ContextLockError, "noncanonical"):
            self.check(lock, sources, changed)

    def test_absolute_and_windows_paths_fail_closed(self):
        for path in ("/tmp/lock.json", r"C:\temp\lock.json", "docs//note.md"):
            with self.subTest(path=path):
                with self.assertRaises(ContextLockError):
                    safe_path(path, "fixture")

    def test_duplicate_json_key_fails_closed(self):
        with self.assertRaisesRegex(ContextLockError, "duplicate JSON key"):
            json.loads('{"baseSha": "x", "baseSha": "y"}', object_pairs_hook=reject_duplicate_json_keys)

    def test_declared_nonzero_mismatches_fails_closed(self):
        lock, sources, changed = fixture()
        lock["sourceSnapshot"]["mismatches"] = 1
        with self.assertRaisesRegex(ContextLockError, "mismatches must be zero"):
            self.check(lock, sources, changed)


class ContextLockRealGitTests(unittest.TestCase):
    def git(self, root: Path, *args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    def setup_repo(self, root: Path, *, unauthorized: bool = False, with_lock: bool = True):
        self.git(root, "init", "-q")
        self.git(root, "config", "user.email", "ci@example.invalid")
        self.git(root, "config", "user.name", "CI Fixture")
        source = root / SOURCE_PATH
        source.parent.mkdir(parents=True)
        source.write_text("# Hierarchy\n", encoding="utf-8")
        self.git(root, "add", SOURCE_PATH)
        self.git(root, "commit", "-q", "-m", "base")
        base = self.git(root, "rev-parse", "HEAD")
        tree = self.git(root, "rev-parse", "HEAD^{tree}")
        blob = self.git(root, "rev-parse", f"HEAD:{SOURCE_PATH}")
        script = root / "scripts" / "verify_context_lock.py"
        script.parent.mkdir()
        script.write_text("# changed script fixture\n", encoding="utf-8")
        allowed = [LOCK_PATH, "scripts/verify_context_lock.py"]
        if with_lock:
            lock = {
                "schemaVersion": "iris-context-lock-v1",
                "workOrder": "IRIS-WO-0018", "issue": 120,
                "baseSha": base, "baseTreeSha": tree,
                "sourceSnapshot": {"algorithm": "Git blob SHA-1", "expected": 1, "checked": 1, "matched": 1, "mismatches": 0},
                "criticalSources": [{"path": SOURCE_PATH, "gitBlobSha1": blob}],
                "authorizedChangedFiles": allowed,
            }
            path = root / LOCK_PATH
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(lock), encoding="utf-8")
        if unauthorized:
            outside = root / "iris_resource_twin" / "recovery.py"
            outside.parent.mkdir()
            outside.write_text("# out of scope\n", encoding="utf-8")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "candidate")
        return base, self.git(root, "rev-parse", "HEAD")

    def test_real_git_exact_tree_blobs_and_pr_diff_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.setup_repo(root)
            self.assertEqual(verify_current_pr(root, base_sha=base, head_sha=head), [LOCK_PATH])

    def test_real_git_unauthorized_diff_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.setup_repo(root, unauthorized=True)
            with self.assertRaisesRegex(ContextLockError, "unauthorized PR diff"):
                verify_current_pr(root, base_sha=base, head_sha=head)

    def test_real_git_missing_changed_lock_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.setup_repo(root, with_lock=False)
            with self.assertRaisesRegex(ContextLockError, "must change at least one"):
                verify_current_pr(root, base_sha=base, head_sha=head)

    def test_real_git_incorrect_checkout_head_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.setup_repo(root)
            with self.assertRaisesRegex(ContextLockError, "checkout is not the exact PR head"):
                verify_current_pr(root, base_sha=base, head_sha=base)


if __name__ == "__main__":
    unittest.main()
