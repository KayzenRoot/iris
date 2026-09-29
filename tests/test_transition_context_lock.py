"""Version-two source-lock transition: tamper and exact-scope refusals."""
from __future__ import annotations
import base64
from copy import deepcopy
import unittest

from scripts.verify_context_lock import (
    ContextLockError, MANDATORY_SOURCE_PATHS, verify_transition_lock,
    inherited_original_source_paths, decoded_source_path,
)

BASE = "a" * 40
TREE = "b" * 40
LOCK = ".engineering/context-locks/IRIS-WO-0067-STANDALONE-CURRENT.json"
ANCHOR = ".engineering/context-locks/IRIS-WO-0066-PRIOR.json"
EDIT = "scripts/validate_governance.py"
ADDED = "docs/new-note.md"


def encode(path: str) -> str:
    return base64.b64encode(path.encode("utf-8")).decode("ascii")


def fixture():
    base = {path: f"{i+1:040x}" for i, path in enumerate(
        sorted(MANDATORY_SOURCE_PATHS | {ANCHOR, EDIT}))}
    changed = {EDIT, LOCK, ADDED}
    inherited = set(MANDATORY_SOURCE_PATHS) | {ANCHOR}
    rows = [{"pathBase64": encode(p), "gitBlobSha1": base[p]}
            for p in sorted(changed & base.keys() | inherited)]
    lock = {
        "schemaVersion": "iris-context-lock-v2",
        "workOrder": "IRIS-WO-0067", "issue": 190,
        "baseSha": BASE, "baseTreeSha": TREE,
        "sourceSnapshot": {
            "algorithm": "Git blob SHA-1", "baseSha": BASE,
            "baseTreeSha": TREE, "expected": len(rows), "checked": len(rows),
            "matched": len(rows), "mismatches": 0,
        },
        "criticalSources": rows,
        "authorizedChangedFilesBase64": [encode(p) for p in sorted(changed)],
        "sourceManifestAnchor": {
            "pathBase64": encode(ANCHOR), "gitBlobSha1": base[ANCHOR],
        },
    }
    return lock, base, changed, inherited


class VersionTwoSourceLockTests(unittest.TestCase):
    def audit(self, lock, base, changed, inherited):
        verify_transition_lock(
            lock, base_sha=BASE, base_tree_sha=TREE, base_blobs=base,
            changed_paths=changed, lock_path=LOCK, inherited_source_paths=inherited)

    def test_01_original_source_and_full_scope_pass(self):
        self.audit(*fixture())

    def test_02_source_git_blob_tamper_rejected(self):
        lock, base, changed, prior = fixture()
        lock["criticalSources"][0]["gitBlobSha1"] = "f" * 40
        with self.assertRaisesRegex(ContextLockError, "fingerprint mismatch"):
            self.audit(lock, base, changed, prior)

    def test_03_unknown_actual_pr_diff_rejected(self):
        lock, base, changed, prior = fixture()
        changed.add("iris_resource_twin/recovery.py")
        with self.assertRaisesRegex(ContextLockError, "coverage"):
            self.audit(lock, base, changed, prior)

    def test_04_lost_inherited_prior_source_rejected(self):
        lock, base, changed, prior = fixture()
        lock["criticalSources"].pop()
        with self.assertRaisesRegex(ContextLockError, "coverage"):
            self.audit(lock, base, changed, prior)

    def test_05_duplicate_allowlist_rejected(self):
        lock, base, changed, prior = fixture()
        lock["authorizedChangedFilesBase64"].append(encode(ADDED))
        with self.assertRaisesRegex(ContextLockError, "duplicate"):
            self.audit(lock, base, changed, prior)

    def test_06_wrong_original_base_anchor_rejected(self):
        lock, base, changed, prior = fixture()
        lock["sourceManifestAnchor"]["gitBlobSha1"] = "f" * 40
        with self.assertRaisesRegex(ContextLockError, "anchor drift"):
            self.audit(lock, base, changed, prior)

    def test_07_unsafe_or_noncanonical_base64_rejected(self):
        for val in ("../secrets", encode("../private.json"), encode("safe//path")):
            with self.subTest(value=val), self.assertRaises(ContextLockError):
                decoded_source_path(val, "fixture")

    def test_08_old_original_anchor_is_source_verified(self):
        lock, base, changed, prior = fixture()
        original = {
            "schemaVersion": "iris-context-lock-v1",
            "criticalSources": [
                {"path": p, "gitBlobSha1": base[p]}
                for p in sorted(prior)
            ],
            "sourceSnapshot": {
                "expected": len(prior), "checked": len(prior),
                "matched": len(prior), "mismatches": 0,
            },
        }
        self.assertEqual(inherited_original_source_paths(original, base), prior)
        original["criticalSources"][0]["gitBlobSha1"] = "f" * 40
        with self.assertRaisesRegex(ContextLockError, "source mismatch"):
            inherited_original_source_paths(original, base)


if __name__ == "__main__":
    unittest.main()
