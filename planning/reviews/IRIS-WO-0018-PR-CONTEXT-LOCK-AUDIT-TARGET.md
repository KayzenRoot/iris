# IRIS-WO-0018: separate exact-head PR Context Lock verification audit

Status: PENDING_FINAL_HEAD_GOVERNANCE_AND_SEPARATE_BOUNDED_AUDIT | Issue #120
Exact-base `407078499027253703ee09ec986832095d355b0f` / tree `b1c4d9db004f152acf2cdfabf689c73566be1d78`.

## Mandatory independent checks

- Verify new lock 30/30 unique base source SHA-1 hashes including all eight mandatory source hierarchy roots via full Git base tree; actual changed filenames strictly within its 12 authorized paths; no historical lock rewrite, frozen-contract or product-runtime changes. Compare `main` and final PR head at review time.
- Source-review `scripts/verify_context_lock.py` for secure/strict SHA, canonical paths, duplicate JSON key rejection, exact base/tree/ancestry, Git object source verification and real changed path allowlist. Ensure no GitHub API token, symlink traversal, executing untrusted JSON, hidden writes or external owner authority.
- Verify checkout `fetch-depth: 0` is required for local base commit; PR-only job step takes GitHub event trusted `base.sha`/`head.sha`, compiles and executes verifier, while protected push-main remains unaffected and existing governance+bridge suite runs.
- Confirm 19 deterministic cases include actual local Git commits for positive, unauthorized diff, absent lock and incorrect HEAD, not just fake hash strings. Check exact-head CI logs and count baseline 3,949 + newly added tests. Do not claim local GPU/OS/M09/M11 verification.
- Confirm WO0017 PR #119 Governance #466/#467 exact receipts reconciled with failure #465 historical retained. Markdown checkpoints byte-identical and machine JSON nextStep exactly equal.
- No change to M09 v1.0, M09 C01 proposal A/B/C undecided, M11 v0.2 nonfrozen; four C02 HIGH_FOR_FUTURE_FREEZE blockers and 86/86 questions remain OPEN. #110 needs actual owner disposition independent from this improvement.

## Verdict and STOP
APPROVED / CORRECTION REQUIRED / BLOCKED with exact final head SHA, changed paths, regression count and reviewer limitation (separate assistant pass is not a separate human). Any HIGH/CRITICAL introduced must be corrected in same PR and rerun exact-head CI. Merge only the audited unchanged head through protected squash then verify exact-main Governance; issue #120 close only after exact-main.
