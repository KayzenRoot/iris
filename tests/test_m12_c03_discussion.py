"""Fail-closed tests for 19 original nonbinding M12 C03 discussion packets."""
from __future__ import annotations

import json
import unittest
from copy import deepcopy

from scripts.verify_m12_c03_discussion import (
    ROOT, PACKET, ROUTING, REGISTER, C02, ROLES, EXPECTED, LANE, REPORT,
    DiscussionEvidenceError, read_json, render_report, verify_packet, verify_all,
    git_blob_sha,
)


class C03DiscussionEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = read_json(ROOT, PACKET)
        cls.route = read_json(ROOT, ROUTING)
        cls.reg = read_json(ROOT, REGISTER)
        cls.c02 = read_json(ROOT, C02)

    def audit(self, packet=None, route=None, register=None, c02=None):
        return verify_packet(
            self.packet if packet is None else packet,
            self.route if route is None else route,
            self.reg if register is None else register,
            self.c02 if c02 is None else c02,
            ROOT,
        )

    def test_exact_main_source_packet_and_report(self):
        self.assertEqual(verify_all(ROOT)["discussionPackets"], 19)

    def test_all_19_match_original_unrated_questions(self):
        self.assertEqual([q["id"] for q in self.packet["proposals"]],
                         [q["id"] for q in self.route["questions"]
                          if q["intakeLane"] == LANE])
        self.assertTrue(all(q["ownerDecisionStatus"] == "OPEN_UNRATED_PENDING_OWNER"
                            and q["risk"] == "UNRATED" for q in self.packet["proposals"]))

    def test_all_80_original_negatives_unexecuted(self):
        self.assertEqual(len(self.reg["negativeScenarios"]), 80)
        self.assertTrue(all(q["oraclesStatus"] == "SPECIFIED_NOT_EXECUTED"
                            for q in self.packet["proposals"]))

    def test_exact_original_future_oracle_session_references(self):
        original = {q["id"]: q["session"] for q in self.reg["negativeScenarios"]}
        for q in self.packet["proposals"]:
            self.assertTrue(all(original[r] == q["session"]
                                for r in q["existingFutureOracleIds"]))

    def test_global_hard_stop_four_highs_and_no_owner_decision(self):
        self.assertEqual(self.packet["openHighs"],
                         [f"C02-FR-H{i:02d}" for i in range(1, 5)])
        self.assertEqual(self.packet["ownerApprovals"], 0)
        self.assertEqual(self.packet["selectedM09Topology"], "NONE_SELECTED")
        self.assertEqual(self.packet["runtime"], "M10_M11_M12_NOT_ADMITTED")

    def test_pinned_source_git_blob_hashes_match(self):
        for record in self.packet["sourceDocs"]:
            actual = git_blob_sha((ROOT / record["path"]).read_bytes())
            self.assertEqual(actual, record["gitBlobSha1"])

    def test_human_report_is_exact_projection(self):
        self.assertEqual((ROOT / REPORT).read_text(encoding="utf-8"),
                         render_report(self.packet["proposals"]))

    def test_other_91_owner_questions_remain_untouched(self):
        ids = {q["id"] for q in self.packet["proposals"]}
        self.assertEqual(len(self.reg["questions"]) - len(ids), 91)
        self.assertTrue(all(q["status"] == "OPEN_UNRATED_PENDING_OWNER"
                            for q in self.reg["questions"] if q["id"] not in ids))

    def test_all_five_source_document_roles_present(self):
        self.assertEqual([q["role"] for q in self.packet["sourceDocs"]],
                         list(ROLES))

    def test_no_unapproved_positive_authority_or_risk_granted(self):
        for q in self.packet["proposals"]:
            self.assertEqual(q["ownerApproval"], "NONE")
            self.assertEqual(q["executableAuthority"], "NONE")
            self.assertEqual(q["candidateStatus"],
                             "NONBINDING_SOURCE_CONSTRAINED_DISCUSSION")

    def test_all_19_have_falsifiable_gaps_and_existing_future_case_ids(self):
        self.assertTrue(all(len(q["gap"]) >= 65 and
                            q["existingFutureOracleIds"] for q in self.packet["proposals"]))

    def test_19_declared_negative_oracle_and_high_mappings_fixed(self):
        self.assertEqual([(q["id"], q["existingFutureOracleIds"], q["linkedInheritedHighs"])
                          for q in self.packet["proposals"]],
                         [(id, list(cases), list(highs)) for id, cases, highs in EXPECTED])

    def test_forged_owner_approval_rejected(self):
        packet = deepcopy(self.packet)
        packet["proposals"][0]["ownerApproval"] = "APPROVED"
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_forged_approved_question_rejected(self):
        packet = deepcopy(self.packet)
        packet["proposals"][0]["ownerDecisionStatus"] = "APPROVED"
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_forged_risk_rating_rejected(self):
        packet = deepcopy(self.packet)
        packet["proposals"][0]["risk"] = "LOW"
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_forged_runtime_authority_rejected(self):
        packet = deepcopy(self.packet)
        packet["proposals"][0]["executableAuthority"] = "ADMITTED"
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_fake_executed_future_case_rejected(self):
        packet = deepcopy(self.packet)
        packet["proposals"][0]["oraclesStatus"] = "EXECUTED_PASS"
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_modified_original_question_rejected(self):
        packet = deepcopy(self.packet)
        packet["proposals"][1]["originalQuestion"] = "Invented owner answer"
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_modified_original_owner_label_rejected(self):
        packet = deepcopy(self.packet)
        packet["proposals"][1]["originalOwners"] = "M12"
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_wrong_future_test_from_other_session_rejected(self):
        packet = deepcopy(self.packet)
        packet["proposals"][0]["existingFutureOracleIds"] = ["FT-19"]
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_fabricated_original_oracle_reference_rejected(self):
        packet = deepcopy(self.packet)
        packet["proposals"][0]["existingFutureOracleIds"] = ["WR-99"]
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_omitted_packet_rejected(self):
        packet = deepcopy(self.packet)
        packet["proposals"].pop()
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_duplicated_and_reordered_packets_rejected(self):
        packet = deepcopy(self.packet)
        packet["proposals"][0] = deepcopy(packet["proposals"][1])
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_forged_source_anchor_rejected(self):
        packet = deepcopy(self.packet)
        packet["proposals"][0]["anchors"][0]["exactNeedle"] = "owner approved"
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_forged_source_git_blob_sha_rejected(self):
        packet = deepcopy(self.packet)
        packet["sourceDocs"][0]["gitBlobSha1"] = "0" * 40
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_omitted_original_owner_source_rejected(self):
        packet = deepcopy(self.packet)
        packet["proposals"][1]["anchors"].pop()
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_fabricated_issue110_topology_rejected(self):
        packet = deepcopy(self.packet)
        packet["selectedM09Topology"] = "A"
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_legacy_high_closed_without_owner_proof_rejected(self):
        c02 = deepcopy(self.c02)
        c02["futureFreezeBlockers"][0]["status"] = "CLOSED"
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(c02=c02)

    def test_missing_high_c02_rejected(self):
        c02 = deepcopy(self.c02)
        c02["futureFreezeBlockers"].pop()
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(c02=c02)

    def test_original_register_fake_approval_rejected(self):
        reg = deepcopy(self.reg)
        reg["questions"][0]["status"] = "CLOSED"
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(register=reg)

    def test_original_register_fake_executed_case_rejected(self):
        reg = deepcopy(self.reg)
        reg["negativeScenarios"][0]["status"] = "EXECUTED_PASS"
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(register=reg)

    def test_proposal_and_proof_gap_cannot_go_blank(self):
        for name in ("proposal", "gap"):
            with self.subTest(name=name):
                packet = deepcopy(self.packet)
                packet["proposals"][2][name] = ""
                with self.assertRaises(DiscussionEvidenceError):
                    self.audit(packet=packet)

    def test_original_c02_intake_lane_cannot_be_promoted(self):
        route = deepcopy(self.route)
        route["questions"][0]["intakeLane"] = LANE
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(route=route)

    def test_source_docs_wrong_role_rejected(self):
        packet = deepcopy(self.packet)
        packet["sourceDocs"][0]["role"] = "M99"
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_packet_global_owner_approval_rejected(self):
        packet = deepcopy(self.packet)
        packet["ownerApprovals"] = 1
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)

    def test_packet_global_future_test_execution_rejected(self):
        packet = deepcopy(self.packet)
        packet["counts"]["futureOriginalOraclesNotExecuted"] = 79
        with self.assertRaises(DiscussionEvidenceError):
            self.audit(packet=packet)


if __name__ == "__main__":
    unittest.main()
