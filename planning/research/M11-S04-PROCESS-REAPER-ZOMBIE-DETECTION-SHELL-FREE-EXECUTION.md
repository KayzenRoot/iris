# M11 S04 — Process Reaper, Zombie Detection and Shell-Free Execution

Status: COMPLETE_FOR_MODULE_PLANNING
Work Order: IRIS-WO-0015 / Issue #82
Planning base: 61864d387b20b6cb283ccfec12ab5cf6f2ffaa14
Base tree: e4f4972e9514e3e6f2ad526e8ff516d8ed3c9544
Branch: iris-wo-0015-m11-s04-process-reaper-shell-free-execution-20260925
Context Lock: .engineering/context-locks/IRIS-WO-0015-S04.json
Base exact-main Governance: run 36191418025 / job 108257166485 — PASS (3,940/3,940 tests)
M11 contract: NOT_FROZEN
M11 implementation: NOT_ADMITTED
M10 contract: m10-contract-v1.0 (FROZEN)
M10 implementation: NOT_ADMITTED
IRIS-WO-0014 preflight: BLOCKED
Research checked: 2026-09-26
HIVE evidence: NOT_USED. HIVE v1.0.0 is pinned at a53b5b9fcf55c32a5696180fb1b1ef80ccd1edcf; the IRIS HIVE context was on stale source head 2432cfe29a501e18a1cdf8a46adc49cd42fdfba0. checkpoint.read returned source_not_current and the attempted context.build request was rejected as invalid arguments. No HIVE-derived evidence is used.

## Purpose and scope

Compare existing technologies and proven repository reuse for process identity, direct-child waiting and reaping, zombie/orphan observation, descendant/group containment, and shell-free process creation. Record source facts, planning inferences, candidate tradeoffs, owner boundaries and unresolved questions. This is planning only. It selects no M11 architecture, process policy, executable allowlist, environment policy, platform baseline, state machine, cleanup guarantee, timeout or retry rule.

No real process was inspected, launched, signaled, terminated, waited for, or reaped. No IPC, provider or DCC application was run; no resource or lease was changed; no hardware was measured. Repository review was read-only.

The user authorized the existing repository tests/CI to start only isolated Python child processes needed by the suite. This exception does not authorize IRIS workers or other real process, provider, DCC, IPC, resource or hardware operations. No test, runtime or script file is changed.

## Canonical facts and authority boundaries

- Issue #82 admits M11 planning documentation. The exact base is `61864d387b20b6cb283ccfec12ab5cf6f2ffaa14` and its recursive tree is `e4f4972e9514e3e6f2ad526e8ff516d8ed3c9544`; the pinned exact-main Governance run passed on that SHA.
- S01-S03 were complete for module planning. S04 is complete for module planning after PR #92 exact-head Governance, protected squash merge and exact-main Governance passed. The separate checkpoint/evidence closeout passed its own review gate: PR #93 was HEDS APPROVED on exact head 6e9e717ecacacfbef787a53ffbf0254f1188323c, protected squash-merged as e0d8aeeea676d884e9c6a716df42a363f0765020, and exact-main Governance #415 (36244566768 / 108411232665) passed. This current S05 planning proposal does not complete S05.
- M02 owns semantic work identity, Production Graph causality, canonical ExecutionPlan and production lifecycle/acceptance.
- M06 owns operational revisions, materialization lineage and attempt evidence. Its ExecutionAttemptPort payload and the mapping from a process to an operational attempt remain unresolved.
- M09 owns resource truth, claims, leases, reservations, residency and resource-control outcomes. S04 does not create or mutate them.
- M10 remains frozen at `m10-contract-v1.0`; its recommendations cannot dispatch, place, reserve or control a process. WO-0014 preflight remains BLOCKED.
- No M11 owner contract or version exists. M12-M60 individual owner-specific semantics remain pending where their canonical contract is absent. In particular, placement and orchestration (M12), DCC integration (M26), identity/trust/environment (M54), telemetry/correlation/retention (M56), and platform/service/recovery/acceptance (M60) cannot be inferred from the module index or dependency register.

## Sourced technology facts

### Identity and reaping differ by operating system

**Linux wait and zombie facts.** Linux `wait()`, `waitpid()` and `waitid()` report state changes for children of the calling process. Waiting for a terminated child releases its associated resources; a terminated child that has not been waited for remains a zombie and retains a minimal PID/status/resource record. If its parent exits, Linux reparents a zombie child to init or the nearest configured child subreaper, which may then wait for it. The Linux manual identifies this interface as POSIX.1-2024, but it also documents Linux-specific behavior. This means an application-level "job ended" flag, a process-table scan and a successful child wait are different evidence.

**Linux pidfds.** A pidfd is a file descriptor referring to a process task. Linux documents pidfd support from kernel 5.3; the descriptor can be monitored for exit, and a pidfd for a child can be waited on with `waitid()`. Opening a pidfd for an existing numeric PID has race conditions: the documented guarantee for a child that already exited depends on SIGCHLD disposition and whether another thread/handler has already reaped it. A pidfd does not grant wait authority over arbitrary non-child processes and is Linux-specific.

**Windows process handles and jobs.** `CreateProcessW` returns process/thread handles plus IDs. Microsoft documents that the handles remain valid until closed, including after termination, while the process identifier is valid only until the process terminates. A raw PID or parent PID therefore cannot be treated as a durable identity. Windows Job Objects can manage a group of associated processes. Child processes created through `CreateProcess` join by default, but breakaway settings can exclude children; processes created through `Win32_Process.Create` are not implicitly associated. Nested jobs were introduced in Windows 8 / Windows Server 2012, and the documented hierarchy can cover only part of a process tree.

**Planning inference.** There is no single portable "reap any descendant" operation established by these sources. Linux wait semantics attach to children and OS reparenting; Windows offers process handles and Job Object membership. Any future ownership claim must be tied to an owner-issued launch/reference and the platform's actual wait/containment capability. A process name, path, parent PID or numeric PID alone does not prove that a process belongs to a particular IRIS job or attempt.

### Shell-free invocation is a boundary, not a complete trust policy

Python 3.12.14 recommends a sequence of arguments and defaults `shell=False`; without an explicit shell, Python does not implicitly choose a command shell. The full executable path is the most reliable lookup. Executable resolution, `cwd` and `env` lookup behavior vary between POSIX and Windows; providing `env` replaces inheritance rather than extending it. On Windows the underlying CreateProcess API consumes a command-line string, so a sequence is converted before the target program parses it. Python also warns that Windows `.bat` and `.cmd` files may be launched through a system shell even when `shell=False`.

**Planning inference.** An argument vector reduces shell metacharacter interpretation, but does not establish that the selected executable, current directory, PATH, environment, inherited handles, target-specific argument parser or file contents are trusted. M54 owns executable authorization, environment/secrets and sandbox semantics; S04 does not define an allowlist or default.

### Groups and containment do not settle reaping ownership

Python exposes POSIX `start_new_session` and `process_group` parameters. Linux `setpgid()` can change a process group subject to parent/child and same-session rules; `setsid()` creates a new session and process group when the caller is eligible. Linux `waitpid` can select children by process-group ID. These facilities have different purposes: group membership is not a durable job/attempt identity and does not define who owns wait/reap duties. Windows Job Objects also depend on successful association and breakaway/host constraints. The actual guarantees required for workstation or service deployments belong in M60's platform and acceptance contract.

## Technology candidates

These are comparison records only. Each remains PROPOSED and none is selected. IDs were checked against the exact-base evidence bundle. S04 is complete for module planning; S04-U01 through S04-U21 remain unresolved. S05 was NOT_STARTED at the S04 research base; after PR #93 closeout and exact-main Governance #415, the separate S05 planning proposal is now in progress and remains incomplete.

### TECH-M11-016 — Python 3.12 subprocess argument-vector launch

- Classification: Existing standard-library technology; re-evaluation of TECH-M11-001 from S01 for S04's argument and executable boundary.
- Status: PROPOSED.
- Purpose / operating model: `subprocess.run` for a completed direct child; `Popen` when the caller must retain a process object and observe its direct child. A sequence of arguments with the default `shell=False` avoids constructing a shell command for ordinary executable targets.
- Benefit: Standard-library support for explicit executable, `cwd`, `env`, stdio, return code and child wait.
- Dependencies: Supported Python version, platform process-creation API and the target executable's own argument parser.
- Risks / failure modes: Cross-platform executable search differs; `env` replaces inheritance; Windows argument sequences become a string for CreateProcess; `.bat`/`.cmd` can still invoke a shell; a direct-child `Popen` object does not define descendant ownership.
- Future proof plan: Add non-running contract fixtures and CI tests over argv boundaries, path/cwd/env inputs, launch errors and result evidence after M54/M60 define support. Any actual process test remains separately authorized.
- Destination: Possible future M11 launcher boundary; M54 trust/environment and M60 support requirements remain prerequisites.

### TECH-M11-017 — POSIX/Linux wait, waitpid and waitid

- Classification: Existing POSIX interface with documented Linux behavior.
- Status: PROPOSED.
- Purpose / operating model: Observe status changes and collect a child process result within the caller's child relationship.
- Benefit: Kernel-defined child exit/status collection, including the distinction between terminated-but-not-waited zombies and collected children.
- Dependencies: Parent/child relationship, OS behavior, signal disposition and platform-specific wait API support.
- Risks / failure modes: Not a general wait/reap API for arbitrary processes; status may be collected elsewhere; SIGCHLD and SA_NOCLDWAIT alter zombie/wait behavior; Linux child subreaper behavior is not a portable application contract.
- Future proof plan: Once M60 sets the platform matrix, test documented wait/error cases in isolated fixtures and verify that a child result is bound to an owner-issued launch reference and M06 evidence.
- Destination: Future M11 lifecycle research, subject to M60 platform ownership and M06 attempt evidence mapping.

### TECH-M11-018 — Linux pidfds

- Classification: Existing Linux kernel technology; S04 re-evaluation of TECH-M11-003 from S01.
- Status: PROPOSED.
- Purpose / operating model: Hold a file descriptor referring to a specific process task; monitor it and, for a child, use `waitid()`.
- Benefit: Object-like reference and readiness observation are less exposed to later numeric-PID reuse than storing only a PID.
- Dependencies: Linux kernel 5.3+ for pidfd_open; kernel/libc/API availability and file-descriptor lifecycle.
- Risks / failure modes: Linux-only; opening by PID is still a lookup race; child wait guarantee has SIGCHLD/other-reaper conditions; pidfd does not confer permission or child-wait ownership.
- Future proof plan: After M60 selects supported kernels, verify creation races, descriptor closure, poll/readiness and child-wait rights without signaling or terminating a production process.
- Destination: Possible Linux-specific identity/observation adapter; no cross-platform contract implied.

### TECH-M11-019 — POSIX process groups and sessions

- Classification: Existing POSIX platform facility.
- Status: PROPOSED.
- Purpose / operating model: Organize processes into sessions/groups; Python can request a new session or process group when creating a child.
- Benefit: A kernel-recognized grouping primitive that can be considered for launch-time ownership and group-scoped observation.
- Dependencies: POSIX support, launch flags, group/session inheritance rules and host policy.
- Risks / failure modes: Group membership is not canonical job/attempt identity; descendants can change session/group; group operations do not by themselves specify who may signal, wait for, or reap each child.
- Future proof plan: If a later owner contract considers groups, test inheritance, setsid/setpgid transitions and escaped-descendant detection on each supported OS without exercising cleanup policy.
- Destination: Candidate for future M11/M60 interop review only; no signal or termination rule is selected.

### TECH-M11-020 — Windows CreateProcess and process handles

- Classification: Existing Windows platform technology.
- Status: PROPOSED.
- Purpose / operating model: Create a process with explicit application/command-line, environment and current-directory parameters; retain returned process/thread handles and IDs.
- Benefit: Retaining a process handle preserves a reference to its process object beyond termination until the handle is closed; launch can return status and handles.
- Dependencies: Windows API/runtime, handle rights and inheritance, a valid executable path and M60's supported Windows matrix.
- Risks / failure modes: IDs are only lifetime-scoped; command-line parsing is target-specific; search-order ambiguity can select another executable; inherited handles affect security; handles require closure; CreateProcess returns before process initialization is complete.
- Future proof plan: Review exact API/version and test path, command-line, environment, handle inheritance and close/result evidence in an isolated Windows CI fixture after M54/M60 contracts exist.
- Destination: Possible Windows-specific launch/identity adapter; no M11 public API or trust policy is selected.

### TECH-M11-021 — Windows Job Objects

- Classification: Existing Windows platform technology; S04 re-evaluation of TECH-M11-002 (S01) and TECH-M11-013 (S03) for descendant observation.
- Status: PROPOSED.
- Purpose / operating model: Associate processes with a job object and receive a grouping/notification surface for associated processes.
- Benefit: Can represent a managed process group and expose lifecycle/resource-limit events where all relevant descendants remain associated.
- Dependencies: Windows version, successful assignment, parent job hierarchy, breakaway settings, process creation mechanism and host/service environment.
- Risks / failure modes: Breakaway settings can exclude descendants; `Win32_Process.Create` children are not implicitly associated; nested jobs and host constraints vary; Job Object membership is not equivalent to the complete process tree.
- Future proof plan: On every M60-supported Windows host, test association, breakaway, nested-job restrictions, process creation route and notification loss. Do not test termination behavior until a separate implementation Work Order authorizes it.
- Destination: Possible Windows-specific containment/observation option for M11/M60 review; no containment guarantee is claimed.

No proprietary candidate is added: the sources do not establish an IRIS-owned capability with a distinct semantic contract. No novelty or patent claim is made.

## Repository reuse review

Read-only search at the pinned default-branch source found:

- `scripts/hive_mcp.py` constructs a Docker Compose argv and invokes `subprocess.run(..., cwd=..., check=False)`. This is a narrow one-shot bridge command; it does not demonstrate a persistent supervisor, child registration, descendant tracking or a reaping contract. The command was not run.
- `scripts/gef_preflight.py` invokes `git rev-parse HEAD` through `subprocess.check_output` to verify a pinned checkout. This is a one-shot Git query, not process lifecycle management. The script was not run.
- The M01/M02 domain-neutrality tests launch Python child interpreters with `sys.executable -c` and captured outputs; M02 also uses a temporary directory and explicit environment. These are existing test-fixture subprocesses, not IRIS workers. The user authorized only those isolated Python test/CI children for the suite.
- Search results did not establish any IRIS-owned PID/handle registry, child-wait owner, descendant containment adapter, orphan-recovery loop, process-to-attempt mapping or process-control policy. HIVE/UGAS/CORE reuse remains unverified because the current HIVE source was stale and no usable HIVE-derived evidence was obtained.

## Existing IRIS-owned candidates

- CAND-M11-001 — Reference-only work/attempt/process association: PROPOSED_UNCHANGED. S04 does not define fields or mappings.
- CAND-M11-002 — Reference-preserving startup and registration envelope: PROPOSED_UNCHANGED. S04 does not invent its schema or lifecycle.

## Decisions, options and unresolved questions

**Architecture decision: NONE.** The research does not select a process identity, platform adapter, group containment method, reaper owner, process-state machine, shell rule, executable policy, environment rule, OS baseline or cleanup guarantee. All candidates remain PROPOSED.

| ID | Unresolved question | Owner / handoff |
| --- | --- | --- |
| S04-U01 | Which owner-issued identity can bind a process to a semantic job without replacing M02 work identity or ExecutionPlan? | M02 / M11 |
| S04-U02 | How, if at all, does a process reference map to M06's operational attempt and evidence? | M06; ExecutionAttemptPort payload unresolved |
| S04-U03 | Which component may create, observe, wait for, collect, reap or clean up each direct child? | M11 / M60 |
| S04-U04 | Which state is OS process evidence versus M06 attempt outcome, and how are unknown or contradictory results represented? | M06 / M11 / M56 |
| S04-U05 | What child relationship grants wait/reap rights, and who inherits that duty when a parent exits? | M11 / M60 |
| S04-U06 | How are Linux orphan reparenting and optional subreaper behavior handled without assuming the original parent retains ownership? | M60 / M11 |
| S04-U07 | Which identity remains safe when a numeric PID or parent PID is stale or reused? | M11 / M60 |
| S04-U08 | Which descendant mechanisms are supported, and what happens when a child escapes a POSIX group or breaks away from a Windows Job Object? | M60 / M11 |
| S04-U09 | How do existing host jobs, nesting restrictions, privileges and handle inheritance affect a Windows deployment? | M60 / M54 |
| S04-U10 | Which OS/kernel versions and launch mechanisms are supported and tested? | M60 |
| S04-U11 | Which wait/open/assignment errors are evidence of failure, permission denial or an unknown state, including ECHILD and stale references? | M11 / M60 |
| S04-U12 | What evidence is emitted for launch error, child exit status, signal termination, incomplete initialization and partial output? | M06 / M56 / M60 |
| S04-U13 | What argument boundary is accepted for shell-free execution, and how are Windows batch files treated? | M11 / M54 / M60 |
| S04-U14 | Who authorizes the executable and validates its path, search order, working directory, file replacement and target-specific argument parsing? | M54 / M60 |
| S04-U15 | Which environment variables are inherited, replaced, redacted or excluded, and how are secrets protected? | M54 |
| S04-U16 | Which correlation IDs, freshness, redaction and retention rules apply to process-lifecycle evidence? | M56 |
| S04-U17 | What platform-support and acceptance evidence must M60 require for descendant observation or cleanup claims? | M60 / M51 |
| S04-U18 | How do process launch and observation hand off to M12 placement, remote orchestration and queue ownership? | M12 |
| S04-U19 | Which Blender/DCC process wrappers, version support and application-startup evidence belong to M26? | M26 / M60 |
| S04-U20 | Which cancellation, timeout, restart, retry, partial-result, recovery and workstation-coexistence questions remain for S05 or another owner? | S05 / M06 / M60 |
| S04-U21 | Can HIVE/UGAS/CORE provide current, source-verifiable process-lifecycle evidence in a later planning session? | HIVE source owner; currently unresolved |

## Validation and gates

- Exact base SHA/tree and base Governance are bound in the Context Lock.
- The Context Lock fingerprints all critical exact-base sources. It includes the two test files whose isolated Python subprocesses prompted the stop, plus the S03 closeout audit.
- PR #92 changed exactly four authorized proposal documentation/evidence paths; its proposal Context Lock matched 74/74 sources. This closeout proposal changes exactly the 11 paths listed in its Context Lock and audit. No runtime, test, script, validator or workflow path is changed.
- PR #92 proposal evidence and Context Lock were checked against its exact four-path proposal. For this checkpoint closeout, the Evidence and Context Lock JSON parse and cross-check against the exact 11-path authorization; the 77/77 source hashes were recomputed at the bound base, `git diff --check` passed, and `python scripts/validate_governance.py` passed locally.
- PR #92 exact-head Governance completed the Python 3.12 bootstrap compilation, governance validator and full repository suite. The first submitted PR #93 head `17de559d4d04963ff8a086b571ce61bd770cbea0` subsequently passed exact-head Governance run #413 (`36239758962`, job `108397938994`) with 3,940/3,940 tests. That receipt applies only to that SHA; every later head requires fresh exact-head Governance. No local repository test suite was run for this closeout. Only isolated Python test children already present in the suite are authorized by the existing planning gate.
- PR #92 proposal exact-head Governance run 36213241691 / job 108323991494 passed on 7bd29099adfe3c4b2035e3da1ab9c09349e95001 with 3940/3940 tests. Its protected squash merge is f779cec13d0877cf9c5ac6797a49c5ef85389d0b; exact-main Governance run 36235782621 / job 108387156827 passed on that SHA with 3940/3940 tests in 16.550 seconds.
- The proposal review record was an APPROVED chat review with 0 HIGH/CRITICAL findings and 74/74 source fingerprints; it is not a formal GitHub review.
- The S04 closeout Context Lock bound base f779cec13d0877cf9c5ac6797a49c5ef85389d0b / tree 222627601b9a72fe17ae8253184f88d4620b5f7f and matched 77/77 exact-base Git blob fingerprints. PR #93 exact head 6e9e717ecacacfbef787a53ffbf0254f1188323c passed Governance #414 (36241125704 / 108401697787), received a separate read-only HEDS APPROVED review, was protected squash-merged as e0d8aeeea676d884e9c6a716df42a363f0765020, and passed exact-main Governance #415 (36244566768 / 108411232665). S05 planning begins as a separate proposal from that exact main; the session remains incomplete pending its own gates.
- At the S04 proposal base S05 was NOT_STARTED. On current main, PR #93 closeout and exact-main Governance #415 have passed; this S05 proposal is active but not complete. Keep M11 contract NOT_FROZEN, M10 frozen, M10/M11 implementation NOT_ADMITTED, WO-0014 BLOCKED and Issue #82 open.

## Primary sources

Checked 2026-09-26. These sources describe platform/library behavior; they do not decide IRIS ownership or policy.

- Python 3.12.14, `subprocess`: https://docs.python.org/3.12/library/subprocess.html
- Open Group POSIX.1-2024 `wait()` page (queried but unavailable through the research reader on this date): https://pubs.opengroup.org/onlinepubs/9799919799/functions/wait.html
- Linux man-pages 6.19, `wait(2)`: https://man7.org/linux/man-pages/man2/waitpid.2.html
- Linux man-pages 6.19, `pidfd_open(2)`: https://man7.org/linux/man-pages/man2/pidfd_open.2.html
- Linux man-pages, `kill(2)`: https://man7.org/linux/man-pages/man2/kill.2.html
- Linux man-pages 6.19, `setpgid(2)`: https://man7.org/linux/man-pages/man2/setpgid.2.html
- Linux man-pages 6.19, `setsid(2)`: https://man7.org/linux/man-pages/man2/setsid.2.html
- Microsoft Learn, Process Handles and Identifiers: https://learn.microsoft.com/en-us/windows/win32/procthread/process-handles-and-identifiers
- Microsoft Learn, `Win32_Process`: https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-process
- Microsoft Learn, `CreateProcessW`: https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw
- Microsoft Learn, Job Objects: https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
- Microsoft Learn, Nested Jobs: https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs

## Session result

S04 is COMPLETE_FOR_MODULE_PLANNING based on PR #92 exact-head Governance, protected squash merge and exact-main Governance. No architecture or process policy is selected, and S04-U01 through S04-U21 remain unresolved. PR #93 reconciled the checkpoint/evidence closeout, received HEDS APPROVED on its exact head, was protected squash-merged as e0d8aeeea676d884e9c6a716df42a363f0765020, and passed exact-main Governance #415 (36244566768 / 108411232665). S05 planning is now proposed from that exact main; S05 is not complete, and no M11 contract freeze or implementation admission is authorized.
