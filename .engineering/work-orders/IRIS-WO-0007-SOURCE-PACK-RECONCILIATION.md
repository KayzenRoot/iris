# IRIS-WO-0007 — Canonical Source Pack Reconciliation Before M04

Status: `EXECUTED_PENDING_AUDIT`
Risk: `STANDARD`
Issue: `#24`
Branch: `iris-wo-0007-source-pack-reconciliation`
Authorized base: `d65df7f239627f99941896451340f43ee1a887fd`

## OBJECTIVE

Reconcile stale canonical Source Pack statements so the repository truth is internally consistent with the approved `M04_PLANNING_READY` checkpoint before M04 deep planning begins.

## CONTEXT

The canonical checkpoint already records M01-M03 as implemented/merged and M04 planning-ready, while several lower-priority Source Pack documents still describe bootstrap-only or M03-planning state. Source Hierarchy declares stale/conflicting authoritative sources blocking.

## SCOPE

- update Project Overview current phase truth;
- update Scope to the admitted M04 planning increment;
- update Architecture to record frozen M01/M02/M03 authority layers and the planned M04 boundary;
- update Integration Contracts status/boundaries without inventing CORE runtime contracts;
- update Test/Benchmark Plan to the actual pre-M04 semantic-kernel baseline;
- update Local Deployment to distinguish semantic foundations from unavailable product runtime deployment;
- update Backlog to the current M04 queue and explicitly record unresolved M00 planning debt without inventing completion;
- add bounded Work Order / Context Lock / Evidence for this reconciliation.

## OUT OF SCOPE

- M04 S01-S05 deep planning;
- M04 implementation;
- any product/kernel code;
- provider/model/DCC runtime selection or execution;
- changing frozen M01/M02/M03 contracts or authority;
- declaring M00 complete without approved evidence;
- broad documentation cleanup.

## FILES / SOURCES TO READ

1. `docs/project-brain/13-CHECKPOINT.md`
2. `docs/project-brain/16-DECISIONS-LEDGER.md`
3. `docs/project-brain/03-SCOPE.md`
4. `docs/project-brain/15-DEFINITION-OF-DONE.md`
5. `docs/project-brain/04-ARCHITECTURE.md`
6. `docs/project-brain/02-REQUIREMENTS.md`
7. `.engineering/SOURCE-HIERARCHY.md`
8. `.engineering/REVIEW-AUTOFIX-POLICY.md`
9. `planning/MASTER-MODULE-INDEX.md`
10. `planning/compatibility/M03-FORWARD-COMPATIBILITY-SCAN.md`

## REQUIREMENTS

- canonical current-state statements MUST agree with the checkpoint;
- lower-priority backlog MUST NOT override checkpoint state;
- M00 MUST remain unresolved unless evidence explicitly proves its freeze;
- M01 quality authority, M02 project/graph/release/ExecutionPlan authority and M03 creative-semantic authority MUST remain unchanged;
- M04/M16 provider-compiler overlap MUST remain a planning question, not be silently implemented;
- no product code or runtime dependency may change.

## ARCHITECTURE RULES

- M04 is planned as provider-neutral detailed multimodal/scene IR.
- M04 consumes M03 admitted semantic intent rather than redefining it.
- M04 cannot duplicate M01 quality decision authority or M02 execution/project authority.
- Concrete provider/workflow compilation remains future M16 ownership unless later approved planning changes that boundary.
- HIVE remains derived context; Git/Project Brain remain canonical.

## CONSTRAINTS

- no force push/history rewrite;
- protected-main squash PR flow only;
- no Codex escalation while the correction remains safely CHAT_FIXABLE;
- do not expand into M04 deep planning during this increment.

## ACCEPTANCE CRITERIA

1. No canonical Source Pack file states that bootstrap or M03 planning is the current phase.
2. Scope truthfully names M04 planning as the admitted next product increment.
3. Architecture records the already-frozen M01/M02/M03 boundaries.
4. Backlog does not falsely declare M00 complete and does not block M04 contrary to the checkpoint.
5. Test plan records the verified 2527-test pre-M04 baseline without inventing M04 thresholds.
6. Deployment truthfully distinguishes semantic packages from absent product runtime.
7. No product/kernel file changes.
8. Governance exact-head PASS and full suite remains green.
9. Independent review finds no HIGH/CRITICAL blocker.

## TESTS

- inspect PR diff for docs/governance-only scope;
- `python scripts/validate_governance.py`;
- `python -m unittest discover -s tests -p "test_*.py"`;
- exact-head GitHub Governance;
- post-merge exact-main Governance.

## DELIVERABLES

- reconciled canonical Source Pack documents;
- Work Order;
- Context Lock;
- Evidence Bundle;
- PR linked to Issue #24;
- independent review result in Portuguese;
- post-merge main validation.

## REVIEW FORMAT

Report: findings, canonical conflicts repaired, changed files, tests/Governance, remaining planning debt, blockers, verdict and STOP CONDITION.

## STOP CONDITION

STOP when the bounded Source Pack reconciliation is independently APPROVED, squash-merged through `main-governance`, and the resulting exact `main` passes Governance. Only then may M04 S01 deep planning begin.
