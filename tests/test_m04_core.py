"""Identity, schema, graph, composition, resource, and character acceptance tests."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError, replace


from iris_multimodal_ir import (
    AssetDNARef,
    AssetIR,
    AttachmentPortIR,
    CharacterIdentityIR,
    CharacterIR,
    CollectionIR,
    CompositionArc,
    CompositionPrecedence,
    ContainmentEdge,
    CyclePolicy,
    EntityIR,
    ExternalIdentityRef,
    ExtensionValue,
    FacetRef,
    GeometryIR,
    IRAdmissionError,
    IRFragment,
    IRIntegrityError,
    IRLimitError,
    IRLimits,
    IRInterfaceCapsule,
    IRNodeRef,
    IRSchemaError,
    IRValidationProfile,
    IdentityAnchorRef,
    InstanceIR,
    InterfacePort,
    JointIR,
    JointWeight,
    MorphChannelIR,
    NodeKind,
    PersonaDNARef,
    PrototypeIR,
    RelationshipPolicy,
    ResourceLocatorRef,
    ResourceRef,
    SchemaFamilyRef,
    SchemaManifest,
    SchemaUnknownPolicy,
    SemanticRelationship,
    SkeletonIR,
    SkinBindingIR,
    TraceOrigin,
    Traceability,
    compose_fragments,
    content_digest,
    validate_graph,
    validate_revision,
)
from tests.m04_support import DOCUMENT_ID, SOURCE, fixture_revision, trace


def node(ref_id: str, kind: NodeKind = NodeKind.ENTITY, **kwargs):
    cls = {NodeKind.ENTITY: EntityIR, NodeKind.ASSET: AssetIR, NodeKind.CHARACTER: CharacterIR,
           NodeKind.GEOMETRY: GeometryIR, NodeKind.COLLECTION: CollectionIR}[kind]
    return cls(ref=IRNodeRef(DOCUMENT_ID, ref_id), kind=kind, trace=trace(), **kwargs)


class CoreIdentityAndGraphTests(unittest.TestCase):
    def test_node_identity_excludes_name_and_path(self):
        revision_a = fixture_revision(display_name="Scene A", path_hint="a/main")
        revision_b = fixture_revision(display_name="Scene B", path_hint="b/renamed")
        self.assertEqual(revision_a.scene.ref, revision_b.scene.ref)
        self.assertNotEqual(revision_a.scene.display_name, revision_b.scene.display_name)
        self.assertEqual(revision_a.nodes[0].identity_key, revision_b.nodes[0].identity_key)

    def test_resource_locator_is_not_identity(self):
        one = ResourceRef("resource.mesh", "geometry", content_digest=content_digest("mesh"), locator=ResourceLocatorRef("file", "a/mesh.bin"))
        two = ResourceRef("resource.mesh", "geometry", content_digest=content_digest("mesh"), locator=ResourceLocatorRef("https", "https://cdn.example/mesh.bin"))
        self.assertEqual(one.identity_key, two.identity_key)
        self.assertNotEqual(one.locator, two.locator)

    def test_duplicate_node_identity_fails_closed(self):
        first = node("dup")
        with self.assertRaises(IRIntegrityError):
            validate_graph((first, first), (), ())

    def test_containment_cycle_is_rejected(self):
        left, right = node("left"), node("right")
        edges = (ContainmentEdge(left.ref, right.ref, "edge.left-right"), ContainmentEdge(right.ref, left.ref, "edge.right-left"))
        with self.assertRaises(IRIntegrityError):
            validate_graph((left, right), edges)

    def test_custom_graph_depth_limit_is_enforced(self):
        root, middle, leaf = node("depth.root"), node("depth.middle"), node("depth.leaf")
        edges = (
            ContainmentEdge(root.ref, middle.ref, "edge.depth.root-middle"),
            ContainmentEdge(middle.ref, leaf.ref, "edge.depth.middle-leaf"),
        )
        with self.assertRaises(IRLimitError):
            validate_graph((root, middle, leaf), edges, limits=IRLimits(max_depth=1))

    def test_semantic_relationship_cycle_policy_is_family_specific(self):
        left, right = node("rel.left"), node("rel.right")
        relations = (
            SemanticRelationship("rel.one", "peer", left.ref, right.ref, trace()),
            SemanticRelationship("rel.two", "peer", right.ref, left.ref, trace()),
        )
        with self.assertRaises(IRIntegrityError):
            validate_graph((left, right), (), relations, (RelationshipPolicy("peer", CyclePolicy.ACYCLIC),))
        validate_graph((left, right), (), relations, (RelationshipPolicy("peer", CyclePolicy.ALLOW),))

    def test_relationship_family_without_cycle_policy_fails(self):
        left, right = node("rel.a"), node("rel.b")
        relation = SemanticRelationship("rel.unknown", "unregistered", left.ref, right.ref, trace())
        with self.assertRaises(IRAdmissionError):
            validate_graph((left, right), (), (relation,))

    def test_containment_dangling_reference_fails(self):
        left = node("dangling.left")
        right = IRNodeRef(DOCUMENT_ID, "missing.node")
        with self.assertRaises(IRIntegrityError):
            validate_graph((left,), (ContainmentEdge(left.ref, right, "edge.dangling"),))

    def test_provider_observation_cannot_be_admitted_as_canonical_truth(self):
        with self.assertRaises(IRSchemaError):
            Traceability(source_refs=(SOURCE,), origin=TraceOrigin.PROVIDER_OBSERVATION)

    def test_required_node_requires_admitted_trace(self):
        with self.assertRaises(IRAdmissionError):
            EntityIR(ref=IRNodeRef(DOCUMENT_ID, "untraced"), kind=NodeKind.ENTITY, trace=Traceability())

    def test_revision_is_frozen(self):
        revision = fixture_revision()
        with self.assertRaises(FrozenInstanceError):
            revision.revision_id = "changed"

    def test_transform_graph_and_relationship_graph_are_separate_fields(self):
        revision = fixture_revision()
        self.assertTrue(hasattr(revision, "containment"))
        self.assertTrue(hasattr(revision, "relationships"))
        self.assertEqual(len(revision.containment), 1)
        self.assertEqual(len(revision.relationships), 0)

    def test_interface_is_available_without_payload_bytes(self):
        capsule = IRInterfaceCapsule(
            "interface.logo",
            ports=(InterfacePort("input.mark", "input", "mark.logo", semantic_refs=(SOURCE,)),),
            payload_resource_refs=(ResourceRef("payload.logo", "image", content_digest=content_digest("pixels")),),
        )
        self.assertEqual(capsule.ports[0].port_id, "input.mark")
        self.assertEqual(capsule.payload_resource_refs[0].resource_id, "payload.logo")
        self.assertFalse(hasattr(capsule.payload_resource_refs[0], "payload_bytes"))

    def test_required_interface_port_requires_semantic_trace(self):
        with self.assertRaises(IRSchemaError):
            InterfacePort("input.required", "input", "image", semantic_refs=())

    def test_resource_size_and_digest_are_typed(self):
        with self.assertRaises(IRSchemaError):
            ResourceRef("r", "media", expected_size_bytes=-1)
        with self.assertRaises(IRSchemaError):
            ResourceRef("r", "media", content_digest="not-a-digest")

    def test_prototype_is_immutable_and_instance_overrides_are_scoped(self):
        template = node("prototype.entity")
        prototype = PrototypeIR("prototype.logo", (template,), IRInterfaceCapsule("prototype.interface"), ("appearance.color",))
        with self.assertRaises(FrozenInstanceError):
            prototype.prototype_id = "changed"
        instance = InstanceIR("instance.logo", prototype.prototype_id, prototype.digest, IRNodeRef(DOCUMENT_ID, "instance.one"), {"appearance.color": "blue"})
        instance.validate_against(prototype)
        invalid = InstanceIR("instance.bad", prototype.prototype_id, prototype.digest, IRNodeRef(DOCUMENT_ID, "instance.two"), {"identity.name": "other"})
        with self.assertRaises(IRAdmissionError):
            invalid.validate_against(prototype)

    def test_composition_requires_explicit_override_and_order(self):
        base_node = node("shared")
        replacement = node("shared", attributes={"variant": "approved"})
        revision = fixture_revision()
        rev_ref = revision.revision_ref
        first = IRFragment("fragment.base", rev_ref, (base_node.ref,), (SOURCE,), IRInterfaceCapsule("if.base"))
        second = IRFragment("fragment.override", rev_ref, (replacement.ref,), (SOURCE,), IRInterfaceCapsule("if.override"))
        with self.assertRaises(IRIntegrityError):
            compose_fragments((first, second), (), {first.fragment_id: (base_node,), second.fragment_id: (replacement,)})
        arc = CompositionArc("arc.override", first.fragment_id, second.fragment_id, 2, CompositionPrecedence.OVERRIDE, ("shared",))
        result = compose_fragments((first, second), (arc,), {first.fragment_id: (base_node,), second.fragment_id: (replacement,)})
        self.assertEqual(result.ordered_fragment_ids, (first.fragment_id, second.fragment_id))
        self.assertEqual(result.nodes[0].attributes["variant"], "approved")

    def test_m05_dna_refs_are_opaque_namespace_pins(self):
        external = ExternalIdentityRef("m05.asset_dna", "assetdna.logo", "v1", content_digest("opaque"))
        wrapped = AssetDNARef(external)
        self.assertEqual(wrapped.reference, external)
        with self.assertRaises(IRSchemaError):
            AssetDNARef(ExternalIdentityRef("m05.persona_dna", "dna.persona", "v1"))
        persona = PersonaDNARef(ExternalIdentityRef("m05.persona_dna", "dna.persona", "v1"))
        anchor = IdentityAnchorRef(ExternalIdentityRef("m05.identity", "anchor.character", "v1"))
        character = node("character.dna", NodeKind.CHARACTER, character_identity=CharacterIdentityIR(IRNodeRef(DOCUMENT_ID, "character.dna"), anchor, wrapped, persona))
        self.assertEqual(character.character_identity.asset_dna.reference.authority, "m05.asset_dna")

    def test_skeleton_parent_and_cycle_validation(self):
        valid = SkeletonIR("skeleton.one", ("root",), (JointIR("root", "root"), JointIR("hand", "hand", "root")), "world")
        self.assertEqual(len(valid.joints), 2)
        with self.assertRaises(IRIntegrityError):
            SkeletonIR("skeleton.cycle", (), (JointIR("a", "a", "b"), JointIR("b", "b", "a")), "world")

    def test_skin_weights_sum_to_one_and_reference_existing_joints(self):
        skeleton = SkeletonIR("skeleton.skin", ("root",), (JointIR("root", "root"), JointIR("hand", "hand", "root")), "world")
        binding = SkinBindingIR("skin.one", skeleton.skeleton_id, IRNodeRef(DOCUMENT_ID, "geometry"), {"v0": (JointWeight("root", 0.25), JointWeight("hand", 0.75))})
        binding.validate_against(skeleton)
        with self.assertRaises(IRIntegrityError):
            SkinBindingIR("skin.bad", skeleton.skeleton_id, IRNodeRef(DOCUMENT_ID, "geometry"), {"v0": (JointWeight("root", 0.2),)})

    def test_morph_and_attachment_ports_are_typed(self):
        morph = MorphChannelIR("morph.smile", "face.expression.smile", IRNodeRef(DOCUMENT_ID, "geometry"), -1, 1, 0)
        port = AttachmentPortIR("attach.hand", IRNodeRef(DOCUMENT_ID, "character"), "prop.handheld", "many")
        self.assertEqual((morph.minimum, morph.maximum), (-1.0, 1.0))
        self.assertEqual(port.cardinality, "many")


class SchemaAndSerializationBoundaryTests(unittest.TestCase):
    def test_schema_family_and_version_are_explicit(self):
        family = SchemaFamilyRef("iris.scene", "2.1")
        self.assertEqual(family.version, "2.1")
        with self.assertRaises(IRSchemaError):
            SchemaFamilyRef("iris.scene", "")

    def test_unknown_mandatory_facet_fails_closed(self):
        manifest = SchemaManifest(facets=(FacetRef("vendor.facet", "1", mandatory=True),))
        with self.assertRaises(IRAdmissionError):
            manifest.validate_registered(facets=set(), dialects=set())

    def test_unknown_optional_facet_preserved_only_when_explicitly_allowed(self):
        manifest = SchemaManifest(facets=(FacetRef("vendor.optional", "1", preserve_opaque=True),), unknown_policy=SchemaUnknownPolicy.PRESERVE_OPTIONAL_OPAQUE)
        manifest.validate_registered(facets=set(), dialects=set())
        strict = SchemaManifest(facets=(FacetRef("vendor.optional", "1", preserve_opaque=True),))
        with self.assertRaises(IRAdmissionError):
            strict.validate_registered(facets=set(), dialects=set())

    def test_unknown_mandatory_extension_fails_closed_during_validation(self):
        extension = ExtensionValue(SchemaFamilyRef("vendor.extension", "1"), {"payload": "opaque"}, mandatory=True)
        revision = replace(fixture_revision(), extensions=(extension,))
        report = validate_revision(revision, IRValidationProfile("strict.extensions", "1"))
        self.assertFalse(report.valid)
        self.assertIn("UNKNOWN_EXTENSION", {finding.code for finding in report.findings})

    def test_unknown_optional_extension_requires_explicit_opaque_policy(self):
        extension = ExtensionValue(
            SchemaFamilyRef("vendor.optional.extension", "1"),
            {"payload": "opaque"},
            preserve_opaque=True,
        )
        revision = replace(fixture_revision(), extensions=(extension,))
        strict = validate_revision(revision, IRValidationProfile("strict.extensions", "1"))
        self.assertFalse(strict.valid)
        permissive = validate_revision(
            revision,
            IRValidationProfile(
                "opaque.extensions",
                "1",
                unknown_policy=SchemaUnknownPolicy.PRESERVE_OPTIONAL_OPAQUE,
            ),
        )
        self.assertTrue(permissive.valid)
        self.assertIn("UNKNOWN_EXTENSION", {finding.code for finding in permissive.findings})

    def test_unknown_mandatory_schema_facet_and_extension_fail_closed(self):
        future_schema = replace(
            fixture_revision(),
            schema_manifest=SchemaManifest(core_schema_version="future-core-v2"),
        )
        self.assertFalse(validate_revision(future_schema).valid)

        mandatory_facet = replace(
            fixture_revision(),
            schema_manifest=SchemaManifest(facets=(FacetRef("vendor.required", "1", mandatory=True),)),
        )
        self.assertFalse(validate_revision(mandatory_facet).valid)

        mandatory_extension = replace(
            fixture_revision(),
            extensions=(ExtensionValue(SchemaFamilyRef("vendor.required.extension", "1"), {"value": "opaque"}, mandatory=True),),
        )
        self.assertFalse(validate_revision(mandatory_extension).valid)

    def test_optional_unknown_facet_and_extension_require_explicit_opaque_policy(self):
        revision = replace(
            fixture_revision(),
            schema_manifest=SchemaManifest(
                facets=(FacetRef("vendor.optional", "1", preserve_opaque=True),),
                unknown_policy=SchemaUnknownPolicy.PRESERVE_OPTIONAL_OPAQUE,
            ),
            extensions=(
                ExtensionValue(
                    SchemaFamilyRef("vendor.optional.extension", "1"),
                    {"value": "opaque"},
                    preserve_opaque=True,
                ),
            ),
        )
        strict = validate_revision(revision, IRValidationProfile("strict.opaque", "1"))
        self.assertFalse(strict.valid)
        permissive = validate_revision(
            revision,
            IRValidationProfile(
                "permissive.opaque",
                "1",
                unknown_policy=SchemaUnknownPolicy.PRESERVE_OPTIONAL_OPAQUE,
            ),
        )
        self.assertTrue(permissive.valid)
        self.assertEqual(
            {finding.code for finding in permissive.findings},
            {"UNKNOWN_FACET", "UNKNOWN_EXTENSION"},
        )



if __name__ == "__main__":
    unittest.main()
