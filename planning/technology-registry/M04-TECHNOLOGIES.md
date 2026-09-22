# M04 Technology Registry

Module: `M04 — Multimodal IR / Scene IR`
Status: `S02_REGISTRY_ACTIVE`
Rule: proprietary candidates are design identifiers, not novelty/patentability claims until dedicated prior-art/legal review.

## External prior-art references

- `EXT-M04-001 OpenUSD` — ACCEPTED_AS_SCENE_COMPOSITION_AND_SCHEMA_REFERENCE.
- `EXT-M04-002 OpenUSD Payload/Instancing patterns` — ACCEPTED_AS_SCALE_REFERENCE.
- `EXT-M04-003 UsdSkel` — ACCEPTED_AS_CHARACTER_DEFORMATION_REFERENCE.
- `EXT-M04-004 glTF 2.0/2.0.1` — ACCEPTED_AS_RUNTIME_DELIVERY_INTERCHANGE_REFERENCE.
- `EXT-M04-005 glTF 2.1 complex-scene work` — RESEARCH_ONLY_UNTIL_FINAL_STANDARD_QUALIFICATION.
- `EXT-M04-006 MLIR dialect/interface model` — ACCEPTED_AS_IR_EXTENSIBILITY_REFERENCE.
- `EXT-M04-007 MLIR dialect versioning/upgrades` — ACCEPTED_AS_VERSIONING_REFERENCE.

No external technology above becomes a mandatory M04 runtime dependency by this disposition.

---

## IRIS-MIRX-001 — Semantic Scene Graph Fabric
**Purpose:** IRIS-owned provider-neutral graph substrate for multimodal production representation.
**S01 use:** scene/entity/asset/character structure.

## IRIS-MIRX-002 — Dual-Graph Topology
**Purpose:** separate strict containment/transform hierarchy from arbitrary typed semantic relationships.
**Why:** prevents transform rules from contaminating narrative/material/attachment/deformation relationships.

## IRIS-MIRX-003 — Intent-to-IR Trace Spine
**Purpose:** every correctness-relevant IR fact resolves to M03 semantic source/policy refs.

## IRIS-MIRX-004 — IR Interface Capsule
**Purpose:** compact asset/fragment interface readable without heavy payload.

## IRIS-MIRX-005 — Deferred Semantic Payload
**Purpose:** defer geometry/media/cache payload while keeping semantic interface available.

## IRIS-MIRX-006 — Obligation Coverage Matrix
**Purpose:** map M03 obligations and M01 quality obligations to representing IR nodes/properties and expose holes.

## IRIS-MIRX-007 — Semantic Lowering Receipt
**Purpose:** immutable receipt of M03 -> M04 lowering rule/version, coverage, loss and gaps.

## IRIS-MIRX-008 — Versioned Facet/Dialect Registry
**Purpose:** bounded extensibility without growing one universal core schema.

## IRIS-MIRX-009 — Character Semantic Skeleton Envelope
**Purpose:** provider-neutral skeleton/joint/rest/bind/deformation contract independent of DCC control rigs.

## IRIS-MIRX-010 — Identity Anchor Bridge
**Purpose:** bind future M05 identity/DNA refs into M04 application points without taking M05 ownership.

## IRIS-MIRX-011 — Prototype/Instance Integrity Graph
**Purpose:** immutable prototypes plus bounded instance-local overrides.

## IRIS-MIRX-012 — Semantic Attachment Ports
**Purpose:** typed sockets/bindings rather than free-form name links.

## IRIS-MIRX-013 — Asset Role Map
**Purpose:** classify components/resources by semantic production role rather than file layout.

## IRIS-MIRX-014 — Representation Capability Envelope
**Purpose:** declare what a representation can express without provider-specific capability logic.

## IRIS-MIRX-015 — Spatial Contract Ref
**Purpose:** S01 placeholder/boundary for S02 coordinate/space/unit semantics.

## IRIS-MIRX-016 — Multimodal Relationship Edge
**Purpose:** one typed relationship substrate usable across visual, character, motion, audio and narrative domains.

## IRIS-MIRX-017 — Scene Fragment Composition Graph
**Purpose:** explicit composition of immutable IR fragments.

## IRIS-MIRX-018 — Deterministic Composition Precedence
**Purpose:** explicit precedence/override surfaces; prohibit last-writer-wins.

## IRIS-MIRX-019 — IR Gap Ledger
**Purpose:** typed unresolved/missing/loss/incompatibility records with remedies and ownership.

## IRIS-MIRX-020 — Canonical/Derived Property Partition
**Purpose:** distinguish canonical authored/lowered facts from calculated/cache/provider-derived facts.

## IRIS-MIRX-021 — Semantic Change Surface
**Purpose:** report exactly which semantic paths/subgraphs changed.

## IRIS-MIRX-022 — Locality-Preserving IR Delta
**Purpose:** delta localized subgraphs without invalidating unrelated IR.

## IRIS-MIRX-023 — Cross-Domain Type Family
**Purpose:** reusable type families/facets shared by image, 3D, video, character and future audio domains.

## IRIS-MIRX-024 — Round-Trip Confidence Anchor
**Purpose:** S01 seed for S05 proof that adapter round trips preserve declared semantics.

## IRIS-MIRX-025 — Provider Extension Quarantine
**Purpose:** permit opaque provider extension refs without contaminating canonical core semantics.

## IRIS-MIRX-026 — Context-Budgeted IR Slice
**Purpose:** minimum sufficient subgraph with dependency/provenance closure.

## IRIS-MIRX-027 — Quality Obligation Binding
**Purpose:** bind M01 obligation refs to IR regions without reimplementing quality judgment.

## IRIS-MIRX-028 — Rights/Provenance Attachment Ref
**Purpose:** future M53/M54 policy hooks at entity/resource/fragment granularity.

## IRIS-MIRX-029 — Resource Handle Integrity
**Purpose:** logical resource identity + content digest/provenance separated from mutable location.

## IRIS-MIRX-030 — Scene Assembly Manifest
**Purpose:** compact deterministic declaration of fragment/prototype/resource composition needed to materialize a scene interface.

---

## S01 registry disposition

All `MIRX-001..030` remain **CANDIDATE_FOR_FINAL_TECHNOLOGY_REVIEW**.

No candidate is frozen until:
1. S01-S05 planning completes;
2. overlap/duplication is consolidated;
3. external prior art is considered;
4. M05-M60 Forward Compatibility Scan passes;
5. Final Technology Review accepts/supersedes/rejects it.


## IRIS-MIRX-031 — Unit-Safe Spatial Ledger
**Purpose:** bind physical/spatial values to explicit dimensions, units and reference conventions.

## IRIS-MIRX-032 — Coordinate Frame Registry
**Purpose:** versioned named/scoped coordinate-frame semantics independent of DCC namespaces.

## IRIS-MIRX-033 — Transform Intent Stack
**Purpose:** preserve authored operation order separately from derived matrices.

## IRIS-MIRX-034 — Spatial Conversion Receipt
**Purpose:** prove source/target frames, units, version and loss for coordinate conversion.

## IRIS-MIRX-035 — Physical Camera Envelope
**Purpose:** portable physical camera semantics with typed units and projection model.

## IRIS-MIRX-036 — Lens Model Extension Registry
**Purpose:** fisheye/panoramic/calibrated/nonlinear lens extensions without polluting core.

## IRIS-MIRX-037 — Framing Constraint Binding
**Purpose:** bind M03 composition/framing intent to camera/subject/spatial IR.

## IRIS-MIRX-038 — Focus & DOF Semantic Contract
**Purpose:** explicit focus targets/distance/aperture intent independent of renderer knobs.

## IRIS-MIRX-039 — Exposure Semantics Partition
**Purpose:** keep physical exposure controls separate from tone/display transforms.

## IRIS-MIRX-040 — Photometric Light Core
**Purpose:** typed emitter and physically identified quantity/unit semantics.

## IRIS-MIRX-041 — Spectral Intent Envelope
**Purpose:** represent RGB/color-temperature/spectral intent with explicit basis and future spectral extension.

## IRIS-MIRX-042 — Light Influence Set
**Purpose:** typed include/exclude affected-subgraph semantics.

## IRIS-MIRX-043 — Light Shaping Contract
**Purpose:** provider-neutral cones/spread/profile/filter semantics.

## IRIS-MIRX-044 — Shadow Intent Contract
**Purpose:** separate artistic/physical shadow requirements from renderer parameters.

## IRIS-MIRX-045 — Environment Illumination Envelope
**Purpose:** environment/HDRI/procedural illumination resource + orientation/exposure/color contracts.

## IRIS-MIRX-046 — Material Semantic Graph
**Purpose:** typed target-neutral material network with deterministic port validation.

## IRIS-MIRX-047 — Shading Dialect Registry
**Purpose:** versioned extension families for advanced BSDF/volume/displacement semantics.

## IRIS-MIRX-048 — Material Purpose Binding
**Purpose:** FINAL/PREVIEW/utility bindings with explicit target/subset scope.

## IRIS-MIRX-049 — Color-Space Tagged Value
**Purpose:** make color-space/encoding/alpha semantics inseparable from correctness-critical color values.

## IRIS-MIRX-050 — Color Pipeline Contract Ref
**Purpose:** bind an admitted OCIO-like profile/config without taking color-management runtime ownership.

## IRIS-MIRX-051 — Color Conversion Receipt
**Purpose:** source/target color identity, transform version, tolerance and loss evidence.

## IRIS-MIRX-052 — Texture Semantic Binding
**Purpose:** coordinate set, channel role, encoding, alpha and sampling intent around texture resources.

## IRIS-MIRX-053 — Material Coverage Graph
**Purpose:** prove geometry/subset material coverage and reveal unbound/ambiguous regions.

## IRIS-MIRX-054 — Physicality Classifier
**Purpose:** tag PHYSICAL vs approximation vs artistic non-physical semantics.

## IRIS-MIRX-055 — Preview/Final Separation Shield
**Purpose:** prevent cheaper preview representations from silently satisfying final obligations.

## IRIS-MIRX-056 — Spatial Dependency Closure
**Purpose:** ensure subgraph slices include frames/transforms/coordinate dependencies required for correct interpretation.

## IRIS-MIRX-057 — Camera Match Receipt
**Purpose:** record semantic/calibration correspondence when importing/matching external cameras.

## IRIS-MIRX-058 — Approximation Impact Map
**Purpose:** enumerate exact IR paths/quality obligations affected by provider approximation.

## IRIS-MIRX-059 — Projection Space Bridge
**Purpose:** scoped named coordinate frames for projection painting/procedural material spaces.

## IRIS-MIRX-060 — Spatial Staleness Vector
**Purpose:** mark derived bounds/transforms/projections stale when correctness-relevant geometry/frame dependencies change.


All `MIRX-031..060` remain **CANDIDATE_FOR_FINAL_TECHNOLOGY_REVIEW**.
