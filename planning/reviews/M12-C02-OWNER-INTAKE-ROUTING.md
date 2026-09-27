# M12 C02: source-exact owner-intake queues for real owner review

**Status:** ROUTING_ONLY_ALL_OWNER_DECISIONS_PENDING | Work Order IRIS-WO-0031 | Issue #128 OPEN.
**Canonical data:** `.engineering/evidence/M12-OWNER-DECISION-REGISTER.json` (110 original OPEN/UNRATED questions, 80 future cases SPECIFIED_NOT_EXECUTED); new **derived** queue `.engineering/evidence/M12-OWNER-INTAKE-C02.json` and fail-closed `scripts/verify_m12_owner_intake.py`.
**Base:** `cccc9f3cd23be53e6154f605a37eb9cd6f28b1ca`, tree `f3178da68514279ef5454b8520debed6871d7416` (prior exact-main Governance #505 PASS 4018/4018). This document only prepares review and cannot itself record a single actual owner acceptance.

## Why this narrows the next work

The M12 v0.1 owner candidate (PR #135) has 24 proposed invariants and nine non-public conceptual boundaries; the FTR's 16 references and FCS's 48 indexed future owners do not select technology, create APIs or authorize execution. The C02 intake layer makes the already source-listed responsibilities addressable without reopening S01–S05, fabricating risk scores or mistaking a source-owner mention for permission. The five **mutually exclusive organizational lanes are not severity rankings and do not imply any lane is ready to freeze**.

| Routing lane | Original questions | What can actually be done |
| --- | ---: | --- |
| EXPLICIT_ISSUE_110_REVIEW | 5 | Submit the exact owner decision request in Issue #110, no A/B/C/DEFER assumption. |
| LATER_OWNER_CONTRACT_REQUIRED | 70 | Route to the exact originally cited M13–M60 future owner(s). Their master-index headings are reference only, not approved ports. |
| M11_CANDIDATE_CROSS_OWNER_REVIEW | 13 | Compare M11 v0.2 proposal with frozen owner facts; M11 NOT_FROZEN and H01 still OPEN. |
| FROZEN_OWNER_HANDOFF_REVIEW | 3 | Ask frozen-source owner(s) for exact cross-owner interface disposition; old in-process facts do not prove new M11/M12 grants. |
| M12_PROPOSABLE_WITH_FROZEN_SOURCE_INPUTS | 19 | Author **nonbinding** M12 question-level proposals grounded in existing M02/M06/M09/M10 sources for later actual M12 owner decision; no positive grant, selection or runtime. |

All 110 are **OPEN/UNRATED_PENDING_OWNER** and all 80 future WR/SQ/MG/FN/FT scenarios remain **SPECIFIED_NOT_EXECUTED**. These lanes are derived from original `owners` labels, not from an inferred priority, assistant-selected owner, or implemented API. The 17 module queues overlap: a question listed for several owners appears in each of those queues. From the source labels, M12 occurs in 72 questions, M54 in 39, M11 in 30, M60 in 27 and M09 in 23; these are occurrences, **not** approvals or 110 disjoint assignments.

## Exact five explicit #110 owner-decision requests

| Original ID | Exact owner label | Source question, not answer |
| --- | --- | --- |
| M12-S01-U05 | M09/#110 | What jointly coherent M09 snapshot+lease evidence can qualify current per-action resource admission? |
| M12-S02-U08 | M12/M09/#110 | What coherent per-request M09 lease+snapshot recheck is needed before any positive placement? |
| M12-S03-U02 | M09/#110 | Can M09 prove one coherent jointly owned snapshot+lease cut for all mandatory GPU/CPU/RAM members, including epoch/revocation? |
| M12-S04-U06 | M09/#110 | Which owner-approved M09 grant could bind remote per-device resources and all group members coherently? |
| M12-S05-U04 | M09/#110 | How does M09 prove that an interrupted request's capacity was actually reclaimed? |

These five do **not** exhaust all M09/M11 integration dependencies: all owner links remain visible per question. Real #110 disposition must specify A/B/C/limited stages/DEFER in the owner's own decision record plus source-backed proofs of the independent H01 reverse M11→M09 liveness, H02 atomic member-complete M09 snapshot+lease and at-use invalidation, H03 M12/M54/M58/M60 owner contracts, and H04 M02/M06 exact work/attempt/revocation-to-action. An explicit deferral is allowed but does not close a freeze gate.

## Review sequence without freezing anything

1. Use the machine `explicitIssue110QuestionIds` and `ownerQueues` for **discussion intake only**. An actual owner, not CI or assistant comments, answers each applicable question with its own source, validation and risk classification.
2. The 19 M12-proposable questions may receive separately gated source-only candidate analysis while the topology remains unresolved. For example M12-S02-U01 concerns consuming an existing M02 accepted-work reference, whereas M12-S01-U13 still depends on M09 composite-grant semantics. No positive placement may arise from either.
3. When actual M54/M58/M60 and other future-owner contracts exist, update the source register under a fresh authorized Work Order and re-run re-derivation against the new exact Git state. Never use today's index-only classification as a permanent owner API.
4. After *every* original M12 question receives actual adjudication, revisit FR-03. After H01–H04 and other substantive owners are evidenced, perform the distinct freeze/readiness audit, eventual separately authorized implementation and real qualified negative/OS/GPU/network tests. None of that occurs in IRIS-WO-0031.

## Hard STOP

M09 v1.0 remains FROZEN; M09 C01 handoff UNADOPTED; M11 v0.2 NOT_FROZEN (86 original OPEN questions); M12 v0.1 PREPARED_FOR_OWNER_REVIEW_ONLY/NOT_FROZEN (110 OPEN/UNRATED, 80 unexecuted); M10/M11/M12 implementations NOT_ADMITTED, OS/GPU/network/cloud actions DISABLED. Issue #110 topology NONE_SELECTED, H01–H04 OPEN HIGH_FOR_FUTURE_FREEZE and issues #82/#110/#112/#128 stay OPEN. Source integrity tests certify only the deterministic mirroring and nonpromotion checks, never owner agreement or physical runtime safety.
