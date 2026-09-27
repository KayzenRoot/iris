# M12 — Compute Orchestration: Local, Multi-GPU, LAN, Remote & Cloud

Status: S01_S02_S03_COMPLETE_FOR_REFERENCE_PLANNING_S04_PROPOSED | NOT_FROZEN | IMPLEMENTATION_NOT_ADMITTED
Planning Issue: #128 | S01 Work Order: IRIS-WO-0022, merged exact-main `032dcda35df48d53012b3b32fdabb78de17c2b41` (#485 PASS) | S02 Work Order: IRIS-WO-0023, merged exact-main `7ab6743ce2d88d596a6da73abbcfc6456d7762e6` (#487 PASS) | S03 completed: IRIS-WO-0024, exact-main `d94f19de4a7b5ed8e248ea41239bc53df90a58b1` (#489 PASS) | S04 proposed: IRIS-WO-0025, base `d94f19de4a7b5ed8e248ea41239bc53df90a58b1`
Canonical scope: `planning/MASTER-MODULE-INDEX.md`; no individual M12 owner contract, placement API or runtime has been adopted.

## Mission and disciplined boundaries

M12 planning investigates how a future orchestration owner would locate possible compute workers, consider placement/queue/cost constraints, and coordinate heterogeneous or remote execution **only after** applicable owner-issued proofs exist. It cannot create M02 work, attest M06 outcomes, infer M09 resources/grants/leases, turn M10 advice into dispatch, take over M11's OS process/worker control, define M54 security, publish network APIs on behalf of M58, or assume M60 OS/deployment rights. No worker registration, heartbeat, network discovery, allocation, queue, process, hardware probe, cloud connection, authentication, placement or dispatch is performed by this module plan.

## Five planned sessions

| Session | Bounded exploration | Status |
| --- | --- | --- |
| S01 | Worker registry and capability advertisements; advertisement vs verified truth, identity, permission and current grant | COMPLETE_FOR_REFERENCE_PLANNING_ONLY; PR #129 exact-head #484 / exact-main #485 PASS 3979/3979, 18 OPEN/UNRATED owner questions and 12 future NOT_EXECUTED oracles |
| S02 | Placement, queues, quotas and priority scheduling; six unselected strategies, 20 open questions, 14 future tests | COMPLETE_FOR_REFERENCE_PLANNING_ONLY; PR #130 exact-head #486 / exact-main #487 PASS 3979/3979 |
| S03 | Multi-GPU/heterogeneous execution reference study; five unselected shapes, 22 open owner questions, 16 future MG scenarios | COMPLETE_FOR_REFERENCE_PLANNING_ONLY; PR #131 exact-head #488 and exact-main #489 PASS 3979/3979 |
| S04 | LAN/remote/cloud spillover and federated nodes; candidate topologies, identity, consent, partitions, cost and security boundaries | PROPOSED_NON_EXECUTABLE_REFERENCE_RESEARCH; IRIS-WO-0025 |
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

## S01 completion and S02 source admission

S01 source research completed for **reference exploration only** through PR #129, reviewed head `f9b2dcb2dab13f43b409fb1ba3ca68ea85573e50` (40/40 exact Git sources, 12/12 paths), Governance #484 run 36324795399/job 108635360544 PASS 3979/3979, protected squash main `032dcda35df48d53012b3b32fdabb78de17c2b41` (tree `b83f0e8c1572fe2164baee606f0653116e1be2b5`) and exact-main Governance #485 run 36324884488/job 108635619085 PASS 3979/3979. Issue #128 remains OPEN. S02 reference research is proposed as separately bounded IRIS-WO-0023; it must not be marked complete until its own final-head review, guarded merge and exact-main Governance pass. S03–S05, technology selection, future M12 contract/freeze and implementation remain pending.

## S02 completion and S03 source admission

S02 reference research completed through audited PR #130, exact-head Governance #486 run 36325232475/job 108636612763 PASS 3979/3979, protected squash `7ab6743ce2d88d596a6da73abbcfc6456d7762e6` / tree `a5bcc17a93d228c3f66d5c51b755fbe11d85281e`, and exact-main Governance #487 run 36325338819/job 108636913754 PASS 3979/3979. All six S02 options remain NOT_SELECTED, twenty S02 owner questions OPEN/UNRATED, fourteen SQ scenarios SPECIFIED_NOT_EXECUTED; no scheduler selected, installed or tested. S03 source study is a separate proposal IRIS-WO-0024, pending own exact-head CI/review/protected merge/exact-main. S04–S05, FTR/FCS, owner-contract candidate, independent freeze audit and all M12 runtime remain pending.

## S03 completion and S04 research admission

S03 audited PR #131 head `0026b1fb85932b42d075493d953f0bbc5c1b023d`, Governance #488 run 36325625861/job 108637727139 PASS 3979/3979, protected squash `d94f19de4a7b5ed8e248ea41239bc53df90a58b1` (tree `963d02cf2083e44f1f78a651bc383e8fc7386eed`) and exact-main Governance #489 run 36325721431/job 108637995310 PASS 3979/3979. Five S03 alternatives NOT_SELECTED, 22 questions OPEN/UNRATED and 16 future MG scenarios NOT_EXECUTED. S04 is newly proposed in a separate Work Order, not frozen or executable; S05, FTR/FCS and later owner contract/implementation remain pending.

## Completion and STOP

S01 research source: `planning/research/M12-S01-WORKER-REGISTRY-AND-CAPABILITY-ADVERTISEMENTS.md`. Each subsequent session requires a separately scoped Work Order/review under Issue #128. Technology discovery/FTR, forward compatibility scan, versioned M12 owner candidate, independent freeze-readiness audit and **separate future implementation** remain pending. After S01–S03 exact-main PASS while S04 is proposed, M12 remains NOT_FROZEN / IMPLEMENTATION_NOT_ADMITTED, M09/M11 owner blockers stay OPEN and no hardware/network/process behavior has been tested.
