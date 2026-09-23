"""Evidence-gated reuse, selective regeneration and mixed ancestry receipts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from iris_project_os.graph import DependencySlice as M02DependencySlice
from iris_project_os.reuse import ReuseReceipt as M02ReuseReceipt

from .base import CanonicalRecord, exact_ref_key, require_exact_ref, require_m02_build_plan, require_sequence
from .dependencies import ImpactConeReceipt, OperationalDependencyFingerprint, validate_impact_cone
from .enums import EquivalenceState, ImpactState, WorkDisposition
from .errors import ProductionStateAdmissionError, ProductionStateIntegrityError, ProductionStateValidationError
from .limits import DEFAULT_LIMITS
from .revisions import MaterializationRef, OperationalRevisionRef
from .versions import CORE_SCHEMA_VERSION, require_identifier, require_text, require_version

__all__ = [
    "ReuseEvidenceState",
    "ReuseEvidenceDimension",
    "ReuseProof",
    "ReuseAdmissionReceipt",
    "RebuildBoundary",
    "WorkFrontier",
    "VerificationReceipt",
    "MixedReconstructionReceipt",
    "admit_reuse",
    "decide_work",
    "expand_frontier",
    "admit_mixed_reconstruction",
]


class ReuseEvidenceState(str):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ReuseEvidenceDimension(CanonicalRecord):
    name: str
    state: str
    evidence_ref: Any
    material: bool = True

    def __post_init__(self) -> None:
        require_text(self.name, "name", maximum=2048)
        if self.state not in {ReuseEvidenceState.VERIFIED, ReuseEvidenceState.FAILED, ReuseEvidenceState.STALE, ReuseEvidenceState.UNKNOWN}:
            raise ProductionStateValidationError("unknown reuse evidence state")
        require_exact_ref(self.evidence_ref, "evidence_ref")
        if type(self.material) is not bool:
            raise ProductionStateValidationError("material must be a boolean")


@dataclass(frozen=True)
class ReuseProof(CanonicalRecord):
    candidate_revision_ref: OperationalRevisionRef
    candidate_materialization_ref: MaterializationRef
    dependency_fingerprint: OperationalDependencyFingerprint
    m02_build_ref: Any
    m02_node_id: str
    dimensions: tuple[ReuseEvidenceDimension, ...]
    cache_hit_only: bool = False
    digest_only: bool = False
    proof_version: str = CORE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if type(self.candidate_revision_ref) is not OperationalRevisionRef or type(self.candidate_materialization_ref) is not MaterializationRef:
            raise ProductionStateValidationError("reuse proof requires exact candidate revision and materialization refs")
        if self.candidate_materialization_ref.revision_ref != self.candidate_revision_ref:
            raise ProductionStateIntegrityError("candidate materialization and revision refs do not match")
        if type(self.dependency_fingerprint) is not OperationalDependencyFingerprint:
            raise ProductionStateValidationError("reuse proof requires an exact causal fingerprint")
        require_m02_build_plan(self.m02_build_ref, "m02_build_ref")
        require_identifier(self.m02_node_id, "m02_node_id")
        step = _m02_build_step(self.m02_build_ref, self.m02_node_id)
        if step.disposition.value != "REUSE" or type(step.receipt) is not M02ReuseReceipt or not step.receipt.satisfies_output:
            raise ProductionStateAdmissionError("reuse proof must bind the exact M02 BuildPlan REUSE step and its admitted M02 ReuseReceipt")
        if self.candidate_materialization_ref.content_digest.algorithm != "sha256" or self.candidate_materialization_ref.content_digest.value != step.receipt.result_digest:
            raise ProductionStateIntegrityError("M06 materialization digest must match the exact output digest admitted by M02")
        dims = require_sequence(self.dimensions, "dimensions", maximum=DEFAULT_LIMITS.max_fingerprint_dimensions, item_type=ReuseEvidenceDimension)
        if len({item.name for item in dims}) != len(dims):
            raise ProductionStateValidationError("reuse evidence dimension names must be unique")
        required_dimensions = {item.key for item in self.dependency_fingerprint.dimensions if item.mandatory and item.materiality.value == "MATERIAL"}
        if not required_dimensions.issubset({item.name for item in dims if item.material}):
            raise ProductionStateAdmissionError("reuse proof must positively cover every mandatory material fingerprint dimension")
        object.__setattr__(self, "dimensions", dims)
        for name in ("cache_hit_only", "digest_only"):
            if type(getattr(self, name)) is not bool:
                raise ProductionStateValidationError(f"{name} must be a boolean")
        require_version(self.proof_version, "proof_version")


@dataclass(frozen=True)
class ReuseAdmissionReceipt(CanonicalRecord):
    receipt_id: str
    decision_id: str
    candidate_revision_ref: OperationalRevisionRef
    candidate_materialization_ref: MaterializationRef
    dependency_fingerprint: OperationalDependencyFingerprint
    m02_build_ref: Any
    m02_node_id: str
    m02_reuse_receipt: Any
    evidence_dimensions: tuple[ReuseEvidenceDimension, ...]
    evidence_refs: tuple[Any, ...]
    equivalence: EquivalenceState
    admitted_at_ms: int
    receipt_version: str = CORE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_identifier(self.receipt_id, "receipt_id")
        require_identifier(self.decision_id, "decision_id")
        if type(self.candidate_revision_ref) is not OperationalRevisionRef or type(self.candidate_materialization_ref) is not MaterializationRef:
            raise ProductionStateValidationError("reuse receipt requires exact immutable M06 refs")
        if self.candidate_materialization_ref.revision_ref != self.candidate_revision_ref:
            raise ProductionStateIntegrityError("reuse receipt revision and materialization bindings do not match")
        if type(self.dependency_fingerprint) is not OperationalDependencyFingerprint:
            raise ProductionStateValidationError("reuse receipt requires an exact causal fingerprint")
        require_m02_build_plan(self.m02_build_ref, "m02_build_ref")
        require_identifier(self.m02_node_id, "m02_node_id")
        step = _m02_build_step(self.m02_build_ref, self.m02_node_id)
        if type(self.m02_reuse_receipt) is not M02ReuseReceipt or step.receipt != self.m02_reuse_receipt or not self.m02_reuse_receipt.satisfies_output:
            raise ProductionStateIntegrityError("M06 reuse receipt must preserve its exact admitted M02 reuse evidence")
        if self.candidate_materialization_ref.content_digest.algorithm != "sha256" or self.candidate_materialization_ref.content_digest.value != self.m02_reuse_receipt.result_digest:
            raise ProductionStateIntegrityError("M06 materialization digest must remain bound to M02 admitted output bytes")
        dimensions = require_sequence(
            self.evidence_dimensions,
            "evidence_dimensions",
            maximum=DEFAULT_LIMITS.max_fingerprint_dimensions,
            item_type=ReuseEvidenceDimension,
        )
        if len({item.name for item in dimensions}) != len(dimensions):
            raise ProductionStateValidationError("reuse admission evidence dimension names must be unique")
        required_dimension_names = {
            item.key
            for item in self.dependency_fingerprint.dimensions
            if item.mandatory and item.materiality.value == "MATERIAL"
        }
        verified_material_names = {
            item.name
            for item in dimensions
            if item.material and item.state == ReuseEvidenceState.VERIFIED
        }
        if not required_dimension_names.issubset(verified_material_names):
            raise ProductionStateAdmissionError("reuse admission must retain VERIFIED evidence for every mandatory material dimension")
        if any(item.material and item.state != ReuseEvidenceState.VERIFIED for item in dimensions):
            raise ProductionStateAdmissionError("reuse admission cannot retain stale, failed or unknown material evidence")
        object.__setattr__(self, "evidence_dimensions", dimensions)
        refs = require_sequence(self.evidence_refs, "evidence_refs", maximum=DEFAULT_LIMITS.max_fingerprint_dimensions)
        for index, ref in enumerate(refs):
            require_exact_ref(ref, f"evidence_refs[{index}]")
        expected_refs = tuple(item.evidence_ref for item in dimensions if item.material)
        if refs != expected_refs:
            raise ProductionStateIntegrityError("reuse admission evidence refs must exactly match its retained material evidence dimensions")
        object.__setattr__(self, "evidence_refs", refs)
        if not isinstance(self.equivalence, EquivalenceState):
            object.__setattr__(self, "equivalence", EquivalenceState(self.equivalence))
        if self.equivalence is not EquivalenceState.PROVEN:
            raise ProductionStateAdmissionError("reuse admission requires positive scoped equivalence evidence")
        if type(self.admitted_at_ms) is not int or self.admitted_at_ms < 0:
            raise ProductionStateValidationError("admitted_at_ms must be a nonnegative exact integer")
        require_version(self.receipt_version, "receipt_version")


@dataclass(frozen=True)
class RebuildBoundary(CanonicalRecord):
    boundary_id: str
    m02_build_ref: Any
    m02_node_id: str
    m02_slice: Any
    selected_slice: tuple[str, ...]
    recomposition_rule: str
    recomposition_version: str
    protected_identity_ref: Any
    protected_quality_ref: Any

    def __post_init__(self) -> None:
        require_identifier(self.boundary_id, "boundary_id")
        require_m02_build_plan(self.m02_build_ref, "m02_build_ref")
        require_identifier(self.m02_node_id, "m02_node_id")
        step = _m02_build_step(self.m02_build_ref, self.m02_node_id)
        if step.disposition.value != "REPAIR" or type(step.slice) is not M02DependencySlice:
            raise ProductionStateAdmissionError("partial rebuild boundary must bind an exact M02 REPAIR step with its admitted DependencySlice")
        if type(self.m02_slice) is not M02DependencySlice or self.m02_slice != step.slice:
            raise ProductionStateIntegrityError("partial rebuild boundary must preserve the exact M02 DependencySlice record")
        items = require_sequence(self.selected_slice, "selected_slice", maximum=DEFAULT_LIMITS.max_fingerprint_dimensions)
        if not items or any(type(item) is not str for item in items) or len(items) != len(set(items)):
            raise ProductionStateValidationError("partial rebuild requires a non-empty unique admitted slice")
        object.__setattr__(self, "selected_slice", tuple(sorted(items)))
        expected_slice = {f"{step.slice.axis}:{value}" for value in step.slice.values}
        if set(self.selected_slice) != expected_slice:
            raise ProductionStateIntegrityError("M06 partial rebuild slice must preserve the exact M02 axis and selected values")
        require_identifier(self.recomposition_rule, "recomposition_rule")
        require_version(self.recomposition_version, "recomposition_version")
        require_exact_ref(self.protected_identity_ref, "protected_identity_ref")
        require_exact_ref(self.protected_quality_ref, "protected_quality_ref")


@dataclass(frozen=True)
class WorkFrontier(CanonicalRecord):
    decision_id: str
    candidate_refs: tuple[Any, ...]
    uncertain_refs: tuple[Any, ...]
    blockers: tuple[str, ...]
    generation: int
    disposition: WorkDisposition
    m02_build_ref: Any

    def __post_init__(self) -> None:
        require_identifier(self.decision_id, "decision_id")
        for name in ("candidate_refs", "uncertain_refs"):
            values = require_sequence(getattr(self, name), name, maximum=DEFAULT_LIMITS.max_lineage_nodes)
            for index, value in enumerate(values):
                require_exact_ref(value, f"{name}[{index}]")
            object.__setattr__(self, name, values)
        if any(type(item) is not str for item in self.blockers):
            raise ProductionStateValidationError("frontier blockers must be strings")
        object.__setattr__(self, "blockers", tuple(sorted(set(self.blockers))))
        if type(self.generation) is not int or self.generation < 0:
            raise ProductionStateValidationError("generation must be a nonnegative exact integer")
        if not isinstance(self.disposition, WorkDisposition):
            object.__setattr__(self, "disposition", WorkDisposition(self.disposition))
        require_m02_build_plan(self.m02_build_ref, "m02_build_ref")


@dataclass(frozen=True)
class VerificationReceipt(CanonicalRecord):
    receipt_id: str
    subject_ref: Any
    result: EquivalenceState
    evidence_ref: Any
    verified_at_ms: int

    def __post_init__(self) -> None:
        require_identifier(self.receipt_id, "receipt_id")
        require_exact_ref(self.subject_ref, "subject_ref")
        require_exact_ref(self.evidence_ref, "evidence_ref")
        if not isinstance(self.result, EquivalenceState):
            object.__setattr__(self, "result", EquivalenceState(self.result))
        if type(self.verified_at_ms) is not int or self.verified_at_ms < 0:
            raise ProductionStateValidationError("verified_at_ms must be a nonnegative exact integer")


@dataclass(frozen=True)
class MixedReconstructionReceipt(CanonicalRecord):
    receipt_id: str
    target_ref: OperationalRevisionRef
    rebuilt_ancestry: tuple[OperationalRevisionRef, ...]
    reused_ancestry: tuple[OperationalRevisionRef, ...]
    reuse_receipts: tuple[ReuseAdmissionReceipt, ...]
    boundary: RebuildBoundary
    recomposition_version: str
    identity_protected_ref: Any
    quality_obligation_ref: Any
    created_at_ms: int

    def __post_init__(self) -> None:
        require_identifier(self.receipt_id, "receipt_id")
        if type(self.target_ref) is not OperationalRevisionRef or type(self.boundary) is not RebuildBoundary:
            raise ProductionStateValidationError("mixed reconstruction requires exact target and rebuild boundary")
        rebuilt = require_sequence(self.rebuilt_ancestry, "rebuilt_ancestry", maximum=DEFAULT_LIMITS.max_lineage_nodes, item_type=OperationalRevisionRef)
        reused = require_sequence(self.reused_ancestry, "reused_ancestry", maximum=DEFAULT_LIMITS.max_lineage_nodes, item_type=OperationalRevisionRef)
        if not rebuilt or not reused:
            raise ProductionStateAdmissionError("mixed reconstruction must declare both rebuilt and reused ancestry")
        if set(rebuilt) & set(reused):
            raise ProductionStateIntegrityError("an ancestor cannot be both rebuilt and reused in one receipt")
        object.__setattr__(self, "rebuilt_ancestry", rebuilt)
        object.__setattr__(self, "reused_ancestry", reused)
        reuse = require_sequence(self.reuse_receipts, "reuse_receipts", maximum=DEFAULT_LIMITS.max_lineage_nodes, item_type=ReuseAdmissionReceipt)
        if {item.candidate_revision_ref for item in reuse} != set(reused):
            raise ProductionStateAdmissionError("each reused ancestor must have its matching scoped reuse admission receipt")
        object.__setattr__(self, "reuse_receipts", reuse)
        require_version(self.recomposition_version, "recomposition_version")
        require_exact_ref(self.identity_protected_ref, "identity_protected_ref")
        require_exact_ref(self.quality_obligation_ref, "quality_obligation_ref")
        if self.identity_protected_ref != self.boundary.protected_identity_ref or self.quality_obligation_ref != self.boundary.protected_quality_ref:
            raise ProductionStateIntegrityError("mixed rebuild cannot weaken boundary identity or quality obligations")
        if type(self.created_at_ms) is not int or self.created_at_ms < 0:
            raise ProductionStateValidationError("created_at_ms must be a nonnegative exact integer")


def admit_reuse(proof: ReuseProof, *, receipt_id: str, decision_id: str, admitted_at_ms: int) -> ReuseAdmissionReceipt:
    if type(proof) is not ReuseProof:
        raise ProductionStateValidationError("proof must be an exact immutable ReuseProof")
    if proof.cache_hit_only or proof.digest_only:
        raise ProductionStateAdmissionError("cache presence or digest equality alone cannot authorize reuse")
    required = [item for item in proof.dimensions if item.material]
    if not required:
        raise ProductionStateAdmissionError("reuse requires positive evidence for at least one material dimension")
    if any(item.state != ReuseEvidenceState.VERIFIED for item in required):
        raise ProductionStateAdmissionError("every mandatory material reuse dimension must have current VERIFIED evidence")
    return ReuseAdmissionReceipt(
        receipt_id,
        decision_id,
        proof.candidate_revision_ref,
        proof.candidate_materialization_ref,
        proof.dependency_fingerprint,
        proof.m02_build_ref,
        proof.m02_node_id,
        _m02_build_step(proof.m02_build_ref, proof.m02_node_id).receipt,
        proof.dimensions,
        tuple(item.evidence_ref for item in required),
        EquivalenceState.PROVEN,
        admitted_at_ms,
    )


def decide_work(
    requested: WorkDisposition,
    *,
    decision_id: str | None = None,
    impact: ImpactConeReceipt | None = None,
    reuse_receipt: ReuseAdmissionReceipt | None = None,
    verification: VerificationReceipt | None = None,
    boundary: RebuildBoundary | None = None,
    mandatory_state_known: bool = True,
) -> WorkDisposition:
    """Return the safest disposition justified by supplied positive evidence."""
    if not isinstance(requested, WorkDisposition):
        requested = WorkDisposition(requested)
    if decision_id is not None:
        require_identifier(decision_id, "decision_id")
    if not mandatory_state_known:
        return WorkDisposition.BLOCKED
    if requested is WorkDisposition.NO_WORK_PROVEN:
        if impact is None or impact.state is not ImpactState.UNAFFECTED_PROVEN:
            raise ProductionStateAdmissionError("NO_WORK_PROVEN requires a positive complete-index unaffected proof")
        validate_impact_cone(impact)
        return requested
    if requested in {WorkDisposition.REUSE_EXACT, WorkDisposition.REUSE_WITH_VERIFICATION}:
        if reuse_receipt is None or type(reuse_receipt) is not ReuseAdmissionReceipt:
            return WorkDisposition.BLOCKED
        if decision_id is None or reuse_receipt.decision_id != decision_id:
            return WorkDisposition.BLOCKED
        if requested is WorkDisposition.REUSE_WITH_VERIFICATION:
            if (
                verification is None
                or type(verification) is not VerificationReceipt
                or verification.result is not EquivalenceState.PROVEN
                or verification.subject_ref != reuse_receipt.candidate_materialization_ref
            ):
                return WorkDisposition.VERIFY_ONLY
        return requested
    if requested is WorkDisposition.REBUILD_PARTIAL:
        return requested if type(boundary) is RebuildBoundary else WorkDisposition.REBUILD_FULL_TARGET
    if requested is WorkDisposition.VERIFY_ONLY:
        return requested if verification is not None else WorkDisposition.VERIFY_ONLY
    return requested


_DISPOSITION_CONSERVATISM = {
    WorkDisposition.NO_WORK_PROVEN: 0,
    WorkDisposition.REUSE_EXACT: 1,
    WorkDisposition.REUSE_WITH_VERIFICATION: 2,
    WorkDisposition.VERIFY_ONLY: 3,
    WorkDisposition.REPAIR_CANDIDATE: 4,
    WorkDisposition.REBUILD_PARTIAL: 5,
    WorkDisposition.REBUILD_FULL_TARGET: 6,
    WorkDisposition.BLOCKED: 7,
}


def expand_frontier(previous: WorkFrontier, next_frontier: WorkFrontier) -> WorkFrontier:
    if type(previous) is not WorkFrontier or type(next_frontier) is not WorkFrontier:
        raise ProductionStateValidationError("frontier expansion requires exact work frontier records")
    if previous.decision_id != next_frontier.decision_id or previous.m02_build_ref != next_frontier.m02_build_ref:
        raise ProductionStateIntegrityError("frontier expansion cannot cross decision or M02 build boundaries")
    old = {exact_ref_key(value) for value in previous.candidate_refs + previous.uncertain_refs}
    new = {exact_ref_key(value) for value in next_frontier.candidate_refs + next_frontier.uncertain_refs}
    if not old.issubset(new) or next_frontier.generation <= previous.generation:
        raise ProductionStateIntegrityError("frontier growth must be monotone and increment its generation")
    if _DISPOSITION_CONSERVATISM[next_frontier.disposition] < _DISPOSITION_CONSERVATISM[previous.disposition]:
        raise ProductionStateAdmissionError("a less conservative disposition requires a separate stronger evidence admission")
    return next_frontier


def admit_mixed_reconstruction(receipt: MixedReconstructionReceipt) -> MixedReconstructionReceipt:
    if type(receipt) is not MixedReconstructionReceipt:
        raise ProductionStateValidationError("receipt must be an exact MixedReconstructionReceipt")
    if not receipt.reuse_receipts:
        raise ProductionStateAdmissionError("mixed reconstruction requires positive reuse admission evidence")
    return receipt


def _m02_build_step(build_plan: Any, node_id: str) -> Any:
    matches = tuple(step for step in build_plan.steps if step.node_id == node_id)
    if len(matches) != 1:
        raise ProductionStateAdmissionError("M02 build plan must contain exactly one step for the bound node")
    if build_plan.blocked:
        raise ProductionStateAdmissionError("M02 build plan contains blocked nodes and cannot support safe M06 work admission")
    return matches[0]
