"""One deterministic regression test for each frozen M04 hard invariant."""

from __future__ import annotations

import importlib
import unittest
from dataclasses import FrozenInstanceError, fields, replace

import iris_multimodal_ir as M04
from iris_intent.identity import RefKind, SemanticRef

from iris_multimodal_ir import (
    CapabilityDeclaration,
    CapabilitySupport,
    ComparisonTolerance,
    EquivalenceKind,
    IRIntegrityError,
    IRRevision,
    IRSchemaError,
    RepresentationCapabilityManifest,
    RequirementLevel,
    SchemaCompatibilityDeclaration,
    SchemaFamilyRef,
    SemanticCapabilityDebt,
    SemanticLoweringRule,
    SemanticLossClass,
    SupportState,
    TargetRepresentationProfile,
    content_digest,
)
from iris_multimodal_ir.enums import RepresentationState
from iris_multimodal_ir.invariants import FROZEN_INVARIANT_PROOFS, validate_invariant_proof_index
from tests.m04_support import POLICY, SOURCE, fixture_revision, trace


_CASE_BY_TARGET = {
    "canonical_identity": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_node_identity_excludes_name_and_path"),
    "provider_neutral_refs": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_resource_locator_is_not_identity"),
    "display_metadata_excluded": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_node_identity_excludes_name_and_path"),
    "immutable_revision": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_revision_is_frozen"),
    "authority_m02": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_governance_authority_fields_and_closed_import_boundary"),
    "no_parallel_vcs": ("tests.test_m04_invariants", "FrozenInvariantProofTests", "_prove_no_parallel_vcs"),
    "dual_graph": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_transform_graph_and_relationship_graph_are_separate_fields"),
    "acyclic_containment": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_containment_cycle_is_rejected"),
    "typed_relationship_policy": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_semantic_relationship_cycle_policy_is_family_specific"),
    "traceability": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_required_node_requires_admitted_trace"),
    "no_observation_promotion": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_provider_observation_cannot_be_admitted_as_canonical_truth"),
    "m01_obligation_ref": ("tests.test_m04_invariants", "FrozenInvariantProofTests", "_prove_m01_obligation_ref"),
    "no_quality_authority": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_governance_authority_fields_and_closed_import_boundary"),
    "quality_class_immutable": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_governance_authority_fields_and_closed_import_boundary"),
    "m03_constraint_immutable": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_m03_lowering_receipt_preserves_upstream_rules_without_authority_expansion"),
    "mandatory_semantics_preserved": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_m03_lowering_receipt_preserves_upstream_rules_without_authority_expansion"),
    "lossless_blocks": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_m03_lowering_receipt_preserves_upstream_rules_without_authority_expansion"),
    "bounded_loss_authorized": ("tests.test_m04_invariants", "FrozenInvariantProofTests", "_prove_bounded_loss_authorized"),
    "capability_read_only": ("tests.test_m04_invariants", "FrozenInvariantProofTests", "_prove_capability_read_only"),
    "m16_boundary": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_governance_authority_fields_and_closed_import_boundary"),
    "provider_neutral_plan": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_governance_authority_fields_and_closed_import_boundary"),
    "m05_opaque_dna": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_m05_dna_refs_are_opaque_namespace_pins"),
    "identity_opaque": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_m05_dna_refs_are_opaque_namespace_pins"),
    "no_storage_backend": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_governance_authority_fields_and_closed_import_boundary"),
    "location_not_identity": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_resource_locator_is_not_identity"),
    "deferred_resource": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_interface_is_available_without_payload_bytes"),
    "interface_without_payload": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_interface_is_available_without_payload_bytes"),
    "immutable_prototype": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_prototype_is_immutable_and_instance_overrides_are_scoped"),
    "scoped_instance_override": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_prototype_is_immutable_and_instance_overrides_are_scoped"),
    "explicit_composition_precedence": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_composition_requires_explicit_override_and_order"),
    "unknown_mandatory_fails_closed": ("tests.test_m04_core", "SchemaAndSerializationBoundaryTests", "test_unknown_mandatory_facet_fails_closed"),
    "optional_opaque_policy": ("tests.test_m04_core", "SchemaAndSerializationBoundaryTests", "test_unknown_optional_facet_preserved_only_when_explicitly_allowed"),
    "schema_version_explicit": ("tests.test_m04_core", "SchemaAndSerializationBoundaryTests", "test_schema_family_and_version_are_explicit"),
    "transport_version_distinct": ("tests.test_m04_invariants", "FrozenInvariantProofTests", "_prove_transport_version_distinct"),
    "directional_compatibility": ("tests.test_m04_invariants", "FrozenInvariantProofTests", "_prove_directional_compatibility"),
    "migration_new_revision": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_migration_creates_new_revision_and_receipt_verifies_the_applied_actions"),
    "migration_receipt": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_migration_creates_new_revision_and_receipt_verifies_the_applied_actions"),
    "canonical_serialization": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_canonical_envelope_round_trips_every_integrated_modality"),
    "finite_numbers": ("tests.test_m04_spatial_materials", "SpatialSemanticsTests", "test_quantity_requires_dimension_and_registered_unit"),
    "duplicate_ids": ("tests.test_m04_core", "CoreIdentityAndGraphTests", "test_duplicate_node_identity_fails_closed"),
    "authored_derived_transform": ("tests.test_m04_spatial_materials", "SpatialSemanticsTests", "test_transform_operation_order_is_semantic_and_resolved_as_derived"),
    "explicit_spatial_units": ("tests.test_m04_spatial_materials", "SpatialSemanticsTests", "test_quantity_requires_dimension_and_registered_unit"),
    "conversion_receipt": ("tests.test_m04_spatial_materials", "SpatialSemanticsTests", "test_unit_conversion_is_deterministic_and_receipted"),
    "portable_camera": ("tests.test_m04_spatial_materials", "SpatialSemanticsTests", "test_camera_physical_optics_round_trip_and_projection_extension"),
    "nonlinear_projection_extension": ("tests.test_m04_spatial_materials", "SpatialSemanticsTests", "test_camera_physical_optics_round_trip_and_projection_extension"),
    "typed_light_quantity": ("tests.test_m04_spatial_materials", "SpatialSemanticsTests", "test_light_intensity_is_typed_and_nonphysical_controls_classified"),
    "classified_artistic_light": ("tests.test_m04_spatial_materials", "SpatialSemanticsTests", "test_light_intensity_is_typed_and_nonphysical_controls_classified"),
    "typed_material_graph": ("tests.test_m04_spatial_materials", "MaterialAndColorTests", "test_typed_material_ports_and_connections_round_trip"),
    "no_executable_shader": ("tests.test_m04_invariants", "FrozenInvariantProofTests", "_prove_no_executable_shader"),
    "color_semantics": ("tests.test_m04_spatial_materials", "MaterialAndColorTests", "test_color_semantics_pin_space_encoding_alpha_and_conversion_authority"),
    "preview_final_separation": ("tests.test_m04_spatial_materials", "MaterialAndColorTests", "test_material_binding_preview_cannot_satisfy_final_obligation"),
    "explicit_time_basis": ("tests.test_m04_temporal_media", "TimeAndMotionTests", "test_time_basis_and_conversion_are_exact_rational"),
    "time_layer_separation": ("tests.test_m04_temporal_media", "TimeAndMotionTests", "test_time_layers_are_explicit_and_ranges_are_bounded"),
    "typed_motion_target": ("tests.test_m04_temporal_media", "TimeAndMotionTests", "test_motion_channel_uses_typed_semantic_target_and_value_type"),
    "portable_motion_only": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_governance_authority_fields_and_closed_import_boundary"),
    "motion_production_boundary": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_governance_authority_fields_and_closed_import_boundary"),
    "external_audio_resource": ("tests.test_m04_temporal_media", "AudioMusicNarrativeTimelineTests", "test_audio_media_bytes_are_external_and_spatial_audio_is_frame_aware"),
    "audio_production_boundary": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_governance_authority_fields_and_closed_import_boundary"),
    "music_not_midi": ("tests.test_m04_temporal_media", "AudioMusicNarrativeTimelineTests", "test_music_is_independent_of_midi_and_allows_free_meter_semantics"),
    "music_production_boundary": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_governance_authority_fields_and_closed_import_boundary"),
    "narrative_local_only": ("tests.test_m04_temporal_media", "AudioMusicNarrativeTimelineTests", "test_timeline_and_narrative_projection_remain_local"),
    "canon_authority_boundary": ("tests.test_m04_temporal_media", "AudioMusicNarrativeTimelineTests", "test_timeline_and_narrative_projection_remain_local"),
    "timeline_representation_only": ("tests.test_m04_temporal_media", "AudioMusicNarrativeTimelineTests", "test_timeline_and_narrative_projection_remain_local"),
    "editorial_authority_boundary": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_governance_authority_fields_and_closed_import_boundary"),
    "sync_tolerance": ("tests.test_m04_temporal_media", "AudioMusicNarrativeTimelineTests", "test_sync_tolerance_fails_closed_when_required"),
    "temporal_loss_receipt": ("tests.test_m04_temporal_media", "TimeAndMotionTests", "test_time_basis_and_conversion_are_exact_rational"),
    "capability_requirement_stable": ("tests.test_m04_invariants", "FrozenInvariantProofTests", "_prove_capability_requirement_stable"),
    "semantic_target_profiles": ("tests.test_m04_invariants", "FrozenInvariantProofTests", "_prove_semantic_target_profile"),
    "provider_observation_evidence": ("tests.test_m04_invariants", "FrozenInvariantProofTests", "_prove_provider_observation_evidence"),
    "capability_debt_separate": ("tests.test_m04_invariants", "FrozenInvariantProofTests", "_prove_capability_debt_separate"),
    "derived_data_noncanonical": ("tests.test_m04_spatial_materials", "SpatialSemanticsTests", "test_transform_operation_order_is_semantic_and_resolved_as_derived"),
    "semantic_roundtrip": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_semantic_witnesses_detect_transform_camera_material_time_and_sync_loss"),
    "no_adapter_self_cert": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_adapter_cannot_claim_independent_qualification"),
    "witness_before_result": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_semantic_witnesses_detect_transform_camera_material_time_and_sync_loss"),
    "typed_equivalence_contract": ("tests.test_m04_invariants", "FrozenInvariantProofTests", "_prove_typed_equivalence_contract"),
    "deterministic_findings": ("tests.test_m04_invariants", "FrozenInvariantProofTests", "_prove_deterministic_findings"),
    "bounded_resource_limits": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_minimum_slice_and_temporal_slice_are_bounded_and_payload_free"),
    "typed_failures": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_public_surface_is_unique_complete_and_uses_typed_failures"),
    "readiness_not_promotion": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_governance_authority_fields_and_closed_import_boundary"),
    "hive_context_non_authority": ("tests.test_m04_runtime", "RuntimeAndTransportAcceptanceTests", "test_governance_authority_fields_and_closed_import_boundary"),
}


class FrozenInvariantProofTests(unittest.TestCase):
    def test_proof_index_covers_all_families_and_test_ids(self):
        validate_invariant_proof_index()
        self.assertEqual({proof.family for proof in FROZEN_INVARIANT_PROOFS}, {f"F-M04-{number:02d}" for number in range(1, 21)})
        self.assertEqual({proof.test_id for proof in FROZEN_INVARIANT_PROOFS}, {f"test_m04_invariant_{number:02d}" for number in range(1, 81)})
        self.assertEqual({proof.proof_target for proof in FROZEN_INVARIANT_PROOFS}, set(_CASE_BY_TARGET))

    def _run_case(self, address: tuple[str, str, str]) -> None:
        module_name, class_name, method_name = address
        module = importlib.import_module(module_name)
        case_class = getattr(module, class_name)
        case = case_class(methodName=method_name)
        setup = getattr(case, "setUp", None)
        teardown = getattr(case, "tearDown", None)
        if setup is not None:
            setup()
        try:
            getattr(case, method_name)()
        finally:
            if teardown is not None:
                teardown()

    def _prove_no_parallel_vcs(self) -> None:
        source = fixture_revision()
        left = M04.MultimodalIRDocument(source.scene.ref.document_id, (source,))
        first_child = replace(source, revision_id="child.one", parent_ref=source.revision_ref)
        second_child = replace(source, revision_id="child.two", parent_ref=source.revision_ref)
        branched = M04.MultimodalIRDocument(source.scene.ref.document_id, (source, first_child, second_child))
        self.assertEqual(left.head.revision_id, source.revision_id)
        with self.assertRaises(IRIntegrityError):
            _ = branched.head
        self.assertFalse({item.name for item in fields(IRRevision)} & {"branch", "build_id", "execution_plan", "release_id"})

    def _prove_m01_obligation_ref(self) -> None:
        entity = fixture_revision().nodes[0]
        self.assertEqual(len(entity.quality_obligation_refs), 1)
        self.assertEqual(entity.quality_obligation_refs[0].kind, RefKind.OBLIGATION.value)

    def _prove_bounded_loss_authorized(self) -> None:
        tolerance = SemanticRef(RefKind.POLICY.value, "fixture.tolerance", version="1")
        rule = SemanticLoweringRule(
            "bounded.authorized", SOURCE, RepresentationState.BOUNDED,
            SemanticLossClass.BOUNDED_APPROXIMATION, tolerance_ref=tolerance,
            loss_rule_ref=POLICY,
        )
        self.assertEqual(rule.state, RepresentationState.BOUNDED)
        self.assertEqual(rule.tolerance_ref, tolerance)

    def _prove_capability_read_only(self) -> None:
        declaration = CapabilityDeclaration("geometry.portable", "1", RequirementLevel.REQUIRED, (SOURCE,), trace())
        support = CapabilitySupport("geometry.portable", SupportState.UNSUPPORTED)
        manifest = RepresentationCapabilityManifest("manifest.target", "target.generic", "1", (declaration,), (support,))
        before = content_digest(manifest.to_payload())
        report = M04.analyze_legality(manifest, report_id="legality.fixture", source_revision_digest=fixture_revision().revision_digest)
        self.assertTrue(report.findings[0].blocks)
        self.assertEqual(content_digest(manifest.to_payload()), before)

    def _prove_transport_version_distinct(self) -> None:
        manifest = M04.SchemaManifest()
        self.assertNotEqual(manifest.core_schema_version, manifest.transport_version)
        self.assertEqual(M04.TRANSPORT_VERSION, "iris-m04-json-v1")
        self.assertEqual(M04.CORE_SCHEMA_VERSION, "iris-m04-core-v1")

    def _prove_directional_compatibility(self) -> None:
        source = SchemaFamilyRef("iris.multimodal.scene", "1")
        target = SchemaFamilyRef("iris.multimodal.scene", "2")
        forward = SchemaCompatibilityDeclaration("compat.forward", source, target, True, "compat.1")
        reverse = SchemaCompatibilityDeclaration("compat.reverse", target, source, False, "migration.1", True)
        self.assertTrue(forward.permits(source, target))
        self.assertFalse(forward.permits(target, source))
        self.assertFalse(reverse.permits(source, target))

    def _prove_no_executable_shader(self) -> None:
        with self.assertRaises(IRSchemaError):
            M04.MaterialNodeIR(
                "node.shader", "surface.standard", "1",
                (M04.MaterialPortIR("out", "output", "surface"),),
                parameters={"shader_source": "void main() { }"},
            )

    def _prove_capability_requirement_stable(self) -> None:
        declaration = CapabilityDeclaration("camera.physical", "1", RequirementLevel.REQUIRED, (SOURCE,), trace())
        self.assertEqual(declaration.requirement, RequirementLevel.REQUIRED)
        with self.assertRaises(FrozenInstanceError):
            declaration.requirement = RequirementLevel.OPTIONAL

    def _prove_semantic_target_profile(self) -> None:
        declaration = CapabilityDeclaration("camera.physical", "1", RequirementLevel.REQUIRED, (SOURCE,), trace())
        manifest = RepresentationCapabilityManifest("manifest.portable", "profile.semantic", "1", (declaration,))
        profile = TargetRepresentationProfile("profile.semantic", "1", manifest, ("iris.multimodal.scene",))
        self.assertEqual(profile.profile_id, manifest.profile_id)
        self.assertFalse(any("vendor" in item.casefold() for item in profile.schema_families))

    def _prove_provider_observation_evidence(self) -> None:
        declaration = CapabilityDeclaration("camera.physical", "1", RequirementLevel.REQUIRED, (SOURCE,), trace())
        manifest = RepresentationCapabilityManifest(
            "manifest.observed", "profile.semantic", "1", (declaration,),
            provider_observation_refs=(SOURCE,),
        )
        report = M04.analyze_legality(manifest, report_id="legality.observed", source_revision_digest=fixture_revision().revision_digest)
        self.assertEqual(report.findings[0].state, SupportState.UNKNOWN)
        self.assertEqual(manifest.provider_observation_refs, (SOURCE,))

    def _prove_capability_debt_separate(self) -> None:
        debt = SemanticCapabilityDebt("debt.camera", "profile.semantic", (SOURCE,), True, "target lacks capability")
        self.assertFalse({item.name for item in fields(SemanticCapabilityDebt)} & {"quality_debt", "quality_class", "promotion"})
        self.assertEqual(debt.semantic_refs, (SOURCE,))

    def _prove_typed_equivalence_contract(self) -> None:
        tolerance = ComparisonTolerance("cameras/camera.primary/optics/focal_length", 0.1, "LENGTH", "mm")
        profile = M04.IREquivalenceProfile("profile.tolerant", EquivalenceKind.TOLERANT, (tolerance,))
        self.assertEqual(profile.tolerances[0].domain, "LENGTH")
        with self.assertRaises(IRSchemaError):
            M04.IREquivalenceProfile("profile.invalid", EquivalenceKind.EXACT, (tolerance,))

    def _prove_deterministic_findings(self) -> None:
        revision = fixture_revision()
        first = M04.validate_revision(revision)
        second = M04.validate_revision(revision)
        self.assertEqual(first.to_payload(), second.to_payload())
        self.assertEqual(first.digest, second.digest)


def _make_proof_test(proof):
    def test(self):
        address = _CASE_BY_TARGET[proof.proof_target]
        if address[0] == "tests.test_m04_invariants":
            getattr(self, address[2])()
        else:
            self._run_case(address)

    test.__name__ = proof.test_id
    test.__doc__ = f"Direct acceptance proof for {proof.family} invariant {proof.invariant_number}."
    return test


for _proof in FROZEN_INVARIANT_PROOFS:
    setattr(FrozenInvariantProofTests, _proof.test_id, _make_proof_test(_proof))


if __name__ == "__main__":
    unittest.main()
