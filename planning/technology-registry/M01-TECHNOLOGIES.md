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


### IRIS-QX-016 — Gameplay Distance Fidelity
**Purpose:** judge game assets at actual gameplay distance/angle as well as beauty-closeup distance.
**How it works:** standardized multi-scale/camera renders evaluate silhouette, identity, equipment/material distinction, pose and VFX clarity.
**Benefit:** production effort targets quality players can actually perceive.
**Dependencies:** M31 camera/render, M35 engine delivery, M51 benchmarks.
**Risk:** camera profiles must represent real gameplay.
**Proof:** correlation with player/reviewer recognition and readability tests.
**Status:** PROPOSED.

### IRIS-QX-017 — Isometric Readability Field
**Purpose:** map readability of important game entities across high-angle/isometric scenes.
**How it works:** projection-space analysis combines value/color/edge/depth/semantic separation to identify background merges and occlusion zones.
**Benefit:** stronger gameplay readability without flattening visual richness.
**Dependencies:** M31, M35, scene segmentation.
**Risk:** artistic contrast can be over-optimized.
**Proof:** controlled recognition-time/error benchmark.
**Status:** PROPOSED.

### IRIS-QX-018 — Detail Survival Analyzer
**Purpose:** spend art/render budget on detail that survives actual delivery conditions.
**How it works:** compares master detail through target resolution, camera distance, LOD, mip/compression and display profiles; classifies visible/lost/aliasing detail.
**Benefit:** better perceived quality per polygon/texel/GPU cost.
**Dependencies:** M27, M28, M34, M35.
**Risk:** target profiles can change.
**Proof:** perceptual A/B + runtime budget comparison.
**Status:** PROPOSED.

### IRIS-QX-019 — VFX Occlusion Budget
**Purpose:** preserve gameplay information under rich effects.
**How it works:** tracks temporal screen-space overlap of important silhouettes/telegraphs with particles, bloom, smoke, decals and emissives.
**Benefit:** cinematic VFX without unreadable combat.
**Dependencies:** M32, M35, M37.
**Risk:** semantic importance labeling.
**Proof:** combat-recognition and telegraph-response tests.
**Status:** PROPOSED.

### IRIS-QX-020 — Isometric Motion Legibility Score
**Purpose:** ensure high-quality motion remains readable from gameplay camera.
**How it works:** evaluates projected pose silhouette, anticipation, action direction, contact, foot sliding, timing and transition clarity at target scale.
**Benefit:** prevents beautiful close-up animation that reads poorly in actual play.
**Dependencies:** M29, M30, M35.
**Risk:** genre/action-specific calibration.
**Proof:** action-recognition benchmark + motion defect corpus.
**Status:** PROPOSED.


## M01 hard-case gap review — 2026-09-20

### EXT-M01-006 — Blender Hair Curves / Geometry Nodes
**Type:** existing.
**What it does:** procedural hair/fur generation, guide maps, clumping/curl/noise and surface attachment/validity through curve-based workflows.
**IRIS use:** foundation for groom generation and deterministic groom QA; viewport density may be reduced independently of final render density.
**Proof:** groom attachment, silhouette, deformation and performance benchmarks.

### EXT-M01-007 — Blender Cloth / Collision / Self-Collision
**Type:** existing.
**What it does:** cloth simulation with object collision, optional self-collision, collision quality and bakeable simulation.
**IRIS use:** physical-cloth reference and distance-aware simulation qualification.
**Proof:** penetration, stability, silhouette and runtime tests.

### EXT-M01-008 — Blender Principled BSDF / OpenPBR-compatible shading
**Type:** existing.
**What it does:** layered physically based surface model with diffuse/metal/subsurface/transmission/coat/sheen/thin-film behavior; skin-oriented Random Walk is available in Cycles.
**IRIS use:** material validation reference for skin, glass, cloth, metal and layered materials.
**Proof:** controlled light-rig material turntables and cross-renderer comparisons.

### EXT-M01-009 — OpenUSD Validation
**Type:** existing.
**What it does:** extensible core/schema/client validation rules for robust interoperable USD assets.
**IRIS use:** structural validation layer for USD/DCC exchange and custom IRIS rules.
**Proof:** invalid-asset corpus and round-trip tests.

### EXT-M01-010 — NVIDIA Kaolin
**Type:** existing.
**What it does:** GPU-accelerated 3D representations, differentiable rendering/conversion and geometric losses/operations.
**IRIS use:** research/benchmark toolbox for geometric similarity, mesh and projection-space validation where qualified.
**Proof:** compare against Blender/OpenUSD validators and human-reviewed geometry defects.

### IRIS-QX-021 — Semantic Critical Zone Matrix
**Purpose:** prevent whole-asset averages from hiding failures in high-risk semantic regions.
**How it works:** asset classes declare semantic zones such as eyes, mouth, hands, feet, face, joints, hair roots, cloth contacts, weapon grip and transparent boundaries. Each zone gets applicable Fidelity Vector dimensions and stricter defect policies.
**Benefit:** malformed fingers or dead eyes cannot disappear inside an excellent full-image score.
**Dependencies:** segmentation/landmarks, M24/M29/M39.
**Risk:** zone detection errors.
**Proof:** protected-zone defect escape rate.
**Status:** PROPOSED.

### IRIS-QX-022 — Anatomy Constraint Lattice
**Purpose:** validate humans, humanoids and creatures beyond generic image aesthetics.
**How it works:** combines skeleton/landmark topology, joint limits, bilateral/proportional constraints, contact state and species/body-plan profiles. Supports intentional stylization through explicit anatomy profiles rather than one universal human template.
**Benefit:** targets extra/missing/misaligned limbs, impossible joints and deformation.
**Dependencies:** M05 Asset DNA, M29, M30.
**Risk:** over-constraining stylized/non-human anatomy.
**Proof:** anatomy challenge corpus across human/stylized/creature classes.
**Status:** PROPOSED.

### IRIS-QX-023 — Ocular Life & Gaze Validator
**Purpose:** eliminate dead, crossed, floating or materially implausible eyes.
**How it works:** evaluates binocular convergence, gaze target consistency, eyelid/eyeball contact, corneal catchlights/reflections, sclera/iris/pupil geometry and temporal gaze continuity.
**Benefit:** major improvement to perceived character life.
**Dependencies:** M29, M31, M39.
**Risk:** stylized eyes need alternate profiles.
**Proof:** human gaze-plausibility benchmark + geometric checks.
**Status:** PROPOSED.

### IRIS-QX-024 — Dermal Fidelity Stack
**Purpose:** validate skin as a layered optical/material system rather than a flat texture.
**How it works:** evaluates macro color/value, roughness variation, pore/micro-normal scale, subsurface response, specular breakup and distance survival under standardized lighting.
**Benefit:** reduces wax/plastic skin while avoiding wasteful invisible microdetail.
**Dependencies:** M28, M31, Detail Survival Analyzer.
**Risk:** skin tone/lighting bias in learned evaluators.
**Proof:** diverse calibrated material/lighting corpus and human review.
**Status:** PROPOSED.

### IRIS-QX-025 — Strand & Groom Integrity Field
**Purpose:** validate hair/fur attachment, flow, silhouette and motion.
**How it works:** tracks root validity, guide continuity, density/clump fields, scalp penetration, flyaway budget, silhouette, temporal coherence and LOD/detail survival.
**Benefit:** catches floating hair, broken roots, noisy fur and unstable animation.
**Dependencies:** Blender Hair Curves, M28/M30/M32.
**Risk:** hairstyle diversity and simulation cost.
**Proof:** groom defect corpus + attachment and temporal tests.
**Status:** PROPOSED.

### IRIS-QX-026 — Cloth Contact & Fold Fidelity
**Purpose:** validate garments/capes against body, motion and material intent.
**How it works:** combines penetration/self-intersection tests, contact gaps, stretch/compression, fold-scale plausibility, pin/constraint behavior and temporal stability. Simulation fidelity may scale with actual viewing distance.
**Benefit:** avoids cloth-through-body, exploding cloth and rubbery fabric.
**Dependencies:** Blender Cloth, M29/M30/M32.
**Risk:** expensive simulation if applied indiscriminately.
**Proof:** standardized motion/cloth torture scenes at multiple camera distances.
**Status:** PROPOSED.

### IRIS-QX-027 — Optical Boundary Validator
**Purpose:** protect transparent, refractive, emissive and thin-film materials that ordinary RGB similarity can misjudge.
**How it works:** evaluates silhouette boundary, alpha coverage, refraction continuity, IOR/transmission behavior, volume absorption, emission clipping, reflection consistency and compositing halos.
**Benefit:** better glass, holograms, hair cards, particles and translucent assets.
**Dependencies:** M28/M31/M32, linear color pipeline.
**Risk:** renderer-specific behavior.
**Proof:** canonical optical material test scenes.
**Status:** PROPOSED.

### IRIS-QX-028 — Microexpression Continuity Graph
**Purpose:** preserve believable facial acting across time.
**How it works:** represents facial state as temporally constrained regions/controls, checking asymmetry, eye-mouth timing, blink dynamics, lip/teeth intersections, expression transitions and identity preservation.
**Benefit:** avoids frame-perfect faces that become uncanny in motion.
**Dependencies:** M29/M30/M37/M39.
**Risk:** cultural/individual variation.
**Proof:** temporal facial benchmark + human naturalness review.
**Status:** PROPOSED.

### IRIS-QX-029 — Creature Morphology Grammar
**Purpose:** support extreme quality for non-human creatures without forcing human anatomy.
**How it works:** Asset DNA defines body-plan grammar: limb count, attachment graph, locomotion/contact rules, symmetry/asymmetry, joint families, mass distribution and intentional exceptions.
**Benefit:** validates dragons, quadrupeds, insects and fantasy creatures coherently.
**Dependencies:** M05, M25/M29/M30.
**Risk:** unusual designs may not fit predefined grammars.
**Proof:** diverse creature corpus + designer override tests.
**Status:** PROPOSED.

### IRIS-QX-030 — Procedural Determinism & Variation Auditor
**Purpose:** ensure procedural detail is reproducible but not visibly repetitive.
**How it works:** records seeds/graphs/inputs, checks deterministic rebuilds, detects tiling/repetition/correlation artifacts and measures controlled variation envelopes.
**Benefit:** procedural worlds/materials/hair/VFX can be regenerated exactly without looking mechanically repeated.
**Dependencies:** M06/M28/M32/M53.
**Risk:** perceptual repetition detection is domain-sensitive.
**Proof:** exact rebuild hash/evidence + repetition challenge corpus.
**Status:** PROPOSED.

### IRIS-QX-031 — Contact Truth Field
**Purpose:** unify believable physical contact across feet, hands, weapons, cloth, props and environment.
**How it works:** tracks signed distance/contact patches, normal alignment, penetration, hover gaps, sliding velocity and temporal persistence around semantically expected contacts.
**Benefit:** catches floating feet, loose weapon grips and subtle intersections across stills and animation.
**Dependencies:** M29/M30/M32, geometry/depth evidence.
**Risk:** soft/deformable contact requires tolerance models.
**Proof:** contact torture suite and annotated animation corpus.
**Status:** PROPOSED.

### IRIS-QX-032 — Multi-Light Material Truth Test
**Purpose:** stop materials from being approved because they look good under one flattering light.
**How it works:** every qualified material/character master is rendered under a compact canonical light rig set: neutral studio, grazing, hard directional, soft diffuse, dark/high-contrast and environment profile. Material dimensions are compared for physically/art-directably plausible response.
**Benefit:** exposes waxy skin, broken normals, fake roughness, bad transparency and texture baking artifacts.
**Dependencies:** M28/M31.
**Risk:** render cost.
**Proof:** defect discovery uplift vs single-light review.
**Status:** PROPOSED.
