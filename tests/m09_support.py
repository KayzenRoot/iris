"""Deterministic test values shared by focused M09 suites."""

from __future__ import annotations

from iris_resource_twin import (
    CapacityTruth,
    Confidence,
    DirtyState,
    DurabilityClass,
    EvidenceOrigin,
    Precision,
    ProviderAxisCapability,
    ProvenanceRef,
    ProviderCapabilities,
    ResourceIdentity,
    ResourceSnapshot,
    ResourceTier,
    SpillTargetCapability,
    TransferRequest,
    TransferSegment,
    TransferCostEvidence,
    TransferCostState,
)

GIB = 1024**3


def make_snapshot(
    *,
    physical_id: str = "gpu-8g",
    tier: ResourceTier = ResourceTier.VRAM,
    context_id: str = "runtime-a",
    snapshot_id: str = "snapshot-1",
    confidence: Confidence = Confidence.OBSERVED,
    observed_at_ms: int = 1_000,
    expires_at_ms: int = 10_000,
    capacity: CapacityTruth | None = None,
    display_name: str = "Accelerator",
    evidence_origin: EvidenceOrigin = EvidenceOrigin.REPORTED_OBSERVATION,
    identity: ResourceIdentity | None = None,
) -> ResourceSnapshot:
    if capacity is None:
        physical = 8 * GIB
        capacity = CapacityTruth(
            physical, physical, 7 * GIB, 1 * GIB, 1 * GIB, 512 * 1024**2,
            0, 0, 0, 1 * GIB,
        )
    identity = identity or ResourceIdentity(physical_id, tier, context_id, display_name)
    return ResourceSnapshot(
        snapshot_id, "1.0.0", identity, observed_at_ms, expires_at_ms, confidence,
        capacity,
        (ProvenanceRef("M07:discovery", f"genome-{identity.physical_id}", observed_at_ms),),
        "M07:discovery-snapshot", "M08:capability-envelope",
        evidence_origin=evidence_origin,
    )


def make_spill_target(*, physical_id: str = "spill-0", available_bytes: int | None = 8 * GIB) -> SpillTargetCapability:
    identity = ResourceIdentity(physical_id, ResourceTier.SPILL, "storage-runtime")
    return SpillTargetCapability(
        "m55-capability-1", "M55:spill-capability", identity.stable_key, ResourceTier.SPILL,
        available_bytes, True, True, "M53:permission-ref", identity, "M54:encryption-ref",
        "M55:endurance-ref", False, DurabilityClass.DURABLE, "M55:latency-profile", None, True,
    )


def make_destination_snapshot(target=None, *, snapshot_id: str = "destination-snapshot", observed_at_ms: int = 1_000, evidence_origin: EvidenceOrigin = EvidenceOrigin.REPORTED_OBSERVATION) -> ResourceSnapshot:
    if target is None:
        target = make_spill_target()
    return make_snapshot(
        snapshot_id=snapshot_id,
        observed_at_ms=observed_at_ms,
        evidence_origin=evidence_origin,
        identity=target.identity,
    )


def make_transfer_request(
    *,
    transfer_id: str = "transfer-1",
    target: SpillTargetCapability | None = None,
    byte_count: int = 8,
    dirty_state: DirtyState = DirtyState.CLEAN,
    writeback_ref: str | None = None,
    reconstruction_ref: str | None = None,
    segments: tuple[TransferSegment, ...] = (),
    evidence_origin: EvidenceOrigin = EvidenceOrigin.REPORTED_OBSERVATION,
    composite_group_ref: str | None = None,
) -> TransferRequest:
    selected_target = target or make_spill_target()
    source_identity = make_snapshot().identity
    return TransferRequest(
        transfer_id, f"idem-{transfer_id}", source_identity.stable_key,
        selected_target, byte_count, "a" * 64, dirty_state,
        writeback_ref, reconstruction_ref, segments, 1_100, "M09:authorized-request",
        source_tier=ResourceTier.VRAM,
        source_identity=source_identity,
        artifact_ref=f"asset:{transfer_id}",
        artifact_revision="revision:1",
        source_lease_ref=f"M09:lease:{transfer_id}",
        source_residency_ref=f"M09:residency:{transfer_id}",
        deadline_ms=60_000,
        clock_ref="clock:monotonic-test",
        supports_resume=True,
        maximum_retries=3,
        evidence_origin=evidence_origin,
        cost=TransferCostEvidence(TransferCostState.UNKNOWN, ResourceTier.VRAM, selected_target.tier, None, f"cost:{transfer_id}"),
        composite_group_ref=composite_group_ref,
    )


def make_provider() -> ProviderCapabilities:
    return ProviderCapabilities(
        "provider-neutral-map", (Precision.FP32, Precision.FP16, Precision.BF16),
        ((Precision.FP32, "f32"), (Precision.FP16, "f16"), (Precision.BF16, "bf16")),
        4, True, True, ("batch_size", "precision", "tile", "temporal_chunk"),
        (
            ProviderAxisCapability("batch_size", 1, 4, 1, "ITEM"),
            ProviderAxisCapability("temporal_chunk", 1, 1_000_000, 1, "FRAME"),
            ProviderAxisCapability("tile_height", 1, 1_000_000, 1, "PIXEL"),
            ProviderAxisCapability("tile_width", 1, 1_000_000, 1, "PIXEL"),
        ),
    )
