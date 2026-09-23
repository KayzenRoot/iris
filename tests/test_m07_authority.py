from __future__ import annotations

import unittest

from iris_hardware_genome import (
    DiscoveryBatch,
    DiscoverySessionRef,
    HardwareGenomeAdmissionError,
    HardwareGenomeIntegrityError,
    HardwareGenomeValidationError,
    M07_INVARIANTS,
    ObservationState,
    ProjectionContract,
    RedactionPolicy,
    admit_adapter_batch,
    admit_discovery_batch,
    project_genome,
    project_to_m06,
    redact_genome_view,
    require_fresh_current_truth,
    restore_as_historical,
    validate_projection,
)
from m07_support import PROBE, PROBE_REGISTRY, RUNTIME, SUBJECT, capability_assertion, evidence, genome, observation, snapshot
from scripts.validate_m07_boundaries import validate_boundaries


class TestProjectionAndRecovery(unittest.TestCase):
    def test_frozen_invariant_catalog_has_all_235_exact_numbers(self):
        self.assertEqual(len(M07_INVARIANTS), 235)
        self.assertEqual(tuple(item.number for item in M07_INVARIANTS), tuple(range(1, 236)))

    def test_consumer_projection_is_explicit_named_and_fingerprinted(self):
        source = genome((observation("hardware.gpu.vendor", observation_id="project-vendor"),))
        contract = ProjectionContract("m06-material", "1.0", "M06", ("hardware.gpu.vendor", "runtime.os.family"), ("hardware.gpu.vendor",), False)
        with self.assertRaises(HardwareGenomeAdmissionError):
            project_to_m06(source, contract)
        from iris_hardware_genome import FactEnvelope, REGISTRY_VERSION
        obs = observation("hardware.gpu.vendor", observation_id="project-declared")
        source = genome((obs,), facts=(FactEnvelope(obs.fact_key, obs, REGISTRY_VERSION, contract.contract_id),))
        projection = project_to_m06(source, contract)
        validate_projection(projection, source)
        self.assertEqual(projection.source_genome_id, source.genome_id)
        missing = next(item for item in projection.omissions if item.fact_key == "runtime.os.family")
        self.assertFalse(missing.captured_in_source)
        with self.assertRaises(HardwareGenomeAdmissionError):
            project_to_m06(source, ProjectionContract("wrong-consumer", "1.0", "M05", ("hardware.gpu.vendor",), (), False))
        with self.assertRaises(HardwareGenomeAdmissionError):
            project_genome(source, ProjectionContract("missing-required", "1.0", "M06", ("runtime.os.family",), ("runtime.os.family",), False))

    def test_consumer_fingerprint_excludes_dynamic_telemetry_unless_selected(self):
        from iris_hardware_genome import FactEnvelope, MetricSemantics, REGISTRY_VERSION, TelemetrySample
        obs = observation("hardware.gpu.vendor", observation_id="stable-fact")
        fact = FactEnvelope(obs.fact_key, obs, REGISTRY_VERSION, "static-slice")
        static_source = genome((obs,), facts=(fact,))
        dynamic = TelemetrySample(
            "dynamic-power", "telemetry.gpu.power", MetricSemantics.INSTANTANEOUS_GAUGE, 100.0, "watt",
            SUBJECT, RUNTIME, "power-sensor", "1.0", 1, 1_000, 0, 2_000, ObservationState.OBSERVED,
            evidence("dynamic-power-e", observed_at_ms=1_000), visibility_scope="local",
        )
        telemetry_source = genome((obs,), facts=(fact,), telemetry=(dynamic,))
        contract = ProjectionContract("static-slice", "1.0", "M06", (obs.fact_key,), (obs.fact_key,), False)
        left = project_to_m06(static_source, contract)
        right = project_to_m06(telemetry_source, contract)
        self.assertNotEqual(left.source_genome_id, right.source_genome_id)
        self.assertEqual(left.fingerprint, right.fingerprint)
        validate_projection(right, telemetry_source)

    def test_redacted_advertisement_drops_raw_identity_and_preserves_state(self):
        claim = capability_assertion()
        source = genome((claim.observation,), capabilities=(claim,))
        policy = RedactionPolicy("public-ad", "1.0", (claim.capability_key,))
        view = redact_genome_view(source, policy)
        self.assertFalse(view.is_canonical_content_identity)
        self.assertNotIn(SUBJECT.subject_id, {item.pseudonymous_subject_id for item in view.subjects})
        self.assertNotIn(claim.capability_key, view.preserved_fact_states)
        self.assertEqual(view.withheld_fact_keys, (claim.capability_key,))
        with self.assertRaises(HardwareGenomeIntegrityError):
            from iris_hardware_genome import RedactedGenomeView
            RedactedGenomeView(view.view_id, view.source_genome_id, view.redaction_policy, view.subjects, view.capabilities, view.preserved_fact_states, view.withheld_fact_keys, True)
        with self.assertRaises(HardwareGenomeValidationError):
            RedactionPolicy("unsafe", "1.0", (), redact_locators=False)

    def test_recovery_keeps_history_historical_until_new_complete_discovery(self):
        source = genome()
        restored = restore_as_historical(source, restoration_id="restore", restored_at_ms=2_000)
        with self.assertRaises(HardwareGenomeAdmissionError):
            require_fresh_current_truth(restored, snapshot(captured_at_ms=1_500))
        partial = snapshot((observation(state=ObservationState.PARTIAL, partial_frontier=("vendor",), observed_at_ms=3_000),), complete=False, captured_at_ms=3_000, frontier=("vendor",))
        with self.assertRaises(HardwareGenomeAdmissionError):
            require_fresh_current_truth(restored, partial)
        current = snapshot((observation(observation_id="fresh", observed_at_ms=3_000),), captured_at_ms=3_000)
        evidence = require_fresh_current_truth(restored, current)
        self.assertEqual(evidence.source_genome_id, source.genome_id)
        self.assertEqual(evidence.subject_ids, (SUBJECT.subject_id,))

    def test_discovery_adapter_is_explicitly_selected_and_exact_request_bound(self):
        session = DiscoverySessionRef("adapter-session", "1.0", RUNTIME, ("hardware.gpu.vendor",), 0, 5_000, 8, 100_000)
        class Adapter:
            adapter_id = "adapter"
            adapter_version = "1.0"
            def collect(self, session_arg, probe_arg):
                return DiscoveryBatch("adapter-batch", session_arg, probe_arg, (observation(),), 1_000, 128, True)
        batch = admit_adapter_batch(Adapter(), session, PROBE)
        admitted = admit_discovery_batch(batch, PROBE_REGISTRY)
        self.assertIs(admitted.completeness, ObservationState.OBSERVED)
        class Misdirected(Adapter):
            def collect(self, session_arg, probe_arg):
                wrong = DiscoverySessionRef("wrong-session", "1.0", RUNTIME, session_arg.requested_fact_keys, 0, 5_000, 8, 100_000)
                return DiscoveryBatch("wrong-batch", wrong, probe_arg, (observation(),), 1_000, 128, True)
        with self.assertRaises(HardwareGenomeAdmissionError):
            admit_adapter_batch(Misdirected(), session, PROBE)

    def test_m07_has_no_concrete_provider_execution_network_or_database_dependency(self):
        modules = validate_boundaries()
        self.assertGreaterEqual(len(modules), 20)

    def test_seven_domain_neutral_profiles_are_valid_and_non_live(self):
        from examples.m07_domain_neutral_profiles import build_seven_profiles
        profiles = build_seven_profiles()
        self.assertEqual(len(profiles), 7)
        self.assertEqual(len({item.profile_id for item in profiles}), 7)
        self.assertIn("gpu-8gb", {item.profile_id for item in profiles})
        self.assertIn("cpu-only", {item.profile_id for item in profiles})

    def test_external_authorities_remain_outside_the_semantic_kernel(self):
        import iris_hardware_genome as package
        self.assertNotIn("benchmark_workload", package.__all__)
        self.assertNotIn("schedule_gpu", package.__all__)
        self.assertNotIn("execute_workflow", package.__all__)
        self.assertEqual(PROBE.interface.value, "DECLARED_EVIDENCE")
        self.assertEqual(PROBE.permission_class.value, "BASIC_READ")
        self.assertFalse(hasattr(PROBE, "workflow_id"))


if __name__ == "__main__":
    unittest.main()
