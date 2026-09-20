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
Status: `NOT_STARTED`

# S03 — Branches, variants, snapshots and rollback
Status: `NOT_STARTED`

# S04 — Creative Build System and incremental rebuild semantics
Status: `NOT_STARTED`

# S05 — Production state machine, promotion and archive
Status: `NOT_STARTED`

## S01 disposition

S01 is proposed complete for discussion. No implementation is authorized. Technology candidates remain PROPOSED until M02 Final Technology Review.
