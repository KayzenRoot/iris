"""WO0079: 24 strictly offline S04 source/authority integrity regressions."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from scripts.verify_m14_s04_research import (
    ROOT, REPORT, M14S04IntegrityError, read_json, render_report,
    unique_json_keys, verify_all, verify_packet,
)


class M14S04SourceResearchTests(unittest.TestCase):
    """Test documentary invariants only; never run a provider or hardware probe."""

    @classmethod
    def setUpClass(cls):
        """Load the exact original-source research packet for deterministic tests."""
        cls.packet = read_json(ROOT)

    def copy(self):
        """Copy unapproved research evidence for isolated negative mutation."""
        return deepcopy(self.packet)

    def audit(self, packet=None, *, markdown=False):
        """Validate a supplied research packet without touching any GPU or provider."""
        return verify_packet(self.packet if packet is None else packet, ROOT,
                             verify_markdown=markdown)

    def test_01_original_sources_and_human_packet_pass(self):
        """Check original sources and human packet pass. """
        self.assertEqual(verify_all(ROOT)["originalSourcePinsVerified"], 15)

    def test_02_fifteen_exact_original_source_sha_and_anchors(self):
        """Check fifteen exact original source sha and anchors. """
        self.assertEqual(self.audit()["originalSourcePinsVerified"], 15)

    def test_03_eight_facets_are_not_hardware_adoption(self):
        """Check eight facets are not hardware adoption. """
        self.assertEqual(self.audit()["nonadoptedFacets"], 8)

    def test_04_five_future_states_have_no_real_compatibility(self):
        """Check five future states have no real compatibility. """
        self.assertEqual(self.audit()["futureEvidenceLabelsOnly"], 5)

    def test_05_four_alternatives_all_unselected(self):
        """Check four alternatives all unselected. """
        self.assertEqual(self.audit()["unselectedAlternatives"], 4)

    def test_06_twenty_two_original_owner_questions_open(self):
        """Check twenty two original owner questions open. """
        self.assertEqual(self.audit()["newOpenOwnerQuestions"], 22)
        self.assertTrue(all(x["risk"] == "UNRATED" and x["ownerAnswer"] is None
                            for x in self.packet["questions"]))

    def test_07_eighteen_future_hostile_designs_not_executed(self):
        """Check eighteen future hostile designs not executed. """
        self.assertEqual(self.audit()["futureNegativesNotExecuted"], 18)
        self.assertTrue(all(x["status"] == "SPECIFIED_NOT_EXECUTED"
                            for x in self.packet["negativeScenarios"]))

    def test_08_prior_owner_question_and_case_counts_unchanged(self):
        """Check prior owner question and case counts unchanged. """
        p = self.packet
        self.assertEqual((p["priorS01QuestionsOpen"],p["priorS01FutureCases"],
                          p["priorS02QuestionsOpen"],p["priorS02FutureCases"],
                          p["priorS03QuestionsOpen"],p["priorS03FutureCases"],
                          p["priorM13QuestionsOpen"],p["priorM13FutureCases"]),
                         (16,12,18,14,20,16,96,74))

    def test_09_actual_benchmark_and_runtime_counts_zero(self):
        """Check actual benchmark and runtime counts zero. """
        self.assertEqual(self.audit()["realHardwareBenchmarks"], 0)
        self.assertEqual(self.packet["nativeRuntime"], "NOT_ADMITTED")

    def test_10_corrupt_original_git_sha_rejected(self):
        """Check corrupt original git sha rejected. """
        p = self.copy()
        p["sourceDocs"][0]["gitBlobSha1"] = "0" * 40
        with self.assertRaises(M14S04IntegrityError):
            self.audit(p)

    def test_11_original_source_text_anchor_forgery_rejected(self):
        """Check original source text anchor forgery rejected. """
        p = self.copy()
        p["sourceDocs"][1]["exactNeedle"] = "fabricated M14 owner approval"
        with self.assertRaises(M14S04IntegrityError):
            self.audit(p)

    def test_12_missing_original_source_typed_failure_and_cause(self):
        """Check missing original source typed failure and cause. """
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(M14S04IntegrityError,
                                        "original source unreadable: INDEX") as x:
                verify_packet(self.copy(), Path(d), verify_markdown=False)
            self.assertIsInstance(x.exception.__cause__, FileNotFoundError)

    def test_13_invalid_utf8_original_source_typed_failure_and_cause(self):
        """Check invalid utf8 original source typed failure and cause. """
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "planning/MASTER-MODULE-INDEX-CURRENT.md"
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(b"\xff invalid source encoding")
            with self.assertRaisesRegex(M14S04IntegrityError,
                                        "original source unreadable: INDEX") as x:
                verify_packet(self.copy(),Path(d),verify_markdown=False)
            self.assertIsInstance(x.exception.__cause__,UnicodeDecodeError)

    def test_14_truncated_compatibility_caveat_rejected(self):
        """Check truncated compatibility caveat rejected. """
        p = self.copy()
        p["facets"][0]["caveat"] = "Supported."
        with self.assertRaises(M14S04IntegrityError):
            self.audit(p)

    def test_15_future_qualifier_state_cannot_be_claimed_real(self):
        """Check future qualifier state cannot be claimed real. """
        p = self.copy()
        p["states"][4]["status"] = "REAL_OWNER_APPROVED_GPU"
        with self.assertRaises(M14S04IntegrityError):
            self.audit(p)

    def test_16_selected_or_missing_alternative_caveat_rejected(self):
        """Check selected or missing alternative caveat rejected. """
        for mode in ("selected","missing","truncated"):
            with self.subTest(mode=mode):
                p = self.copy()
                if mode=="selected":
                    p["alternatives"][0]["selected"]=True
                elif mode=="missing":
                    del p["alternatives"][0]["tradeoffs"]
                else:
                    p["alternatives"][0]["tradeoffs"]="Too brief."
                with self.assertRaises(M14S04IntegrityError):
                    self.audit(p)

    def test_17_missing_original_s04_owner_question_rejected(self):
        """Check missing original s04 owner question rejected. """
        p = self.copy()
        p["questions"].pop()
        with self.assertRaises(M14S04IntegrityError):
            self.audit(p)

    def test_18_forged_hardware_owner_answer_rejected(self):
        """Check forged hardware owner answer rejected. """
        p = self.copy()
        p["questions"][0]["ownerAnswer"]="signed"
        with self.assertRaises(M14S04IntegrityError):
            self.audit(p)

    def test_19_fabricated_question_risk_score_rejected(self):
        """Check fabricated question risk score rejected. """
        p = self.copy()
        p["questions"][0]["risk"]="LOW"
        with self.assertRaises(M14S04IntegrityError):
            self.audit(p)

    def test_20_unqualified_gpu_execution_authority_rejected(self):
        """Check unqualified gpu execution authority rejected. """
        p = self.copy()
        p["questions"][0]["executionAuthority"]="GPU_RUN_ALLOWED"
        with self.assertRaises(M14S04IntegrityError):
            self.audit(p)

    def test_21_future_hostile_design_false_execution_rejected(self):
        """Check future hostile design false execution rejected. """
        p = self.copy()
        p["negativeScenarios"][0]["status"]="REAL_GPU_PASS"
        with self.assertRaises(M14S04IntegrityError):
            self.audit(p)

    def test_22_foreign_owner_question_reference_rejected(self):
        """Check foreign owner question reference rejected. """
        p = self.copy()
        p["negativeScenarios"][0]["questionIds"]=["M14-S03-U01"]
        with self.assertRaises(M14S04IntegrityError):
            self.audit(p)

    def test_23_fake_hardware_benchmarks_rights_and_runtime_rejected(self):
        """Check fake hardware benchmarks rights and runtime rejected. """
        for field,value in (("realGpuBenchmarks",1),
                            ("realHardwareCompatibilityReceipts",1),
                            ("realProviderTests",1),
                            ("realM09Leases",1),
                            ("ownerApproval","APPROVED"),
                            ("hardwareContractAdopted",True)):
            with self.subTest(field=field):
                p=self.copy()
                p[field]=value
                with self.assertRaises(M14S04IntegrityError):
                    self.audit(p)

    def test_24_exact_human_projection_and_duplicate_keys(self):
        """Check exact human projection and duplicate keys. """
        self.assertEqual((ROOT / REPORT).read_text(encoding="utf-8"),
                         render_report(self.packet))
        p=self.copy()
        p["questions"][0]["question"]+=" Unmirrored source report."
        with self.assertRaisesRegex(M14S04IntegrityError,"human S04 source report"):
            self.audit(p,markdown=True)
        with self.assertRaisesRegex(M14S04IntegrityError,"duplicate JSON key"):
            unique_json_keys([("ownerApproval","NONE"),("ownerApproval","APPROVED")])
        for field in ("facets", "states", "alternatives", "questions", "negativeScenarios"):
            for malformed in (["not a dictionary"], {"id": "not a list"}):
                with self.subTest(field=field, malformed=type(malformed).__name__):
                    p = self.copy()
                    p[field] = malformed
                    with self.assertRaises(M14S04IntegrityError):
                        self.audit(p)
        nested_cases = (
            ("facets", "title", None),
            ("facets", "caveat", None),
            ("alternatives", "title", None),
            ("alternatives", "tradeoffs", None),
            ("questions", "question", None),
            ("questions", "sourceRoles", [{}, "INDEX"]),
            ("negativeScenarios", "trigger", None),
            ("negativeScenarios", "questionIds", [{}]),
        )
        for field, subfield, malformed in nested_cases:
            with self.subTest(field=field, subfield=subfield):
                p = self.copy()
                p[field][0][subfield] = malformed
                with self.assertRaises(M14S04IntegrityError):
                    self.audit(p)


if __name__ == "__main__":
    unittest.main()
