# M11 S03 — Concurrency Limits, Priorities and Resource Leases

Status: PROPOSED_COMPLETE_PENDING_GOVERNANCE
Work Order: IRIS-WO-0015 / Issue #82
Planning base: 9463dfe087bd9991c7e9aaf40a956ff497a8b9f4
Base tree: b8b6520d4c33e0e1eecd5b1c483b45c070844e42
Branch: iris-wo-0015-m11-s03-concurrency-priorities-leases-20260925
Context Lock: .engineering/context-locks/IRIS-WO-0015-S03.json
Exact-main Governance at base: run 36070121053 / job 107868864362 — PASS
Research checked: 2026-09-25
M11 contract: NOT_FROZEN
M11 implementation: NOT_ADMITTED
M10 contract: m10-contract-v1.0 (FROZEN)
M10 implementation: NOT_ADMITTED
IRIS-WO-0014 preflight: BLOCKED

## Purpose and scope

Explore concurrency boundaries, queue and priority alternatives, backpressure, workstation headroom, and the handoff to M09 resource claims and leases and M12 orchestration. This is a planning record. It does not choose an M11 API, queue, process limit, priority policy, lease protocol, numeric headroom or formula.

The admitted change is documentation only. No worker, process, provider, Blender, ComfyUI, resource reservation or lease operation was performed. No hardware or runtime measurements were taken.

## Planning result

S03 records candidate boundaries and evidence for later owner review. It separates five quantities which must not be treated as interchangeable:

1. Work waiting in an application queue.
2. Work admitted by a future M11/M12 contract.
3. Logical attempts and process trees, whose mapping is not specified by M02/M06/M11.
4. Process and operating-system resource controls, which do not constitute a grant of M09 resource capacity.
5. M09 resource claims, leases, reservations and outcomes, which remain M09-owned.

No alternative is selected. Priority vocabulary, freshness and capacity rules, queue disposition, process limits, ownership/cardinality and lease-reference semantics remain unresolved. Unknown, stale, conflicting, denied, unsupported or unavailable evidence cannot be treated as permission to admit work; the concrete response and reporting contract still requires owner decisions.

## Canonical source facts and planning inferences

| Authority/source at the exact base | Canonical fact | S03 consequence |
| --- | --- | --- |
| M02, planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md | M02 owns semantic production/work identity, Production Graph causality, canonical ExecutionPlan, lifecycle and acceptance. A worker admission or successful attempt is not production acceptance. | Do not use queue order or a process count as a second work identity, plan or acceptance state. Attempt mapping remains unresolved. |
| M06, planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md | M06 owns operational revision/materialization and execution evidence. ExecutionAttemptPort is a future M11/M12 handoff; its payload and mapping are unspecified. | Do not assume whether one queued item, admitted job, attempt or process maps to another. |
| M09, docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md and iris_resource_twin/leases.py | M09 owns resource truth, typed claims, leases, reservations, residency and resource-control outcomes. The implementation contains an in-process LeaseBook; it is not evidence of a cross-process or distributed lease coordinator. | M11 may only consume a future owner-issued reference. It must not create, mutate, renew, release or assert M09 resource truth. The reference schema, freshness, cardinality and handoff remain unresolved. |
| M10, planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md and planning/compatibility/M10-FORWARD-COMPATIBILITY-SCAN.md | m10-contract-v1.0 is frozen. Recommendations remain advisory and do not dispatch, place work, reserve resources or control workers/processes. WO-0014 preflight is BLOCKED. | A recommendation cannot be treated as a queue command, priority authorization, capacity grant or process instruction. |
| PR-005, PR-006, PR-008 and PR-009 in docs/project-brain/02-REQUIREMENTS.md | Product requirements call for headless/background automation, a structured control surface, managed lifecycle/concurrency/cancellation/cleanup/orphan detection, and configurable workstation CPU/RAM/VRAM headroom. | The requirements do not settle counting boundaries, measurement ownership, defaults, formula, enforcement, GPU memory semantics or behavior when data is missing. No numerical value is chosen here. |
| M11 session map and S01/S02 records | S01 and S02 are complete for module planning only. No M11 contract is frozen. S04 and S05 have not started. | Keep this session inside concurrency, priority and resource-lease planning; do not define reaping, cancellation, timeout, retry or recovery behavior assigned to later work. |
| M11–M60 owner dependency register | Individual owner contracts M11–M60 are absent at the exact base; index and scan rows are candidate context only. | Keep each cross-owner interface pending until its owner contract exists. |

The following are planning inferences, not canonical owner decisions:

- A semaphore or bounded queue inside one event loop can limit work within that process but cannot, on its own, enforce a limit across independent supervisors or machines.
- An operating-system process-count or CPU control is a containment/enforcement mechanism, not a semantic work-admission decision and not proof that RAM or VRAM is available.
- A priority ordering may delay lower-priority items when higher-priority items continue to arrive. A priority data structure does not itself define aging, a guaranteed share, inversion handling or an urgency/deadline contract.
- “Lease granted”, “capacity feasible”, “process slot free” and “attempt accepted” are distinct facts with different owners.

## Concurrency and admission boundaries to compare

| Boundary option | What it could count or constrain | Evidence and trade-off | Unresolved owner questions |
| --- | --- | --- | --- |
| In-process async task slots | Tasks admitted through one event loop | Simple local coordination; no guarantee across multiple supervisors, processes or hosts. | Is the governed unit a task, workflow, job, attempt or provider operation? Who owns aggregate limits? |
| Bounded application queue | Waiting items held by one process | A bounded queue can apply producer backpressure locally; FIFO and priority queues encode ordering, not resource feasibility. A blocked producer can also wait indefinitely unless a later contract defines cancellation and timeout. | What happens at capacity: wait, reject, defer, surface a retryable state, or another owner-defined result? |
| Logical workload or attempt slots | M02/M06-referenced units | Could express a product-level concurrency boundary but requires canonical identity and cardinality handoffs. | Which M02/M06 reference and lifecycle is authoritative? May retries overlap? |
| OS process/job-tree limits | Processes grouped under a platform containment object | Can constrain processes independently of application queue semantics; platform permissions and child/breakaway behavior matter. | Which owner creates and owns the containment object? What is the supported host baseline and failure response? |
| Resource-aware admission | CPU, RAM, VRAM or other claims | Must use M09-owned resource evidence and grants; measurements and process counts alone do not equal a grant. | Which claim dimensions, freshness and policy are owned by M09, and which decisions belong to M12? |
| Multi-supervisor or remote aggregate | Work across local, LAN, remote or cloud coordinators | Requires shared authority and conflict behavior beyond a process-local primitive. | M12 placement, queues, quotas, remote-host and preemption contract is absent. |

No count, aggregate limit, admission rule, default, fallback or combination is selected.

### Workstation headroom alternatives

PR-009 calls for configurable CPU/RAM/VRAM headroom, but no owner freezes how it is represented or enforced. Two planning options remain:

| Option | Potential benefit | Risks and evidence needed | Status |
| --- | --- | --- | --- |
| Operator-configured static headroom | Stable and explainable configuration when an operator knows the workstation use case. | A static value can become stale across hardware, workload or interactive-use changes. The configuration owner, scope, validation and safe behavior when absent are not defined. | Option only; no values or formula selected. |
| Evidence-driven headroom | Could account for changing host pressure and workload evidence. | Needs M09 resource observations, freshness/uncertainty behavior, measurement coverage and M56 telemetry provenance. A measurement is not itself an M09 grant; missing evidence cannot silently admit work. | Option only; no estimator or formula selected. |

These options are not combined here. No CPU, RAM or VRAM default, reserve, percentage, conversion, estimator or enforcement mechanism is selected.

## Priority, fairness and coexistence questions

“Priority” may describe different things. They must remain separate until an owner contract defines any mapping:

- Application queue ordering.
- Service or tenant fairness and workload class.
- M12 placement or orchestration preference.
- Operating-system CPU scheduling priority.
- M10 advisory ranking or risk recommendation.
- Interactive workstation responsiveness or an operator's urgency request.

These concepts have different effects and authority. Raising OS CPU scheduling priority does not grant GPU memory, create an M09 lease, make an M10 recommendation binding or guarantee service-level fairness.

| Alternative to evaluate later | Potential benefit | Main risk or proof question | Status |
| --- | --- | --- | --- |
| FIFO | Understandable arrival order and a baseline for comparison | Long work can delay short work; a single ordering may not preserve interactive responsiveness or tenant shares. | Compared only; not selected. |
| Strict priority | Higher-ranked work can be dequeued first | Sustained high-priority arrivals can starve lower classes; priority source, trust, ties and preemption remain undefined. | Compared only; not selected. |
| Aging | Waiting time can gradually affect ordering | Needs a time source, aging formula, limits and interaction with authorization; those would be policy choices. | Open question. |
| Weighted service or per-class queues | Could reserve service attention across classes | Requires class ownership, weight meaning, resource accounting and fairness evidence. | Open question. |
| Deadline/urgency ordering | Could express time sensitivity | Deadline provenance and clock/freshness semantics are not owned here; deadlines must not be inferred from a priority label. | Open question. |
| Priority inversion | Could expose when work with a higher ordering value waits on a resource held by other work | The lock/lease ownership, resource protocol and any inheritance or preemption response are unresolved. The scenario is a planning inference, not a frozen IRIS behavior. | Open question. |
| OS scheduler priority | Can influence CPU scheduling for a process/job | Platform-specific and separate from application fairness and M09 CPU/RAM/VRAM claims; can harm workstation coexistence if misused. | Platform capability only; no policy selected. |
| Preemption | Could reclaim a slot for more urgent work | This session cannot define interruption, partial output, lease release, cleanup or recovery; these cross M09, M12, M54 and S05. | Deferred; not authorized here. |

A queue being full, a resource reference being unknown or stale, a grant being denied, two sources conflicting, a platform feature being unsupported, or measured capacity being unavailable are explicit planning cases. They must remain non-admitted/unknown until the owning contracts define a visible outcome. S03 does not define retries, timeouts, default priority, automatic downgrade, lease mutation, preemption or a numeric fallback.

## Unresolved question register

Every question remains open; the identifiers are used by the S03 evidence record.

| ID | Question to resolve with the owning contract |
| --- | --- |
| S03-U01 | Does concurrency count queued work, admitted work, an M02 workload, an M06 attempt, a provider operation, a process, or a process tree? |
| S03-U02 | Is a limit local to one event loop, one supervisor, one workstation, a pool, or a remote aggregate, and which owner coordinates it? |
| S03-U03 | What M02 work/plan reference is preserved, and which owner controls the relationship between that identity and queue/admission state? |
| S03-U04 | What is the M06 attempt relationship and cardinality for retries, overlapping attempts and process descendants? |
| S03-U05 | What opaque M09 claim/lease/grant reference, if any, can M11 receive without owning its schema or mutation? |
| S03-U06 | Who defines resource reference freshness, epoch/version, expiry, revocation and stale/conflict behavior? |
| S03-U07 | How are M09 grant/deny outcomes distinguished from observed CPU/RAM/VRAM feasibility and from a free process slot? |
| S03-U08 | What caller-visible state is required when resource evidence is unknown, stale, conflicting, denied or unsupported? |
| S03-U09 | What happens when a bounded queue has no capacity: wait, reject, defer or another owner-defined response, and who owns cancellation/timeouts? |
| S03-U10 | Which priority concepts exist, who may assert them, and how are M10 advisory output and any operator urgency kept non-authoritative until an owner decides? |
| S03-U11 | What ordering, tie handling and priority provenance are required, if any? |
| S03-U12 | Which fairness or starvation guarantee is required across workload classes and tenants, if any? |
| S03-U13 | Are aging, weighted service or separate queues acceptable, and who owns their policy and proof? |
| S03-U14 | How is resource priority inversion treated, and is preemption permitted after M09/M12/S05 define interruption, partial output and cleanup semantics? |
| S03-U15 | Is PR-009 headroom operator-configured, evidence-driven or something else, and which owner controls configuration and enforcement? |
| S03-U16 | Which CPU, RAM and VRAM measurements and uncertainty/freshness semantics are authoritative? |
| S03-U17 | Which OS process/job controls are supported by each M60-approved platform and what does unsupported or failed setup mean? |
| S03-U18 | What evidence and responsiveness target represent coexistence with interactive workstation use? |
| S03-U19 | Which M12 owner coordinates multiple supervisors, GPUs, LAN/remote hosts, quotas and placement? |
| S03-U20 | Which M54 trust and authorization rules protect queue/priority/lease references, and what queue/worker evidence belongs to M56? |

## Technology discovery

The following records use the next IDs after S01/S02. Each is an existing technology comparison, not an implementation selection.

### TECH-M11-011 — Python 3.12 asyncio bounded queues and semaphores

- **Classification/status:** EXISTING_TECHNOLOGY / PROPOSED.
- **Purpose and operating model:** An event-loop-local asyncio.Queue(maxsize=...) supports FIFO producer/consumer flow; asyncio.PriorityQueue retrieves items by priority ordering; asyncio.Semaphore coordinates a counter among async tasks.
- **Potential benefit:** Standard-library primitives could express local in-process waiting and backpressure without an external service.
- **Dependencies:** A single event loop, in-memory state and later M11/M12 decisions about item identity and queue behavior.
- **Risks/failure modes:** Asyncio queue and synchronization objects are not thread-safe; state is not shared across processes or hosts. A zero/default maxsize is unbounded. Queue priority gives no IRIS meaning to values, fairness guarantee, aging, authorization, resource claim or recovery behavior. A blocked producer can wait until a consumer progresses.
- **Future benchmark/proof plan:** With synthetic arrivals, compare FIFO and priority ordering, bounded/full behavior, producer wait, queue wait and fairness metrics. Include shutdown, consumer loss, saturation and multiple-supervisor tests after the owner contract exists. Do not benchmark now.
- **Destination:** Future M11/M12 queue and concurrency review; evaluate only after identity, backpressure, failure and aggregate-scope owners agree.

### TECH-M11-012 — Python 3.12 queue.PriorityQueue comparison

- **Classification/status:** EXISTING_TECHNOLOGY / PROPOSED.
- **Purpose and operating model:** A thread-safe standard-library queue for threaded consumers, with bounded insertion and lowest-valued entry retrieved first.
- **Potential benefit:** A distinct comparison if a future supervisor uses worker threads instead of asyncio.
- **Dependencies:** Threading model, in-process owner and explicit priority ordering/tie representation.
- **Risks/failure modes:** The queue does not supply M12 policy, priority provenance, fairness or starvation protection. It is in-process and does not coordinate independent supervisors; a full blocking queue still needs owner-defined timeout, cancellation and caller-visible behavior.
- **Future benchmark/proof plan:** Compare lock/contention and queue latency only after the threading model is admitted; test tied priorities, saturation and starvation under controlled synthetic loads. No benchmark was run.
- **Destination:** Future M11 implementation alternatives; not a recommendation to switch from asyncio or to select threads.

### TECH-M11-013 — Windows Job Objects

- **Classification/status:** EXISTING_PLATFORM_TECHNOLOGY / PROPOSED.
- **Purpose and operating model:** Windows can group processes into a job object; child processes are associated by default, and job limits can include active process count and CPU-rate controls.
- **Potential benefit:** Platform-level grouping and containment may constrain a process tree more directly than an application task semaphore.
- **Dependencies:** A Windows host, process creation/assignment rights, a defined job owner, version support and correct treatment of nested jobs and child processes. Microsoft documents nested jobs as introduced with Windows 8 and Windows Server 2012; older behavior differs. This is a platform fact, not IRIS's supported-version decision, which remains with M60.
- **Risks/failure modes:** Breakaway configuration can exclude descendants; assignment or limit failures need an owner-defined result; association/security/host constraints can prevent use. A process-count cap is not an M09 resource grant, application-level admission policy, GPU VRAM measurement or priority fairness policy.
- **Future benchmark/proof plan:** On each M60-supported Windows version, prove child-process membership, active-process limit behavior, breakaway/assignment failure handling, CPU-control observability and coexistence. Use isolated synthetic children only after implementation admission; none were launched in this session.
- **Destination:** M11/M60 platform feasibility review, with M54 security ownership. No Windows baseline or limit is selected.

### TECH-M11-014 — Linux cgroup v2 CPU and memory controllers

- **Classification/status:** EXISTING_PLATFORM_TECHNOLOGY / PROPOSED.
- **Purpose and operating model:** Linux cgroup v2 can distribute CPU cycles and control/account for memory by hierarchy, subject to controller availability, enablement and host configuration.
- **Potential benefit:** Host-level grouping and accounting can cover a process tree and expose controls below application-level queueing.
- **Dependencies:** A supported Linux kernel and cgroup v2 hierarchy, enabled controllers, suitable delegation/permissions and a host-manager integration decision.
- **Risks/failure modes:** Controller availability and ancestor constraints vary by host; some CPU controls do not apply to every scheduling class, and real-time behavior has documented limitations. Memory accounting is not a measure of useful workload headroom. These controls do not provide GPU VRAM truth, M09 leases, M12 placement or IRIS service fairness.
- **Future benchmark/proof plan:** On each M60-supported Linux distribution and configuration, establish delegated-controller availability, process-tree accounting, CPU and memory control behavior, inherited limits and failure modes. Compare observed host impact with M09 evidence. No host was inspected or measured.
- **Destination:** M11/M60 Linux platform feasibility review, with M09 resource evidence ownership. No Linux baseline, cgroup layout or resource limit is selected.

### TECH-M11-015 — RabbitMQ priority queues, comparison only

- **Classification/status:** EXISTING_EXTERNAL_QUEUE_TECHNOLOGY / PROPOSED. This record is a comparison only.
- **Purpose and operating model:** A brokered queue can dispatch messages according to configured priority; RabbitMQ documents priority behavior for classic and quorum queues. As documented on the checked date, strict priority for quorum queues is available from RabbitMQ 4.3; this is a product capability, not an IRIS version requirement.
- **Potential benefit:** A concrete comparator for broker-owned queue ordering and consumer delivery behavior if a future M12 design considers remote or brokered coordination.
- **Dependencies:** An independently operated broker, network, service identity and M12 ownership of remote queue/placement semantics.
- **Risks/failure modes:** The broker introduces deployment, connectivity and authorization dependencies that are absent from the current local IRIS evidence. RabbitMQ documents that strict priority may indefinitely delay lower-priority messages under sustained higher-priority arrivals. Broker queue priority is not M09 resource arbitration and does not prove workload fit.
- **Future benchmark/proof plan:** Only if M12 admits a brokered queue, compare queueing delay, class starvation, consumer prefetch, broker outage/reconnect and resource-accounting boundaries using a controlled deployment. No broker was installed, contacted or benchmarked.
- **Destination:** M12 architecture comparison only. Not selected for IRIS M11 and not evidence that IRIS needs a broker.

### Existing IRIS candidates and proprietary-candidate status

S01 proposed CAND-M11-001 (reference-only work/attempt/process association); S02 proposed CAND-M11-002 (reference-preserving startup and registration envelope). Both remain PROPOSED; S03 does not change their status or define their schemas. No new proprietary candidate is advanced because M09 reference semantics and M11/M12 ownership boundaries are not yet settled. No novelty or patent claim is made.

## Internal reuse

- iris_resource_twin/leases.py proves that IRIS contains an in-process LeaseBook for M09 resource/lease semantics. It does not prove that the object can coordinate independent OS processes, multiple supervisors or remote hosts, and S03 does not extend it.
- scripts/gef_preflight.py and scripts/hive_mcp.py contain narrow one-shot subprocess use; they do not prove a reusable worker fabric, queue, process-wide concurrency controller or lease coordinator.
- UGAS, HIVE and CORE supervisor or resource-coordination reuse remains UNVERIFIED. The HIVE project is offline in this environment and its MCP checkpoint response was not current. No HIVE-derived statement is used.

## Pending owner register

The exhaustive M11–M60 dependency register marks every individual owner contract in that range PENDING_OWNER_CONTRACT. Master-index and M10 scan descriptions remain candidate context, not owner decisions. This session records the following direct dependencies:

| Owner | S03 question that must wait for the owner contract |
| --- | --- |
| M09 | Typed CPU/RAM/VRAM claims, source and freshness of resource evidence, lease/grant/deny outcomes, opaque reference form, validity and mutation rules. |
| M10 | Advisory outputs only; no command, dispatch, placement, priority authorization, reservation or process control. |
| M11 | Queue/admission boundaries, boundedness, local versus aggregate scope, unknown/error states and future interfaces remain part of the unfinished contract. |
| M12 | Local versus remote placement, orchestration queues, quotas, priority authority, preemption, multi-GPU/host aggregation and capacity ownership. |
| M13–M15 | Performance evidence, model/risk estimates and policy semantics; no index-level statement binds M11. |
| M16–M19 | Workflow/provider queue and runtime boundaries, acquisition/integrity, model/workload capabilities and related invalidation signals. |
| M26 | Supported Blender/DCC version, background process and resource semantics, adapter boundary. |
| M51 | Benchmark ownership, workload corpus, repeatability and acceptance of resource/fairness evidence. |
| M52 | Any future HIVE context handoff; none is used as authority in this session. |
| M54 | Principal, authentication/authorization, sandbox, environment, secret handling and trust in priority or lease references. |
| M56 | Event and correlation identity, queue/worker telemetry, freshness, logging, redaction and retention. |
| M57–M58 | Automation authorization/stop conditions and any public API/SDK/MCP projection. |
| M60 | Supported host and service model, setup, platform capability detection, upgrade/restart/recovery and final acceptance. |
| All remaining M12–M60 owners | Individual input/output, lifecycle, error, evidence and authority semantics remain pending as registered; no behavior is inferred for them here. |

## Future benchmark and proof plan

This plan is a proposal for later owner-approved work. No measurements, runtime tests, process experiments or resource operations were performed for S03.

1. Define the counted unit and ownership first: waiting item, admitted unit, attempt, provider operation and process tree; explicitly test the non-equivalence and any M02/M06 mapping.
2. Create a deterministic synthetic arrival corpus with mixed durations and classes. Record queue wait, admitted/start/finish timing, throughput and per-class wait distribution under FIFO, strict priority, aging and weighted-service comparators. Report starvation and tie behavior rather than selecting a policy from averages alone.
3. Exercise bounded capacity with slow, absent and failed consumers; verify that producer behavior and caller-visible states are explicit and that unknown, stale, conflict, denied, unsupported and capacity-unavailable evidence does not silently become admission.
4. Use mock, opaque M09 references for granted, denied, stale, conflicting and unsupported cases. Prove that M11 passes or reports references without mutating a lease and that a process slot or OS limit cannot substitute for M09 capacity evidence.
5. Compare one process-local coordinator with multiple independent supervisors to show which limits are local and which require M12 coordination.
6. On the M60-approved Windows and Linux matrix, record OS/kernel, Python, controller/host configuration, hardware, workload and measurement method. Verify OS-level containment/accounting separately from queue admission and M09 resource evidence.
7. Include interactive workstation response and CPU/RAM/VRAM evidence only through their owning measurement authorities. Define no headroom default, formula, worker limit, priority value, deadline or recovery budget during this session.
8. Have M51/M56 owners approve the corpus, metric definitions, provenance, freshness and retention before any result is used as a product claim.

## Official technology references

Checked 2026-09-25. These sources describe technology behavior; they do not grant IRIS authority or select an implementation.

- Python 3.12 asyncio synchronization primitives: https://docs.python.org/3.12/library/asyncio-sync.html
- Python 3.12 asyncio queues: https://docs.python.org/3.12/library/asyncio-queue.html
- Python 3.12 thread-safe queues and PriorityQueue: https://docs.python.org/3.12/library/queue.html
- Microsoft Learn Windows Job Objects: https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
- Microsoft Learn active process limits: https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information
- Microsoft Learn CPU rate controls: https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_cpu_rate_control_information
- Linux Kernel Control Group v2 documentation: https://docs.kernel.org/admin-guide/cgroup-v2.html
- RabbitMQ Priority Support in Queues: https://www.rabbitmq.com/docs/priority

## S03 review checklist

- [x] Exact issue, base SHA, base tree, branch and base Governance run pinned in the Context Lock.
- [x] Critical Git sources fingerprinted and matched at the exact base.
- [x] M02, M06, M09 and M10 authority checked; absent M11 and M12–M60 contracts retained as pending.
- [x] Official primary technology documentation checked and linked.
- [x] Options, dependencies, benefits, risks/failure modes and future proof plans recorded with stable candidate IDs.
- [x] M09 lease mutation, resource truth, numeric policy selection, runtime implementation and cross-owner semantic invention excluded.
- [x] Four-file path inventory, governance validator, bootstrap compile and repository suite passed locally on Python 3.13.15.
- [ ] Exact-head Governance must still run on the Draft PR head; repository CI uses Python 3.12.
- [ ] Draft PR against main, linked to Issue #82, remains a required delivery gate.
