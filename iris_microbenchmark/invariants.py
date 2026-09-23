"""Literal M08 hard-invariant proof-target index for the frozen 330-item contract."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .errors import MicrobenchmarkIntegrityError

__all__ = ["InvariantRequirement", "M08_INVARIANTS", "M08_INVARIANT_MAP", "validate_invariant_catalog"]


@dataclass(frozen=True)
class InvariantRequirement:
    number: int
    section: str
    proof_target: str


_PROOF_RANGES = (
    (1, 8, "S01", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_protocol_authority_and_provenance"),
    (9, 18, "S01", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_hard_budgets_and_first_run_safety"),
    (19, 22, "S01", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_cancel_abort_interference_and_unknown_telemetry"),
    (23, 33, "S01", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_timing_metric_uncertainty_and_comparability"),
    (34, 43, "S01", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_cpu_only_8gb_and_external_authority_firewalls"),
    (44, 50, "S01", "tests/test_m08_protocol_safety.py::TestProtocolSafety::test_subject_scoping_raw_immutability_and_lineage"),
    (51, 60, "S02", "tests/test_m08_probes.py::TestMultimodalProbes::test_probe_fixture_and_correctness_contract"),
    (61, 68, "S02", "tests/test_m08_probes.py::TestMultimodalProbes::test_directional_transfer_paths_and_synchronization"),
    (69, 79, "S02", "tests/test_m08_probes.py::TestMultimodalProbes::test_image_video_codec_path_and_stream_semantics"),
    (80, 85, "S02", "tests/test_m08_probes.py::TestMultimodalProbes::test_3d_primitive_probes_cannot_claim_renderer_fitness"),
    (86, 91, "S02", "tests/test_m08_probes.py::TestMultimodalProbes::test_audio_probes_use_synthetic_data_without_capture"),
    (92, 100, "S02", "tests/test_m08_probes.py::TestMultimodalProbes::test_adapter_fallback_and_benchmark_authority_firewall"),
    (101, 122, "S03", "tests/test_m08_envelopes.py::TestCapabilityEnvelopes::test_conservative_regions_and_bounded_search"),
    (123, 137, "S03", "tests/test_m08_envelopes.py::TestCapabilityEnvelopes::test_memory_boundary_evidence_has_no_resource_control"),
    (138, 150, "S03", "tests/test_m08_envelopes.py::TestCapabilityEnvelopes::test_concurrency_and_sustainability_are_observation_scoped"),
    (151, 175, "S03", "tests/test_m08_envelopes.py::TestCapabilityEnvelopes::test_unknown_staleness_lineage_and_authority_boundaries"),
    (176, 186, "S04", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_projection_schema_privacy_and_stable_lineage"),
    (187, 199, "S04", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_comparability_noise_and_metric_scope"),
    (200, 208, "S04", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_baseline_promotion_and_supersession_are_explicit"),
    (209, 225, "S04", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_context_changes_correlate_without_causal_or_control_authority"),
    (226, 245, "S04", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_drift_states_and_rechecks_do_not_schedule_work"),
    (246, 250, "S04", "tests/test_m08_fingerprints.py::TestFingerprintDrift::test_consumer_and_m06_m51_m56_firewalls"),
    (251, 261, "S05", "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_raw_samples_are_immutable_and_calibration_is_derived"),
    (262, 277, "S05", "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_freshness_aging_supersession_and_scoped_invalidation"),
    (278, 289, "S05", "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_fixture_and_oracle_defects_propagate_and_recalibration_retains_lineage"),
    (290, 302, "S05", "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_clock_and_normalization_preserve_context"),
    (303, 320, "S05", "tests/test_m08_calibration.py::TestCalibrationAndInvalidation::test_freshness_and_invalidation_never_schedule_or_delete"),
    (321, 330, "FC", "tests/test_m08_schema_migration.py::TestExternalContracts::test_external_projection_and_acceptance_evidence_are_exact"),
)

M08_INVARIANTS = tuple(
    InvariantRequirement(number, section, target)
    for first, last, section, target in _PROOF_RANGES
    for number in range(first, last + 1)
)
M08_INVARIANT_MAP = MappingProxyType({item.number: item for item in M08_INVARIANTS})


def validate_invariant_catalog() -> None:
    numbers = tuple(item.number for item in M08_INVARIANTS)
    if len(M08_INVARIANTS) != 330 or numbers != tuple(range(1, 331)):
        raise MicrobenchmarkIntegrityError("M08 invariant map must contain exact unique numbers 1..330")
    if len(M08_INVARIANT_MAP) != 330:
        raise MicrobenchmarkIntegrityError("M08 invariant map contains duplicate invariant numbers")
    for first, last, section, target in _PROOF_RANGES:
        if first > last or not section or not target:
            raise MicrobenchmarkIntegrityError("M08 invariant proof ranges cannot be empty")
        if any(M08_INVARIANT_MAP[number].section != section or M08_INVARIANT_MAP[number].proof_target != target for number in range(first, last + 1)):
            raise MicrobenchmarkIntegrityError("M08 invariant proof range does not match its executable target")
