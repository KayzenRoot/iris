# IRIS Backlog

Status: `M07_PLANNING_MERGED_MAIN_VALIDATED`

## COMPLETED FOUNDATION
- M01 planning/freeze/implementation merged.
- M02 planning/freeze/implementation merged.
- M03 planning/freeze/implementation merged.
- M04 planning/freeze/implementation/review/reconciliation merged and exact-main validated.
- M05 planning frozen as `m05-contract-v1.0`; implementation independently approved, merged, reconciled and exact-main validated.
- M06 planning frozen as `m06-contract-v1.0`.
- M06 implementation `IRIS-WO-0010`: 25/25 frozen families, 150/150 hard invariants indexed to executable proof, 20/20 versioned evidence ports and 8/8 synthetic profiles.
- M06 independent audit initially found 8 bounded semantic-safety defects; all were corrected in the same PR and final audit approved with 0 residual HIGH/CRITICAL findings.
- M06 PR #48 squash-merged as `19f439837136cfd1e4882b085426ff6d91ad62f0`; exact-main Governance `35881369542 / 107250376754` PASS with 2770/2770 tests.
- M06 post-merge reconciliation PR #49 squash-merged as `b52e9837bef893c5c040c929520996cd110579e6`; exact-main Governance `35881919002 / 107252244422` PASS with 2770/2770 tests.
- M06 is durably closed as implemented/merged/validated.

## ACTIVE PLANNING
- Module: **M07 — Hardware Genome & Runtime Discovery**.
- Issue: #50.
- Branch: `iris-m07-s01-planning`.
- Exact planning base: `b52e9837bef893c5c040c929520996cd110579e6`.
- S01 GPU/CPU/RAM/storage/runtime discovery: **COMPLETE_FOR_MODULE_PLANNING**.
- S02 CUDA/ROCm/DirectML/Metal capability mapping: **COMPLETE_FOR_MODULE_PLANNING**.
- S03 driver, precision, encoder/decoder and topology detection: **COMPLETE_FOR_MODULE_PLANNING**.
- S04 thermal, power and memory-pressure telemetry: **COMPLETE_FOR_MODULE_PLANNING**.
- S05 Hardware Genome schema, versioning and confidence: **COMPLETE_FOR_MODULE_PLANNING**.
- All five canonical M07 sessions: **COMPLETE_FOR_MODULE_PLANNING**.
- Cumulative candidate hard invariants: 210.
- Cumulative proprietary technology candidates: 25.
- Final Technology Review: **APPROVED_FOR_FORWARD_COMPATIBILITY_SCAN**.
- Consolidated independent technology surfaces: 20 ADOPT + 5 ADOPT_AS_COMPONENT.
- M08-M60 Forward Compatibility Scan: **APPROVED_FOR_MODULE_CONTRACT_FREEZE**.
- Future modules scanned: 53/53.
- Freeze-candidate hard invariants after compatibility scan: 235.
- M07 Module Contract Freeze candidate: `m07-contract-v1.0`.
- Frozen planning contract: `FROZEN_APPROVED / m07-contract-v1.0`.
- Independent final planning audit: **APPROVED**, residual HIGH/CRITICAL: 0.
- PR #51 squash-merged as `cbdf9071ca2980d4ff9823d7fbbd271cc15935b7`; exact-main Governance `35885688381 / 107265126344` PASS with 2770/2770 tests.
- Product/runtime implementation introduced: **NO**.

## NECESSARY NEXT
1. Review and merge the M07 planning post-merge reconciliation.
2. Validate the reconciliation merge on exact main.
3. Compile and admit a separate bounded M07 implementation Work Order, Context Lock and Evidence package against `m07-contract-v1.0`.
4. Only after admission may M07 implementation begin.

## IMPLEMENTATION GATE
No M07 product/runtime code is authorized during the active planning cycle. M08+ deep planning/implementation is also out of scope until M07 reaches an explicit planning/implementation state.

## RECORDED PLANNING DEBT
The separate M00 S01-S05 constitution freeze artifact remains historical planning debt.
