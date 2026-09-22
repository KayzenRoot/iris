# M04 Technology Registry

Module: `M04 — Multimodal IR / Scene IR`
Status: `S01_S05_CANDIDATES_COMPLETE`
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


## IRIS-MIRX-061 — Unified Temporal Reference Fabric
**Purpose:** exact rational time basis shared across motion/audio/music/narrative.

## IRIS-MIRX-062 — Temporal Layer Partition
**Purpose:** separate semantic, authored, sampled/baked and editorial time.

## IRIS-MIRX-063 — Temporal Conversion Receipt
**Purpose:** explicit frame/timebase conversion with quantization/loss evidence.

## IRIS-MIRX-064 — Motion Channel Contract
**Purpose:** typed target-property temporal channels independent of DCC paths.

## IRIS-MIRX-065 — Curve Semantics Envelope
**Purpose:** provider-neutral knots/tangents/interpolation/extrapolation/loop semantics.

## IRIS-MIRX-066 — Motion Clip Semantic Layer
**Purpose:** immutable reusable clips with timing/blend/root-motion contracts.

## IRIS-MIRX-067 — Motion Composition Ledger
**Purpose:** deterministic layer/blend precedence and provenance.

## IRIS-MIRX-068 — Deformation Time Binding
**Purpose:** bind skeleton/morph/attachment temporal data to CharacterIR.

## IRIS-MIRX-069 — Temporal Sampling Contract
**Purpose:** shutter/sample-window/motion-blur semantics without renderer settings.

## IRIS-MIRX-070 — Motion Bake Receipt
**Purpose:** prove sampled/baked output corresponds to authored motion and expose loss.

## IRIS-MIRX-071 — Audio Object Semantic Envelope
**Purpose:** semantic role, media, timing, identity and rights around audio objects.

## IRIS-MIRX-072 — Spatial Audio Representation Profile
**Purpose:** channel/object/scene/binaural metadata without renderer ownership.

## IRIS-MIRX-073 — Audio Clip Binding
**Purpose:** source/target ranges, fades, gain envelopes and sync refs.

## IRIS-MIRX-074 — Voice Identity Bridge
**Purpose:** opaque Voice/Persona refs without taking M39/M40 ownership.

## IRIS-MIRX-075 — Audio Conform Receipt
**Purpose:** record trim/resample/channel/layout conversion effects.

## IRIS-MIRX-076 — Music Structural IR
**Purpose:** tempo/meter/form/parts/events independent of a DAW or MIDI protocol.

## IRIS-MIRX-077 — Tempo & Meter Map
**Purpose:** exact temporal mapping between musical and real-time domains.

## IRIS-MIRX-078 — Music Performance Event Dialect
**Purpose:** optional note/expression/articulation semantics beyond MIDI limitations.

## IRIS-MIRX-079 — Music Media/Score Duality
**Purpose:** keep symbolic/structural representation distinct from rendered audio media.

## IRIS-MIRX-080 — Music Adapter Quarantine
**Purpose:** MIDI/score/DAW extensions never contaminate canonical core identity.

## IRIS-MIRX-081 — Narrative Projection Firewall
**Purpose:** prevent production-local narrative realization from becoming Canon truth.

## IRIS-MIRX-082 — Narrative Cue Envelope
**Purpose:** bounded beat/action/dialogue/reaction/transition cues before M43 integration.

## IRIS-MIRX-083 — Story/Canon Ref Bridge
**Purpose:** future M43 references without implementing Canon internals.

## IRIS-MIRX-084 — Portable Timeline Fabric
**Purpose:** nested track/clip/gap/marker/transition representation without editor authority.

## IRIS-MIRX-085 — Shot Representation Capsule
**Purpose:** compact camera/scene/entity/audio/narrative binding for a shot.

## IRIS-MIRX-086 — Cross-Modal Sync Graph
**Purpose:** typed exact/offset/beat/lip/event synchronization relations.

## IRIS-MIRX-087 — Sync Tolerance Shield
**Purpose:** fail closed when mandatory synchronization exceeds admitted tolerance.

## IRIS-MIRX-088 — Continuity Dependency Bridge
**Purpose:** expose continuity-relevant state to future M37 without implementing its judge.

## IRIS-MIRX-089 — Temporal Loss Impact Map
**Purpose:** bind resampling/baking/edit loss to exact semantic paths and quality obligations.

## IRIS-MIRX-090 — Context-Budgeted Temporal Slice
**Purpose:** time-window + dependency-closure slices for localized temporal work.


All `MIRX-061..090` remain **CANDIDATE_FOR_FINAL_TECHNOLOGY_REVIEW**.


## IRIS-MIRX-091 — Representation Capability Manifest
**Purpose:** deterministic required/used semantic capability inventory for an IR slice/document.

## IRIS-MIRX-092 — Required/Used Capability Split
**Purpose:** prevent correctness-critical semantics from being relabelled optional.

## IRIS-MIRX-093 — Target Representation Profile
**Purpose:** versioned semantic destination support contract, not a vendor identity.

## IRIS-MIRX-094 — Semantic Legality Analyzer
**Purpose:** analysis-only exact/bounded/unsupported/unknown classification.

## IRIS-MIRX-095 — Dynamic Legality Constraint
**Purpose:** declare conditional support for a feature under bounded constraints.

## IRIS-MIRX-096 — Semantic Lowering Plan
**Purpose:** provider-neutral ordered adaptation contract consumed by future concrete compilers.

## IRIS-MIRX-097 — Declarative Lowering Rule Registry
**Purpose:** versioned non-executable source/target semantic adaptation rules.

## IRIS-MIRX-098 — Loss Authorization Gate
**Purpose:** bounded adaptation only when upstream loss policy authorizes it.

## IRIS-MIRX-099 — No-Downgrade Quality Shield
**Purpose:** prohibit scarcity/cost/provider weakness from reducing canonical QualityClass or mandatory semantics.

## IRIS-MIRX-100 — Representation Gap Ledger
**Purpose:** target support failures/remedies bound to exact IR/quality/constraint refs.

## IRIS-MIRX-101 — Adaptation Proposal Ledger
**Purpose:** proposals such as split/bake/extension/escalation without self-authorization.

## IRIS-MIRX-102 — Semantic/Concrete Compiler Split
**Purpose:** architectural firewall between M04 semantic lowering and M16 concrete workflow compilation.

## IRIS-MIRX-103 — Provider Observation Quarantine
**Purpose:** runtime/provider capability observations remain evidence, not canonical mutation authority.

## IRIS-MIRX-104 — Translation Receipt Chain
**Purpose:** link M03 semantic translation -> M04 IR translation -> M16 concrete provider receipt.

## IRIS-MIRX-105 — Target Profile Version Pin
**Purpose:** target semantic profile/version participates in legality/fingerprint evidence.

## IRIS-MIRX-106 — Extension Requirement Ledger
**Purpose:** required vs optional extension families and exact support evidence.

## IRIS-MIRX-107 — Capability Evidence Ref
**Purpose:** bind support claims to future M14/M16 qualification evidence.

## IRIS-MIRX-108 — Semantic Capability Debt
**Purpose:** governed non-blocking representation debt distinct from M01 QualityDebt.

## IRIS-MIRX-109 — Capability Debt Expiry
**Purpose:** stale/temporary approximation acceptance invalidates dependent translations.

## IRIS-MIRX-110 — Multi-Target Lowering Bundle
**Purpose:** one canonical source mapped to multiple semantic targets with explicit equivalence obligations.

## IRIS-MIRX-111 — Cross-Target Identity Bridge
**Purpose:** preserve stable semantic identity across DCC/web/game/render target representations.

## IRIS-MIRX-112 — Cross-Target Fidelity Matrix
**Purpose:** enumerate exact/approx/loss per obligation for every requested target.

## IRIS-MIRX-113 — Semantic Destination Taxonomy
**Purpose:** target families remain vendor-neutral and capability-oriented.

## IRIS-MIRX-114 — Capability Slice Compiler
**Purpose:** minimum sufficient compatibility input rather than full scene/provider catalog.

## IRIS-MIRX-115 — Unsupported Feature Escalation Contract
**Purpose:** deterministic escalation to extension/alternate target/future provider routing.

## IRIS-MIRX-116 — Opaque Preservation Contract
**Purpose:** preserve optional unknown extensions without pretending to understand them.

## IRIS-MIRX-117 — Approximation Boundary Proof
**Purpose:** prove bounded adaptation remains inside authorized tolerances.

## IRIS-MIRX-118 — Canonical Master Preservation
**Purpose:** derived/lossy target representation never replaces canonical source IR.

## IRIS-MIRX-119 — Representation Qualification Ref
**Purpose:** future signed qualification evidence from M16 without circular ownership.

## IRIS-MIRX-120 — Semantic Compiler Contract
**Purpose:** frozen interface handed from M04 to M16: source IR + capability manifest + lowering plan + obligations + validation requirements.


All `MIRX-091..120` remain **CANDIDATE_FOR_FINAL_TECHNOLOGY_REVIEW**.


## IRIS-MIRX-121 — Multi-Axis Version Vector
**Purpose:** separate contract/transport/core-schema/facet/lowering/validator versions.

## IRIS-MIRX-122 — Canonical IR Envelope
**Purpose:** bind canonical payload, manifests, versions and digests in one transport-neutral trust envelope.

## IRIS-MIRX-123 — Canonical Byte Profile
**Purpose:** deterministic finite-number-safe encoding for hashing/signing/fingerprints.

## IRIS-MIRX-124 — Layered Validation Pipeline
**Purpose:** transport -> schema -> structure -> refs -> semantics -> authority -> capability -> limits -> round trip.

## IRIS-MIRX-125 — Stable Validation Finding Taxonomy
**Purpose:** typed deterministic finding codes rather than free-form-only errors.

## IRIS-MIRX-126 — Validation Profile
**Purpose:** versioned phase/schema/limit/round-trip requirements for PREVIEW/FINAL/targets.

## IRIS-MIRX-127 — Schema Evolution Ledger
**Purpose:** family/version compatibility, deprecation, migration and behavior-change records.

## IRIS-MIRX-128 — Directional Compatibility Declaration
**Purpose:** READ/WRITE/ROUND_TRIP/BEHAVIOR/MIGRATION/INCOMPATIBLE/UNKNOWN status per version pair.

## IRIS-MIRX-129 — Unknown Extension Policy
**Purpose:** required fail-closed vs explicitly opaque-preservable optional data.

## IRIS-MIRX-130 — Immutable Migration Plan
**Purpose:** source/target schema conversion contract before execution.

## IRIS-MIRX-131 — Immutable Migration Receipt
**Purpose:** new revision + exact path/loss/evidence record while preserving historical source.

## IRIS-MIRX-132 — Semantic Round-Trip Contract
**Purpose:** per-family exact/tolerant/opaque/loss/one-way guarantees.

## IRIS-MIRX-133 — Round-Trip Receipt
**Purpose:** adapter chain and path-by-path semantic comparison evidence.

## IRIS-MIRX-134 — Semantic Witness Set
**Purpose:** canonical predeclared invariants that a round trip must preserve.

## IRIS-MIRX-135 — IR Equivalence Profile
**Purpose:** versioned exact/tolerant/unit/color/time comparison semantics.

## IRIS-MIRX-136 — Witness Coverage Matrix
**Purpose:** prove every mandatory obligation has an applicable round-trip witness.

## IRIS-MIRX-137 — Canonical/Derived Data Firewall
**Purpose:** prevent cache/observation/recomputed values from overwriting authored/lowered truth.

## IRIS-MIRX-138 — Digest Profile Registry
**Purpose:** versioned digest algorithms and canonical input definitions.

## IRIS-MIRX-139 — Subgraph Integrity Digest
**Purpose:** localized tamper/change detection without hashing unrelated graph regions.

## IRIS-MIRX-140 — Resource Manifest Digest
**Purpose:** pin external resource identity/integrity independently of mutable locations.

## IRIS-MIRX-141 — Adversarial Complexity Shield
**Purpose:** deterministic node/edge/depth/fanout/size/sample limits.

## IRIS-MIRX-142 — Graph Cycle Policy Validator
**Purpose:** edge-family-specific cycle legality with strict containment rejection.

## IRIS-MIRX-143 — Reference Reachability Validator
**Purpose:** required refs/provenance/lowering traces cannot dangle.

## IRIS-MIRX-144 — Deterministic Finding Order
**Purpose:** stable audit output for same input/profile/version.

## IRIS-MIRX-145 — Adapter Qualification Contract
**Purpose:** version/hash/profile/witness/loss corpus required before claiming round-trip support.

## IRIS-MIRX-146 — Anti-Self-Certification Shield
**Purpose:** adapter/provider output cannot declare its own equivalence/qualification authoritative.

## IRIS-MIRX-147 — IR Release Readiness Evidence
**Purpose:** aggregate M04 readiness without stealing downstream release/quality/security authority.

## IRIS-MIRX-148 — Schema Downgrade Refusal
**Purpose:** prevent automatic coercion into older/weaker schema without authorized migration/loss policy.

## IRIS-MIRX-149 — Opaque Preservation Digest
**Purpose:** prove unknown optional opaque extensions survived untouched when preservation is promised.

## IRIS-MIRX-150 — Round-Trip Regression Corpus Contract
**Purpose:** deterministic representative corpus/witness matrix for adapter qualification and schema evolution.


All `MIRX-121..150` remain **CANDIDATE_FOR_FINAL_TECHNOLOGY_REVIEW**.
