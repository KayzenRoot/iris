# M10 S03 — Predictive OOM, thermal and quality-risk calibration

Status: `CANDIDATE_COMPLETE_PENDING_GOVERNANCE`
Work Order: [Issue #68](https://github.com/KayzenRoot/iris/issues/68)
S03 session base: `8d068d1cf9ef604aef8506ec879b7a382ec1b738`
Research checked: 2026-09-24
Implementation authority: **NOT ADMITTED**

## Purpose

Record primary-source findings for the S03 planning candidate. The sources support separation of targets, careful calibration scope and explicit unknown states. They do not select an IRIS estimator, establish a universal guarantee, or provide production calibration data.

## Source findings and design implications

### Risk-control guarantees depend on the method's assumptions

Angelopoulos et al., [Distribution-Free, Risk-Controlling Prediction Sets](https://arxiv.org/abs/2101.02703), develop prediction sets that control expected loss at a chosen level for future test points under the method's setup. **Design implication:** risk-controlling calibration is a candidate for S03, but its guarantee must be tied to the calibration protocol and assumptions. It is not automatically a per-request, per-device, conditional or worst-subgroup guarantee.

Bates et al., [Non-Exchangeable Conformal Risk Control](https://arxiv.org/abs/2310.01262), extend expected monotone-loss control to non-exchangeable data using additional relevance/weighting structure. **Design implication:** time-ordered or drifting evidence needs an explicitly matched method and assumptions. Naming a non-exchangeable method does not make arbitrary runtime drift covered.

Xu and Xie, [Conformal Prediction Interval for Dynamic Time-Series](https://proceedings.mlr.press/v139/xu21h.html), introduce EnbPI and report approximate marginal coverage for dynamic time series under stated conditions on the regression function and stochastic errors. **Design implication:** sequential calibration may be evaluated for ordered thermal telemetry, but this paper does not validate IRIS device/workload risk labels, nor does it remove the need to test its assumptions.

### Thermal and power observations are different evidence

NVIDIA's [NVML clock-event reasons](https://docs.nvidia.com/deploy/nvml-api/api/group__nvmlClocksEventReasons.html) enumerate software thermal slowdown, hardware thermal slowdown and hardware power-brake slowdown as distinct reasons. **Design implication:** temperature, thermal limit/throttle state, power limiting and clock changes remain separate feature and outcome fields; a lower clock alone does not establish a thermal event.

AMD's [GPU violations documentation](https://rocm.docs.amd.com/projects/amdsmi/en/develop/conceptual/gpu-violations.html) distinguishes instantaneous throttle status/reason flags from time-accumulated power (PVIOL) and thermal (TVIOL) violation metrics, and documents hardware/API support variation. **Design implication:** M07 capability and source metadata must accompany each telemetry field. Unsupported or unavailable violation data is unknown, not zero or “not throttled.”

M07 S04 is the owner for read-only temperature, power, clocks, throttle reasons and memory-pressure telemetry. S03 consumes these versioned observations; it does not add a competing sensor schema or tune device controls.

### Resource pressure is not an OOM label

The M09 resource-state model deliberately distinguishes observed, estimated, committed, resident, reclaimable, external and unknown capacity. M09 owns leases, reservations and resource-pressure outcomes. **Design implication:** memory pressure and resource-shape transitions can be predictive features, but the OOM label must be a validated allocation-failure/resource-exhaustion outcome from its owning runtime/provider receipt. A generic failure, timeout or cancellation is not a confirmed OOM.

M08's benchmark evidence binds metric semantics, protocol version, sample count, uncertainty, environment and validity state to exact hardware/runtime/workload scope. **Design implication:** a benchmark, label or estimate cannot be copied across mismatched hardware, runtime, driver, workflow or protocol versions without an owner-approved applicability rule.

### Quality labels remain under M01

M01 owns the Fidelity Contract, evaluator set, evidence requirements and promotion rules. Its planning makes human review mandatory for certain high-value outputs, evaluator disagreement, out-of-distribution cases and uncertain protected defects. **Design implication:** M10 may predict risk of an M01 contract failure and signal uncertainty; it cannot score itself into a quality decision, weaken a contract or promote output.

## S03 candidate protocol

The evidence motivates the following planning requirements:

1. Keep allocation-failure, thermal-limit and M01 quality-contract targets separate, each with an owner-defined label and version.
2. Pin workload, hardware/partition, runtime/driver, provider/workflow, model, benchmark and resource context for the data used to fit and calibrate each estimate.
3. Separate training, calibration and evaluation by workload instance/run lineage and preserve temporal order for sequential telemetry. Retain independent workload and hardware/runtime cohorts for leakage and generalization checks.
4. Report calibration/reliability and proper scoring appropriate to each target, false-safe/missed-event behavior, interval or risk coverage where applicable, abstention coverage, subgroup/worst-group results and uncertainty. Do not treat aggregate marginal calibration as conditional safety.
5. Trigger explicit abstention for missing, unsupported, stale, conflicting, censored, out-of-distribution or materially drifting evidence, or when the method's assumptions cannot be defended.
6. Treat synthetic fixtures as checks of mechanics only. Physical calibration claims require valid, provenance-bound observations on the stated hardware/runtime slice.
7. Leave estimator selection, label acceptance policy, numeric horizons, risk budgets, minimum support, freshness limits and acceptance thresholds open for later evidence and policy review. S05 owns update/rollback lifecycle.

## Sources

- Angelopoulos, Bates, Jordan and Malik (2021), [Distribution-Free, Risk-Controlling Prediction Sets](https://arxiv.org/abs/2101.02703).
- Bates, Angelopoulos, Lei, Malik and Jordan (2023), [Non-Exchangeable Conformal Risk Control](https://arxiv.org/abs/2310.01262).
- Xu and Xie (2021), [Conformal Prediction Interval for Dynamic Time-Series](https://proceedings.mlr.press/v139/xu21h.html).
- NVIDIA, [NVML API: Clock Event Reasons](https://docs.nvidia.com/deploy/nvml-api/api/group__nvmlClocksEventReasons.html).
- AMD, [AMD SMI: GPU Violations](https://rocm.docs.amd.com/projects/amdsmi/en/develop/conceptual/gpu-violations.html).
- IRIS owner contracts: [M01](../modules/M01-EXTREME-QUALITY.md), [M07](../modules/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md), [M08](../modules/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md), [M09](../modules/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md), [M10 S01](M10-S01-WORKLOAD-SIGNATURE-ENGINE.md), [M10 S02](M10-S02-HARDWARE-AWARE-PLAN-COMPILATION.md).

## Limits

This note is design research, not a physical benchmark, calibrated model card, safety certification or admission to implementation. Statistical method guarantees are conditional on their stated setup; hardware telemetry fields and availability vary by model, driver and API version. S03 selects no operational risk target, policy threshold or model.
