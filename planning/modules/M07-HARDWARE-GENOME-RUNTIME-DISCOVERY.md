# M07 — Hardware Genome & Runtime Discovery

Status: `S01_COMPLETE_FOR_MODULE_PLANNING`
Planning model: `FULL_VERSION_NO_MVP`
Issue: #50
Planning base: `b52e9837bef893c5c040c929520996cd110579e6`

## Governing boundary

M07 is the provider-neutral **hardware/runtime observation authority** for IRIS. It discovers, normalizes and versions evidence about the machine/runtime substrate so later modules can reason from explicit facts instead of hard-coded GPU presets.

M07 does **not** benchmark performance, allocate VRAM/RAM, choose models, compile execution plans, supervise workers, place jobs, lower quality targets, or become physical-storage authority.

Ownership remains separated:

- M01 owns quality judgment and promotion.
- M02 owns project/production/build lifecycle semantics.
- M06 owns operational production-state/reproducibility semantics and consumes hardware facts only when explicitly material.
- M07 owns observed hardware/runtime facts and discovery evidence.
- M08 owns microbenchmarks and capability envelopes.
- M09 owns Resource Digital Twin state, VRAM leases/residency and spill/offload governance.
- M10 owns hardware-aware execution planning and predictive OOM/thermal shields.
- M11 owns worker/process lifecycle.
- M12 owns compute placement/orchestration.
- M14 owns empirical model cards/model capability truth.
- M55 owns physical media storage.
- M56 owns observability/dashboard aggregation.

The 8 GB VRAM rule remains a first-class product invariant. Low capacity is a fact to plan around, never a reason for M07 to mark a valid device as unsupported or silently lower requested quality.

# S01 — GPU/CPU/RAM/storage/runtime discovery

## 1. Goal

Define a deterministic, bounded, side-effect-free discovery layer that can answer:

- what compute/storage/runtime substrate is observable;
- which exact subject each observation refers to;
- where the evidence came from;
- when it was observed;
- whether the result is known, unknown, unavailable, permission-blocked, conflicting or stale;
- what facts are safe for downstream modules to consume.

S01 establishes **discovery evidence**, not benchmark capability or scheduling authority.

## 2. Core concepts

- `DiscoverySessionRef`: one bounded discovery attempt under an exact probe registry/version.
- `HardwareSubjectRef`: opaque M07 subject reference for one physical/logical hardware unit or host-level resource domain.
- `RuntimeSubjectRef`: opaque reference for one host/container/VM/WSL/process runtime substrate.
- `DiscoveryObservation`: one typed fact plus source, timestamp, state and evidence reference.
- `DiscoverySnapshot`: immutable closure of observations admitted from one discovery session.
- `ProbeDescriptor`: versioned declaration of what an allowlisted probe observes and what side effects it is forbidden to perform.
- `ProbeEvidenceRef`: reference/digest for normalized evidence used to support an observation.
- `ObservationState`: explicit state lattice for positive and non-positive discovery.
- `DiscoveryConflict`: explicit disagreement between independent evidence sources.
- `FreshnessClass`: observation volatility class used to decide when later revalidation is required.
- `RuntimeSubstrate`: host OS/kernel/process architecture plus container/VM/WSL boundaries observable to the current process.
- `DeviceLocatorEvidence`: non-semantic, potentially ephemeral locator evidence such as PCI/LUID/IORegistry/OS-device handles.
- `PrivacyClass`: classification used to minimize serial numbers, host identifiers and other unnecessary identifying data.

S05 will own the final Hardware Genome schema/versioning/confidence contract. S01 defines the factual discovery inputs that schema must be able to represent.

## 3. Observation-state lattice

Required discovery states:

- `OBSERVED`: positive fact supported by admitted evidence;
- `NOT_PRESENT_PROVEN`: absence positively established within an explicitly bounded discovery scope;
- `UNKNOWN`: no sufficient evidence;
- `UNSUPPORTED_PROBE`: current platform/adapter cannot perform the probe;
- `PERMISSION_DENIED`: the environment blocked observation;
- `UNAVAILABLE`: subject/source existed but could not be queried at observation time;
- `CONFLICTING`: admitted sources disagree materially;
- `STALE`: evidence is outside its admitted freshness condition;
- `PARTIAL`: discovery completed only for a declared subset.

These states are not interchangeable. In particular, `UNKNOWN`, `UNSUPPORTED_PROBE`, `PERMISSION_DENIED`, `UNAVAILABLE` and `PARTIAL` never become `NOT_PRESENT_PROVEN`.

## 4. Probe registry and execution contract

Every discovery probe is allowlisted and versioned.

A `ProbeDescriptor` declares:
- probe ID/version;
- platform families supported;
- subject/fact families emitted;
- maximum duration;
- maximum output/evidence size;
- whether elevated privilege is required;
- expected volatility/freshness class;
- privacy classification;
- permitted native/system API surface;
- deterministic normalization version.

Normal discovery is read-only and side-effect-free. It must not:
- install drivers/packages;
- change clocks, power limits or device modes;
- allocate stress-sized GPU/RAM buffers;
- start benchmark workloads;
- write persistent configuration;
- scan unrelated user files;
- execute arbitrary payload-provided commands;
- invoke unrestricted shell strings.

Where an OS/runtime can only expose a fact through an external utility, a later implementation may use a narrowly allowlisted executable adapter with fixed argument schemas and bounded output. The command path/arguments become evidence. Arbitrary shell composition is prohibited.

## 5. GPU discovery

S01 GPU observations may include:

### Identity/topology evidence
- vendor/vendor ID;
- device/product ID;
- subsystem ID where available;
- architecture/family string as reported by an admitted source;
- discrete/integrated/virtual/partition classification;
- host-visible device index/locator evidence;
- PCI domain/bus/device/function when exposed;
- OS-native LUID/registry/IORegistry/DRM locator where applicable;
- partition/MIG/vGPU parent-child relationship when observable;
- display-attached versus compute-only role as an observation, not capability truth.

### Memory facts
- dedicated physical VRAM capacity where the platform exposes it;
- shared/system memory aperture separately;
- BAR/resizable-BAR facts where observable;
- unified-memory architecture classification where observable.

S01 does **not** treat `reported free VRAM` as static device capacity. Dynamic free/used/pressure values belong to S04 telemetry and later M09 resource-state reasoning.

A device with 8 GB VRAM, less than 8 GB, shared memory or CPU-only fallback remains discoverable. Capacity is not a pass/fail product classification.

## 6. CPU discovery

Candidate CPU observations:
- architecture/ISA family;
- vendor/family/model/stepping when available;
- physical package count;
- physical core count;
- logical processor count;
- efficiency/performance core topology when exposed;
- NUMA node topology;
- cache-level capacity/topology summaries;
- virtualization exposure;
- process architecture versus host architecture.

S01 may record **reported** instruction-set/capability flags as facts, but S02 owns the normalized compute/capability mapping used by downstream compatibility decisions.

Physical-core counts must not be silently guessed from logical count. Unknown topology stays unknown.

## 7. RAM discovery

Candidate static/semi-static facts:
- installed physical RAM;
- host-visible physical RAM;
- process-address-space constraints;
- page/swap configuration presence and declared capacity where observable;
- NUMA-affinity memory domains;
- unified-memory relationships that materially change the meaning of GPU memory.

Installed capacity, currently available memory, commit limits and pressure are separate facts. Dynamic availability/pressure belongs to S04.

## 8. Storage discovery

M07 may discover storage substrate facts relevant to later offload/placement decisions:
- mount/volume identity as an opaque runtime locator;
- total/available capacity observations;
- media/device class where reliably reported;
- filesystem type/capability facts;
- local/removable/network/virtual classification;
- path case-sensitivity or filesystem constraints when relevant;
- device topology relationships when exposed.

M07 does not allocate storage, select M55 tiers, perform CAS/dedup/GC, inspect user media content or turn a path into canonical production identity.

Free capacity is time-sensitive observation, not immutable storage capability.

## 9. Runtime substrate discovery

S01 records the substrate in which later probes are interpreted:
- OS family/version/build;
- kernel version;
- process architecture;
- Python/runtime version where IRIS executes;
- native versus emulated process;
- container boundary;
- VM/hypervisor exposure;
- WSL generation/distribution boundary;
- sandbox/restricted-environment indicators;
- host visibility limitations known to the current process.

A container/VM/WSL view is not automatically the same as physical-host truth. When host facts are hidden, M07 records scoped visibility rather than fabricating a complete host inventory.

## 10. Subject identity and locator separation

M07 hardware subject identity is operational and local to hardware discovery. It is never:
- M02 project/production identity;
- M05 Asset/Persona DNA;
- M06 materialization identity;
- a content digest;
- a model/provider identity.

Locators may change across boots, driver resets, hot-plug, VM/container remapping or device ordering.

Canonical S01 reasoning therefore separates:
- opaque subject reference;
- stable evidence anchors when legitimately exposed;
- ephemeral locators;
- human-readable labels.

Serial numbers and host-unique identifiers are not collected merely for convenience. Where a downstream requirement later proves one necessary, raw values require explicit privacy classification and should be minimized or transformed when possible.

## 11. Evidence anchoring

Every positive observation must be attributable to:
- exact probe ID/version;
- source adapter ID/version;
- observation timestamp;
- discovery-session ID;
- visibility scope;
- normalized fact schema/version;
- evidence reference/digest;
- subject reference;
- observation state.

Evidence digests prove which normalized observation payload was evaluated. They do not become hardware identity.

If two independent admitted sources materially disagree, S01 emits `DiscoveryConflict` and the affected fact becomes `CONFLICTING` until a later governed resolution rule applies. Source priority may be defined, but disagreement is never silently erased.

## 12. Snapshot and change semantics

A `DiscoverySnapshot` is immutable.

A later discovery creates a new snapshot when:
- hardware is added/removed;
- a device locator changes;
- runtime substrate changes;
- an observation changes;
- a probe/normalization version changes;
- prior evidence expires or becomes stale.

Hot-plug/removal never rewrites an earlier snapshot.

Snapshots carry a completeness declaration over their **bounded requested scope**. Completeness outside that scope is never implied.

## 13. Freshness classes

S01 needs at least these planning-level volatility classes:
- `BOOT_STABLE`: normally stable for the current boot/session;
- `INSTALL_STABLE`: stable until software/driver/runtime installation changes;
- `TOPOLOGY_STABLE`: stable until device/hardware topology changes;
- `DYNAMIC`: must be re-observed for runtime decisions;
- `UNKNOWN_VOLATILITY`: downstream consumers must fail closed when freshness is mandatory.

S05 will decide final schema/version/confidence rules. S04 owns the dynamic telemetry stream. S01 only ensures every discovered fact can declare the freshness semantics necessary for those later contracts.

## 14. Completeness and negative evidence

`NOT_PRESENT_PROVEN` requires:
- a declared discovery scope;
- an admitted probe capable of enumerating that scope;
- successful completion with no truncation/permission gap;
- source freshness sufficient for the claim.

Examples:
- “no NVIDIA adapter was enumerated by a complete NVIDIA/OS adapter probe” may support scoped absence;
- “probe binary missing” does not;
- “permission denied” does not;
- “container cannot see host GPUs” does not prove the host lacks GPUs.

## 15. Resource limits and defensive discovery

Later implementation must bound:
- number of enumerated subjects;
- observations per subject;
- evidence bytes;
- probe duration;
- nested topology depth;
- conflict fan-out;
- string/path lengths;
- repeated retry count.

Limit exhaustion produces explicit `PARTIAL` or `UNKNOWN` state and preserved frontier information. Truncation never masquerades as completeness.

## 16. 8 GB and heterogeneous-hardware rule

M07 is descriptive, not prescriptive.

An 8 GB VRAM-class GPU:
- is fully valid hardware;
- must expose the same discovery/evidence model as larger devices;
- must not be assigned a degraded quality class by M07;
- must remain eligible for later adaptive execution planning.

CPU-only, integrated-GPU, heterogeneous multi-GPU and mixed-vendor systems are representable without forcing one “primary GPU” as canonical truth.

Later M08-M10 may determine safe routes from evidence. M07 only provides trustworthy facts.

## 17. Downstream contract projections

S01 must remain able to project evidence toward:
- M06 `HardwareMaterialityEvidencePort` when a reconstruction contract explicitly declares a hardware/runtime fact material;
- M08 benchmark target selection;
- M09 Resource Digital Twin bootstrap;
- M10 workload-planning inputs;
- M12 worker capability advertisements;
- M14 empirical model compatibility evaluation;
- M56 observability.

These are references/evidence projections. M07 does not assume those downstream modules' internal schemas before their own planning.

## 18. S01 hard-invariant candidates

1. Hardware/runtime observations are evidence, not project, identity, quality, scheduling or execution authority.
2. M07 hardware subjects never become M02/M05/M06 semantic identities automatically.
3. S01 discovery cannot claim benchmark performance or safe workload limits.
4. S01 discovery cannot allocate VRAM/RAM leases or choose offload policy.
5. Every admitted observation records an exact observation time.
6. Every admitted observation binds an exact probe/source adapter version.
7. `UNKNOWN` cannot be coerced to `OBSERVED` or `NOT_PRESENT_PROVEN`.
8. `PERMISSION_DENIED`, `UNSUPPORTED_PROBE`, `UNAVAILABLE` and `PARTIAL` cannot prove absence.
9. Materially conflicting admitted sources remain explicit.
10. Hot-plug/removal creates new history instead of rewriting prior discovery snapshots.
11. Multiple GPUs/adapters remain separately addressable; device index zero is never canonical “the GPU.”
12. Dedicated VRAM and shared/system memory are distinct facts.
13. Installed memory and currently available memory are distinct facts.
14. Static capacity and dynamic pressure are distinct facts.
15. CPU physical/logical/NUMA topology cannot be silently inferred when unavailable.
16. Host architecture and current process architecture are distinct when emulation/translation exists.
17. Container/VM/WSL visibility cannot be treated automatically as complete physical-host truth.
18. Storage discovery does not transfer M55 physical-storage authority to M07.
19. Paths, labels, device indices and mutable locators are not canonical semantic identity.
20. Raw serial/host identifiers are not collected without a justified privacy-classified need.
21. Unsupported platform APIs fail explicitly rather than fabricating portable facts.
22. Probe timeout, truncation or resource-limit exhaustion cannot yield a complete snapshot.
23. Normal discovery probes are read-only and may not alter hardware/driver/runtime state.
24. Arbitrary shell strings or payload-directed commands are forbidden in discovery.
25. 8 GB VRAM-class hardware remains a first-class valid discovery subject.
26. Hardware scarcity cannot lower M01 quality targets or M03 semantic obligations.
27. Discovery snapshots are immutable and superseded only by new snapshots.
28. Evidence digests prove observation payloads and never become hardware identity.
29. M06 may treat hardware/runtime facts as reconstruction material only through explicit declared materiality.
30. HIVE, agents and UI clients may request/observe discovery but cannot fabricate admitted hardware facts.

These are S01 candidates until final M07 contract freeze.

## 19. Proprietary technology candidates

### IRIS-HDF — Hardware Discovery Fabric
Versioned multi-adapter discovery fabric that joins OS, vendor and runtime evidence while preserving source provenance, visibility scope and uncertainty instead of flattening everything into one hardware preset.

### IRIS-ODG — Opaque Device Graph
Topology model that keeps physical/logical/virtual/partition relationships explicit while separating stable evidence anchors, ephemeral locators and human labels from semantic identity.

### IRIS-NAF — Negative Assertion Firewall
Proof rule for “not present” hardware/runtime claims. Absence is admitted only after a complete capable probe over a declared scope; blocked, partial or unsupported probes remain uncertainty.

### IRIS-RSP — Runtime Substrate Passport
Immutable evidence capsule describing the exact host/process/container/VM/WSL substrate in which discovery occurred so downstream reproducibility and compatibility logic can interpret facts correctly.

### IRIS-DCF — Discovery Conflict Fabric
Cross-source disagreement surface that retains competing observations, source versions and reason codes instead of choosing a convenient winner silently.

All remain planning candidates pending Final Technology Review and prior-art review. Names do not imply novelty or patentability.

## 20. S01 acceptance-evidence targets

Later implementation must prove at minimum:
- deterministic normalized discovery serialization/fingerprints;
- source/probe provenance on every positive observation;
- NVIDIA/AMD/Intel/integrated/CPU-only fixture neutrality;
- 8 GB VRAM fixture remains a valid first-class device;
- multi-GPU and mixed-vendor enumeration does not collapse into one primary device;
- dedicated/shared/unified memory distinctions;
- physical versus logical CPU topology preservation;
- host versus process architecture separation;
- container/VM/WSL visibility scoping;
- permission-denied/unsupported/unavailable/partial states fail closed;
- positive proof requirement for bounded absence;
- conflict preservation across disagreeing evidence sources;
- hot-plug/removal creates new snapshots;
- privacy minimization for host/device identifiers;
- no arbitrary shell/dynamic execution in discovery adapters;
- resource-limit exhaustion yields partial/unknown rather than false completeness;
- M06 hardware-materiality projection remains explicit and does not change semantic identity;
- no quality downgrade, benchmark authority, scheduler authority or M55 storage-authority leakage.

## S01 STOP CONDITION

S01 is complete for module planning when:
- M07 observation authority and M08-M12/M14/M55/M56 firewalls are explicit;
- GPU/CPU/RAM/storage/runtime discovery surfaces are defined;
- uncertainty, scoped absence, conflict, freshness and partial discovery semantics are explicit;
- read-only/bounded/privacy-aware probe rules are defined;
- 8 GB and heterogeneous hardware remain first-class;
- downstream evidence projections are identified without designing future internals;
- 30 candidate hard invariants are recorded;
- five S01 proprietary technology candidates are registered for later review;
- planning may advance to M07 S02 capability mapping;
- no M07 product/runtime implementation is introduced.


# S02 — CUDA / ROCm / DirectML / Metal capability mapping

## 21. Goal

S02 converts raw S01 discovery facts into **versioned capability assertions with explicit evidence and scope**. A backend name, installed driver, shared library, environment variable or importable package is never sufficient by itself to prove end-to-end workload capability.

S02 remains descriptive. It answers “what interface/capability is evidenced here?” rather than “how fast is it?”, “how much can we allocate?”, or “which route should IRIS choose?”.

## 22. Capability evidence ladder

Capability assertions are stratified so downstream modules cannot mistake weak evidence for strong evidence:

- `DECLARED`: a trusted source reports the capability/version, but no runtime binding was observed;
- `LOADABLE`: the admitted runtime/API can be loaded or opened through a bounded non-stress probe;
- `DEVICE_BOUND`: the runtime/API can enumerate or bind the exact M07 hardware subject;
- `FEATURE_REPORTED`: the bound runtime reports an exact feature/limit/format/precision capability;
- `SMOKE_VERIFIED`: a narrowly bounded, non-benchmark conformance probe verifies that the feature is operational;
- `UNKNOWN`, `UNAVAILABLE`, `UNSUPPORTED`, `PERMISSION_DENIED`, `CONFLICTING`, `STALE`: explicit non-positive states.

Evidence strength is monotonic. `DECLARED` cannot be promoted to `SMOKE_VERIFIED` without new evidence.

A smoke probe is a conformance check only. It must be tiny, bounded and excluded from performance ranking. Throughput, latency, sustained memory limits, thermal stability and safe production envelopes remain M08+ concerns.

## 23. Capability subject and binding

Every capability assertion binds:
- exact M07 hardware subject;
- exact runtime substrate snapshot;
- backend family;
- backend/runtime/driver versions when observable;
- probe/source adapter version;
- capability key and normalized value;
- evidence-strength level;
- observation time/freshness;
- visibility scope;
- evidence reference/digest.

Capability evidence for device A cannot authorize device B. Evidence observed inside one container/VM/WSL/runtime scope cannot silently authorize another scope.

## 24. Backend-family neutrality

M07 must represent at least these backend families without making one canonical:

### NVIDIA / CUDA family
Candidate observations:
- driver/runtime API availability and reported versions;
- CUDA-visible device binding;
- compute capability/SM architecture as reported by admitted APIs;
- runtime/device feature flags and hard limits;
- library/runtime presence as separate facts;
- NVENC/NVDEC presence only as reported capability evidence, with detailed codec/session mapping deferred to S03.

### AMD / ROCm family
Candidate observations:
- ROCm/HIP runtime availability and versions;
- exact bound device/agent;
- reported GFX target/architecture;
- runtime/device feature flags and hard limits;
- relevant runtime libraries as separate facts;
- Linux/Windows/platform support state represented explicitly rather than assumed from vendor identity.

### Windows / DirectML family
Candidate observations:
- DirectML/DXGI/D3D runtime availability;
- adapter LUID binding to the exact M07 subject;
- reported feature levels/capability properties;
- dedicated/shared memory facts cross-checked against S01 identity evidence;
- software/WARP adapters kept distinguishable from hardware adapters.

### Apple / Metal family
Candidate observations:
- Metal device binding;
- registry/device relationship evidence where available;
- reported GPU family/feature support;
- unified-memory classification;
- Metal/runtime/OS version facts;
- capability evidence scoped to the exact observed Apple runtime substrate.

### Generic CPU / portable backends
CPU-only and portable execution surfaces remain representable. M07 does not require a discrete GPU or one of the four named vendor APIs to form a valid Hardware Genome.

Future backends may be added through versioned adapters without changing the semantic meaning of existing capability keys.

## 25. Version semantics

M07 records distinct version facts rather than one ambiguous “CUDA/ROCm/Metal version” string.

Candidate version dimensions:
- kernel/display/compute driver version;
- user-space runtime version;
- loader/API version;
- toolkit/SDK version when actually observable;
- library version;
- framework/backend binding version;
- OS runtime version;
- device firmware version where legitimately exposed and material.

Presence of a toolkit does not prove a compatible driver/device. A driver-reported maximum runtime level does not prove that a specific user-space toolkit/library is installed. A framework compiled for a backend does not prove that the current hardware/runtime can bind it.

Conflicting version sources remain explicit evidence conflicts until governed resolution.

## 26. Normalized capability vocabulary

S02 introduces a provider-neutral capability vocabulary with namespaced extensions.

Core capability families may include:
- `compute.api`;
- `compute.architecture`;
- `compute.queue_or_stream_model`;
- `compute.max_workgroup_or_block`;
- `compute.shared_or_local_memory`;
- `compute.atomic_features`;
- `compute.tensor_or_matrix_acceleration_reported`;
- `memory.dedicated`;
- `memory.unified`;
- `memory.host_visible`;
- `memory.peer_access_reported`;
- `precision.fp64`;
- `precision.fp32`;
- `precision.tf32`;
- `precision.fp16`;
- `precision.bf16`;
- `precision.fp8_family`;
- `precision.int8`;
- `precision.int4_family`;
- `interop.graphics_compute`;
- `interop.external_memory`;
- `interop.external_semaphore`.

A capability key states **what was evidenced**, not expected quality, speed, numerical suitability for a particular model, or scheduler preference.

Vendor-specific facts that do not yet have a safe normalized semantic live under versioned namespaces such as `nvidia.*`, `amd.*`, `directml.*`, `metal.*` instead of being forced into a misleading common field.

## 27. Precision capability semantics

Precision support is multidimensional. S02 must not collapse it into a boolean.

Where evidence exists, a precision assertion may distinguish:
- storage/representation support;
- arithmetic support;
- accelerated arithmetic reported;
- accumulation mode reported;
- conversion support;
- framework/backend exposure;
- smoke-verified execution.

Reported tensor/matrix acceleration is not benchmark proof and not model-quality proof.

S02 does not decide that FP16/BF16/FP8/INT8/INT4 is acceptable for a workload. M01 protects quality, M14 owns empirical model evidence, and M10 later chooses execution routes under those constraints.

## 28. Compatibility graph

M07 may represent an evidence-backed compatibility graph connecting:
- hardware subject;
- driver/runtime;
- backend API;
- feature/capability;
- runtime substrate.

Edges carry evidence strength and freshness.

The graph may prove:
- “this runtime bound this device and reported feature X”;
- “this backend cannot be observed in the current scope”;
- “these two evidence sources conflict”.

It may not prove:
- workload performance;
- production-safe VRAM headroom;
- model quality;
- preferred provider;
- scheduler placement;
- maximum sustainable concurrency.

## 29. Cross-source reconciliation

Where multiple adapters report the same normalized capability:
- exact agreement may increase evidence confidence later under S05;
- disagreement becomes `CONFLICTING`;
- source priority can select a presentation preference but cannot erase the disagreement;
- a weaker source cannot overwrite a stronger, fresher exact-subject observation;
- stale evidence cannot silently override current evidence.

Cross-vendor naming is normalized only when semantics are demonstrably equivalent. Similar marketing names are not sufficient.

## 30. Safe smoke verification

Optional `SMOKE_VERIFIED` evidence must:
- bind the exact subject/runtime/backend;
- use a fixed allowlisted conformance operation;
- have strict memory/time/output bounds;
- avoid stress, sustained load and performance scoring;
- avoid persistent cache/config mutation where practical;
- record failure state rather than retrying unboundedly;
- never be required merely to enumerate valid low-resource hardware.

Examples of acceptable planning intent include tiny device-open/buffer/copy/arithmetic conformance. Exact implementation remains deferred.

If a smoke check could materially heat, stress, allocate large memory, benchmark throughput or interfere with workstation use, it belongs outside S02.

## 31. 8 GB and low-resource compatibility

An 8 GB VRAM device can have rich capability evidence without being benchmarked or rejected.

S02 therefore separates:
- feature support;
- static memory capacity;
- runtime binding;
- empirical workload fit.

A backend with feature support but insufficient memory for a future workload remains a valid capability mapping. M08-M10 determine workload envelopes/routes later.

No capability map may encode “low VRAM = low quality.”

## 32. Multi-backend and multi-device systems

One physical device may expose multiple runtime paths. One host may expose multiple devices/vendors.

M07 must retain:
- one-to-many device→backend relationships;
- separate evidence per path;
- runtime-scope differences;
- software/emulated adapters;
- partitions/virtual devices;
- cross-device peer/interconnect facts only when explicitly evidenced.

“CUDA available on host” cannot be promoted into “all NVIDIA devices are CUDA-operational.” The same rule applies across ROCm, DirectML, Metal and portable backends.

## 33. Capability freshness and invalidation

Capability evidence may become stale after:
- driver/runtime/toolkit update;
- OS update;
- device reset/hot-plug;
- container/image change;
- VM/WSL boundary change;
- backend/framework update;
- topology/partition change.

S02 capability snapshots are immutable. Revalidation produces new evidence.

Downstream consumers requiring current capability must reject stale evidence according to the final S05 freshness/confidence contract.

## 34. Security and privacy

Capability probes inherit S01's read-only, allowlisted, bounded execution rules.

Additionally:
- library search paths are treated as untrusted input;
- discovery must not load arbitrary project-local binaries merely because they match a runtime filename;
- environment variables are observations, not trusted executable instructions;
- untrusted plugin/model/DCC content cannot register privileged hardware probes;
- raw device identifiers remain privacy-minimized;
- driver/runtime errors are normalized without leaking unnecessary host secrets.

M54 remains the security authority; M07 exposes evidence needed for policy decisions.

## 35. S02 hard-invariant candidates

31. Backend/package presence alone cannot prove operational device capability.
32. Capability evidence is exact-subject bound.
33. Capability evidence is exact-runtime-scope bound.
34. Evidence strength cannot increase without new evidence.
35. Smoke verification cannot be treated as a benchmark.
36. M07 cannot convert capability evidence into scheduler preference.
37. M07 cannot convert capability evidence into workload-safe memory limits.
38. Driver version, runtime version, toolkit version and library version remain distinct facts.
39. A driver-reported compatibility level does not prove a matching toolkit/library installation.
40. Framework backend availability does not prove device binding.
41. Vendor identity does not prove backend availability.
42. Software/emulated adapters remain distinguishable from physical hardware adapters.
43. CUDA/ROCm/DirectML/Metal are peer backend families in the M07 schema, not a priority order.
44. CPU-only/portable backends remain valid capability subjects.
45. Precision support cannot be represented safely as one undifferentiated boolean.
46. Reported acceleration is not empirical performance proof.
47. Precision capability cannot authorize a quality downgrade.
48. Vendor marketing names cannot establish normalized semantic equivalence.
49. Conflicting normalized capability evidence remains explicit.
50. A weaker/staler source cannot silently overwrite stronger/fresher exact-subject evidence.
51. One device may expose multiple backend paths without identity collapse.
52. Host-level backend presence cannot be broadcast to every device.
53. Cross-device peer/interconnect support requires explicit exact-pair evidence.
54. Capability snapshots are immutable.
55. Driver/runtime/topology changes can invalidate capability freshness.
56. Untrusted library paths cannot become privileged discovery execution.
57. Environment variables are evidence, not commands.
58. Optional conformance probes must be bounded and non-stress.
59. 8 GB VRAM-class hardware cannot be rejected solely because a later workload may exceed capacity.
60. Capability mapping cannot claim M08 benchmark envelopes, M09 resource policy, M10 execution plans or M14 empirical model fitness.

These remain candidates until final M07 contract freeze.

## 36. Proprietary technology candidates

### IRIS-CEL — Capability Evidence Ladder
Typed evidence-strength model separating declaration, loadability, exact-device binding, reported features and bounded smoke verification so downstream modules cannot accidentally upgrade weak evidence.

### IRIS-BRM — Backend Relationship Matrix
Provider-neutral one-to-many graph connecting devices, runtime substrates and CUDA/ROCm/DirectML/Metal/portable paths without inventing a single preferred backend.

### IRIS-PDM — Precision Dimensional Matrix
Capability model that separates representation, arithmetic, acceleration, accumulation, conversion, backend exposure and smoke verification for each precision family.

### IRIS-VSF — Version Separation Fabric
Explicit version topology for driver, runtime, toolkit, library, framework binding and OS substrate, preventing ambiguous “backend version” claims.

### IRIS-CCG — Capability Conflict Graph
Evidence-preserving reconciliation layer for normalized capability disagreements across OS, vendor and framework/runtime sources.

All remain planning candidates pending Final Technology Review and prior-art review.

## 37. S02 acceptance-evidence targets

Later implementation must prove at minimum:
- exact-subject and exact-runtime binding for every positive capability assertion;
- declared/loadable/device-bound/feature-reported/smoke-verified evidence levels remain distinct;
- driver/runtime/toolkit/library/framework versions do not collapse;
- CUDA, ROCm, DirectML, Metal and CPU/portable fixtures share one provider-neutral semantic model;
- software/emulated adapters remain explicit;
- multi-device hosts do not receive host-wide capability broadcast;
- one device can retain multiple backend paths;
- precision support is multidimensional;
- conflict preservation across independent sources;
- stale evidence invalidates current-capability claims;
- optional smoke probes remain bounded and excluded from benchmark results;
- malicious/untrusted library paths or environment values cannot become arbitrary execution;
- 8 GB hardware remains valid without benchmark or quality downgrade;
- M08/M09/M10/M14 authority remains external.

## S02 STOP CONDITION

S02 is complete for module planning when:
- capability evidence strength and exact subject/runtime binding are explicit;
- CUDA/ROCm/DirectML/Metal/portable backend mappings are provider-neutral;
- version dimensions are separated;
- precision capability semantics are multidimensional;
- cross-source conflicts and freshness invalidation are explicit;
- smoke verification is bounded and cannot become benchmarking;
- 30 additional hard-invariant candidates are recorded (60 cumulative);
- five additional proprietary technology candidates are registered (10 cumulative);
- planning may advance to M07 S03 driver/precision/encoder/decoder/topology detection;
- no M07 product/runtime implementation is introduced.


# S03 — Driver, precision, encoder/decoder and topology detection

## 38. Goal

S03 defines the evidence model for driver/runtime compatibility surfaces, numerical precision features, hardware media engines and device/interconnect topology.

It remains a discovery layer. It does not:
- benchmark codecs or compute;
- claim production-safe throughput/concurrency;
- select a codec/model/backend for a job;
- allocate resources;
- schedule across devices;
- infer quality from hardware features.

## 39. Driver and runtime compatibility evidence

Driver state is represented as a set of facts, not one “driver OK” boolean.

Candidate facts include:
- vendor/provider;
- driver package/version/build;
- kernel-mode versus user-mode components where observable;
- loaded/active state;
- runtime/API compatibility level as reported by an admitted source;
- device binding;
- restart/reboot-required state when reliably exposed;
- signature/trust metadata where an authoritative platform API exposes it;
- known visibility limitations of the current container/VM/WSL/process scope.

M07 may report compatibility relationships evidenced by authoritative APIs. It cannot claim that a future framework/model/workflow will run successfully unless the relevant evidence contract actually proves that narrower claim.

A newer version number is not automatically “better,” compatible, stable or preferred.

## 40. Driver/runtime skew

M07 must preserve skew explicitly:
- kernel driver versus user-space runtime;
- host driver versus container runtime;
- host GPU exposure versus VM/WSL guest runtime;
- framework-bundled runtime versus system runtime;
- multiple installed runtime/toolkit versions;
- active runtime versus merely installed artifacts.

Skew can produce `COMPATIBLE_REPORTED`, `INCOMPATIBLE_REPORTED`, `UNKNOWN`, `CONFLICTING` or other versioned states. It is not silently repaired by choosing the highest version string.

## 41. Precision detection

S03 deepens S02 precision evidence into exact feature dimensions.

Candidate dimensions per precision family:
- storage/representation;
- scalar arithmetic;
- vector/SIMD arithmetic;
- tensor/matrix acceleration reported;
- accumulation precision/modes;
- denormal/subnormal behavior where authoritatively reported;
- rounding/control modes where relevant;
- atomic support;
- conversion paths;
- framework/backend exposure;
- bounded conformance evidence.

Supported families may include:
- FP64;
- FP32;
- TF32-like modes;
- FP16;
- BF16;
- FP8 families as distinct encodings where necessary;
- INT64/INT32/INT16/INT8;
- INT4/sub-byte families where semantics are explicit.

Marketing labels never substitute for exact precision semantics.

M07 does not decide whether reduced precision preserves perceptual/model quality. That remains governed by M01/M14 and later execution planning.

## 42. Media engine discovery

Hardware encode/decode is represented per exact device and engine/API path.

Candidate evidence:
- engine/API family;
- codec;
- encode versus decode;
- profile;
- level/tier where exposed;
- bit depth;
- chroma format;
- resolution/dimension limits as **reported static limits**;
- pixel/input/output format;
- rate-control modes as reported features;
- B-frame/reference-frame feature presence where exposed;
- HDR metadata path support where exposed;
- alpha support where exposed;
- interop path with compute/graphics memory where evidenced.

Codec families may include H.264/AVC, H.265/HEVC, AV1, VP9, ProRes or future codecs only when an admitted backend exposes them.

“Codec supported” must never be a single host-wide boolean.

## 43. Encoder/decoder evidence strength

Media capabilities use the same evidence ladder principles:
- declared/reported;
- engine/device bound;
- feature reported;
- bounded conformance verified.

A tiny bounded encode/decode conformance operation may prove basic operation but cannot establish:
- real-time performance;
- sustained 4K/8K throughput;
- concurrent-session count;
- quality at a bitrate;
- thermal stability;
- production-safe queue depth.

Those belong to M08 benchmarking/capability envelopes and later planning.

## 44. Session/concurrency limits

Vendor/API-reported static session limits may be recorded as reported facts when authoritative and version-bound.

M07 must not convert:
- marketing documentation;
- historical product tables;
- license folklore;
- one successful session;
- current idle-engine count

into a production-safe concurrency envelope.

Dynamic/sustainable concurrency requires M08 evidence.

## 45. Device topology graph

S03 extends the S01 Opaque Device Graph with topology evidence.

Candidate nodes:
- host;
- CPU package;
- NUMA node;
- GPU/accelerator;
- GPU partition/MIG/vGPU;
- memory domain;
- PCIe root/bridge/device;
- storage device/volume;
- media engine when separately addressable;
- runtime-visible logical adapter.

Candidate edges:
- attached-to;
- parent/child partition;
- NUMA-local-to;
- shares-memory-with;
- peer-access-reported-with;
- interconnect-reported-with;
- routed-through;
- exposed-as/logical-view-of.

Every topology edge is evidence-bound and directional where semantics require it.

## 46. PCIe/interconnect evidence

Candidate static/reported observations:
- PCIe generation capability;
- negotiated link generation;
- lane width capability;
- negotiated lane width;
- resizable BAR state;
- peer-access capability;
- NVLink/Infinity Fabric or other vendor interconnect presence where authoritatively exposed;
- NUMA locality;
- integrated/unified-memory relationship.

The distinction between **maximum capability** and **currently negotiated state** is mandatory.

Reported link width/speed is not measured transfer bandwidth. Measured bandwidth belongs to M08.

## 47. Peer relationships

Peer capability is exact-pair evidence.

For devices A and B:
- A→B and B→A may differ;
- runtime/backend path matters;
- topology visibility scope matters;
- partition/virtualization boundaries matter.

A host with two compatible-looking GPUs does not automatically have peer access.

M07 may record a peer relationship but cannot choose multi-GPU placement or sharding. M12/M10 own those decisions.

## 48. Unified and shared memory topology

S03 must represent:
- physically unified CPU/GPU memory architectures;
- discrete VRAM plus host RAM;
- shared-memory apertures;
- BAR mappings;
- runtime-managed unified/managed memory capabilities;
- device-local versus host-visible memory facts.

These concepts are not collapsed into one “shared memory” field.

Static topology does not imply safe oversubscription or spill policy. M09 owns resource governance.

## 49. Virtualization and partitioning

Topology must retain:
- VM/guest-visible logical devices;
- mediated/vGPU devices;
- GPU partitions such as MIG-like instances;
- host physical parent when legitimately observable;
- partition-local memory/capability;
- hidden parent state when the guest lacks authority.

A partition is not silently treated as the full physical GPU.

A guest-visible device can be a complete valid M07 subject even when physical-host topology is unknown.

## 50. Media/compute interop

S03 may record reported interop capabilities such as:
- zero-copy/shared surfaces;
- external memory;
- external semaphore/synchronization;
- graphics-compute interop;
- media-compute surface sharing.

Interop evidence must bind both relevant APIs/backends and the exact subject/runtime scope.

Presence of interop support does not prove that a specific future DCC/provider/workflow integration is implemented.

## 51. Precision/media/topology conflict handling

Examples of material conflicts:
- OS reports one driver version while vendor API reports another active component;
- framework reports BF16 while device API does not expose compatible arithmetic;
- one API reports AV1 encode and another denies it for the same exact device/runtime;
- topology sources disagree on partition parent or NUMA locality.

Conflicts remain explicit and scoped. A presentation layer may show a preferred source, but admitted truth retains the disagreement and evidence.

## 52. Change invalidation

S03 evidence can become stale after:
- driver install/update/rollback;
- OS/kernel update;
- runtime/framework update;
- device reset;
- hot-plug;
- BIOS/firmware/topology change;
- VM/container/WSL image/config change;
- GPU partition/reconfiguration;
- display/compute mode change.

A new snapshot supersedes old current-state claims without rewriting history.

## 53. Security and boundedness

Driver/media/topology discovery must not:
- install/repair drivers;
- flash firmware;
- alter clocks/power/device modes;
- create large media files;
- decode untrusted arbitrary media merely to discover codec support;
- enumerate unrelated user content;
- execute vendor tools through unbounded shell strings;
- follow attacker-controlled library/tool paths.

Any conformance media payload used later must be fixed, tiny, synthetic, bounded and treated as test data.

## 54. S03 hard-invariant candidates

61. Driver state cannot collapse into one undifferentiated “OK” boolean.
62. Higher driver/runtime version cannot be assumed preferable or compatible.
63. Host/container/guest/framework runtime skew remains explicit.
64. Installed artifacts cannot prove the active runtime path.
65. Driver compatibility evidence must bind an exact subject/runtime scope.
66. Precision marketing labels cannot replace exact semantic dimensions.
67. FP8/sub-byte families remain encoding-specific when semantics differ.
68. Reported precision acceleration cannot prove workload quality.
69. Reduced precision support cannot authorize silent quality downgrade.
70. Codec support is exact device/engine/API/path evidence, not host-wide truth.
71. Encode and decode capabilities remain distinct.
72. Codec profile/level/bit-depth/chroma features remain explicit where material.
73. A successful bounded codec smoke check cannot prove real-time throughput.
74. Static reported codec limits cannot prove sustainable production envelopes.
75. One successful media session cannot prove concurrency capacity.
76. Marketing/session folklore cannot become admitted concurrency evidence.
77. Device topology edges require evidence.
78. PCIe maximum capability and negotiated state remain distinct.
79. Negotiated PCIe state cannot be represented as measured bandwidth.
80. Peer capability is exact-pair and direction-aware evidence.
81. Multiple GPUs do not imply peer access.
82. M07 topology cannot choose sharding, placement or scheduler policy.
83. Unified physical memory, shared aperture and managed/unified runtime memory remain distinct.
84. Static memory topology cannot authorize oversubscription/offload.
85. Virtual/partitioned devices remain distinct from physical parents.
86. Hidden physical parent state remains unknown rather than inferred.
87. Guest-visible hardware remains valid even when host topology is unavailable.
88. Media/compute interop evidence binds exact APIs and subject/runtime scope.
89. Interop capability cannot prove a future provider/DCC integration exists.
90. Driver/precision/media/topology conflicts remain explicit until governed resolution.
91. Driver/topology/runtime changes invalidate affected current-state evidence.
92. Discovery cannot mutate driver, firmware, clocks, power or device modes.
93. Codec discovery cannot require arbitrary untrusted media input.
94. Conformance media fixtures must be fixed, synthetic and bounded.
95. Raw vendor-tool output cannot bypass normalized evidence contracts.
96. M07 cannot convert topology into M08 performance claims.
97. M07 cannot convert topology into M09 resource policy.
98. M07 cannot convert topology into M10/M12 execution placement.
99. 8 GB hardware retains full precision/media/topology representation without categorical downgrade.
100. HIVE/UI/agents may consume S03 evidence but cannot manufacture or override admitted hardware truth.

These remain candidates until final M07 contract freeze.

## 55. Proprietary technology candidates

### IRIS-DSG — Driver Skew Graph
Versioned graph of kernel, host, container, guest, runtime, toolkit and framework components that exposes active-path skew instead of reducing compatibility to one version string.

### IRIS-PFX — Precision Feature Lattice
Evidence lattice for exact precision semantics across storage, arithmetic, acceleration, accumulation, conversion and conformance, preventing unsafe boolean capability claims.

### IRIS-MEC — Media Engine Capability Matrix
Exact-device codec/engine/profile/bit-depth/chroma/interop evidence model that cleanly separates reported static limits, bounded conformance and later empirical throughput.

### IRIS-TGE — Topology Graph Evidence
Evidence-bound graph for CPU/NUMA/GPU/partition/PCIe/interconnect/memory relationships, with explicit distinction between physical, logical and runtime-visible topology.

### IRIS-P2P — Pairwise Path Proof
Directional exact-pair evidence contract for peer access/interconnect/interop paths so multi-device systems cannot inherit host-wide assumptions.

All remain planning candidates pending Final Technology Review and prior-art review.

## 56. S03 acceptance-evidence targets

Later implementation must prove at minimum:
- host/container/guest/framework driver-runtime skew is preserved;
- active versus merely installed runtime components remain distinct;
- precision semantics remain dimensional and encoding-aware;
- reduced precision never authorizes quality downgrade;
- codec encode/decode/profile/bit-depth/chroma evidence remains exact-device/path scoped;
- bounded codec conformance cannot become throughput/concurrency proof;
- PCIe maximum versus negotiated state remains distinct;
- negotiated link state cannot masquerade as measured bandwidth;
- pairwise peer relationships remain exact and directional;
- unified/shared/managed memory concepts remain distinct;
- partitions/virtual devices remain separate from physical parents;
- hidden host topology stays unknown;
- media-compute interop remains exact-path evidence;
- conflicts remain explicit;
- no driver/firmware/power/clock mutation;
- no arbitrary media or shell execution;
- 8 GB and heterogeneous systems remain fully representable;
- M08/M09/M10/M12 authority remains external.

## S03 STOP CONDITION

S03 is complete for module planning when:
- driver/runtime skew and compatibility evidence are explicit;
- precision feature semantics are exact and quality-neutral;
- encoder/decoder evidence is exact-device/path scoped and separated from empirical throughput;
- topology/interconnect/peer/unified-memory semantics are evidence-bound;
- virtualization/partitioning and hidden-host uncertainty are explicit;
- 40 additional hard-invariant candidates are recorded (100 cumulative);
- five additional proprietary technology candidates are registered (15 cumulative);
- planning may advance to M07 S04 thermal, power and memory-pressure telemetry;
- no M07 product/runtime implementation is introduced.


# S04 — Thermal, power and memory-pressure telemetry

## 57. Goal

S04 defines bounded, read-only telemetry evidence for dynamic hardware state:
- temperature;
- power;
- clocks and throttling indicators;
- utilization;
- device and host memory pressure;
- selected health/availability signals.

S04 observes. It does not tune clocks, power limits, fan curves, process priority, memory policy, scheduler placement, workload concurrency or quality.

Dynamic telemetry is explicitly separated from the relatively static discovery/capability facts of S01-S03.

## 58. Telemetry sample model

A telemetry observation binds:
- exact HardwareSubjectRef;
- exact RuntimeSubjectRef when runtime visibility matters;
- metric key;
- value and unit;
- source/probe;
- monotonic capture sequence;
- wall-clock timestamp when available;
- sampling window or instantaneous semantics;
- freshness/expiry;
- evidence digest;
- visibility scope;
- source confidence/status.

A sample without subject, unit or time semantics cannot become admitted telemetry truth.

## 59. Metric semantic classes

Metrics are classified before interpretation:
- instantaneous gauge;
- cumulative counter;
- monotonic counter;
- bounded percentage/rate;
- reported limit;
- current configured limit;
- event/flag;
- derived value.

Counters are not treated as rates without a valid interval.
Reported maximums are not current values.
Configured limits are not measured consumption.

## 60. Temperature evidence

Candidate temperature facts include:
- GPU core/device temperature;
- hotspot/junction temperature;
- memory temperature where exposed;
- CPU package/core temperature;
- storage temperature where safely available;
- platform thermal-zone readings.

Temperature sensors remain individually identified where semantics differ.

M07 must not fabricate a single “system temperature” by averaging unrelated sensors.

Missing hotspot/memory sensors remain unavailable/unsupported, not zero.

## 61. Thermal limits and throttling

Authoritatively reported thermal limits/targets may be recorded separately from current temperature.

Throttling evidence can include:
- thermal throttle active/reason;
- power-limit throttle active/reason;
- reliability/voltage/current limit reasons;
- clock-cap reasons;
- platform thermal-pressure states.

A lower observed clock alone cannot prove throttling cause.

M07 reports the evidence. M10 later decides whether execution should adapt.

## 62. Power evidence

Candidate power facts:
- instantaneous device/package power;
- energy counters;
- reported/default/configured power limits;
- board/package power where semantically distinct;
- battery/AC/platform power state when relevant to execution context.

Power units and measurement domains remain explicit.

An energy counter delta may derive average power only when timestamps and counter semantics are valid.

M07 cannot change a power limit.

## 63. Clock telemetry

Candidate clock domains:
- GPU graphics/core;
- GPU memory;
- GPU video/media;
- CPU effective/core;
- fabric/interconnect where exposed.

Current clock, requested clock, base/default clock, boost limit and maximum reported capability remain separate.

Clock telemetry is not a benchmark.

## 64. Utilization telemetry

Utilization can include:
- GPU compute/graphics utilization;
- media encode/decode utilization;
- memory-controller utilization;
- CPU utilization;
- storage I/O utilization where relevant.

A utilization percentage must preserve source semantics and sampling window.

Different vendor/API utilization metrics are not assumed numerically equivalent merely because both use percent.

## 65. Device-memory telemetry

Dynamic memory evidence may include:
- total visible device memory;
- currently used;
- currently free/available as reported;
- reserved;
- committed;
- process-local allocation where legitimately visible;
- shared/host-visible allocation where semantically exposed;
- eviction/page-fault/pressure indicators where exposed.

S04 dynamic memory telemetry does not supersede S01/S03 static topology/capacity facts.

“Free VRAM” is a transient observation, not a safe allocation budget.

## 66. Host-memory pressure

Candidate host evidence:
- physical RAM total/available;
- committed memory and commit limit;
- swap/pagefile capacity and use;
- memory pressure state;
- major paging/fault signals where supported;
- cgroup/container memory limit/current use;
- VM/guest-visible memory limits.

Host “free memory” and “available memory” remain distinct where the platform exposes both.

Container/guest limits override assumptions based on physical host capacity for that runtime scope.

## 67. Memory-pressure semantics

Pressure is represented as evidence, not inferred from one arbitrary threshold.

Candidate states:
- NORMAL_REPORTED;
- PRESSURE_REPORTED;
- CRITICAL_REPORTED;
- UNKNOWN;
- UNAVAILABLE;
- CONFLICTING;
- STALE.

Derived pressure classification is allowed only when a versioned M07 derivation rule explicitly identifies inputs, units, thresholds and scope. Such a classification remains M07 evidence, not an execution-policy decision.

## 68. Process visibility and privacy

Process-level telemetry is optional and least-privilege.

M07 should prefer aggregate device/runtime evidence when sufficient.

If process attribution is necessary, retained facts should minimize identity:
- opaque process/workload reference;
- resource quantity;
- scope;
- timestamp.

Command lines, environment contents, user document paths and unrelated process metadata are not hardware telemetry.

## 69. Sampling discipline

Sampling must be bounded and configurable by contract.

The design must define:
- minimum supported interval;
- maximum frequency;
- maximum sample count/window;
- timeout;
- jitter/timestamp semantics;
- backpressure/drop behavior.

No busy-loop polling.

A telemetry consumer cannot silently force privileged or high-frequency sampling.

## 70. Observation windows

S04 distinguishes:
- single snapshot;
- bounded short window;
- historical series reference.

M07 can create bounded evidence windows for discovery/validation.

Long-term retention, aggregation, dashboarding and observability pipelines belong to M56 and storage/retention governance.

## 71. Derived telemetry

Allowed derived examples:
- energy-counter delta to average power;
- used/total ratio;
- bounded temperature delta;
- clock ratio to an explicitly identified reference;
- rate from a monotonic counter.

Every derived metric binds:
- source sample IDs;
- derivation rule/version;
- units;
- interval;
- validity conditions.

Derived telemetry never erases raw evidence.

## 72. Missing and impossible values

Telemetry parsers must reject or explicitly classify:
- NaN/Infinity when semantically invalid;
- negative memory or impossible percentages;
- unitless values when units are required;
- counter regressions unless reset/wrap semantics explain them;
- timestamps outside admitted ordering bounds;
- stale samples represented as current;
- sentinel values misread as real measurements.

Zero is a valid value only when the source contract says zero is meaningful.

## 73. Sensor identity and reconciliation

Multiple sources may expose apparently similar sensors.

Reconciliation requires semantic identity evidence, not just similar labels.

Examples:
- GPU “temperature” versus hotspot;
- CPU package versus per-core;
- board power versus chip power;
- committed versus resident memory.

Conflicting sources remain visible and evidence-bound.

## 74. Telemetry freshness

Dynamic telemetry has shorter freshness than hardware identity/capability facts.

Freshness can be metric-class specific.

Consumers must be able to determine:
- capture time/window;
- expiration;
- whether the subject/runtime changed since capture;
- whether the sampling source remained available.

A stale sample cannot authorize a current-state claim.

## 75. Event-driven invalidation

Telemetry windows terminate or become non-current when material context changes, including:
- device reset/removal;
- runtime restart when scope-bound;
- suspend/resume when metric semantics require it;
- driver reset/update;
- partition reconfiguration;
- VM/container boundary change;
- telemetry source failure;
- monotonic clock discontinuity relevant to interval math.

Historical evidence remains immutable.

## 76. Safety boundaries

S04 probes must be observational.

They cannot:
- set fan speed;
- change voltage;
- overclock/underclock;
- change power caps;
- toggle performance modes;
- kill/suspend processes;
- evict allocations;
- clear caches;
- force garbage collection in unrelated runtimes;
- allocate large buffers to “measure pressure”;
- run stress workloads.

Any active microbenchmark or stress-based characterization belongs to M08 under its own bounded contract.

## 77. 8 GB and constrained systems

An 8 GB VRAM device is not classified as deficient merely because transient free memory is low.

S04 reports:
- capacity/topology references;
- current dynamic usage;
- pressure evidence;
- freshness.

Later modules may use that evidence to plan execution without silently lowering canonical quality.

## 78. Multi-device telemetry

Telemetry is exact-device scoped.

For multi-GPU systems:
- each device has independent metrics;
- shared rails/sensors remain explicitly shared;
- aggregate values require an explicit derivation;
- one hot/pressured device cannot silently contaminate another device’s state;
- pair/interconnect telemetry, when available, remains pair scoped.

## 79. Heterogeneous metric vocabulary

Provider-neutral metric keys define semantic intent, while source-specific extensions preserve vendor detail.

Normalization cannot erase:
- different sensor domains;
- different averaging windows;
- different utilization definitions;
- different power domains;
- different memory accounting semantics.

Cross-vendor comparability must be declared only where semantics genuinely align.

## 80. S04 hard-invariant candidates

101. Dynamic telemetry remains distinct from static hardware/capability facts.
102. Every admitted sample binds exact subject, metric, unit and time semantics.
103. Counters cannot become rates without a valid interval.
104. Reported limits cannot masquerade as current measurements.
105. Configured limits cannot masquerade as consumption.
106. Distinct thermal sensors cannot be silently averaged into “system temperature.”
107. Missing sensors cannot become zero.
108. Lower clocks alone cannot prove throttling cause.
109. Throttling reasons remain evidence-bound.
110. Power measurement domains and units remain explicit.
111. Energy-derived power requires valid counter and interval semantics.
112. M07 cannot mutate power limits.
113. Current/requested/base/boost/max clocks remain distinct.
114. Clock telemetry cannot become benchmark evidence.
115. Utilization metrics retain source sampling semantics.
116. Same-unit vendor metrics cannot be assumed semantically equivalent.
117. Dynamic free VRAM cannot become a safe allocation budget.
118. Device-memory telemetry cannot overwrite static capacity/topology truth.
119. Host free and available memory remain distinct where supported.
120. Container/guest memory limits remain authoritative for their runtime scope.
121. Memory pressure cannot be inferred from an undocumented arbitrary threshold.
122. Derived pressure states require a versioned derivation rule.
123. Pressure evidence cannot directly become execution policy.
124. Process telemetry follows least privilege and identity minimization.
125. Hardware telemetry cannot retain unrelated command lines/environment/user paths.
126. Sampling frequency and window are bounded.
127. Busy-loop telemetry polling is prohibited.
128. Consumers cannot silently escalate telemetry privilege/frequency.
129. M07 telemetry windows remain bounded; long-term observability belongs to M56.
130. Derived telemetry binds source samples and derivation version.
131. Derived telemetry cannot erase raw evidence.
132. Invalid NaN/Infinity/impossible values cannot enter admitted truth.
133. Unit-required metrics cannot be admitted unitless.
134. Counter reset/wrap/regression semantics must be explicit.
135. Stale samples cannot represent current state.
136. Zero is accepted only when source semantics make zero meaningful.
137. Sensor reconciliation requires semantic identity evidence.
138. Conflicting sensors/sources remain explicit.
139. Telemetry freshness may vary by metric class.
140. Material subject/runtime/source changes invalidate current telemetry windows.
141. Historical telemetry evidence remains immutable after invalidation.
142. S04 probes cannot tune fans, voltage, clocks, power or performance modes.
143. S04 probes cannot kill/suspend processes or evict unrelated allocations.
144. S04 cannot allocate large buffers or stress hardware to infer pressure.
145. Active performance characterization remains M08 authority.
146. Low transient free VRAM cannot classify an 8 GB device as categorically deficient.
147. Quality cannot be silently lowered from pressure telemetry.
148. Multi-device telemetry remains exact-device scoped.
149. Shared sensor/rail values remain explicitly shared rather than duplicated as device-local truth.
150. Cross-vendor normalization cannot erase materially different metric semantics.

These remain candidates until final M07 contract freeze.

## 81. Proprietary technology candidates

### IRIS-TSL — Telemetry Semantics Ledger
Versioned registry of metric meaning, unit, source window, freshness and validity rules, preventing same-name/same-unit metrics from becoming false equivalents.

### IRIS-MPF — Memory Pressure Fabric
Evidence model combining device, host and runtime-scope memory observations without turning transient “free memory” into allocation policy.

### IRIS-TCR — Thermal Causality Resolver
Conflict-aware representation of temperatures, clocks and authoritative throttle reasons that prevents low-clock observations from inventing thermal causality.

### IRIS-EDE — Evidence Derivation Engine
Deterministic versioned derivation layer that produces ratios, rates and bounded classifications while retaining exact source-sample lineage.

### IRIS-SWG — Sampling Window Governor
Contract-level governor for frequency, duration, privilege, backpressure and invalidation of telemetry sampling, designed to keep discovery bounded and non-invasive.

All remain planning candidates pending Final Technology Review and prior-art review.

## 82. S04 acceptance-evidence targets

Later implementation must prove at minimum:
- telemetry samples require exact subject/unit/time semantics;
- static discovery and dynamic telemetry remain separate;
- temperature sensors preserve distinct semantics;
- missing sensors never become zero;
- throttling causes require authoritative evidence;
- power/energy domains and derivations are explicit;
- clock classes remain distinct;
- utilization preserves source window semantics;
- transient free VRAM never becomes allocation budget;
- host/container/guest memory scopes remain explicit;
- pressure derivations are versioned and non-prescriptive;
- process metadata is minimized;
- sampling is bounded and cannot busy-loop;
- derived telemetry retains source lineage;
- invalid/sentinel/stale values fail closed;
- sensor conflicts remain explicit;
- telemetry windows invalidate on material context change;
- probes cannot mutate clocks/power/fans/processes/memory state;
- stress/benchmark behavior remains outside S04;
- 8 GB systems remain first-class;
- multi-device and shared-sensor semantics remain exact;
- M08/M09/M10/M56 authority remains external.

## S04 STOP CONDITION

S04 is complete for module planning when:
- thermal, power, clocks, utilization and memory-pressure telemetry semantics are explicit;
- samples, windows, freshness, derivations and invalidation are evidence-bound;
- observation is non-invasive and bounded;
- pressure telemetry remains separate from allocation/execution policy;
- 50 additional hard-invariant candidates are recorded (150 cumulative);
- five additional proprietary technology candidates are registered (20 cumulative);
- planning may advance to M07 S05 Hardware Genome schema, versioning and confidence;
- no M07 product/runtime implementation is introduced.


# S05 — Hardware Genome schema, versioning and confidence

## 83. Goal

S05 defines the canonical Hardware Genome representation that packages admitted M07 discovery evidence without erasing provenance, uncertainty, conflicts, visibility scope or freshness.

The Hardware Genome is an evidence product, not a scheduler profile, benchmark score, hardware ranking or optimization policy.

## 84. Genome identity

Every canonical genome binds:
- GenomeId;
- schema identifier and semantic version;
- exact discovery snapshot/session lineage;
- HardwareSubjectRef set;
- RuntimeSubjectRef set;
- capture interval;
- producer implementation/version;
- admitted probe-set version;
- evidence-root digest;
- creation timestamp;
- current/historical status.

Genome identity is content/evidence anchored. A mutable display name cannot identify canonical hardware truth.

## 85. Canonical sections

The schema may contain versioned sections for:
- host/runtime substrate;
- CPU;
- memory;
- GPU/accelerators;
- storage visibility facts;
- backend/runtime capability assertions;
- driver/runtime relationships;
- precision capabilities;
- media engines;
- topology/interconnect;
- bounded dynamic telemetry references;
- conflicts;
- unknown/unavailable facts;
- provenance/evidence references;
- confidence descriptors;
- extensions.

Sections are independently evolvable under compatibility rules.

## 86. Fact envelope

Every admitted fact uses a common envelope containing at minimum:
- canonical fact key;
- subject reference;
- value/state;
- unit/semantic type when applicable;
- source/probe;
- evidence strength;
- confidence descriptor;
- capture/freshness metadata;
- visibility scope;
- evidence reference/digest;
- conflict/supersession metadata where applicable.

Raw source payloads may be retained by evidence storage policy, but cannot replace normalized fact envelopes.

## 87. Unknown as first-class data

The genome preserves explicit states such as:
- UNKNOWN;
- UNAVAILABLE;
- UNSUPPORTED_PROBE;
- PERMISSION_DENIED;
- CONFLICTING;
- STALE;
- PARTIAL;
- NOT_PRESENT_PROVEN.

Unknown is not schema omission when the contract requires a field/state to be represented.

Consumers can therefore distinguish “not asked,” “not observable,” “not supported,” and “proven absent.”

## 88. Confidence model

Confidence is multidimensional rather than one opaque percentage.

Candidate dimensions:
- source authority;
- subject-binding strength;
- evidence strength;
- freshness;
- cross-source agreement;
- semantic completeness;
- visibility completeness;
- derivation depth.

Each dimension uses a versioned ordinal/enumerated scale with explicit meaning.

A composite display score may exist only as a derived convenience. It cannot replace dimensions or authorize a stronger semantic claim.

## 89. Confidence monotonicity

Confidence cannot increase merely because:
- more weak sources repeat the same claim;
- a marketing/product-name lookup agrees;
- a newer timestamp exists without stronger evidence;
- unknown fields are omitted;
- conflicts are hidden;
- a derived fact is rounded or normalized.

Confidence promotion requires contract-defined evidence improvement.

## 90. Confidence and conflict

A conflict cannot be “averaged away.”

When authoritative sources disagree:
- both claims remain traceable;
- conflict state is explicit;
- confidence dimensions reflect disagreement;
- a governed preferred interpretation may be projected separately;
- the underlying evidence remains immutable.

Consumers must be able to request conflict-preserving form.

## 91. Schema versioning

Hardware Genome uses semantic schema versioning:
- PATCH: clarification/additive metadata that does not alter admitted semantics;
- MINOR: backward-compatible additive fields/states/capabilities;
- MAJOR: incompatible semantic or structural change.

The exact compatibility rules are machine-readable and versioned.

Producer version and schema version remain separate.

## 92. Reader compatibility

A reader declares:
- supported schema major/minor range;
- understood required feature flags;
- understood extension namespaces;
- behavior for unknown optional fields;
- behavior for unknown required semantics.

Unknown optional fields may be preserved/ignored according to contract.
Unknown required semantics fail closed.

A reader cannot silently reinterpret a newer semantic state as an older familiar one.

## 93. Writer compatibility

Writers:
- emit one explicit schema version;
- cannot claim an older schema while embedding newer incompatible semantics;
- preserve unknown fields when performing contract-defined lossless transformations where required;
- identify lossy export explicitly.

Canonical storage never depends on lossy downgrade.

## 94. Extensions

Vendor/provider/platform extensions use namespaced keys.

Extensions cannot:
- override canonical keys;
- weaken canonical invariants;
- redefine canonical units/states;
- inject executable behavior;
- become mandatory for generic readers without a schema revision.

Promoted extensions require explicit governance and compatibility review.

## 95. Genome snapshots

A genome snapshot is immutable once admitted.

A newer snapshot:
- references prior lineage when applicable;
- may supersede current-state projections;
- never rewrites historical evidence;
- can identify material change categories.

Snapshots are valid even when incomplete, provided incompleteness is explicit and required admission rules are satisfied.

## 96. Genome delta

A delta can represent change between compatible snapshots.

Every delta binds:
- exact base GenomeId;
- exact target GenomeId;
- schema compatibility;
- changed fact envelopes;
- additions/removals;
- state transitions;
- invalidations;
- conflict changes.

A delta is not independently authoritative without its bound base/target context.

## 97. Material-change classes

Candidate change classes:
- identity;
- runtime substrate;
- driver/runtime;
- capability;
- topology;
- memory/capacity;
- media/precision;
- telemetry-only;
- visibility/permission;
- confidence/evidence;
- schema-only.

Downstream consumers can subscribe to change classes without M07 deciding their reaction.

## 98. Fingerprints

M07 may expose privacy-preserving fingerprints for:
- whole genome;
- static hardware identity subset;
- runtime/capability subset;
- topology subset;
- explicitly declared M06 reproducibility-material subset.

Fingerprints bind canonicalized admitted facts and schema/canonicalization version.

They cannot include unstable telemetry unless the fingerprint contract explicitly calls for it.

## 99. Reproducibility projection

M06 receives only an explicitly declared projection of M07 facts that are material to a reproducibility contract.

Rules:
- M07 does not decide which hardware differences are materially acceptable for a production artifact;
- M06 does not manufacture hardware facts;
- the projection binds exact GenomeId/fingerprint/schema;
- omitted dynamic telemetry cannot later be implied as captured;
- equivalence policies remain owned by the consuming contract.

## 100. Canonicalization

Canonical hashing requires deterministic:
- field ordering;
- encoding;
- number/unit representation;
- state representation;
- extension ordering;
- absent versus explicit-unknown handling.

Presentation formatting cannot affect canonical identity.

Floating telemetry is excluded from static fingerprints unless explicitly included by a separate contract.

## 101. Redaction and privacy views

A genome may have derived redacted views.

Redaction can remove/minimize:
- serial numbers;
- stable platform identifiers;
- hostnames;
- sensitive device locators;
- process/user identifiers.

A redacted view:
- identifies its source GenomeId;
- identifies redaction policy/version;
- cannot claim byte/content identity with the canonical genome;
- preserves semantic states needed by the consumer.

## 102. Trust and signatures

Genome/evidence envelopes may support cryptographic integrity/authenticity metadata.

Trust metadata can identify:
- producer identity;
- signer/key reference;
- digest algorithm;
- signature;
- verification state.

Cryptographic validity proves integrity/authenticity under the trust model, not semantic truth of a lying or defective probe.

## 103. Merge and federation

Two genomes are not silently merged because they appear to describe the same machine.

Federation requires explicit subject-identity reconciliation and provenance preservation.

Conflicting snapshots/sources remain distinguishable.

A fleet view is a derived collection, not one giant hardware genome.

## 104. Storage and retention boundary

M07 defines logical evidence/genome semantics, identifiers and integrity requirements.

Physical retention, deletion, tiering and storage placement remain M55 authority.

M07 cannot promise indefinite retention unless the owning storage policy does.

## 105. Consumer contract

Consumers must declare which facts/states they require.

A consumer cannot:
- treat unknown as false/zero;
- ignore stale/conflicting state where contract marks it material;
- strengthen evidence;
- overwrite canonical genome facts;
- infer benchmark capability from discovery facts;
- convert confidence into execution authorization without its own policy.

## 106. Migration

Schema migration is explicit and testable.

A migration binds:
- source schema;
- target schema;
- migration implementation/version;
- lossless/lossy classification;
- transformed fields/states;
- evidence lineage.

Lossy migration cannot replace the canonical source genome.

## 107. Deterministic fixtures

M07 planning requires future fixtures covering:
- NVIDIA/CUDA;
- AMD/ROCm;
- Windows DirectML;
- Apple Metal;
- CPU-only;
- 8 GB discrete GPU;
- multi-GPU;
- partitioned/vGPU;
- container/VM/WSL;
- missing permissions;
- conflicting sources;
- stale evidence;
- partial/unknown data;
- schema upgrade/downgrade;
- redacted views.

Fixtures are synthetic or sanitized and deterministic.

## 108. S05 hard-invariant candidates

151. Canonical GenomeId is evidence/content anchored, not display-name anchored.
152. Schema version and producer version remain separate.
153. Canonical genome sections preserve provenance and uncertainty.
154. Every admitted fact uses a normalized evidence envelope.
155. Raw payloads cannot replace normalized fact envelopes.
156. Required unknown states cannot disappear through field omission.
157. NOT_PRESENT_PROVEN remains distinct from unknown/unavailable.
158. Confidence is multidimensional, not one opaque percentage.
159. Composite confidence cannot strengthen semantic claims.
160. Repetition of weak evidence cannot automatically promote confidence.
161. Newer timestamp alone cannot promote evidence strength.
162. Hidden unknowns/conflicts cannot increase confidence.
163. Conflicts cannot be averaged away.
164. Preferred projections cannot erase conflicting source evidence.
165. Schema compatibility rules are machine-readable and versioned.
166. PATCH cannot alter admitted semantics.
167. MINOR remains backward-compatible under declared reader rules.
168. Incompatible semantics require MAJOR versioning.
169. Unknown required semantics fail closed.
170. Readers cannot silently reinterpret newer semantic states.
171. Writers cannot mislabel incompatible semantics as an older schema.
172. Canonical storage cannot depend on lossy downgrade.
173. Extensions are namespaced.
174. Extensions cannot override or weaken canonical semantics.
175. Extensions cannot inject executable behavior.
176. Extension promotion requires governance/compatibility review.
177. Admitted genome snapshots are immutable.
178. New snapshots supersede projections, not historical evidence.
179. Incomplete snapshots remain explicitly incomplete.
180. Deltas bind exact base and target genomes.
181. Deltas are not authoritative outside bound base/target context.
182. Material-change classes do not prescribe downstream reactions.
183. Fingerprints bind canonicalization and schema versions.
184. Static fingerprints exclude unstable telemetry unless explicitly contracted.
185. M06 reproducibility receives only explicitly declared M07 projections.
186. M07 cannot decide M06 hardware-equivalence policy.
187. M06 cannot manufacture M07 hardware facts.
188. Canonical hashing is independent of presentation formatting.
189. Absent and explicit-unknown handling is deterministic.
190. Redacted views identify source genome and redaction policy.
191. Redacted views cannot claim canonical content identity.
192. Cryptographic validity cannot prove semantic truth of probe claims.
193. Genome federation requires explicit subject reconciliation.
194. Fleet collections cannot masquerade as one hardware subject.
195. Physical retention/deletion/tiering remains M55 authority.
196. Consumers declare material fact/state requirements.
197. Consumers cannot strengthen M07 evidence.
198. Consumers cannot overwrite canonical genome facts.
199. Confidence alone cannot authorize execution.
200. Schema migrations bind source/target/version and loss classification.
201. Lossy migration cannot replace canonical source genome.
202. Deterministic fixtures cover heterogeneous and constrained hardware classes.
203. 8 GB discrete GPUs remain first-class canonical genome subjects.
204. CPU-only systems remain first-class canonical genome subjects.
205. Missing permissions remain explicit evidence states.
206. Stale evidence cannot become current during serialization/migration.
207. Conflict state survives serialization, redaction and compatible migration.
208. Privacy redaction cannot silently alter capability semantics.
209. Hardware Genome cannot become a benchmark ranking.
210. Hardware Genome cannot become scheduler/placement policy.

These remain candidates until final M07 contract freeze.

## 109. Proprietary technology candidates

### IRIS-HGX — Hardware Genome Exchange
Canonical evidence-preserving schema and exchange contract for heterogeneous hardware/runtime truth, including unknowns, conflicts, provenance and redacted projections.

### IRIS-MCD — Multidimensional Confidence Descriptor
Non-scalar confidence representation across source authority, binding, evidence strength, freshness, agreement, completeness and derivation depth.

### IRIS-GDL — Genome Delta Ledger
Immutable base/target-bound change representation for hardware/runtime evolution without rewriting historical snapshots.

### IRIS-RFP — Reproducibility Fingerprint Projection
Contract-controlled projection from Hardware Genome into reproducibility-material fingerprints without allowing M07 to own M06 equivalence policy.

### IRIS-SCB — Schema Compatibility Barrier
Machine-readable reader/writer/migration compatibility gate that fails closed on unknown required semantics and prevents semantic downgrade masquerading as compatibility.

All remain planning candidates pending Final Technology Review and prior-art review.

## 110. S05 acceptance-evidence targets

Later implementation must prove at minimum:
- canonical genome identity is deterministic and evidence anchored;
- normalized fact envelopes preserve state/provenance/freshness/conflict;
- explicit unknown states survive round-trip serialization;
- confidence remains multidimensional;
- weak repeated evidence cannot self-promote;
- conflicts survive projections and serialization;
- schema PATCH/MINOR/MAJOR rules are enforced;
- unknown required semantics fail closed;
- extensions cannot override canonical semantics;
- snapshots are immutable;
- deltas require exact compatible base/target;
- fingerprints are deterministic and contract scoped;
- M06 projections are explicit and do not transfer authority;
- redaction preserves semantic states while removing sensitive identifiers;
- cryptographic verification remains distinct from semantic confidence;
- federation requires subject reconciliation;
- consumers cannot strengthen evidence;
- migration loss is explicit;
- deterministic heterogeneous fixtures exist;
- 8 GB and CPU-only systems remain first-class;
- M08/M09/M10/M12/M14/M55/M56 authority remains external.

## S05 STOP CONDITION

S05 is complete for module planning when:
- Hardware Genome identity, schema, fact envelope and sections are explicit;
- unknown/conflict/freshness/provenance survive canonical representation;
- confidence is multidimensional and cannot manufacture certainty;
- schema compatibility, extensions, snapshots, deltas, fingerprints, redaction and migrations are governed;
- 60 additional hard-invariant candidates are recorded (210 cumulative);
- five additional proprietary technology candidates are registered (25 cumulative);
- all five canonical M07 sessions are complete for module planning;
- the next permitted work is M07 Final Technology Review, followed by the M08-M60 Forward Compatibility Scan and Module Contract Freeze;
- no M07 product/runtime implementation is introduced.


# Final Technology Review

## 111. Review purpose

This review consolidates the 25 M07 proprietary technology candidates created during S01-S05.

The names are internal architecture labels only. This review makes no novelty, patentability or freedom-to-operate claim. Any external IP claim requires separate prior-art/legal review.

Classification:
- **ADOPT** — necessary enough to enter the M07 frozen contract.
- **ADOPT_AS_COMPONENT** — useful semantic/component pattern, retained under a broader adopted technology rather than as a separate subsystem.
- **DEFER** — potentially useful, but implementation is not necessary for the first bounded M07 implementation.
- **REJECT_AS_DUPLICATE** — semantics are absorbed elsewhere.

## 112. Consolidated technology decisions

### S01 candidates

1. **IRIS-HDF — Hardware Discovery Fabric: ADOPT**
   - Core bounded probe orchestration and evidence admission surface.
   - Must remain allowlisted, read-only and deterministic.

2. **IRIS-ODG — Opaque Device Graph: ADOPT**
   - Canonical identity/locator separation and hardware relationship substrate.
   - Extended by TGE rather than replaced by it.

3. **IRIS-NAF — Negative Assertion Firewall: ADOPT**
   - Mandatory guard against converting unknown/unavailable/unsupported into absence.

4. **IRIS-RSP — Runtime Substrate Passport: ADOPT**
   - Required for host/container/VM/WSL/runtime visibility truth.

5. **IRIS-DCF — Discovery Conflict Fabric: ADOPT_AS_COMPONENT**
   - Conflict semantics remain mandatory but are incorporated into HGX/MCD evidence envelopes rather than implemented as an independent service.

### S02 candidates

6. **IRIS-CEL — Capability Evidence Ladder: ADOPT**
   - Core capability evidence-strength contract.

7. **IRIS-BRM — Backend Relationship Matrix: ADOPT**
   - Required to preserve device/backend/runtime/version relationships without false capability broadcast.

8. **IRIS-PDM — Precision Dimensional Matrix: ADOPT_AS_COMPONENT**
   - Retained as the provider-neutral precision vocabulary feeding PFX.

9. **IRIS-VSF — Version Separation Fabric: ADOPT**
   - Required to prevent driver/runtime/toolkit/library/framework version collapse.

10. **IRIS-CCG — Capability Conflict Graph: ADOPT_AS_COMPONENT**
    - Conflict graph semantics are retained under HGX/BRM rather than a separate first-release subsystem.

### S03 candidates

11. **IRIS-DSG — Driver Skew Graph: ADOPT**
    - Required for host/kernel/container/guest/framework active-path skew.

12. **IRIS-PFX — Precision Feature Lattice: ADOPT**
    - Superset execution of PDM semantics; exact precision evidence remains dimensional.

13. **IRIS-MEC — Media Engine Capability Matrix: ADOPT**
    - Required for exact-device/path encode/decode capability truth.

14. **IRIS-TGE — Topology Graph Evidence: ADOPT**
    - Evidence layer extending ODG with topology/interconnect semantics.

15. **IRIS-P2P — Pairwise Path Proof: ADOPT_AS_COMPONENT**
    - Exact directional peer proof retained inside TGE.

### S04 candidates

16. **IRIS-TSL — Telemetry Semantics Ledger: ADOPT**
    - Required to prevent cross-provider metric semantic collapse.

17. **IRIS-MPF — Memory Pressure Fabric: ADOPT**
    - Required dynamic evidence surface, explicitly non-prescriptive.

18. **IRIS-TCR — Thermal Causality Resolver: ADOPT_AS_COMPONENT**
    - Causality guard retained under TSL rather than an independent subsystem.

19. **IRIS-EDE — Evidence Derivation Engine: ADOPT**
    - Required deterministic derivation lineage for rates/ratios/classifications.

20. **IRIS-SWG — Sampling Window Governor: ADOPT**
    - Required safety/boundedness governor for dynamic telemetry.

### S05 candidates

21. **IRIS-HGX — Hardware Genome Exchange: ADOPT**
    - Canonical schema/exchange contract for admitted M07 truth.

22. **IRIS-MCD — Multidimensional Confidence Descriptor: ADOPT**
    - Required non-scalar confidence representation.

23. **IRIS-GDL — Genome Delta Ledger: ADOPT**
    - Required exact base/target change representation.

24. **IRIS-RFP — Reproducibility Fingerprint Projection: ADOPT**
    - Required controlled M07→M06 projection boundary.

25. **IRIS-SCB — Schema Compatibility Barrier: ADOPT**
    - Required fail-closed schema reader/writer/migration compatibility gate.

## 113. Consolidation result

Final disposition:
- ADOPT: 20
- ADOPT_AS_COMPONENT: 5
- DEFER: 0
- REJECT_AS_DUPLICATE: 0

The 25 candidate concepts therefore remain represented, but only 20 are independent frozen technology surfaces. Five become mandatory components of broader surfaces to reduce subsystem fragmentation.

## 114. Dependency graph

Core dependency direction:
- HDF → admitted probe evidence.
- ODG + RSP → exact subject/runtime identity.
- NAF → negative/absence admission safety.
- CEL + BRM + VSF → capability/runtime truth.
- DSG + PFX + MEC + TGE → specialized driver/precision/media/topology evidence.
- TSL + MPF + EDE + SWG → bounded dynamic telemetry evidence.
- HGX consumes admitted evidence from all preceding surfaces.
- MCD annotates evidence quality without changing semantics.
- GDL compares immutable HGX snapshots.
- RFP emits explicitly contracted reproducibility projections to M06.
- SCB guards schema compatibility, readers, writers and migrations.

No dependency edge permits a downstream component to strengthen upstream evidence.

## 115. Implementation criticality

**Foundation-critical for first implementation slice**
- HDF
- ODG
- NAF
- RSP
- CEL
- VSF
- HGX
- MCD
- SCB

**Necessary specialized capability surfaces**
- BRM
- DSG
- PFX
- MEC
- TGE

**Necessary dynamic telemetry surfaces**
- TSL
- MPF
- EDE
- SWG

**Necessary lifecycle/integration surfaces**
- GDL
- RFP

Implementation may be staged, but a staged implementation cannot claim complete M07 conformance until all frozen mandatory surfaces and acceptance evidence pass.

## 116. Technology risk review

Principal risks and controls:

- **Vendor semantic drift**: versioned probes, source contracts and fail-closed unknown states.
- **False equivalence across APIs/vendors**: provider-neutral vocabulary plus namespaced extensions and semantic identity requirements.
- **Probe privilege creep**: HDF allowlist, read-only contract and SWG bounds.
- **Confidence laundering**: MCD dimensions cannot strengthen semantic evidence.
- **Schema drift**: SCB semantic versioning and compatibility gates.
- **Identity/privacy leakage**: ODG identity/locator separation and redacted HGX views.
- **Telemetry becoming policy**: TSL/MPF remain observational; M09/M10/M12 retain decision authority.
- **Discovery becoming benchmark**: smoke/conformance remains bounded; M08 owns empirical performance.
- **M06 authority leakage**: RFP is explicit projection only.
- **Subsystem proliferation**: five candidates collapsed into mandatory components rather than independent services.

## 117. 8 GB / heterogeneous hardware review

The consolidated design preserves:
- 8 GB discrete GPUs as first-class;
- CPU-only hosts as first-class;
- AMD/NVIDIA/Intel/Apple/generic backends without one vendor becoming canonical;
- VM/container/WSL/partitioned devices as valid subjects;
- missing capabilities as explicit evidence states rather than product exclusion;
- no automatic quality downgrade from constrained hardware.

## 118. Final Technology Review verdict

**APPROVED_FOR_FORWARD_COMPATIBILITY_SCAN**

Conditions:
- all 210 candidate invariants remain subject to final contract freeze wording;
- the 20 independent adopted technology surfaces and five absorbed components remain semantically represented;
- no implementation begins before the M08-M60 Forward Compatibility Scan, contract freeze, independent planning audit, merge and exact-main validation;
- no novelty/patentability claim is made by this review.

## Final Technology Review STOP CONDITION

The technology review is complete when:
- every candidate has a disposition;
- overlaps are consolidated;
- dependency direction and implementation criticality are explicit;
- risk controls and authority boundaries remain intact;
- constrained/heterogeneous hardware remains first-class;
- the next permitted planning action is the M08-M60 Forward Compatibility Scan.


# M08-M60 Forward Compatibility Scan

## 119. Scan method

This scan checks whether the M07 contract leaves sufficient stable interfaces for later modules without deep-planning those modules or importing their authority into M07.

Result vocabulary:
- **DIRECT_CONSUMER** — expected to consume M07 facts/genome/projections directly.
- **INDIRECT_CONSUMER** — likely receives M07-derived decisions through another owning module.
- **BOUNDARY_ONLY** — M07 must preserve a boundary/identifier but should not provide the module's domain decision.
- **NO_NEW_M07_CONTRACT** — current M07 contract is sufficient; no extra interface is required now.

## 120. Area B scan — M08-M13

### M08 — Microbenchmark Lab & Capability Envelope
**DIRECT_CONSUMER.**
Needs exact subject/runtime IDs, capability evidence, topology, freshness and bounded probe safety. M08 adds empirical performance/capability envelopes and must not rewrite M07 discovery facts.

**M07 contract requirement:** stable GenomeId/HardwareSubjectRef/RuntimeSubjectRef, evidence references and change invalidation hooks.

### M09 — Resource Digital Twin & Dynamic VRAM Governor
**DIRECT_CONSUMER.**
Consumes static capacity/topology plus fresh telemetry/pressure. M09 owns leases, reservations, residency, spill/offload and cleanup policy.

**Requirement:** distinguish static capacity from transient usage and expose freshness/source semantics.

### M10 — Adaptive Execution Planner
**DIRECT_CONSUMER.**
Consumes M07 truth plus M08 envelopes and M09 resource state. M10 owns workload plans, OOM/thermal policy and quality-aware adaptation.

**Requirement:** no prescriptive “recommended execution mode” field in M07.

### M11 — Background Worker Fabric
**BOUNDARY_ONLY.**
Worker lifecycle may use runtime/device identifiers and health visibility but owns process lifecycle/concurrency.

**Requirement:** stable opaque subject/runtime refs; M07 cannot kill/restart workers.

### M12 — Compute Orchestration
**DIRECT_CONSUMER.**
Consumes capability/topology advertisements but owns placement, federation, trust, queues and quotas.

**Requirement:** genome supports redacted capability advertisement and exact node-local subject identity without assuming global identity equivalence.

### M13 — Performance, Cache & Execution Efficiency
**INDIRECT_CONSUMER.**
Consumes M08/M10 performance decisions and may use M07 fingerprints for invalidation.

**Requirement:** material-change classes/fingerprints remain stable; no cache policy in M07.

## 121. Area C scan — M14-M19

### M14 — Model Registry & Empirical Model Cards
**DIRECT_CONSUMER.**
Needs hardware/runtime fingerprints to bind empirical model compatibility evidence.

**Requirement:** RFP-like projections can be consumer-specific without M07 asserting model compatibility.

### M15 — Multi-Model Director
**INDIRECT_CONSUMER.**
Uses M14/M10 evidence. No direct routing authority belongs in M07.

### M16 — Workflow Registry & Provider Compiler
**DIRECT_CONSUMER.**
May declare hardware/backend capability requirements against provider-neutral M07 vocabulary.

**Requirement:** capability keys are versioned and extensible; workflow compatibility remains M16-owned.

### M17 — ComfyUI Runtime Integration
**DIRECT_CONSUMER.**
Needs runtime/backend/device visibility and version relationships for qualification/recovery.

**Requirement:** extensions can represent ComfyUI-specific runtime facts without making ComfyUI canonical.

### M18 — Model Acquisition/Supply Chain
**BOUNDARY_ONLY.**
May use capacity/storage visibility facts for planning, but downloads, licenses and package trust remain M18.

### M19 — Training
**DIRECT_CONSUMER.**
Needs exact precision/backend/memory/topology evidence. Training feasibility/performance remains M19/M08/M10.

## 122. Area D scan — M20-M24

M20 Image Studio, M21 Reference Fusion, M22 Design Intelligence, M23 Image Repair and M24 Image Quality Evals are primarily **INDIRECT_CONSUMER** modules.

They consume hardware-aware choices through M10/M14/M16 and quality authority through M01/M24/M48.

**M07 requirement:** no image-domain capability promises are embedded in Hardware Genome. Consumer-specific projections may bind exact hardware evidence without claiming creative quality.

## 123. Area E scan — M25-M35

### M25-M30
3D asset, geometry, materials, rigging and animation modules are **INDIRECT_CONSUMER** modules. Hardware execution choices flow through M10/M16/M26.

### M26 — Blender Automation
**DIRECT_CONSUMER.**
Needs CPU/GPU/backend/runtime identity and capability facts to qualify headless renderer/runtime visibility.

**Requirement:** DCC-specific extension namespace, no DCC process control in M07.

### M31 — Camera, Lighting & Rendering
**DIRECT_CONSUMER.**
Renderer choice may consume M07 capability truth plus M08 empirical evidence.

**Requirement:** M07 reports backend/precision/device/media facts, never chooses Cycles/EEVEE or render settings.

### M32 — VFX/Physics
**INDIRECT_CONSUMER.**
Hardware strategy is downstream of M10/M16/M26.

### M33 — Maya/DCC Interoperability
**DIRECT_CONSUMER.**
Requires extension-friendly DCC capability discovery and runtime version evidence.

### M34 — Web 3D/WebGPU
**BOUNDARY_ONLY.**
Local production hardware may affect compilation, but destination-device profiles belong to M34/M59.

### M35 — Game Engine Asset Delivery
**BOUNDARY_ONLY.**
Engine destination compatibility is not workstation hardware truth.

## 124. Area F scan — M36-M38

### M36-M37
Video generation/continuity are **INDIRECT_CONSUMER** modules using M10/M14/M16.

### M38 — Editing, Compositing, Color & Encode
**DIRECT_CONSUMER.**
Needs MEC exact encode/decode/profile/bit-depth/chroma evidence.

**Requirement:** codec capability schema remains extensible and distinguishes static/report/smoke evidence from M08 empirical throughput. M38 owns codec/container/bitrate strategy.

## 125. Area G scan — M39-M42

Digital humans, voice, music and sound are **INDIRECT_CONSUMER** modules.

Audio/video hardware acceleration facts may be consumed through M10/M14/M16/M38, but M07 must not define voice/music/audio quality or creative capability.

**No new M07 contract required.**

## 126. Area H scan — M43-M47

Narrative, faceless content, advertising, brand and localization are **INDIRECT_CONSUMER** modules.

Their hardware awareness is execution infrastructure, not domain truth.

**No new M07 contract required.**

## 127. Area I scan — M48-M51

### M48 — Quality Court
**BOUNDARY_ONLY.**
May inspect whether evidence was produced under a known hardware/runtime genome, but hardware confidence cannot substitute for output-quality confidence.

### M49 — Self-Correction
**INDIRECT_CONSUMER.**
Repair planning uses M10/M14/M48.

### M50 — Cost-to-Quality Optimization
**INDIRECT_CONSUMER.**
Uses M08/M10/M14 and cost evidence. M07 cannot assign compute ROI.

### M51 — Benchmark Lab/Evals
**DIRECT_CONSUMER.**
Needs stable GenomeId/fingerprints for comparative benchmark provenance.

**Requirement:** M51 benchmark results bind exact M07 genome/projection; M07 remains non-benchmarking.

## 128. Area J scan — M52-M55

### M52 — HIVE Memory
**DIRECT_CONSUMER / BOUNDARY_ONLY.**
May index/retrieve redacted genome metadata and checkpoint references.

**Requirement:** redacted views and stable IDs; HIVE cannot become source of current hardware truth without fresh M07 evidence.

### M53 — Provenance/Rights/C2PA
**DIRECT_CONSUMER.**
May include Hardware Genome/reproducibility references in provenance.

**Requirement:** stable digest/signature metadata and privacy-safe projections. Hardware identity does not imply rights/consent.

### M54 — Security/Identity
**DIRECT_CONSUMER.**
Owns trust/RBAC/secrets/sandbox policy and may constrain M07 probe permissions.

**Requirement:** HDF probe capabilities are permission-addressable and extensions cannot inject executable behavior.

### M55 — Storage/Cache/Archive
**DIRECT_CONSUMER / AUTHORITY_BOUNDARY.**
Stores M07 evidence/genomes according to retention/tiering policy.

**Requirement:** immutable logical IDs/digests plus externalized retention references. M07 cannot own physical deletion/tiering.

## 129. Area K scan — M56-M60

### M56 — Observability/Control Center
**DIRECT_CONSUMER.**
Consumes S04 telemetry and genome state for dashboards/analytics.

**Requirement:** TSL metric semantics, freshness and zero-invented-data behavior remain machine-readable. M56 owns aggregation/history/UI.

### M57 — Automation/Agents
**BOUNDARY_ONLY.**
Agents may request/read M07 discovery but cannot manufacture hardware truth or bypass probe bounds.

### M58 — API/SDK/MCP/Plugin Ecosystem
**DIRECT_CONSUMER.**
Exposes stable M07 domain APIs.

**Requirement:** HGX/SCB schemas, extension namespaces, compatibility rules and redacted views must be API-safe. Plugin probes remain governed by HDF/M54 permissions.

### M59 — Export/Adaptive Delivery
**BOUNDARY_ONLY.**
May use local codec capabilities for production, but destination capability profiles are M59-owned.

### M60 — Deployment/Recovery/Final Acceptance
**DIRECT_CONSUMER.**
Needs install-time/runtime discovery, migrations, backup/restore semantics and 8 GB acceptance evidence.

**Requirement:** deterministic fixtures, schema migration, genome reconstruction and exact hardware-class evidence must be testable. Deployment may invoke discovery but cannot weaken M07 truth rules.

## 130. Cross-module compatibility findings

### Finding FC-01 — Consumer-specific projections
**IMPORTANT / ADMIT TO FREEZE.**
RFP must support named/versioned consumer projection contracts, not only M06. This permits M14/M16/M51/M53/M58/M60 to bind the minimum required M07 facts without copying the full genome.

Authority remains with each consumer for its domain interpretation.

### Finding FC-02 — Machine-readable capability vocabulary registry
**NECESSARY / ADMIT TO FREEZE.**
CEL/BRM/PFX/MEC/TSL keys require a versioned registry with semantic type, unit, evidence requirements and extension namespace rules so M16/M38/M56/M58 can safely consume them.

### Finding FC-03 — Permission-addressable probe classes
**NECESSARY / ADMIT TO FREEZE.**
HDF probe descriptors need explicit capability/permission classes for M54/M58 plugin governance. A plugin cannot gain discovery privilege merely by registering a probe.

### Finding FC-04 — Redacted advertisement profile
**NECESSARY / ADMIT TO FREEZE.**
HGX needs a standard privacy-safe capability-advertisement view for M12 federation and M58 APIs. It must preserve evidence strength/freshness while minimizing stable identifiers.

### Finding FC-05 — Change subscription contract
**IMPORTANT / ADMIT TO FREEZE.**
GDL/material-change classes need a versioned event/reference contract so M08/M09/M13/M56 can invalidate derived state without polling or interpreting raw deltas ad hoc.

This defines event semantics only; M11/M56 own delivery infrastructure.

### Finding FC-06 — Domain extension isolation
**NECESSARY / ALREADY SATISFIED; REINFORCE.**
ComfyUI, Blender, Maya, codecs and future plugins require namespaced extensions that cannot override canonical M07 semantics.

### Finding FC-07 — Benchmark provenance binding
**NECESSARY / ADMIT TO FREEZE.**
M08/M14/M51 empirical evidence must be able to bind exact GenomeId plus a named hardware projection/fingerprint and freshness/change context.

M07 still does not own benchmark results.

### Finding FC-08 — Quality-confidence separation
**NECESSARY / ALREADY SATISFIED; REINFORCE.**
MCD hardware-evidence confidence must never be interpreted as M01/M24/M48 output-quality confidence.

### Finding FC-09 — Destination capability separation
**NECESSARY / ALREADY SATISFIED; REINFORCE.**
Workstation Hardware Genome cannot absorb web/mobile/game/social destination-device profiles from M34/M35/M59.

### Finding FC-10 — Recovery reconstruction contract
**IMPORTANT / ADMIT TO FREEZE.**
M60 requires reconstruction/import validation that can restore a stored genome/evidence package as historical evidence while requiring fresh discovery before current-state claims.

## 131. Scan-induced invariant candidates

211. Consumer-specific projections are named and versioned.
212. A consumer projection cannot strengthen source genome evidence.
213. Projection omission cannot imply an uncaptured fact.
214. Capability/metric keys come from a versioned semantic registry or governed namespace.
215. Registry entries declare semantic type/unit/evidence requirements where applicable.
216. Plugin/provider extensions cannot shadow canonical registry keys.
217. Probe descriptors declare explicit permission/capability classes.
218. Probe registration cannot grant execution privilege.
219. Federated capability advertisements use privacy-safe redacted profiles.
220. Redaction cannot remove evidence state/freshness needed for advertised claims.
221. Change notifications bind exact prior/current genome or delta identity.
222. Change events describe evidence change, not downstream policy action.
223. Benchmark/model/workflow evidence can bind exact genome projection/fingerprint.
224. Benchmark bindings cannot convert M07 discovery into benchmark truth.
225. Hardware-evidence confidence remains distinct from output-quality confidence.
226. Destination-device capability profiles remain outside M07 authority.
227. Historical genome restoration cannot create a current-state claim.
228. Recovery requires fresh discovery for current hardware truth.
229. HIVE retrieval cannot override fresher admitted M07 evidence.
230. Agents/plugins cannot manufacture or strengthen M07 evidence.
231. DCC/provider extensions remain namespaced and non-authoritative over canonical keys.
232. M56 may aggregate telemetry but cannot invent missing M07 samples.
233. M55 retention/deletion actions cannot rewrite genome/evidence semantic history.
234. M12 federation cannot assume globally stable raw device identifiers.
235. M60 acceptance can require hardware-class evidence without redefining M07 fact semantics.

These are added to the freeze candidate because they are required to keep M07 forward-compatible without deep-planning future modules.

## 132. Forward Compatibility Scan verdict

Modules scanned: **53/53 (M08-M60)**.

Result:
- no future module requires M07 to take over another module's authority;
- 10 compatibility findings identified;
- 6 findings add/reinforce concrete freeze requirements;
- 4 findings reinforce already-planned boundaries;
- 25 additional invariant candidates admitted, bringing the freeze-candidate total to **235**;
- no product/runtime implementation is introduced.

**Verdict: APPROVED_FOR_MODULE_CONTRACT_FREEZE.**

## Forward Compatibility Scan STOP CONDITION

The scan is complete when:
- M08-M60 have each been classified by relationship to M07;
- direct consumers have a stable interface path;
- future-domain authority remains outside M07;
- cross-module compatibility findings are incorporated into the freeze candidate;
- the next permitted action is M07 Module Contract Freeze and final independent planning audit.


# M07 Module Contract Freeze

Freeze ID: `m07-contract-v1.0`
Freeze status: `FROZEN_CANDIDATE_PENDING_FINAL_AUDIT`

## 133. Frozen mission

M07 owns evidence-bound discovery and representation of hardware/runtime truth.

It discovers and versions:
- GPU/CPU/RAM/storage/runtime visibility;
- CUDA/ROCm/DirectML/Metal and generic capability evidence;
- driver/runtime/precision/media/topology facts;
- bounded thermal/power/utilization/memory-pressure telemetry;
- Hardware Genome identity, schema, confidence, snapshots, deltas, projections and compatibility.

M07 does not benchmark workloads, allocate resources, plan execution, control workers, schedule compute, rank models, choose creative quality, manage physical storage or own dashboard aggregation.

## 134. Frozen authority boundaries

- M06 owns production/reproducibility policy; M07 supplies explicit hardware projections only.
- M08 owns empirical microbenchmarks and capability envelopes.
- M09 owns resource digital twin, VRAM leases/residency/offload.
- M10 owns hardware-aware execution planning and OOM/thermal decisions.
- M11 owns worker/process lifecycle.
- M12 owns placement, queues, federation and scheduling.
- M14 owns empirical model capability/compatibility truth.
- M55 owns physical retention/deletion/tiering.
- M56 owns observability aggregation/history/UI.
- M01/M24/M48 own output-quality semantics/evidence, not M07 confidence.

## 135. Frozen canonical concepts

Required concepts include:
- DiscoverySessionRef;
- HardwareSubjectRef;
- RuntimeSubjectRef;
- DiscoveryObservation;
- DiscoverySnapshot;
- ProbeDescriptor;
- ProbeEvidenceRef;
- ObservationState;
- DiscoveryConflict;
- FreshnessClass;
- RuntimeSubstrate;
- DeviceLocatorEvidence;
- PrivacyClass;
- Hardware Genome / GenomeId;
- normalized Fact Envelope;
- multidimensional confidence descriptor;
- schema compatibility descriptor;
- immutable genome snapshot;
- exact base/target genome delta;
- named/versioned consumer projection;
- canonical fingerprint;
- redacted capability advertisement;
- material-change event/reference.

Names may evolve only through a later governed contract revision; semantics cannot be silently weakened.

## 136. Frozen evidence-state semantics

At minimum the contract preserves:
- OBSERVED;
- NOT_PRESENT_PROVEN;
- UNKNOWN;
- UNSUPPORTED_PROBE;
- PERMISSION_DENIED;
- UNAVAILABLE;
- CONFLICTING;
- STALE;
- PARTIAL.

Unknown/unavailable/unsupported/permission-denied/partial cannot become absence.

Stale cannot become current through serialization, migration, retrieval or projection.

## 137. Frozen capability evidence ladder

Capability evidence strength preserves:
- DECLARED;
- LOADABLE;
- DEVICE_BOUND;
- FEATURE_REPORTED;
- SMOKE_VERIFIED;
plus explicit non-proof/error states.

Evidence strength is monotonic only when stronger new evidence is admitted. Tiny smoke verification is conformance evidence, never workload-performance evidence.

## 138. Frozen probe safety contract

M07 probes are:
- allowlisted;
- versioned;
- bounded;
- read-only;
- timeout/resource constrained;
- permission-addressable;
- non-arbitrary;
- provenance producing.

M07 probes cannot install/configure drivers, execute arbitrary project binaries, stress hardware, mutate clocks/fans/power, kill workers/processes, evict unrelated memory or silently escalate privilege.

Plugin/provider registration cannot grant probe privilege.

## 139. Frozen identity and privacy contract

Canonical identity remains separate from mutable locator/display information.

Raw serials, hostnames, user paths, command lines and unrelated process metadata are minimized.

Federated/API advertisement uses a privacy-safe redacted profile that preserves claim evidence strength, freshness and semantic state without assuming globally stable raw device identifiers.

## 140. Frozen backend/version contract

Backend relationships are exact-subject scoped.

Driver, user runtime, loader/API, toolkit/SDK, library/framework binding, OS runtime and firmware facts remain semantically separate.

Installed components remain distinct from active/bound components.

One backend/device fact cannot be broadcast to other devices or the host.

## 141. Frozen precision/media/topology contract

Precision remains multidimensional across storage, arithmetic, acceleration, accumulation, conversion, exposure and verification.

Encode/decode facts remain direction/path/device/profile/level/bit-depth/chroma scoped.

Codec conformance cannot become throughput/session-concurrency proof.

Topology preserves physical/virtual/partitioned subjects, PCIe capability versus negotiated state versus measured performance, exact-pair directional peer evidence and distinct memory/interconnect semantics.

## 142. Frozen telemetry contract

Dynamic telemetry remains distinct from static discovery.

Every admitted sample binds subject, metric semantics, unit, time/window, freshness and evidence.

Transient free VRAM is not a safe allocation budget.

Sampling is bounded and non-invasive.

Derived metrics preserve source lineage and derivation version.

Telemetry evidence does not itself authorize execution/resource/quality policy.

## 143. Frozen Hardware Genome contract

A canonical genome is:
- evidence/content anchored;
- schema-versioned independently from producer version;
- immutable once admitted;
- provenance/conflict/unknown/freshness preserving;
- deterministic under canonical serialization;
- extension-safe;
- redaction-capable;
- migration-aware.

PATCH/MINOR/MAJOR compatibility is governed and machine-readable.

Unknown required semantics fail closed.

Extensions are namespaced and cannot override canonical keys, units, states, invariants or inject executable behavior.

## 144. Frozen confidence contract

Confidence is multidimensional.

A scalar/composite presentation cannot strengthen evidence or semantic claims.

Repeated weak evidence, newer timestamps, omitted unknowns or hidden conflicts cannot manufacture confidence.

Cryptographic integrity/authenticity is distinct from semantic truth.

Hardware-evidence confidence is distinct from output-quality confidence.

## 145. Frozen snapshot/delta/projection contract

Snapshots are immutable.

Deltas bind exact base and target genomes and are not authoritative outside that context.

Consumer projections are named/versioned and cannot:
- strengthen source evidence;
- imply omitted facts;
- transfer M07 authority to a consumer or consumer authority to M07.

M06 reproducibility, M14 model evidence, M16 workflows, M51 benchmarks, M53 provenance, M58 APIs and M60 acceptance can bind exact projections/fingerprints under their own policies.

## 146. Frozen semantic registry contract

Canonical capability/metric keys use a versioned machine-readable registry or governed namespace.

Registry entries define, where applicable:
- semantic type;
- unit;
- evidence requirements;
- allowed states;
- freshness class;
- canonicalization rules.

Provider/plugin extensions cannot shadow canonical keys.

## 147. Frozen change contract

Material changes use versioned classes and bind exact prior/current genome or delta identity.

Change events report evidence change, not downstream policy action.

Delivery infrastructure remains outside M07.

Historical restoration never creates a current-state claim; fresh discovery is required for current truth after recovery.

## 148. Frozen constrained-hardware doctrine

8 GB discrete GPUs and CPU-only systems are first-class supported Hardware Genome subjects.

Scarcity or transient pressure can expose explicit evidence/gaps/routes but cannot silently lower canonical output quality.

Mixed-vendor, multi-GPU, partitioned/vGPU, VM/container/WSL and generic runtimes remain first-class discovery cases.

## 149. Frozen technology surfaces

Independent mandatory surfaces:
1. IRIS-HDF — Hardware Discovery Fabric
2. IRIS-ODG — Opaque Device Graph
3. IRIS-NAF — Negative Assertion Firewall
4. IRIS-RSP — Runtime Substrate Passport
5. IRIS-CEL — Capability Evidence Ladder
6. IRIS-BRM — Backend Relationship Matrix
7. IRIS-VSF — Version Separation Fabric
8. IRIS-DSG — Driver Skew Graph
9. IRIS-PFX — Precision Feature Lattice
10. IRIS-MEC — Media Engine Capability Matrix
11. IRIS-TGE — Topology Graph Evidence
12. IRIS-TSL — Telemetry Semantics Ledger
13. IRIS-MPF — Memory Pressure Fabric
14. IRIS-EDE — Evidence Derivation Engine
15. IRIS-SWG — Sampling Window Governor
16. IRIS-HGX — Hardware Genome Exchange
17. IRIS-MCD — Multidimensional Confidence Descriptor
18. IRIS-GDL — Genome Delta Ledger
19. IRIS-RFP — Reproducibility Fingerprint Projection
20. IRIS-SCB — Schema Compatibility Barrier

Mandatory absorbed components:
- IRIS-DCF under HGX/MCD conflict semantics;
- IRIS-PDM under PFX;
- IRIS-CCG under HGX/BRM;
- IRIS-P2P under TGE;
- IRIS-TCR under TSL.

These are internal architecture labels, not novelty/patentability claims.

## 150. Frozen invariant set

The freeze adopts hard invariants **1-235** from S01-S05 plus the Forward Compatibility Scan.

Later implementation must encode/test the invariants relevant to each implementation slice and provide traceable evidence.

An implementation cannot claim complete M07 conformance while any applicable frozen invariant is unimplemented, untested, contradicted or waived without a governed contract revision.

## 151. Frozen acceptance evidence

Complete M07 implementation must eventually prove:
- deterministic bounded discovery;
- exact subject/runtime/evidence binding;
- negative-assertion safety;
- backend/version/precision/media/topology correctness;
- bounded non-invasive telemetry;
- static/dynamic fact separation;
- explicit unknown/conflict/stale handling;
- deterministic Hardware Genome serialization/identity;
- schema compatibility and migration behavior;
- multidimensional confidence behavior;
- privacy-safe redaction/advertisement;
- exact snapshot/delta/projection behavior;
- semantic registry governance;
- permission-addressable probe safety;
- deterministic heterogeneous fixtures;
- 8 GB and CPU-only first-class behavior;
- authority boundaries against M06/M08/M09/M10/M11/M12/M14/M55/M56;
- full repository regression evidence.

## 152. Implementation staging rule

The implementation Work Order may stage delivery to reduce risk, but:
- every stage must have explicit frozen-contract coverage;
- partial implementation must identify unsupported/unimplemented surfaces honestly;
- no placeholder can claim admitted hardware truth;
- no stage can weaken frozen invariants to make tests pass;
- final M07 completion requires all mandatory surfaces and applicable acceptance evidence.

## 153. Freeze change control

After `m07-contract-v1.0` is approved and merged, changes to frozen semantics require:
1. explicit change proposal;
2. affected invariant/interface list;
3. cross-module impact analysis;
4. compatibility/migration analysis;
5. independent review;
6. new contract version when semantics change;
7. exact-main validation.

Editorial clarification that does not alter semantics may follow PATCH governance.

## 154. Freeze verdict candidate

Candidate verdict: `M07_CONTRACT_V1_0_READY_FOR_INDEPENDENT_AUDIT`.

No implementation authorization is implied.

## M07 CONTRACT FREEZE STOP CONDITION

The freeze candidate is complete when:
- canonical M07 scope and authority are explicit;
- all 235 invariants are adopted;
- all 20 independent surfaces and five mandatory components are dispositioned;
- acceptance evidence and implementation staging rules are explicit;
- change control is explicit;
- an independent final planning audit is the only remaining pre-merge planning gate.
