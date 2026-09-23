# M05 — Asset DNA 2.0 & Cross-Modal Identity

Status: `S01_COMPLETE_FOR_MODULE_PLANNING`
Module: `M05`
Area: `A — Product Constitution & Production OS`
Planning issue: `#37`
Authorized baseline: `6f2311b59f5da91778d3fc9d9fe1572953a0c60b`

## Mission

M05 defines IRIS's persistent semantic identity layer for reusable assets, characters, creatures, products, environments, scenes and future persona-bearing objects.

Asset DNA is not a file format and not a model embedding. It is the governed semantic identity contract that states which traits make a subject remain the same subject across revisions, modalities, renderers, providers and production contexts, which traits may vary, which changes require explicit authority, and which observations are merely evidence rather than canonical truth.

M05 must let IRIS answer:
- what makes this asset the same asset across image, 3D, video, motion, audio or narrative projections;
- which traits are identity-critical, mutable, contextual or derived;
- which identity anchors are canonical versus observed;
- when a change is an authorized mutation versus identity drift;
- how later domain modules can project DNA without taking ownership of the canonical DNA.

## Ownership boundary

### M05 owns
- persistent Asset/Persona DNA semantic identity;
- canonical DNA revisions and trait namespace;
- cross-modal identity anchors and projection contracts;
- identity-critical versus mutable trait policy;
- mutation authorization boundaries;
- drift semantics/evidence contracts;
- DNA compatibility/equivalence semantics;
- reusable DNA package contract and identity-level branching semantics, without replacing M02 project history.

### M05 does not own
- M01 quality scoring, acceptance, promotion or QualityDebt;
- M02 project/build/branch/release topology;
- M03 creative intent and constraints;
- M04 provider-neutral scene/media representation;
- M06 persistence, CAS, database or content-addressed storage;
- M16 provider/workflow compilation;
- M39 digital-human generation/acting/appearance runtime;
- M40 voice production/cloning;
- M41 music production;
- M43 story/canon authority;
- M46 Brand & IP Studio authority;
- M53 provenance/rights decision authority;
- M54 security/privacy enforcement runtime.

### Inter-module law

M04 describes **what is represented now**.
M05 states **which semantic identity must persist across representations and authorized mutations**.
M02 states **which project/build/branch event produced or owns a revision**.
M06 later states **where immutable content/revisions are persisted**.
M39/M40/M41/M46 and other domain modules consume/project DNA but do not silently rewrite M05 canonical identity.

---

# S01 — Asset DNA schema and identity invariants

## 1. S01 goals

S01 must make these statements true:

1. one persistent subject identity survives file/path/provider/modality changes;
2. canonical identity does not collapse into a content hash, display name, prompt, embedding or provider-specific ID;
3. DNA revisions are immutable and never rewritten in place;
4. canonical traits are explicitly classified by mutability and identity criticality;
5. observations, embeddings and generated outputs cannot self-promote into canonical DNA;
6. cross-modal anchors can point from M04 representations into one M05 identity without M05 owning the representation payload;
7. unauthorized mutation of protected identity traits fails closed;
8. absence, unknown, not-applicable and intentionally-unconstrained states remain distinct;
9. every canonical DNA fact has provenance/policy reachability;
10. downstream modules can request a minimum sufficient DNA slice instead of the whole subject history.

## 2. Core identity model

### AssetDNAIdentity

Stable semantic identity for one persistent subject.

Proposed fields:
- `dna_id` — opaque stable identity, never inferred from name/path/content;
- `subject_class` — domain-neutral semantic class;
- `namespace`;
- `root_revision_ref`;
- `current_admitted_revision_ref` as an authority-controlled reference, not mutable history inside the DNA record;
- `external_identity_refs` for mapped external systems;
- `policy_refs`;
- `provenance_refs`;
- `rights_privacy_refs`;
- `contract_version`.

Identifier generation may use a standard UUID/opaque identifier strategy, but UUID format is an implementation detail rather than semantic identity truth.

### DNARevision

Every admitted DNA state is immutable.

A revision binds:
- `dna_id`;
- unique revision identity;
- parent revision ref(s) as semantic lineage evidence only;
- schema family/version;
- canonical trait set;
- anchor set;
- mutation authorization refs;
- compatibility/equivalence declarations;
- provenance/evidence refs;
- deterministic canonical fingerprint.

M02 remains owner of project branch/history topology. M05 lineage cannot become a parallel VCS.

## 3. Canonical trait model

### DNATrait

A trait is a typed semantic identity fact.

Required metadata:
- stable trait path;
- schema family/version;
- typed value or typed reference;
- identity criticality;
- mutability class;
- applicability state;
- provenance/policy refs;
- optional tolerance/equivalence rule ref;
- optional cross-modal projection rules.

### Identity criticality

Initial S01 classes:
- `IDENTITY_DEFINING` — unauthorized change means identity break or blocked mutation;
- `IDENTITY_SIGNIFICANT` — bounded authorized change permitted;
- `CONSISTENCY_RELEVANT` — should remain coherent but is not alone identity-defining;
- `CONTEXTUAL` — expected to vary by production context;
- `DERIVED_EVIDENCE_ONLY` — never canonical identity truth.

Criticality is not M01 quality class.

### Mutability

Initial classes:
- `IMMUTABLE`;
- `MUTABLE_WITH_EXPLICIT_POLICY`;
- `MUTABLE_WITHIN_BOUNDS`;
- `CONTEXTUAL_VARIANT`;
- `DERIVED_ONLY`.

A trait cannot become more mutable merely because a downstream provider cannot reproduce it.

## 4. Four-state applicability semantics

M05 forbids overloading null/empty values.

Every optional trait uses an explicit state:
- `PRESENT`;
- `UNKNOWN`;
- `NOT_APPLICABLE`;
- `INTENTIONALLY_UNCONSTRAINED`.

These states are semantically different and affect compatibility, mutation and drift reasoning.

## 5. Canonical versus evidence partition

M05 has a hard two-plane model.

### Canonical DNA plane
Contains admitted identity truth:
- canonical traits;
- identity anchors;
- mutation policy;
- compatibility declarations;
- explicit aliases/external mappings;
- canonical revision fingerprint.

### Evidence plane
May contain:
- perceptual fingerprints;
- embeddings;
- similarity observations;
- generated-reference measurements;
- provider/DCC observations;
- content hashes;
- thumbnails/previews;
- quality/evaluation outputs;
- external metadata.

Evidence can support a proposal but cannot modify canonical DNA without an admitted authority path.

## 6. Identity anchors

### IdentityAnchor

A typed stable semantic handle connecting DNA to representations or external identity evidence.

Anchor classes proposed:
- `SEMANTIC_ANCHOR` — stable M05 semantic anchor;
- `M04_REPRESENTATION_ANCHOR` — points to a provider-neutral M04 application point;
- `EXTERNAL_IDENTITY_ANCHOR` — mapped external asset/persona system;
- `PROVENANCE_ANCHOR` — links signed/provenance evidence;
- `OBSERVATION_ANCHOR` — evidence only.

An anchor contains:
- anchor ID;
- owning DNA ID;
- anchor class;
- typed target ref;
- schema/version;
- provenance;
- authority classification;
- optional validity scope.

Observation anchors can never be authoritative merely because their confidence/similarity is high.

## 7. Cross-modal identity contract

S01 introduces `DNAProjectionContract`.

A projection contract says how canonical DNA may be referenced by a modality without copying ownership.

Examples:
- M04 CharacterIR binds to one DNA anchor;
- later M39 digital-human representation consumes persona/character DNA;
- M40 voice runtime consumes VoiceDNA links admitted in S03;
- M46 Brand & IP Studio consumes BrandDNA links admitted in S03.

Projection requirements:
- source DNA revision is explicit;
- consumed trait paths are explicit;
- required versus optional traits are explicit;
- unsupported mandatory identity traits become gaps/blocks, never silent drops;
- projection result cannot self-certify canonical equivalence.

## 8. Names, paths, hashes and embeddings are not identity

S01 freezes these negative rules:

- display name is metadata, not identity;
- file/path/URL/storage location is not identity;
- content digest identifies bytes/representation, not necessarily persistent subject identity;
- provider/model/workflow ID is not identity;
- prompt text is not identity;
- perceptual hash is evidence, not identity;
- embedding/vector is evidence, not identity;
- face/voice similarity score is evidence, not identity;
- M04 node ID is a representation identity, not automatically the M05 persistent subject identity.

Explicit binding is required between representation identity and DNA identity.

## 9. Trait namespace and extension model

M05 core uses a small domain-neutral trait substrate plus versioned namespaces.

Core namespaces proposed:
- `identity.*`;
- `structure.*`;
- `appearance.*`;
- `behavior.*`;
- `relationship.*`;
- `provenance.*`;
- `policy.*`.

S02/S03 may add typed domain families.

Unknown mandatory trait schemas fail closed.
Unknown optional trait families may remain opaque only under explicit preservation policy.

No arbitrary executable validator or mutation rule is embedded as canonical DNA.

## 10. Mutation boundary

A `DNAMutationProposal` is not automatically a new canonical revision.

It must name:
- source revision;
- proposed trait changes;
- mutation reason;
- authority/policy refs;
- affected identity-critical traits;
- expected compatibility impact;
- evidence refs;
- declared loss/tolerance if any.

S04 will freeze drift detection and mutation admission semantics. S01 freezes only the rule that protected traits cannot mutate implicitly.

## 11. Identity collision and aliasing

Two identities must not merge because they look similar.

M05 supports:
- `IdentityAlias` for explicit human/governance-controlled aliases;
- `IdentityEquivalenceClaim` for proposed equivalence;
- collision findings when two DNA IDs appear to refer to one subject;
- split findings when one DNA ID appears to contain incompatible identity-defining traits.

Equivalence is a governed claim, not a similarity threshold.

## 12. Canonical DNA fingerprint

`DNAFingerprint` is a deterministic digest over canonical identity material only.

It excludes:
- display metadata;
- storage location;
- provider IDs;
- caches;
- noncanonical observations;
- similarity scores;
- timestamps that do not alter semantic identity;
- derived previews.

The fingerprint can detect semantic changes but is not itself the subject identity.

## 13. Minimum sufficient DNA context

M05 introduces `MinimumSufficientDNASlice`.

A slice contains only:
- requested trait paths;
- dependency/constraint closure;
- required anchors;
- mutation/compatibility rules needed to interpret those traits;
- relevant provenance/policy refs;
- source revision fingerprint.

This is designed for HIVE/agents/downstream modules without replaying all DNA history.

## 14. Provenance, rights and privacy boundary

M05 carries references and minimization rules, but does not become M53/M54.

Requirements:
- sensitive identity evidence is not copied into canonical DNA merely for convenience;
- rights/consent/privacy refs can gate use of identity anchors;
- external provenance evidence can support identity continuity;
- signed provenance proves association/tamper resistance, not semantic identity by itself;
- personal identity authentication/biometric verification is not required for generic Asset DNA.

## 15. External prior-art disposition for S01

S01 uses external standards as references only:

- RFC 9562 UUIDs: opaque globally unique identifier reference; does not define M05 semantic identity.
- OpenUSD `assetInfo`: asset identifier/name/version metadata and composition-surviving asset management reference.
- VRM 1.0: avatar/humanoid/meta interoperability reference for later character/persona DNA, not canonical M05 schema.
- C2PA: provenance/content-binding reference; verifiable provenance is evidence, not M05 semantic identity authority.

No external standard becomes a mandatory M05 runtime dependency in S01.

## 16. S01 candidate hard invariants

1. `dna_id` is stable and opaque; display metadata never defines it.
2. file/path/URL/storage location never defines persistent identity.
3. content digest identifies representation/content, not automatically subject identity.
4. provider/model/workflow IDs never define canonical M05 identity.
5. prompts and generated output IDs never define canonical identity.
6. embeddings/perceptual hashes/similarity scores are evidence only.
7. DNA revisions are immutable.
8. M02 remains branch/project/history authority.
9. M06 remains persistence/CAS/storage authority.
10. M04 remains provider-neutral representation authority.
11. canonical traits declare schema family/version.
12. canonical traits declare identity criticality.
13. canonical traits declare mutability class.
14. PRESENT/UNKNOWN/NOT_APPLICABLE/INTENTIONALLY_UNCONSTRAINED are distinct states.
15. identity-defining immutable traits cannot change without identity break or explicit governed rule.
16. downstream scarcity/provider limitation cannot weaken a trait's criticality/mutability.
17. observed/generated/provider data cannot self-promote into canonical DNA.
18. every canonical fact has provenance/policy reachability.
19. unknown mandatory trait schema fails closed.
20. opaque optional traits require explicit preservation policy.
21. representation anchors require explicit DNA binding.
22. M04 identity and M05 identity are not implicitly equivalent.
23. aliases never merge identities implicitly.
24. equivalence is a governed claim, not a similarity threshold.
25. canonical fingerprint excludes evidence/cache/location noise.
26. fingerprint change does not itself authorize mutation.
27. DNA projection declares consumed required/optional traits.
28. unsupported mandatory projected identity traits cannot disappear silently.
29. rights/privacy/provenance evidence is referenced with minimization; M05 does not seize M53/M54 authority.
30. HIVE/agents may retrieve/propose identity context but cannot mutate canonical DNA directly.

These are S01 planning invariants and may be consolidated or expanded by S02-S05 before final contract freeze.

---

# S02 — Character, creature, object, product and environment DNA

Status: `COMPLETE_FOR_MODULE_PLANNING`

## 1. S02 goals

S02 specializes the S01 identity substrate without creating separate incompatible identity engines.

The same `AssetDNAIdentity`, `DNARevision`, trait law, anchor law and evidence firewall remain canonical.

S02 adds:
- family profiles;
- semantic identity levels;
- persistent component identity;
- trait bundles;
- family-specific namespaces;
- variant/archetype semantics;
- persistent-vs-contextual appearance partitions.

## 2. Semantic identity levels

M05 distinguishes:
- `CLASS` — broad semantic category;
- `ARCHETYPE` — reusable species/model/design pattern;
- `INDIVIDUAL` — one persistent subject;
- `VARIANT` — governed derivative identity/configuration.

Similarity cannot promote or collapse these levels.

## 3. DNAFamilyProfile

A `DNAFamilyProfile` declares:
- family ID/version;
- supported semantic levels;
- required/optional namespaces;
- allowed component roles;
- default criticality/mutability guidance;
- extension namespaces;
- projection obligations;
- compatibility rules.

Defaults never silently override explicit trait policy.

## 4. DNATraitBundle

A `DNATraitBundle` groups versioned typed traits under one family/profile.

It carries:
- bundle ID;
- subject DNA ref;
- family/profile ref;
- trait path set;
- required/optional declarations;
- provenance/policy refs;
- compatibility refs.

Bundles are composition units, not new identities.

## 5. DNAComponentIdentity

Persistent subcomponents may receive DNA-scoped identity when their continuity matters.

Component identity:
- is stable under ordering/index changes;
- is not derived from display name;
- is not automatically an M04 node ID;
- may bind to M04 representation anchors;
- supports governed replacement/split/merge;
- excludes derived LOD/proxy fragments by default.

## 6. CharacterDNA profile

Candidate namespaces:
- `character.identity.*`;
- `character.anatomy.*`;
- `character.face.*`;
- `character.body.*`;
- `character.hair.*`;
- `character.signature.*`;
- `character.costume_binding.*`;
- `character.relationship_role.*`.

Persistent candidates:
- defining face/body morphology where policy requires it;
- stable marks/scars/signatures;
- component identities;
- identity-bearing proportions;
- explicit archetype/species refs.

Contextual candidates:
- pose;
- expression;
- camera/light;
- temporary clothing/props;
- dirt/wetness/damage state;
- temporary styling permitted by policy.

M39 owns digital-human production/acting continuity.
M29/M30 own rigging/motion production.
M40 owns voice production.
M43 owns canon/story truth.

## 7. CreatureDNA profile

Candidate namespaces:
- `creature.taxonomy.*`;
- `creature.morphology.*`;
- `creature.anatomy.*`;
- `creature.appendage.*`;
- `creature.surface.*`;
- `creature.pattern.*`;
- `creature.signature.*`.

Creature DNA must support:
- non-humanoid anatomy;
- variable component counts;
- bilateral and asymmetric forms;
- procedural/species archetypes;
- individual signatures.

Species/archetype identity never implies individual identity.

## 8. ObjectDNA profile

Candidate namespaces:
- `object.form.*`;
- `object.part.*`;
- `object.function.*`;
- `object.articulation.*`;
- `object.surface_identity.*`;
- `object.signature.*`.

Persistent identity may include stable form, component topology, articulation structure, unique marks and function-critical geometry.

Scene placement, open/closed state, transform and transient wear remain contextual unless explicitly admitted otherwise.

## 9. ProductDNA profile

Identity levels may include:
- `PRODUCT_FAMILY`;
- `MODEL`;
- `VARIANT_SKU`;
- `PACKAGE_VARIANT`;
- `PHYSICAL_INSTANCE`.

Candidate namespaces:
- `product.model.*`;
- `product.geometry.*`;
- `product.variant.*`;
- `product.packaging.*`;
- `product.marking.*`;
- `product.dimension.*`;
- `product.external_identifier.*`.

SKU/GTIN/MPN/serial values are governed external identity refs, not universal substitutes for M05 DNA identity.

M46 remains Brand & IP authority.

## 10. EnvironmentDNA profile

Candidate namespaces:
- `environment.layout.*`;
- `environment.zone.*`;
- `environment.landmark.*`;
- `environment.architecture.*`;
- `environment.signature.*`;
- `environment.ecology.*`;
- `environment.context_boundary.*`.

Persistent candidates:
- topology/layout;
- landmark set;
- stable zone relationships;
- defining architecture/ecology;
- protected spatial relationships.

Contextual candidates:
- time of day;
- weather;
- temporary props/crowds;
- lighting/camera;
- temporary damage;
- growth/seasonal state unless identity policy says otherwise.

M04 SceneIR remains representation authority.

## 11. Persistent appearance partition

S02 introduces three explicit roles:
- `PersistentAppearanceTrait`;
- `ContextualAppearanceState`;
- `AppearanceObservation`.

Lighting, renderer, camera, pose and output-model artifacts must not leak into persistent identity.

## 12. Variant and archetype relation

A governed variant relation declares:
- parent/archetype ref;
- relation role;
- inherited trait paths;
- overridden trait paths;
- compatibility expectation;
- resulting identity relationship.

Inheritance is semantic, not shared mutable storage.

## 13. Family reclassification

Changing family/profile is not an ordinary field edit.

Character ↔ Creature, Product ↔ Object or Environment ↔ generic Scene use requires an explicit migration/projection decision.

A projection can expose a generic view without changing canonical family identity.

## 14. S02 candidate hard invariants

31. family specialization must reuse the S01 identity core rather than create an independent identity engine.
32. CLASS, ARCHETYPE, INDIVIDUAL and VARIANT remain semantically distinct.
33. visual similarity cannot infer semantic identity level.
34. family-profile defaults cannot silently override explicit trait criticality/mutability.
35. trait bundles cannot become independent subject identities.
36. component index/order/name never defines component identity.
37. M04 node identity cannot silently define M05 component identity.
38. component replacement/split/merge requires explicit governed semantics.
39. derived LOD/proxy fragments do not become new persistent components by default.
40. CharacterDNA cannot treat pose/expression/camera/light as persistent identity by default.
41. CharacterDNA cannot seize M39 acting/digital-human production authority.
42. CreatureDNA cannot require human anatomy or fixed human component slots.
43. species/archetype identity cannot imply creature individual identity.
44. ObjectDNA separates persistent form/components from contextual scene state.
45. Product family/model/SKU/package/physical-instance identity levels cannot be collapsed implicitly.
46. SKU/GTIN/MPN/serial refs are external mappings, not universal DNA IDs.
47. Product variant changes declare inherited and overridden trait surfaces.
48. M46 remains Brand & IP Studio production/brand authority.
49. EnvironmentDNA cannot silently absorb M04 SceneIR representation authority.
50. weather/time/camera/lighting are contextual environment state unless explicitly identity-defining.
51. environment topology/landmark identity must be represented as typed traits/relations, not file paths.
52. persistent appearance is distinct from contextual appearance and observations.
53. renderer/provider/model differences cannot redefine persistent appearance automatically.
54. family reclassification requires explicit migration/projection semantics.
55. cross-family generic projection cannot rewrite canonical source-family identity.
56. family extensions use versioned namespaces and fail closed for unknown mandatory semantics.
57. family-specific traits preserve S01 provenance/policy reachability.
58. downstream provider scarcity cannot downgrade family-specific identity protections.
59. family/profile changes participate in deterministic canonical fingerprint/change-surface evidence.
60. HIVE/agents may propose family classification but cannot canonically reclassify DNA without authority.

These extend S01 invariants 1–30 and remain candidates until final contract freeze.

## 15. S02 proprietary candidates

S02 adds `IRIS-DNAX-031..060` to the technology registry.

## S02 STOP CONDITION

S02 is complete for module planning when:
- one common identity core is preserved;
- CLASS/ARCHETYPE/INDIVIDUAL/VARIANT is explicit;
- Character/Creature/Object/Product/Environment profiles are explicit;
- component identity and variant semantics are explicit;
- persistent/contextual/observed appearance separation is explicit;
- candidate invariants 31–60 are recorded;
- DNAX-031..060 are registered;
- planning checkpoint advances to S03;
- no M05 implementation code is introduced.

# S03 — SceneDNA, Motion DNA, Voice DNA and Brand DNA links

Status: `COMPLETE_FOR_MODULE_PLANNING`

## 1. S03 goals

S03 makes cross-modal identity explicit without duplicating domain ownership.

M05 owns identity linkage and preservation obligations.

Domain ownership:
- M30 owns MotionDNA contents and motion production;
- M40 owns VoiceDNA contents and voice production;
- M46 owns BrandDNA contents and Brand/IP production;
- M45 owns Campaign DNA / Creative Genome and advertising;
- M43 owns narrative Canon;
- M04 owns current provider-neutral representation.

## 2. LinkedDomainDNARef

A generic `LinkedDomainDNARef` binds M05 identity to a domain-owned DNA revision.

Required fields/concepts:
- owner module;
- DNA family;
- external DNA identity;
- pinned revision/version;
- link role;
- REQUIRED / OPTIONAL;
- bound M05 trait/component paths;
- preservation obligations;
- compatibility expectation;
- validity scope;
- provenance/policy/rights refs;
- freshness state.

"Latest" is not a valid canonical version selector.

## 3. SceneIdentityDNA

M05 may own a reusable persistent scene/set identity composition.

It can bind:
- environment DNA;
- member DNA identities;
- stable identity-role slots;
- continuity-critical relationships;
- permitted substitutions;
- M04 SceneIR projection refs;
- M43 Canon refs.

It cannot own:
- current SceneIR state;
- camera/light/material transforms;
- shot/editorial timeline;
- narrative/canon truth;
- M37 continuity judgment.

## 4. IdentityRoleSlot

A stable scene/composite role slot declares:
- role ID;
- semantic role;
- accepted family/profile;
- required traits;
- cardinality;
- substitution policy;
- bound DNA refs.

Role substitution may preserve scene identity only when explicitly allowed.

## 5. MotionDNALink

A `MotionDNALink` points to M30-owned MotionDNA.

M05 may bind:
- approved motion identity revision;
- motion-style/signature refs;
- relevant body/component paths;
- preservation obligations;
- allowed contextual variation.

M05 does not own animation curves, clips, mocap payloads, retargeting, rigs or current pose.

## 6. VoiceDNALink

A `VoiceDNALink` points to M40-owned VoiceDNA.

M05 may bind:
- approved voice identity revision;
- language-independent identity anchor refs;
- allowed voice roles;
- cross-language persistence obligation;
- rights/consent/privacy refs;
- allowed bounded variation.

M05 does not own TTS model weights, provider voice IDs, biometric authentication, raw speaker templates or speech generation.

## 7. BrandDNALink

A `BrandDNALink` points to M46-owned BrandDNA.

M05 may bind:
- approved brand identity/version;
- brand role;
- required/optional association;
- subject trait/component binding;
- compatibility expectation;
- policy/IP refs.

M45 Campaign DNA is a separate advertising-domain identity and must not be relabelled BrandDNA.

## 8. CrossModalIdentityBinding

Binds one M05 identity revision to multiple domain DNA refs and M04 anchors.

It declares:
- participating identities/revisions;
- bound canonical trait paths;
- mandatory/optional links;
- cross-modal consistency obligations;
- compatibility/freshness state;
- evidence requirements;
- policy/provenance refs.

No linked module can mutate M05 canonical DNA through the binding.

## 9. CrossModalIdentityObligation

A typed obligation states which identity facts must remain coherent across modalities.

Expectation classes:
- EXACT;
- BOUNDED;
- ROLE_COMPATIBLE;
- CONTEXTUAL;
- OPAQUE_REFERENCE_ONLY.

The obligation records the evaluation owner. M05 never turns this into independent quality/promotion authority.

## 10. CrossModalDNAGraph

A typed identity-link graph relates:
- M05 subject DNA;
- SceneIdentityDNA;
- external domain DNA refs;
- M04 representation anchors.

Allowed edge families include:
- HAS_MOTION_IDENTITY;
- HAS_VOICE_IDENTITY;
- BOUND_TO_BRAND;
- MEMBER_OF_SCENE_IDENTITY;
- PERFORMS_ROLE;
- REPRESENTED_BY.

This graph is not:
- M02 Production Graph;
- M04 scene/relationship graph;
- M43 Canon Graph.

## 11. Revision freshness

Every external DNA link is revision-pinned.

When an external domain DNA changes:
- existing M05 revision remains immutable;
- link becomes stale/review-required unless declared compatibility proves admissibility;
- no silent follow-latest;
- accepting a new external revision requires a new M05 DNA revision or an explicit compatibility mechanism frozen later.

## 12. Voice privacy boundary

Voice identity is not authentication.

Rules:
- raw biometric templates are not generic M05 canonical data;
- speaker similarity is evidence only;
- provider/model voice ID is not persona identity;
- rights/consent/privacy refs are carried where required;
- M40/M53/M54 retain production/rights/security authority.

## 13. Generic future domain links

The S03 link fabric must support future references such as:
- M41 ArtistDNA / MusicDNA;
- M45 CampaignDNA / Creative Genome;
- M46 IP asset/brand packs;
- future localization/content/persona DNA families.

Unknown mandatory link families fail closed.

## 14. S03 candidate hard invariants

61. M05 owns cross-modal identity linkage, not MotionDNA/VoiceDNA/BrandDNA domain contents.
62. M30 remains sole MotionDNA/motion-production authority.
63. M40 remains sole VoiceDNA/voice-production authority.
64. M46 remains sole BrandDNA/Brand & IP Studio authority.
65. M45 Campaign DNA/Creative Genome cannot be relabelled as BrandDNA.
66. M43 remains narrative Canon authority.
67. M04 SceneIR snapshot cannot silently become persistent SceneIdentityDNA.
68. SceneIdentityDNA cannot become narrative scene/canon truth.
69. SceneIdentityDNA member identity is explicit through stable role/member refs.
70. role-slot substitution requires explicit substitution policy.
71. LinkedDomainDNARef must identify owner module, family and pinned revision/version.
72. canonical external DNA links cannot use implicit "latest".
73. external domain DNA advancement cannot mutate an existing M05 revision.
74. stale required external DNA links fail closed or require explicit review policy.
75. MotionDNALink cannot canonicalize animation curves, mocap payloads, rigs or current pose.
76. one motion clip/provider ID cannot define MotionDNA identity.
77. VoiceDNALink cannot canonicalize provider voice IDs/model weights as persona identity.
78. VoiceDNA similarity/voiceprints remain evidence unless their owning policy explicitly admits a reference.
79. generic M05 identity does not require biometric authentication.
80. BrandDNALink association is explicit and versioned.
81. brand-link change is identity-breaking only when M05 trait/policy says so.
82. CrossModalIdentityBinding cannot grant linked modules canonical mutation authority over M05.
83. cross-modal obligations declare required/optional participants explicitly.
84. missing required linked DNA cannot disappear silently during projection.
85. cross-modal consistency expectation is typed, not inferred from similarity.
86. M01/evaluator owners retain quality and acceptance authority for cross-modal evidence.
87. CrossModalDNAGraph cannot duplicate M02 Production Graph ownership.
88. CrossModalDNAGraph cannot duplicate M04 scene graph or M43 Canon Graph ownership.
89. future domain DNA families use versioned owner/family refs and unknown mandatory families fail closed.
90. HIVE/agents may retrieve/propose cross-modal links but cannot admit or rewrite canonical links directly.

These extend S01-S02 invariants 1–60 and remain candidates until final contract freeze.

## 15. S03 proprietary candidates

S03 adds `IRIS-DNAX-061..090`.

## S03 STOP CONDITION

S03 is complete for module planning when:
- domain-DNA ownership firewalls are explicit;
- SceneIdentityDNA boundary is explicit;
- Motion/Voice/Brand links are revision-pinned and versioned;
- M45 CampaignDNA vs M46 BrandDNA is explicit;
- cross-modal bindings/obligations/graph are explicit;
- stale-link semantics are explicit;
- candidate invariants 61–90 are recorded;
- DNAX-061..090 are registered;
- checkpoint advances to S04;
- no M05 implementation code is introduced.

# S04 — Identity anchors, mutation boundaries and drift detection

Status: `COMPLETE_FOR_MODULE_PLANNING`

## 1. S04 goals

S04 defines how IRIS distinguishes allowed variation, representation drift, canonical mutation and identity break.

M05 owns identity-transition semantics. It does not become M01 quality authority, M37 temporal-continuity authority or M39 digital-human production authority.

## 2. IdentityAnchor authority classes

Anchors are explicitly classified:
- `CANONICAL`;
- `BOUND_EXTERNAL`;
- `REPRESENTATION`;
- `PROVENANCE`;
- `OBSERVATION`;
- `PROPOSED`;
- `REVOKED`.

Confidence/similarity cannot upgrade an anchor's authority class.

## 3. Anchor lifecycle

Governed anchor operations:
- ADD;
- REBIND;
- SUPERSEDE;
- REVOKE;
- RESTORE;
- EXPIRE;
- INVALIDATE_EVIDENCE.

Operations preserve source revision, authority/policy, reason and evidence.

Deletion never erases historical identity evidence.

## 4. IdentityDriftEvidence

Path-level typed evidence records:
- canonical expected trait/anchor;
- observation;
- comparison domain;
- semantic/numeric delta;
- uncertainty;
- modality/source;
- provenance;
- evaluator owner;
- impacted criticality/mutability;
- scope.

Evidence is noncanonical until admitted through mutation authority.

## 5. Drift dimensions

Required semantic dimensions:
- numeric/unit-aware;
- categorical;
- structural/component;
- topology/relation;
- anchor/link;
- cross-modal;
- missing-required;
- family/profile;
- collision/split evidence.

M05 forbids reducing all identity continuity to one scalar score.

## 6. Drift status

Candidate semantic states:
- `NO_DRIFT`;
- `WITHIN_DECLARED_VARIATION`;
- `OBSERVATION_UNCERTAIN`;
- `REPRESENTATION_DRIFT`;
- `IDENTITY_RELEVANT_DRIFT`;
- `MUTATION_CANDIDATE`;
- `IDENTITY_BREAK_CANDIDATE`;
- `COLLISION_OR_SPLIT_CANDIDATE`.

These are identity semantics, not M01 quality grades.

## 7. Repair boundary

Repair targets a representation/output back toward the same canonical DNA revision.

Repair:
- does not mutate DNA;
- does not create canonical traits;
- does not authorize protected changes;
- may consume drift evidence;
- may produce new representation evidence.

## 8. DNAMutationProposal

A mutation proposal names:
- proposal ID;
- stable dna_id;
- source revision;
- typed trait/anchor/link change set;
- reason;
- requested continuity outcome;
- authority/policy refs;
- evidence/provenance refs;
- impact/compatibility surface;
- required approvals;
- validity/expiry if applicable.

A proposal is never itself canonical DNA.

## 9. IdentityMutationDecision

Candidate decisions:
- `REJECT`;
- `REPAIR_INSTEAD`;
- `CONTEXTUAL_VARIATION_ONLY`;
- `ADMIT_SAME_IDENTITY_REVISION`;
- `REQUIRE_NEW_IDENTITY`;
- `REQUIRE_SPLIT`;
- `REQUEST_MORE_EVIDENCE`.

Decision authority must be explicit and policy-bound.

## 10. IdentityContinuityEnvelope

Defines same-identity policy context:
- identity-defining traits;
- bounded mutable traits;
- contextual traits;
- required anchors;
- required cross-modal links;
- allowed substitutions;
- forbidden transitions;
- evidence/evaluator requirements;
- decision-authority refs.

It is not an M01 Fidelity/Quality contract.

## 11. IdentityDriftReport

Aggregates drift evidence while preserving path-level facts.

Requirements:
- no averaging-away of identity-defining failure;
- missing/unknown evidence remains distinct from pass;
- uncertainty retained;
- evaluator owner retained;
- deterministic ordering/fingerprint;
- report never self-admits a mutation.

## 12. Identity break

When continuity policy fails, a new identity is required.

Identity break:
- creates a new `dna_id`;
- preserves explicit lineage to source revision;
- records break reason;
- carries only explicitly permitted traits/anchors/links;
- never rewrites source identity history.

## 13. Identity split

Split handles one historical identity containing or becoming multiple separately governed subjects.

Rules:
- source history remains immutable/auditable;
- resulting identities have explicit stable IDs;
- continuation branch, if any, is policy-explicit;
- traits/components/links allocation is explicit;
- provenance/rights refs remain reachable.

## 14. Identity equivalence / consolidation

Similarity never merges IDs automatically.

An `IdentityConsolidationProposal` can request equivalence/consolidation.

If admitted:
- both histories remain auditable;
- alias/redirect/equivalence semantics are explicit;
- canonical continuation selection is policy-bound;
- IDs are not erased;
- provenance/rights/privacy constraints survive.

S05 finalizes portability/branching compatibility.

## 15. M39 overlap resolution

M05 is the generic root authority for persistent Asset/Persona DNA identity.

M39 Digital Humans & Virtual Identity owns:
- digital-human persona production;
- face/body/hair/clothing consistency runtime;
- acting/expression/mannerism;
- cross-modal digital-human production continuity;
- spokesperson/avatar runtime and domain rights workflows.

M39 may expose a domain persona profile/link bound to M05, but cannot create a competing generic root identity.

This decision must be revalidated in the M06-M60 Forward Compatibility Scan.

## 16. Privacy-minimized drift

Sensitive identity evidence remains referenced and access-controlled.

M05 does not require raw:
- face embeddings;
- voiceprints;
- biometric templates;
- private reference media.

M54 may own restricted storage/access/security policy.
M53 owns rights/consent/provenance policy.

## 17. S04 candidate hard invariants

91. anchor authority class is explicit and cannot be upgraded by similarity/confidence alone.
92. anchor lifecycle changes preserve immutable historical evidence.
93. canonical anchor rebind/revoke requires explicit authority/policy.
94. observation/proposed anchors cannot mutate canonical identity.
95. drift evidence is path-level and typed.
96. identity drift cannot be represented solely by one scalar score.
97. missing/unknown evidence cannot be treated as pass.
98. identity-defining failures cannot be averaged away by aggregate scores.
99. drift findings preserve uncertainty and evaluator ownership.
100. drift evidence cannot self-admit a canonical mutation.
101. representation repair cannot rewrite canonical DNA.
102. contextual variation does not require DNA mutation when policy allows it.
103. DNAMutationProposal is noncanonical until an explicit decision admits it.
104. mutation proposals identify exact source revision and typed change surface.
105. protected trait mutation requires explicit policy/authority.
106. downstream model/provider output cannot silently authorize mutation.
107. IdentityMutationDecision authority is explicit and policy-bound.
108. same-identity admitted mutation creates a new immutable DNA revision.
109. identity break creates a new stable dna_id rather than rewriting the original.
110. identity-break lineage to source revision remains explicit.
111. identity split preserves source history and explicit allocation of traits/components/links.
112. identity consolidation/equivalence never erases source IDs/history.
113. similarity threshold alone cannot merge identities.
114. IdentityContinuityEnvelope is separate from M01 quality/Fidelity authority.
115. M37 temporal continuity evidence cannot mutate canonical M05 DNA.
116. M39 digital-human persona/runtime cannot create a competing generic identity root.
117. sensitive drift evidence may remain restricted references rather than canonical payload copies.
118. M53/M54 retain rights/consent/provenance/security authority over protected identity evidence.
119. drift/transition reports are deterministic and fingerprintable without embedding private evidence payloads.
120. HIVE/agents may detect/propose drift or mutation but cannot directly admit protected canonical identity changes.

These extend S01-S03 invariants 1–90 and remain candidates until final contract freeze.

## 18. S04 proprietary candidates

S04 adds `IRIS-DNAX-091..120`.

## S04 STOP CONDITION

S04 is complete for module planning when:
- anchor authority/lifecycle is explicit;
- drift evidence/status/report semantics are explicit;
- repair vs mutation is explicit;
- mutation proposal/decision boundaries are explicit;
- same-identity mutation vs identity break/split/consolidation is explicit;
- M01/M37/M39/M53/M54 firewalls are explicit;
- candidate invariants 91–120 are recorded;
- DNAX-091..120 are registered;
- checkpoint advances to S05;
- no M05 implementation code is introduced.

# S05 — DNA branching, compatibility and reusable DNA marketplace contract

Status: `NOT_STARTED`

Will freeze compatibility/equivalence, package portability, reusable DNA contract, marketplace safety boundaries and final versioning/migration semantics.

## S01 STOP CONDITION

S01 is complete for module planning when:
- the domain-neutral identity model is explicit;
- canonical/evidence separation is explicit;
- identity anchors and cross-modal projection boundaries are explicit;
- 30 candidate invariants are recorded;
- M02/M04/M06/M39/M40/M41/M43/M46/M53/M54 ownership boundaries are protected;
- technology candidates and prior-art references are registered;
- planning checkpoint advances to S02;
- no M05 implementation code is introduced.
