# M12 S01 — Worker Registry and Capability Advertisements

Status: SOURCE_BACKED_REFERENCE_RESEARCH_PROPOSED (non-executable) | IRIS-WO-0022 | Issue #128
Exact study base: `e3fc858d3c92a8a3eba3c7c6119fc490c4098129` / tree `171bb58cec6a327a2cdab8a9b63bcc78a32363a0`.
Reference-only exploration. No discovery protocol, wire schema, TTL, signing algorithm, worker registration, trust decision, positive M09 grant or process lifecycle is selected.

## 1. Source-backed question

How could future M12 know **which workers might be candidates for a requested action** without treating self-asserted registration or device properties as authorization, live capacity, process control or a guarantee of placement? The existing architecture separates M02 accepted ExecutionPlan, M06 operational attempts, M09 resource/grant authority, M10 advisory suggestions, M11 candidate worker process ownership and M12's proposed placement/registry responsibilities. The master index calls for S01 worker registry and capability advertisements; none of those current artifacts defines an admitted M12 registry interface. That is the exact scope of this exploration.

## 2. Semantic layers to avoid conflating

| Layer | Potential future evidence, not an adopted schema | Who would have to verify/own it | What it does *not* establish |
| --- | --- | --- | --- |
| Candidate announcement | Advertiser-supplied worker/node reference, supported task/accelerator/adapter/runtime classes, explicit source and observed timestamp | M12 proposal, subject to future M54 identity/M58 publish and M60 platform rules | Authenticated worker, available device, current VRAM, authorized action |
| Node/worker binding | Verified node/worker association, provenance and revocation/epoch if future owner contracts provide them | Future M11 process/worker association; M54 trust; M60 OS identity | Accepted M02 work or M06 attempt outcome |
| Capability verification | Evidence that a named worker can support an advertised task type/adapter/accelerator under a qualified version | Future M12 registry contract plus M17/M26/other runtime owners; M54/M60 if privileged | Current capacity, license/rights, resource lease, live availability |
| Freshness/health | Last observation, bounded evidence age and explicit reachability/UNKNOWN | M11 liveness and future M56 observed telemetry with M54 trust | Process OS ownership, M09 grant or successful action |
| Resource admission | Exact fresh owner-issued request-scoped grant, composite members, expiry/epoch/revocation and time-of-use recheck **if and only if a future M09 contract adopts it** | M09; pending #110/C02 H01–H04 | Automatic worker dispatch or M12 scheduling authority |
| Placement/dispatch eligibility | Multiple independently verified M02/M06/M09/M11/M12/M54/M60 proofs linked to one exact request/action | Future separately frozen owner contracts and implementation admission | This S01 candidate does not compute or publish any positive result |

**Safeguard:** storing a field such as `available_vram`, `gpu_count`, `trusted=true` or `healthy` from an announcement MUST NOT be documented as verified current resource, authenticated principal, or authorized executable dispatch. No advertisement establishes a lease solely by being present in an index. This is preservation of established owner boundaries, not selection of a new public M12 policy.

## 3. Minimum future question vocabulary, not public serialization

The S01 register needs candidate **identity** (node ref, worker ref and owner/provenance; ephemeral vs stable binding unresolved), **capabilities** (task/accelerator/adapter class, declared version, optional software/driver compatibility and evidence origin), **scope** (host/locality/availability class where future owners allow it), **observation** (capture time, validity window, confidence/unknown, issuer/ref and policy revision only when verifiable), **trust** (M54-principal binding and revocation, pending), **operational readiness** (M11 liveness/OS association, pending), and **resource proof** (M09 owner grant/claims/expiry/TOCTOU, currently absent for M11). Whether any field is transmitted, stored or made public is pending M54/M58/M60 owner contract, not decided here.

Do not assign concrete JSON names, stable IDs, TTL defaults, discovery addresses, network hosts, cryptographic signatures, admission thresholds or optimistic cache semantics in S01. An M12 concept may carry `UNSUPPORTED`, `UNKNOWN`, stale, incompatible or conflicting descriptors for future analysis, but no invented owner-specific M09 or M54 return code is assumed.

## 4. Reference-only architecture alternatives and tradeoffs

| Candidate | Potential advantage | Risks and missing contracts | S01 status |
| --- | --- | --- | --- |
| In-process static registry/local manual allowlist | Simple discovery boundary for one current workstation and explicit operator-visible registration candidates | Still needs provenance, M11 process owner and M09 joint admission proof; local presence is not authority; lifecycle may change across UI restarts | CONSIDERED_NOT_SELECTED |
| Pull-based local capability inspection | Can query currently reachable candidates rather than only historical announcements | Needs platform-specific safe inspection, M60 rights and M11 ownership; software/VRAM observation can be stale before use | CONSIDERED_NOT_SELECTED |
| Worker-initiated announcements and heartbeats | Potentially supports headless workers and changing inventory, future remote nodes | Spoofing/replay, expiry, jitter, clock skew, partial partitions, revocation, authenticated channel and M54/M58/M60 contracts missing | CONSIDERED_NOT_SELECTED |
| Central coordinator with remote registry | May enable a later federated LAN/cloud inventory view | Single point of failure, trust isolation, residency, network ACLs, tenancy, connectivity and disclosure; M12 S04/M54/M58/M60 decisions missing | CONSIDERED_NOT_SELECTED |
| Federated/event-based discovery | May reduce dependence on one coordinator for larger deployments | Split-brain membership, conflicting declarations, consistency windows, unverified remote principal and unsafe double scheduling | CONSIDERED_NOT_SELECTED |

No implementation, topology or default policy is selected by this comparison. A worker being discoverable is not evidence that it is currently running or that its children are safe to manipulate.

## 5. Negative/ambiguity scenario matrix for future test design

All the following are **SPECIFIED_NOT_EXECUTED** candidate tests, not actual integration evidence:

| ID | Proposed hostile/ambiguous input | Expected *non-authorizing* planning boundary | Owning future proof |
| --- | --- | --- | --- |
| WR-01 | Self-advertised GPU/VRAM free without M09 owner-issued grant | No positive placement/dispatch from claims | M09/#110, M12 |
| WR-02 | Announcement expired or last heartbeat missing | No presumption of current worker liveness or ready capacity | M11, M56 |
| WR-03 | Same worker ID reused on a different node/OS handle | Preserve identity conflict, never control new/foreign process by PID/name | M11, M54, M60 |
| WR-04 | Remote node certificate/identity missing, revoked or unverified | No trusted federation, no remote dispatch | M54, M60 |
| WR-05 | Software task/adapter version unsupported, model absent or architecture mismatch | Capability INDETERMINATE/UNSUPPORTED; no inferred execution route | M12, M14, M17, M26 |
| WR-06 | Network partition, clock skew or contradictory announcements | No optimistic availability, double placement, retry or recovered outcome | M02, M06, M11, M12, M54 |
| WR-07 | Valid advertisement but M09 lease revoked/expired/preemption requested | Revalidate actual M09 owner evidence; no grant inferred from `active()` | M09/#110, M11 |
| WR-08 | M11 process ownership/OS permission unsupported | No process action; registry may retain only explicitly non-executable candidate data | M11, M54, M60 |
| WR-09 | Composite two-GPU advertised, only one member has valid owner proof | No partial composite admission | M09 H02, M12 S03 |
| WR-10 | Same M02 work submitted through two supervisors with stale queue mirror | No invented duplicate attempt/replay policy | M02, M06, M11, M12 |
| WR-11 | M10 recommends cheaper remote worker with no admitted M12/M54/M60 contract | Advice cannot authorize placement, data transfer, resource lease or execution | M10, M12, M54, M60 |
| WR-12 | API publishes private node/task descriptors without M58/M54 publication policy | No public registry or unsafe metadata exposure | M54, M58 |

These are *future* oracles for separately admitted implementations. S01 performs no OS probes, synthetic production grants or actual cross-module tests and cannot claim to have discharged C02 HX/LV cases.

## 6. Source-to-claim ledger

- `planning/MASTER-MODULE-INDEX.md`: M12 S01–S05 and neighboring M11/M13/other future-module headings are **index-level scope**, not adopted contract.
- `planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md`: M02's canonical production/ExecutionPlan ownership, distinct from scheduler/OS commands.
- `planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md`: M06 operational attempt, revision/materialization and evidence ownership.
- `docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md`: M09 resource/claim/lease authority and cross-process/M11 handoff deferred.
- `planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md`: M10 advice only, no dispatch/reservation.
- `planning/modules/M11-BACKGROUND-WORKER-FABRIC-PROCESS-LIFECYCLE.md`, `planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md`: non-executable M11 future supervisor/OS roles; v0.2 NOT_FROZEN.
- `planning/research/M11-S03-CONCURRENCY-LIMITS-PRIORITIES-AND-RESOURCE-LEASES.md`, `planning/research/M11-C09-REVERSE-LIVENESS-OWNER-RESEARCH.md`, `.engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json`: actual #110 remains unresolved, four H01–H04 future-freeze HIGHs and unexecuted liveness/handoff proofs.
- `docs/project-brain/16-DECISIONS-LEDGER.md` and `.engineering/SOURCE-HIERARCHY.md`: exact frozen-owner status and hierarchy; HIVE context is derived, Git source wins.

## 7. Explicit owner questions, 18 open/unrated

Each M12-S01-U ID remains OPEN/UNRATED_PENDING_OWNER and needs source-backed answer/assurance before M12 freeze, not merely documentation approval.

| ID | Owner(s) | Question |
| --- | --- | --- |
| M12-S01-U01 | M11/M12 | What canonical reference identifies a worker independent of OS PID, job and node? |
| M12-S01-U02 | M54/M60 | Which proof binds a principal to that worker/node on each supported platform? |
| M12-S01-U03 | M12/M54 | How is announcement issuer authenticity/replay/revocation verified? |
| M12-S01-U04 | M12/M56 | What source and expiry make an observed capability/health descriptor current? |
| M12-S01-U05 | M09/#110 | What jointly coherent M09 snapshot+lease evidence can qualify current per-action resource admission? |
| M12-S01-U06 | M09/M11 | How is reverse M11 owner liveness bound/authenticated without interpreting `M11:` prefixes as signatures? |
| M12-S01-U07 | M12/M60 | How are exact host/OS/accelerator and unsupported-platform capabilities described safely? |
| M12-S01-U08 | M12/M58/M54 | Which registry fields, if any, may cross node/project/tenant/public API boundaries? |
| M12-S01-U09 | M02/M06 | What exact work/attempt/epoch binds an advertisement to a separately authorized action? |
| M12-S01-U10 | M12/M11/M54 | Which observable state distinguishes discoverable, reachable, running and owner-controllable? |
| M12-S01-U11 | M12/M54/M60 | How are host clock skew, partitions and local-vs-remote identity handled? |
| M12-S01-U12 | M12/M17/M26 | Who verifies installed adapter/provider/task compatibility and qualified versions? |
| M12-S01-U13 | M12/M09 | How are composite member grants and mismatched expiry/revocation handled without partial admission? |
| M12-S01-U14 | M12/M11/M60 | What worker retirement/draining lifecycle would invalidate stale announcements? |
| M12-S01-U15 | M12/M02/M06 | Can duplicate announcements from two nodes ever imply a new attempt or retry? (Default: no claim.) |
| M12-S01-U16 | M12/M54/M56 | What permission-filtered provenance/telemetry can be retained without leaking tenant/node secrets? |
| M12-S01-U17 | M12/M10 | How is M10's plan recommendation kept separate from M12 placement and all owner grants? |
| M12-S01-U18 | M12/M11/M54/M60 | What separately reviewed minimal capabilities would be required for a future local-only registry before any remote federation? |

## 8. Outcome and STOP

S01 **reference exploration** can be completed after its own exact-head CI, separate scoped review and protected exact-main Governance. No owner question closes; no technical alternative becomes adopted; M12 S02–S05/technology discovery/FTR/FCS/freeze/implementation stay not started. M09 #110 decision, C02 H01–H04, M11 #82/#112 remain independent OPEN. Future actual worker/OS/GPU/network tests and security review are separate.
