# M12 — Compute Orchestration: Local, Multi-GPU, LAN, Remote & Cloud

Status: S01_PROPOSED_FOR_MODULE_PLANNING_ONLY | NOT_FROZEN | IMPLEMENTATION_NOT_ADMITTED
Planning Issue: #128 | Planning Work Order: IRIS-WO-0022 | exact base `e3fc858d3c92a8a3eba3c7c6119fc490c4098129`
Canonical scope: `planning/MASTER-MODULE-INDEX.md`; no individual M12 owner contract, placement API or runtime has been adopted.

## Mission and disciplined boundaries

M12 planning investigates how a future orchestration owner would locate possible compute workers, consider placement/queue/cost constraints, and coordinate heterogeneous or remote execution **only after** applicable owner-issued proofs exist. It cannot create M02 work, attest M06 outcomes, infer M09 resources/grants/leases, turn M10 advice into dispatch, take over M11's OS process/worker control, define M54 security, publish network APIs on behalf of M58, or assume M60 OS/deployment rights. No worker registration, heartbeat, network discovery, allocation, queue, process, hardware probe, cloud connection, authentication, placement or dispatch is performed by this module plan.

## Five planned sessions

| Session | Bounded exploration | Status |
| --- | --- | --- |
| S01 | Worker registry and capability advertisements; advertisement vs verified truth, identity, permission and current grant | PROPOSED, pending this PR's exact-head/audit/merge/exact-main |
| S02 | Placement, queues, quotas and priority scheduling; never infer an M09 grant or M11 process permission | NOT_STARTED |
| S03 | Multi-GPU/heterogeneous execution, exact composite-member requirements and evidence, no assumed joint M09 snapshot+lease proof | NOT_STARTED |
| S04 | LAN/remote/cloud spillover and federated nodes; trust, isolation and network endpoints pending M54/M58/M60 | NOT_STARTED |
| S05 | Failover, preemption, cost/quality placement and trust; no autonomous re-dispatch/retry without M02/M06/M09/M11 authorization | NOT_STARTED |

## Existing source boundaries as of admission

| Owner | Current source status | M12 dependency |
| --- | --- | --- |
| M02 | Frozen contract v1.0 | Semantic ExecutionPlan, accepted work identity, causality and production acceptance remain M02-only. |
| M06 | Frozen contract v1.0 | Operational attempt, artifact materialization, revision and outcome remain M06-only. |
| M09 | Frozen/implemented v1.0, 83/83 surfaces, 15/15 components, 514/514 invariant proofs | Resource truth and leases belong exclusively to M09; M09→M11 read-only evidence extension C01 is UNADOPTED, H01–H04 still OPEN HIGH_FOR_FUTURE_FREEZE. No M12 positive placement grant inferred. |
| M10 | Frozen advisory v1.0; implementation NOT_ADMITTED | Optimization suggestions do not dispatch workers, place jobs, reserve resources or create lease facts. |
| M11 | Five sessions and non-executable candidate v0.2, NOT_FROZEN; Issue #82 OPEN | OS process/supervisor and worker lifecycle owned by future M11; neither M12 nor M11 implementation admitted. |
| M12 | Index-level five-session scope only prior to this increment | Initial research may name questions and nonbinding alternatives; no owner contract or public schema exists. |
| M13–M60 | Individual owner contracts pending/index-only except existing frozen owners noted above | M54 authenticates/authorizes; M56 telemetry; M58 publication/API; M60 OS capabilities/deployment. Status PENDING_OWNER_CONTRACT / UNRATED, not invented as adopted interfaces. |

## Required cross-module gates

The positive M09→M11 topology A/B/C, coherent joint snapshot+lease and reverse verified M11 liveness owner proof are **NOT SELECTED** pending the actual M09 owner answer [#110](https://github.com/KayzenRoot/iris/issues/110). A worker's presence in any registry or a capability announcement is NEVER an M09 resource grant, an M54 authentication credential, an M11 process ownership proof, or an M02 dispatch command. Registry absence or staleness cannot silently trigger remote retries or recovery. Keep all executable paths DISABLED until distinct owner contracts, admission Work Orders, platform and negative tests exist.

## Completion and STOP

S01 research source: `planning/research/M12-S01-WORKER-REGISTRY-AND-CAPABILITY-ADVERTISEMENTS.md`. Each subsequent session requires a separately scoped Work Order/review under Issue #128. Technology discovery/FTR, forward compatibility scan, versioned M12 owner candidate, independent freeze-readiness audit and **separate future implementation** remain pending. Even after S01 documentation exact-main PASS, M12 remains NOT_FROZEN / IMPLEMENTATION_NOT_ADMITTED, M09/M11 owner blockers stay OPEN and no hardware/network/process behavior has been tested.
