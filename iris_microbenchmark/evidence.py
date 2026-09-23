"""Immutable raw results, correctness gates, interference, and abort evidence."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

from .base import M08Record, content_digest, require_sequence
from .enums import AbortReason, CorrectnessState, EvidenceOrigin, InterferenceState, ResultState
from .errors import MicrobenchmarkAdmissionError, MicrobenchmarkIntegrityError, MicrobenchmarkLimitError, MicrobenchmarkValidationError
from .limits import DEFAULT_LIMITS
from .provenance import M07ProvenanceBinding
from .protocols import MetricSemantics, ProtocolAdmission, ProtocolDescriptor, admit_protocol
from .versions import require_digest, require_finite_number, require_identifier, require_nonnegative_int, require_version

__all__ = [
    "MeasurementSample", "CorrectnessEvidence", "InterferenceEvidence", "AbortEvidence",
    "BenchmarkResult", "aggregate_samples", "create_result", "validate_result",
]


@dataclass(frozen=True)
class MeasurementSample(M08Record):
    sample_id: str
    value: float
    observed_at_ms: int
    elapsed_ns: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "sample_id", require_identifier(self.sample_id, "sample_id"))
        object.__setattr__(self, "value", require_finite_number(self.value, "value"))
        object.__setattr__(self, "observed_at_ms", require_nonnegative_int(self.observed_at_ms, "observed_at_ms"))
        object.__setattr__(self, "elapsed_ns", require_nonnegative_int(self.elapsed_ns, "elapsed_ns"))


@dataclass(frozen=True)
class CorrectnessEvidence(M08Record):
    oracle_id: str
    oracle_version: str
    state: CorrectnessState
    input_digest: str
    expected_digest: str | None
    output_digest: str | None
    tolerance: float | None
    checked_at_ms: int
    detail_ref: str | None
    expected_value: float | None = None
    observed_value: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "oracle_id", require_identifier(self.oracle_id, "oracle_id"))
        object.__setattr__(self, "oracle_version", require_version(self.oracle_version, "oracle_version"))
        if not isinstance(self.state, CorrectnessState):
            raise MicrobenchmarkValidationError("state must be CorrectnessState")
        object.__setattr__(self, "input_digest", require_digest(self.input_digest, "input_digest"))
        for field in ("expected_digest", "output_digest"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_digest(value, field))
        if self.tolerance is not None:
            tolerance = require_finite_number(self.tolerance, "tolerance")
            if tolerance < 0:
                raise MicrobenchmarkValidationError("correctness tolerance cannot be negative")
            object.__setattr__(self, "tolerance", tolerance)
        object.__setattr__(self, "checked_at_ms", require_nonnegative_int(self.checked_at_ms, "checked_at_ms"))
        if self.detail_ref is not None:
            object.__setattr__(self, "detail_ref", require_identifier(self.detail_ref, "detail_ref"))
        if self.state is CorrectnessState.PASS and self.expected_digest is not None and self.output_digest != self.expected_digest:
            raise MicrobenchmarkIntegrityError("exact correctness pass has different expected and observed digests")
        for field in ("expected_value", "observed_value"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_finite_number(value, field))
        if self.state is CorrectnessState.PASS:
            if self.expected_digest is not None and (self.output_digest is None or self.output_digest != self.expected_digest):
                raise MicrobenchmarkAdmissionError("exact correctness pass requires matching expected/output digests")
            if self.expected_digest is None and (
                self.tolerance is None or self.expected_value is None or self.observed_value is None
                or abs(self.expected_value - self.observed_value) > self.tolerance
            ):
                raise MicrobenchmarkAdmissionError("numeric correctness pass requires measured values inside its declared tolerance")


@dataclass(frozen=True)
class InterferenceEvidence(M08Record):
    state: InterferenceState
    observed_load_fraction: float | None
    tolerance_fraction: float | None
    observation_ref: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.state, InterferenceState):
            raise MicrobenchmarkValidationError("state must be InterferenceState")
        for field in ("observed_load_fraction", "tolerance_fraction"):
            value = getattr(self, field)
            if value is not None:
                number = require_finite_number(value, field)
                if not 0 <= number <= 1:
                    raise MicrobenchmarkValidationError(f"{field} must be within 0..1")
                object.__setattr__(self, field, number)
        if self.observation_ref is not None:
            object.__setattr__(self, "observation_ref", require_identifier(self.observation_ref, "observation_ref"))
        if self.state is InterferenceState.CONTAMINATED and self.observation_ref is None:
            raise MicrobenchmarkAdmissionError("contamination must retain an evidence reference")
        if self.state is InterferenceState.WITHIN_TOLERANCE and (
            self.observed_load_fraction is None or self.tolerance_fraction is None
            or self.observed_load_fraction > self.tolerance_fraction
        ):
            raise MicrobenchmarkIntegrityError("within-tolerance evidence must carry an in-range observed load")


@dataclass(frozen=True)
class AbortEvidence(M08Record):
    abort_id: str
    reason: AbortReason
    aborted_at_ms: int
    observed_frontier: str
    evidence_ref: str
    terminal_for_attempt: bool

    def __post_init__(self) -> None:
        for field in ("abort_id", "observed_frontier", "evidence_ref"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if not isinstance(self.reason, AbortReason):
            raise MicrobenchmarkValidationError("reason must be AbortReason")
        object.__setattr__(self, "aborted_at_ms", require_nonnegative_int(self.aborted_at_ms, "aborted_at_ms"))
        if self.terminal_for_attempt is not True:
            raise MicrobenchmarkAdmissionError("cancellation and abort are terminal for the active attempt")


@dataclass(frozen=True)
class BenchmarkResult(M08Record):
    result_id: str
    protocol_id: str
    protocol_version: str
    binding: M07ProvenanceBinding
    metric: MetricSemantics
    samples: tuple[MeasurementSample, ...]
    aggregate_value: float | None
    uncertainty: float | None
    state: ResultState
    correctness: CorrectnessEvidence
    interference: InterferenceEvidence
    abort: AbortEvidence | None
    measured_at_ms: int
    raw_digest: str
    origin: EvidenceOrigin
    external_measurement_ref: str | None

    def __post_init__(self) -> None:
        for field in ("result_id", "protocol_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "protocol_version", require_version(self.protocol_version, "protocol_version"))
        object.__setattr__(self, "binding", M07ProvenanceBinding.coerce(self.binding, "binding"))
        object.__setattr__(self, "metric", MetricSemantics.coerce(self.metric, "metric"))
        raw_samples = require_sequence(self.samples, "samples", maximum=DEFAULT_LIMITS.max_samples_per_result)
        samples = tuple(MeasurementSample.coerce(item, "samples[]") for item in raw_samples)
        if len({item.sample_id for item in samples}) != len(samples):
            raise MicrobenchmarkIntegrityError("result repeats a raw sample identity")
        object.__setattr__(self, "samples", samples)
        if self.aggregate_value is not None:
            object.__setattr__(self, "aggregate_value", require_finite_number(self.aggregate_value, "aggregate_value"))
        if self.uncertainty is not None:
            uncertainty = require_finite_number(self.uncertainty, "uncertainty")
            if uncertainty < 0:
                raise MicrobenchmarkValidationError("measurement uncertainty cannot be negative")
            object.__setattr__(self, "uncertainty", uncertainty)
        if not isinstance(self.state, ResultState):
            raise MicrobenchmarkValidationError("state must be ResultState")
        object.__setattr__(self, "correctness", CorrectnessEvidence.coerce(self.correctness, "correctness"))
        object.__setattr__(self, "interference", InterferenceEvidence.coerce(self.interference, "interference"))
        if self.abort is not None:
            object.__setattr__(self, "abort", AbortEvidence.coerce(self.abort, "abort"))
        object.__setattr__(self, "measured_at_ms", require_nonnegative_int(self.measured_at_ms, "measured_at_ms"))
        object.__setattr__(self, "raw_digest", require_digest(self.raw_digest, "raw_digest"))
        if not isinstance(self.origin, EvidenceOrigin):
            raise MicrobenchmarkValidationError("origin must be EvidenceOrigin")
        if self.external_measurement_ref is not None:
            object.__setattr__(self, "external_measurement_ref", require_identifier(self.external_measurement_ref, "external_measurement_ref"))
        if self.origin is EvidenceOrigin.SYNTHETIC_SEMANTIC_FIXTURE:
            if self.external_measurement_ref is not None or not self.binding.synthetic:
                raise MicrobenchmarkIntegrityError("synthetic semantic evidence must be scoped to synthetic M07 provenance")
        elif self.external_measurement_ref is None or self.binding.synthetic:
            raise MicrobenchmarkAdmissionError("external measurement references require non-synthetic M07 binding and an opaque source reference")
        if content_digest(self.samples) != self.raw_digest:
            raise MicrobenchmarkIntegrityError("raw evidence digest does not match immutable samples")
        if self.samples:
            expected = aggregate_samples(self.samples, self.metric)
            if self.aggregate_value is None or not math.isclose(expected, self.aggregate_value, rel_tol=1e-12, abs_tol=1e-12):
                raise MicrobenchmarkIntegrityError("aggregate does not match raw samples and metric semantics")
        elif self.aggregate_value is not None:
            raise MicrobenchmarkIntegrityError("result without samples cannot claim an aggregate")
        if self.metric.uncertainty_required and self.uncertainty is None and self.state is ResultState.VALID:
            raise MicrobenchmarkAdmissionError("metric semantics require retained measurement uncertainty")
        if self.state is ResultState.VALID:
            if self.metric.timing_source.value == "UNKNOWN":
                raise MicrobenchmarkAdmissionError("valid measurements require a qualified timing source")
            if self.correctness.state is not CorrectnessState.PASS:
                raise MicrobenchmarkAdmissionError("correctness must pass before a result can be valid")
            if self.interference.state is not InterferenceState.WITHIN_TOLERANCE:
                raise MicrobenchmarkAdmissionError("interference must be observed within protocol tolerance for a valid result")
            if self.abort is not None or len(self.samples) < self.metric.minimum_samples:
                raise MicrobenchmarkAdmissionError("aborted or under-sampled evidence cannot be valid")
        elif self.state in {ResultState.CANCELLED, ResultState.INVALID_THERMAL_ABORT, ResultState.INVALID_RESOURCE_ABORT} and self.abort is None:
            raise MicrobenchmarkAdmissionError("cancelled and aborted results require structured abort evidence")
        if self.state is ResultState.INVALID_INTERFERENCE and self.interference.state is not InterferenceState.CONTAMINATED:
            raise MicrobenchmarkIntegrityError("interference-invalid result must retain contamination evidence")


def aggregate_samples(samples: tuple[MeasurementSample, ...], metric: MetricSemantics) -> float:
    if not samples:
        raise MicrobenchmarkValidationError("cannot aggregate an empty sample sequence")
    values = tuple(item.value for item in samples)
    aggregation = metric.aggregation.value
    if aggregation == "MINIMUM":
        return min(values)
    if aggregation == "MAXIMUM":
        return max(values)
    if aggregation == "MEAN":
        return sum(values) / len(values)
    if aggregation == "MEDIAN":
        return float(statistics.median(values))
    if aggregation == "P95":
        ordered = sorted(values)
        return ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]
    return sum(values)


def create_result(
    protocol: ProtocolDescriptor,
    admission: ProtocolAdmission,
    metric: MetricSemantics,
    samples: tuple[MeasurementSample, ...],
    *,
    result_id: str,
    state: ResultState,
    correctness: CorrectnessEvidence,
    interference: InterferenceEvidence,
    measured_at_ms: int,
    uncertainty: float | None = None,
    abort: AbortEvidence | None = None,
    origin: EvidenceOrigin = EvidenceOrigin.SYNTHETIC_SEMANTIC_FIXTURE,
    external_measurement_ref: str | None = None,
) -> BenchmarkResult:
    protocol = ProtocolDescriptor.coerce(protocol, "protocol")
    admission = ProtocolAdmission.coerce(admission, "admission")
    metric = MetricSemantics.coerce(metric, "metric")
    if (
        (admission.protocol_id, admission.protocol_version) != (protocol.protocol_id, protocol.version)
        or admission.binding_digest != content_digest(protocol.binding)
        or admission.authorization_receipt_id != protocol.authorization_id
    ):
        raise MicrobenchmarkIntegrityError("admission is not bound to this protocol, provenance, and authorization")
    revalidated_admission = admit_protocol(protocol, admission.authorization_receipt, at_ms=admission.admitted_at_ms)
    if revalidated_admission != admission:
        raise MicrobenchmarkIntegrityError("protocol admission differs from its exact authorization receipt")
    if measured_at_ms < admission.admitted_at_ms or measured_at_ms >= admission.authorization_receipt.expires_at_ms:
        raise MicrobenchmarkAdmissionError("measurement must occur inside the active authorization interval")
    security = protocol.security_authorization_ref
    if protocol.security_authorization_required and (security is None or measured_at_ms >= security.expires_at_ms):
        raise MicrobenchmarkAdmissionError("measurement must remain inside the active security-authorization interval")
    if metric not in protocol.metrics:
        raise MicrobenchmarkAdmissionError("result metric is not declared by its admitted protocol")
    raw_samples = require_sequence(samples, "samples", maximum=min(DEFAULT_LIMITS.max_samples_per_result, protocol.budget.max_iterations))
    sample_tuple = tuple(MeasurementSample.coerce(item, "samples[]") for item in raw_samples)
    DEFAULT_LIMITS.require("max_iterations", len(sample_tuple))
    if len(sample_tuple) > protocol.budget.max_iterations:
        raise MicrobenchmarkLimitError("raw sample count exceeds the admitted protocol iteration budget")
    if sample_tuple:
        start_ns = min(item.observed_at_ms * 1_000_000 for item in sample_tuple)
        end_ns = max(item.observed_at_ms * 1_000_000 + item.elapsed_ns for item in sample_tuple)
        if (end_ns + 999_999) // 1_000_000 > measured_at_ms:
            raise MicrobenchmarkIntegrityError("result measurement time precedes completion of one of its raw samples")
        if end_ns - start_ns > protocol.budget.max_wall_ms * 1_000_000:
            raise MicrobenchmarkLimitError("sample timing exceeds the admitted protocol wall-clock budget")
    aggregate = aggregate_samples(sample_tuple, metric) if sample_tuple else None
    return BenchmarkResult(
        result_id, protocol.protocol_id, protocol.version, protocol.binding, metric, sample_tuple,
        aggregate, uncertainty, state, correctness, interference, abort, measured_at_ms,
        content_digest(sample_tuple), origin, external_measurement_ref,
    )


def validate_result(result: BenchmarkResult, protocol: ProtocolDescriptor) -> bool:
    result, protocol = BenchmarkResult.coerce(result, "result"), ProtocolDescriptor.coerce(protocol, "protocol")
    if (result.protocol_id, result.protocol_version, result.binding) != (protocol.protocol_id, protocol.version, protocol.binding):
        raise MicrobenchmarkIntegrityError("result provenance differs from its protocol")
    if result.metric not in protocol.metrics:
        raise MicrobenchmarkIntegrityError("result metric semantics are not declared by the protocol")
    return True
