# M11 C09: reverse owner-liveness and cooperative-release producer boundary

**Status:** M11_PRODUCER_SIDE_RESEARCH_PROPOSAL_ONLY, NOT_FROZEN, NO_PORT_ADOPTED | **WO:** IRIS-WO-0015 | **Issues:** #82/#110/#112 OPEN
**Base:** `885659cecdd8865bb713f80c1b503583311233e9` / `8767077dbed3599829855373a6bb7da2f829c581`. PR #116 C02 is canonical documentary compatibility evidence (exact-head #461, exact-main #462, 3,940/3,940); its four HIGH_FOR_FUTURE_FREEZE blockers remain OPEN. This file does **not** adopt a contract or authorize M11/M09 actions.

## 1. Normative source facts distinct from proposals

Frozen M09 FC-09-03 requires a future M11 owner-liveness reference with freshness and UNKNOWN, and a cooperative-release handshake. At exact base `iris_resource_twin/recovery.py` already defines in-process `OwnerLivenessRef(owner_ref,state,authority_ref,observed_at_ms,evidence_ref)`: ALIVE/TERMINATED/UNKNOWN, requiring only an `M11` textual prefix for non-UNKNOWN. That prefix is a structural check, not an authenticated M11 process producer. `confirm_leak` checks owner, time, observations and fresh production-origin snapshot but, absent a genuinely verified external M11 producer, cannot establish cross-module trust by itself. `evaluate_cooperative_release` maps accepted response to `ACCEPTED_AWAITING_RESOURCE_RECONCILIATION` with `capacity_reclaimed=false`. A timeout proves neither termination nor release.

M11 v0.2 §9.2 already proposes an owner- and action-scoped OS `ProcessCapabilityEvidence`, distinct from PID/PPID. §9.3 keeps OS observation, delivery, exit and M06 outcome as separate evidence stages, with UNKNOWN as recovery default. All are candidate semantics, not M60 OS rights. M09 C01 addresses the *opposite direction*, proposed M09→M11 read-only exact-request grant proof; it cannot be reused as a liveness issuer.

## 2. M11-owned logical producer proposal (NOT a new exported type, wire format or API)

| Logical M11 role | Required evidence if future owners admit it | Refusal/default |
| --- | --- | --- |
| Owner/process association | Exact M11 request revision, owner_ref, M02 accepted-work ref, optional M06 attempt ref, provenance and an M60-qualified process capability for the exact observation; do not mint missing foreign refs. | No valid capability/owner match → UNKNOWN; no process control. |
| Observed liveness | ALIVE/TERMINATED/UNKNOWN as *observation at capture time*, including source evidence, revision, producer status and capture/freshness confidence. A non-UNKNOWN state must be justified by valid owner-scoped process observation, not PID or a string prefix. | Unreachable, PID reuse, stale, unsupported, lost parent or conflicting observation → UNKNOWN/non-admitting. |
| Issuer verification boundary | A versioned source, issuer/authorization validity and exact scope/identity proof selected by M11+M54+M60 and acceptable to M09. M11 cannot set its own `M09 verified` flag. Trust/transport and cross-host policy deferred to owners. | No admitted verifier/transport → no authenticated handoff. |
| Lease/action correlation | Preserve opaque M09 lease/request_id, M11 owner_ref, exact action/scope, attempt/process evidence reference and observed_at. No M11-generated lease epoch or resource availability claim. | Mismatched/stale lease or work/owner scope → no positive liveness consumption. |
| Cooperative-release handling | M09 owns the request and resource reconciliation. M11 may *propose* response/ack role for matching request/owner and observed handoff, separately from actual OS action/exit; idempotency/duplicate and delivery proof subject to owner contracts. | ACCEPTED means only accepted request; M09 retains `capacity_reclaimed=false` until independent reconciliation. |
| Recovery/unknown | Record missing/partial/conflicting evidence and inability to prove rights, transport or current state, preserving original M11 reason. UNKNOWN never authorizes automatic termination/relaunch, M09 leak confirmation, resource release or M06 success. | Fail closed; no inferred side effects. |

A future *logical* envelope could carry `(owner_ref, m11_request_ref, process_capability_ref, observed_state, observed_at, issuer_evidence_ref, validity_status, optional_m09_request_id, optional_m02_work_ref, optional_m06_attempt_ref)`. This is a role inventory for owner review, **not** an adopted serialized field list or guarantee that all values exist. Actual M09 owner decides admissible projections under #110; M54/M60 set provenance/platform proof; M12/M58 gates apply to remote/public exposure. Never expose this envelope as a live cross-module interface under C09.

## 3. Case-by-case future negative/proof mapping (existing IDs; none executed)

| Existing LV ID | M11 source/proposed behavior | Forbidden interpretation |
| --- | --- | --- |
| LV-01 | Reject externally unverified, forged but fresh `M11:...` TERMINATED assertion; require real issuer+OS-capability proof. | No remote leak promotion, process control or resource reclamation from prefix. |
| LV-02 | Preserve UNKNOWN for stale, missing, mismatched or unsupported owner-liveness evidence. | No inferred owner death, no M09 grant/release. |
| LV-03 | Correlate ACCEPTED ack to the exact M09 request and owner; keep acceptance separate from exit/reconciliation. | No `capacity_reclaimed=true` or immediate reuse. |
| LV-04 | Handle absent, late, wrong-request/owner, replayed or contradictory ack conservatively; preserve request evidence. | Timeout or receipt is not OS kill/reap authorization. |
| LV-05 | Preserve each mandatory composite claim/lease member state as M09-owned, no aggregate positive inference. | No positive grant from a subset, independent locks or `active()`. |
| LV-06 | Preserve uncertainty after liveness/lease epoch conflict, revocation, lost owner or verification-to-action race. | No stale liveness reuse, reaper or resource release. |

The original six `LV-01..06` remain `SPECIFIED_NOT_EXECUTED` under C02, in addition to twelve HX, ten C08 and eight PO-C02 not executed. No duplicate IDs are added; this note identifies what an eventual M11-owned proof fixture would need to witness and which decisions are external.

## 4. Owner dependencies and explicit design gates

- **M09 #110**: accepted reverse consumer mapping and M09-side owner decision, snapshot/lease atomics and release reconciliation. The C01 forward options A/B/C remain NONE_SELECTED.
- **M11 #82**: process-capability-backed producer identity, versioned liveness/UNKNOWN semantics, ack correlation, loss/recovery state. Future exact M11 owner review required; M11 v0.2 unchanged and NOT_FROZEN.
- **M54/M60**: issuer/principal authorization, observation rights, platform capability and process identity proof. Both are INDEX_ONLY/PENDING at this base. Without them, no trusted non-UNKNOWN intermodule handoff.
- **M12/M58**: placement, host/cross-boundary trust and public schema if that topology is admitted. No local/remote default and no public serialization chosen.
- **M02/M06**: exact accepted-work revision and independent attempt/materialization ownership, never inferred from worker exit/ack.

## 5. Freeze/implementation STOP

No actual M11 producer, transport or M09 consumer port exists by virtue of this note. Future-freeze H01 remains OPEN despite clarified proposed M11 responsibilities; H02–H04 remain OPEN in C02. No tests added, 514 existing M09 proofs untouched; no real OS/GPU/process/IPC action or resource mutation. Next substantive step still requires actual owner disposition #110 and admitted owner contracts, not another documentary pass presented as implementation.
