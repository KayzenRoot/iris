# M11 S01 — Long-lived Supervisor and Job Process Model

Status: RESEARCH_COMPLETE_PENDING_GOVERNANCE
Work Order: IRIS-WO-0015 / Issue #82
Planning base: 889b29b773676649a15bd497cbe22f6fe4d8a9a5
Research checked: 2026-09-24
M11 contract: NOT_FROZEN
M11 implementation: NOT_ADMITTED
M10 contract: m10-contract-v1.0 (FROZEN)
M10 implementation: NOT_ADMITTED

## Purpose and scope

Explore candidate boundaries for the lifetime of an IRIS supervisor, a logical production job, an execution attempt, and the operating-system process or process group that performs work. The intended outcome is an evidence-backed planning map for later M11 sessions. It is not a process-state machine, identity schema, public API, technology selection, or implementation specification.

This session changes planning documents only. No process or worker was launched, inspected, signalled, connected to, reaped, or measured. No resource was reserved, and no provider, Blender, or ComfyUI work was executed.

## Planning result

S01 is complete as a planning exploration, subject to the exact-head and exact-main Governance gates. It establishes the following guardrails for the remaining M11 planning:

1. Keep four concepts distinct while planning: M02 semantic production/work identity and accepted ExecutionPlan; M06 operational attempt evidence; a possible M11 logical job/supervisor association; and the platform-specific process or containment handle.
2. Treat any mapping, cardinality, ownership, durability, and recovery relationship between those concepts as unresolved until the responsible owner contracts define it.
3. Compare an embedded supervisor, a separate long-lived per-user service, and optional operating-system service-manager integration. Select none in S01.
4. Keep operating-system process handles and IDs scoped as temporary platform references in the candidate model. This is an inference from the M02/M06 identity boundaries and the platform references below, not a frozen rule.
5. Carry platform differences and failure handling into S02–S05. No candidate in this document is accepted for production use.

## Canonical IRIS source findings

| Owner/source | Canonical fact at the planning base | S01 consequence |
| --- | --- | --- |
| M02, m02-contract-v1.0 | M02 defines semantic project/production identity, Production Graph causality, canonical ExecutionPlan and production lifecycle. Its public concepts include AttemptIdentity, but M02 is not a workflow runner and real worker/process scheduling is explicitly outside its scope. Attempt success cannot directly make a production ACCEPTED. | M11 cannot replace the M02 work identity, causality, plan, or production acceptance authority. The M02 AttemptIdentity fields and its mapping to M06/M11 are not specified by this session. |
| M06, m06-contract-v1.0 | M06 materializes M02 semantics into operational revisions, manifests, reconstruction and execution evidence. Its identity firewall distinguishes semantic identity, revision/snapshot, operational revision, content digest, materialization and attempt. The future ExecutionAttemptPort is assigned to M11/M12. M06 excludes worker scheduling and placement. | The intended M11-to-M06 evidence handoff is real, but the port payload, attempt ownership, event cardinality, persistence, and recovery semantics remain unresolved. S01 assigns none of them. |
| M09, m09-contract-v1.0 | M09 owns resource truth, claims, leases, reservations, residency and resource-control outcomes. Resource state is evidence-bearing; a successful M09 result does not execute a provider or reclaim capacity. | A process/job scope is not a resource lease. M11 must consume owner-issued references and leave lease mutation and resource truth to M09. PR-009 workstation headroom remains an owner-controlled constraint; S03/S05 must plan its handoff. |
| M10, m10-contract-v1.0 | M10 returns advisory, bounded plan alternatives. A proposal is not an accepted M02 plan, placement, reservation, dispatch, process action, or provider submission. | No M10 recommendation can be interpreted as a worker command. |
| M11 | No M11 owner contract exists yet. Issue #82 admits five planning sessions only. | All M11-owned identity, supervisor, job, attempt and process-lifecycle semantics remain candidates. |
| M12–M60 | Individual owner contracts are absent where recorded in the M11 planning admission and owner-dependency register. Index-level descriptions are candidate context only. | Placement/orchestration and all other owner-specific handoffs stay PENDING until their canonical contract exists. |

The cited M02 and M06 contracts establish the ownership boundary, not a complete M11 integration. In particular, M02's AttemptIdentity and M06's future ExecutionAttemptPort must not be assumed to be the same record or to share an identifier. Whether M11 reports an attempt, creates an operational process association, or participates in both remains for an owner-reviewed contract decision.

## Supervisor placement options

| Candidate | Potential benefit | Main cost or failure domain | S01 status |
| --- | --- | --- | --- |
| Supervisor embedded in the interactive IRIS process | Fewer components and no separate service-control or IPC boundary for an initial single-user process. | UI shutdown/crash and supervisor/job lifetime become coupled; long waits and child output may affect the interactive application; restart recovery is not inherent. | Considered; not selected. |
| Separate long-lived per-user supervisor | Can isolate job tracking from an individual UI window and may outlive that window within the user session. | Needs a separately authenticated control/inspection channel, single-instance ownership, permissions, upgrade/shutdown behavior, and durable or reconcilable job state. | Considered; not selected. |
| Host service-manager integration | Can delegate service lifetime and process grouping to an operating-system manager where supported. | Host-specific APIs, installation and permissions, manager availability, account boundaries and non-managed-host fallback. It may not be suitable for ordinary desktop/user-session installation. | Optional integration candidate only; not selected. |

These are architecture alternatives, not a recommendation that IRIS must run as a background service. Whether a supervisor survives a GUI close, logout, reboot, or user-session change is unresolved.

## Technology capture

Each entry follows the Slow Planning Protocol. PROPOSED records a candidate for the later Final Technology Review; it does not mean accepted or selected.

### TECH-M11-001 — Python 3.12 subprocess.Popen

- Classification: Existing technology.
- Purpose: Spawn and observe a direct child process, manage its standard streams, and obtain a return code.
- Operating model: The application owns a Popen object for the child. Python 3.12 documents shell=False and close_fds=True defaults. On POSIX, start_new_session and process_group expose setsid/setpgid creation behavior; they do not define a cross-platform supervisor or durable job registry.
- Expected benefit: Standard-library process creation and direct-child observation that fit the repository's Python 3.12 Governance environment.
- Dependencies: Python runtime; executable/path/environment policy; OS-specific lifecycle behavior; an owner-defined job/attempt boundary.
- Risks and failure modes: Platform differences; direct-child state is not process-tree containment; descendants can outlive the direct child; waiting on pipes can deadlock if output is not drained; a long-lived service, restart recovery, permissions, and process ownership must be built elsewhere.
- Benchmark/proof plan: If later admitted, test direct exit/error handling, noisy stdout/stderr, child-spawn and descendant behavior, repeated wait/reconnect behavior, and supported-OS parity using isolated synthetic executables. Measure supervisor idle overhead and per-job launch/observation cost against declared targets. No such process test or benchmark was run in this planning session.
- Status: PROPOSED.
- Destination: M11 S02/S04/S05 and Final Technology Review.

### TECH-M11-002 — Windows Job Objects

- Classification: Existing platform technology.
- Purpose: Associate and manage process groups as a unit; Windows documents accounting, limit, notification and termination operations.
- Operating model: Create a job object, associate processes, and govern inheritance/breakaway behavior. By default, CreateProcess children join the job; breakaway settings alter that behavior. Nested jobs are supported beginning with Windows 8 / Windows Server 2012.
- Expected benefit: A native containment and accounting primitive that can cover more than one direct child.
- Dependencies: Windows-specific adapter; job-object access/security descriptors; supported OS version; process creation/assignment order; caller's existing job membership.
- Risks and failure modes: Assignment can fail or descendants can break away depending on configuration. Closing the final handle with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE terminates associated processes, so handle lifetime can become destructive lifecycle coupling. Older Windows versions differ on nesting.
- Benchmark/proof plan: If later admitted, verify child and grandchild membership, breakaway and assignment failures, nested-job constraints, accounting completeness, permission denial, supervisor crash and final-handle behavior on every supported Windows baseline. Use a disposable test process tree only under a future implementation Work Order.
- Status: PROPOSED.
- Destination: M11 S04/S05 and Final Technology Review.

### TECH-M11-003 — Linux pidfds

- Classification: Existing platform technology.
- Purpose: Hold a stable reference to one Linux task and observe or signal that task without relying only on a recyclable numeric PID.
- Operating model: pidfd_open is available from Linux 5.3; pidfd_send_signal is documented from Linux 5.1. A pidfd can be monitored for exit, and signalling by pidfd avoids the PID-reuse race documented for numeric-PID signalling.
- Expected benefit: More reliable correlation to a specific process on Linux and a pollable exit reference.
- Dependencies: Linux kernel/API availability; PID namespace relationship; permission to signal; Python/native bindings and fallback policy.
- Risks and failure modes: A pidfd identifies a task, not a process tree, worker job, or durable IRIS attempt. Availability and flags vary by kernel. pidfd_open's already-exited-child guarantee depends on SIGCHLD disposition and that the child was not reaped elsewhere. It does not supply restart recovery or cross-platform parity.
- Benchmark/proof plan: If later admitted, test pidfd acquisition races, exit notification, already-reaped and permission-denied outcomes, namespace boundaries, kernel feature fallback, and distinction between direct process and descendant containment. No kernel capability was probed here.
- Status: PROPOSED.
- Destination: M11 S04/S05 and Final Technology Review.

### TECH-M11-004 — systemd transient service/scope units

- Classification: Existing optional host-manager technology.
- Purpose: Register process work in the systemd unit/cgroup tree and delegate supported lifecycle or resource-control operations to the system service manager.
- Operating model: systemd documents StartTransientUnit for transient services/scopes/slices; a runtime unit name is unique during the unit's lifetime. RemainAfterExit can retain an exited unit state. The API is explicitly systemd-specific; non-systemd systems use another userspace cgroup manager/API.
- Expected benefit: Host-managed grouping and state observation on systems where systemd is the selected manager and the caller has the necessary bus access.
- Dependencies: systemd presence/version; D-Bus availability; user-versus-system manager choice; unit-name lifecycle; host permissions and resource policy.
- Risks and failure modes: Not portable to non-systemd hosts; daemon/API availability and authorization; host policy may conflict with IRIS assumptions; transient runtime handles do not by themselves define durable M02/M06 identity; shutdown behavior needs explicit review.
- Benchmark/proof plan: If later admitted, test service versus scope behavior, permission and bus failures, child membership, restart/shutdown behavior, exited-state retention, and fallback on non-systemd Linux. Resource-control verification must use M09's contract and remain separate from process grouping.
- Status: PROPOSED.
- Destination: M11 S02/S04/S05 and Final Technology Review.

### CAND-M11-001 — Reference-only work/attempt/process association

- Classification: Proprietary candidate. This names an IRIS-owned design candidate, not a novelty or patentability claim.
- Purpose: Explore an auditable relationship among M02's semantic work and plan references, M06's ExecutionAttemptPort evidence, an M11 logical job/supervisor association, and one or more platform process references without collapsing their identities.
- Operating model: A future M11-owned envelope could carry owner-issued references and scoped process observations while each owning module retains its identity and state authority. No field set, identifier, cardinality, state vocabulary, storage model, or event order is proposed as normative here.
- Expected benefit: Traceability across logical production work and OS execution while preserving M02/M06/M09 authority and making missing or stale mappings visible.
- Dependencies: M02 AttemptIdentity and ExecutionPlan semantics; M06 ExecutionAttemptPort; M12 placement/orchestration contract; S02 IPC/permission planning; S03 lease/resource handoff; S04 containment/reaping; S05 cancellation/recovery; any relevant M56 observation contract when available.
- Risks and failure modes: Duplicate attempt authority; ambiguous one-to-many job/process relationships; stale process references after restart; PID reuse; untrusted event attribution; missing owner contracts; accidental promotion of an OS return code into production acceptance.
- Benchmark/proof plan: After contract review, use property/table-driven tests for identity non-equivalence, immutable reference binding, duplicate/out-of-order event handling, unknown/stale mappings, supervisor restart, process-tree mismatch, and M02/M06 authority preservation. A future full implementation gate must separately test OS-specific containment and evidence persistence.
- Status: PROPOSED.
- Destination: M11 contract candidate only after S02–S05, Final Technology Review, compatibility review and independent audit.

## Internal reuse review

The IRIS default-branch search found narrow standard-library subprocess invocations in scripts/hive_mcp.py and scripts/gef_preflight.py. They run a helper command or Git query; the available sources do not establish a long-lived worker supervisor, job registry, process-tree containment policy, restart recovery, or M02/M06 execution-attempt handoff. Treat them as evidence that one-shot subprocess invocation exists in repository tooling only, not as proven supervisor reuse.

No UGAS or CORE supervisor source was available in this repository/connection. HIVE MCP was not exposed in the active Work Mode connection. Therefore no UGAS/HIVE/CORE supervisor reuse is marked PROVEN or ACCEPTED. This is an evidence limitation, not evidence that no such implementation exists elsewhere. Revisit only when authoritative source material is accessible.

## Session questions carried forward

| ID | Unresolved question | Planned owner/session |
| --- | --- | --- |
| S01-U01 | Is the supervisor embedded, a separate per-user service, or optionally hosted by an OS service manager? What should happen on UI exit, user logout, reboot, upgrade, and shutdown? | M11 S02/S05; product deployment sources |
| S01-U02 | How does M11's logical job refer to M02 work/plan identity and M06's ExecutionAttemptPort without creating or duplicating attempt authority? What are the cardinality and restart rules? | M02/M06/M11 contract handoff; M12 where placement applies |
| S01-U03 | Which operating systems and minimum versions are supported, and what containment/reference primitive is required on each? | M11 S02/S04 and compatibility review |
| S01-U04 | Does one job own one worker, a tree of child processes, or a sequence of worker invocations? Can descendants detach or escape the chosen scope? | M11 S04 |
| S01-U05 | What durable registry or evidence allows a restarted supervisor to distinguish live, exited, reaped, unknown, or foreign processes? | M11 S05, M06 handoff and security review |
| S01-U06 | Which authentication, permission and trust rules apply to control and inspection of the supervisor? | M11 S02 and M54 contract when available |
| S01-U07 | How do M09 leases/headroom and M12 placement relate to job admission and lifetime without M11 asserting resource truth? | M11 S03; M09 frozen contract; M12 contract pending |
| S01-U08 | What is M11's process observation/evidence handoff to M06's ExecutionAttemptPort, including unknown/incomplete result behavior? | M06/M11 contract handoff |
| S01-U09 | Which M11 concerns rely on unavailable UGAS/HIVE/CORE materials, and what authoritative evidence would prove reuse? | M11 technology discovery |
| S01-U10 | Which M56 observation/audit details are owner-defined and which remain pending? | Revisit against M56 contract when available |

Cancellation, timeout and escalation policy remain for S05; reaper/zombie semantics and shell-free command rules remain for S04; IPC and authentication remain for S02; concurrency, fairness, leases and headroom remain for S03. No session question authorizes a runtime action.

## Validation and limits

- Repository base: exact main 889b29b773676649a15bd497cbe22f6fe4d8a9a5; account KayzenRoot; repository KayzenRoot/iris.
- Context Lock: 53 critical source paths re-pinned against the base tree; exact-match count is recorded in the S01 Evidence package.
- Owner sources checked: frozen M02, M06, M09 and M10 contracts; M11 admission scaffold; M11–M60 owner-dependency register and M10 compatibility scan.
- Technology evidence: official Python 3.12 documentation, Microsoft Learn, Linux man-pages, and systemd's control-group interface documentation, accessed 2026-09-24.
- Governance validation and repository tests are performed on the exact PR head by the repository workflow. This planning session itself did not run runtime tests or any process operation.
- HIVE MCP unavailable; no HIVE-derived evidence is asserted.

## References

### Canonical repository sources at the planning base

- [M02 frozen contract](https://github.com/KayzenRoot/iris/blob/889b29b773676649a15bd497cbe22f6fe4d8a9a5/planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md)
- [M06 frozen contract](https://github.com/KayzenRoot/iris/blob/889b29b773676649a15bd497cbe22f6fe4d8a9a5/planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md)
- [M09 frozen owner contract](https://github.com/KayzenRoot/iris/blob/889b29b773676649a15bd497cbe22f6fe4d8a9a5/docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md)
- [M10 frozen contract](https://github.com/KayzenRoot/iris/blob/889b29b773676649a15bd497cbe22f6fe4d8a9a5/planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md)
- [M11 planning scaffold](https://github.com/KayzenRoot/iris/blob/889b29b773676649a15bd497cbe22f6fe4d8a9a5/planning/modules/M11-BACKGROUND-WORKER-FABRIC-PROCESS-LIFECYCLE.md)
- [M11–M60 owner dependency register](https://github.com/KayzenRoot/iris/blob/889b29b773676649a15bd497cbe22f6fe4d8a9a5/planning/reviews/IRIS-WO-0014-M11-M60-OWNER-DEPENDENCY-REGISTER.md)

### Official technology sources

- [Python 3.12 subprocess documentation](https://docs.python.org/3.12/library/subprocess.html)
- [Microsoft Learn — Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
- [Linux man-pages — pidfd_open(2)](https://man7.org/linux/man-pages/man2/pidfd_open.2.html)
- [Linux man-pages — pidfd_send_signal(2)](https://man7.org/linux/man-pages/man2/pidfd_send_signal.2.html)
- [systemd — New Control Group Interfaces](https://systemd.io/CONTROL_GROUP_INTERFACE/)
