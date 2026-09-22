# M04 Final Technology Review

Status: `APPROVED_FOR_FORWARD_COMPATIBILITY`
Date: 2026-09-22
Module: `M04 — Multimodal IR / Scene IR`
Issue: `#26`

## Review rule

Acceptance means "admitted to the M04 freeze candidate architecture" after consolidation. It does **not** claim novelty, patentability or implementation.

Detailed identifiers `IRIS-MIRX-001..150` remain design-history references. The frozen contract should depend on consolidated families `F-M04-01..20`, not on 150 independent implementation classes.

External standards are architectural/interoperability references only unless a later adapter module explicitly qualifies them.

## External prior-art disposition

| ID | Disposition | Rationale |
| --- | --- | --- |
| EXT-M04-001 OpenUSD scene/schema | ACCEPTED_AS_REFERENCE | strong scene composition/schema prior art; no core runtime dependency |
| EXT-M04-002 OpenUSD payload/instancing | ACCEPTED_AS_REFERENCE | useful scale/interface-payload pattern |
| EXT-M04-003 UsdSkel | ACCEPTED_AS_REFERENCE | skeletal/skinning/blend-shape prior art |
| EXT-M04-004 glTF 2.0/2.0.1 | ACCEPTED_AS_INTERCHANGE_REFERENCE | runtime delivery reference, not authoring truth |
| EXT-M04-005 glTF 2.1 work | RESEARCH_ONLY | emerging/unfrozen dependency risk |
| EXT-M04-006 MLIR dialect/interfaces | ACCEPTED_AS_ARCHITECTURE_REFERENCE | extensibility/lowering pattern, not compiler dependency |
| EXT-M04-007 MLIR versioning | ACCEPTED_AS_ARCHITECTURE_REFERENCE | per-dialect/version upgrade pattern |
| EXT-M04-008 MaterialX 1.39 family | ACCEPTED_AS_MATERIAL_INTERCHANGE_REFERENCE | provider-independent material graph prior art |
| EXT-M04-009 OpenColorIO 2.x | ACCEPTED_AS_COLOR_PIPELINE_REFERENCE | color identity/transform prior art; runtime ownership elsewhere |
| EXT-M04-010 OpenTimelineIO | ACCEPTED_AS_EDITORIAL_INTERCHANGE_REFERENCE | timeline/clip/track/media-ref pattern |
| EXT-M04-011 MIDI 2.0 | ACCEPTED_AS_MUSIC_EVENT_INTERCHANGE_REFERENCE | music/performance prior art, not canonical protocol |
| EXT-M04-012 ITU ADM | ACCEPTED_AS_AUDIO_METADATA_REFERENCE | channel/object/scene/binaural metadata prior art |
| EXT-M04-013 RFC 8785 JCS | ACCEPTED_AS_CANONICALIZATION_REFERENCE | deterministic hashable JSON pattern; no mandatory library |
| EXT-M04-014 OpenUSD schema versioning | ACCEPTED_AS_VERSIONING_REFERENCE | behavioral compatibility/family-version prior art |

## Ownership correction

### Legacy conflict
The Master Module Index used "Provider Compiler" in both M04 S04 and M16.

### Final disposition
**M04 S04 is renamed to "Representation Capability & Semantic Lowering".**

M04 owns semantic representability, legality analysis, provider-neutral lowering contracts and loss/gap evidence.

M16 remains the **sole concrete Workflow Registry & Provider Compiler** owner.

Disposition: `OWNERSHIP_CONFLICT_RESOLVED`.

## Consolidated frozen technology families

### F-M04-01 — Semantic Multimodal IR Core
Sources: MIRX-001, 002, 016, 023.
Status: ACCEPT.
Purpose: IRIS-owned typed multimodal node/relationship substrate with dual graph topology.

### F-M04-02 — Intent / Quality Trace Spine
Sources: MIRX-003, 006, 007, 027, 028.
Status: ACCEPT.
Purpose: trace M03 semantics and M01 obligations into IR representation and lowering receipts.

### F-M04-03 — Interface / Payload / Resource Fabric
Sources: MIRX-004, 005, 029, 030.
Status: ACCEPT.
Purpose: lightweight semantic interfaces plus deferred heavy payload/resource identity.

### F-M04-04 — Versioned Schema / Facet / Extension Fabric
Sources: MIRX-008, 014, 015, 025.
Status: ACCEPT_WITH_CONSOLIDATION.
Note: MIRX-015 placeholder is superseded by the full S02 spatial contract but retained as design history.

### F-M04-05 — Character / Identity Anchor Bridge
Sources: MIRX-009, 010, 012, 013.
Status: ACCEPT.
Boundary: deformation representation only; M05/M29/M39 retain identity/rigging/digital-human authority.

### F-M04-06 — Composition / Prototype / Instance Integrity
Sources: MIRX-011, 017, 018.
Status: ACCEPT.
Purpose: immutable prototypes/fragments and deterministic scoped composition without last-writer-wins.

### F-M04-07 — Gap / Delta / Slice / Canonical-Derived Fabric
Sources: MIRX-019, 020, 021, 022, 026.
Status: ACCEPT.
Purpose: explicit gaps, locality-preserving deltas and minimum sufficient IR context.

### F-M04-08 — Unit-Safe Spatial & Transform Fabric
Sources: MIRX-031, 032, 033, 034, 056, 060.
Status: ACCEPT.

### F-M04-09 — Physical Camera & Projection Fabric
Sources: MIRX-035, 036, 037, 038, 039, 057.
Status: ACCEPT.
Boundary: M31 owns production camera/rendering strategy.

### F-M04-10 — Lighting Semantic Fabric
Sources: MIRX-040, 041, 042, 043, 044, 045.
Status: ACCEPT.
Boundary: M31/M32 own actual lighting/VFX/render behavior.

### F-M04-11 — Material / Texture / Color Integrity Fabric
Sources: MIRX-046..055, 058, 059.
Status: ACCEPT_WITH_CONSOLIDATION.
Purpose: typed material graph, color identity, preview/final separation and approximation evidence.
Boundary: M28/M31/M38 own material production, rendering and color operations.

### F-M04-12 — Temporal / Motion Representation Fabric
Sources: MIRX-061..070.
Status: ACCEPT.
Boundary: M29/M30 own rigging/animation generation and repair.

### F-M04-13 — Audio / Voice Representation Fabric
Sources: MIRX-071..075.
Status: ACCEPT.
Boundary: M40/M42 own voice/audio production and post.

### F-M04-14 — Music Structural Representation Fabric
Sources: MIRX-076..080.
Status: ACCEPT.
Boundary: M41 owns composition, Music DNA and mix/master.

### F-M04-15 — Narrative / Timeline / Sync Projection Fabric
Sources: MIRX-081..090.
Status: ACCEPT_WITH_BOUNDARY.
MIRX-081 Narrative Projection Firewall is mandatory.
Boundary: M36/M38 own editorial operations; M43 owns Canon/story truth; M37 owns continuity judgment.

### F-M04-16 — Representation Capability & Legality Fabric
Sources: MIRX-091..095, 105, 106, 107.
Status: ACCEPT.
Purpose: deterministic used/required capability manifests and semantic legality analysis.

### F-M04-17 — Semantic Lowering & Compiler Boundary Fabric
Sources: MIRX-096..104, 115..120.
Status: ACCEPT_WITH_OWNERSHIP_SHIELD.
Purpose: declarative provider-neutral lowering plans/receipts only.
M16 concrete provider/workflow compilation is non-negotiable boundary.

### F-M04-18 — Multi-Target / Capability Debt Fabric
Sources: MIRX-108..114.
Status: ACCEPT.
Boundary: capability debt never becomes M01 QualityDebt and cannot waive quality gates.

### F-M04-19 — Canonical Envelope / Validation / Schema Evolution Fabric
Sources: MIRX-121..131.
Status: ACCEPT.
Purpose: multi-axis versions, canonical bytes, layered validation, directional compatibility and immutable migrations.

### F-M04-20 — Semantic Round-Trip & Readiness Proof Fabric
Sources: MIRX-024, 132..150.
Status: ACCEPT_WITH_SUPERSESSION.
MIRX-024 early Round-Trip Confidence Anchor is superseded by the complete witness/receipt/equivalence/qualification family in S05.
IR readiness remains evidence only, not release/promotion authority.

## Candidate-level disposition summary

- MIRX-001..014: ACCEPT through F-M04-01..06.
- MIRX-015: SUPERSEDED_BY_S02_SPATIAL_CONTRACT, retained as history.
- MIRX-016..023: ACCEPT through F-M04-01/06/07.
- MIRX-024: SUPERSEDED_BY_F_M04_20, retained as history.
- MIRX-025..030: ACCEPT through F-M04-02/03/04/07.
- MIRX-031..060: ACCEPT through F-M04-08..11.
- MIRX-061..090: ACCEPT through F-M04-12..15.
- MIRX-091..120: ACCEPT through F-M04-16..18, with M16 ownership shield.
- MIRX-121..150: ACCEPT through F-M04-19..20.
- No candidate is independently labelled "novel" or "patentable".

## Mandatory architecture shields

1. M01 remains sole quality decision/promotion authority.
2. M02 remains project/graph/build/ExecutionPlan/release authority.
3. M03 remains creative brief/intent/constraint/override authority.
4. M05 remains persistent Asset/Persona DNA authority.
5. M06 remains storage/CAS/persistence authority.
6. M14/M15 own empirical capability and routing.
7. M16 solely owns concrete provider/workflow compiler.
8. M29/M30 own rigging and motion production.
9. M31/M28 own rendering/material production depth.
10. M36/M38 own cinema/editorial operations.
11. M39-M43 own identity/voice/music/audio/story domain engines.
12. M53/M54/M59 later own rights/security/side-effect authority.
13. Canonical M04 truth cannot be weakened by target/provider scarcity.

## Final review verdict

`APPROVED_FOR_FORWARD_COMPATIBILITY`

S01-S05 plus F-M04-01..20 are coherent enough to perform the M05-M60 Forward Compatibility Scan.

No M04 implementation is authorized.


## Independent audit correction notes

- `M04-PLAN-R01` — CHAT_FIXABLE / CLOSED: MIRX-028 was accepted in candidate-level prose but omitted from all consolidated family source lists. It is now mapped to `F-M04-02 Intent / Quality Trace Spine`.
- `M04-PLAN-R02` — CHAT_FIXABLE / CLOSED: MIRX-100 was listed in both `F-M04-16` and `F-M04-17`. Its single canonical family is now `F-M04-17 Semantic Lowering & Compiler Boundary Fabric`.
- Consolidated family mapping is intended to cover `MIRX-001..150` exactly once.
