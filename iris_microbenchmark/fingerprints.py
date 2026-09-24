"""Privacy-conscious performance projections, baselines, drift and recheck evidence."""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from .base import M08Record, content_digest, require_sequence
from .enums import DriftClass, FreshnessState, PrivacyClass, ResultState
from .errors import MicrobenchmarkAdmissionError, MicrobenchmarkAuthorityError, MicrobenchmarkCompatibilityError, MicrobenchmarkIntegrityError, MicrobenchmarkValidationError
from .evidence import BenchmarkResult
from .provenance import ConsumerProjectionDescriptor, M07ProvenanceBinding
from .versions import FINGERPRINT_VERSION, require_digest, require_finite_number, require_identifier, require_nonnegative_int, require_text, require_unique, require_version

__all__ = [
    "FingerprintMetric", "PerformanceFingerprint", "project_fingerprint", "BaselinePromotionReceipt",
    "PerformanceBaseline", "promote_baseline", "MetricNoiseGuard", "FingerprintCompatibilityContract",
    "DriftEvidence", "DriftAttribution", "detect_drift", "RecheckTriggerDecision", "evaluate_recheck_trigger",
]


@dataclass(frozen=True)
class FingerprintMetric(M08Record):
    metric_id: str
    metric_version: str
    unit: str
    value: float
    uncertainty: float | None
    sample_count: int
    dispersion: float

    def __post_init__(self) -> None:
        for field in ("metric_id", "unit"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "metric_version", require_version(self.metric_version, "metric_version"))
        for field in ("value", "dispersion"):
            number = require_finite_number(getattr(self, field), field)
            if field == "dispersion" and number < 0:
                raise MicrobenchmarkValidationError("dispersion cannot be negative")
            object.__setattr__(self, field, number)
        if self.uncertainty is not None:
            uncertainty = require_finite_number(self.uncertainty, "uncertainty")
            if uncertainty < 0:
                raise MicrobenchmarkValidationError("uncertainty cannot be negative")
            object.__setattr__(self, "uncertainty", uncertainty)
        count = require_nonnegative_int(self.sample_count, "sample_count")
        if count < 1:
            raise MicrobenchmarkValidationError("fingerprint metrics require at least one sample")
        object.__setattr__(self, "sample_count", count)


@dataclass(frozen=True)
class PerformanceFingerprint(M08Record):
    fingerprint_id: str
    schema_version: str
    projection_id: str
    projection_version: str
    binding_digest: str
    source_protocol_refs: tuple[tuple[str, str], ...]
    source_result_ids: tuple[str, ...]
    source_results_digest: str
    metrics: tuple[FingerprintMetric, ...]
    included_context_axes: tuple[str, ...]
    context_value_digests: tuple[tuple[str, str], ...]
    excluded_context_axes: tuple[str, ...]
    privacy_class: PrivacyClass
    subject_token: str | None
    evidence_purpose_id: str
    created_at_ms: int
    fingerprint_digest: str

    def __post_init__(self) -> None:
        for field in ("fingerprint_id", "projection_id", "evidence_purpose_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "schema_version", require_version(self.schema_version))
        object.__setattr__(self, "projection_version", require_version(self.projection_version))
        for field in ("binding_digest", "source_results_digest", "fingerprint_digest"):
            object.__setattr__(self, field, require_digest(getattr(self, field), field))
        protocols = tuple(sorted((require_identifier(key, "protocol_id"), require_version(version, "protocol_version")) for key, version in self.source_protocol_refs))
        if not protocols or len(set(protocols)) != len(protocols):
            raise MicrobenchmarkIntegrityError("fingerprint protocol references must be non-empty and unique")
        object.__setattr__(self, "source_protocol_refs", protocols)
        result_ids = tuple(sorted(require_unique(self.source_result_ids, "source_result_ids", maximum=50_000)))
        if not result_ids:
            raise MicrobenchmarkIntegrityError("fingerprint must bind at least one exact source result")
        object.__setattr__(self, "source_result_ids", result_ids)
        object.__setattr__(self, "metrics", tuple(FingerprintMetric.coerce(item, "metrics[]") for item in self.metrics))
        if not self.metrics or len({item.metric_id for item in self.metrics}) != len(self.metrics):
            raise MicrobenchmarkIntegrityError("fingerprint must project distinct metric identities")
        object.__setattr__(self, "included_context_axes", tuple(sorted(require_unique(self.included_context_axes, "included_context_axes", maximum=512))))
        context_digests = tuple(sorted((require_identifier(axis, "context axis"), require_digest(digest, "context value digest")) for axis, digest in self.context_value_digests))
        if tuple(axis for axis, _ in context_digests) != self.included_context_axes:
            raise MicrobenchmarkIntegrityError("fingerprint context digests must exactly cover included axes")
        object.__setattr__(self, "context_value_digests", context_digests)
        object.__setattr__(self, "excluded_context_axes", tuple(sorted(require_unique(self.excluded_context_axes, "excluded_context_axes", maximum=512))))
        if set(self.included_context_axes) & set(self.excluded_context_axes):
            raise MicrobenchmarkIntegrityError("context axis cannot be both included and excluded")
        if not isinstance(self.privacy_class, PrivacyClass):
            raise MicrobenchmarkValidationError("privacy_class must be PrivacyClass")
        if self.subject_token is not None:
            object.__setattr__(self, "subject_token", require_identifier(self.subject_token, "subject_token"))
        if self.privacy_class in {PrivacyClass.PUBLIC, PrivacyClass.SYNTHETIC} and self.subject_token is not None:
            raise MicrobenchmarkIntegrityError("public/synthetic projections cannot expose a stable subject token")
        if self.privacy_class is PrivacyClass.SENSITIVE:
            raise MicrobenchmarkAdmissionError("sensitive identity projection is outside the M08 fingerprint surface")
        if self.privacy_class is PrivacyClass.LOCAL and self.subject_token is None:
            raise MicrobenchmarkAdmissionError("local fingerprint projection requires an opaque pseudonymous subject token")
        object.__setattr__(self, "created_at_ms", require_nonnegative_int(self.created_at_ms, "created_at_ms"))
        if self.source_results_digest != content_digest(self.source_result_ids):
            raise MicrobenchmarkIntegrityError("fingerprint source-results digest does not match its exact source IDs")
        expected = _fingerprint_digest_material(
            self.schema_version, self.projection_id, self.projection_version, self.binding_digest,
            self.source_protocol_refs, self.source_result_ids, self.metrics, self.included_context_axes,
            self.context_value_digests, self.privacy_class, self.subject_token, self.evidence_purpose_id,
        )
        if self.fingerprint_digest != content_digest(expected):
            raise MicrobenchmarkIntegrityError("fingerprint digest does not match its immutable projection content")


def _fingerprint_digest_material(
    schema_version: str,
    projection_id: str,
    projection_version: str,
    binding_digest: str,
    source_protocol_refs: tuple[tuple[str, str], ...],
    source_result_ids: tuple[str, ...],
    metrics: tuple[FingerprintMetric, ...],
    included_context_axes: tuple[str, ...],
    context_value_digests: tuple[tuple[str, str], ...],
    privacy_class: PrivacyClass,
    subject_token: str | None,
    evidence_purpose_id: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "projection_id": projection_id,
        "projection_version": projection_version,
        "binding_digest": binding_digest,
        "source_protocol_refs": source_protocol_refs,
        "source_result_ids": source_result_ids,
        "metrics": metrics,
        "included_context_axes": included_context_axes,
        "context_value_digests": context_value_digests,
        "privacy_class": privacy_class,
        "subject_token": subject_token,
        "evidence_purpose_id": evidence_purpose_id,
    }


def project_fingerprint(
    results: tuple[BenchmarkResult, ...],
    binding: M07ProvenanceBinding,
    projection: ConsumerProjectionDescriptor,
    *,
    fingerprint_id: str,
    created_at_ms: int,
    context_axes: tuple[tuple[str, str], ...] = (),
) -> PerformanceFingerprint:
    selected = tuple(BenchmarkResult.coerce(item, "results[]") for item in require_sequence(results, "results", maximum=50_000))
    if not selected or len({item.result_id for item in selected}) != len(selected):
        raise MicrobenchmarkIntegrityError("fingerprints need non-empty unique exact source results")
    if any(item.binding != binding or item.state is not ResultState.VALID for item in selected):
        raise MicrobenchmarkAdmissionError("fingerprints accept only valid results with one exact provenance binding")
    if not projection.evidence_purpose.qualifies("hardware-capability-fingerprint"):
        raise MicrobenchmarkAdmissionError("projection purpose does not permit hardware capability fingerprints")
    if not projection.evidence_purpose.qualifies(f"consumer:{projection.consumer_namespace}"):
        raise MicrobenchmarkAdmissionError("evidence purpose does not authorize this fingerprint consumer namespace")
    metrics_by_id: dict[str, list[BenchmarkResult]] = {}
    for item in selected:
        if item.metric.metric_id in projection.included_metrics:
            metrics_by_id.setdefault(item.metric.metric_id, []).append(item)
    if set(metrics_by_id) != set(projection.included_metrics):
        missing = sorted(set(projection.included_metrics) - set(metrics_by_id))
        raise MicrobenchmarkAdmissionError(f"fingerprint projection lacks selected metrics: {missing}")
    metrics: list[FingerprintMetric] = []
    for metric_id, values in sorted(metrics_by_id.items()):
        semantics = {item.metric for item in values}
        if len(semantics) != 1:
            raise MicrobenchmarkCompatibilityError("one fingerprint cannot merge incompatible metric semantics")
        metric = values[0].metric
        samples = tuple(sample.value for result in values for sample in result.samples)
        mean = sum(samples) / len(samples)
        dispersion = statistics.pstdev(samples) if len(samples) > 1 else 0.0
        uncertainties = [item.uncertainty for item in values if item.uncertainty is not None]
        uncertainty = max(uncertainties) if uncertainties else None
        metrics.append(FingerprintMetric(metric_id, metric.version, metric.unit, mean, uncertainty, len(samples), dispersion))
    binding_digest = content_digest(binding)
    sources = tuple(sorted({(item.protocol_id, item.protocol_version) for item in selected}))
    source_ids = tuple(sorted(item.result_id for item in selected))
    source_digest = content_digest(source_ids)
    axis_values = require_sequence(context_axes, "context_axes", maximum=512)
    supplied_axes = tuple(sorted((require_identifier(key, "context axis"), require_text(value, "context value")) for key, value in axis_values))
    if len({axis for axis, _ in supplied_axes}) != len(supplied_axes):
        raise MicrobenchmarkIntegrityError("fingerprint context axes must be unique")
    allowed_axes = set(projection.included_dimensions)
    supplied_axis_names = {axis for axis, _ in supplied_axes}
    if allowed_axes - supplied_axis_names:
        raise MicrobenchmarkAdmissionError("fingerprint projection requires context dimensions that were not supplied")
    included_context = tuple((axis, value) for axis, value in supplied_axes if axis in allowed_axes)
    included_axes = tuple(axis for axis, _ in included_context)
    context_digests = tuple((axis, content_digest((axis, value))) for axis, value in included_context)
    excluded_axes = tuple(axis for axis, _ in supplied_axes if axis not in allowed_axes)
    if len(included_axes) > 512 or len(excluded_axes) > 512:
        raise MicrobenchmarkValidationError("included fingerprint context values must be explicit opaque strings")
    fingerprint_material = _fingerprint_digest_material(
        FINGERPRINT_VERSION, projection.projection_id, projection.version, binding_digest,
        sources, source_ids, tuple(metrics), included_axes, context_digests,
        projection.privacy_class, projection.pseudonymous_subject_token,
        projection.evidence_purpose.purpose_id,
    )
    digest = content_digest(fingerprint_material)
    return PerformanceFingerprint(
        fingerprint_id, FINGERPRINT_VERSION, projection.projection_id, projection.version,
        binding_digest, sources, source_ids, source_digest, tuple(metrics), included_axes,
        context_digests, excluded_axes, projection.privacy_class, projection.pseudonymous_subject_token,
        projection.evidence_purpose.purpose_id, created_at_ms, digest,
    )


@dataclass(frozen=True)
class BaselinePromotionReceipt(M08Record):
    receipt_id: str
    policy_ref: str
    fingerprint_id: str
    fingerprint_digest: str
    promoted_at_ms: int
    supersedes_baseline_id: str | None

    def __post_init__(self) -> None:
        for field in ("receipt_id", "policy_ref", "fingerprint_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "fingerprint_digest", require_digest(self.fingerprint_digest, "fingerprint_digest"))
        object.__setattr__(self, "promoted_at_ms", require_nonnegative_int(self.promoted_at_ms, "promoted_at_ms"))
        if self.supersedes_baseline_id is not None:
            object.__setattr__(self, "supersedes_baseline_id", require_identifier(self.supersedes_baseline_id, "supersedes_baseline_id"))


@dataclass(frozen=True)
class PerformanceBaseline(M08Record):
    baseline_id: str
    name: str
    source_fingerprint_id: str
    source_fingerprint_digest: str
    creation_policy_ref: str
    environment_binding_digest: str
    validity_dependency_refs: tuple[str, ...]
    promotion_receipt: BaselinePromotionReceipt
    supersedes_baseline_id: str | None
    created_at_ms: int
    freshness: FreshnessState

    def __post_init__(self) -> None:
        for field in ("baseline_id", "name", "source_fingerprint_id", "creation_policy_ref"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        for field in ("source_fingerprint_digest", "environment_binding_digest"):
            object.__setattr__(self, field, require_digest(getattr(self, field), field))
        object.__setattr__(self, "validity_dependency_refs", tuple(sorted(require_unique(self.validity_dependency_refs, "validity_dependency_refs", maximum=10_000))))
        object.__setattr__(self, "promotion_receipt", BaselinePromotionReceipt.coerce(self.promotion_receipt, "promotion_receipt"))
        if self.supersedes_baseline_id is not None:
            object.__setattr__(self, "supersedes_baseline_id", require_identifier(self.supersedes_baseline_id, "supersedes_baseline_id"))
        object.__setattr__(self, "created_at_ms", require_nonnegative_int(self.created_at_ms, "created_at_ms"))
        if not isinstance(self.freshness, FreshnessState):
            raise MicrobenchmarkValidationError("freshness must be FreshnessState")
        if (self.promotion_receipt.fingerprint_id, self.promotion_receipt.fingerprint_digest) != (self.source_fingerprint_id, self.source_fingerprint_digest):
            raise MicrobenchmarkIntegrityError("baseline promotion receipt does not bind its source fingerprint")
        if self.promotion_receipt.supersedes_baseline_id != self.supersedes_baseline_id:
            raise MicrobenchmarkIntegrityError("baseline supersession must match its explicit promotion receipt")


def promote_baseline(
    fingerprint: PerformanceFingerprint,
    receipt: BaselinePromotionReceipt,
    *,
    baseline_id: str,
    name: str,
    creation_policy_ref: str,
    validity_dependency_refs: tuple[str, ...],
    created_at_ms: int,
    previous_baseline: PerformanceBaseline | None = None,
) -> PerformanceBaseline:
    fingerprint = PerformanceFingerprint.coerce(fingerprint, "fingerprint")
    receipt = BaselinePromotionReceipt.coerce(receipt, "receipt")
    supersedes = previous_baseline.baseline_id if previous_baseline is not None else None
    if (receipt.fingerprint_id, receipt.fingerprint_digest) != (fingerprint.fingerprint_id, fingerprint.fingerprint_digest):
        raise MicrobenchmarkIntegrityError("promotion receipt must bind the exact fingerprint")
    if receipt.supersedes_baseline_id != supersedes:
        raise MicrobenchmarkAdmissionError("baseline replacement requires explicit supersession of the exact prior baseline")
    return PerformanceBaseline(
        baseline_id, name, fingerprint.fingerprint_id, fingerprint.fingerprint_digest,
        creation_policy_ref, fingerprint.binding_digest, validity_dependency_refs,
        receipt, supersedes, created_at_ms, FreshnessState.CURRENT,
    )


@dataclass(frozen=True)
class MetricNoiseGuard(M08Record):
    metric_id: str
    metric_version: str
    minimum_samples_per_window: int
    minimum_absolute_effect: float
    minimum_variance_effect: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "metric_id", require_identifier(self.metric_id, "metric_id"))
        object.__setattr__(self, "metric_version", require_version(self.metric_version, "metric_version"))
        count = require_nonnegative_int(self.minimum_samples_per_window, "minimum_samples_per_window")
        if count < 2:
            raise MicrobenchmarkValidationError("noise guard needs at least two samples per measurement window")
        object.__setattr__(self, "minimum_samples_per_window", count)
        for field in ("minimum_absolute_effect", "minimum_variance_effect"):
            number = require_finite_number(getattr(self, field), field)
            if number < 0:
                raise MicrobenchmarkValidationError("noise guard thresholds cannot be negative")
            object.__setattr__(self, field, number)


@dataclass(frozen=True)
class FingerprintCompatibilityContract(M08Record):
    contract_id: str
    version: str
    comparable_protocol_refs: tuple[tuple[str, str], ...]
    allow_cross_subject: bool
    allow_cross_runtime: bool
    allowed_context_delta_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", require_identifier(self.contract_id, "contract_id"))
        object.__setattr__(self, "version", require_version(self.version))
        pairs = tuple(sorted((require_identifier(k, "protocol_id"), require_version(v, "protocol_version")) for k, v in self.comparable_protocol_refs))
        if not pairs or len(set(pairs)) != len(pairs):
            raise MicrobenchmarkValidationError("comparability contract must name at least one protocol")
        object.__setattr__(self, "comparable_protocol_refs", pairs)
        if type(self.allow_cross_subject) is not bool or type(self.allow_cross_runtime) is not bool:
            raise MicrobenchmarkValidationError("cross-subject/runtime declarations must be bool")
        object.__setattr__(self, "allowed_context_delta_refs", tuple(sorted(require_unique(self.allowed_context_delta_refs, "allowed_context_delta_refs", maximum=1_024))))


@dataclass(frozen=True)
class DriftEvidence(M08Record):
    drift_id: str
    baseline_id: str
    baseline_fingerprint_id: str
    current_fingerprint_id: str
    metric_id: str | None
    classification: DriftClass
    effect: float | None
    variance_effect: float | None
    reasons: tuple[str, ...]
    compared_at_ms: int
    causal_claim: bool = False

    def __post_init__(self) -> None:
        for field in ("drift_id", "baseline_id", "baseline_fingerprint_id", "current_fingerprint_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if self.metric_id is not None:
            object.__setattr__(self, "metric_id", require_identifier(self.metric_id, "metric_id"))
        if not isinstance(self.classification, DriftClass):
            raise MicrobenchmarkValidationError("classification must be DriftClass")
        for field in ("effect", "variance_effect"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_finite_number(value, field))
        object.__setattr__(self, "reasons", tuple(sorted(require_unique(self.reasons, "reasons", maximum=256))))
        object.__setattr__(self, "compared_at_ms", require_nonnegative_int(self.compared_at_ms, "compared_at_ms"))
        if self.causal_claim is not False:
            raise MicrobenchmarkAuthorityError("M08 context correlation cannot assert causality")


@dataclass(frozen=True)
class DriftAttribution(M08Record):
    drift_id: str
    correlated_context_refs: tuple[str, ...]
    causal_claim: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "drift_id", require_identifier(self.drift_id, "drift_id"))
        object.__setattr__(self, "correlated_context_refs", tuple(sorted(require_unique(self.correlated_context_refs, "correlated_context_refs", maximum=1_024))))
        if self.causal_claim is not False:
            raise MicrobenchmarkAuthorityError("correlation evidence cannot become a causal diagnosis")


def detect_drift(
    baseline: PerformanceBaseline,
    baseline_fingerprint: PerformanceFingerprint,
    current: PerformanceFingerprint,
    guards: tuple[MetricNoiseGuard, ...],
    compatibility: FingerprintCompatibilityContract,
    *,
    drift_id: str,
    compared_at_ms: int,
    context_delta_refs: tuple[str, ...] = (),
) -> tuple[DriftEvidence, ...]:
    baseline = PerformanceBaseline.coerce(baseline, "baseline")
    old = PerformanceFingerprint.coerce(baseline_fingerprint, "baseline_fingerprint")
    new = PerformanceFingerprint.coerce(current, "current")
    compatibility = FingerprintCompatibilityContract.coerce(compatibility, "compatibility")
    if (baseline.source_fingerprint_id, baseline.source_fingerprint_digest) != (old.fingerprint_id, old.fingerprint_digest):
        raise MicrobenchmarkIntegrityError("drift comparison baseline is not the exact fingerprint promoted in the baseline artifact")
    if baseline.freshness is FreshnessState.STALE:
        return (DriftEvidence(drift_id, baseline.baseline_id, old.fingerprint_id, new.fingerprint_id, None, DriftClass.STALE_BASELINE, None, None, ("baseline_stale",), compared_at_ms),)
    if (old.projection_id, old.projection_version, old.privacy_class, old.included_context_axes) != (new.projection_id, new.projection_version, new.privacy_class, new.included_context_axes):
        return (DriftEvidence(drift_id, baseline.baseline_id, old.fingerprint_id, new.fingerprint_id, None, DriftClass.INCOMPARABLE, None, None, ("fingerprint_projection_changed",), compared_at_ms),)
    old_protocols, new_protocols = set(old.source_protocol_refs), set(new.source_protocol_refs)
    allowed = set(compatibility.comparable_protocol_refs)
    if not old_protocols.issubset(allowed) or not new_protocols.issubset(allowed):
        return (DriftEvidence(drift_id, baseline.baseline_id, old.fingerprint_id, new.fingerprint_id, None, DriftClass.INCOMPARABLE, None, None, ("protocol_semantics_incompatible",), compared_at_ms),)
    if old.binding_digest != new.binding_digest and not (compatibility.allow_cross_subject and compatibility.allow_cross_runtime):
        return (DriftEvidence(drift_id, baseline.baseline_id, old.fingerprint_id, new.fingerprint_id, None, DriftClass.INCOMPARABLE, None, None, ("hardware_runtime_binding_changed_without_full_comparability_contract",), compared_at_ms),)
    changed_context = old.context_value_digests != new.context_value_digests
    context_refs = tuple(sorted(require_unique(context_delta_refs, "context_delta_refs", maximum=1_024)))
    allowed_context_refs = set(compatibility.allowed_context_delta_refs)
    if changed_context and (not context_refs or not set(context_refs).issubset(allowed_context_refs)):
        return (DriftEvidence(drift_id, baseline.baseline_id, old.fingerprint_id, new.fingerprint_id, None, DriftClass.INCOMPARABLE, None, None, ("context_delta_not_qualified_by_comparability_contract",), compared_at_ms),)
    old_metrics = {item.metric_id: item for item in old.metrics}
    new_metrics = {item.metric_id: item for item in new.metrics}
    guard_map = {(item.metric_id, item.metric_version): item for item in guards}
    reports: list[DriftEvidence] = []
    for metric_id in sorted(set(old_metrics) | set(new_metrics)):
        before, after = old_metrics.get(metric_id), new_metrics.get(metric_id)
        if before is None or after is None or (before.metric_version, before.unit) != (after.metric_version, after.unit):
            classification, effect, variance, reasons = DriftClass.INCOMPARABLE, None, None, ("metric_semantics_changed",)
        else:
            guard = guard_map.get((metric_id, before.metric_version))
            if guard is None or min(before.sample_count, after.sample_count) < guard.minimum_samples_per_window:
                classification, effect, variance, reasons = DriftClass.INSUFFICIENT_EVIDENCE, None, None, ("sample_window_below_metric_guard",)
            else:
                effect = after.value - before.value
                variance = after.dispersion ** 2 - before.dispersion ** 2
                if abs(effect) <= guard.minimum_absolute_effect and abs(variance) <= guard.minimum_variance_effect:
                    classification, reasons = DriftClass.NO_MATERIAL_DRIFT, ("within_metric_noise_guard",)
                elif abs(variance) > guard.minimum_variance_effect and abs(effect) <= guard.minimum_absolute_effect:
                    classification, reasons = DriftClass.VARIANCE_SHIFT, ("variance_shift_exceeds_metric_guard",)
                else:
                    classification, reasons = DriftClass.PERFORMANCE_SHIFT, ("effect_exceeds_metric_guard",)
        reports.append(DriftEvidence(drift_id, baseline.baseline_id, old.fingerprint_id, new.fingerprint_id, metric_id, classification, effect, variance, reasons, compared_at_ms))
    return tuple(reports)


@dataclass(frozen=True)
class RecheckTriggerDecision(M08Record):
    decision_id: str
    eligible: bool
    required: bool
    reason_refs: tuple[str, ...]
    benchmark_authorization_required: bool
    scheduling_ref: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", require_identifier(self.decision_id, "decision_id"))
        if type(self.eligible) is not bool or type(self.required) is not bool or type(self.benchmark_authorization_required) is not bool:
            raise MicrobenchmarkValidationError("recheck decision flags must be bool")
        object.__setattr__(self, "reason_refs", tuple(sorted(require_unique(self.reason_refs, "reason_refs", maximum=1_024))))
        if self.scheduling_ref is not None:
            object.__setattr__(self, "scheduling_ref", require_identifier(self.scheduling_ref, "scheduling_ref"))
        if self.scheduling_ref is not None:
            raise MicrobenchmarkAuthorityError("M08 recheck evaluation cannot schedule work")
        if self.required and not self.benchmark_authorization_required:
            raise MicrobenchmarkAdmissionError("required rechecks still require active benchmark authorization")


def evaluate_recheck_trigger(
    *,
    decision_id: str,
    stale: bool,
    material_change_refs: tuple[str, ...],
    explicit_request_ref: str | None,
    safely_eligible: bool,
) -> RecheckTriggerDecision:
    reasons = list(material_change_refs)
    if stale:
        reasons.append("freshness_threshold")
    if explicit_request_ref is not None:
        reasons.append(explicit_request_ref)
    required = stale or bool(material_change_refs) or explicit_request_ref is not None
    return RecheckTriggerDecision(decision_id, bool(safely_eligible), required, tuple(sorted(set(reasons))), required, None)
