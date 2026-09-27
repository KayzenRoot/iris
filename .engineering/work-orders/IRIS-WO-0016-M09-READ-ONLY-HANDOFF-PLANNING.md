# IRIS-WO-0016 — M09 read-only owner-evidence handoff planning

Status: **PROPOSED_FOR_PLANNING_ADMISSION** until this Work Order passes separate scoped audit, protected merge and exact-main Governance. Thereafter **ADMITTED_FOR_PLANNING_ONLY**; this conditional admission is not implementation or a frozen-contract amendment.
Risk: ELEVATED
Issue: #112 | Upstream M09 owner review #110 | M11 dependency #82
Source base: `7cdfa0015eaf67bac570deea67177239bb4549af` | exact tree `6030279a39a95920c6e1e5ef7288ecfce1818239`
Branch: `iris-wo-0016-m09-handoff-planning-admission-20260927`
Existing frozen owner contract: `m09-contract-v1.0` (unchanged)
M09 implementation and M11 runtime extension: NOT_ADMITTED

## Purpose

Determine the narrowest owner-controlled, read-only way for future M11 to verify resource admission facts without taking M09's resource, grant, lease, revocation or residency authority. This is an independent M09-owned **planning** track, not a sub-order that lets M11 silently rewrite M09. M09 v1.0's 83 mandatory surfaces, 15 absorbed components, 514 invariant proofs, 14 FC-09 handshakes and 3,940-test repository baseline remain frozen and unchanged. Preserve S03-U08 and all M11 questions OPEN and risk UNRATED until their actual independent owner decisions.

## Authority and source admission

Git exact base → canonical Checkpoint → Decisions Ledger → Scope/DoD/Architecture/Requirements → canonical `docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md`, `planning/compatibility/M09-FORWARD-COMPATIBILITY-SCAN.md`, `IRIS-WO-0013` → actual `iris_resource_twin/` API → M11 v0.2 candidate and research → #110/#112. Source audit cannot itself be an M09 owner verdict. FC-09-09's generic versioned public evidence projection and M09's audit `EvidenceBundle` are **not** assumed to be an action-scoped resource-grant verifier.

This proposal's Context Lock pins **68/68** unique exact-base Git blob SHAs, and its ten-path allowlist contains only checkpoint/evidence/planning/Work Order documentation. PR-head Governance, a separate bounded review of admission and risk, protected squash promotion and exact-main Governance are mandatory.

## Permitted planning activities

1. Compare **A**: existing single-authority in-process, read-only typed M09 reads; **B**: a future versioned, owner-issued, read-only immutable per-request grant-evidence receipt and verifier; **C**: negative-only evidence projection with no positive grant path pending owner infrastructure. Analyze TOCTOU and races. No alternative is selected solely from a Python public export.
2. Build a versioned **proposal** for M09-owned evidence fields and distinct original observation, grant-state, denial, unsupported and unverified outcomes. Maintain exact M02 accepted-work reference, resource and requested action/target/scope, owner provenance, current lease epoch/state/revocation and freshness with explicit trust/transport/clock uncertainty, as future owner decisions, **not existing M09 port claims**.
3. Design an atomicity or explicit conservative invalidation proof for snapshot-plus-lease consistency, including in-process locks being independent. Cross-process, failover and external serialization depend on admitted owner-defined security, placement, OS/platform and storage policy.
4. Define deterministic proof obligations and a source-backed freeze-readiness delta without executing fake OS/GPU/live worker tests. Plan how to regression-check all 514 existing invariants **without editing** their frozen catalog.
5. Request source-backed M09 owner disposition in #110, documenting whether existing API suffices under a narrowly proven topology or a separately admitted **additive extension contract** is necessary. Future M12 placement, M54 security and M60 OS capability stay independently PENDING.

## Explicit prohibitions

No edits to `iris_resource_twin/`, existing frozen M09 docs/contract/invariants/tests, M11's contract or live worker code under this planning admission. No selected wire format, crypto algorithm, IPC transport, optimistic distributed-lock assumption, global lease epoch, clock tolerance, default TTL, rights delegation, resource mutation or system deployment is conferred. Do not count a docs CI pass as a negative safety test or permission to dispatch. A proposed receipt is not a new M09 API.

## Completion/STOP for this admission increment

Produce source-locked research/preflight with options and negative proof obligations, this conditional Work Order, separate review candidate, independent review and exact-head and exact-main green evidence. Once merged+validated, WO0016 is **admitted for planning only** so a later, separately reviewable owner-extension contract candidate may be drafted and audited. It remains **NOT_FROZEN**, implementation NOT_ADMITTED and #110/#112 OPEN until owner-reviewed. S03-U08 and the original 86 questions OPEN/UNRATED, eight PO-C02 and ten C08 scenarios NOT_EXECUTED, M11 v0.2 NOT_FROZEN, process actions DISABLED, M12–M60 PENDING/UNRATED and #82 OPEN. Do not claim an M09 owner adoption by this PR.
