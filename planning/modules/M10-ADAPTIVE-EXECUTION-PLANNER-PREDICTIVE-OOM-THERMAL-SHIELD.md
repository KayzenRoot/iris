# M10 — Adaptive Execution Planner & Predictive OOM/Thermal Shield

Status: `PLANNING_S02_CANDIDATE_PENDING_GOVERNANCE`
Module: **M10 Adaptive Execution Planner & Predictive OOM/Thermal Shield**
Planning Work Order: [Issue #68](https://github.com/KayzenRoot/iris/issues/68)
Authorized planning base: `b6456670a7c61621db1d3b3fc6d55487adb9cd64`
S02 session base: `fc1a3c954a1629b9e9a4c45c4e557a7832c290d7`
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
| S02 | Hardware-aware execution plan compilation | CANDIDATE_COMPLETE_PENDING_GOVERNANCE |
| S03 | Predictive OOM, thermal and quality-risk models | NOT_STARTED |
| S04 | ECO / BALANCED / QUALITY / MAX / CUSTOM policy semantics | NOT_STARTED |
| S05 | Observed-result learning loop and explainable decisions | NOT_STARTED |

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

Status: `CANDIDATE_COMPLETE_PENDING_GOVERNANCE`

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
4. **Build bounded alternatives.** Describe only alternatives represented by owner-issued options and accepted by the M02 plan contract. S04 owns policy-mode preferences and ranking semantics; S03 owns risk thresholds and calibration.
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
17. S02 does not set OOM, thermal or quality-risk thresholds; those remain S03/S04 planning inputs.
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
- Policy weights and prediction thresholds remain deferred to S03/S04.
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

Status: `NOT_STARTED`

Compare analytical bounds, empirical/quantile models, calibrated prediction intervals and conservative rules. Define separate labels, horizons, calibration/freshness, drift handling, abstention and evidence requirements. Do not promise risk guarantees outside proven assumptions.

## S04 — ECO / BALANCED / QUALITY / MAX / CUSTOM policy semantics

Status: `NOT_STARTED`

Define named policy semantics as bounded preferences and explicit constraints. Preserve M01 quality authority, M03 protected semantics, user/operator authorization and an explicit refusal/no-safe-plan outcome.

## S05 — Observed-result learning loop and explainable decisions

Status: `NOT_STARTED`

Define outcome receipts, feedback provenance, label validity, versioned model updates, rollback, drift quarantine, explanations and reproducible re-evaluation. Learning cannot mutate upstream evidence or silently change policy.

## Required planning lifecycle

Complete S01-S05; conduct technology discovery and a Final Technology Review; scan M11-M60 for authority/compatibility requirements; produce a versioned contract candidate; independently audit with zero unresolved HIGH/CRITICAL findings; merge through protected gates; validate exact main; and reconcile project state.

## STOP CONDITION

Do not freeze or implement M10 from this S01 document alone. M10 product/runtime implementation remains NOT ADMITTED and NOT STARTED until the full planning lifecycle and a separate implementation Work Order / Context Lock / Evidence preflight pass.
