# M12 C03: 19 source-constrained owner discussion packets

Status: **NONBINDING_SOURCE_DISCUSSION_ONLY** | IRIS-WO-0032 | Issue #128 OPEN.

The 19 source-derived M12-proposable original questions remain OPEN/UNRATED. This report adds source-anchored discussion proposals and specific unresolved proof gaps, and cross-references existing future negative oracles without claiming execution. Existing frozen contracts constrain interpretation, **not** M12 cross-owner acceptance. The other 91 original questions and all 80 NOT_EXECUTED future cases remain untouched. Neither a priority ranking nor an owner decision is derived.

## M12-S01-U13 | M12/M09

**Original question:** How are composite member grants and mismatched expiry/revocation handled without partial admission?

**Nonbinding discussion:** Review composite membership as an indivisible owner-proven set, not independent apparently-fresh observations.

**Owner proof still missing:** No joint M09 snapshot+lease decision, at-use invalidation or member revocation rule exists.

**Pinned owner-source anchors:** `M09` [docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md](../../docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md) (`Composite claims, grants and transfers report atomicity and per-member outcomes.`); `C01` [planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md](../../planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md) (`Status: **PROPOSED_UNADOPTED_NOT_FROZEN**`).

**Existing future negative test designs, all NOT_EXECUTED:** WR-09. Inherited blocker references: C02-FR-H02.

## M12-S01-U15 | M12/M02/M06

**Original question:** Can duplicate announcements from two nodes ever imply a new attempt or retry? (Default: no claim.)

**Nonbinding discussion:** Treat repeated announcements as observations only; retain distinct M02 work and M06 attempt identities.

**Owner proof still missing:** A genuine cross-owner work-to-attempt epoch and external-effect dedup decision is missing.

**Pinned owner-source anchors:** `M02` [planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`semantic object ID != content/revision ID != attempt ID;`); `M06` [planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`M02 semantic identity != M02 revision/snapshot != M06 operational revision`).

**Existing future negative test designs, all NOT_EXECUTED:** WR-10. Inherited blocker references: C02-FR-H04.

## M12-S01-U17 | M12/M10

**Original question:** How is M10's plan recommendation kept separate from M12 placement and all owner grants?

**Nonbinding discussion:** Keep versioned M10 recommendations strictly advisory, separate from future M12 consideration.

**Owner proof still missing:** No M12 placement, resource, process or trust authorization follows from optimizer advice.

**Pinned owner-source anchors:** `M10` [planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`A recommendation SHALL NOT imply reservation, placement, dispatch, worker control, provider submission or authorization.`).

**Existing future negative test designs, all NOT_EXECUTED:** WR-11. Inherited blocker references: none per-item; all four remain open globally.

## M12-S02-U01 | M02/M12

**Original question:** What canonical accepted M02 work/plan reference permits queue consideration without manufacturing M02 state?

**Nonbinding discussion:** A prospective queue association could reference only exact owner-issued M02 accepted work; it cannot create accepted state.

**Owner proof still missing:** M02-to-M12 queue semantics, epoch revalidation and M06 optional attempt linkage require real cross-owner decision.

**Pinned owner-source anchors:** `M02` [planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`semantic object ID != content/revision ID != attempt ID;`).

**Existing future negative test designs, all NOT_EXECUTED:** SQ-01. Inherited blocker references: C02-FR-H04.

## M12-S02-U04 | M12/M02

**Original question:** Who supplies allowable priority policy evidence and can it vary by project?

**Nonbinding discussion:** Preserve M02 accepted-work scope while considering priority only as an unselected M12 policy question.

**Owner proof still missing:** There is no approved project-priority source, selected policy or authorized M54 override.

**Pinned owner-source anchors:** `M02` [planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`semantic object ID != content/revision ID != attempt ID;`).

**Existing future negative test designs, all NOT_EXECUTED:** SQ-06. Inherited blocker references: none per-item; all four remain open globally.

## M12-S02-U07 | M12/M09

**Original question:** Are hard quotas policy limits or M09 grants, and how are they separately versioned?

**Nonbinding discussion:** Keep proposed project quotas and M09-issued live grants in separate versioned source namespaces.

**Owner proof still missing:** M12 quota policy and the M09 joint per-request grant handoff are unapproved.

**Pinned owner-source anchors:** `M09` [docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md](../../docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md) (`Composite claims, grants and transfers report atomicity and per-member outcomes.`); `C01` [planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md](../../planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md) (`Status: **PROPOSED_UNADOPTED_NOT_FROZEN**`).

**Existing future negative test designs, all NOT_EXECUTED:** SQ-05. Inherited blocker references: C02-FR-H02.

## M12-S02-U09 | M12/M09

**Original question:** How are unknown/stale quota or headroom estimates represented without positive claims?

**Nonbinding discussion:** Represent unknown, stale, contradicted, revoked or unsupported estimates as non-admitting observations.

**Owner proof still missing:** The M09 coherent at-use validity port and owner-approved fallback do not exist.

**Pinned owner-source anchors:** `M09` [docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md](../../docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md) (`Composite claims, grants and transfers report atomicity and per-member outcomes.`); `C01` [planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md](../../planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md) (`Status: **PROPOSED_UNADOPTED_NOT_FROZEN**`).

**Existing future negative test designs, all NOT_EXECUTED:** SQ-02, SQ-03. Inherited blocker references: C02-FR-H02.

## M12-S02-U13 | M12/M06

**Original question:** Can expected duration/VRAM be used for backfill, and what uncertainty bounds are required?

**Nonbinding discussion:** Compare proposed duration/VRAM only as uncertain evidence-linked projections without promoting M06 outcome history into a forecast guarantee.

**Owner proof still missing:** Calibrated estimator, uncertainty threshold, safe backfill policy and permission to preempt remain undefined.

**Pinned owner-source anchors:** `M06` [planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`M02 semantic identity != M02 revision/snapshot != M06 operational revision`).

**Existing future negative test designs, all NOT_EXECUTED:** SQ-14. Inherited blocker references: none per-item; all four remain open globally.

## M12-S02-U17 | M12/M02/M06

**Original question:** Who decides cancellation/retry/idempotency when a queued job's plan or attempt changes?

**Nonbinding discussion:** Keep cancellation intent, M02 work supersession and M06 attempt receipts distinct; a stale ranking is not a retry.

**Owner proof still missing:** Epoch/fencing, idempotent external-effect disposition and H04 handoff are unresolved.

**Pinned owner-source anchors:** `M02` [planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`semantic object ID != content/revision ID != attempt ID;`); `M06` [planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`M02 semantic identity != M02 revision/snapshot != M06 operational revision`).

**Existing future negative test designs, all NOT_EXECUTED:** SQ-08, SQ-09. Inherited blocker references: C02-FR-H04.

## M12-S02-U20 | M12/M10

**Original question:** How does advisory optimization input stay separate from admitted scheduling and proof?

**Nonbinding discussion:** Present M10 advice as a separately versioned input; preserve distinct M12 selection and M09 lease proofs.

**Owner proof still missing:** No admitted M10 implementation, M12 scheduler or authoritative resource handoff exists.

**Pinned owner-source anchors:** `M10` [planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`A recommendation SHALL NOT imply reservation, placement, dispatch, worker control, provider submission or authorization.`).

**Existing future negative test designs, all NOT_EXECUTED:** SQ-11. Inherited blocker references: none per-item; all four remain open globally.

## M12-S03-U01 | M09/M12

**Original question:** What exact request-scoped per-device claims may future composite placement consume from a separately admitted M09 owner port?

**Nonbinding discussion:** Record intended request and per-device members only as candidate inventory until M09 issues a member-complete receipt.

**Owner proof still missing:** M09 C01 is unadopted, issue #110 topology is undecided and H02 proof is absent.

**Pinned owner-source anchors:** `M09` [docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md](../../docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md) (`Composite claims, grants and transfers report atomicity and per-member outcomes.`); `C01` [planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md](../../planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md) (`Status: **PROPOSED_UNADOPTED_NOT_FROZEN**`).

**Existing future negative test designs, all NOT_EXECUTED:** MG-01. Inherited blocker references: C02-FR-H02.

## M12-S03-U03 | M12/M09

**Original question:** How does each member's freshness/expiry and time-of-use revalidation work without mixing different observation epochs?

**Nonbinding discussion:** Require future member-complete M09 epoch, expiry, revocation and at-use verification; never assemble independent samples.

**Owner proof still missing:** The future atomic M09 snapshot+lease owner port remains unapproved under H02.

**Pinned owner-source anchors:** `M09` [docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md](../../docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md) (`Composite claims, grants and transfers report atomicity and per-member outcomes.`); `C01` [planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md](../../planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md) (`Status: **PROPOSED_UNADOPTED_NOT_FROZEN**`).

**Existing future negative test designs, all NOT_EXECUTED:** MG-02, MG-03. Inherited blocker references: C02-FR-H02.

## M12-S03-U12 | M12/M09

**Original question:** How are per-device headroom and the 8 GB-class production route preserved without summing unrelated VRAM?

**Nonbinding discussion:** Preserve separate per-device VRAM evidence and independently qualified 8GB-class routes; do not add unrelated VRAM.

**Owner proof still missing:** M09 member grant, model/provider sharding qualification and physical performance evidence are missing.

**Pinned owner-source anchors:** `M09` [docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md](../../docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md) (`Composite claims, grants and transfers report atomicity and per-member outcomes.`); `C01` [planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md](../../planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md) (`Status: **PROPOSED_UNADOPTED_NOT_FROZEN**`).

**Existing future negative test designs, all NOT_EXECUTED:** MG-11. Inherited blocker references: C02-FR-H02, C02-FR-H03.

## M12-S03-U14 | M02/M06/M12

**Original question:** Which exact plan/attempt/output lineage binds each split subtask without promoting partial output to success?

**Nonbinding discussion:** Tie each proposed shard to exact M02 work and distinct M06 revision/attempt/output lineage; partial output never implies success.

**Owner proof still missing:** Shard aggregation, parent acceptance, external effects and H04 replay semantics require owner decision.

**Pinned owner-source anchors:** `M02` [planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`semantic object ID != content/revision ID != attempt ID;`); `M06` [planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`M02 semantic identity != M02 revision/snapshot != M06 operational revision`).

**Existing future negative test designs, all NOT_EXECUTED:** MG-08, MG-13. Inherited blocker references: C02-FR-H04.

## M12-S03-U18 | M12/M10

**Original question:** How are advisory cost/quality/latency estimates kept separate from M12 selection and M09 lease authorization?

**Nonbinding discussion:** Keep predicted cost/quality/latency as M10 advisory evidence; no score becomes grant, placement or rights permission.

**Owner proof still missing:** Any real M12 selection, M09 lease handoff or platform permission remains unadopted.

**Pinned owner-source anchors:** `M10` [planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`A recommendation SHALL NOT imply reservation, placement, dispatch, worker control, provider submission or authorization.`).

**Existing future negative test designs, all NOT_EXECUTED:** MG-16. Inherited blocker references: C02-FR-H02.

## M12-S03-U21 | M12/M06

**Original question:** How will the outcome distinguish data parallel output aggregation from merely observed worker process exits?

**Nonbinding discussion:** Request actual M06 disposition of verified materialization and accepted output; worker exit remains observation only.

**Owner proof still missing:** No adopted shard aggregation/immutable provenance-to-parent acceptance handoff exists.

**Pinned owner-source anchors:** `M06` [planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`M02 semantic identity != M02 revision/snapshot != M06 operational revision`).

**Existing future negative test designs, all NOT_EXECUTED:** MG-13. Inherited blocker references: C02-FR-H04.

## M12-S05-U07 | M02/M06/M12

**Original question:** Who decides the future retry budget, attempt revision and dedup semantics?

**Nonbinding discussion:** Treat retry budget and dedup as M02/M06 owner questions; preserve exact work, attempt and external-effect identities.

**Owner proof still missing:** No actual epoch/fencing/retry cap or H04 owner-authorized replay proof exists.

**Pinned owner-source anchors:** `M02` [planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`semantic object ID != content/revision ID != attempt ID;`); `M06` [planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`M02 semantic identity != M02 revision/snapshot != M06 operational revision`).

**Existing future negative test designs, all NOT_EXECUTED:** FT-04, FT-19. Inherited blocker references: C02-FR-H04.

## M12-S05-U08 | M02/M06/M12

**Original question:** What effect classes are non-idempotent and must require explicit owner/operator adjudication?

**Nonbinding discussion:** Distinguish potentially non-idempotent external effects from M06 attempts; no inferred replay before owner adjudication.

**Owner proof still missing:** An authorized effect-class catalog and operator procedure are not selected; M02 idempotency law is not per-effect proof.

**Pinned owner-source anchors:** `M02` [planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`semantic object ID != content/revision ID != attempt ID;`); `M06` [planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md](../../planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md) (`M02 semantic identity != M02 revision/snapshot != M06 operational revision`).

**Existing future negative test designs, all NOT_EXECUTED:** FT-04. Inherited blocker references: C02-FR-H04.

## M12-S05-U18 | M12/M09

**Original question:** What resource protection keeps user-interactive 8GB hardware responsive during preemption decisions?

**Nonbinding discussion:** Keep workstation interaction policy distinct from M09 conservative resource truth and verified actual reclamation.

**Owner proof still missing:** No numeric interactive reserve, override, process right or at-use M09 composite grant exists.

**Pinned owner-source anchors:** `M09` [docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md](../../docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md) (`Composite claims, grants and transfers report atomicity and per-member outcomes.`); `C01` [planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md](../../planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md) (`Status: **PROPOSED_UNADOPTED_NOT_FROZEN**`).

**Existing future negative test designs, all NOT_EXECUTED:** FT-13, FT-02. Inherited blocker references: C02-FR-H02.

## Exact freeze STOP

M09 #110 A/B/C/limited stages/DEFER **NONE_SELECTED**; C02 H01–H04 **OPEN HIGH_FOR_FUTURE_FREEZE**; M09 C01 **UNADOPTED**; M11 v0.2 **NOT_FROZEN** (86 OPEN); M12 v0.1 **PREPARED_FOR_OWNER_REVIEW_ONLY/NOT_FROZEN** (110 OPEN, 80 future cases NOT_EXECUTED); M10/M11/M12 runtime **NOT_ADMITTED**. No claimed actual owner signoff, technology selection, OS/GPU/network/cloud execution, grant or runtime test. Any source or owner change requires a new exact Git lock, qualified review and separately admitted Work Order.
