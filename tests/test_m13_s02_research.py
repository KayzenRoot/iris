"""WO0046: no real GPU, backend, model install, user permission or future test execution."""
from __future__ import annotations

from copy import deepcopy
import unittest

from scripts.verify_m13_s02_research import (
    ROOT, REPORT, S02IntegrityError, check_packet, read_packet, verify_all,
)


class M13S02ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = read_packet(ROOT)

    def audit(self, p=None, *, human=False, text=None):
        return check_packet(self.p if p is None else p, ROOT,
                            verify_markdown=human, human_text=text)

    def test_01_exact_source_and_full_human_report_match(self):
        self.assertEqual(verify_all(ROOT)["originalSourceGitBlobs"], 13)

    def test_02_eight_external_references_are_mutable_not_proof(self):
        self.assertEqual(self.audit()["mutableOfficialReferences"], 8)

    def test_03_seven_candidate_families_are_unselected(self):
        self.assertEqual(self.audit()["unselectedBackendFamilies"], 7)

    def test_04_twelve_unqualified_owner_measurement_axes(self):
        self.assertEqual(self.audit()["unqualifiedOwnerAxes"], 12)

    def test_05_eighteen_new_s02_original_questions_unanswered(self):
        self.assertEqual(self.audit()["newS02OpenQuestions"], 18)

    def test_06_fourteen_future_integration_cases_not_executed(self):
        self.assertEqual(self.audit()["futureS02CasesNotExecuted"], 14)

    def test_07_no_owner_signatures_or_runtime_permission(self):
        r = self.audit()
        self.assertEqual(r["actualOwnerApprovals"], 0)
        self.assertEqual(r["runtime"], "NOT_ADMITTED")

    def test_08_forged_upstream_url_rejected(self):
        p = deepcopy(self.p)
        p["officialReferences"][0]["url"] = "https://example.com/fake"
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_09_upstream_url_cannot_claim_installed_proof(self):
        p = deepcopy(self.p)
        p["officialReferences"][1]["status"] = "TRUSTED_INSTALLED_VERSION"
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_10_original_git_blob_tamper_rejected(self):
        p = deepcopy(self.p)
        p["sourceDocs"][3]["sha"] = "0" * 40
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_11_source_role_and_question_route_tamper_rejected(self):
        p = deepcopy(self.p)
        p["questions"][0]["sourceRole"] = "M60"
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_12_missing_candidate_fails(self):
        p = deepcopy(self.p)
        p["candidates"].pop()
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_13_forged_backend_selection_fails(self):
        p = deepcopy(self.p)
        p["selectedBackend"] = "NVIDIA_ENGINE"
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_14_forged_third_party_code_install_fails(self):
        p = deepcopy(self.p)
        p["candidates"][4]["installed"] = True
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_15_forged_gpu_benchmark_fails(self):
        p = deepcopy(self.p)
        p["candidates"][3]["benchmarked"] = True
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_16_unqualified_owner_axis_cannot_close_itself(self):
        p = deepcopy(self.p)
        p["qualificationDimensions"][0]["status"] = "APPROVED"
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_17_missing_original_question_rejected(self):
        p = deepcopy(self.p)
        p["questions"].pop()
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_18_forged_owner_answer_rejected(self):
        p = deepcopy(self.p)
        p["questions"][0]["ownerAnswer"] = "Approved by external owner"
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_19_duplicate_question_id_rejected(self):
        p = deepcopy(self.p)
        p["questions"][1]["id"] = p["questions"][0]["id"]
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_20_future_case_claim_executed_rejected(self):
        p = deepcopy(self.p)
        p["negativeCases"][0]["status"] = "EXECUTED_PASS"
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_21_future_case_unknown_candidate_rejected(self):
        p = deepcopy(self.p)
        p["negativeCases"][0]["candidateIds"] = ["INVENTED_BACKEND"]
        with self.assertRaises(S02IntegrityError):
            self.audit(p)

    def test_22_forged_human_packet_appendix_rejected(self):
        content = (ROOT / REPORT).read_text(encoding="utf-8")
        content = content.replace('"session": "S02"', '"session": "IMPLEMENTED"', 1)
        with self.assertRaises(S02IntegrityError):
            self.audit(human=True, text=content)

    def test_23_original_h01_h04_b_c01_and_runtime_cannot_advance(self):
        for key, val in (
            ("highs", "CLOSED"),
            ("b", "RUNTIME_APPROVED"),
            ("c01", "FROZEN_APPROVED"),
            ("runtime", "ADMITTED"),
        ):
            with self.subTest(key=key):
                p = deepcopy(self.p)
                p[key] = val
                with self.assertRaises(S02IntegrityError):
                    self.audit(p)


if __name__ == "__main__":
    unittest.main()
