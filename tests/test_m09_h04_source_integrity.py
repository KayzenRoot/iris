"""WO-0036 H04 documentary integrity: no fake other-owner work/attempt proof."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
EVID=".engineering/evidence/M09-H04-WORK-ATTEMPT-EPOCH-EVIDENCE.json"
REPORT="planning/reviews/M09-H04-SYNTHETIC-WORK-ATTEMPT-SEAM-PROBE.md"
TESTS="tests/test_m09_h04_work_attempt_epoch_seams.py"
PINS={
    "iris_resource_twin/leases.py":"5757d15156d62ac8cc49a1763eba62b944af52d9",
    "iris_resource_twin/model.py":"e64228e6a58b787ee107da8e737dd640ad4dad56",
    "tests/m09_support.py":"63a0e77f623afdc350a602d9ffd2fc93b4f52fd8",
    "planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md":"a36fd73c03f06b7558f850a2ad515a0df37c243b",
    "planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md":"d6778684e0c34e55d05ddc06cf5aa47fe347c037",
    "planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md":"4a5f384271504365701bdd685455d93984617f21",
}

def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

class H04SourceHistoryAndScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=read(EVID)
        cls.c01=read(".engineering/evidence/M09-HANDOFF-CANDIDATE-C01.json")
        cls.c02=read(".engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json")
        cls.d01=read(".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json")
        cls.report=(ROOT/REPORT).read_text(encoding="utf-8")

    def test_01_exact_original_frozen_sources_and_m02_m06_m11_candidates(self):
        for path,sha in PINS.items():
            b=(ROOT/path).read_bytes()
            got=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
            self.assertEqual(got,sha,path)

    def test_02_b_is_later_architecture_direction_not_c01_adoption(self):
        self.assertEqual(self.c01["topologySelected"],"NONE")
        self.assertEqual(self.c02["issue110OwnerDecision"],"NOT_RECORDED")
        self.assertEqual(self.d01["direction"]["name"],"B_FUTURE_OWNER_RECEIPT")
        self.assertEqual(self.d01["direction"]["status"],
                         "OWNER_SELECTED_FOR_DOCUMENTARY_PLANNING_ONLY")
        self.assertFalse(self.d01["direction"]["c01Adopted"])
        self.assertIn("5857665032",self.e["ownerDecisionUrl"])

    def test_03_four_original_high_future_freeze_gates_unchanged(self):
        hs=self.c02["futureFreezeBlockers"]
        self.assertEqual(self.e["inheritedHighs"],[h["id"] for h in hs])
        self.assertEqual(len(hs),4)
        self.assertTrue(all(h["severity"]=="HIGH_FOR_FUTURE_FREEZE"
                            and h["status"].startswith("OPEN_") for h in hs))
        self.assertEqual(self.e["H04"],"OPEN_CROSS_OWNER_DISPOSITION")
        self.assertEqual(self.e["H04severity"],"HIGH_FOR_FUTURE_FREEZE")

    def test_04_original_hx_lv_others_remain_specified_not_executed(self):
        self.assertEqual(self.e["originalFutureCases"],dict(
            HX=12,LV=6,C08=10,POC02=8,M12=80,
            status="SPECIFIED_NOT_EXECUTED"))
        self.assertEqual([x["id"] for x in self.c01["proofObligations"]],
                         [f"HX-{n:02d}" for n in range(1,13)])
        self.assertEqual([x["id"] for x in self.c02["additionalReverseProofs"]],
                         [f"LV-{n:02d}" for n in range(1,7)])
        self.assertTrue(all(x["status"]=="SPECIFIED_NOT_EXECUTED"
                            for x in self.c01["proofObligations"]+
                                     self.c02["additionalReverseProofs"]))

    def test_05_eighteen_distinct_h04_methods_match_evidence(self):
        node=ast.parse((ROOT/TESTS).read_text(encoding="utf-8"))
        cs=[c for c in node.body if isinstance(c,ast.ClassDef)
            and c.name=="H04SyntheticExistingM09BindingSeams"]
        self.assertEqual(len(cs),1)
        methods=[f.name for f in cs[0].body if isinstance(f,ast.FunctionDef)
                 and f.name.startswith("test_")]
        self.assertEqual(self.e["probeCount"],18)
        self.assertEqual(methods,[p["test"] for p in self.e["probes"]])
        self.assertEqual([p["id"] for p in self.e["probes"]],
                         [f"H04-P{n:02d}" for n in range(1,19)])

    def test_06_report_explicit_owner_restrictions_and_original_cases(self):
        for term in ("B_FUTURE_OWNER_RECEIPT","OPEN_CROSS_OWNER_DISPOSITION",
                     "OPEN HIGH_FOR_FUTURE_FREEZE","UNADOPTED_NOT_FROZEN",
                     "SPECIFIED_NOT_EXECUTED","NOT_ADMITTED",
                     "M02","M06","M09","M11","M12","M54","M60",
                     "H04-P01","H04-P18"):
            self.assertIn(term,self.report)

    def test_07_all_fixtures_are_local_not_external_owner_issued_proofs(self):
        self.assertEqual(self.e["probeStatusAtCreation"],
                         "PENDING_OWN_EXACT_HEAD_CI")
        self.assertTrue(all(p["statusAtCreation"]==
                            "SYNTHETIC_EXISTING_M09_FIXTURE_PENDING_CI"
                            and not p["externalOwnerProof"]
                            and not p["originalHxLvExecuted"]
                            for p in self.e["probes"]))
        self.assertEqual(len(self.e["externalOwnerProofsPending"]),6)

    def test_08_frozen_m09_and_other_owner_runtime_status_unchanged(self):
        self.assertEqual(self.e["m09Frozen"],"m09-contract-v1.0_FROZEN_UNCHANGED")
        self.assertEqual(self.e["m09C01"],"UNADOPTED_NOT_FROZEN")
        self.assertEqual(self.e["m11"],"NOT_FROZEN_86_OPEN")
        self.assertEqual(self.e["m12"],"NOT_FROZEN_110_OPEN_80_NOT_EXECUTED")
        self.assertEqual(self.e["runtime"],"M10_M11_M12_NOT_ADMITTED")
        self.assertEqual(self.e["osGpuNetworkCloudProcess"],"DISABLED")

if __name__=="__main__":
    unittest.main()
