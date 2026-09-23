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

# S03 — Capability Envelope & Safe Workload Limits

Status: `S03_SLOW_PLANNING_ACTIVE`

## 23. S03 objective

S03 converts qualified M08 empirical evidence into conservative, versioned capability envelopes. An envelope describes what a specific hardware/runtime/protocol context has empirically demonstrated within declared safety margins. It is not a scheduler decision, resource lease, production guarantee, model recommendation, quality downgrade, or arbitrary extrapolation.

## 24. Envelope dimensions

A capability envelope may contain independently evidenced dimensions such as:
- admitted working-set/allocation range;
- input shape/resolution range;
- batch/concurrency range;
- latency and throughput bands;
- directional transfer bands;
- codec/session dimensions;
- precision/data-type dimensions;
- bounded duration class;
- thermal/power observation context;
- interference class;
- confidence/coverage;
- provenance/freshness/invalidation state.

Missing dimensions remain unknown. A strong dimension cannot launder a weak or unmeasured dimension.

## 25. Demonstrated, bounded and unsupported regions

S03 separates:
- `DEMONSTRATED`: directly supported by valid empirical evidence;
- `CONSERVATIVE_BOUND`: derived inside explicitly permitted interpolation/safety-margin rules;
- `UNKNOWN`: not sufficiently evidenced;
- `UNSUPPORTED_PROTOCOL`: protocol cannot characterize the requested dimension;
- `INVALIDATED`: previously derived region no longer valid.

No generic `SAFE` boolean is sufficient.

## 26. Safe workload limit semantics

A “safe workload limit” means only: a conservative empirical boundary under the named protocol, environment, hardware/runtime binding, safety margin and validity window. It does not mean:
- impossible to exceed;
- production SLA;
- guaranteed OOM avoidance;
- guaranteed thermal stability;
- recommended execution plan;
- acceptable creative quality.

M10 may consume an M08 envelope as evidence but owns execution planning and predictive OOM/thermal policy.

## 27. Conservative derivation

Envelope derivation must:
- retain all source result IDs;
- declare derivation algorithm/version;
- declare safety margins;
- reject unsupported extrapolation;
- distinguish interpolation from extrapolation;
- preserve discontinuities;
- retain failed/aborted boundary observations;
- avoid monotonicity assumptions unless protocol semantics prove them;
- emit uncertainty/coverage separately from measured values.

A single peak result cannot define a sustainable envelope.

## 28. Boundary search

S03 may define bounded experimental boundary-search protocols, but they must inherit S01 safety budgets. Candidate strategies include:
- bracketed monotonic search only for dimensions whose monotonic behavior is contractually justified;
- bounded grid/sparse sampling;
- adaptive refinement with hard attempt/time/allocation ceilings;
- explicit stop on thermal/resource/interference invalidation.

Boundary search is benchmark protocol logic, not M10 workload planning.

## 29. Memory envelope

Memory characterization may record:
- requested benchmark allocation;
- successfully admitted allocation;
- peak observed benchmark allocation;
- failure/abort point;
- fragmentation/context overhead observations when measurable;
- exact runtime/backend and concurrent benchmark conditions.

It cannot create production reservations, evict allocations, or promise that a later production workload will fit. M09 owns resource state/leases; M10 owns predictive OOM policy.

## 30. Concurrency envelope

Concurrency evidence must preserve:
- operation/protocol family;
- concurrency degree;
- per-lane workload identity;
- aggregate and per-lane metrics;
- synchronization;
- fairness/starvation observations where measurable;
- resource/thermal/interference context.

A benchmark-local concurrency envelope cannot become M12 placement or scheduling policy.

## 31. Sustainability classes

S03 candidate evidence classes:
- `BURST`: short bounded empirical evidence;
- `SHORT_STEADY`: bounded steady interval;
- `SUSTAINED_OBSERVED`: longer admitted observation with explicit duration;
- `UNKNOWN_SUSTAINABILITY`.

Duration is evidence. Class names never imply indefinite stability.

## 32. Envelope technology candidates

### IRIS-CEF — Capability Envelope Fabric
Immutable multidimensional envelope artifact with exact source lineage and validity context.

### IRIS-CBD — Conservative Boundary Deriver
Produces bounded demonstrated/conservative regions without unsupported extrapolation.

### IRIS-BSE — Bounded Search Engine
Runs contract-qualified bracket/grid/refinement protocols under S01 hard budgets.

### IRIS-MEM — Memory Envelope Mapper
Characterizes benchmark allocation boundaries without becoming M09 allocator state.

### IRIS-CCM — Concurrency Capability Mapper
Measures bounded concurrency behavior without scheduling/placement authority.

### IRIS-SCM — Sustainability Classifier Matrix
Separates burst, bounded steady and sustained-observed evidence by actual observation duration.

### IRIS-ECC — Envelope Coverage & Confidence
Represents per-dimension evidence coverage, uncertainty and confidence without collapsing to one score.

### IRIS-ELF — Envelope Lineage Fabric
Binds every derived boundary to source result IDs, derivation version, margin and invalidation dependencies.

## 33. S03 hard-invariant candidates

101. Every capability envelope binds exact M07 and M08 provenance.
102. Every envelope has an immutable schema/version identity.
103. Envelope dimensions remain independently evidenced.
104. Unknown dimensions remain unknown.
105. One strong dimension cannot promote another unmeasured dimension.
106. Demonstrated evidence is distinguishable from conservative derivation.
107. Interpolation is distinguishable from extrapolation.
108. Unsupported extrapolation cannot produce a conservative bound.
109. Derivation algorithm/version is explicit.
110. Safety margin is explicit.
111. Source result IDs are retained.
112. Failed/aborted boundary observations remain retained.
113. A single peak result cannot prove sustainable capacity.
114. A single success cannot prove a maximum limit.
115. A single failure cannot prove all larger workloads fail unless monotonicity is contractually justified.
116. Monotonicity assumptions are protocol-specific and explicit.
117. Boundary search has a hard attempt ceiling.
118. Boundary search has a hard wall-clock ceiling.
119. Boundary search inherits allocation/concurrency ceilings.
120. Boundary search aborts on inherited safety conditions.
121. Adaptive search cannot become unbounded exploration.
122. Envelope derivation cannot rewrite raw benchmark results.
123. Corrections/calibration preserve original source evidence.
124. Safe workload limit is not a production SLA.
125. Safe workload limit is not guaranteed OOM avoidance.
126. Safe workload limit is not guaranteed thermal stability.
127. Safe workload limit is not an execution plan.
128. Safe workload limit cannot lower M01 quality.
129. M10 owns workload planning using envelope evidence.
130. M09 owns production resource leases/residency.
131. Memory envelope cannot reserve production memory.
132. Memory envelope cannot evict unrelated allocations.
133. Peak observed benchmark allocation is not available-memory truth.
134. Allocation failure does not prove physical memory absence.
135. Fragmentation/context overhead observations retain environment provenance.
136. CPU and device memory dimensions remain distinct.
137. Host spill/offload decisions remain M09/M10 authority.
138. Concurrency envelope is operation/protocol-specific.
139. Per-lane and aggregate metrics remain distinguishable.
140. Benchmark concurrency cannot become scheduler concurrency.
141. Benchmark concurrency cannot become placement policy.
142. Single-stream evidence cannot prove multi-stream envelope.
143. Multi-stream evidence cannot erase per-stream provenance.
144. Burst evidence cannot be labeled sustained.
145. Sustainability class records actual observation duration.
146. Sustained-observed does not imply indefinite stability.
147. Missing thermal telemetry cannot prove thermal sustainability.
148. Thermal abort evidence constrains only its exact context unless derivation rules justify broader scope.
149. Interference-contaminated evidence cannot silently define an envelope.
150. Invalid benchmark evidence cannot be a valid envelope source.
151. Stale source evidence makes dependent envelope stale or invalid per policy.
152. Relevant M07 material change invalidates dependent envelope as declared.
153. Protocol-breaking change invalidates incompatible envelopes.
154. Backend/driver/runtime change cannot silently inherit old envelopes.
155. Envelope comparability requires explicit compatibility judgment.
156. Cross-machine envelope aggregation cannot erase machine identity.
157. Cross-device envelope aggregation cannot erase device identity.
158. Envelope confidence/coverage cannot collapse into a hardware ranking.
159. Envelope evidence cannot claim model-specific fitness.
160. Envelope evidence cannot select a model.
161. Envelope evidence cannot select a renderer/workflow.
162. Envelope evidence cannot claim creative-quality sufficiency.
163. Synthetic empirical evidence remains labeled synthetic.
164. Simulated evidence cannot masquerade as physical measurement.
165. Conservative margin cannot be negative.
166. Margin changes produce a new derived artifact identity.
167. Envelope derivation is deterministic for identical ordered inputs/configuration.
168. Envelope serialization is canonical for fingerprinting.
169. Envelope artifacts are immutable once issued.
170. Invalidated envelopes remain auditable.
171. Consumer projections are explicit and named.
172. Consumer projections cannot add authority absent from the source envelope.
173. M06 reproducibility binding is explicit when material.
174. M14/M51 may bind M08 evidence but cannot retroactively redefine it.
175. S03 cannot silently absorb S04 drift monitoring or S05 calibration/aging authority.

## 34. S03 proof obligations for later implementation

Future implementation must prove:
- no single-score/generic-safe collapse;
- unknown dimension preservation;
- rejection of unsupported extrapolation;
- deterministic derivation and immutable identity;
- bounded search termination;
- explicit monotonicity requirements;
- source lineage and failed-boundary retention;
- memory/concurrency authority firewalls;
- burst vs sustained separation;
- stale/invalidation propagation;
- no model/workflow/quality selection.

## 35. S03 checkpoint

S02 independent audit: `APPROVED`.  
S03 adds capability-envelope semantics and invariants 101-175. No implementation is admitted. Next permitted work after independent S03 review is S04 Continuous performance fingerprint and drift.

# S04 — Continuous Performance Fingerprint & Drift

Status: `S04_SLOW_PLANNING_ACTIVE`

## 36. S04 objective

S04 defines stable, privacy-conscious performance fingerprints and evidence-based drift detection over qualified M08 results. It detects meaningful empirical change without converting M08 into an always-on stress agent, observability backend, anomaly-response controller, scheduler, or hardware-health oracle.

## 37. Performance fingerprint

A performance fingerprint is a versioned projection over explicitly selected compatible benchmark evidence. It must declare:
- fingerprint schema/version;
- included protocol/metric identities;
- exact M07 Genome/projection binding;
- environment/runtime/backend dimensions;
- normalization rules, if any;
- ordering/canonicalization;
- validity/freshness;
- excluded dimensions;
- privacy/redaction policy;
- source result IDs.

Fingerprint equality means equality under that exact projection/version only. It does not mean identical hardware or identical future performance.

## 38. Drift model

Drift is an evidence-backed difference between comparable fingerprints/result windows. Candidate classes:
- `NO_MATERIAL_DRIFT`;
- `PERFORMANCE_SHIFT`;
- `VARIANCE_SHIFT`;
- `CAPABILITY_REGION_CHANGE`;
- `ENVIRONMENT_CHANGED`;
- `INCOMPARABLE`;
- `INSUFFICIENT_EVIDENCE`;
- `STALE_BASELINE`.

Thresholds are protocol/metric/version specific. A universal percentage threshold is prohibited.

## 39. Baseline semantics

A baseline is an immutable named reference, not “the truth forever”. It records:
- exact source fingerprint;
- creation policy/version;
- creation time;
- environment binding;
- validity dependencies;
- promotion evidence;
- supersession lineage.

A new result cannot silently replace a baseline. Baseline promotion is explicit and auditable.

## 40. Continuous does not mean constant

S04 “continuous” means lifecycle-aware repeatability, not nonstop benchmarking. Rechecks may be triggered by:
- relevant M07 material-change event;
- protocol/calibration change;
- explicit user/policy request;
- age/freshness threshold;
- consumer-required validation;
- sufficiently idle/eligible window under future scheduling policy.

M08 defines benchmark eligibility evidence and cadence semantics, but does not own M12 scheduling or background worker lifecycle.

## 41. Drift attribution

S04 may correlate drift with declared context changes such as:
- driver/runtime/backend version;
- thermal/power observation context;
- topology/material hardware change;
- protocol/calibration revision;
- interference class.

Correlation is not causation. M08 must not claim a root cause unless the protocol supplies evidence sufficient for that claim.

## 42. Noise and statistical guardrails

Drift logic must account for:
- measurement dispersion;
- sample/window sufficiency;
- repeated-measures semantics;
- multiple metrics;
- censoring/invalid samples;
- minimum meaningful effect;
- confidence/uncertainty.

A tiny numeric difference is not automatically material drift.

## 43. Privacy and fingerprintability

Performance fingerprints can become device identifiers. Therefore:
- consumer projections use minimum necessary dimensions;
- raw stable hardware identifiers are not added merely to strengthen fingerprint uniqueness;
- external/export projections support redaction/pseudonymous binding;
- benchmark fingerprints are not authentication credentials;
- cross-user/device correlation requires explicit authority outside M08;
- retention/export remains governed by appropriate storage/privacy modules.

## 44. Drift technology candidates

### IRIS-PFF — Performance Fingerprint Fabric
Canonical versioned projection of compatible empirical evidence.

### IRIS-DED — Drift Evidence Detector
Compares qualified windows/fingerprints using metric-specific materiality and uncertainty.

### IRIS-BLR — Baseline Lineage Registry
Immutable named baselines with explicit promotion, supersession and validity lineage.

### IRIS-RTE — Recheck Trigger Evaluator
Determines that benchmark evidence is eligible/required for refresh without scheduling workers itself.

### IRIS-NGF — Noise Guard Fabric
Prevents ordinary variance and insufficient samples from becoming false drift.

### IRIS-DAG — Drift Attribution Graph
Links observed shifts to context-change evidence without inventing causation.

### IRIS-PFP — Privacy Fingerprint Projector
Produces consumer-specific minimum-necessary/redacted performance projections.

### IRIS-DCP — Drift Compatibility Protocol
Fails closed when baseline/current evidence cannot be validly compared.

## 45. S04 hard-invariant candidates

176. Every performance fingerprint has an explicit schema/version.
177. Every fingerprint names included metric/protocol identities.
178. Every fingerprint retains exact source-result lineage.
179. Fingerprint canonicalization is deterministic.
180. Fingerprint equality is projection/version scoped.
181. Fingerprint equality cannot prove identical hardware.
182. Fingerprint inequality cannot by itself prove hardware failure.
183. Fingerprints cannot become authentication credentials.
184. Raw stable identifiers are not added solely to increase uniqueness.
185. Export projections support minimum-necessary disclosure.
186. Redaction cannot silently change fingerprint semantics.
187. Drift comparison requires compatible protocol semantics.
188. Drift comparison requires compatible metric semantics.
189. Incompatible evidence produces INCOMPARABLE, not a numeric drift.
190. Insufficient evidence produces INSUFFICIENT_EVIDENCE.
191. Stale baseline state is explicit.
192. Drift thresholds are metric/protocol specific.
193. A universal drift percentage is prohibited.
194. Measurement dispersion participates where required.
195. Sample/window sufficiency is explicit.
196. Invalid/censored samples cannot silently become valid drift inputs.
197. Tiny numeric difference cannot automatically become material drift.
198. Multiple-metric drift preserves per-metric evidence.
199. Aggregate drift cannot erase contradictory dimensions.
200. Baselines are immutable once issued.
201. Baseline promotion is explicit.
202. Baseline replacement is not implicit on new measurement.
203. Baseline supersession preserves lineage.
204. Baseline creation policy/version is recorded.
205. Baseline validity dependencies are recorded.
206. Relevant M07 material change can invalidate baseline comparability.
207. Protocol-breaking change can invalidate baseline comparability.
208. Calibration-breaking change can invalidate baseline comparability.
209. Driver/runtime/backend changes remain visible in drift context.
210. Context correlation cannot be claimed as causation.
211. Root-cause claims require protocol-supported evidence.
212. “Continuous” cannot require nonstop benchmarking.
213. Rechecks inherit S01 safety budgets.
214. Rechecks cannot bypass user/policy authorization.
215. M08 cannot own worker lifecycle for periodic rechecks.
216. M08 cannot become M12 scheduling authority.
217. Idle-window eligibility cannot become process-killing/preemption authority.
218. Drift detection cannot modify clocks/power/fans.
219. Drift detection cannot auto-tune production workloads.
220. Drift detection cannot auto-lower creative quality.
221. Drift evidence cannot directly mutate M09 resource state.
222. Drift evidence cannot directly emit M10 execution plans.
223. Drift evidence cannot directly rank M14 models.
224. Performance shift is not hardware-health diagnosis.
225. Performance shift is not proof of hardware degradation.
226. Thermal-context correlation is not proof of thermal causation.
227. Variance shift remains distinct from mean/median performance shift.
228. Capability-region change retains source envelope lineage.
229. Drift artifacts are immutable and auditable.
230. Drift recalculation uses versioned logic.
231. Logic-version change produces a distinguishable derived artifact.
232. Consumer projections cannot add absent authority.
233. Cross-machine comparison preserves each machine identity.
234. Cross-device comparison preserves each device identity.
235. Cross-user correlation is outside M08 authority unless separately governed.
236. Benchmark fingerprints cannot expose private fixture content.
237. Synthetic fixtures remain labeled in fingerprint provenance.
238. Missing telemetry cannot be interpreted as unchanged environment.
239. A missing recheck cannot be interpreted as no drift.
240. A cancelled recheck cannot be interpreted as no drift.
241. A failed recheck cannot silently invalidate a valid baseline without policy.
242. Stale evidence cannot silently remain current.
243. Freshness policy is explicit and versioned.
244. Consumer-required freshness cannot force unsafe benchmarking.
245. Drift evidence can trigger a request for reevaluation but not execute downstream policy.
246. M56 may aggregate/display M08 drift but does not redefine M08 evidence.
247. M51 may consume benchmark evidence for evals but cannot rewrite M08 baseline lineage.
248. M06 materiality binding remains explicit when performance drift matters to reproducibility.
249. Privacy/redaction policy is part of exported fingerprint semantics.
250. S04 cannot silently absorb S05 calibration, aging or invalidation policy.

## 46. S04 proof obligations for later implementation

Future implementation must prove:
- deterministic fingerprint projection/canonicalization;
- incompatible comparison fails closed;
- immutable baseline promotion/supersession;
- noise guard rejects underpowered/tiny differences;
- missing/cancelled/failed recheck is not “no drift”;
- material-change/freshness trigger semantics without scheduler authority;
- correlation cannot become causal diagnosis;
- privacy projection minimizes stable identifying dimensions;
- no auto-tuning/resource mutation/quality lowering.

## 47. S04 checkpoint

S03 independent audit: `APPROVED`.  
S04 adds fingerprint/drift semantics and invariants 176-250. No implementation is admitted. Next permitted work after independent S04 review is S05 Benchmark calibration, aging and invalidation.

