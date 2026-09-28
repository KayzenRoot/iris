"""WO0060 offline documentary regressions for prior WO0059 actual completion."""
import json
import unittest
from pathlib import Path

R=Path(__file__).resolve().parents[1]
H="e32ff01bf4503dbf41698a183f727c95894bba24"
M="db348eec9b93ed82e380edb7a22bf68e726f9854"

class WO0060CanonicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cp=(R/"docs/project-brain/13-CHECKPOINT.md").read_text(encoding="utf-8")
        cls.mirror=(R/".engineering/CHECKPOINT.md").read_text(encoding="utf-8")
        cls.machine=json.loads((R/".engineering/CHECKPOINT.json").read_text(encoding="utf-8"))
        cls.backlog=(R/"docs/project-brain/14-BACKLOG.md").read_text(encoding="utf-8")
        cls.lock=json.loads((R/".engineering/context-locks/IRIS-WO-0060-WO0059-CANONICAL-CLOSEOUT.json").read_text(encoding="utf-8"))
        cls.evidence=json.loads((R/".engineering/evidence/IRIS-WO-0060.json").read_text(encoding="utf-8"))
        cls.original=json.loads((R/".engineering/evidence/IRIS-WO-0059.json").read_text(encoding="utf-8"))

    def test_01_mirror_and_machine_match(self):
        self.assertEqual(self.cp,self.mirror)
        self.assertEqual(self.machine["nextStep"],self.cp.split("## NEXT STEP\n",1)[1].strip())

    def test_02_original_independent_completion_factual(self):
        completed=self.cp.split("## COMPLETED\n",1)[1].split("\n## IN PROGRESS",1)[0]
        line=next((s for s in completed.splitlines() if "**IRIS-WO-0059 COMPLETED**" in s),"")
        for token in ("PR #176",H,M,"23/23","10/10","Governance #36443533687","Governance #36444676423","4628/4628","Greptile","CodeRabbit","Socket","#175 CLOSED"):
            self.assertIn(token,line)

    def test_03_next_step_preserves_all_actual_owner_stop_markers(self):
        next=self.machine["nextStep"]
        for token in ("NEXT_REQUIRED_OWNER_GATE","actual M09 owner disposition","B_FUTURE_OWNER_RECEIPT","DIRECTION_ONLY","UNADOPTED_NOT_FROZEN","PREPARED_FOR_OWNER_REVIEW_ONLY","COMPLETE_DRAFT_FORMAT_ONLY is never approval","SPECIFIED_NOT_EXECUTED","H01–H04 OPEN HIGH_FOR_FUTURE_FREEZE","M12/#128","M54/#145","M58/#146","M60/#147","NOT_RECEIVED","NOT_ADMITTED","86","110","96","80","74","INDEX_ONLY","#82/#110/#112/#128/#145/#146/#147/#155"):
            self.assertIn(token,next)
        self.assertNotIn("WO0060 COMPLETED",next)

    def test_04_current_backlog_not_stale(self):
        recent=self.backlog.split("## VERIFIED SCOPED EXISTING-KERNEL MAINTENANCE, NO NEW AUTHORITY",1)[1].split("## COMPLETED FOUNDATION",1)[0]
        for token in ("WO0059",H,M,"Governance #36443533687","Governance #36444676423","4628/4628","23/23","10/10","#175 CLOSED","H01–H04"):
            self.assertIn(token,recent)
        self.assertNotIn("PENDING OWN EXACT-HEAD",recent)

    def test_05_immutable_original_source_lock_and_own_no_preclaim(self):
        self.assertEqual(self.lock["workOrder"],"IRIS-WO-0060")
        self.assertEqual(self.lock["baseSha"],M)
        self.assertEqual(self.lock["issue"],177)
        self.assertEqual(len(self.lock["criticalSources"]),16)
        self.assertEqual(self.lock["sourceSnapshot"]["matched"],16)
        self.assertEqual(len(self.lock["authorizedChangedFiles"]),9)
        self.assertEqual(self.evidence["previousActuallyGreen"]["fullSuite"],"4628/4628")
        self.assertEqual(self.evidence["ownHeadCI"],"PENDING")
        self.assertEqual(self.evidence["ownProtectedMerge"],"PENDING")

    def test_06_original_author_time_is_not_retroactively_rewritten(self):
        self.assertEqual(self.original["workOrder"],"IRIS-WO-0059")
        self.assertEqual(self.original["ownProtectedMerge"],"PENDING")
        self.assertIn("PENDING",self.original["ownHeadCI"])
        self.assertIn("secondFailingGovernanceRun",self.original["correctionDelta"])
        self.assertFalse(self.evidence["actualIndependentOriginalOwnerProof"])
        self.assertEqual(self.evidence["nativeRuntime"],"NOT_ADMITTED")
