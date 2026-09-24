"""Bounded local CPU reference execution for admitted M08 probes."""

from __future__ import annotations

import hashlib
import math
import statistics
import threading
import time
from dataclasses import dataclass, field as dataclass_field

from .base import M08Record, content_digest
from .enums import (
    AbortReason, BenchmarkClass, CorrectnessState, EvidenceOrigin, FixtureKind,
    InterferenceState, ResultState, TimingSource,
)
from .errors import (
    MicrobenchmarkAdmissionError, MicrobenchmarkIntegrityError,
    MicrobenchmarkLimitError, MicrobenchmarkValidationError,
)
from .evidence import (
    AbortEvidence, BenchmarkResult, CorrectnessEvidence, InterferenceEvidence,
    MeasurementSample, create_result,
)
from .limits import DEFAULT_LIMITS, M08Limits
from .probes import FixtureManifest, ProbeDefinition
from .protocols import (
    ProtocolAdmission, ProtocolDescriptor, admit_protocol,
    validate_first_run_batch,
)
from .versions import require_digest, require_identifier, require_nonnegative_int

__all__ = [
    "CancellationToken", "CPUProbeRequest", "ActiveExecutionReceipt",
    "ExecutionOutcome", "execute_cpu_reference", "execute_first_run_batch",
]

_CPU_REFERENCE_BACKEND = "cpu-reference"
_CPU_REFERENCE_OPERATION = "cpu-reference-sha256"
_CPU_REFERENCE_PREDICATE = "sha256-equals-fixture-digest"
_CHUNK_BYTES = 65_536
_ACTIVE_CPU_EXECUTION = threading.Lock()


@dataclass(frozen=True)
class CancellationToken:
    """Thread-safe caller-owned cancellation signal; the kernel starts no threads."""

    token_id: str
    _event: threading.Event = dataclass_field(default_factory=threading.Event, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "token_id", require_identifier(self.token_id, "token_id"))

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


@dataclass(frozen=True)
class CPUProbeRequest:
    protocol: ProtocolDescriptor
    admission: ProtocolAdmission
    fixture: FixtureManifest
    probe: ProbeDefinition
    payload: bytes
    cancellation: CancellationToken

    def __post_init__(self) -> None:
        object.__setattr__(self, "protocol", ProtocolDescriptor.coerce(self.protocol, "protocol"))
        object.__setattr__(self, "admission", ProtocolAdmission.coerce(self.admission, "admission"))
        object.__setattr__(self, "fixture", FixtureManifest.coerce(self.fixture, "fixture"))
        object.__setattr__(self, "probe", ProbeDefinition.coerce(self.probe, "probe"))
        if type(self.payload) is not bytes:
            raise MicrobenchmarkValidationError("CPU reference payload must be immutable bytes")
        if type(self.cancellation) is not CancellationToken:
            raise MicrobenchmarkValidationError("CPU reference execution requires a caller cancellation token")


@dataclass(frozen=True)
class ActiveExecutionReceipt(M08Record):
    execution_id: str
    protocol_digest: str
    admission_digest: str
    probe_digest: str
    fixture_id: str
    fixture_digest: str
    input_digest: str
    operation_id: str
    timing_source: TimingSource
    timing_clock: str
    started_at_ms: int
    finished_at_ms: int
    elapsed_ns: int
    warmup_iterations: int
    requested_iterations: int
    completed_iterations: int
    allocation_bytes: int
    device_allocation_bytes: int
    retry_count: int
    correctness_state: CorrectnessState
    interference_state: InterferenceState
    abort_reason: AbortReason | None
    result_digest: str | None
    physical_measurement: bool
    synthetic_fixture: bool

    def __post_init__(self) -> None:
        for field in ("execution_id", "fixture_id", "operation_id", "timing_clock"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        for field in ("protocol_digest", "admission_digest", "probe_digest", "fixture_digest", "input_digest"):
            object.__setattr__(self, field, require_digest(getattr(self, field), field))
        for field in (
            "started_at_ms", "finished_at_ms", "elapsed_ns", "warmup_iterations",
            "requested_iterations", "completed_iterations", "allocation_bytes",
            "device_allocation_bytes", "retry_count",
        ):
            object.__setattr__(self, field, require_nonnegative_int(getattr(self, field), field))
        if self.finished_at_ms < self.started_at_ms or self.completed_iterations > self.requested_iterations:
            raise MicrobenchmarkIntegrityError("execution receipt timing or iteration counts are inconsistent")
        if self.completed_iterations and (not self.physical_measurement or self.timing_source is not TimingSource.MONOTONIC_HOST):
            raise MicrobenchmarkIntegrityError("measured iterations require a physical monotonic-host execution")
        if self.abort_reason is not None and self.completed_iterations == self.requested_iterations:
            raise MicrobenchmarkIntegrityError("completed execution cannot retain an abort reason")
        if self.result_digest is not None:
            object.__setattr__(self, "result_digest", require_digest(self.result_digest, "result_digest"))
        if not isinstance(self.timing_source, TimingSource) or not isinstance(self.correctness_state, CorrectnessState):
            raise MicrobenchmarkValidationError("execution receipt uses an invalid timing or correctness state")
        if not isinstance(self.interference_state, InterferenceState):
            raise MicrobenchmarkValidationError("execution receipt uses an invalid interference state")
        if self.abort_reason is not None and not isinstance(self.abort_reason, AbortReason):
            raise MicrobenchmarkValidationError("abort_reason must be AbortReason or None")
        if type(self.physical_measurement) is not bool or type(self.synthetic_fixture) is not bool:
            raise MicrobenchmarkValidationError("execution origin flags must be bool")


@dataclass(frozen=True)
class ExecutionOutcome(M08Record):
    state: ResultState
    result: BenchmarkResult | None
    receipt: ActiveExecutionReceipt

    def __post_init__(self) -> None:
        if not isinstance(self.state, ResultState):
            raise MicrobenchmarkValidationError("state must be ResultState")
        object.__setattr__(self, "receipt", ActiveExecutionReceipt.coerce(self.receipt, "receipt"))
        if self.result is not None:
            object.__setattr__(self, "result", BenchmarkResult.coerce(self.result, "result"))
            if self.result.state is not self.state or self.receipt.result_digest != content_digest(self.result):
                raise MicrobenchmarkIntegrityError("execution outcome does not bind its exact benchmark result")
        elif self.receipt.result_digest is not None:
            raise MicrobenchmarkIntegrityError("execution receipt cannot name an absent benchmark result")


class _Abort(Exception):
    def __init__(self, reason: AbortReason, frontier: str, evidence_ref: str) -> None:
        self.reason = reason
        self.frontier = frontier
        self.evidence_ref = evidence_ref


def _wall_ms() -> int:
    return time.time_ns() // 1_000_000


def _new_receipt(
    request: CPUProbeRequest,
    *,
    execution_id: str,
    input_digest: str,
    started_at_ms: int,
    finished_at_ms: int,
    elapsed_ns: int,
    warmup_iterations: int,
    completed_iterations: int,
    allocation_bytes: int,
    correctness_state: CorrectnessState,
    interference_state: InterferenceState,
    abort_reason: AbortReason | None,
    result: BenchmarkResult | None,
    physical_measurement: bool,
    timing_source: TimingSource,
) -> ActiveExecutionReceipt:
    return ActiveExecutionReceipt(
        execution_id,
        content_digest(request.protocol),
        content_digest(request.admission),
        content_digest(request.probe),
        request.fixture.fixture_id,
        request.fixture.fixture_digest,
        input_digest,
        request.probe.operation_family,
        timing_source,
        "time.perf_counter_ns",
        started_at_ms,
        finished_at_ms,
        elapsed_ns,
        warmup_iterations,
        request.probe.measured_iterations,
        completed_iterations,
        allocation_bytes,
        0,
        0,
        correctness_state,
        interference_state,
        abort_reason,
        content_digest(result) if result is not None else None,
        physical_measurement,
        request.fixture.kind is FixtureKind.DETERMINISTIC_SYNTHETIC,
    )


def _validate_request(request: CPUProbeRequest, limits: M08Limits, now_ms: int) -> ProtocolAdmission:
    protocol = request.protocol
    probe = request.probe
    fixture = request.fixture
    admission = request.admission
    if (probe.protocol_id, probe.domain, probe.operation_family, probe.fixture_id) != (
        protocol.protocol_id, protocol.domain, protocol.operation_family, fixture.fixture_id,
    ):
        raise MicrobenchmarkIntegrityError("probe, fixture, and exact admitted protocol identities differ")
    if request.cancellation.token_id != protocol.cancellation_path:
        raise MicrobenchmarkAdmissionError("caller cancellation token does not match the admitted protocol path")
    if (
        admission.protocol_id != protocol.protocol_id
        or admission.protocol_version != protocol.version
        or admission.binding_digest != content_digest(protocol.binding)
        or admission.authorization_receipt_id != protocol.authorization_id
        or admission.authorization_receipt.protocol_digest != content_digest(protocol)
    ):
        raise MicrobenchmarkIntegrityError("admission does not bind the exact protocol and M07 provenance")
    if now_ms < admission.admitted_at_ms:
        raise MicrobenchmarkAdmissionError("active execution cannot precede its admission")
    renewed = admit_protocol(protocol, admission.authorization_receipt, at_ms=now_ms, limits=limits)
    if renewed.security_authorization_id != admission.security_authorization_id:
        raise MicrobenchmarkIntegrityError("security authorization differs from the admitted protocol")
    protocol.budget.validate_against(limits)
    if protocol.budget.first_run:
        validate_first_run_batch((protocol,), limits=limits)
    if request.probe.warmup_iterations + request.probe.measured_iterations > protocol.budget.max_iterations:
        raise MicrobenchmarkLimitError("probe iterations exceed the admitted total iteration budget")
    if request.probe.measured_iterations < protocol.metrics[0].minimum_samples:
        raise MicrobenchmarkAdmissionError("probe does not meet the admitted metric sample minimum")
    if now_ms + protocol.budget.max_wall_ms + 1 >= admission.authorization_receipt.expires_at_ms:
        raise MicrobenchmarkAdmissionError("authorization expiry does not cover the full active execution ceiling")
    security = protocol.security_authorization_ref
    if protocol.security_authorization_required and (security is None or now_ms + protocol.budget.max_wall_ms + 1 >= security.expires_at_ms):
        raise MicrobenchmarkAdmissionError("security authorization expiry does not cover the full active execution ceiling")
    return renewed


def _unsupported(request: CPUProbeRequest, state: ResultState, now_ms: int) -> ExecutionOutcome:
    digest = request.fixture.fixture_digest
    execution_id = content_digest(("m08-unsupported-execution-v1", content_digest(request.protocol), content_digest(request.probe), now_ms))[:32]
    receipt = _new_receipt(
        request,
        execution_id=execution_id,
        input_digest=digest,
        started_at_ms=now_ms,
        finished_at_ms=now_ms,
        elapsed_ns=0,
        warmup_iterations=0,
        completed_iterations=0,
        allocation_bytes=0,
        correctness_state=CorrectnessState.UNSUPPORTED,
        interference_state=InterferenceState.UNKNOWN_TELEMETRY,
        abort_reason=None,
        result=None,
        physical_measurement=False,
        timing_source=TimingSource.UNKNOWN,
    )
    return ExecutionOutcome(state, None, receipt)


def _resource_rejected(request: CPUProbeRequest, now_ms: int, observed_bytes: int) -> ExecutionOutcome:
    execution_id = content_digest(("m08-cpu-resource-reject-v1", content_digest(request.protocol), content_digest(request.probe), now_ms))[:32]
    receipt = _new_receipt(
        request,
        execution_id=execution_id,
        input_digest=request.fixture.fixture_digest,
        started_at_ms=now_ms,
        finished_at_ms=now_ms,
        elapsed_ns=0,
        warmup_iterations=0,
        completed_iterations=0,
        allocation_bytes=observed_bytes,
        correctness_state=CorrectnessState.NOT_CHECKED,
        interference_state=InterferenceState.UNKNOWN_TELEMETRY,
        abort_reason=AbortReason.RESOURCE_LIMIT,
        result=None,
        physical_measurement=False,
        timing_source=TimingSource.UNKNOWN,
    )
    return ExecutionOutcome(ResultState.INVALID_RESOURCE_ABORT, None, receipt)


def _not_started_after_batch_limit(request: CPUProbeRequest, reason: AbortReason) -> ExecutionOutcome:
    now_ms = _wall_ms()
    execution_id = content_digest((
        "m08-cpu-batch-not-started-v1", content_digest(request.protocol),
        content_digest(request.probe), now_ms, reason.value,
    ))[:32]
    receipt = _new_receipt(
        request,
        execution_id=execution_id,
        input_digest=request.fixture.fixture_digest,
        started_at_ms=now_ms,
        finished_at_ms=now_ms,
        elapsed_ns=0,
        warmup_iterations=0,
        completed_iterations=0,
        allocation_bytes=0,
        correctness_state=CorrectnessState.NOT_CHECKED,
        interference_state=InterferenceState.UNKNOWN_TELEMETRY,
        abort_reason=reason,
        result=None,
        physical_measurement=False,
        timing_source=TimingSource.UNKNOWN,
    )
    return ExecutionOutcome(_result_state_for_abort(reason), None, receipt)


def _perform_hash(payload_view: memoryview, cancellation: CancellationToken, deadline_ns: int, frontier: str) -> bytes:
    digest = hashlib.sha256()
    for offset in range(0, len(payload_view), _CHUNK_BYTES):
        if cancellation.cancelled:
            raise _Abort(AbortReason.USER_CANCELLED, frontier, cancellation.token_id)
        if time.perf_counter_ns() >= deadline_ns:
            raise _Abort(AbortReason.TIME_BUDGET, frontier, "protocol-wall-deadline")
        digest.update(payload_view[offset : offset + _CHUNK_BYTES])
    if cancellation.cancelled:
        raise _Abort(AbortReason.USER_CANCELLED, frontier, cancellation.token_id)
    return digest.digest()


def _result_state_for_abort(reason: AbortReason) -> ResultState:
    if reason is AbortReason.USER_CANCELLED:
        return ResultState.CANCELLED
    if reason in {AbortReason.RESOURCE_LIMIT, AbortReason.TIME_BUDGET}:
        return ResultState.INVALID_RESOURCE_ABORT
    return ResultState.INVALID_PROTOCOL


def _execute_locked(
    request: CPUProbeRequest,
    *,
    limits: M08Limits,
    batch_deadline_ns: int | None = None,
) -> ExecutionOutcome:
    protocol = request.protocol
    now_ms = _wall_ms()
    admission = _validate_request(request, limits, now_ms)
    probe = request.probe
    fixture = request.fixture
    if protocol.binding.synthetic:
        raise MicrobenchmarkAdmissionError("local active measurements require exact non-synthetic M07 provenance")
    if len(protocol.metrics) != 1:
        return _unsupported(request, ResultState.UNSUPPORTED, now_ms)
    metric = protocol.metrics[0]
    if not time.get_clock_info("perf_counter").monotonic:
        return _unsupported(request, ResultState.UNAVAILABLE, now_ms)
    if (
        protocol.domain.value != "SYSTEM"
        or protocol.binding.backend_id != _CPU_REFERENCE_BACKEND
        or probe.adapter.backend_id != _CPU_REFERENCE_BACKEND
        or probe.operation_family != _CPU_REFERENCE_OPERATION
        or probe.correctness_predicate != _CPU_REFERENCE_PREDICATE
        or probe.precision != "sha256"
        or probe.synchronization_semantics != "synchronous-completion"
        or probe.adapter.version != protocol.binding.backend_version
        or probe.adapter.protocol_mechanics_version != protocol.version
        or not {"monotonic-host-timing", "sha256-reference"}.issubset(probe.adapter.declared_capabilities)
        or metric.timing_source is not TimingSource.MONOTONIC_HOST
        or metric.quantity_kind.value != "DURATION"
        or metric.unit not in {"ms", "ns"}
        or protocol.safety_class is BenchmarkClass.SUSTAINED
        or protocol.budget.max_wall_ms > limits.max_first_run_protocol_ms
    ):
        return _unsupported(request, ResultState.UNSUPPORTED, now_ms)
    if fixture.payload_bytes != len(request.payload):
        raise MicrobenchmarkIntegrityError("fixture payload length differs from its immutable manifest")
    if request.probe.input_shape != {"payload_bytes": len(request.payload)} or request.probe.output_shape != {"digest_bytes": 32}:
        raise MicrobenchmarkIntegrityError("CPU reference probe shape does not bind the exact payload and digest sizes")
    budget = protocol.budget
    allocation_bytes = len(request.payload) + min(len(request.payload), _CHUNK_BYTES) + 64
    limits.require("max_host_allocation_bytes", allocation_bytes)
    if allocation_bytes > budget.max_host_allocation_bytes or 32 > budget.max_output_bytes:
        return _resource_rejected(request, now_ms, allocation_bytes)
    started_at_ms = _wall_ms()
    started_ns = time.perf_counter_ns()
    protocol_deadline_ns = started_ns + budget.max_wall_ms * 1_000_000
    deadline_ns = min(protocol_deadline_ns, batch_deadline_ns) if batch_deadline_ns is not None else protocol_deadline_ns
    interference = InterferenceEvidence(InterferenceState.UNKNOWN_TELEMETRY, None, None, None)
    payload_view = memoryview(request.payload)
    try:
        input_digest = _perform_hash(payload_view, request.cancellation, deadline_ns, "fixture-correctness-precheck").hex()
    except _Abort as aborted:
        execution_id = content_digest(("m08-cpu-reference-abort-v1", content_digest(protocol), content_digest(probe), started_at_ms))[:32]
        return _aborted_outcome(request, admission, execution_id, fixture.fixture_digest, started_at_ms, started_ns, 0, (), aborted, interference, allocation_bytes)
    execution_id = content_digest((
        "m08-cpu-reference-execution-v1", content_digest(protocol),
        content_digest(admission), content_digest(probe), fixture.fixture_digest,
        input_digest, started_at_ms,
    ))[:32]
    if input_digest != fixture.fixture_digest:
        finished_ms = _wall_ms() + 1
        receipt = _new_receipt(
            request, execution_id=execution_id, input_digest=input_digest,
            started_at_ms=started_at_ms, finished_at_ms=finished_ms,
            elapsed_ns=time.perf_counter_ns() - started_ns, warmup_iterations=0,
            completed_iterations=0, allocation_bytes=allocation_bytes,
            correctness_state=CorrectnessState.FAIL,
            interference_state=InterferenceState.UNKNOWN_TELEMETRY,
            abort_reason=None, result=None, physical_measurement=False,
            timing_source=TimingSource.UNKNOWN,
        )
        return ExecutionOutcome(ResultState.INVALID_PROTOCOL, None, receipt)
    expected = bytes.fromhex(fixture.fixture_digest)

    correctness = CorrectnessEvidence(
        _CPU_REFERENCE_PREDICATE,
        "1.0.0",
        CorrectnessState.PASS,
        input_digest,
        fixture.fixture_digest,
        input_digest,
        None,
        _wall_ms(),
        fixture.fixture_id,
    )
    warmup_started_ns = time.perf_counter_ns()
    completed_warmups = 0
    samples: list[MeasurementSample] = []
    abort: _Abort | None = None
    try:
        for warmup_index in range(probe.warmup_iterations):
            output = _perform_hash(payload_view, request.cancellation, deadline_ns, f"warmup-{warmup_index + 1}")
            if output != expected:
                raise _Abort(AbortReason.PROTOCOL_VIOLATION, f"warmup-{warmup_index + 1}", "correctness-oracle-mismatch")
            completed_warmups += 1
            if time.perf_counter_ns() - warmup_started_ns > budget.max_warmup_ms * 1_000_000:
                raise _Abort(AbortReason.TIME_BUDGET, "warmup", "warmup-wall-deadline")
        for iteration in range(probe.measured_iterations):
            if request.cancellation.cancelled:
                raise _Abort(AbortReason.USER_CANCELLED, f"iteration-{iteration + 1}", request.cancellation.token_id)
            if time.perf_counter_ns() >= deadline_ns:
                raise _Abort(AbortReason.TIME_BUDGET, f"iteration-{iteration + 1}", "protocol-wall-deadline")
            observed_at_ms = _wall_ms()
            sample_started_ns = time.perf_counter_ns()
            output = _perform_hash(payload_view, request.cancellation, deadline_ns, f"iteration-{iteration + 1}")
            sample_elapsed_ns = time.perf_counter_ns() - sample_started_ns
            if output != expected:
                raise _Abort(AbortReason.PROTOCOL_VIOLATION, f"iteration-{iteration + 1}", "correctness-oracle-mismatch")
            if time.perf_counter_ns() > deadline_ns:
                raise _Abort(AbortReason.TIME_BUDGET, f"iteration-{iteration + 1}", "protocol-wall-deadline")
            value = sample_elapsed_ns / 1_000_000 if metric.unit == "ms" else float(sample_elapsed_ns)
            samples.append(MeasurementSample(f"{execution_id[:16]}-s{iteration + 1:04d}", value, observed_at_ms, sample_elapsed_ns))
    except _Abort as error:
        abort = error

    elapsed_ns = time.perf_counter_ns() - started_ns
    finished_at_ms = _wall_ms() + 1
    if finished_at_ms >= admission.authorization_receipt.expires_at_ms:
        raise MicrobenchmarkAdmissionError("authorization expired before active execution evidence was finalized")
    if protocol.security_authorization_required and protocol.security_authorization_ref is not None and finished_at_ms >= protocol.security_authorization_ref.expires_at_ms:
        raise MicrobenchmarkAdmissionError("security authorization expired before active execution evidence was finalized")
    abort_evidence = None
    if abort is not None:
        abort_evidence = AbortEvidence(
            f"{execution_id[:16]}-abort",
            abort.reason,
            finished_at_ms,
            abort.frontier,
            abort.evidence_ref,
            True,
        )
    if abort is not None:
        result_state = _result_state_for_abort(abort.reason)
    elif len(samples) < metric.minimum_samples:
        result_state = ResultState.PARTIAL
    else:
        # The stdlib reference executor has no trusted host-wide interference sensor.
        result_state = ResultState.PARTIAL
    uncertainty = statistics.pstdev(sample.value for sample in samples) / math.sqrt(len(samples)) if len(samples) > 1 else (0.0 if samples else None)
    result = create_result(
        protocol,
        admission,
        metric,
        tuple(samples),
        result_id=f"{execution_id[:16]}-result",
        state=result_state,
        correctness=correctness,
        interference=interference,
        measured_at_ms=finished_at_ms,
        uncertainty=uncertainty,
        abort=abort_evidence,
        origin=EvidenceOrigin.LOCAL_ACTIVE_MEASUREMENT,
    )
    receipt = _new_receipt(
        request,
        execution_id=execution_id,
        input_digest=input_digest,
        started_at_ms=started_at_ms,
        finished_at_ms=finished_at_ms,
        elapsed_ns=elapsed_ns,
        warmup_iterations=completed_warmups,
        completed_iterations=len(samples),
        allocation_bytes=allocation_bytes,
        correctness_state=CorrectnessState.PASS,
        interference_state=InterferenceState.UNKNOWN_TELEMETRY,
        abort_reason=abort.reason if abort is not None else None,
        result=result,
        physical_measurement=bool(samples),
        timing_source=TimingSource.MONOTONIC_HOST if samples else TimingSource.UNKNOWN,
    )
    return ExecutionOutcome(result_state, result, receipt)


def _aborted_outcome(
    request: CPUProbeRequest,
    admission: ProtocolAdmission,
    execution_id: str,
    input_digest: str,
    started_at_ms: int,
    started_ns: int,
    completed_warmups: int,
    samples: tuple[MeasurementSample, ...],
    abort: _Abort,
    interference: InterferenceEvidence,
    allocation_bytes: int,
) -> ExecutionOutcome:
    # This pre-measurement abort has no raw performance result to promote.
    finished_at_ms = _wall_ms() + 1
    receipt = _new_receipt(
        request,
        execution_id=execution_id,
        input_digest=input_digest,
        started_at_ms=started_at_ms,
        finished_at_ms=finished_at_ms,
        elapsed_ns=time.perf_counter_ns() - started_ns,
        warmup_iterations=completed_warmups,
        completed_iterations=0,
        allocation_bytes=allocation_bytes,
        correctness_state=CorrectnessState.NOT_CHECKED,
        interference_state=interference.state,
        abort_reason=abort.reason,
        result=None,
        physical_measurement=False,
        timing_source=TimingSource.UNKNOWN,
    )
    return ExecutionOutcome(_result_state_for_abort(abort.reason), None, receipt)


def execute_cpu_reference(request: CPUProbeRequest, *, limits: M08Limits = DEFAULT_LIMITS) -> ExecutionOutcome:
    """Run the one allowlisted CPU primitive after exact admission and safety checks."""
    if type(request) is not CPUProbeRequest:
        raise MicrobenchmarkValidationError("request must be an exact CPUProbeRequest")
    request = CPUProbeRequest(
        request.protocol, request.admission, request.fixture, request.probe,
        request.payload, request.cancellation,
    )
    _validate_request(request, limits, _wall_ms())
    if not _ACTIVE_CPU_EXECUTION.acquire(blocking=False):
        raise MicrobenchmarkAdmissionError("CPU reference executor concurrency ceiling is already occupied")
    try:
        return _execute_locked(request, limits=limits)
    finally:
        _ACTIVE_CPU_EXECUTION.release()


def execute_first_run_batch(
    requests: tuple[CPUProbeRequest, ...],
    *,
    limits: M08Limits = DEFAULT_LIMITS,
) -> tuple[ExecutionOutcome, ...]:
    """Execute an admitted first-run batch serially under one aggregate deadline."""
    if not isinstance(requests, tuple) or not requests:
        raise MicrobenchmarkValidationError("first-run batch must be a non-empty tuple")
    if len(requests) > limits.max_protocols:
        raise MicrobenchmarkLimitError("first-run batch exceeds the protocol-count ceiling")
    protocols = tuple(request.protocol for request in requests)
    aggregate_ms = validate_first_run_batch(protocols, limits=limits)
    for request in requests:
        _validate_request(request, limits, _wall_ms())
    if not _ACTIVE_CPU_EXECUTION.acquire(blocking=False):
        raise MicrobenchmarkAdmissionError("CPU reference executor concurrency ceiling is already occupied")
    try:
        batch_started_ns = time.perf_counter_ns()
        batch_deadline_ns = batch_started_ns + aggregate_ms * 1_000_000
        outcomes: list[ExecutionOutcome] = []
        for index, request in enumerate(requests):
            if time.perf_counter_ns() >= batch_deadline_ns:
                outcomes.extend(_not_started_after_batch_limit(item, AbortReason.TIME_BUDGET) for item in requests[index:])
                break
            outcomes.append(_execute_locked(request, limits=limits, batch_deadline_ns=batch_deadline_ns))
            if outcomes[-1].receipt.abort_reason is not None:
                outcomes.extend(
                    _not_started_after_batch_limit(item, outcomes[-1].receipt.abort_reason)
                    for item in requests[index + 1 :]
                )
                break
        return tuple(outcomes)
    finally:
        _ACTIVE_CPU_EXECUTION.release()
