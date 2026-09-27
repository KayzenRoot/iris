# IRIS-WO-0016 C02: read-only handoff compatibility and reverse liveness audit

Status: ADMITTED_FOR_WO0016_PLANNING_DOCS_ONLY | Risk: ELEVATED | Issue #112 | Related #110/#82
Exact base `452aff2f09e3f9130c26eb2068401b385cea67d1`, tree `84c9b89179c0eddcc617524e20ea122966679085`. Branch `iris-wo-0016-m09-c02-compatibility-audit-20260927`.
Previous C01 is canonical as a **NONFROZEN, UNADOPTED** proposal after reviewed PR #115, Governance #459, protected squash merge to this base and exact-main Governance #460 (3,940/3,940 tests). M09 v1.0 (83 surfaces, 15 components, 514 invariant proofs) remains FROZEN unchanged.

## New scope and outputs

Review the C01 proposal against all **14 FC-09-01..14**, **12 relevant owner lanes**, actual `iris_resource_twin/recovery.py` reverse owner-liveness and cooperative-release semantics, original `M11` §9.1, M09 frozen source and index-only M12/M53/M54/M55/M56/M58/M60. Produce `planning/compatibility/M09-HANDOFF-C02-FORWARD-COMPATIBILITY-SCAN.md`, `planning/reviews/M09-HANDOFF-C02-FREEZE-READINESS-REVIEW.md` and machine-readable `.engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json`. Record four **HIGH_FOR_FUTURE_FREEZE** source-backed owner prerequisites and six additional `LV-01..06` future reverse/lease-conflict proof oracles; mark all unexecuted. Distinguish frozen M09 in-process recovery types (not external trust) from proposed **M11 → M09** evidence producer port and the separate **M09 → M11** grant-evidence consumer port. Neither port is selected or adopted.

Reconcile exact C01 merge and Governance #460 evidence in WO0016's Evidence Bundle and checkpoint. Both checkpoint Markdown mirrors must stay byte-identical to one another and have identical `nextStep` to JSON. No owner response exists in Issue #110; do not fabricate one or treat a planning scan as contract adoption.

## Ten-path strict allowlist

- `.engineering/CHECKPOINT.json`
- `.engineering/CHECKPOINT.md`
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/14-BACKLOG.md`
- `.engineering/evidence/IRIS-WO-0016.json`
- `.engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json`
- `.engineering/context-locks/IRIS-WO-0016-M09-HANDOFF-C02-COMPATIBILITY-AUDIT.json`
- `.engineering/work-orders/IRIS-WO-0016-M09-HANDOFF-C02-COMPATIBILITY-AUDIT.md`
- `planning/compatibility/M09-HANDOFF-C02-FORWARD-COMPATIBILITY-SCAN.md`
- `planning/reviews/M09-HANDOFF-C02-FREEZE-READINESS-REVIEW.md`

## Acceptance and STOP

Pin 79/79 unique exact-base Git blob SHAs in the new Context Lock. Check 14 FC rows, 12 owners, four HIGH **future-freeze** blockers, six new LV cases, plus unchanged 12 HX/10 C08/8 PO-C02 unexecuted; owner trusts and races remain UNRATED, no claims of integration tests or physical proof. Zero edits to product code, existing `m09-contract-v1.0`, existing nonfrozen `m09-evidence-handoff-candidate-v0.1`, `m11-contract-candidate-v0.2`, tests, invariants or scripts. Exact-head Governance PASS, then leave PR OPEN pending **separate bounded audit** with no residual HIGH/CRITICAL in the newly authored *documentary scan scope*. Only guarded protected squash merge and exact-main Governance promote the scan. Do not freeze either candidate, select A/B/C, create M11-owned liveness proof, infer automatic release, admit M09/M11 implementation, invoke OS/IPC/process/lease action, or close Issues #82/#110/#112. All 86 M11 questions OPEN/UNRATED, M12–M60 contracts PENDING/UNRATED.
