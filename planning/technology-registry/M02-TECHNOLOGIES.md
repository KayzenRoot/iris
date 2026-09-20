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
