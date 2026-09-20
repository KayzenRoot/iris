# M02 — Final Technology Review

Status: `APPROVED_FOR_CONTRACT_FREEZE`
Module: `M02 — Project OS & Production Graph`
Reviewed scope: S01–S05, EXT-M02-001..023, IRIS-PGX-001..096

## Verdict

M02 planning is internally coherent and sufficiently bounded for contract freeze.

The module establishes one domain-neutral semantic production substrate for:
- project/production/artifact identity;
- typed Production Graph causality;
- branching/variants/snapshots/rollback;
- incremental build/reuse semantics;
- promotion/release/archive lifecycle.

No external technology becomes a mandatory product authority.

## Existing technology disposition

### ACCEPTED_AS_REFERENCE / PATTERN
`EXT-M02-001..023`

These references inform architecture but do not become mandatory runtime dependencies merely because they were studied.

Key borrowed ideas:
- UUIDv7: decentralized sortable identity;
- Git: mutable refs over immutable history;
- Nix/Bazel/Buck2/DVC/Ninja: explicit inputs, DAGs, cache/incremental discipline;
- Temporal: durable/replayable execution history;
- Dagster: asset/materialization thinking;
- OpenUSD: layered composition/variants/film-scale collaboration;
- SCXML: explicit guarded/orthogonal state-machine semantics;
- Transformer KV/prefix caching: ephemeral context reuse.

## Internal candidate disposition

### ACCEPTED — M02 kernel/contract ownership
`PGX-001,002,003,005,006,007,008,009,011,012,013,014,015,017,018,019,020,021,022,023,024,025,026,027,028,029,030,031,032,033,034,035,036,037,038,039,040,041,042,043,044,045,046,047,048,049,050,051,052,053,054,056,057,069,073,074,075,076,077,078,079,080,081,082,083,084,085,086,091,092,093,094,095`

These concepts define or directly constrain M02 public semantics.

### ACCEPTED — contract in M02, implementation deepens in later owner module

- `PGX-010 Continuation Capsule` → M11 execution/recovery.
- `PGX-016 Dependency Truth Auditor` → M11/M16/provider adapters.
- `PGX-055 Layered Reuse Fabric` → M13/M55.
- `PGX-058 Cache Poisoning Shield` → M18/M54/M55.
- `PGX-059 Context Fingerprint Cache` → M52/M13.
- `PGX-060 Prefix/KV Compatibility Gate` → M13/model-provider runtime.
- `PGX-061 Provider Warmth Scheduler` → M09/M10/M13.
- `PGX-062 Variant Work Coalescer` → M10/M13.
- `PGX-063 Build Journal` → M11/M55 persistence.
- `PGX-064 Atomic Materialization Commit` → M55.
- `PGX-065 Incremental Truth Oracle` → M51.
- `PGX-066 Shadow Rebuild Sentinel` → M51/M13.
- `PGX-067 Differential Mutation Lab` → M51.
- `PGX-068 Cache Quarantine Circuit` → M13/M18/M54.
- `PGX-070 Adaptive Retention Value Model` → M13/M55.
- `PGX-071 Persona Production Prefix Cache` → M39/M43/M45/M52.
- `PGX-072 Token/Context Delta Compiler` → M52/provider runtime.
- `PGX-087 Archive Contract Manifest` → M53/M55.
- `PGX-088 Multi-Tier Archive Policy` → M51/M53/M55.
- `PGX-089 Archive Integrity Sentinel` → M55.
- `PGX-090 Reproducibility Horizon Tracker` → M14/M18/M55.
- `PGX-096 Persona Public Release Gate` → M39/M45/M46/M53.

M02 freezes the interface/invariant expected by these technologies but does not prematurely implement the later module internals.

### SUPERSEDED

- `PGX-004 Lifecycle State Lattice` → **SUPERSEDED_BY `PGX-074 Orthogonal Production State Vector`**.

S01 correctly identified the need for separate lifecycle machines; S05 refined it into an orthogonal versioned state vector that avoids a single overloaded state dimension.

No other candidate requires rejection at this stage.

## Composition decisions

### Identity
PGX-001/002/003/005/006/009/012 form one identity/receipt family. They remain separate concepts because stable semantic identity, materialization identity, aliases and transitions have different invariants.

### Invalidation
PGX-017/018/020/024/027/052 are complementary:
- facets/slices define dependency surface;
- causal fingerprint defines bound correctness identity;
- Impact Cone finds affected region;
- Dirty Frontier reduces work roots;
- Explain Trace proves why.

### Branching
PGX-030/031/033/036/041 are not duplicates:
- Branch is a movable work line;
- Snapshot is immutable closure;
- Variant is coexisting alternative;
- Merge combines histories;
- Rollback creates new history from an older snapshot.

### Reuse/cache
PGX-055/056/057/058 distinguish cache topology, trust, evidence and poisoning response. They must not collapse into one opaque “smart cache”.

### Lifecycle
PGX-074/075/076/077/078/079/080 separate state representation, transition compilation, promotion request, gate policy, freshness, evidence and attempt/production authority. This separation is retained.

## Required invariants carried to freeze

1. paths/names are never identity;
2. semantic identity, immutable revision/content and attempt identity remain separate;
3. Production Graph is provider-neutral and versioned;
4. material causality is acyclic per immutable graph revision;
5. all causal dependency surfaces are declared/admitted;
6. unknown/untrusted dependency state fails closed;
7. branch/variant/snapshot/rollback are distinct;
8. snapshots are immutable and structurally shared;
9. merge is semantic, not blind byte merge;
10. incremental correctness is never weaker than full-build truth;
11. stochastic generation is not falsely treated as byte-deterministic;
12. semantic cache reuse has explicit trust/admission;
13. M01 QualityDecision is first-class and cannot be bypassed;
14. attempt success never implies production acceptance;
15. ACCEPTED and RELEASED are distinct;
16. public/external side effects require idempotency/reconciliation semantics;
17. archive is evidence/retention/reproducibility state, not a folder;
18. current state is provable from immutable history;
19. persistent persona identity anchors are protected across variants/merges/releases;
20. later providers/storage/workers may implement M02 contracts but cannot redefine them.

## Novelty note

IRIS-PGX candidates are internal architecture/design candidates. This review makes no patentability, originality or prior-art novelty claim.

## Next gate

Proceed to M02 Forward Compatibility Scan.
