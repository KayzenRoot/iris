# IRIS-WO-0017: exact-head bounded governance-guard audit target

Status: PENDING_EXACT_HEAD_GOVERNANCE_AND_SEPARATE_BOUNDED_REVIEW | Issue #118 | base `467cea12c78b875d8a9966e48bde2dade8d48f8a`.

## Required separate read-only checks

1. Git complete base source tree `ed1454de247b7ad26e186b55f999dfebcf74f0d4`, Context Lock 27/27 unique exact-base blobs and actual PR path set 11/11, no runtime/frozen contract/workflow changes. Check issue #118 scope and current Git base.
2. Reproduce old four-field-only source gap from `scripts/validate_governance.py` at base. Verify new helper checks byte-exact `.engineering/CHECKPOINT.md` versus `docs/project-brain/13-CHECKPOINT.md` **before** unchanged JSON canonical target/status/version/phase/nextStep and required seven heading checks; no dropped GEF/HIVE pins or bootstrap file checks.
3. Verify nine new regression tests have real inputs/assertions and all nine outcomes match: identical PASS, OBJECTIVE, IN PROGRESS, BLOCKERS, trailing LF, CRLF, JSON nextStep, JSON status and JSON canonical-target mismatches FAIL_CLOSED. Inspect actual GitHub exact-head Governance logs for those nine plus baseline, validator, bridge steps; do not infer process/OS tests from CLI CI.
4. Confirm earlier PR #117 exact-head #463 and exact-main #464 receipts (head `af1f4da285be2177c6bb7afbba4a41866b112231`, protected merge `467cea12c78b875d8a9966e48bde2dade8d48f8a`) are exactly reconciled in all three checkpoints and `IRIS-WO-0015.json`, with C09 documentary semantics and six LV still unexecuted. No owner disposition #110 inferred.
5. New diff-specific HIGH/CRITICAL must be zero before APPROVED. Pre-existing four HIGH_FOR_FUTURE_FREEZE blockers H01–H04 remain OPEN/OUTSIDE_THIS_MAINTENANCE_SCOPE. Check all 86 questions still OPEN/UNRATED, M09 v1.0 frozen 83/15/514, M11 v0.2 not frozen, process actions DISABLED, implementations NOT_ADMITTED and #82/#110/#112 OPEN.

## Verdict format and STOP
Review exact commit SHA and matching complete Context Lock; state 9-test and full-suite exact logs, risk, scope, findings with source and APPROVED / CORRECTION REQUIRED / BLOCKED. A later pass by the same assistant is not an independent human review. No silent merge before a separately recorded scoped audit. If APPROVED and exact-head remains unchanged, guarded protected squash merge followed by exact-main Governance; receipt-only future PR prohibited.
