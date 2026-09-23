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

Status: `NOT_STARTED`

Will define cross-modal linked DNA families and ownership firewalls with M30/M40/M41/M43/M46.

# S04 — Identity anchors, mutation boundaries and drift detection

Status: `NOT_STARTED`

Will freeze drift evidence, mutation admission, identity break/split/merge semantics and repair proposals.

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
