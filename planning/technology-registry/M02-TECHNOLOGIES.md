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
