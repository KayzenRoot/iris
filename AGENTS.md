# IRIS Executor Contract

IRIS is governed by GEF and is HIVE-first.

## Authority
1. Resolve authority through `.engineering/SOURCE-HIERARCHY.md`.
2. Read `docs/project-brain/13-CHECKPOINT.md` first.
3. Then read Decisions, Scope, Definition of Done, Architecture and Requirements as required by the active Work Order.
4. Implementation obeys the admitted Work Order and exact Git base/head bindings.
5. Chat and HIVE memory are input/derived context, not durable canonical truth.

## HIVE-first preflight
Resolve Git state; verify the HIVE v1.0.3 context/MCP baseline; resolve IRIS through HIVE MCP; retrieve minimum sufficient context; prefer deterministic Git/static/hash/test evidence; never fabricate HIVE evidence.

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

## HIVE v1.0.3 context-first work and prompt contract

The current HIVE executor-context baseline is the published **v1.0.3** read-only MCP surface. This is a context and prompt-preparation baseline; it does **not** change this repository's product dependency, runtime, compatibility pin, or HIVE V1/V2 integration contract. Keep those project-specific pins unchanged unless their own authorized Work Order validates and admits an upgrade. This repository's Git state, approved checkpoint, source hierarchy, decisions, scope, and active Work Order remain authoritative over HIVE-derived memory/context.

### Preflight

1. Confirm the exact repository, branch, HEAD/base SHA, and active Work Order or issue before building context. Read this repository's checkpoint/source hierarchy and the Work Order's scope, allowed files, acceptance criteria, and stop condition.
2. When HIVE MCP is available in this execution surface, verify the handshake and the reported v1.0.3 context baseline. Resolve this repository by its actual registered identity; use only an existing, canonical task ID. Never guess a project or task ID.
3. Use only read-only tools actually exposed by the handshake. The v1.0.3 reference surface includes `project.list`, `project.status`, `context.build`, `context.search`, `memory.search`, `memory.get`, and `checkpoint.read`. Build task context only for a valid task ID. Retrieve the minimum context needed for this Work Order; do not load unrelated history or the whole corpus.
4. Record the exact Git basis and only HIVE version, project/task identity, source references, or context fingerprint actually returned. A HIVE summary is derived context, not canonical approval or evidence that an unobserved check passed.
5. If HIVE is absent, stale, mismatched, or not exposed here, label it accurately and continue from canonical repository sources whenever the Work Order permits. Finish independent authorized work and do not stop for routine confirmation. Mark BLOCKED only when an explicit gate requires unavailable HIVE evidence. Never claim local HIVE access from a hosted execution surface, or vice versa.
6. Do not synchronize/reindex a corpus, create tasks, write a database, call a provider, or mutate remote/runtime state unless the active Work Order explicitly authorizes that operation.

### Compact HIVE-grounded executor prompt

When preparing a Codex/Cursor or other executor prompt, include only the task-relevant context and these fields:

- **Identity:** repository/path, Work Order/issue, branch, exact base and current HEAD.
- **Authority:** canonical checkpoint and source paths; the active Work Order and Context Lock, if present.
- **HIVE context:** v1.0.3 handshake status, verified project/task IDs, and returned source references/fingerprint — or the truthful status `UNAVAILABLE`, `STALE`, or `NOT_REQUIRED`.
- **Work:** objective, exact allowed change surface, acceptance criteria, required focused checks, evidence to return, exclusions, and stop condition.
- **Execution direction:** complete every authorized step, fix review findings within scope, perform the required review, and report which checks actually ran. Do not ask for routine confirmation; do not widen scope or claim unperformed work.

Prefer canonical file paths and short HIVE context references over copying full documents or chat history. Keep stable policy, Work Order-specific requirements, and volatile runtime evidence in separate, compact sections.
