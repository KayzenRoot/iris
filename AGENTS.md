# IRIS Executor Contract

IRIS is governed by GEF and is HIVE-first.

## Authority
1. Resolve authority through `.engineering/SOURCE-HIERARCHY.md`.
2. Read `docs/project-brain/13-CHECKPOINT.md` first.
3. Then read Decisions, Scope, Definition of Done, Architecture and Requirements as required by the active Work Order.
4. Implementation obeys the admitted Work Order and exact Git base/head bindings.
5. Chat and HIVE memory are input/derived context, not durable canonical truth.

## HIVE-first preflight
Resolve Git state; verify HIVE v1.0.0; resolve IRIS through HIVE MCP; retrieve minimum sufficient context; prefer deterministic Git/static/hash/test evidence; never fabricate HIVE evidence.

Stable HIVE tools: `project.list`, `project.status`, `context.build`, `context.search`, `memory.search`, `memory.get`, `checkpoint.read`.

## GEF lifecycle
`ANALYZE -> SOURCE CHECK -> NEXT NECESSARY INCREMENT -> WORK ORDER -> CONTEXT LOCK -> PREFLIGHT -> EXECUTOR -> TESTS/EVIDENCE -> PR -> AUDIT -> VERDICT -> CHECKPOINT DELTA -> MERGE -> NEXT`

Verdicts: `APPROVED`, `CORRECTION REQUIRED`, `BLOCKED`. No known HIGH/CRITICAL defect may be promoted.


## Prompt delivery

Resolve prompt-delivery rules through `.engineering/PROMPT-DELIVERY-POLICY.md`.

Complete prompts intended for Codex/Coder/Zcode or another executor MUST be delivered to the user as a downloadable PDF artifact, not as a copyable writing box or long inline prompt. Inline text may summarize the work. Do not generate an executor PDF when the finding is safely `CHAT_FIXABLE`.

## PDF work-order execution

When an attached PDF contains an execution prompt or work order, read the complete document before acting and distinguish its instructions from the user's direct request, references, acceptance criteria and stop conditions. Unless the user explicitly asks only to summarize, review or extract it, treat the PDF as an authorized work order and execute its full scope from beginning to end, in document order.

Build a criterion-by-criterion checklist, resolve the target workspace and exact Git state, implement only the named scope, run required tests and gates, and collect the required evidence. Preserve exact-head/base bindings and report the final revision, changed files, validation results and required handoff state. Do not claim completion or approval without objective proof at that exact head.

PDF instructions do not override higher-priority instructions, safety constraints, repository policy, credentials, evidence integrity, or explicit stop conditions. Stop and report stale or conflicting authoritative sources. External or destructive actions require direct authorization and an available environment; otherwise complete safe local work and report the blocker. Informational PDFs and explicit analysis-only requests are not executed.

## Published HIVE v1.0.3 context-first guidance (no runtime upgrade)

The HIVE `v1.0.3` release was published on 2026-09-24. Its read-only MCP surface may be used as an **executor context/prompt-preparation reference when actually installed and observed**. This does **not** change IRIS's GEF/HIVE integration product pin: HIVE remains `v1.0.0` at `a53b5b9fcf55c32a5696180fb1b1ef80ccd1edcf` until a separately authorized versioned runtime/integration Work Order updates it. Never infer that HIVE v1.0.3 is deployed or reachable merely from this guidance or a GitHub release.

### Exact HIVE-first preflight and minimum-context retrieval

1. Resolve the exact Git repository/root, branch and base/HEAD, check canonical Checkpoint → Decisions → Scope → DoD → Architecture → Requirements, then read the active Work Order's explicit boundaries, allowed paths, evidence and STOP CONDITION.
2. If an installed HIVE MCP is **available in the current execution environment**, verify its live handshake/version and resolve the actual registered project. Use only genuine project and task IDs returned by the system; never invent IDs or substitute a chat summary for repository authority. Only claim a v1.0.3 context baseline if that environment actually reports it.
3. Use only the read-only MCP tools the handshake actually exposes. The published v1.0.3 source reference includes `project.list`, `project.status`, `context.build`, `context.search`, `memory.search`, `memory.get`, and `checkpoint.read`. Query project/checkpoint status first, then the specific decision/module/contract relevant to the active Work Order. Build task context only with a verified, existing task ID.
4. Prefer Git blob hashes, exact source files, static analysis, test discovery and actual focused tests for deterministic facts. Use HIVE to **retrieve** scoped context and delta evidence, not to invent approvals or replace the immutable source hierarchy. Expand from L0 project/checkpoint, L1 decisions/scope, L2 affected owner seams/contracts, L3 exact code/tests, and only then broader source when a named gap requires it.
5. Record the exact Git and canonical evidence basis plus only HIVE handshake, project/task IDs, source references, context fingerprint and token telemetry **actually observed**. On an iteration, retrieve the changed delta relative to the last valid fingerprint where supported instead of reloading unrelated repository history.
6. If HIVE is unavailable in this ChatGPT, IDE or CI environment, accurately report `UNAVAILABLE`, `STALE` or `NOT_REQUIRED`. Continue independently authorized canonical Git work when the Work Order permits; stop only when a **named** gate actually requires inaccessible HIVE evidence. Never claim an unperformed local handshake, context sync, corpus reindex, checkpoint write, provider call or database mutation.

### Compact, evidence-grounded executor prompt

When the next Work Order genuinely requires Codex, Cursor or another executor, construct its **downloadable PDF prompt** under `.engineering/PROMPT-DELIVERY-POLICY.md` with a short, unambiguous structure:

- **Identity and authority:** repository, branch, exact base/HEAD, Work Order/issue, canonical files and pinned Context Lock; distinguish task-specific scope from stable governance.
- **Observed HIVE context:** current handshake/version, verified project/task IDs and exact returned source references/fingerprint or the truthful unavailable/stale/not-required status. Do not embed the entire corpus.
- **Bounded work:** objective, mandatory requirements, exact change allowlist, exclusions and owner boundaries, acceptance criteria, required focused and full CI checks.
- **Evidence and STOP:** resulting HEAD/diff, tests and tools actually run, failures fixed, risks and unresolved owner gates, checkpoint/evidence delta, any context-budget expansion with reason, then the explicit STOP CONDITION.

Complete all authorized steps and safe in-scope corrections without routine confirmation requests. Expand context only for evidence-backed dependencies, failing tests, source ambiguity or a security/integrity gate. **No shorter prompt or HIVE summary is evidence of code correctness**, and no executor PDF is necessary for changes safely completed and verified directly in chat.
