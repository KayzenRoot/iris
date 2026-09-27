# H01: source-semantic reverse-producer and cooperative-release seams, synthetic fixtures only

**Status:** proposed IRIS-WO-0035 for source-only synthetic probing of *unchanged frozen M09 v1.0 in-process semantics*, not the actual M11 issuer. B_FUTURE_OWNER_RECEIPT is selected solely for future M09→M11 read-only receipt planning by [#110 ratification](https://github.com/KayzenRoot/iris/issues/110#issuecomment-5857665032). B in the *forward* direction never authenticates the distinct *reverse* M11→M09 liveness/ACK producer. Historical C01 remains UNADOPTED_NOT_FROZEN.

## 1. Source truths and boundaries

At base `a50686bfb551d5b106957685aa30a9c0f4e8c86e`/tree `cc1d12622621989321b3d69212c9ec5cd095e78a`, frozen `iris_resource_twin/recovery.py` creates `OwnerLivenessRef` after checking that non-UNKNOWN `authority_ref` starts with the literal `M11:`. The value does **not** verify that M11, M54 or M60 issued any record or that an OS process actually died. The independent `LeaseBook.OwnerLivenessEvidence` has a comparable structural-prefix check. `confirm_leak()` consumes the caller-provided ref, and with a matching owner, recent TERMINATED text, fresh reported resource truth, enough independent observation refs and sufficient excess resident bytes, it can return **`confirmed=True` locally**, even when a synthetic test caller authored the text. That is a demonstrated missing *cross-module trust boundary* for a naive future integration, not an allegation that existing M09 v1.0 had an admitted trusted M11 producer.

`StaleCommitmentReaper.reconcile()` also accepts an in-process owner ref, but correctly yields `RECONCILIATION_RECORDED_PENDING_FRESH_RESOURCE_TRUTH` for locally claimed termination, with `freed_bytes=None` and `capacity_reclaimed=False`; UNKNOWN yields quarantine and ALIVE preserves owner. It does not independently prove issuer identity or release real capacity.

`evaluate_cooperative_release()` matches exact request+owner and rejects future response timestamps. It has no issuer/capability authentication, replay tracking or lower-bound requirement tying `responded_at_ms` to the request creation. Thus a synthetically caller-created ACK timestamped before the request can still produce `ACCEPTED_AWAITING_RESOURCE_RECONCILIATION`, **never reclaimed capacity**. This in-process API is not the not-yet-adopted M11 cross-module verifier. A response of ACCEPTED, late, absent or replayed does not establish OS termination, M06 attempt success or M09 resource reconciliation.

## 2. Twenty deterministic existing-M09 synthetic fixture probes, NOT original LV cases

| ID | Local API test method | Source-observable meaning |
| --- | --- | --- |
| H01-P01 | `test_01_textual_m11_prefix_creates_structurally_accepted_terminated_ref` | The source value accepts caller-supplied TERMINATED text with M11 prefix; issuer remains unverified. |
| H01-P02 | `test_02_non_m11_prefix_for_nonunknown_liveness_is_rejected` | A non-M11 prefix is rejected structurally, not authentication. |
| H01-P03 | `test_03_unknown_allows_unverified_external_reference_without_authority` | UNKNOWN does not prove liveness or confirm leak regardless of unverified ref. |
| H01-P04 | `test_04_caller_claimed_m11_prefix_can_confirm_inprocess_leak_semantics` | A caller-created M11-prefixed TERMINATED ref plus distinct fixture observations and fresh production-looking snapshot can satisfy existing in-process confirm_leak; not a verified actual M11 producer. |
| H01-P05 | `test_05_alive_structural_ref_does_not_confirm_leak` | ALIVE does not confirm leak. |
| H01-P06 | `test_06_wrong_owner_terminated_ref_does_not_confirm_leak` | Owner scope mismatch cannot confirm leak. |
| H01-P07 | `test_07_stale_terminated_ref_does_not_confirm_leak` | Old liveness must not confirm despite independently fresh resource truth. |
| H01-P08 | `test_08_synthetic_reported_looking_resource_does_not_confirm_leak` | Synthetic resource origin cannot confirm leak despite OBSERVED confidence. |
| H01-P09 | `test_09_caller_claimed_termination_reaper_remains_pending_resource_truth` | Caller-claimed termination can produce pending reconciliation record, never freed capacity. |
| H01-P10 | `test_10_unknown_liveness_reaper_quarantines_without_freed_bytes` | UNKNOWN liveness leads quarantine, not capacity reuse. |
| H01-P11 | `test_11_alive_liveness_reaper_preserves_owner_and_does_not_reclaim` | ALIVE liveness preserves owner, never reclaims capacity. |
| H01-P12 | `test_12_unverified_caller_claimed_acceptance_is_only_local_ack_state` | In-process ACCEPTED maps to accepted pending independent resource reconciliation. |
| H01-P13 | `test_13_wrong_request_ack_is_rejected` | Mismatched request rejected by local evaluator. |
| H01-P14 | `test_14_wrong_owner_ack_is_rejected` | Mismatched owner rejected by local evaluator. |
| H01-P15 | `test_15_response_claiming_a_future_timestamp_is_rejected` | A response timestamp beyond evaluation time is rejected. |
| H01-P16 | `test_16_pre_request_time_ack_can_pass_local_shape_check_not_issuer` | A caller-claimed response timestamp before request creation currently passes local shape check; future verifier must separately require causality and trustworthy issuer. |
| H01-P17 | `test_17_late_matching_ack_times_out_without_reclaim` | Matching but late response times out without reclaim. |
| H01-P18 | `test_18_missing_ack_before_and_after_deadline_never_reclaims` | No response remains pending before deadline and timeout afterward. |
| H01-P19 | `test_19_replayed_identical_ack_is_deterministic_but_has_no_replay_store` | Repeated same ACK yields same local result with no replay store; external verifier must independently bind nonce/replay protection. |
| H01-P20 | `test_20_claimed_dead_reaper_rejects_wrong_owner_or_future_evidence` | Stale commitment reaper rejects wrong owner and future evidence. |

All twenty scenarios use deterministic in-memory test values, no real OS process/IPC/credential issuer/GPU/network/cloud, and do not call M11 runtime. Tests of locally accepted fake prefix/early ACK are *negative illustrations of missing trust*, not endorsement of a safe positive handoff or evidence of real attacker capability.

## 3. Future owner-review proof obligations, no design selected

- **H01-M11 actual producer:** M11 owner must choose observable process+request/revision and a versioned issuer/provenance field, provide freshness, original UNKNOWN reasons, PID-reuse and stale-owner rules and bind optional M06 attempt only when actually issued. Existing C09 is source research, not a published port.
- **H01-M54/M60 issuer/OS rights:** Actual M54 principal/credential verification and M60 process observation/rights for exact process instance and host. A literal `M11:...`, an in-memory object or a test fixture is insufficient. Do not invent crypto, TPM, host, TTL or transport.
- **H01-M09 exact consumer:** Owner M09 must define accepted external authenticated liveness and ACK verification, exact M09 request+owner+lease/action+epoch, timestamp lower/upper bounds, replay or contradictory ACK behavior, evidence retention and UNKNOWN fallback; accepted ACK never frees resources until independent source-owned reconciliation.
- **H02–H04 upstream/downstream:** Maintain unproved M09 coherent all-member joint snapshot+lease/at-use revocation H02; M12/M54/M58/M60 independent contracts H03; M02/M06/M09/M11 exact work/attempt/action/epoch H04. C09's proposed envelope is not a published M11 type or a grant.

## 4. STOP

Original C02 **LV-01..06**, original HX-01..12/C08 ten/PO-C02 eight and M12 80 future negatives remain SPECIFIED_NOT_EXECUTED. These twenty **H01-Pxx** newly executed semantic fixture tests, if CI passes, are separately named and are not a qualification of H01 or an execution of the LV integration suite. H01 OPEN_OWNER_EVIDENCE_REQUIRED and H02/H03/H04 also OPEN HIGH_FOR_FUTURE_FREEZE. M09 frozen v1.0 unchanged, C01 UNADOPTED_NOT_FROZEN; M11 v0.2 NOT_FROZEN 86 OPEN, M12 v0.1 NOT_FROZEN 110 OPEN and 80 future cases NOT_EXECUTED; M10/M11/M12 implementation NOT_ADMITTED, OS/GPU/network/cloud/process actions DISABLED. Keep #82/#110/#112/#128 OPEN.
