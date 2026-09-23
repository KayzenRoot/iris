"""Frozen M07 technology surfaces and absorbed component map."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .errors import HardwareGenomeIntegrityError

__all__ = [
    "TechnologySurface", "AbsorbedComponent", "M07_SURFACES", "M07_SURFACE_MAP",
    "M07_ABSORBED_COMPONENTS", "validate_surface_catalog",
]


@dataclass(frozen=True)
class TechnologySurface:
    code: str
    name: str
    implementation_module: str
    proof_target: str


@dataclass(frozen=True)
class AbsorbedComponent:
    code: str
    name: str
    owning_surfaces: tuple[str, ...]


M07_SURFACES = (
    TechnologySurface("HDF", "Hardware Discovery Fabric", "discovery", "tests/test_m07_discovery.py::TestDiscovery::test_runtime_probe_admission_requires_an_exact_non_escalating_grant"),
    TechnologySurface("ODG", "Opaque Device Graph", "subjects/topology", "tests/test_m07_discovery.py::TestDiscovery::test_hardware_identity_is_opaque_and_separate_from_mutable_locators"),
    TechnologySurface("NAF", "Negative Assertion Firewall", "evidence", "tests/test_m07_discovery.py::TestDiscovery::test_unknown_and_nonpositive_states_cannot_prove_absence"),
    TechnologySurface("RSP", "Runtime Substrate Passport", "subjects", "tests/test_m07_discovery.py::TestDiscovery::test_runtime_passport_preserves_visibility_and_architecture_axes"),
    TechnologySurface("CEL", "Capability Evidence Ladder", "capabilities", "tests/test_m07_capabilities.py::TestCapabilitySurfaces::test_strength_cannot_increase_without_a_new_evidence_identity"),
    TechnologySurface("BRM", "Backend Relationship Matrix", "capabilities", "tests/test_m07_capabilities.py::TestCapabilitySurfaces::test_capability_cannot_broadcast_across_subject_or_runtime"),
    TechnologySurface("VSF", "Version Separation Fabric", "capabilities", "tests/test_m07_capabilities.py::TestCapabilitySurfaces::test_version_axes_are_separate_and_runtime_skew_is_evidence_linked"),
    TechnologySurface("DSG", "Driver Skew Graph", "capabilities", "tests/test_m07_capabilities.py::TestCapabilitySurfaces::test_version_axes_are_separate_and_runtime_skew_is_evidence_linked"),
    TechnologySurface("PFX", "Precision Feature Lattice", "precision", "tests/test_m07_hardware_surfaces.py::TestPrecisionMediaTopology::test_precision_dimensions_do_not_collapse_to_boolean"),
    TechnologySurface("MEC", "Media Engine Capability Matrix", "media", "tests/test_m07_hardware_surfaces.py::TestPrecisionMediaTopology::test_media_codec_direction_engine_and_feature_limits_are_exact"),
    TechnologySurface("TGE", "Topology Graph Evidence", "topology", "tests/test_m07_hardware_surfaces.py::TestPrecisionMediaTopology::test_topology_edges_are_evidence_bound_acyclic_and_bounded"),
    TechnologySurface("TSL", "Telemetry Semantics Ledger", "telemetry/registry", "tests/test_m07_telemetry.py::TestTelemetry::test_metric_semantics_preserve_units_and_exact_scope"),
    TechnologySurface("MPF", "Memory Pressure Fabric", "telemetry", "tests/test_m07_telemetry.py::TestTelemetry::test_static_memory_capacity_is_not_dynamic_availability_or_pressure"),
    TechnologySurface("EDE", "Evidence Derivation Engine", "telemetry", "tests/test_m07_telemetry.py::TestTelemetry::test_derived_metric_revalidates_formula_and_exact_source_binding"),
    TechnologySurface("SWG", "Sampling Window Governor", "telemetry", "tests/test_m07_telemetry.py::TestTelemetry::test_sampling_window_is_bounded_non_escalating_and_not_busy_looped"),
    TechnologySurface("HGX", "Hardware Genome Exchange", "genome/serialization", "tests/test_m07_genome.py::TestGenome::test_semantic_round_trip_and_fingerprints_are_deterministic"),
    TechnologySurface("MCD", "Multidimensional Confidence Descriptor", "genome", "tests/test_m07_genome.py::TestGenome::test_confidence_is_multidimensional_and_cannot_exceed_its_evidence"),
    TechnologySurface("GDL", "Genome Delta Ledger", "deltas", "tests/test_m07_genome.py::TestGenome::test_delta_is_bound_to_exact_base_and_target_snapshots"),
    TechnologySurface("RFP", "Reproducibility Fingerprint Projection", "projections", "tests/test_m07_authority.py::TestProjectionAndRecovery::test_consumer_projection_is_explicit_named_and_fingerprinted"),
    TechnologySurface("SCB", "Schema Compatibility Barrier", "schema/migration", "tests/test_m07_genome.py::TestGenome::test_schema_reader_barrier_and_compatibility_axes_fail_closed"),
)

M07_ABSORBED_COMPONENTS = (
    AbsorbedComponent("DCF", "Discovery Conflict Fabric", ("HGX", "MCD")),
    AbsorbedComponent("PDM", "Precision Dimensional Matrix", ("PFX",)),
    AbsorbedComponent("CCG", "Capability Conflict Graph", ("HGX", "BRM")),
    AbsorbedComponent("P2P", "Pairwise Path Proof", ("TGE",)),
    AbsorbedComponent("TCR", "Thermal Causality Resolver", ("TSL",)),
)

M07_SURFACE_MAP = MappingProxyType({item.code: item for item in M07_SURFACES})


def validate_surface_catalog() -> None:
    codes = tuple(item.code for item in M07_SURFACES)
    if len(codes) != 20 or len(set(codes)) != 20:
        raise HardwareGenomeIntegrityError("M07 must register exactly 20 independent technology surfaces")
    component_codes = tuple(item.code for item in M07_ABSORBED_COMPONENTS)
    if len(component_codes) != 5 or len(set(component_codes)) != 5:
        raise HardwareGenomeIntegrityError("M07 must register exactly five absorbed components")
    if any(not item.implementation_module or not item.proof_target for item in M07_SURFACES):
        raise HardwareGenomeIntegrityError("every M07 surface requires an implementation module and proof target")
    if any(not item.owning_surfaces or any(owner not in M07_SURFACE_MAP for owner in item.owning_surfaces) for item in M07_ABSORBED_COMPONENTS):
        raise HardwareGenomeIntegrityError("every absorbed component must map to an adopted surface")
