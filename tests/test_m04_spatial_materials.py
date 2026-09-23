"""Unit-safe spatial, camera, lighting, material, and color acceptance tests."""

from __future__ import annotations

import unittest

from iris_intent.identity import RefKind, SemanticRef

from iris_multimodal_ir import (
    CameraIR,
    CameraOpticsIR,
    ColorPipelineRef,
    ColorValueIR,
    CoordinateFrameIR,
    ExternalIdentityRef,
    IRIntegrityError,
    IRAdmissionError,
    IRNodeRef,
    IRSchemaError,
    LightIR,
    LightShapingIR,
    MaterialBindingIR,
    MaterialConnectionIR,
    MaterialGraphIR,
    MaterialIR,
    MaterialNodeIR,
    MaterialPortIR,
    MaterialTerminalIR,
    Physicality,
    ProjectionKind,
    QuantityDimension,
    QuantityIR,
    SchemaFamilyRef,
    ShadowIntentIR,
    SpatialReferenceIR,
    TransformChainIR,
    TransformOperation,
    ColorConversionReceipt,
    convert_quantity,
    content_digest,
    resolve_transform,
)
from tests.m04_support import DOCUMENT_ID, SOURCE


class SpatialSemanticsTests(unittest.TestCase):
    def test_quantity_requires_dimension_and_registered_unit(self):
        self.assertEqual(QuantityIR(1, "m", QuantityDimension.LENGTH).value, 1)
        with self.assertRaises(IRSchemaError):
            QuantityIR(1, "m", QuantityDimension.TIME)
        with self.assertRaises(IRSchemaError):
            QuantityIR(1, "lightyear", QuantityDimension.LENGTH)

    def test_unit_conversion_is_deterministic_and_receipted(self):
        source = QuantityIR(125, "cm", QuantityDimension.LENGTH)
        converted, first = convert_quantity(source, "m", "convert.length")
        _, second = convert_quantity(source, "m", "convert.length")
        self.assertEqual(converted.value, "1.25")
        self.assertEqual(first, second)
        self.assertEqual(first.source_digest, content_digest(source.to_payload()))
        with self.assertRaises(IRIntegrityError):
            convert_quantity(source, "s")

    def test_spatial_reference_pins_axis_and_unit_semantics(self):
        reference = SpatialReferenceIR("world.right", "m", handedness="RIGHT", up_axis="Y", forward_axis="-Z")
        origin = (QuantityIR(0, "m", QuantityDimension.LENGTH),) * 3
        frame = CoordinateFrameIR("frame.world", reference.reference_id, origin=origin)
        self.assertEqual(frame.spatial_reference_id, reference.reference_id)
        with self.assertRaises(IRSchemaError):
            CoordinateFrameIR("frame.implicit", reference.reference_id)

    def test_transform_operation_order_is_semantic_and_resolved_as_derived(self):
        translate = TransformOperation("op.translate", "translate", (1, 0, 0), "m")
        scale = TransformOperation("op.scale", "scale", (2, 2, 2))
        first = TransformChainIR("chain.one", "local", "world", (translate, scale))
        second = TransformChainIR("chain.two", "local", "world", (scale, translate))
        self.assertNotEqual(first.digest, second.digest)
        self.assertNotEqual(resolve_transform(first).matrix4x4, resolve_transform(second).matrix4x4)
        self.assertTrue(resolve_transform(first).derived)
        with self.assertRaises(IRSchemaError):
            TransformOperation("op.bad", "translate", (1, 2, 3))

    def test_camera_physical_optics_round_trip_and_projection_extension(self):
        optics = CameraOpticsIR(
            ProjectionKind.PERSPECTIVE,
            QuantityIR(36, "mm", QuantityDimension.LENGTH), QuantityIR(24, "mm", QuantityDimension.LENGTH),
            focal_length=QuantityIR(50, "mm", QuantityDimension.LENGTH),
            focus_distance=QuantityIR(2, "m", QuantityDimension.LENGTH), f_stop=2.8, depth_of_field_enabled=True,
        )
        camera = CameraIR(IRNodeRef(DOCUMENT_ID, "camera.main"), optics, "frame.world", SOURCE.text)
        self.assertEqual(camera.optics.focal_length.value, 50)
        with self.assertRaises(IRSchemaError):
            CameraOpticsIR(ProjectionKind.FISHEYE, optics.filmback_width, optics.filmback_height)
        fisheye = CameraOpticsIR(ProjectionKind.FISHEYE, optics.filmback_width, optics.filmback_height, extension=SchemaFamilyRef("iris.camera.fisheye", "1"))
        self.assertEqual(fisheye.projection, ProjectionKind.FISHEYE)

    def test_light_intensity_is_typed_and_nonphysical_controls_classified(self):
        physical = LightIR(IRNodeRef(DOCUMENT_ID, "light.key"), "area", QuantityIR(800, "lux", QuantityDimension.ILLUMINANCE), Physicality.PHYSICAL, shadow=ShadowIntentIR(True))
        self.assertEqual(physical.emission.dimension, QuantityDimension.ILLUMINANCE)
        with self.assertRaises(IRSchemaError):
            LightIR(IRNodeRef(DOCUMENT_ID, "light.bad"), "area", QuantityIR(1, "m", QuantityDimension.LENGTH), Physicality.PHYSICAL)
        artistic = LightIR(
            IRNodeRef(DOCUMENT_ID, "light.artistic"), "stylized", QuantityIR(2, "1", QuantityDimension.DIMENSIONLESS),
            Physicality.ARTISTIC, shaping=LightShapingIR("rim_boost", {"strength": 0.4}, Physicality.ARTISTIC),
        )
        self.assertEqual(artistic.shaping.physicality, Physicality.ARTISTIC)


class MaterialAndColorTests(unittest.TestCase):
    def setUp(self):
        self.color_node = MaterialNodeIR(
            "node.color", "constant.color", "1", (MaterialPortIR("out", "output", "color.rgb"),),
            parameters={"value": (0.2, 0.3, 0.4)}, trace_refs=(SOURCE,),
        )
        self.surface_node = MaterialNodeIR(
            "node.surface", "surface.standard", "1",
            (MaterialPortIR("base_color", "input", "color.rgb"), MaterialPortIR("surface", "output", "surface")),
            parameters={}, trace_refs=(SOURCE,),
        )
        self.graph = MaterialGraphIR(
            "graph.surface", (self.color_node, self.surface_node),
            (MaterialConnectionIR("connect.color", "node.color", "out", "node.surface", "base_color"),),
            (MaterialTerminalIR("SURFACE", "node.surface", "surface"),),
        )

    def test_typed_material_ports_and_connections_round_trip(self):
        material = MaterialIR("material.logo", self.graph, (SOURCE,))
        self.assertEqual(material.graph.digest, self.graph.digest)
        self.assertEqual(material.graph.terminals[0].terminal_kind, "SURFACE")

    def test_material_graph_rejects_port_type_mismatch(self):
        wrong_surface = MaterialNodeIR(
            "node.wrong", "surface.standard", "1",
            (MaterialPortIR("base_color", "input", "vector3"), MaterialPortIR("surface", "output", "surface")),
            parameters={},
        )
        with self.assertRaises(IRIntegrityError):
            MaterialGraphIR("graph.bad", (self.color_node, wrong_surface), (MaterialConnectionIR("connect.bad", "node.color", "out", "node.wrong", "base_color"),), (MaterialTerminalIR("SURFACE", "node.wrong", "surface"),))

    def test_material_graph_rejects_cycles_and_missing_required_inputs(self):
        left = MaterialNodeIR("node.left", "mix", "1", (MaterialPortIR("in", "input", "color"), MaterialPortIR("out", "output", "color")), parameters={})
        right = MaterialNodeIR("node.right", "mix", "1", (MaterialPortIR("in", "input", "color"), MaterialPortIR("out", "output", "color")), parameters={})
        cycle = (MaterialConnectionIR("edge.lr", "node.left", "out", "node.right", "in"), MaterialConnectionIR("edge.rl", "node.right", "out", "node.left", "in"))
        with self.assertRaises(IRIntegrityError):
            MaterialGraphIR("graph.cycle", (left, right), cycle, (MaterialTerminalIR("SURFACE", "node.left", "out"),))
        with self.assertRaises(IRIntegrityError):
            MaterialGraphIR("graph.incomplete", (left,), (), (MaterialTerminalIR("SURFACE", "node.left", "out"),))

    def test_material_binding_preview_cannot_satisfy_final_obligation(self):
        with self.assertRaises(IRAdmissionError):
            MaterialBindingIR("bind.preview", "material.logo", IRNodeRef(DOCUMENT_ID, "geometry"), "surface", fidelity_tier="preview", satisfies_final_obligation=True, obligation_refs=(SemanticRef(RefKind.OBLIGATION.value, "final.logo", version="1"),))
        binding = MaterialBindingIR("bind.final", "material.logo", IRNodeRef(DOCUMENT_ID, "geometry"), "surface", fidelity_tier="final", satisfies_final_obligation=True, obligation_refs=(SemanticRef(RefKind.OBLIGATION.value, "final.logo", version="1"),))
        self.assertEqual(binding.fidelity_tier, "final")

    def test_color_semantics_pin_space_encoding_alpha_and_conversion_authority(self):
        color = ColorValueIR((0.1, 0.2, 0.3, 1.0), "linear-srgb", "float32", "opaque", SOURCE)
        self.assertEqual(color.color_space, "linear-srgb")
        with self.assertRaises(IRSchemaError):
            ColorValueIR((0.1, 0.2, 0.3), "linear-srgb", "float32", alpha_mode="")
        with self.assertRaises(IRSchemaError):
            ColorPipelineRef(ExternalIdentityRef("provider.color", "pipeline", "1"))
        pipeline = ColorPipelineRef(ExternalIdentityRef("m38.color_pipeline", "pipeline.standard", "1"))
        receipt = ColorConversionReceipt("color.receipt", content_digest(color), content_digest(color), pipeline, SOURCE, "color-conversion-v1")
        self.assertEqual(receipt.pipeline, pipeline)


if __name__ == "__main__":
    unittest.main()
