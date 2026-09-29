"""WO0078: 24 source-only S03 empirical-card integrity regression tests."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from scripts.verify_m14_s03_research import (
    ROOT, REPORT, M14S03IntegrityError, read_json, render_report,
    unique_json_keys, verify_all, verify_packet,
)


class M14S03SourceResearchTests(unittest.TestCase):
    """Exercise only synthetic source/authority failures, never real benchmarks."""

    @classmethod
    def setUpClass(cls):
        """Load the exact source-only M14 S03 packet for synthetic regression cases."""
        cls.packet = read_json(ROOT)

    def copy(self):
        """Clone the packet before an isolated negative-case mutation."""
        return deepcopy(self.packet)

    def audit(self, packet=None, *, markdown=False):
        """Audit an offline packet without performing external provider work."""
        return verify_packet(self.packet if packet is None else packet, ROOT,
                             verify_markdown=markdown)

    def test_01_original_sources_and_machine_human_report_pass(self):
        """Check original sources and machine human report pass."""
        self.assertEqual(verify_all(ROOT)["exactOriginalSources"], 12)

    def test_02_twelve_git_original_sha_and_anchor_paths_verified(self):
        """Check twelve git original sha and anchor paths verified."""
        self.assertEqual(self.audit()["exactOriginalSources"], 12)

    def test_03_eight_facets_never_promoted_to_real_measurement(self):
        """Check eight facets never promoted to real measurement."""
        self.assertEqual(self.audit()["unadoptedFacets"], 8)

    def test_04_five_empirical_labels_are_vocabulary_only(self):
        """Check five empirical labels are vocabulary only."""
        self.assertEqual(self.audit()["futureEvidenceLabelsOnly"], 5)

    def test_05_four_design_alternatives_are_unselected(self):
        """Check four design alternatives are unselected."""
        self.assertEqual(self.audit()["unselectedAlternatives"], 4)

    def test_06_twenty_s03_owner_questions_are_open_unrated(self):
        """Check twenty s03 owner questions are open unrated."""
        self.assertEqual(self.audit()["newOpenOwnerQuestions"], 20)
        self.assertTrue(all(x["ownerAnswer"] is None for x in self.packet["questions"]))

    def test_07_sixteen_future_negative_designs_are_unexecuted(self):
        """Check sixteen future negative designs are unexecuted."""
        self.assertEqual(self.audit()["futureCasesNotExecuted"], 16)
        self.assertTrue(all(x["status"] == "SPECIFIED_NOT_EXECUTED"
                            for x in self.packet["negativeScenarios"]))

    def test_08_s01_s02_and_m13_original_counters_unchanged(self):
        """Check s01 s02 and m13 original counters unchanged."""
        p = self.packet
        self.assertEqual((p["previousS01QuestionsOpen"], p["previousS01FutureCases"],
                          p["previousS02QuestionsOpen"], p["previousS02FutureCases"],
                          p["previousM13QuestionsOpen"], p["previousM13FutureCases"]),
                         (16, 12, 18, 14, 96, 74))

    def test_09_owner_authority_and_real_measurement_counts_zero(self):
        """Check owner authority and real measurement counts zero."""
        self.assertEqual(self.audit()["actualPhysicalMeasurements"], 0)
        self.assertEqual(self.packet["m10m11m12m13Runtime"], "NOT_ADMITTED")

    def test_10_mutated_original_source_blob_sha_is_rejected(self):
        """Check mutated original source blob sha is rejected."""
        p = self.copy()
        p["sourceDocs"][0]["gitBlobSha1"] = "0" * 40
        with self.assertRaises(M14S03IntegrityError):
            self.audit(p)

    def test_11_mutated_original_source_needle_is_rejected(self):
        """Check mutated original source needle is rejected."""
        p = self.copy()
        p["sourceDocs"][1]["exactNeedle"] = "fabricated M14 license approval"
        with self.assertRaises(M14S03IntegrityError):
            self.audit(p)

    def test_12_missing_original_source_yields_typed_error_with_cause(self):
        """Check missing original source yields typed error with cause."""
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(M14S03IntegrityError,
                                        "original source unreadable: INDEX") as raised:
                verify_packet(self.copy(), Path(tmp), verify_markdown=False)
            self.assertIsInstance(raised.exception.__cause__, FileNotFoundError)

    def test_13_invalid_utf8_original_source_yields_typed_error_with_cause(self):
        """Check invalid utf8 original source yields typed error with cause."""
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "planning/MASTER-MODULE-INDEX-CURRENT.md"
            first.parent.mkdir(parents=True, exist_ok=True)
            first.write_bytes(b"\xff\xfe not valid source UTF-8")
            with self.assertRaisesRegex(M14S03IntegrityError,
                                        "original source unreadable: INDEX") as raised:
                verify_packet(self.copy(), Path(tmp), verify_markdown=False)
            self.assertIsInstance(raised.exception.__cause__, UnicodeDecodeError)

    def test_14_truncated_evidence_boundary_is_rejected(self):
        """Check truncated evidence boundary is rejected."""
        p = self.copy()
        p["facets"][0]["boundary"] = "Vendor says benchmark complete."
        with self.assertRaises(M14S03IntegrityError):
            self.audit(p)

    def test_15_future_measurement_state_cannot_claim_actual_record(self):
        """Check future measurement state cannot claim actual record."""
        p = self.copy()
        p["states"][3]["status"] = "REAL_MEASUREMENT_APPROVED"
        with self.assertRaises(M14S03IntegrityError):
            self.audit(p)

    def test_16_design_alternative_cannot_be_selected_implicitly(self):
        """Check design alternative cannot be selected implicitly."""
        p = self.copy()
        p["alternatives"][3]["selected"] = True
        with self.assertRaises(M14S03IntegrityError):
            self.audit(p)

    def test_17_missing_new_open_owner_question_is_rejected(self):
        """Check missing new open owner question is rejected."""
        p = self.copy()
        p["questions"].pop()
        with self.assertRaises(M14S03IntegrityError):
            self.audit(p)

    def test_18_fake_owner_question_answer_is_rejected(self):
        """Check fake owner question answer is rejected."""
        p = self.copy()
        p["questions"][0]["ownerAnswer"] = "signed"
        with self.assertRaises(M14S03IntegrityError):
            self.audit(p)

    def test_19_fake_risk_score_from_synthetic_evidence_is_rejected(self):
        """Check fake risk score from synthetic evidence is rejected."""
        p = self.copy()
        p["questions"][0]["risk"] = "LOW"
        with self.assertRaises(M14S03IntegrityError):
            self.audit(p)

    def test_20_fake_runtime_authority_from_owner_question_is_rejected(self):
        """Check fake runtime authority from owner question is rejected."""
        p = self.copy()
        p["questions"][0]["authority"] = "GPU_BENCHMARK_ALLOWED"
        with self.assertRaises(M14S03IntegrityError):
            self.audit(p)

    def test_21_future_negative_case_cannot_be_marked_executed(self):
        """Check future negative case cannot be marked executed."""
        p = self.copy()
        p["negativeScenarios"][0]["status"] = "PASS_ON_REAL_HARDWARE"
        with self.assertRaises(M14S03IntegrityError):
            self.audit(p)

    def test_22_foreign_question_in_negative_case_is_rejected(self):
        """Check foreign question in negative case is rejected."""
        p = self.copy()
        p["negativeScenarios"][0]["questionIds"] = ["M14-S02-U01"]
        with self.assertRaises(M14S03IntegrityError):
            self.audit(p)

    def test_23_fake_empirical_values_and_qualified_owner_rejected(self):
        """Check fake empirical values and qualified owner rejected."""
        for key, val in (("realMeasurements", 1), ("realQualityScores", 1),
                         ("realLatencySamples", 1), ("realVramObservations", 1),
                         ("ownerApproval", "APPROVED"), ("schemaAdopted", True)):
            with self.subTest(field=key):
                p = self.copy()
                p[key] = val
                with self.assertRaises(M14S03IntegrityError):
                    self.audit(p)

    def test_24_exact_human_report_and_duplicate_json_key_rejection(self):
        """Check exact human report and duplicate json key rejection."""
        self.assertEqual((ROOT / REPORT).read_text(encoding="utf-8"),
                         render_report(self.packet))
        p = self.copy()
        p["questions"][0]["question"] += " Unmirrored human edit."
        with self.assertRaisesRegex(M14S03IntegrityError, "human S03 source report"):
            self.audit(p, markdown=True)
        with self.assertRaisesRegex(M14S03IntegrityError, "duplicate JSON key"):
            unique_json_keys([("ownerApproval", "NONE"),
                              ("ownerApproval", "APPROVED")])


if __name__ == "__main__":
    unittest.main()
