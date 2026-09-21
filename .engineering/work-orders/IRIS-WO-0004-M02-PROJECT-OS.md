# IRIS-WO-0004 — M02 Project OS & Production Graph Kernel

Status: `COMPLETED_APPROVED`
Risk: `ELEVATED`
Frozen contract: `m02-contract-v1.0`
Authorized base: `59ee339c27750522106d0d2aa5a525f07f613702`
Issue: `#11`
Branch: `iris-wo-0004-m02-project-os`

## OBJECTIVE

Implement the complete domain-neutral semantic kernel frozen by M02 without implementing later-module runtimes.

The implementation must make IRIS capable of representing, validating, diffing, merging, incrementally planning and governing a production from stable identity through release/archive semantics while remaining provider-neutral.

## SOURCES TO READ — ORDER

1. `.engineering/SOURCE-HIERARCHY.md`
2. `.engineering/REVIEW-AUTOFIX-POLICY.md`
3. `docs/project-brain/13-CHECKPOINT.md`
4. `docs/project-brain/16-DECISIONS-LEDGER.md`
5. `docs/project-brain/03-SCOPE.md`
6. `docs/project-brain/15-DEFINITION-OF-DONE.md`
7. `docs/project-brain/04-ARCHITECTURE.md`
8. `docs/project-brain/02-REQUIREMENTS.md`
9. `planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md`
10. `planning/compatibility/M02-FORWARD-COMPATIBILITY-SCAN.md`
11. `planning/modules/M02-PROJECT-OS-PRODUCTION-GRAPH.md`
12. `planning/reviews/M02-FINAL-TECHNOLOGY-REVIEW.md`
13. `planning/technology-registry/M02-TECHNOLOGIES.md`
14. `docs/product/IRIS-VIRTUAL-SPOKESPERSON-DIRECTION.md`
15. existing M01 implementation (`iris_quality/`) and repository tests/tooling.

Do not implement from this Work Order alone. The frozen repository contract is canonical.

## IMPLEMENTATION BOUNDARY

Implement M02 semantics only.

### A. Identity and immutable history
Support:
- stable project/production/artifact/attempt identities;
- aliases/locators separated from identity;
- immutable revision references;
- transition receipts;
- supersession references;
- deterministic serialization/versioning.

Use a standards-compliant UUIDv7 implementation if the current Python/runtime supports it directly; otherwise implement a bounded tested UUIDv7-compatible generator without adding an unjustified dependency. Timestamp order is not causal authority.

### B. Typed Production Graph
Implement:
- immutable/versioned graph definition;
- typed nodes/ports/edges;
- dependency edge kinds;
- dependency facets and selector/slice contracts;
- causal-cycle rejection;
- subgraph interface semantics;
- reproducibility and side-effect classes;
- causal fingerprints;
- impact-cone calculation;
- explain traces;
- dynamic-dependency discovery/admission records.

Do not implement Blender/ComfyUI/provider execution.

### C. Branches, variants, snapshots and rollback
Implement:
- mutable branch refs over immutable snapshots;
- typed Variant Sets and constraints;
- sparse/lazy variant semantics as planning data;
- Snapshot classes + Closure Manifest;
- semantic diff;
- three-way semantic merge and typed conflicts;
- experiment branch metadata;
- semantic delta transplant/cherry-pick-like semantics;
- rollback as new history;
- reachability/pin semantics;
- persona protected-anchor guard hook.

No real CAS/storage engine is required; use provider-neutral stores/interfaces and deterministic in-memory/reference implementations for tests when necessary.

### D. Incremental build semantics
Implement:
- Build Delta;
- CLEAN / DIRTY / UNKNOWN / BLOCKED / CACHED_ELIGIBLE / REVALIDATE_ONLY / REPACKAGE_ONLY state semantics;
- REBUILD / REPAIR / REVALIDATE / REPACKAGE / REUSE / BLOCK dispositions;
- Dirty Frontier;
- Repair Frontier contract;
- reuse classes and Reuse Receipt;
- Build Plan / Explain Trace;
- context-fingerprint contract and opaque cache/provider compatibility refs;
- incremental/full truth semantics.

Do not implement real KV cache, GPU cache, model residency or HIVE retrieval.

### E. Production lifecycle, promotion and archive
Implement:
- orthogonal Production State Vector;
- lifecycle/execution/review/release conditions;
- legal transition compiler/validator;
- Promotion Request;
- typed Promotion Gates;
- stale-gate/freshness invalidation hooks;
- Promotion Evidence Bundle;
- release transaction state semantics;
- external-state UNKNOWN/reconciliation semantics;
- withdrawal/recall;
- supersession resolver;
- archive manifest/tier contracts;
- revival fork semantics;
- state replay;
- transition idempotency;
- completion profile;
- cross-state invariant guard.

No real publishing API, legal engine or cold-storage provider.

## M01 INTEGRATION

Use the existing `iris_quality` package as the quality authority.

M02 may reference/consume:
- FidelityContract / QualityClass;
- QualityDecision;
- quality evidence / human-review state.

M02 MUST NOT:
- duplicate M01 evaluator/judge logic;
- create an alternate quality score;
- infer acceptance from a process exit code;
- bypass M01 gate semantics.

Tests must prove an under-qualified QualityDecision cannot satisfy a higher production promotion requirement.

## REQUIRED EXTENSION BOUNDARIES

Expose provider-neutral contracts/opaque references sufficient for later:
- SemanticType / IR schema registry;
- identity-anchor policy;
- execution/worker capability;
- provider compiler;
- dependency observer;
- materialization ingestor;
- repair provider;
- Artifact/Snapshot/Receipt stores;
- rights/provenance gate provider;
- HIVE/context fingerprint source;
- delivery/publishing provider.

Do not implement those providers now.

## M06 OWNERSHIP RULE

M02 is semantic authority.

M06 may later deepen:
- content-addressed persistence;
- dependency indexes;
- reconstruction;
- cleanup;
- rollback execution.

This Work Order MUST NOT create an architecture that forces M06 to invent a competing branch/snapshot/state/build model.

## FIVE REQUIRED SYNTHETIC PROFILES

Implement fixtures/examples/tests proving the same kernel can model:

1. **Logo / web / vector**
   - master logo;
   - favicon variant;
   - Web3D treatment;
   - quality/delivery gates.

2. **Nerim / isometric 3D asset**
   - character;
   - material/rig/animation chain;
   - gameplay-view validation;
   - LOD/export variant.

3. **Film / shot production**
   - multiple shots;
   - local repair;
   - continuity/evidence;
   - accepted master/release.

4. **Persistent corporate spokesperson**
   - stable persona identity;
   - outfit/language/campaign variants;
   - protected face/voice anchor;
   - episode branch/snapshot;
   - public-release gate refs.

5. **Non-visual voice/music**
   - same graph/snapshot/lifecycle kernel;
   - no visual-only required core fields.

These are semantic contract fixtures. No real generation/inference is required.

## HARD INVARIANTS

All 28 invariants from the frozen contract are mandatory.

Especially:
- names/paths are not identity;
- semantic ID != content/revision != attempt;
- history is immutable;
- causal graph revision is acyclic;
- undeclared/unknown material dependency fails closed;
- providers cannot silently mutate frozen graph revisions;
- branch != variant != snapshot != rollback;
- persona identity anchors cannot drift through ordinary variants;
- rollback creates new history;
- incremental correctness cannot be weaker than admitted full-build truth;
- stochastic fingerprint equality does not imply byte determinism;
- semantic cache reuse requires explicit trust class;
- QualityDecision is a first-class gate;
- attempt success never means ACCEPTED;
- ACCEPTED != RELEASED;
- external mutations require idempotency/reconciliation;
- archive is evidence/retention state, not a folder;
- current state is replayable from receipts;
- duplicate commands are idempotent or conflicting;
- HIVE is derived context.

## ARCHITECTURE RULES

- Inspect repository before choosing package layout.
- Prefer a separate domain-neutral M02 package rather than mixing state semantics into `iris_quality`.
- Preserve stdlib-only posture unless a dependency is objectively necessary and explicitly justified in evidence.
- Immutable/value-object style where practical.
- Canonical serialization must be deterministic.
- Validate schema versions strictly.
- Reject unknown enums/state/event/edge/facet/conflict/gate kinds by default.
- Bound collection sizes and extension metadata where untrusted input could create resource abuse.
- No hidden network dependency in tests.
- No global mutable registry/singleton for semantic authority.
- Error messages must be actionable.
- Avoid provider/database/DCC SDK imports in the M02 kernel.

## REQUIRED TEST FAMILIES

At minimum:

### Identity/history
- rename/move does not change semantic identity;
- same bytes can represent different semantic artifacts;
- one artifact can have multiple immutable revisions;
- retry creates new attempt;
- transition serialization/round-trip;
- idempotent duplicate transition vs conflicting duplicate.

### Graph
- material cycle rejection;
- legal previous-epoch feedback;
- port type/cardinality mismatch;
- edge-kind behavior;
- facet/slice invalidation;
- dynamic dependency admission/fail-closed;
- producer exclusivity;
- deterministic causal fingerprint;
- irrelevant metadata excluded from fingerprint;
- explainable impact cone.

### Branch/variant/snapshot
- branch rename stability;
- exact fork point;
- immutable snapshot;
- invalid variant constraint;
- sparse variant semantics;
- persona anchor guard;
- Snapshot completeness classes;
- semantic three-way merge;
- typed merge conflicts;
- unresolved conflict blocks head move;
- rollback creates new snapshot and preserves intervening history;
- retention pin/reachability.

### Build/reuse
- UNKNOWN never treated CLEAN/reusable;
- quality-only delta can REVALIDATE;
- provenance/delivery-only delta can REPACKAGE;
- Repair Frontier semantics;
- reuse trust ladder;
- poisoned/untrusted cache metadata rejected at semantic admission layer;
- deterministic vs stochastic reuse rules;
- context fingerprint mutation;
- build explanation trace.

### Lifecycle/promotion/archive
- orthogonal state invariants;
- illegal transition fails;
- attempt success cannot ACCEPT;
- blocking UNKNOWN gate prevents promotion;
- stale gate invalidation;
- required human review;
- ACCEPTED without RELEASED is legal;
- RELEASED without accepted Release Snapshot is illegal;
- ambiguous external release becomes reconciliation-required;
- withdrawal preserves history;
- supersession exact-vs-latest behavior;
- archive manifest completeness;
- legal/golden pins;
- revival creates new lineage;
- receipt replay equals projected current state;
- Completion Profile semantics.

### Integration/regression
- all five synthetic profiles;
- existing M01 tests unchanged/green;
- repository Governance;
- compile/lint/typecheck/build as configured.

Prefer property/state-machine tests where supported without unjustified dependency expansion; otherwise exhaustive table-driven + mutation/adversarial fixtures.

## SECURITY / TRUST TESTS

Include adversarial cases for:
- path/alias confusion;
- identifier collision/forgery attempts;
- unknown schema/event/kind;
- cycle/resource-explosion graphs;
- malicious huge metadata/variant/edge sets within realistic bounded limits;
- stale gate/cache evidence;
- untrusted extension fields;
- side-effect retry ambiguity;
- protected persona-anchor mutation;
- archive/replay tampering.

## DELIVERABLES

- production M02 kernel code;
- tests/fixtures/examples;
- API/internal architecture documentation;
- Evidence Bundle at `.engineering/evidence/IRIS-WO-0004.json`;
- updated Context Lock if only allowed deltas are needed;
- proposed Checkpoint Delta;
- implementation commit(s);
- pushed branch;
- PR linked to Issue #11.

## EVIDENCE BUNDLE

Record:
- exact base/head;
- files changed;
- design decisions;
- test totals;
- compile/lint/typecheck/build commands/results;
- failures encountered/fixed;
- scope deviations;
- dependency changes;
- proof no DCC/provider/database SDK leaked into M02 core;
- proof M01 remains quality authority;
- proof five synthetic profiles;
- risks/deferred future-module ports;
- STOP CONDITION.

## REVIEW FORMAT

Return in Brazilian Portuguese:
- what was implemented;
- architecture chosen;
- exact tests/results;
- files changed;
- deviations/risks;
- commit/PR IDs;
- Evidence Bundle location;
- STOP CONDITION result.

## REVIEW CLOSURE

Verdict: `APPROVED`

- Reviewed head: `3e439f404a16cbf5d1652296c93160519ff4d0b6`
- Governance run/job: `35596394803 / 106322077536`
- Exact-head suite: `1805/1805 OK`
- Review corrections: `CHAT_FIXABLE`, completed on the same branch/PR without contract weakening.
- CRITICAL/HIGH blockers at approval: `0`
- M03 status at approval: not started.
- Promotion delta: governance/documentation only; requires exact-head CI before merge.

## STOP CONDITION

STOP only after the full M02 semantic kernel is implemented, tested, documented, committed/pushed, PR + Evidence Bundle are ready for independent review, and exact-head CI/Governance has been requested or completed according to repository workflow.

DO NOT MERGE.
DO NOT START M03.
DO NOT implement real later-module providers/runtimes.
If a frozen invariant cannot be satisfied without semantic contract change, report `BLOCKED_CONTRACT_CONFLICT` instead of weakening it.
