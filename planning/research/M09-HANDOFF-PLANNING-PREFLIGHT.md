# M09 read-only owner-evidence handoff: admission preflight and decision map

Status: RESEARCH_PROPOSED, not a frozen contract or authorized inter-module port
Work Order: IRIS-WO-0016 (conditional planning admission), Issues #112 / #110 / #82
Exact source: `7cdfa0015eaf67bac570deea67177239bb4549af`, tree `6030279a39a95920c6e1e5ef7288ecfce1818239`. Current M09 v1.0 implementation and owner contract untouched.

## Existing verified facts

- `iris_resource_twin.__version__ = 1.0.0` publicly exposes in-process Python data types, including `ResourceSnapshot`, `ResourceTwin`, `LeaseBook` and generic schema/serialization. Export is not network authorization or public M11 grant-verification semantics.
- `ResourceTwin.admission_snapshot` retrieves **one** fresh, noninvalidated, nonquarantined snapshot from an RLock-protected in-memory twin. `ResourceSnapshot.is_fresh` uses capture/expiry and `Confidence.OBSERVED`, **not** `EvidenceOrigin.REPORTED_OBSERVATION`, an active lease or request scope. A fresh synthetic-observed snapshot may still pass that snapshot reader.
- `LeaseBook.active()` returns ACTIVE plus PREEMPTION_REQUESTED and REVOCATION_REQUESTED; `tombstone()` returns terminal lease records. Its lock is distinct from `ResourceTwin`'s lock, and there is no proven atomic M11-visible combined snapshot/grant epoch in the reviewed sources. `LeaseBook.grant` separately checks matching resource, production evidence origin and freshness under its own admission semantics.
- M09 `EvidenceBundle` is qualification evidence for 83/15/514 coverage and exact implementation revisions, **not** an action-scoped resource grant. FC-09-09's versioned public evidence projection requires provenance/redaction, not a currently selected authenticated cross-process M11 proof.
- Canonical M09 docs explicitly defer cross-process locking, persistence and concrete M11 integration. M02 owns plan/production authority, M06 outcomes, M09 grants/leases/resource truth; M11 process evidence cannot inherit those. M12/M54/M60 lack detailed owner contracts.

## Three decision alternatives, no selection yet

| Track | What can be proposed | Positive M11 admission today | Required separate decision |
|---|---|---|---|
| A: restricted same-process read-only M09 view | Typed immutable snapshot and lease facts only in a verifiably single-authority owner topology | NO | M09 owner proves atomic combined current state, no cross-process use; M12/M54/M60 gates still absent |
| B: versioned M09-issued immutable evidence receipt + verifier | Owner binds exact request/work/resource/action/target/scope, version, provenance, verified live grant+snapshot consistency, epoch, expiry and revocation | NO | New additive owner version, security/trust, serialization, concurrency and invalidation; no invented implementation |
| C: negative-only projection | Versioned refusal/unknown evidence without an executable positive result | NO | M09 owner acceptance of distinct reasons, downgrade/unsupported mapping and publication boundary |

A and B are candidates, not two implementations that can be switched by M11. C may be layered on either only if M09 accepts. No platform, algorithm, TTL, clock sync or remote placement is selected.

## Minimum proposed owner receipt roles (not wire fields)

The future M09-owned proposal must resolve a verifier's exact issuer/contract and integrity identity; M02 owner-issued accepted work reference; intended M11 action, resource/host/target/scope and immutable request correlation; resource observation ID/digest/origin/confidence/timestamp; lease ID/epoch/claims/state/owner/grant provenance/current expiry/revocation; a proof that both facts were consistent under one **M09 authority** at the relevant decision point; freshness with owner-defined bounded clock uncertainty; redaction and M54-owned permission reference; rejection of unsupported semantics and any unknown extra *required* feature. If M09 can't prove a joint current cut, only a non-admitting outcome is possible.

A one-time hash, serialized `Lease`, cached `active()` membership, receipt signature, PID, OS slot, M10 recommendation, estimated capacity or current snapshot **alone** is never an action-scoped grant. M09 read receipt cannot grant M12 placement, M54 process permission, M60 OS ownership, M02 plan acceptance, M06 attempt/materialization or launch.

## Explicit proposal for future negative proof obligations

| ID | Test condition | Required fail-closed property |
|---|---|---|
| HX-01 | M09-to-M11 versioned owner port absent | UNSUPPORTED, no process action |
| HX-02 | Owner port exists but applicable receipt absent/undecidable | INDETERMINATE, no process action |
| HX-03 | OBSERVED but SYNTHETIC_FIXTURE or DERIVED_ESTIMATE snapshot | no production grant or worker admission |
| HX-04 | Fresh snapshot, revoked/revocation-requested/preemption-requested lease | no blanket positive from `active()` |
| HX-05 | Snapshot/lease read in different epochs or racing mutation | no positive without owner-verifiable consistent cut |
| HX-06 | Work/resource/action/target or host binding mismatch | no reinterpretation/rebind |
| HX-07 | Revocation/expiry between issuance and consumption | no positive without owner-defined validation/recheck |
| HX-08 | Stale, conflicted, UNKNOWN, UNSUPPORTED, QUARANTINED or invalidated observation | preserve original M09 facts and no admission |
| HX-09 | Unknown issuer/required schema feature/cryptographic trust | fail closed, no silent downgrade |
| HX-10 | Positive M09 evidence but missing M12/M54/M60 proofs | M11 action still DISABLED |
| HX-11 | Cross-process/host consumer without admitted coordination or clock model | no claim from in-memory RLock alone |
| HX-12 | M09 error/timeout or unavailable owner during revalidation | no automated lease mutation, dispatch or retry |

All 12 are **SPECIFIED_NOT_EXECUTED** planning oracles requiring separate source-backed M09 acceptance and admitted implementation. The 8 PO-C02 and 10 C08 non-dispatch examples remain NOT_EXECUTED. Synthetic future tests would not certify physical/GPU/OS execution.

## Required decision gates and STOP

Before drafting an actual owner-extension candidate, this admission preflight needs an exact-base lock, exact-head CI, separate bounded review, protected merge and exact-main CI. A later M09-owner review must decide the topology, field/scope/proof contract, atomicity, freshness, revocation race, redaction and tests; unresolved security/placement/platform details remain unratable and non-executable. Preserve `m09-contract-v1.0` and 514 old invariant claims; no frozen change without owner amendment, new audit and implementation gates. Do not resolve #110, S03-U08 or #82 based on this planning draft.
