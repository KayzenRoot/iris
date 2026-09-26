# M11 Final Technology Review

**Status:** PROPOSED — submitted for PR-head Governance; no independent-review verdict or merge is implied.
**Review decision:** 28 existing-technology records and two IRIS-owned candidates are individually dispositioned below. ACCEPT means reference/boundary evidence only. No runtime, product dependency, default, API, process policy, IPC protocol, identity schema, contract freeze, or implementation is selected.
**Work Order:** IRIS-WO-0015-M11-FINAL-TECHNOLOGY-REVIEW-C01-PREFLIGHT-RECOVERY
**Issue:** #82 (open)
**Exact base:** 6ccb65f25c3bae2ad10d511473d2944f980478fa
**Base tree:** 71ea766d7511cc745855faa662783f023755ac5c
**Proposal branch:** iris-wo-0015-m11-final-technology-review-20260926
**Review date:** 2026-09-26
**Planning boundary:** Documentation only. S04-U01..U21 and S05-U01..U23 remain OPEN. M12–M60 owner-specific contracts remain PENDING. M11 remains NOT_FROZEN; M11 and M10 implementation remain NOT_ADMITTED.

## 1. Authority, scope, and verdict meanings

This review follows the repository source hierarchy and C01 Work Order. The exact base is the protected merge commit from PR #96. The earlier S05 context lock supplied 83 critical source paths; all 83 Git blob fingerprints were recomputed at this base and matched the working tree with zero missing paths and zero mismatches before edits. Issue #82 was verified open. The active branch was clean and the proposed remote branch and PR did not exist.

The attached C01 PDF is task input, not an authority override. Canonical Git/project-brain sources govern. HIVE's registered IRIS snapshot was stale and was not used as canonical evidence. No HIVE result is claimed.

- **ACCEPT** — sufficient evidence to retain the item in the M11 contract-candidate evidence set as a reference, limitation, architecture comparator, or owner-boundary question. It does not select or mandate use.
- **SUPERSEDE** — remove an existing candidate from its current role and name the narrower, better-supported replacement boundary. This does not design that boundary's schema.
- **REJECT** — the item is not suitable to guide the current M11 candidate in the described role. The topic and owner question can remain open.

Every item below has exactly one verdict. For grouped repeated implementations, the IDs, session provenance, and distinct study scopes are retained once in one row. A source fact, IRIS inference, verdict rationale, contract boundary, risk/dependency, open question, destination, and revisit condition are identified separately.

## 2. Owner boundaries preserved

| Owner | Canonical boundary used in this review | Review limit |
| --- | --- | --- |
| M02 | m02-contract-v1.0: production causality, semantic identity, canonical ExecutionPlan, and production lifecycle | No M11-owned production identity or lifecycle is introduced. |
| M06 | m06-contract-v1.0: operational state/revision, materialization lineage, reproducibility, and attempt evidence | No attempt schema, cardinality, lifecycle, or materialization acceptance rule is selected. |
| M09 | Canonical resource governor: resource truth, claims, leases, reservations, residency, and control outcomes | No process count or sampled metric becomes a grant; no lease mutation or handshake is defined. |
| M10 | m10-contract-v1.0 is FROZEN and advisory | M10 cannot dispatch, place, reserve, or control workers/processes. |
| M12 | Individual owner contract unavailable | Placement/orchestration remains PENDING; no aggregate queue or remote-host authority is inferred. |
| M26 | Individual owner contract unavailable | Blender/DCC product behavior remains PENDING beyond the cited Blender 5.1 command-line facts. |
| M54 | Individual owner contract unavailable | Trust, executable authorization, endpoint security, permissions, and secrets remain PENDING. |
| M56 | Individual owner contract unavailable | Telemetry, provenance, correlation, redaction, and retention remain PENDING. |
| M60 | Individual owner contract unavailable | Supported platform baselines, deployment, recovery, and final acceptance remain PENDING. |
| M11 | No frozen owner contract | This review records evidence and open boundaries only. |

## 3. Primary-source review and comparison with 2026-09-24

Only official primary sources were used for technology behavior. Versioned documents and upstream commit history were rechecked on 2026-09-26. For rolling or versionless vendor documentation, the reviewed page and its exposed revision information are stated; lack of a visible revision date is not treated as proof that the text never changed.

| Source family | Current primary evidence, version/revision, and 2026-09-26 access | Comparison with 2026-09-24 |
| --- | --- | --- |
| Python | Python 3.12.14 documentation: [subprocess](https://docs.python.org/3.12/library/subprocess.html), [asyncio subprocesses](https://docs.python.org/3.12/library/asyncio-subprocess.html), [asyncio tasks](https://docs.python.org/3.12/library/asyncio-task.html), [asyncio queues](https://docs.python.org/3.12/library/asyncio-queue.html), and [queue](https://docs.python.org/3.12/library/queue.html). Upstream source histories include subprocess documentation commit 7c653e2540cbe4180efb3bd83b63865a1f675650 (2026-08-07) and asyncio task documentation commit 539e85abc4931d2173e1311b6cf2c52ca94b0c45 (2026-09-20). | The checked source revisions predate 2026-09-24. No post-baseline source commit was found for the reviewed documentation; no behavior change is claimed. |
| Microsoft Windows | Microsoft Learn: [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [Creating Processes](https://learn.microsoft.com/en-us/windows/win32/procthread/creating-processes), [GenerateConsoleCtrlEvent](https://learn.microsoft.com/en-us/windows/console/generateconsolectrlevent), [Named Pipe Security and Access Rights](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights), and [Named Pipes](https://learn.microsoft.com/windows/win32/ipc/named-pipes). Exposed update dates for Creating Processes, GenerateConsoleCtrlEvent, and Named Pipe Security are 2026-07-17, 2021-08-26, and 2021-01-07. Job Objects has no visible revision date on the reviewed page. | The dated pages predate 2026-09-24. Re-read the current Job Objects page; because it exposes no revision date, this review records its current behavior and does not claim a page-history guarantee. No new platform behavior or supported IRIS baseline is inferred. |
| Linux | Linux man-pages 6.19: [waitpid(2)](https://man7.org/linux/man-pages/man2/waitpid.2.html), [pidfd_open(2)](https://man7.org/linux/man-pages/man2/pidfd_open.2.html), [pidfd_send_signal(2)](https://man7.org/linux/man-pages/man2/pidfd_send_signal.2.html), [setpgid(2)](https://man7.org/linux/man-pages/man2/setpgid.2.html), [setsid(3p)](https://man7.org/linux/man-pages/man3/setsid.3p.html); current Linux kernel documentation: [Control Group v2](https://docs.kernel.org/admin-guide/cgroup-v2.html). The man-pages page reports 6.19 and a 2026-09-09 source snapshot. Upstream Linux documentation history for cgroup-v2.rst showed no commit since 2026-09-24. | Man-pages snapshot and checked kernel documentation history predate or show no post-baseline delta. Current facts were re-read. Kernel support level remains an M60 decision. |
| systemd | Upstream systemd v262 release (2026-09-22); tagged [systemd-run](https://github.com/systemd/systemd/blob/v262/man/systemd-run.xml), [systemd.service](https://github.com/systemd/systemd/blob/v262/man/systemd.service.xml), and [Control Group Interface](https://systemd.io/CONTROL_GROUP_INTERFACE/). Checked histories for systemd-run.xml, systemd.service.xml, and CGROUP_DELEGATION.md show no commits since 2026-09-24. | v262 predates the baseline by two days; no post-baseline change was found in the checked source histories. Optional manager integration remains only an alternative. |
| Blender | Blender 5.1 Manual: [Command Line Arguments](https://docs.blender.org/manual/en/5.1/advanced/command_line/arguments.html), [Rendering From the Command Line](https://docs.blender.org/manual/en/5.1/advanced/command_line/render.html); official [Blender 5.1 release page](https://www.blender.org/releases/5-1/) identifies 5.1.2, released 2026-05-19, as the latest 5.1 update. The 5.1 German manual page was also read where the English command-line page could not be opened by the source browser; it is the same official 5.1 manual release. | No later Blender 5.1 release is listed as of 2026-09-26. The manual page does not expose a comparable source revision date in the reviewed rendering, so no claim about an unchanged documentation file history is made. M26's index mention of Blender 5.2 LTS does not prove M26 support. |
| MCP | Official 2026-07-28 specification at immutable upstream revisions: [stdio](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/b488c16623e5202a3961e551886044577ae0f096/docs/specification/2026-07-28/basic/transports/stdio.mdx) and [Streamable HTTP](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/0cb6c6a31768cbb16129b35e6b569a31fecfe1b6/docs/specification/2026-07-28/basic/transports/streamable-http.mdx); [specification version index](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/db4bfcff3d60f5df01a21bdf6b78f7012cac4634/docs/specification/2026-07-28/basic/index.mdx). | The versioned documents and listed commits predate 2026-09-24; checked file histories showed no post-baseline commits. No process lifecycle semantics are added to MCP transport behavior. |
| RabbitMQ | Official [Priority Support in Queues](https://www.rabbitmq.com/docs/priority), [Quorum Queues](https://www.rabbitmq.com/docs/quorum-queues), and [Consumer Prefetch](https://www.rabbitmq.com/docs/consumer-prefetch); RabbitMQ 4.3 release notes and [4.3.6 release](https://github.com/rabbitmq/rabbitmq-server/releases/tag/v4.3.6) dated 2026-09-14. The priority documentation source history showed no commit since 2026-09-24. | Current 4.3 strict-priority behavior was reconfirmed; the 4.3.6 release predates the baseline and no post-baseline priority-document change was found. This remains a broker comparison, not IRIS infrastructure. |

### Source interpretation

- Python argument sequences and direct-child APIs constrain what a Python launch call does; they do not settle target authorization, child trees, trust, or IRIS policy.
- Windows Job Objects, Linux pidfds/cgroups, POSIX process groups, and systemd units have different ownership and failure semantics. Similar words such as “group,” “handle,” “kill,” “service,” or “wait” do not make them interchangeable.
- The MCP specification describes transport framing, session/HTTP behavior, and request cancellation. It does not authorize or terminate an external process.
- Blender's background command line is product behavior at the cited version, not an M11 worker contract or M26 acceptance guarantee.
- RabbitMQ's queue ordering is not an IRIS fairness, scheduler, resource-lease, or cancellation policy.

## 4. Technology and IRIS-candidate decision matrix

### Existing technologies

#### TECH-M11-001 — Python 3.12 subprocess.Popen

- **Class / provenance / authority:** Existing technology; S01 supervisor/job process model. M11 owns only future process-adapter boundaries; M54 owns trust; M60 owns support and deployment.
- **Primary source:** SRC-PY1, Python 3.12 subprocess documentation.
- **Sourced fact:** A sequence of arguments avoids shell parsing by default; shell behavior has platform caveats including batch files. Popen controls a direct child. Pipe handling can deadlock if output is not drained; process launch, handles, environment and working-directory resolution have platform behavior.
- **IRIS inference and verdict rationale — ACCEPT:** This is sufficient evidence to preserve argument-vector launch and direct-child ownership as comparison boundaries, not to choose a launch policy or containment implementation.
- **Contract boundary:** No executable allowlist, shell prohibition, path-resolution rule, environment policy, child-tree guarantee, reaper, state machine, or supported OS is selected.
- **Risks / dependencies:** Batch-file behavior, inherited environment/handles, pipe backpressure, direct-child-only scope, and platform differences depend on M54/M60 decisions.
- **Open question:** S04-U03, S04-U13..U15: who owns launch, argument acceptance, executable authorization, environment, and secret handling?
- **Destination / revisit trigger:** Reference-only in the M11 candidate. Revisit when M54 security requirements and M60 platform baseline are available.

#### TECH-M11-002, TECH-M11-013, TECH-M11-021, TECH-M11-027 — Windows Job Objects

- **Class / provenance / authority:** Existing technology; S01, S03, S04, and S05 re-evaluate the same Windows mechanism for lifetime association, concurrency/resource limits, process grouping/reaping, and interruption. M11/M60 own any future adapter boundary; M54 owns permissions.
- **Primary source:** SRC-WIN1, Microsoft Learn Job Objects.
- **Sourced fact:** A Job Object can group processes and apply limits or termination. Descendants can escape through breakaway behavior; nesting and pre-existing job membership affect compatibility. Closing a handle terminates the job only when the corresponding kill-on-close limit is configured.
- **IRIS inference and verdict rationale — ACCEPT:** The documented grouping and failure caveats are useful platform reference evidence; they are not a cross-platform process-tree guarantee or selected cleanup policy.
- **Contract boundary:** No nesting policy, job assignment sequence, limit values, breakaway policy, kill-on-close behavior, owner, or Windows minimum version is chosen.
- **Risks / dependencies:** Host jobs, permissions, breakaway, inherited handles, assignment failures, process creation races, and account/session behavior require M54/M60 validation.
- **Open question:** S04-U08..U10 and S05-U19: which containment capability is supported and what happens when assignment or cleanup fails?
- **Destination / revisit trigger:** Reference-only platform row in the M11 candidate. Revisit after M60 names Windows baselines and M54 specifies trust/permissions; do not repeat the same implementation as four separate selections.

#### TECH-M11-003, TECH-M11-018 — Linux pidfds

- **Class / provenance / authority:** Existing technology; S01 evaluates process reference identity; S04 re-evaluates reference safety and waiting. M11/M60 own any future adapter boundary.
- **Primary source:** SRC-LNX2 and SRC-LNX3, Linux man-pages 6.19.
- **Sourced fact:** A pidfd refers to a particular process, can be polled, and can be used for signal delivery; waitid support via P_PIDFD is kernel-version dependent. It is not a general process-tree owner.
- **IRIS inference and verdict rationale — ACCEPT:** This is useful evidence for avoiding a bare numeric-PID reference in a Linux-specific design comparison; it does not define an IRIS semantic identity or tree-lifecycle contract.
- **Contract boundary:** No kernel floor, handle lifecycle, permission rule, or mapping to M02/M06 identity is selected.
- **Risks / dependencies:** Kernel availability, permissions, parent/child wait rights, and loss of the supervisor's reference remain relevant.
- **Open question:** S04-U01..U11 and S05-U22: what exact owner-issued reference and wait right apply after restart or parent exit?
- **Destination / revisit trigger:** Reference-only Linux capability. Revisit when M60 declares a Linux baseline and M02/M06/M54 handoffs are available.

#### TECH-M11-004 — systemd transient service or scope units

- **Class / provenance / authority:** Existing technology; S01 supervisor-placement and host-manager alternative. M60 owns deployment; M11 owns only the future relationship to an optional manager.
- **Primary source:** SRC-SYS1 through SRC-SYS3, systemd v262.
- **Sourced fact:** A transient service is manager-controlled and supervised; a scope groups processes whose caller remains the parent. User/system manager availability and permissions vary with host setup.
- **IRIS inference and verdict rationale — ACCEPT:** Keep manager integration as an optional host capability comparator; systemd is not universally installed or suitable as the required desktop supervisor.
- **Contract boundary:** No service installation, user manager requirement, restart behavior, unit properties, or coupling to worker success is selected.
- **Risks / dependencies:** Service/scope parentage differs, manager access may be unavailable, and installation/privilege behavior is platform and account dependent.
- **Open question:** S01-U01/U03/U04: what lifetime should outlive the UI, on which hosts, and with which parent/reaper?
- **Destination / revisit trigger:** Optional integration reference. Revisit after M60 deployment targets and M54 privilege boundaries are defined.

#### TECH-M11-005 — Blender 5.1 command-line background mode

- **Class / provenance / authority:** Existing technology; S02 startup and DCC behavior. M26 owns Blender/DCC integration; M60 owns supported product acceptance.
- **Primary source:** SRC-BL1 through SRC-BL3, Blender 5.1 Manual and official 5.1 release record.
- **Sourced fact:** Blender 5.1 supports background command-line rendering; command-line arguments are order-sensitive. The cited 5.1 release page lists 5.1.2 as the latest 5.1 update at review date.
- **IRIS inference and verdict rationale — ACCEPT:** This establishes a version-bounded startup comparator, not a promise that any command, startup sequence, add-on, file, or render is safe or accepted by IRIS.
- **Contract boundary:** No Blender version support matrix, command template, exit-code contract, startup readiness protocol, DCC plugin policy, or product default is selected.
- **Risks / dependencies:** User configuration/add-ons, command ordering, executable selection, resource pressure, and later-version differences depend on M26/M54/M60.
- **Open question:** S02 and S04-U19: which Blender versions, startup behavior, and acceptance evidence does M26/M60 require?
- **Destination / revisit trigger:** Version-limited product reference. Revisit when M26's canonical contract and supported Blender release matrix exist; do not infer Blender 5.2 support from an index entry.

#### TECH-M11-006 — Python 3.12 asyncio subprocess APIs

- **Class / provenance / authority:** Existing technology; S02 child-worker and asynchronous process-start comparator. M11 owns any future adapter; M54/M60 own security and support.
- **Primary source:** SRC-PY2, Python 3.12 asyncio subprocess documentation.
- **Sourced fact:** Async subprocess APIs operate on a direct child process; communicate-style collection avoids common pipe-buffer deadlocks. The APIs expose terminate/kill operations whose platform behavior differs.
- **IRIS inference and verdict rationale — ACCEPT:** The API is a relevant implementation reference, but asynchronous API shape does not settle worker topology or cancellation/reaping policy.
- **Contract boundary:** No event-loop architecture, output limit, async lifecycle, process tree, or cancellation guarantee is selected.
- **Risks / dependencies:** Unread pipes, platform-specific terminate semantics, event-loop shutdown, and direct-child limitations.
- **Open question:** S02-U01..U10 and S05-U02/U06: what relationship exists between API interruption, transport cancellation, and process interruption?
- **Destination / revisit trigger:** Reference-only. Revisit after M11 API boundaries and M60 platforms are separately admitted.

#### TECH-M11-007 — MCP 2026-07-28 stdio transport

- **Class / provenance / authority:** Existing protocol technology; S02 evaluates it as one structured transport. M54 owns trust; M11/M12 own any future integration boundary.
- **Primary source:** SRC-MCP1 and SRC-MCP3, immutable 2026-07-28 specification revisions.
- **Sourced fact:** stdio transport uses a launched subprocess with protocol messages on standard input/output; server logs use standard error and must not corrupt protocol output. Request cancellation is a protocol notification requesting work to stop.
- **IRIS inference and verdict rationale — ACCEPT:** Retain as a possible protocol-binding comparison with strict output rules; a protocol cancellation request is not an OS process-kill guarantee.
- **Contract boundary:** No MCP adoption, readiness handshake, worker identity, authentication model, cancellation propagation, or process ownership is selected.
- **Risks / dependencies:** Output contamination, framing errors, unauthorized request sources, and a mismatch between request and process lifetimes.
- **Open question:** S02-U04..U09 and S05-U01..U07: who authenticates the caller and connects request cancellation to any separately owned process policy?
- **Destination / revisit trigger:** Transport reference only. Revisit when M54 and M11 define any structured control surface and M26 confirms product needs.

#### TECH-M11-008 — MCP 2026-07-28 Streamable HTTP

- **Class / provenance / authority:** Existing protocol technology; S02 independent endpoint comparator. M54 owns security; M12 owns placement and remote trust boundaries.
- **Primary source:** SRC-MCP2 and SRC-MCP3, immutable 2026-07-28 specification revisions.
- **Sourced fact:** Streamable HTTP defines JSON-RPC over HTTP with optional streaming/session behavior. The specification calls for Origin validation, localhost-only binding for local servers, and authentication; transport-level cancellation closes/cancels a request stream and does not terminate an external process.
- **IRIS inference and verdict rationale — ACCEPT:** Retain only as a possible structured endpoint reference and a concrete security-boundary example.
- **Contract boundary:** No HTTP server, local or remote bind, authentication scheme, endpoint lifetime, session model, process mapping, or M12 placement behavior is chosen.
- **Risks / dependencies:** DNS rebinding, remote exposure, caller authorization, endpoint discovery, disconnect/reconnect, and duplicated requests.
- **Open question:** S02-U06..U10 and S05-U01/U20: which owner defines endpoint trust, placement, request cancellation, and process interruption?
- **Destination / revisit trigger:** Reference-only. Revisit only if M54 and M12 contracts provide local/remote endpoint authority.

#### TECH-M11-009 — Unix domain sockets

- **Class / provenance / authority:** Existing IPC technology; S02 local IPC comparator. M54/M60 own access and platform support.
- **Primary source:** SRC-LNX4, Linux man-pages unix(7), plus the S02 primary-source review.
- **Sourced fact:** Unix-domain sockets provide local IPC facilities with platform-specific addressing and permission behavior.
- **IRIS inference and verdict rationale — ACCEPT:** The mechanism belongs in a local IPC comparison; its existence does not prove a portable IRIS transport or authorization contract.
- **Contract boundary:** No socket path, framing, peer-credential use, discovery, reconnect, or cleanup semantics are chosen.
- **Risks / dependencies:** Path squatting, stale endpoints, permissions, namespace behavior, message limits, and Linux-only assumptions require M54/M60.
- **Open question:** S02-U03..U08: what endpoint lifecycle, same-user isolation, and reconnect behavior would be required?
- **Destination / revisit trigger:** Local IPC comparator. Revisit after M54 security and M60 OS support requirements.

#### TECH-M11-010 — Windows named pipes

- **Class / provenance / authority:** Existing IPC technology; S02 local IPC comparator. M54 owns access control; M60 owns Windows support.
- **Primary source:** SRC-WIN4 and SRC-WIN5, Microsoft Learn named-pipe and security documentation.
- **Sourced fact:** Named-pipe security depends on the pipe DACL; documented defaults can grant broad access, and remote accessibility depends on host/service configuration. Explicit security descriptors are needed for a restricted design.
- **IRIS inference and verdict rationale — ACCEPT:** This is useful as a local IPC alternative and threat-boundary reference; it is not inherently private or safe by name alone.
- **Contract boundary:** No DACL, logon SID, remote-pipe policy, framing, peer authentication, or reconnect behavior is selected.
- **Risks / dependencies:** Overbroad access, cross-session clients, remote clients, endpoint squatting, inherited rights, and Windows-version differences.
- **Open question:** S02-U05..U08 and M54/M60: which principals may connect and how is remote access ruled in or out?
- **Destination / revisit trigger:** Platform comparator. Revisit after M54 access-control contract and M60 baseline.

#### TECH-M11-011 — Python 3.12 asyncio bounded queues and semaphores

- **Class / provenance / authority:** Existing technology; S03 concurrency/backpressure mechanisms. M11 may later expose a local boundary; M12/M09 own aggregate placement/resources.
- **Primary source:** SRC-PY4, Python 3.12 asyncio queues.
- **Sourced fact:** asyncio queues are not thread-safe; maxsize greater than zero bounds queue occupancy and blocks producers when full, while zero means unbounded. Queue/semaphore mechanics do not assign resource truth.
- **IRIS inference and verdict rationale — ACCEPT:** Keep local capacity and backpressure as a comparator only. A bounded in-process structure cannot stand in for workstation, host-pool, or resource-owner admission.
- **Contract boundary:** No capacity, queue-full response, timeout, queue ownership, admission unit, or aggregation scope is selected.
- **Risks / dependencies:** Indefinite producer wait, event-loop scope, single-process limits, and stale/unavailable M09 evidence.
- **Open question:** S03-U01..U09/U16/U19: what is counted, who aggregates it, and who defines queue-full and unknown outcomes?
- **Destination / revisit trigger:** Reference-only. Revisit when M11, M09, and M12 define their owner interfaces and M56 evidence needs.

#### TECH-M11-012 — Python 3.12 queue.PriorityQueue comparison

- **Class / provenance / authority:** Existing technology; S03 ordering comparator. M11/M12 own any future product policy; M54 constrains who may assert priority.
- **Primary source:** SRC-PY5, Python 3.12 queue documentation.
- **Sourced fact:** PriorityQueue returns the lowest-valued queued item first; the standard queue is synchronized for threads. This ordering primitive does not itself supply IRIS fairness, starvation, trust, or resource semantics.
- **IRIS inference and verdict rationale — ACCEPT:** Retain as evidence that a mechanism can order items, not as a recommendation for strict priority or numeric priority semantics.
- **Contract boundary:** No priority source, comparator, tie rule, fairness, aging, preemption, tenant class, or public field is chosen.
- **Risks / dependencies:** Incorrect ordering conventions, starvation, untrusted priority inputs, and confusing queue order with OS CPU or M10 ranking.
- **Open question:** S03-U10..U14/U20: who owns priority provenance, fairness guarantees, and any handling of inversion?
- **Destination / revisit trigger:** Comparator only. Revisit when M11/M12 and M54 set authority and a proof plan for fairness.

#### TECH-M11-014 — Linux cgroup v2 CPU and memory controllers

- **Class / provenance / authority:** Existing OS facility; S03 process/resource-limiting comparator. M60 owns platform baseline; M09 owns resource truth and control outcomes.
- **Primary source:** SRC-LNX6, current Linux kernel Control Group v2 documentation.
- **Sourced fact:** cgroup v2 organizes processes hierarchically and provides CPU/memory controls. CPU quota behavior is scheduler/controller-specific; memory limits can trigger cgroup OOM and may transiently exceed a configured maximum. It is not a VRAM measurement, M09 lease, or child-reaping contract.
- **IRIS inference and verdict rationale — ACCEPT:** Preserve as an optional OS capability reference, with its limitations and failures explicit.
- **Contract boundary:** No controller enablement, subtree ownership, numeric limits, cgroup delegation, OOM policy, or support guarantee is selected.
- **Risks / dependencies:** Delegation/permissions, controller availability, hierarchy constraints, OOM side effects, and divergent kernels.
- **Open question:** S03-U07/U16/U17 and S05-U15/U19/U23: which resource evidence and capabilities does M60 support under M09 authority?
- **Destination / revisit trigger:** Platform reference only. Revisit after M60 deployment and M09 resource/control contracts.

#### TECH-M11-015 — RabbitMQ priority queues, comparison only

- **Class / provenance / authority:** Existing technology; S03 explicitly studies a broker queue for comparison. M12 would own any distributed queue/orchestration; M54 owns broker security.
- **Primary source:** SRC-RMQ1 through SRC-RMQ3, official RabbitMQ 4.3 documentation/release.
- **Sourced fact:** Quorum queues in 4.3 have 32 strict priority levels; a sustained stream of higher-priority work can indefinitely delay lower-priority work, and consumer prefetch affects dispatch.
- **IRIS inference and verdict rationale — ACCEPT:** Keep as a documented comparator demonstrating starvation and deployment costs; the verdict accepts the evidence reference only, not a broker dependency or selected IRIS queue policy.
- **Contract boundary:** No RabbitMQ deployment, message schema, queue topology, retry, persistence, authentication, or priority policy is selected.
- **Risks / dependencies:** Broker operations/security, deployment, durability semantics, prefetch, strict-priority starvation, and missing M12 contract.
- **Open question:** S03-U02/U12/U19/U20: is distributed coordination in scope, and who owns fairness and queue trust?
- **Destination / revisit trigger:** Comparison-only. Revisit only if M12's canonical contract and an explicit infrastructure decision bring a broker into scope.

#### TECH-M11-016 — Python 3.12 argument-vector invocation

- **Class / provenance / authority:** Existing technology; S04 re-evaluates shell-free launch as an execution boundary. M54/M60 own authorization and platform behavior.
- **Primary source:** SRC-PY1, Python 3.12 subprocess documentation.
- **Sourced fact:** Passing an argument sequence with shell disabled avoids Python constructing a shell command, but Windows batch-file processing can still involve shell behavior; target applications may parse arguments themselves. Python cautions against unsafe preexec_fn use in threaded programs and documents more specific session/process-group APIs.
- **IRIS inference and verdict rationale — ACCEPT:** The distinction is enough to retain argument-vector launch as a boundary under review, but not enough to declare an IRIS shell policy or executable trust model.
- **Contract boundary:** No blanket shell-free rule, batch-file prohibition, executable-path policy, target-specific escaping, working directory, or environment filtering is decided.
- **Risks / dependencies:** Batch wrappers, path replacement/search order, application argument interpretation, inherited secrets, and permission gaps.
- **Open question:** S04-U13..U15: what executable and argument sources are trusted, and who owns their validation?
- **Destination / revisit trigger:** Boundary reference. Revisit with M54 security and M60 support; preserve the batch-file caveat in any future contract.

#### TECH-M11-017 — POSIX/Linux wait, waitpid, and waitid

- **Class / provenance / authority:** Existing OS APIs; S04 process observation/reaping. M11/M60 own any future parent/wait adapter; M06 owns attempt outcome.
- **Primary source:** SRC-LNX1, Linux man-pages 6.19 waitpid(2).
- **Sourced fact:** wait-family calls report state for eligible child processes and reap terminated children; availability and status forms depend on relationship and API. Wait results describe OS child status, not production or materialization acceptance.
- **IRIS inference and verdict rationale — ACCEPT:** Preserve child ownership and reaping as separate evidence responsibilities; do not infer a universal reaper for orphaned/foreign processes.
- **Contract boundary:** No state machine, subreaper behavior, parent-exit handoff, polling strategy, or M06 mapping is selected.
- **Risks / dependencies:** ECHILD/permission/stale state, orphan reparenting, ownership loss, and platform differences.
- **Open question:** S04-U03..U07/U11/U12: who retains wait rights and what evidence is emitted when the relationship is lost?
- **Destination / revisit trigger:** OS evidence reference. Revisit when M11/M60 process ownership and M06 attempt evidence are defined.

#### TECH-M11-019 — POSIX process groups and sessions

- **Class / provenance / authority:** Existing OS mechanism; S04 grouping and signal comparator. M11/M60 own any future adapter; M54 owns permission/trust.
- **Primary source:** SRC-LNX4 and SRC-LNX5, Linux man-pages 6.19.
- **Sourced fact:** Process-group/session APIs establish groups and allow signal targeting by group; group/session membership can change and does not provide general descendant ownership or wait rights.
- **IRIS inference and verdict rationale — ACCEPT:** Retain for comparing signal scopes only; it cannot establish guaranteed process-tree containment, exit, or reaping.
- **Contract boundary:** No new-session launch policy, group ownership, signal escalation, or cleanup sequence is selected.
- **Risks / dependencies:** Descendant detachment, group reuse, session/terminal behavior, permissions, and separate child wait duties.
- **Open question:** S04-U05..U08 and S05-U06/U22: who can signal which group and how is exit independently confirmed?
- **Destination / revisit trigger:** Platform comparator. Revisit after M60 platform acceptance and M54 process-control authorization.

#### TECH-M11-020 — Windows CreateProcess and process handles

- **Class / provenance / authority:** Existing Windows API; S04 creation and reference comparator. M11/M60 own any future adapter; M54 owns access and handle security.
- **Primary source:** SRC-WIN2, Microsoft Learn Creating Processes.
- **Sourced fact:** CreateProcess returns process/thread handles and identifiers. Handle inheritance can unintentionally expose or prolong access to files, sockets, or other resources; inheritance must be constrained.
- **IRIS inference and verdict rationale — ACCEPT:** Preserve direct OS handles and inheritance risk as evidence, without equating a numeric process ID to an IRIS identity.
- **Contract boundary:** No handle transfer, inheritance list, parent model, termination policy, or process state machine is selected.
- **Risks / dependencies:** Leaked handles, PID reuse, access rights, process creation flags, inherited standard streams, and host baseline.
- **Open question:** S04-U03/U07/U09/U12/U14/U15: which owner creates, retains, inspects, and closes each handle?
- **Destination / revisit trigger:** Platform reference. Revisit after M54 and M60 define security and supported launch behavior.

#### TECH-M11-022 — Python 3.12 asyncio task cancellation and TaskGroup

- **Class / provenance / authority:** Existing runtime primitive; S05 coroutine cancellation comparator. M11 owns only a future mapping boundary; M06 owns attempt state.
- **Primary source:** SRC-PY3, Python 3.12 asyncio task documentation.
- **Sourced fact:** Task cancellation is cooperative through CancelledError; TaskGroup waits for child tasks when leaving its scope. It does not terminate an OS process merely because a coroutine is cancelled.
- **IRIS inference and verdict rationale — ACCEPT:** Keep as a distinct in-process cancellation layer; never treat it as process or production cancellation evidence.
- **Contract boundary:** No cancellation authority, propagation tree, shielding rule, public state, or partial-output disposition is selected.
- **Risks / dependencies:** Suppressed cancellation, cleanup during cancellation, child tasks that outlive a caller, and mismatch with OS child lifetime.
- **Open question:** S05-U01..U03/U06/U07: which owner request can cause coroutine cancellation and how is its outcome reported?
- **Destination / revisit trigger:** Evidence-layer reference. Revisit after M02/M06/M54 define operation and cancellation ownership.

#### TECH-M11-023 — Python 3.12 asyncio timeout scopes and wait_for

- **Class / provenance / authority:** Existing runtime primitive; S05 deadline/timeout comparator. M11/M12/M60 own any future deadline boundary.
- **Primary source:** SRC-PY3, Python 3.12 asyncio task documentation.
- **Sourced fact:** Timeout scopes and wait_for cancel coroutine/task work; wait_for can wait for cancellation cleanup and therefore exceed its nominal timeout. A coroutine timeout does not guarantee that a child process is gone.
- **IRIS inference and verdict rationale — ACCEPT:** Retain as timeout behavior evidence, not a hard process deadline or chosen cancellation sequence.
- **Contract boundary:** No timeout type, clock, deadline owner, grace period, termination escalation, or user-visible outcome is selected.
- **Risks / dependencies:** Cleanup delay, suspended host clocks, detached work, remote clocks, and ambiguity between request timeout and process exit.
- **Open question:** S05-U04..U07/U19: which deadline scope and clock belongs to which owner?
- **Destination / revisit trigger:** Reference-only. Revisit when M11/M12/M60 define deadline ownership and process termination is separately admitted.

#### TECH-M11-024 — Python 3.12 asyncio subprocess interruption

- **Class / provenance / authority:** Existing runtime API; S05 direct-child interruption comparator. M11/M60 own any future adapter; M54 owns authorization.
- **Primary source:** SRC-PY2, Python 3.12 asyncio subprocess documentation.
- **Sourced fact:** terminate/kill operate on the subprocess object; POSIX and Windows map these operations differently, and the API refers to the direct child. They do not independently prove descendant termination, output cleanup, or M06 result.
- **IRIS inference and verdict rationale — ACCEPT:** Keep the API's platform and scope limits as source facts only.
- **Contract boundary:** No TERM/KILL sequence, delay, retry, descendant policy, or final outcome is chosen.
- **Risks / dependencies:** Platform-specific behavior, permissions, descendants, and partial effects.
- **Open question:** S05-U02/U06/U07/U13/U22: who authorizes interruption and reconciles surviving descendants or leases?
- **Destination / revisit trigger:** Platform behavior reference. Revisit after M09/M54/M60 handoffs exist.

#### TECH-M11-025 — POSIX process-group signal delivery

- **Class / provenance / authority:** Existing OS mechanism; S05 multi-process signal-scope comparator. M11/M54/M60 own any future control boundary.
- **Primary source:** SRC-LNX4 and SRC-LNX5, Linux man-pages 6.19.
- **Sourced fact:** Signals can target process groups/sessions, but signal delivery does not prove every descendant exited or was reaped.
- **IRIS inference and verdict rationale — ACCEPT:** Keep as a distinct signal scope and failure case, not a cleanup guarantee.
- **Contract boundary:** No signal choice, group creation, escalation, grace period, or M06 mapping is selected.
- **Risks / dependencies:** Escaped members, permission errors, signal handling, partial output, and wait ownership.
- **Open question:** S05-U02/U06/U07/U22: what request authority and independent exit evidence would be required?
- **Destination / revisit trigger:** Comparison only. Revisit with M54/M60 process-control boundaries and M06 evidence.

#### TECH-M11-026 — Windows console process-group control event

- **Class / provenance / authority:** Existing Windows console API; S05 interruption comparator. M54/M60 own any future support/security boundary.
- **Primary source:** SRC-WIN3, Microsoft Learn GenerateConsoleCtrlEvent.
- **Sourced fact:** Console control events target eligible processes sharing a console and process group; services and processes without a shared console do not become universally interruptible through this mechanism.
- **IRIS inference and verdict rationale — ACCEPT:** Retain as a limited interactive-console capability, not as general worker termination.
- **Contract boundary:** No console creation/attachment, service support, signal mapping, fallback, or grace policy is selected.
- **Risks / dependencies:** No shared console, target ignores event, unrelated same-group processes, permissions, and deployment mode.
- **Open question:** S05-U06/U16/U19: what host modes and operator interaction are within supported platforms?
- **Destination / revisit trigger:** Windows comparator. Revisit after M60 names supported execution modes and M54 authorizes process control.

#### TECH-M11-028 — Linux cgroup v2 cgroup.kill

- **Class / provenance / authority:** Existing Linux facility; S05 descendant termination comparator. M60 owns support; M09 owns resource truth and M54/M11 own any future control boundary.
- **Primary source:** SRC-LNX6, current Linux kernel Control Group v2 documentation.
- **Sourced fact:** Writing 1 to cgroup.kill sends SIGKILL to processes in the cgroup and descendants. This is forceful termination behavior; it does not itself supply graceful cancellation, parent wait rights, per-process status, or M06 outcome.
- **IRIS inference and verdict rationale — ACCEPT:** Preserve the documented mechanism as a Linux-specific hard-termination reference with explicit limitations.
- **Contract boundary:** No cgroup ownership/delegation, authorization, escalation, timeout, cleanup, or recovery policy is selected.
- **Risks / dependencies:** Requires an appropriate writable cgroup and delegation; forceful partial effects and process/reaper evidence remain separate.
- **Open question:** S05-U06..U14/U19/U22: what owner can create or kill a cgroup, and how are resulting attempts, leases, and partial outputs reconciled?
- **Destination / revisit trigger:** Linux capability reference only. Revisit after M60 platform and M09/M54/M06 control/evidence contracts.

### Existing IRIS-owned candidates

#### CAND-M11-001 — Reference-only work/attempt/process association

- **Class / provenance / authority:** IRIS-owned candidate; S01 identity and process association. M02 owns semantic work/ExecutionPlan identity; M06 owns attempt evidence; M11 could only retain opaque references; OS APIs own process handles.
- **Primary source:** Canonical M02 and M06 owner contracts, plus SRC-PY1, SRC-WIN2, and SRC-LNX2/3 for OS reference limits.
- **Sourced fact:** OS process identifiers/references describe an operating-system process, not IRIS semantic work or an M06 attempt. M02/M06 authority cannot be inferred from a local process handle.
- **IRIS inference and verdict rationale — SUPERSEDE:** Supersede this as a standalone M11-owned association schema. The better-supported replacement boundary is a future composition of owner-issued opaque M02/M06 references with an OS process reference, with ownership, cardinality, and lifecycle still deferred to those canonical owners. No fields or schema are specified here.
- **Contract boundary:** No public identity, attempt identifier, payload, foreign-key/cardinality rule, restart policy, or correlation format is chosen.
- **Risks / dependencies:** Duplicate identity authority, ambiguous retries, cross-owner semantic drift, PID reuse, and stale references.
- **Open question:** S01-U02/U08 and S04-U01/U02: what references may be carried and which owners define their validity and relationship?
- **Destination / revisit trigger:** Record only the owner boundary in the M11 candidate. Revisit after M02/M06 issue a compatible, current handoff.

#### CAND-M11-002 — Reference-preserving startup and registration envelope

- **Class / provenance / authority:** IRIS-owned candidate; S02 startup/readiness/registration. M02/M06 own identity and outcomes; M26 startup; M54 security; M56 telemetry; M11 transport is undecided.
- **Primary source:** Canonical M02/M06 contracts; official Blender 5.1 manual; MCP 2026-07-28 transport specification.
- **Sourced fact:** Process existence, protocol readiness, request response, process exit, M06 attempt result, and materialization acceptance are separate events in their respective sources/owners.
- **IRIS inference and verdict rationale — REJECT:** The proposed envelope is not mature as one IRIS candidate because it combines readiness, registration, identity, protocol version, and authorization without owner contracts or defined evidence. The underlying questions remain open; this is not a rejection of future startup evidence.
- **Contract boundary:** No message envelope, handshake, auth, capability negotiation, duplicate-registration rule, version fallback, or readiness guarantee is chosen.
- **Risks / dependencies:** Spoof/replay, stale readiness, duplicate attempt authority, identity cardinality, downgrade, and treating startup as production success.
- **Open question:** S02 readiness/registration questions, S02-U04..U09, S04-U12/U19, and M54/M56/M26 handoffs.
- **Destination / revisit trigger:** Do not carry this envelope as a current M11 design candidate. Revisit separate owner questions after M26/M54/M56 contracts and M02/M06 references are available.

## 5. Architecture alternatives and lifecycle evidence distinctions

Each item below receives one ACCEPT verdict as a comparison reference only. None is ranked, selected, or adopted. For each, “fact” summarizes the study or official source; “inference/risk” and “revisit” state what remains unresolved. An ACCEPT here never authorizes runtime behavior.

| Alternative; class and provenance | Verdict; fact and inference/rationale | Boundary; risks/dependencies | Owner/open question; destination and revisit trigger |
| --- | --- | --- | --- |
| Supervisor embedded in interactive IRIS process; architecture alternative, S01 | **ACCEPT — comparator only.** S01 records fewer components as a possible benefit. Coupled UI/supervisor failures are an IRIS inference, not measured behavior. | UI exit/crash and job lifetime can couple; output and long waits may affect interaction; restart is not inherent. No default. | M11/M60; S01-U01/U04/U05. Keep for comparison; revisit on UI/lifetime and deployment requirements. |
| Separate per-user long-lived supervisor; architecture alternative, S01 | **ACCEPT — comparator only.** S01 records isolation from a single UI window as a possible benefit. | Requires separately secured endpoint, single-instance ownership, upgrade/shutdown, and durable or reconcilable state. | M11/M54/M60; S01-U01/U05/U06. Revisit after endpoint security and restart authority are available. |
| Optional host service-manager integration; architecture alternative, S01 | **ACCEPT — optional comparator.** systemd facts show one manager model, not universal host support. | Host-specific install, permission/account boundaries, unavailable manager, and non-managed-host fallback. | M60/M54; S01-U01/U03. Revisit with deployment targets; remains optional. |
| Supervisor-spawned child with standard streams; topology alternative, S02 | **ACCEPT — comparator only.** Direct parent-child association can avoid endpoint discovery; pipe and protocol rules add risk. | Pipe backpressure/output bounds and coupled process/connection lifetime; MCP stdio rules only if MCP is selected. | M11/M54/M60; S02-U01..U04. Revisit after worker lifetime and output boundaries are assigned. |
| Separately running worker with local IPC endpoint; topology alternative, S02 | **ACCEPT — comparator only.** Socket/named-pipe mechanisms may allow reconnect; this does not solve duplicate work or identity. | Endpoint discovery, stale names, local identity, permissions, OS differences, and message framing. | M54/M60/M11; S02-U03..U08. Revisit after supported OS and local trust model exist. |
| Independent HTTP endpoint; topology alternative, S02 | **ACCEPT — comparator only.** Familiar request/response and MCP Streamable HTTP exist; no placement conclusion follows. | Origin, authentication, bind address, remote exposure, disconnect/reconnect, and request duplication. | M54/M12; S02-U06..U10. Revisit only after local/remote trust and placement contracts exist. |
| In-process async task slots; concurrency alternative, S03 | **ACCEPT — comparator only.** A local loop can count local tasks; aggregate reach is absent. | Not a workstation or multi-supervisor cap; unit may not equal job/attempt/process. | M11/M12/M06; S03-U01..U04. Revisit when the counted unit and scope are owner-defined. |
| Bounded application queue; concurrency alternative, S03 | **ACCEPT — comparator only.** Bounded queues provide local producer backpressure. | A full queue can block indefinitely; ordering is not resource feasibility or M09 grant. | M11/M09/M12; S03-U05..U09. Revisit with queue-full, timeout, and grant outcomes defined. |
| Logical workload or attempt slots; concurrency alternative, S03 | **ACCEPT — comparator only.** M02/M06 references could describe product-level units. | Identity and cardinality are owner-controlled; retries may overlap. | M02/M06/M11; S03-U01/U03/U04. Revisit after canonical reference and retry boundaries. |
| OS process/job-tree limits; concurrency alternative, S03 | **ACCEPT — comparator only.** Windows and Linux offer different grouping/control primitives. | Permission, setup failure, breakaway, nesting, and platform baselines; limits are not app-queue semantics. | M60/M54/M11; S03-U02/U17. Revisit after M60 platform and M54 control requirements. |
| Resource-aware admission; concurrency alternative, S03 | **ACCEPT — comparator only.** Resource dimensions may be considered only through M09 authority. | Measurements are not grants; freshness, uncertainty, and M12 placement are pending. | M09/M12; S03-U05..U08/U16/U19. Revisit when owner contracts expose current reference semantics. |
| Multi-supervisor or remote aggregate; concurrency alternative, S03 | **ACCEPT — comparator only.** A process-local primitive cannot coordinate multiple supervisors or hosts. | Needs shared authority, conflict, placement, quotas, and trust contract. | M12/M54/M09; S03-U02/U19/U20. Revisit when the M12 contract exists. |
| Operator-configured static headroom; headroom alternative, S03/S05 | **ACCEPT — comparator only.** Stable explicit configuration may be explainable. | Values, units, scope, validation, stale configuration, and safe unknown behavior are undefined. | M09/M11/M12/M60; S03-U15/U16, S05-U15. Revisit after resource contract; no number/formula. |
| Evidence-driven headroom; headroom alternative, S03/S05 | **ACCEPT — comparator only.** Changing host evidence could inform a future owner decision. | Requires M09 authority, freshness/uncertainty, measurement coverage, M56 provenance; measurement is not a grant. | M09/M56/M60; S03-U15/U16, S05-U23. Revisit after telemetry/resource contracts; no estimator. |
| FIFO; queue-order alternative, S03 | **ACCEPT — comparator only.** Clear arrival-order baseline. | Long jobs may block later short work; no tenant share/responsiveness proof. | M11/M12; S03-U10..U13. Revisit with fairness requirements. |
| Strict priority; queue-order alternative, S03 | **ACCEPT — comparator only.** Python/RabbitMQ sources show ordering primitives; RabbitMQ confirms sustained high-priority work can starve low-priority work. | Priority authority, ties, starvation, and preemption are open. | M11/M12/M54; S03-U10..U14. Revisit after provenance and fairness criteria are defined. |
| Aging; queue-order alternative, S03 | **ACCEPT — comparator only.** Could alter ordering over waiting time; this is an unselected policy concept. | Clock, formula, bounds, authorization, and interaction with deadlines are absent. | M11/M56/M12; S03-U11..U13. Revisit only with measurable policy requirements. |
| Weighted service or per-class queues; fairness alternative, S03 | **ACCEPT — comparator only.** Could represent class-level share. | Class owner, weights, accounting, queue topology, and proof are open. | M12/M11/M54; S03-U12/U13/U20. Revisit after class authority is defined. |
| Deadline/urgency ordering; queue-order alternative, S03 | **ACCEPT — comparator only.** It is distinct from a priority label. | Deadline source, clock, freshness, authority, and timeout handling are unresolved. | M11/M12/M56; S03-U10/U11 and S05-U04/U05. Revisit after owner-declared deadlines. |
| Priority inversion scenario; risk comparator, S03 | **ACCEPT — scenario reference only.** S03 identifies the possibility that higher-ordered work waits on a resource held elsewhere; this is not a proven IRIS runtime state. | No inheritance, lease rule, lock, or preemption response is defined. | M09/M12/M11; S03-U14. Revisit when resource protocol is canonical. |
| OS scheduler priority; scheduling alternative, S03 | **ACCEPT — capability comparator only.** It affects CPU scheduling, not M09 VRAM grants or service fairness. | Platform-specific; may worsen interactive responsiveness; no priority mapping is chosen. | M60/M09/M12; S03-U10/U16/U17/U18. Revisit with platform and coexistence requirements. |
| Preemption; admission alternative, S03/S05 | **ACCEPT — comparator only; deferred.** It is recorded to expose cross-owner effects, not to authorize interruption. | Partial outputs, lease release, cancellation, cleanup, and recovery are unresolved; no action may be inferred. | M02/M06/M09/M12/M54/M60; S03-U14 and S05-U02/U06..U14/U21. Revisit only after those contracts and explicit authority exist. |
| Operator-configured headroom; workstation alternative, S05 | **ACCEPT — comparator only.** PR-009 asks for configurable headroom but specifies no value/policy. | No process inspection, values, notices, or enforcement is authorized. | M09/M26/M54/M60; S05-U15..U17/U23. Revisit with owner requirements. |
| OS-enforced process limits; workstation alternative, S05 | **ACCEPT — comparator only.** Job/cgroup facilities constrain processes in different ways. | A cap is not a grant, VRAM measurement, fairness promise, or responsiveness proof. | M09/M60; S05-U15/U19/U23. Revisit after OS capability evidence. |
| M09 evidence or lease reference; workstation alternative, S05 | **ACCEPT — boundary comparator only.** Only M09 can own resource truth and claims. | No process handshake, freshness, revocation, or consequence is defined; lease state does not prove a process stopped. | M09/M11/M60; S05-U13/U15/U23. Revisit when M09 provides a current owner interface. |
| Operator-session observation; workstation alternative, S05 | **ACCEPT — comparator only.** Host pressure or foreground use could be relevant evidence. | No telemetry or process inspection occurred; privacy, freshness, authorization, and provenance belong to owners. | M26/M54/M56/M60; S05-U16..U18/U23. Revisit after contracts and evidence rules exist. |
| No automation / explicit unknown; workstation alternative, S05 | **ACCEPT — comparator only.** Preserving an explicit unknown avoids equating missing evidence with capacity. | A future owner must define visible outcome and allowed response; this review does not create a default/fallback. | M09/M11/M12/M60; S05-U07/U15/U23. Revisit when outcome vocabulary and UI/operations owner exist. |

### Lifecycle evidence layers

The following are accepted as distinct terminology/evidence layers for future contract work; they are not an M11 state machine or cancellation policy:

| Layer | Source fact versus IRIS inference | Boundary and revisit |
| --- | --- | --- |
| Coroutine/task cancellation | Python cancellation is cooperative; a task request is not OS process termination. | Keep separate; revisit with M02/M06/M11 operation ownership. |
| Deadline or timeout | Python timeout APIs cancel coroutine work and can exceed nominal duration while cancellation settles. | No hard deadline guarantee; revisit with M11/M12/M56 clocks. |
| Process signal or interruption request | OS APIs deliver a signal/control operation with platform-specific scope. | Delivery is not exit proof; revisit with M54/M60 authority. |
| Process exit observation and reap | OS wait mechanisms report eligible child status and may reap that child. | Not attempt/materialization acceptance; revisit with M11/M06/M60. |
| M06 attempt result | M06 owns operational attempt evidence and outcome. | M11 cannot synthesize or close it; revisit with a canonical M06 handoff. |
| M06 materialization result | M06 owns revision/lineage/reproducibility evidence for accepted materialization. | Process zero-exit is insufficient; revisit with M06 owner contract. |
| Process-group/job/cgroup termination | Platform mechanism affects a group or hierarchy with OS-specific escape, force, and permission limits. | No uniform descendant guarantee; revisit per M60 platform and M54 control boundary. |

## 6. Internal reuse and candidate cross-check

The repository scan found no production process supervisor, reaper, worker IPC, cancellation/recovery engine, or M09 cross-process lease coordinator at the exact base. The available HIVE/GEF clients are narrow one-shot governance/MCP tooling and are not evidence of worker-lifecycle reuse. Test fixtures are not product behavior. **Verdict for reuse as process-lifecycle precedent: REJECT** — no candidate is sufficiently evidenced as a production lifecycle precedent. Revisit only if a current, canonical source proves such reuse and its authority/behavior.

Cross-check of the five study inventories and all headings found 28/28 distinct technology IDs and two IRIS-candidate records dispositioned exactly once, with repeated Windows/PID-reference technologies grouped without dropping a session or scope. All explicit architecture/topology/headroom/queue/fairness/workstation alternatives are included above. No S01–S05 question is closed by this review.

## 7. Unresolved decisions and excluded work

- S04-U01..U21 and S05-U01..U23 remain OPEN; no session question or owner handoff is closed.
- M12–M60 owner-contract details remain PENDING. The available M10 forward-compatibility scan is index-level evidence only.
- No journal, log, database, durable queue, distributed coordinator, or recovery algorithm was compared or selected. S05 explicitly deferred storage/recovery design because the relevant M06/M55/M60 authority is absent.
- No public API, semantic identity/attempt schema, IPC handshake/framing/authentication/permissions, process state machine, shell policy, start/stop/restart policy, reaper/reaper ownership, cancel/timeout/signal/retry/crash-recovery/journal/idempotency/cleanup guarantee, concurrency or priority number, fairness/quota, lease handshake, supported target OS, benchmark, compatibility scan, audit, freeze, implementation, or process/IPC/hardware operation is authorized or decided.
- M10 remains advisory, FROZEN at m10-contract-v1.0, and unable to dispatch/control workers. M11 remains NOT_FROZEN. M11/M10 implementation remains NOT_ADMITTED. Issue #82 remains OPEN.

## 8. Recommendation and handoff

**Review recommendation:** ACCEPT the listed technologies and architecture alternatives only as source-backed references, limits, and open comparators for a future M11 owner-contract candidate; SUPERSEDE the standalone identity-association candidate with the narrower owner-reference boundary described above; REJECT the combined startup/registration envelope and any claimed internal process-lifecycle precedent. These are executor planning recommendations, not an independent review or freeze verdict.

**Next planning gate after this proposal's required PR-head Governance:** Forward Compatibility Scan against available owner contracts and index-level M12–M60 entries, explicitly preserving missing contracts as PENDING. This increment stops after the exact PR-head Governance gate with its PR open and unmerged.
