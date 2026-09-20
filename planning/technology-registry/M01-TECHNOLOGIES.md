# IRIS 1.0 — M01 Technology Registry

Status: `PROPOSED_FOR_DISCUSSION`
Module: `M01 — Extreme Quality North Star & Fidelity System`
Rule: candidate proprietary technologies MUST NOT be described as novel/patentable until prior-art research is completed.

## Existing technology foundation

### EXT-M01-001 — DreamSim
**Type:** existing / perceptual similarity.
**What it does:** measures holistic perceptual similarity with stronger sensitivity to layout, pose, foreground objects, semantic content and color than purely pixel-level metrics.
**How IRIS uses it:** one sensor for reference fidelity, identity/style drift and candidate comparison. Never a sole approval gate.
**Why:** helps bridge low-level pixel metrics and human visual similarity.
**Risk:** domain bias and resolution/backbone limitations.
**Proof:** calibrate against IRIS human pairwise judgments per asset class.

### EXT-M01-002 — NVIDIA FLIP
**Type:** existing / perceptual render-difference metric.
**What it does:** produces perceptual difference/error maps designed to correspond to differences humans notice when alternating reference/test images.
**How IRIS uses it:** render regression, local defect heatmaps and before/after repair verification.
**Why:** spatial error maps are useful to tell M49 where quality changed.
**Risk:** requires a meaningful reference and controlled viewing assumptions.
**Proof:** compare FLIP maps with reviewer-marked defect regions.

### EXT-M01-003 — TOPIQ
**Type:** existing / image quality assessment.
**What it does:** top-down IQA using semantic information to reason about lower-level distortions.
**How IRIS uses it:** one no-reference/full-reference quality sensor depending qualified implementation.
**Risk:** benchmark performance does not imply reliable acceptance on every IRIS domain.
**Proof:** correlation with IRIS human MOS/pairwise benchmark.

### EXT-M01-004 — CLIP-IQA / CLIP perceptual priors
**Type:** existing / semantic quality assessment.
**What it does:** uses CLIP priors and prompt pairs to assess perceptual qualities/look-and-feel.
**How IRIS uses it:** semantic/aesthetic sensor for candidate ranking, never anatomy/geometry proof.
**Risk:** prompt sensitivity and learned preference bias.
**Proof:** per-domain calibration and adversarial examples.

### EXT-M01-005 — LPIPS / SSIM / PSNR baseline family
**Type:** existing / low-to-mid-level comparison baselines.
**What it does:** supplies complementary pixel/structural/perceptual-difference evidence.
**How IRIS uses it:** regression diagnostics and controlled reconstruction/render comparisons.
**Risk:** poor proxy for holistic generative-media quality when used alone.
**Proof:** retained only where each metric demonstrates predictive value.

## Proprietary candidate technologies

### IRIS-QX-001 — Fidelity Vector
**Purpose:** replace one misleading quality score with a typed multidimensional quality state.
**How it works:** every asset is evaluated on applicable axes such as intent adherence, identity, anatomy, geometry, composition, material/texture, lighting, temporal continuity, motion, technical integrity, brand/style, target-platform fitness and perceptual quality. Each dimension stores score/range, confidence, evidence, evaluator version and gate state.
**Benefit:** a beautiful render cannot hide a catastrophic hand, skeleton, mesh or motion defect behind an average.
**Dependencies:** M03 Fidelity Contract, M04 IR, M48 Quality Court, domain judges.
**Risk:** metric explosion and false precision.
**Proof:** ablation against single-score ranking; defect escape rate.
**Status:** PROPOSED.

### IRIS-QX-002 — Critical Defect Firewall
**Purpose:** make non-negotiable defects fail closed.
**How it works:** Fidelity Contract declares fatal classes per output type. A fatal defect such as broken anatomy, invalid topology, severe clipping, identity loss or corrupt alpha sets the candidate to REJECT independent of aggregate scores.
**Benefit:** eliminates quality averaging failures.
**Dependencies:** defect taxonomy, domain validators, M48.
**Risk:** overly aggressive false rejection.
**Proof:** measure catastrophic-defect escape rate and false reject rate.
**Status:** PROPOSED.

### IRIS-QX-003 — Perceptual Jury
**Purpose:** combine heterogeneous quality evidence without pretending one metric understands everything.
**How it works:** task-aware jury selects qualified sensors/judges, normalizes calibrated outputs, detects disagreement, records confidence and produces dimension-level evidence. No static universal weight vector.
**Benefit:** DreamSim, FLIP, IQA, structural validators and later vision judges can complement one another.
**Dependencies:** evaluator registry, calibration corpus, M51.
**Risk:** correlated judges can create false consensus.
**Proof:** ensemble vs individual judge human-agreement benchmark.
**Status:** PROPOSED.

### IRIS-QX-004 — Uncertainty Envelope
**Purpose:** make IRIS say “I do not know” when evidence is weak.
**How it works:** each quality decision carries confidence intervals/evidence coverage. High judge disagreement, out-of-distribution assets or missing validators widen uncertainty and can force HUMAN_REVIEW rather than PASS.
**Benefit:** avoids invented certainty.
**Dependencies:** Perceptual Jury, benchmark calibration.
**Risk:** excessive escalation.
**Proof:** calibration error, coverage vs accuracy, human escalation rate.
**Status:** PROPOSED.

### IRIS-QX-005 — Fidelity Contract Compiler
**Purpose:** convert creative intent into machine-testable quality obligations.
**How it works:** compiles project/asset intent, destination, references and output class into required dimensions, thresholds, fatal defects, judge set, review policy and evidence requirements.
**Benefit:** “extreme quality” becomes executable rather than rhetorical.
**Dependencies:** M03, M04, M16, M48.
**Risk:** incomplete contracts can encode the wrong target.
**Proof:** contract completeness tests + reviewer agreement.
**Status:** PROPOSED.

### IRIS-QX-006 — Quality Class Ladder
**Purpose:** separate iteration speed from final acceptance without silently degrading masters.
**How it works:** standard output classes DRAFT, PREVIEW, REVIEW, MASTER and ARCHIVAL_MASTER inherit progressively stricter evidence/gates. The creative target can remain identical while evaluation/render effort changes.
**Benefit:** efficient iteration on 8 GB hardware while preserving final quality.
**Dependencies:** Fidelity Contract, M10 adaptive execution, M50 Render Cascade.
**Risk:** accidental promotion from low class.
**Proof:** cryptographically/structurally block promotion without required evidence.
**Status:** PROPOSED.

### IRIS-QX-007 — Quality Budget Allocator 2.0
**Purpose:** spend compute where it creates visible quality.
**How it works:** allocate VRAM/time/candidates/upscale/repair/judge budget by Fidelity Vector deficits and marginal expected quality gain, rather than applying maximum compute to every stage.
**Benefit:** extreme final quality with less wasted GPU time.
**Dependencies:** M09/M10, M50, quality history.
**Risk:** predictor can underfund unusual defects.
**Proof:** approved-master quality per GPU-minute against fixed-budget baseline.
**Status:** PROPOSED.

### IRIS-QX-008 — Visual Delta Radar
**Purpose:** detect exactly what improved or regressed between asset revisions.
**How it works:** aligns revisions/references, generates multi-sensor spatial delta maps, attaches semantic regions and classifies changes by Fidelity Vector dimension.
**Benefit:** supports minimal repair instead of full regeneration.
**Dependencies:** FLIP/DreamSim/structural sensors, M49, provenance.
**Risk:** alignment artifacts can masquerade as regressions.
**Proof:** localization IoU/precision against human defect annotations.
**Status:** PROPOSED.

### IRIS-QX-009 — Quality Memory
**Purpose:** make the system learn project-specific quality expectations without silently changing canonical standards.
**How it works:** stores approved/rejected examples, reviewer reasons, judge disagreements and defect fingerprints as versioned evidence. Retrieval proposes calibration/context; it cannot overwrite Fidelity Contracts.
**Benefit:** recurring characters/brands/projects become more consistent over time.
**Dependencies:** M52 HIVE, M51 benchmarks, provenance.
**Risk:** preference drift and feedback loops.
**Proof:** blind human A/B evaluation with/without retrieved quality memory.
**Status:** PROPOSED.

### IRIS-QX-010 — Reviewer Calibration Loop
**Purpose:** turn human review into measurable calibration data.
**How it works:** pairwise comparisons, defect labels and accept/reject decisions are sampled into a benchmark set; evaluator correlations and thresholds are recalibrated per domain/version.
**Benefit:** automated judges progressively align with the actual production bar.
**Dependencies:** M51, M48, rights/privacy policy.
**Risk:** reviewer inconsistency.
**Proof:** inter-rater agreement and held-out prediction agreement.
**Status:** PROPOSED.

### IRIS-QX-011 — Quality Debt Ledger
**Purpose:** prevent temporary compromises from becoming invisible permanent defects.
**How it works:** any accepted exception records dimension, severity, reason, owner, affected derivatives, expiration/review trigger and downstream impact. MASTER may forbid debt classes entirely.
**Benefit:** quality compromises remain explicit and traceable.
**Dependencies:** Production Graph, provenance, checkpointing.
**Risk:** administrative noise.
**Proof:** zero untracked accepted exceptions in release audits.
**Status:** PROPOSED.

### IRIS-QX-012 — Cross-Modal Fidelity Bridge
**Purpose:** preserve the same creative identity across 2D → 3D → animation → video → web/game exports.
**How it works:** maps applicable Fidelity Vector dimensions and invariant anchors across modality transformations and requires evidence after each conversion.
**Benefit:** prevents a character/product from being excellent in concept art and drifting during modeling/rigging/render/export.
**Dependencies:** Asset DNA, Multimodal IR, M25–M42.
**Risk:** not all dimensions are directly comparable across modalities.
**Proof:** cross-modal identity/structure human benchmark + domain validators.
**Status:** PROPOSED.

### IRIS-QX-013 — Quality Pareto Frontier
**Purpose:** avoid optimizing quality, time and memory through a crude weighted average.
**How it works:** maintains non-dominated execution/candidate configurations across fidelity dimensions, GPU time, VRAM, latency and cost. Final selection first satisfies hard fidelity constraints, then chooses efficient Pareto candidates.
**Benefit:** especially valuable for 8 GB machines.
**Dependencies:** M08 benchmarks, M10 planner, M50.
**Risk:** search-space cost.
**Proof:** compare master approval rate and GPU-minutes against fixed presets.
**Status:** PROPOSED.

### IRIS-QX-014 — Adversarial Quality Sentinel
**Purpose:** find cases where metrics report high quality despite obvious human failure.
**How it works:** benchmark corpus deliberately includes metric traps: extra limbs, malformed hands, subtle identity swaps, reflections, repeated textures, text corruption, topology errors, foot sliding and temporal flicker. A release fails if the jury is confidently wrong on protected classes.
**Benefit:** protects IRIS from Goodhart's law and metric gaming.
**Dependencies:** M51, M24/M29/M30 domain corpora.
**Risk:** benchmark overfitting.
**Proof:** rotating hidden challenge set.
**Status:** PROPOSED.

### IRIS-QX-015 — North Star Guard
**Purpose:** prevent future performance/cost optimizations from quietly lowering quality.
**How it works:** stores versioned MASTER acceptance envelopes and golden cases. Any model/workflow/runtime change must demonstrate non-regression on protected quality dimensions or be explicitly approved as a quality-policy change.
**Benefit:** speed improvements cannot smuggle visual regressions into production.
**Dependencies:** M51, CI/release gates, provenance.
**Risk:** stale golden sets.
**Proof:** periodic corpus refresh + hidden benchmark tranche.
**Status:** PROPOSED.
