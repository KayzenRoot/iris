"""Seven deterministic synthetic M09 capacity profiles; no hardware is queried."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iris_resource_twin import (  # noqa: E402
    CapacityTruth,
    Confidence,
    EvidenceOrigin,
    ProvenanceRef,
    ResourceIdentity,
    ResourceSnapshot,
    ResourceTier,
    canonical_json,
    content_digest,
    reconcile_snapshots,
)

GIB = 1024**3
PROFILES = (
    ("cpu-only-host", ResourceTier.RAM, 16 * GIB, 2 * GIB, Confidence.OBSERVED, 1 * GIB),
    ("gpu-8gb-synthetic", ResourceTier.VRAM, 8 * GIB, 1 * GIB, Confidence.OBSERVED, 2 * GIB),
    ("gpu-8gb-constrained-headroom", ResourceTier.VRAM, 8 * GIB, 7 * GIB, Confidence.OBSERVED, 1 * GIB),
    ("balanced-16gb-synthetic", ResourceTier.VRAM, 16 * GIB, 2 * GIB, Confidence.OBSERVED, 4 * GIB),
    ("high-capacity-24gb-synthetic", ResourceTier.VRAM, 24 * GIB, 2 * GIB, Confidence.OBSERVED, 6 * GIB),
    ("gpu-8gb-unknown-telemetry", ResourceTier.VRAM, 8 * GIB, 1 * GIB, Confidence.UNKNOWN, 1 * GIB),
    ("gpu-8gb-conflicting-observations", ResourceTier.VRAM, 8 * GIB, 1 * GIB, Confidence.OBSERVED, 1 * GIB),
)


def _snapshot(profile_id: str, tier: ResourceTier, physical_bytes: int, headroom_bytes: int, confidence: Confidence, *, snapshot_id: str, allocatable_override: int | None = None) -> ResourceSnapshot:
    identity = ResourceIdentity(f"synthetic-{profile_id}", tier, "synthetic-runtime", profile_id)
    committed = min(1 * GIB, max(0, physical_bytes - headroom_bytes))
    if confidence is Confidence.UNKNOWN:
        capacity = CapacityTruth(None, None, None, None, None, None, None, None, None, None)
    else:
        allocatable = physical_bytes - headroom_bytes if allocatable_override is None else allocatable_override
        capacity = CapacityTruth(
            physical_bytes, physical_bytes, allocatable, committed, committed,
            committed // 2, 0, 0, 0, headroom_bytes,
        )
    return ResourceSnapshot(
        snapshot_id, "1.0.0", identity, 1_000, 10_000, confidence, capacity,
        (ProvenanceRef("synthetic-fixture", f"fixture:{profile_id}", 1_000, "SYNTHETIC"),),
        evidence_origin=EvidenceOrigin.SYNTHETIC_FIXTURE,
    )


def build_profiles() -> tuple[dict[str, Any], ...]:
    results: list[dict[str, Any]] = []
    for profile_id, tier, physical, headroom, confidence, request_bytes in PROFILES:
        first = _snapshot(profile_id, tier, physical, headroom, confidence, snapshot_id=f"{profile_id}-snapshot")
        if profile_id == "gpu-8gb-conflicting-observations":
            second = _snapshot(profile_id, tier, physical, headroom, confidence, snapshot_id=f"{profile_id}-alternate", allocatable_override=physical - headroom - GIB)
            reconciliation = reconcile_snapshots((first, second), snapshot_id=f"{profile_id}-reconciled", now_ms=1_100, freshness_window_ms=5_000)
            admitted = reconciliation.snapshot.admits_commitment(1_100, request_bytes)
            result = {
                "profile_id": profile_id,
                "confidence": reconciliation.snapshot.confidence.value,
                "conflict_fields": reconciliation.conflict_fields,
                "request_bytes": request_bytes,
                "commitment_admitted": admitted,
                "evidence_digest": reconciliation.evidence_digest,
            }
        else:
            result = {
                "profile_id": profile_id,
                "confidence": confidence.value,
                "physical_capacity_bytes": physical,
                "operator_headroom_bytes": headroom,
                "request_bytes": request_bytes,
                "commitment_admitted": first.admits_commitment(1_100, request_bytes),
                "snapshot_digest": first.digest,
            }
        result["synthetic_fixture_only"] = True
        result["physical_measurement_performed"] = False
        result["domain_neutral"] = True
        results.append(result)
    if len(results) != 7 or len({item["profile_id"] for item in results}) != 7:
        raise RuntimeError("M09 profile harness requires seven unique deterministic fixtures")
    if any(not item["synthetic_fixture_only"] or item["physical_measurement_performed"] for item in results):
        raise RuntimeError("synthetic M09 evidence cannot claim physical measurement")
    if not next(item for item in results if item["profile_id"] == "gpu-8gb-synthetic")["commitment_admitted"]:
        raise RuntimeError("the 8 GiB constrained-hardware profile must be first-class")
    if next(item for item in results if item["profile_id"] == "gpu-8gb-unknown-telemetry")["commitment_admitted"]:
        raise RuntimeError("unknown telemetry must not authorize a commitment")
    if next(item for item in results if item["profile_id"] == "gpu-8gb-conflicting-observations")["commitment_admitted"]:
        raise RuntimeError("conflicting telemetry must not authorize a commitment")
    return tuple(results)


def main() -> int:
    profiles = build_profiles()
    report = {
        "harness_version": "1.0.0",
        "profile_count": len(profiles),
        "physical_measurements_performed": False,
        "profiles": profiles,
    }
    report["output_digest"] = content_digest(report)
    print(canonical_json(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
