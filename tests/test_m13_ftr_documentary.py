"""WO0050: documentary FTR source and future-readiness gate regression tests."""
from __future__ import annotations

from copy import deepcopy
import unittest

from scripts.verify_m13_ftr import (
    ROOT, REPORT, FTRIntegrityError, GATES, load, mock_ftr_claims,
    verify, verify_all,
)


class M13FTRSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = load()

    def audit(self, value=None, *, human=False, md=None):
        return verify(self.p if value is None else value, ROOT,
                      check_human=human, human_text=md)

    def test_01_full_machine_human_ftr_and_five_sources(self):
        self.assertEqual(verify_all()["originalFiveSessions"], 5)

    def test_02_all_96_original_m13_questions_open(self):
        self.assertEqual(self.audit()["originalQuestionsOpen"], 96)

    def test_03_all_74_original_future_cases_unexecuted(self):
        self.assertEqual(self.audit()["futureNegativeCasesNotExecuted"], 74)

    def test_04_five_distinct_deferred_research_families(self):
        self.assertEqual(self.audit()["unselectedFamilies"], 5)

    def test_05_six_cross_session_hazards_unresolved(self):
        self.assertEqual(self.audit()["crossSessionUnresolvedSeams"], 6)

    def test_06_ten_actual_future_owner_and_measurement_gates(self):
        self.assertEqual(self.audit()["futureOwnerEvidenceGates"], 10)

    def test_07_m14_to_m60_fortyseven_original_index_titles(self):
        self.assertEqual(self.audit()["indexOnlyFutureModuleTitles"], 47)

    def test_08_zero_final_approval_contract_freeze_and_runtime(self):
        a = self.audit()
        self.assertFalse(a["independentActualFinalApproval"])
        self.assertFalse(a["m13Frozen"])
        self.assertEqual(a["runtime"], "NOT_ADMITTED")

    def test_09_mutated_original_source_git_blob_rejected(self):
        q = deepcopy(self.p); q["sessions"][0]["gitBlobSha1"] = "0" * 40
        with self.assertRaises(FTRIntegrityError): self.audit(q)

    def test_10_mutated_original_open_question_id_rejected(self):
        q = deepcopy(self.p); q["sessions"][1]["questions"][0] = "FAKE_OWNER_APPROVAL"
        with self.assertRaises(FTRIntegrityError): self.audit(q)

    def test_11_missing_original_future_case_rejected(self):
        q = deepcopy(self.p); q["sessions"][4]["futureNegativeIds"].pop()
        with self.assertRaises(FTRIntegrityError): self.audit(q)

    def test_12_forged_original_index_module_title_rejected(self):
        q = deepcopy(self.p)
        q["futureIndexOnlyModules"][0]["canonicalTitle"] = "Live GPU Owner"
        with self.assertRaises(FTRIntegrityError): self.audit(q)

    def test_13_missing_47th_forward_module_rejected(self):
        q = deepcopy(self.p); q["futureIndexOnlyModules"].pop()
        with self.assertRaises(FTRIntegrityError): self.audit(q)

    def test_14_falsely_selected_backend_family_rejected(self):
        q = deepcopy(self.p); q["researchFamilies"][1]["decision"] = "SELECTED"
        with self.assertRaises(FTRIntegrityError): self.audit(q)

    def test_15_missing_cross_session_seam_rejected(self):
        q = deepcopy(self.p); q["seams"].pop()
        with self.assertRaises(FTRIntegrityError): self.audit(q)

    def test_16_h01_h04_gate_falsely_closed_rejected(self):
        q = deepcopy(self.p); q["gates"][0]["status"] = "APPROVED"
        with self.assertRaises(FTRIntegrityError): self.audit(q)

    def test_17_false_independent_ftr_reviewer_and_freeze_rejected(self):
        for key, value in (("qualifiedIndependentFinalReview", "APPROVED"),
                           ("m13ModuleContract", "FROZEN"),
                           ("technologySelection", "PYTORCH"),
                           ("runtime", "ADMITTED")):
            with self.subTest(key=key):
                q = deepcopy(self.p); q[key] = value
                with self.assertRaises(FTRIntegrityError): self.audit(q)

    def test_18_unauthorized_m09_b_c01_high_gate_promotions_rejected(self):
        for key, value in (("b", "RUNTIME_APPROVED"),
                           ("c01", "FROZEN"), ("highs", "CLOSED")):
            with self.subTest(key=key):
                q = deepcopy(self.p); q[key] = value
                with self.assertRaises(FTRIntegrityError): self.audit(q)

    def test_19_machine_human_full_appendix_mismatch_rejected(self):
        md = (ROOT / REPORT).read_text(encoding="utf-8")
        md = md.replace('"technologySelection": "NONE"',
                        '"technologySelection": "SELECTED"', 1)
        with self.assertRaises(FTRIntegrityError):
            self.audit(human=True, md=md)

    def test_20_all_six_favorable_fake_proofs_cannot_admit_runtime(self):
        a = mock_ftr_claims({k: True for k in GATES})
        self.assertEqual(a["missingMock"], [])
        self.assertEqual(a["disposition"],
                         "DOCUMENTARY_RECONCILED_REAL_APPROVAL_REQUIRED")
        self.assertFalse(a["independentQualifiedReview"])
        self.assertFalse(a["m13Frozen"])
        self.assertFalse(a["technologySelected"])
        self.assertFalse(a["runtimeAllowed"])

    def test_21_missing_independent_rights_mock_still_no_runtime(self):
        inputs = {k: True for k in GATES}
        inputs["currentRights"] = False
        a = mock_ftr_claims(inputs)
        self.assertEqual(a["missingMock"], ["currentRights"])
        self.assertFalse(a["runtimeAllowed"])

    def test_22_nonboolean_or_missing_mock_field_rejected(self):
        values = {k: True for k in GATES}; values["resourceLease"] = "true"
        with self.assertRaises(FTRIntegrityError):
            mock_ftr_claims(values)
        values = {k: True for k in GATES}; values.pop("resourceLease")
        with self.assertRaises(FTRIntegrityError):
            mock_ftr_claims(values)


if __name__ == "__main__":
    unittest.main()
