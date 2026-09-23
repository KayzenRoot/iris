"""Machine-readable schema compatibility and governed extension barriers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from .base import M07Record, freeze_json
from .enums import CompatibilityLevel, ExtensionDisposition
from .errors import HardwareGenomeAdmissionError, HardwareGenomeCompatibilityError, HardwareGenomeIntegrityError, HardwareGenomeValidationError
from .versions import CORE_SCHEMA_VERSION, require_identifier, require_unique, require_version

__all__ = [
    "SchemaVersion", "SchemaCompatibilityDeclaration", "SchemaReaderDeclaration", "SchemaDescriptor",
    "ExtensionField", "CORE_SCHEMA", "compare_schema_versions", "require_reader_compatibility",
]

_SCHEMA_VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


@dataclass(frozen=True, order=True)
class SchemaVersion(M07Record):
    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        for field in ("major", "minor", "patch"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise HardwareGenomeValidationError(f"schema {field} must be a non-negative integer")

    @classmethod
    def parse(cls, value: str) -> "SchemaVersion":
        text = require_version(value, "schema_version")
        match = _SCHEMA_VERSION.fullmatch(text)
        if match is None:
            raise HardwareGenomeValidationError("schema version must use explicit major.minor.patch integers")
        return cls(*(int(item) for item in match.groups()))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def compare_schema_versions(source: SchemaVersion, target: SchemaVersion) -> CompatibilityLevel:
    source = SchemaVersion.coerce(source, "source")
    target = SchemaVersion.coerce(target, "target")
    if source.major != target.major:
        return CompatibilityLevel.MAJOR
    if target.minor < source.minor or (target.minor == source.minor and target.patch < source.patch):
        return CompatibilityLevel.MAJOR
    if target.minor > source.minor:
        return CompatibilityLevel.MINOR
    return CompatibilityLevel.PATCH


@dataclass(frozen=True)
class SchemaCompatibilityDeclaration(M07Record):
    declaration_id: str
    source: SchemaVersion
    target: SchemaVersion
    level: CompatibilityLevel
    backward_compatible: bool
    migration_required: bool
    rationale: str
    required_feature_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "declaration_id", require_identifier(self.declaration_id, "declaration_id"))
        for field in ("source", "target"):
            object.__setattr__(self, field, SchemaVersion.coerce(getattr(self, field), field))
        if type(self.level) is not CompatibilityLevel or self.level is not compare_schema_versions(self.source, self.target):
            raise HardwareGenomeIntegrityError("schema compatibility level differs from the declared version transition")
        if type(self.backward_compatible) is not bool or type(self.migration_required) is not bool:
            raise HardwareGenomeValidationError("schema compatibility flags must be bool")
        object.__setattr__(self, "rationale", require_identifier(self.rationale, "rationale"))
        features = tuple(sorted(require_unique(self.required_feature_ids, "required_feature_ids", maximum=2_000)))
        object.__setattr__(self, "required_feature_ids", features)
        if self.level is CompatibilityLevel.PATCH and not self.backward_compatible:
            raise HardwareGenomeAdmissionError("PATCH changes cannot alter admitted semantics")
        if self.level is CompatibilityLevel.PATCH and (self.source.major, self.source.minor) != (self.target.major, self.target.minor):
            raise HardwareGenomeIntegrityError("PATCH transitions cannot change major or minor schema axes")
        if self.level is CompatibilityLevel.MAJOR and (self.backward_compatible or not self.migration_required):
            raise HardwareGenomeAdmissionError("MAJOR changes require a migration and cannot be declared backward compatible")
        if self.level is CompatibilityLevel.MINOR and not self.backward_compatible:
            raise HardwareGenomeAdmissionError("MINOR additions must preserve declared reader compatibility")
        if self.level is CompatibilityLevel.MINOR and self.target.minor <= self.source.minor:
            raise HardwareGenomeIntegrityError("MINOR transitions must advance the schema minor axis")


@dataclass(frozen=True)
class SchemaReaderDeclaration(M07Record):
    reader_id: str
    supported_major: int
    maximum_minor: int
    known_features: tuple[str, ...]
    preserves_unknown_optional: bool
    fails_unknown_required: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "reader_id", require_identifier(self.reader_id, "reader_id"))
        for field in ("supported_major", "maximum_minor"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise HardwareGenomeValidationError(f"{field} must be a non-negative integer")
        object.__setattr__(self, "known_features", tuple(sorted(require_unique(self.known_features, "known_features", maximum=10_000))))
        for field in ("preserves_unknown_optional", "fails_unknown_required"):
            if type(getattr(self, field)) is not bool:
                raise HardwareGenomeValidationError(f"{field} must be bool")
        if not self.fails_unknown_required:
            raise HardwareGenomeAdmissionError("readers must fail closed on unknown required semantics")


@dataclass(frozen=True)
class SchemaDescriptor(M07Record):
    schema_id: str
    version: SchemaVersion
    required_features: tuple[str, ...]
    optional_features: tuple[str, ...]
    canonicalization_version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_identifier(self.schema_id, "schema_id"))
        object.__setattr__(self, "version", SchemaVersion.coerce(self.version, "version"))
        required = tuple(sorted(require_unique(self.required_features, "required_features", maximum=10_000)))
        optional = tuple(sorted(require_unique(self.optional_features, "optional_features", maximum=10_000)))
        if set(required) & set(optional):
            raise HardwareGenomeIntegrityError("schema features cannot be both required and optional")
        object.__setattr__(self, "required_features", required)
        object.__setattr__(self, "optional_features", optional)
        object.__setattr__(self, "canonicalization_version", require_version(self.canonicalization_version, "canonicalization_version"))


@dataclass(frozen=True)
class ExtensionField(M07Record):
    namespace: str
    key: str
    version: str
    value: Mapping[str, Any]
    disposition: ExtensionDisposition

    def __post_init__(self) -> None:
        namespace = require_identifier(self.namespace, "namespace")
        if "." in namespace or not namespace[0].islower() or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", namespace):
            raise HardwareGenomeValidationError("extension namespace must be a bounded lower-case identifier")
        object.__setattr__(self, "namespace", namespace)
        object.__setattr__(self, "key", require_identifier(self.key, "key"))
        if self.key.startswith("iris.") or self.key in {"state", "unit", "evidence", "subject_id", "runtime_id"}:
            raise HardwareGenomeAdmissionError("extension cannot shadow canonical fact semantics")
        object.__setattr__(self, "version", require_version(self.version, "version"))
        frozen = freeze_json(self.value, "extension value")
        if not isinstance(frozen, MappingProxyType):
            raise HardwareGenomeValidationError("extension value must be an object")
        object.__setattr__(self, "value", frozen)
        if type(self.disposition) is not ExtensionDisposition:
            raise HardwareGenomeValidationError("extension disposition must be explicit")


CORE_SCHEMA = SchemaDescriptor(
    CORE_SCHEMA_VERSION,
    SchemaVersion(1, 0, 0),
    ("evidence-envelope-v1", "unknown-state-v1"),
    ("telemetry-v1", "redacted-advertisement-v1"),
    "iris-m07-canonical-v1",
)


def require_reader_compatibility(schema: SchemaDescriptor, reader: SchemaReaderDeclaration) -> None:
    schema = SchemaDescriptor.coerce(schema, "schema")
    reader = SchemaReaderDeclaration.coerce(reader, "reader")
    if schema.version.major != reader.supported_major or schema.version.minor > reader.maximum_minor:
        raise HardwareGenomeCompatibilityError("reader does not support this schema major/minor")
    known = set(reader.known_features)
    unknown_required = set(schema.required_features) - known
    if unknown_required:
        raise HardwareGenomeCompatibilityError(f"reader does not understand required schema features: {sorted(unknown_required)}")
    unknown_optional = set(schema.optional_features) - known
    if unknown_optional and not reader.preserves_unknown_optional:
        raise HardwareGenomeCompatibilityError("reader cannot preserve unknown optional schema features")
