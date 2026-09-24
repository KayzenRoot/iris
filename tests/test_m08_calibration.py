from __future__ import annotations

import unittest

from iris_microbenchmark import (
    CalibrationArtifact, CalibrationKind, ExternalContextReference,
    FreshnessPolicy, FreshnessState, InvalidationDependency, InvalidationEvent,
    InvalidationGraph, InvalidationReason, MicrobenchmarkAdmissionError,
    MicrobenchmarkAuthorityError, MicrobenchmarkIntegrityError, NormalizationPolicy,
    TimingCalibrationDescriptor, TimingSource, append_invalidation, apply_calibration,
    content_digest, evaluate_freshness, normalize_metric, propagate_invalidation,
)
from m08_support import measurement_result


class TestCalibrationAndInvalidation(unittest.TestCase):
    def calibration(self, result, *, calibration_id: str = "calibration-v1", version: str = "1.0.0", scale: float = 2.0, offset: float = 1.0):
        return CalibrationArtifact(
            calibration_id, version, result.protocol_id, result.protocol_version,
            result.metric.metric_id, result.metric.version, "calibration-reference-01",
            content_digest(result.binding), CalibrationKind.CORRECTION, "affine-correction-v1",
            scale, offset, 0.05, 0, 10_000, 10, "calibration-review-01",
        )

    def test_raw_samples_are_immutable_and_calibration_is_derived(self):
        result = measurement_result()
        raw_digest = result.raw_digest
        calibration = self.calibration(result)
        derived = apply_calibration(result, calibration, derived_id="derived-result-v1", at_ms=40)
        self.assertEqual(derived.source_result_id, result.result_id)
        self.assertEqual(derived.source_raw_digest, raw_digest)
        self.assertEqual(derived.raw_value, result.aggregate_value)
        self.assertEqual(derived.derived_value, result.aggregate_value * 2.0 + 1.0)
        self.assertEqual(result.raw_digest, raw_digest)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            apply_calibration(result, self.calibration(result, calibration_id="expired", version="1.0.1"), derived_id="late-calibration", at_ms=10_000)

    def test_freshness_aging_supersession_and_scoped_invalidation(self):
        policy = FreshnessPolicy("freshness-policy", "1.0.0", 10, 20, ("driver", "runtime"))
        self.assertEqual(evaluate_freshness("evidence-01", created_at_ms=100, evaluated_at_ms=109, policy=policy).state, FreshnessState.CURRENT)
        self.assertEqual(evaluate_freshness("evidence-01", created_at_ms=100, evaluated_at_ms=110, policy=policy).state, FreshnessState.AGING)
        stale = evaluate_freshness("evidence-01", created_at_ms=100, evaluated_at_ms=120, policy=policy)
        self.assertEqual(stale.state, FreshnessState.STALE)
        self.assertFalse(stale.required_current_satisfied)
        invalidated = evaluate_freshness("evidence-01", created_at_ms=100, evaluated_at_ms=105, policy=policy, invalidation_refs=("invalidation-01",))
        self.assertEqual(invalidated.state, FreshnessState.INVALIDATED)
        superseded = evaluate_freshness("evidence-01", created_at_ms=100, evaluated_at_ms=105, policy=policy, superseding_ref="result-newer")
        self.assertEqual(superseded.state, FreshnessState.SUPERSEDED)

        graph = InvalidationGraph(
            "invalidation-graph", "1.0.0", ("result-old", "envelope-old", "fingerprint-old"),
            (InvalidationDependency("result-old", "envelope-old", "1.0.0", ("driver",)), InvalidationDependency("envelope-old", "fingerprint-old", "1.0.0", ("driver",))), (),
        )
        event = InvalidationEvent("driver-change-01", "result-old", InvalidationReason.MATERIAL_CONTEXT_CHANGE, ("driver",), 120, "system-observer", ExternalContextReference("driver", "driver-42", "1.0.0", "a" * 64, "material"), None)
        appended = append_invalidation(graph, event)
        propagated = propagate_invalidation(appended, event)
        self.assertEqual(tuple(item[0] for item in propagated.invalidated_refs), ("envelope-old", "fingerprint-old", "result-old"))
        self.assertEqual(propagated.graph_version, graph.version)
        self.assertEqual(propagated.propagation_digest, content_digest({"event_id": event.event_id, "affected": propagated.invalidated_refs, "graph_version": graph.version}))
        with self.assertRaises(MicrobenchmarkIntegrityError):
            propagate_invalidation(appended, InvalidationEvent("driver-change-01", "envelope-old", InvalidationReason.LATE_CONTAMINATION, ("runtime",), 120, "system-observer", None, None))

    def test_fixture_and_oracle_defects_propagate_and_recalibration_retains_lineage(self):
        result = measurement_result(result_id="fixture-result-01")
        old_calibration = self.calibration(result, calibration_id="calibration-old")
        first = apply_calibration(result, old_calibration, derived_id="derived-old", at_ms=40)
        new_calibration = self.calibration(result, calibration_id="calibration-rechecked", version="1.0.1", scale=1.5, offset=0.5)
        second = apply_calibration(result, new_calibration, derived_id="derived-rechecked", at_ms=41)
        self.assertEqual(first.source_result_id, second.source_result_id)
        self.assertEqual(first.source_raw_digest, second.source_raw_digest)
        self.assertNotEqual(first.lineage_digest, second.lineage_digest)

        graph = InvalidationGraph("defect-graph", "1.0.0", (result.result_id, "derived-old"), (InvalidationDependency(result.result_id, "derived-old", "1.0.0", ("fixture", "oracle")),), ())
        event = InvalidationEvent("fixture-defect-01", result.result_id, InvalidationReason.FIXTURE_DEFECT, ("fixture", "oracle"), 50, "fixture-reviewer", None, None)
        result_graph = append_invalidation(graph, event)
        affected = propagate_invalidation(result_graph, event)
        self.assertIn(("derived-old", ("fixture", "oracle")), affected.invalidated_refs)
        self.assertEqual(result.raw_digest, content_digest(result.samples))

    def test_clock_and_normalization_preserve_context(self):
        clock = TimingCalibrationDescriptor("clock-monotonic", "1.0.0", TimingSource.MONOTONIC_HOST, 10, True, "paired-clock-samples", "host-only", 20)
        self.assertEqual(clock.resolution_ns, 10)
        result = measurement_result()
        policy = NormalizationPolicy("normalization-policy", "1.0.0", result.protocol_id, result.protocol_version, result.metric.metric_id, result.metric.version, "named-stable-reference-v1", 100.0, 50.0, 0.01)
        normalized = normalize_metric(result, policy, normalized_id="normalized-result-v1")
        self.assertEqual(normalized.policy, policy)
        self.assertEqual(normalized.machine_binding_digest, content_digest(result.binding))
        self.assertEqual(normalized.normalized_value, result.aggregate_value * 2.0)
        self.assertFalse(normalized.universal_hardware_score)
        with self.assertRaises(MicrobenchmarkAuthorityError):
            type(normalized)(
                normalized.normalized_id, normalized.source_result_id, normalized.source_raw_digest,
                normalized.policy_id, normalized.policy, normalized.metric_id, normalized.machine_binding_digest,
                normalized.raw_value, normalized.raw_uncertainty, normalized.normalized_value,
                normalized.uncertainty, True,
            )

    def test_freshness_and_invalidation_never_schedule_or_delete(self):
        with self.assertRaises(MicrobenchmarkAdmissionError):
            InvalidationEvent("global-without-proof", "result-01", InvalidationReason.LATE_CONTAMINATION, (), 50, "observer", None, None)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            InvalidationEvent("admin-without-grant", "result-01", InvalidationReason.GOVERNED_ADMINISTRATIVE, ("driver",), 50, "administrator", None, None)
        graph = InvalidationGraph("append-only-graph", "1.0.0", ("result-01",), (), ())
        event = InvalidationEvent("global-defect", "result-01", InvalidationReason.FIXTURE_DEFECT, (), 50, "reviewer", None, None, True, "global-scope-proof-01")
        appended = append_invalidation(graph, event)
        self.assertEqual(appended.nodes, graph.nodes)
        self.assertEqual(len(graph.events), 0)
        self.assertEqual(len(appended.events), 1)
        self.assertFalse(hasattr(appended, "schedule_rebenchmark"))
        with self.assertRaises(MicrobenchmarkIntegrityError):
            append_invalidation(appended, event)
        result = measurement_result()
        self.assertFalse(hasattr(result, "delete"))
        self.assertFalse(hasattr(result, "schedule"))


if __name__ == "__main__":
    unittest.main()
