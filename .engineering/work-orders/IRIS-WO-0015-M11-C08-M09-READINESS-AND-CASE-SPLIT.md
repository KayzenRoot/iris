# IRIS-WO-0015 C08: C07 closeout, M09 source audit, C06 missing-port case split

Status: ADMITTED_FOR_M11_PLANNING_DOCS_ONLY; risk: ELEVATED; Issue #82 OPEN
Base 33f9eb934db8a262a7ba705f5667f832c4abdca4 / tree 4c15513bae0f5e2312617de5beeb8cc4f9e43ba2
Branch: iris-wo-0015-m11-c08-m09-source-audit-c06-disposition-fix-20260927

## Objective
Reconcile C07 reviewed PR #111 exact-head Governance #453, protected merge 33f9eb934db8a262a7ba705f5667f832c4abdca4 and exact-main Governance #454. Source-audit M09 public in-process ResourceTwin and LeaseBook surfaces without fabricating a versioned M11 intermodule owner port. Fix AUD-C06-H01 HIGH_FOR_FUTURE_FREEZE_IF_UNCORRECTED: C06 draft S03U08-01 conflates owner port unavailable (UNSUPPORTED) with port available but no applicable owner proof (INDETERMINATE), which M11 v0.2 §9.1 distinguishes. Version the correction as new C08 evidence, retaining immutable original C06 and all 86 questions OPEN/UNRATED. Link open M09 source review #110 and proposed M09 extension-planning #112; neither is owner approval.

## Exact nine-path allowlist
- `.engineering/CHECKPOINT.json`
- `.engineering/CHECKPOINT.md`
- `.engineering/context-locks/IRIS-WO-0015-M11-C08-M09-READINESS-AND-CASE-SPLIT.json`
- `.engineering/evidence/IRIS-WO-0015.json`
- `.engineering/evidence/M11-C08-M09-READINESS-AND-CASE-SPLIT.json`
- `.engineering/work-orders/IRIS-WO-0015-M11-C08-M09-READINESS-AND-CASE-SPLIT.md`
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/14-BACKLOG.md`
- `planning/reviews/M11-C08-M09-SOURCE-READINESS-AND-C06-CORRECTION.md`

## Gates/STOP
60/60 base Git blob fingerprints, 9/9 allowlisted docs/evidence, checkpoint mirrors byte-exact. Ten C08 negative/non-admitting DRAFT_NOT_EXECUTED cases; preserve nine C06 historical scenarios and eight PO-C02 obligations NOT_EXECUTED. Distinguish ResourceTwin.admission_snapshot and LeaseBook.active from a verified exact-request resource grant; no M09 port, schema, freshness windows, IPC, OS or security policy selected. Exact-head Governance PASS and separate bounded audit required before guarded protected merge and exact-main PASS. STOP at PR OPEN/UNMERGED after proposal/CI. No owner decision, M09 frozen contract/code amendment, S03-U08 closure, M11 freeze, M10/M11 runtime admission, lease mutation, process action or Issue #82/#110 closure.
