# M13 S05 | Performance Budgets, Profiling and Anti-Regression Gates

**IRIS-WO-0049 | Issue #155 | Source-only fifth session, NOT an M13 contract freeze or implementation admission.**

Performance is evidence-gated, not inferred from upstream hardware marketing or scripts. M01 fidelity and M02 accepted production state remain hard gates; M07 owns observed hardware and M08 independent benchmark evidence; M09 actual resource owner; M10 advisory only; M11/M12 unfrozen; M53/M54/M55/M60 future rights, physical storage and OS contracts missing. No numeric latency, throughput, memory, power or cost budget is selected in this session.

## I. Original exact repository-source hierarchy

Exact protected source main `e4c8821fdc504fe398ec72b287dc13ed0e24f442`, tree `958140fc1207f480cc0da67037184eceb6865a8c`. Four previous S01–S04 sessions are original SOURCE_ONLY research and their unanswered questions/unexecuted negative designs remain intact.

- **INDEX**: [`planning/MASTER-MODULE-INDEX.md`](../../planning/MASTER-MODULE-INDEX.md); exact original Git blob `a60d19c86bddd3699498f7d1f248a00368e32220`; required literal `S05 — S05 Performance budgets, profiling and anti-regression gates`.
- **M01**: [`docs/M01-QUALITY-KERNEL.md`](../../docs/M01-QUALITY-KERNEL.md); exact original Git blob `df4f899ad414c47ad379f26fe1782edb6f43cf6f`; required literal `m01-contract-v1.0`.
- **M02**: [`planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md`](../../planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md); exact original Git blob `a36fd73c03f06b7558f850a2ad515a0df37c243b`; required literal `semantic reuse requires explicit reuse class/admission`.
- **M06**: [`planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md`](../../planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md); exact original Git blob `d6778684e0c34e55d05ddc06cf5aa47fe347c037`; required literal `Digest equality proves byte equality under the declared digest domain only.`.
- **M07**: [`docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md`](../../docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md); exact original Git blob `2a0b95dd3cc665e2206e454caef5858ef7fb61b0`; required literal `M07 does not lower quality targets`.
- **M08**: [`docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md`](../../docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md); exact original Git blob `461e0f332d9be2af694634bbdc8cf67e29d56393`; required literal `UNKNOWN_TELEMETRY`.
- **M09**: [`docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md`](../../docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md); exact original Git blob `d12b4f48030c1a57b8e6228df39f35dac8c2b20a`; required literal `m09-contract-v1.0`.
- **M10**: [`planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md`](../../planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md); exact original Git blob `f69ec3e3eab24b47c0e31832d64d9ab9cce21828`; required literal `Implementation authority: NOT ADMITTED`.
- **M11**: [`planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md`](../../planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md); exact original Git blob `4a5f384271504365701bdd685455d93984617f21`; required literal `PROPOSED_C02_CORRECTION_NOT_FROZEN`.
- **M12**: [`planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md`](../../planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md); exact original Git blob `28b3802901349263100ceaaf80c0990513dbbded`; required literal `Implementation authority: NOT_ADMITTED`.
- **S01**: [`.engineering/evidence/M13-S01-SOURCE-RESEARCH.json`](../../.engineering/evidence/M13-S01-SOURCE-RESEARCH.json); exact original Git blob `5fe1b1ec36ce1e49a0810f553825c9d71b2af3e0`; required literal `SOURCE_RESEARCH_ONLY_NONBINDING`.
- **S02**: [`.engineering/evidence/M13-S02-BACKEND-ATTENTION-RESEARCH.json`](../../.engineering/evidence/M13-S02-BACKEND-ATTENTION-RESEARCH.json); exact original Git blob `8ac11eaa91292a81d10de1d44ccd21b5e240a664`; required literal `SOURCE_ONLY_UNSELECTED_NONBINDING`.
- **S03**: [`.engineering/evidence/M13-S03-DELTA-REUSE-RESEARCH.json`](../../.engineering/evidence/M13-S03-DELTA-REUSE-RESEARCH.json); exact original Git blob `fe0ea0d3a4b4229f79e19d023c255cc6a0cafdf1`; required literal `SOURCE_ONLY_NONBINDING`.
- **S04**: [`.engineering/evidence/M13-S04-OVERLAP-IO-RESEARCH.json`](../../.engineering/evidence/M13-S04-OVERLAP-IO-RESEARCH.json); exact original Git blob `b9b87ac36189c1cabd75989a07920752c23704fd`; required literal `SOURCE_ONLY_NO_HARDWARE_OR_IO_RUNTIME`.
- **D01**: [`.engineering/evidence/M09-B-OWNER-DIRECTION-D01.json`](../../.engineering/evidence/M09-B-OWNER-DIRECTION-D01.json); exact original Git blob `8877331a5004a3e816e4c42fb521ff3408bad08a`; required literal `B_FUTURE_OWNER_RECEIPT`.

## II. Three publicly documented profiling references, MUTABLE only

- **TORCH_PROFILER** [Official PyTorch maintainers reference](https://docs.pytorch.org/docs/stable/profiler): PyTorch profiler exposes scoped CPU/CUDA activities and scheduled record windows; availability and overhead depend on the installed software and device. **MUTABLE_EXTERNAL_SOURCE_NOT_LOCAL_PROFILING_OR_PRODUCTION_PROOF**. Current as-of date 2026-09-27.
- **NVIDIA_NSIGHT** [Official NVIDIA reference](https://docs.nvidia.com/nsight-systems/UserGuide/): Nsight Systems documents CUDA timeline correlations and trace-buffer/instrumentation overhead and compatibility constraints; trace timestamps require source-qualified interpretation. **MUTABLE_EXTERNAL_SOURCE_NOT_LOCAL_PROFILING_OR_PRODUCTION_PROOF**. Current as-of date 2026-09-27.
- **CUDA_TIMING** [Official NVIDIA reference](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/): CUDA guidance distinguishes asynchronous host enqueue time from synchronized CUDA execution/event elapsed time and advocates representative profiled workloads. **MUTABLE_EXTERNAL_SOURCE_NOT_LOCAL_PROFILING_OR_PRODUCTION_PROOF**. Current as-of date 2026-09-27.

## III. Six nonnumerical candidate budget families, all UNRATED

### BUDGET-01 HARD_CREATIVE_QUALITY

Hard future scope: M01 creative fidelity, exact source rights and accepted production truth are non-negotiable constraints, not tradeable performance weights.
Required actual independent evidence: Owner-qualified current M01 evaluator and accepted M02 graph; no earlier benchmark can replace genuine master/promote authority.
Owner route M01/M02; threshold `OWNER_DEFINED_NOT_ASSIGNED`; **UNRATED_NO_NUMERIC_THRESHOLD**.

### BUDGET-02 MEASUREMENT_ADMISSIBILITY

Hard future scope: Only exact protocol-, fixture-, workload- and hardware-bound correctness/freshness/uncertainty-qualified measurements can establish a performance envelope.
Required actual independent evidence: M08 owner valid result, actual M07 fingerprint, interference policy and sample contamination/abort classification, not copied profile charts.
Owner route M07/M08; threshold `OWNER_DEFINED_NOT_ASSIGNED`; **UNRATED_NO_NUMERIC_THRESHOLD**.

### BUDGET-03 USER_FOREGROUND_TAIL

Hard future scope: Distinct interactive workstation p95/p99 and bounded foreground preemption requirements protect responsiveness during optional background processing.
Required actual independent evidence: Real M08 host-wide interference proof plus independent M11/M12 worker/placement and M54/M60 current OS principal authority.
Owner route M08/M11/M12; threshold `OWNER_DEFINED_NOT_ASSIGNED`; **UNRATED_NO_NUMERIC_THRESHOLD**.

### BUDGET-04 DEVICE_RESOURCE_PRESSURE

Hard future scope: Host RAM, pinned pages, observed VRAM and power/thermal risk must not be substituted for genuine M09 owner-issued all-member resource grants.
Required actual independent evidence: Versioned M07 telemetry, actual M08 qualification and complete-member M09 lease/at-use revocation with H01–H04 real proof.
Owner route M07/M08/M09; threshold `OWNER_DEFINED_NOT_ASSIGNED`; **UNRATED_NO_NUMERIC_THRESHOLD**.

### BUDGET-05 COLD_WARM_COMPILE

Hard future scope: Compare cold startup, compilation, cache invalidation and warmed model inference by exact workload and model/backend identity.
Required actual independent evidence: Actual qualified installed model/toolchain, source-bound compilation and M08 comparable cold/warm samples; avoid fictional amortization.
Owner route M08/M13/M14/M16; threshold `OWNER_DEFINED_NOT_ASSIGNED`; **UNRATED_NO_NUMERIC_THRESHOLD**.

### BUDGET-06 PHYSICAL_IO_AND_REBUILD

Hard future scope: Report physical read/write, cache miss/restore, rebuild latency and verified multimodal output, without deriving bytes/rights from a hash hit.
Required actual independent evidence: Independent M55 storage lifecycle, M02/M06 accepted causal rebuild evidence and M08 comparable read/decode/write protocol.
Owner route M02/M06/M08/M55; threshold `OWNER_DEFINED_NOT_ASSIGNED`; **UNRATED_NO_NUMERIC_THRESHOLD**.

## IV. Five distinct profiling and regression research protocols, none run

### PROFILE-01 M08_VALID_BASELINE

Future method: Admitted exact M08 fixtures and valid M07 context with registered source workload/clock/correctness.
Failure and instrumentation caveat: A source-only synthetic profile cannot be an actual M08 result; no sample magnitude or slowdown ratio is asserted.
**PROTOCOL_NOT_EXECUTED**.

### PROFILE-02 PAIRED_END_TO_END

Future method: Paired prior/new source-exact representative media operations with comparable CPU/GPU/storage/interference and actual completion timing.
Failure and instrumentation caveat: Unmatched source, changed hardware, different model/quality or missing ambient interference invalidates comparative claims.
**PROTOCOL_NOT_EXECUTED**.

### PROFILE-03 CAUSAL_TRACE_CORRELATION

Future method: Future CPU timeline versus CUDA event/stream trace and physical I/O windows with actual sync and profiler-instrumentation overhead.
Failure and instrumentation caveat: Host enqueue completion, device event time, or tracer timestamps alone cannot prove end-to-end wall time or safe concurrent work.
**PROTOCOL_NOT_EXECUTED**.

### PROFILE-04 COLD_WARM_SEPARATION

Future method: Independent warmed/cold model, compiled graph, cache invalidation/restore and legitimate rights checks under exact input revisions.
Failure and instrumentation caveat: A favorable warm-only metric does not establish cold startup, sustained output quality or safe tenant/cache invalidation.
**PROTOCOL_NOT_EXECUTED**.

### PROFILE-05 QUALITY_REPRO_TEST

Future method: Bound M01 reference quality and M02/M06 revision/attempt lineage to actual output before discussing throughput optimization.
Failure and instrumentation caveat: Passing throughput cannot waive a quality regression, stochastic mismatch or a previously accepted master gate.
**PROTOCOL_NOT_EXECUTED**.

## V. Twelve future source-owner/empirical evidence axes

- **QUALITY_MASTER** [M01/M02]: Independently qualified current creative-quality contract, explicit accepted graph revision and no runtime degradation. **OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED**.
- **WORK_ATTEMPT_LINEAGE** [M02/M06]: Exact accepted work/revision, original attempt/materialization IDs, fresh source digest-domain and immutable measurement lineage. **OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED**.
- **HARDWARE_FINGERPRINT** [M07/M60]: Actual hardware subject, OS/device/driver, current telemetry capability, sensor uncertainty and invalidation events. **OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED**.
- **BENCHMARK_PROTOCOL** [M08]: Owner-issued comparable fixture, clock, run count/warmup, independent correctness, confidence and abort policy. **OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED**.
- **INTERFERENCE_COMPLETENESS** [M08/M56]: Real host-wide activity evidence or explicit UNKNOWN_TELEMETRY/PARTIAL preserved without VALID promotion. **OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED**.
- **TRACE_OBSERVER_EFFECT** [M08/M56/M60]: Profiler installed-version and permission scope, capture overhead/clock correlation and sensor sampling disturbance. **OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED**.
- **RESOURCE_TRUTH** [M09/M11/M12]: Actual complete-member coherent grant/lease, at-use revoke, authenticated worker proof and exact attempt/action fence. **OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED**.
- **MODEL_AND_COMPILER** [M14/M16/M17/M18]: Real separately reviewed model weights, provider compiler/runtime, package provenance and exact fallback/version profile. **OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED**.
- **STORAGE_LIFECYCLE** [M55]: Qualified physical read/write/CAS availability, retention, data locality, encryption and deletion authority. **OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED**.
- **CURRENT_TENANT_RIGHTS** [M53/M54]: Real current authenticated principal, model/media rights, consent, redaction and at-use revocation for all traces. **OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED**.
- **HUMAN_POLICY_APPROVAL** [M01/M02/M10/M57]: Owner-issued production-specific budget policy and hard quality minima; M10 advice cannot freeze numeric gate. **OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED**.
- **OBSERVABILITY_REVIEW** [M56/M58/M60]: Verified telemetry source, privacy-redacted report scope, independent trace reviewer and no public API from profiling. **OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED**.

## VI. Twenty NEW S05 source-routed OPEN/UNRATED owner questions

These new S05 questions do not change the original S01 18, S02 18, S03 20, S04 20 or M12 original 110 OPEN. Names indicate future source owners, not real signatures.

### M13-S05-U01 | M01/M02

Which independently issued fidelity/accepted-graph policy is a hard veto that no future S05 throughput budget may weaken?

Exact original source role `M01`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U02 | M07/M08

Which exact current M07 device/driver/sensor scope and M08 protocol must be version-bound before any p95 slowdown comparison?

Exact original source role `M08`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U03 | M08

How must M08 distinguish genuine VALID results from PARTIAL, UNKNOWN_TELEMETRY, contaminated, aborted or unsupported samples?

Exact original source role `M08`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U04 | M08/M56

Which measured external interference and workstation foreground latency must accompany every background throughput claim?

Exact original source role `M08`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U05 | M07/M08/M60

What exact installed profiler version, trace permissions and observer-overhead calibration qualify a CUDA or CPU profiling capture?

Exact original source role `M07`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U06 | M08/M13

What actual paired cold/warm/startup/cache-invalidation comparison is needed before claiming that S01 locality reduced latency?

Exact original source role `S01`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U07 | M08/M13/M14/M16

How can actual compile/recompile overhead and model/provider version changes invalidate apparently favorable S02 performance reports?

Exact original source role `S02`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U08 | M02/M06/M08

Which accepted work/attempt/source lineage and unchanged input/protocol class must pair S03 partial-rebuild and full-build comparisons?

Exact original source role `S03`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U09 | M07/M08/M09

What independently observed real VRAM/host RAM/pinned-page/thermal evidence can inform a future resource budget without minting a grant?

Exact original source role `M09`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U10 | M09/M11/M12

Which original H01–H04 verified M11 ACK, M09 all-member joint lease and M12 attempt/action fences are prerequisites to any live benchmark?

Exact original source role `M09`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U11 | M53/M54/M55

Which actual current rights and physical storage-owner proofs authorize optional traces, I/O samples and retention of profile artifacts?

Exact original source role `INDEX`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U12 | M08/M56

What owner-defined uncertainty bounds and reproducible paired result protocol distinguish regression from normal variance across sessions?

Exact original source role `M08`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U13 | M08/M57

Who will define and separately sign numeric production latency, memory or power budgets after actual admitted measurements?

Exact original source role `INDEX`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U14 | M08/M10

How can measured capability evidence stay independent of frozen M10 advisor predictions and its unimplemented risk flags?

Exact original source role `M10`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U15 | M01/M08/M13

Which S01–S04 hypotheses can be rejected on quality or foreground tail even if aggregate throughput appears higher?

Exact original source role `M01`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U16 | M08/M56/M60

How can CPU host, GPU stream/device-event and I/O timeline clocks be reconciled without mistaking enqueue for execution?

Exact original source role `M08`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U17 | M55/M60

Which separately qualified physical I/O and OS tracing contracts would permit profiling on Windows or Linux without assuming parity?

Exact original source role `INDEX`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U18 | M02/M06/M53/M54

Which source-bound tenant and redaction scopes prevent trace exports or profiles from leaking raw media/prompt or credential data?

Exact original source role `M02`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U19 | M08/M56

Which unchanged benchmark protocol, baseline/target commit, sample-distribution and uncertainty receipts qualify eventual regression triage?

Exact original source role `M08`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

### M13-S05-U20 | M13/M14/M16/M17/M60

Which qualified model/toolchain/backend/hardware version matrix would make a final M13 performance budget technology-neutral and revisit-safe?

Exact original source role `INDEX`; OPEN_UNRATED_PENDING_QUALIFIED_OWNER; risk UNRATED; qualified owner answer NOT RECEIVED.

## VII. Sixteen NEW future negative-case designs, all SPECIFIED_NOT_EXECUTED

### M13-S05-N01 QUALITY_BEFORE_SPEED

Hypothetical trigger: A candidate appears faster but its quality evidence is missing or violates original M01 fidelity.
Expected future nonauthorizing check: `NO_PERFORMANCE_PASS_WITH_QUALITY_FAILURE`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N02 UNKNOWN_IS_NOT_VALID

Hypothetical trigger: A partial M08 result without host-wide interference sensors is relabeled valid and promoted.
Expected future nonauthorizing check: `NO_UNKNOWN_TELEMETRY_TO_VALID`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N03 PROFILER_PERTURBATION

Hypothetical trigger: A tracing configuration adds synchronization or memory overhead but its raw results are compared with uninstrumented baseline.
Expected future nonauthorizing check: `NO_UNCALIBRATED_PROFILER_SPEEDUP`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N04 CUDA_ENQUEUE_ONLY

Hypothetical trigger: A CPU wall-clock stop before CUDA completion is treated as device-complete end-to-end latency.
Expected future nonauthorizing check: `NO_ENQUEUE_AS_GPU_COMPLETION`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N05 STALE_DEVICE

Hypothetical trigger: A benchmark is reused after driver or compute-device firmware replacement while its hardware version key stays unchanged.
Expected future nonauthorizing check: `NO_STALE_HARDWARE_PERFORMANCE_CERT`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N06 UNMATCHED_WORKLOAD

Hypothetical trigger: Baseline and candidate use different model seeds, graph revisions, quality policy or media dimensions.
Expected future nonauthorizing check: `NO_UNPAIRED_REGRESSION_RESULT`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N07 INSUFFICIENT_UNCERTAINTY

Hypothetical trigger: A tiny average improvement is claimed as reliable despite unqualified sample count and wide overlapping variability.
Expected future nonauthorizing check: `NO_INFERENCE_WITH_UNKNOWN_CONFIDENCE`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N08 COLD_WARM_CONFUSION

Hypothetical trigger: Warm cached runs are presented as representative cold first-use performance without startup/compile accounting.
Expected future nonauthorizing check: `NO_COLD_LATENCY_FROM_WARM_ONLY`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N09 TENANT_PROFILE_LEAK

Hypothetical trigger: Profiler traces include another tenant's prompt or credential content under an overly broad system capture.
Expected future nonauthorizing check: `NO_UNAUTHORIZED_PROFILE_EXPORT`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N10 NUMERIC_POLICY_INVENTION

Hypothetical trigger: A proposed threshold is marked adopted even though no independent policy owner assigned or qualified it.
Expected future nonauthorizing check: `NO_DEFAULT_SLO_FROM_DRAFT`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N11 RESOURCE_HINT_AS_LEASE

Hypothetical trigger: Performance pressure readings are used to authorize new GPU work without coherent M09 lease/owner ACK.
Expected future nonauthorizing check: `NO_RESOURCE_GRANT_FROM_METRIC`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N12 THERMAL_CAUSAL_ERROR

Hypothetical trigger: CPU/GPU thermal throttling or power cap is mislabeled as disk I/O bottleneck without independent sensor evidence.
Expected future nonauthorizing check: `NO_UNGROUNDED_CAUSAL_PROFILE`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N13 MISSING_OWNER_TRACE

Hypothetical trigger: A simulated all-green checklist is used in place of real M08/source security owner signatures and runtime authorization.
Expected future nonauthorizing check: `NO_MOCK_CHECKLIST_AS_OWNER_PROOF`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N14 STORAGE_STALE_RIGHTS

Hypothetical trigger: A cached profiler trace is retained or re-read after M55 physical deletion or M53 rights revocation.
Expected future nonauthorizing check: `NO_PROFILE_RETENTION_FROM_HISTORY`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N15 PARTIAL_REBUILD_LINEAGE

Hypothetical trigger: A faster S03 partial rebuild silently changes M02/M06 accepted work or M01 master quality.
Expected future nonauthorizing check: `NO_PERF_RESULT_AS_PRODUCTION_ADMISSION`; **SPECIFIED_NOT_EXECUTED**.

### M13-S05-N16 HYPOTHESIS_MARKED_MEASURED

Hypothetical trigger: A documentation-only S01–S04 metric is described as observed local GPU speedup by copying a vendor example.
Expected future nonauthorizing check: `NO_PUBLIC_DOC_AS_LOCAL_BENCHMARK`; **SPECIFIED_NOT_EXECUTED**.

## VIII. Performance-budget screening is non-authorizing

A standalone synthetic evidence classifier may identify missing mock fields but can NEVER grant production speed budgets, model quality, profiler installation or resource admission. The real sequence requires source identity; current M01 quality; exact current rights; source-valid real M07/M08 independent empirical protocol and observer perturbation evidence; qualified production policy thresholds issued by their genuine owners; actual M09 lease/M11/M12 attempt fence and M60 OS rights if any hardware run is proposed; source-qualified independent security and storage access. Every UNKNOWN or PARTIAL remains explicit. No default numeric SLOs are defined.

## IX. Handoff after five sessions

After S05 source-only CI/merge, independently source-lock a separate M13 Final Technology Review and M14–M60 full Forward Compatibility Scan. Preserve each original open question and future nonexecuted test as a debt item. No new M13 FTR, contract freeze, implementation or runtime is preapproved by completing five planning sessions.

**STOP:** S05 completes five documentary research sessions only, not M13 final technology review, independent cross-module compatibility, selected budget/profiler, installed profiling, real hardware measurement, authenticated quality/rights/OS/source owner signature, positive H01-H04 closure, M09 C01 adoption, GPU/CPU/OS/network/cloud/storage execution, actual negative integration cases or M10/M11/M12/M13 runtime. H01-H04 OPEN HIGH_FOR_FUTURE_FREEZE; B DIRECTION_ONLY; C01 UNADOPTED_NOT_FROZEN; all future original cases SPECIFIED_NOT_EXECUTED.

## Appendix A: canonical original machine packet

```json
{
  "schema": "iris-m13-s05-performance-budgets-v0.1",
  "workOrder": "IRIS-WO-0049",
  "issue": 155,
  "module": "M13",
  "session": "S05",
  "baseSha": "e4c8821fdc504fe398ec72b287dc13ed0e24f442",
  "baseTreeSha": "958140fc1207f480cc0da67037184eceb6865a8c",
  "asOf": "2026-09-27",
  "status": "SOURCE_ONLY_FIFTH_SESSION_NOT_MODULE_FREEZE",
  "actualOwnerApprovals": 0,
  "selectedPolicy": "NONE",
  "numericBudgets": "NONE_ASSIGNED",
  "measurements": "NONE_PERFORMED",
  "installedProfilers": "NONE",
  "runtime": "NOT_ADMITTED",
  "b": "DIRECTION_ONLY",
  "c01": "UNADOPTED_NOT_FROZEN",
  "highs": "H01_H02_H03_H04_OPEN_HIGH_FOR_FUTURE_FREEZE",
  "previousSessions": {
    "s01Questions": "18_OPEN",
    "s01FutureNegatives": "12_NOT_EXECUTED",
    "s02Questions": "18_OPEN",
    "s02FutureNegatives": "14_NOT_EXECUTED",
    "s03Questions": "20_OPEN",
    "s03FutureNegatives": "16_NOT_EXECUTED",
    "s04Questions": "20_OPEN",
    "s04FutureNegatives": "16_NOT_EXECUTED"
  },
  "originalM12Questions": "110_OPEN_UNRATED",
  "originalM12FutureNegatives": "80_SPECIFIED_NOT_EXECUTED",
  "sourceDocs": [
    {
      "role": "INDEX",
      "path": "planning/MASTER-MODULE-INDEX.md",
      "sha": "a60d19c86bddd3699498f7d1f248a00368e32220",
      "anchor": "S05 — S05 Performance budgets, profiling and anti-regression gates"
    },
    {
      "role": "M01",
      "path": "docs/M01-QUALITY-KERNEL.md",
      "sha": "df4f899ad414c47ad379f26fe1782edb6f43cf6f",
      "anchor": "m01-contract-v1.0"
    },
    {
      "role": "M02",
      "path": "planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
      "sha": "a36fd73c03f06b7558f850a2ad515a0df37c243b",
      "anchor": "semantic reuse requires explicit reuse class/admission"
    },
    {
      "role": "M06",
      "path": "planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
      "sha": "d6778684e0c34e55d05ddc06cf5aa47fe347c037",
      "anchor": "Digest equality proves byte equality under the declared digest domain only."
    },
    {
      "role": "M07",
      "path": "docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md",
      "sha": "2a0b95dd3cc665e2206e454caef5858ef7fb61b0",
      "anchor": "M07 does not lower quality targets"
    },
    {
      "role": "M08",
      "path": "docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md",
      "sha": "461e0f332d9be2af694634bbdc8cf67e29d56393",
      "anchor": "UNKNOWN_TELEMETRY"
    },
    {
      "role": "M09",
      "path": "docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md",
      "sha": "d12b4f48030c1a57b8e6228df39f35dac8c2b20a",
      "anchor": "m09-contract-v1.0"
    },
    {
      "role": "M10",
      "path": "planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
      "sha": "f69ec3e3eab24b47c0e31832d64d9ab9cce21828",
      "anchor": "Implementation authority: NOT ADMITTED"
    },
    {
      "role": "M11",
      "path": "planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
      "sha": "4a5f384271504365701bdd685455d93984617f21",
      "anchor": "PROPOSED_C02_CORRECTION_NOT_FROZEN"
    },
    {
      "role": "M12",
      "path": "planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
      "sha": "28b3802901349263100ceaaf80c0990513dbbded",
      "anchor": "Implementation authority: NOT_ADMITTED"
    },
    {
      "role": "S01",
      "path": ".engineering/evidence/M13-S01-SOURCE-RESEARCH.json",
      "sha": "5fe1b1ec36ce1e49a0810f553825c9d71b2af3e0",
      "anchor": "SOURCE_RESEARCH_ONLY_NONBINDING"
    },
    {
      "role": "S02",
      "path": ".engineering/evidence/M13-S02-BACKEND-ATTENTION-RESEARCH.json",
      "sha": "8ac11eaa91292a81d10de1d44ccd21b5e240a664",
      "anchor": "SOURCE_ONLY_UNSELECTED_NONBINDING"
    },
    {
      "role": "S03",
      "path": ".engineering/evidence/M13-S03-DELTA-REUSE-RESEARCH.json",
      "sha": "fe0ea0d3a4b4229f79e19d023c255cc6a0cafdf1",
      "anchor": "SOURCE_ONLY_NONBINDING"
    },
    {
      "role": "S04",
      "path": ".engineering/evidence/M13-S04-OVERLAP-IO-RESEARCH.json",
      "sha": "b9b87ac36189c1cabd75989a07920752c23704fd",
      "anchor": "SOURCE_ONLY_NO_HARDWARE_OR_IO_RUNTIME"
    },
    {
      "role": "D01",
      "path": ".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json",
      "sha": "8877331a5004a3e816e4c42fb521ff3408bad08a",
      "anchor": "B_FUTURE_OWNER_RECEIPT"
    }
  ],
  "externalReferences": [
    {
      "id": "TORCH_PROFILER",
      "url": "https://docs.pytorch.org/docs/stable/profiler",
      "publisher": "PyTorch maintainers",
      "claim": "PyTorch profiler exposes scoped CPU/CUDA activities and scheduled record windows; availability and overhead depend on the installed software and device.",
      "checkedOn": "2026-09-27",
      "status": "MUTABLE_EXTERNAL_SOURCE_NOT_LOCAL_PROFILING_OR_PRODUCTION_PROOF"
    },
    {
      "id": "NVIDIA_NSIGHT",
      "url": "https://docs.nvidia.com/nsight-systems/UserGuide/",
      "publisher": "NVIDIA",
      "claim": "Nsight Systems documents CUDA timeline correlations and trace-buffer/instrumentation overhead and compatibility constraints; trace timestamps require source-qualified interpretation.",
      "checkedOn": "2026-09-27",
      "status": "MUTABLE_EXTERNAL_SOURCE_NOT_LOCAL_PROFILING_OR_PRODUCTION_PROOF"
    },
    {
      "id": "CUDA_TIMING",
      "url": "https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/",
      "publisher": "NVIDIA",
      "claim": "CUDA guidance distinguishes asynchronous host enqueue time from synchronized CUDA execution/event elapsed time and advocates representative profiled workloads.",
      "checkedOn": "2026-09-27",
      "status": "MUTABLE_EXTERNAL_SOURCE_NOT_LOCAL_PROFILING_OR_PRODUCTION_PROOF"
    }
  ],
  "budgetClasses": [
    {
      "id": "BUDGET-01",
      "name": "HARD_CREATIVE_QUALITY",
      "ownerRoute": "M01/M02",
      "scope": "M01 creative fidelity, exact source rights and accepted production truth are non-negotiable constraints, not tradeable performance weights.",
      "necessaryFutureEvidence": "Owner-qualified current M01 evaluator and accepted M02 graph; no earlier benchmark can replace genuine master/promote authority.",
      "threshold": "OWNER_DEFINED_NOT_ASSIGNED",
      "status": "UNRATED_NO_NUMERIC_THRESHOLD"
    },
    {
      "id": "BUDGET-02",
      "name": "MEASUREMENT_ADMISSIBILITY",
      "ownerRoute": "M07/M08",
      "scope": "Only exact protocol-, fixture-, workload- and hardware-bound correctness/freshness/uncertainty-qualified measurements can establish a performance envelope.",
      "necessaryFutureEvidence": "M08 owner valid result, actual M07 fingerprint, interference policy and sample contamination/abort classification, not copied profile charts.",
      "threshold": "OWNER_DEFINED_NOT_ASSIGNED",
      "status": "UNRATED_NO_NUMERIC_THRESHOLD"
    },
    {
      "id": "BUDGET-03",
      "name": "USER_FOREGROUND_TAIL",
      "ownerRoute": "M08/M11/M12",
      "scope": "Distinct interactive workstation p95/p99 and bounded foreground preemption requirements protect responsiveness during optional background processing.",
      "necessaryFutureEvidence": "Real M08 host-wide interference proof plus independent M11/M12 worker/placement and M54/M60 current OS principal authority.",
      "threshold": "OWNER_DEFINED_NOT_ASSIGNED",
      "status": "UNRATED_NO_NUMERIC_THRESHOLD"
    },
    {
      "id": "BUDGET-04",
      "name": "DEVICE_RESOURCE_PRESSURE",
      "ownerRoute": "M07/M08/M09",
      "scope": "Host RAM, pinned pages, observed VRAM and power/thermal risk must not be substituted for genuine M09 owner-issued all-member resource grants.",
      "necessaryFutureEvidence": "Versioned M07 telemetry, actual M08 qualification and complete-member M09 lease/at-use revocation with H01–H04 real proof.",
      "threshold": "OWNER_DEFINED_NOT_ASSIGNED",
      "status": "UNRATED_NO_NUMERIC_THRESHOLD"
    },
    {
      "id": "BUDGET-05",
      "name": "COLD_WARM_COMPILE",
      "ownerRoute": "M08/M13/M14/M16",
      "scope": "Compare cold startup, compilation, cache invalidation and warmed model inference by exact workload and model/backend identity.",
      "necessaryFutureEvidence": "Actual qualified installed model/toolchain, source-bound compilation and M08 comparable cold/warm samples; avoid fictional amortization.",
      "threshold": "OWNER_DEFINED_NOT_ASSIGNED",
      "status": "UNRATED_NO_NUMERIC_THRESHOLD"
    },
    {
      "id": "BUDGET-06",
      "name": "PHYSICAL_IO_AND_REBUILD",
      "ownerRoute": "M02/M06/M08/M55",
      "scope": "Report physical read/write, cache miss/restore, rebuild latency and verified multimodal output, without deriving bytes/rights from a hash hit.",
      "necessaryFutureEvidence": "Independent M55 storage lifecycle, M02/M06 accepted causal rebuild evidence and M08 comparable read/decode/write protocol.",
      "threshold": "OWNER_DEFINED_NOT_ASSIGNED",
      "status": "UNRATED_NO_NUMERIC_THRESHOLD"
    }
  ],
  "profilingMethods": [
    {
      "id": "PROFILE-01",
      "name": "M08_VALID_BASELINE",
      "conditionalMethod": "Admitted exact M08 fixtures and valid M07 context with registered source workload/clock/correctness.",
      "failureLimit": "A source-only synthetic profile cannot be an actual M08 result; no sample magnitude or slowdown ratio is asserted.",
      "status": "PROTOCOL_NOT_EXECUTED"
    },
    {
      "id": "PROFILE-02",
      "name": "PAIRED_END_TO_END",
      "conditionalMethod": "Paired prior/new source-exact representative media operations with comparable CPU/GPU/storage/interference and actual completion timing.",
      "failureLimit": "Unmatched source, changed hardware, different model/quality or missing ambient interference invalidates comparative claims.",
      "status": "PROTOCOL_NOT_EXECUTED"
    },
    {
      "id": "PROFILE-03",
      "name": "CAUSAL_TRACE_CORRELATION",
      "conditionalMethod": "Future CPU timeline versus CUDA event/stream trace and physical I/O windows with actual sync and profiler-instrumentation overhead.",
      "failureLimit": "Host enqueue completion, device event time, or tracer timestamps alone cannot prove end-to-end wall time or safe concurrent work.",
      "status": "PROTOCOL_NOT_EXECUTED"
    },
    {
      "id": "PROFILE-04",
      "name": "COLD_WARM_SEPARATION",
      "conditionalMethod": "Independent warmed/cold model, compiled graph, cache invalidation/restore and legitimate rights checks under exact input revisions.",
      "failureLimit": "A favorable warm-only metric does not establish cold startup, sustained output quality or safe tenant/cache invalidation.",
      "status": "PROTOCOL_NOT_EXECUTED"
    },
    {
      "id": "PROFILE-05",
      "name": "QUALITY_REPRO_TEST",
      "conditionalMethod": "Bound M01 reference quality and M02/M06 revision/attempt lineage to actual output before discussing throughput optimization.",
      "failureLimit": "Passing throughput cannot waive a quality regression, stochastic mismatch or a previously accepted master gate.",
      "status": "PROTOCOL_NOT_EXECUTED"
    }
  ],
  "futureQualificationAxes": [
    {
      "id": "QUALITY_MASTER",
      "ownerRoute": "M01/M02",
      "requiredActualEvidence": "Independently qualified current creative-quality contract, explicit accepted graph revision and no runtime degradation.",
      "status": "OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED"
    },
    {
      "id": "WORK_ATTEMPT_LINEAGE",
      "ownerRoute": "M02/M06",
      "requiredActualEvidence": "Exact accepted work/revision, original attempt/materialization IDs, fresh source digest-domain and immutable measurement lineage.",
      "status": "OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED"
    },
    {
      "id": "HARDWARE_FINGERPRINT",
      "ownerRoute": "M07/M60",
      "requiredActualEvidence": "Actual hardware subject, OS/device/driver, current telemetry capability, sensor uncertainty and invalidation events.",
      "status": "OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED"
    },
    {
      "id": "BENCHMARK_PROTOCOL",
      "ownerRoute": "M08",
      "requiredActualEvidence": "Owner-issued comparable fixture, clock, run count/warmup, independent correctness, confidence and abort policy.",
      "status": "OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED"
    },
    {
      "id": "INTERFERENCE_COMPLETENESS",
      "ownerRoute": "M08/M56",
      "requiredActualEvidence": "Real host-wide activity evidence or explicit UNKNOWN_TELEMETRY/PARTIAL preserved without VALID promotion.",
      "status": "OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED"
    },
    {
      "id": "TRACE_OBSERVER_EFFECT",
      "ownerRoute": "M08/M56/M60",
      "requiredActualEvidence": "Profiler installed-version and permission scope, capture overhead/clock correlation and sensor sampling disturbance.",
      "status": "OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED"
    },
    {
      "id": "RESOURCE_TRUTH",
      "ownerRoute": "M09/M11/M12",
      "requiredActualEvidence": "Actual complete-member coherent grant/lease, at-use revoke, authenticated worker proof and exact attempt/action fence.",
      "status": "OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED"
    },
    {
      "id": "MODEL_AND_COMPILER",
      "ownerRoute": "M14/M16/M17/M18",
      "requiredActualEvidence": "Real separately reviewed model weights, provider compiler/runtime, package provenance and exact fallback/version profile.",
      "status": "OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED"
    },
    {
      "id": "STORAGE_LIFECYCLE",
      "ownerRoute": "M55",
      "requiredActualEvidence": "Qualified physical read/write/CAS availability, retention, data locality, encryption and deletion authority.",
      "status": "OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED"
    },
    {
      "id": "CURRENT_TENANT_RIGHTS",
      "ownerRoute": "M53/M54",
      "requiredActualEvidence": "Real current authenticated principal, model/media rights, consent, redaction and at-use revocation for all traces.",
      "status": "OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED"
    },
    {
      "id": "HUMAN_POLICY_APPROVAL",
      "ownerRoute": "M01/M02/M10/M57",
      "requiredActualEvidence": "Owner-issued production-specific budget policy and hard quality minima; M10 advice cannot freeze numeric gate.",
      "status": "OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED"
    },
    {
      "id": "OBSERVABILITY_REVIEW",
      "ownerRoute": "M56/M58/M60",
      "requiredActualEvidence": "Verified telemetry source, privacy-redacted report scope, independent trace reviewer and no public API from profiling.",
      "status": "OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED"
    }
  ],
  "questions": [
    {
      "id": "M13-S05-U01",
      "ownerRoute": "M01/M02",
      "question": "Which independently issued fidelity/accepted-graph policy is a hard veto that no future S05 throughput budget may weaken?",
      "primarySourceRole": "M01",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U02",
      "ownerRoute": "M07/M08",
      "question": "Which exact current M07 device/driver/sensor scope and M08 protocol must be version-bound before any p95 slowdown comparison?",
      "primarySourceRole": "M08",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U03",
      "ownerRoute": "M08",
      "question": "How must M08 distinguish genuine VALID results from PARTIAL, UNKNOWN_TELEMETRY, contaminated, aborted or unsupported samples?",
      "primarySourceRole": "M08",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U04",
      "ownerRoute": "M08/M56",
      "question": "Which measured external interference and workstation foreground latency must accompany every background throughput claim?",
      "primarySourceRole": "M08",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U05",
      "ownerRoute": "M07/M08/M60",
      "question": "What exact installed profiler version, trace permissions and observer-overhead calibration qualify a CUDA or CPU profiling capture?",
      "primarySourceRole": "M07",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U06",
      "ownerRoute": "M08/M13",
      "question": "What actual paired cold/warm/startup/cache-invalidation comparison is needed before claiming that S01 locality reduced latency?",
      "primarySourceRole": "S01",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U07",
      "ownerRoute": "M08/M13/M14/M16",
      "question": "How can actual compile/recompile overhead and model/provider version changes invalidate apparently favorable S02 performance reports?",
      "primarySourceRole": "S02",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U08",
      "ownerRoute": "M02/M06/M08",
      "question": "Which accepted work/attempt/source lineage and unchanged input/protocol class must pair S03 partial-rebuild and full-build comparisons?",
      "primarySourceRole": "S03",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U09",
      "ownerRoute": "M07/M08/M09",
      "question": "What independently observed real VRAM/host RAM/pinned-page/thermal evidence can inform a future resource budget without minting a grant?",
      "primarySourceRole": "M09",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U10",
      "ownerRoute": "M09/M11/M12",
      "question": "Which original H01–H04 verified M11 ACK, M09 all-member joint lease and M12 attempt/action fences are prerequisites to any live benchmark?",
      "primarySourceRole": "M09",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U11",
      "ownerRoute": "M53/M54/M55",
      "question": "Which actual current rights and physical storage-owner proofs authorize optional traces, I/O samples and retention of profile artifacts?",
      "primarySourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U12",
      "ownerRoute": "M08/M56",
      "question": "What owner-defined uncertainty bounds and reproducible paired result protocol distinguish regression from normal variance across sessions?",
      "primarySourceRole": "M08",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U13",
      "ownerRoute": "M08/M57",
      "question": "Who will define and separately sign numeric production latency, memory or power budgets after actual admitted measurements?",
      "primarySourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U14",
      "ownerRoute": "M08/M10",
      "question": "How can measured capability evidence stay independent of frozen M10 advisor predictions and its unimplemented risk flags?",
      "primarySourceRole": "M10",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U15",
      "ownerRoute": "M01/M08/M13",
      "question": "Which S01–S04 hypotheses can be rejected on quality or foreground tail even if aggregate throughput appears higher?",
      "primarySourceRole": "M01",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U16",
      "ownerRoute": "M08/M56/M60",
      "question": "How can CPU host, GPU stream/device-event and I/O timeline clocks be reconciled without mistaking enqueue for execution?",
      "primarySourceRole": "M08",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U17",
      "ownerRoute": "M55/M60",
      "question": "Which separately qualified physical I/O and OS tracing contracts would permit profiling on Windows or Linux without assuming parity?",
      "primarySourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U18",
      "ownerRoute": "M02/M06/M53/M54",
      "question": "Which source-bound tenant and redaction scopes prevent trace exports or profiles from leaking raw media/prompt or credential data?",
      "primarySourceRole": "M02",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U19",
      "ownerRoute": "M08/M56",
      "question": "Which unchanged benchmark protocol, baseline/target commit, sample-distribution and uncertainty receipts qualify eventual regression triage?",
      "primarySourceRole": "M08",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    },
    {
      "id": "M13-S05-U20",
      "ownerRoute": "M13/M14/M16/M17/M60",
      "question": "Which qualified model/toolchain/backend/hardware version matrix would make a final M13 performance budget technology-neutral and revisit-safe?",
      "primarySourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null
    }
  ],
  "negativeCases": [
    {
      "id": "M13-S05-N01",
      "label": "QUALITY_BEFORE_SPEED",
      "trigger": "A candidate appears faster but its quality evidence is missing or violates original M01 fidelity.",
      "futureNonAuthorizingOracle": "NO_PERFORMANCE_PASS_WITH_QUALITY_FAILURE",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N02",
      "label": "UNKNOWN_IS_NOT_VALID",
      "trigger": "A partial M08 result without host-wide interference sensors is relabeled valid and promoted.",
      "futureNonAuthorizingOracle": "NO_UNKNOWN_TELEMETRY_TO_VALID",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N03",
      "label": "PROFILER_PERTURBATION",
      "trigger": "A tracing configuration adds synchronization or memory overhead but its raw results are compared with uninstrumented baseline.",
      "futureNonAuthorizingOracle": "NO_UNCALIBRATED_PROFILER_SPEEDUP",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N04",
      "label": "CUDA_ENQUEUE_ONLY",
      "trigger": "A CPU wall-clock stop before CUDA completion is treated as device-complete end-to-end latency.",
      "futureNonAuthorizingOracle": "NO_ENQUEUE_AS_GPU_COMPLETION",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N05",
      "label": "STALE_DEVICE",
      "trigger": "A benchmark is reused after driver or compute-device firmware replacement while its hardware version key stays unchanged.",
      "futureNonAuthorizingOracle": "NO_STALE_HARDWARE_PERFORMANCE_CERT",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N06",
      "label": "UNMATCHED_WORKLOAD",
      "trigger": "Baseline and candidate use different model seeds, graph revisions, quality policy or media dimensions.",
      "futureNonAuthorizingOracle": "NO_UNPAIRED_REGRESSION_RESULT",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N07",
      "label": "INSUFFICIENT_UNCERTAINTY",
      "trigger": "A tiny average improvement is claimed as reliable despite unqualified sample count and wide overlapping variability.",
      "futureNonAuthorizingOracle": "NO_INFERENCE_WITH_UNKNOWN_CONFIDENCE",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N08",
      "label": "COLD_WARM_CONFUSION",
      "trigger": "Warm cached runs are presented as representative cold first-use performance without startup/compile accounting.",
      "futureNonAuthorizingOracle": "NO_COLD_LATENCY_FROM_WARM_ONLY",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N09",
      "label": "TENANT_PROFILE_LEAK",
      "trigger": "Profiler traces include another tenant's prompt or credential content under an overly broad system capture.",
      "futureNonAuthorizingOracle": "NO_UNAUTHORIZED_PROFILE_EXPORT",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N10",
      "label": "NUMERIC_POLICY_INVENTION",
      "trigger": "A proposed threshold is marked adopted even though no independent policy owner assigned or qualified it.",
      "futureNonAuthorizingOracle": "NO_DEFAULT_SLO_FROM_DRAFT",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N11",
      "label": "RESOURCE_HINT_AS_LEASE",
      "trigger": "Performance pressure readings are used to authorize new GPU work without coherent M09 lease/owner ACK.",
      "futureNonAuthorizingOracle": "NO_RESOURCE_GRANT_FROM_METRIC",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N12",
      "label": "THERMAL_CAUSAL_ERROR",
      "trigger": "CPU/GPU thermal throttling or power cap is mislabeled as disk I/O bottleneck without independent sensor evidence.",
      "futureNonAuthorizingOracle": "NO_UNGROUNDED_CAUSAL_PROFILE",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N13",
      "label": "MISSING_OWNER_TRACE",
      "trigger": "A simulated all-green checklist is used in place of real M08/source security owner signatures and runtime authorization.",
      "futureNonAuthorizingOracle": "NO_MOCK_CHECKLIST_AS_OWNER_PROOF",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N14",
      "label": "STORAGE_STALE_RIGHTS",
      "trigger": "A cached profiler trace is retained or re-read after M55 physical deletion or M53 rights revocation.",
      "futureNonAuthorizingOracle": "NO_PROFILE_RETENTION_FROM_HISTORY",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N15",
      "label": "PARTIAL_REBUILD_LINEAGE",
      "trigger": "A faster S03 partial rebuild silently changes M02/M06 accepted work or M01 master quality.",
      "futureNonAuthorizingOracle": "NO_PERF_RESULT_AS_PRODUCTION_ADMISSION",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S05-N16",
      "label": "HYPOTHESIS_MARKED_MEASURED",
      "trigger": "A documentation-only S01–S04 metric is described as observed local GPU speedup by copying a vendor example.",
      "futureNonAuthorizingOracle": "NO_PUBLIC_DOC_AS_LOCAL_BENCHMARK",
      "status": "SPECIFIED_NOT_EXECUTED"
    }
  ],
  "nextStep": "AFTER_GREEN_WO0049_PREPARE_SEPARATE_M13_FINAL_TECH_REVIEW_AND_M14_M60_FORWARD_COMPAT_SCAN_SOURCE_ONLY_NOT_FROZEN",
  "stop": "S05 completes five documentary research sessions only, not M13 final technology review, independent cross-module compatibility, selected budget/profiler, installed profiling, real hardware measurement, authenticated quality/rights/OS/source owner signature, positive H01-H04 closure, M09 C01 adoption, GPU/CPU/OS/network/cloud/storage execution, actual negative integration cases or M10/M11/M12/M13 runtime. H01-H04 OPEN HIGH_FOR_FUTURE_FREEZE; B DIRECTION_ONLY; C01 UNADOPTED_NOT_FROZEN; all future original cases SPECIFIED_NOT_EXECUTED."
}
```
