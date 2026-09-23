from __future__ import annotations

import unittest
from dataclasses import replace

from iris_microbenchmark import (
    BaselinePromotionReceipt, DriftAttribution, DriftClass, FingerprintCompatibilityContract,
    FreshnessState, MetricNoiseGuard, MicrobenchmarkAdmissionError,
    MicrobenchmarkAuthorityError, MicrobenchmarkIntegrityError, PrivacyClass, RecheckTriggerDecision,
    ConsumerProjectionDescriptor, content_digest, detect_drift, evaluate_recheck_trigger,
    project_fingerprint, promote_baseline,
)
from m08_support import binding, measurement_result, protocol, purpose


class TestFingerprintDrift(unittest.TestCase):
    def make_projection(self, *, namespace: str = "consumer-test", privacy: PrivacyClass = PrivacyClass.SYNTHETIC, token: str | None = None, purpose_value=None):
        return ConsumerProjectionDescriptor(
            "latency-projection", "1.0.0", namespace, purpose_value or purpose(),
            ("latency",), ("driver",), privacy, token,
        )

    def make_fingerprint(self, name: str, values: tuple[float, float], *, binding_value=None, context: str = "1.0.0", projection=None):
        selected_binding = binding_value or binding()
        selected_protocol = protocol(binding_value=selected_binding)
        results = (
            measurement_result(result_id=f"{name}-result-a", protocol_value=selected_protocol, values=values),
            measurement_result(result_id=f"{name}-result-b", protocol_value=selected_protocol, values=values),
        )
        selected_projection = projection or self.make_projection()
        return project_fingerprint(
            results, selected_binding, selected_projection, fingerprint_id=name,
            created_at_ms=40, context_axes=(("driver", context),),
        )

    def make_compatibility(self, *, cross_subject: bool = False, cross_runtime: bool = False, context_refs=("driver-upgrade-01",)):
        return FingerprintCompatibilityContract(
            "comparability-policy", "1.0.0", (("cpu-latency-v1", "1.0.0"),),
            cross_subject, cross_runtime, context_refs,
        )

    def make_baseline(self, fingerprint, *, baseline_id: str = "baseline-a", previous=None):
        receipt = BaselinePromotionReceipt(
            f"promotion-{baseline_id}", "baseline-policy-v1", fingerprint.fingerprint_id,
            fingerprint.fingerprint_digest, 50, previous.baseline_id if previous is not None else None,
        )
        return promote_baseline(
            fingerprint, receipt, baseline_id=baseline_id, name="cpu-latency-baseline",
            creation_policy_ref="baseline-policy-v1", validity_dependency_refs=("driver",),
            created_at_ms=50, previous_baseline=previous,
        )

    def detect(self, baseline, old, current, compatibility=None):
        return detect_drift(
            baseline, old, current,
            (MetricNoiseGuard("latency", "1.0.0", 2, 0.2, 0.1),),
            compatibility or self.make_compatibility(), drift_id="drift-check", compared_at_ms=100,
        )

    def test_projection_schema_privacy_and_stable_lineage(self):
        old = self.make_fingerprint("fingerprint-stable", (1.0, 2.0))
        self.assertEqual(old.source_results_digest, content_digest(old.source_result_ids))
        self.assertEqual(len(old.source_protocol_refs), 1)
        self.assertEqual(old.included_context_axes, ("driver",))
        self.assertEqual(old.excluded_context_axes, ())
        self.assertEqual(len(old.context_value_digests), 1)
        self.assertIsNone(old.subject_token)
        with self.assertRaises(MicrobenchmarkIntegrityError):
            replace(old, source_results_digest="0" * 64)
        with self.assertRaises(MicrobenchmarkIntegrityError):
            replace(old, fingerprint_digest="0" * 64)

        public = self.make_projection(namespace="public-report", privacy=PrivacyClass.PUBLIC)
        public_fingerprint = self.make_fingerprint("fingerprint-public", (1.0, 2.0), projection=public)
        self.assertIsNone(public_fingerprint.subject_token)
        local = self.make_projection(privacy=PrivacyClass.LOCAL, token="subject-token-opaque")
        local_fingerprint = self.make_fingerprint("fingerprint-local", (1.0, 2.0), projection=local)
        self.assertEqual(local_fingerprint.subject_token, "subject-token-opaque")
        sensitive = self.make_projection(privacy=PrivacyClass.SENSITIVE, token="sensitive-subject")
        with self.assertRaises(MicrobenchmarkAdmissionError):
            self.make_fingerprint("fingerprint-sensitive", (1.0, 2.0), projection=sensitive)

    def test_comparability_noise_and_metric_scope(self):
        old = self.make_fingerprint("fingerprint-old", (1.0, 2.0))
        baseline = self.make_baseline(old)
        tiny_change = self.make_fingerprint("fingerprint-tiny", (1.05, 2.05))
        self.assertTrue(all(item.classification is DriftClass.NO_MATERIAL_DRIFT for item in self.detect(baseline, old, tiny_change)))
        variance_change = self.make_fingerprint("fingerprint-variance", (0.5, 2.5))
        self.assertEqual(self.detect(baseline, old, variance_change)[0].classification, DriftClass.VARIANCE_SHIFT)

        other_subject = self.make_fingerprint("fingerprint-other-subject", (1.0, 2.0), binding_value=binding(subject_id="subject-02"))
        incomparable = self.detect(baseline, old, other_subject)
        self.assertEqual(incomparable[0].classification, DriftClass.INCOMPARABLE)
        partial_contract = self.make_compatibility(cross_subject=True, cross_runtime=False)
        self.assertEqual(self.detect(baseline, old, other_subject, partial_contract)[0].classification, DriftClass.INCOMPARABLE)
        cross_contract = self.make_compatibility(cross_subject=True, cross_runtime=True)
        self.assertEqual(self.detect(baseline, old, other_subject, cross_contract)[0].classification, DriftClass.NO_MATERIAL_DRIFT)

    def test_baseline_promotion_and_supersession_are_explicit(self):
        first = self.make_fingerprint("fingerprint-base-01", (1.0, 2.0))
        baseline = self.make_baseline(first)
        self.assertEqual(baseline.source_fingerprint_digest, first.fingerprint_digest)
        second = self.make_fingerprint("fingerprint-base-02", (1.0, 2.1))
        receipt = BaselinePromotionReceipt("promotion-replacement", "baseline-policy-v1", second.fingerprint_id, second.fingerprint_digest, 60, baseline.baseline_id)
        replacement = promote_baseline(
            second, receipt, baseline_id="baseline-b", name="cpu-latency-baseline-v2",
            creation_policy_ref="baseline-policy-v1", validity_dependency_refs=("driver",),
            created_at_ms=60, previous_baseline=baseline,
        )
        self.assertEqual(replacement.supersedes_baseline_id, baseline.baseline_id)
        invalid_receipt = replace(receipt, supersedes_baseline_id=None)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            promote_baseline(
                second, invalid_receipt, baseline_id="baseline-c", name="cpu-latency-baseline-v3",
                creation_policy_ref="baseline-policy-v1", validity_dependency_refs=(),
                created_at_ms=70, previous_baseline=baseline,
            )

    def test_context_changes_correlate_without_causal_or_control_authority(self):
        old = self.make_fingerprint("fingerprint-context-old", (1.0, 2.0))
        baseline = self.make_baseline(old)
        changed = self.make_fingerprint("fingerprint-context-new", (1.0, 2.0), context="2.0.0")
        self.assertEqual(self.detect(baseline, old, changed)[0].classification, DriftClass.INCOMPARABLE)
        compatible = detect_drift(
            baseline, old, changed, (MetricNoiseGuard("latency", "1.0.0", 2, 0.2, 0.1),),
            self.make_compatibility(), drift_id="drift-context", compared_at_ms=100,
            context_delta_refs=("driver-upgrade-01",),
        )
        self.assertEqual(compatible[0].classification, DriftClass.NO_MATERIAL_DRIFT)
        attribution = DriftAttribution("drift-context", ("driver-upgrade-01",), False)
        self.assertEqual(attribution.correlated_context_refs, ("driver-upgrade-01",))
        with self.assertRaises(MicrobenchmarkAuthorityError):
            DriftAttribution("drift-context", ("driver-upgrade-01",), True)

    def test_drift_states_and_rechecks_do_not_schedule_work(self):
        old = self.make_fingerprint("fingerprint-stale-old", (1.0, 2.0))
        stale_baseline = replace(self.make_baseline(old), freshness=FreshnessState.STALE)
        current = self.make_fingerprint("fingerprint-stale-current", (5.0, 6.0))
        self.assertEqual(self.detect(stale_baseline, old, current)[0].classification, DriftClass.STALE_BASELINE)
        decision = evaluate_recheck_trigger(
            decision_id="recheck-required", stale=True, material_change_refs=("driver-change",),
            explicit_request_ref=None, safely_eligible=False,
        )
        self.assertTrue(decision.required)
        self.assertFalse(decision.eligible)
        self.assertTrue(decision.benchmark_authorization_required)
        self.assertIsNone(decision.scheduling_ref)
        with self.assertRaises(MicrobenchmarkAuthorityError):
            RecheckTriggerDecision("invalid-recheck", True, True, (), True, "scheduler-job-01")

    def test_consumer_and_m06_m51_m56_firewalls(self):
        old = self.make_fingerprint("fingerprint-public-consumer", (1.0, 2.0))
        self.assertEqual(old.privacy_class, PrivacyClass.SYNTHETIC)
        forbidden_consumer = self.make_projection(namespace="m51-quality")
        with self.assertRaises(MicrobenchmarkAdmissionError):
            self.make_fingerprint("fingerprint-m51", (1.0, 2.0), projection=forbidden_consumer)
        decision = evaluate_recheck_trigger(
            decision_id="no-schedule", stale=False, material_change_refs=(),
            explicit_request_ref="external-request", safely_eligible=True,
        )
        self.assertFalse(hasattr(decision, "execution_plan"))
        self.assertFalse(hasattr(decision, "release_decision"))
        self.assertFalse(hasattr(old, "quality_score"))
        with self.assertRaises(MicrobenchmarkAuthorityError):
            replace(decision, scheduling_ref="m56-dashboard-action")


if __name__ == "__main__":
    unittest.main()
