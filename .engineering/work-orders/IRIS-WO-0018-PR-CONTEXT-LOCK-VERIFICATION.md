# IRIS-WO-0018: enforce Context Lock against actual PR Git base and changed-file allowlist

Status: ADMITTED_FOR_BOUNDED_GOVERNANCE_MAINTENANCE_ONLY | Issue #120 | Risk ELEVATED_GOVERNANCE
Exact source base `407078499027253703ee09ec986832095d355b0f` / tree `b1c4d9db004f152acf2cdfabf689c73566be1d78`, exact-main Governance #467 PASS 3949/3949; branch `iris-wo-0018-ci-context-lock-verifier-20260927`.
Scope: GitHub PR Context Lock verifier and negative/positive deterministic test harness only. No owner-contract or module runtime admission.

## SOURCE HIERARCHY AND PREFLIGHT
Canonical Git Checkpoint → Decisions → Scope → DoD → Architecture → Requirements → Security → Work Order. Context Lock pins 30/30 exact-base Git blob SHA-1s. Existing `.github/workflows/governance.yml` executes validator and suite but does not check source lock hashes or actual PR changed scope automatically. Confirm complete tree and authorized issue #120 before authoring. GitHub-only provenance cannot assert external live IRIS context; existing IRIS/GEF CI bridges remain mandatory.

## AUTHORIZED CHANGE AND STRICT 12-PATH ALLOWLIST
- `scripts/verify_context_lock.py`
- `tests/test_context_lock_verifier.py`
- `.github/workflows/governance.yml`
- `.engineering/CHECKPOINT.json`
- `.engineering/CHECKPOINT.md`
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/14-BACKLOG.md`
- `.engineering/evidence/IRIS-WO-0017.json`
- `.engineering/evidence/IRIS-WO-0018.json`
- `.engineering/context-locks/IRIS-WO-0018-PR-CONTEXT-LOCK-VERIFICATION.json`
- `.engineering/work-orders/IRIS-WO-0018-PR-CONTEXT-LOCK-VERIFICATION.md`
- `planning/reviews/IRIS-WO-0018-PR-CONTEXT-LOCK-AUDIT-TARGET.md`

## REQUIREMENTS
1. A deterministic, pure `verify_lock` helper that verifies lock schema, exact Git base SHA/tree, source SHA uniqueness, all eight canonical hierarchy roots and actual base blob equality, source counters and original statuses; canonical paths only, duplicates and forged counts fail closed; lock itself must be present and authorized.
2. Git-backed PR runner validates exact checkout HEAD, exact GitHub-supplied base SHA, ancestry, complete base tree source blobs and actual `git diff --name-only -z --no-renames`; rejects unauthorized changed paths and absence of a changed Context Lock. No new credentials/network in CI, no reliance on untrusted lock's self-described base. Avoid OS path traversal from untrusted lock data, do not execute any PR-supplied serialized payload.
3. Existing Governance workflow adds `fetch-depth: 0` for local Git base and a **PR-only** verification step using GitHub event-provided base/head SHA; push-main CI still runs its existing validator and full unit suite. Compile new script with existing tooling. Reuse pinned checkout/setup-python versions, existing branch protection.
4. New isolated pure and real-Git unit tests for valid, forged/missing/duplicate sources, false counters, stale base/tree, unauthorized diff, unsafe path, duplicate allowlist/JSON keys and CLI local Git truth. Old 3,949 test baseline retained. No M09/M11 runtime or OS-process API changes.
5. As substantive part of this increment, reconcile WO0017 #119 head #466 (initial #465 failed two fixed fixture escapes) and protected main #467 in canonical checkpoint/backlog/evidence. Do not create a receipt-only PR.

## PRE-MERGE PROOF AND STOP
Expected 19 newly authored verifier tests; not claimed run until exact-head Governance. Pin 30/30 and verify 12/12 paths. Independent bounded reviewer checks Git base source truth, no new HIGH/CRITICAL within the diff, real negative fixtures, unmodified M09/M11 contracts and all open owner gates. Stop after exact-head Governance with PR OPEN; if approved, guarded protected squash merge, exact-main CI and issue closure. Preserve H01–H04 OPEN, #82/#110/#112 OPEN, A/B/C NONE_SELECTED, 86/86 M11 questions OPEN/UNRATED, M09 v1.0 FROZEN 83/15/514, M11 v0.2 NOT_FROZEN, M10/M11 implementation NOT_ADMITTED, processes DISABLED.
