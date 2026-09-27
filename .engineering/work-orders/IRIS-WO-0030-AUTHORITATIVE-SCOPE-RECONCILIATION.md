# IRIS-WO-0030: Repair stale authoritative Scope after M11 FTR/FCS and M12 candidate merge

Status: ADMITTED_FOR_BOUNDED_DOCUMENTARY_REPAIR_AND_REGRESSION_TESTS_ONLY
Issue: #128 (OPEN); dependencies #82/#110/#112 (OPEN)
Risk: LOW documentation-state repair; inherited H01-H04 remain HIGH_FOR_FUTURE_FREEZE
Exact Git base: `becf5cc4d4e3540d051b5402c0d930647f2ffdd8`; tree: `40d4af2d66b6e9375c445587fc522a173434d584`; branch: `iris-wo-0030-authoritative-scope-20260927`.

## OBJECTIVE / EVIDENCE
The source-hierarchy designates Scope as authoritative. On exact validated main following PR #136 and Governance #503 PASS 4014/4014, `docs/project-brain/03-SCOPE.md` still describes IRIS-WO-0028 as future and M11 Final Technology Review, FCS and v0.2 candidate as not yet completed. This is objectively contradicted by protected PRs #100/#117/#135/#136, source contracts, canonical checkpoint, and documented CI. Repair the current-status prose while preserving all approved architecture and genuine historical receipts.

## SOURCE ORDER / LOCK
Checkpoint → Decisions Ledger → Scope → DoD → Architecture → Requirements, then AGENTS, Source Hierarchy, README/Overview, M11/M12 candidate and verified CI #499/#503. Context Lock pins 18/18 exact-base Git blob SHA-1 sources including eight authority roots. Do not substitute HIVE-derived state for Git; HIVE handshake unavailable in this connector environment, but CI shall verify GEF/HIVE bridges.

## SCOPE / REQUIRED DELIVERABLES
Update only the current-state M11 and M12 paragraphs plus Scope's last next-step paragraph. Preserve historical M10/M11 receipts and normative ownership/exclusions. Add four small stdlib-only tests in a standalone Scope harness rejecting the three stale future-tense claims, requiring actual M11/M12 state and unchanged owner/non-admission gates, and matching the canonical checkpoint's owner gating. Write this Work Order, one pinned Context Lock, proposed Evidence Bundle, bounded diff audit target and historical in-repo checkpoint. Exactly 7 paths are authorized; no canonical checkpoint state change is needed because no module gate advances.

## OUT OF SCOPE / CONSTRAINTS
Do not touch runtime, frozen contracts, M09 topology A/B/C/DEFER choice, cross-owner grants, any actual owner answer, M11/M12 freeze, third-party pins, issue closures, GPU/OS/network/cloud execution, unrun HX/LV/WR/SQ/MG/FN/FT future cases or speculative new planning increments. No H01-H04 downgrade or FTR reference turned into adopted technology.

## ACCEPTANCE / TESTS / EVIDENCE
Scope reflects M11 FTR/FCS/v0.2 candidate and M12 PR #135/#136 as historical delivered source evidence; explicitly preserves 86+110 unanswered owner questions, 80 unexecuted M12 oracles, H01-H04 and all four OPEN issues, M10/M11/M12 NOT_ADMITTED. All four new focused tests and existing 4014-suite baseline must pass (expected total 4018); exact source lock, 7-path allowlist, governance, GEF/HIVE bridges and exact-head CI pass. Separate bounded documentary diff review by this assistant is not an independent person or owner decision. Guarded protected squash only audited head then exact-main CI PASS; post factual receipt in #128 without claiming freeze.

## REVIEW / STOP
Verdict is APPROVED_FOR_DOC_TEST_ONLY, CORRECTION_REQUIRED or BLOCKED based on actual head evidence; zero new HIGH/CRITICAL permitted. STOP after exact-main Scope alignment. All #82/#110/#112/#128 remain OPEN; actual #110 owner answer/proofs or explicit owner-approved carve-out remains the next substantive gating input.
