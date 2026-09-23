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
