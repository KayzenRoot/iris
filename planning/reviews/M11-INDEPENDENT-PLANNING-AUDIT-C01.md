# M11 C01 Separate Planning Audit: Versioned Owner-Contract Candidate

Status: CORRECTION_REQUIRED_FOR_FREEZE — report proposal subject to exact-head Governance and governed merge
Candidate under review: `m11-contract-candidate-v0.1` (PR #101 exact head `2df777a14aaac9bdb673f9c812c75a5af188b31d`)
Exact reviewed main: `9c7cafcfc73700728981f8f90e27110be8dd9fd0` / tree `b1b3084905b6f5f81212fcafce3b6509a3d02832`; candidate protected squash merge `9c7cafcfc73700728981f8f90e27110be8dd9fd0` passed exact-main Governance #438 (run 36285702518 / job 108525960964; 3,940/3,940 tests in 15.684s).
Reviewer context: separate read-only chat review of the previously authored/merged C01 proposal; the same KayzenRoot GitHub credential is used, and no independent human identity or formal GitHub approval is claimed.

## 1. Scope and evidence

Read source hierarchy, checkpoint, Decisions, Scope, DoD, Architecture, Requirements, frozen/available M02/M06/M09/M10 owners, M11 S01-S05 research, Final Technology Review, corrected 30-row FCS/49 owner-index rows, candidate C01, Work Order and Issue #82. The merged candidate's 94/94 exact-base lock and ten-path diff passed bounded review; Governance #436 passed on its exact head; exact-main Governance #438 passed after protected merge. These document tests are not real OS, GPU, IPC, recovery or authorization proof.

Independently checked 26 distinct M11-I01..I26 candidate invariant identifiers and the verbatim original S04 21/21 plus S05 23/23 question texts. The candidate does not falsely claim that M12–M60 owner-specific contracts exist. The 49 future owner entries remain INDEX_ONLY / PENDING_OWNER_CONTRACT / risk UNRATED; S01–S03 decisions also remain open. Audit assesses readiness for a safe owner-contract freeze, not the previously approved bounded drafting increment.

## 2. Audit verdict

**CORRECTION REQUIRED for contract freeze**: three distinct HIGH_FOR_FREEZE positive-contract gaps, zero observed CRITICAL *runtime* findings because there is no admitted runtime in this increment. This does not mean runtime security or cross-module risk is zero. Do not freeze M11 or admit M11/M10 implementation. Retain Issue #82 OPEN and m10-contract-v1.0 FROZEN; WO-0014 BLOCKED. Candidate C01 remains a valid versioned draft, not an executable interface.

## 3. Trace across 26 invariants

| Invariants | Subject | Disposition | Evidence / remaining work |
|---|---|---|---|
| I01–I03 | Owner separation for M02/M06 | BOUNDARY_SUPPORTED | M02/M06 frozen contracts; no process-as-attempt equivalence |
| I04–I05 | Process identity, ownership and foreign-process control | OPEN_FREEZE_H02 | S04-U03..U11 and S05-U22 require positive OS handle/wait-right proof |
| I06–I08 | M10 advisory versus M09 resource authority | BOUNDARY_SUPPORTED | m10-contract-v1.0; m09-contract-v1.0; no resource grant inferred |
| I09–I10 | Startup prerequisites, M12 placement, M54 principal | OPEN_FREEZE_H01 | S04-U01/U18; S05-U01/U20; M12/M54 owner contracts pending |
| I11–I14 | Action states, timeouts, crash recovery, duplicate effects | OPEN_FREEZE_H03 | S05-U02..U14/U21 and M06 attempt port require positive semantics |
| I15–I17 | Shell-free trust, platform and numeric policies | OPEN_OWNER_PROOFS | S04-U10/U13..U15; S05-U19/U23; M54/M60 pending; no runtime admission |
| I18–I20 | Downstream acceptance, principal, provenance | BOUNDARY_SUPPORTED_WITH_PENDING_PORTS | M01/M06/M53..M60 owners preserved; concrete handoffs pending |
| I21–I26 | Git authority, admission, unresolved decisions, audit and non-regression | BOUNDARY_SUPPORTED | Source Hierarchy, issue #82, frozen M10 and open 44-question register |

## 4. Findings, corrective proof obligations and owners

### AUD-C01-H01 — HIGH_FOR_FREEZE: Missing positive authorization/preflight contract

**Observed gap:** Candidate §3 StartupPreconditions and §4 I09/I10/I19 decline implicit permission, correctly, but define no M11-owned validation result/field semantics for binding one exact action, principal decision reference, accepted M02 plan, M09 grant and pending M12 placement to a single request. M54 and M12 are index-only. A fail-closed boundary is necessary but insufficient to freeze a callable worker-start/control interface.

**Required correction and proof:** Define M11 semantic request/preflight/result records with explicit required evidence references, action/scope, version/freshness binding, DENIED/UNSUPPORTED/INDETERMINATE handling, and a non-bypassable verification handoff to future M54/M12. While those owner ports lack contracts, callable startup/control MUST stay DISABLED. Do not invent M54 principals, placement or M09 leases.

**Owners / source questions:** M11 / M02 / M09 / M12 / M54; S04-U01/U14/U18; S05-U01/U20.

### AUD-C01-H02 — HIGH_FOR_FREEZE: Unresolved positive process ownership and wait/reap safety

**Observed gap:** I04/I05 properly reject PID-only control and foreign process action, but WorkerAssociation and ProcessObservation have no owner-validated handle-lifecycle or capability proof that survives stale/reused identifiers, orphan reparenting and descendant breakaway. S04-U03..U11 and S05-U22 remain open.

**Required correction and proof:** Specify M11-owned capability-scoped identity/observation validity and deny/unknown semantics; define what is only an OS observation and what positive platform/parent/handle proof is required before a supported action. Delegate Windows/POSIX adapter guarantees to M60 and keep unsupported platforms disabled until independently proved.

**Owners / source questions:** M11 / M54 / M60; S04-U03..U11/U17; S05-U22.

### AUD-C01-H03 — HIGH_FOR_FREEZE: No replay-safe partial/cancel/recovery interface contract

**Observed gap:** I11..I14 distinguish cancellation intent, signal and exit and prohibit duplicate relaunch, but ControlIntent/ControlEvidence/RecoveryUncertainty have no minimal transition, idempotency-reference or uncertain-outcome interface required to prevent false completion or repeated external effects. M06 ExecutionAttemptPort and M60 recovery ownership are unresolved.

**Required correction and proof:** Define versioned M11 observation/intent/result semantics that never auto-retry, never self-commit M06 attempts, emit explicit UNKNOWN/PARTIAL/UNSUPPORTED, and require M06/M60-issued idempotency and recovery authorization for any future retry/restart. Keep process actions disabled until those owner handoffs and OS proofs exist.

**Owners / source questions:** M11 / M02 / M06 / M09 / M54 / M60; S04-U04/U12/U20; S05-U02..U14/U21.


## 5. Explicitly open boundaries, not manufactured HIGH findings

- M12–M60: 49/49 INDEX_ONLY and PENDING_OWNER_CONTRACT; severity/risk UNRATED because individual contracts are missing. Revisit each on its own canonical contract; do not mark zero overall HIGH/CRITICAL or block an inert semantic boundary merely because headings exist.
- S04-U01..U21/S05-U01..U23: 44/44 still OPEN and verbatim in candidate C01. S01–S03 unresolved questions remain referenced in their original research files. No claim that all 44 require a new runtime policy now; resolve the M11-owned positive freeze-safety core and preserve others as explicit owner-dependent STOP conditions.
- HIVE registered state was stale during scan; GEF/HIVE CI bridge success establishes only pinned-bridge test success, never current derived project authority.

## 6. Minimal safe correction path

Use **the same IRIS-WO-0015** in a bounded C02 Correction Delta after this audit is governed. Add the minimum explicit M11 semantic preflight, process ownership/observation and control/recovery result contracts required by AUD-C01-H01..H03, retaining strict separation of M02/M06/M09/M10/M12/M54/M60 authority. Do not invent owner schemas or transport and do not enable worker actions. Require a new Context Lock, Evidence Bundle, exact-head Governance, a separate audit of the corrected head and zero remaining HIGH/CRITICAL *within the proposed freeze scope*. Freeze or implementation requires separate authority and gates. Treat any unproven safety premise as a disabled capability, not a permissive default.

## 7. Stop condition

Audit PR carries findings and checkpoint/evidence only. No contract edits, freeze, runtime, process/IPC operation, M09 lease mutation, issue closure or M10 implementation in this increment. Stop after exact-head Governance and bounded audit of this report; protected merge and exact-main Governance may promote the report, not the M11 contract.
