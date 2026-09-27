# IRIS-WO-0024: M12 S03 Multi-GPU / Heterogeneous Owner-Safe Source Study

Status: ADMITTED_FOR_BOUNDED_S03_REFERENCE_RESEARCH_ONLY | Issue #128 | Risk ELEVATED_COMPOSITE_RESOURCE_BOUNDARIES
Base main `7ab6743ce2d88d596a6da73abbcfc6456d7762e6`, tree `a5bcc17a93d228c3f66d5c51b755fbe11d85281e`, Governance #487 PASS 3979/3979. Branch `iris-wo-0024-m12-s03-multigpu-source-plan-20260927`.
Source order Checkpoint -> Decisions -> Scope -> DoD -> Architecture -> Requirements -> Security -> Work Order. 42/42 exact-base unique SHA-1 source blobs, eight mandatory canonical roots, strict 12-path allowlist. Actual HIVE v1.0.3 live handshake **not executed**; Git-canonical sources govern and IRIS runtime HIVE v1.0.0 remains pinned.

## Deliverables
Reconcile S02 verified PR #130 exact head #486 / exact-main #487 as part of substantive S03 and promote only S02 reference-planning completion (20 OPEN/UNRATED questions, 14 future SQ cases). Compare five multi-device candidate shapes without selecting any: independent per-GPU jobs; one multi-GPU process; one M11-owned process per device; qualified model/pipeline/tensor/data sharding/offload; and all-or-nothing composite group. Cite official NVIDIA CUDA multi-GPU and peer capability, Kubernetes DRA device claims, Ray atomic placement group and PyTorch per-device DDP for **reference only**. Deliver 22 explicit M12-S03-U questions OPEN/UNRATED and 16 future hostile/ambiguity MG cases SPECIFIED_NOT_EXECUTED. Distinguish arbitrary GPU count and summed nominal VRAM from validated exact-member M09 owner-issued coherent snapshot+lease proof, H01 authenticated M11 liveness, individual GPU compatibility/peer checks, M02/M06 task/outcome lineage, M54/M60 OS/trust/IPC rights. S04–S05 remain NOT_STARTED; S03 does not freeze M12.

## Strict allowlist (12)
- `docs/project-brain/03-SCOPE.md`
- `planning/modules/M12-COMPUTE-ORCHESTRATION.md`
- `planning/research/M12-S03-MULTI-GPU-HETEROGENEOUS-EXECUTION.md`
- `.engineering/CHECKPOINT.json`
- `.engineering/CHECKPOINT.md`
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/14-BACKLOG.md`
- `.engineering/evidence/IRIS-WO-0023.json`
- `.engineering/evidence/IRIS-WO-0024.json`
- `.engineering/context-locks/IRIS-WO-0024-M12-S03-PLANNING.json`
- `.engineering/work-orders/IRIS-WO-0024-M12-S03-PLANNING.md`
- `planning/reviews/IRIS-WO-0024-M12-S03-AUDIT-TARGET.md`

## STOP
Do not edit frozen module contracts or M09 code, decide #110 A/B/C, execute CUDA/OS/network/GPU tests, launch/kill worker, add a public registry, change product pins or claim any positive composite grant, shared VRAM, P2P support or S04 federation. Require own exact-head Governance 3979/3979 with Context Lock/checkpoint mirror/GEF/HIVE PASS, bounded separate-same-assistant audit zero newly introduced HIGH/CRITICAL in documentation-only scope, guarded squash expected HEAD and unchanged base, exact-main Governance. S03 reference complete **only** after those proofs; Issue #128 and #82/#110/#112 stay OPEN, no runtime admission.
