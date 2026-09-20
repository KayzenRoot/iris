# IRIS 1.0 — Research Baseline — 2026-09-20

Status: `ACTIVE_DISCOVERY_REFERENCE`

## Sources inspected

### IRIS
- Repository: `KayzenRoot/iris`
- Bootstrap main base: `f41c85f64f764400cc600eb52d98cadd0f78a49e`
- State before this Work Order: `PRODUCT_DISCOVERY_READY`

### UGAS V1
- Repository: `KayzenRoot/ugas`
- Inspected main: `0169f84248703931bb7578177d9773bce319c14e`
- V1 strengths retained as evidence/reference: Art DNA/spec schemas, model manifests with exact hashes/licenses/hardware evidence, ComfyUI HTTP client, provider/workflow contracts, FAST/QUALITY lanes, candidate hard gates, provenance, alpha/structural QA, fail-closed states, GPU/VRAM telemetry, cache invalidation and honest unknown/gap reporting.

### UGAS V2 planning
- Source: `UGAS-V2-MASTER-BLUEPRINT.md`
- Blueprint version: `0.3.0`
- Original macro-taxonomy: 30 categories.
- Central retained concepts: Production Graph, Hardware Genome, Adaptive Execution Fabric, Dynamic VRAM Governor, Model Intelligence Fabric, Multi-Model Director, Scene IR, Asset DNA 2.0, Persistent Identity, Quality Court, Self-Correction, Render Cascade, multimodal memory/RAG, provenance/rights/C2PA, storage/cache, dashboard, agents and adaptive export.

## 2026 toolchain research

### Blender
Production baseline candidate: Blender `5.2 LTS` line. The current LTS receives fixes through July 2028. IRIS uses Blender as the primary 3D/motion DCC.

Primary automation mode:
- headless `blender --background` subprocess jobs;
- Python/`bpy` scripts with bounded inputs/outputs;
- fresh or pooled workers only where evidence shows it is safe;
- no dependence on visible UI for normal batch production.

MCP role:
- structured control/inspection interface;
- optional live-session interaction;
- not the only execution path;
- headless CLI/API remains the production fallback.

Important safety/performance rule:
Blender Python is not treated as thread-safe. Concurrency is process-oriented and resource-governed.

### ComfyUI
Current public release observed during research: `v0.36.0`. IRIS treats ComfyUI as a local workflow server/fabric, not a pile of ad-hoc PowerShell windows.

Control model:
- one supervised runtime per configured worker where practical;
- server/API submission;
- queue/progress events;
- bounded concurrency;
- explicit unload/free-memory and restart policies;
- compatibility matrix for core/custom nodes;
- pinned qualified versions;
- canary upgrade + rollback instead of blind auto-update.

### Image model strategy
No single model is frozen as 'the best'. IRIS maintains a benchmarked pool and routes per task.

Initial research pool includes:
- local FLUX.2 Klein 4B/9B families;
- local/open candidates such as Z-Image;
- qualified API escalation candidates such as GPT-Image-1, Seedream-class models and Stable Image Ultra;
- future models admitted by Model Assimilation, empirical benchmarks, license checks and hardware qualification.

UGAS V1 already contains evidence for a quantized FLUX.2 Klein 4B lane on the 8 GB RTX 5050 class. IRIS uses that as evidence that the 8 GB class is viable, not as a permanent model choice.

## Architectural conclusions

1. `QUALITY_FIRST_MASTER`: final masters target maximum validated quality; speed optimizations apply only when they preserve the Fidelity Contract.
2. `NO_FIXED_GPU_PRESETS`: hardware is measured and modeled, not hard-coded as 'RTX 5050 mode'.
3. `8GB_FIRST_CLASS`: 8 GB VRAM systems must have a supported execution route using quantization/offload/tile/chunk/model routing where necessary.
4. `HEADLESS_FIRST_DCC`: Blender batch work runs in background by default so the operator can continue using the desktop.
5. `SUPERVISED_PROCESSES`: IRIS owns worker lifecycle, cleanup, timeouts, cancellation and zombie detection. Shell windows are not the orchestration layer.
6. `MODEL_CHAMPION_CHALLENGER`: quality/performance decisions come from empirical tournaments, not vendor claims.
7. `PIN_CANARY_ROLLBACK`: ComfyUI, Blender adapters, workflows, custom nodes and models are qualified before production promotion.
8. `PROGRESSIVE_FIDELITY`: draft/preview may be cheap, but final master gates stay strict.
9. `MINIMAL_REPAIR`: defects should trigger the smallest valid regeneration/repair surface.
10. `HIVE_DERIVED_CONTEXT`: HIVE accelerates context/retrieval/memory while Git/IRIS canonical sources remain authoritative.
