# M01 — Extreme Quality North Star & Fidelity System

Status: `SLOW_PLANNING_ACTIVE`

## Objective
Define what “extreme quality” means in IRIS as measurable, domain-aware, evidence-backed contracts before implementation.

## S01 — Quality dimensions and measurable fidelity vocabulary
### Decisions to resolve
- canonical Fidelity Vector dimensions;
- required vs optional dimensions by media type;
- fatal defect taxonomy;
- measurement units/ranges and confidence semantics;
- distinction among technical correctness, perceptual quality, aesthetic preference and creative intent.

### Technology focus
IRIS-QX-001 Fidelity Vector; IRIS-QX-002 Critical Defect Firewall; IRIS-QX-003 Perceptual Jury; IRIS-QX-008 Visual Delta Radar.

## S02 — Fidelity Contract and output classes
### Decisions to resolve
- contract schema;
- DRAFT/PREVIEW/REVIEW/MASTER/ARCHIVAL_MASTER;
- inheritance and promotion rules;
- project/asset/platform overrides;
- machine-readable acceptance obligations.

### Technology focus
IRIS-QX-005 Fidelity Contract Compiler; IRIS-QX-006 Quality Class Ladder; IRIS-QX-011 Quality Debt Ledger.

## S03 — Human-perceptual quality, visual review and approval boundaries
### Decisions to resolve
- where human review is mandatory;
- pairwise vs absolute review;
- reviewer evidence format;
- judge disagreement handling;
- project-specific calibration without hidden drift.

### Technology focus
DreamSim, FLIP, TOPIQ, CLIP-IQA, LPIPS; IRIS-QX-003 Perceptual Jury; IRIS-QX-004 Uncertainty Envelope; IRIS-QX-009 Quality Memory; IRIS-QX-010 Reviewer Calibration Loop.

## S04 — Quality budgets, acceptance thresholds and uncertainty
### Decisions to resolve
- threshold calibration by asset/domain;
- confidence/coverage requirements;
- hard gates vs soft ranking;
- 8 GB compute-quality policy;
- cost/time/VRAM optimization after fidelity constraints.

### Technology focus
IRIS-QX-004 Uncertainty Envelope; IRIS-QX-007 Quality Budget Allocator 2.0; IRIS-QX-013 Quality Pareto Frontier.

## S05 — Quality evidence, regression policy and North Star freeze
### Decisions to resolve
- Quality Evidence Bundle schema;
- golden/hidden benchmark policy;
- release regression gates;
- exception/debt policy;
- cross-modal fidelity preservation;
- quality-policy versioning.

### Technology focus
IRIS-QX-011 Quality Debt Ledger; IRIS-QX-012 Cross-Modal Fidelity Bridge; IRIS-QX-014 Adversarial Quality Sentinel; IRIS-QX-015 North Star Guard.

## Slow-planning gate
M01 SHALL NOT be marked complete from this overview. Each S01–S05 must be discussed in depth, its technologies accepted/modified/rejected, and the resulting decisions recorded before the next module begins.
