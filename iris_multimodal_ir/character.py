"""Portable character, skeleton, deformation, and attachment representation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Mapping

from .base import IRRecord, many, one, optional
from .common import deep_freeze, identifiers
from .errors import IRIntegrityError, IRSchemaError
from .identity import AssetDNARef, IRNodeRef, IdentityAnchorRef, PersonaDNARef, ResourceRef
from .limits import DEFAULT_LIMITS, IRLimits
from .versions import require_identifier, require_text

__all__ = ["JointIR", "SkeletonIR", "JointWeight", "SkinBindingIR", "MorphChannelIR", "AttachmentPortIR", "CharacterIdentityIR"]


@dataclass(frozen=True)
class JointIR(IRRecord):
    joint_id: str
    semantic_name: str
    parent_joint_id: str | None = None
    rest_transform: tuple[float, ...] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
    bind_transform: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "joint_id", require_identifier(self.joint_id, "joint_id"))
        object.__setattr__(self, "semantic_name", require_identifier(self.semantic_name, "semantic_name"))
        if self.parent_joint_id is not None:
            object.__setattr__(self, "parent_joint_id", require_identifier(self.parent_joint_id, "parent_joint_id"))
        import math
        if any(isinstance(value, bool) for value in self.rest_transform):
            raise IRSchemaError("rest_transform cannot contain bool values")
        rest = tuple(float(value) for value in self.rest_transform)
        if len(rest) != 9 or any(not math.isfinite(value) for value in rest):
            raise IRSchemaError("rest_transform must contain nine finite translation/rotation/scale values")
        object.__setattr__(self, "rest_transform", rest)
        if self.bind_transform is not None:
            if any(isinstance(value, bool) for value in self.bind_transform):
                raise IRSchemaError("bind_transform cannot contain bool values")
            bind = tuple(float(value) for value in self.bind_transform)
            if len(bind) != 9 or any(not math.isfinite(value) for value in bind):
                raise IRSchemaError("bind_transform must contain nine finite values")
            object.__setattr__(self, "bind_transform", bind)


@dataclass(frozen=True)
class SkeletonIR(IRRecord):
    skeleton_id: str
    root_joint_ids: tuple[str, ...]
    joints: tuple[JointIR, ...]
    spatial_reference_id: str

    NESTED: ClassVar = {"joints": many(JointIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "skeleton_id", require_identifier(self.skeleton_id, "skeleton_id"))
        object.__setattr__(self, "spatial_reference_id", require_identifier(self.spatial_reference_id, "spatial_reference_id"))
        object.__setattr__(self, "root_joint_ids", identifiers(self.root_joint_ids, "root_joint_ids"))
        joints = tuple(JointIR.coerce(item, "joints[]") for item in self.joints)
        ids = {item.joint_id for item in joints}
        if len(ids) != len(joints) or not joints:
            raise IRIntegrityError("skeleton joint ids must be non-empty and unique")
        roots = {item.joint_id for item in joints if item.parent_joint_id is None}
        if set(self.root_joint_ids) != roots:
            raise IRIntegrityError("skeleton root ids do not match joint parent topology")
        for joint in joints:
            if joint.parent_joint_id is not None and joint.parent_joint_id not in ids:
                raise IRIntegrityError(f"joint {joint.joint_id} has a missing parent")
        parents = {item.joint_id: item.parent_joint_id for item in joints}
        for joint in joints:
            seen: set[str] = set()
            current: str | None = joint.joint_id
            while current is not None:
                if current in seen:
                    raise IRIntegrityError("skeleton hierarchy contains a cycle")
                seen.add(current)
                current = parents[current]
        object.__setattr__(self, "joints", tuple(sorted(joints, key=lambda item: item.joint_id)))


@dataclass(frozen=True, order=True)
class JointWeight(IRRecord):
    joint_id: str
    weight: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "joint_id", require_identifier(self.joint_id, "joint_id"))
        import math
        if isinstance(self.weight, bool) or not isinstance(self.weight, (int, float)) or not math.isfinite(self.weight) or not 0.0 <= self.weight <= 1.0:
            raise IRSchemaError("joint weight must be finite and between 0 and 1")


@dataclass(frozen=True)
class SkinBindingIR(IRRecord):
    binding_id: str
    skeleton_id: str
    geometry_ref: IRNodeRef
    weights_by_vertex: Mapping[str, tuple[JointWeight, ...]]
    normalization_tolerance: float = 1e-6

    NESTED: ClassVar = {"geometry_ref": one(IRNodeRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "binding_id", require_identifier(self.binding_id, "binding_id"))
        object.__setattr__(self, "skeleton_id", require_identifier(self.skeleton_id, "skeleton_id"))
        object.__setattr__(self, "geometry_ref", IRNodeRef.coerce(self.geometry_ref, "geometry_ref"))
        import math
        tolerance = float(self.normalization_tolerance)
        if not math.isfinite(tolerance) or tolerance < 0 or tolerance > 0.01:
            raise IRSchemaError("normalization_tolerance must be finite and in [0, 0.01]")
        object.__setattr__(self, "normalization_tolerance", tolerance)
        if not isinstance(self.weights_by_vertex, Mapping):
            raise IRSchemaError("weights_by_vertex must be a mapping")
        normalized: dict[str, tuple[JointWeight, ...]] = {}
        for vertex_id, raw_weights in self.weights_by_vertex.items():
            key = require_identifier(vertex_id, "vertex_id")
            weights = tuple(JointWeight.coerce(item, "weights_by_vertex[]") for item in raw_weights)
            if not weights or len({item.joint_id for item in weights}) != len(weights):
                raise IRIntegrityError(f"vertex {key} needs unique skin weights")
            if abs(sum(item.weight for item in weights) - 1.0) > tolerance:
                raise IRIntegrityError(f"skin weights for vertex {key} do not sum to one within tolerance")
            normalized[key] = tuple(sorted(weights, key=lambda item: item.joint_id))
        object.__setattr__(self, "weights_by_vertex", deep_freeze(normalized, "weights_by_vertex"))

    def validate_against(self, skeleton: SkeletonIR, *, limits: IRLimits = DEFAULT_LIMITS) -> None:
        if skeleton.skeleton_id != self.skeleton_id:
            raise IRIntegrityError("skin binding references another skeleton")
        joints = {item.joint_id for item in skeleton.joints}
        for vertex_id, weights in self.weights_by_vertex.items():
            limits.require("max_fanout", len(weights))
            unknown = {item.joint_id for item in weights} - joints
            if unknown:
                raise IRIntegrityError(f"skin weights reference unknown joints: {sorted(unknown)}")


@dataclass(frozen=True)
class MorphChannelIR(IRRecord):
    channel_id: str
    semantic_path: str
    geometry_ref: IRNodeRef
    minimum: float = 0.0
    maximum: float = 1.0
    default: float = 0.0
    value_resource: ResourceRef | None = None

    NESTED: ClassVar = {"geometry_ref": one(IRNodeRef), "value_resource": optional(ResourceRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "channel_id", require_identifier(self.channel_id, "channel_id"))
        object.__setattr__(self, "semantic_path", require_text(self.semantic_path, "semantic_path", maximum=256))
        object.__setattr__(self, "geometry_ref", IRNodeRef.coerce(self.geometry_ref, "geometry_ref"))
        import math
        values = tuple(float(value) for value in (self.minimum, self.maximum, self.default))
        if any(not math.isfinite(value) for value in values) or values[0] > values[2] or values[2] > values[1]:
            raise IRSchemaError("morph channel requires finite minimum <= default <= maximum")
        object.__setattr__(self, "minimum", values[0])
        object.__setattr__(self, "maximum", values[1])
        object.__setattr__(self, "default", values[2])
        if self.value_resource is not None:
            object.__setattr__(self, "value_resource", ResourceRef.coerce(self.value_resource, "value_resource"))


@dataclass(frozen=True)
class AttachmentPortIR(IRRecord):
    port_id: str
    owner_ref: IRNodeRef
    semantic_type: str
    cardinality: str = "one"
    required: bool = False

    NESTED: ClassVar = {"owner_ref": one(IRNodeRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "port_id", require_identifier(self.port_id, "port_id"))
        object.__setattr__(self, "owner_ref", IRNodeRef.coerce(self.owner_ref, "owner_ref"))
        object.__setattr__(self, "semantic_type", require_identifier(self.semantic_type, "semantic_type"))
        object.__setattr__(self, "cardinality", require_identifier(self.cardinality, "cardinality"))
        if self.cardinality not in {"one", "optional", "many"}:
            raise IRSchemaError("attachment cardinality must be one, optional, or many")
        if not isinstance(self.required, bool):
            raise IRSchemaError("required must be bool")


@dataclass(frozen=True)
class CharacterIdentityIR(IRRecord):
    character_ref: IRNodeRef
    identity_anchor: IdentityAnchorRef | None = None
    asset_dna: AssetDNARef | None = None
    persona_dna: PersonaDNARef | None = None

    NESTED: ClassVar = {"character_ref": one(IRNodeRef), "identity_anchor": optional(IdentityAnchorRef), "asset_dna": optional(AssetDNARef), "persona_dna": optional(PersonaDNARef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "character_ref", IRNodeRef.coerce(self.character_ref, "character_ref"))
        for name, kind in (("identity_anchor", IdentityAnchorRef), ("asset_dna", AssetDNARef), ("persona_dna", PersonaDNARef)):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, kind.coerce(value, name))
