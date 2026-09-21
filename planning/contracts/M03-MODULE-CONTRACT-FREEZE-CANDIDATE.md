# M03 — Module Contract Freeze Candidate

Status: `FROZEN_APPROVED`
Version: `m03-contract-v1.0`
Module: `Creative Brief, Intent & Constraint Compiler`

## 1. Contract purpose

Freeze the provider-neutral semantic compiler that turns human/project creative direction into immutable, explainable and versioned:
- Intent Model;
- Constraint Set;
- M01 Fidelity Contract Set;
- Execution Intent Bundle;
- conflict/override/versioning evidence;
- semantic fingerprints/deltas/slices.

M03 is **not** a media generator, prompt store, quality judge, Production Graph owner, Scene IR, provider workflow compiler, worker scheduler, rights/security authority, HIVE state owner or publishing provider.

## 2. Upstream authority dependencies

M03 consumes without redefining:

### M01 Quality Kernel
M01 remains sole authority for:
- `FidelityContract`;
- `FidelityDimension` / DimensionRegistry;
- QualityClass;
- PromotionRule / hard gates;
- evaluator registry/authority;
- defects / QualityDebt;
- QualityDecision;
- human-review evidence semantics.

### M02 Project OS & Production Graph
M02 remains sole authority for:
- project/production identity;
- graph causality;
- branches/variants/snapshots;
- build/reuse semantics;
- lifecycle/promotion/release/archive;
- executable side-effect/reconciliation semantics;
- ProviderCompiler port and ExecutionPlan contract.

M03 objects bind to M02 refs; M03 never creates a competing project/branch/build/release state model.

## 3. Required public semantic concepts

Exact implementation class names may adapt to repository conventions, but these semantics must exist.

### Brief / intent
- CreativeBriefIdentity
- BriefRevision
- RawInputRef
- IntentModel
- IntentStatement
- IntentOrigin
- IntentAuthorityRef
- AmbiguityRecord
- AmbiguityConsequence
- FreedomZone
- OpenQuestion
- SemanticIntentFingerprint
- IntentDelta
- SemanticEquivalenceProfile

### Constraints
- Constraint
- ConstraintPolarity
- ConstraintStrength
- ConstraintPredicate
- ConstraintScope
- ConditionalConstraint
- ToleranceEnvelope
- AntiReference
- ProtectedSemanticZone/AnchorRef
- ConstraintBundle
- ConstraintCoverage
- ConstraintFingerprint
- ConstraintViolationRef

### Fidelity compilation
- QualityIntentProjection
- FidelityContractSpec
- FidelityCompilationGap
- FidelityCompilationStatus
- FidelityContractSetRef
- QualityObligationTrace
- QualityContractDelta
- FidelityCompilationFingerprint

### Execution intent
- ExecutionIntentBundle
- IntentOperation
- CapabilityDemand
- SemanticMutationEnvelope
- SemanticLossClass
- ProviderTranslationReceiptRef/contract
- ExecutionIntentGap
- ExecutionIntentDelta
- ExecutionIntentFingerprint
- MinimumSufficientExecutionSlice

### Explainability / provenance
- IntentExplanationGraph
- ExplanationNode/Edge
- ExplanationProjection
- ProvenanceCapsule/Ref
- MinimumSufficientSemanticSlice

### Conflicts / overrides / versioning
- SemanticConflict
- ConflictClass
- ConflictConsequence
- ConflictResolutionState
- AuthorityPolicyGraphRef
- OverrideReceipt
- OverrideAction
- TemporaryOverrideLease
- OverrideDebt
- BriefSemanticMergeAnalysis
- MigrationReceipt
- BriefFreshnessVector
- DerivedIntentDependency
- RestorationRevision
- ConflictResolutionFingerprint
- SemanticReleaseReadinessReport

## 4. Consolidated technology families

The contract recognizes these families from Final Technology Review:
1. `F-M03-01 Intent Semantic Core`;
2. `F-M03-02 Ambiguity & Clarification Core`;
3. `F-M03-03 Minimum Sufficient Semantic Slice Fabric`;
4. `F-M03-04 Semantic Fingerprint, Delta & Reuse Fabric`;
5. `F-M03-05 Constraint Semantic Core`;
6. `F-M03-06 Negative / Protected Intent Integrity`;
7. `F-M03-07 Semantic Admission Shield`;
8. `F-M03-08 M01 Fidelity Compilation Bridge`;
9. `F-M03-09 No-Downgrade Quality Shield`;
10. `F-M03-10 Explainability & Provenance Graph`;
11. `F-M03-11 Provider-Neutral Execution Intent Core`;
12. `F-M03-12 Semantic Loss & Provider Translation Integrity`;
13. `F-M03-13 Conflict & Override Governance`;
14. `F-M03-14 Temporary Override / Semantic Debt`;
15. `F-M03-15 Semantic Revision, Merge, Migration & Restoration`;
16. `F-M03-16 Semantic Release Readiness`.

Detailed design-history identifiers `IRIS-ICX-001..090` remain non-normative supporting history.

`ICX-014 Semantic Entropy Radar` and `ICX-034 Creative Elasticity Budget` are research-only and are not frozen core requirements.

## 5. Hard invariants

1. raw input/source is preserved separately from normalized semantics;
2. Creative Brief stable identity is distinct from immutable brief revision identity;
3. admitted revisions are immutable; edits create new revisions;
4. explicit/derived/inferred/defaulted origins are never conflated;
5. authority and confidence are independent;
6. generated/retrieved/untrusted text cannot self-promote authority;
7. creative Freedom Zones are first-class and are not treated as missing data;
8. blocking ambiguity fails closed;
9. canonical intent is structured semantic data, not provider prompt text;
10. canonical constraints are semantic rules, not provider-specific negative-prompt syntax;
11. constraint polarity is distinct from strength;
12. arbitrary executable code is forbidden in canonical constraints;
13. mandatory unknown predicate/semantic extension fails closed;
14. scope does not imply authority;
15. negative intent/protected anchors must survive downstream translation or block;
16. M03 may not invent M01 FidelityDimension IDs;
17. M03 may not grant M01 evaluator capability;
18. M03 may not fabricate HUMAN_DECISION evidence;
19. M03 may not weaken M01 FATAL/hard-gate invariants;
20. vague adjectives do not directly choose M01 QualityClass;
21. hardware/provider scarcity must not silently lower requested final QualityClass;
22. incomplete quality capability/profile coverage blocks complete FidelityContract emission;
23. M03 Execution Intent is not an M02 ExecutionPlan;
24. provider/model/DCC/worker/runtime choices are not canonical M03 semantics;
25. prompts/workflows are derived provider artifacts;
26. mandatory unsupported provider capability cannot be silently dropped;
27. semantic loss is tracked per obligation; no aggregate score may hide a lossless-required failure;
28. every operation/capability/quality obligation has an explanation path to admitted source/policy;
29. recency, specificity or LLM confidence alone cannot resolve conflicts;
30. effective overrides require explicit authorized immutable receipts;
31. ordinary M03 overrides cannot bypass M01/M02/governance/non-overridable rights-security invariants;
32. weakening/disable actions are explicitly authority-gated;
33. expired/stale temporary overrides invalidate dependent compiled state;
34. OverrideDebt is distinct from M01 QualityDebt;
35. agents may propose but cannot self-approve restricted overrides;
36. semantic restoration creates new history;
37. migrations never rewrite old revisions;
38. stale derived/inferred statements cannot continue as current truth after their dependencies change;
39. M02 remains authority for branch/variant/rollback topology;
40. HIVE remains derived context, never canonical intent state;
41. publishing/delivery desire is not side-effect authorization;
42. provider observations/results cannot mutate canonical M03 state directly;
43. every compiled object is version-pinned and fingerprinted;
44. timestamps are never sufficient proof of semantic freshness;
45. semantic-equivalent source edits may preserve downstream reuse only under explicit versioned equivalence rules;
46. final semantic release-readiness is evidence, not a replacement for downstream M01/M02/M53/M54/M59 gates.

## 6. Domain neutrality

The same M03 core must represent at minimum:
1. logo/brand/web visual production;
2. 2D/image/product photography production;
3. Nerim/isometric 3D/game asset production;
4. film/commercial/multi-shot video production;
5. persistent corporate spokesperson/digital-human production;
6. voice/narration/music/audio production.

No core schema may require pixel, mesh, camera, visual or text-to-image-only fields.

Domain-specific semantics enter through versioned opaque refs/extension registries.

## 7. S01 brief/intent contract

Implementation must support:
- stable CreativeBrief identity + immutable revisions;
- preserved original sources;
- typed Intent Statements;
- origin/authority/confidence/provenance;
- purpose/audience/outcome/deliverable/direction/reference/open-question semantics;
- Ambiguity Records with BLOCKING/QUALITY_CRITICAL/COST_CRITICAL/NON_BLOCKING/CREATIVE_FREEDOM consequence;
- Freedom Zones;
- multilingual source anchors;
- semantic fingerprint/equivalence;
- Minimum Sufficient Intent slices.

Hidden semantic promotion is forbidden.

## 8. S02 constraint contract

Implementation must support:
- polarity: REQUIRE/FORBID/PREFER/AVOID/ALLOW;
- strength: HARD/GUARDED/SOFT/ADVISORY/EXPERIMENTAL;
- typed predicates without arbitrary code;
- scope + condition;
- typed tolerance with units/metric semantics;
- faceted anti-references;
- protected semantic zones/anchors;
- cross-modal constraints;
- immutable/versioned bundles;
- deterministic Constraint Normal Form;
- coverage state;
- Minimum Sufficient Constraint slices;
- constraint fingerprints/deltas;
- Semantic Admission Shield.

S05 owns authority/override resolution over normalized rules.

## 9. S03 M01 Fidelity compilation contract

Implementation must:
- compile from admitted M03 semantics into a non-authoritative `FidelityContractSpec`;
- select only admitted/versioned M01 DomainProfiles/registries;
- map mandatory quality obligations only to admitted M01 dimensions;
- preserve profile-owned defect/hard-gate/promotion semantics;
- source evaluator_set only through M01-authorized profile/registry mechanisms;
- support one brief -> multiple subject-specific FidelityContract outputs;
- round-trip emitted M01 contracts through current M01 validation/serialization before admission;
- produce Fidelity Compilation Gaps rather than drop unrepresentable obligations;
- emit Quality Obligation Traces and fingerprints/deltas;
- never downgrade QualityClass to fit hardware/provider availability.

No M01 DecisionEngine/evaluator/debt logic is reimplemented.

## 10. S04 Execution Intent contract

Implementation must support:
- immutable ExecutionIntentBundle;
- provider-neutral IntentOperation families:
  CREATE, TRANSFORM, COMPOSE, EXTEND, REPAIR, VARIATE, SELECT, VALIDATE, PACKAGE, LOCALIZE;
- CapabilityDemand;
- SemanticMutationEnvelope;
- semantic loss classes:
  LOSSLESS_REQUIRED, BOUNDED_APPROXIMATION, CREATIVE_FREEDOM, ADVISORY;
- Provider Translation Receipt contract/interface;
- Execution Intent Gaps;
- Minimum Sufficient Execution slices;
- Intent Explanation Graph and projections;
- fingerprints/deltas.

It must contain no mandatory provider/model/DCC/host/queue implementation dependency.

## 11. S05 conflict / override / versioning contract

Implementation must support:
- typed SemanticConflict objects;
- explicit consequence classes;
- versioned AuthorityPolicyGraph;
- immutable OverrideReceipt;
- strengthening/narrow/replace/relax/disable/temporary/restore actions;
- temporary override expiry/review;
- OverrideDebt separate from QualityDebt;
- scope split / exploration fork;
- minimal clarification ranking;
- semantic three-way merge analysis consumed by M02 merge flow;
- revision classifications;
- MigrationReceipt;
- RestorationRevision;
- BriefFreshnessVector;
- DerivedIntentDependency;
- Minimum Sufficient Conflict slices;
- release-readiness evidence.

No last-writer-wins behavior is allowed.

## 12. Required extension / opaque-ref boundaries

M03 must provide versioned provider-neutral refs/interfaces for:
1. M02 Project/Production/Branch/Variant refs;
2. SemanticType / IR schema refs for M04;
3. IdentityAnchor / DNA policy refs;
4. M01 DomainProfile / DimensionRegistry / evaluator-capability resolution;
5. CapabilityDemand / ProviderTranslationReceipt;
6. Canon/Story refs;
7. ContextSource / DerivedIntentDependency refs;
8. Provenance/Rights/Consent policy refs;
9. Security/authority policy refs;
10. Destination/Delivery profile refs;
11. explanation/provenance export;
12. domain semantic-path/predicate extension registry.

No real provider implementation is required in M03.

## 13. Serialization / persistence boundary

M03 may implement:
- deterministic immutable value objects;
- canonical serialization;
- schema/version guards;
- content/semantic fingerprints;
- in-memory/reference registries/stores for tests.

Production persistence/CAS/database belongs to M06/M55.

No database vendor is frozen into M03.

## 14. Security / trust boundary

Implementation must fail closed when:
- source authority is forged/unknown where authority is mandatory;
- untrusted metadata attempts to create authoritative constraints;
- a provider/result attempts semantic mutation without governed revision;
- mandatory semantic extension/predicate is unknown;
- override authority is insufficient;
- a non-overridable policy is targeted by an ordinary override;
- stale derived semantics are used as current;
- compiler/schema/registry versions are incompatible.

Arbitrary eval/shell/network behavior is prohibited inside the semantic kernel.

## 15. Performance / token-economy requirements

Implementation must make these first-class:
- Minimum Sufficient Semantic Slice Fabric;
- semantic fingerprints/deltas;
- reuse passports/freshness;
- compact explanation projections;
- conflict-local context;
- no need to replay full conversation/project history for localized compilation;
- provider changes do not invalidate provider-neutral semantics when requirements are unchanged.

Optimization may never remove correctness-relevant context silently.

## 16. Explainability requirements

For every admitted normalized/compiled object the kernel must be able to answer:
- source(s);
- origin/authority;
- rationale/derivation;
- relevant semantic paths;
- dependencies;
- which downstream obligations consumed it;
- what would become stale if it changed.

Compact/HUMAN/AUDIT projections resolve to the same canonical facts.

## 17. Required behavior

At minimum:
- create/edit/serialize immutable brief revisions;
- normalize source intent without losing provenance;
- classify ambiguity/freedom;
- normalize/validate constraints;
- compute semantic fingerprints/deltas;
- produce minimum sufficient slices;
- detect conflicts deterministically;
- validate override authority/receipts;
- compile M01 FidelityContractSpecs and accepted contracts;
- create multi-contract sets;
- compile ExecutionIntentBundles;
- compute semantic-loss/provider-translation requirements;
- generate explanation graph/projections;
- detect staleness;
- semantic three-way merge analysis;
- migrate/restore through new revisions/receipts;
- semantic readiness report.

Heavy provider/media execution is out of scope.

## 18. Acceptance tests

At minimum, implementation must prove:

### Identity/revision/provenance
- rename/wording edits do not replace stable brief identity;
- admitted revision is immutable;
- raw source survives normalization;
- explicit/inferred/defaulted/derived origin round-trips;
- source authority cannot be forged by untrusted text.

### Ambiguity/freedom
- BLOCKING ambiguity stops completion;
- CREATIVE_FREEDOM does not become error/default;
- clarification ranking is deterministic for identical normalized inputs.

### Constraints
- polarity != strength;
- negative constraint remains first-class;
- anti-reference facets are selective;
- unknown mandatory predicate fails closed;
- units/tolerances normalize deterministically;
- inactive condition does not contaminate active slice/fingerprint;
- untrusted retrieved text cannot self-admit as authoritative rule.

### M01 bridge
- valid admitted profile produces real M01 FidelityContract accepted by current M01 serialization;
- unknown dimension blocks;
- missing evaluator capability blocks;
- M03 cannot grant evaluator authority;
- hard-gate/FATAL semantics cannot be weakened;
- human-review requirement creates obligation but no fabricated evidence;
- hardware/provider scarcity cannot lower requested QualityClass;
- multimodal brief can produce multiple domain-separated contracts.

### Execution intent
- canonical bundle is provider-order-independent;
- provider/model/host changes do not alter semantic fingerprint;
- mandatory missing capability creates gap;
- LOSSLESS_REQUIRED unsupported translation blocks;
- mutation envelope preserves protected anchors;
- provider prompt cannot create canonical intent;
- provider result cannot mutate semantic state directly.

### Conflicts/overrides/versioning
- direct contradiction detected;
- disjoint scopes do not falsely conflict;
- last timestamp cannot resolve;
- confidence cannot override authority;
- unauthorized relaxation fails closed;
- temporary override expires/stales dependents;
- OverrideDebt is not M01 QualityDebt;
- three-way merge detects divergent same-path edits;
- restoration/migration create new revisions.

### Token/reuse/explainability
- consumer slices exclude unrelated semantics;
- semantic-equivalent source-only edit can preserve safe reuse;
- explanation trace reaches source/policy for every compiled obligation;
- stale dependency invalidates only affected derived semantics where possible.

### Domain neutrality
Run the same core with synthetic fixtures for the six domains in §6 with no domain-specific code imported into the M03 kernel.

## 19. Out of scope for M03 implementation

- media generation;
- pixel/CV inference;
- Blender/ComfyUI/Maya/provider execution;
- real worker/process scheduling;
- hardware discovery/resource placement;
- model routing/training/download;
- Scene/Asset/Camera/Material IR implementation;
- Asset/Persona/Voice/Music/Brand DNA implementation;
- narrative Canon engine;
- real image/video/3D/audio evaluators;
- HIVE retrieval implementation;
- universal media provenance/C2PA;
- security/RBAC engine;
- storage/CAS/database;
- actual publishing/export APIs;
- M04+ domain implementation.

## 20. Evidence obligations for executor

The later implementation Work Order must record:
- exact base/head SHA;
- changed files;
- frozen contract version;
- public API/concept mapping;
- full tests/lint/typecheck/compile results;
- deterministic serialization/fingerprint evidence;
- M01 FidelityContract integration evidence;
- M02 authority-boundary evidence;
- six-domain neutrality evidence;
- security/source-authority tests;
- token/slice/reuse tests;
- proof no provider/DCC/cloud/database SDK leaked into semantic core;
- risks/deferred ports;
- Evidence Bundle + proposed Checkpoint Delta.

## 21. STOP CONDITION for implementation Work Order

STOP after the complete M03 provider-neutral semantic kernel is implemented, tested, documented, evidence-bundled, committed/pushed and ready for independent review.

DO NOT merge on executor word.
DO NOT start M04 implementation.
DO NOT implement future provider/domain systems merely to satisfy extension interfaces.
If implementation requires weakening any frozen invariant, report `BLOCKED_CONTRACT_CONFLICT` instead.

## 22. Planning freeze evidence required before v1.0 approval

Before changing this candidate to `FROZEN_APPROVED / m03-contract-v1.0`, the planning PR must prove:
- S01-S05 complete;
- Final Technology Review approved;
- M04-M60 Forward Compatibility `PASS_WITH_EXTENSION_PORTS`;
- exact-head Governance PASS;
- existing repository tests green;
- planning-only diff (no M03 product implementation);
- independent planning audit APPROVED;
- zero HIGH/CRITICAL planning blockers.

Any semantic change after v1.0 freeze requires a versioned contract amendment plus renewed compatibility review.


## 23. Freeze evidence

- S01-S05 planning: complete.
- Final Technology Review: `APPROVED_FOR_FORWARD_COMPATIBILITY`.
- Consolidated frozen families: `F-M03-01..16`.
- Research-only / excluded from frozen core: `ICX-014`, `ICX-034`.
- Forward Compatibility Scan: `PASS_WITH_EXTENSION_PORTS` across M04-M60.
- Independent planning audit verdict: `APPROVED`.
- Independently reviewed head: `0c7098a4dfdd3db6e917da4378b5952061ce3fcd`.
- Exact-head Governance: run `35607101679`, job `106356761740`, PASS.
- Exact-head assertion: expected = checked out = `0c7098a4dfdd3db6e917da4378b5952061ce3fcd`.
- Governance required artifacts: 35.
- Existing repository suite: `1805/1805 OK`.
- Planning diff: planning/docs/checkpoint files only; no M03 product/kernel implementation.
- HIGH/CRITICAL planning blockers at approval: `0`.
- M01 quality authority preserved.
- M02 project/graph/build/release authority preserved.
- M04-M60 provider/domain ownership boundaries preserved.
- Review finding: one stale planning-status sentence was `CHAT_FIXABLE` and corrected on the same PR before approval.

Any semantic change after this freeze requires a versioned M03 contract amendment plus renewed compatibility and independent review.
