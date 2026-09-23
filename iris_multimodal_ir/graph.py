"""Immutable scene nodes, dual graph topology, fragments, and composition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Mapping

from iris_intent.identity import SemanticRef

from .base import IRRecord, many, one, optional
from .common import deep_freeze, identifiers, non_negative_int, require_enum
from .enums import CompositionPrecedence, CyclePolicy, NodeKind
from .errors import IRAdmissionError, IRIntegrityError, IRLimitError, IRSchemaError
from .identity import IRNodeRef, IRRevisionRef, ResourceRef
from .character import AttachmentPortIR, CharacterIdentityIR, MorphChannelIR, SkeletonIR, SkinBindingIR
from .materials import ColorConversionReceipt, ColorValueIR, MaterialBindingIR, MaterialIR
from .media import AudioClipBindingIR, AudioIR, MusicIR, NarrativeProjectionIR, SyncRelationIR, TimelineIR
from .limits import DEFAULT_LIMITS, IRLimits
from .provenance import Traceability
from .resources import IRInterfaceCapsule, TextureResourceIR
from .schema import SchemaManifest
from .schema import ExtensionValue
from .spatial import CameraIR, CoordinateFrameIR, LightIR, SpatialConversionReceipt, SpatialReferenceIR, SpatialRegionIR, TransformChainIR
from .temporal import MotionIR, MotionLayerIR, TemporalConversionReceipt, TemporalMarkerIR, TemporalReferenceIR, TemporalRelationIR, TemporalSamplingIR
from .versions import CORE_SCHEMA_VERSION, CONTRACT_VERSION, content_digest, require_identifier, require_version

__all__ = [
    "IRNode", "SceneIR", "EntityIR", "AssetIR", "CharacterIR", "GeometryIR", "CollectionIR",
    "ContainmentEdge", "SemanticRelationship", "RelationshipPolicy", "IRFragment", "CompositionArc",
    "CompositionResult", "compose_fragments", "PrototypeIR", "InstanceIR", "IRRevision",
    "MultimodalIRDocument", "IRDocumentEnvelope", "validate_graph", "find_transform_path", "decode_ir_node",
]


@dataclass(frozen=True)
class IRNode(IRRecord):
    ref: IRNodeRef
    kind: NodeKind
    trace: Traceability
    display_name: str | None = None
    path_hint: str | None = None
    quality_obligation_refs: tuple[SemanticRef, ...] = ()
    semantic_refs: tuple[SemanticRef, ...] = ()
    resource_refs: tuple[ResourceRef, ...] = ()
    interface: IRInterfaceCapsule | None = None
    attributes: Mapping[str, Any] | None = None
    facets: tuple[str, ...] = ()
    admission_required: bool = True

    NESTED: ClassVar = {
        "ref": one(IRNodeRef), "trace": one(Traceability), "quality_obligation_refs": many(SemanticRef),
        "semantic_refs": many(SemanticRef), "resource_refs": many(ResourceRef), "interface": optional(IRInterfaceCapsule),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref", IRNodeRef.coerce(self.ref, "ref"))
        object.__setattr__(self, "kind", require_enum(self.kind, NodeKind, "kind"))
        object.__setattr__(self, "trace", Traceability.coerce(self.trace, "trace"))
        if self.admission_required:
            self.trace.require_admitted(f"node {self.ref.node_id}")
        if self.display_name is not None:
            from .versions import require_text
            object.__setattr__(self, "display_name", require_text(self.display_name, "display_name", maximum=512))
        if self.path_hint is not None:
            from .versions import require_text
            object.__setattr__(self, "path_hint", require_text(self.path_hint, "path_hint", maximum=2048))
        for name in ("quality_obligation_refs", "semantic_refs"):
            refs = tuple(SemanticRef.coerce(item, f"{name}[]") for item in getattr(self, name))
            object.__setattr__(self, name, tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))
        resources = tuple(ResourceRef.coerce(item, "resource_refs[]") for item in self.resource_refs)
        if len({item.identity_key for item in resources}) != len(resources):
            raise IRSchemaError("resource refs contain duplicate canonical identities")
        object.__setattr__(self, "resource_refs", tuple(sorted(resources, key=lambda item: (item.resource_kind, item.resource_id, item.content_digest or ""))))
        if self.interface is not None:
            object.__setattr__(self, "interface", IRInterfaceCapsule.coerce(self.interface, "interface"))
        if self.attributes is not None:
            object.__setattr__(self, "attributes", deep_freeze(self.attributes, "attributes"))
        object.__setattr__(self, "facets", identifiers(self.facets, "facets"))
        if not isinstance(self.admission_required, bool):
            raise IRSchemaError("admission_required must be bool")

    @property
    def identity_key(self) -> tuple[str, str]:
        return self.ref.document_id, self.ref.node_id


@dataclass(frozen=True)
class SceneIR(IRNode):
    root_node_refs: tuple[IRNodeRef, ...] = ()
    NESTED: ClassVar = {**IRNode.NESTED, "root_node_refs": many(IRNodeRef)}

    def __post_init__(self) -> None:
        super(SceneIR, self).__post_init__()
        if self.kind is not NodeKind.SCENE:
            raise IRSchemaError("SceneIR requires kind=SCENE")
        refs = tuple(IRNodeRef.coerce(item, "root_node_refs[]") for item in self.root_node_refs)
        if len(set(refs)) != len(refs):
            raise IRSchemaError("scene root node refs must be unique")
        object.__setattr__(self, "root_node_refs", tuple(sorted(refs)))


@dataclass(frozen=True)
class EntityIR(IRNode):
    transform_chain_id: str | None = None
    NESTED: ClassVar = {**IRNode.NESTED, "transform_chain_id": lambda value, path: None if value is None else require_identifier(value, path)}

    def __post_init__(self) -> None:
        super(EntityIR, self).__post_init__()
        if self.kind is not NodeKind.ENTITY:
            raise IRSchemaError("EntityIR requires kind=ENTITY")


@dataclass(frozen=True)
class AssetIR(IRNode):
    geometry_refs: tuple[IRNodeRef, ...] = ()
    collection_ref: IRNodeRef | None = None
    interface_version: str = "asset-interface-v1"
    NESTED: ClassVar = {**IRNode.NESTED, "geometry_refs": many(IRNodeRef), "collection_ref": optional(IRNodeRef)}

    def __post_init__(self) -> None:
        super(AssetIR, self).__post_init__()
        if self.kind is not NodeKind.ASSET:
            raise IRSchemaError("AssetIR requires kind=ASSET")
        refs = tuple(IRNodeRef.coerce(item, "geometry_refs[]") for item in self.geometry_refs)
        if len(set(refs)) != len(refs):
            raise IRSchemaError("asset geometry refs must be unique")
        object.__setattr__(self, "geometry_refs", tuple(sorted(refs)))
        if self.collection_ref is not None:
            object.__setattr__(self, "collection_ref", IRNodeRef.coerce(self.collection_ref, "collection_ref"))
        object.__setattr__(self, "interface_version", require_version(self.interface_version))


@dataclass(frozen=True)
class CharacterIR(IRNode):
    skeleton: SkeletonIR | None = None
    skin_bindings: tuple[SkinBindingIR, ...] = ()
    morph_channels: tuple[MorphChannelIR, ...] = ()
    attachment_ports: tuple[AttachmentPortIR, ...] = ()
    character_identity: CharacterIdentityIR | None = None
    NESTED: ClassVar = {
        **IRNode.NESTED, "skeleton": optional(SkeletonIR), "skin_bindings": many(SkinBindingIR),
        "morph_channels": many(MorphChannelIR), "attachment_ports": many(AttachmentPortIR),
        "character_identity": optional(CharacterIdentityIR),
    }

    def __post_init__(self) -> None:
        super(CharacterIR, self).__post_init__()
        if self.kind is not NodeKind.CHARACTER:
            raise IRSchemaError("CharacterIR requires kind=CHARACTER")
        for name, kind in (("skeleton", SkeletonIR), ("character_identity", CharacterIdentityIR)):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, kind.coerce(value, name))
        for name, kind in (("skin_bindings", SkinBindingIR), ("morph_channels", MorphChannelIR), ("attachment_ports", AttachmentPortIR)):
            values = tuple(kind.coerce(item, f"{name}[]") for item in getattr(self, name))
            object.__setattr__(self, name, values)
        if self.character_identity is not None and self.character_identity.character_ref != self.ref:
            raise IRIntegrityError("CharacterIdentityIR ref differs from owning CharacterIR")
        if self.skin_bindings and self.skeleton is None:
            raise IRIntegrityError("skin bindings require a portable skeleton representation")
        if self.skeleton is not None:
            for binding in self.skin_bindings:
                binding.validate_against(self.skeleton)


@dataclass(frozen=True)
class GeometryIR(IRNode):
    geometry_kind: str = "GENERIC"
    coordinate_frame_id: str | None = None
    topology_resource: ResourceRef | None = None
    vertex_count: int | None = None
    face_count: int | None = None
    NESTED: ClassVar = {**IRNode.NESTED, "topology_resource": optional(ResourceRef)}

    def __post_init__(self) -> None:
        super(GeometryIR, self).__post_init__()
        if self.kind is not NodeKind.GEOMETRY:
            raise IRSchemaError("GeometryIR requires kind=GEOMETRY")
        object.__setattr__(self, "geometry_kind", require_identifier(self.geometry_kind, "geometry_kind"))
        if self.coordinate_frame_id is not None:
            object.__setattr__(self, "coordinate_frame_id", require_identifier(self.coordinate_frame_id, "coordinate_frame_id"))
        if self.topology_resource is not None:
            object.__setattr__(self, "topology_resource", ResourceRef.coerce(self.topology_resource, "topology_resource"))
        for name in ("vertex_count", "face_count"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise IRSchemaError(f"{name} must be a non-negative integer")


@dataclass(frozen=True)
class CollectionIR(IRNode):
    member_refs: tuple[IRNodeRef, ...] = ()
    NESTED: ClassVar = {**IRNode.NESTED, "member_refs": many(IRNodeRef)}

    def __post_init__(self) -> None:
        super(CollectionIR, self).__post_init__()
        if self.kind is not NodeKind.COLLECTION:
            raise IRSchemaError("CollectionIR requires kind=COLLECTION")
        refs = tuple(IRNodeRef.coerce(item, "member_refs[]") for item in self.member_refs)
        if len(set(refs)) != len(refs):
            raise IRSchemaError("collection member refs must be unique")
        object.__setattr__(self, "member_refs", tuple(sorted(refs)))


def decode_ir_node(value: Any, path: str = "node") -> IRNode:
    if isinstance(value, IRNode):
        return value
    if not isinstance(value, Mapping):
        raise IRSchemaError(f"{path} must be an IRNode payload")
    kind = value.get("kind")
    class_by_kind = {
        NodeKind.SCENE.value: SceneIR, NodeKind.ENTITY.value: EntityIR, NodeKind.ASSET.value: AssetIR,
        NodeKind.CHARACTER.value: CharacterIR, NodeKind.GEOMETRY.value: GeometryIR, NodeKind.COLLECTION.value: CollectionIR,
    }
    return class_by_kind.get(kind, IRNode).from_payload(value)


def _decode_nodes(value: Any, path: str) -> tuple[IRNode, ...]:
    if not isinstance(value, (tuple, list)):
        raise IRSchemaError(f"{path} must be a sequence")
    return tuple(decode_ir_node(item, f"{path}[]") for item in value)


@dataclass(frozen=True, order=True)
class ContainmentEdge(IRRecord):
    parent: IRNodeRef
    child: IRNodeRef
    edge_id: str

    NESTED: ClassVar = {"parent": one(IRNodeRef), "child": one(IRNodeRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "parent", IRNodeRef.coerce(self.parent, "parent"))
        object.__setattr__(self, "child", IRNodeRef.coerce(self.child, "child"))
        object.__setattr__(self, "edge_id", require_identifier(self.edge_id, "edge_id"))
        if self.parent == self.child:
            raise IRIntegrityError("containment self-cycle is forbidden")


@dataclass(frozen=True)
class RelationshipPolicy(IRRecord):
    family: str
    cycle_policy: CyclePolicy

    def __post_init__(self) -> None:
        object.__setattr__(self, "family", require_identifier(self.family, "family"))
        object.__setattr__(self, "cycle_policy", require_enum(self.cycle_policy, CyclePolicy, "cycle_policy"))


@dataclass(frozen=True, order=True)
class SemanticRelationship(IRRecord):
    relationship_id: str
    family: str
    source: IRNodeRef
    target: IRNodeRef
    trace: Traceability
    attributes: Mapping[str, Any] | None = None

    NESTED: ClassVar = {"source": one(IRNodeRef), "target": one(IRNodeRef), "trace": one(Traceability)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "relationship_id", require_identifier(self.relationship_id, "relationship_id"))
        object.__setattr__(self, "family", require_identifier(self.family, "family"))
        object.__setattr__(self, "source", IRNodeRef.coerce(self.source, "source"))
        object.__setattr__(self, "target", IRNodeRef.coerce(self.target, "target"))
        object.__setattr__(self, "trace", Traceability.coerce(self.trace, "trace"))
        self.trace.require_admitted(f"relationship {self.relationship_id}")
        if self.attributes is not None:
            object.__setattr__(self, "attributes", deep_freeze(self.attributes, "attributes"))


@dataclass(frozen=True)
class IRFragment(IRRecord):
    fragment_id: str
    revision_ref: IRRevisionRef
    node_refs: tuple[IRNodeRef, ...]
    source_refs: tuple[SemanticRef, ...]
    interface: IRInterfaceCapsule
    fragment_digest: str | None = None

    NESTED: ClassVar = {"revision_ref": one(IRRevisionRef), "node_refs": many(IRNodeRef), "source_refs": many(SemanticRef), "interface": one(IRInterfaceCapsule)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "fragment_id", require_identifier(self.fragment_id, "fragment_id"))
        object.__setattr__(self, "revision_ref", IRRevisionRef.coerce(self.revision_ref, "revision_ref"))
        refs = tuple(IRNodeRef.coerce(item, "node_refs[]") for item in self.node_refs)
        if len(set(refs)) != len(refs):
            raise IRSchemaError("fragment node refs must be unique")
        object.__setattr__(self, "node_refs", tuple(sorted(refs)))
        sources = tuple(SemanticRef.coerce(item, "source_refs[]") for item in self.source_refs)
        if not sources:
            raise IRAdmissionError("fragment requires source refs")
        object.__setattr__(self, "source_refs", tuple(sorted({item.text: item for item in sources}.values(), key=lambda item: item.text)))
        object.__setattr__(self, "interface", IRInterfaceCapsule.coerce(self.interface, "interface"))
        if self.fragment_digest is not None:
            from .versions import require_digest
            object.__setattr__(self, "fragment_digest", require_digest(self.fragment_digest, "fragment_digest"))

    @property
    def digest(self) -> str:
        return content_digest({"fragment_id": self.fragment_id, "revision_ref": self.revision_ref, "node_refs": self.node_refs, "source_refs": self.source_refs, "interface": self.interface})


@dataclass(frozen=True, order=True)
class CompositionArc(IRRecord):
    arc_id: str
    source_fragment_id: str
    target_fragment_id: str
    order: int
    precedence: CompositionPrecedence = CompositionPrecedence.AFTER
    override_node_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("arc_id", "source_fragment_id", "target_fragment_id"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        non_negative_int(self.order, "order")
        object.__setattr__(self, "precedence", require_enum(self.precedence, CompositionPrecedence, "precedence"))
        object.__setattr__(self, "override_node_ids", identifiers(self.override_node_ids, "override_node_ids"))
        if self.source_fragment_id == self.target_fragment_id:
            raise IRIntegrityError("composition self-arcs are forbidden")
        if self.precedence is not CompositionPrecedence.OVERRIDE and self.override_node_ids:
            raise IRSchemaError("override node ids require OVERRIDE precedence")


@dataclass(frozen=True)
class CompositionResult(IRRecord):
    ordered_fragment_ids: tuple[str, ...]
    nodes: tuple[IRNode, ...]
    composition_digest: str


def compose_fragments(
    fragments: tuple[IRFragment, ...] | list[IRFragment],
    arcs: tuple[CompositionArc, ...] | list[CompositionArc],
    nodes_by_fragment: Mapping[str, tuple[IRNode, ...] | list[IRNode]],
    *,
    limits: IRLimits = DEFAULT_LIMITS,
) -> CompositionResult:
    """Compose immutable fragments in explicit order; overrides name exact node ids."""
    fragment_by_id = {item.fragment_id: item for item in fragments}
    if len(fragment_by_id) != len(fragments):
        raise IRSchemaError("fragment ids must be unique")
    if len(arcs) > limits.max_edges:
        raise IRLimitError("composition arc count exceeds max_edges")
    if any(arc.source_fragment_id not in fragment_by_id or arc.target_fragment_id not in fragment_by_id for arc in arcs):
        raise IRIntegrityError("composition arc references an unknown fragment")
    if len({arc.arc_id for arc in arcs}) != len(arcs):
        raise IRSchemaError("composition arc ids must be unique")
    adjacency: dict[str, set[str]] = {key: set() for key in fragment_by_id}
    for arc in arcs:
        adjacency[arc.source_fragment_id].add(arc.target_fragment_id)
    _require_acyclic(adjacency, "composition")
    indegree = {key: 0 for key in adjacency}
    for targets in adjacency.values():
        for target in targets:
            indegree[target] += 1
    arc_rank: dict[str, tuple[int, str, str]] = {}
    for arc in arcs:
        rank = (arc.order, arc.precedence.value, arc.arc_id)
        arc_rank[arc.target_fragment_id] = min(rank, arc_rank.get(arc.target_fragment_id, rank))
    ready = sorted((key for key, value in indegree.items() if value == 0), key=lambda key: (arc_rank.get(key, (-1, "BASE", key)), key))
    order: list[str] = []
    while ready:
        ready.sort(key=lambda key: (arc_rank.get(key, (-1, "BASE", key)), key))
        current = ready.pop(0)
        order.append(current)
        for target in sorted(adjacency[current]):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
                ready.sort(key=lambda key: (arc_rank.get(key, (-1, "BASE", key)), key))
    result: dict[tuple[str, str], IRNode] = {}
    for fragment_id in order:
        arc = next((item for item in arcs if item.target_fragment_id == fragment_id), None)
        for node in nodes_by_fragment.get(fragment_id, ()):
            identity = node.identity_key
            if identity in result:
                if arc is None or arc.precedence is not CompositionPrecedence.OVERRIDE or node.ref.node_id not in arc.override_node_ids:
                    raise IRIntegrityError(f"composition duplicates node {node.ref.node_id} without explicit override")
            result[identity] = node
    nodes = tuple(result[key] for key in sorted(result))
    limits.require("max_nodes", len(nodes))
    ids = tuple(order)
    return CompositionResult(ids, nodes, content_digest({"fragments": ids, "nodes": nodes}))


@dataclass(frozen=True)
class PrototypeIR(IRRecord):
    prototype_id: str
    template_nodes: tuple[IRNode, ...]
    interface: IRInterfaceCapsule
    overridable_paths: tuple[str, ...] = ()
    prototype_digest: str | None = None

    NESTED: ClassVar = {"template_nodes": _decode_nodes, "interface": one(IRInterfaceCapsule)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "prototype_id", require_identifier(self.prototype_id, "prototype_id"))
        nodes = tuple(IRNode.coerce(item, "template_nodes[]") for item in self.template_nodes)
        if len({node.identity_key for node in nodes}) != len(nodes):
            raise IRSchemaError("prototype node refs must be unique")
        object.__setattr__(self, "template_nodes", tuple(sorted(nodes, key=lambda item: item.identity_key)))
        object.__setattr__(self, "interface", IRInterfaceCapsule.coerce(self.interface, "interface"))
        object.__setattr__(self, "overridable_paths", tuple(sorted({require_identifier(path, "overridable_paths[]") for path in self.overridable_paths})))
        if self.prototype_digest is not None and self.prototype_digest != self.digest:
            raise IRIntegrityError("prototype digest does not match immutable contents")

    @property
    def digest(self) -> str:
        return content_digest({"prototype_id": self.prototype_id, "template_nodes": self.template_nodes, "interface": self.interface, "overridable_paths": self.overridable_paths})


@dataclass(frozen=True)
class InstanceIR(IRRecord):
    instance_id: str
    prototype_id: str
    prototype_digest: str
    instance_ref: IRNodeRef
    overrides: Mapping[str, Any]

    NESTED: ClassVar = {"instance_ref": one(IRNodeRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "instance_id", require_identifier(self.instance_id, "instance_id"))
        object.__setattr__(self, "prototype_id", require_identifier(self.prototype_id, "prototype_id"))
        from .versions import require_digest
        object.__setattr__(self, "prototype_digest", require_digest(self.prototype_digest, "prototype_digest"))
        object.__setattr__(self, "instance_ref", IRNodeRef.coerce(self.instance_ref, "instance_ref"))
        object.__setattr__(self, "overrides", deep_freeze(self.overrides, "overrides"))

    def validate_against(self, prototype: PrototypeIR) -> None:
        if self.prototype_id != prototype.prototype_id or self.prototype_digest != prototype.digest:
            raise IRIntegrityError("instance prototype ref/digest is stale")
        illegal = set(self.overrides) - set(prototype.overridable_paths)
        if illegal:
            raise IRAdmissionError(f"instance override is outside declared prototype ports: {sorted(illegal)}")


@dataclass(frozen=True)
class IRRevision(IRRecord):
    revision_id: str
    scene: SceneIR
    nodes: tuple[IRNode, ...]
    containment: tuple[ContainmentEdge, ...] = ()
    relationships: tuple[SemanticRelationship, ...] = ()
    relationship_policies: tuple[RelationshipPolicy, ...] = ()
    fragments: tuple[IRFragment, ...] = ()
    composition_arcs: tuple[CompositionArc, ...] = ()
    prototypes: tuple[PrototypeIR, ...] = ()
    instances: tuple[InstanceIR, ...] = ()
    schema_manifest: SchemaManifest = SchemaManifest()
    source_refs: tuple[SemanticRef, ...] = ()
    policy_refs: tuple[SemanticRef, ...] = ()
    parent_ref: IRRevisionRef | None = None
    contract_version: str = CONTRACT_VERSION
    extensions: tuple[ExtensionValue, ...] = ()
    spatial_references: tuple[SpatialReferenceIR, ...] = ()
    coordinate_frames: tuple[CoordinateFrameIR, ...] = ()
    transform_chains: tuple[TransformChainIR, ...] = ()
    spatial_conversion_receipts: tuple[SpatialConversionReceipt, ...] = ()
    cameras: tuple[CameraIR, ...] = ()
    lights: tuple[LightIR, ...] = ()
    spatial_regions: tuple[SpatialRegionIR, ...] = ()
    materials: tuple[MaterialIR, ...] = ()
    texture_resources: tuple[TextureResourceIR, ...] = ()
    material_bindings: tuple[MaterialBindingIR, ...] = ()
    color_values: tuple[ColorValueIR, ...] = ()
    color_conversion_receipts: tuple[ColorConversionReceipt, ...] = ()
    temporal_references: tuple[TemporalReferenceIR, ...] = ()
    temporal_markers: tuple[TemporalMarkerIR, ...] = ()
    temporal_relations: tuple[TemporalRelationIR, ...] = ()
    temporal_samplings: tuple[TemporalSamplingIR, ...] = ()
    temporal_conversion_receipts: tuple[TemporalConversionReceipt, ...] = ()
    motions: tuple[MotionIR, ...] = ()
    motion_layers: tuple[MotionLayerIR, ...] = ()
    audio: tuple[AudioIR, ...] = ()
    audio_bindings: tuple[AudioClipBindingIR, ...] = ()
    music: tuple[MusicIR, ...] = ()
    narrative_projections: tuple[NarrativeProjectionIR, ...] = ()
    timelines: tuple[TimelineIR, ...] = ()
    sync_relations: tuple[SyncRelationIR, ...] = ()

    NESTED: ClassVar = {
        "scene": one(SceneIR), "nodes": _decode_nodes, "containment": many(ContainmentEdge),
        "relationships": many(SemanticRelationship), "relationship_policies": many(RelationshipPolicy),
        "fragments": many(IRFragment), "composition_arcs": many(CompositionArc), "prototypes": many(PrototypeIR),
        "instances": many(InstanceIR), "schema_manifest": one(SchemaManifest), "source_refs": many(SemanticRef),
        "policy_refs": many(SemanticRef), "parent_ref": optional(IRRevisionRef),
        "extensions": many(ExtensionValue), "spatial_references": many(SpatialReferenceIR), "coordinate_frames": many(CoordinateFrameIR),
        "transform_chains": many(TransformChainIR), "spatial_conversion_receipts": many(SpatialConversionReceipt),
        "cameras": many(CameraIR), "lights": many(LightIR), "spatial_regions": many(SpatialRegionIR),
        "materials": many(MaterialIR), "texture_resources": many(TextureResourceIR), "material_bindings": many(MaterialBindingIR), "color_values": many(ColorValueIR),
        "color_conversion_receipts": many(ColorConversionReceipt), "temporal_references": many(TemporalReferenceIR),
        "temporal_markers": many(TemporalMarkerIR), "temporal_relations": many(TemporalRelationIR), "temporal_samplings": many(TemporalSamplingIR),
        "temporal_conversion_receipts": many(TemporalConversionReceipt), "motions": many(MotionIR), "motion_layers": many(MotionLayerIR),
        "audio": many(AudioIR), "audio_bindings": many(AudioClipBindingIR), "music": many(MusicIR),
        "narrative_projections": many(NarrativeProjectionIR), "timelines": many(TimelineIR), "sync_relations": many(SyncRelationIR),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "revision_id", require_identifier(self.revision_id, "revision_id"))
        object.__setattr__(self, "scene", SceneIR.coerce(self.scene, "scene"))
        for name, kind in (("nodes", IRNode), ("containment", ContainmentEdge), ("relationships", SemanticRelationship), ("relationship_policies", RelationshipPolicy), ("fragments", IRFragment), ("composition_arcs", CompositionArc), ("prototypes", PrototypeIR), ("instances", InstanceIR)):
            object.__setattr__(self, name, tuple(kind.coerce(item, f"{name}[]") for item in getattr(self, name)))
        multimodal_fields = (
            ("extensions", ExtensionValue), ("spatial_references", SpatialReferenceIR), ("coordinate_frames", CoordinateFrameIR),
            ("transform_chains", TransformChainIR), ("spatial_conversion_receipts", SpatialConversionReceipt),
            ("cameras", CameraIR), ("lights", LightIR), ("spatial_regions", SpatialRegionIR),
            ("materials", MaterialIR), ("texture_resources", TextureResourceIR), ("material_bindings", MaterialBindingIR), ("color_values", ColorValueIR),
            ("color_conversion_receipts", ColorConversionReceipt), ("temporal_references", TemporalReferenceIR),
            ("temporal_markers", TemporalMarkerIR), ("temporal_relations", TemporalRelationIR), ("temporal_samplings", TemporalSamplingIR),
            ("temporal_conversion_receipts", TemporalConversionReceipt), ("motions", MotionIR), ("motion_layers", MotionLayerIR),
            ("audio", AudioIR), ("audio_bindings", AudioClipBindingIR), ("music", MusicIR),
            ("narrative_projections", NarrativeProjectionIR), ("timelines", TimelineIR), ("sync_relations", SyncRelationIR),
        )
        for name, kind in multimodal_fields:
            values = tuple(kind.coerce(item, f"{name}[]") for item in getattr(self, name))
            object.__setattr__(self, name, values)
        object.__setattr__(self, "schema_manifest", SchemaManifest.coerce(self.schema_manifest, "schema_manifest"))
        for name in ("source_refs", "policy_refs"):
            refs = tuple(SemanticRef.coerce(item, f"{name}[]") for item in getattr(self, name))
            object.__setattr__(self, name, tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))
        if not self.source_refs and not self.policy_refs:
            raise IRAdmissionError("IR revision requires M03 source refs or explicit policy refs")
        if self.parent_ref is not None:
            object.__setattr__(self, "parent_ref", IRRevisionRef.coerce(self.parent_ref, "parent_ref"))
        object.__setattr__(self, "contract_version", require_version(self.contract_version, "contract_version"))
        validate_graph(self.nodes, self.containment, self.relationships, self.relationship_policies)
        self._validate_cross_references()
        for instance in self.instances:
            prototype = next((item for item in self.prototypes if item.prototype_id == instance.prototype_id), None)
            if prototype is None:
                raise IRIntegrityError("instance refers to a missing prototype")
            instance.validate_against(prototype)

    def _validate_cross_references(self, *, limits: IRLimits = DEFAULT_LIMITS) -> None:
        node_by_ref = {node.identity_key: node for node in self.nodes}
        for root in self.scene.root_node_refs:
            if (root.document_id, root.node_id) not in node_by_ref:
                raise IRIntegrityError("scene root ref is missing from revision nodes")
        for node in self.nodes:
            typed_refs = ()
            if isinstance(node, AssetIR):
                typed_refs = node.geometry_refs + ((node.collection_ref,) if node.collection_ref is not None else ())
            elif isinstance(node, CollectionIR):
                typed_refs = node.member_refs
            elif isinstance(node, CharacterIR):
                typed_refs = tuple(binding.geometry_ref for binding in node.skin_bindings) + tuple(morph.geometry_ref for morph in node.morph_channels)
            for ref in typed_refs:
                if (ref.document_id, ref.node_id) not in node_by_ref:
                    raise IRIntegrityError(f"typed node {node.ref.node_id} has a dangling semantic ref")
        spatial_refs = {item.reference_id: item for item in self.spatial_references}
        frames = {item.frame_id: item for item in self.coordinate_frames}
        if len(spatial_refs) != len(self.spatial_references) or len(frames) != len(self.coordinate_frames):
            raise IRIntegrityError("spatial reference/frame ids must be unique")
        unique_collections = (
            ("transform chain", self.transform_chains, lambda item: item.chain_id),
            ("spatial conversion receipt", self.spatial_conversion_receipts, lambda item: item.conversion_id),
            ("camera", self.cameras, lambda item: (item.camera_ref.document_id, item.camera_ref.node_id)),
            ("light", self.lights, lambda item: (item.light_ref.document_id, item.light_ref.node_id)),
            ("spatial region", self.spatial_regions, lambda item: item.region_id),
            ("material binding", self.material_bindings, lambda item: item.binding_id),
            ("color conversion receipt", self.color_conversion_receipts, lambda item: item.receipt_id),
            ("temporal marker", self.temporal_markers, lambda item: item.marker_id),
            ("temporal relation", self.temporal_relations, lambda item: item.relation_id),
            ("temporal sampling", self.temporal_samplings, lambda item: item.sampling_id),
            ("temporal conversion receipt", self.temporal_conversion_receipts, lambda item: item.receipt_id),
            ("motion", self.motions, lambda item: item.motion_id),
            ("motion layer", self.motion_layers, lambda item: item.layer_id),
            ("audio", self.audio, lambda item: item.audio_id),
            ("audio binding", self.audio_bindings, lambda item: item.binding_id),
            ("music", self.music, lambda item: item.music_id),
            ("narrative projection", self.narrative_projections, lambda item: item.projection_id),
            ("timeline", self.timelines, lambda item: item.timeline_id),
            ("sync relation", self.sync_relations, lambda item: item.relation_id),
        )
        for label, values, key in unique_collections:
            if len({key(item) for item in values}) != len(values):
                raise IRIntegrityError(f"{label} ids must be unique within a revision")
        for frame in self.coordinate_frames:
            if frame.spatial_reference_id not in spatial_refs:
                raise IRIntegrityError(f"coordinate frame {frame.frame_id} references an unknown spatial reference")
            if frame.parent_frame_id is not None and frame.parent_frame_id not in frames:
                raise IRIntegrityError(f"coordinate frame {frame.frame_id} has a dangling parent frame")
        _require_acyclic({key: ({frames[key].parent_frame_id} if frames[key].parent_frame_id else set()) for key in frames}, "coordinate frame", max_depth=limits.max_depth)
        transform_ids = {item.chain_id for item in self.transform_chains}
        for node in self.nodes:
            if isinstance(node, EntityIR) and node.transform_chain_id is not None and node.transform_chain_id not in transform_ids:
                raise IRIntegrityError("entity has a dangling authored transform-chain ref")
            if isinstance(node, GeometryIR) and node.coordinate_frame_id is not None and node.coordinate_frame_id not in frames:
                raise IRIntegrityError("geometry has a dangling coordinate-frame ref")
        for chain in self.transform_chains:
            source, target = frames.get(chain.source_frame_id), frames.get(chain.target_frame_id)
            if source is None or target is None:
                raise IRIntegrityError("transform chain has a dangling coordinate-frame ref")
            spatial = spatial_refs[source.spatial_reference_id]
            for operation in chain.operations:
                if operation.operation == "translate" and operation.unit != spatial.length_unit:
                    raise IRIntegrityError("authored translation unit differs from its spatial reference")
                if operation.operation == "rotate_euler" and operation.unit != spatial.angle_unit:
                    raise IRIntegrityError("authored rotation unit differs from its spatial reference")
        for camera in self.cameras:
            if camera.camera_ref.document_id != self.scene.ref.document_id or (camera.camera_ref.document_id, camera.camera_ref.node_id) not in node_by_ref:
                raise IRIntegrityError("camera ref is missing from revision nodes")
            if camera.coordinate_frame_id not in frames:
                raise IRIntegrityError("camera has a dangling coordinate-frame ref")
        for light in self.lights:
            if (light.light_ref.document_id, light.light_ref.node_id) not in node_by_ref:
                raise IRIntegrityError("light ref is missing from revision nodes")
            for influence in light.influences:
                if influence.affected_region_ref is not None and (influence.affected_region_ref.document_id, influence.affected_region_ref.node_id) not in node_by_ref:
                    raise IRIntegrityError("light influence has a dangling region ref")
        for region in self.spatial_regions:
            if region.coordinate_frame_id not in frames:
                raise IRIntegrityError("spatial region has a dangling coordinate-frame ref")
        material_ids = {item.material_id for item in self.materials}
        if len(material_ids) != len(self.materials):
            raise IRIntegrityError("material ids must be unique within a revision")
        for binding in self.material_bindings:
            if binding.material_id not in material_ids or (binding.target_ref.document_id, binding.target_ref.node_id) not in node_by_ref:
                raise IRIntegrityError("material binding has a dangling material or target ref")
        temporal_refs = {item.reference_id: item for item in self.temporal_references}
        if len(temporal_refs) != len(self.temporal_references):
            raise IRIntegrityError("temporal reference ids must be unique")
        for item in self.temporal_markers:
            if item.time.reference_id not in temporal_refs:
                raise IRIntegrityError("temporal marker has a dangling time reference")
        for item in self.temporal_relations:
            if item.source_time.reference_id not in temporal_refs or item.target_time.reference_id not in temporal_refs:
                raise IRIntegrityError("temporal relation has a dangling time reference")
        for item in self.temporal_samplings:
            if item.range.start.reference_id not in temporal_refs:
                raise IRIntegrityError("temporal sampling has a dangling time reference")
        for item in self.temporal_conversion_receipts:
            if item.source_reference.reference_id not in temporal_refs or item.target_reference.reference_id not in temporal_refs:
                raise IRIntegrityError("temporal conversion receipt has a dangling reference")
        motion_ids = {item.motion_id for item in self.motions}
        for layer in self.motion_layers:
            if len({clip.clip_id for clip in layer.clips}) != len(layer.clips):
                raise IRIntegrityError("motion clip ids must be unique within a layer")
            for clip in layer.clips:
                if clip.motion_ref not in motion_ids or clip.time_range.start.reference_id not in temporal_refs:
                    raise IRIntegrityError("motion clip has a dangling motion or time ref")
        for motion in self.motions:
            for channel in motion.channels:
                key = (channel.target.target.document_id, channel.target.target.node_id)
                if key not in node_by_ref:
                    raise IRIntegrityError("motion channel has a dangling semantic target ref")
        audio_ids = {item.audio_id for item in self.audio}
        for item in self.audio:
            if item.spatial is not None and item.spatial.coordinate_frame.frame_id not in frames:
                raise IRIntegrityError("spatial audio has a dangling coordinate-frame ref")
        for binding in self.audio_bindings:
            if binding.audio_id not in audio_ids or binding.range.start.reference_id not in temporal_refs:
                raise IRIntegrityError("audio clip binding has a dangling audio or time ref")
        for item in self.music:
            if item.time_reference_id not in temporal_refs:
                raise IRIntegrityError("MusicIR has a dangling time reference")
        for timeline in self.timelines:
            if timeline.time_reference_id not in temporal_refs:
                raise IRIntegrityError("TimelineIR has a dangling time reference")
            item_ids = [item.item_id for track in timeline.tracks for item in track.items]
            if len(set(item_ids)) != len(item_ids):
                raise IRIntegrityError("timeline item ids must be unique within a timeline")
            for track in timeline.tracks:
                for item in track.items:
                    if item.range.start.reference_id != timeline.time_reference_id:
                        raise IRIntegrityError("timeline item has a dangling time reference")
                    key = (item.target_ref.document_id, item.target_ref.node_id)
                    if item.target_ref != self.scene.ref and key not in node_by_ref:
                        raise IRIntegrityError("timeline item has a dangling target ref")
            for sequence in timeline.shot_sequences:
                for shot in sequence.shots:
                    key = (shot.scene_ref.document_id, shot.scene_ref.node_id)
                    if shot.scene_ref != self.scene.ref and key not in node_by_ref:
                        raise IRIntegrityError("sequence shot has a dangling scene ref")
                    if shot.camera_ref is not None:
                        camera_key = (shot.camera_ref.document_id, shot.camera_ref.node_id)
                        if camera_key not in node_by_ref or not any(camera.camera_ref == shot.camera_ref for camera in self.cameras):
                            raise IRIntegrityError("sequence shot has a dangling or unrepresented camera ref")
            if timeline.narrative_projection is not None and any(cue.range.start.reference_id not in temporal_refs for cue in timeline.narrative_projection.cues):
                raise IRIntegrityError("timeline narrative cue has a dangling time reference")
        for projection in self.narrative_projections:
            if any(cue.range.start.reference_id not in temporal_refs for cue in projection.cues):
                raise IRIntegrityError("narrative projection cue has a dangling time reference")
        for relation in self.sync_relations:
            if relation.source.reference_id not in temporal_refs:
                raise IRIntegrityError("sync relation has a dangling time reference")

    @property
    def revision_digest(self) -> str:
        return content_digest(self.to_payload())

    @property
    def revision_ref(self) -> IRRevisionRef:
        return IRRevisionRef(self.scene.ref.document_id, self.revision_id, self.revision_digest)


@dataclass(frozen=True)
class MultimodalIRDocument(IRRecord):
    document_id: str
    revisions: tuple[IRRevision, ...]

    NESTED: ClassVar = {"revisions": many(IRRevision)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "document_id", require_identifier(self.document_id, "document_id"))
        revisions = tuple(IRRevision.coerce(item, "revisions[]") for item in self.revisions)
        if not revisions or len({item.revision_id for item in revisions}) != len(revisions):
            raise IRSchemaError("document revisions must be non-empty and uniquely identified")
        for revision in revisions:
            if revision.scene.ref.document_id != self.document_id or any(node.ref.document_id != self.document_id for node in revision.nodes):
                raise IRIntegrityError("revision contains refs from another document")
        refs = {item.revision_id: item.revision_ref for item in revisions}
        for revision in revisions:
            if revision.parent_ref is not None:
                parent = refs.get(revision.parent_ref.revision_id)
                if parent is None or parent.revision_digest != revision.parent_ref.revision_digest:
                    raise IRIntegrityError("revision parent ref is missing or stale")
        object.__setattr__(self, "revisions", tuple(revisions))

    @property
    def head(self) -> IRRevision:
        child_ids = {item.parent_ref.revision_id for item in self.revisions if item.parent_ref is not None}
        heads = [item for item in self.revisions if item.revision_id not in child_ids]
        if len(heads) != 1:
            raise IRIntegrityError("document must have exactly one unparented head revision")
        return heads[0]


@dataclass(frozen=True)
class IRDocumentEnvelope(IRRecord):
    document: MultimodalIRDocument
    contract_version: str = CONTRACT_VERSION
    core_schema_version: str = CORE_SCHEMA_VERSION
    transport_version: str = "iris-m04-json-v1"

    NESTED: ClassVar = {"document": one(MultimodalIRDocument)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "document", MultimodalIRDocument.coerce(self.document, "document"))
        object.__setattr__(self, "contract_version", require_version(self.contract_version, "contract_version"))
        object.__setattr__(self, "core_schema_version", require_version(self.core_schema_version, "core_schema_version"))
        object.__setattr__(self, "transport_version", require_version(self.transport_version, "transport_version"))

    @property
    def digest(self) -> str:
        return content_digest(self.to_payload())


def validate_graph(
    nodes: tuple[IRNode, ...] | list[IRNode],
    containment: tuple[ContainmentEdge, ...] | list[ContainmentEdge],
    relationships: tuple[SemanticRelationship, ...] | list[SemanticRelationship] = (),
    policies: tuple[RelationshipPolicy, ...] | list[RelationshipPolicy] = (),
    *, limits: IRLimits = DEFAULT_LIMITS,
) -> None:
    node_map = {node.identity_key: node for node in nodes}
    if len(node_map) != len(nodes):
        raise IRIntegrityError("duplicate canonical node ids")
    limits.require("max_nodes", len(nodes))
    limits.require("max_edges", len(containment) + len(relationships))
    if len({edge.edge_id for edge in containment}) != len(containment):
        raise IRIntegrityError("duplicate containment edge ids")
    adjacency: dict[tuple[str, str], set[tuple[str, str]]] = {key: set() for key in node_map}
    for edge in containment:
        parent, child = (edge.parent.document_id, edge.parent.node_id), (edge.child.document_id, edge.child.node_id)
        if parent not in node_map or child not in node_map:
            raise IRIntegrityError("containment edge has a dangling node ref")
        adjacency[parent].add(child)
    _require_acyclic(adjacency, "containment/transform", max_depth=limits.max_depth)
    counts: dict[tuple[str, str], int] = {}
    for source, targets in adjacency.items():
        counts[source] = len(targets)
    if counts and max(counts.values()) > limits.max_fanout:
        raise IRLimitError("containment graph fanout exceeds max_fanout")
    policies_by_family = {item.family: item.cycle_policy for item in policies}
    if len(policies_by_family) != len(policies):
        raise IRSchemaError("relationship policies must have unique families")
    relation_ids = set()
    grouped: dict[str, dict[tuple[str, str], set[tuple[str, str]]]] = {}
    for relationship in relationships:
        if relationship.relationship_id in relation_ids:
            raise IRIntegrityError("duplicate semantic relationship ids")
        relation_ids.add(relationship.relationship_id)
        source = (relationship.source.document_id, relationship.source.node_id)
        target = (relationship.target.document_id, relationship.target.node_id)
        if source not in node_map or target not in node_map:
            raise IRIntegrityError("semantic relationship has a dangling node ref")
        policy = policies_by_family.get(relationship.family)
        if policy is None:
            raise IRAdmissionError(f"relationship family {relationship.family} has no cycle policy")
        family_graph = grouped.setdefault(relationship.family, {key: set() for key in node_map})
        family_graph[source].add(target)
    for family, graph in grouped.items():
        if policies_by_family[family] is CyclePolicy.ACYCLIC:
            _require_acyclic(graph, f"relationship family {family}", max_depth=limits.max_depth)


def _require_acyclic(adjacency: Mapping[Any, set[Any]], label: str, *, max_depth: int = DEFAULT_LIMITS.max_depth) -> None:
    visiting: set[Any] = set()
    depth_by_node: dict[Any, int] = {}

    def visit(node: Any) -> int:
        if node in visiting:
            raise IRIntegrityError(f"{label} graph contains a cycle")
        cached = depth_by_node.get(node)
        if cached is not None:
            return cached
        visiting.add(node)
        depth = 0
        for child in sorted(adjacency.get(node, ()), key=repr):
            depth = max(depth, 1 + visit(child))
        visiting.remove(node)
        if depth > max_depth:
            raise IRLimitError(f"{label} depth exceeds max_depth")
        depth_by_node[node] = depth
        return depth

    for node in sorted(adjacency, key=repr):
        visit(node)


def find_transform_path(nodes: tuple[IRNode, ...], edges: tuple[ContainmentEdge, ...], source: IRNodeRef, target: IRNodeRef) -> tuple[IRNodeRef, ...] | None:
    graph: dict[IRNodeRef, list[IRNodeRef]] = {}
    for edge in edges:
        graph.setdefault(edge.parent, []).append(edge.child)
    queue: list[tuple[IRNodeRef, tuple[IRNodeRef, ...]]] = [(source, (source,))]
    seen = {source}
    while queue:
        current, path = queue.pop(0)
        if current == target:
            return path
        for child in sorted(graph.get(current, [])):
            if child not in seen:
                seen.add(child)
                queue.append((child, path + (child,)))
    return None
