# IRIS 1.0 — M02 Technology Registry

Status: `S01_PROPOSED_FOR_DISCUSSION`
Module: `M02 — Project OS & Production Graph`
Rule: internal/proprietary candidates are design candidates only. No novelty or patentability claim is made before prior-art review.

# Existing technology / pattern foundation

## EXT-M02-001 — RFC 9562 UUIDv7
**Type:** existing standard / identity.
**What it does:** defines time-ordered UUIDv7 using Unix-epoch milliseconds plus uniqueness bits.
**How IRIS may use it:** default ID form for project, production, attempt, artifact, graph and transition identities created locally.
**Why useful:** decentralized generation, sortable creation locality and no central ID allocator.
**Risk:** timestamps are not trustworthy event ordering by themselves; clock anomalies remain possible.
**Proof:** collision/concurrency tests, serialization and clock-skew handling.
**Status:** REFERENCE_ACCEPTED_FOR_S01.

## EXT-M02-002 — Git object/commit identity model
**Type:** existing / immutable history pattern.
**What it does:** separates mutable refs/names from immutable content-addressed objects and commits.
**How IRIS uses the pattern:** aliases and friendly names remain mutable while durable lineage points to stable immutable records.
**Risk:** Git semantics are not a complete media-production lifecycle.
**Proof:** rename/move/supersession tests.
**Status:** PATTERN_ACCEPTED_FOR_S01.

## EXT-M02-003 — Nix derivations and immutable store
**Type:** existing / reproducible-build pattern.
**What it does:** models builds as derivations over explicit inputs and stores outputs under immutable dependency-derived identities.
**How IRIS uses the pattern:** inspiration for reproducible production receipts, immutable revisions and later content-addressed/cached rebuilds.
**Risk:** IRIS media workflows can include nondeterministic models/hardware paths, so Nix purity cannot be copied literally.
**Proof:** explicit-input lineage and reproducibility-class tests.
**Status:** PATTERN_ACCEPTED_FOR_M02.

## EXT-M02-004 — Bazel action/dependency graph
**Type:** existing / incremental-build pattern.
**What it does:** builds an action graph from declared inputs/dependencies, computes action keys and reuses cached outputs when relevant inputs/actions are unchanged.
**How IRIS uses the pattern:** inspiration for declared causal dependencies, later impact cones and incremental media rebuild.
**Risk:** media graphs have probabilistic generators and human decisions that normal software build graphs do not.
**Proof:** declared-vs-actual dependency audits and selective/full rebuild equivalence.
**Status:** PATTERN_ACCEPTED_FOR_M02.

## EXT-M02-005 — Temporal durable workflow execution
**Type:** existing / durable-workflow pattern.
**What it does:** persists workflow history so long-running workflows can resume after process/infrastructure failures.
**How IRIS uses the pattern:** inspiration for durable production continuation, retries and attempt history without relying on one worker process.
**Risk:** adopting Temporal itself would add a service/runtime dependency; M02 currently adopts the semantics, not the product.
**Proof:** crash/resume/retry state-machine tests.
**Status:** PATTERN_ACCEPTED_FOR_M02.

## EXT-M02-006 — Dagster software-defined assets / asset graph
**Type:** existing / asset-centric orchestration pattern.
**What it does:** declares persistent assets, upstream dependencies, lineage and desired-state materialization/reconciliation.
**How IRIS uses the pattern:** inspiration for artifact-centric production rather than task-only orchestration.
**Risk:** Dagster targets data workflows and is not a media/DCC production engine.
**Proof:** compare asset-centric vs task-centric modeling on IRIS production cases.
**Status:** PATTERN_ACCEPTED_FOR_M02.

## EXT-M02-007 — OpenUSD composition, variants and payloads
**Type:** existing / non-destructive composition pattern.
**What it does:** composes scene descriptions through references, payloads, variants and layered opinions with dependency/change processing.
**How IRIS uses the pattern:** inspiration for non-destructive production variants and lightweight interfaces to heavy assets.
**Risk:** USD is a scene-description system, not the universal IRIS project database.
**Proof:** later M02/M25 tests mapping IRIS variants/assets to USD without leaking USD semantics into the universal core.
**Status:** PATTERN_ACCEPTED_FOR_M02.

# Internal technology candidates — S01

## IRIS-PGX-001 — Project Identity Envelope
**Purpose:** give every IRIS project a stable machine identity independent of folder/name/UI.
**How it works:** a versioned envelope binds project_id, domain/profile refs, canonical policy refs, created_at, root graph ref and alias metadata. Mutable presentation fields are separated from identity fields.
**Benefit:** projects survive rename, move, clone/export and future local/cloud execution.
**Dependencies:** repository/project manifest, M52 HIVE context namespace.
**Risk:** envelope schema creep.
**Proof:** rename/move/round-trip tests.
**Status:** PROPOSED.

## IRIS-PGX-002 — Identity Triad
**Purpose:** stop semantic identity, content identity and execution identity from being confused.
**How it works:** every produced object can expose three independent references: semantic ID, immutable revision/content digest, and producing attempt ID.
**Benefit:** enables safe cache/dedup while preserving meaning and provenance.
**Dependencies:** M55 CAS, M53 provenance.
**Risk:** more identifiers can confuse API consumers.
**Proof:** same-bytes/different-artifact and same-artifact/multiple-revision tests.
**Status:** PROPOSED.

## IRIS-PGX-003 — Production Passport
**Purpose:** make a production request durable and auditable.
**How it works:** a production_id binds project_id, immutable intent snapshot, requested outputs, graph/version, quality contract refs, supersession lineage and creation reason.
**Benefit:** a job can resume or be re-planned without relying on transient UI/session context.
**Dependencies:** M03 brief compiler, M04 IR, M52 HIVE.
**Risk:** passport may become too heavy if runtime telemetry is embedded rather than referenced.
**Proof:** deterministic passport serialization + resume-from-repository fixture.
**Status:** PROPOSED.

## IRIS-PGX-004 — Lifecycle State Lattice
**Purpose:** define legal lifecycle transitions without one giant ambiguous status field.
**How it works:** separate state machines for Project, Production and Attempt, with typed legal transitions and exceptional states.
**Benefit:** failed attempts do not corrupt production state; archiving a project is not confused with releasing an artifact.
**Dependencies:** Transition Receipt, M11 workers.
**Risk:** state explosion.
**Proof:** exhaustive transition-table tests and unreachable-state analysis.
**Status:** PROPOSED.

## IRIS-PGX-005 — Transition Receipt
**Purpose:** make every lifecycle mutation independently auditable/replayable.
**How it works:** every transition emits immutable from/to state, entity, reason, actor, causal parent, policy version and evidence refs.
**Benefit:** crash recovery, audit, debugging and HIVE context can rely on facts rather than inferred logs.
**Dependencies:** provenance/event storage, later M55.
**Risk:** receipt volume.
**Proof:** replay state from receipts; reject tampered/out-of-order transitions.
**Status:** PROPOSED.

## IRIS-PGX-006 — Alias & Rename Shield
**Purpose:** protect lineage from filenames, DCC names, slugs and folder movement.
**How it works:** friendly aliases resolve to stable IDs through versioned mappings; old aliases may retire but never rebind silently to another live identity.
**Benefit:** artists/developers can reorganize projects without breaking graphs/cache/history.
**Dependencies:** Project Identity Envelope, locator service.
**Risk:** alias ambiguity and stale external links.
**Proof:** rename/move/case-collision tests.
**Status:** PROPOSED.

## IRIS-PGX-007 — Intent Lineage Seal
**Purpose:** bind the “why” of production to the production identity.
**How it works:** the normalized creative intent/constraint snapshot receives a digest/ref stored in the Production Passport; later graph/materialization changes can identify which intent version they satisfy.
**Benefit:** prevents a later output from being mistaken for evidence of an older/different brief.
**Dependencies:** M03 Intent Compiler, M04 IR.
**Risk:** normalization mistakes could change digest without semantic change.
**Proof:** canonicalization and semantically-relevant delta tests.
**Status:** PROPOSED.

## IRIS-PGX-008 — Supersession & Tombstone Ledger
**Purpose:** prevent deletion/overwriting from erasing production history.
**How it works:** obsolete entities point to replacement/superseding refs; governed deletion leaves a minimal tombstone where policy permits.
**Benefit:** old links, provenance and HIVE memories can explain what happened.
**Dependencies:** M53 rights/privacy, M55 retention/archive.
**Risk:** retention/privacy obligations may require true erasure.
**Proof:** supersession traversal + policy-driven redaction/deletion tests.
**Status:** PROPOSED.

## IRIS-PGX-009 — Universal Production Locator
**Purpose:** create stable internal references across local paths, DCCs and future remote nodes.
**How it works:** canonical URI-like locators resolve semantic IDs, e.g. project/production/artifact/revision, while filesystem/network locations remain replaceable resolution targets.
**Benefit:** graphs and HIVE context stop embedding Windows paths as identity.
**Dependencies:** locator/resolver layer, M12 distributed compute.
**Risk:** premature URI grammar can become rigid.
**Proof:** round-trip parsing, relocation and ambiguous-alias tests.
**Status:** PROPOSED.

## IRIS-PGX-010 — Continuation Capsule
**Purpose:** let long productions resume after worker/process loss without pretending the failed attempt never existed.
**How it works:** stores a durable continuation reference to production/node state, last committed receipt, required inputs and retry lineage; a new attempt consumes it.
**Benefit:** Blender/ComfyUI/video jobs can survive crashes/restarts cleanly.
**Dependencies:** M11 worker fabric, M17 ComfyUI, M26 Blender.
**Risk:** resuming non-idempotent external tools can duplicate side effects.
**Proof:** crash-at-every-boundary fault-injection plan.
**Status:** PROPOSED.

## IRIS-PGX-011 — Policy-Bound Lifecycle Profile
**Purpose:** keep one universal lifecycle kernel while allowing domain-specific gates.
**How it works:** logo/web/game/video/audio profiles attach additional transition prerequisites/evidence without inventing incompatible core lifecycle machines.
**Benefit:** extreme domain specificity without fragmenting IRIS into separate products.
**Dependencies:** M01 Quality Kernel, domain profiles.
**Risk:** profiles may become hidden alternate state machines.
**Proof:** profile rules cannot add contradictory core transitions.
**Status:** PROPOSED.

## IRIS-PGX-012 — Materialization Identity Boundary
**Purpose:** distinguish “this artifact exists semantically” from “these bytes currently materialize it.”
**How it works:** artifact_id remains stable; every materialization creates an immutable revision bound to content digest, producer attempt and evidence.
**Benefit:** regenerations, format conversions and delivery variants remain traceable.
**Dependencies:** M06 revisions, M55 CAS, M59 delivery.
**Risk:** excessive revision count.
**Proof:** revision dedup/storage reuse without semantic identity collapse.
**Status:** PROPOSED.

# S01 relationship map

- PGX-001 Project Identity Envelope owns project-level stable identity.
- PGX-002 Identity Triad is the general identity doctrine.
- PGX-003 Production Passport owns production-level durable intent.
- PGX-004 + PGX-005 define lifecycle + immutable transition evidence.
- PGX-006 + PGX-009 protect identity from paths/names/location.
- PGX-007 binds intent/version semantics.
- PGX-008 protects historical continuity.
- PGX-010 bridges lifecycle semantics to later durable execution.
- PGX-011 keeps domain-specific gates compatible with one kernel.
- PGX-012 separates semantic artifact identity from byte materialization.

No candidate is yet IMPLEMENTED or VALIDATED.

# Existing foundations added for S02

## EXT-M02-008 — Bazel declared/actual dependency graph and action graph
**Type:** existing / build-graph pattern.
**What it does:** Bazel models targets as a DAG and distinguishes actual dependencies from declared dependencies. Correct builds require real direct dependencies to be represented in the declared graph; its analysis phase produces an action graph describing inputs/outputs/actions.
**How IRIS uses the pattern:** every material dependency must be declared/admitted, while excessive dependencies are avoided because they expand invalidation and work.
**Risk:** media generation is not ordinary compilation; stochastic/human steps need richer semantics.
**Proof:** hidden-dependency and over-invalidation challenge graphs.
**Status:** PATTERN_ACCEPTED_FOR_S02.

## EXT-M02-009 — Ninja dependency classes, depfiles and dyndep
**Type:** existing / incremental-build dependency pattern.
**What it does:** separates explicit/implicit/order-only/validation dependencies and can load dynamically discovered dependencies before execution through dyndep.
**How IRIS uses the pattern:** inspiration for edge semantics and a bounded dynamic-dependency discovery phase.
**Risk:** Ninja is file/action centric and its types do not cover rights, quality or semantic facets.
**Proof:** graph fixtures where order-only and material dependencies produce different invalidation outcomes.
**Status:** PATTERN_ACCEPTED_FOR_S02.

## EXT-M02-010 — DVC explicit deps/outs DAG
**Type:** existing / data-pipeline pattern.
**What it does:** stages declare dependencies and outputs; the resulting DAG lets DVC reason about which stages need rerunning when dependencies change.
**How IRIS uses the pattern:** reinforces explicit dependency/output declarations and reproducible stage graph thinking.
**Risk:** files are too coarse as the universal IRIS semantic dependency model.
**Proof:** compare whole-file invalidation with IRIS facet/slice invalidation.
**Status:** PATTERN_ACCEPTED_FOR_S02.

## EXT-M02-011 — OpenUSD dependency tracking and change processing
**Type:** existing / scene-composition dependency pattern.
**What it does:** Pcp retains dependencies discovered during composition and uses them to propagate changes/invalidate affected cached computations; USD clients can defer updating dirty consumers until needed.
**How IRIS uses the pattern:** inspiration for dependency receipts, impact analysis and lazy/selective recomputation for composed media.
**Risk:** USD dependency semantics are specific to scene composition.
**Proof:** USD integration later must map to IRIS graph semantics without redefining them.
**Status:** PATTERN_ACCEPTED_FOR_S02.

# Internal technology candidates — S02

## IRIS-PGX-013 — Typed Production Graph Kernel
**Purpose:** provide one provider-neutral graph substrate for every IRIS production domain.
**How it works:** immutable versioned DAG of logical nodes connected only through typed semantic ports and typed dependency edges.
**Benefit:** image, 3D, web, VFX, video and audio share one causal model.
**Dependencies:** PGX-001/003, M04 IR.
**Risk:** a universal graph can become over-generic.
**Proof:** same kernel drives four radically different synthetic domain graphs.
**Status:** PROPOSED.

## IRIS-PGX-014 — Semantic Port Contract
**Purpose:** prevent accidental connection of semantically incompatible graph values.
**How it works:** ports declare semantic/media type, schema/version, cardinality, optionality and quality/profile requirements; incompatible links require explicit conversion nodes.
**Benefit:** catches wrong graph wiring before expensive execution.
**Dependencies:** M04 typed IR, M01 quality classes.
**Risk:** too-rigid typing can slow evolution.
**Proof:** compatibility matrix and schema evolution tests.
**Status:** PROPOSED.

## IRIS-PGX-015 — Causal Edge Taxonomy
**Purpose:** stop ordering, evidence and telemetry relations from causing false rebuilds.
**How it works:** edges are explicitly MATERIAL_CAUSAL, CONSTRAINT_CAUSAL, EVIDENCE_CAUSAL, ACTIVATION, ORDER_ONLY or OBSERVATION.
**Benefit:** correct and smaller invalidation cones.
**Dependencies:** PGX-013.
**Risk:** misclassification can under- or over-invalidate.
**Proof:** adversarial edge-semantics graph corpus.
**Status:** PROPOSED.

## IRIS-PGX-016 — Dependency Truth Auditor
**Purpose:** detect hidden reads/dependencies that make a graph look reproducible when it is not.
**How it works:** compares declared causal dependencies with provider/runtime observed dependency receipts; undeclared material reads fail/quarantine or create a governed Graph Delta.
**Benefit:** prevents flaky “works because something happened to exist on disk” productions.
**Dependencies:** M11 sandbox/process observation, provider adapters.
**Risk:** black-box tools may hide dependencies that are difficult to observe.
**Proof:** seeded hidden-file/model/reference access tests.
**Status:** PROPOSED.

## IRIS-PGX-017 — Facet-Aware Invalidation Matrix
**Purpose:** avoid rebuilding expensive media when only non-material facets changed.
**How it works:** edges select facets such as CONTENT, SEMANTICS, QUALITY, POLICY, RIGHTS, PROVENANCE, DELIVERY and ENVIRONMENT. Deltas propagate only to consumers that observe the changed facets.
**Benefit:** major compute/time/cache savings with truthful dependencies.
**Dependencies:** M53 provenance/rights, M59 delivery, S04 rebuild.
**Risk:** missing a correctness-relevant facet can produce stale outputs.
**Proof:** facet mutation matrix versus full-rebuild oracle.
**Status:** PROPOSED.

## IRIS-PGX-018 — Semantic Dependency Slice
**Purpose:** narrow dependencies below whole-object granularity.
**How it works:** versioned deterministic selectors bind a consumer to the exact fields/regions/properties it uses.
**Benefit:** smaller invalidation cones and less context/token transfer.
**Dependencies:** typed IR and canonical selectors.
**Risk:** selector drift or hidden reads.
**Proof:** property mutation tests and hidden-read auditor.
**Status:** PROPOSED.

## IRIS-PGX-019 — Graph Triptych
**Purpose:** keep logical production semantics separate from bound materialization and provider execution.
**How it works:** Definition Graph -> Bound Materialization Graph -> Execution Plan, with explicit compilation boundaries.
**Benefit:** IRIS can swap Blender/ComfyUI/API/providers without rewriting project meaning.
**Dependencies:** M16 provider compiler, M57 agents.
**Risk:** extra layers increase implementation complexity.
**Proof:** compile the same definition into two provider-specific synthetic execution plans with identical declared outputs.
**Status:** PROPOSED.

## IRIS-PGX-020 — Causal Fingerprint
**Purpose:** create a deterministic invalidation/cache identity for one bound node.
**How it works:** hashes normalized node definition plus only correctness-relevant bound input slices/facets, policies, qualified component/environment refs, seeds and decisions.
**Benefit:** precise cache/invalidation without hashing irrelevant project noise.
**Dependencies:** canonical serialization, M13 cache.
**Risk:** omitted relevant input creates unsafe cache reuse.
**Proof:** differential mutation corpus against full execution oracle.
**Status:** PROPOSED.

## IRIS-PGX-021 — Reproducibility Classifier
**Purpose:** prevent cache identity from being mistaken for replay guarantees.
**How it works:** every operation declares DETERMINISTIC, SEEDED, ENVIRONMENT_SENSITIVE, STOCHASTIC, HUMAN_DECISION or EXTERNAL_STATE.
**Benefit:** correct replay, cache and provenance behavior for generative media.
**Dependencies:** model/tool qualification, M51 benchmark lab.
**Risk:** providers may claim determinism incorrectly.
**Proof:** repeated execution qualification and drift tests.
**Status:** PROPOSED.

## IRIS-PGX-022 — Epochal Feedback Loop
**Purpose:** support iterative creative correction without corrupting the causal DAG with cycles.
**How it works:** each feedback iteration creates a new epoch/graph binding that consumes immutable prior-epoch outputs.
**Benefit:** repair loops remain replayable, comparable and rollback-safe.
**Dependencies:** S03 snapshots/branches, M49 repair.
**Risk:** many epochs can produce history volume.
**Proof:** generate/evaluate/repair loop reconstructed from receipts without a graph cycle.
**Status:** PROPOSED.

## IRIS-PGX-023 — Subgraph ABI
**Purpose:** make complex production pipelines reusable and composable.
**How it works:** a versioned subgraph exposes stable typed input/output ports and hides internal nodes unless expanded for analysis.
**Benefit:** reusable character/logo/web-hero pipelines with controlled evolution.
**Dependencies:** PGX-014, S03 versioning.
**Risk:** interface versioning and hidden internal dependencies.
**Proof:** compatibility tests across subgraph versions.
**Status:** PROPOSED.

## IRIS-PGX-024 — Impact Cone Engine
**Purpose:** determine exactly what becomes stale when something changes.
**How it works:** traverses dependency facets/slices and activation paths from a delta to derive direct, transitive, conditional and clean nodes.
**Benefit:** foundation for minimal incremental media rebuild.
**Dependencies:** PGX-015/017/018, S04.
**Risk:** under-invalidation is dangerous; over-invalidation wastes compute.
**Proof:** compare impact cone with full-rebuild oracle across mutation corpus.
**Status:** PROPOSED.

## IRIS-PGX-025 — Dynamic Dependency Admission Gate
**Purpose:** safely handle dependencies only discoverable after inspecting content.
**How it works:** discovery emits typed dependency receipts and a proposed Graph Delta; execution cannot treat the result as trusted until the delta is admitted/rebound according to policy.
**Benefit:** supports USD refs, UDIMs, generated manifests and adapter discovery without silent graph mutation.
**Dependencies:** PGX-016, S03 graph revisions.
**Risk:** discovery/recompile loops.
**Proof:** missing/dynamic dependency fault cases.
**Status:** PROPOSED.

## IRIS-PGX-026 — Producer Exclusivity Guard
**Purpose:** eliminate ambiguous last-writer-wins outputs.
**How it works:** one revision/materialization has one producer attempt; multiple candidate producers must feed an explicit selection/merge/decision node.
**Benefit:** unambiguous provenance and reproducibility.
**Dependencies:** PGX-002/012, M53 provenance.
**Risk:** some DCC workflows naturally overwrite files and need adapter isolation.
**Proof:** concurrent producer race tests.
**Status:** PROPOSED.

## IRIS-PGX-027 — Causal Explain Trace
**Purpose:** make every rebuild/dirty decision human- and machine-explainable.
**How it works:** records a compact path from source delta through facet/slice/edge/fingerprint difference to each dirty consumer.
**Benefit:** developers can answer “why did IRIS rerender this?” instead of guessing.
**Dependencies:** PGX-024, M56 observability.
**Risk:** trace volume.
**Proof:** explanation path must correspond exactly to graph traversal.
**Status:** PROPOSED.

## IRIS-PGX-028 — Quality Graph Gate
**Purpose:** make M01 quality state a first-class causal input rather than an external UI check.
**How it works:** validators emit QualityDecision values consumed by selection, repair, release and delivery nodes with explicit required quality classes.
**Benefit:** PREVIEW cannot silently flow into a MASTER/release path.
**Dependencies:** M01 Quality Kernel, M48 Quality Court.
**Risk:** too many quality edges could over-invalidate generation.
**Proof:** quality-only changes re-run decisions/delivery without unnecessary media regeneration.
**Status:** PROPOSED.

## IRIS-PGX-029 — Side-Effect Fence
**Purpose:** stop publishing/external mutation nodes from being retried like pure rendering.
**How it works:** node effect class is NO_SIDE_EFFECT, CONTROLLED_OUTPUTS or EXTERNAL_MUTATION; external mutation requires idempotency/compensation/admission policy.
**Benefit:** prevents duplicate uploads/releases or destructive repeated actions.
**Dependencies:** M11 execution, M59 publishing.
**Risk:** adapters may misdeclare effects.
**Proof:** retry/fault-injection tests with fake external sinks.
**Status:** PROPOSED.

# S02 relationship map

- PGX-013 + PGX-014 form the universal typed graph substrate.
- PGX-015 + PGX-017 + PGX-018 define truthful causal granularity.
- PGX-016 + PGX-025 close the hidden/dynamic dependency problem.
- PGX-019 separates product meaning from execution provider.
- PGX-020 + PGX-021 make cache/replay claims safe.
- PGX-022 gives iterative creativity an acyclic historical model.
- PGX-023 enables reusable graph components.
- PGX-024 + PGX-027 provide selective invalidation with explanations.
- PGX-026 protects producer provenance.
- PGX-028 integrates the M01 quality kernel into production causality.
- PGX-029 protects external side effects.

All remain PROPOSED until M02 Final Technology Review.

# Existing foundations added for S03

## EXT-M02-012 — Git snapshots and movable refs
**Type:** existing / version-control pattern.
**What it does:** Git commits point at immutable snapshots/history while branches are lightweight movable references to commits.
**How IRIS uses the pattern:** branch refs move; production Snapshots remain immutable. IRIS does not require large media bytes to be stored in Git.
**Risk:** Git's line/text merge semantics are not suitable as universal media merge semantics.
**Proof:** ref movement + immutable Snapshot history tests.
**Status:** PATTERN_ACCEPTED_FOR_S03.

## EXT-M02-013 — OpenUSD VariantSets
**Type:** existing / non-destructive variant composition.
**What it does:** packages switchable alternatives within scene description and allows downstream variant selection without destructively rewriting the base asset.
**How IRIS uses the pattern:** inspiration for typed non-destructive Variant Sets across 2D/3D/web/video/audio domains.
**Risk:** USD variants are scene-description constructs and cannot be the universal IRIS variant kernel.
**Proof:** provider mapping without leaking USD-only semantics into core.
**Status:** PATTERN_ACCEPTED_FOR_S03.

## EXT-M02-014 — Perforce Streams
**Type:** existing / managed branching/merge pattern.
**What it does:** provides structured parent/child stream relationships and controlled propagation across concurrent development lines, commonly used in large asset/code projects.
**How IRIS uses the pattern:** inspiration for explicit branch relationships, propagation policy and large-media production workflows.
**Risk:** IRIS does not inherit depot/path-centric assumptions.
**Proof:** branch lineage and merge-flow fixtures.
**Status:** PATTERN_ACCEPTED_FOR_S03.

# Internal technology candidates — S03

## IRIS-PGX-030 — Creative Branch Ref
**Purpose:** provide cheap independent creative lines over immutable production history.
**How it works:** stable branch_id + mutable head_snapshot_id + exact fork point + policy profile.
**Benefit:** many experiments/campaigns/shots can evolve without project duplication.
**Dependencies:** PGX-001/003, Snapshot Manifest.
**Risk:** uncontrolled branch proliferation.
**Proof:** fork/advance/rename/merge/retention tests.
**Status:** PROPOSED.

## IRIS-PGX-031 — Immutable Production Snapshot
**Purpose:** freeze a reproducible production state without copying all media.
**How it works:** immutable snapshot references graph revision, variants, artifact revisions, policies, decisions and parent snapshots.
**Benefit:** time travel, fork, rollback and evidence.
**Dependencies:** M55 CAS, PGX-012.
**Risk:** incomplete closure being mistaken for full reproducibility.
**Proof:** snapshot immutability + closure completeness tests.
**Status:** PROPOSED.

## IRIS-PGX-032 — Snapshot Closure Manifest
**Purpose:** make snapshot completeness a provable claim.
**How it works:** canonical manifest lists graph, selected variants, revisions, quality/rights/provenance/environment refs and unresolved dependencies.
**Benefit:** LOGICAL/MATERIALIZED/VALIDATED/RELEASE claims can fail closed.
**Dependencies:** M01, M53, M55.
**Risk:** manifest growth.
**Proof:** missing-reference mutation corpus.
**Status:** PROPOSED.

## IRIS-PGX-033 — Variant Lattice
**Purpose:** represent orthogonal coexisting alternatives without cloning branches.
**How it works:** typed Variant Sets combine along controlled axes such as outfit/language/platform/motion/brand-mark.
**Benefit:** compact representation of large product/campaign matrices.
**Dependencies:** graph activation/port contracts.
**Risk:** combinatorial explosion.
**Proof:** variant-space and identity-preservation tests.
**Status:** PROPOSED.

## IRIS-PGX-034 — Variant Constraint Solver
**Purpose:** reject impossible/unsafe variant combinations before execution.
**How it works:** compatibility predicates/constraints over Variant Sets produce valid/invalid/conditional combinations with explanations.
**Benefit:** saves compute and protects persona/brand/platform invariants.
**Dependencies:** PGX-033, M03 constraints.
**Risk:** constraint complexity.
**Proof:** seeded legal/illegal combination corpus.
**Status:** PROPOSED.

## IRIS-PGX-035 — Sparse Variant Materializer
**Purpose:** avoid eagerly rendering every Cartesian variant.
**How it works:** materializes only requested/downstream-required combinations while structurally sharing common upstream revisions.
**Benefit:** large savings in GPU/storage/time.
**Dependencies:** PGX-024 Impact Cone, M55 CAS.
**Risk:** late missing variant discovery.
**Proof:** combinatorial benchmark against eager baseline.
**Status:** PROPOSED.

## IRIS-PGX-036 — Semantic Three-Way Merge
**Purpose:** merge media-production histories using graph/object semantics rather than byte heuristics.
**How it works:** compares merge base, source and target Snapshots per graph/object/variant/policy dimension.
**Benefit:** safe collaboration and creative convergence.
**Dependencies:** Semantic Diff, conflict engine.
**Risk:** domain-specific conflict ambiguity.
**Proof:** structured merge corpus with known oracle.
**Status:** PROPOSED.

## IRIS-PGX-037 — Creative Conflict Taxonomy
**Purpose:** classify merge conflicts into actionable production meanings.
**How it works:** typed conflicts cover topology, node definition, artifact revision, variants, identity, quality, rights, delivery and side effects.
**Benefit:** human/agent resolution is explicit rather than "merge failed".
**Dependencies:** PGX-036.
**Risk:** unknown conflict types.
**Proof:** fail closed on unrecognized/ambiguous conflict.
**Status:** PROPOSED.

## IRIS-PGX-038 — Merge Rebuild Planner
**Purpose:** prevent a successful metadata merge from pretending downstream media is still valid.
**How it works:** merge result feeds semantic deltas into S04 Impact Cone and computes nodes requiring revalidation/rebuild.
**Benefit:** safe merge plus minimal recomputation.
**Dependencies:** PGX-024, S04.
**Risk:** merge/invalidation mismatch.
**Proof:** merged state vs clean full rebuild oracle.
**Status:** PROPOSED.

## IRIS-PGX-039 — Experiment Sandbox Branch
**Purpose:** make model/style/camera/campaign experiments cheap and governed.
**How it works:** bounded branch stores hypothesis, origin Snapshot, budget, providers, TTL/pin and acceptance criteria.
**Benefit:** systematic experimentation without polluting canonical history.
**Dependencies:** M51 benchmarks, M15 champion/challenger.
**Risk:** experiment accumulation.
**Proof:** TTL/pin/promotion tests.
**Status:** PROPOSED.

## IRIS-PGX-040 — Experiment Promotion Bridge
**Purpose:** promote a winning experiment without copying arbitrary files.
**How it works:** emits an admitted semantic Delta/Merge Receipt from experiment to target branch with provenance and impact analysis.
**Benefit:** reproducible A/B winner promotion.
**Dependencies:** PGX-036/039.
**Risk:** hidden dependencies in experiment.
**Proof:** winner transplant retains causal lineage.
**Status:** PROPOSED.

## IRIS-PGX-041 — Safe Rollback Planner
**Purpose:** restore an older known-good state without rewriting history.
**How it works:** selects target Snapshot, validates reachability/policy, derives reverse semantic delta, checks external side effects and creates a new rollback Snapshot/receipt.
**Benefit:** reliable recovery.
**Dependencies:** PGX-031/032, S04.
**Risk:** old dependencies/providers may no longer be available.
**Proof:** rollback/rebuild/revalidation matrix.
**Status:** PROPOSED.

## IRIS-PGX-042 — External Side-Effect Rollback Fence
**Purpose:** prevent local state rollback from falsely claiming the outside world was undone.
**How it works:** marks published/uploaded/payment/external mutations and requires explicit compensation or release rollback workflows.
**Benefit:** avoids duplicate or inconsistent external actions.
**Dependencies:** PGX-029, M59.
**Risk:** provider-specific compensation limitations.
**Proof:** fake external sink fault tests.
**Status:** PROPOSED.

## IRIS-PGX-043 — Structural Snapshot Sharing
**Purpose:** make branches/snapshots cheap for large media.
**How it works:** snapshot manifests share immutable CAS/revision references; copy-on-write occurs only for changed semantics/materializations.
**Benefit:** branch a feature film or game asset set without duplicating terabytes.
**Dependencies:** M55 CAS.
**Risk:** reachability/GC correctness.
**Proof:** storage amplification benchmark and GC safety.
**Status:** PROPOSED.

## IRIS-PGX-044 — Persona Continuity Branch Guard
**Purpose:** prevent a persistent avatar's protected identity from drifting through ordinary variants/merges.
**How it works:** identity-anchor fields are protected across branches; changes require explicit identity migration/new persona semantics and stronger review.
**Benefit:** stable corporate spokesperson across campaigns/episodes.
**Dependencies:** M05, M39, M01 Quality.
**Risk:** too-strict anchors can limit intentional evolution.
**Proof:** outfit/language pass; face/voice-core mutation blocks.
**Status:** PROPOSED.

## IRIS-PGX-045 — Campaign & Episode Baseline
**Purpose:** give recurring media a stable shared production ancestry.
**How it works:** each campaign/episode/shot can fork from an approved baseline Snapshot while inheriting persona/brand/world/music/voice anchors.
**Benefit:** hundreds of videos can evolve independently without continuity collapse.
**Dependencies:** M36/M37/M43/M45.
**Risk:** baseline updates need controlled propagation.
**Proof:** multi-episode continuity and propagation tests.
**Status:** PROPOSED.

## IRIS-PGX-046 — Semantic Delta Transplant
**Purpose:** cherry-pick bounded creative/technical improvements across branches.
**How it works:** transplants a typed Graph/Production Delta with dependency preconditions and conflict/impact checks.
**Benefit:** reuse one fix without merging unrelated experiments.
**Dependencies:** PGX-036/038.
**Risk:** delta assumes missing context.
**Proof:** precondition mismatch must block.
**Status:** PROPOSED.

## IRIS-PGX-047 — Merge Provenance Receipt
**Purpose:** make merge outcomes independently auditable.
**How it works:** records base/source/target, auto/manual resolutions, unresolved conflicts, resulting Snapshot and policy/evidence.
**Benefit:** explains exactly how a creative direction became canonical.
**Dependencies:** M53 provenance.
**Risk:** receipt volume.
**Proof:** replay/verify merge decision history.
**Status:** PROPOSED.

## IRIS-PGX-048 — Variant Explosion Governor
**Purpose:** prevent apparently harmless Variant Sets from creating runaway compute/storage demand.
**How it works:** estimates reachable combination count, materialization demand and quality-test matrix; requires policy approval/budget when thresholds exceed limits.
**Benefit:** protects workstation and cloud cost.
**Dependencies:** PGX-033/035, M09/M10/M50.
**Risk:** conservative estimates may block useful batches.
**Proof:** predicted vs actual materialization cost.
**Status:** PROPOSED.

## IRIS-PGX-049 — Snapshot Reachability & Pin Ledger
**Purpose:** make cleanup safe.
**How it works:** tracks reachability from live branches plus release/benchmark/rights/audit pins before materialization GC.
**Benefit:** reclaim storage without deleting evidence or rollback targets.
**Dependencies:** M53/M55.
**Risk:** stale pins leak storage.
**Proof:** mark/sweep-style adversarial reachability corpus.
**Status:** PROPOSED.

## IRIS-PGX-050 — Production Time-Travel Inspector
**Purpose:** inspect any historical Snapshot without mutating it.
**How it works:** resolves snapshot closure into a read-only project/graph/asset view suitable for comparison, provenance and optional reproduction.
**Benefit:** debugging, quality regression and creative archaeology.
**Dependencies:** PGX-031/032.
**Risk:** unavailable historic providers/assets.
**Proof:** immutability and read-only access tests.
**Status:** PROPOSED.

# S03 relationship map

- PGX-030/031 separate moving creative refs from immutable history.
- PGX-032 makes Snapshot completeness provable.
- PGX-033/034/035/048 form the variant composition + explosion-control suite.
- PGX-036/037/038/047 form semantic merge and auditable conflict resolution.
- PGX-039/040 govern experiments and winner promotion.
- PGX-041/042 define safe rollback without pretending external effects vanished.
- PGX-043/049 make large-media branching/storage practical.
- PGX-044/045 protect persistent avatars, campaigns and episodes.
- PGX-046 provides bounded cherry-pick-like semantic reuse.
- PGX-050 provides immutable time travel.

All remain PROPOSED until M02 Final Technology Review.

# Existing foundations added for S04

## EXT-M02-015 — Bazel Action Cache + CAS
**Type:** existing / build cache pattern.
**What it does:** Bazel breaks builds into declared actions, maps action hashes to result metadata and stores output bytes in a CAS; reproducible results can be reused locally/remotely.
**How IRIS uses the pattern:** separate action/build-result lookup from immutable content storage, with explicit declared inputs and trust boundaries.
**Risk:** generative media is frequently non-hermetic/non-deterministic; IRIS cannot equate action-key equality with byte determinism for every node.
**Proof:** cache-class/reproducibility tests.
**Status:** PATTERN_ACCEPTED_FOR_S04.

## EXT-M02-016 — Nix derivations/store
**Type:** existing / immutable build-store pattern.
**What it does:** derivations specify precise build inputs/outputs and the Nix store keeps immutable objects; deterministic build assumptions make caching/reuse meaningful.
**How IRIS uses the pattern:** inspiration for immutable materializations, explicit closure and reproducibility-class-aware reuse.
**Risk:** IRIS must model stochastic models and external/human state rather than pretending all production is pure.
**Proof:** derivation-style fixtures across IRIS reproducibility classes.
**Status:** PATTERN_ACCEPTED_FOR_S04.

## EXT-M02-017 — Buck2 incremental actions
**Type:** existing / incremental-action pattern.
**What it does:** supports actions that reuse previous outputs when the action understands what changed and can update only affected portions.
**How IRIS uses the pattern:** validates the value of preserving previous result state plus an explicit changed-input description for partial updates.
**Risk:** partial update logic can leave stale output.
**Proof:** incremental-vs-clean oracle.
**Status:** PATTERN_ACCEPTED_FOR_S04.

## EXT-M02-018 — DVC run cache / selective reproduction
**Type:** existing / pipeline cache pattern.
**What it does:** DVC pipelines track declared dependencies/outputs, rerun affected stages and can reuse previous stage results through run-cache.
**How IRIS uses the pattern:** inspiration for long-lived production result reuse independent of one Git commit.
**Risk:** whole-file/stage semantics are coarser than IRIS media dependency slices.
**Proof:** compare file-level vs semantic-slice invalidation.
**Status:** PATTERN_ACCEPTED_FOR_S04.

## EXT-M02-019 — Transformer KV / prefix caching
**Type:** existing / inference optimization.
**What it does:** reuses previously computed attention key/value state or prefilled prompt prefixes so repeated autoregressive inference avoids recomputing unchanged prefixes.
**How IRIS uses the pattern:** provider/runtime optimization for repeated script/planning/localization/evaluator contexts, always bound to exact model/tokenizer/template/runtime compatibility.
**Risk:** stale/mismatched context cache can corrupt inference; runtime caches are not durable semantic evidence.
**Proof:** context-fingerprint and recompute-equivalence tests.
**Status:** PATTERN_ACCEPTED_FOR_S04.

# Internal technology candidates — S04

## IRIS-PGX-051 — Creative Build Compiler
**Purpose:** compile semantic deltas and target requests into the smallest safe production Work Set.
**How it works:** combines current Snapshot, Impact Cone, cache inventory, quality/policy constraints and runtime capability to assign work dispositions.
**Benefit:** central engine for minimal recomputation.
**Dependencies:** PGX-024, S03 snapshots.
**Risk:** planner bug can under-invalidate.
**Proof:** full-build oracle corpus.
**Status:** PROPOSED.

## IRIS-PGX-052 — Dirty Frontier Reducer
**Purpose:** shrink a broad Impact Cone into the true roots that require action.
**How it works:** stops propagation at admitted reusable/repaired/revalidated boundaries while preserving causal explanations.
**Benefit:** fewer expensive downstream operations.
**Dependencies:** PGX-024/051.
**Risk:** unsafe frontier cut.
**Proof:** mutation oracle + shadow rebuild.
**Status:** PROPOSED.

## IRIS-PGX-053 — Work Disposition Matrix
**Purpose:** decide REBUILD vs REPAIR vs REVALIDATE vs REPACKAGE vs REUSE vs BLOCK.
**How it works:** policy table combines delta facet, material state, reproducibility class, quality debt/evidence and repair capabilities.
**Benefit:** avoids regenerating media when validation/package repair is enough.
**Dependencies:** M01, M49, M59.
**Risk:** wrong disposition.
**Proof:** domain matrix fixtures.
**Status:** PROPOSED.

## IRIS-PGX-054 — Repair Frontier
**Purpose:** localize regeneration inside a materialization.
**How it works:** represents bounded affected region/time/subasset plus surrounding continuity constraints and required post-repair validators.
**Benefit:** minimal image/frame/audio/mesh repair.
**Dependencies:** M49.
**Risk:** seam/continuity defects.
**Proof:** local repair vs full rebuild quality benchmark.
**Status:** PROPOSED.

## IRIS-PGX-055 — Layered Reuse Fabric
**Purpose:** make cache semantics explicit across planning, context, warm provider state, intermediate and final materializations, and evidence.
**How it works:** independent cache layers with separate keys, trust and eviction rules.
**Benefit:** much higher reuse without mixing transient optimization with canonical truth.
**Dependencies:** M13/M55.
**Risk:** cache complexity.
**Proof:** layer isolation and eviction tests.
**Status:** PROPOSED.

## IRIS-PGX-056 — Reuse Trust Ladder
**Purpose:** prevent “cache hit” from meaning “automatically safe”.
**How it works:** EXACT_REUSE, QUALIFIED_REUSE, PARTIAL_REUSE, WARM_REUSE, ADVISORY_REUSE, NO_REUSE with explicit admission rules.
**Benefit:** safe reuse across deterministic and generative workflows.
**Dependencies:** PGX-021/055.
**Risk:** too conservative => low hit rate.
**Proof:** unsafe-hit rejection and hit-quality metrics.
**Status:** PROPOSED.

## IRIS-PGX-057 — Reuse Receipt
**Purpose:** make semantic cache reuse auditable.
**How it works:** records source, fingerprint, class, producer, qualification, environment/policy comparison and required validation.
**Benefit:** answers “why did IRIS not rebuild this?”
**Dependencies:** M53 provenance.
**Risk:** receipt volume.
**Proof:** replay cache admission decision.
**Status:** PROPOSED.

## IRIS-PGX-058 — Cache Poisoning Shield
**Purpose:** stop stale/tampered/unqualified entries contaminating production.
**How it works:** verifies digest, producer/version, key schema, dependency closure, qualification, rights/provenance and writer trust before admission.
**Benefit:** shared cache can remain a performance layer without becoming a trust hole.
**Dependencies:** M18 supply chain, M53, M54.
**Risk:** false quarantine.
**Proof:** malicious/stale cache corpus.
**Status:** PROPOSED.

## IRIS-PGX-059 — Context Fingerprint Cache
**Purpose:** reduce LLM tokens/compute while guaranteeing context freshness.
**How it works:** fingerprints canonical sources, HIVE retrieval set/order, prompt/compiler/template, model/tokenizer, policy, locale and tool schemas; unchanged slices/prefixes can be reused.
**Benefit:** major token and latency savings for repeated planning/content/evaluator jobs.
**Dependencies:** HIVE/M52, M43/M44/M47/M48.
**Risk:** omitted context dependency creates stale reasoning.
**Proof:** context mutation matrix.
**Status:** PROPOSED.

## IRIS-PGX-060 — Prefix/KV Compatibility Gate
**Purpose:** safely exploit provider/runtime prefix or KV caching.
**How it works:** reuse allowed only when model/tokenizer/template/runtime/context-prefix compatibility matches; cache remains ephemeral.
**Benefit:** faster repeated inference, especially on long shared prompts.
**Dependencies:** model providers/runtime.
**Risk:** provider-specific cache semantics.
**Proof:** recompute vs cached inference compatibility suite.
**Status:** PROPOSED.

## IRIS-PGX-061 — Provider Warmth Scheduler
**Purpose:** reduce model load/compile churn.
**How it works:** planner considers resident models/adapters/kernels/workflows as a cost signal among otherwise correctness-equivalent plans.
**Benefit:** faster local 8GB workflows and lower thrashing.
**Dependencies:** M09/M10/M11/M13.
**Risk:** warm-state bias might select inferior provider if quality policy is not dominant.
**Proof:** assert quality/provider constraints before warmth optimization.
**Status:** PROPOSED.

## IRIS-PGX-062 — Variant Work Coalescer
**Purpose:** share expensive prefixes across related variants.
**How it works:** finds causally common upstream/context/model work, batches it, then fans out at the first true divergent dependency.
**Benefit:** efficient multilingual, aspect-ratio, campaign and avatar batches.
**Dependencies:** PGX-033/035.
**Risk:** accidental cross-variant contamination.
**Proof:** fan-out boundary tests.
**Status:** PROPOSED.

## IRIS-PGX-063 — Build Journal
**Purpose:** make crashes/cancellation recoverable without trusting temp files.
**How it works:** append-only attempt journal differentiates planned, running, temp-produced, committed, validated and side-effect states.
**Benefit:** resume/cleanup/retry truth.
**Dependencies:** PGX-005/010, M11.
**Risk:** journal/reality divergence.
**Proof:** crash-at-every-boundary fault injection.
**Status:** PROPOSED.

## IRIS-PGX-064 — Atomic Materialization Commit
**Purpose:** prevent partial multi-output results from entering cache/history as complete.
**How it works:** output set commits atomically or uses an explicit partial-output contract with per-output truth.
**Benefit:** no half-built cache hits.
**Dependencies:** M55 storage/CAS.
**Risk:** huge outputs make transaction design difficult.
**Proof:** crash and torn-write simulations.
**Status:** PROPOSED.

## IRIS-PGX-065 — Incremental Truth Oracle
**Purpose:** prove incremental build behavior against a clean/full reference.
**How it works:** exact byte/digest comparison for qualified deterministic nodes, class-aware causal/quality equivalence for non-deterministic nodes.
**Benefit:** incremental correctness becomes benchmarked rather than assumed.
**Dependencies:** M51.
**Risk:** full reference is expensive.
**Proof:** protected benchmark corpus.
**Status:** PROPOSED.

## IRIS-PGX-066 — Shadow Rebuild Sentinel
**Purpose:** detect hidden stale dependencies in apparently clean/cache-hit nodes.
**How it works:** samples reused nodes for clean recomputation and compares digest/evidence/dependency observations.
**Benefit:** catches under-invalidation before it becomes systemic.
**Dependencies:** PGX-065.
**Risk:** extra compute.
**Proof:** inject missing dependency and measure detection.
**Status:** PROPOSED.

## IRIS-PGX-067 — Differential Mutation Lab
**Purpose:** systematically test incremental dependency truth.
**How it works:** mutates one facet/slice/model/policy/environment field at a time and asserts dirty/clean/reuse/disposition sets.
**Benefit:** strong regression protection for the build compiler.
**Dependencies:** M51.
**Risk:** combinatorial corpus growth.
**Proof:** mutation coverage reporting.
**Status:** PROPOSED.

## IRIS-PGX-068 — Cache Quarantine Circuit
**Purpose:** react to proven cache mismatch/poisoning.
**How it works:** quarantines entry/key namespace/provider/workflow scope, disables writes or widens invalidation until requalification.
**Benefit:** one bad cache hit does not silently spread.
**Dependencies:** M18/M54/M56.
**Risk:** broad quarantine hurts performance.
**Proof:** fault injection + recovery policy tests.
**Status:** PROPOSED.

## IRIS-PGX-069 — Incremental Explain Receipt
**Purpose:** make minimal-build decisions transparent.
**How it works:** records delta → facet/slice → dirty frontier → disposition → cache admission/rejection → expected savings.
**Benefit:** operator and agents understand why work was or was not repeated.
**Dependencies:** PGX-027/051.
**Risk:** explanation overhead.
**Proof:** trace corresponds to planner decisions.
**Status:** PROPOSED.

## IRIS-PGX-070 — Adaptive Retention Value Model
**Purpose:** keep the most valuable intermediates under bounded storage.
**How it works:** retention score considers recompute cost, hit frequency, size, quality/provenance importance, protection pins and hardware scarcity.
**Benefit:** better cache hit rate than blind LRU for media.
**Dependencies:** M13/M55.
**Risk:** predictor error and starvation.
**Proof:** replay workload benchmark vs LRU/LFU.
**Status:** PROPOSED.

## IRIS-PGX-071 — Persona Production Prefix Cache
**Purpose:** accelerate recurring corporate-avatar/series production without weakening identity.
**How it works:** caches admitted persona/brand/voice/context baseline compilation and heavy shared intermediates separately from episode-specific script/performance/delivery deltas.
**Benefit:** hundreds of recurring videos reuse stable identity foundations.
**Dependencies:** M05/M39/M40/M43/M45, PGX-059/062.
**Risk:** stale baseline after persona/brand change.
**Proof:** baseline mutation invalidates every dependent episode path correctly.
**Status:** PROPOSED.

## IRIS-PGX-072 — Token/Context Delta Compiler
**Purpose:** minimize LLM input rebuilding when only part of production context changed.
**How it works:** compiles canonical context into fingerprinted semantic segments and transmits/rebuilds only changed segments where the provider protocol allows safe reuse.
**Benefit:** lower LLM input tokens and faster iterative planning/localization/script work.
**Dependencies:** HIVE M52, provider context caching.
**Risk:** provider APIs differ and semantic ordering may matter.
**Proof:** full-context vs delta-context task equivalence/calibration.
**Status:** PROPOSED.

## IRIS-PGX-073 — Quality-Preserving Cost Frontier
**Purpose:** choose the cheapest safe rebuild plan without turning quality into a tradeable afterthought.
**How it works:** first filters plans that satisfy Fidelity Contract/correctness; only then Pareto-optimizes time, VRAM, GPU work, storage, network and token cost.
**Benefit:** maximum efficiency with no silent MASTER degradation.
**Dependencies:** M01, M09/M10/M50.
**Risk:** incomplete cost estimates.
**Proof:** selected plan must always lie inside admissible quality set.
**Status:** PROPOSED.

# S04 relationship map

- PGX-051/052/053 compile semantic changes into minimal work.
- PGX-054 integrates bounded repair into build truth.
- PGX-055/056/057/058 define layered, trusted reuse.
- PGX-059/060/072 target LLM/context/token efficiency.
- PGX-061/062 optimize provider warmth and variant batching.
- PGX-063/064 make execution crash/commit safe.
- PGX-065/066/067 make incremental correctness testable.
- PGX-068 protects production after cache mismatch.
- PGX-069 makes incremental choices explainable.
- PGX-070 makes retention cost-aware.
- PGX-071 specializes safe reuse for persistent avatars/series.
- PGX-073 preserves quality before cost optimization.

All remain PROPOSED until M02 Final Technology Review.

# Existing foundations added for S05

## EXT-M02-020 — W3C SCXML / statecharts
**Type:** existing standard / state-machine semantics.
**What it does:** defines generic state-machine semantics including guarded transitions, compound/parallel state regions, final states and history states.
**How IRIS uses the pattern:** reference for explicit legal state configurations and orthogonal production state regions without adopting XML/runtime dependency.
**Risk:** SCXML executable semantics are broader than IRIS needs.
**Proof:** state vector legality and transition-table tests.
**Status:** PATTERN_ACCEPTED_FOR_S05.

## EXT-M02-021 — Temporal durable workflow history
**Type:** existing / durable execution pattern.
**What it does:** persists workflow history and resumes execution after failures/outages.
**How IRIS uses the pattern:** inspiration for replayable transition history, reconciliation and attempts that survive process failure.
**Risk:** Temporal is not IRIS canonical production authority.
**Proof:** reconstruct production state without Temporal runtime.
**Status:** PATTERN_ACCEPTED_FOR_S05.

## EXT-M02-022 — Dagster asset materialization / lineage model
**Type:** existing / asset lifecycle pattern.
**What it does:** models persistent assets, dependencies, materializations, checks and lineage rather than only ephemeral tasks.
**How IRIS uses the pattern:** reinforces separation of materialization fact from orchestration execution and quality/check state.
**Risk:** data-asset semantics are narrower than multimodal production.
**Proof:** media/artifact lifecycle fixtures.
**Status:** PATTERN_ACCEPTED_FOR_S05.

## EXT-M02-023 — OpenUSD large-scale film composition workflow
**Type:** existing / film/VFX production pattern.
**What it does:** provides layered non-destructive composition and asset referencing designed for large-scale animated/VFX scene production.
**How IRIS uses the pattern:** evidence that immutable/layered asset/shot composition and collaborative history are practical for film-scale workloads.
**Risk:** scene composition is not production promotion/release governance.
**Proof:** later M25/M36 mappings preserve IRIS lifecycle authority.
**Status:** PATTERN_ACCEPTED_FOR_S05.

# Internal technology candidates — S05

## IRIS-PGX-074 — Orthogonal Production State Vector
**Purpose:** eliminate contradictory overloaded status fields.
**How it works:** separate versioned lifecycle, execution, review/promotion and release regions with cross-region invariants.
**Benefit:** precise state/recovery reasoning.
**Dependencies:** Transition Receipts.
**Risk:** more state dimensions.
**Proof:** legal-state model checking/table tests.
**Status:** PROPOSED.

## IRIS-PGX-075 — Lifecycle Transition Compiler
**Purpose:** turn versioned lifecycle profiles into executable legal-transition tables.
**How it works:** compiles states, events, guards, required receipts and resulting vector transitions into deterministic policy.
**Benefit:** domains can add gates without hand-coded scattered conditionals.
**Dependencies:** M03 policy compiler.
**Risk:** bad profile compiles bad workflow.
**Proof:** static validation + mutation tests.
**Status:** PROPOSED.

## IRIS-PGX-076 — Promotion Request Envelope
**Purpose:** make approval/promotion an explicit auditable operation.
**How it works:** binds candidate Snapshot, requested phase/class, Gate Set, reviewers, policy refs and reason.
**Benefit:** finishing a render cannot accidentally promote it.
**Dependencies:** S03 Snapshots, M01.
**Risk:** ceremony/latency.
**Proof:** no implicit promotion path.
**Status:** PROPOSED.

## IRIS-PGX-077 — Promotion Gate Set
**Purpose:** unify structural, quality, rights, provenance, security, delivery and human-review admission.
**How it works:** typed gates emit PASS/FAIL/UNKNOWN/N/A with evidence/authority/version.
**Benefit:** production approval becomes machine-auditable and domain-aware.
**Dependencies:** M01, M48, M53/M54/M59.
**Risk:** gate sprawl.
**Proof:** gate completeness by profile.
**Status:** PROPOSED.

## IRIS-PGX-078 — Gate Freshness Graph
**Purpose:** prevent stale approvals from surviving dependency changes.
**How it works:** each gate declares causal facets/slices; relevant deltas invalidate only affected gate results.
**Benefit:** safe revalidation without rerendering clean media.
**Dependencies:** PGX-017/018, S04.
**Risk:** missing dependency causes stale approval.
**Proof:** facet mutation corpus.
**Status:** PROPOSED.

## IRIS-PGX-079 — Promotion Evidence Bundle
**Purpose:** provide one immutable evidence package for ACCEPTED/RELEASED promotions.
**How it works:** binds snapshot, state transition, all gates, QualityDecisions, human decisions, rights/provenance and observations.
**Benefit:** auditability and HIVE retrieval.
**Dependencies:** M53/M55.
**Risk:** bundle size.
**Proof:** completeness validator.
**Status:** PROPOSED.

## IRIS-PGX-080 — Attempt/Production Separation Guard
**Purpose:** prevent successful provider processes from masquerading as accepted production.
**How it works:** type/state API forbids attempt terminal events from directly mutating acceptance/release regions.
**Benefit:** closes a common automation safety hole.
**Dependencies:** S01 attempt model.
**Risk:** integration adapters may try shortcuts.
**Proof:** adversarial adapter tests.
**Status:** PROPOSED.

## IRIS-PGX-081 — Correction Lineage Loop
**Purpose:** govern reject/fix/review cycles without rewriting prior evidence.
**How it works:** CHANGES_REQUIRED emits Graph/Production Delta lineage into a new attempt/revision/snapshot/review.
**Benefit:** every correction round is reproducible.
**Dependencies:** PGX-022, S03/S04.
**Risk:** long lineage.
**Proof:** multi-round correction replay.
**Status:** PROPOSED.

## IRIS-PGX-082 — Reversible Blocker Ledger
**Purpose:** model missing rights/hardware/provider/human/security inputs without terminally killing production.
**How it works:** typed blockers open/resolve through receipts and re-trigger affected gates.
**Benefit:** durable pause/resume.
**Dependencies:** M11, M54.
**Risk:** stale blockers.
**Proof:** unblock/revalidation tests.
**Status:** PROPOSED.

## IRIS-PGX-083 — Release Transaction Coordinator
**Purpose:** make public/external delivery a governed multi-step transaction.
**How it works:** prepare Release Snapshot → gates → stage → external mutation → receipt → publish state.
**Benefit:** avoids half-published releases.
**Dependencies:** PGX-029/042, M59.
**Risk:** distributed transaction ambiguity.
**Proof:** fault injection at each step.
**Status:** PROPOSED.

## IRIS-PGX-084 — External State Reconciler
**Purpose:** safely handle timeouts/unknown outcomes after external side effects.
**How it works:** queries external destination using idempotency/external IDs before deciding retry/success/failure.
**Benefit:** prevents duplicate uploads/releases.
**Dependencies:** M59 providers.
**Risk:** external APIs may not expose enough truth.
**Proof:** ambiguous-response simulator.
**Status:** PROPOSED.

## IRIS-PGX-085 — Release Recall Ledger
**Purpose:** model withdrawal/recall without deleting public history.
**How it works:** immutable recall receipts bind release, reason, destination actions and replacement.
**Benefit:** legal/quality/security recall audit.
**Dependencies:** M53/M59.
**Risk:** destination removal may be partial.
**Proof:** multi-destination recall tests.
**Status:** PROPOSED.

## IRIS-PGX-086 — Supersession Resolver
**Purpose:** identify preferred current production/release without corrupting exact historical refs.
**How it works:** append-only supersession graph plus policy-controlled "latest admitted" resolver.
**Benefit:** consumers can follow current version while audits remain exact.
**Dependencies:** PGX-008.
**Risk:** supersession cycles.
**Proof:** cycle rejection + exact/latest resolution tests.
**Status:** PROPOSED.

## IRIS-PGX-087 — Archive Contract Manifest
**Purpose:** make archival completeness explicit.
**How it works:** binds final snapshots, evidence, graph, provenance, retention tier, digests, reproducibility requirements and restoration risks.
**Benefit:** archive is provable, not a folder move.
**Dependencies:** M53/M55.
**Risk:** very large manifests.
**Proof:** missing closure/object mutation tests.
**Status:** PROPOSED.

## IRIS-PGX-088 — Multi-Tier Archive Policy
**Purpose:** retain the right amount of production state by purpose.
**How it works:** LIGHT / REPRODUCIBLE / LEGAL_HOLD / GOLDEN tiers with composable pins and retention obligations.
**Benefit:** controls storage while preserving evidence/rebuild needs.
**Dependencies:** M51/M53/M55.
**Risk:** policy interaction complexity.
**Proof:** retention/GC matrix.
**Status:** PROPOSED.

## IRIS-PGX-089 — Archive Integrity Sentinel
**Purpose:** detect bit rot, missing CAS objects and broken evidence closure.
**How it works:** periodic/on-access digest/reachability/manifest audits with explicit damage state.
**Benefit:** long-lived media archives remain trustworthy.
**Dependencies:** M55.
**Risk:** audit I/O cost.
**Proof:** corrupted/missing object injection.
**Status:** PROPOSED.

## IRIS-PGX-090 — Reproducibility Horizon Tracker
**Purpose:** tell operators how reproducible an old production still is as external tools/models disappear.
**How it works:** tracks availability/qualification of model/tool/provider/input dependencies and degrades restoration claims explicitly.
**Benefit:** honest archive restoration.
**Dependencies:** M14/M18/M55.
**Risk:** external dependency discovery gaps.
**Proof:** simulated provider/model retirement.
**Status:** PROPOSED.

## IRIS-PGX-091 — Revival Fork
**Purpose:** reopen archived/superseded work without mutating historical state.
**How it works:** creates new active production/branch from exact historic Snapshot and forces stale policy/tool/right revalidation.
**Benefit:** safe remaster/remake/relaunch.
**Dependencies:** S03 branch/fork.
**Risk:** user may expect exact historic environment.
**Proof:** archive→revival lineage tests.
**Status:** PROPOSED.

## IRIS-PGX-092 — State Projection Replay Engine
**Purpose:** prove current production state from immutable history.
**How it works:** replays baseline + transition/snapshot/promotion/release receipts into a deterministic current-state projection.
**Benefit:** cached database state can be audited/rebuilt.
**Dependencies:** PGX-005, M55.
**Risk:** event schema evolution.
**Proof:** cached-vs-replayed state equality.
**Status:** PROPOSED.

## IRIS-PGX-093 — Transition Idempotency Seal
**Purpose:** prevent duplicate commands/events from duplicating approvals/releases/archives.
**How it works:** stable event/command identity plus semantic digest returns prior receipt or flags conflict.
**Benefit:** safe retries.
**Dependencies:** PGX-005/083.
**Risk:** bad idempotency scope can collapse distinct operations.
**Proof:** duplicate/conflicting command corpus.
**Status:** PROPOSED.

## IRIS-PGX-094 — Completion Profile Resolver
**Purpose:** avoid a universal misleading COMPLETED state.
**How it works:** each production profile declares terminal obligation (ACCEPTED, RELEASED, ARCHIVED, etc.); completion is derived with profile evidence.
**Benefit:** honest completion semantics across internal assets, films, campaigns and releases.
**Dependencies:** lifecycle profiles.
**Risk:** confusing UI if profile is hidden.
**Proof:** profile-specific terminal tests.
**Status:** PROPOSED.

## IRIS-PGX-095 — Cross-State Invariant Guard
**Purpose:** reject impossible combinations across orthogonal regions.
**How it works:** compiled invariants validate whole State Vector on every transition/replay.
**Benefit:** no PUBLISHED-before-ACCEPTED or ARCHIVED-with-active-attempt contradictions.
**Dependencies:** PGX-074/075.
**Risk:** invariant evolution.
**Proof:** exhaustive invalid-vector corpus.
**Status:** PROPOSED.

## IRIS-PGX-096 — Persona Public Release Gate
**Purpose:** apply stricter release admission to persistent public-facing synthetic identities.
**How it works:** requires cross-modal persona/voice/brand continuity, rights/consent/provenance and human approval according to profile before public release.
**Benefit:** corporate avatar cannot drift or publish without governed identity evidence.
**Dependencies:** M05/M39/M40/M45/M46/M53.
**Risk:** review latency.
**Proof:** outfit/language variation passes; protected identity/rights drift blocks.
**Status:** PROPOSED.

# S05 relationship map

- PGX-074/075/095 define the orthogonal lifecycle state kernel.
- PGX-076/077/078/079 define explicit evidence-based promotion.
- PGX-080 prevents attempt success from bypassing M01/M02 acceptance.
- PGX-081/082 govern correction and reversible blockers.
- PGX-083/084/085 govern release, uncertain external outcomes and recall.
- PGX-086 handles supersession/current resolution.
- PGX-087/088/089/090 define archive, retention and long-term integrity.
- PGX-091 reopens old work through new lineage.
- PGX-092/093 provide replayable/idempotent durable state.
- PGX-094 derives honest completion by profile.
- PGX-096 applies the stricter public-avatar release contract.

All remain PROPOSED until M02 Final Technology Review.
