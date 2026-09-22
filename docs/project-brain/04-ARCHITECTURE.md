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

## Next planned layer — M04

M04 Multimodal IR / Scene IR is planned to materialize admitted M03 semantic intent into detailed provider-neutral scene/media IR for scene, character, asset, camera, lighting, material, spatial, motion, audio, music and narrative representation.

M04 must not:
- become an M02 ExecutionPlan/runtime scheduler;
- become a provider-specific workflow/prompt compiler;
- duplicate M01 quality judgment;
- redefine M03 canonical intent;
- absorb M05 Asset DNA ownership.

The known M04 S04 / M16 Provider Compiler naming overlap must be resolved during M04 planning. The current compatibility boundary is: M04 owns semantic IR lowering/capability-loss representation; M16 owns concrete workflow/provider compilation and qualification.

## Ecosystem boundary

Target topology remains `HIVE <-> CORE <-> IRIS`, but CORE<->IRIS runtime contracts are not implemented/frozen.

HIVE remains a separate Docker/local-first runtime. GEF remains a separate source workspace/release. No HIVE backend/database or GEF package workspace is vendored into IRIS. Machine-local integration uses environment variables.

Provider, DCC, hardware, storage and delivery runtimes remain behind later versioned ports/contracts and are not implied by the semantic kernels already implemented.
