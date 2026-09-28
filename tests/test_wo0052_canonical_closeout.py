"""WO0052 local documentary-only truth and mirror regressions."""
import json
import unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
HEAD="b1c5dc3741b6760626fb9a12123528e2d4fcde17"
MAIN="533da642fd227b898031228de5f99ea65c58781d"

class WO0052CanonicalCloseoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cp=(R/"docs/project-brain/13-CHECKPOINT.md").read_text(encoding="utf-8")
        cls.bridge=(R/".engineering/CHECKPOINT.md").read_text(encoding="utf-8")
        cls.machine=json.loads((R/".engineering/CHECKPOINT.json").read_text(encoding="utf-8"))
        cls.backlog=(R/"docs/project-brain/14-BACKLOG.md").read_text(encoding="utf-8")
        cls.readme=(R/"README.md").read_text(encoding="utf-8")
        cls.overview=(R/"docs/project-brain/01-PROJECT-OVERVIEW.md").read_text(encoding="utf-8")
        cls.lock=json.loads((R/".engineering/context-locks/IRIS-WO-0052-CANONICAL-WO0051-CLOSEOUT.json").read_text(encoding="utf-8"))
        cls.evidence=json.loads((R/".engineering/evidence/IRIS-WO-0052.json").read_text(encoding="utf-8"))
    
    def test_exact_human_and_machine_checkpoint(self):
        self.assertEqual(self.cp,self.bridge)
        self.assertEqual(self.machine["nextStep"],self.cp.split("## NEXT STEP\n",1)[1].strip())
        self.assertEqual(self.machine["status"],"M11_PLANNING_ACTIVE_M10_IMPLEMENTATION_NOT_ADMITTED")
    
    def test_previous_exact_head_and_independently_green_main_are_factual(self):
        for marker in ("IRIS-WO-0051 **COMPLETED**","PR #162",HEAD,MAIN,"Governance #36362338152",
                       "Governance #36362432890","4526/4526","47/47","235/235","INDEX_ONLY"):
            self.assertIn(marker,self.cp)
        self.assertIn("NEXT_REQUIRED_OWNER_GATE",self.machine["nextStep"])
        self.assertNotIn("PROPOSED IRIS-WO-0051",self.machine["nextStep"])
    
    def test_historic_backlog_and_public_prior_baselines_are_not_erased(self):
        self.assertIn("**WO0051 separately gated exhaustive M14–M60 source-only index FCS proposal:**",self.backlog)
        self.assertIn("**WO0051 FACTUAL protected postmerge closeout",self.backlog)
        for doc in (self.readme,self.overview):
            for marker in ("2026-09-28 UTC","PR #162",HEAD,MAIN,"Governance #36362432890",
                           "4526/4526","47/47","235/235","Historical"):
                self.assertIn(marker,doc)
            self.assertIn("PR #149",doc)
            self.assertIn("Governance #528",doc)
    
    def test_unqualified_actual_owner_and_runtime_gates_remain_explicit(self):
        for doc in (self.cp,self.machine["nextStep"],self.backlog,self.readme,self.overview):
            for marker in ("B_FUTURE_OWNER_RECEIPT","DIRECTION_ONLY","UNADOPTED_NOT_FROZEN",
                           "OPEN HIGH_FOR_FUTURE_FREEZE","NOT_ADMITTED"):
                self.assertIn(marker,doc)
        for marker in ("M12/#128","M54/#145","M58/#146","M60/#147","96","74",
                       "110","80","86","COMPLETE_DRAFT_FORMAT_ONLY is never approval"):
            self.assertIn(marker,self.machine["nextStep"])
    
    def test_original_source_lock_and_pending_evidence_not_preclaimed(self):
        self.assertEqual(self.lock["workOrder"],"IRIS-WO-0052")
        self.assertEqual(self.lock["baseSha"],MAIN)
        self.assertEqual(len(self.lock["criticalSources"]),16)
        self.assertEqual(self.lock["sourceSnapshot"]["matched"],16)
        self.assertEqual(len(self.lock["authorizedChangedFiles"]),11)
        self.assertEqual(self.evidence["previousActuallyGreen"]["fullSuite"],"4526/4526")
        self.assertEqual(self.evidence["ownHeadCI"],"PENDING")
        self.assertFalse(self.evidence["actualIndependentOwnerApproval"])
        self.assertEqual(self.evidence["nativeRuntime"],"NOT_ADMITTED")
