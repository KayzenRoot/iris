# IRIS-WO-0003 — M01 Quality Kernel Implementation

Status: `READY_FOR_EXECUTOR`
Risk: `STANDARD`
Frozen contract: `m01-contract-v1.0`

## OBJECTIVE
Implement the domain-neutral IRIS Quality Kernel defined by M01 without implementing domain-specific media engines.

## CONTEXT
IRIS is a complete multimodal production system, not game-specific. The quality kernel must later serve image, 2D/2.5D/3D, game/isometric assets, logos/brand/vector, premium web/Web3D, dashboards/cockpits, motion/VFX, video, digital humans and audio/narrative extensions.

## SOURCES TO READ — ORDER
1. docs/project-brain/00-SOURCE-HIERARCHY.md
2. docs/project-brain/13-CHECKPOINT.md
3. planning/contracts/M01-MODULE-CONTRACT-FREEZE-CANDIDATE.md
4. planning/compatibility/M01-FORWARD-COMPATIBILITY-SCAN.md
5. planning/modules/M01-EXTREME-QUALITY.md
6. planning/reviews/M01-FINAL-TECHNOLOGY-REVIEW.md
7. planning/technology-registry/M01-TECHNOLOGIES.md
8. docs/product/IRIS-PRODUCT-NORTH-STAR.md
9. docs/product/IRIS-CREATIVE-DOMAIN-COVERAGE.md
10. docs/product/NERIM-VISUAL-QUALITY-REFERENCE.md
11. existing repository architecture/tests/tooling before changing code.

## SCOPE
Implement a small, typed, deterministic, versioned quality kernel with:
- FidelityContract
- FidelityDimension
- QualityClass
- Defect and severity
- SemanticZone
- EvidenceRef
- JudgeResult
- QualityDecision
- UncertaintyState
- QualityDebt
- QualityJudge port
- AssetValidator port
- evaluator registry
- domain/profile registry
- promotion/decision engine
- serialization/schema validation appropriate to repository language/architecture
- documentation and examples.

## REQUIRED SEMANTICS
1. Fatal defect rejects independently of aggregate score.
2. Missing/insufficient evidence may yield UNKNOWN or HUMAN_REVIEW; never fabricate certainty.
3. Every contract, judge/evaluator and decision is version-identifiable.
4. Output classes: DRAFT, PREVIEW, REVIEW, MASTER, ARCHIVAL_MASTER.
5. Invalid promotion is blocked.
6. Judges/validators are pluggable and vendor-neutral.
7. Evidence/confidence is dimension-level.
8. Domain profiles extend the kernel without game/web/image hardcoding.
9. Identical normalized inputs produce deterministic decision records.
10. Quality debt is explicit and policy-governed.
11. No single scalar score can override a failed hard gate.
12. Kernel types must not import Blender, ComfyUI, DreamSim, FLIP, WebGPU or model-provider SDKs.

## REQUIRED SYNTHETIC PROFILES
Implement fixtures/examples/tests proving extension with:
A. generic image profile;
B. Nerim/isometric game asset profile;
C. logo/web/vector profile.

These are contract tests, not real inference.

## OUT OF SCOPE
- real DreamSim/FLIP/TOPIQ/CLIP-IQA execution;
- Blender/ComfyUI integration;
- model download/inference;
- CV segmentation;
- real anatomy/groom/cloth validators;
- real logo/SVG renderer;
- WebGL/WebGPU runtime;
- UI/dashboard;
- distributed compute;
- HIVE runtime mutation;
- M02 implementation.

## ARCHITECTURE RULES
- Inspect repository before choosing package/file layout.
- Reuse existing conventions; do not introduce a framework without necessity.
- Keep domain-neutral core separate from synthetic profile fixtures.
- Prefer explicit immutable/value-object style where practical.
- Version schemas/contracts.
- Fail closed on invalid state transitions.
- Error types/messages must be actionable.
- Avoid premature abstraction beyond known ports.
- No hidden network dependency in unit tests.

## TESTS
At minimum:
- schema/type construction validation;
- serialization round trip;
- deterministic decision;
- fatal defect rejection;
- major/minor/observation policy;
- UNKNOWN/HUMAN_REVIEW behavior;
- promotion state-machine tests;
- quality debt tests;
- judge disagreement/uncertainty tests;
- evaluator/profile registration/version collision tests;
- three synthetic profile contract tests;
- malformed/untrusted extension metadata tests;
- existing repository tests;
- lint/typecheck/build where configured.

Use property-based tests if the existing stack supports them without unjustified dependency expansion; otherwise table-driven/state-transition coverage is acceptable.

## DELIVERABLES
- production code;
- tests/fixtures;
- public/internal API documentation;
- architecture note if implementation choices require it;
- Evidence Bundle with exact commands/results;
- proposed Checkpoint Delta;
- branch/commit/PR suitable for independent review.

## EVIDENCE BUNDLE
Record:
- base/head SHA;
- changed files;
- design decisions;
- tests;
- lint/typecheck/build;
- failures encountered/fixed;
- risks/deferred work;
- proof that no domain SDK leaked into kernel;
- proof for all three synthetic profiles.

## REVIEW FORMAT
Return concise Brazilian Portuguese summary with:
- what was implemented;
- exact test/build results;
- files changed;
- deviations, if any;
- risks;
- PR/commit identifiers;
- STOP CONDITION status.

## STOP CONDITION
STOP after M01 Quality Kernel implementation is committed/pushed and PR/evidence are ready for independent review. Do NOT merge. Do NOT start M02. Do NOT implement real domain evaluators/providers. If any acceptance criterion cannot be proven, report BLOCKED instead of weakening the contract.
