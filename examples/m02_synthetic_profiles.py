"""IRIS-WO-0004 synthetic production profiles.

Five different domains, one kernel. Each profile below is assembled only from
:mod:`iris_project_os` primitives: a typed Production Graph, variant axes,
identity anchors, materialization records and a snapshot closure. Nothing here
knows how a pixel, a mesh or a waveform is produced; that is the point. If these
five domains fit the same kernel without the kernel learning any of their
vocabulary, the kernel is general.

Like :mod:`examples.m01_synthetic_profiles`, this module is a fixture, not a
feature. The kernel must stay importable with this directory deleted, and no
production code may import it.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Mapping, Sequence

from iris_project_os.branching import (
    ConstraintKind,
    IdentityAnchorPolicy,
    VariantConstraint,
    VariantOption,
    VariantSelection,
    VariantSet,
)
from iris_project_os.graph import (
    DependencyFacet,
    DependencySlice,
    EdgeKind,
    GraphDefinition,
    GraphEdge,
    GraphNode,
    GraphRevision,
    MaterializationGraph,
    MaterializationRecord,
    NodeRole,
    PortCardinality,
    PortDirection,
    PortExport,
    ReproducibilityClass,
    SemanticPort,
    SemanticTypeRef,
    SideEffectClass,
    SideEffectPolicy,
    SubgraphInterface,
)
from iris_project_os.identity import EntityKind, ExternalRef
from iris_project_os.snapshots import (
    Snapshot,
    SnapshotClass,
    SnapshotClosureManifest,
    commit_snapshot,
)
from iris_project_os.versions import ComponentVersion
from iris_quality.contracts import QualityClass

__all__ = [
    "ANCHOR_FACE",
    "ANCHOR_VOICE",
    "AUDIO_PROFILE",
    "FILM_PROFILE",
    "GAME_ASSET_PROFILE",
    "LOGO_PROFILE",
    "MIGRATION_FACE",
    "MIGRATION_VOICE",
    "PROFILES",
    "ProfileFixture",
    "SPOKESPERSON_PROFILE",
    "digest",
    "external_ref",
    "identity_id",
    "profile_for",
    "semantic_types_of",
]

NOW_MS = 1_700_000_000_000
ACTOR = ComponentVersion("iris.m02.profiles", "1.0.0")
QUALITY_FLOOR = QualityClass.REVIEW

VECTOR = "vector.svg"
RASTER = "raster.png"
MESH = "mesh.tri"
MATERIAL = "material.pbr"
RIG = "rig.skeleton"
CLIP = "animation.clip"
FRAMES = "frames.exr"
PRORES = "video.prores"
VOICE = "voice.audio"
WAVE = "audio.wave"
MUSIC = "music.stem"
SCRIPT = "text.script"
POSE = "avatar.pose"
VERDICT = "verdict.json"


def digest(seed: str) -> str:
    """A content digest for any label, so no fixture has to hardcode a hash."""

    return sha256(seed.encode("utf-8")).hexdigest()


def identity_id(seed: str) -> str:
    """A canonical UUID derived from a label: stable across runs, unique per fixture."""

    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"iris.m02.profile.{seed}"))


def external_ref(
    kind: EntityKind, reference: str, version: str | None = None
) -> ExternalRef:
    return ExternalRef(kind=kind, reference=reference, version=version)


def _type(type_id: str) -> SemanticTypeRef:
    return SemanticTypeRef(
        type_id=type_id,
        schema_ref=external_ref(EntityKind.SCHEMA, f"schema.{type_id.split('.', 1)[0]}", "1.0.0"),
    )


def _port(
    port_id: str,
    direction: PortDirection,
    type_id: str,
    *,
    cardinality: PortCardinality = PortCardinality.ONE,
    required: bool = True,
    minimum_quality_class: QualityClass | None = None,
    accepted_schema_refs: Sequence[ExternalRef] = (),
) -> SemanticPort:
    return SemanticPort(
        port_id=port_id,
        direction=direction,
        semantic_type=_type(type_id),
        cardinality=cardinality,
        required=required,
        minimum_quality_class=minimum_quality_class,
        accepted_schema_refs=tuple(accepted_schema_refs),
    )


def _output(port_id: str, type_id: str, **kwargs: Any) -> SemanticPort:
    return _port(port_id, PortDirection.OUTPUT, type_id, **kwargs)


def _input(port_id: str, type_id: str, **kwargs: Any) -> SemanticPort:
    return _port(port_id, PortDirection.INPUT, type_id, **kwargs)


def _node(
    node_id: str,
    role: NodeRole,
    *,
    inputs: Sequence[SemanticPort] = (),
    outputs: Sequence[SemanticPort] = (),
    reproducibility: ReproducibilityClass | None = None,
    side_effect: SideEffectClass = SideEffectClass.NO_SIDE_EFFECT,
    side_effect_policy: SideEffectPolicy | None = None,
    human_decision_required: bool = False,
    display_name: str = "",
    policy_refs: Sequence[ExternalRef] = (),
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
        human_decision_required=human_decision_required,
        display_name=display_name,
        policy_refs=tuple(policy_refs),
        **kwargs,
    )


def _edge(
    edge_id: str,
    source_node: str,
    target_node: str,
    type_id: str,
    *,
    kind: EdgeKind = EdgeKind.MATERIAL_CAUSAL,
    source_port: str = "out",
    target_port: str = "in",
    facets: Sequence[DependencyFacet] = (DependencyFacet.CONTENT,),
    order: int | None = None,
    slice: DependencySlice | None = None,
) -> GraphEdge:
    return GraphEdge(
        edge_id=edge_id,
        kind=kind,
        source_node_id=source_node,
        source_port_id=source_port,
        target_node_id=target_node,
        target_port_id=target_port,
        facets=tuple(facets),
        order=order,
        slice=slice,
    )


def _option(option_id: str, seed: str, **kwargs: Any) -> VariantOption:
    return VariantOption(option_id=option_id, content_digest=digest(seed), **kwargs)


def _definition(
    graph_id: str,
    nodes: Sequence[GraphNode],
    edges: Sequence[GraphEdge],
    declared: Sequence[ExternalRef],
    **kwargs: Any,
) -> GraphDefinition:
    return GraphDefinition(
        graph_id=graph_id,
        version=kwargs.pop("version", 1),
        nodes=tuple(nodes),
        edges=tuple(edges),
        declared_external_inputs=tuple(declared),
        **kwargs,
    )


@dataclass(frozen=True)
class ProfileFixture:
    """One domain's full claim on the kernel: graph, variants, evidence and closure.

    The fixture exposes the parts a test needs separately so it can ask the kernel
    for a narrower or a wider claim than the profile itself makes.
    """

    profile_id: str
    summary: str
    project_id: str
    production_id: str
    branch_id: str
    definition: GraphDefinition
    variant_sets: tuple[VariantSet, ...] = ()
    variant_constraints: tuple[VariantConstraint, ...] = ()
    selection: VariantSelection | None = None
    claim: SnapshotClass = SnapshotClass.VALIDATED_SNAPSHOT
    release_ready: bool = True
    revised_definition: GraphDefinition | None = None
    actor: ComponentVersion = ACTOR
    created_at_ms: int = NOW_MS
    metadata: Mapping[str, str] = field(default_factory=dict)

    @property
    def graph_id(self) -> str:
        return self.definition.graph_id

    @property
    def identity_anchors(self) -> tuple[IdentityAnchorPolicy, ...]:
        return tuple(
            sorted(
                (item.identity_anchor for item in self.variant_sets if item.identity_anchor is not None),
                key=lambda item: item.anchor_id,
            )
        )

    @property
    def semantic_types(self) -> tuple[str, ...]:
        return semantic_types_of(self.definition)

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(node.node_id for node in self.definition.nodes)

    def selection_pairs(self, selection: VariantSelection | None = None) -> tuple[tuple[str, str], ...]:
        chosen = self.selection if selection is None else selection
        return () if chosen is None else chosen.pairs

    def revision(self, definition: GraphDefinition | None = None) -> GraphRevision:
        wanted = definition or self.definition
        return GraphRevision(
            revision_id=identity_id(f"revision.{wanted.graph_id}.{wanted.version}"),
            definition=wanted,
        )

    def records(
        self,
        definition: GraphDefinition | None = None,
        selection: VariantSelection | None = None,
    ) -> tuple[MaterializationRecord, ...]:
        """One judged record per declared output, which is what a validated closure owes."""

        wanted = definition or self.definition
        collected: list[MaterializationRecord] = []
        for node in wanted.nodes:
            if not node.role.emits_material:
                continue
            for port in node.outputs:
                key = f"{self.profile_id}.{node.node_id}.{port.port_id}"
                collected.append(
                    MaterializationRecord(
                        node_id=node.node_id,
                        port_id=port.port_id,
                        revision_ref=external_ref(EntityKind.REVISION, f"rev.{key}", "1"),
                        content_digest=digest(key),
                        producer_attempt_id=identity_id(f"attempt.{key}"),
                        quality_class=QUALITY_FLOOR,
                        decision_ref=external_ref(EntityKind.QUALITY_DECISION, identity_id(f"decision.{key}")),
                        seed=digest(f"seed.{key}") if node.reproducibility.requires_recorded_seed else None,
                        tool_refs=(external_ref(EntityKind.TOOL, f"tool.{key}", "1"),),
                        produced_at_ms=self.created_at_ms,
                    )
                )
        return tuple(collected)

    def bound(
        self,
        *,
        definition: GraphDefinition | None = None,
        selection: VariantSelection | None = None,
        records: Sequence[MaterializationRecord] | None = None,
        environment: bool = True,
    ) -> MaterializationGraph:
        return MaterializationGraph(
            revision=self.revision(definition),
            materializations=tuple(
                self.records(definition, selection) if records is None else records
            ),
            variant_selection=self.selection_pairs(selection),
            environment_fingerprint=digest(f"env.{self.production_id}") if environment else None,
        )

    def closure(
        self,
        *,
        definition: GraphDefinition | None = None,
        selection: VariantSelection | None = None,
        graph: MaterializationGraph | None = None,
        release_ready: bool | None = None,
        **over: Any,
    ) -> SnapshotClosureManifest:
        """The closure this profile is entitled to, with the refs its claim demands."""

        settled = self.release_ready if release_ready is None else release_ready
        bound_graph = graph or self.bound(definition=definition, selection=selection)
        chosen = bound_graph.variant_selection
        payload: dict[str, Any] = dict(
            project_id=self.project_id,
            production_id=self.production_id,
            branch_id=self.branch_id,
            graph=bound_graph,
            intent_ref=external_ref(EntityKind.INTENT, f"intent.{self.profile_id}"),
            variant_sets=self.variant_sets,
            variant_constraints=self.variant_constraints,
            variant_selection=None if chosen == () and self.selection is None else (
                self.selection if selection is None else selection
            ),
            identity_anchors=self.identity_anchors,
            quality_decisions=tuple(
                record.decision_ref for record in bound_graph.materializations if record.decision_ref is not None
            ),
            policy_refs=(external_ref(EntityKind.FIDELITY_CONTRACT, f"contract.{self.profile_id}", "1.0.0"),),
            tool_refs=(external_ref(EntityKind.TOOL, f"tool.{self.production_id}", "1"),),
            model_refs=(external_ref(EntityKind.MODEL, f"model.{self.production_id}", "1"),),
            external_admissions=tuple(
                external_ref(item.kind, item.reference)
                for item in (definition or self.definition).declared_external_inputs
            ),
            environment_fingerprint=bound_graph.environment_fingerprint,
        )
        if settled:
            payload.update(
                rights_refs=(external_ref(EntityKind.RIGHTS, f"rights.{self.production_id}", "1"),),
                provenance_refs=(external_ref(EntityKind.PROVENANCE, f"provenance.{self.production_id}", "1"),),
                delivery_refs=(external_ref(EntityKind.DESTINATION, f"destination.{self.production_id}", "1"),),
                environment_refs=(external_ref(EntityKind.ENVIRONMENT, f"environment.{self.production_id}", "1"),),
            )
        payload.update(over)
        return SnapshotClosureManifest(**payload)

    def commit(
        self,
        snapshot_class: SnapshotClass | None = None,
        **over: Any,
    ) -> Snapshot:
        """Freeze this profile at the class it claims, or at one the test asks for."""

        wanted = self.claim if snapshot_class is None else snapshot_class
        closure_over = {key: value for key, value in over.items() if key not in {"snapshot_id", "derivation", "label"}}
        return commit_snapshot(
            self.closure(**closure_over),
            snapshot_class=wanted,
            snapshot_id=identity_id(f"snapshot.{self.profile_id}.{wanted.value}"),
            actor=self.actor,
            created_at_ms=self.created_at_ms,
            label=f"{self.profile_id}.{wanted.value.lower()}",
        )


def semantic_types_of(definition: GraphDefinition) -> tuple[str, ...]:
    """Every semantic type a definition's ports speak, sorted and de-duplicated."""

    found = {
        port.semantic_type.type_id
        for node in definition.nodes
        for port in (*node.inputs, *node.outputs)
    }
    return tuple(sorted(found))


def _selection(profile: str, pairs: Mapping[str, str], migrations: Sequence[str] = ()) -> VariantSelection:
    return VariantSelection(
        selection_id=identity_id(f"selection.{profile}"),
        pairs=tuple(sorted(pairs.items())),
        migration_receipt_ids=tuple(sorted(migrations)),
        actor=ACTOR,
        created_at_ms=NOW_MS,
    )


# --- profile 1: logo, web and vector ------------------------------------------

LOGO_PROFILE = ProfileFixture(
    profile_id="profile.logo-web",
    summary="A brand mark treated once and delivered at several web sizes.",
    project_id=identity_id("project.logo"),
    production_id=identity_id("production.logo"),
    branch_id=identity_id("branch.logo.main"),
    definition=_definition(
        "graph.logo-web",
        (
            _node(
                "source.brandmark",
                NodeRole.SOURCE,
                outputs=(_output("out", VECTOR),),
                reproducibility=ReproducibilityClass.EXTERNAL_STATE,
                display_name="Brand mark",
            ),
            _node(
                "treat.depth",
                NodeRole.SUBGRAPH,
                inputs=(_input("in", VECTOR),),
                outputs=(_output("out", VECTOR),),
                reproducibility=ReproducibilityClass.DETERMINISTIC,
                display_name="Depth treatment",
            ),
            _node(
                "render.social",
                NodeRole.OPERATION,
                inputs=(_input("in", VECTOR),),
                outputs=(_output("out", RASTER),),
                reproducibility=ReproducibilityClass.ENVIRONMENT_SENSITIVE,
                display_name="Social raster",
            ),
            _node(
                "deliver.web",
                NodeRole.DELIVERY,
                inputs=(_input("in", RASTER, minimum_quality_class=QUALITY_FLOOR),),
                outputs=(_output("out", RASTER),),
                reproducibility=ReproducibilityClass.DETERMINISTIC,
                side_effect=SideEffectClass.CONTROLLED_OUTPUTS,
                display_name="Web delivery",
            ),
            _node(
                "validate.legibility",
                NodeRole.VALIDATION,
                inputs=(_input("in", RASTER), _input("reference", VECTOR, required=False)),
                outputs=(_output("out", VERDICT),),
                human_decision_required=True,
                display_name="Legibility review",
            ),
        ),
        (
            _edge("edge.treat", "source.brandmark", "treat.depth", VECTOR, facets=(DependencyFacet.CONTENT, DependencyFacet.SEMANTICS)),
            _edge("edge.render", "treat.depth", "render.social", VECTOR),
            _edge("edge.deliver", "render.social", "deliver.web", RASTER, facets=(DependencyFacet.CONTENT, DependencyFacet.DELIVERY)),
            _edge("edge.validate", "deliver.web", "validate.legibility", RASTER, kind=EdgeKind.EVIDENCE_CAUSAL),
            _edge("edge.reference", "source.brandmark", "validate.legibility", VECTOR, kind=EdgeKind.OBSERVATION, target_port="reference"),
        ),
        (
            external_ref(EntityKind.ARTIFACT, "asset.brandmark"),
            external_ref(EntityKind.ARTIFACT, "asset.typeface"),
        ),
        interfaces=(
            SubgraphInterface(
                node_id="treat.depth",
                inner_graph_ref=external_ref(EntityKind.GRAPH, "graph.logo-depth", "1"),
                exports=(
                    PortExport("in", "extrude.bevel", "base", PortDirection.INPUT),
                    PortExport("out", "extrude.bevel", "result", PortDirection.OUTPUT),
                ),
            ),
        ),
    ),
    variant_sets=(
        VariantSet(
            variant_set_id="axis.palette",
            purpose="Day and night brand palettes over one mark.",
            options=(_option("day", "logo.palette.day"), _option("night", "logo.palette.night")),
            default_option_id="day",
            affected_ports=("out",),
        ),
        VariantSet(
            variant_set_id="axis.ratio",
            purpose="Crop ratios for the platforms this mark ships to.",
            options=(_option("square", "logo.ratio.square"), _option("wide", "logo.ratio.wide")),
            default_option_id="square",
            affected_facets=(DependencyFacet.CONTENT, DependencyFacet.SEMANTICS),
            affected_ports=("in", "out"),
        ),
    ),
    variant_constraints=(
        VariantConstraint(
            constraint_id="constraint.night-square",
            kind=ConstraintKind.PROHIBITS,
            when_set="axis.palette",
            when_option="night",
            target_set="axis.ratio",
            target_options=("square",),
            reason_code="night-mark-needs-room",
        ),
    ),
    selection=_selection("logo-web", {"axis.palette": "night", "axis.ratio": "wide"}),
    claim=SnapshotClass.VALIDATED_SNAPSHOT,
    release_ready=False,
)


# --- profile 2: stylized isometric game asset ---------------------------------

GAME_ASSET_PROFILE = ProfileFixture(
    profile_id="profile.game-asset",
    summary="A stylized isometric asset built, textured, rigged and exported to an engine.",
    project_id=identity_id("project.game"),
    production_id=identity_id("production.game-asset"),
    branch_id=identity_id("branch.game.main"),
    definition=_definition(
        "graph.game-asset",
        (
            _node(
                "source.sketch",
                NodeRole.SOURCE,
                outputs=(_output("out", VECTOR),),
                reproducibility=ReproducibilityClass.EXTERNAL_STATE,
                display_name="Concept sketch",
            ),
            _node(
                "build.blockout",
                NodeRole.OPERATION,
                inputs=(_input("in", VECTOR),),
                outputs=(_output("out", MESH),),
                reproducibility=ReproducibilityClass.DETERMINISTIC,
                display_name="Blockout mesh",
            ),
            _node(
                "texture.surface",
                NodeRole.OPERATION,
                inputs=(_input("in", MESH),),
                outputs=(_output("out", MATERIAL),),
                reproducibility=ReproducibilityClass.STOCHASTIC,
                display_name="Surface bake",
            ),
            _node(
                "rig.character",
                NodeRole.OPERATION,
                inputs=(_input("mesh", MESH), _input("surface", MATERIAL, required=False)),
                outputs=(_output("out", RIG),),
                reproducibility=ReproducibilityClass.DETERMINISTIC,
                display_name="Skeleton rig",
            ),
            _node(
                "animate.idle",
                NodeRole.OPERATION,
                inputs=(_input("in", RIG),),
                outputs=(_output("out", CLIP),),
                reproducibility=ReproducibilityClass.SEEDED,
                display_name="Idle animation",
            ),
            _node(
                "deliver.engine",
                NodeRole.DELIVERY,
                inputs=(_input("in", CLIP, minimum_quality_class=QualityClass.PREVIEW),),
                outputs=(_output("out", CLIP),),
                reproducibility=ReproducibilityClass.DETERMINISTIC,
                side_effect=SideEffectClass.CONTROLLED_OUTPUTS,
                display_name="Engine export",
            ),
            _node(
                "validate.silhouette",
                NodeRole.VALIDATION,
                inputs=(_input("in", CLIP),),
                outputs=(_output("out", VERDICT),),
                display_name="Play-distance silhouette",
            ),
        ),
        (
            _edge("edge.blockout", "source.sketch", "build.blockout", VECTOR),
            _edge("edge.texture", "build.blockout", "texture.surface", MESH),
            _edge("edge.rig-mesh", "build.blockout", "rig.character", MESH, target_port="mesh"),
            _edge("edge.rig-surface", "texture.surface", "rig.character", MATERIAL, target_port="surface", facets=(DependencyFacet.CONTENT, DependencyFacet.PROVENANCE)),
            _edge("edge.animate", "rig.character", "animate.idle", RIG),
            _edge("edge.export", "animate.idle", "deliver.engine", CLIP, facets=(DependencyFacet.CONTENT, DependencyFacet.DELIVERY)),
            _edge("edge.validate", "deliver.engine", "validate.silhouette", CLIP, kind=EdgeKind.EVIDENCE_CAUSAL),
        ),
        (external_ref(EntityKind.ARTIFACT, "asset.concept"),),
    ),
    variant_sets=(
        VariantSet(
            variant_set_id="axis.lod",
            purpose="Level of detail the runtime can afford for this prop.",
            options=(
                _option("hero", "game.lod.hero"),
                _option("mid", "game.lod.mid"),
                _option("low", "game.lod.low"),
            ),
            default_option_id="mid",
            affected_facets=(DependencyFacet.CONTENT, DependencyFacet.SEMANTICS),
            affected_ports=("out",),
        ),
        VariantSet(
            variant_set_id="axis.export",
            purpose="Which engine's asset interchange this build targets.",
            options=(_option("native", "game.export.native"), _option("generic", "game.export.generic")),
            default_option_id="native",
        ),
    ),
    variant_constraints=(
        VariantConstraint(
            constraint_id="constraint.generic-export",
            kind=ConstraintKind.REQUIRES,
            when_set="axis.export",
            when_option="generic",
            target_set="axis.lod",
            target_options=("mid", "low"),
            reason_code="hero-mesh-overflows-the-generic-pipeline",
        ),
    ),
    selection=_selection("game-asset", {"axis.lod": "mid", "axis.export": "generic"}),
    claim=SnapshotClass.VALIDATED_SNAPSHOT,
    release_ready=True,
)


# --- profile 3: film / video sequence -----------------------------------------

_FILM_GRADE_POLICY = external_ref(EntityKind.POLICY, "policy.film-look", "3")


def _film_definition(version: int = 1, *, grade_policy: ExternalRef | None = None) -> GraphDefinition:
    return _definition(
        "graph.film-sequence",
        (
            _node(
                "source.plate-a",
                NodeRole.SOURCE,
                outputs=(_output("out", FRAMES),),
                reproducibility=ReproducibilityClass.EXTERNAL_STATE,
                display_name="Camera plate A",
            ),
            _node(
                "source.plate-b",
                NodeRole.SOURCE,
                outputs=(_output("out", FRAMES),),
                reproducibility=ReproducibilityClass.EXTERNAL_STATE,
                display_name="Camera plate B",
            ),
            _node(
                "comp.plates",
                NodeRole.COMPOSITION,
                inputs=(_input("shots", FRAMES, cardinality=PortCardinality.MANY_ORDERED),),
                outputs=(_output("out", FRAMES),),
                reproducibility=ReproducibilityClass.DETERMINISTIC,
                display_name="Plate comp",
            ),
            _node(
                "grade.sequence",
                NodeRole.OPERATION,
                inputs=(_input("in", FRAMES),),
                outputs=(_output("out", PRORES),),
                reproducibility=ReproducibilityClass.ENVIRONMENT_SENSITIVE,
                display_name="Sequence grade",
                policy_refs=(grade_policy or _FILM_GRADE_POLICY,),
            ),
            _node(
                "validate.look",
                NodeRole.VALIDATION,
                inputs=(_input("in", PRORES),),
                outputs=(_output("out", VERDICT),),
                human_decision_required=True,
                display_name="Creative review",
            ),
            _node(
                "deliver.master",
                NodeRole.DELIVERY,
                inputs=(
                    _input("in", PRORES, minimum_quality_class=QUALITY_FLOOR),
                    _input("clearance", VERDICT, required=False),
                ),
                outputs=(_output("out", PRORES),),
                reproducibility=ReproducibilityClass.DETERMINISTIC,
                side_effect=SideEffectClass.CONTROLLED_OUTPUTS,
                display_name="Master delivery",
            ),
            _node(
                "publish.cdn",
                NodeRole.DELIVERY,
                inputs=(_input("in", PRORES),),
                outputs=(_output("out", PRORES),),
                reproducibility=ReproducibilityClass.EXTERNAL_STATE,
                side_effect=SideEffectClass.EXTERNAL_MUTATION,
                side_effect_policy=SideEffectPolicy(
                    idempotency_key_ref=external_ref(EntityKind.POLICY, "key.film-publish", "1"),
                    compensation_ref=external_ref(EntityKind.POLICY, "policy.film-withdraw", "1"),
                ),
                display_name="CDN publish",
            ),
        ),
        (
            _edge("edge.plate-a", "source.plate-a", "comp.plates", FRAMES, target_port="shots", order=1),
            _edge("edge.plate-b", "source.plate-b", "comp.plates", FRAMES, target_port="shots", order=2),
            _edge(
                "edge.grade",
                "comp.plates",
                "grade.sequence",
                FRAMES,
                facets=(DependencyFacet.CONTENT, DependencyFacet.POLICY),
                slice=DependencySlice(axis="shot", values=("shot-0410", "shot-0411")),
            ),
            _edge("edge.review", "grade.sequence", "validate.look", PRORES, kind=EdgeKind.EVIDENCE_CAUSAL),
            _edge("edge.deliver", "grade.sequence", "deliver.master", PRORES, facets=(DependencyFacet.CONTENT, DependencyFacet.DELIVERY)),
            _edge("edge.publish", "deliver.master", "publish.cdn", PRORES, kind=EdgeKind.ACTIVATION, target_port="in"),
            _edge("edge.clearance", "validate.look", "deliver.master", VERDICT, kind=EdgeKind.ORDER_ONLY, target_port="clearance"),
        ),
        (
            external_ref(EntityKind.ARTIFACT, "asset.plate-a"),
            external_ref(EntityKind.ARTIFACT, "asset.plate-b"),
        ),
        version=version,
    )


FILM_PROFILE = ProfileFixture(
    profile_id="profile.film-sequence",
    summary="Two plates composited, graded, reviewed and published as an accepted master.",
    project_id=identity_id("project.film"),
    production_id=identity_id("production.film-sequence"),
    branch_id=identity_id("branch.film.main"),
    definition=_film_definition(),
    revised_definition=_film_definition(2, grade_policy=external_ref(EntityKind.POLICY, "policy.film-look", "4")),
    variant_sets=(
        VariantSet(
            variant_set_id="axis.master",
            purpose="Which finishing frame rate this master is cut at.",
            options=(_option("24", "film.master.24"), _option("25", "film.master.25")),
            default_option_id="24",
            affected_facets=(DependencyFacet.CONTENT,),
            affected_ports=("in", "out"),
            requires_revalidation=True,
        ),
        VariantSet(
            variant_set_id="axis.subtitles",
            purpose="Caption burn-in for the territories this cut ships to.",
            options=(_option("none", "film.subtitles.none"), _option("burned", "film.subtitles.burned")),
            default_option_id="none",
            affected_facets=(DependencyFacet.CONTENT, DependencyFacet.SEMANTICS),
        ),
    ),
    variant_constraints=(
        VariantConstraint(
            constraint_id="constraint.25-no-burn",
            kind=ConstraintKind.PROHIBITS,
            when_set="axis.master",
            when_option="25",
            target_set="axis.subtitles",
            target_options=("burned",),
            reason_code="burned-in-captions-are-timed-to-24",
        ),
    ),
    selection=_selection("film-sequence", {"axis.master": "24", "axis.subtitles": "burned"}),
    claim=SnapshotClass.RELEASE_SNAPSHOT,
    release_ready=True,
)


# --- profile 4: virtual spokesperson -----------------------------------------

ANCHOR_FACE = "anchor.persona-face"
ANCHOR_VOICE = "anchor.persona-voice"
MIGRATION_FACE = identity_id("migration.persona-face")
MIGRATION_VOICE = identity_id("migration.persona-voice")
_FACE_BASELINE = digest("persona.face.keynote")
_VOICE_BASELINE = digest("persona.voice.keynote")

SPOKESPERSON_PROFILE = ProfileFixture(
    profile_id="profile.spokesperson",
    summary="A persistent on-camera persona whose face and voice are identity anchors.",
    project_id=identity_id("project.avatar"),
    production_id=identity_id("production.spokesperson"),
    branch_id=identity_id("branch.avatar.episode-12"),
    definition=_definition(
        "graph.spokesperson",
        (
            _node(
                "source.lines",
                NodeRole.SOURCE,
                outputs=(_output("out", SCRIPT),),
                reproducibility=ReproducibilityClass.EXTERNAL_STATE,
                display_name="Approved script",
            ),
            _node(
                "voice.line",
                NodeRole.OPERATION,
                inputs=(_input("in", SCRIPT),),
                outputs=(_output("out", VOICE),),
                reproducibility=ReproducibilityClass.STOCHASTIC,
                display_name="Voice line",
            ),
            _node(
                "drive.avatar",
                NodeRole.OPERATION,
                inputs=(
                    _input("in", VOICE, accepted_schema_refs=(external_ref(EntityKind.SCHEMA, "schema.voice", "1.0.0"),)),
                    _input("gesture", POSE, required=False),
                ),
                outputs=(_output("out", POSE),),
                reproducibility=ReproducibilityClass.DETERMINISTIC,
                display_name="Performance drive",
            ),
            _node(
                "render.spokesperson",
                NodeRole.OPERATION,
                inputs=(_input("in", POSE),),
                outputs=(_output("out", PRORES),),
                reproducibility=ReproducibilityClass.ENVIRONMENT_SENSITIVE,
                display_name="Persona render",
            ),
            _node(
                "validate.persona",
                NodeRole.VALIDATION,
                inputs=(_input("in", PRORES),),
                outputs=(_output("out", VERDICT),),
                human_decision_required=True,
                display_name="Persona and rights review",
            ),
            _node(
                "deliver.public",
                NodeRole.DELIVERY,
                inputs=(_input("in", PRORES, minimum_quality_class=QUALITY_FLOOR),),
                outputs=(_output("out", PRORES),),
                reproducibility=ReproducibilityClass.DETERMINISTIC,
                side_effect=SideEffectClass.EXTERNAL_MUTATION,
                side_effect_policy=SideEffectPolicy(
                    idempotency_key_ref=external_ref(EntityKind.POLICY, "key.spokesperson-publish", "1"),
                    compensation_ref=external_ref(EntityKind.POLICY, "policy.spokesperson-withdraw", "1"),
                ),
                display_name="Public release",
            ),
        ),
        (
            _edge("edge.voice", "source.lines", "voice.line", SCRIPT),
            _edge("edge.drive", "voice.line", "drive.avatar", VOICE),
            _edge("edge.render", "drive.avatar", "render.spokesperson", POSE),
            _edge("edge.validate", "render.spokesperson", "validate.persona", PRORES, kind=EdgeKind.EVIDENCE_CAUSAL),
            _edge("edge.deliver", "render.spokesperson", "deliver.public", PRORES, facets=(DependencyFacet.CONTENT, DependencyFacet.DELIVERY, DependencyFacet.RIGHTS)),
        ),
        (
            external_ref(EntityKind.ARTIFACT, "asset.script"),
            external_ref(EntityKind.ARTIFACT, "asset.persona-model"),
        ),
    ),
    variant_sets=(
        VariantSet(
            variant_set_id="axis.persona-face",
            purpose="The protected face this spokesperson is recognised by.",
            options=(
                _option("keynote", "persona.face.keynote", anchor_digest=_FACE_BASELINE),
                _option(
                    "restyled",
                    "persona.face.restyled",
                    anchor_digest=digest("persona.face.restyled"),
                    migration_receipt_id=MIGRATION_FACE,
                ),
            ),
            default_option_id="keynote",
            identity_anchor=IdentityAnchorPolicy(
                anchor_id=ANCHOR_FACE,
                policy_ref=external_ref(EntityKind.POLICY, "policy.persona-face", "2"),
                baseline_digest=_FACE_BASELINE,
                baseline_option_id="keynote",
                description="A restyle is only admissible through the recorded identity migration.",
            ),
            affected_facets=(DependencyFacet.SEMANTICS, DependencyFacet.CONTENT),
            affected_ports=("in", "out"),
            requires_revalidation=True,
        ),
        VariantSet(
            variant_set_id="axis.persona-voice",
            purpose="The protected voice identity licensed to this persona.",
            options=(
                _option("keynote", "persona.voice.keynote", anchor_digest=_VOICE_BASELINE),
                _option(
                    "alt",
                    "persona.voice.alt",
                    anchor_digest=digest("persona.voice.alt"),
                    migration_receipt_id=MIGRATION_VOICE,
                ),
            ),
            default_option_id="keynote",
            identity_anchor=IdentityAnchorPolicy(
                anchor_id=ANCHOR_VOICE,
                policy_ref=external_ref(EntityKind.POLICY, "policy.persona-voice", "2"),
                baseline_digest=_VOICE_BASELINE,
                baseline_option_id="keynote",
            ),
            requires_revalidation=True,
        ),
        VariantSet(
            variant_set_id="axis.outfit",
            purpose="Wardrobe for the episode.",
            options=(_option("studio", "outfit.studio"), _option("field", "outfit.field")),
            default_option_id="studio",
        ),
        VariantSet(
            variant_set_id="axis.language",
            purpose="Delivery language of the approved script.",
            options=(_option("pt-br", "language.pt-br"), _option("en-us", "language.en-us")),
            default_option_id="pt-br",
        ),
        VariantSet(
            variant_set_id="axis.campaign",
            purpose="Which campaign this episode belongs to.",
            options=(_option("launch", "campaign.launch"), _option("retail", "campaign.retail")),
            default_option_id="launch",
        ),
    ),
    variant_constraints=(
        VariantConstraint(
            constraint_id="constraint.field-studio-only",
            kind=ConstraintKind.PROHIBITS,
            when_set="axis.language",
            when_option="en-us",
            target_set="axis.outfit",
            target_options=("field",),
            reason_code="field-shoots-only-for-the-launch-market",
        ),
    ),
    selection=_selection(
        "spokesperson",
        {
            "axis.persona-face": "keynote",
            "axis.persona-voice": "keynote",
            "axis.outfit": "studio",
            "axis.language": "pt-br",
            "axis.campaign": "launch",
        }
    ),
    claim=SnapshotClass.RELEASE_SNAPSHOT,
    release_ready=True,
)


# --- profile 5: non-visual voice and music ------------------------------------

AUDIO_PROFILE = ProfileFixture(
    profile_id="profile.voice-music",
    summary="A narration bed and a music stem, mixed and published without a single frame.",
    project_id=identity_id("project.audio"),
    production_id=identity_id("production.voice-music"),
    branch_id=identity_id("branch.audio.main"),
    definition=_definition(
        "graph.voice-music",
        (
            _node(
                "source.brief",
                NodeRole.SOURCE,
                outputs=(_output("out", SCRIPT),),
                reproducibility=ReproducibilityClass.EXTERNAL_STATE,
                display_name="Narration brief",
            ),
            _node(
                "voice.read",
                NodeRole.OPERATION,
                inputs=(_input("in", SCRIPT),),
                outputs=(_output("out", VOICE),),
                reproducibility=ReproducibilityClass.STOCHASTIC,
                display_name="Reference read",
            ),
            _node(
                "source.library",
                NodeRole.SOURCE,
                outputs=(_output("out", MUSIC),),
                reproducibility=ReproducibilityClass.EXTERNAL_STATE,
                display_name="Licensed music",
            ),
            _node(
                "mix.final",
                NodeRole.COMPOSITION,
                inputs=(_input("voice", VOICE), _input("music", MUSIC)),
                outputs=(_output("out", WAVE),),
                reproducibility=ReproducibilityClass.DETERMINISTIC,
                display_name="Final mix",
            ),
            _node(
                "validate.listen",
                NodeRole.VALIDATION,
                inputs=(_input("in", WAVE),),
                outputs=(_output("out", VERDICT),),
                display_name="Loudness and sync review",
            ),
            _node(
                "deliver.feed",
                NodeRole.DELIVERY,
                inputs=(_input("in", WAVE, minimum_quality_class=QualityClass.PREVIEW),),
                outputs=(_output("out", WAVE),),
                reproducibility=ReproducibilityClass.DETERMINISTIC,
                side_effect=SideEffectClass.CONTROLLED_OUTPUTS,
                display_name="Feed delivery",
            ),
        ),
        (
            _edge("edge.read", "source.brief", "voice.read", SCRIPT),
            _edge("edge.mix-voice", "voice.read", "mix.final", VOICE, target_port="voice"),
            _edge("edge.mix-music", "source.library", "mix.final", MUSIC, target_port="music", facets=(DependencyFacet.CONTENT, DependencyFacet.RIGHTS)),
            _edge("edge.validate", "mix.final", "validate.listen", WAVE, kind=EdgeKind.EVIDENCE_CAUSAL),
            _edge("edge.deliver", "mix.final", "deliver.feed", WAVE, facets=(DependencyFacet.CONTENT, DependencyFacet.DELIVERY)),
        ),
        (
            external_ref(EntityKind.ARTIFACT, "asset.brief"),
            external_ref(EntityKind.ARTIFACT, "asset.music-bed"),
        ),
    ),
    variant_sets=(
        VariantSet(
            variant_set_id="axis.loudness",
            purpose="Loudness target for the platform this bed ships to.",
            options=(_option("broadcast", "loudness.broadcast"), _option("streaming", "loudness.streaming")),
            default_option_id="streaming",
            affected_facets=(DependencyFacet.CONTENT, DependencyFacet.QUALITY),
            affected_ports=("in", "out"),
        ),
    ),
    selection=_selection("voice-music", {"axis.loudness": "broadcast"}),
    claim=SnapshotClass.VALIDATED_SNAPSHOT,
    release_ready=True,
)

PROFILES: Mapping[str, ProfileFixture] = {
    profile.profile_id: profile
    for profile in (
        LOGO_PROFILE,
        GAME_ASSET_PROFILE,
        FILM_PROFILE,
        SPOKESPERSON_PROFILE,
        AUDIO_PROFILE,
    )
}


def profile_for(name: str) -> ProfileFixture:
    """Look a profile up by short name or by its full id."""

    wanted = name if name.startswith("profile.") else f"profile.{name}"
    try:
        return PROFILES[wanted]
    except KeyError as error:
        known = sorted(item.split(".", 1)[1] for item in PROFILES)
        raise KeyError(f"unknown synthetic profile {name!r}; choose from {known}") from error
