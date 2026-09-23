"""Positive-proof lineage cleanup, two-phase deletion evidence and rollback receipts."""

from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import dataclass
from typing import Any

from iris_project_os.identity import EntityKind, ExternalRef
from iris_project_os.snapshots import Snapshot as M02Snapshot

from .base import CanonicalRecord, canonical_bytes, exact_ref_key, require_exact_ref, require_sequence
from .enums import CleanupState, DeletionAuthorizationState, DeletionState, IndexState, RollbackState
from .errors import ProductionStateAdmissionError, ProductionStateIntegrityError, ProductionStateValidationError
from .limits import DEFAULT_LIMITS
from .reconstruction import ReproducibilityReceipt
from .revisions import OperationalRevisionRef
from .versions import CORE_SCHEMA_VERSION, require_identifier, require_text

__all__ = [
    "LineageEdge",
    "LineageGraph",
    "RetentionPinEvidence",
    "LineagePath",
    "ProtectedClosureEvidence",
    "CleanupEligibilityReceipt",
    "LogicalRetirementReceipt",
    "DeletionAuthorizationReceipt",
    "DeletionRevalidationReceipt",
    "DeletionCompletionReceipt",
    "RollbackPlan",
    "RollbackReceipt",
    "build_lineage_graph",
    "evaluate_cleanup",
    "record_deletion_authorization",
    "revalidate_deletion_authorization",
    "record_deletion_completion",
    "record_rollback",
]


@dataclass(frozen=True)
class LineageEdge(CanonicalRecord):
    ancestor_ref: Any
    descendant_ref: Any
    relation: str

    def __post_init__(self) -> None:
        require_exact_ref(self.ancestor_ref, "ancestor_ref")
        require_exact_ref(self.descendant_ref, "descendant_ref")
        require_identifier(self.relation, "relation")
        if self.ancestor_ref == self.descendant_ref:
            raise ProductionStateIntegrityError("lineage edge cannot point to itself")


@dataclass(frozen=True)
class LineageGraph(CanonicalRecord):
    graph_id: str
    epoch: str
    state: IndexState
    edges: tuple[LineageEdge, ...]
    fingerprint: str
    completeness_evidence_ref: Any | None = None
    schema_version: str = CORE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_identifier(self.graph_id, "graph_id")
        require_identifier(self.epoch, "epoch")
        if not isinstance(self.state, IndexState):
            object.__setattr__(self, "state", IndexState(self.state))
        edges = require_sequence(self.edges, "edges", maximum=DEFAULT_LIMITS.max_lineage_edges, item_type=LineageEdge)
        keys = [(exact_ref_key(item.ancestor_ref), exact_ref_key(item.descendant_ref), item.relation) for item in edges]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ProductionStateValidationError("lineage edges must be unique and canonically sorted")
        object.__setattr__(self, "edges", edges)
        if len(self.fingerprint) != 64 or any(char not in "0123456789abcdef" for char in self.fingerprint):
            raise ProductionStateValidationError("lineage fingerprint must be sha256")
        if hashlib.sha256(canonical_bytes(edges)).hexdigest() != self.fingerprint:
            raise ProductionStateIntegrityError("lineage graph fingerprint does not match its exact edge set")
        if self.completeness_evidence_ref is not None:
            require_exact_ref(self.completeness_evidence_ref, "completeness_evidence_ref")
        if self.state is IndexState.COMPLETE_FRESH and self.completeness_evidence_ref is None:
            raise ProductionStateAdmissionError("complete fresh lineage graph requires exact closure-completeness evidence")
        _require_acyclic(edges)


@dataclass(frozen=True)
class RetentionPinEvidence(CanonicalRecord):
    pin_ref: Any
    protected_refs: tuple[Any, ...]
    active: bool
    current_policy_evidence_ref: Any

    def __post_init__(self) -> None:
        require_exact_ref(self.pin_ref, "pin_ref")
        refs = require_sequence(self.protected_refs, "protected_refs", maximum=DEFAULT_LIMITS.max_lineage_nodes)
        for index, ref in enumerate(refs):
            require_exact_ref(ref, f"protected_refs[{index}]")
        if not refs:
            raise ProductionStateValidationError("retention pin must protect at least one exact ref")
        object.__setattr__(self, "protected_refs", refs)
        if type(self.active) is not bool:
            raise ProductionStateValidationError("active must be a boolean")
        require_exact_ref(self.current_policy_evidence_ref, "current_policy_evidence_ref")


@dataclass(frozen=True)
class LineagePath(CanonicalRecord):
    refs: tuple[Any, ...]

    def __post_init__(self) -> None:
        refs = require_sequence(self.refs, "refs", maximum=DEFAULT_LIMITS.max_lineage_nodes)
        if len(refs) < 2:
            raise ProductionStateValidationError("lineage path must contain at least one edge")
        for index, ref in enumerate(refs):
            require_exact_ref(ref, f"refs[{index}]")
        object.__setattr__(self, "refs", refs)


@dataclass(frozen=True)
class ProtectedClosureEvidence(CanonicalRecord):
    closure_kind: str
    protected_refs: tuple[Any, ...]
    evidence_ref: Any

    def __post_init__(self) -> None:
        allowed = {"M02_HISTORY", "M05_IDENTITY", "REUSED_ANCESTRY", "RECONSTRUCTION", "RELEASE", "RETENTION"}
        if self.closure_kind not in allowed:
            raise ProductionStateValidationError("unknown protected closure category")
        refs = require_sequence(self.protected_refs, "protected_refs", maximum=DEFAULT_LIMITS.max_lineage_nodes)
        for index, ref in enumerate(refs):
            require_exact_ref(ref, f"protected_refs[{index}]")
        object.__setattr__(self, "protected_refs", refs)
        require_exact_ref(self.evidence_ref, "evidence_ref")


@dataclass(frozen=True)
class CleanupEligibilityReceipt(CanonicalRecord):
    receipt_id: str
    target_ref: Any
    state: CleanupState
    graph_id: str
    graph_epoch: str
    graph_fingerprint: str
    source_graph: LineageGraph
    protected_closures: tuple[ProtectedClosureEvidence, ...]
    retention_pin_evidence: tuple[RetentionPinEvidence, ...]
    protected_roots: tuple[Any, ...]
    reachable_paths: tuple[LineagePath, ...]
    active_retention_pin_refs: tuple[Any, ...]
    checked_at_ms: int
    reason: str

    def __post_init__(self) -> None:
        require_identifier(self.receipt_id, "receipt_id")
        require_exact_ref(self.target_ref, "target_ref")
        if not isinstance(self.state, CleanupState):
            object.__setattr__(self, "state", CleanupState(self.state))
        require_identifier(self.graph_id, "graph_id")
        require_identifier(self.graph_epoch, "graph_epoch")
        if len(self.graph_fingerprint) != 64 or any(char not in "0123456789abcdef" for char in self.graph_fingerprint):
            raise ProductionStateValidationError("graph_fingerprint must be sha256")
        if type(self.source_graph) is not LineageGraph:
            raise ProductionStateValidationError("cleanup receipt must embed its exact lineage graph evidence")
        if (self.graph_id, self.graph_epoch, self.graph_fingerprint) != (self.source_graph.graph_id, self.source_graph.epoch, self.source_graph.fingerprint):
            raise ProductionStateIntegrityError("cleanup receipt graph bindings do not match its embedded graph")
        closures = require_sequence(self.protected_closures, "protected_closures", maximum=6, item_type=ProtectedClosureEvidence)
        required_kinds = {"M02_HISTORY", "M05_IDENTITY", "REUSED_ANCESTRY", "RECONSTRUCTION", "RELEASE", "RETENTION"}
        if {item.closure_kind for item in closures} != required_kinds or len(closures) != len(required_kinds):
            raise ProductionStateAdmissionError("cleanup requires positive evidence for all six protected closure classes")
        object.__setattr__(self, "protected_closures", closures)
        pins = require_sequence(self.retention_pin_evidence, "retention_pin_evidence", maximum=DEFAULT_LIMITS.max_records, item_type=RetentionPinEvidence)
        object.__setattr__(self, "retention_pin_evidence", pins)
        for field in ("protected_roots", "active_retention_pin_refs"):
            refs = require_sequence(getattr(self, field), field, maximum=DEFAULT_LIMITS.max_lineage_nodes)
            for index, ref in enumerate(refs):
                require_exact_ref(ref, f"{field}[{index}]")
            object.__setattr__(self, field, refs)
        expected_roots = {exact_ref_key(ref) for proof in closures for ref in proof.protected_refs}
        actual_roots = {exact_ref_key(ref) for ref in self.protected_roots}
        if expected_roots != actual_roots:
            raise ProductionStateIntegrityError("protected root list must exactly match the complete closure evidence")
        retention_roots = {exact_ref_key(ref) for proof in closures if proof.closure_kind == "RETENTION" for ref in proof.protected_refs}
        if any(item.active and any(exact_ref_key(ref) not in retention_roots for ref in item.protected_refs) for item in pins):
            raise ProductionStateIntegrityError("active retention pins must be represented in the retention protected closure")
        expected_pin_refs = {
            exact_ref_key(item.pin_ref): item.pin_ref
            for item in pins
            if item.active and any(ref == self.target_ref for ref in item.protected_refs)
        }
        actual_pin_refs = {exact_ref_key(ref) for ref in self.active_retention_pin_refs}
        if set(expected_pin_refs) != actual_pin_refs:
            raise ProductionStateIntegrityError("active retention pin refs must match embedded exact pin evidence")
        paths = require_sequence(self.reachable_paths, "reachable_paths", maximum=DEFAULT_LIMITS.max_lineage_edges, item_type=LineagePath)
        object.__setattr__(self, "reachable_paths", paths)
        if type(self.checked_at_ms) is not int or self.checked_at_ms < 0:
            raise ProductionStateValidationError("checked_at_ms must be a nonnegative exact integer")
        require_text(self.reason, "reason", maximum=2048)
        if self.state is CleanupState.ELIGIBLE and (paths or self.active_retention_pin_refs):
            raise ProductionStateIntegrityError("cleanup eligibility cannot coexist with reachable paths or active pins")
        if self.state is CleanupState.ELIGIBLE:
            if self.source_graph.state is not IndexState.COMPLETE_FRESH:
                raise ProductionStateAdmissionError("partial/stale/corrupt lineage evidence cannot prove cleanup eligibility")
            if _find_lineage_paths(self.target_ref, self.protected_roots, self.source_graph):
                raise ProductionStateIntegrityError("cleanup eligibility contradicts its embedded lineage graph")
        if self.state is CleanupState.REACHABLE and not paths:
            raise ProductionStateIntegrityError("reachable cleanup state requires at least one retained lineage path")
        if self.state is CleanupState.REACHABLE and tuple(paths) != _find_lineage_paths(self.target_ref, self.protected_roots, self.source_graph):
            raise ProductionStateIntegrityError("reachable cleanup paths do not match the embedded lineage graph")


@dataclass(frozen=True)
class LogicalRetirementReceipt(CanonicalRecord):
    receipt_id: str
    subject_ref: Any
    eligibility: CleanupEligibilityReceipt
    authority_ref: Any
    retired_at_ms: int

    def __post_init__(self) -> None:
        require_identifier(self.receipt_id, "receipt_id")
        require_exact_ref(self.subject_ref, "subject_ref")
        if type(self.eligibility) is not CleanupEligibilityReceipt or self.eligibility.state is not CleanupState.ELIGIBLE:
            raise ProductionStateAdmissionError("logical retirement requires positive cleanup eligibility evidence")
        if self.eligibility.target_ref != self.subject_ref:
            raise ProductionStateIntegrityError("retirement and eligibility must bind the same exact subject")
        require_exact_ref(self.authority_ref, "authority_ref")
        if type(self.retired_at_ms) is not int or self.retired_at_ms < 0:
            raise ProductionStateValidationError("retired_at_ms must be a nonnegative exact integer")


@dataclass(frozen=True)
class DeletionAuthorizationReceipt(CanonicalRecord):
    authorization_id: str
    target_ref: Any
    eligibility: CleanupEligibilityReceipt
    retirement: LogicalRetirementReceipt
    state: DeletionAuthorizationState
    m55_authorization_ref: Any
    current_policy_ref: Any
    authorized_at_ms: int

    def __post_init__(self) -> None:
        require_identifier(self.authorization_id, "authorization_id")
        require_exact_ref(self.target_ref, "target_ref")
        if type(self.eligibility) is not CleanupEligibilityReceipt or type(self.retirement) is not LogicalRetirementReceipt:
            raise ProductionStateValidationError("deletion authorization requires exact eligibility and retirement receipts")
        if self.eligibility.target_ref != self.target_ref or self.retirement.subject_ref != self.target_ref:
            raise ProductionStateIntegrityError("deletion authorization subject bindings do not match")
        if self.retirement.eligibility != self.eligibility:
            raise ProductionStateIntegrityError("retirement must bind this exact cleanup eligibility receipt")
        if not isinstance(self.state, DeletionAuthorizationState):
            object.__setattr__(self, "state", DeletionAuthorizationState(self.state))
        require_exact_ref(self.m55_authorization_ref, "m55_authorization_ref")
        require_exact_ref(self.current_policy_ref, "current_policy_ref")
        if type(self.authorized_at_ms) is not int or self.authorized_at_ms < 0:
            raise ProductionStateValidationError("authorized_at_ms must be a nonnegative exact integer")
        if self.state is DeletionAuthorizationState.AUTHORIZED and self.eligibility.state is not CleanupState.ELIGIBLE:
            raise ProductionStateAdmissionError("M55 deletion authorization requires current positive cleanup eligibility")


@dataclass(frozen=True)
class DeletionRevalidationReceipt(CanonicalRecord):
    receipt_id: str
    authorization_id: str
    target_ref: Any
    state: DeletionAuthorizationState
    current_eligibility: CleanupEligibilityReceipt
    current_policy_ref: Any
    current_policy_authorized: bool
    revalidated_at_ms: int
    reason: str

    def __post_init__(self) -> None:
        require_identifier(self.receipt_id, "receipt_id")
        require_identifier(self.authorization_id, "authorization_id")
        require_exact_ref(self.target_ref, "target_ref")
        if not isinstance(self.state, DeletionAuthorizationState):
            object.__setattr__(self, "state", DeletionAuthorizationState(self.state))
        if type(self.current_eligibility) is not CleanupEligibilityReceipt:
            raise ProductionStateValidationError("deletion revalidation requires exact current cleanup eligibility")
        if self.current_eligibility.target_ref != self.target_ref:
            raise ProductionStateIntegrityError("deletion revalidation and current eligibility must bind the same target")
        require_exact_ref(self.current_policy_ref, "current_policy_ref")
        if type(self.current_policy_authorized) is not bool:
            raise ProductionStateValidationError("current_policy_authorized must be a boolean")
        if type(self.revalidated_at_ms) is not int or self.revalidated_at_ms < 0:
            raise ProductionStateValidationError("revalidated_at_ms must be a nonnegative exact integer")
        require_text(self.reason, "reason", maximum=2048)
        if self.state is DeletionAuthorizationState.AUTHORIZED and (
            self.current_eligibility.state is not CleanupState.ELIGIBLE or not self.current_policy_authorized
        ):
            raise ProductionStateAdmissionError("authorized deletion revalidation requires current eligibility and policy authorization")


@dataclass(frozen=True)
class DeletionCompletionReceipt(CanonicalRecord):
    receipt_id: str
    authorization: DeletionAuthorizationReceipt
    revalidation: DeletionRevalidationReceipt
    target_ref: Any
    state: DeletionState
    physical_result_ref: Any
    completed_at_ms: int

    def __post_init__(self) -> None:
        require_identifier(self.receipt_id, "receipt_id")
        if type(self.authorization) is not DeletionAuthorizationReceipt:
            raise ProductionStateValidationError("deletion completion requires the exact authorization receipt")
        if type(self.revalidation) is not DeletionRevalidationReceipt:
            raise ProductionStateValidationError("deletion completion requires exact current revalidation evidence")
        require_exact_ref(self.target_ref, "target_ref")
        if self.authorization.target_ref != self.target_ref or self.revalidation.target_ref != self.target_ref:
            raise ProductionStateIntegrityError("deletion completion, authorization and revalidation must bind the same target")
        if self.revalidation.authorization_id != self.authorization.authorization_id:
            raise ProductionStateIntegrityError("deletion revalidation must bind the exact authorization being completed")
        if self.authorization.state is not DeletionAuthorizationState.AUTHORIZED or self.revalidation.state is not DeletionAuthorizationState.AUTHORIZED:
            raise ProductionStateAdmissionError("physical deletion completion requires active authorization and current revalidation")
        if not isinstance(self.state, DeletionState):
            object.__setattr__(self, "state", DeletionState(self.state))
        require_exact_ref(self.physical_result_ref, "physical_result_ref")
        if type(self.completed_at_ms) is not int or self.completed_at_ms < 0:
            raise ProductionStateValidationError("completed_at_ms must be a nonnegative exact integer")
        if self.completed_at_ms < self.revalidation.revalidated_at_ms:
            raise ProductionStateIntegrityError("physical deletion completion cannot predate its current revalidation")


@dataclass(frozen=True)
class RollbackPlan(CanonicalRecord):
    plan_id: str
    current_snapshot: Any
    target_snapshot: Any
    previous_current_revision_ref: OperationalRevisionRef
    m02_rollback_ref: Any
    current_rights_evidence_ref: Any
    current_security_evidence_ref: Any
    current_rights_authorized: bool
    current_security_authorized: bool
    created_at_ms: int

    def __post_init__(self) -> None:
        require_identifier(self.plan_id, "plan_id")
        _require_m02_snapshot(self.current_snapshot, "current_snapshot")
        _require_m02_snapshot(self.target_snapshot, "target_snapshot")
        if (
            self.current_snapshot.project_id != self.target_snapshot.project_id
            or self.current_snapshot.production_id != self.target_snapshot.production_id
        ):
            raise ProductionStateIntegrityError("rollback current and target snapshots must belong to the same project and production")
        if self.current_snapshot.snapshot_id == self.target_snapshot.snapshot_id:
            raise ProductionStateAdmissionError("rollback target must be a distinct exact historical snapshot")
        if type(self.previous_current_revision_ref) is not OperationalRevisionRef:
            raise ProductionStateValidationError("previous_current_revision_ref must be an exact M06 operational revision")
        require_exact_ref(self.m02_rollback_ref, "m02_rollback_ref")
        require_exact_ref(self.current_rights_evidence_ref, "current_rights_evidence_ref")
        require_exact_ref(self.current_security_evidence_ref, "current_security_evidence_ref")
        if type(self.current_rights_authorized) is not bool or type(self.current_security_authorized) is not bool:
            raise ProductionStateValidationError("current authority outcomes must be booleans")
        if type(self.created_at_ms) is not int or self.created_at_ms < 0:
            raise ProductionStateValidationError("created_at_ms must be a nonnegative exact integer")


@dataclass(frozen=True)
class RollbackReceipt(CanonicalRecord):
    receipt_id: str
    plan: RollbackPlan
    state: RollbackState
    resulting_revision_ref: OperationalRevisionRef | None
    reproducibility_receipt: ReproducibilityReceipt | None
    failure_evidence_ref: Any | None
    recorded_at_ms: int

    def __post_init__(self) -> None:
        require_identifier(self.receipt_id, "receipt_id")
        if type(self.plan) is not RollbackPlan:
            raise ProductionStateValidationError("rollback receipt requires an exact rollback plan")
        if not isinstance(self.state, RollbackState):
            object.__setattr__(self, "state", RollbackState(self.state))
        if self.resulting_revision_ref is not None and type(self.resulting_revision_ref) is not OperationalRevisionRef:
            raise ProductionStateValidationError("rollback result must be a new M06 revision ref or None")
        if self.reproducibility_receipt is not None and type(self.reproducibility_receipt) is not ReproducibilityReceipt:
            raise ProductionStateValidationError("reproducibility_receipt must be exact evidence or None")
        if self.state is RollbackState.COMPLETE:
            if self.resulting_revision_ref is None or self.reproducibility_receipt is None:
                raise ProductionStateAdmissionError("complete rollback requires an appended result and reproducibility evidence")
            if not self.plan.current_rights_authorized or not self.plan.current_security_authorized:
                raise ProductionStateAdmissionError("current M53/M54 authority must allow rollback")
            if self.resulting_revision_ref == self.plan.previous_current_revision_ref:
                raise ProductionStateIntegrityError("rollback must append a new operational revision")
            if self.reproducibility_receipt.output_revision_ref != self.resulting_revision_ref:
                raise ProductionStateIntegrityError("rollback result must be the exact output proven by its reproducibility receipt")
            if self.reproducibility_receipt.manifest.method.value != "ROLLBACK":
                raise ProductionStateAdmissionError("complete rollback requires a reconstruction manifest explicitly classified as ROLLBACK")
            target_snapshot_bound = any(
                type(ref) is ExternalRef
                and ref.kind is EntityKind.SNAPSHOT
                and ref.reference == self.plan.target_snapshot.snapshot_id
                for ref in self.reproducibility_receipt.manifest.exact_input_refs
            )
            if not target_snapshot_bound:
                raise ProductionStateAdmissionError("rollback reproducibility evidence must bind the exact target M02 snapshot")
        if self.failure_evidence_ref is not None:
            require_exact_ref(self.failure_evidence_ref, "failure_evidence_ref")
        if self.state in {RollbackState.FAILED, RollbackState.PARTIAL, RollbackState.BLOCKED} and self.failure_evidence_ref is None:
            raise ProductionStateAdmissionError("failed, partial or blocked rollback must retain explicit failure evidence")
        if type(self.recorded_at_ms) is not int or self.recorded_at_ms < 0:
            raise ProductionStateValidationError("recorded_at_ms must be a nonnegative exact integer")


def build_lineage_graph(
    graph_id: str,
    epoch: str,
    edges: tuple[LineageEdge, ...],
    *,
    state: IndexState = IndexState.UNKNOWN,
    completeness_evidence_ref: Any | None = None,
) -> LineageGraph:
    records = require_sequence(edges, "edges", maximum=DEFAULT_LIMITS.max_lineage_edges, item_type=LineageEdge)
    ordered = tuple(sorted(records, key=lambda item: (exact_ref_key(item.ancestor_ref), exact_ref_key(item.descendant_ref), item.relation)))
    fingerprint = hashlib.sha256(canonical_bytes(ordered)).hexdigest()
    return LineageGraph(graph_id, epoch, state, ordered, fingerprint, completeness_evidence_ref)


def evaluate_cleanup(
    target_ref: Any,
    protected_roots: tuple[Any, ...],
    graph: LineageGraph,
    *,
    protected_closures: tuple[ProtectedClosureEvidence, ...],
    retention_pins: tuple[RetentionPinEvidence, ...] = (),
    receipt_id: str,
    checked_at_ms: int,
) -> CleanupEligibilityReceipt:
    require_exact_ref(target_ref, "target_ref")
    roots = require_sequence(protected_roots, "protected_roots", maximum=DEFAULT_LIMITS.max_lineage_nodes)
    for index, root in enumerate(roots):
        require_exact_ref(root, f"protected_roots[{index}]")
    closures = require_sequence(protected_closures, "protected_closures", maximum=6, item_type=ProtectedClosureEvidence)
    required_kinds = {"M02_HISTORY", "M05_IDENTITY", "REUSED_ANCESTRY", "RECONSTRUCTION", "RELEASE", "RETENTION"}
    if {item.closure_kind for item in closures} != required_kinds or len(closures) != len(required_kinds):
        raise ProductionStateAdmissionError("cleanup requires all six protected closure evidence categories")
    complete_roots = {exact_ref_key(ref) for proof in closures for ref in proof.protected_refs}
    if complete_roots != {exact_ref_key(ref) for ref in roots}:
        raise ProductionStateIntegrityError("protected roots do not match the complete closure evidence")
    if type(graph) is not LineageGraph:
        raise ProductionStateValidationError("graph must be an exact LineageGraph")
    pins = require_sequence(retention_pins, "retention_pins", maximum=DEFAULT_LIMITS.max_records, item_type=RetentionPinEvidence)
    active = tuple(item for item in pins if item.active)
    active_pin_refs = tuple(item.pin_ref for item in active if target_ref in item.protected_refs)
    if graph.state is not IndexState.COMPLETE_FRESH:
        state = CleanupState.NOT_SAFE_TO_DELETE
        reason = f"lineage graph state {graph.state.value} cannot prove all protected closures"
        paths: tuple[LineagePath, ...] = ()
    elif active_pin_refs:
        state = CleanupState.RETENTION_PINNED
        reason = "an active retention pin protects the exact target ref"
        paths = ()
    else:
        found = list(_find_lineage_paths(target_ref, roots, graph))
        state, reason = (CleanupState.REACHABLE, "target is reachable from a protected lineage root") if found else (CleanupState.ELIGIBLE, "complete fresh graph proves the target outside every evidenced protected closure")
        paths = tuple(found)
    return CleanupEligibilityReceipt(receipt_id, target_ref, state, graph.graph_id, graph.epoch, graph.fingerprint, graph, closures, pins, roots, paths, active_pin_refs, checked_at_ms, reason)


def record_deletion_authorization(
    eligibility: CleanupEligibilityReceipt,
    retirement: LogicalRetirementReceipt,
    *,
    authorization_id: str,
    m55_authorization_ref: Any,
    current_policy_ref: Any,
    authorized_at_ms: int,
) -> DeletionAuthorizationReceipt:
    if type(eligibility) is not CleanupEligibilityReceipt or eligibility.state is not CleanupState.ELIGIBLE:
        raise ProductionStateAdmissionError("only a positive exact cleanup eligibility receipt can be authorized")
    if type(retirement) is not LogicalRetirementReceipt or retirement.subject_ref != eligibility.target_ref:
        raise ProductionStateIntegrityError("logical retirement must bind the eligible exact target")
    require_exact_ref(m55_authorization_ref, "m55_authorization_ref")
    return DeletionAuthorizationReceipt(authorization_id, eligibility.target_ref, eligibility, retirement, DeletionAuthorizationState.AUTHORIZED, m55_authorization_ref, current_policy_ref, authorized_at_ms)


def revalidate_deletion_authorization(
    authorization: DeletionAuthorizationReceipt,
    current_graph: LineageGraph,
    *,
    current_protected_closures: tuple[ProtectedClosureEvidence, ...],
    current_retention_pins: tuple[RetentionPinEvidence, ...] = (),
    current_policy_ref: Any,
    current_policy_authorized: bool,
    receipt_id: str,
    revalidated_at_ms: int,
) -> DeletionRevalidationReceipt:
    if type(authorization) is not DeletionAuthorizationReceipt or type(current_graph) is not LineageGraph:
        raise ProductionStateValidationError("revalidation requires exact M06 authorization and lineage evidence")
    require_exact_ref(current_policy_ref, "current_policy_ref")
    if type(current_policy_authorized) is not bool:
        raise ProductionStateValidationError("current_policy_authorized must be a boolean")
    if type(revalidated_at_ms) is not int or revalidated_at_ms < authorization.authorized_at_ms:
        raise ProductionStateValidationError("revalidated_at_ms must not predate deletion authorization")

    closures = require_sequence(
        current_protected_closures,
        "current_protected_closures",
        maximum=6,
        item_type=ProtectedClosureEvidence,
    )
    pins = require_sequence(
        current_retention_pins,
        "current_retention_pins",
        maximum=DEFAULT_LIMITS.max_records,
        item_type=RetentionPinEvidence,
    )
    roots_by_key = {
        exact_ref_key(ref): ref
        for proof in closures
        for ref in proof.protected_refs
    }
    roots = tuple(roots_by_key[key] for key in sorted(roots_by_key))
    current_eligibility = evaluate_cleanup(
        authorization.target_ref,
        roots,
        current_graph,
        protected_closures=closures,
        retention_pins=pins,
        receipt_id=f"{receipt_id}-eligibility",
        checked_at_ms=revalidated_at_ms,
    )

    if authorization.state is not DeletionAuthorizationState.AUTHORIZED:
        state, reason = authorization.state, "original deletion authorization is no longer active"
    elif current_policy_ref != authorization.current_policy_ref:
        state, reason = DeletionAuthorizationState.STALE, "current policy ref changed after deletion authorization"
    elif not current_policy_authorized:
        state, reason = DeletionAuthorizationState.REVOKED, "current policy no longer authorizes deletion"
    elif (
        current_graph.graph_id,
        current_graph.epoch,
        current_graph.fingerprint,
        current_graph.state,
    ) != (
        authorization.eligibility.graph_id,
        authorization.eligibility.graph_epoch,
        authorization.eligibility.graph_fingerprint,
        IndexState.COMPLETE_FRESH,
    ):
        state, reason = DeletionAuthorizationState.STALE, "lineage graph changed after deletion authorization"
    elif closures != authorization.eligibility.protected_closures or pins != authorization.eligibility.retention_pin_evidence:
        state, reason = DeletionAuthorizationState.STALE, "protected closure or retention evidence changed after deletion authorization"
    elif current_eligibility.state is not CleanupState.ELIGIBLE:
        state, reason = DeletionAuthorizationState.STALE, "current evidence no longer proves deletion eligibility"
    else:
        state, reason = DeletionAuthorizationState.AUTHORIZED, "authorization remains current against exact lineage, closure, retention and policy evidence"

    return DeletionRevalidationReceipt(
        receipt_id,
        authorization.authorization_id,
        authorization.target_ref,
        state,
        current_eligibility,
        current_policy_ref,
        current_policy_authorized,
        revalidated_at_ms,
        reason,
    )


def record_deletion_completion(
    authorization: DeletionAuthorizationReceipt,
    revalidation: DeletionRevalidationReceipt,
    *,
    physical_result_ref: Any,
    success: bool,
    completed_at_ms: int,
    receipt_id: str,
) -> DeletionCompletionReceipt:
    if type(authorization) is not DeletionAuthorizationReceipt or authorization.state is not DeletionAuthorizationState.AUTHORIZED:
        raise ProductionStateAdmissionError("completion evidence requires active M55 authorization")
    if type(revalidation) is not DeletionRevalidationReceipt:
        raise ProductionStateValidationError("completion evidence requires exact current deletion revalidation")
    if revalidation.authorization_id != authorization.authorization_id or revalidation.target_ref != authorization.target_ref:
        raise ProductionStateIntegrityError("deletion completion revalidation does not bind the supplied authorization")
    if revalidation.state is not DeletionAuthorizationState.AUTHORIZED:
        raise ProductionStateAdmissionError("stale or revoked deletion authorization cannot record physical completion")
    if type(success) is not bool:
        raise ProductionStateValidationError("success must be a boolean result from M55")
    return DeletionCompletionReceipt(
        receipt_id,
        authorization,
        revalidation,
        authorization.target_ref,
        DeletionState.COMPLETED if success else DeletionState.FAILED,
        physical_result_ref,
        completed_at_ms,
    )


def record_rollback(receipt: RollbackReceipt) -> RollbackReceipt:
    if type(receipt) is not RollbackReceipt:
        raise ProductionStateValidationError("rollback must be an exact immutable receipt")
    return receipt


def _require_m02_snapshot(value: Any, field: str) -> None:
    if type(value) is not M02Snapshot:
        raise ProductionStateValidationError(f"{field} must be an exact immutable M02 Snapshot")


def _find_lineage_paths(target_ref: Any, roots: tuple[Any, ...], graph: LineageGraph) -> tuple[LineagePath, ...]:
    adjacency: dict[str, list[Any]] = {}
    for edge in graph.edges:
        adjacency.setdefault(exact_ref_key(edge.ancestor_ref), []).append(edge.descendant_ref)
    target_key = exact_ref_key(target_ref)
    found: list[LineagePath] = []
    visited_total = 0
    for root in roots:
        root_key = exact_ref_key(root)
        queue = deque([root_key])
        refs = {root_key: root}
        parent: dict[str, str | None] = {root_key: None}
        reached = False
        while queue:
            visited_total += 1
            if visited_total > DEFAULT_LIMITS.max_lineage_nodes:
                raise ProductionStateAdmissionError("lineage traversal exceeded configured safety bound")
            current_key = queue.popleft()
            if current_key == target_key:
                chain: list[Any] = []
                cursor: str | None = current_key
                while cursor is not None:
                    chain.append(refs[cursor])
                    cursor = parent[cursor]
                found.append(LineagePath(tuple(reversed(chain))))
                reached = True
                break
            for child in adjacency.get(current_key, ()):
                key = exact_ref_key(child)
                if key not in parent:
                    parent[key] = current_key
                    refs[key] = child
                    queue.append(key)
        if reached:
            continue
    return tuple(found)


def _require_acyclic(edges: tuple[LineageEdge, ...]) -> None:
    adjacency: dict[str, list[str]] = {}
    indegree: dict[str, int] = {}
    for edge in edges:
        source = exact_ref_key(edge.ancestor_ref)
        target = exact_ref_key(edge.descendant_ref)
        adjacency.setdefault(source, []).append(target)
        indegree.setdefault(source, 0)
        indegree[target] = indegree.get(target, 0) + 1
    ready = deque(key for key, degree in indegree.items() if degree == 0)
    visited = 0
    while ready:
        source = ready.popleft()
        visited += 1
        for target in adjacency.get(source, ()):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    if visited != len(indegree):
        raise ProductionStateIntegrityError("lineage graph contains a cycle")
