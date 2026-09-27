# M11 Background Worker Fabric & Process Lifecycle: Versioned Owner-Contract Candidate

Status: PROPOSED_C01_NOT_FROZEN
Candidate ID: m11-contract-candidate-v0.1 (not a frozen module contract)
Module: M11 | Work Order: IRIS-WO-0015 | Issue: #82 OPEN
Planning base: 9acfe5400a490a996602d5b09f7adb3d92b3050b | base tree: 578a11b3a90f5087bc7fd66c8e72e28d0d04d4af

## 1. Evidence and scope

M11 S01-S05, Final Technology Review and corrected Forward Compatibility Scan C01 are complete for module planning, not implementation. FCS #99 corrected three source paths and an omitted S05 research fingerprint, achieving 89/89 scan sources, 30/30 owner/source rows and 49/49 M12-M60 index-level entries. Separate FCS closeout PR #100 passed exact-head Governance, protected-merged to 9acfe5400a490a996602d5b09f7adb3d92b3050b and passed exact-main Governance #435 (36285351940 / 108524953905; 3,940/3,940 tests). This candidate binds 94/94 exact-base source blobs and does not select technology, policy or implementation.

## 2. Mission and authority map

M11 proposes only a scoped OS worker/process association and lifecycle-evidence boundary for separately authorized IRIS work. It cannot create a new production or resource authority. No local or remote worker may actually launch under this planning proposal.

| Owner | Canonical authority | M11 candidate boundary |
|---|---|---|
| M02 | Production Graph causality, work identity and accepted ExecutionPlan | Consume opaque exact references; never create product transitions. |
| M06 | Operational attempts, revisions, reproducibility and materialization | Offer future process evidence by an owner-defined port; no adopted schema or success verdict. |
| M09 | Resource truth, reservations, claims, leases, residency and headroom evidence | Never assert resource truth or mutate grants; require a future verified owner-issued handoff. |
| M10 | Frozen advisory plan proposals and distinct risk evidence | Planner advice is not worker authorization, dispatch, placement or reservation. |
| M12 | Placement, queue/orchestration and multi-host policy (pending) | No local/remote selection, quota or failover inferred. |
| M26, M48, M53-M60 | DCC wrapper, quality, provenance, security, storage, telemetry, agents, public APIs, publication and release (index only) | Respect each owner; details and permissions remain PENDING_OWNER_CONTRACT and risk UNRATED. |

## 3. Candidate record semantics, not public serialization

| Candidate logical record | Bounded meaning | Boundary or unresolved decision |
|---|---|---|
| WorkerAssociation | Local M11 reference with exact opaque M02 work/plan and owner-issued optional M06 attempt reference plus uncertainty/provenance | Association cardinality, persistence, supervisor topology and OS identity not selected. |
| StartupPreconditions | Explicit owner-issued authorization/plan/resource/placement requirements, versions, proof and unknown/denied/unsupported results | M02/M09/M12/M54 handshake has no invented schema or implicit allow. |
| ProcessObservation | OS-scope process/descendant observation, capability, ownership proof, capture time and explicit error/conflict/unknown | A numeric PID or observed exit is neither semantic identity nor materialization. |
| ControlIntent | A requested subject/scope/action and verified owner-issued authorization reference when available | Intent does not confirm action acceptance or permit a signal/termination. |
| ControlEvidence | Distinguishes action permission, attempted OS operation, observed OS result, incomplete/unknown or denied response | No cancellation/kill/reaper or cleanup behavior is selected. |
| AttemptEvidenceHandoff | Minimal provenance-bound OS observations for a later M06 owner-defined port | M06 owns attempt outcome and materialization; M56 owns telemetry schemas. |
| RecoveryUncertainty | Durable or transient evidence of unknown ownership, PID reuse, unreachable worker or incomplete operation | No journal, replay, restart, idempotency or duplicate-effect policy is selected. |

## 4. Proposed invariant IDs (audit obligations, not frozen semantics)

| ID | Proposed invariant |
|---|---|
| M11-I01 | Keep exact owner-issued M02 work/plan references; process observation must never advance a canonical Production Graph state. |
| M11-I02 | Never mint, infer or substitute M02 identity from an OS process identifier, command line or process name. |
| M11-I03 | Keep M11 OS process evidence distinct from M06 operational attempts, revisions, materialization and final acceptance. |
| M11-I04 | Treat PID/PPID alone as insufficient evidence of identity, controllability, lineage or reaping ownership. |
| M11-I05 | Never control or claim cleanup of a foreign, ambiguous, reused, inaccessible or insufficiently authorized process. |
| M11-I06 | Do not treat M10 advice as accepted execution authorization or as an M09 resource grant. |
| M11-I07 | Do not mint, grant, renew, reclaim, release, reinterpret or assert truth about M09 leases, reservations or resource residency. |
| M11-I08 | Do not treat sampled VRAM/RAM/CPU readings, process liveness or an empty queue as proof of resource capacity or a lease. |
| M11-I09 | Required owner authorization, plan, resource or placement prerequisites that are missing, stale, conflicting or unsupported are non-admitting rather than permissive. |
| M11-I10 | M12 placement and multi-host quotas are pending an owner contract; neither a local nor remote target is inferred. |
| M11-I11 | Preserve distinctions among request intent, authorized acceptance, OS action attempt, signal delivery, process exit, M06 attempt outcome and accepted output. |
| M11-I12 | A caller timeout, asyncio cancellation or interrupted IPC connection does not prove OS process or descendant termination. |
| M11-I13 | Do not promise a reaper, orphan cleanup, escalation, descendant containment, retry, durability or recovery guarantee without matched OS/owner proof. |
| M11-I14 | Unknown or foreign recovery state must not silently trigger launch or create duplicate external side effects. |
| M11-I15 | Do not equate shell-free argument vectors with trusted executable path, environment, working directory, secrets or Windows batch invocation. |
| M11-I16 | No transport, process topology, PID handle, IPC protocol, operating-system adapter or OS service manager is selected by the reference-only technology review. |
| M11-I17 | No numerical concurrency, priority, fairness, CPU/RAM/VRAM headroom, timeout, cancellation escalation or backoff policy is selected without explicit owner-reviewed proof. |
| M11-I18 | OS process exit cannot certify M01 quality, M53 rights, M55 deletion, M59 publishing or M60 final acceptance. |
| M11-I19 | Authorization requires the future M54 owner contract; an OS handle or process ID is not an authenticated security principal. |
| M11-I20 | M06/M56 handoffs must preserve provenance, freshness, uncertainties and owner-defined permission-filtered telemetry without invented public serialization. |
| M11-I21 | An unavailable HIVE derived context never supersedes the exact Git checkpoint or immutable source/CI evidence. |
| M11-I22 | No process/action is authorized by this document or by passing doc-only CI; future implementation requires a separate Work Order and exact preflight. |
| M11-I23 | Revisit every M12–M60 index-only handoff after the corresponding canonical owner contract exists; absent details remain PENDING and risk UNRATED. |
| M11-I24 | Each unresolved S04/S05 question remains OPEN until a source-backed owner disposition is reviewed; generic fail-closed constraints do not answer it. |
| M11-I25 | Independent audit must block freeze on every remaining HIGH or CRITICAL authority conflict and distinguish unknown risk from proven zero risk. |
| M11-I26 | No frozen M10 semantic rule, M01 fidelity, M03 protected intent, rights/privacy or resource-owner invariant may be weakened to make the candidate appear complete. |

## 5. Failure and owner-dependency matrix

| Scenario | Candidate evidence disposition | Owner dependency |
|---|---|---|
| Missing or contradictory ownership, authorization, accepted plan or owner resource prerequisites | NOT_ADMITTED / INDETERMINATE, never silent execution | M02, M09, M12, M54 |
| Launch/registration OS error or unsupported platform capability | Distinct attempted action, failed/partial observation and no fictional success | M06, M11, M60 |
| Caller cancellation or timer expiration without observed worker exit | Keep request, timeout and OS outcome distinct | M06, M11, M54, M60 |
| OS exit with partial output | Observation only; no automatic commit, quality promotion, cleanup or publishing | M06, M48, M53, M55, M59 |
| Stale PID, supervisor failure, foreign descendant, conflicting recovered record | Explicit unknown and no unverified relaunch or control | M06, M11, M54, M60 |
| Stale resource pressure evidence, absent M09 grant or future M12 decision | No inferred headroom, lease, preemption, priority or placement | M09, M12, M56 |

## 6. Open decision register: verbatim source-backed S04 and S05

The 44 original questions below remain OPEN. They are recorded without inventing answers. This candidate carries S01-S03 question registers by reference to their canonical research files as well. Each later decision needs exact owner source, proof/evidence and audit disposition. M12-M60 contracts are all index-only/PENDING and risk UNRATED.

### S04 unresolved (21/21)

| ID | Original question | Referenced owner |
|---|---|---|
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

### S05 unresolved (23/23)

| ID | Original question | Referenced owner |
|---|---|---|
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

## 7. Required independent planning audit and proof obligations

Audit all 26 invariant proposals against M02/M06/M09/M10 frozen/available sources and S01-S05 session evidence. Explicitly grade unresolved S04/S05 owner/security/process authority decisions and the 49 index-only future-owner interfaces without scoring them as compatible. Challenge PID reuse, process breakaway, foreign-process control, duplicate launch/recovery, inherited secrets, stale M09 resource references, timeout-as-exit, exit-as-M06-success and M10 advice-as-dispatch. Require evidence-driven classification of each unresolved question. Missing M54/M60 security/platform authority blocks any implied callable process-control interface.

CI validation in this documentation increment proves repository consistency only: exact 94-source fingerprint lock, exact file allowlist, checkpoint mirrors, JSON syntax, governance validator, pinned GEF/HIVE bridges and the existing 3,940 tests. Real-process, OS, GPU or recovery validation requires separate admitted implementation and M51/M54/M60 proof plan.

## 8. Disposition

This is m11-contract-candidate-v0.1 PROPOSED_C01, not frozen m11-contract-v1.0. Independent planning audit and source-backed owner decisions are separate necessary gates; no M11/M10 implementation, process/IPC action, authorization model, numeric policy or technology default is admitted. M10 remains frozen at m10-contract-v1.0; WO-0014 BLOCKED; Issue #82 OPEN.
