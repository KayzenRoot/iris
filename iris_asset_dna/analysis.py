"""Deterministic fingerprint witnesses and path-level DNA change surfaces."""

from __future__ import annotations

from dataclasses import dataclass

from .base import CanonicalRecord, SemanticRef, require_refs
from .errors import DNAIntegrityError, DNAValidationError
from .identity import DNAFingerprint, DNARevision, DNARevisionRef
from .versions import content_digest, require_digest, require_identifier, require_text

__all__ = [
    "DNAChangeSurface",
    "DNAFingerprintWitness",
    "DNARevisionComparison",
    "EquivalenceAxisResult",
    "IdentityEquivalenceWitness",
    "IdentityEquivalenceDecision",
    "compare_revisions",
    "build_fingerprint_witness",
    "verify_fingerprint_witness",
    "build_equivalence_witness",
    "decide_equivalence",
]


@dataclass(frozen=True)
class DNAChangeSurface(CanonicalRecord):
    added_trait_paths: tuple[str, ...]
    removed_trait_paths: tuple[str, ...]
    changed_trait_paths: tuple[str, ...]
    added_anchor_refs: tuple[SemanticRef, ...]
    removed_anchor_refs: tuple[SemanticRef, ...]
    added_component_refs: tuple[SemanticRef, ...]
    removed_component_refs: tuple[SemanticRef, ...]
    added_domain_link_refs: tuple[SemanticRef, ...]
    removed_domain_link_refs: tuple[SemanticRef, ...]
    family_changed: bool
    identity_level_changed: bool
    profile_changed: bool
    identity_id_changed: bool
    semantic_changed: bool
    surface_digest: str

    def __post_init__(self) -> None:
        for name in ("added_trait_paths", "removed_trait_paths", "changed_trait_paths"):
            values = tuple(sorted({require_identifier(item, f"{name}[]") for item in getattr(self, name)}))
            object.__setattr__(self, name, values)
        for name in (
            "added_anchor_refs", "removed_anchor_refs", "added_component_refs", "removed_component_refs",
            "added_domain_link_refs", "removed_domain_link_refs",
        ):
            object.__setattr__(self, name, require_refs(getattr(self, name), name))
        for name in ("family_changed", "identity_level_changed", "profile_changed", "identity_id_changed", "semantic_changed"):
            if not isinstance(getattr(self, name), bool):
                raise DNAValidationError(f"{name} must be a bool")
        object.__setattr__(self, "surface_digest", require_digest(self.surface_digest, "surface_digest"))
        body = {name: getattr(self, name) for name in (
            "added_trait_paths", "removed_trait_paths", "changed_trait_paths",
            "added_anchor_refs", "removed_anchor_refs", "added_component_refs", "removed_component_refs",
            "added_domain_link_refs", "removed_domain_link_refs", "family_changed", "identity_level_changed",
            "profile_changed", "identity_id_changed", "semantic_changed",
        )}
        if content_digest(body) != self.surface_digest:
            raise DNAIntegrityError("DNA change surface digest does not match its declared paths")


@dataclass(frozen=True)
class DNAFingerprintWitness(CanonicalRecord):
    revision_ref: DNARevisionRef
    fingerprint: DNAFingerprint
    canonical_payload_digest: str
    excluded_nonsemantic_fields: tuple[str, ...]
    witness_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.revision_ref, DNARevisionRef) or not isinstance(self.fingerprint, DNAFingerprint):
            raise DNAValidationError("fingerprint witness requires a pinned revision and typed fingerprint")
        for name in ("canonical_payload_digest", "witness_digest"):
            object.__setattr__(self, name, require_digest(getattr(self, name), name))
        excluded = tuple(sorted({require_identifier(item, "excluded_nonsemantic_fields[]") for item in self.excluded_nonsemantic_fields}))
        object.__setattr__(self, "excluded_nonsemantic_fields", excluded)
        body = {
            "revision_ref": self.revision_ref,
            "fingerprint": self.fingerprint,
            "canonical_payload_digest": self.canonical_payload_digest,
            "excluded_nonsemantic_fields": self.excluded_nonsemantic_fields,
        }
        if content_digest(body) != self.witness_digest:
            raise DNAIntegrityError("DNA fingerprint witness digest does not match its contents")
        if self.canonical_payload_digest != self.fingerprint.digest:
            raise DNAIntegrityError("fingerprint witness payload digest does not match the semantic fingerprint")


@dataclass(frozen=True)
class DNARevisionComparison(CanonicalRecord):
    source_ref: DNARevisionRef
    target_ref: DNARevisionRef
    change_surface: DNAChangeSurface
    source_fingerprint: str
    target_fingerprint: str
    requires_governed_decision: bool
    comparison_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_ref, DNARevisionRef) or not isinstance(self.target_ref, DNARevisionRef):
            raise DNAValidationError("revision comparison requires pinned source and target refs")
        if not isinstance(self.change_surface, DNAChangeSurface):
            raise DNAValidationError("change_surface must be typed")
        object.__setattr__(self, "source_fingerprint", require_digest(self.source_fingerprint, "source_fingerprint"))
        object.__setattr__(self, "target_fingerprint", require_digest(self.target_fingerprint, "target_fingerprint"))
        if not isinstance(self.requires_governed_decision, bool):
            raise DNAValidationError("requires_governed_decision must be a bool")
        object.__setattr__(self, "comparison_digest", require_digest(self.comparison_digest, "comparison_digest"))
        semantic_changed = self.source_fingerprint != self.target_fingerprint
        identity_id_changed = self.source_ref.dna_id != self.target_ref.dna_id
        if self.change_surface.semantic_changed != semantic_changed:
            raise DNAIntegrityError("revision comparison semantic flag disagrees with its fingerprints")
        if self.change_surface.identity_id_changed != identity_id_changed:
            raise DNAIntegrityError("revision comparison identity flag disagrees with its pinned refs")
        if self.requires_governed_decision != (semantic_changed or identity_id_changed):
            raise DNAIntegrityError("revision comparison decision requirement disagrees with its change surface")
        body = {
            "source_ref": self.source_ref,
            "target_ref": self.target_ref,
            "change_surface": self.change_surface,
            "source_fingerprint": self.source_fingerprint,
            "target_fingerprint": self.target_fingerprint,
            "requires_governed_decision": self.requires_governed_decision,
        }
        if content_digest(body) != self.comparison_digest:
            raise DNAIntegrityError("DNA revision comparison digest does not match its contents")


@dataclass(frozen=True)
class EquivalenceAxisResult(CanonicalRecord):
    axis: str
    outcome: str
    evidence_refs: tuple[SemanticRef, ...]

    def __post_init__(self) -> None:
        axis = require_identifier(self.axis, "axis")
        if axis not in {"family", "identity_level", "schema", "traits", "components", "anchors", "domain_links"}:
            raise DNAValidationError(f"unsupported identity equivalence axis {axis!r}")
        outcome = require_text(self.outcome, "outcome", maximum=32).upper()
        if outcome not in {"MATCH", "DIFFERENT", "UNKNOWN"}:
            raise DNAValidationError("equivalence axis outcome must be MATCH, DIFFERENT, or UNKNOWN")
        object.__setattr__(self, "axis", axis)
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(self, "evidence_refs", require_refs(self.evidence_refs, "evidence_refs"))


@dataclass(frozen=True)
class IdentityEquivalenceWitness(CanonicalRecord):
    left_ref: DNARevisionRef
    right_ref: DNARevisionRef
    candidate_fingerprint_match: bool
    axes: tuple[EquivalenceAxisResult, ...]
    evidence_refs: tuple[SemanticRef, ...]
    witness_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.left_ref, DNARevisionRef) or not isinstance(self.right_ref, DNARevisionRef):
            raise DNAValidationError("equivalence witness requires two pinned DNA revision refs")
        if self.left_ref.dna_id == self.right_ref.dna_id:
            raise DNAValidationError("equivalence witness compares distinct persistent identities")
        if not isinstance(self.candidate_fingerprint_match, bool):
            raise DNAValidationError("candidate_fingerprint_match must be a bool")
        axes = tuple(self.axes)
        if any(not isinstance(item, EquivalenceAxisResult) for item in axes):
            raise DNAValidationError("equivalence witness axes must be typed")
        names = [item.axis for item in axes]
        if len(names) != len(set(names)):
            raise DNAIntegrityError("equivalence witness contains duplicate axes")
        object.__setattr__(self, "axes", tuple(sorted(axes, key=lambda item: item.axis)))
        object.__setattr__(self, "evidence_refs", require_refs(self.evidence_refs, "evidence_refs"))
        object.__setattr__(self, "witness_digest", require_digest(self.witness_digest, "witness_digest"))
        body = {
            "left_ref": self.left_ref,
            "right_ref": self.right_ref,
            "candidate_fingerprint_match": self.candidate_fingerprint_match,
            "axes": self.axes,
            "evidence_refs": self.evidence_refs,
        }
        if content_digest(body) != self.witness_digest:
            raise DNAIntegrityError("identity equivalence witness digest does not match its contents")


@dataclass(frozen=True)
class IdentityEquivalenceDecision(CanonicalRecord):
    witness_digest: str
    outcome: str
    authority_ref: SemanticRef
    policy_ref: SemanticRef
    evidence_refs: tuple[SemanticRef, ...]
    decision_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "witness_digest", require_digest(self.witness_digest, "witness_digest"))
        outcome = require_text(self.outcome, "outcome", maximum=32).upper()
        if outcome not in {"EQUIVALENT", "DISTINCT", "INDETERMINATE"}:
            raise DNAValidationError("equivalence decision outcome is unsupported")
        object.__setattr__(self, "outcome", outcome)
        if not isinstance(self.authority_ref, SemanticRef) or not isinstance(self.policy_ref, SemanticRef):
            raise DNAValidationError("equivalence decision requires explicit authority and policy refs")
        if self.authority_ref.owner_module != "m05":
            raise DNAValidationError("equivalence decisions remain under M05 identity governance")
        object.__setattr__(self, "evidence_refs", require_refs(self.evidence_refs, "evidence_refs"))
        if self.outcome == "EQUIVALENT" and not self.evidence_refs:
            raise DNAValidationError("equivalence decision requires explicit evidence refs")
        object.__setattr__(self, "decision_digest", require_digest(self.decision_digest, "decision_digest"))
        body = {
            "witness_digest": self.witness_digest,
            "outcome": self.outcome,
            "authority_ref": self.authority_ref,
            "policy_ref": self.policy_ref,
            "evidence_refs": self.evidence_refs,
        }
        if content_digest(body) != self.decision_digest:
            raise DNAIntegrityError("identity equivalence decision digest does not match its contents")


def compare_revisions(source: DNARevision, target: DNARevision) -> DNARevisionComparison:
    if not isinstance(source, DNARevision) or not isinstance(target, DNARevision):
        raise DNAValidationError("compare_revisions requires two DNARevision records")
    old_traits = source.trait_map()
    new_traits = target.trait_map()
    added = tuple(sorted(set(new_traits) - set(old_traits)))
    removed = tuple(sorted(set(old_traits) - set(new_traits)))
    changed = tuple(sorted(path for path in set(old_traits) & set(new_traits) if old_traits[path] != new_traits[path]))
    old_anchors, new_anchors = set(source.anchor_refs), set(target.anchor_refs)
    old_components, new_components = set(source.component_refs), set(target.component_refs)
    old_links, new_links = set(source.domain_link_refs), set(target.domain_link_refs)
    surface_body = {
        "added_trait_paths": added,
        "removed_trait_paths": removed,
        "changed_trait_paths": changed,
        "added_anchor_refs": tuple(sorted(new_anchors - old_anchors)),
        "removed_anchor_refs": tuple(sorted(old_anchors - new_anchors)),
        "added_component_refs": tuple(sorted(new_components - old_components)),
        "removed_component_refs": tuple(sorted(old_components - new_components)),
        "added_domain_link_refs": tuple(sorted(new_links - old_links)),
        "removed_domain_link_refs": tuple(sorted(old_links - new_links)),
        "family_changed": source.family is not target.family,
        "identity_level_changed": source.identity_level is not target.identity_level,
        "profile_changed": source.profile_ref != target.profile_ref,
        "identity_id_changed": source.dna_id != target.dna_id,
        "semantic_changed": source.semantic_digest != target.semantic_digest,
    }
    surface = DNAChangeSurface(**surface_body, surface_digest=content_digest(surface_body))
    comparison_body = {
        "source_ref": source.ref,
        "target_ref": target.ref,
        "change_surface": surface,
        "source_fingerprint": source.semantic_digest,
        "target_fingerprint": target.semantic_digest,
        "requires_governed_decision": surface.semantic_changed or surface.identity_id_changed,
    }
    comparison = DNARevisionComparison(**comparison_body, comparison_digest=content_digest(comparison_body))
    if comparison.requires_governed_decision and not comparison.change_surface.semantic_changed and not comparison.change_surface.identity_id_changed:
        raise DNAIntegrityError("decision requirement is inconsistent with the semantic change surface")
    return comparison


def build_fingerprint_witness(revision: DNARevision) -> DNAFingerprintWitness:
    if not isinstance(revision, DNARevision):
        raise DNAValidationError("revision must be a DNARevision")
    excluded = tuple(sorted(("display_metadata", "evidence_refs", "revision_id", "revision_number", "parent_revision_refs", "dna_id")))
    body = {
        "revision_ref": revision.ref,
        "fingerprint": revision.fingerprint,
        "canonical_payload_digest": content_digest(revision.canonical_payload()),
        "excluded_nonsemantic_fields": excluded,
    }
    return DNAFingerprintWitness(**body, witness_digest=content_digest(body))


def verify_fingerprint_witness(revision: DNARevision, witness: DNAFingerprintWitness) -> bool:
    if not isinstance(revision, DNARevision) or not isinstance(witness, DNAFingerprintWitness):
        raise DNAValidationError("verify_fingerprint_witness requires a revision and witness")
    body = {
        "revision_ref": witness.revision_ref,
        "fingerprint": witness.fingerprint,
        "canonical_payload_digest": witness.canonical_payload_digest,
        "excluded_nonsemantic_fields": witness.excluded_nonsemantic_fields,
    }
    return (
        revision.ref == witness.revision_ref
        and revision.fingerprint == witness.fingerprint
        and content_digest(revision.canonical_payload()) == witness.canonical_payload_digest
        and content_digest(body) == witness.witness_digest
    )


def build_equivalence_witness(
    left: DNARevision,
    right: DNARevision,
    axes: tuple[EquivalenceAxisResult, ...],
    evidence_refs: tuple[SemanticRef, ...],
) -> IdentityEquivalenceWitness:
    if not isinstance(left, DNARevision) or not isinstance(right, DNARevision):
        raise DNAValidationError("equivalence witness requires two DNARevision records")
    if left.dna_id == right.dna_id:
        raise DNAValidationError("equivalence witness compares distinct dna_id values")
    items = tuple(axes)
    body = {
        "left_ref": left.ref,
        "right_ref": right.ref,
        "candidate_fingerprint_match": left.semantic_digest == right.semantic_digest,
        "axes": tuple(sorted(items, key=lambda item: item.axis)),
        "evidence_refs": require_refs(evidence_refs, "evidence_refs"),
    }
    return IdentityEquivalenceWitness(**body, witness_digest=content_digest(body))


def decide_equivalence(
    witness: IdentityEquivalenceWitness,
    *,
    authority_ref: SemanticRef,
    policy_ref: SemanticRef,
    decision_evidence_refs: tuple[SemanticRef, ...],
) -> IdentityEquivalenceDecision:
    """Record an explicit equivalence decision; no outcome merges or rewrites IDs."""
    if not isinstance(witness, IdentityEquivalenceWitness):
        raise DNAValidationError("decide_equivalence requires an IdentityEquivalenceWitness")
    evidence = require_refs(decision_evidence_refs, "decision_evidence_refs")
    axes = {item.axis: item.outcome for item in witness.axes}
    required = {"family", "identity_level", "schema", "traits", "components", "anchors", "domain_links"}
    if any(axes.get(axis) == "DIFFERENT" for axis in required):
        outcome = "DISTINCT"
    elif required <= axes.keys() and all(axes[axis] == "MATCH" for axis in required) and evidence:
        outcome = "EQUIVALENT"
    else:
        outcome = "INDETERMINATE"
    body = {
        "witness_digest": witness.witness_digest,
        "outcome": outcome,
        "authority_ref": authority_ref,
        "policy_ref": policy_ref,
        "evidence_refs": evidence,
    }
    return IdentityEquivalenceDecision(**body, decision_digest=content_digest(body))
