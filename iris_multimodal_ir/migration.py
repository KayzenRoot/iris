"""Declarative, immutable schema migration plans and receipts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, ClassVar

from iris_intent.identity import SemanticRef

from .base import IRRecord, many, one
from .errors import IRAdmissionError, IRIntegrityError, IRSchemaError
from .graph import IRRevision
from .identity import IRRevisionRef
from .schema import SchemaCompatibilityDeclaration, SchemaFamilyRef, SchemaManifest
from .versions import content_digest, require_digest, require_identifier, require_text, require_version

__all__ = ["SchemaMigrationAction", "IRMigrationPlan", "IRMigrationReceipt", "migrate_revision"]


@dataclass(frozen=True)
class SchemaMigrationAction(IRRecord):
    action_id: str
    operation: str
    source_key: str
    target_key: str | None
    authorization_ref: SemanticRef
    optional_only: bool = False

    NESTED: ClassVar = {"authorization_ref": one(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "action_id", require_identifier(self.action_id, "action_id"))
        object.__setattr__(self, "operation", require_text(self.operation, "operation", maximum=64))
        if self.operation not in {"RENAME_NODE_ATTRIBUTE", "DROP_OPTIONAL_NODE_ATTRIBUTE"}:
            raise IRSchemaError("unsupported declarative migration operation")
        object.__setattr__(self, "source_key", require_text(self.source_key, "source_key", maximum=256))
        if self.target_key is not None:
            object.__setattr__(self, "target_key", require_text(self.target_key, "target_key", maximum=256))
        if self.operation == "RENAME_NODE_ATTRIBUTE" and not self.target_key:
            raise IRSchemaError("attribute rename requires a target_key")
        if self.operation == "DROP_OPTIONAL_NODE_ATTRIBUTE" and (not self.optional_only or self.target_key is not None):
            raise IRAdmissionError("dropping is permitted only for explicitly optional source attributes")
        object.__setattr__(self, "authorization_ref", SemanticRef.coerce(self.authorization_ref, "authorization_ref"))
        if not self.authorization_ref.pinned:
            raise IRAdmissionError("migration action authorization must be version or digest pinned")


@dataclass(frozen=True)
class IRMigrationPlan(IRRecord):
    plan_id: str
    source_revision: IRRevisionRef
    source_schema: SchemaFamilyRef
    target_schema: SchemaFamilyRef
    target_manifest: SchemaManifest
    compatibility: SchemaCompatibilityDeclaration
    actions: tuple[SchemaMigrationAction, ...]
    migration_version: str = "migration-v1"

    NESTED: ClassVar = {"source_revision": one(IRRevisionRef), "source_schema": one(SchemaFamilyRef), "target_schema": one(SchemaFamilyRef), "target_manifest": one(SchemaManifest), "compatibility": one(SchemaCompatibilityDeclaration), "actions": many(SchemaMigrationAction)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", require_identifier(self.plan_id, "plan_id"))
        for name, kind in (("source_revision", IRRevisionRef), ("source_schema", SchemaFamilyRef), ("target_schema", SchemaFamilyRef), ("target_manifest", SchemaManifest), ("compatibility", SchemaCompatibilityDeclaration)):
            object.__setattr__(self, name, kind.coerce(getattr(self, name), name))
        if self.compatibility.source != self.source_schema or self.compatibility.target != self.target_schema:
            raise IRIntegrityError("migration plan compatibility declaration has different direction/endpoints")
        if not self.compatibility.compatible and not self.compatibility.migration_required:
            raise IRAdmissionError("schema compatibility declaration neither permits nor requires migration")
        actions = tuple(SchemaMigrationAction.coerce(item, "actions[]") for item in self.actions)
        if len({item.action_id for item in actions}) != len(actions):
            raise IRSchemaError("migration action ids must be unique")
        object.__setattr__(self, "actions", tuple(sorted(actions, key=lambda item: item.action_id)))
        object.__setattr__(self, "migration_version", require_version(self.migration_version))


@dataclass(frozen=True)
class IRMigrationReceipt(IRRecord):
    receipt_id: str
    plan_id: str
    source_revision: IRRevisionRef
    result_revision: IRRevisionRef
    action_results: tuple[tuple[str, str], ...]
    receipt_digest: str

    NESTED: ClassVar = {"source_revision": one(IRRevisionRef), "result_revision": one(IRRevisionRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "receipt_id", require_identifier(self.receipt_id, "receipt_id"))
        object.__setattr__(self, "plan_id", require_identifier(self.plan_id, "plan_id"))
        object.__setattr__(self, "source_revision", IRRevisionRef.coerce(self.source_revision, "source_revision"))
        object.__setattr__(self, "result_revision", IRRevisionRef.coerce(self.result_revision, "result_revision"))
        if self.source_revision == self.result_revision:
            raise IRIntegrityError("migration must create a new revision")
        results = tuple(sorted((require_identifier(item[0], "action_results[].id"), require_text(item[1], "action_results[].result", maximum=256)) for item in self.action_results))
        if len({item[0] for item in results}) != len(results):
            raise IRSchemaError("migration receipt action result ids must be unique")
        object.__setattr__(self, "action_results", results)
        object.__setattr__(self, "receipt_digest", require_digest(self.receipt_digest, "receipt_digest"))

    def verify(self, source: IRRevision, result: IRRevision, plan: IRMigrationPlan) -> bool:
        if not (
            source.revision_ref == self.source_revision
            and result.revision_ref == self.result_revision
            and plan.plan_id == self.plan_id
            and plan.source_revision == self.source_revision
            and self.receipt_digest == content_digest({"receipt_id": self.receipt_id, "plan_id": self.plan_id, "source": self.source_revision, "result": self.result_revision, "actions": self.action_results})
        ):
            return False
        try:
            expected_nodes, expected_results = _apply_migration_actions(source, plan)
            expected = replace(
                source, revision_id=result.revision_id, nodes=expected_nodes,
                schema_manifest=plan.target_manifest, parent_ref=source.revision_ref,
            )
        except Exception:
            return False
        return self.action_results == expected_results and result.revision_digest == expected.revision_digest


def _apply_migration_actions(source: IRRevision, plan: IRMigrationPlan) -> tuple[tuple[Any, ...], tuple[tuple[str, str], ...]]:
    attrs_by_ref: dict[tuple[str, str], dict[str, Any]] = {
        node.identity_key: dict(node.attributes or {}) for node in source.nodes
    }
    results: list[tuple[str, str]] = []
    for action in plan.actions:
        touched = 0
        for attributes in attrs_by_ref.values():
            if action.operation == "RENAME_NODE_ATTRIBUTE" and action.source_key in attributes:
                if action.target_key in attributes:
                    raise IRIntegrityError(f"migration rename target {action.target_key} already exists")
                attributes[action.target_key] = attributes.pop(action.source_key)
                touched += 1
            elif action.operation == "DROP_OPTIONAL_NODE_ATTRIBUTE" and action.source_key in attributes:
                del attributes[action.source_key]
                touched += 1
        results.append((action.action_id, f"applied:{touched}"))
    new_nodes = tuple(replace(node, attributes=attrs_by_ref[node.identity_key]) for node in source.nodes)
    return new_nodes, tuple(sorted(results))


def migrate_revision(source: IRRevision, plan: IRMigrationPlan, *, new_revision_id: str, receipt_id: str) -> tuple[IRRevision, IRMigrationReceipt]:
    source, plan = IRRevision.coerce(source, "source"), IRMigrationPlan.coerce(plan, "plan")
    if source.revision_ref != plan.source_revision:
        raise IRIntegrityError("migration plan source revision is stale")
    new_nodes, results = _apply_migration_actions(source, plan)
    result = replace(source, revision_id=require_identifier(new_revision_id, "new_revision_id"), nodes=new_nodes, schema_manifest=plan.target_manifest, parent_ref=source.revision_ref)
    if result.revision_id == source.revision_id or result.revision_digest == source.revision_digest:
        raise IRIntegrityError("migration did not produce a distinct immutable revision")
    receipt_digest = content_digest({"receipt_id": receipt_id, "plan_id": plan.plan_id, "source": source.revision_ref, "result": result.revision_ref, "actions": results})
    receipt = IRMigrationReceipt(receipt_id, plan.plan_id, source.revision_ref, result.revision_ref, results, receipt_digest)
    if not receipt.verify(source, result, plan):
        raise IRIntegrityError("migration receipt does not verify against produced revisions")
    return result, receipt
