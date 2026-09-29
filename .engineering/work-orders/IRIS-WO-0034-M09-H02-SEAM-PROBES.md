# IRIS-WO-0034: H02 existing frozen M09 seam semantic probes (test-only, no module promotion)

Status: ADMITTED_FOR_BOUNDED_EXISTING_SEMANTIC_FIXTURE_TESTS_ONLY | Issue #110 remains OPEN
Exact base SHA `ed743fda62764fedb5d31b55c04b9c939979f6f8`; tree `1acba17d5d2301e067c4abb219142a106fe414a5`; exact-main Governance #513 run 36334277712/job 108662018344 PASS 4136/4136. B_FUTURE_OWNER_RECEIPT ratified for documentary planning only at https://github.com/KayzenRoot/iris/issues/110#issuecomment-5857665032. D01 PR #140 exact-head Governance #512 and exact-main #513 PASS on this base, source lock 35/35 and diff 19/19.

## Next necessary bounded increment
H02 remains an explicit unproved HIGH future-freeze gate for a future M09 owner-coherent snapshot+lease + composite member cut and at-use revocation check. This Work Order adds **14 new deterministic synthetic in-memory fixture tests of the existing M09 public APIs**, some illustrating risky interleavings for a naive external consumer, others establishing present frozen M09 safety controls. It neither implements nor drafts an admitted M09→M11 receipt, edits M09 runtime code, nor runs original HX/LV integration tests. Add **8 documentary integrity tests** to tie test cases, original C01/C02 H01–H04 and HX/LV inventories, actual chosen B-only direction and explicit STOP to exact Git source blobs. The proof is only source-level in-memory semantic evidence, never a concurrency linearizability or cross-host authority qualification.

## Exact source lock and strict allowlist
Bind **22/22** exact base Git blob SHA-1s, including all eight project authority roots, ratified D01/C01/C02 source evidence, frozen M09 contract, exact existing twin/leases/model code and test support/current M09 tests, prior WO0033 historical evidence and M11 C09. Only the following **10** files may change:

- `.engineering/context-locks/IRIS-WO-0034-M09-H02-SEAM-PROBES.json`
- `.engineering/evidence/IRIS-WO-0034.json`
- `.engineering/evidence/M09-H02-SEMANTIC-PROBE-EVIDENCE.json`
- `.engineering/work-orders/IRIS-WO-0034-M09-H02-SEAM-PROBES.md`
- `docs/project-brain/14-BACKLOG.md`
- `planning/checkpoints/IRIS-WO-0034-M09-H02-SEAM-PROBES.md`
- `planning/reviews/IRIS-WO-0034-M09-H02-SEAM-PROBES-AUDIT-TARGET.md`
- `planning/reviews/M09-H02-SYNTHETIC-SEAM-PROBE.md`
- `tests/test_m09_h02_evidence_integrity.py`
- `tests/test_m09_h02_seam_probe.py`

Do NOT modify frozen M09 code, existing 514 invariants/721 historical M09 tests, actual original HX/LV or M12 registers, original D01 B owner-choice JSON, Decisions Ledger, canonical checkpoint or public status pages. No new authoritative owner decision is made; only a historical Work Order checkpoint and backlog research receipt may be added without gate promotion.

## Test cases and DoD
14 separately identified cases `H02-P01..P14` in `tests/test_m09_h02_seam_probe.py` cover initially valid independent reads; detached snapshot after twin invalidation; naive grant from detached snapshot; invalidation after grant; `active()` including revocation-requested; stale captured active lease after revocation; action-time expiry unknown to `active()`; twin/lease epochs not a joint cut; observed-synthetic rejection by the book; book-local successful composite; source-invalidated cached mandatory member still passed into standalone book; missing member rejection; revocation-requested renewal refusal; stale epoch revocation rejection. Expected source outcomes are encoded in `.engineering/evidence/M09-H02-SEMANTIC-PROBE-EVIDENCE.json`. The corresponding report compares **unselected** J1 joint owner critical section, J2 joint revision with at-use fencing, J3 conditional owner capability/commit; these are future questions, NOT selected architecture or executable designs.

8 additional strict source/document regression tests require 22 Git blob pins where referenced, the ratified issue #110 B-only D01 owner source and unchanged historic C01/C02, four OPEN HIGH freeze blockers, original 12 HX/6 LV all still NOT_EXECUTED, and no fake permission/approval. Exact-head CI target **4158/4158** (4136 baseline+14 semantic+8 documentary), 22/22 source pins, 10/10 changed paths, governance validator, pinned GEF/IRIS bridges, bounded separate same-assistant diff review with honest non-independent-review status, guarded protected squash at exact reviewed head and separate exact-main Governance PASS.

## STOP CONDITION
Do not confuse any newly EXECUTED `H02-Pxx` **in-memory synthetic fixture** with original HX/LV/C08/PO-C02/M12 scenarios, all NOT_EXECUTED, or with proof that M09 can issue a real coherent receipt. H01–H04 all remain OPEN HIGH_FOR_FUTURE_FREEZE; H02 remains OPEN_M09_OWNER_ATOMICITY_DECISION. M09 v1.0 FROZEN unchanged; C01 UNADOPTED_NOT_FROZEN; M11 v0.2 NOT_FROZEN with 86 OPEN, M12 v0.1 NOT_FROZEN with 110 OPEN and 80 future negatives not executed. M10/M11/M12 implementation NOT_ADMITTED; no new receipt, transport, authentication, GPU, OS, process, IPC, network, cloud action, provider permission, grant or true at-use proof. Keep #82/#110/#112/#128 OPEN and separately seek actual owner H01–H04 proof before any freeze/implementation.
