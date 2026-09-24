"""Frozen M08 technology surface and absorbed-component implementation map."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .errors import MicrobenchmarkIntegrityError

__all__ = [
    "TechnologySurface", "AbsorbedComponent", "M08_SURFACES", "M08_SURFACE_MAP",
    "M08_ABSORBED_COMPONENTS", "M08_ABSORBED_COMPONENT_MAP", "validate_surface_catalog",
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
    proof_target: str


M08_SURFACES = (
    TechnologySurface("BPF", "Benchmark Protocol Fabric", "protocols", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_protocol_authority_and_provenance"),
    TechnologySurface("SBG", "Safety Budget Governor", "protocols", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_hard_budgets_and_first_run_safety"),
    TechnologySurface("EPB", "Empirical Provenance Binder", "provenance/evidence", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_result_binds_exact_m07_context_and_protocol"),
    TechnologySurface("ICD", "Interference & Contamination Detector", "evidence", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_cancel_abort_interference_and_unknown_telemetry"),
    TechnologySurface("AEG", "Abort Evidence Generator", "evidence", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_abort_states_remain_explicit"),
    TechnologySurface("CMF", "Comparability Matrix Fabric", "protocols/fingerprints", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_timing_metric_uncertainty_and_comparability"),
    TechnologySurface("UQF", "Uncertainty & Quality-of-Measurement Fabric", "evidence/fingerprints", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_timing_metric_uncertainty_and_comparability"),
    TechnologySurface("FRB", "First-Run Benchmark Budgeter", "protocols", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_hard_budgets_and_first_run_safety"),
    TechnologySurface("MPB", "Multimodal Probe Bank", "probes", "tests/test_m08_probes.py::TestMultimodalProbes::test_probe_fixture_and_correctness_contract"),
    TechnologySurface("COG", "Correctness Oracle Gate", "evidence", "tests/test_m08_probes.py::TestMultimodalProbes::test_probe_fixture_and_correctness_contract"),
    TechnologySurface("TPE", "Transfer Path Examiner", "probes", "tests/test_m08_probes.py::TestMultimodalProbes::test_directional_transfer_paths_and_synchronization"),
    TechnologySurface("MEE", "Media Engine Examiner", "probes", "tests/test_m08_probes.py::TestMultimodalProbes::test_image_video_codec_path_and_stream_semantics"),
    TechnologySurface("GPK", "Graphics Primitive Kernel", "probes", "tests/test_m08_probes.py::TestMultimodalProbes::test_3d_primitive_probes_cannot_claim_renderer_fitness"),
    TechnologySurface("APK", "Audio Primitive Kernel", "probes", "tests/test_m08_probes.py::TestMultimodalProbes::test_audio_probes_use_synthetic_data_without_capture"),
    TechnologySurface("DFM", "Deterministic Fixture Manifest", "probes", "tests/test_m08_probes.py::TestMultimodalProbes::test_probe_fixture_and_correctness_contract"),
    TechnologySurface("BAC", "Backend Adapter Capsule", "probes", "tests/test_m08_probes.py::TestMultimodalProbes::test_adapter_fallback_and_benchmark_authority_firewall"),
    TechnologySurface("CEF", "Capability Envelope Fabric", "envelopes", "tests/test_m08_envelopes.py::TestCapabilityEnvelopes::test_unknown_staleness_lineage_and_authority_boundaries"),
    TechnologySurface("CBD", "Conservative Boundary Deriver", "envelopes", "tests/test_m08_envelopes.py::TestCapabilityEnvelopes::test_conservative_regions_and_bounded_search"),
    TechnologySurface("BSE", "Bounded Search Engine", "envelopes", "tests/test_m08_envelopes.py::TestCapabilityEnvelopes::test_conservative_regions_and_bounded_search"),
    TechnologySurface("MEM", "Memory Envelope Mapper", "envelopes", "tests/test_m08_envelopes.py::TestCapabilityEnvelopes::test_memory_boundary_evidence_has_no_resource_control"),
    TechnologySurface("CCM", "Concurrency Capability Mapper", "envelopes", "tests/test_m08_envelopes.py::TestCapabilityEnvelopes::test_concurrency_and_sustainability_are_observation_scoped"),
    TechnologySurface("SCM", "Sustainability Classifier Matrix", "envelopes", "tests/test_m08_envelopes.py::TestCapabilityEnvelopes::test_concurrency_and_sustainability_are_observation_scoped"),
    TechnologySurface("ECC", "Envelope Coverage & Confidence", "envelopes", "tests/test_m08_envelopes.py::TestCapabilityEnvelopes::test_unknown_staleness_lineage_and_authority_boundaries"),
    TechnologySurface("ELF", "Envelope Lineage Fabric", "envelopes/calibration", "tests/test_m08_envelopes.py::TestCapabilityEnvelopes::test_unknown_staleness_lineage_and_authority_boundaries"),
    TechnologySurface("PFF", "Performance Fingerprint Fabric", "fingerprints", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_projection_schema_privacy_and_stable_lineage"),
    TechnologySurface("DED", "Drift Evidence Detector", "fingerprints", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_comparability_noise_and_metric_scope"),
    TechnologySurface("BLR", "Baseline Lineage Registry", "fingerprints", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_baseline_promotion_and_supersession_are_explicit"),
    TechnologySurface("RTE", "Recheck Trigger Evaluator", "fingerprints", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_drift_states_and_rechecks_do_not_schedule_work"),
    TechnologySurface("NGF", "Noise Guard Fabric", "fingerprints", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_comparability_noise_and_metric_scope"),
    TechnologySurface("DAG", "Drift Attribution Graph", "fingerprints", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_context_changes_correlate_without_causal_or_control_authority"),
    TechnologySurface("PFP", "Privacy Fingerprint Projector", "fingerprints", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_projection_schema_privacy_and_stable_lineage"),
    TechnologySurface("DCP", "Drift Compatibility Protocol", "fingerprints", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_comparability_noise_and_metric_scope"),
    TechnologySurface("CAF", "Calibration Artifact Fabric", "calibration", "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_raw_samples_are_immutable_and_calibration_is_derived"),
    TechnologySurface("EAL", "Evidence Aging Ledger", "calibration", "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_freshness_aging_supersession_and_scoped_invalidation"),
    TechnologySurface("IAG", "Invalidation Graph", "calibration", "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_freshness_aging_supersession_and_scoped_invalidation"),
    TechnologySurface("RCF", "Recalibration Fabric", "calibration", "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_fixture_and_oracle_defects_propagate_and_recalibration_retains_lineage"),
    TechnologySurface("TCB", "Timing Calibration Binder", "calibration", "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_clock_and_normalization_preserve_context"),
    TechnologySurface("FDF", "Fixture Defect Firewall", "calibration", "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_fixture_and_oracle_defects_propagate_and_recalibration_retains_lineage"),
    TechnologySurface("FPE", "Freshness Policy Evaluator", "calibration", "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_freshness_and_invalidation_never_schedule_or_delete"),
    TechnologySurface("NNF", "Non-Normative Normalization Fabric", "calibration", "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_clock_and_normalization_preserve_context"),
)


M08_ABSORBED_COMPONENTS = (
    AbsorbedComponent("BAR", "Benchmark Authorization Receipt", ("BPF", "SBG", "AEG"), "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_protocol_authority_and_provenance"),
    AbsorbedComponent("MSR", "Metric Semantics Registry", ("BPF", "CMF", "UQF"), "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_timing_metric_uncertainty_and_comparability"),
    AbsorbedComponent("MCD", "Measurement Clock Descriptor", ("BPF", "TCB"), "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_clock_and_normalization_preserve_context"),
    AbsorbedComponent("EID", "Envelope Invalidation Dependency Map", ("ELF", "IAG", "FPE"), "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_freshness_aging_supersession_and_scoped_invalidation"),
    AbsorbedComponent("ECP", "Evidence Consumer Projection Descriptor", ("EPB", "PFP", "CEF", "PFF"), "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_projection_schema_privacy_and_stable_lineage"),
    AbsorbedComponent("EPD", "Evidence Purpose Descriptor", ("EPB", "PFP"), "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_projection_schema_privacy_and_stable_lineage"),
    AbsorbedComponent("ECD", "Execution Context Descriptor", ("EPB", "BAC"), "tests/test_m08_probes.py::TestMultimodalProbes::test_adapter_fallback_and_benchmark_authority_firewall"),
    AbsorbedComponent("RQH", "Requirement Qualification Handshake", ("CEF", "CMF", "FPE"), "tests/test_m08_envelopes.py::TestCapabilityEnvelopes::test_unknown_staleness_lineage_and_authority_boundaries"),
    AbsorbedComponent("EIR", "External Invalidation Reference", ("IAG", "ELF"), "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_freshness_aging_supersession_and_scoped_invalidation"),
    AbsorbedComponent("AND", "Authority Namespace Descriptor", ("BPF", "EPB"), "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_cpu_only_8gb_and_external_authority_firewalls"),
    AbsorbedComponent("PED", "Provenance Export Digest", ("EPB", "PFP"), "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_projection_schema_privacy_and_stable_lineage"),
    AbsorbedComponent("SAR", "Security Authorization Reference", ("SBG", "BPF"), "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_protocol_authority_and_provenance"),
    AbsorbedComponent("AOD", "Automation Origin Descriptor", ("EPB", "SBG"), "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_protocol_authority_and_provenance"),
    AbsorbedComponent("ESP", "External Schema Projection", ("CEF", "PFF"), "tests/test_m08_schema_migration.py::TestExternalContracts::test_external_projection_and_acceptance_evidence_are_exact"),
    AbsorbedComponent("AEB", "Acceptance Evidence Bundle", ("EPB", "CEF", "PFF", "CAF", "EAL"), "tests/test_m08_schema_migration.py::TestExternalContracts::test_external_projection_and_acceptance_evidence_are_exact"),
)

M08_SURFACE_MAP = MappingProxyType({item.code: item for item in M08_SURFACES})
M08_ABSORBED_COMPONENT_MAP = MappingProxyType({item.code: item for item in M08_ABSORBED_COMPONENTS})


def validate_surface_catalog() -> None:
    codes = tuple(item.code for item in M08_SURFACES)
    if len(codes) != 40 or len(set(codes)) != 40:
        raise MicrobenchmarkIntegrityError("M08 must register exactly 40 independent technology surfaces")
    component_codes = tuple(item.code for item in M08_ABSORBED_COMPONENTS)
    if len(component_codes) != 15 or len(set(component_codes)) != 15:
        raise MicrobenchmarkIntegrityError("M08 must register exactly 15 absorbed components")
    if any(not item.implementation_module or not item.proof_target for item in M08_SURFACES):
        raise MicrobenchmarkIntegrityError("every M08 surface requires an implementation module and proof target")
    if any(not item.owning_surfaces or any(owner not in M08_SURFACE_MAP for owner in item.owning_surfaces) or not item.proof_target for item in M08_ABSORBED_COMPONENTS):
        raise MicrobenchmarkIntegrityError("every absorbed component must map to adopted surfaces and an executable proof target")
