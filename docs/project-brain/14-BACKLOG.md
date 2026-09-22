# IRIS Backlog

Status: `M04_PLANNING_NEXT`

## COMPLETED FOUNDATION
- IRIS-WO-0002 promoted the M00-M60 master module map and product discovery baseline.
- M01 planning/freeze/implementation is complete and merged.
- M02 planning/freeze/implementation is complete and merged.
- Repository professional governance hardening is complete.
- M03 planning/freeze/implementation is complete and merged.

## NECESSARY NEXT
1. Execute M04 S01-S05 slow planning.
2. Perform M04 Final Technology Review and prior-art/proprietary-technology disposition.
3. Run the M05-M60 Forward Compatibility Scan.
4. Freeze the M04 Module Contract.
5. Independently audit and merge the planning package.
6. Only after exact-`main` validation, admit a separate bounded M04 implementation Work Order / Context Lock / Evidence package.
7. Define measurable quality/benchmark obligations before implementation for every affected later domain.
8. Freeze HIVE<->CORE<->IRIS runtime contracts before integration code that depends on them.

## RECORDED PLANNING DEBT
The earlier backlog called for a separate M00 S01-S05 constitution freeze. The repository history inspected before M04 contains the M00-M60 discovery baseline but no separate approved M00 contract-freeze artifact. This reconciliation does **not** invent or mark M00 complete.

The canonical checkpoint outranks backlog and currently authorizes `M04_PLANNING_READY`. Therefore the M00 disposition remains explicit planning debt to resolve before IRIS 1.0 final acceptance, or earlier if a later module exposes a concrete conflict.

## PLANNING QUEUE
Canonical module/session queue: `planning/MASTER-MODULE-INDEX.md`.

## IMPLEMENTATION GATE
No product implementation Work Order is admitted until its governing module planning is sufficiently frozen, its forward compatibility scan passes, its planning review/merge is validated, and upstream canonical sources are not stale.
