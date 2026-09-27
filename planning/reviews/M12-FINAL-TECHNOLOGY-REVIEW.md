# M12 Final Technology Review: five-session reference-only consolidation

Status: PROPOSED_FOR_SOURCE_REVIEW_ONLY | Issue #128 | IRIS-WO-0027 | 2026-09-27
Exact Git base `a69830dd963e0800d8f1e294254b97cc57cd5d60`, tree `02820f866a1acc662e9fec8aef162f6a7da59330`. Prior M12 S05 PR #133 head Governance #492 and exact-main #493 both PASS 3979/3979.
**Scope:** S01 worker inventory, S02 placement/quotas, S03 heterogeneous GPUs, S04 local/LAN/cloud federation, S05 failover/preemption/cost/trust. External official docs were consulted on 2026-09-27 (pages may be rolling). Nothing here selects an implementation, public API, provider dependency or privileged default.

## Review vocabulary

`ACCEPT_REFERENCE` means source-supported technical behavior can remain in the M12 planning evidence set but **does not** admit or recommend a technology for the Íris runtime. `DEFER_OWNER_CONTRACT` means a candidate needs exact source-based owner approvals; no protocol or technology is selected. `REJECT_AS_CURRENT_AUTHORITY` rejects incorrectly treating an external framework or research note as an IRIS trust/resource/process authority. These are documentary dispositions, not evaluations of political actors, runtime benchmark rankings or freeze verdicts.

## Authority and current session disposition

S01–S05 are **COMPLETE_FOR_REFERENCE_PLANNING_ONLY** after their individually gated PRs #129–#133 and exact-main Governances #485/#487/#489/#491/#493; #133 exact-main is `a69830dd963e0800d8f1e294254b97cc57cd5d60`. Historical first-line `PROPOSED` statuses in each research source are admission states at their own exact study bases. Current protected checkpoint and successful exact-main receipts outrank those historical headings; do not rewrite all archival inputs into fresh authority.

| Session | Research outcome | Not-adopted items | Owner questions still OPEN/UNRATED | Future negative scenarios, all NOT_EXECUTED |
| --- | --- | --- | ---: | ---: |
| S01 | Worker inventory and provenance/trust layers | 5 discovery options | 18 | 12 WR |
| S02 | Queue, fairness and capacity policy separation | 6 algorithm candidates | 20 | 14 SQ |
| S03 | Composite resource and GPU-topology questions | 5 multi-GPU shapes | 22 | 16 MG |
| S04 | Remote identity, consent, split-brain and spend | 6 federation approaches | 24 | 18 FN |
| S05 | Failover, retry idempotency, resource release and cost/trust | 6 recovery options | 26 | 20 FT |
| TOTAL | Reference planning only | 28 unselected research options across sessions | 110 distinct session questions, OPEN/UNRATED | 80 future tests, SPECIFIED_NOT_EXECUTED |

The counts are inventory counts, not coverage percentages or executed tests. M12 individual owner contract remains unavailable, M09 #110 owner topology A/B/C NONE_SELECTED, H01–H04 OPEN HIGH_FOR_FUTURE_FREEZE, M11 v0.2 NOT_FROZEN and 86 M11 questions OPEN/UNRATED, implementations M10/M11/M12 NOT_ADMITTED.

## Technology reference disposition register (16 separately audited records)

| ID | Session | Technology/pattern | Official/IRIS source | Disposition | Supported lesson and strict anti-inference | Owner gate |
| --- | --- | --- | --- | --- | --- | --- |
| FTR-01 | S01 | Local static/manual inventory | Internal S01 source | ACCEPT_REFERENCE | A limited source of candidate discovery, never authentication, current capacity or a worker grant. | M11/M12/M54/M60 local identity and freshness owner policy |
| FTR-02 | S01/S04 | Authenticated distributed registry | Internal S01/S04 source and Ray cluster/security docs | DEFER_OWNER_CONTRACT | Network availability can extend inventory, but trust, revocation, tenant isolation, endpoint ACLs and federation remain unapproved. | M54/M58/M60 identity, trust, export and endpoint contract |
| FTR-03 | S02 | Kubernetes Scheduling Framework | https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/ | ACCEPT_REFERENCE | QueueSort, Filter, Score, Reserve, Permit/Bind are distinct extension phases; they are NOT M09 grant, M11 process right or adopted IRIS scheduler. | M02/M06/M09/M11/M12/M54 exact identity, grant and actuation proof |
| FTR-04 | S02 | Kueue ClusterQueue | https://kueue.sigs.k8s.io/docs/concepts/cluster_queue/ | ACCEPT_REFERENCE | Resource flavor quota, cohort borrowing and fair sharing provide policy comparators, not real free VRAM nor cross-tenant authorization. | M12 future quota/priority owner and M09 actual capacity |
| FTR-05 | S02/S03 | Ray Placement Groups | https://docs.ray.io/en/latest/ray-core/scheduling/placement-group.html | ACCEPT_REFERENCE | Atomic bundled reservation in Ray illustrates all-or-nothing group question; Ray's own proof cannot discharge M09 H02. | M09 owner-issued coherent joint snapshot+lease, M11 ownership |
| FTR-06 | S03 | NVIDIA CUDA multiple-GPU/P2P | https://docs.nvidia.com/cuda/cuda-programming-guide/03-advanced/multi-gpu-systems.html | ACCEPT_REFERENCE | Multi-device contexts and peer-transfer capability depend on real topology/device support; VRAM cannot be summed into contiguous memory by advertising GPUs. | M07/M09/M12/M14/M17/M26/M60 hardware/model proof and actual tests |
| FTR-07 | S03 | Kubernetes Dynamic Resource Allocation | https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/ | DEFER_OWNER_CONTRACT | Device descriptors/claim-oriented scheduling are conceptual; no mapping to M09 resource truth or M60 OS permission is available. | M09/M12/M54/M60 exact typed claim and endpoint owners |
| FTR-08 | S03 | PyTorch DistributedDataParallel | https://docs.pytorch.org/docs/stable/generated/torch.nn.parallel.DistributedDataParallel.html | ACCEPT_REFERENCE | Per-process multi-accelerator training is a qualified workload example; this does not assert image/video/DCC model splitting or device support. | M14/M17/M19/M26 real model/provider qualification |
| FTR-09 | S04 | Ray clusters and security | https://docs.ray.io/en/latest/cluster/key-concepts.html ; https://docs.ray.io/en/latest/ray-security/index.html | ACCEPT_REFERENCE | Cluster head/worker concepts and Ray's trusted-boundary requirement demonstrate separation of inventory from remotely trusted control. | M54/M58/M60 and media/data consent owner contracts |
| FTR-10 | S04/S05 | KubeRay GCS recovery | https://docs.ray.io/en/latest/cluster/kubernetes/user-guides/kuberay-gcs-ft.html | DEFER_OWNER_CONTRACT | Recovery of control-plane metadata does not prove foreign process stopped, capacity returned, or external effects deduplicated. | M02/M06/M09/M11 verified reconciliation/epoch and idempotency |
| FTR-11 | S04/S05 | EC2 Spot operational interruption guidance | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-best-practices.html | ACCEPT_REFERENCE | Interruptible instances need fault-tolerant workload design; hints cannot prove timely warning, valid checkpoint or grant reclamation. | M02/M06/M09/M11/M54 budget/export/recovery owners |
| FTR-12 | S05 | Ray task fault-tolerance/retries | https://docs.ray.io/en/latest/ray-core/fault_tolerance/tasks.html | DEFER_OWNER_CONTRACT | Task restart support is not permission for IRIS's externally visible side-effect replay or artifact acceptance. | M02/M06 exact idempotency/attempt/version evidence |
| FTR-13 | S05 | Kueue preemption | https://kueue.sigs.k8s.io/docs/concepts/preemption/ | ACCEPT_REFERENCE | Configurable priority/preemption policy can inform future questions; never treats preemption requested or accepted as reclaimed M09 capacity. | M09/M11/M54 actual grant/OS rights/reconciliation |
| FTR-14 | S05 | Kubernetes pod disruptions | https://kubernetes.io/docs/concepts/workloads/pods/disruptions/ | ACCEPT_REFERENCE | Voluntary/involuntary disruptions differ; disruption-budget-style constraints cannot prove arbitrary process survives or returns resources. | M11/M60 OS platform proof and M02/M06 retries |
| FTR-15 | ALL | Direct adoption of any framework as M12 dispatch/lease authority | Cross-session owner boundary comparison | REJECT_AS_CURRENT_AUTHORITY | Kubernetes, Ray and Kueue do not constitute already admitted IRIS owner APIs, signed M09 joint proofs, verified M11 process rights or M54 permissions. | Explicit new owner contracts, independent integration tests and gated implementation WO |
| FTR-16 | ALL | Proprietary typed source/evidence projection only as a future research target | All five IRIS S01–S05 research files | DEFER_OWNER_CONTRACT | Potential provider-neutral separation without importing external scheduler, but serialization/transport/token/lease schema still unselected. | M12 owner candidate, M09 #110, M11 freeze and M54/M58/M60 contract review |

## Architecture invariants emerging from five studies, not newly frozen schemas

1. Inventory and identity are distinct from admission: a self-announcement or heartbeat never proves M54 principal authorization, current M09 resource truth or verified M11 OS process ownership.
2. Candidate scoring, priority, nominal quota and an optimization recommendation are not dispatch, accepted M02 work, M06 attempt state, or owner-issued M09 grants.
3. For composite GPUs, future exact request-scoped, member-complete **coherent M09 snapshot+lease** and per-device tested compatibility are prerequisites before any positive grant or shared-memory claim. Independent M09 class-local locks/read methods cannot supply that cut.
4. A remote trust domain needs future M54/M58/M60 endpoint authorization plus data rights/residency and artifact integrity under their actual owner contracts; no source currently authorizes network peers, media export, cloud spending or secrets.
5. Lost heartbeat, warning of cloud interruption, accepted cancellation or process exit cannot independently establish M06 accepted outcome, safe retry, OS process death or released M09 capacity. No owner is permitted to mint a proof belonging to another owner.
6. Canonical 8 GB-class local production routes must remain honest about actual local model/adapter/device support and workload-specific VRAM; two physical 8 GB cards never imply one contiguous 16 GB device.

## Review-to-contract blockers

The review cannot resolve M09↔M11 H01 reverse owner-liveness authentication, H02 jointly coherent owner-issued snapshot+lease, H03/H04 other-owner/identity/authorization gates; all remain OPEN HIGH_FOR_FUTURE_FREEZE. The M09 owner must explicitly select A/B/C or DEFER on Issue #110. M11 #82 and dependent M09 extension #112 remain OPEN. M54/M58/M60 and M13–M60 individual owner contracts are unavailable or index-level; the FCS companion enumerates all later M12 relationships without fabricating APIs or owner acceptances.

**Technology-review output only:** Reference families were source-checked and individually dispositioned as evidence; no IRIS scheduler, library, transport, GPU topology, cloud provider, budget or failover policy is selected. Progress to source-level FCS is permitted in this same bounded WO; a versioned M12 contract/freeze and any implementation require further separate authority, explicit owner proofs and actual runtime tests. Issue #128 remains OPEN. No new OS/network/cloud/GPU trial took place in this review.
