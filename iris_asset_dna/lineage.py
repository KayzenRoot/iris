"""Semantic identity lineage that cannot become project or production branching."""

from __future__ import annotations

from dataclasses import dataclass

from .base import CanonicalRecord, SemanticRef, require_refs
from .enums import LineageRelation
from .errors import DNAAdmissionError, DNAIntegrityError, DNAAuthorityError, DNAValidationError
from .identity import AssetDNAIdentity, DNARevision, DNARevisionRef
from .versions import content_digest, require_identifier, require_semantic_path, require_text

__all__ = [
    "DNAIdentityLineageEdge",
    "IdentityAlias",
    "IdentityEquivalenceClaim",
    "DNAConflict",
    "IdentityCollisionFinding",
    "IdentityConsolidationProposal",
    "IdentityConsolidationReceipt",
    "IdentityBreakLineage",
    "IdentitySplitAllocation",
    "IdentitySplitPlan",
    "create_identity_break",
    "build_split_plan",
    "record_consolidation",
]


@dataclass(frozen=True)
class DNAIdentityLineageEdge(CanonicalRecord):
    edge_id: str
    source_ref: DNARevisionRef
    target_ref: DNARevisionRef
    relation: LineageRelation
    inherited_paths: tuple[str, ...] = ()
    retired_paths: tuple[str, ...] = ()
    authority_ref: SemanticRef | None = None
    policy_ref: SemanticRef | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "edge_id", require_identifier(self.edge_id, "edge_id"))
        if not isinstance(self.source_ref, DNARevisionRef) or not isinstance(self.target_ref, DNARevisionRef):
            raise DNAValidationError("lineage edges require pinned DNA revision refs")
        if not isinstance(self.relation, LineageRelation):
            object.__setattr__(self, "relation", LineageRelation(self.relation))
        if self.source_ref == self.target_ref:
            raise DNAIntegrityError("lineage edge cannot point to itself")
        for name in ("inherited_paths", "retired_paths"):
            object.__setattr__(self, name, tuple(sorted({require_semantic_path(p) for p in getattr(self, name)})))
        if set(self.inherited_paths) & set(self.retired_paths):
            raise DNAValidationError("lineage paths cannot be both inherited and retired")
        for name in ("authority_ref", "policy_ref"):
            ref = getattr(self, name)
            if ref is not None and not isinstance(ref, SemanticRef):
                raise DNAValidationError(f"{name} must be a SemanticRef")
        if self.relation in {
            LineageRelation.SAME_IDENTITY_REVISION,
            LineageRelation.IDENTITY_BREAK_DERIVATION,
            LineageRelation.SPLIT_CHILD,
            LineageRelation.CONSOLIDATION_CONTINUATION,
        } and (self.authority_ref is None or self.policy_ref is None):
            raise DNAAuthorityError("canonical lineage transitions require explicit authority and policy refs")
        if self.relation in {LineageRelation.IDENTITY_BREAK_DERIVATION, LineageRelation.SPLIT_CHILD}:
            if self.source_ref.dna_id == self.target_ref.dna_id:
                raise DNAAdmissionError("identity break/split lineage must use a new dna_id")


@dataclass(frozen=True)
class IdentityAlias(CanonicalRecord):
    alias_id: str
    dna_id: str
    alias_ref: SemanticRef
    authority_ref: SemanticRef
    policy_ref: SemanticRef
    source_revision_ref: DNARevisionRef

    def __post_init__(self) -> None:
        for name in ("alias_id", "dna_id"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        for name in ("alias_ref", "authority_ref", "policy_ref"):
            if not isinstance(getattr(self, name), SemanticRef):
                raise DNAAuthorityError(f"{name} must be an explicit SemanticRef")
        if not isinstance(self.source_revision_ref, DNARevisionRef) or self.source_revision_ref.dna_id != self.dna_id:
            raise DNAIntegrityError("alias must be pinned to its target DNA revision")


@dataclass(frozen=True)
class IdentityEquivalenceClaim(CanonicalRecord):
    claim_id: str
    left_ref: DNARevisionRef
    right_ref: DNARevisionRef
    evidence_refs: tuple[SemanticRef, ...]
    requested_relation: str = "EQUIVALENT"

    def __post_init__(self) -> None:
        object.__setattr__(self, "claim_id", require_identifier(self.claim_id, "claim_id"))
        if not isinstance(self.left_ref, DNARevisionRef) or not isinstance(self.right_ref, DNARevisionRef):
            raise DNAValidationError("equivalence claims require pinned revisions")
        if self.left_ref.dna_id == self.right_ref.dna_id:
            raise DNAValidationError("equivalence claims compare distinct dna_id values")
        object.__setattr__(self, "evidence_refs", require_refs(self.evidence_refs, "evidence_refs"))
        if not self.evidence_refs:
            raise DNAAdmissionError("equivalence is a governed claim and requires evidence refs")
        object.__setattr__(self, "requested_relation", require_text(self.requested_relation, "requested_relation", maximum=64).upper())


@dataclass(frozen=True)
class DNAConflict(CanonicalRecord):
    conflict_id: str
    path: str
    claims: tuple[SemanticRef, ...]
    reason: str
    fatal_identity_conflict: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "conflict_id", require_identifier(self.conflict_id, "conflict_id"))
        object.__setattr__(self, "path", require_semantic_path(self.path))
        object.__setattr__(self, "claims", require_refs(self.claims, "claims"))
        if len(self.claims) < 2:
            raise DNAValidationError("DNAConflict requires at least two conflicting claim refs")
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=2048))
        if not isinstance(self.fatal_identity_conflict, bool):
            raise DNAValidationError("fatal_identity_conflict must be a bool")


@dataclass(frozen=True)
class IdentityCollisionFinding(CanonicalRecord):
    finding_id: str
    revision_refs: tuple[DNARevisionRef, ...]
    conflict_refs: tuple[SemanticRef, ...]
    cause: str
    requires_governed_resolution: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "finding_id", require_identifier(self.finding_id, "finding_id"))
        refs = tuple(self.revision_refs)
        if len(refs) < 2 or any(not isinstance(item, DNARevisionRef) for item in refs):
            raise DNAValidationError("collision finding requires at least two pinned DNA revisions")
        if len({item.dna_id for item in refs}) < 2:
            raise DNAValidationError("collision finding requires distinct dna_id values")
        object.__setattr__(self, "revision_refs", tuple(sorted(refs)))
        object.__setattr__(self, "conflict_refs", require_refs(self.conflict_refs, "conflict_refs"))
        object.__setattr__(self, "cause", require_identifier(self.cause, "cause"))
        if not isinstance(self.requires_governed_resolution, bool) or not self.requires_governed_resolution:
            raise DNAAdmissionError("identity collisions never auto-resolve")


@dataclass(frozen=True)
class IdentityConsolidationProposal(CanonicalRecord):
    proposal_id: str
    source_refs: tuple[DNARevisionRef, ...]
    evidence_refs: tuple[SemanticRef, ...]
    rationale: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposal_id", require_identifier(self.proposal_id, "proposal_id"))
        refs = tuple(self.source_refs)
        if len(refs) < 2 or any(not isinstance(item, DNARevisionRef) for item in refs):
            raise DNAValidationError("consolidation proposals require at least two source histories")
        if len({item.dna_id for item in refs}) < 2:
            raise DNAValidationError("consolidation proposals must preserve distinct source dna_id values")
        object.__setattr__(self, "source_refs", tuple(sorted(refs)))
        object.__setattr__(self, "evidence_refs", require_refs(self.evidence_refs, "evidence_refs"))
        if not self.evidence_refs:
            raise DNAAdmissionError("identity consolidation proposals require explicit evidence refs")
        object.__setattr__(self, "rationale", require_text(self.rationale, "rationale", maximum=2048))


@dataclass(frozen=True)
class IdentityConsolidationReceipt(CanonicalRecord):
    proposal_id: str
    source_refs: tuple[DNARevisionRef, ...]
    continuation_ref: DNARevisionRef
    authority_ref: SemanticRef
    policy_ref: SemanticRef
    evidence_refs: tuple[SemanticRef, ...]
    digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposal_id", require_identifier(self.proposal_id, "proposal_id"))
        refs = tuple(self.source_refs)
        if len(refs) < 2 or any(not isinstance(item, DNARevisionRef) for item in refs):
            raise DNAValidationError("consolidation receipt must preserve all pinned source refs")
        if not isinstance(self.continuation_ref, DNARevisionRef) or self.continuation_ref not in refs:
            raise DNAIntegrityError("consolidation receipt continuation must be one retained source history")
        object.__setattr__(self, "source_refs", tuple(sorted(refs)))
        if not isinstance(self.authority_ref, SemanticRef) or not isinstance(self.policy_ref, SemanticRef):
            raise DNAAuthorityError("consolidation receipt requires authority and policy refs")
        from .versions import require_digest
        object.__setattr__(self, "digest", require_digest(self.digest, "digest"))
        object.__setattr__(self, "evidence_refs", require_refs(self.evidence_refs, "evidence_refs"))
        if not self.evidence_refs:
            raise DNAAdmissionError("consolidation receipt requires minimized evidence refs")
        body = {
            "proposal_id": self.proposal_id,
            "source_refs": self.source_refs,
            "continuation_ref": self.continuation_ref,
            "authority_ref": self.authority_ref,
            "policy_ref": self.policy_ref,
            "evidence_refs": self.evidence_refs,
        }
        if content_digest(body) != self.digest:
            raise DNAIntegrityError("consolidation receipt digest does not match its retained refs")


def record_consolidation(
    proposal: IdentityConsolidationProposal,
    continuation_ref: DNARevisionRef,
    *,
    authority_ref: SemanticRef,
    policy_ref: SemanticRef,
) -> IdentityConsolidationReceipt:
    if not isinstance(proposal, IdentityConsolidationProposal) or not isinstance(continuation_ref, DNARevisionRef):
        raise DNAValidationError("consolidation requires a proposal and pinned continuation ref")
    if continuation_ref not in proposal.source_refs:
        raise DNAAdmissionError("continuation must be one declared source; source histories are never erased")
    if not isinstance(authority_ref, SemanticRef) or not isinstance(policy_ref, SemanticRef):
        raise DNAAuthorityError("consolidation admission requires authority and policy refs")
    if authority_ref.owner_module != "m05":
        raise DNAAuthorityError("identity consolidation remains under M05 authority")
    digest = content_digest({
        "proposal_id": proposal.proposal_id,
        "source_refs": proposal.source_refs,
        "continuation_ref": continuation_ref,
        "authority_ref": authority_ref,
        "policy_ref": policy_ref,
        "evidence_refs": proposal.evidence_refs,
    })
    return IdentityConsolidationReceipt(
        proposal.proposal_id,
        proposal.source_refs,
        continuation_ref,
        authority_ref,
        policy_ref,
        proposal.evidence_refs,
        digest,
    )


@dataclass(frozen=True)
class IdentityBreakLineage(CanonicalRecord):
    source_revision_ref: DNARevisionRef
    new_identity_ref: DNARevisionRef
    reason: str
    inherited_paths: tuple[str, ...]
    retired_paths: tuple[str, ...]
    authority_ref: SemanticRef
    policy_ref: SemanticRef

    def __post_init__(self) -> None:
        if not isinstance(self.source_revision_ref, DNARevisionRef) or not isinstance(self.new_identity_ref, DNARevisionRef):
            raise DNAValidationError("identity break lineage requires pinned source and new revisions")
        if self.source_revision_ref.dna_id == self.new_identity_ref.dna_id:
            raise DNAIntegrityError("identity break must create a new dna_id")
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=2048))
        object.__setattr__(self, "inherited_paths", tuple(sorted({require_semantic_path(p) for p in self.inherited_paths})))
        object.__setattr__(self, "retired_paths", tuple(sorted({require_semantic_path(p) for p in self.retired_paths})))
        if set(self.inherited_paths) & set(self.retired_paths):
            raise DNAValidationError("identity-break paths cannot be inherited and retired together")
        if not isinstance(self.authority_ref, SemanticRef) or not isinstance(self.policy_ref, SemanticRef):
            raise DNAAuthorityError("identity break requires explicit authority and policy refs")


def create_identity_break(
    source: DNARevision,
    *,
    new_dna_id: str,
    new_revision_id: str,
    revision_number: int,
    inherited_paths: tuple[str, ...],
    retired_paths: tuple[str, ...],
    reason: str,
    authority_ref: SemanticRef,
    policy_ref: SemanticRef,
) -> tuple[AssetDNAIdentity, DNARevision, IdentityBreakLineage]:
    if not isinstance(source, DNARevision):
        raise DNAValidationError("source must be a DNARevision")
    new_dna_id = require_identifier(new_dna_id, "new_dna_id")
    if new_dna_id == source.dna_id:
        raise DNAIntegrityError("identity break requires a new stable dna_id")
    if revision_number != 1:
        raise DNAIntegrityError("identity break must start the new identity at revision 1")
    if authority_ref.owner_module != "m05":
        raise DNAAuthorityError("identity break remains under M05 authority")
    inherited = tuple(sorted({require_semantic_path(p) for p in inherited_paths}))
    retired = tuple(sorted({require_semantic_path(p) for p in retired_paths}))
    if set(inherited) & set(retired) or set(inherited) | set(retired) != set(source.trait_map()):
        raise DNAAdmissionError("identity break must allocate or retire every source trait explicitly")
    source_traits = source.trait_map()
    child_traits = tuple(source_traits[path] for path in inherited)
    identity = AssetDNAIdentity(
        new_dna_id,
        source.family.value.lower(),
        family=source.family,
        namespace="iris.asset",
        policy_refs=(policy_ref,),
        provenance_refs=source.provenance_refs,
        rights_privacy_refs=source.rights_privacy_refs,
    )
    child = DNARevision(
        new_dna_id,
        new_revision_id,
        revision_number,
        source.family,
        source.identity_level,
        child_traits,
        schema_version=source.schema_version,
        profile_ref=source.profile_ref,
        anchor_refs=source.anchor_refs,
        component_refs=source.component_refs,
        domain_link_refs=source.domain_link_refs,
        provenance_refs=source.provenance_refs,
        policy_refs=tuple(set(source.policy_refs + (policy_ref,))),
        rights_privacy_refs=source.rights_privacy_refs,
    )
    lineage = IdentityBreakLineage(
        source.ref, child.ref, reason, inherited, retired, authority_ref, policy_ref
    )
    return identity, child, lineage


@dataclass(frozen=True)
class IdentitySplitAllocation(CanonicalRecord):
    child_identity_ref: DNARevisionRef
    trait_paths: tuple[str, ...]
    component_refs: tuple[SemanticRef, ...]
    domain_link_refs: tuple[SemanticRef, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.child_identity_ref, DNARevisionRef):
            raise DNAValidationError("child_identity_ref must be a DNARevisionRef")
        object.__setattr__(self, "trait_paths", tuple(sorted({require_semantic_path(p) for p in self.trait_paths})))
        object.__setattr__(self, "component_refs", require_refs(self.component_refs, "component_refs"))
        object.__setattr__(self, "domain_link_refs", require_refs(self.domain_link_refs, "domain_link_refs"))


@dataclass(frozen=True)
class IdentitySplitPlan(CanonicalRecord):
    split_id: str
    source_revision_ref: DNARevisionRef
    allocations: tuple[IdentitySplitAllocation, ...]
    retained_source_paths: tuple[str, ...]
    retired_source_paths: tuple[str, ...]
    authority_ref: SemanticRef
    policy_ref: SemanticRef

    def __post_init__(self) -> None:
        object.__setattr__(self, "split_id", require_identifier(self.split_id, "split_id"))
        if not isinstance(self.source_revision_ref, DNARevisionRef):
            raise DNAValidationError("source_revision_ref must be pinned")
        allocations = tuple(self.allocations)
        if not allocations or any(not isinstance(item, IdentitySplitAllocation) for item in allocations):
            raise DNAValidationError("split plan requires typed child allocations")
        child_ids = [item.child_identity_ref.dna_id for item in allocations]
        if self.source_revision_ref.dna_id in child_ids or len(child_ids) != len(set(child_ids)):
            raise DNAIntegrityError("split plan requires distinct new child identities")
        object.__setattr__(self, "allocations", tuple(sorted(allocations, key=lambda item: item.child_identity_ref.dna_id)))
        for name in ("retained_source_paths", "retired_source_paths"):
            object.__setattr__(self, name, tuple(sorted({require_semantic_path(item) for item in getattr(self, name)})))
        inherited = [path for item in self.allocations for path in item.trait_paths]
        all_groups = [set(inherited), set(self.retained_source_paths), set(self.retired_source_paths)]
        if any(all_groups[left] & all_groups[right] for left in range(3) for right in range(left + 1, 3)):
            raise DNAIntegrityError("split plan cannot allocate a source path more than once")
        if not isinstance(self.authority_ref, SemanticRef) or not isinstance(self.policy_ref, SemanticRef):
            raise DNAAuthorityError("split plan requires authority and policy refs")
        if self.authority_ref.owner_module != "m05":
            raise DNAAuthorityError("identity split remains under M05 authority")


def build_split_plan(
    source: DNARevision,
    *,
    split_id: str,
    allocations: tuple[IdentitySplitAllocation, ...],
    retained_source_paths: tuple[str, ...],
    retired_source_paths: tuple[str, ...],
    authority_ref: SemanticRef,
    policy_ref: SemanticRef,
) -> IdentitySplitPlan:
    if not isinstance(source, DNARevision):
        raise DNAValidationError("source must be a DNARevision")
    items = tuple(allocations)
    if not items or any(not isinstance(item, IdentitySplitAllocation) for item in items):
        raise DNAValidationError("identity split requires explicit child allocations")
    if any(item.child_identity_ref.dna_id == source.dna_id for item in items):
        raise DNAIntegrityError("every split child must have a new dna_id")
    inherited = [path for item in items for path in item.trait_paths]
    retained = tuple(sorted({require_semantic_path(p) for p in retained_source_paths}))
    retired = tuple(sorted({require_semantic_path(p) for p in retired_source_paths}))
    all_paths = set(inherited) | set(retained) | set(retired)
    if (
        len(inherited) != len(set(inherited))
        or set(inherited) & set(retained)
        or set(inherited) & set(retired)
        or all_paths != set(source.trait_map())
    ):
        raise DNAAdmissionError("split plan must allocate, retain, or retire every trait exactly once")
    if set(retained) & set(retired):
        raise DNAAdmissionError("split paths cannot be both retained and retired")
    component_refs = [ref for item in items for ref in item.component_refs]
    link_refs = [ref for item in items for ref in item.domain_link_refs]
    if len(component_refs) != len(set(component_refs)) or len(link_refs) != len(set(link_refs)):
        raise DNAAdmissionError("split component and domain-link allocations cannot silently duplicate")
    if not isinstance(authority_ref, SemanticRef) or not isinstance(policy_ref, SemanticRef):
        raise DNAAuthorityError("identity split requires authority and policy refs")
    return IdentitySplitPlan(
        require_identifier(split_id, "split_id"),
        source.ref,
        tuple(sorted(items, key=lambda item: item.child_identity_ref.dna_id)),
        retained,
        retired,
        authority_ref,
        policy_ref,
    )
