# H04: frozen M09 work/attempt/action/epoch source seam, deterministic synthetic probes

**Scope:** IRIS-WO-0036, 18 deterministic tests of **existing** M09 v1.0 in-process `LeaseBook` semantics plus separate documentary integrity tests. B_FUTURE_OWNER_RECEIPT remains the ratified future **M09→M11 documentary direction only**, source [issue #110](https://github.com/KayzenRoot/iris/issues/110#issuecomment-5857665032). No M09→M11 port, M11 implementation or external owner proof is admitted.

## 1. Existing verified source facts and ownership boundary

Exact base `caa0bb74ffc91b307d7fbd7f74c4c04bc3f5893b` tree `4ee8fa15c64d5f3264853fa8da66cf9750ae8858`. `iris_resource_twin/leases.py` source blob `5757d15156d62ac8cc49a1763eba62b944af52d9`. `LeaseRequest` binds M09 lease ID, request-scoped idempotency, `owner_ref`, actor authorization/context, typed resource claims, arbitrary `purpose_ref`, times and clock uncertainty. `Lease` stores the original request digest and in-book epoch/state. Neither structural string is an externally verified M02 accepted-work/plan revision or M06 operational attempt, and `Lease` does not bind exact M11 request/revision/action/target in an owner-verifiable M09 B receipt.

Within the existing book, idempotency correctly checks the full original request digest; renewal, revocation and release enforce appropriate M09 lease epochs. These are **local M09 integrity guards**, not a cross-module action-time revocation barrier or a claim that an OS process has stopped, M06 marked an attempt successful, or M02 admitted a new revision. A previously captured immutable `ACTIVE` lease is a historical value and may remain unchanged after a real in-book renewal/revocation. External action-time authorization would require separately owner-approved freshness, composite joint-cut and fencing.

Frozen M02 and M06 source documents explicitly distinguish M02 semantic identity and accepted revision, M06 operational revision, independent issued attempt, content hash, output acceptance and storage location. The M11 v0.2 candidate §9.1 requires actual M02 owner-issued accepted-work evidence and optional **only actual** M06-issued attempt association; M09 grant, M12 placement, M54 permission and M60 platform action each require independently verifiable relevant scope. These *candidate* semantics do not install another owner's port.

## 2. New tests: 18 separately named H04-P01..18 source semantic fixtures

| New test | Exact local control / seam observation |
| --- | --- |
| H04-P01 `test_01_local_grant_records_typed_owner_claims_digest_and_epoch` | Existing LeaseBook records request/owner/claim/digest and lease epoch but does not attest M02 accepted plan or M06 issued attempt. |
| H04-P02 `test_02_same_full_request_idempotently_returns_same_grant` | Same complete M09 request idempotently returns same grant locally; not cross-owner replay authorization. |
| H04-P03 `test_03_same_idempotency_different_unverified_owner_ref_conflicts` | M09 correctly rejects request identity reuse with a different supplied owner_ref. |
| H04-P04 `test_04_same_idempotency_changed_m06_purpose_text_conflicts` | M09 correctly rejects request identity reuse when caller-supplied purpose text changes. |
| H04-P05 `test_05_distinct_leases_same_owner_accept_separate_unverified_purposes` | Distinct M09 lease IDs can refer to the same textual owner but different purpose labels without M02/M06 verification. |
| H04-P06 `test_06_arbitrary_m02_looking_owner_ref_is_a_structural_label_only` | M02-looking label is syntactically accepted, not an M02 issuer-signed accepted-plan revision. |
| H04-P07 `test_07_arbitrary_m06_looking_purpose_ref_is_a_structural_label_only` | M06-looking claim purpose text is accepted but cannot certify issued operational attempt. |
| H04-P08 `test_08_lease_has_no_combined_m02_m06_m11_work_action_attestation` | Lease public dataclass has no exact combined M02 work/revision, M06 attempt, M11 action/target or B receipt attestation fields. |
| H04-P09 `test_09_mutation_context_binds_actor_auth_idempotency_not_owner_work` | Existing mutation context binds actor/authorization/idempotency but not external accepted M02 plan/M06 attempt. |
| H04-P10 `test_10_renewal_updates_lease_epoch_without_adding_m02_or_m06_evidence` | M09 renew changes lease epoch while retaining original request digest, without minting external owner-issued work/attempt proof. |
| H04-P11 `test_11_stale_original_epoch_is_rejected_for_second_renewal` | M09 rejects stale epoch renew within its book. |
| H04-P12 `test_12_renewal_does_not_mutate_captured_old_lease_copy` | An immutable old active lease copy remains unchanged after a real book-local renewal; a future M11 action must revalidate. |
| H04-P13 `test_13_revocation_updates_lease_epoch_without_cross_owner_fence` | M09 increments epoch for revocation but neither issues nor proves an M11 action-time fence. |
| H04-P14 `test_14_captured_prior_active_lease_remains_after_revocation` | Old detached active lease copies remain apparently ACTIVE after actual book state is REVOCATION_REQUESTED. |
| H04-P15 `test_15_stale_pre_renewal_epoch_cannot_release_current_lease` | M09 book correctly rejects stale epoch release following renewal. |
| H04-P16 `test_16_exact_current_epoch_release_tombstones_the_lease` | M09 book accepts valid exact-epoch release and removes it from active listing. |
| H04-P17 `test_17_replay_identical_release_causal_ref_is_book_local_idempotent` | Matching causal text allows idempotent M09-local release receipt, not verified M11 OS side effect. |
| H04-P18 `test_18_different_causal_release_after_tombstone_is_rejected` | Conflicting causal release id is rejected by existing book-local tombstone protection. |

Each test uses only deterministic local synthetic fixture strings and reported-looking **test-created** M09 resource values. Any successful local lease is merely an in-memory unit-test state and must **not** be presented as a valid production M09→M11 positive resource grant. All original 12 HX, 6 LV, ten C08, eight PO-C02 and 80 M12 future negative tests remain `SPECIFIED_NOT_EXECUTED`.

## 3. Unselected future proof requirements for actual owners

| Gate | Owner-required separate positive proof | Current status |
| --- | --- | --- |
| H01 | Actual M11 issuer+M54/M60-qualified process identity and provenance, exact owner/request/lease/action ACK/time/replay and independent M09 resource reconciliation. | OPEN_OWNER_EVIDENCE_REQUIRED |
| H02 | M09 owner-coherent all mandatory member snapshot+lease cut, revocation/expiry/epoch and enforceable at-use revalidation. No composition of two independent locks. | OPEN_M09_OWNER_ATOMICITY_DECISION |
| H03 | M12 placement, M54 principal/action permission, M58 publication where needed and M60 OS/adapter rights as independently signed/qualified owner decisions. | OPEN_FUTURE_OWNER_CONTRACTS |
| H04 | Owner-approved exact M02 accepted semantic work/revision, actual M06 operational attempt (if issued), M09 all-member grant/lease epoch and M11 action/target/request/revision with issuer, freshness and race-proof conditional at-use fencing. | OPEN_CROSS_OWNER_DISPOSITION |

Do not select a reference serialization, unified token, issuer trust mechanism, IPC, TTL, cryptographic algorithm, scheduling topology or remote host before real owner approval; this report defines only a precise proof gap and synthetic regression guards. A valid M09 lease is not an M02 or M06 owner decision and not M11 dispatch permission.

## 4. Immutable STOP

Four H01–H04 remain **OPEN HIGH_FOR_FUTURE_FREEZE**. M09 `m09-contract-v1.0` FROZEN unchanged and proposed C01 `UNADOPTED_NOT_FROZEN`. M11 v0.2 NOT_FROZEN with original 86 owner questions OPEN; M12 v0.1 NOT_FROZEN with original 110 owner questions OPEN and 80 future negative cases NOT_EXECUTED. M10/M11/M12 implementation NOT_ADMITTED; no OS/GPU/network/cloud/process actions, real M11 process observation or cross-module positive grant. Keep #82/#110/#112/#128 OPEN. The H04-P tests are source-semantic unit tests only, never execution of original future oracles or proof of authentic cross-owner handoff.
