"""Declarative, explicit-loss migration plans and deterministic immutable receipts."""

from __future__ import annotations

from dataclasses import dataclass

from .base import CanonicalRecord, SemanticRef, require_refs
from .enums import DNAFamily, IdentityContinuity, MigrationActionKind
from .errors import DNAAdmissionError, DNACompatibilityError, DNAIntegrityError, DNAAuthorityError, DNAValidationError
from .identity import AssetDNAIdentity, DNARevision, DNARevisionRef, validate_revision
from .limits import DEFAULT_LIMITS, DNARecordLimits
from .traits import DNATrait, TraitSchemaRegistry, DEFAULT_TRAIT_SCHEMAS
from .versions import content_digest, require_digest, require_identifier, require_semantic_path, require_text, require_version

__all__ = [
    "MigrationAction",
    "DNAMigrationPlan",
    "DNAMigrationReceipt",
    "MigrationResult",
    "apply_migration",
    "verify_migration_receipt",
]


@dataclass(frozen=True)
class MigrationAction(CanonicalRecord):
    kind: MigrationActionKind
    target_path: str
    source_path: str | None = None
    default_trait: DNATrait | None = None
    loss_declared: bool = False
    loss_reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MigrationActionKind):
            object.__setattr__(self, "kind", MigrationActionKind(self.kind))
        object.__setattr__(self, "target_path", require_semantic_path(self.target_path, "target_path"))
        if self.source_path is not None:
            object.__setattr__(self, "source_path", require_semantic_path(self.source_path, "source_path"))
        if self.default_trait is not None and not isinstance(self.default_trait, DNATrait):
            raise DNAValidationError("default_trait must be a DNATrait")
        if self.loss_reason is not None:
            object.__setattr__(self, "loss_reason", require_text(self.loss_reason, "loss_reason", maximum=2048))
        if self.kind is MigrationActionKind.DEFAULT:
            if self.source_path is not None or self.default_trait is None or self.default_trait.path != self.target_path:
                raise DNAValidationError("DEFAULT requires a target-matching typed default trait and no source path")
        else:
            if self.source_path is None or self.default_trait is not None:
                raise DNAValidationError(f"{self.kind.value} requires source_path and no default_trait")
        if self.kind is MigrationActionKind.DROP:
            if self.target_path != self.source_path or not self.loss_declared or self.loss_reason is None:
                raise DNACompatibilityError("DROP requires a declared path-level loss and reason")
        elif self.loss_declared or self.loss_reason is not None:
            raise DNAValidationError("loss declarations apply only to explicit DROP actions")
        if self.kind is MigrationActionKind.RENAME and self.source_path == self.target_path:
            raise DNAValidationError("RENAME must change the semantic path")
        if self.kind is MigrationActionKind.PRESERVE and self.source_path != self.target_path:
            raise DNAValidationError("PRESERVE must retain the semantic path")


@dataclass(frozen=True)
class DNAMigrationPlan(CanonicalRecord):
    plan_id: str
    source_ref: DNARevisionRef
    source_schema_family: str
    source_schema_version: str
    target_family: DNAFamily
    target_schema_family: str
    target_schema_version: str
    actions: tuple[MigrationAction, ...]
    identity_continuity: IdentityContinuity
    authority_ref: SemanticRef
    policy_ref: SemanticRef
    result_anchor_refs: tuple[SemanticRef, ...] | None = None
    result_domain_link_refs: tuple[SemanticRef, ...] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", require_identifier(self.plan_id, "plan_id"))
        if not isinstance(self.source_ref, DNARevisionRef):
            raise DNAValidationError("source_ref must be a DNARevisionRef")
        for name in ("source_schema_family", "target_schema_family"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        object.__setattr__(self, "source_schema_version", require_version(self.source_schema_version, "source_schema_version"))
        object.__setattr__(self, "target_schema_version", require_version(self.target_schema_version, "target_schema_version"))
        if not isinstance(self.target_family, DNAFamily):
            object.__setattr__(self, "target_family", DNAFamily(self.target_family))
        if not isinstance(self.identity_continuity, IdentityContinuity):
            object.__setattr__(self, "identity_continuity", IdentityContinuity(self.identity_continuity))
        if not isinstance(self.authority_ref, SemanticRef) or not isinstance(self.policy_ref, SemanticRef):
            raise DNAAuthorityError("migration plans require authority and policy refs")
        if self.authority_ref.owner_module != "m05":
            raise DNAAuthorityError("canonical identity migration decisions remain under M05 authority")
        actions = tuple(self.actions)
        if not actions or any(not isinstance(item, MigrationAction) for item in actions):
            raise DNAValidationError("migration plan requires declarative typed actions")
        sources = [item.source_path for item in actions if item.source_path is not None]
        targets = [item.target_path for item in actions if item.kind is not MigrationActionKind.DROP]
        if len(sources) != len(set(sources)) or len(targets) != len(set(targets)):
            raise DNACompatibilityError("migration actions cannot duplicate source or result paths")
        object.__setattr__(self, "actions", tuple(sorted(actions, key=lambda item: (item.source_path or "", item.target_path))))
        for name in ("result_anchor_refs", "result_domain_link_refs"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_refs(value, name))

    @property
    def loss_surface(self) -> tuple[str, ...]:
        return tuple(sorted(item.source_path for item in self.actions if item.kind is MigrationActionKind.DROP and item.source_path is not None))


@dataclass(frozen=True)
class DNAMigrationReceipt(CanonicalRecord):
    plan_id: str
    plan_digest: str
    authority_ref: SemanticRef
    policy_ref: SemanticRef
    source_ref: DNARevisionRef
    result_ref: DNARevisionRef
    transformed_paths: tuple[str, ...]
    preserved_paths: tuple[str, ...]
    dropped_paths: tuple[str, ...]
    defaulted_paths: tuple[str, ...]
    identity_continuity: IdentityContinuity
    source_fingerprint: str
    result_fingerprint: str
    receipt_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", require_identifier(self.plan_id, "plan_id"))
        object.__setattr__(self, "plan_digest", require_digest(self.plan_digest, "plan_digest"))
        if not isinstance(self.authority_ref, SemanticRef) or not isinstance(self.policy_ref, SemanticRef):
            raise DNAAuthorityError("migration receipt must preserve authority and policy refs")
        if not isinstance(self.source_ref, DNARevisionRef) or not isinstance(self.result_ref, DNARevisionRef):
            raise DNAValidationError("migration receipt requires pinned source and result revisions")
        if not isinstance(self.identity_continuity, IdentityContinuity):
            object.__setattr__(self, "identity_continuity", IdentityContinuity(self.identity_continuity))
        for name in ("transformed_paths", "preserved_paths", "dropped_paths", "defaulted_paths"):
            object.__setattr__(self, name, tuple(sorted({require_semantic_path(path) for path in getattr(self, name)})))
        surfaces = [set(getattr(self, name)) for name in ("transformed_paths", "preserved_paths", "dropped_paths", "defaulted_paths")]
        if any(surfaces[left] & surfaces[right] for left in range(len(surfaces)) for right in range(left + 1, len(surfaces))):
            raise DNAIntegrityError("migration receipt path surfaces must be disjoint")
        if self.identity_continuity is IdentityContinuity.BREAK_REQUIRED and self.source_ref.dna_id == self.result_ref.dna_id:
            raise DNAIntegrityError("BREAK_REQUIRED migration receipt must identify a new dna_id")
        if self.identity_continuity is not IdentityContinuity.BREAK_REQUIRED and self.source_ref.dna_id != self.result_ref.dna_id:
            raise DNAIntegrityError("identity-preserving migration receipt must retain its dna_id")
        for name in ("source_fingerprint", "result_fingerprint", "receipt_digest"):
            object.__setattr__(self, name, require_digest(getattr(self, name), name))
        body = {
            "plan_id": self.plan_id,
            "plan_digest": self.plan_digest,
            "authority_ref": self.authority_ref,
            "policy_ref": self.policy_ref,
            "source_ref": self.source_ref,
            "result_ref": self.result_ref,
            "transformed_paths": self.transformed_paths,
            "preserved_paths": self.preserved_paths,
            "dropped_paths": self.dropped_paths,
            "defaulted_paths": self.defaulted_paths,
            "identity_continuity": self.identity_continuity.value,
            "source_fingerprint": self.source_fingerprint,
            "result_fingerprint": self.result_fingerprint,
        }
        if content_digest(body) != self.receipt_digest:
            raise DNAIntegrityError("migration receipt digest does not match its immutable fields")


@dataclass(frozen=True)
class MigrationResult(CanonicalRecord):
    identity: AssetDNAIdentity
    revision: DNARevision
    receipt: DNAMigrationReceipt

    def __post_init__(self) -> None:
        if not isinstance(self.identity, AssetDNAIdentity) or not isinstance(self.revision, DNARevision) or not isinstance(self.receipt, DNAMigrationReceipt):
            raise DNAValidationError("migration result requires typed identity, revision and receipt")
        if self.identity.dna_id != self.revision.dna_id or self.receipt.result_ref != self.revision.ref:
            raise DNAIntegrityError("migration result identity, revision and receipt do not agree")


def apply_migration(
    source: DNARevision,
    plan: DNAMigrationPlan,
    *,
    new_revision_id: str,
    new_revision_number: int,
    new_dna_id: str | None = None,
    schemas: TraitSchemaRegistry = DEFAULT_TRAIT_SCHEMAS,
    limits: DNARecordLimits = DEFAULT_LIMITS,
) -> MigrationResult:
    if not isinstance(source, DNARevision) or not isinstance(plan, DNAMigrationPlan):
        raise DNAValidationError("apply_migration requires a source revision and DNAMigrationPlan")
    if source.ref != plan.source_ref:
        raise DNAIntegrityError("migration plan must bind the exact immutable source revision")
    if source.schema_version != plan.source_schema_version:
        raise DNACompatibilityError("migration source schema version does not match the pinned revision")
    actions = {item.source_path: item for item in plan.actions if item.source_path is not None}
    defaults = [item for item in plan.actions if item.kind is MigrationActionKind.DEFAULT]
    if set(actions) != set(source.trait_map()):
        raise DNACompatibilityError("migration plan must explicitly preserve, rename, or drop every source trait")
    mapped: dict[str, DNATrait] = {}
    transformed: list[str] = []
    preserved: list[str] = []
    dropped: list[str] = []
    defaulted: list[str] = []
    traits = source.trait_map()
    for source_path, action in actions.items():
        source_trait = traits[source_path]
        if (
            action.kind is MigrationActionKind.DROP
            and source_trait.criticality.value == "IDENTITY_DEFINING"
            and plan.identity_continuity is not IdentityContinuity.BREAK_REQUIRED
        ):
            raise DNACompatibilityError(
                f"identity-defining trait {source_path} cannot be dropped while preserving identity"
            )
        if (
            action.kind is MigrationActionKind.DROP
            and source_trait.mutability.value == "IMMUTABLE"
            and plan.identity_continuity is not IdentityContinuity.BREAK_REQUIRED
        ):
            raise DNACompatibilityError(
                f"immutable trait {source_path} cannot be dropped while preserving identity"
            )
        if action.kind is MigrationActionKind.DROP:
            dropped.append(source_path)
        elif action.kind is MigrationActionKind.PRESERVE:
            mapped[action.target_path] = source_trait
            preserved.append(source_path)
        elif action.kind is MigrationActionKind.RENAME:
            mapped[action.target_path] = _retarget_trait(source_trait, action.target_path)
            transformed.append(source_path)
        else:
            raise DNAValidationError("source action must be PRESERVE, RENAME, or DROP")
    for action in defaults:
        if action.target_path in mapped:
            raise DNACompatibilityError(f"default path {action.target_path} collides with migrated traits")
        assert action.default_trait is not None
        mapped[action.target_path] = action.default_trait
        defaulted.append(action.target_path)
    if plan.identity_continuity is IdentityContinuity.BREAK_REQUIRED:
        if new_dna_id is None:
            raise DNAAdmissionError("BREAK_REQUIRED migration must supply a new dna_id")
        new_dna_id = require_identifier(new_dna_id, "new_dna_id")
        if new_dna_id == source.dna_id:
            raise DNAIntegrityError("BREAK_REQUIRED migration must create a new dna_id")
    elif new_dna_id is not None:
        raise DNAAdmissionError("new_dna_id is only valid for BREAK_REQUIRED migration")
    result_id = new_dna_id or source.dna_id
    revision = DNARevision(
        result_id,
        new_revision_id,
        new_revision_number,
        plan.target_family,
        source.identity_level,
        tuple(mapped.values()),
        schema_version=plan.target_schema_version,
        contract_version=source.contract_version,
        profile_ref=source.profile_ref,
        parent_revision_refs=(source.ref,) if result_id == source.dna_id else (),
        anchor_refs=source.anchor_refs if plan.result_anchor_refs is None else plan.result_anchor_refs,
        component_refs=source.component_refs,
        domain_link_refs=source.domain_link_refs if plan.result_domain_link_refs is None else plan.result_domain_link_refs,
        provenance_refs=source.provenance_refs,
        policy_refs=tuple(set(source.policy_refs + (plan.policy_ref,))),
        rights_privacy_refs=source.rights_privacy_refs,
        evidence_refs=source.evidence_refs,
    )
    if result_id == source.dna_id and revision.revision_id == source.revision_id:
        raise DNAIntegrityError("migration must create a distinct immutable revision ID")
    if result_id == source.dna_id and new_revision_number <= source.revision_number:
        raise DNAIntegrityError("migration must create a strictly later immutable revision")
    if result_id != source.dna_id and new_revision_number != 1:
        raise DNAIntegrityError("identity-break migration must start the new identity at revision 1")
    if revision.semantic_digest == source.semantic_digest and plan.identity_continuity is not IdentityContinuity.BREAK_REQUIRED:
        raise DNACompatibilityError("migration plan does not change canonical schema or identity semantics")
    validate_revision(revision, schemas=schemas, limits=limits)
    identity = AssetDNAIdentity(
        result_id,
        plan.target_family.value.lower(),
        plan.target_family,
        namespace="iris.asset",
        policy_refs=(plan.policy_ref,),
        provenance_refs=source.provenance_refs,
        rights_privacy_refs=source.rights_privacy_refs,
    )
    receipt_body = {
        "plan_id": plan.plan_id,
        "plan_digest": content_digest(plan),
        "authority_ref": plan.authority_ref,
        "policy_ref": plan.policy_ref,
        "source_ref": source.ref,
        "result_ref": revision.ref,
        "transformed_paths": tuple(sorted(transformed)),
        "preserved_paths": tuple(sorted(preserved)),
        "dropped_paths": tuple(sorted(dropped)),
        "defaulted_paths": tuple(sorted(defaulted)),
        "identity_continuity": plan.identity_continuity.value,
        "source_fingerprint": source.semantic_digest,
        "result_fingerprint": revision.semantic_digest,
    }
    receipt = DNAMigrationReceipt(
        plan.plan_id,
        receipt_body["plan_digest"],
        plan.authority_ref,
        plan.policy_ref,
        source.ref,
        revision.ref,
        receipt_body["transformed_paths"],
        receipt_body["preserved_paths"],
        receipt_body["dropped_paths"],
        receipt_body["defaulted_paths"],
        plan.identity_continuity,
        source.semantic_digest,
        revision.semantic_digest,
        content_digest(receipt_body),
    )
    return MigrationResult(identity, revision, receipt)


def _retarget_trait(trait: DNATrait, path: str) -> DNATrait:
    from dataclasses import replace
    return replace(trait, path=path)


def verify_migration_receipt(receipt: DNAMigrationReceipt) -> bool:
    if not isinstance(receipt, DNAMigrationReceipt):
        raise DNAValidationError("receipt must be a DNAMigrationReceipt")
    body = {
        "plan_id": receipt.plan_id,
        "plan_digest": receipt.plan_digest,
        "authority_ref": receipt.authority_ref,
        "policy_ref": receipt.policy_ref,
        "source_ref": receipt.source_ref,
        "result_ref": receipt.result_ref,
        "transformed_paths": receipt.transformed_paths,
        "preserved_paths": receipt.preserved_paths,
        "dropped_paths": receipt.dropped_paths,
        "defaulted_paths": receipt.defaulted_paths,
        "identity_continuity": receipt.identity_continuity.value,
        "source_fingerprint": receipt.source_fingerprint,
        "result_fingerprint": receipt.result_fingerprint,
    }
    return (
        (
            receipt.source_fingerprint != receipt.result_fingerprint
            or (
                receipt.identity_continuity is IdentityContinuity.BREAK_REQUIRED
                and receipt.source_ref.dna_id != receipt.result_ref.dna_id
            )
        )
        and content_digest(body) == receipt.receipt_digest
    )
