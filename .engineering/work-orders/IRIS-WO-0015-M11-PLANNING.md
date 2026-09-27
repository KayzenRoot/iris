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

### M11 Forward Compatibility Scan C01 — proposal state

The scan proposal is recorded in planning/compatibility/M11-FORWARD-COMPATIBILITY-SCAN.md and binds to main b3fc093cfc5b5370872dacc7ff6694af6bcfd1cd / tree be410381b1e940aa906ebceb7ba89520353a52e5. Its Context Lock fingerprints 89/89 unique exact-base Git blobs; the source matrix contains 30/30 records and the M12–M60 matrix contains 49/49 index headings. All future-owner rows are INDEX_ONLY and PENDING_OWNER_CONTRACT with risk UNRATED. Available M02/M06/M09/M10 boundaries are reference-only and do not grant M11 authority. The proposal is not canonical before governed promotion. M11 stays NOT_FROZEN; M11/M10 implementation stays NOT_ADMITTED; Issue #82 stays OPEN. The required final gate is exact-head Governance PASS with the PR OPEN and UNMERGED. No runtime, process, IPC, resource mutation, owner-contract candidate, independent audit, freeze, or issue closure is part of this increment.

### M11 FCS C01 reviewed and protected-merged; checkpoint closeout proposed

Corrected PR #99 head 9571b24b0a22c1d48e5ccf48d8cb1e9fda31c164 received a bounded chat APPROVED review after three source path repairs and S05 lock coverage correction. Its 89/89 scan lock, 30/30 sources and 49/49 M12-M60 index-only rows were verified. Exact-head Governance run 36285058612 / job 108524110396 passed 3,940/3,940 tests. Protected squash merge 019de28b59db4b1b1dc39bd76780f331a655ccca passed exact-main Governance #433 (36285123475 / 108524313508) and 3,940/3,940 tests on tree 9d0dd1f3198609a225ffd00d20deb66e6f07d7e7. The next separate checkpoint promotion proposal binds 92/92 exact-main sources and does not select technology/policy, freeze M11, authorize implementation or close Issue #82. Following its own approved review and exact-head/merge/exact-main gates, the next separate increment is a versioned M11 owner-contract candidate and then independent planning audit. Missing M12-M60 owner contracts stay INDEX_ONLY/PENDING_OWNER_CONTRACT and UNRATED; S04-U01..U21 and S05-U01..U23 stay OPEN.

### M11 FCS closeout promoted; owner-contract candidate C01

Closeout PR #100 exact head 749eafeafa79463920cc3c0399d9bdac16f0ade4 passed Governance 36285307444 / 108524829278, protected-merged as 9acfe5400a490a996602d5b09f7adb3d92b3050b and passed exact-main Governance #435 (36285351940 / 108524953905; 3,940/3,940 tests). FCS is COMPLETE_FOR_MODULE_PLANNING. The separate C01 candidate document carries 26 invariant proposals and all 44 S04/S05 OPEN questions, bound by 94/94 exact-base Git sources. Missing M12-M60 owner contracts remain PENDING/UNRATED. Independent contract audit, freeze and implementation are not admitted by this documentation proposal; Issue #82 stays OPEN.

### Separate C01 freeze-readiness audit proposal

Candidate PR #101 passed exact-head Governance #436, protected-merged as 9c7cafcfc73700728981f8f90e27110be8dd9fd0 and passed exact-main Governance #438 (3,940/3,940 tests). Separate audit C01 proposes CORRECTION REQUIRED for three HIGH_FOR_FREEZE missing positive interface/authority proofs; no freeze or implementation is admitted by this report.

### C02 Correction Delta

Audit C01 report PR #103 protected-merged as 6006be5af8f58ac6eec00df030fffab2d1d121ab and passed exact-main Governance #440. C02 proposes minimum M11-owned semantic proofs for H01/H02/H03 with DISABLED actions and 44 S04/S05 questions still OPEN. v0.2 is not frozen and cannot admit implementation.
