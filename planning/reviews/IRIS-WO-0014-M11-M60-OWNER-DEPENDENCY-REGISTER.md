# IRIS-WO-0014 — M11–M60 Owner Contract Dependency Register

Status: `EXHAUSTIVE_PENDING_OWNER_CONTRACTS`  
Work Order: `IRIS-WO-0014` — proposal only, implementation NOT ADMITTED  
Proposal base: `873053d24d9e28f5ff9b186914fa3de7caf749de`  
Source scan: [M10 Forward Compatibility Scan](../compatibility/M10-FORWARD-COMPATIBILITY-SCAN.md), exact-main validated at `2328978175a59768e64687748b259027b3a79d4e`

## Finding

At exact main `873053d24d9e28f5ff9b186914fa3de7caf749de`, the repository has 50 master-index entries M11–M60 and 50 index-level candidate rows in the M10 scan. The Git tree contains no individual `planning/modules/M11…M60` plan files and no `planning/contracts/M11…M60` frozen contract files. The scan states this limitation and requires each handoff to be revisited against the owning module contract when planned.

Every candidate relation below remains pending owner confirmation. A scan row is a discovery record, not an approved interface, schema, threshold, permission, or implementation instruction.

## Exhaustive register

| Owner module | M10 scan relationship | Status at proposal base | Required preflight closure |
| --- | --- | --- | --- |
| M11 — Background Worker Fabric & Process Lifecycle | Direct handoff; authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M12 — Compute Orchestration: Local, Multi-GPU, LAN, Remote & Cloud | Direct handoff; authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M13 — Performance, Cache & Execution Efficiency | Evidence consumer; authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M14 — Model Registry & Empirical Model Cards | Evidence consumer; model authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M15 — Multi-Model Director & Champion/Challenger Routing | Policy boundary | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M16 — Workflow Registry & Provider Compiler | Direct typed handoff | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M17 — ComfyUI Runtime Integration | Indirect runtime / invalidation source | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M18 — Model Acquisition, Integrity, License & Supply Chain | Supply-chain authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M19 — Fine-Tuning, LoRA, Adapters & Style/Identity Training | Workload consumer; training authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M20 — Image & Photography Studio | Domain workload consumer | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M21 — Reference Fusion, Pose, Depth, Edge & Segmentation Control | Semantic-input shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M22 — Composition, Typography, Product & Design Intelligence | Semantic hard-constraint consumer | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M23 — Image Repair, Retouch, Relight, Upscale & Transparency | Bounded workload consumer | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M24 — Image Quality Evals & Visual Acceptance | Quality authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M25 — 3D & Spatial Asset Studio | Domain workload consumer | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M26 — Blender 5.2 LTS Headless Automation & MCP | Runtime/DCC adapter boundary | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M27 — Geometry, Retopology, UV, LOD & Topology Quality | Quality / semantic shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M28 — Materials, PBR, Textures & Baking | Domain workload consumer | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M29 — Rigging, Skinning, Anatomy & Deformation | Domain constraint consumer | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M30 — Animation & Motion Studio | Temporal-quality shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M31 — Camera, Lighting & Rendering | Renderer handoff; authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M32 — VFX, Physics, Particles & Geometry Nodes | Simulation-integrity boundary | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M33 — Maya & DCC Interoperability | Provider-neutrality boundary | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M34 — Web 3D / WebGPU Asset Compiler | Destination-profile consumer | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M35 — Game Engine Asset Delivery | Destination-profile consumer | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M36 — Video & Cinema Studio | Domain workload consumer | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M37 — Temporal Consistency & Shot Continuity | Temporal-quality authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M38 — Editing, Compositing, Color & Encode | Delivery-semantic boundary | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M39 — Digital Humans & Virtual Identity | Identity and rights shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M40 — Voice Studio & Dubbing | Audio/rights authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M41 — Music Studio | Rights and quality shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M42 — Sound Design & Audio Post | Cross-media quality boundary | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M43 — Narrative, Script & Canon Engine | Semantic / production authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M44 — Faceless Content Factory | Indirect consumer; autonomy shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M45 — Advertising & Synthetic UGC Studio | Cost / rights / approval shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M46 — Brand & IP Studio | Semantic and rights shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M47 — Localization & Culturalization Studio | Locale and identity shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M48 — Quality Court & Automated Review | Quality authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M49 — Self-Correction, Partial Repair & Minimal Regeneration | Repair-policy boundary | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M50 — Render Cascade & Cost-to-Quality Optimization | Objective / cost boundary | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M51 — Benchmark Lab, Evals & Regression Corpus | Calibration evidence consumer / source boundary | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M52 — HIVE Multimodal Memory & Creative RAG Integration | Read-only context handoff | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M53 — Provenance, Rights, Consent & C2PA | Provenance authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M54 — Security, Identity & Restricted Content | Security authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M55 — Media CAS, Storage, Cache & Archive Fabric | Storage-control boundary | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M56 — Observability, Telemetry & IRIS Control Center | Telemetry handoff / source boundary | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M57 — Automation, Agents & Autonomous Production | Authorization / stop-condition shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M58 — API, SDK, MCP & Plugin Ecosystem | Versioned projection boundary | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M59 — Export, Publishing & Adaptive Delivery Compiler | Delivery / publication shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |
| M60 — Deployment, Recovery, System Integration & IRIS 1.0 Final Acceptance | Final evidence consumer; release authority shield | `PENDING_OWNER_CONTRACT` | Verify the scan candidate against the owner’s frozen contract; pin exact interface, evidence, failure and authority semantics before admission. |

## Admission rule

For each row: obtain the owner’s canonical planning contract; confirm exact M10 inputs/outputs, owner/version/scope, freshness/invalidation, unknown/error behavior, authorization/approval and acceptance evidence; update the M10 interface proposal if needed; record the contract SHA and owner confirmation in a refreshed Context Lock and Evidence Bundle. Do not infer a missing contract from the master index, scan or adjacent implementation.

All 50 rows must be closed before the separate implementation Work Order can pass preflight, consistent with section 8 of `m10-contract-v1.0`.
