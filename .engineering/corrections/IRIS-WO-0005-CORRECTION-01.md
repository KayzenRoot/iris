# IRIS-WO-0005 — Correction Delta 01

Status: `EXECUTOR_REQUIRED`
Finding: `IRIS-WO-0005-C01`
Severity: `MEDIUM` (merge-blocking)
PR: `#14`
Branch: `iris-wo-0005-github-hardening`
Reviewed head: `3c242487c65fef3f189135374e9ec79af934f525`

## FINDING

The repository hardening is not yet complete because the executor classified vulnerability alerts as `NOT_AVAILABLE` after calling the enable endpoint with the wrong HTTP method.

Recorded command:
`gh api -X POST repos/KayzenRoot/iris/vulnerability-alerts` -> 404.

GitHub's REST contract uses **PUT** to enable repository vulnerability alerts. A GET 404 means the feature is not enabled. It does not prove the feature is unavailable.

The subsequent automated-security-fixes request returned 422 because vulnerability alerts remained disabled, which is consistent with this root cause.

## CLASSIFICATION

`EXECUTOR_REQUIRED`.

Chat can correct repository evidence/docs, but this GitHub connection cannot perform repository Administration writes to the vulnerability-alerts / automated-security-fixes endpoints.

## CORRECTION SCOPE

Perform only this bounded server-side correction plus evidence/CI refresh.

1. Confirm the same authorized repository/account and that PR #14 still targets `main`.
2. Do not alter the already-correct `main-governance` ruleset or repository merge settings unless readback proves drift.
3. Execute the correct enable request:
   `gh api -X PUT repos/KayzenRoot/iris/vulnerability-alerts`
4. Verify:
   `gh api -i repos/KayzenRoot/iris/vulnerability-alerts`
   Expected enabled response: HTTP 204.
5. Then execute:
   `gh api -X PUT repos/KayzenRoot/iris/automated-security-fixes`
6. Read back automated security fixes and record the actual result.
7. If either correct PUT fails, capture HTTP status/body and permission context. Do not reinterpret a failure as NOT_AVAILABLE without evidence matching GitHub's documented contract.
8. Update `.engineering/evidence/IRIS-WO-0005.json`:
   - status -> `READY_FOR_REVIEW` only if the correction succeeds or a genuinely unsupported state is objectively proven;
   - AFTER security state from readback;
   - exact commands/results;
   - limitations;
   - risks;
   - proposed Checkpoint Delta;
   - STOP CONDITION.
9. Commit and push to the same branch/PR.
10. Run/observe:
   - `python scripts/validate_governance.py`
   - `python -m unittest discover -s tests -p "test_*.py"`
   - `gh pr checks 14 -R KayzenRoot/iris --required`
11. STOP before merge and before M03 for independent review.

## OUT OF SCOPE

- changing product/kernel code;
- changing the existing main-governance ruleset unless objective drift is found;
- changing merge strategy/settings already read back correctly;
- broad repository cleanup;
- merging PR #14;
- starting M03.

## ACCEPTANCE CRITERIA

- vulnerability alerts enable/readback uses the documented PUT flow;
- automated security fixes are retried only after alerts are enabled;
- final state is objectively read back;
- evidence contains no false NOT_AVAILABLE claim;
- exact-head Governance and all 1805 tests are green;
- required `Governance` check is green;
- PR #14 remains unmerged;
- M03 remains unstarted.

## STOP CONDITION

STOP at `READY_FOR_INDEPENDENT_REVIEW` after the bounded correction is pushed, read back, evidenced and green. Do not merge.
