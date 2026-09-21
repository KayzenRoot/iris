"""M02 area C (diffing): semantic diff between two snapshot closures.

A Snapshot diff is not "which files differ". The kernel has to say *what kind* of
meaning moved, because merge, review and the build planner all read the same
output and each of them treats a topology move differently from a re-render. Ten
categories come from the frozen contract; anything that cannot be classified is
refused rather than filed under a vague "other".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .base import Labeled, Record, of
from .errors import SchemaValidationError, SnapshotClosureError
from .graph import GraphRevision, MaterializationRecord
from .identity import ExternalRef, new_id, require_id
from .limits import MAX_DIFF_ENTRIES, MAX_DIFF_SUBJECT_CHARS, MAX_IMPACT_NODES
from .versions import (
    CONTRACT_VERSION,
    canonical_json,
    content_digest,
    require_bounded,
    require_digest,
    require_identifier,
    require_supported_version,
    require_text,
)

__all__ = [
    "DiffCategory",
    "DiffOperation",
    "DiffEntry",
    "SemanticDiff",
    "semantic_diff",
]


class DiffCategory(Labeled):
    """The ten kinds of semantic movement a snapshot diff can name."""

    GRAPH_TOPOLOGY = "GRAPH_TOPOLOGY"
    NODE_DEFINITION = "NODE_DEFINITION"
    DEPENDENCY_FACET = "DEPENDENCY_FACET"
    VARIANT_SELECTION = "VARIANT_SELECTION"
    INTENT_BRIEF = "INTENT_BRIEF"
    ASSET_REVISION = "ASSET_REVISION"
    QUALITY_DECISION = "QUALITY_DECISION"
    RIGHTS_PROVENANCE = "RIGHTS_PROVENANCE"
    DELIVERY_POLICY = "DELIVERY_POLICY"
    ENVIRONMENT_QUALIFICATION = "ENVIRONMENT_QUALIFICATION"

    @property
    def blocking_by_default(self) -> bool:
        """Whether this category changes what the production *is*, not how it looks.

        A merge may carry a non-blocking difference forward; a blocking one has to
        be resolved before a branch head moves.
        """

        return self in {
            DiffCategory.GRAPH_TOPOLOGY,
            DiffCategory.NODE_DEFINITION,
            DiffCategory.DEPENDENCY_FACET,
            DiffCategory.INTENT_BRIEF,
            DiffCategory.ASSET_REVISION,
            DiffCategory.QUALITY_DECISION,
            DiffCategory.RIGHTS_PROVENANCE,
            DiffCategory.DELIVERY_POLICY,
        }


class DiffOperation(Labeled):
    """How one subject moved between the two closures."""

    ADDED = "ADDED"
    REMOVED = "REMOVED"
    CHANGED = "CHANGED"


@dataclass(frozen=True)
class DiffEntry(Record):
    """One classified difference, with the nodes it touches so impact can follow."""

    category: DiffCategory
    operation: DiffOperation
    subject: str
    before: Any = None
    after: Any = None
    node_ids: tuple[str, ...] = ()
    facet: Any = None
    blocking: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "category", DiffCategory.parse(self.category, "category"))
        object.__setattr__(self, "operation", DiffOperation.parse(self.operation, "operation"))
        object.__setattr__(self, "subject", require_text(self.subject, "subject", maximum=MAX_DIFF_SUBJECT_CHARS))
        for name in ("before", "after"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _text(value, name))
        nodes = require_bounded(self.node_ids, "node_ids", maximum=MAX_IMPACT_NODES, kind="node id")
        object.__setattr__(self, "node_ids", tuple(sorted({require_identifier(item, "node_ids[]") for item in nodes})))
        if self.facet is not None:
            from .graph import DependencyFacet

            object.__setattr__(self, "facet", DependencyFacet.parse(self.facet, "facet").value)
        if self.blocking is None:
            object.__setattr__(self, "blocking", self.category.blocking_by_default)
        if not isinstance(self.blocking, bool):
            raise SchemaValidationError("blocking must be a boolean or None")
        if self.operation is DiffOperation.CHANGED and (self.before == self.after):
            raise SnapshotClosureError(
                f"diff entry for {self.subject!r} claims CHANGED while both sides agree"
            )

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.category.value, self.operation.value, self.subject)

    @property
    def text(self) -> str:
        return f"{self.category.value}:{self.operation.value}:{self.subject}"


def _text(value: Any, field: str) -> str:
    if isinstance(value, ExternalRef):
        return value.text
    if isinstance(value, (tuple, list, set, frozenset)):
        return canonical_json([_text(item, field) for item in value])
    if isinstance(value, Mapping):
        return canonical_json({str(key): _text(item, field) for key, item in value.items()})
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise SchemaValidationError(f"{field} must be text, a reference or a collection of them")
    return require_text(str(value), field, maximum=MAX_DIFF_SUBJECT_CHARS)


@dataclass(frozen=True)
class SemanticDiff(Record):
    """The classified distance between two closures, and the nodes it touches."""

    diff_id: str
    base_digest: str
    target_digest: str
    entries: tuple[DiffEntry, ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {"entries": of(DiffEntry)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "diff_id", require_id(self.diff_id, "diff_id"))
        for name in ("base_digest", "target_digest"):
            object.__setattr__(self, name, require_digest(getattr(self, name), name))
        collected = require_bounded_entries(self.entries)
        seen: set[tuple[str, str, str]] = set()
        for entry in collected:
            if entry.key in seen:
                raise SnapshotClosureError(f"diff reports {entry.text} twice")
            seen.add(entry.key)
        object.__setattr__(self, "entries", tuple(sorted(collected, key=lambda item: item.text)))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def is_empty(self) -> bool:
        return not self.entries

    @property
    def categories(self) -> tuple[DiffCategory, ...]:
        return tuple(sorted({item.category for item in self.entries}, key=lambda item: item.value))

    @property
    def blocking(self) -> tuple[DiffEntry, ...]:
        return tuple(item for item in self.entries if item.blocking)

    @property
    def affected_nodes(self) -> tuple[str, ...]:
        found: set[str] = set()
        for entry in self.entries:
            found.update(entry.node_ids)
        return tuple(sorted(found))

    def entries_in(self, *categories: Any) -> tuple[DiffEntry, ...]:
        wanted = {DiffCategory.parse(item, "categories[]") for item in categories}
        return tuple(item for item in self.entries if item.category in wanted)

    def touches(self, category: Any) -> bool:
        wanted = DiffCategory.parse(category, "category")
        return any(item.category is wanted for item in self.entries)

    def digest(self) -> str:
        return content_digest([entry.text for entry in self.entries])


def require_bounded_entries(values: Any) -> tuple[DiffEntry, ...]:
    collected = require_bounded(values, "entries", maximum=MAX_DIFF_ENTRIES)
    return tuple(DiffEntry.coerce(item, "entries[]") for item in collected)


def _closure(value: Any) -> Any:
    """Accept either side of a comparison: a committed snapshot or a bare closure."""

    from .snapshots import SnapshotClosureManifest

    closure = getattr(value, "closure", value)
    if isinstance(closure, SnapshotClosureManifest):
        return closure
    raise SchemaValidationError("semantic_diff expects two snapshots or two closure manifests")


def _projection(revision: GraphRevision) -> dict[str, Any]:
    definition = revision.definition
    return {
        "nodes": {node.node_id: content_digest(node.to_payload()) for node in definition.nodes},
        "edges": {edge.edge_id: (edge.kind.value, content_digest(edge.to_payload())) for edge in definition.edges},
        "declared": sorted(item.text for item in definition.declared_external_inputs),
        "interfaces": sorted(item.node_id for item in definition.interfaces),
    }


def semantic_diff(base: Any, target: Any, *, diff_id: str | None = None) -> SemanticDiff:
    """Classify every semantic difference between two snapshot closures."""

    left, right = _closure(base), _closure(target)
    entries: list[DiffEntry] = []
    entries.extend(_graph_entries(left.graph.revision, right.graph.revision))
    entries.extend(_selection_entries(left, right))
    entries.extend(_materialization_entries(left.graph.materializations, right.graph.materializations))
    entries.extend(_reference_entries(left, right))
    return SemanticDiff(
        diff_id=require_id(diff_id, "diff_id") if diff_id is not None else new_id(),
        base_digest=left.digest,
        target_digest=right.digest,
        entries=tuple(entries),
    )


def _graph_entries(base: GraphRevision, target: GraphRevision) -> tuple[DiffEntry, ...]:
    if base.digest == target.digest:
        return ()
    left, right = _projection(base), _projection(target)
    found: list[DiffEntry] = []
    for node_id in sorted(set(left["nodes"]) | set(right["nodes"])):
        before, after = left["nodes"].get(node_id), right["nodes"].get(node_id)
        if before is None:
            found.append(DiffEntry(
                category=DiffCategory.GRAPH_TOPOLOGY, operation=DiffOperation.ADDED,
                subject=node_id, after=after, node_ids=(node_id,),
            ))
        elif after is None:
            found.append(DiffEntry(
                category=DiffCategory.GRAPH_TOPOLOGY, operation=DiffOperation.REMOVED,
                subject=node_id, before=before, node_ids=(node_id,),
            ))
        elif before != after:
            found.append(DiffEntry(
                category=DiffCategory.NODE_DEFINITION, operation=DiffOperation.CHANGED,
                subject=node_id, before=before, after=after, node_ids=(node_id,),
            ))
    for edge_id in sorted(set(left["edges"]) | set(right["edges"])):
        before, after = left["edges"].get(edge_id), right["edges"].get(edge_id)
        if before is None or after is None:
            found.append(DiffEntry(
                category=DiffCategory.GRAPH_TOPOLOGY,
                operation=DiffOperation.ADDED if before is None else DiffOperation.REMOVED,
                subject=edge_id,
                before=_text(before, "before") if before is not None else None,
                after=_text(after, "after") if after is not None else None,
            ))
            continue
        if before == after:
            continue
        source = base.definition.edge_index.get(edge_id)
        found.append(DiffEntry(
            category=DiffCategory.DEPENDENCY_FACET, operation=DiffOperation.CHANGED,
            subject=edge_id, before=before[1], after=after[1],
            node_ids=tuple(sorted({source.source_node_id, source.target_node_id})) if source else (),
        ))
    for node_id in sorted(set(left["interfaces"]) ^ set(right["interfaces"])):
        found.append(DiffEntry(
            category=DiffCategory.GRAPH_TOPOLOGY,
            operation=DiffOperation.ADDED if node_id in right["interfaces"] else DiffOperation.REMOVED,
            subject=f"interface:{node_id}", node_ids=(node_id,),
        ))
    for reference in sorted(set(left["declared"]) ^ set(right["declared"])):
        found.append(DiffEntry(
            category=DiffCategory.GRAPH_TOPOLOGY,
            operation=DiffOperation.ADDED if reference in right["declared"] else DiffOperation.REMOVED,
            subject=reference,
        ))
    return tuple(found)


def _selection_entries(left: Any, right: Any) -> tuple[DiffEntry, ...]:
    found: list[DiffEntry] = []
    before = dict(left.graph.variant_selection)
    after = dict(right.graph.variant_selection)
    for set_id in sorted(set(before) | set(after)):
        if before.get(set_id) == after.get(set_id):
            continue
        operation = DiffOperation.CHANGED
        if set_id not in before:
            operation = DiffOperation.ADDED
        elif set_id not in after:
            operation = DiffOperation.REMOVED
        found.append(DiffEntry(
            category=DiffCategory.VARIANT_SELECTION,
            operation=operation,
            subject=set_id,
            before=before.get(set_id),
            after=after.get(set_id),
            blocking=False,
        ))
    if left.intent_ref != right.intent_ref:
        found.append(DiffEntry(
            category=DiffCategory.INTENT_BRIEF, operation=DiffOperation.CHANGED,
            subject="intent", before=left.intent_ref, after=right.intent_ref,
        ))
    return tuple(found)


def _materialization_entries(
    left: Sequence[MaterializationRecord], right: Sequence[MaterializationRecord]
) -> tuple[DiffEntry, ...]:
    before = {(item.node_id, item.port_id): item for item in left}
    after = {(item.node_id, item.port_id): item for item in right}
    found: list[DiffEntry] = []
    for key in sorted(set(before) | set(after)):
        subject = f"{key[0]}.{key[1]}"
        node_ids = (key[0],)
        if key not in before or key not in after:
            found.append(DiffEntry(
                category=DiffCategory.ASSET_REVISION,
                operation=DiffOperation.ADDED if key in after else DiffOperation.REMOVED,
                subject=subject,
                before=before[key].content_digest if key in before else None,
                after=after[key].content_digest if key in after else None,
                node_ids=node_ids,
            ))
            continue
        old, new = before[key], after[key]
        if old.content_digest != new.content_digest:
            found.append(DiffEntry(
                category=DiffCategory.ASSET_REVISION, operation=DiffOperation.CHANGED,
                subject=subject, before=old.content_digest, after=new.content_digest, node_ids=node_ids,
            ))
        elif old.revision_ref != new.revision_ref:
            # Same bytes under a different immutable revision is still a different asset.
            found.append(DiffEntry(
                category=DiffCategory.ASSET_REVISION, operation=DiffOperation.CHANGED,
                subject=subject, before=old.revision_ref, after=new.revision_ref, node_ids=node_ids,
            ))
        if old.quality != new.quality:
            found.append(DiffEntry(
                category=DiffCategory.QUALITY_DECISION, operation=DiffOperation.CHANGED,
                subject=subject,
                before=old.quality.value if old.quality else None,
                after=new.quality.value if new.quality else None,
                node_ids=node_ids,
            ))
        elif old.decision_ref != new.decision_ref:
            # A re-judgement that lands on the same class moved the evidence, not the verdict.
            found.append(DiffEntry(
                category=DiffCategory.QUALITY_DECISION, operation=DiffOperation.CHANGED,
                subject=subject, before=old.decision_ref, after=new.decision_ref, node_ids=node_ids,
            ))
        old_tools = {item.text for item in old.tool_refs}
        new_tools = {item.text for item in new.tool_refs}
        for reference in sorted(old_tools ^ new_tools):
            found.append(DiffEntry(
                category=DiffCategory.ENVIRONMENT_QUALIFICATION,
                operation=DiffOperation.REMOVED if reference in old_tools else DiffOperation.ADDED,
                subject=f"{subject}:tool:{reference}",
                before=reference if reference in old_tools else None,
                after=reference if reference in new_tools else None,
                node_ids=node_ids,
                blocking=False,
            ))
    return tuple(found)


_REFERENCE_GROUPS = (
    (DiffCategory.QUALITY_DECISION, "quality_decisions"),
    (DiffCategory.RIGHTS_PROVENANCE, "rights_refs"),
    (DiffCategory.RIGHTS_PROVENANCE, "provenance_refs"),
    (DiffCategory.DELIVERY_POLICY, "delivery_refs"),
    (DiffCategory.DELIVERY_POLICY, "policy_refs"),
    (DiffCategory.ENVIRONMENT_QUALIFICATION, "model_refs"),
    (DiffCategory.ENVIRONMENT_QUALIFICATION, "tool_refs"),
)


def _reference_entries(left: Any, right: Any) -> tuple[DiffEntry, ...]:
    """One entry per reference that appeared or disappeared, never one lump per group.

    A merge has to resolve "this branch dropped the rights record", so the diff must
    name the individual reference instead of hiding it inside a changed collection.
    """

    found: list[DiffEntry] = []
    for category, name in _REFERENCE_GROUPS:
        before = {item.text for item in getattr(left, name)}
        after = {item.text for item in getattr(right, name)}
        for reference in sorted(before ^ after):
            found.append(DiffEntry(
                category=category,
                operation=DiffOperation.REMOVED if reference in before else DiffOperation.ADDED,
                subject=f"{name}:{reference}",
                before=reference if reference in before else None,
                after=reference if reference in after else None,
            ))
    if left.environment_fingerprint != right.environment_fingerprint:
        found.append(DiffEntry(
            category=DiffCategory.ENVIRONMENT_QUALIFICATION, operation=DiffOperation.CHANGED,
            subject="environment", before=left.environment_fingerprint,
            after=right.environment_fingerprint, blocking=False,
        ))
    return tuple(found)
