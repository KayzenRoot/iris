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

### Current S05 proposal

Status: PROPOSED_NOT_COMPLETE; S01-S04 remain COMPLETE_FOR_MODULE_PLANNING. Proposal base: e0d8aeeea676d884e9c6a716df42a363f0765020 / tree b82ddfb80b7ff57f409b9d48f07263b7c7d356a2. Branch: iris-wo-0015-m11-s05-cancellation-recovery-20260926. Research: planning/research/M11-S05-CANCELLATION-TIMEOUT-CRASH-RECOVERY-WORKSTATION-COEXISTENCE.md. Context Lock: .engineering/context-locks/IRIS-WO-0015-S05.json. This documentation-only proposal leaves cancellation, timeout, recovery, retry, cleanup and headroom decisions unresolved. It stops with the proposal PR open after exact-head Governance; no HEDS, merge, S05 closeout, Final Technology Review, Forward Compatibility Scan, M11 freeze, or implementation is included. M11/M10 implementation remain NOT_ADMITTED, M10 remains frozen at m10-contract-v1.0, and WO-0014 remains BLOCKED.

The planning-admission package merged through PR #83. Exact PR head e35632e3f4775b0ccc89c6723a19faca767a59f2 passed Governance 36063003154 / 107846144342; protected squash merge 09441373deffe35258a41d14b959333a42fbcdd3 passed exact-main Governance 36063188222 / 107846747270 (actor: KayzenRoot). M11 S01 is COMPLETE_FOR_MODULE_PLANNING through PR #85 exact head 819b184cef722a945391d96b75edeb1f74f47c99 (Governance 36065623865 / 107854567970, PASS), protected squash merge 8ea0871668fc182d0f0a829bee352e03a0ec7ce4, and exact-main Governance 36065770189 / 107855048099 (PASS; actor KayzenRoot). M11 S02 is COMPLETE_FOR_MODULE_PLANNING: PR #87 exact head 78893daec68aabe3bb23836a4429017f13e97f30 passed Governance 36068426412 / 107863497210 (3940/3940 tests); protected squash merge b090ae68bac23be2261932e75549b3ea255990ec passed exact-main Governance 36068660747 / 107864233622 (3940/3940 tests; actor KayzenRoot). S02's Context Lock matched 63/63 exact-base fingerprints; the post-authoring documentation audit found 0 HIGH and 0 CRITICAL findings. S01-S04 are COMPLETE_FOR_MODULE_PLANNING; S05 planning proposal is IN_PROGRESS but S05 is NOT complete; no M11 owner contract is frozen. S04 proposal PR #92 exact head 7bd29099adfe3c4b2035e3da1ab9c09349e95001 passed Governance run 36213241691 / job 108323991494 (3940/3940 tests), was protected squash-merged as f779cec13d0877cf9c5ac6797a49c5ef85389d0b, and passed exact-main Governance run 36235782621 / job 108387156827 (3940/3940 tests). The recorded proposal review was a chat review, not a formal GitHub review; Issue #82 remains open; neither M11 nor M10 implementation is admitted. S03 PR #89 corrected exact head 778218c04fb9481cab75122001deb87814ce3e68 passed Governance 36189044035 / 108249450672 (3940/3940 tests), protected squash merge ad3c4ac4aa84890248fbc7e6250bea2de271fd65 passed exact-main Governance 36189379137 / 108250522233 (3940/3940 tests; actor: KayzenRoot), the Context Lock matched 68/68 sources, and the documentation audit found 0 HIGH/CRITICAL/residual findings. The S03 checkpoint/evidence closeout passed exact-main Governance before S04 began. S04 closeout PR #93 received HEDS APPROVED on exact head 6e9e717ecacacfbef787a53ffbf0254f1188323c, was protected squash-merged as e0d8aeeea676d884e9c6a716df42a363f0765020, and passed exact-main Governance #415 (36244566768 / 108411232665; 3940/3940 tests). Its closeout Context Lock matched 77/77 sources. S05 planning is now proposed from that exact main and remains incomplete; no M11 owner contract is frozen.
