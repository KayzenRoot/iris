# M09 H02: deterministic source-semantic seam probes of existing in-memory interfaces

**Scope:** IRIS-WO-0034, proposed-only source evidence using synthetic fixture values in existing M09 v1.0 APIs. **Do not interpret as owner approval of a future M09→M11 receipt.** Issue [#110](https://github.com/KayzenRoot/iris/issues/110), B_FUTURE_OWNER_RECEIPT selected as planning direction only. Original C01 remains UNADOPTED_NOT_FROZEN. Original H01–H04 remain OPEN HIGH_FOR_FUTURE_FREEZE.

## 1. What exact frozen M09 source exposes

- `ResourceTwin` has a private in-process `RLock`; `admission_snapshot()` reads latest and checks `is_fresh`, source invalidation, resource quarantine. It does **not** test `EvidenceOrigin.REPORTED_OBSERVATION`, certify a valid M09 lease or produce a joint immutable owner-issued receipt. Its immutable historical snapshots remain readable after later source invalidation.
- `LeaseBook` has a *different* private in-process `RLock`; `grant()` validates a **caller-supplied** `ResourceSnapshot` for identity, reported production origin, freshness and capacity while serializing grants *inside the book*. It does not query `ResourceTwin`'s current `_invalidated`, `_quarantines` or `_epochs`. This is expected existing standalone semantics, **not** a claim of a newly discovered M09 v1.0 contract breach.
- `LeaseBook.active()` includes ACTIVE, PREEMPTION_REQUESTED and REVOCATION_REQUESTED leases without a clock argument. Returned immutable `Lease` snapshots preserve their old epoch/state even after a later book mutation. Active collection membership or an old copy is never a B receipt or current resource permission.
- Composite leases have atomic *book-local* grants from supplied individual snapshots; the book's lock does not make those supplied snapshots a cross-fabric jointly valid cut or attest action-time revocation state of **every mandatory member**.

Exact base Git `ed743fda62764fedb5d31b55c04b9c939979f6f8`, tree `1acba17d5d2301e067c4abb219142a106fe414a5`. Source blobs `twin.py=f8d217d46ca4284d439aba418d6113eb0c4059e2`, `leases.py=5757d15156d62ac8cc49a1763eba62b944af52d9`, `tests/m09_support.py=63a0e77f623afdc350a602d9ffd2fc93b4f52fd8`. Exact historic C02 H02 stays `OPEN_M09_OWNER_ATOMICITY_DECISION`.

## 2. Fourteen deterministic source-semantic fixtures (not original HX/LV)

| ID | Synthetic interleaving / control | Source-level observation and limited meaning |
| --- | --- | --- |
| H02-P01 | `test_01_control_individual_snapshot_and_lease_are_valid_at_capture` | Individual valid states do not imply jointly verified external receipt. |
| H02-P02 | `test_02_detached_earlier_snapshot_remains_fresh_after_twin_invalidates` | The detached snapshot retains its own expiry while ResourceTwin invalidation makes it ineligible at the source. |
| H02-P03 | `test_03_detached_snapshot_can_be_passed_to_separate_lease_grant` | Independent in-memory LeaseBook grant can consume previously captured, source-invalidated snapshot; not a cross-module owner grant. |
| H02-P04 | `test_04_invalidation_after_grant_does_not_transition_independent_lease` | The two in-memory authorities need a future owner-defined joint consistency protocol. |
| H02-P05 | `test_05_revocation_requested_is_still_in_active_collection` | Active-list membership alone is not positive M11 run authorization. |
| H02-P06 | `test_06_detached_active_lease_copy_survives_subsequent_revocation` | Lease owner state/epoch at later use must be revalidated. |
| H02-P07 | `test_07_active_without_a_clock_cannot_prove_unexpired_at_use` | A detached active value cannot independently attest action-time expiry status. |
| H02-P08 | `test_08_twin_event_epoch_and_lease_epoch_are_not_jointly_bound` | Twin state epoch can change while the independently managed lease epoch remains unchanged. |
| H02-P09 | `test_09_observed_synthetic_is_not_sufficient_for_production_grant` | The existing book correctly rejects a fresh-looking synthetic OBSERVED snapshot. |
| H02-P10 | `test_10_complete_composite_grant_is_atomic_inside_leasebook` | Existing book enforces a complete all-member grant from supplied data; this is not a cross-fabric proof. |
| H02-P11 | `test_11_detached_composite_member_can_be_invalidated_before_grant` | Independent book can grant from detached member snapshots despite subsequent source invalidation; missing joint source cut. |
| H02-P12 | `test_12_missing_mandatory_composite_member_still_fails_closed` | Existing book correctly refuses incomplete mandatory member inputs. |
| H02-P13 | `test_13_revoking_lease_cannot_be_renewed_as_active` | Existing book correctly refuses renewal of a revocation-requested lease. |
| H02-P14 | `test_14_wrong_original_lease_epoch_cannot_authorize_revocation` | Existing book correctly refuses stale repeated revocation attempts. |

These cases use in-memory `make_snapshot` fixture values, no real GPU, OS process, IPC, networking, cloud, cross-host verification, permissions or real concurrent timing race. Tests explicitly **observe the limitations of a naive consumer** using distinct currently valid M09 APIs; they do not invent or implement a positive M09→M11 port. A passing test demonstrates one deterministic API interleaving/control at the exact code revision only.

## 3. H02 owner options for further review, none selected/admitted

**Option J1, owner-coordinated logical critical section:** M09 would need to define a joint owner-held snapshot+lease read/decision and controlled lock ordering, update/invalidation interaction and all mandatory composite members. A local lock alone would not ensure applicability in another process/host at action time.

**Option J2, versioned transactional decision with at-use fencing:** M09 could propose a joint decision revision tying snapshot/lease state, exact claim members/epochs and revocation/expiry; it must specify trusted replay prevention, eligibility windows and an M09-owned at-use validation barrier. Current independent event epochs or a detached serialized copy do not provide this guarantee.

**Option J3, owner-held conditional capability/commit:** any future M09-owned conditional proof handshake or fenced commit would require clear control-plane placement and verified issuer+consumer and OS action capabilities. Future actual M12/M54/M60 owner contracts and H04 M02/M06 work/attempt/action binding are prerequisites; no transport, cryptographic mechanism, TTL or runtime is chosen here.

None of J1–J3 is an owner decision or an approved M09 contract amendment. H02 remains **OPEN HIGH_FOR_FUTURE_FREEZE**, independently of how many semantic fixture controls succeed.

## 4. STOP

Retain existing M09 v1.0 FROZEN implementation and immutable C01/C02 history. The B choice remains documentary direction only, no issuer protocol, no positive grant, no new M09 operational interface and no installation. Original **HX-01..12, LV-01..06, C08 ten, PO-C02 eight and M12 80** future negative cases remain **SPECIFIED_NOT_EXECUTED** regardless of these fourteen *newly named* synthetic semantic tests. H01 reverse M11 liveness/ACK, H02 source-coherent all-member cut, H03 M12/M54/M58/M60 owner contracts and H04 M02/M06/M09/M11 exact work/attempt/action/revocation-to-use binding remain OPEN HIGH_FOR_FUTURE_FREEZE. M11 v0.2 NOT_FROZEN 86 original questions OPEN, M12 v0.1 NOT_FROZEN 110 original questions OPEN; M10/M11/M12 runtime NOT_ADMITTED, OS/GPU/network/cloud/process actions DISABLED; leave issues #82/#110/#112/#128 OPEN.
