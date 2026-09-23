"""Representation anchors, explicit projection contracts and governed anchor history."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .base import CanonicalRecord, SemanticRef, require_refs
from .enums import AnchorAuthorityClass, AnchorLifecycleOperation
from .errors import DNAAdmissionError, DNAIntegrityError, DNAValidationError
from .identity import DNARevision, DNARevisionRef
from .versions import content_digest, require_identifier, require_semantic_path, require_text, require_version

__all__ = [
    "IdentityAnchor",
    "AnchorLifecycleEvent",
    "AnchorLifecycleReceipt",
    "apply_anchor_operation",
    "DNAProjectionContract",
    "ProjectionResult",
    "project_revision",
]


@dataclass(frozen=True)
class IdentityAnchor(CanonicalRecord):
    anchor_id: str
    dna_id: str
    authority_class: AnchorAuthorityClass
    target_ref: SemanticRef
    schema_version: str = "iris-m05-anchor-v1"
    source_revision_ref: DNARevisionRef | None = None
    validity_ref: SemanticRef | None = None
    lifecycle_history: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "anchor_id", require_identifier(self.anchor_id, "anchor_id"))
        object.__setattr__(self, "dna_id", require_identifier(self.dna_id, "dna_id"))
        if not isinstance(self.authority_class, AnchorAuthorityClass):
            object.__setattr__(self, "authority_class", AnchorAuthorityClass(self.authority_class))
        if not isinstance(self.target_ref, SemanticRef):
            raise DNAValidationError("target_ref must be a SemanticRef")
        object.__setattr__(self, "schema_version", require_version(self.schema_version, "schema_version"))
        if self.source_revision_ref is not None and not isinstance(self.source_revision_ref, DNARevisionRef):
            raise DNAValidationError("source_revision_ref must be a DNARevisionRef")
        if self.validity_ref is not None and not isinstance(self.validity_ref, SemanticRef):
            raise DNAValidationError("validity_ref must be a SemanticRef")
        object.__setattr__(self, "lifecycle_history", require_refs(self.lifecycle_history, "lifecycle_history"))
        if self.authority_class is AnchorAuthorityClass.OBSERVATION and self.target_ref.owner_module == "m05":
            raise DNAAdmissionError("observation anchors cannot claim canonical M05 ownership")


@dataclass(frozen=True)
class AnchorLifecycleEvent(CanonicalRecord):
    event_id: str
    operation: AnchorLifecycleOperation
    anchor_id: str
    source_revision_ref: DNARevisionRef
    authority_ref: SemanticRef | None
    policy_ref: SemanticRef | None
    reason: str
    evidence_refs: tuple[SemanticRef, ...] = ()
    previous_target_ref: SemanticRef | None = None
    next_target_ref: SemanticRef | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", require_identifier(self.event_id, "event_id"))
        object.__setattr__(self, "anchor_id", require_identifier(self.anchor_id, "anchor_id"))
        if not isinstance(self.operation, AnchorLifecycleOperation):
            object.__setattr__(self, "operation", AnchorLifecycleOperation(self.operation))
        if not isinstance(self.source_revision_ref, DNARevisionRef):
            raise DNAValidationError("source_revision_ref must be a DNARevisionRef")
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=2048))
        object.__setattr__(self, "evidence_refs", require_refs(self.evidence_refs, "evidence_refs"))
        for name in ("authority_ref", "policy_ref", "previous_target_ref", "next_target_ref"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, SemanticRef):
                raise DNAValidationError(f"{name} must be a SemanticRef")
        if self.operation in {
            AnchorLifecycleOperation.REBIND,
            AnchorLifecycleOperation.REVOKE,
            AnchorLifecycleOperation.RESTORE,
            AnchorLifecycleOperation.SUPERSEDE,
        } and (self.authority_ref is None or self.policy_ref is None):
            raise DNAAdmissionError("protected anchor lifecycle events require authority and policy refs")
        if self.operation is AnchorLifecycleOperation.REBIND and (
            self.previous_target_ref is None or self.next_target_ref is None or self.previous_target_ref == self.next_target_ref
        ):
            raise DNAIntegrityError("REBIND event must bind distinct previous and next targets")


@dataclass(frozen=True)
class AnchorLifecycleReceipt(CanonicalRecord):
    event: AnchorLifecycleEvent
    result_anchor: IdentityAnchor
    source_anchor_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.event, AnchorLifecycleEvent) or not isinstance(self.result_anchor, IdentityAnchor):
            raise DNAValidationError("receipt requires an event and result anchor")
        object.__setattr__(self, "source_anchor_id", require_identifier(self.source_anchor_id, "source_anchor_id"))
        if self.event.anchor_id != self.source_anchor_id or self.result_anchor.anchor_id != self.source_anchor_id:
            raise DNAIntegrityError("anchor lifecycle receipt must preserve the addressed anchor identity")


def apply_anchor_operation(
    anchor: IdentityAnchor,
    operation: AnchorLifecycleOperation,
    *,
    event_id: str,
    source_revision_ref: DNARevisionRef,
    reason: str,
    authority_ref: SemanticRef | None = None,
    policy_ref: SemanticRef | None = None,
    new_target_ref: SemanticRef | None = None,
    restore_authority_class: AnchorAuthorityClass | None = None,
    evidence_refs: tuple[SemanticRef, ...] = (),
) -> AnchorLifecycleReceipt:
    if not isinstance(anchor, IdentityAnchor):
        raise DNAValidationError("anchor must be an IdentityAnchor")
    if not isinstance(operation, AnchorLifecycleOperation):
        operation = AnchorLifecycleOperation(operation)
    if source_revision_ref.dna_id != anchor.dna_id:
        raise DNAIntegrityError("anchor lifecycle source revision must belong to the anchor dna_id")
    guarded = {
        AnchorLifecycleOperation.REBIND,
        AnchorLifecycleOperation.REVOKE,
        AnchorLifecycleOperation.RESTORE,
        AnchorLifecycleOperation.SUPERSEDE,
    }
    if anchor.authority_class in {
        AnchorAuthorityClass.CANONICAL,
        AnchorAuthorityClass.BOUND_EXTERNAL,
        AnchorAuthorityClass.REVOKED,
    } and operation in guarded:
        if authority_ref is None or policy_ref is None:
            raise DNAAdmissionError("protected anchor lifecycle changes require authority and policy refs")
    if anchor.authority_class in {AnchorAuthorityClass.OBSERVATION, AnchorAuthorityClass.PROPOSED} and operation in guarded:
        raise DNAAdmissionError("observation/proposed anchors cannot be promoted through lifecycle operations")
    if anchor.authority_class is AnchorAuthorityClass.REVOKED and operation not in {
        AnchorLifecycleOperation.RESTORE,
        AnchorLifecycleOperation.INVALIDATE_EVIDENCE,
    }:
        raise DNAAdmissionError("a revoked anchor must be explicitly restored before another lifecycle change")
    next_target = anchor.target_ref
    next_class = anchor.authority_class
    if operation is AnchorLifecycleOperation.REBIND:
        if new_target_ref is None:
            raise DNAValidationError("REBIND requires a new_target_ref")
        if new_target_ref == anchor.target_ref:
            raise DNAIntegrityError("REBIND must identify a different representation target")
        next_target = new_target_ref
    elif operation in {AnchorLifecycleOperation.REVOKE, AnchorLifecycleOperation.SUPERSEDE}:
        next_class = AnchorAuthorityClass.REVOKED
    elif operation is AnchorLifecycleOperation.RESTORE:
        if anchor.authority_class is not AnchorAuthorityClass.REVOKED:
            raise DNAAdmissionError("RESTORE applies only to a revoked anchor")
        if restore_authority_class in {None, AnchorAuthorityClass.REVOKED, AnchorAuthorityClass.OBSERVATION}:
            raise DNAAdmissionError("RESTORE requires a non-observation authority class")
        next_class = restore_authority_class
    event = AnchorLifecycleEvent(
        event_id=event_id,
        operation=operation,
        anchor_id=anchor.anchor_id,
        source_revision_ref=source_revision_ref,
        authority_ref=authority_ref,
        policy_ref=policy_ref,
        reason=reason,
        evidence_refs=evidence_refs,
        previous_target_ref=anchor.target_ref,
        next_target_ref=next_target,
    )
    event_ref = SemanticRef(
        "m05",
        "anchor.lifecycle.event",
        event.event_id,
        "1",
        revision_id=source_revision_ref.revision_id,
        content_digest=content_digest(event),
    )
    result = replace(
        anchor,
        target_ref=next_target,
        authority_class=next_class,
        source_revision_ref=source_revision_ref,
        lifecycle_history=anchor.lifecycle_history + (event_ref,),
    )
    return AnchorLifecycleReceipt(event, result, anchor.anchor_id)


@dataclass(frozen=True)
class DNAProjectionContract(CanonicalRecord):
    contract_id: str
    source_revision_ref: DNARevisionRef
    required_trait_paths: tuple[str, ...]
    optional_trait_paths: tuple[str, ...] = ()
    preserved_trait_paths: tuple[str, ...] = ()
    projection_owner: str = "m04"
    policy_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", require_identifier(self.contract_id, "contract_id"))
        if not isinstance(self.source_revision_ref, DNARevisionRef):
            raise DNAValidationError("source_revision_ref must be a DNARevisionRef")
        for name in ("required_trait_paths", "optional_trait_paths", "preserved_trait_paths"):
            items = tuple(sorted({require_semantic_path(item, f"{name}[]") for item in getattr(self, name)}))
            object.__setattr__(self, name, items)
        if set(self.required_trait_paths) & set(self.optional_trait_paths):
            raise DNAValidationError("required and optional projection paths must be disjoint")
        if not set(self.required_trait_paths) <= set(self.preserved_trait_paths):
            raise DNAValidationError("every required projected path must be explicitly preserved")
        object.__setattr__(self, "projection_owner", require_identifier(self.projection_owner, "projection_owner"))
        object.__setattr__(self, "policy_refs", require_refs(self.policy_refs, "policy_refs"))


@dataclass(frozen=True)
class ProjectionResult(CanonicalRecord):
    contract_id: str
    source_revision_ref: DNARevisionRef
    projected_traits: tuple[Any, ...]
    omitted_optional_paths: tuple[str, ...]
    fingerprint: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", require_identifier(self.contract_id, "contract_id"))
        if not isinstance(self.source_revision_ref, DNARevisionRef):
            raise DNAValidationError("source_revision_ref must be a DNARevisionRef")
        from .traits import DNATrait
        if any(not isinstance(item, DNATrait) for item in self.projected_traits):
            raise DNAValidationError("projected traits must be typed DNATrait records")
        object.__setattr__(self, "omitted_optional_paths", tuple(sorted({require_semantic_path(item) for item in self.omitted_optional_paths})))
        from .versions import require_digest
        object.__setattr__(self, "fingerprint", require_digest(self.fingerprint, "fingerprint"))


def project_revision(revision: DNARevision, contract: DNAProjectionContract) -> ProjectionResult:
    if not isinstance(revision, DNARevision) or not isinstance(contract, DNAProjectionContract):
        raise DNAValidationError("project_revision requires a DNARevision and DNAProjectionContract")
    if revision.ref != contract.source_revision_ref:
        raise DNAIntegrityError("projection contract must pin the exact source revision digest")
    traits = revision.trait_map()
    missing = sorted(set(contract.required_trait_paths) - set(traits))
    if missing:
        raise DNAAdmissionError(f"mandatory projected traits are missing: {missing}")
    selected = tuple(traits[path] for path in contract.required_trait_paths + contract.optional_trait_paths if path in traits)
    omitted = tuple(path for path in contract.optional_trait_paths if path not in traits)
    return ProjectionResult(
        contract.contract_id,
        revision.ref,
        selected,
        omitted,
        content_digest(selected),
    )
