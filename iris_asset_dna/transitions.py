"""Proposal-governed mutation, same-identity revisions and explicit receipts."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .base import CanonicalRecord, SemanticRef, require_refs
from .enums import IdentityContinuity, MutationDecisionKind, TraitCriticality, TraitMutability
from .errors import DNAAdmissionError, DNAAuthorityError, DNAIntegrityError, DNAValidationError
from .identity import DNARevision, DNARevisionRef
from .traits import DNATrait
from .versions import content_digest, require_digest, require_identifier, require_semantic_path, require_text

__all__ = [
    "DNATraitChange",
    "DNAMutationProposal",
    "IdentityMutationDecision",
    "DNAMutationReceipt",
    "admit_same_identity_revision",
    "verify_mutation_receipt",
]


@dataclass(frozen=True)
class DNATraitChange(CanonicalRecord):
    path: str
    new_trait: DNATrait | None
    authority_exception_ref: SemanticRef | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", require_semantic_path(self.path))
        if self.new_trait is not None:
            if not isinstance(self.new_trait, DNATrait) or self.new_trait.path != self.path:
                raise DNAValidationError("new_trait must be a DNATrait at the declared path")
        if self.authority_exception_ref is not None and not isinstance(self.authority_exception_ref, SemanticRef):
            raise DNAValidationError("authority_exception_ref must be a SemanticRef")


@dataclass(frozen=True)
class DNAMutationProposal(CanonicalRecord):
    proposal_id: str
    dna_id: str
    source_revision_ref: DNARevisionRef
    changes: tuple[DNATraitChange, ...]
    reason: str
    requested_continuity: IdentityContinuity
    evidence_refs: tuple[SemanticRef, ...]
    policy_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposal_id", require_identifier(self.proposal_id, "proposal_id"))
        object.__setattr__(self, "dna_id", require_identifier(self.dna_id, "dna_id"))
        if not isinstance(self.source_revision_ref, DNARevisionRef) or self.source_revision_ref.dna_id != self.dna_id:
            raise DNAIntegrityError("mutation proposal must pin its exact source DNA revision")
        changes = tuple(self.changes)
        if not changes or any(not isinstance(item, DNATraitChange) for item in changes):
            raise DNAValidationError("mutation proposal needs typed trait changes")
        if len({item.path for item in changes}) != len(changes):
            raise DNAIntegrityError("mutation proposal has duplicate paths")
        object.__setattr__(self, "changes", tuple(sorted(changes, key=lambda item: item.path)))
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=2048))
        if not isinstance(self.requested_continuity, IdentityContinuity):
            object.__setattr__(self, "requested_continuity", IdentityContinuity(self.requested_continuity))
        object.__setattr__(self, "evidence_refs", require_refs(self.evidence_refs, "evidence_refs"))
        object.__setattr__(self, "policy_refs", require_refs(self.policy_refs, "policy_refs"))


@dataclass(frozen=True)
class IdentityMutationDecision(CanonicalRecord):
    decision_id: str
    proposal_id: str
    source_revision_ref: DNARevisionRef
    decision: MutationDecisionKind
    authority_ref: SemanticRef
    policy_ref: SemanticRef
    rationale: str
    evidence_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", require_identifier(self.decision_id, "decision_id"))
        object.__setattr__(self, "proposal_id", require_identifier(self.proposal_id, "proposal_id"))
        if not isinstance(self.source_revision_ref, DNARevisionRef):
            raise DNAValidationError("source_revision_ref must be a DNARevisionRef")
        if not isinstance(self.decision, MutationDecisionKind):
            object.__setattr__(self, "decision", MutationDecisionKind(self.decision))
        if not isinstance(self.authority_ref, SemanticRef) or not isinstance(self.policy_ref, SemanticRef):
            raise DNAAuthorityError("identity mutation decisions require explicit authority and policy refs")
        if self.authority_ref.owner_module != "m05":
            raise DNAAuthorityError("canonical identity mutation decisions remain under M05 authority")
        object.__setattr__(self, "rationale", require_text(self.rationale, "rationale", maximum=2048))
        object.__setattr__(self, "evidence_refs", require_refs(self.evidence_refs, "evidence_refs"))


@dataclass(frozen=True)
class DNAMutationReceipt(CanonicalRecord):
    proposal_id: str
    decision_id: str
    decision_ref: SemanticRef
    authority_ref: SemanticRef
    policy_ref: SemanticRef
    source_revision_ref: DNARevisionRef
    result_revision_ref: DNARevisionRef
    changed_paths: tuple[str, ...]
    preserved_paths: tuple[str, ...]
    source_fingerprint: str
    result_fingerprint: str
    fingerprint: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposal_id", require_identifier(self.proposal_id, "proposal_id"))
        object.__setattr__(self, "decision_id", require_identifier(self.decision_id, "decision_id"))
        for name in ("decision_ref", "authority_ref", "policy_ref"):
            if not isinstance(getattr(self, name), SemanticRef):
                raise DNAAuthorityError(f"mutation receipt requires {name}")
        if not isinstance(self.source_revision_ref, DNARevisionRef) or not isinstance(self.result_revision_ref, DNARevisionRef):
            raise DNAValidationError("mutation receipt requires pinned source and result revisions")
        if self.source_revision_ref.dna_id != self.result_revision_ref.dna_id or self.source_revision_ref == self.result_revision_ref:
            raise DNAIntegrityError("same-identity mutation receipt must bind a distinct later revision of the same dna_id")
        for name in ("changed_paths", "preserved_paths"):
            values = tuple(sorted({require_semantic_path(path) for path in getattr(self, name)}))
            object.__setattr__(self, name, values)
        if not self.changed_paths:
            raise DNAValidationError("mutation receipt requires a non-empty changed path surface")
        if set(self.changed_paths) & set(self.preserved_paths):
            raise DNAIntegrityError("mutation receipt paths cannot be both changed and preserved")
        for name in ("source_fingerprint", "result_fingerprint", "fingerprint"):
            object.__setattr__(self, name, require_digest(getattr(self, name), name))
        body = {
            "proposal_id": self.proposal_id,
            "decision_id": self.decision_id,
            "decision_ref": self.decision_ref,
            "authority_ref": self.authority_ref,
            "policy_ref": self.policy_ref,
            "source_revision_ref": self.source_revision_ref,
            "result_revision_ref": self.result_revision_ref,
            "changed_paths": self.changed_paths,
            "preserved_paths": self.preserved_paths,
            "source_fingerprint": self.source_fingerprint,
            "result_fingerprint": self.result_fingerprint,
        }
        if content_digest(body) != self.fingerprint:
            raise DNAIntegrityError("mutation receipt digest does not match its immutable fields")


def admit_same_identity_revision(
    source: DNARevision,
    proposal: DNAMutationProposal,
    decision: IdentityMutationDecision,
    *,
    new_revision_id: str,
    new_revision_number: int,
) -> tuple[DNARevision, DNAMutationReceipt]:
    if not isinstance(source, DNARevision) or not isinstance(proposal, DNAMutationProposal):
        raise DNAValidationError("mutation admission requires a source revision and proposal")
    if not isinstance(decision, IdentityMutationDecision):
        raise DNAAuthorityError("mutation admission requires an explicit IdentityMutationDecision")
    if (
        source.ref != proposal.source_revision_ref
        or decision.source_revision_ref != source.ref
        or decision.proposal_id != proposal.proposal_id
    ):
        raise DNAIntegrityError("mutation proposal and decision must bind the exact source revision")
    if decision.decision is not MutationDecisionKind.ADMIT_SAME_IDENTITY_REVISION:
        raise DNAAdmissionError(f"decision {decision.decision.value} does not admit a same-identity revision")
    traits = source.trait_map()
    changed: list[str] = []
    for change in proposal.changes:
        previous = traits.get(change.path)
        protected = previous is not None and (
            previous.criticality is TraitCriticality.IDENTITY_DEFINING
            or previous.mutability is TraitMutability.IMMUTABLE
        )
        protected = protected or (
            previous is None
            and change.new_trait is not None
            and (
                change.new_trait.criticality is TraitCriticality.IDENTITY_DEFINING
                or change.new_trait.mutability is TraitMutability.IMMUTABLE
            )
        )
        if protected and change.authority_exception_ref is None:
            raise DNAAuthorityError(
                f"protected trait {change.path} needs an explicit path-level authority exception"
            )
        if change.authority_exception_ref is not None and change.authority_exception_ref.owner_module != "m05":
            raise DNAAuthorityError("protected trait exceptions must be issued through M05 identity governance")
        if previous == change.new_trait:
            raise DNAAdmissionError(f"mutation proposal contains a no-op change at {change.path}")
        if change.new_trait is None:
            traits.pop(change.path, None)
        else:
            if previous is not None and (
                change.new_trait.criticality is not previous.criticality
                or change.new_trait.mutability is not previous.mutability
                or change.new_trait.schema_ref != previous.schema_ref
            ):
                raise DNAAdmissionError(
                    f"mutation cannot silently reclassify criticality, mutability, or schema at {change.path}"
                )
            traits[change.path] = change.new_trait
        changed.append(change.path)
    revision = replace(
        source,
        revision_id=require_identifier(new_revision_id, "new_revision_id"),
        revision_number=new_revision_number,
        parent_revision_refs=(source.ref,),
        traits=tuple(traits.values()),
        evidence_refs=require_refs(source.evidence_refs + proposal.evidence_refs, "evidence_refs"),
    )
    if revision.revision_id == source.revision_id or revision.revision_number <= source.revision_number:
        raise DNAIntegrityError("same-identity mutation must create a strictly later immutable revision")
    if revision.semantic_digest == source.semantic_digest:
        raise DNAAdmissionError("same-identity mutation does not change canonical semantic identity")
    receipt_body = {
        "proposal_id": proposal.proposal_id,
        "decision_id": decision.decision_id,
        "decision_ref": SemanticRef(
            "m05", "mutation.decision", decision.decision_id, "1",
            content_digest=content_digest(decision),
        ),
        "authority_ref": decision.authority_ref,
        "policy_ref": decision.policy_ref,
        "source_revision_ref": source.ref,
        "result_revision_ref": revision.ref,
        "changed_paths": tuple(sorted(changed)),
        "preserved_paths": tuple(sorted(set(source.trait_map()) - set(changed))),
        "source_fingerprint": source.semantic_digest,
        "result_fingerprint": revision.semantic_digest,
    }
    receipt = DNAMutationReceipt(
        proposal.proposal_id,
        decision.decision_id,
        receipt_body["decision_ref"],
        decision.authority_ref,
        decision.policy_ref,
        source.ref,
        revision.ref,
        receipt_body["changed_paths"],
        receipt_body["preserved_paths"],
        receipt_body["source_fingerprint"],
        receipt_body["result_fingerprint"],
        content_digest(receipt_body),
    )
    return revision, receipt


def verify_mutation_receipt(receipt: DNAMutationReceipt) -> bool:
    if not isinstance(receipt, DNAMutationReceipt):
        raise DNAValidationError("receipt must be a DNAMutationReceipt")
    if receipt.result_revision_ref.dna_id != receipt.source_revision_ref.dna_id:
        return False
    if receipt.result_revision_ref.revision_id == receipt.source_revision_ref.revision_id:
        return False
    body = {
        "proposal_id": receipt.proposal_id,
        "decision_id": receipt.decision_id,
        "decision_ref": receipt.decision_ref,
        "authority_ref": receipt.authority_ref,
        "policy_ref": receipt.policy_ref,
        "source_revision_ref": receipt.source_revision_ref,
        "result_revision_ref": receipt.result_revision_ref,
        "changed_paths": receipt.changed_paths,
        "preserved_paths": receipt.preserved_paths,
        "source_fingerprint": receipt.source_fingerprint,
        "result_fingerprint": receipt.result_fingerprint,
    }
    return receipt.source_fingerprint != receipt.result_fingerprint and content_digest(body) == receipt.fingerprint
