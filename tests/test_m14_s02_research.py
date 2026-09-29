"""WO0077: 24 strictly synthetic S02 source/owner/evidence Genome tests."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from scripts.verify_m14_s02_research import (
    ROOT, REPORT, M14S02IntegrityError, read_json, render_report,
    unique_json_keys, verify_all, verify_packet,
)


class M14S02SourceResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Load a shared exact source-only packet for all offline cases."""
        cls.packet = read_json(ROOT)

    def copy(self):
        """Clone the packet to isolate negative-case mutations."""
        return deepcopy(self.packet)

    def audit(self, p=None, markdown=False):
        """Validate a candidate packet without running any provider."""
        return verify_packet(self.packet if p is None else p, ROOT,
                             verify_markdown=markdown)

    def test_01_original_source_and_exact_report_pass(self):
        """Verify original source and exact report pass."""
        self.assertEqual(verify_all(ROOT)["newOpenOwnerQuestions"], 18)

    def test_02_twelve_original_git_sources_and_needles_pinned(self):
        """Verify twelve original git sources and needles pinned."""
        self.assertEqual(self.audit()["sourceShaAndAnchorsVerified"], 12)

    def test_03_six_dimensions_remain_nonbinding(self):
        """Verify six dimensions remain nonbinding."""
        self.assertEqual(self.audit()["unadoptedGenomeDimensions"], 6)

    def test_04_seven_task_families_unratified(self):
        """Verify seven task families unratified."""
        self.assertEqual(self.audit()["unratifiedTaskFamilies"], 7)

    def test_05_five_evidence_state_names_do_not_prove_real_receipt(self):
        """Verify five evidence state names do not prove real receipt."""
        self.assertEqual(self.audit()["vocabularyOnlyEvidenceStates"], 5)
        self.assertEqual(self.audit()["realOwnerReceipts"], 0)

    def test_06_four_taxonomy_alternatives_all_unselected(self):
        """Verify four taxonomy alternatives all unselected."""
        self.assertEqual(self.audit()["unselectedAlternatives"], 4)

    def test_07_eighteen_new_questions_open_unrated(self):
        """Verify eighteen new questions open unrated."""
        self.assertEqual(self.audit()["newOpenOwnerQuestions"], 18)
        self.assertTrue(all(x["ownerAnswer"] is None and x["risk"] == "UNRATED"
                            for x in self.packet["questions"]))

    def test_08_fourteen_future_negatives_not_executed(self):
        """Verify fourteen future negatives not executed."""
        self.assertEqual(self.audit()["futureNegativesUnexecuted"], 14)
        self.assertTrue(all(x["status"] == "SPECIFIED_NOT_EXECUTED"
                            for x in self.packet["negativeScenarios"]))

    def test_09_s01_and_prior_other_owner_stops_preserved(self):
        """Verify s01 and prior other owner stops preserved."""
        self.assertEqual(self.packet["priorM14S01QuestionsOpen"], 16)
        self.assertEqual(self.packet["priorM14S01NegativeCasesNotExecuted"], 12)
        self.assertEqual(self.packet["originalM13QuestionsOpen"], 96)
        self.assertEqual(self.packet["originalM13NegativesNotExecuted"], 74)
        self.assertEqual(self.packet["m10m11m12m13Runtime"], "NOT_ADMITTED")

    def test_10_forged_original_source_sha_denied(self):
        """Verify forged original source sha denied."""
        p = self.copy()
        p["sourceDocs"][0]["gitBlobSha1"] = "0" * 40
        with self.assertRaises(M14S02IntegrityError):
            self.audit(p)

    def test_11_forged_original_source_anchor_denied(self):
        """Verify forged original source anchor denied."""
        p = self.copy()
        p["sourceDocs"][3]["exactNeedle"] = "fabricated owner-signature"
        with self.assertRaises(M14S02IntegrityError):
            self.audit(p)

    def test_12_duplicated_source_role_denied(self):
        """Verify duplicated source role denied."""
        p = self.copy()
        p["sourceDocs"][3]["role"] = "INDEX"
        with self.assertRaises(M14S02IntegrityError):
            self.audit(p)

    def test_13_missing_original_dimension_denied(self):
        """Verify missing original dimension denied."""
        p = self.copy()
        p["dimensions"].pop()
        with self.assertRaises(M14S02IntegrityError):
            self.audit(p)

    def test_14_provider_claim_falsely_rated_as_actual_dimension_denied(self):
        """Verify provider claim falsely rated as actual dimension denied."""
        p = self.copy()
        p["dimensions"][0]["status"] = "VERIFIED_REAL_PROVIDER"
        with self.assertRaises(M14S02IntegrityError):
            self.audit(p)

    def test_15_task_type_cannot_be_promoted_to_approved(self):
        """Verify task type cannot be promoted to approved."""
        p = self.copy()
        p["taskFamilies"][1]["status"] = "ADOPTED_AND_BENCHMARKED"
        with self.assertRaises(M14S02IntegrityError):
            self.audit(p)

    def test_16_future_verified_evidence_label_is_not_real_proof(self):
        """Verify future verified evidence label is not real proof."""
        p = self.copy()
        p["evidenceStates"][3]["status"] = "REAL_OWNER_APPROVED"
        with self.assertRaises(M14S02IntegrityError):
            self.audit(p)

    def test_17_taxonomy_alternative_cannot_be_selected(self):
        """Verify taxonomy alternative cannot be selected."""
        p = self.copy()
        p["alternatives"][-1]["selected"] = True
        with self.assertRaises(M14S02IntegrityError):
            self.audit(p)

    def test_18_missing_new_owner_question_rejected(self):
        """Verify missing new owner question rejected."""
        p = self.copy()
        p["questions"].pop()
        with self.assertRaises(M14S02IntegrityError):
            self.audit(p)

    def test_19_forged_question_owner_answer_and_risk_rejected(self):
        """Verify forged question owner answer and risk rejected."""
        for key, value in (("ownerAnswer", "approved"),
                           ("risk", "LOW"),
                           ("executableAuthority", "MODEL_LOAD")):
            with self.subTest(key=key):
                p = self.copy()
                p["questions"][0][key] = value
                with self.assertRaises(M14S02IntegrityError):
                    self.audit(p)

    def test_20_future_hostile_test_cannot_be_marked_executed(self):
        """Verify future hostile test cannot be marked executed."""
        p = self.copy()
        p["negativeScenarios"][0]["status"] = "REAL_GPU_PASS"
        with self.assertRaises(M14S02IntegrityError):
            self.audit(p)

    def test_21_foreign_question_reference_denied(self):
        """Verify foreign question reference denied."""
        p = self.copy()
        p["negativeScenarios"][0]["questionIds"] = ["M12-S01-U01"]
        with self.assertRaises(M14S02IntegrityError):
            self.audit(p)

    def test_22_false_empirical_measurements_or_receipt_denied(self):
        """Verify false empirical measurements or receipt denied."""
        for key, value in (("realEmpiricalMeasurements", 1),
                           ("realCapabilityReceipts", 1),
                           ("capabilitySchemaAdopted", True)):
            with self.subTest(key=key):
                p = self.copy()
                p[key] = value
                with self.assertRaises(M14S02IntegrityError):
                    self.audit(p)

    def test_23_human_report_exact_machine_projection(self):
        """Verify human report exact machine projection."""
        self.assertEqual((ROOT / REPORT).read_text(encoding="utf-8"),
                         render_report(self.packet))
        p = self.copy()
        p["questions"][0]["question"] += " Updated without human report."
        with self.assertRaisesRegex(M14S02IntegrityError,
                                    "human M14 S02 source report"):
            self.audit(p, markdown=True)

    def test_24_extra_owner_signature_and_duplicate_json_keys_denied(self):
        """Verify extra owner signature and duplicate json keys denied."""
        p = self.copy()
        p["actualOwnerSignature"] = "assistant-pretending-to-sign"
        with self.assertRaises(M14S02IntegrityError):
            self.audit(p)
        with self.assertRaisesRegex(M14S02IntegrityError, "duplicate JSON key"):
            unique_json_keys([("ownerApproval", "NONE"),
                              ("ownerApproval", "APPROVED")])


    def test_25_missing_pinned_source_produces_typed_error_with_cause(self):
        """Verify missing pinned source produces typed error with cause."""
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(M14S02IntegrityError,
                                        "original source unreadable: INDEX") as raised:
                verify_packet(self.copy(), Path(tmp), verify_markdown=False)
            self.assertIsInstance(raised.exception.__cause__, FileNotFoundError)

    def test_26_invalid_utf8_source_produces_typed_error_with_cause(self):
        """Verify invalid utf8 source produces typed error with cause."""
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "planning/MASTER-MODULE-INDEX-CURRENT.md"
            first.parent.mkdir(parents=True, exist_ok=True)
            first.write_bytes(b"\xff invalid UTF-8 source")
            with self.assertRaisesRegex(M14S02IntegrityError,
                                        "original source unreadable: INDEX") as raised:
                verify_packet(self.copy(), Path(tmp), verify_markdown=False)
            self.assertIsInstance(raised.exception.__cause__, UnicodeDecodeError)


if __name__ == "__main__":
    unittest.main()
