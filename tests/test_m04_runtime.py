"""Transport, multimodal witness, context, migration, and boundary acceptance tests."""

from __future__ import annotations

import ast
import sys
import unittest
from dataclasses import fields, replace
from fractions import Fraction
from pathlib import Path

import iris_multimodal_ir as M04

from iris_multimodal_ir import (
    AnimationCurveIR,
    AudioClipBindingIR,
    AudioIR,
    AudioSpatialIR,
    CameraIR,
    CameraOpticsIR,
    ColorValueIR,
    ComparisonTolerance,
    CurveKeyIR,
    DurationIR,
    EquivalenceKind,
    ExternalIdentityRef,
    IRDocumentEnvelope,
    IRInterfaceCapsule,
    IRLimits,
    IRMigrationPlan,
    IRNodeRef,
    IRRevision,
    IREquivalenceProfile,
    IRLimitError,
    InterfacePort,
    LightIR,
    MaterialBindingIR,
    MaterialConnectionIR,
    MaterialGraphIR,
    MaterialIR,
    MaterialNodeIR,
    MaterialPortIR,
    MaterialTerminalIR,
    MotionChannelIR,
    MotionClipIR,
    MotionIR,
    MotionLayerIR,
    MotionTargetRef,
    MusicEventIR,
    MusicEventKind,
    MusicIR,
    MusicSectionIR,
    MusicTempoIR,
    NarrativeCueIR,
    NarrativeProjectionIR,
    NodeKind,
    Physicality,
    ProjectionKind,
    QuantityDimension,
    QuantityIR,
    ResourceRef,
    SchemaCompatibilityDeclaration,
    SchemaFamilyRef,
    SchemaManifest,
    SchemaMigrationAction,
    SemanticLoweringRule,
    SemanticLossClass,
    RepresentationState,
    SequenceRepresentationIR,
    ShotRepresentationIR,
    SyncKind,
    SyncRelationIR,
    TemporalLayer,
    TemporalMarkerIR,
    TemporalReferenceIR,
    TextureResourceIR,
    TimePointIR,
    TimeRangeIR,
    TimelineIR,
    TimelineItemIR,
    TimelineTrackIR,
    TransformChainIR,
    TransformOperation,
    build_ir_slice,
    build_round_trip_contract,
    canonical_digest,
    content_digest,
    deserialize_envelope,
    interface_fingerprint,
    migrate_revision,
    semantic_delta,
    serialize_envelope,
    structural_fingerprint,
    subgraph_fingerprint,
    validate_revision,
    verify_round_trip,
)
from tests.m04_support import DOCUMENT_ID, POLICY, SOURCE, fixture_revision, m03_bundle, trace
from examples.m04_synthetic_profiles import run_synthetic_profiles


def multimodal_revision() -> IRRevision:
    revision = fixture_revision()
    entity_ref = IRNodeRef(DOCUMENT_ID, "fixture.entity")
    geometry_ref = IRNodeRef(DOCUMENT_ID, "fixture.geometry")
    camera_ref = IRNodeRef(DOCUMENT_ID, "camera.primary")
    light_ref = IRNodeRef(DOCUMENT_ID, "light.key")
    time_ref = TemporalReferenceIR("time.base", Fraction(24), "production.zero")

    camera_node = M04.EntityIR(ref=camera_ref, kind=NodeKind.ENTITY, trace=trace())
    light_node = M04.EntityIR(ref=light_ref, kind=NodeKind.ENTITY, trace=trace())
    filmback = QuantityIR(36, "mm", QuantityDimension.LENGTH)
    filmback_height = QuantityIR(24, "mm", QuantityDimension.LENGTH)
    camera_optics = CameraOpticsIR(
        ProjectionKind.PERSPECTIVE, filmback, filmback_height,
        focal_length=QuantityIR(50, "mm", QuantityDimension.LENGTH),
        focus_distance=QuantityIR(2, "m", QuantityDimension.LENGTH), f_stop=2.8,
        depth_of_field_enabled=True,
    )
    camera = CameraIR(camera_ref, camera_optics, "world", SOURCE.text)
    light = LightIR(
        light_ref, "area", QuantityIR(800, "lux", QuantityDimension.ILLUMINANCE),
        Physicality.PHYSICAL,
    )

    texture = TextureResourceIR(
        ResourceRef("texture.albedo", "texture", content_digest("albedo")),
        "linear-srgb", "float32", ("r", "g", "b"), "opaque",
    )
    color_node = MaterialNodeIR(
        "node.color", "constant.color", "1", (MaterialPortIR("out", "output", "color.rgb"),),
        parameters={"value": (0.2, 0.3, 0.4)}, texture_refs=(texture,), trace_refs=(SOURCE,),
    )
    surface_node = MaterialNodeIR(
        "node.surface", "surface.standard", "1",
        (MaterialPortIR("base_color", "input", "color.rgb"), MaterialPortIR("surface", "output", "surface")),
        parameters={"roughness": 0.4}, trace_refs=(SOURCE,),
    )
    material_graph = MaterialGraphIR(
        "graph.surface", (color_node, surface_node),
        (MaterialConnectionIR("connect.color", "node.color", "out", "node.surface", "base_color"),),
        (MaterialTerminalIR("SURFACE", "node.surface", "surface"),),
    )
    material = MaterialIR("material.surface", material_graph, (SOURCE,))
    material_binding = MaterialBindingIR("binding.geometry", material.material_id, geometry_ref, "surface")
    color = ColorValueIR((0.1, 0.2, 0.3, 1.0), "linear-srgb", "float32", "opaque", SOURCE)

    t0 = TimePointIR(time_ref.reference_id, Fraction(0), TemporalLayer.AUTHORED)
    t4 = TimePointIR(time_ref.reference_id, Fraction(4), TemporalLayer.AUTHORED)
    t8 = TimePointIR(time_ref.reference_id, Fraction(8), TemporalLayer.AUTHORED)
    clip_range = TimeRangeIR(t0, t8)
    curve = AnimationCurveIR("curve.position", (CurveKeyIR(t0, 0.0), CurveKeyIR(t8, 1.0)), "scalar")
    channel = MotionChannelIR("channel.position", MotionTargetRef(entity_ref, "transform.translation.x", "scalar"), curve=curve, semantic_refs=(SOURCE,))
    motion = MotionIR("motion.walk", (channel,), (SOURCE,))
    motion_layer = MotionLayerIR("layer.body", 0, (MotionClipIR("clip.walk", clip_range, motion.motion_id),), "replace")

    audio_resource = ResourceRef("audio.dialogue", "audio", content_digest("dialogue"), expected_size_bytes=24)
    audio = AudioIR("audio.line", "dialogue", audio_resource, "audio/wav", AudioSpatialIR("binaural", revision.coordinate_frames[0], ("left", "right")), trace_refs=(SOURCE,))
    audio_binding = AudioClipBindingIR("audio.binding", audio.audio_id, clip_range, Fraction(0), 1.0)
    music = MusicIR(
        "music.score", time_ref.reference_id,
        (MusicEventIR("music.texture", MusicEventKind.TEXTURE, TimePointIR(time_ref.reference_id, Fraction(0), TemporalLayer.SEMANTIC), DurationIR(time_ref.reference_id, Fraction(8)), "pad"),),
        (MusicTempoIR(TimePointIR(time_ref.reference_id, Fraction(0), TemporalLayer.SEMANTIC), Fraction(93, 2)),),
        None,
        (MusicSectionIR("section.ambient", "ambient", TimeRangeIR(TimePointIR(time_ref.reference_id, Fraction(0), TemporalLayer.SEMANTIC), TimePointIR(time_ref.reference_id, Fraction(8), TemporalLayer.SEMANTIC)), ("pad",)),),
        ("pad",), None,
    )
    canon_ref = ExternalIdentityRef("m43.canon", "world.logo", "1")
    cue = NarrativeCueIR("cue.title", clip_range, "caption", "Local description", canon_ref, True, (SOURCE,))
    narrative = NarrativeProjectionIR("narrative.local", (cue,), (canon_ref,))
    timeline_item = TimelineItemIR("timeline.camera", "camera", camera_ref, clip_range, 0)
    timeline = TimelineIR(
        "timeline.main", time_ref.reference_id,
        (TimelineTrackIR("track.picture", "picture", (timeline_item,), 0),), clip_range,
        (SequenceRepresentationIR("sequence.main", (ShotRepresentationIR("shot.one", clip_range, revision.scene.ref, camera_ref, (SOURCE,)),), time_ref.reference_id),),
        narrative,
    )
    sync = SyncRelationIR("sync.av", SyncKind.AUDIO_VISUAL, t4, t4, Fraction(0), Fraction(1), True, (SOURCE,))

    chain = TransformChainIR("transform.logo", "local", "world", (TransformOperation("op.translate", "translate", (1, 0, 0), "m"),))
    local_origin = tuple(QuantityIR(0, "m", QuantityDimension.LENGTH) for _ in range(3))
    local_frame = M04.CoordinateFrameIR("local", "world", "world", local_origin)
    entity = replace(revision.nodes[0], transform_chain_id=chain.chain_id)
    nodes = tuple(entity if item.ref == entity_ref else item for item in revision.nodes) + (camera_node, light_node)
    return replace(
        revision, revision_id="fixture.multimodal", nodes=nodes,
        coordinate_frames=(*revision.coordinate_frames, local_frame), transform_chains=(chain,),
        cameras=(camera,), lights=(light,), materials=(material,), texture_resources=(texture,),
        material_bindings=(material_binding,), color_values=(color,), temporal_references=(time_ref,),
        motions=(motion,), motion_layers=(motion_layer,), audio=(audio,), audio_bindings=(audio_binding,),
        music=(music,), narrative_projections=(narrative,), timelines=(timeline,), sync_relations=(sync,),
    )


class RuntimeAndTransportAcceptanceTests(unittest.TestCase):
    def test_canonical_envelope_round_trips_every_integrated_modality(self):
        revision = multimodal_revision()
        envelope = IRDocumentEnvelope(M04.MultimodalIRDocument(DOCUMENT_ID, (revision,)))
        encoded = serialize_envelope(envelope)
        decoded = deserialize_envelope(encoded)
        self.assertEqual(serialize_envelope(decoded), encoded)
        self.assertEqual(decoded.document.head.revision_digest, revision.revision_digest)
        self.assertEqual(canonical_digest(decoded.document.head), revision.revision_digest)

    def test_deserialize_enforces_caller_graph_limits(self):
        revision = multimodal_revision()
        envelope = IRDocumentEnvelope(M04.MultimodalIRDocument(DOCUMENT_ID, (revision,)))
        encoded = serialize_envelope(envelope)
        with self.assertRaises(IRLimitError):
            deserialize_envelope(encoded, limits=IRLimits(max_nodes=1))

    def test_tolerant_round_trip_is_unit_aware_for_camera_lengths(self):
        revision = multimodal_revision()
        profile = IREquivalenceProfile(
            "tolerant.camera.length",
            EquivalenceKind.TOLERANT,
            (ComparisonTolerance("cameras/camera.primary", 0.2, "LENGTH", "mm"),),
        )
        contract = build_round_trip_contract(
            revision,
            profile,
            contract_id="roundtrip.tolerant.camera",
            adapter_ref=ExternalIdentityRef("m04.adapter_identity", "adapter.fixture", "1"),
        )
        changed_optics = replace(
            revision.cameras[0].optics,
            focal_length=QuantityIR(5.01, "cm", QuantityDimension.LENGTH),
        )
        adapted = replace(revision, cameras=(replace(revision.cameras[0], optics=changed_optics),))
        receipt = verify_round_trip(contract, adapted, receipt_id="roundtrip.tolerant.camera.result")
        self.assertTrue(receipt.semantic_match)
        self.assertEqual({item.classification for item in receipt.differences}, {"TOLERATED"})

    def test_tolerant_round_trip_is_color_space_and_encoding_aware(self):
        revision = multimodal_revision()
        profile = IREquivalenceProfile(
            "tolerant.color",
            EquivalenceKind.TOLERANT,
            (ComparisonTolerance("color_values/index.0", 0.02, "COLOR", "float32", color_space="linear-srgb"),),
        )
        contract = build_round_trip_contract(
            revision,
            profile,
            contract_id="roundtrip.tolerant.color",
            adapter_ref=ExternalIdentityRef("m04.adapter_identity", "adapter.fixture", "1"),
        )
        source_color = revision.color_values[0]
        adapted_color = replace(source_color, components=(0.11, 0.19, 0.3, 1.0))
        receipt = verify_round_trip(
            contract,
            replace(revision, color_values=(adapted_color,)),
            receipt_id="roundtrip.tolerant.color.result",
        )
        self.assertTrue(receipt.semantic_match)
        self.assertEqual({item.classification for item in receipt.differences}, {"TOLERATED"})
        wrong_space = replace(source_color, color_space="display-p3")
        rejected = verify_round_trip(
            contract,
            replace(revision, color_values=(wrong_space,)),
            receipt_id="roundtrip.tolerant.color.wrong-space",
        )
        self.assertFalse(rejected.semantic_match)

    def test_tolerant_round_trip_is_time_reference_aware(self):
        revision = multimodal_revision()
        marker = TemporalMarkerIR(
            "marker.tolerant",
            TimePointIR("time.base", Fraction(2), TemporalLayer.AUTHORED),
            "beat",
        )
        revision = replace(revision, temporal_markers=(marker,))
        profile = IREquivalenceProfile(
            "tolerant.time",
            EquivalenceKind.TOLERANT,
            (ComparisonTolerance("temporal_markers/marker.tolerant", 0.5, "TIME", "time.base"),),
        )
        contract = build_round_trip_contract(
            revision,
            profile,
            contract_id="roundtrip.tolerant.time",
            adapter_ref=ExternalIdentityRef("m04.adapter_identity", "adapter.fixture", "1"),
        )
        adapted_marker = replace(
            marker,
            time=TimePointIR("time.base", Fraction(9, 4), TemporalLayer.AUTHORED),
        )
        receipt = verify_round_trip(
            contract,
            replace(revision, temporal_markers=(adapted_marker,)),
            receipt_id="roundtrip.tolerant.time.result",
        )
        self.assertTrue(receipt.semantic_match)
        self.assertEqual({item.classification for item in receipt.differences}, {"TOLERATED"})
        wrong_reference = replace(
            marker,
            time=TimePointIR("time.other", Fraction(9, 4), TemporalLayer.AUTHORED),
        )
        with self.assertRaises(M04.IRIntegrityError):
            replace(revision, temporal_markers=(wrong_reference,))

    def test_semantic_witnesses_detect_transform_camera_material_time_and_sync_loss(self):
        revision = multimodal_revision()
        profile = IREquivalenceProfile("exact", EquivalenceKind.EXACT)
        contract = build_round_trip_contract(
            revision, profile, contract_id="roundtrip.logo",
            adapter_ref=ExternalIdentityRef("m04.adapter_identity", "adapter.fixture", "1"),
        )
        changed_transform = replace(revision.transform_chains[0].operations[0], values=(2, 0, 0))
        variants = (
            (replace(revision, transform_chains=(replace(revision.transform_chains[0], operations=(changed_transform,)),)), "transform_chains/transform.logo"),
            (replace(revision, cameras=(replace(revision.cameras[0], optics=replace(revision.cameras[0].optics, f_stop=4.0)),)), "cameras/camera.primary"),
            (replace(revision, materials=(replace(revision.materials[0], extensions=("material.extension.v1",)),)), "materials/material.surface"),
            (replace(revision, temporal_references=(replace(revision.temporal_references[0], ticks_per_second=Fraction(25)),)), "temporal_references/time.base"),
            (replace(revision, sync_relations=(replace(revision.sync_relations[0], tolerance=Fraction(2)),)), "sync_relations/sync.av"),
        )
        for index, (adapted, expected_path) in enumerate(variants):
            receipt = verify_round_trip(contract, adapted, receipt_id=f"roundtrip.result.{index}")
            self.assertFalse(receipt.semantic_match)
            self.assertFalse(receipt.independently_qualified)
            self.assertIn(expected_path, {item.path for item in receipt.differences})

    def test_adapter_cannot_claim_independent_qualification(self):
        revision = fixture_revision()
        with self.assertRaises(M04.IRAdmissionError):
            M04.RoundTripReceipt(
                "receipt.false", content_digest("contract"), revision.revision_digest,
                revision.revision_digest, (), True, True,
            )

    def test_fingerprints_and_deltas_include_non_node_semantics(self):
        revision = multimodal_revision()
        changed = replace(revision, cameras=(replace(revision.cameras[0], optics=replace(revision.cameras[0].optics, f_stop=4.0)),))
        delta = semantic_delta(revision, changed)
        self.assertIn("cameras/camera.primary", {item.path for item in delta.record_changes})
        self.assertEqual(delta.record_changes[0].change, "CHANGED")
        self.assertNotEqual(structural_fingerprint(revision).source_revision_digest, structural_fingerprint(changed).source_revision_digest)
        self.assertNotEqual(subgraph_fingerprint(revision, (IRNodeRef(DOCUMENT_ID, "camera.primary"),)).digest,
                            subgraph_fingerprint(changed, (IRNodeRef(DOCUMENT_ID, "camera.primary"),)).digest)
        sliced = build_ir_slice(revision, (IRNodeRef(DOCUMENT_ID, "camera.primary"),), slice_id="slice.camera")
        paths = {item.path for item in sliced.semantic_records}
        self.assertIn("cameras/camera.primary", paths)
        self.assertIn("timelines/timeline.main", paths)
        self.assertEqual(sliced.loaded_payload_bytes, 0)
        decoded = M04.MinimumSufficientIRSlice.coerce(sliced.to_payload(), "slice")
        self.assertEqual(decoded.slice_digest, sliced.slice_digest)

    def test_minimum_slice_and_temporal_slice_are_bounded_and_payload_free(self):
        revision = fixture_revision()
        sliced = build_ir_slice(revision, (revision.nodes[0].ref,), slice_id="slice.logo")
        self.assertEqual(len(sliced.nodes), 2)
        self.assertEqual(sliced.loaded_payload_bytes, 0)
        with self.assertRaises(IRLimitError):
            subgraph_fingerprint(revision, (revision.nodes[0].ref,), limits=IRLimits(max_nodes=1))
        temporal = M04.build_temporal_slice(
            content_digest("time.series"),
            TimeRangeIR(TimePointIR("time.test", Fraction(0), TemporalLayer.AUTHORED), TimePointIR("time.test", Fraction(4), TemporalLayer.AUTHORED)),
            slice_id="slice.time",
            points_by_path={
                "motion/key.0": TimePointIR("time.test", Fraction(0), TemporalLayer.AUTHORED),
                "motion/key.8": TimePointIR("time.test", Fraction(8), TemporalLayer.AUTHORED),
            },
        )
        self.assertEqual(temporal.included_paths, ("motion/key.0",))

    def test_interface_fingerprint_reads_ports_without_loading_resources(self):
        revision = fixture_revision()
        entity = revision.nodes[0]
        capsule = IRInterfaceCapsule(
            "interface.logo", ports=(InterfacePort("input.logo", "input", "image", semantic_refs=(SOURCE,)),),
            payload_resource_refs=(ResourceRef("payload.logo", "image", content_digest("pixels")),),
        )
        changed = replace(revision, nodes=(replace(entity, interface=capsule), *revision.nodes[1:]))
        fingerprint = interface_fingerprint(changed, entity.ref)
        self.assertEqual(fingerprint.payload_resource_count, 1)

    def test_m03_lowering_receipt_preserves_upstream_rules_without_authority_expansion(self):
        revision = fixture_revision()
        bundle = m03_bundle()
        original_digest = content_digest(bundle.to_payload())
        mapping = M04.M03ToM04Mapping("fixture.create", (revision.nodes[0].ref,), ("fixture.lossless",))
        receipt = M04.lower_m03_bundle(bundle, revision, (mapping,), receipt_id="lower.fixture")
        self.assertEqual(content_digest(bundle.to_payload()), original_digest)
        self.assertEqual(receipt.m03_bundle_id, bundle.bundle_id)
        self.assertTrue(any(item.loss_class is SemanticLossClass.LOSSLESS_REQUIRED for item in receipt.rules))
        untraced_node = replace(revision.nodes[0], semantic_refs=())
        untraced_revision = replace(revision, nodes=(untraced_node, *revision.nodes[1:]))
        with self.assertRaises(M04.IRAdmissionError):
            M04.lower_m03_bundle(bundle, untraced_revision, (mapping,), receipt_id="lower.untraced")
        with self.assertRaises(M04.IRAdmissionError):
            SemanticLoweringRule("lossless.bad", SOURCE, RepresentationState.BOUNDED, SemanticLossClass.LOSSLESS_REQUIRED)

    def test_migration_creates_new_revision_and_receipt_verifies_the_applied_actions(self):
        source = fixture_revision()
        schema_v1 = SchemaFamilyRef("iris.multimodal.scene", "1")
        schema_v2 = SchemaFamilyRef("iris.multimodal.scene", "2")
        action = SchemaMigrationAction("rename.purpose", "RENAME_NODE_ATTRIBUTE", "purpose", "intent.purpose", POLICY)
        compatibility = SchemaCompatibilityDeclaration("scene.migrate", schema_v1, schema_v2, False, "migration.1", True)
        plan = IRMigrationPlan("migration.logo", source.revision_ref, schema_v1, schema_v2, SchemaManifest(), compatibility, (action,))
        result, receipt = migrate_revision(source, plan, new_revision_id="fixture.revision.v2", receipt_id="migration.receipt")
        self.assertNotEqual(source.revision_ref, result.revision_ref)
        self.assertEqual(source.nodes[0].attributes["purpose"], "logo")
        self.assertTrue(receipt.verify(source, result, plan))
        forged = replace(result, nodes=(replace(result.nodes[0], attributes={"purpose": "forged"}), *result.nodes[1:]))
        self.assertFalse(receipt.verify(source, forged, plan))

    def test_governance_authority_fields_and_closed_import_boundary(self):
        revision_fields = {item.name for item in fields(IRRevision)}
        self.assertFalse(revision_fields & {"execution_plan", "quality_class", "quality_score", "release_authorized", "provider_workflow", "provider_model"})
        self.assertFalse(M04.IRReleaseReadinessReport.__dataclass_fields__["release_authorized"].default)
        source_root = Path(M04.__file__).resolve().parent
        allowed_roots = set(sys.stdlib_module_names) | {"iris_intent", "iris_multimodal_ir"}
        forbidden = {"socket", "urllib", "http", "requests", "subprocess", "sqlite3", "sqlalchemy", "blender", "maya", "comfyui", "torch", "ctypes"}
        for path in source_root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots = {alias.name.split(".")[0] for alias in node.names}
                    self.assertFalse(roots & forbidden, f"forbidden import in {path.name}: {roots & forbidden}")
                    self.assertLessEqual(roots, allowed_roots, f"unapproved import in {path.name}: {roots - allowed_roots}")
                elif isinstance(node, ast.ImportFrom) and node.module:
                    root = node.module.split(".")[0]
                    self.assertNotIn(root, forbidden, f"forbidden import in {path.name}: {root}")
                    if node.level == 0:
                        self.assertIn(root, allowed_roots, f"unapproved import in {path.name}: {root}")
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, {"eval", "exec", "__import__"}, f"dynamic execution/import in {path.name}")
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "os":
                        self.assertNotIn(node.func.attr, {"system", "popen", "spawnl", "spawnv", "execv", "execve"}, f"process execution in {path.name}")

    def test_public_surface_is_unique_complete_and_uses_typed_failures(self):
        self.assertEqual(len(M04.__all__), len(set(M04.__all__)))
        self.assertTrue(all(hasattr(M04, name) for name in M04.__all__))
        self.assertIsInstance(validate_revision(fixture_revision()).valid, bool)
        with self.assertRaises(M04.IRSchemaError):
            M04.ResourceRef("invalid", "media", content_digest="not-a-digest")

    def test_seven_synthetic_domains_share_one_kernel_and_surface(self):
        report = run_synthetic_profiles()
        self.assertEqual(len(report["domains"]), 7)
        self.assertEqual(report["profileSpecificKernelBranches"], 0)
        self.assertEqual(len({item["validation"] for item in report["domains"]}), 1)
        self.assertEqual(len({item["roundTrip"] for item in report["domains"]}), 1)
        self.assertEqual(len({item["canonicalEnvelopeDigest"] for item in report["domains"]}), 7)


if __name__ == "__main__":
    unittest.main()
