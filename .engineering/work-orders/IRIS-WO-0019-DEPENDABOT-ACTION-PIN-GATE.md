# IRIS-WO-0019: strict Dependabot-only pinned action upgrade CI eligibility

Status: ADMITTED_FOR_BOUNDED_GEF_GOVERNANCE_MAINTENANCE_ONLY | Issue #122 | Risk: ELEVATED_CI_SECURITY
Exact base `32e1ecc3edd698460c34bce1f28045a20d53e804`, tree `5e3818a1719047f185c34aeb545d50ed7065f73a`, Governance #470 PASS 3968/3968. Branch `iris-wo-0019-dependabot-action-pin-guard-20260927`.

## SOURCE GATE
Read checkpoint, Decisions, Scope, DoD, Architecture, Requirements, security and admitted Work Order. Pin 32/32 unique exact-base Git blob SHA-1s. Current main Governance #470 succeeded; PRs #15/#16 failed #472/#471 solely on missing Context Lock despite changing only one pinned Actions SHA line. The strict WO0018 source/scope guard still applies to all human/other bot PRs.

## OBJECTIVE AND CHANGE SCOPE
Restore automated CI **eligibility** for authentic GitHub event `dependabot[bot]` same-repo `dependabot/github_actions/actions/` PRs with a single exact 40-char SHA pinned `uses: actions/checkout` OR `uses: actions/setup-python` version-line replacement. Verify actual Git HEAD/base ancestry, single file `.github/workflows/governance.yml`, base/head 100644 Git file mode, Git-produced exact diff with exactly one deleted and one added properly formatted line and unchanged action identity. All other content/modes/paths/bots reject; all other PRs require an exact source Context Lock including all eight hierarchy roots. This guard passes PR CI only; official-release trust/review and merge remain separate. Trusted bot metadata is taken from GitHub event, not PR-authored files.

## STRICT 12-PATH ALLOWLIST
- `scripts/verify_context_lock.py`
- `tests/test_dependabot_pin_guard.py`
- `.github/workflows/governance.yml`
- `.engineering/CHECKPOINT.json`
- `.engineering/CHECKPOINT.md`
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/14-BACKLOG.md`
- `.engineering/evidence/IRIS-WO-0018.json`
- `.engineering/evidence/IRIS-WO-0019.json`
- `.engineering/context-locks/IRIS-WO-0019-DEPENDABOT-ACTION-PIN-GATE.json`
- `.engineering/work-orders/IRIS-WO-0019-DEPENDABOT-ACTION-PIN-GATE.md`
- `planning/reviews/IRIS-WO-0019-DEPENDABOT-ACTION-PIN-AUDIT.md`

## REGRESSION, EVIDENCE AND STOP
Add 11 deterministic local-Git tests for setup-python/checkout positives plus wrong author, external repo, wrong branch, extra YAML, extra file, truncated SHA, switched action, mode change and changed checkout HEAD. Existing 3,968-suite baseline retained. Reconcile WO0018 #469/#470 receipts and seven administratively closed original-scope historical issues in the same substantive checkpoint/evidence increment. Submit exact-head Governance (new verifier + original 19 tests + 11 bot tests), separate bounded review with no introduced HIGH/CRITICAL before protected squash merge, then exact-main Governance. No auto-merge bot PRs, no M09/M11 product code, no contract/admission changes; #82/#110/#112 stay OPEN and owner decision #110 PENDING.
