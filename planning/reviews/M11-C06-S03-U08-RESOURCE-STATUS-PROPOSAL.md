# M11 C06: S03-U08 caller-visible resource evidence status, bounded draft

Status: PROPOSED_FOR_SEPARATE_REVIEW, not adopted or frozen | IRIS-WO-0015 | Issue #82 OPEN
Exact base: `9af145412decfb6083574cf0d890b22b7df04c5c` / tree `615977775536694e4530cab526db0f8a3e576a57`

## Previous C05 closeout

PR #108 exact head `c717715a8cc4e2fd36bc6d4e8e3b0a5db1863a4b` passed Governance #449 (run `36312357732` / job `108600620655`, 3,940/3,940). Protected squash merge `9af145412decfb6083574cf0d890b22b7df04c5c` passed exact-main Governance #450 (run `36312414947` / job `108600777464`, 3,940/3,940) at this exact source base. C05 kept 86 questions OPEN/UNRATED, eight PO-C02 obligations NOT_EXECUTED, and refined owner triage to 20 / 1 / 63 / 2. S03-U08 is the one M11-led **documentation-proposable** question; the routing is a proposal, not M09 approval.

## Exact unchanged question

**S03-U08:** What caller-visible state is required when resource evidence is unknown, stale, conflicting, denied or unsupported?

M11 may propose a *logical caller-visible refusal and evidence envelope* only. M09 still owns resource confidence, claims, grants, lease state, verification, revocation, freshness and resource truth. M02 owns accepted work/plan causality; M12 placement, M54 security permission and M60 OS/platform capability contracts are not available. This document neither defines an M09-to-M11 port nor adopts a public API/serialization, retry policy or process/resource action.

## Source-grounded distinctions

M09's existing model provides `Confidence` values `OBSERVED`, `ESTIMATED`, `STALE`, `CONFLICTED`, `UNKNOWN`, `UNSUPPORTED`, `QUARANTINED`; and `EvidenceOrigin` distinguishes reported observation, derived estimate and synthetic fixture. These are **M09 observation facts, not M11 permission decisions**. Its lease model separately tracks `ACTIVE`, `PREEMPTION_REQUESTED`, `REVOCATION_REQUESTED`, `REVOKED`, `RELEASED`, `EXPIRED`. A snapshot or lease state by itself is not a verified grant for an arbitrary exact request. M09's `LeaseBook.grant` explicitly rejects unknown, non-production and non-fresh truth; its in-process nature proves no cross-supervisor or distributed coordination. M11 candidate §9.1 already proposes distinct logical `DENIED`, `UNSUPPORTED`, `INDETERMINATE`, `STALE_OR_CONFLICTING` and documentation-only `CONTRACT_ELIGIBLE` preflight classes. No existing M11-facing M09 owner port, authoritative mapping or numeric freshness window is claimed.

## Nine negative/non-admitting draft examples

These are **M11-facing draft projections**, not actual M09 API responses. Even apparently fresh owner grant evidence is not dispatch authorization while M12/M54/M60 remain pending.

| ID | Evidence situation | Draft M11 preflight result | Distinct reason |
| --- | --- | --- | --- |
| S03U08-01 | No owner-issued M09 evidence/reference or M09-facing port unavailable | `INDETERMINATE` | OWNER_EVIDENCE_MISSING |
| S03U08-02 | Owner M09 observation/reference STALE, invalid freshness or conflicting scopes | `STALE_OR_CONFLICTING` | M09_STALE_OR_SCOPE_CONFLICT |
| S03U08-03 | Verified M09 owner decision expressly denies applicable resource claim, if such future M11-facing decision exists | `DENIED` | M09_OWNER_DENIAL_IF_VERIFIABLE |
| S03U08-04 | M09 owner declares needed evidence or capability UNSUPPORTED, when verifiably stated | `UNSUPPORTED` | M09_UNSUPPORTED_IF_VERIFIABLE |
| S03U08-05 | M09 snapshot QUARANTINED or reconciliation CONFLICTED; owner decision or safe handoff absent | `INDETERMINATE` | M09_QUARANTINED_DISTINCT_EVIDENCE |
| S03U08-06 | M09 observation ESTIMATED or synthetic/derived rather than production-reported owner grant | `INDETERMINATE` | NON_AUTHORITATIVE_OBSERVATION |
| S03U08-07 | M09 grant ref REVOKED, EXPIRED or mismatched current epoch/scope/action | `STALE_OR_CONFLICTING` | M09_INVALID_OR_TERMINAL_REFERENCE |
| S03U08-08 | Evidence for another work/resource/host/action, even if fresh and owner-issued | `STALE_OR_CONFLICTING` | EXACT_REQUEST_SCOPE_MISMATCH |
| S03U08-09 | Fresh verified M09-issued applicable grant-state evidence, if future handoff defined | `INDETERMINATE` | RESOURCE_EVIDENCE_PRESENT_OTHER_OWNER_GATES_PENDING |

Each hypothetical caller-visible receipt would preserve exact M11 correlation/intended action, version-pinned M02 accepted plan if available, owner-issued M09 proof/issuer only if actually issued, exact resource/work/scope binding, source freshness/verification outcome and distinct non-admitting cause. No M11-created M09 lease ID, principal, placement, owner decision, OS process capability or outcome may be fabricated. Case 09 records an M09 evidence-present *fact*, not `CONTRACT_ELIGIBLE`, process permission or release of any other owner gate.

## Future independent evidence and risk boundaries

The accompanying machine-readable `.engineering/evidence/M11-C06-S03-U08-RESOURCE-STATUS.json` defines nine **DESIGNED_NOT_EXECUTED** synthetic/negative proof scenarios. After M09 owner review of the proposed projection, test each with immutable synthetic references and distinct input owners. PO-C02-02 (M09 stale/conflict) and PO-C02-03 (missing M12 placement) remain NOT_EXECUTED, as do all eight prior obligations. Test the distinction between M09 confidence, owner decision, lease status and M11 refusal projection; a green documentation CI cannot prove a positive integration or any host/GPU behavior.

S03-U08 remains **OPEN** with risk **UNRATED**, pending a source-backed M09 owner disposition and a separate freeze-readiness audit. Do not auto-close it because the draft exists. No automatic retry/backoff, fallback allocation, resource mutation, process start/control, OS/IPC/platform choice or policy threshold is selected. M11 `m11-contract-candidate-v0.2` remains NOT_FROZEN, M10/M11 implementation NOT_ADMITTED, all process actions DISABLED, M12–M60 owner contracts PENDING/UNRATED, Issue #82 OPEN.
