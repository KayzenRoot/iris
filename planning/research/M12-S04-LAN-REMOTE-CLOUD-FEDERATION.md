# M12 S04 — LAN, Remote and Cloud Spillover and Federated IRIS Nodes

Status: PROPOSED_NON_EXECUTABLE_REFERENCE_RESEARCH | IRIS-WO-0025 | Issue #128
Exact research base: `d94f19de4a7b5ed8e248ea41239bc53df90a58b1`, tree `963d02cf2083e44f1f78a651bc383e8fc7386eed`. Governance #489 exact-main PASS 3979/3979.
This document selects no federation topology, provider, transport, endpoint, credential, capacity quota, default remote-execution mode or retry policy.

## 1. Research question and non-negotiable boundaries

How could future M12 discover and compare *candidate* off-host compute while keeping network availability, identity, resource truth, OS-process control, accepted work and data-transfer permissions independent? M12 S01 only provides candidate advertisements; S02's scheduler policy families and S03's multi-GPU shapes are reference studies, not executable interfaces. M02 owns accepted plans; M06 owns operational attempts and artifact outcomes; M09 v1.0 owns resource truth/grants/leases; M10 recommendations never grant dispatch rights; M11's OS/supervisor candidate v0.2 remains NOT_FROZEN. M54 security, M55 storage, M56 telemetry, M58 API and M60 platform/deployment owner contracts are PENDING. Issue #110 still has no explicit owner selection A/B/C; H01–H04 remain OPEN HIGH_FOR_FUTURE_FREEZE. No positive remote M09 grant, verified M11 process owner, M54 principal authorization or M06 output is available from a remote advertisement.

No real network, cloud, paid provider, OS, GPU or credential operation occurs in this study. A remote endpoint is not proof of safe data export, and a missed heartbeat is not proof of terminated OS work.

## 2. Verified external technical references, NOT adopted dependencies

| Official published source | Documented property | Future IRIS question |
| --- | --- | --- |
| Ray Cluster Key Concepts | Head/control processes, worker nodes and autoscaler can operate in a cluster | Which *separately admitted* owner could safely govern a future cluster controller? |
| Ray Security | Deployment requires an appropriate trusted and access-controlled security boundary | Which M54/M58/M60 network and principal contracts would isolate IRIS project data? |
| KubeRay GCS Fault Tolerance | External durable control metadata can enable GCS restart recovery, with operational caveats | How would IRIS avoid stale-generation and split-brain worker ownership? |
| AWS EC2 Spot Best Practices | Interruptible instances, fault-tolerance, rebalance and interruption warnings; capacity is not guaranteed | What actual proof would permit owner-approved checkpoint and retry decisions? |

Primary docs consulted 2026-09-27:
- https://docs.ray.io/en/latest/cluster/key-concepts.html
- https://docs.ray.io/en/latest/ray-security/index.html
- https://docs.ray.io/en/latest/cluster/kubernetes/user-guides/kuberay-gcs-ft.html
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-best-practices.html

No Ray, KubeRay, AWS or equivalent software is installed, called, adopted or tested as part of this document.

## 3. Six architecture alternatives, unselected

| ID | Candidate | Research status |
| --- | --- | --- |
| F-01 | Local only with explicit export/import: smallest network exposure but no remote compute | CONSIDERED_NOT_SELECTED |
| F-02 | Direct authenticated LAN peer: possible lower overhead; node identity and firewall authority still absent | CONSIDERED_NOT_SELECTED |
| F-03 | Single authenticated LAN coordinator: possible central inventory; failover/split-brain unresolved | CONSIDERED_NOT_SELECTED |
| F-04 | Federation among separately governed LAN sites: possible scale; policy/consent boundaries unresolved | CONSIDERED_NOT_SELECTED |
| F-05 | Private dedicated remote host: potential batch capacity; data export and worker ownership unresolved | CONSIDERED_NOT_SELECTED |
| F-06 | On-demand/interruptible cloud: potential elasticity; budget, egress and interruption/rights unresolved | CONSIDERED_NOT_SELECTED |

Each alternative requires separately approved M54/M58/M60 trust and endpoint policy, owner-issued M09 exact fresh per-request resource proof (including all composite members), M11 worker/process ownership and actual M02/M06 work identity. A LAN hostname or advertised price never establishes any of those facts. S05 will study recovery/preemption separately.

## 4. Prospective proof layers (NOT a public interface)

| Layer | Required future owner evidence | Unsafe shortcut |
| --- | --- | --- |
| Discovery | Source-approved remote node identity, permitted endpoint and project scope | Anyone can advertise a remote worker |
| Authentication | Revocable principal and peer binding, secure transport and explicit policy | A reachable hostname means trusted remote compute |
| Capability | Qualified per-model/provider/accelerator version evidence with provenance and freshness | Self-reported GPU count or architecture means supported task |
| Resource truth | Exact owner-issued request-scoped coherent M09 snapshot+lease/member proof, if a separate handoff is adopted | Two independent snapshots, cache or quotas imply a grant |
| Process control | Verified M11 worker/OS owner evidence and M60 platform rights | Missing heartbeat or reused PID authorizes killing a process |
| Transfer | M54 user/project authorization, rights, residency and integrity-bound M55/M59 storage | A valid cluster invitation authorizes exporting private files |
| Accounting | Actual cost, egress, regional limits, deadlines, interruptions and explicit spend authority | An advisory M10 score approves cloud billing |
| Recovery | M02/M06 attempt lineage, dedup proof, verified liveness, safe grant reclamation | Network partition or Spot notice implies failure/retry is safe |

**Network partition and identity reuse:** cached announcements or cloned coordinator histories are never sufficient for resumed execution, accepted output, reclaimed capacity or a new attempt. The choice of generation fencing, storage, protocol and split-brain resolution requires future owner decisions, not this study.

## 5. Future negative/ambiguous verification scenarios

All **18** cases are SPECIFIED_NOT_EXECUTED, not assertions of passing integration/security tests.

| ID | Hypothetical condition | Required non-inference for future owner | Dependency |
| --- | --- | --- | --- |
| FN-01 | Unauthenticated node advertises abundant GPUs | No trusted candidate or positive placement | M09/M54 |
| FN-02 | Rebooted node reuses an OS PID and stale registration | No control of foreign process | M11/M60 |
| FN-03 | Peer credential is revoked despite successful network connection | No data transfer or remote execution | M54/M58 |
| FN-04 | Untrusted candidate substitutes private/internal service endpoint | No reachability escalation or endpoint use | M54/M58 |
| FN-05 | Two disconnected coordinators both claim one worker | No duplicate attempt or capacity admission | M02/M06/M09 |
| FN-06 | Heartbeat remains cached through partition or clock skew | No assumption of current liveness | M11/M56 |
| FN-07 | Remote VRAM sample lacks coherent owner-issued snapshot and lease | No remote grant or dispatch | M09/#110 |
| FN-08 | Remote work candidate has no accepted M11 process/OS capability | No spawn, kill, resume or reap | M11/M60 |
| FN-09 | Cross-site media or model lacks approved rights or residency | No remote export | M54/M59 |
| FN-10 | Remote worker requests a local provider credential | No secret handoff | M54/M60 |
| FN-11 | Cloud instance disappears without interruption warning | No presumed checkpoint, retry or lease reclamation | M06/M09/M11 |
| FN-12 | Replacement instance overlaps with still-running prior task | No duplicated side effect or optimistic release | M02/M06/M09 |
| FN-13 | Transfer, GPU tariff or cloud budget is unverified | No claimed cost saving or paid spillover | M10/M12 |
| FN-14 | Remote model or driver version conflicts with advertised capabilities | No executable route inferred | M12/M14 |
| FN-15 | Federation publishes confidential queue or worker descriptors | No unauthorized disclosure | M54/M58 |
| FN-16 | Remote output is incomplete or has incorrect hash/provenance | No accepted artifact or fabricated success | M06/M55 |
| FN-17 | Another tenant connects using recycled node identity | No inherited authority or stale grant | M54/M60 |
| FN-18 | Two nodes report GPUs totaling 16 GB without a split model | No contiguous-memory claim or composite admission | M09/M12 |

## 6. Owner-question register

All **24** distinct M12-S04 questions remain OPEN/UNRATED_PENDING_OWNER, including future M54/M58/M60 authority. Documentation approval does not resolve them.

| ID | Prospective owner(s) | Question |
| --- | --- | --- |
| M12-S04-U01 | M54/M58/M60 | What source-issued proof binds a remote endpoint, worker and principal to the allowed tenant? |
| M12-S04-U02 | M11/M54/M60 | How would a rebooted/readdressed node prevent reuse of stale worker/PID ownership? |
| M12-S04-U03 | M54/M58 | Who authorizes discovery publication and versions of future remote APIs? |
| M12-S04-U04 | M54/M60 | What source-backed transport encryption, peer authentication and key rotation evidence is mandatory? |
| M12-S04-U05 | M11/M56 | How is remote liveness observed without treating heartbeat age as worker/process proof? |
| M12-S04-U06 | M09/#110 | Which owner-approved M09 grant could bind remote per-device resources and all group members coherently? |
| M12-S04-U07 | M11/M54/M60 | What authenticated M11 process-owner evidence can cross operating-system and node boundaries? |
| M12-S04-U08 | M02/M06 | Which accepted work/attempt/revision identities must accompany any proposed cross-host execution? |
| M12-S04-U09 | M54/M59/M60 | Who owns remote media/model export, consent, jurisdiction and data-residency permissions? |
| M12-S04-U10 | M55/M06 | How would remote staged data retain integrity, exact provenance and accepted-output boundaries? |
| M12-S04-U11 | M54/M60 | How are privileged credentials prevented from being exported to a remote worker? |
| M12-S04-U12 | M12/M13/M56 | What measured latency, throughput, warm-model state and egress cost permit a future placement comparison? |
| M12-S04-U13 | M54/M58 | What project/tenant/capacity fields may be exposed to another federation domain? |
| M12-S04-U14 | M11/M56 | What is the safe meaning of missing heartbeat versus verified process exit? |
| M12-S04-U15 | M02/M06/M11 | Who approves retries and prevents duplicated side effects after remote link loss? |
| M12-S04-U16 | M11/M54 | What authenticated generation/epoch fences stale federation controllers and recycled node identifiers? |
| M12-S04-U17 | M09/M11 | When is remote resource capacity truly reclaimed after cancellation or instance interruption? |
| M12-S04-U18 | M10/M12/M54 | Who may approve paid cloud usage and exact budgets, regional policies, and quality/cost preferences? |
| M12-S04-U19 | M12/M14/M17/M26 | Who qualifies runtime, model, license, provider and accelerator compatibility on foreign hosts? |
| M12-S04-U20 | M54/M58/M60 | What network ingress/egress, NAT, firewall, endpoint allowlist and private-link contract is necessary? |
| M12-S04-U21 | M54/M58 | How is malicious endpoint substitution or unintended local-network reachability excluded? |
| M12-S04-U22 | M54/M56 | What filtered telemetry/provenance is permitted without leaking project identity, IPs or secrets? |
| M12-S04-U23 | M06/M55/M59 | How do partial uploads and conflicting output revisions avoid false master acceptance? |
| M12-S04-U24 | M11/M54/M60 | What separately admitted local-LAN canary and security review precedes any cloud federation? |

## 7. Forward compatibility and STOP

S05 must separately examine cancellation, preemption, worker/leader failure, idempotent retry, Spot interruption and cost/quality. Technology discovery/FTR/FCS and any candidate M12 contract require new review; S04 never silently chooses a network protocol, federation trust model, region, provider or automatic spillover policy. Complete this S04 *reference research only* after its own reviewed exact-head Governance and protected exact-main; leave #128 OPEN for S05 and further freeze gates, and keep #82/#110/#112 OPEN. No process, network, cloud, GPU or resource action authorized.
