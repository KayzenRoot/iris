# IRIS-WO-0017: enforce byte-exact checkpoint mirrors at governance validation

Status: ADMITTED_FOR_BOUNDED_GOVERNANCE_MAINTENANCE_ONLY | Issue #118 | Risk: ELEVATED_GOVERNANCE
Exact base: `467cea12c78b875d8a9966e48bde2dade8d48f8a` / tree `ed1454de247b7ad26e186b55f999dfebcf74f0d4` | branch `iris-wo-0017-checkpoint-mirror-guard-20260927`
Parent unrelated gate: M09/M11 #110 remains BLOCKED_PENDING_OWNER; this Work Order does not implement either product module.

## OBJECTIVE
Fix a verified local governance weakness: `scripts/validate_governance.py` compares STATUS, VERSION, PHASE and NEXT STEP but does not compare the two Markdown files byte-for-byte. This can let OBJECTIVE, IN PROGRESS or BLOCKERS divergence pass. Add a small, pure source-local checkpoint consistency helper and nine deterministic regression cases; preserve current CLI validator, source pins, GEF/IRIS bridges and entire 3,940-test historical suite. Reconcile already verified #117/C09 exact-main #464 receipts as part of this substantive guardrail increment.

## SOURCE CHECK AND PREFLIGHT
Read Git-canonical Checkpoint → Decisions → Scope → DoD → Architecture → Requirements, AGENTS and active review policy. Context Lock pins 27/27 Git blob SHA-1 values at the exact main above. Confirm base tree fully traversed, current checkpoint Markdown mirror equality, and the absence of another WO0017. IRIS local desktop state is not asserted by GitHub-only source audit; CI bridges remain required. Do not create work outside the 11 exact authorized paths.

## IMPLEMENTATION
Only `scripts/validate_governance.py`: exact byte comparison of Markdown bridge and canonical, then all existing checkpoint heading and machine-field validations; extract a testable pure helper and retain CLI `main()` behavior and existing pins. Only `tests/test_checkpoint_mirror_guard.py`: nine isolated in-memory test cases for equality, untouched previously unchecked section drift, LF/CRLF differences, original JSON target/status/nextStep mismatches. No changes to `.github/workflows`, external GEF, IRIS, frozen M09/M10/M11 contracts, runtime, security or actual process/IPC/lease behavior.

## FILE ALLOWLIST
- `scripts/validate_governance.py`
- `tests/test_checkpoint_mirror_guard.py`
- `.engineering/CHECKPOINT.json`
- `.engineering/CHECKPOINT.md`
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/14-BACKLOG.md`
- `.engineering/evidence/IRIS-WO-0015.json`
- `.engineering/evidence/IRIS-WO-0017.json`
- `.engineering/context-locks/IRIS-WO-0017-CHECKPOINT-MIRROR-GUARD.json`
- `.engineering/work-orders/IRIS-WO-0017-CHECKPOINT-MIRROR-GUARD.md`
- `planning/reviews/IRIS-WO-0017-CHECKPOINT-GUARD-AUDIT-TARGET.md`

## VALIDATION / ACCEPTANCE
Expected 27/27 exact-base source fingerprints, 11/11 authorized file paths; 9/9 newly introduced regressions and full-suite baseline plus nine if no other changes; governance CLI validator PASS; exact-head Governance checkout equals reviewed head, GEF/IRIS bridges and all tests PASS. Two Markdown mirrors must remain byte-identical; checkpoint JSON nextStep exact. Preserve old GEF SHA `866fe3af8cccc65c929aaf6a47a924401fa448b3`, IRIS SHA `a53b5b9fcf55c32a5696180fb1b1ef80ccd1edcf`. Do not claim nine passed before actual CI.

## AUDIT / STOP
Separate bounded review on exact FINAL PR head: source-scope, pure guard behavior, tests proof, no semantics weakened, source Context Lock and C09 receipt. Any newly introduced HIGH/CRITICAL requires in-branch fix and rerun. Leave PR OPEN after exact-head Governance for review; only guarded protected squash merge after APPROVED, then exact-main Governance. Keep #82/#110/#112 OPEN, #118 open until full protected completion; four C02 future freeze HIGHs and M09 owner decision still unresolved, no M10/M11 implementation admission.
