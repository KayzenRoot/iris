"""WO0044: cross-lane original 110 question partition, never real signoff."""
from __future__ import annotations

from copy import deepcopy
import unittest

from scripts.verify_m12_h03_cross_lane import (
    ROOT, ROUTING, REGISTER, C03, H03, audit_cross_lane, verify_all,
    CrossLaneIntegrityError, read_json, ISSUE_110_H03_MEMBER,
)


class WO0044M12H03CrossLaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intake = read_json(ROOT, ROUTING)
        cls.register = read_json(ROOT, REGISTER)
        cls.c03 = read_json(ROOT, C03)
        cls.h03 = read_json(ROOT, H03)

    def audit(self, **changes):
        return audit_cross_lane(
            changes.get("intake", self.intake),
            changes.get("register", self.register),
            changes.get("c03", self.c03),
            changes.get("h03", self.h03),
        )

    def test_01_both_independently_verified_original_packets_pass_joint_audit(self):
        r = verify_all(ROOT)
        self.assertEqual(r["status"], "SOURCE_ONLY_CROSS_LANE_INTEGRITY_NO_OWNER_APPROVAL")
        self.assertFalse(r["realFutureNegativeTestsExecuted"])
        self.assertEqual(r["realOwnerApprovals"], 0)

    def test_02_exact_partition_110_equals_91_plus_19(self):
        r = self.audit()
        self.assertEqual(r["originalM12QuestionsStillOpen"], 110)
        self.assertEqual(r["h03UniqueOriginalQuestions"], 91)
        self.assertEqual(r["h03OutsideOriginalQuestions"], 19)
        self.assertEqual(r["h03OriginalAssignments"], 147)

    def test_03_exact_complement_four_five_three_seven(self):
        self.assertEqual(self.audit()["h03OutsideLaneCounts"], {
            "EXPLICIT_ISSUE_110_REVIEW": 4,
            "M11_CANDIDATE_CROSS_OWNER_REVIEW": 5,
            "FROZEN_OWNER_HANDOFF_REVIEW": 3,
            "LATER_OWNER_CONTRACT_REQUIRED": 7,
        })

    def test_04_19_c03_proposals_are_not_other_19(self):
        r = self.audit()
        self.assertEqual(r["independentC03NonbindingProposals"], 19)
        self.assertTrue(r["c03DisjointFromH03Complement"])

    def test_05_issue110_five_four_outside_one_inside_m12(self):
        r = self.audit()
        self.assertEqual(r["issue110OriginalQuestions"], 5)
        self.assertTrue(r["issue110FourOutsideOneInside"])
        self.assertIn(ISSUE_110_H03_MEMBER,
                      self.intake["ownerQueues"]["M12"])

    def test_06_m54_m60_18_shared_split_nine_seven_two(self):
        r = self.audit()
        self.assertEqual(r["sharedM54M60Questions"], 18)
        self.assertEqual(r["sharedOwnerGroups"], {
            "M54+M60": 9, "M12+M54+M60": 7, "M54+M58+M60": 2})

    def test_07_duplicate_original_register_id_fails_closed(self):
        reg = deepcopy(self.register)
        reg["questions"][1]["id"] = reg["questions"][0]["id"]
        with self.assertRaises(CrossLaneIntegrityError):
            self.audit(register=reg)

    def test_08_missing_original_register_row_fails_closed(self):
        reg = deepcopy(self.register)
        reg["questions"].pop()
        with self.assertRaises(CrossLaneIntegrityError):
            self.audit(register=reg)

    def test_09_original_question_text_rewrite_fails_closed(self):
        intake = deepcopy(self.intake)
        intake["questions"][0]["question"] = "invented answer"
        with self.assertRaises(CrossLaneIntegrityError):
            self.audit(intake=intake)

    def test_10_h03_original_owner_queue_row_removed_fails_closed(self):
        h03 = deepcopy(self.h03)
        h03["sourceOwners"][1]["questions"].pop()
        with self.assertRaises(CrossLaneIntegrityError):
            self.audit(h03=h03)

    def test_11_h03_extra_shared_owner_assignment_fails_closed(self):
        h03 = deepcopy(self.h03)
        h03["sourceOwners"][3]["questions"][0] = deepcopy(
            h03["sourceOwners"][1]["questions"][0])
        with self.assertRaises(CrossLaneIntegrityError):
            self.audit(h03=h03)

    def test_12_c03_proposal_overlap_with_outside_fails_closed(self):
        c03 = deepcopy(self.c03)
        c03["proposals"][0]["id"] = "M12-S01-U05"
        with self.assertRaisesRegex(CrossLaneIntegrityError, "C03"):
            self.audit(c03=c03)

    def test_13_c03_claimed_owner_approval_fails_closed(self):
        c03 = deepcopy(self.c03)
        c03["proposals"][0]["ownerApproval"] = "APPROVED"
        with self.assertRaises(CrossLaneIntegrityError):
            self.audit(c03=c03)

    def test_14_original_future_case_claim_executed_fails_closed(self):
        register = deepcopy(self.register)
        register["negativeScenarios"][0]["status"] = "EXECUTED_PASS"
        with self.assertRaises(CrossLaneIntegrityError):
            self.audit(register=register)

    def test_15_new_h03_future_negative_claim_executed_fails_closed(self):
        h03 = deepcopy(self.h03)
        h03["newH03FutureNegatives"][0]["status"] = "EXECUTED_PASS"
        with self.assertRaises(CrossLaneIntegrityError):
            self.audit(h03=h03)

    def test_16_fifth_explicit_issue110_question_missing_fails_closed(self):
        intake = deepcopy(self.intake)
        intake["explicitIssue110QuestionIds"].remove(ISSUE_110_H03_MEMBER)
        with self.assertRaises(CrossLaneIntegrityError):
            self.audit(intake=intake)

    def test_17_outside_h03_original_routing_lane_tamper_fails_closed(self):
        intake = deepcopy(self.intake)
        row = next(q for q in intake["questions"]
                   if q["id"] == "M12-S01-U05")
        row["intakeLane"] = "M12_PROPOSABLE_WITH_FROZEN_SOURCE_INPUTS"
        with self.assertRaises(CrossLaneIntegrityError):
            self.audit(intake=intake)

    def test_18_historical_current_b_direction_or_h03_grant_tamper_rejected(self):
        for key, value in (
            ("ownerSelectedTopologyDirection", "B_APPROVED_RUNTIME"),
            ("crossOwnerApproval", "APPROVED"),
            ("H03status", "CLOSED"),
        ):
            with self.subTest(key=key):
                h03 = deepcopy(self.h03)
                h03[key] = value
                with self.assertRaises(CrossLaneIntegrityError):
                    self.audit(h03=h03)


if __name__ == "__main__":
    unittest.main()
