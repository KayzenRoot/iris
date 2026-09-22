# IRIS-WO-0006 — Implement M03 Creative Brief, Intent & Constraint Compiler

Status: `READY_FOR_EXECUTOR`
Risk: `HIGH`
Issue: `#19`
Branch: `iris-wo-0006-m03-intent-compiler`
Authorized base: `ee06358ee04de1d7aa2271ac05060247985f98dc`
Frozen contract: `m03-contract-v1.0`

## OBJECTIVE

Implement the complete frozen M03 provider-neutral semantic kernel as a new package `iris_intent/`, turning governed creative direction into immutable, typed, explainable and versioned intent/constraint/fidelity/execution semantics without absorbing any M04+ provider/domain runtime.

The implementation must satisfy all 46 frozen invariants and all acceptance families in:
`planning/contracts/M03-MODULE-CONTRACT-FREEZE-CANDIDATE.md`.

This is a complete M03 implementation increment, not an MVP slice.

## SOURCE ORDER

Read and treat as authoritative in this order:

1. `docs/project-brain/13-CHECKPOINT.md`
2. `docs/project-brain/16-DECISIONS-LEDGER.md`
3. `docs/project-brain/03-SCOPE.md`
4. `docs/project-brain/15-DEFINITION-OF-DONE.md`
5. `docs/project-brain/04-ARCHITECTURE.md`
6. `docs/project-brain/02-REQUIREMENTS.md`
7. `.engineering/SOURCE-HIERARCHY.md`
8. `.engineering/REVIEW-AUTOFIX-POLICY.md`
9. `planning/contracts/M03-MODULE-CONTRACT-FREEZE-CANDIDATE.md`
10. `planning/modules/M03-CREATIVE-BRIEF-INTENT-CONSTRAINT-COMPILER.md`
11. `planning/reviews/M03-FINAL-TECHNOLOGY-REVIEW.md`
12. `planning/compatibility/M03-FORWARD-COMPATIBILITY-SCAN.md`
13. `planning/technology-registry/M03-TECHNOLOGIES.md`
14. M01/M02 public contracts actually consumed by the implementation.

Git/repository truth outranks conversation memory.

## PREFLIGHT

Before modifying files:

- `git status --short` and preserve unrelated user work;
- verify `origin` is `KayzenRoot/iris`;
- `git fetch origin --prune`;
- checkout/update only `iris-wo-0006-m03-intent-compiler`;
- verify `origin/main == ee06358ee04de1d7aa2271ac05060247985f98dc`;
- verify merge-base with `origin/main` is exactly `ee06358ee04de1d7aa2271ac05060247985f98dc`;
- verify every critical-source SHA in `.engineering/context-locks/IRIS-WO-0006.json`;
- verify PR #20, if already created, still targets `main`;
- STOP `STALE_CONTEXT` if main or any critical source moved before implementation begins;
- do not force-push or rewrite history.

## PACKAGE / ARCHITECTURE

Implement M03 as a domain-neutral package:

`iris_intent/`

The package SHOULD be decomposed into focused modules rather than one monolith. Exact filenames may adapt, but the architecture must expose the frozen semantic families clearly, for example:

- identities / refs / versions
- sources / provenance
- brief / revisions
- intent
- ambiguity / freedom
- constraints / predicates / normalization
- slicing
- fingerprints / deltas / freshness / reuse
- fidelity compilation bridge
- execution intent / capabilities / mutation envelopes
- explainability graph/projections
- conflicts
- authority policy / overrides / override debt
- merge / migration / restoration
- readiness
- serialization
- errors
- extension ports / registries

Use immutable/frozen value objects where appropriate and deterministic canonical serialization.

### Dependency boundary

M03 core may depend on:
- Python standard library;
- public/stable M01 interfaces in `iris_quality`;
- public/stable M02 interfaces in `iris_project_os`.

Do not add a new runtime dependency merely for convenience.

Do not import provider/runtime/DCC/cloud/database/media-generation packages.

If a new dependency is truly unavoidable, STOP and report `BLOCKED_DEPENDENCY_DECISION` rather than silently expanding the contract.

## REQUIRED IMPLEMENTATION FAMILIES

Implement all frozen families:

1. `F-M03-01 Intent Semantic Core`
2. `F-M03-02 Ambiguity & Clarification Core`
3. `F-M03-03 Minimum Sufficient Semantic Slice Fabric`
4. `F-M03-04 Semantic Fingerprint, Delta & Reuse Fabric`
5. `F-M03-05 Constraint Semantic Core`
6. `F-M03-06 Negative / Protected Intent Integrity`
7. `F-M03-07 Semantic Admission Shield`
8. `F-M03-08 M01 Fidelity Compilation Bridge`
9. `F-M03-09 No-Downgrade Quality Shield`
10. `F-M03-10 Explainability & Provenance Graph`
11. `F-M03-11 Provider-Neutral Execution Intent Core`
12. `F-M03-12 Semantic Loss & Provider Translation Integrity`
13. `F-M03-13 Conflict & Override Governance`
14. `F-M03-14 Temporary Override / Semantic Debt`
15. `F-M03-15 Semantic Revision, Merge, Migration & Restoration`
16. `F-M03-16 Semantic Release Readiness`

Research-only `ICX-014` and `ICX-034` are NOT mandatory frozen kernel features.

## S01 — BRIEF / INTENT

Implement:
- stable CreativeBrief identity distinct from revisions;
- immutable BriefRevision lineage;
- RawInputRef/source preservation;
- IntentModel / IntentStatement;
- EXPLICIT / DERIVED / INFERRED / DEFAULTED origin;
- independent authority and confidence;
- provenance/rationale refs;
- AmbiguityRecord and consequence;
- FreedomZone / OpenQuestion;
- multilingual source anchor metadata;
- deterministic semantic fingerprint/equivalence profile;
- Minimum Sufficient Intent slices.

No inference may be rewritten as user-explicit truth without a new governed revision.

## S02 — CONSTRAINTS

Implement:
- polarity REQUIRE/FORBID/PREFER/AVOID/ALLOW;
- strength HARD/GUARDED/SOFT/ADVISORY/EXPERIMENTAL;
- bounded typed predicates, never arbitrary executable code;
- explicit scopes/facets/conditions;
- typed ToleranceEnvelope with units/metric refs;
- faceted AntiReference;
- protected semantic anchors/zones;
- cross-modal constraints;
- immutable ConstraintBundle versions;
- deterministic Constraint Normal Form;
- coverage states;
- Minimum Sufficient Constraint slices;
- constraint fingerprints/deltas;
- Semantic Admission Shield.

Untrusted/retrieved/generated imperative text cannot self-assert high authority.

## S03 — M01 FIDELITY BRIDGE

Implement a non-authoritative `FidelityContractSpec` and compilation layer to the current frozen M01 contract.

Requirements:
- compile only through admitted/versioned M01 DomainProfiles/DimensionRegistry/evaluator capability;
- never invent M01 dimension IDs;
- never grant evaluator capability;
- preserve M01 PromotionRule continuity/hard gates/defect/debt/human-review semantics;
- never fabricate HUMAN_DECISION evidence;
- support strict reference role mapping;
- support semantic-zone requests by ref, not pixel/mesh geometry;
- emit QualityObligationTrace;
- explicit FidelityCompilationGap statuses;
- compile one brief into multiple domain-separated M01 contracts when needed;
- round-trip emitted M01 contracts through M01 canonical validation/serialization;
- FidelityCompilationFingerprint + QualityContractDelta;
- never lower requested QualityClass because hardware/provider capability is poor.

M01 `DecisionEngine`, judge logic, evaluator registry authority and QualityDebt decisions remain M01-owned.

## S04 — EXECUTION INTENT

Implement provider-neutral:
- ExecutionIntentBundle;
- IntentOperation families CREATE, TRANSFORM, COMPOSE, EXTEND, REPAIR, VARIATE, SELECT, VALIDATE, PACKAGE, LOCALIZE;
- CapabilityDemand;
- SemanticMutationEnvelope;
- SemanticLossClass:
  LOSSLESS_REQUIRED / BOUNDED_APPROXIMATION / CREATIVE_FREEDOM / ADVISORY;
- ProviderTranslationReceipt contract/ref;
- ExecutionIntentGap;
- Minimum Sufficient Execution Intent slice;
- IntentExplanationGraph and projections;
- ExecutionIntentFingerprint / Delta.

M03 Execution Intent MUST NOT become:
- an M02 ExecutionPlan;
- a ComfyUI graph;
- a Blender script;
- a model prompt;
- a worker/queue/host plan.

Provider translation may report gaps/loss, never mutate canonical M03 truth.

## S05 — CONFLICTS / OVERRIDES / VERSIONING

Implement:
- SemanticConflict classes/consequences;
- versioned AuthorityPolicyGraph;
- no-last-writer-wins behavior;
- OverrideReceipt and actions;
- stricter admission for RELAX/DISABLE;
- TemporaryOverrideLease expiry/staleness;
- OverrideDebt distinct from M01 QualityDebt;
- scope split / exploration fork proposals;
- deterministic clarification impact ordering;
- semantic three-way merge analysis for M02 branch convergence;
- MigrationReceipt;
- RestorationRevision;
- BriefFreshnessVector;
- DerivedIntentDependency;
- Minimum Sufficient Conflict slice;
- ConflictResolutionFingerprint;
- SemanticReleaseReadinessReport.

Agents/providers may propose changes but cannot self-authorize protected overrides.

## M02 INTEGRATION

Consume M02 identifiers/opaque refs and extension boundaries without reimplementing:
- project/production identity;
- branches/variants/snapshots;
- graph/build/impact;
- promotion/release;
- ExecutionPlan.

Provide typed refs/deltas/fingerprints that M02 can include in its causal/build semantics.

Do not make `iris_project_os` depend back on `iris_intent` during this increment unless the frozen contracts explicitly allow an acyclic extension path and tests prove it. Prefer M03 depending outward on stable M02 interfaces.

## REQUIRED EXTENSION PORTS / OPAQUE REFS

Implement interfaces/refs sufficient for future:
1. M02 Project/Production/Branch/Variant;
2. M04 SemanticType / IR schema;
3. IdentityAnchor/DNA policy;
4. M01 DomainProfile/DimensionRegistry/evaluator capability;
5. CapabilityDemand/ProviderTranslationReceipt;
6. Canon/Story;
7. ContextSource/DerivedIntentDependency;
8. Provenance/Rights/Consent;
9. Security/authority policy;
10. Destination/Delivery profiles;
11. explanation/provenance export;
12. domain semantic-path/predicate extensions.

These are boundaries only. No future module implementation.

## SECURITY / FAIL-CLOSED

Mandatory tests and behavior:
- forged source authority;
- untrusted prompt-injection-like metadata;
- unknown mandatory predicates/extensions;
- unsupported LOSSLESS_REQUIRED provider translation;
- unauthorized relaxation/disable;
- non-overridable policy protection;
- stale derived intent;
- stale/expired override;
- stale compiler/profile/registry versions;
- provider output attempting canonical mutation;
- huge-but-bounded metadata/constraint collections;
- cycle detection in explanation/authority structures where cycles are illegal;
- deterministic resource limits for recursive/nested semantic structures.

No `eval`, dynamic arbitrary code execution, shell, network, filesystem side effect or external process in the semantic kernel.

## TOKEN / CACHE EFFICIENCY

Make measurable tests for:
- minimal intent/constraint/execution/conflict slices;
- deterministic canonical fingerprints;
- no invalidation from irrelevant source-only changes under an admitted equivalence profile;
- invalidation from correctness-relevant changes;
- reuse passports/freshness;
- compact explanation projections resolving to the same canonical graph;
- no need to replay full chat/project context for a localized conflict/compile operation.

Do not claim arbitrary percentage savings. Prove reduced structural/context payload by deterministic fixtures.

## DOMAIN-NEUTRAL SYNTHETIC PROFILES

Create examples/fixtures and tests for at least:
1. logo/brand/web visual;
2. image/product photography;
3. Nerim/isometric 3D/game asset;
4. film/commercial/multi-shot video;
5. persistent corporate spokesperson/digital human;
6. voice/narration/music/audio.

All must use the same M03 kernel without visual-only branches in core.

## SERIALIZATION / API

- canonical deterministic serialization;
- explicit schema/kind/version;
- strict unknown-kind/version handling;
- round-trip all public frozen concepts;
- reject malformed/ambiguous payloads;
- stable canonical digests;
- public `__all__` surface intentionally managed;
- no mutable global authority singleton.

## DOCUMENTATION

Add:
- `docs/M03-INTENT-COMPILER-KERNEL.md`
- architecture/public API overview;
- M01/M02 authority diagram/boundary explanation;
- serialization/versioning notes;
- examples for all six domains;
- known deferred extension ports;
- no unsupported performance/quality claims.

## TESTS

At minimum, cover every acceptance item from frozen contract §18 plus:
- all 46 hard invariants;
- every public serialization kind;
- invalid enum/ref/version/predicate payloads;
- authority-forgery regressions;
- stale-context/freshness regressions;
- semantic equivalence/fingerprint regressions;
- M01 round-trip bridge;
- M02 authority boundary;
- no provider SDK leakage;
- no network/shell/database imports/touchpoints;
- six domain-neutral profiles;
- deterministic repeatability.

Use stdlib `unittest` to match repository conventions unless existing project tooling clearly dictates otherwise.

Required commands:
- `python -m py_compile` over all new M03 modules/tests/examples and existing governance tooling;
- `python scripts/validate_governance.py`;
- `python -m unittest discover -s tests -p "test_*.py"`;
- focused M03 suite;
- available linter against new M03 files only if already installed/configured;
- exact-head GitHub Governance.

Existing 1805 tests are the starting floor. New M03 tests must add to that total; no existing test may be deleted/disabled merely to make the suite pass.

## DELIVERABLES

- complete `iris_intent/` semantic kernel;
- `tests/test_m03_*.py` and support fixtures as appropriate;
- `examples/m03_synthetic_profiles.py` or equivalent;
- `docs/M03-INTENT-COMPILER-KERNEL.md`;
- updated `.engineering/evidence/IRIS-WO-0006.json`;
- Context Lock only if an allowed non-semantic metadata delta is needed;
- proposed Checkpoint Delta, not executor-promoted;
- implementation commit(s) pushed to the same branch;
- same PR linked to Issue #19;
- exact-head CI/Governance evidence.

## EVIDENCE BUNDLE

Record truthfully:
- base/head SHA;
- PR number/url/state;
- exact changed files/count;
- package/public API shape;
- dependency changes;
- design decisions;
- tests by family + full total;
- compile/lint/governance commands and results;
- failures encountered and fixed;
- proof M01 remains sole quality authority;
- proof M02 authority not duplicated;
- proof no provider/DCC/cloud/database/network leakage;
- six-domain neutrality evidence;
- token/slice/fingerprint evidence;
- security/admission-shield evidence;
- risks/deferred ports;
- proposed Checkpoint Delta;
- STOP CONDITION.

Never make the Evidence Bundle self-referentially claim its own commit SHA. Use a documented head chain and exact-head CI.

## REVIEW FORMAT

Return in Brazilian Portuguese:
- architecture implemented;
- files/package/public surface;
- exact tests/results;
- M01/M02 integration proof;
- six domain fixtures;
- security/token-efficiency proof;
- deviations/risks;
- commit/head;
- PR;
- Evidence Bundle;
- STOP CONDITION.

## STOP CONDITION

STOP only when:
- complete frozen M03 kernel is implemented;
- full tests/docs/evidence are complete;
- branch is pushed;
- one PR is ready for independent review;
- exact-head Governance is green or deterministically pending and subsequently recorded;
- no frozen invariant was weakened.

DO NOT MERGE.
DO NOT START M04.
DO NOT implement provider/domain runtimes to satisfy ports.
DO NOT lower QualityClass for hardware/provider scarcity.
If the frozen contract cannot be satisfied without semantic change, STOP `BLOCKED_CONTRACT_CONFLICT`.


## REVIEW CLOSURE

Verdict: `APPROVED`

- Independently reviewed/corrected code head: `c7b88bab561144ef6a55be61e60a9d8023246653`
- Governance run/job: `35671496462 / 106568752831`
- Exact-head suite: `2527/2527 OK`
- M03 tests represented in the full suite: `722`
- Required governance artifacts: `35`
- Review findings: `6 CHAT_FIXABLE`, all CLOSED
- EXECUTOR_REQUIRED findings: `0`
- CRITICAL/HIGH blockers remaining: `0`
- Frozen contract weakened: `false`
- M01 quality authority preserved: `true`
- M02 project/graph/release/ExecutionPlan authority preserved: `true`
- M04 started: `false`

Independent review hardened exact-content identity, canonical numeric serialization, immutable extension/authority/semantic lookup law and corrected the admission-time checkpoint pin. No Codex re-execution was required.

The review itself temporarily produced failing test-only heads while patches were being corrected. Those heads are not approval evidence. The approval evidence is the exact head and Governance run above.

## REVIEW STOP CONDITION

Approved for a governance/documentation promotion delta, squash merge through `main-governance`, and post-merge `main` validation.

Do not start M04 implementation before M03 is merged and the resulting `main` is validated.
