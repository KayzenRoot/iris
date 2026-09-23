# M05 Module Contract Freeze Candidate — Asset DNA 2.0 & Cross-Modal Identity

Status: `FROZEN_APPROVED`
Frozen version: `m05-contract-v1.0`
Module: `M05`
Issue: `#37`
PR: `#38`
Authorized baseline: `6f2311b59f5da91778d3fc9d9fe1572953a0c60b`

## 1. Mission

M05 owns IRIS's generic persistent semantic identity model for assets/personas across representations, modalities, providers, projects and governed identity evolution.

M05 is the canonical authority for:
- stable persistent subject identity;
- immutable semantic DNA revisions;
- identity traits/criticality/mutability;
- identity anchors and projection obligations;
- family/profile/component identity semantics;
- cross-domain DNA links;
- drift/mutation/break/split/consolidation semantics;
- semantic identity lineage;
- directional compatibility/migration;
- reusable DNA package semantics.

M05 is **not**:
- M01 quality/evaluator/promotion authority;
- M02 project/Production Graph/branch/build/release authority;
- M04 representation/SceneIR authority;
- M06 operational production-state persistence/reconstruction authority;
- M30 MotionDNA production authority;
- M37 temporal/shot-continuity authority;
- M39 digital-human/persona production engine;
- M40 VoiceDNA authority;
- M41 ArtistDNA/MusicDNA authority;
- M43 Canon authority;
- M45 Campaign DNA authority;
- M46 BrandDNA authority;
- M53 rights/license/consent/provenance authority;
- M54 security/restricted-content authority;
- M55 media CAS/storage/cache/archive authority;
- M58 API/SDK/MCP/plugin-lifecycle authority;
- M59 export/publishing/delivery authority.

## 2. Upstream and adjacent authority

M05 consumes or references, but does not supersede:

- **M01**: quality/Fidelity/evaluator/promotion authority.
- **M02**: project/production identity, Production Graph, branch/variant/snapshot/rollback, incremental-build/reuse, promotion/release/archive lifecycle.
- **M03**: admitted creative intent/constraints and identity-relevant semantic obligations.
- **M04**: provider-neutral representation identities/anchors/SceneIR.

Adjacent/downstream ownership:
- **M06** operationalizes content-addressed production-state persistence/revisions, dependency indexing, reconstruction, cleanup and rollback execution under M02 semantic contracts.
- **M55** owns media CAS/storage/cache/archive backends.
- domain DNA engines own their domain contents; M05 owns only generic identity/link semantics unless explicitly stated otherwise.

## 3. Public frozen concept families

Implementation class names may adapt, but these semantics MUST exist.

### Identity / revision / traits
- AssetDNAIdentity
- DNARevision
- DNAEnvelope
- DNATrait
- TraitSchemaRef
- TraitCriticality
- TraitMutability
- TraitApplicability
- DNAFingerprint
- IdentityChangeSurface

### Anchors / projections / aliases
- IdentityAnchor
- AnchorAuthorityClass
- AnchorLifecycleOperation
- DNAProjectionContract
- IdentityAlias
- IdentityEquivalenceClaim
- DNAConflict
- IdentityCollisionFinding
- MinimumSufficientDNASlice

### Family / component / subject profiles
- DNAFamilyProfile
- DNATraitBundle
- DNAComponentIdentity
- CharacterDNA profile
- CreatureDNA profile
- ObjectDNA profile
- ProductDNA profile
- EnvironmentDNA profile
- PersistentAppearanceTrait
- ContextualAppearanceState
- AppearanceObservation

### Cross-domain links / scene identity
- LinkedDomainDNARef
- SceneIdentityDNA
- IdentityRoleSlot
- MotionDNALink
- VoiceDNALink
- BrandDNALink
- CrossModalIdentityBinding
- CrossModalIdentityObligation
- CrossModalDNAGraph

### Drift / mutation / continuity
- IdentityDriftEvidence
- IdentityDriftReport
- IdentityContinuityEnvelope
- DNAMutationProposal
- IdentityMutationDecision
- IdentityConsolidationProposal
- IdentityBreakLineage
- IdentitySplitAllocation

### Compatibility / migration / packaging
- DNACompatibilityProfile
- DNAMigrationPlan
- DNAMigrationReceipt
- ReusableDNAPackageManifest
- DNAMarketplaceContract
- DNAPackageConformanceReport
- DNAImportAdmissionState
- DNAPackageLifecycle

## 4. Consolidated technology families

Frozen contract candidate recognizes:

1. `F-M05-01 Persistent Identity & Revision Core`
2. `F-M05-02 Trait Semantics & Applicability Fabric`
3. `F-M05-03 Canonical / Evidence Authority Fabric`
4. `F-M05-04 Anchor & Projection Authority Fabric`
5. `F-M05-05 Identity Resolution, Alias & Consolidation Fabric`
6. `F-M05-06 Interface Capsule & Minimum Context Fabric`
7. `F-M05-07 Family / Profile / Extension Fabric`
8. `F-M05-08 Persistent Component Identity Fabric`
9. `F-M05-09 Character & Creature Identity Profile Fabric`
10. `F-M05-10 Object & Product Identity Profile Fabric`
11. `F-M05-11 Environment Identity Profile Fabric`
12. `F-M05-12 Cross-Domain DNA Link Fabric`
13. `F-M05-13 Scene Identity Composition Fabric`
14. `F-M05-14 Motion / Voice / Brand Link Firewall Fabric`
15. `F-M05-15 Cross-Modal Binding & Obligation Graph`
16. `F-M05-16 Drift Evidence & Continuity Analysis Fabric`
17. `F-M05-17 Mutation Admission & Same-Identity Revision Fabric`
18. `F-M05-18 Identity Break & Split Fabric`
19. `F-M05-19 Protected Identity Evidence & Authority Bridge`
20. `F-M05-20 Semantic Identity Lineage & Versioning Firewall`
21. `F-M05-21 Directional Compatibility & Migration Fabric`
22. `F-M05-22 Reusable DNA Package & Dependency Fabric`
23. `F-M05-23 Marketplace / Storage / Delivery Boundary Fabric`
24. `F-M05-24 Import / Conformance / Package Lifecycle Fabric`
25. `F-M05-25 Identity Risk & Threat Radar Fabric`

Detailed `IRIS-DNAX-001..150` remain non-normative design-history references.
The Final Technology Review maps all 150 exactly once into these 25 families.

## 5. Hard invariants

### Identity core — 1..30

1. `dna_id` is stable and opaque; display metadata never defines it.
2. file/path/URL/storage location never defines persistent identity.
3. content digest identifies representation/content, not automatically subject identity.
4. provider/model/workflow IDs never define canonical M05 identity.
5. prompts and generated output IDs never define canonical identity.
6. embeddings/perceptual hashes/similarity scores are evidence only.
7. DNA revisions are immutable.
8. M02 remains branch/project/history authority.
9. M06 operational production-state/content-addressed persistence/reconstruction and M55 media CAS/storage/cache/archive remain external authorities; M05 owns neither.
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

### Domain family identity — 31..60

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

### Cross-modal identity links — 61..90

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

### Drift / mutation / continuity — 91..120

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

### Compatibility / packaging / import — 121..150

121. M05 lineage relations cannot create or replace M02 project/production branches.
122. M02 remains branch/snapshot/rollback authority.
123. M06 operational persistence/reconstruction/versioning must implement M02 semantic build/version/rollback contracts rather than create competing authority.
124. build/master/content hashes cannot become persistent dna_id automatically.
125. DNA compatibility is directional.
126. DNA compatibility is multi-axis and cannot be proven by version number alone.
127. compatibility outcome preserves unknown/indeterminate distinct from compatible.
128. lossy compatibility must be explicit.
129. DNAMigrationPlan declares transformed/preserved/dropped/defaulted paths.
130. migration loss cannot be hidden.
131. migration cannot silently convert identity break into same-identity continuation.
132. unknown mandatory schema/extension semantics fail closed during migration/import.
133. reusable package ID/version is distinct from subject dna_id/revision.
134. repackaging cannot redefine subject identity by itself.
135. a package may contain multiple DNA identities only when explicitly declared.
136. package dependency closure distinguishes required and optional dependencies.
137. missing required package dependency fails closed.
138. marketplace contract cannot self-authorize rights/license/consent.
139. M53 remains rights/license/consent/provenance authority.
140. package security classification cannot self-prove safety.
141. M54 remains security/restricted-content/permission authority.
142. M55 remains storage/CAS/cache/archive authority.
143. M59 remains concrete export/publishing/delivery authority.
144. import parsing/validation cannot overwrite existing canonical DNA silently.
145. imported identity collision/equivalence routes through governed S04 semantics.
146. restricted biometric/private evidence is referenced/minimized unless explicit policy permits inclusion.
147. canonical reusable DNA package requires no arbitrary executable code.
148. deprecation/retirement never rewrites historical package/DNA revisions.
149. conformance report proves contract/schema conformance, not legal rights or semantic identity equivalence by itself.
150. HIVE/agents may discover/package/propose compatibility but cannot directly admit imported canonical identity or protected mutations.

## 6. Identity substrate contract

Implementation must support:
- stable opaque `dna_id`;
- immutable revision IDs and source-revision refs;
- explicit trait schema family/version;
- identity criticality and mutability;
- four-state applicability;
- deterministic canonical serialization/fingerprint;
- canonical/evidence twin-plane separation;
- provenance/policy reachability;
- unknown mandatory semantics fail-closed;
- optional opaque preservation only under explicit policy;
- minimum-sufficient DNA slices.

Names, paths, URLs, storage locations, model/provider IDs, prompts, embeddings and similarity scores are never sufficient subject identity.

## 7. Family / component contract

Implementation must support:
- CLASS / ARCHETYPE / INDIVIDUAL / VARIANT levels;
- typed family profiles;
- typed trait bundles;
- persistent components independent of order/name/index;
- governed replacement/split/merge;
- Character/Creature/Object/Product/Environment profiles;
- non-humanoid/variable-component creatures;
- Product family/model/SKU/package/physical-instance distinctions;
- environment topology/landmark persistence;
- persistent/contextual/observed appearance separation;
- explicit family reclassification/migration.

## 8. Anchor / projection contract

Implementation must support:
- explicit anchor authority classes;
- auditable anchor lifecycle;
- representation anchors distinct from persistent subject identity;
- explicit DNA projection consumed paths;
- required/optional preservation;
- no silent loss of mandatory identity traits;
- stale/unknown mandatory anchors fail-closed where policy requires;
- deterministic anchor/link change surfaces.

## 9. Cross-domain DNA link contract

Implementation must support:
- owner module;
- DNA family;
- external identity;
- exact pinned revision/version;
- REQUIRED/OPTIONAL role;
- bound M05 trait/component paths;
- preservation obligations;
- compatibility expectation;
- validity scope;
- policy/provenance/rights refs;
- freshness/staleness state.

Implicit `latest` is forbidden for canonical required links.

M30/M40/M41/M45/M46 retain their domain DNA contents.

## 10. Scene identity contract

Implementation must support:
- reusable persistent SceneIdentityDNA;
- environment DNA refs;
- member DNA refs;
- stable IdentityRoleSlots;
- cardinality/substitution policy;
- continuity-critical member/landmark relationships;
- M04 SceneIR projection refs;
- M43 Canon refs.

SceneIdentityDNA is not:
- one current SceneIR snapshot;
- shot/editorial state;
- Canon truth;
- M37 continuity judgment.

## 11. Drift / mutation contract

Implementation must support:
- path-level typed drift evidence;
- numeric/categorical/structural/component/relation/anchor/link/cross-modal/missing/family drift;
- explicit uncertainty and evaluator ownership;
- deterministic IdentityDriftReport;
- no single-score identity decision;
- IdentityContinuityEnvelope;
- repair vs mutation firewall;
- DNAMutationProposal;
- explicit policy-bound IdentityMutationDecision;
- same-identity new immutable revision;
- identity break -> new dna_id + lineage;
- identity split allocation;
- non-destructive consolidation/equivalence.

Provider/model output and similarity evidence may propose, never self-admit protected canonical changes.

## 12. Privacy / rights / security contract

M05 must minimize sensitive identity evidence.

Generic canonical DNA does not require raw:
- face embeddings;
- voiceprints;
- biometric templates;
- private reference media.

M05 may hold versioned refs to:
- M53 rights/license/consent/provenance records;
- M54 restricted-vault/security/access policy.

A package/conformance result cannot prove legal rights, consent, safety or real-world personal identity.

## 13. Semantic lineage contract

Allowed identity-level lineage semantics include:
- SAME_IDENTITY_REVISION;
- VARIANT_DERIVATION;
- ARCHETYPE_DERIVATION;
- IDENTITY_BREAK_DERIVATION;
- SPLIT_CHILD;
- CONSOLIDATION_CONTINUATION;
- TEMPLATE_INSTANTIATION.

These never create or replace:
- M02 project/Production Graph branches/snapshots/rollback/build lifecycle;
- Git/VCS branches;
- M06 operational production-state reconstruction history.

## 14. Compatibility / migration contract

DNA compatibility is directional and multi-axis.

Required axes:
- schema;
- family/profile;
- traits;
- components;
- anchors;
- domain links;
- extensions;
- consumer capability;
- policy/rights references.

Required outcomes:
- EXACT;
- COMPATIBLE;
- COMPATIBLE_WITH_LOSS;
- REQUIRES_MIGRATION;
- BREAKING;
- INDETERMINATE.

Migration must record:
- source/target schema-family-version;
- transformed/preserved/dropped/defaulted paths;
- anchor/link changes;
- loss surface;
- identity-continuity expectation;
- authority/policy refs;
- deterministic receipt/fingerprint.

Migration cannot silently preserve identity when the continuity policy requires a break.

## 15. Reusable DNA package contract

Implementation must support ReusableDNAPackageManifest with:
- package ID/version;
- contained M05 DNA identities/revisions;
- family/profile schemas;
- canonical fingerprints;
- required/optional external DNA refs;
- compatibility profile;
- migration capabilities;
- dependency closure;
- rights/license/consent refs;
- provenance refs;
- security classification/policy refs;
- conformance requirements;
- human-readable metadata.

Package ID/version is distinct from subject dna_id/revision.

Portable levels:
- INTERFACE_ONLY;
- PORTABLE_CANONICAL;
- PRODUCTION_REFERENCE;
- RESTRICTED_REFERENCE.

Canonical package format requires no arbitrary executable code.

## 16. Marketplace boundary

DNAMarketplaceContract is exchange/conformance metadata only.

It may expose:
- package identity/version;
- family/profile;
- compatibility claims;
- consumer capability requirements;
- rights/license/consent/provenance refs;
- security classification;
- use/role/geographic restrictions as policy refs;
- allowed derivative/mutation classes;
- attribution refs;
- lifecycle/deprecation status.

M05 does not own:
- payment;
- pricing;
- ranking;
- seller reputation;
- storefront UI;
- tax/commercial settlement;
- hosting/CDN.

## 17. Import / conformance contract

Import admission states:
- PARSED;
- VALIDATED;
- COMPATIBILITY_CHECKED;
- POLICY_CHECKED;
- QUARANTINED;
- ADMISSION_PROPOSED;
- ADMITTED;
- REJECTED.

Import cannot silently overwrite existing canonical DNA.

DNAPackageConformanceReport checks:
- manifest integrity;
- schema/version support;
- fingerprints;
- dependency closure;
- compatibility declarations;
- required domain links;
- rights/provenance/security refs;
- restricted-payload policy;
- deterministic serialization;
- unknown mandatory extension handling.

Conformance is not legal/safety/identity-equivalence proof.

## 18. Required future extension / ref boundaries

M05 must expose versioned boundaries sufficient for:

1. `ProductionStateRefPort` — M02/M06 build/master/reconstruction refs without identity takeover.
2. `HardwareExecutionConstraintRef` — M07-M10 runtime limitations cannot mutate DNA.
3. `WorkerPlacementIdentityContextPort` — M11-M13 identity slices/refs for execution/cache.
4. `ModelCapabilityIdentityEvidencePort` — M14/M15 evidence only.
5. `ConcreteWorkflowIdentityProjectionPort` — M16/M17 compile/run identity obligations.
6. `TrainingIdentityDatasetRefPort` — M18/M19 training/provenance refs without canonical mutation.
7. `ImageReferenceIdentityEvidencePort` — M20-M24 observation/control/evaluation refs.
8. `GeometryAppearanceIdentityPort` — M25-M29 representation of identity-relevant form/material/anatomy.
9. `MotionDNARefPort` — M30 domain-owned MotionDNA.
10. `RenderObservationPort` — M31/M32 contextual/render evidence.
11. `DCCIdentityBindingPort` — M26/M33 representation anchors and round-trip refs.
12. `DeliveryProjectionCompatibilityPort` — M34/M35 constrained-target preservation/loss.
13. `TemporalContinuityEvidencePort` — M36-M38/M37 evidence without DNA mutation.
14. `DigitalHumanPersonaBindingPort` — M39 domain persona continuity bound to M05 root.
15. `VoiceMusicAudioDomainDNAPort` — M40-M42 domain DNA/audio refs.
16. `CanonContentCampaignBrandPort` — M43-M46 domain identity links without ownership transfer.
17. `LocalizationIdentityPreservationPort` — M47 cross-language adaptation obligations.
18. `QualityRepairProposalPort` — M48-M51 evidence/proposals, no direct mutation.
19. `HIVEMemoryIdentitySlicePort` — M52 derived context/minimum sufficient DNA.
20. `RightsSecurityEvidencePort` — M53/M54 policy/vault refs.
21. `StorageObservabilityAutomationPort` — M55-M57 location/telemetry/agent proposal boundaries.
22. `APIExportRecoveryIdentityPort` — M58-M60 conformance/export/restore boundaries.

These are contracts/ports, not implementations.

## 19. Ownership overlap freezes

### M02 / M06 / M55
M02 owns semantic project/production branch/snapshot/rollback/build-reuse/promotion lifecycle.
M06 operationalizes production-state content-addressed persistence/revisions, dependency indexing, reconstruction, cleanup and rollback execution under M02.
M55 owns media CAS/storage/cache/archive backends.
M05 owns semantic identity revision/lineage only.

### M04
M04 owns provider-neutral representation identities and SceneIR.
M05 owns persistent semantic subject identity.
Bindings are explicit; neither identity space silently becomes the other.

### M30 / M40 / M41 / M45 / M46
M30 owns MotionDNA.
M40 owns VoiceDNA.
M41 owns ArtistDNA/MusicDNA.
M45 owns Campaign DNA / Creative Genome.
M46 owns BrandDNA / Brand & IP.
M05 owns generic revision-pinned domain-DNA link semantics.

### M37 / M39
M37 owns temporal/shot continuity judgment and repair evidence.
M39 owns digital-human/persona production continuity and binds its persona domain profile to the M05 root.
Neither may mutate M05 canonical DNA directly.

### M43
M43 owns Canon/story/world truth.
M05 may bind persistent character/scene/environment identities to Canon refs.

### M48 / M01
M01/M48 own quality judgment/evaluator/promotion semantics.
M05 drift/continuity statuses are identity semantics, not quality grades.

### M53 / M54
M53 owns rights/license/consent/provenance/C2PA.
M54 owns security/access identity/restricted-content/restricted-vault policy.
M05 carries minimized refs and semantic identity facts only.

### M58 / M59 / M60
M58 exposes APIs/SDK/MCP/plugin lifecycle and conformance surfaces.
M59 owns concrete export/publishing/delivery.
M60 owns deployment/recovery/final system integration acceptance.
None may redefine persistent subject identity or strip mandatory identity/policy refs.

## 20. Serialization / dependency boundary

The future M05 semantic kernel may depend on:
- Python standard library;
- stable public M01/M02/M03/M04 interfaces where required;
- opaque/versioned refs to downstream authorities.

The M05 core MUST NOT require:
- Blender/Maya/ComfyUI;
- provider/model SDKs;
- GPU/runtime SDKs;
- database/media-storage SDKs;
- TTS/voice/biometric engines;
- payment/storefront SDKs;
- network/shell/external process access;
- arbitrary executable package/schema validators.

Adapters/infrastructure belong later.

## 21. Security / trust boundary

Implementation must fail closed for:
- unknown mandatory trait/link/schema/extension semantics;
- forged canonical mutation authority;
- provider/model output self-promoting to canonical DNA;
- similarity/confidence auto-merge;
- stale required domain links;
- unauthorized anchor rebind/revoke;
- hidden identity-defining drift behind aggregate scores;
- missing evidence represented as pass;
- package import overwrite/collision;
- hidden lossy migration;
- rights/security refs stripped during package transformation;
- executable payload embedded in canonical DNA package by default;
- restricted evidence copied without policy;
- history erasure during break/split/consolidation;
- package/content/build IDs spoofed as persistent subject identity.

## 22. Context / performance requirements

Implementation must make measurable:
- DNAInterfaceCapsule;
- MinimumSufficientDNASlice;
- trait/component/link scoped retrieval;
- deterministic fingerprints and change surfaces;
- locality-preserving drift/mutation analysis;
- no full identity-history replay for localized read operations when a dependency-closed slice suffices;
- evidence payload separation from canonical semantic identity;
- downstream provider/model changes do not invalidate canonical DNA when semantics are unchanged.

No arbitrary performance/token-saving percentages may be claimed without benchmark evidence.

## 23. Domain-neutral synthetic targets

The same M05 core must support at least:

1. persistent human/digital spokesperson character;
2. non-humanoid creature with variable/asymmetric components;
3. generic object/prop/tool/vehicle;
4. product family/model/SKU/package/serialized instance;
5. persistent environment/set/location across scene-state changes;
6. cross-modal character with MotionDNA + VoiceDNA + BrandDNA links;
7. reusable SceneIdentityDNA with replaceable role slots;
8. portable/reusable DNA package imported under rights/security constraints.

No one domain's fields may be mandatory for all others.

## 24. Required behavior

At minimum, later implementation must:
- create/read immutable DNA identities/revisions;
- deterministically serialize/fingerprint canonical DNA;
- validate trait schema/criticality/mutability/applicability;
- bind/unbind anchors through governed lifecycle;
- build family/profile/component identity structures;
- create cross-domain DNA links with pinned revisions;
- create SceneIdentityDNA and role slots;
- produce minimum-sufficient DNA slices;
- compute drift evidence/reports without canonical mutation;
- create mutation proposals/decisions/receipts;
- admit same-identity revisions;
- create identity break/split/consolidation lineage;
- compute directional compatibility;
- plan/receipt migrations;
- create/validate reusable DNA package manifests;
- compute dependency closure;
- stage imports without overwrite;
- produce package conformance reports;
- preserve rights/security/provenance refs;
- expose extension/ref ports without implementing downstream modules.

## 25. Acceptance tests

Later implementation must prove at minimum:

### Identity / revision
- dna_id stable under display/path/location/provider changes;
- immutable revisions;
- fingerprint deterministic;
- observation/evidence excluded from canonical digest where specified;
- duplicate/conflicting canonical IDs rejected.

### Traits / families / components
- four applicability states remain distinct;
- unknown mandatory trait schema fails closed;
- family defaults cannot override explicit criticality/mutability;
- component order/name/index changes do not change component identity;
- human-only assumptions do not leak into CreatureDNA;
- product identity levels remain distinct.

### Anchors / projections
- M04 node IDs cannot self-promote to M05 identity;
- protected anchor changes require authority;
- mandatory projected traits cannot silently disappear;
- stale required links block/review as declared.

### Cross-modal
- external DNA links are owner/family/revision pinned;
- implicit latest rejected for canonical required links;
- Motion/Voice/Brand contents remain domain-owned;
- SceneIdentityDNA does not become SceneIR or Canon truth;
- missing required domain links fail closed.

### Drift / mutation
- one similarity score cannot admit identity continuity/mutation;
- missing evidence != pass;
- fatal identity-defining conflicts cannot be averaged away;
- repair does not mutate DNA;
- model/provider output cannot self-admit mutation;
- same-identity mutation creates new immutable revision;
- identity break creates new dna_id;
- split/consolidation preserve source history.

### Rights / privacy / security
- sensitive evidence may remain ref-only;
- rights/security refs preserved;
- no biometric authentication required for generic DNA;
- conformance cannot claim legal rights/safety.

### Lineage / compatibility / migration
- M05 lineage cannot create M02 branches;
- build/content hashes cannot become dna_id;
- compatibility is directional/multi-axis;
- INDETERMINATE distinct from COMPATIBLE;
- lossy compatibility explicit;
- migration loss/defaults explicit;
- identity-break requirement cannot be silently migrated away.

### Package / import
- package ID distinct from dna_id;
- required dependency missing fails closed;
- package import cannot overwrite canonical identity;
- collision/equivalence routes through governed resolution;
- non-executable package default enforced;
- lifecycle deprecation does not rewrite history.

### Authority / closed runtime
- no direct canonical mutation from HIVE/agents/providers;
- M39 persona continuity binds to M05 root;
- M02/M06/M55 ownership shields enforced;
- no provider/DCC/cloud/database/network/shell requirement in core.

## 26. Out of scope for M05 implementation

- project/Production Graph branch/snapshot/build/release engine;
- content-addressed production reconstruction runtime;
- media CAS/storage backend;
- SceneIR implementation beyond refs/bindings;
- image/video/3D/audio generation;
- rigging/motion generation;
- VoiceDNA creation/TTS/voice cloning;
- MusicDNA/composition;
- Campaign/advertising engine;
- BrandDNA authoring/Brand Court;
- Canon/story engine;
- temporal continuity judge/repair runtime;
- quality judges/promotion;
- rights/license/consent engine;
- restricted-vault/security engine;
- marketplace payments/storefront/ranking/commerce settlement;
- API/plugin platform;
- publishing/export runtime;
- HIVE retrieval implementation.

## 27. Evidence obligations for implementation executor

A later bounded implementation Work Order must record:
- exact base/head SHA and frozen contract version;
- public API/concept mapping;
- mapping from `F-M05-01..25` into implementation modules;
- proof coverage for all 150 hard invariants;
- dependency/import surface;
- serialization/schema/version profile;
- deterministic fingerprint evidence;
- focused M05 test counts/results;
- authority-firewall static/runtime tests;
- domain-neutral fixture evidence;
- minimum-sufficient-slice/context evidence;
- drift/mutation/break/split/consolidation evidence;
- compatibility/migration/package/import evidence;
- privacy/restricted-evidence tests;
- no executable canonical package evidence;
- no provider/DCC/database/network/shell core dependency;
- failures fixed;
- deferred extension ports;
- Evidence Bundle and proposed Checkpoint Delta.

## 28. Implementation STOP CONDITION

STOP only when the complete frozen M05 provider-neutral semantic identity kernel is implemented, tested, documented, evidence-bundled, pushed and ready for independent review.

DO NOT MERGE on executor word.
DO NOT start M06 implementation merely to satisfy M05 ports.
DO NOT implement downstream domain engines merely to satisfy refs.
DO NOT weaken any frozen invariant.
If implementation requires semantic contract change, STOP `BLOCKED_CONTRACT_CONFLICT`.

## 29. Freeze evidence required before v1.0 approval

Before status becomes `FROZEN_APPROVED / m05-contract-v1.0`, planning PR must prove:

- S01-S05 complete;
- Final Technology Review `APPROVED_FOR_FORWARD_COMPATIBILITY`;
- `IRIS-DNAX-001..150` mapped exactly once into `F-M05-01..25`;
- M06-M60 Forward Compatibility `PASS_WITH_EXTENSION_PORTS`;
- 22 required future extension/ref families recorded;
- M02/M06/M55 ownership boundary reconciled;
- M39 persona continuity explicitly bound to M05 root identity;
- exact-head Governance PASS;
- full existing repository tests green;
- planning/docs/governance-only diff;
- independent planning audit `APPROVED`;
- zero HIGH/CRITICAL planning blockers.

Any semantic change after freeze requires a versioned M05 contract amendment + renewed compatibility review.

## 30. Freeze candidate state

- Target contract: `m05-contract-v1.0`
- Status: `FROZEN_APPROVED`
- S01-S05: complete
- Hard invariants: 150
- Consolidated technology families: 25
- Forward compatibility modules scanned: 55
- Future extension/ref families: 22
- Final Technology Review: approved for forward compatibility
- Forward Compatibility Scan: pass with extension ports
- Independent planning audit: `APPROVED`
- Product/kernel implementation: not started
- HIGH/CRITICAL blockers known at candidate creation: 0

The independent planning audit must review the exact candidate head before promotion to `FROZEN_APPROVED`.


## 31. Freeze closure

- Contract: `m05-contract-v1.0`
- Status: `FROZEN_APPROVED`
- Independent planning audit: `APPROVED`
- Reviewed freeze-candidate head: `2f3102b4701fd0f3a9113f1a7d9cef924c9cc6fa`
- Reviewed Governance: `35842498444 / 107120660586` — PASS
- Reviewed full suite: `2677/2677 OK`
- Hard invariants: `150/150`
- Consolidated families: `25/25`
- Future extension/ref families: `22/22`
- DNAX mapping: `150/150 exactly once`
- HIGH/CRITICAL planning blockers: `0`
- Product/kernel implementation: not started

This freeze-promotion delta is governance/documentation-only and must pass exact-head Governance before planning merge.

Any semantic contract change after this point requires a versioned M05 contract amendment and renewed compatibility review.


## 32. Planning merge / exact-main validation

- Planning PR: `#38`
- Merge method: `squash`
- Merge SHA: `2b5b7330a684fece8e354b6fe88b8fcd4bb0611f`
- Exact-main Governance: `35843109186 / 107122673542` — PASS
- Required artifacts: `35`
- Exact-main full suite: `2677/2677 OK`
- Planning state: `MERGED_MAIN_VALIDATED`
- M05 implementation: not started

The frozen contract is now the only admissible semantic source for a later M05 implementation package.
