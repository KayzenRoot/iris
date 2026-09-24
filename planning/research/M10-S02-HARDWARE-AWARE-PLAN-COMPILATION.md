# M10 S02 — Hardware-aware plan compilation: planning research

Status: `CANDIDATE_COMPLETE_PENDING_GOVERNANCE`
Work Order: [Issue #68](https://github.com/KayzenRoot/iris/issues/68)
S02 session base: `fc1a3c954a1629b9e9a4c45c4e557a7832c290d7`
Exact-main Governance on session base: `36031548275 / 107741264931` — PASS
Research checked: 2026-09-24
Implementation authority: **NOT ADMITTED**

## Purpose

Define the evidence and authority boundary between M10 workload signatures and M02-compatible execution-plan alternatives. This session does not implement planning, select a device, reserve resources, start a worker or compile a provider workflow.

## Research findings

### Allocator memory and device-global free memory answer different questions

PyTorch documents `memory_allocated()` as tensor memory and `memory_reserved()` as memory managed by its caching allocator. Unused memory retained by the allocator can still appear as used in `nvidia-smi`; allocator statistics also vary with allocator backend. Its `mem_get_info` API reports global free/total memory from CUDA. See [PyTorch CUDA semantics](https://docs.pytorch.org/docs/main/notes/cuda.html) and [PyTorch CUDA API](https://docs.pytorch.org/docs/stable/cuda.html).

**Design implication (inference):** a feasibility decision must retain measurement source and scope. M10 cannot subtract allocator-reserved bytes from device-global free memory, or combine snapshots from different scopes/times, unless an owner-approved reconciliation contract proves that operation.

### Runtime capability may cover only part of a workload graph

ONNX Runtime's Execution Provider framework uses `GetCapability()` to identify supported nodes or subgraphs. Provider order can permit lower-priority providers to execute nodes the preferred provider cannot run. See [ONNX Runtime Execution Providers](https://onnxruntime.ai/docs/execution-providers/).

**Design implication (inference):** provider presence or support for one subgraph does not prove that a complete M02 workload is feasible on a desired runtime. M10 should consume a versioned whole-request compatibility/compilation receipt from the owning M16 boundary; it must not infer full coverage from a model name or partial capability list.

### Hardware partition identity changes usable capacity

NVIDIA MIG partitions supported GPUs into isolated instances with dedicated compute and memory. The guide identifies devices using instance profiles that include compute and memory slices, and documents driver-generation caveats for enumeration. See [NVIDIA MIG User Guide](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/latest/) and [MIG Device Names](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/mig-device-names.html).

**Design implication (inference):** when partitioning is present, the parent GPU model or total VRAM does not fully describe the execution-visible target. M10 consumes the exact M07 instance/profile/runtime identity and current visibility by reference; it does not create or reconfigure partitions.

### Preferred allocation does not equal final placement

Kubernetes documents that a device plugin's `GetPreferredAllocation` may help the device manager but does not guarantee the ultimate allocation. Dynamic Resource Allocation lets the scheduler select devices satisfying a request and schedule the workload onto a node with access. See [Kubernetes Device Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/) and [DRA API Objects](https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/dra-api/).

**Design implication (inference):** a planner's hardware-aware alternatives are constraints/advice for the placement owner. M10 must not report that a specific target is allocated, committed or reserved before M12/M09 authority returns exact evidence.

These vendor/platform examples inform boundary design only. They do not make PyTorch, ONNX Runtime, MIG or Kubernetes an IRIS dependency or selected implementation.

## S02 compilation boundary

The planning candidate uses:

- M02's exact production graph/revision and its own plan/request contract;
- M01 quality obligations and M03 protected semantic constraints;
- M07 immutable hardware/runtime facts and explicit projection omissions;
- M08 capability evidence pinned to the exact workload/hardware/runtime/benchmark scope;
- M09 resource snapshots, claims, leases and owner-admitted shape options;
- M14 and M16 compatibility/fitness references where applicable.

M10 first verifies reference, schema, scope and evidence coherence; then applies hard admissibility gates; then builds a bounded set of alternatives that M02 can accept. Preference ranking and prediction thresholds are deferred to S03/S04. Final M09 revalidation, reservation, placement, worker dispatch and provider compilation remain at their owning module boundaries.

No fixed memory margin, risk percentage, batch cap, precision switch, target device or tie-break policy is selected here.

## Candidate alternative content (conceptual only)

This list describes what a reviewed candidate needs to account for; it is not a proposed serialized schema:

- exact M02 graph, target revision and plan-contract references;
- pinned workload-signature revision;
- mandatory M01/M03 requirement references;
- M07 hardware/runtime/driver and visible partition references;
- M08 capability-envelope evidence and its benchmark/workload binding;
- M09 snapshot/claim/shape-option references with freshness and state;
- applicable M14/M16 compatibility references;
- hard constraints and why each alternative passed or failed them;
- explicit evidence scope, capture time/window and uncertainty;
- M02 acceptance result or an explicit indeterminate/no-safe-plan result.

## Provisional S02 requirements

- Unknown, stale, conflicted, quarantined or omitted mandatory evidence cannot establish positive feasibility.
- Evidence sources and scopes remain distinct; no arithmetic combines unlike memory facts by guess.
- M08 evidence must be bound to exact compatible hardware/runtime and workload scope.
- Hardware partitions/virtual devices are distinct versioned targets where the owner exposes them.
- M02 graph causality, request coverage, dependencies and permitted side effects cannot be widened by M10.
- M01/M03 obligations are non-negotiable hard constraints.
- M09 alone grants resource leases/reservations and owns resource-state transitions.
- M12 alone makes placement decisions; a preference is never represented as final assignment.
- M11 alone controls worker/process lifecycle.
- M16 alone performs concrete provider/workflow compilation.
- A provider capability subset does not prove complete-workflow support.
- S03 owns predictive risk budgets/calibration; S04 owns named policy preferences/ranking.
- No eligible alternative yields explicit no-safe-plan/indeterminate outcome with blocking evidence.
- The decision explanation binds exact input revisions and lists accepted/rejected alternatives.
- Synthetic fixtures remain marked synthetic and cannot claim physical resource feasibility.
- No product/runtime/test code or implementation authority is introduced.

## Sources

- [PyTorch — CUDA semantics](https://docs.pytorch.org/docs/main/notes/cuda.html)
- [PyTorch — CUDA API](https://docs.pytorch.org/docs/stable/cuda.html)
- [ONNX Runtime — Execution Providers](https://onnxruntime.ai/docs/execution-providers/)
- [NVIDIA — MIG User Guide](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/latest/)
- [NVIDIA — MIG Device Names](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/mig-device-names.html)
- [Kubernetes — Device Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)
- [Kubernetes — DRA API Objects](https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/dra-api/)

## Gate

This S02 package is a planning candidate. Continue S03-S05 and the full M10 planning gates before contract freeze or implementation admission. M10 product/runtime implementation remains **NOT ADMITTED and NOT STARTED**.
