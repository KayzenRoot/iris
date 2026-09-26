# M11 — Background Worker Fabric & Process Lifecycle

Status: S01_S04_COMPLETE_S05_PROPOSAL_IN_PROGRESS
Contract: NOT_FROZEN
Planning issue: #82
Planning Work Order: IRIS-WO-0015
Planning admission base: 0014d23115f5fec60a77e5e32d5083e90069a918
Implementation authority: NOT_ADMITTED

## Purpose

This file is the session map for the admitted M11 planning lifecycle. It is not an owner contract, implementation specification, technology decision, process policy, or authorization to launch or control workers. S01-S04 are COMPLETE_FOR_MODULE_PLANNING; S05 cancellation/recovery planning is IN_PROGRESS as a proposal, but S05 is NOT complete. No M11 contract is frozen by this document. S04 completion is evidenced by PR #92; its separate checkpoint/evidence closeout PR #93 received HEDS APPROVED on exact head 6e9e717ecacacfbef787a53ffbf0254f1188323c, was protected squash-merged as e0d8aeeea676d884e9c6a716df42a363f0765020, and passed exact-main Governance #415 (36244566768 / 108411232665).

M11 is expected to plan the background worker and operating-system process lifecycle required by IRIS. Product requirements PR-005, PR-006, PR-008 and PR-009 establish the planning context: Blender headless/background automation, a structured control surface without mandatory live GUI, managed worker lifecycle/concurrency/cancellation/cleanup/orphan detection, and configurable workstation CPU/RAM/VRAM headroom. Their concrete semantics remain to be planned and assigned to owners.

## Available contract boundaries at the admission base

| Owner | Canonical source available at base | Boundary to preserve |
| --- | --- | --- |
| M02 | planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md | Production Graph causality, canonical ExecutionPlan and production lifecycle remain M02-owned. |
| M06 | planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md | Operational state/revision, materialization lineage and reproducibility remain M06-owned. |
| M09 | docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md and planning/modules/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md | Resource truth, claims, leases, reservations, residency and resource-control outcomes remain M09-owned. |
| M10 | planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md and planning/compatibility/M10-FORWARD-COMPATIBILITY-SCAN.md | M10 recommendations do not dispatch, place, reserve resources, or control worker/process lifecycle. |
| M11 | No M11 plan or owner contract exists at the admission base. | This issue plans the M11 owner contract; no details are assumed frozen. |
| M12–M60 | No individual owner plan or contract exists at the admission base; the master index and prior index-level scans are candidate context only. | Record each unavailable owner-specific handoff as PENDING. Revisit it only when that owner’s canonical contract is available. |

## Slow-planning sessions

### S01 — Long-lived supervisor and job process model
Status: COMPLETE_FOR_MODULE_PLANNING

Plan supervisor and job identity/lifecycle roles, process ownership boundaries, long-lived versus per-job responsibilities, failure domains, and the relationship to M02 production work identity and M06 operational attempts. Do not decide lifecycle states or identity schemas before source and technology review.

Research record: planning/research/M11-S01-LONG-LIVED-SUPERVISOR-AND-JOB-PROCESS-MODEL.md. S01 closed for module planning through PR #85 exact head 819b184cef722a945391d96b75edeb1f74f47c99 (Governance 36065623865 / 107854567970, PASS), squash merge 8ea0871668fc182d0f0a829bee352e03a0ec7ce4, and exact-main Governance 36065770189 / 107855048099 (PASS). No architecture, identity schema, M11 contract, or implementation is selected.

### S02 — Headless/background worker startup and IPC
Status: COMPLETE_FOR_MODULE_PLANNING
Research record: planning/research/M11-S02-HEADLESS-BACKGROUND-WORKER-STARTUP-AND-IPC.md. PR #87 exact head 78893daec68aabe3bb23836a4429017f13e97f30 passed Governance 36068426412 / 107863497210 (3940/3940 tests), was protected squash-merged as b090ae68bac23be2261932e75549b3ea255990ec, and passed exact-main Governance 36068660747 / 107864233622 (3940/3940 tests; actor: KayzenRoot). S02 compares startup and IPC candidates without selecting a transport, handshake or permission model. The exact-base Context Lock matched 63/63 critical source fingerprints; the post-authoring audit found 0 HIGH and 0 CRITICAL findings. No M11 contract or implementation is admitted.
### S03 — Concurrency limits, priorities and resource leases
Status: COMPLETE_FOR_MODULE_PLANNING

Research record: planning/research/M11-S03-CONCURRENCY-LIMITS-PRIORITIES-AND-RESOURCE-LEASES.md. PR #89 corrected exact head 778218c04fb9481cab75122001deb87814ce3e68 passed Governance 36189044035 / 108249450672 (3940/3940 tests), was protected squash-merged as ad3c4ac4aa84890248fbc7e6250bea2de271fd65, and passed exact-main Governance 36189379137 / 108250522233 (3940/3940 tests; actor: KayzenRoot). Its Context Lock matched 68/68 exact-base source fingerprints and the post-authoring documentation audit found 0 HIGH, 0 CRITICAL and 0 residual findings. The S03 checkpoint/evidence closeout passed exact-main Governance before S04 began. No M11 contract is frozen and no implementation is admitted.

Plan queue/concurrency responsibility, priority and fairness questions, backpressure, workstation headroom, and the handoff to M09 resource claims/leases and M12 placement/orchestration. Do not grant, reserve, release, or assert resource truth.

### S04 — Process reaper, zombie detection and shell-free execution
Status: COMPLETE_FOR_MODULE_PLANNING

Research record: planning/research/M11-S04-PROCESS-REAPER-ZOMBIE-DETECTION-SHELL-FREE-EXECUTION.md. Proposal base 61864d387b20b6cb283ccfec12ab5cf6f2ffaa14; proposal head 7bd29099adfe3c4b2035e3da1ab9c09349e95001 passed PR-head Governance run 36213241691 / job 108323991494 (3940/3940 tests). PR #92 was protected squash-merged as f779cec13d0877cf9c5ac6797a49c5ef85389d0b; exact-main Governance run 36235782621 / job 108387156827 passed (3940/3940 tests). The proposal Context Lock matched 74/74 source fingerprints. A prior chat review recorded APPROVED with 0 HIGH/CRITICAL findings; there is no formal GitHub review record. The separate closeout Context Lock binds this checkpoint delta to base tree 222627601b9a72fe17ae8253184f88d4620b5f7f and matches 77/77 source fingerprints. No process architecture or policy is selected; S04-U01 through S04-U21 remain unresolved. PR #93 closeout is complete on main; S05 now proceeds as a separate proposal from exact base e0d8aeeea676d884e9c6a716df42a363f0765020 / tree b82ddfb80b7ff57f409b9d48f07263b7c7d356a2. M11 remains NOT_FROZEN; M11/M10 implementation remain NOT_ADMITTED.

### S05 — Cancellation, timeout, crash recovery and workstation coexistence
Status: PROPOSED_NOT_COMPLETE

Research record: planning/research/M11-S05-CANCELLATION-TIMEOUT-CRASH-RECOVERY-WORKSTATION-COEXISTENCE.md. Proposal base e0d8aeeea676d884e9c6a716df42a363f0765020 / tree b82ddfb80b7ff57f409b9d48f07263b7c7d356a2; branch iris-wo-0015-m11-s05-cancellation-recovery-20260926; Context Lock: .engineering/context-locks/IRIS-WO-0015-S05.json. This proposal compares coroutine and platform cancellation/timeouts, records crash/restart/partial-output questions, preserves M02/M06/M09/M12 and M54/M56/M60 boundaries, and leaves recovery journaling and all owner decisions open. Exact-head Governance remains required. Stop with the planning PR open; do not perform HEDS, merge, S05 closeout, final technology review, forward scan, M11 freeze, or implementation in this increment.

## Required outputs before an M11 contract can be proposed

1. Complete all five sessions in order and persist each session’s research, options, decisions, unknowns and evidence in Git.
2. Evaluate existing technologies, proven internal reuse and IRIS-owned candidates using the Slow Planning Protocol. Record stable IDs, classification, purpose, operating model, benefits, dependencies, risks/failure modes, benchmark/proof plan, status and destination.
3. Complete a Final Technology Review with ACCEPT / SUPERSEDE / REJECT decisions and rationale.
4. Complete a Forward Compatibility Scan for M12–M60 and all relevant M10 handoffs. Distinguish canonical owner-contract facts from index-level candidate assumptions.
5. Prepare a versioned M11 owner-contract candidate and an independent planning audit. Do not freeze while HIGH/CRITICAL findings or unresolved authority conflicts remain.
6. Keep M11 implementation and M10 implementation NOT_ADMITTED.

## Explicitly unresolved

No M11 contract version, public API, IPC protocol, permission model, process-state machine, cancellation/timeout semantics, retry/recovery policy, concurrency limit, lease handshake, priority policy, shell invocation rule set, platform adapter, or numerical headroom is selected here. No M12–M60 detail is treated as known beyond its available canonical contract.
