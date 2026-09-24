# M11 S02 — Headless/Background Worker Startup and IPC

Status: COMPLETE_FOR_MODULE_PLANNING  
Work Order: IRIS-WO-0015 / Issue #82  
Planning base: 5c9ac035e10e5485a0b8449e59622eaa1374cb6e  
Research checked: 2026-09-24  
M11 contract: NOT_FROZEN  
M11 implementation: NOT_ADMITTED  
M10 contract: m10-contract-v1.0 (FROZEN)  
M10 implementation: NOT_ADMITTED

## Purpose and scope

Explore how a future IRIS worker could be started in headless/background mode, become discoverable and ready to its supervisor, and exchange control and status messages. Compare supported platform technologies and candidate IPC families, review the available owner contracts, and record decisions that remain with M11, M12, M26, M54, M56 and M60.

This is planning documentation only. No worker, Blender process, service, socket, pipe or MCP endpoint was started, inspected or contacted. No runtime code was changed; no resource was reserved; no provider or DCC operation or hardware measurement was performed. Every benchmark and protocol test below is a future proof plan.

## Planning result

S02 records candidate startup and IPC models without selecting one. Blender background startup, process creation, worker readiness, the message transport, worker cancellation and production acceptance are separate concerns. A successful process launch, a ready response, an MCP response or a zero exit code cannot independently accept an M02 production or materialization.

The available technologies suggest three families for later review:

1. A supervisor launches a child worker and owns stdin/stdout/stderr pipes. MCP stdio is one standardized binding for a client-launched tool server; it has stricter framing and output rules than a general task worker.
2. A separately started local worker exposes a local IPC endpoint, such as a Unix domain socket on Linux or a Windows named pipe. The parent/worker lifetime, endpoint discovery and access policy must be designed together.
3. An independent process exposes an HTTP endpoint. MCP Streamable HTTP defines one possible structured control surface. Local endpoint security is explicit in the MCP specification; remote placement and trust domains remain M12 questions.

These are comparison categories, not an event sequence or state machine. No transport, startup authority, readiness handshake, protocol version, authentication policy, permission model or process lifetime has been accepted.

## Canonical IRIS source findings

| Owner/source | Canonical fact at this base | S02 consequence |
| --- | --- | --- |
| M02, m02-contract-v1.0 | M02 owns semantic project/production identity, Production Graph causality, the canonical ExecutionPlan and production lifecycle. Attempt identity is distinct from semantic identity and content/revision identity. | A worker registration cannot become a second production or attempt authority. The M02 plan-acceptance and M11 startup handshake remain unresolved. |
| M06, m06-contract-v1.0 | M06 owns operational revision/materialization, reproducibility and the future M11/M12 ExecutionAttemptPort evidence boundary. | The attempt mapping, payload, cardinality, durability and success evidence remain unspecified. Process exit and transport status do not replace M06 evidence. |
| M09, m09-contract-v1.0 | M09 owns resource truth, claims, leases, reservations, residency and resource-control outcomes. | Startup and IPC cannot reserve resources or manufacture lease evidence. A later handoff must consume owner-issued M09 evidence. |
| M10, m10-contract-v1.0 | M10 returns advisory plan alternatives and risk evidence; it does not dispatch, place, reserve resources or control workers/processes. | A plan proposal or recommendation cannot launch or command a worker. |
| ADR-0010 | Blender is headless-first for normal automation; MCP is a structured control/inspection surface and optional live-session path, not the only execution mechanism. | Keep the product MCP/tool surface distinct from the M11 worker fabric. MCP may be evaluated as a binding, but ADR-0010 does not select worker IPC. |
| M11 S01 | Supervisor placement and work/attempt/process association remain candidate topics. Platform process handles are not semantic identities. | Preserve S01 questions; S02 does not define M11 identity or supervisor placement. |
| M12–M60 | The repository master index has candidate module descriptions, but no individual M12–M60 owner contract is present at this base. | Any later-owner detail below is pending until its canonical contract exists. |

## Startup and IPC boundary map

This list separates research concerns. It does not prescribe an interface or normative order.

- **Startup authority:** Who may request process creation, under which owner-issued plan/evidence, and how that request is authorized remain open. M10 is never the dispatcher.
- **Headless configuration:** Blender documents background command-line execution and Python scripting controls. Exact Blender release support, executable discovery, scene/script trust and result interpretation must be coordinated with M26 and M54.
- **Readiness and registration:** A process can exist without being ready to accept work. The worker identity, readiness proof, supported protocol/schema versions, capabilities, duplicate-registration handling and restart behavior have no M11 contract yet.
- **IPC framing:** Standard input/output pipes, local sockets, named pipes and HTTP have different framing, endpoint lifetime and reconnect behavior. MCP framing applies only when the MCP protocol is selected.
- **Identity and evidence:** M02 identities, M06 operational attempt evidence and OS process handles stay distinct. Their cardinality and reference handoff are unresolved.
- **Access control:** Same-user versus multi-user isolation, local endpoint ownership, process privilege, inherited environment/handles, credential scope and sandboxing are security-owner decisions. M54's individual contract is absent.
- **Observation:** Logs, progress, correlation IDs, retention, secret redaction and telemetry ownership await M56 and M54 contracts.
- **Failure states:** Spawn failure, early exit, failed readiness, malformed or oversized messages, EOF, lost connection, duplicate registration and stale endpoint outcomes need a typed M11 contract. Retry, cancellation, timeout and recovery semantics remain for later sessions and owner reviews.

## Candidate topology comparison

| Candidate family | Useful property | Principal boundary or risk | Status |
| --- | --- | --- | --- |
| Supervisor-spawned child with standard streams | Direct parent/child association; no listening endpoint to discover; Python supports asynchronous direct-executable spawning. | Pipe backpressure and unbounded output; the process and connection lifetimes are coupled. MCP stdio requires stdout to contain protocol messages only. | PROPOSED |
| Local IPC endpoint | A worker can outlive a caller connection and accept reconnection; local peer identity may be available from OS facilities. | Endpoint ownership, stale names, user/session isolation and message framing vary by OS. Reconnect does not solve duplicate work or identity. | PROPOSED |
| Independent HTTP endpoint | Familiar request/response deployment and multi-client access; Streamable HTTP is an official MCP binding. | Larger network/security surface; Origin validation, authentication and local bind policy are required by MCP. Remote placement is not M11's to infer from the M12 index row. | PROPOSED |

No family is ranked or selected. A future comparison must state supported operating systems and whether the same logical worker may be reconnected to by another supervisor.

## Technology capture

Every item follows the Slow Planning Protocol. PROPOSED records a candidate for the later Final Technology Review; it does not mean accepted or selected.

### TECH-M11-005 — Blender 5.1 command-line background mode

- Classification: Existing technology.
- Purpose: Run Blender without its interactive UI and execute a declared command-line task or Python script.
- Operating model: Blender 5.1 documents the --background option, Python script/expression options, command-line argument ordering, and --python-exit-code for exceptions in command-line scripts. The manual also documents controls for whether automatic script execution is enabled.
- Expected benefit: A documented batch path for the Blender-first product requirement that can be supervised as a separate OS process.
- Dependencies: A qualified Blender release and executable path; M26 DCC and file semantics; M54 trust/sandbox policy; M02 plan authority; M11 process lifecycle.
- Risks/failure modes: Startup success is not task readiness or production acceptance; version and add-on drift; untrusted blend files or scripts; environment and path injection; output streams may contain diagnostics; Python exception exit handling does not define a complete result contract. The repository index labels M26 as Blender 5.2 LTS, but that is index-level candidate context and no M26 owner contract is available here. S02 uses the official 5.1 manual only and makes no 5.2 compatibility claim.
- Benchmark/proof plan: Under a later implementation Work Order, compare cold and warm startup on each supported OS/version; test missing/corrupt files, script exceptions, unavailable add-ons, disabled/enabled automatic execution policy, stdout/stderr volume, graceful exit, and result/evidence correlation. Use synthetic files and isolated workers; measure only against declared targets. No Blender process or benchmark was run in S02.
- Status: PROPOSED.
- Destination: M11 S02 / Final Technology Review; M26 and M54 handoff when those contracts exist.

### TECH-M11-006 — Python 3.12 asyncio subprocess APIs

- Classification: Existing technology.
- Purpose: Create and asynchronously observe a direct executable process while managing standard streams.
- Operating model: Python 3.12 documents asyncio.create_subprocess_exec, Process.wait and Process.communicate. The exec form accepts an executable plus argument vector rather than a shell command string. communicate drains stdin/stdout/stderr and waits, but buffers captured output in memory. Python documents ProactorEventLoop subprocess support on Windows and child watchers on Unix.
- Expected benefit: A standard-library option aligned with IRIS Governance's Python 3.12 environment for future supervisor integration and concurrent I/O.
- Dependencies: Event-loop choice; OS-specific process APIs; executable/environment/path policy; an M11 lifetime/attempt boundary.
- Risks/failure modes: communicate is unsuitable for unbounded output; waits on undrained pipes can deadlock; process behavior differs by OS and event-loop implementation; a direct child API alone does not define descendant containment, durable registration, security or restart recovery. It is a candidate implementation family, not a decision to use asyncio.
- Benchmark/proof plan: If admitted later, use disposable synthetic executables to test argv preservation, no-shell invocation, noisy dual streams, stream limits, early exit, connection closure, event-loop shutdown and platform parity. Test bounded streaming separately from whole-output capture. No subprocess was created in S02.
- Status: PROPOSED.
- Destination: M11 S02/S04/S05 and Final Technology Review.

### TECH-M11-007 — MCP 2026-07-28 stdio transport

- Classification: Existing protocol technology.
- Purpose: Carry MCP JSON-RPC between a client and a server launched as a child process.
- Operating model: The client launches the server subprocess. The server reads newline-delimited JSON-RPC from stdin, writes only valid protocol messages to stdout, and may use stderr for logs. Closing stdin is the portable graceful-shutdown signal. The 2026-07-28 transport specification is stateless; unexpected process loss loses in-flight requests, which a client may retry against a fresh process.
- Expected benefit: Reuse of an established structured control protocol when a tool server is intentionally coupled to its client-launched process.
- Dependencies: MCP revision/version negotiation; client/server implementation; clean stdout framing; an explicit distinction between tool requests and worker-job identity.
- Risks/failure modes: Blender or child-task logs on stdout corrupt framing; a retry after process loss can duplicate side effects unless owner-defined idempotency/reconciliation exists; MCP request cancellation does not define OS process termination; the client-launched lifetime may not fit a persistent supervisor or detachable worker. This binding does not itself provide M02/M06 semantics.
- Benchmark/proof plan: On a future synthetic protocol fixture, verify framing and malformed-line rejection, stderr isolation, EOF shutdown, cancellation during an in-flight request, worker loss/restart, duplicate request handling and protocol-era compatibility. No MCP server was launched or connected in S02.
- Status: PROPOSED.
- Destination: M11 S02; M26 control-surface handoff and Final Technology Review.

### TECH-M11-008 — MCP 2026-07-28 Streamable HTTP

- Classification: Existing protocol technology.
- Purpose: Expose an MCP server as an independent HTTP process with request-scoped JSON or SSE responses.
- Operating model: The 2026-07-28 binding uses a single endpoint with POST requests; it removes the GET stream endpoint and protocol-level sessions. For local deployments, the specification requires Origin validation and recommends binding to localhost and implementing authentication. Closing an SSE response stream signals cancellation of that request.
- Expected benefit: A structured control surface that is independent of a caller's subprocess stream and can serve multiple connections.
- Dependencies: HTTP server lifecycle; authentication and Origin policy; endpoint ownership; M12's local/remote placement contract; M54 authorization.
- Risks/failure modes: Network reachability and DNS rebinding; local authentication mistakes; transport cancellation may not terminate a separately managed worker; persistent notification streams have independent lifetimes; no M12 contract currently defines remote trust or placement.
- Benchmark/proof plan: In a future isolated test, validate Origin rejection, loopback-only configuration for local mode, unauthenticated access rejection, concurrent clients, request-stream disconnect, server restart and correlation to the worker. No endpoint was started in S02.
- Status: PROPOSED.
- Destination: M11 S02, M12/M54 handoff and Final Technology Review.

### TECH-M11-009 — Unix domain sockets

- Classification: Existing platform technology.
- Purpose: Provide local bidirectional IPC on Unix-like systems, including Linux.
- Operating model: Linux AF_UNIX supports pathname, unnamed and abstract addresses and can expose peer credentials through SO_PEERCRED. Linux pathname sockets use directory and socket permissions, while POSIX does not require socket-file permissions to provide that security behavior. Linux abstract sockets have no filesystem permissions and are a Linux-specific extension.
- Expected benefit: A local endpoint for long-lived workers where the caller needs to reconnect without using a network listener.
- Dependencies: OS support and path/namespace policy; framing; lifecycle cleanup; peer-credential API and M54 authorization.
- Risks/failure modes: Permissions and address semantics vary across operating systems; abstract namespace is not portable and has no file permissions; stale filesystem socket paths and process restart can confuse discovery; a peer credential identifies an OS principal, not an IRIS production attempt.
- Benchmark/proof plan: In a future Linux/macOS support matrix, test same-user and different-user access, peer credentials, stale-path recovery, disconnect/reconnect, partial frames, concurrent clients and bounded payloads. Use synthetic peers; do not infer portable guarantees from Linux man pages. No socket was created in S02.
- Status: PROPOSED.
- Destination: M11 S02, M54 handoff and Final Technology Review.

### TECH-M11-010 — Windows named pipes

- Classification: Existing platform technology.
- Purpose: Provide local interprocess communication using Windows pipe objects.
- Operating model: Windows lets the creator provide a security descriptor for both pipe ends. Microsoft documents that the default ACL grants full control to LocalSystem, administrators and creator-owner, and read access to Everyone and anonymous accounts. A logon SID can restrict access to a logon session.
- Expected benefit: A native Windows IPC option with access checks tied to Windows security principals.
- Dependencies: Windows-specific implementation/binding; explicit DACL and session policy; endpoint naming; M54 authorization and M60 support baseline.
- Risks/failure modes: Relying on the default ACL exposes a broader read surface; generic write rights have documented permission implications; one user's other logon sessions and remote clients require explicit policy; the available source does not establish a Python binding or cross-platform abstraction.
- Benchmark/proof plan: Under a later implementation Work Order, test allow/deny cases for intended and unintended principals, cross-session access, endpoint squatting, reconnect, process restart, framing and permission errors on each supported Windows baseline. No named pipe was created in S02.
- Status: PROPOSED.
- Destination: M11 S02, M54/M60 handoff and Final Technology Review.

### CAND-M11-002 — Reference-preserving startup and registration envelope

- Classification: Proprietary candidate. This is an IRIS-owned design candidate, not a novelty or patentability claim.
- Purpose: Explore a future boundary that binds a supervisor's authorized startup request to a worker's readiness/registration response without replacing owner-issued identities or security decisions.
- Operating model: A future envelope could carry versioned protocol/capability claims and opaque references issued by M02/M06/M09/M12/M26/M54. This is a design space only: there is no proposed field set, identifier, signature, state vocabulary, storage rule, event order or cardinality.
- Expected benefit: Make incompatible workers, untrusted registrations and missing owner evidence visible while keeping semantic production, operational attempt, resource lease and OS process identities separate.
- Dependencies: M02 plan/identity handoff; M06 ExecutionAttemptPort; M09 resource evidence; M12 placement; M26 worker/DCC integration; M54 identity/security; M56 observation. Individual owner contracts for M12–M60 are not available at this base.
- Risks/failure modes: A duplicate attempt authority; spoofed, replayed or stale registrations; incompatible version downgrade; ambiguous worker-to-process cardinality; accidentally treating readiness as successful production; assuming M54 authorization from transport identity.
- Benchmark/proof plan: After owner review, use synthetic protocol fixtures for forged identity, replay, stale endpoint, duplicate registration, version mismatch, out-of-order messages, supervisor restart and unknown owner references. Prove M02/M06/M09 authority is preserved. No protocol fixture or live peer was executed.
- Status: PROPOSED.
- Destination: M11 owner-contract candidate only after S03–S05, Final Technology Review, compatibility scan and independent audit.

## Internal reuse review

The exact-base repository contains limited one-shot subprocess use in scripts/hive_mcp.py and scripts/gef_preflight.py. The HIVE bridge resolves a checkout through HIVE_REPO_PATH or an adjacent directory, then runs a Docker Compose command through subprocess.run; GEF preflight uses subprocess.check_output for a Git query. These utilities do not prove a long-lived supervisor, worker registration, IPC framing, process-tree containment, restart recovery, process ownership, or an M02/M06 attempt handoff. They are evidence of narrow command invocation only.

No UGAS or CORE supervisor source was available in this repository/connection. HIVE MCP tools were not exposed in the active Work Mode connection. Therefore no HIVE-derived claim or UGAS/HIVE/CORE supervisor reuse is marked PROVEN or ACCEPTED. This is an evidence limit, not evidence that no such implementation exists elsewhere. No HIVE command or process was launched for this session.

## Pending M12–M60 owner-contract details

No individual owner contract from M12 through M60 exists in the exact-base repository tree. The rows below identify planning dependencies from the module index; they do not confer contract authority.

| Owner | Index-level candidate dependency | Detail pending its contract |
| --- | --- | --- |
| M12 — Compute Orchestration | Local, multi-GPU, LAN, remote and cloud placement | Placement authority, endpoint trust domain, host discovery, remote execution and supervisor handoff. |
| M16/M17 — Workflow/ComfyUI | Workflow compilation and runtime integration | Provider-specific launch/request semantics, queue/job state and provider capabilities. |
| M26 — Blender headless automation and MCP | Blender 5.2 LTS label and DCC integration | Supported release, file/script trust, addon environment, task/result contract and MCP-to-worker boundary. |
| M54 — Security, Identity & Restricted Content | Security and identity authority | Principal model, authentication/authorization, sandbox, credential/environment handling, redaction and restricted content. |
| M56 — Observability and telemetry | Event/log aggregation | Event schema, correlation, redaction, retention and health/telemetry authority. |
| M60 — Deployment, Recovery and Final Acceptance | Whole-system lifecycle | Supported host services, installation, upgrades, durable restart/recovery and final acceptance evidence. |
| M12–M60 other owners | Individual owner contracts absent | Any owner-specific worker input/output, capability, policy, evidence, lifecycle and error semantics remain PENDING until that owner contract exists. |

The M10 forward-compatibility scan is available only as a candidate map because it explicitly reviewed these modules at index level. It does not settle any of the details above.

## Questions carried forward

- S02-U01: Which owner-issued request, if any, can cause an M11 supervisor to create a process? Preserve M10's prohibition and M02/M12 authority.
- S02-U02: Is a worker tied to the launching supervisor's lifetime, or can it detach and be rediscovered? Coordinate with S01 and M12/M60.
- S02-U03: What evidence constitutes readiness and registration, and who owns the protocol/version negotiation?
- S02-U04: How are M02 identity and plan references bound to M06 ExecutionAttemptPort evidence without choosing mapping/cardinality?
- S02-U05: Which principals may launch, connect, inspect or send control messages; how are multiple users and logon sessions isolated under M54?
- S02-U06: What executable, Blender version, scene/script trust, environment variables and inherited handles are permitted under M26/M54?
- S02-U07: Which framing, size limits, backpressure, stdout/stderr and log redaction rules are needed for each transport?
- S02-U08: How are duplicate, replayed, stale, out-of-order or post-restart registrations handled? Carry into S04/S05 without inventing semantics.
- S02-U09: How does protocol-request cancellation relate to M11 process/job cancellation? The transport specification does not decide process lifecycle; carry into S05.
- S02-U10: Which local/remote endpoint and placement responsibilities belong to M12?
- S02-U11: Which health, progress, event and retention fields belong to M56?
- S02-U12: Which OS and Blender release matrix is supported, and what setup/recovery is owned by M60?

## S02 governance closeout

PR #87 exact head 78893daec68aabe3bb23836a4429017f13e97f30 passed exact-head Governance run 36068426412, job 107863497210 (3940/3940 tests). The PR was protected squash-merged as b090ae68bac23be2261932e75549b3ea255990ec. Exact-main Governance run 36068660747, job 107864233622, passed on that merge SHA (3940/3940 tests; actor KayzenRoot). The post-authoring S02 documentation audit found 0 HIGH and 0 CRITICAL findings. S02 is COMPLETE_FOR_MODULE_PLANNING only; the final independent M11 planning audit remains pending until S01–S05 and the required planning reviews are complete.

## Validation and limits

- Source base and repository tree were pinned to exact main 5c9ac035e10e5485a0b8449e59622eaa1374cb6e; the Context Lock records Git blob SHA-1 fingerprints.
- Available M02, M06, M09 and frozen M10 source boundaries were read. M12–M60 owner-contract absence was checked in the repository tree.
- Official technology documentation was checked on 2026-09-24. Sources are listed below.
- HIVE MCP was unavailable; Git is the canonical record and no HIVE evidence was fabricated.
- No worker/process, Blender, IPC endpoint, provider, resource reservation or benchmark was operated.

## References

### Canonical repository sources at the planning base

- AGENTS.md and .engineering/SOURCE-HIERARCHY.md — startup source order and HIVE evidence rules.
- docs/project-brain/02-REQUIREMENTS.md — PR-005, PR-006, PR-008 and PR-009.
- docs/project-brain/07-RUNTIME-EXECUTION-PRINCIPLES.md — background-first and process-discipline objectives.
- docs/project-brain/10-SECURITY-GOVERNANCE.md — untrusted DCC inputs and future sandbox boundary.
- docs/project-brain/16-DECISIONS-LEDGER.md — ADR-0010.
- planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md — m02-contract-v1.0.
- planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md — m06-contract-v1.0.
- docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md — M09 resource/lease owner contract.
- planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md — m10-contract-v1.0.
- planning/compatibility/M10-FORWARD-COMPATIBILITY-SCAN.md — M12–M60 index-level candidates.
- planning/research/M11-S01-LONG-LIVED-SUPERVISOR-AND-JOB-PROCESS-MODEL.md — S01 boundaries and questions.

### Official technology sources

- [Blender 5.1 Manual — Command Line Arguments](https://docs.blender.org/manual/en/5.1/advanced/command_line/arguments.html)
- [Python 3.12 — asyncio subprocesses](https://docs.python.org/3.12/library/asyncio-subprocess.html)
- [MCP 2026-07-28 — Transports overview](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
- [MCP 2026-07-28 — stdio transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio)
- [MCP 2026-07-28 — Streamable HTTP transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
- [MCP 2026-07-28 — Security best practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices)
- [Linux man-pages — unix(7)](https://man7.org/linux/man-pages/man7/unix.7.html)
- [Microsoft Learn — Named Pipe Security and Access Rights](https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights)
