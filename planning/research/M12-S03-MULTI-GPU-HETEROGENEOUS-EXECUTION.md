# M12 S03 — Multi-GPU and Heterogeneous Execution

Status: PROPOSED_SOURCE_BACKED_REFERENCE_RESEARCH_ONLY | Issue #128 / IRIS-WO-0024
Exact Git study base `7ab6743ce2d88d596a6da73abbcfc6456d7762e6`, tree `a5bcc17a93d228c3f66d5c51b755fbe11d85281e`. Governance #487 exact-main PASS 3979/3979.
No topology, CUDA/OS API, partition rule, resource amount, placement/worker protocol or M09→M11 A/B/C option is adopted.

## 1. The unsolved multi-device authority problem

The existing M12 master index assigns S03 multi-GPU and heterogeneous execution to M12 as **prospective compute orchestration**, not as an owner-issued runtime contract. S01 advertisements cannot authenticate device count or resource headroom; S02 queue priorities and policy quotas cannot mint leases. Frozen M09 v1.0 governs real resources/grants/leases but its candidate M09→M11 handoff is UNADOPTED and M09 H02 lacks a coherent per-request **joint snapshot+lease cut for all composite members**. `ResourceTwin` and `LeaseBook` have independent locks; two sequential reads do not prove one atomic cut. H01 reverse M11 liveness is unverified, H03/H04 other-owner and identity gates unresolved. M11 v0.2 process/OS candidate NOT_FROZEN and implementations M10/M11/M12 NOT_ADMITTED.

**Non-equivalences:** two visible GPUs do not mean shared VRAM; two individually fresh snapshots do not prove simultaneous grant validity; a borrowed quota, cached recommendation, P2P capability advertisement or a scheduler gang primitive from another framework cannot bind an M09 owner grant. No `GPU_COUNT >= 2` or combined VRAM arithmetic can permit process execution. Keep 8 GB-class hardware an independently truthful production target, not a promise of magic VRAM aggregation.

## 2. Published primary-source technology comparison (reference only)

| Primary technical source | Precisely documented capability | Question for future IRIS owner | False conclusion forbidden |
| --- | --- | --- | --- |
| NVIDIA CUDA Programming Guide multi-GPU | Multiple host threads/processes may manage separate GPU contexts; device peer transfers/access depend on topology and tested peer capabilities | Are future M11 processes/OS rights and per-device topology supported for an exact task? | CUDA API availability does not imply working P2P for any given two devices or joint M09 capacity |
| Kubernetes DRA | DeviceClass/ResourceClaim/ResourceSlice distinguish available device descriptions from claim-based allocation | What owner-defined device descriptors and claim handoff would later M12 need? | A Kubernetes DRA ResourceClaim is **not** an existing M09 port or proof of M09 H02 |
| Ray Placement Groups | Bundled resources and pack/spread scheduling, group atomic reservation within Ray | Which same-host/all-member consistency obligation must later M09/M12 prove? | Ray's own cluster reservation does not authorize IRIS workers/leases |
| PyTorch DistributedDataParallel | For typical single-host N-GPU training the docs describe one worker process per accelerator with separate process-group initialization | Which workloads/models actually support independently owned workers and collective operation? | DDP does not mean Blender, ComfyUI or every diffusion model supports sharding or mixed hardware |

Reviewed published official documentation:
- https://docs.nvidia.com/cuda/cuda-programming-guide/03-advanced/multi-gpu-systems.html
- https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/
- https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/dra-api/
- https://docs.ray.io/en/latest/ray-core/scheduling/placement-group.html
- https://docs.pytorch.org/docs/main/generated/torch.nn.parallel.DistributedDataParallel.html

No NVIDIA API called, Kubernetes installed, Ray/PyTorch job launched or local GPU interrogated here.

## 3. Five explicit unselected execution shapes

| ID | Candidate shape | Unresolved authority and safety cost | Status |
| --- | --- | --- | --- |
| S03-A | Independent single-GPU jobs spread across separately qualified devices | No implication that one task's model or memory spans GPUs; requires individual owner grant/worker proofs | CONSIDERED_NOT_SELECTED |
| S03-B | One host process managing several GPUs using explicit CUDA contexts | May require verified device/driver/topology and peer behavior; M11 OS rights, M09 joint grant unproven | CONSIDERED_NOT_SELECTED |
| S03-C | One independently owned worker process per GPU, explicit interprocess data flow | Future M11 process ownership and M54/M60 IPC rights; OS PID alone insufficient | CONSIDERED_NOT_SELECTED |
| S03-D | Model/pipeline/tensor/data partitioning or per-stage offload across devices | Requires validated model/provider capability, transfer budget and correct quality/lineage per owners | CONSIDERED_NOT_SELECTED |
| S03-E | Composite/gang all-or-nothing same-host group, with future federated variant | Every member must share a coherent M09 snapshot+lease proof; different-host atomicity remains S04 | CONSIDERED_NOT_SELECTED |

Study S03-A independently scheduled GPU-bound jobs versus S03-B/C one logical task spanning device/worker contexts. S03-D adds partition semantics only when a qualified provider/model and M02/M06 output lineage are actually source-backed. S03-E is a proof obligation for *future* jointly valid composite grants; no positive port exists yet. No candidate is a recommended or already-implemented technology.

## 4. Source and owner separation

| Source/owner | Current authority | S03 required negative discipline |
| --- | --- | --- |
| M02 frozen | Accepted ExecutionPlan, work identities, causality/production acceptance | Shards/replicas cannot mint a new accepted task or imply original production success |
| M06 frozen | Operational attempt, materialization and output lineage | Individual process exit, partial tensor/shard or merged bytes cannot imply accepted output |
| M09 frozen v1.0 | Per-resource truth, claims, leases, residency, valid owner mutations | Composite all-or-nothing proof unavailable for cross-boundary handoff; grant freshness/epoch/revocation must come from future M09-approved port |
| M10 frozen | Advice-only planning | Cost/quality estimate neither dispatches nor authorizes multi-GPU memory |
| M11 v0.2 unfreezed | Candidate worker/supervisor/OS lifetime | No process spawning, IPC, OS control or authenticated reverse liveness port |
| M12 owner pending | Prospective inventory and placement/queue orchestration only | No shared-memory guarantee, no placement topology/algorithm adopted |
| M13/M14/M17/M26/M48 index-only | Future performance, models, adapters/DCC, quality | No inferred model split, backend support, successful multi-GPU production or master acceptance |
| M54/M56/M58/M60 index-only | Future identity/security, telemetry, public API, deployment/OS rights | No inferred principal, driver topology, peer access, public worker registry or cross-host permission |

## 5. Exact future proof obligations (non-executable)

1. **All members:** candidate composite record must preserve exact work/action identity and every declared mandatory GPU/CPU/RAM member, not just a count or nominal group.
2. **Owner coherency:** future M09 owner must demonstrate one per-request jointly coherent snapshot+lease cut with version/epoch, freshness, expiry, revocation and all mandatory members. Independent M09 class-local `RLock` reads, cache snapshots, synthetics and `active()` are not evidence of that combined operation.
3. **At-use revalidation:** any feasible future candidate must re-evaluate exact work/attempt, M09 claims/member statuses and M11/M54/M60 authorization at the placement-to-dispatch boundary. The topology and protocol remain for owner decision, not this research.
4. **Heterogeneous devices:** preserve actual architecture/precision/memory/driver/runtime/model support and P2P/IPC capability as individually verifiable inputs. For separate-node devices, move to S04's remote trust/partitions contract, not an S03 local shortcut.
5. **Quality and failure:** M02/M06/M48 must separately handle attempt/replay, shard failure and partial output/quality acceptance. M11's OS evidence cannot rewrite those results or presume cooperative-release ACCEPTED reclaimed any capacity.
6. **8 GB guarantee discipline:** an 8 GB-class host must retain honest independently qualified routes via M09/M13/M14/M17/M26 as separately documented. Two devices with 8 GB each cannot be relabeled a single contiguous 16 GB allocation without proven qualified splitting and owner grants.

## 6. Proposed future hostile/ambiguity test matrix

Every case is **SPECIFIED_NOT_EXECUTED**; the repository Governance suite cannot qualify these scenarios.

| ID | Input / defect | Required safe non-inference | Dependency |
| --- | --- | --- | --- |
| MG-01 | Two GPUs advertised but one has no owner-issued M09 proof | No positive composite placement or dispatch | M09 H02 |
| MG-02 | Member A proof valid at t1, B at t2 without a joint owner cut | Never construct fictitious atomic grant from independent snapshots/locks | M09/#110 |
| MG-03 | Member B revoked after candidate ranking and before use | Revalidation blocks placement; no assumed capacity reclaimed | M09/M11 |
| MG-04 | One of two `LeaseBook.active()` entries is PREEMPTION_REQUESTED | No inference both are valid active grants | M09 |
| MG-05 | Synthetic/estimated sample reports extra GPU or VRAM | No positive admission from telemetry or fixture origin | M09/M56 |
| MG-06 | Advertised P2P link lacks verified supported peer access | Do not promise P2P transfer or shared GPU memory | M12/M60 |
| MG-07 | Mixed device architecture incompatible with required kernels or model | No assumed task compatibility, transparent fallback requires later owner proof | M12/M14/M17 |
| MG-08 | One worker process crashes after a partial model shard update | No unverified replay, re-launch or M06 success | M02/M06/M11 |
| MG-09 | OS PID reused or one GPU worker has unverified owner rights | No signal/reap or foreign-process control | M11/M54/M60 |
| MG-10 | GPU partition is represented as a full physical device and overcounted | No double reservation or overclaimed capacity | M09/M12/M60 |
| MG-11 | Model requiring 12GB appears to fit two 8GB devices based only on sum | No inferred model split, transfer capability or positive execution route | M09/M12/M14 |
| MG-12 | Cross-process IPC handoff omits principal or exact action association | No memory share or process action | M11/M54/M60 |
| MG-13 | Two successful process exits emit conflicting or incomplete outputs | No automatic M06 materialization or accepted master | M02/M06/M48 |
| MG-14 | One GPU stalls past timeout while another continues executing | No inferred termination, lease reclaim or safe duplicate retry | M06/M09/M11 |
| MG-15 | Future multi-host group loses network partition between owner proofs | No optimistic atomic placement or claim of node trust | M12 S04/M54/M60 |
| MG-16 | Unqualified GPU power/performance claim drives lower-cost remote recommendation | Advisory score not authoritative M09 grant or rights permission | M10/M12/M54 |

## 7. Twenty-two owner questions, all OPEN/UNRATED

Each distinct S03-U item is owner-routed for separate future review; no question is answered by comparing CUDA/DRA/DDP/Ray.

| ID | Future owner(s) | Pending question |
| --- | --- | --- |
| M12-S03-U01 | M09/M12 | What exact request-scoped per-device claims may future composite placement consume from a separately admitted M09 owner port? |
| M12-S03-U02 | M09/#110 | Can M09 prove one coherent jointly owned snapshot+lease cut for all mandatory GPU/CPU/RAM members, including epoch/revocation? |
| M12-S03-U03 | M12/M09 | How does each member's freshness/expiry and time-of-use revalidation work without mixing different observation epochs? |
| M12-S03-U04 | M11/M60 | Who proves worker/process ownership and OS rights for one-process-per-GPU and one-process-multiple-GPU candidates? |
| M12-S03-U05 | M12/M54 | Who verifies topology and device identities without trusting self-advertised accelerator counts? |
| M12-S03-U06 | M12/M60 | Which physical/virtual GPU partitions and supported platforms may be represented without conflating device count and isolation? |
| M12-S03-U07 | M12/M17 | Which ComfyUI/provider adapters actually support multi-device placement and validated output provenance? |
| M12-S03-U08 | M12/M26 | Which Blender/headless workloads support multi-GPU and which use one GPU per independent render task? |
| M12-S03-U09 | M12/M14 | Which model cards prove architecture, precision, memory and version support per heterogeneous accelerator? |
| M12-S03-U10 | M12/M13 | What evidence bounds copy/IPC/PCIe/NVLink/host staging latency and net benefit without guessing throughput? |
| M12-S03-U11 | M12/M54/M60 | What authenticated authority permits peer or cross-process memory sharing and revokes it? |
| M12-S03-U12 | M12/M09 | How are per-device headroom and the 8 GB-class production route preserved without summing unrelated VRAM? |
| M12-S03-U13 | M12/M11/M60 | What does failure of one member mean for still-running peers and OS cleanup rights? |
| M12-S03-U14 | M02/M06/M12 | Which exact plan/attempt/output lineage binds each split subtask without promoting partial output to success? |
| M12-S03-U15 | M12/M09/M11 | How is grant revocation while a multi-GPU action runs represented without silently reclaiming capacity or killing workers? |
| M12-S03-U16 | M12/M54/M58 | Which topology/capability details may be published across tenant or host boundaries? |
| M12-S03-U17 | M12/M56 | What verified telemetry separates advertised accelerator capability, observed utilization and resource owner truth? |
| M12-S03-U18 | M12/M10 | How are advisory cost/quality/latency estimates kept separate from M12 selection and M09 lease authorization? |
| M12-S03-U19 | M12/M11/M60 | What explicit CPU NUMA/affinity and process-containment evidence may influence heterogeneous placement? |
| M12-S03-U20 | M12/M09/M54 | What fail-closed behavior applies when two matching devices report conflicting stable IDs or provenance? |
| M12-S03-U21 | M12/M06 | How will the outcome distinguish data parallel output aggregation from merely observed worker process exits? |
| M12-S03-U22 | M12/M54/M60 | What additional remote-node security and data-movement consent must S04 define before multi-host placement? |

## 8. Forward scan and STOP

S03 is reference study only pending its own exact-head Governance, bounded audit, protected merge and exact-main. S04 must separately address LAN/cloud node federation, topology across trust domains, device claim transport and partition; S05 must separately address liveness, preemption, failover and cost/quality tradeoffs. Technology Discovery/FTR/FCS, versioned M12 owner contract and any implementation require later independently authorized gates. M09 #110 still requires actual owner choice or explicit DEFER, and H01–H04 all remain OPEN HIGH_FOR_FUTURE_FREEZE; no M12 positive placement, launch, allocation or trust proof may be proclaimed.
