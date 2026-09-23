"""Seven deterministic synthetic Hardware Genome profiles (no live probing)."""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iris_hardware_genome import (  # noqa: E402
    AbsenceProof,
    DiscoveryBatch,
    DiscoveryConflict,
    DiscoveryObservation,
    DiscoverySessionRef,
    DiscoverySnapshot,
    EvidenceStrength,
    FactEnvelope,
    FreshnessClass,
    HardwareSubjectRef,
    HardwareGenome,
    MetricSemantics,
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
    TelemetrySample,
    create_hardware_genome,
    validate_genome,
)


@dataclass(frozen=True)
class SyntheticProfile:
    profile_id: str
    description: str
    genome: HardwareGenome


def _evidence(key: str, *, runtime: RuntimeSubjectRef, subject: HardwareSubjectRef | None, state_time: int = 1_000, probe_id: str = "fixture") -> ProbeEvidenceRef:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return ProbeEvidenceRef(
        f"fixture-evidence:{key}", digest, probe_id, "1.0", "synthetic", "1.0", state_time, "synthetic", 128,
        subject.subject_id if subject is not None else None, None, runtime.runtime_id,
    )


def _observation(
    key: str,
    value: object = None,
    *,
    runtime: RuntimeSubjectRef,
    subject: HardwareSubjectRef | None,
    state: ObservationState = ObservationState.OBSERVED,
    freshness: FreshnessClass = FreshnessClass.TOPOLOGY_STABLE,
    unit: str | None = None,
    identifier: str,
    partial_frontier: tuple[str, ...] = (),
    evidence: ProbeEvidenceRef | None = None,
    absence_proof: AbsenceProof | None = None,
) -> DiscoveryObservation:
    observed_at = evidence.observed_at_ms if evidence is not None else 1_000
    if state is ObservationState.OBSERVED and evidence is None:
        evidence = _evidence(identifier, runtime=runtime, subject=subject)
    if state is not ObservationState.OBSERVED and state is not ObservationState.NOT_PRESENT_PROVEN:
        value = None
        evidence = None
    return DiscoveryObservation(
        identifier, key, state, observed_at, freshness, "synthetic", subject, runtime,
        value, unit, None, evidence,
        EvidenceStrength.FEATURE_REPORTED if state is ObservationState.OBSERVED else None,
        absence_proof, partial_frontier,
    )


def _snapshot(runtime: RuntimeSubjectRef, observations: tuple[DiscoveryObservation, ...], *, complete: bool = True, frontier: tuple[str, ...] = ()) -> DiscoverySnapshot:
    probe = ProbeDescriptor(
        "fixture", "1.0", ("domain-neutral",), ("hardware", "runtime", "telemetry"),
        10_000, 200_000, ProbeInterface.DECLARED_EVIDENCE, ProbePermissionClass.BASIC_READ,
        FreshnessClass.TOPOLOGY_STABLE, PrivacyClass.PUBLIC_FACT, "1.0",
    )
    registry = ProbeRegistry("1.0", (probe,))
    session = DiscoverySessionRef(
        "fixture-session", "1.0", runtime, tuple(sorted({item.fact_key for item in observations})),
        0, 5_000, 256, 200_000,
    )
    batch = DiscoveryBatch(
        "fixture-batch", session, probe, observations, 1_000, 1024, complete,
        False, False, frontier,
    )
    from iris_hardware_genome import admit_discovery_batch
    return admit_discovery_batch(batch, registry)


def _genome(
    profile_id: str,
    description: str,
    runtime: RuntimeSubjectRef,
    subjects: tuple[HardwareSubjectRef, ...],
    observations: tuple[DiscoveryObservation, ...],
    *,
    complete: bool = True,
    frontier: tuple[str, ...] = (),
    facts: tuple[FactEnvelope, ...] | None = None,
    conflicts: tuple[DiscoveryConflict, ...] = (),
    telemetry: tuple[TelemetrySample, ...] = (),
) -> SyntheticProfile:
    snapshot = _snapshot(runtime, observations, complete=complete, frontier=frontier)
    if facts is None:
        facts = tuple(FactEnvelope(item.fact_key, item, "iris-m07-semantic-registry-v1") for item in observations)
    value = create_hardware_genome(
        discovery=snapshot, subjects=subjects, facts=facts, conflicts=conflicts,
        telemetry=telemetry, created_at_ms=1_000,
    )
    return SyntheticProfile(profile_id, description, value)


def build_seven_profiles() -> tuple[SyntheticProfile, ...]:
    host = RuntimeSubjectRef("host-runtime", RuntimeScope.HOST, "1.0")

    cpu = HardwareSubjectRef("cpu-host-resource", SubjectKind.HOST_RESOURCE)
    cpu_facts = (
        _observation("hardware.cpu.logical_processors", 16, runtime=host, subject=cpu, unit="count", identifier="cpu-logical"),
    )
    cpu_absence_evidence = _evidence("no-discrete-gpu", runtime=host, subject=cpu)
    absence = AbsenceProof("no-gpu-proof", "hardware.gpu.vendor", "fixture", cpu_absence_evidence, True, False, False, True)
    cpu_facts += (
        _observation("hardware.gpu.vendor", runtime=host, subject=cpu, state=ObservationState.NOT_PRESENT_PROVEN, identifier="cpu-no-gpu", evidence=cpu_absence_evidence, absence_proof=absence),
    )
    cpu_only = _genome("cpu-only", "CPU-only host with scoped proof of no enumerated discrete GPU", host, (cpu,), cpu_facts)

    gpu8 = HardwareSubjectRef("accelerator-8gb", SubjectKind.PHYSICAL)
    gpu8_facts = (
        _observation("hardware.gpu.vendor", "vendor-a", runtime=host, subject=gpu8, identifier="gpu8-vendor"),
        _observation("hardware.gpu.dedicated_vram_bytes", 8 * 1024**3, runtime=host, subject=gpu8, unit="byte", identifier="gpu8-vram"),
    )
    eight_gb = _genome("gpu-8gb", "First-class 8 GiB physical accelerator", host, (gpu8,), gpu8_facts)

    gpu_a = HardwareSubjectRef("accelerator-a", SubjectKind.PHYSICAL)
    gpu_b = HardwareSubjectRef("accelerator-b", SubjectKind.PHYSICAL)
    multi_facts = (
        _observation("hardware.gpu.vendor", "vendor-a", runtime=host, subject=gpu_a, identifier="multi-a"),
        _observation("hardware.gpu.vendor", "vendor-b", runtime=host, subject=gpu_b, identifier="multi-b"),
    )
    multi = _genome("multi-adapter", "Two separately addressed adapters with no inferred peer access", host, (gpu_a, gpu_b), multi_facts)

    shared = HardwareSubjectRef("shared-memory-domain", SubjectKind.HOST_RESOURCE)
    memory_facts = (
        _observation("hardware.memory.shared_bytes", 16 * 1024**3, runtime=host, subject=shared, unit="byte", identifier="shared-memory"),
        _observation("hardware.gpu.dedicated_vram_bytes", 8 * 1024**3, runtime=host, subject=gpu8, unit="byte", identifier="dedicated-memory"),
    )
    memory = _genome("shared-and-dedicated-memory", "Separate shared-memory and dedicated-device capacities", host, (shared, gpu8), memory_facts)

    vm = RuntimeSubjectRef("guest-vm", RuntimeScope.VM, "1.0", parent_runtime_id=host.runtime_id)
    guest_device = HardwareSubjectRef("guest-visible-adapter", SubjectKind.VIRTUAL)
    guest_facts = (
        _observation("hardware.gpu.vendor", "guest-reported-vendor", runtime=vm, subject=guest_device, identifier="guest-vendor"),
        _observation("hardware.gpu.parent_identity", runtime=vm, subject=guest_device, state=ObservationState.UNKNOWN, identifier="hidden-parent"),
    )
    guest = _genome("guest-partial", "Guest-visible virtual adapter with unknown hidden physical parent", vm, (guest_device,), guest_facts, complete=False, frontier=("host-parent-topology",))

    process = RuntimeSubjectRef("limited-process", RuntimeScope.CONTAINER, "1.0", parent_runtime_id=host.runtime_id)
    limited_gpu = HardwareSubjectRef("limited-gpu", SubjectKind.PHYSICAL)
    limited_facts = (
        _observation("compute.api.cuda", runtime=process, subject=limited_gpu, state=ObservationState.PERMISSION_DENIED, identifier="cuda-denied"),
        _observation("hardware.gpu.vendor", runtime=process, subject=limited_gpu, state=ObservationState.STALE, identifier="stale-vendor"),
    )
    permission_limited = _genome("permission-limited", "Container visibility with explicit permission and stale states", process, (limited_gpu,), limited_facts)

    left = _observation("hardware.gpu.vendor", "vendor-left", runtime=host, subject=gpu_a, identifier="conflict-left")
    right = _observation("hardware.gpu.vendor", "vendor-right", runtime=host, subject=gpu_a, identifier="conflict-right", evidence=_evidence("conflict-right", runtime=host, subject=gpu_a))
    conflicted = _observation("hardware.gpu.vendor", runtime=host, subject=gpu_a, state=ObservationState.CONFLICTING, identifier="conflict-state")
    conflict = DiscoveryConflict("vendor-disagreement", left.fact_key, (left.observation_id, right.observation_id), "MATERIAL_SOURCE_DISAGREEMENT")
    conflict_fact = FactEnvelope(conflicted.fact_key, conflicted, "iris-m07-semantic-registry-v1")
    stale_telemetry = TelemetrySample(
        "stale-power", "telemetry.gpu.power", MetricSemantics.INSTANTANEOUS_GAUGE, None, "watt",
        gpu_a, host, "power-source", "1.0", 1, 1_000, 0, 1_000, ObservationState.STALE,
        _evidence("stale-power", runtime=host, subject=gpu_a), visibility_scope="synthetic",
    )
    conflict_profile = _genome(
        "conflicting-stale-telemetry", "Explicit vendor disagreement plus historical-only stale power sample",
        host, (gpu_a,), (left, right, conflicted), facts=(conflict_fact,), conflicts=(conflict,), telemetry=(stale_telemetry,),
    )

    result = (cpu_only, eight_gb, multi, memory, guest, permission_limited, conflict_profile)
    if len(result) != 7 or len({item.profile_id for item in result}) != 7:
        raise AssertionError("the M07 harness must provide exactly seven named synthetic profiles")
    for item in result:
        report = validate_genome(item.genome)
        if not report.valid:
            raise AssertionError(f"synthetic profile {item.profile_id!r} failed M07 validation: {report.findings}")
    return result


def main() -> int:
    profiles = build_seven_profiles()
    for item in profiles:
        print(f"{item.profile_id}: PASS (synthetic, no hardware probe executed)")
    print(f"M07 domain-neutral synthetic profiles: {len(profiles)}/7 — PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
