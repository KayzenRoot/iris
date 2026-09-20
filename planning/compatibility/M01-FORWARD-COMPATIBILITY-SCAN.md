# M01 — Forward Compatibility Scan

Status: `PASS_WITH_EXTENSION_PORTS`
Date: 2026-09-20
Scope: known contracts of M02–M60, without deep-planning future internals.

## Question
Can the M01 quality architecture serve all currently known IRIS 1.0 domains without forcing future modules to depend on M01 implementation details?

## Required future consumers

### Production/IR
M02–M06 require versioned Fidelity Contracts, evidence references, asset/scene IDs, lineage and cross-modal invariants.

### Hardware/execution
M07–M13 require quality constraints to be separable from execution strategy. Lower hardware may change route/time/precision strategy but cannot silently mutate MASTER thresholds.

### Models/workflows
M14–M19 require pluggable judges/providers, versioned evaluator metadata and benchmark qualification.

### Image
M20–M24 require image/reference/pose/composition/repair/IQA validators.

### 3D/game/web3D
M25–M35 require geometry/material/rig/motion/VFX/camera/runtime validators plus gameplay-distance and web budgets.

### Video
M36–M38 require temporal dimensions, shot continuity and frame/region evidence.

### Humans/audio
M39–M42 require face/identity/voice/music/audio domain evaluators. M01 must permit non-visual Fidelity Vector extensions without changing its core protocol.

### Story/content/brand
M43–M47 require narrative/brand/localization constraints and cross-surface continuity.

### Quality
M48–M51 are direct implementation/benchmark consumers of M01 contracts.

### Memory/provenance/security
M52–M55 require evidence/provenance IDs and immutable version metadata, but HIVE memory cannot silently alter acceptance contracts.

### Control/API/export/release
M56–M60 require machine-readable quality states, provider ports, export-target validation and final acceptance evidence.

## Extension contract required before M01 implementation

M01 SHALL define protocol-level abstractions, not domain implementations:

- `FidelityContract`
- `FidelityDimension`
- `QualityClass`
- `Defect`
- `SemanticZone`
- `EvidenceRef`
- `JudgeResult`
- `QualityDecision`
- `UncertaintyState`
- `QualityDebt`
- `QualityJudge` port
- `AssetValidator` port
- domain/profile registry extension point

Audio/narrative/etc. may register dimensions/profiles later without modifying M01 core state-machine semantics.

## Compatibility hazards and protections

1. **Metric lock-in** → judges are provider/versioned ports.
2. **Visual-only schema** → dimension registry supports typed media domains.
3. **Game bias** → Nerim QX technologies live in profiles, not global mandatory rules.
4. **Vendor lock-in** → no Blender/ComfyUI/model-specific type in M01 core contracts.
5. **8 GB policy leakage** → hardware execution policy consumes fidelity requirements; it does not define them.
6. **Schema churn** → explicit version + migration strategy.
7. **Future unknown evaluator** → evidence payload supports typed extension metadata while canonical decision fields remain stable.

## Verdict
PASS. M01 may proceed to Module Contract Freeze and executor preparation after canonical schema/acceptance criteria are written.
