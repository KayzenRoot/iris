# M04 Forward Compatibility Scan — M05 to M60

Status: `PASS_WITH_EXTENSION_PORTS`
Date: 2026-09-22
Module: `M04 — Multimodal IR / Scene IR`
Issue: `#26`

## Purpose

Check the completed M04 planning against known M05-M60 responsibilities without deep-planning future modules.

The scan asks:
- does M04 steal future ownership?
- does M04 need a versioned extension/ref boundary?
- would a frozen M04 concept block an obvious future requirement?
- can future modules extend M04 without rewriting its core authority model?

## Result summary

- Modules scanned: **M05-M60 (56 modules)**.
- Critical ownership conflicts remaining: **0**.
- Historical M04/M16 Provider Compiler conflict: **RESOLVED** by narrowing M04 S04 to Representation Capability & Semantic Lowering.
- Cross-module overlap warnings requiring explicit freeze text: **4** (M28, M31, M36/M38, M48); all resolved by extension/authority boundaries below.
- Required future extension/ref families: **20**.
- Verdict: `PASS_WITH_EXTENSION_PORTS`.

## Module-by-module scan

| Module | M04 interaction | Compatibility boundary / result |
| --- | --- | --- |
| M05 Asset DNA | M04 Character/Asset IR carries identity anchors | M05 owns DNA contents/drift/branching; opaque/versioned DNA refs only. PASS |
| M06 Production State/Versioning | M04 has immutable semantic IR revisions/digests | M02/M06 own project build/version/CAS/reconstruction; M04 does not create competing branch/build history. PASS |
| M07 Hardware Genome | target/runtime capabilities may consume M04 manifests | hardware facts never mutate canonical IR. PASS |
| M08 Microbenchmark | capability evidence may qualify target profiles | evidence refs only; M04 has no benchmark authority. PASS |
| M09 Resource Twin/VRAM | heavy payloads affect execution | M04 only resource semantics/refs; residency/offload belongs M09. PASS |
| M10 Execution Planner | plans consume M04 capability/resource needs | M04 lowering plan is not M02/M10 execution plan. PASS |
| M11 Worker Fabric | workers execute later compiled artifacts | zero worker/process semantics in canonical M04 core. PASS |
| M12 Compute Orchestration | distributed placement consumes workloads | no queue/GPU/LAN/cloud placement in M04. PASS |
| M13 Performance/Cache | fingerprints/slices support reuse | M13 owns cache/performance policy; correctness fingerprints remain stable input. PASS |
| M14 Model Registry | model capability evidence can support M16 | M04 TargetRepresentationProfile is semantic, not Model Card. PASS |
| M15 Multi-Model Director | routing consumes capability gaps | M04 never selects models/providers. PASS |
| M16 Workflow Registry & Provider Compiler | consumes M04 IR + M01 contracts | **Concrete compiler solely M16**; M04 owns semantic legality/lowering contract only. PASS |
| M17 ComfyUI Runtime | realizes M16 workflow | Comfy graph/node/runtime fields quarantined outside M04 core. PASS |
| M18 Supply Chain | resources/models/nodes carry integrity/licensing | M04 holds refs, not acquisition/install policy. PASS |
| M19 Training/LoRA | identity/style training consumes canonical anchors | training/dataset/model adapters outside M04. PASS |
| M20 Image Studio | produces/consumes image-oriented IR facets | image generation pipeline is M20; M04 core remains domain-neutral. PASS |
| M21 Reference/Pose/Depth Controls | control signals bind to scene/entity/spatial semantics | versioned domain facets/ResourceRefs; no control-model assumptions in core. PASS |
| M22 Composition/Typography/Product | semantic layout/design extensions | extension dialects/constraints map into M04; M22 owns design intelligence. PASS |
| M23 Image Repair | localized repairs use slices/deltas | repair decisions/actions M23/M49; M04 records new representation revisions. PASS |
| M24 Image Quality | evaluates rendered assets | M04 carries M01 obligation refs only; no evaluator authority. PASS |
| M25 3D Studio | generates geometry/scenes | M04 provides representation contract; generation strategies M25. PASS |
| M26 Blender Automation | DCC adapter consumes/produces M04 | Blender/bpy/collection IDs never canonical core. PASS |
| M27 Geometry/Retopo/UV/LOD | extends GeometryIR | M27 owns topology/UV/LOD quality and domain dialects; M04 owns generic geometry/resource substrate. PASS |
| M28 Materials/PBR/Textures | apparent "Material IR" overlap | **M04 owns generic cross-domain MaterialIR/typed graph; M28 owns PBR/material-production dialects, baking, generation and material QA.** PASS_WITH_PORT |
| M29 Rigging/Skinning | apparent Character skeleton overlap | M04 owns portable skeleton/skin/morph representation; M29 owns rig/control/anatomy/deformation production & QA. PASS |
| M30 Animation/Motion | MotionIR is interchange substrate | M30 owns motion generation, retarget, performance and QA. PASS |
| M31 Camera/Lighting/Rendering | apparent Camera/Lighting IR overlap | **M04 owns portable physical/semantic CameraIR/LightIR; M31 owns camera direction, lighting rigs/relighting, renderer strategy/AOV/render QA.** PASS_WITH_PORT |
| M32 VFX/Physics/Geometry Nodes | simulation/effect graphs extend IR | versioned VFX/simulation facets/payload refs; M32 owns simulation/effect behavior. PASS |
| M33 Maya/DCC Interop | direct consumer of round-trip contract | adapters/format mapping/qualification implement M04 RoundTripContract. PASS |
| M34 Web3D/WebGPU | target representation consumer | web/glTF profiles compile downstream; M04 canonical master remains richer. PASS |
| M35 Game Engine Delivery | target representation consumer | engine profiles/import presets downstream; no engine fields in core. PASS |
| M36 Video/Cinema | shot/timeline concepts overlap | **M04 owns portable Shot/Timeline representation; M36 owns planning/routing/assembly/master operations.** PASS_WITH_PORT |
| M37 Temporal Continuity | consumes continuity refs/state projections | M37 owns continuity graph/judgment/repair. PASS |
| M38 Editing/Compositing/Color | timeline/color concepts overlap | **M04 owns portable timeline/color identity contracts; M38 owns editing/compositing/grading/encode operations.** PASS_WITH_PORT |
| M39 Digital Humans | consumes CharacterIR/identity refs | M39 owns persistent persona/appearance/acting continuity. PASS |
| M40 Voice Studio | consumes VoiceIdentityRef/AudioIR | voice design/cloning/TTS/dubbing/prosody/QA owned M40. PASS |
| M41 Music Studio | consumes/produces MusicIR | composition/Music DNA/stems/mix/master owned M41. PASS |
| M42 Sound Design/Audio Post | consumes/produces AudioIR | generation/post/spatial rendering/loudness/QA owned M42. PASS |
| M43 Narrative/Canon | M04 NarrativeProjection points to Canon | M43 owns Story/Canon truth/world state/arcs/dialogue; M04 local cues never self-promote. PASS |
| M44 Faceless Content | multi-domain orchestration uses M04 | content factory logic outside IR; consumes scene/timeline/audio refs. PASS |
| M45 Advertising/UGC | campaign variants use IR | campaign/audience/attribution logic M45; M04 remains production representation. PASS |
| M46 Brand/IP | Brand DNA/constraints bind through refs | brand truth M46/M05; M04 only application/binding refs. PASS |
| M47 Localization | localized variants/timing/text/audio projections | localization/cultural decisions M47; M04 supports refs/slices without owning translation. PASS |
| M48 Quality Court | quality obligations/evidence touch IR paths | **M01/M48 remain quality authority; M04 readiness is never promotion.** PASS_WITH_AUTHORITY_SHIELD |
| M49 Self-Correction | defects map to localized IR paths | repair planner owns mutation proposal; accepted change creates governed new revisions. PASS |
| M50 Render Cascade | preview/final/cost routing | Preview/Final shield and canonical master prevent cost optimization from weakening final quality. PASS |
| M51 Benchmark Lab | validates schemas/adapters/regressions | M04 defines corpus/witness contracts; M51 owns benchmark infrastructure/governance. PASS |
| M52 HIVE Memory/RAG | semantic refs/slices useful for retrieval | HIVE remains derived context; cannot mutate canonical M04. PASS |
| M53 Provenance/Rights | M04 stores granular policy/provenance refs | M53 owns lineage/rights/consent/C2PA decisions. PASS |
| M54 Security | schemas/resources/adapters require trust | M54 owns RBAC/secrets/sandbox/restricted policy. M04 fail-closed refs/limits compatible. PASS |
| M55 Media CAS/Storage | payload/resource/digest storage | M55 owns locations/tiers/GC/archive; M04 identity separated from location. PASS |
| M56 Observability | dashboards inspect IR/gaps/readiness | telemetry is observational, no canonical authority. PASS |
| M57 Agents/Automation | agents create proposals/plans | agents cannot self-author protected M03/M04 changes or approvals. PASS |
| M58 API/SDK/MCP/Plugins | exposes schemas/extension lifecycle | M04 versioned schema/facet registry provides stable surface; permissions belong M58/M54. PASS |
| M59 Export/Delivery Compiler | compiles target deliverables | consumes M04 targets/capability manifests; cannot replace canonical master or M16 provider-workflow compiler. PASS |
| M60 Deployment/Final Acceptance | validates end-to-end | M04 evidence/round-trip contracts feed final acceptance; M60 owns release completion. PASS |

## Required extension/ref families

1. `IdentityDNARefPort` — M05/M39/M46.
2. `PersistenceCASPort` — M06/M55.
3. `HardwareCapabilityEvidenceRef` — M07-M10.
4. `ExecutionWorkloadDemandRef` — M10-M13 without embedding execution plans.
5. `ModelCapabilityEvidenceRef` — M14/M15.
6. `ConcreteProviderCompilerContract` — M16 boundary.
7. `ProviderRuntimeArtifactRef` — M17+ runtimes.
8. `GeometryMaterialDomainDialectPort` — M27/M28.
9. `RigDeformationDomainDialectPort` — M29.
10. `MotionProductionPort` — M30.
11. `RenderCameraLightingDialectPort` — M31/M32.
12. `DCCInterchangeAdapterPort` — M26/M33-M35.
13. `EditorialContinuityPort` — M36-M38.
14. `PersonaVoiceMusicAudioPort` — M39-M42.
15. `CanonStoryProjectionPort` — M43.
16. `BrandLocalizationProjectionPort` — M44-M47.
17. `QualityEvidencePort` — M48/M51 with M01 authority preserved.
18. `RepairOptimizationProposalPort` — M49/M50.
19. `ContextRightsSecurityStoragePort` — M52-M55.
20. `ObservabilityAutomationAPIExportPort` — M56-M60 with explicit sub-ownership in destination modules.

These are versioned boundaries, not implementations.

## Freeze requirements derived from scan

The M04 contract freeze MUST explicitly state:

1. M04 is provider-neutral and runtime-neutral.
2. M04 base schemas are extensible by versioned dialect/facet families.
3. M04 generic MaterialIR is base representation; M28 owns PBR/material-production depth.
4. M04 generic CameraIR/LightIR are base representations; M31 owns production lighting/rendering.
5. M04 TimelineIR is base representation; M36/M38 own planning/editing operations.
6. M04 quality/readiness evidence cannot promote quality or release.
7. M04 revisions do not create a competing M02/M06 version/build system.
8. M16 solely owns concrete provider/workflow compilation.
9. M05/M39/M43 remain identity/persona/canon authorities.
10. target/provider/hardware scarcity cannot weaken canonical final-quality semantics.
11. adapters use RoundTripContract/qualification evidence rather than claiming compatibility ad hoc.
12. M04 heavy payload/resources remain location-independent refs compatible with M55 storage.
13. future domain modules may add dialects/facets without requiring core-schema mutation when core invariants suffice.
14. a future extension that requires changing a frozen invariant requires a versioned M04 contract amendment and renewed compatibility review.

## Final compatibility verdict

`PASS_WITH_EXTENSION_PORTS`

No HIGH/CRITICAL future-ownership conflict remains.

Next legal gate: **M04 Module Contract Freeze Candidate**.

No M04 implementation is authorized.
