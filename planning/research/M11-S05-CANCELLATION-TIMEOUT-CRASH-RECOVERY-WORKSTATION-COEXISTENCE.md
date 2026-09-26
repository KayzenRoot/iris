# M11 S05 — Cancellation, Timeout, Crash Recovery and Workstation Coexistence

Status: PROPOSED_FOR_MODULE_PLANNING; S05 IS NOT COMPLETE
Work Order: IRIS-WO-0015 / Issue #82
Planning base: e0d8aeeea676d884e9c6a716df42a363f0765020
Base tree: b82ddfb80b7ff57f409b9d48f07263b7c7d356a2
Branch: iris-wo-0015-m11-s05-cancellation-recovery-20260926
Context Lock: .engineering/context-locks/IRIS-WO-0015-S05.json
S04 closeout: PR #93, merged as e0d8aeeea676d884e9c6a716df42a363f0765020; exact-main Governance run #415 / 36244566768, job 108411232665, PASS
M11 contract: NOT_FROZEN
M11 implementation: NOT_ADMITTED
M10 contract: m10-contract-v1.0 (FROZEN)
M10 implementation: NOT_ADMITTED
IRIS-WO-0014 preflight: BLOCKED
Research checked: 2026-09-26
HIVE evidence: NOT_USED for IRIS. The registered IRIS HIVE context was stale; exact Git sources are used. HIVE v1.0.0 project status was READY at pinned commit a53b5b9fcf55c32a5696180fb1b1ef80ccd1edcf.

## Objective and scope

Compare documented cancellation and timeout layers, platform process-interruption mechanisms, crash/restart recovery questions, partial-result boundaries, and workstation coexistence requirements. Record source facts, carefully separated planning inferences, technology alternatives, ownership, failure cases, future proof work, and unresolved decisions. This is a proposal for S05 planning only. It selects no API, process-control mechanism, timeout scope/value, escalation sequence, restart behavior, journal, retry rule, cleanup guarantee, headroom formula, or workstation policy.

The accepted change is documentation and evidence only. No worker, child process, provider, IPC endpoint, DCC application, machine resource, or lease was started, inspected, interrupted, recovered, measured, or changed. No experiment, benchmark, timing test, or hardware measurement was run. Repository inspection was read-only. Any future process or runtime test requires a separate implementation Work Order and its own safety gates.

## Exact base and S04 gate reconciliation

- The current branch was created from exact `main` SHA `e0d8aeeea676d884e9c6a716df42a363f0765020`, tree `b82ddfb80b7ff57f409b9d48f07263b7c7d356a2`; the checkout was clean before authoring.
- S04 checkpoint/evidence closeout PR #93 had HEDS verdict APPROVED on exact proposal head `6e9e717ecacacfbef787a53ffbf0254f1188323c` (separate read-only reviewer task; no formal GitHub review was submitted), then protected squash merge `e0d8aeeea676d884e9c6a716df42a363f0765020`. Exact-main Governance run #415 (`36244566768`, job `108411232665`) passed on that merge SHA, including the repository suite (3,940/3,940).
- PR #93's closeout Context Lock bound base `f779cec13d0877cf9c5ac6797a49c5ef85389d0b` / tree `222627601b9a72fe17ae8253184f88d4620b5f7f` and matched 77/77 Git blob fingerprints. This S05 proposal recompiles its own Context Lock against the exact current main, not the prior closeout base.
- Issue #82 is OPEN. The canonical checkpoint and session map showed S05 NOT_STARTED at the base; this proposal begins the S05 planning increment but does not complete the session.
- S01–S04 remain COMPLETE_FOR_MODULE_PLANNING. M11 remains NOT_FROZEN; M11/M10 implementation remain NOT_ADMITTED; M10 stays frozen at `m10-contract-v1.0`; IRIS-WO-0014 remains BLOCKED.

## Requirements and authority boundaries

| Authority/source at the exact base | Canonical fact | S05 boundary |
| --- | --- | --- |
| `docs/project-brain/02-REQUIREMENTS.md`, PR-008 | The runtime must manage worker lifecycle, concurrency, cancellation, cleanup, and orphan/zombie detection. | Requirement; it does not choose implementation, signal, timeout, retry, or cleanup semantics. |
| `docs/project-brain/02-REQUIREMENTS.md`, PR-009 | Workstation CPU/RAM/VRAM headroom is configurable. | No default, numerical headroom, estimator, intervention, or process-throttling policy is selected here. |
| M02, `planning/modules/M02-PROJECT-OS-PRODUCTION-GRAPH.md` §§23, 26–28 | Cancellation cannot promote partial work to successful materialization; committed immutable revisions remain historical facts, uncommitted temporary outputs are not promoted, downstream nodes remain dirty/blocked, and a retry creates a new attempt. | Preserve M02 semantic causality, ExecutionPlan, production lifecycle, commit/admission, and external-side-effect fences. M11 does not decide materialization success. |
| M06, `docs/M06-PRODUCTION-STATE-KERNEL.md` and `planning/modules/M06-PRODUCTION-STATE-VERSIONING-INCREMENTAL-MEDIA-BUILD.md` | Operational revision, attempt evidence, reproducibility, reconstruction, partial recovery, and historical receipts have explicit owner boundaries. Historical receipts are not rewritten; unknown, partial, stale, or corrupt evidence cannot be promoted to complete evidence. | M06 owns operational revision/materialization lineage and attempt evidence. The process-to-attempt mapping and `ExecutionAttemptPort` payload remain unresolved; M11 cannot infer them. |
| M09, `planning/modules/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md` §§S03 hard invariants 231–245, 261–270, 272–275, 288–290 and `iris_resource_twin/invariants.py` M09-INV-0408/0474 | Transfer cancellation has explicit owner outcomes; cancellation cannot silently release residency; resume requires compatible capability; retry identity is stable/idempotent; transfer deadlines and resource ownership are M09 concerns. An expired lease alone does not prove a process can be terminated. | M11 must not create, renew, release, or infer M09 claims, leases, residency, capacity, or safe process termination from lease expiry. M09 S03 transfer semantics do not become worker-process semantics. |
| M10 `m10-contract-v1.0` and WO-0014 | M10 recommendations are advisory and cannot dispatch, place, reserve resources, or control workers/processes; WO-0014 preflight remains BLOCKED. | No M10 recommendation is a cancellation command, recovery instruction, capacity grant, or authority to terminate a worker. |
| M12–M60 dependency register / master index | M12 placement/orchestration, M26 DCC integration, M54 security/trust/environment, M55 physical storage/deletion, M56 telemetry, and M60 platform/service/recovery/acceptance details are not backed by individual canonical owner contracts at this base. | The exhaustive dependency register marks owner handoffs PENDING_OWNER_CONTRACT and supplies a closure checklist, not owner-specific lifecycle or process semantics. Treat individual details as pending. |

## Terminology kept separate for review

- **Cancellation request** is an intent/evidence event; it is not proof that a coroutine, process, descendant, provider operation, or side effect stopped.
- **Timeout/deadline observation** says a selected waiting/execution interval elapsed under some clock and scope; it does not establish the process result or authorize termination.
- **Python task cancellation** is cooperative exception delivery at an await point; it is separate from operating-system process signaling.
- **Child-process interruption/exit** is platform evidence about an operating-system process object or child relationship; it is not by itself M02 materialization acceptance or an M06 attempt result.
- **Supervisor/host crash** may leave incomplete or unknown process and output state. It is not automatically a failed, cancelled, or retryable production attempt.
- **Recovery** is a future owner-defined reconciliation action against M02/M06/M09/M55 facts. It is not automatically resume, replay, retry, cleanup, rollback, or lease release.
- **Workstation coexistence** is a requirement to keep operator work and admitted work within separately owned resource/security boundaries. An OS process count, CPU cap, memory limit, M09 claim, and VRAM observation are not interchangeable.
## Sourced technology facts and options

All candidates below are comparison records only. They are PROPOSED, not selected. Candidate IDs continue after `TECH-M11-021` from S04. No new IRIS-owned/proprietary candidate is asserted.

| Boundary | Documented option | Observed behavior | Boundary or unresolved issue |
| --- | --- | --- | --- |
| Coroutine cancellation | Python 3.12 `asyncio.Task.cancel()` / `CancelledError` | Cancellation is injected at the next opportunity. A coroutine may run `finally` cleanup and generally should propagate `CancelledError`; suppressing it can interfere with structured-concurrency components. | Applies to an asyncio task, not an OS process tree. Cleanup can take time or fail; no IRIS task owner, cancellation authority, caller-visible result, or cleanup deadline is selected. |
| Grouped coroutine work | Python 3.12 `asyncio.TaskGroup` | Exiting waits for grouped tasks. A non-cancellation exception cancels remaining tasks and the group waits; termination is not a native TaskGroup operation. | Coroutine containment is not process containment. A child process launched by a task requires separate ownership and platform evidence. |
| Coroutine timeout | Python 3.12 `asyncio.timeout()` / `timeout_at()` | The scope cancels the current task and transforms its cancellation into `TimeoutError` outside the context. It uses the event-loop clock. | Does not decide whether to interrupt a child, whether cleanup is bounded, whether elapsed wall time exceeds the deadline, or how cross-process/host clocks relate. |
| Wait-for timeout | Python 3.12 `asyncio.wait_for()` | On expiry it cancels the awaited task and waits for cancellation to complete, so total elapsed time can exceed the timeout. `shield()` changes cancellation propagation. | A timeout on waiting is not a hard upper bound on process lifetime or total operation time. Ownership if work is shielded remains undefined. |
| Async child process | Python 3.12 `asyncio.subprocess.Process` | `terminate()` sends SIGTERM on POSIX and calls `TerminateProcess()` on Windows; `kill()` sends SIGKILL on POSIX and aliases `terminate()` on Windows. `send_signal()` has Windows console-event qualifications. These methods address the child process represented by that object. | Abruptness, graceful cleanup, descendants, output/partial artifacts, Windows event handling, and caller authorization differ by platform. The API does not create M11 policy. |
| POSIX process-group signal | `kill()` with a negative process-group ID | Linux documents group-directed signals and permission checks. Signal delivery is a request to processes currently in the target group; it is not a durable IRIS identity or a wait/reap contract. | Membership can differ from an application job; descendants can change grouping; numeric IDs and authorization/error results need owner-defined interpretation. No signal or escalation is selected. |
| Windows console process group | `CREATE_NEW_PROCESS_GROUP` plus `GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT)` | Console events target a group sharing the caller's console; a new console changes which processes receive the event. CTRL+C has different group targeting behavior from CTRL+BREAK. | Not a universal service/session/process-tree cancellation channel. Console attachment, control handlers, detached children, and descendants outside the console group remain open. |
| Windows Job Object | Job membership / job termination APIs | A job can manage associated processes as a unit; `CreateProcess` children join by default subject to breakaway settings, while `Win32_Process.Create` children are not implicitly associated. `TerminateJobObject` terminates currently associated processes. Nested-job and host constraints apply. | Membership is not proof of complete ancestry; assignment, nesting, breakaway and security can fail or exclude descendants. Termination is destructive and remains unauthorized in this planning session. |
| Linux cgroup v2 | `cgroup.kill` in a non-root cgroup | The kernel documentation describes writing `1` as killing the cgroup and descendant cgroups; threaded cgroups reject the operation because it is process-directed. | Requires an owner-defined cgroup placement/lifecycle/permission model and supported kernel/host configuration. It is not graceful cancellation, a portable API, resource truth, or artifact cleanup. |

### TECH-M11-022 — Python 3.12 asyncio task cancellation and TaskGroup

- Classification: Existing standard-library technology; cancellation-layer comparison.
- Status: PROPOSED.
- Purpose / operating model: Request cancellation of a coroutine task, allow exception/finally handling, and wait for grouped tasks through structured-concurrency scopes.
- Benefit: Documented task cancellation and group-completion behavior; makes cancellation propagation and cleanup opportunities inspectable at the coroutine layer.
- Dependencies: Python 3.12 event loop and participating coroutine behavior.
- Risks / failure modes: A coroutine can suppress cancellation; cancellation is cooperative; cleanup may take longer or raise; TaskGroup is not a process tree or native force-termination API.
- Future proof plan: After M11/M54/M60 define the public caller and lifecycle contract, add deterministic coroutine-only contract tests for cancellation propagation, suppressed cancellation, group sibling handling, cleanup exceptions, and result evidence. Do not launch a real child process as part of this plan.
- Destination: Possible future M11 coroutine boundary; M02/M06 outcome and attempt authority remains intact.

### TECH-M11-023 — Python 3.12 asyncio timeout scopes and wait_for

- Classification: Existing standard-library technology; timeout-layer comparison.
- Status: PROPOSED.
- Purpose / operating model: Bound an asyncio scope using the event-loop clock, or await an operation with cancellation-on-timeout behavior.
- Benefit: Standard library supplies relative and absolute timeout scopes and explicit waiting behavior.
- Dependencies: Event-loop clock semantics, awaited operation cancellation behavior, Python 3.12.
- Risks / failure modes: `wait_for()` may exceed its nominal timeout while awaiting cancellation; timeout scope cancellation may be swallowed or delayed; waiting timeout does not terminate an OS process; shielded work may outlive its caller.
- Future proof plan: Once owner contracts define timeout scope, clock, cleanup and caller-visible outcome, use fake-clock or coroutine-only tests for deadline boundaries, nested scopes, cleanup-overrun and shield ownership. No numerical default or retry is selected.
- Destination: Possible M11 coroutine waiting layer; no process timeout or product deadline is implied.

### TECH-M11-024 — Python 3.12 asyncio subprocess Process interruption

- Classification: Existing standard-library technology; process-operation comparison.
- Status: PROPOSED.
- Purpose / operating model: Await a direct child, collect its return code, and expose platform-specific `send_signal()`, `terminate()` and `kill()` methods.
- Benefit: Standard library associates process-wait evidence with the direct child object and documents platform divergence.
- Dependencies: Event-loop subprocess backend, child ownership, executable/platform support, stream handling, Python 3.12.
- Risks / failure modes: Windows `terminate()` is TerminateProcess, which does not provide application cleanup; POSIX signal behavior differs; direct child methods do not settle descendants; `wait()` has no timeout argument; undrained pipes can deadlock.
- Future proof plan: After M54/M60 authorize a support matrix, test mocked state transitions and isolated platform-specific child fixtures for return codes, signal status, cancellation races and stream draining. Any actual process termination test needs a separate implementation Work Order.
- Destination: Future M11 launcher/observer discussion only; M06 still owns attempt evidence and M02 outcome.

### TECH-M11-025 — POSIX process-group signal delivery

- Classification: Existing POSIX/Linux process-group facility.
- Status: PROPOSED.
- Purpose / operating model: Send a signal to a process group through the documented group ID form.
- Benefit: Can address multiple current group members using an OS primitive.
- Dependencies: POSIX/Linux platform support, group membership, signal permissions, session/group setup and stable owner tracking.
- Risks / failure modes: A group ID is not a durable workload identity; membership can change; permission failure, non-existent/stale groups and partial delivery require explicit evidence; signal delivery does not wait for or reap children.
- Future proof plan: If M60 and M54 select support and authorization conditions, test membership transitions, permissions and observed completion in isolated disposable fixtures. Do not signal user processes or infer production ownership from a PID.
- Destination: Possible POSIX adapter comparison for M11/M60; no signal, escalation, grace interval or cleanup guarantee selected.
### TECH-M11-026 — Windows console process-group control event

- Classification: Existing Windows console API and process-creation flag.
- Status: PROPOSED.
- Purpose / operating model: Create a new console process group and deliver a supported control event to processes sharing the caller's console.
- Benefit: Offers a cooperative console-handler event distinct from immediate process termination.
- Dependencies: Console process model, shared console, CREATE_NEW_PROCESS_GROUP, target handler behavior, Windows API support.
- Risks / failure modes: Detached/non-console/service execution may not share the console; newly created consoles change recipients; handlers can delay or otherwise affect completion; it is not Job Object membership or a guarantee of process-tree coverage.
- Future proof plan: Only after M60 identifies a console-capable support case, validate recipients and event completion in an isolated disposable Windows fixture, including detached/new-console children. No user workstation process is targeted.
- Destination: Possible Windows interactive-process comparison; not a universal M11 cancellation mechanism.

### TECH-M11-027 — Windows Job Objects for process grouping and termination

- Classification: Existing Windows platform technology; S05 re-evaluation of TECH-M11-002, TECH-M11-013 and TECH-M11-021.
- Status: PROPOSED.
- Purpose / operating model: Track processes associated with a job object and, if separately authorized by a future contract, perform group-level operations.
- Benefit: Provides a kernel-managed process grouping and completion/limit surface; documented child association can include `CreateProcess` descendants.
- Dependencies: Windows version, assignment rights, nested-job/service host conditions, process-creation route and breakaway configuration.
- Risks / failure modes: Breakaway and alternate creation routes can exclude children; assignment can fail; `TerminateJobObject` terminates processes rather than requesting application cleanup; kill-on-close behavior can be destructive; group completeness is not guaranteed.
- Future proof plan: If a future owner contract permits the mechanism, prove association coverage, host nesting, breakaway, exit observation and handle lifecycle across M60-supported Windows configurations. Termination policy and output handling require a separate implementation authorization.
- Destination: Possible M11/M60 process-containment option; no selection or termination authorization.

### TECH-M11-028 — Linux cgroup v2 `cgroup.kill`

- Classification: Existing Linux kernel cgroup v2 facility.
- Status: PROPOSED.
- Purpose / operating model: Request kernel-directed fatal termination of processes in a non-root cgroup subtree.
- Benefit: Documented cgroup-level operation covers descendants placed in the cgroup tree rather than relying on a single PID.
- Dependencies: cgroup v2 enabled, writable/owned cgroup subtree, host delegation, kernel support and M60 platform contract.
- Risks / failure modes: Fatal SIGKILL leaves no application cleanup window; threaded cgroup use can fail; processes not placed there are outside the operation; privilege/delegation/host-manager coordination are unresolved.
- Future proof plan: Only after M60/M54 owner contracts and a future implementation Work Order define delegated cgroup ownership, test capability and error cases in an isolated disposable Linux environment. No cgroup operation or benchmark was run.
- Destination: Possible Linux-specific comparison for M11/M60; no support baseline, group layout, escalation or cleanup behavior selected.

## Recovery persistence and coordination boundary

The exact-base owner inventory has no M60 service/recovery contract and no M11 lifecycle contract. Therefore this session does **not** compare or select a journal format, filesystem/database, append-only log, transaction protocol, distributed coordinator, durable queue, lease recovery strategy, supervisor restart policy, or cross-host reconciliation algorithm. Their reliability claims cannot be derived from Python, Windows, or Linux API documentation. A future M60 owner source and explicit storage/security/attempt contracts are prerequisites before such comparison.

The planning questions to bring to those owners include: what facts must survive process exit or supervisor/host restart; which owner records launch intent and child identity before/after launch; how journal durability and torn writes are proven; how recovered observations are distinguished from newly performed actions; how duplicate replay is fenced by M02/M06 identities; what rights are required to reopen OS references; and how M09/M55 resources and artifacts reconcile when the OS and durable record disagree. These are unresolved questions, not proposed fields or semantics.

## Workstation coexistence options (unselected)

| Alternative for future owner review | What it could expose/control | Why it is not a decision here |
| --- | --- | --- |
| Operator-configured headroom | A product-level CPU/RAM/VRAM allowance or preference. | PR-009 says configurable; it supplies no value, units, scope, priority or policy. M09 owns resource truth and M12 placement. |
| OS-enforced process limits | Windows job limits or Linux cgroup controllers. | An OS cap is not a M09 grant, VRAM measurement, fairness policy, or evidence that interactive applications remain usable. |
| M09 evidence and lease reference | Owner-issued resource claim/lease/pressure reference. | No M11/M09 process handshake, freshness, expiry, revocation, or process-termination semantics are frozen. Expired lease does not prove process is gone. |
| Operator-session observation | Signals or telemetry about foreground workload/host pressure. | Requires M54/M56/M60 ownership, privacy and freshness rules; no process inspection or telemetry was performed here. |
| No automation / explicit unknown | Surface unsupported or unknown capability to an operator/owner. | A future owner must define visible states and allowed response; this record does not prescribe a fallback or acceptance state. |

No headroom number, CPU/RAM/VRAM formula, priority, preemption, throttle, workload admission policy, interactive-process discovery, user notification, or resource reservation is selected. M11 may not suspend or terminate unrelated operator applications. M10 recommendations do not authorize those actions.

## Failure and ambiguity matrix

| Scenario | Evidence distinction to preserve | Owner question / handoff; no response selected |
| --- | --- | --- |
| Cancellation requested before launch, during process creation, or after a child is created | Request time, launch outcome, child reference, and observed child exit are separate facts. | M11/M60 must define race ownership; M02/M06 define semantic and attempt evidence. |
| Coroutine suppresses `CancelledError`, blocks in cleanup, or raises during cleanup | Cancellation request is not task completion; cleanup may overrun the timeout. | M11 must define result and deadline scope with M54/M60; asyncio docs do not define IRIS policy. |
| Timeout fires while a child continues or a shielded operation survives | Wait expiration and child exit are distinct; total elapsed time can exceed a coroutine timeout. | M11/M60 process lifecycle and caller ownership; M06 attempt outcome; no forced termination or retry inferred. |
| Child handles SIGTERM, ignores cooperative control, exits by signal, or is killed abruptly | Signal/control request, OS exit status, output completeness, and accepted materialization remain distinct. | M02/M06 define committed/partial output and attempt evidence; M54/M60 define permission/platform semantics. |
| Descendant escapes a POSIX group, leaves a console group, or breaks away from a Windows job | Parent exit does not prove every descendant ended. | M60 platform/containment contract; M11 cannot claim process-tree cleanup from a direct-child status. |
| Job assignment, process-group delivery, cgroup operation, or signal permission fails | Unsupported, denied, stale reference, partial coverage, and observed absence are not interchangeable. | M54/M60 define error and unknown outcomes; M56 defines evidence correlation. |
| Supervisor crashes before/after launch registration or while recording exit | Durable record and live OS state can disagree or one side may be unavailable. | M60 recovery contract and M06/M02 identity/attempt ownership must define reconciliation before any recovery algorithm is compared. |
| Host restart loses volatile state; surviving or restarted provider has partial output | No process table snapshot proves an M02/M06 completion. | M02/M06/M55/M60 must define output, attempt, artifact and reconstruction state; no resume/replay/delete choice is made. |
| Cancellation overlaps M09 lease expiry, transfer, residency or a process still consuming resources | Lease state, actual process lifetime, resource occupancy, and artifact state are separate. | M09 owns resource/lease truth; M11 cannot release capacity because a cancellation request or expired lease exists. |
| Interactive DCC/GUI and worker contend for CPU/RAM/VRAM or storage | A count or limit does not establish user-visible responsiveness or safe headroom. | M09/M26/M56/M60 must define evidence, units, support, and acceptance; no benchmark or hardware measurement was performed. |
| Retry/recovery replays a non-idempotent external side effect | A new attempt is not evidence that an earlier effect did not occur. | Preserve M02 side-effect fences and M06 attempt history; M11 does not authorize replay or deduplication semantics. |
## Repository reuse and existing M11 candidates

Read-only exact-base search found no production M11 supervisor, process cancellation/recovery coordinator, worker journal, process-to-attempt registry, timeout service, or workstation headroom governor. `iris_microbenchmark/execution.py` has a bounded, synchronous M08 CPU-reference `CancellationToken` and `time.perf_counter_ns()` checks; its module contract restricts it to admitted CPU-reference probes, starts no threads/processes, and is not a worker/process lifecycle implementation. M08 cancellation behavior therefore cannot be reused as an M11 contract. Existing subprocess use in `scripts/hive_mcp.py` and `scripts/gef_preflight.py` remains narrow one-shot command execution; M01/M02 subprocesses are isolated test fixtures. No child or worker was run during this review.

- CAND-M11-001 — Reference-only work/attempt/process association: PROPOSED_UNCHANGED; S05 defines no fields or mapping.
- CAND-M11-002 — Reference-preserving startup and registration envelope: PROPOSED_UNCHANGED; S05 defines no registration order or durable journal.
- New IRIS-owned candidate: NONE. Current evidence establishes no new distinct IRIS capability with an owner contract. No novelty or patent claim is made.

## Unresolved question register and handoffs

All questions below remain open; these are planning prompts, not hidden requirements. The S04 questions `S04-U01` through `S04-U21` remain OPEN_UNCHANGED and must travel with the eventual M11 package.

| ID | Unresolved question | Owner / handoff |
| --- | --- | --- |
| S05-U01 | Who may request cancellation, through which authenticated control surface, and what authorization evidence accompanies it? | M54 / M11 / M60 |
| S05-U02 | Which cancellation scopes exist (queue, coroutine, attempt, direct child, process group, worker, host), and who owns their propagation? | M02 / M06 / M11 / M60 |
| S05-U03 | How are cancellation intent, request acceptance, signal delivery, process exit, attempt outcome, and materialization acceptance represented distinctly? | M02 / M06 / M11 / M56 |
| S05-U04 | Which deadline scopes are needed (queue wait, startup, handshake, runtime, shutdown, recovery), and who defines each clock and deadline owner? | M11 / M12 / M60 |
| S05-U05 | How do monotonic deadlines interact with suspend/resume, wall-clock evidence, remote hosts, and event timestamps? | M56 / M60 |
| S05-U06 | Is any graceful-to-forceful interruption sequence permitted, and what owner, permission, delay, and proof gate would authorize each step? | M54 / M60 / M11 |
| S05-U07 | Which terminal, partial, unknown, unsupported, denied, timed-out, cancelled, crashed, or still-running outcomes are required at each owner boundary? | M02 / M06 / M11 / M60 |
| S05-U08 | Which partial outputs remain temporary, committed, reusable, invalid, quarantined, or recoverable after cancellation or crash? | M02 / M06 / M55 |
| S05-U09 | Which source of truth survives supervisor crash, service restart, OS restart, or machine power loss? | M06 / M60; durable state/storage authority unresolved |
| S05-U10 | If a journal is permitted, what are its owner, durability, atomicity, schema evolution, corruption and retention contract? | M06 / M54 / M55 / M60 |
| S05-U11 | How does restart reconciliation prevent duplicate launch, replayed external side effect, duplicate commitment, or false completion? | M02 / M06 / M60 |
| S05-U12 | What is the safe outcome if the durable record says running while the OS reference is absent, reused, inaccessible, or ambiguous? | M06 / M11 / M54 / M60 |
| S05-U13 | What owner reconciles M09 leases, residency and capacity if a child survives after supervisor loss or cancellation? | M09 / M11 / M60 |
| S05-U14 | Who may reclaim or delete temporary/partial output, and what M06/M55 reachability/retention evidence is required first? | M06 / M55 / M54 |
| S05-U15 | What operator CPU/RAM/VRAM headroom dimensions, units, freshness, and priority rules are supported by M09? | M09 / M12 / M11 |
| S05-U16 | How do worker operations coexist with interactive DCC/GUI sessions, and which process discovery or operator controls are permitted? | M26 / M54 / M60 |
| S05-U17 | What user-visible control, notice, override, and audit behavior is required for cancellation and unknown recovery state? | M54 / M56 / M60 |
| S05-U18 | What correlation, freshness, redaction, retention, and provenance bind cancellation/recovery evidence to an attempt? | M06 / M56 |
| S05-U19 | What OS, kernel, Python, service-host and deployment matrix is supported, and what capability proof is required per platform? | M60 / M51 |
| S05-U20 | How do local cancellation, remote placement, queue ownership, and agent/operator disconnects hand off across M12? | M12 / M54 / M60 |
| S05-U21 | Which retry/restart/backoff limits, if any, are permitted, and which effects must be proven idempotent first? | M02 / M06 / M09 / M12 / M60 |
| S05-U22 | How is the process/reference/wait right from S04 kept valid across cancellation, parent exit, supervisor replacement and PID reuse? | M11 / M54 / M60; S04-U01..U17 remain open |
| S05-U23 | What proves a workstation remains within safe headroom and responsive without turning sampled or stale telemetry into a grant? | M09 / M26 / M56 / M60 |

## Future proof and benchmark plan

No experiment, benchmark, process operation, system restart, power-loss simulation, operator-workload measurement, DCC launch, lease mutation, or recovery journal test was performed. A future evidence plan, only after owner contracts and a separately admitted implementation Work Order, may include:

1. Coroutine-only contract fixtures for cancellation injection, cleanup exceptions, swallowed cancellation, nested timeouts, `wait_for()` overrun and shielded-work ownership.
2. Per-platform isolated disposable-child fixtures, only when M54/M60 authorize them, covering direct-child completion, platform-specific control/termination, group membership/breakaway, permission failure, stale handles/IDs, stream draining and descendant coverage.
3. Recovery fault-injection at documented transaction boundaries, only after an owner specifies the journal/transaction protocol, idempotency boundary, artifacts, resource ownership and permitted recovery actions.
4. Cross-platform contract evidence for Python/OS/kernel/service-host versions explicitly supported by M60; unsupported and unavailable cases must be represented separately.
5. Workstation coexistence measurements that identify machine, OS, workload, DCC, CPU/RAM/VRAM and I/O evidence provenance, freshness, interference and operator acceptance criteria. No numeric target should be introduced before M09/M26/M60 owners define it.
6. M02/M06/M09 invariants for partial output, immutable historical receipts, new attempts, lease/residency reconciliation, idempotency, and unknown-state non-promotion.

These are proof-plan options, not current tests, acceptance thresholds, implementation authorization, or benchmark results.

## S05 session result and next gate

S05 is **PROPOSED, NOT COMPLETE** on exact base `e0d8aeeea676d884e9c6a716df42a363f0765020`. Evidence establishes useful coroutine and OS-level comparison points, but does not select an IRIS cancellation API, timeout contract, signal/escalation policy, durable recovery journal, restart/retry behavior, partial-output decision, cleanup guarantee, or workstation headroom policy. The open owner handoffs and all S04-U01..U21 questions remain unresolved. M11 stays NOT_FROZEN and M11/M10 implementation stays NOT_ADMITTED. After this proposal reaches its required exact-head Governance gate, it must remain an open S05 planning PR pending separate HEDS review and merge; this Work Order increment does not include HEDS, merge, S05 closeout, Final Technology Review, Forward Compatibility Scan, M11 freeze, or implementation.

## Primary sources

Checked 2026-09-26. Source facts below describe documented API/kernel behavior only; applicability is limited to the named versions/platforms. They do not establish IRIS ownership or policy.

1. Python 3.12.14, `asyncio` Tasks, TaskGroups, cancellation and timeouts: https://docs.python.org/3.12/library/asyncio-task.html
2. Python 3.12.14, `asyncio` subprocess process methods, signal differences and platform event-loop support: https://docs.python.org/3.12/library/asyncio-subprocess.html
3. Microsoft Learn, Windows Job Objects, child association, breakaway, termination and nested-job notes (last updated 2025-07-14): https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
4. Microsoft Learn, `GenerateConsoleCtrlEvent`, process-group and same-console behavior (last updated 2021-08-26): https://learn.microsoft.com/en-us/windows/console/generateconsolectrlevent
5. Microsoft Learn, process termination and child-process behavior: https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process
6. Linux kernel documentation, Control Group v2, `cgroup.kill` and threaded-cgroup limitation: https://docs.kernel.org/admin-guide/cgroup-v2.html
7. Linux man-pages 6.19, `kill(2)`, process/group target and permissions (dated 2026-06-05): https://man7.org/linux/man-pages/man2/kill.2.html
8. IRIS canonical requirements, M02, M06, M09, M10 and session map are repository sources fingerprinted in `.engineering/context-locks/IRIS-WO-0015-S05.json`.
