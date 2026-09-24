from __future__ import annotations

import hashlib
import time
import unittest
from unittest.mock import patch

from iris_microbenchmark import (
    AbortReason, AuthorizationState, BackendAdapterCapsule, BenchmarkClass,
    BenchmarkAuthorizationReceipt, CancellationToken, CPUProbeRequest,
    CorrectnessState, Domain, EvidenceOrigin, FixtureKind, FixtureManifest,
    InterferenceState, MicrobenchmarkAdmissionError, MicrobenchmarkIntegrityError,
    MicrobenchmarkLimitError, MetricSemantics, PrivacyClass, ProbeDefinition,
    ResultState, TimingSource, admit_protocol, content_digest,
    SchemaDescriptor, SchemaVersion, create_document, decode_document,
    encode_document, execute_cpu_reference, execute_first_run_batch,
)
from iris_microbenchmark.enums import Aggregation, Directionality, QuantityKind
import iris_microbenchmark.execution as execution_module
from m08_support import binding, protocol


OPERATION = "cpu-reference-sha256"
PREDICATE = "sha256-equals-fixture-digest"


def make_request(
    *,
    protocol_id: str = "cpu-active-reference",
    backend_id: str = "cpu-reference",
    max_wall_ms: int = 5_000,
    max_iterations: int = 4,
    measured_iterations: int = 3,
    warmup_iterations: int = 1,
    first_run: bool = True,
    payload: bytes = b"IRIS bounded CPU reference payload" * 64,
    expected_fixture_digest: str | None = None,
    max_host_allocation_bytes: int = 1_000_000,
    authorization_lifetime_ms: int = 60_000,
    safety_class: BenchmarkClass = BenchmarkClass.TINY,
) -> CPUProbeRequest:
    selected_binding = binding(backend_id=backend_id, synthetic=False)
    selected_metric = MetricSemantics(
        "cpu-reference-latency", "1.0.0", QuantityKind.DURATION, "ms",
        Directionality.LOWER_IS_BETTER, Aggregation.MEAN, "exclude-warmup",
        min(2, measured_iterations), TimingSource.MONOTONIC_HOST, True,
    )
    selected_protocol = protocol(
        protocol_id=protocol_id,
        binding_value=selected_binding,
        metric_value=selected_metric,
        first_run=first_run,
        safety_class=safety_class,
        max_wall_ms=max_wall_ms,
        max_iterations=max_iterations,
        operation_family=OPERATION,
    )
    if max_host_allocation_bytes != 1_000_000:
        selected_protocol = selected_protocol.__class__(
            **{
                **selected_protocol.__dict__,
                "budget": selected_protocol.budget.__class__(
                    selected_protocol.budget.max_wall_ms,
                    selected_protocol.budget.max_warmup_ms,
                    selected_protocol.budget.max_iterations,
                    max_host_allocation_bytes,
                    selected_protocol.budget.max_device_allocation_bytes,
                    selected_protocol.budget.max_output_bytes,
                    selected_protocol.budget.max_concurrency,
                    selected_protocol.budget.max_retries,
                    selected_protocol.budget.cooldown_ms,
                    selected_protocol.budget.first_run,
                ),
            }
        )
    now_ms = time.time_ns() // 1_000_000
    receipt = BenchmarkAuthorizationReceipt(
        selected_protocol.authorization_id,
        "m08-active-cpu-test-policy",
        selected_protocol.protocol_id,
        selected_protocol.version,
        content_digest(selected_protocol),
        selected_protocol.binding.subject_id,
        selected_protocol.binding.runtime_id,
        content_digest(selected_protocol.binding),
        now_ms - 100,
        now_ms + max_wall_ms + authorization_lifetime_ms,
        AuthorizationState.GRANTED,
        selected_protocol.evidence_purpose.purpose_id,
    )
    admission = admit_protocol(selected_protocol, receipt, at_ms=now_ms)
    digest = expected_fixture_digest or hashlib.sha256(payload).hexdigest()
    selected_fixture = FixtureManifest(
        "cpu-active-fixture",
        digest,
        "m08-cpu-reference-byte-fixture",
        "1.0.0",
        FixtureKind.DETERMINISTIC_SYNTHETIC,
        PrivacyClass.SYNTHETIC,
        None,
        "cpu-active-fixture-seed",
        len(payload),
    )
    adapter = BackendAdapterCapsule(
        "m08-cpu-reference-adapter", "1.0.0", backend_id, "1.0.0",
        (OPERATION,), ("monotonic-host-timing", "sha256-reference"),
    )
    selected_probe = ProbeDefinition(
        "cpu-active-probe",
        selected_protocol.protocol_id,
        Domain.SYSTEM,
        OPERATION,
        selected_fixture.fixture_id,
        {"payload_bytes": len(payload)},
        {"digest_bytes": 32},
        "sha256",
        warmup_iterations,
        measured_iterations,
        "synchronous-completion",
        PREDICATE,
        adapter,
        ("runtime-api",),
    )
    cancellation = CancellationToken(selected_protocol.cancellation_path)
    return CPUProbeRequest(selected_protocol, admission, selected_fixture, selected_probe, payload, cancellation)


class TestActiveCPUReference(unittest.TestCase):
    def test_cpu_measurement_uses_monotonic_samples_and_real_origin(self):
        request = make_request()
        outcome = execute_cpu_reference(request)

        self.assertEqual(outcome.state, ResultState.PARTIAL)
        self.assertIsNotNone(outcome.result)
        self.assertEqual(outcome.result.origin, EvidenceOrigin.LOCAL_ACTIVE_MEASUREMENT)
        self.assertGreaterEqual(len(outcome.result.samples), 2)
        self.assertTrue(all(sample.elapsed_ns > 0 for sample in outcome.result.samples))
        self.assertEqual(outcome.result.metric.timing_source, TimingSource.MONOTONIC_HOST)
        self.assertEqual(outcome.receipt.timing_clock, "time.perf_counter_ns")
        self.assertEqual(outcome.receipt.completed_iterations, len(outcome.result.samples))
        self.assertEqual(outcome.receipt.requested_iterations, request.probe.measured_iterations)
        self.assertEqual(outcome.receipt.warmup_iterations, request.probe.warmup_iterations)
        self.assertEqual(outcome.receipt.retry_count, 0)
        self.assertIsNotNone(outcome.result.uncertainty)
        self.assertEqual(outcome.result.correctness.state, CorrectnessState.PASS)
        self.assertEqual(outcome.result.metric.unit, "ms")
        self.assertTrue(outcome.receipt.physical_measurement)
        self.assertEqual(outcome.receipt.interference_state, InterferenceState.UNKNOWN_TELEMETRY)

    def test_synthetic_input_is_distinct_from_physical_execution_origin(self):
        outcome = execute_cpu_reference(make_request())
        self.assertTrue(outcome.receipt.synthetic_fixture)
        self.assertTrue(outcome.receipt.physical_measurement)
        self.assertFalse(outcome.result.binding.synthetic)
        self.assertEqual(outcome.result.origin, EvidenceOrigin.LOCAL_ACTIVE_MEASUREMENT)

    def test_execution_receipt_has_deterministic_schema_round_trip(self):
        outcome = execute_cpu_reference(make_request())
        schema = SchemaDescriptor("iris-m08-core", SchemaVersion(1, 0, 0), (), (), "nfc-json-sort-v1")
        document = create_document(schema, outcome.receipt, created_at_ms=outcome.result.measured_at_ms)

        decoded = decode_document(encode_document(document))

        self.assertEqual(decoded, document)

    def test_unknown_interference_cannot_be_promoted_to_valid(self):
        outcome = execute_cpu_reference(make_request())
        self.assertEqual(outcome.result.interference.state, InterferenceState.UNKNOWN_TELEMETRY)
        self.assertNotEqual(outcome.result.state, ResultState.VALID)

    def test_cancellation_is_terminal_and_emits_abort_without_samples(self):
        request = make_request()
        request.cancellation.cancel()
        outcome = execute_cpu_reference(request)
        self.assertEqual(outcome.state, ResultState.CANCELLED)
        self.assertIsNone(outcome.result)
        self.assertEqual(outcome.receipt.abort_reason, AbortReason.USER_CANCELLED)
        self.assertEqual(outcome.receipt.completed_iterations, 0)

    def test_wall_clock_abort_is_checked_inside_bounded_work_chunks(self):
        request = make_request(max_wall_ms=1, max_iterations=4, payload=b"x" * 256)
        clock_value = 1_000_000_000

        def over_deadline() -> int:
            nonlocal clock_value
            clock_value += 2_000_000
            return clock_value

        with patch("iris_microbenchmark.execution.time.perf_counter_ns", side_effect=over_deadline):
            outcome = execute_cpu_reference(request)
        self.assertEqual(outcome.state, ResultState.INVALID_RESOURCE_ABORT)
        self.assertIsNone(outcome.result)
        self.assertEqual(outcome.receipt.abort_reason, AbortReason.TIME_BUDGET)

    def test_host_allocation_budget_aborts_before_hash_or_sample_creation(self):
        request = make_request(max_host_allocation_bytes=1_024, payload=b"x" * 4_096)
        outcome = execute_cpu_reference(request)
        self.assertEqual(outcome.state, ResultState.INVALID_RESOURCE_ABORT)
        self.assertIsNone(outcome.result)
        self.assertEqual(outcome.receipt.abort_reason, AbortReason.RESOURCE_LIMIT)
        self.assertEqual(outcome.receipt.completed_iterations, 0)

    def test_fixture_correctness_failure_cannot_create_positive_result(self):
        request = make_request(expected_fixture_digest="0" * 64)
        outcome = execute_cpu_reference(request)
        self.assertEqual(outcome.state, ResultState.INVALID_PROTOCOL)
        self.assertIsNone(outcome.result)
        self.assertEqual(outcome.receipt.correctness_state, CorrectnessState.FAIL)
        self.assertFalse(outcome.receipt.physical_measurement)

    def test_unsupported_backend_returns_no_physical_evidence(self):
        request = make_request(backend_id="provider-gpu", first_run=False)
        outcome = execute_cpu_reference(request)
        self.assertEqual(outcome.state, ResultState.UNSUPPORTED)
        self.assertIsNone(outcome.result)
        self.assertFalse(outcome.receipt.physical_measurement)
        self.assertEqual(outcome.receipt.timing_source, TimingSource.UNKNOWN)

    def test_sustained_cpu_protocol_is_unsupported_without_thermal_telemetry(self):
        requests = (
            make_request(first_run=False, safety_class=BenchmarkClass.SUSTAINED),
            make_request(protocol_id="long-cpu-reference", first_run=False, max_wall_ms=20_000),
        )
        for request in requests:
            with self.subTest(protocol_id=request.protocol.protocol_id):
                outcome = execute_cpu_reference(request)
                self.assertEqual(outcome.state, ResultState.UNSUPPORTED)
                self.assertIsNone(outcome.result)
                self.assertFalse(outcome.receipt.physical_measurement)

    def test_first_run_aggregate_budget_fails_before_execution(self):
        requests = tuple(
            make_request(protocol_id=f"first-run-{index}", max_wall_ms=15_000)
            for index in range(5)
        )
        with self.assertRaises(MicrobenchmarkLimitError):
            execute_first_run_batch(requests)

    def test_first_run_batch_records_unstarted_probes_after_terminal_abort(self):
        first = make_request(protocol_id="first-run-cancelled")
        second = make_request(protocol_id="first-run-not-started")
        first.cancellation.cancel()

        outcomes = execute_first_run_batch((first, second))

        self.assertEqual(len(outcomes), 2)
        self.assertEqual(outcomes[0].state, ResultState.CANCELLED)
        self.assertEqual(outcomes[1].state, ResultState.CANCELLED)
        self.assertEqual(outcomes[1].receipt.abort_reason, AbortReason.USER_CANCELLED)
        self.assertFalse(outcomes[1].receipt.physical_measurement)

    def test_executor_concurrency_gate_rejects_an_overlapping_attempt(self):
        request = make_request()
        self.assertTrue(execution_module._ACTIVE_CPU_EXECUTION.acquire(blocking=False))
        try:
            with self.assertRaises(MicrobenchmarkAdmissionError):
                execute_cpu_reference(request)
        finally:
            execution_module._ACTIVE_CPU_EXECUTION.release()

    def test_protocol_probe_and_fixture_identity_must_match(self):
        request = make_request()
        wrong_probe = request.probe.__class__(
            **{**request.probe.__dict__, "fixture_id": "other-fixture"}
        )
        mismatched = CPUProbeRequest(
            request.protocol, request.admission, request.fixture, wrong_probe,
            request.payload, request.cancellation,
        )
        with self.assertRaises(MicrobenchmarkIntegrityError):
            execute_cpu_reference(mismatched)

    def test_authorization_denial_fails_closed_before_execution(self):
        from dataclasses import replace

        now_ms = time.time_ns() // 1_000_000
        request = make_request()
        denied = replace(request.admission.authorization_receipt, state=AuthorizationState.DENIED)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            admit_protocol(request.protocol, denied, at_ms=now_ms)

    def test_expired_authorization_cannot_start_active_measurement(self):
        request = make_request(max_wall_ms=1, authorization_lifetime_ms=10)
        time.sleep(0.06)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            execute_cpu_reference(request)


if __name__ == "__main__":
    unittest.main()
