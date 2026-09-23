# M04 Module Contract Freeze Candidate — Multimodal IR / Scene IR

Status: `FROZEN_APPROVED`
Frozen version: `m04-contract-v1.0`
Module: `M04`
Issue: `#26`
Authorized baseline: `c231dd61a210fe6d315126e755b4642a4fd2e9a3`

## 1. Mission

M04 owns the provider-neutral, runtime-neutral multimodal intermediate representation that materializes admitted M03 creative semantics into typed scene/media structures while preserving M01 quality obligations and M02 production authority.

M04 is the canonical representation of **structured production meaning**, not:
- raw user intent;
- a project/build graph;
- a provider workflow;
- a DCC file model;
- a runtime execution plan;
- a quality judge;
- a persistent identity/Canon authority.

## 2. Upstream authority

M04 consumes, but does not supersede:

- **M01**: Fidelity Contract, QualityClass, evaluator/judge/promotion/quality-debt authority.
- **M02**: project/production identity, graph, branches/variants/snapshots, build/reuse, ExecutionPlan, release/archive authority.
- **M03**: Creative Brief, intent, constraints, ambiguity/freedom, semantic overrides, provider-neutral execution intent and semantic-loss classes.

Canonical source priority remains repository/checkpoint/decisions/scope/DoD/architecture/requirements.

## 3. Public frozen concept families

Implementation class names may adapt, but these semantics MUST exist.

### Document / identity / schema
- MultimodalIRDocument
- IRRevision
- IRDocumentEnvelope
- IRNodeRef
- SchemaFamilyRef
- SchemaManifest
- FacetRef / DialectRef
- RepresentationCapabilityManifest

### Core graph
- SceneIR
- EntityIR
- AssetIR
- CharacterIR
- GeometryIR
- CollectionIR
- PrototypeIR
- InstanceIR
- IRFragment
- SemanticRelationship
- CompositionArc
- ResourceRef
- IRInterfaceCapsule

### Character / deformation
- SkeletonIR
- JointIR
- SkinBindingIR
- MorphChannelIR
- AttachmentPortIR
- IdentityAnchorRef / AssetDNARef / PersonaDNARef

### Spatial / camera / lighting
- SpatialReferenceIR
- QuantityIR
- CoordinateFrameIR
- TransformChainIR
- ResolvedTransform
- CameraIR / CameraOpticsIR
- LightIR
- LightShapingIR
- ShadowIntentIR
- LightInfluenceIR
- SpatialRegionIR

### Material / color
- MaterialIR
- MaterialGraphIR
- MaterialBindingIR
- TextureResourceIR
- ColorValueIR
- ColorPipelineRef
- ColorConversionReceipt

### Temporal / motion
- TemporalReferenceIR
- TimePointIR / TimeRangeIR / DurationIR
- MotionIR
- MotionChannelIR
- AnimationCurveIR
- MotionClipIR / MotionLayerIR
- TemporalSamplingIR
- TemporalMarkerIR / TemporalRelationIR

### Audio / music / narrative
- AudioIR
- AudioSpatialIR
- AudioClipBindingIR
- VoiceIdentityRef / PersonaRef / SpeakerRef
- MusicIR
- MusicEventIR
- NarrativeProjectionIR
- NarrativeCueIR
- TimelineIR
- ShotRepresentationIR / SequenceRepresentationIR
- SyncRelationIR

### Lowering / capability / loss
- SemanticLoweringReceipt
- TargetRepresentationProfile
- SemanticLegalityReport
- SemanticLoweringPlan
- SemanticLoweringRule
- AdaptationProposal
- RepresentationGap
- IRTranslationReceipt
- SemanticCapabilityDebt
- LoweringBundlePlan

### Validation / version / round trip
- IRValidationProfile
- IRValidationFinding
- SchemaCompatibilityDeclaration
- IRMigrationPlan
- IRMigrationReceipt
- RoundTripContract
- RoundTripReceipt
- SemanticWitnessSet
- IREquivalenceProfile
- IRReleaseReadinessReport

### Context / fingerprints
- MinimumSufficientIRSlice
- MinimumSufficientTemporalSlice
- CapabilitySlice
- IRStructuralFingerprint
- IRSubgraphFingerprint
- IRInterfaceFingerprint
- IRSemanticDelta

## 4. Consolidated technology families

Frozen contract recognizes:

1. `F-M04-01 Semantic Multimodal IR Core`
2. `F-M04-02 Intent / Quality Trace Spine`
3. `F-M04-03 Interface / Payload / Resource Fabric`
4. `F-M04-04 Versioned Schema / Facet / Extension Fabric`
5. `F-M04-05 Character / Identity Anchor Bridge`
6. `F-M04-06 Composition / Prototype / Instance Integrity`
7. `F-M04-07 Gap / Delta / Slice / Canonical-Derived Fabric`
8. `F-M04-08 Unit-Safe Spatial & Transform Fabric`
9. `F-M04-09 Physical Camera & Projection Fabric`
10. `F-M04-10 Lighting Semantic Fabric`
11. `F-M04-11 Material / Texture / Color Integrity Fabric`
12. `F-M04-12 Temporal / Motion Representation Fabric`
13. `F-M04-13 Audio / Voice Representation Fabric`
14. `F-M04-14 Music Structural Representation Fabric`
15. `F-M04-15 Narrative / Timeline / Sync Projection Fabric`
16. `F-M04-16 Representation Capability & Legality Fabric`
17. `F-M04-17 Semantic Lowering & Compiler Boundary Fabric`
18. `F-M04-18 Multi-Target / Capability Debt Fabric`
19. `F-M04-19 Canonical Envelope / Validation / Schema Evolution Fabric`
20. `F-M04-20 Semantic Round-Trip & Readiness Proof Fabric`

Detailed `IRIS-MIRX-001..150` are non-normative design history.

## 5. Hard invariants

1. canonical M04 IR is IRIS-owned, provider-neutral and runtime-neutral;
2. provider/DCC/workflow/runtime identifiers are not canonical core identity;
3. M04 canonical node identity is independent of display name/path;
4. admitted IR revisions are immutable;
5. M02 remains authority for branch/variant/build/history/release topology;
6. M04 revision identity cannot create a competing VCS/build system;
7. containment/transform topology is distinct from semantic relationship topology;
8. transform/containment graph is acyclic;
9. relationship-cycle legality is edge-family-specific;
10. every correctness-relevant canonical IR fact traces to admitted M03 semantics or an admitted explicit policy/default;
11. inferred/provider observations cannot self-promote into canonical truth;
12. M01 quality obligations are referenced, never reimplemented;
13. M04 cannot grant evaluator/judge/promotion capability;
14. M04 cannot lower M01 QualityClass for hardware/provider/cost scarcity;
15. M03 mandatory/protected constraints cannot be weakened by M04;
16. mandatory M03 semantics cannot silently disappear during lowering;
17. LOSSLESS_REQUIRED unrepresentable semantics block;
18. bounded approximation requires explicit upstream loss/tolerance authorization;
19. target/provider capability observations cannot mutate canonical IR;
20. M16 is sole owner of concrete provider/workflow compilation;
21. M04 semantic lowering plans contain no provider workflow graph/model selection/runtime queue plan;
22. M05 owns persistent Asset/Persona DNA contents/drift policy;
23. M04 DNA/identity values are opaque refs/application points only;
24. M06/M55 own persistence/CAS/storage locations;
25. resource location/path/URL is not resource identity;
26. heavy geometry/media/cache payloads may be deferred behind typed ResourceRefs;
27. interface capsules remain interpretable without loading heavy payloads;
28. prototypes are immutable through instances;
29. instance overrides are explicitly scoped and cannot mutate prototypes;
30. composition precedence is explicit; last-writer/timestamp-wins is forbidden;
31. unknown mandatory schema/facet/extension fails closed;
32. optional unknown extensions remain opaque only under explicit preservation policy;
33. schema family and version are explicit for canonical extensions;
34. transport encoding version is distinct from semantic schema versions;
35. "latest schema" does not imply compatibility;
36. migrations never rewrite old admitted revisions in place;
37. migrations produce new revisions and immutable receipts;
38. canonical serialization is deterministic for a declared profile/version;
39. canonical hash material rejects non-finite numeric ambiguity;
40. duplicate canonical IDs/keys are rejected;
41. authored and derived transform data are distinct facts;
42. all correctness-relevant spatial quantities use explicit unit/reference semantics;
43. coordinate conversion requires deterministic source/target semantics and receipt;
44. camera physical semantics are provider-neutral;
45. unsupported nonlinear/specialized projection becomes extension/gap, never silent perspective coercion;
46. correctness-critical light quantity is typed/identified, not an unlabelled scalar;
47. artistic non-physical controls are explicitly classified;
48. MaterialIR is target-neutral and typed;
49. arbitrary executable shader/provider source is not canonical MaterialGraphIR;
50. color values requiring interpretation carry color-space/encoding semantics;
51. preview representation cannot silently satisfy final obligations;
52. canonical time basis is explicit and independent of display frame numbering;
53. semantic/authored/sampled/editorial time layers are distinct;
54. motion channels target typed semantic paths, not arbitrary executable/path strings;
55. M29/M30 own rig/motion production; M04 owns portable representation only;
56. audio/media bytes remain external resources;
57. M40/M42 own voice/audio production and post;
58. MIDI/DAW protocol identity is not canonical MusicIR identity;
59. M41 owns composition/Music DNA/mix-master;
60. NarrativeProjectionIR/local cues cannot become M43 Canon truth;
61. M43 owns story/canon/world-state authority;
62. TimelineIR is portable representation, not editorial authority;
63. M36/M38 own shot planning/editing/assembly operations;
64. mandatory sync relations cannot silently drift outside tolerance;
65. temporal resampling/baking/conversion produces explicit receipts/loss evidence;
66. required vs optional representation capabilities cannot be relabelled downstream;
67. semantic legality analysis is read-only against canonical source IR;
68. target profiles are semantic/versioned, not vendor identities;
69. provider observations are evidence, not capability promotion authority;
70. SemanticCapabilityDebt is distinct from M01 QualityDebt and cannot waive gates;
71. derived/cache/provider-observation data cannot overwrite canonical authored/lowered facts;
72. round-trip success is semantic, not merely parse success;
73. adapters cannot self-certify semantic equivalence/qualification;
74. round-trip contracts state exact/tolerant/opaque/loss expectations;
75. witness sets are derived from canonical obligations before adapter result inspection;
76. validator findings are deterministic for same canonical input/profile/version;
77. deterministic resource/depth/fanout/sample limits are enforced;
78. validation failures are typed and fail closed where contract-critical;
79. IR release-readiness is evidence only and cannot replace M01/M02/M53/M54/M59 authority;
80. HIVE/agents/retrieval may propose or derive context but cannot mutate canonical M04 truth directly.

## 6. Ownership overlap freezes

### M28 Materials
M04 owns generic cross-domain MaterialIR/typed graph/color/resource/binding contracts.
M28 owns PBR channel standards, material/texture generation, baking, repair and material fidelity/QA.

### M31 Camera/Lighting/Rendering
M04 owns portable physical/semantic CameraIR/LightIR.
M31 owns production camera direction, lighting rigs/relighting, renderer choice, AOV/render behavior and render QA.

### M36/M38 Timeline/Color
M04 owns portable temporal/timeline/color identity representation.
M36 owns video/cinema shot planning/routing/assembly.
M38 owns editing, compositing, grading, encoding and delivery operations.

### M48 Quality
M04 carries M01 quality obligation refs and readiness evidence.
M01/M48 remain quality decision/judgment/promotion authority.

## 7. M03 → M04 lowering contract

Implementation must support:
- source M03 revision refs;
- per-statement/constraint/operation representation mapping;
- SemanticLoweringReceipt;
- lowering rule/version;
- representation state EXACT / BOUNDED / DEFERRED / EXTENSION_REQUIRED / BLOCKED;
- loss class/tolerance;
- gaps/remedies;
- explanation/provenance reachability;
- no silent drop of mandatory semantics.

M03 stays canonical intent truth.

## 8. Core scene / asset / character contract

Implementation must support:
- stable document/node/asset/character identities;
- dual graph topology;
- immutable scene fragments;
- explicit deterministic composition arcs;
- interface/payload split;
- ResourceRefs;
- prototypes/instances;
- typed attachment/binding ports;
- generic GeometryIR;
- CharacterIR with skeleton/joints/rest/bind/skin/morph semantics;
- identity/DNA refs without M05 ownership;
- gap/completeness state.

DCC control rigs are out of core.

## 9. Spatial / camera / lighting contract

Implementation must support:
- SpatialReferenceIR;
- units/dimensions;
- coordinate frames;
- authored TransformChainIR vs derived transform;
- deterministic conversions/receipts;
- camera projection/filmback/focal/focus/DOF/framing semantics;
- light emitter/emission/shaping/influence/shadow semantics;
- physical/non-physical classification;
- extension points for calibrated/nonlinear/spectral concepts.

Renderer-specific parameters are out of core.

## 10. Material / color contract

Implementation must support:
- typed MaterialGraphIR;
- typed ports/connections;
- surface/volume/displacement/emission terminals;
- MaterialBindingIR with subset/purpose;
- TextureResourceIR;
- color-space/encoding/alpha semantics;
- ColorPipelineRef / conversion receipt;
- preview/final separation;
- target-neutral extensions.

MaterialX/renderer shader source is adapter scope.

## 11. Temporal / motion contract

Implementation must support:
- exact TemporalReferenceIR;
- time points/ranges/durations/markers;
- authored vs sampled vs editorial time layers;
- typed MotionChannelIR;
- curves/keyed/sampled/clip refs;
- motion clips/layers;
- skeleton/morph temporal bindings;
- camera temporal sampling/shutter contract;
- temporal conversion/bake receipts.

Motion generation/retargeting remains M30.

## 12. Audio / music / narrative / timeline contract

Implementation must support:
- AudioIR roles and external media refs;
- channel/object/scene/binaural representation profiles;
- AudioClipBindingIR;
- Voice/Persona refs;
- MusicIR tempo/meter/sections/parts/event dialect;
- MIDI-independent canonical semantics;
- NarrativeProjectionIR/local bounded cues;
- Canon refs without Canon ownership;
- portable TimelineIR;
- shot/sequence representation;
- SyncRelationIR/tolerances;
- continuity dependency refs.

Audio/music/story/editorial engines remain later modules.

## 13. Representation capability / lowering contract

Implementation must support:
- RepresentationCapabilityManifest;
- REQUIRED vs optional/opaque capabilities;
- TargetRepresentationProfile;
- exact/bounded/unsupported/unknown support states;
- read-only SemanticLegalityReport;
- declarative SemanticLoweringPlan/Rule;
- AdaptationProposal;
- RepresentationGap;
- IRTranslationReceipt;
- SemanticCapabilityDebt;
- multi-target LoweringBundlePlan;
- no canonical mutation on capability failure.

M16 consumes this contract and implements concrete provider/workflow compilation.

## 14. Versioning / validation / migration contract

Implementation must support:
- IRDocumentEnvelope;
- multi-axis versions;
- canonical deterministic serialization;
- schema/facet manifest;
- layered validation;
- typed deterministic findings;
- validation profiles;
- directional SchemaCompatibilityDeclaration;
- explicit unknown-field policy;
- immutable migration plans/receipts;
- content/subgraph/interface/resource digests;
- adversarial resource limits;
- graph/ref integrity checks.

## 15. Round-trip contract

Implementation must support:
- RoundTripContract;
- RoundTripReceipt;
- SemanticWitnessSet;
- IREquivalenceProfile;
- exact/structural/semantic/tolerant/opaque/loss/one-way classes;
- adapter/profile/version binding;
- path-by-path differences;
- unit/color/time-aware comparisons;
- qualification evidence refs;
- no self-certification.

## 16. Required future extension / ref boundaries

M04 core must expose versioned provider-neutral boundaries sufficient for:

1. M05/M39/M46 identity/DNA refs;
2. M06/M55 persistence/CAS/resource location;
3. M07-M10 hardware/runtime capability evidence;
4. M10-M13 workload/performance demands;
5. M14/M15 model capability/routing evidence;
6. M16 concrete provider compiler contract;
7. M17+ provider runtime artifact refs;
8. M27/M28 geometry/material domain dialects;
9. M29 rig/deformation dialects;
10. M30 motion production;
11. M31/M32 render/camera/light/VFX dialects;
12. M26/M33-M35 DCC/web/game interchange;
13. M36-M38 editorial/continuity;
14. M39-M42 persona/voice/music/audio;
15. M43 Canon/story projections;
16. M44-M47 brand/localization/content projections;
17. M48/M51 quality/benchmark evidence;
18. M49/M50 repair/optimization proposals;
19. M52-M55 context/rights/security/storage;
20. M56-M60 observability/agents/API/export/deployment.

No future implementation is required inside M04 to satisfy these ports.

## 17. Serialization and dependency boundary

M04 core may depend on:
- Python standard library;
- stable public M01 interfaces;
- stable public M03 interfaces;
- opaque/versioned M02 refs or stable public interfaces where required.

M04 core MUST NOT require:
- Blender/Maya/ComfyUI SDKs;
- provider/model SDKs;
- database/storage SDKs;
- GPU/runtime SDKs;
- MaterialX/USD/glTF/OTIO/MIDI/OCIO libraries merely to represent canonical core semantics;
- network/shell/external process access.

Adapters belong later.

## 18. Security / trust boundary

Implementation must fail closed for:
- forged authority/provenance where mandatory;
- provider result direct canonical mutation;
- untrusted metadata self-registering a schema/facet;
- unknown mandatory schema/facet/extension;
- digest mismatch;
- duplicate IDs;
- illegal graph cycles;
- dangling mandatory refs;
- resource/path identity spoofing;
- stale identity/DNA refs where mandatory;
- invalid migration/round-trip receipt;
- forged adapter qualification;
- excessive graph/resource complexity;
- non-finite canonical numbers;
- lowering of mandatory constraints/quality semantics without authority.

No eval/arbitrary executable schema rules in canonical core.

## 19. Context / performance requirements

Implementation must make measurable:
- MinimumSufficientIRSlice;
- MinimumSufficientTemporalSlice;
- CapabilitySlice;
- interface-only inspection without heavy payload;
- localized subgraph fingerprints/deltas;
- locality-preserving invalidation;
- no full-project replay for localized operations;
- deterministic validation cost bounded by declared limits;
- provider changes do not invalidate canonical provider-neutral IR when semantics are unchanged.

No arbitrary percentage savings may be claimed without benchmark evidence.

## 20. Domain neutrality

The same core must support synthetic fixtures for at least:

1. logo/brand/web visual scene/asset;
2. product/image photography setup;
3. Nerim/isometric 3D game asset/scene;
4. film/commercial multi-shot sequence;
5. persistent corporate spokesperson/digital-human representation;
6. voice/narration/music/audio production;
7. mixed multimodal scene combining visual + motion + audio + narrative bindings.

Core must not require one domain's fields for all other domains.

## 21. Required behavior

At minimum:
- build/validate immutable IR documents/revisions;
- serialize/deserialize canonical envelopes deterministically;
- validate node/schema/facet/reference integrity;
- construct dual graph scene;
- compose fragments/prototypes/instances;
- create interface/payload resource boundaries;
- represent CharacterIR/skeleton/skin/morph semantics;
- represent spatial/camera/light/material/color semantics;
- represent temporal/motion/audio/music/narrative/timeline semantics;
- compile M03 lowering receipts and gaps;
- compute capability manifests/legality reports/lowering plans;
- create multi-target semantic plans;
- compute fingerprints/deltas/slices;
- migrate via new revisions/receipts;
- validate round trips through witness/equivalence contracts;
- produce IRReleaseReadinessReport.

Heavy media/provider execution is out of scope.

## 22. Acceptance tests

Later implementation must prove at minimum:

### Identity / graph / composition
- names/paths do not define identity;
- duplicate IDs reject;
- transform cycles reject;
- relationship cycle policy is typed;
- prototype immutable through instance;
- composition precedence deterministic;
- fragment/source refs round-trip.

### Trace / lowering
- every mandatory produced IR fact traces to M03 source/policy;
- mandatory M03 semantics cannot disappear;
- lossless unrepresentable blocks;
- bounded representation requires authorization;
- provider result cannot mutate canonical source.

### Character / resources
- skeleton hierarchy/skin/morph semantics round-trip;
- M05 refs remain opaque;
- interface-only asset works without payload;
- resource location changes do not change resource identity.

### Spatial / camera / lighting
- unit mismatch rejects;
- coordinate conversions deterministic;
- transform op order preserved;
- physical camera semantics round-trip;
- nonlinear projection cannot silently coerce;
- light quantity semantics typed;
- non-physical controls explicit.

### Material / color
- graph port/type validation;
- binding purpose/subset validation;
- color space/encoding preserved;
- untagged mandatory color fails according to policy;
- preview does not satisfy final by default.

### Temporal / motion
- rational time conversion deterministic;
- no hidden FPS;
- motion target type checks;
- curves/clips round-trip;
- dense payload can remain deferred;
- resample/bake losses recorded.

### Audio / music / narrative
- media bytes external;
- spatial audio frame-aware;
- MusicIR not dependent on MIDI;
- non-tonal/non-metered music representable;
- local narrative cue cannot self-promote to Canon;
- sync tolerance failure-closed;
- timeline nesting/ranges valid.

### Capability / compiler boundary
- required/optional cannot be forged;
- unknown mandatory capability blocks;
- legality analysis read-only;
- bounded support requires loss permission;
- M01 QualityClass unchanged under scarcity;
- M03 mandatory constraints unchanged;
- lowering plan has zero provider/DCC/workflow runtime specifics;
- M16 boundary static/import test.

### Version / validation / migration
- deterministic canonical bytes/digest;
- NaN/Infinity reject;
- duplicate map keys/IDs reject where applicable;
- explicit schema family/version;
- directional compatibility;
- migration leaves source immutable;
- stale/invalid migration receipt rejects;
- deterministic finding order;
- complexity limits deterministic.

### Round trip
- exact witness set generated before adapter result;
- transform/camera/material/time/sync loss detected;
- tolerant comparisons unit/color/time aware;
- opaque preservation digest verified;
- adapter cannot self-certify;
- readiness cannot claim quality/release promotion.

### Domain neutrality / closed runtime
- seven synthetic profiles use same core;
- no provider/DCC/cloud/database/network/shell requirement in kernel.

## 23. Out of scope for M04 implementation

- actual image/video/3D/audio generation;
- Blender/Maya/ComfyUI execution;
- provider/model selection;
- concrete workflow compilation;
- GPU/VRAM/runtime scheduling;
- storage/CAS backend;
- Asset/Persona DNA implementation;
- rig control systems/auto-rig;
- motion generation/retargeting;
- renderer selection/render execution;
- material baking/texture generation;
- voice/music/audio generation/mix/master;
- story/Canon engine;
- video editing/compositing/encoding;
- real quality judges;
- rights/security engines;
- HIVE retrieval implementation;
- publishing/export/delivery execution.

## 24. Evidence obligations for implementation executor

A later bounded implementation Work Order must record:
- exact base/head SHA and frozen contract version;
- public API/concept mapping;
- dependency/import surface;
- serialization schema/versions;
- full test counts/results;
- focused M04 tests by family;
- deterministic fingerprint/serialization evidence;
- M01/M02/M03 authority-boundary evidence;
- seven-domain neutrality evidence;
- closed-runtime/no provider SDK evidence;
- adversarial/security/resource-limit tests;
- context/slice/delta evidence;
- migration/round-trip evidence;
- failures fixed;
- deferred extension ports;
- Evidence Bundle and proposed Checkpoint Delta.

## 25. Implementation STOP CONDITION

STOP only when the complete frozen M04 provider-neutral semantic IR kernel is implemented, tested, documented, evidence-bundled, pushed and ready for independent review.

DO NOT MERGE on executor word.
DO NOT start M05 implementation.
DO NOT implement provider/DCC/domain runtimes merely to satisfy ports.
DO NOT weaken any frozen invariant.
If implementation requires semantic contract change, STOP `BLOCKED_CONTRACT_CONFLICT`.

## 26. Freeze evidence required before v1.0 approval

Before status becomes `FROZEN_APPROVED / m04-contract-v1.0`, planning PR must prove:

- S01-S05 complete;
- Final Technology Review `APPROVED_FOR_FORWARD_COMPATIBILITY`;
- consolidated families `F-M04-01..20`;
- M05-M60 Forward Compatibility `PASS_WITH_EXTENSION_PORTS`;
- M04/M16 concrete Provider Compiler conflict resolved;
- exact-head Governance PASS;
- full existing repository tests green;
- planning/docs/checkpoint-only diff;
- independent planning audit APPROVED;
- zero HIGH/CRITICAL planning blockers.

Any semantic change after freeze requires versioned M04 contract amendment + renewed compatibility review.


## 27. Freeze closure

- Contract: `m04-contract-v1.0`
- Status: `FROZEN_APPROVED`
- Independent planning audit: `APPROVED`
- Reviewed semantic/planning head: `86a75307c7e50b47702ed2fede74a92ca6ea5e5a`
- Governance: `35681272803 / 106598537403` — PASS
- Full suite: `2527/2527 OK`
- Planning findings: 4 CHAT_FIXABLE / all CLOSED
- HIGH/CRITICAL blockers: 0
- Product/kernel implementation: not started
- M16 concrete Provider Compiler boundary: preserved

The promotion/checkpoint commits that follow this audit are governance/documentation-only and must pass their own exact-head Governance before merge.
