# M11 C04 — Owner routing and blocker traceability (proposal)

Status: PROPOSED_FOR_SEPARATE_REVIEW | Work Order IRIS-WO-0015 | Issue #82 OPEN
Base `3df76a21f113959b01127c05d20eb7abe5a5a269` / tree `730993accc15c20d9669645f2cc68a9b0abd539a`. This is classification, **not** 86 answered decisions, owner acceptance, risk reduction, a frozen M11 contract, or any runtime authorization.

## C03 exact-main closeout

PR #106 head `e608c95dee84363ffd09b88ef315c16b265fe8d5` passed exact-head Governance #445 (`36292142852` / `108544149198`; 3,940/3,940). Protected squash merge `3df76a21f113959b01127c05d20eb7abe5a5a269` passed exact-main Governance #446 (`36292194144` / `108544291487`; 3,940/3,940), checkout SHA confirmed. C03's original 86-question intake and eight PO-C02 obligations are now Git-canonical as a traceability register. It made no owner decisions and did not execute safety tests.

## Per-question routing

The machine-readable `.engineering/evidence/M11-C04-OWNER-ROUTING.json` preserves all 86 original question texts, IDs, exact source paths/recorded source Git blob hashes, proposed primary owner, coordination candidates, missing-future-owner references and a conservative lane. Every question remains **OPEN** and its actual risk **UNRATED**. Owner routing cannot grant contract or dispatch authority. No owner-specific interface is guessed from an index heading.

| Routing lane | Count | Meaning |
| --- | ---: | --- |
| M11-led blocked by missing future owner contracts | 17 | M11 may draft only non-executable interface questions; cannot settle external permission/policy. |
| M11 documentation proposable with available-owner review | 4 | M11 may draft safe evidence/refusal semantics; M02/M06/M09 decisions still require their source-backed acceptance. |
| External-owner decision required | 63 | Proposed primary authority outside M11 must resolve its own semantics through proper module governance. |
| Source-reuse verification | 2 | S01-U09 and S04-U21 require current source-proven provenance; unverified UGAS/HIVE/CORE material grants no authority. |
| **Total** | **86** | 86/86 OPEN and UNRATED; no decision selected. |

Proposed primary routing counts (not a priority ranking): M11 23, M60 15, M54 9, M09 11, M06 7, M56 5, M02 6, M12 8, M26 2. The future-owner-dependent occurrences across all records are: M60 31, M12 23, M54 20, M56 11, M26 6, M58 5, M55 4, M53 1. Counts overlap intentionally when several contracts govern a single question.

## Authority and evidence gates

- **Existing owner contracts:** M02 owns ExecutionPlan/production causality; M06 owns operational attempts/materialization and reproducibility under M02; M09 owns grants/leases/resource truth; frozen M10 only advises and never dispatches or authorizes anything.
- **Future pending owner contracts:** M12 orchestration/placement, M54 security/principal authorization, M60 platform/process rights, and all other M12–M60 index-level owners have no current detailed M11 handoff. Keep `PENDING_OWNER_CONTRACT` and `UNRATED` until their own source-backed module review.
- **PO-C02-01..08:** existing negative scenarios remain DEFINED_NOT_EXECUTED and receive no fake synthetic/OS pass from docs Governance. No PID-only control, inferred local placement, grant from sampled telemetry, automatic retry/relaunch or result/materialization from process exit.

## Next independent decisions

Start with the four M11-led documentation-proposable questions only as **drafts** and require M02/M06/M09 agreement where relevant. Route M12/M54/M60-specific questions to their future individual contract planning; leave blocked question dispositions OPEN or explicitly deferred subject to independent freeze-readiness audit. Do not permit runnable worker/process APIs until owner authorization, platform rights and eight negative proof obligations have been independently proven in a separately admitted runtime Work Order. Nothing here freezes M11 or admits M10/M11 runtime.

## Gate

C04 exact-head Governance and separate scope-limited review are necessary before protected squash merge/exact-main closeout. 39/39 pinned base-source fingerprints, nine allowlisted files, and machine-to-source 86/86 identity checks are audit requirements.
