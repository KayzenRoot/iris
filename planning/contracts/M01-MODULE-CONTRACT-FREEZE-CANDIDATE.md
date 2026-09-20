# M01 — Module Contract Freeze Candidate

Status: `FREEZE_CANDIDATE`
Version: `m01-contract-v0.1`

## M01 implementation boundary

M01 implementation builds the domain-neutral quality kernel and contracts. It does NOT implement Blender, ComfyUI, game-specific anatomy, logo generation, WebGPU rendering or final domain judges. Those future modules plug into M01.

## Required kernel concepts
FidelityContract; FidelityDimension; QualityClass; Defect; SemanticZone; EvidenceRef; JudgeResult; QualityDecision; UncertaintyState; QualityDebt; evaluator/profile registries.

## Required behavior
- reject fatal defects independent of aggregate ranking;
- preserve UNKNOWN/HUMAN_REVIEW rather than fabricate certainty;
- version every contract/evaluator/evidence decision;
- support DRAFT/PREVIEW/REVIEW/MASTER/ARCHIVAL_MASTER;
- block invalid promotion;
- support pluggable judges and validators;
- store dimension-level evidence/confidence;
- support domain profiles without hardcoding game/web/image assumptions;
- produce deterministic decision records from identical normalized inputs;
- expose machine-readable evidence suitable for later HIVE/provenance storage.

## Explicitly deferred
Actual DreamSim/FLIP/TOPIQ runtime integration; Blender/ComfyUI; computer vision segmentation; game validators; web rendering; logo/vector implementation; human UI; model training; distributed compute.

## Acceptance gate
Implementation must pass unit/schema/state-machine/property tests and prove extension with at least three synthetic profiles:
1. generic image;
2. Nerim/isometric game asset;
3. logo/web/vector asset.

No synthetic profile needs real model inference at M01.

## STOP CONDITION
M01 implementation is complete only when the frozen kernel contract is implemented, tested, documented, evidence-bundled and independently reviewed APPROVED. No M02 implementation starts before this state.
