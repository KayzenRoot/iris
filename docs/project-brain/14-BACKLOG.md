# IRIS Backlog

Status: `M07_S02_PLANNING_COMPLETE`

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
- Cumulative candidate hard invariants: 60.
- Cumulative proprietary technology candidates: 10.
- Product/runtime implementation introduced: **NO**.

## NECESSARY NEXT
1. Deep-plan M07 S03 — driver, precision, encoder/decoder and topology detection.
2. Deep-plan M07 S04 — thermal, power and memory-pressure telemetry.
3. Deep-plan M07 S05 — Hardware Genome schema, versioning and confidence.
4. Perform M07 Final Technology Review and consolidate candidate technologies.
5. Run M08-M60 Forward Compatibility Scan without deep-planning future module internals.
6. Produce the M07 Module Contract Freeze candidate and independent planning audit.
7. Merge the approved M07 planning package and validate exact main.
8. Only then compile a separate bounded M07 implementation Work Order, Context Lock, Evidence obligations and executor PDF.

## IMPLEMENTATION GATE
No M07 product/runtime code is authorized during the active planning cycle. M08+ deep planning/implementation is also out of scope until M07 reaches an explicit planning/implementation state.

## RECORDED PLANNING DEBT
The separate M00 S01-S05 constitution freeze artifact remains historical planning debt.
