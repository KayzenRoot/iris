# IRIS GitHub Repository Hardening

Status: `EXECUTOR_READY`
Work Order: `IRIS-WO-0005`
Issue: `#13`
Authorized base: `732895d17ead7a1497985a3a98396f4f2aa975d2`

## Purpose

Make GitHub itself enforce the repository workflow already required by IRIS governance, without adding manual gates that deadlock the single-owner automation model.

## Current verified baseline

- `main` exact SHA: `732895d17ead7a1497985a3a98396f4f2aa975d2`.
- Post-merge Governance run/job: `35596884279 / 106323644504` — PASS.
- Full suite: `1805/1805 OK`.
- `main` legacy protection: disabled.
- repository rulesets: none.
- squash merge: enabled.
- merge commits: enabled.
- rebase merges: enabled.
- auto-merge: disabled.
- update-branch: disabled.
- delete-branch-on-merge: disabled.
- Governance workflow name/job: `Governance`.
- CODEOWNERS: `* @KayzenRoot`.
- Workflow permissions declared in `.github/workflows/governance.yml`: `contents: read`.

## Desired GitHub state

### Repository defaults
Apply `.engineering/github/repository-settings.desired.json` idempotently:
- keep `main` as default branch;
- allow squash merge only;
- enable auto-merge capability;
- enable Update branch;
- delete merged head branches automatically;
- PR title + PR body become the squash commit title/message;
- preserve visibility and unrelated feature toggles.

### Main protection
Use one active repository ruleset named `main-governance`, sourced from `.engineering/github/main-governance.ruleset.json`.

The ruleset protects `refs/heads/main` with:
- no branch deletion;
- no non-fast-forward/force push;
- linear history;
- PR required;
- squash as the only allowed merge method;
- review threads resolved;
- no required human approval count, CODEOWNER approval or last-pusher approval, because those gates would deadlock the authenticated single-owner automation flow;
- exact `Governance` status check required;
- strict status-check policy so the PR is tested against current base truth.

Do not create redundant classic branch protection when this ruleset is active. Classic branch protection is only an explicit fallback if repository rulesets are unavailable.

### Actions/security defaults
- repository Actions default workflow permission: read-only;
- workflows may not approve PR reviews by default;
- enable vulnerability alerts and automated security fixes when available;
- enable secret scanning and push protection when supported for this repository/account;
- unsupported plan/platform security features must be recorded as `NOT_AVAILABLE`, not bypassed or falsely claimed.
- keep workflow action versions SHA-pinned; do not weaken the current pins.

### Repository hygiene
- preserve current CODEOWNERS and PR template unless a concrete validation defect is found;
- add a minimal `.github/SECURITY.md` only if absent, with a private-reporting-first policy and no invented email/address;
- add `.github/dependabot.yml` for GitHub Actions if absent so pinned action SHAs can be maintained automatically; do not invent package ecosystems that have no manifest.

## Safe mutation order

1. Confirm authenticated `gh` admin access and exact repository.
2. Confirm local/remote branch is `iris-wo-0005-github-hardening` and its merge base is the authorized base.
3. Capture BEFORE snapshots of repository settings, rulesets, main rules, Actions permissions and security feature availability.
4. Add/update repository-side hardening files, tests/validation if needed, commit and push the Work Order branch, and open/update the PR.
5. Confirm the PR's `Governance` check exists and passes.
6. Apply repository defaults with `gh api`.
7. Upsert `main-governance` idempotently. Prefer creating/updating it disabled first, verify its JSON, then activate it.
8. Apply least-privilege Actions/security settings.
9. Verify with `gh ruleset list`, `gh ruleset view`, `gh ruleset check --default`, repository API reads and `gh pr checks --required`.
10. Capture AFTER snapshots and update Evidence Bundle.
11. Re-run/observe exact-head Governance.
12. STOP before merge for independent ChatGPT review.

## Safety constraints

- no force-push;
- no history rewrite;
- no direct push to `main`;
- no branch/ruleset deletion;
- no visibility change;
- no license change;
- no bypass actor added silently;
- no signed-commit requirement in this increment;
- no review requirement that makes the single-owner workflow impossible;
- no M03 work;
- if the token lacks Administration write permission, STOP `BLOCKED_ADMIN_PERMISSION` before partial server mutation.

## Rollback posture

Capture enough BEFORE state to restore repository settings if independent review finds a HIGH/CRITICAL regression. Do not execute rollback destructively without explicit authorization. A ruleset created by this Work Order may be disabled by an authorized correction if necessary; deleting it is not part of normal execution.
