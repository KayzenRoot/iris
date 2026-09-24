# M10 S05 — Observed-result learning and explainability

Status: `CANDIDATE_COMPLETE_PENDING_GOVERNANCE`
Work Order: [Issue #68](https://github.com/KayzenRoot/iris/issues/68)
S05 session base: `96aee147e701c6d716cfbcf5f2be524ee5d751e7`
Research checked: 2026-09-24
Implementation authority: **NOT ADMITTED**

## Purpose

Record primary-source foundations for outcome provenance, model reporting and lifecycle risk management. These sources motivate documentation and evaluation evidence; they do not select an M10 learning algorithm, registry, monitoring vendor or approval workflow.

## Findings

### Model reports need scope and evaluation context

Mitchell et al., [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993), propose reporting intended uses and model performance across relevant evaluation conditions. **Design implication:** every candidate risk model needs a revision-pinned model/evaluation record describing target, validated scope, metrics, subgroup results, limitations and non-intended use; a model version without scope/evidence is not an admissible M10 prediction source.

### Dataset lineage needs its own record

Gebru et al., [Datasheets for Datasets](https://arxiv.org/abs/1803.09010), propose documenting a dataset's motivation, composition, collection process and recommended uses. **Design implication:** S05 should preserve an immutable dataset snapshot manifest, including outcome-label owners, time window, collection scope, exclusions, transformations, cohort coverage, privacy basis and known gaps. Model metrics cannot be interpreted without the data lineage that produced them.

### Risk governance spans the model lifecycle

NIST's [AI Risk Management Framework 1.0](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf) organizes risk work through Govern, Map, Measure and Manage functions. **Design implication (inference):** S05 must carry approvals, use scope, evaluation evidence and monitoring/quarantine decisions through a versioned lifecycle. The framework is a reference, not an IRIS certification or replacement for M01/M14/M54 ownership.

### Observed feedback is not complete counterfactual evidence

An execution produces an outcome only for the alternative actually run. M10 S02 defines a bounded candidate set and M10 S04 makes policy preferences explicit; M09/M11/M12 own resource commitment, process lifecycle and placement. **Design implication (inference):** S05 records the complete considered set and selection reason, but marks outcomes for unselected alternatives as unobserved. Training/evaluation must account for mode and selection effects and may not claim causal performance from observational receipts alone.

## S05 candidate protocol

1. Preserve immutable, owner-issued decision and terminal-outcome receipts with exact source, scope, timestamps, censoring, label version and authorization.
2. Keep prediction, observed telemetry/resource facts, terminal labels and policy decisions in separate fields.
3. Freeze datasets with a reproducible manifest and model/evaluation artifacts with a scope-specific model report.
4. Validate candidates offline using S03 calibration and S04 policy cases, temporal/workload-grouped holdouts and current approved references.
5. Quarantine missing, disputed, stale or out-of-scope labels and drift-affected evidence; return the affected prediction slice to abstention.
6. Require explicit owner/governance review before a candidate can be used; preserve immutable versions and a compatible, auditable rollback path.
7. Make explanations replayable from exact inputs and artifacts; distinguish evidence from interpretation and correlation from causation.
8. Apply M54 privacy, retention and access controls. Exclude raw prompts/media by default.
9. Keep online learning, automatic promotion, rollout/canary and retraining cadence open; S05 does not implement them.

## Sources

- Mitchell et al. (2019), [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993).
- Gebru et al. (2021), [Datasheets for Datasets](https://arxiv.org/abs/1803.09010).
- NIST, [Artificial Intelligence Risk Management Framework (AI RMF 1.0)](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf).
- IRIS owner contracts: [M01](../modules/M01-EXTREME-QUALITY.md), [M02](../modules/M02-PROJECT-OS-PRODUCTION-GRAPH.md), [M03](../modules/M03-CREATIVE-BRIEF-INTENT-CONSTRAINT-COMPILER.md), [M07](../modules/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md), [M08](../modules/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md), [M09](../modules/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md), [M10 S01](M10-S01-WORKLOAD-SIGNATURE-ENGINE.md), [M10 S02](M10-S02-HARDWARE-AWARE-PLAN-COMPILATION.md), [M10 S03](M10-S03-PREDICTIVE-RISK-CALIBRATION.md), [M10 S04](M10-S04-POLICY-SEMANTICS.md).

## Limits

This research is planning context, not an endorsed training pipeline, deployment process, certification or implementation. Model Cards and dataset documentation do not validate an IRIS model or label set. M10 implementation remains NOT ADMITTED.
