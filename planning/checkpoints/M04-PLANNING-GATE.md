# IRIS M04 Planning Gate

Status: `CONTRACT_FREEZE_CANDIDATE_AUDIT_NEXT`
Issue: `#26`
Branch: `m04-multimodal-ir-planning`
Authorized main baseline: `c231dd61a210fe6d315126e755b4642a4fd2e9a3`

## Sessions
- S01 — Scene, Character and Asset IR: COMPLETE_FOR_MODULE_PLANNING
- S02 — Camera, Lighting, Material and Spatial IR: COMPLETE_FOR_MODULE_PLANNING
- S03 — Motion, Audio, Music and Narrative IR: COMPLETE_FOR_MODULE_PLANNING
- S04 — Representation Capability & Semantic Lowering (legacy Provider Compiler label): COMPLETE_FOR_MODULE_PLANNING
- S05 — IR validation, versioning and round-trip guarantees: COMPLETE_FOR_MODULE_PLANNING

## Current guard
Planning only. No M04 implementation is authorized.

## Baseline evidence
- IRIS-WO-0007 / PR #25 merged.
- `main`: `c231dd61a210fe6d315126e755b4642a4fd2e9a3`.
- Post-merge Governance: run `35680287034`, job `106595594379`, PASS.
- Full suite: `2527/2527 OK`.
- `main-governance` remains required.

## S01 artifacts
- research: `planning/research/M04-S01-SCENE-CHARACTER-ASSET-IR-RESEARCH-2026-09-22.md`
- module plan: `planning/modules/M04-MULTIMODAL-SCENE-IR.md`
- technology registry: `planning/technology-registry/M04-TECHNOLOGIES.md`

## S01 boundary decisions
- IRIS-owned canonical IR, provider-neutral.
- dual graph topology.
- interface/payload split.
- M03 trace spine.
- M01 quality refs only.
- M05 identity/DNA refs only.
- M16 provider/workflow compiler boundary preserved.
- provider extensions quarantined from canonical core.

## S02 artifacts
- research: `planning/research/M04-S02-CAMERA-LIGHT-MATERIAL-SPATIAL-IR-RESEARCH-2026-09-22.md`
- module plan: S02 in `planning/modules/M04-MULTIMODAL-SCENE-IR.md`
- technologies: `IRIS-MIRX-031..060`

## S03 artifacts
- research: `planning/research/M04-S03-MOTION-AUDIO-MUSIC-NARRATIVE-IR-RESEARCH-2026-09-22.md`
- module plan: S03 in `planning/modules/M04-MULTIMODAL-SCENE-IR.md`
- technologies: `IRIS-MIRX-061..090`

## S04 artifacts
- research: `planning/research/M04-S04-REPRESENTATION-CAPABILITY-SEMANTIC-LOWERING-RESEARCH-2026-09-22.md`
- module plan: S04 in `planning/modules/M04-MULTIMODAL-SCENE-IR.md`
- technologies: `IRIS-MIRX-091..120`
- ownership resolution: M04 semantic legality/lowering only; M16 concrete provider/workflow compiler

## S05 artifacts
- research: `planning/research/M04-S05-VALIDATION-VERSIONING-ROUNDTRIP-RESEARCH-2026-09-22.md`
- module plan: S05 in `planning/modules/M04-MULTIMODAL-SCENE-IR.md`
- technologies: `IRIS-MIRX-121..150`

## Planning sessions gate
S01-S05 complete. M04 implementation remains blocked.

## Final Technology Review
- Status: `APPROVED_FOR_FORWARD_COMPATIBILITY`
- File: `planning/reviews/M04-FINAL-TECHNOLOGY-REVIEW.md`
- Detailed candidates: `IRIS-MIRX-001..150`
- Consolidated contract families: `F-M04-01..20`
- Ownership correction: M04 S04 = Representation Capability & Semantic Lowering; M16 = concrete Provider Compiler.

## Forward Compatibility Scan
- Status: `PASS_WITH_EXTENSION_PORTS`
- File: `planning/compatibility/M04-FORWARD-COMPATIBILITY-SCAN.md`
- Modules scanned: M05-M60
- Critical ownership conflicts remaining: 0
- Required extension/ref families: 20
- Explicit overlap shields: M28 MaterialIR, M31 Camera/Light IR, M36/M38 Timeline/Color, M48 quality authority
- M16 concrete Provider Compiler ownership preserved.

## Module Contract Freeze Candidate
- Target version: `m04-contract-v1.0`
- Status: `FREEZE_CANDIDATE`
- File: `planning/contracts/M04-MODULE-CONTRACT-FREEZE-CANDIDATE.md`
- Hard invariants: 80
- Consolidated technology families: 20
- Domain-neutral synthetic targets: 7
- Concrete Provider Compiler ownership: M16 only

## Next legal action
Run exact-head Governance and an **independent planning audit**. Only an APPROVED planning audit may promote this candidate to `FROZEN_APPROVED`.

M04 implementation remains blocked.

Do not implement M04.
