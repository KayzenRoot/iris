"""Bounded dynamic telemetry, evidence derivation and non-invasive sampling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import M07Record
from .enums import FreshnessClass, MemoryKind, MetricSemantics, ObservationState, PressureState, ProbePermissionClass
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError, HardwareGenomeLimitError, HardwareGenomeValidationError
from .evidence import DiscoveryObservation, ProbeEvidenceRef
from .limits import DEFAULT_LIMITS, HardwareGenomeLimits
from .registry import SemanticKeyRegistry
from .subjects import HardwareSubjectRef, RuntimeSubjectRef
from .versions import require_finite_number, require_identifier, require_nonnegative_int, require_version

__all__ = [
    "TelemetrySample", "TelemetryWindow", "SamplingWindowPolicy", "validate_sampling_window",
    "DerivationRule", "DerivedMetric", "derive_counter_rate", "validate_derived_metric", "MemoryPressureFact",
    "ThermalCausalityEvidence", "MemoryCapacityFact", "require_telemetry_fresh", "validate_sample_registry",
]


@dataclass(frozen=True)
class TelemetrySample(M07Record):
    sample_id: str
    metric_key: str
    semantics: MetricSemantics
    value: Any
    unit: str | None
    subject: HardwareSubjectRef | None
    runtime: RuntimeSubjectRef | None
    source_id: str
    source_version: str
    sequence: int
    captured_at_ms: int
    window_ms: int
    expires_at_ms: int
    state: ObservationState
    evidence: ProbeEvidenceRef | None
    sensor_id: str | None = None
    visibility_scope: str = "host"

    def __post_init__(self) -> None:
        for field in ("sample_id", "metric_key", "source_id", "visibility_scope"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "source_version", require_version(self.source_version, "source_version"))
        if type(self.semantics) is not MetricSemantics or type(self.state) is not ObservationState:
            raise HardwareGenomeValidationError("telemetry semantics and state must use closed M07 vocabularies")
        for field in ("sequence", "captured_at_ms", "window_ms", "expires_at_ms"):
            object.__setattr__(self, field, require_nonnegative_int(getattr(self, field), field))
        if self.expires_at_ms < self.captured_at_ms:
            raise HardwareGenomeValidationError("telemetry expiry cannot precede capture")
        if self.subject is None and self.runtime is None:
            raise HardwareGenomeValidationError("telemetry must bind an exact hardware or runtime subject")
        if self.subject is not None:
            object.__setattr__(self, "subject", HardwareSubjectRef.coerce(self.subject, "subject"))
        if self.runtime is not None:
            object.__setattr__(self, "runtime", RuntimeSubjectRef.coerce(self.runtime, "runtime"))
        if self.unit is not None:
            object.__setattr__(self, "unit", require_identifier(self.unit, "unit"))
        if self.sensor_id is not None:
            object.__setattr__(self, "sensor_id", require_identifier(self.sensor_id, "sensor_id"))
        if self.metric_key.endswith("temperature") and self.state is ObservationState.OBSERVED and self.sensor_id is None:
            raise HardwareGenomeAdmissionError("temperature samples require an exact semantic sensor identity")
        if self.evidence is not None:
            object.__setattr__(self, "evidence", ProbeEvidenceRef.coerce(self.evidence, "evidence"))
            if self.evidence.observed_at_ms != self.captured_at_ms or self.evidence.visibility_scope != self.visibility_scope:
                raise HardwareGenomeIntegrityError("telemetry time and scope must match its evidence")
            if self.subject is not None and self.evidence.subject_id != self.subject.subject_id:
                raise HardwareGenomeIntegrityError("telemetry evidence belongs to a different hardware subject")
            if self.runtime is not None and self.evidence.runtime_id != self.runtime.runtime_id:
                raise HardwareGenomeIntegrityError("telemetry evidence belongs to a different runtime")
            if self.subject is None and self.evidence.subject_id is not None:
                raise HardwareGenomeIntegrityError("telemetry evidence has an undeclared hardware subject binding")
            if self.runtime is None and self.evidence.runtime_id is not None:
                raise HardwareGenomeIntegrityError("telemetry evidence has an undeclared runtime binding")
        if self.state is ObservationState.OBSERVED:
            if self.value is None or self.unit is None or self.evidence is None:
                raise HardwareGenomeAdmissionError("positive telemetry requires value, unit and evidence")
            if self.evidence.payload_bytes <= 0:
                raise HardwareGenomeAdmissionError("positive telemetry requires a non-empty evidence payload")
            if self.semantics is MetricSemantics.EVENT_FLAG:
                if type(self.value) is not bool:
                    raise HardwareGenomeValidationError("event flags must be exact bool values")
            elif self.semantics in {MetricSemantics.CUMULATIVE_COUNTER, MetricSemantics.MONOTONIC_COUNTER}:
                if isinstance(self.value, bool) or not isinstance(self.value, int) or self.value < 0:
                    raise HardwareGenomeValidationError("counter values must be non-negative integers")
            else:
                value = require_finite_number(self.value, "telemetry value")
                if value < 0 and self.metric_key.endswith(("temperature", "delta")) is False:
                    raise HardwareGenomeValidationError("negative telemetry requires a metric whose semantics permit it")
                if self.semantics is MetricSemantics.BOUNDED_PERCENTAGE and not 0 <= value <= 100:
                    raise HardwareGenomeValidationError("percentage telemetry must be within 0..100")
            if self.window_ms == 0 and self.semantics in {MetricSemantics.CUMULATIVE_COUNTER, MetricSemantics.MONOTONIC_COUNTER}:
                raise HardwareGenomeValidationError("counter samples require an explicit observation interval")
        elif self.value is not None:
            raise HardwareGenomeAdmissionError("non-positive telemetry cannot carry a measured value")
        if self.semantics is MetricSemantics.REPORTED_LIMIT and self.metric_key.endswith(("used", "available", "pressure")):
            raise HardwareGenomeValidationError("reported limits cannot masquerade as current consumption or pressure")
        if self.semantics is MetricSemantics.CONFIGURED_LIMIT and self.metric_key.endswith(("used", "consumed", "temperature")):
            raise HardwareGenomeValidationError("configured limits cannot masquerade as measured consumption")


@dataclass(frozen=True)
class TelemetryWindow(M07Record):
    window_id: str
    subject_id: str
    runtime_id: str
    started_at_ms: int
    ended_at_ms: int
    samples: tuple[TelemetrySample, ...]
    complete: bool
    remaining_frontier: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in ("window_id", "subject_id", "runtime_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        for field in ("started_at_ms", "ended_at_ms"):
            object.__setattr__(self, field, require_nonnegative_int(getattr(self, field), field))
        if self.ended_at_ms < self.started_at_ms:
            raise HardwareGenomeValidationError("telemetry window end cannot precede start")
        samples = tuple(TelemetrySample.coerce(item, "samples[]") for item in self.samples)
        if len({item.sample_id for item in samples}) != len(samples):
            raise HardwareGenomeValidationError("telemetry sample ids must be unique within a window")
        if any(item.subject is None or item.subject.subject_id != self.subject_id or item.runtime is None or item.runtime.runtime_id != self.runtime_id for item in samples):
            raise HardwareGenomeIntegrityError("telemetry windows cannot mix hardware or runtime scopes")
        if any(not self.started_at_ms <= item.captured_at_ms <= self.ended_at_ms for item in samples):
            raise HardwareGenomeIntegrityError("telemetry sample time falls outside its declared window")
        object.__setattr__(self, "samples", tuple(sorted(samples, key=lambda item: (item.captured_at_ms, item.sequence, item.sample_id))))
        if type(self.complete) is not bool:
            raise HardwareGenomeValidationError("window complete must be bool")
        frontier = tuple(sorted(set(require_identifier(item, "remaining_frontier[]") for item in self.remaining_frontier)))
        if self.complete and frontier:
            raise HardwareGenomeIntegrityError("a complete telemetry window cannot contain an unfinished frontier")
        if not self.complete and not frontier:
            raise HardwareGenomeAdmissionError("an incomplete telemetry window must preserve its frontier")
        object.__setattr__(self, "remaining_frontier", frontier)


@dataclass(frozen=True)
class SamplingWindowPolicy(M07Record):
    policy_id: str
    version: str
    minimum_interval_ms: int
    maximum_samples: int
    maximum_window_ms: int
    maximum_timeout_ms: int
    permission_class: ProbePermissionClass
    permits_privilege_escalation: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy_id", require_identifier(self.policy_id, "policy_id"))
        object.__setattr__(self, "version", require_version(self.version, "version"))
        for field in ("minimum_interval_ms", "maximum_samples", "maximum_window_ms", "maximum_timeout_ms"):
            object.__setattr__(self, field, require_nonnegative_int(getattr(self, field), field))
            if getattr(self, field) == 0:
                raise HardwareGenomeValidationError(f"{field} must be positive")
        if type(self.permits_privilege_escalation) is not bool:
            raise HardwareGenomeValidationError("privilege escalation flag must be bool")
        if self.permits_privilege_escalation:
            raise HardwareGenomeAdmissionError("M07 sampling cannot escalate privilege")
        if type(self.permission_class) is not ProbePermissionClass:
            raise HardwareGenomeValidationError("sampling policy permission class must use the closed probe permission vocabulary")
        if self.minimum_interval_ms < 10:
            raise HardwareGenomeAdmissionError("sampling minimum interval cannot permit a busy-loop rate")


def validate_sampling_window(
    window: TelemetryWindow,
    policy: SamplingWindowPolicy,
    *,
    limits: HardwareGenomeLimits = DEFAULT_LIMITS,
) -> None:
    window = TelemetryWindow.coerce(window, "window")
    policy = SamplingWindowPolicy.coerce(policy, "policy")
    limits.require("max_samples_per_window", len(window.samples))
    if len(window.samples) > policy.maximum_samples:
        raise HardwareGenomeLimitError("sampling window exceeds policy sample count")
    duration = window.ended_at_ms - window.started_at_ms
    if duration > min(policy.maximum_window_ms, policy.maximum_timeout_ms):
        raise HardwareGenomeLimitError("sampling window exceeds its bounded duration/timeout")
    previous: TelemetrySample | None = None
    groups: dict[tuple[str, str, str | None], list[TelemetrySample]] = {}
    for sample in window.samples:
        groups.setdefault((sample.metric_key, sample.source_id, sample.sensor_id), []).append(sample)
    for samples in groups.values():
        previous = None
        for sample in samples:
            if previous is not None:
                if sample.sequence <= previous.sequence:
                    raise HardwareGenomeIntegrityError("sample sequence must increase monotonically per metric/source")
                if sample.captured_at_ms - previous.captured_at_ms < policy.minimum_interval_ms:
                    raise HardwareGenomeAdmissionError("sampling frequency exceeds the declared minimum interval")
            previous = sample


@dataclass(frozen=True)
class DerivationRule(M07Record):
    rule_id: str
    version: str
    operation: str
    input_semantics: tuple[MetricSemantics, ...]
    output_semantics: MetricSemantics

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_id", require_identifier(self.rule_id, "rule_id"))
        object.__setattr__(self, "version", require_version(self.version, "version"))
        operation = require_identifier(self.operation, "operation")
        if operation not in {"COUNTER_RATE", "ENERGY_AVERAGE_POWER", "USED_TOTAL_RATIO", "GAUGE_DELTA"}:
            raise HardwareGenomeAdmissionError("unknown telemetry derivation operation")
        object.__setattr__(self, "operation", operation)
        inputs = tuple(self.input_semantics)
        if not inputs or any(type(item) is not MetricSemantics for item in inputs):
            raise HardwareGenomeValidationError("derivation rules require closed input semantics")
        object.__setattr__(self, "input_semantics", inputs)
        if type(self.output_semantics) is not MetricSemantics:
            raise HardwareGenomeValidationError("derivation output semantics must be explicit")


@dataclass(frozen=True)
class DerivedMetric(M07Record):
    derived_id: str
    rule: DerivationRule
    source_sample_ids: tuple[str, ...]
    subject_id: str
    runtime_id: str
    value: int | float
    unit: str
    interval_ms: int
    derived_at_ms: int
    state: ObservationState

    def __post_init__(self) -> None:
        for field in ("derived_id", "subject_id", "runtime_id", "unit"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "rule", DerivationRule.coerce(self.rule, "rule"))
        ids = tuple(sorted(set(require_identifier(item, "source_sample_ids[]") for item in self.source_sample_ids)))
        if len(ids) < 2:
            raise HardwareGenomeValidationError("derived telemetry must preserve at least two source sample ids")
        object.__setattr__(self, "source_sample_ids", ids)
        object.__setattr__(self, "value", require_finite_number(self.value, "derived value"))
        object.__setattr__(self, "interval_ms", require_nonnegative_int(self.interval_ms, "interval_ms"))
        object.__setattr__(self, "derived_at_ms", require_nonnegative_int(self.derived_at_ms, "derived_at_ms"))
        if self.interval_ms == 0 or type(self.state) is not ObservationState or self.state is not ObservationState.OBSERVED:
            raise HardwareGenomeAdmissionError("derived values require a positive interval and explicit observed state")


def derive_counter_rate(previous: TelemetrySample, current: TelemetrySample, rule: DerivationRule, *, derived_id: str) -> DerivedMetric:
    previous = TelemetrySample.coerce(previous, "previous")
    current = TelemetrySample.coerce(current, "current")
    rule = DerivationRule.coerce(rule, "rule")
    if rule.operation not in {"COUNTER_RATE", "ENERGY_AVERAGE_POWER"}:
        raise HardwareGenomeAdmissionError("rule does not define a counter-rate derivation")
    if previous.semantics not in {MetricSemantics.CUMULATIVE_COUNTER, MetricSemantics.MONOTONIC_COUNTER} or current.semantics is not previous.semantics:
        raise HardwareGenomeAdmissionError("counter rate requires matching cumulative counter samples")
    if previous.semantics not in rule.input_semantics or rule.output_semantics is not MetricSemantics.DERIVED_VALUE:
        raise HardwareGenomeAdmissionError("counter-rate samples/output differ from their versioned derivation rule")
    if (previous.metric_key, previous.unit, previous.subject, previous.runtime) != (current.metric_key, current.unit, current.subject, current.runtime):
        raise HardwareGenomeIntegrityError("counter samples must share exact metric, unit, subject and runtime")
    if previous.subject is None or previous.runtime is None:
        raise HardwareGenomeAdmissionError("counter rates require exact hardware and runtime scope")
    if current.captured_at_ms <= previous.captured_at_ms or current.sequence <= previous.sequence or current.value < previous.value:
        raise HardwareGenomeAdmissionError("counter regression/reset or invalid interval cannot produce a rate")
    if rule.operation == "ENERGY_AVERAGE_POWER" and previous.unit != "joule":
        raise HardwareGenomeAdmissionError("energy-derived average power requires an energy counter in joules")
    interval = current.captured_at_ms - previous.captured_at_ms
    rate = (current.value - previous.value) * 1000 / interval
    unit = "watt" if rule.operation == "ENERGY_AVERAGE_POWER" else f"{previous.unit}_per_second"
    result = DerivedMetric(
        derived_id, rule, (previous.sample_id, current.sample_id), previous.subject.subject_id,
        previous.runtime.runtime_id, rate, unit, interval,
        current.captured_at_ms, ObservationState.OBSERVED,
    )
    validate_derived_metric(result, (previous, current))
    return result


def validate_derived_metric(metric: DerivedMetric, samples: tuple[TelemetrySample, ...]) -> None:
    metric = DerivedMetric.coerce(metric, "metric")
    samples = tuple(TelemetrySample.coerce(item, "samples[]") for item in samples)
    by_id = {item.sample_id: item for item in samples}
    if len(by_id) != len(samples) or set(by_id) != set(metric.source_sample_ids) or len(samples) != 2:
        raise HardwareGenomeIntegrityError("derived telemetry must bind exactly its two unique source samples")
    ordered = sorted(samples, key=lambda item: (item.captured_at_ms, item.sequence, item.sample_id))
    previous, current = ordered
    if (
        previous.semantics not in metric.rule.input_semantics
        or current.semantics is not previous.semantics
        or previous.value is None
        or current.value is None
        or previous.subject is None
        or previous.runtime is None
        or (previous.metric_key, previous.unit, previous.subject, previous.runtime) != (current.metric_key, current.unit, current.subject, current.runtime)
        or (metric.subject_id, metric.runtime_id) != (previous.subject.subject_id, previous.runtime.runtime_id)
        or current.captured_at_ms <= previous.captured_at_ms
        or current.sequence <= previous.sequence
        or current.value < previous.value
    ):
        raise HardwareGenomeIntegrityError("derived telemetry does not preserve source semantics, lineage or exact scope")
    if metric.rule.operation not in {"COUNTER_RATE", "ENERGY_AVERAGE_POWER"} or metric.rule.output_semantics is not MetricSemantics.DERIVED_VALUE:
        raise HardwareGenomeAdmissionError("derivation rule is not implemented by the bounded counter-rate validator")
    if metric.rule.operation == "ENERGY_AVERAGE_POWER" and previous.unit != "joule":
        raise HardwareGenomeAdmissionError("energy-derived average power requires an energy counter in joules")
    interval = current.captured_at_ms - previous.captured_at_ms
    expected_value = (current.value - previous.value) * 1000 / interval
    expected_unit = "watt" if metric.rule.operation == "ENERGY_AVERAGE_POWER" else f"{previous.unit}_per_second"
    if (metric.interval_ms, metric.derived_at_ms, metric.unit, metric.value) != (interval, current.captured_at_ms, expected_unit, expected_value):
        raise HardwareGenomeIntegrityError("derived value differs from its exact source samples and versioned formula")


@dataclass(frozen=True)
class MemoryPressureFact(M07Record):
    pressure_id: str
    scope_id: str
    state: PressureState
    evidence_sample_ids: tuple[str, ...]
    derivation_rule: DerivationRule | None = None
    reported_by_source: bool = True

    def __post_init__(self) -> None:
        for field in ("pressure_id", "scope_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if type(self.state) is not PressureState or type(self.reported_by_source) is not bool:
            raise HardwareGenomeValidationError("memory pressure state must be explicit")
        ids = tuple(sorted(set(require_identifier(item, "evidence_sample_ids[]") for item in self.evidence_sample_ids)))
        if self.state in {PressureState.NORMAL_REPORTED, PressureState.PRESSURE_REPORTED, PressureState.CRITICAL_REPORTED} and not ids:
            raise HardwareGenomeAdmissionError("reported memory pressure requires evidence samples")
        object.__setattr__(self, "evidence_sample_ids", ids)
        if self.derivation_rule is not None:
            object.__setattr__(self, "derivation_rule", DerivationRule.coerce(self.derivation_rule, "derivation_rule"))
        if not self.reported_by_source and self.derivation_rule is None:
            raise HardwareGenomeAdmissionError("derived pressure classification requires a versioned derivation rule")

    def validate_against(self, samples: tuple[TelemetrySample, ...]) -> None:
        by_id = {item.sample_id: item for item in samples}
        selected = [by_id.get(item) for item in self.evidence_sample_ids]
        if any(item is None for item in selected):
            raise HardwareGenomeIntegrityError("memory pressure references an absent telemetry sample")
        for item in selected:
            if item is None:
                continue
            scope_ids = {
                item.subject.subject_id if item.subject is not None else "",
                item.runtime.runtime_id if item.runtime is not None else "",
            }
            if self.scope_id not in scope_ids:
                raise HardwareGenomeIntegrityError("memory pressure evidence must bind its exact declared scope")
            if not self.reported_by_source and self.derivation_rule is not None and item.semantics not in self.derivation_rule.input_semantics:
                raise HardwareGenomeIntegrityError("memory pressure inputs differ from their versioned derivation rule")


@dataclass(frozen=True)
class ThermalCausalityEvidence(M07Record):
    causality_id: str
    temperature_sample_ids: tuple[str, ...]
    clock_sample_ids: tuple[str, ...]
    throttle_reason_observation_ids: tuple[str, ...]
    cause_state: ObservationState

    def __post_init__(self) -> None:
        object.__setattr__(self, "causality_id", require_identifier(self.causality_id, "causality_id"))
        for field in ("temperature_sample_ids", "clock_sample_ids", "throttle_reason_observation_ids"):
            values = tuple(sorted(set(require_identifier(item, f"{field}[]") for item in getattr(self, field))))
            object.__setattr__(self, field, values)
        if type(self.cause_state) is not ObservationState:
            raise HardwareGenomeValidationError("thermal cause state must be explicit")
        if self.cause_state is ObservationState.OBSERVED and not (self.temperature_sample_ids and self.clock_sample_ids and self.throttle_reason_observation_ids):
            raise HardwareGenomeAdmissionError("observed thermal causality requires temperature, clock and explicit reason evidence")

    def validate_against(self, samples: tuple[TelemetrySample, ...], observations: tuple[DiscoveryObservation, ...]) -> None:
        by_sample = {item.sample_id: item for item in samples}
        by_observation = {item.observation_id: item for item in observations}
        selected = [by_sample.get(item) for item in (*self.temperature_sample_ids, *self.clock_sample_ids)]
        reasons = [by_observation.get(item) for item in self.throttle_reason_observation_ids]
        if any(item is None for item in (*selected, *reasons)):
            raise HardwareGenomeIntegrityError("thermal causality references missing source evidence")
        temperatures = [by_sample[item] for item in self.temperature_sample_ids]
        clocks = [by_sample[item] for item in self.clock_sample_ids]
        if any(not item.metric_key.endswith("temperature") for item in temperatures):
            raise HardwareGenomeIntegrityError("thermal temperature evidence must use an explicit temperature metric")
        if any("clock" not in item.metric_key for item in clocks):
            raise HardwareGenomeIntegrityError("thermal clock evidence must use an explicit clock metric")
        if any("throttle" not in item.fact_key for item in reasons if item is not None):
            raise HardwareGenomeIntegrityError("thermal cause evidence must explicitly identify a throttling reason")
        scopes = {
            (item.subject.subject_id if item.subject else None, item.runtime.runtime_id if item.runtime else None)
            for item in (*temperatures, *clocks)
        }
        scopes.update(
            (item.subject.subject_id if item.subject else None, item.runtime.runtime_id if item.runtime else None)
            for item in reasons
            if item is not None
        )
        if len(scopes) > 1:
            raise HardwareGenomeIntegrityError("thermal causality sources must share exact subject/runtime scope")


@dataclass(frozen=True)
class MemoryCapacityFact(M07Record):
    capacity_id: str
    subject_id: str
    kind: MemoryKind
    capacity_bytes: int
    observation: DiscoveryObservation

    def __post_init__(self) -> None:
        for field in ("capacity_id", "subject_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if type(self.kind) is not MemoryKind:
            raise HardwareGenomeValidationError("memory kind must use the closed M07 vocabulary")
        if self.kind is MemoryKind.STORAGE_AVAILABLE:
            raise HardwareGenomeAdmissionError("time-sensitive available storage is not static capacity")
        object.__setattr__(self, "capacity_bytes", require_nonnegative_int(self.capacity_bytes, "capacity_bytes"))
        object.__setattr__(self, "observation", DiscoveryObservation.coerce(self.observation, "observation"))
        if self.observation.subject is None or self.observation.subject.subject_id != self.subject_id:
            raise HardwareGenomeIntegrityError("memory capacity must bind the exact hardware/resource subject")
        if self.observation.state is not ObservationState.OBSERVED or self.observation.value != self.capacity_bytes or self.observation.unit != "byte":
            raise HardwareGenomeIntegrityError("static capacity must equal its positive byte-valued observation")
        if self.observation.freshness is FreshnessClass.DYNAMIC:
            raise HardwareGenomeAdmissionError("dynamic memory pressure/availability cannot be admitted as static capacity")


def require_telemetry_fresh(sample: TelemetrySample, *, now_ms: int) -> None:
    sample = TelemetrySample.coerce(sample, "sample")
    now_ms = require_nonnegative_int(now_ms, "now_ms")
    if sample.state is not ObservationState.OBSERVED or now_ms >= sample.expires_at_ms:
        raise HardwareGenomeAdmissionError("stale, unavailable or non-positive telemetry cannot represent current state")


def validate_sample_registry(sample: TelemetrySample, registry: SemanticKeyRegistry) -> None:
    sample = TelemetrySample.coerce(sample, "sample")
    registry = SemanticKeyRegistry.coerce(registry, "registry")
    definition = registry.find(sample.metric_key)
    if definition is None:
        raise HardwareGenomeAdmissionError("telemetry metric is absent from the versioned semantic registry")
    if sample.state not in definition.allowed_states:
        raise HardwareGenomeAdmissionError("telemetry state is not allowed by its semantic registry entry")
    if sample.unit != definition.unit:
        raise HardwareGenomeIntegrityError("telemetry unit differs from its semantic registry entry")
    if definition.freshness is not FreshnessClass.DYNAMIC:
        raise HardwareGenomeIntegrityError("dynamic telemetry key must declare DYNAMIC freshness")
    if definition.evidence_required and sample.state is ObservationState.OBSERVED and sample.evidence is None:
        raise HardwareGenomeAdmissionError("registry requires evidence for this telemetry key")
