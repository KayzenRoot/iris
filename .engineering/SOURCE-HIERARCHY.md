# IRIS Source Hierarchy

Status: `ACTIVE`

- REPOSITORY_STATE: exact Git state.
- PROJECT_STATE: `docs/project-brain/13-CHECKPOINT.md`.
- DECISION: `docs/project-brain/16-DECISIONS-LEDGER.md`.
- SCOPE: `docs/project-brain/03-SCOPE.md`.
- COMPLETION: `docs/project-brain/15-DEFINITION-OF-DONE.md`.
- ARCHITECTURE: `docs/project-brain/04-ARCHITECTURE.md`.
- REQUIREMENT: `docs/project-brain/02-REQUIREMENTS.md`.
- SECURITY: `docs/project-brain/10-SECURITY-GOVERNANCE.md`.
- VALIDATION: `docs/project-brain/11-TEST-BENCHMARK-PLAN.md` plus exact-head evidence.
- DEPLOYMENT: `docs/project-brain/12-LOCAL-DEPLOYMENT.md`.
- INTEGRATION: `docs/project-brain/05-INTEGRATION-CONTRACTS.md`.
- FUTURE_WORK: `docs/project-brain/14-BACKLOG.md`.
- ACTIVE_MODULE_INDEX: `planning/MASTER-MODULE-INDEX-CURRENT.md` (post-retirement, non-executable future M52/M60 supersession; the older frozen index is historical audit evidence).
- EXECUTION: currently scoped source-only Work Order `.engineering/work-orders/IRIS-WO-0067-CURRENT-TREE-TRANSITION.md` and Git-verified source lock `.engineering/context-locks/IRIS-WO-0067-STANDALONE-CURRENT.json` once its separate PR validates; neither is an admission for native module runtime.
- ORIGINAL_HISTORY: exact immutable Git commit `95d58dd7a3b1275f4aaff4f147f2be852ecad588` retains the original historical snapshots and full-suite baseline outside the current source working tree.
- ABI_TRANSITION: `docs/IRIS-SOURCE-ABI-MIGRATION.md`; renamed public identifiers do not automatically migrate persisted historical payloads.
- REVIEW_POLICY: `.engineering/REVIEW-AUTOFIX-POLICY.md`.
- PROMPT_DELIVERY: `.engineering/PROMPT-DELIVERY-POLICY.md`.

Startup order: `Checkpoint -> Decisions -> Scope -> DoD -> Architecture -> Requirements -> other applicable sources`.

Missing, stale or conflicting authoritative sources block progression. PROJECT_CONTEXT and GEF derived state never supersede canonical Git truth.
