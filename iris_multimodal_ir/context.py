"""Local fingerprints, semantic deltas, and minimum-sufficient slices."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Any, ClassVar, Mapping

from iris_intent.identity import SemanticRef

from .base import IRRecord, many, one
from .common import deep_freeze
from .errors import IRIntegrityError, IRSchemaError
from .graph import ContainmentEdge, EntityIR, GeometryIR, IRNode, IRRevision, SemanticRelationship, decode_ir_node
from .identity import IRNodeRef, ResourceRef
from .limits import DEFAULT_LIMITS, IRLimits
from .lowering import TargetRepresentationProfile
from .resources import IRInterfaceCapsule
from .temporal import TimeRangeIR
from .versions import canonical_value, content_digest, require_digest, require_identifier, require_text

__all__ = [
    "IRStructuralFingerprint", "IRSubgraphFingerprint", "IRInterfaceFingerprint", "IRSemanticDelta",
    "SemanticRecordChange",
    "IRCanonicalSliceRecord", "MinimumSufficientIRSlice", "MinimumSufficientTemporalSlice", "CapabilitySlice",
    "structural_fingerprint", "subgraph_fingerprint", "interface_fingerprint", "semantic_delta",
    "build_ir_slice", "build_temporal_slice", "build_capability_slice",
]


@dataclass(frozen=True)
class IRStructuralFingerprint(IRRecord):
    source_revision_digest: str
    digest: str
    node_count: int
    containment_edge_count: int
    relationship_count: int
    fingerprint_version: str = "structural-fingerprint-v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_revision_digest", require_digest(self.source_revision_digest, "source_revision_digest"))
        object.__setattr__(self, "digest", require_digest(self.digest, "digest"))
        for name in ("node_count", "containment_edge_count", "relationship_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise IRSchemaError(f"{name} must be a non-negative integer")


@dataclass(frozen=True)
class IRSubgraphFingerprint(IRRecord):
    source_revision_digest: str
    root_refs: tuple[IRNodeRef, ...]
    included_refs: tuple[IRNodeRef, ...]
    digest: str
    boundary_refs: tuple[IRNodeRef, ...] = ()
    resource_digests: tuple[str, ...] = ()

    NESTED: ClassVar = {"root_refs": many(IRNodeRef), "included_refs": many(IRNodeRef), "boundary_refs": many(IRNodeRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_revision_digest", require_digest(self.source_revision_digest, "source_revision_digest"))
        for name in ("root_refs", "included_refs", "boundary_refs"):
            refs = tuple(IRNodeRef.coerce(item, f"{name}[]") for item in getattr(self, name))
            object.__setattr__(self, name, tuple(sorted(set(refs))))
        object.__setattr__(self, "digest", require_digest(self.digest, "digest"))
        object.__setattr__(self, "resource_digests", tuple(sorted(set(require_digest(item, "resource_digests[]") for item in self.resource_digests))))


@dataclass(frozen=True)
class IRInterfaceFingerprint(IRRecord):
    source_revision_digest: str
    node_ref: IRNodeRef
    interface_digest: str
    payload_resource_count: int

    NESTED: ClassVar = {"node_ref": one(IRNodeRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_revision_digest", require_digest(self.source_revision_digest, "source_revision_digest"))
        object.__setattr__(self, "node_ref", IRNodeRef.coerce(self.node_ref, "node_ref"))
        object.__setattr__(self, "interface_digest", require_digest(self.interface_digest, "interface_digest"))
        if isinstance(self.payload_resource_count, bool) or not isinstance(self.payload_resource_count, int) or self.payload_resource_count < 0:
            raise IRSchemaError("payload_resource_count must be non-negative")


@dataclass(frozen=True, order=True)
class SemanticNodeChange(IRRecord):
    node_ref: IRNodeRef
    change: str
    previous_digest: str | None = None
    current_digest: str | None = None

    NESTED: ClassVar = {"node_ref": one(IRNodeRef)}


@dataclass(frozen=True, order=True)
class SemanticRecordChange(IRRecord):
    path: str
    change: str
    previous_digest: str | None = None
    current_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", require_text(self.path, "path", maximum=1024))
        object.__setattr__(self, "change", require_text(self.change, "change", maximum=32))
        if self.change not in {"ADDED", "REMOVED", "CHANGED"}:
            raise IRSchemaError("semantic record change must be ADDED, REMOVED, or CHANGED")
        for name in ("previous_digest", "current_digest"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_digest(value, name))


@dataclass(frozen=True)
class IRSemanticDelta(IRRecord):
    previous_revision_digest: str
    current_revision_digest: str
    changes: tuple[SemanticNodeChange, ...]
    invalidated_resource_digests: tuple[str, ...]
    delta_digest: str
    record_changes: tuple[SemanticRecordChange, ...] = ()

    NESTED: ClassVar = {"changes": many(SemanticNodeChange), "record_changes": many(SemanticRecordChange)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "previous_revision_digest", require_digest(self.previous_revision_digest, "previous_revision_digest"))
        object.__setattr__(self, "current_revision_digest", require_digest(self.current_revision_digest, "current_revision_digest"))
        changes = tuple(SemanticNodeChange.coerce(item, "changes[]") for item in self.changes)
        object.__setattr__(self, "changes", tuple(sorted(changes, key=lambda item: (item.node_ref.document_id, item.node_ref.node_id))))
        record_changes = tuple(SemanticRecordChange.coerce(item, "record_changes[]") for item in self.record_changes)
        if len({item.path for item in record_changes}) != len(record_changes):
            raise IRSchemaError("semantic delta record paths must be unique")
        object.__setattr__(self, "record_changes", tuple(sorted(record_changes, key=lambda item: item.path)))
        object.__setattr__(self, "invalidated_resource_digests", tuple(sorted(set(require_digest(item, "invalidated_resource_digests[]") for item in self.invalidated_resource_digests))))
        object.__setattr__(self, "delta_digest", require_digest(self.delta_digest, "delta_digest"))


@dataclass(frozen=True)
class IRCanonicalSliceRecord(IRRecord):
    path: str
    record_kind: str
    value_digest: str
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", require_text(self.path, "path", maximum=1024))
        object.__setattr__(self, "record_kind", require_text(self.record_kind, "record_kind", maximum=128))
        object.__setattr__(self, "value_digest", require_digest(self.value_digest, "value_digest"))
        frozen = deep_freeze(self.payload, "payload")
        object.__setattr__(self, "payload", frozen)
        if content_digest(canonical_value(frozen)) != self.value_digest:
            raise IRIntegrityError("slice record digest does not match its canonical payload")


def _decode_interface_capsules(value: Any, path: str) -> tuple[tuple[IRNodeRef, IRInterfaceCapsule], ...]:
    if not isinstance(value, (tuple, list)):
        raise IRSchemaError(f"{path} must be a sequence")
    decoded = []
    for item in value:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise IRSchemaError(f"{path} entries must contain a node ref and interface capsule")
        decoded.append((IRNodeRef.coerce(item[0], f"{path}[].node_ref"), IRInterfaceCapsule.coerce(item[1], f"{path}[].interface")))
    return tuple(decoded)


@dataclass(frozen=True)
class MinimumSufficientIRSlice(IRRecord):
    slice_id: str
    source_revision_digest: str
    root_refs: tuple[IRNodeRef, ...]
    nodes: tuple[IRNode, ...]
    containment: tuple[ContainmentEdge, ...]
    relationships: tuple[SemanticRelationship, ...]
    interface_capsules: tuple[tuple[IRNodeRef, IRInterfaceCapsule], ...]
    resource_refs: tuple[ResourceRef, ...]
    loaded_payload_bytes: int
    slice_digest: str
    semantic_records: tuple[IRCanonicalSliceRecord, ...] = ()

    NESTED: ClassVar = {
        "root_refs": many(IRNodeRef), "nodes": lambda value, path: tuple(decode_ir_node(item, f"{path}[]") for item in value),
        "containment": many(ContainmentEdge), "relationships": many(SemanticRelationship),
        "interface_capsules": _decode_interface_capsules, "resource_refs": many(ResourceRef),
        "semantic_records": many(IRCanonicalSliceRecord),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "slice_id", require_identifier(self.slice_id, "slice_id"))
        object.__setattr__(self, "source_revision_digest", require_digest(self.source_revision_digest, "source_revision_digest"))
        object.__setattr__(self, "slice_digest", require_digest(self.slice_digest, "slice_digest"))
        records = tuple(IRCanonicalSliceRecord.coerce(item, "semantic_records[]") for item in self.semantic_records)
        if len({item.path for item in records}) != len(records):
            raise IRSchemaError("minimum-sufficient slice record paths must be unique")
        object.__setattr__(self, "semantic_records", tuple(sorted(records, key=lambda item: item.path)))
        resources = tuple(ResourceRef.coerce(item, "resource_refs[]") for item in self.resource_refs)
        if len({item.identity_key for item in resources}) != len(resources):
            raise IRSchemaError("minimum-sufficient slice resource identities must be unique")
        object.__setattr__(self, "resource_refs", tuple(sorted(resources, key=lambda item: repr(item.identity_key))))
        if self.loaded_payload_bytes != 0:
            raise IRIntegrityError("minimum sufficient semantic slice must not load deferred media payload bytes")


@dataclass(frozen=True)
class MinimumSufficientTemporalSlice(IRRecord):
    slice_id: str
    source_digest: str
    requested_range: TimeRangeIR
    included_paths: tuple[str, ...]
    slice_digest: str

    NESTED: ClassVar = {"requested_range": one(TimeRangeIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "slice_id", require_identifier(self.slice_id, "slice_id"))
        object.__setattr__(self, "source_digest", require_digest(self.source_digest, "source_digest"))
        object.__setattr__(self, "requested_range", TimeRangeIR.coerce(self.requested_range, "requested_range"))
        object.__setattr__(self, "included_paths", tuple(sorted(set(require_text(item, "included_paths[]", maximum=1024) for item in self.included_paths))))
        object.__setattr__(self, "slice_digest", require_digest(self.slice_digest, "slice_digest"))


@dataclass(frozen=True)
class CapabilitySlice(IRRecord):
    slice_id: str
    source_revision_digest: str
    profile_id: str
    capability_ids: tuple[str, ...]
    semantic_refs: tuple[SemanticRef, ...]
    digest: str

    NESTED: ClassVar = {"semantic_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "slice_id", require_identifier(self.slice_id, "slice_id"))
        object.__setattr__(self, "source_revision_digest", require_digest(self.source_revision_digest, "source_revision_digest"))
        object.__setattr__(self, "profile_id", require_identifier(self.profile_id, "profile_id"))
        object.__setattr__(self, "capability_ids", tuple(sorted(set(require_identifier(item, "capability_ids[]") for item in self.capability_ids))))
        refs = tuple(SemanticRef.coerce(item, "semantic_refs[]") for item in self.semantic_refs)
        object.__setattr__(self, "semantic_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))
        object.__setattr__(self, "digest", require_digest(self.digest, "digest"))


def structural_fingerprint(revision: IRRevision) -> IRStructuralFingerprint:
    revision = IRRevision.coerce(revision, "revision")
    shape = {
        "nodes": tuple(sorted((node.ref, node.kind.value) for node in revision.nodes)),
        "containment": tuple(sorted((edge.parent, edge.child) for edge in revision.containment)),
        "relationships": tuple(sorted((edge.family, edge.source, edge.target) for edge in revision.relationships)),
        "schema": revision.schema_manifest,
    }
    return IRStructuralFingerprint(revision.revision_digest, content_digest(shape), len(revision.nodes), len(revision.containment), len(revision.relationships))


def _related_revision_records(revision: IRRevision, included: set[tuple[str, str]]) -> tuple[tuple[str, Any], ...]:
    nodes = {(node.ref.document_id, node.ref.node_id): node for node in revision.nodes}
    node_ids = {node_id for _, node_id in included}
    selected: dict[str, Any] = {}

    def add(field_name: str, item: Any, key_name: str | None = None, *, item_key: str | None = None) -> None:
        if item_key is None:
            if key_name is not None:
                item_key = str(getattr(item, key_name))
            elif field_name == "cameras":
                item_key = item.camera_ref.node_id
            elif field_name == "lights":
                item_key = item.light_ref.node_id
            elif field_name == "texture_resources":
                item_key = item.resource.resource_id
            else:
                item_key = content_digest(item)
        selected[f"{field_name}/{item_key}"] = item

    frame_ids: set[str] = set()
    chain_ids: set[str] = set()
    for node in nodes.values():
        if (node.ref.document_id, node.ref.node_id) not in included:
            continue
        if isinstance(node, EntityIR) and node.transform_chain_id:
            chain_ids.add(node.transform_chain_id)
        if isinstance(node, GeometryIR) and node.coordinate_frame_id:
            frame_ids.add(node.coordinate_frame_id)

    chains = {item.chain_id: item for item in revision.transform_chains}
    for chain_id in chain_ids:
        chain = chains.get(chain_id)
        if chain is not None:
            add("transform_chains", chain, "chain_id")
            frame_ids.update((chain.source_frame_id, chain.target_frame_id))
    frames = {item.frame_id: item for item in revision.coordinate_frames}
    pending = list(frame_ids)
    while pending:
        frame = frames.get(pending.pop())
        if frame is None:
            continue
        add("coordinate_frames", frame, "frame_id")
        add("spatial_references", next(item for item in revision.spatial_references if item.reference_id == frame.spatial_reference_id), "reference_id")
        if frame.parent_frame_id is not None and frame.parent_frame_id not in frame_ids:
            frame_ids.add(frame.parent_frame_id)
            pending.append(frame.parent_frame_id)

    camera_refs = {(item.camera_ref.document_id, item.camera_ref.node_id) for item in revision.cameras}
    selected_camera_refs = camera_refs & included
    for camera in revision.cameras:
        if (camera.camera_ref.document_id, camera.camera_ref.node_id) in selected_camera_refs:
            add("cameras", camera)
            frame_ids.add(camera.coordinate_frame_id)
            frame = frames.get(camera.coordinate_frame_id)
            if frame is not None:
                add("coordinate_frames", frame, "frame_id")
                spatial = next(item for item in revision.spatial_references if item.reference_id == frame.spatial_reference_id)
                add("spatial_references", spatial, "reference_id")

    selected_light_refs = {(item.light_ref.document_id, item.light_ref.node_id) for item in revision.lights} & included
    for light in revision.lights:
        if (light.light_ref.document_id, light.light_ref.node_id) in selected_light_refs or any(
            influence.affected_region_ref is not None
            and (influence.affected_region_ref.document_id, influence.affected_region_ref.node_id) in included
            for influence in light.influences
        ):
            add("lights", light)

    for region in revision.spatial_regions:
        if region.region_id in node_ids or region.coordinate_frame_id in frame_ids:
            add("spatial_regions", region, "region_id")

    material_ids: set[str] = set()
    for binding in revision.material_bindings:
        if (binding.target_ref.document_id, binding.target_ref.node_id) in included:
            add("material_bindings", binding, "binding_id")
            material_ids.add(binding.material_id)
    texture_ids: set[str] = set()
    for material in revision.materials:
        if material.material_id in material_ids:
            add("materials", material, "material_id")
            texture_ids.update(
                texture.resource.resource_id
                for node in material.graph.nodes
                for texture in node.texture_refs
            )
    for texture in revision.texture_resources:
        if texture.resource.resource_id in texture_ids:
            add("texture_resources", texture)

    motion_ids: set[str] = set()
    temporal_ids: set[str] = set()
    for motion in revision.motions:
        if any((channel.target.target.document_id, channel.target.target.node_id) in included for channel in motion.channels):
            add("motions", motion, "motion_id")
            motion_ids.add(motion.motion_id)
            for channel in motion.channels:
                if channel.curve is not None and channel.curve.keys:
                    temporal_ids.add(channel.curve.keys[0].time.reference_id)
    for layer in revision.motion_layers:
        if any(clip.motion_ref in motion_ids for clip in layer.clips):
            add("motion_layers", layer, "layer_id")
            temporal_ids.update(clip.time_range.start.reference_id for clip in layer.clips if clip.motion_ref in motion_ids)

    audio_ids: set[str] = set()
    for audio in revision.audio:
        if audio.audio_id in node_ids or (audio.spatial is not None and audio.spatial.coordinate_frame.frame_id in frame_ids):
            add("audio", audio, "audio_id")
            audio_ids.add(audio.audio_id)
            if audio.spatial is not None:
                frame_ids.add(audio.spatial.coordinate_frame.frame_id)
    for binding in revision.audio_bindings:
        if binding.audio_id in audio_ids:
            add("audio_bindings", binding, "binding_id")
            temporal_ids.add(binding.range.start.reference_id)

    for timeline in revision.timelines:
        timeline_selected = any(
            (item.target_ref.document_id, item.target_ref.node_id) in included
            for track in timeline.tracks for item in track.items
        ) or any(
            (shot.scene_ref.document_id, shot.scene_ref.node_id) in included
            or (shot.camera_ref is not None and (shot.camera_ref.document_id, shot.camera_ref.node_id) in included)
            for sequence in timeline.shot_sequences for shot in sequence.shots
        )
        if timeline_selected:
            add("timelines", timeline, "timeline_id")
            temporal_ids.add(timeline.time_reference_id)

    for music in revision.music:
        if music.time_reference_id in temporal_ids:
            add("music", music, "music_id")
    for projection in revision.narrative_projections:
        if any(cue.range.start.reference_id in temporal_ids for cue in projection.cues):
            add("narrative_projections", projection, "projection_id")
            temporal_ids.update(cue.range.start.reference_id for cue in projection.cues)
    for reference in revision.temporal_references:
        if reference.reference_id in temporal_ids:
            add("temporal_references", reference, "reference_id")
    for marker in revision.temporal_markers:
        if marker.time.reference_id in temporal_ids:
            add("temporal_markers", marker, "marker_id")
    for relation in revision.temporal_relations:
        if relation.source_time.reference_id in temporal_ids or relation.target_time.reference_id in temporal_ids:
            add("temporal_relations", relation, "relation_id")
    for sampling in revision.temporal_samplings:
        if sampling.range.start.reference_id in temporal_ids:
            add("temporal_samplings", sampling, "sampling_id")
    for receipt in revision.temporal_conversion_receipts:
        if receipt.source_reference.reference_id in temporal_ids or receipt.target_reference.reference_id in temporal_ids:
            add("temporal_conversion_receipts", receipt, "receipt_id")
    for relation in revision.sync_relations:
        if relation.source.reference_id in temporal_ids:
            add("sync_relations", relation, "relation_id")

    return tuple(sorted(selected.items()))


def subgraph_fingerprint(revision: IRRevision, root_refs: tuple[IRNodeRef, ...], *, include_relationship_neighbors: bool = True, limits: IRLimits = DEFAULT_LIMITS) -> IRSubgraphFingerprint:
    revision = IRRevision.coerce(revision, "revision")
    roots = tuple(IRNodeRef.coerce(item, "root_refs[]") for item in root_refs)
    if not roots:
        raise IRSchemaError("subgraph fingerprint requires at least one root")
    node_by_ref = {(node.ref.document_id, node.ref.node_id): node for node in revision.nodes}
    included = {(item.document_id, item.node_id) for item in roots}
    if included - set(node_by_ref):
        raise IRIntegrityError("subgraph root is absent from revision")
    edges = revision.containment
    changed = True
    while changed:
        changed = False
        for edge in edges:
            parent = (edge.parent.document_id, edge.parent.node_id)
            child = (edge.child.document_id, edge.child.node_id)
            if parent in included and child not in included:
                included.add(child)
                changed = True
        if include_relationship_neighbors:
            for edge in revision.relationships:
                source = (edge.source.document_id, edge.source.node_id)
                target = (edge.target.document_id, edge.target.node_id)
                if source in included and target not in included:
                    included.add(target)
                    changed = True
    limits.require("max_nodes", len(included))
    selected_nodes = tuple(node_by_ref[key] for key in sorted(included))
    selected_containment = tuple(edge for edge in revision.containment if (edge.parent.document_id, edge.parent.node_id) in included and (edge.child.document_id, edge.child.node_id) in included)
    selected_relationships = tuple(edge for edge in revision.relationships if (edge.source.document_id, edge.source.node_id) in included and (edge.target.document_id, edge.target.node_id) in included)
    related_records = _related_revision_records(revision, included)
    canonical_records = tuple(
        IRCanonicalSliceRecord(
            path, type(value).__name__, content_digest(value),
            value.to_payload() if hasattr(value, "to_payload") else value,
        )
        for path, value in related_records
    )
    resources = tuple(
        {item.identity_key: item for item in (
            *(resource for node in selected_nodes for resource in node.resource_refs),
            *(resource for _, value in related_records for resource in _iter_resource_refs(value)),
        )}.values()
    )
    resource_digests = tuple(sorted({resource.content_digest for resource in resources if resource.content_digest is not None}))
    shape = {
        "nodes": tuple((node.ref, _node_semantics(node)) for node in selected_nodes),
        "containment": selected_containment, "relationships": selected_relationships,
        "semantic_records": canonical_records,
    }
    refs = tuple(node_by_ref[key].ref for key in sorted(included))
    return IRSubgraphFingerprint(revision.revision_digest, roots, refs, content_digest(shape), (), resource_digests)


def interface_fingerprint(revision: IRRevision, node_ref: IRNodeRef) -> IRInterfaceFingerprint:
    revision, node_ref = IRRevision.coerce(revision, "revision"), IRNodeRef.coerce(node_ref, "node_ref")
    node = next((item for item in revision.nodes if item.identity_key == (node_ref.document_id, node_ref.node_id)), None)
    if node is None or node.interface is None:
        raise IRIntegrityError("interface fingerprint target has no interface capsule")
    return IRInterfaceFingerprint(revision.revision_digest, node_ref, content_digest(node.interface), len(node.interface.payload_resource_refs))


def _revision_record_map(revision: IRRevision) -> dict[str, Any]:
    records: dict[str, Any] = {
        "scene/representation": _node_semantics(revision.scene),
        "schema/manifest": revision.schema_manifest,
    }
    for field_name, values, key_name in (
        ("containment", revision.containment, "edge_id"),
        ("relationships", revision.relationships, "relation_id"),
        ("relationship_policies", revision.relationship_policies, "family"),
        ("fragments", revision.fragments, "fragment_id"),
        ("composition_arcs", revision.composition_arcs, "arc_id"),
        ("prototypes", revision.prototypes, "prototype_id"),
        ("instances", revision.instances, "instance_id"),
        ("source_refs", revision.source_refs, None),
        ("policy_refs", revision.policy_refs, None),
        ("extensions", revision.extensions, None),
        ("spatial_references", revision.spatial_references, "reference_id"),
        ("coordinate_frames", revision.coordinate_frames, "frame_id"),
        ("transform_chains", revision.transform_chains, "chain_id"),
        ("spatial_conversion_receipts", revision.spatial_conversion_receipts, "conversion_id"),
        ("cameras", revision.cameras, None),
        ("lights", revision.lights, None),
        ("spatial_regions", revision.spatial_regions, "region_id"),
        ("materials", revision.materials, "material_id"),
        ("texture_resources", revision.texture_resources, None),
        ("material_bindings", revision.material_bindings, "binding_id"),
        ("color_values", revision.color_values, None),
        ("color_conversion_receipts", revision.color_conversion_receipts, "receipt_id"),
        ("temporal_references", revision.temporal_references, "reference_id"),
        ("temporal_markers", revision.temporal_markers, "marker_id"),
        ("temporal_relations", revision.temporal_relations, "relation_id"),
        ("temporal_samplings", revision.temporal_samplings, "sampling_id"),
        ("temporal_conversion_receipts", revision.temporal_conversion_receipts, "receipt_id"),
        ("motions", revision.motions, "motion_id"),
        ("motion_layers", revision.motion_layers, "layer_id"),
        ("audio", revision.audio, "audio_id"),
        ("audio_bindings", revision.audio_bindings, "binding_id"),
        ("music", revision.music, "music_id"),
        ("narrative_projections", revision.narrative_projections, "projection_id"),
        ("timelines", revision.timelines, "timeline_id"),
        ("sync_relations", revision.sync_relations, "relation_id"),
    ):
        for item in values:
            if key_name is not None:
                item_key = str(getattr(item, key_name))
            elif field_name == "cameras":
                item_key = item.camera_ref.node_id
            elif field_name == "lights":
                item_key = item.light_ref.node_id
            elif field_name == "texture_resources":
                item_key = item.resource.resource_id
            elif field_name == "source_refs" or field_name == "policy_refs":
                item_key = content_digest(item.text)
            elif field_name == "extensions":
                item_key = f"{item.family.family_id}@{item.family.version}"
            else:
                item_key = content_digest(item)
            records[f"{field_name}/{item_key}"] = item
    return records


def _resource_digests(value: Any) -> set[str]:
    if isinstance(value, ResourceRef):
        return {value.content_digest} if value.content_digest is not None else set()
    if is_dataclass(value):
        result: set[str] = set()
        for item in fields(value):
            result.update(_resource_digests(getattr(value, item.name)))
        return result
    if isinstance(value, Mapping):
        result: set[str] = set()
        for item in value.values():
            result.update(_resource_digests(item))
        return result
    if isinstance(value, (tuple, list)):
        result: set[str] = set()
        for item in value:
            result.update(_resource_digests(item))
        return result
    return set()


def _iter_resource_refs(value: Any):
    if isinstance(value, ResourceRef):
        yield value
    elif is_dataclass(value):
        for item in fields(value):
            yield from _iter_resource_refs(getattr(value, item.name))
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_resource_refs(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from _iter_resource_refs(item)


def semantic_delta(previous: IRRevision, current: IRRevision) -> IRSemanticDelta:
    previous, current = IRRevision.coerce(previous, "previous"), IRRevision.coerce(current, "current")
    left = {node.identity_key: node for node in previous.nodes}
    right = {node.identity_key: node for node in current.nodes}
    changes: list[SemanticNodeChange] = []
    invalidated: set[str] = set()
    for key in sorted(set(left) | set(right)):
        before, after = left.get(key), right.get(key)
        if before is None:
            changes.append(SemanticNodeChange(right[key].ref, "ADDED", None, content_digest(_node_semantics(right[key]))))
        elif after is None:
            changes.append(SemanticNodeChange(left[key].ref, "REMOVED", content_digest(_node_semantics(left[key])), None))
        elif content_digest(_node_semantics(before)) != content_digest(_node_semantics(after)):
            changes.append(SemanticNodeChange(after.ref, "CHANGED", content_digest(_node_semantics(before)), content_digest(_node_semantics(after))))
            for resource in (*before.resource_refs, *after.resource_refs):
                if resource.content_digest is not None:
                    invalidated.add(resource.content_digest)
    previous_records, current_records = _revision_record_map(previous), _revision_record_map(current)
    record_changes: list[SemanticRecordChange] = []
    for path in sorted(set(previous_records) | set(current_records)):
        before, after = previous_records.get(path), current_records.get(path)
        before_digest = content_digest(before) if path in previous_records else None
        after_digest = content_digest(after) if path in current_records else None
        if before_digest == after_digest:
            continue
        if before is None:
            kind = "ADDED"
        elif after is None:
            kind = "REMOVED"
        else:
            kind = "CHANGED"
        record_changes.append(SemanticRecordChange(path, kind, before_digest, after_digest))
        invalidated.update(_resource_digests(before))
        invalidated.update(_resource_digests(after))
    delta_digest = content_digest({
        "previous": previous.revision_digest, "current": current.revision_digest,
        "changes": changes, "record_changes": record_changes,
        "invalidated_resources": sorted(invalidated),
    })
    return IRSemanticDelta(previous.revision_digest, current.revision_digest, tuple(changes), tuple(invalidated), delta_digest, tuple(record_changes))


def build_ir_slice(revision: IRRevision, root_refs: tuple[IRNodeRef, ...], *, slice_id: str, limits: IRLimits = DEFAULT_LIMITS) -> MinimumSufficientIRSlice:
    revision = IRRevision.coerce(revision, "revision")
    fingerprint = subgraph_fingerprint(revision, root_refs, limits=limits)
    included_ids = {(item.document_id, item.node_id) for item in fingerprint.included_refs}
    node_map = {(node.ref.document_id, node.ref.node_id): node for node in revision.nodes}
    nodes = tuple(node_map[key] for key in sorted(included_ids))
    containment = tuple(edge for edge in revision.containment if (edge.parent.document_id, edge.parent.node_id) in included_ids and (edge.child.document_id, edge.child.node_id) in included_ids)
    relationships = tuple(edge for edge in revision.relationships if (edge.source.document_id, edge.source.node_id) in included_ids and (edge.target.document_id, edge.target.node_id) in included_ids)
    capsules = tuple((node.ref, node.interface) for node in nodes if node.interface is not None)
    related_records = _related_revision_records(revision, included_ids)
    semantic_records = tuple(
        IRCanonicalSliceRecord(
            path, type(value).__name__, content_digest(value),
            value.to_payload() if hasattr(value, "to_payload") else value,
        )
        for path, value in related_records
    )
    resources_by_identity = {
        resource.identity_key: resource
        for resource in (
            *(resource for node in nodes for resource in node.resource_refs),
            *(resource for _, value in related_records for resource in _iter_resource_refs(value)),
        )
    }
    resources = tuple(resources_by_identity[key] for key in sorted(resources_by_identity, key=repr))
    digest = content_digest({"source": revision.revision_digest, "roots": root_refs, "nodes": nodes, "containment": containment, "relationships": relationships, "capsules": capsules, "semantic_records": semantic_records, "resources": tuple(resource.identity_key for resource in resources)})
    return MinimumSufficientIRSlice(slice_id, revision.revision_digest, root_refs, nodes, containment, relationships, capsules, resources, 0, digest, semantic_records)


def build_temporal_slice(source_digest: str, requested_range: TimeRangeIR, *, slice_id: str, points_by_path: Mapping[str, Any], limits: IRLimits = DEFAULT_LIMITS) -> MinimumSufficientTemporalSlice:
    requested_range = TimeRangeIR.coerce(requested_range, "requested_range")
    included: list[str] = []
    examined = 0
    for path, value in points_by_path.items():
        examined += 1
        limits.require("max_temporal_samples", examined)
        time_point = getattr(value, "time", value)
        if getattr(time_point, "reference_id", None) != requested_range.start.reference_id:
            continue
        ticks = getattr(time_point, "ticks", None)
        if ticks is not None and requested_range.start.ticks <= ticks <= requested_range.end.ticks:
            included.append(require_text(path, "included_paths[]", maximum=1024))
    included_tuple = tuple(sorted(set(included)))
    digest = content_digest({"source": source_digest, "range": requested_range, "paths": included_tuple})
    return MinimumSufficientTemporalSlice(slice_id, source_digest, requested_range, included_tuple, digest)


def build_capability_slice(source_revision_digest: str, profile: TargetRepresentationProfile, needed_refs: tuple[SemanticRef, ...], *, slice_id: str) -> CapabilitySlice:
    profile = TargetRepresentationProfile.coerce(profile, "profile")
    needed = {item.text for item in (SemanticRef.coerce(ref, "needed_refs[]") for ref in needed_refs)}
    declarations = [item for item in profile.manifest.declarations if any(ref.text in needed for ref in item.semantic_refs)]
    refs = tuple(sorted({ref.text: ref for item in declarations for ref in item.semantic_refs if ref.text in needed}.values(), key=lambda item: item.text))
    ids = tuple(sorted(item.capability_id for item in declarations))
    digest = content_digest({"source": source_revision_digest, "profile": profile.profile_id, "capabilities": ids, "refs": refs})
    return CapabilitySlice(slice_id, source_revision_digest, profile.profile_id, ids, refs, digest)


def _node_semantics(node: Any) -> dict[str, Any]:
    payload = node.to_payload()
    payload.pop("display_name", None)
    payload.pop("path_hint", None)
    return payload
