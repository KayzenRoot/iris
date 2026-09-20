# M01 — Extreme Quality North Star & Fidelity System

Status: `S01-S05_PROPOSED_COMPLETE_PENDING_REVIEW`

## S01 — Quality dimensions and measurable fidelity vocabulary

### Canonical Fidelity Vector v0.1
Every asset evaluates only applicable dimensions:
1. Intent adherence.
2. Identity/reference fidelity.
3. Anatomy/biological plausibility.
4. Geometry/topology integrity.
5. Silhouette/readability.
6. Composition/framing.
7. Material/PBR fidelity.
8. Texture/detail fidelity.
9. Lighting/shadow/contact fidelity.
10. Color/value hierarchy.
11. Style/brand consistency.
12. Motion/deformation quality.
13. Temporal continuity.
14. VFX clarity/integration.
15. Technical integrity.
16. Target-platform/runtime fitness.
17. Cross-modal consistency.
18. Perceptual finish.

Each dimension stores `value/range + confidence + evidence + evaluator version + gate state`.

### Defect classes
- `FATAL`: cannot be promoted regardless of other scores.
- `MAJOR`: blocks MASTER unless explicitly governed by an allowed exception class.
- `MINOR`: repairable imperfection; may block ARCHIVAL_MASTER.
- `OBSERVATION`: non-blocking evidence.

### Decision
No universal scalar quality score is authoritative.

## S02 — Fidelity Contract and output classes

### Output classes
- `DRAFT`: search/ideation; cheapest valid evidence.
- `PREVIEW`: coherent candidate for direction review.
- `REVIEW`: near-final candidate with domain validators.
- `MASTER`: production-approved artifact.
- `ARCHIVAL_MASTER`: highest-fidelity reproducible source from which delivery variants are derived.

### Fidelity Contract
A machine-readable contract binds:
- asset/project intent;
- output class;
- applicable Fidelity Vector dimensions;
- references/anchors;
- fatal/major defect classes;
- minimum evidence coverage/confidence;
- evaluator set;
- target platform/camera/delivery constraints;
- human-review requirements;
- allowed quality debt;
- promotion rules.

Promotion is monotonic only with required evidence; a DRAFT cannot be relabeled MASTER.

## S03 — Human-perceptual quality, review and approval boundaries

### Human review
Mandatory when:
- high-value MASTER/ARCHIVAL_MASTER policy requires it;
- identity/brand/art direction has insufficient machine confidence;
- evaluator disagreement exceeds calibrated bounds;
- asset is out-of-distribution;
- protected/adversarial defect class is uncertain.

### Review method
Prefer pairwise/A-B comparison where useful; absolute accept/reject and defect annotation remain available. Reviewer decision includes reason codes and marked regions/times when possible.

### Calibration
Automated evaluators are calibrated per domain against held-out human judgments. Project Quality Memory may inform evaluation but cannot silently mutate canonical thresholds.

## S04 — Quality budgets, thresholds and uncertainty

### Threshold model
No global threshold. Threshold profiles are versioned by domain/output class/Fidelity Contract.

### Hard vs soft
Fatal gates are hard. Qualified dimensions may participate in candidate ranking only after hard constraints pass.

### Uncertainty
IRIS stores confidence/evidence coverage. Low confidence is not converted to a low/high score; it produces `UNKNOWN` or `HUMAN_REVIEW`.

### Compute policy
Quality constraints are satisfied first. Among satisfying candidates/plans, IRIS seeks Pareto-efficient VRAM/time/cost. 8 GB hardware may use slower/offloaded/tiled/cascaded execution but does not silently inherit lower MASTER thresholds.

## S05 — Evidence, regression policy and North Star freeze

### Quality Evidence Bundle
Every promoted MASTER records:
- Fidelity Contract version;
- Fidelity Vector evidence;
- evaluator/model/workflow versions;
- defects and repairs;
- uncertainty/disagreement;
- human decisions where applicable;
- provenance;
- target-platform checks;
- benchmark/golden references when applicable.

### Regression
Model/workflow/runtime upgrades must pass protected golden + rotating hidden/adversarial cases for affected domains. A performance optimization cannot be promoted when it violates protected quality dimensions without an explicit quality-policy decision.

### Cross-modal rule
2D→3D→rig→animation→render→game/web delivery transformations revalidate applicable invariants rather than assuming upstream quality survives conversion.

### North Star
Extreme quality means maximum validated fidelity to the intended artifact and its real viewing/use conditions, not maximum polygon count, texture resolution, render time or model size.

## M01 proposed disposition
S01–S05 are now specified at planning depth sufficient for review. Technologies remain individually PROPOSED until the M01 review promotes accepted entries.


## Hard-case gap review addendum

M01 explicitly treats the following as protected quality regions/domains:
- hands, feet, face, eyes and mouth;
- skin and subsurface/material response;
- hair/fur roots, groom flow and motion;
- cloth contact, collision, folds and temporal stability;
- transparent/refractive/emissive boundaries;
- facial microexpressions;
- non-human creature morphology;
- procedural repetition/determinism;
- physical contact between characters, props and environment;
- material behavior under multiple lighting conditions.

These are not separate global Fidelity Vector dimensions by default. They are semantic zones/domain validators that attach stricter evidence to existing dimensions. This avoids an unbounded vector while preserving high-risk quality checks.

### Added candidate technologies
IRIS-QX-021 through IRIS-QX-032 are admitted to M01 review as PROPOSED.
