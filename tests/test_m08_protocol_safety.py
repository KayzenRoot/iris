from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from iris_microbenchmark import (
    AbortEvidence, AbortReason, AuthorizationState, BenchmarkClass, InterferenceEvidence, InterferenceState, MicrobenchmarkAdmissionError,
    MicrobenchmarkAuthorityError, MicrobenchmarkIntegrityError, MicrobenchmarkLimitError,
    ProtocolDescriptor, ResultState, SafetyBudget,
    SecurityAuthorizationReference, TimingCalibrationDescriptor, TimingSource,
    admit_protocol, content_digest, create_result, validate_first_run_batch, validate_result,
)
from m08_support import authorization, binding, measurement_result, metric, protocol


class TestProtocolSafety(unittest.TestCase):
    def test_protocol_authority_and_provenance(self):
        bound = binding(projection=True)
        selected = protocol(binding_value=bound)
        receipt = authorization(selected)
        admitted = admit_protocol(selected, receipt, at_ms=20)
        self.assertEqual(admitted.binding_digest, content_digest(bound))
        self.assertEqual(admitted.authorization_receipt, receipt)
        self.assertEqual(admitted.authority_namespace, "hardware-capability")

        foreign = authorization(selected, receipt_id="different-receipt")
        with self.assertRaises(MicrobenchmarkAdmissionError):
            admit_protocol(selected, foreign, at_ms=20)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            admit_protocol(selected, authorization(selected, state=AuthorizationState.DENIED), at_ms=20)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            admit_protocol(selected, receipt, at_ms=100_000)
        changed_budget = protocol(protocol_id=selected.protocol_id, max_wall_ms=4_000)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            admit_protocol(changed_budget, receipt, at_ms=20)

        security = SecurityAuthorizationReference(
            "security-grant-01", "security-policy-01", selected.protocol_id,
            selected.version, content_digest(bound), selected.evidence_purpose.purpose_id,
            bound.subject_id, bound.runtime_id, AuthorizationState.GRANTED, 90_000,
        )
        secured = protocol(binding_value=bound, security_required=True, security_reference=security)
        secured_admission = admit_protocol(secured, authorization(secured), at_ms=20)
        self.assertEqual(secured_admission.security_authorization_id, security.authorization_id)
        mismatched = SecurityAuthorizationReference(
            "security-grant-02", "security-policy-01", "other-protocol", selected.version,
            content_digest(bound), selected.evidence_purpose.purpose_id, bound.subject_id,
            bound.runtime_id, AuthorizationState.GRANTED, 90_000,
        )
        with self.assertRaises(MicrobenchmarkAdmissionError):
            admit_protocol(protocol(binding_value=bound, security_required=True, security_reference=mismatched), authorization(protocol(binding_value=bound, security_required=True, security_reference=mismatched)), at_ms=20)
        with self.assertRaises(MicrobenchmarkAuthorityError):
            protocol(binding_value=bound, security_required=False).__class__(
                **{**protocol(binding_value=bound).__dict__, "authority_namespace": "m10-execution-plan"}
            )

    def test_hard_budgets_and_first_run_safety(self):
        with self.assertRaises(MicrobenchmarkLimitError):
            SafetyBudget(900_001, 0, 1, 1, 1, 1, 1, 0, 0, False)
        with self.assertRaises(MicrobenchmarkLimitError):
            SafetyBudget(10, 0, 100_001, 1, 1, 1, 1, 0, 0, False)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            protocol(safety_class=BenchmarkClass.SUSTAINED, first_run=True)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            protocol(safety_class=BenchmarkClass.DESTRUCTIVE_OR_STRESS, first_run=False)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            protocol(safety_class=BenchmarkClass.SUSTAINED, first_run=False, max_wall_ms=1_000).__class__(
                **{**protocol(safety_class=BenchmarkClass.SUSTAINED, first_run=False).__dict__, "budget": SafetyBudget(1_000, 0, 2, 1, 1, 1, 1, 0, 0, False)}
            )

        within = tuple(protocol(protocol_id=f"first-run-{index}", max_wall_ms=10_000) for index in range(6))
        self.assertEqual(validate_first_run_batch(within), 60_000)
        over = within + (protocol(protocol_id="first-run-over", max_wall_ms=1_000),)
        with self.assertRaises(MicrobenchmarkLimitError):
            validate_first_run_batch(over)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            validate_first_run_batch((protocol(first_run=False),))

    def test_cancel_abort_interference_and_unknown_telemetry(self):
        selected = protocol()
        cancelled = AbortEvidence("cancel-01", AbortReason.USER_CANCELLED, 25, "iteration-1", "cancel-request-01", True)
        result = measurement_result(protocol_value=selected, state=ResultState.CANCELLED, abort=cancelled)
        self.assertEqual(result.state, ResultState.CANCELLED)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            AbortEvidence("cancel-02", AbortReason.USER_CANCELLED, 25, "iteration-1", "cancel-request-01", False)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            measurement_result(protocol_value=selected, state=ResultState.CANCELLED)

        contaminated = InterferenceEvidence(InterferenceState.CONTAMINATED, 0.5, 0.1, "load-spike-01")
        invalid = measurement_result(protocol_value=selected, state=ResultState.INVALID_INTERFERENCE, interference=contaminated)
        self.assertEqual(invalid.interference.state, InterferenceState.CONTAMINATED)
        unknown = InterferenceEvidence(InterferenceState.UNKNOWN_TELEMETRY, None, None, None)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            measurement_result(protocol_value=selected, interference=unknown)
        partial = measurement_result(protocol_value=selected, state=ResultState.PARTIAL, interference=unknown)
        self.assertEqual(partial.state, ResultState.PARTIAL)

    def test_timing_metric_uncertainty_and_comparability(self):
        timed = protocol(metric_value=metric(timing_source=TimingSource.SYNCHRONIZED_DEVICE_EVENT))
        result = measurement_result(protocol_value=timed, uncertainty=0.2)
        self.assertTrue(validate_result(result, timed))
        self.assertEqual(len(result.samples), 2)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            measurement_result(protocol_value=protocol(metric_value=metric(timing_source=TimingSource.UNKNOWN)))
        with self.assertRaises(MicrobenchmarkAdmissionError):
            measurement_result(protocol_value=protocol(), uncertainty=None)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            TimingCalibrationDescriptor("unknown-clock", "1.0.0", TimingSource.UNKNOWN, 1, True, "none", "unknown", 20)
        calibration = TimingCalibrationDescriptor("host-clock", "1.0.0", TimingSource.MONOTONIC_HOST, 10, True, "paired-samples", "host-only", 20)
        self.assertTrue(calibration.monotonic)

    def test_cpu_only_8gb_and_external_authority_firewalls(self):
        cpu = protocol(protocol_id="cpu-only-protocol", binding_value=binding(backend_id="cpu-only"))
        self.assertEqual(cpu.binding.backend_id, "cpu-only")
        zero_device = SafetyBudget(5_000, 100, 4, 1_000_000, 0, 64_000, 1, 0, 1_000, True)
        self.assertEqual(zero_device.max_device_allocation_bytes, 0)
        profile_capacity = 8 * 1024**3
        self.assertEqual(profile_capacity, 8_589_934_592)
        self.assertEqual(cpu.authority_namespace, "hardware-capability")
        with self.assertRaises(MicrobenchmarkAuthorityError):
            ProtocolDescriptor(
                **{**cpu.__dict__, "authority_namespace": "m09-vram-lease"}
            )

    def test_subject_scoping_raw_immutability_and_lineage(self):
        first = protocol(protocol_id="subject-a-protocol", binding_value=binding(subject_id="subject-a"))
        second = protocol(protocol_id="subject-b-protocol", binding_value=binding(subject_id="subject-b"))
        first_result = measurement_result(result_id="subject-a-result", protocol_value=first)
        second_result = measurement_result(result_id="subject-b-result", protocol_value=second)
        self.assertNotEqual(first_result.binding.subject_id, second_result.binding.subject_id)
        with self.assertRaises(MicrobenchmarkIntegrityError):
            validate_result(first_result, second)
        self.assertEqual(first_result.raw_digest, content_digest(first_result.samples))
        with self.assertRaises(FrozenInstanceError):
            first_result.samples = ()
        self.assertNotEqual(first_result.raw_digest, second_result.raw_digest)

    def test_result_binds_exact_m07_context_and_protocol(self):
        selected = protocol()
        result = measurement_result(protocol_value=selected)
        self.assertTrue(validate_result(result, selected))
        changed = protocol(protocol_id=selected.protocol_id, binding_value=binding(runtime_id="other-runtime"))
        with self.assertRaises(MicrobenchmarkIntegrityError):
            validate_result(result, changed)

    def test_abort_states_remain_explicit(self):
        thermal = AbortEvidence("thermal-01", AbortReason.THERMAL_LIMIT, 25, "sample-1", "thermal-sensor-01", True)
        result = measurement_result(state=ResultState.INVALID_THERMAL_ABORT, abort=thermal)
        self.assertEqual(result.abort.reason, AbortReason.THERMAL_LIMIT)
        self.assertEqual(result.state, ResultState.INVALID_THERMAL_ABORT)
        original = protocol()
        other = protocol(protocol_id="different-protocol")
        with self.assertRaises(MicrobenchmarkIntegrityError):
            create_result(
                other, admit_protocol(original, authorization(original), at_ms=20), metric(), (),
                result_id="bad-cross-protocol", state=ResultState.UNSUPPORTED,
                correctness=measurement_result().correctness,
                interference=measurement_result().interference, measured_at_ms=30,
            )


if __name__ == "__main__":
    unittest.main()
