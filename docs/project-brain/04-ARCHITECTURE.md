# IRIS Architecture

Status: `PRODUCT_ARCHITECTURE_EVOLVING`

Git + Project Brain are authoritative. GEF governs lifecycle/evidence. HIVE supplies derived context/retrieval/memory/read-only MCP.

## Frozen authority layers

### M01 — Quality authority
`iris_quality` owns Fidelity Contract semantics, evaluator authority, quality decision/promotion, defect/debt rules and QualityClass acceptance. Later modules may consume or compile into M01 contracts but may not create a competing quality authority.

### M02 — Project / production authority
`iris_project_os` owns project/production identity, Production Graph causality, branch/variant/snapshot semantics, build/reuse semantics, ExecutionPlan contracts and promotion/release/archive lifecycle.

### M03 — Creative semantic authority
`iris_intent` owns Creative Brief identity/revisions, normalized intent, ambiguity/freedom, constraints, provider-neutral execution intent, explainability, conflicts/overrides and semantic freshness/versioning. It may compile admitted quality intent into M01-compatible contracts without taking M01 authority.

### M04 — Multimodal IR / Scene IR authority
M04 is frozen as `m04-contract-v1.0`. Its implementation package is `iris_multimodal_ir/`.

M04 owns the provider-neutral, runtime-neutral structured production representation derived from admitted M03 semantics:
- Scene/Entity/Asset/Character/Geometry representation;
- spatial/camera/light/material/color semantics;
- temporal/motion/audio/music/narrative/timeline representation;
- schema/facet/versioning/validation/migration/round-trip contracts;
- semantic capability/legality analysis and declarative lowering plans;
- slices, fingerprints, deltas and interface/payload boundaries.

M04 must not:
- become an M02 ExecutionPlan/runtime scheduler;
- become a provider-specific workflow/prompt compiler;
- duplicate M01 quality judgment;
- redefine M03 canonical intent;
- absorb M05 Asset/Persona DNA authority;
- own persistence/CAS/storage backends.

The historical M04 S04 / M16 Provider Compiler overlap is resolved: **M04 owns Representation Capability & Semantic Lowering; M16 solely owns concrete workflow/provider compilation and qualification.**

## Dependency direction

M04 may depend on:
- Python standard library;
- stable public M01 interfaces;
- stable public M03 interfaces;
- opaque/versioned M02 refs or stable public interfaces where required.

The M04 core must not require Blender/Maya/ComfyUI, provider/model SDKs, GPU/runtime SDKs, database/storage SDKs, or network/shell/external-process access.

## Ecosystem boundary

Target topology remains `HIVE <-> CORE <-> IRIS`, but CORE<->IRIS runtime contracts are not implemented/frozen.

HIVE remains a separate Docker/local-first runtime. GEF remains a separate source workspace/release. No HIVE backend/database or GEF package workspace is vendored into IRIS. Machine-local integration uses environment variables.

Provider, DCC, hardware, storage and delivery runtimes remain behind later versioned ports/contracts.
