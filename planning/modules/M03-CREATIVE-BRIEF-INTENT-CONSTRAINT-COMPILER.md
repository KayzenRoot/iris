# M03 — Creative Brief, Intent & Constraint Compiler

Status: `S03_PROPOSED_COMPLETE_PENDING_DISCUSSION`
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


---

# S02 — Constraint taxonomy and negative constraints

Status: `S02_PROPOSED_COMPLETE_PENDING_DISCUSSION`

## 1. Constraint doctrine

A constraint is not a prompt suffix. It is a versioned semantic rule that narrows the legal solution space of a Creative Brief.

M03 constraints describe what an acceptable interpretation/execution may or may not do. Providers may later translate them into prompts, masks, graph choices, solver bounds, policies, validators or workflow parameters, but those provider encodings are projections rather than canonical truth.

## 2. Constraint object

Every constraint has at minimum:
- `constraint_id`;
- `brief_revision_id` or reusable policy/profile owner;
- `semantic_target` / affected paths;
- `predicate` or typed relation;
- `polarity`;
- `strength`;
- `scope`;
- `origin` and source reference;
- authority + confidence;
- applicability condition;
- tolerance semantics where relevant;
- rationale/evidence reference;
- schema/compiler version;
- lifecycle status.

Constraints are immutable inside an admitted brief revision. Changes create semantic deltas/new revisions.

## 3. Polarity

Initial polarity classes:
- `REQUIRE` — state/property must hold;
- `FORBID` — state/property must not hold;
- `PREFER` — optimize toward;
- `AVOID` — optimize away from without making it illegal;
- `ALLOW` — explicitly open a region otherwise constrained by a broader rule.

`FORBID` is not represented by injecting words into a model-specific negative prompt.

## 4. Strength

Initial strength levels:
- `HARD` — violation makes this interpretation/execution inadmissible;
- `GUARDED` — violation requires explicit authorized override/escalation;
- `SOFT` — optimization objective, may trade off against peers;
- `ADVISORY` — informative direction that does not by itself block;
- `EXPERIMENTAL` — intentionally relaxed for an exploration branch.

Strength belongs to the constraint contract, not to provider prompt weight syntax.

M01 quality gates remain M01-owned. M03 may compile requested quality intent into M01 Fidelity Contract inputs/references later, but cannot create an alternate quality authority by labeling a preference HARD.

## 5. Constraint taxonomy

### 5.1 Semantic/content
What the output is or communicates.

Examples:
- product must remain recognizable;
- scene must contain two characters;
- advertisement must not state an unapproved claim.

### 5.2 Identity
Constraints over stable identity anchors supplied by M05/M39/M40/M41/M46.

Examples:
- preserve spokesperson identity;
- do not mutate approved logo geometry;
- preserve Voice DNA reference.

M03 references identity contracts. It does not define DNA internals.

### 5.3 Composition/spatial
Relationships such as framing, order, relative position, occupancy or layout intent.

The canonical rule is semantic. Exact camera/scene coordinates belong to M04+ when compiled.

### 5.4 Temporal/motion
Pacing, duration ranges, ordering, continuity intent and forbidden transitions.

### 5.5 Style/brand
Style direction, brand boundaries, tone and anti-style rules.

### 5.6 Technical/delivery
Target capabilities and output requirements that are genuinely known at brief time.

Codec/provider/runtime details are deferred to M59 or provider compilers unless the user explicitly made them a hard requirement.

### 5.7 Rights/provenance/security
References to M53/M54 policy obligations.

M03 carries the constraint reference and applicability, not the legal/security engine.

### 5.8 Quality-request
Requested quality rung/dimensions expressed as inputs to M01 contract compilation in S03.

M03 does not judge satisfaction.

### 5.9 Cost/time/resource
User/project business constraints such as deadline, budget class or hardware availability.

Runtime placement/VRAM strategy remains M07-M13.

### 5.10 Accessibility/localization
Requested languages, captions, readability, cultural or accessibility requirements by reference. M47 owns full localization/culturalization semantics.

## 6. Negative constraints as first-class semantics

Negative constraints identify forbidden properties, relationships, transformations or outcomes.

Examples:
- must not alter approved facial identity;
- must not add text to a clean product image;
- must not crop the logo clear-space zone;
- must not introduce extra fingers/limbs;
- must not show a competitor mark;
- must not make an unapproved medical/financial claim;
- must not change canonical character weapon;
- must avoid camera shake beyond declared tolerance.

A negative constraint may later compile to:
- a provider negative prompt fragment;
- mask/protected region;
- graph exclusion;
- model/workflow capability filter;
- validator requirement;
- repair trigger;
- release gate reference.

Those mechanisms are interchangeable implementations of the same semantic rule.

## 7. Anti-reference semantics

A reference can express “do not become this” without implying every visual property of the reference is forbidden.

An Anti-Reference binds:
- reference asset/revision;
- forbidden semantic facets;
- comparison scope;
- tolerance;
- explanation.

Example: a competing logo may be an anti-reference for silhouette similarity while its color palette is irrelevant.

This avoids accidental over-constraint from whole-image similarity.

## 8. Constraint predicates

Provider-neutral predicate families include:
- equality / inequality;
- membership / exclusion;
- numeric range;
- cardinality;
- existence / absence;
- ordering;
- relational / graph relation;
- semantic compatibility;
- threshold by external metric reference;
- protected-anchor preservation;
- temporal duration/sequence relation;
- capability requirement.

Arbitrary executable code is forbidden inside canonical constraint data.

Unknown mandatory predicate types fail closed.

## 9. Scope mesh

Constraints can scope to:
- entire project;
- production;
- branch/variant set;
- deliverable family;
- one artifact;
- scene/shot/region/time span;
- semantic path/facet;
- audience/destination profile.

Narrower scope does not automatically mean higher authority. S05 will define conflict precedence.

## 10. Conditional constraints

A constraint may activate only when a declared condition holds.

Examples:
- if output is a favicon, minimum line thickness rule applies;
- if a shot uses the persistent spokesperson, identity-preservation constraints activate;
- if destination is social vertical video, safe-area intent applies;
- if a branch is marked experimental, selected SOFT constraints may relax.

Conditions are provider-neutral and versioned.

Hidden runtime branching is not allowed to invent a new canonical constraint.

## 11. Tolerance envelopes

Not every constraint is binary.

Typed tolerance can express:
- numeric interval;
- categorical acceptable set;
- bounded deviation from anchor;
- temporal tolerance;
- spatial tolerance;
- metric threshold reference.

Tolerance must carry units/semantic meaning. “0.8” without metric/version/unit is invalid.

## 12. Cross-modal constraints

One semantic rule may bind multiple modalities.

Examples:
- spokesperson identity spans face/body/voice/mannerism;
- Brand DNA spans logo/color/typography/voice/music;
- narrative canon constrains image/video/dialogue;
- a product color must match across still, video and 3D.

M03 owns the cross-modal constraint relation; domain modules own the modality-specific representation/evidence.

## 13. Constraint bundles

Reusable bundles group compatible constraints by explicit version.

Examples:
- corporate brand pack;
- persistent spokesperson public-release pack;
- ecommerce product fidelity pack;
- game-ready character pack;
- family-safe campaign pack;
- destination-specific delivery intent pack.

Bundle inclusion is explicit. A bundle does not silently update inside an immutable brief revision.

## 14. Constraint normal form

M03 normalizes semantically comparable constraints into a canonical representation before fingerprinting/conflict analysis.

Normalization may:
- canonicalize units;
- normalize set ordering;
- resolve aliases to semantic IDs;
- split compound statements into atomic rules;
- bind explicit scope;
- attach schema versions.

Normalization must not strengthen or weaken the rule.

Raw/source representation remains preserved.

## 15. Constraint slicing and performance

Downstream consumers receive only constraints whose scope/facets can affect them.

A `Minimum Sufficient Constraint Slice` contains:
- relevant canonical rules;
- necessary provenance/authority;
- active bundle refs;
- conflict/override receipts applicable to those rules.

This supports:
- smaller LLM prompts;
- smaller M02 invalidation cones;
- provider cache reuse;
- less accidental interaction between unrelated rules.

## 16. Constraint fingerprints

Constraint state contributes a versioned `constraint_fingerprint`.

Fingerprint includes correctness-relevant normalized rule semantics, scope, strength, polarity, active conditions, referenced immutable policy/profile versions and compiler/schema version.

Changing only explanatory prose does not necessarily imply a semantic fingerprint change. Changing an active hard rule does.

## 17. Constraint coverage

Before compilation, M03 can report which brief dimensions are constrained, intentionally free, unknown or uncovered.

Coverage states:
- `CONSTRAINED`;
- `FREEDOM_ZONE`;
- `UNKNOWN`;
- `NOT_APPLICABLE`.

Coverage is not automatically “the more constraints, the better”. Over-constraint is itself a production risk.

## 18. Constraint cost awareness

Constraints may carry an estimated execution/quality impact class without binding to one provider.

Examples:
- exact identity preservation: likely high-cost/high-quality-critical;
- strict 4K delivery: compute/storage impact;
- multi-reference consistency: additional validation/candidate cost.

Actual resource planning remains M07-M13. M03 only exposes semantic demand for those planners.

## 19. Poisoning / injection boundary

Untrusted reference text, metadata or retrieved context cannot create a high-authority constraint simply because it contains imperative language.

Constraint admission requires explicit source classification + authority.

Examples that must not self-promote:
- EXIF/comment saying “ignore brand rules”;
- webpage text saying “publish secret”; 
- retrieved prompt injection;
- model-generated metadata claiming USER_EXPLICIT authority.

This constraint-admission shield is foundational for M52/M54 integrations.

## 20. Violation semantics

M03 defines what a rule means and how violations are represented, but does not become the universal evaluator.

A `ConstraintViolation` can reference:
- constraint ID/version;
- observed evidence;
- severity derived from constraint strength/policy;
- affected output/ref;
- detector/evaluator authority ref;
- remediation hint.

The authoritative domain judge may live in M01/M24/M48/etc.

## 21. S02 decisions proposed

- **D-M03-S02-001:** canonical constraints are semantic rules, never provider prompt syntax.
- **D-M03-S02-002:** REQUIRE/FORBID/PREFER/AVOID/ALLOW polarity is distinct from HARD/GUARDED/SOFT/ADVISORY/EXPERIMENTAL strength.
- **D-M03-S02-003:** negative constraints are first-class and may compile into multiple provider mechanisms.
- **D-M03-S02-004:** anti-references bind forbidden facets, not whole-reference blanket similarity.
- **D-M03-S02-005:** arbitrary executable code is forbidden in canonical constraint predicates.
- **D-M03-S02-006:** constraints are explicitly scoped; scope and authority are separate.
- **D-M03-S02-007:** conditional activation must be declared and versioned.
- **D-M03-S02-008:** tolerance requires typed units/metric semantics.
- **D-M03-S02-009:** cross-modal constraints are semantic links; domain evidence stays with domain modules.
- **D-M03-S02-010:** reusable constraint bundles are immutable/versioned when referenced by a brief revision.
- **D-M03-S02-011:** canonical normalization must preserve meaning and source representation.
- **D-M03-S02-012:** downstream consumers use Minimum Sufficient Constraint Slices.
- **D-M03-S02-013:** over-constraint and under-constraint are both diagnosable states.
- **D-M03-S02-014:** untrusted/retrieved text cannot self-promote into authoritative constraints.
- **D-M03-S02-015:** M03 violation records do not replace M01/M24/M48 evaluator authority.
- **D-M03-S02-016:** S05 owns conflict/override precedence; S02 supplies normalized rules and conflict candidates only.

## 22. S02 proof plan

Future implementation/tests must prove at least:
1. a FORBID rule survives provider-neutral serialization without becoming prompt text;
2. polarity and strength cannot be conflated;
3. HARD violation fails admission unless later S05 policy provides an authorized override path;
4. SOFT/ADVISORY rules remain non-blocking by default;
5. anti-reference can prohibit selected facets without banning unrelated facets;
6. unknown mandatory predicate type fails closed;
7. unit/range normalization is deterministic;
8. conditional constraints activate only from declared condition state;
9. inactive constraints do not contaminate consumer slices/fingerprints;
10. bundle revisions are immutable and pinned;
11. narrower scope does not forge higher authority;
12. untrusted metadata cannot claim USER_EXPLICIT/PROJECT_POLICY authority;
13. cross-modal constraint round-trip preserves all target refs;
14. constraint fingerprint changes on semantic rule change;
15. wording/rationale-only change can remain semantically equivalent under a versioned normalization profile;
16. over-constraint coverage can be detected separately from unknown/under-specified areas;
17. M01 quality authority is not imported/reimplemented;
18. M02 can consume constraint refs/fingerprints without importing constraint internals.



---

# S03 — Fidelity Contract compilation

Status: `S03_PROPOSED_COMPLETE_PENDING_DISCUSSION`

## 1. Compilation doctrine

M03 compiles an admitted Creative Brief revision plus its active Constraint Set into a **Fidelity Contract Compilation** that targets the already-frozen M01 quality contract.

The compiler does not create a second quality model. It performs a typed, explainable translation from “what the production intends” into “what M01 must require evidence for”.

The authority split is strict:
- M03 decides how admitted intent/constraints map into a requested quality contract specification;
- M01 owns the legal `FidelityContract` schema, QualityClass ladder, dimension registry, promotion rules, defect semantics, evaluator authority, uncertainty and final QualityDecision;
- domain modules/profiles own domain-specific quality dimensions/evaluators when they are admitted through M01 extension contracts;
- M03 may not manufacture evaluator capability or bypass M01 registry resolution.

## 2. Compilation input

A compilation binds immutable references to:
- M03 `brief_revision_id`;
- semantic intent fingerprint;
- active constraint fingerprint;
- requested deliverable/destination profile refs;
- applicable project/brand/persona/policy refs;
- selected M01 `DomainProfile` reference/version;
- M01 contract/schema version;
- M01 dimension-registry reference/digest;
- compiler component version;
- optional previously approved contract lineage when recompiling.

Raw prose is evidence/source material, not the canonical compilation input after normalization.

## 3. Compilation output layers

S03 separates three artifacts.

### 3.1 Quality Intent Projection
A provider-neutral statement of which admitted intent/constraints create quality obligations.

Examples:
- “persistent spokesperson must remain the same person” -> identity-fidelity obligation + protected identity reference;
- “logo must remain readable as a favicon” -> silhouette/readability + technical/platform fitness obligations;
- “final cinematic master” -> requested output class + applicable visual/temporal dimensions supplied by an admitted domain profile;
- “voice must remain the corporate voice” -> admitted voice-identity extension dimension when available.

It is traceable back to exact M03 statements/constraints.

### 3.2 Fidelity Contract Spec
A compiler-owned intermediate specification containing only values M03 is authorized to request/bind.

Minimum fields:
- `compilation_id`;
- source brief/constraint refs + fingerprints;
- target M01 contract version;
- selected domain profile ref;
- requested `QualityClass`;
- contract intent summary;
- approved reference IDs;
- target platform/camera/delivery profile refs where applicable;
- applicable Semantic Zone requests/references;
- requested human-review obligations by semantic reason;
- policy references for debt/defect handling, without redefining M01 semantics;
- rationale map from each requested obligation to source intent/constraint IDs;
- unresolved compilation gaps;
- compiler version/fingerprint.

The Spec is not itself a M01 `FidelityContract` and cannot be sent to `DecisionEngine`.

### 3.3 M01 FidelityContract
The final instantiated object accepted by M01 schema/registries.

It must be constructed only through an admitted M01/domain profile path or other future M01-approved extension path.

M03 compilation is successful only if the resulting M01 contract validates under the targeted M01 contract version and dimension/evaluator/profile registries.

## 4. Exact M01 surface targeted by S03

Current `m01-contract-v1.0` / implementation surface includes:
- `contract_id`;
- `intent`;
- `output_class`;
- `dimension_ids`;
- `reference_ids`;
- fatal/major/minor/observation defect classes;
- `evaluator_set`;
- `target_platform`;
- `camera_profile`;
- `delivery_profile`;
- `SemanticZone` entries;
- contiguous `PromotionRule` ladder;
- `human_review_dimension_ids`;
- `DimensionRegistry`;
- `QualityDebtPolicy`;
- `max_judge_disagreement`;
- versioned contract identity.

S03 explicitly acknowledges this surface so later implementation cannot invent fields that M01 does not own.

## 5. QualityClass compilation

M03 may request only M01 classes:
- `DRAFT`;
- `PREVIEW`;
- `REVIEW`;
- `MASTER`;
- `ARCHIVAL_MASTER`.

Rules:
1. human adjectives such as “amazing”, “premium”, “cinematic” or “ultra quality” do not directly map to a QualityClass;
2. output class comes from explicit user/project/delivery policy or an approved domain-profile rule;
3. a final production master must never be silently downgraded because of hardware/provider limits;
4. runtime constraints may change execution strategy, not the requested quality class;
5. if the requested class cannot be legally instantiated/proven, compilation reports a blocking capability/contract gap rather than lowering the target.

This preserves ADR-0008 and the non-MVP quality doctrine.

## 6. Dimension compilation

M03 does not invent dimension identifiers.

A requested semantic quality obligation is mapped only to:
- a dimension admitted by the selected M01 `DimensionRegistry` / DomainProfile; or
- a declared unresolved requirement that blocks final compilation until an authorized future module registers the needed extension dimension.

Example:
- voice identity can compile only if an admitted dimension such as `voice-identity` exists in the bound registry/profile.

Unknown dimensions fail closed. They never become free-form strings in a production M01 contract.

## 7. Domain profile selection

Domain profile selection is capability admission, not a nearest-text guess.

Selection inputs may include:
- deliverable family;
- semantic type;
- required dimensions;
- destination profile;
- identity/brand requirements;
- admitted profile registry metadata.

The selected profile must cover every mandatory quality obligation or compilation remains incomplete.

A composite production may require multiple Fidelity Contracts for different governed subjects/artifacts rather than one giant contract pretending to judge everything.

## 8. Evaluator authority firewall

M03 cannot infer evaluator authority from a model name, prompt, result payload or recommendation text.

The final contract's `evaluator_set` must come from an admitted M01/domain profile or another M01-authorized capability mechanism. M01's `EvaluatorRegistry.resolve()` remains the promotion-capable authority boundary.

If no registered evaluator covers a required dimension:
- compilation may describe the missing capability;
- execution/promotion for that contract is blocked;
- M03 must not remove the dimension, weaken the requirement or invent an evaluator to make the contract pass.

## 9. Promotion-rule integrity

M03 cannot create an arbitrary shorter quality ladder.

Current M01 requires contiguous PromotionRules up to the requested output class.

Therefore S03 must preserve:
- ascending contiguous rung order;
- required dimensions per rung;
- hard-gate dimensions subset of required dimensions;
- evidence count/confidence requirements;
- explicit human-review requirements.

Profile-owned promotion rules are preferred. Any future customization path requires an M01 contract amendment/authorized profile mechanism, not M03-side schema mutation.

## 10. Intent-to-dimension traceability

Every compiled dimension obligation carries a rationale link to one or more:
- Intent Statement IDs;
- Constraint IDs;
- domain/profile policy refs;
- destination/profile refs.

This forms a `Quality Obligation Trace`:

`source intent/constraint -> quality obligation -> M01 dimension/profile/rule -> evidence/judge requirement`

Users and agents must be able to ask “why are we judging this?” and receive a deterministic explanation.

## 11. References compilation

M03 compiles only admitted, typed references into M01 `reference_ids` or future profile-specific references.

Reference roles include:
- identity anchor;
- must-match artifact;
- approved brand reference;
- structural target;
- quality baseline;
- anti-reference evidence reference when an evaluator/profile supports it.

A general inspiration image is not automatically a strict fidelity reference.

## 12. Semantic Zone compilation

M03 may request quality emphasis/protection over semantic zones only when the selected domain/profile can bind those zones legally to M01 dimensions.

Examples:
- eyes/face for persistent human identity;
- hands/weapon grip for a game character;
- logo clear-space/silhouette region;
- product label area.

S03 does not define pixel masks or 3D selections. M04/domain modules later materialize semantic zone geometry.

A zone may increase confidence/severity requirements through the M01 contract, but M03 cannot dilute a profile's stricter requirement.

## 13. Defect-class compilation

Defect classes and severities in a final FidelityContract are profile/policy-owned M01 semantics.

M03 can project intent into requested protections and explain why a defect family matters, but it cannot casually relabel a profile-declared FATAL/MAJOR defect as MINOR.

When user/project policy adds a stricter rule, the compilation records the requested strictness and requires a legal M01 profile/policy representation.

Weakening an admitted severity requires an authorized versioned policy change, never a prompt-level override.

## 14. Human-review compilation

Human review requests can arise from:
- explicit user policy;
- domain profile requirements;
- sensitive identity/brand/public-release constraints;
- M01 promotion rules;
- unresolved uncertainty requiring a human boundary.

M03 may compile the requirement, but M01 owns how a `HUMAN_DECISION` evidence obligation blocks promotion.

M03 never fabricates human approval evidence.

## 15. Quality Debt boundary

M03 does not decide which defects are “acceptable enough” after evaluation.

It may bind an approved `QualityDebtPolicy` reference or request a project policy profile, but M01 remains the decision authority.

FATAL/hard-gate behavior cannot be bypassed by a creative brief or ordinary override.

## 16. Confidence and disagreement

M03 may request policy/profile settings that ultimately bind M01 confidence/human-review behavior, but does not compute judge confidence or jury disagreement.

Current M01 `max_judge_disagreement` and zone confidence floors remain M01 semantics.

The compilation must record the exact profile/policy source for any non-default setting.

## 17. Contract gap model

S03 introduces `Fidelity Compilation Gap` types:
- `MISSING_DOMAIN_PROFILE`;
- `MISSING_DIMENSION`;
- `MISSING_EVALUATOR_CAPABILITY`;
- `UNRESOLVED_REFERENCE`;
- `UNSUPPORTED_QUALITY_CLASS`;
- `UNREPRESENTABLE_CONSTRAINT`;
- `PROFILE_POLICY_CONFLICT`;
- `REGISTRY_VERSION_MISMATCH`;
- `BLOCKING_AMBIGUITY`;
- `STALE_COMPILATION_INPUT`.

A blocking gap prevents production-grade contract emission.

No gap is repaired by silently dropping the originating requirement.

## 18. Compilation completeness

A compilation is `COMPLETE` only when:
- source brief/constraint revisions are immutable/current;
- no BLOCKING ambiguity remains;
- selected profile is version-pinned and admitted;
- every mandatory quality obligation maps to admitted dimensions/rules;
- evaluator capability is resolvable by M01 registry boundary;
- every strict reference is resolved;
- requested QualityClass can be legally represented;
- generated M01 FidelityContract validates round-trip;
- rationale coverage is complete for every compiled obligation.

Otherwise status is `INCOMPLETE` or `BLOCKED`, never a partial contract mislabeled ready.

## 19. Compilation fingerprint

Each compilation gets a `fidelity_compilation_fingerprint` over correctness-relevant inputs:
- source brief/constraint fingerprints;
- selected domain profile/version;
- target M01 contract version;
- dimension registry identity/version;
- destination/profile refs;
- policy refs;
- compiler version;
- emitted contract payload digest when complete.

This makes stale contracts detectable and enables M02 reuse/invalidation.

## 20. Recompilation / minimal invalidation

A brief edit does not automatically invalidate every quality obligation.

Using S01/S02 semantic deltas, S03 computes which Fidelity Contract fields are affected.

Examples:
- copy change may leave geometry/identity dimensions unchanged;
- output destination change may alter target-platform/delivery requirements;
- identity-anchor change invalidates identity references and related zones;
- requested final-class change alters promotion obligations;
- purely explanatory text change may not require a new semantic contract payload even though brief revision history advances.

M02 remains the authority for graph impact/rebuild decisions. S03 supplies a typed Quality Contract Delta.

## 21. Quality Contract Delta

S03 produces a semantic delta classification such as:
- `NO_SEMANTIC_CHANGE`;
- `REFERENCE_CHANGE`;
- `DIMENSION_OBLIGATION_CHANGE`;
- `QUALITY_CLASS_CHANGE`;
- `ZONE_CHANGE`;
- `DELIVERY_PROFILE_CHANGE`;
- `POLICY_CHANGE`;
- `PROFILE_CHANGE`;
- `REGISTRY_CHANGE`.

The delta includes explanation paths back to source changes.

## 22. Multi-contract productions

One Creative Brief may compile into multiple subject-specific Fidelity Contracts.

Example film/commercial production:
- persistent spokesperson identity contract;
- individual shot visual/master contract;
- voice/dialogue contract;
- music/audio contract;
- final delivery/package contract.

M03 maintains a `Fidelity Contract Set` linking them to one brief revision without merging incompatible dimension/evaluator domains into one mega-contract.

## 23. Contract inheritance / overlays

Reusable quality policy may be layered from:
- IRIS project defaults;
- domain profile;
- brand/persona/product profile;
- production-specific strict additions;
- destination requirements.

Compilation must produce one explicit resolved result plus a provenance trace.

Hidden runtime inheritance is forbidden.

Overlays may strengthen within legal profile/policy mechanisms. They cannot weaken immutable/higher-authority requirements without an authorized S05 override that is itself legally representable by M01.

## 24. No hardware-driven quality collapse

8 GB VRAM and other resource constraints are first-class execution realities, but they do not rewrite the Fidelity Contract.

If local hardware cannot produce the requested MASTER quality in one pass, later planners may use tiling, staged rendering, offload, remote spillover, alternative models or more time.

S03 emits the target quality truthfully; M07-M13 solve execution feasibility.

## 25. Explainability packet

Each complete compilation emits compact evidence answering:
- why this QualityClass?
- why each dimension?
- why each strict reference?
- why human review?
- which profile/registry/evaluator capabilities are expected?
- what could not be represented?
- what changed from the previous contract?

This packet is referenceable rather than repeatedly injecting the full brief into downstream LLM context.

## 26. S03 decisions proposed

- **D-M03-S03-001:** M03 compiles to the frozen M01 FidelityContract contract; it does not create a parallel quality system.
- **D-M03-S03-002:** compilation uses a separate Fidelity Contract Spec intermediate that has no M01 decision authority.
- **D-M03-S03-003:** requested QualityClass comes from explicit/admitted policy, never adjective heuristics or hardware limitations.
- **D-M03-S03-004:** M03 cannot invent dimension IDs; mandatory unmapped quality intent becomes a blocking compilation gap.
- **D-M03-S03-005:** domain profile selection is admitted capability matching, not nearest-text guessing.
- **D-M03-S03-006:** evaluator_set is supplied only through M01-authorized profile/registry mechanisms; M03 never grants evaluator capability.
- **D-M03-S03-007:** M01 promotion-rule contiguity/hard-gate/human-review invariants are preserved exactly.
- **D-M03-S03-008:** every compiled quality obligation is traceable to source intent/constraint/policy.
- **D-M03-S03-009:** inspiration references are not silently promoted to strict fidelity references.
- **D-M03-S03-010:** M03 may request Semantic Zones but domain modules materialize their geometry/regions.
- **D-M03-S03-011:** M03 cannot weaken profile-owned defect severity or bypass FATAL/hard gates with ordinary overrides/debt.
- **D-M03-S03-012:** human-review requirement may be compiled, but only M01-recognized HUMAN_DECISION evidence can satisfy M01.
- **D-M03-S03-013:** incomplete capability/schema/profile coverage blocks contract emission rather than dropping requirements.
- **D-M03-S03-014:** compiled contracts carry versioned fingerprints and stale-input detection.
- **D-M03-S03-015:** semantic brief deltas compile into typed Quality Contract Deltas for M02 impact analysis.
- **D-M03-S03-016:** one brief may produce a Fidelity Contract Set of subject-specific contracts rather than an unsafe mega-contract.
- **D-M03-S03-017:** quality-policy layering must resolve to one explicit payload with provenance; no hidden inheritance.
- **D-M03-S03-018:** hardware/resource constraints cannot silently downgrade requested final quality.
- **D-M03-S03-019:** explainability is emitted as a compact referenceable compilation packet for token-efficient downstream work.
- **D-M03-S03-020:** successful compilation requires M01 schema/registry validation and deterministic round-trip of the emitted contract.

## 27. S03 proof plan

Future implementation/tests must prove at least:
1. a valid admitted profile compiles to an actual `FidelityContract` accepted by current M01 serialization/validation;
2. emitted contract round-trips deterministically;
3. “premium/cinematic/high quality” text alone cannot choose MASTER/ARCHIVAL_MASTER;
4. explicit/admitted MASTER policy compiles to MASTER without hardware-based downgrade;
5. unknown dimension request produces MISSING_DIMENSION, not a free-form M01 dimension;
6. missing evaluator capability blocks completion;
7. M03 cannot append an evaluator that M01 registry/profile did not admit;
8. promotion rules remain contiguous through requested class;
9. strict profile defect severity cannot be weakened by a brief constraint;
10. user inspiration reference is not strict unless its role says so;
11. unresolved strict reference blocks completion;
12. Semantic Zone request must bind only admitted contract dimensions;
13. human-review request produces an M01-compatible obligation but no fabricated decision evidence;
14. blocking ambiguity prevents complete contract emission;
15. compilation fingerprint changes when profile/registry/policy/source semantics change;
16. stale source revision is detectable;
17. unrelated wording change can yield NO_SEMANTIC_CHANGE in Quality Contract Delta;
18. destination change selectively changes delivery/platform obligations;
19. one multimodal brief can legally produce multiple distinct contracts without cross-domain evaluator contamination;
20. every emitted dimension/rule/reference has an explanation path to source or selected profile;
21. provider/model/DCC names are unnecessary to compile the quality contract;
22. M01 `DecisionEngine`, `EvaluatorRegistry` and defect/debt authority are not reimplemented in M03.

---

## M03 current disposition

S01, S02 and S03 are proposed complete for discussion.

No M03 implementation is authorized.

Next legal planning action after S03 review/acceptance: **S04 — Provider-neutral execution intent and explainability**.
