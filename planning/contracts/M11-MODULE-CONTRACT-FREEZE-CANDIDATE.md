# M11 Background Worker Fabric & Process Lifecycle: Versioned Owner-Contract Candidate

Status: PROPOSED_C02_CORRECTION_NOT_FROZEN
Candidate ID: m11-contract-candidate-v0.2 (C02 correction; not a frozen module contract)
C01 lineage: m11-contract-candidate-v0.1 merged through PR #101; audit C01 through PR #103; original M11-I01..I26 and 44 original S04/S05 questions retained.
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

## 9. C02 Correction Delta: minimum semantic safety interfaces (proposal, not freeze)

C02 revises only this candidate to `m11-contract-candidate-v0.2` from the audited C01 draft. Bound correction base: `6006be5af8f58ac6eec00df030fffab2d1d121ab` / tree `039f6fc7e4d89a20af830bdd09ad994a8a26ee58`, after separate audit PR #103 protected merge and exact-main Governance #440 (run 36285939240). C01 I01–I26 and all 44 original S04/S05 OPEN questions remain unchanged; this annex adds positive M11-owned *semantic records and refusal behavior* without adopting a wire schema, IPC, OS adapter, authentication principal, provider, concurrency limit or executable policy. M12/M54/M60 owner contracts are not available. Therefore every callable process start/control capability remains **DISABLED**. Read this annex together with §§2–8 and the AUD-C01-H01..H03 audit obligations.

### 9.1 M11 semantic input and preflight envelope (AUD-C01-H01)

The proposed M11-owned `WorkerRequestEnvelope` has required fields with the following semantic meanings. These names are candidate logical roles, not an exported API or an assertion that another owner already exposes a matching port:

| Required role | Minimum semantic obligation | Authority |
|---|---|---|
| M11 correlation reference | A request-local opaque unique reference and revision scoped solely to M11 process evidence; not M02 work identity or authorization. | M11 |
| M02 accepted-work evidence | Exact owner-issued work/plan reference and verifiable accepted-status evidence, with issuer/contract revision and provenance. Missing or merely proposed M10/M02 evidence is non-admitting. | M02 |
| M09 grant-state evidence | An owner-issued, verifiable, currently applicable resource decision/reference, bound to the same workload/resource scope. M11 does not create or renew a lease or assert current capacity. | M09 |
| M12 placement decision | Owner-issued target/scope and validity evidence under the future M12 contract. No local/remote placement or queue ownership is inferred. | M12 (PENDING) |
| M54 authorization decision | Owner-issued and verifiable permission decision bound to actor/subject reference, requested action, target scope and current validity. Principal schema, cryptography and policy stay exclusively M54-owned. | M54 (PENDING) |
| M60 platform capability | Owner-proven platform/adapter capability and supported action/target validity, including executable, environment and process-rights prerequisites where applicable. | M60 (PENDING) |
| M06 attempt association | Only when an actual M06-issued attempt reference is available; absence must be represented explicitly and cannot be fabricated. Never an M11 completion result. | M06 |

Each owner proof requires an opaque issuer/source reference, contract/revision reference, evidence scope, capture/freshness disposition and explicit validity or unknown/error result **when such an owning port exists**. These obligations do not specify another owner's data schema or numeric expiry. The envelope is invalid if proofs conflict or are not for the *same exact request and intended action*. An unavailable owner contract/port is `UNSUPPORTED`, not a convenient default. If M54 or M12 cannot issue/verify an applicable decision, a positive execution preflight is impossible.

`M11PreflightDisposition` has separate logical outcomes `DENIED`, `UNSUPPORTED`, `INDETERMINATE`, `STALE_OR_CONFLICTING`, and `CONTRACT_ELIGIBLE`. The last is a documentation-only statement that all applicable **owner-issued** obligations were verified in a future admitted implementation; it is neither a dispatch permission nor an OS-action receipt. No outcome permits execution from this candidate. Fail-closed is mandatory for every nonpositive/missing input. M11 may never infer permissions from an OS handle, a numeric PID, an existing process, an M10 recommendation, local availability or stale telemetry. A future M54-owned permission port and M12-owned placement port are mandatory before any positive start/control outcome can be admitted.

### 9.2 Positive process-ownership evidence boundary (AUD-C01-H02)

The proposed `ProcessCapabilityEvidence` is an opaque, versioned and action-scoped OS-association proof, minted only from an actual M11-authorized launch and an M60-qualified platform/adapter owner. Its required logical roles are: the exact M11 request/revision, source and provenance of the **OS-issued process handle or equivalent owner capability**, verified direct-child/parent or owner relationship, rights to observe/wait/control *for the requested operation*, handle lifetime and freshness/validity result, platform/adapter capability proof, and distinct descendant-containment support or explicit `UNSUPPORTED`. A numeric PID/PPID, process name, command line, inherited environment, process group ID or OS exit code never substitutes for this proof. If any proof is absent, reused, stale, inaccessible, foreign or conflicting, disposition is `NO_CONTROL` / `INDETERMINATE`. No process is signaled, collected, waited on, terminated or claimed cleaned up under this proposal.

`ProcessObservation` must bind that exact capability and explicitly distinguish `RUNNING_OBSERVED`, `EXIT_OBSERVED`, `OBSERVATION_FAILED`, `UNKNOWN` and `UNSUPPORTED` at the evidence scope and capture time. No observation establishes current M09 lease state or final M06 attempt status. Descendant observation/containment is independent from a direct-child relationship; unsupported POSIX group, optional subreaper, Windows Job Object, inherited job, process breakaway and OS privilege semantics remain separate M60 proofs. Reaping must be `NOT_PERMITTED` until a still-valid owner-issued wait/reap right is positively verified; neither parent death nor PID matching grants that right. No default supported OS/kernel/service matrix is selected.

### 9.3 Ordered control, incomplete outcome and recovery boundary (AUD-C01-H03)

The proposed `M11ControlEvidenceSeries` is an append-only *logical* sequence, with one M11 correlation reference, exact request/action/scope and versioned provenance. Each distinct stage is independently observable and may remain unknown: `INTENT_RECORDED`, `OWNER_AUTHORIZATION_VERIFIED`, `OS_OPERATION_ATTEMPTED`, `OS_DELIVERY_OBSERVED`, `EXIT_OBSERVED`, `M06_OUTCOME_REFERENCED`. These are evidence categories, not an adopted state machine, transport protocol or assumption that every stage occurred. A cancellation request, accepted request, coroutine/IPC timeout, signal attempt and process exit must never be collapsed. Only an M06-issued outcome reference can describe the M06 attempt; only the owning quality/provenance/storage/publishing owners may accept or discard outputs.

`M11RecoveryReconciliation` is observation-first and has `UNKNOWN` as its safe default for lost/stale/ambiguous handles, supervisor crash, conflicting records, unreachable worker or unknown external side effects. No automatic retry/restart, duplicate launch, process reclamation, owner lease release, storage deletion, attempt promotion or recovery journal is selected or allowed by this candidate. A future positive replay/restart requires *all* independently verified owner decisions for M02 causality/idempotency, M06 attempt/recovery evidence, M09 resource state, M12 placement, M54 authorization and M60 platform support; their schema and policy are external and pending. Missing any one yields `NOT_ADMITTED` and an explicit owner-specific missing/unknown reason. M11's local correlation reference alone never establishes idempotency.

### 9.4 C02 additive proof obligations and invariant proposals

| ID | Additional proposed invariant |
|---|---|
| M11-I27 | Every candidate M11 request binds one exact owner-accepted M02 work/plan reference and per-action M11 correlation; neither identity authorizes execution. |
| M11-I28 | An M11 preflight may be positive only with mutually applicable, currently verifiable M02/M09/M12/M54/M60 owner proofs; any missing, stale, conflicting, denied or unsupported owner decision is non-admitting. |
| M11-I29 | Until versioned M12, M54 and M60 ports and independent platform/security proof exist, start/control remain DISABLED even if documentation CI passes. |
| M11-I30 | A controllable process requires an M60-qualified, action-scoped and lifetime-valid OS capability bound to the exact M11 request, never just PID/PPID or process name. |
| M11-I31 | Foreign, ambiguous, stale, reused, inherited or inaccessible process identities are never controllable by M11. |
| M11-I32 | Waiting/reaping and descendant containment require separately proven valid platform/owner rights and capabilities; unsupported behavior remains UNSUPPORTED. |
| M11-I33 | Record control intent, authorization verification, OS attempt, delivery observation, OS exit and M06 outcome as separate provenance-bound evidence categories. |
| M11-I34 | Timeout, interrupted IPC, lost parent, cancellation or unknown process observation cannot be promoted to a confirmed OS exit or M06 success. |
| M11-I35 | Recovery with missing or conflicting authority remains UNKNOWN and cannot trigger retries, relaunches, deletion, lease changes or duplicate external effects. |
| M11-I36 | Any future replay/restart requires independent fresh owner-issued M02/M06/M09/M12/M54/M60 authorizations; M11 supplies evidence, never overrides their policy. |

The minimum semantic proof matrix for later owner-approved implementation/benchmark planning is: `PO-C02-01` M54 authorization unavailable ⇒ no positive preflight; `PO-C02-02` stale/conflicting M09 evidence ⇒ no resource claim or start; `PO-C02-03` M12 placement unknown ⇒ no implicit local placement; `PO-C02-04` PID reuse/foreign handle ⇒ no control or reap; `PO-C02-05` cancelled coroutine/IPC timeout without exit evidence ⇒ unknown process outcome; `PO-C02-06` supervisor crash with ambiguous external effects ⇒ no automatic relaunch; `PO-C02-07` partial output after OS exit ⇒ no M06 materialization, rights, quality or release claim; `PO-C02-08` unsupported POSIX/Windows descendant capability ⇒ no cleanup guarantee. These are **future proof obligations**, not executed runtime tests in this documentation correction.

### 9.5 Corrective disposition and STOP boundary

This C02 proposal responds to `AUD-C01-H01`, `H02` and `H03` with concrete M11-owned input, output, error/unknown and permission-verification *boundary semantics*. The actual M54 principal and security policy, M12 placement, M60 adapter/OS rights, M06 attempt port, numeric timeouts, resource/workstation headroom, runtime technology and IPC serialization remain pending their owners. Re-audit the corrected candidate on its **exact final head**; an independent reviewer, not the executor, must decide whether those three findings are discharged within the inert semantic-freeze scope. Nothing here freezes `m11-contract-v1.0`, grants executable process authority or admits M10/M11 implementation. Issue #82 stays OPEN.
