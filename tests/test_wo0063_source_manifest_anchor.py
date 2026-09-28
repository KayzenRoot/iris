"""WO0063: fail-closed original Git-base anchored source manifest regressions."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.verify_context_lock import (
    ContextLockError, MANDATORY_SOURCE_PATHS, verify_current_pr, verify_lock,
)

BASE = "a" * 40
TREE = "b" * 40
ANCHOR = ".engineering/context-locks/IRIS-WO-0000.json"
LOCK = ".engineering/context-locks/IRIS-WO-0063.json"
EXTRA = "docs/project-brain/14-BACKLOG.md"
REPLACEMENT = "docs/project-brain/12-LOCAL-DEPLOYMENT.md"


def pure_fixture():
    paths = sorted(MANDATORY_SOURCE_PATHS | {ANCHOR, EXTRA})
    blobs = {path: f"{index + 1:040x}" for index, path in enumerate(paths)}
    blobs[REPLACEMENT] = "f" * 40
    rows = [{"path": path, "gitBlobSha1": blobs[path]} for path in paths]
    lock = {
        "schemaVersion": "iris-context-lock-v1",
        "workOrder": "IRIS-WO-0063", "issue": 182,
        "baseSha": BASE, "baseTreeSha": TREE,
        "sourceSnapshot": {"algorithm": "Git blob SHA-1", "expected": len(rows),
                           "checked": len(rows), "matched": len(rows), "mismatches": 0},
        "criticalSources": rows,
        "sourceManifestAnchor": {"path": ANCHOR, "gitBlobSha1": blobs[ANCHOR]},
        "authorizedChangedFiles": [LOCK],
    }
    return lock, blobs, {LOCK}, set(paths)


class WO0063PureManifestTests(unittest.TestCase):
    def check(self, lock, blobs, changed, inherited):
        verify_lock(lock, base_sha=BASE, base_tree_sha=TREE,
                    base_blobs=blobs, changed_paths=changed, lock_path=LOCK,
                    inherited_source_paths=inherited)

    def test_01_original_manifest_passes(self):
        self.check(*pure_fixture())

    def test_02_omitted_nonmandatory_source_even_with_corrected_counts_fails(self):
        lock, blobs, changed, inherited = pure_fixture()
        lock["criticalSources"] = [row for row in lock["criticalSources"] if row["path"] != EXTRA]
        for field in ("expected", "checked", "matched"):
            lock["sourceSnapshot"][field] -= 1
        with self.assertRaisesRegex(ContextLockError, "missing inherited original-base"):
            self.check(lock, blobs, changed, inherited)

    def test_03_substituted_valid_nonmandatory_source_and_same_counts_fails(self):
        lock, blobs, changed, inherited = pure_fixture()
        target = next(row for row in lock["criticalSources"] if row["path"] == EXTRA)
        target.update(path=REPLACEMENT, gitBlobSha1=blobs[REPLACEMENT])
        with self.assertRaisesRegex(ContextLockError, "missing inherited original-base"):
            self.check(lock, blobs, changed, inherited)

    def test_04_forged_anchor_blob_fails(self):
        lock, blobs, changed, inherited = pure_fixture()
        lock["sourceManifestAnchor"]["gitBlobSha1"] = "d" * 40
        with self.assertRaisesRegex(ContextLockError, "anchor blob mismatch"):
            self.check(lock, blobs, changed, inherited)

    def test_05_untrusted_or_unavailable_original_manifest_fails(self):
        lock, blobs, changed, _ = pure_fixture()
        with self.assertRaisesRegex(ContextLockError, "missing trusted original-base"):
            self.check(lock, blobs, changed, None)

    def test_06_legacy_v1_without_anchor_still_works(self):
        lock, blobs, changed, _ = pure_fixture()
        del lock["sourceManifestAnchor"]
        self.check(lock, blobs, changed, None)

    def test_07_current_lock_must_pin_original_anchor_itself(self):
        lock, blobs, changed, inherited = pure_fixture()
        lock["criticalSources"] = [row for row in lock["criticalSources"] if row["path"] != ANCHOR]
        for field in ("expected", "checked", "matched"):
            lock["sourceSnapshot"][field] -= 1
        with self.assertRaisesRegex(ContextLockError, "anchor itself must be pinned"):
            self.check(lock, blobs, changed, inherited)


class WO0063RealGitManifestTests(unittest.TestCase):
    def git(self, root, *args):
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    def make_repo(self, root, *, omit=(), forge=False, wrong_anchor=False, weaker_older_anchor=False):
        self.git(root, "init", "-q")
        self.git(root, "config", "user.email", "ci@example.invalid")
        self.git(root, "config", "user.name", "CI Fixture")
        source_paths = sorted(MANDATORY_SOURCE_PATHS | {EXTRA})
        for path in source_paths:
            dst = root / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text("# Canonical base source " + path + "\n", encoding="utf-8")
        original_rows = [{"path": path, "gitBlobSha1": self.git_blob(root, path)}
                         for path in source_paths]
        anchor_file = root / ANCHOR
        anchor_file.parent.mkdir(parents=True, exist_ok=True)
        older_rows = ([row for row in original_rows if row["path"] != EXTRA]
                      if weaker_older_anchor else original_rows)
        anchor_file.write_text(json.dumps({
            "schemaVersion": "iris-context-lock-v1",
            "criticalSources": older_rows,
            "sourceSnapshot": {"expected": len(older_rows),
                               "checked": len(older_rows), "matched": len(older_rows)}
        }), encoding="utf-8")
        if weaker_older_anchor:
            newer = root / ".engineering/context-locks/IRIS-WO-0001.json"
            newer.write_text(json.dumps({
                "schemaVersion": "iris-context-lock-v1",
                "criticalSources": original_rows,
                "sourceSnapshot": {"expected": len(original_rows),
                                   "checked": len(original_rows), "matched": len(original_rows)}
            }), encoding="utf-8")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "trusted-base")
        base, tree = self.git(root, "rev-parse", "HEAD"), self.git(root, "rev-parse", "HEAD^{tree}")
        inherited = set(source_paths) | {ANCHOR}
        actual_rows = [{"path": path, "gitBlobSha1": self.git(root, "rev-parse", f"HEAD:{path}")}
                       for path in sorted(inherited - set(omit))]
        script = root / "scripts" / "offline_probe.py"
        script.parent.mkdir(exist_ok=True)
        script.write_text("# deterministic test-only PR change\n", encoding="utf-8")
        lock = {
            "schemaVersion": "iris-context-lock-v1", "workOrder": "IRIS-WO-0063", "issue": 182,
            "baseSha": base, "baseTreeSha": tree,
            "sourceSnapshot": {"algorithm": "Git blob SHA-1", "baseSha": base,
                               "baseTreeSha": tree, "expected": len(actual_rows),
                               "checked": len(actual_rows), "matched": len(actual_rows), "mismatches": 0},
            "criticalSources": actual_rows,
            "sourceManifestAnchor": {"path": ".engineering/context-locks/does-not-exist.json"
                                    if wrong_anchor else ANCHOR,
                                    "gitBlobSha1": "e" * 40 if forge
                                    else self.git(root, "rev-parse", f"HEAD:{ANCHOR}")},
            "authorizedChangedFiles": [LOCK, "scripts/offline_probe.py"],
        }
        path = root / LOCK
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(lock), encoding="utf-8")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "current-head")
        return base, self.git(root, "rev-parse", "HEAD")

    def git_blob(self, root, path):
        # The trusted original base Git blob is reconstructed by Git itself.
        return self.git(root, "hash-object", str(root / path))

    def test_08_real_git_anchor_accepts_all_inherited_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.make_repo(root)
            self.assertEqual(verify_current_pr(root, base_sha=base, head_sha=head), [LOCK])

    def test_09_real_git_missing_optional_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.make_repo(root, omit={EXTRA})
            with self.assertRaisesRegex(ContextLockError, "missing inherited original-base"):
                verify_current_pr(root, base_sha=base, head_sha=head)

    def test_10_real_git_forged_original_anchor_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.make_repo(root, forge=True)
            with self.assertRaisesRegex(ContextLockError, "anchor blob mismatch"):
                verify_current_pr(root, base_sha=base, head_sha=head)

    def test_11_real_git_missing_original_anchor_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.make_repo(root, wrong_anchor=True)
            with self.assertRaisesRegex(ContextLockError, "anchor blob mismatch"):
                verify_current_pr(root, base_sha=base, head_sha=head)

    def test_12_older_weaker_anchor_cannot_omit_latest_original_optional_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.make_repo(root, omit={EXTRA}, weaker_older_anchor=True)
            with self.assertRaisesRegex(ContextLockError, "not the latest original-base Context Lock"):
                verify_current_pr(root, base_sha=base, head_sha=head)


if __name__ == "__main__":
    unittest.main()
