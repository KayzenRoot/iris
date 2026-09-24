"""Immutable calibration, freshness, scoped invalidation and recalibration lineage."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import heapq

from .base import M08Record, content_digest, require_sequence
from .enums import CalibrationKind, FreshnessState, InvalidationReason, TimingSource
from .errors import MicrobenchmarkAdmissionError, MicrobenchmarkAuthorityError, MicrobenchmarkIntegrityError, MicrobenchmarkLimitError, MicrobenchmarkValidationError
from .evidence import BenchmarkResult
from .limits import DEFAULT_LIMITS
from .provenance import ExternalContextReference
from .versions import require_digest, require_finite_number, require_identifier, require_nonnegative_int, require_unique, require_version

__all__ = [
    "CalibrationArtifact", "CalibratedEvidence", "apply_calibration", "FreshnessPolicy",
    "FreshnessAssessment", "evaluate_freshness", "InvalidationEvent", "InvalidationDependency",
    "InvalidationGraph", "InvalidationPropagation", "append_invalidation", "propagate_invalidation",
    "TimingCalibrationDescriptor", "NormalizationPolicy", "NormalizedMetricEvidence", "normalize_metric",
]


@dataclass(frozen=True)
class CalibrationArtifact(M08Record):
    calibration_id: str
    version: str
    protocol_id: str
    protocol_version: str
    metric_id: str
    metric_version: str
    source_reference: str
    applicable_binding_digest: str
    kind: CalibrationKind
    method: str
    scale: float
    offset: float
    uncertainty: float
    valid_from_ms: int
    valid_until_ms: int
    created_at_ms: int
    provenance_ref: str

    def __post_init__(self) -> None:
        for field in ("calibration_id", "protocol_id", "metric_id", "source_reference", "method", "provenance_ref"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        for field in ("version", "protocol_version", "metric_version"):
            object.__setattr__(self, field, require_version(getattr(self, field), field))
        object.__setattr__(self, "applicable_binding_digest", require_digest(self.applicable_binding_digest, "applicable_binding_digest"))
        if not isinstance(self.kind, CalibrationKind):
            raise MicrobenchmarkValidationError("kind must be CalibrationKind")
        for field in ("scale", "offset", "uncertainty"):
            object.__setattr__(self, field, require_finite_number(getattr(self, field), field))
        if self.scale <= 0 or self.uncertainty < 0:
            raise MicrobenchmarkValidationError("calibration scale must be positive and uncertainty non-negative")
        for field in ("valid_from_ms", "valid_until_ms", "created_at_ms"):
            object.__setattr__(self, field, require_nonnegative_int(getattr(self, field), field))
        if self.valid_until_ms <= self.valid_from_ms:
            raise MicrobenchmarkValidationError("calibration validity interval must be ordered")
        if self.kind is CalibrationKind.QUALIFICATION and (self.scale != 1 or self.offset != 0):
            raise MicrobenchmarkIntegrityError("qualification cannot numerically change a measurement")
        if self.kind is CalibrationKind.REJECTION and (self.scale != 1 or self.offset != 0):
            raise MicrobenchmarkIntegrityError("rejection cannot emit corrected numeric values")


@dataclass(frozen=True)
class CalibratedEvidence(M08Record):
    derived_id: str
    source_result_id: str
    source_raw_digest: str
    calibration_id: str
    calibration_version: str
    state: CalibrationKind
    raw_value: float
    derived_value: float | None
    uncertainty: float
    created_at_ms: int
    lineage_digest: str

    def __post_init__(self) -> None:
        for field in ("derived_id", "source_result_id", "calibration_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "source_raw_digest", require_digest(self.source_raw_digest, "source_raw_digest"))
        object.__setattr__(self, "calibration_version", require_version(self.calibration_version))
        if not isinstance(self.state, CalibrationKind):
            raise MicrobenchmarkValidationError("state must be CalibrationKind")
        object.__setattr__(self, "raw_value", require_finite_number(self.raw_value, "raw_value"))
        if self.derived_value is not None:
            object.__setattr__(self, "derived_value", require_finite_number(self.derived_value, "derived_value"))
        object.__setattr__(self, "uncertainty", require_finite_number(self.uncertainty, "uncertainty"))
        if self.uncertainty < 0:
            raise MicrobenchmarkValidationError("derived uncertainty cannot be negative")
        object.__setattr__(self, "created_at_ms", require_nonnegative_int(self.created_at_ms, "created_at_ms"))
        object.__setattr__(self, "lineage_digest", require_digest(self.lineage_digest, "lineage_digest"))
        if self.state is CalibrationKind.REJECTION and self.derived_value is not None:
            raise MicrobenchmarkIntegrityError("rejected evidence cannot carry a usable derived number")
        if self.state is not CalibrationKind.REJECTION and self.derived_value is None:
            raise MicrobenchmarkIntegrityError("qualified or corrected evidence must carry a derived number")
        expected = content_digest({
            "derived_id": self.derived_id,
            "source_result_id": self.source_result_id,
            "source_raw_digest": self.source_raw_digest,
            "calibration_id": self.calibration_id,
            "calibration_version": self.calibration_version,
            "kind": self.state,
            "raw_value": self.raw_value,
            "derived_value": self.derived_value,
            "uncertainty": self.uncertainty,
            "created_at_ms": self.created_at_ms,
        })
        if self.lineage_digest != expected:
            raise MicrobenchmarkIntegrityError("calibrated evidence lineage digest does not match its raw and derived values")


def apply_calibration(result: BenchmarkResult, calibration: CalibrationArtifact, *, derived_id: str, at_ms: int) -> CalibratedEvidence:
    result = BenchmarkResult.coerce(result, "result")
    calibration = CalibrationArtifact.coerce(calibration, "calibration")
    at_ms = require_nonnegative_int(at_ms, "at_ms")
    if result.state.value != "VALID" or result.aggregate_value is None:
        raise MicrobenchmarkAdmissionError("calibration requires intact valid raw benchmark evidence")
    if (result.protocol_id, result.protocol_version, result.metric.metric_id, result.metric.version) != (
        calibration.protocol_id, calibration.protocol_version, calibration.metric_id, calibration.metric_version,
    ):
        raise MicrobenchmarkAdmissionError("calibration applicability does not match exact protocol and metric semantics")
    if content_digest(result.binding) != calibration.applicable_binding_digest:
        raise MicrobenchmarkAdmissionError("calibration is bound to another hardware/runtime context")
    if not calibration.valid_from_ms <= at_ms < calibration.valid_until_ms:
        raise MicrobenchmarkAdmissionError("calibration is outside its declared validity interval")
    value = None if calibration.kind is CalibrationKind.REJECTION else result.aggregate_value * calibration.scale + calibration.offset
    uncertainty = (result.uncertainty or 0.0) * calibration.scale + calibration.uncertainty
    material = {
        "derived_id": derived_id,
        "source_result_id": result.result_id,
        "source_raw_digest": result.raw_digest,
        "calibration_id": calibration.calibration_id,
        "calibration_version": calibration.version,
        "kind": calibration.kind,
        "raw_value": result.aggregate_value,
        "derived_value": value,
        "uncertainty": uncertainty,
        "created_at_ms": at_ms,
    }
    return CalibratedEvidence(
        derived_id, result.result_id, result.raw_digest, calibration.calibration_id,
        calibration.version, calibration.kind, result.aggregate_value, value, uncertainty,
        at_ms, content_digest(material),
    )


@dataclass(frozen=True)
class FreshnessPolicy(M08Record):
    policy_id: str
    version: str
    aging_after_ms: int
    stale_after_ms: int
    relevant_materiality_axes: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy_id", require_identifier(self.policy_id, "policy_id"))
        object.__setattr__(self, "version", require_version(self.version))
        object.__setattr__(self, "aging_after_ms", require_nonnegative_int(self.aging_after_ms, "aging_after_ms"))
        object.__setattr__(self, "stale_after_ms", require_nonnegative_int(self.stale_after_ms, "stale_after_ms"))
        if self.aging_after_ms < 1 or self.stale_after_ms <= self.aging_after_ms:
            raise MicrobenchmarkValidationError("freshness policy requires ordered positive aging/stale thresholds")
        object.__setattr__(self, "relevant_materiality_axes", tuple(sorted(require_unique(self.relevant_materiality_axes, "relevant_materiality_axes", maximum=512))))


@dataclass(frozen=True)
class FreshnessAssessment(M08Record):
    subject_ref: str
    state: FreshnessState
    evaluated_at_ms: int
    age_ms: int
    reason_refs: tuple[str, ...]
    superseding_ref: str | None
    required_current_satisfied: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject_ref", require_identifier(self.subject_ref, "subject_ref"))
        if not isinstance(self.state, FreshnessState):
            raise MicrobenchmarkValidationError("state must be FreshnessState")
        object.__setattr__(self, "evaluated_at_ms", require_nonnegative_int(self.evaluated_at_ms, "evaluated_at_ms"))
        object.__setattr__(self, "age_ms", require_nonnegative_int(self.age_ms, "age_ms"))
        object.__setattr__(self, "reason_refs", tuple(sorted(require_unique(self.reason_refs, "reason_refs", maximum=1_024))))
        if self.superseding_ref is not None:
            object.__setattr__(self, "superseding_ref", require_identifier(self.superseding_ref, "superseding_ref"))
        if type(self.required_current_satisfied) is not bool:
            raise MicrobenchmarkValidationError("required_current_satisfied must be bool")
        if self.required_current_satisfied != (self.state is FreshnessState.CURRENT):
            raise MicrobenchmarkIntegrityError("only CURRENT evidence can satisfy mandatory-current freshness")


def evaluate_freshness(
    subject_ref: str,
    *,
    created_at_ms: int,
    evaluated_at_ms: int,
    policy: FreshnessPolicy,
    relevant_change_refs: tuple[str, ...] = (),
    invalidation_refs: tuple[str, ...] = (),
    superseding_ref: str | None = None,
) -> FreshnessAssessment:
    policy = FreshnessPolicy.coerce(policy, "policy")
    created_at_ms = require_nonnegative_int(created_at_ms, "created_at_ms")
    evaluated_at_ms = require_nonnegative_int(evaluated_at_ms, "evaluated_at_ms")
    if evaluated_at_ms < created_at_ms:
        raise MicrobenchmarkValidationError("freshness cannot be evaluated before evidence creation")
    age = evaluated_at_ms - created_at_ms
    reasons = list(relevant_change_refs) + list(invalidation_refs)
    if invalidation_refs:
        state = FreshnessState.INVALIDATED
    elif superseding_ref is not None:
        state = FreshnessState.SUPERSEDED
        reasons.append("superseded_by_newer_evidence")
    elif relevant_change_refs:
        state = FreshnessState.STALE
    elif age >= policy.stale_after_ms:
        state = FreshnessState.STALE
        reasons.append("age_exceeded_stale_threshold")
    elif age >= policy.aging_after_ms:
        state = FreshnessState.AGING
        reasons.append("age_exceeded_aging_threshold")
    else:
        state = FreshnessState.CURRENT
    return FreshnessAssessment(subject_ref, state, evaluated_at_ms, age, tuple(sorted(set(reasons))), superseding_ref, state is FreshnessState.CURRENT)


@dataclass(frozen=True)
class InvalidationEvent(M08Record):
    event_id: str
    source_ref: str
    reason: InvalidationReason
    scope_refs: tuple[str, ...]
    created_at_ms: int
    attributable_actor_ref: str
    external_context_ref: ExternalContextReference | None
    administrative_authorization_ref: str | None
    global_scope_proven: bool = False
    global_scope_evidence_ref: str | None = None

    def __post_init__(self) -> None:
        for field in ("event_id", "source_ref", "attributable_actor_ref"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if not isinstance(self.reason, InvalidationReason):
            raise MicrobenchmarkValidationError("reason must be InvalidationReason")
        object.__setattr__(self, "scope_refs", tuple(sorted(require_unique(self.scope_refs, "scope_refs", maximum=10_000))))
        object.__setattr__(self, "created_at_ms", require_nonnegative_int(self.created_at_ms, "created_at_ms"))
        if self.external_context_ref is not None:
            object.__setattr__(self, "external_context_ref", ExternalContextReference.coerce(self.external_context_ref, "external_context_ref"))
        if self.administrative_authorization_ref is not None:
            object.__setattr__(self, "administrative_authorization_ref", require_identifier(self.administrative_authorization_ref, "administrative_authorization_ref"))
        if type(self.global_scope_proven) is not bool:
            raise MicrobenchmarkValidationError("global_scope_proven must be bool")
        if self.global_scope_evidence_ref is not None:
            object.__setattr__(self, "global_scope_evidence_ref", require_identifier(self.global_scope_evidence_ref, "global_scope_evidence_ref"))
        if self.global_scope_proven != (self.global_scope_evidence_ref is not None):
            raise MicrobenchmarkAdmissionError("global invalidation scope requires its explicit evidence reference")
        if not self.scope_refs and not self.global_scope_proven:
            raise MicrobenchmarkAdmissionError("empty invalidation scope requires proof of global applicability")
        if self.reason is InvalidationReason.GOVERNED_ADMINISTRATIVE and self.administrative_authorization_ref is None:
            raise MicrobenchmarkAdmissionError("administrative invalidation requires an explicit governed authorization reference")
        if self.reason is InvalidationReason.MATERIAL_CONTEXT_CHANGE and self.external_context_ref is None and not self.scope_refs:
            raise MicrobenchmarkAdmissionError("context invalidation must bind an external ref or explicit material scope")


@dataclass(frozen=True)
class InvalidationDependency(M08Record):
    source_ref: str
    dependent_ref: str
    dependency_version: str
    dimension_scope: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in ("source_ref", "dependent_ref"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if self.source_ref == self.dependent_ref:
            raise MicrobenchmarkIntegrityError("invalidation graph cannot contain a self-dependency")
        object.__setattr__(self, "dependency_version", require_version(self.dependency_version))
        object.__setattr__(self, "dimension_scope", tuple(sorted(require_unique(self.dimension_scope, "dimension_scope", maximum=512))))


@dataclass(frozen=True)
class InvalidationGraph(M08Record):
    graph_id: str
    version: str
    nodes: tuple[str, ...]
    dependencies: tuple[InvalidationDependency, ...]
    events: tuple[InvalidationEvent, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        object.__setattr__(self, "version", require_version(self.version))
        nodes = tuple(sorted(require_unique(self.nodes, "nodes", maximum=DEFAULT_LIMITS.max_invalidation_nodes)))
        object.__setattr__(self, "nodes", nodes)
        raw_dependencies = require_sequence(self.dependencies, "dependencies", maximum=DEFAULT_LIMITS.max_invalidation_edges)
        dependencies = tuple(InvalidationDependency.coerce(item, "dependencies[]") for item in raw_dependencies)
        if len({(item.source_ref, item.dependent_ref) for item in dependencies}) != len(dependencies):
            raise MicrobenchmarkIntegrityError("invalidation graph repeats a dependency edge")
        object.__setattr__(self, "dependencies", dependencies)
        raw_events = require_sequence(self.events, "events", maximum=DEFAULT_LIMITS.max_invalidation_events)
        events = tuple(InvalidationEvent.coerce(item, "events[]") for item in raw_events)
        if len({item.event_id for item in events}) != len(events):
            raise MicrobenchmarkIntegrityError("invalidation graph repeats an event identity")
        object.__setattr__(self, "events", events)
        vertices = set(nodes)
        if any(item.source_ref not in vertices or item.dependent_ref not in vertices for item in dependencies):
            raise MicrobenchmarkIntegrityError("invalidation edge references a node outside the graph")
        _require_acyclic(vertices, dependencies)


def _require_acyclic(nodes: set[str], edges: tuple[InvalidationDependency, ...]) -> None:
    successors: dict[str, list[str]] = {node: [] for node in nodes}
    indegree = {node: 0 for node in nodes}
    for edge in edges:
        successors[edge.source_ref].append(edge.dependent_ref)
        indegree[edge.dependent_ref] += 1
    ready = [node for node, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    processed = 0
    while ready:
        source = heapq.heappop(ready)
        processed += 1
        for target in sorted(successors[source]):
            indegree[target] -= 1
            if indegree[target] == 0:
                heapq.heappush(ready, target)
    if processed != len(nodes):
        raise MicrobenchmarkIntegrityError("invalidation dependency graph must be acyclic")


@dataclass(frozen=True)
class InvalidationPropagation(M08Record):
    event_id: str
    graph_version: str
    invalidated_refs: tuple[tuple[str, tuple[str, ...]], ...]
    propagation_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", require_identifier(self.event_id, "event_id"))
        object.__setattr__(self, "graph_version", require_version(self.graph_version, "graph_version"))
        entries = tuple(sorted(
            (require_identifier(key, "invalidated_ref"), tuple(sorted(require_unique(scope, "dimension_scope", maximum=512))))
            for key, scope in self.invalidated_refs
        ))
        if not entries or len({key for key, _ in entries}) != len(entries):
            raise MicrobenchmarkIntegrityError("invalidation propagation must have unique affected references")
        object.__setattr__(self, "invalidated_refs", entries)
        object.__setattr__(self, "propagation_digest", require_digest(self.propagation_digest, "propagation_digest"))
        expected = content_digest({"event_id": self.event_id, "affected": self.invalidated_refs, "graph_version": self.graph_version})
        if self.propagation_digest != expected:
            raise MicrobenchmarkIntegrityError("invalidation propagation digest does not match its deterministic graph result")


def append_invalidation(graph: InvalidationGraph, event: InvalidationEvent) -> InvalidationGraph:
    graph, event = InvalidationGraph.coerce(graph, "graph"), InvalidationEvent.coerce(event, "event")
    if len(graph.events) >= DEFAULT_LIMITS.max_invalidation_events:
        raise MicrobenchmarkLimitError("invalidation event history reached its bounded capacity")
    if event.event_id in {item.event_id for item in graph.events}:
        raise MicrobenchmarkIntegrityError("invalidation history is append-only and event IDs cannot be reused")
    if event.source_ref not in graph.nodes:
        raise MicrobenchmarkAdmissionError("invalidation event source is not registered in the dependency graph")
    return InvalidationGraph(graph.graph_id, graph.version, graph.nodes, graph.dependencies, graph.events + (event,))


def propagate_invalidation(graph: InvalidationGraph, event: InvalidationEvent) -> InvalidationPropagation:
    graph, event = InvalidationGraph.coerce(graph, "graph"), InvalidationEvent.coerce(event, "event")
    stored = next((item for item in graph.events if item.event_id == event.event_id), None)
    if stored is None:
        raise MicrobenchmarkAdmissionError("invalidation must be appended to the immutable graph before propagation")
    if stored != event:
        raise MicrobenchmarkIntegrityError("invalidation propagation must use the exact event appended to the graph")
    by_source: dict[str, list[InvalidationDependency]] = {}
    for edge in graph.dependencies:
        by_source.setdefault(edge.source_ref, []).append(edge)
    affected: dict[str, set[str]] = {event.source_ref: set(event.scope_refs)}
    queue = deque([event.source_ref])
    while queue:
        source = queue.popleft()
        for edge in sorted(by_source.get(source, ()), key=lambda item: item.dependent_ref):
            inherited = affected[source]
            if edge.dimension_scope:
                scope = inherited & set(edge.dimension_scope) if inherited else set(edge.dimension_scope)
                if not scope:
                    continue
            else:
                scope = set(inherited)
            old = affected.get(edge.dependent_ref)
            merged = scope if old is None else old | scope
            if old != merged:
                affected[edge.dependent_ref] = merged
                queue.append(edge.dependent_ref)
    if not affected:
        raise MicrobenchmarkIntegrityError("invalidation event produced no source scope")
    payload = tuple(sorted((key, tuple(sorted(value))) for key, value in affected.items()))
    return InvalidationPropagation(event.event_id, graph.version, payload, content_digest({"event_id": event.event_id, "affected": payload, "graph_version": graph.version}))


@dataclass(frozen=True)
class TimingCalibrationDescriptor(M08Record):
    timing_source_id: str
    version: str
    source: TimingSource
    resolution_ns: int
    monotonic: bool
    synchronization_method: str
    host_device_clock_relation: str
    calibrated_at_ms: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "timing_source_id", require_identifier(self.timing_source_id, "timing_source_id"))
        object.__setattr__(self, "version", require_version(self.version))
        if not isinstance(self.source, TimingSource):
            raise MicrobenchmarkValidationError("source must be TimingSource")
        object.__setattr__(self, "resolution_ns", require_nonnegative_int(self.resolution_ns, "resolution_ns"))
        if self.resolution_ns < 1:
            raise MicrobenchmarkValidationError("timing resolution must be positive")
        if type(self.monotonic) is not bool:
            raise MicrobenchmarkValidationError("monotonic must be bool")
        for field in ("synchronization_method", "host_device_clock_relation"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "calibrated_at_ms", require_nonnegative_int(self.calibrated_at_ms, "calibrated_at_ms"))
        if self.source is TimingSource.UNKNOWN or not self.monotonic:
            raise MicrobenchmarkAdmissionError("unqualified or non-monotonic timing source cannot qualify duration measurements")


@dataclass(frozen=True)
class NormalizationPolicy(M08Record):
    policy_id: str
    version: str
    protocol_id: str
    protocol_version: str
    metric_id: str
    metric_version: str
    stable_reference_semantics: str
    reference_value: float
    source_reference_value: float
    uncertainty: float

    def __post_init__(self) -> None:
        for field in ("policy_id", "protocol_id", "metric_id", "stable_reference_semantics"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        for field in ("version", "protocol_version", "metric_version"):
            object.__setattr__(self, field, require_version(getattr(self, field), field))
        for field in ("reference_value", "source_reference_value", "uncertainty"):
            object.__setattr__(self, field, require_finite_number(getattr(self, field), field))
        if self.reference_value <= 0 or self.source_reference_value <= 0 or self.uncertainty < 0:
            raise MicrobenchmarkValidationError("normalization needs positive reference values and non-negative uncertainty")


@dataclass(frozen=True)
class NormalizedMetricEvidence(M08Record):
    normalized_id: str
    source_result_id: str
    source_raw_digest: str
    policy_id: str
    policy: NormalizationPolicy
    metric_id: str
    machine_binding_digest: str
    raw_value: float
    raw_uncertainty: float
    normalized_value: float
    uncertainty: float
    universal_hardware_score: bool = False

    def __post_init__(self) -> None:
        for field in ("normalized_id", "source_result_id", "policy_id", "metric_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "policy", NormalizationPolicy.coerce(self.policy, "policy"))
        if self.policy.policy_id != self.policy_id or self.policy.metric_id != self.metric_id:
            raise MicrobenchmarkIntegrityError("normalized evidence must bind the exact normalization policy and metric")
        for field in ("source_raw_digest", "machine_binding_digest"):
            object.__setattr__(self, field, require_digest(getattr(self, field), field))
        for field in ("raw_value", "raw_uncertainty", "normalized_value", "uncertainty"):
            object.__setattr__(self, field, require_finite_number(getattr(self, field), field))
        if self.raw_uncertainty < 0 or self.uncertainty < 0:
            raise MicrobenchmarkValidationError("normalized uncertainty cannot be negative")
        expected_value = self.raw_value * self.policy.reference_value / self.policy.source_reference_value
        expected_uncertainty = self.raw_uncertainty * self.policy.reference_value / self.policy.source_reference_value + self.policy.uncertainty
        if abs(expected_value - self.normalized_value) > max(1e-12, abs(expected_value) * 1e-12) or abs(expected_uncertainty - self.uncertainty) > max(1e-12, abs(expected_uncertainty) * 1e-12):
            raise MicrobenchmarkIntegrityError("normalized metric does not match its versioned policy transformation")
        if self.universal_hardware_score is not False:
            raise MicrobenchmarkAuthorityError("normalization cannot create a universal hardware score")


def normalize_metric(result: BenchmarkResult, policy: NormalizationPolicy, *, normalized_id: str) -> NormalizedMetricEvidence:
    result = BenchmarkResult.coerce(result, "result")
    policy = NormalizationPolicy.coerce(policy, "policy")
    if result.state.value != "VALID" or result.aggregate_value is None:
        raise MicrobenchmarkAdmissionError("normalization requires valid source measurement")
    if (result.protocol_id, result.protocol_version, result.metric.metric_id, result.metric.version) != (
        policy.protocol_id, policy.protocol_version, policy.metric_id, policy.metric_version,
    ):
        raise MicrobenchmarkAdmissionError("normalization policy does not match exact protocol and metric")
    value = result.aggregate_value * policy.reference_value / policy.source_reference_value
    return NormalizedMetricEvidence(
        normalized_id, result.result_id, result.raw_digest, policy.policy_id, policy,
        result.metric.metric_id, content_digest(result.binding), result.aggregate_value,
        result.uncertainty or 0.0, value,
        (result.uncertainty or 0.0) * policy.reference_value / policy.source_reference_value + policy.uncertainty,
    )
