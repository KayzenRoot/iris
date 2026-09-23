"""Shared deterministic fixtures for focused M07 contract tests."""

from __future__ import annotations

from iris_hardware_genome import (
    BackendFamily,
    DiscoveryBatch,
    DiscoveryObservation,
    DiscoverySessionRef,
    DiscoverySnapshot,
    EvidenceStrength,
    FreshnessClass,
    HardwareSubjectRef,
    ObservationState,
    ProbeDescriptor,
    ProbeEvidenceRef,
    ProbeInterface,
    ProbePermissionClass,
    ProbeRegistry,
    PrivacyClass,
    RuntimeScope,
    RuntimeSubjectRef,
    SubjectKind,
    admit_discovery_batch,
    create_hardware_genome,
)

SUBJECT = HardwareSubjectRef("gpu-0", SubjectKind.PHYSICAL, display_label="Adapter 0")
SUBJECT_1 = HardwareSubjectRef("gpu-1", SubjectKind.PHYSICAL, display_label="Adapter 1")
RUNTIME = RuntimeSubjectRef("runtime-process", RuntimeScope.PROCESS, "1.0")
PROBE = ProbeDescriptor(
    "inventory", "1.0", ("portable",), ("hardware", "runtime", "capability"),
    5_000, 128_000, ProbeInterface.DECLARED_EVIDENCE, ProbePermissionClass.BASIC_READ,
    FreshnessClass.TOPOLOGY_STABLE, PrivacyClass.PUBLIC_FACT,
    "1.0",
)
PROBE_REGISTRY = ProbeRegistry("1.0", (PROBE,))


def evidence(
    evidence_id: str,
    *,
    observed_at_ms: int = 1_000,
    subject: HardwareSubjectRef | None = SUBJECT,
    related_subject: HardwareSubjectRef | None = None,
    runtime: RuntimeSubjectRef | None = RUNTIME,
    probe_id: str = "inventory",
    probe_version: str = "1.0",
    payload_bytes: int = 64,
    scope: str = "local",
) -> ProbeEvidenceRef:
    return ProbeEvidenceRef(
        evidence_id, "a" * 64, probe_id, probe_version, "adapter", "1.0", observed_at_ms,
        scope, payload_bytes, subject.subject_id if subject else None,
        related_subject.subject_id if related_subject else None, runtime.runtime_id if runtime else None,
    )


def observation(
    fact_key: str = "hardware.gpu.vendor",
    *,
    observation_id: str = "obs-vendor",
    value: object = "vendor-x",
    state: ObservationState = ObservationState.OBSERVED,
    freshness: FreshnessClass = FreshnessClass.TOPOLOGY_STABLE,
    subject: HardwareSubjectRef | None = SUBJECT,
    runtime: RuntimeSubjectRef | None = RUNTIME,
    evidence_ref: ProbeEvidenceRef | None = None,
    evidence_strength: EvidenceStrength | None = EvidenceStrength.DEVICE_BOUND,
    unit: str | None = None,
    partial_frontier: tuple[str, ...] = (),
    absence_proof=None,
    observed_at_ms: int = 1_000,
) -> DiscoveryObservation:
    if evidence_ref is None and state is ObservationState.OBSERVED:
        evidence_ref = evidence(observation_id + "-e", observed_at_ms=observed_at_ms, subject=subject, runtime=runtime)
    if state is not ObservationState.OBSERVED:
        value = None
        evidence_strength = None
    return DiscoveryObservation(
        observation_id, fact_key, state, observed_at_ms, freshness, "local", subject, runtime,
        value, unit, None, evidence_ref, evidence_strength, absence_proof, partial_frontier,
    )


def snapshot(
    observations: tuple[DiscoveryObservation, ...] | None = None,
    *,
    complete: bool = True,
    captured_at_ms: int | None = None,
    frontier: tuple[str, ...] = (),
) -> DiscoverySnapshot:
    observations = observations or (observation(),)
    captured_at_ms = captured_at_ms if captured_at_ms is not None else max(item.observed_at_ms for item in observations)
    keys = tuple(sorted({item.fact_key for item in observations}))
    session = DiscoverySessionRef("session-1", "1.0", RUNTIME, keys, 0, 10_000, 128, 128_000)
    batch = DiscoveryBatch(
        "batch-1", session, PROBE, observations, captured_at_ms, 256, complete,
        not complete and not frontier, False, frontier,
    )
    return admit_discovery_batch(batch, PROBE_REGISTRY)


def genome(
    observations: tuple[DiscoveryObservation, ...] | None = None,
    *,
    subjects: tuple[HardwareSubjectRef, ...] = (SUBJECT,),
    **kwargs,
):
    discovered = snapshot(observations)
    return create_hardware_genome(discovery=discovered, subjects=subjects, created_at_ms=discovered.captured_at_ms, **kwargs)


def capability_assertion(*, subject=SUBJECT, runtime=RUNTIME, evidence_strength=EvidenceStrength.DEVICE_BOUND, observation_id="obs-cap", state=ObservationState.OBSERVED, backend=BackendFamily.CUDA, key="compute.api.cuda"):
    from iris_hardware_genome import CapabilityAssertion

    observed = observation(
        key, observation_id=observation_id, value="available" if state is ObservationState.OBSERVED else None,
        state=state, subject=subject, runtime=runtime, evidence_strength=evidence_strength,
    )
    return CapabilityAssertion(
        "assertion-" + observation_id, subject, runtime, backend, key, state,
        evidence_strength if state is ObservationState.OBSERVED else None, observed,
        "available" if state is ObservationState.OBSERVED else None,
    )
