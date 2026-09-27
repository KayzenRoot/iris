"""IRIS-WO-0035 H01 source-only evidence integrity, not original LV execution."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=".engineering/evidence/M09-H01-REVERSE-SEAM-EVIDENCE.json"
REPORT="planning/reviews/M09-H01-SYNTHETIC-REVERSE-SEAM-PROBE.md"
PROBES="tests/test_m09_h01_synthetic_reverse_seams.py"
PINS={
    "iris_resource_twin/recovery.py":"65678b060bdfafabb78ab63772794be410c48a92",
    "iris_resource_twin/leases.py":"5757d15156d62ac8cc49a1763eba62b944af52d9",
    "iris_resource_twin/model.py":"e64228e6a58b787ee107da8e737dd640ad4dad56",
    "tests/m09_support.py":"63a0e77f623afdc350a602d9ffd2fc93b4f52fd8",
    "tests/test_m09_recovery.py":"3976f8e27b6da66e2403611806886da8f18807e1",
    "planning/research/M11-C09-REVERSE-LIVENESS-OWNER-RESEARCH.md":"de97d44a49b9c8483aa6d5a051a0b42f97f5a3cc",
}

def get(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

class H01SourceIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v=get(EVIDENCE)
        cls.c01=get(".engineering/evidence/M09-HANDOFF-CANDIDATE-C01.json")
        cls.c02=get(".engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json")
        cls.b=get(".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json")
        cls.report=(ROOT/REPORT).read_text(encoding="utf-8")

    def test_01_exact_original_recovery_lease_test_and_c09_source_blobs(self):
        for path,want in PINS.items():
            data=(ROOT/path).read_bytes()
            sha=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
            self.assertEqual(sha,want,path)

    def test_02_historical_c01_none_current_b_direction_only(self):
        self.assertEqual(self.c01["topologySelected"],"NONE")
        self.assertEqual(self.c02["issue110OwnerDecision"],"NOT_RECORDED")
        self.assertEqual(self.b["direction"]["name"],"B_FUTURE_OWNER_RECEIPT")
        self.assertEqual(self.b["direction"]["status"],
                         "OWNER_SELECTED_FOR_DOCUMENTARY_PLANNING_ONLY")
        self.assertFalse(self.b["direction"]["c01Adopted"])
        self.assertIn("5857665032",self.v["ownerRatificationUrl"])

    def test_03_all_four_inherited_original_high_gates_still_open(self):
        hs=self.c02["futureFreezeBlockers"]
        self.assertEqual(self.v["inheritedHighs"],[h["id"] for h in hs])
        self.assertEqual(len(hs),4)
        self.assertTrue(all(h["severity"]=="HIGH_FOR_FUTURE_FREEZE"
                            and h["status"].startswith("OPEN_") for h in hs))
        self.assertEqual(self.v["H01"],"OPEN_OWNER_EVIDENCE_REQUIRED")
        self.assertEqual(self.v["risk"],"HIGH_FOR_FUTURE_FREEZE")

    def test_04_original_six_lv_and_twelve_hx_not_executed(self):
        self.assertEqual(self.v["originalFutureCases"],dict(
            LV=6,HX=12,C08=10,POC02=8,M12=80,status="SPECIFIED_NOT_EXECUTED"))
        self.assertEqual([x["id"] for x in self.c02["additionalReverseProofs"]],
                         [f"LV-{n:02d}" for n in range(1,7)])
        self.assertEqual([x["id"] for x in self.c01["proofObligations"]],
                         [f"HX-{n:02d}" for n in range(1,13)])
        self.assertTrue(all(x["status"]=="SPECIFIED_NOT_EXECUTED"
                            for x in self.c01["proofObligations"]+
                                     self.c02["additionalReverseProofs"]))

    def test_05_twenty_separately_named_fixture_methods_match_ast_and_inventory(self):
        ast_tree=ast.parse((ROOT/PROBES).read_text(encoding="utf-8"))
        cs=[x for x in ast_tree.body if isinstance(x,ast.ClassDef)
            and x.name=="H01SyntheticExistingM09ReverseSeamTests"]
        self.assertEqual(len(cs),1)
        methods=[x.name for x in cs[0].body
                 if isinstance(x,ast.FunctionDef) and x.name.startswith("test_")]
        self.assertEqual(len(methods),20)
        self.assertEqual(self.v["probeCount"],20)
        self.assertEqual([x["test"] for x in self.v["probes"]],methods)
        self.assertEqual([x["id"] for x in self.v["probes"]],
                         [f"H01-P{n:02d}" for n in range(1,21)])

    def test_06_report_preserves_trust_gap_and_no_runtime_or_fake_lv_clearance(self):
        for marker in (
            "B_FUTURE_OWNER_RECEIPT","OPEN_OWNER_EVIDENCE_REQUIRED",
            "HIGH_FOR_FUTURE_FREEZE","UNADOPTED_NOT_FROZEN",
            "SPECIFIED_NOT_EXECUTED","NOT_ADMITTED","DISABLED",
            "capacity_reclaimed=False","confirmed=True","M54","M60",
            "responded_at_ms","LV-01..06","H01-P01","H01-P20"):
            self.assertIn(marker,self.report)

    def test_07_all_probes_are_separate_synthetic_not_genuine_m11_issuer_tests(self):
        self.assertEqual(self.v["probeStatusAtCreation"],"PENDING_OWN_EXACT_HEAD_CI")
        self.assertTrue(all(x["status"]=="SYNTHETIC_SOURCE_TEST_PENDING_CI"
                            and not x["originalLVCaseExecuted"]
                            and x["noM11IssuerProof"] for x in self.v["probes"]))
        self.assertEqual(len(self.v["futureOwnerProofs"]),5)

    def test_08_no_original_m09_contract_or_future_runtime_promotion(self):
        self.assertEqual(self.v["m09Frozen"],"m09-contract-v1.0_FROZEN_UNCHANGED")
        self.assertEqual(self.v["m09C01"],"UNADOPTED_NOT_FROZEN")
        self.assertEqual(self.v["M11"],"NOT_FROZEN_86_OPEN")
        self.assertEqual(self.v["M12"],"NOT_FROZEN_110_OPEN_80_NOT_EXECUTED")
        self.assertEqual(self.v["runtime"],"M10_M11_M12_NOT_ADMITTED")
        self.assertEqual(self.v["OSGPUProcessNetworkCloud"],"DISABLED")

if __name__=="__main__":
    unittest.main()
