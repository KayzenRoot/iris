# M01 — Hard-Case Quality Gap Review

Date: 2026-09-20
Status: `REVIEW_COMPLETE_PROPOSALS_PENDING_PROMOTION`

## Why this review exists
Whole-image and whole-asset metrics can miss small regions with enormous perceptual impact. M01 therefore adds semantic-zone and domain-specific evidence before freezing the quality system.

## Findings

### Finding 1 — semantic locality was under-specified
Severity: HIGH if left unresolved.
Resolution: IRIS-QX-021 Semantic Critical Zone Matrix.

### Finding 2 — anatomy cannot be one human template
Severity: HIGH.
Resolution: IRIS-QX-022 Anatomy Constraint Lattice + IRIS-QX-029 Creature Morphology Grammar.

### Finding 3 — eye/gaze failures deserve an explicit validator
Severity: MAJOR.
Resolution: IRIS-QX-023 Ocular Life & Gaze Validator.

### Finding 4 — skin quality requires optical/material evidence
Severity: MAJOR.
Resolution: IRIS-QX-024 Dermal Fidelity Stack + IRIS-QX-032 Multi-Light Material Truth Test.

### Finding 5 — hair/fur needs attachment and temporal evidence
Severity: MAJOR.
Resolution: IRIS-QX-025 Strand & Groom Integrity Field.

### Finding 6 — cloth must be evaluated physically and perceptually
Severity: MAJOR.
Resolution: IRIS-QX-026 Cloth Contact & Fold Fidelity.

### Finding 7 — transparency/refraction/emission are special optical cases
Severity: MAJOR.
Resolution: IRIS-QX-027 Optical Boundary Validator.

### Finding 8 — facial quality must survive time
Severity: MAJOR.
Resolution: IRIS-QX-028 Microexpression Continuity Graph.

### Finding 9 — procedural detail must be reproducible without repetition
Severity: STANDARD.
Resolution: IRIS-QX-030 Procedural Determinism & Variation Auditor.

### Finding 10 — contact truth crosses multiple media domains
Severity: HIGH for animation/game assets.
Resolution: IRIS-QX-031 Contact Truth Field.

## Existing foundations evaluated
Blender Hair Curves/Geometry Nodes; Blender Cloth/Collision; Blender Principled BSDF/OpenPBR-compatible shading; OpenUSD Validation; NVIDIA Kaolin.

## Architectural decision
Do NOT expand the core Fidelity Vector with one dimension for every difficult material/body region. Keep the vector bounded and attach domain validators through the Semantic Critical Zone Matrix. This prevents metric sprawl while retaining strict evidence.

## Current verdict
`M01 CONTENT COMPLETE — PROMOTION NOT YET APPLIED`

No unresolved quality-domain gap found that requires changing the M01 five-session architecture. Candidate technologies QX-001..QX-032 remain subject to final disposition/promotion.
