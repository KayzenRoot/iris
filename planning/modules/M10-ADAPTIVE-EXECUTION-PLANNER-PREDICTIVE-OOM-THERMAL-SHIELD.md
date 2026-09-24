# M10 — Adaptive Execution Planner & Predictive OOM/Thermal Shield

Status: `PLANNING_S01_COMPLETE_FOR_MODULE_PLANNING`
Module: **M10 Adaptive Execution Planner & Predictive OOM/Thermal Shield**
Planning Work Order: [Issue #68](https://github.com/KayzenRoot/iris/issues/68)
Authorized planning base: `b6456670a7c61621db1d3b3fc6d55487adb9cd64`
Admission Governance: `36029536926 / 107734488887` — **PASS**
Implementation authority: **NOT ADMITTED**

## Governing intent

Plan the complete M10 capability for IRIS 1.0, not an MVP slice. M10 planning covers workload signatures, hardware-aware execution planning, predictive OOM/thermal/quality-risk estimates, policy semantics and observed-result learning with explanations.

This document is a planning candidate. No M10 product/runtime/test implementation is admitted.

## Canonical sessions

| Session | Scope | Status |
|---|---|---|
| S01 | Workload Signature Engine | COMPLETE_FOR_MODULE_PLANNING |
| S02 | Hardware-aware execution plan compilation | NOT_STARTED |
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

Status: `NOT_STARTED`

Plan the boundary from workload signatures plus exact M07/M08/M09 evidence to a bounded M02-compatible plan proposal, preserving M02 ExecutionPlan authority. Define candidate alternatives, feasibility, evidence requirements and no-safe-plan behavior.

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
