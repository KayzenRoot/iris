# M13 S02 | Compilation, Attention & Backend Selection

**NONBINDING SOURCE RESEARCH | WO0046 | issue #155 | 2026-09-27.**

All seven candidate families are **UNSELECTED, UNINSTALLED, UNBENCHMARKED**. An upstream API or a vendor example does NOT grant source trust, operator support, numerical fidelity, native-code permission, device ownership or runtime authority.

## Canonical owner boundary and exact original source provenance

Original exact source main: `ac26499c8753ddc7b96246b9d698d8bcfbe0561f`, tree `4847f9010aaca5ffac560228ee14fb52390cfa0b`. The original M13 S01 report is COMPLETE FOR DOCUMENTARY RESEARCH ONLY. Original M12 and H01–H04 owner gates remain blocked.

- **INDEX**: [planning/MASTER-MODULE-INDEX.md](../../planning/MASTER-MODULE-INDEX.md), exact historical Git blob `19c8ff6126748cb89e53108bdff8289322071970`. Required original source anchor: `S02 — S02 Compilation, attention and backend selection`.
- **S01_REPORT**: [planning/research/M13-S01-WARM-MODEL-CACHE-LOCALITY.md](../../planning/research/M13-S01-WARM-MODEL-CACHE-LOCALITY.md), exact historical Git blob `7701c1e744d2b459d2f6bb4fa754352374fb67fd`. Required original source anchor: `C04_COMPILED_BACKEND_ARTIFACT`.
- **S01_PACKET**: [.engineering/evidence/M13-S01-SOURCE-RESEARCH.json](../../.engineering/evidence/M13-S01-SOURCE-RESEARCH.json), exact historical Git blob `ee65b960ca7e4f83f5419ec744f4c1f304edb6d7`. Required original source anchor: `UNADOPTED_CONCEPT_ONLY`.
- **M01**: [docs/M01-QUALITY-KERNEL.md](../../docs/M01-QUALITY-KERNEL.md), exact historical Git blob `930af57944fa83c44745873c42eb3a7740972ee6`. Required original source anchor: `m01-contract-v1.0`.
- **M02**: [planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md), exact historical Git blob `a85d80ab3bb5f4bdc9be915a59caa92569d66af4`. Required original source anchor: `FROZEN_APPROVED`.
- **M06**: [planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md), exact historical Git blob `18b5303d1e36ef60de17b42dd9e2c371ecf4f191`. Required original source anchor: `Digest equality proves byte equality`.
- **M07**: [docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md](../../docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md), exact historical Git blob `2a0b95dd3cc665e2206e454caef5858ef7fb61b0`. Required original source anchor: `M07 does not lower quality targets`.
- **M08**: [docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md](../../docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md), exact historical Git blob `461e0f332d9be2af694634bbdc8cf67e29d56393`. Required original source anchor: `M08 records empirical performance evidence`.
- **M09**: [docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md](../../docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md), exact historical Git blob `d12b4f48030c1a57b8e6228df39f35dac8c2b20a`. Required original source anchor: `M09 is the provider-neutral resource-state`.
- **M10**: [planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md), exact historical Git blob `f69ec3e3eab24b47c0e31832d64d9ab9cce21828`. Required original source anchor: `Implementation authority: NOT ADMITTED`.
- **M11**: [planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md), exact historical Git blob `41ab89727c7be14e35e2481aefbd97a0cb81cb48`. Required original source anchor: `NOT_FROZEN`.
- **M12**: [planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md), exact historical Git blob `28b3802901349263100ceaaf80c0990513dbbded`. Required original source anchor: `PROPOSED_NOT_FROZEN`.
- **D01**: [.engineering/evidence/M09-B-OWNER-DIRECTION-D01.json](../../.engineering/evidence/M09-B-OWNER-DIRECTION-D01.json), exact historical Git blob `30cc56a2dd34a8c45cfb96f0a900cafbdd2717bb`. Required original source anchor: `B_FUTURE_OWNER_RECEIPT`.

## Eight official external technology references, mutable and never installed evidence

- **SDPA** (PyTorch): [original official documentation](https://docs.pytorch.org/docs/main/generated/torch.nn.functional.scaled_dot_product_attention.html). Scaled-dot-product attention may dispatch input-eligible fused/math implementations, not one universal kernel. PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE.
- **SDPA_POLICY** (PyTorch): [original official documentation](https://docs.pytorch.org/docs/stable/generated/torch.nn.attention.sdpa_kernel.html). Scoped kernel selection is beta and forced fused-kernel choice requires demonstrated operator eligibility. PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE.
- **TORCH_COMPILE** (PyTorch): [original official documentation](https://docs.pytorch.org/docs/stable/generated/torch.compile). Graph compilation may cache by code/guard and recompile or fall back; no current model speedup is proved. PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE.
- **TORCH_CACHE** (PyTorch): [original official documentation](https://docs.pytorch.org/tutorials/recipes/torch_compile_caching_tutorial.html). Compiler cache reuse requires original PyTorch, Triton and exact hardware context qualification. PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE.
- **RECOMPILE** (PyTorch): [original official documentation](https://docs.pytorch.org/docs/main/user_guide/torch_compiler/compile/programming_model.recompilation.html). Dynamic shapes and guard failures change compilation cost; exact workload distributions require measurement. PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE.
- **TENSORRT** (NVIDIA): [original official documentation](https://docs.nvidia.com/deeplearning/tensorrt/latest/inference-library/engine-compatibility.html). Serialized engine plans have version/platform/GPU compatibility restrictions and executable binary trust hazards. PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE.
- **FLASHATTN** (FlashAttention maintainers): [original official documentation](https://github.com/Dao-AILab/flash-attention/blob/main/README.md?plain=1). Optional source extension lists architecture, dtype and attention head limitations, not automatic GPU support. PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE.
- **COMFY_SECURITY** (ComfyUI maintainers): [original official documentation](https://github.com/Comfy-Org/ComfyUI/blob/master/SECURITY.md). Custom nodes run arbitrary Python and are not trusted merely because a workflow declares one. PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE.

## Seven nonbinding candidate families

### REFERENCE_MATH: Reference mathematical attention, conditional comparison only.

Original external research reference: `SDPA`. Required owner evidence: Exact tensor/mask/causal semantics, independent M01 numerical quality tolerance and M16 qualification.
**Prohibition:** No automatic fallback, optimized throughput, provider selection or master promotion is implied.
Status UNSELECTED_NOT_QUALIFIED. No selection, installation, benchmark, approved runtime or actual qualified owner signature.

### AUTO_SDPA: Native framework input-dependent fused or mathematical attention.

Original external research reference: `SDPA`. Required owner evidence: Verified PyTorch/CUDA installed build, M07 device, dtype, dimensions, mask and actual observed kernel.
**Prohibition:** An SDPA API name does not prove FlashAttention availability, acceleration or a verified device.
Status UNSELECTED_NOT_QUALIFIED. No selection, installation, benchmark, approved runtime or actual qualified owner signature.

### EXPLICIT_SDPA: Explicit scoped SDPA kernel policy, subject to beta API changes.

Original external research reference: `SDPA_POLICY`. Required owner evidence: Genuine per-operator eligibility, framework version, failure mode and original M01 accuracy rules.
**Prohibition:** A warning, unsupported fused implementation or silent fallback must never be treated as measured fused execution.
Status UNSELECTED_NOT_QUALIFIED. No selection, installation, benchmark, approved runtime or actual qualified owner signature.

### PYTORCH_INDUCTOR: Optional guarded PyTorch graph compilation/cache candidate.

Original external research reference: `TORCH_COMPILE`. Required owner evidence: M16/M17 accepted graph, exact toolchain/hardware, shape guards, cold compilation latency and M08 evidence.
**Prohibition:** Compilation/guard/cache outcomes cannot authorize storage, GPU reservations or trusted native code.
Status UNSELECTED_NOT_QUALIFIED. No selection, installation, benchmark, approved runtime or actual qualified owner signature.

### EXTERNAL_FLASH: Optional externally sourced FlashAttention native extension.

Original external research reference: `FLASHATTN`. Required owner evidence: Exact CUDA, GPU architecture, dtype/head dimension, audited source/build/rights and M60 OS constraints.
**Prohibition:** Untrusted extension download, wheel installation, native build or invented compatibility is prohibited.
Status UNSELECTED_NOT_QUALIFIED. No selection, installation, benchmark, approved runtime or actual qualified owner signature.

### NVIDIA_ENGINE: Optional separately trusted TensorRT serialized-engine research candidate.

Original external research reference: `TENSORRT`. Required owner evidence: Exact model export/operator set, native build toolchain, runtime/OS/GPU support, engine origin and license.
**Prohibition:** Never deserialize an untrusted engine file or infer compatibility from filename or vendor marketing.
Status UNSELECTED_NOT_QUALIFIED. No selection, installation, benchmark, approved runtime or actual qualified owner signature.

### COMFY_NODE: Deferred ComfyUI custom-node/workflow backend research candidate.

Original external research reference: `COMFY_SECURITY`. Required owner evidence: M16 workflow compiler, M17 runtime, M18 supply-chain, M54/M60 authority and exact reviewed custom-node code.
**Prohibition:** Custom nodes execute arbitrary Python, so the plan does not install, import, download or run one.
Status UNSELECTED_NOT_QUALIFIED. No selection, installation, benchmark, approved runtime or actual qualified owner signature.

## Twelve required future qualification dimensions

- `GRAPH_SEMANTICS` [M02/M04/M06/M16]: Exact accepted graph/revision and versioned lowering; content equality alone cannot prove semantic equivalence. **UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK**.
- `MODEL_ORIGIN` [M14/M18/M53]: Exact owner-issued weights, adapter, license, package and provenance with verification of every imported binary. **UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK**.
- `DEVICE_CONTEXT` [M07/M60]: Actually verified GPU compute capability, OS and runtime/driver version, not inferred from marketing family. **UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK**.
- `TENSOR_ELIGIBILITY` [M04/M16]: Exact Q/K/V layout, mask, causal/dropout, grouped-query and head-dimension compatibility. **UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK**.
- `PRECISION_QUALITY` [M01/M08]: Observed reference/fused numerical accuracy and creative fidelity obligations for exact qualified precision. **UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK**.
- `SHAPE_AND_GUARDS` [M04/M08/M16]: Representative input-shape distribution, graph breaks, guard failure traces and cold-start amortization. **UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK**.
- `ACTUAL_DISPATCH` [M08/M56]: Observed selected kernel and fallback telemetry with trusted versioned provenance; no self-report as proof. **UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK**.
- `COMPILE_ARTIFACT` [M08/M13/M55]: Bounded compiler artifact trust, cache invalidation, observed compilation cost and storage ownership. **UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK**.
- `GRANT_LIVENESS` [M09/M11/M12]: Genuine coherent all-member M09 grant, independent M11 owner ACK and at-use revocation before any GPU action. **UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK**.
- `NATIVE_CODE_TRUST` [M18/M54/M60]: Actual signed/reviewed custom node, wheel or serialized native engine with enforceable host OS rights. **UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK**.
- `TENANCY_RIGHTS` [M53/M54/M55]: Independently reviewed tenant, model/media license, key isolation, delete and consent revocation semantics. **UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK**.
- `MEASURED_VALUE` [M01/M07/M08]: Actual M08-controlled cold/warm latency, throughput, peak VRAM, interactive interference and output fidelity. **UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK**.

## Eighteen NEW M13 S02 owner questions, all OPEN and UNRATED

These are new S02 questions and NOT revisions of original M12 110 OPEN, H03 original 91/147, C03 proposals or separate M13 S01 18 OPEN questions.

### M13-S02-U01 | M13/M04/M16

Which original M04 tensor/mask/causal semantics and M02 accepted graph can a future M16 compiler optimize without rewriting creative meaning?

Original source role `INDEX`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U02 | M13/M07/M60

Which actually verified GPU capability, driver, operating system and toolchain must match each candidate kernel or engine rather than inferring from vendor name?

Original source role `M07`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U03 | M13/M08

How will a genuinely admitted M08 protocol separate first compile cost, warm execution, exact memory pressure, interference and actual output quality?

Original source role `M08`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U04 | M13/M14/M18

Which genuine source-owner model identity, adapters, license and software package provenance must be independently reviewed for optional precompiled code?

Original source role `INDEX`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U05 | M13/M16

What explicit operator coverage and conversion-loss evidence could a future M16 workflow compiler accept without adopting a competing graph contract?

Original source role `INDEX`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U06 | M13/M17

What future M17 source-qualified ComfyUI runtime/node graph, isolation and rollback contract must exist before any third-party node executes?

Original source role `INDEX`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U07 | M13/M01/M08

What M01 creative-quality tolerances and independent M08 numerical reference evidence would be required for any fused attention precision claim?

Original source role `M01`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U08 | M13/M07/M08

What exact real head dimension, input shape, attention mask, dtype and installed backend eligibility must be measured for each purported GPU kernel?

Original source role `M07`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U09 | M13/M16

How should a future owner distinguish explicit SDPA policy failure, missing kernel support and beta API changes from a verified successful fused path?

Original source role `INDEX`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U10 | M13/M08

Which workload shape distribution, guard failures, cold compilation time and cache identity could justify a future measured compiler benefit?

Original source role `M08`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U11 | M13/M18/M54/M60

How will future security and supply-chain owners reject unsigned TensorRT plans, untrusted native kernels and arbitrary Python custom-node execution?

Original source role `INDEX`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U12 | M13/M09/M11/M12

What independently reviewed exact M09 joint lease, M11 real producer ACK and M12 request/attempt/fence proof would precede any authorized GPU prewarming?

Original source role `M09`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U13 | M13/M53/M54/M55

Who owns cross-tenant compiled artifact isolation, original model rights, physical cache expiry, deletion and credential/consent revocation?

Original source role `INDEX`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U14 | M13/M14/M16

Which exact model operator and precision exclusions should condition optional FlashAttention versus TensorRT research without selecting either implementation?

Original source role `INDEX`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U15 | M13/M07/M08/M10

How are observed M08 latency, recompilation, thermal impact and peak VRAM kept distinct from frozen M10 advisory predictions and model qualification?

Original source role `M10`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U16 | M13/M08/M56

What independent telemetry shows the actual selected attention kernel, fallback, compiler cache hit and graph recompilation instead of trusting labels?

Original source role `M08`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U17 | M13/M16/M17/M60

Which future source-approved compiler, runtime and host-platform owners may select or reject a backend without inheriting rights from their module names?

Original source role `INDEX`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

### M13-S02-U18 | M13/M01/M02/M53

How must every later attention or compiler optimization preserve M01 master quality, M02 accepted production truth and genuine M53 rights evidence?

Original source role `M01`, status OPEN_UNRATED_PENDING_QUALIFIED_OWNER, risk UNRATED, owner answer NOT RECEIVED, runtime authority NONE.

## Fourteen NEW future negative scenarios, all NOT EXECUTED

### CBA-01

Relevant candidates: AUTO_SDPA, EXPLICIT_SDPA
Trigger: An unsupported dtype, mask or head dimension prevents a forced fused backend from running.
Future expected non-authorizing oracle: `NO_FALSE_FUSED_SUCCESS_OR_UNQUALIFIED_FALLBACK`. **SPECIFIED_NOT_EXECUTED**.

### CBA-02

Relevant candidates: REFERENCE_MATH, EXPLICIT_SDPA
Trigger: Optimized attention changes original M01-defined numerical fidelity under an advertised speed improvement.
Future expected non-authorizing oracle: `NO_MASTER_PROMOTION_FROM_FAST_NUMERICAL_DRIFT`. **SPECIFIED_NOT_EXECUTED**.

### CBA-03

Relevant candidates: PYTORCH_INDUCTOR
Trigger: Dynamic shapes repeatedly invalidate guarded compiled graphs and increase cold-start latency.
Future expected non-authorizing oracle: `NO_UNMEASURED_COMPILATION_SPEEDUP`. **SPECIFIED_NOT_EXECUTED**.

### CBA-04

Relevant candidates: NVIDIA_ENGINE
Trigger: An untrusted third-party serialized engine claims to match installed GPU and runtime.
Future expected non-authorizing oracle: `NEVER_DESERIALIZE_UNTRUSTED_NATIVE_ENGINE`. **SPECIFIED_NOT_EXECUTED**.

### CBA-05

Relevant candidates: NVIDIA_ENGINE
Trigger: Builder/runtime version or compute capability is incompatible despite a plausible filename.
Future expected non-authorizing oracle: `NO_ENGINE_COMPATIBILITY_BY_FILENAME`. **SPECIFIED_NOT_EXECUTED**.

### CBA-06

Relevant candidates: EXTERNAL_FLASH
Trigger: A native FlashAttention wheel/source demands unreviewed build scripts or operating-system rights.
Future expected non-authorizing oracle: `NO_UNTRUSTED_EXTENSION_INSTALL`. **SPECIFIED_NOT_EXECUTED**.

### CBA-07

Relevant candidates: COMFY_NODE
Trigger: A custom workflow node requests arbitrary Python import, dependencies and privileged filesystem access.
Future expected non-authorizing oracle: `NO_UNTRUSTED_CUSTOM_NODE_EXECUTION`. **SPECIFIED_NOT_EXECUTED**.

### CBA-08

Relevant candidates: REFERENCE_MATH, AUTO_SDPA
Trigger: Output hashes match even though source graph, lineage, master fidelity or consent differs.
Future expected non-authorizing oracle: `NO_HASH_BASED_PRODUCTION_APPROVAL`. **SPECIFIED_NOT_EXECUTED**.

### CBA-09

Relevant candidates: PYTORCH_INDUCTOR, NVIDIA_ENGINE
Trigger: A compiled artifact is reused across tenants or after driver, model license or rights revocation.
Future expected non-authorizing oracle: `NO_CROSS_SCOPE_COMPILED_ARTIFACT_REUSE`. **SPECIFIED_NOT_EXECUTED**.

### CBA-10

Relevant candidates: EXTERNAL_FLASH, NVIDIA_ENGINE
Trigger: A warm device cache exists but real M09 joint lease, M11 ACK and work/attempt fence are absent.
Future expected non-authorizing oracle: `NO_RESOURCE_GRANT_OR_GPU_ACTION_FROM_HINT`. **SPECIFIED_NOT_EXECUTED**.

### CBA-11

Relevant candidates: PYTORCH_INDUCTOR
Trigger: A cold compilation benchmark hides foreground interactive interference and thermal throttling.
Future expected non-authorizing oracle: `NO_BENCHMARK_ADMISSION_WITH_MISSING_INTERFERENCE`. **SPECIFIED_NOT_EXECUTED**.

### CBA-12

Relevant candidates: EXPLICIT_SDPA, COMFY_NODE
Trigger: An upstream framework or node silently changes API or dependency version after historic review.
Future expected non-authorizing oracle: `REQUALIFY_EXACT_INSTALLED_VERSION`. **SPECIFIED_NOT_EXECUTED**.

### CBA-13

Relevant candidates: AUTO_SDPA
Trigger: Dispatcher uses a different fallback kernel while labels still claim fused attention.
Future expected non-authorizing oracle: `NO_UNOBSERVED_POSITIVE_KERNEL_IDENTITY`. **SPECIFIED_NOT_EXECUTED**.

### CBA-14

Relevant candidates: NVIDIA_ENGINE
Trigger: Model export omits an unsupported operator or changes precision despite a seemingly valid serialized engine.
Future expected non-authorizing oracle: `NO_PARTIAL_GRAPH_EQUIVALENCE`. **SPECIFIED_NOT_EXECUTED**.

## Explicit STOP and next session

Current B=`DIRECTION_ONLY`, C01=`UNADOPTED_NOT_FROZEN`, HIGH gates `H01_H02_H03_H04_OPEN_HIGH_FOR_FUTURE_FREEZE`, runtime=`NOT_ADMITTED`. This research selects no candidate. S03 future intermediate cache/delta reuse requires an independent new source-locked Work Order and cannot use byte equality or backend speed to assert M02/M06 production success or M01 promotion.

**STOP:** S02 is documentary comparison, NOT selected technology, installed framework, signed module contract, qualified actual GPU, measured speedup, M09 lease or real resource capacity, M11 process owner, M12 placement, custom-node or native-engine code execution, OS/GPU/storage/network/cloud/public API or M10/M11/M12/M13 runtime. Upstream pages are mutable and do not prove any installed version. B DIRECTION_ONLY, C01 UNADOPTED_NOT_FROZEN, H01-H04 OPEN HIGH; S01/S02/M12/H03 future negative scenarios SPECIFIED_NOT_EXECUTED.

## Appendix A: canonical machine packet

```json
{
  "schema": "iris-m13-s02-source-research-v0.1",
  "workOrder": "IRIS-WO-0046",
  "issue": 155,
  "module": "M13",
  "session": "S02",
  "base": "ac26499c8753ddc7b96246b9d698d8bcfbe0561f",
  "baseTree": "4847f9010aaca5ffac560228ee14fb52390cfa0b",
  "asOf": "2026-09-27",
  "status": "SOURCE_ONLY_UNSELECTED_NONBINDING",
  "ownerApprovals": 0,
  "selectedBackend": "NONE",
  "selectedKernel": "NONE",
  "selectedCompiler": "NONE",
  "hardwareMeasurements": "NONE",
  "runtime": "NOT_ADMITTED",
  "b": "DIRECTION_ONLY",
  "c01": "UNADOPTED_NOT_FROZEN",
  "highs": "H01_H02_H03_H04_OPEN_HIGH_FOR_FUTURE_FREEZE",
  "originalS01Questions": "18_OPEN_UNRATED",
  "originalS01Negatives": "12_SPECIFIED_NOT_EXECUTED",
  "originalM12Questions": "110_OPEN_UNRATED",
  "originalM12Negatives": "80_SPECIFIED_NOT_EXECUTED",
  "sourceDocs": [
    {
      "role": "INDEX",
      "path": "planning/MASTER-MODULE-INDEX.md",
      "sha": "19c8ff6126748cb89e53108bdff8289322071970",
      "anchor": "S02 — S02 Compilation, attention and backend selection"
    },
    {
      "role": "S01_REPORT",
      "path": "planning/research/M13-S01-WARM-MODEL-CACHE-LOCALITY.md",
      "sha": "7701c1e744d2b459d2f6bb4fa754352374fb67fd",
      "anchor": "C04_COMPILED_BACKEND_ARTIFACT"
    },
    {
      "role": "S01_PACKET",
      "path": ".engineering/evidence/M13-S01-SOURCE-RESEARCH.json",
      "sha": "ee65b960ca7e4f83f5419ec744f4c1f304edb6d7",
      "anchor": "UNADOPTED_CONCEPT_ONLY"
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
      "anchor": "FROZEN_APPROVED"
    },
    {
      "role": "M06",
      "path": "planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
      "sha": "18b5303d1e36ef60de17b42dd9e2c371ecf4f191",
      "anchor": "Digest equality proves byte equality"
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
      "anchor": "M08 records empirical performance evidence"
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
      "anchor": "Implementation authority: NOT ADMITTED"
    },
    {
      "role": "M11",
      "path": "planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
      "sha": "41ab89727c7be14e35e2481aefbd97a0cb81cb48",
      "anchor": "NOT_FROZEN"
    },
    {
      "role": "M12",
      "path": "planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
      "sha": "28b3802901349263100ceaaf80c0990513dbbded",
      "anchor": "PROPOSED_NOT_FROZEN"
    },
    {
      "role": "D01",
      "path": ".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json",
      "sha": "30cc56a2dd34a8c45cfb96f0a900cafbdd2717bb",
      "anchor": "B_FUTURE_OWNER_RECEIPT"
    }
  ],
  "officialReferences": [
    {
      "id": "SDPA",
      "url": "https://docs.pytorch.org/docs/main/generated/torch.nn.functional.scaled_dot_product_attention.html",
      "publisher": "PyTorch",
      "sourceClaim": "Scaled-dot-product attention may dispatch input-eligible fused/math implementations, not one universal kernel.",
      "checkedOn": "2026-09-27",
      "status": "PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE"
    },
    {
      "id": "SDPA_POLICY",
      "url": "https://docs.pytorch.org/docs/stable/generated/torch.nn.attention.sdpa_kernel.html",
      "publisher": "PyTorch",
      "sourceClaim": "Scoped kernel selection is beta and forced fused-kernel choice requires demonstrated operator eligibility.",
      "checkedOn": "2026-09-27",
      "status": "PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE"
    },
    {
      "id": "TORCH_COMPILE",
      "url": "https://docs.pytorch.org/docs/stable/generated/torch.compile",
      "publisher": "PyTorch",
      "sourceClaim": "Graph compilation may cache by code/guard and recompile or fall back; no current model speedup is proved.",
      "checkedOn": "2026-09-27",
      "status": "PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE"
    },
    {
      "id": "TORCH_CACHE",
      "url": "https://docs.pytorch.org/tutorials/recipes/torch_compile_caching_tutorial.html",
      "publisher": "PyTorch",
      "sourceClaim": "Compiler cache reuse requires original PyTorch, Triton and exact hardware context qualification.",
      "checkedOn": "2026-09-27",
      "status": "PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE"
    },
    {
      "id": "RECOMPILE",
      "url": "https://docs.pytorch.org/docs/main/user_guide/torch_compiler/compile/programming_model.recompilation.html",
      "publisher": "PyTorch",
      "sourceClaim": "Dynamic shapes and guard failures change compilation cost; exact workload distributions require measurement.",
      "checkedOn": "2026-09-27",
      "status": "PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE"
    },
    {
      "id": "TENSORRT",
      "url": "https://docs.nvidia.com/deeplearning/tensorrt/latest/inference-library/engine-compatibility.html",
      "publisher": "NVIDIA",
      "sourceClaim": "Serialized engine plans have version/platform/GPU compatibility restrictions and executable binary trust hazards.",
      "checkedOn": "2026-09-27",
      "status": "PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE"
    },
    {
      "id": "FLASHATTN",
      "url": "https://github.com/Dao-AILab/flash-attention/blob/main/README.md?plain=1",
      "publisher": "FlashAttention maintainers",
      "sourceClaim": "Optional source extension lists architecture, dtype and attention head limitations, not automatic GPU support.",
      "checkedOn": "2026-09-27",
      "status": "PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE"
    },
    {
      "id": "COMFY_SECURITY",
      "url": "https://github.com/Comfy-Org/ComfyUI/blob/master/SECURITY.md",
      "publisher": "ComfyUI maintainers",
      "sourceClaim": "Custom nodes run arbitrary Python and are not trusted merely because a workflow declares one.",
      "checkedOn": "2026-09-27",
      "status": "PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE"
    }
  ],
  "candidates": [
    {
      "id": "REFERENCE_MATH",
      "description": "Reference mathematical attention, conditional comparison only.",
      "officialRef": "SDPA",
      "requiredEvidence": "Exact tensor/mask/causal semantics, independent M01 numerical quality tolerance and M16 qualification.",
      "prohibition": "No automatic fallback, optimized throughput, provider selection or master promotion is implied.",
      "status": "UNSELECTED_NOT_QUALIFIED",
      "selected": false,
      "installed": false,
      "benchmarked": false,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "AUTO_SDPA",
      "description": "Native framework input-dependent fused or mathematical attention.",
      "officialRef": "SDPA",
      "requiredEvidence": "Verified PyTorch/CUDA installed build, M07 device, dtype, dimensions, mask and actual observed kernel.",
      "prohibition": "An SDPA API name does not prove FlashAttention availability, acceleration or a verified device.",
      "status": "UNSELECTED_NOT_QUALIFIED",
      "selected": false,
      "installed": false,
      "benchmarked": false,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "EXPLICIT_SDPA",
      "description": "Explicit scoped SDPA kernel policy, subject to beta API changes.",
      "officialRef": "SDPA_POLICY",
      "requiredEvidence": "Genuine per-operator eligibility, framework version, failure mode and original M01 accuracy rules.",
      "prohibition": "A warning, unsupported fused implementation or silent fallback must never be treated as measured fused execution.",
      "status": "UNSELECTED_NOT_QUALIFIED",
      "selected": false,
      "installed": false,
      "benchmarked": false,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "PYTORCH_INDUCTOR",
      "description": "Optional guarded PyTorch graph compilation/cache candidate.",
      "officialRef": "TORCH_COMPILE",
      "requiredEvidence": "M16/M17 accepted graph, exact toolchain/hardware, shape guards, cold compilation latency and M08 evidence.",
      "prohibition": "Compilation/guard/cache outcomes cannot authorize storage, GPU reservations or trusted native code.",
      "status": "UNSELECTED_NOT_QUALIFIED",
      "selected": false,
      "installed": false,
      "benchmarked": false,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "EXTERNAL_FLASH",
      "description": "Optional externally sourced FlashAttention native extension.",
      "officialRef": "FLASHATTN",
      "requiredEvidence": "Exact CUDA, GPU architecture, dtype/head dimension, audited source/build/rights and M60 OS constraints.",
      "prohibition": "Untrusted extension download, wheel installation, native build or invented compatibility is prohibited.",
      "status": "UNSELECTED_NOT_QUALIFIED",
      "selected": false,
      "installed": false,
      "benchmarked": false,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "NVIDIA_ENGINE",
      "description": "Optional separately trusted TensorRT serialized-engine research candidate.",
      "officialRef": "TENSORRT",
      "requiredEvidence": "Exact model export/operator set, native build toolchain, runtime/OS/GPU support, engine origin and license.",
      "prohibition": "Never deserialize an untrusted engine file or infer compatibility from filename or vendor marketing.",
      "status": "UNSELECTED_NOT_QUALIFIED",
      "selected": false,
      "installed": false,
      "benchmarked": false,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "COMFY_NODE",
      "description": "Deferred ComfyUI custom-node/workflow backend research candidate.",
      "officialRef": "COMFY_SECURITY",
      "requiredEvidence": "M16 workflow compiler, M17 runtime, M18 supply-chain, M54/M60 authority and exact reviewed custom-node code.",
      "prohibition": "Custom nodes execute arbitrary Python, so the plan does not install, import, download or run one.",
      "status": "UNSELECTED_NOT_QUALIFIED",
      "selected": false,
      "installed": false,
      "benchmarked": false,
      "runtimeAuthority": "NONE"
    }
  ],
  "qualificationDimensions": [
    {
      "id": "GRAPH_SEMANTICS",
      "ownerRoute": "M02/M04/M06/M16",
      "neededEvidence": "Exact accepted graph/revision and versioned lowering; content equality alone cannot prove semantic equivalence.",
      "status": "UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK"
    },
    {
      "id": "MODEL_ORIGIN",
      "ownerRoute": "M14/M18/M53",
      "neededEvidence": "Exact owner-issued weights, adapter, license, package and provenance with verification of every imported binary.",
      "status": "UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK"
    },
    {
      "id": "DEVICE_CONTEXT",
      "ownerRoute": "M07/M60",
      "neededEvidence": "Actually verified GPU compute capability, OS and runtime/driver version, not inferred from marketing family.",
      "status": "UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK"
    },
    {
      "id": "TENSOR_ELIGIBILITY",
      "ownerRoute": "M04/M16",
      "neededEvidence": "Exact Q/K/V layout, mask, causal/dropout, grouped-query and head-dimension compatibility.",
      "status": "UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK"
    },
    {
      "id": "PRECISION_QUALITY",
      "ownerRoute": "M01/M08",
      "neededEvidence": "Observed reference/fused numerical accuracy and creative fidelity obligations for exact qualified precision.",
      "status": "UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK"
    },
    {
      "id": "SHAPE_AND_GUARDS",
      "ownerRoute": "M04/M08/M16",
      "neededEvidence": "Representative input-shape distribution, graph breaks, guard failure traces and cold-start amortization.",
      "status": "UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK"
    },
    {
      "id": "ACTUAL_DISPATCH",
      "ownerRoute": "M08/M56",
      "neededEvidence": "Observed selected kernel and fallback telemetry with trusted versioned provenance; no self-report as proof.",
      "status": "UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK"
    },
    {
      "id": "COMPILE_ARTIFACT",
      "ownerRoute": "M08/M13/M55",
      "neededEvidence": "Bounded compiler artifact trust, cache invalidation, observed compilation cost and storage ownership.",
      "status": "UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK"
    },
    {
      "id": "GRANT_LIVENESS",
      "ownerRoute": "M09/M11/M12",
      "neededEvidence": "Genuine coherent all-member M09 grant, independent M11 owner ACK and at-use revocation before any GPU action.",
      "status": "UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK"
    },
    {
      "id": "NATIVE_CODE_TRUST",
      "ownerRoute": "M18/M54/M60",
      "neededEvidence": "Actual signed/reviewed custom node, wheel or serialized native engine with enforceable host OS rights.",
      "status": "UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK"
    },
    {
      "id": "TENANCY_RIGHTS",
      "ownerRoute": "M53/M54/M55",
      "neededEvidence": "Independently reviewed tenant, model/media license, key isolation, delete and consent revocation semantics.",
      "status": "UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK"
    },
    {
      "id": "MEASURED_VALUE",
      "ownerRoute": "M01/M07/M08",
      "neededEvidence": "Actual M08-controlled cold/warm latency, throughput, peak VRAM, interactive interference and output fidelity.",
      "status": "UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK"
    }
  ],
  "questions": [
    {
      "id": "M13-S02-U01",
      "ownerRoute": "M13/M04/M16",
      "question": "Which original M04 tensor/mask/causal semantics and M02 accepted graph can a future M16 compiler optimize without rewriting creative meaning?",
      "sourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U02",
      "ownerRoute": "M13/M07/M60",
      "question": "Which actually verified GPU capability, driver, operating system and toolchain must match each candidate kernel or engine rather than inferring from vendor name?",
      "sourceRole": "M07",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U03",
      "ownerRoute": "M13/M08",
      "question": "How will a genuinely admitted M08 protocol separate first compile cost, warm execution, exact memory pressure, interference and actual output quality?",
      "sourceRole": "M08",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U04",
      "ownerRoute": "M13/M14/M18",
      "question": "Which genuine source-owner model identity, adapters, license and software package provenance must be independently reviewed for optional precompiled code?",
      "sourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U05",
      "ownerRoute": "M13/M16",
      "question": "What explicit operator coverage and conversion-loss evidence could a future M16 workflow compiler accept without adopting a competing graph contract?",
      "sourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U06",
      "ownerRoute": "M13/M17",
      "question": "What future M17 source-qualified ComfyUI runtime/node graph, isolation and rollback contract must exist before any third-party node executes?",
      "sourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U07",
      "ownerRoute": "M13/M01/M08",
      "question": "What M01 creative-quality tolerances and independent M08 numerical reference evidence would be required for any fused attention precision claim?",
      "sourceRole": "M01",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U08",
      "ownerRoute": "M13/M07/M08",
      "question": "What exact real head dimension, input shape, attention mask, dtype and installed backend eligibility must be measured for each purported GPU kernel?",
      "sourceRole": "M07",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U09",
      "ownerRoute": "M13/M16",
      "question": "How should a future owner distinguish explicit SDPA policy failure, missing kernel support and beta API changes from a verified successful fused path?",
      "sourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U10",
      "ownerRoute": "M13/M08",
      "question": "Which workload shape distribution, guard failures, cold compilation time and cache identity could justify a future measured compiler benefit?",
      "sourceRole": "M08",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U11",
      "ownerRoute": "M13/M18/M54/M60",
      "question": "How will future security and supply-chain owners reject unsigned TensorRT plans, untrusted native kernels and arbitrary Python custom-node execution?",
      "sourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U12",
      "ownerRoute": "M13/M09/M11/M12",
      "question": "What independently reviewed exact M09 joint lease, M11 real producer ACK and M12 request/attempt/fence proof would precede any authorized GPU prewarming?",
      "sourceRole": "M09",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U13",
      "ownerRoute": "M13/M53/M54/M55",
      "question": "Who owns cross-tenant compiled artifact isolation, original model rights, physical cache expiry, deletion and credential/consent revocation?",
      "sourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U14",
      "ownerRoute": "M13/M14/M16",
      "question": "Which exact model operator and precision exclusions should condition optional FlashAttention versus TensorRT research without selecting either implementation?",
      "sourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U15",
      "ownerRoute": "M13/M07/M08/M10",
      "question": "How are observed M08 latency, recompilation, thermal impact and peak VRAM kept distinct from frozen M10 advisory predictions and model qualification?",
      "sourceRole": "M10",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U16",
      "ownerRoute": "M13/M08/M56",
      "question": "What independent telemetry shows the actual selected attention kernel, fallback, compiler cache hit and graph recompilation instead of trusting labels?",
      "sourceRole": "M08",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U17",
      "ownerRoute": "M13/M16/M17/M60",
      "question": "Which future source-approved compiler, runtime and host-platform owners may select or reject a backend without inheriting rights from their module names?",
      "sourceRole": "INDEX",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    },
    {
      "id": "M13-S02-U18",
      "ownerRoute": "M13/M01/M02/M53",
      "question": "How must every later attention or compiler optimization preserve M01 master quality, M02 accepted production truth and genuine M53 rights evidence?",
      "sourceRole": "M01",
      "status": "OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
      "risk": "UNRATED",
      "ownerAnswer": null,
      "runtimeAuthority": "NONE"
    }
  ],
  "negativeCases": [
    {
      "id": "CBA-01",
      "candidateIds": [
        "AUTO_SDPA",
        "EXPLICIT_SDPA"
      ],
      "trigger": "An unsupported dtype, mask or head dimension prevents a forced fused backend from running.",
      "oracle": "NO_FALSE_FUSED_SUCCESS_OR_UNQUALIFIED_FALLBACK",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "CBA-02",
      "candidateIds": [
        "REFERENCE_MATH",
        "EXPLICIT_SDPA"
      ],
      "trigger": "Optimized attention changes original M01-defined numerical fidelity under an advertised speed improvement.",
      "oracle": "NO_MASTER_PROMOTION_FROM_FAST_NUMERICAL_DRIFT",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "CBA-03",
      "candidateIds": [
        "PYTORCH_INDUCTOR"
      ],
      "trigger": "Dynamic shapes repeatedly invalidate guarded compiled graphs and increase cold-start latency.",
      "oracle": "NO_UNMEASURED_COMPILATION_SPEEDUP",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "CBA-04",
      "candidateIds": [
        "NVIDIA_ENGINE"
      ],
      "trigger": "An untrusted third-party serialized engine claims to match installed GPU and runtime.",
      "oracle": "NEVER_DESERIALIZE_UNTRUSTED_NATIVE_ENGINE",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "CBA-05",
      "candidateIds": [
        "NVIDIA_ENGINE"
      ],
      "trigger": "Builder/runtime version or compute capability is incompatible despite a plausible filename.",
      "oracle": "NO_ENGINE_COMPATIBILITY_BY_FILENAME",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "CBA-06",
      "candidateIds": [
        "EXTERNAL_FLASH"
      ],
      "trigger": "A native FlashAttention wheel/source demands unreviewed build scripts or operating-system rights.",
      "oracle": "NO_UNTRUSTED_EXTENSION_INSTALL",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "CBA-07",
      "candidateIds": [
        "COMFY_NODE"
      ],
      "trigger": "A custom workflow node requests arbitrary Python import, dependencies and privileged filesystem access.",
      "oracle": "NO_UNTRUSTED_CUSTOM_NODE_EXECUTION",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "CBA-08",
      "candidateIds": [
        "REFERENCE_MATH",
        "AUTO_SDPA"
      ],
      "trigger": "Output hashes match even though source graph, lineage, master fidelity or consent differs.",
      "oracle": "NO_HASH_BASED_PRODUCTION_APPROVAL",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "CBA-09",
      "candidateIds": [
        "PYTORCH_INDUCTOR",
        "NVIDIA_ENGINE"
      ],
      "trigger": "A compiled artifact is reused across tenants or after driver, model license or rights revocation.",
      "oracle": "NO_CROSS_SCOPE_COMPILED_ARTIFACT_REUSE",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "CBA-10",
      "candidateIds": [
        "EXTERNAL_FLASH",
        "NVIDIA_ENGINE"
      ],
      "trigger": "A warm device cache exists but real M09 joint lease, M11 ACK and work/attempt fence are absent.",
      "oracle": "NO_RESOURCE_GRANT_OR_GPU_ACTION_FROM_HINT",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "CBA-11",
      "candidateIds": [
        "PYTORCH_INDUCTOR"
      ],
      "trigger": "A cold compilation benchmark hides foreground interactive interference and thermal throttling.",
      "oracle": "NO_BENCHMARK_ADMISSION_WITH_MISSING_INTERFERENCE",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "CBA-12",
      "candidateIds": [
        "EXPLICIT_SDPA",
        "COMFY_NODE"
      ],
      "trigger": "An upstream framework or node silently changes API or dependency version after historic review.",
      "oracle": "REQUALIFY_EXACT_INSTALLED_VERSION",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "CBA-13",
      "candidateIds": [
        "AUTO_SDPA"
      ],
      "trigger": "Dispatcher uses a different fallback kernel while labels still claim fused attention.",
      "oracle": "NO_UNOBSERVED_POSITIVE_KERNEL_IDENTITY",
      "status": "SPECIFIED_NOT_EXECUTED"
    },
    {
      "id": "CBA-14",
      "candidateIds": [
        "NVIDIA_ENGINE"
      ],
      "trigger": "Model export omits an unsupported operator or changes precision despite a seemingly valid serialized engine.",
      "oracle": "NO_PARTIAL_GRAPH_EQUIVALENCE",
      "status": "SPECIFIED_NOT_EXECUTED"
    }
  ],
  "stop": "S02 is documentary comparison, NOT selected technology, installed framework, signed module contract, qualified actual GPU, measured speedup, M09 lease or real resource capacity, M11 process owner, M12 placement, custom-node or native-engine code execution, OS/GPU/storage/network/cloud/public API or M10/M11/M12/M13 runtime. Upstream pages are mutable and do not prove any installed version. B DIRECTION_ONLY, C01 UNADOPTED_NOT_FROZEN, H01-H04 OPEN HIGH; S01/S02/M12/H03 future negative scenarios SPECIFIED_NOT_EXECUTED."
}
```
