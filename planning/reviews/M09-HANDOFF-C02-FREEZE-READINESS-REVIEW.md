# M09 C02 independent source-review target and owner decision form

Status: PENDING_SEPARATE_BOUNDED_AUDIT | WO0016 planning-only | Issues #112/#110/#82 OPEN

## Auditor tasks at the final exact PR head

Verify 79/79 unique pinned base Git blobs and ten authorized documentation/evidence paths. Compare all 14 FC-09 rows line by line to the original FCS; all 12 owner lanes must reflect actual source depths. Verify previous C01 canonical documentary status with PR #115 exact-head Governance #459, protected merge and exact-main Governance #460; no owner decision is implied. Confirm C01 original contract and M09 frozen 83/15/514 source are **unmodified**.

In `iris_resource_twin/recovery.py` independently re-read `OwnerLivenessRef` (source lines 525–541), `confirm_leak` (551–570), `CooperativeReleaseRequest/Response` (574–603), `evaluate_cooperative_release` (483–499). Check that the M11 string prefix in `authority_ref` is **not asserted** to be authenticated cross-process provenance; actual owner-issued process liveness/rights require a new separate source-backed handoff. Check that `ACCEPTED_AWAITING_RESOURCE_RECONCILIATION` and `capacity_reclaimed=false` cannot be turned into a positive grant. Compare snapshot/lease independent locks and M09 FC-09-07 composite atomicity to prevent a falsely coherent read. Confirm all four future-freeze HIGH blockers remain OPEN/UNRATED under owner-specific review.

Verify `LV-01..06` are distinct **SPECIFIED_NOT_EXECUTED** cases, each noDispatch/noM09Mutation, in addition to 12 HX, 10 C08 and eight PO-C02. No semantic simulator is being claimed. A passing 3,940-test Governance baseline proves repository regression only, not execution of new LV/HX or live OS/GPU/process safety.

## Decision-ready questions for actual owners, not inferred approvals

1. **M09/M11 reverse handshake (FC-09-03):** Which M11-owner-issued liveness states and freshness, privilege, process capability and issuer verification may M09 accept? How is `UNKNOWN` handled without converting a candidate leak into confirmed recovery? Which owner owns request, delivery and acknowledgment of cooperative release?
2. **M09 grant consistency (FC-09-07):** What single-owner atomic read/validation path proves required composite members, member outcomes, lease epoch and revocation invalidation at time of use? If none, retain nonpositive scope.
3. **M12/M54/M58/M60 boundaries (FC-09-04/09):** Who defines placement target, read-request principal, redaction/trust, published schema and platform capability? These detailed owner contracts do not currently exist.
4. **M02/M06/M09/M11 interaction:** Which exact M02 accepted plan, M09 grant and M06 attempt/materiality refs may accompany future process evidence, and how is a stale/foreign resource receipt rejected without false attempt completion?
5. **A/B/C topology:** Does the M09 owner adopt restricted in-process A, future owner-issued per-request B, negative-only C, a permitted combination or defer? Do not assign a selection without owner-sourced approval.

## Scope-limited verdict logic

No unresolved HIGH/CRITICAL in the **documentation-only scan itself** may permit its promotion after exact-head CI and independent audit, while four HIGH **future-freeze blockers** remain explicitly OPEN and prohibit declaring owner-extension freeze or positive M11 process admission. This audit is a checklist, not a pre-awarded approval. Post-merge exact-main CI must then confirm documentary baseline; the next meaningful gate is the actual M09 owner response at #110 or separately admitted owner-specific research, not another receipt-only PR.
