"""WO0047: synthetic S03 source tests, NEVER original future integration execution."""
from __future__ import annotations

from copy import deepcopy
import unittest

from scripts.verify_m13_s03_research import (
    ROOT, REPORT, S03IntegrityError, check_packet, read_packet, verify_all,
    illustrate_synthetic_blockers, ILLUSTRATIVE_GATES,
)


class M13S03SourceOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = read_packet(ROOT)

    def audit(self, value=None, *, human=False, text=None):
        return check_packet(self.p if value is None else value, ROOT,
                            verify_human=human, human_text=text)

    def test_01_exact_source_and_full_human_appendix(self):
        self.assertEqual(verify_all(ROOT)["exactOriginalSourceBlobs"], 11)

    def test_02_seven_concepts_never_adopted(self):
        self.assertEqual(self.audit()["conceptsUnadopted"], 7)

    def test_03_five_strategies_unselected(self):
        self.assertEqual(self.audit()["strategiesUnselected"], 5)

    def test_04_twelve_future_owner_dimensions_open(self):
        self.assertEqual(self.audit()["futureOwnerDimensions"], 12)

    def test_05_twenty_new_s03_questions_unanswered(self):
        self.assertEqual(self.audit()["newOpenS03Questions"], 20)

    def test_06_sixteen_future_real_cases_not_executed(self):
        self.assertEqual(self.audit()["futureNewNegativeDesignsNotExecuted"], 16)

    def test_07_zero_owner_approvals_or_runtime(self):
        result = self.audit()
        self.assertEqual(result["actualOwnerApprovals"], 0)
        self.assertEqual(result["runtime"], "NOT_ADMITTED")

    def test_08_source_git_blob_fingerprint_tamper(self):
        q = deepcopy(self.p)
        q["sources"][0]["sha"] = "0" * 40
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_09_original_source_anchor_tamper(self):
        q = deepcopy(self.p)
        q["sources"][1]["anchor"] = "new fabricated authorization"
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_10_missing_reuse_concept(self):
        q = deepcopy(self.p)
        q["reuseConcepts"].pop()
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_11_concept_false_approval(self):
        q = deepcopy(self.p)
        q["reuseConcepts"][0]["status"] = "ADOPTED"
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_12_selected_unapproved_strategy(self):
        q = deepcopy(self.p)
        q["strategies"][0]["selected"] = True
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_13_executed_strategy_without_permission(self):
        q = deepcopy(self.p)
        q["strategies"][0]["executed"] = True
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_14_independent_future_owner_axis_fake_qualification(self):
        q = deepcopy(self.p)
        q["qualificationAxes"][0]["status"] = "QUALIFIED"
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_15_new_question_missing(self):
        q = deepcopy(self.p)
        q["questions"].pop()
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_16_new_question_original_route_forged(self):
        q = deepcopy(self.p)
        q["questions"][0]["ownerRoute"] = "M13"
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_17_new_question_real_owner_answer_forged(self):
        q = deepcopy(self.p)
        q["questions"][0]["ownerAnswer"] = "Approved"
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_18_new_question_source_role_changed(self):
        q = deepcopy(self.p)
        q["questions"][0]["primarySourceRole"] = "INDEX"
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_19_original_future_case_fake_execution(self):
        q = deepcopy(self.p)
        q["futureNegativeCases"][0]["status"] = "EXECUTED_PASS"
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_20_original_case_unknown_concept(self):
        q = deepcopy(self.p)
        q["futureNegativeCases"][0]["conceptIds"] = ["UNAPPROVED"]
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_21_original_future_oracle_swap(self):
        q = deepcopy(self.p)
        q["futureNegativeCases"][0]["futureNonAuthorizingOracle"] = "PASS"
        with self.assertRaises(S03IntegrityError):
            self.audit(q)

    def test_22_h01_h04_b_c01_or_runtime_cannot_advance(self):
        for key, value in (
            ("highs", "CLOSED"), ("c01", "FROZEN"),
            ("bDirection", "RUNTIME_APPROVED"), ("runtime", "ADMITTED"),
            ("actualOwnerApprovals", 1),
        ):
            with self.subTest(key=key):
                q = deepcopy(self.p)
                q[key] = value
                with self.assertRaises(S03IntegrityError):
                    self.audit(q)

    def test_23_forged_human_original_appendix_rejected(self):
        text = (ROOT / REPORT).read_text(encoding="utf-8")
        text = text.replace('"session": "S03"', '"session": "ADMITTED"', 1)
        with self.assertRaises(S03IntegrityError):
            self.audit(human=True, text=text)

    def test_24_original_s01_s02_and_m12_futures_never_upgraded(self):
        for key in ("s01FutureCases", "s02FutureCases", "m12FutureCases"):
            with self.subTest(key=key):
                q = deepcopy(self.p)
                q[key] = "EXECUTED"
                with self.assertRaises(S03IntegrityError):
                    self.audit(q)

    def test_25_mock_missing_untrusted_owner_proof_requires_review(self):
        fake = {k: True for k in ILLUSTRATIVE_GATES}
        fake["m53m54CurrentRights"] = False
        result = illustrate_synthetic_blockers(fake)
        self.assertEqual(result["blockers"], ["m53m54CurrentRights"])
        self.assertEqual(result["disposition"], "REVIEW_REQUIRED_NO_REUSE_ADMISSION")

    def test_26_even_every_mock_positive_never_grants_reuse(self):
        fake = {k: True for k in ILLUSTRATIVE_GATES}
        result = illustrate_synthetic_blockers(fake)
        self.assertEqual(result["blockers"], [])
        self.assertFalse(result["authenticatedOwnerProof"])
        self.assertEqual(result["disposition"], "REVIEW_REQUIRED_NO_REUSE_ADMISSION")
        self.assertEqual(result["runtimeAuthority"], "NONE")

    def test_27_missing_mock_field_fails_closed(self):
        fake = {k: True for k in ILLUSTRATIVE_GATES}
        fake.pop("m02OwnerReuseClass")
        with self.assertRaises(S03IntegrityError):
            illustrate_synthetic_blockers(fake)

    def test_28_invalid_mock_field_type_fails_closed(self):
        fake = {k: True for k in ILLUSTRATIVE_GATES}
        fake["sourceExactVersion"] = "true"
        with self.assertRaises(S03IntegrityError):
            illustrate_synthetic_blockers(fake)


if __name__ == "__main__":
    unittest.main()
