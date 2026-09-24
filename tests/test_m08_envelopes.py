from __future__ import annotations

import unittest
from dataclasses import replace

from iris_microbenchmark import (
    BoundedSearchPlan, CapabilityDimensionEvidence, CapabilityRegion, CapabilityRequirement,
    ConcurrencyEnvelopeEvidence, DerivationMethod, Directionality, FreshnessState,
    MemoryEnvelopeEvidence,
    MicrobenchmarkAdmissionError, MicrobenchmarkAuthorityError, MicrobenchmarkIntegrityError,
    MicrobenchmarkLimitError, QualificationState, RequirementQualificationHandshake,
    SafetyBudget, SearchAttempt, SearchOutcome, SearchStrategy, SustainabilityClass,
    SustainabilityEvidence, content_digest, derive_envelope, evaluate_requirements,
    validate_search_trace,
)
from m08_support import binding, envelope, measurement_result, protocol, purpose


class TestCapabilityEnvelopes(unittest.TestCase):
    def test_conservative_regions_and_bounded_search(self):
        selected_binding = binding()
        first = measurement_result(result_id="boundary-result-01", protocol_value=protocol(binding_value=selected_binding))
        second = measurement_result(result_id="boundary-result-02", protocol_value=protocol(binding_value=selected_binding), values=(1.1, 1.9))
        conservative = CapabilityDimensionEvidence(
            "latency-bound", "ms", CapabilityRegion.CONSERVATIVE_BOUND, DerivationMethod.CONSERVATIVE_MARGIN,
            (first.result_id, second.result_id), 80.0, 100.0, 120.0, 0.2,
            Directionality.LOWER_IS_BETTER, SustainabilityClass.SHORT_STEADY, None,
        )
        result_envelope = derive_envelope(
            (conservative,), (first, second), envelope_id="conservative-envelope", binding=selected_binding,
            derivation_algorithm="conservative-margin-v1", derivation_version="1.0.0",
            evidence_purpose=purpose(), created_at_ms=40, synthetic_fixture_mode=True,
        )
        self.assertEqual(result_envelope.dimensions[0].conservative_limit, 120.0)
        self.assertEqual(len(result_envelope.source_result_ids), 2)
        with self.assertRaises(MicrobenchmarkIntegrityError):
            CapabilityDimensionEvidence(
                "unsafe-bound", "ms", CapabilityRegion.CONSERVATIVE_BOUND, DerivationMethod.INTERPOLATION,
                (first.result_id, second.result_id), 80.0, 100.0, 105.0, 0.2,
                Directionality.LOWER_IS_BETTER, SustainabilityClass.SHORT_STEADY, None,
            )
        with self.assertRaises(MicrobenchmarkAdmissionError):
            CapabilityDimensionEvidence(
                "extrapolation", "ms", CapabilityRegion.CONSERVATIVE_BOUND, DerivationMethod.EXTRAPOLATION,
                (first.result_id, second.result_id), 1.0, 100.0, 70.0, 0.2,
                Directionality.LOWER_IS_BETTER, SustainabilityClass.SHORT_STEADY, None,
            )

        budget = SafetyBudget(5_000, 100, 20, 1_000_000, 1_000_000, 64_000, 2, 0, 1_000, True)
        plan = BoundedSearchPlan("search-01", "1.0.0", "latency-bound", SearchStrategy.BOUNDED_GRID, 3, 2_000, 500_000, 2, False, budget)
        trace = (
            SearchAttempt(1, 10, 500, 1, 100_000, SearchOutcome.SUCCESS, "result-a", None),
            SearchAttempt(2, 510, 500, 2, 200_000, SearchOutcome.FAILURE, "result-b", None),
        )
        self.assertTrue(validate_search_trace(plan, trace))
        aborted = SearchAttempt(3, 1_010, 100, 3, 300_000, SearchOutcome.ABORTED, None, "abort-01")
        self.assertTrue(validate_search_trace(plan, trace + (aborted,)))
        with self.assertRaises(MicrobenchmarkIntegrityError):
            validate_search_trace(plan, (aborted, trace[0]))
        with self.assertRaises(MicrobenchmarkLimitError):
            validate_search_trace(plan, trace + (trace[0], trace[1]))

    def test_memory_boundary_evidence_has_no_resource_control(self):
        capacity = 8 * 1024**3
        memory = MemoryEnvelopeEvidence("vram-observed", capacity, 6 * 1024**3, 5 * 1024**3, 7 * 1024**3, ("result-memory-01",), "a" * 64)
        self.assertEqual(memory.requested_bytes, capacity)
        self.assertEqual(memory.peak_observed_bytes, 5 * 1024**3)
        self.assertFalse(hasattr(memory, "lease_id"))
        self.assertFalse(hasattr(memory, "evict"))
        with self.assertRaises(MicrobenchmarkIntegrityError):
            MemoryEnvelopeEvidence("bad-memory", 1_000, 500, 400, 1_001, ("result-memory-02",), "b" * 64)

    def test_concurrency_and_sustainability_are_observation_scoped(self):
        concurrent = ConcurrencyEnvelopeEvidence(
            "tensor-reduction", 2, ("lane-result-01", "lane-result-02"), "aggregate-result-01",
            "device-event-sync", "equal-work-observed", "c" * 64,
        )
        self.assertEqual(concurrent.concurrency_degree, 2)
        with self.assertRaises(MicrobenchmarkIntegrityError):
            ConcurrencyEnvelopeEvidence("tensor-reduction", 2, ("lane-result-01", "lane-result-02"), "lane-result-01", "sync", "fair", "c" * 64)
        sustained = SustainabilityEvidence(SustainabilityClass.SUSTAINED_OBSERVED, 60_000, ("result-long-01",), "thermal-context-01")
        self.assertEqual(sustained.classification, SustainabilityClass.SUSTAINED_OBSERVED)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            SustainabilityEvidence(SustainabilityClass.SUSTAINED_OBSERVED, 59_999, ("result-short-01",), None)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            SustainabilityEvidence(SustainabilityClass.BURST, 5_001, ("result-burst-01",), None)

    def test_unknown_staleness_lineage_and_authority_boundaries(self):
        result = measurement_result()
        positive = envelope(result)
        requirement = CapabilityRequirement("latency", "ms", None, 10.0, FreshnessState.CURRENT, "consumer-test", False)
        handshake = RequirementQualificationHandshake("consumer-handshake", "1.0.0", "consumer-x", purpose(), (requirement,))
        qualified = evaluate_requirements(positive, handshake)
        self.assertEqual(qualified.state, QualificationState.SATISFIED)
        self.assertIsNone(qualified.policy_decision_ref)

        unknown_dimension = CapabilityDimensionEvidence(
            "latency", "ms", CapabilityRegion.UNKNOWN, DerivationMethod.DIRECT_OBSERVATION,
            (), None, None, None, 0.0, Directionality.NEUTRAL, SustainabilityClass.UNKNOWN_SUSTAINABILITY,
            "telemetry-unknown",
        )
        unknown_envelope = envelope(result, envelope_id="unknown-envelope", dimension=unknown_dimension)
        self.assertEqual(evaluate_requirements(unknown_envelope, handshake).state, QualificationState.UNKNOWN)
        physical_requirement = replace(requirement, require_physical_evidence=True)
        physical_handshake = replace(handshake, requirements=(physical_requirement,))
        self.assertEqual(evaluate_requirements(positive, physical_handshake).state, QualificationState.UNSATISFIED)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            replace(requirement, required_freshness=FreshnessState.UNKNOWN_FRESHNESS)
        with self.assertRaises(MicrobenchmarkAuthorityError):
            replace(qualified, policy_decision_ref="release-acceptance")

        stale_state = FreshnessState.STALE
        semantic = {
            "schema_version": positive.schema_version,
            "binding": positive.binding,
            "dimensions": positive.dimensions,
            "source_result_ids": positive.source_result_ids,
            "derivation_algorithm": positive.derivation_algorithm,
            "derivation_version": positive.derivation_version,
            "invalidation_dependency_ids": positive.invalidation_dependency_ids,
            "evidence_purpose": positive.evidence_purpose,
            "created_at_ms": positive.created_at_ms,
            "validity_state": stale_state,
            "synthetic_only": positive.synthetic_only,
        }
        stale = replace(positive, validity_state=stale_state, envelope_digest=content_digest(semantic))
        self.assertEqual(evaluate_requirements(stale, handshake).state, QualificationState.UNKNOWN)
        with self.assertRaises(MicrobenchmarkIntegrityError):
            replace(positive, validity_state=FreshnessState.STALE)


if __name__ == "__main__":
    unittest.main()
