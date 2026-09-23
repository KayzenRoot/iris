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

### M05 — Asset DNA 2.0 & Cross-Modal Identity authority
M05 is implemented, independently audited, merged and exact-main validated as `m05-contract-v1.0`. Its domain-neutral core owns persistent semantic identity across representations and authorized mutations.

S01 freezes these architectural directions:
- stable opaque DNA subject identity separate from M04 representation identity;
- immutable DNA revisions;
- typed identity traits with explicit criticality and mutability;
- canonical/evidence twin-plane separation;
- cross-modal identity anchors and projection contracts;
- observation/embedding/hash/provider outputs remain evidence, never self-authorizing canonical truth;
- M02 keeps project/branch/history authority;
- M06 keeps operational production-state/content-addressed persistence/reconstruction under M02 contracts; M55 keeps media CAS/storage/cache/archive authority;
- M53/M54 keep rights/provenance/privacy/security authority;
- M39/M40/M41/M43/M46 keep domain production/canon/brand authority.

S02 adds typed family profiles while preserving one common identity engine:
- CLASS / ARCHETYPE / INDIVIDUAL / VARIANT are distinct semantic levels;
- Character, Creature, Object, Product and Environment use typed profile/trait bundles;
- persistent component identity is independent of array order, names and M04 node IDs;
- persistent appearance is separated from contextual appearance and observations;
- product model/SKU/package/physical-instance identities remain distinct;
- EnvironmentDNA persists place identity while M04 SceneIR remains current representation authority;
- family reclassification requires explicit migration/projection semantics.

S03 adds cross-modal identity links without transferring domain authority:
- M30 owns MotionDNA and motion production; M05 owns only revision-pinned MotionDNALink relations;
- M40 owns VoiceDNA and voice production; M05 owns only revision-pinned VoiceDNALink relations;
- M46 owns BrandDNA / Brand & IP; M05 owns only BrandDNALink relations;
- M45 owns Campaign DNA / Creative Genome and advertising, which is explicitly distinct from BrandDNA;
- SceneIdentityDNA is persistent reusable composition identity, not M04 SceneIR state or M43 Canon truth;
- cross-modal links are owner/family/revision pinned and never silently follow latest;
- CrossModalDNAGraph is an identity-link graph, not M02 Production Graph, M04 Scene Graph or M43 Canon Graph.

S04 adds identity transition semantics without absorbing evaluator or downstream runtime authority:
- anchors have explicit authority classes and auditable lifecycle;
- drift is path-level, typed and multi-dimensional, never one similarity score;
- representation repair cannot mutate canonical DNA;
- protected canonical mutation requires proposal, policy/authority and explicit decision;
- same-identity mutation creates a new immutable revision;
- identity break creates a new dna_id with explicit lineage;
- split/consolidation preserve source histories and provenance;
- M01 retains quality/evaluator authority and M37 temporal-continuity authority;
- M05 remains the generic persistent identity root while M39 owns digital-human/persona production continuity;
- M53/M54 retain provenance/rights/consent/security authority for protected evidence.

S05 completes the functional planning boundary:
- M05 lineage relations are semantic identity lineage only; M02 remains project/production branch authority;
- M02 retains semantic branch/snapshot/rollback/build-reuse lifecycle authority; M06 operationalizes content-addressed persistence, dependency indexing, reconstruction and rollback execution under M02 contracts;
- compatibility is directional and multi-axis, with explicit loss/migration/indeterminate outcomes;
- reusable DNA package identity remains distinct from persistent subject identity;
- M53 owns rights/license/consent/provenance, M54 security/restricted-content, M55 storage/CAS, M58 API/conformance surfaces and M59 concrete export/publishing;
- package import is staged and cannot overwrite canonical identity;
- canonical DNA packages are non-executable by default and unknown mandatory semantics fail closed.

Final Technology Review consolidates the 150 DNAX design-history candidates into `F-M05-01..25` with exact-once coverage (150/150, 0 missing, 0 duplicate assignments). The consolidated families, not 150 independent implementation classes, are the freeze-candidate architecture surface.

The M06-M60 Forward Compatibility Scan and Independent Planning Audit are complete. M05 is implemented and durably closed. M06 is frozen as `m06-contract-v1.0`, implemented through IRIS-WO-0010, independently approved, merged and exact-main validated. M07 Hardware Genome & Runtime Discovery is the active planning module.

Forward Compatibility Scan result:
- M06-M60 scanned: 55 modules;
- verdict: `PASS_WITH_EXTENSION_PORTS`;
- critical downstream ownership conflicts remaining: 0;
- required future extension/ref families: 22;
- M02/M06 semantic-vs-operational ownership wording reconciled;
- M39 persona continuity explicitly bound to the M05 generic identity root;
- frozen M05 invariants may only change through a versioned contract amendment and renewed compatibility review.

M05 and M06 implementations are complete and exact-main validated. M07 planning may define provider-neutral hardware/runtime observation contracts, but M07 implementation remains gated until its own planning freeze, independent audit, merged planning baseline and separately admitted implementation Work Order. M08+ remains behind the Future Contract Shield.

## M07 active planning boundary

M07 may discover, normalize and version hardware/runtime facts. It does not benchmark workloads (M08), govern VRAM/RAM leases or offload (M09), compile adaptive execution plans (M10), supervise worker/process lifecycle (M11), place jobs across compute targets (M12), replace empirical model capability authority (M14), own physical storage (M55), or replace observability aggregation (M56).

Hardware scarcity is represented as explicit capability/evidence state and cannot silently lower M01 quality targets or protected M03 semantic obligations. Hardware/runtime facts become material to M06 reproducibility only through explicit declared materiality.

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
