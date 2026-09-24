# M09 — Resource Digital Twin & Dynamic VRAM Governor

Status: `S01_PLANNING_CANDIDATE`
Planning base: `11db4286e77ec9d740f1e115bf8c537536bc2b85`
Issue: #61
Implementation: **NOT ADMITTED**

## Mission
M09 owns the resource-state and resource-control truth needed to keep IRIS productive on constrained and heterogeneous machines, with 8 GB VRAM-class hardware as a first-class target. It models observed/estimated/committed memory state, grants bounded resource leases and reservations, tracks residency, and later governs spill/offload/prefetch and memory-pressure recovery. Scarcity is explicit evidence; it never silently lowers M01 quality or protected M03 semantics.

## Canonical sessions
1. S01 Resource Digital Twin state model
2. S02 VRAM leases, reservations and model residency
3. S03 RAM/NVMe spill, offload and prefetch planning
4. S04 Dynamic tile/chunk/batch/precision control
5. S05 Memory-pressure recovery, cleanup and leak detection

# S01 — Resource Digital Twin state model

## S01 objective
Define a provider-neutral, versioned, uncertainty-aware digital twin of resource state. S01 models truth and admissibility primitives. It does not yet implement concrete lease arbitration, spill/offload execution, workload-plan compilation, worker supervision or cross-node placement.

## Authority boundary
- M07 owns discovered hardware/runtime facts and topology.
- M08 owns empirical benchmark/capability-envelope evidence.
- M09 owns transient resource state, reservations/leases/residency and memory-pressure resource policy.
- M10 owns adaptive execution plans, predictive OOM and thermal decisions.
- M11 owns worker/process lifecycle.
- M12 owns placement/orchestration.
- M14 owns model-specific empirical fitness.
- M55 owns physical storage/CAS/cache/archive.
- M56 owns observability aggregation.
- M01 remains quality authority; M03 protected semantics cannot be weakened by scarcity.

## S01 technology surfaces

### RDT-01 — Resource Digital Twin Fabric
Canonical immutable snapshot model for GPU VRAM, host RAM and eligible spill tiers. Every snapshot has stable identity, schema version, observation time, source refs and confidence/validity state.

### RDT-02 — Resource State Ledger
Append-oriented transition ledger connecting snapshots without rewriting historical observations. Transitions distinguish observation, reservation intent, commitment, release, reconciliation and invalidation.

### RDT-03 — Capacity Truth Partition
Separates physical capacity, OS/runtime reported capacity, allocatable capacity, reserved headroom, committed bytes, resident bytes, reclaimable bytes, unavailable/unknown bytes and externally consumed capacity. These values cannot collapse into one free-memory scalar.

### RDT-04 — Confidence & Unknown-State Lattice
Resource facts use explicit KNOWN / ESTIMATED / STALE / CONFLICTED / UNKNOWN / UNSUPPORTED semantics with provenance. Unknown capacity is never interpreted as zero or infinite capacity.

### RDT-05 — Resource Provenance Binder
Every material resource fact can reference M07 discovery evidence, M08 empirical evidence, runtime observation and calibration lineage without transferring their authority into M09.

### RDT-06 — Headroom Covenant
Represents operator-configurable workstation headroom for VRAM/RAM/CPU-adjacent resource pressure. Headroom is a protected constraint, not spare capacity available to IRIS.

### RDT-07 — Commitment Conservation Engine
Tracks committed/reserved/resident/reclaimable quantities with conservation predicates so double counting, negative availability and phantom releases fail closed.

### RDT-08 — Resource Identity Namespace
Stable resource identities distinguish device, memory heap/tier, runtime/provider context and host scope. Device reorder, display name change or process restart cannot silently create a new resource identity.

### RDT-09 — Observation Reconciliation Fabric
Combines asynchronous observations without pretending they are simultaneous. Carries observation windows, skew, source priority and conflict evidence.

### RDT-10 — Staleness & Expiry Governor
Resource state has explicit freshness windows and invalidation triggers. Stale state cannot authorize a resource commitment that requires fresh evidence.

### RDT-11 — External Consumption Sentinel
Models memory/resource use not controlled by IRIS as external consumption with uncertainty. It must not kill, suspend or evict unrelated processes.

### RDT-12 — Scarcity Non-Degradation Firewall
Resource scarcity can yield WAIT / REJECT / REQUIRE_REPLAN / REQUIRE_OFFLOAD / UNKNOWN outcomes but cannot silently lower quality, fidelity, protected semantics or acceptance thresholds.

### RDT-13 — Resource Claim Algebra
Defines typed claim units, scopes, exclusivity/shareability, hard/soft reservation semantics and compatibility predicates that S02 can use for leases without embedding scheduler policy.

### RDT-14 — Snapshot Consistency Seal
Deterministic digest over canonicalized resource snapshot semantics and provenance refs. It is resource-state identity only, not M06 production identity.

### RDT-15 — Resource Event Causality Graph
Links observation and state-transition causes so later M10/M11/M56 consumers can explain why capacity changed without M09 taking their authorities.

### RDT-16 — Pressure Signal Normalizer
Normalizes provider/runtime pressure signals into typed evidence. It reports pressure; S01 does not predict OOM or thermal outcomes.

### RDT-17 — Reconciliation Quarantine
Conflicting or impossible observations enter quarantine and cannot become commitment-authorizing truth until reconciled or explicitly invalidated.

### RDT-18 — Resource Safety Envelope
Defines hard structural bounds for resource-state arithmetic and future control operations: no negative capacity, overflow, unbounded reservation, implicit overcommit, or authority-free mutation.

## S01 hard invariants
1. Every Resource Digital Twin snapshot is immutable once emitted.
2. Every snapshot has schema version, snapshot identity and observation timestamp/window.
3. Resource facts preserve source/provenance references.
4. Physical, reported, allocatable, reserved, committed, resident, reclaimable, external and unknown capacity remain semantically distinct.
5. Unknown is never coerced to zero.
6. Unknown is never coerced to unlimited capacity.
7. Estimated state is distinguishable from directly observed state.
8. Stale state is distinguishable from fresh state.
9. Conflicted state cannot authorize a fresh-only commitment.
10. Unsupported telemetry remains explicit.
11. Capacity arithmetic cannot produce negative available capacity.
12. Capacity arithmetic is overflow/bounds checked.
13. A release cannot free more commitment than its causal claim owns.
14. The same commitment cannot be counted twice.
15. Reconciliation cannot rewrite historical snapshots.
16. Every state transition identifies its causal predecessor(s).
17. Resource identity is independent of enumeration order.
18. Display-name changes do not silently change resource identity.
19. Runtime/process restart alone does not silently create new physical-resource identity.
20. Provider/runtime context identity remains distinct from physical device identity.
21. M07 discovery evidence is consumed by reference and not mutated.
22. M08 empirical evidence is consumed by reference and not reclassified as M09 observation.
23. M09 cannot emit M08 benchmark/capability-envelope authority.
24. M09 cannot compile an M10 execution plan.
25. M09 cannot claim predictive OOM authority.
26. M09 cannot claim thermal decision authority.
27. M09 cannot supervise/kill/restart M11 workers.
28. M09 cannot place jobs across M12 compute targets.
29. M09 cannot claim M14 model fitness.
30. M09 cannot become M55 physical storage authority.
31. M09 cannot replace M56 observability aggregation.
32. Operator-reserved headroom is never counted as IRIS allocatable capacity.
33. External consumption is represented even when ownership is unknown.
34. M09 cannot kill, suspend or evict unrelated external processes to reclaim capacity.
35. Scarcity cannot silently lower M01 quality thresholds.
36. Scarcity cannot silently weaken protected M03 semantics.
37. Scarcity outcome must be explicit and machine-readable.
38. A snapshot digest covers canonical semantic fields and provenance references.
39. Snapshot digest excludes nondeterministic serialization artifacts.
40. Conflicting observations produce conflict evidence.
41. Observation timestamps from different sources are not assumed simultaneous.
42. Reconciliation records source skew/window information where material.
43. Staleness policy is versioned.
44. Freshness requirements are purpose-sensitive and explicit.
45. State invalidation records reason and scope.
46. Invalidated state remains auditable.
47. Resource claims use typed units.
48. Unit conversion is explicit and loss-aware.
49. Claim scope identifies target resource/tier/context.
50. Claim exclusivity/shareability is explicit.
51. Hard and soft reservation semantics remain distinct.
52. S01 claim algebra cannot silently grant a lease.
53. Lease arbitration remains S02 authority.
54. Residency mutation remains S02 authority.
55. Spill/offload/prefetch execution remains S03 authority.
56. Tile/chunk/batch/precision control remains S04 authority.
57. Recovery/cleanup/leak-control actions remain S05 authority.
58. Pressure signals are evidence, not predictive OOM decisions.
59. Pressure normalization preserves original source/value/unit.
60. Impossible state enters quarantine rather than normalization-by-guess.
61. Quarantined state cannot authorize commitments.
62. Reconciliation from quarantine is explicit and auditable.
63. Resource-state mutation requires an authorized transition type.
64. No arbitrary executable callback is stored in canonical state.
65. Canonical state is provider-neutral.
66. Provider-specific fields remain versioned extension evidence.
67. Missing provider telemetry cannot fabricate measurements.
68. Synthetic fixtures are explicitly distinguishable from physical observations.
69. Test/synthetic state cannot masquerade as production resource truth.
70. 8 GB VRAM-class devices are valid first-class resources.
71. Small capacity alone is not an unsupported-device reason.
72. Multi-GPU state preserves per-device capacity and identity.
73. Host RAM and VRAM are not fungible without an explicit later transfer/offload contract.
74. NVMe/spill capacity is not counted as RAM or VRAM.
75. Reclaimable capacity is not equivalent to immediately free capacity.
76. Resident bytes are not automatically owned/evictable by IRIS.
77. Reserved bytes are not automatically resident bytes.
78. Committed bytes are not automatically physically allocated bytes.
79. External use uncertainty contributes to conservative availability.
80. Resource facts material to reproducibility require explicit M06 materiality reference, not implicit coupling.
81. Security/permission restrictions remain explicit when telemetry is unavailable.
82. Automation has the same authorization and provenance requirements as interactive control.
83. Resource state export is versioned.
84. Unknown mandatory schema semantics fail closed.
85. Older readers cannot silently ignore unknown mandatory resource semantics.
86. Every acceptance proof can identify the exact S01 invariant(s) exercised.
87. Shared proof targets explicitly enumerate all invariant IDs they claim.
88. Missing/orphan/duplicate invariant proof mappings fail validation.
89. Canonical invariant text drift requires a versioned planning amendment.
90. S01 implementation remains forbidden until the full M09 contract is frozen and independently approved.

## Required S01 proof classes
- deterministic snapshot serialization/digest;
- arithmetic conservation and bounds;
- unknown/stale/conflicted/quarantine behavior;
- provenance and identity stability;
- headroom/external-consumption semantics;
- cross-module authority firewall;
- claim algebra without lease grant;
- provider-neutral extension behavior;
- synthetic-vs-physical separation;
- invariant-to-proof integrity.

## S01 risks
- Driver/runtime telemetry may disagree or arrive at different times. Mitigation: reconciliation windows + conflict quarantine.
- “Free VRAM” can be misleading due to caches/reserved pools. Mitigation: capacity truth partition and conservative uncertainty.
- Overengineering S01 into a scheduler. Mitigation: claim algebra only; arbitration is S02 and execution planning is M10.
- Workstation usability can be destroyed by aggressive reclamation. Mitigation: protected headroom and no unrelated-process eviction.
- Resource scarcity can accidentally become a quality-degradation mechanism. Mitigation: explicit non-degradation firewall.

## S01 acceptance gate
S01 may advance to S02 planning only when:
- all 18 technology surfaces have explicit purpose/boundary/proof intent;
- all 90 invariants are present and non-contradictory;
- M07/M08/M10/M11/M12/M14/M55/M56 authority boundaries remain intact;
- 8 GB VRAM and operator headroom remain first-class;
- no implementation code is introduced;
- independent review reports zero unresolved HIGH/CRITICAL planning findings.

## STOP CONDITION
Stop at S01 planning. Do not implement M09. Do not deep-plan S02 until S01 receives independent review.
