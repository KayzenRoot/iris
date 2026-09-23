from __future__ import annotations

import unittest

from iris_hardware_genome import (
    BackendFamily,
    BackendRelationship,
    ConfidenceAxis,
    ConfidenceLevel,
    EvidenceStrength,
    HardwareGenomeAdmissionError,
    HardwareGenomeIntegrityError,
    HardwareGenomeValidationError,
    ObservationState,
    PrecisionFamily,
    RuntimeScope,
    RuntimeSubjectRef,
    VersionDimension,
    VersionFact,
    validate_strength_transition,
)
from m07_support import RUNTIME, SUBJECT, SUBJECT_1, capability_assertion, evidence, genome, observation


class TestCapabilitySurfaces(unittest.TestCase):
    def test_backend_presence_is_exact_observation_not_operational_authority(self):
        claim = capability_assertion()
        self.assertEqual(claim.subject, SUBJECT)
        self.assertEqual(claim.runtime, RUNTIME)
        self.assertEqual(claim.state, ObservationState.OBSERVED)
        self.assertEqual(claim.evidence_strength, EvidenceStrength.DEVICE_BOUND)
        self.assertNotIn("benchmark", claim.capability_key)

    def test_capability_cannot_broadcast_across_subject_or_runtime(self):
        claim = capability_assertion()
        wrong_subject = BackendRelationship("rel-wrong", SUBJECT_1, RUNTIME, BackendFamily.CUDA, (claim.assertion_id,))
        with self.assertRaises(HardwareGenomeIntegrityError):
            wrong_subject.validate_assertions((claim,))
        other_runtime = RuntimeSubjectRef("container", RuntimeScope.CONTAINER, "1.0")
        wrong_runtime = BackendRelationship("rel-runtime", SUBJECT, other_runtime, BackendFamily.CUDA, (claim.assertion_id,))
        with self.assertRaises(HardwareGenomeIntegrityError):
            wrong_runtime.validate_assertions((claim,))
        with self.assertRaises(HardwareGenomeAdmissionError):
            BackendRelationship("empty", SUBJECT, RUNTIME, BackendFamily.CUDA, ())

    def test_strength_cannot_increase_without_a_new_evidence_identity(self):
        before = capability_assertion(evidence_strength=EvidenceStrength.DEVICE_BOUND, observation_id="cap-stable")
        same_evidence = capability_assertion(evidence_strength=EvidenceStrength.SMOKE_VERIFIED, observation_id="cap-stable")
        with self.assertRaises(HardwareGenomeAdmissionError):
            validate_strength_transition(before, same_evidence)
        new_evidence = capability_assertion(evidence_strength=EvidenceStrength.SMOKE_VERIFIED, observation_id="cap-new")
        validate_strength_transition(before, new_evidence)

    def test_backend_families_are_peer_vocabulary_not_priority(self):
        from iris_hardware_genome import BackendFamily
        self.assertEqual({item.value for item in BackendFamily}, {"CUDA", "ROCM", "DIRECTML", "METAL", "CPU", "PORTABLE", "GENERIC"})
        portable = capability_assertion(backend=BackendFamily.CPU, observation_id="cpu")
        software = BackendRelationship("cpu-software", SUBJECT, RUNTIME, BackendFamily.CPU, (portable.assertion_id,), True)
        software.validate_assertions((portable,))
        self.assertTrue(software.software_or_emulated)

    def test_version_axes_are_separate_and_runtime_skew_is_evidence_linked(self):
        driver_obs = observation("version.kernel_driver.driver", observation_id="driver-v", value="550.1")
        toolkit_obs = observation("version.toolkit_sdk.toolkit", observation_id="toolkit-v", value="12.4")
        driver = VersionFact("driver-fact", VersionDimension.KERNEL_DRIVER, "driver", "550.1", True, driver_obs)
        toolkit = VersionFact("toolkit-fact", VersionDimension.TOOLKIT_SDK, "toolkit", "12.4", False, toolkit_obs)
        self.assertIsNot(driver.dimension, toolkit.dimension)
        with self.assertRaises((HardwareGenomeAdmissionError, HardwareGenomeIntegrityError)):
            VersionFact("bad-version", VersionDimension.KERNEL_DRIVER, "driver", "550.1", True, toolkit_obs)
        from iris_hardware_genome import DriverSkewEdge, DriverSkewGraph
        compat_obs = observation("driver.compatibility.driver-fact.toolkit-fact", observation_id="driver-compat", state=ObservationState.UNKNOWN)
        edge = DriverSkewEdge("edge", driver.version_fact_id, toolkit.version_fact_id, "REPORTED_COMPATIBILITY", ObservationState.UNKNOWN, compat_obs.observation_id, compat_obs)
        graph = DriverSkewGraph("skew", (driver, toolkit), (edge,))
        self.assertEqual(len(graph.edges), 1)
        with self.assertRaises(HardwareGenomeIntegrityError):
            DriverSkewGraph("skew-bad", (driver, toolkit), (DriverSkewEdge("edge-missing", driver.version_fact_id, toolkit.version_fact_id, "compat", ObservationState.UNKNOWN, "not-present", compat_obs),))

    def test_precision_is_a_multidimensional_lattice(self):
        from iris_hardware_genome import CapabilityDimension, PrecisionFeature, precision_evidence_dimensions
        dimensions = precision_evidence_dimensions(
            representation=ObservationState.OBSERVED, arithmetic=ObservationState.OBSERVED,
            acceleration_reported=ObservationState.UNKNOWN, accumulation=ObservationState.UNKNOWN,
            conversion=ObservationState.OBSERVED, framework_exposure=ObservationState.PERMISSION_DENIED,
            conformance=ObservationState.UNKNOWN,
        )
        observed = observation("precision.fp8", observation_id="precision-observation")
        precision = PrecisionFeature("fp8", SUBJECT.subject_id, RUNTIME.runtime_id, BackendFamily.CUDA, PrecisionFamily.FP8_E4M3, dimensions, (observed.observation_id,))
        precision.validate_observations((observed,))
        self.assertEqual(len(precision.dimensions), 7)
        self.assertIs(precision.state_for(CapabilityDimension.ACCELERATION_REPORTED), ObservationState.UNKNOWN)
        self.assertIs(precision.state_for(CapabilityDimension.FRAMEWORK_EXPOSURE), ObservationState.PERMISSION_DENIED)
        self.assertNotEqual(PrecisionFamily.FP8_E4M3, PrecisionFamily.FP8_E5M2)
        with self.assertRaises(HardwareGenomeValidationError):
            PrecisionFeature("bad", SUBJECT.subject_id, RUNTIME.runtime_id, BackendFamily.CUDA, PrecisionFamily.FP8_E4M3, dimensions[:-1], (observed.observation_id,))

    def test_conflicting_capability_sources_are_not_resolved_by_preference(self):
        left = observation("compute.api.cuda", observation_id="cap-left", value="present")
        right = observation("compute.api.cuda", observation_id="cap-right", value="absent", evidence_ref=evidence("cap-right-e"))
        from iris_hardware_genome import DiscoveryConflict, FactEnvelope, REGISTRY_VERSION
        conflict = DiscoveryConflict("api-conflict", "compute.api.cuda", (left.observation_id, right.observation_id), "MATERIAL_DISAGREEMENT", "higher-priority-is-projection-only")
        conflicted = observation("compute.api.cuda", observation_id="api-conflicted", state=ObservationState.CONFLICTING)
        result = genome((left, right, conflicted), conflicts=(conflict,), facts=(FactEnvelope(conflicted.fact_key, conflicted, REGISTRY_VERSION),))
        self.assertEqual(result.conflicts[0], conflict)
        self.assertIs(result.confidence.level_for(ConfidenceAxis.SOURCE_AGREEMENT), ConfidenceLevel.LOW)

    def test_smoke_is_conformance_evidence_not_benchmark_or_quality(self):
        from iris_hardware_genome import CapabilityDimension, PrecisionFeature, precision_evidence_dimensions
        smoke = capability_assertion(evidence_strength=EvidenceStrength.SMOKE_VERIFIED, observation_id="smoke")
        self.assertIs(smoke.evidence_strength, EvidenceStrength.SMOKE_VERIFIED)
        dimensions = precision_evidence_dimensions(
            representation=ObservationState.OBSERVED, arithmetic=ObservationState.OBSERVED,
            acceleration_reported=ObservationState.OBSERVED, accumulation=ObservationState.UNKNOWN,
            conversion=ObservationState.UNKNOWN, framework_exposure=ObservationState.OBSERVED,
            conformance=ObservationState.OBSERVED,
        )
        feature = PrecisionFeature("smoke-feature", SUBJECT.subject_id, RUNTIME.runtime_id, BackendFamily.CUDA, PrecisionFamily.FP16, dimensions, (smoke.observation.observation_id,))
        feature.validate_observations((smoke.observation,))
        self.assertIs(feature.state_for(CapabilityDimension.CONFORMANCE), ObservationState.OBSERVED)
        self.assertFalse(hasattr(feature, "benchmark_score"))


if __name__ == "__main__":
    unittest.main()
