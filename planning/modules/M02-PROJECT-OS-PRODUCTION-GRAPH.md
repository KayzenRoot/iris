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
Status: `NOT_STARTED`

# S04 — Creative Build System and incremental rebuild semantics
Status: `NOT_STARTED`

# S05 — Production state machine, promotion and archive
Status: `NOT_STARTED`

## M02 current disposition

S01 and S02 are proposed complete for discussion. No implementation is authorized. Technology candidates remain PROPOSED until M02 Final Technology Review. Next session: S03 — Branches, variants, snapshots and rollback.
