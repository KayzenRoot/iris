"""WO0037 fail-closed H03 four-owner source packet, intersection and status tests."""
from __future__ import annotations
from copy import deepcopy
import unittest
from scripts.verify_m09_h03_owner_packets import (
    ROOT,PACKETS,INTAKE,ORIGINAL,C02,D01,
    SOURCE_HASHES,git_blob,read_json,H03IntegrityError,verify_h03,verify_all,
)


class H03SourcePacketIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=read_json(ROOT,PACKETS)
        cls.i=read_json(ROOT,INTAKE)
        cls.original=read_json(ROOT,ORIGINAL)
        cls.c02=read_json(ROOT,C02)
        cls.d01=read_json(ROOT,D01)

    def check(self,p=None,intake=None,original=None,c02=None,d01=None):
        return verify_h03(
            self.p if p is None else p,
            self.i if intake is None else intake,
            self.original if original is None else original,
            self.c02 if c02 is None else c02,
            self.d01 if d01 is None else d01,ROOT,check_documents=False)

    def fail(self,*,p=None,intake=None,original=None,c02=None,d01=None):
        with self.assertRaises(H03IntegrityError):
            self.check(p,intake,original,c02,d01)

    def test_01_all_prior_owner_routing_and_h03_doc_validate(self):
        self.assertEqual(verify_all(ROOT)["openHighs"],4)

    def test_02_all_four_owner_queues_are_nonexclusive_not_signoffs(self):
        r=self.check()
        self.assertEqual(
            (r["M12"],r["M54"],r["M58"],r["M60"]),(72,39,9,27))
        self.assertEqual(r["ownerQuestionAssignments"],147)
        self.assertEqual(r["uniqueQuestions"],91)

    def test_03_six_pairwise_intersections_are_exact_source_derived(self):
        self.assertEqual([x["questionCount"]
            for x in self.p["pairwiseIntersections"]],[23,4,13,9,18,2])

    def test_04_all_five_issue110_question_ids_remain_visible(self):
        self.assertEqual(len(self.p["explicitIssue110QuestionIds"]),5)
        self.assertEqual(self.p["explicitIssue110QuestionIds"],
                         self.i["explicitIssue110QuestionIds"])

    def test_05_historic_none_and_later_b_are_distinct_source_events(self):
        self.assertEqual(self.i["selectedTopology"],"NONE")
        self.assertEqual(self.c02["issue110OwnerDecision"],"NOT_RECORDED")
        self.assertEqual(self.p["ownerSelectedTopologyDirection"],
                         "B_FUTURE_OWNER_RECEIPT_DOCUMENTARY_ONLY")
        self.assertFalse(self.d01["direction"]["c01Adopted"])

    def test_06_all_historical_m12_questions_still_open_not_rated(self):
        self.assertEqual(len(self.original["questions"]),110)
        self.assertTrue(all(x["status"]=="OPEN_UNRATED_PENDING_OWNER"
                            for x in self.original["questions"]))

    def test_07_all_original_future_m12_tests_remain_not_executed(self):
        self.assertEqual(len(self.original["negativeScenarios"]),80)
        self.assertTrue(all(x["status"]=="SPECIFIED_NOT_EXECUTED"
                            for x in self.original["negativeScenarios"]))

    def test_08_twelve_new_h03_negatives_are_design_only_not_executed(self):
        self.assertEqual(len(self.p["newH03FutureNegatives"]),12)
        self.assertTrue(all(x["status"]=="SPECIFIED_NOT_EXECUTED"
                            and x["runtime"] is False
                            for x in self.p["newH03FutureNegatives"]))

    def test_09_eight_immutable_h03_authority_sources_exact_git_blobs(self):
        self.assertEqual(len(SOURCE_HASHES),7)
        for path,sha in SOURCE_HASHES.items():
            self.assertEqual(git_blob((ROOT/path).read_bytes()),sha,path)

    def test_10_fake_owner_approval_is_detected(self):
        p=deepcopy(self.p)
        p["sourceOwners"][1]["actualSignedOwnerContract"]=True
        self.fail(p=p)

    def test_11_wrong_original_question_text_is_detected(self):
        p=deepcopy(self.p)
        p["sourceOwners"][2]["questions"][0]["originalQuestion"]="APPROVED"
        self.fail(p=p)

    def test_12_dropped_owner_queue_question_is_detected(self):
        p=deepcopy(self.p)
        p["sourceOwners"][3]["questions"].pop()
        self.fail(p=p)

    def test_13_fabricated_public_m58_port_is_detected(self):
        p=deepcopy(self.p)
        p["sourceOwners"][2]["publicOrExecutablePort"]=True
        self.fail(p=p)

    def test_14_closed_h03_or_risk_downgrade_is_detected(self):
        p=deepcopy(self.p)
        p["H03status"]="CLOSED"
        self.fail(p=p)
        p=deepcopy(self.p)
        p["H03severity"]="LOW"
        self.fail(p=p)

    def test_15_later_b_backfilled_into_historic_intake_is_detected(self):
        intake=deepcopy(self.i)
        intake["selectedTopology"]="B_FUTURE_OWNER_RECEIPT"
        self.fail(intake=intake)

    def test_16_missing_overlap_is_detected(self):
        p=deepcopy(self.p)
        p["pairwiseIntersections"][3]["questionCount"]-=1
        self.fail(p=p)

    def test_17_falsely_executed_h03_future_case_is_detected(self):
        p=deepcopy(self.p)
        p["newH03FutureNegatives"][0]["status"]="PASS"
        self.fail(p=p)

    def test_18_falsely_executed_original_m12_future_case_is_detected(self):
        original=deepcopy(self.original)
        original["negativeScenarios"][0]["status"]="EXECUTED_PASS"
        self.fail(original=original)

    def test_19_fake_m12_original_question_acceptance_is_detected(self):
        original=deepcopy(self.original)
        original["questions"][0]["status"]="OWNER_APPROVED"
        self.fail(original=original)

    def test_20_false_runtime_or_external_owner_grant_is_detected(self):
        p=deepcopy(self.p)
        p["runtime"]="M11_ADMITTED"
        self.fail(p=p)
        p=deepcopy(self.p)
        p["crossOwnerApproval"]="ALL_APPROVED"
        self.fail(p=p)

    def test_21_historic_c02_one_high_closed_is_detected(self):
        c02=deepcopy(self.c02)
        c02["futureFreezeBlockers"][2]["status"]="CLOSED"
        self.fail(c02=c02)

    def test_22_forged_ratified_owner_d01_c01_adoption_is_detected(self):
        d=deepcopy(self.d01)
        d["direction"]["c01Adopted"]=True
        self.fail(d01=d)

    def test_23_fake_m54_owner_index_tier_promotion_is_detected(self):
        p=deepcopy(self.p)
        p["sourceOwners"][1]["tier"]="FROZEN_OWNER_CONTRACT"
        self.fail(p=p)

    def test_24_invented_m58_overlapping_assignment_is_detected(self):
        p=deepcopy(self.p)
        p["sourceOwners"][2]["questions"][0]["exactOwnerLabel"]="M58"
        self.fail(p=p)


if __name__=="__main__":
    unittest.main()
