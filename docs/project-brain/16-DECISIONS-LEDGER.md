# IRIS Decisions Ledger

## ADR-0001 - Project identity
Status: `APPROVED`
Project name is **Hive IRIS**, IRIS = **Intelligent Rendering & Immersive Synthesis**.

## ADR-0002 - New-project treatment
Status: `APPROVED`
IRIS is a new V1. UGAS may later supply proven reusable components, but legacy decisions are not inherited automatically.

## ADR-0003 - GEF adoption
Status: `APPROVED`
Use GEF Bootstrap v1.0.0 pinned to `866fe3af8cccc65c929aaf6a47a924401fa448b3`; do not vendor GEF.

## ADR-0004 - HIVE integration
Status: `APPROVED`
Use HIVE v1.0.0 pinned to `a53b5b9fcf55c32a5696180fb1b1ef80ccd1edcf` as external local-first context/retrieval/MCP; Git remains canonical.

## ADR-0005 - Product gate
Status: `APPROVED`
No product implementation before canonical planning sources and bounded Work Order admit it.

## ADR-0006 - CORE relationship
Status: `TARGET`
IRIS will collaborate with CORE, but runtime contracts require dedicated planning.

## ADR-0007 - IRIS 1.0 is not an MVP
Status: `APPROVED`
IRIS 1.0 is the complete first production version. Planning may sequence implementation, but required V1 capabilities are not deferred merely to create an MVP label.

## ADR-0008 - Extreme quality is a product invariant
Status: `APPROVED`
Final masters prioritize validated visual/multimodal quality. Draft/preview lanes may optimize speed but cannot silently lower master acceptance criteria.

## ADR-0009 - ComfyUI is the primary image workflow fabric, not a permanent model lock
Status: `APPROVED`
IRIS uses ComfyUI as the primary local image workflow/runtime integration while models/providers remain replaceable and empirically routed.

## ADR-0010 - Blender headless-first
Status: `APPROVED`
Blender is the primary 3D/motion DCC. Normal automation uses supervised headless/background workers. MCP is a structured control/inspection surface and optional live-session path, not the only execution mechanism.

## ADR-0011 - 8 GB VRAM is a first-class hardware class
Status: `APPROVED`
IRIS must provide a truthful execution route for 8 GB VRAM-class systems through hardware-aware model selection, quantization, offload, tiling/chunking and scheduling. No fixed GPU presets.

## ADR-0012 - UGAS V2 vision is carried into IRIS 1.0
Status: `APPROVED`
All useful UGAS V2 categories and previously planned ideas are mapped into IRIS 1.0. Reuse is evidence-based and classified; legacy implementation is not inherited blindly.

## ADR-0013 - Qualified versions, canary upgrades and rollback
Status: `APPROVED`
Fast-moving dependencies such as ComfyUI, custom nodes, models and DCC adapters are pinned/qualified for production and upgraded through compatibility checks/canaries with rollback.



## ADR-0014 - Review auto-fix before executor escalation
Status: `APPROVED`
During IRIS reviews, bounded findings that ChatGPT can safely correct and validate using repository/CI evidence are fixed directly in the active branch/PR. A Codex/Coder/Zcode corrective prompt is produced only when the correction requires unavailable workstation/runtime capabilities or cannot be safely proven from the review environment. The canonical operational rule is `.engineering/REVIEW-AUTOFIX-POLICY.md`.


## ADR-0015 - M02 semantic authority and M06 operational ownership
Status: `APPROVED`
M02 is the canonical semantic authority for project/production identity, Production Graph causality, branch/variant/snapshot/rollback semantics, incremental-build/reuse semantics, and production promotion/release/archive lifecycle. M06 may deepen content-addressed persistence, dependency indexing, reconstruction, cleanup and rollback execution, but MUST implement/extend M02 contracts rather than create a competing second state/version/build model.


## ADR-0016 - M03 semantic ownership and compiler boundary
Status: `APPROVED`
M03 is the canonical semantic authority for Creative Brief identity/revisions, normalized intent, ambiguity/freedom representation, constraint semantics and later provider-neutral execution-intent compilation. M03 does not own M01 quality judgment/promotion, M02 production/graph/lifecycle semantics, M04 media/scene IR, or provider-specific workflow/runtime details. M02 consumes versioned M03 references; M04+ consume compiled M03 intent.


## ADR-0017 - M03 compiles quality intent into M01 without authority duplication
Status: `APPROVED`
M03 may compile admitted brief/constraint semantics into a versioned Fidelity Contract Spec and, through an admitted M01 DomainProfile/registry path, into the frozen M01 `FidelityContract`. M03 MUST NOT invent FidelityDimension IDs, grant evaluator capability, weaken M01 defect/hard-gate rules, fabricate HUMAN_DECISION evidence or silently lower QualityClass due to hardware/provider limits. M01 remains the sole quality decision/promotion authority.


## ADR-0018 - M03 Execution Intent is not an M02 ExecutionPlan
Status: `APPROVED`
M03 owns a provider-neutral semantic Execution Intent Bundle expressing desired operations, capability demands, mutation/protection envelopes and explainability. It MUST NOT emit provider workflows, prompts as canonical truth, worker commands or M02 `ExecutionPlan` objects. M02 remains the causal graph/execution-plan contract authority; M16/M17/M26 and other provider modules perform concrete translation. Mandatory semantic obligations may not be silently weakened to fit provider capability.


## ADR-0019 - M03 conflicts and overrides are receipt-governed
Status: `APPROVED`
M03 semantic conflicts are explicit versioned objects. Recency, specificity or model confidence alone never determines precedence. Effective overrides require an authorized versioned Authority Policy Graph plus immutable Override Receipt, and ordinary M03 overrides cannot bypass M01/M02 invariants or admitted non-overridable rights/security/governance policy. Brief edits/migrations/restorations create new immutable revisions; M02 remains branch/variant/rollback authority.


## ADR-0020 - M03 contract freezes semantic compilation, not provider execution
Status: `APPROVED`
The M03 freeze covers immutable Creative Brief/Intent/Constraint semantics, compilation into M01 Fidelity Contract references/objects, provider-neutral Execution Intent, explainability, conflicts/overrides and semantic revision/freshness. It explicitly excludes provider prompts/workflows, M02 ExecutionPlan/worker execution, M04 Scene IR internals, domain DNA engines, real judges, HIVE retrieval, rights/security engines, persistence and publishing.


## ADR-0021 - M04 owns provider-neutral structured production IR
Status: `APPROVED`
M04 is the canonical authority for provider-neutral multimodal structured production representation derived from admitted M03 semantics. It owns Scene/Entity/Asset/Character/Geometry, spatial/camera/light/material/color, temporal/motion/audio/music/narrative/timeline representation, schema/version/validation and round-trip contracts. It does not replace M01 quality, M02 project/build/release or M03 creative-intent authority.

## ADR-0022 - M04 uses dual graph, interface/payload and immutable revision semantics
Status: `APPROVED`
Containment/transform topology is a strict acyclic graph distinct from typed semantic relationships. Canonical IR revisions/fragments/prototypes are immutable. Lightweight interface capsules remain interpretable independently of heavy geometry/media/cache payloads, which are referenced through typed resources.

## ADR-0023 - M04 base representations do not steal domain-engine ownership
Status: `APPROVED`
M04 owns generic cross-domain MaterialIR, CameraIR, LightIR, TimelineIR, MotionIR, AudioIR, MusicIR and NarrativeProjectionIR representation contracts. M28/M31/M36/M38/M40-M43 and related domain modules own generation, editing, rendering, mix, story/Canon, QA and other domain operations. M04 representation is substrate, not those engines.

## ADR-0024 - M16 solely owns the concrete Provider Compiler
Status: `APPROVED`
The historical M04 S04 Provider Compiler label is superseded by **Representation Capability & Semantic Lowering**. M04 may analyze semantic representability and emit declarative provider-neutral lowering plans/receipts. M16 alone owns concrete provider/workflow compilation, workflow graphs, provider nodes/parameters, qualification and rollback.

## ADR-0025 - Capability scarcity cannot downgrade canonical quality or semantics
Status: `APPROVED`
Unsupported target/provider/hardware capability produces explicit gaps, extension requirements, alternate-target/escalation proposals or an upstream governed revision. M04 MUST NOT lower M01 QualityClass, relax mandatory/protected M03 constraints, relabel required capability as optional, or replace final semantics with preview semantics merely to fit provider scarcity/cost.

## ADR-0026 - M04 schema evolution and migration are explicit and immutable
Status: `APPROVED`
Transport version, core schema version, facet/dialect versions and validation/lowering versions are separate axes. Compatibility is directional and version-pinned; "latest" is not automatic compatibility. Migration creates a new immutable IR revision plus receipt and leaves the historical source unchanged.

## ADR-0027 - Round-trip fidelity is semantic and independently evidenced
Status: `APPROVED`
M04 round-trip contracts define exact, structural, semantic, tolerant, opaque-preservation or allowed-loss expectations per semantic family/path. Witness sets are derived from canonical obligations before adapter output. Adapters/providers cannot self-certify equivalence or promotion; M04 readiness remains evidence only.
