"""Immutable, loss-explicit document migration with verifiable lineage receipts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .model import content_digest, require_id
from .versioning import CompatibilityLevel, ExtensionField, SchemaDescriptor, VersionedDocument, create_document, verify_document

__all__ = [
    "MigrationOperation", "MigrationAction", "MigrationPlan", "MigrationReceipt",
    "migrate_document", "verify_migration_receipt",
]


class MigrationOperation(str, Enum):
    ADD_OPTIONAL = "ADD_OPTIONAL"
    RENAME_OPTIONAL = "RENAME_OPTIONAL"
    DROP_OPTIONAL = "DROP_OPTIONAL"
    CLARIFY_METADATA = "CLARIFY_METADATA"


@dataclass(frozen=True)
class MigrationAction:
    action_id: str
    operation: MigrationOperation
    namespace: str
    source_key: str | None = None
    target_key: str | None = None
    extension_value: ExtensionField | None = None

    def __post_init__(self) -> None:
        for field in ("action_id", "namespace"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if not isinstance(self.operation, MigrationOperation):
            raise ValueError("migration operation must be explicit")
        for field in ("source_key", "target_key"):
            if getattr(self, field) is not None:
                object.__setattr__(self, field, require_id(getattr(self, field), field))
        if self.operation is MigrationOperation.ADD_OPTIONAL:
            if self.source_key is not None or self.target_key is None or type(self.extension_value) is not ExtensionField:
                raise ValueError("add-optional action requires target key and extension value only")
            if self.extension_value.namespace != self.namespace or self.extension_value.key != self.target_key or self.extension_value.required:
                raise ValueError("added extension must match action and remain optional")
        elif self.operation is MigrationOperation.RENAME_OPTIONAL:
            if self.source_key is None or self.target_key is None or self.extension_value is not None:
                raise ValueError("rename action requires source and target only")
        elif self.operation in {MigrationOperation.DROP_OPTIONAL, MigrationOperation.CLARIFY_METADATA}:
            if self.source_key is None or self.target_key is not None or self.extension_value is not None:
                raise ValueError("drop/metadata action requires source only")


@dataclass(frozen=True)
class MigrationPlan:
    plan_id: str
    source_document_digest: str
    source_schema: SchemaDescriptor
    target_schema: SchemaDescriptor
    compatibility: str
    actions: tuple[MigrationAction, ...]
    preserved_features: tuple[str, ...]
    loss_features: tuple[str, ...]
    defaulted_features: tuple[str, ...]
    authorization_ref: str

    def __post_init__(self) -> None:
        for field in ("plan_id", "authorization_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        _digest(self.source_document_digest, "source_document_digest")
        if type(self.source_schema) is not SchemaDescriptor or type(self.target_schema) is not SchemaDescriptor:
            raise ValueError("migration schemas must be exact SchemaDescriptor values")
        if self.source_schema.schema_id != self.target_schema.schema_id:
            raise ValueError("migration cannot change canonical schema identity")
        if self.compatibility not in {CompatibilityLevel.PATCH, CompatibilityLevel.MINOR, CompatibilityLevel.MAJOR}:
            raise ValueError("compatibility classification must be explicit")
        actions = tuple(self.actions)
        if len(actions) > 4_096 or any(type(item) is not MigrationAction for item in actions) or len({item.action_id for item in actions}) != len(actions):
            raise ValueError("migration actions must be bounded with unique typed identities")
        object.__setattr__(self, "actions", actions)
        for field in ("preserved_features", "loss_features", "defaulted_features"):
            raw = tuple(getattr(self, field))
            if len(raw) > 2_048:
                raise ValueError("migration feature evidence exceeds its finite bound")
            values = tuple(sorted({require_id(item, field) for item in raw}))
            object.__setattr__(self, field, values)
        if set(self.loss_features) & (set(self.preserved_features) | set(self.defaulted_features)):
            raise ValueError("declared losses cannot contradict preserved/defaulted features")
        if self.compatibility == CompatibilityLevel.MAJOR and not (self.preserved_features or self.loss_features or self.defaulted_features):
            raise ValueError("major migration requires explicit preservation/loss/default analysis")


@dataclass(frozen=True)
class MigrationReceipt:
    receipt_id: str
    plan_id: str
    source_document_digest: str
    result_document_digest: str
    lineage_parent_digest: str
    action_results: tuple[tuple[str, str], ...]
    loss_classification: str
    preserved_features: tuple[str, ...]
    loss_features: tuple[str, ...]
    defaulted_features: tuple[str, ...]
    receipt_digest: str

    def __post_init__(self) -> None:
        for field in ("receipt_id", "plan_id"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        for field in ("source_document_digest", "result_document_digest", "lineage_parent_digest", "receipt_digest"):
            _digest(getattr(self, field), field)
        if self.loss_classification not in {"LOSSLESS", "LOSSY"}:
            raise ValueError("receipt must classify migration loss")


def migrate_document(source: VersionedDocument, plan: MigrationPlan, *, result_id: str, result_time_ms: int, receipt_id: str) -> tuple[VersionedDocument, MigrationReceipt]:
    _validate_plan_for_source(source, plan)

    extensions, results = _apply_actions(source, plan)

    result_document = create_document(
        plan.target_schema, source.body, document_id=result_id,
        created_at_ms=result_time_ms, extensions=extensions,
        parent_document_digest=source.document_digest,
    )
    if result_document.document_digest == source.document_digest:
        raise ValueError("migration must create a new immutable document identity")
    material = _receipt_material(
        receipt_id, plan, source, result_document, tuple(sorted(results)),
    )
    receipt = MigrationReceipt(
        receipt_id, plan.plan_id, source.document_digest, result_document.document_digest,
        source.document_digest, tuple(sorted(results)),
        "LOSSY" if plan.loss_features else "LOSSLESS",
        plan.preserved_features, plan.loss_features, plan.defaulted_features,
        content_digest(material),
    )
    verify_document(result_document)
    verify_migration_receipt(source, result_document, plan, receipt)
    return result_document, receipt


def verify_migration_receipt(source: VersionedDocument, result: VersionedDocument, plan: MigrationPlan, receipt: MigrationReceipt) -> bool:
    if type(source) is not VersionedDocument or type(result) is not VersionedDocument or type(plan) is not MigrationPlan or type(receipt) is not MigrationReceipt:
        raise ValueError("receipt verification requires exact migration records")
    _validate_plan_for_source(source, plan)
    verify_document(source)
    verify_document(result)
    if (
        receipt.plan_id != plan.plan_id
        or receipt.source_document_digest != source.document_digest
        or receipt.result_document_digest != result.document_digest
        or receipt.lineage_parent_digest != source.document_digest
        or result.parent_document_digest != source.document_digest
        or result.schema != plan.target_schema
        or result.body != source.body
    ):
        raise ValueError("migration receipt lineage or semantic body preservation is invalid")
    expected_extensions, results = _apply_actions(source, plan)
    if receipt.action_results != results or receipt.loss_features != plan.loss_features:
        raise ValueError("migration receipt action/loss map does not match the frozen plan")
    if result.extensions != expected_extensions:
        raise ValueError("migration result extensions do not match the declared actions")
    if content_digest(_receipt_material(receipt.receipt_id, plan, source, result, results)) != receipt.receipt_digest:
        raise ValueError("migration receipt digest mismatch")
    return True


def _validate_plan_for_source(source: VersionedDocument, plan: MigrationPlan) -> None:
    if type(source) is not VersionedDocument or type(plan) is not MigrationPlan:
        raise ValueError("migration requires exact source and plan records")
    verify_document(source)
    if source.document_digest != plan.source_document_digest or source.schema != plan.source_schema:
        raise ValueError("migration plan is stale or bound to another source document")
    if plan.target_schema == source.schema:
        raise ValueError("migration must create a new schema version")
    if plan.compatibility == CompatibilityLevel.MAJOR and plan.target_schema.major == source.schema.major:
        raise ValueError("major compatibility requires a major version change")
    if plan.compatibility == CompatibilityLevel.MINOR and plan.target_schema.major != source.schema.major:
        raise ValueError("minor compatibility cannot change the major version")
    if plan.compatibility == CompatibilityLevel.PATCH and (plan.target_schema.major, plan.target_schema.minor) != (source.schema.major, source.schema.minor):
        raise ValueError("patch compatibility cannot change major or minor version")


def _apply_actions(source: VersionedDocument, plan: MigrationPlan) -> tuple[tuple[ExtensionField, ...], tuple[tuple[str, str], ...]]:
    extensions = {(item.namespace, item.key): item for item in source.extensions}
    results: list[tuple[str, str]] = []
    for action in plan.actions:
        source_key = (action.namespace, action.source_key) if action.source_key is not None else None
        target_key = (action.namespace, action.target_key) if action.target_key is not None else None
        if action.operation is MigrationOperation.ADD_OPTIONAL:
            if target_key is None or action.extension_value is None:
                raise ValueError("optional migration add action is incomplete")
            if target_key in extensions:
                raise ValueError("optional migration target already exists")
            extensions[target_key] = action.extension_value
            result = "added_optional"
        elif action.operation is MigrationOperation.RENAME_OPTIONAL:
            if source_key is None or target_key is None or action.target_key is None:
                raise ValueError("optional migration rename action is incomplete")
            if source_key not in extensions or target_key in extensions:
                raise ValueError("rename source must exist and target must be absent")
            old = extensions[source_key]
            if old.required:
                raise ValueError("required extensions cannot be renamed by an optional migration")
            extensions[target_key] = ExtensionField(old.namespace, action.target_key, old.version, False, old.value)
            del extensions[source_key]
            result = "renamed_optional"
        elif action.operation is MigrationOperation.DROP_OPTIONAL:
            if source_key is None:
                raise ValueError("optional migration drop action has no source")
            if source_key not in extensions:
                raise ValueError("drop source extension is absent")
            old = extensions[source_key]
            if old.required:
                raise ValueError("required extensions cannot be dropped")
            if f"{old.namespace}:{old.key}" not in plan.loss_features:
                raise ValueError("dropping optional extension requires explicit loss declaration")
            del extensions[source_key]
            result = "dropped_optional"
        else:
            if source_key is None:
                raise ValueError("metadata clarification action has no source")
            if source_key not in extensions:
                raise ValueError("metadata clarification source is absent")
            result = "clarified_without_semantic_change"
        results.append((action.action_id, result))
    ordered_extensions = tuple(sorted(extensions.values(), key=lambda item: (item.namespace, item.key)))
    return ordered_extensions, tuple(sorted(results))


def _receipt_material(receipt_id: str, plan: MigrationPlan, source: VersionedDocument, result: VersionedDocument, results: tuple[tuple[str, str], ...]) -> dict[str, object]:
    return {
        "receipt_id": receipt_id,
        "plan_id": plan.plan_id,
        "source": source.document_digest,
        "result": result.document_digest,
        "actions": results,
        "loss": "LOSSY" if plan.loss_features else "LOSSLESS",
        "preserved": plan.preserved_features,
        "loss_features": plan.loss_features,
        "defaults": plan.defaulted_features,
    }


def _digest(value: str, field: str) -> None:
    if type(value) is not str or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field} must be lowercase SHA-256")
