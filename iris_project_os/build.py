"""M02 area D (build): states, deltas, frontiers and the incremental plan.

A planner is where an incremental build becomes honest or dishonest. The same
inputs either produce "this node must work, and here is the change that says so",
or they produce a quiet assumption that unchanged bytes mean unchanged truth. This
module keeps the first shape and refuses the second:

* every node ends in a named ``BuildState``, and ``UNKNOWN`` is a real state that
  fails closed into ``BLOCK`` rather than being read as ``CLEAN``;
* a ``BuildDelta`` records causes, not conclusions, so the frontier can be re-derived;
* every ``BuildStep`` carries the reasons that selected its disposition, and a step
  with no reason is refused at construction;
* a ``REUSE`` step is only representable with an admitted ``ReuseReceipt`` behind it,
  and never while something it consumes is scheduled to emit new bytes.

The result is a plan that can be argued with node by node, which is what the
incremental truth oracle needs in order to prove an incremental run was no less
correct than the admitted full build.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .analysis import CausalFingerprint, Change, ImpactCone, compute_fingerprint, impact_of
from .base import Labeled, Record, of
from .diffing import DiffCategory, DiffEntry, SemanticDiff
from .errors import BuildError, SchemaValidationError
from .graph import (
    DependencyFacet,
    DependencySlice,
    GraphNode,
    MaterializationGraph,
    NodeRole,
    ReproducibilityClass,
)
from .identity import EntityKind, ExternalRef, new_id, require_id
from .limits import (
    MAX_BUILD_PLAN_STEPS,
    MAX_DIRTY_NODES,
    MAX_EVENTS,
    MAX_EXPLAIN_STEPS,
    MAX_FACETS,
    MAX_PORTS,
    MAX_REPAIR_TARGETS,
    MAX_SLICES_PER_NODE,
    MAX_VARIANT_SELECTIONS,
    MAX_VARIANT_SETS,
)
from .machines import topological_order
from .reuse import (
    CacheEntry,
    CacheKey,
    CacheLayer,
    CacheTrust,
    ContextFingerprint,
    ReuseReceipt,
    ReuseRejection,
    ReuseRequest,
    admit_reuse,
)
from .versions import (
    CONTRACT_VERSION,
    content_digest,
    require_bounded,
    require_digest,
    require_identifier,
    require_millis,
    require_optional_text,
    require_supported_version,
    require_text,
)

__all__ = [
    "BuildDelta",
    "BuildExplainTrace",
    "BuildJournal",
    "BuildPlan",
    "BuildState",
    "BuildStep",
    "CacheLookup",
    "CoalescedBatch",
    "DirtyFrontier",
    "DirtyNode",
    "IncrementalVerdict",
    "JournalEvent",
    "JournalKind",
    "NodeComparison",
    "OutputCommitMode",
    "RecoveryClass",
    "RecoveryVerdict",
    "RepairFrontier",
    "RepairTarget",
    "ShadowAudit",
    "ShadowResult",
    "SharedWork",
    "VariantCandidate",
    "WorkDisposition",
    "admit_reuse",
    "closure_of",
    "audit_shadow_rebuilds",
    "coalesce_variants",
    "compile_build_delta",
    "dirty_frontier",
    "explain_build",
    "plan_build",
    "repair_frontier",
    "verify_incremental",
]


class BuildState(Labeled):
    """What is known about one node's output right now. Seven states, no implicit eighth.

    ``UNKNOWN`` is not "probably fine". The module spec requires it to fail closed, so
    a node whose truth cannot be established is planned as blocked work, never as a hit.
    """

    UNKNOWN = "UNKNOWN"
    CLEAN = "CLEAN"
    DIRTY = "DIRTY"
    CACHED_ELIGIBLE = "CACHED_ELIGIBLE"
    REVALIDATE_ONLY = "REVALIDATE_ONLY"
    REPACKAGE_ONLY = "REPACKAGE_ONLY"
    BLOCKED = "BLOCKED"

    @property
    def fails_closed(self) -> bool:
        """No disposition but ``BLOCK`` may be chosen from here."""

        return self in {BuildState.UNKNOWN, BuildState.BLOCKED}

    @property
    def claims_current(self) -> bool:
        """Whether the node's stored bytes are already the answer, work-wise."""

        return self in {BuildState.CLEAN, BuildState.CACHED_ELIGIBLE}

    @property
    def emits_new_bytes(self) -> bool:
        return self is BuildState.DIRTY

    @property
    def needs_work(self) -> bool:
        return self in {
            BuildState.DIRTY,
            BuildState.REVALIDATE_ONLY,
            BuildState.REPACKAGE_ONLY,
        }

    @property
    def legal_dispositions(self) -> tuple[WorkDisposition, ...]:
        return _STATE_DISPOSITIONS[self]

    def admits(self, disposition: Any) -> bool:
        return WorkDisposition.parse(disposition, "disposition") in self.legal_dispositions


class WorkDisposition(Labeled):
    """The six first-class answers to "what does this node do now?".

    ``REVALIDATE`` and ``REPACKAGE`` exist so a change of evidence or of delivery
    policy is not silently promoted into a re-render, and ``BLOCK`` exists so a node
    the kernel cannot speak about is reported instead of skipped.
    """

    REBUILD = "REBUILD"
    REPAIR = "REPAIR"
    REVALIDATE = "REVALIDATE"
    REPACKAGE = "REPACKAGE"
    REUSE = "REUSE"
    BLOCK = "BLOCK"

    @property
    def is_work(self) -> bool:
        return self is not WorkDisposition.REUSE

    @property
    def avoids_work(self) -> bool:
        return self is WorkDisposition.REUSE

    @property
    def emits_new_bytes(self) -> bool:
        """Whether the node's own material outputs are rewritten by this step."""

        return self in {
            WorkDisposition.REBUILD,
            WorkDisposition.REPAIR,
            WorkDisposition.REPACKAGE,
        }

    @property
    def requires_receipt(self) -> bool:
        """A disposition that claims existing bytes stands or falls on admission evidence."""

        return self is WorkDisposition.REUSE

    @property
    def requires_slice(self) -> bool:
        return self is WorkDisposition.REPAIR

    @property
    def may_proceed(self) -> bool:
        return self is not WorkDisposition.BLOCK


_STATE_DISPOSITIONS: Mapping[BuildState, tuple[WorkDisposition, ...]] = {
    BuildState.UNKNOWN: (WorkDisposition.BLOCK,),
    BuildState.BLOCKED: (WorkDisposition.BLOCK,),
    BuildState.CLEAN: (WorkDisposition.REUSE,),
    BuildState.DIRTY: (
        WorkDisposition.REBUILD,
        WorkDisposition.REPAIR,
        WorkDisposition.REUSE,
        WorkDisposition.BLOCK,
    ),
    BuildState.CACHED_ELIGIBLE: (WorkDisposition.REUSE, WorkDisposition.REBUILD),
    BuildState.REVALIDATE_ONLY: (WorkDisposition.REVALIDATE, WorkDisposition.BLOCK),
    BuildState.REPACKAGE_ONLY: (WorkDisposition.REPACKAGE, WorkDisposition.BLOCK),
}

# Facets that re-attest evidence rather than re-render bytes.
_REVALIDATING_FACETS = frozenset(
    {DependencyFacet.QUALITY, DependencyFacet.RIGHTS, DependencyFacet.PROVENANCE}
)
_REPACKAGING_FACETS = frozenset({DependencyFacet.DELIVERY})
# What each kind of semantic movement actually invalidates.
_CATEGORY_FACETS: Mapping[DiffCategory, tuple[DependencyFacet, ...]] = {
    DiffCategory.GRAPH_TOPOLOGY: (DependencyFacet.SEMANTICS,),
    DiffCategory.NODE_DEFINITION: (DependencyFacet.SEMANTICS,),
    DiffCategory.DEPENDENCY_FACET: (DependencyFacet.CONTENT,),
    DiffCategory.VARIANT_SELECTION: (DependencyFacet.SEMANTICS,),
    DiffCategory.INTENT_BRIEF: (DependencyFacet.POLICY,),
    DiffCategory.ASSET_REVISION: (DependencyFacet.CONTENT,),
    DiffCategory.QUALITY_DECISION: (DependencyFacet.QUALITY,),
    DiffCategory.RIGHTS_PROVENANCE: (DependencyFacet.RIGHTS, DependencyFacet.PROVENANCE),
    DiffCategory.DELIVERY_POLICY: (DependencyFacet.DELIVERY,),
    DiffCategory.ENVIRONMENT_QUALIFICATION: (DependencyFacet.ENVIRONMENT,),
}


@dataclass(frozen=True)
class OutputCommitMode(Labeled):
    """Whether a multi-output node commits as one set or port by port.

    A crash must not expose a half-written output set as a valid cache hit, so the
    mode is part of the step and the journal enforces it, instead of being an
    execution detail the planner never sees.
    """

    ATOMIC = "ATOMIC"
    PARTIAL = "PARTIAL"


@dataclass(frozen=True)
class BuildDelta(Record):
    """The stated causes of a build, before anyone decides what they mean.

    A delta holds ``Change`` records, the same currency the impact cone is computed
    from. That is deliberate: the planner's conclusions must be re-derivable from its
    premises, so a plan can always be re-explained from this record alone.
    """

    graph_id: str
    base_revision: ExternalRef
    target_revision: ExternalRef
    changes: tuple[Change, ...] = ()
    categories: tuple[DiffCategory, ...] = ()
    origin: Any = None
    contract_version: str = CONTRACT_VERSION

    NESTED = {"changes": of(Change)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        for name in ("base_revision", "target_revision"):
            object.__setattr__(self, name, _revision(getattr(self, name), name))
        if self.base_revision.text == self.target_revision.text:
            raise BuildError(
                "a build delta from a revision to itself states no change; compare two revisions"
            )
        collected = require_bounded(self.changes, "changes", maximum=MAX_DIRTY_NODES)
        resolved = tuple(Change.coerce(item, "changes[]") for item in collected)
        slots = [_slot(item) for item in resolved]
        doubled = sorted({item for item in slots if slots.count(item) > 1})
        if doubled:
            raise BuildError(
                "a build delta states one cause per (node, port, facet); repeated: "
                + ", ".join("/".join(item or "-" for item in name) for name in doubled[:8])
            )
        object.__setattr__(
            self, "changes", tuple(sorted(resolved, key=lambda item: _slot(item)))
        )
        named = require_bounded(self.categories, "categories", maximum=len(DiffCategory))
        object.__setattr__(
            self,
            "categories",
            tuple(
                sorted(
                    {DiffCategory.parse(item, "categories[]") for item in named},
                    key=lambda item: item.value,
                )
            ),
        )
        if self.origin is not None:
            object.__setattr__(self, "origin", ExternalRef.coerce(self.origin, "origin"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def is_empty(self) -> bool:
        return not self.changes

    @property
    def roots(self) -> tuple[str, ...]:
        return tuple(sorted({item.node_id for item in self.changes}))

    @property
    def facets(self) -> tuple[DependencyFacet, ...]:
        return tuple(sorted({item.facet for item in self.changes}, key=lambda item: item.value))

    @property
    def delta_digest(self) -> str:
        """Identity of the causes, independent of which revisions they were stated on."""

        return content_digest([_slot(item) for item in self.changes])

    def changes_at(self, node_id: str) -> tuple[Change, ...]:
        wanted = require_identifier(node_id, "node_id")
        return tuple(item for item in self.changes if item.node_id == wanted)

    def changes_in(self, facet: Any) -> tuple[Change, ...]:
        wanted = DependencyFacet.parse(facet, "facet")
        return tuple(item for item in self.changes if item.facet is wanted)

    def __bool__(self) -> bool:
        return not self.is_empty


def _slot(change: Change) -> tuple[str, str, str]:
    return (change.node_id, change.port_id or "", change.facet.value)


def _revision(value: Any, field_name: str) -> ExternalRef:
    ref = ExternalRef.coerce(value, field_name)
    if ref.kind is not EntityKind.REVISION:
        raise SchemaValidationError(f"{field_name} must reference a REVISION, got {ref.kind.value}")
    return ref


def compile_build_delta(
    diff: SemanticDiff,
    *,
    graph_id: str,
    base_revision: ExternalRef,
    target_revision: ExternalRef,
    known_nodes: Iterable[str] = (),
) -> BuildDelta:
    """Turn a semantic diff into causes, mapping each category onto the facets it moves.

    The mapping is the interesting part and it is deliberately narrow: a delivery
    policy change is not a content change, and a quality decision is not a re-render.
    Compiling every category to ``CONTENT`` would be the cheapest way to make an
    incremental build correct-by-accident and unusably slow in production.
    """

    if not isinstance(diff, SemanticDiff):
        raise SchemaValidationError("compile_build_delta requires a SemanticDiff")
    declared = tuple(sorted({require_identifier(item, "known_nodes[]") for item in known_nodes}))
    changes: list[Change] = []
    categories: list[DiffCategory] = []
    for entry in diff.entries:
        wanted = entry.category
        facets = _CATEGORY_FACETS.get(wanted)
        if facets is None:
            raise BuildError(f"{wanted.value} carries no build meaning: the diff is not a build cause")
        if wanted is DiffCategory.DEPENDENCY_FACET and entry.facet is not None:
            facets = (DependencyFacet.parse(entry.facet, "facet"),)
        categories.append(wanted)
        subjects = entry.node_ids or ()
        if not subjects:
            # A cause that cannot be attributed to a node invalidates every node: that
            # is what an unaddressed topology change means, and it must not be dropped.
            if not declared:
                raise BuildError(
                    f"diff entry {entry.text} names no node and no declared nodes were supplied, so "
                    "the change it implies cannot be attributed; pass known_nodes to compile it as a "
                    "whole-graph invalidation"
                )
            subjects = declared
            for node_id in subjects:
                for facet in facets:
                    _add_change(changes, node_id, facet, entry, port_id=None)
            continue
        node, port = _address(entry, subjects)
        for facet in facets:
            _add_change(changes, node, facet, entry, port_id=port)
    return BuildDelta(
        graph_id=graph_id,
        base_revision=base_revision,
        target_revision=target_revision,
        changes=tuple(changes),
        categories=tuple(categories),
        origin=ExternalRef(kind=EntityKind.DELTA, reference=diff.digest(), version=diff.contract_version),
    )


def _address(entry: DiffEntry, subjects: tuple[str, ...]) -> tuple[str, str | None]:
    """Which (node, port) a diff entry addresses, read from its own subject.

    A materialization subject is ``node.port``; a tool subject is ``node:tool:ref``.
    Only the first addresses a port, and guessing otherwise would attach a change to
    a port that never moved.
    """

    if len(subjects) > 1:
        return subjects[0], None
    node = subjects[0]
    prefix = f"{node}."
    if entry.subject.startswith(prefix):
        tail = entry.subject[len(prefix) :]
        if "." not in tail and ":" not in tail:
            return node, require_identifier(tail, "subject.port")
    return node, None


def _add_change(
    changes: list[Change],
    node_id: str,
    facet: DependencyFacet,
    entry: DiffEntry,
    *,
    port_id: str | None,
) -> None:
    """Append one cause, carrying the digests the diff actually reported."""

    candidate = Change(
        node_id=require_identifier(node_id, "node_ids[]"),
        facet=facet,
        port_id=port_id,
        previous_digest=_digest_side(entry.before),
        current_digest=_digest_side(entry.after),
    )
    for existing in changes:
        if _slot(existing) == _slot(candidate) and existing.previous_digest != candidate.previous_digest:
            raise BuildError(
                f"{candidate.node_id} is stated twice with different previous bytes "
                f"({existing.previous_digest} and {candidate.previous_digest})"
            )
    if any(_slot(existing) == _slot(candidate) for existing in changes):
        return
    changes.append(candidate)


def _digest_side(value: Any) -> str | None:
    """Keep a diff's bytes claim only when it really is a digest.

    Most diff sides hold text (a class name, a reference); turning those into a
    ``Change`` digest would invent a bytes comparison the diff never made.
    """

    if isinstance(value, str) and len(value) == 64:
        try:
            return require_digest(value, "before")
        except SchemaValidationError:
            return None
    return None


@dataclass(frozen=True)
class DirtyNode(Record):
    """One node that must run, with the causes that put it in the frontier.

    ``slices`` carries the bounded part of the node each stated change touched. It is
    what lets a repair frontier answer a cause without inventing a whole-node claim,
    and its absence on a downstream node is what makes that node rebuild.
    """

    node_id: str
    facets: tuple[DependencyFacet, ...] = ()
    reasons: tuple[str, ...] = ()
    roots: tuple[str, ...] = ()
    depth: int = 0
    port_ids: tuple[str, ...] = ()
    slices: tuple[DependencySlice, ...] = ()
    state: BuildState = BuildState.DIRTY
    conditional: bool = False

    NESTED = {"slices": of(DependencySlice)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        collected = require_bounded(self.facets, "facets", maximum=MAX_FACETS)
        object.__setattr__(
            self, "facets", tuple(sorted({DependencyFacet.parse(i, "facets[]") for i in collected}, key=lambda i: i.value))
        )
        stated = require_bounded(self.reasons, "reasons", maximum=MAX_FACETS)
        object.__setattr__(
            self,
            "reasons",
            tuple(sorted({require_text(i, "reasons[]", maximum=512) for i in stated})),
        )
        if not self.reasons:
            raise BuildError(
                f"{self.node_id} entered the dirty frontier with no stated cause; a frontier nobody can "
                "explain is an assumption that the cache is right"
            )
        roots = require_bounded(self.roots, "roots", maximum=MAX_FACETS)
        object.__setattr__(self, "roots", tuple(sorted({require_identifier(i, "roots[]") for i in roots})))
        ports = require_bounded(self.port_ids, "port_ids", maximum=MAX_PORTS)
        object.__setattr__(self, "port_ids", tuple(sorted({require_identifier(i, "port_ids[]") for i in ports})))
        sliced = require_bounded(self.slices, "slices", maximum=MAX_SLICES_PER_NODE, kind="slice")
        object.__setattr__(
            self,
            "slices",
            tuple(sorted({DependencySlice.coerce(item, "slices[]") for item in sliced}, key=lambda item: item.text)),
        )
        object.__setattr__(self, "state", BuildState.parse(self.state, "state"))
        if isinstance(self.depth, bool) or not isinstance(self.depth, int) or self.depth < 0:
            raise SchemaValidationError("depth must be a non-negative integer")
        if not isinstance(self.conditional, bool):
            raise SchemaValidationError("conditional must be a boolean")

    @property
    def text(self) -> str:
        bounded = f" within {', '.join(item.text for item in self.slices)}" if self.slices else ""
        return (
            f"{self.node_id} ({', '.join(item.value for item in self.facets)}){bounded} "
            f"after {self.depth} hop(s): " + "; ".join(self.reasons)
        )


@dataclass(frozen=True)
class DirtyFrontier(Record):
    """The minimal set that must run, and the path from each stated cause to it."""

    graph_id: str
    delta_digest: str
    nodes: tuple[DirtyNode, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        object.__setattr__(self, "delta_digest", require_digest(self.delta_digest, "delta_digest"))
        collected = require_bounded(self.nodes, "nodes", maximum=MAX_DIRTY_NODES, kind="node")
        resolved = tuple(DirtyNode.coerce(item, "nodes[]") for item in collected)
        repeated = sorted({item.node_id for item in resolved if _appears(resolved, item.node_id) > 1})
        if repeated:
            raise BuildError(f"the frontier lists a node more than once: {repeated[:8]}")
        object.__setattr__(self, "nodes", tuple(sorted(resolved, key=lambda item: item.node_id)))

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(item.node_id for item in self.nodes)

    @property
    def is_empty(self) -> bool:
        return not self.nodes

    @property
    def states(self) -> tuple[BuildState, ...]:
        return tuple(sorted({item.state for item in self.nodes}, key=lambda item: item.value))

    def at(self, node_id: str) -> DirtyNode | None:
        wanted = require_identifier(node_id, "node_id")
        return next((item for item in self.nodes if item.node_id == wanted), None)

    def in_state(self, state: Any) -> tuple[DirtyNode, ...]:
        wanted = BuildState.parse(state, "state")
        return tuple(item for item in self.nodes if item.state is wanted)

    def explaining(self, node_id: str) -> tuple[str, ...]:
        found = self.at(node_id)
        return () if found is None else found.reasons

    def __bool__(self) -> bool:
        return not self.is_empty


def _appears(nodes: Sequence[DirtyNode], node_id: str) -> int:
    return sum(1 for item in nodes if item.node_id == node_id)


@dataclass(frozen=True)
class RepairTarget(Record):
    """A node that can be brought back by redoing a bounded slice instead of all of it."""

    node_id: str
    slice: DependencySlice
    facets: tuple[DependencyFacet, ...] = ()
    reasons: tuple[str, ...] = ()
    covers_whole_node: bool = False

    NESTED = {"slice": of(DependencySlice)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        if not isinstance(self.slice, DependencySlice):
            raise SchemaValidationError("slice must be a DependencySlice")
        collected = require_bounded(self.facets, "facets", maximum=MAX_FACETS)
        object.__setattr__(
            self, "facets", tuple(sorted({DependencyFacet.parse(i, "facets[]") for i in collected}, key=lambda i: i.value))
        )
        if not self.facets:
            raise BuildError(f"{self.node_id} has a repair target with no facet it repairs")
        stated = require_bounded(self.reasons, "reasons", maximum=MAX_FACETS)
        object.__setattr__(self, "reasons", tuple(sorted({require_text(i, "reasons[]", maximum=512) for i in stated})))
        if not self.reasons:
            raise BuildError(f"{self.node_id} is a repair target for no stated reason")
        if not isinstance(self.covers_whole_node, bool):
            raise SchemaValidationError("covers_whole_node must be a boolean")

    @property
    def text(self) -> str:
        scope = "whole node" if self.covers_whole_node else self.slice.text
        return f"{self.node_id} repair {scope} ({', '.join(i.value for i in self.facets)})"


@dataclass(frozen=True)
class RepairFrontier(Record):
    """What a bounded repair can cover, and what it demonstrably cannot.

    A dirty node outside this frontier, or one whose dirty slice is not covered by the
    target's slice, has to rebuild. That split is the whole point: a repair that quietly
    leaves part of the node stale is worse than no repair at all.
    """

    graph_id: str
    targets: tuple[RepairTarget, ...] = ()
    uncovered: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        collected = require_bounded(self.targets, "targets", maximum=MAX_REPAIR_TARGETS, kind="target")
        resolved = tuple(RepairTarget.coerce(item, "targets[]") for item in collected)
        index: dict[str, list[RepairTarget]] = {}
        for item in resolved:
            index.setdefault(item.node_id, []).append(item)
        for node_id, group in index.items():
            if any(other.covers_whole_node for other in group) and len(group) > 1:
                raise BuildError(
                    f"{node_id} is targeted both as a whole node and as {len(group) - 1} slice(s)"
                )
            axes = {(other.slice.axis, other.slice.selector_version) for other in group}
            if len(axes) > 1:
                raise BuildError(
                    f"{node_id} cannot be repaired along two axes at once: {sorted(axes)}"
                )
        object.__setattr__(
            self, "targets", tuple(sorted(resolved, key=lambda item: (item.node_id, item.slice.text)))
        )
        missing = require_bounded(self.uncovered, "uncovered", maximum=MAX_DIRTY_NODES, kind="node id")
        object.__setattr__(self, "uncovered", tuple(sorted({require_identifier(i, "uncovered[]") for i in missing})))

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(item.node_id for item in self.targets)

    def target_for(self, node_id: str) -> RepairTarget | None:
        wanted = require_identifier(node_id, "node_id")
        return next((item for item in self.targets if item.node_id == wanted), None)

    def covers(self, node_id: str, change: Any) -> bool:
        """Whether the stated change is inside what this node's repair redoes."""

        found = self.target_for(node_id)
        if found is None or found.covers_whole_node:
            return found is not None
        resolved = Change.coerce(change, "change")
        if resolved.facet not in found.facets:
            return False
        if resolved.slice is None:
            # A cause with no slice is a claim about the whole input, which a partial
            # repair cannot answer.
            return False
        return found.slice.overlaps(resolved.slice)

    def settles(self, node: Any) -> bool:
        """Whether this frontier's target answers every cause recorded for a dirty node."""

        found = DirtyNode.coerce(node, "node") if not isinstance(node, DirtyNode) else node
        target = self.target_for(found.node_id)
        if target is None:
            return False
        if target.covers_whole_node:
            return True
        causes = _stated_causes(found)
        return bool(causes) and all(self.covers(found.node_id, change) for change in causes)

    def rebuild_instead(self, frontier: Any) -> tuple[str, ...]:
        """Nodes a dirty frontier names that this repair frontier cannot settle."""

        wanted = DirtyFrontier.coerce(frontier, "frontier") if not isinstance(frontier, DirtyFrontier) else frontier
        return tuple(item.node_id for item in wanted.nodes if not self.settles(item))

    def __bool__(self) -> bool:
        return bool(self.targets)


def _stated_causes(node: DirtyNode) -> tuple[Change, ...]:
    """A frontier node's causes re-expressed as the changes a repair must answer."""

    facets = node.facets or (DependencyFacet.CONTENT,)
    slices: tuple[DependencySlice | None, ...] = node.slices or (None,)
    port_id = node.port_ids[0] if node.port_ids else None
    return tuple(
        Change(node_id=node.node_id, facet=facet, port_id=port_id, slice=sliced)
        for facet in facets
        for sliced in slices
    )


@dataclass(frozen=True)
class BuildStep(Record):
    """One node's decided work, with the evidence that decided it.

    The construction rules are the interesting part. A step may not claim reuse
    without a receipt, may not repair without a slice, may not be scheduled from a
    state that admits another disposition, and must always say why.
    """

    node_id: str
    state: BuildState
    disposition: WorkDisposition
    reasons: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    commit_mode: OutputCommitMode = OutputCommitMode.ATOMIC
    facets: tuple[DependencyFacet, ...] = ()
    slice: Any = None
    key: Any = None
    receipt: Any = None
    fingerprint: Any = None
    rejection: Any = None
    reproducibility: Any = None
    attempts: int = 1
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        state = BuildState.parse(self.state, "state")
        disposition = WorkDisposition.parse(self.disposition, "disposition")
        if not state.admits(disposition):
            allowed = ", ".join(item.value for item in state.legal_dispositions)
            raise BuildError(
                f"{self.node_id}: {disposition.value} is not admissible from {state.value} "
                f"(this state admits {allowed})"
            )
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "disposition", disposition)
        stated = require_bounded(self.reasons, "reasons", maximum=MAX_FACETS)
        resolved = tuple(sorted({require_text(item, "reasons[]", maximum=512) for item in stated}))
        if not resolved:
            raise BuildError(
                f"{self.node_id}: a {disposition.value} step states no reason; an unexplained plan step "
                "is the opaque smart-cache decision this kernel forbids"
            )
        object.__setattr__(self, "reasons", resolved)
        deps = require_bounded(self.depends_on, "depends_on", maximum=MAX_DIRTY_NODES, kind="node id")
        object.__setattr__(
            self,
            "depends_on",
            tuple(sorted({require_identifier(item, "depends_on[]") for item in deps if item != self.node_id})),
        )
        ports = require_bounded(self.outputs, "outputs", maximum=MAX_PORTS)
        object.__setattr__(self, "outputs", tuple(sorted({require_identifier(item, "outputs[]") for item in ports})))
        object.__setattr__(self, "commit_mode", OutputCommitMode.parse(self.commit_mode, "commit_mode"))
        collected = require_bounded(self.facets, "facets", maximum=MAX_FACETS)
        object.__setattr__(
            self,
            "facets",
            tuple(sorted({DependencyFacet.parse(item, "facets[]") for item in collected}, key=lambda i: i.value)),
        )
        if self.slice is not None:
            object.__setattr__(self, "slice", DependencySlice.coerce(self.slice, "slice"))
        if disposition.requires_slice:
            if not isinstance(self.slice, DependencySlice):
                raise BuildError(
                    f"{self.node_id}: REPAIR without a DependencySlice is a rebuild described as a repair"
                )
        elif self.slice is not None:
            raise BuildError(
                f"{self.node_id}: only REPAIR may carry a slice, not {disposition.value}"
            )
        if disposition is WorkDisposition.REPACKAGE and not self.outputs:
            raise BuildError(
                f"{self.node_id}: REPACKAGE with no output ports would re-deliver nothing"
            )
        if disposition.requires_receipt:
            if self.receipt is None:
                raise BuildError(
                    f"{self.node_id}: REUSE without a ReuseReceipt is a cache hit that cannot be audited"
                )
            granted = ReuseReceipt.coerce(self.receipt, "receipt")
            if granted.node_id != self.node_id:
                raise BuildError(
                    f"{self.node_id}: the reuse receipt behind this step belongs to {granted.node_id}"
                )
            if not granted.satisfies_output:
                raise BuildError(
                    f"{self.node_id}: a {granted.reuse_class.value} receipt covers a bounded part of the work, "
                    f"so this step cannot be {disposition.value}; the node still has output to produce"
                )
            object.__setattr__(self, "receipt", granted)
            if self.key is None:
                raise BuildError(f"{self.node_id}: reuse is claimed without the key it was admitted for")
        if self.key is not None:
            object.__setattr__(self, "key", CacheKey.coerce(self.key, "key"))
            if self.key.node_id != self.node_id:
                raise BuildError(
                    f"{self.node_id}: the cache key behind this step was derived for {self.key.node_id}"
                )
        if self.receipt is not None and disposition is not WorkDisposition.REUSE:
            raise BuildError(
                f"{self.node_id}: {disposition.value} does not reuse anything, so it must not carry a receipt"
            )
        if self.rejection is not None:
            refused = ReuseRejection.coerce(self.rejection, "rejection")
            if refused.node_id != self.node_id:
                raise BuildError(
                    f"{self.node_id}: the reuse rejection behind this step belongs to {refused.node_id}"
                )
            object.__setattr__(self, "rejection", refused)
            if disposition.avoids_work:
                raise BuildError(
                    f"{self.node_id}: this step both reuses and reports a refused cache entry"
                )
        if self.fingerprint is not None:
            object.__setattr__(self, "fingerprint", CausalFingerprint.coerce(self.fingerprint, "fingerprint"))
        if self.reproducibility is not None:
            object.__setattr__(
                self, "reproducibility", ReproducibilityClass.parse(self.reproducibility, "reproducibility").value
            )
        if isinstance(self.attempts, bool) or not isinstance(self.attempts, int) or self.attempts < 1:
            raise SchemaValidationError("attempts must be a positive integer")
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def is_reuse(self) -> bool:
        return self.disposition is WorkDisposition.REUSE

    @property
    def blocked(self) -> bool:
        return self.disposition is WorkDisposition.BLOCK

    @property
    def emits_new_bytes(self) -> bool:
        return self.disposition.emits_new_bytes

    @property
    def claims_byte_identity(self) -> bool:
        """Whether a digest match here really means the same bytes."""

        if self.reproducibility is None:
            return False
        return ReproducibilityClass(self.reproducibility).claims_byte_identity

    @property
    def avoids(self) -> bool:
        """Work this step does not do, counted in nodes for the plan's own summary."""

        return self.disposition.avoids_work

    @property
    def text(self) -> str:
        return f"{self.node_id}: {self.state.value} -> {self.disposition.value} ({'; '.join(self.reasons)})"

    def explains(self) -> tuple[str, ...]:
        """The human-readable lines this step owes, including the cache's own answer."""

        lines = list(self.reasons)
        if self.rejection is not None:
            lines.extend(self.rejection.reasons)
        if self.receipt is not None:
            lines.append(f"cache admitted: {self.receipt.reason}")
        return tuple(lines)


@dataclass(frozen=True)
class BuildPlan(Record):
    """An ordered set of decided steps, refusing to be internally inconsistent.

    The checks here are what make "incremental" mean something: dependencies have to
    be steps, the order has to exist, and no step may reuse bytes while something it
    consumes is scheduled to write new ones.
    """

    plan_id: str
    graph_id: str
    base_revision: ExternalRef
    target_revision: ExternalRef
    steps: tuple[BuildStep, ...] = ()
    delta_digest: Any = None
    created_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", require_id(self.plan_id, "plan_id"))
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        for name in ("base_revision", "target_revision"):
            object.__setattr__(self, name, _revision(getattr(self, name), name))
        collected = require_bounded(self.steps, "steps", maximum=MAX_BUILD_PLAN_STEPS, kind="step")
        resolved = tuple(BuildStep.coerce(item, "steps[]") for item in collected)
        repeated = sorted({item.node_id for item in resolved if _steps_for(resolved, item.node_id) > 1})
        if repeated:
            raise BuildError(f"a plan gives one node two dispositions: {repeated[:8]}")
        known = {item.node_id for item in resolved}
        for item in resolved:
            unknown = sorted(set(item.depends_on) - known)
            if unknown:
                raise BuildError(
                    f"{item.node_id} depends on nodes outside this plan: {unknown[:8]}; a step may not "
                    "wait for work nobody decided on"
                )
        object.__setattr__(
            self, "steps", tuple(sorted(resolved, key=lambda item: item.node_id))
        )
        if self.delta_digest is not None:
            object.__setattr__(self, "delta_digest", require_digest(self.delta_digest, "delta_digest"))
        object.__setattr__(self, "created_at_ms", require_millis(self.created_at_ms, "created_at_ms"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})
        self._require_consistent()

    def _require_consistent(self) -> None:
        index = {item.node_id: item for item in self.steps}
        edges = {item.node_id: item.depends_on for item in self.steps}
        try:
            topological_order(tuple(index), edges)
        except Exception as error:  # machines reports the cycle, the plan owns the wording
            raise BuildError(f"this plan cannot be executed in any order: {error}") from error
        for item in self.steps:
            if not item.is_reuse:
                continue
            upstream = [index[name] for name in item.depends_on if name in index]
            writers = sorted(other.node_id for other in upstream if other.emits_new_bytes)
            if writers:
                raise BuildError(
                    f"{item.node_id} may not reuse while its inputs {writers[:6]} are scheduled to emit "
                    "new bytes; that is under-invalidation, and the oracle would have to catch it later"
                )

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(item.node_id for item in self.steps)

    @property
    def reused(self) -> tuple[str, ...]:
        return tuple(sorted(item.node_id for item in self.steps if item.is_reuse))

    @property
    def must_run(self) -> tuple[str, ...]:
        return tuple(sorted(item.node_id for item in self.steps if item.disposition.is_work and not item.blocked))

    @property
    def blocked(self) -> tuple[str, ...]:
        return tuple(sorted(item.node_id for item in self.steps if item.blocked))

    @property
    def repairs(self) -> tuple[str, ...]:
        return tuple(sorted(item.node_id for item in self.steps if item.disposition is WorkDisposition.REPAIR))

    @property
    def receipts(self) -> tuple[ReuseReceipt, ...]:
        return tuple(item.receipt for item in self.steps if item.receipt is not None)

    @property
    def is_settled(self) -> bool:
        """Nothing left to decide: no unknown, no blocked step."""

        return not self.blocked and not any(item.state is BuildState.UNKNOWN for item in self.steps)

    @property
    def summary(self) -> Mapping[WorkDisposition, tuple[str, ...]]:
        collected: dict[WorkDisposition, list[str]] = {}
        for item in self.steps:
            collected.setdefault(item.disposition, []).append(item.node_id)
        return {key: tuple(sorted(value)) for key, value in sorted(collected.items(), key=lambda i: i[0].value)}

    def at(self, node_id: str) -> BuildStep:
        wanted = require_identifier(node_id, "node_id")
        for item in self.steps:
            if item.node_id == wanted:
                return item
        raise BuildError(f"this plan says nothing about {wanted}")

    def covers(self, node_ids: Iterable[str]) -> tuple[str, ...]:
        """Which of the named nodes this plan does not decide, reported not hidden."""

        wanted = {require_identifier(item, "node_ids[]") for item in node_ids}
        return tuple(sorted(wanted - set(self.node_ids)))

    def ordered(self) -> tuple[str, ...]:
        """Causal execution order: producers before consumers."""

        edges = {item.node_id: item.depends_on for item in self.steps}
        return topological_order(tuple(self.node_ids), edges)

    def requires(self, node_id: str) -> tuple[BuildStep, ...]:
        wanted = require_identifier(node_id, "node_id")
        index = {item.node_id: item for item in self.steps}
        return tuple(index[name] for name in self.at(wanted).depends_on if name in index)

    def downstream_of(self, node_id: str) -> tuple[str, ...]:
        wanted = require_identifier(node_id, "node_id")
        edges = {item.node_id: item.depends_on for item in self.steps}
        consumers: dict[str, list[str]] = {}
        for node, deps in edges.items():
            for dep in deps:
                consumers.setdefault(dep, []).append(node)
        seen: set[str] = set()
        frontier = [wanted]
        while frontier:
            for target in consumers.get(frontier.pop(), ()):
                if target not in seen:
                    seen.add(target)
                    frontier.append(target)
        return tuple(sorted(seen))

    def __bool__(self) -> bool:
        return bool(self.steps)


def _steps_for(steps: Sequence[BuildStep], node_id: str) -> int:
    return sum(1 for item in steps if item.node_id == node_id)


def dirty_frontier(
    bound: MaterializationGraph,
    delta: BuildDelta,
    *,
    cone: ImpactCone | None = None,
    states: Mapping[str, Any] | None = None,
) -> DirtyFrontier:
    """Compile a delta through the facets and edges into the nodes that must run.

    ``states`` lets the caller name a node that is already known to need work (an
    unmaterialized node, a blocked one) without inventing a cause for it; anything not
    named there and not reached by the cone stays out of the frontier, which is the
    whole economy of an incremental build.
    """

    if not isinstance(bound, MaterializationGraph):
        raise SchemaValidationError("dirty_frontier requires a bound MaterializationGraph")
    if not isinstance(delta, BuildDelta):
        raise SchemaValidationError("dirty_frontier requires a BuildDelta")
    definition = bound.revision.definition
    if definition.graph_id != delta.graph_id:
        raise BuildError(
            f"the delta is for graph {delta.graph_id} but the bound graph is {definition.graph_id}"
        )
    known = definition.node_index
    for change in delta.changes:
        if change.node_id not in known:
            raise BuildError(
                f"the delta changes {change.node_id!r}, which {definition.graph_id} does not declare"
            )
    resolved = None if delta.is_empty else (cone if cone is not None else impact_of(bound, delta.changes))
    declared = dict(states or {})
    facets_by_node: dict[str, set[DependencyFacet]] = {}
    reasons_by_node: dict[str, set[str]] = {}
    roots_by_node: dict[str, set[str]] = {}
    ports_by_node: dict[str, set[str]] = {}
    slices_by_node: dict[str, set[DependencySlice]] = {}
    depth_by_node: dict[str, int] = {}
    for change in delta.changes:
        facets_by_node.setdefault(change.node_id, set()).add(change.facet)
        reasons_by_node.setdefault(change.node_id, set()).add(_cause_reason(change))
        roots_by_node.setdefault(change.node_id, set()).add(change.node_id)
        if change.port_id:
            ports_by_node.setdefault(change.node_id, set()).add(change.port_id)
        if change.slice is not None:
            slices_by_node.setdefault(change.node_id, set()).add(change.slice)
        depth_by_node.setdefault(change.node_id, 0)
    for step in (() if resolved is None else resolved.explanation):
        node = step.consumer_node_id
        facets_by_node.setdefault(node, set()).add(step.facet)
        reasons_by_node.setdefault(node, set()).add(step.reason)
        roots_by_node.setdefault(node, set()).add(step.changed_node_id)
        depth_by_node.setdefault(node, _depth_of(resolved, node))
    conditional = set() if resolved is None else set(resolved.conditional)
    nodes: list[DirtyNode] = []
    for node_id in sorted(set(facets_by_node) | set(declared)):
        if node_id not in known:
            raise BuildError(f"the frontier names undeclared node {node_id!r}")
        state = BuildState.parse(declared.get(node_id, BuildState.DIRTY), "states[]")
        if node_id in conditional and state is BuildState.DIRTY:
            # A conditional consumer only matters if a selection resolves that way; the
            # planner has to know that instead of discovering it as a surprise miss.
            state = BuildState.REVALIDATE_ONLY
        nodes.append(
            DirtyNode(
                node_id=node_id,
                facets=tuple(facets_by_node.get(node_id, ())),
                reasons=tuple(reasons_by_node.get(node_id, ()))
                or (_inherited_reason(node_id, resolved, state),),
                roots=tuple(roots_by_node.get(node_id, ())),
                depth=0 if resolved is None else depth_by_node.get(node_id, 0),
                port_ids=tuple(ports_by_node.get(node_id, ())),
                slices=tuple(slices_by_node.get(node_id, ())),
                state=state,
                conditional=node_id in conditional,
            )
        )
    return DirtyFrontier(
        graph_id=definition.graph_id,
        delta_digest=delta.delta_digest,
        nodes=tuple(nodes),
    )


def _depth_of(cone: ImpactCone | None, node_id: str) -> int:
    if cone is None or node_id in cone.direct:
        return 0
    hops = [step for step in cone.explanation if step.consumer_node_id == node_id]
    return max(1, len(hops)) if hops else 0


def _cause_reason(change: Change) -> str:
    moved = ""
    if change.previous_digest and change.current_digest:
        moved = f" ({change.previous_digest[:8]} -> {change.current_digest[:8]})"
    elif change.current_digest:
        moved = f" (now {change.current_digest[:8]})"
    where = f".{change.port_id}" if change.port_id else ""
    bounded = f" @{change.slice.text}" if change.slice is not None else ""
    return f"{change.node_id}{where}{bounded} changed in facet {change.facet.value}{moved}"[:512]


def _inherited_reason(node_id: str, cone: ImpactCone | None, state: BuildState) -> str:
    if cone is None:
        return (
            f"{node_id} was named by the caller as {state.value} while nothing in the graph states a "
            "change, so the planner acts on that declaration"
        )
    steps = cone.reason_for(node_id)
    return steps[0].reason if steps else f"{node_id} is inside the impact cone of the stated changes"


def repair_frontier(
    bound: MaterializationGraph,
    frontier: DirtyFrontier,
    *,
    slices: Mapping[str, Any] | None = None,
    whole_node: Iterable[str] = (),
) -> RepairFrontier:
    """Decide which dirty nodes a bounded slice repair can actually settle.

    A repair is admitted only where the dirty cause is itself sliced and falls inside
    the slice being redone. Everything else is reported as uncovered, so the planner
    rebuilds it rather than pretending a partial redo answered a whole-node change.
    """

    if not isinstance(bound, MaterializationGraph):
        raise SchemaValidationError("repair_frontier requires a bound MaterializationGraph")
    wanted = DirtyFrontier.coerce(frontier, "frontier")
    declared = bound.revision.definition.node_index
    supplied = dict(slices or {})
    forced = {require_identifier(item, "whole_node[]") for item in whole_node}
    unknown = sorted((set(supplied) | forced) - set(declared))
    if unknown:
        raise BuildError(f"repair targets name nodes this graph does not declare: {unknown[:8]}")
    targets: list[RepairTarget] = []
    uncovered: list[str] = []
    for item in wanted.nodes:
        if item.node_id in forced:
            targets.append(_whole_node_target(item, "the caller asked for a whole-node repair"))
            continue
        offered = supplied.get(item.node_id)
        if offered is None:
            uncovered.append(item.node_id)
            continue
        resolved = DependencySlice.coerce(offered, "slices[]")
        if not _slice_answers(item, resolved):
            uncovered.append(item.node_id)
            continue
        facets = _repairable_facets(item)
        if not facets:
            uncovered.append(item.node_id)
            continue
        if set(facets) != set(item.facets):
            # One bounded redo has to answer every cause the node states. A node dirty in
            # content *and* in evidence is not settled by redoing its content, so it stays
            # uncovered here rather than owing a target the frontier then refuses to settle.
            uncovered.append(item.node_id)
            continue
        targets.append(
            RepairTarget(
                node_id=item.node_id,
                slice=resolved,
                facets=facets,
                reasons=(
                    f"redoing {resolved.text} covers the sliced causes of {item.node_id}",
                    *item.reasons[:1],
                ),
            )
        )
    return RepairFrontier(
        graph_id=wanted.graph_id,
        targets=tuple(targets),
        uncovered=tuple(sorted(set(uncovered))),
    )


def _repairable_facets(node: DirtyNode) -> tuple[DependencyFacet, ...]:
    """Only content and semantics changes can be repaired by redoing a slice."""

    return tuple(item for item in node.facets if item in {DependencyFacet.CONTENT, DependencyFacet.SEMANTICS})


def _slice_answers(node: DirtyNode, offered: DependencySlice) -> bool:
    """Whether redoing ``offered`` answers every slice the node's own causes name.

    A cause stated about the whole input is not answered by a bounded redo, and a cause
    that spans two regions is not answered by repairing one of them. In both cases the
    node stays uncovered so the planner rebuilds it instead of leaving part of it stale.
    """

    if not node.slices:
        return False
    return all(offered.overlaps(item) for item in node.slices)


def _whole_node_target(node: DirtyNode, reason: str) -> RepairTarget:
    axis = f"repair.{node.node_id}"
    return RepairTarget(
        node_id=node.node_id,
        slice=DependencySlice(axis=axis[:63] or "repair", values=("all",)),
        facets=node.facets or (DependencyFacet.CONTENT,),
        reasons=(reason,),
        covers_whole_node=True,
    )


@dataclass(frozen=True)
class BuildExplainTrace(Record):
    """Why one node got its disposition, in the order a reader would ask.

    The module spec asks for human and machine readable explanations of every dirty,
    cache and repair decision. This is that record: the machine part is the fields,
    the human part is ``lines``, and both are derived from the same step so they
    cannot disagree.
    """

    node_id: str
    state: BuildState
    disposition: WorkDisposition
    causes: tuple[str, ...] = ()
    cone: tuple[str, ...] = ()
    cache: tuple[str, ...] = ()
    repairs: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    downstream: tuple[str, ...] = ()
    journal: tuple[str, ...] = ()
    plan_digest: Any = None
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        state = BuildState.parse(self.state, "state")
        disposition = WorkDisposition.parse(self.disposition, "disposition")
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "disposition", disposition)
        for name in ("causes", "cone", "cache", "repairs", "journal"):
            collected = require_bounded(getattr(self, name), name, maximum=MAX_EXPLAIN_STEPS)
            object.__setattr__(
                self,
                name,
                tuple(require_text(item, f"{name}[]", maximum=512) for item in collected),
            )
        for name in ("dependencies", "downstream"):
            collected = require_bounded(getattr(self, name), name, maximum=MAX_DIRTY_NODES, kind="node id")
            object.__setattr__(
                self, name, tuple(sorted({require_identifier(item, f"{name}[]") for item in collected}))
            )
        if not self.causes:
            raise BuildError(
                f"{self.node_id}: an explain trace with no cause explains nothing; the plan step must "
                "have carried reasons"
            )
        if self.plan_digest is not None:
            object.__setattr__(self, "plan_digest", require_digest(self.plan_digest, "plan_digest"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def lines(self) -> tuple[str, ...]:
        head = f"{self.node_id} is {self.state.value}, so it will {self.disposition.value}"
        body = [f"  cause: {item}" for item in self.causes]
        body += [f"  reached from: {item}" for item in self.cone]
        body += [f"  cache: {item}" for item in self.cache]
        body += [f"  repair: {item}" for item in self.repairs]
        if self.dependencies:
            body.append(f"  waits for: {', '.join(self.dependencies)}")
        if self.downstream:
            body.append(f"  blocks until done: {', '.join(self.downstream)}")
        body += [f"  journal: {item}" for item in self.journal]
        return tuple([head, *body])

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def explain_build(
    plan: BuildPlan,
    node_id: str,
    *,
    cone: ImpactCone | None = None,
    journal: "BuildJournal | None" = None,
) -> BuildExplainTrace:
    """Render one step of a plan as the trace it owes."""

    wanted = BuildPlan.coerce(plan, "plan")
    step = wanted.at(node_id)
    reached = ()
    if cone is not None:
        reached = tuple(
            sorted({f"{item.changed_node_id} -> {item.edge_id} -> {item.consumer_node_id}" for item in cone.explanation if item.consumer_node_id == step.node_id})
        )
    journal_lines = ()
    if journal is not None:
        journal_lines = tuple(item.text for item in journal.events_for(step.node_id))
    return BuildExplainTrace(
        node_id=step.node_id,
        state=step.state,
        disposition=step.disposition,
        causes=step.explains(),
        cone=reached,
        cache=tuple(item.text for item in step.rejection.checks) if step.rejection is not None else (
            (f"admitted: {step.receipt.reason}",) if step.receipt is not None else ()
        ),
        repairs=(step.slice.text,) if step.slice is not None else (),
        dependencies=step.depends_on,
        downstream=wanted.downstream_of(step.node_id),
        journal=journal_lines,
        plan_digest=wanted.digest(),
    )


class JournalKind(Labeled):
    """What a build attempt actually did, one event at a time.

    ``OUTPUT_STAGED`` and ``OUTPUT_COMMITTED`` are separate kinds because the whole
    point of the journal is the boundary between them: staged bytes are not canonical
    until a commit event says so, and a recovery decision that ignores that boundary
    is how a half-written output set becomes a cache hit.
    """

    ATTEMPT_STARTED = "ATTEMPT_STARTED"
    PLAN_ADOPTED = "PLAN_ADOPTED"
    NODE_STARTED = "NODE_STARTED"
    NODE_COMPLETED = "NODE_COMPLETED"
    CACHE_HIT = "CACHE_HIT"
    CACHE_MISS = "CACHE_MISS"
    OUTPUT_STAGED = "OUTPUT_STAGED"
    OUTPUT_COMMITTED = "OUTPUT_COMMITTED"
    OUTPUT_DISCARDED = "OUTPUT_DISCARDED"
    VALIDATOR_RAN = "VALIDATOR_RAN"
    NODE_FAILED = "NODE_FAILED"
    SIDE_EFFECT_OBSERVED = "SIDE_EFFECT_OBSERVED"
    ATTEMPT_CANCELLED = "ATTEMPT_CANCELLED"
    ATTEMPT_COMMITTED = "ATTEMPT_COMMITTED"

    @property
    def names_output(self) -> bool:
        return self in {
            JournalKind.OUTPUT_STAGED,
            JournalKind.OUTPUT_COMMITTED,
            JournalKind.OUTPUT_DISCARDED,
        }

    @property
    def ends_attempt(self) -> bool:
        return self in {JournalKind.ATTEMPT_COMMITTED, JournalKind.ATTEMPT_CANCELLED}

    @property
    def reports_failure(self) -> bool:
        return self in {JournalKind.NODE_FAILED, JournalKind.ATTEMPT_CANCELLED}


@dataclass(frozen=True)
class JournalEvent(Record):
    """One immutable fact about an attempt, ordered by its own sequence number.

    The bytes claim is named ``output_digest`` rather than ``digest``: ``digest`` is the
    method every ``Record`` owes, and a field of that name would hide it on this type.
    """

    event_id: str
    attempt_id: str
    kind: JournalKind
    sequence: int
    at_ms: int = 0
    node_id: Any = None
    port_ids: tuple[str, ...] = ()
    output_digest: Any = None
    detail: Any = None
    plan_digest: Any = None
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", require_id(self.event_id, "event_id"))
        object.__setattr__(self, "attempt_id", require_id(self.attempt_id, "attempt_id"))
        kind = JournalKind.parse(self.kind, "kind")
        object.__setattr__(self, "kind", kind)
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 1:
            raise SchemaValidationError("sequence must be a positive integer")
        object.__setattr__(self, "at_ms", require_millis(self.at_ms, "at_ms"))
        if self.node_id is not None:
            object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        elif kind.names_output or kind in {
            JournalKind.NODE_STARTED,
            JournalKind.NODE_COMPLETED,
            JournalKind.CACHE_HIT,
            JournalKind.CACHE_MISS,
            JournalKind.VALIDATOR_RAN,
            JournalKind.NODE_FAILED,
        }:
            raise BuildError(f"{kind.value} must name the node it is about")
        ports = require_bounded(self.port_ids, "port_ids", maximum=MAX_PORTS)
        object.__setattr__(self, "port_ids", tuple(sorted({require_identifier(i, "port_ids[]") for i in ports})))
        if kind.names_output and not self.port_ids:
            raise BuildError(f"{kind.value} names no port, so it could not identify an output")
        if self.output_digest is not None:
            object.__setattr__(self, "output_digest", require_digest(self.output_digest, "output_digest"))
        elif kind in {JournalKind.OUTPUT_STAGED, JournalKind.OUTPUT_COMMITTED}:
            raise BuildError(f"{kind.value} is a bytes claim with no digest behind it")
        object.__setattr__(self, "detail", require_optional_text(self.detail, "detail", maximum=512))
        if self.plan_digest is not None:
            object.__setattr__(self, "plan_digest", require_digest(self.plan_digest, "plan_digest"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def text(self) -> str:
        where = f" {self.node_id}" if self.node_id else ""
        ports = f"[{','.join(self.port_ids)}]" if self.port_ids else ""
        tail = f" {str(self.output_digest)[:12]}" if self.output_digest else ""
        note = f": {self.detail}" if self.detail else ""
        return f"#{self.sequence}{where}{ports}{tail}{note}"


class RecoveryClass(Labeled):
    """What crash recovery may do, chosen from the journal rather than assumed.

    ``CLEAN`` means the attempt can continue but its staged bytes are gone; ``RESTART``
    means nothing in the attempt can be trusted. The two are different because the
    first keeps completed, committed work and the second does not.
    """

    RESUME = "RESUME"
    REUSE = "REUSE"
    CLEAN = "CLEAN"
    RESTART = "RESTART"

    @property
    def keeps_committed_work(self) -> bool:
        return self in {RecoveryClass.RESUME, RecoveryClass.REUSE, RecoveryClass.CLEAN}

    @property
    def discards_staged_output(self) -> bool:
        return self is not RecoveryClass.REUSE


@dataclass(frozen=True)
class RecoveryVerdict(Record):
    """The recovery decision, and the exact node sets it applies to."""

    attempt_id: str
    classification: RecoveryClass
    plan_digest: Any = None
    done: tuple[str, ...] = ()
    resumable: tuple[str, ...] = ()
    reusable: tuple[str, ...] = ()
    must_clean: tuple[str, ...] = ()
    restart: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempt_id", require_id(self.attempt_id, "attempt_id"))
        object.__setattr__(self, "classification", RecoveryClass.parse(self.classification, "classification"))
        if self.plan_digest is not None:
            object.__setattr__(self, "plan_digest", require_digest(self.plan_digest, "plan_digest"))
        for name in ("done", "resumable", "reusable", "must_clean", "restart"):
            collected = require_bounded(getattr(self, name), name, maximum=MAX_BUILD_PLAN_STEPS, kind="node id")
            object.__setattr__(
                self, name, tuple(sorted({require_identifier(item, f"{name}[]") for item in collected}))
            )
        stated = require_bounded(self.reasons, "reasons", maximum=MAX_FACETS)
        object.__setattr__(self, "reasons", tuple(require_text(item, "reasons[]", maximum=512) for item in stated))
        if not self.reasons:
            raise BuildError("a recovery verdict without reasons is a guess about a crash")
        overlap = sorted(set(self.done) & (set(self.must_clean) | set(self.restart)))
        if overlap:
            raise BuildError(
                f"recovery cannot both keep and discard {overlap[:6]}; that is the bug this verdict exists "
                "to prevent"
            )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def may_trust_committed(self) -> bool:
        return self.classification.keeps_committed_work

    @property
    def text(self) -> str:
        return f"{self.classification.value}: " + "; ".join(self.reasons)


@dataclass(frozen=True)
class BuildJournal(Record):
    """The append-only record of one build attempt.

    Journals here are immutable values: ``with_event`` returns a new journal, which is
    what makes "temp outputs are not canonical until commit" checkable rather than a
    convention a caller may forget.
    """

    attempt_id: str
    plan_digest: str
    events: tuple[JournalEvent, ...] = ()
    created_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempt_id", require_id(self.attempt_id, "attempt_id"))
        object.__setattr__(self, "plan_digest", require_digest(self.plan_digest, "plan_digest"))
        if isinstance(self.created_at_ms, bool) or not isinstance(self.created_at_ms, int):
            raise SchemaValidationError("created_at_ms must be an integer")
        collected = require_bounded(self.events, "events", maximum=MAX_EVENTS)
        resolved = tuple(JournalEvent.coerce(item, "events[]") for item in collected)
        if not resolved:
            raise BuildError(
                "a build journal holds at least its ATTEMPT_STARTED event; an attempt that recorded "
                "nothing cannot be recovered, because there is nothing to recover it from"
            )
        if resolved[0].kind is not JournalKind.ATTEMPT_STARTED:
            raise BuildError(
                "a build journal begins with ATTEMPT_STARTED; an attempt that never said it started "
                "cannot be recovered, only restarted"
            )
        foreign = sorted({item.attempt_id for item in resolved if item.attempt_id != self.attempt_id})
        if foreign:
            raise BuildError(f"a journal holds one attempt's events, found {foreign[:4]}")
        sequences = [item.sequence for item in resolved]
        if sequences != list(range(1, len(sequences) + 1)):
            raise BuildError(
                f"journal sequences must run 1..{len(sequences)} with no gaps, got {sequences[:12]}"
            )
        ids = [item.event_id for item in resolved]
        if len(set(ids)) != len(ids):
            raise BuildError("two journal events share an id, so one of them overwrote the other")
        object.__setattr__(self, "events", resolved)
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @classmethod
    def begin(cls, plan: BuildPlan, *, attempt_id: str | None = None, at_ms: int = 0) -> "BuildJournal":
        made = require_id(attempt_id or new_id(), "attempt_id")
        digest_value = plan.digest()
        return cls(
            attempt_id=made,
            plan_digest=digest_value,
            created_at_ms=at_ms,
            events=(
                JournalEvent(
                    event_id=new_id(),
                    attempt_id=made,
                    kind=JournalKind.ATTEMPT_STARTED,
                    sequence=1,
                    at_ms=at_ms,
                    plan_digest=digest_value,
                    detail=f"plan {digest_value[:12]} adopted",
                ),
            ),
        )

    def with_event(
        self,
        kind: Any,
        *,
        node_id: str | None = None,
        port_ids: Iterable[str] = (),
        output_digest: str | None = None,
        detail: str | None = None,
        at_ms: int = 0,
        event_id: str | None = None,
    ) -> "BuildJournal":
        """Append one event, refusing to invent a fact this journal cannot support."""

        resolved = JournalKind.parse(kind, "kind")
        sequence = len(self.events) + 1
        if self.closed:
            raise BuildError(f"attempt {self.attempt_id[:8]} is {self.ending_kind.value}; nothing more is journaled")
        if resolved is JournalKind.OUTPUT_COMMITTED:
            self._require_committable(node_id, port_ids)
        event = JournalEvent(
            event_id=event_id or new_id(),
            attempt_id=self.attempt_id,
            kind=resolved,
            sequence=sequence,
            at_ms=at_ms,
            node_id=node_id,
            port_ids=tuple(port_ids),
            output_digest=output_digest,
            detail=detail,
            plan_digest=self.plan_digest,
        )
        return BuildJournal(
            attempt_id=self.attempt_id,
            plan_digest=self.plan_digest,
            events=self.events + (event,),
            created_at_ms=self.created_at_ms,
            contract_version=self.contract_version,
        )

    def _require_committable(self, node_id: Any, port_ids: Iterable[str]) -> None:
        """A commit may only name bytes this attempt already staged, all at once or per port."""

        wanted = require_identifier(node_id, "node_id") if node_id is not None else None
        if wanted is None:
            raise BuildError("OUTPUT_COMMITTED must name the node whose outputs it commits")
        ports = tuple(sorted({require_identifier(item, "port_ids[]") for item in port_ids}))
        if not ports:
            raise BuildError("OUTPUT_COMMITTED names no port")
        staged = self.staged_outputs.get(wanted, {})
        missing = sorted(set(ports) - set(staged))
        if missing:
            raise BuildError(
                f"{wanted} cannot commit {missing[:6]}: those outputs were never staged, so the commit "
                "would claim bytes this attempt did not produce"
            )
        discarded = [
            event
            for event in self.events
            if event.kind is JournalKind.OUTPUT_DISCARDED and event.node_id == wanted
        ]
        if any(set(ports) & set(event.port_ids) for event in discarded):
            raise BuildError(f"{wanted} discarded its staged bytes; a discard is not un-happened by a commit")

    @property
    def ending_kind(self) -> JournalKind | None:
        return self.events[-1].kind if self.events and self.events[-1].kind.ends_attempt else None

    @property
    def closed(self) -> bool:
        return self.ending_kind is not None

    @property
    def committed(self) -> bool:
        return any(event.kind is JournalKind.ATTEMPT_COMMITTED for event in self.events)

    @property
    def cancelled(self) -> bool:
        return any(event.kind is JournalKind.ATTEMPT_CANCELLED for event in self.events)

    def events_for(self, node_id: str) -> tuple[JournalEvent, ...]:
        wanted = require_identifier(node_id, "node_id")
        return tuple(event for event in self.events if event.node_id == wanted)

    def _nodes_where(self, kind: JournalKind) -> tuple[str, ...]:
        return tuple(sorted({event.node_id for event in self.events if event.kind is kind and event.node_id}))

    @property
    def started_nodes(self) -> tuple[str, ...]:
        return self._nodes_where(JournalKind.NODE_STARTED)

    @property
    def completed_nodes(self) -> tuple[str, ...]:
        return self._nodes_where(JournalKind.NODE_COMPLETED)

    @property
    def failed_nodes(self) -> tuple[str, ...]:
        return self._nodes_where(JournalKind.NODE_FAILED)

    @property
    def hits(self) -> tuple[str, ...]:
        return self._nodes_where(JournalKind.CACHE_HIT)

    @property
    def misses(self) -> tuple[str, ...]:
        return self._nodes_where(JournalKind.CACHE_MISS)

    @property
    def in_flight(self) -> tuple[str, ...]:
        """Started and never completed: exactly the work a crash interrupted."""

        return tuple(sorted(set(self.started_nodes) - set(self.completed_nodes)))

    @property
    def staged_outputs(self) -> Mapping[str, Mapping[str, str]]:
        collected: dict[str, dict[str, str]] = {}
        for event in self.events:
            if event.kind is not JournalKind.OUTPUT_STAGED or event.output_digest is None:
                continue
            for port in event.port_ids:
                collected.setdefault(event.node_id, {})[port] = event.output_digest
        return {node: dict(sorted(ports.items())) for node, ports in sorted(collected.items())}

    @property
    def committed_outputs(self) -> Mapping[str, Mapping[str, str]]:
        """Only committed bytes, which is the sole view the rest of the kernel may use."""

        collected: dict[str, dict[str, str]] = {}
        for event in self.events:
            if event.kind is not JournalKind.OUTPUT_COMMITTED:
                continue
            for port in event.port_ids:
                digest_value = self.staged_outputs.get(event.node_id, {}).get(port)
                if digest_value is not None:
                    collected.setdefault(event.node_id, {})[port] = digest_value
        return {node: dict(sorted(ports.items())) for node, ports in sorted(collected.items())}

    @property
    def pending_temporary(self) -> Mapping[str, tuple[str, ...]]:
        """Staged but never committed. Losing these costs time, not truth."""

        out: dict[str, list[str]] = {}
        for node, ports in self.staged_outputs.items():
            committed = self.committed_outputs.get(node, {})
            leftover = sorted(set(ports) - set(committed))
            if leftover:
                out[node] = leftover
        return dict(sorted(out.items()))

    def recover(self, plan: BuildPlan) -> RecoveryVerdict:
        """Decide what a crashed attempt may keep, from the journal alone."""

        wanted = BuildPlan.coerce(plan, "plan")
        digest_value = wanted.digest()
        if digest_value != self.plan_digest:
            return RecoveryVerdict(
                attempt_id=self.attempt_id,
                classification=RecoveryClass.RESTART,
                plan_digest=digest_value,
                restart=tuple(wanted.node_ids),
                reasons=(
                    f"the plan adopted by this attempt is {self.plan_digest[:12]} but the plan on the "
                    f"table is {digest_value[:12]}; a changed plan invalidates every partial claim in it",
                ),
            )
        if self.cancelled:
            return RecoveryVerdict(
                attempt_id=self.attempt_id,
                classification=RecoveryClass.RESTART,
                plan_digest=digest_value,
                restart=tuple(wanted.node_ids),
                reasons=("the attempt was cancelled, so none of its staging is admissible",),
            )
        done = tuple(sorted(set(self.completed_nodes) & set(wanted.node_ids)))
        staged_nodes = tuple(sorted(self.pending_temporary))
        remaining = tuple(sorted(set(wanted.node_ids) - set(done)))
        reusable = tuple(sorted(set(wanted.reused) & set(done)))
        reasons: list[str] = []
        if not staged_nodes and not remaining:
            reasons.append("every step reported completion, so nothing is left to do")
            classification = RecoveryClass.REUSE
        elif not staged_nodes:
            reasons.append(
                f"{len(done)} of {len(wanted.steps)} steps completed and committed, and nothing is half-staged"
            )
            classification = RecoveryClass.RESUME
        else:
            reasons.append(
                f"{len(staged_nodes)} node(s) staged bytes that never committed: "
                + ", ".join(
                    f"{node}[{','.join(ports)}]" for node, ports in sorted(self.pending_temporary.items())
                )
            )
            reasons.append("uncommitted staging is not canonical, so it is discarded and those nodes redo work")
            classification = RecoveryClass.CLEAN
        return RecoveryVerdict(
            attempt_id=self.attempt_id,
            classification=classification,
            plan_digest=digest_value,
            done=done,
            resumable=tuple(sorted(set(remaining) - set(staged_nodes))),
            reusable=reusable,
            must_clean=staged_nodes,
            reasons=tuple(reasons),
        )

    def validate_against(self, plan: BuildPlan) -> tuple[str, ...]:
        """Report every place the journal claims work the plan never decided.

        A hit for a node the plan scheduled as a rebuild is the audit finding that
        matters most, because it means the executor and the planner disagreed and
        nobody noticed.
        """

        wanted = BuildPlan.coerce(plan, "plan")
        if wanted.digest() != self.plan_digest:
            return (f"journal plan {self.plan_digest[:12]} is not the plan on the table",)
        findings: list[str] = []
        for node_id in self.hits:
            step = next((item for item in wanted.steps if item.node_id == node_id), None)
            if step is None:
                findings.append(f"CACHE_HIT names {node_id}, which the plan does not contain")
            elif not step.is_reuse:
                findings.append(
                    f"{node_id} reports a cache hit but the plan decided {step.disposition.value}"
                )
        for node_id in self.completed_nodes:
            step = next((item for item in wanted.steps if item.node_id == node_id), None)
            if step is None:
                findings.append(f"NODE_COMPLETED names {node_id}, which the plan does not contain")
                continue
            unstarted = node_id not in self.started_nodes
            if unstarted:
                findings.append(f"{node_id} completed without ever starting")
            if step.emits_new_bytes and node_id not in self.committed_outputs:
                findings.append(
                    f"{step.disposition.value} step {node_id} completed without committing its outputs"
                )
        for node_id, ports in sorted(self.committed_outputs.items()):
            step = next((item for item in wanted.steps if item.node_id == node_id), None)
            if step is None:
                continue
            promised = set(step.outputs)
            extra = sorted(set(ports) - promised)
            if extra:
                findings.append(f"{node_id} committed outputs the graph never promised: {extra[:6]}")
            if step.commit_mode is OutputCommitMode.ATOMIC and promised - set(ports):
                findings.append(
                    f"{node_id} commits {sorted(set(ports))[:6]} of its atomic output set "
                    f"{sorted(promised)[:8]}"
                )
        return tuple(findings)


@dataclass(frozen=True)
class NodeComparison(Record):
    """One node's incremental result measured against the admitted full build."""

    node_id: str
    mode: str
    disposition: WorkDisposition
    reproducibility: Any = None
    incremental_digest: Any = None
    reference_digest: Any = None
    matched: bool = True
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        verdict = require_text(self.mode, "mode", maximum=32).upper()
        if verdict not in _ORACLE_MODES:
            raise SchemaValidationError(f"mode must be one of {', '.join(_ORACLE_MODES)}, got {self.mode!r}")
        object.__setattr__(self, "mode", verdict)
        object.__setattr__(self, "disposition", WorkDisposition.parse(self.disposition, "disposition"))
        if self.reproducibility is not None:
            object.__setattr__(
                self,
                "reproducibility",
                ReproducibilityClass.parse(self.reproducibility, "reproducibility").value,
            )
        for name in ("incremental_digest", "reference_digest"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_digest(value, name))
        if not isinstance(self.matched, bool):
            raise SchemaValidationError("matched must be a boolean")
        stated = require_bounded(self.reasons, "reasons", maximum=MAX_FACETS)
        object.__setattr__(self, "reasons", tuple(require_text(i, "reasons[]", maximum=512) for i in stated))
        if self.mode == "EXACT" and not self.reasons:
            raise BuildError(f"{self.node_id}: an exact comparison states no basis for its judgement")


_ORACLE_MODES = ("EXACT", "EQUIVALENCE", "REFUSED")


@dataclass(frozen=True)
class IncrementalVerdict(Record):
    """The oracle's answer: was the incremental run as correct as the full one?"""

    graph_id: str
    plan_digest: str
    comparisons: tuple[NodeComparison, ...] = ()
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        object.__setattr__(self, "plan_digest", require_digest(self.plan_digest, "plan_digest"))
        collected = require_bounded(self.comparisons, "comparisons", maximum=MAX_BUILD_PLAN_STEPS, kind="comparison")
        resolved = tuple(NodeComparison.coerce(item, "comparisons[]") for item in collected)
        repeated = sorted({item.node_id for item in resolved if _appears_in(resolved, item.node_id) > 1})
        if repeated:
            raise BuildError(f"the oracle judged a node twice: {repeated[:8]}")
        object.__setattr__(self, "comparisons", tuple(sorted(resolved, key=lambda item: item.node_id)))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def agrees(self) -> bool:
        return all(item.matched for item in self.comparisons)

    @property
    def disagreements(self) -> tuple[NodeComparison, ...]:
        return tuple(item for item in self.comparisons if not item.matched)

    @property
    def byte_exact(self) -> tuple[str, ...]:
        return tuple(sorted(item.node_id for item in self.comparisons if item.mode == "EXACT"))

    @property
    def equivalence_only(self) -> tuple[str, ...]:
        return tuple(sorted(item.node_id for item in self.comparisons if item.mode == "EQUIVALENCE"))

    @property
    def text(self) -> str:
        head = (
            f"incremental build agrees with the admitted full build over {len(self.comparisons)} node(s): "
            f"{len(self.byte_exact)} compared by exact digest, {len(self.equivalence_only)} by causal equivalence"
        )
        return "\n".join([head, *(f"  {item.node_id}: " + "; ".join(item.reasons) for item in self.comparisons)])

    def at(self, node_id: str) -> NodeComparison:
        wanted = require_identifier(node_id, "node_id")
        for item in self.comparisons:
            if item.node_id == wanted:
                return item
        raise BuildError(f"the oracle says nothing about {wanted}")


def _appears_in(items: Sequence[NodeComparison], node_id: str) -> int:
    return sum(1 for item in items if item.node_id == node_id)


def verify_incremental(
    plan: BuildPlan,
    *,
    produced: Mapping[str, str],
    reference: Mapping[str, str],
    fingerprints: Mapping[str, CausalFingerprint] | None = None,
    reference_fingerprints: Mapping[str, CausalFingerprint] | None = None,
) -> IncrementalVerdict:
    """Judge an incremental run against a clean full build, node by node.

    The rule the module spec is strict about is the one this function exists to
    enforce: exact digest equality is demanded only of nodes whose reproducibility
    class actually claims byte identity. Demanding it of a stochastic node would
    report a false failure; not demanding it of a deterministic one would hide a
    stale reuse, so the two claims are kept apart and named in the verdict.
    """

    wanted = BuildPlan.coerce(plan, "plan")
    given = {require_identifier(key, "produced.key"): require_digest(value, "produced") for key, value in produced.items()}
    clean = {require_identifier(key, "reference.key"): require_digest(value, "reference") for key, value in reference.items()}
    comparisons: list[NodeComparison] = []
    for step in wanted.steps:
        node_id = step.node_id
        mine = given.get(node_id)
        theirs = clean.get(node_id)
        if step.blocked:
            comparisons.append(
                NodeComparison(
                    node_id=node_id,
                    mode="REFUSED",
                    disposition=step.disposition,
                    reproducibility=step.reproducibility,
                    reasons=("the step was blocked, so the oracle cannot judge work that was never run",),
                )
            )
            continue
        if step.is_reuse:
            served = step.receipt.result_digest
            if mine is not None and mine != served:
                comparisons.append(
                    NodeComparison(
                        node_id=node_id,
                        mode="EXACT" if step.claims_byte_identity else "EQUIVALENCE",
                        disposition=step.disposition,
                        reproducibility=step.reproducibility,
                        incremental_digest=mine,
                        reference_digest=served,
                        matched=False,
                        reasons=(
                            f"the receipt admitted {served[:12]} but {mine[:12]} was handed out, so the "
                            "cache served bytes its own admission never covered",
                        ),
                    )
                )
                continue
        if step.claims_byte_identity:
            if mine is None or theirs is None:
                comparisons.append(
                    NodeComparison(
                        node_id=node_id,
                        mode="EXACT",
                        disposition=step.disposition,
                        reproducibility=step.reproducibility,
                        incremental_digest=mine,
                        reference_digest=theirs,
                        matched=False,
                        reasons=(
                            f"{step.reproducibility} must be compared by exact digest and one side named "
                            "no bytes, so equality cannot be claimed",
                        ),
                    )
                )
                continue
            same = mine == theirs
            comparisons.append(
                NodeComparison(
                    node_id=node_id,
                    mode="EXACT",
                    disposition=step.disposition,
                    reproducibility=step.reproducibility,
                    incremental_digest=mine,
                    reference_digest=theirs,
                    matched=same,
                    reasons=(
                        f"{step.disposition.value} reproduced the full build's bytes exactly"
                        if same
                        else f"{step.disposition.value} produced {mine[:12]} where the full build produced "
                        f"{theirs[:12]}: the increment missed something the delta said was dirty",
                    ),
                )
            )
            continue
        moved = _fingerprint_difference(step, fingerprints, reference_fingerprints)
        stale = sorted({item for item in moved if item.startswith("input.")})
        comparisons.append(
            NodeComparison(
                node_id=node_id,
                mode="EQUIVALENCE",
                disposition=step.disposition,
                reproducibility=step.reproducibility,
                incremental_digest=mine,
                reference_digest=theirs,
                matched=not stale,
                reasons=_equivalence_reasons(step, stale),
            )
        )
    return IncrementalVerdict(
        graph_id=wanted.graph_id,
        plan_digest=wanted.digest(),
        comparisons=tuple(comparisons),
    )


def _equivalence_reasons(step: "BuildStep", stale: Sequence[str]) -> tuple[str, ...]:
    """The judgement a non-byte-claiming node gets, and the stale inputs it did not get."""

    if not stale:
        return (
            f"{step.reproducibility} does not claim byte identity, so equal digests are not demanded; "
            "its causal inputs are unchanged and its evidence is current",
        )
    return (
        f"{step.reproducibility} does not claim byte identity: equal digests are not demanded, but the "
        "increment consumed inputs the full build did not have",
        *(f"stale dependency consumed: {item}" for item in stale),
    )


def _fingerprint_difference(
    step: BuildStep,
    fingerprints: Mapping[str, CausalFingerprint] | None,
    reference: Mapping[str, CausalFingerprint] | None,
) -> tuple[str, ...]:
    """Which causal components the incremental run saw that the full build did not."""

    if not fingerprints or not reference:
        return ()
    mine = fingerprints.get(step.node_id)
    theirs = reference.get(step.node_id)
    if mine is None or theirs is None:
        return ()
    return mine.differs_from(theirs)


@dataclass(frozen=True)
class ShadowResult(Record):
    """One apparently-clean node that was rebuilt anyway, and what the rebuild said."""

    node_id: str
    cached_digest: str
    rebuilt_digest: str
    reproducibility: Any = None
    key_digest: Any = None
    reused: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        for name in ("cached_digest", "rebuilt_digest"):
            object.__setattr__(self, name, require_digest(getattr(self, name), name))
        if self.reproducibility is not None:
            object.__setattr__(
                self,
                "reproducibility",
                ReproducibilityClass.parse(self.reproducibility, "reproducibility").value,
            )
        if self.key_digest is not None:
            object.__setattr__(self, "key_digest", require_digest(self.key_digest, "key_digest"))
        if not isinstance(self.reused, bool):
            raise SchemaValidationError("reused must be a boolean")

    @property
    def matched(self) -> bool:
        return self.cached_digest == self.rebuilt_digest

    @property
    def claims_bytes(self) -> bool:
        return (
            self.reproducibility is None
            or ReproducibilityClass(self.reproducibility).claims_byte_identity
        )

    @property
    def indicts(self) -> bool:
        """A mismatch only condemns the cache for a node that claims byte identity."""

        return not self.matched and self.claims_bytes

    @property
    def text(self) -> str:
        verdict = "agreed" if self.matched else "DIFFERED"
        return (
            f"{self.node_id} shadow rebuild {verdict}: cached {self.cached_digest[:12]} against "
            f"rebuilt {self.rebuilt_digest[:12]}"
            + ("" if self.claims_bytes else " (stochastic: bytes are not a verdict)")
        )


@dataclass(frozen=True)
class ShadowAudit(Record):
    """The sample of clean nodes that were rebuilt anyway, and what it found.

    Shadow rebuilds are how under-invalidation is detected before a release ships a
    stale render: the sample proves the frontier's "clean" verdicts against work the
    planner did not think it needed.
    """

    graph_id: str
    plan_digest: str
    results: tuple[ShadowResult, ...] = ()
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        object.__setattr__(self, "plan_digest", require_digest(self.plan_digest, "plan_digest"))
        collected = require_bounded(self.results, "results", maximum=MAX_BUILD_PLAN_STEPS, kind="result")
        resolved = tuple(ShadowResult.coerce(item, "results[]") for item in collected)
        repeated = sorted({item.node_id for item in resolved if _shadow_for(resolved, item.node_id) > 1})
        if repeated:
            raise BuildError(f"a shadow audit sampled one node twice: {repeated[:8]}")
        object.__setattr__(self, "results", tuple(sorted(resolved, key=lambda item: item.node_id)))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def sampled(self) -> int:
        return len(self.results)

    @property
    def indictments(self) -> tuple[ShadowResult, ...]:
        return tuple(item for item in self.results if item.indicts)

    @property
    def noisy(self) -> tuple[ShadowResult, ...]:
        """Differed, but the node never promised identical bytes. Not a cache bug."""

        return tuple(item for item in self.results if not item.matched and not item.indicts)

    @property
    def clean(self) -> bool:
        return not self.indictments

    def widening(self, entries: Iterable[Any]) -> tuple[Any, ...]:
        """The cache entries the indictments name, so quarantine can act on them."""

        accused = {item.node_id for item in self.indictments} | {
            item.key_digest for item in self.indictments if item.key_digest
        }
        found = []
        for claimed in entries:
            entry = CacheEntry.coerce(claimed, "entries[]")
            if entry.key.node_id in accused or entry.key.address in accused:
                found.append(entry)
        return tuple(found)

    @property
    def text(self) -> str:
        head = (
            f"shadow audit of {self.sampled} reused node(s): {len(self.indictments)} indictment(s), "
            f"{len(self.noisy)} non-byte-claiming difference(s)"
        )
        return "\n".join([head, *(f"  {item.text}" for item in self.results)])


def _shadow_for(items: Sequence[ShadowResult], node_id: str) -> int:
    return sum(1 for item in items if item.node_id == node_id)


def audit_shadow_rebuilds(
    plan: BuildPlan,
    results: Iterable[Any],
    *,
    reuse_only: bool = True,
) -> ShadowAudit:
    """Collect shadow rebuilds into a verdict bound to one plan digest."""

    wanted = BuildPlan.coerce(plan, "plan")
    resolved = tuple(ShadowResult.coerce(item, "results[]") for item in results)
    if reuse_only:
        decided = {item.node_id: item for item in wanted.steps}
        for item in resolved:
            step = decided.get(item.node_id)
            if step is None:
                raise BuildError(f"shadow result names {item.node_id}, which the plan does not decide")
            if not step.is_reuse:
                raise BuildError(
                    f"{item.node_id} was not a reuse step ({step.disposition.value}), so a shadow "
                    "rebuild of it proves nothing about the cache"
                )
    return ShadowAudit(
        graph_id=wanted.graph_id,
        plan_digest=wanted.digest(),
        results=resolved,
    )


@dataclass(frozen=True)
class VariantCandidate(Record):
    """One variant's request for the same node, with the key that decides sharing.

    Coalescing is only ever about work, never about results: two variants may share a
    render only when their causal, context and compatibility inputs are identical, so
    the candidate carries the key rather than a description of what it looks like.
    """

    variant_id: str
    node_id: str
    key: CacheKey
    fingerprint: Any = None
    label: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "variant_id", require_identifier(self.variant_id, "variant_id"))
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "key", CacheKey.coerce(self.key, "key"))
        if self.key.node_id != self.node_id:
            raise SchemaValidationError(
                f"variant {self.variant_id} asks for {self.node_id} but its key was derived for {self.key.node_id}"
            )
        if self.fingerprint is not None:
            object.__setattr__(self, "fingerprint", CausalFingerprint.coerce(self.fingerprint, "fingerprint"))
            if self.fingerprint.node_id != self.node_id:
                raise SchemaValidationError(
                    f"variant {self.variant_id} carries a fingerprint of {self.fingerprint.node_id}"
                )
        object.__setattr__(self, "label", require_optional_text(self.label, "label", maximum=128))

    @property
    def text(self) -> str:
        return f"{self.variant_id}:{self.node_id}={self.key.address[:12]}"


@dataclass(frozen=True)
class SharedWork(Record):
    """One unit of work several variants may pay for once."""

    node_id: str
    key_digest: str
    layer: Any = None
    variants: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "key_digest", require_digest(self.key_digest, "key_digest"))
        if self.layer is not None:
            object.__setattr__(self, "layer", CacheLayer.parse(self.layer, "layer").value)
        collected = require_bounded(self.variants, "variants", maximum=MAX_VARIANT_SELECTIONS)
        resolved = tuple(sorted({require_identifier(item, "variants[]") for item in collected}))
        if len(resolved) < 2:
            raise BuildError(
                f"{self.node_id} is shared by {len(resolved)} variant(s); one is not a batch"
            )
        object.__setattr__(self, "variants", resolved)

    @property
    def runs_saved(self) -> int:
        return len(self.variants) - 1

    @property
    def text(self) -> str:
        return f"{self.node_id} once for {', '.join(self.variants)} ({self.key_digest[:12]})"


@dataclass(frozen=True)
class CoalescedBatch(Record):
    """What a variant batch actually shares, and what it refuses to fuse."""

    graph_id: str
    shared: tuple[SharedWork, ...] = ()
    distinct: tuple[VariantCandidate, ...] = ()
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        shared_items = require_bounded(self.shared, "shared", maximum=MAX_VARIANT_SETS, kind="group")
        resolved = tuple(SharedWork.coerce(item, "shared[]") for item in shared_items)
        repeated = sorted({(item.node_id, item.key_digest) for item in resolved if _shared_for(resolved, item) > 1})
        if repeated:
            raise BuildError(f"one unit of shared work is listed twice: {repeated[:8]}")
        object.__setattr__(self, "shared", tuple(sorted(resolved, key=lambda item: (item.node_id, item.key_digest))))
        lone = require_bounded(self.distinct, "distinct", maximum=MAX_VARIANT_SELECTIONS, kind="candidate")
        candidates = tuple(VariantCandidate.coerce(item, "distinct[]") for item in lone)
        object.__setattr__(self, "distinct", tuple(sorted(candidates, key=lambda item: item.text)))
        paid = {(variant, item.node_id) for item in resolved for variant in item.variants}
        overlap = sorted({(item.variant_id, item.node_id) for item in candidates} & paid)
        if overlap:
            raise BuildError(
                f"{overlap[:6]} is asked to both join a shared run and pay for itself"
            )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def runs(self) -> int:
        return len(self.shared) + len(self.distinct)

    @property
    def requested(self) -> int:
        return sum(len(item.variants) for item in self.shared) + len(self.distinct)

    @property
    def runs_saved(self) -> int:
        return sum(item.runs_saved for item in self.shared)

    def groups_for(self, node_id: str) -> tuple[SharedWork, ...]:
        """Every shared run this node takes part in, which is more than one when variants split."""

        wanted = require_identifier(node_id, "node_id")
        return tuple(item for item in self.shared if item.node_id == wanted)

    @property
    def text(self) -> str:
        return (
            f"batch of {self.requested} variant task(s) runs as {self.runs}: "
            + ("; ".join(item.text for item in self.shared) or "nothing is shared")
        )


def _shared_for(items: Sequence[SharedWork], group: SharedWork) -> int:
    return sum(1 for item in items if (item.node_id, item.key_digest) == (group.node_id, group.key_digest))


def coalesce_variants(graph_id: str, candidates: Iterable[Any]) -> CoalescedBatch:
    """Group variant work that is provably the same work, and nothing else.

    Grouping is by the cache key's own address: same node, same causal fingerprint,
    same context, same compatibility. Everything else runs separately, because fusing
    two variants whose prefixes merely look similar is how a batch ends up shipping
    one language in four aspect ratios.
    """

    wanted = require_identifier(graph_id, "graph_id")
    resolved = tuple(VariantCandidate.coerce(item, "candidates[]") for item in candidates)
    if not resolved:
        raise BuildError("variant coalescing with no candidates describes an empty batch")
    identities = {(item.variant_id, item.node_id) for item in resolved}
    if len(identities) != len(resolved):
        raise BuildError("a variant may ask for one node once per batch")
    grouped: dict[tuple[str, str], list[VariantCandidate]] = {}
    for item in resolved:
        grouped.setdefault((item.node_id, item.key.address), []).append(item)
    shared: list[SharedWork] = []
    distinct: list[VariantCandidate] = []
    for (node_id, address), group in sorted(grouped.items()):
        if len(group) > 1:
            shared.append(
                SharedWork(
                    node_id=node_id,
                    key_digest=address,
                    layer=group[0].key.layer,
                    variants=tuple(item.variant_id for item in group),
                )
            )
            continue
        distinct.append(group[0])
    return CoalescedBatch(graph_id=wanted, shared=tuple(shared), distinct=tuple(distinct))


@dataclass(frozen=True)
class CacheLookup(Record):
    """What one node asked the cache for, and whether the shield answered yes.

    Held as a record so a plan can be re-examined without the cache: the rejection
    text is the only trace of a miss that says what to fix.
    """

    node_id: str
    key: CacheKey
    outcome: Any
    entry: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "key", CacheKey.coerce(self.key, "key"))
        if self.key.node_id != self.node_id:
            raise SchemaValidationError(
                f"the lookup for {self.node_id} used a key derived for {self.key.node_id}"
            )
        claimed = self.outcome
        if isinstance(claimed, ReuseReceipt):
            pass
        elif isinstance(claimed, ReuseRejection):
            pass
        elif isinstance(claimed, Mapping):
            try:
                claimed = ReuseReceipt.from_payload(claimed)
            except (SchemaValidationError, KeyError, TypeError):
                claimed = ReuseRejection.from_payload(claimed)
        else:
            raise SchemaValidationError(
                "outcome must be a ReuseReceipt or a ReuseRejection, got "
                + type(self.outcome).__name__
            )
        if claimed.node_id != self.node_id:
            raise SchemaValidationError(f"the cache answer belongs to {claimed.node_id}")
        object.__setattr__(self, "outcome", claimed)
        if self.entry is not None:
            object.__setattr__(self, "entry", CacheEntry.coerce(self.entry, "entry"))

    @property
    def admitted(self) -> bool:
        return isinstance(self.outcome, ReuseReceipt)

    @property
    def receipt(self) -> ReuseReceipt | None:
        return self.outcome if self.admitted else None

    @property
    def rejection(self) -> ReuseRejection | None:
        return None if self.admitted else self.outcome

    @property
    def text(self) -> str:
        return self.outcome.reason if self.admitted else self.outcome.text


def _layer_for(node: GraphNode) -> CacheLayer:
    """A delivery node's bytes are the product; everything else is an intermediate.

    The layer chooses which shield questions matter and what eviction may drop, so
    it is derived from the node's role rather than passed in per call.
    """

    return CacheLayer.FINAL if node.role is NodeRole.DELIVERY else CacheLayer.INTERMEDIATE


def _dependencies_of(definition: Any, node_id: str) -> tuple[str, ...]:
    """Upstream nodes this one waits for: anything that can carry work forward.

    Ordering and observation edges are excluded because they record sequence and
    provenance, not a dependency that can leave a consumer stale.
    """

    return tuple(
        sorted(
            {
                edge.source_node_id
                for edge in definition.edges_into(node_id)
                if not edge.kind.never_creates_rebuild_dependency
            }
        )
    )


def closure_of(fingerprint: CausalFingerprint) -> tuple[str, ...]:
    """The dependency closure a cache entry has to match, as stable text."""

    return tuple(
        sorted(
            f"{item.kind}={item.reference}"
            for item in fingerprint.components
            if item.kind.startswith("input.")
        )
    )


def _index_cache(cache: Any) -> Mapping[str, CacheEntry]:
    if cache is None:
        return {}
    if isinstance(cache, Mapping):
        collected = {
            require_identifier(key, "cache.key"): CacheEntry.coerce(value, "cache[]")
            for key, value in cache.items()
        }
    else:
        collected = {}
        for claimed in cache:
            entry = CacheEntry.coerce(claimed, "cache[]")
            collected[entry.key.node_id] = entry
    for node_id, entry in collected.items():
        if entry.key.node_id != node_id:
            raise BuildError(
                f"the cache entry for {node_id} is keyed to {entry.key.node_id}; the store and the "
                "caller disagree about who owns this row"
            )
    return collected


def _state_of(
    node: GraphNode,
    dirty: DirtyNode | None,
    *,
    materialized: bool,
    unresolved: bool,
    explicit: Any,
) -> tuple[BuildState, tuple[str, ...]]:
    """Which state a node is in, and the sentences that say so.

    The order is the policy: a node whose inputs are not even bound cannot be spoken
    about, so it is UNKNOWN whatever the delta says; a node the caller named gets that
    state; otherwise the delta decides, and only then does absence of a cause mean clean.
    """

    reasons: list[str] = []
    if explicit is not None:
        reasons.append(f"the caller stated {node.node_id} as {BuildState.parse(explicit, 'states[]').value}")
    if unresolved:
        return BuildState.UNKNOWN, (*reasons, f"{node.node_id} has material inputs that bind to nothing")
    if explicit is not None:
        return BuildState.parse(explicit, "states[]"), tuple(reasons)
    if dirty is not None:
        return dirty.state, dirty.reasons
    if not materialized:
        return (
            BuildState.DIRTY,
            (f"{node.node_id} declares no materialization, so there is nothing to compare or reuse",),
        )
    return BuildState.CLEAN, (f"{node.node_id} is outside the impact cone of every stated change",)


def _facet_disposition(
    node: GraphNode, facets: Sequence[DependencyFacet], state: BuildState
) -> tuple[BuildState, str | None]:
    """Downgrade a material change to revalidation or repackaging where that is all it is.

    A quality decision that moved does not make a render stale, and a delivery policy
    that moved does not make a master file stale. Treating either as ``CONTENT`` work
    would be correct but dishonest about the cost, and it is exactly the modelling
    mistake that makes an incremental build look slow and a full build look obvious.
    """

    if state is not BuildState.DIRTY or not facets:
        return state, None
    named = set(facets)
    if node.role is NodeRole.DELIVERY and named & {DependencyFacet.RIGHTS, DependencyFacet.PROVENANCE}:
        return BuildState.BLOCKED, (
            "a delivery node whose rights or provenance moved must be re-cleared before it ships"
        )
    if named == _REPACKAGING_FACETS:
        return BuildState.REPACKAGE_ONLY, "only the delivery policy moved, so the bytes stay and the package changes"
    if named and named <= _REVALIDATING_FACETS:
        return (
            BuildState.REVALIDATE_ONLY,
            "only evidence moved, so the output is re-attested rather than re-rendered",
        )
    return state, None


def _planned_nodes(
    bound: MaterializationGraph,
    frontier: DirtyFrontier,
    declared: Mapping[str, Any],
    unresolved: set[str],
) -> set[str]:
    """The nodes a plan will speak about, decided before any cache work runs.

    A plan carries only work, so a clean prerequisite is deliberately absent from it.
    Steps still have to know that, because a dependency nobody decided on is exactly
    the dangling edge a plan is supposed to refuse.
    """

    planned: set[str] = set()
    for node in bound.revision.definition.nodes:
        node_id = node.node_id
        if node_id in unresolved:
            planned.add(node_id)
            continue
        dirty = frontier.at(node_id)
        state, _reasons = _state_of(
            node,
            dirty,
            materialized=bound.materialization_of_first(node_id) is not None,
            unresolved=False,
            explicit=declared.get(node_id),
        )
        state, _downgrade = _facet_disposition(
            node, tuple(dirty.facets) if dirty is not None else (), state
        )
        if state is not BuildState.CLEAN:
            planned.add(node_id)
    return planned


def _execution_order(definition: Any, planned: set[str]) -> tuple[str, ...]:
    """Planned nodes with every producer before the consumers that wait for it.

    The cache question a node asks depends on whether its inputs are about to write new
    bytes, so the plan is decided in this order rather than in declaration order. A
    feedback edge is the one case where no such order exists; a node caught in that
    cycle keeps the definition's own position, and the plan refuses itself later.
    """

    ordered: list[str] = []
    placed: set[str] = set()
    for root in (item.node_id for item in definition.nodes if item.node_id in planned):
        if root in placed:
            continue
        pending: list[tuple[str, bool]] = [(root, False)]
        on_path: set[str] = set()
        while pending:
            node_id, expanded = pending.pop()
            if expanded:
                on_path.discard(node_id)
                if node_id not in placed:
                    placed.add(node_id)
                    ordered.append(node_id)
                continue
            if node_id in placed or node_id in on_path:
                continue
            on_path.add(node_id)
            pending.append((node_id, True))
            for dependency in reversed(_dependencies_of(definition, node_id)):
                if dependency in planned:
                    pending.append((dependency, False))
    return tuple(ordered)


def _left_out_note(nodes: Sequence[str]) -> tuple[str, ...]:
    """Say out loud that a step's upstream prerequisite is absent from the plan."""

    if not nodes:
        return ()
    named = ", ".join(nodes[:4]) + (" and others" if len(nodes) > 4 else "")
    return (
        f"{named} sits upstream and needs no work, so it is outside this plan instead of being "
        "listed as a no-op",
    )


def plan_build(
    bound: MaterializationGraph,
    *,
    delta: BuildDelta | None = None,
    cache: Any = (),
    trust: Any = None,
    project_id: str = "iris",
    context: ContextFingerprint | None = None,
    fingerprint_context: Any = None,
    now_ms: int = 0,
    rights_digest: str | None = None,
    provenance_digest: str | None = None,
    environment_fingerprint: str | None = None,
    required_quality_class: Any = None,
    qualified_evaluators: Iterable[Any] = (),
    repair_slices: Mapping[str, Any] | None = None,
    whole_node_repairs: Iterable[str] = (),
    partial_commit: Iterable[str] = (),
    states: Mapping[str, Any] | None = None,
    quarantine: Any = None,
    protected_identity: bool = False,
) -> BuildPlan:
    """Decide every node the build has to speak about, and why.

    This is the one function that turns the whole of area D into an answer: causes in,
    dispositions out, with a cache claim admitted per node through the shield in
    :mod:`iris_project_os.reuse`. Nodes that are demonstrably untouched are left out of
    the plan rather than listed as no-ops, so a plan is a statement of work and not an
    inventory.
    """

    if not isinstance(bound, MaterializationGraph):
        raise SchemaValidationError("plan_build requires a bound MaterializationGraph")
    definition = bound.revision.definition
    resolved_delta = BuildDelta.coerce(delta, "delta") if delta is not None else None
    cone = None if resolved_delta is None or resolved_delta.is_empty else impact_of(bound, resolved_delta.changes)
    frontier = (
        dirty_frontier(bound, resolved_delta, cone=cone, states=states)
        if resolved_delta is not None
        else DirtyFrontier(graph_id=definition.graph_id, delta_digest=content_digest([]))
    )
    if resolved_delta is None:
        for node_id, given in dict(states or {}).items():
            if BuildState.parse(given, "states[]") is not BuildState.CLEAN:
                frontier = _force_state(frontier, bound, node_id, given)
    repairs = repair_frontier(
        bound,
        frontier,
        slices=repair_slices,
        whole_node=whole_node_repairs,
    )
    entries = _index_cache(cache)
    policy = CacheTrust.coerce(trust) if trust is not None else None
    guarded = {require_identifier(item, "partial_commit[]") for item in partial_commit}
    unresolved = {edge.target_node_id for edge in bound.unresolved_inputs()}
    declared = dict(states or {})
    ghost = sorted({require_identifier(item, "states.key") for item in declared} - set(definition.node_index))
    if ghost:
        raise BuildError(
            f"states names nodes this graph does not declare: {ghost[:8]}; a decision about a node that "
            "is not in the graph cannot be checked, so it is refused instead of quietly dropped"
        )
    planned = _planned_nodes(bound, frontier, declared, unresolved)
    steps: list[BuildStep] = []
    emitting: set[str] = set()

    def record(step: BuildStep) -> None:
        """Keep the step and, if it writes bytes, remember that for its consumers."""

        steps.append(step)
        if step.emits_new_bytes:
            emitting.add(step.node_id)

    index = definition.node_index
    for node_id in _execution_order(definition, planned):
        node = index[node_id]
        waiting = _dependencies_of(definition, node_id)
        depends = tuple(item for item in waiting if item in planned)
        left_out = tuple(item for item in waiting if item not in planned)
        if node_id in unresolved:
            record(
                _blocked_step(
                    node_id,
                    BuildState.UNKNOWN,
                    depends,
                    (
                        f"{node_id} has an input edge that binds to no materialization, so the kernel "
                        "cannot say whether its stored bytes are current",
                        *_left_out_note(left_out),
                    ),
                )
            )
            continue
        dirty = frontier.at(node_id)
        materialized = bound.materialization_of_first(node_id) is not None
        state, reasons = _state_of(
            node, dirty, materialized=materialized, unresolved=False, explicit=declared.get(node_id)
        )
        facets = tuple(dirty.facets) if dirty is not None else ()
        state, downgrade = _facet_disposition(node, facets, state)
        if downgrade:
            reasons = (*reasons, downgrade)
        if state is BuildState.CLEAN:
            continue
        if state is BuildState.BLOCKED:
            record(_blocked_step(node_id, state, depends, (*reasons, *_left_out_note(left_out))))
            continue
        outputs = tuple(port.port_id for port in node.outputs)
        reasons = (*reasons, *_left_out_note(left_out))
        fingerprint = compute_fingerprint(bound, node_id, context=fingerprint_context)
        if state is BuildState.DIRTY:
            claimed = entries.get(node_id)
            if claimed is not None:
                standing_on = tuple(sorted(set(depends) & emitting))
                if standing_on:
                    # The entry matches the graph as it stands now, and the graph is about
                    # to change under this node. Asking for the hit would be a plan that
                    # BuildPlan itself refuses, so the cache is never asked at all.
                    reasons = (
                        *reasons,
                        f"the cache entry for {node_id} is not asked, because {', '.join(standing_on[:4])} "
                        "will emit new bytes and this node's key was derived over the inputs it has now",
                    )
                    claimed = None
            wanted_key = None
            if claimed is not None:
                request = ReuseRequest(
                    node_id=node_id,
                    key=CacheKey.of(
                        node_id,
                        build_fingerprint=fingerprint.fingerprint,
                        context=context,
                        layer=_layer_for(node),
                    ),
                    project_id=project_id,
                    now_ms=now_ms,
                    closure_digest=content_digest(list(closure_of(fingerprint))),
                    rights_digest=rights_digest,
                    provenance_digest=provenance_digest,
                    environment_fingerprint=environment_fingerprint,
                    required_quality_class=required_quality_class,
                    qualified_evaluators=qualified_evaluators,
                    protected_identity=protected_identity,
                )
                verdict = admit_reuse(
                    claimed, request, trust=policy, quarantine=quarantine
                )
                wanted_key = request.key
                lookup = CacheLookup(node_id=node_id, key=request.key, outcome=verdict, entry=claimed)
                if lookup.admitted:
                    granted = lookup.receipt
                    if granted.satisfies_output:
                        record(
                            BuildStep(
                                node_id=node_id,
                                state=BuildState.CACHED_ELIGIBLE,
                                disposition=WorkDisposition.REUSE,
                                reasons=(
                                    *reasons,
                                    f"cache at {_layer_for(node).label} admitted: {granted.reason}",
                                ),
                                depends_on=depends,
                                outputs=outputs,
                                facets=facets,
                                key=request.key,
                                receipt=granted,
                                fingerprint=fingerprint,
                                reproducibility=node.reproducibility,
                                commit_mode=_commit_mode(node_id, outputs, guarded),
                            )
                        )
                        continue
                    # A partial hit is real but does not finish the node, so it is recorded
                    # as a reason and the node is planned for the work it still owes.
                    reasons = (
                        *reasons,
                        f"cache admitted {granted.reuse_class.value} which does not satisfy this node's "
                        f"output, so the node still runs: {granted.reason}",
                    )
                    rejection = None
                else:
                    reasons = (*reasons, f"cache refused: {lookup.rejection.text}")
                    rejection = lookup.rejection
            else:
                rejection = None
            if dirty is not None and repairs.settles(dirty):
                target = repairs.target_for(node_id)
                record(
                    BuildStep(
                        node_id=node_id,
                        state=state,
                        disposition=WorkDisposition.REPAIR,
                        reasons=(*reasons, f"bounded repair of {target.slice.text}"),
                        depends_on=depends,
                        outputs=outputs,
                        facets=facets,
                        slice=target.slice,
                        fingerprint=fingerprint,
                        reproducibility=node.reproducibility,
                        commit_mode=_commit_mode(node_id, outputs, guarded),
                    )
                )
                continue
            record(
                BuildStep(
                    node_id=node_id,
                    state=state,
                    disposition=WorkDisposition.REBUILD,
                    reasons=reasons,
                    depends_on=depends,
                    outputs=outputs,
                    facets=facets,
                    key=wanted_key,
                    rejection=rejection,
                    fingerprint=fingerprint,
                    reproducibility=node.reproducibility,
                    commit_mode=_commit_mode(node_id, outputs, guarded),
                )
            )
            continue
        if state is BuildState.REPACKAGE_ONLY and not outputs:
            record(
                _blocked_step(
                    node_id,
                    BuildState.BLOCKED,
                    depends,
                    (*reasons, "repackaging was chosen but the node emits no output port"),
                )
            )
            continue
        disposition = {
            BuildState.REVALIDATE_ONLY: WorkDisposition.REVALIDATE,
            BuildState.REPACKAGE_ONLY: WorkDisposition.REPACKAGE,
        }[state]
        record(
            BuildStep(
                node_id=node_id,
                state=state,
                disposition=disposition,
                reasons=reasons,
                depends_on=depends,
                outputs=outputs,
                facets=facets,
                fingerprint=fingerprint,
                reproducibility=node.reproducibility,
                commit_mode=_commit_mode(node_id, outputs, guarded),
            )
        )
    base, target = _plan_revisions(bound, resolved_delta)
    return BuildPlan(
        plan_id=new_id(),
        graph_id=definition.graph_id,
        base_revision=base,
        target_revision=target,
        steps=tuple(steps),
        delta_digest=None if resolved_delta is None else resolved_delta.delta_digest,
        created_at_ms=now_ms,
    )


def _plan_revisions(bound: MaterializationGraph, delta: BuildDelta | None) -> tuple[ExternalRef, ExternalRef]:
    current = ExternalRef(
        kind=EntityKind.REVISION,
        reference=bound.revision.revision_id,
        version=bound.revision.definition.graph_id,
    )
    if delta is None:
        return current, current
    return delta.base_revision, delta.target_revision


def _force_state(frontier: DirtyFrontier, bound: MaterializationGraph, node_id: str, given: Any) -> DirtyFrontier:
    """Add a caller-named node to the frontier, with the state as its only cause."""

    wanted = require_identifier(node_id, "states.key")
    if frontier.at(wanted) is not None:
        return frontier
    return DirtyFrontier(
        graph_id=frontier.graph_id,
        delta_digest=frontier.delta_digest,
        nodes=tuple(
            sorted(
                (*frontier.nodes, DirtyNode(node_id=wanted, reasons=(f"the caller stated {given}",), state=given)),
                key=lambda item: item.node_id,
            )
        ),
    )


def _commit_mode(node_id: str, outputs: tuple[str, ...], guarded: set[str]) -> OutputCommitMode:
    """Multi-output nodes commit as one set unless the caller accepts partial results."""

    if node_id in guarded:
        return OutputCommitMode.PARTIAL
    return OutputCommitMode.ATOMIC if len(outputs) > 1 else OutputCommitMode.PARTIAL


def _blocked_step(node_id: str, state: BuildState, depends: tuple[str, ...], reasons: Sequence[str]) -> BuildStep:
    return BuildStep(
        node_id=node_id,
        state=state,
        disposition=WorkDisposition.BLOCK,
        reasons=tuple(reasons) or (f"{node_id} is {state.value} and cannot be decided",),
        depends_on=depends,
    )
