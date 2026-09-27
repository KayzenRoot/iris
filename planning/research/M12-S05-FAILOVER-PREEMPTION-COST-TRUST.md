# M12 S05 — Failover, Preemption, Cost/Quality Placement and Trust

Status: PROPOSED_NON_EXECUTABLE_REFERENCE_RESEARCH | Issue #128 / IRIS-WO-0026
Exact source base: `278d3c2905237dfb90a1d0db60cc5db54b834811`; tree `030650da12d2ac36d5bf162c0f61b1578de8a291`. Exact-main Governance #491 PASS 3979/3979.
No retry engine, failover topology, cloud spending policy, process signal, M09 owner port, public API, OS operation or positive dispatch is adopted.

## 1. Why failure recovery cannot be inferred from scheduling

M12 S01–S04 are only source-backed reference studies. An advertised worker, ranked queue, qualified-looking GPU or reachable remote site cannot authorize a retry. Frozen M02 owns accepted production work, M06 owns the operational attempt and artifact lineage, M09 v1.0 owns resource/lease truth, M10 v1.0 is strictly advice, and M11 v0.2 remains NOT_FROZEN without admitted OS worker lifecycle. M54/M55/M56/M58/M60 owner contracts are index-only pending. Four M09↔M11 C02 blockers H01–H04 stay OPEN HIGH_FOR_FUTURE_FREEZE: no actual owner decision A/B/C (#110), no proved jointly coherent M09 snapshot+lease cut (H02), no authenticated reverse M11 liveness (H01), other permission/identity owner gates unresolved.

In particular an M11-style cooperative cancellation `ACCEPTED_AWAITING_RESOURCE_RECONCILIATION` must not be described as M09 capacity reclaimed. Unreachable does not mean dead; process exit does not mean M06 accepted output; a cloud interruption hint does not prove the instance terminated or a checkpoint was created. No runtime/system-side effect occurs in this document.

## 2. Official external reference comparison, not IRIS adoption

| Primary publication | Documented approach | Missing IRIS-specific proof |
| --- | --- | --- |
| Ray task fault tolerance | Configurable task retries after worker/node failure | Accepted M02 work and safe replay of M06 externally visible effects |
| Kueue ClusterQueue preemption | Configurable priority/cohort/quota preemption | Owner-issued M09 grant and separately authorized M11 process cancellation |
| Kubernetes Pod Disruptions | Voluntary/involuntary disruptions differ and PodDisruptionBudget constrains some voluntary cases, not all failures | M11 OS proof and M09 actual resource reconciliation, not just a disruption policy |
| AWS EC2 Spot best practices | Interruptible capacity, best-effort rebalance and interruption warnings; safe applications design for unexpected loss | M02/M06 checkpoint, M09 lease disposition, user consent and realistic cloud/transfer cost |

Official primary docs consulted 2026-09-27:
- https://docs.ray.io/en/latest/ray-core/fault_tolerance/tasks.html
- https://kueue.sigs.k8s.io/docs/concepts/preemption/
- https://kubernetes.io/docs/concepts/workloads/pods/disruptions/
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-best-practices.html

None is an adopted IRIS implementation or evidence that retry/preemption, Kubernetes/Ray/Kueue/AWS or hardware tests ran.

## 3. Six recovery/placement approaches for future owner selection

| ID | Candidate for comparison | Status |
| --- | --- | --- |
| R-01 | Hold candidate work for explicit owner adjudication with no automatic retry | CONSIDERED_NOT_SELECTED |
| R-02 | Future checkpoint-aware resume with verified M02/M06 attempt and immutable checkpoint provenance | CONSIDERED_NOT_SELECTED |
| R-03 | Owner-approved idempotent retry only after verified process exit, effects and grant disposition | CONSIDERED_NOT_SELECTED |
| R-04 | Separate-site failover after authenticated node/worker fencing and new owner-issued resource proof | CONSIDERED_NOT_SELECTED |
| R-05 | Cooperative interruption/preemption requests with explicit M11 acknowledgment and M09 reconciliation | CONSIDERED_NOT_SELECTED |
| R-06 | Policy-bounded cost/quality placement with actual costs, user consent, evidence and workstation protections | CONSIDERED_NOT_SELECTED |

All potential recoveries require separately verified owner proofs and event history; manual adjudication itself still needs identity/authorization and M06 correctness. There is no numeric retry count, preemption timeout, cloud budget, cost weight or default user policy selected here.

## 4. Owner-specific gates before any future positive recovery

| Gate | Owner and future evidence | Unsafe short-circuit |
| --- | --- | --- |
| Intent and effects | M02 accepted work + M06 exact attempt/outcome and known external-effect class | Same user prompt means retry is harmless |
| Liveness and worker rights | M11 authenticated exact worker/OS process ownership, platform permission from M60, security M54 | Missing heartbeat, exit status or PID implies safe signal/relaunch |
| Resource truth | M09-issued exact request/member grant, coherent snapshot+lease proof and actual reclamation, if future handoff approved | Cached VRAM, two RLocks, cooperative ack or quota means resource released |
| Checkpoint/artifact | M06/M55/M59 integrity, revision, media rights and partial-output state | Files exist on disk or remote bucket so outcome succeeded |
| Security and budget | M54 policy and data transfer rights plus real compute/egress/latency/interrupt cost observations | Cloud quote or M10 advice authorizes expense and export |
| Quality/telemetry | M48/M56 actual measured quality, observed latency and traceable owner events | One green dashboard light or an advisory score proves correctness |
| Reconciliation | M02/M06 idempotency and attempt epochs + M09/M11 owner fencing and revocation | Another scheduler node may simply take over after timeout |

## 5. Negative/ambiguous scenario backlog

These **20** future FT cases are SPECIFIED_NOT_EXECUTED, not CI-passed runtime or fault-injection tests.

| ID | Trigger | Safe non-inference to be proven later | Owner |
| --- | --- | --- | --- |
| FT-01 | Network partition but old remote process continues after heartbeat loss | No automatic duplicate retry or OS-death inference | M02/M06/M11 |
| FT-02 | M09 preemption request accepted but resource reconciliation pending | No positive capacity-reclaimed or new grant claim | M09/M11 |
| FT-03 | Recycled OS PID points to foreign process | No signal, reap or privilege escalation | M11/M54/M60 |
| FT-04 | Cancelled work generated external effect before ack | No replay without M06 effect/idempotency proof | M02/M06 |
| FT-05 | Worker exits zero while output checksum or revision is wrong | No M06 success/master promotion | M06/M55 |
| FT-06 | Remote node emits duplicated final result from two concurrent attempts | No double acceptance or silent output overwrite | M02/M06 |
| FT-07 | Checkpoint bytes exist but model/runtime provenance differs | No unverified cross-host resume | M06/M14/M55 |
| FT-08 | Cloud spot instance vanishes without early warning | No presumed orderly shutdown or usable checkpoint | M11/M60 |
| FT-09 | Rebalance warning arrives but original instance remains running | No concurrent replacement task without fencing | M02/M06/M11 |
| FT-10 | New coordinator sees stale old resource lease after failover | No positive M09 grant without fresh owner-issued evidence | M09/#110 |
| FT-11 | Lowest cost route violates user residency or model license | No remote transfer or paid selection | M54/M59 |
| FT-12 | Quoted cloud price excludes egress, cold start or time overrun | No false cheaper-than-local claim or spending | M10/M12 |
| FT-13 | High-priority task demands immediate kill of interactive session | No priority override of OS/process or workstation protections | M11/M54/M60 |
| FT-14 | Two of three composite GPU members fail at different epochs | No aggregate grant or unsafe partial recovery | M09 H02/M12 S03 |
| FT-15 | Manual recovery operator lacks the relevant M54 principal authority | No foreign process recovery or private data access | M54/M60 |
| FT-16 | M10 advisory model ranks unverified failover host as suitable | No dispatch permission from score | M10/M12 |
| FT-17 | Telemetry claims success but M06 accepted artifact missing | No fabricated user-facing completion | M06/M56 |
| FT-18 | Remote transfer incomplete after leader loss | No final accepted output or unauthorized upload restart | M06/M55/M59 |
| FT-19 | S05 retry loops without verified max-attempt/deadline policy | No unbounded duplicate cost, process or data effects | M02/M06/M54 |
| FT-20 | Two coordinators each reclaim same capacity based on stale kill ack | No joint M09 state proof or overcommitted GPU | M09/M11 |

## 6. Unresolved owner questions, 26 OPEN/UNRATED

| ID | Future owner(s) | Specific question to resolve with source and proof |
| --- | --- | --- |
| M12-S05-U01 | M02/M06 | Which exact accepted work and operational attempt IDs can be resumed or retried without replaying external effects? |
| M12-S05-U02 | M06/M55 | What committed checkpoint and artifact lineage distinguishes safe resume from copying partial bytes? |
| M12-S05-U03 | M11/M60 | Who can attest that a worker really exited rather than merely losing connectivity? |
| M12-S05-U04 | M09/#110 | How does M09 prove that an interrupted request's capacity was actually reclaimed? |
| M12-S05-U05 | M09/M11 | Does an ACCEPTED_AWAITING_RESOURCE_RECONCILIATION acknowledgment prohibit positive capacity reclamation? |
| M12-S05-U06 | M11/M54/M60 | What independently authorized process identity and rights permit a future cancel/reap/signal? |
| M12-S05-U07 | M02/M06/M12 | Who decides the future retry budget, attempt revision and dedup semantics? |
| M12-S05-U08 | M02/M06/M12 | What effect classes are non-idempotent and must require explicit owner/operator adjudication? |
| M12-S05-U09 | M11/M56 | What evidence distinguishes missed heartbeat, local OS crash, remote network partition and node restart? |
| M12-S05-U10 | M09/M11/M12 | How can a new placement be fenced from stale grants, old worker epochs and duplicate supervisors? |
| M12-S05-U11 | M54/M60 | What trust revocation proof immediately blocks retry to a previously trusted node? |
| M12-S05-U12 | M12/M54 | Who can authorize manual versus automated failover and what is the approval evidence? |
| M12-S05-U13 | M12/M56 | What measurement/source qualifies observed MTTR, recovery success or failure rate? |
| M12-S05-U14 | M12/M10/M54 | What price source, budget owner, paid-cloud cap and user consent enable future spillover? |
| M12-S05-U15 | M12/M13/M56 | How are cold-start, staging time, network transfer and compute duration measured per candidate? |
| M12-S05-U16 | M12/M10/M56 | What empirical quality/latency/cost uncertainty may inform advice without becoming authorization? |
| M12-S05-U17 | M02/M06/M48 | Who decides partial-output quality and accepted master after interrupted multi-GPU work? |
| M12-S05-U18 | M12/M09 | What resource protection keeps user-interactive 8GB hardware responsive during preemption decisions? |
| M12-S05-U19 | M11/M60 | Which platform-specific graceful shutdown and timeout observations would be verified on Windows/Linux? |
| M12-S05-U20 | M09/M11 | What does preemption requested versus accepted versus fully reclaimed mean per owner contract? |
| M12-S05-U21 | M12/M54/M56 | Which incident/evidence telemetry can be exposed without leaking tenant/workflow credentials? |
| M12-S05-U22 | M12/M54/M58 | Who is permitted to publish or invoke any future recovery/preemption API and rate policy? |
| M12-S05-U23 | M12/M54/M60 | What security checks prevent unknown foreign PID or worker ownership from forced termination? |
| M12-S05-U24 | M12/M55/M59 | What checksum, rights and remote artifact/export guarantees are required after cloud interruption? |
| M12-S05-U25 | M12/M09/M11 | What evidence simultaneously qualifies a composite multi-device grant and worker controls after one GPU fails? |
| M12-S05-U26 | M12/M02/M06/M54 | What default future policy applies when any owner proof is missing, stale, conflicted or unsupported? |

## 7. Technology/freeze next gate, independent of S05 study

Once its own reviewed exact-head PR/protected exact-main both pass, S05 may be COMPLETE_FOR_REFERENCE_PLANNING_ONLY. That does NOT close issue #128's remaining technology discovery, final technology review, forward compatibility scan, owner-question adjudication, M12 versioned candidate, independent freeze-readiness audit or separate implementation admission. No existing H01–H04 HIGH is addressed by an M12 reference document. Issues #82/#110/#112 stay OPEN; no process/OS/remote/GPU recovery action or actual fault-injection test occurred.
