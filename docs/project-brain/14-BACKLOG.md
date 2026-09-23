# IRIS Backlog

Status: `M04_COMPLETE_M05_PLANNING_READY`

## COMPLETED FOUNDATION
- IRIS-WO-0002 promoted the M00-M60 master module map and product discovery baseline.
- M01 planning/freeze/implementation is complete and merged.
- M02 planning/freeze/implementation is complete and merged.
- Repository professional governance hardening is complete.
- M03 planning/freeze/implementation is complete and merged.
- M04 planning, contract freeze, implementation, independent review, protected merge and exact-main validation are complete.
- M04 merge SHA: `8dd188fcea7fa0874fab214867e1f5f6ce23e8cd`.
- M04 exact-main suite: `2677/2677 OK`.
- M04 independent review: 6 CHAT_FIXABLE closed, 0 EXECUTOR_REQUIRED, 0 remaining HIGH/CRITICAL.

## NECESSARY NEXT
1. Merge this post-M04 reconciliation and validate its exact main.
2. Admit M05 planning/discovery through the normal S01-S05 / technology review / compatibility / freeze lifecycle.
3. Do not create M05 implementation code before its own contract and Work Order are admitted.
4. Freeze HIVE<->CORE<->IRIS runtime contracts before integration code that depends on them.

## RECORDED PLANNING DEBT
The earlier backlog called for a separate M00 S01-S05 constitution freeze. Repository history still lacks a separate approved M00 contract-freeze artifact. This remains explicit planning debt and must not be inferred complete.

## PLANNING QUEUE
Canonical module/session queue: `planning/MASTER-MODULE-INDEX.md`.

## IMPLEMENTATION GATE
No later module may inherit M04 approval. Each module requires its own planning, frozen contract, Work Order, Context Lock, evidence, tests, independent review and protected merge.
