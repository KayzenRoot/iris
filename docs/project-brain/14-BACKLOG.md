# IRIS Backlog

Status: `M05_PLANNING_MERGED_MAIN_VALIDATED`

## COMPLETED FOUNDATION
- M01 planning/freeze/implementation merged.
- M02 planning/freeze/implementation merged.
- M03 planning/freeze/implementation merged.
- M04 planning/freeze/implementation/review/reconciliation merged and exact-main validated.
- M05 planning Issue #37 / PR #38 opened from exact validated main.
- M05 S01 complete.
- M05 S02 complete.
- M05 S03 complete.
- M05 S04 complete.
- M05 S05 complete.
- S01-S05 candidate invariants: 150.
- Technology registry: `IRIS-DNAX-001..150`.
- Final Technology Review complete: `APPROVED_FOR_FORWARD_COMPATIBILITY`.
- Consolidated families: `F-M05-01..25`, exact-once mapping across all 150 DNAX candidates.
- M06-M60 Forward Compatibility Scan: `PASS_WITH_EXTENSION_PORTS`, 55 modules, 0 critical ownership conflicts, 22 future extension/ref families.
- M02/M06/M53/M54/M55/M58/M59 authority boundaries explicitly protected.
- `m05-contract-v1.0` freeze candidate created with 150 invariants, 25 consolidated families and 22 extension/ref ports.

## NECESSARY NEXT
1. Create a separate bounded M05 implementation Work Order from exact validated main.
2. Create and admit its Context Lock.
3. Define implementation Evidence obligations and preflight.
4. Implement only the frozen `m05-contract-v1.0` semantic kernel.
5. Independent implementation review before merge.

## RECORDED PLANNING DEBT
The separate M00 S01-S05 constitution freeze artifact remains historical planning debt.

## IMPLEMENTATION GATE
No M05 product/kernel code is authorized during this planning cycle.


## M05 FREEZE
- Contract: `m05-contract-v1.0`
- Status: `FROZEN_APPROVED`
- Independent Planning Audit: `APPROVED`
- 150 hard invariants
- 25 consolidated technology families
- 22 forward extension/ref ports
- implementation: not started


## M05 PLANNING PROMOTION
- PR #38: squash-merged
- merge SHA: `2b5b7330a684fece8e354b6fe88b8fcd4bb0611f`
- exact-main Governance: `35843109186 / 107122673542` — PASS
- exact-main full suite: `2677/2677 OK`
- implementation: not started
