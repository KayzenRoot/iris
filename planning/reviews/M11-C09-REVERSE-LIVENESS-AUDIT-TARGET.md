# M11 C09 separate bounded source-review target

Status: PENDING_FINAL_HEAD_GOVERNANCE_AND_SEPARATE_BOUNDED_AUDIT | IRIS-WO-0015 | M11 planning only
Exact base: `885659cecdd8865bb713f80c1b503583311233e9`; tree `8767077dbed3599829855373a6bb7da2f829c581`. Never pre-award approval.

## Required independent review checks
1. Verify source Context Lock (38/38) unique exact-base Git blobs and actual PR file set exactly within the 11-path strict allowlist. Confirm base main is still the declared base, or mark STALE and rebase without force-push.
2. Cross-check C02 merge `885659cecdd8865bb713f80c1b503583311233e9`, PR #116 approved head `af4d829193833939903aa64d9b2b19220b81afb5`, exact-head Governance #461 (run 36315712111 / job 108609901760) and exact-main #462 (run 36315791781 / job 108610123330) 3,940/3,940. Check old C02 JSON was reconciled with recorded facts; no owner disposition is inferred.
3. Re-read exact-source `iris_resource_twin/recovery.py` including `OwnerLivenessRef` validation and `evaluate_cooperative_release`. Verify M11 string prefix is *not* described as authenticated issuer; ACCEPTED/timeout never means capacity reclaimed or termination. Compare with M11 v0.2 §§9.1–9.5; C02 scan/14 FC/12 owners/four open future-freeze blockers.
4. Check new research only proposes M11-owned logical producer/ack/UNKNOWN semantics and maps all six existing LV IDs without claiming execution; source ownership M02/M06/M09/M12/M54/M58/M60 remains intact. Detect accidental positive trust, PID reuse, automatic resource release, process action or hidden contract freeze.
5. Check M09 v1.0 83/15/514, C01 v0.1 UNADOPTED_NOT_FROZEN, M11 v0.2 NOT_FROZEN, all 86 M11 questions OPEN/UNRATED, C02-FR-H01..H04 OPEN, M10/M11 implementation NOT_ADMITTED, processes DISABLED and Issues #82/#110/#112 OPEN.
6. Confirm no code/test/script/frozen contract change. Verify JSON syntax, checkpoint Markdown mirrors and JSON nextStep. Inspect actual exact-head Governance validator/bridges/full-suite receipt; full-suite regression is not proof that LV/HX/C08/PO-C02 or physical/process tests ran.

## Review format and STOP
Report exact head/base SHA, finding IDs/impact/sources, tests and files reviewed, HIGH/CRITICAL specifically in the *new documentary scope*, known future-freeze HIGHs left open, and APPROVED / CORRECTION REQUIRED / BLOCKED. A separate same-assistant pass is **not** a distinct human reviewer. Leave PR OPEN until this review and exact-head pass. Only after APPROVED perform guarded protected squash merge and exact-main Governance; otherwise correction in same branch/PR. Do not promote owner adoption, freeze or implementation.
