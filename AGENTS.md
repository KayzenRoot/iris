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
