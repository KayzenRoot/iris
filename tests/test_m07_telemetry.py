from __future__ import annotations

import unittest
from dataclasses import replace

from iris_hardware_genome import (
    DerivationRule,
    FreshnessClass,
    HardwareGenomeAdmissionError,
    HardwareGenomeIntegrityError,
    HardwareGenomeLimitError,
    HardwareGenomeValidationError,
    MemoryCapacityFact,
    MemoryKind,
    MemoryPressureFact,
    MetricSemantics,
    ObservationState,
    PressureState,
    ProbePermissionClass,
    RuntimeScope,
    RuntimeSubjectRef,
    SamplingWindowPolicy,
    TelemetrySample,
    TelemetryWindow,
    ThermalCausalityEvidence,
    derive_counter_rate,
    require_telemetry_fresh,
    validate_derived_metric,
    validate_sample_registry,
    validate_sampling_window,
)
from m07_support import RUNTIME, SUBJECT, SUBJECT_1, evidence, observation


def sample(sample_id, metric, value, captured, *, semantics=MetricSemantics.INSTANTANEOUS_GAUGE, unit="watt", sequence=1, sensor=None, subject=SUBJECT, runtime=RUNTIME, expires=None):
    return TelemetrySample(
        sample_id, metric, semantics, value, unit, subject, runtime, "sensor-source", "1.0", sequence,
        captured, 10 if semantics in {MetricSemantics.CUMULATIVE_COUNTER, MetricSemantics.MONOTONIC_COUNTER} else 0,
        expires if expires is not None else captured + 1000, ObservationState.OBSERVED,
        evidence("evidence-" + sample_id, observed_at_ms=captured, subject=subject, runtime=runtime),
        sensor, "local",
    )


class TestTelemetry(unittest.TestCase):
    def test_metric_semantics_preserve_units_and_exact_scope(self):
        gauge = sample("power-1", "telemetry.gpu.power", 115.5, 1_000)
        self.assertIs(gauge.semantics, MetricSemantics.INSTANTANEOUS_GAUGE)
        with self.assertRaises(HardwareGenomeIntegrityError):
            TelemetrySample(
                "wrong-subject", "telemetry.gpu.power", MetricSemantics.INSTANTANEOUS_GAUGE, 100, "watt", SUBJECT, RUNTIME,
                "sensor-source", "1.0", 1, 1_000, 0, 2_000, ObservationState.OBSERVED,
                evidence("wrong-subject-e", observed_at_ms=1_000, subject=SUBJECT_1), visibility_scope="local",
            )
        from iris_hardware_genome import SemanticKeyRegistry
        validate_sample_registry(gauge, SemanticKeyRegistry())

    def test_static_memory_capacity_is_not_dynamic_availability_or_pressure(self):
        capacity_obs = observation("hardware.gpu.dedicated_vram_bytes", observation_id="vram", value=8 * 1024**3, unit="byte", freshness=FreshnessClass.TOPOLOGY_STABLE)
        capacity = MemoryCapacityFact("vram-capacity", SUBJECT.subject_id, MemoryKind.DEDICATED_VRAM, 8 * 1024**3, capacity_obs)
        self.assertEqual(capacity.capacity_bytes, 8 * 1024**3)
        dynamic_obs = observation("hardware.gpu.dedicated_vram_bytes", observation_id="dynamic-vram", value=8 * 1024**3, unit="byte", freshness=FreshnessClass.DYNAMIC)
        with self.assertRaises(HardwareGenomeAdmissionError):
            MemoryCapacityFact("bad-capacity", SUBJECT.subject_id, MemoryKind.DEDICATED_VRAM, 8 * 1024**3, dynamic_obs)
        with self.assertRaises(HardwareGenomeAdmissionError):
            MemoryCapacityFact("storage-free", SUBJECT.subject_id, MemoryKind.STORAGE_AVAILABLE, 10, capacity_obs)
        reported = MemoryPressureFact("pressure", "host-memory", PressureState.PRESSURE_REPORTED, ("sample-a",))
        self.assertIs(reported.state, PressureState.PRESSURE_REPORTED)
        rule = DerivationRule("pressure-rule", "1.0", "USED_TOTAL_RATIO", (MetricSemantics.BOUNDED_PERCENTAGE,), MetricSemantics.DERIVED_VALUE)
        derived = MemoryPressureFact("derived-pressure", "host-memory", PressureState.CRITICAL_REPORTED, ("sample-a", "sample-b"), rule, False)
        self.assertEqual(derived.derivation_rule, rule)
        with self.assertRaises(HardwareGenomeAdmissionError):
            MemoryPressureFact("no-rule", "host-memory", PressureState.PRESSURE_REPORTED, ("sample-a",), None, False)

    def test_dynamic_telemetry_requires_fresh_evidence_and_sensor_identity(self):
        current = sample("temperature", "telemetry.gpu.temperature", 74.0, 1_000, unit="celsius", sensor="gpu-die")
        require_telemetry_fresh(current, now_ms=1_500)
        with self.assertRaises(HardwareGenomeAdmissionError):
            require_telemetry_fresh(current, now_ms=2_000)
        with self.assertRaises(HardwareGenomeAdmissionError):
            sample("no-sensor", "telemetry.gpu.temperature", 74.0, 1_000, unit="celsius")

    def test_counter_derivation_preserves_source_lineage_and_rejects_reset(self):
        earlier = sample("counter-a", "telemetry.gpu.memory_used", 1000, 1_000, semantics=MetricSemantics.CUMULATIVE_COUNTER, unit="byte", sequence=1)
        later = sample("counter-b", "telemetry.gpu.memory_used", 1500, 2_000, semantics=MetricSemantics.CUMULATIVE_COUNTER, unit="byte", sequence=2)
        rule = DerivationRule("rate", "1.0", "COUNTER_RATE", (MetricSemantics.CUMULATIVE_COUNTER,), MetricSemantics.DERIVED_VALUE)
        derived = derive_counter_rate(earlier, later, rule, derived_id="memory-rate")
        self.assertEqual(derived.source_sample_ids, ("counter-a", "counter-b"))
        self.assertEqual(derived.value, 500.0)
        self.assertEqual(derived.interval_ms, 1_000)
        reset = sample("counter-reset", "telemetry.gpu.memory_used", 10, 2_000, semantics=MetricSemantics.CUMULATIVE_COUNTER, unit="byte", sequence=2)
        with self.assertRaises(HardwareGenomeAdmissionError):
            derive_counter_rate(earlier, reset, rule, derived_id="invalid-rate")
        other = sample("counter-other", "telemetry.gpu.memory_used", 1500, 2_000, semantics=MetricSemantics.CUMULATIVE_COUNTER, unit="byte", sequence=2, runtime=RuntimeSubjectRef("host", RuntimeScope.HOST, "1.0"))
        with self.assertRaises(HardwareGenomeIntegrityError):
            derive_counter_rate(earlier, other, rule, derived_id="wrong-scope")

    def test_sampling_window_is_bounded_non_escalating_and_not_busy_looped(self):
        first = sample("sample-1", "telemetry.gpu.power", 100, 1_000, sequence=1)
        second = sample("sample-2", "telemetry.gpu.power", 105, 1_010, sequence=2)
        window = TelemetryWindow("window", SUBJECT.subject_id, RUNTIME.runtime_id, 1_000, 1_010, (first, second), True)
        policy = SamplingWindowPolicy("policy", "1.0", 10, 10, 1_000, 2_000, ProbePermissionClass.TELEMETRY_READ)
        validate_sampling_window(window, policy)
        too_fast = sample("sample-fast", "telemetry.gpu.power", 106, 1_005, sequence=3)
        fast_window = TelemetryWindow("window-fast", SUBJECT.subject_id, RUNTIME.runtime_id, 1_000, 1_005, (first, too_fast), True)
        with self.assertRaises(HardwareGenomeAdmissionError):
            validate_sampling_window(fast_window, policy)
        with self.assertRaises(HardwareGenomeLimitError):
            validate_sampling_window(window, SamplingWindowPolicy("short", "1.0", 10, 10, 5, 5, ProbePermissionClass.TELEMETRY_READ))
        with self.assertRaises(HardwareGenomeAdmissionError):
            SamplingWindowPolicy("escalate", "1.0", 10, 10, 1_000, 1_000, ProbePermissionClass.TELEMETRY_READ, True)
        with self.assertRaises(HardwareGenomeValidationError):
            SamplingWindowPolicy("open-permission", "1.0", 10, 10, 1_000, 1_000, "TELEMETRY_READ")

    def test_derived_metric_revalidates_formula_and_exact_source_binding(self):
        earlier = sample("counter-a", "telemetry.gpu.memory_used", 1_000, 1_000, semantics=MetricSemantics.CUMULATIVE_COUNTER, unit="byte", sequence=1)
        later = sample("counter-b", "telemetry.gpu.memory_used", 1_500, 2_000, semantics=MetricSemantics.CUMULATIVE_COUNTER, unit="byte", sequence=2)
        rule = DerivationRule("rate", "1.0", "COUNTER_RATE", (MetricSemantics.CUMULATIVE_COUNTER,), MetricSemantics.DERIVED_VALUE)
        derived = derive_counter_rate(earlier, later, rule, derived_id="memory-rate")
        validate_derived_metric(derived, (earlier, later))
        with self.assertRaises(HardwareGenomeIntegrityError):
            validate_derived_metric(replace(derived, value=derived.value + 1), (earlier, later))
        with self.assertRaises(HardwareGenomeIntegrityError):
            validate_derived_metric(derived, (earlier, replace(later, sample_id="other-counter")))

    def test_memory_pressure_and_thermal_causality_bind_evidence_scope_and_kind(self):
        percent_a = sample("percent-a", "telemetry.host.memory_pressure", 70, 1_000, semantics=MetricSemantics.BOUNDED_PERCENTAGE, unit="percent")
        percent_b = sample("percent-b", "telemetry.host.memory_pressure", 90, 2_000, semantics=MetricSemantics.BOUNDED_PERCENTAGE, unit="percent", sequence=2)
        rule = DerivationRule("pressure-rule", "1.0", "USED_TOTAL_RATIO", (MetricSemantics.BOUNDED_PERCENTAGE,), MetricSemantics.DERIVED_VALUE)
        pressure = MemoryPressureFact("derived-pressure", SUBJECT.subject_id, PressureState.CRITICAL_REPORTED, (percent_a.sample_id, percent_b.sample_id), rule, False)
        pressure.validate_against((percent_a, percent_b))
        other_subject = sample("percent-other", "telemetry.host.memory_pressure", 90, 2_000, semantics=MetricSemantics.BOUNDED_PERCENTAGE, unit="percent", sequence=2, subject=SUBJECT_1)
        with self.assertRaises(HardwareGenomeIntegrityError):
            pressure.validate_against((percent_a, other_subject))

        temp = sample("temp", "telemetry.gpu.temperature", 92, 1_000, unit="celsius", sensor="gpu-die")
        clock = sample("clock", "telemetry.gpu.clock_core", 300, 1_000, unit="megahertz")
        reason = observation("hardware.gpu.throttle_reason", observation_id="throttle-reason", value="thermal", unit=None)
        causal = ThermalCausalityEvidence("thermal-cause", (temp.sample_id,), (clock.sample_id,), (reason.observation_id,), ObservationState.OBSERVED)
        causal.validate_against((temp, clock), (reason,))
        wrong_reason = observation("hardware.gpu.power_limit_reason", observation_id="throttle-reason", value="power", unit=None)
        with self.assertRaises(HardwareGenomeIntegrityError):
            causal.validate_against((temp, clock), (wrong_reason,))

    def test_temperature_sensor_and_throttle_causality_are_not_inferred(self):
        temp = sample("temp", "telemetry.gpu.temperature", 92, 1_000, unit="celsius", sensor="gpu-die")
        self.assertEqual(temp.sensor_id, "gpu-die")
        with self.assertRaises(HardwareGenomeAdmissionError):
            ThermalCausalityEvidence("thermal-no-reason", (temp.sample_id,), (), (), ObservationState.OBSERVED)
        causal = ThermalCausalityEvidence("thermal-cause", (temp.sample_id,), ("clock",), ("throttle-reason",), ObservationState.OBSERVED)
        self.assertEqual(causal.throttle_reason_observation_ids, ("throttle-reason",))

    def test_unknown_or_stale_samples_never_become_current_pressure(self):
        with self.assertRaises(HardwareGenomeAdmissionError):
            TelemetrySample("unknown", "telemetry.gpu.power", MetricSemantics.INSTANTANEOUS_GAUGE, 1.0, "watt", SUBJECT, RUNTIME, "source", "1.0", 1, 1_000, 0, 2_000, ObservationState.UNKNOWN, evidence("unknown-e", observed_at_ms=1_000), visibility_scope="local")
        from iris_hardware_genome import SemanticKeyRegistry
        definition = SemanticKeyRegistry().find("telemetry.host.memory_pressure")
        self.assertEqual(definition.semantic_type, "pressure_state")
        self.assertIs(definition.freshness, FreshnessClass.DYNAMIC)

    def test_reported_limits_and_configured_limits_cannot_masquerade_as_usage(self):
        with self.assertRaises(HardwareGenomeValidationError):
            sample("reported-used", "telemetry.gpu.memory_used", 100, 1_000, semantics=MetricSemantics.REPORTED_LIMIT, unit="byte")
        with self.assertRaises(HardwareGenomeValidationError):
            sample("configured-used", "telemetry.gpu.memory_used", 100, 1_000, semantics=MetricSemantics.CONFIGURED_LIMIT, unit="byte")


if __name__ == "__main__":
    unittest.main()
