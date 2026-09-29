"""IRIS-WO-0076: synthetic-only M14 S01 research/authority integrity regressions."""
from __future__ import annotations

from copy import deepcopy
import unittest

from scripts.verify_m14_s01_research import (
    ROOT, PACKET, REPORT, M14S01IntegrityError, read_json,
    render_report, unique_json_keys, verify_all, verify_packet,
)


class M14S01SourceResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = read_json(ROOT)

    def audit(self, packet=None, *, markdown=False):
        return verify_packet(
            self.packet if packet is None else packet, ROOT, verify_markdown=markdown
        )

    def copy(self):
        return deepcopy(self.packet)

    def test_01_original_source_and_exact_human_report_pass(self):
        proof = verify_all(ROOT)
        self.assertEqual(proof["originalM14S01QuestionsOpen"], 16)
        self.assertEqual(proof["futureNegativesSpecifiedNotExecuted"], 12)

    def test_02_nine_exact_git_original_source_hashes_and_anchors(self):
        self.assertEqual(self.audit()["originalSourcePinsVerified"], 9)

    def test_03_five_component_classes_remain_conceptual(self):
        self.assertEqual(self.audit()["conceptualComponentsUnadopted"], 5)
        self.assertTrue(all(x["status"] == "SOURCE_TAXONOMY_UNADOPTED"
                            for x in self.packet["componentClasses"]))

    def test_04_five_rights_facets_are_never_legal_authority(self):
        self.assertEqual(self.audit()["licenseFacetsUnverified"], 5)
        self.assertTrue(all(x["verification"] == "NOT_OWNER_VERIFIED"
                            for x in self.packet["licenseFacets"]))

    def test_05_four_research_alternatives_all_unselected(self):
        self.assertEqual(self.audit()["alternativesUnselected"], 4)
        self.assertTrue(all(x["selected"] is False
                            for x in self.packet["alternatives"]))

    def test_06_sixteen_owner_questions_open_and_unrated(self):
        self.assertEqual(len(self.packet["questions"]), 16)
        self.assertTrue(all(q["ownerAnswer"] is None
                            and q["risk"] == "UNRATED"
                            and q["status"] == "OPEN_UNRATED_PENDING_QUALIFIED_OWNER"
                            for q in self.packet["questions"]))

    def test_07_twelve_negative_designs_all_unexecuted(self):
        self.assertEqual(len(self.packet["negativeScenarios"]), 12)
        self.assertTrue(all(n["status"] == "SPECIFIED_NOT_EXECUTED"
                            for n in self.packet["negativeScenarios"]))

    def test_08_external_standards_are_only_reference_examples(self):
        self.assertEqual(self.audit()["externalReferencesOnly"], 3)
        self.assertTrue(all(x["status"] == "REFERENCE_ONLY_NOT_ADOPTED_OR_LEGAL_PROOF"
                            for x in self.packet["externalReferences"]))

    def test_09_original_owner_and_native_runtime_stops_unmodified(self):
        proof = self.audit()
        self.assertEqual(proof["qualifiedOwnerApprovals"], 0)
        self.assertEqual(self.packet["m10m11m12m13Runtime"], "NOT_ADMITTED")
        self.assertEqual(self.packet["ownerB"], "B_FUTURE_OWNER_RECEIPT_DIRECTION_ONLY")
        self.assertEqual(self.packet["originalM13QuestionsOpen"], 96)
        self.assertEqual(self.packet["originalM13FutureCasesNotExecuted"], 74)

    def test_10_original_source_git_sha_forgery_rejected(self):
        p = self.copy()
        p["sourceDocs"][1]["gitBlobSha1"] = "0" * 40
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)

    def test_11_forged_original_source_anchor_rejected(self):
        p = self.copy()
        p["sourceDocs"][2]["exactNeedle"] = "invented M14 owner approval"
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)

    def test_12_duplicate_original_source_role_rejected(self):
        p = self.copy()
        p["sourceDocs"][3]["role"] = "INDEX"
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)

    def test_13_missing_original_open_owner_question_rejected(self):
        p = self.copy()
        p["questions"].pop()
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)

    def test_14_reordered_original_question_ids_rejected(self):
        p = self.copy()
        p["questions"][0], p["questions"][1] = p["questions"][1], p["questions"][0]
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)

    def test_15_forged_owner_answer_rejected(self):
        p = self.copy()
        p["questions"][0]["ownerAnswer"] = "owner-approved commercial model"
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)

    def test_16_forged_question_risk_grade_rejected(self):
        p = self.copy()
        p["questions"][0]["risk"] = "LOW"
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)

    def test_17_executable_model_registry_authority_cannot_be_claimed(self):
        p = self.copy()
        p["questions"][0]["executableAuthority"] = "REGISTRY_LOAD_ALLOWED"
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)

    def test_18_future_hostile_scenario_cannot_be_marked_executed(self):
        p = self.copy()
        p["negativeScenarios"][0]["status"] = "EXECUTED_PASS"
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)

    def test_19_foreign_owner_question_in_negative_scenario_rejected(self):
        p = self.copy()
        p["negativeScenarios"][0]["questionIds"] = ["M12-S01-U01"]
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)

    def test_20_unqualified_technology_selection_rejected(self):
        p = self.copy()
        p["alternatives"][-1]["selected"] = True
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)

    def test_21_license_attestation_cannot_be_fabricated(self):
        p = self.copy()
        p["licenseFacets"][0]["verification"] = "LEGAL_OWNER_APPROVED"
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)

    def test_22_forged_empirical_model_cards_rejected(self):
        p = self.copy()
        p["empiricalModelCards"] = "REPRESENTATIVE_BENCHMARK_PASS"
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)

    def test_23_human_markdown_must_be_exact_machine_projection(self):
        self.assertEqual((ROOT / REPORT).read_text(encoding="utf-8"),
                         render_report(self.packet))
        p = self.copy()
        p["questions"][0]["question"] += " Altered without human report revision."
        with self.assertRaisesRegex(M14S01IntegrityError, "human M14 S01"):
            self.audit(p, markdown=True)

    def test_24_extra_signed_owner_and_duplicate_json_keys_rejected(self):
        p = self.copy()
        p["actualSignedOwner"] = "assistant-is-not-a-qualified-owner"
        with self.assertRaises(M14S01IntegrityError):
            self.audit(p)
        with self.assertRaisesRegex(M14S01IntegrityError, "duplicate JSON key"):
            unique_json_keys([("sourceBaseSha", "a" * 40),
                              ("sourceBaseSha", "b" * 40)])


if __name__ == "__main__":
    unittest.main()
