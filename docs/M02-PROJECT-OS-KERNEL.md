# M02 Project OS & Production Graph Kernel — implementation note

Work Order: `IRIS-WO-0004` · Frozen contract: `m02-contract-v1.0` · Schema: `iris-project-os-schema-v1`

This page documents the running code in `iris_project_os/`. It is an
implementation note, not a planning document: the normative wording stays in
`planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md` and
`planning/modules/M02-PROJECT-OS-PRODUCTION-GRAPH.md`.

## Shape

The kernel is one package of 22 modules, organised along the five frozen areas
plus the boundaries later modules implement. It runs no tool, imports no asset,
renderer, cloud, database or provider library, and holds no network call.

| Area | Module | Holds | Audience |
| --- | --- | --- | --- |
| — | `errors` | `ProjectOSError` and the sixteen typed failures below it (`GraphValidationError`, `SnapshotClosureError`, `MergeBlockedError`, `SideEffectFenceError`, `RollbackBlockedError`, `LifecycleError`, `PromotionBlockedError`, `ReleaseError`, `ArchiveError`, `PortContractError`, `StoreConflictError`, …) | every caller |
| — | `base` | `Record`, `Labeled`, `encode_payload`/`decode_nested`, `of`/`union` schema markers | every value object |
| — | `versions` | `ComponentVersion`, `CONTRACT_VERSION`/`SCHEMA_VERSION` and their supported sets, `canonical_json`, `content_digest`, the `require_*` guards, `require_quality_class` | kernel + callers |
| — | `limits` | the `MAX_*` resource bounds the kernel enforces on structures it cannot otherwise measure | every collection field |
| — | `machines` | `StateMachine`, `topological_order`, `closure_reachable` | lifecycle regions |
| A | `identity` | `EntityKind`, `ExternalRef`, `ProjectEnvelope`, `ProductionPassport`, `ArtifactIdentity`, `RevisionRef`, `AttemptIdentity`, `AliasRef`/`AliasLedger`, `LocatorRef`, `TransitionReceipt`, `SupersessionRef`/`SupersessionLedger`, `new_id`/`require_id`, the project and attempt lifecycles | every caller |
| B | `graph` | the typed immutable `GraphDefinition`/`GraphRevision`, `GraphNode`, `GraphEdge`, `SemanticPort`/`SemanticTypeRef`, `NodeRole`, `EdgeKind`, `DependencyFacet`/`DependencySlice`, `ReproducibilityClass`, `SideEffectClass`/`SideEffectPolicy`, `SubgraphInterface`, `GraphDelta`/`GraphMutation`, and the bound `MaterializationGraph`/`MaterializationRecord` | callers, providers |
| B | `analysis` | `FingerprintContext`, `CausalFingerprint`, `compute_fingerprint`, `Change`, `ImpactCone`, `impact_of`, `ExplainStep`, `DependencyDiscoveryReceipt`, `DependencyLedger` | build, callers |
| C | `branching` | `Branch`/`BranchRef`/`BranchLedger`, `ForkReceipt`, the variant ladder (`VariantSet`/`VariantOption`/`VariantConstraint`/`VariantSelection`), `resolve_selection`/`validate_selection`, `IdentityAnchorPolicy` + rulings, `RetentionPin` | callers |
| C | `snapshots` | `SnapshotClass`, `SnapshotClosureManifest`, `Snapshot`, `SnapshotStore`, `commit_snapshot`/`derive_snapshot`, `closure_obligations`, `plan_rollback`/`execute_rollback`, `retention_reasons`/`collectable_snapshots`, `ExternalSideEffect` | every caller |
| C | `diffing` | `DiffCategory`, `DiffEntry`, `SemanticDiff`, `semantic_diff` | merge, callers |
| C | `merge` | `ConflictKind`, `ResolutionStrategy`, `MergeConflict`, `MergeReceipt`, `three_way_merge`, `advance_merge`, `transplant` | callers |
| D | `build` | `BuildState`, `BuildDelta`, `compile_build_delta`, `DirtyFrontier`/`dirty_frontier`, `RepairFrontier`/`repair_frontier`, `BuildPlan`/`plan_build`, `IncrementalVerdict`/`verify_incremental`, `coalesce_variants`, `explain_build`, `ShadowAudit`/`audit_shadow_rebuilds` | callers |
| D | `reuse` | `CacheKey`/`CacheLayer`, `CacheEntry`, `ContextFingerprint`, `CacheTrust`, `Qualification`, `ReuseClass`, `admit_reuse` (the admission shield), `QuarantineLedger`, `evict` | build |
| E | `lifecycle` | `LifecyclePhase` and the orthogonal `Execution`/`Review`/`Release` conditions, `ProductionStateVector`, `TransitionProfile`/`AuthorizedJump`, `advance`, `Blocker`/`BlockerLedger`, `CompletionProfile`, `ProductionLedger`, `LIFECYCLE_TABLES` | callers |
| E | `promotion` | `GateKind`, `PromotionGate`, `GateResult`, `compile_gates`, `FreshnessBinding`, `HumanApproval`, `PromotionRequest`, `PromotionEvidenceBundle`, `admit_promotion`, `promote` | callers |
| E | `release` | `ReleasePhase`, `ExternalAction`, `RemoteState`, `ReleaseTransaction`/`ReleaseStep`, `begin_release`, `sync_release_state`, `WithdrawalReceipt`, supersession, `ReleaseLedger`/`ReleaseRegistry` | callers |
| E | `archive` | `ArchiveTier`, `ArchiveManifest`, `seal_archive`, `ObjectProbe`, `audit_archive` → `IntegrityReport`, `restore_archive` → `RestorationReport`, `revive_archive`, `CleanupPlan`, `ArchiveLedger`/`ArchiveRegistry` | callers |
| — | `ports` | the provider-neutral protocols and the opaque refs that cross them (`CapabilitySource`, `ProviderCompiler`, `DependencyObserver`, `MaterializationIngestor`, `RepairProvider`, `RightsProvenanceGate`, `ContextFingerprintSource`, `DeliveryProvider`, `PolicySource`, `IdentityAnchorSource`) plus `PortBoundary`/`describe_boundaries` | later modules |
| — | `stores` | `ArtifactRepository`, `SnapshotRepository`, `ReceiptRepository` protocols and the deterministic `InMemoryArtifactStore`/`InMemoryReceiptStore` references | callers, repositories |
| — | `serialization` | the versioned envelope (`ENVELOPE_KEYS`, `SERIALIZABLE_TYPES`), `dumps`/`loads`/`envelope`/`from_envelope`, `validate_payload` | storage, HIVE later |

`examples/m02_synthetic_profiles.py` and `tests/m02_kernel_support.py` sit
outside the package on purpose: domain vocabulary must never be reachable from
`iris_project_os/`. `tests/test_m02_domain_neutrality.py` enforces that boundary
mechanically, and `tests/test_m02_profiles.py` drives the five profiles through
every family.

## Public API

`iris_project_os.__all__` is derived at import from each module's own `__all__`
(399 names), not hand-copied. The two failure modes of a copied list are refused
at import: a name two modules claim as two different objects, and a module that
exports nothing. So the table above and the package cannot drift apart.

```python
from iris_project_os import (
    GraphDefinition, GraphNode, GraphEdge, SemanticPort,   # a typed definition
    MaterializationGraph, MaterializationRecord,           # bound to a real attempt
    commit_snapshot, Snapshot, SnapshotClass,              # an immutable closure
    ForkReceipt, VariantSet, VariantSelection, Branch,     # branches and variants
    three_way_merge, MergeReceipt, plan_rollback,          # history that can move
    compile_build_delta, dirty_frontier, plan_build,       # incremental rebuild
    admit_reuse, CacheKey, ContextFingerprint,             # the reuse shield
    advance, PromotionRequest, promote,                    # lifecycle and gates
    seal_archive, audit_archive, restore_archive,          # durable evidence
)
```

### Freezing one production

```python
graph = MaterializationGraph(revision=revision, materializations=records,
                             variant_selection=selection)
closure = SnapshotClosureManifest(
    project_id="iris", production_id=production, branch_id=branch, graph=graph,
    external_admissions=admitted, quality_decisions=decisions,   # M01's verdicts, by reference
    rights_refs=rights, provenance_refs=provenance, policy_refs=policies,
)
snapshot = commit_snapshot(closure, snapshot_class=SnapshotClass.VALIDATED_SNAPSHOT)
```

A `VALIDATED_SNAPSHOT` cannot be claimed unless the closure carries the material
behind it: every declared external input admitted, every materialized node
bound to an attempt **and** to an M01 quality decision, rights and provenance
present. `commit_snapshot` fails closed with the full set of missing items via
`closure_obligations`, so a reviewer sees every gap at once rather than one per
commit attempt.

## Invariants the kernel enforces

1. **A snapshot is a claim, and the claim is checked against the closure.**
   `SnapshotClass` is monotonic (`LOGICAL → MATERIALIZED → VALIDATED →
   RELEASE_READY`), and each rung's `requires_*` flags drive
   `closure_obligations`. Relabelling a thin closure as `VALIDATED` raises rather
   than silently over-claiming.
2. **History is walked, never edited.** `Snapshot` and the closure manifest are
   frozen; `derive_snapshot` returns a new object over a new closure digest and
   refuses to write into the one handed in. `ancestors_of`/`descendants_of` read
   the committed chain; there is no setter anywhere in the surface.
3. **Cycles are refused at the definition.** `GraphDefinition` rejects a material
   cycle (`cyclic dependency detected among nodes: [...]`) and an edge with no
   dependency facet (an unscoped dependency cannot be invalidated selectively),
   so incremental impact is always well-founded.
4. **Facets scope invalidation.** A change carries a `DependencyFacet`
   (`CONTENT`/`RIGHTS`/…), and `impact_of` propagates only along edges declaring
   that facet — a rights change sweeps the edge that admitted it, not the content
   downstream of it.
5. **Side effects are fenced.** A node marked `EXTERNAL_MUTATION` must declare an
   idempotency, compensation and retry policy at construction; an uncontrolled
   side effect is refused before anything runs.
6. **Variants are resolved, not guessed.** `validate_selection` reports unknown
   options and constraint violations as data; `resolve_selection` fills defaults.
   `VariantSet` refuses an anchor-protected set whose options declare no
   `anchor_digest`. A merge never silently picks a variant — a disagreement comes
   back as a typed `MergeConflict` (`ResolutionStrategy`), and only a clean
   one-sided change auto-resolves, recorded in `MergeReceipt.auto_resolved_subjects`.
7. **Reuse is admitted through a shield.** `admit_reuse` re-derives the
   `CacheKey` from the live `ContextFingerprint` and `CausalFingerprint`, checks
   `CacheTrust`, `Qualification` expiry, origin class and `PoisonCheck`, and
   returns a `ReuseRejection` rather than a receipt when any guard fails. A cache
   hit is a proven equivalence, never a stale guess.
8. **The lifecycle ladder has no skipping.** `advance` moves a
   `ProductionStateVector` one legal rung at a time; `DRAFT → MATERIALIZED`
   raises (`skips a rung with no transition profile`). `ACCEPTED` requires a
   promotion evidence bundle; the orthogonal execution/review/release conditions
   are tracked separately so a node can be `READY` to run yet `PENDING` review.
9. **Retention is proven, not assumed.** `collectable_snapshots` never returns a
   live head or anything a validated tip carries; a `RetentionPin` with an AUDIT
   or RIGHTS reason holds past its `expires_at_ms` (`may_release` stays false),
   while a pure `RETENTION_TTL` pin releases on schedule.
10. **An archive must be able to say where the work came from.**
    `seal_archive` refuses a closure with no provenance reference, requires the
    phase/claim the tier owes, and needs at least one `FINAL` asset and quality
    references. `audit_archive` marks unprobed required refs `UNVERIFIABLE`
    (which alone does not damage an archive), and `restore_archive` reports
    `DAMAGED`/`INTACT`/`UNKNOWN` rather than raising — revival is an
    engineering decision, not an exception.
11. **Unknown enums fail closed.** Parsing an unrecognised kind, state, event,
    edge, facet, conflict or gate raises rather than defaulting, so a stored
    record written by a newer module cannot be quietly reinterpreted.
12. **Untrusted sizes are bounded.** Every collection and text field is checked
    against the `limits.MAX_*` bounds at construction, so a hostile payload cannot
    make the kernel allocate without measure.

## M01 integration

Quality vocabulary is borrowed, never rebuilt. The ladder and the canonical JSON
form come from `iris_quality`, and `iris_project_os.versions.QualityClass` **is**
`iris_quality.contracts.QualityClass` (same object, asserted by the neutrality
test). The kernel touches exactly four M01 submodules — `contracts`, `decision`,
`errors`, `versions` — for that borrowed vocabulary and for checking a decision
reference. It never imports the judging machinery (`dimensions`, `evidence`,
`judging`, `registry`, `zones`) and never names `DecisionEngine`,
`EvaluatorRegistry`, `JudgeRequest`, `DomainProfile`, `DimensionRegistry` or
`SemanticZone`. A M02 `VALIDATED` claim carries M01 decision **references**;
M02 checks that they are bound, and never computes a score. M01 remains the sole
quality authority.

## Ports and stores

The provider-neutral boundaries are in `ports`: a real Blender/ComfyUI/cloud
provider implements `MaterializationIngestor`, `ProviderCompiler`,
`DependencyObserver`, `RepairProvider`, `RightsProvenanceGate`,
`ContextFingerprintSource`, `DeliveryProvider`, `PolicySource`,
`IdentityAnchorSource` and `CapabilitySource` from the outside and crosses via
opaque `PortBoundary` refs. `stores` says what a repository has to satisfy
(`ArtifactRepository`, `SnapshotRepository`, `ReceiptRepository`) and ships
deterministic in-memory references — it does not choose a database. Nothing in
the core imports either side's implementation.

## Five synthetic profiles

`examples/m02_synthetic_profiles.py` defines the five frozen §7 profiles —
`profile.logo-web`, `profile.game-asset`, `profile.film-sequence`,
`profile.spokesperson`, `profile.voice-music` — as `ProfileFixture` objects over
the same kernel. Each declares its own nodes, variant sets, constraints, identity
anchors and quality claim, and `tests/test_m02_profiles.py` runs all five through
the graph, identity, branch/variant/snapshot, diff/merge/rollback, build/reuse,
lifecycle/promotion and archive/retention families. The domains differ; the code
under test does not. This is the proof the kernel is domain-neutral rather than
one profile generalised — and `test_m02_domain_neutrality.py` asserts that the
core never names any identifier those fixtures introduce.

## Design decisions inside the freeze

- **The package surface is derived, not copied** (see Public API), because a
  hand-listed ~390-name `__all__` is a second API that drifts invisibly.
- **`closure_obligations` returns blockers instead of raising** so `commit_snapshot`
  can report the whole set of missing evidence at once; the raise happens once at
  the `Snapshot` boundary.
- **Variant merge canonicalises against the axis default** (`_merge_selection`),
  so an effective choice is asserted through `resolve_selection` rather than read
  off raw pairs that a default might have dropped.
- **`restore_archive` never raises on damage**, returning a `RestorationReport`
  with the lost/blocked/rights-held objects, because "can we get the work back"
  is a decision to inform, not a failure to throw.
- **The three module-level tables (`LIFECYCLE_TABLES`, `REQUIRED_GATES`,
  `EVIDENCE_KINDS`) are annotated `Mapping`**, i.e. frozen lookup tables, not the
  mutable global registries §11 forbids; the neutrality test allows a declared
  immutable annotation and rejects a bare mutable singleton.

## What M02 deliberately does not do

No Blender, ComfyUI, DreamSim/FLIP, WebGPU or model-provider calls; no game,
web, film, spokesperson or music engine; no CV or numeric library (no numpy, PIL,
cv2, torch); no HTTP, database, object-store, cloud, container or Kubernetes SDK;
no HIVE mutation; no M01 quality decision of its own; no UI. The five profiles in
`examples/` are fixtures with arithmetic stand-ins; the real providers that will
replace them arrive in later modules through the ports above. This branch does not
merge and does not start M03.
