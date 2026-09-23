"""Typed deferred resource and interface/payload boundary records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Mapping

from iris_intent.identity import SemanticRef

from .base import IRRecord, many, one, optional
from .common import deep_freeze, identifiers, non_negative_int, require_enum
from .enums import RequirementLevel
from .errors import IRSchemaError
from .identity import ResourceRef
from .versions import require_identifier

__all__ = ["ResourceRequirement", "InterfacePort", "IRInterfaceCapsule", "PayloadDescriptor", "TextureResourceIR"]


@dataclass(frozen=True)
class ResourceRequirement(IRRecord):
    requirement_id: str
    resource_kind: str
    level: RequirementLevel
    semantic_ref: SemanticRef | None = None

    NESTED: ClassVar = {"semantic_ref": optional(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "requirement_id", require_identifier(self.requirement_id, "requirement_id"))
        object.__setattr__(self, "resource_kind", require_identifier(self.resource_kind, "resource_kind"))
        object.__setattr__(self, "level", require_enum(self.level, RequirementLevel, "level"))
        if self.semantic_ref is not None:
            object.__setattr__(self, "semantic_ref", SemanticRef.coerce(self.semantic_ref, "semantic_ref"))
        if self.level is RequirementLevel.REQUIRED and self.semantic_ref is None:
            raise IRSchemaError("required resource requirements need an admitted semantic ref")


@dataclass(frozen=True)
class InterfacePort(IRRecord):
    port_id: str
    direction: str
    value_type: str
    requirement: RequirementLevel = RequirementLevel.REQUIRED
    semantic_refs: tuple[SemanticRef, ...] = ()

    NESTED: ClassVar = {"semantic_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "port_id", require_identifier(self.port_id, "port_id"))
        object.__setattr__(self, "direction", require_identifier(self.direction, "direction"))
        if self.direction not in {"input", "output", "bidirectional"}:
            raise IRSchemaError("interface port direction must be input, output, or bidirectional")
        object.__setattr__(self, "value_type", require_identifier(self.value_type, "value_type"))
        object.__setattr__(self, "requirement", require_enum(self.requirement, RequirementLevel, "requirement"))
        refs = tuple(SemanticRef.coerce(item, "semantic_refs[]") for item in self.semantic_refs)
        object.__setattr__(self, "semantic_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))
        if self.requirement is RequirementLevel.REQUIRED and not self.semantic_refs:
            raise IRSchemaError("required interface ports require semantic trace refs")


@dataclass(frozen=True)
class IRInterfaceCapsule(IRRecord):
    capsule_id: str
    ports: tuple[InterfacePort, ...] = ()
    requirements: tuple[ResourceRequirement, ...] = ()
    summary: Mapping[str, Any] | None = None
    payload_resource_refs: tuple[ResourceRef, ...] = ()

    NESTED: ClassVar = {
        "ports": many(InterfacePort),
        "requirements": many(ResourceRequirement),
        "payload_resource_refs": many(ResourceRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "capsule_id", require_identifier(self.capsule_id, "capsule_id"))
        ports = tuple(InterfacePort.coerce(item, "ports[]") for item in self.ports)
        if len({item.port_id for item in ports}) != len(ports):
            raise IRSchemaError("interface port ids must be unique")
        requirements = tuple(ResourceRequirement.coerce(item, "requirements[]") for item in self.requirements)
        if len({item.requirement_id for item in requirements}) != len(requirements):
            raise IRSchemaError("resource requirement ids must be unique")
        object.__setattr__(self, "ports", tuple(sorted(ports, key=lambda item: item.port_id)))
        object.__setattr__(self, "requirements", tuple(sorted(requirements, key=lambda item: item.requirement_id)))
        if self.summary is not None:
            object.__setattr__(self, "summary", deep_freeze(self.summary, "summary"))
        refs = tuple(ResourceRef.coerce(item, "payload_resource_refs[]") for item in self.payload_resource_refs)
        object.__setattr__(self, "payload_resource_refs", tuple(sorted({item.identity_key: item for item in refs}.values(), key=lambda item: item.resource_id)))


@dataclass(frozen=True)
class PayloadDescriptor(IRRecord):
    resource: ResourceRef
    deferred: bool = True
    expected_size_bytes: int | None = None
    inline_digest: str | None = None

    NESTED: ClassVar = {"resource": one(ResourceRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "resource", ResourceRef.coerce(self.resource, "resource"))
        if not isinstance(self.deferred, bool):
            raise IRSchemaError("deferred must be bool")
        if self.expected_size_bytes is not None:
            non_negative_int(self.expected_size_bytes, "expected_size_bytes")
        if self.inline_digest is not None:
            from .versions import require_digest
            object.__setattr__(self, "inline_digest", require_digest(self.inline_digest, "inline_digest"))
        if self.deferred and self.inline_digest is not None:
            raise IRSchemaError("deferred payload cannot claim an inline payload digest")


@dataclass(frozen=True)
class TextureResourceIR(IRRecord):
    resource: ResourceRef
    color_space: str
    encoding: str
    channel_semantics: tuple[str, ...] = ()
    alpha_mode: str = "OPAQUE"

    NESTED: ClassVar = {"resource": one(ResourceRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "resource", ResourceRef.coerce(self.resource, "resource"))
        object.__setattr__(self, "color_space", require_identifier(self.color_space, "color_space"))
        object.__setattr__(self, "encoding", require_identifier(self.encoding, "encoding"))
        object.__setattr__(self, "channel_semantics", identifiers(self.channel_semantics, "channel_semantics"))
        object.__setattr__(self, "alpha_mode", require_identifier(self.alpha_mode, "alpha_mode"))
