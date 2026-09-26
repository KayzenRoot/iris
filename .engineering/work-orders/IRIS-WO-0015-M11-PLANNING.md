# IRIS-WO-0015 — M11 Background Worker Fabric & Process Lifecycle Planning

Status: ADMITTED_FOR_PLANNING_ONLY
Risk: ELEVATED
Tracking issue: #82
Repository: KayzenRoot/iris
Authorized planning base: 0014d23115f5fec60a77e5e32d5083e90069a918
Planning branch: iris-wo-0015-m11-planning-docs-20260924
Target owner contract: NOT_FROZEN
M11 implementation authority: NOT_ADMITTED
M10 implementation authority: NOT_ADMITTED

## ADMISSION

Issue #82 admits the M11 planning lifecycle from exact main 0014d23115f5fec60a77e5e32d5083e90069a918. That main passed exact-main Governance run 36059512224, job 107834755459. This Work Order formalizes documentation-only planning scope. It grants no M11 runtime or process-control authority and does not modify the frozen M10 contract or its NOT_ADMITTED implementation state.

## OBJECTIVE

Complete the M11 Background Worker Fabric & Process Lifecycle planning lifecycle: five canonical Slow Planning sessions, Technology Discovery, Final Technology Review, Forward Compatibility Scan, a versioned M11 owner-contract candidate, and independent planning audit. Work proceeds through separately reviewable documentation increments under Issue #82.

## SOURCE ORDER

Read the canonical startup order: Checkpoint → Decisions Ledger → Scope → Definition of Done → Architecture → Requirements → other applicable sources. The Context Lock pins the exact base and source fingerprints. Repository state and Git evidence are authoritative; derived context does not supersede them.

## PLANNING SCOPE

- Complete these sessions in order:
  1. S01 Long-lived supervisor and job process model
  2. S02 Headless/background worker startup and IPC
  3. S03 Concurrency limits, priorities and resource leases
  4. S04 Process reaper, zombie detection and shell-free execution
  5. S05 Cancellation, timeout, crash recovery and workstation coexistence
- For every session, evaluate existing technologies, proven reuse and IRIS-owned candidates as required by the Slow Planning Protocol.
- Perform Technology Discovery, a Final Technology Review and a Forward Compatibility Scan.
- Verify M02, M06, M09 and M10 handoffs against their available canonical contracts. Treat M12–M60 detail as pending where individual owner contracts do not exist.
- Produce a versioned M11 owner-contract candidate only after the five sessions and reviews provide sufficient evidence.
- Perform an independent planning audit with no residual HIGH/CRITICAL finding before contract freeze.
- Update the checkpoint and backlog only through reviewed documentation PRs and Governance.

## AUTHORITY BOUNDARIES

- M02 owns Production Graph causality, canonical ExecutionPlan semantics and production lifecycle.
- M06 owns operational state/revision, materialization lineage and reproducibility.
- M09 owns resource truth, resource claims/leases/reservations/residency and resource-control outcomes.
- M10 may provide recommendations; it does not dispatch, place, reserve resources, or control workers/processes.
- M12 owns placement/orchestration details when its contract is available.
- M11 planning must not absorb quality, protected creative semantics, rights, consent, privacy, security, storage or observability authority owned elsewhere.

## OUT OF SCOPE

- Any runtime/product code, service, process launch, worker start/stop/restart, process inspection/reaping, IPC connection, reservation, lease mutation, provider execution, Blender/ComfyUI operation, or hardware measurement.
- An implementation contract or executor prompt before all planning gates pass.
- Invented IPC, authentication/authorization, process-state, cancellation, timeout, recovery, lease, quota, priority, headroom or cleanup semantics.
- Deep planning M12–M60 or declaring any missing owner contract closed.
- Any amendment to m10-contract-v1.0.

## ACCEPTANCE

- All five canonical M11 sessions are completed and backed by source-linked technology evidence.
- Final Technology Review records explicit ACCEPT / SUPERSEDE / REJECT outcomes.
- Forward scan distinguishes each available owner-contract fact from index-level candidates; M12–M60 gaps remain explicitly pending.
- The M11 contract candidate defines ownership, interfaces, failure/unknown behavior, security and handoffs without taking another owner’s authority.
- Independent planning audit finds zero unresolved HIGH and zero unresolved CRITICAL issues.
- Exact-head Governance passes; protected squash merge and exact-main Governance are recorded in the checkpoint closeout.
- M11 implementation remains NOT_ADMITTED. M10 remains frozen at m10-contract-v1.0, implementation NOT_ADMITTED, and IRIS-WO-0014 preflight BLOCKED.

## CURRENT PACKAGE STATE

### S05 session and proposal history

Status: S05 COMPLETE_FOR_MODULE_PLANNING. Proposal PR #94 exact head c2478c757814df72ca7e5b03fe530e27674f5694 had HEDS-01 APPROVED, protected squash merge 2e6c0b89b67230b2b39c4bbb37ff51648d061060, and exact-main Governance #417 (36254017572 / 108437249087; 3,940/3,940 tests). Closeout PR #95 exact head 77dccb7e350d51d66f8b5cc135566becf0537dcc passed Governance #418 (36257428623 / 108446767119; 3,940/3,940 tests), was protected squash-merged as 091361e71e2d55f05b2623163bd6f8c7234eb5b8, and exact-main Governance #419 (36258590273 / 108449958757) passed on tree d0ea17dde647eec2f73a64df2c6fa2d61bd8dcd1 (3,940/3,940 tests; 16.258 seconds). This chat audit found zero HIGH/CRITICAL or factual/semantic findings; no formal GitHub review or separate human reviewer identity is claimed. The ruleset required zero approving reviews and exact Governance. S05 is complete for module planning only; policy decisions and S04-U01..U21/S05-U01..U23 remain open; M12-M60 owner contracts pending. M11 remains NOT_FROZEN and implementation NOT_ADMITTED.

### S05 post-merge checkpoint promotion

The checkpoint and Evidence Bundle record S05 completion using PR #95's exact head, protected merge, and exact-main Governance receipts. The original PR #95 proposal remains historical; a separate promotion event records the canonical state. The new 83-source Context Lock binds main 091361e71e2d55f05b2623163bd6f8c7234eb5b8 / tree d0ea17dde647eec2f73a64df2c6fa2d61bd8dcd1.

S04-U01..U21, S05-U01..U23 and M12-M60 owner-specific handoffs remain open or pending. M11 Final Technology Review C01 is COMPLETE_FOR_MODULE_PLANNING: PR #97 exact head bdf0a9fb71db037f49ac2d5001f8a65c1237ca57 passed Governance #422, was protected squash-merged as 163b1af387506c092ae07ef3a02c740d9d1ed8ba, and passed exact-main Governance #423 on tree c114856e0fda058c655199d4fd7f97d1c47ad7c9. The review is reference-only and selects no runtime or policy. Next is the separate Forward Compatibility Scan against available owner contracts and M12-M60 index candidates; missing contracts remain PENDING. Then a versioned contract candidate and independent planning audit. No freeze, implementation admission, or issue closure.
