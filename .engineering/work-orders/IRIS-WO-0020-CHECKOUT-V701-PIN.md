# IRIS-WO-0020: upgrade exact-SHA pinned official checkout action v7.0.1

Status: ADMITTED_FOR_BOUNDED_CI_DEPENDENCY_UPDATE_ONLY | Issue #124 | Risk ELEVATED_SUPPLY_CHAIN_CI
Exact base `ad99f343431a0984fedb99746c64fb26462d7ad2`, tree `f74b481d51953d183b8a84ea8ee24cc85155b96d`, head Governance #477 PASS 3979/3979.
Blocked Dependabot #16 rebased to 1c4ed2ad23cdb0b91c34d081215b6c29a3b3cce3 on this base but has NO exact-head CI after bot rebase/reopen; old #476 PASS is another head. Replace it with a new governed owner-controlled PR for **the exact same single line**, NOT with an untested Dependabot merge.

## Source and release admission
Read Checkpoint → Decisions → Scope → DoD → Architecture → Requirements → AGENTS/security → active Work Order. 31/31 immutable exact-base Git blobs verified including eight mandatory roots. GitHub official `actions/checkout` tag `v7.0.1` is commit `3d3c42e5aac5ba805825da76410c181273ba90b1`, independently retrieved via official tag Git ref endpoint. Pinned action major upgrade is not covered by source SHA alone; require actual head CI and scoped review. Pinned `actions/setup-python` v7.0.0 stays `5fda3b95a4ea91299a34e894583c3862153e4b97` (already reviewed PR #15 / exact-main #477).

## Exact allowlist (10)
- `.github/workflows/governance.yml`
- `.engineering/CHECKPOINT.json`
- `.engineering/CHECKPOINT.md`
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/14-BACKLOG.md`
- `.engineering/evidence/IRIS-WO-0019.json`
- `.engineering/evidence/IRIS-WO-0020.json`
- `.engineering/context-locks/IRIS-WO-0020-CHECKOUT-V701-PIN.json`
- `.engineering/work-orders/IRIS-WO-0020-CHECKOUT-V701-PIN.md`
- `planning/reviews/IRIS-WO-0020-CHECKOUT-V701-PIN-AUDIT.md`

## Authorized execution
Only update the single `.github/workflows/governance.yml` line from `uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # v5` to `uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`. Preserve `fetch-depth: 0`, exact PR candidate checkout, full source Context Lock check, GEF/HIVE bridges and tests, restricted read-only permissions. Reconcile previously validated WO0019 #473/#474 and official setup-python PR #15 #475/#477 in checkpoint and evidence **as part of this substantive action upgrade**. No historic source rewrites, no extra Dependabot workflow pin bumps, no M09/M11 product/contracts/OS/process changes. No new tests necessary for this single-line dependency revision; full existing 3,979-test suite must actually run on newly reviewed exact head.

## STOP and acceptance
Context Lock match 31/31 base blobs, 10/10 changed paths, Markdown checkpoint mirrors byte-identical and machine nextStep exact. Require strict PR-head CI to execute **new v7.0.1 checkout** and all 3,979 tests PASS, then separately scoped review of SHA/ref, path diff and CI logs, zero new HIGH/CRITICAL. Only after APPROVED exact head guarded protected squash merge, exact-main CI 3,979/3,979 and verified main SHA. If all PASS, comment/close original bot PR #16 as SUPERSEDED_BY_THIS_GOVERNED_PR, not as successfully merged. Issue #124 can then close. Keep #82/#110/#112 OPEN, M09 v1.0 frozen 83/15/514, M11 v0.2 unfrozen, M10/M11 implementation NOT_ADMITTED and processes DISABLED.
