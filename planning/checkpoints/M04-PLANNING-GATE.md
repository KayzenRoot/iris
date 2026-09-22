# IRIS M04 Planning Gate

Status: `S03_COMPLETE_S04_NEXT`
Issue: `#26`
Branch: `m04-multimodal-ir-planning`
Authorized main baseline: `c231dd61a210fe6d315126e755b4642a4fd2e9a3`

## Sessions
- S01 — Scene, Character and Asset IR: COMPLETE_FOR_MODULE_PLANNING
- S02 — Camera, Lighting, Material and Spatial IR: COMPLETE_FOR_MODULE_PLANNING
- S03 — Motion, Audio, Music and Narrative IR: COMPLETE_FOR_MODULE_PLANNING
- S04 — Provider Compiler and capability downgrade planning: NEXT
- S05 — IR validation, versioning and round-trip guarantees: NOT_STARTED

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

## Next legal action
Continue slow planning with **S04 — Provider Compiler and capability downgrade planning**.

Do not implement M04.
