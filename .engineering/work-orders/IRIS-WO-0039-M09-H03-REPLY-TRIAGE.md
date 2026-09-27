# IRIS-WO-0039: H03 local offline TRIAGE harness for untrusted future owner replies

**Admitted scope:** offline source-bound **UNTRUSTED_DRAFT_FORMAT_ONLY**, no owner/freeze review or real implementation. Existing owner inboxes [M12 #128](https://github.com/KayzenRoot/iris/issues/128), [M54 #145](https://github.com/KayzenRoot/iris/issues/145), [M58 #146](https://github.com/KayzenRoot/iris/issues/146), [M60 #147](https://github.com/KayzenRoot/iris/issues/147) were live checked OPEN, without actual reviewed owner responses. All four H01–H04 inherited HIGH freeze blockers OPEN. User-ratified B_FUTURE_OWNER_RECEIPT only future documentary M09→M11 direction; original C01 remains UNADOPTED_NOT_FROZEN.

**Exact source base:** main `47a1a41096ebb3153e7e5918edeedb58a0706154`, tree `af5ddf3fa2de211a3c1bf3d48df7fd801d27793c`, preceding WO0038 [protected PR #148](https://github.com/KayzenRoot/iris/pull/148), [exact-main Governance #526](https://github.com/KayzenRoot/iris/actions/runs/36343355054) run 36343355054/job 108687618373 PASS **4260/4260**, GEF/HIVE pinned bridges PASS.

## New substantive work

Build local standard-library Python CLI `scripts/triage_m09_h03_untrusted_owner_reply.py` that accepts only a **local JSON draft** and first verifies the independently governed exact original H03 WO0037 + E01 WO0038 owner/source packets and seven inherited exact source Git blobs. A valid-looking 40-hex Git SHA, contract path, claimed GitHub PR or comment URL, self-identified author or completed question queue remains explicitly **unverified** and never results in actual signoff. Check the exact four module/issue pairs, original question IDs per owner and their overlapping co-owners, uniqueness, proposed/defer/unsupported per-question status and explanation, claimed contract-owner namespace and required scoped exclusions. Reject unexpected `approved`/`runtimeAdmitted` or `EXECUTED_PASS` fields, malformed/foreign question IDs, path traversal and spoofed GitHub URLs. Always output `actualApprovedContract=false`, `permissionToPlacePublishUseOsOrExecute=false` and H01–H04 HIGH OPEN. Three syntax-only statuses: `MISSING_FIELDS_NOT_REVIEWABLE`, `PARTIAL_DRAFT_FORMAT_ONLY`, `COMPLETE_DRAFT_FORMAT_ONLY`; malformed/unscoped drafts exit code 2.

Add **30 new deterministic in-memory synthetic/adversarial unit tests** exercising all four exact owner queues, duplicate/foreign question, malicious claim, expired-looking/prior-looking source shapes, spoofed URL, path traversal, overlap warnings, missing exclusions, no false reviewer status and original source verifier reuse. Supply machine E02 evidence with zero received authentic replies, human example guide, bounded audit target, checkpoint/backlog. No secret, network calls, GitHub action in CI, hardware/OS/process control or external source verification; actual future owner reply claims must be **independently verified in a separate admitted Work Order**.

## Strict base source lock and changed file allowlist

Exactly **24/24** original Git blob SHA-1 sources incl eight project authority roots, unchanged historic C01/C02/current owner B D01, original M12 110 questions and 80 future negatives, original WO0037 4-owner packets/verifier, WO0038 E01 issue routes/report/verifier, old WO0038 factual evidence and existing backlog. Actual diff must equal exactly **10/10** paths:
- `.engineering/context-locks/IRIS-WO-0039-M09-H03-REPLY-TRIAGE.json`
- `.engineering/evidence/IRIS-WO-0039.json`
- `.engineering/evidence/M09-H03-UNTRUSTED-OWNER-REPLY-TRIAGE-E02.json`
- `.engineering/work-orders/IRIS-WO-0039-M09-H03-REPLY-TRIAGE.md`
- `docs/project-brain/14-BACKLOG.md`
- `planning/checkpoints/IRIS-WO-0039-M09-H03-REPLY-TRIAGE.md`
- `planning/reviews/IRIS-WO-0039-M09-H03-TRIAGE-AUDIT-TARGET.md`
- `planning/reviews/M09-H03-UNTRUSTED-OWNER-REPLY-TRIAGE-E02.md`
- `scripts/triage_m09_h03_untrusted_owner_reply.py`
- `tests/test_m09_h03_untrusted_owner_reply_triage.py`

Do not modify prior M09 frozen v1.0, original future HX/LV/C08/PO-C02/M12 evidence or approved owner authority records. Reconcile WO0038 #525/#526 actual outcomes only as part of this new executable **offline planning harness**. Leave canonical project authority checkpoint and Decisions Ledger unchanged.

## DoD, audit and protected merge

Exact-head full suite target **4290/4290** (4260 baseline+30 genuinely new local synthetic triage tests), Context Lock 24/24, changed paths 10/10, IRIS governance and pinned GEF/HIVE PASS. Separate bounded same-assistant exact-head test/code safety review with no fabricated independent security/actual owner signoff and no new HIGH/CRITICAL in scoped offline diff. Protected squash at exact reviewed green HEAD and independently confirm exact-main full CI. Update original issues #82/#110/#112/#128 and owner #145/#146/#147 with factual test-only receipt; preserve OPEN state.

## Immutable STOP

Original H01 actual M11 issuer/ACK, H02 M09 owner-coherent all-member snapshot+lease/at-use revocation, H03 real M12/M54/M58/M60 independent contracts and H04 exact M02/M06/M09/M11 work/attempt/action/epoch remain **OPEN HIGH_FOR_FUTURE_FREEZE**. Original 110 M12 owner questions OPEN/UNRATED, original 80 M12 future negatives NOT_EXECUTED, new 12 H03-N future designs NOT_EXECUTED, original 12 HX/six LV/ten C08/eight PO-C02 future cases NOT_EXECUTED, M11 v0.2 NOT_FROZEN 86 owner questions OPEN. M09 FROZEN unchanged, C01 UNADOPTED_NOT_FROZEN, M12 v0.1 PROPOSED_NOT_FROZEN, M54/M58/M60 INDEX_ONLY_NO_APPROVED_CONTRACTS. M10/M11/M12 runtime NOT_ADMITTED, OS/GPU/network/cloud/process actions DISABLED, no M58 public/negative-only API or M54/M60 real permission from formatting.
