"""Versioned schema, facet, dialect, and opaque extension declarations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Mapping

from .base import IRRecord, many, one
from .common import deep_freeze, require_enum
from .enums import SchemaUnknownPolicy
from .errors import IRAdmissionError, IRSchemaError
from .versions import CORE_SCHEMA_VERSION, TRANSPORT_VERSION, require_identifier, require_version

__all__ = [
    "SchemaFamilyRef", "FacetRef", "DialectRef", "SchemaManifest", "ExtensionValue",
    "SchemaCompatibilityDeclaration", "CORE_SCHEMA_FAMILIES",
]

CORE_SCHEMA_FAMILIES = frozenset({"iris.multimodal.scene", "iris.multimodal.fragment", "iris.multimodal.material", "iris.multimodal.temporal"})


@dataclass(frozen=True, order=True)
class SchemaFamilyRef(IRRecord):
    family_id: str
    version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "family_id", require_identifier(self.family_id, "family_id"))
        object.__setattr__(self, "version", require_version(self.version))


@dataclass(frozen=True, order=True)
class FacetRef(IRRecord):
    facet_id: str
    version: str
    mandatory: bool = False
    preserve_opaque: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "facet_id", require_identifier(self.facet_id, "facet_id"))
        object.__setattr__(self, "version", require_version(self.version))
        if not isinstance(self.mandatory, bool) or not isinstance(self.preserve_opaque, bool):
            raise IRSchemaError("facet flags must be bool")
        if self.mandatory and self.preserve_opaque:
            raise IRSchemaError("mandatory facets cannot be treated as optional opaque data")


@dataclass(frozen=True, order=True)
class DialectRef(IRRecord):
    dialect_id: str
    version: str
    family: SchemaFamilyRef
    mandatory: bool = False

    NESTED: ClassVar = {"family": one(SchemaFamilyRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "dialect_id", require_identifier(self.dialect_id, "dialect_id"))
        object.__setattr__(self, "version", require_version(self.version))
        object.__setattr__(self, "family", SchemaFamilyRef.coerce(self.family, "family"))
        if not isinstance(self.mandatory, bool):
            raise IRSchemaError("mandatory must be bool")


@dataclass(frozen=True)
class SchemaManifest(IRRecord):
    core_schema_version: str = CORE_SCHEMA_VERSION
    transport_version: str = TRANSPORT_VERSION
    facets: tuple[FacetRef, ...] = ()
    dialects: tuple[DialectRef, ...] = ()
    unknown_policy: SchemaUnknownPolicy = SchemaUnknownPolicy.FAIL_CLOSED

    NESTED: ClassVar = {"facets": many(FacetRef), "dialects": many(DialectRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "core_schema_version", require_version(self.core_schema_version, "core_schema_version"))
        object.__setattr__(self, "transport_version", require_version(self.transport_version, "transport_version"))
        facets = tuple(FacetRef.coerce(item, "facets[]") for item in self.facets)
        dialects = tuple(DialectRef.coerce(item, "dialects[]") for item in self.dialects)
        if len({item.facet_id for item in facets}) != len(facets):
            raise IRSchemaError("facet ids must be unique within a manifest")
        if len({item.dialect_id for item in dialects}) != len(dialects):
            raise IRSchemaError("dialect ids must be unique within a manifest")
        object.__setattr__(self, "facets", tuple(sorted(facets, key=lambda item: item.facet_id)))
        object.__setattr__(self, "dialects", tuple(sorted(dialects, key=lambda item: item.dialect_id)))
        object.__setattr__(self, "unknown_policy", require_enum(self.unknown_policy, SchemaUnknownPolicy, "unknown_policy"))

    def validate_registered(self, *, facets: set[tuple[str, str]], dialects: set[tuple[str, str]]) -> None:
        for facet in self.facets:
            known = (facet.facet_id, facet.version) in facets
            if not known and (facet.mandatory or not facet.preserve_opaque or self.unknown_policy is SchemaUnknownPolicy.FAIL_CLOSED):
                raise IRAdmissionError(f"unknown facet {facet.facet_id}@{facet.version}")
        for dialect in self.dialects:
            if dialect.mandatory and (dialect.dialect_id, dialect.version) not in dialects:
                raise IRAdmissionError(f"unknown mandatory dialect {dialect.dialect_id}@{dialect.version}")


@dataclass(frozen=True)
class ExtensionValue(IRRecord):
    family: SchemaFamilyRef
    value: Mapping[str, Any]
    mandatory: bool = False
    preserve_opaque: bool = False

    NESTED: ClassVar = {"family": one(SchemaFamilyRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "family", SchemaFamilyRef.coerce(self.family, "family"))
        object.__setattr__(self, "value", deep_freeze(self.value, "value"))
        if not isinstance(self.mandatory, bool) or not isinstance(self.preserve_opaque, bool):
            raise IRSchemaError("extension flags must be bool")
        if self.mandatory and self.preserve_opaque:
            raise IRSchemaError("mandatory extensions cannot be opaque-preserved as optional")

    def validate_registered(self, registered: set[tuple[str, str]]) -> None:
        pair = (self.family.family_id, self.family.version)
        if pair not in registered and (self.mandatory or not self.preserve_opaque):
            raise IRAdmissionError(f"unknown extension family {pair[0]}@{pair[1]}")


@dataclass(frozen=True)
class SchemaCompatibilityDeclaration(IRRecord):
    declaration_id: str
    source: SchemaFamilyRef
    target: SchemaFamilyRef
    compatible: bool
    rationale: str
    migration_required: bool = False

    NESTED: ClassVar = {"source": one(SchemaFamilyRef), "target": one(SchemaFamilyRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "declaration_id", require_identifier(self.declaration_id, "declaration_id"))
        object.__setattr__(self, "source", SchemaFamilyRef.coerce(self.source, "source"))
        object.__setattr__(self, "target", SchemaFamilyRef.coerce(self.target, "target"))
        object.__setattr__(self, "rationale", require_version(self.rationale, "rationale"))
        if not isinstance(self.compatible, bool) or not isinstance(self.migration_required, bool):
            raise IRSchemaError("compatibility flags must be bool")
        if self.compatible and self.migration_required:
            raise IRSchemaError("a compatible declaration cannot simultaneously require migration")

    def permits(self, source: SchemaFamilyRef, target: SchemaFamilyRef) -> bool:
        return self.source == source and self.target == target and self.compatible and not self.migration_required
