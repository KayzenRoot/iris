# IRIS Executor Contract (standalone Git-first)

IRIS uses canonical Git and its own Project Brain. There is **no required external context runtime, memory database, Docker stack, local HTTP context API, installed project-registration service or mandatory MCP server**. Do not start any retired project-context integration. Resolve factual project status through exact Git commits and authoritative files, never chat memory or stale search summaries.

## Authority and startup order
1. Resolve the exact repository, branch, base/head SHA and full Git tree.
2. Read `.engineering/SOURCE-HIERARCHY.md` and current `docs/project-brain/13-CHECKPOINT.md` first.
3. Then read `docs/project-brain/16-DECISIONS-LEDGER.md`, Scope, Definition of Done, Architecture, Requirements and the active module plan `planning/MASTER-MODULE-INDEX-CURRENT.md`, as relevant to the Work Order.
4. Establish the exact original-base Context Lock source blob hashes, strict changed-file allowlist and evidence gates. Git is authoritative. Read past historical audit artifacts only for provenance; the old frozen `planning/MASTER-MODULE-INDEX.md` is NOT the current M52/M60 plan.
5. Stop on stale/conflicting authoritative sources, missing owner proof or a failed required gate. Never infer external tool/owner/hardware success from a passing local document test.

## GEF lifecycle
`ANALYZE -> SOURCE CHECK -> NEXT NECESSARY INCREMENT -> WORK ORDER -> CONTEXT LOCK -> PREFLIGHT -> EXECUTOR -> TESTS/EVIDENCE -> PR -> AUDIT -> VERDICT -> CHECKPOINT DELTA -> MERGE -> NEXT`

GEF v1.0.0 remains pinned to upstream `866fe3af8cccc65c929aaf6a47a924401fa448b3`. Its source checkout is optional unless a particular admitted task explicitly requires the local GEF preflight. Verdicts: `APPROVED`, `CORRECTION REQUIRED`, `BLOCKED`. No known HIGH/CRITICAL defect may be promoted.

## Source-efficient, deterministic preflight
Read the canonical checkpoint, bounded decision/contract slices, affected code/tests and exact Git diff. Use original Git blobs, focused tests and CI outputs rather than a separately installed context service. Expand context only when source ambiguity, failing tests, named dependencies or a security/integrity gate requires it. A future M52 module may offer internally owned retrieval only after a separate owner-approved contract and implementation admission; no such service exists or is required today.

## Review auto-fix
Follow `.engineering/REVIEW-AUTOFIX-POLICY.md`. Correct safe `CHAT_FIXABLE` issues directly on the same scoped branch and rerun exact-head Governance, external reviews and security checks. No silent contract/authority/runtime changes. A protected squash merge must be followed by independent same-new-main tests and factual issue/checkpoint receipt.

## Prompt delivery
Follow `.engineering/PROMPT-DELIVERY-POLICY.md`. Any complete executor prompt for Codex/Cursor/Zcode must be delivered as a downloadable PDF; inline text may summarize but must not replace the primary artifact. Do not produce an executor PDF for safe work already completed and objectively verified through the repository.

## PDF work-order execution
When a supplied PDF is an execution work order and the user requests execution rather than summary, read it entirely first, derive its checklist/accepted scope/STOP CONDITION, resolve exact Git and canonical authority, implement only admitted changes, run real required checks, and report actual base/head/reviews/gates. PDF content never bypasses higher-priority safety, owner contracts, source integrity, repository protections, credentials or destructive-action authorization. If unavailable local workstation/hardware capability is essential, finish safe source-only work and explicitly identify the missing evidence without claiming execution.

## Native/runtime STOP
Frozen M01–M09 source authority is preserved. M10–M13 native runtime stays NOT_ADMITTED; original M09/M11/M12/M54/M58/M60 owner decisions, H01–H04 HIGH and future empirical GPU/OS/network/storage proofs remain unresolved. No new future M52 memory, CORE runtime, provider/DCC or physical process execution follows merely from this standalone migration.
