"""M12 C02 owner-intake source routing: deterministic fail-closed documentary tests."""
from __future__ import annotations

import json
import unittest
from copy import deepcopy

from scripts.verify_m12_planning_evidence import ROOT, unique_json
from scripts.verify_m12_owner_intake import (
    REGISTER, C02, INDEX, ROUTING, LANES, IntakeRoutingError,
    parse_owner_label, later_owner_ids, build_routing, verify_routing,
)


class M12OwnerIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.register = json.loads((ROOT / REGISTER).read_text(encoding="utf-8"),
                                  object_pairs_hook=unique_json)
        cls.c02 = json.loads((ROOT / C02).read_text(encoding="utf-8"),
                             object_pairs_hook=unique_json)
        cls.index = (ROOT / INDEX).read_text(encoding="utf-8")
        cls.matrix = json.loads((ROOT / ROUTING).read_text(encoding="utf-8"),
                                object_pairs_hook=unique_json)
        cls.later = later_owner_ids(cls.index)

    def build(self, register=None, c02=None, index=None):
        return build_routing(self.register if register is None else register,
                             self.c02 if c02 is None else c02,
                             self.index if index is None else index)

    def test_exact_canonical_repository_integrity(self):
        self.assertEqual(self.build(), self.matrix)
        self.assertEqual(verify_routing(ROOT)["questions"], 110)

    def test_all_110_open_questions_and_80_future_cases_retained(self):
        self.assertEqual(len(self.matrix["questions"]), 110)
        self.assertEqual(sum(x["count"] for x in self.matrix["futureNegatives"].values()), 80)
        self.assertTrue(all(x["ownerDecisionStatus"] == "OPEN_UNRATED_PENDING_OWNER"
                            and x["risk"] == "UNRATED" and x["executableAuthority"] == "NONE"
                            for x in self.matrix["questions"]))

    def test_review_lanes_partition_exactly_once(self):
        queues = self.matrix["reviewLanes"]
        ids = [id for name in LANES for id in queues[name]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {q["id"] for q in self.register["questions"]})

    def test_derived_lane_counts_are_exact_and_not_risk_rankings(self):
        self.assertEqual(self.matrix["counts"]["byLane"], dict(zip(LANES, (5, 70, 13, 3, 19))))
        self.assertEqual(self.matrix["priorityOrOwnerChoice"], "NOT_ASSIGNED_BY_ROUTING")

    def test_five_explicit_110_questions_from_all_five_sessions(self):
        self.assertEqual(self.matrix["explicitIssue110QuestionIds"], [
            "M12-S01-U05", "M12-S02-U08", "M12-S03-U02", "M12-S04-U06", "M12-S05-U04",
        ])

    def test_source_sessions_and_negative_counts(self):
        self.assertEqual([self.matrix["sessions"][s]["questionCount"]
                          for s in ("S01", "S02", "S03", "S04", "S05")], [18, 20, 22, 24, 26])
        self.assertEqual([self.matrix["futureNegatives"][s]["count"]
                          for s in ("S01", "S02", "S03", "S04", "S05")], [12, 14, 16, 18, 20])

    def test_17_source_owner_queues_are_overlapping_not_17_approvals(self):
        q = self.matrix["ownerQueues"]
        self.assertEqual(len(q), 17)
        self.assertEqual((len(q["M12"]), len(q["M54"]), len(q["M60"])), (72, 39, 27))
        self.assertEqual(self.matrix["ownerApproval"], "NONE_RECORDED")

    def test_19_m12_source_research_candidates_have_no_owner_adoption(self):
        ids = set(self.matrix["reviewLanes"]["M12_PROPOSABLE_WITH_FROZEN_SOURCE_INPUTS"])
        self.assertEqual(len(ids), 19)
        self.assertTrue(all(set(x["ownerIds"]) <= {"M02", "M06", "M09", "M10", "M12"}
                            and "M12" in x["ownerIds"] and not x["explicitIssue110"]
                            and x["executableAuthority"] == "NONE"
                            for x in self.matrix["questions"] if x["id"] in ids))

    def test_70_later_contract_dependencies_are_index_only(self):
        ids = set(self.matrix["reviewLanes"]["LATER_OWNER_CONTRACT_REQUIRED"])
        self.assertEqual(len(ids), 70)
        self.assertTrue(all(x["laterIndexOnlyOwners"]
                            for x in self.matrix["questions"] if x["id"] in ids))
        self.assertEqual(len(self.matrix["ownerSourceTiers"]["futureIndexOnlyOwners"]), 48)

    def test_13_m11_cross_owner_candidates_not_frozen(self):
        ids = set(self.matrix["reviewLanes"]["M11_CANDIDATE_CROSS_OWNER_REVIEW"])
        self.assertEqual(len(ids), 13)
        self.assertTrue(all("M11" in x["pendingCandidateOwners"]
                            and not x["laterIndexOnlyOwners"] and not x["explicitIssue110"]
                            for x in self.matrix["questions"] if x["id"] in ids))

    def test_three_frozen_source_owner_handoffs_still_require_review(self):
        ids = set(self.matrix["reviewLanes"]["FROZEN_OWNER_HANDOFF_REVIEW"])
        self.assertEqual(len(ids), 3)
        self.assertTrue(all("M12" not in x["ownerIds"] and
                            set(x["ownerIds"]) <= {"M02", "M06", "M09", "M10"}
                            for x in self.matrix["questions"] if x["id"] in ids))

    def test_no_positive_topology_api_runtime_or_risk_certification(self):
        for name, exact in (
            ("status", "ROUTING_ONLY_ALL_OWNER_DECISIONS_PENDING"),
            ("selectedTopology", "NONE"),
            ("publicOrExecutablePort", "NONE"),
            ("implementationStatus", "NOT_ADMITTED"),
            ("futureNegativeStatus", "SPECIFIED_NOT_EXECUTED"),
        ):
            self.assertEqual(self.matrix[name], exact)
        self.assertTrue(all(x["status"].startswith("OPEN_") and
                            x["severity"] == "HIGH_FOR_FUTURE_FREEZE"
                            for x in self.matrix["unresolvedHighs"]))

    def test_exact_question_wording_source_and_owner_labels_retained(self):
        for origin, route in zip(self.register["questions"], self.matrix["questions"]):
            self.assertEqual((origin["id"], origin["question"], origin["source"], origin["owners"]),
                             (route["id"], route["question"], route["source"], route["exactOwnerLabel"]))

    def test_future_case_ids_are_exact_and_still_unexecuted(self):
        for session, data in self.matrix["futureNegatives"].items():
            cases = [n for n in self.register["negativeScenarios"] if n["session"] == session]
            self.assertEqual(data["ids"], [n["id"] for n in cases])
            self.assertEqual(data["status"], "SPECIFIED_NOT_EXECUTED")

    def test_source_c02_four_highs_preserved(self):
        self.assertEqual([x["id"] for x in self.matrix["unresolvedHighs"]],
                         [f"C02-FR-H{i:02d}" for i in range(1, 5)])
        self.assertEqual(self.c02["issue110OwnerDecision"], "NOT_RECORDED")

    def test_unknown_owner_module_rejected(self):
        with self.assertRaisesRegex(IntakeRoutingError, "source tier"):
            parse_owner_label("M12/M61", self.later)

    def test_duplicate_owner_rejected(self):
        with self.assertRaisesRegex(IntakeRoutingError, "duplicated"):
            parse_owner_label("M12/M12", self.later)

    def test_issue110_without_m09_rejected(self):
        with self.assertRaisesRegex(IntakeRoutingError, "alongside M09"):
            parse_owner_label("M12/#110", self.later)

    def test_duplicate_issue110_marker_rejected(self):
        with self.assertRaisesRegex(IntakeRoutingError, "once"):
            parse_owner_label("M09/#110/#110", self.later)

    def test_malformed_or_empty_owner_rejected(self):
        for label in ("", "M12, M54", "M12/M54 ", "M12//M54", "#110", None):
            with self.subTest(label=label), self.assertRaises(IntakeRoutingError):
                parse_owner_label(label, self.later)

    def test_forged_positive_owner_question_is_rejected(self):
        forged = deepcopy(self.register)
        forged["questions"][0]["status"] = "APPROVED"
        with self.assertRaisesRegex(IntakeRoutingError, "falsely approved"):
            self.build(register=forged)

    def test_forged_executed_future_case_rejected(self):
        forged = deepcopy(self.register)
        forged["negativeScenarios"][0]["status"] = "PASS"
        with self.assertRaisesRegex(IntakeRoutingError, "non-execution"):
            self.build(register=forged)

    def test_missing_question_rejected(self):
        forged = deepcopy(self.register)
        forged["questions"].pop()
        with self.assertRaisesRegex(IntakeRoutingError, "110 unresolved"):
            self.build(register=forged)

    def test_duplicate_original_question_rejected(self):
        forged = deepcopy(self.register)
        forged["questions"][0]["id"] = forged["questions"][1]["id"]
        with self.assertRaisesRegex(IntakeRoutingError, "missing/duplicate"):
            self.build(register=forged)

    def test_missing_future_scenario_rejected(self):
        forged = deepcopy(self.register)
        forged["negativeScenarios"].pop()
        with self.assertRaisesRegex(IntakeRoutingError, "80 unexecuted"):
            self.build(register=forged)

    def test_m12_status_promotion_rejected(self):
        forged = deepcopy(self.register)
        forged["status"] = "FROZEN"
        with self.assertRaisesRegex(IntakeRoutingError, "promoted"):
            self.build(register=forged)

    def test_runtime_port_promotion_rejected(self):
        forged = deepcopy(self.register)
        forged["publicOrExecutablePort"] = "ACTIVE"
        with self.assertRaisesRegex(IntakeRoutingError, "promoted"):
            self.build(register=forged)

    def test_missing_hard_dependency_rejected(self):
        forged = deepcopy(self.register)
        forged["unresolvedHardDependencies"].remove("C02_FR_H02_OPEN")
        with self.assertRaisesRegex(IntakeRoutingError, "dependency"):
            self.build(register=forged)

    def test_m09_fake_owner_selection_requires_new_review(self):
        forged = deepcopy(self.c02)
        forged["issue110OwnerDecision"] = "B"
        with self.assertRaisesRegex(IntakeRoutingError, "new source-locked"):
            self.build(c02=forged)

    def test_closing_one_high_without_proof_rejected(self):
        forged = deepcopy(self.c02)
        forged["futureFreezeBlockers"][0]["status"] = "CLOSED"
        with self.assertRaisesRegex(IntakeRoutingError, "HIGH blockers"):
            self.build(c02=forged)

    def test_missing_one_high_rejected(self):
        forged = deepcopy(self.c02)
        forged["futureFreezeBlockers"].pop()
        with self.assertRaisesRegex(IntakeRoutingError, "HIGH blockers"):
            self.build(c02=forged)

    def test_later_owner_heading_missing_rejected(self):
        forged = self.index.replace("### M54 —", "### MXX —", 1)
        with self.assertRaisesRegex(IntakeRoutingError, "48 canonical"):
            self.build(index=forged)

    def test_owner_label_change_cannot_silently_reuse_old_routing(self):
        forged = deepcopy(self.register)
        forged["questions"][0]["owners"] = "M12/M54"
        self.assertNotEqual(self.build(register=forged), self.matrix)

    def test_question_text_change_cannot_silently_reuse_old_routing(self):
        forged = deepcopy(self.register)
        forged["questions"][0]["question"] = "Fabricated owner approval"
        self.assertNotEqual(self.build(register=forged), self.matrix)

    def test_routing_lane_forgery_does_not_match_derived_evidence(self):
        forged = deepcopy(self.matrix)
        forged["counts"]["byLane"]["M12_PROPOSABLE_WITH_FROZEN_SOURCE_INPUTS"] = 110
        self.assertNotEqual(forged, self.build())

    def test_duplicate_json_keys_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            json.loads('{"ownerApproval":"NONE","ownerApproval":"ACCEPTED"}',
                       object_pairs_hook=unique_json)


if __name__ == "__main__":
    unittest.main()
