# IRIS Backlog

Status: `M04_IMPLEMENTATION_ADMISSION_RECOMPILED`

## COMPLETED FOUNDATION
- IRIS-WO-0002 promoted the M00-M60 master module map and product discovery baseline.
- M01 planning/freeze/implementation is complete and merged.
- M02 planning/freeze/implementation is complete and merged.
- Repository professional governance hardening is complete.
- M03 planning/freeze/implementation is complete and merged.
- M04 S01-S05 planning, Final Technology Review, M05-M60 compatibility scan, contract freeze, independent planning audit, protected merge and exact-main reconciliation are complete.

## NECESSARY NEXT
1. Complete IRIS-WO-0008 admission and exact-head Governance.
2. Execute the complete frozen M04 provider-neutral kernel on `iris-wo-0008-m04-multimodal-ir-r2`.
3. Produce focused M04 tests, seven domain-neutral fixtures, docs and Evidence Bundle.
4. Independently audit the implementation against all 80 invariants and frozen acceptance families.
5. Correct CHAT_FIXABLE findings in the same PR where safe; use executor only for findings that genuinely require runtime/repository execution.
6. Squash-merge only after APPROVED and exact-head Governance.
7. Validate the resulting exact `main`.
8. Reconcile checkpoint/source truth.
9. Only then admit M05 planning/implementation according to its own lifecycle.
10. Freeze HIVE<->CORE<->IRIS runtime contracts before integration code that depends on them.

## RECORDED PLANNING DEBT
The earlier backlog called for a separate M00 S01-S05 constitution freeze. Repository history still lacks a separate approved M00 contract-freeze artifact. This remains explicit planning debt and must not be inferred complete.

## PLANNING QUEUE
Canonical module/session queue: `planning/MASTER-MODULE-INDEX.md`.

## IMPLEMENTATION GATE
No module implementation may advance from executor completion to merge without independent audit, evidence, exact-head Governance and protected merge validation. No next module may begin while the current increment requires correction or validation.
