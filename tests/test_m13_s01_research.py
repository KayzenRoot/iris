"""WO0045: strict M13 S01 documentary evidence, no actual cache activity."""
from __future__ import annotations

from copy import deepcopy
import unittest

from scripts.verify_m13_s01_research import (
    ROOT, read_json, verify_all, verify_packet, render_report,
    M13S01IntegrityError, PACKET, REPORT,
)


class M13S01SourceResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = read_json(ROOT)

    def audit(self, packet=None, *, markdown=False):
        return verify_packet(self.packet if packet is None else packet, ROOT,
                             verify_markdown=markdown)

    def test_01_source_and_exact_human_report_pass(self):
        result = verify_all(ROOT)
        self.assertEqual(result["originalM13S01QuestionsOpen"], 18)
        self.assertEqual(result["futureNegativeDesignsNotExecuted"], 12)

    def test_02_original_source_inputs_all_sha_and_anchors(self):
        self.assertEqual(self.audit()["sourceGitBlobPinsVerified"], 11)

    def test_03_original_18_questions_remain_unanswered(self):
        for question in self.packet["questions"]:
            self.assertEqual(question["status"],
                             "OPEN_UNRATED_PENDING_QUALIFIED_OWNER")
            self.assertEqual(question["risk"], "UNRATED")
            self.assertIsNone(question["ownerAnswer"])
            self.assertEqual(question["executableAuthority"], "NONE")

    def test_04_all_12_original_future_negatives_unexecuted(self):
        self.assertEqual(self.audit()["futureNegativeDesignsNotExecuted"], 12)
        for scenario in self.packet["negativeScenarios"]:
            self.assertEqual(scenario["status"], "SPECIFIED_NOT_EXECUTED")

    def test_05_all_five_cache_classes_not_adopted(self):
        self.assertEqual(self.audit()["cacheClassesNotAdopted"], 5)

    def test_06_all_four_architectural_candidates_unselected(self):
        self.assertEqual(self.audit()["alternativesNotSelected"], 4)
        self.assertTrue(all(x["selected"] is False
                            for x in self.packet["alternatives"]))

    def test_07_ten_metric_protocols_never_claim_real_measurements(self):
        self.assertEqual(self.audit()["coldWarmMetricProtocolsNotMeasured"], 10)
        self.assertFalse(self.packet["measurementPlan"]["adoptedNumericThresholds"])

    def test_08_no_owner_gate_or_runtime_claim(self):
        result = self.audit()
        self.assertEqual(result["realOwnerApprovals"], 0)
        self.assertEqual(result["H01H02H03H04"],
                         "ALL_OPEN_HIGH_FOR_FUTURE_FREEZE")
        self.assertEqual(result["M10M11M12Runtime"], "NOT_ADMITTED")

    def test_09_unknown_source_sha_rejected(self):
        packet = deepcopy(self.packet)
        packet["sourceDocs"][1]["gitBlobSha1"] = "0" * 40
        with self.assertRaises(M13S01IntegrityError):
            self.audit(packet)

    def test_10_changed_source_needle_rejected(self):
        packet = deepcopy(self.packet)
        packet["sourceDocs"][2]["exactNeedle"] = "invented grant"
        with self.assertRaises(M13S01IntegrityError):
            self.audit(packet)

    def test_11_duplicate_and_wrong_source_role_rejected(self):
        packet = deepcopy(self.packet)
        packet["sourceDocs"][1]["role"] = "INDEX"
        with self.assertRaises(M13S01IntegrityError):
            self.audit(packet)

    def test_12_missing_original_question_rejected(self):
        packet = deepcopy(self.packet)
        packet["questions"].pop()
        with self.assertRaises(M13S01IntegrityError):
            self.audit(packet)

    def test_13_reordered_original_question_rejected(self):
        packet = deepcopy(self.packet)
        packet["questions"][0], packet["questions"][1] = (
            packet["questions"][1], packet["questions"][0])
        with self.assertRaises(M13S01IntegrityError):
            self.audit(packet)

    def test_14_fake_owner_answer_and_risk_scores_rejected(self):
        for field, value in (("ownerAnswer", "approved by everyone"),
                             ("risk", "LOW"),
                             ("status", "APPROVED")):
            with self.subTest(field=field):
                packet = deepcopy(self.packet)
                packet["questions"][0][field] = value
                with self.assertRaises(M13S01IntegrityError):
                    self.audit(packet)

    def test_15_cache_class_forged_adoption_rejected(self):
        packet = deepcopy(self.packet)
        packet["cacheClasses"][0]["status"] = "ADOPTED"
        with self.assertRaises(M13S01IntegrityError):
            self.audit(packet)

    def test_16_selected_prefetch_candidate_rejected(self):
        packet = deepcopy(self.packet)
        packet["alternatives"][-1]["selected"] = True
        with self.assertRaises(M13S01IntegrityError):
            self.audit(packet)

    def test_17_claimed_hardware_metrics_rejected(self):
        packet = deepcopy(self.packet)
        packet["measurementPlan"]["metrics"][0]["status"] = "MEASURED_PASS"
        with self.assertRaises(M13S01IntegrityError):
            self.audit(packet)

    def test_18_fake_executed_future_scenario_rejected(self):
        packet = deepcopy(self.packet)
        packet["negativeScenarios"][0]["status"] = "EXECUTED_PASS"
        with self.assertRaises(M13S01IntegrityError):
            self.audit(packet)

    def test_19_cross_tenant_scenario_cannot_point_to_foreign_question(self):
        packet = deepcopy(self.packet)
        packet["negativeScenarios"][0]["questionIds"] = ["M12-S01-U01"]
        with self.assertRaises(M13S01IntegrityError):
            self.audit(packet)

    def test_20_current_b_and_c01_status_not_promoted(self):
        for field, value in (("ownerB", "B_RUNTIME_APPROVED"),
                             ("m09C01", "FROZEN"),
                             ("h01h02h03h04", "ALL_CLOSED"),
                             ("runtime", "ADMITTED")):
            with self.subTest(field=field):
                packet = deepcopy(self.packet)
                packet[field] = value
                with self.assertRaises(M13S01IntegrityError):
                    self.audit(packet)

    def test_21_stale_human_report_rejected(self):
        packet = deepcopy(self.packet)
        packet["questions"][0]["question"] += " Mutated."
        with self.assertRaisesRegex(M13S01IntegrityError,
                                    "human M13 S01 source report"):
            self.audit(packet, markdown=True)

    def test_22_extra_fake_owner_signature_field_rejected(self):
        packet = deepcopy(self.packet)
        packet["actualSignedOwner"] = "pretend-reviewer"
        with self.assertRaises(M13S01IntegrityError):
            self.audit(packet)

    def test_23_report_matches_exact_machine_projection(self):
        self.assertEqual((ROOT / REPORT).read_text(encoding="utf-8"),
                         render_report(self.packet))

    def test_24_all_source_roles_and_s01_index_canonical(self):
        result = self.audit()
        self.assertEqual(result["sourceGitBlobPinsVerified"], 11)
        self.assertIn("S01", (ROOT / REPORT).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
