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
    TechnologySurface("HDF", "Hardware Discovery Fabric", "discovery", "test_hdf_probe_admission"),
    TechnologySurface("ODG", "Opaque Device Graph", "subjects/topology", "test_odg_identity_and_topology"),
    TechnologySurface("NAF", "Negative Assertion Firewall", "evidence", "test_naf_absence_proof"),
    TechnologySurface("RSP", "Runtime Substrate Passport", "subjects", "test_rsp_visibility_scope"),
    TechnologySurface("CEL", "Capability Evidence Ladder", "capabilities", "test_cel_evidence_ladder"),
    TechnologySurface("BRM", "Backend Relationship Matrix", "capabilities", "test_brm_exact_binding"),
    TechnologySurface("VSF", "Version Separation Fabric", "capabilities", "test_vsf_version_axes"),
    TechnologySurface("DSG", "Driver Skew Graph", "capabilities", "test_dsg_runtime_skew"),
    TechnologySurface("PFX", "Precision Feature Lattice", "precision", "test_pfx_precision_dimensions"),
    TechnologySurface("MEC", "Media Engine Capability Matrix", "media", "test_mec_device_path_scope"),
    TechnologySurface("TGE", "Topology Graph Evidence", "topology", "test_tge_directional_edges"),
    TechnologySurface("TSL", "Telemetry Semantics Ledger", "telemetry/registry", "test_tsl_metric_semantics"),
    TechnologySurface("MPF", "Memory Pressure Fabric", "telemetry", "test_mpf_static_dynamic_separation"),
    TechnologySurface("EDE", "Evidence Derivation Engine", "telemetry", "test_ede_derivation_lineage"),
    TechnologySurface("SWG", "Sampling Window Governor", "telemetry", "test_swg_bounded_sampling"),
    TechnologySurface("HGX", "Hardware Genome Exchange", "genome/serialization", "test_hgx_round_trip"),
    TechnologySurface("MCD", "Multidimensional Confidence Descriptor", "genome", "test_mcd_no_confidence_laundering"),
    TechnologySurface("GDL", "Genome Delta Ledger", "deltas", "test_gdl_exact_base_target"),
    TechnologySurface("RFP", "Reproducibility Fingerprint Projection", "projections", "test_rfp_consumer_projection"),
    TechnologySurface("SCB", "Schema Compatibility Barrier", "schema/migration", "test_scb_fail_closed_migration"),
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
