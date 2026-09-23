"""Machine-readable index of the frozen hard-invariant proof obligations."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import IRSchemaError

__all__ = ["FrozenInvariantProof", "FROZEN_INVARIANT_PROOFS", "validate_invariant_proof_index"]


@dataclass(frozen=True)
class FrozenInvariantProof:
    invariant_number: int
    family: str
    proof_target: str
    test_id: str


_FAMILY_BY_NUMBER = {
    **{number: "F-M04-01" for number in range(1, 10)},
    **{number: "F-M04-02" for number in (*range(10, 16), 80)},
    16: "F-M04-17",
    17: "F-M04-17",
    18: "F-M04-17",
    19: "F-M04-16",
    20: "F-M04-17",
    21: "F-M04-17",
    22: "F-M04-05",
    23: "F-M04-05",
    24: "F-M04-03",
    25: "F-M04-03",
    26: "F-M04-03",
    27: "F-M04-03",
    28: "F-M04-06",
    29: "F-M04-06",
    30: "F-M04-06",
    **{number: "F-M04-04" for number in range(31, 36)},
    **{number: "F-M04-19" for number in range(36, 41)},
    **{number: "F-M04-08" for number in range(41, 44)},
    **{number: "F-M04-09" for number in range(44, 46)},
    **{number: "F-M04-10" for number in range(46, 48)},
    **{number: "F-M04-11" for number in range(48, 52)},
    **{number: "F-M04-12" for number in (*range(52, 56), 65)},
    **{number: "F-M04-13" for number in range(56, 58)},
    **{number: "F-M04-14" for number in range(58, 60)},
    **{number: "F-M04-15" for number in range(60, 65)},
    **{number: "F-M04-16" for number in range(66, 70)},
    70: "F-M04-18",
    71: "F-M04-07",
    **{number: "F-M04-20" for number in range(72, 76)},
    **{number: "F-M04-19" for number in range(76, 79)},
    79: "F-M04-20",
}

_PROOF_TARGETS = (
    "canonical_identity", "provider_neutral_refs", "display_metadata_excluded", "immutable_revision", "authority_m02", "no_parallel_vcs", "dual_graph", "acyclic_containment", "typed_relationship_policy", "traceability", "no_observation_promotion", "m01_obligation_ref", "no_quality_authority", "quality_class_immutable", "m03_constraint_immutable", "mandatory_semantics_preserved", "lossless_blocks", "bounded_loss_authorized", "capability_read_only", "m16_boundary", "provider_neutral_plan", "m05_opaque_dna", "identity_opaque", "no_storage_backend", "location_not_identity", "deferred_resource", "interface_without_payload", "immutable_prototype", "scoped_instance_override", "explicit_composition_precedence", "unknown_mandatory_fails_closed", "optional_opaque_policy", "schema_version_explicit", "transport_version_distinct", "directional_compatibility", "migration_new_revision", "migration_receipt", "canonical_serialization", "finite_numbers", "duplicate_ids", "authored_derived_transform", "explicit_spatial_units", "conversion_receipt", "portable_camera", "nonlinear_projection_extension", "typed_light_quantity", "classified_artistic_light", "typed_material_graph", "no_executable_shader", "color_semantics", "preview_final_separation", "explicit_time_basis", "time_layer_separation", "typed_motion_target", "portable_motion_only", "motion_production_boundary", "external_audio_resource", "audio_production_boundary", "music_not_midi", "music_production_boundary", "narrative_local_only", "canon_authority_boundary", "timeline_representation_only", "editorial_authority_boundary", "sync_tolerance", "temporal_loss_receipt", "capability_requirement_stable", "semantic_target_profiles", "provider_observation_evidence", "capability_debt_separate", "derived_data_noncanonical", "semantic_roundtrip", "no_adapter_self_cert", "witness_before_result", "typed_equivalence_contract", "deterministic_findings", "bounded_resource_limits", "typed_failures", "readiness_not_promotion", "hive_context_non_authority",
)

FROZEN_INVARIANT_PROOFS = tuple(
    FrozenInvariantProof(number, _FAMILY_BY_NUMBER[number], _PROOF_TARGETS[number - 1], f"test_m04_invariant_{number:02d}")
    for number in range(1, 81)
)


def validate_invariant_proof_index() -> None:
    if len(FROZEN_INVARIANT_PROOFS) != 80 or {item.invariant_number for item in FROZEN_INVARIANT_PROOFS} != set(range(1, 81)):
        raise IRSchemaError("frozen invariant proof index must map all 80 hard invariants exactly once")
    if len({item.test_id for item in FROZEN_INVARIANT_PROOFS}) != 80:
        raise IRSchemaError("each frozen invariant requires a unique focused test id")
    expected_families = {f"F-M04-{number:02d}" for number in range(1, 21)}
    if {item.family for item in FROZEN_INVARIANT_PROOFS} != expected_families:
        raise IRSchemaError("frozen invariant proof index must cover all 20 technology families")
