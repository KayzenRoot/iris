# M08 — Microbenchmark Lab & Capability Envelope

Status: `S01_SLOW_PLANNING_ACTIVE`  
Planning base: `b3a2f191674c96e98887361e3a036737a53d8816`  
Predecessor: M07 `m07-contract-v1.0` durably closed  
Implementation: **NOT ADMITTED**

## 1. Mission

M08 is the empirical performance-characterization authority for bounded hardware/runtime microbenchmarks and evidence-backed capability envelopes. It consumes exact M07 Hardware Genome identity/projections and produces empirical measurements without rewriting M07 discovery truth, allocating resources, compiling execution plans, ranking creative quality, or claiming model fitness.

## 2. Canonical sessions

1. S01 — First-run safe microbenchmarks
2. S02 — Image/video/3D/audio benchmark probes
3. S03 — Capability Envelope and safe workload limits
4. S04 — Continuous performance fingerprint and drift
5. S05 — Benchmark calibration, aging and invalidation

Required lifecycle after S05: Final Technology Review → M09-M60 Forward Compatibility Scan → Module Contract Freeze → independent planning audit → protected merge → exact-main validation → separate implementation Work Order.

## 3. Authority firewall

M08 owns:
- empirical microbenchmark protocols and results;
- benchmark provenance bound to exact hardware/runtime context;
- measured throughput/latency/bandwidth and bounded saturation evidence;
- capability-envelope evidence derived from admitted benchmark protocols;
- performance fingerprints, drift evidence, calibration, aging and invalidation.

M08 does not own:
- hardware/runtime discovery truth or Genome identity (M07);
- VRAM/RAM leases, residency, spill/offload or resource control (M09);
- workload execution planning, predictive OOM or thermal policy (M10);
- worker/process lifecycle (M11);
- placement/orchestration (M12);
- empirical model fitness/model cards (M14);
- concrete provider/workflow compilation (M16);
- global eval/benchmark authority unrelated to hardware capability (M51);
- quality judgment/promotion (M01);
- project/build/release identity (M02/M06);
- physical storage lifecycle (M55);
- observability aggregation/dashboard authority (M56).

## 4. M07 inheritance contract

Every M08 empirical claim must bind:
- exact M07 GenomeId or explicitly named M07 projection/fingerprint;
- exact opaque subject/runtime identity;
- backend and relevant version axes;
- relevant capability evidence;
- freshness/material-change context;
- benchmark protocol/version and measurement semantics.

M08 must never mutate M07 facts. Discovery/report/smoke evidence remains distinguishable from empirical benchmark evidence.

## 5. S01 objective — First-run safe microbenchmarks

S01 defines how a newly observed machine/runtime may be characterized safely enough to produce useful empirical evidence without turning onboarding into a stress test or workstation hazard.

### 5.1 Admission before execution

A benchmark may run only when all required conditions are explicit:
- protocol ID and immutable protocol version;
- exact target subject/runtime;
- compatible M07 evidence binding;
- declared resource envelope;
- declared duration/work bounds;
- declared thermal/power abort conditions where observable;
- cancellation path;
- cooldown policy;
- foreground/background interference policy;
- data/privacy classification;
- result schema and units;
- invalidation inputs;
- user/policy authorization for active measurement.

Unknown mandatory prerequisites fail closed.

### 5.2 Safety classes

S01 introduces planning candidates:
- `TINY`: milliseconds/very small buffers; onboarding-safe when admitted;
- `BOUNDED`: short active measurement with strict memory/time ceilings;
- `SUSTAINED`: longer thermal/stability characterization; not silently run at first launch;
- `DESTRUCTIVE_OR_STRESS`: prohibited for normal M08 first-run operation.

Class names remain planning candidates until contract freeze.

### 5.3 Probe budget

Every active benchmark must have hard ceilings for:
- wall-clock duration;
- warm-up duration;
- iterations;
- allocation size;
- host RAM;
- device memory;
- output bytes;
- concurrency;
- retry count;
- cooldown;
- total first-run benchmark budget.

No benchmark may use “run until stable” without a hard upper bound.

### 5.4 Workstation coexistence

M08 must assume the device may be interactive and shared with unrelated workloads. First-run characterization must:
- detect/record interference rather than kill unrelated processes;
- never tune voltage, clocks, fan curves or OS power plans;
- never evict unrelated allocations;
- never require privileged escalation merely to obtain a score;
- abort or invalidate evidence when interference exceeds protocol tolerance;
- distinguish unavailable telemetry from safe conditions.

### 5.5 Measurement semantics

A result is not a naked score. Minimum candidate envelope:
- metric ID;
- semantic version;
- quantity kind;
- unit;
- directionality;
- aggregation method;
- warm-up policy;
- sample count;
- timing source;
- uncertainty/dispersion;
- censoring/abort state;
- environment binding;
- provenance/evidence refs;
- timestamp/freshness;
- validity state.

Raw values from incompatible protocols/versions are not directly comparable.

### 5.6 Result states

Candidate closed states:
- `VALID`
- `INVALID_INTERFERENCE`
- `INVALID_THERMAL_ABORT`
- `INVALID_RESOURCE_ABORT`
- `INVALID_PROTOCOL`
- `CANCELLED`
- `UNSUPPORTED`
- `UNAVAILABLE`
- `STALE`
- `PARTIAL`

Failure/abort is evidence, not permission to fabricate a lower capability.

### 5.7 8 GB / CPU-only doctrine

8 GB VRAM and CPU-only systems are first-class benchmark targets. S01 must characterize what is safely measurable, not grade such systems as defective. Scarcity cannot lower M01 quality targets or mutate M05 identity/semantic obligations.

## 6. S01 technology discovery candidates

### IRIS-BPF — Benchmark Protocol Fabric
Versioned immutable protocol definitions, measurement semantics, prerequisites, safety class and comparability rules.

### IRIS-SBG — Safety Budget Governor
Enforces hard time/memory/iteration/concurrency/cooldown ceilings before and during an admitted benchmark.

### IRIS-EPB — Empirical Provenance Binder
Binds every result to exact M07 Genome/projection, subject/runtime, backend/version axes and protocol revision.

### IRIS-ICD — Interference & Contamination Detector
Records foreground load, unrelated contention and measurement contamination; invalidates rather than “correcting” unsupported data.

### IRIS-AEG — Abort Evidence Generator
Turns thermal/resource/user/protocol aborts into explicit structured evidence instead of missing-data ambiguity.

### IRIS-CMF — Comparability Matrix Fabric
Defines when two benchmark results are comparable, conditionally comparable, or incomparable across protocol/hardware/runtime/version changes.

### IRIS-UQF — Uncertainty & Quality-of-Measurement Fabric
Carries dispersion, timing quality, sample sufficiency and measurement uncertainty without converting them into M01 creative quality.

### IRIS-FRB — First-Run Benchmark Budgeter
Builds a bounded onboarding characterization set from admitted protocol classes. It selects benchmark probes only; it does not become M10 execution planning.

## 7. S01 hard-invariant candidates

1. Every empirical result binds an exact immutable benchmark protocol version.
2. Every empirical result binds exact M07 hardware/runtime provenance.
3. M08 cannot mutate M07 discovery facts.
4. Smoke verification from M07 is not benchmark evidence.
5. Benchmark evidence cannot become M01 quality authority.
6. Benchmark evidence cannot mutate M05 identity semantics.
7. M08 cannot allocate production VRAM/RAM leases.
8. M08 cannot emit M10 execution plans.
9. First-run benchmarks are bounded before execution.
10. Unknown mandatory safety prerequisites fail closed.
11. A benchmark cannot escalate privileges to obtain a result.
12. A benchmark cannot modify voltage, clocks, fan curves or OS power policy.
13. A benchmark cannot kill/suspend unrelated processes.
14. A benchmark cannot evict unrelated allocations.
15. Every allocation has a declared hard ceiling.
16. Every benchmark has a declared hard duration ceiling.
17. Every retry policy is bounded.
18. Every cooldown policy is explicit for protocols that can materially heat hardware.
19. User cancellation is terminal for the active attempt.
20. Aborted measurements cannot be promoted to VALID.
21. Interference beyond protocol tolerance invalidates or censors the result.
22. Missing telemetry cannot be interpreted as safe telemetry.
23. Timing source and unit are explicit.
24. Metric quantity kind and directionality are explicit.
25. Warm-up samples cannot silently contaminate measured samples.
26. Sample count is explicit.
27. Aggregation semantics are versioned.
28. Dispersion/uncertainty is retained where the protocol requires it.
29. Raw scores from incompatible protocol versions cannot be directly compared.
30. Comparability requires explicit CMF judgment.
31. Result freshness is explicit.
32. Relevant M07 material change can invalidate derived benchmark evidence.
33. Runtime/backend/driver changes cannot silently inherit old empirical truth.
34. CPU-only systems are valid benchmark subjects.
35. 8 GB VRAM systems are valid benchmark subjects.
36. Resource scarcity cannot silently lower canonical quality.
37. A failed benchmark does not prove hardware absence.
38. An unsupported protocol does not prove general hardware incapability.
39. Synthetic fixtures cannot masquerade as physical benchmark evidence.
40. Benchmark output cannot claim model-specific fitness reserved to M14.
41. First-run budget selection cannot become general execution planning.
42. Benchmark data cannot become canonical M02/M06 production identity.
43. Any M06 materiality binding must be explicit and named.
44. Active benchmark execution must be attributable to an authorization/policy decision.
45. Results preserve exact subject/runtime scoping on multi-device systems.
46. Cross-device aggregation cannot erase per-device provenance.
47. Measurement corrections/calibration cannot overwrite raw evidence.
48. Derived values retain source-result lineage.
49. Invalidated results remain auditable.
50. S01 cannot silently expand into sustained stress testing.

## 8. S01 proof obligations for later implementation

Future implementation must prove at minimum:
- deterministic protocol identity/serialization;
- exact M07 provenance binding;
- bounded budget enforcement;
- cancellation/abort semantics;
- contamination/interference invalidation;
- incompatible-protocol comparison rejection;
- exact-device scoping;
- CPU-only and 8 GB synthetic fixtures;
- no forbidden authority imports or product-planner/resource-governor behavior;
- no physical hardware claim from synthetic fixtures.

## 9. S01 risks requiring later sessions

- Thermal/power observability differs strongly by platform.
- GPU/provider SDK benchmark adapters may require qualified optional integrations.
- Media-domain probes belong to S02 and must not be prematurely frozen here.
- “Safe workload limits” belong to S03 and require conservative inference from empirical evidence, not a single peak score.
- Continuous fingerprint/drift belongs to S04.
- Calibration, aging and invalidation policy belongs to S05.

## 10. S01 checkpoint

S01 Slow Planning establishes the empirical/safety substrate only. No M08 implementation is admitted. Next permitted work is S02 planning after independent review of this S01 delta.

# S02 — Image / Video / 3D / Audio Benchmark Probes

Status: `S02_SLOW_PLANNING_ACTIVE`

## 11. S02 objective

S02 defines domain-specific empirical probes that characterize compute, memory-transfer and media-engine behavior while preserving the S01 safety/provenance substrate. These probes measure bounded hardware/runtime behavior. They do not grade generated content, rank models, select workflows, or claim production-safe limits before S03.

## 12. Cross-domain probe contract

Every S02 probe must additionally declare:
- domain and operation family;
- synthetic or redistributable deterministic fixture identity;
- input shape/format;
- output shape/format when applicable;
- precision/data type;
- warm-up and measured phases;
- synchronization semantics;
- host-to-device/device-to-host/device-local transfer scope where relevant;
- measured latency/throughput quantities;
- peak observed benchmark allocation as evidence, not M09 reservation policy;
- correctness/conformance predicate sufficient to reject meaningless speed;
- provider/backend adapter identity;
- protocol-specific comparability dimensions.

A fast but incorrect operation is not a valid performance result.

## 13. Image probe families

Candidate bounded families:
- decode/encode for admitted image codecs;
- resize/resample;
- colorspace conversion;
- tensor upload/download;
- convolution-like/tensor primitives where backend-neutral semantics can be defined;
- tiled image transform with deterministic tile geometry;
- bounded high-resolution allocation/transfer probe.

Image probes must not become image-quality evaluation, model inference ranking or M16 workflow compilation.

## 14. Video probe families

Candidate bounded families:
- codec decode throughput/latency;
- codec encode throughput/latency;
- frame upload/download;
- colorspace/pixel-format conversion;
- bounded frame-pipeline concurrency;
- hardware-engine session admission/conformance;
- short GOP/container-independent elementary-stream fixtures where licensing permits.

Video probes must distinguish:
- codec from container;
- encode from decode;
- software path from hardware-engine path;
- bit depth/chroma/profile/level;
- single-stream from bounded multi-stream evidence.

S02 cannot infer sustained production session capacity from a short probe; S03 owns safe-envelope derivation.

## 15. 3D probe families

Candidate bounded families:
- buffer upload/download;
- texture upload/readback;
- shader/kernel dispatch latency;
- raster fill/fragment bounded probe;
- geometry/vertex throughput proxy;
- compute primitive;
- bounded ray-query/ray-tracing capability probe only where an admitted backend exposes it;
- synchronization/fence overhead.

3D probes measure runtime/hardware primitives, not scene artistic quality, renderer choice or production-frame performance for arbitrary scenes.

## 16. Audio probe families

Candidate bounded families:
- PCM transform/copy;
- sample-rate conversion;
- FFT/spectral primitive;
- bounded convolution;
- codec encode/decode where admitted;
- device-independent buffer processing latency;
- CPU vectorization/backend primitive where semantically stable.

Audio probes must not access microphones, speakers or private user media merely to obtain a benchmark. Synthetic deterministic fixtures are preferred.

## 17. Transfer and bandwidth semantics

M08 may now measure the bandwidth that M07 deliberately refused to infer. Each bandwidth result must name the exact path:
- host ↔ host;
- host → device;
- device → host;
- device-local;
- peer → peer where explicitly supported and safely admitted.

Measured bandwidth cannot be attached back onto M07 topology as discovery truth. Direction, payload size, synchronization, pinned/pageable semantics, topology binding and protocol version remain explicit.

## 18. Correctness-before-speed gate

Each probe has a bounded correctness oracle appropriate to the primitive:
- exact digest for deterministic byte-preserving operations;
- bounded numeric tolerance for floating-point primitives;
- structural decode/encode validation for media;
- explicit unsupported state when a required semantic cannot be verified.

A timing sample is discarded or invalidated when its correctness oracle fails. M08 never rewards wrong output for speed.

## 19. Domain technology candidates

### IRIS-MPB — Multimodal Probe Bank
Versioned registry of image/video/3D/audio primitive protocols with deterministic fixture manifests.

### IRIS-COG — Correctness Oracle Gate
Separates successful execution from semantically valid benchmark evidence.

### IRIS-TPE — Transfer Path Examiner
Measures explicitly named directional memory/data paths without mutating M07 topology.

### IRIS-MEE — Media Engine Examiner
Measures bounded codec-engine behavior with exact codec/profile/bit-depth/chroma/direction/session provenance.

### IRIS-GPK — Graphics Primitive Kernel
Backend-qualified 3D primitive probes that avoid scene/renderer policy authority.

### IRIS-APK — Audio Primitive Kernel
Deterministic audio DSP/codec primitive probes without private media/device capture.

### IRIS-DFM — Deterministic Fixture Manifest
Content-addressed benchmark fixtures with generator/version/license/privacy metadata.

### IRIS-BAC — Backend Adapter Capsule
Pins provider/backend adapter identity and translates only protocol mechanics; it cannot redefine benchmark semantics.

## 20. S02 hard-invariant candidates

51. Every S02 result identifies exactly one benchmark domain and operation family.
52. Every probe binds an immutable deterministic fixture identity.
53. Private user media is not required for benchmark fixtures.
54. Fixture generation is versioned and reproducible.
55. Fixture licensing/redistribution metadata is explicit where persisted/distributed.
56. Correctness is checked independently of timing.
57. Incorrect output cannot produce VALID performance evidence.
58. Floating-point correctness tolerances are protocol-versioned.
59. Timing excludes or includes setup only as explicitly declared by protocol.
60. Synchronization semantics are explicit for asynchronous devices.
61. Device timings cannot be inferred from host enqueue latency alone.
62. Transfer measurements name exact direction.
63. Transfer measurements name payload size.
64. Transfer measurements name synchronization policy.
65. Pinned/pageable or equivalent host-memory semantics are explicit when material.
66. Device-local bandwidth cannot masquerade as host-device bandwidth.
67. Peer bandwidth requires exact source and destination subject identity.
68. M08 measured bandwidth cannot mutate M07 topology evidence.
69. Image codec probes identify codec and relevant format/profile semantics.
70. Image transforms identify dimensions, channels and data type.
71. Image benchmark evidence cannot become image-quality judgment.
72. Video encode and decode evidence remain separate.
73. Video codec and container semantics remain separate.
74. Hardware and software video paths remain separate.
75. Video bit depth/chroma/profile are explicit when material.
76. Single-stream evidence cannot prove multi-stream capacity.
77. Short video probes cannot prove sustained production capacity.
78. Multi-stream probes have explicit bounded concurrency.
79. Media-engine session failures remain evidence, not generalized hardware absence.
80. 3D buffer/texture transfer evidence remains path-specific.
81. Shader/compute dispatch timing declares synchronization semantics.
82. Raster proxy evidence cannot claim arbitrary-scene FPS.
83. Geometry proxy evidence cannot claim renderer fitness.
84. Ray capability probes cannot claim production ray-tracing capacity.
85. 3D probes cannot select a renderer.
86. Audio fixtures are deterministic and non-private by default.
87. Audio sample rate/channel layout/sample format are explicit.
88. Audio DSP numeric tolerance is explicit where non-exact.
89. Audio benchmark evidence cannot become perceptual/audio-quality judgment.
90. Audio probes cannot require microphone capture.
91. Audio probes cannot require speaker playback.
92. Provider adapters cannot redefine canonical metric semantics.
93. Adapter version is part of empirical provenance.
94. Backend fallback cannot silently merge results with the requested backend.
95. CPU fallback is reported as CPU fallback.
96. Peak observed benchmark allocation is evidence, not an M09 lease/reservation.
97. Probe concurrency is benchmark-local and cannot become M12 placement policy.
98. Domain probes inherit all S01 abort/interference/budget rules.
99. Synthetic fixture results are explicitly labeled synthetic empirical evidence.
100. S02 cannot derive S03 safe workload envelopes prematurely.

## 21. S02 proof obligations for later implementation

Future implementation must prove:
- deterministic fixture generation and digest stability;
- correctness gate rejects fast-but-wrong results;
- async timing cannot use enqueue-only latency as device execution time;
- directional transfer metrics remain distinct;
- codec/container and encode/decode separation;
- software/hardware media path separation;
- single-stream evidence does not imply multi-stream capacity;
- 3D proxy results cannot claim arbitrary scene FPS;
- audio probes use synthetic data without capture devices;
- backend fallback is provenance-visible;
- peak benchmark allocation does not create M09 state.

## 22. S02 checkpoint

S01 independent audit: `APPROVED`.  
S02 adds domain probe semantics and invariants 51-100. No implementation is admitted. Next permitted work after independent S02 review is S03 Capability Envelope and safe workload limits.

