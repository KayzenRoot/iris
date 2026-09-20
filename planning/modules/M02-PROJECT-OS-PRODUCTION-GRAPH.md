# M02 — Project OS & Production Graph

Status: `S01_PROPOSED_COMPLETE_PENDING_DISCUSSION`

## Mission

M02 defines the operating system of an IRIS production: how projects, productions, attempts, artifacts and revisions are identified; how they move through legal lifecycle states; and how later graph/build/rebuild/rollback systems can reason about them without depending on filenames, UI labels or one workstation.

M02 must remain domain-neutral. A Nerim character, a logo, a favicon, a WebGPU scene, a cinematic shot, a voice take and a dashboard animation must all fit the same production identity/lifecycle substrate.

---

# S01 — Project / production identity and lifecycle

## 1. Identity doctrine

### 1.1 Names and paths are not identity
Human-facing names, slugs, folder paths, filenames, DCC object names and export paths are aliases/locators only.

Renaming:
- a project;
- an asset;
- a Blender collection;
- a website package;
- a logo variant;
- a production folder

MUST NOT create a new semantic object by accident.

### 1.2 Identity is layered
IRIS separates three questions:

1. **What semantic object is this?**
   - stable semantic ID such as project/artifact/production identity.
2. **Which immutable revision/content state is this?**
   - content/revision digest plus versioned metadata.
3. **Which execution attempt produced or evaluated it?**
   - attempt identity and transition/evidence receipts.

These layers MUST NOT be collapsed into one identifier.

### 1.3 Proposed identifier baseline
Use UUIDv7 for newly created semantic/runtime identities unless a later contract demonstrates a stronger requirement.

Initial identities:
- `project_id`
- `production_id`
- `attempt_id`
- `artifact_id`
- `graph_id`
- `transition_id`

A separate cryptographic `content_digest` identifies immutable bytes/normalized payload where applicable.

UUID is not a content proof. Content digest is not a semantic identity.

## 2. Core entity model

### Project
Long-lived creative/production container.

Minimum identity fields:
- project_id
- project_type/domain profile references
- display_name
- mutable aliases
- created_at
- canonical policy/profile references
- root production graph reference
- HIVE context namespace reference

### Production
One governed intent to produce a coherent result or result family.

Examples:
- create the launch logo system;
- build a Nerim creature set;
- render a cinematic shot;
- create a futuristic website hero;
- synthesize a voice pack.

Minimum:
- production_id
- project_id
- immutable intent/constraint snapshot reference
- requested output classes
- root graph/version reference
- lifecycle state
- supersession lineage
- creation reason/actor

### Attempt
One execution attempt against a production or production node.

Retries MUST create a new attempt identity. A failed attempt is historical evidence, not rewritten into success.

### Artifact
Stable semantic output identity.

An artifact can have many immutable revisions.

Examples:
- `artifact.logo.primary`
- `artifact.character.nerim.guardian-07`
- `artifact.web.hero.neural-brain`

Human aliases may change. `artifact_id` does not.

### Revision
Immutable materialization state of an artifact.

A revision binds:
- artifact_id
- content_digest
- producer attempt
- input lineage
- applicable Fidelity Contract / QualityDecision refs
- created_at
- format/schema version
- provenance/evidence refs

Identical bytes MAY reuse storage, but two semantic artifacts are not automatically the same artifact merely because the bytes match.

## 3. Lifecycle separation

Project lifecycle, production lifecycle and attempt lifecycle are different state machines.

### 3.1 Project lifecycle
Proposed core states:
- `CREATED`
- `ACTIVE`
- `PAUSED`
- `ARCHIVED`

Archival preserves identity/history. Destructive deletion is a retention/security operation, not a normal lifecycle transition.

### 3.2 Production lifecycle
Proposed core ladder:
- `DRAFT`
- `PLANNED`
- `READY`
- `RUNNING`
- `MATERIALIZED`
- `VALIDATING`
- `ACCEPTED`
- `RELEASED`
- `SUPERSEDED`

Exceptional states:
- `BLOCKED`
- `FAILED`
- `CANCELLED`

Rules:
- promotion is explicit;
- state rollback never rewrites history;
- correction/retry creates new receipts and, where execution occurred, new attempts;
- `SUPERSEDED` points at the replacement production/revision;
- `RELEASED` is not synonymous with `ARCHIVAL_MASTER`; quality and lifecycle are separate contracts.

### 3.3 Attempt lifecycle
Proposed:
- `QUEUED`
- `LEASED`
- `RUNNING`
- `SUCCEEDED`
- `FAILED`
- `CANCELLED`
- `ABANDONED`

Worker/scheduler mechanics are deferred to M11. M02 defines only the durable semantics those workers must obey.

## 4. Transition law

Every legal lifecycle transition produces an immutable Transition Receipt containing:
- transition_id;
- entity reference;
- from_state;
- to_state;
- lifecycle schema/version;
- reason code;
- actor/component;
- timestamp;
- causal parent receipt;
- evidence references;
- policy/contract reference where applicable.

Invalid transitions fail closed.

A crash after side effects but before a receipt is committed MUST be detectable and reconciled later; M02 S04/S05 will define the broader reconciliation rules.

## 5. Rename / alias safety

IRIS MUST support:
- renaming projects and artifacts;
- moving project folders;
- changing export destinations;
- changing UI labels;
- DCC renames;
- multiple friendly aliases

without invalidating semantic lineage.

Aliases are versioned mappings to IDs. Old aliases may resolve through explicit history or become retired; they never cause ID reuse.

## 6. Supersession and tombstones

Normal production history is append-only.

When an entity is obsolete:
- mark it superseded/archived;
- point to replacement if one exists;
- preserve provenance;
- prevent silent ID reuse.

Hard deletion belongs to retention/privacy/security policy and leaves a governed tombstone when policy allows/needs historical reference integrity.

## 7. HIVE / CORE / IRIS ownership

### IRIS
Owns production identities, lifecycle transitions, artifact/revision lineage and production graph semantics.

### HIVE
Indexes/retrieves IRIS identities and evidence as derived memory/context. HIVE does not become canonical identity authority.

### CORE
Reasons/plans against versioned IRIS identity/graph contracts. CORE may propose state transitions/actions; IRIS validates/applies them.

## 8. Domain neutrality examples

### Logo / brand
One artifact identity survives:
- full logo;
- monochrome;
- favicon;
- responsive mark;
- 3D logo treatment

as either revisions/variants/related artifacts according to later graph contracts, without relying on filenames.

### Website / futuristic cockpit
A project can carry:
- design system;
- SVG/icon family;
- neural-motion system;
- WebGPU scene;
- dashboard screens;
- release bundles

under one production lineage.

### Nerim
Character identity remains stable while geometry, textures, rig, animation, LOD and engine-delivery revisions evolve.

### Audio
Voice/music artifacts use the same semantic identity/lifecycle model without forcing visual fields.

## 9. Proposed S01 decisions

- **D-M02-S01-001:** names, paths and UI labels are never canonical identity.
- **D-M02-S01-002:** UUIDv7 is the default semantic/runtime ID format; content digest remains separate.
- **D-M02-S01-003:** project, production, attempt, artifact and revision identities are distinct.
- **D-M02-S01-004:** lifecycle transitions are append-only receipts.
- **D-M02-S01-005:** retries create new attempt IDs; history is not rewritten.
- **D-M02-S01-006:** same content may deduplicate storage without collapsing semantic artifact identity.
- **D-M02-S01-007:** project/production/attempt lifecycle machines are separate.
- **D-M02-S01-008:** supersession/archival is normal; destructive deletion is governed separately.
- **D-M02-S01-009:** IRIS is canonical for production lifecycle; HIVE is derived context; CORE is a reasoning client.
- **D-M02-S01-010:** S01 defines semantics only; scheduler/worker implementation waits for M11 and graph execution for later M02 sessions.

## 10. S01 proof plan

Before S01 can be frozen, future implementation/tests must prove:
1. rename does not change semantic identity;
2. move to another filesystem path does not change semantic identity;
3. two artifacts with identical bytes can remain distinct semantic artifacts;
4. one artifact can have multiple immutable revisions;
5. retries never rewrite failed attempts;
6. illegal lifecycle transitions fail closed;
7. duplicate transition submission is idempotent or detectably duplicated;
8. supersession preserves a traversable history chain;
9. archived entities cannot be silently reactivated without a governed transition;
10. identifiers survive serialization/round-trip;
11. concurrent creation does not collide;
12. later non-visual domains can reuse the model without adding visual-only fields.

---

# S02 — Production Graph node/dependency model
Status: `S02_PROPOSED_COMPLETE_PENDING_DISCUSSION`

## 1. Production Graph doctrine

The Production Graph is IRIS's provider-neutral causal description of how governed production inputs can become governed outputs.

It is NOT:
- a Blender node tree;
- a ComfyUI workflow;
- a Temporal workflow;
- a Dagster graph;
- a filesystem dependency list;
- a provider-specific execution plan.

Those systems may later compile from or integrate with the Production Graph.

## 2. Three graph layers

IRIS separates three graph forms.

### 2.1 Definition Graph
Immutable logical production definition.

Contains:
- graph_id + graph revision;
- nodes and ports;
- declared dependency edges;
- lifecycle/profile/policy refs;
- subgraph interfaces;
- activation rules;
- reproducibility/effect declarations.

It contains no worker PID and no transient runtime state.

### 2.2 Bound Materialization Graph
A Definition Graph bound to actual immutable inputs/revisions, selected variants, qualified model/tool/workflow versions and applicable policies.

This is the graph form from which causal fingerprints and impact cones are computed.

### 2.3 Execution Plan
Provider/runtime-specific actions compiled from a Bound Materialization Graph.

Examples:
- Blender background command;
- ComfyUI queue/workflow submission;
- image API call;
- WebGPU packaging operation.

Execution-plan internals belong to later provider/runtime modules. The Definition Graph never embeds provider-specific execution assumptions as universal semantics.

## 3. Graph topology

### 3.1 Causal graph is a DAG per graph revision
Material causality MUST be acyclic within one immutable graph revision.

Creative feedback loops such as:

`generate -> evaluate -> repair -> evaluate again`

are represented by a new iteration/epoch referencing immutable outputs from the prior epoch, not by inserting an ambiguous causal cycle into the same graph revision.

This preserves:
- deterministic dependency traversal;
- impact analysis;
- replay;
- rollback;
- cache reasoning;
- auditability.

### 3.2 Subgraphs
Reusable pipelines are represented as versioned subgraphs with an explicit interface rather than copy/paste node expansion.

Examples:
- brand master pipeline;
- character asset pipeline;
- neural website hero pipeline;
- cinematic shot pipeline;
- voice pack pipeline.

A subgraph may be expanded for analysis, but external consumers bind only to its versioned interface.

## 4. Node model

Every node has a stable `node_id` inside the graph lineage plus a versioned immutable definition.

Proposed logical node roles:
- `SOURCE` — existing revision, brief, policy, external admitted input;
- `OPERATION` — generates/transforms material;
- `VALIDATION` — evaluates a candidate and emits quality/evidence state;
- `DECISION` — selects/approves/branches among candidates;
- `COMPOSITION` — assembles multiple governed inputs;
- `SUBGRAPH` — invokes a versioned reusable graph interface;
- `DELIVERY` — creates target-facing package/export materialization.

Roles are semantic and provider-neutral. A Blender operation and a ComfyUI operation can both be `OPERATION` nodes without putting Blender/ComfyUI types into the graph kernel.

## 5. Semantic ports

Nodes communicate through explicit typed input/output ports.

Each port declares:
- port_id;
- direction;
- semantic/media type;
- schema/version;
- cardinality;
- required/optional status;
- accepted quality class/profile where applicable;
- accepted content/revision class;
- activation/variant constraints where applicable.

Proposed cardinalities:
- `ONE`
- `OPTIONAL_ONE`
- `MANY_ORDERED`
- `MANY_SET`

A connection is legal only when producer/consumer port contracts are compatible or an explicit conversion node exists.

## 6. Edge taxonomy

Edges are typed because dependency meaning controls invalidation.

### 6.1 MATERIAL_CAUSAL
Consumer result semantically/materially depends on producer output.

Relevant changes can dirty the consumer.

### 6.2 CONSTRAINT_CAUSAL
Consumer behavior depends on brief/intent/policy/quality/security/brand/etc.

Only declared dependency facets propagate invalidation.

### 6.3 EVIDENCE_CAUSAL
Validation/decision depends on evidence or QualityDecision state.

A quality-evidence change can re-run approval/delivery logic without necessarily regenerating upstream media.

### 6.4 ACTIVATION
Controls which branch/subgraph is active.

Activation changes invalidate the selected causal path.

### 6.5 ORDER_ONLY
Producer must complete before consumer starts, but a change in that dependency alone does not make the consumer material output stale.

### 6.6 OBSERVATION
Telemetry/advisory relation. It cannot create a rebuild dependency.

Provenance/lineage edges may be derived from receipts/materializations and are not automatically executable dependencies.

## 7. Dependency facets

A causal edge declares which aspects of an upstream object can affect the downstream node.

Initial facets:
- `CONTENT`
- `SEMANTICS`
- `QUALITY`
- `POLICY`
- `RIGHTS`
- `PROVENANCE`
- `DELIVERY`
- `ENVIRONMENT`

Examples:
- geometry retopology may depend on `CONTENT + SEMANTICS`;
- final publishing may depend on `CONTENT + QUALITY + RIGHTS + PROVENANCE + DELIVERY`;
- adding provenance metadata can invalidate packaging while leaving expensive generation clean;
- changing target quality acceptance can re-run validators without automatically regenerating a source candidate.

Facets are versioned/extendable but fail closed when an unknown facet is required.

## 8. Semantic dependency slices

A consumer may declare a narrow, typed selector over a structured upstream object rather than depending on the entire object.

Example:
- a roughness-bake node depends on material roughness parameters, not on a character's display name;
- a favicon export depends on approved brand geometry/colors, not on campaign copy;
- a camera render depends on scene geometry/material/light/camera facets but not unrelated project metadata.

Selectors MUST be deterministic, versioned and auditable. Hidden reads are not allowed.

This is a key IRIS performance mechanism because smaller dependency surfaces produce smaller invalidation cones.

## 9. Declared vs observed dependencies

IRIS adopts a strict rule:

> Every real direct causal dependency must be declared or explicitly admitted as a discovered dependency before its result can be trusted.

Runtime/provider integrations may observe additional reads/dependencies.

If a material dependency is observed but not declared:
- never silently trust the result;
- emit a Dependency Discovery Receipt;
- follow policy: fail/quarantine and propose a Graph Delta, or explicitly admit/recompile before promotion.

Over-declaring everything is also discouraged because it causes needless invalidation and rebuild cost.

## 10. Dynamic dependencies

Some outputs/dependencies can only be discovered after inspecting an input.

Examples:
- USD external references;
- UDIM tiles;
- generated texture sets;
- dynamically selected model adapters;
- generated web asset manifests.

Dynamic dependencies must pass through a bounded discovery phase before the dependent materialization is treated as valid.

The graph revision itself is not silently mutated mid-run. Discovery creates a versioned graph/dependency delta and a re-bound plan when needed.

## 11. Reproducibility classes

Every operation node declares a reproducibility class because cache/replay semantics differ.

Initial classes:
- `DETERMINISTIC` — qualified identical relevant inputs/environment => identical output;
- `SEEDED` — seed is explicit; exact replay only if provider/environment qualification proves it;
- `ENVIRONMENT_SENSITIVE` — output depends on declared runtime/environment fingerprint;
- `STOCHASTIC` — same request may legitimately create different output;
- `HUMAN_DECISION` — output depends on an explicit human decision receipt;
- `EXTERNAL_STATE` — output depends on admitted state outside IRIS control.

A cache key match is never sufficient to claim deterministic replay for a class that does not guarantee it.

## 12. Side-effect classes

Every executable operation declares one of:
- `NO_SIDE_EFFECT`
- `CONTROLLED_OUTPUTS`
- `EXTERNAL_MUTATION`

`EXTERNAL_MUTATION` nodes require explicit idempotency/compensation/retry policy before automatic retry. Publishing/uploading is not treated like pure rendering.

## 13. Causal fingerprint

A Bound Materialization node receives a causal fingerprint over only correctness-relevant inputs, including as applicable:
- immutable node definition;
- bound input revision/content digests;
- selected dependency slices/facets;
- intent/policy refs;
- qualified model/tool/workflow/provider versions;
- relevant environment fingerprint;
- random seed;
- reproducibility/effect class;
- human/quality decision refs.

The fingerprint is an invalidation/cache-safety primitive. It is not itself proof that a stochastic node will reproduce identical bytes.

## 14. Producer law

Within one bound graph execution:
- one output port materialization has one producing attempt;
- multiple consumers may read one immutable materialization;
- multiple candidate producers must feed an explicit selection/merge/decision node;
- silent last-writer-wins behavior is forbidden.

An Artifact may accumulate many Revisions over time, but a Revision never has ambiguous provenance.

## 15. Impact cones

Given a changed revision/facet/slice/policy, IRIS can derive a downstream Impact Cone by following only edges whose dependency semantics observe the changed facet.

Impact analysis returns:
- directly dirty nodes;
- transitively dirty nodes;
- conditionally affected nodes;
- clean nodes;
- explanation path/reason.

S04 will define the actual incremental rebuild algorithm. S02 defines the truthful graph semantics it depends on.

## 16. Explainable dirtiness

Every dirty decision should be explainable as:

`changed source -> observed facet/slice -> edge -> consumer fingerprint difference -> downstream impact`

No node should be rebuilt solely because “the project changed”.

## 17. Graph mutation law

A frozen graph revision is immutable during a production attempt.

Changes create:
- Graph Delta;
- new graph revision;
- re-binding/impact analysis.

This prevents a running attempt from changing the plan it is supposedly proving.

## 18. Quality Kernel integration

M01 QualityDecision is an explicit graph value.

A node requiring `MASTER` cannot consume a candidate that only has `PREVIEW` approval.

Quality changes can:
- dirty validation/decision/delivery nodes;
- trigger repair paths;
- block promotion;
- avoid needlessly regenerating upstream candidates when the candidate bytes did not change.

## 19. HIVE / CORE integration

### HIVE
Indexes graph definitions, dependency explanations, receipts and impact summaries as derived context. It is not graph canonical storage.

### CORE
Can reason over graph/query interfaces to propose plans, Graph Deltas or repair paths. It cannot introduce undeclared dependencies by narrative assertion.

## 20. Domain examples

### Logo / website
`Brand brief -> logo candidates -> vector validation -> selection -> responsive mark -> favicon/SVG/Web3D treatments -> quality gates -> delivery bundles`

Changing favicon export policy should not regenerate the master logo.

### Futuristic neural dashboard
`Brand DNA + interaction intent -> neural graph geometry -> shader/material -> WebGPU scene -> reduced-motion variant -> performance validation -> website bundle`

Changing accessibility motion policy can invalidate motion/delivery paths without invalidating static brand geometry.

### Nerim character
`Character DNA -> high-res model -> retopo -> UV -> textures -> rig -> animation -> gameplay-camera validation -> LOD/export`

Changing gameplay camera/readability policy can invalidate validation/LOD decisions without automatically discarding the sculpt.

### Audio
`Voice DNA + script -> synthesis -> cleanup -> identity/quality validation -> mastering -> localization/delivery`

Uses the same graph/port/edge concepts without visual-only fields.

### Persistent spokesperson / cinematic production example
`Persona DNA + brand role + script -> scene/shot graph -> performance/voice -> image/3D/video materialization -> temporal/cross-modal identity validation -> edit/VFX/music -> campaign/episode master -> localized/delivery variants`

The persona remains one stable semantic identity while shots, outfits, languages, scenes and campaign revisions change.

## 21. Proposed S02 decisions

- **D-M02-S02-001:** Production Graph is provider-neutral and versioned.
- **D-M02-S02-002:** Definition Graph, Bound Materialization Graph and Execution Plan are separate layers.
- **D-M02-S02-003:** the material causal graph is acyclic per immutable graph revision.
- **D-M02-S02-004:** iterative creative loops become new epochs/revisions, not hidden causal cycles.
- **D-M02-S02-005:** all nodes communicate through typed semantic ports.
- **D-M02-S02-006:** edges carry explicit dependency semantics; order/observation do not masquerade as material causality.
- **D-M02-S02-007:** causal dependencies are facet-aware and may be selector/slice-scoped.
- **D-M02-S02-008:** undeclared observed material dependencies fail closed or require an admitted Graph Delta.
- **D-M02-S02-009:** dynamic dependencies use a bounded discovery/recompile path; graph revisions are not mutated silently.
- **D-M02-S02-010:** operation nodes declare reproducibility and side-effect classes.
- **D-M02-S02-011:** causal fingerprints include only correctness-relevant declared dependency surfaces.
- **D-M02-S02-012:** one materialization has unambiguous producer provenance; multi-producer flows require explicit selection/merge.
- **D-M02-S02-013:** M01 QualityDecision is a first-class graph value/gate.
- **D-M02-S02-014:** every invalidation/dirty decision must provide an explainable causal path.

## 22. S02 proof plan

Future implementation must prove:
1. graph cycle detection rejects material causal cycles;
2. previous-epoch iteration remains legal without a cycle;
3. invalid port type/cardinality connections fail closed;
4. order-only changes do not dirty material output;
5. CONTENT change propagates only through edges observing CONTENT;
6. RIGHTS/PROVENANCE changes can repackage/revalidate without regenerating unrelated media;
7. selector/slice changes outside the selected field do not dirty consumer;
8. selector-relevant changes do dirty consumer;
9. undeclared observed dependency cannot be silently promoted;
10. dynamic dependency discovery produces a versioned delta/rebind;
11. incomplete dynamic discovery blocks trust;
12. deterministic causal fingerprints are stable under canonical serialization;
13. irrelevant metadata does not change a node fingerprint;
14. stochastic nodes cannot claim deterministic replay from fingerprint equality alone;
15. multiple producers require explicit selector/merge semantics;
16. impact cone includes every truly affected downstream node;
17. impact cone does not include independent branches;
18. every dirty node has an explainable reason path;
19. M01 quality-class gate blocks an under-qualified candidate;
20. all four representative domains (image/web, Nerim, logo/vector, non-visual audio) use the same graph kernel semantics.

---

# S03 — Branches, variants, snapshots and rollback
Status: `S03_PROPOSED_COMPLETE_PENDING_DISCUSSION`

## 1. Four concepts that MUST remain separate

IRIS does not use one generic "version" concept for every creative alternative.

### 1.1 Branch
A mutable named/reference line of creative or production development.

A Branch points to one current immutable Snapshot and advances by creating/admitting new Snapshots.

Branch name is an alias. Branch identity is stable.

### 1.2 Variant
A compositional alternative inside one semantic production/artifact family.

Examples:
- outfit = formal / casual / launch-event;
- language = pt-BR / en-US / es-ES;
- logo = full / compact / monochrome;
- platform = web / mobile / game;
- motion = full / reduced;
- camera package = cinematic / product-demo.

A Variant does not automatically deserve a whole Branch.

### 1.3 Snapshot
An immutable point-in-time closure over production state.

It captures references to:
- project/production identity;
- graph revision;
- selected variants;
- artifact/revision map;
- intent/policy/quality refs;
- relevant environment/qualification refs;
- parent snapshot(s);
- transition/evidence refs.

A Snapshot points to immutable revisions/CAS objects rather than copying large media bytes.

### 1.4 Rollback
A governed operation that creates a new current state derived from an earlier Snapshot.

Rollback NEVER deletes the intervening history and never rewrites an old Snapshot.

## 2. Branch identity and refs

Proposed Branch record:
- branch_id;
- project_id / production_id;
- branch_type/profile;
- display_name / aliases;
- head_snapshot_id;
- fork_point_snapshot_id;
- parent_branch_id where applicable;
- policy refs;
- lifecycle state;
- created_at / creator;
- retention/pin policy.

A branch ref is mutable; every Snapshot it points to is immutable.

This deliberately follows the useful separation seen in Git between lightweight movable branch refs and immutable commit/snapshot history, without requiring IRIS media to live inside Git.

## 3. Branch kinds are policy, not new kernels

Suggested initial profiles:
- `CANONICAL` — accepted/main production line;
- `EXPERIMENT` — bounded creative exploration;
- `CAMPAIGN` — marketing/campaign-specific direction;
- `EPISODE_SHOT` — scene/shot-level production line where needed;
- `RELEASE` — stabilization/delivery line.

These are policy profiles over one branch mechanism. IRIS must not implement five incompatible branch systems.

## 4. Fork law

A fork creates a new Branch from a specific immutable Snapshot.

Fork receipt records:
- source branch/snapshot;
- new branch identity;
- reason;
- initial variant selections;
- inherited pins/policies;
- actor;
- time.

A branch cannot silently "start from current" without persisting the exact fork-point Snapshot.

## 5. Variant Sets

Variants are organized into typed Variant Sets.

Examples:
- `outfit = {formal, casual, keynote}`
- `language = {pt-BR, en-US}`
- `brand-mark = {full, compact, icon}`
- `motion-policy = {full, reduced, static}`
- `render-tier = {preview, master}`

Each Variant Set declares:
- variant_set_id;
- semantic purpose;
- allowed options;
- default/none behavior;
- compatibility/constraint rules;
- affected graph facets/ports;
- whether selection changes require revalidation/rebuild.

OpenUSD VariantSets are a useful reference for non-destructive switchable alternatives, but IRIS Variant Sets are cross-domain and do not inherit USD scene-specific semantics.

## 6. Variant Constraint Graph

Not every Cartesian product is legal.

Example:
- `outfit=keynote` may require `event=launch`;
- `motion-policy=reduced` may prohibit a particle-heavy WebGPU treatment;
- `language=ja-JP` may require a different typography/layout node;
- a corporate spokesperson's "approved hairstyle B" may be legal only for some campaign profile.

IRIS therefore stores compatibility constraints separately from the Variant Set values.

Invalid combinations fail before expensive execution.

## 7. Sparse / lazy variant materialization

IRIS never materializes all possible variant combinations just because they exist.

A variant combination is materialized only when:
- requested;
- required downstream;
- selected by a campaign/release profile;
- needed for testing/quality coverage.

Shared upstream revisions remain structurally shared.

This prevents a combinatorial explosion such as:
`4 outfits × 6 languages × 5 aspect ratios × 3 motion modes × 4 platforms`.

## 8. Persona continuity rule

For a persistent virtual spokesperson/digital ambassador:

### Variant-safe changes
May include, within approved policy:
- outfit;
- background;
- language;
- camera;
- lighting;
- campaign styling;
- approved hairstyle variant;
- emotional performance range.

### Identity-anchor changes
Face/body identity anchors, voice identity core, canonical persona role and other protected identity anchors are NOT ordinary variants.

Changing protected anchors requires:
- explicit identity migration, or
- creation of a new persona/semantic identity branch/fork according to later M05/M39 policy.

This prevents an "outfit variant" mechanism from slowly mutating the spokesperson into a different person.

## 9. Snapshot classes

Proposed Snapshot completeness classes:

### LOGICAL_SNAPSHOT
Captures graph/project/variant/policy state but may reference outputs not yet materialized.

### MATERIALIZED_SNAPSHOT
All required selected graph outputs have immutable materialization refs.

### VALIDATED_SNAPSHOT
Required M01 QualityDecisions/evidence are bound and satisfy declared gates for the snapshot profile.

### RELEASE_SNAPSHOT
A validated closure additionally binds delivery/provenance/rights/release evidence required by the release profile.

A class is a completeness claim, not merely a label.

## 10. Snapshot closure manifest

Every Snapshot has a canonical Closure Manifest.

It answers:
- which graph revision?
- which branch/fork ancestry?
- which variant selections?
- which artifact revisions?
- which quality decisions?
- which policies/rights/provenance refs?
- which environment/tool/model qualification refs matter?
- which dependencies are unresolved or external?

A Snapshot claiming MATERIALIZED/VALIDATED/RELEASE completeness fails closed if required closure references are missing.

## 11. Structural sharing

Snapshots store references to immutable objects/revisions.

If Snapshot B differs from Snapshot A only in one subtitle, outfit, texture or graph node:
- unchanged assets remain referenced;
- only the changed delta/revisions are new;
- storage deduplication belongs to CAS/M55;
- semantic identities remain separate from byte deduplication.

This enables cheap creative branches even with very large media projects.

## 12. Semantic diff

A Snapshot Diff is not just "which files differ".

It classifies deltas such as:
- graph topology;
- node definition;
- dependency facet/slice;
- variant selection;
- intent/brief;
- semantic asset revision;
- quality decision;
- rights/provenance;
- delivery policy;
- environment/tool/model qualification.

Diff output drives merge, review and S04 impact/rebuild planning.

## 13. Three-way semantic merge

IRIS merge uses:
- merge base Snapshot;
- target head Snapshot;
- source head Snapshot.

Merge is object/graph semantic, not blind byte merging.

Safe auto-merge examples:
- independent graph nodes edited on separate branches;
- disjoint Variant Sets;
- independent metadata fields with compatible policies.

Conflict examples:
- both branches modify the same node definition differently;
- both replace the same artifact revision differently;
- one branch deletes a node the other depends on;
- incompatible variant constraints;
- identity-anchor disagreement;
- rights/policy conflict;
- one branch lowers required Quality Class;
- divergent release/published state.

Binary media is never "merged" by averaging bytes. Competing revisions require explicit selection, recomposition, regeneration or a domain merge operation.

## 14. Conflict taxonomy

Initial conflict families:
- `TOPOLOGY_CONFLICT`
- `NODE_DEFINITION_CONFLICT`
- `ARTIFACT_REVISION_CONFLICT`
- `VARIANT_SELECTION_CONFLICT`
- `VARIANT_CONSTRAINT_CONFLICT`
- `IDENTITY_ANCHOR_CONFLICT`
- `QUALITY_POLICY_CONFLICT`
- `RIGHTS_PROVENANCE_CONFLICT`
- `DELIVERY_RELEASE_CONFLICT`
- `SIDE_EFFECT_CONFLICT`

Each conflict is explicit and has legal resolution strategies.

Unknown conflict classes fail closed.

## 15. Merge Receipt

A merge produces:
- merge_id;
- base/source/target Snapshot refs;
- semantic diff refs;
- automatically resolved items;
- manually resolved items;
- unresolved conflicts;
- resulting Snapshot;
- actor/tool/version;
- evidence and policy refs.

A branch head cannot advance to a merge result with unresolved blocking conflicts.

## 16. Graph Delta / semantic cherry-pick

IRIS should support transplanting a bounded admitted change without merging an entire branch.

Examples:
- bring one approved logo geometry improvement into a campaign branch;
- reuse one rig correction across character delivery branches;
- apply one subtitle timing fix to another locale branch.

The transplant is a versioned Graph/Production Delta with:
- source Snapshot;
- target Snapshot;
- dependency preconditions;
- semantic scope;
- resulting conflicts/impact cone.

It is not an untracked manual copy.

## 17. Experiment branches

Experiments are cheap, bounded Branches with:
- origin Snapshot;
- hypothesis/intent;
- budget;
- retention TTL or pin;
- allowed providers/models;
- acceptance criteria.

Examples:
- compare two image models;
- test two avatar outfits;
- try a new WebGPU neural shader;
- test an alternate camera style;
- A/B commercial hook variants.

Winning experiment outputs can be promoted by a governed delta/merge, preserving provenance.

Losing experiments remain auditable until retention policy allows cleanup.

## 18. Campaign / episode / shot lineage

For film, advertising and recurring avatar content:

- a Series/Campaign can have a canonical production branch;
- episodes/campaign waves may fork from approved baseline Snapshots;
- shots can branch only when independent iteration warrants it;
- persona/Brand DNA anchors remain inherited/protected;
- final episode/campaign Snapshot records exact shot/persona/music/voice/brand revisions.

This allows a company spokesperson to stay consistent across 100 videos while each episode evolves independently.

## 19. Safe rollback

Rollback means:
1. select an earlier trusted Snapshot;
2. verify it is reachable/admissible;
3. calculate semantic diff from current head to rollback target;
4. compute impact / incompatible external side effects;
5. create a new rollback Snapshot/Transition Receipt;
6. move the Branch ref only after policy gates pass.

History between current and target remains preserved.

## 20. External side-effect rollback fence

IRIS distinguishes state rollback from undoing the outside world.

Examples:
- moving a branch back does NOT automatically delete a YouTube upload;
- restoring an older website package does NOT imply payment/campaign state has rolled back;
- reverting a project snapshot does NOT revoke already-issued rights/legal records.

External mutations require explicit compensation/release procedures.

## 21. Time travel / inspection

Any immutable Snapshot can be opened read-only for:
- comparison;
- evidence review;
- provenance;
- quality regression;
- export reproduction when allowed;
- branch/fork creation.

Read-only time travel must not mutate the historical Snapshot.

## 22. Reachability, pins and cleanup

A Snapshot/revision can be retained because it is:
- reachable from a live Branch;
- referenced by a Release/Validated Snapshot;
- pinned for benchmark/golden evidence;
- required by rights/provenance/audit;
- retained by policy/TTL.

Garbage collection may remove unneeded materializations only when reachability/retention policy says they are disposable.

A semantic tombstone remains when identity/provenance policy requires it.

## 23. Branch vs Variant decision rule

Use a **Variant** when alternatives:
- belong to one semantic identity/family;
- are expected to coexist;
- can be described by a bounded typed axis;
- share most lineage/dependencies.

Use a **Branch** when alternatives:
- represent competing or independently evolving creative directions;
- require separate history/review/promotion;
- may change graph topology/intent materially;
- need independent rollback/merge.

A branch may contain Variant Sets.

## 24. Proposed S03 decisions

- **D-M02-S03-001:** Branch refs are mutable; Snapshots are immutable.
- **D-M02-S03-002:** branch name/alias is not branch identity.
- **D-M02-S03-003:** Branch, Variant, Snapshot and Rollback are separate concepts.
- **D-M02-S03-004:** forks always record an exact immutable source Snapshot.
- **D-M02-S03-005:** Variant Sets are typed, constrained and lazily materialized.
- **D-M02-S03-006:** persona protected identity anchors are not ordinary variants.
- **D-M02-S03-007:** Snapshot completeness claims are LOGICAL/MATERIALIZED/VALIDATED/RELEASE and require closure evidence.
- **D-M02-S03-008:** Snapshots structurally share immutable revisions/CAS objects instead of duplicating media.
- **D-M02-S03-009:** merge is three-way and semantic; binary media is not blind-byte merged.
- **D-M02-S03-010:** unresolved blocking conflicts prevent branch-head advancement.
- **D-M02-S03-011:** bounded Graph/Production Deltas provide cherry-pick-like transplant semantics.
- **D-M02-S03-012:** experiments are explicit bounded branches with promotion/retention policy.
- **D-M02-S03-013:** rollback creates new history; it never erases intervening history.
- **D-M02-S03-014:** branch rollback does not automatically compensate external side effects.
- **D-M02-S03-015:** Snapshot GC is reachability/pin/rights-policy aware.
- **D-M02-S03-016:** recurring films/campaigns/avatar content use branch/snapshot lineage while persona/brand anchors stay protected.

## 25. S03 proof plan

Future implementation must prove:
1. Branch ref can move while old Snapshots remain immutable/readable;
2. renaming branch does not change branch_id;
3. fork persists exact fork-point Snapshot;
4. Variant selection never mutates base variant definition;
5. invalid variant combination fails before execution;
6. sparse variant materialization does not create unused combinations;
7. persona outfit/language variants preserve identity anchors;
8. protected persona-anchor mutation cannot sneak through a normal Variant Set;
9. LOGICAL cannot be relabeled VALIDATED without closure evidence;
10. structural sharing avoids duplicate large media references;
11. semantic diff distinguishes graph/variant/quality/rights/delivery deltas;
12. three-way merge auto-merges disjoint compatible changes;
13. same-node divergent edits create an explicit conflict;
14. competing binary/media revisions require explicit resolution;
15. unresolved conflict prevents branch-head move;
16. cherry-pick/Graph Delta checks dependency preconditions;
17. experiment promotion preserves origin/hypothesis/provenance;
18. rollback creates a new Snapshot/receipt rather than deleting history;
19. rollback blocks or flags incompatible external side effects;
20. time-travel inspection is read-only;
21. GC never removes pinned/reachable/release/provenance-required objects;
22. 100 recurring avatar episodes can share persona baseline while carrying independent episode/shot revisions;
23. multilingual/commercial variants can share heavy upstream media where causally legal;
24. merge/rollback output feeds S04 impact-cone/rebuild logic deterministically.

---

# S04 — Creative Build System and incremental rebuild semantics
Status: `NOT_STARTED`

# S05 — Production state machine, promotion and archive
Status: `NOT_STARTED`

## M02 current disposition

S01, S02 and S03 are proposed complete for discussion. No implementation is authorized. Technology candidates remain PROPOSED until M02 Final Technology Review. Next session: S04 — Creative Build System and incremental rebuild semantics.
