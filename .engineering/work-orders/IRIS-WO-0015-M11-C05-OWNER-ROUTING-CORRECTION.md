# IRIS-WO-0015 C05 — Correct incomplete owner routing and close C04 receipt

Status: ADMITTED_FOR_DOC_CORRECTION_ONLY | Risk: ELEVATED | Issue #82 OPEN
Base: `6e76ca2b4ffb731e0415f122afa9fba328bd8305` / tree `859cdbf5f76cf9bd9170f4a6ed9caa4dfbec550f`; branch `iris-wo-0015-m11-c05-owner-routing-correction-20260927`

## Objective

Record PR #107 exact-head Governance #447 (run 36312085887 / job 108599872403; 3,940/3,940), protected squash merge `6e76ca2b4ffb731e0415f122afa9fba328bd8305` and exact-main Governance #448 (run 36312139275 / job 108600021845; 3,940/3,940). Correct newly identified **ROUTE-C04-H01 HIGH_FOR_FUTURE_FREEZE_IF_UNCORRECTED**: C04 advisory triage marked three M11 topics available-owner-only although M11 candidate §9.1–9.3 requires later M12/M54/M60 owner proofs for corresponding restart, process observation or control evidence. There is no runtime impact or implementation authority because processes are already DISABLED. This C05 is a source-backed routing correction, **not** M12/M54/M60 interface selection, a policy decision, contract freeze or implementation.

Required corrected dependencies (all still pending owner-specific contracts): S01-U02 adds M12/M54/M60 for actual restart; S04-U04 adds M54/M60 for authorized OS process observation; S05-U03 adds M54/M60 for any real signal delivery/process-exit observation. Preserve all original 86 texts/IDs, statuses OPEN, risks UNRATED, and proof obligations NOT_EXECUTED. Revised routes: 20 M11-led future-owner gated, 1 M11 doc-proposable with current M09 review (S03-U08), 63 external-owner-led, 2 source verification. Owner dependencies are *proposed minimum, not exhaustive*. M02/M06/M09 remain canonical for their own decisions.

## Exact nine-path allowlist

- `.engineering/CHECKPOINT.json`
- `.engineering/CHECKPOINT.md`
- `.engineering/context-locks/IRIS-WO-0015-M11-C05-OWNER-ROUTING-CORRECTION.json`
- `.engineering/evidence/IRIS-WO-0015.json`
- `.engineering/evidence/M11-C05-OWNER-ROUTING-CORRECTED.json`
- `.engineering/work-orders/IRIS-WO-0015-M11-C05-OWNER-ROUTING-CORRECTION.md`
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/14-BACKLOG.md`
- `planning/reviews/M11-C05-ROUTING-RECHECK.md`

## Acceptance and STOP

43/43 unique Git blob fingerprints exact base; original 86/86 questions byte-identical, 8/8 proof obligations NOT_EXECUTED; only three routing rows have dependency/lanes corrected; all rows get explicit minimum/non-exhaustive caveat. JSON valid and checkpoint mirrors identical. CI PASS at exact PR head and separate bounded re-audit required before guarded protected squash merge and exact-main Governance. Leave PR OPEN/UNMERGED after authoring/CI for review; no process, IPC, queue, lease, policy, owner schema, freeze, M10/M11 implementation or Issue #82 closure admitted.
