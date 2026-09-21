"""Construction helpers shared by the M02 kernel tests.

The kernel is verbose by design: every node must declare reproducibility, every
edge must declare its facets. These helpers keep a test focused on the one
property it is proving instead of spending forty lines on a legal graph.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Iterable, Sequence

from iris_project_os.analysis import Change, DependencyDiscoveryReceipt, FingerprintContext, compute_fingerprint
from iris_project_os.branching import ForkReceipt
from iris_project_os.build import closure_of
from iris_project_os.reuse import (
    CacheEntry,
    CacheKey,
    CacheLayer,
    CacheTrust,
    CompatibilityKind,
    CompatibilityRef,
    ContextFingerprint,
    ContextSource,
    OriginClass,
    Qualification,
    ReuseClass,
    ReuseReceipt,
    ReuseRequest,
    admit_reuse,
)
from iris_project_os.graph import (
    DeltaKind,
    DependencyFacet,
    DependencySlice,
    EdgeKind,
    GraphDefinition,
    GraphDelta,
    GraphEdge,
    GraphMutation,
    GraphNode,
    GraphRevision,
    MaterializationGraph,
    MaterializationRecord,
    NodeRole,
    PortCardinality,
    PortDirection,
    ReproducibilityClass,
    SemanticPort,
    SemanticTypeRef,
    SideEffectClass,
    SideEffectPolicy,
)
from iris_project_os.identity import (
    ArtifactIdentity,
    EntityKind,
    ExternalRef,
    RevisionRef,
    TransitionReceipt,
    new_id,
)
from iris_project_os.snapshots import Snapshot, SnapshotClass, SnapshotClosureManifest, commit_snapshot
from iris_project_os.versions import ComponentVersion, content_digest

VECTOR = "vector.svg"
RASTER = "raster.png"
TEXT = "text.script"

CACHE_NOW = 1_700_000_000_000
CACHE_PRODUCER = ComponentVersion("m02.render", "1.4.2")
CACHE_EVALUATOR = ComponentVersion("m02.judge", "2.0.0")


def digest(seed: str) -> str:
    """A stable 64-hex digest for any string, so fixtures do not hardcode hashes."""

    return sha256(seed.encode("utf-8")).hexdigest()


def semantic_type(type_id: str = VECTOR, *, schema: str = "schema.vector", version: str = "1.0.0") -> SemanticTypeRef:
    return SemanticTypeRef(
        type_id=type_id,
        schema_ref=ExternalRef(kind=EntityKind.SCHEMA, reference=schema, version=version),
    )


def ref(kind: EntityKind = EntityKind.POLICY, reference: str = "policy.default", version: Any = None) -> ExternalRef:
    return ExternalRef(kind=kind, reference=reference, version=version)


def port(
    port_id: str,
    direction: PortDirection,
    *,
    type_id: str = VECTOR,
    cardinality: PortCardinality = PortCardinality.ONE,
    required: bool = True,
    minimum_quality_class: Any = None,
    activation_ref: Any = None,
) -> SemanticPort:
    return SemanticPort(
        port_id=port_id,
        direction=direction,
        semantic_type=semantic_type(type_id, schema=f"schema.{type_id.split('.')[0]}"),
        cardinality=cardinality,
        required=required,
        minimum_quality_class=minimum_quality_class,
        activation_ref=activation_ref,
    )


def output(port_id: str = "out", **kwargs: Any) -> SemanticPort:
    return port(port_id, PortDirection.OUTPUT, **kwargs)


def input_port(port_id: str = "in", **kwargs: Any) -> SemanticPort:
    return port(port_id, PortDirection.INPUT, **kwargs)


def node(
    node_id: str,
    role: NodeRole,
    *,
    inputs: Sequence[SemanticPort] = (),
    outputs: Sequence[SemanticPort] = (),
    reproducibility: Any = ReproducibilityClass.DETERMINISTIC,
    side_effect: SideEffectClass = SideEffectClass.NO_SIDE_EFFECT,
    side_effect_policy: Any = None,
    epoch: int = 0,
    display_name: str = "",
    **kwargs: Any,
) -> GraphNode:
    return GraphNode(
        node_id=node_id,
        role=role,
        inputs=tuple(inputs),
        outputs=tuple(outputs),
        reproducibility=reproducibility,
        side_effect=side_effect,
        side_effect_policy=side_effect_policy,
        epoch=epoch,
        display_name=display_name,
        **kwargs,
    )


def source(node_id: str = "source.logo", *, type_id: str = VECTOR, port_id: str = "out") -> GraphNode:
    return node(
        node_id,
        NodeRole.SOURCE,
        outputs=(output(port_id, type_id=type_id),),
        reproducibility=ReproducibilityClass.EXTERNAL_STATE,
    )


def operation(
    node_id: str = "render.logo",
    *,
    in_type: str = VECTOR,
    out_type: str = RASTER,
    in_port: str = "in",
    out_port: str = "out",
    reproducibility: Any = ReproducibilityClass.DETERMINISTIC,
    **kwargs: Any,
) -> GraphNode:
    return node(
        node_id,
        NodeRole.OPERATION,
        inputs=(input_port(in_port, type_id=in_type),),
        outputs=(output(out_port, type_id=out_type),),
        reproducibility=reproducibility,
        **kwargs,
    )


def delivery(node_id: str = "deliver.web", *, type_id: str = RASTER, **kwargs: Any) -> GraphNode:
    return node(
        node_id,
        NodeRole.DELIVERY,
        inputs=(input_port("in", type_id=type_id),),
        outputs=(output("out", type_id=type_id),),
        reproducibility=ReproducibilityClass.DETERMINISTIC,
        side_effect=SideEffectClass.CONTROLLED_OUTPUTS,
        **kwargs,
    )


def validation(node_id: str = "validate.quality", *, type_id: str = RASTER, **kwargs: Any) -> GraphNode:
    return node(
        node_id,
        NodeRole.VALIDATION,
        inputs=(input_port("in", type_id=type_id),),
        outputs=(output("out", type_id="verdict.json"),),
        reproducibility=None,
        **kwargs,
    )


def edge(
    edge_id: str,
    source_node: str,
    target_node: str,
    *,
    kind: EdgeKind = EdgeKind.MATERIAL_CAUSAL,
    facets: Iterable[DependencyFacet] = (DependencyFacet.CONTENT,),
    source_port_id: str = "out",
    target_port_id: str = "in",
    order: Any = None,
    slice: Any = None,
    feedback: bool = False,
) -> GraphEdge:
    return GraphEdge(
        edge_id=edge_id,
        kind=kind,
        source_node_id=source_node,
        source_port_id=source_port_id,
        target_node_id=target_node,
        target_port_id=target_port_id,
        facets=tuple(facets),
        order=order,
        slice=slice,
        feedback=feedback,
    )


def definition(
    *nodes: GraphNode,
    edges: Sequence[GraphEdge] = (),
    declared: Sequence[ExternalRef] = (ref(EntityKind.ARTIFACT, "asset.logo"),),
    graph_id: str = "graph.test",
    version: int = 1,
    **kwargs: Any,
) -> GraphDefinition:
    return GraphDefinition(
        graph_id=graph_id,
        version=version,
        nodes=tuple(nodes),
        edges=tuple(edges),
        declared_external_inputs=tuple(declared),
        **kwargs,
    )


def chain_definition(**kwargs: Any) -> GraphDefinition:
    """source.logo -> render.logo -> deliver.web, the smallest legal production chain."""

    return definition(
        source(),
        operation(),
        delivery(),
        edges=(
            edge("edge.render", "source.logo", "render.logo"),
            edge("edge.deliver", "render.logo", "deliver.web"),
        ),
        **kwargs,
    )


def chain_revision(**kwargs: Any) -> GraphRevision:
    return revision(chain_definition(**kwargs))


def revision(definition_value: GraphDefinition, **kwargs: Any) -> GraphRevision:
    return GraphRevision(revision_id=new_id(), definition=definition_value, **kwargs)


def materialization(
    node_id: str,
    *,
    port_id: str = "out",
    seed: str | None = None,
    quality_class: Any = None,
    attempt: Any = None,
    revision_reference: str | None = None,
    tools: Sequence[ExternalRef] = (),
    decision: Any = None,
    produced_at_ms: int = 1_700_000_000_000,
) -> MaterializationRecord:
    key = seed or f"{node_id}.{port_id}"
    return MaterializationRecord(
        node_id=node_id,
        port_id=port_id,
        revision_ref=ref(
            EntityKind.REVISION, revision_reference or f"rev.{key}", "1"
        ),
        content_digest=digest(key),
        producer_attempt_id=attempt,
        quality_class=quality_class,
        decision_ref=decision,
        tool_refs=tuple(tools),
        produced_at_ms=produced_at_ms,
    )


def bound(
    *,
    records: Sequence[MaterializationRecord] = (),
    revision_value: GraphRevision | None = None,
    variant_selection: Sequence[tuple[str, str]] = (),
    environment: str | None = None,
    **kwargs: Any,
) -> MaterializationGraph:
    if not records:
        records = (
            materialization("source.logo"),
            materialization("render.logo"),
            materialization("deliver.web"),
        )
    return MaterializationGraph(
        revision=revision_value or chain_revision(),
        materializations=tuple(records),
        variant_selection=tuple(variant_selection),
        environment_fingerprint=digest(environment) if environment else None,
        **kwargs,
    )


def chain_records(
    node_ids: Sequence[str] = ("source.logo", "render.logo", "deliver.web"),
    **over: Any,
) -> tuple[MaterializationRecord, ...]:
    """One attempt and one bound decision per node — the shape a VALIDATED closure owes."""

    return tuple(
        materialization(node_id, attempt=new_id(), decision=ref(EntityKind.QUALITY_DECISION, new_id()), **over)
        for node_id in node_ids
    )


def closure(
    *,
    production_id: str,
    graph: MaterializationGraph | None = None,
    project_id: str = "iris",
    branch_id: str = "branch.main",
    **over: Any,
) -> SnapshotClosureManifest:
    """A closure over the chain graph: every declared input admitted, every node judged."""

    graph_value = graph or bound(records=chain_records())
    return SnapshotClosureManifest(
        project_id=project_id,
        production_id=production_id,
        branch_id=branch_id,
        graph=graph_value,
        external_admissions=tuple(
            ExternalRef(kind=item.kind, reference=item.reference)
            for item in graph_value.revision.definition.declared_external_inputs
        ),
        quality_decisions=tuple(
            item.decision_ref for item in graph_value.materializations if item.decision_ref is not None
        ),
        rights_refs=(ref(EntityKind.RIGHTS, new_id()),),
        provenance_refs=(ref(EntityKind.PROVENANCE, new_id()),),
        policy_refs=(ref(EntityKind.POLICY, new_id()),),
        delivery_refs=(ref(EntityKind.DESTINATION, new_id()),),
        environment_refs=(ref(EntityKind.ENVIRONMENT, new_id()),),
        tool_refs=(ref(EntityKind.TOOL, new_id()),),
        model_refs=(ref(EntityKind.MODEL, new_id()),),
        **over,
    )


def snapshot(
    *,
    production_id: str,
    klass: Any = SnapshotClass.VALIDATED_SNAPSHOT,
    actor: ComponentVersion | None = None,
    created_at_ms: int = CACHE_NOW,
    closure_value: SnapshotClosureManifest | None = None,
    **over: Any,
) -> Snapshot:
    return commit_snapshot(
        closure_value or closure(production_id=production_id),
        snapshot_class=klass,
        actor=actor,
        created_at_ms=created_at_ms,
        **over,
    )


def context(*, environment: str | None = None, intent: str = "intent.brief") -> FingerprintContext:
    return FingerprintContext(
        intent_ref=ref(EntityKind.POLICY, intent),
        environment_fingerprint=digest(environment) if environment else None,
    )


def change(
    node_id: str,
    facet: DependencyFacet = DependencyFacet.CONTENT,
    *,
    previous: str | None = None,
    current: str | None = None,
    **kwargs: Any,
) -> Change:
    return Change(
        node_id=node_id,
        facet=facet,
        previous_digest=digest(previous) if previous else None,
        current_digest=digest(current) if current else None,
        **kwargs,
    )


def delta(mutations: Sequence[Any], *, graph_id: str = "graph.test", base_version: int = 1, **kwargs: Any) -> GraphDelta:
    return GraphDelta(
        delta_id=new_id(),
        graph_id=graph_id,
        base_version=base_version,
        mutations=tuple(mutations),
        **kwargs,
    )


def component_version(identifier: str = "m02.test", version: str = "1.0.0") -> ComponentVersion:
    return ComponentVersion(identifier, version)


def artifact_identity(**over: Any) -> ArtifactIdentity:
    """One registered artifact: an id, an owner and a meaning that revisions may not change."""

    payload: dict[str, Any] = dict(
        artifact_id=new_id(),
        production_id=new_id(),
        semantic_type_ref=ref(EntityKind.SEMANTIC_TYPE, VECTOR),
        display_name="logo",
        created_at_ms=CACHE_NOW,
    )
    payload.update(over)
    return ArtifactIdentity(**payload)


def revision_ref(record: ArtifactIdentity, **over: Any) -> RevisionRef:
    """A revision of ``record`` that inherits the artifact's semantic type unless told otherwise."""

    payload: dict[str, Any] = dict(
        artifact_id=record.artifact_id,
        revision_id=new_id(),
        content_digest=digest("first bytes"),
        semantic_type_ref=record.semantic_type_ref,
        created_at_ms=CACHE_NOW,
    )
    payload.update(over)
    return RevisionRef(**payload)


def fork_receipt(**over: Any) -> ForkReceipt:
    payload: dict[str, Any] = dict(
        fork_id=new_id(),
        source_branch_id=new_id(),
        source_snapshot_id=new_id(),
        new_branch_id=new_id(),
        reason_code="alternate-direction",
        created_at_ms=CACHE_NOW,
    )
    payload.update(over)
    return ForkReceipt(**payload)


def transition_receipt(**over: Any) -> TransitionReceipt:
    payload: dict[str, Any] = dict(
        transition_id=new_id(),
        entity_kind=EntityKind.PRODUCTION,
        entity_id=new_id(),
        from_state="DRAFT",
        to_state="ACTIVE",
        actor=component_version("m02.os", "1.0.0"),
        reason_code="first-promotion",
        timestamp_ms=CACHE_NOW,
    )
    payload.update(over)
    return TransitionReceipt(**payload)


def discovery_receipt(**over: Any) -> DependencyDiscoveryReceipt:
    payload: dict[str, Any] = dict(
        discovery_id=new_id(),
        observed_by=ref(EntityKind.ATTEMPT, new_id()),
        attempt_id=new_id(),
        consumer_node_id="render.logo",
        observed_reference=ref(EntityKind.ARTIFACT, "asset.font"),
        observed_at_ms=CACHE_NOW,
    )
    payload.update(over)
    return DependencyDiscoveryReceipt(**payload)


def mutation(kind: DeltaKind = DeltaKind.ADD_DECLARED_INPUT, target_id: str = "asset.font", **over: Any) -> GraphMutation:
    """One typed definition change; a delta is a list of these plus the version it expects."""

    payload: dict[str, Any] = dict(kind=kind, target_id=target_id)
    if kind is DeltaKind.ADD_DECLARED_INPUT:
        payload["declared_input"] = ref(EntityKind.ARTIFACT, target_id)
    payload.update(over)
    return GraphMutation(**payload)


def cache_context(**over: Any) -> ContextFingerprint:
    """The context half of a cache key: the same brief, model and tools every time."""

    base: dict[str, Any] = dict(
        sources=(
            ContextSource(ref=ref(EntityKind.HIVE_CONTEXT, "brief.front"), ordinal=0),
            ContextSource(ref=ref(EntityKind.HIVE_CONTEXT, "brief.style"), ordinal=1),
        ),
        compiler=component_version("m02.context", "3.1.0"),
        model=component_version("provider.model", "2026-01"),
        tokenizer=component_version("provider.tokenizer", "4"),
        policy=component_version("m02.instruction-policy", "1.1.0"),
        profile="web",
        tool_schemas=(ref(EntityKind.SCHEMA, "schema.tool.render", version="2"),),
        compatibility=(
            CompatibilityRef(
                kind=CompatibilityKind.PROVIDER, provider_id="provider.a", opaque_digest=digest("provider-a")
            ),
        ),
    )
    base.update(over)
    return ContextFingerprint(**base)


def cache_qualification(**over: Any) -> Qualification:
    base: dict[str, Any] = dict(
        refs=(ref(EntityKind.ENVIRONMENT, "env.linux.x86_64", version="9"),),
        expires_at_ms=CACHE_NOW + 86_400_000,
    )
    base.update(over)
    return Qualification(**base)


def cache_trust(**over: Any) -> CacheTrust:
    base: dict[str, Any] = dict(allowed_producers=(CACHE_PRODUCER,))
    base.update(over)
    return CacheTrust(**base)


def cache_entry(
    bound_graph: MaterializationGraph,
    node_id: str,
    *,
    layer: CacheLayer = CacheLayer.INTERMEDIATE,
    context: ContextFingerprint | None = None,
    **over: Any,
) -> CacheEntry:
    """An entry that states exactly the claim this bound graph makes about ``node_id``."""

    fingerprint = compute_fingerprint(bound_graph, node_id)
    base: dict[str, Any] = dict(
        entry_id=new_id(),
        key=CacheKey.of(
            node_id, build_fingerprint=fingerprint.fingerprint, context=context or cache_context(), layer=layer
        ),
        reuse_class=ReuseClass.EXACT_REUSE,
        producer=CACHE_PRODUCER,
        writer_origin=OriginClass.TRUSTED_WORKER,
        project_id="iris",
        result_digest=digest(f"bytes.{node_id}"),
        revision_ref=ref(EntityKind.REVISION, "rev.0001", "1"),
        dependency_closure=closure_of(fingerprint),
        qualification=cache_qualification(),
        recorded_at_ms=CACHE_NOW - 1_000,
    )
    base["observed_digest"] = over.get("observed_digest", base["result_digest"])
    base.update(over)
    return CacheEntry(**base)


def reuse_request(
    bound_graph: MaterializationGraph,
    node_id: str,
    *,
    layer: CacheLayer = CacheLayer.INTERMEDIATE,
    context: ContextFingerprint | None = None,
    **over: Any,
) -> ReuseRequest:
    fingerprint = compute_fingerprint(bound_graph, node_id)
    base: dict[str, Any] = dict(
        node_id=node_id,
        key=CacheKey.of(
            node_id, build_fingerprint=fingerprint.fingerprint, context=context or cache_context(), layer=layer
        ),
        project_id="iris",
        now_ms=CACHE_NOW,
        closure_digest=content_digest(list(closure_of(fingerprint))),
    )
    base.update(over)
    return ReuseRequest(**base)


def admitted_receipt(
    bound_graph: MaterializationGraph, node_id: str, **over: Any
) -> ReuseReceipt:
    """A receipt the shield grants, so a test can state the exception instead of the happy path."""

    layer = over.get("layer", CacheLayer.INTERMEDIATE)
    outcome = admit_reuse(
        cache_entry(bound_graph, node_id, **over),
        reuse_request(bound_graph, node_id, layer=layer),
        trust=cache_trust(),
    )
    if not isinstance(outcome, ReuseReceipt):
        raise AssertionError(f"expected an admission for {node_id}: {outcome.text}")
    return outcome


__all__ = [
    "CACHE_EVALUATOR",
    "CACHE_NOW",
    "CACHE_PRODUCER",
    "Change",
    "DeltaKind",
    "DependencyFacet",
    "DependencySlice",
    "EdgeKind",
    "FingerprintContext",
    "GraphDefinition",
    "GraphDelta",
    "GraphEdge",
    "GraphMutation",
    "GraphNode",
    "GraphRevision",
    "MaterializationGraph",
    "MaterializationRecord",
    "NodeRole",
    "PortCardinality",
    "PortDirection",
    "RASTER",
    "SemanticPort",
    "SemanticTypeRef",
    "SideEffectClass",
    "SideEffectPolicy",
    "TEXT",
    "VECTOR",
    "admitted_receipt",
    "artifact_identity",
    "bound",
    "cache_context",
    "cache_entry",
    "cache_qualification",
    "cache_trust",
    "chain_definition",
    "chain_records",
    "chain_revision",
    "change",
    "closure",
    "component_version",
    "compute_fingerprint",
    "context",
    "definition",
    "delta",
    "discovery_receipt",
    "delivery",
    "digest",
    "edge",
    "fork_receipt",
    "input_port",
    "materialization",
    "mutation",
    "new_id",
    "node",
    "operation",
    "output",
    "port",
    "ref",
    "reuse_request",
    "revision",
    "revision_ref",
    "semantic_type",
    "snapshot",
    "source",
    "transition_receipt",
    "validation",
]
