# IRIS Scope

Status: `M04_IMPLEMENTATION_REVIEW_APPROVED_PENDING_MERGE`

## Current increment — IRIS-WO-0008 / M04 implementation

### COMPLETE AND REVIEWED
- complete frozen `m04-contract-v1.0` provider-neutral Multimodal IR / Scene IR kernel in `iris_multimodal_ir/`;
- all 20 frozen `F-M04-01..20` families represented;
- all 80 hard invariants preserved with direct/deterministic proof mapping;
- M01 quality authority, M02 project/build/release/ExecutionPlan authority, M03 creative semantic authority and M16 concrete provider/workflow compiler authority preserved;
- deterministic identity, graph/composition, schema/facet/extension, serialization, migration and validation semantics;
- scene/entity/asset/character, spatial/camera/light/material/color, temporal/motion/audio/music/narrative/timeline representations;
- M03→M04 lowering traces, capability/legality/lowering contracts and explicit loss/gap evidence;
- semantic round-trip witnesses with unit/color/time-aware tolerance behavior and anti-self-certification;
- minimum-sufficient slices, fingerprints/deltas and deterministic resource/depth/fanout/sample limits;
- seven domain-neutral synthetic profiles on one kernel;
- documentation and Evidence Bundle;
- independent review: 6 CHAT_FIXABLE findings closed, 0 EXECUTOR_REQUIRED, 0 remaining HIGH/CRITICAL;
- reviewed exact-head full suite: 2677/2677 OK.

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

The implementation order does not reduce the V1 scope. M05 remains blocked until M04 is merged and reconciled on exact main.
