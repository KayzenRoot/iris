# M11 — Background Worker Fabric & Process Lifecycle

Status: S01_COMPLETE_FOR_MODULE_PLANNING
Contract: NOT_FROZEN
Planning issue: #82
Planning Work Order: IRIS-WO-0015
Planning admission base: 0014d23115f5fec60a77e5e32d5083e90069a918
Implementation authority: NOT_ADMITTED

## Purpose

This file is the session map for the admitted M11 planning lifecycle. It is not an owner contract, implementation specification, technology decision, process policy, or authorization to launch or control workers. S01 is COMPLETE_FOR_MODULE_PLANNING; S02–S05 remain NOT_STARTED. No M11 contract is frozen by this document.

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
Status: NOT_STARTED

Plan supported startup modes and their trust boundary, worker registration/handshake, control and inspection surfaces, IPC candidate families, authentication/authorization questions, and Blender headless/background coexistence. Research platform constraints before selecting any transport or permission model.

### S03 — Concurrency limits, priorities and resource leases
Status: NOT_STARTED

Plan queue/concurrency responsibility, priority and fairness questions, backpressure, workstation headroom, and the handoff to M09 resource claims/leases and M12 placement/orchestration. Do not grant, reserve, release, or assert resource truth.

### S04 — Process reaper, zombie detection and shell-free execution
Status: NOT_STARTED

Plan owned-process tracking, descendant/orphan detection, reaping boundaries, executable and argument validation, environment/path handling, and shell-free invocation constraints. No process inspection, termination, or reaping operation is performed by this planning increment.

### S05 — Cancellation, timeout, crash recovery and workstation coexistence
Status: NOT_STARTED

Plan cancellation and timeout scopes, terminal/unknown outcomes, crash and restart recovery, partial-result handling, cleanup responsibility, and operator workstation headroom. Preserve M02/M06/M09/M12 authority and identify every unresolved decision.

## Required outputs before an M11 contract can be proposed

1. Complete all five sessions in order and persist each session’s research, options, decisions, unknowns and evidence in Git.
2. Evaluate existing technologies, proven internal reuse and IRIS-owned candidates using the Slow Planning Protocol. Record stable IDs, classification, purpose, operating model, benefits, dependencies, risks/failure modes, benchmark/proof plan, status and destination.
3. Complete a Final Technology Review with ACCEPT / SUPERSEDE / REJECT decisions and rationale.
4. Complete a Forward Compatibility Scan for M12–M60 and all relevant M10 handoffs. Distinguish canonical owner-contract facts from index-level candidate assumptions.
5. Prepare a versioned M11 owner-contract candidate and an independent planning audit. Do not freeze while HIGH/CRITICAL findings or unresolved authority conflicts remain.
6. Keep M11 implementation and M10 implementation NOT_ADMITTED.

## Explicitly unresolved

No M11 contract version, public API, IPC protocol, permission model, process-state machine, cancellation/timeout semantics, retry/recovery policy, concurrency limit, lease handshake, priority policy, shell invocation rule set, platform adapter, or numerical headroom is selected here. No M12–M60 detail is treated as known beyond its available canonical contract.