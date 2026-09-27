# IRIS-WO-0021: HIVE v1.0.3 context-first guidance and compact executor prompts

Status: ADMITTED_FOR_EXECUTOR_DOCUMENTATION_ONLY | Issue #126 | Risk ELEVATED_REPO_WIDE_EXECUTOR_POLICY
Exact base `a186fe2d6c659c3e410a16eccd42f3b82166428e` / tree `1ace7ea201487593f4bd6b1358c9c6df3d79d77b`, exact-main Governance #480 PASS 3979/3979. New branch `iris-wo-0021-hive-v103-context-guidance-20260927`.
Stale predecessor PR #91 (one-file AGENTS proposal on historical `61864d387b20b6cb283ccfec12ab5cf6f2ffaa14`) is not currently mergeable or authorized under today's Context Lock; retain its valid HIVE-first intent via this separately admitted replacement. Do NOT mutate the old branch.

## SOURCE PREFLIGHT
Checkpoint → Decisions → Scope → DoD → Architecture → Requirements → Work Order. Lock 34/34 unique exact-base Git blob SHA-1s including eight required canonical hierarchy roots. Confirm connected HIVE GitHub stable release v1.0.3 published `2026-09-24T09:02:41Z`, annotated tag `f0db3464debcde75d78e6b321e8a27b0404d02a6` resolves to commit `52bd3dab54dd4f16264072e198ed1fc23168f7fa`. The tagged `backend/app/mcp_server.py` contains `project.list`, `project.status`, `context.build`, `context.search`, `memory.search`, `memory.get`, `checkpoint.read` read-only reference surface; **external published source is not proof of locally installed HIVE or actual handshake**.

## OBJECTIVE AND 10-PATH STRICT SCOPE
Carry the useful v1.0.3 prompt/context workflow from PR #91 into AGENTS without changing HIVE `v1.0.0` product/runtime pinned SHA `a53b5b9fcf55c32a5696180fb1b1ef80ccd1edcf` or GEF/HIVE bootstraps. Require actual observed HIVE environment handshake, legitimate project/task IDs, minimal read-only progressive disclosure, deterministic Git/static facts and changed-delta retrieval with fingerprints, truthful fallback, explicit context budget. Preserve existing PDF executor-prompt delivery and STOP. No repo-wide refactor, code execution, provider/storage actions or HIVE version upgrade. Fold already verified WO0020 PR #125 head Governance #478 and main Governance #480 receipts as part of this substantive AGENTS change; close old PR #91 only after this WO exact-main PASS.

Allowlist:
- `AGENTS.md`
- `.engineering/CHECKPOINT.json`
- `.engineering/CHECKPOINT.md`
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/14-BACKLOG.md`
- `.engineering/evidence/IRIS-WO-0020.json`
- `.engineering/evidence/IRIS-WO-0021.json`
- `.engineering/context-locks/IRIS-WO-0021-HIVE-CONTEXT-PROMPTS.json`
- `.engineering/work-orders/IRIS-WO-0021-HIVE-CONTEXT-PROMPTS.md`
- `planning/reviews/IRIS-WO-0021-HIVE-CONTEXT-PROMPTS-AUDIT.md`

## GATES
All 34 source hashes and 10 changed files in lock; both checkpoint Markdown mirrors byte-identical and JSON `nextStep` exact. Full existing **3979/3979** tests, compile, validator, GEF/HIVE CI bridges on this new exact final PR head. Separate bounded review must check claim of release/tag/API tool names, v1.0.0 runtime pin unchanged everywhere, no fabricated observed live HIVE access or local tests, no change to frozen M09/M10/M11. Audit zero new HIGH/CRITICAL, protected squash on final approved head and exact-main Governance PASS. If passed close Issue #126 and obsolete PR #91 as SUPERSEDED. Keep #82/#110/#112 OPEN, four H01..H04 and 86 M11 questions unresolved, M10/M11 code NOT_ADMITTED, processes DISABLED.
