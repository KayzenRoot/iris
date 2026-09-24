"""Frozen catalog for the M09 technology-surface review."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["TechnologySurface", "AbsorbedComponent", "M09_SURFACES", "M09_ABSORBED_COMPONENTS", "validate_surface_catalog"]

@dataclass(frozen=True)
class TechnologySurface:
    number: int
    section: str
    name: str
    obligation: str
    implementation_area: str

@dataclass(frozen=True)
class AbsorbedComponent:
    number: int
    name: str
    obligation: str

M09_SURFACES = (
    TechnologySurface(1, 'S01', 'Resource Digital Twin Fabric', 'canonical immutable resource-state snapshots', 'twin'),
    TechnologySurface(2, 'S01', 'Resource State Ledger', 'append-oriented resource transitions', 'twin'),
    TechnologySurface(3, 'S01', 'Capacity Truth Partition', 'distinct physical/reported/allocatable/headroom/committed/resident/reclaimable/external/unknown capacity', 'twin'),
    TechnologySurface(4, 'S01', 'Confidence & Unknown-State Lattice', 'KNOWN/ESTIMATED/STALE/CONFLICTED/UNKNOWN/UNSUPPORTED semantics', 'twin'),
    TechnologySurface(5, 'S01', 'Headroom Covenant', 'protected operator/workstation resource reserve', 'twin'),
    TechnologySurface(6, 'S01', 'Commitment Conservation Engine', 'conservation and anti-double-counting predicates', 'twin'),
    TechnologySurface(7, 'S01', 'Resource Identity Namespace', 'stable physical/runtime/tier identity', 'twin'),
    TechnologySurface(8, 'S01', 'Observation Reconciliation Fabric', 'asynchronous source reconciliation and skew/conflict evidence', 'twin'),
    TechnologySurface(9, 'S01', 'Staleness & Expiry Governor', 'purpose-sensitive freshness/invalidation', 'twin'),
    TechnologySurface(10, 'S01', 'External Consumption Sentinel', 'conservative unowned/external pressure accounting', 'twin'),
    TechnologySurface(11, 'S01', 'Scarcity Non-Degradation Firewall', 'scarcity cannot silently weaken quality/semantics', 'twin'),
    TechnologySurface(12, 'S01', 'Resource Claim Algebra', 'typed claim scope, quantity, exclusivity and reservation semantics', 'twin'),
    TechnologySurface(13, 'S01', 'Resource Event Causality Graph', 'explainable resource-state causes', 'twin'),
    TechnologySurface(14, 'S01', 'Pressure Signal Normalizer', 'provider-neutral pressure evidence', 'twin'),
    TechnologySurface(15, 'S01', 'Reconciliation Quarantine', 'impossible/conflicting state isolation', 'twin'),
    TechnologySurface(16, 'S01', 'Resource Safety Envelope', 'arithmetic/mutation structural bounds', 'twin'),
    TechnologySurface(17, 'S02', 'Lease Grant Fabric', 'resource-commitment admission', 'leases'),
    TechnologySurface(18, 'S02', 'Reservation Intent Queue', 'pending hard/soft commitment intent', 'leases'),
    TechnologySurface(19, 'S02', 'Atomic Capacity Committer', 'concurrency-safe commitment', 'leases'),
    TechnologySurface(20, 'S02', 'Model Residency Registry', 'typed model/component residency lifecycle', 'leases'),
    TechnologySurface(21, 'S02', 'Shared Residency Refcounter', 'safe multi-consumer residency ownership', 'leases'),
    TechnologySurface(22, 'S02', 'Lease Renewal Gate', 'explicit revalidated extension', 'leases'),
    TechnologySurface(23, 'S02', 'Lease Expiry & Tombstone Ledger', 'durable terminal lease identity', 'leases'),
    TechnologySurface(24, 'S02', 'Anti-Overcommit Firewall', 'conservative hard-commit safety', 'leases'),
    TechnologySurface(25, 'S02', 'Fairness & Starvation Evidence Fabric', 'wait/denial/displacement evidence without scheduling', 'leases'),
    TechnologySurface(26, 'S02', 'Priority Inversion Sentinel', 'inversion evidence without workload reordering', 'leases'),
    TechnologySurface(27, 'S02', 'Lease Preemption Contract', 'explicit cooperative/revocable semantics', 'leases'),
    TechnologySurface(28, 'S02', 'Residency Compatibility Matrix', 'exact sharing compatibility', 'leases'),
    TechnologySurface(29, 'S02', 'Fragmentation Evidence Mapper', 'contiguous/fragmentation uncertainty', 'leases'),
    TechnologySurface(30, 'S02', 'Warm Residency Hint Channel', 'non-authoritative locality/warmth hint', 'leases'),
    TechnologySurface(31, 'S02', 'Orphan Lease Reconciler', 'bounded orphan ownership reconciliation', 'leases'),
    TechnologySurface(32, 'S02', 'Residency Transition Journal', 'causal residency transition evidence', 'leases'),
    TechnologySurface(33, 'S03', 'Tiered Resource Mobility Fabric', 'VRAM/RAM/spill movement semantics', 'mobility'),
    TechnologySurface(34, 'S03', 'Offload Transaction Protocol', 'PREPARED/COPYING/VERIFIED/COMMITTED/ABORTED state', 'mobility'),
    TechnologySurface(35, 'S03', 'Spill Target Capability Contract', 'M55-backed eligible destination contract', 'mobility'),
    TechnologySurface(36, 'S03', 'Transfer Integrity Seal', 'exact moved-material integrity', 'mobility'),
    TechnologySurface(37, 'S03', 'Two-Phase Residency Handoff', 'verify destination before source release', 'mobility'),
    TechnologySurface(38, 'S03', 'Prefetch Intent Fabric', 'bounded non-scheduling prefetch requests', 'mobility'),
    TechnologySurface(39, 'S03', 'Prefetch Budget Governor', 'speculative occupancy/concurrency safety', 'mobility'),
    TechnologySurface(40, 'S03', 'Transfer Cost Evidence Model', 'measured/estimated/unknown transfer cost', 'mobility'),
    TechnologySurface(41, 'S03', 'Dirty-State & Writeback Contract', 'dirty/clean/reconstructible distinction', 'mobility'),
    TechnologySurface(42, 'S03', 'Partial Segment Mobility', 'exact segmented movement/completeness', 'mobility'),
    TechnologySurface(43, 'S03', 'Transfer Cancellation & Resume Ledger', 'bounded cancel/resume state', 'mobility'),
    TechnologySurface(44, 'S03', 'Bandwidth Contention Sentinel', 'non-invasive I/O pressure evidence', 'mobility'),
    TechnologySurface(45, 'S03', 'Data Locality Hint Channel', 'non-authoritative tier/locality evidence', 'mobility'),
    TechnologySurface(46, 'S03', 'Transfer Failure Quarantine', 'corrupt/incomplete destination isolation', 'mobility'),
    TechnologySurface(47, 'S03', 'Spill Garbage Eligibility Contract', 'cleanup eligibility without deletion', 'mobility'),
    TechnologySurface(48, 'S03', 'Zero-Fabrication Offload Firewall', 'explicit unsupported/unavailable/replan outcomes', 'mobility'),
    TechnologySurface(49, 'S04', 'Adaptive Resource Shape Fabric', 'typed tile/chunk/batch/precision axes', 'shaping'),
    TechnologySurface(50, 'S04', 'Feasible Shape Envelope', 'conservative resource feasibility', 'shaping'),
    TechnologySurface(51, 'S04', 'Quality Constraint Binder', 'owning quality authorization for sensitive controls', 'shaping'),
    TechnologySurface(52, 'S04', 'Precision Safety Matrix', 'context-specific precision transition safety', 'shaping'),
    TechnologySurface(53, 'S04', 'Tile Boundary Integrity Contract', 'overlap/halo/seam/context obligations', 'shaping'),
    TechnologySurface(54, 'S04', 'Temporal Chunk Integrity Contract', 'temporal state/continuity obligations', 'shaping'),
    TechnologySurface(55, 'S04', 'Batch Isolation Governor', 'per-item semantic/identity isolation', 'shaping'),
    TechnologySurface(56, 'S04', 'Hysteresis & Thrash Guard', 'bounded oscillation control', 'shaping'),
    TechnologySurface(57, 'S04', 'Resource Control Epoch', 'stale-control mutation protection', 'shaping'),
    TechnologySurface(58, 'S04', 'Provider Capability Adapter', 'canonical-to-provider control mapping', 'shaping'),
    TechnologySurface(59, 'S04', 'Control Reversibility Descriptor', 'reversible/reload/material transition semantics', 'shaping'),
    TechnologySurface(60, 'S04', 'Minimum Viable Shape Guard', 'provider/domain structural minima', 'shaping'),
    TechnologySurface(61, 'S04', 'Shape Compatibility Matrix', 'cross-axis/provider compatibility', 'shaping'),
    TechnologySurface(62, 'S04', 'Adaptation Budget Governor', 'finite change count/frequency/magnitude', 'shaping'),
    TechnologySurface(63, 'S04', 'Degradation Consent Gate', 'scoped authorization for quality-sensitive degradation', 'shaping'),
    TechnologySurface(64, 'S04', 'Replan Signal Fabric', 'FIT/NO_FIT/REQUIRE_REPLAN/REQUIRE_OFFLOAD/QUALITY_AUTH_REQUIRED/UNKNOWN', 'shaping'),
    TechnologySurface(65, 'S04', 'Scarcity Escape Hatch Firewall', 'fail closed when no safe shape exists', 'shaping'),
    TechnologySurface(66, 'S05', 'Memory Pressure State Machine', 'scoped pressure lifecycle', 'recovery'),
    TechnologySurface(67, 'S05', 'Recovery Action Contract', 'enumerated M09-owned recovery actions', 'recovery'),
    TechnologySurface(68, 'S05', 'Leak Suspicion Engine', 'evidence-based suspicion', 'recovery'),
    TechnologySurface(69, 'S05', 'Leak Confirmation Protocol', 'confirmation threshold/proof', 'recovery'),
    TechnologySurface(70, 'S05', 'Ownership Liveness Binder', 'external owner-liveness evidence', 'recovery'),
    TechnologySurface(71, 'S05', 'Stale Commitment Reaper', 'idempotent accounting reconciliation', 'recovery'),
    TechnologySurface(72, 'S05', 'Cooperative Release Handshake', 'bounded owner release request', 'recovery'),
    TechnologySurface(73, 'S05', 'Recovery Escalation Ladder', 'least-disruptive M09 actions and cross-authority signals', 'recovery'),
    TechnologySurface(74, 'S05', 'Cleanup Eligibility Fabric', 'cleanup eligibility without physical deletion', 'recovery'),
    TechnologySurface(75, 'S05', 'False-Leak Quarantine', 'ambiguous leak isolation', 'recovery'),
    TechnologySurface(76, 'S05', 'Pressure Hysteresis Governor', 'pressure entry/exit/dwell/cooldown', 'recovery'),
    TechnologySurface(77, 'S05', 'Recovery Budget Governor', 'bounded recovery attempts/time/churn', 'recovery'),
    TechnologySurface(78, 'S05', 'Incident Causality Capsule', 'deterministic incident evidence', 'recovery'),
    TechnologySurface(79, 'S05', 'Resource Debt Ledger', 'unresolved discrepancy accounting', 'recovery'),
    TechnologySurface(80, 'S05', 'Post-Recovery Reconciliation Gate', 'fresh truth before reuse', 'recovery'),
    TechnologySurface(81, 'S05', 'External Pressure Protection Firewall', 'non-interference with unrelated workloads', 'recovery'),
    TechnologySurface(82, 'S05', 'Recovery Quality Firewall', 'no silent quality/semantic degradation', 'recovery'),
    TechnologySurface(83, 'S05', 'Safe Failure Capsule', 'fail-closed incident package', 'recovery'),
)

M09_ABSORBED_COMPONENTS = (
    AbsorbedComponent(1, 'Resource Provenance Binder', 'absorbed as cross-cutting provenance component of snapshots/events/evidence'),
    AbsorbedComponent(2, 'Snapshot Consistency Seal', 'absorbed as deterministic identity/integrity component of Resource Digital Twin Fabric'),
    AbsorbedComponent(3, 'Lease Token & Epoch Protocol', 'absorbed across Lease Grant Fabric, Renewal Gate and Atomic Capacity Committer'),
    AbsorbedComponent(4, 'Residency Identity Binder', 'absorbed into Model Residency Registry + Compatibility Matrix'),
    AbsorbedComponent(5, 'Lease Authorization Binder', 'absorbed as cross-cutting authorization component for lease mutation'),
    AbsorbedComponent(6, 'Commitment Idempotency Shield', 'absorbed into atomic commitment lifecycle'),
    AbsorbedComponent(7, 'Spill Encryption/Permission Binder', 'absorbed into Spill Target Capability Contract/security references'),
    AbsorbedComponent(8, 'Transfer Idempotency Shield', 'absorbed into Offload Transaction Protocol'),
    AbsorbedComponent(9, 'Spill Wear & Endurance Evidence Port', 'absorbed into Spill Target Capability Contract as optional evidence'),
    AbsorbedComponent(10, 'Resource Mobility Journal', 'absorbed into Resource State Ledger + Event Causality Graph'),
    AbsorbedComponent(11, 'Shape Transition Ledger', 'absorbed into Resource State Ledger + Event Causality Graph'),
    AbsorbedComponent(12, 'Quality-Neutral Preference Channel', 'absorbed into Quality Constraint Binder/Feasible Shape Envelope'),
    AbsorbedComponent(13, 'Shape Evidence Projection', 'absorbed as cross-cutting versioned evidence projection'),
    AbsorbedComponent(14, 'Recovery Idempotency Shield', 'absorbed into Recovery Action Contract/Stale Commitment Reaper'),
    AbsorbedComponent(15, 'Leak Trend Evidence Port', 'absorbed into Incident Causality Capsule/versioned evidence projection'),
)

def validate_surface_catalog() -> bool:
    if len(M09_SURFACES) != 83 or len(M09_ABSORBED_COMPONENTS) != 15:
        raise ValueError("M09 requires exactly 83 surfaces and 15 absorbed components")
    if tuple(item.number for item in M09_SURFACES) != tuple(range(1, 84)):
        raise ValueError("M09 surface sequence has gaps or duplicates")
    if tuple(item.number for item in M09_ABSORBED_COMPONENTS) != tuple(range(1, 16)):
        raise ValueError("M09 absorbed-component sequence has gaps or duplicates")
    if len({item.name for item in M09_SURFACES}) != 83 or len({item.name for item in M09_ABSORBED_COMPONENTS}) != 15:
        raise ValueError("M09 technology catalog contains duplicate names")
    return True
