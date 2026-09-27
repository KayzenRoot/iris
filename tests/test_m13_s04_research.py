"""WO0048 S04 read-only original source & synthetic safety tests, no actual CUDA or I/O."""
from __future__ import annotations

from copy import deepcopy
import unittest

from scripts.verify_m13_s04_research import (
    ROOT, REPORT, S04IntegrityError, load, validate, verify_all,
    synthetic_schedule_guard,
)


class M13S04OfflineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = load(ROOT)

    def check(self, p=None, *, human=False, human_text=None):
        return validate(self.original if p is None else p, ROOT,
                        compare_human=human, human_text=human_text)

    def test_01_exact_sources_and_full_human_packet(self):
        self.assertEqual(verify_all(ROOT)["exactOriginalGitBlobs"], 14)

    def test_02_one_mutable_not_installed_official_source(self):
        self.assertEqual(self.check()["mutablePublicOfficialReferences"], 1)

    def test_03_all_seven_concepts_nonadopted(self):
        self.assertEqual(self.check()["unadoptedConcepts"], 7)

    def test_04_four_unselected_alternatives(self):
        self.assertEqual(self.check()["unselectedAlternatives"], 4)

    def test_05_twelve_metrics_not_measured(self):
        self.assertEqual(self.check()["proposedNotMeasuredMetricProtocols"], 12)

    def test_06_twenty_new_open_owner_questions(self):
        self.assertEqual(self.check()["newOpenS04OwnerQuestions"], 20)

    def test_07_sixteen_future_not_executed_cases(self):
        self.assertEqual(self.check()["futureS04NegativesNotExecuted"], 16)

    def test_08_no_gpu_io_or_signed_owner_conclusions(self):
        v = self.check()
        self.assertEqual(v["gpuRuns"], 0)
        self.assertEqual(v["hardwareMeasurements"], 0)
        self.assertEqual(v["qualifiedOwners"], 0)

    def test_09_fabricated_immutable_original_blob_fails(self):
        q = deepcopy(self.original)
        q["sourceDocs"][0]["sha"] = "0" * 40
        with self.assertRaises(S04IntegrityError):
            self.check(q)

    def test_10_fabricated_original_anchor_fails(self):
        q = deepcopy(self.original)
        q["sourceDocs"][1]["anchor"] = "unapproved CUDA launch"
        with self.assertRaises(S04IntegrityError):
            self.check(q)

    def test_11_original_mutable_official_url_swap_fails(self):
        q = deepcopy(self.original)
        q["externalReferences"][0]["url"] = "https://example.com/fake"
        with self.assertRaises(S04IntegrityError):
            self.check(q)

    def test_12_fake_hardware_attestation_fails(self):
        q = deepcopy(self.original)
        q["externalReferences"][0]["status"] = "DEVICE_VERIFIED"
        with self.assertRaises(S04IntegrityError):
            self.check(q)

    def test_13_missing_original_concept_fails(self):
        q = deepcopy(self.original)
        q["concepts"].pop()
        with self.assertRaises(S04IntegrityError):
            self.check(q)

    def test_14_falsely_adopted_pinned_memory_fails(self):
        q = deepcopy(self.original)
        q["concepts"][1]["status"] = "ADOPTED"
        with self.assertRaises(S04IntegrityError):
            self.check(q)

    def test_15_falsely_selected_async_gpu_strategy_fails(self):
        q = deepcopy(self.original)
        q["alternatives"][2]["selected"] = True
        with self.assertRaises(S04IntegrityError):
            self.check(q)

    def test_16_falsely_measured_metric_fails(self):
        q = deepcopy(self.original)
        q["metricProtocols"][0]["status"] = "OBSERVED_VALID"
        with self.assertRaises(S04IntegrityError):
            self.check(q)

    def test_17_original_question_removed_fails(self):
        q = deepcopy(self.original)
        q["questions"].pop()
        with self.assertRaises(S04IntegrityError):
            self.check(q)

    def test_18_real_owner_answer_forged_fails(self):
        q = deepcopy(self.original)
        q["questions"][0]["answer"] = "signed by owner"
        with self.assertRaises(S04IntegrityError):
            self.check(q)

    def test_19_source_routing_changed_fails(self):
        q = deepcopy(self.original)
        q["questions"][0]["sourceRole"] = "M10"
        with self.assertRaises(S04IntegrityError):
            self.check(q)

    def test_20_unexecuted_case_falsely_passed_fails(self):
        q = deepcopy(self.original)
        q["negativeCases"][0]["status"] = "EXECUTED"
        with self.assertRaises(S04IntegrityError):
            self.check(q)

    def test_21_future_case_oracle_changed_fails(self):
        q = deepcopy(self.original)
        q["negativeCases"][0]["futureNonAuthorizingOracle"] = "ALLOW"
        with self.assertRaises(S04IntegrityError):
            self.check(q)

    def test_22_historical_owner_b_c01_h01_h04_and_runtime_stay_blocked(self):
        for key, value in (
            ("b", "ADOPTED"), ("c01", "FROZEN"), ("highs", "CLOSED"),
            ("runtime", "ADMITTED"), ("selectedPipeline", "CUDA_STREAMS"),
            ("qualifiedOwnerApprovals", 1), ("realGpuRuns", 1),
            ("ioExecuted", True),
        ):
            with self.subTest(field=key):
                q = deepcopy(self.original)
                q[key] = value
                with self.assertRaises(S04IntegrityError):
                    self.check(q)

    def test_23_human_appendix_tamper_rejected(self):
        md = (ROOT / REPORT).read_text(encoding="utf-8")
        md = md.replace('"session": "S04"', '"session": "EXECUTED"', 1)
        with self.assertRaises(S04IntegrityError):
            self.check(human=True, human_text=md)

    def test_24_untrusted_all_positive_checklist_still_no_dispatch(self):
        values = {k: True for k in (
            "observedM07", "validM08", "jointM09Lease", "m11OwnerAck",
            "m12AttemptFence", "currentRightsM54M55", "m60OSCapability",
        )}
        yes = synthetic_schedule_guard(values)
        self.assertEqual(yes["missingMockClaims"], [])
        self.assertEqual(yes["state"], "DOCUMENTARY_ONLY_NO_DISPATCH")
        self.assertFalse(yes["gpuAllowed"])
        self.assertFalse(yes["storageAllowed"])
        self.assertEqual(yes["authenticatedSourceReceipts"], 0)
        values["jointM09Lease"] = False
        no = synthetic_schedule_guard(values)
        self.assertEqual(no["missingMockClaims"], ["jointM09Lease"])


if __name__ == "__main__":
    unittest.main()
