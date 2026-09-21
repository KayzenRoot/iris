"""M02 area C (snapshots): immutable closures, completeness claims and rollback.

A Snapshot is an immutable point-in-time closure over production state. It names
the graph revision it was taken against and points at revisions and CAS objects;
it never copies media bytes, because a cheap creative branch has to stay cheap
even when the project is huge. Byte-level deduplication is M55/M06 work, and
keeping it out of here is what lets semantic identity stay independent of storage.

The hardest rule in this module is that a Snapshot *class* is a completeness
claim, not a label. ``VALIDATED`` is refused unless the closure actually carries
the M01 decisions that make it validated, so relabelling a logical snapshot as
validated is impossible rather than merely discouraged. Rollback follows the same
discipline from the other side: it creates new history pointing at old state, and
it never pretends that moving a ref undoes the outside world.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping, Sequence

from .base import Labeled, Record, of
from .branching import (
    BranchLedger,
    IdentityAnchorPolicy,
    VariantConstraint,
    VariantSelection,
    VariantSet,
    validate_selection,
)
from .diffing import SemanticDiff, semantic_diff
from .errors import (
    GraphValidationError,
    RollbackBlockedError,
    SchemaValidationError,
    SideEffectFenceError,
    SnapshotClosureError,
    StoreConflictError,
)
from .graph import GraphRevision, MaterializationGraph, MaterializationRecord, SideEffectClass
from .identity import (
    EntityKind,
    ExternalRef,
    TransitionReceipt,
    new_id,
    require_id,
)
from .limits import (
    MAX_CLOSURE_REFS,
    MAX_RECEIPT_EVIDENCE,
    MAX_SNAPSHOT_NODES,
    MAX_VARIANT_SETS,
)
from .versions import (
    CONTRACT_VERSION,
    ComponentVersion,
    content_digest,
    require_bounded,
    require_component_version,
    require_digest,
    require_identifier,
    require_millis,
    require_optional_text,
    require_supported_version,
    require_text,
)

__all__ = [
    "SnapshotClass",
    "SnapshotDerivation",
    "RetentionReason",
    "ExternalEffectState",
    "SnapshotClosureManifest",
    "Snapshot",
    "SnapshotStore",
    "SnapshotView",
    "ExternalSideEffect",
    "DeltaPrecondition",
    "PreconditionKind",
    "ProductionDelta",
    "RollbackPlan",
    "RollbackReceipt",
    "commit_snapshot",
    "derive_snapshot",
    "plan_rollback",
    "execute_rollback",
    "retention_reasons",
    "collectable_snapshots",
]


def _refs(value: Iterable[Any], field: str) -> tuple[ExternalRef, ...]:
    """Deduplicate and order opaque references so a closure digest is stable."""

    collected = require_bounded(tuple(value), field, maximum=MAX_CLOSURE_REFS, kind="reference")
    unique = {ExternalRef.coerce(item, f"{field}[]") for item in collected}
    return tuple(sorted(unique, key=lambda item: item.text))


def _ids(value: Iterable[Any], field: str) -> tuple[str, ...]:
    collected = require_bounded(tuple(value), field, maximum=MAX_SNAPSHOT_NODES, kind="snapshot id")
    return tuple(sorted({require_id(item, f"{field}[]") for item in collected}))


class SnapshotClass(Labeled):
    """How complete a closure is. Each rank inherits the obligations below it."""

    LOGICAL_SNAPSHOT = "LOGICAL_SNAPSHOT"
    MATERIALIZED_SNAPSHOT = "MATERIALIZED_SNAPSHOT"
    VALIDATED_SNAPSHOT = "VALIDATED_SNAPSHOT"
    RELEASE_SNAPSHOT = "RELEASE_SNAPSHOT"

    @property
    def rank(self) -> int:
        return _CLASS_RANK[self]

    @property
    def requires_materialization(self) -> bool:
        return self.rank >= _CLASS_RANK[SnapshotClass.MATERIALIZED_SNAPSHOT]

    @property
    def requires_quality_evidence(self) -> bool:
        return self.rank >= _CLASS_RANK[SnapshotClass.VALIDATED_SNAPSHOT]

    @property
    def requires_release_evidence(self) -> bool:
        return self.rank >= _CLASS_RANK[SnapshotClass.RELEASE_SNAPSHOT]

    def at_least(self, other: Any) -> bool:
        return self.rank >= SnapshotClass.parse(other, "other").rank


_CLASS_RANK = {
    SnapshotClass.LOGICAL_SNAPSHOT: 0,
    SnapshotClass.MATERIALIZED_SNAPSHOT: 1,
    SnapshotClass.VALIDATED_SNAPSHOT: 2,
    SnapshotClass.RELEASE_SNAPSHOT: 3,
}


class SnapshotDerivation(Labeled):
    """Why this snapshot exists. Every derivation is still new history."""

    BASELINE = "BASELINE"
    COMMITTED = "COMMITTED"
    MERGED = "MERGED"
    TRANSPLANTED = "TRANSPLANTED"
    ROLLED_BACK = "ROLLED_BACK"


class RetentionReason(Labeled):
    """The six separate claims that keep a snapshot alive past cleanup."""

    REACHABLE_FROM_LIVE_BRANCH = "REACHABLE_FROM_LIVE_BRANCH"
    CARRIED_BY_VALIDATED_SNAPSHOT = "CARRIED_BY_VALIDATED_SNAPSHOT"
    CARRIED_BY_RELEASE_SNAPSHOT = "CARRIED_BY_RELEASE_SNAPSHOT"
    PINNED = "PINNED"
    RIGHTS_OR_PROVENANCE_REQUIRED = "RIGHTS_OR_PROVENANCE_REQUIRED"
    SUPERSESION_SOURCE = "SUPERSESION_SOURCE"


class ExternalEffectState(Labeled):
    """What actually happened outside the repository. State here is never implied."""

    NOT_APPLIED = "NOT_APPLIED"
    APPLIED = "APPLIED"
    COMPENSATED = "COMPENSATED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    IRREVERSIBLE = "IRREVERSIBLE"

    @property
    def needs_compensation(self) -> bool:
        """Anything the outside world already observed has to be handled explicitly."""

        return self in {
            ExternalEffectState.APPLIED,
            ExternalEffectState.RECONCILIATION_REQUIRED,
            ExternalEffectState.IRREVERSIBLE,
        }

    @property
    def is_settled(self) -> bool:
        return self in {ExternalEffectState.NOT_APPLIED, ExternalEffectState.COMPENSATED}


@dataclass(frozen=True)
class SnapshotClosureManifest(Record):
    """Every answer a snapshot must give about the state it closes over.

    The manifest is deliberately wide: a closure that omits "which policies were in
    force" cannot later prove why a decision was admissible, and a snapshot is worth
    nothing as evidence if its own reasoning has to be reconstructed from memory.
    """

    project_id: str
    production_id: str
    branch_id: str
    graph: MaterializationGraph
    ancestry: tuple[str, ...] = ()
    fork_point_snapshot_id: Any = None
    parent_snapshot_ids: tuple[str, ...] = ()
    intent_ref: Any = None
    variant_sets: tuple[VariantSet, ...] = ()
    variant_constraints: tuple[VariantConstraint, ...] = ()
    variant_selection: Any = None
    identity_anchors: tuple[IdentityAnchorPolicy, ...] = ()
    quality_decisions: tuple[ExternalRef, ...] = ()
    rights_refs: tuple[ExternalRef, ...] = ()
    provenance_refs: tuple[ExternalRef, ...] = ()
    delivery_refs: tuple[ExternalRef, ...] = ()
    policy_refs: tuple[ExternalRef, ...] = ()
    environment_refs: tuple[ExternalRef, ...] = ()
    tool_refs: tuple[ExternalRef, ...] = ()
    model_refs: tuple[ExternalRef, ...] = ()
    external_admissions: tuple[ExternalRef, ...] = ()
    environment_fingerprint: Any = None
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "graph": of(MaterializationGraph),
        "intent_ref": of(ExternalRef),
        "variant_sets": of(VariantSet),
        "variant_constraints": of(VariantConstraint),
        "variant_selection": of(VariantSelection),
        "identity_anchors": of(IdentityAnchorPolicy),
        "quality_decisions": of(ExternalRef),
        "rights_refs": of(ExternalRef),
        "provenance_refs": of(ExternalRef),
        "delivery_refs": of(ExternalRef),
        "policy_refs": of(ExternalRef),
        "environment_refs": of(ExternalRef),
        "tool_refs": of(ExternalRef),
        "model_refs": of(ExternalRef),
        "external_admissions": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        for name in ("project_id", "production_id", "branch_id"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        if not isinstance(self.graph, MaterializationGraph):
            raise SchemaValidationError("graph must be a MaterializationGraph")
        revision = self.graph.revision
        if not isinstance(revision, GraphRevision):
            raise SchemaValidationError("graph must carry a GraphRevision")
        if not revision.is_intact:
            raise SnapshotClosureError(
                f"graph revision {revision.revision_id} does not carry the digest it claims"
            )
        object.__setattr__(self, "ancestry", _ids(self.ancestry, "ancestry"))
        object.__setattr__(self, "parent_snapshot_ids", _ids(self.parent_snapshot_ids, "parent_snapshot_ids"))
        if self.fork_point_snapshot_id is not None:
            object.__setattr__(self, "fork_point_snapshot_id", require_id(self.fork_point_snapshot_id, "fork_point_snapshot_id"))
        if self.intent_ref is not None and not isinstance(self.intent_ref, ExternalRef):
            raise SchemaValidationError("intent_ref must be an ExternalRef or None")
        sets = require_bounded(self.variant_sets, "variant_sets", maximum=MAX_VARIANT_SETS)
        object.__setattr__(self, "variant_sets", tuple(VariantSet.coerce(item, "variant_sets[]") for item in sets))
        constraints = require_bounded(self.variant_constraints, "variant_constraints", maximum=MAX_VARIANT_SETS)
        object.__setattr__(
            self,
            "variant_constraints",
            tuple(VariantConstraint.coerce(item, "variant_constraints[]") for item in constraints),
        )
        if self.variant_selection is not None:
            object.__setattr__(self, "variant_selection", VariantSelection.coerce(self.variant_selection, "variant_selection"))
        anchors = require_bounded(self.identity_anchors, "identity_anchors", maximum=MAX_VARIANT_SETS)
        object.__setattr__(
            self,
            "identity_anchors",
            tuple(sorted((IdentityAnchorPolicy.coerce(item, "identity_anchors[]") for item in anchors), key=lambda item: item.anchor_id)),
        )
        for name in (
            "quality_decisions",
            "rights_refs",
            "provenance_refs",
            "delivery_refs",
            "policy_refs",
            "environment_refs",
            "tool_refs",
            "model_refs",
            "external_admissions",
        ):
            object.__setattr__(self, name, _refs(getattr(self, name), name))
        if self.environment_fingerprint is not None:
            object.__setattr__(
                self, "environment_fingerprint", require_digest(self.environment_fingerprint, "environment_fingerprint")
            )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def revision(self) -> GraphRevision:
        return self.graph.revision

    @property
    def graph_id(self) -> str:
        return self.revision.graph_id

    @property
    def digest(self) -> str:
        return content_digest(self.to_payload())

    @property
    def artifact_revisions(self) -> tuple[tuple[str, str], ...]:
        """Which immutable revision fills which output port: the semantic asset map."""

        return tuple(
            sorted((record.node_id, f"{record.revision_ref.text}@{record.content_digest}") for record in self.graph.materializations)
        )

    @property
    def unresolved_dependencies(self) -> tuple[str, ...]:
        """Material the closure admits it does not yet hold, stated port by port."""

        found = [
            f"{edge.source_node_id}.{edge.source_port_id}->{edge.target_node_id}.{edge.target_port_id}"
            for edge in self.graph.unresolved_inputs()
        ]
        found.extend(f"node:{node_id}" for node_id in self.graph.unmaterialized_nodes())
        found.extend(f"external:{item.text}" for item in self.unadmitted_external_inputs)
        return tuple(sorted(found))

    @property
    def unadmitted_external_inputs(self) -> tuple[ExternalRef, ...]:
        admitted = {item.reference for item in self.external_admissions}
        return tuple(
            item
            for item in self.revision.definition.declared_external_inputs
            if item.reference not in admitted
        )

    @property
    def effective_selection(self) -> Mapping[str, str]:
        if self.variant_selection is None or not self.variant_sets:
            return {}
        from .branching import resolve_selection

        return resolve_selection(self.variant_sets, self.variant_selection)

    def selection_violations(self) -> tuple[str, ...]:
        """Why this closure may not be built at all, before any cost is paid."""

        if self.variant_selection is None or not self.variant_sets:
            return ()
        return validate_selection(self.variant_sets, self.variant_constraints, self.variant_selection)


def _materialization_obligations(closure: SnapshotClosureManifest) -> list[str]:
    found: list[str] = []
    unresolved = closure.graph.unresolved_inputs()
    if unresolved:
        found.append(
            "claims MATERIALIZED while "
            + ", ".join(sorted(f"{edge.source_node_id}.{edge.source_port_id}" for edge in unresolved))
            + " has no admitted producer"
        )
    missing = closure.graph.unmaterialized_nodes()
    if missing:
        found.append("claims MATERIALIZED while nodes " + ", ".join(missing) + " emitted nothing")
    return found


def _quality_obligations(closure: SnapshotClosureManifest) -> list[str]:
    unmaterialized = closure.graph.unmaterialized_nodes()
    if unmaterialized:
        return ["claims VALIDATED while nodes " + ", ".join(unmaterialized) + " emitted nothing"]
    found: list[str] = []
    bound = {item.text for item in closure.quality_decisions}
    unjudged = sorted(
        f"{record.node_id}.{record.port_id}"
        for record in closure.graph.materializations
        if record.producer_attempt_id is not None and (record.decision_ref is None or record.decision_ref.text not in bound)
    )
    if unjudged:
        found.append(
            "claims VALIDATED while materializations "
            + ", ".join(unjudged)
            + " carry no bound M01 QualityDecision"
        )
    if not closure.quality_decisions:
        found.append("claims VALIDATED while the closure binds no quality decision at all")
    if not closure.policy_refs:
        found.append("claims VALIDATED while the closure binds no policy or fidelity contract reference")
    return found


def _release_obligations(closure: SnapshotClosureManifest) -> list[str]:
    found: list[str] = []
    for name, label in (
        ("rights_refs", "rights"),
        ("provenance_refs", "provenance"),
        ("delivery_refs", "delivery"),
        ("environment_refs", "environment qualification"),
    ):
        if not getattr(closure, name):
            found.append(f"claims RELEASE while the closure binds no {label} reference")
    return found


def closure_obligations(
    closure: Any, snapshot_class: Any
) -> tuple[str, ...]:
    """Every reason the closure fails to support the class it is given.

    Returned rather than raised so a caller can show a reviewer the whole set of
    missing evidence at once instead of discovering it one commit attempt at a time.
    """

    wanted = SnapshotClass.parse(snapshot_class, "snapshot_class")
    resolved = SnapshotClosureManifest.coerce(closure, "closure")
    found: list[str] = []
    if resolved.selection_violations():
        found.extend(f"variant selection: {item}" for item in resolved.selection_violations())
    if resolved.unadmitted_external_inputs:
        found.append(
            "declared external inputs have no admission receipt: "
            + ", ".join(sorted(item.text for item in resolved.unadmitted_external_inputs))
        )
    if wanted.requires_materialization:
        found.extend(_materialization_obligations(resolved))
    if wanted.requires_quality_evidence:
        found.extend(_quality_obligations(resolved))
    if wanted.requires_release_evidence:
        found.extend(_release_obligations(resolved))
    return tuple(found)


@dataclass(frozen=True)
class Snapshot(Record):
    """One immutable closure, plus the completeness claim made about it."""

    snapshot_id: str
    closure: SnapshotClosureManifest
    snapshot_class: SnapshotClass = SnapshotClass.LOGICAL_SNAPSHOT
    derivation: SnapshotDerivation = SnapshotDerivation.BASELINE
    created_at_ms: int = 0
    creator: Any = None
    label: Any = None
    origin_snapshot_id: Any = None
    origin_receipt_id: Any = None
    supersedes_snapshot_ids: tuple[str, ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "closure": of(SnapshotClosureManifest),
        "creator": of(ComponentVersion),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_id", require_id(self.snapshot_id, "snapshot_id"))
        object.__setattr__(self, "closure", SnapshotClosureManifest.coerce(self.closure, "closure"))
        object.__setattr__(self, "snapshot_class", SnapshotClass.parse(self.snapshot_class, "snapshot_class"))
        object.__setattr__(self, "derivation", SnapshotDerivation.parse(self.derivation, "derivation"))
        object.__setattr__(self, "created_at_ms", require_millis(self.created_at_ms, "created_at_ms"))
        if self.creator is not None:
            object.__setattr__(self, "creator", require_component_version(self.creator, "creator"))
        object.__setattr__(self, "label", require_optional_text(self.label, "label", maximum=256))
        for name in ("origin_snapshot_id", "origin_receipt_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_id(value, name))
        object.__setattr__(self, "supersedes_snapshot_ids", _ids(self.supersedes_snapshot_ids, "supersedes_snapshot_ids"))
        if self.snapshot_id in self.parent_snapshot_ids:
            raise SnapshotClosureError(
                f"snapshot {self.snapshot_id} lists itself as a parent; snapshot history must remain acyclic"
            )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})
        blockers = closure_obligations(self.closure, self.snapshot_class)
        if blockers:
            raise SnapshotClosureError(
                f"snapshot {self.snapshot_id} claims {self.snapshot_class.value} but its closure "
                f"does not carry the evidence: " + "; ".join(blockers)
            )

    @property
    def digest(self) -> str:
        """The content identity of the closure. Two snapshots may share it and differ."""

        return self.closure.digest

    @property
    def project_id(self) -> str:
        return self.closure.project_id

    @property
    def production_id(self) -> str:
        return self.closure.production_id

    @property
    def branch_id(self) -> str:
        return self.closure.branch_id

    @property
    def graph(self) -> MaterializationGraph:
        return self.closure.graph

    @property
    def revision(self) -> GraphRevision:
        return self.closure.revision

    @property
    def parent_snapshot_ids(self) -> tuple[str, ...]:
        return self.closure.parent_snapshot_ids

    def covers(self, node_id: str) -> bool:
        return node_id in self.closure.revision.definition.node_index

    def materializations_of(self, node_id: str) -> tuple[MaterializationRecord, ...]:
        return tuple(item for item in self.closure.graph.materializations if item.node_id == node_id)

    def diff_against(self, other: Any) -> SemanticDiff:
        """Classified distance to another snapshot, base on this side."""

        return semantic_diff(self, Snapshot.coerce(other, "other"))


def commit_snapshot(
    closure: Any,
    *,
    snapshot_class: Any = SnapshotClass.LOGICAL_SNAPSHOT,
    snapshot_id: str | None = None,
    derivation: Any = SnapshotDerivation.COMMITTED,
    actor: Any = None,
    label: Any = None,
    origin_snapshot_id: Any = None,
    origin_receipt_id: Any = None,
    supersedes_snapshot_ids: Sequence[str] = (),
    created_at_ms: int = 0,
) -> Snapshot:
    """Freeze a closure into a snapshot, failing closed on an unsupported claim."""

    return Snapshot(
        snapshot_id=require_id(snapshot_id, "snapshot_id") if snapshot_id is not None else new_id(),
        closure=SnapshotClosureManifest.coerce(closure, "closure"),
        snapshot_class=SnapshotClass.parse(snapshot_class, "snapshot_class"),
        derivation=SnapshotDerivation.parse(derivation, "derivation"),
        created_at_ms=created_at_ms,
        creator=actor,
        label=label,
        origin_snapshot_id=origin_snapshot_id,
        origin_receipt_id=origin_receipt_id,
        supersedes_snapshot_ids=tuple(supersedes_snapshot_ids),
    )


def derive_snapshot(
    base: Any,
    *,
    snapshot_id: str | None = None,
    snapshot_class: Any = None,
    derivation: Any = SnapshotDerivation.COMMITTED,
    parents: Sequence[str] = (),
    actor: Any = None,
    origin_snapshot_id: Any = None,
    origin_receipt_id: Any = None,
    supersedes_snapshot_ids: Sequence[str] = (),
    created_at_ms: int = 0,
    **changes: Any,
) -> Snapshot:
    """A new snapshot from an existing closure; the base itself is never edited.

    Anything structural has to arrive as ``graph=`` or another closure change, which
    produces a new closure with a new digest. There is no path that writes into the
    snapshot that was handed in.
    """

    source = Snapshot.coerce(base, "base")
    wanted = SnapshotClass.parse(snapshot_class, "snapshot_class") if snapshot_class is not None else source.snapshot_class
    if "closure" in changes:
        raise SchemaValidationError("derive_snapshot changes closure fields directly, not the closure itself")
    manifest = source.closure
    if changes:
        manifest = replace(manifest, **changes)
    parents = tuple({source.snapshot_id, *tuple(parents)}) if parents else (source.snapshot_id,)
    manifest = replace(manifest, parent_snapshot_ids=tuple(sorted(set(parents))))
    return commit_snapshot(
        manifest,
        snapshot_class=wanted,
        snapshot_id=snapshot_id,
        derivation=derivation,
        actor=actor,
        origin_snapshot_id=origin_snapshot_id if origin_snapshot_id is not None else source.snapshot_id,
        origin_receipt_id=origin_receipt_id,
        supersedes_snapshot_ids=supersedes_snapshot_ids,
        created_at_ms=created_at_ms,
    )


class SnapshotStore:
    """Content-checked commit plus the ancestor walks every rule here needs.

    Committing is idempotent for an identical snapshot and conflicting for a
    different one under the same id: history is written once, and a second writer
    that disagrees has to be heard rather than silently overwrite the first.
    """

    def __init__(self, snapshots: Iterable[Any] = ()) -> None:
        self._items: dict[str, Snapshot] = {}
        for item in snapshots:
            self.commit(item)

    def commit(self, snapshot: Any) -> Snapshot:
        wanted = Snapshot.coerce(snapshot, "snapshot")
        existing = self._items.get(wanted.snapshot_id)
        if existing is not None:
            if existing.digest == wanted.digest and existing.snapshot_class is wanted.snapshot_class:
                return existing
            raise StoreConflictError(
                f"snapshot {wanted.snapshot_id} already exists with different content; "
                "an immutable snapshot is never rewritten, mint a new id instead"
            )
        self._items[wanted.snapshot_id] = wanted
        return wanted

    def get(self, snapshot_id: str) -> Snapshot:
        wanted = require_id(snapshot_id, "snapshot_id")
        try:
            return self._items[wanted]
        except KeyError as error:
            raise SnapshotClosureError(f"no committed snapshot {wanted}") from error

    def __contains__(self, snapshot_id: Any) -> bool:
        try:
            require_id(snapshot_id, "snapshot_id")
        except SchemaValidationError:
            return False
        return str(snapshot_id).strip().lower() in self._items

    def __len__(self) -> int:
        return len(self._items)

    @property
    def snapshot_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))

    def descendants_of(self, snapshot_id: str) -> tuple["Snapshot", ...]:
        """The committed snapshots that cite this one as a parent, oldest id first."""

        wanted = require_id(snapshot_id, "snapshot_id")
        self.get(wanted)
        return tuple(
            sorted(
                (item for item in self._items.values() if wanted in item.parent_snapshot_ids),
                key=lambda item: item.snapshot_id,
            )
        )

    def ancestors_of(self, snapshot_id: str) -> tuple[str, ...]:
        """Closure over parents, cycle-safe: a broken lineage is refused, not looped."""

        wanted = require_id(snapshot_id, "snapshot_id")
        ordered: list[str] = []
        state: dict[str, int] = {}
        frontier: list[tuple[str, bool]] = [(wanted, False)]
        while frontier:
            current, leaving = frontier.pop()
            if leaving:
                state[current] = 2
                ordered.append(current)
                continue
            mark = state.get(current, 0)
            if mark == 2:
                continue
            if mark == 1:
                raise SnapshotClosureError(
                    f"snapshot ancestry contains a cycle at {current}; immutable history must be acyclic"
                )
            snapshot = self.get(current)
            unknown = sorted(set(snapshot.parent_snapshot_ids) - set(self._items))
            if unknown:
                raise SnapshotClosureError(
                    f"snapshot {current} names parents that were never committed: {unknown}"
                )
            state[current] = 1
            frontier.append((current, True))
            for parent in reversed(snapshot.parent_snapshot_ids):
                if state.get(parent, 0) == 1:
                    raise SnapshotClosureError(
                        f"snapshot ancestry contains a cycle through {parent}; immutable history must be acyclic"
                    )
                if state.get(parent, 0) != 2:
                    frontier.append((parent, False))
        return tuple(ordered)

    def is_ancestor(self, candidate: Any, of_snapshot_id: str) -> bool:
        if candidate is None:
            return False
        wanted = require_id(candidate, "candidate")
        if wanted == require_id(of_snapshot_id, "of_snapshot_id"):
            return True
        return wanted in set(self.ancestors_of(of_snapshot_id)) - {of_snapshot_id}

    def intervening(self, *, head_snapshot_id: str, target_snapshot_id: str) -> tuple[str, ...]:
        """History between a head and an older snapshot: rollback preserves all of it."""

        head = require_id(head_snapshot_id, "head_snapshot_id")
        target = require_id(target_snapshot_id, "target_snapshot_id")
        kept = set(self.ancestors_of(target))
        return tuple(item for item in self.ancestors_of(head) if item not in kept)

    def time_travel(self, snapshot_id: str) -> "SnapshotView":
        """A read-only window onto one historical closure. Nothing here writes back."""

        return SnapshotView(self.get(snapshot_id))

    def projection_digest(self) -> str:
        """A digest over the whole store: time travel provably changes no history."""

        return content_digest([[key, self._items[key].digest] for key in sorted(self._items)])


class SnapshotView:
    """Read-only inspection of one committed snapshot: diff, provenance, closure."""

    __slots__ = ("_snapshot",)

    def __init__(self, snapshot: Snapshot) -> None:
        object.__setattr__(self, "_snapshot", snapshot)

    def __setattr__(self, name: str, value: Any) -> None:
        raise SnapshotClosureError("a historical snapshot is read-only and cannot be mutated")

    def __delattr__(self, name: str) -> None:
        raise SnapshotClosureError("a historical snapshot is read-only and cannot be mutated")

    @property
    def snapshot(self) -> Snapshot:
        return self._snapshot

    @property
    def snapshot_id(self) -> str:
        return self._snapshot.snapshot_id

    @property
    def closure(self) -> SnapshotClosureManifest:
        return self._snapshot.closure

    @property
    def snapshot_class(self) -> SnapshotClass:
        return self._snapshot.snapshot_class

    @property
    def digest(self) -> str:
        return self._snapshot.digest

    @property
    def graph(self) -> MaterializationGraph:
        return self._snapshot.graph

    def node_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._snapshot.closure.revision.definition.node_index))

    def materialization(self, node_id: str, port_id: str) -> MaterializationRecord | None:
        return self._snapshot.graph.materialization_of(node_id, port_id)

    def unresolved_dependencies(self) -> tuple[str, ...]:
        return self._snapshot.closure.unresolved_dependencies

    def diff_to(self, other: Any) -> SemanticDiff:
        return self._snapshot.diff_against(other)


@dataclass(frozen=True)
class ExternalSideEffect(Record):
    """A mutation the outside world already saw, recorded against a snapshot.

    Moving a branch ref back does not un-publish a video, un-charge a payment or
    revoke an issued right. This record exists so the kernel can say which of them
    happened after the state being restored, instead of implying they did not.
    """

    side_effect_id: str
    node_id: str
    observed_after_snapshot_id: str
    destination: ExternalRef
    attempt_id: Any = None
    kind: SideEffectClass = SideEffectClass.EXTERNAL_MUTATION
    state: ExternalEffectState = ExternalEffectState.APPLIED
    idempotency_key_ref: Any = None
    compensation_ref: Any = None
    compensation_receipt_ref: Any = None
    evidence_refs: tuple[ExternalRef, ...] = ()
    recorded_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "destination": of(ExternalRef),
        "idempotency_key_ref": of(ExternalRef),
        "compensation_ref": of(ExternalRef),
        "compensation_receipt_ref": of(ExternalRef),
        "evidence_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "side_effect_id", require_id(self.side_effect_id, "side_effect_id"))
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        if self.attempt_id is not None:
            object.__setattr__(self, "attempt_id", require_id(self.attempt_id, "attempt_id"))
        if not isinstance(self.destination, ExternalRef):
            raise SchemaValidationError("destination must be an ExternalRef to the mutated system")
        object.__setattr__(self, "kind", SideEffectClass.parse(self.kind, "kind"))
        if self.kind is not SideEffectClass.EXTERNAL_MUTATION:
            raise GraphValidationError(
                f"{self.kind.value} is inside the kernel's own storage and needs no external fence"
            )
        object.__setattr__(self, "state", ExternalEffectState.parse(self.state, "state"))
        object.__setattr__(
            self, "observed_after_snapshot_id", require_id(self.observed_after_snapshot_id, "observed_after_snapshot_id")
        )
        for name in ("idempotency_key_ref", "compensation_ref", "compensation_receipt_ref"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, ExternalRef):
                raise SchemaValidationError(f"{name} must be an ExternalRef or None")
        evidence = require_bounded(self.evidence_refs, "evidence_refs", maximum=MAX_RECEIPT_EVIDENCE)
        object.__setattr__(self, "evidence_refs", tuple(ExternalRef.coerce(item, "evidence_refs[]") for item in evidence))
        object.__setattr__(self, "recorded_at_ms", require_millis(self.recorded_at_ms, "recorded_at_ms"))
        if self.state is ExternalEffectState.COMPENSATED and self.compensation_receipt_ref is None:
            raise SideEffectFenceError(
                f"side effect {self.side_effect_id} claims COMPENSATED without a compensation receipt"
            )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def needs_compensation(self) -> bool:
        return self.state.needs_compensation and self.compensation_receipt_ref is None


class PreconditionKind(Labeled):
    """What a transplant insists the target still looks like before it applies."""

    UNCHANGED_CONTENT = "UNCHANGED_CONTENT"
    UNCHANGED_DEFINITION = "UNCHANGED_DEFINITION"
    ABSENT_NODE = "ABSENT_NODE"
    PRESENT_NODE = "PRESENT_NODE"
    MATCHING_VARIANT = "MATCHING_VARIANT"


@dataclass(frozen=True)
class DeltaPrecondition(Record):
    """One dependency precondition of a bounded transplant."""

    subject: str
    kind: PreconditionKind
    expected: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject", require_text(self.subject, "subject", maximum=512))
        object.__setattr__(self, "kind", PreconditionKind.parse(self.kind, "kind"))
        if self.expected is not None:
            object.__setattr__(self, "expected", require_text(self.expected, "expected", maximum=512))

    @property
    def text(self) -> str:
        return f"{self.kind.value}:{self.subject}={self.expected or ''}"


@dataclass(frozen=True)
class ProductionDelta(Record):
    """A versioned, bounded transplant of an admitted change between snapshots.

    This is the kernel's answer to "bring that one rig fix into the other branch"
    without merging a whole line of history. The delta is a record with preconditions
    and a scope, never an untracked copy of bytes somebody made in a hurry.
    """

    delta_id: str
    source_snapshot_id: str
    target_snapshot_id: str
    merge_base_snapshot_id: str
    scope: tuple[Any, ...] = ()
    included_node_ids: tuple[str, ...] = ()
    excluded_node_ids: tuple[str, ...] = ()
    preconditions: tuple[DeltaPrecondition, ...] = ()
    reason: Any = None
    actor: Any = None
    created_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    NESTED = {"preconditions": of(DeltaPrecondition), "actor": of(ComponentVersion)}

    def __post_init__(self) -> None:
        from .diffing import DiffCategory

        object.__setattr__(self, "delta_id", require_id(self.delta_id, "delta_id"))
        for name in ("source_snapshot_id", "target_snapshot_id", "merge_base_snapshot_id"):
            object.__setattr__(self, name, require_id(getattr(self, name), name))
        collected = require_bounded(self.scope, "scope", maximum=len(DiffCategory), kind="category")
        object.__setattr__(
            self, "scope", tuple(sorted({DiffCategory.parse(item, "scope[]") for item in collected}, key=lambda item: item.value))
        )
        for name in ("included_node_ids", "excluded_node_ids"):
            values = require_bounded(getattr(self, name), name, maximum=MAX_SNAPSHOT_NODES, kind="node id")
            object.__setattr__(self, name, tuple(sorted({require_identifier(item, f"{name}[]") for item in values})))
        overlap = sorted(set(self.included_node_ids) & set(self.excluded_node_ids))
        if overlap:
            raise GraphValidationError(f"a delta cannot both carry and exclude {overlap}")
        preconditions = require_bounded(self.preconditions, "preconditions", maximum=MAX_SNAPSHOT_NODES)
        object.__setattr__(
            self,
            "preconditions",
            tuple(sorted((DeltaPrecondition.coerce(item, "preconditions[]") for item in preconditions), key=lambda item: item.text)),
        )
        object.__setattr__(self, "reason", require_optional_text(self.reason, "reason", maximum=512))
        if self.actor is not None:
            object.__setattr__(self, "actor", require_component_version(self.actor, "actor"))
        object.__setattr__(self, "created_at_ms", require_millis(self.created_at_ms, "created_at_ms"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def text(self) -> str:
        return content_digest(self.to_payload())

    def precondition_failures(self, target: Any) -> tuple[str, ...]:
        """Reasons the target is no longer the state this delta was written against."""

        snapshot = Snapshot.coerce(target, "target")
        index = snapshot.closure.revision.definition.node_index
        selection = dict(snapshot.closure.effective_selection)
        found: list[str] = []
        for item in self.preconditions:
            if item.kind is PreconditionKind.ABSENT_NODE and item.subject in index:
                found.append(f"{item.text} but the target already carries node {item.subject}")
            elif item.kind is PreconditionKind.PRESENT_NODE and item.subject not in index:
                found.append(f"{item.text} but the target has no node {item.subject}")
            elif item.kind is PreconditionKind.MATCHING_VARIANT:
                if selection.get(item.subject) != item.expected:
                    found.append(
                        f"{item.text} but the target selects {selection.get(item.subject)} for {item.subject}"
                    )
            elif item.kind in {PreconditionKind.UNCHANGED_CONTENT, PreconditionKind.UNCHANGED_DEFINITION}:
                if item.subject not in index:
                    found.append(f"{item.text} but the target has no node {item.subject}")
                    continue
                records = snapshot.graph.materialization_of_first(item.subject)
                if item.kind is PreconditionKind.UNCHANGED_CONTENT and records is not None:
                    if records.content_digest != item.expected:
                        found.append(
                            f"{item.text} but the target holds {records.content_digest} at {item.subject}"
                        )
        return tuple(found)


@dataclass(frozen=True)
class RollbackPlan(Record):
    """Steps 1 to 4 of a rollback: what would change, and what the world already saw."""

    plan_id: str
    branch_id: str
    from_snapshot_id: str
    to_snapshot_id: str
    diff: SemanticDiff
    affected_node_ids: tuple[str, ...] = ()
    intervening_snapshot_ids: tuple[str, ...] = ()
    side_effects: tuple[ExternalSideEffect, ...] = ()
    blockers: tuple[str, ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {"diff": of(SemanticDiff), "side_effects": of(ExternalSideEffect)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", require_id(self.plan_id, "plan_id"))
        object.__setattr__(self, "branch_id", require_identifier(self.branch_id, "branch_id"))
        for name in ("from_snapshot_id", "to_snapshot_id"):
            object.__setattr__(self, name, require_id(getattr(self, name), name))
        object.__setattr__(self, "diff", SemanticDiff.coerce(self.diff, "diff"))
        nodes = require_bounded(self.affected_node_ids, "affected_node_ids", maximum=MAX_SNAPSHOT_NODES, kind="node id")
        object.__setattr__(self, "affected_node_ids", tuple(sorted({require_identifier(item, "affected_node_ids[]") for item in nodes})))
        object.__setattr__(self, "intervening_snapshot_ids", _ids(self.intervening_snapshot_ids, "intervening_snapshot_ids"))
        effects = require_bounded(self.side_effects, "side_effects", maximum=MAX_CLOSURE_REFS)
        object.__setattr__(
            self,
            "side_effects",
            tuple(sorted((ExternalSideEffect.coerce(item, "side_effects[]") for item in effects), key=lambda item: item.side_effect_id)),
        )
        object.__setattr__(
            self,
            "blockers",
            tuple(require_text(item, "blockers[]", maximum=1024) for item in self.blockers),
        )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def is_cleared(self) -> bool:
        return not self.blockers

    @property
    def pending_side_effects(self) -> tuple[ExternalSideEffect, ...]:
        return tuple(item for item in self.side_effects if item.needs_compensation)

    def compensation_digest(self) -> str:
        return content_digest([item.side_effect_id for item in self.pending_side_effects])


@dataclass(frozen=True)
class RollbackReceipt(Record):
    """Proof that a rollback created new history rather than deleting the old."""

    rollback_id: str
    branch_id: str
    from_snapshot_id: str
    to_snapshot_id: str
    created_snapshot_id: str
    diff: SemanticDiff
    preserved_snapshot_ids: tuple[str, ...] = ()
    side_effects: tuple[ExternalSideEffect, ...] = ()
    compensation_refs: tuple[ExternalRef, ...] = ()
    actor: Any = None
    recorded_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "diff": of(SemanticDiff),
        "side_effects": of(ExternalSideEffect),
        "compensation_refs": of(ExternalRef),
        "actor": of(ComponentVersion),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "rollback_id", require_id(self.rollback_id, "rollback_id"))
        object.__setattr__(self, "branch_id", require_identifier(self.branch_id, "branch_id"))
        for name in ("from_snapshot_id", "to_snapshot_id", "created_snapshot_id"):
            object.__setattr__(self, name, require_id(getattr(self, name), name))
        object.__setattr__(self, "diff", SemanticDiff.coerce(self.diff, "diff"))
        object.__setattr__(self, "preserved_snapshot_ids", _ids(self.preserved_snapshot_ids, "preserved_snapshot_ids"))
        effects = require_bounded(self.side_effects, "side_effects", maximum=MAX_CLOSURE_REFS)
        object.__setattr__(
            self,
            "side_effects",
            tuple(sorted((ExternalSideEffect.coerce(item, "side_effects[]") for item in effects), key=lambda item: item.side_effect_id)),
        )
        object.__setattr__(self, "compensation_refs", _refs(self.compensation_refs, "compensation_refs"))
        if self.actor is not None:
            object.__setattr__(self, "actor", require_component_version(self.actor, "actor"))
        object.__setattr__(self, "recorded_at_ms", require_millis(self.recorded_at_ms, "recorded_at_ms"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})


def plan_rollback(
    store: SnapshotStore,
    ledger: BranchLedger,
    *,
    branch_id: str,
    to_snapshot_id: str,
    side_effects: Iterable[Any] = (),
    plan_id: str | None = None,
) -> RollbackPlan:
    """Rollback steps 1 to 4: select, verify reachability, diff, and count side effects.

    Nothing is written here. A caller sees the whole consequence, including the parts
    of it that already escaped into the outside world, before any ref moves.
    """

    reference = ledger.ref(branch_id)
    target = store.get(to_snapshot_id)
    current = store.get(reference.head_snapshot_id)
    if target.digest == current.digest and target.snapshot_class is current.snapshot_class:
        raise SnapshotClosureError(
            f"branch {reference.branch_id} already points at snapshot {target.snapshot_id}; "
            "a rollback to the current state is not a change worth recording"
        )
    reachable = store.is_ancestor(target.snapshot_id, of_snapshot_id=current.snapshot_id)
    if not reachable:
        raise SnapshotClosureError(
            f"snapshot {target.snapshot_id} is not reachable from the head of branch {reference.branch_id}; "
            "rolling back onto another line's history is a merge or a fork, never a rollback"
        )
    diff = current.diff_against(target)
    intervening = store.intervening(head_snapshot_id=current.snapshot_id, target_snapshot_id=target.snapshot_id)
    kept = set(intervening)
    recorded = tuple(ExternalSideEffect.coerce(item, "side_effects[]") for item in side_effects)
    uncommitted = sorted(
        {
            item.observed_after_snapshot_id
            for item in recorded
            if item.observed_after_snapshot_id not in set(store.snapshot_ids)
        }
    )
    if uncommitted:
        raise SnapshotClosureError(
            "a side effect is dated against snapshots that were never committed: " + ", ".join(uncommitted)
        )
    caught = tuple(item for item in recorded if item.observed_after_snapshot_id in kept)
    blockers: list[str] = [
        f"external mutation {item.side_effect_id} at node {item.node_id} toward "
        f"{item.destination.text} is {item.state.value} after the rollback target and carries no "
        "compensation receipt; moving a ref back does not undo the outside world"
        for item in caught
        if item.needs_compensation
    ]
    blocking = diff.blocking
    if blocking:
        blockers.append(
            "the rollback carries blocking semantic differences that need review before the head moves: "
            + ", ".join(sorted(item.text for item in blocking)[:8])
        )
    return RollbackPlan(
        plan_id=require_id(plan_id, "plan_id") if plan_id is not None else new_id(),
        branch_id=reference.branch_id,
        from_snapshot_id=current.snapshot_id,
        to_snapshot_id=target.snapshot_id,
        diff=diff,
        affected_node_ids=diff.affected_nodes,
        intervening_snapshot_ids=intervening,
        side_effects=caught,
        blockers=tuple(blockers),
    )


def execute_rollback(
    store: SnapshotStore,
    ledger: BranchLedger,
    plan: Any,
    *,
    actor: Any,
    compensation_refs: Iterable[Any] = (),
    acknowledge_blocking_diff: bool = False,
    created_snapshot_id: str | None = None,
    now_ms: int = 0,
) -> tuple[Snapshot, RollbackReceipt, TransitionReceipt]:
    """Rollback steps 5 and 6: write the new snapshot and receipt, then move the ref.

    The new head is derived from the target closure but is a fresh snapshot with both
    the old head and the target as parents, so the intervening history stays reachable.

    Two fences are enforced here and neither is negotiable by review alone: an
    outstanding external mutation needs its own compensation procedure, and a blocking
    semantic difference needs an explicit acknowledgement rather than a silent override.
    """

    wanted = RollbackPlan.coerce(plan, "plan")
    compensated = _refs(compensation_refs, "compensation_refs")
    outstanding = wanted.pending_side_effects
    if outstanding and not compensated:
        raise SideEffectFenceError(
            "rollback is fenced by external mutations that need explicit compensation procedures: "
            + ", ".join(sorted(item.side_effect_id for item in outstanding))
        )
    if compensated and len(compensated) < len(outstanding):
        raise SideEffectFenceError(
            f"rollback names {len(compensated)} compensation reference(s) for {len(outstanding)} "
            "outstanding external mutation(s); every one needs its own procedure"
        )
    if wanted.diff.blocking and not acknowledge_blocking_diff:
        raise RollbackBlockedError(
            f"rollback of branch {wanted.branch_id} is blocked by "
            f"{len(wanted.diff.blocking)} blocking semantic difference(s); acknowledge them explicitly "
            "once the review has been recorded"
        )

    target = store.get(wanted.to_snapshot_id)
    snapshot = derive_snapshot(
        target,
        snapshot_id=created_snapshot_id,
        snapshot_class=target.snapshot_class,
        derivation=SnapshotDerivation.ROLLED_BACK,
        parents=(wanted.from_snapshot_id, wanted.to_snapshot_id),
        actor=actor,
        origin_snapshot_id=target.snapshot_id,
        supersedes_snapshot_ids=(wanted.from_snapshot_id,),
        created_at_ms=now_ms,
        branch_id=wanted.branch_id,
    )
    store.commit(snapshot)
    receipt = RollbackReceipt(
        rollback_id=wanted.plan_id,
        branch_id=wanted.branch_id,
        from_snapshot_id=wanted.from_snapshot_id,
        to_snapshot_id=wanted.to_snapshot_id,
        created_snapshot_id=snapshot.snapshot_id,
        diff=wanted.diff,
        preserved_snapshot_ids=wanted.intervening_snapshot_ids,
        side_effects=wanted.side_effects,
        compensation_refs=compensated,
        actor=actor,
        recorded_at_ms=now_ms,
    )
    _, transition = ledger.advance(
        wanted.branch_id,
        snapshot.snapshot_id,
        actor=actor,
        reason_code="rollback",
        expected_head_snapshot_id=wanted.from_snapshot_id,
        evidence_refs=tuple(
            sorted(
                {
                    *[ExternalRef(kind=EntityKind.SNAPSHOT, reference=item) for item in wanted.intervening_snapshot_ids],
                    *[item.compensation_receipt_ref for item in wanted.side_effects if item.compensation_receipt_ref],
                    *compensated,
                },
                key=lambda item: item.text,
            )
        ),
        now_ms=now_ms,
    )
    return snapshot, receipt, transition


def retention_reasons(
    store: SnapshotStore,
    snapshot_id: str,
    *,
    live_heads: Iterable[str] = (),
    pins: Iterable[Any] = (),
    now_ms: int = 0,
) -> tuple[RetentionReason, ...]:
    """Why a snapshot must survive cleanup, computed from the claims that hold.

    Rights and provenance keep material alive on their own: a deleted byte is a
    legal problem long after the branch that produced it stopped being interesting.
    """

    wanted = require_id(snapshot_id, "snapshot_id")
    snapshot = store.get(wanted)
    found: set[RetentionReason] = set()
    for head in live_heads:
        if store.is_ancestor(wanted, of_snapshot_id=require_id(head, "live_heads[]")):
            found.add(RetentionReason.REACHABLE_FROM_LIVE_BRANCH)
            break
    for other in store.snapshot_ids:
        if other == wanted or not store.is_ancestor(wanted, of_snapshot_id=other):
            continue
        claim = store.get(other).snapshot_class
        if claim is SnapshotClass.RELEASE_SNAPSHOT:
            found.add(RetentionReason.CARRIED_BY_RELEASE_SNAPSHOT)
        elif claim is SnapshotClass.VALIDATED_SNAPSHOT:
            found.add(RetentionReason.CARRIED_BY_VALIDATED_SNAPSHOT)
    for item in pins:
        pin = _pin_coerce(item)
        if pin is None:
            continue
        if not pin.is_live(now_ms) and pin.may_release(now_ms):
            continue
        if any(pin.covers(reference) for reference in _pinnable_refs(snapshot)):
            found.add(RetentionReason.PINNED)
    if snapshot.closure.rights_refs or snapshot.closure.provenance_refs:
        found.add(RetentionReason.RIGHTS_OR_PROVENANCE_REQUIRED)
    if snapshot.supersedes_snapshot_ids:
        found.add(RetentionReason.SUPERSESION_SOURCE)
    return tuple(sorted(found, key=lambda item: item.value))


def _pinnable_refs(snapshot: Snapshot) -> tuple[ExternalRef, ...]:
    """The two ways a pin may name a snapshot: by identity, or by the closure it holds."""

    return (
        ExternalRef(kind=EntityKind.SNAPSHOT, reference=snapshot.snapshot_id),
        ExternalRef(kind=EntityKind.SNAPSHOT, reference=snapshot.snapshot_id, content_digest=snapshot.digest),
    )


def _pin_coerce(value: Any) -> Any:
    from .branching import RetentionPin

    try:
        return RetentionPin.coerce(value, "pin")
    except SchemaValidationError:
        return None


def collectable_snapshots(
    store: SnapshotStore,
    *,
    live_heads: Iterable[str] = (),
    pins: Iterable[Any] = (),
    now_ms: int = 0,
) -> tuple[str, ...]:
    """Snapshots with no retention claim at all. M02 decides; M06 and M55 execute."""

    return tuple(
        sorted(
            item
            for item in store.snapshot_ids
            if not retention_reasons(store, item, live_heads=live_heads, pins=pins, now_ms=now_ms)
        )
    )
