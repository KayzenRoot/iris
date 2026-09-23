# IRIS Architecture

Status: `PRODUCT_ARCHITECTURE_EVOLVING_M04_FROZEN`

Git + Project Brain are authoritative. GEF governs lifecycle/evidence. HIVE supplies derived context/retrieval/memory/read-only MCP.

## Frozen authority layers

### M01 — Quality authority
`iris_quality` owns Fidelity Contract semantics, evaluator authority, quality decision/promotion, defect/debt rules and QualityClass acceptance. Later modules may consume or compile into M01 contracts but may not create a competing quality authority.

### M02 — Project / production authority
`iris_project_os` owns project/production identity, Production Graph causality, branch/variant/snapshot semantics, build/reuse semantics, ExecutionPlan contracts and promotion/release/archive lifecycle.

### M03 — Creative semantic authority
`iris_intent` owns Creative Brief identity/revisions, normalized intent, ambiguity/freedom, constraints, provider-neutral execution intent, explainability, conflicts/overrides and semantic freshness/versioning. It may compile admitted quality intent into M01-compatible contracts without taking M01 authority.

### M04 — Multimodal IR / Scene IR
Frozen contract: `m04-contract-v1.0`.

M04 owns the provider-neutral, runtime-neutral structured production representation that materializes admitted M03 semantics into typed scene/media IR. The implementation package admitted by IRIS-WO-0008 is `iris_multimodal_ir`.

M04 owns:
- immutable IR documents/revisions/envelopes and stable semantic identities;
- scene/entity/asset/character/geometry representation;
- dual containment/transform and semantic-relationship graph contracts;
- explicit composition, prototype/instance and interface/payload/resource boundaries;
- spatial/unit/transform/camera/light/material/color representation;
- temporal/motion/audio/music/narrative/timeline representation;
- M03→M04 lowering receipts, representation gaps and semantic-loss evidence;
- representation capability/legality and provider-neutral lowering plans;
- schema/facet/version/validation/migration contracts;
- semantic round-trip witnesses/equivalence/readiness evidence;
- minimum-sufficient slices, structural/subgraph/interface fingerprints and semantic deltas.

M04 does not:
- become an M02 ExecutionPlan/runtime scheduler or competing history/build authority;
- become a provider-specific workflow/prompt/compiler;
- duplicate M01 quality judgment or lower QualityClass for scarcity;
- redefine or weaken M03 canonical intent/constraints;
- absorb M05 Asset/Persona DNA policy;
- own persistence/CAS/storage locations;
- execute Blender/ComfyUI/Maya/providers, media generation or GPU scheduling.

The former M04/M16 naming overlap is resolved: **M04 owns semantic representability/legality and declarative provider-neutral lowering contracts; M16 solely owns concrete provider/workflow compilation and qualification.**

## Ecosystem boundary

Target topology remains `HIVE <-> CORE <-> IRIS`, but CORE<->IRIS runtime contracts are not implemented/frozen.

HIVE remains a separate Docker/local-first runtime. GEF remains a separate source workspace/release. No HIVE backend/database or GEF package workspace is vendored into IRIS. Machine-local integration uses environment variables.

Provider, DCC, hardware, storage and delivery runtimes remain behind later versioned ports/contracts and are not implied by M01-M04 semantic kernels.
