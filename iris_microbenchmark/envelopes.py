"""Conservative multidimensional envelopes, bounded search, and consumer qualification."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M08Record, content_digest, require_sequence
from .enums import (
    CapabilityRegion, DerivationMethod, Directionality, FreshnessState, QualificationState,
    SearchOutcome, SearchStrategy, SustainabilityClass,
)
from .errors import MicrobenchmarkAdmissionError, MicrobenchmarkAuthorityError, MicrobenchmarkIntegrityError, MicrobenchmarkLimitError, MicrobenchmarkValidationError
from .evidence import BenchmarkResult
from .limits import DEFAULT_LIMITS
from .provenance import EvidencePurposeDescriptor, M07ProvenanceBinding
from .protocols import SafetyBudget
from .versions import require_digest, require_finite_number, require_identifier, require_nonnegative_int, require_unique, require_version

__all__ = [
    "CapabilityDimensionEvidence", "CapabilityEnvelope", "derive_envelope", "BoundedSearchPlan",
    "SearchAttempt", "validate_search_trace", "MemoryEnvelopeEvidence", "ConcurrencyEnvelopeEvidence",
    "SustainabilityEvidence", "CapabilityRequirement", "RequirementQualificationHandshake",
    "QualificationReport", "evaluate_requirements",
]


@dataclass(frozen=True)
class CapabilityDimensionEvidence(M08Record):
    dimension_id: str
    unit: str
    region: CapabilityRegion
    method: DerivationMethod
    result_ids: tuple[str, ...]
    observed_minimum: float | None
    observed_maximum: float | None
    conservative_limit: float | None
    safety_margin_fraction: float
    directionality: Directionality
    sustainability: SustainabilityClass
    unknown_reason: str | None

    def __post_init__(self) -> None:
        for field in ("dimension_id", "unit"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if not isinstance(self.region, CapabilityRegion) or not isinstance(self.method, DerivationMethod):
            raise MicrobenchmarkValidationError("dimension region and method must use closed M08 vocabularies")
        if not isinstance(self.directionality, Directionality) or not isinstance(self.sustainability, SustainabilityClass):
            raise MicrobenchmarkValidationError("dimension directionality and sustainability must use closed M08 vocabularies")
        object.__setattr__(self, "result_ids", tuple(sorted(require_unique(self.result_ids, "result_ids", maximum=10_000))))
        for field in ("observed_minimum", "observed_maximum", "conservative_limit"):
            value = getattr(self, field)
            if value is not None:
                number = require_finite_number(value, field)
                if number < 0:
                    raise MicrobenchmarkValidationError(f"{field} cannot be negative")
                object.__setattr__(self, field, number)
        if self.observed_minimum is not None and self.observed_maximum is not None and self.observed_minimum > self.observed_maximum:
            raise MicrobenchmarkIntegrityError("observed capability range minimum cannot exceed its maximum")
        margin = require_finite_number(self.safety_margin_fraction, "safety_margin_fraction")
        if not 0 <= margin < 1:
            raise MicrobenchmarkValidationError("safety margin must be within 0..1 and cannot be negative")
        object.__setattr__(self, "safety_margin_fraction", margin)
        if self.unknown_reason is not None:
            object.__setattr__(self, "unknown_reason", require_identifier(self.unknown_reason, "unknown_reason"))
        if self.region is CapabilityRegion.DEMONSTRATED:
            if self.method is not DerivationMethod.DIRECT_OBSERVATION or not self.result_ids or self.observed_maximum is None:
                raise MicrobenchmarkAdmissionError("demonstrated regions require direct observed evidence")
            if self.conservative_limit is not None:
                raise MicrobenchmarkIntegrityError("demonstrated values cannot be relabeled as conservative derivations")
        elif self.region is CapabilityRegion.CONSERVATIVE_BOUND:
            if self.method not in {DerivationMethod.INTERPOLATION, DerivationMethod.CONSERVATIVE_MARGIN}:
                raise MicrobenchmarkAdmissionError("conservative regions cannot use unsupported extrapolation")
            if len(self.result_ids) < 2 or self.conservative_limit is None or self.observed_maximum is None or margin <= 0:
                raise MicrobenchmarkAdmissionError("conservative regions require multiple sources, a bound, and a positive margin")
            if self.method is DerivationMethod.INTERPOLATION:
                if self.observed_minimum is None or self.observed_maximum is None or not self.observed_minimum <= self.conservative_limit <= self.observed_maximum:
                    raise MicrobenchmarkIntegrityError("interpolated bounds must remain inside the exact observed range")
            elif self.directionality is Directionality.HIGHER_IS_BETTER:
                if self.observed_minimum is None:
                    raise MicrobenchmarkAdmissionError("higher-is-better conservative margins require a measured lower bound")
                expected = self.observed_minimum * (1 - margin)
                if abs(expected - self.conservative_limit) > max(1e-9, abs(expected) * 1e-12):
                    raise MicrobenchmarkIntegrityError("higher-is-better conservative limit must reduce its measured lower bound by the declared margin")
            elif self.directionality is Directionality.LOWER_IS_BETTER:
                if self.observed_maximum is None:
                    raise MicrobenchmarkAdmissionError("lower-is-better conservative margins require a measured upper bound")
                expected = self.observed_maximum * (1 + margin)
                if abs(expected - self.conservative_limit) > max(1e-9, abs(expected) * 1e-12):
                    raise MicrobenchmarkIntegrityError("lower-is-better conservative limit must expand its measured upper bound by the declared margin")
            else:
                raise MicrobenchmarkAdmissionError("conservative margin derivation requires explicit directionality")
        elif self.region in {CapabilityRegion.UNKNOWN, CapabilityRegion.UNSUPPORTED_PROTOCOL, CapabilityRegion.INVALIDATED}:
            if self.conservative_limit is not None:
                raise MicrobenchmarkIntegrityError("unknown, unsupported, or invalidated regions cannot claim a usable limit")
            if not self.unknown_reason:
                raise MicrobenchmarkAdmissionError("non-positive capability regions require an explicit reason")


@dataclass(frozen=True)
class CapabilityEnvelope(M08Record):
    envelope_id: str
    schema_version: str
    binding: M07ProvenanceBinding
    dimensions: tuple[CapabilityDimensionEvidence, ...]
    source_result_ids: tuple[str, ...]
    derivation_algorithm: str
    derivation_version: str
    invalidation_dependency_ids: tuple[str, ...]
    evidence_purpose: EvidencePurposeDescriptor
    created_at_ms: int
    validity_state: FreshnessState
    synthetic_only: bool
    envelope_digest: str

    def __post_init__(self) -> None:
        for field in ("envelope_id", "derivation_algorithm"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "schema_version", require_version(self.schema_version, "schema_version"))
        object.__setattr__(self, "binding", M07ProvenanceBinding.coerce(self.binding, "binding"))
        dimensions = tuple(sorted((CapabilityDimensionEvidence.coerce(item, "dimensions[]") for item in require_sequence(self.dimensions, "dimensions", maximum=DEFAULT_LIMITS.max_context_dimensions)), key=lambda item: item.dimension_id))
        if not dimensions or len({item.dimension_id for item in dimensions}) != len(dimensions):
            raise MicrobenchmarkIntegrityError("envelope dimensions must be non-empty and unique")
        object.__setattr__(self, "dimensions", dimensions)
        object.__setattr__(self, "source_result_ids", tuple(sorted(require_unique(self.source_result_ids, "source_result_ids", maximum=DEFAULT_LIMITS.max_results))))
        object.__setattr__(self, "derivation_version", require_version(self.derivation_version, "derivation_version"))
        object.__setattr__(self, "invalidation_dependency_ids", tuple(sorted(require_unique(self.invalidation_dependency_ids, "invalidation_dependency_ids", maximum=10_000))))
        object.__setattr__(self, "evidence_purpose", EvidencePurposeDescriptor.coerce(self.evidence_purpose, "evidence_purpose"))
        object.__setattr__(self, "created_at_ms", require_nonnegative_int(self.created_at_ms, "created_at_ms"))
        if not isinstance(self.validity_state, FreshnessState):
            raise MicrobenchmarkValidationError("validity_state must be FreshnessState")
        if type(self.synthetic_only) is not bool:
            raise MicrobenchmarkValidationError("synthetic_only must be bool")
        object.__setattr__(self, "envelope_digest", require_digest(self.envelope_digest, "envelope_digest"))
        referenced = {result_id for dim in dimensions for result_id in dim.result_ids}
        if not referenced.issubset(set(self.source_result_ids)):
            raise MicrobenchmarkIntegrityError("envelope source list omits a dimension evidence reference")
        expected = content_digest({
            "schema_version": self.schema_version,
            "binding": self.binding,
            "dimensions": self.dimensions,
            "source_result_ids": self.source_result_ids,
            "derivation_algorithm": self.derivation_algorithm,
            "derivation_version": self.derivation_version,
            "invalidation_dependency_ids": self.invalidation_dependency_ids,
            "evidence_purpose": self.evidence_purpose,
            "created_at_ms": self.created_at_ms,
            "validity_state": self.validity_state,
            "synthetic_only": self.synthetic_only,
        })
        if self.envelope_digest != expected:
            raise MicrobenchmarkIntegrityError("envelope digest does not match its immutable evidence and derivation payload")


def derive_envelope(
    dimensions: tuple[CapabilityDimensionEvidence, ...],
    results: tuple[BenchmarkResult, ...],
    *,
    envelope_id: str,
    binding: M07ProvenanceBinding,
    derivation_algorithm: str,
    derivation_version: str,
    evidence_purpose: EvidencePurposeDescriptor,
    created_at_ms: int,
    invalidation_dependency_ids: tuple[str, ...] = (),
    synthetic_fixture_mode: bool = False,
) -> CapabilityEnvelope:
    binding = M07ProvenanceBinding.coerce(binding, "binding")
    evidence_purpose = EvidencePurposeDescriptor.coerce(evidence_purpose, "evidence_purpose")
    created_at_ms = require_nonnegative_int(created_at_ms, "created_at_ms")
    derivation_algorithm = require_identifier(derivation_algorithm, "derivation_algorithm")
    derivation_version = require_version(derivation_version, "derivation_version")
    invalidation_dependency_ids = tuple(sorted(require_unique(invalidation_dependency_ids, "invalidation_dependency_ids", maximum=10_000)))
    dimension_values = tuple(sorted((CapabilityDimensionEvidence.coerce(item, "dimensions[]") for item in require_sequence(dimensions, "dimensions", maximum=DEFAULT_LIMITS.max_context_dimensions)), key=lambda item: item.dimension_id))
    result_values = tuple(BenchmarkResult.coerce(item, "results[]") for item in require_sequence(results, "results", maximum=DEFAULT_LIMITS.max_results))
    if type(synthetic_fixture_mode) is not bool:
        raise MicrobenchmarkValidationError("synthetic_fixture_mode must be bool")
    by_id = {item.result_id: item for item in result_values}
    if len(by_id) != len(result_values):
        raise MicrobenchmarkIntegrityError("envelope derivation repeats a result identity")
    if len({item.dimension_id for item in dimension_values}) != len(dimension_values):
        raise MicrobenchmarkIntegrityError("envelope derivation repeats a capability dimension")
    source_ids = tuple(sorted({item for dimension in dimension_values for item in dimension.result_ids}))
    synthetic_only = bool(source_ids)
    for dimension in dimension_values:
        for result_id in dimension.result_ids:
            result = by_id.get(result_id)
            if result is None:
                raise MicrobenchmarkAdmissionError("envelope dimension references a missing benchmark result")
            if result.binding != binding:
                raise MicrobenchmarkIntegrityError("envelope cannot combine results from another hardware/runtime context")
            if dimension.region in {CapabilityRegion.DEMONSTRATED, CapabilityRegion.CONSERVATIVE_BOUND} and result.state.value != "VALID":
                raise MicrobenchmarkAdmissionError("invalid, aborted, or censored evidence cannot prove a positive capability region")
            if result.origin.value != "SYNTHETIC_SEMANTIC_FIXTURE":
                synthetic_only = False
    if synthetic_only and not synthetic_fixture_mode and source_ids:
        raise MicrobenchmarkAdmissionError("synthetic semantic fixtures require explicit synthetic_fixture_mode and remain non-physical")
    if not source_ids and any(item.region in {CapabilityRegion.DEMONSTRATED, CapabilityRegion.CONSERVATIVE_BOUND} for item in dimension_values):
        raise MicrobenchmarkAdmissionError("positive envelope regions require exact result lineage")
    semantic = {
        "schema_version": "iris-m08-envelope-v1",
        "binding": binding,
        "dimensions": dimension_values,
        "source_result_ids": source_ids,
        "derivation_algorithm": derivation_algorithm,
        "derivation_version": derivation_version,
        "invalidation_dependency_ids": invalidation_dependency_ids,
        "evidence_purpose": evidence_purpose,
        "created_at_ms": created_at_ms,
        "validity_state": FreshnessState.CURRENT,
        "synthetic_only": synthetic_only,
    }
    digest = content_digest(semantic)
    return CapabilityEnvelope(
        envelope_id, "iris-m08-envelope-v1", binding, dimension_values, source_ids, derivation_algorithm,
        derivation_version, invalidation_dependency_ids, evidence_purpose, created_at_ms,
        FreshnessState.CURRENT, synthetic_only, digest,
    )


@dataclass(frozen=True)
class BoundedSearchPlan(M08Record):
    search_id: str
    version: str
    dimension_id: str
    strategy: SearchStrategy
    maximum_attempts: int
    maximum_wall_ms: int
    maximum_allocation_bytes: int
    maximum_concurrency: int
    monotonicity_declared: bool
    inherited_budget: SafetyBudget

    def __post_init__(self) -> None:
        for field in ("search_id", "dimension_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "version", require_version(self.version))
        if not isinstance(self.strategy, SearchStrategy):
            raise MicrobenchmarkValidationError("strategy must be SearchStrategy")
        for field, limit in (("maximum_attempts", "max_search_attempts"), ("maximum_wall_ms", "max_protocol_duration_ms"), ("maximum_allocation_bytes", "max_device_allocation_bytes"), ("maximum_concurrency", "max_concurrency")):
            value = require_nonnegative_int(getattr(self, field), field)
            DEFAULT_LIMITS.require(limit, value)
            if value < 1:
                raise MicrobenchmarkValidationError(f"{field} must be positive")
            object.__setattr__(self, field, value)
        if type(self.monotonicity_declared) is not bool:
            raise MicrobenchmarkValidationError("monotonicity_declared must be bool")
        if self.strategy is SearchStrategy.BRACKETED_MONOTONIC and not self.monotonicity_declared:
            raise MicrobenchmarkAdmissionError("bracketed search requires protocol-qualified monotonicity")
        object.__setattr__(self, "inherited_budget", SafetyBudget.coerce(self.inherited_budget, "inherited_budget"))
        if self.maximum_wall_ms > self.inherited_budget.max_wall_ms or self.maximum_allocation_bytes > max(self.inherited_budget.max_host_allocation_bytes, self.inherited_budget.max_device_allocation_bytes) or self.maximum_concurrency > self.inherited_budget.max_concurrency:
            raise MicrobenchmarkAdmissionError("boundary search cannot exceed its inherited protocol safety budget")


@dataclass(frozen=True)
class SearchAttempt(M08Record):
    attempt_number: int
    started_at_ms: int
    elapsed_ms: int
    workload_size: int
    observed_allocation_bytes: int
    outcome: SearchOutcome
    result_id: str | None
    abort_ref: str | None

    def __post_init__(self) -> None:
        for field in ("attempt_number", "started_at_ms", "elapsed_ms", "workload_size", "observed_allocation_bytes"):
            object.__setattr__(self, field, require_nonnegative_int(getattr(self, field), field))
        if self.attempt_number < 1 or self.elapsed_ms < 1 or self.workload_size < 1:
            raise MicrobenchmarkValidationError("search attempt number, duration, and workload size must be positive")
        if not isinstance(self.outcome, SearchOutcome):
            raise MicrobenchmarkValidationError("outcome must be SearchOutcome")
        for field in ("result_id", "abort_ref"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_identifier(value, field))
        if self.outcome is SearchOutcome.ABORTED and self.abort_ref is None:
            raise MicrobenchmarkAdmissionError("aborted boundary attempt requires abort evidence")


def validate_search_trace(plan: BoundedSearchPlan, attempts: tuple[SearchAttempt, ...]) -> bool:
    plan = BoundedSearchPlan.coerce(plan, "plan")
    trace = tuple(SearchAttempt.coerce(item, "attempts[]") for item in attempts)
    if len(trace) > plan.maximum_attempts:
        raise MicrobenchmarkLimitError("bounded search trace exceeded its declared attempt ceiling")
    if tuple(item.attempt_number for item in trace) != tuple(range(1, len(trace) + 1)):
        raise MicrobenchmarkIntegrityError("bounded search attempts must be contiguous and ordered")
    if sum(item.elapsed_ms for item in trace) > plan.maximum_wall_ms:
        raise MicrobenchmarkLimitError("bounded search trace exceeded its wall-clock ceiling")
    if any(right.started_at_ms < left.started_at_ms for left, right in zip(trace, trace[1:])):
        raise MicrobenchmarkIntegrityError("bounded search trace timestamps must be ordered")
    if trace and trace[-1].started_at_ms + trace[-1].elapsed_ms - trace[0].started_at_ms > plan.maximum_wall_ms:
        raise MicrobenchmarkLimitError("bounded search trace timestamps exceed their wall-clock ceiling")
    if any(item.observed_allocation_bytes > plan.maximum_allocation_bytes for item in trace):
        raise MicrobenchmarkLimitError("bounded search trace exceeded its allocation ceiling")
    if any(item.outcome in {SearchOutcome.ABORTED, SearchOutcome.UNSUPPORTED} for item in trace[:-1]):
        raise MicrobenchmarkIntegrityError("aborted or unsupported search must stop immediately")
    return True


@dataclass(frozen=True)
class MemoryEnvelopeEvidence(M08Record):
    dimension_id: str
    requested_bytes: int
    admitted_bytes: int
    peak_observed_bytes: int
    failure_or_abort_bytes: int | None
    result_ids: tuple[str, ...]
    context_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "dimension_id", require_identifier(self.dimension_id, "dimension_id"))
        for field in ("requested_bytes", "admitted_bytes", "peak_observed_bytes"):
            object.__setattr__(self, field, require_nonnegative_int(getattr(self, field), field))
        if self.failure_or_abort_bytes is not None:
            object.__setattr__(self, "failure_or_abort_bytes", require_nonnegative_int(self.failure_or_abort_bytes, "failure_or_abort_bytes"))
            if self.failure_or_abort_bytes > self.requested_bytes:
                raise MicrobenchmarkIntegrityError("memory failure/abort evidence cannot exceed the declared request ceiling")
        if self.admitted_bytes > self.requested_bytes or self.peak_observed_bytes > self.requested_bytes:
            raise MicrobenchmarkIntegrityError("memory evidence cannot exceed the declared benchmark request")
        object.__setattr__(self, "result_ids", tuple(sorted(require_unique(self.result_ids, "result_ids", maximum=10_000))))
        object.__setattr__(self, "context_digest", require_digest(self.context_digest, "context_digest"))


@dataclass(frozen=True)
class ConcurrencyEnvelopeEvidence(M08Record):
    operation_family: str
    concurrency_degree: int
    per_lane_result_ids: tuple[str, ...]
    aggregate_result_id: str
    synchronization_semantics: str
    fairness_observation: str
    context_digest: str

    def __post_init__(self) -> None:
        for field in ("operation_family", "aggregate_result_id", "synchronization_semantics", "fairness_observation"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        degree = require_nonnegative_int(self.concurrency_degree, "concurrency_degree")
        DEFAULT_LIMITS.require("max_concurrency", degree)
        if degree < 1:
            raise MicrobenchmarkValidationError("concurrency_degree must be positive")
        object.__setattr__(self, "concurrency_degree", degree)
        object.__setattr__(self, "per_lane_result_ids", tuple(sorted(require_unique(self.per_lane_result_ids, "per_lane_result_ids", maximum=10_000))))
        if len(self.per_lane_result_ids) != degree:
            raise MicrobenchmarkIntegrityError("concurrency evidence must preserve one exact result per lane")
        if self.aggregate_result_id in self.per_lane_result_ids:
            raise MicrobenchmarkIntegrityError("aggregate concurrency evidence requires its own distinct result identity")
        object.__setattr__(self, "context_digest", require_digest(self.context_digest, "context_digest"))


@dataclass(frozen=True)
class SustainabilityEvidence(M08Record):
    classification: SustainabilityClass
    observed_duration_ms: int
    result_ids: tuple[str, ...]
    thermal_context_ref: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.classification, SustainabilityClass):
            raise MicrobenchmarkValidationError("classification must be SustainabilityClass")
        object.__setattr__(self, "observed_duration_ms", require_nonnegative_int(self.observed_duration_ms, "observed_duration_ms"))
        object.__setattr__(self, "result_ids", tuple(sorted(require_unique(self.result_ids, "result_ids", maximum=10_000))))
        if self.thermal_context_ref is not None:
            object.__setattr__(self, "thermal_context_ref", require_identifier(self.thermal_context_ref, "thermal_context_ref"))
        if self.classification is SustainabilityClass.SUSTAINED_OBSERVED and (self.observed_duration_ms < 60_000 or self.thermal_context_ref is None):
            raise MicrobenchmarkAdmissionError("sustained-observed evidence requires a declared long interval and thermal context")
        if self.classification is SustainabilityClass.SUSTAINED_OBSERVED and not self.result_ids:
            raise MicrobenchmarkAdmissionError("sustained-observed evidence requires exact result lineage")
        if self.classification is SustainabilityClass.BURST and self.observed_duration_ms > 5_000:
            raise MicrobenchmarkAdmissionError("burst evidence cannot claim a long observation interval")


@dataclass(frozen=True)
class CapabilityRequirement(M08Record):
    dimension_id: str
    unit: str
    minimum_value: float | None
    maximum_value: float | None
    required_freshness: FreshnessState
    purpose_use: str
    require_physical_evidence: bool

    def __post_init__(self) -> None:
        for field in ("dimension_id", "unit", "purpose_use"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        for field in ("minimum_value", "maximum_value"):
            value = getattr(self, field)
            if value is not None:
                number = require_finite_number(value, field)
                if number < 0:
                    raise MicrobenchmarkValidationError(f"{field} cannot be negative")
                object.__setattr__(self, field, number)
        if self.minimum_value is not None and self.maximum_value is not None and self.minimum_value > self.maximum_value:
            raise MicrobenchmarkValidationError("minimum requirement cannot exceed maximum")
        if not isinstance(self.required_freshness, FreshnessState):
            raise MicrobenchmarkValidationError("required_freshness must be FreshnessState")
        if self.required_freshness not in {FreshnessState.CURRENT, FreshnessState.AGING}:
            raise MicrobenchmarkAdmissionError("positive qualification cannot accept stale, invalidated, superseded, or unknown freshness")
        if type(self.require_physical_evidence) is not bool:
            raise MicrobenchmarkValidationError("require_physical_evidence must be bool")


@dataclass(frozen=True)
class RequirementQualificationHandshake(M08Record):
    handshake_id: str
    version: str
    consumer_namespace: str
    evidence_purpose: EvidencePurposeDescriptor
    requirements: tuple[CapabilityRequirement, ...]

    def __post_init__(self) -> None:
        for field in ("handshake_id", "consumer_namespace"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "version", require_version(self.version))
        object.__setattr__(self, "evidence_purpose", EvidencePurposeDescriptor.coerce(self.evidence_purpose, "evidence_purpose"))
        values = tuple(CapabilityRequirement.coerce(item, "requirements[]") for item in require_sequence(self.requirements, "requirements", maximum=DEFAULT_LIMITS.max_context_dimensions))
        if not values or len({item.dimension_id for item in values}) != len(values):
            raise MicrobenchmarkIntegrityError("qualification handshake requirements must be non-empty and unique")
        object.__setattr__(self, "requirements", values)


@dataclass(frozen=True)
class QualificationReport(M08Record):
    handshake_id: str
    envelope_id: str
    state: QualificationState
    satisfied_dimensions: tuple[str, ...]
    unsatisfied_dimensions: tuple[str, ...]
    unknown_dimensions: tuple[str, ...]
    incomparable_dimensions: tuple[str, ...]
    reasons: tuple[str, ...]
    policy_decision_ref: str | None

    def __post_init__(self) -> None:
        for field in ("handshake_id", "envelope_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if not isinstance(self.state, QualificationState):
            raise MicrobenchmarkValidationError("state must be QualificationState")
        for field in ("satisfied_dimensions", "unsatisfied_dimensions", "unknown_dimensions", "incomparable_dimensions", "reasons"):
            object.__setattr__(self, field, tuple(sorted(require_unique(getattr(self, field), field, maximum=10_000))))
        if self.policy_decision_ref is not None:
            object.__setattr__(self, "policy_decision_ref", require_identifier(self.policy_decision_ref, "policy_decision_ref"))
        if self.policy_decision_ref is not None:
            raise MicrobenchmarkAuthorityError("M08 reports evidence qualification; consumer policy decisions remain external")


def evaluate_requirements(
    envelope: CapabilityEnvelope,
    handshake: RequirementQualificationHandshake,
    *,
    allow_synthetic_fixture: bool = False,
) -> QualificationReport:
    envelope = CapabilityEnvelope.coerce(envelope, "envelope")
    handshake = RequirementQualificationHandshake.coerce(handshake, "handshake")
    if type(allow_synthetic_fixture) is not bool:
        raise MicrobenchmarkValidationError("allow_synthetic_fixture must be bool")
    reasons: list[str] = []
    if (handshake.evidence_purpose.purpose_id, handshake.evidence_purpose.version) != (envelope.evidence_purpose.purpose_id, envelope.evidence_purpose.version):
        return QualificationReport(handshake.handshake_id, envelope.envelope_id, QualificationState.INCOMPARABLE, (), (), (), tuple(item.dimension_id for item in handshake.requirements), ("evidence_purpose_mismatch",), None)
    try:
        handshake.evidence_purpose.qualifies(handshake.requirements[0].purpose_use)
        for requirement in handshake.requirements[1:]:
            handshake.evidence_purpose.qualifies(requirement.purpose_use)
    except MicrobenchmarkAdmissionError:
        return QualificationReport(handshake.handshake_id, envelope.envelope_id, QualificationState.INCOMPARABLE, (), (), (), tuple(item.dimension_id for item in handshake.requirements), ("evidence_purpose_not_qualified_for_consumer_use",), None)
    dimensions = {item.dimension_id: item for item in envelope.dimensions}
    satisfied: list[str] = []
    unsatisfied: list[str] = []
    unknown: list[str] = []
    incomparable: list[str] = []
    for requirement in handshake.requirements:
        dimension = dimensions.get(requirement.dimension_id)
        if dimension is None or dimension.region in {CapabilityRegion.UNKNOWN, CapabilityRegion.UNSUPPORTED_PROTOCOL, CapabilityRegion.INVALIDATED}:
            unknown.append(requirement.dimension_id)
            reasons.append(f"{requirement.dimension_id}:dimension_not_demonstrated")
            continue
        if dimension.unit != requirement.unit:
            incomparable.append(requirement.dimension_id)
            reasons.append(f"{requirement.dimension_id}:unit_mismatch")
            continue
        if requirement.require_physical_evidence and envelope.synthetic_only and not allow_synthetic_fixture:
            unsatisfied.append(requirement.dimension_id)
            reasons.append(f"{requirement.dimension_id}:synthetic_only")
            continue
        if dimension.region is CapabilityRegion.DEMONSTRATED:
            if dimension.directionality is Directionality.HIGHER_IS_BETTER:
                value = dimension.observed_minimum
            elif dimension.directionality is Directionality.LOWER_IS_BETTER:
                value = dimension.observed_maximum
            else:
                value = dimension.observed_maximum
        else:
            value = dimension.conservative_limit
        if value is None or (requirement.minimum_value is not None and value < requirement.minimum_value) or (requirement.maximum_value is not None and value > requirement.maximum_value):
            unsatisfied.append(requirement.dimension_id)
            reasons.append(f"{requirement.dimension_id}:outside_requirement")
            continue
        freshness_rank = {
            FreshnessState.CURRENT: 0,
            FreshnessState.AGING: 1,
            FreshnessState.STALE: 2,
            FreshnessState.SUPERSEDED: 3,
            FreshnessState.INVALIDATED: 4,
            FreshnessState.UNKNOWN_FRESHNESS: 5,
        }
        if envelope.validity_state not in {FreshnessState.CURRENT, FreshnessState.AGING} or freshness_rank[envelope.validity_state] > freshness_rank[requirement.required_freshness]:
            unknown.append(requirement.dimension_id)
            reasons.append(f"{requirement.dimension_id}:freshness_not_current")
            continue
        satisfied.append(requirement.dimension_id)
    if incomparable:
        state = QualificationState.INCOMPARABLE
    elif unknown:
        state = QualificationState.UNKNOWN
    elif unsatisfied:
        state = QualificationState.UNSATISFIED
    else:
        state = QualificationState.SATISFIED
    return QualificationReport(handshake.handshake_id, envelope.envelope_id, state, tuple(satisfied), tuple(unsatisfied), tuple(unknown), tuple(incomparable), tuple(reasons), None)
