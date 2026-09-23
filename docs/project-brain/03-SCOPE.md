# IRIS Scope

Status: `M04_IMPLEMENTATION_WORK_ORDER_READY`

## Current admitted increment — M04 post-merge reconciliation

### NECESSARY
- preserve the merged M04 planning package and frozen `m04-contract-v1.0`;
- record PR #27 merge SHA `9ae6a8b8e7ba15730d8e216fb4cc524cc895adf4`;
- record post-merge Governance `35801333080 / 106992107984` and `2527/2527 OK`;
- remove stale promotion-pending-merge state;
- preserve M01/M02/M03 authority boundaries and M16 concrete Provider Compiler ownership;
- pass exact-head Governance for this reconciliation;
- squash-merge this reconciliation through `main-governance`;
- validate the resulting exact `main`;
- only then compile/admit a separate bounded M04 implementation Work Order / Context Lock / Evidence package.

### OUT OF SCOPE FOR THIS INCREMENT
- M04 product/kernel implementation;
- M05 implementation;
- concrete provider/model prompt/workflow compilation;
- Blender/ComfyUI/Maya/DCC execution;
- model downloads, training or media generation;
- changing or weakening frozen M01, M02, M03 or M04 contracts;
- provider/runtime choices that silently reduce final M01 QualityClass.

## IRIS 1.0 product scope

IRIS 1.0 includes the capabilities represented by M00–M60, including the useful UGAS V2 vision: project/production OS, hardware intelligence, compute, model intelligence, multimodal IR, Asset DNA, digital humans, persistent virtual spokespersons/digital ambassadors, image, video, film/cinema/scene production, commercials, motion, advanced 3D, Blender/DCC, voice/music/audio, narrative, faceless and presenter-led content, advertising, brand, localization, Quality Court, repair, render cascade, HIVE memory/RAG, provenance/rights, security, storage/cache, dashboard, automation/agents, APIs/MCP, adaptive export and release/recovery.

The implementation order does not reduce the V1 scope.
