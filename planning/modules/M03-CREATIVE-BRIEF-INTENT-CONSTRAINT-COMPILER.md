# M03 — Creative Brief, Intent & Constraint Compiler

Status: `S01_PROPOSED_COMPLETE_PENDING_DISCUSSION`
Module: `M03`
Area: `A — Product Constitution & Production OS`
Planning issue: `#17`
Authorized baseline: `bb5201fea5c394cf4dd7a169ca60df7924153e92`

## Mission

M03 turns human creative direction into a versioned, provider-neutral, explainable semantic contract that later IRIS modules can compile and execute without confusing natural-language wording with canonical intent.

M03 does **not** generate media. It captures, normalizes, versions and explains what the production is trying to achieve, what freedom remains, what must never happen, and which external contracts/policies the production must obey.

M03 must preserve creative freedom rather than reducing every brief to rigid prompt text. The compiler should make intent executable without flattening nuance.

## Ownership boundary

### M03 owns
- Creative Brief identity and immutable revision semantics;
- intent capture and semantic normalization;
- explicit goals, desired outcomes and requested deliverables;
- creative degrees of freedom;
- ambiguity/confidence representation;
- source/provenance for intent statements;
- later S02 constraint semantics;
- later S03 compilation to M01 Fidelity Contract references;
- later S04 provider-neutral Execution Intent;
- later S05 conflict/override/version policy.

### M03 does not own
- M01 quality judgment, scores, gates or promotion authority;
- M02 project/production/graph/lifecycle identity;
- M04 Scene/Character/Asset/Camera/etc. IR schemas;
- provider prompts/workflows;
- Blender/ComfyUI/model-specific parameters;
- worker scheduling, VRAM planning or runtime placement;
- HIVE as canonical truth.

### Inter-module law
M02 references M03 brief/intent/constraint revisions. M03 may consume project/production references from M02, but it cannot redefine M02 identity or lifecycle. M01 remains the sole authority for quality semantics. M04 consumes M03 compiled execution intent rather than raw user prose.

---

# S01 — Creative brief schema and intent capture

## 1. Design goals

S01 must make five things true:

1. one human request can be represented without losing its original wording;
2. normalized intent is machine-readable and provider-neutral;
3. inferred meaning is distinguishable from explicit user statements;
4. ambiguity is represented rather than silently guessed away;
5. semantically equivalent briefs can be recognized for reuse/cache without pretending text equality equals semantic equality.

## 2. Creative Brief identity

A Creative Brief is a stable semantic object with immutable revisions.

### Stable identity
- `creative_brief_id`
- belongs to one M02 production or reusable brief library entry
- survives edits, clarifications and wording changes

### Immutable revision
Each change creates a new `brief_revision_id` and binds:
- parent revision(s);
- raw input references;
- normalized Intent Model;
- declared output targets;
- referenced policies/contracts;
- compiler version;
- semantic fingerprint;
- change reason;
- author/actor;
- timestamp;
- evidence/provenance refs.

A revision is never edited in place after admission.

## 3. Raw input preservation

M03 stores or references the original input independently from normalized intent.

Possible source classes:
- user text;
- structured form;
- uploaded creative document;
- selected reference asset;
- voice transcript;
- UI choice;
- imported campaign/product metadata;
- HIVE-derived context proposal;
- CORE/agent proposal.

Rules:
- normalized fields never erase the original source;
- source order and provenance are retained;
- derived context must be labeled as derived;
- an agent inference must never be rewritten as a user statement.

## 4. Intent Model

S01 introduces a provider-neutral `Intent Model`.

The model is composed of versioned **Intent Statements** rather than one giant prompt.

Each statement contains at minimum:
- `statement_id`;
- `semantic_path`;
- `value` or typed reference;
- `source_ref`;
- `source_kind`;
- `origin` = EXPLICIT / DERIVED / INFERRED / DEFAULTED;
- `confidence`;
- `authority`;
- `scope`;
- `rationale_ref` when derived/inferred;
- `status` = ACTIVE / SUPERSEDED / REJECTED;
- `schema_version`.

S02 will add detailed constraint strength/taxonomy. S01 only establishes the statement substrate.

## 5. Core brief sections

The S01 schema supports domain-neutral sections:

### 5.1 Purpose
Why this production exists.

Examples:
- launch a product;
- produce a cinematic scene;
- create a persistent corporate spokesperson campaign;
- build a game asset family;
- create a music identity.

### 5.2 Audience / recipient
Who or what the output is for:
- human audience;
- customer segment;
- game engine/runtime;
- social platform;
- website;
- internal production use.

Audience may be unknown. Unknown is explicit state, not empty-string ambiguity.

### 5.3 Desired outcome
The intended effect or measurable production outcome, separate from implementation.

Examples:
- premium futuristic identity;
- trustworthy enterprise spokesperson;
- readable logo at favicon scale;
- emotionally tense shot;
- seamless looping locomotion;
- clean product hero image.

### 5.4 Deliverable intent
What families of outputs are requested, without forcing provider formats prematurely.

Examples:
- still image family;
- video sequence;
- 3D asset;
- animation;
- audio/music;
- brand system;
- web visual package;
- cross-modal persona package.

Concrete codecs, model names and provider workflows belong later.

### 5.5 Creative direction
Semantic descriptors such as:
- mood;
- visual/sonic/narrative tone;
- era/context;
- realism/stylization direction;
- pacing;
- composition intent;
- performance/acting intent;
- brand/persona references.

These are structured semantic directions, not opaque comma-separated prompt tokens.

### 5.6 References
References are typed:
- inspiration;
- identity anchor;
- must-match;
- structural;
- style;
- content;
- anti-reference.

S02 will define strength/negative semantics in detail.

### 5.7 Open questions
Unresolved choices are first-class data.

Each open question records:
- question;
- affected semantic paths;
- impact estimate;
- whether execution may continue under uncertainty;
- default/fallback policy if explicitly authorized.

## 6. Explicit vs inferred intent

M03 forbids hidden semantic promotion.

An inference can be useful but must carry:
- origin = INFERRED;
- confidence;
- rationale/evidence;
- compiler identity/version.

A user or authorized policy can later accept the inference, converting it through an explicit revision rather than mutating provenance.

This prevents:
- “cinematic” silently becoming one specific lens/model;
- “premium” silently forcing gold/black;
- “realistic” silently becoming photoreal human;
- “for TikTok” silently deciding aspect/length before platform profile compilation.

## 7. Ambiguity model

S01 introduces `Ambiguity Record`.

Types:
- missing information;
- multi-interpretation;
- contradictory wording;
- underspecified range;
- unresolved reference;
- uncertain inference;
- domain-dependent meaning.

Each ambiguity binds:
- semantic paths;
- candidate interpretations;
- confidence;
- consequence class;
- clarification priority.

### Clarification priority
- `BLOCKING` — cannot safely compile;
- `QUALITY_CRITICAL` — execution possible but likely to miss intended quality;
- `COST_CRITICAL` — ambiguity may create major waste;
- `NON_BLOCKING` — system may proceed with explicit policy;
- `CREATIVE_FREEDOM` — intentionally left open.

The compiler must not turn creative freedom into a “missing field” bug.

## 8. Creative Degrees-of-Freedom Map

M03 explicitly records what is **not fixed**.

A `Freedom Zone` can say:
- composition may vary;
- wardrobe can vary within Brand DNA;
- camera angle is open;
- exact melody is open;
- environment may be invented;
- wording may be rewritten while preserving claim semantics.

This is essential because over-constrained generative systems collapse exploration quality.

Freedom Zones later influence:
- candidate diversity;
- branching/variants in M02;
- provider compiler choices;
- evaluation expectations.

## 9. Authority and provenance

Intent sources have explicit authority classes.

Initial model:
- `USER_EXPLICIT`
- `PROJECT_POLICY`
- `APPROVED_REFERENCE`
- `DOMAIN_PROFILE`
- `DERIVED_CONTEXT`
- `AGENT_PROPOSAL`
- `SYSTEM_DEFAULT`

Authority is not identical to confidence.

A low-confidence user statement can still outrank a high-confidence system guess.

S05 will define conflict/override resolution.

## 10. Context economy

M03 must minimize unnecessary LLM/context consumption.

Canonical brief state is structured and addressable. A downstream task should receive only the semantic slices it declares.

### Minimum Sufficient Intent Slice
A consumer requests specific semantic paths plus required provenance/constraints.

Example:
a favicon compiler should not receive full film narrative, voice direction and unrelated campaign history.

Benefits:
- lower token use;
- smaller causal fingerprints;
- better cache reuse;
- fewer accidental prompt interactions;
- easier explanation of what influenced an output.

M52/HIVE later supplies retrieval mechanics. M03 defines the semantic slice contract only.

## 11. Semantic fingerprint

Each immutable brief revision receives a `semantic_intent_fingerprint` over normalized correctness-relevant intent.

Rules:
- raw wording changes that do not change admitted semantics may preserve a semantic-equivalence relation;
- the immutable revision ID still changes;
- compiler/schema version participates in equivalence safety;
- inferred/defaulted statements are included;
- provenance-sensitive policies may require source identity in the fingerprint.

M02 can consume this reference in causal fingerprints without understanding M03 internals.

## 12. Semantic equivalence

S01 distinguishes:
- textual equality;
- structural equality;
- semantic equivalence;
- policy equivalence.

Two briefs can be semantically equivalent for one consumer but not another.

Example:
“warm sunset lighting” and “golden-hour warm light” may be equivalent for a broad mood selector but not for a strict photography profile.

Equivalence must be typed and versioned. It is never a universal fuzzy-text shortcut.

## 13. Multilingual capture

Canonical semantics are language-neutral references/values where feasible, while original wording remains preserved.

Translation is not allowed to silently strengthen/weaken intent.

A translated statement retains:
- original source;
- source locale;
- translated representation;
- translation provenance;
- semantic confidence.

M47 owns full localization/culturalization. M03 only preserves intent fidelity across capture languages.

## 14. Sensitive / rights-aware references

S01 records reference type and provenance hooks but does not implement legal policy.

Identity/voice/persona/reference material can carry:
- rights/consent reference;
- usage boundary reference;
- provenance reference;
- restricted-vault reference.

M53/M54 later decide rights/security policy.

## 15. Failure philosophy

M03 fails closed on:
- invalid schema;
- missing required semantic identity;
- unresolved BLOCKING ambiguity;
- forged/missing required provenance;
- compiler version mismatch;
- unknown mandatory semantic extension.

M03 does not fail merely because:
- creative freedom exists;
- optional details are absent;
- the user used natural, non-technical language.

## 16. Explainability

Every normalized statement must be answerable with:
- What does IRIS think the user wants?
- Where did that understanding come from?
- Was it explicit, inferred, defaulted or derived?
- How confident is it?
- Which downstream consumers read it?
- What would change if this statement changed?

This explanation model is mandatory, not UI decoration.

## 17. S01 decisions proposed

- **D-M03-S01-001:** preserve raw creative input separately from normalized intent.
- **D-M03-S01-002:** Creative Brief has stable identity plus immutable revisions.
- **D-M03-S01-003:** canonical intent is a set/graph of typed Intent Statements, not one provider prompt.
- **D-M03-S01-004:** explicit, inferred, derived and defaulted meaning are never conflated.
- **D-M03-S01-005:** ambiguity is first-class and typed; creative freedom is not treated as missing data.
- **D-M03-S01-006:** downstream consumers receive Minimum Sufficient Intent Slices.
- **D-M03-S01-007:** semantic fingerprints are versioned and provider-neutral.
- **D-M03-S01-008:** semantic equivalence is consumer/profile scoped, not global fuzzy equality.
- **D-M03-S01-009:** authority and confidence are independent dimensions.
- **D-M03-S01-010:** M03 never compiles provider-specific prompt/workflow parameters in S01.
- **D-M03-S01-011:** M01 remains sole quality authority; M03 only references/compiles quality intent later.
- **D-M03-S01-012:** M02 remains canonical for production/graph lifecycle; M03 supplies versioned intent refs.
- **D-M03-S01-013:** original language/provenance survives multilingual normalization.
- **D-M03-S01-014:** hidden semantic promotion is forbidden; accepting an inference requires a new explicit revision.
- **D-M03-S01-015:** explainability/provenance is part of the contract, not optional metadata.

## 18. S01 proof plan

Future implementation/tests must prove at least:

1. wording edit can create a new brief revision without changing stable brief identity;
2. explicit user intent cannot be overwritten by lower-authority inferred/defaulted state;
3. inferred statements retain rationale and compiler provenance;
4. BLOCKING ambiguity prevents compile/promotion;
5. CREATIVE_FREEDOM ambiguity does not fail the brief;
6. one brief can serve image/video/3D/audio without visual-only required fields;
7. downstream semantic slice excludes unrelated sections;
8. semantic fingerprint changes when correctness-relevant admitted intent changes;
9. raw text changes alone do not automatically imply semantic inequality;
10. unknown mandatory semantic extension fails closed;
11. multilingual normalization preserves source/provenance;
12. M02 can reference brief revision/fingerprint without importing M03 internals;
13. no provider/model/DCC-specific field is needed;
14. no M01 quality-decision authority is duplicated;
15. serialization/round-trip preserves origin, authority, confidence and ambiguity state.

---

## Current disposition

S01 is proposed complete for discussion.

No M03 implementation is authorized.

Next legal planning action after S01 review/acceptance: **S02 — Constraint taxonomy and negative constraints**.
