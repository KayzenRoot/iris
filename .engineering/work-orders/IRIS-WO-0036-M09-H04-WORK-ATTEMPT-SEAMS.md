# IRIS-WO-0036: H04 frozen M09 work/attempt/action/lease-epoch source semantic fixture probes

Status: ADMITTED_FOR_SYNTHETIC_EXISTING_M09_SOURCE_TEST_ONLY. #110 and related #82/#112/#128 remain OPEN.
Exact source base `caa0bb74ffc91b307d7fbd7f74c4c04bc3f5893b`, tree `4ee8fa15c64d5f3264853fa8da66cf9750ae8858`, prior exact-main Governance #517 run 36339710385/job 108677270035 PASS **4186/4186**. Owner ratified B_FUTURE_OWNER_RECEIPT for *planning a future M09→M11 forward read-only owner-issued receipt*, NOT admission of C01 or a verified M02/M06/M11 binding, at https://github.com/KayzenRoot/iris/issues/110#issuecomment-5857665032.

## Objective
Produce 18 deterministic **synthetic in-memory** H04-P01..P18 tests of the *existing* frozen M09 `LeaseBook` and source-accurate M02/M06/M11 cross-owner identity gap analysis. Establish what existing M09 already protects within the book (full request idempotency digest; mutation actor/auth; lease epochs on renewal, revocation and release; tombstone) versus what is **not yet present** (owner-issued M02 accepted semantic work/revision and M06 genuine operational attempt, M11 scoped request/revision/action/target, composite M09 joint-cut, action-time revocation barrier). Explicitly distinguish local caller-supplied `M02:` or `M06:` strings from genuine issuer decisions. No real M02/M06 port or execution action is created. Add eight documentary/source history guard tests, machine probe inventory, source analysis, backlog delta, historical checkpoint and bounded review target. Reconcile WO0035 #516/#517 receipts substantively.

## Source and change controls
Pin **26/26** base Git SHA1 original blobs including eight project authority roots, existing frozen M09 code and test sources, M02/M06/M11 documented contracts, existing implemented M02/M06 graph/revision/ports, historical C01/C02 and ratified B D01, M11 C09 reverse, previous WO0035 evidence/report and backlog. Strict **10/10** diff allowlist:
- `.engineering/context-locks/IRIS-WO-0036-M09-H04-WORK-ATTEMPT-SEAMS.json`
- `.engineering/evidence/IRIS-WO-0036.json`
- `.engineering/evidence/M09-H04-WORK-ATTEMPT-EPOCH-EVIDENCE.json`
- `.engineering/work-orders/IRIS-WO-0036-M09-H04-WORK-ATTEMPT-SEAMS.md`
- `docs/project-brain/14-BACKLOG.md`
- `planning/checkpoints/IRIS-WO-0036-M09-H04-WORK-ATTEMPT-SEAMS.md`
- `planning/reviews/IRIS-WO-0036-M09-H04-BOUNDARY-AUDIT-TARGET.md`
- `planning/reviews/M09-H04-SYNTHETIC-WORK-ATTEMPT-SEAM-PROBE.md`
- `tests/test_m09_h04_source_integrity.py`
- `tests/test_m09_h04_work_attempt_epoch_seams.py`

No M09/M02/M06/M11 runtime code edits, no frozen contract or original HX/LV future tests, no current canonical Decisions Ledger, Scope or Checkpoint authority promotion; only tests and documentary bounded provenance.

## Completion checks
Exact-head 4212/4212 expected (4186 baseline+18 H04-P synthetic source semantics+8 new history/documentary integrity). Validate Context Lock 26/26 and actual 10/10 allowlisted paths, all IRIS validator steps and pinned GEF/HIVE. Separate bounded same-assistant exact-head review distinguishes any new HIGH/CRITICAL in scoped test/doc diff from **four inherited unresolved HIGH**. Protect squash at exact reviewed head, separate main CI must pass; closeout comments record only executed H04-P fixtures, not any original future oracles.

## STOP
Original HX-01..12/LV-01..06/C08 ten/PO-C02 eight/M12 80 future cases remain **SPECIFIED_NOT_EXECUTED**. No M02 accepted-revision issuer, M06 attempt issuer, M11 process action/target port, M09 owner-issued cross-module receipt, M54 permission or M60 OS capability is proven by source fixtures. H01..H04 OPEN HIGH_FOR_FUTURE_FREEZE; H04 OPEN_CROSS_OWNER_DISPOSITION, H01 authentic reverse liveness+ACK, H02 atomic all-member joint snapshot+lease and revocation-to-use, H03 M12/M54/M58/M60 real owner contracts. M09 v1.0 FROZEN unchanged, C01 UNADOPTED_NOT_FROZEN; M11 v0.2 NOT_FROZEN 86 OPEN; M12 v0.1 NOT_FROZEN 110 OPEN and 80 future cases unexecuted. M10/M11/M12 implementation NOT_ADMITTED; all OS/GPU/network/cloud/process actions DISABLED, no grant, freeze or new endpoint. Keep #82/#110/#112/#128 OPEN.
