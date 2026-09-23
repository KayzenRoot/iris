"""Explicit unit, frame, transform, camera, and lighting semantics."""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any, ClassVar

from .base import IRRecord, fraction, many, one, optional
from .common import require_enum
from .enums import Physicality, ProjectionKind, QuantityDimension
from .errors import IRIntegrityError, IRSchemaError
from .identity import IRNodeRef
from .schema import SchemaFamilyRef
from .versions import content_digest, require_finite_number, require_identifier, require_text, require_version

__all__ = [
    "QuantityIR", "SpatialReferenceIR", "CoordinateFrameIR", "TransformOperation", "TransformChainIR",
    "ResolvedTransform", "SpatialConversionReceipt", "convert_quantity", "resolve_transform",
    "CameraOpticsIR", "CameraIR", "LightShapingIR", "ShadowIntentIR", "LightInfluenceIR", "LightIR", "SpatialRegionIR",
]


_UNIT_SCALE: dict[str, tuple[QuantityDimension, Decimal]] = {
    "m": (QuantityDimension.LENGTH, Decimal("1")), "cm": (QuantityDimension.LENGTH, Decimal("0.01")),
    "mm": (QuantityDimension.LENGTH, Decimal("0.001")), "km": (QuantityDimension.LENGTH, Decimal("1000")),
    "inch": (QuantityDimension.LENGTH, Decimal("0.0254")), "ft": (QuantityDimension.LENGTH, Decimal("0.3048")),
    "s": (QuantityDimension.TIME, Decimal("1")), "ms": (QuantityDimension.TIME, Decimal("0.001")),
    "us": (QuantityDimension.TIME, Decimal("0.000001")), "ns": (QuantityDimension.TIME, Decimal("0.000000001")),
    "Hz": (QuantityDimension.FREQUENCY, Decimal("1")), "kHz": (QuantityDimension.FREQUENCY, Decimal("1000")),
    "rad": (QuantityDimension.ANGLE, Decimal("1")), "deg": (QuantityDimension.ANGLE, Decimal("0.017453292519943295769236907684886127")),
    "kg": (QuantityDimension.MASS, Decimal("1")), "g": (QuantityDimension.MASS, Decimal("0.001")),
    "K": (QuantityDimension.TEMPERATURE, Decimal("1")), "cd": (QuantityDimension.LUMINOUS_INTENSITY, Decimal("1")),
    "lux": (QuantityDimension.ILLUMINANCE, Decimal("1")), "nit": (QuantityDimension.LUMINANCE, Decimal("1")),
    "1": (QuantityDimension.DIMENSIONLESS, Decimal("1")),
}


def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool):
        raise IRSchemaError(f"{field} cannot be bool")
    try:
        result = Decimal(value.numerator) / Decimal(value.denominator) if isinstance(value, Fraction) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError, ZeroDivisionError):
        raise IRSchemaError(f"{field} must be a finite numeric value") from None
    if not result.is_finite():
        raise IRSchemaError(f"{field} must be finite")
    return result


@dataclass(frozen=True)
class QuantityIR(IRRecord):
    value: int | float | str | Fraction
    unit: str
    dimension: QuantityDimension
    semantic_ref: Any | None = None

    @staticmethod
    def _number(value: Any, path: str) -> Any:
        if isinstance(value, dict) and set(value) == {"numerator", "denominator"}:
            return fraction(value, path)
        return value

    def __post_init__(self) -> None:
        value = self._number(self.value, "value")
        object.__setattr__(self, "value", value)
        if not isinstance(self.value, (int, float, str, Fraction)) or isinstance(self.value, bool):
            raise IRSchemaError("quantity value must be a finite canonical number")
        numeric = _decimal(self.value, "value")
        if isinstance(self.value, str):
            if not self.value or len(self.value) > 128:
                raise IRSchemaError("numeric string must contain 1..128 characters")
            canonical: Any = format(numeric.normalize(), "f")
        else:
            canonical = self.value
        object.__setattr__(self, "value", canonical)
        object.__setattr__(self, "unit", require_text(self.unit, "unit", maximum=32))
        object.__setattr__(self, "dimension", require_enum(self.dimension, QuantityDimension, "dimension"))
        if self.semantic_ref is not None:
            from iris_intent.identity import SemanticRef
            object.__setattr__(self, "semantic_ref", SemanticRef.coerce(self.semantic_ref, "semantic_ref"))
        spec = _UNIT_SCALE.get(self.unit)
        if spec is None and self.dimension is not QuantityDimension.OTHER:
            raise IRSchemaError(f"unknown unit {self.unit!r}; use an explicit extension for custom units")
        if spec is not None and spec[0] is not self.dimension:
            raise IRSchemaError(f"unit {self.unit!r} is not a {self.dimension.value} unit")


@dataclass(frozen=True)
class SpatialReferenceIR(IRRecord):
    reference_id: str
    length_unit: str
    angle_unit: str = "rad"
    handedness: str = "RIGHT"
    up_axis: str = "Y"
    forward_axis: str = "-Z"
    version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "reference_id", require_identifier(self.reference_id, "reference_id"))
        for name in ("length_unit", "angle_unit"):
            object.__setattr__(self, name, require_text(getattr(self, name), name, maximum=32))
        for name in ("handedness", "up_axis", "forward_axis"):
            object.__setattr__(self, name, require_text(getattr(self, name), name, maximum=8))
        object.__setattr__(self, "version", require_version(self.version))
        if self.handedness not in {"LEFT", "RIGHT"} or self.up_axis not in {"X", "Y", "Z", "-X", "-Y", "-Z"}:
            raise IRSchemaError("spatial handedness/up axis is invalid")
        if self.forward_axis not in {"X", "Y", "Z", "-X", "-Y", "-Z"} or self.forward_axis[-1] == self.up_axis[-1]:
            raise IRSchemaError("forward and up axes must be distinct valid axes")
        if _UNIT_SCALE.get(self.length_unit, (None,))[0] is not QuantityDimension.LENGTH:
            raise IRSchemaError("spatial length_unit must be a registered length unit")
        if _UNIT_SCALE.get(self.angle_unit, (None,))[0] is not QuantityDimension.ANGLE:
            raise IRSchemaError("spatial angle_unit must be a registered angle unit")


@dataclass(frozen=True)
class CoordinateFrameIR(IRRecord):
    frame_id: str
    spatial_reference_id: str
    parent_frame_id: str | None = None
    origin: tuple[QuantityIR, ...] = ()
    semantic_role: str = "local"

    NESTED: ClassVar = {"origin": many(QuantityIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "frame_id", require_identifier(self.frame_id, "frame_id"))
        object.__setattr__(self, "spatial_reference_id", require_identifier(self.spatial_reference_id, "spatial_reference_id"))
        if self.parent_frame_id is not None:
            object.__setattr__(self, "parent_frame_id", require_identifier(self.parent_frame_id, "parent_frame_id"))
        values = tuple(QuantityIR.coerce(item, "origin[]") for item in self.origin)
        if len(values) != 3 or any(item.dimension is not QuantityDimension.LENGTH for item in values):
            raise IRSchemaError("frame origin must have three explicit length quantities")
        if len({item.unit for item in values}) != 1:
            raise IRSchemaError("frame origin components must share one length unit")
        object.__setattr__(self, "origin", values)
        object.__setattr__(self, "semantic_role", require_identifier(self.semantic_role, "semantic_role"))


@dataclass(frozen=True)
class TransformOperation(IRRecord):
    operation_id: str
    operation: str
    values: tuple[float, float, float]
    unit: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation_id", require_identifier(self.operation_id, "operation_id"))
        object.__setattr__(self, "operation", require_identifier(self.operation, "operation"))
        if self.operation not in {"translate", "rotate_euler", "scale"}:
            raise IRSchemaError("transform operation must be translate, rotate_euler, or scale")
        values = tuple(float(require_finite_number(value, "values[]")) for value in self.values)
        if len(values) != 3:
            raise IRSchemaError("transform operations require exactly three values")
        if self.operation == "scale" and any(value == 0 for value in values):
            raise IRSchemaError("zero scale is not invertible and is not allowed in canonical transforms")
        if self.operation in {"translate", "rotate_euler"} and self.unit is None:
            raise IRSchemaError(f"{self.operation} requires an explicit unit")
        if self.unit is not None:
            object.__setattr__(self, "unit", require_text(self.unit, "unit", maximum=32))
        object.__setattr__(self, "values", values)


@dataclass(frozen=True)
class TransformChainIR(IRRecord):
    chain_id: str
    source_frame_id: str
    target_frame_id: str
    operations: tuple[TransformOperation, ...]
    authored: bool = True
    trace_digest: str | None = None

    NESTED: ClassVar = {"operations": many(TransformOperation)}

    def __post_init__(self) -> None:
        for name in ("chain_id", "source_frame_id", "target_frame_id"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        operations = tuple(TransformOperation.coerce(item, "operations[]") for item in self.operations)
        if len({item.operation_id for item in operations}) != len(operations):
            raise IRSchemaError("transform operation ids must be unique")
        object.__setattr__(self, "operations", operations)  # order is semantic and deliberately preserved
        if not isinstance(self.authored, bool):
            raise IRSchemaError("authored must be bool")
        if self.trace_digest is not None:
            from .versions import require_digest
            object.__setattr__(self, "trace_digest", require_digest(self.trace_digest, "trace_digest"))

    @property
    def digest(self) -> str:
        return content_digest(self.to_payload())


@dataclass(frozen=True)
class ResolvedTransform(IRRecord):
    source_chain_digest: str
    matrix4x4: tuple[float, ...]
    resolution_version: str = "transform-v1"
    derived: bool = True

    def __post_init__(self) -> None:
        from .versions import require_digest
        object.__setattr__(self, "source_chain_digest", require_digest(self.source_chain_digest, "source_chain_digest"))
        matrix = tuple(float(require_finite_number(item, "matrix4x4[]")) for item in self.matrix4x4)
        if len(matrix) != 16:
            raise IRSchemaError("resolved transform must have sixteen finite matrix elements")
        object.__setattr__(self, "matrix4x4", matrix)
        object.__setattr__(self, "resolution_version", require_version(self.resolution_version))
        if self.derived is not True:
            raise IRSchemaError("ResolvedTransform is derived data; authored transforms use TransformChainIR")


@dataclass(frozen=True)
class SpatialConversionReceipt(IRRecord):
    conversion_id: str
    source: QuantityIR
    target_unit: str
    result_value: str
    conversion_factor: str
    source_digest: str
    conversion_version: str = "unit-conversion-v1"

    NESTED: ClassVar = {"source": one(QuantityIR)}

    def __post_init__(self) -> None:
        from .versions import require_digest
        object.__setattr__(self, "conversion_id", require_identifier(self.conversion_id, "conversion_id"))
        object.__setattr__(self, "source", QuantityIR.coerce(self.source, "source"))
        object.__setattr__(self, "target_unit", require_text(self.target_unit, "target_unit", maximum=32))
        object.__setattr__(self, "result_value", require_text(self.result_value, "result_value", maximum=128))
        object.__setattr__(self, "conversion_factor", require_text(self.conversion_factor, "conversion_factor", maximum=128))
        object.__setattr__(self, "source_digest", require_digest(self.source_digest, "source_digest"))
        object.__setattr__(self, "conversion_version", require_version(self.conversion_version))


def convert_quantity(quantity: QuantityIR, target_unit: str, conversion_id: str = "conversion") -> tuple[QuantityIR, SpatialConversionReceipt]:
    quantity = QuantityIR.coerce(quantity, "quantity")
    target_unit = require_text(target_unit, "target_unit", maximum=32)
    source_spec, target_spec = _UNIT_SCALE.get(quantity.unit), _UNIT_SCALE.get(target_unit)
    if source_spec is None or target_spec is None or source_spec[0] is not target_spec[0] or source_spec[0] is not quantity.dimension:
        raise IRIntegrityError("unit conversion requires compatible registered dimensions")
    factor = source_spec[1] / target_spec[1]
    result = _decimal(quantity.value, "value") * factor
    canonical_result = format(result.normalize(), "f")
    converted = QuantityIR(canonical_result, target_unit, quantity.dimension, quantity.semantic_ref)
    receipt = SpatialConversionReceipt(conversion_id, quantity, target_unit, canonical_result, format(factor.normalize(), "f"), content_digest(quantity.to_payload()))
    return converted, receipt


def resolve_transform(chain: TransformChainIR, *, spatial: SpatialReferenceIR | None = None) -> ResolvedTransform:
    chain = TransformChainIR.coerce(chain, "chain")
    matrix = _identity_matrix()
    for operation in chain.operations:
        values = operation.values
        if operation.operation == "translate":
            assert operation.unit is not None
            if spatial is not None and operation.unit != spatial.length_unit:
                raise IRIntegrityError("translation unit differs from chain spatial reference")
            current = _identity_matrix()
            current[3], current[7], current[11] = values
        elif operation.operation == "scale":
            current = _identity_matrix()
            current[0], current[5], current[10] = values
        else:
            assert operation.unit is not None
            if operation.unit not in {"rad", "deg"}:
                raise IRIntegrityError("rotation requires explicit rad or deg unit")
            angle_factor = float(_UNIT_SCALE[operation.unit][1])
            ax, ay, az = (item * angle_factor for item in values)
            rx, ry, rz = _rotation_x(ax), _rotation_y(ay), _rotation_z(az)
            current = _multiply(_multiply(rx, ry), rz)
        matrix = _multiply(matrix, current)
    return ResolvedTransform(chain.digest, tuple(matrix))


@dataclass(frozen=True)
class CameraOpticsIR(IRRecord):
    projection: ProjectionKind
    filmback_width: QuantityIR
    filmback_height: QuantityIR
    focal_length: QuantityIR | None = None
    focus_distance: QuantityIR | None = None
    f_stop: float | None = None
    depth_of_field_enabled: bool = False
    framing_intent: str | None = None
    extension: SchemaFamilyRef | None = None

    NESTED: ClassVar = {"filmback_width": one(QuantityIR), "filmback_height": one(QuantityIR), "focal_length": optional(QuantityIR), "focus_distance": optional(QuantityIR), "extension": optional(SchemaFamilyRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "projection", require_enum(self.projection, ProjectionKind, "projection"))
        for name in ("filmback_width", "filmback_height", "focal_length", "focus_distance"):
            value = getattr(self, name)
            if value is not None:
                value = QuantityIR.coerce(value, name)
                if value.dimension is not QuantityDimension.LENGTH:
                    raise IRSchemaError(f"{name} must be a length quantity")
                object.__setattr__(self, name, value)
        if self.f_stop is not None:
            value = float(require_finite_number(self.f_stop, "f_stop"))
            if value <= 0:
                raise IRSchemaError("f_stop must be positive")
            object.__setattr__(self, "f_stop", value)
        if not isinstance(self.depth_of_field_enabled, bool):
            raise IRSchemaError("depth_of_field_enabled must be bool")
        if self.depth_of_field_enabled and (self.focus_distance is None or self.f_stop is None):
            raise IRSchemaError("depth of field requires explicit focus distance and f-stop")
        if self.framing_intent is not None:
            object.__setattr__(self, "framing_intent", require_text(self.framing_intent, "framing_intent", maximum=512))
        if self.projection in {ProjectionKind.FISHEYE, ProjectionKind.CALIBRATED, ProjectionKind.OTHER} and self.extension is None:
            raise IRSchemaError("specialized projection requires an explicit versioned extension")
        if self.extension is not None:
            object.__setattr__(self, "extension", SchemaFamilyRef.coerce(self.extension, "extension"))


@dataclass(frozen=True)
class CameraIR(IRRecord):
    camera_ref: IRNodeRef
    optics: CameraOpticsIR
    coordinate_frame_id: str
    trace_ref: str

    NESTED: ClassVar = {"camera_ref": one(IRNodeRef), "optics": one(CameraOpticsIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "camera_ref", IRNodeRef.coerce(self.camera_ref, "camera_ref"))
        object.__setattr__(self, "optics", CameraOpticsIR.coerce(self.optics, "optics"))
        object.__setattr__(self, "coordinate_frame_id", require_identifier(self.coordinate_frame_id, "coordinate_frame_id"))
        object.__setattr__(self, "trace_ref", require_text(self.trace_ref, "trace_ref", maximum=256))


@dataclass(frozen=True)
class LightShapingIR(IRRecord):
    shaping_kind: str
    parameters: dict[str, Any]
    physicality: Physicality

    def __post_init__(self) -> None:
        from .common import deep_freeze
        object.__setattr__(self, "shaping_kind", require_identifier(self.shaping_kind, "shaping_kind"))
        object.__setattr__(self, "parameters", deep_freeze(self.parameters, "parameters"))
        object.__setattr__(self, "physicality", require_enum(self.physicality, Physicality, "physicality"))


@dataclass(frozen=True)
class ShadowIntentIR(IRRecord):
    enabled: bool
    softness: QuantityIR | None = None
    trace_ref: str | None = None

    NESTED: ClassVar = {"softness": optional(QuantityIR)}

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise IRSchemaError("enabled must be bool")
        if self.softness is not None:
            softness = QuantityIR.coerce(self.softness, "softness")
            if softness.dimension is not QuantityDimension.LENGTH:
                raise IRSchemaError("shadow softness must be a length quantity")
            object.__setattr__(self, "softness", softness)
        if self.trace_ref is not None:
            object.__setattr__(self, "trace_ref", require_text(self.trace_ref, "trace_ref", maximum=256))


@dataclass(frozen=True)
class LightInfluenceIR(IRRecord):
    influence_kind: str
    affected_region_ref: IRNodeRef | None = None
    falloff: str = "UNSPECIFIED"

    NESTED: ClassVar = {"affected_region_ref": optional(IRNodeRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "influence_kind", require_identifier(self.influence_kind, "influence_kind"))
        object.__setattr__(self, "falloff", require_identifier(self.falloff, "falloff"))
        if self.affected_region_ref is not None:
            object.__setattr__(self, "affected_region_ref", IRNodeRef.coerce(self.affected_region_ref, "affected_region_ref"))


@dataclass(frozen=True)
class LightIR(IRRecord):
    light_ref: IRNodeRef
    emitter_kind: str
    emission: QuantityIR
    physicality: Physicality
    shaping: LightShapingIR | None = None
    shadow: ShadowIntentIR | None = None
    influences: tuple[LightInfluenceIR, ...] = ()

    NESTED: ClassVar = {"light_ref": one(IRNodeRef), "emission": one(QuantityIR), "shaping": optional(LightShapingIR), "shadow": optional(ShadowIntentIR), "influences": many(LightInfluenceIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "light_ref", IRNodeRef.coerce(self.light_ref, "light_ref"))
        object.__setattr__(self, "emitter_kind", require_identifier(self.emitter_kind, "emitter_kind"))
        object.__setattr__(self, "physicality", require_enum(self.physicality, Physicality, "physicality"))
        emission = QuantityIR.coerce(self.emission, "emission")
        allowed_dimensions = {QuantityDimension.LUMINOUS_INTENSITY, QuantityDimension.ILLUMINANCE, QuantityDimension.LUMINANCE, QuantityDimension.OTHER}
        if self.physicality is not Physicality.PHYSICAL:
            allowed_dimensions.add(QuantityDimension.DIMENSIONLESS)
        if emission.dimension not in allowed_dimensions:
            raise IRSchemaError("light emission needs a typed luminous quantity")
        object.__setattr__(self, "emission", emission)
        for name, kind in (("shaping", LightShapingIR), ("shadow", ShadowIntentIR)):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, kind.coerce(value, name))
        object.__setattr__(self, "influences", tuple(LightInfluenceIR.coerce(item, "influences[]") for item in self.influences))
        if self.physicality is not Physicality.PHYSICAL and self.shaping is None:
            raise IRSchemaError("artistic/non-physical light controls require explicit shaping classification")


@dataclass(frozen=True)
class SpatialRegionIR(IRRecord):
    region_id: str
    coordinate_frame_id: str
    bounds_min: tuple[QuantityIR, QuantityIR, QuantityIR]
    bounds_max: tuple[QuantityIR, QuantityIR, QuantityIR]

    NESTED: ClassVar = {"bounds_min": many(QuantityIR), "bounds_max": many(QuantityIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "region_id", require_identifier(self.region_id, "region_id"))
        object.__setattr__(self, "coordinate_frame_id", require_identifier(self.coordinate_frame_id, "coordinate_frame_id"))
        for name in ("bounds_min", "bounds_max"):
            values = tuple(QuantityIR.coerce(item, f"{name}[]") for item in getattr(self, name))
            if len(values) != 3 or any(item.dimension is not QuantityDimension.LENGTH for item in values):
                raise IRSchemaError("spatial region bounds require three length quantities")
            if len({item.unit for item in values}) != 1:
                raise IRSchemaError("spatial region bounds must use one explicit length unit")
            object.__setattr__(self, name, values)
        for low, high in zip(self.bounds_min, self.bounds_max):
            if _decimal(low.value, "bounds_min") > _decimal(high.value, "bounds_max"):
                raise IRIntegrityError("spatial region min exceeds max")


def _identity_matrix() -> list[float]:
    return [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


def _multiply(left: list[float], right: list[float]) -> list[float]:
    return [sum(left[row * 4 + k] * right[k * 4 + column] for k in range(4)) for row in range(4) for column in range(4)]


def _rotation_x(angle: float) -> list[float]:
    c, s = math.cos(angle), math.sin(angle)
    return [1.0, 0.0, 0.0, 0.0, 0.0, c, -s, 0.0, 0.0, s, c, 0.0, 0.0, 0.0, 0.0, 1.0]


def _rotation_y(angle: float) -> list[float]:
    c, s = math.cos(angle), math.sin(angle)
    return [c, 0.0, s, 0.0, 0.0, 1.0, 0.0, 0.0, -s, 0.0, c, 0.0, 0.0, 0.0, 0.0, 1.0]


def _rotation_z(angle: float) -> list[float]:
    c, s = math.cos(angle), math.sin(angle)
    return [c, -s, 0.0, 0.0, s, c, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
