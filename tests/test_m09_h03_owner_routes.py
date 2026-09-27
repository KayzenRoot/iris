"""WO0038: owner-review issue routes are NOT actual cross-owner approvals."""
from __future__ import annotations

from copy import deepcopy
import unittest

from scripts.verify_m09_h03_owner_routes import (
    ROOT,ROUTES,PRIOR,C02,D01,M12,SOURCE_HASHES,OWNER_ISSUES,
    RESPONSE_NULLS,H03OwnerRouteError,git_blob,read,verify_all,verify_routes,
)


class H03ActualOwnerIssueRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=read(ROOT,ROUTES)
        cls.prior=read(ROOT,PRIOR)
        cls.c02=read(ROOT,C02)
        cls.d01=read(ROOT,D01)
        cls.m12=read(ROOT,M12)

    def check(self,*,e=None,prior=None,c02=None,d01=None,m12=None):
        return verify_routes(
            self.e if e is None else e,
            self.prior if prior is None else prior,
            self.c02 if c02 is None else c02,
            self.d01 if d01 is None else d01,
            self.m12 if m12 is None else m12,ROOT,
            check_documents=False)

    def fails(self,**updates):
        with self.assertRaises(H03OwnerRouteError):
            self.check(**updates)

    def test_01_actual_repository_source_and_report_verify(self):
        receipt=verify_all(ROOT)
        self.assertEqual(receipt["fourUnresolvedHighGates"],4)
        self.assertEqual(receipt["actualOwnerApprovals"],0)

    def test_02_exact_four_genuine_issue_inboxes(self):
        self.assertEqual([x["ownerIssue"] for x in self.e["routes"]],
                         [128,145,146,147])
        self.assertEqual([x["module"] for x in self.e["routes"]],
                         ["M12","M54","M58","M60"])

    def test_03_m12_uses_existing_issue_not_duplicate(self):
        self.assertEqual(self.e["routes"][0]["m12FormalCommentId"],
                         "5858805944")
        self.assertEqual(self.e["routes"][0]["ownerIssue"],128)

    def test_04_source_packets_questions_not_rewritten_or_extra(self):
        self.assertEqual(self.check()["uniqueOriginalQuestions"],91)
        for route,prior in zip(self.e["routes"],self.prior["sourceOwners"]):
            self.assertEqual(route["sourceQuestionIds"],
                             [q["id"] for q in prior["questions"]])

    def test_05_original_owner_assignments_overlap_not_approvals(self):
        self.assertEqual(self.check()["overlappingOwnerAssignments"],147)
        self.assertEqual([x["sourceQuestionCount"]
                          for x in self.e["routes"]],[72,39,9,27])

    def test_06_all_original_m12_questions_and_negatives_still_open(self):
        self.assertEqual(len(self.m12["questions"]),110)
        self.assertEqual(len(self.m12["negativeScenarios"]),80)
        self.assertTrue(all(q["status"]=="OPEN_UNRATED_PENDING_OWNER"
                            for q in self.m12["questions"]))
        self.assertTrue(all(q["status"]=="SPECIFIED_NOT_EXECUTED"
                            for q in self.m12["negativeScenarios"]))

    def test_07_twelve_h03_future_oracles_are_not_executed(self):
        self.assertEqual(len(self.prior["newH03FutureNegatives"]),12)
        self.assertTrue(all(x["status"]=="SPECIFIED_NOT_EXECUTED"
                            for x in self.prior["newH03FutureNegatives"]))

    def test_08_every_source_hash_uses_real_git_blob_algorithm(self):
        self.assertEqual(len(SOURCE_HASHES),7)
        for path,sha in SOURCE_HASHES.items():
            self.assertEqual(git_blob((ROOT/path).read_bytes()),sha,path)

    def test_09_unverified_signoff_cannot_be_self_asserted(self):
        e=deepcopy(self.e)
        e["routes"][1]["actualSignedOwnerDecision"]=True
        self.fails(e=e)

    def test_10_fabricated_real_owner_identity_is_rejected(self):
        e=deepcopy(self.e)
        e["routes"][2]["actualOwnerIdentity"]="self-asserted-owner"
        self.fails(e=e)

    def test_11_fabricated_independent_review_is_rejected(self):
        e=deepcopy(self.e)
        e["routes"][3]["qualifiedIndependentReview"]={"ci":"passed"}
        self.fails(e=e)

    def test_12_false_public_m58_approval_scope_is_rejected(self):
        e=deepcopy(self.e)
        e["routes"][2]["approvalScope"]="external negative-only API allowed"
        self.fails(e=e)

    def test_13_fabricated_actual_m12_source_commit_is_rejected(self):
        e=deepcopy(self.e)
        e["routes"][0]["actualOwnerReviewedContractCommit"]="deadbeef"
        self.fails(e=e)

    def test_14_wrong_issue_number_and_url_are_rejected(self):
        e=deepcopy(self.e)
        e["routes"][1]["ownerIssue"]=128
        self.fails(e=e)
        e=deepcopy(self.e)
        e["routes"][1]["issueUrl"]="https://github.com/KayzenRoot/iris/issues/128"
        self.fails(e=e)

    def test_15_dropped_original_owner_question_is_rejected(self):
        e=deepcopy(self.e)
        e["routes"][3]["sourceQuestionIds"].pop()
        self.fails(e=e)

    def test_16_duplicate_owner_route_is_rejected(self):
        e=deepcopy(self.e)
        e["routes"][3]=deepcopy(e["routes"][2])
        self.fails(e=e)

    def test_17_false_live_issue_state_without_refetch_is_rejected(self):
        e=deepcopy(self.e)
        e["routes"][1]["liveStateRequiresIndependentRefetch"]=False
        self.fails(e=e)
        e=deepcopy(self.e)
        e["routes"][2]["issueObservedAtRouting"]="CLOSED_APPROVED"
        self.fails(e=e)

    def test_18_h03_closed_or_downgraded_without_original_owner_proof_fails(self):
        e=deepcopy(self.e)
        e["h03"]="CLOSED"
        self.fails(e=e)
        c02=deepcopy(self.c02)
        c02["futureFreezeBlockers"][2]["severity"]="LOW"
        self.fails(c02=c02)

    def test_19_original_m12_future_test_falsely_executed_rejected(self):
        m12=deepcopy(self.m12)
        m12["negativeScenarios"][0]["status"]="EXECUTED_PASS"
        self.fails(m12=m12)

    def test_20_owner_ratified_b_must_not_adopt_c01(self):
        d=deepcopy(self.d01)
        d["direction"]["c01Adopted"]=True
        self.fails(d01=d)

    def test_21_m54_does_not_inherit_m12_candidate_contract_tier(self):
        e=deepcopy(self.e)
        e["routes"][1]["sourceTier"]="FROZEN_M54_CONTRACT"
        self.fails(e=e)

    def test_22_m58_synthetic_negative_case_does_not_prove_real_test(self):
        e=deepcopy(self.e)
        e["routes"][2]["realNegativeTestEvidence"]=["all passed"]
        self.fails(e=e)

    def test_23_all_owner_issue_routes_remain_open_not_signature(self):
        self.assertEqual(self.e["allOwnerApproval"],"NONE_RECORDED")
        self.assertEqual(self.e["routingStatus"],
                         "ROUTED_FOR_REAL_OWNER_DISCUSSION_ONLY")
        for route in self.e["routes"]:
            self.assertFalse(route["actualSignedOwnerDecision"])
            self.assertTrue(all(route[k] is None for k in RESPONSE_NULLS))

    def test_24_lying_original_h03_report_with_fake_owner_approval_fails(self):
        p=deepcopy(self.prior)
        p["sourceOwners"][3]["actualSignedOwnerContract"]=True
        # The new route verifier is source-sensitive, and the prior
        # independent H03 verifier already checks this old source record.
        from scripts.verify_m09_h03_owner_packets import (
            H03IntegrityError,verify_h03,
        )
        with self.assertRaises(H03IntegrityError):
            verify_h03(p,read(ROOT,
                ".engineering/evidence/M12-OWNER-INTAKE-C02.json"),
                self.m12,self.c02,self.d01,ROOT,check_documents=False)


if __name__=="__main__":
    unittest.main()
