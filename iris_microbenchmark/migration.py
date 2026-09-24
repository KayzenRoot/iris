"""Immutable schema migration plans and receipts over optional M08 extensions."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M08Record, content_digest
from .enums import CompatibilityLevel, MigrationOperation
from .errors import MicrobenchmarkAdmissionError, MicrobenchmarkCompatibilityError, MicrobenchmarkIntegrityError, MicrobenchmarkValidationError
from .schema import ExtensionDisposition, ExtensionField, SchemaDescriptor
from .serialization import VersionedRecordDocument, create_document, verify_document
from .versions import require_digest, require_identifier, require_unique, require_version

__all__ = ["MigrationAction", "SchemaMigrationPlan", "SchemaMigrationReceipt", "migrate_document", "verify_migration_receipt"]


@dataclass(frozen=True)
class MigrationAction(M08Record):
    action_id: str
    operation: MigrationOperation
    namespace: str
    source_key: str | None
    target_key: str | None
    extension_value: ExtensionField | None
    rationale_ref: str

    def __post_init__(self) -> None:
        for field in ("action_id", "namespace", "rationale_ref"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if not isinstance(self.operation, MigrationOperation):
            raise MicrobenchmarkValidationError("operation must be MigrationOperation")
        for field in ("source_key", "target_key"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_identifier(value, field))
        if self.extension_value is not None:
            object.__setattr__(self, "extension_value", ExtensionField.coerce(self.extension_value, "extension_value"))
        if self.operation is MigrationOperation.ADD_OPTIONAL_EXTENSION:
            if self.source_key is not None or self.target_key is None or self.extension_value is None:
                raise MicrobenchmarkValidationError("add-extension action requires an optional target value only")
            if self.extension_value.namespace != self.namespace or self.extension_value.key != self.target_key or self.extension_value.disposition != ExtensionDisposition.OPTIONAL_PRESERVE:
                raise MicrobenchmarkAdmissionError("migration can add only the exact optional target extension")
        elif self.operation is MigrationOperation.RENAME_OPTIONAL_EXTENSION:
            if self.source_key is None or self.target_key is None or self.source_key == self.target_key or self.extension_value is not None:
                raise MicrobenchmarkValidationError("rename action requires distinct source and target keys")
        elif self.operation is MigrationOperation.DROP_OPTIONAL_EXTENSION:
            if self.source_key is None or self.target_key is not None or self.extension_value is not None:
                raise MicrobenchmarkValidationError("drop action requires a source key only")
        elif self.operation is MigrationOperation.CLARIFY_METADATA:
            if self.source_key is None or self.target_key is not None or self.extension_value is not None:
                raise MicrobenchmarkValidationError("metadata clarification requires an existing source key")


@dataclass(frozen=True)
class SchemaMigrationPlan(M08Record):
    plan_id: str
    version: str
    source_document_digest: str
    source_schema: SchemaDescriptor
    target_schema: SchemaDescriptor
    compatibility: CompatibilityLevel
    actions: tuple[MigrationAction, ...]
    preserved_features: tuple[str, ...]
    loss_features: tuple[str, ...]
    defaulted_features: tuple[str, ...]
    authorization_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", require_identifier(self.plan_id, "plan_id"))
        object.__setattr__(self, "version", require_version(self.version))
        object.__setattr__(self, "source_document_digest", require_digest(self.source_document_digest, "source_document_digest"))
        object.__setattr__(self, "source_schema", SchemaDescriptor.coerce(self.source_schema, "source_schema"))
        object.__setattr__(self, "target_schema", SchemaDescriptor.coerce(self.target_schema, "target_schema"))
        if self.source_schema.schema_id != self.target_schema.schema_id:
            raise MicrobenchmarkCompatibilityError("schema migration cannot change canonical schema identity")
        if not isinstance(self.compatibility, CompatibilityLevel):
            raise MicrobenchmarkValidationError("compatibility must be CompatibilityLevel")
        actions = tuple(MigrationAction.coerce(item, "actions[]") for item in self.actions)
        if len({item.action_id for item in actions}) != len(actions):
            raise MicrobenchmarkIntegrityError("migration plan repeats an action identity")
        if len({(item.namespace, item.source_key, item.target_key) for item in actions}) != len(actions):
            raise MicrobenchmarkIntegrityError("migration plan repeats an extension transformation")
        object.__setattr__(self, "actions", actions)
        for field in ("preserved_features", "loss_features", "defaulted_features"):
            object.__setattr__(self, field, tuple(sorted(require_unique(getattr(self, field), field, maximum=10_000))))
        object.__setattr__(self, "authorization_ref", require_identifier(self.authorization_ref, "authorization_ref"))
        if set(self.preserved_features) & set(self.loss_features) or set(self.defaulted_features) & set(self.loss_features):
            raise MicrobenchmarkIntegrityError("migration preservation, defaults, and declared losses cannot contradict each other")
        if self.compatibility is CompatibilityLevel.MAJOR and not (self.preserved_features or self.loss_features or self.defaulted_features):
            raise MicrobenchmarkAdmissionError("major migration requires explicit preservation/loss/default analysis")


@dataclass(frozen=True)
class SchemaMigrationReceipt(M08Record):
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
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        for field in ("source_document_digest", "result_document_digest", "lineage_parent_digest", "receipt_digest"):
            object.__setattr__(self, field, require_digest(getattr(self, field), field))
        results = tuple(sorted((require_identifier(action, "action_id"), require_identifier(result, "action_result")) for action, result in self.action_results))
        if len({action for action, _ in results}) != len(results):
            raise MicrobenchmarkIntegrityError("migration receipt repeats an action")
        object.__setattr__(self, "action_results", results)
        if self.loss_classification not in {"LOSSLESS", "LOSSY"}:
            raise MicrobenchmarkValidationError("migration loss classification must be explicit")
        for field in ("preserved_features", "loss_features", "defaulted_features"):
            object.__setattr__(self, field, tuple(sorted(require_unique(getattr(self, field), field, maximum=10_000))))
        if self.source_document_digest == self.result_document_digest or self.lineage_parent_digest != self.source_document_digest:
            raise MicrobenchmarkIntegrityError("migration must create a new immutable document with exact source lineage")
        if (self.loss_classification == "LOSSY") != bool(self.loss_features):
            raise MicrobenchmarkIntegrityError("migration loss classification must match declared semantic losses")
        expected = content_digest({
            "receipt_id": self.receipt_id,
            "plan_id": self.plan_id,
            "source": self.source_document_digest,
            "result": self.result_document_digest,
            "actions": self.action_results,
            "loss": self.loss_classification,
            "preserved": self.preserved_features,
            "loss_features": self.loss_features,
            "defaults": self.defaulted_features,
        })
        if self.receipt_digest != expected:
            raise MicrobenchmarkIntegrityError("migration receipt digest does not match its immutable transformation summary")


def _apply_actions(source: VersionedRecordDocument, plan: SchemaMigrationPlan) -> tuple[tuple[ExtensionField, ...], tuple[tuple[str, str], ...]]:
    extensions = {(item.namespace, item.key): item for item in source.extensions}
    results: list[tuple[str, str]] = []
    for action in plan.actions:
        source_key = (action.namespace, action.source_key) if action.source_key is not None else None
        target_key = (action.namespace, action.target_key) if action.target_key is not None else None
        if action.operation is MigrationOperation.ADD_OPTIONAL_EXTENSION:
            if target_key is None or action.extension_value is None:
                raise MicrobenchmarkIntegrityError("add-extension action lost its required target value")
            if target_key in extensions:
                raise MicrobenchmarkIntegrityError("migration extension target already exists")
            extensions[target_key] = action.extension_value
            result = "added_optional"
        elif action.operation is MigrationOperation.RENAME_OPTIONAL_EXTENSION:
            if source_key is None or target_key is None or action.target_key is None:
                raise MicrobenchmarkIntegrityError("rename action lost its required source or target")
            if source_key not in extensions or target_key in extensions:
                raise MicrobenchmarkAdmissionError("rename source must exist and target must be absent")
            item = extensions[source_key]
            if item.disposition != ExtensionDisposition.OPTIONAL_PRESERVE:
                raise MicrobenchmarkAdmissionError("required extension semantics cannot be renamed by an optional migration")
            extensions[target_key] = ExtensionField(item.namespace, action.target_key, item.version, item.disposition, item.value)
            del extensions[source_key]
            result = "renamed_optional"
        elif action.operation is MigrationOperation.DROP_OPTIONAL_EXTENSION:
            if source_key is None:
                raise MicrobenchmarkIntegrityError("drop action lost its required source")
            if source_key not in extensions:
                raise MicrobenchmarkAdmissionError("drop source extension is absent")
            item = extensions[source_key]
            if item.disposition != ExtensionDisposition.OPTIONAL_PRESERVE:
                raise MicrobenchmarkAdmissionError("required extension semantics cannot be dropped")
            if f"{item.namespace}:{item.key}" not in plan.loss_features:
                raise MicrobenchmarkAdmissionError("dropping optional extension requires an explicit loss declaration")
            del extensions[source_key]
            result = "dropped_optional"
        else:
            if source_key is None:
                raise MicrobenchmarkIntegrityError("metadata clarification action lost its required source")
            if source_key not in extensions:
                raise MicrobenchmarkAdmissionError("metadata clarification source extension is absent")
            result = "clarified_without_semantic_change"
        results.append((action.action_id, result))
    return tuple(sorted(extensions.values(), key=lambda item: (item.namespace, item.key))), tuple(sorted(results))


def migrate_document(
    source: VersionedRecordDocument,
    plan: SchemaMigrationPlan,
    *,
    result_time_ms: int,
    receipt_id: str,
) -> tuple[VersionedRecordDocument, SchemaMigrationReceipt]:
    source, plan = VersionedRecordDocument.coerce(source, "source"), SchemaMigrationPlan.coerce(plan, "plan")
    if source.document_digest != plan.source_document_digest or source.schema != plan.source_schema:
        raise MicrobenchmarkIntegrityError("migration plan is stale or bound to another source document")
    if plan.target_schema.version == source.schema.version:
        raise MicrobenchmarkCompatibilityError("schema migration must create a new schema version")
    if plan.compatibility is CompatibilityLevel.MAJOR and plan.target_schema.version.major == source.schema.version.major:
        raise MicrobenchmarkCompatibilityError("major compatibility classification requires a major version change")
    extensions, action_results = _apply_actions(source, plan)
    result = create_document(plan.target_schema, source.record, extensions=extensions, created_at_ms=result_time_ms, parent_document_digest=source.document_digest)
    if result.document_digest == source.document_digest:
        raise MicrobenchmarkIntegrityError("migration did not create a new immutable document identity")
    loss = "LOSSY" if plan.loss_features else "LOSSLESS"
    receipt_material = {
        "receipt_id": receipt_id, "plan_id": plan.plan_id, "source": source.document_digest,
        "result": result.document_digest, "actions": action_results, "loss": loss,
        "preserved": plan.preserved_features, "loss_features": plan.loss_features,
        "defaults": plan.defaulted_features,
    }
    receipt = SchemaMigrationReceipt(
        receipt_id, plan.plan_id, source.document_digest, result.document_digest,
        source.document_digest, action_results, loss, plan.preserved_features,
        plan.loss_features, plan.defaulted_features, content_digest(receipt_material),
    )
    verify_document(result)
    verify_migration_receipt(source, result, plan, receipt)
    return result, receipt


def verify_migration_receipt(
    source: VersionedRecordDocument,
    result: VersionedRecordDocument,
    plan: SchemaMigrationPlan,
    receipt: SchemaMigrationReceipt,
) -> bool:
    source, result = VersionedRecordDocument.coerce(source, "source"), VersionedRecordDocument.coerce(result, "result")
    plan, receipt = SchemaMigrationPlan.coerce(plan, "plan"), SchemaMigrationReceipt.coerce(receipt, "receipt")
    if (
        receipt.plan_id != plan.plan_id
        or receipt.source_document_digest != source.document_digest
        or receipt.result_document_digest != result.document_digest
        or result.parent_document_digest != source.document_digest
        or result.schema != plan.target_schema
        or result.record != source.record
    ):
        raise MicrobenchmarkIntegrityError("migration receipt lineage or semantic record preservation is invalid")
    expected_extensions, action_results = _apply_actions(source, plan)
    loss = "LOSSY" if plan.loss_features else "LOSSLESS"
    expected_material = {
        "receipt_id": receipt.receipt_id, "plan_id": plan.plan_id, "source": source.document_digest,
        "result": result.document_digest, "actions": action_results, "loss": loss,
        "preserved": plan.preserved_features, "loss_features": plan.loss_features,
        "defaults": plan.defaulted_features,
    }
    if (
        result.extensions != expected_extensions
        or action_results != receipt.action_results
        or loss != receipt.loss_classification
        or receipt.preserved_features != plan.preserved_features
        or receipt.loss_features != plan.loss_features
        or receipt.defaulted_features != plan.defaulted_features
        or content_digest(expected_material) != receipt.receipt_digest
    ):
        raise MicrobenchmarkIntegrityError("migration receipt does not prove exact immutable transformation")
    return True
