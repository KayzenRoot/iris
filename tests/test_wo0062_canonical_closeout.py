"""WO0062 offline documentary regressions for factual WO0061 completion."""
import json
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
H = "6102b5c8f8c39341eb3638407b73055d1dee552a"
M = "bd994626edee41d0587bbc5fffa6a1f61a15f029"
TREE = "2972459d08e248bbf3761771dd32cb9b5f981bcc"


class WO0062CanonicalCloseoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cp = (R / "docs/project-brain/13-CHECKPOINT.md").read_text(encoding="utf-8")
        cls.mirror = (R / ".engineering/CHECKPOINT.md").read_text(encoding="utf-8")
        cls.machine = json.loads((R / ".engineering/CHECKPOINT.json").read_text(encoding="utf-8"))
        cls.backlog = (R / "docs/project-brain/14-BACKLOG.md").read_text(encoding="utf-8")
        cls.lock = json.loads((R / ".engineering/context-locks/IRIS-WO-0062-WO0061-CANONICAL-CLOSEOUT.json").read_text(encoding="utf-8"))
        cls.evidence = json.loads((R / ".engineering/evidence/IRIS-WO-0062.json").read_text(encoding="utf-8"))
        cls.original = json.loads((R / ".engineering/evidence/IRIS-WO-0061.json").read_text(encoding="utf-8"))

    def test_01_mirrors_and_machine_next_step_match(self):
        self.assertEqual(self.cp, self.mirror)
        self.assertEqual(self.machine["nextStep"], self.cp.split("## NEXT STEP\n", 1)[1].strip())

    def test_02_factual_wo0061_completion_is_current(self):
        completed = self.cp.split("## COMPLETED\n", 1)[1].split("\n## IN PROGRESS", 1)[0]
        line = next((row for row in completed.splitlines() if "**IRIS-WO-0061 COMPLETED**" in row), "")
        for token in ("PR #180", H, M, TREE, "Governance #36450986971", "Governance #36452077561", "4643/4643", "22/22", "10/10", "#179", "#5874353354"):
            self.assertIn(token, line)
        self.assertNotIn("PENDING AT AUTHORING", line)

    def test_03_next_step_keeps_original_owner_and_runtime_stops(self):
        next_step = self.machine["nextStep"]
        for token in ("NEXT_REQUIRED_OWNER_GATE", "actual M09 owner disposition", "B_FUTURE_OWNER_RECEIPT", "DIRECTION_ONLY", "C01 UNADOPTED_NOT_FROZEN", "M11 86", "M12 110", "M13 96", "OPEN/UNRATED", "SPECIFIED_NOT_EXECUTED", "H01–H04 OPEN HIGH_FOR_FUTURE_FREEZE", "M12/#128", "M54/#145", "M58/#146", "M60/#147", "NOT_RECEIVED", "NOT_ADMITTED", "original issues #82/#110/#112/#128/#145/#146/#147/#155 remain OPEN", "OFFLINE", "source_not_current"):
            self.assertIn(token, next_step)

    def test_04_backlog_has_no_stale_active_wo0061(self):
        active = self.backlog.split("## ACTIVE SCOPED EXISTING-KERNEL MAINTENANCE, NO NEW AUTHORITY", 1)[1].split("\n## VERIFIED SCOPED", 1)[0]
        verified = self.backlog.split("## VERIFIED SCOPED EXISTING-KERNEL MAINTENANCE, NO NEW AUTHORITY", 1)[1].split("\n## COMPLETED FOUNDATION", 1)[0]
        self.assertIn("None recorded", active)
        self.assertIn("WO0061", verified)
        for token in ("PR #180", H, M, "Governance #36450986971", "Governance #36452077561", "4643/4643", "#179", "#5874353354"):
            self.assertIn(token, verified)
        self.assertNotIn("PENDING AT AUTHORING", verified)

    def test_05_original_wo0061_author_time_is_preserved(self):
        self.assertEqual(self.original["workOrder"], "IRIS-WO-0061")
        self.assertEqual(self.original["ownHeadCI"], "PENDING")
        self.assertEqual(self.original["ownProtectedMerge"], "PENDING")
        self.assertEqual(self.original["ownIndependentExactMain"], "PENDING")
        self.assertEqual(self.original["correctionDelta"]["initialFailingGovernanceRun"], 36449220072)
        self.assertEqual(self.original["correctionDelta"]["secondCorrection"]["actualFailingGovernanceRun"], 36450620186)

    def test_06_this_increment_is_pinned_and_makes_no_authority_claim(self):
        self.assertEqual(self.lock["workOrder"], "IRIS-WO-0062")
        self.assertEqual(self.lock["baseSha"], M)
        self.assertEqual(self.lock["baseTreeSha"], TREE)
        self.assertEqual(self.lock["issue"], 179)
        self.assertEqual(self.lock["sourceSnapshot"]["matched"], 22)
        self.assertEqual(len(self.lock["criticalSources"]), 22)
        self.assertEqual(len(self.lock["authorizedChangedFiles"]), 9)
        self.assertEqual(self.evidence["originalSourcePins"], 22)
        self.assertEqual(len(self.evidence["authorizedChangedPaths"]), 9)
        self.assertEqual(self.evidence["newOfflineConsistencyTests"], 6)
        self.assertEqual(self.evidence["ownHeadCI"], "PENDING")
        self.assertEqual(self.evidence["ownProtectedMerge"], "PENDING")
        self.assertFalse(self.evidence["originalOwnerProofReceived"])
        self.assertFalse(self.evidence["actualPhysicalOrRuntimeAction"])
        self.assertEqual(self.evidence["nativeRuntime"], "NOT_ADMITTED")
