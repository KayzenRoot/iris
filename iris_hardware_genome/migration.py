"""Declarative immutable schema migration; no executable migration payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import M07Record, content_digest, freeze_json
from .enums import MigrationOperation
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError, HardwareGenomeValidationError
from .genome import HardwareGenome, create_hardware_genome
from .schema import SchemaCompatibilityDeclaration, SchemaDescriptor
from .versions import MIGRATION_VERSION, require_identifier, require_version

__all__ = ["SchemaMigrationAction", "SchemaMigrationPlan", "SchemaMigrationReceipt", "migrate_genome", "verify_migration_receipt"]


@dataclass(frozen=True)
class SchemaMigrationAction(M07Record):
    action_id: str
    operation: MigrationOperation
    source_key: str | None = None
    target_key: str | None = None
    value: Any = None
    optional_only: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "action_id", require_identifier(self.action_id, "action_id"))
        if type(self.operation) is not MigrationOperation:
            raise HardwareGenomeValidationError("migration operation must be a closed declarative enum")
        for field in ("source_key", "target_key"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_identifier(value, field))
        if type(self.optional_only) is not bool:
            raise HardwareGenomeValidationError("optional_only must be bool")
        if self.operation is MigrationOperation.ADD_OPTIONAL_EXTENSION:
            if self.source_key is not None or self.target_key is None or self.value is None:
                raise HardwareGenomeValidationError("adding an extension requires a target key and inert value")
        elif self.operation is MigrationOperation.RENAME_OPTIONAL_EXTENSION:
            if not self.optional_only or self.source_key is None or self.target_key is None or self.value is not None:
                raise HardwareGenomeAdmissionError("extension rename must target explicitly optional data")
        elif self.operation is MigrationOperation.DROP_OPTIONAL_EXTENSION:
            if not self.optional_only or self.source_key is None or self.target_key is not None or self.value is not None:
                raise HardwareGenomeAdmissionError("lossy drop is permitted only for explicitly optional extensions")
        elif self.operation is MigrationOperation.CLARIFY_METADATA:
            if self.source_key is not None or self.target_key is not None or self.value is not None:
                raise HardwareGenomeValidationError("metadata clarification cannot carry data operations")
        if self.value is not None:
            object.__setattr__(self, "value", freeze_json(self.value, "migration value"))


@dataclass(frozen=True)
class SchemaMigrationPlan(M07Record):
    plan_id: str
    source_genome_id: str
    source_schema_version: str
    target_schema: SchemaDescriptor
    compatibility: SchemaCompatibilityDeclaration
    actions: tuple[SchemaMigrationAction, ...]
    migration_version: str = MIGRATION_VERSION

    def __post_init__(self) -> None:
        for field in ("plan_id", "source_genome_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "source_schema_version", require_version(self.source_schema_version, "source_schema_version"))
        object.__setattr__(self, "target_schema", SchemaDescriptor.coerce(self.target_schema, "target_schema"))
        object.__setattr__(self, "compatibility", SchemaCompatibilityDeclaration.coerce(self.compatibility, "compatibility"))
        if str(self.compatibility.source) != self.source_schema_version or self.compatibility.target != self.target_schema.version:
            raise HardwareGenomeIntegrityError("migration compatibility declaration has different source/target versions")
        actions = tuple(SchemaMigrationAction.coerce(item, "actions[]") for item in self.actions)
        if len({item.action_id for item in actions}) != len(actions):
            raise HardwareGenomeValidationError("migration action ids must be unique")
        object.__setattr__(self, "actions", tuple(sorted(actions, key=lambda item: item.action_id)))
        object.__setattr__(self, "migration_version", require_version(self.migration_version, "migration_version"))


@dataclass(frozen=True)
class SchemaMigrationReceipt(M07Record):
    receipt_id: str
    plan_id: str
    source_genome_id: str
    result_genome_id: str
    action_results: tuple[tuple[str, str], ...]
    loss_classification: str
    lineage_parent_genome_id: str
    receipt_digest: str

    def __post_init__(self) -> None:
        from .versions import require_digest

        for field in ("receipt_id", "plan_id", "source_genome_id", "result_genome_id", "lineage_parent_genome_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        results = tuple(sorted((require_identifier(item[0], "action id"), require_identifier(item[1], "action result")) for item in self.action_results))
        if len({item[0] for item in results}) != len(results):
            raise HardwareGenomeIntegrityError("migration receipt repeats an action id")
        object.__setattr__(self, "action_results", results)
        if self.loss_classification not in {"LOSSLESS", "LOSSY"}:
            raise HardwareGenomeValidationError("migration loss classification must be explicit")
        object.__setattr__(self, "receipt_digest", require_digest(self.receipt_digest, "receipt_digest"))
        if self.source_genome_id == self.result_genome_id or self.lineage_parent_genome_id != self.source_genome_id:
            raise HardwareGenomeIntegrityError("migration must create a new result with exact source lineage")


def _apply_actions(source: HardwareGenome, plan: SchemaMigrationPlan) -> tuple[dict[str, Any], tuple[tuple[str, str], ...], str]:
    extensions = dict(source.extensions)
    results: list[tuple[str, str]] = []
    lossy = False
    for action in plan.actions:
        if action.operation is MigrationOperation.ADD_OPTIONAL_EXTENSION:
            if action.target_key is None:
                raise HardwareGenomeIntegrityError("validated add-extension action lost its target key")
            if action.target_key in extensions:
                raise HardwareGenomeIntegrityError("migration extension target already exists")
            extensions[action.target_key] = action.value
            result = "added"
        elif action.operation is MigrationOperation.RENAME_OPTIONAL_EXTENSION:
            if action.source_key is None or action.target_key is None:
                raise HardwareGenomeIntegrityError("validated rename action lost its source or target key")
            if action.source_key not in extensions:
                raise HardwareGenomeAdmissionError("migration source extension is not present")
            if action.target_key in extensions:
                raise HardwareGenomeIntegrityError("migration rename target already exists")
            extensions[action.target_key] = extensions.pop(action.source_key)
            result = "renamed"
        elif action.operation is MigrationOperation.DROP_OPTIONAL_EXTENSION:
            if action.source_key is None:
                raise HardwareGenomeIntegrityError("validated drop-extension action lost its source key")
            if action.source_key not in extensions:
                raise HardwareGenomeAdmissionError("migration source extension is not present")
            del extensions[action.source_key]
            result = "dropped_optional"
            lossy = True
        else:
            result = "clarified_without_semantic_change"
        results.append((action.action_id, result))
    return extensions, tuple(sorted(results)), "LOSSY" if lossy else "LOSSLESS"


def migrate_genome(source: HardwareGenome, plan: SchemaMigrationPlan, *, result_time_ms: int, receipt_id: str) -> tuple[HardwareGenome, SchemaMigrationReceipt]:
    source = HardwareGenome.coerce(source, "source")
    plan = SchemaMigrationPlan.coerce(plan, "plan")
    if source.genome_id != plan.source_genome_id or str(source.schema.version) != plan.source_schema_version:
        raise HardwareGenomeIntegrityError("migration plan is stale or bound to another source genome")
    if source.schema.schema_id != plan.target_schema.schema_id:
        raise HardwareGenomeAdmissionError("schema migration cannot change the canonical schema family")
    if plan.compatibility.source != source.schema.version or plan.compatibility.target != plan.target_schema.version:
        raise HardwareGenomeIntegrityError("migration compatibility endpoints differ from the source/result schemas")
    if plan.compatibility.level.value == "MAJOR" and not plan.compatibility.migration_required:
        raise HardwareGenomeAdmissionError("MAJOR migration requires explicit loss/compatibility analysis")
    extensions, action_results, loss = _apply_actions(source, plan)
    result = create_hardware_genome(
        discovery=source.discovery, subjects=source.subjects, passports=source.passports, facts=source.facts,
        semantic_registry=source.semantic_registry,
        capabilities=source.capabilities, backend_relationships=source.backend_relationships,
        version_facts=source.version_facts, driver_skew=source.driver_skew,
        precision_features=source.precision_features, media_capabilities=source.media_capabilities,
        topology=source.topology, telemetry=source.telemetry, conflicts=source.conflicts,
        confidence=source.confidence, extensions=extensions, created_at_ms=result_time_ms,
        producer_version=source.producer_version, schema=plan.target_schema,
        claim_status=source.claim_status, parent_genome_id=source.genome_id,
    )
    receipt_material = {
        "receipt_id": receipt_id, "plan_id": plan.plan_id, "source": source.genome_id,
        "result": result.genome_id, "actions": action_results, "loss": loss,
    }
    receipt = SchemaMigrationReceipt(
        receipt_id, plan.plan_id, source.genome_id, result.genome_id, action_results, loss,
        source.genome_id, content_digest(receipt_material),
    )
    if result.genome_id == source.genome_id:
        raise HardwareGenomeIntegrityError("migration did not create a new immutable genome snapshot")
    verify_migration_receipt(source, result, plan, receipt)
    return result, receipt


def verify_migration_receipt(source: HardwareGenome, result: HardwareGenome, plan: SchemaMigrationPlan, receipt: SchemaMigrationReceipt) -> bool:
    source, result = HardwareGenome.coerce(source, "source"), HardwareGenome.coerce(result, "result")
    plan, receipt = SchemaMigrationPlan.coerce(plan, "plan"), SchemaMigrationReceipt.coerce(receipt, "receipt")
    if (
        receipt.plan_id != plan.plan_id
        or receipt.source_genome_id != source.genome_id
        or receipt.result_genome_id != result.genome_id
        or result.parent_genome_id != source.genome_id
        or result.schema != plan.target_schema
    ):
        raise HardwareGenomeIntegrityError("migration receipt lineage or schema binding is invalid")
    extensions, action_results, loss = _apply_actions(source, plan)
    expected_material = {
        "receipt_id": receipt.receipt_id, "plan_id": plan.plan_id, "source": source.genome_id,
        "result": result.genome_id, "actions": action_results, "loss": loss,
    }
    if extensions != dict(result.extensions) or action_results != receipt.action_results or loss != receipt.loss_classification or content_digest(expected_material) != receipt.receipt_digest:
        raise HardwareGenomeIntegrityError("migration receipt does not prove the exact immutable transformation")
    return True
