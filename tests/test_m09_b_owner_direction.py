"""IRIS-WO-0033: source-only B direction proof and hostile nonpromotion tests."""
from __future__ import annotations
import unittest
from copy import deepcopy
from scripts.verify_m09_b_owner_direction import (
    ROOT, RECORD, C01, C02, ROUTING, PINS, ROLES, ROLE_GATES,
    HIGHS, HX, LV, M09BDirectionError, read_json, git_blob_sha,
    verify_decision, verify_all,
)

class M09BDirectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record=read_json(ROOT,RECORD)
        cls.c01=read_json(ROOT,C01)
        cls.c02=read_json(ROOT,C02)
        cls.routing=read_json(ROOT,ROUTING)
    def check(self,record=None,c01=None,c02=None,routing=None):
        return verify_decision(
            self.record if record is None else record,
            self.c01 if c01 is None else c01,
            self.c02 if c02 is None else c02,
            self.routing if routing is None else routing,ROOT)
    def mutate(self,path,key,value):
        obj=deepcopy(self.record)
        curr=obj
        for name in path: curr=curr[name]
        curr[key]=value
        with self.assertRaises(M09BDirectionError):
            self.check(record=obj)

    def test_full_original_evidence_and_b_direction(self):
        v=verify_all(ROOT)
        self.assertEqual(v["highsOpen"],4)
        self.assertFalse(v["runtimeAdmitted"])
    def test_original_historical_none_is_distinct_from_current_b(self):
        self.assertEqual(self.c01["topologySelected"],"NONE")
        self.assertEqual(self.c02["issue110OwnerDecision"],"NOT_RECORDED")
        self.assertEqual(self.record["direction"]["name"],"B_FUTURE_OWNER_RECEIPT")
    def test_original_highs_identical_and_still_open(self):
        self.assertEqual([x["id"] for x in self.record["inheritedHighs"]],list(HIGHS))
        self.assertTrue(all(x["currentStatus"].startswith("OPEN_")
                            for x in self.record["inheritedHighs"]))
    def test_eight_exact_git_source_blobs(self):
        self.assertEqual(len(PINS),8)
        for path,sha in PINS:
            self.assertEqual(git_blob_sha((ROOT/path).read_bytes()),sha)
    def test_original_negative_case_references(self):
        self.assertEqual([x["id"] for x in self.record["futureOriginalNegatives"]["HX"]],list(HX))
        self.assertEqual([x["id"] for x in self.record["futureOriginalNegatives"]["LV"]],list(LV))
    def test_prior_negatives_none_executed(self):
        self.assertEqual(self.record["futureOriginalNegatives"]["executed"],0)
        self.assertEqual(self.record["notExecutedM12Cases"],80)
    def test_six_conceptual_roles_not_apis(self):
        self.assertEqual([x["name"] for x in self.record["conceptualRoles"]],list(ROLES))
        self.assertTrue(all(x["status"]=="CONCEPTUAL_NOT_ADOPTED"
                            for x in self.record["conceptualRoles"]))
    def test_m12_five_linked_questions_still_open(self):
        self.assertEqual(self.record["linkedOriginalM12Issue110QuestionIds"],
                         self.routing["explicitIssue110QuestionIds"])
        self.assertEqual(self.record["openM12Questions"],110)
    def test_real_user_comment_link_is_explicit_offline_source_reference(self):
        self.assertEqual(self.record["decisionSource"]["commentId"],5857665032)
        self.assertEqual(self.record["direction"]["status"],
                         "OWNER_SELECTED_FOR_DOCUMENTARY_PLANNING_ONLY")
    def test_no_runtime_or_grant_anywhere_in_record(self):
        self.assertFalse(self.record["direction"]["implementationAdmitted"])
        self.assertFalse(self.record["direction"]["positiveGrantAuthorized"])
        self.assertEqual(self.record["actions"],"OS_GPU_NETWORK_CLOUD_PROCESS_DISABLED")
    def test_empty_git_blob_fingerprint(self):
        self.assertEqual(git_blob_sha(b""),"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")

    def test_false_selected_a(self):
        self.mutate(["direction"],"alternativeA","SELECTED")
    def test_false_selected_c(self):
        self.mutate(["direction"],"alternativeC","SELECTED")
    def test_false_c01_adoption(self):
        self.mutate(["direction"],"c01Adopted",True)
    def test_false_grant_authority(self):
        self.mutate(["direction"],"positiveGrantAuthorized",True)
    def test_false_runtime_admission(self):
        self.mutate(["direction"],"implementationAdmitted",True)
    def test_false_other_owner_approval(self):
        self.mutate(["direction"],"decisionsOutsideTopology","APPROVED")
    def test_wrong_issue_comment_id(self):
        self.mutate(["decisionSource"],"commentId",42)
    def test_wrong_base_git_commit(self):
        self.mutate(["decisionSource"],"sourceBaseSha","0"*40)
    def test_wrong_work_order(self):
        self.mutate([],"workOrder","IRIS-WO-0034")
    def test_missing_inherited_high(self):
        obj=deepcopy(self.record)
        obj["inheritedHighs"].pop()
        with self.assertRaises(M09BDirectionError): self.check(record=obj)
    def test_faked_high_closed(self):
        obj=deepcopy(self.record)
        obj["inheritedHighs"][0]["currentStatus"]="CLOSED"
        with self.assertRaises(M09BDirectionError): self.check(record=obj)
    def test_faked_source_high_closed(self):
        obj=deepcopy(self.c02)
        obj["futureFreezeBlockers"][0]["status"]="CLOSED"
        with self.assertRaises(M09BDirectionError): self.check(c02=obj)
    def test_faked_source_risk_rating(self):
        obj=deepcopy(self.c02)
        obj["futureFreezeBlockers"][1]["severity"]="LOW"
        with self.assertRaises(M09BDirectionError): self.check(c02=obj)
    def test_source_c01_fake_topology_b_backfill(self):
        obj=deepcopy(self.c01)
        obj["topologySelected"]="B_FUTURE_OWNER_RECEIPT"
        with self.assertRaises(M09BDirectionError): self.check(c01=obj)
    def test_source_c02_fake_current_owner_choice(self):
        obj=deepcopy(self.c02)
        obj["issue110OwnerDecision"]="B_FUTURE_OWNER_RECEIPT"
        with self.assertRaises(M09BDirectionError): self.check(c02=obj)
    def test_replaced_source_blob_hash(self):
        obj=deepcopy(self.record)
        obj["sourceAnchors"][0]["gitBlobSha1"]="0"*40
        with self.assertRaises(M09BDirectionError): self.check(record=obj)
    def test_removed_source_anchor(self):
        obj=deepcopy(self.record)
        obj["sourceAnchors"].pop()
        with self.assertRaises(M09BDirectionError): self.check(record=obj)
    def test_missing_conceptual_role(self):
        obj=deepcopy(self.record)
        obj["conceptualRoles"].pop()
        with self.assertRaises(M09BDirectionError): self.check(record=obj)
    def test_promoted_conceptual_role(self):
        obj=deepcopy(self.record)
        obj["conceptualRoles"][0]["status"]="ADOPTED_API"
        with self.assertRaises(M09BDirectionError): self.check(record=obj)
    def test_changed_role_owner_proof_gates(self):
        obj=deepcopy(self.record)
        obj["conceptualRoles"][0]["pendingProofGates"]=["H02"]
        with self.assertRaises(M09BDirectionError): self.check(record=obj)
    def test_short_or_missing_role_obligation(self):
        obj=deepcopy(self.record)
        obj["conceptualRoles"][1]["candidateObligation"]="APPROVED"
        with self.assertRaises(M09BDirectionError): self.check(record=obj)
    def test_fabricated_hx_execution(self):
        obj=deepcopy(self.record)
        obj["futureOriginalNegatives"]["HX"][0]["status"]="EXECUTED_PASS"
        with self.assertRaises(M09BDirectionError): self.check(record=obj)
    def test_fabricated_lv_execution(self):
        obj=deepcopy(self.record)
        obj["futureOriginalNegatives"]["LV"][0]["status"]="EXECUTED_PASS"
        with self.assertRaises(M09BDirectionError): self.check(record=obj)
    def test_missing_hx_case(self):
        obj=deepcopy(self.record)
        obj["futureOriginalNegatives"]["HX"].pop()
        with self.assertRaises(M09BDirectionError): self.check(record=obj)
    def test_original_c02_fake_lv_execution(self):
        obj=deepcopy(self.c02)
        obj["additionalReverseProofs"][1]["status"]="EXECUTED_PASS"
        with self.assertRaises(M09BDirectionError): self.check(c02=obj)
    def test_m12_other_owner_question_falsely_closed(self):
        self.mutate([],"openM12Questions",109)
    def test_m11_other_owner_question_falsely_closed(self):
        self.mutate([],"openM11Questions",85)
    def test_m12_future_runtime_case_falsely_executed(self):
        self.mutate([],"notExecutedM12Cases",79)
    def test_false_m09_c01_frozen(self):
        self.mutate([],"m09C01","FROZEN")
    def test_false_m11_runtime_admission(self):
        self.mutate([],"runtime","M10_M11_M12_ADMITTED")
    def test_false_os_action(self):
        self.mutate([],"actions","OS_PROCESS_ENABLED")
    def test_removed_future_independent_owner(self):
        self.mutate([],"pendingRealOwnerContracts",["M12","M54"])
    def test_false_gate_closed_or_audit_promotion(self):
        self.mutate([],"nextGate","COMPLETE")
    def test_removed_original_m12_link(self):
        obj=deepcopy(self.record)
        obj["linkedOriginalM12Issue110QuestionIds"].pop()
        with self.assertRaises(M09BDirectionError): self.check(record=obj)

if __name__=="__main__":
    unittest.main()
