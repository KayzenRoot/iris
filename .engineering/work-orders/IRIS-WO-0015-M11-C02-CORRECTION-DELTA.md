# IRIS-WO-0015 — M11 C02 Correction Delta

Status: ADMITTED_FOR_DOCUMENTATION_CORRECTION_ONLY | Risk: ELEVATED | Issue #82 OPEN
Base: 6006be5af8f58ac6eec00df030fffab2d1d121ab / 039f6fc7e4d89a20af830bdd09ad994a8a26ee58; branch iris-wo-0015-m11-c02-correction-20260926

## OBJECTIVE
Respond to audit C01 HIGH_FOR_FREEZE findings AUD-C01-H01..H03 with only M11-owned minimal positive semantic input/preflight, process-capability and recovery uncertainty interfaces. Maintain process actions DISABLED until versioned M12/M54/M60 owner proofs exist. Propose m11-contract-candidate-v0.2, not freeze.

## CONTEXT / FILES TO READ
Exact Git state, Source Hierarchy, checkpoint, Decisions, Scope, DoD, Architecture, Requirements, candidate C01 and audit C01, S01-S05 source research, FTR/FCS, available M02/M06/M09/M10 owner contracts and master index. 32 exact Git blob fingerprints bind this base. IRIS derived context cannot replace Git.

## SCOPE / REQUIREMENTS
Extend existing candidate with C02 annex, preserve I01-I26 and verbatim original 44 S04/S05 open questions, add I27-I36 and 8 future proof obligations. Define bounded logical records for required owner evidence, positive/negative preflight, scoped process capability and ordered incomplete control/recovery evidence. Update checkpoint, evidence, backlog and module plan. No new runtime, APIs or external owner decisions.

## OUT OF SCOPE / ARCHITECTURE RULES / CONSTRAINTS
Do not select process topology/IPC/OS adapter, M54 principal or policy, M12 placement, M60 platform rights, M09 lease schema, timeout/priorities/headroom numbers, automatic retry, storage deletion, attempt success, freeze or M10/M11 implementation. Do not change frozen M10. Missing owner proofs are UNSUPPORTED/NOT_ADMITTED, never permissive.

## ACCEPTANCE CRITERIA / TESTS
Exact 10-file allowlist, 32/32 unique base fingerprints, all 26 prior + ten new unique invariant IDs, all original S04 21/21 + S05 23/23 question text byte-preserved in C02 candidate, explicit H01/H02/H03 proof mapping, valid JSON and checkpoint mirrors, git diff --check, repository governance validator, pinned GEF/IRIS bridges, 3,940/3,940 exact-head suite. Re-audit positive semantics separately; passing docs CI never establishes OS safety or authorizes worker action.

## DELIVERABLES / REVIEW FORMAT
One bounded C02 Correction Delta PR on this same Work Order, Context Lock, Evidence Bundle, v0.2 candidate, checkpoint delta, tests/evidence, Brazilian Portuguese review. Freeze requires a separate independent audit after this PR is merged/exact-main validated.

## STOP CONDITION
Stop after exact-head Governance and PR OPEN/UNMERGED, or earlier on stale lock/scope/mirror/tests or unresolved critical factual conflicts. No finding may be marked discharged, no contract frozen, no runtime/IPC/resource action, no Issue #82 closure and no subsequent implementation increment before re-audit.

## AUTHORIZED FILES
- `.engineering/CHECKPOINT.json`
- `.engineering/CHECKPOINT.md`
- `.engineering/context-locks/IRIS-WO-0015-M11-C02-CORRECTION-DELTA.json`
- `.engineering/evidence/IRIS-WO-0015.json`
- `.engineering/work-orders/IRIS-WO-0015-M11-C02-CORRECTION-DELTA.md`
- `.engineering/work-orders/IRIS-WO-0015-M11-PLANNING.md`
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/14-BACKLOG.md`
- `planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md`
- `planning/modules/M11-BACKGROUND-WORKER-FABRIC-PROCESS-LIFECYCLE.md`
