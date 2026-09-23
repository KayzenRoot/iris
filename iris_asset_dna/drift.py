"""Typed multidimensional drift evidence without quality or mutation authority."""

from __future__ import annotations

from dataclasses import dataclass

from .base import CanonicalRecord, SemanticRef, require_refs
from .enums import (
    DriftDimension,
    DriftEvidenceResult,
    DriftState,
    LinkFreshness,
    TraitCriticality,
)
from .errors import DNAAdmissionError, DNAValidationError
from .identity import DNARevision, DNARevisionRef
from .versions import content_digest, require_identifier, require_semantic_path

__all__ = [
    "IdentityDriftEvidence",
    "IdentityContinuityEnvelope",
    "IdentityDriftReport",
    "DriftDimensionSummary",
    "build_drift_report",
    "validate_continuity_envelope",
]


@dataclass(frozen=True)
class IdentityDriftEvidence(CanonicalRecord):
    evidence_id: str
    source_revision_ref: DNARevisionRef
    path: str
    dimension: DriftDimension
    result: DriftEvidenceResult
    criticality: TraitCriticality
    evaluator_owner_ref: SemanticRef
    observation_ref: SemanticRef | None = None
    policy_ref: SemanticRef | None = None
    uncertainty_ref: SemanticRef | None = None
    restricted_evidence_ref: SemanticRef | None = None
    evidence_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", require_identifier(self.evidence_id, "evidence_id"))
        if not isinstance(self.source_revision_ref, DNARevisionRef):
            raise DNAValidationError("source_revision_ref must be a DNARevisionRef")
        object.__setattr__(self, "path", require_semantic_path(self.path))
        for name, enum_type in (
            ("dimension", DriftDimension),
            ("result", DriftEvidenceResult),
            ("criticality", TraitCriticality),
        ):
            value = getattr(self, name)
            if not isinstance(value, enum_type):
                object.__setattr__(self, name, enum_type(value))
        if not isinstance(self.evaluator_owner_ref, SemanticRef):
            raise DNAAdmissionError("drift evidence must retain its evaluator owner")
        for name in ("observation_ref", "policy_ref", "uncertainty_ref", "restricted_evidence_ref"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, SemanticRef):
                raise DNAValidationError(f"{name} must be a SemanticRef")
        object.__setattr__(self, "evidence_refs", require_refs(self.evidence_refs, "evidence_refs"))
        if self.result in {DriftEvidenceResult.MISSING, DriftEvidenceResult.UNKNOWN} and self.observation_ref is not None:
            raise DNAValidationError("missing/unknown drift evidence cannot claim an observed value")
        if self.restricted_evidence_ref is not None and self.restricted_evidence_ref in self.evidence_refs:
            raise DNAValidationError("restricted evidence remains a separate minimized reference")
        if self.restricted_evidence_ref is not None and (
            self.policy_ref is None or self.policy_ref.owner_module not in {"m53", "m54"}
        ):
            raise DNAAdmissionError("restricted drift evidence requires an M53/M54 policy reference")


@dataclass(frozen=True)
class IdentityContinuityEnvelope(CanonicalRecord):
    envelope_id: str
    source_revision_ref: DNARevisionRef
    identity_defining_paths: tuple[str, ...]
    bounded_mutable_paths: tuple[str, ...] = ()
    contextual_paths: tuple[str, ...] = ()
    required_anchor_refs: tuple[SemanticRef, ...] = ()
    required_domain_link_ids: tuple[str, ...] = ()
    allowed_substitution_refs: tuple[SemanticRef, ...] = ()
    forbidden_transition_refs: tuple[SemanticRef, ...] = ()
    evaluator_owner_refs: tuple[SemanticRef, ...] = ()
    policy_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "envelope_id", require_identifier(self.envelope_id, "envelope_id"))
        if not isinstance(self.source_revision_ref, DNARevisionRef):
            raise DNAValidationError("source_revision_ref must be a DNARevisionRef")
        for name in ("identity_defining_paths", "bounded_mutable_paths", "contextual_paths"):
            values = tuple(sorted({require_semantic_path(item, f"{name}[]") for item in getattr(self, name)}))
            object.__setattr__(self, name, values)
        groups = [set(self.identity_defining_paths), set(self.bounded_mutable_paths), set(self.contextual_paths)]
        if any(groups[i] & groups[j] for i in range(3) for j in range(i + 1, 3)):
            raise DNAValidationError("continuity path classes must be disjoint")
        object.__setattr__(self, "required_anchor_refs", require_refs(self.required_anchor_refs, "required_anchor_refs"))
        object.__setattr__(self, "required_domain_link_ids", require_refs_to_ids(self.required_domain_link_ids))
        for name in ("allowed_substitution_refs", "forbidden_transition_refs", "evaluator_owner_refs", "policy_refs"):
            object.__setattr__(self, name, require_refs(getattr(self, name), name))
        if not self.evaluator_owner_refs:
            raise DNAAdmissionError("continuity analysis must preserve evaluator ownership")


def require_refs_to_ids(values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise DNAValidationError("required_domain_link_ids must be a sequence")
    items = tuple(sorted({require_identifier(item, "required_domain_link_ids[]") for item in values}))
    return items


@dataclass(frozen=True)
class DriftDimensionSummary(CanonicalRecord):
    dimension: DriftDimension
    finding_count: int
    different_paths: tuple[str, ...]
    missing_paths: tuple[str, ...]
    unknown_paths: tuple[str, ...]


@dataclass(frozen=True)
class IdentityDriftReport(CanonicalRecord):
    report_id: str
    source_revision_ref: DNARevisionRef
    evidence: tuple[IdentityDriftEvidence, ...]
    state: DriftState
    summaries: tuple[DriftDimensionSummary, ...]
    required_anchor_refs: tuple[SemanticRef, ...]
    absent_anchor_refs: tuple[SemanticRef, ...]
    required_domain_link_ids: tuple[str, ...]
    stale_or_missing_domain_link_ids: tuple[str, ...]
    evaluator_owner_refs: tuple[SemanticRef, ...]
    fingerprint: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_id", require_identifier(self.report_id, "report_id"))
        if not isinstance(self.source_revision_ref, DNARevisionRef):
            raise DNAValidationError("source_revision_ref must be a DNARevisionRef")
        if not isinstance(self.state, DriftState):
            object.__setattr__(self, "state", DriftState(self.state))
        evidence = tuple(self.evidence)
        if any(not isinstance(item, IdentityDriftEvidence) for item in evidence):
            raise DNAValidationError("drift report evidence must be typed")
        object.__setattr__(self, "evidence", tuple(sorted(evidence, key=lambda item: (item.path, item.dimension.value, item.evidence_id))))
        object.__setattr__(self, "required_anchor_refs", require_refs(self.required_anchor_refs, "required_anchor_refs"))
        object.__setattr__(self, "absent_anchor_refs", require_refs(self.absent_anchor_refs, "absent_anchor_refs"))
        object.__setattr__(self, "required_domain_link_ids", require_refs_to_ids(self.required_domain_link_ids))
        object.__setattr__(self, "stale_or_missing_domain_link_ids", require_refs_to_ids(self.stale_or_missing_domain_link_ids))
        object.__setattr__(self, "evaluator_owner_refs", require_refs(self.evaluator_owner_refs, "evaluator_owner_refs"))
        from .versions import require_digest
        object.__setattr__(self, "fingerprint", require_digest(self.fingerprint, "fingerprint"))
        body = {
            "report_id": self.report_id,
            "source_revision_ref": self.source_revision_ref,
            "evidence": self.evidence,
            "state": self.state.value,
            "summaries": self.summaries,
            "absent_anchor_refs": self.absent_anchor_refs,
            "stale_or_missing_domain_link_ids": self.stale_or_missing_domain_link_ids,
            "evaluator_owner_refs": self.evaluator_owner_refs,
        }
        if content_digest(body) != self.fingerprint:
            raise DNAValidationError("identity drift report fingerprint does not match its contents")

    @property
    def admits_mutation(self) -> bool:
        return False


def build_drift_report(
    report_id: str,
    continuity: IdentityContinuityEnvelope,
    evidence: tuple[IdentityDriftEvidence, ...],
    *,
    present_anchor_refs: tuple[SemanticRef, ...] = (),
    link_freshness: tuple[tuple[str, LinkFreshness], ...] = (),
) -> IdentityDriftReport:
    if not isinstance(continuity, IdentityContinuityEnvelope):
        raise DNAValidationError("continuity must be an IdentityContinuityEnvelope")
    evidence = tuple(evidence)
    if any(not isinstance(item, IdentityDriftEvidence) for item in evidence):
        raise DNAValidationError("evidence must contain IdentityDriftEvidence values")
    if any(item.source_revision_ref != continuity.source_revision_ref for item in evidence):
        raise DNAAdmissionError("drift evidence must pin the continuity envelope source revision")
    if len({item.evidence_id for item in evidence}) != len(evidence):
        raise DNAValidationError("drift report contains duplicate evidence IDs")
    evidence = tuple(sorted(evidence, key=lambda item: (item.path, item.dimension.value, item.evidence_id)))
    required_paths = set(continuity.identity_defining_paths)
    measured_paths = {item.path for item in evidence}
    implicit_missing = required_paths - measured_paths
    rows: list[DriftDimensionSummary] = []
    for dimension in DriftDimension:
        items = [item for item in evidence if item.dimension is dimension]
        different = tuple(sorted(item.path for item in items if item.result is DriftEvidenceResult.DIFFERENT))
        missing = tuple(sorted(
            {item.path for item in items if item.result is DriftEvidenceResult.MISSING}
            | (implicit_missing if dimension is DriftDimension.MISSING_REQUIRED else set())
        ))
        unknown = tuple(sorted(item.path for item in items if item.result is DriftEvidenceResult.UNKNOWN))
        if items or missing:
            rows.append(DriftDimensionSummary(dimension, len(items), different, missing, unknown))
    identity_break = any(
        item.result is DriftEvidenceResult.DIFFERENT
        and (item.criticality is TraitCriticality.IDENTITY_DEFINING or item.path in required_paths)
        for item in evidence
    )
    collision = any(
        item.dimension is DriftDimension.COLLISION_SPLIT
        and item.result is DriftEvidenceResult.DIFFERENT
        for item in evidence
    )
    has_unknown = bool(implicit_missing) or any(
        item.result in {DriftEvidenceResult.UNKNOWN, DriftEvidenceResult.MISSING}
        for item in evidence
    )
    has_difference = any(item.result is DriftEvidenceResult.DIFFERENT for item in evidence)
    has_allowed = any(item.result is DriftEvidenceResult.ALLOWED_VARIATION for item in evidence)
    if collision:
        state = DriftState.COLLISION_OR_SPLIT_CANDIDATE
    elif identity_break:
        state = DriftState.IDENTITY_BREAK_CANDIDATE
    elif has_unknown:
        state = DriftState.INDETERMINATE
    elif has_difference:
        state = DriftState.IDENTITY_RELEVANT_DRIFT
    elif has_allowed:
        state = DriftState.WITHIN_DECLARED_VARIATION
    else:
        state = DriftState.NO_DRIFT
    present = set(present_anchor_refs)
    absent_anchors = tuple(item for item in continuity.required_anchor_refs if item not in present)
    fresh_by_id: dict[str, LinkFreshness] = {}
    for identifier, freshness in link_freshness:
        identifier = require_identifier(identifier, "link_freshness.link_id")
        if not isinstance(freshness, LinkFreshness):
            freshness = LinkFreshness(freshness)
        if identifier in fresh_by_id:
            raise DNAValidationError("link freshness evidence contains duplicate domain-link IDs")
        fresh_by_id[identifier] = freshness
    stale_links = tuple(sorted(
        item for item in continuity.required_domain_link_ids
        if fresh_by_id.get(item) is not LinkFreshness.CURRENT
    ))
    if (absent_anchors or stale_links) and state in {DriftState.NO_DRIFT, DriftState.WITHIN_DECLARED_VARIATION}:
        state = DriftState.INDETERMINATE
    owners = require_refs(
        tuple(set(continuity.evaluator_owner_refs + tuple(item.evaluator_owner_ref for item in evidence))),
        "evaluator_owner_refs",
    )
    summaries = tuple(sorted(rows, key=lambda item: item.dimension.value))
    body = {
        "report_id": require_identifier(report_id, "report_id"),
        "source_revision_ref": continuity.source_revision_ref,
        "evidence": evidence,
        "state": state.value,
        "summaries": summaries,
        "absent_anchor_refs": absent_anchors,
        "stale_or_missing_domain_link_ids": stale_links,
        "evaluator_owner_refs": owners,
    }
    return IdentityDriftReport(
        body["report_id"], continuity.source_revision_ref, evidence, state, summaries,
        continuity.required_anchor_refs, absent_anchors, continuity.required_domain_link_ids,
        stale_links, owners, content_digest(body),
    )


def validate_continuity_envelope(envelope: IdentityContinuityEnvelope, revision: DNARevision) -> None:
    if not isinstance(envelope, IdentityContinuityEnvelope) or not isinstance(revision, DNARevision):
        raise DNAValidationError("continuity validation requires an envelope and DNARevision")
    if envelope.source_revision_ref != revision.ref:
        raise DNAAdmissionError("continuity envelope must pin the exact immutable source revision")
    traits = revision.trait_map()
    declared = set(envelope.identity_defining_paths) | set(envelope.bounded_mutable_paths) | set(envelope.contextual_paths)
    missing = declared - set(traits)
    if missing:
        raise DNAAdmissionError(f"continuity envelope declares paths absent from its revision: {sorted(missing)}")
    for path in envelope.identity_defining_paths:
        if traits[path].criticality is not TraitCriticality.IDENTITY_DEFINING:
            raise DNAAdmissionError(f"continuity path {path} is not identity-defining in the pinned revision")
    for path in envelope.bounded_mutable_paths:
        if traits[path].mutability.value != "MUTABLE_WITHIN_BOUNDS":
            raise DNAAdmissionError(f"bounded continuity path {path} lacks bounded-mutation semantics")
    for path in envelope.contextual_paths:
        if traits[path].criticality is not TraitCriticality.CONTEXTUAL and traits[path].mutability.value != "CONTEXTUAL_VARIANT":
            raise DNAAdmissionError(f"contextual continuity path {path} is not declared contextual in the pinned revision")
