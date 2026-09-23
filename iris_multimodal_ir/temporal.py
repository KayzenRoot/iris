"""Exact rational time, motion curves, sampling, and temporal conversion receipts."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, ClassVar

from iris_intent.identity import SemanticRef

from .base import IRRecord, fraction, many, one, optional
from .common import non_negative_int, positive_int, require_enum
from .enums import TemporalLayer
from .errors import IRIntegrityError, IRLimitError, IRSchemaError
from .identity import IRNodeRef, ResourceRef
from .limits import DEFAULT_LIMITS, IRLimits
from .versions import content_digest, require_identifier, require_text, require_version

__all__ = [
    "TemporalReferenceIR", "TimePointIR", "TimeRangeIR", "DurationIR", "MotionTargetRef", "CurveKeyIR",
    "AnimationCurveIR", "MotionChannelIR", "MotionIR", "MotionClipIR", "MotionLayerIR", "TemporalSamplingIR",
    "TemporalMarkerIR", "TemporalRelationIR", "TemporalConversionReceipt", "convert_time_point", "sample_curve",
]


def _fraction(value: Any, field: str) -> Fraction:
    if isinstance(value, bool):
        raise IRSchemaError(f"{field} cannot be bool")
    if isinstance(value, Fraction):
        result = value
    elif isinstance(value, int):
        result = Fraction(value, 1)
    elif isinstance(value, tuple) and len(value) == 2:
        try:
            result = Fraction(value[0], value[1])
        except (TypeError, ValueError, ZeroDivisionError):
            raise IRSchemaError(f"{field} must be an exact rational") from None
    else:
        raise IRSchemaError(f"{field} must be Fraction, integer, or numerator/denominator pair")
    return result


@dataclass(frozen=True)
class TemporalReferenceIR(IRRecord):
    reference_id: str
    ticks_per_second: Fraction
    epoch: str
    version: str = "temporal-v1"

    NESTED: ClassVar = {"ticks_per_second": fraction}

    def __post_init__(self) -> None:
        object.__setattr__(self, "reference_id", require_identifier(self.reference_id, "reference_id"))
        rate = _fraction(self.ticks_per_second, "ticks_per_second")
        if rate <= 0:
            raise IRSchemaError("ticks_per_second must be positive")
        object.__setattr__(self, "ticks_per_second", rate)
        object.__setattr__(self, "epoch", require_text(self.epoch, "epoch", maximum=256))
        object.__setattr__(self, "version", require_version(self.version))


@dataclass(frozen=True)
class TimePointIR(IRRecord):
    reference_id: str
    ticks: Fraction
    layer: TemporalLayer

    NESTED: ClassVar = {"ticks": fraction}

    def __post_init__(self) -> None:
        object.__setattr__(self, "reference_id", require_identifier(self.reference_id, "reference_id"))
        object.__setattr__(self, "ticks", _fraction(self.ticks, "ticks"))
        object.__setattr__(self, "layer", require_enum(self.layer, TemporalLayer, "layer"))


@dataclass(frozen=True)
class TimeRangeIR(IRRecord):
    start: TimePointIR
    end: TimePointIR

    NESTED: ClassVar = {"start": one(TimePointIR), "end": one(TimePointIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "start", TimePointIR.coerce(self.start, "start"))
        object.__setattr__(self, "end", TimePointIR.coerce(self.end, "end"))
        if self.start.reference_id != self.end.reference_id or self.start.layer is not self.end.layer:
            raise IRIntegrityError("time range endpoints require the same time reference and layer")
        if self.end.ticks < self.start.ticks:
            raise IRIntegrityError("time range end precedes start")

    @property
    def duration_ticks(self) -> Fraction:
        return self.end.ticks - self.start.ticks


@dataclass(frozen=True)
class DurationIR(IRRecord):
    reference_id: str
    ticks: Fraction

    NESTED: ClassVar = {"ticks": fraction}

    def __post_init__(self) -> None:
        object.__setattr__(self, "reference_id", require_identifier(self.reference_id, "reference_id"))
        object.__setattr__(self, "ticks", _fraction(self.ticks, "ticks"))
        if self.ticks < 0:
            raise IRSchemaError("duration cannot be negative")


@dataclass(frozen=True)
class MotionTargetRef(IRRecord):
    target: IRNodeRef
    semantic_path: str
    value_type: str

    NESTED: ClassVar = {"target": one(IRNodeRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "target", IRNodeRef.coerce(self.target, "target"))
        object.__setattr__(self, "semantic_path", require_text(self.semantic_path, "semantic_path", maximum=256))
        object.__setattr__(self, "value_type", require_identifier(self.value_type, "value_type"))


@dataclass(frozen=True)
class CurveKeyIR(IRRecord):
    time: TimePointIR
    value: float
    interpolation: str = "linear"

    NESTED: ClassVar = {"time": one(TimePointIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "time", TimePointIR.coerce(self.time, "time"))
        from .versions import require_finite_number
        object.__setattr__(self, "value", float(require_finite_number(self.value, "value")))
        object.__setattr__(self, "interpolation", require_identifier(self.interpolation, "interpolation"))
        if self.interpolation not in {"step", "linear", "cubic"}:
            raise IRSchemaError("curve interpolation must be step, linear, or cubic")


@dataclass(frozen=True)
class AnimationCurveIR(IRRecord):
    curve_id: str
    keys: tuple[CurveKeyIR, ...]
    output_type: str
    extrapolation: str = "clamp"

    NESTED: ClassVar = {"keys": many(CurveKeyIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "curve_id", require_identifier(self.curve_id, "curve_id"))
        keys = tuple(CurveKeyIR.coerce(item, "keys[]") for item in self.keys)
        if not keys:
            raise IRSchemaError("animation curve requires keys")
        first_ref, first_layer = keys[0].time.reference_id, keys[0].time.layer
        ordered = tuple(sorted(keys, key=lambda item: item.time.ticks))
        if any(item.time.reference_id != first_ref or item.time.layer is not first_layer for item in ordered):
            raise IRIntegrityError("curve keys require one explicit time basis and layer")
        if len({item.time.ticks for item in ordered}) != len(ordered):
            raise IRIntegrityError("curve key times must be unique")
        object.__setattr__(self, "keys", ordered)
        object.__setattr__(self, "output_type", require_identifier(self.output_type, "output_type"))
        object.__setattr__(self, "extrapolation", require_identifier(self.extrapolation, "extrapolation"))
        if self.extrapolation not in {"clamp", "linear", "error"}:
            raise IRSchemaError("unsupported curve extrapolation")

    def evaluate(self, time: TimePointIR) -> float:
        if time.reference_id != self.keys[0].time.reference_id or time.layer is not self.keys[0].time.layer:
            raise IRIntegrityError("curve evaluation time basis or layer differs")
        if time.ticks <= self.keys[0].time.ticks:
            if time.ticks < self.keys[0].time.ticks and self.extrapolation == "error":
                raise IRIntegrityError("curve sample precedes declared range")
            return self.keys[0].value
        if time.ticks >= self.keys[-1].time.ticks:
            if time.ticks > self.keys[-1].time.ticks and self.extrapolation == "error":
                raise IRIntegrityError("curve sample exceeds declared range")
            return self.keys[-1].value
        for left, right in zip(self.keys, self.keys[1:]):
            if left.time.ticks <= time.ticks <= right.time.ticks:
                if left.interpolation == "step":
                    return left.value
                ratio = float((time.ticks - left.time.ticks) / (right.time.ticks - left.time.ticks))
                return left.value + (right.value - left.value) * ratio
        raise IRIntegrityError("curve segment could not be resolved")


@dataclass(frozen=True)
class MotionChannelIR(IRRecord):
    channel_id: str
    target: MotionTargetRef
    curve: AnimationCurveIR | None = None
    sampled_resource: ResourceRef | None = None
    semantic_refs: tuple[SemanticRef, ...] = ()

    NESTED: ClassVar = {"target": one(MotionTargetRef), "curve": optional(AnimationCurveIR), "sampled_resource": optional(ResourceRef), "semantic_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "channel_id", require_identifier(self.channel_id, "channel_id"))
        object.__setattr__(self, "target", MotionTargetRef.coerce(self.target, "target"))
        if (self.curve is None) == (self.sampled_resource is None):
            raise IRSchemaError("motion channel requires exactly one inline curve or deferred sample resource")
        if self.curve is not None:
            object.__setattr__(self, "curve", AnimationCurveIR.coerce(self.curve, "curve"))
            if self.curve.output_type != self.target.value_type:
                raise IRIntegrityError("motion curve value type differs from semantic target type")
        if self.sampled_resource is not None:
            object.__setattr__(self, "sampled_resource", ResourceRef.coerce(self.sampled_resource, "sampled_resource"))
        refs = tuple(SemanticRef.coerce(item, "semantic_refs[]") for item in self.semantic_refs)
        object.__setattr__(self, "semantic_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))


@dataclass(frozen=True)
class MotionIR(IRRecord):
    motion_id: str
    channels: tuple[MotionChannelIR, ...]
    source_refs: tuple[SemanticRef, ...]

    NESTED: ClassVar = {"channels": many(MotionChannelIR), "source_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "motion_id", require_identifier(self.motion_id, "motion_id"))
        channels = tuple(MotionChannelIR.coerce(item, "channels[]") for item in self.channels)
        if len({item.channel_id for item in channels}) != len(channels):
            raise IRSchemaError("motion channel ids must be unique")
        object.__setattr__(self, "channels", tuple(sorted(channels, key=lambda item: item.channel_id)))
        refs = tuple(SemanticRef.coerce(item, "source_refs[]") for item in self.source_refs)
        object.__setattr__(self, "source_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))
        if not self.source_refs:
            raise IRIntegrityError("motion representation requires source refs")


@dataclass(frozen=True)
class MotionClipIR(IRRecord):
    clip_id: str
    time_range: TimeRangeIR
    motion_ref: str
    loop_mode: str = "once"

    NESTED: ClassVar = {"time_range": one(TimeRangeIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "clip_id", require_identifier(self.clip_id, "clip_id"))
        object.__setattr__(self, "time_range", TimeRangeIR.coerce(self.time_range, "time_range"))
        object.__setattr__(self, "motion_ref", require_identifier(self.motion_ref, "motion_ref"))
        object.__setattr__(self, "loop_mode", require_identifier(self.loop_mode, "loop_mode"))
        if self.loop_mode not in {"once", "loop", "ping_pong"}:
            raise IRSchemaError("unsupported motion clip loop mode")


@dataclass(frozen=True)
class MotionLayerIR(IRRecord):
    layer_id: str
    order: int
    clips: tuple[MotionClipIR, ...]
    blend_semantics: str = "replace"

    NESTED: ClassVar = {"clips": many(MotionClipIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "layer_id", require_identifier(self.layer_id, "layer_id"))
        non_negative_int(self.order, "order")
        object.__setattr__(self, "blend_semantics", require_identifier(self.blend_semantics, "blend_semantics"))
        clips = tuple(MotionClipIR.coerce(item, "clips[]") for item in self.clips)
        if len({item.clip_id for item in clips}) != len(clips):
            raise IRSchemaError("motion clip ids must be unique within a layer")
        object.__setattr__(self, "clips", tuple(sorted(clips, key=lambda item: (item.time_range.start.ticks, item.clip_id))))


@dataclass(frozen=True)
class TemporalSamplingIR(IRRecord):
    sampling_id: str
    range: TimeRangeIR
    sample_period: Fraction
    sample_count: int
    sampled_resource: ResourceRef | None = None

    NESTED: ClassVar = {"range": one(TimeRangeIR), "sample_period": fraction, "sampled_resource": optional(ResourceRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "sampling_id", require_identifier(self.sampling_id, "sampling_id"))
        object.__setattr__(self, "range", TimeRangeIR.coerce(self.range, "range"))
        period = _fraction(self.sample_period, "sample_period")
        if period <= 0:
            raise IRSchemaError("sample_period must be positive")
        object.__setattr__(self, "sample_period", period)
        positive_int(self.sample_count, "sample_count")
        DEFAULT_LIMITS.require("max_temporal_samples", self.sample_count)
        if self.range.duration_ticks // period + 1 > self.sample_count:
            raise IRIntegrityError("sample_count does not cover declared range and period")
        if self.sampled_resource is not None:
            object.__setattr__(self, "sampled_resource", ResourceRef.coerce(self.sampled_resource, "sampled_resource"))


@dataclass(frozen=True)
class TemporalMarkerIR(IRRecord):
    marker_id: str
    time: TimePointIR
    marker_kind: str
    semantic_refs: tuple[str, ...] = ()

    NESTED: ClassVar = {"time": one(TimePointIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "marker_id", require_identifier(self.marker_id, "marker_id"))
        object.__setattr__(self, "time", TimePointIR.coerce(self.time, "time"))
        object.__setattr__(self, "marker_kind", require_identifier(self.marker_kind, "marker_kind"))
        object.__setattr__(self, "semantic_refs", tuple(sorted(set(require_identifier(item, "semantic_refs[]") for item in self.semantic_refs))))


@dataclass(frozen=True)
class TemporalRelationIR(IRRecord):
    relation_id: str
    relation_kind: str
    source_time: TimePointIR
    target_time: TimePointIR
    tolerance_ticks: Fraction | None = None

    NESTED: ClassVar = {"source_time": one(TimePointIR), "target_time": one(TimePointIR), "tolerance_ticks": lambda value, path: None if value is None else fraction(value, path)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "relation_id", require_identifier(self.relation_id, "relation_id"))
        object.__setattr__(self, "relation_kind", require_identifier(self.relation_kind, "relation_kind"))
        object.__setattr__(self, "source_time", TimePointIR.coerce(self.source_time, "source_time"))
        object.__setattr__(self, "target_time", TimePointIR.coerce(self.target_time, "target_time"))
        if self.tolerance_ticks is not None:
            tolerance = _fraction(self.tolerance_ticks, "tolerance_ticks")
            if tolerance < 0:
                raise IRSchemaError("tolerance_ticks cannot be negative")
            object.__setattr__(self, "tolerance_ticks", tolerance)


@dataclass(frozen=True)
class TemporalConversionReceipt(IRRecord):
    receipt_id: str
    source_digest: str
    source_reference: TemporalReferenceIR
    target_reference: TemporalReferenceIR
    conversion_version: str = "rational-time-v1"

    NESTED: ClassVar = {"source_reference": one(TemporalReferenceIR), "target_reference": one(TemporalReferenceIR)}

    def __post_init__(self) -> None:
        from .versions import require_digest
        object.__setattr__(self, "receipt_id", require_identifier(self.receipt_id, "receipt_id"))
        object.__setattr__(self, "source_digest", require_digest(self.source_digest, "source_digest"))
        for name in ("source_reference", "target_reference"):
            object.__setattr__(self, name, TemporalReferenceIR.coerce(getattr(self, name), name))
        if self.source_reference.epoch != self.target_reference.epoch:
            raise IRIntegrityError("temporal conversion requires an explicit shared epoch")
        object.__setattr__(self, "conversion_version", require_version(self.conversion_version))


def convert_time_point(point: TimePointIR, source: TemporalReferenceIR, target: TemporalReferenceIR, receipt_id: str = "time-conversion") -> tuple[TimePointIR, TemporalConversionReceipt]:
    point = TimePointIR.coerce(point, "point")
    source, target = TemporalReferenceIR.coerce(source, "source"), TemporalReferenceIR.coerce(target, "target")
    if point.reference_id != source.reference_id or source.epoch != target.epoch:
        raise IRIntegrityError("time point does not match explicit source reference/epoch")
    seconds = point.ticks / source.ticks_per_second
    converted = TimePointIR(target.reference_id, seconds * target.ticks_per_second, point.layer)
    receipt = TemporalConversionReceipt(receipt_id, content_digest(point.to_payload()), source, target)
    return converted, receipt


def sample_curve(curve: AnimationCurveIR, sampling: TemporalSamplingIR, *, limits: IRLimits = DEFAULT_LIMITS) -> tuple[tuple[TimePointIR, float], ...]:
    curve, sampling = AnimationCurveIR.coerce(curve, "curve"), TemporalSamplingIR.coerce(sampling, "sampling")
    limits.require("max_temporal_samples", sampling.sample_count)
    if curve.keys[0].time.reference_id != sampling.range.start.reference_id or curve.keys[0].time.layer is not sampling.range.start.layer:
        raise IRIntegrityError("curve and sample range use different time basis")
    required_count = int(sampling.range.duration_ticks // sampling.sample_period) + 1
    if sampling.sample_count < required_count:
        raise IRLimitError("sample_count cannot cover requested range")
    samples = []
    current = sampling.range.start.ticks
    for _ in range(sampling.sample_count):
        if current > sampling.range.end.ticks:
            break
        point = TimePointIR(sampling.range.start.reference_id, current, sampling.range.start.layer)
        samples.append((point, curve.evaluate(point)))
        current += sampling.sample_period
    if not samples:
        raise IRLimitError("sample_count cannot cover requested range")
    return tuple(samples)
