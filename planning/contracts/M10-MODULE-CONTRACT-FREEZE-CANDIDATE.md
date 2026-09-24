# M10 Module Contract Freeze Candidate
## Adaptive Execution Planner & Predictive OOM/Thermal Shield

Status: M10_CONTRACT_CANDIDATE_PENDING_GOVERNANCE_AND_INDEPENDENT_AUDIT
Candidate version: m10-contract-v0.1.0-candidate
Module: M10
Planning Work Order: Issue #68
Planning base: 2328978175a59768e64687748b259027b3a79d4e
Implementation authority: NOT ADMITTED

This document is a versioned planning contract candidate. It is not a frozen public schema, an implementation admission, or authorization to execute work. Candidate invariant identifiers below remain subject to independent planning audit and owner-contract confirmation.

## 1. Mission and contract boundary

M10 consumes owner-issued workload, quality, semantic, hardware, capability, resource, model and workflow evidence and returns a bounded, explainable set of execution-plan alternatives with separately scoped OOM, thermal and M01 quality-contract risk estimates.

M02 remains canonical for Production Graph causality, ExecutionPlan semantics and production lifecycle. M10 is an advisory planning boundary attached to M02's contract. A plan proposal is not an accepted ExecutionPlan unless M02 accepts it, and is never a reservation, placement, dispatch, process action, provider submission, publication or release authorization.

M10 must preserve required output quality, protected creative intent, rights, consent, security and owner-issued domain constraints even when resources are scarce. If required evidence is missing, stale, conflicting, unsupported, out of scope or insufficiently calibrated, M10 returns an explicit indeterminate/abstain/no-safe-plan result rather than inventing a safe default.

## 2. Candidate ownership map

| Owner | Canonical authority | M10 relationship |
|---|---|---|
| M01 | Fidelity Contract, quality evaluation and promotion | Consume versioned obligations and outcomes; predict distinct quality-contract risk; never judge or promote quality. |
| M02 | Production Graph, canonical ExecutionPlan and lifecycle | Bind exact request/graph revision; return bounded alternatives through an M02-approved adapter; do not create a competing plan contract. |
| M06 | Immutable operational revisions, materialization lineage and reconstruction evidence | Bind exact M06 references when material; do not create a competing production revision/history authority. |
| M03 | Creative intent and protected semantic constraints | Treat applicable constraints as hard gates; never weaken or reinterpret them for resource preference. |
| M07 | Hardware and runtime facts | Consume source-capability-aware, versioned facts; do not probe or control hardware. |
| M08 | Empirical benchmark/capability evidence | Consume exact-scope empirical envelopes and validity; do not manufacture benchmark evidence. |
| M09 | Resource state, leases, reservations and resource-control outcomes | Consume owner evidence by reference; do not reserve, release, reshape or assert resource truth. |
| M11 | Worker/process lifecycle | Provide a proposal only; do not start, cancel, reap, kill or suspend a worker. |
| M12 | Placement, queues, quotas, preemption and remote/cloud orchestration | Provide requirements and alternatives only; do not select or commit placement. |
| M14 | Model identity, empirical fitness and model lifecycle | Consume exact model/fitness references; do not self-certify, activate or promote M10 models. |
| M15 | Model routing and champion/challenger decisions | Do not duplicate model selection, tournament or ensemble policy. |
| M16 | Workflow identity, provider compilation and qualification | Consume provider-neutral references; do not compile a provider workflow or equate partial coverage with executability. |
| M17–M19 | Runtime integration, acquisition/supply chain and training | Consume only authorized, versioned evidence; do not submit runtime jobs, install packages, train or promote adapters. |
| M20–M49 | Domain production, identity, evaluation and repair authorities | Preserve their declared semantic and quality requirements; do not choose domain operations or silently degrade them. |
| M50–M51 | Cost-to-quality routing and benchmark/evaluation protocols | Keep plan-level resource preferences distinct from cross-stage cost/model routing and benchmark authority. |
| M52–M55 | Memory/retrieval, provenance/rights, security and physical storage | Consume minimal permitted projections; preserve rights/security authority and physical storage ownership. |
| M56–M60 | Observability, autonomy, APIs, delivery and final acceptance | Export explainable evidence only; do not authorize automation, expose a public API, publish or claim final acceptance. |

The detailed index-level requirements and revisit conditions are in [the M11–M60 compatibility scan](../compatibility/M10-FORWARD-COMPATIBILITY-SCAN.md). Confirm every applicable boundary against the owning module contract when that contract is planned.

## 3. Candidate contract records

The candidate contract describes semantic records without selecting a serialization, digest, database, registry or transport.

### 3.1 Workload Signature

A Workload Signature identifies a workload instance/family and its typed, versioned shape projection. It binds exact M02 request/graph references, material M06 revision/materialization references, and applicable M01, M03, M07, M08, M09, M14 and M16 evidence references. It declares feature provenance, capture window, source capability, material runtime/hardware context, applicability, freshness and explicit unknown/unsupported/conflict states.

Instance identity and family/generalization identity are distinct. Similarity is not authorization to transfer a calibration result. Raw prompts, media, credentials and unnecessary personal data are excluded by default; any permitted feature needs an M54-compatible purpose and retention basis.

### 3.2 Plan Proposal and Alternative Set

A Plan Proposal references the canonical M02 request and graph revision, the Workload Signature revision, all hard-constraint results, evidence versions, separate risk records, policy-profile revision and a bounded alternative set. Each alternative includes an admissibility disposition, resource-shape assumptions, capability requirements, evidence scope, rejection reasons and unresolved handoff requirements.

M10 may reject a candidate as unsupported or infeasible under owner-issued facts. It cannot reserve resources, issue a lease, choose M12 placement, dispatch through M11/M17, rewrite M02 state or claim that a proposed allocation was granted. M02 acceptance and any M09/M11/M12/M16 handshakes remain separate owner actions.

### 3.3 Risk Estimate

Each estimate is a separate typed record with a versioned risk-family target, owner/label definition, exact workload and evidence scope, applicable model and calibration references, uncertainty/support summary, capture time/window, freshness, drift/OOD state and reasoned abstention field.

| Risk family | Candidate target | Authoritative distinction |
|---|---|---|
| OOM/allocation failure | Owner-validated terminal allocation/resource-exhaustion outcome in a pinned scope | Pressure, low free memory, timeout, cancellation, generic failure or provider error alone is not confirmed OOM. |
| Thermal | Owner-validated thermal-limit/throttle event in a pinned scope | Temperature, throttle reason, time window and sensor capability remain separate observations. Power-limit behavior is a distinct event family. |
| Quality-contract risk | M01 evaluator/Fidelity Contract outcome for the pinned output class and revision | M10's prediction, execution success, resource scarcity or a surrogate metric is not a quality judgment or promotion. |

No aggregate scalar may replace these outputs. No estimator family, numeric horizon, risk budget, freshness interval, support threshold, acceptance percentage, physical safety claim or accuracy claim is selected by this candidate.

### 3.4 Policy Profile and Decision Receipt

A versioned Policy Profile identifies ECO, BALANCED, QUALITY, MAX or CUSTOM; applicable hard constraints; objective/preference identifiers and units; owner-issued resource/cost/risk references; permitted trade-offs; explicit fallback authorization; and deterministic, disclosed tie-break behavior.

A Decision Receipt binds the profile and revision, candidate set, exact evidence references, hard-gate outcomes, separate risk dispositions, applied preferences, rejection rationale, recommendation and no-safe-plan/indeterminate reason. ECO/BALANCED/QUALITY/MAX/CUSTOM are preferences over admissible alternatives, not guarantees or authority to override a hard gate.

- ECO may prefer lower authorized resource demand and cost; unknown cost/energy is not zero or favorable.
- BALANCED preserves nondominated alternatives unless a versioned, authorized preference profile defines selection.
- QUALITY uses applicable M01 evidence; M01 retains evaluation and promotion authority.
- MAX requires one explicit authorized objective, unit, direction and scope. “Maximize everything” is invalid.
- CUSTOM requires explicit preferences, units/scales, constraints and authorization; incompatible or unknown fields fail closed.
- No mode silently falls back, rewrites another mode or weakens hard constraints. Any permitted transition must be pinned and explained.

M15 owns model routing; M50 owns cross-stage cost-to-quality routing. M10 preference semantics are limited to authorized plan-level alternatives.

### 3.5 Outcome Receipt, Dataset Manifest and Evaluation Record

An append-only Outcome Receipt binds the exact plan/request, selected and executed alternative, considered alternatives and selection reason, policy revision, material M06 revision/materialization references, hardware/runtime/provider/model/workflow context, M09 state, owner-issued terminal results, observation windows, censoring/abort/unknown state, label-validation provenance, integrity and M54-compatible privacy/retention metadata.

Only the alternative actually run has an observed outcome. Non-selected alternatives remain unobserved; M10 may not fabricate counterfactual labels. Corrections append a superseding receipt and preserve history.

A Dataset Manifest pins label definitions and owners, source revisions, time window, inclusion/exclusion rules, cohorts, transformations, missingness/censoring, privacy basis and lineage. An Evaluation Record pins the candidate model, dataset, calibration/evaluation protocol, time/workload-grouped splits, current approved reference, metrics, uncertainty, subgroup/worst-group behavior, false-safe behavior, abstention coverage and limitations.

M14 owns model fitness. M51 owns benchmark protocols and regression corpora. Candidate training/evaluation is offline and separately authorized; no online training, automatic promotion, rollout, shadow dispatch or canary execution is admitted.

### 3.6 Explanation and Replay Projection

An explanation ties the actual policy path to exact inputs, hard constraints, evidence, alternatives, separate predictions, observed facts, owner labels, applicability, uncertainty, model/dataset/calibration versions and the reason for abstention or recommendation. It distinguishes measurement from prediction and correlation from causal evidence.

Replay requires compatible pinned artifacts and authorized data. M56 may aggregate versioned decision events but cannot supply missing physical truth or rewrite history. Explanations are permission-filtered and redact content outside the viewer's authorization.

## 4. Candidate invariants

The following 36 candidate invariants map to FC-10-01 through FC-10-12. They are normative candidate clauses for audit and owner review, not yet frozen invariants.

1. M10 SHALL bind each proposal to the exact M02 request, graph revision and canonical plan contract.
2. M10 SHALL NOT create a competing ExecutionPlan schema or mutate M02 production state.
3. A recommendation SHALL NOT imply reservation, placement, dispatch, worker control, provider submission or authorization.
4. M10 SHALL preserve applicable M01 quality obligations and M03 protected semantic constraints as hard gates.
5. M10 SHALL consume M07, M08 and M09 evidence in distinct owner/version/scope namespaces.
6. Every mandatory evidence reference SHALL identify source owner, schema/version, scope, timestamp/window and validity/freshness state.
7. Missing, stale, conflicting, unsupported, out-of-scope or revoked mandatory evidence SHALL produce an explicit unknown, abstain, indeterminate or no-safe-plan disposition.
8. Similar workload-family membership SHALL NOT by itself establish calibration applicability or transfer an owner decision.
9. Alternatives SHALL remain bounded, evidence-linked and admissible under all hard constraints before preference ranking.
10. M10 SHALL NOT use hidden weights, penalty terms or defaults to soften hard constraints.
11. ECO SHALL compare only authorized resource/cost dimensions; unknown cost, energy or thermal burden SHALL NOT be imputed as favorable.
12. BALANCED SHALL preserve nondominated alternatives unless a versioned, authorized preference profile resolves the trade-off.
13. QUALITY SHALL consume M01-owned evidence and SHALL NOT evaluate or promote output quality.
14. MAX SHALL identify one authorized objective with unit, direction and scope; absent or incomparable objectives SHALL fail closed.
15. CUSTOM SHALL pin explicit preference scales, constraints, fallback permissions and authorization; unknown incompatible fields SHALL be rejected.
16. A mode transition or fallback SHALL be explicit, pre-authorized, versioned and recorded; silent mode rewriting is prohibited.
17. OOM, thermal and quality-contract risk SHALL be separate typed estimates with distinct targets and labels.
18. Confirmed OOM labels SHALL require owner-validated allocation/resource-exhaustion outcomes; pressure, timeout and cancellation alone are insufficient.
19. Thermal observations SHALL preserve sensor capability and separately identify thermal-limit/throttle and power-limit behavior.
20. Quality-risk labels SHALL reference the applicable M01 evaluator/Fidelity Contract revision and owner outcome.
21. Every predictive estimate SHALL identify estimator/model and calibration lineage, support, uncertainty and applicability.
22. Calibration SHALL be scoped to pinned workload, hardware/partition, driver/runtime, provider/workflow, model and resource evidence material to the estimate.
23. Distribution shift, OOD, insufficient support or violated calibration assumptions SHALL trigger an explicit abstention/quarantine disposition.
24. Synthetic fixtures SHALL NOT prove physical calibration, real-device accuracy or hardware safety.
25. Outcome and label records SHALL be owner-issued, append-only and correction-preserving; material M06 operational revision/materialization references are linked without M10 claiming production-state ownership.
26. Outcomes for unselected alternatives SHALL remain unobserved; fabricated counterfactuals are prohibited.
27. Dataset and evaluation lineage SHALL be immutable, revision-pinned, reproducible and time/workload-group aware.
28. M10 SHALL NOT self-label, self-certify, train online, activate or promote its own model.
29. M14 fitness approval, M01 quality authority and applicable governance approval SHALL remain external prerequisites to any future model use.
30. Drift or invalid provenance SHALL quarantine the affected applicability slice and return it to abstention until owner review.
31. Rollback SHALL reference a still-approved compatible version and preserve transition reason, evidence and history.
32. Decision explanations SHALL distinguish owner observations, predictions, labels, policy choices and inferred interpretation.
33. Replayable decisions SHALL pin policy, artifacts, evidence and compatibility needed for reproduction.
34. Raw prompts, media, credentials and unnecessary personal data SHALL be excluded by default; M54 purpose, access, minimization and retention controls apply.
35. M15/M50 routing and cost-quality authority, M11/M12 execution authority and M53/M54 rights/security authority SHALL NOT be absorbed into M10.
36. M56/M58/M60 projections SHALL preserve provenance and versioning; observability, APIs and release evidence SHALL NOT grant runtime authority or imply final acceptance.

## 5. Forward-compatibility traceability

| Finding | Candidate clauses | Owner confirmation or contract detail still required |
|---|---|---|
| FC-10-01 Canonical plan and execution acceptance | 1–4, 9 | M02 adapter; M11 process acceptance; M12 placement feasibility/commit boundary |
| FC-10-02 Typed evidence and invalidation | 5–8, 21–23 | Owner schemas, freshness, invalidation and source capability |
| FC-10-03 Prediction vs quality decision | 13, 17–20, 29 | M01/M24/M48 evaluator and label handoffs |
| FC-10-04 Constraint-preserving alternatives | 4, 7–10, 16 | Domain-specific hard-constraint projection |
| FC-10-05 Model/workflow handoff | 21, 22, 28, 29, 35 | M14/M15/M16/M17/M18/M19 identities and lifecycle |
| FC-10-06 Resource/process/placement/cache separation | 3, 5–7, 35 | M09/M11/M12/M13/M55 namespaces and acceptance |
| FC-10-07 Cost and objective authority | 9–16, 35 | M15/M50 boundaries and authorized units/objectives |
| FC-10-08 Learning/benchmark/model lifecycle | 17–31 | M14/M51 labels, evaluation and approval |
| FC-10-09 Rights/privacy/security | 25, 28, 34, 35 | M53/M54 purpose, consent, retention and redaction |
| FC-10-10 Explanation/observability | 21, 25, 31–34, 36 | M56 event schema, replay and authorization projection |
| FC-10-11 Agent/API non-bypass | 3, 16, 35, 36 | M57 stop conditions and M58 permissions/versioning |
| FC-10-12 Final acceptance/recovery | 23, 31–33, 36 | M60 acceptance and recovery evidence matrix |

## 6. Evidence and verification obligations

A future admitted implementation must provide owner-reviewable evidence for:

- exact M02 plan binding and separation between proposal, acceptance, reservation, placement and execution;
- all hard-gate and unknown/stale/conflict/unsupported/OOD paths, including explicit no-safe-plan;
- distinct validated OOM, thermal/power and M01 quality-contract outcomes;
- exact-scope calibration, leakage-resistant workload/time splits, uncertainty, false-safe behavior, drift and abstention;
- ECO/BALANCED/QUALITY/MAX/CUSTOM semantics, explicit objective units, tie-breaks and authorized fallback;
- owner-issued receipt immutability, censoring, selection bias and absence of fabricated counterfactuals;
- offline dataset/model/evaluation lineage, M14 approval boundary, quarantine and compatible rollback;
- replayable explanations that separate predictions, observations, labels and policy;
- M53/M54 rights, privacy, access and retention controls;
- M11/M12/M16/M50/M56/M57/M58/M60 interface and authority shields.

Synthetic tests may verify schemas, transitions, provenance bookkeeping and fail-closed mechanics. Physical claims require separately authorized owner measurements on exact hardware/runtime cohorts; synthetic fixtures cannot establish them. This candidate adds no tests, benchmark results, thresholds or runtime implementation.

## 7. Deferred owner decisions

The following remain open and SHALL NOT be silently defaulted inside M10:

- canonical record serialization, digest, storage, retention and public/internal projection;
- exact M02/M11/M12 plan-acceptance, process and placement handshakes;
- M09 resource-claim/reservation boundary and M16 provider capability/qualification handshake;
- supported risk estimators, target windows, calibration methods, minimum evidence support, freshness, uncertainty and numeric risk budgets;
- M01/M14/M24/M48 label ownership, model-fitness and approval interfaces;
- M15/M50 model-routing and cross-stage cost-quality objective boundary;
- M51 benchmark protocol/label handoff and physical-evidence acceptance;
- M53/M54 authorization, consent, redaction, access, retention and deletion projection;
- M56 event schema, M57 agent invocation/stop conditions, M58 public API projection and M60 final evidence matrix;
- any future shadow/canary measurement, online learning, rollout, automatic promotion or autonomous dispatch.

Resolve each against the owning module's planned contract and record any approved change through versioned governance.

## 8. Scope and implementation STOP condition

This candidate freezes no vendor, model, solver, library, registry, database, provider, runtime, numeric threshold or hardware-specific behavior. It does not implement schemas, calibration, training, dispatch, resource control, observability or UI.

Do not promote this candidate to a frozen M10 contract until:

- S01–S05 and the Final Technology Review remain exact-main validated;
- the M11–M60 compatibility scan and its 12 findings are reconciled in the candidate;
- each applicable owner boundary and explicit deferral is reviewed;
- an independent planning audit approves lifecycle completeness, traceability and evidence limitations with zero unresolved HIGH/CRITICAL findings;
- exact-head Governance and exact-main validation pass for the candidate.

M10 product/runtime implementation remains NOT ADMITTED and NOT STARTED. A separate implementation Work Order, Context Lock, Evidence package and preflight are required after planning completion.

## 9. Candidate state

- Candidate version: m10-contract-v0.1.0-candidate
- Candidate head: pending
- S01–S05: COMPLETE_FOR_MODULE_PLANNING
- Final Technology Review: exact-main validated at e38912a57c2d452badd5a35a031eb78f95d0e899
- M11–M60 Forward Compatibility Scan: exact-main validated at 2328978175a59768e64687748b259027b3a79d4e; 50/50 index entries; FC-10-01..12
- Candidate invariants: 36, pending independent audit
- Individual M11–M60 module plans at scan base: absent; revisit required
- Independent planning audit: PENDING
- Frozen contract: NO
- M10 implementation: NOT ADMITTED
- Known unresolved HIGH/CRITICAL conflict at index-level evidence: NONE; explicit owner decisions above remain open

The scan and contract candidate do not assert that future module-level contract reviews are complete.