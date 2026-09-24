# M10 S01 — Workload Signature Engine: planning research

Status: `COMPLETE_FOR_MODULE_PLANNING`
Work Order: [Issue #68](https://github.com/KayzenRoot/iris/issues/68)
Authorized planning base: `b6456670a7c61621db1d3b3fc6d55487adb9cd64`
Research checked: 2026-09-24
Implementation authority: **NOT ADMITTED**

## Purpose

Define how M10 describes a workload and binds prior observations so later planning sessions can reason about OOM, thermal and quality risk without taking upstream identity, telemetry, resource or quality authority.

This session does not select a predictive model, policy threshold or runtime implementation. Those remain open for S02-S05 and the Final Technology Review.

## Research findings

### Allocator-scoped memory is not total device memory

PyTorch's CUDA memory snapshots primarily describe allocations managed by the PyTorch allocator. Direct CUDA allocations and third-party allocations, including NCCL examples, are outside that view; the documentation recommends comparing allocator state with device-level memory usage when investigating those allocations. Pinned host allocations are separately opt-in for snapshots. See [PyTorch: Understanding CUDA Memory Usage](https://docs.pytorch.org/docs/main/torch_cuda_memory) and [PyTorch CUDA semantics](https://docs.pytorch.org/docs/main/notes/cuda.html).

**Design implication (inference):** a workload signature must preserve the scope of a memory feature—allocator-specific, process-reported or device-global—and its source, sampling window and freshness. M10 cannot treat one runtime's allocator snapshot as authoritative total capacity or merge unlike memory measures.

### Telemetry capability and sampling vary

NVML exposes queries for utilization, memory, temperature, power, clocks, topology, processes and events. Its API documents unsupported queries on some configurations, including MIG-related gaps; some utilization APIs report a sampling period. See the [NVML API Reference](https://docs.nvidia.com/deploy/nvml-api/latest/) and [device query reference](https://docs.nvidia.com/deploy/nvml-api/api/group__nvmlDeviceQueries.html).

AMD SMI documents monitoring for power, temperature, graphics and memory utilization/clocks, VRAM and PCIe data. Its CLI documentation describes the CLI as example tooling and recommends its Python or C++ library as the robust data source. See [AMD SMI CLI tool usage](https://rocm.docs.amd.com/projects/amdsmi/en/latest/how-to/amdsmi-cli-tool.html).

**Design implication (inference):** telemetry feature values need an explicit provider/schema version, availability state, sample timestamp/window and source capability reference. Missing or unsupported sensors must remain unknown; they must not be imputed as zero or equivalent to a healthy state.

### Prediction intervals are candidates, not guarantees under drift

Distribution-free conformal methods can provide finite-sample marginal predictive coverage under stated assumptions; see Lei et al., [Distribution-Free Predictive Inference for Regression](https://arxiv.org/abs/1604.04173). Barber et al., [Conformal Prediction Beyond Exchangeability](https://arxiv.org/abs/2202.13415), analyze how validity changes when exchangeability assumptions do not hold.

**Design implication (inference):** calibration and uncertainty are first-class planning outputs, but no “distribution-free” label may be treated as unconditional safety under hardware, driver, model, workflow or workload drift. S03 must define freshness, drift detection, recalibration, abstention and no-safe-plan behavior before selecting a technique.

## S01 candidate signature envelope

A later M10 contract should consider these separately versioned, reference-based groups:

- **Identity:** signature schema/version, workload family ref, signature revision, distinct workload-instance ref, canonical feature-set digest.
- **Workload shape:** typed modality-owned dimensions and bounded structural features such as image dimensions/batch, video frame count/rate, audio duration/sample rate/channels, 3D scene/geometry counts, and training sequence/batch descriptors when the owning module supplies them.
- **Causal operation reference:** immutable M02 Production Graph/ExecutionPlan-related refs; M10 does not create a competing graph or production identity.
- **Protected requirements:** M01 Fidelity Contract and M03 intent/constraint refs pinned by revision.
- **Model/workflow context:** M14 model identity/fitness refs and M16 workflow/provider refs, without reclassifying either.
- **Hardware/software context:** M07 hardware/runtime/driver refs, with unsupported or partial telemetry represented explicitly.
- **Empirical context:** M08 benchmark/capability-envelope refs pinned to exact hardware and workload scope.
- **Resource context:** M09 resource snapshot, lease and shape outcome refs; M10 does not reinterpret them as new memory truth.
- **Execution context:** later M11/M12 process/concurrency/placement refs where authorized.
- **Observed labels:** typed terminal outcomes with evidence, separating successful completion, allocation failure/OOM, thermal throttling, timeout, cancellation, process loss and unknown/incomplete results.

Raw prompts, source media, credentials and arbitrary user text are not signature features by default. Domain-specific feature semantics remain with their owning modules and enter M10 through typed, versioned projections.

## Candidate independent S01 surfaces

These are planning candidates, not frozen classifications:

1. Workload Signature Envelope
2. Workload Instance/Family Identity Split
3. Workload Family Namespace
4. Typed Multimodal Shape Projection
5. M02 Causal Plan Reference Binder
6. M01 Quality Contract Reference Binder
7. M03 Protected Constraint Reference Binder
8. M14 Model Evidence Reference Binder
9. M16 Workflow/Provider Reference Binder
10. M07 Hardware and Runtime Context Binder
11. M08 Empirical Capability Context Binder
12. M09 Resource Context Binder
13. Memory Feature Scope Descriptor
14. Thermal/Power Feature Scope Descriptor
15. Telemetry Sampling Window and Freshness Descriptor
16. Feature-Version and Runtime Materiality Binder
17. Observed Outcome Label Registry
18. Unknown/Unsupported Feature Lattice
19. Signature Similarity and Generalization Boundary
20. Data Minimization and Redaction Contract

## Provisional S01 acceptance requirements

- Workload family, workload instance and M02 production identity are distinct identifiers.
- A signature is immutable and binds the feature schema, upstream source revisions and provenance.
- Feature values are typed, bounded, unit-bearing where numeric, and version-pinned.
- Modality-specific semantics arrive through owner-defined references; M10 does not invent or weaken them.
- Unknown, stale, conflicting, unsupported and unavailable values remain distinct and cannot silently become zero or “safe”.
- Similarity is advisory until S03 proves a scope-specific generalization and calibration rule; a nearby signature alone cannot authorize a risky plan.
- Device-global and allocator-scoped memory remain separate features; source and sampling windows are preserved.
- Temperature, power, clocks, thermal-limit events and utilization remain distinct observations with source capability and freshness.
- OOM labels require evidence of allocation failure/resource exhaustion; generic failure, timeout, cancellation and worker loss are not OOM labels.
- No raw prompt, media payload, credential or unrestricted free-form text is required to generate a signature.
- Feature extraction and serialized signatures are bounded and deterministic.
- M10 S01 planning adds no runtime, test or product code and claims no physical measurement.

## S01 open decisions carried to later sessions

- Which M02-owned graph/plan references are sufficient inputs and which plan artifact, if any, M10 may propose.
- Workload-family taxonomy and safe exact-match versus generalization strata.
- Required calibration sample size, target risk budgets and abstention thresholds.
- Thermal forecast horizons and the distinction between device limits, driver throttle evidence and operator-defined comfort policy.
- How policy modes map to M01/M03 obligations without granting M10 quality-degradation authority.
- Which observed outcomes may update a model, how feedback is quarantined, and how model versions roll back.
- Which M11/M12/M13/M14/M16/M50/M54/M56 references are mandatory at each planning decision.

## Sources

- [PyTorch — Understanding CUDA Memory Usage](https://docs.pytorch.org/docs/main/torch_cuda_memory)
- [PyTorch — CUDA semantics](https://docs.pytorch.org/docs/main/notes/cuda.html)
- [NVIDIA — NVML API Reference](https://docs.nvidia.com/deploy/nvml-api/latest/)
- [NVIDIA — NVML Device Queries](https://docs.nvidia.com/deploy/nvml-api/api/group__nvmlDeviceQueries.html)
- [AMD — AMD SMI CLI tool usage](https://rocm.docs.amd.com/projects/amdsmi/en/latest/how-to/amdsmi-cli-tool.html)
- [Lei et al. (2016) — Distribution-Free Predictive Inference for Regression](https://arxiv.org/abs/1604.04173)
- [Barber et al. (2022) — Conformal Prediction Beyond Exchangeability](https://arxiv.org/abs/2202.13415)

## Gate

S01 is complete for module planning. Continue S02-S05, final technology review, M11-M60 compatibility scan, module contract freeze and independent planning audit before implementation admission. No M10 implementation is authorized.
