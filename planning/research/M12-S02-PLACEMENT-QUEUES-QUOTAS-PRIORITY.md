# M12 S02 — Placement, Queues, Quotas and Priority Scheduling

Status: PROPOSED_NON_EXECUTABLE_REFERENCE_RESEARCH | IRIS-WO-0023 | Issue #128 OPEN
Research base: `032dcda35df48d53012b3b32fdabb78de17c2b41`; tree `b83f0e8c1572fe2164baee606f0653116e1be2b5`. Baseline Governance #485 exact-main PASS 3979/3979.
This record compares published scheduling techniques with IRIS's existing frozen owner boundaries. **It does not select a scheduler, queue algorithm, numeric quota/priority, placement policy, transport, API, executable state machine or resource-admission port.**

## 1. Research question and source boundaries

M12's index calls for placement, queues, quotas and priority scheduling, but a discoverable S01 worker/capability advertisement is only a **candidate inventory record**. M02 accepts canonical ExecutionPlan/work and retains causality; M06 owns operational attempt/outcome; M09 v1.0 owns resource truth, claims/grants/leases and forbids treating sampled GPU availability as a grant; M10 v1.0 is recommendation-only, not scheduling authority; M11 v0.2 is a non-frozen, non-executable proposed supervisor/OS worker lifecycle. No M12 positive dispatch, placement or capacity reservation is admitted. Future M54 identity/security, M56 telemetry, M58 interfaces and M60 OS/deployment/rights are still pending individual contracts. The M09→M11 owner #110 has **no actual A/B/C topology selection**, its H01–H04 future-freeze HIGHs are OPEN, and cross-owner joint snapshot+lease evidence cannot be inferred.

### Proposed boundary map, not an interface

| Prospective stage | Possible candidate evidence | Exclusive owner/gate | Forbidden shortcut |
| --- | --- | --- | --- |
| Production intent | Exact M02 accepted plan and work/action/attempt association | M02 and M06 own their separate identities/outcomes | A queued job is not M02 acceptance or a new attempt |
| Candidate inventory | S01 provenance-bearing worker advertisements and compatibility descriptors | Future M12 registry, with M11/M54/M60 identity/OS verification | A registered GPU or heartbeat is not a live resource grant |
| Queue evaluation | Pending candidate, scope, admissibility questions, fairness/urgency inputs from owners | M12's future contract, subject to source-backed policy approval | Queue rank never authorizes M09 reserve or M11 start |
| Resource proof | Exact work/action/epoch/scope, all composite members and coherent fresh owner-issued grant if an extension is later admitted | M09, #110 H02; M11 reverse H01 and M54/M60 dependencies | `LeaseBook.active()`, synthetic snapshot and two independent RLocks are not such proof |
| Placement possibility | Potential candidate worker and reasons for rejection/unknown; not an execution command | Future M12 under M02/M09/M11/M54/M60 handoffs | An apparent positive score is not a dispatch permit |
| Actual worker dispatch | Separately verified process ownership/authorization and exact attempt provenance | Future M11/M54/M60; implementation NOT_ADMITTED | No shell/process launch, preempt/kill or cloud API in this session |

No new public error enum is defined. Where evidence is absent, stale, conflicting or owner-unsupported, S02 records an **open ambiguity**; its future implementation must preserve the owner contract's real distinctions instead of inventing positive decisions.

## 2. External technology discovery, factual reference only

The following sources describe existing systems; none is an authorized IRIS dependency, adopted behavior, implementation plan or proof of equivalent IRIS safety.

| Reference | Verifiable design in its official documentation | Candidate insight for later owner consideration | Unproven/unsafe analogy to IRIS |
| --- | --- | --- | --- |
| Kubernetes Scheduling Framework | Plugin extension stages include queue sort, filter, score, reserve/unreserve and permit/bind; scheduling and binding are separate phases | **Conceptual separation** between prioritization, feasibility, intermediate reservations and final actuation | Kubernetes `Reserve` is not an M09 lease; `Permit` is not M54 permission nor M11 ownership |
| Kueue ClusterQueue | Explicit resource-flavor quotas, queues/cohorts, borrowing and policy-configured preemption/fair sharing | Investigate quota/fairness isolation and proof of limits, including heterogeneous GPU resource groups | Kueue nominal quota is not real current GPU headroom; cannot copy preemption to control M09/M11 |
| Ray Placement Groups | Placement groups atomically reserve bundles across nodes and support pack/spread strategies for gang tasks | Identify all-or-nothing **proof obligation** for future M12 S03 composite tasks | Ray's real reservation does not solve M09 H02 without an owner-approved *joint* M09 snapshot+lease cut |
| FIFO/priority, aging, weighted fair queue and bounded backfill | These are candidate queue policy families to contrast, not source-backed choices already implemented in IRIS | Structure starvation, priority inversion, throughput and user-session coexistence questions | No default priority numbers, emergency override, quantum, backfill permissions or preemption semantics from reference techniques |

Official primary-source references (reviewed 2026-09-27):
- Kubernetes Scheduling Framework: https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/
- Kubernetes scheduler two-stage explanation: https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/
- Kueue ClusterQueue: https://kueue.sigs.k8s.io/docs/concepts/cluster_queue/
- Ray Placement Groups: https://docs.ray.io/en/latest/ray-core/scheduling/placement-group.html

## 3. Six reference-only queue/scheduling policy candidates

| Candidate | Why study it | Counterexample to test later | Status |
| --- | --- | --- | --- |
| Q-A: Simple FIFO within one owner scope | Easy-to-audit order, potential predictability for one workstation | Head-of-line blocking and enormous job starvation | CONSIDERED_NOT_SELECTED |
| Q-B: Explicit owner-approved priority with aging | Could balance urgent work with finite waiting, if M02/source priority exists | Invalid or user-invented priority, permanently starved low priority | CONSIDERED_NOT_SELECTED |
| Q-C: Weighted fair sharing across project/tenant scopes | Future multi-project coexistence, quota attribution | Borrowed quota becomes ambiguous during partial network failure, leaked private tenant weights | CONSIDERED_NOT_SELECTED |
| Q-D: Capacity-aware bounded backfill | Potential idle periods utilization without delaying protected jobs | Predicted duration/VRAM is wrong, preemption/cancellation impossible without M11 proof | CONSIDERED_NOT_SELECTED |
| Q-E: Hard quota/flavor isolation | Potential local-workstation protection and future heterogeneous groups | Self-reported GPU count mistaken for verified M09 lease, unbounded cross-project borrow | CONSIDERED_NOT_SELECTED |
| Q-F: Gang/co-placement of composite tasks | Explore multi-GPU all-or-nothing requests and locality requirements | One composite member stale/revoked or unknown, split placement incorrectly consumes partial capacity | CONSIDERED_NOT_SELECTED; detailed proof in S03 |

None of these is a positive placement algorithm in IRIS. A future owner may combine or reject them after M09/M11 authority and actual performance/safety evidence; this session merely defines questions and counterexamples.

## 4. Proposed design separations for future reviews

**Queue presence vs admission:** a future pending entry would describe provenance and owner-issued M02 work association if present, not manufacture an accepted ExecutionPlan, M06 attempt or executable capability. Whether a queue item is durable, cancellable, retryable or uniquely identified remains OPEN.

**Quota vs live resource truth:** a declared budget or per-project limit is a scheduler policy candidate. M09 alone issues real lease/grant state. Global quota math, workstation headroom and cross-host aggregate evidence must be documented independently; a queue's arithmetic cannot substitute for a coherent M09 grant across all members.

**Fairness vs privileged execution:** fairness and priority never override M54/M60 authorization or an M11 process right. A user-interactive workload, overnight batch and emergency preemption cannot be selected by this research as default priority ordering; workstation coexistence remains a separate owner question.

**Feasibility vs actuation:** even if a candidate worker matches a task type, positive placement remains unavailable until exact M02 plan and M06 attempt association, owner-issued M09 joint resource proof, M11 worker/OS ownership, M54 principal and M60 platform evidence all exist and are freshly rechecked. The one-to-one or many-to-one binding remains unresolved.

**Failure and requeue:** node loss, stale heartbeat, cancellation, partition and superseded queue epoch cannot imply process death, released capacity, safe retry, deduplicated external effect or successful output. M02/M06/M09/M11/M12 owners must separately specify safe behavior; this research issues no queue mutation/retry or network request.

## 5. Negative/ambiguity future test matrix

All **14 SQ tests below are SPECIFIED_NOT_EXECUTED**, not CI-executed or live integration evidence.

| ID | Trigger | Fail-closed behavior that future owners must prove | Dependency |
| --- | --- | --- | --- |
| SQ-01 | High queue priority but M02 plan/work not accepted or scope mismatch | No creation of accepted plan/attempt or process start | M02, M06 |
| SQ-02 | Worker advertises free VRAM but no M09 request-scoped owner-issued proof | Do not promote quota match or score into grant/dispatch | M09/#110 |
| SQ-03 | M09 `active()` entry is PREEMPTION_REQUESTED or REVOCATION_REQUESTED | No assumed unqualified active grant; preserve revocation state | M09, M11 |
| SQ-04 | Two-member GPU request, one member's proof stale or missing | All-or-nothing non-admission; no partial reservation claim | M09 H02, M12 S03 |
| SQ-05 | Competing projects each borrow the same unverified quota | No double-spend claim; policy math cannot mint M09 lease | M09, M12 |
| SQ-06 | Aging boosts task above M54 authorization or workstation interactive safeguards | No priority privilege escalation, bypass or process action | M54, M60, M11 |
| SQ-07 | Deadline near but M11 liveness, OS ownership or platform capability UNKNOWN | No forced worker start/kill/reap; urgency is not OS evidence | M11 H01, M60 |
| SQ-08 | Owner cancels task during score/placement calculation | No stale cached result promoted; future exact identity/epoch recheck required | M02, M06, M12 |
| SQ-09 | Queue mirror stale after supervisor failure or remote partition | No unverified duplicate attempt or relaunch | M02, M06, M11, M12 |
| SQ-10 | Local node appears cheaper than remote with unsupported adapter/version | Unsupported compatibility cannot become executable route | M12, M14, M17 |
| SQ-11 | Kueue/Ray-style reserve/permit simulated in a proposal without actual M09 port | Comparison remains documentary, no actual reserve/lease/dispatch | M09/#110, M12 |
| SQ-12 | Future preemption chooses a foreign or PID-reused process | No M11 control without M54/M60 process identity and rights | M11, M54, M60 |
| SQ-13 | Queue telemetry exposes private project priorities/tenant node data | No publication without M54/M58 data policy | M54, M56, M58 |
| SQ-14 | Backfill assumes runtime/VRAM estimate is certain, planned task overstays | No unverified forced reclaim/retry or external-effect duplication | M06, M09, M11, M12 |

These are S02-local candidates; none are satisfied by the 3,979-test repository Governance suite or by M12 S01's twelve future WR cases. Future ownership and implementation must define actual observed/tested outcomes before freeze.

## 6. S02 owner decision register: 20 distinct questions

Every item is **OPEN/UNRATED_PENDING_OWNER**, not an adopted interface or a blocker discharged by planning-only CI.

| ID | Owner(s) | Explicit unresolved question |
| --- | --- | --- |
| M12-S02-U01 | M02/M12 | What canonical accepted M02 work/plan reference permits queue consideration without manufacturing M02 state? |
| M12-S02-U02 | M06/M11/M12 | What exact attempt and supervisor cardinality prevents duplicate external effects across requeue? |
| M12-S02-U03 | M12/M54 | What tenant/project/user scope may a queue own, and who verifies it? |
| M12-S02-U04 | M12/M02 | Who supplies allowable priority policy evidence and can it vary by project? |
| M12-S02-U05 | M12/M54/M60 | Is interactive workstation co-existence a mandatory preemption/hold boundary? |
| M12-S02-U06 | M12/M56 | What verified timestamps/evidence allow aging or starvation metrics? |
| M12-S02-U07 | M12/M09 | Are hard quotas policy limits or M09 grants, and how are they separately versioned? |
| M12-S02-U08 | M12/M09/#110 | What coherent per-request M09 lease+snapshot recheck is needed before any positive placement? |
| M12-S02-U09 | M12/M09 | How are unknown/stale quota or headroom estimates represented without positive claims? |
| M12-S02-U10 | M12/M09/M11 | Who may request cooperative preemption, and what proof prohibits assumed capacity reclaimed? |
| M12-S02-U11 | M12/M11/M60 | What exact owner proof authorizes worker lifecycle after a placement decision? |
| M12-S02-U12 | M12/M54 | What are fair-share weights, principal authorization and audit requirements? |
| M12-S02-U13 | M12/M06 | Can expected duration/VRAM be used for backfill, and what uncertainty bounds are required? |
| M12-S02-U14 | M12/M09/M11 | What atomic/composite grant semantics are necessary for gang scheduling? |
| M12-S02-U15 | M12/M54/M58 | Which queue descriptors and priority values may be published outside local trust boundary? |
| M12-S02-U16 | M12/M56 | What observation/event record distinguishes enqueue, eligible, selected and actually dispatched? |
| M12-S02-U17 | M12/M02/M06 | Who decides cancellation/retry/idempotency when a queued job's plan or attempt changes? |
| M12-S02-U18 | M12/M54/M60 | Can any remote quota borrow occur before node/principal/OS security contracts exist? |
| M12-S02-U19 | M12/M11/M09 | Who revalidates leases and process rights at the TOCTOU edge between ranking and use? |
| M12-S02-U20 | M12/M10 | How does advisory optimization input stay separate from admitted scheduling and proof? |

## 7. Dependency and next-session ledger

| Future session | S02 deliverable/question carried forward | Gate |
| --- | --- | --- |
| M12 S03 | Composite-member all-or-nothing gang placement, heterogeneous GPU locality and simultaneous proof | M09 H02 + M11 process capability unresolved |
| M12 S04 | Multi-node queue partitions, remote admission, quota borrow, identity/privacy boundaries | M54/M58/M60 owner contracts pending |
| M12 S05 | Failover/requeue/preemption/starvation safeguards, priority inversion, cost/quality objectives | M02/M06 idempotency and M09/M11 liveness/reconciliation unproven |
| M12 FTR/FCS | Re-evaluate official Kubernetes/Kueue/Ray patterns and all M13–M60 owner dependencies | No tooling/policy adoption at S02 |

S02 can be **COMPLETE_FOR_REFERENCE_PLANNING_ONLY** after its own reviewed PR + exact-main CI, with all twenty owner questions OPEN/UNRATED, fourteen SQ tests SPECIFIED_NOT_EXECUTED and six approaches NOT_SELECTED. This does not freeze an M12 contract or execute one scheduling action. #82/#110/#112 remain OPEN, #128 remains OPEN through remaining M12 sessions.
