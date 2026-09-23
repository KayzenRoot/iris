"""Stable schema descriptors, extension disposition, and external capability negotiation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .base import M08Record, freeze_json
from .enums import CompatibilityLevel
from .errors import MicrobenchmarkAdmissionError, MicrobenchmarkIntegrityError, MicrobenchmarkValidationError
from .versions import require_identifier, require_unique, require_version

__all__ = [
    "SchemaVersion", "SchemaDescriptor", "ExtensionDisposition", "ExtensionField",
    "ExternalSchemaProjection", "SchemaNegotiation", "negotiate_schema",
]


@dataclass(frozen=True, order=True)
class SchemaVersion(M08Record):
    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        for field in ("major", "minor", "patch"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise MicrobenchmarkValidationError(f"{field} version component must be a non-negative integer")

    @classmethod
    def parse(cls, value: str) -> SchemaVersion:
        if not isinstance(value, str) or re.fullmatch(r"0|[1-9][0-9]*\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", value) is None:
            raise MicrobenchmarkValidationError("schema version must be strict MAJOR.MINOR.PATCH")
        major, minor, patch = (int(part) for part in value.split("."))
        return cls(major, minor, patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


class ExtensionDisposition:
    OPTIONAL_PRESERVE = "OPTIONAL_PRESERVE"
    REQUIRED_KNOWN = "REQUIRED_KNOWN"
    UNKNOWN_REQUIRED = "UNKNOWN_REQUIRED"


@dataclass(frozen=True)
class SchemaDescriptor(M08Record):
    schema_id: str
    version: SchemaVersion
    required_features: tuple[str, ...]
    optional_features: tuple[str, ...]
    canonicalization_version: str
    fails_unknown_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_identifier(self.schema_id, "schema_id"))
        if not isinstance(self.version, SchemaVersion):
            raise MicrobenchmarkValidationError("version must be SchemaVersion")
        required = tuple(sorted(require_unique(self.required_features, "required_features", maximum=10_000)))
        optional = tuple(sorted(require_unique(self.optional_features, "optional_features", maximum=10_000)))
        if set(required) & set(optional):
            raise MicrobenchmarkIntegrityError("schema feature cannot be both required and optional")
        object.__setattr__(self, "required_features", required)
        object.__setattr__(self, "optional_features", optional)
        object.__setattr__(self, "canonicalization_version", require_version(self.canonicalization_version, "canonicalization_version"))
        if self.fails_unknown_required is not True:
            raise MicrobenchmarkAdmissionError("M08 schema readers must fail closed on unknown required semantics")


@dataclass(frozen=True)
class ExtensionField(M08Record):
    namespace: str
    key: str
    version: str
    disposition: str
    value: dict[str, object]

    def __post_init__(self) -> None:
        for field in ("namespace", "key"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "version", require_version(self.version))
        if self.disposition not in {ExtensionDisposition.OPTIONAL_PRESERVE, ExtensionDisposition.REQUIRED_KNOWN, ExtensionDisposition.UNKNOWN_REQUIRED}:
            raise MicrobenchmarkValidationError("extension disposition is outside the closed schema policy")
        object.__setattr__(self, "value", freeze_json(self.value, "extension value"))
        if self.disposition == ExtensionDisposition.UNKNOWN_REQUIRED:
            raise MicrobenchmarkAdmissionError("unknown required extension semantics fail closed")


@dataclass(frozen=True)
class ExternalSchemaProjection(M08Record):
    projection_id: str
    version: str
    consumer_namespace: str
    schema_id: str
    minimum_version: SchemaVersion
    maximum_version: SchemaVersion
    required_features: tuple[str, ...]
    optional_features: tuple[str, ...]
    supported_compatibility: tuple[CompatibilityLevel, ...]

    def __post_init__(self) -> None:
        for field in ("projection_id", "consumer_namespace", "schema_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "version", require_version(self.version))
        for field in ("minimum_version", "maximum_version"):
            if not isinstance(getattr(self, field), SchemaVersion):
                raise MicrobenchmarkValidationError(f"{field} must be SchemaVersion")
        if self.minimum_version > self.maximum_version:
            raise MicrobenchmarkValidationError("external projection version range must be ordered")
        for field in ("required_features", "optional_features"):
            object.__setattr__(self, field, tuple(sorted(require_unique(getattr(self, field), field, maximum=10_000))))
        if set(self.required_features) & set(self.optional_features):
            raise MicrobenchmarkIntegrityError("external feature cannot be both required and optional")
        if not self.supported_compatibility or any(not isinstance(item, CompatibilityLevel) for item in self.supported_compatibility):
            raise MicrobenchmarkValidationError("external projection must declare supported compatibility levels")
        if len(set(self.supported_compatibility)) != len(self.supported_compatibility):
            raise MicrobenchmarkIntegrityError("external projection repeats a compatibility level")


@dataclass(frozen=True)
class SchemaNegotiation(M08Record):
    projection_id: str
    producer_schema_id: str
    producer_version: SchemaVersion
    level: CompatibilityLevel
    accepted_features: tuple[str, ...]
    missing_required_features: tuple[str, ...]
    result: str
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in ("projection_id", "producer_schema_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if not isinstance(self.producer_version, SchemaVersion) or not isinstance(self.level, CompatibilityLevel):
            raise MicrobenchmarkValidationError("negotiation version/level uses an invalid schema type")
        for field in ("accepted_features", "missing_required_features", "reasons"):
            object.__setattr__(self, field, tuple(sorted(require_unique(getattr(self, field), field, maximum=10_000))))
        if self.result not in {"ACCEPTED", "REJECTED", "INCOMPATIBLE"}:
            raise MicrobenchmarkValidationError("negotiation result is outside the closed result vocabulary")
        if self.result == "ACCEPTED" and self.missing_required_features:
            raise MicrobenchmarkIntegrityError("accepted schema negotiation cannot omit required features")


def negotiate_schema(
    producer: SchemaDescriptor,
    consumer: ExternalSchemaProjection,
    *,
    producer_features: tuple[str, ...],
    declared_level: CompatibilityLevel,
) -> SchemaNegotiation:
    producer = SchemaDescriptor.coerce(producer, "producer")
    consumer = ExternalSchemaProjection.coerce(consumer, "consumer")
    if not isinstance(declared_level, CompatibilityLevel):
        raise MicrobenchmarkValidationError("declared_level must be CompatibilityLevel")
    if producer.schema_id != consumer.schema_id:
        return SchemaNegotiation(consumer.projection_id, producer.schema_id, producer.version, declared_level, (), consumer.required_features, "INCOMPATIBLE", ("schema_identity_mismatch",))
    features = set(require_unique(producer_features, "producer_features", maximum=10_000))
    required = set(consumer.required_features) | set(producer.required_features)
    missing = tuple(sorted(required - features))
    if not consumer.minimum_version <= producer.version <= consumer.maximum_version:
        return SchemaNegotiation(consumer.projection_id, producer.schema_id, producer.version, declared_level, tuple(sorted(features & set(consumer.optional_features))), missing, "INCOMPATIBLE", ("version_outside_negotiated_range",))
    if declared_level not in consumer.supported_compatibility:
        return SchemaNegotiation(consumer.projection_id, producer.schema_id, producer.version, declared_level, (), missing, "INCOMPATIBLE", ("compatibility_level_not_negotiated",))
    if missing:
        return SchemaNegotiation(consumer.projection_id, producer.schema_id, producer.version, declared_level, (), missing, "REJECTED", ("unknown_or_missing_required_features",))
    accepted = tuple(sorted(features & (set(consumer.required_features) | set(consumer.optional_features))))
    return SchemaNegotiation(consumer.projection_id, producer.schema_id, producer.version, declared_level, accepted, (), "ACCEPTED", ())
