# M09 Read-Only Resource Evidence Handoff: additive owner-contract candidate C01

Status: **PROPOSED_UNADOPTED_NOT_FROZEN** | Candidate: `m09-evidence-handoff-candidate-v0.1`
Existing canonical owner contract: `m09-contract-v1.0` FROZEN and unchanged
Planning Work Order: IRIS-WO-0016, planning admission passed exact-main Governance #458
Owner review: Issues #110/#112 OPEN, **no source-backed M09 owner adoption**
Consumer: M11 S03-U08 (still OPEN/UNRATED under Issue #82)
Source base: `045d82ce1328d85dfcb6c09cd602a2fbd5af3f9b`, tree `801fa6fd436cdfd36794f2b881627d1657ce306f`

## 1. What is being proposed and what is not

This is an **additive, conditional** M09 owner-owned interface proposal. It describes only read-only evidence about M09 resource truth, requests/claims, grants and lease-state validity for a *particular intended consumer request*. It is not a new resource allocator, permission grant, placement decision or process API. It neither amends nor weakens M09 v1.0's 83/15/514 frozen requirements and FC-09-01..14. No implementation is admitted, no wire schema/IPC/crypto chosen, and no positive execution path is available. The M09 owner must first decide whether same-process restricted reads suffice or a new versioned, independently verified boundary is required, then independently audit any actual interface contract.

Source boundaries: frozen `docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md`, `iris_resource_twin/{model,twin,leases,evidence,versioning}.py`, FC-09-03/09-09, M11 candidate v0.2 §9.1, M02/M06 owner contracts, Issues #110/#112. FC-09-09's generic public projection and M09's **qualification** `EvidenceBundle` are not M11 grant receipts. A Python symbol exported by M09 is not evidence of transport or trust.

## 2. Three topology alternatives (owner selection still pending)

A. **Narrow in-process-only read:** existing immutable `ResourceSnapshot` and `Lease` values may be studied only under a proven single M09 authority in the same process. A caller collecting two separately RLock-protected views does **not** obtain a coherent snapshot/lease cut or time-of-use authority. A would require the M09 owner to define any future atomic read/validation operation and an enforceable topology restriction. If that cannot be proven, all outputs are evidence-only/non-admitting.
B. **Future owner-issued versioned immutable receipt plus verifier:** conditional logical requirements in §§3–7 below. An implementation requires a separately approved additive M09 extension, an M09-owned atomic proof/invalidation design and independently provided M54/M60 trust/transport and M12 placement contracts.
C. **Negative-only public view:** may communicate unsupported/unknown/conflicting/denied/stale evidence in an owner-approved format while all positive grants remain unavailable. A safe interim option, but even its public schema, redaction and authority mapping need M09 and M54 owner review.

No topology is selected by this proposal or made operational by its merge.

## 3. Proposed logical read request and owner receipt roles, not serialized fields

**M09ReadEvidenceIntent (logical candidate only):** an opaque M11 request correlation and explicitly named intended resource-consuming action; the *exact* M02-issued accepted work/ExecutionPlan revision and provenance, if available; a canonical M09 resource/claim scope and requested target supplied only by the appropriate future owner; and an immutable caller context/reference if an owning permission port eventually supports it. If required M02 or M12/M54/M60 details cannot be verified, this intent can be logged for triage, **not** used as proof for a positive action.

**M09ReadOnlyResourceEvidence (logical candidate only):** must be **issued or validated by M09 itself** and distinguish:
- immutable issuer/contract revision and verification method, evidence identity, provenance, bounded required-feature/version set, exact intended work/resource/action/target/scope binding and an M09-controlled idempotent correlation;
- independently identifiable M09 observation: `ResourceSnapshot` ID/digest/schema, `ResourceIdentity`, `Confidence`, `EvidenceOrigin`, observation and expiry times, invalidation/quarantine status and freshness disposition. Original states stay distinct; `OBSERVED` plus synthetic origin is not a production grant;
- independently identifiable resource decision: actual M09 grant/lease **only if issued**, authoritative `Lease` ID, owner, original claims (including composite/sharing semantics), immutable grant provenance, current lease epoch, state, expiry, tombstone/revocation/preemption history and owner-verifiable request match. `LeaseBook.active()` membership alone proves neither no revocation nor applicability;
- **joint validity evidence** binding snapshot and grant to one coherent M09-controlled decision point. Existing `ResourceTwin` and `LeaseBook` have independent in-process locks, so the current package **does not claim** to supply this future proof. A stale cache, serialization, detached signature or two separate reads is not a joint cut;
- captured/current decision validity with explicitly owner-chosen clock uncertainty, lease transition epoch/freshness and non-replay constraints. No numeric TTL, cross-host clock assumption or cryptographic algorithm is invented here;
- M09 owner decision and evidence-status **separately** from M11's caller-visible projection; explicit missing, owner-denied, owner-unsupported, unknown, stale/conflicting, revoked/terminal and verification-error distinctions with retained original owner reasons and redaction/provenance references;
- if an M09 owner-selected version/feature/verification rule is unknown or cannot be checked, emit no positive proof. Any future provider/transport trust boundary is entirely conditional on M54/M60 owner contracts.

The receipt is an immutable statement of what M09 verified **under explicit validity conditions**, not a perpetual promise that another process may run. Only an admitted owner verifier may assert its current applicability. M09 never grants M11 general mutation access.

## 4. Proposed verifier obligations

A future `M09EvidenceVerifier` (logical name only) MUST reject by default unless its **owner** can prove all of the following in one permitted topology: authentic/correct owner issuer and required version/features; exact source/caller/intended request/work/resource/claim/action/target matching; trusted, non-synthetic, eligible reported-observation origin; original resource confidence not UNKNOWN/ESTIMATED/STALE/CONFLICTED/UNSUPPORTED/QUARANTINED; no invalidation or quarantine; complete owner-defined fresh scope; matching active **grant** with valid epoch, owner, claims and nonterminal, nonrevoking state; and a coherent owner-defined cross-record revision/TOCTOU check at verification time. Explicit `DENIED` requires an actual verifiable owner denial; no local guess from missing data. Revocation, expiry, preemption ambiguity, race, transport or owner outage are non-admitting until M09 defines any finer distinction. 

**No positive proof exists today.** If M09 cannot make a coherent cut or cannot confirm expiry/revocation while the consumer acts, the result is indeterminate/non-admitting. The M09 owner must specify whether later validation, short-lived owner-side tokens, or an owner-held transaction is needed. A future verified M09 receipt still does not supply M12 placement, M54 requested-action authorization, M60 OS process ownership/capability, M02 work admission or M06 attempt/outcome. M11 independently requires each applicable owner-issued proof before any admitted execution preflight. M10 advice, raw VRAM readings, a numeric PID, a local queue slot and generic serializer output never authorize dispatch.

## 5. Proposed refusal semantics and evidence preserving map

| Source condition | Logical owner evidence (M09 owner still to select) | M11 candidate projection (not yet adopted) |
|---|---|---|
| Required versioned M09 owner port unavailable or not admitted | no owner port, not an M09 denial | `UNSUPPORTED` |
| Port exists, exact owner proof missing/unverifiable/owner outage | missing/unknown, no owner denial inferred | `INDETERMINATE` |
| Verifiable M09 owner explicitly refuses the exact grant | owner denial with immutable source | `DENIED` |
| Verifiable owner declares requested capability unsupported | owner-specific unsupported, not stale or denied | `UNSUPPORTED` |
| Stale/conflicted/invalidated exact evidence or wrong owner scope | retain original statuses and nonmatching facts | `STALE_OR_CONFLICTING` only if M09 owner adopts the mapping |
| Quarantined or nonproduction estimated/synthetic observation | preserve original M09 status/origin | `INDETERMINATE` pending M09 mapping; no grant |
| Terminal or revocation-requested lease, epoch or joint-cut race | retain exact owner lease/epoch/reason | non-admitting; precise projection pending owner |
| Fully verifiable M09 grant, but M12/M54/M60 absent | M09 grant evidence alone | `INDETERMINATE` for M11 operational preflight; process DISABLED |

No row independently authorizes `CONTRACT_ELIGIBLE` or an OS action, even after owner amendment, without separate owner gates.

## 6. Negative proof and admission plan

Future M09 source-backed HX-01..12 negative proof cases are indexed in `.engineering/evidence/M09-HANDOFF-CANDIDATE-C01.json`. They must be implemented as deterministic harness tests **only under a separately admitted M09 implementation Work Order** with bounded fixtures and explicit mutation-free read assertions. In particular test the synthetic OBSERVED snapshot loophole, a revocation-requested lease in `active()`, mixed snapshot/lease epochs across two independent locks, mid-verification invalidation and cross-host no-trust conditions. An implementation must additionally prove 514/514 frozen invariant proofs and existing regression baselines intact; new HX IDs are separate candidate extension obligations, **not renumberings** of those invariants. Exact-head and exact-main Governance alone cannot certify cross-process, GPU, OS trust, owner permission or the HX semantics if no tests were executed.

## 7. Open owner decisions and freeze gate

**M09 owner must decide**, in a new independently reviewed source-backed disposition under Issue #110: whether A, B and/or C is actually acceptable; how a combined snapshot-and-lease decision is atomically made and invalidated; how cross-process identity and trust will be supplied only when M54/M60 own contracts exist; which recipient and redaction policy is permitted; clock/replay/expiry and revocation races; which original M09 statuses project to M11 logical refusals; and whether the proposal can remain nonpositive while M12/M54/M60 are pending. This candidate must undergo a separate compatibility/freeze-readiness review with zero residual HIGH/CRITICAL findings before *any* future owner amendment could be approved. Risk of absent owner contracts remains **UNRATED**, not zero.

IRIS-WO-0016 currently admits **planning only** after PR #114/#458. This candidate C01 is not owner adoption or contract freeze. No `iris_resource_twin/` code, frozen `m09-contract-v1.0`, 83/15/514 legacy catalogs, process, lease or resource operation changed. Issues #82/#110/#112 remain OPEN; M11 S03-U08 and all 86 original questions OPEN/UNRATED, eight PO-C02 and ten C08 cases NOT_EXECUTED, all M11 process actions DISABLED, M10/M11 implementation NOT_ADMITTED, M12–M60 PENDING/UNRATED. Stop at independently audited planning candidate and await owner-source decisions.
