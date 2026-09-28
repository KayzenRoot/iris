"""WO0064 offline documentary regressions for verified prior WO0063 postmerge."""
import json
import re
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
H = "9cf00a7fb598f849c89915eb6ca8c86d13035585"
M = "6bb811bb4bf747903f3f8b754eca6e076947262b"
TREE = "619cabc4487112af98c63a552f86d18ad2490b7f"
ANCHOR = ".engineering/context-locks/IRIS-WO-0063-SOURCE-MANIFEST-ANCHOR.json"
LOCK = ".engineering/context-locks/IRIS-WO-0064-WO0063-CANONICAL-CLOSEOUT.json"

class WO0064CanonicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cp = (R / "docs/project-brain/13-CHECKPOINT.md").read_text(encoding="utf-8")
        cls.mirror = (R / ".engineering/CHECKPOINT.md").read_text(encoding="utf-8")
        cls.machine = json.loads((R / ".engineering/CHECKPOINT.json").read_text(encoding="utf-8"))
        cls.backlog = (R / "docs/project-brain/14-BACKLOG.md").read_text(encoding="utf-8")
        cls.lock = json.loads((R / LOCK).read_text(encoding="utf-8"))
        cls.evidence = json.loads((R / ".engineering/evidence/IRIS-WO-0064.json").read_text(encoding="utf-8"))
        cls.original_lock = json.loads((R / ANCHOR).read_text(encoding="utf-8"))
        cls.original_evidence = json.loads((R / ".engineering/evidence/IRIS-WO-0063.json").read_text(encoding="utf-8"))

    def test_01_exact_checkpoint_mirrors(self):
        self.assertEqual(self.cp, self.mirror)
        self.assertEqual(self.machine["nextStep"], self.cp.split("## NEXT STEP\n", 1)[1].strip())

    def test_02_original_wo0063_factual_completion(self):
        completed = self.cp.split("## COMPLETED\n", 1)[1].split("\n## IN PROGRESS", 1)[0]
        row = next((r for r in completed.splitlines() if "**IRIS-WO-0063 COMPLETED**" in r), "")
        for token in ("PR #183", H, M, TREE, "25/25", "10/10", "12 new", "Governance #36480957370", "Governance #36482361141", "4661/4661", "#182 CLOSED", "#5878378278"):
            self.assertIn(token, row)
        self.assertNotIn("PENDING AT AUTHORING", row)

    def test_03_next_step_preserves_owner_and_runtime_stop(self):
        n = self.machine["nextStep"]
        for token in ("NEXT_REQUIRED_OWNER_GATE", "actual M09 owner disposition", "B_FUTURE_OWNER_RECEIPT", "DIRECTION_ONLY", "C01 UNADOPTED_NOT_FROZEN", "H01–H04 OPEN HIGH_FOR_FUTURE_FREEZE", "M11 86", "M12 110", "M13 96", "M12/#128", "M54/#145", "M58/#146", "M60/#147", "NOT_RECEIVED", "SPECIFIED_NOT_EXECUTED", "NOT_ADMITTED", "original issues #82/#110/#112/#128/#145/#146/#147/#155 remain OPEN"):
            self.assertIn(token, n)
        self.assertNotIn("source-manifest-only IRIS-WO-0063", n)
        self.assertNotIn("WO0064 COMPLETED", n)

    def test_04_actual_backlog_excludes_stale_active_wo0063(self):
        active = self.backlog.split("## ACTIVE SCOPED EXISTING-KERNEL MAINTENANCE, NO NEW AUTHORITY", 1)[1].split("\n## VERIFIED SCOPED", 1)[0]
        verified = self.backlog.split("## VERIFIED SCOPED EXISTING-KERNEL MAINTENANCE, NO NEW AUTHORITY", 1)[1].split("\n## COMPLETED FOUNDATION", 1)[0]
        self.assertIn("None recorded", active)
        self.assertIsNone(re.search(r"(?m)^\s*[-*]\s+(?:\*\*)?WO0063\b", active))
        for token in ("WO0063", "PR #183", H, M, "25/25", "10/10", "Governance #36480957370", "Governance #36482361141", "4661/4661", "#182 CLOSED", "#5878378278", "WO0061"):
            self.assertIn(token, verified)
        self.assertNotIn("PENDING AT AUTHORING", verified)

    def test_05_immutable_original_author_time_history(self):
        self.assertEqual(self.original_evidence["workOrder"], "IRIS-WO-0063")
        self.assertEqual(self.original_evidence["ownHeadCI"], "PENDING")
        self.assertEqual(self.original_evidence["ownProtectedMerge"], "PENDING")
        self.assertEqual(self.original_evidence["ownIndependentExactMain"], "PENDING")
        self.assertEqual(self.original_evidence["correctionDelta"]["firstHeadGovernanceRun"], 36479809910)
        self.assertEqual(self.original_evidence["correctionDelta"]["greptileIndependentP1P2"]["classification"], "VALID_CHAT_FIXABLE")
        self.assertEqual(self.original_lock["sourceSnapshot"]["matched"], 25)

    def test_06_new_work_order_anchor_evidence_scope(self):
        self.assertEqual(self.lock["workOrder"], "IRIS-WO-0064")
        self.assertEqual(self.lock["issue"], 184)
        self.assertEqual(self.lock["baseSha"], M)
        self.assertEqual(self.lock["baseTreeSha"], TREE)
        self.assertEqual(self.lock["sourceManifestAnchor"]["path"], ANCHOR)
        prior = {r["path"] for r in self.original_lock["criticalSources"]}
        current = {r["path"] for r in self.lock["criticalSources"]}
        self.assertEqual(len(prior), 25)
        self.assertEqual(len(current), 26)
        self.assertTrue(prior | {ANCHOR} <= current)
        self.assertEqual(self.lock["sourceSnapshot"]["matched"], 26)
        self.assertEqual(self.evidence["originalSourcePins"], 26)
        self.assertEqual(self.evidence["authorizedChangedPaths"], self.lock["authorizedChangedFiles"])
        self.assertEqual(len(self.lock["authorizedChangedFiles"]), 9)
        self.assertEqual(self.evidence["newOfflineConsistencyTests"], 6)
        self.assertEqual(self.evidence["ownHeadCI"], "PENDING")
        self.assertEqual(self.evidence["ownProtectedMerge"], "PENDING")
        self.assertFalse(self.evidence["originalOwnerProofReceived"])
        self.assertFalse(self.evidence["actualPhysicalOrRuntimeAction"])
        self.assertEqual(self.evidence["nativeRuntime"], "NOT_ADMITTED")

if __name__ == "__main__":
    unittest.main()
