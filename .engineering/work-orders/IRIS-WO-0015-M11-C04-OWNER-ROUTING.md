# IRIS-WO-0015 C04 — M11 owner routing and C03 post-merge checkpoint

Status: ADMITTED_FOR_PLANNING_DOCS_ONLY | Risk: ELEVATED | Issue #82 OPEN
Base: `3df76a21f113959b01127c05d20eb7abe5a5a269` | base tree: `730993accc15c20d9669645f2cc68a9b0abd539a`
Branch: `iris-wo-0015-m11-c04-owner-routing-20260927`

## Objective

1. Reconcile PR #106 C03: exact head `e608c95dee84363ffd09b88ef315c16b265fe8d5`, Governance #445 run `36292142852`, job `108544149198`, 3940/3940; protected squash merge `3df76a21f113959b01127c05d20eb7abe5a5a269`, Governance #446 run `36292194144`, job `108544291487`, 3940/3940.
2. Classify the 86 original still-OPEN S01–S05 questions by **proposed primary decision owner** and coordination candidates, keyed strictly to the verified C03 register, preserving every original question and source Git SHA, marking index-only future owner handoffs as pending.
3. Link eight previously defined PO-C02 proof obligations, NOT_EXECUTED; do not infer owner contracts, thresholds, runtime permission, CI proof of process safety or resolution of any question.

## Bounded allowlist

- `.engineering/CHECKPOINT.json`
- `.engineering/CHECKPOINT.md`
- `.engineering/context-locks/IRIS-WO-0015-M11-C04-OWNER-ROUTING.json`
- `.engineering/evidence/IRIS-WO-0015.json`
- `.engineering/evidence/M11-C04-OWNER-ROUTING.json`
- `.engineering/work-orders/IRIS-WO-0015-M11-C04-OWNER-ROUTING.md`
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/14-BACKLOG.md`
- `planning/reviews/M11-C04-OWNER-ROUTING.md`

## Acceptance and STOP

- Exact-base Context Lock 39/39 unique present base-tree source blobs; exactly nine authorized doc/evidence paths, JSON parseable; 86/86 original questions unchanged and OPEN/UNRATED, eight POs unexecuted; reviewer verifies every proposed owner against exact source/available M02/M06/M09/M10 contract boundaries and M12–M60 index-only status. Checkpoint JSON/Markdown mirrors byte-identical. Exact PR-head Governance success and a separate bounded review are required before any protected merge and exact-main Governance.
- All proposed owner routing is advisory documentation only; no owner accepts it until separately source-backed. M11 candidate v0.2 NOT_FROZEN, M10/M11 implementation NOT_ADMITTED, all callable process actions DISABLED, issue #82 OPEN; M12–M60 PENDING/UNRATED. No OS/IPC/technology/policy selection, resource mutation or live process/worker actions permitted. Stop with PR OPEN and UNMERGED for review.
