"""M02 area C (merge): three-way semantic merge, typed conflicts and transplant.

Merge here is object-level and semantic: a base snapshot, a target head and a
source head, combined through their closure manifests. Binary media is never
"merged" by averaging bytes, because two competing renders of the same logo are
not two halves of one answer; the only legal outcomes are explicit selection,
recomposition or regeneration, and that constraint shapes the whole module.

Conflicts fall into the ten families the frozen contract names, and each family
declares which resolution strategies exist for it. Unknown families are refused
rather than folded into a catch-all, so a reviewer is never handed a "miscellaneous"
problem they cannot reason about. A blocking conflict that is still unresolved makes
advancing a branch head impossible at the record level, not merely inadvisable: a
merge receipt refuses to name a result snapshot while blocking work remains open.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping, Sequence

from .base import Labeled, Record, encode_payload, of
from .branching import (
    VariantSelection,
    resolve_selection,
    selection_rulings,
)
from .diffing import DiffEntry, semantic_diff
from .errors import (
    GraphValidationError,
    MergeBlockedError,
    SchemaValidationError,
    SnapshotClosureError,
)
from .graph import (
    GraphDefinition,
    GraphEdge,
    GraphRevision,
    MaterializationGraph,
    MaterializationRecord,
    PortDirection,
)
from .identity import EntityKind, ExternalRef, TransitionReceipt, new_id, require_id
from .limits import (
    MAX_CONFLICTS,
    MAX_CLOSURE_REFS,
    MAX_IMPACT_NODES,
    MAX_MERGE_INPUT_NODES,
)
from .snapshots import (
    ProductionDelta,
    Snapshot,
    SnapshotClass,
    SnapshotClosureManifest,
    SnapshotDerivation,
    SnapshotStore,
    commit_snapshot,
    closure_obligations,
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
    "ConflictKind",
    "ResolutionStrategy",
    "MergeConflict",
    "Resolution",
    "MergeReceipt",
    "three_way_merge",
    "transplant",
    "advance_merge",
]


class ResolutionStrategy(Labeled):
    """The legal ways to settle one conflict of a given family."""

    KEEP_TARGET = "KEEP_TARGET"
    TAKE_SOURCE = "TAKE_SOURCE"
    EXPLICIT_CHOICE = "EXPLICIT_CHOICE"
    RECOMPOSE = "RECOMPOSE"
    MIGRATE_IDENTITY = "MIGRATE_IDENTITY"
    COMPENSATE = "COMPENSATE"
    RECONCILE = "RECONCILE"
    REVALIDATE = "REVALIDATE"
    DEFER = "DEFER"

    @property
    def needs_evidence(self) -> bool:
        """Strategies that assert something happened must point at the receipt."""

        return self in {
            ResolutionStrategy.EXPLICIT_CHOICE,
            ResolutionStrategy.RECOMPOSE,
            ResolutionStrategy.MIGRATE_IDENTITY,
            ResolutionStrategy.COMPENSATE,
            ResolutionStrategy.RECONCILE,
            ResolutionStrategy.REVALIDATE,
        }

    @property
    def settles(self) -> bool:
        return self is not ResolutionStrategy.DEFER


class ConflictKind(Labeled):
    """The ten families a semantic merge can disagree about. Unknown ones fail closed."""

    TOPOLOGY_CONFLICT = "TOPOLOGY_CONFLICT"
    NODE_DEFINITION_CONFLICT = "NODE_DEFINITION_CONFLICT"
    ARTIFACT_REVISION_CONFLICT = "ARTIFACT_REVISION_CONFLICT"
    VARIANT_SELECTION_CONFLICT = "VARIANT_SELECTION_CONFLICT"
    VARIANT_CONSTRAINT_CONFLICT = "VARIANT_CONSTRAINT_CONFLICT"
    IDENTITY_ANCHOR_CONFLICT = "IDENTITY_ANCHOR_CONFLICT"
    QUALITY_POLICY_CONFLICT = "QUALITY_POLICY_CONFLICT"
    RIGHTS_PROVENANCE_CONFLICT = "RIGHTS_PROVENANCE_CONFLICT"
    DELIVERY_RELEASE_CONFLICT = "DELIVERY_RELEASE_CONFLICT"
    SIDE_EFFECT_CONFLICT = "SIDE_EFFECT_CONFLICT"

    @property
    def blocking_by_default(self) -> bool:
        """Only a variant choice may be carried forward unreviewed.

        Two lines picking different options of the same set disagree about a
        switchable alternative that both still hold: the omitted option costs a
        re-render, not the loss of meaning or of a granted legal standing. Every
        other family here changes what the production *is*, what M01 judged, or what
        rights and releases were already given, so it must be settled first.
        """

        return self is not ConflictKind.VARIANT_SELECTION_CONFLICT

    @property
    def strategies(self) -> tuple[ResolutionStrategy, ...]:
        return _STRATEGIES[self]


_ALL = (
    ResolutionStrategy.KEEP_TARGET,
    ResolutionStrategy.TAKE_SOURCE,
    ResolutionStrategy.EXPLICIT_CHOICE,
)

_STRATEGIES = {
    ConflictKind.TOPOLOGY_CONFLICT: (
        ResolutionStrategy.KEEP_TARGET,
        ResolutionStrategy.TAKE_SOURCE,
        ResolutionStrategy.RECOMPOSE,
        ResolutionStrategy.DEFER,
    ),
    ConflictKind.NODE_DEFINITION_CONFLICT: _ALL + (ResolutionStrategy.RECOMPOSE,),
    ConflictKind.ARTIFACT_REVISION_CONFLICT: _ALL + (ResolutionStrategy.RECOMPOSE,),
    ConflictKind.VARIANT_SELECTION_CONFLICT: _ALL,
    ConflictKind.VARIANT_CONSTRAINT_CONFLICT: (
        ResolutionStrategy.KEEP_TARGET,
        ResolutionStrategy.TAKE_SOURCE,
        ResolutionStrategy.EXPLICIT_CHOICE,
    ),
    ConflictKind.IDENTITY_ANCHOR_CONFLICT: (
        ResolutionStrategy.KEEP_TARGET,
        ResolutionStrategy.MIGRATE_IDENTITY,
    ),
    ConflictKind.QUALITY_POLICY_CONFLICT: (
        ResolutionStrategy.KEEP_TARGET,
        ResolutionStrategy.TAKE_SOURCE,
        ResolutionStrategy.REVALIDATE,
    ),
    ConflictKind.RIGHTS_PROVENANCE_CONFLICT: _ALL,
    ConflictKind.DELIVERY_RELEASE_CONFLICT: (
        ResolutionStrategy.KEEP_TARGET,
        ResolutionStrategy.TAKE_SOURCE,
    ),
    ConflictKind.SIDE_EFFECT_CONFLICT: (
        ResolutionStrategy.KEEP_TARGET,
        ResolutionStrategy.COMPENSATE,
        ResolutionStrategy.RECONCILE,
    ),
}

_REF_GROUPS = (
    "quality_decisions",
    "rights_refs",
    "provenance_refs",
    "delivery_refs",
    "policy_refs",
    "environment_refs",
    "tool_refs",
    "model_refs",
)

_KIND_OF_LABEL = {
    "node": ConflictKind.NODE_DEFINITION_CONFLICT,
    "edge": ConflictKind.TOPOLOGY_CONFLICT,
    "interface": ConflictKind.TOPOLOGY_CONFLICT,
    "declared": ConflictKind.RIGHTS_PROVENANCE_CONFLICT,
    "admission": ConflictKind.TOPOLOGY_CONFLICT,
    "revision": ConflictKind.ARTIFACT_REVISION_CONFLICT,
    "variant": ConflictKind.VARIANT_SELECTION_CONFLICT,
    "variant-set": ConflictKind.TOPOLOGY_CONFLICT,
    "variant-constraint": ConflictKind.VARIANT_CONSTRAINT_CONFLICT,
    "identity-anchor": ConflictKind.IDENTITY_ANCHOR_CONFLICT,
    "quality_decisions": ConflictKind.QUALITY_POLICY_CONFLICT,
    "rights_refs": ConflictKind.RIGHTS_PROVENANCE_CONFLICT,
    "provenance_refs": ConflictKind.RIGHTS_PROVENANCE_CONFLICT,
    "delivery_refs": ConflictKind.DELIVERY_RELEASE_CONFLICT,
    "policy_refs": ConflictKind.DELIVERY_RELEASE_CONFLICT,
    "environment_refs": ConflictKind.DELIVERY_RELEASE_CONFLICT,
    "tool_refs": ConflictKind.DELIVERY_RELEASE_CONFLICT,
    "model_refs": ConflictKind.DELIVERY_RELEASE_CONFLICT,
    "intent": ConflictKind.QUALITY_POLICY_CONFLICT,
    "environment": ConflictKind.DELIVERY_RELEASE_CONFLICT,
}

_CATALOGUE_FIELD = {
    "variant-set": "variant_sets",
    "variant-constraint": "variant_constraints",
    "identity-anchor": "identity_anchors",
}

# What kind of disagreement each address in a selection ruling names. An axis choice
# and an identity migration are settled by different procedures, so the family cannot
# come from the ruling text; it comes from what the ruling points at.
_ADDRESS_KIND = {
    "variant": ConflictKind.VARIANT_SELECTION_CONFLICT,
    "variant-set": ConflictKind.VARIANT_CONSTRAINT_CONFLICT,
    "variant-constraint": ConflictKind.VARIANT_CONSTRAINT_CONFLICT,
    "anchor": ConflictKind.IDENTITY_ANCHOR_CONFLICT,
}


def _side(value: Any) -> str | None:
    """A readable side for short values, a digest for anything carrying a record."""

    if value is None:
        return None
    if isinstance(value, ExternalRef):
        return value.text
    if isinstance(value, str):
        return require_text(value, "side", maximum=512)
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return "digest:" + content_digest(encode_payload(value))
    return str(value)


@dataclass(frozen=True)
class MergeConflict(Record):
    """One disagreement, with all three sides recorded so the choice is auditable."""

    conflict_id: str
    kind: ConflictKind
    subject: str
    base_side: Any = None
    target_side: Any = None
    source_side: Any = None
    node_ids: tuple[str, ...] = ()
    blocking: Any = None
    explanation: Any = None
    resolution: Any = None
    resolution_ref: Any = None
    resolved_by: Any = None
    contract_version: str = CONTRACT_VERSION

    NESTED = {"resolution_ref": of(ExternalRef), "resolved_by": of(ComponentVersion)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "conflict_id", require_id(self.conflict_id, "conflict_id"))
        object.__setattr__(self, "kind", ConflictKind.parse(self.kind, "kind"))
        object.__setattr__(self, "subject", require_text(self.subject, "subject", maximum=1024))
        for name in ("base_side", "target_side", "source_side"):
            object.__setattr__(self, name, _side(getattr(self, name)))
        nodes = require_bounded(self.node_ids, "node_ids", maximum=MAX_IMPACT_NODES, kind="node id")
        object.__setattr__(
            self, "node_ids", tuple(sorted({require_identifier(item, "node_ids[]") for item in nodes}))
        )
        if self.blocking is None:
            object.__setattr__(self, "blocking", self.kind.blocking_by_default)
        if not isinstance(self.blocking, bool):
            raise SchemaValidationError("blocking must be a boolean or None")
        object.__setattr__(
            self, "explanation", require_optional_text(self.explanation, "explanation", maximum=1024)
        )
        for name in ("resolution_ref",):
            value = getattr(self, name)
            if value is not None and not isinstance(value, ExternalRef):
                raise SchemaValidationError(f"{name} must be an ExternalRef or None")
        if self.resolved_by is not None:
            object.__setattr__(self, "resolved_by", require_component_version(self.resolved_by, "resolved_by"))
        if self.resolution is not None:
            chosen = ResolutionStrategy.parse(self.resolution, "resolution")
            object.__setattr__(self, "resolution", chosen)
            if chosen not in self.kind.strategies:
                raise MergeBlockedError(
                    f"{self.kind.value} may only be settled by "
                    + ", ".join(item.value for item in self.kind.strategies)
                    + f", not {chosen.value}"
                )
            if chosen.needs_evidence and self.resolution_ref is None:
                raise MergeBlockedError(
                    f"resolution {chosen.value} of {self.kind.value} on {self.subject} asserts work "
                    "that has to be evidenced by a receipt"
                )
            if chosen.settles and chosen is not ResolutionStrategy.KEEP_TARGET and self.resolved_by is None:
                raise SchemaValidationError(
                    f"resolution {chosen.value} must record which actor or component settled it"
                )
            if chosen is ResolutionStrategy.DEFER and self.blocking:
                raise MergeBlockedError(
                    f"{self.kind.value} on {self.subject} is blocking and cannot be deferred"
                )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def is_resolved(self) -> bool:
        return self.resolution is not None and self.resolution.settles

    @property
    def text(self) -> str:
        return f"{self.kind.value}:{self.subject}"


@dataclass(frozen=True)
class Resolution(Record):
    """What a reviewer decided about one conflict, matched to it by subject."""

    subject: str
    strategy: ResolutionStrategy
    kind: Any = None
    evidence_ref: Any = None
    resolved_by: Any = None
    note: Any = None

    NESTED = {"evidence_ref": of(ExternalRef), "resolved_by": of(ComponentVersion)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject", require_text(self.subject, "subject", maximum=1024))
        object.__setattr__(self, "strategy", ResolutionStrategy.parse(self.strategy, "strategy"))
        if self.kind is not None:
            object.__setattr__(self, "kind", ConflictKind.parse(self.kind, "kind").value)
        if self.evidence_ref is not None and not isinstance(self.evidence_ref, ExternalRef):
            raise SchemaValidationError("evidence_ref must be an ExternalRef or None")
        if self.resolved_by is not None:
            object.__setattr__(self, "resolved_by", require_component_version(self.resolved_by, "resolved_by"))
        object.__setattr__(self, "note", require_optional_text(self.note, "note", maximum=512))


class _ResolutionIndex:
    """Resolutions addressed by full subject or by the bare id a caller would write."""

    def __init__(self, values: Iterable[Any]) -> None:
        self._items: dict[str, Resolution] = {}
        self._used: set[str] = set()
        for value in values:
            resolution = Resolution.coerce(value, "resolutions[]")
            if resolution.subject in self._items:
                raise GraphValidationError(f"conflict {resolution.subject} is resolved twice")
            self._items[resolution.subject] = resolution

    def _find(self, subject: str) -> tuple[Resolution | None, str | None]:
        exact = self._items.get(subject)
        if exact is not None:
            return exact, subject
        tail = subject.split(":", 1)[-1]
        for key in sorted(self._items):
            if key.split(":", 1)[-1] == tail:
                return self._items[key], key
        return None, None

    def get(self, subject: str) -> Resolution | None:
        found, key = self._find(subject)
        if key is not None:
            self._used.add(key)
        return found

    @property
    def unmatched(self) -> tuple[str, ...]:
        """Settlements offered for a disagreement that never happened.

        A resolution that matches nothing is a reviewer believing they settled
        something the merge never asked them about, so it is refused rather than
        quietly ignored.
        """

        return tuple(sorted(set(self._items) - self._used))

    def __len__(self) -> int:
        return len(self._items)

    @property
    def values(self) -> tuple[Resolution, ...]:
        return tuple(self._items[key] for key in sorted(self._items))


@dataclass(frozen=True)
class MergeReceipt(Record):
    """The governed record of one merge: inputs, disagreements, settlements, result."""

    merge_id: str
    base_snapshot_id: str
    target_snapshot_id: str
    source_snapshot_id: str
    result_snapshot_id: Any = None
    conflicts: tuple[MergeConflict, ...] = ()
    auto_resolved_subjects: tuple[str, ...] = ()
    target_digest: str = ""
    source_digest: str = ""
    result_digest: Any = None
    affected_node_ids: tuple[str, ...] = ()
    evidence_refs: tuple[ExternalRef, ...] = ()
    policy_refs: tuple[ExternalRef, ...] = ()
    actor: Any = None
    recorded_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "conflicts": of(MergeConflict),
        "evidence_refs": of(ExternalRef),
        "policy_refs": of(ExternalRef),
        "actor": of(ComponentVersion),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "merge_id", require_id(self.merge_id, "merge_id"))
        for name in ("base_snapshot_id", "target_snapshot_id", "source_snapshot_id"):
            object.__setattr__(self, name, require_id(getattr(self, name), name))
        if self.result_snapshot_id is not None:
            object.__setattr__(self, "result_snapshot_id", require_id(self.result_snapshot_id, "result_snapshot_id"))
        collected = require_bounded(self.conflicts, "conflicts", maximum=MAX_CONFLICTS)
        resolved = tuple(MergeConflict.coerce(item, "conflicts[]") for item in collected)
        texts = [item.text for item in resolved]
        clashes = sorted({item for item in texts if texts.count(item) > 1})
        if clashes:
            raise GraphValidationError(f"a merge reports the same conflict twice: {clashes}")
        object.__setattr__(self, "conflicts", tuple(sorted(resolved, key=lambda item: item.text)))
        subjects = require_bounded(
            self.auto_resolved_subjects, "auto_resolved_subjects", maximum=MAX_MERGE_INPUT_NODES
        )
        object.__setattr__(
            self,
            "auto_resolved_subjects",
            tuple(sorted({require_text(item, "auto_resolved_subjects[]", maximum=1024) for item in subjects})),
        )
        for name in ("target_digest", "source_digest", "result_digest"):
            value = getattr(self, name)
            if value:
                object.__setattr__(self, name, require_digest(value, name))
        nodes = require_bounded(
            self.affected_node_ids, "affected_node_ids", maximum=MAX_MERGE_INPUT_NODES, kind="node id"
        )
        object.__setattr__(
            self,
            "affected_node_ids",
            tuple(sorted({require_identifier(item, "affected_node_ids[]") for item in nodes})),
        )
        for name in ("evidence_refs", "policy_refs"):
            bounded = require_bounded(getattr(self, name), name, maximum=MAX_CLOSURE_REFS)
            refs = {ExternalRef.coerce(item, f"{name}[]") for item in bounded}
            object.__setattr__(self, name, tuple(sorted(refs, key=lambda item: item.text)))
        if self.actor is not None:
            object.__setattr__(self, "actor", require_component_version(self.actor, "actor"))
        object.__setattr__(self, "recorded_at_ms", require_millis(self.recorded_at_ms, "recorded_at_ms"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})
        blocking = self.unresolved_blocking
        if blocking and self.result_snapshot_id is not None:
            raise MergeBlockedError(
                f"merge {self.merge_id} names a result while {len(blocking)} blocking conflict(s) remain "
                "unresolved: " + ", ".join(sorted(item.text for item in blocking))
            )

    @property
    def unresolved(self) -> tuple[MergeConflict, ...]:
        return tuple(item for item in self.conflicts if not item.is_resolved)

    @property
    def unresolved_blocking(self) -> tuple[MergeConflict, ...]:
        return tuple(item for item in self.unresolved if item.blocking)

    @property
    def is_cleared(self) -> bool:
        return not self.unresolved

    @property
    def is_clean(self) -> bool:
        return not self.conflicts

    @property
    def kinds(self) -> tuple[ConflictKind, ...]:
        return tuple(sorted({item.kind for item in self.conflicts}, key=lambda item: item.value))

    def conflict(self, kind: Any, subject: str) -> MergeConflict | None:
        wanted = ConflictKind.parse(kind, "kind")
        return next(
            (item for item in self.conflicts if item.kind is wanted and item.subject == subject), None
        )


def _index(items: Iterable[Any], key: Any) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for item in items:
        found[key(item)] = item
    return found


def _slot(reference: ExternalRef) -> str:
    """Which external thing a reference names, ignoring which statement of it is held.

    Version and digest belong to the statement, not to the thing. Keying a rights
    binding by its full text would let two lines that renegotiated the same licence
    merge additively, silently holding both grants; keyed by slot they disagree,
    which is the RIGHTS_PROVENANCE conflict the contract names.
    """

    return f"{reference.kind.value.lower()}:{reference.reference}"


def _by_slot(refs: Iterable[Any]) -> dict[str, tuple[ExternalRef, ...]]:
    grouped: dict[str, list[ExternalRef]] = {}
    for item in refs:
        grouped.setdefault(_slot(item), []).append(item)
    return {
        key: tuple(sorted(value, key=lambda item: item.text))
        for key, value in grouped.items()
    }


def _flatten(grouped: Mapping[str, Any]) -> tuple[ExternalRef, ...]:
    carried = [item for key in sorted(grouped) for item in grouped[key]]
    return tuple(sorted(carried, key=lambda item: item.text))


def _touched_slots(
    *groups: Mapping[str, tuple[ExternalRef, ...]], wanted: set[str]
) -> set[str]:
    """The slots whose statements the diff actually named."""

    return {
        key
        for group in groups
        for key, value in group.items()
        if any(item.text in wanted for item in value)
    }


def _merge_ref_group(
    name: str,
    left: Iterable[Any],
    middle: Iterable[Any],
    right: Iterable[Any],
    wanted: _ResolutionIndex,
    conflicts: list[MergeConflict],
    auto: list[str],
) -> tuple[ExternalRef, ...]:
    """Merge one reference group by slot, then flatten it back into a closure tuple."""

    merged = _merge_subjects(
        _by_slot(left), _by_slot(middle), _by_slot(right),
        label=name,
        resolutions=wanted,
        conflicts=conflicts,
        auto=auto,
        bare=True,
    )
    return _flatten(merged)


def _merge_subjects(
    base: Mapping[str, Any],
    target: Mapping[str, Any],
    source: Mapping[str, Any],
    *,
    label: str,
    resolutions: _ResolutionIndex,
    conflicts: list[MergeConflict],
    auto: list[str],
    node_ids: Any = None,
    equal: Any = None,
    bare: bool = False,
) -> dict[str, Any]:
    """Combine three keyed maps, recording one conflict per genuine disagreement.

    A subject both lines moved the same way is taken once; a subject only one line
    moved is taken from that line; anything else is a disagreement a human or a
    governed procedure has to settle. The three cases are exactly the safe
    auto-merge and conflict families the contract separates.

    ``equal`` lets one family compare on less than full object identity, because a
    materialization records the run that produced it as well as what it produced.
    ``bare`` drops the family prefix where the key already names the whole subject.
    """

    kind = _KIND_OF_LABEL[label]
    merged: dict[str, Any] = {}
    for key in sorted(set(base) | set(target) | set(source)):
        subject = key if bare else f"{label}:{key}"
        earlier, here, over = base.get(key), target.get(key), source.get(key)
        if _same(here, over, equal):
            if here is not None:
                merged[key] = here
            if not _same(here, earlier, equal):
                auto.append(subject)
            continue
        if _same(here, earlier, equal):
            auto.append(subject)
            if over is not None:
                merged[key] = over
            continue
        if _same(over, earlier, equal):
            auto.append(subject)
            if here is not None:
                merged[key] = here
            continue
        matches = resolutions.get(subject)
        conflicts.append(
            _conflict(
                kind,
                subject,
                earlier,
                here,
                over,
                explanation=_why(here, over, kind),
                node_ids=() if node_ids is None else node_ids(key, here, over),
                resolution=matches,
            )
        )
        chosen = _chosen(matches, here, over)
        if chosen is not None:
            merged[key] = chosen
    return merged


def _same(first: Any, second: Any, equal: Any) -> bool:
    if first is None or second is None:
        return first is None and second is None
    return first == second if equal is None else equal(first, second)


def _same_output(first: MaterializationRecord, second: MaterializationRecord) -> bool:
    """Whether two lines committed the same thing, ignoring which run committed it.

    A re-render that reproduced the bytes is not a disagreement, so a merge that
    compared attempt identity would refuse every pair of branches that re-ran shared
    work. The attempt id and its timestamp are the only fields describing the run
    rather than the result, so they are the only ones this comparison forgets.
    """

    def substance(record: MaterializationRecord) -> str:
        payload = record.to_payload()
        for name in ("producer_attempt_id", "produced_at_ms"):
            payload.pop(name, None)
        return content_digest(payload)

    return substance(first) == substance(second)


def _why(here: Any, over: Any, kind: ConflictKind) -> str:
    if here is None:
        return "the target deleted what the source changed"
    if over is None:
        return "the source deleted what the target changed"
    return f"both lines changed it differently, so {kind.value.lower()} needs an explicit settlement"


def _conflict(
    kind: ConflictKind,
    subject: str,
    base_side: Any,
    target_side: Any,
    source_side: Any,
    *,
    explanation: str,
    node_ids: Sequence[str] = (),
    resolution: Resolution | None = None,
) -> MergeConflict:
    return MergeConflict(
        conflict_id=new_id(),
        kind=kind,
        subject=subject,
        base_side=_side(base_side),
        target_side=_side(target_side),
        source_side=_side(source_side),
        node_ids=tuple(node_ids),
        explanation=explanation,
        resolution=None if resolution is None else resolution.strategy,
        resolution_ref=None if resolution is None else resolution.evidence_ref,
        resolved_by=None if resolution is None else resolution.resolved_by,
    )


def _chosen(resolution: Resolution | None, target: Any, source: Any) -> Any:
    """Where a settlement is missing the candidate keeps the target side, unreviewed."""

    if resolution is None:
        return target
    if resolution.strategy is ResolutionStrategy.TAKE_SOURCE:
        return source
    return target


def _prune_records(
    records: Iterable[MaterializationRecord], index: Mapping[str, Any]
) -> tuple[MaterializationRecord, ...]:
    """Drop materializations the merged graph can no longer host on a real output port."""

    kept: list[MaterializationRecord] = []
    for record in records:
        node = index.get(record.node_id)
        if node is None:
            continue
        try:
            port = node.port(record.port_id)
        except GraphValidationError:
            continue
        if port.direction is PortDirection.OUTPUT:
            kept.append(record)
    return tuple(kept)


def _selection_map(closure: SnapshotClosureManifest) -> dict[str, str]:
    return dict(closure.effective_selection)


def _migration_ids(
    closures: Sequence[SnapshotClosureManifest], resolutions: _ResolutionIndex
) -> tuple[str, ...]:
    found: set[str] = set()
    for closure in closures:
        if closure.variant_selection is not None:
            found.update(closure.variant_selection.migration_receipt_ids)
    for resolution in resolutions.values:
        if resolution.strategy is not ResolutionStrategy.MIGRATE_IDENTITY:
            continue
        reference = None if resolution.evidence_ref is None else resolution.evidence_ref.reference
        try:
            found.add(require_id(reference, "migration receipt"))
        except SchemaValidationError as error:
            raise MergeBlockedError(
                f"the identity migration on {resolution.subject} must cite a receipt id: {error}"
            ) from error
    return tuple(sorted(found))


def _merge_catalogue(
    label: str,
    left: SnapshotClosureManifest,
    middle: SnapshotClosureManifest,
    right: SnapshotClosureManifest,
    wanted: _ResolutionIndex,
    conflicts: list[MergeConflict],
    auto: list[str],
    key: Any,
) -> tuple[Any, ...]:
    """Merge a catalogue (variant sets, constraints, anchors) by its own identity.

    A catalogue entry is a definition, not a value: two lines that reshaped the same
    axis disagree about what may be chosen at all, which no option-level rule can
    settle. Carrying whichever copy happened to be indexed first would hide that.
    """

    merged = _merge_subjects(
        _index(getattr(left, _CATALOGUE_FIELD[label]), key),
        _index(getattr(middle, _CATALOGUE_FIELD[label]), key),
        _index(getattr(right, _CATALOGUE_FIELD[label]), key),
        label=label,
        resolutions=wanted,
        conflicts=conflicts,
        auto=auto,
        node_ids=lambda name, here, over: (name,),
    )
    return tuple(merged[item] for item in sorted(merged))


def _check_merged_selection(
    sets: Any,
    constraints: Any,
    selection: VariantSelection | None,
    conflicts: list[MergeConflict],
    resolutions: _ResolutionIndex,
) -> None:
    """Re-validate the merged choice once, typing anchor drift apart from constraints.

    A persona anchor drifting is a different problem from an incompatible axis pair:
    one needs an identity migration, the other needs somebody to pick a combination.
    Checking the whole merged selection is what stops a legal-on-both-sides pair from
    surviving the merge, because neither line held it alone.
    """

    if selection is None or not sets:
        return
    effective = resolve_selection(sets, selection)
    grouped: dict[str, list[str]] = {}
    for address, reason in selection_rulings(sets, constraints, selection):
        grouped.setdefault(address, []).append(reason)
    for subject in sorted(grouped):
        head, separator, tail = subject.partition(":")
        conflicts.append(
            _conflict(
                _ADDRESS_KIND[head],
                subject,
                None,
                effective.get(tail) if separator and head.startswith("variant") else None,
                None,
                explanation="; ".join(grouped[subject])[:1000],
                node_ids=(tail,) if head in ("variant", "variant-set") else (),
                resolution=resolutions.get(subject),
            )
        )


def _anchor_divergence(
    closures: Sequence[SnapshotClosureManifest],
    sets: Sequence[Any],
    conflicts: list[MergeConflict],
    resolutions: _ResolutionIndex,
) -> None:
    """Two lines that moved the same protected anchor apart never auto-resolve."""

    base, target, source = closures
    here, over, earlier = (
        _selection_map(target),
        _selection_map(source),
        _selection_map(base),
    )
    for variant_set in sets:
        anchor = variant_set.identity_anchor
        if anchor is None:
            continue
        set_id = variant_set.variant_set_id
        left, right = here.get(set_id), over.get(set_id)
        if left == right:
            continue
        moved = [
            side
            for side in (left, right)
            if side is not None and anchor.drifts(_anchor_digest(variant_set, side))
        ]
        if len(moved) < 2:
            continue
        subject = f"anchor-drift:{anchor.anchor_id}"
        conflicts.append(
            _conflict(
                ConflictKind.IDENTITY_ANCHOR_CONFLICT,
                subject,
                earlier.get(set_id),
                left,
                right,
                explanation=(
                    f"the two lines move protected identity anchor {anchor.anchor_id} apart under "
                    f"policy {anchor.policy_ref.text}; only an identity migration may authorise either side"
                ),
                node_ids=(set_id,),
                resolution=resolutions.get(subject),
            )
        )


def _anchor_policy_moves(
    base: SnapshotClosureManifest,
    sets: Sequence[Any],
    conflicts: list[MergeConflict],
    resolutions: _ResolutionIndex,
) -> tuple[Any, ...]:
    """A persona protection that a merge weakens is a conflict, never an auto-merge.

    Changing an axis *definition* is already handled by the catalogue merge. This
    catches the narrower and nastier case: one line edited the axis for its own
    reasons and, in doing so, dropped or re-pointed the anchor, while the other line
    simply never touched it. Silence here would let a merge unprotect an identity as
    a side effect of unrelated work.

    Keeping the target side restores the protection and leaves the rest of the merged
    definition alone; an identity migration is the only way to merge without it.
    """

    earlier = {item.variant_set_id: item for item in base.variant_sets}
    resolved: dict[str, Any] = {}
    for variant_set in sets:
        guarded = earlier.get(variant_set.variant_set_id)
        if guarded is None or guarded.identity_anchor is None:
            continue  # a new axis, or one that was never protected, has nothing to weaken
        anchor = variant_set.identity_anchor
        if anchor == guarded.identity_anchor:
            continue
        protected = guarded.identity_anchor
        subject = f"anchor-policy:{protected.anchor_id}"
        resolution = resolutions.get(subject)
        conflicts.append(
            _conflict(
                ConflictKind.IDENTITY_ANCHOR_CONFLICT,
                subject,
                protected.anchor_id,
                None if anchor is None else anchor.anchor_id,
                None,
                explanation=(
                    f"the merged variant set {variant_set.variant_set_id} "
                    + ("no longer carries" if anchor is None else "now carries")
                    + f" the protected identity anchor {protected.anchor_id} that the base enforced under "
                    f"policy {protected.policy_ref.text}; dropping a persona guard is a decision, not a merge"
                ),
                node_ids=(variant_set.variant_set_id,),
                resolution=resolution,
            )
        )
        if resolution is None or resolution.strategy is ResolutionStrategy.KEEP_TARGET:
            resolved[variant_set.variant_set_id] = replace(variant_set, identity_anchor=protected)
    if not resolved:
        return tuple(sets)
    return tuple(resolved.get(item.variant_set_id, item) for item in sets)


def _anchor_digest(variant_set: Any, option_id: str) -> Any:
    try:
        return variant_set.option(option_id).anchor_digest
    except GraphValidationError:
        return None


def _side_effect_conflict(item: Any, resolutions: _ResolutionIndex) -> MergeConflict:
    from .snapshots import ExternalSideEffect

    effect = ExternalSideEffect.coerce(item, "side_effect_conflicts[]")
    subject = f"side-effect:{effect.node_id}:{effect.destination.text}"
    matches = resolutions.get(subject)
    return MergeConflict(
        conflict_id=new_id(),
        kind=ConflictKind.SIDE_EFFECT_CONFLICT,
        subject=subject,
        target_side=effect.state.value,
        source_side=effect.side_effect_id,
        node_ids=(effect.node_id,),
        explanation=(
            "both lines mutated the same external destination; a merge cannot un-publish, un-charge "
            "or revoke, so a compensation or reconciliation procedure has to be named"
        ),
        resolution=None if matches is None else matches.strategy,
        resolution_ref=None if matches is None else matches.evidence_ref,
        resolved_by=None if matches is None else matches.resolved_by,
    )


def _inherited_class(*snapshots: Snapshot) -> SnapshotClass:
    """A merge inherits only the weakest completeness claim all three inputs support."""

    return min((item.snapshot_class for item in snapshots), key=lambda item: item.rank)


def _merge_closures(
    store: SnapshotStore,
    *,
    base: Snapshot,
    target: Snapshot,
    source: Snapshot,
    source_closure: SnapshotClosureManifest | None = None,
    resolutions: Iterable[Any] = (),
    side_effect_conflicts: Iterable[Any] = (),
    merge_id: str | None = None,
    actor: Any = None,
    snapshot_class: Any = None,
    derivation: Any = SnapshotDerivation.MERGED,
    created_at_ms: int = 0,
    commit: bool = True,
) -> tuple[Snapshot | None, MergeReceipt]:
    """The one merge algorithm: combine three closures, type the disagreements.

    ``source_closure`` lets a transplant hand in a source whose changes were already
    clipped to a bounded scope, so cherry-picking and branch merging share exactly one
    set of conflict rules instead of two that can drift apart.
    """

    left, middle = base.closure, target.closure
    right = source_closure if source_closure is not None else source.closure
    tag = require_id(merge_id, "merge_id") if merge_id is not None else new_id()
    wanted = _ResolutionIndex(resolutions)
    conflicts: list[MergeConflict] = []
    auto: list[str] = []
    for name, first, second in (("target", base, target), ("source", base, source)):
        if first.project_id != second.project_id or first.production_id != second.production_id:
            raise SnapshotClosureError(
                f"the {name} snapshot belongs to production {second.production_id}, which is not the base "
                f"production {first.production_id}; merging across productions is a different operation"
            )
        if first.closure.graph_id != second.closure.graph_id:
            raise SnapshotClosureError(
                f"the {name} snapshot closes over graph {second.closure.graph_id} while the base closes over "
                f"{first.closure.graph_id}: one graph revision family merges against itself, never across graphs"
            )
    parts = _merge_definition(left, middle, right, wanted, conflicts, auto)
    sets = _merge_catalogue(
        "variant-set", left, middle, right, wanted, conflicts, auto, lambda item: item.variant_set_id
    )
    constraints = _merge_catalogue(
        "variant-constraint", left, middle, right, wanted, conflicts, auto, lambda item: item.constraint_id
    )
    anchors = _merge_catalogue(
        "identity-anchor", left, middle, right, wanted, conflicts, auto, lambda item: item.anchor_id
    )
    sets = _anchor_policy_moves(left, sets, conflicts, resolutions=wanted)
    selection = _merge_selection(sets, left, middle, right, wanted, conflicts, auto)
    records = _merge_materializations(left, middle, right, parts["nodes"], wanted, conflicts, auto)
    _check_merged_selection(sets, constraints, selection, conflicts, wanted)
    _anchor_divergence((left, middle, right), sets, conflicts, resolutions=wanted)
    intent = _merge_scalar("intent", left.intent_ref, middle.intent_ref, right.intent_ref, wanted, conflicts, auto)
    environment = _merge_scalar(
        "environment", left.environment_fingerprint, middle.environment_fingerprint,
        right.environment_fingerprint, wanted, conflicts, auto,
    )
    graph = _merged_graph(
        base, target, source, parts, records, selection, intent, environment, tag, conflicts, wanted
    )
    groups = {
        name: _merge_ref_group(
            name, getattr(left, name), getattr(middle, name), getattr(right, name), wanted, conflicts, auto
        )
        for name in _REF_GROUPS
    }
    admitted = _merge_ref_group(
        "admission", left.external_admissions, middle.external_admissions,
        right.external_admissions, wanted, conflicts, auto
    )
    for item in side_effect_conflicts:
        conflicts.append(_side_effect_conflict(item, wanted))
    if graph is None:
        closure = None
    else:
        closure = replace(
            middle,
            graph=graph,
            ancestry=tuple(sorted({*left.ancestry, *middle.ancestry, *right.ancestry, target.snapshot_id, source.snapshot_id})),
            parent_snapshot_ids=tuple(sorted({target.snapshot_id, source.snapshot_id})),
            variant_sets=sets,
            variant_constraints=constraints,
            variant_selection=selection,
            identity_anchors=anchors,
            intent_ref=intent,
            environment_fingerprint=environment,
            external_admissions=admitted,
            **groups,
        )
    wanted_class = (
        SnapshotClass.parse(snapshot_class, "snapshot_class")
        if snapshot_class is not None
        else _inherited_class(base, target, source)
    )
    reasons = () if closure is None else closure_obligations(closure, wanted_class)
    if reasons:
        subject = f"closure:{wanted_class.value}"
        conflicts.append(
            _conflict(
                ConflictKind.QUALITY_POLICY_CONFLICT,
                subject,
                None,
                None,
                None,
                explanation="; ".join(reasons)[:1000],
                resolution=wanted.get(subject),
            )
        )
    stray = wanted.unmatched
    if stray:
        raise MergeBlockedError(
            "no disagreement in this merge matched the settlement offered for "
            + ", ".join(stray)
            + "; a resolution that addresses nothing is a misunderstanding, not a decision"
        )
    blocking = tuple(item for item in conflicts if not item.is_resolved and item.blocking)
    snapshot: Snapshot | None = None
    if closure is not None and not blocking and commit:
        snapshot = commit_snapshot(
            closure,
            snapshot_class=wanted_class,
            derivation=SnapshotDerivation.parse(derivation, "derivation"),
            actor=actor,
            supersedes_snapshot_ids=(target.snapshot_id, source.snapshot_id),
            created_at_ms=created_at_ms,
        )
        store.commit(snapshot)
    affected: set[str] = {node for item in conflicts for node in item.node_ids}
    if graph is not None:
        affected.update(
            node_id for node_id in parts["nodes"] if node_id not in middle.revision.definition.node_index
        )
    receipt = MergeReceipt(
        merge_id=tag,
        base_snapshot_id=base.snapshot_id,
        target_snapshot_id=target.snapshot_id,
        source_snapshot_id=source.snapshot_id,
        result_snapshot_id=None if snapshot is None else snapshot.snapshot_id,
        conflicts=tuple(conflicts),
        auto_resolved_subjects=tuple(sorted(set(auto))),
        target_digest=middle.digest,
        source_digest=right.digest,
        result_digest=None if snapshot is None else snapshot.digest,
        affected_node_ids=tuple(sorted(affected & set(parts["nodes"]))),
        evidence_refs=tuple(
            sorted(
                {
                    *[item.evidence_ref for item in wanted.values if item.evidence_ref is not None],
                    *[item.resolution_ref for item in conflicts if item.resolution_ref is not None],
                },
                key=lambda item: item.text,
            )
        ),
        actor=actor,
        recorded_at_ms=created_at_ms,
    )
    return snapshot, receipt


def _merge_definition(
    left: SnapshotClosureManifest,
    middle: SnapshotClosureManifest,
    right: SnapshotClosureManifest,
    wanted: _ResolutionIndex,
    conflicts: list[MergeConflict],
    auto: list[str],
) -> dict[str, Any]:
    """Merge the definition into unbound maps, one per subject space.

    Binding is deliberately left to ``_merged_definition``: a merged graph can be
    incoherent in a way only the whole picture shows (a node one line kept without the
    edge another line deleted), and that has to come back as a typed conflict instead
    of raising out of the middle of the merge.
    """

    base, target, source = left.revision.definition, middle.revision.definition, right.revision.definition
    nodes = _merge_subjects(
        _index(base.nodes, lambda item: item.node_id),
        _index(target.nodes, lambda item: item.node_id),
        _index(source.nodes, lambda item: item.node_id),
        label="node",
        resolutions=wanted,
        conflicts=conflicts,
        auto=auto,
        node_ids=lambda key, here, over: (key,),
    )
    edges = _merge_subjects(
        _index(base.edges, lambda item: item.edge_id),
        _index(target.edges, lambda item: item.edge_id),
        _index(source.edges, lambda item: item.edge_id),
        label="edge",
        resolutions=wanted,
        conflicts=conflicts,
        auto=auto,
        node_ids=lambda key, here, over: _edge_nodes(key, here, over),
    )
    declared = _merge_subjects(
        _index(base.declared_external_inputs, lambda item: item.text),
        _index(target.declared_external_inputs, lambda item: item.text),
        _index(source.declared_external_inputs, lambda item: item.text),
        label="declared",
        resolutions=wanted,
        conflicts=conflicts,
        auto=auto,
    )
    interfaces = _merge_subjects(
        _index(base.interfaces, lambda item: item.node_id),
        _index(target.interfaces, lambda item: item.node_id),
        _index(source.interfaces, lambda item: item.node_id),
        label="interface",
        resolutions=wanted,
        conflicts=conflicts,
        auto=auto,
        node_ids=lambda key, here, over: (key,),
    )
    _check_surviving_edges(base, target, source, nodes, edges, wanted, conflicts, auto)
    return {
        "graph_id": target.graph_id,
        "version": max(base.version, target.version, source.version) + 1,
        "nodes": nodes,
        "edges": edges,
        "declared": declared,
        "interfaces": interfaces,
        "metadata": target.metadata,
    }


def _check_surviving_edges(
    base: GraphDefinition,
    target: GraphDefinition,
    source: GraphDefinition,
    nodes: dict[str, Any],
    edges: dict[str, Any],
    wanted: _ResolutionIndex,
    conflicts: list[MergeConflict],
    auto: list[str],
) -> None:
    """A deleted dependency the merged graph still needs is a conflict, not a drop.

    One line deleting an edge the other never touched reads as a clean deletion until
    the node it fed turns out to survive the merge, because the other line changed it.
    Left alone that merges a required input with no producer, so the deletion is
    re-filed as a topology conflict and only a settlement that restores the edge (or
    drops the node it feeds) can bind the result.
    """

    by_id = {
        name: {item.edge_id: item for item in found.edges}
        for name, found in (("base", base), ("target", target), ("source", source))
    }
    universe: dict[str, GraphEdge] = {}
    for name in ("base", "target", "source"):
        universe.update(by_id[name])
    for edge_id in sorted(set(universe) - set(edges)):
        if edge_id not in by_id["target"] and edge_id not in by_id["source"]:
            continue  # both lines deleted it together, which is a decision rather than a merge
        edge = universe[edge_id]
        if edge.source_node_id not in nodes or edge.target_node_id not in nodes:
            continue  # the node it fed is gone as well, so nothing in the merged graph needs it
        subject = f"edge:{edge_id}"
        matches = wanted.get(subject)
        if subject in auto:
            auto.remove(subject)
        conflicts.append(
            _conflict(
                ConflictKind.TOPOLOGY_CONFLICT,
                subject,
                by_id["base"].get(edge_id),
                by_id["target"].get(edge_id),
                by_id["source"].get(edge_id),
                explanation=(
                    f"the merged graph keeps {edge.source_node_id} and {edge.target_node_id} but "
                    f"{edge_id} was deleted on one line; a required input cannot survive its own producer"
                ),
                node_ids=(edge.source_node_id, edge.target_node_id),
                resolution=matches,
            )
        )
        if matches is not None and matches.strategy is ResolutionStrategy.TAKE_SOURCE:
            restored = by_id["source"].get(edge_id) or by_id["base"].get(edge_id)
            if restored is not None:
                edges[edge_id] = restored


def _merged_definition(parts: Mapping[str, Any]) -> GraphDefinition:
    """Bind what ``_merge_definition`` combined, or raise why it cannot be bound."""

    return GraphDefinition(
        graph_id=parts["graph_id"],
        version=parts["version"],
        nodes=tuple(parts["nodes"][key] for key in sorted(parts["nodes"])),
        edges=tuple(parts["edges"][key] for key in sorted(parts["edges"])),
        declared_external_inputs=tuple(parts["declared"][key] for key in sorted(parts["declared"])),
        interfaces=tuple(parts["interfaces"][key] for key in sorted(parts["interfaces"])),
        metadata=parts["metadata"],
    )


def _edge_nodes(key: str, here: Any, over: Any) -> tuple[str, ...]:
    for value in (here, over):
        if isinstance(value, GraphEdge):
            return tuple(sorted({value.source_node_id, value.target_node_id}))
    return ()


def _merge_materializations(
    left: SnapshotClosureManifest,
    middle: SnapshotClosureManifest,
    right: SnapshotClosureManifest,
    nodes: Mapping[str, Any],
    wanted: _ResolutionIndex,
    conflicts: list[MergeConflict],
    auto: list[str],
) -> tuple[MaterializationRecord, ...]:
    def key(record: MaterializationRecord) -> str:
        return f"{record.node_id}.{record.port_id}"

    merged = _merge_subjects(
        _index(left.graph.materializations, key),
        _index(middle.graph.materializations, key),
        _index(right.graph.materializations, key),
        label="revision",
        resolutions=wanted,
        conflicts=conflicts,
        auto=auto,
        node_ids=lambda name, here, over: (name.rsplit(".", 1)[0],),
        equal=_same_output,
    )
    return _prune_records((merged[name] for name in sorted(merged)), nodes)


def _merge_selection(
    sets: Sequence[Any],
    left: SnapshotClosureManifest,
    middle: SnapshotClosureManifest,
    right: SnapshotClosureManifest,
    wanted: _ResolutionIndex,
    conflicts: list[MergeConflict],
    auto: list[str],
) -> VariantSelection | None:
    if not sets:
        return middle.variant_selection
    merged = _merge_subjects(
        _selection_map(left), _selection_map(middle), _selection_map(right),
        label="variant",
        resolutions=wanted,
        conflicts=conflicts,
        auto=auto,
        node_ids=lambda key, here, over: (key,),
    )
    defaults = {item.variant_set_id: item.default_option_id for item in sets}
    pairs = tuple((key, value) for key, value in merged.items() if defaults.get(key) != value)
    return VariantSelection(
        selection_id=new_id(),
        pairs=pairs,
        migration_receipt_ids=_migration_ids((left, middle, right), wanted),
        actor=None if middle.variant_selection is None else middle.variant_selection.actor,
    )


def _merge_scalar(
    label: str,
    base: Any,
    target: Any,
    source: Any,
    wanted: _ResolutionIndex,
    conflicts: list[MergeConflict],
    auto: list[str],
) -> Any:
    if target == source:
        return target
    subject = label
    if base == target:
        auto.append(subject)
        return source
    if base == source:
        auto.append(subject)
        return target
    conflicts.append(
        _conflict(
            _KIND_OF_LABEL[label], subject, base, target, source,
            explanation="both lines restated it differently",
            resolution=wanted.get(subject),
        )
    )
    return _chosen(wanted.get(subject), target, source)


def _merged_graph(
    base: Snapshot,
    target: Snapshot,
    source: Snapshot,
    parts: Mapping[str, Any],
    records: tuple[MaterializationRecord, ...],
    selection: VariantSelection | None,
    intent: Any,
    environment: Any,
    merge_tag: str,
    conflicts: list[MergeConflict],
    wanted: _ResolutionIndex,
) -> MaterializationGraph | None:
    """Bind the merged definition, or type the failure instead of raising through it.

    A merged graph can still be illegal in ways only the whole picture reveals: a
    node left on a lower quality class than its consumer demands, an edge whose port
    another line renamed, a node kept without the edge that fed it. Those become
    conflicts a reviewer can act on rather than an exception that abandons the merge.
    """

    try:
        revision = GraphRevision(
            revision_id=new_id(),
            definition=_merged_definition(parts),
            created_at_ms=max(
                base.revision.created_at_ms, target.revision.created_at_ms, source.revision.created_at_ms
            ),
            admitted_by=ExternalRef(kind=EntityKind.RECEIPT, reference=merge_tag),
        )
        return MaterializationGraph(
            revision=revision,
            materializations=records,
            variant_selection=() if selection is None else tuple(sorted(selection.as_map().items())),
            environment_fingerprint=environment,
        )
    except (GraphValidationError, SchemaValidationError) as error:
        subject = "graph:merged"
        conflicts.append(
            _conflict(
                ConflictKind.TOPOLOGY_CONFLICT, subject, None, None, None,
                explanation=str(error)[:1000],
                resolution=wanted.get(subject),
            )
        )
        return None


def three_way_merge(
    store: SnapshotStore,
    *,
    base_snapshot_id: str,
    target_snapshot_id: str,
    source_snapshot_id: str,
    resolutions: Iterable[Any] = (),
    side_effect_conflicts: Iterable[Any] = (),
    merge_id: str | None = None,
    actor: Any = None,
    snapshot_class: Any = None,
    created_at_ms: int = 0,
    commit: bool = True,
) -> tuple[Snapshot | None, MergeReceipt]:
    """Merge two heads against their common base, and say exactly what disagreed.

    With ``commit=False`` the caller gets the receipt and no snapshot: that is how a
    review screen shows the disagreements before anybody has decided them.
    """

    return _merge_closures(
        store,
        base=store.get(base_snapshot_id),
        target=store.get(target_snapshot_id),
        source=store.get(source_snapshot_id),
        resolutions=resolutions,
        side_effect_conflicts=side_effect_conflicts,
        merge_id=merge_id,
        actor=actor,
        snapshot_class=snapshot_class,
        created_at_ms=created_at_ms,
        commit=commit,
    )


def advance_merge(
    store: SnapshotStore,
    ledger: Any,
    receipt: Any,
    *,
    branch_id: str,
    actor: Any,
    expected_head_snapshot_id: Any = None,
    evidence_refs: Sequence[ExternalRef] = (),
    now_ms: int = 0,
    command_id: str | None = None,
    command_digest: str | None = None,
) -> tuple[Any, TransitionReceipt]:
    """Move a branch head onto a merge result, and only onto a cleared one."""

    wanted = MergeReceipt.coerce(receipt, "receipt")
    if wanted.result_snapshot_id is None:
        raise MergeBlockedError(
            f"merge {wanted.merge_id} produced no result snapshot; settle its conflicts and merge again"
        )
    blocking = wanted.unresolved_blocking
    if blocking:
        raise MergeBlockedError(
            f"branch {branch_id} may not advance onto merge {wanted.merge_id}: "
            + ", ".join(sorted(item.text for item in blocking))
        )
    result = store.get(wanted.result_snapshot_id)
    if set(result.closure.parent_snapshot_ids) != {wanted.target_snapshot_id, wanted.source_snapshot_id}:
        raise MergeBlockedError(
            f"merge {wanted.merge_id} does not name both heads among its result's parents, so the "
            "receipt would not describe the history being adopted"
        )
    settled = tuple(
        item.resolution_ref for item in wanted.conflicts if item.resolution_ref is not None
    )
    return ledger.advance(
        branch_id,
        wanted.result_snapshot_id,
        actor=actor,
        reason_code="merge",
        expected_head_snapshot_id=expected_head_snapshot_id,
        evidence_refs=tuple(
            sorted(
                {
                    *settled,
                    *wanted.evidence_refs,
                    *evidence_refs,
                    ExternalRef(kind=EntityKind.RECEIPT, reference=wanted.merge_id),
                },
                key=lambda item: item.text,
            )
        ),
        command_id=command_id,
        command_digest=command_digest,
        now_ms=now_ms,
    )


def _universe(closure: SnapshotClosureManifest) -> tuple[set[str], ...]:
    definition = closure.revision.definition
    return (
        set(definition.node_index),
        {item.edge_id for item in definition.edges},
        {item.node_id for item in definition.interfaces},
        {item.text for item in definition.declared_external_inputs},
        {f"{item.node_id}.{item.port_id}" for item in closure.graph.materializations},
    )


def _scoped_keys(
    entries: Iterable[DiffEntry], *closures: SnapshotClosureManifest
) -> dict[str, set[str]]:
    """Map the diff entries a delta carries back onto the merge's own subject spaces.

    Routing is by which space actually holds the subject, not by the entry's category,
    because one category covers several spaces: a topology entry may name a node only
    the base still has, and a quality entry names either a materialization or a bound
    decision depending on how its subject is spelled.
    """

    nodes: set[str] = set()
    edges: set[str] = set()
    interfaces: set[str] = set()
    revisions: set[str] = set()
    for closure in closures:
        found = _universe(closure)
        nodes |= found[0]
        edges |= found[1]
        interfaces |= found[2]
        revisions |= found[4]
    keys: dict[str, set[str]] = {name: set() for name in _KIND_OF_LABEL}
    for entry in entries:
        subject = entry.subject
        head, separator, tail = subject.partition(":")
        if separator and head in _REF_GROUPS:
            keys[head].add(tail)
        elif subject in ("intent", "environment"):
            keys[subject].add(subject)
        elif head == "interface" and tail in interfaces:
            keys["interface"].add(tail)
        elif subject.split(":tool:", 1)[0] in revisions:
            keys["revision"].add(subject.split(":tool:", 1)[0])
        elif subject in nodes:
            keys["node"].add(subject)
        elif subject in edges:
            keys["edge"].add(subject)
        else:
            keys["declared"].add(subject)
    return keys


def _by(value: Iterable[Any], key: Any) -> dict[str, Any]:
    return {key(item): item for item in value}


def _keep(
    carried: Mapping[str, Any], wanted: set[str], fallback: Mapping[str, Any]
) -> dict[str, Any]:
    """In-scope keys come from the source, its deletions included; the rest from the base."""

    result = {key: value for key, value in fallback.items() if key not in wanted}
    result.update({key: value for key, value in carried.items() if key in wanted})
    return result


def _clip_to_scope(
    base: SnapshotClosureManifest,
    source: SnapshotClosureManifest,
    keys: Mapping[str, set[str]],
) -> SnapshotClosureManifest:
    """A source carrying only the delta's scope: everything else reverts to the base.

    This is what makes a transplant share the merge's conflict rules instead of
    inventing a second, weaker set. Out-of-scope movement cannot leak through, because
    it is not present in the closure the merge is handed.
    """

    definition = source.revision.definition
    earlier = base.revision.definition
    merged_nodes = _keep(
        _by(definition.nodes, lambda item: item.node_id), keys["node"],
        _by(earlier.nodes, lambda item: item.node_id),
    )
    merged_edges = _keep(
        _by(definition.edges, lambda item: item.edge_id), keys["edge"],
        _by(earlier.edges, lambda item: item.edge_id),
    )
    merged_declared = _keep(
        _by(definition.declared_external_inputs, lambda item: item.text), keys["declared"],
        _by(earlier.declared_external_inputs, lambda item: item.text),
    )
    merged_interfaces = _keep(
        _by(definition.interfaces, lambda item: item.node_id), keys["interface"],
        _by(earlier.interfaces, lambda item: item.node_id),
    )
    clipped = GraphDefinition(
        graph_id=definition.graph_id,
        version=definition.version,
        nodes=tuple(merged_nodes[key] for key in sorted(merged_nodes)),
        edges=tuple(merged_edges[key] for key in sorted(merged_edges)),
        declared_external_inputs=tuple(merged_declared[key] for key in sorted(merged_declared)),
        interfaces=tuple(merged_interfaces[key] for key in sorted(merged_interfaces)),
        metadata=definition.metadata,
    )
    records = _keep(
        _by(source.graph.materializations, lambda item: f"{item.node_id}.{item.port_id}"),
        keys["revision"],
        _by(base.graph.materializations, lambda item: f"{item.node_id}.{item.port_id}"),
    )
    selection = _keep(_selection_map(source), keys["variant"], _selection_map(base))
    groups: dict[str, tuple[ExternalRef, ...]] = {}
    for name in _REF_GROUPS:
        carried = _by_slot(getattr(source, name))
        fallback = _by_slot(getattr(base, name))
        touched = _touched_slots(carried, fallback, wanted=keys[name])
        groups[name] = _flatten(_keep(carried, touched, fallback))
    axes = set(keys["variant"]) | set(keys["variant-set"])
    variant_sets = _keep(
        _by(source.variant_sets, lambda item: item.variant_set_id), axes,
        _by(base.variant_sets, lambda item: item.variant_set_id),
    )
    constraints = _clip_constraints(base, source, variant_sets, axes)
    anchors = _by(base.identity_anchors, lambda item: item.anchor_id)
    for variant_set in variant_sets.values():
        if variant_set.identity_anchor is not None:
            anchors[variant_set.identity_anchor.anchor_id] = variant_set.identity_anchor
    # An admission travels with the dependency it admits. Out-of-scope dependencies
    # reverted to the base above, so their grants come from the base too.
    admitted = _by(base.external_admissions, lambda item: item.text)
    declared_here = {item.reference for item in clipped.declared_external_inputs}
    for item in source.external_admissions:
        if item.reference in declared_here:
            admitted[item.text] = item
    graph = MaterializationGraph(
        revision=GraphRevision(
            revision_id=new_id(), definition=clipped, created_at_ms=source.revision.created_at_ms
        ),
        materializations=tuple(
            _prune_records((records[key] for key in sorted(records)), clipped.node_index)
        ),
        variant_selection=tuple(sorted(selection.items())),
        environment_fingerprint=(
            base.graph.environment_fingerprint if not keys["environment"]
            else source.graph.environment_fingerprint
        ),
    )
    return replace(
        source,
        graph=graph,
        variant_sets=tuple(variant_sets[key] for key in sorted(variant_sets)),
        variant_constraints=constraints,
        identity_anchors=tuple(anchors[key] for key in sorted(anchors)),
        variant_selection=_narrowed_selection(source, selection),
        intent_ref=base.intent_ref if not keys["intent"] else source.intent_ref,
        environment_fingerprint=(
            base.environment_fingerprint if not keys["environment"] else source.environment_fingerprint
        ),
        external_admissions=tuple(admitted[key] for key in sorted(admitted)),
        **groups,
    )


def _clip_constraints(
    base: SnapshotClosureManifest,
    source: SnapshotClosureManifest,
    variant_sets: Mapping[str, Any],
    touched: set[str],
) -> tuple[Any, ...]:
    """Carry a source constraint only when the transplant actually moved its axes.

    Constraints are policy, not payload: an unrequested rule arriving with a rig fix
    could refuse a selection the target line had always held.
    """

    index = _by(base.variant_constraints, lambda item: item.constraint_id)
    surviving = set(variant_sets)
    for item in source.variant_constraints:
        if item.constraint_id in index:
            continue
        if {item.when_set, item.target_set} & touched and {item.when_set, item.target_set} <= surviving:
            index[item.constraint_id] = item
    return tuple(index[key] for key in sorted(index))


def _narrowed_selection(
    source: SnapshotClosureManifest, selection: Mapping[str, str]
) -> VariantSelection | None:
    """Keep the source's own selection record, narrowed to the axes that survived.

    A fresh id would invent an identity the delta never carried, and dropping the
    migration receipts would refuse an identity change the source had already proved.
    """

    original = source.variant_selection
    if original is None:
        return None
    return replace(original, pairs=tuple(sorted(selection.items())))


def transplant(
    store: SnapshotStore,
    delta: Any,
    *,
    resolutions: Iterable[Any] = (),
    side_effect_conflicts: Iterable[Any] = (),
    merge_id: str | None = None,
    actor: Any = None,
    snapshot_class: Any = None,
    created_at_ms: int = 0,
    commit: bool = True,
) -> tuple[Snapshot | None, MergeReceipt]:
    """Carry a bounded scope from one snapshot into another without merging a branch.

    Everything outside the delta's scope stays exactly as the target had it. That is
    what separates a transplant from a merge, and what lets one approved rig fix move
    between ten delivery branches without dragging their divergent histories along.
    """

    wanted = ProductionDelta.coerce(delta, "delta")
    base = store.get(wanted.merge_base_snapshot_id)
    target = store.get(wanted.target_snapshot_id)
    source = store.get(wanted.source_snapshot_id)
    failures = wanted.precondition_failures(target)
    if failures:
        raise GraphValidationError(
            f"delta {wanted.delta_id} cannot be transplanted: " + "; ".join(failures)
        )
    carried = semantic_diff(base, source)
    inside = tuple(
        entry
        for entry in carried.entries
        if entry.category in wanted.scope
        and (
            not wanted.included_node_ids
            or not entry.node_ids
            or bool(set(entry.node_ids) & set(wanted.included_node_ids))
        )
    )
    blocked = sorted(
        entry.subject
        for entry in inside
        if entry.node_ids and set(entry.node_ids) & set(wanted.excluded_node_ids)
    )
    if blocked:
        raise GraphValidationError(
            f"delta {wanted.delta_id} would carry subjects it also excludes: {blocked}"
        )
    keys = _scoped_keys(inside, base.closure, source.closure)
    clipped = _clip_to_scope(base.closure, source.closure, keys)
    snapshot, receipt = _merge_closures(
        store,
        base=base,
        target=target,
        source=source,
        source_closure=clipped,
        resolutions=resolutions,
        side_effect_conflicts=side_effect_conflicts,
        merge_id=merge_id,
        actor=actor,
        snapshot_class=snapshot_class,
        derivation=SnapshotDerivation.TRANSPLANTED,
        created_at_ms=created_at_ms,
        commit=commit,
    )
    return snapshot, receipt
