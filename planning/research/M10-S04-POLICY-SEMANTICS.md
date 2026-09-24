# M10 S04 — Policy semantics and objective handling

Status: `CANDIDATE_COMPLETE_PENDING_GOVERNANCE`
Work Order: [Issue #68](https://github.com/KayzenRoot/iris/issues/68)
S04 session base: `8768661ee348815ec5b1eb6e32bc85505fa10b17`
Research checked: 2026-09-24
Implementation authority: **NOT ADMITTED**

## Purpose

Ground the S04 policy candidate in constraint and multiobjective decision concepts. These sources demonstrate alternative ways to express feasibility, objective priorities and trade-offs; they do not select an optimizer, solver or weighting scheme for IRIS.

## Findings

### Separate feasibility constraints from ranking objectives

Google's [OR-Tools CP-SAT documentation](https://developers.google.com/optimization/cp/cp_solver) describes a model built from variables, constraints and an objective. IBM's [multiobjective optimization guide](https://www.ibm.com/docs/en/icos/22.1.1?topic=optimization-solving-multiple-objective-problems) describes objectives solved hierarchically by priority; IBM's [objective specification guide](https://www.ibm.com/docs/en/icos/22.1.2?topic=optimization-specifying-multiple-objective-problems) documents explicit priority, weight and absolute/relative tolerance attributes.

**Design implication (inference):** M10 policy resolution should first filter alternatives through non-negotiable M01/M03/M02 and owner-issued admissibility gates, then apply a disclosed preference method. If a weighted/blended objective is ever used, its dimensions, scale, units and authority must be explicit. These sources do not imply that IRIS should adopt OR-Tools, CPLEX, or either solver's semantics.

### Multiobjective choice may retain several efficient alternatives

Wang et al., [A Tutorial on Multiobjective Optimization: Fundamentals and Evolutionary Methods](https://link.springer.com/article/10.1007/s11047-018-9685-y), reviews Pareto dominance and the use of nondominated solution sets when objectives conflict. **Design implication (inference):** a BALANCED profile can preserve a bounded nondominated set when no authorized preference resolves the trade-off. M10 should not manufacture a unique answer by silently combining incomparable measures.

### IRIS owner contracts constrain policy authority

- M01 owns the Fidelity Contract, quality evaluator and promotion authority.
- M02 owns Production Graph causality, canonical ExecutionPlan and production lifecycle.
- M03 owns protected intent and semantic constraints.
- M07/M08/M09 own hardware/runtime facts, empirical capability and resource truth.
- M50 owns broader cost/quality routing; M54 owns security policy.
- S03 provides separate, scope-bound OOM, thermal and M01 quality-risk evidence; S04 applies only explicitly authorized policy references to those predictions.

**Design implication (inference):** ECO/BALANCED/QUALITY/MAX/CUSTOM are preference profiles over owner-admissible options. They cannot modify upstream contracts, treat unknown metrics as zero, authorize a placement/reservation/worker action, or silently downgrade the requested output class.

## S04 candidate requirements

1. Preserve hard constraints separately from soft objectives and record which owner supplies each.
2. Make mode semantics distinct, explicit, versioned and explainable.
3. Require a named metric, unit, direction and applicability scope for MAX.
4. Let BALANCED retain nondominated options or use a published, versioned preference profile; do not use hidden weights.
5. Permit weighted trade-offs in CUSTOM only when the operator supplies explicit units/scales, authorization and revision.
6. Treat cost, energy, latency, quality evidence and risk as distinct dimensions unless an owner-approved comparable metric exists.
7. Never interpret unsupported evidence as zero, safe or preferable; preserve abstention and no-safe-plan.
8. Disallow silent mode transitions and any relaxation of M01/M03/M02/M54 hard obligations.
9. Leave solver choice, numerical budgets, thresholds, weights, supported MAX objectives and balanced defaults open for later technology review and contract freeze.

## Sources

- Google, [OR-Tools CP-SAT Solver](https://developers.google.com/optimization/cp/cp_solver).
- IBM, [Solving Multiple Objective Problems](https://www.ibm.com/docs/en/icos/22.1.1?topic=optimization-solving-multiple-objective-problems).
- IBM, [Specifying Multiple Objective Problems](https://www.ibm.com/docs/en/icos/22.1.2?topic=optimization-specifying-multiple-objective-problems).
- Wang et al., [A Tutorial on Multiobjective Optimization: Fundamentals and Evolutionary Methods](https://link.springer.com/article/10.1007/s11047-018-9685-y).
- IRIS owner contracts: [M01](../modules/M01-EXTREME-QUALITY.md), [M02](../modules/M02-PROJECT-OS-PRODUCTION-GRAPH.md), [M03](../modules/M03-CREATIVE-BRIEF-INTENT-CONSTRAINT-COMPILER.md), [M07](../modules/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md), [M08](../modules/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md), [M09](../modules/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md), [M10 S03](M10-S03-PREDICTIVE-RISK-CALIBRATION.md).

## Limits

This is design research, not a solver-selection decision or implementation specification. A feasibility filter may have no valid solution, and a nondominated set does not imply an automatic final choice. S04 selects no operational risk target, numerical tolerance, default weight, exact balanced profile or runtime behavior.
