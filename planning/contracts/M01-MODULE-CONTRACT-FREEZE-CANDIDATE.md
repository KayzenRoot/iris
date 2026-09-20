# M01 — Module Contract Freeze Candidate

Status: `FROZEN_APPROVED`
Version: `m01-contract-v1.0`

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


## Freeze evidence
- Planning audit head: `a1ad9ae33d6953f882302e9c23cafdad7d778b18`
- Governance run: `35520010518` — SUCCESS
- Diff audit: 5 planning commits, 11 planning/docs files, no product implementation.
- Forward Compatibility Scan: PASS_WITH_EXTENSION_PORTS.
- Final Technology Review: APPROVED_FOR_CONTRACT_FREEZE.

Any semantic change after this freeze requires a versioned contract amendment and renewed compatibility review.
