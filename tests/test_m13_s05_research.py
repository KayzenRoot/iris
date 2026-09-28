"""M13 S05 original source and synthetic-only performance gate tests."""
from __future__ import annotations
from copy import deepcopy
import unittest
from scripts.verify_m13_s05_research import (
    ROOT, REPORT, S05IntegrityError, GOOD, read_packet, validate,
    verify_all, synthetic_screen,
)

class S05SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = read_packet()

    def audit(self, value=None, human=False, text=None):
        return validate(self.p if value is None else value, ROOT,
                        human=human, human_text=text)

    def test_01_exact_fifteen_sources_and_human_appendix(self):
        self.assertEqual(verify_all()["immutableOriginalSourceDocs"], 15)

    def test_02_three_mutable_external_profiling_refs(self):
        self.assertEqual(self.audit()["mutableOfficialProfilingRefs"], 3)

    def test_03_six_nonnumeric_performance_budget_families(self):
        self.assertEqual(self.audit()["nonnumericBudgetFamilies"], 6)

    def test_04_five_not_executed_profiling_methods(self):
        self.assertEqual(self.audit()["unexecutedProfilingMethods"], 5)

    def test_05_twelve_unqualified_real_owner_axes(self):
        self.assertEqual(self.audit()["unqualifiedOwnerAxes"], 12)

    def test_06_twenty_new_s05_owner_questions_open(self):
        self.assertEqual(self.audit()["newOpenOwnerQuestions"], 20)

    def test_07_sixteen_new_real_future_cases_not_executed(self):
        self.assertEqual(self.audit()["newUnexecutedNegativeCases"], 16)

    def test_08_runtime_remains_nonadmitted(self):
        self.assertEqual(self.audit()["runtime"], "NOT_ADMITTED")

    def test_09_mutated_original_source_hash_fails(self):
        p = deepcopy(self.p)
        p["sourceDocs"][0]["sha"] = "0" * 40
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_10_mutated_original_source_anchor_fails(self):
        p = deepcopy(self.p)
        p["sourceDocs"][0]["anchor"] = "FAKE_APPROVAL"
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_11_mutated_mutable_external_url_fails(self):
        p = deepcopy(self.p)
        p["externalReferences"][0]["url"] = "https://example.com/not-source"
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_12_external_reference_not_installed_proof(self):
        p = deepcopy(self.p)
        p["externalReferences"][0]["status"] = "GPU_MEASURED"
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_13_missing_original_budget_family_fails(self):
        p = deepcopy(self.p)
        p["budgetClasses"].pop()
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_14_numeric_budget_not_adopted_fails(self):
        p = deepcopy(self.p)
        p["budgetClasses"][0]["threshold"] = "100MS"
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_15_profiler_was_not_run_fails(self):
        p = deepcopy(self.p)
        p["profilingMethods"][0]["status"] = "EXECUTED"
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_16_real_owner_evidence_not_received_fails(self):
        p = deepcopy(self.p)
        p["futureQualificationAxes"][0]["status"] = "QUALIFIED"
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_17_missing_question_fails(self):
        p = deepcopy(self.p)
        p["questions"].pop()
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_18_forged_owner_answer_fails(self):
        p = deepcopy(self.p)
        p["questions"][0]["ownerAnswer"] = "signed"
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_19_question_original_source_route_changed_fails(self):
        p = deepcopy(self.p)
        p["questions"][0]["primarySourceRole"] = "M12"
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_20_original_future_case_false_execution_fails(self):
        p = deepcopy(self.p)
        p["negativeCases"][0]["status"] = "EXECUTED_PASS"
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_21_future_case_nonauthorization_oracle_changed_fails(self):
        p = deepcopy(self.p)
        p["negativeCases"][0]["futureNonAuthorizingOracle"] = "ALLOW"
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_22_all_h01_h04_b_c01_or_runtime_promotions_fail(self):
        for k, v in (
            ("highs", "CLOSED"), ("c01", "FROZEN"),
            ("b", "EXECUTABLE"), ("runtime", "ADMITTED"),
            ("actualOwnerApprovals", 1), ("measurements", "MEASURED"),
            ("numericBudgets", "100MS"), ("selectedPolicy", "QUALITY"),
        ):
            with self.subTest(field=k):
                p = deepcopy(self.p); p[k] = v
                with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_23_human_machine_appendix_mismatch_fails(self):
        md = (ROOT / REPORT).read_text(encoding="utf-8")
        md = md.replace('"session": "S05"', '"session": "FROZEN"', 1)
        with self.assertRaises(S05IntegrityError): self.audit(human=True, text=md)

    def test_24_historical_s01_s04_nonexecution_fails(self):
        p = deepcopy(self.p)
        p["previousSessions"]["s04FutureNegatives"] = "EXECUTED"
        with self.assertRaises(S05IntegrityError): self.audit(p)

    def test_25_all_favorable_mock_values_never_admit_budget(self):
        out = synthetic_screen(dict(GOOD))
        self.assertEqual(out["mockBlockers"], [])
        self.assertEqual(out["disposition"],
                         "TRIAGE_ONLY_NO_REAL_BUDGET_OR_RUNTIME_ADMISSION")
        self.assertEqual(out["actualOwnerReceipts"], 0)
        self.assertFalse(out["numericBudgetAdmitted"])
        self.assertFalse(out["runtimeAllowed"])

    def test_26_unknown_interference_and_failed_quality_remain_blocked(self):
        values = dict(GOOD)
        values["quality"] = "FAIL"; values["interference"] = "UNKNOWN"
        out = synthetic_screen(values)
        self.assertEqual(out["mockBlockers"], ["quality", "interference"])
        self.assertEqual(out["actualMeasurements"], 0)

    def test_27_incomplete_or_invalid_mock_categories_fail(self):
        q = dict(GOOD); q.pop("source")
        with self.assertRaises(S05IntegrityError): synthetic_screen(q)
        q = dict(GOOD); q["source"] = "VERIFIED_BY_TOOL"
        with self.assertRaises(S05IntegrityError): synthetic_screen(q)

    def test_28_session_five_not_a_module_freeze(self):
        p = deepcopy(self.p)
        p["status"] = "FROZEN"
        with self.assertRaises(S05IntegrityError): self.audit(p)

if __name__ == "__main__":
    unittest.main()
