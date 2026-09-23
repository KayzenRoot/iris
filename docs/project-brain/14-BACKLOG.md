# IRIS Backlog

Status: `M04_IMPLEMENTATION_REVIEW_APPROVED_PENDING_MERGE`

## COMPLETED FOUNDATION
- IRIS-WO-0002 promoted the M00-M60 master module map and product discovery baseline.
- M01 planning/freeze/implementation is complete and merged.
- M02 planning/freeze/implementation is complete and merged.
- Repository professional governance hardening is complete.
- M03 planning/freeze/implementation is complete and merged.
- M04 S01-S05 planning, Final Technology Review, M05-M60 compatibility scan, contract freeze, independent planning audit and planning merge are complete.
- IRIS-WO-0008 M04 implementation is complete on PR #34.
- Independent M04 implementation review is APPROVED: 6 CHAT_FIXABLE findings closed, 0 EXECUTOR_REQUIRED, 0 remaining HIGH/CRITICAL.
- Reviewed code head `7d3237a3ea39a1006fca8137046587077de29602`: Governance PASS, 2677/2677 tests OK.

## NECESSARY NEXT
1. Validate the final checkpoint/evidence promotion head of PR #34.
2. Squash-merge PR #34 only through protected `main-governance`.
3. Validate the resulting exact `main` SHA.
4. Reconcile M04 checkpoint/source truth as merged.
5. Only then admit M05 planning/implementation according to its own lifecycle.
6. Freeze HIVE<->CORE<->IRIS runtime contracts before integration code that depends on them.

## RECORDED PLANNING DEBT
The earlier backlog called for a separate M00 S01-S05 constitution freeze. Repository history still lacks a separate approved M00 contract-freeze artifact. This remains explicit planning debt and must not be inferred complete.

## PLANNING QUEUE
Canonical module/session queue: `planning/MASTER-MODULE-INDEX.md`.

## IMPLEMENTATION GATE
No module implementation may advance from independent approval to merged truth without exact-head Governance, protected merge validation and exact-main validation. No next module may begin while the current increment requires merge or reconciliation.
