# M01 Quality Kernel — implementation note

Work Order: `IRIS-WO-0003` · Frozen contract: `m01-contract-v1.0` · Schema: `iris-quality-schema-v1`

This page documents the running code in `iris_quality/`. It is an implementation
note, not a planning document: the normative wording stays in
`planning/contracts/M01-MODULE-CONTRACT-FREEZE-CANDIDATE.md` and
`planning/modules/M01-EXTREME-QUALITY.md`.

## Shape

| Module | Holds | Audience |
| --- | --- | --- |
| `versions` | `ComponentVersion`, version/schema constants, identifier and text guards, `canonical_json`, `content_digest` | kernel + callers |
| `dimensions` | `FidelityDimension`, `CANONICAL_FIDELITY_VECTOR` (18 ids), `DimensionRegistry` + `DEFAULT_DIMENSION_REGISTRY`, `GateState`, `UncertaintyState`, `MeasurementRange`, `DimensionAssessment` | kernel + judges |
| `evidence` | `EvidenceRef`, `EVIDENCE_KINDS`, relative-locator guard | judges, validators |
| `defects` | `Defect`, `DefectSeverity` | judges, validators |
| `zones` | `SemanticZone` | domain profiles |
| `contracts` | `QualityClass`, `PromotionRule`, `FidelityContract` | every caller |
| `debt` | `QualityDebt`, `QualityDebtPolicy`, `DebtRuling` | quality policy |
| `judging` | `SubjectRef`, `JudgeRequest`, `JudgeResult`, `Abstention`, `QualityJudge` and `AssetValidator` ports, `ValidationCheck`, `ValidatorOutcome`, `attach_contract_checks`, `numeric_spread` | evaluator authors |
| `registry` | `TrustTier`, `ExtensionMetadata`, `EvaluatorDescriptor`, `EvaluatorRegistry`, `EvaluatorAuthority`, `DomainProfile`, `DomainProfileRegistry` | module authors |
| `decision` | `DecisionEngine`, `QualityDecision`, `Blocker`, `DimensionOutcome`, `EffectiveFinding`, `merge_assessments` | callers |
| `serialization` | typed envelopes, `dumps`/`loads`, `validate_payload` | storage, HIVE later |

`examples/m01_synthetic_profiles.py` sits outside the package on purpose: domain
vocabulary must never be reachable from `iris_quality/`.
`tests/test_m01_domain_neutrality.py` enforces that boundary mechanically.

## Public API

```python
from iris_quality import (
    FidelityContract, PromotionRule, QualityClass,   # obligations
    SubjectRef, JudgeRequest, JudgeResult,           # ports
    DimensionAssessment, EvidenceRef, Defect, SemanticZone,
    DimensionRegistry, DEFAULT_DIMENSION_REGISTRY,   # admitted dimensions
    DecisionEngine, QualityDecision, DecisionOutcome,  # verdicts
    EvaluatorRegistry, EvaluatorAuthority,           # capability
    DomainProfileRegistry,
    dumps, loads, envelope, from_envelope, validate_payload,
)
```

Every exported symbol is listed in `iris_quality.__all__` and asserted present by
the neutrality test, so the table above and the package agree.

### Deciding one asset

```python
contract = profile.instantiate(
    contract_id="contract.nerim.siege-01",
    intent="isometric siege asset readable at play distance",
    output_class=QualityClass.MASTER,
    zones=GAME_ASSET_ZONES,
)
subject = SubjectRef("asset.siege-01", content_sha256=digest)
results = tuple(judge.evaluate(JudgeRequest(contract, subject, contract.dimension_ids))
                for judge in jurors)
decision = DecisionEngine().evaluate(
    contract, subject, results=results,
    authority=EvaluatorAuthority.resolved(contract, evaluator_registry),
)
if decision.outcome is DecisionOutcome.PROMOTED:
    decision.require_promotable()   # raises PromotionBlockedError otherwise
```

`authority` is mandatory and must carry a registry resolved against the whole
declared panel, which `EvaluatorAuthority` now guarantees while it is being
built: a missing or declaration-only authority is refused instead of deciding on
a weaker rule (invariant 10).

Inputs may be handed over as `results` (from `QualityJudge` ports, merged by the
engine) or as direct `assessments`. Mixing the two sources for the same dimension
raises `EvaluationInputError` rather than picking a winner silently.

## Invariants the kernel enforces

1. **Severity belongs to the contract.** A defect class must be declared in
   exactly one of `fatal/major/minor/observation_defect_classes`; an undeclared
   class raises. The effective severity is the strictest of the contract's
   declaration, the reporter's severity, and any zone override, so a reporter
   cannot dilute a `MINOR` class by calling it an `OBSERVATION`.
2. **FATAL is a firewall, and debt is ruled against the firewall.**
   `QualityDebtPolicy.rule(defect, debt, effective_severity)` and `rule_all` take
   the authoritative severity, so a `MINOR` report of a contract-`FATAL` class
   with matching `MINOR` debt is refused (`effective_fatal_defects_are_never_deferrable`)
   instead of buying a deferral. Any non-deferred effective FATAL awards `DRAFT`,
   returns `REJECTED` and carries `fatal_defect_firewall`; `QualityDecision`
   additionally refuses to *construct* a record where an effective FATAL finding
   is marked deferred, so the bypass is unrepresentable in a stored decision, not
   merely unreachable through one call path.
3. **No aggregate score.** `QualityDecision` carries per-dimension gates,
   uncertainty, evidence counts and confidences. Nothing averages a defect away.
4. **Monotonic ladder.** Promotion evaluates `PREVIEW → REVIEW → MASTER →
   ARCHIVAL_MASTER` in order and stops at the first unmet rung, so a weak
   candidate can never be labelled above what its own evidence supports.
   `require_promotable()` is the only sanctioned way to act on a decision.
5. **Uncertainty is preserved.** A dimension with no assessment stays
   `UNVERIFIED`/`UNKNOWN` with zero evidence; low confidence becomes
   `HUMAN_REVIEW`, never a fabricated score. Zone `minimum_confidence` floors and
   juror disagreement above `max_judge_disagreement` both force review.
6. **Hard gates are not for sale.** A `hard_gate_dimension_ids` failure blocks its
   rung even when accepted `QualityDebt` covers the same defect; ordinary gates may
   be carried by policy-accepted debt.
7. **Human review is explicit.** `FidelityContract.human_review_dimension_ids`
   demands a `HUMAN_DECISION` evidence item on that dimension at every rung, and a
   `PromotionRule.requires_human_review` rung demands one on each of its required
   dimensions. A judge's own `JudgeResult.human_review_dimension_ids` is honoured
   too: the union across jurors marks the dimension `HUMAN_REVIEW`, records the
   requesters on `DimensionOutcome.human_review_requested_by`, raises
   `judge_human_review_requested` and blocks promotion until a `HUMAN_DECISION`
   item answers it. A request naming a dimension the contract never admitted
   raises instead of being dropped.
8. **Deterministic records.** Identical normalized inputs produce identical
   `QualityDecision.to_payload()` bytes and the same `content_sha256`; findings,
   blockers and dimensions are canonically ordered, never input-ordered.
9. **Extension metadata is closed.** `ExtensionMetadata` accepts at most 16
   allowlisted keys of bounded plain text, and `source` must be a relative
   locator; anything else raises `UntrustedExtensionError`. No field is ever
   interpreted as instructions.
10. **Capability is declared, never inferred.** `EvaluatorRegistry.resolve()` fails
    when a contract names an unregistered evaluator or a dimension it cannot
    cover; two versions of one evaluator may not silently change coverage.
    `DecisionEngine.evaluate()` enforces the same thing on the way in, and it is
    not optional: every juror, every direct `DimensionAssessment` producer and
    every defect speaker must appear in `contract.evaluator_set` at the exact
    version that spoke **and** be registered with coverage for each dimension it
    opined on. `evaluate()` therefore requires a promotion-capable
    `EvaluatorAuthority.resolved(contract, registry)`; `authority=None` and
    `EvaluatorAuthority.preflight(contract)` both raise `EvaluationInputError`.
    A missing registry is a fail-closed condition, never permission, and no
    public constructor is weaker than `resolved`: building a registry-backed
    authority resolves `registry.resolve(contract)` first, so a panel that omits
    a declared evaluator — even one that never speaks — cannot become
    promotion-capable.
11. **Dimensions are a closed, versioned set.** `DimensionRegistry` holds the 18
    frozen `CANONICAL_FIDELITY_VECTOR` ids plus at most `MAX_EXTENSION_DIMENSIONS`
    explicitly registered, non-core, non-shadowing extensions. Contracts, domain
    profiles and evaluator descriptors each carry a registry (defaulting to
    `DEFAULT_DIMENSION_REGISTRY`) and reject any id outside it, so a new modality
    is admitted by data at the freeze boundary rather than by editing the state
    machine in `decision.py`.

### Blocker codes

Every non-promotion carries at least one named blocker:
`fatal_defect_firewall`, `judge_disagreement`, `zone_confidence_floor`,
`judge_human_review_requested`, `insufficient_certainty`,
`insufficient_evidence_coverage`, `insufficient_confidence`,
`dimension_gate_not_pass`, `hard_gate_failed`, `major_defect_without_debt`,
`minor_defect_without_debt`, `human_review_missing_for_dimension`,
`human_review_not_recorded`.

## Ports

`QualityJudge` (`component_version`, `covers()`, `evaluate(request)`) and
`AssetValidator` (`component_version`, `validate(contract, subject)`) are
`runtime_checkable` protocols. A judge returns `JudgeResult` with assessments,
defects and explicit `Abstention`s; a validator returns `ValidatorOutcome`, whose
binary `ValidationCheck`s are projected onto dimensions by
`attach_contract_checks()`, which refuses an outcome bound to a different
contract reference or subject. A projection is structural, not perceptual: each
check becomes a `PASS`/`FAIL` gate at the boundary values 1.0/0.0 with the
validator as its evaluator, so a validator can force a gate but can never
manufacture a mid-range perceptual value.

A `JudgeResult` may ask for a human on dimensions it assessed or abstained from;
the engine treats that request as an unresolved obligation (invariant 7). The
kernel deliberately does not authenticate *who* signed a `HUMAN_DECISION`
evidence item: the outer boundary of M01 is that such an item exists and is
attributed to a versioned producer. Identity, quorum and tamper-evidence of human
sign-off belong to the review workflow that stores these records, not to the
decision kernel.

## Serialization

`envelope()` wraps any serializable type as
`{schema_version, type, payload, payload_sha256}`; `dumps`/`loads` and
`from_envelope` verify the digest before parsing and rebuild the object through
`from_payload`, which accepts only its exact key set. `validate_payload` adds the
canonicality check: a payload that changes shape when re-emitted is rejected, so
`"master"` cannot be smuggled in where `"MASTER"` is stored. The 16 serializable
kinds are enumerated in `serialization.SERIALIZABLE_TYPES`.

## Design decisions inside the freeze

- **`observation_defect_classes` was added to `FidelityContract`** and
  `DomainProfile`. The freeze names concept-level fields, not a closed list, and
  S01 defines `OBSERVATION` as non-blocking evidence. Without a declaration site
  the severity would be unreachable through a contract, and the Work Order's
  "major/minor/observation policy" test could not be written without weakening the
  rule that a reporter cannot downgrade a declared class.
- **`human_review_dimension_ids` lives on the contract**, mirroring the frozen
  requirement that a contract binds "human-review requirements"; per-rung demands
  are carried by `PromotionRule.requires_human_review`.
- **Promotion rules must be contiguous** up to the requested class, which keeps the
  "stops at the first unmet rung" property from silently skipping a rung.
- **Evidence locators must be relative** so a bundle can later be stored in HIVE
  verbatim and replayed from any checkout.
- **`merge_assessments` is worst-case**, not average: strictest gate, weakest
  uncertainty, lowest confidence, median value, union of evidence, attributed to a
  synthetic `jury-consensus@<digest>` evaluator.
- **Extension dimensions are registry data, not a kernel constant**
  (IRIS-WO-0003-CORRECTION-01 F4). The approved freeze promises non-visual Fidelity
  Vector growth; putting an id in `dimensions.py` would have made that growth a code
  change to the state machine. `DimensionRegistry` is instead a persisted, versioned,
  bounded field on `FidelityContract`, `DomainProfile` and `EvaluatorDescriptor`, so
  `DecisionEngine` stayed byte-for-byte unchanged and `profile.narration-audio`
  promotes through it. The serializable-kind count stays 16 because a registry is
  carried by its three owners rather than exchanged on its own.
- **Evaluator capability is checked at the input boundary** (F2) through a small
  value object rather than by making `DecisionEngine` depend on
  `EvaluatorRegistry` directly: `EvaluatorAuthority.resolved(contract, registry)`
  is the only promotion-capable form, and it is required on every
  `DecisionEngine.evaluate()` call. CORRECTION-02 removed the tier that let a
  caller skip registration, because an optional registry is an optional invariant.
  CORRECTION-03 moved the same resolution into `__post_init__`, so the invariant
  lives in the type rather than in one recommended constructor: a directly built
  authority over an incomplete panel raises `RegistrationError` instead of
  quietly becoming promotion-capable.
  Declaration-only inspection survives as `EvaluatorAuthority.preflight(contract)`,
  which answers "who does this contract admit?" and is refused by the engine, so a
  production caller cannot silently fall back to the weaker rule.
- **Debt rulings moved behind severity resolution** (F1) rather than special-casing
  FATAL at the deferral site, because the bypass was a dilution of *which* severity
  the ruling consulted. `_apply_policy` now resolves contract, report and zone
  severity first and rules once, and `QualityDecision` refuses a deferred effective
  FATAL so no caller can reintroduce the hole through a hand-built record.

## What M01 deliberately does not do

No inference, no pixel/mesh/scene access, no Blender or ComfyUI, no DreamSim/FLIP
or model-provider calls, no CV segmentation, no game/web/logo engines, no UI, no
distributed compute, no HIVE mutation, no M02 code. The three frozen profiles in
`examples/` (plus the non-visual `profile.narration-audio` extension fixture) are
contract fixtures with arithmetic stand-ins; the real evaluators that will replace
them are delivered by their own modules through the ports above.
