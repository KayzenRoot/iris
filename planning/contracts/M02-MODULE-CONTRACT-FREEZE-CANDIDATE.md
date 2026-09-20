# M02 — Module Contract Freeze Candidate

Status: `FROZEN_APPROVED`
Version: `m02-contract-v1.0`
Module: `Project OS & Production Graph`

## 1. Contract purpose

Freeze the domain-neutral semantic kernel required to represent and reason about IRIS productions before later provider/storage/domain modules are implemented.

M02 is NOT a workflow runner, DCC adapter, CAS implementation, legal engine, media generator or publishing provider.

## 2. Required public concepts

### Identity / history
- ProjectIdentity / ProjectEnvelope
- ProductionPassport
- ArtifactIdentity
- RevisionRef
- AttemptIdentity
- AliasRef / LocatorRef
- TransitionReceipt
- SupersessionRef

### Production Graph
- GraphDefinition / GraphRevision
- GraphNode
- SemanticPort
- GraphEdge
- EdgeKind
- DependencyFacet
- DependencySelector/Slice
- ReproducibilityClass
- SideEffectClass
- CausalFingerprint
- ImpactCone
- DependencyDiscoveryReceipt
- SubgraphInterface

### Branching / snapshots
- Branch
- VariantSet / VariantSelection
- VariantConstraint
- Snapshot
- SnapshotClass
- SnapshotClosureManifest
- SemanticDiff
- MergeConflict / ConflictKind
- MergeReceipt
- ProductionDelta / GraphDelta
- RollbackReceipt
- RetentionPin

### Build
- BuildDelta
- BuildState
- WorkDisposition
- DirtyFrontier
- RepairFrontier
- ReuseClass
- ReuseReceipt
- BuildPlan
- BuildExplainTrace

### Lifecycle / promotion
- ProductionStateVector
- LifecyclePhase
- ExecutionCondition
- ReviewCondition
- ReleaseCondition
- PromotionRequest
- PromotionGate / GateKind / GateResult
- PromotionEvidenceBundle
- ReleaseTransaction state
- ArchiveManifest / ArchiveTier
- Blocker
- CompletionProfile

Exact class names may adapt to repository conventions, but these semantics must exist.

## 3. Hard invariants

1. display names, paths and aliases are never canonical identity;
2. semantic object ID != content/revision ID != attempt ID;
3. immutable historical records are not rewritten;
4. graph revisions are immutable and material causality is acyclic;
5. providers cannot silently introduce undeclared material dependencies;
6. unknown/untrusted dependency or gate state fails closed;
7. Definition Graph is distinct from provider Execution Plan;
8. ports/edges are typed and provider-neutral;
9. one revision/materialization has unambiguous producer provenance;
10. branch refs may move; snapshots never mutate;
11. variants are not branches;
12. persona protected identity anchors cannot mutate through ordinary variants;
13. rollback creates new history;
14. merge conflicts are typed and blocking conflicts prevent head advancement;
15. incremental plan cannot be less correct than admitted full-build semantics;
16. stochastic nodes do not claim exact replay from fingerprint equality;
17. semantic reuse requires explicit reuse class/admission;
18. cache/warm-state loss changes performance, not production truth;
19. M01 QualityDecision is a first-class graph/promotion gate;
20. attempt success never directly promotes Production ACCEPTED;
21. ACCEPTED != RELEASED;
22. external mutation has explicit idempotency/reconciliation semantics;
23. stale gate evidence is invalidated by relevant causal changes;
24. archive completeness is a manifest/evidence claim, not a filesystem location;
25. current state is reconstructable from immutable receipts;
26. duplicate transition/release commands are idempotent or detectably conflicting;
27. HIVE is derived context, not canonical production state;
28. later modules may implement extension ports but cannot redefine M02 semantics.

## 4. Domain neutrality

The implementation must prove the same kernel can model at least:
1. logo/web/vector production;
2. Nerim/isometric 3D asset production;
3. film/shot production;
4. persistent corporate spokesperson episode/campaign;
5. non-visual voice/music production.

No core type may require visual-only fields.

## 5. M01 integration

M02 must integrate with the implemented M01 Quality Kernel through explicit references/values:
- Fidelity Contract / QualityClass;
- QualityDecision;
- human-review requirements;
- quality evidence freshness.

M02 MUST NOT reimplement the M01 judging engine.

## 6. Extension-port boundary

M02 defines interfaces/opaque refs sufficient for:
- semantic IR type registry;
- policy/Fidelity Contract;
- identity-anchor policy;
- execution capability;
- provider compilation;
- dependency observation;
- materialization ingestion;
- repair;
- storage;
- rights/provenance;
- context fingerprint source;
- delivery/publishing.

No real Blender/ComfyUI/cloud/database/provider runtime is required in M02 implementation.

## 7. Persistence boundary

M02 may provide deterministic serialization/schema/versioning and in-memory/reference repository implementations for tests.

Production-grade CAS/database/distributed storage mechanics belong to M55/M06.

The M02 implementation must not hardcode a database vendor.

## 8. M06 ownership boundary

M06 MUST consume M02 contracts for revision/state/build semantics.

M06 may deepen:
- content-addressed persistence;
- dependency indexes;
- reconstruction;
- cleanup;
- rollback execution.

It may not introduce a competing second branch/snapshot/lifecycle model.

## 9. Required behavior

Implementation must support:
- stable identity generation/roundtrip;
- legal/illegal lifecycle validation;
- typed DAG construction/cycle rejection;
- typed port/edge validation;
- dependency facets/selectors;
- impact-cone/explain trace calculation;
- immutable branch/snapshot/fork/rollback records;
- variant constraint validation;
- semantic three-way merge/conflicts;
- build delta/dirty frontier/work disposition;
- causal fingerprint canonicalization;
- reuse-class admission model;
- promotion gate/state-vector validation;
- receipt-based state replay;
- archive manifest validation.

Heavy provider execution is out of scope.

## 10. Acceptance tests

At minimum:
- rename/move identity stability;
- same bytes/different semantic artifact;
- immutable revision lineage;
- cycle rejection;
- hidden/unknown dependency fail-closed;
- facet/slice invalidation;
- graph serialization determinism;
- branch/fork/snapshot immutability;
- variant constraint + persona protected-anchor guard;
- semantic merge conflict cases;
- rollback preserves intervening history;
- build dirty frontier and work disposition;
- cache/reuse trust classification;
- deterministic vs stochastic replay semantics;
- M01 quality gate integration;
- orthogonal state-vector invariants;
- attempt success cannot ACCEPT;
- gate freshness invalidation;
- release idempotency/reconciliation state;
- archive completeness/integrity contracts;
- receipt replay equals projected current state;
- five synthetic domain profiles listed in §4.

Property-based testing is preferred if already supported; otherwise exhaustive/table-driven and mutation-style state/graph tests are acceptable without unjustified dependency expansion.

## 11. Out of scope

- real worker/process scheduling;
- real Blender/ComfyUI execution;
- real media/model generation;
- production database/CAS implementation;
- cloud/LAN distribution;
- real provider KV cache;
- real HIVE retrieval;
- real rights/legal engine;
- actual C2PA signing;
- actual publishing APIs;
- M03+ domain implementation.

## 12. Evidence obligations

Executor must record:
- base/head SHA;
- exact changed files;
- design decisions;
- full test/lint/typecheck/build results;
- state/graph mutation coverage;
- proof no provider/database vendor leaked into core;
- proof five synthetic domains use same kernel;
- proof M01 integration does not bypass Quality Kernel;
- risks/deferred ports;
- proposed Checkpoint Delta.

## 13. STOP CONDITION

STOP after the complete M02 domain-neutral semantic kernel is implemented, tested, documented, committed/pushed and its PR + Evidence Bundle are ready for independent review.

DO NOT merge.
DO NOT start M03.
DO NOT implement later-module providers simply to satisfy an interface.
If the contract cannot be implemented without changing a frozen M02 invariant, report BLOCKED rather than weakening it.


## 14. Freeze evidence

- Final Technology Review: `APPROVED_FOR_CONTRACT_FREEZE`.
- Forward Compatibility Scan: `PASS_WITH_EXTENSION_PORTS`.
- Planning audit head: `935669fa851eec55489877e4697e46a34760c067`.
- Governance run: `35535628768` — SUCCESS.
- Exact-head checkout: PASS.
- Governance validation: PASS.
- Required artifacts: 35.
- Existing repository suite: 216 tests, OK.
- Planning diff: 14 documentation/planning files, zero product-code files at audit head.
- M06 overlap: resolved by explicit ownership boundary.
- Public spokesperson/film/commercial/music scope: explicitly carried in PR-017/PR-018 and canonical product direction.

Any semantic change to a frozen invariant after this point requires a versioned contract amendment plus renewed Forward Compatibility Scan.
