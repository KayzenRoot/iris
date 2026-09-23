"""Immutable, data-only schema migration plans with a closed operation vocabulary."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .base import CanonicalRecord, canonical_bytes, freeze_json, thaw_json
from .enums import MigrationOperationKind
from .errors import ProductionStateAdmissionError, ProductionStateIntegrityError, ProductionStateValidationError
from .limits import DEFAULT_LIMITS
from .versions import CORE_SCHEMA_VERSION, require_identifier, require_version

__all__ = [
    "DataMigrationOperation",
    "MigrationPlan",
    "MigrationReceipt",
    "apply_migration",
]


@dataclass(frozen=True)
class DataMigrationOperation(CanonicalRecord):
    kind: MigrationOperationKind
    source_path: tuple[str, ...]
    target_path: tuple[str, ...] | None = None
    literal_value: Any = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MigrationOperationKind):
            object.__setattr__(self, "kind", MigrationOperationKind(self.kind))
        source = _path(self.source_path, "source_path")
        object.__setattr__(self, "source_path", source)
        if self.target_path is not None:
            object.__setattr__(self, "target_path", _path(self.target_path, "target_path"))
        if self.kind in {MigrationOperationKind.RENAME, MigrationOperationKind.COPY} and self.target_path is None:
            raise ProductionStateValidationError(f"{self.kind.value} migration requires a target path")
        if self.kind is MigrationOperationKind.DEFAULT and self.target_path is not None:
            raise ProductionStateValidationError("DEFAULT writes to source_path and cannot specify target_path")
        if self.kind is MigrationOperationKind.DROP and self.target_path is not None:
            raise ProductionStateValidationError("DROP cannot specify target_path")
        object.__setattr__(self, "literal_value", freeze_json(self.literal_value, "literal_value"))
        if self.kind is not MigrationOperationKind.DEFAULT and self.literal_value is not None:
            raise ProductionStateValidationError("only DEFAULT operations may contain a literal JSON value")


@dataclass(frozen=True)
class MigrationPlan(CanonicalRecord):
    plan_id: str
    source_schema: str
    target_schema: str
    operations: tuple[DataMigrationOperation, ...]
    plan_version: str = CORE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_identifier(self.plan_id, "plan_id")
        require_version(self.source_schema, "source_schema")
        require_version(self.target_schema, "target_schema")
        if self.source_schema == self.target_schema:
            raise ProductionStateValidationError("schema migration must move between distinct explicit versions")
        operations = tuple(self.operations)
        if not operations or len(operations) > DEFAULT_LIMITS.max_fingerprint_dimensions:
            raise ProductionStateValidationError("migration plan requires a bounded non-empty operation sequence")
        if any(type(item) is not DataMigrationOperation for item in operations):
            raise ProductionStateValidationError("migration operations must use the closed data-only operation type")
        object.__setattr__(self, "operations", operations)
        require_version(self.plan_version, "plan_version")


@dataclass(frozen=True)
class MigrationReceipt(CanonicalRecord):
    receipt_id: str
    plan: MigrationPlan
    source_fingerprint: str
    result_fingerprint: str
    migrated_document: Any
    applied_at_ms: int

    def __post_init__(self) -> None:
        require_identifier(self.receipt_id, "receipt_id")
        if type(self.plan) is not MigrationPlan:
            raise ProductionStateValidationError("migration receipt requires an exact immutable migration plan")
        for field in ("source_fingerprint", "result_fingerprint"):
            value = getattr(self, field)
            if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
                raise ProductionStateValidationError(f"{field} must be sha256")
        object.__setattr__(self, "migrated_document", freeze_json(self.migrated_document, "migrated_document"))
        if type(self.applied_at_ms) is not int or self.applied_at_ms < 0:
            raise ProductionStateValidationError("applied_at_ms must be a nonnegative exact integer")
        actual = hashlib.sha256(canonical_bytes(self.migrated_document)).hexdigest()
        if actual != self.result_fingerprint:
            raise ProductionStateIntegrityError("migration result fingerprint does not match immutable result payload")


def apply_migration(document: Any, plan: MigrationPlan, *, receipt_id: str, applied_at_ms: int) -> MigrationReceipt:
    if type(plan) is not MigrationPlan:
        raise ProductionStateValidationError("plan must be an exact MigrationPlan")
    source = thaw_json(freeze_json(document, "document"))
    if type(source) is not dict or source.get("schema_version") != plan.source_schema:
        raise ProductionStateAdmissionError("source document does not bind the migration plan's exact schema version")
    source_fp = hashlib.sha256(canonical_bytes(source)).hexdigest()
    result = thaw_json(freeze_json(source, "document"))
    for operation in plan.operations:
        if operation.kind is MigrationOperationKind.DEFAULT:
            parent, key = _parent(result, operation.source_path, create=True)
            if key not in parent:
                parent[key] = thaw_json(operation.literal_value)
        elif operation.kind is MigrationOperationKind.DROP:
            parent, key = _parent(result, operation.source_path, create=False)
            if key in parent:
                del parent[key]
        elif operation.kind is MigrationOperationKind.COPY:
            value = _get(result, operation.source_path)
            parent, key = _parent(result, operation.target_path, create=True)
            if key in parent:
                raise ProductionStateIntegrityError("COPY target already exists; implicit overwrite is forbidden")
            parent[key] = thaw_json(freeze_json(value, "copy source"))
        elif operation.kind is MigrationOperationKind.RENAME:
            source_parent, source_key = _parent(result, operation.source_path, create=False)
            if source_key not in source_parent:
                raise ProductionStateValidationError("RENAME source path does not exist")
            target_parent, target_key = _parent(result, operation.target_path, create=True)
            if target_key in target_parent:
                raise ProductionStateIntegrityError("RENAME target already exists; implicit overwrite is forbidden")
            target_parent[target_key] = source_parent.pop(source_key)
        else:  # pragma: no cover - closed enum validation makes this unreachable
            raise ProductionStateValidationError("unsupported migration operation")
        result = thaw_json(freeze_json(result, "migration result"))
    result["schema_version"] = plan.target_schema
    frozen = freeze_json(result, "migration result")
    result_fp = hashlib.sha256(canonical_bytes(frozen)).hexdigest()
    return MigrationReceipt(receipt_id, plan, source_fp, result_fp, frozen, applied_at_ms)


def _path(value: Any, field: str) -> tuple[str, ...]:
    if type(value) not in (tuple, list) or not value:
        raise ProductionStateValidationError(f"{field} must be a non-empty sequence of field names")
    return tuple(require_identifier(item, f"{field}[]") for item in value)


def _parent(document: dict[str, Any], path: tuple[str, ...] | None, *, create: bool) -> tuple[dict[str, Any], str]:
    if path is None:
        raise ProductionStateValidationError("migration target path is required")
    node = document
    for segment in path[:-1]:
        value = node.get(segment)
        if value is None and create:
            value = {}
            node[segment] = value
        if type(value) is not dict:
            raise ProductionStateValidationError(f"migration path segment {segment!r} is not an object")
        node = value
    return node, path[-1]


def _get(document: dict[str, Any], path: tuple[str, ...]) -> Any:
    node: Any = document
    for segment in path:
        if type(node) is not dict or segment not in node:
            raise ProductionStateValidationError("COPY source path does not exist")
        node = node[segment]
    return node
