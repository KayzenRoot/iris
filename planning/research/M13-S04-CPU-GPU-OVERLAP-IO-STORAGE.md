# M13 S04 | CPU/GPU Overlap, I/O Scheduling and Storage Efficiency

**IRIS-WO-0048 | Issue #155 | September 27, 2026 | SOURCE-ONLY RESEARCH; NO RUNTIME**

Study sequencing, concurrency and storage overhead as hypotheses. CPU and GPU operations may overlap only with separately verified device/toolchain abilities, authentic owner-issued work/resource rights and a valid benchmark protocol. CUDA documentation is mutable upstream context, NOT evidence that the user's GPU supports a proposed mode.

## Source-exact authority boundary

Exact original protected main `c73b524e90a433d3476521d7a4b47f9451e3d32c`; exact base tree `489187561ab7c581c932a4721edfcadf9ac7dd9e`. Existing frozen M07 and M08 evidence/protocol, M09 immutable resource governor, M10 frozen advisory-only plan, unfrozen M11/M12, and previous S01–S03 research are independent authority layers. No M13 planning exercise selects a stream, worker or storage backend.

- `INDEX`: [planning/MASTER-MODULE-INDEX.md](../../planning/MASTER-MODULE-INDEX.md); exact original Git blob `19c8ff6126748cb89e53108bdff8289322071970`; required original anchor `S04 — S04 CPU/GPU overlap, I/O scheduling and storage efficiency`.
- `M07`: [docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md](../../docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md); exact original Git blob `2a0b95dd3cc665e2206e454caef5858ef7fb61b0`; required original anchor `M07 does not lower quality targets`.
- `M08`: [docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md](../../docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md); exact original Git blob `461e0f332d9be2af694634bbdc8cf67e29d56393`; required original anchor `UNKNOWN_TELEMETRY`.
- `M09`: [docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md](../../docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md); exact original Git blob `d12b4f48030c1a57b8e6228df39f35dac8c2b20a`; required original anchor `M09 is the provider-neutral resource-state`.
- `M10`: [planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md); exact original Git blob `f69ec3e3eab24b47c0e31832d64d9ab9cce21828`; required original anchor `m10-contract-v1.0`.
- `M11`: [planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md); exact original Git blob `41ab89727c7be14e35e2481aefbd97a0cb81cb48`; required original anchor `PROPOSED_C02_CORRECTION_NOT_FROZEN`.
- `M12`: [planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md); exact original Git blob `28b3802901349263100ceaaf80c0990513dbbded`; required original anchor `Implementation authority: NOT_ADMITTED`.
- `S01`: [planning/research/M13-S01-WARM-MODEL-CACHE-LOCALITY.md](../../planning/research/M13-S01-WARM-MODEL-CACHE-LOCALITY.md); exact original Git blob `7701c1e744d2b459d2f6bb4fa754352374fb67fd`; required original anchor `C03_DEVICE_RESIDENCY_HINT`.
- `S02`: [planning/research/M13-S02-COMPILATION-ATTENTION-BACKENDS.md](../../planning/research/M13-S02-COMPILATION-ATTENTION-BACKENDS.md); exact original Git blob `33736cc40214af1ee25586d6c94789d8c0d95739`; required original anchor `AUTO_SDPA`.
- `S03`: [planning/research/M13-S03-INTERMEDIATE-REUSE-GENERATION-DELTA.md](../../planning/research/M13-S03-INTERMEDIATE-REUSE-GENERATION-DELTA.md); exact original Git blob `96a9952086300a1ae2d46195bd7dc6d50dea06ba`; required original anchor `Seven unadopted reuse concepts`.
- `M01`: [docs/M01-QUALITY-KERNEL.md](../../docs/M01-QUALITY-KERNEL.md); exact original Git blob `930af57944fa83c44745873c42eb3a7740972ee6`; required original anchor `m01-contract-v1.0`.
- `M02`: [planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md); exact original Git blob `a85d80ab3bb5f4bdc9be915a59caa92569d66af4`; required original anchor `semantic reuse requires explicit reuse class/admission`.
- `M06`: [planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md); exact original Git blob `18b5303d1e36ef60de17b42dd9e2c371ecf4f191`; required original anchor `Digest equality proves byte equality under the declared digest domain only.`.
- `D01`: [.engineering/evidence/M09-B-OWNER-DIRECTION-D01.json](../../.engineering/evidence/M09-B-OWNER-DIRECTION-D01.json); exact original Git blob `30cc56a2dd34a8c45cfb96f0a900cafbdd2717bb`; required original anchor `B_FUTURE_OWNER_RECEIPT`.

## Mutable public upstream reference: illustrative technology, never local proof

- **NVIDIA_CUDA_BPG** [Official NVIDIA source](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/): NVIDIA documents host pinned memory as a prerequisite for async H2D/D2H overlap with GPU kernels in separate non-default streams on capable devices; actual async copy engine support is device-dependent, excess pinning can harm host performance and nominal API availability proves no throughput. **MUTABLE_OFFICIAL_REFERENCE_NOT_GPU_OR_OS_ATTESTATION**.

## Seven nonadopted CPU/GPU/I/O concepts

### CLASS-01: HOST_PREPROCESS_WORKSET

Conditional research hypothesis: Future CPU-side decoding, validation and transformation before GPU work.
Mandatory future owner proof: CPU cores and host RAM budget, original media decode validity, exact input ownership, M08 load and interference must be demonstrated.
Failure/limit: Parallel decoding can amplify RAM pressure or quality/synchronization divergence; does not imply worker launch.
Future owner route: M01/M04/M07/M08/M11/M55. **CONCEPT_ONLY_UNADOPTED**.

### CLASS-02: PAGE_LOCKED_STAGING

Conditional research hypothesis: Future bounded pinned-memory staging for transfers, not automatic host pressure budget.
Mandatory future owner proof: M07 host pressure and exact device/copy capabilities, pinned memory availability and current M09 composite member grant.
Failure/limit: Pinned host pages are a scarce resource; GPU access and DMA cannot be inferred from allocatable memory.
Future owner route: M07/M08/M09/M11/M12/M60. **CONCEPT_ONLY_UNADOPTED**.

### CLASS-03: ASYNC_TRANSFER_COPY_ENGINES

Conditional research hypothesis: Potential overlap of GPU transfer and compute using properly qualified asynchronous stream semantics.
Mandatory future owner proof: Exact owner-qualified CUDA runtime and hardware copy-engine facts, pinned staging, non-default streams, dependencies and measured M08 concurrency.
Failure/limit: Async API can return early while operations serialize; an advertised GPU does not prove concurrent engine availability.
Future owner route: M07/M08/M09/M17/M60. **CONCEPT_ONLY_UNADOPTED**.

### CLASS-04: BOUNDED_PREFETCH_QUEUE

Conditional research hypothesis: Speculative decoded-input/model artifact prefetch with explicit owner-scoped backpressure.
Mandatory future owner proof: M55 storage access and retention, M53/M54 model/content rights, M09 resource authority, M11 process and M12 placement proof.
Failure/limit: Prefetch can crowd out interactive work or reintroduce deleted/unlicensed bytes; not an M09 reservation.
Future owner route: M09/M11/M12/M53/M54/M55. **CONCEPT_ONLY_UNADOPTED**.

### CLASS-05: LOCALITY_TRANSFER_SHAPING

Conditional research hypothesis: Study batch sizing, read locality and reduced host/device roundtrips as nonadmitted candidates.
Mandatory future owner proof: Actually measured M08 end-to-end p50/p95 and copy/compute decomposition, exact M07 topology and M01 output fidelity.
Failure/limit: Fewer transfers may require excess RAM/VRAM, stale data, bad tail latency or silent color/precision changes.
Future owner route: M01/M07/M08/M09/M55. **CONCEPT_ONLY_UNADOPTED**.

### CLASS-06: IO_DECODE_RECOMPOSITION

Conditional research hypothesis: Investigate separate read, decode, inference and recomposition bottlenecks across video/audio/3D.
Mandatory future owner proof: M04 temporal and multimodal synchronization, M06 exact mixed lineage, M55 physical I/O and M08 workload-specific measurements.
Failure/limit: A faster pipeline can generate gaps, reorder frames or corrupt audio alignment and cannot self-accept output.
Future owner route: M01/M02/M04/M06/M08/M55. **CONCEPT_ONLY_UNADOPTED**.

### CLASS-07: PLATFORM_STORAGE_ASYNC

Conditional research hypothesis: Future platform-specific async file I/O, tiering and spill only under separate host/storage owners.
Mandatory future owner proof: M55 physical storage backend, retention/deletion and M60 process/OS API authorization; no assumed io_uring or Windows parity.
Failure/limit: Operating-system async queues vary, can exhaust file descriptors and leak tenant objects across unauthorized scopes.
Future owner route: M53/M54/M55/M60. **CONCEPT_ONLY_UNADOPTED**.

## Four unselected scheduling and transfer alternatives

### ALT-01: SEQUENTIAL_CONTROL

Research hypothesis: Measure a qualified read-decode-transfer-infer-write sequential reference before discussing optimization.
Tradeoff: Without exact matched inputs, thermal state and current interference, all speedup ratios are ungrounded.
**UNSELECTED_UNMEASURED**, selected=false, not measured.

### ALT-02: BOUNDED_CPU_PREP_PIPELINE

Research hypothesis: Potentially overlap allowed CPU preparation of a later batch with separately authorized GPU work.
Tradeoff: CPU pressure, quality, cancellation, rights, bounded queue depth and M11/M12 permission must be proven.
**UNSELECTED_UNMEASURED**, selected=false, not measured.

### ALT-03: QUALIFIED_ASYNC_GPU_STREAMS

Research hypothesis: Investigate separated device streams and host staging only after source owner grants and exact hardware capability evidence.
Tradeoff: Default stream ordering, missing pinned memory or insufficient async copy engines may completely remove overlap.
**UNSELECTED_UNMEASURED**, selected=false, not measured.

### ALT-04: STORAGE_LOCALITY_IO

Research hypothesis: Investigate M55-qualified sequential/queued reads and batching under hard latency and retention constraints.
Tradeoff: Excess prefetch, cache eviction, excessive pinned pages and physical deletion races may dominate outcomes.
**UNSELECTED_UNMEASURED**, selected=false, not measured.

## Twelve not-yet-qualified metric protocols

- `PIPELINE_END_TO_END_P50_P95` [M08]: Paired complete real media operation latency including read/decode/staging/compute/recomposition/write and cancellation. **PROTOCOL_CONCEPT_NOT_MEASURED**.
- `COPY_COMPUTE_OVERLAP_TRACE` [M07/M08]: Observed GPU transfer and compute timestamps with exact device concurrency and stream/wait semantics. **PROTOCOL_CONCEPT_NOT_MEASURED**.
- `HOST_RAM_PRESSURE` [M07/M09]: Qualified pinned/pageable RAM occupancy, queue sizes, hard memory pressure and host reclaim impact. **PROTOCOL_CONCEPT_NOT_MEASURED**.
- `GPU_VRAM_PRESSURE` [M07/M08/M09]: Actual allocated, resident and grant-backed peak VRAM with coherent member snapshots and at-use revocation. **PROTOCOL_CONCEPT_NOT_MEASURED**.
- `DISK_READ_WRITE_LATENCY` [M08/M55]: Source-qualified physical I/O bytes and latency by tier, including cold storage and restore penalties. **PROTOCOL_CONCEPT_NOT_MEASURED**.
- `CPU_DECODE_TAIL` [M08/M56]: Latency/variance and CPU utilization of exact media decode/encode/format transform per versioned workload. **PROTOCOL_CONCEPT_NOT_MEASURED**.
- `QUEUE_BACKPRESSURE` [M08/M11/M12]: Observed queue depth, cancelled work, wait time, hard owner cap and foreground priority evidence. **PROTOCOL_CONCEPT_NOT_MEASURED**.
- `THERMAL_POWER_CAUSALITY` [M07/M08/M60]: Separate observed temperature, throttle reason, valid sensors, power-limit and contamination under a qualified protocol. **PROTOCOL_CONCEPT_NOT_MEASURED**.
- `FOREGROUND_INTERFERENCE` [M08/M56]: Actual interactive application p95 and protocol-valid external workload overlap, with unknown host-wide sensors flagged. **PROTOCOL_CONCEPT_NOT_MEASURED**.
- `MEDIA_FIDELITY_CONSISTENCY` [M01/M04/M06]: Independent output quality, frame/audio sync and immutable mixed lineage retained across compared alternatives. **PROTOCOL_CONCEPT_NOT_MEASURED**.
- `WARM_COLD_AND_INVALIDATION` [M08/M13/M55]: Separate first-run prefetch cost, warmed reuse, invalidation/restoration cost and current physical-storage rights. **PROTOCOL_CONCEPT_NOT_MEASURED**.
- `PROVENANCE_SCOPE` [M02/M06/M53/M54]: Exact source, tenant, work/revision, model/driver, rights, age and responsible owner for every recorded outcome. **PROTOCOL_CONCEPT_NOT_MEASURED**.

## Twenty NEW S04 original source-routed questions: OPEN/UNRATED

These 20 questions are NEW M13 S04 research, not the original M12 110, original M13 S01 18, S02 18 or S03 20. Labels designate prospective routes, not signed owners.

### M13-S04-U01 | M07/M08

Which independently observed CUDA async copy-engine and stream capabilities, driver versions and exact hardware subjects could establish eligible overlap?

Original source role `M07`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U02 | M07/M09/M60

Which actual host pinned-memory availability and pressure proofs must constrain any future page-locked staging allocation?

Original source role `M07`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U03 | M08

Which source-qualified cold and steady-state protocols isolate CPU pre-decode, GPU copy, GPU compute, I/O and recomposition in end-to-end latency?

Original source role `M08`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U04 | M08/M56

How should missing host-wide external load sensors preserve UNKNOWN_TELEMETRY instead of falsely certifying clean interference?

Original source role `M08`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U05 | M09/M11/M12

Which all-member coherent resource lease and authenticated worker ACK must exist before prefetch or overlapped GPU processing?

Original source role `M09`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U06 | M09/M11/M12/M60

How should at-use resource revocation and process cancellation stop future queued DMA and prefetch without inventing OS termination?

Original source role `M11`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U07 | M13/M55

Who owns actual physical file reads, cache eviction, object retention and deletion while M13 only proposes read-locality research?

Original source role `INDEX`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U08 | M01/M04/M06

What exact media fidelity, frame order, sample sync and mixed reused/rebuilt lineage proofs must a future overlapped pipeline preserve?

Original source role `M01`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U09 | M53/M54/M55

Which current real tenant identity, signed rights and storage authorization prevent lookahead prefetch of revoked or confidential content?

Original source role `INDEX`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U10 | M07/M08/M10

How should hardware-specific M08 measured transfer traces remain distinct from frozen M10 advisory forecasts and unproven nominal PCIe bandwidth?

Original source role `M10`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U11 | M07/M08/M09

What measured threshold or positive source proof, rather than nominal VRAM, would qualify double buffering under exact M09 grants?

Original source role `M07`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U12 | M08/M11/M12

Which owner-defined bounded queue and backpressure semantics protect foreground interactive latency when CPU preparation outruns GPU use?

Original source role `M08`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U13 | M55/M60

Which future physical-storage and OS contracts would authorize platform-specific asynchronous I/O without assuming cross-platform API parity?

Original source role `INDEX`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U14 | M02/M06/M13

How will M02 semantic work identity and M06 revision/attempt receipts fence stale prefetched data across edits, cancellation and branch motion?

Original source role `M02`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U15 | M07/M08/M09

What actual copy-engine, NUMA, multi-GPU and topology qualifications avoid claiming peer-to-peer transfer on unsupported paths?

Original source role `M07`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U16 | M08/M56

Which exact observed trace can distinguish stream enqueue latency from completion and expose implicit default-stream synchronization?

Original source role `M08`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U17 | M01/M08

How could throughput-oriented batching be rejected when it worsens tail latency or M01 quality despite favorable average GPU utilization?

Original source role `M01`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U18 | M07/M08/M60

Which separately observed thermal, power and device-throttle causes must be retained rather than attributing all slowdowns to I/O?

Original source role `M07`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U19 | M13/M14/M16/M17

How must exact model weights, workflow/codec/toolchain versions and S02 selected-none backend state condition any hypothetical pre-decode overlap?

Original source role `S02`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

### M13-S04-U20 | M09/M11/M12/M54/M60

What complete H01–H04 authenticated source receipt bundle and OS principal proof would be necessary before a future real S04 experiment?

Original source role `D01`; risk UNRATED; qualified owner answer NOT_RECEIVED; **OPEN_UNRATED_PENDING_QUALIFIED_OWNER**.

## Sixteen NEW future hostile/negative designs: SPECIFIED, NOT EXECUTED

### M13-S04-N01: ASYNC_ENQUEUE_NOT_COMPLETE

Concepts: CLASS-03
Hypothetical trigger: A host call returns early but DMA and GPU compute serialize because default stream ordering remains active.
Desired future non-authorizing oracle: `NO_FALSE_CONCURRENT_EXECUTION`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N02: MISSING_COPY_ENGINE

Concepts: CLASS-03
Hypothetical trigger: Nominal CUDA support is mistaken for an independently observed hardware asynchronous copy engine.
Desired future non-authorizing oracle: `NO_OVERLAP_CAPABILITY_BY_GPU_BRAND`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N03: UNPINNED_HOST_MEMORY

Concepts: CLASS-02, CLASS-03
Hypothetical trigger: A proposed async transfer uses pageable memory and no source-qualified staging eligibility.
Desired future non-authorizing oracle: `NO_ASSUMED_PINNED_TRANSFER`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N04: EXCESSIVE_PAGE_LOCKING

Concepts: CLASS-02
Hypothetical trigger: Too many host pages are pinned and foreground RAM pressure or paging severely increases.
Desired future non-authorizing oracle: `NO_UNBOUNDED_HOST_STAGING`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N05: PREFETCH_WITHOUT_LEASE

Concepts: CLASS-04
Hypothetical trigger: Future prefetch starts device work using a warm residency hint without coherent M09 lease or genuine M11 owner ACK.
Desired future non-authorizing oracle: `NO_GPU_ACTION_FROM_HINT`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N06: REVOKED_WORK_QUEUED

Concepts: CLASS-03, CLASS-04
Hypothetical trigger: A complete grant expires after enqueue but before queued work begins and at-use fencing is absent.
Desired future non-authorizing oracle: `NO_EXECUTION_FROM_STALE_LEASE`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N07: TENANT_PREFETCH

Concepts: CLASS-04, CLASS-07
Hypothetical trigger: Storage lookahead reads another tenant's identical-content object without qualified current authorization.
Desired future non-authorizing oracle: `NO_CROSS_TENANT_READ`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N08: DELETED_OBJECT_PREFETCH

Concepts: CLASS-04, CLASS-07
Hypothetical trigger: Previously eligible cache object is physically deleted or rights-revoked while I/O remains queued.
Desired future non-authorizing oracle: `NO_STALE_STORAGE_READ`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N09: SILENT_AUDIO_REORDER

Concepts: CLASS-06
Hypothetical trigger: Concurrent decode/recomposition reorders audio samples or image frames despite faster wall-clock time.
Desired future non-authorizing oracle: `NO_FIDELITY_BY_THROUGHPUT`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N10: QUALITY_DOWNGRADE

Concepts: CLASS-05
Hypothetical trigger: A batching or transfer shortcut changes precision/color encoding but an average speedup is reported.
Desired future non-authorizing oracle: `NO_M01_QUALITY_GATE_BYPASS`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N11: MISSING_INTERFERENCE_SENSOR

Concepts: CLASS-01, CLASS-06
Hypothetical trigger: Benchmark samples look fast even though host-wide interactive interference telemetry is UNKNOWN.
Desired future non-authorizing oracle: `NO_UNVERIFIED_VALID_BENCHMARK`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N12: THERMAL_CONFUSION

Concepts: CLASS-05
Hypothetical trigger: GPU power limit and thermal throttling are conflated with storage stalls to justify a transfer strategy.
Desired future non-authorizing oracle: `NO_CAUSAL_SPEEDUP_CLAIM`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N13: QUEUE_DEADLOCK

Concepts: CLASS-01, CLASS-04
Hypothetical trigger: The bounded prefetch queue holds stale work after cancellation and cannot recover backpressure.
Desired future non-authorizing oracle: `NO_UNBOUNDED_OR_UNRECONCILED_QUEUE`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N14: IMPLICIT_LATEST_EDIT

Concepts: CLASS-04, CLASS-06
Hypothetical trigger: A concurrent graph revision moves a branch alias while decoded frames still reference an older accepted work attempt.
Desired future non-authorizing oracle: `NO_IMPLICIT_LATEST_PRODUCTION_REUSE`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N15: PLATFORM_API_INFERENCE

Concepts: CLASS-07
Hypothetical trigger: A Linux-specific async I/O behavior is assumed to provide equivalent safety or performance on Windows.
Desired future non-authorizing oracle: `NO_UNQUALIFIED_CROSS_PLATFORM_RUNTIME`. **SPECIFIED_NOT_EXECUTED**.

### M13-S04-N16: FALSE_S04_EXECUTION

Concepts: CLASS-03, CLASS-07
Hypothetical trigger: A source-only synthetic checklist claims a real GPU benchmark, storage operation or independent owner contract passed.
Desired future non-authorizing oracle: `NO_DOCUMENTARY_TEST_AS_RUNTIME_PROOF`. **SPECIFIED_NOT_EXECUTED**.

## Safety invariants and STOP

The S04 comparison must separately bind accepted M02/M06 work and materialization identities, M07 genuine hardware declarations and M08 independent correctness/interference protocols, M09 complete-member grants, M11 process and M12 placement, M53/M54 present-time principal and rights, M55 physical storage and M60 OS rights. Source-only true/false mock flags are not signed owner receipts. No metric here is a measured latency or a default numeric policy.

**STOP:** No actual CPU/GPU overlap, CUDA stream, pinned allocation, GPU or CPU probe, network, native extension, model load, M55 physical I/O or GC, M09 grant, M11 process, M12 placement, M10 implementation, vendor selection, resource rights, measured speedup, module freeze, authentic independent owner approval or M13 runtime is authorized. H01-H04 OPEN HIGH_FOR_FUTURE_FREEZE; B DIRECTION_ONLY; C01 UNADOPTED_NOT_FROZEN. All original M12/H03 and new M13 S01/S02/S03/S04 real integration negatives remain SPECIFIED_NOT_EXECUTED.

## Appendix A: canonical original machine packet

```json
{
  "schema": "iris-m13-s04-source-research-v0.1",
  "workOrder": "IRIS-WO-0048",
  "issue": 155,
  "module": "M13",
  "session": "S04",
  "baseSha": "c73b524e90a433d3476521d7a4b47f9451e3d32c",
  "baseTreeSha": "489187561ab7c581c932a4721edfcadf9ac7dd9e",
  "asOf": "2026-09-27",
  "status": "SOURCE_ONLY_NO_HARDWARE_OR_IO_RUNTIME",
  "qualifiedOwnerApprovals": 0,
  "selectedPipeline": "NONE",
  "measuredHardware": "NONE",
  "ioExecuted": false,
  "realGpuRuns": 0,
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
    "s03FutureNegatives": "16_NOT_EXECUTED"
  },
  "m12OriginalQuestions": "110_OPEN",
  "m12OriginalFutureNegatives": "80_SPECIFIED_NOT_EXECUTED",
  "sourceDocs": [
    {
      "role": "INDEX",
      "path": "planning/MASTER-MODULE-INDEX.md",
      "sha": "19c8ff6126748cb89e53108bdff8289322071970",
      "anchor": "S04 — S04 CPU/GPU overlap, I/O scheduling and storage efficiency"
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
      "anchor": "M09 is the provider-neutral resource-state"
    },
    {
      "role": "M10",
      "path": "planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
      "sha": "f69ec3e3eab24b47c0e31832d64d9ab9cce21828",
      "anchor": "m10-contract-v1.0"
    },
    {
      "role": "M11",
      "path": "planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
      "sha": "41ab89727c7be14e35e2481aefbd97a0cb81cb48",
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
      "path": "planning/research/M13-S01-WARM-MODEL-CACHE-LOCALITY.md",
      "sha": "7701c1e744d2b459d2f6bb4fa754352374fb67fd",
      "anchor": "C03_DEVICE_RESIDENCY_HINT"
    },
    {
      "role": "S02",
      "path": "planning/research/M13-S02-COMPILATION-ATTENTION-BACKENDS.md",
      "sha": "33736cc40214af1ee25586d6c94789d8c0d95739",
      "anchor": "AUTO_SDPA"
    },
    {
      "role": "S03",
      "path": "planning/research/M13-S03-INTERMEDIATE-REUSE-GENERATION-DELTA.md",
      "sha": "96a9952086300a1ae2d46195bd7dc6d50dea06ba",
      "anchor": "Seven unadopted reuse concepts"
    },
    {
      "role": "M01",
      "path": "docs/M01-QUALITY-KERNEL.md",
      "sha": "930af57944fa83c44745873c42eb3a7740972ee6",
      "anchor": "m01-contract-v1.0"
    },
    {
      "role": "M02",
      "path": "planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
      "sha": "a85d80ab3bb5f4bdc9be915a59caa92569d66af4",
      "anchor": "semantic reuse requires explicit reuse class/admission"
    },
    {
      "role": "M06",
      "path": "planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
      "sha": "18b5303d1e36ef60de17b42dd9e2c371ecf4f191",
      "anchor": "Digest equality proves byte equality under the declared digest domain only."
    },
    {
      "role": "D01",
      "path": ".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json",
      "sha": "30cc56a2dd34a8c45cfb96f0a900cafbdd2717bb",
      "anchor": "B_FUTURE_OWNER_RECEIPT"
    }
  ],
  "externalReferences": [
    {
      "id": "NVIDIA_CUDA_BPG",
      "url": "https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/",
      "publisher": "NVIDIA",
      "checkedOn": "2026-09-27",
      "status": "MUTABLE_OFFICIAL_REFERENCE_NOT_GPU_OR_OS_ATTESTATION",
      "scope": "NVIDIA documents host pinned memory as a prerequisite for async H2D/D2H overlap with GPU kernels in separate non-default streams on capable devices; actual async copy engine support is device-dependent, excess pinning can harm host performance and nominal API availability proves no throughput."
    }
  ],
  "concepts": [
    {
      "id": "CLASS-01",
      "name": "HOST_PREPROCESS_WORKSET",
      "hypothesis": "Future CPU-side decoding, validation and transformation before GPU work.",
      "requiredOwnerProof": "CPU cores and host RAM budget, original media decode validity, exact input ownership, M08 load and interference must be demonstrated.",
      "failureBoundary": "Parallel decoding can amplify RAM pressure or quality/synchronization divergence; does not imply worker launch.",
      "originalOwnerRoute": "M01/M04/M07/M08/M11/M55",
      "status": "CONCEPT_ONLY_UNADOPTED"
    },
    {
      "id": "CLASS-02",
      "name": "PAGE_LOCKED_STAGING",
      "hypothesis": "Future bounded pinned-memory staging for transfers, not automatic host pressure budget.",
      "requiredOwnerProof": "M07 host pressure and exact device/copy capabilities, pinned memory availability and current M09 composite member grant.",
      "failureBoundary": "Pinned host pages are a scarce resource; GPU access and DMA cannot be inferred from allocatable memory.",
      "originalOwnerRoute": "M07/M08/M09/M11/M12/M60",
      "status": "CONCEPT_ONLY_UNADOPTED"
    },
    {
      "id": "CLASS-03",
      "name": "ASYNC_TRANSFER_COPY_ENGINES",
      "hypothesis": "Potential overlap of GPU transfer and compute using properly qualified asynchronous stream semantics.",
      "requiredOwnerProof": "Exact owner-qualified CUDA runtime and hardware copy-engine facts, pinned staging, non-default streams, dependencies and measured M08 concurrency.",
      "failureBoundary": "Async API can return early while operations serialize; an advertised GPU does not prove concurrent engine availability.",
      "originalOwnerRoute": "M07/M08/M09/M17/M60",
      "status": "CONCEPT_ONLY_UNADOPTED"
    },
    {
      "id": "CLASS-04",
      "name": "BOUNDED_PREFETCH_QUEUE",
      "hypothesis": "Speculative decoded-input/model artifact prefetch with explicit owner-scoped backpressure.",
      "requiredOwnerProof": "M55 storage access and retention, M53/M54 model/content rights, M09 resource authority, M11 process and M12 placement proof.",
      "failureBoundary": "Prefetch can crowd out interactive work or reintroduce deleted/unlicensed bytes; not an M09 reservation.",
      "originalOwnerRoute": "M09/M11/M12/M53/M54/M55",
      "status": "CONCEPT_ONLY_UNADOPTED"
    },
    {
      "id": "CLASS-05",
      "name": "LOCALITY_TRANSFER_SHAPING",
      "hypothesis": "Study batch sizing, read locality and reduced host/device roundtrips as nonadmitted candidates.",
      "requiredOwnerProof": "Actually measured M08 end-to-end p50/p95 and copy/compute decomposition, exact M07 topology and M01 output fidelity.",
      "failureBoundary": "Fewer transfers may require excess RAM/VRAM, stale data, bad tail latency or silent color/precision changes.",
      "originalOwnerRoute": "M01/M07/M08/M09/M55",
      "status": "CONCEPT_ONLY_UNADOPTED"
    },
    {
      "id": "CLASS-06",
      "name": "IO_DECODE_RECOMPOSITION",
      "hypothesis": "Investigate separate read, decode, inference and recomposition bottlenecks across video/audio/3D.",
      "requiredOwnerProof": "M04 temporal and multimodal synchronization, M06 exact mixed lineage, M55 physical I/O and M08 workload-specific measurements.",
      "failureBoundary": "A faster pipeline can generate gaps, reorder frames or corrupt audio alignment and cannot self-accept output.",
      "originalOwnerRoute": "M01/M02/M04/M06/M08/M55",
      "status": "CONCEPT_ONLY_UNADOPTED"
    },
    {
      "id": "CLASS-07",
      "name": "PLATFORM_STORAGE_ASYNC",
      "hypothesis": "Future platform-specific async file I/O, tiering and spill only under separate host/storage owners.",
      "requiredOwnerProof": "M55 physical storage backend, retention/deletion and M60 process/OS API authorization; no assumed io_uring or Windows parity.",
      "failureBoundary": "Operating-system async queues vary, can exhaust file descriptors and leak tenant objects across unauthorized scopes.",
      "originalOwnerRoute": "M53/M54/M55/M60",
      "status": "CONCEPT_ONLY_UNADOPTED"
    }
  ],
  "alternatives": [
    {
      "id": "ALT-01",
      "name": "SEQUENTIAL_CONTROL",
      "hypothesis": "Measure a qualified read-decode-transfer-infer-write sequential reference before discussing optimization.",
      "tradeoff": "Without exact matched inputs, thermal state and current interference, all speedup ratios are ungrounded.",
      "status": "UNSELECTED_UNMEASURED",
      "selected": false
    },
    {
      "id": "ALT-02",
      "name": "BOUNDED_CPU_PREP_PIPELINE",
      "hypothesis": "Potentially overlap allowed CPU preparation of a later batch with separately authorized GPU work.",
      "tradeoff": "CPU pressure, quality, cancellation, rights, bounded queue depth and M11/M12 permission must be proven.",
      "status": "UNSELECTED_UNMEASURED",
      "selected": false
    },
    {
      "id": "ALT-03",
      "name": "QUALIFIED_ASYNC_GPU_STREAMS",
      "hypothesis": "Investigate separated device streams and host staging only after source owner grants and exact hardware capability evidence.",
      "tradeoff": "Default stream ordering, missing pinned memory or insufficient async copy engines may completely remove overlap.",
      "status": "UNSELECTED_UNMEASURED",
      "selected": false
    },
    {
      "id": "ALT-04",
      "name": "STORAGE_LOCALITY_IO",
      "hypothesis": "Investigate M55-qualified sequential/queued reads and batching under hard latency and retention constraints.",
      "tradeoff": "Excess prefetch, cache eviction, excessive pinned pages and physical deletion races may dominate outcomes.",
      "status": "UNSELECTED_UNMEASURED",
      "selected": false
    }
  ],
  "metricProtocols": [
    {
      "id": "PIPELINE_END_TO_END_P50_P95",
      "ownerRoute": "M08",
      "proposedProtocol": "Paired complete real media operation latency including read/decode/staging/compute/recomposition/write and cancellation.",
      "status": "PROTOCOL_CONCEPT_NOT_MEASURED"
    },
    {
      "id": "COPY_COMPUTE_OVERLAP_TRACE",
      "ownerRoute": "M07/M08",
      "proposedProtocol": "Observed GPU transfer and compute timestamps with exact device concurrency and stream/wait semantics.",
      "status": "PROTOCOL_CONCEPT_NOT_MEASURED"
    },
    {
      "id": "HOST_RAM_PRESSURE",
      "ownerRoute": "M07/M09",
      "proposedProtocol": "Qualified pinned/pageable RAM occupancy, queue sizes, hard memory pressure and host reclaim impact.",
      "status": "PROTOCOL_CONCEPT_NOT_MEASURED"
    },
    {
      "id": "GPU_VRAM_PRESSURE",
      "ownerRoute": "M07/M08/M09",
      "proposedProtocol": "Actual allocated, resident and grant-backed peak VRAM with coherent member snapshots and at-use revocation.",
      "status": "PROTOCOL_CONCEPT_NOT_MEASURED"
    },
    {
      "id": "DISK_READ_WRITE_LATENCY",
      "ownerRoute": "M08/M55",
      "proposedProtocol": "Source-qualified physical I/O bytes and latency by tier, including cold storage and restore penalties.",
      "status": "PROTOCOL_CONCEPT_NOT_MEASURED"
    },
    {
      "id": "CPU_DECODE_TAIL",
      "ownerRoute": "M08/M56",
      "proposedProtocol": "Latency/variance and CPU utilization of exact media decode/encode/format transform per versioned workload.",
      "status": "PROTOCOL_CONCEPT_NOT_MEASURED"
    },
    {
      "id": "QUEUE_BACKPRESSURE",
      "ownerRoute": "M08/M11/M12",
      "proposedProtocol": "Observed queue depth, cancelled work, wait time, hard owner cap and foreground priority evidence.",
      "status": "PROTOCOL_CONCEPT_NOT_MEASURED"
    },
    {
      "id": "THERMAL_POWER_CAUSALITY",
      "ownerRoute": "M07/M08/M60",
      "proposedProtocol": "Separate observed temperature, throttle reason, valid sensors, power-limit and contamination under a qualified protocol.",
      "status": "PROTOCOL_CONCEPT_NOT_MEASURED"
    },
    {
      "id": "FOREGROUND_INTERFERENCE",
      "ownerRoute": "M08/M56",
      "proposedProtocol": "Actual interactive application p95 and protocol-valid external workload overlap, with unknown host-wide sensors flagged.",
      "status": "PROTOCOL_CONCEPT_NOT_MEASURED"
    },
    {
      "id": "MEDIA_FIDELITY_CONSISTENCY",
      "ownerRoute": "M01/M04/M06",
      "proposedProtocol": "Independent output quality, frame/audio sync and immutable mixed lineage retained across compared alternatives.",
      "status": "PROTOCOL_CONCEPT_NOT_MEASURED"
    },
    {
      "id": "WARM_COLD_AND_INVALIDATION",
      "ownerRoute": "M08/M13/M55",
      "proposedProtocol": "Separate first-run prefetch cost, warmed reuse, invalidation/restoration cost and current physical-storage rights.",
      "status": "PROTOCOL_CONCEPT_NOT_MEASURED"
    },
    {
      "id": "PROVENANCE_SCOPE",
      "ownerRoute": "M02/M06/M53/M54",
      "proposedProtocol": "Exact source, tenant, work/revision, model/driver, rights, age and responsible owner for every recorded outcome.",
      "status": "PROTOCOL_CONCEPT_NOT_MEASURED"
    }
  ],
  "questions": [
    {
      "id": "M13-S04-U01",
      "originalOwnerRoute": "M07/M08",
      "question": "Which independently observed CUDA async copy-engine and stream capabilities, driver versions and exact hardware subjects could establish eligible overlap?",
      "sourceRole": "M07",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U02",
      "originalOwnerRoute": "M07/M09/M60",
      "question": "Which actual host pinned-memory availability and pressure proofs must constrain any future page-locked staging allocation?",
      "sourceRole": "M07",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U03",
      "originalOwnerRoute": "M08",
      "question": "Which source-qualified cold and steady-state protocols isolate CPU pre-decode, GPU copy, GPU compute, I/O and recomposition in end-to-end latency?",
      "sourceRole": "M08",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U04",
      "originalOwnerRoute": "M08/M56",
      "question": "How should missing host-wide external load sensors preserve UNKNOWN_TELEMETRY instead of falsely certifying clean interference?",
      "sourceRole": "M08",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U05",
      "originalOwnerRoute": "M09/M11/M12",
      "question": "Which all-member coherent resource lease and authenticated worker ACK must exist before prefetch or overlapped GPU processing?",
      "sourceRole": "M09",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U06",
      "originalOwnerRoute": "M09/M11/M12/M60",
      "question": "How should at-use resource revocation and process cancellation stop future queued DMA and prefetch without inventing OS termination?",
      "sourceRole": "M11",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U07",
      "originalOwnerRoute": "M13/M55",
      "question": "Who owns actual physical file reads, cache eviction, object retention and deletion while M13 only proposes read-locality research?",
      "sourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U08",
      "originalOwnerRoute": "M01/M04/M06",
      "question": "What exact media fidelity, frame order, sample sync and mixed reused/rebuilt lineage proofs must a future overlapped pipeline preserve?",
      "sourceRole": "M01",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U09",
      "originalOwnerRoute": "M53/M54/M55",
      "question": "Which current real tenant identity, signed rights and storage authorization prevent lookahead prefetch of revoked or confidential content?",
      "sourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U10",
      "originalOwnerRoute": "M07/M08/M10",
      "question": "How should hardware-specific M08 measured transfer traces remain distinct from frozen M10 advisory forecasts and unproven nominal PCIe bandwidth?",
      "sourceRole": "M10",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U11",
      "originalOwnerRoute": "M07/M08/M09",
      "question": "What measured threshold or positive source proof, rather than nominal VRAM, would qualify double buffering under exact M09 grants?",
      "sourceRole": "M07",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U12",
      "originalOwnerRoute": "M08/M11/M12",
      "question": "Which owner-defined bounded queue and backpressure semantics protect foreground interactive latency when CPU preparation outruns GPU use?",
      "sourceRole": "M08",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U13",
      "originalOwnerRoute": "M55/M60",
      "question": "Which future physical-storage and OS contracts would authorize platform-specific asynchronous I/O without assuming cross-platform API parity?",
      "sourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U14",
      "originalOwnerRoute": "M02/M06/M13",
      "question": "How will M02 semantic work identity and M06 revision/attempt receipts fence stale prefetched data across edits, cancellation and branch motion?",
      "sourceRole": "M02",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U15",
      "originalOwnerRoute": "M07/M08/M09",
      "question": "What actual copy-engine, NUMA, multi-GPU and topology qualifications avoid claiming peer-to-peer transfer on unsupported paths?",
      "sourceRole": "M07",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U16",
      "originalOwnerRoute": "M08/M56",
      "question": "Which exact observed trace can distinguish stream enqueue latency from completion and expose implicit default-stream synchronization?",
      "sourceRole": "M08",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U17",
      "originalOwnerRoute": "M01/M08",
      "question": "How could throughput-oriented batching be rejected when it worsens tail latency or M01 quality despite favorable average GPU utilization?",
      "sourceRole": "M01",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U18",
      "originalOwnerRoute": "M07/M08/M60",
      "question": "Which separately observed thermal, power and device-throttle causes must be retained rather than attributing all slowdowns to I/O?",
      "sourceRole": "M07",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U19",
      "originalOwnerRoute": "M13/M14/M16/M17",
      "question": "How must exact model weights, workflow/codec/toolchain versions and S02 selected-none backend state condition any hypothetical pre-decode overlap?",
      "sourceRole": "S02",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    },
    {
      "id": "M13-S04-U20",
      "originalOwnerRoute": "M09/M11/M12/M54/M60",
      "question": "What complete H01–H04 authenticated source receipt bundle and OS principal proof would be necessary before a future real S04 experiment?",
      "sourceRole": "D01",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "answer": null
    }
  ],
  "negativeCases": [
    {
      "id": "M13-S04-N01",
      "label": "ASYNC_ENQUEUE_NOT_COMPLETE",
      "classIds": [
        "CLASS-03"
      ],
      "trigger": "A host call returns early but DMA and GPU compute serialize because default stream ordering remains active.",
      "futureNonAuthorizingOracle": "NO_FALSE_CONCURRENT_EXECUTION",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N02",
      "label": "MISSING_COPY_ENGINE",
      "classIds": [
        "CLASS-03"
      ],
      "trigger": "Nominal CUDA support is mistaken for an independently observed hardware asynchronous copy engine.",
      "futureNonAuthorizingOracle": "NO_OVERLAP_CAPABILITY_BY_GPU_BRAND",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N03",
      "label": "UNPINNED_HOST_MEMORY",
      "classIds": [
        "CLASS-02",
        "CLASS-03"
      ],
      "trigger": "A proposed async transfer uses pageable memory and no source-qualified staging eligibility.",
      "futureNonAuthorizingOracle": "NO_ASSUMED_PINNED_TRANSFER",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N04",
      "label": "EXCESSIVE_PAGE_LOCKING",
      "classIds": [
        "CLASS-02"
      ],
      "trigger": "Too many host pages are pinned and foreground RAM pressure or paging severely increases.",
      "futureNonAuthorizingOracle": "NO_UNBOUNDED_HOST_STAGING",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N05",
      "label": "PREFETCH_WITHOUT_LEASE",
      "classIds": [
        "CLASS-04"
      ],
      "trigger": "Future prefetch starts device work using a warm residency hint without coherent M09 lease or genuine M11 owner ACK.",
      "futureNonAuthorizingOracle": "NO_GPU_ACTION_FROM_HINT",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N06",
      "label": "REVOKED_WORK_QUEUED",
      "classIds": [
        "CLASS-03",
        "CLASS-04"
      ],
      "trigger": "A complete grant expires after enqueue but before queued work begins and at-use fencing is absent.",
      "futureNonAuthorizingOracle": "NO_EXECUTION_FROM_STALE_LEASE",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N07",
      "label": "TENANT_PREFETCH",
      "classIds": [
        "CLASS-04",
        "CLASS-07"
      ],
      "trigger": "Storage lookahead reads another tenant's identical-content object without qualified current authorization.",
      "futureNonAuthorizingOracle": "NO_CROSS_TENANT_READ",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N08",
      "label": "DELETED_OBJECT_PREFETCH",
      "classIds": [
        "CLASS-04",
        "CLASS-07"
      ],
      "trigger": "Previously eligible cache object is physically deleted or rights-revoked while I/O remains queued.",
      "futureNonAuthorizingOracle": "NO_STALE_STORAGE_READ",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N09",
      "label": "SILENT_AUDIO_REORDER",
      "classIds": [
        "CLASS-06"
      ],
      "trigger": "Concurrent decode/recomposition reorders audio samples or image frames despite faster wall-clock time.",
      "futureNonAuthorizingOracle": "NO_FIDELITY_BY_THROUGHPUT",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N10",
      "label": "QUALITY_DOWNGRADE",
      "classIds": [
        "CLASS-05"
      ],
      "trigger": "A batching or transfer shortcut changes precision/color encoding but an average speedup is reported.",
      "futureNonAuthorizingOracle": "NO_M01_QUALITY_GATE_BYPASS",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N11",
      "label": "MISSING_INTERFERENCE_SENSOR",
      "classIds": [
        "CLASS-01",
        "CLASS-06"
      ],
      "trigger": "Benchmark samples look fast even though host-wide interactive interference telemetry is UNKNOWN.",
      "futureNonAuthorizingOracle": "NO_UNVERIFIED_VALID_BENCHMARK",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N12",
      "label": "THERMAL_CONFUSION",
      "classIds": [
        "CLASS-05"
      ],
      "trigger": "GPU power limit and thermal throttling are conflated with storage stalls to justify a transfer strategy.",
      "futureNonAuthorizingOracle": "NO_CAUSAL_SPEEDUP_CLAIM",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N13",
      "label": "QUEUE_DEADLOCK",
      "classIds": [
        "CLASS-01",
        "CLASS-04"
      ],
      "trigger": "The bounded prefetch queue holds stale work after cancellation and cannot recover backpressure.",
      "futureNonAuthorizingOracle": "NO_UNBOUNDED_OR_UNRECONCILED_QUEUE",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N14",
      "label": "IMPLICIT_LATEST_EDIT",
      "classIds": [
        "CLASS-04",
        "CLASS-06"
      ],
      "trigger": "A concurrent graph revision moves a branch alias while decoded frames still reference an older accepted work attempt.",
      "futureNonAuthorizingOracle": "NO_IMPLICIT_LATEST_PRODUCTION_REUSE",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N15",
      "label": "PLATFORM_API_INFERENCE",
      "classIds": [
        "CLASS-07"
      ],
      "trigger": "A Linux-specific async I/O behavior is assumed to provide equivalent safety or performance on Windows.",
      "futureNonAuthorizingOracle": "NO_UNQUALIFIED_CROSS_PLATFORM_RUNTIME",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "M13-S04-N16",
      "label": "FALSE_S04_EXECUTION",
      "classIds": [
        "CLASS-03",
        "CLASS-07"
      ],
      "trigger": "A source-only synthetic checklist claims a real GPU benchmark, storage operation or independent owner contract passed.",
      "futureNonAuthorizingOracle": "NO_DOCUMENTARY_TEST_AS_RUNTIME_PROOF",
      "status": "SPECIFIED_NOT_EXECUTED"
    }
  ],
  "stop": "No actual CPU/GPU overlap, CUDA stream, pinned allocation, GPU or CPU probe, network, native extension, model load, M55 physical I/O or GC, M09 grant, M11 process, M12 placement, M10 implementation, vendor selection, resource rights, measured speedup, module freeze, authentic independent owner approval or M13 runtime is authorized. H01-H04 OPEN HIGH_FOR_FUTURE_FREEZE; B DIRECTION_ONLY; C01 UNADOPTED_NOT_FROZEN. All original M12/H03 and new M13 S01/S02/S03/S04 real integration negatives remain SPECIFIED_NOT_EXECUTED."
}
```
