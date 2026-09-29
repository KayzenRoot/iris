# IRIS-WO-0029: Correct stale public project status and reconcile M12 exact-main evidence

Status: ADMITTED_FOR_DOCUMENTATION_AND_TESTS_ONLY
Tracking issue: #128 (remains OPEN); cross-links #82/#110/#112 (all remain OPEN)
Risk: LOW for public-doc/test integrity; inherited ELEVATED future-freeze owner blockers remain untouched
Context Lock base: `b137a99157df3c72b2eaaf7b6209da399802d580`; tree: `207d8c7b604ac07952609bbec766175776a88ab4`
Branch: `iris-wo-0029-public-status-evidence-20260927`

## OBJECTIVE
Repair two objectively outdated public documents (`README.md` and `docs/project-brain/01-PROJECT-OVERVIEW.md`), add fail-closed stale-status regression tests and reconcile the already independently bounded-reviewed IRIS-WO-0028 PR #135 final audited head and exact-main Governance #498/#499 into canonical checkpoint, backlog and the historical WO0028 evidence. Never convert source-only CI into owner adoption.

## CONTEXT
Git main `b137a99157df3c72b2eaaf7b6209da399802d580` exact-main Governance #499 run `36329122328`, job `108647545166` PASS 4009/4009. PR #135 final head `0addb0d768cfc7365fd0b492a4c83dcb790864e9` passed #498, run `36328992393`, job `108647169430`, 4009/4009 and 50/50 source-lock pins, 16/16 paths, validator/GEF/IRIS. Bounded PR review was a separate pass by the same assistant, not an independent person, and does not approve a module freeze.

## FILES / SOURCES TO READ
Startup order: canonical Checkpoint → Decisions Ledger → Scope → DoD → Architecture → Requirements, then AGENTS, Review Auto-Fix Policy, source hierarchy, current README/Project Overview, PR #135 evidence, M12 v0.1 contract candidate, M11/M09 owner blocker issues #82/#110/#112, the current checkpoint and backlog. Context Lock pins 18 exact Git-base source blobs.

## SCOPE
1. Update the public README and Project Overview to factual post-M09/M10/M11/M12 status, preserving verified historical M04/M05 milestones and directing readers to the canonical checkpoint.
2. Record PR #135 exact-reviewed-head and exact-main receipts with honest source-only statuses in checkpoint/backlog and add a `verifiedCloseout` record to WO0028 evidence.
3. Add five targeted stdlib regression tests that reject stale M04/M05 “next” claims, check canonical links/owner gates, verify checkpoint mirrors/machine nextStep, and assert retained source-only nonadmission.
4. Create this stable Work Order, Context Lock, Evidence Bundle and bounded audit target; require separate PR exact-head Governance and protected squash/exact-main before final approval.

## OUT OF SCOPE
Any change to product runtime, frozen M01–M10 contracts, IRIS/GEF pins, issue #110 owner A/B/C/DEFER choice, M09 lease/proof machinery, M11/M12 freeze/worker/process/queue/GPU/network/cloud actions, other issue closures, broad document cleanup, or any claim that 80 future cases were executed.

## REQUIREMENTS / ARCHITECTURE RULES
Git and canonical source hierarchy prevail. Checkpoint Markdown mirrors must be byte-identical and `CHECKPOINT.json.nextStep` equal the canonical NEXT STEP. M09 v1.0 FROZEN and extension UNADOPTED; M11 v0.2 NOT_FROZEN; M12 v0.1 PREPARED_FOR_OWNER_REVIEW_ONLY; 110 M12 questions and 86 M11 questions OPEN/UNRATED; 80 M12 future tests NOT_EXECUTED; four C02 H01..H04 HIGH_FOR_FUTURE_FREEZE OPEN. No new public owner port, API, default topology or external-resource operations.

## CONSTRAINTS
Only 12 explicitly authorized paths in the Context Lock; exact base SHA and 18 source SHA-1 pins. Do not promote proposal/evidence beyond exact checked facts. New tests use Python stdlib, no network/hardware. No rebase/force-push/history rewriting. No HIGH/CRITICAL introduced.

## ACCEPTANCE CRITERIA
Public pages have no obsolete “M04 next/M05 next” claims, accurately describe actual main `b137a99157df3c72b2eaaf7b6209da399802d580` and link to the canonical checkpoint. Verified #135 receipts match GitHub; 110/80/86/H01..H04 status and #82/#110/#112/#128 OPEN remain unchanged. Exact-base lock and changed-file allowlist pass. All five added tests pass, existing 4009 test baseline remains green (expected 4014 if unchanged), validator and GEF/IRIS pass in exact-head Governance. Separate same-assistant bounded documentary diff audit must report no new HIGH/CRITICAL; guarded protected squash only the reviewed head, then exact-main Governance PASS.

## TESTS
`python -m unittest discover -s tests -p "test_*.py" -v`, `python scripts/validate_governance.py`, exact PR Context Lock verifier in Governance workflow; inspect actual PR diff, GitHub CI, approved exact head and main final receipt.

## DELIVERABLES
Updated README, Overview, canonical/bridge checkpoint, JSON machine nextStep, backlog, WO0028 historical evidence, tests, WO0029 Work Order, Context Lock, Evidence Bundle, bounded audit target and protected PR.

## REVIEW FORMAT
Report objective source/diff/allowlist/fingerprint count, exact CI IDs and test totals, source-only authority boundaries, new vs inherited HIGH/CRITICAL findings, `APPROVED`/`CORRECTION REQUIRED`/`BLOCKED`, and proposed checkpoint delta in Brazilian Portuguese. Same-assistant review is never an independent human/owner approval.

## STOP CONDITION
Stop at a documented and exact-main-validated public-status repair. Keep #82/#110/#112/#128 OPEN; M12 PREPARED_FOR_OWNER_REVIEW_ONLY, owner adoption/freeze BLOCKED, all runtimes NOT_ADMITTED. The next owner-dependent substantive gate requires actual #110 decision/proof and cannot be inferred from this PR.
