"""WO-0034: pin H02 source-gap report without confusing fixtures with real HX/LV."""
from __future__ import annotations
import ast
import hashlib
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=".engineering/evidence/M09-H02-SEMANTIC-PROBE-EVIDENCE.json"
REPORT="planning/reviews/M09-H02-SYNTHETIC-SEAM-PROBE.md"
SRC="tests/test_m09_h02_seam_probe.py"
PINS={
 "iris_resource_twin/twin.py":"f8d217d46ca4284d439aba418d6113eb0c4059e2",
 "iris_resource_twin/leases.py":"5757d15156d62ac8cc49a1763eba62b944af52d9",
 "iris_resource_twin/model.py":"e64228e6a58b787ee107da8e737dd640ad4dad56",
 "tests/m09_support.py":"63a0e77f623afdc350a602d9ffd2fc93b4f52fd8",
}

def get(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

class H02EvidenceIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record=get(DATA)
        cls.c01=get(".engineering/evidence/M09-HANDOFF-CANDIDATE-C01.json")
        cls.c02=get(".engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json")
        cls.b=get(".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json")
        cls.report=(ROOT/REPORT).read_text(encoding="utf-8")
    def test_01_exact_historical_frozen_source_blobs(self):
        for path,expected in PINS.items():
            data=(ROOT/path).read_bytes()
            actual=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
            self.assertEqual(actual,expected,path)
    def test_02_frozen_contract_and_historic_c01_not_changed(self):
        self.assertEqual(self.record["m09Frozen"],"m09-contract-v1.0_FROZEN_UNCHANGED")
        self.assertEqual(self.c01["topologySelected"],"NONE")
        self.assertEqual(self.record["m09C01"],"UNADOPTED_NOT_FROZEN")
    def test_03_later_owner_b_only_is_not_new_port(self):
        self.assertEqual(self.b["direction"]["name"],"B_FUTURE_OWNER_RECEIPT")
        self.assertEqual(self.b["direction"]["status"],"OWNER_SELECTED_FOR_DOCUMENTARY_PLANNING_ONLY")
        self.assertEqual(self.record["ownerSelectedDirection"],"B_FUTURE_OWNER_RECEIPT_PLANNING_ONLY")
        self.assertIn("5857665032",self.record["ownerDecisionReference"])
        self.assertEqual(self.record["otherOwnerApprovals"],"NOT_INFERRED")
    def test_04_four_historic_high_gates_still_open(self):
        hs=self.c02["futureFreezeBlockers"]
        self.assertEqual(self.record["inheritedHighs"],[h["id"] for h in hs])
        self.assertEqual(len(hs),4)
        for h in hs:
            self.assertTrue(h["status"].startswith("OPEN_"))
            self.assertEqual(h["severity"],"HIGH_FOR_FUTURE_FREEZE")
        self.assertEqual(self.record["H02status"],"OPEN_M09_OWNER_ATOMICITY_DECISION")
    def test_05_original_hx_lv_and_m12_oracles_unexecuted(self):
        self.assertEqual(self.record["originalFutureTests"],dict(
            HX=12,LV=6,C08=10,POC02=8,M12=80,status="SPECIFIED_NOT_EXECUTED"))
        self.assertEqual([x["id"] for x in self.c01["proofObligations"]],
                         [f"HX-{n:02d}" for n in range(1,13)])
        self.assertEqual([x["id"] for x in self.c02["additionalReverseProofs"]],
                         [f"LV-{n:02d}" for n in range(1,7)])
        for group in (self.c01["proofObligations"],self.c02["additionalReverseProofs"]):
            self.assertTrue(all(x["status"]=="SPECIFIED_NOT_EXECUTED" for x in group))
    def test_06_exact_fourteen_distinct_fixture_test_methods(self):
        node=ast.parse((ROOT/SRC).read_text(encoding="utf-8"))
        cases=[n for n in node.body if isinstance(n,ast.ClassDef)
               and n.name=="H02ExistingSemanticSeamProbes"]
        self.assertEqual(len(cases),1)
        methods=[x.name for x in cases[0].body if isinstance(x,ast.FunctionDef)
                 and x.name.startswith("test_")]
        self.assertEqual(self.record["probeCount"],14)
        self.assertEqual(methods,[p["test"] for p in self.record["probes"]])
        self.assertEqual([p["id"] for p in self.record["probes"]],
                         [f"H02-P{n:02d}" for n in range(1,15)])
    def test_07_report_explicitly_keeps_h02_open_and_options_unselected(self):
        for term in ("OPEN HIGH_FOR_FUTURE_FREEZE","B_FUTURE_OWNER_RECEIPT",
                     "J1","J2","J3","none selected","HX-01..12",
                     "LV-01..06","SPECIFIED_NOT_EXECUTED",
                     "NOT_ADMITTED","DISABLED"):
            self.assertIn(term,self.report)
    def test_08_probe_is_fixture_only_and_no_live_actions(self):
        self.assertEqual(self.record["scope"],
            "CURRENT_FROZEN_M09_SOURCE_SEMANTIC_INTERLEAVING_PROBES_NO_IMPLEMENTATION_MODIFICATION")
        self.assertEqual(self.record["probeExecutionStatus"],
                         "PENDING_OWN_EXACT_HEAD_CI_AT_PROPOSAL_CREATION")
        self.assertTrue(all(p["status"]=="SOURCE_SEMANTIC_FIXTURE_SPECIFIED_PENDING_CI"
                            and p["originalHxLvCasesNotRun"] and p["noOSGPUOrNetwork"]
                            for p in self.record["probes"]))
        self.assertEqual(self.record["runtime"],"M10_M11_M12_NOT_ADMITTED")
        self.assertEqual(self.record["OSGPUProcessNetworkCloud"],"DISABLED")

if __name__=="__main__":
    unittest.main()
