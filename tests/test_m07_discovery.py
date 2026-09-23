from __future__ import annotations

import dataclasses
import unittest

from iris_hardware_genome import (
    AbsenceProof,
    DeviceLocatorEvidence,
    DiscoveryBatch,
    DiscoveryConflict,
    DiscoverySessionRef,
    FreshnessClass,
    HardwareGenomeAdmissionError,
    HardwareGenomeIntegrityError,
    HardwareGenomeLimitError,
    HardwareGenomeSecurityError,
    HardwareGenomeValidationError,
    IdentityAnchor,
    M07_ABSORBED_COMPONENTS,
    M07_INVARIANTS,
    M07_SURFACES,
    ObservationState,
    PrivacyClass,
    ProbeDescriptor,
    ProbeInterface,
    ProbePermissionClass,
    ProbePermissionGrant,
    ProbeRegistry,
    RuntimeScope,
    RuntimeSubjectRef,
    RuntimeSubstrate,
    RuntimeSubstratePassport,
    SubjectKind,
    HardwareSubjectRef,
    authorize_probe,
    validate_surface_catalog,
)
from m07_support import PROBE, PROBE_REGISTRY, RUNTIME, SUBJECT, SUBJECT_1, evidence, genome as make_genome, observation, snapshot


class TestDiscovery(unittest.TestCase):
    def test_closed_inventory_and_public_surface_are_complete(self):
        validate_surface_catalog()
        self.assertEqual(len(M07_SURFACES), 20)
        self.assertEqual(len({surface.code for surface in M07_SURFACES}), 20)
        self.assertEqual(len(M07_ABSORBED_COMPONENTS), 5)
        self.assertEqual([item.number for item in M07_INVARIANTS], list(range(1, 236)))
        self.assertEqual(snapshot().completeness, ObservationState.OBSERVED)

    def test_probes_are_read_only_unprivileged_and_closed(self):
        for kwargs in ({"read_only": False}, {"requires_elevation": True}, {"permits_arbitrary_execution": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(HardwareGenomeSecurityError):
                ProbeDescriptor(
                    "unsafe", "1.0", ("portable",), ("hardware",), 100, 100,
                    ProbeInterface.OPERATING_SYSTEM_API, ProbePermissionClass.BASIC_READ,
                    FreshnessClass.TOPOLOGY_STABLE, PrivacyClass.PUBLIC_FACT, "1.0", **kwargs,
                )
        with self.assertRaises(HardwareGenomeLimitError):
            ProbeRegistry("1.0", tuple(dataclasses.replace(PROBE, probe_id=f"p-{i}") for i in range(257)))

    def test_probe_grant_is_exact_and_time_bounded(self):
        grant = ProbePermissionGrant("grant", PROBE.probe_id, PROBE.version, PROBE.permission_class, SUBJECT.subject_id, RUNTIME.runtime_id, 10, 20, "authority")
        authorize_probe(PROBE, grant, subject_id=SUBJECT.subject_id, runtime_id=RUNTIME.runtime_id, now_ms=15)
        with self.assertRaises(HardwareGenomeAdmissionError):
            authorize_probe(PROBE, grant, subject_id=SUBJECT_1.subject_id, runtime_id=RUNTIME.runtime_id, now_ms=15)
        with self.assertRaises(HardwareGenomeAdmissionError):
            authorize_probe(PROBE, grant, subject_id=SUBJECT.subject_id, runtime_id=RUNTIME.runtime_id, now_ms=20)

    def test_runtime_probe_admission_requires_an_exact_non_escalating_grant(self):
        from iris_hardware_genome import admit_discovery_batch

        runtime_probe = ProbeDescriptor(
            "os-inventory", "1.0", ("portable",), ("hardware",), 5_000, 128_000,
            ProbeInterface.OPERATING_SYSTEM_API, ProbePermissionClass.DEVICE_ENUMERATION,
            FreshnessClass.TOPOLOGY_STABLE, PrivacyClass.PUBLIC_FACT, "1.0",
        )
        registry = ProbeRegistry("1.0", (runtime_probe,))
        session = DiscoverySessionRef("runtime-session", "1.0", RUNTIME, ("hardware.gpu.vendor",), 0, 5_000, 8, 128_000)
        source = evidence("os-evidence", probe_id=runtime_probe.probe_id, probe_version=runtime_probe.version)
        observed = observation(evidence_ref=source)
        batch = DiscoveryBatch("runtime-batch", session, runtime_probe, (observed,), 1_000, 128, True)
        with self.assertRaises(HardwareGenomeAdmissionError):
            admit_discovery_batch(batch, registry)
        grant = ProbePermissionGrant(
            "device-grant", runtime_probe.probe_id, runtime_probe.version, runtime_probe.permission_class,
            SUBJECT.subject_id, RUNTIME.runtime_id, 0, 2_000, "user-grant-evidence",
        )
        admitted = admit_discovery_batch(batch, registry, permission_grants=(grant,), now_ms=1_000)
        self.assertIs(admitted.completeness, ObservationState.OBSERVED)
        wrong = dataclasses.replace(grant, grant_id="wrong-subject", subject_id=SUBJECT_1.subject_id)
        with self.assertRaises(HardwareGenomeAdmissionError):
            admit_discovery_batch(batch, registry, permission_grants=(wrong,), now_ms=1_000)

    def test_evidence_binds_exact_time_probe_source_subject_and_runtime(self):
        good = observation()
        self.assertEqual(good.evidence.observed_at_ms, good.observed_at_ms)
        self.assertEqual(good.evidence.source_adapter_version, "1.0")
        with self.assertRaises(HardwareGenomeIntegrityError):
            observation(evidence_ref=evidence("wrong", subject=SUBJECT_1))
        with self.assertRaises(HardwareGenomeIntegrityError):
            observation(evidence_ref=evidence("wrong-runtime", runtime=RuntimeSubjectRef("other", RuntimeScope.HOST, "1.0")))

    def test_unknown_and_nonpositive_states_cannot_prove_absence(self):
        proof_evidence = evidence("absence-e")
        valid = AbsenceProof("absence", "hardware.gpu.vendor", "inventory", proof_evidence, True, False, False, True)
        absent = observation(
            state=ObservationState.NOT_PRESENT_PROVEN,
            evidence_ref=proof_evidence,
            absence_proof=valid,
            evidence_strength=None,
        )
        self.assertIs(absent.state, ObservationState.NOT_PRESENT_PROVEN)
        for state in (ObservationState.UNKNOWN, ObservationState.UNSUPPORTED_PROBE, ObservationState.PERMISSION_DENIED, ObservationState.UNAVAILABLE, ObservationState.PARTIAL, ObservationState.STALE):
            with self.subTest(state=state):
                with self.assertRaises((HardwareGenomeAdmissionError, HardwareGenomeValidationError)):
                    observation(state=state, evidence_ref=proof_evidence, absence_proof=valid, partial_frontier=("frontier",) if state is ObservationState.PARTIAL else ())
        blocked = AbsenceProof("blocked", "hardware.gpu.vendor", "inventory", proof_evidence, True, False, True, True)
        with self.assertRaises(HardwareGenomeAdmissionError):
            observation(state=ObservationState.NOT_PRESENT_PROVEN, evidence_ref=proof_evidence, absence_proof=blocked, evidence_strength=None)

    def test_conflicts_preserve_disagreement_with_exact_subject_scope(self):
        left = observation(observation_id="vendor-left", value="vendor-a")
        right = observation(observation_id="vendor-right", value="vendor-b", evidence_ref=evidence("vendor-right-e"))
        conflict = DiscoveryConflict("vendor-conflict", left.fact_key, (left.observation_id, right.observation_id), "SOURCE_DISAGREEMENT")
        conflict.validate_against((left, right))
        self.assertEqual(len(conflict.observation_ids), 2)
        with self.assertRaises(HardwareGenomeIntegrityError):
            conflict.validate_against((left, observation(observation_id="other", value="vendor-b", subject=SUBJECT_1)))

    def test_partial_or_truncated_batch_never_claims_completeness(self):
        partial = snapshot((observation(state=ObservationState.PARTIAL, partial_frontier=("vendor",)),), complete=False, frontier=("vendor",))
        self.assertIs(partial.completeness, ObservationState.PARTIAL)
        self.assertTrue(partial.frontier)
        with self.assertRaises(HardwareGenomeAdmissionError):
            from m07_support import PROBE_REGISTRY
            session = DiscoverySessionRef("session-bad", "1.0", RUNTIME, ("hardware.gpu.vendor", "hardware.cpu.family"), 0, 100, 1, 10)
            batch = DiscoveryBatch("batch-bad", session, PROBE, (observation(),), 50, 1, True)
            from iris_hardware_genome import admit_discovery_batch
            admit_discovery_batch(batch, PROBE_REGISTRY)

    def test_batch_obeys_time_output_and_evidence_budgets(self):
        from iris_hardware_genome import HardwareGenomeLimits, admit_discovery_batch

        session = DiscoverySessionRef("session-limit", "1.0", RUNTIME, ("hardware.gpu.vendor",), 0, 100, 4, 128)
        too_late = DiscoveryBatch("late", session, PROBE, (observation(),), 101, 32, True)
        delayed = admit_discovery_batch(too_late, PROBE_REGISTRY)
        self.assertIs(delayed.completeness, ObservationState.PARTIAL)
        too_large = DiscoveryBatch("large", session, PROBE, (observation(),), 50, 129, True)
        with self.assertRaises(HardwareGenomeLimitError):
            admit_discovery_batch(too_large, PROBE_REGISTRY)
        batch = DiscoveryBatch("evidence-large", session, PROBE, (observation(),), 50, 100, True)
        with self.assertRaises(HardwareGenomeLimitError):
            admit_discovery_batch(batch, PROBE_REGISTRY, limits=HardwareGenomeLimits(max_evidence_bytes=1))

    def test_hardware_identity_is_opaque_and_separate_from_mutable_locators(self):
        anchor = IdentityAnchor("vendor-device", "b" * 64, "evidence-1", PrivacyClass.SENSITIVE_IDENTIFIER)
        locator = DeviceLocatorEvidence("locator", "pci-path", "0000:01:00.0", 1_000)
        subject = HardwareSubjectRef("opaque-hardware-id", SubjectKind.PHYSICAL, (anchor,), locator_evidence=(locator,), display_label="Friendly GPU")
        self.assertNotEqual(subject.subject_id, locator.value)
        self.assertEqual(subject.identity_anchors[0].digest, "b" * 64)
        self.assertEqual(SUBJECT.subject_id, "gpu-0")
        self.assertEqual(SUBJECT_1.subject_id, "gpu-1")
        self.assertNotEqual(SUBJECT, SUBJECT_1)

    def test_runtime_passport_preserves_visibility_and_architecture_axes(self):
        host = RuntimeSubjectRef("host", RuntimeScope.HOST, "1.0")
        process = RuntimeSubjectRef("guest-process", RuntimeScope.PROCESS, "1.0", parent_runtime_id="host")
        substrate = RuntimeSubstrate(host, "windows", "11.0", "10.0", "x86_64", "arm64", "3.12", container_boundary="container-a", visibility_limitations=("physical-host-partial",), virtualization_reported=True)
        passport = RuntimeSubstratePassport("passport", substrate, 10, (SUBJECT.subject_id,), "PARTIAL", "evidence")
        self.assertNotEqual(substrate.host_architecture, substrate.process_architecture)
        self.assertEqual(passport.completeness, "PARTIAL")
        self.assertEqual(process.parent_runtime_id, "host")

    def test_genome_binds_passport_and_identity_anchors_to_admitted_evidence(self):
        from iris_hardware_genome import RuntimeSubstrate, create_hardware_genome
        subject = HardwareSubjectRef("anchored-device", SubjectKind.PHYSICAL)
        observed = observation(observation_id="anchor-source", subject=subject)
        anchor = IdentityAnchor("vendor-device", "c" * 64, observed.evidence.evidence_id, PrivacyClass.SENSITIVE_IDENTIFIER)
        anchored_subject = HardwareSubjectRef(subject.subject_id, subject.kind, (anchor,))
        runtime_observation = observation(observation_id="passport-evidence")
        substrate = RuntimeSubstrate(RUNTIME, "windows", None, None, "x86_64", "x86_64")
        passport = RuntimeSubstratePassport("passport-valid", substrate, runtime_observation.observed_at_ms, (SUBJECT.subject_id,), "PARTIAL", runtime_observation.evidence.evidence_id)
        create_hardware_genome(
            discovery=snapshot((runtime_observation,)), subjects=(SUBJECT,), passports=(passport,), created_at_ms=1_000,
        )
        anchored = make_genome((observed,), subjects=(anchored_subject,))
        self.assertEqual(anchored.subjects[0].identity_anchors[0].source_evidence_id, observed.evidence.evidence_id)
        bad_anchor = IdentityAnchor("vendor-device", "c" * 64, "missing-evidence", PrivacyClass.SENSITIVE_IDENTIFIER)
        with self.assertRaises(HardwareGenomeIntegrityError):
            make_genome((observed,), subjects=(HardwareSubjectRef(subject.subject_id, subject.kind, (bad_anchor,)),))
        bad_passport = dataclasses.replace(passport, evidence_id="missing-evidence")
        with self.assertRaises(HardwareGenomeIntegrityError):
            make_genome((runtime_observation,), passports=(bad_passport,))

    def test_semantic_subjects_do_not_gain_external_authority(self):
        self.assertNotIn("scheduler", {field.name.lower() for field in dataclasses.fields(type(SUBJECT))})
        self.assertNotIn("benchmark", {field.name.lower() for field in dataclasses.fields(type(SUBJECT))})


if __name__ == "__main__":
    unittest.main()
