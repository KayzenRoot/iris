# IRIS Backlog

Status: `M04_IMPLEMENTATION_ADMISSION`

## COMPLETED FOUNDATION
- IRIS-WO-0002 promoted the M00-M60 master module map and product discovery baseline.
- M01 planning/freeze/implementation is complete and merged.
- M02 planning/freeze/implementation is complete and merged.
- Repository professional governance hardening is complete.
- M03 planning/freeze/implementation is complete and merged.
- M04 S01-S05 planning, Final Technology Review, M05-M60 compatibility scan, contract freeze and independent planning audit are complete.
- M04 planning PR #27 and post-merge reconciliation PR #29 are merged and exact-main validated.

## NECESSARY NEXT
1. Complete and validate IRIS-WO-0008 / Context Lock / Evidence admission.
2. Execute the complete frozen M04 `m04-contract-v1.0` implementation on the admitted branch.
3. Run focused M04 tests plus the full repository suite.
4. Produce implementation Evidence Bundle and proposed Checkpoint Delta.
5. Independently audit and chat-fix safe findings before any merge.
6. Squash-merge only after APPROVED and exact-head Governance.
7. Validate resulting exact `main`.
8. Only then determine the next necessary module lifecycle; M05 implementation is not automatically admitted.
9. Freeze HIVE<->CORE<->IRIS runtime contracts before integration code that depends on them.

## RECORDED PLANNING DEBT
The earlier backlog called for a separate M00 S01-S05 constitution freeze. Repository history contains the M00-M60 discovery baseline but no separate approved M00 contract-freeze artifact. This remains explicit planning debt and is not treated as completed by M04 work.

## PLANNING QUEUE
Canonical module/session queue: `planning/MASTER-MODULE-INDEX.md`.

## IMPLEMENTATION GATE
No product implementation Work Order is admitted until its governing module planning is frozen, forward compatibility passes, planning review/merge is exact-main validated, canonical sources are coherent, a bounded Work Order/Context Lock/Evidence package exists, and executor preflight proves the context is not stale.
