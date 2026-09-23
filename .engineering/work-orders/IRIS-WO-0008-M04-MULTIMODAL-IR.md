# IRIS-WO-0008 — Implement M04 Multimodal IR / Scene IR

Status: `ADMITTED_FOR_EXECUTION`
Risk: `ELEVATED`
Issue: `#30`
Branch: `iris-wo-0008-m04-multimodal-ir-r2`
Authorized base: `58e4201f1d76d261e9e213b7aab91ae8734188a5`
Frozen contract: `m04-contract-v1.0`
Implementation package: `iris_multimodal_ir/`

## OBJECTIVE

Implement the complete frozen M04 provider-neutral, runtime-neutral Multimodal IR / Scene IR semantic kernel as `iris_multimodal_ir/`.

The implementation MUST satisfy all 20 frozen technology families, all 80 hard invariants and all acceptance families in:
`planning/contracts/M04-MODULE-CONTRACT-FREEZE-CANDIDATE.md`.

This is a complete M04 implementation increment, not an MVP slice.

## CONTEXT

M01, M02 and M03 are implemented, independently reviewed, merged and exact-main validated. M04 S01-S05 planning, Final Technology Review, M05-M60 Forward Compatibility Scan, contract freeze and independent planning audit are complete.

The authorized base `58e4201f1d76d261e9e213b7aab91ae8734188a5` passed post-merge Governance `35803397206 / 106998641283` with **2527/2527 tests OK** and 35 required governance artifacts.

M04 is the canonical representation of structured production meaning. It is not raw creative intent, project/build history, a provider workflow, a DCC file model, an ExecutionPlan, a quality judge, persistence backend, or persistent identity/Canon authority.

## FILES / SOURCES TO READ

Read in this order and treat higher sources as authoritative:

1. `docs/project-brain/13-CHECKPOINT.md`
2. `docs/project-brain/16-DECISIONS-LEDGER.md`
3. `docs/project-brain/03-SCOPE.md`
4. `docs/project-brain/15-DEFINITION-OF-DONE.md`
5. `docs/project-brain/04-ARCHITECTURE.md`
6. `docs/project-brain/02-REQUIREMENTS.md`
7. `.engineering/SOURCE-HIERARCHY.md`
8. `.engineering/REVIEW-AUTOFIX-POLICY.md`\n9. `.engineering/PROMPT-DELIVERY-POLICY.md`
10. `planning/contracts/M04-MODULE-CONTRACT-FREEZE-CANDIDATE.md`
11. `planning/modules/M04-MULTIMODAL-SCENE-IR.md`
12. `planning/reviews/M04-FINAL-TECHNOLOGY-REVIEW.md`
13. `planning/compatibility/M04-FORWARD-COMPATIBILITY-SCAN.md`
14. `planning/technology-registry/M04-TECHNOLOGIES.md`
15. public/stable M01 interfaces actually consumed;
16. public/stable M02 refs/ports actually consumed;
17. public/stable M03 interfaces actually consumed.

Git/code/tests/evidence outrank conversation memory.

## PREFLIGHT

Before modifying implementation files:

- inspect repository structure and current package conventions;
- run `git status --short`; preserve unrelated user work;
- verify `origin` is `KayzenRoot/iris`;
- `git fetch origin --prune`;
- checkout/update only `iris-wo-0008-m04-multimodal-ir-r2`;
- verify `origin/main == 58e4201f1d76d261e9e213b7aab91ae8734188a5`;
- verify merge-base with `origin/main` is exactly the authorized base;
- verify every critical source SHA in `.engineering/context-locks/IRIS-WO-0008.json`;
- verify the implementation PR targets `main`;
- run `python scripts/validate_governance.py`;
- run the full baseline suite before implementation;
- STOP `STALE_CONTEXT` if main or a critical source moved before execution begins;
- do not force-push, reset shared history or rewrite commits.

## SCOPE

### S01 — Semantic Multimodal IR Core
Implement:
- MultimodalIRDocument, IRRevision, IRDocumentEnvelope;
- stable IRNodeRef and semantic identities independent of names/paths;
- SceneIR, EntityIR, AssetIR, CharacterIR, GeometryIR, CollectionIR;
- IRFragment, PrototypeIR, InstanceIR;
- strict acyclic containment/transform graph;
- separately typed semantic relationship graph with edge-family cycle policy;
- immutable revisions/fragments/prototypes;
- explicit deterministic composition arcs and precedence;
- IRInterfaceCapsule and deferred typed ResourceRef payload boundary;
- SkeletonIR, JointIR, SkinBindingIR, MorphChannelIR, AttachmentPortIR;
- opaque/versioned IdentityAnchorRef / AssetDNARef / PersonaDNARef boundaries;
- source M03 refs, M01 quality-obligation refs and provenance/policy refs.

### S02 — Spatial / Camera / Lighting / Material / Color
Implement:
- QuantityIR with explicit dimension/unit semantics;
- SpatialReferenceIR and CoordinateFrameIR;
- authored TransformChainIR distinct from derived ResolvedTransform;
- deterministic spatial conversion receipts;
- CameraIR / CameraOpticsIR including projection, filmback, focal/focus/DOF/framing semantics;
- LightIR, LightShapingIR, ShadowIntentIR, LightInfluenceIR;
- physical vs artistic/non-physical classification;
- MaterialIR / MaterialGraphIR with typed ports/connections/terminals;
- MaterialBindingIR / TextureResourceIR;
- ColorValueIR, ColorPipelineRef, ColorConversionReceipt;
- preview/final separation and explicit approximation evidence;
- extension/gap behavior for nonlinear/calibrated/spectral concepts.

### S03 — Temporal / Motion / Audio / Music / Narrative
Implement:
- exact rational TemporalReferenceIR;
- TimePointIR / TimeRangeIR / DurationIR;
- semantic/authored/sampled/editorial temporal layer separation;
- MotionIR / MotionChannelIR / AnimationCurveIR / MotionClipIR / MotionLayerIR;
- TemporalSamplingIR / markers / relations;
- temporal conversion and bake receipts;
- AudioIR / AudioSpatialIR / AudioClipBindingIR with external media refs;
- opaque VoiceIdentityRef / PersonaRef / SpeakerRef;
- MusicIR / MusicEventIR independent of MIDI/DAW identity;
- NarrativeProjectionIR / NarrativeCueIR with Canon firewall;
- TimelineIR / ShotRepresentationIR / SequenceRepresentationIR;
- SyncRelationIR with fail-closed tolerance semantics.

### S04 — Representation Capability & Semantic Lowering
Implement:
- RepresentationCapabilityManifest;
- REQUIRED vs optional/opaque capability distinction;
- TargetRepresentationProfile;
- deterministic SemanticLegalityReport with exact/bounded/unsupported/unknown states;
- SemanticLoweringReceipt;
- declarative SemanticLoweringPlan / SemanticLoweringRule;
- AdaptationProposal / RepresentationGap;
- IRTranslationReceipt;
- SemanticCapabilityDebt distinct from M01 QualityDebt;
- LoweringBundlePlan for multi-target semantic planning;
- explicit loss/tolerance authorization;
- no canonical mutation on target/provider scarcity;
- no provider workflow graph/model selection/runtime queue plan.

M16 remains the sole concrete provider/workflow compiler owner.

### S05 — Validation / Versioning / Migration / Round Trip
Implement:
- SchemaFamilyRef / SchemaManifest / FacetRef / DialectRef;
- explicit core/facet/dialect/transport/validator/lowering versions;
- deterministic canonical serialization and finite-number-safe hash material;
- strict unknown mandatory schema/facet/extension behavior;
- optional opaque preservation only under explicit policy;
- layered IR validation with typed deterministic findings;
- IRValidationProfile / IRValidationFinding;
- directional SchemaCompatibilityDeclaration;
- immutable IRMigrationPlan / IRMigrationReceipt creating new revisions;
- content/subgraph/interface/resource fingerprints/digests;
- deterministic adversarial complexity limits;
- dangling-ref, duplicate-ID and cycle checks;
- RoundTripContract / RoundTripReceipt;
- SemanticWitnessSet generated before adapter-result inspection;
- IREquivalenceProfile with exact/structural/semantic/tolerant/opaque/loss/one-way expectations;
- path-level unit/color/time-aware differences;
- anti-self-certification of adapter/provider equivalence;
- IRReleaseReadinessReport as evidence only.

### Context efficiency
Implement measurable:
- MinimumSufficientIRSlice;
- MinimumSufficientTemporalSlice;
- CapabilitySlice;
- IRStructuralFingerprint;
- IRSubgraphFingerprint;
- IRInterfaceFingerprint;
- IRSemanticDelta;
- locality-preserving invalidation;
- interface-only inspection without loading heavy payload;
- provider-neutral stability when provider changes but semantics do not.

No arbitrary token-saving percentage may be claimed without benchmark evidence.

## OUT OF SCOPE

- M05 Asset/Persona DNA content/drift implementation;
- M06/M55 persistence, database, CAS or storage-location backend;
- M16 concrete provider/workflow compiler;
- provider/model selection, prompts, workflow nodes or provider qualification runtime;
- Blender/Maya/ComfyUI execution;
- USD/glTF/MaterialX/OCIO/OTIO/MIDI SDK/runtime dependency merely to express canonical semantics;
- GPU/VRAM/worker scheduling;
- image/video/3D/audio generation;
- rig-control/auto-rig or motion generation/retargeting;
- renderer selection/render execution;
- material baking/texture generation;
- voice/music/audio generation/mix/master;
- story/Canon engine;
- video editing/compositing/encoding;
- real M01/M48 quality judges;
- rights/security engines;
- HIVE retrieval implementation;
- publishing/export/delivery execution;
- M05 or any later module implementation.

## ARCHITECTURE RULES

### Package
Implement as `iris_multimodal_ir/`.

Prefer focused modules over a monolith. Exact filenames may adapt after repository inspection, but the public architecture SHOULD separate concepts such as:
- errors / versions / limits;
- identity / refs / provenance;
- schema / facets / extensions;
- resources / envelopes;
- graph / composition / prototypes;
- character / deformation;
- spatial / camera / lighting;
- materials / color;
- temporal / motion;
- audio / music / narrative / timeline;
- lowering / capability / legality;
- validation / compatibility / migration;
- roundtrip / witnesses / equivalence;
- slicing / fingerprints / deltas;
- serialization;
- ports;
- readiness.

### Dependency boundary
M04 core may depend only on:
- Python standard library;
- stable public M01 interfaces;
- stable public M03 interfaces;
- opaque/versioned M02 refs or stable public M02 interfaces where required.

No new runtime dependency may be added merely for convenience.

If a new dependency is genuinely required, STOP `BLOCKED_DEPENDENCY_DECISION`.

### Authority law
- M01 is sole quality/evaluator/promotion/QualityDebt authority.
- M02 is sole project/branch/build/ExecutionPlan/release authority.
- M03 is sole canonical Creative Brief/intent/constraint/override authority.
- M04 is sole provider-neutral structured production representation authority.
- M05 owns persistent Asset/Persona DNA contents and drift policy.
- M06/M55 own persistence/storage locations.
- M16 solely owns concrete provider/workflow compilation.
- M28/M31/M36/M38/M40-M43/M48 retain their frozen domain-operation authorities.
- HIVE/agents may propose/derive context but cannot directly mutate canonical M04 truth.

### Closed runtime
The semantic kernel MUST NOT perform:
- network access;
- shell/external process execution;
- database/storage backend I/O;
- provider/DCC/GPU runtime execution;
- arbitrary dynamic code evaluation.

No `eval` or executable schema rules.

## REQUIREMENTS

- preserve all 80 frozen hard invariants;
- map every public frozen concept family to an implemented public semantic type or documented exact equivalent;
- deterministic canonical bytes/digest for same semantic input/profile/version;
- reject NaN/Infinity and malformed/ambiguous canonical numeric input;
- names/paths/locations are never canonical identity;
- duplicate canonical IDs reject;
- transform/containment cycles reject;
- semantic relationship cycles follow typed registered policy;
- unknown mandatory schema/facet/capability fails closed;
- admitted revisions/prototypes/migrations remain immutable;
- no last-writer/timestamp-wins composition;
- mandatory M03 semantics cannot silently disappear;
- LOSSLESS_REQUIRED unrepresentable semantics block;
- bounded approximation requires explicit upstream authorization;
- scarcity cannot lower M01 QualityClass or weaken protected M03 constraints;
- provider observations remain evidence, never canonical mutation authority;
- M04 lowering is provider-neutral and cannot contain concrete provider workflow detail;
- readiness/equivalence cannot self-authorize quality/release/promotion.

## DOMAIN-NEUTRAL SYNTHETIC PROFILES

Use the same M04 core without domain-specific branches for at least:

1. logo / brand / web visual scene;
2. product / image photography setup;
3. Nerim / isometric 3D game asset + scene;
4. film / commercial multi-shot sequence;
5. persistent corporate spokesperson / digital-human representation;
6. voice / narration / music / audio production;
7. mixed multimodal scene combining visual + motion + audio + narrative bindings.

The shared runner/fixture layer MUST prove that no profile identifier changes kernel behavior through bespoke branches.

## ACCEPTANCE CRITERIA

Implementation is acceptable only when:

1. all 20 F-M04 families are represented;
2. all 80 hard invariants have direct tests or deterministic proof;
3. all §22 frozen acceptance families are covered;
4. every public canonical kind round-trips through deterministic serialization;
5. seven synthetic domains use one kernel;
6. M01/M02/M03/M16 authority boundaries have regression/static tests;
7. no provider/DCC/cloud/database/network/shell dependency leaks into kernel;
8. minimum-sufficient slices and localized fingerprints/deltas are measurable;
9. migration always produces a new immutable revision/receipt;
10. round-trip witness sets predate inspected adapter results;
11. semantic loss in transform/camera/material/time/sync paths is detected;
12. invalid/hostile structures fail deterministically under explicit limits;
13. public `__all__` surface is intentional and tested;
14. full repository suite remains green with no existing test deleted/disabled to hide regressions;
15. docs and Evidence Bundle reflect only verified behavior.

## TESTS

At minimum add focused `test_m04_*.py` suites covering:

- identity / refs / revisions / envelopes;
- graph / relationships / composition / prototypes / instances;
- resources / interface-payload boundary;
- character / skeleton / skin / morph;
- spatial / units / transforms;
- camera / lighting;
- material / texture / color;
- temporal / motion;
- audio / music / narrative / timeline / sync;
- lowering / capability / legality / loss / debt;
- validation / schema / compatibility / migration;
- serialization / canonical numeric rules / digests;
- round trip / witnesses / equivalence / anti-self-certification;
- slices / fingerprints / deltas / resource limits;
- domain neutrality / import-boundary scans.

Required execution:
- focused compile of all new M04 modules/tests/examples;
- `python scripts/validate_governance.py`;
- `python -m unittest discover -s tests -p "test_m04_*.py"`;
- `python -m unittest discover -s tests -p "test_*.py"`;
- configured linter/static checks when already available;
- deterministic static/import scan for forbidden provider/DCC/network/shell/database dependencies;
- run the seven-domain example/fixture harness;
- exact-head GitHub Governance.

Baseline floor is **2527 tests**. New M04 tests MUST increase that total. Existing tests may not be deleted, skipped or weakened merely to reach green.

## DOCUMENTATION

Add:
- `docs/M04-MULTIMODAL-IR-KERNEL.md`;
- public API / concept mapping;
- M01/M02/M03/M16 authority-boundary explanation;
- schema/serialization/versioning/migration notes;
- round-trip/equivalence model;
- seven domain examples;
- deferred extension ports;
- known limitations and risks;
- no unsupported quality/performance/token claims.

## DELIVERABLES

- complete `iris_multimodal_ir/` kernel;
- focused `tests/test_m04_*.py` suites and support fixtures;
- seven-domain example harness under `examples/`;
- `docs/M04-MULTIMODAL-IR-KERNEL.md`;
- updated `.engineering/evidence/IRIS-WO-0008.json`;
- proposed Checkpoint Delta, not executor-promoted as canonical truth;
- implementation commits pushed to this same branch;
- same PR linked to Issue #30;
- exact-head Governance evidence.

## EVIDENCE BUNDLE

Record truthfully:
- authorized base and tested/reviewed head chain;
- issue/PR number, URL and state;
- exact changed files/counts;
- package/module/public API shape;
- frozen-concept mapping;
- dependency/import surface;
- schema/serialization/version set;
- tests by family + focused/full totals;
- compile/lint/governance results;
- failures encountered and corrected;
- proof M01 QualityClass/quality authority is untouched;
- proof M02 history/build/release/ExecutionPlan authority is not duplicated;
- proof M03 mandatory/protected semantics are not weakened;
- proof M16 concrete provider compiler is not implemented;
- seven-domain neutrality evidence;
- slices/fingerprints/deltas evidence;
- migration/round-trip evidence;
- adversarial/security/resource-limit evidence;
- no-provider/no-DCC/no-network/no-shell evidence;
- deferred extension ports;
- risks;
- proposed Checkpoint Delta;
- STOP CONDITION.

Do not make the Evidence Bundle self-referentially claim its own commit SHA. Use a documented head chain and exact-head CI.

## REVIEW FORMAT

Return final executor review in Brazilian Portuguese with:
- architecture implemented;
- files/package/public surface;
- frozen-family and invariant coverage;
- exact tests/results;
- M01/M02/M03/M16 boundary proof;
- seven-domain fixtures;
- serialization/migration/round-trip proof;
- security/resource-limit/context-efficiency proof;
- failures corrected;
- deviations/risks;
- commit/head;
- PR;
- Evidence Bundle;
- proposed Checkpoint Delta;
- STOP CONDITION.

## RECOMPILE NOTE

The previous admission on PR #31 is superseded because repository-canonical prompt/review policy changed on main via PR #33. This Work Order is recompiled against the new validated main and requires a fresh Context Lock + exact-head Governance before execution.

Complete executor prompts for this Work Order MUST be delivered to the user as a downloadable PDF under `.engineering/PROMPT-DELIVERY-POLICY.md`.

## STOP CONDITION


STOP only when:
- the complete frozen M04 kernel is implemented;
- all frozen acceptance families and 80 invariants are tested/proven;
- docs and Evidence Bundle are complete;
- branch is pushed;
- the same PR is ready for independent review;
- exact-head Governance is green or deterministically pending and subsequently recorded;
- no frozen invariant or upstream authority was weakened.

DO NOT MERGE.
DO NOT START M05.
DO NOT implement provider/DCC/domain runtimes merely to satisfy extension ports.
DO NOT lower QualityClass or mandatory M03 semantics to fit target scarcity.
If the frozen contract cannot be satisfied without semantic change, STOP `BLOCKED_CONTRACT_CONFLICT`.
