# M10 — Adaptive Execution Planner & Predictive OOM/Thermal Shield

Status: `PLANNING_FINAL_TECHNOLOGY_REVIEW_CANDIDATE_PENDING_GOVERNANCE`
Module: **M10 Adaptive Execution Planner & Predictive OOM/Thermal Shield**
Planning Work Order: [Issue #68](https://github.com/KayzenRoot/iris/issues/68)
Authorized planning base: `b6456670a7c61621db1d3b3fc6d55487adb9cd64`
S02 session base: `fc1a3c954a1629b9e9a4c45c4e557a7832c290d7`
S02 exact head: `0fa18f55d845192d4225751ec14316af08ec6dad`; Governance `36032894812 / 107745773871` — **PASS**
S02 protected squash merge / exact-main: `8d068d1cf9ef604aef8506ec879b7a382ec1b738`; Governance `36033011233 / 107746156289` — **PASS**
S03 exact head: `db9fc7e0f0e7615c075cfaee3debec3a3990697b`; Governance `36034416554 / 107750841548` — **PASS**
S03 protected squash merge / exact-main: `8768661ee348815ec5b1eb6e32bc85505fa10b17`; Governance `36034538318 / 107751237481` — **PASS**
S04 exact head: `add4344d6b1a495f1aeeb23af0d57fdcddde381e`; Governance `36037625164 / 107761547909` — **PASS**
S04 protected squash merge / exact-main: `96aee147e701c6d716cfbcf5f2be524ee5d751e7`; Governance `36037710495 / 107761836741` — **PASS**
S05 exact head: `fc1fa4959697b88fbfbe303736517aef52d9bc91`; Governance `36038801813 / 107765474152` — **PASS**
S05 protected squash merge / exact-main: `54d85d3491d4cc21e95fc2f9042c53d2852ceb88`; Governance `36038905218 / 107765823628` — **PASS**
S01 exact-main Governance: `36031548275 / 107741264931` — **PASS**
Admission Governance: `36029536926 / 107734488887` — **PASS**
Implementation authority: **NOT ADMITTED**

## Governing intent

Plan the complete M10 capability for IRIS 1.0, not an MVP slice. M10 planning covers workload signatures, hardware-aware execution planning, predictive OOM/thermal/quality-risk estimates, policy semantics and observed-result learning with explanations.

This document is a planning candidate. No M10 product/runtime/test implementation is admitted.

## Canonical sessions

| Session | Scope | Status |
|---|---|---|
| S01 | Workload Signature Engine | COMPLETE_FOR_MODULE_PLANNING |
| S02 | Hardware-aware execution plan compilation | COMPLETE_FOR_MODULE_PLANNING |
| S03 | Predictive OOM, thermal and quality-risk models | COMPLETE_FOR_MODULE_PLANNING |
| S04 | ECO / BALANCED / QUALITY / MAX / CUSTOM policy semantics | COMPLETE_FOR_MODULE_PLANNING |
| S05 | Observed-result learning loop and explainable decisions | COMPLETE_FOR_MODULE_PLANNING |

## Authority boundaries

- **M02** owns Production Graph causality, canonical ExecutionPlan contracts and production lifecycle. M10 must bind to those contracts and must not create a competing graph, identity or execution-plan schema.
- **M01** owns quality evaluation and promotion. **M03** owns creative intent and protected semantic constraints. M10 may estimate risk and propose bounded alternatives; it cannot lower quality targets or rewrite semantic obligations.
- **M07** owns hardware/runtime facts; **M08** owns empirical benchmark/capability truth; **M09** owns resource state, leases, residency and resource-control outcomes. M10 consumes versioned evidence by reference.
- **M11** owns worker/process lifecycle; **M12** owns placement/orchestration; **M13** owns cache and execution-efficiency mechanisms; **M14** owns model fitness; **M16** owns concrete provider/workflow compilation.
- **M50** owns broader cost/quality routing; **M54** owns security policy; **M56** owns observability aggregation.
- M10 planning must define each handshake without taking the owning module's authority.

## S01 — Workload Signature Engine

Status: `COMPLETE_FOR_MODULE_PLANNING`

### Objective

Define a bounded, versioned workload description and an evidence-binding model that supports later prediction without conflating workload instance, production identity, provider workflow, device truth, empirical capability, resource state or quality authority.

### Planning result

A signature candidate is an immutable typed projection of owner-defined workload features plus pinned M02/M01/M03/M07/M08/M09 and, where relevant, M11/M12/M14/M16/M50/M54/M56 references. The signature distinguishes:

- workload family from a specific workload instance;
- semantically material feature values from raw prompt/media payload;
- allocator-scoped memory observations from device/process totals;
- reported telemetry from inferred features;
- prior observations from current target state;
- OOM, thermal, quality-risk, timeout, cancellation and unknown outcomes.

S01 does not select prediction algorithms, target risk thresholds or policy-mode behavior. Those belong to S02-S05.

### Candidate surfaces for S01

1. Workload Signature Envelope
2. Workload Instance/Family Identity Split
3. Workload Family Namespace
4. Typed Multimodal Shape Projection
5. M02 Causal Plan Reference Binder
6. M01 Quality Contract Reference Binder
7. M03 Protected Constraint Reference Binder
8. M14 Model Evidence Reference Binder
9. M16 Workflow/Provider Reference Binder
10. M07 Hardware and Runtime Context Binder
11. M08 Empirical Capability Context Binder
12. M09 Resource Context Binder
13. Memory Feature Scope Descriptor
14. Thermal/Power Feature Scope Descriptor
15. Telemetry Sampling Window and Freshness Descriptor
16. Feature-Version and Runtime Materiality Binder
17. Observed Outcome Label Registry
18. Unknown/Unsupported Feature Lattice
19. Signature Similarity and Generalization Boundary
20. Data Minimization and Redaction Contract

This is a candidate inventory for consolidation during the Final Technology Review. It is not a frozen surface count.

### Provisional S01 planning invariants

1. Workload family, workload instance and M02 production identity use distinct versioned identifiers.
2. A signature is immutable and binds its feature schema, source revisions, provenance and capture time.
3. Each numeric feature has an explicit unit, scope, sampling window and source.
4. Owner-defined semantic features enter through typed versioned projections; M10 does not infer missing domain semantics from raw media or prompts.
5. Unknown, stale, conflicted, unsupported and unavailable feature states remain distinct.
6. Missing or invalid mandatory evidence cannot be treated as zero or as a healthy/safe value.
7. Device-global, process-reported and allocator-scoped memory are not summed or substituted without a proven reconciliation contract.
8. Telemetry capability, freshness and sample interval are bound to the signature; unsupported fields remain explicit.
9. M02, M01, M03, M07, M08 and M09 references are immutable and pinned to exact revisions.
10. Similarity or nearest-neighbor matches are advisory until a calibrated, scope-specific generalization rule is approved.
11. An OOM label requires explicit allocation/resource-exhaustion evidence; generic task failure is insufficient.
12. Thermal throttling, high temperature, high power and performance slowdown are distinct outcomes.
13. Timeout, cancellation, process loss and incomplete observation are not relabeled as successful, OOM or thermal outcomes.
14. Raw prompts, media payloads, credentials and unbounded free-form user text are not required signature fields.
15. Feature extraction, signature size and history references are bounded.
16. Synthetic fixture observations are labeled synthetic and cannot qualify a production signature or physical risk claim.
17. Signature schema changes are versioned; an incompatible projection does not silently match an older signature.
18. A signature match cannot authorize a worker start, placement, provider workflow, resource mutation or quality change.
19. Cross-run joins require a purpose, authorization and privacy-safe provenance reference.
20. Every later prediction records the exact signature revision it consumed.

### Research and evidence

The S01 technical findings and primary references are recorded in [M10 S01 research](../research/M10-S01-WORKLOAD-SIGNATURE-ENGINE.md). PyTorch allocator snapshots have a narrower scope than total device memory; vendor telemetry APIs also expose provider-specific availability and sampling behavior. Those differences motivate explicit source scope, timestamps and unknown-state semantics. This is a design inference from the cited vendor documentation, not an assertion that any one adapter is selected.

### S01 exit criteria

- Workload family, instance and production identity are distinct.
- Typed feature/source/provenance/freshness requirements are explicit.
- M02/M01/M03/M07/M08/M09 authority remains intact.
- Memory scope and telemetry limitations are represented rather than erased.
- Outcome labels distinguish OOM, thermal, quality risk, timeout, cancellation and unknown.
- Privacy and boundedness requirements are explicit.
- No predictor, threshold, product code or implementation authority is introduced.

## S02 — Hardware-aware execution plan compilation

Status: `COMPLETE_FOR_MODULE_PLANNING`

### Objective

Define how M10 converts an admitted workload signature and exact upstream evidence into bounded execution alternatives that M02 can accept under its canonical plan contract. S02 defines the compilation boundary and evidence requirements, not an independent M10 ExecutionPlan schema.

### Planning result

M10's candidate is derived only from revision-pinned, owner-issued evidence:

- M02 production graph, target revision and plan/request contract;
- M01 quality obligations and M03 protected intent/constraints;
- M07 hardware/runtime facts and explicit consumer-projection omissions;
- M08 empirical capability evidence bound to the exact workload and hardware/runtime scope;
- M09 resource snapshots, claims, leases and resource-shape feasibility;
- where applicable, M14 model-fitness and M16 provider/workflow capability references.

The candidate may narrow to M09-admitted resource shapes and M02-authorized work. It cannot widen graph nodes, inputs, dependencies, quality targets, semantic obligations or permissions. M02 remains the only canonical plan contract and lifecycle owner. M10 performs no placement, reservation, worker control, provider compilation or media execution.

### Candidate compilation stages

1. **Pin context.** Bind exact M02/M01/M03/M07/M08/M09 references and capture/version metadata. Do not resolve implicit `latest` references.
2. **Check scope and coherence.** Verify that hardware identity, runtime/driver context, benchmark binding, resource identity and workload signature cover compatible scopes. Preserve M07 projection omissions and M09's observed/reported/allocatable/reserved/committed/resident/reclaimable/external/unknown distinctions.
3. **Apply hard admissibility.** Reject alternatives that violate mandatory M01 quality or M03 semantic requirements, M02 causal constraints, M07 compatibility facts, M08 demonstrated/conservative capability bounds, or M09 feasibility and authorized shape options.
4. **Build bounded alternatives.** Describe only alternatives represented by owner-issued options and accepted by the M02 plan contract. S04 owns policy-mode preferences and ranking semantics; S03 defines risk-target semantics, uncertainty and calibration evidence. Operational budgets and acceptance gates remain deferred to S04/final review.
5. **Return explicit decision evidence.** Candidate dispositions such as eligible, infeasible, indeterminate, stale, conflict and no-safe-plan are provisional labels, not frozen enum values. Each disposition names exact source refs, rejected constraints and reason. Missing/unknown mandatory input cannot become positive feasibility.

### Candidate S02 surfaces

1. M02 Plan Contract/Request Adapter
2. M02 Graph, Revision and Dependency Binder
3. M01 Quality Obligation Gate
4. M03 Protected Constraint Gate
5. M07 Hardware Identity and Capability Slice Consumer
6. M07 Runtime/Driver Compatibility Binder
7. M07 Projection Omission and Unknown-Fact Handler
8. M08 Exact Workload/Hardware Benchmark Binder
9. M08 Demonstrated/Conservative/Unknown Capability Consumer
10. M09 Resource Snapshot and Claim Consumer
11. M09 Resource-Shape Feasibility Option Consumer
12. M14 Model Fitness Reference Binder
13. M16 Provider/Workflow Capability Reference Binder
14. Evidence Scope and Capture-Window Coherence Checker
15. Hard-Constraint Admissibility Filter
16. Bounded Alternative Set Builder
17. Candidate Rejection and Explanation Receipt
18. No-Safe-Plan Outcome Boundary
19. M02 Acceptance/Canonicalization Handshake
20. M09 Reservation and Lease Handshake (deferred to owner)
21. M11 Worker Dispatch Handshake (deferred to owner)
22. M12 Placement Handshake (deferred to owner)
23. M56 Decision/Source Observability References
24. Stale-Context Revalidation Trigger

This inventory remains provisional until Final Technology Review; it is not a frozen family count.

### Provisional S02 invariants

1. Every candidate binds an exact M02 graph/revision and the M02 contract version it targets.
2. M10 cannot create or serialize a competing canonical ExecutionPlan.
3. A candidate cannot add M02 nodes, dependencies, inputs, work or side-effect permissions.
4. Mandatory M01 quality and M03 protected constraints are hard gates, never soft scoring dimensions.
5. M07, M08 and M09 evidence is immutable, provenance-bound and consumed by reference.
6. M07 omitted, unsupported or unknown mandatory facts cannot be interpreted as absent hardware constraints.
7. M08 evidence must match the workload, hardware, runtime and benchmark scope required by its source contract.
8. M09 resource facts remain semantically distinct; unknown, stale, conflicted or quarantined state cannot prove free capacity.
9. Capacity evidence and model predictions are not combined into one unlabeled scalar.
10. Provider registration or partial operator support is not proof that the complete requested workflow is executable.
11. MIG/device partition identity and visible per-instance capacity, when relevant, are pinned separately from parent GPU identity.
12. M10 does not choose a physical device, host, cluster or placement; M12 owns placement/orchestration.
13. M10 does not create a reservation or lease; M09 owns resource commitment.
14. M10 does not start, pause, terminate or restart work; M11 owns worker/process lifecycle.
15. M10 does not compile concrete provider graphs/workflows; M16 owns provider compilation.
16. S02 defines feasibility filters, not ECO/BALANCED/QUALITY/MAX/CUSTOM ranking weights.
17. S02 does not set operational OOM, thermal or quality-risk budgets or acceptance thresholds. S03 defines prediction and calibration semantics; any policy gates remain subject to S04 and Final Technology Review.
18. If no alternative has complete admissible evidence, emit an explicit no-safe-plan/indeterminate candidate rather than choosing the least-unknown option.
19. Dynamic evidence must be revalidated at the owning M09/M12/M11 handoff; a planning snapshot is not a reservation or dispatch token.
20. Explanations identify accepted/rejected alternatives, exact evidence refs and blocking constraints.
21. Candidate counts, processing and retained evidence are bounded.
22. Synthetic evidence stays marked synthetic and cannot qualify physical feasibility.

### S02 exit criteria

- The M02 plan boundary is explicit and no duplicate ExecutionPlan schema is introduced.
- M01/M03 hard constraints are preserved.
- M07/M08/M09 evidence has compatible exact scope, provenance and freshness.
- M10/M11/M12/M16/M09 handoffs remain separated by authority.
- Feasibility, rejection, stale/conflict/unknown and no-safe-plan paths are explicit.
- S03 defines the prediction/calibration interface; numeric policy budgets and acceptance thresholds remain deferred to S04 and Final Technology Review.
- No runtime, test or product code is introduced.

### S02 research and sources

Official documentation and design inferences are recorded in [M10 S02 research](../research/M10-S02-HARDWARE-AWARE-PLAN-COMPILATION.md). Those sources motivate separate evidence dimensions for allocator scope, provider capability, hardware partition identity and actual allocation/placement. They do not select an IRIS runtime, device allocator or provider.

### Open decisions carried forward

- Exact M02 API/record by which M10 submits alternatives and receives canonical acceptance.
- Minimum M08 evidence class and coverage needed for each S03 risk estimate.
- Which M09 facts must be re-read immediately before reservation, and which owner handoff authorizes that read.
- How S03 risk outcomes constrain alternatives without merging predictive and measured facts.
- How S04 policy modes rank eligible alternatives while honoring M01/M03 constraints.
- Which M12 placement evidence is required after M10 returns a bounded candidate set.

## S03 — Predictive OOM, thermal and quality-risk models

Status: `COMPLETE_FOR_MODULE_PLANNING`
Session base: `8d068d1cf9ef604aef8506ec879b7a382ec1b738`
Exact head: `db9fc7e0f0e7615c075cfaee3debec3a3990697b`; Governance `36034416554 / 107750841548` — **PASS**
Protected squash merge / exact-main: `8768661ee348815ec5b1eb6e32bc85505fa10b17`; Governance `36034538318 / 107751237481` — **PASS**
Implementation authority: **NOT ADMITTED**

### Objective

Define three independently evidenced estimates that can inform S04 policy semantics: allocation-failure/OOM risk, thermal-limit risk, and M01 Fidelity Contract violation risk. S03 specifies the evidence, calibration, uncertainty and abstention behavior. It does not select a model, numeric horizon, risk budget, threshold, minimum sample count or runtime action.

### Separate prediction targets

| Risk family | Candidate target and authoritative outcome | Evidence M10 may consume | Must not be conflated with |
|---|---|---|---|
| OOM / allocation failure | A validated run outcome whose owning runtime/provider evidence confirms allocation failure or resource-exhaustion failure under a versioned label. | M09 resource snapshots, leases and pressure outcomes; M07 hardware/runtime identity; M08 exact-scope capability evidence; M11/M16 outcome receipts where authorized. | Memory pressure, low free-memory snapshot, timeout, cancellation, generic process failure or an unrelated provider error as if each were a confirmed OOM. |
| Thermal | A versioned future event target such as a thermal-limit or thermal-throttle event, with temperature, active throttle reason and time-accumulated violation treated as separately sourced observations. Power-limit throttling is a distinct event family. | M07 read-only sensor capability, telemetry samples and exact device/partition/driver/runtime identity; M08 workload-bound empirical evidence; M09 resource context by reference. | High temperature alone, reduced clocks alone, power cap, unsupported telemetry and thermal throttling as interchangeable labels. |
| Quality | A future M01 evaluator/Fidelity Contract outcome that fails an applicable quality obligation for the pinned output class and contract revision. | M01 evaluator, contract and review receipts; M03 protected constraints; exact workload/model/workflow versions and applicable M08 evidence. | M10's own score, successful execution, resource scarcity, or a weaker surrogate metric as a quality decision or promotion. |

M01 remains the sole quality evaluation and promotion authority. M03 constraints remain hard obligations. OOM and thermal labels retain their owning runtime/hardware provenance; M10 may consume them but cannot rewrite their meaning.

### Candidate estimate record

Each risk estimate is a separate typed record, not one aggregate “risk” scalar. The planning candidate carries:

- risk-family identifier and versioned target/label definition;
- prediction horizon/window and observation unit, once those are approved in later policy review;
- exact workload-signature revision and pinned M02/M01/M03/M07/M08/M09 plus applicable M11/M14/M16/M50/M54/M56 evidence references;
- hardware model, partition/profile, driver/runtime, provider/workflow and model versions material to that estimate;
- estimator family/version, training and calibration data lineage, calibration method and evaluation split;
- point/range/set output, uncertainty representation, applicability slice and support summary;
- capture time/window, source capability, freshness/validity state and drift/OOD assessment;
- label provenance, censoring/abort/unknown disposition, and a human-readable reason for abstention or limitations.

The record is a planning interface candidate, not a new canonical ExecutionPlan schema. M02 retains its plan contract and lifecycle. S04 may consume the three risk records to rank or reject otherwise admissible alternatives; it cannot turn missing or uncalibrated risk into evidence of safety.

### Model and uncertainty candidates

Compare these families during planning and technology review; none is selected or frozen by S03:

1. **Owner-backed deterministic bounds and rules.** Use explicit M07/M08/M09 evidence and conservative bounds where semantics support a hard feasibility statement. A bound is not a learned probability.
2. **Empirical classification, regression and tail/quantile estimation.** Fit against validated, versioned labels and exact workload/hardware/runtime strata; expose uncertainty and limited support.
3. **Calibrated intervals or set-valued/risk-controlling prediction.** Conformal risk-control methods are candidates only with their calibration assumptions stated. Distribution-free expected-risk or marginal-coverage results do not imply conditional guarantees for every workload, device or subgroup.
4. **Sequential/time-series calibration.** Consider only if event telemetry is genuinely ordered and the method's assumptions match the observed process. A method designed for non-exchangeable time series is still not assumption-free.
5. **Abstention and conservative fallback.** Return unknown/indeterminate when evidence does not support a calibrated estimate; do not impute a low-risk value.

Keep measured resource facts, empirical capability, telemetry observations and model outputs in separate evidence dimensions. A deterministic S02 admissibility rejection cannot be overridden by a favorable statistical estimate.

### Calibration and evaluation protocol

- Define the label before fitting; record label version, owner, censoring and ambiguous terminal outcomes. Exclude or separately classify timeout, cancellation, worker loss, invalid benchmark and incomplete telemetry rather than silently labeling them safe.
- Split by workload instance and run lineage so repeated frames, retries, near-duplicate prompts or repeated measurements from one run cannot leak across train/calibration/test partitions. Hold out independent workload families and hardware/runtime cohorts for generalization checks.
- Bind every calibration and evaluation result to the exact workload signature, GPU/partition, driver/runtime, provider/workflow, model, benchmark protocol and M09 resource context that materially affect it.
- Evaluate each risk family separately using suitable proper scoring and reliability/calibration diagnostics; include false-safe and missed-event rates, applicable risk/coverage or interval-coverage summaries, abstention coverage, subgroup and worst-group behavior, and uncertainty around the reported metrics.
- Preserve temporal order for sequential telemetry. Report when stationarity, exchangeability, mixing, independence, label completeness or other method assumptions are not established. Distribution shift invalidates a copied calibration claim unless an approved method explicitly covers that shift.
- Synthetic fixtures may test parsing, provenance, calibration bookkeeping and abstention mechanics. They cannot establish real-device calibration, physical safety or predictive accuracy.
- No acceptance percentage, numerical margin, minimum sample count, hardware-specific cutoff, prediction horizon or target risk budget is selected in S03. Those choices require evidence, owner review and later policy/final-review approval.

### Freshness, drift and abstention

The estimate's applicability is scoped to the evidence slice and capture window that support it. Revalidation or abstention is required when a material identifier changes, evidence becomes stale, a telemetry source is unsupported, inputs conflict, labels are ambiguous, sample support is inadequate, or drift/OOD checks fail. The exact freshness limits and support thresholds remain open.

Abstain with an explicit reason and an indeterminate/no-safe-plan candidate when:

- a mandatory owner reference or label is missing, stale, conflicted, quarantined or outside its declared scope;
- the hardware partition, runtime/driver, provider/workflow, model or workload signature is outside the validated slice;
- required thermal, resource or quality evidence is unsupported or incomplete;
- calibration assumptions are materially violated, drift is detected, or uncertainty spans a later policy gate;
- evidence cannot distinguish an event from timeout, cancellation, censoring or unrelated failure.

An unsupported sensor is not a healthy reading. A lack of observed failures is not proof of zero risk. Unknown risk cannot authorize a plan.

### Authority and lifecycle boundary

M10 emits the separate risk estimates, applicability and reasons to the S04 policy stage. M10 does not start or stop work, select placement, reserve resources, alter M01/M03 obligations, tune device controls, or dispatch workers. M09 owns resource truth and reservations; M11 owns worker lifecycle; M12 owns placement; M16 owns provider/workflow compilation; M56 owns observability aggregation. S05 owns outcome-feedback and model-update lifecycle; S03 does not auto-train, auto-calibrate or mutate model versions.

### S03 exit criteria

- OOM, thermal and quality targets have distinct owner-approved label definitions and provenance.
- Prediction records preserve scope, versions, freshness, calibration, uncertainty and abstention reason.
- Candidate model families and assumptions are compared without selecting an unjustified guarantee.
- Evaluation addresses leakage, drift, class imbalance/rare events, subgroup performance and false-safe behavior.
- Unknown, unsupported, stale, conflicting and out-of-distribution evidence cannot be treated as safe.
- M01/M03 hard obligations and M02/M07/M08/M09/M11/M12/M14/M16/M50/M54/M56 authority boundaries remain intact.
- No numeric policy thresholds, model choice, physical calibration claim, auto-learning loop or product/runtime/test implementation is introduced.

See [M10 S03 research](../research/M10-S03-PREDICTIVE-RISK-CALIBRATION.md) for the primary-source basis and open assumptions.

## S04 — ECO / BALANCED / QUALITY / MAX / CUSTOM policy semantics

Status: `COMPLETE_FOR_MODULE_PLANNING`
Session base: `8768661ee348815ec5b1eb6e32bc85505fa10b17`
Exact head: `add4344d6b1a495f1aeeb23af0d57fdcddde381e`; Governance `36037625164 / 107761547909` — **PASS**
Protected squash merge / exact-main: `96aee147e701c6d716cfbcf5f2be524ee5d751e7`; Governance `36037710495 / 107761836741` — **PASS**
Implementation authority: **NOT ADMITTED**

### Objective

Define versioned named policy profiles as explicit preferences over S02-admissible alternatives, using S03's separate risk estimates. Policy modes may rank or bound choices; they cannot rewrite hard obligations, improve evidence quality, or authorize execution.

### Precedence and decision sequence

1. **Pin the request.** Bind the exact M02 target graph/revision, M01 output class/Fidelity Contract, M03 intent/constraints, S01 workload signature, S02 candidate set, S03 risk records, and applicable M07/M08/M09/M50/M54 evidence. Do not resolve implicit `latest`.
2. **Validate the profile.** Require a known mode, supported metric definitions, units, directions, authorized budgets and revision. Unknown fields, unresolved conflicts and missing MAX objectives are invalid policy inputs.
3. **Apply hard constraints.** Filter alternatives against M02 causality/permissions, M01 quality obligations, M03 protected semantics, M07 compatibility, M08 demonstrated capability, M09 current feasibility, M50 authorized cost/quality boundaries and M54 security policy. Hard constraints are not objective weights.
4. **Apply risk admissibility.** Consume the separate S03 OOM, thermal and quality-risk records only through explicit policy/owner-approved applicability and risk-budget references. S04 chooses no numeric budget in this candidate. Unknown, stale or out-of-scope risk cannot count as low risk.
5. **Rank or preserve alternatives.** Apply the selected mode's disclosed preference rule only to surviving alternatives. Where the profile does not decide a trade-off, return a bounded nondominated set or an explicit unresolved/no-safe-plan result; do not hide the trade-off in a scalar.
6. **Explain the result.** Return the profile revision, hard constraints, risk evidence, preference order/weights, rejected and retained alternatives, tie-break and any abstention reason through the M02-compatible handoff. M10 does not serialize a competing canonical ExecutionPlan.

### Candidate mode semantics

| Mode | Preference semantics over admissible alternatives | Required inputs and limits |
|---|---|---|
| **ECO** | Prefer lower authorized resource demand and cost; use measured energy/thermal burden only when owner evidence supports a comparable metric. Latency may be traded only within explicit request limits. | M01/M03 obligations remain hard. M09 owns resource truth; M50 owns broader cost/quality routing. Unknown cost/energy is not zero or a favorable score. |
| **BALANCED** | Preserve alternatives that are nondominated across the declared latency, quality-evidence, resource, cost and thermal dimensions. A recommendation may use a published, versioned preference profile; otherwise return the bounded set with trade-offs explained. | No hidden universal weights. The default preference profile and supported dimensions remain decisions for evidence-based review before contract freeze. |
| **QUALITY** | Prefer alternatives with stronger applicable M01 quality evidence and margin against the requested Fidelity Contract while meeting authorized resource/cost limits. | M01 alone evaluates quality and controls promotion. More compute, a model name or a local proxy score is not proof of better quality. |
| **MAX** | Maximize one explicitly named objective, such as an owner-defined latency, throughput or quality-evidence metric, among hard-admissible alternatives. | Require objective identifier, unit, direction, scope and authorized trade-offs. “Maximize everything” is undefined; absent or incomparable objectives yield invalid-policy/no-safe-plan. |
| **CUSTOM** | Apply an explicit user/operator preference order, permitted objective weights, constraints and fallback permissions. | Bind the profile to an immutable revision and authorization. Weights must name units/scales and cannot override hard gates. Reject unknown fields and incompatible dimensions instead of inventing defaults. |

Mode labels describe preferences, not service guarantees. Each mode retains bounded alternatives and a deterministic, disclosed tie-break. If an authorized profile permits fallback, the fallback mode and transition conditions must be pinned and explained before planning; no silent QUALITY→ECO, MAX→BALANCED or CUSTOM rewrite is allowed.

### Policy profile and decision receipt candidates

A versioned profile reference should identify:

- mode and profile revision;
- requested objective(s), preference ordering and any explicit weight/normalization method;
- hard constraints and owner-issued budget/capability references;
- S03 risk-family applicability and risk-budget references without collapsing risk outputs;
- permitted fallback modes/transitions and required user/operator authorization;
- deterministic tie-break semantics and bounded alternative count.

A decision receipt should bind the profile, exact source revisions, candidate alternatives, hard-gate outcomes, separate risk dispositions, applied preferences, rejected alternatives, recommendation rationale and no-safe-plan/indeterminate reason. These are candidate fields for later contract review; M02 remains canonical plan owner and M56 owns observability aggregation.

### Conflict, fallback and no-safe-plan behavior

- Hard-constraint conflict, infeasible constraints, invalid profile, unsupported objective, stale mandatory evidence or no applicable risk-policy reference yields a typed invalid/indeterminate/no-safe-plan result.
- A lower-priority preference can be relaxed only when the versioned profile explicitly permits that relaxation and the explanation records it. Hard M01/M03/M02/M54 obligations cannot be relaxed by a mode.
- If a user-selected mode has no feasible alternative, do not silently switch modes or change output class, fidelity, precision, seed, semantics, cost ceiling or execution permissions.
- Policy selection is not placement, resource reservation, worker dispatch, provider compilation or execution. Owning modules revalidate dynamic evidence at their handoff.

### Planning evidence and review cases

The eventual validation plan should include cases where: every alternative violates one hard constraint; ECO lacks comparable energy/cost evidence; BALANCED returns multiple nondominated choices; QUALITY has no M01 evidence for the requested class; MAX omits or mismatches its objective unit; CUSTOM contains an unknown field or unauthorized weight; risk is unknown/stale; and an explicitly authorized fallback is or is not available. These are future test/evidence obligations, not tests added in this planning PR.

### Open S04 decisions

- Which measurable objective dimensions and units are supported by M08/M09/M50 and which remain unrankable.
- Whether BALANCED has a default published preference order or always returns a nondominated set until the operator chooses.
- Which MAX objective identifiers are valid, with their owner, scope and comparability rules.
- How explicit risk-budget references are versioned and approved without duplicating M01/M50 authority.
- Which fallback transitions require fresh user confirmation and which, if any, may be preauthorized.
- Deterministic tie-break and alternative-set bounds compatible with M02's canonical plan contract.

### S04 exit criteria

- Named modes have distinct, testable preference semantics and all share the same hard-constraint gates.
- Policy profiles are revision-pinned, unit-aware, authorized and explicit about trade-offs, weights and fallback.
- ECO, BALANCED, QUALITY, MAX and CUSTOM cannot silently weaken M01/M03 or owner-issued safety/resource constraints.
- MAX requires an explicit objective; BALANCED exposes unresolved trade-offs; CUSTOM rejects unsupported input.
- Missing or stale S03 risk evidence and infeasible constraints produce explicit no-safe-plan/indeterminate results.
- Result explanations bind exact inputs, rejected alternatives, preference behavior and deterministic tie-break.
- M02/M01/M03/M07/M08/M09/M11/M12/M13/M14/M16/M50/M54/M56 authority boundaries remain intact.
- No solver, numerical weight, risk threshold, resource budget, implementation or runtime action is selected by this candidate.

See [M10 S04 research](../research/M10-S04-POLICY-SEMANTICS.md) for the primary-source basis and open method choices.

## S05 — Observed-result learning loop and explainable decisions

Status: `COMPLETE_FOR_MODULE_PLANNING`
Session base: `96aee147e701c6d716cfbcf5f2be524ee5d751e7`
Exact head: `fc1fa4959697b88fbfbe303736517aef52d9bc91`; Governance `36038801813 / 107765474152` — **PASS**
Protected squash merge / exact-main: `54d85d3491d4cc21e95fc2f9042c53d2852ceb88`; Governance `36038905218 / 107765823628` — **PASS**
Implementation authority: **NOT ADMITTED**

### Objective

Define how M10 consumes observed outcomes to improve future risk estimates while preserving owner authority, dataset/model provenance, reproducibility, privacy and a controlled rollback path. S05 does not implement online learning, change policy automatically, relabel upstream evidence or promote a model on its own.

### Outcome and decision receipts

A candidate append-only receipt binds:

- exact M02 request/graph revision; S01 signature; S02 bounded alternatives; S03 risk records; and S04 policy-profile revision;
- chosen/executed alternative, alternatives considered but not selected, selection reason and any authorization/fallback used;
- exact hardware/partition, driver/runtime, provider/workflow, model, benchmark and M09 resource context material to the run;
- owner-issued terminal outcome references and capture windows from M01/M07/M08/M09/M11/M16 and other applicable authorities;
- distinct predicted risk, observed sensor/resource facts, terminal label, censoring/abort/unknown state and label-validation receipt;
- timestamps, schema/source versions, integrity reference and permitted privacy/retention classification.

M10 records predictions and references owner outcomes; it does not create device truth, decide M01 quality, infer a confirmed OOM from pressure, or convert an incomplete run into a safe label. Corrections append a superseding receipt with provenance; prior records are not silently rewritten. Raw prompts, media and credentials are excluded by default; any exception requires M54-compatible purpose, access, minimization and retention authority.

### Candidate feedback and model lifecycle

The planning candidate separates these stages:

1. **Ingest.** Accept only owner-issued, revision-pinned receipts with integrity, scope, source capability and privacy/retention metadata.
2. **Validate labels.** Resolve outcomes under the owning M01/M07/M08/M09/M11/M16 contracts. Keep ambiguous, censored, conflicting, unsupported or incomplete results unknown or quarantined.
3. **Freeze a dataset snapshot.** Record feature/label definitions, source revisions, collection window, exclusions, cohort coverage, transformations and lineage in an immutable manifest.
4. **Prepare a candidate evaluation package.** A future owner-authorized training pipeline may produce an immutable candidate; M10 records its lineage and evaluation inputs. M14 remains authority for model fitness; M10 cannot self-certify, overwrite or silently activate a model.
5. **Evaluate independently.** Re-run S03 calibration and S04 decision cases against frozen time-held-out and workload/hardware/runtime cohorts. Compare the candidate with the currently approved reference, including false-safe behavior, calibration, abstention, subgroup/worst-group results and policy-decision changes.
6. **Review and approve.** Require explicit owner review of labels, model fitness, M01 quality implications, M54 privacy/security and the applicable governance gate before any candidate is eligible for use.
7. **Promote by immutable reference.** A future authorized lifecycle may point policy to a new model/dataset/evaluation version. Preserve prior approved versions, applicability scopes, approval receipts and decision history.
8. **Rollback reproducibly.** Revert only to a still-approved compatible version, with a reason, trigger evidence and an auditable policy/model transition receipt. Rollback cannot restore a version whose scope or source contract is invalid.

No update cadence, rollout percentage, performance acceptance threshold or automatic promotion behavior is selected by S05. Exact promotion and rollback owners remain a contract-freeze decision, respecting M14 and governance authority.

### Bias, drift and incomplete feedback

- Outcomes exist only for executed alternatives. A non-selected plan has no observed result; do not fabricate counterfactual labels or treat “not run” as failure/success.
- Log the full considered candidate set and selection policy so evaluation can identify mode/selection effects. Observational feedback alone does not prove causality.
- Keep retries, frames and related executions in one lineage group during evaluation splits; preserve time order for sequential calibration and drift review.
- Retain cancellations, timeouts, process loss, invalid benchmarks and partial telemetry as distinct censored/unknown outcomes, not negative or safe labels.
- A change in hardware partition, runtime/driver, provider/workflow, model, M01 contract, M09 resource semantics, label definition or policy profile may invalidate applicability. Re-evaluate or quarantine the affected slice; never broaden the model's declared scope silently.
- Drift alarms or missing provenance pause use for the affected slice and return to S03 abstention/no-safe-plan behavior pending owner review.
- S05 does not authorize exploration workloads, shadow dispatch, canary execution or additional measurement that consumes resources; those require separate M11/M12/M09 and operator authorization.

### Explanation and reproducibility

A decision explanation should make the chain inspectable:

- the exact policy/profile, candidate set, hard constraints and S03 evidence used;
- why alternatives were rejected, retained or recommended;
- which measurements were observed versus estimated/predicted, their support/freshness and uncertainty;
- model, dataset, calibration, label and owner-receipt versions;
- known limitations, OOD/drift/abstention status and any human/owner review;
- replay inputs and compatible artifacts needed to reproduce the decision.

An explanation must describe the actual policy path and evidence. It must not present correlation, feature attribution or an after-the-fact narrative as causal proof. Keep explanations bounded and redact information outside the viewer's authorization.

### S05 validation cases and exit criteria

Future evidence should prove that: invalid owner labels remain quarantined; corrections preserve prior receipts; dataset/model/evaluation versions replay exactly; time/workload leakage is prevented; non-selected alternatives stay unlabeled; model drift suspends only the affected applicability slice; promotion requires explicit evidence and approval; rollback restores a compatible approved version; explanations distinguish prediction from observation; and privacy/retention limits are enforced. These are planning obligations, not tests added in this PR.

S05 is ready for planning review when:

- outcome receipts preserve exact provenance, source ownership, scope, censoring and privacy state;
- labels cannot be mutated or promoted by M10;
- dataset snapshots and candidate model/evaluation packages are immutable and reproducible;
- candidate evaluation reuses S03 risk calibration and S04 policy cases on independent/time-aware splits;
- selection bias, missing counterfactuals, drift, quarantine and rollback are explicit;
- explanations connect policy, evidence, constraints and alternatives without unsupported causal claims;
- M01/M02/M03/M07/M08/M09/M11/M12/M14/M16/M50/M54/M56 authority boundaries remain intact;
- no online learning, silent promotion, numerical gate, rollout setting or implementation is admitted.

### Open S05 decisions

- Which owner issues each terminal receipt and resolves conflicting or delayed labels.
- M14's exact fitness/evaluation handoff and model-artifact lifecycle.
- M01 approval requirements for evaluator or Fidelity Contract changes.
- M54 retention, redaction, access and deletion semantics for training/evaluation evidence.
- Which re-evaluation cadence, drift detectors, quarantine triggers and rollback authority are supported by evidence.
- Whether any shadow/canary measurement is admitted later, and its M09/M11/M12/operator authorization.

See [M10 S05 research](../research/M10-S05-OBSERVED-RESULT-LEARNING.md) for the primary-source basis and unresolved governance choices.

## Final Technology Review

Status: `FINAL_TECHNOLOGY_REVIEW_CANDIDATE`
Review base: `54d85d3491d4cc21e95fc2f9042c53d2852ceb88`
Scope: S01–S05, owner contracts and linked research
Implementation authority: **NOT ADMITTED**

### Review method and verdict

Compare the five session candidates against owner authority, evidence provenance/scope, unknown-state behavior, portability, reproducibility, security/privacy, explainability and future compatibility. A named technology is not accepted because it is novel or proprietary. Any implementation selection still requires an admitted contract and implementation work order.

**Candidate verdict:** the S01–S05 architecture is internally coherent and provider-neutral enough to proceed to the M11–M60 Forward Compatibility Scan, subject to this review's recorded deferrals and PR Governance. This is not the independent planning audit, contract freeze, hardware validation or implementation admission.

### Cross-session technology disposition

| Area | Review disposition | Reason / carried decision |
|---|---|---|
| Workload signature and identity | **Accept for contract candidate** | Use an immutable typed workload projection with exact owner references and explicit applicability/unknown state. Keep raw prompts/media out by default. Serialization, digest algorithm and storage are unresolved owner/API decisions. |
| Plan compilation | **Accept M02 adapter boundary** | M02 remains the canonical ExecutionPlan and lifecycle owner. M10 returns bounded, revision-pinned alternatives; no second plan schema, placement, reservation or dispatch authority. |
| Hardware/resource evidence | **Accept owner-issued composition** | Bind M07 device/partition/runtime facts, M08 exact-scope empirical capability and M09 current resource state separately. Allocator and device-global memory, reported and allocatable capacity, parent and partition identity remain distinct. |
| Predictive risk | **Accept separate output interface; defer estimator** | Keep OOM, thermal and M01 quality-contract risk separate, each with target, calibration scope, uncertainty and abstention. Deterministic bounds, empirical models, conformal/risk-control methods and sequential calibration remain candidates; no IRIS method is selected without owner-validated labels and calibration data. |
| Thermal telemetry | **Accept M07 adapter and capability boundary** | Preserve source-specific sensor capability, timestamps, unsupported states and reason semantics. NVML and AMD SMI evidence cannot be collapsed into an assumed universal signal; M10 does not tune hardware. |
| Policy and optimization | **Accept constraints-first, explicit preference semantics** | Apply hard M02/M01/M03 and owner gates before mode preferences. Keep unresolved BALANCED choices as bounded alternatives; require an explicit MAX objective; reject hidden weights and silent mode changes. No solver or numerical weights are selected. |
| Outcome learning | **Accept evidence lifecycle; defer pipeline** | Use owner-issued receipts, immutable dataset/model/evaluation lineage, offline review, drift quarantine and reproducible rollback. M14 owns model fitness; M01/M54 retain quality and privacy/security authority. No online learning or self-promotion. |
| Explanation and observability | **Accept evidence-linked explanation** | Explain the actual policy path from exact inputs, constraints, risks and alternatives. Do not infer causal explanations from observational features. M56 remains observability aggregation owner. |

### Rejected or deferred approaches

- **Reject one scalar for OOM, thermal and quality risk:** targets, labels and owners differ.
- **Reject pressure-as-OOM and clock-drop-as-thermal labels:** observations are not the authoritative terminal outcome.
- **Reject unsupported-as-zero/safe:** missing sensor, stale evidence and absent labels remain unknown and can force abstention.
- **Reject partial provider coverage or preferred allocation as proof of execution:** M16/M12 handoffs and M02 plan acceptance remain authoritative.
- **Reject hidden weighted objectives and penalty-based softening of hard gates:** trade-offs must be named, scoped and authorized.
- **Reject an unqualified MAX mode:** a metric, unit, direction and scope are required.
- **Reject online self-training, automatic promotion and synthetic physical claims:** there is no validated IRIS evidence or admitted lifecycle for those actions.
- **Defer solver/vendor, canonical record encoding, common telemetry projection, estimator, numeric horizons/risk budgets, supported MAX metrics, BALANCED default, training store, registry and rollout semantics.**

### Technology/prior-art posture

S01–S05 use public primary research and official API/platform documentation for known method behavior. The sources support candidate designs and expose assumptions; they do not establish IRIS predictive accuracy, physical safety, ownership of a method or patentability. No source-library, optimizer, model registry, GPU telemetry SDK or provider runtime is selected as a product dependency here.

Detailed source findings remain in [S01](../research/M10-S01-WORKLOAD-SIGNATURE-ENGINE.md), [S02](../research/M10-S02-HARDWARE-AWARE-PLAN-COMPILATION.md), [S03](../research/M10-S03-PREDICTIVE-RISK-CALIBRATION.md), [S04](../research/M10-S04-POLICY-SEMANTICS.md) and [S05](../research/M10-S05-OBSERVED-RESULT-LEARNING.md).

### Risk review and required compatibility checks

| Risk | Required control before freeze |
|---|---|
| Labels or hardware evidence are incomplete, stale or mismatched | Owner contract, exact scope/version binding, explicit unknown and S03 abstention |
| Model calibration is copied across devices/workflows | Hardware/runtime/workload cohort validation; out-of-scope inference prohibited |
| Policy silently weakens quality, intent, cost or security | Hard-gate ownership, versioned preferences and no-safe-plan path |
| Learning loop trains on selected-only or invalid outcomes | Immutable receipts, censoring/selection metadata, grouped/time-aware validation, no fabricated counterfactuals |
| Mode decision cannot be explained or replayed | Decision receipt with exact profile, evidence, alternatives, constraints and artifact versions |
| Future modules require new handoffs | M11–M60 scan; carry only owner-approved extension references into the contract candidate |

### Review acceptance and next gate

- S01–S05 exact-main evidence is reconciled in the canonical checkpoint.
- Every candidate technology has an accept/defer/reject disposition and named owner boundary.
- No unresolved decision silently becomes a runtime default.
- No code, model, benchmark claim, numeric risk threshold or solver dependency is admitted.

After this review candidate passes exact-head Governance, protected squash and exact-main Governance, proceed to the M11–M60 Forward Compatibility Scan. Then prepare the versioned contract candidate and independent planning audit. Keep implementation NOT ADMITTED.

## Required planning lifecycle

Complete S01-S05; conduct technology discovery and a Final Technology Review; scan M11-M60 for authority/compatibility requirements; produce a versioned contract candidate; independently audit with zero unresolved HIGH/CRITICAL findings; merge through protected gates; validate exact main; and reconcile project state.

## STOP CONDITION

Do not freeze or implement M10 from this S01 document alone. M10 product/runtime implementation remains NOT ADMITTED and NOT STARTED until the full planning lifecycle and a separate implementation Work Order / Context Lock / Evidence preflight pass.
