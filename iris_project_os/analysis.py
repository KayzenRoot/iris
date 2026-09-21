"""M02 area B (analysis): causal fingerprints, impact cones and explain traces.

Everything here answers one question in a way an auditor can re-check: *why* does
this node need work? The answer must name a changed input, a facet, an edge and a
fingerprint difference. "The project changed" is not an acceptable cause, so no
propagation in this module is allowed to produce a dirty node without a trace.

Fingerprints hash only correctness-relevant inputs. Names, paths and free-form
metadata are excluded on purpose: they are the fields users edit without changing
what a production means, and letting them perturb a build key would silently
invalidate every cache in the graph.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Sequence

from .base import Labeled, Record, of
from .errors import GraphValidationError, PromotionBlockedError, SchemaValidationError
from .graph import (
    DependencyFacet,
    DependencySlice,
    GraphDefinition,
    GraphDelta,
    GraphNode,
    GraphRevision,
    MaterializationGraph,
)
from .identity import ExternalRef, require_id
from .limits import (
    MAX_EXPLAIN_STEPS,
    MAX_FACETS,
    MAX_FINGERPRINT_INPUTS,
    MAX_IMPACT_NODES,
)
from .versions import (
    content_digest,
    require_bounded,
    require_digest,
    require_identifier,
    require_millis,
    require_text,
)

__all__ = [
    "FingerprintContext",
    "FingerprintComponent",
    "CausalFingerprint",
    "Change",
    "ImpactEffect",
    "ExplainStep",
    "ImpactCone",
    "impact_of",
    "DiscoveryState",
    "DependencyDiscoveryReceipt",
    "DependencyLedger",
]

FINGERPRINT_SCHEMA = "iris-causal-fingerprint-v1"

# Fields that describe how a node is *presented* rather than what it computes. They
# are excluded from the fingerprint so a rename cannot invalidate a render chain.
# Anything that must affect the build key has to be declared as a policy, port,
# operation or side-effect field instead: unmodelled metadata is never causal.
NON_CAUSAL_NODE_FIELDS: frozenset[str] = frozenset({"display_name", "metadata"})
NON_CAUSAL_PORT_FIELDS: frozenset[str] = frozenset({"metadata"})


@dataclass(frozen=True)
class FingerprintContext(Record):
    """The non-graph inputs a fingerprint legitimately depends on."""

    intent_ref: Any = None
    environment_fingerprint: Any = None
    provider_refs: tuple[ExternalRef, ...] = ()
    policy_refs: tuple[ExternalRef, ...] = ()
    seed: Any = None
    schema_version: str = FINGERPRINT_SCHEMA

    NESTED = {
        "intent_ref": of(ExternalRef),
        "provider_refs": of(ExternalRef),
        "policy_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        if self.intent_ref is not None and not isinstance(self.intent_ref, ExternalRef):
            raise SchemaValidationError("intent_ref must be an ExternalRef or None")
        if self.environment_fingerprint is not None:
            object.__setattr__(
                self, "environment_fingerprint", require_digest(self.environment_fingerprint, "environment_fingerprint")
            )
        for name in ("provider_refs", "policy_refs"):
            collected = require_bounded(getattr(self, name), name, maximum=64)
            object.__setattr__(self, name, tuple(ExternalRef.coerce(item, f"{name}[]") for item in collected))
        if self.seed is not None:
            object.__setattr__(self, "seed", require_text(self.seed, "seed", maximum=128))
        object.__setattr__(self, "schema_version", require_identifier(self.schema_version, "schema_version"))


@dataclass(frozen=True)
class FingerprintComponent(Record):
    """One hashed input, kept visible so a fingerprint difference is explainable."""

    kind: str
    reference: str
    facet: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", require_identifier(self.kind, "kind"))
        object.__setattr__(self, "reference", require_text(self.reference, "reference", maximum=512))
        if self.facet is not None:
            object.__setattr__(self, "facet", DependencyFacet.parse(self.facet).value)

    @property
    def text(self) -> str:
        if self.facet is None:
            return f"{self.kind}={self.reference}"
        return f"{self.kind}={self.reference}#{self.facet}"


@dataclass(frozen=True)
class CausalFingerprint(Record):
    """The digest of everything that decides what a node computes, and nothing else."""

    node_id: str
    graph_digest: str
    components: tuple[FingerprintComponent, ...] = ()
    fingerprint: str = ""
    reproducibility: Any = None
    schema_version: str = FINGERPRINT_SCHEMA

    NESTED = {"components": of(FingerprintComponent)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "graph_digest", require_digest(self.graph_digest, "graph_digest"))
        collected = require_bounded(self.components, "components", maximum=MAX_FINGERPRINT_INPUTS)
        object.__setattr__(self, "components", tuple(FingerprintComponent.coerce(item, "components[]") for item in collected))
        if not self.components:
            raise GraphValidationError(
                f"node {self.node_id} produced an empty fingerprint; a node with no causal inputs "
                "cannot be tracked and must not be built"
            )
        ordered = tuple(sorted(self.components, key=lambda item: item.text))
        object.__setattr__(self, "components", ordered)
        recomputed = content_digest([item.text for item in ordered])
        if self.fingerprint == "":
            object.__setattr__(self, "fingerprint", recomputed)
        elif self.fingerprint != recomputed:
            raise GraphValidationError(
                f"fingerprint of {self.node_id} does not match its components: the record was altered"
            )
        if self.reproducibility is not None:
            object.__setattr__(self, "reproducibility", str(self.reproducibility))
        object.__setattr__(self, "schema_version", require_identifier(self.schema_version, "schema_version"))

    def differs_from(self, other: "CausalFingerprint") -> tuple[str, ...]:
        """The components that explain a difference, so a rebuild has a stated reason."""

        mine = {item.text for item in self.components}
        theirs = {item.text for item in other.components}
        return tuple(sorted(mine ^ theirs))


def _node_definition_projection(node: GraphNode) -> dict[str, Any]:
    payload = node.to_payload()
    return {key: value for key, value in payload.items() if key not in NON_CAUSAL_NODE_FIELDS}


def _port_projection(port: Any) -> dict[str, Any]:
    payload = port.to_payload()
    return {key: value for key, value in payload.items() if key not in NON_CAUSAL_PORT_FIELDS}


def node_definition_component(node: GraphNode) -> FingerprintComponent:
    return FingerprintComponent(
        kind="node-definition",
        reference=content_digest(_node_definition_projection(node)),
    )


def compute_fingerprint(
    bound: MaterializationGraph,
    node_id: str,
    *,
    context: FingerprintContext | None = None,
) -> CausalFingerprint:
    """Hash the correctness-relevant inputs of one node in a bound graph."""

    definition = bound.revision.definition
    node = definition.node(node_id)
    # The revision digest is recorded as provenance but never hashed: a cosmetic
    # edit anywhere in the graph creates a new revision, and folding that into
    # every node key would invalidate every cache for a rename.
    components: list[FingerprintComponent] = [node_definition_component(node)]
    if node.reproducibility is not None:
        components.append(FingerprintComponent(kind="reproducibility", reference=str(node.reproducibility)))
    for port in (*node.inputs, *node.outputs):
        components.append(
            FingerprintComponent(
                kind="port",
                reference=content_digest(_port_projection(port)),
            )
        )
    for edge in definition.edges:
        if edge.target_node_id != node_id:
            continue
        if edge.kind.never_creates_rebuild_dependency:
            continue
        producer = bound.materialization_of(edge.source_node_id, edge.source_port_id)
        reference = producer.content_digest if producer is not None else "unbound"
        for facet in edge.facets:
            components.append(
                FingerprintComponent(
                    kind=f"input.{edge.source_node_id}.{edge.source_port_id}",
                    reference=reference,
                    facet=facet,
                )
            )
        if edge.slice is not None:
            components.append(FingerprintComponent(kind="slice", reference=edge.slice.text))
    own = bound.materialization_of_first(node_id)
    if own is not None:
        if own.quality_class is not None:
            components.append(FingerprintComponent(kind="quality-decision", reference=str(own.quality_class)))
        if own.decision_ref is not None:
            components.append(FingerprintComponent(kind="human-decision", reference=own.decision_ref.text))
        for tool in own.tool_refs:
            components.append(FingerprintComponent(kind="tool", reference=tool.text))
        if own.seed is not None:
            components.append(FingerprintComponent(kind="seed", reference=str(own.seed)))
    selected = {f"{key}={value}" for key, value in bound.variant_selection}
    if selected:
        components.append(FingerprintComponent(kind="variant", reference=content_digest(sorted(selected))))
    if context is not None:
        if context.intent_ref is not None:
            components.append(FingerprintComponent(kind="intent", reference=context.intent_ref.text))
        if context.environment_fingerprint is not None:
            components.append(
                FingerprintComponent(kind="environment", reference=context.environment_fingerprint)
            )
        for provider in context.provider_refs:
            components.append(FingerprintComponent(kind="provider", reference=provider.text))
        for policy in context.policy_refs:
            components.append(FingerprintComponent(kind="policy", reference=policy.text))
        if context.seed is not None:
            components.append(FingerprintComponent(kind="seed", reference=str(context.seed)))
    return CausalFingerprint(
        node_id=node_id,
        graph_digest=bound.revision.digest,
        components=tuple(components),
        reproducibility=node.reproducibility,
    )


class ImpactEffect(Labeled):
    """What a change does to a consumer."""

    DIRTY_MATERIAL = "DIRTY_MATERIAL"
    REVALIDATE = "REVALIDATE"
    CONDITIONAL = "CONDITIONAL"
    UNCHANGED = "UNCHANGED"


@dataclass(frozen=True)
class Change(Record):
    """A stated cause. Every entry in an impact cone must trace back to one."""

    node_id: str
    facet: DependencyFacet
    port_id: Any = None
    previous_digest: Any = None
    current_digest: Any = None
    slice: Any = None

    NESTED = {"slice": of(DependencySlice)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "facet", DependencyFacet.parse(self.facet, "facet"))
        if self.port_id is not None:
            object.__setattr__(self, "port_id", require_identifier(self.port_id, "port_id"))
        for name in ("previous_digest", "current_digest"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_digest(value, name))
        if self.slice is not None and not isinstance(self.slice, DependencySlice):
            raise SchemaValidationError("slice must be a DependencySlice or None")

    @property
    def key(self) -> tuple[str, Any]:
        return (self.node_id, self.port_id)

    @property
    def describes_replacement(self) -> bool:
        """A change that names two different digests replaced bytes; otherwise it is a re-assertion."""

        return (
            self.previous_digest is not None
            and self.current_digest is not None
            and self.previous_digest != self.current_digest
        )


@dataclass(frozen=True)
class ExplainStep(Record):
    """One hop of an impact trace: changed thing, facet, edge, consumer, effect."""

    changed_node_id: str
    facet: DependencyFacet
    edge_id: Any
    consumer_node_id: str
    effect: ImpactEffect
    reason: str
    fingerprint_difference: tuple[str, ...] = ()
    ordinal: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "changed_node_id", require_identifier(self.changed_node_id, "changed_node_id"))
        object.__setattr__(self, "facet", DependencyFacet.parse(self.facet, "facet"))
        if self.edge_id is not None:
            object.__setattr__(self, "edge_id", require_identifier(self.edge_id, "edge_id"))
        object.__setattr__(self, "consumer_node_id", require_identifier(self.consumer_node_id, "consumer_node_id"))
        object.__setattr__(self, "effect", ImpactEffect.parse(self.effect, "effect"))
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=1024))
        difference = require_bounded(self.fingerprint_difference, "fingerprint_difference", maximum=64)
        object.__setattr__(self, "fingerprint_difference", tuple(require_text(item, "fingerprint_difference[]", maximum=512) for item in difference))
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int) or self.ordinal < 0:
            raise SchemaValidationError("ordinal must be a non-negative integer")


@dataclass(frozen=True)
class ImpactCone(Record):
    """Directly dirty, transitively dirty, conditionally affected, clean, and why."""

    roots: tuple[str, ...]
    facets: tuple[DependencyFacet, ...]
    direct: tuple[str, ...] = ()
    transitive: tuple[str, ...] = ()
    conditional: tuple[str, ...] = ()
    revalidating: tuple[str, ...] = ()
    clean: tuple[str, ...] = ()
    explanation: tuple[ExplainStep, ...] = ()

    NESTED = {"explanation": of(ExplainStep)}

    def __post_init__(self) -> None:
        for name in ("roots", "direct", "transitive", "conditional", "revalidating", "clean"):
            collected = require_bounded(getattr(self, name), name, maximum=MAX_IMPACT_NODES, kind="node id")
            object.__setattr__(self, name, tuple(require_identifier(item, f"{name}[]") for item in collected))
        facets = require_bounded(self.facets, "facets", maximum=MAX_FACETS)
        object.__setattr__(self, "facets", tuple(sorted({DependencyFacet.parse(item) for item in facets}, key=lambda item: item.value)))
        steps = require_bounded(self.explanation, "explanation", maximum=MAX_EXPLAIN_STEPS)
        object.__setattr__(self, "explanation", tuple(ExplainStep.coerce(item, "explanation[]") for item in steps))
        if not self.roots:
            raise GraphValidationError("an impact cone needs at least one stated root cause")
        if (self.direct or self.transitive) and not self.explanation:
            raise GraphValidationError(
                "an impact cone that dirties work must carry an explanation; a rebuild without a "
                "named cause is exactly the 'the project changed' failure this kernel forbids"
            )
        overlap = set(self.direct) & set(self.transitive)
        if overlap:
            raise GraphValidationError(f"nodes are both direct and transitive: {sorted(overlap)}")
        affected = set(self.direct) | set(self.transitive) | set(self.conditional) | set(self.revalidating)
        object.__setattr__(
            self, "clean", tuple(sorted(set(self.clean) - affected))
        )

    @property
    def requires_work(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.direct) | set(self.transitive)))

    def reason_for(self, node_id: str) -> tuple[ExplainStep, ...]:
        return tuple(step for step in self.explanation if step.consumer_node_id == node_id)

    def explains_traversal(self, definition: GraphDefinition) -> bool:
        """Every claimed hop must be a real edge in the revision it was computed from."""

        index = definition.edge_index
        for step in self.explanation:
            if step.edge_id is None:
                return False
            edge = index.get(step.edge_id)
            if edge is None or edge.target_node_id != step.consumer_node_id:
                return False
            if edge.source_node_id != step.changed_node_id:
                return False
        return True


def impact_of(
    bound: MaterializationGraph,
    changes: Sequence[Change],
    *,
    fingerprints: Mapping[str, CausalFingerprint] | None = None,
) -> ImpactCone:
    """Propagate stated changes through the bound graph, facet by facet.

    Material edges dirty their consumers. Constraint and evidence edges force
    revalidation without rebuilding bytes. Activation edges make consumers
    conditionally affected, because whether they matter depends on a selection
    this call cannot resolve. Ordering and observation edges stop the walk.
    """

    resolved = tuple(Change.coerce(item, "changes[]") for item in changes)
    if not resolved:
        raise GraphValidationError("impact requires at least one stated change")
    definition = bound.revision.definition
    known = definition.node_index
    for change in resolved:
        if change.node_id not in known:
            raise GraphValidationError(
                f"change names unknown node {change.node_id!r} of graph {definition.graph_id}"
            )

    facets = tuple(sorted({change.facet for change in resolved}, key=lambda item: item.value))
    roots = tuple(sorted({change.node_id for change in resolved}))
    steps: list[ExplainStep] = []
    effects: dict[str, ImpactEffect] = {}
    shallowest: dict[str, int] = {}
    frontier = deque((change.node_id, change, 0) for change in resolved)
    seen_edges: set[tuple[str, str, str]] = set()
    while frontier:
        node_id, change, depth = frontier.popleft()
        if depth > MAX_EXPLAIN_STEPS:
            raise GraphValidationError(
                f"impact propagation from {roots[0]} exceeded the admitted depth {MAX_EXPLAIN_STEPS}"
            )
        for edge in definition.edges_out_of(node_id):
            if edge.kind.never_creates_rebuild_dependency:
                continue
            if change.facet not in edge.facets:
                continue
            if edge.slice is not None and change.slice is not None and not edge.slice.overlaps(change.slice):
                continue
            marker = (edge.edge_id, change.facet.value, change.node_id)
            if marker in seen_edges:
                continue
            seen_edges.add(marker)
            consumer = edge.target_node_id
            if edge.kind.dirties_material:
                effect = ImpactEffect.DIRTY_MATERIAL
            elif edge.kind.revalidates_consumer:
                effect = ImpactEffect.REVALIDATE
            else:
                effect = ImpactEffect.CONDITIONAL
            difference: tuple[str, ...] = ()
            if fingerprints is not None:
                before = fingerprints.get(consumer)
                if before is not None:
                    moved = f"input.{node_id}."
                    difference = tuple(
                        item.text for item in before.components if item.kind.startswith(moved)
                    )[:4]
            previous = effects.get(consumer)
            rank = _EFFECT_RANK.get(effect, 0)
            if previous is not None and _EFFECT_RANK.get(previous, 0) >= rank:
                effect = previous
            effects[consumer] = effect
            if effect is ImpactEffect.DIRTY_MATERIAL and depth < shallowest.get(consumer, depth + 1):
                shallowest[consumer] = depth
            if len(steps) >= MAX_EXPLAIN_STEPS:
                raise GraphValidationError(
                    f"impact propagation from {roots[0]} exceeded the admitted "
                    f"{MAX_EXPLAIN_STEPS} explain steps"
                )
            steps.append(
                ExplainStep(
                    changed_node_id=node_id,
                    facet=change.facet,
                    edge_id=edge.edge_id,
                    consumer_node_id=consumer,
                    effect=effect,
                    reason=(
                        f"{node_id} changed in facet {change.facet.value}; edge {edge.edge_id} "
                        f"({edge.kind.value}) makes {consumer} {effect.value}"
                    ),
                    fingerprint_difference=difference,
                    ordinal=len(steps),
                )
            )
            if effect is ImpactEffect.DIRTY_MATERIAL:
                frontier.append((consumer, change, depth + 1))

    dirty = {node for node, item in effects.items() if item is ImpactEffect.DIRTY_MATERIAL}
    direct = {node for node in dirty if shallowest[node] == 0}
    transitive = dirty - direct
    revalidating = {
        node for node, item in effects.items() if item is ImpactEffect.REVALIDATE
    } - dirty
    conditional = {
        node for node, item in effects.items() if item is ImpactEffect.CONDITIONAL
    } - dirty - revalidating
    touched = dirty | revalidating | conditional
    clean = tuple(sorted(set(known) - touched - set(roots)))
    return ImpactCone(
        roots=roots,
        facets=facets,
        direct=tuple(sorted(direct)),
        transitive=tuple(sorted(transitive)),
        conditional=tuple(sorted(conditional)),
        revalidating=tuple(sorted(revalidating)),
        clean=clean,
        explanation=tuple(steps),
    )


_EFFECT_RANK: dict[ImpactEffect, int] = {
    ImpactEffect.CONDITIONAL: 1,
    ImpactEffect.REVALIDATE: 2,
    ImpactEffect.DIRTY_MATERIAL: 3,
}


class DiscoveryState(Labeled):
    """Where an observed dependency stands. Only ADMITTED may back a promotion."""

    UNDECLARED = "UNDECLARED"
    QUARANTINED = "QUARANTINED"
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class DependencyDiscoveryReceipt(Record):
    """Proof that something outside the declared graph was read during an attempt.

    A discovered dependency never mutates the frozen revision it was observed in.
    It becomes usable only through an explicit Graph Delta on a new revision.
    """

    discovery_id: str
    observed_by: ExternalRef
    attempt_id: str
    consumer_node_id: str
    observed_reference: ExternalRef
    facets: tuple[DependencyFacet, ...] = (DependencyFacet.CONTENT,)
    state: DiscoveryState = DiscoveryState.UNDECLARED
    proposed_delta: Any = None
    admission_receipt_id: Any = None
    observed_at_ms: int = 0

    NESTED = {
        "observed_by": of(ExternalRef),
        "observed_reference": of(ExternalRef),
        "proposed_delta": of(GraphDelta),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "discovery_id", require_id(self.discovery_id, "discovery_id"))
        for name in ("observed_by", "observed_reference"):
            if not isinstance(getattr(self, name), ExternalRef):
                raise SchemaValidationError(f"{name} must be an ExternalRef")
        object.__setattr__(self, "attempt_id", require_id(self.attempt_id, "attempt_id"))
        object.__setattr__(self, "consumer_node_id", require_identifier(self.consumer_node_id, "consumer_node_id"))
        facets = require_bounded(self.facets, "facets", maximum=MAX_FACETS)
        resolved = tuple(DependencyFacet.parse(item, "facets[]") for item in facets)
        if not resolved:
            raise SchemaValidationError("a discovery receipt must name the facets it observed")
        object.__setattr__(self, "facets", tuple(sorted(set(resolved), key=lambda item: item.value)))
        object.__setattr__(self, "state", DiscoveryState.parse(self.state, "state"))
        if self.proposed_delta is not None and not isinstance(self.proposed_delta, GraphDelta):
            raise SchemaValidationError("proposed_delta must be a GraphDelta or None")
        if self.admission_receipt_id is not None:
            object.__setattr__(self, "admission_receipt_id", require_id(self.admission_receipt_id, "admission_receipt_id"))
        object.__setattr__(self, "observed_at_ms", require_millis(self.observed_at_ms, "observed_at_ms"))
        if self.state is DiscoveryState.ADMITTED and self.admission_receipt_id is None:
            raise PromotionBlockedError(
                f"discovery {self.discovery_id} claims ADMITTED without an admission receipt"
            )

    @property
    def is_material(self) -> bool:
        return DependencyFacet.CONTENT in self.facets or DependencyFacet.SEMANTICS in self.facets

    def declared_in(self, definition: GraphDefinition) -> bool:
        return any(
            item.kind is self.observed_reference.kind and item.reference == self.observed_reference.reference
            for item in definition.declared_external_inputs
        )


@dataclass
class DependencyLedger:
    """Records observed reads and turns admitted ones into new graph revisions."""

    _receipts: dict[str, DependencyDiscoveryReceipt] = field(default_factory=dict)

    def observe(self, receipt: DependencyDiscoveryReceipt) -> DependencyDiscoveryReceipt:
        if not isinstance(receipt, DependencyDiscoveryReceipt):
            raise SchemaValidationError("observe expects a DependencyDiscoveryReceipt")
        stored = self._receipts.get(receipt.discovery_id)
        if stored is not None:
            if stored != receipt:
                raise GraphValidationError(
                    f"discovery {receipt.discovery_id} was already recorded differently; "
                    "a receipt is immutable, so re-observe under a new id"
                )
            return stored
        self._receipts[receipt.discovery_id] = receipt
        return receipt

    def receipt(self, discovery_id: str) -> DependencyDiscoveryReceipt:
        wanted = require_id(discovery_id, "discovery_id")
        try:
            return self._receipts[wanted]
        except KeyError as error:
            raise GraphValidationError(f"unknown discovery {wanted!r}") from error

    def undeclared_material_for(self, revision: GraphRevision) -> tuple[DependencyDiscoveryReceipt, ...]:
        declared = {
            item.reference for item in revision.definition.declared_external_inputs
        }
        return tuple(
            receipt
            for receipt in self._receipts.values()
            if receipt.is_material
            and receipt.observed_reference.reference not in declared
            and receipt.state is not DiscoveryState.REJECTED
        )

    def admit(
        self,
        discovery_id: str,
        revision: GraphRevision,
        *,
        delta: GraphDelta,
        state: DiscoveryState = DiscoveryState.ADMITTED,
    ) -> GraphRevision:
        """Admit a discovery by producing a new revision; the frozen one is never edited."""

        receipt = self.receipt(discovery_id)
        if receipt.state is DiscoveryState.REJECTED:
            raise PromotionBlockedError(
                f"discovery {receipt.discovery_id} was rejected and cannot be admitted"
            )
        if state is not DiscoveryState.ADMITTED:
            raise PromotionBlockedError(
                "only an ADMITTED discovery may enter a revision; quarantine is recorded, not admitted"
            )
        if delta.graph_id != revision.graph_id or delta.base_version != revision.version:
            raise GraphValidationError(
                f"delta {delta.delta_id} does not apply to revision {revision.revision_id} "
                f"(graph {delta.graph_id} v{delta.base_version} vs {revision.graph_id} v{revision.version})"
            )
        if not delta.declares(receipt.observed_reference):
            raise GraphValidationError(
                f"delta {delta.delta_id} does not declare the observed dependency "
                f"{receipt.observed_reference.text}, so admitting it would keep the read hidden"
            )
        admitted = revision.derive(delta)
        self._receipts[discovery_id] = replace(
            receipt,
            state=state,
            proposed_delta=delta,
            admission_receipt_id=admitted.revision_id,
        )
        return admitted

    @property
    def receipts(self) -> tuple[DependencyDiscoveryReceipt, ...]:
        return tuple(self._receipts[key] for key in sorted(self._receipts))
