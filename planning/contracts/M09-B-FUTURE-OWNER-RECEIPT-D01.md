# M09 B: bounded future owner-issued receipt, D01 design candidate

**Status:** OWNER_SELECTED_FOR_DOCUMENTARY_PLANNING_ONLY. **Work Order:** IRIS-WO-0033. **Owner decision:** [#110 ratified B direction](https://github.com/KayzenRoot/iris/issues/110#issuecomment-5857665032).

## 1. Selection, historical evidence and precise limits

The responsible user ratified **B_FUTURE_OWNER_RECEIPT** as the direction for planning a future M09-issued, versioned, immutable, request-scoped, read-only receipt and owner verifier for M09→M11. Only this architectural direction has been chosen. A and C are NOT_SELECTED; the current fail-closed handling when a port or proof does not exist continues without adopting public C. C01 `m09-evidence-handoff-candidate-v0.1` remains UNADOPTED_NOT_FROZEN, and existing frozen `m09-contract-v1.0` remains unchanged.

Source baseline: `97a9fe1666b764278de1379eadd7eda7d04799fe`, tree `a86e2553a630d93e64fefcf4fa9b722e10f81cd1`, Governance #509 PASS 4090/4090. The C01/C02 source snapshots deliberately retain their earlier `NONE`/`NOT_RECORDED` topology history; the later [owner-ratified issue comment](https://github.com/KayzenRoot/iris/issues/110#issuecomment-5857665032) and machine `.engineering/evidence/M09-B-OWNER-DIRECTION-D01.json` establish the **current, limited** architectural direction. This choice does not constitute owner approval of the proposed C01 port, H01–H04 proof or other unresolved M11/M12 questions.

## 2. Six conceptual roles, no adopted API or executable default

| Role | Proposed future owner responsibility | Blocked gate |
| --- | --- | --- |
| B-R01 M09 issuer | Immutable, versioned, owner-issued/verifiable receipt for one exact intended request. Receipt ≠ authorization to run. | H02/H03/H04 |
| B-R02 owner scope | Preserve exact M02 accepted work/revision, optional actual M06 attempt, original M09 resource/claims, target, action, consumer and issuer. Missing scope never fabricated. | H03/H04 |
| B-R03 joint cut | M09 must prove one coherent snapshot+lease decision for all mandatory composite members, epoch, revocation and expiry. Independent twin/lease locks are insufficient. | H02 |
| B-R04 at-use verifier | Owner-issued features/versions and source, reported observation origin (not synthetic), validity, full grant/claim match, no revoked/terminal ambiguity and verified time-of-use check. | H02/H03/H04 |
| B-R05 reverse M11 producer | Distinct M11 owner/process liveness and ACK, verified issuer/scope/freshness/UNKNOWN defaults, actual M54/M60 capability and rights. Accepted ACK is not resource reclaim. | H01/H03/H04 |
| B-R06 other owners | M12 placement, M54 trust/permissions, M60 OS capabilities, M58 optional publication/redaction, M02/M06 production state remain independent of the M09 receipt. | H01/H02/H03/H04 |

The table lists role requirements for later owner review, **not** settled wire fields, serialization, IPC, signature algorithm, TTL, hostname, cloud provider, permission or scheduling policy. All six roles remain CONCEPTUAL_NOT_ADOPTED. M09 still has no admitted positive cross-module proof today.

## 3. Mandatory no-authority behavior

- **Port not admitted/unavailable:** preserve `UNSUPPORTED` as the proposed caller disposition. Do not call raw `LeaseBook.active()` or derive a grant from a snapshot.
- **Port exists, source proof missing/unknown/unverifiable:** preserve `INDETERMINATE`; missing evidence cannot be translated into M09 owner `DENIED`.
- **Explicit owner `DENIED`:** only represent if a real M09 owner refusal with exact verifiable scope exists; original M09 statuses and provenance must remain distinct.
- **Synthetic/estimated/invalidated/quarantined/conflicting/stale sample, mixed epochs, missing mandatory member, expiry, preemption or revocation requested:** no positive projection. `Confidence.OBSERVED` does not erase `EvidenceOrigin.SYNTHETIC_FIXTURE`.
- **Even if future M09 grant were independently verified:** M11 execution remains nonadmitting until separate M02, M06, M11, M12, M54, M60 prerequisites are positively met; a low-cost M10 suggestion is never sufficient.

## 4. Four inherited HIGH future-freeze blockers, NONE CLOSED

| ID | Still-required separately owned proof | Current status |
| --- | --- | --- |
| C02-FR-H01 | M11→M09 authenticated owner/process liveness and exact request-correlated cooperative ACK, provenance/freshness/UNKNOWN and M54/M60 capability evidence. String prefix `M11:...` is insufficient. `ACCEPTED_AWAITING_RESOURCE_RECONCILIATION` retains `capacity_reclaimed=false`. | OPEN_OWNER_EVIDENCE_REQUIRED / HIGH_FOR_FUTURE_FREEZE |
| C02-FR-H02 | M09-owned atomic all-member snapshot+lease proof and expiry/revocation/epoch/TOCTOU recheck at intended use, not independently locked reads or generic serialized records. | OPEN_M09_OWNER_ATOMICITY_DECISION / HIGH_FOR_FUTURE_FREEZE |
| C02-FR-H03 | Actual independently reviewed M12 placement, M54 trust, M58 publication/redaction if used and M60 platform/OS owner contracts, with no invented protocols. | OPEN_FUTURE_OWNER_CONTRACTS / HIGH_FOR_FUTURE_FREEZE |
| C02-FR-H04 | Actual M02/M06/M09/M11 accepted work/revision/attempt/action/target/lease epoch binding, revocation-to-use fencing and independent attempt/outcome/materialization authority. | OPEN_CROSS_OWNER_DISPOSITION / HIGH_FOR_FUTURE_FREEZE |

## 5. Proof inventory, not execution

The original M09 C01 **HX-01..12 (12/12)** and C02 **LV-01..06 (6/6)** remain `SPECIFIED_NOT_EXECUTED`, as do 10 pre-existing C08 and eight PO-C02 design cases. They are references for a future separately admitted implementation harness, not tests executed by this documentary Work Order. The five M12 explicitly #110-linked questions `M12-S01-U05`, `M12-S02-U08`, `M12-S03-U02`, `M12-S04-U06`, `M12-S05-U04` remain OPEN/UNRATED and need their actual owners.

## 6. Planning acceptance and hard STOP

This D01 increment may update the canonical Decisions Ledger, source checkpoint/mirror/JSON, backlog and a historical Work Order checkpoint **only to reflect the real ratified architectural direction B**, never to promote proof, interface or implementation status. Its documentary integrity verifier and regression tests check source hashes, historical versus current selection, H01–H04 status and unopened future oracles. They cannot authenticate the issue comment offline or qualify OS/GPU/security behavior.

Before any C01 adoption or implementation: obtain the required real owner proofs H01–H04, applicable M02/M06/M11/M12/M54/M58/M60 contract dispositions, independent appropriately qualified contract/freeze review and **a separate explicit Work Order**. No selection of TTL/crypto/transport, no interface deployment, positive grant, automatic dispatch, lease mutation, process control, OS/GPU/network/cloud work or HX/LV execution in IRIS-WO-0033. M11 v0.2 NOT_FROZEN (86 OPEN); M12 v0.1 PREPARED_FOR_OWNER_REVIEW_ONLY/NOT_FROZEN (110 OPEN, 80 future negatives NOT_EXECUTED); M10/M11/M12 implementation NOT_ADMITTED. Keep #82/#110/#112/#128 OPEN.
