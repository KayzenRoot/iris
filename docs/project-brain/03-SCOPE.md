# IRIS Scope

Status: `M04_IMPLEMENTATION_ADMISSION_RECOMPILED`

## Current admitted increment — IRIS-WO-0008 / M04 implementation

### NECESSARY
- implement the complete frozen `m04-contract-v1.0` provider-neutral Multimodal IR / Scene IR kernel;
- create `iris_multimodal_ir/` as the M04 package;
- implement all 20 frozen `F-M04-01..20` families and preserve all 80 hard invariants;
- preserve M01 quality authority, M02 project/build/release/ExecutionPlan authority and M03 creative semantic authority;
- preserve M16 as sole concrete provider/workflow compiler owner;
- implement deterministic identity, dual graph, composition, interface/payload, schema/facet/versioning, migration and serialization semantics;
- implement scene/entity/asset/character, spatial/camera/light/material/color, temporal/motion/audio/music/narrative/timeline representations;
- implement M03→M04 lowering traces, capability/legality/lowering contracts, multi-target semantic plans and explicit loss/gap evidence;
- implement round-trip witnesses/equivalence/readiness without adapter self-certification;
- implement minimum-sufficient slices, fingerprints and deltas with deterministic resource limits;
- prove the same core against seven domain-neutral synthetic profiles;
- add focused tests, documentation, Evidence Bundle and proposed Checkpoint Delta;
- preserve the no-provider/no-DCC/no-network/no-shell closed-runtime boundary.

### OUT OF SCOPE FOR THIS INCREMENT
- M05 Asset/Persona DNA implementation;
- M06/M55 persistence/CAS/storage backend;
- M16 concrete provider/workflow compilation;
- Blender/Maya/ComfyUI execution or provider/model SDKs;
- model selection/download/training/routing;
- GPU/VRAM scheduling or worker orchestration;
- image/video/3D/audio generation;
- rig-control or motion-generation systems;
- renderer/material production engines;
- voice/music/audio generation or mastering;
- story/Canon engine;
- real quality judges;
- rights/security engines;
- publishing/export/delivery execution;
- any semantic change to frozen M01, M02, M03 or M04 contracts.

## IRIS 1.0 product scope

IRIS 1.0 includes the capabilities represented by M00–M60, including the useful UGAS V2 vision: project/production OS, hardware intelligence, compute, model intelligence, multimodal IR, Asset DNA, digital humans, persistent virtual spokespersons/digital ambassadors, image, video, film/cinema/scene production, commercials, motion, advanced 3D, Blender/DCC, voice/music/audio, narrative, faceless and presenter-led content, advertising, brand, localization, Quality Court, repair, render cascade, HIVE memory/RAG, provenance/rights, security, storage/cache, dashboard, automation/agents, APIs/MCP, adaptive export and release/recovery.

The implementation order does not reduce the V1 scope.
