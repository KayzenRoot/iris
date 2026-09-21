# IRIS-WO-0005 — GitHub Repository Hardening

Status: `READY_FOR_EXECUTOR`
Risk: `ELEVATED`
Issue: `#13`
Branch: `iris-wo-0005-github-hardening`
Authorized base: `732895d17ead7a1497985a3a98396f4f2aa975d2`

## OBJECTIVE

Configure `KayzenRoot/iris` as a professionally governed GitHub repository before M03 by making GitHub enforce the approved IRIS development workflow through an active `main` ruleset, safe repository merge defaults, least-privilege Actions defaults and available security protections.

## CONTEXT

M02 is merged and validated on `main` at `732895d17ead7a1497985a3a98396f4f2aa975d2` with Governance run `35596884279`, job `106323644504`, and 1805/1805 tests OK.

The ChatGPT GitHub connection proved that `main` is not protected and the repository has no rulesets. It can review and mutate repository files but cannot write Administration/ruleset endpoints. Therefore server-side hardening is `EXECUTOR_REQUIRED` and must be performed locally by Codex with authenticated `gh`.

The repository-canonical review rule remains: first fix `CHAT_FIXABLE` findings directly in the active PR; use a Codex correction only for genuinely `EXECUTOR_REQUIRED` work.

## SCOPE

NECESSARY:
- verify exact Git/gh/admin preconditions before mutation;
- capture BEFORE administrative state;
- apply the desired repository settings manifest;
- create or update one repository ruleset `main-governance` for `refs/heads/main`;
- require PR workflow + squash-only merge + Governance check + linear history + resolved review threads;
- prevent deletion and non-fast-forward updates of `main`;
- enable auto-merge capability, Update branch and automatic deletion of merged head branches;
- set Actions default workflow permissions to read-only and disallow workflows approving PR reviews by default;
- enable vulnerability alerts, automated security fixes, secret scanning and push protection where supported;
- add missing professional security/dependency hygiene files only as defined by this Work Order;
- capture AFTER state and objective evidence;
- update the Evidence Bundle and proposed Checkpoint Delta;
- push/update the same branch and PR;
- stop for independent review.

## OUT OF SCOPE

- M03 planning or implementation;
- product/kernel changes;
- classic branch protection in parallel with an active ruleset;
- GitHub organization-level policy;
- merge queue;
- mandatory signed commits;
- mandatory human approval count;
- mandatory CODEOWNER approval;
- last-pusher approval;
- CodeQL workflow/ruleset expansion;
- license/visibility changes;
- broad label/project/wiki cleanup;
- force push, history rewrite or destructive cleanup;
- merging this Work Order.

## FILES/SOURCES TO READ

Read in this order:
1. `.engineering/SOURCE-HIERARCHY.md`
2. `.engineering/REVIEW-AUTOFIX-POLICY.md`
3. `docs/project-brain/13-CHECKPOINT.md`
4. `docs/project-brain/16-DECISIONS-LEDGER.md`
5. `docs/project-brain/03-SCOPE.md`
6. `docs/project-brain/15-DEFINITION-OF-DONE.md`
7. `docs/project-brain/04-ARCHITECTURE.md`
8. `docs/project-brain/02-REQUIREMENTS.md`
9. `.engineering/github/REPOSITORY-HARDENING.md`
10. `.engineering/github/repository-settings.desired.json`
11. `.engineering/github/main-governance.ruleset.json`
12. `.engineering/context-locks/IRIS-WO-0005.json`
13. `.github/workflows/governance.yml`
14. `.github/CODEOWNERS`
15. `.github/PULL_REQUEST_TEMPLATE.md`

## REQUIREMENTS

### Preflight
- `git status --short` must be understood; do not discard user work.
- `git remote -v` must point to `KayzenRoot/iris`.
- fetch origin; do not rewrite history.
- branch must be `iris-wo-0005-github-hardening`.
- verify merge base with `origin/main` is authorized base `732895d17ead7a1497985a3a98396f4f2aa975d2`; if main moved, STOP `STALE_CONTEXT` and report the new SHA.
- `gh auth status` must succeed.
- `gh api repos/KayzenRoot/iris --jq '.permissions.admin'` must be `true`; otherwise STOP `BLOCKED_ADMIN_PERMISSION`.
- read current rulesets and branch rules before any mutation.

### BEFORE evidence
Record raw or normalized JSON for:
- repository settings;
- `main` branch/protection/rules as readable by `gh`;
- repository rulesets;
- Actions workflow permissions;
- vulnerability/security-analysis capability/status;
- current PR/check state once PR exists.

Do not record tokens, credentials or secrets.

### Repository settings
Apply `.engineering/github/repository-settings.desired.json` idempotently through `gh api`. Preserve values outside the manifest unless a documented platform dependency forces a change.

### Main ruleset
Use the repository Rulesets REST API through `gh api`.
- Upsert by exact name `main-governance`; never create duplicates.
- If absent, create it initially with enforcement disabled, read it back, then activate after validation.
- If present, compare normalized desired/current JSON and patch only the delta.
- Conditions must match only `refs/heads/main`.
- Required status context is exactly `Governance`; prove that the current PR actually emits this check before activation.
- Do not add bypass actors.
- Do not require signed commits.
- Do not add classic branch protection unless rulesets are unavailable; if unavailable, STOP and return the explicit compatibility finding before using a fallback.

### Actions/security
- default workflow permission = read;
- workflows cannot approve PR reviews by default;
- enable vulnerability alerts + automated security fixes when supported;
- enable secret scanning + push protection when supported;
- a 403/404/422 caused by plan/platform unavailability must be classified and evidenced, not hidden.
- availability limitations that do not weaken the main ruleset may be recorded `NOT_AVAILABLE`; an inability to enforce the main ruleset is BLOCKED.

### Repository files
If absent:
- add `.github/SECURITY.md` with GitHub private vulnerability reporting as the preferred path if available, otherwise instruct reporters to use a private channel without inventing contact data;
- add `.github/dependabot.yml` for `github-actions` weekly updates.
Do not add package ecosystems without an actual package manifest.

### PR and CI
- commit/push only to the Work Order branch;
- open or update one PR targeting `main`, linked to Issue #13;
- never merge;
- run/observe repository validation;
- after ruleset activation run `gh ruleset check --default -R KayzenRoot/iris`;
- run `gh pr checks --required` and prove `Governance` is required and green;
- verify API state after every administrative mutation.

## ARCHITECTURE RULES

- Git is canonical for desired policy manifests and evidence; GitHub server state is the enforced projection.
- One `main-governance` ruleset is the protection source of truth.
- Avoid overlapping/contradictory classic protection.
- Admin mutations must be idempotent and replayable from desired manifests.
- Fail closed on ambiguous admin state.
- Preserve single-owner automation: CI/PR enforcement is mandatory; human approvals are not mandatory in this increment.
- Keep Actions least-privilege.
- Do not claim a security feature is enabled without reading it back.
- Do not store auth material in Git/evidence.

## CONSTRAINTS

- No force-push.
- No direct `main` mutation.
- No branch/ruleset deletion.
- No history rewrite.
- No visibility/license change.
- No M03.
- Do not weaken the Governance workflow or review auto-fix policy.
- Do not silently broaden scope.
- Use GitHub API version supported by the installed `gh`; for direct REST headers prefer current documented API version and record it in evidence.
- If local main/base differs from Context Lock, STOP `STALE_CONTEXT`.

## ACCEPTANCE CRITERIA

1. Exact authorized base/context preflight proved.
2. BEFORE state captured without secrets.
3. Desired repository merge settings read back exactly.
4. `main-governance` exists exactly once and is active.
5. Ruleset targets only `refs/heads/main`.
6. Ruleset prevents deletion and non-fast-forward updates.
7. Ruleset requires linear history.
8. Ruleset requires PRs and allows squash only.
9. Ruleset requires resolved review threads.
10. Ruleset requires exact `Governance` status check with strict current-base policy.
11. No mandatory human approval/CODEOWNER/last-pusher rule creates a single-owner deadlock.
12. Auto-merge capability, Update branch and delete-branch-on-merge are enabled.
13. Actions default workflow permissions are read-only; Actions PR approval is disabled.
14. Available requested security features are enabled and read back; unsupported ones are explicitly evidenced.
15. `gh ruleset check --default` reports the intended rules.
16. `gh pr checks --required` shows `Governance` required and green on the Work Order PR.
17. Repository Governance exact-head CI passes; existing suite remains green.
18. Evidence Bundle contains before/after administrative snapshots, command outcomes, ruleset ID/config, PR/head SHA, risks and rollback posture.
19. Checkpoint Delta is proposed but not promoted by executor.
20. PR remains unmerged and M03 remains unstarted.

## TESTS

Required:
- `python -m py_compile scripts/validate_governance.py scripts/gef_preflight.py scripts/hive_bootstrap.py scripts/hive_mcp.py`
- `python scripts/validate_governance.py`
- `python -m unittest discover -s tests -p "test_*.py"`
- `gh pr checks <PR> --watch` or equivalent deterministic wait until completion;
- `gh pr checks <PR> --required`;
- `gh ruleset list -R KayzenRoot/iris`;
- `gh ruleset view <ID> -R KayzenRoot/iris`;
- `gh ruleset check --default -R KayzenRoot/iris`;
- REST readback of repository merge settings;
- REST readback of Actions workflow permissions;
- REST readback of available security settings;
- exact diff proving product/kernel code was not changed.

## DELIVERABLES

- repository hardening changes on `iris-wo-0005-github-hardening`;
- desired-state manifests already present under `.engineering/github/`;
- `.github/SECURITY.md` if absent and supportable without invented contact details;
- `.github/dependabot.yml` for GitHub Actions if absent;
- updated `.engineering/evidence/IRIS-WO-0005.json`;
- proposed Checkpoint Delta;
- Git commit(s) and push;
- one PR linked to Issue #13;
- server-side GitHub hardening applied through `gh`;
- executor review summary in Brazilian Portuguese.

## REVIEW FORMAT

Return in Brazilian Portuguese:
- preflight/base/auth result;
- files changed;
- exact GitHub settings before/after;
- ruleset ID and normalized effective rules;
- Actions/security settings before/after;
- tests/CI and exact SHAs;
- unsupported feature limitations;
- risks/rollback posture;
- PR number/URL;
- Evidence Bundle path;
- STOP CONDITION result.

## STOP CONDITION

STOP only when repository-side files and server-side hardening are applied, read back, tested and evidenced, the PR exact head is green and ready for independent review.

DO NOT MERGE.
DO NOT START M03.
DO NOT bypass a failing required check.
If Administration permission is unavailable, STOP `BLOCKED_ADMIN_PERMISSION` before partial server mutation.
If the base or a critical source is stale, STOP `STALE_CONTEXT`.
