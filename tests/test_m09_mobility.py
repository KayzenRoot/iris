from __future__ import annotations

import unittest
from dataclasses import replace

from iris_resource_twin import (
    DirtyState,
    DurabilityClass,
    EvidenceOrigin,
    LocalityHint,
    BandwidthContentionEvidence,
    ContentionState,
    MobilityLedger,
    MutationActorKind,
    MutationContext,
    PrefetchBudget,
    PrefetchIntent,
    ResourceTier,
    ReferenceActivity,
    SpillGarbageCandidate,
    TransferCostEvidence,
    TransferCostState,
    SpillTargetCapability,
    TransferSegment,
    TransferState,
    evaluate_spill_garbage,
    verify_source_release_authorization,
)
from m09_support import GIB, make_destination_snapshot, make_snapshot, make_spill_target, make_transfer_request


class TestM09Mobility(unittest.TestCase):
    def test_automated_transfer_records_explicit_origin_and_replay_identity(self) -> None:
        request = make_transfer_request(transfer_id="automated-transfer")
        context = MutationContext(
            MutationActorKind.AUTOMATION, "agent:resource-governor",
            request.authorization_ref, "request:offload-1", request.idempotency_key,
            "workflow:resource-governor",
        )
        automated = replace(request, mutation_context=context)
        ledger = MobilityLedger()
        prepared = ledger.prepare(
            automated, now_ms=1_100,
            destination_snapshot=make_destination_snapshot(automated.target),
        ).transfer
        self.assertEqual(prepared.request.mutation_context, context)
        copying = ledger.begin_copy(automated.transfer_id, expected_epoch=prepared.epoch, now_ms=1_200)
        self.assertEqual(copying.request.mutation_context, context)
        self.assertEqual(tuple(item.request.mutation_context for item in ledger.history(automated.transfer_id)), (context, context))

    def test_verified_two_phase_handoff_requires_fresh_destination_before_source_release(self) -> None:
        target = make_spill_target()
        request = make_transfer_request(target=target)
        ledger = MobilityLedger()
        prepared = ledger.prepare(request, now_ms=1_100, destination_snapshot=make_destination_snapshot(target))
        self.assertEqual(prepared.status, "PREPARED")
        copying = ledger.begin_copy(request.transfer_id, expected_epoch=prepared.transfer.epoch, now_ms=1_200)
        verified = ledger.verify_destination(
            request.transfer_id, expected_epoch=copying.epoch,
            observed_digest=request.expected_digest, copy_complete=True, now_ms=1_300,
        )
        self.assertEqual(verified.state, TransferState.VERIFIED)
        destination = make_snapshot(
            physical_id="spill-0", tier=ResourceTier.SPILL, context_id="storage-runtime",
            snapshot_id="destination-resident", observed_at_ms=1_300,
        )
        committed, release = ledger.commit_handoff(
            request.transfer_id, expected_epoch=verified.epoch,
            destination_snapshot=destination, now_ms=1_400,
            authorization_ref="M09:handoff-authorization",
        )
        self.assertEqual(committed.state, TransferState.COMMITTED)
        self.assertEqual(release.source_resource_key, request.source_resource_key)
        self.assertEqual(release.verified_digest, request.expected_digest)
        self.assertTrue(verify_source_release_authorization(release, committed, destination, now_ms=1_400))
        with self.assertRaisesRegex(ValueError, "source release requires"):
            verify_source_release_authorization(
                replace(release, destination_snapshot_digest="0" * 64),
                committed, destination, now_ms=1_400,
            )
        self.assertEqual(ledger.transaction(request.transfer_id).state, TransferState.COMMITTED)
        self.assertEqual(
            tuple(item.state for item in ledger.history(request.transfer_id)),
            (TransferState.PREPARED, TransferState.COPYING, TransferState.VERIFIED, TransferState.COMMITTED),
        )
        candidate = SpillGarbageCandidate(
            "released-garbage", request.artifact_ref, request.artifact_revision,
            request.target.resource_key, request.transfer_id, request.source_lease_ref,
            request.source_residency_ref, ReferenceActivity.RELEASED, ReferenceActivity.RELEASED,
            ("source-lease-tombstone", "source-residency-release"),
        )
        eligible = evaluate_spill_garbage(candidate, committed_transfer=committed)
        self.assertTrue(eligible.eligible_for_m55_review)
        self.assertFalse(eligible.physical_deletion_permitted)

    def test_integrity_failure_quarantines_destination_and_preserves_source(self) -> None:
        target = make_spill_target()
        request = make_transfer_request(target=target)
        ledger = MobilityLedger()
        prepared = ledger.prepare(request, now_ms=1_100, destination_snapshot=make_destination_snapshot(target)).transfer
        copying = ledger.begin_copy(request.transfer_id, expected_epoch=prepared.epoch, now_ms=1_200)
        failed = ledger.verify_destination(
            request.transfer_id, expected_epoch=copying.epoch,
            observed_digest="b" * 64, copy_complete=True, now_ms=1_300,
        )
        self.assertEqual(failed.state, TransferState.QUARANTINED)
        retry = make_transfer_request(transfer_id="transfer-retry", target=target)
        self.assertEqual(ledger.prepare(retry, now_ms=1_400, destination_snapshot=make_destination_snapshot(target)).status, "REQUIRE_REPLAN")

    def test_dirty_material_requires_writeback_and_segments_are_exact(self) -> None:
        segments = (
            TransferSegment("segment-1", 0, 4, "a" * 64),
            TransferSegment("segment-2", 4, 4, "b" * 64),
        )
        with self.assertRaisesRegex(ValueError, "writeback"):
            make_transfer_request(transfer_id="dirty-no-proof", dirty_state=DirtyState.DIRTY)
        request = make_transfer_request(
            transfer_id="dirty-with-proof", dirty_state=DirtyState.DIRTY,
            writeback_ref="M09:writeback-receipt", segments=segments,
        )
        self.assertEqual(sum(item.length_bytes for item in request.segments), request.byte_count)
        with self.assertRaisesRegex(ValueError, "gap-free"):
            bad = (
                TransferSegment("segment-a", 0, 3, "a" * 64),
                TransferSegment("segment-b", 4, 4, "b" * 64),
            )
            make_transfer_request(transfer_id="transfer-gap", segments=bad)
        with self.assertRaisesRegex(ValueError, "reconstruction proof"):
            make_transfer_request(transfer_id="reconstructible-no-proof", dirty_state=DirtyState.RECONSTRUCTIBLE)
        reconstructed = make_transfer_request(transfer_id="reconstructible-with-proof", dirty_state=DirtyState.RECONSTRUCTIBLE, reconstruction_ref="M06:reconstruction-proof")
        self.assertEqual(reconstructed.dirty_state, DirtyState.RECONSTRUCTIBLE)

    def test_cancel_and_resume_retain_epoch_and_content_identity(self) -> None:
        request = make_transfer_request()
        ledger = MobilityLedger()
        prepared = ledger.prepare(request, now_ms=1_100, destination_snapshot=make_destination_snapshot(request.target)).transfer
        copying = ledger.begin_copy(request.transfer_id, expected_epoch=prepared.epoch, now_ms=1_200)
        aborted = ledger.cancel(
            request.transfer_id, expected_epoch=copying.epoch, now_ms=1_300,
            reason_ref="cancel-policy", checkpoint_ref="checkpoint-1",
        )
        self.assertEqual(ledger.cancel(
            request.transfer_id, expected_epoch=copying.epoch, now_ms=1_300,
            reason_ref="cancel-policy", checkpoint_ref="checkpoint-1",
        ), aborted)
        with self.assertRaisesRegex(ValueError, "conflicting cancellation"):
            ledger.cancel(request.transfer_id, expected_epoch=copying.epoch, now_ms=1_300, reason_ref="different-reason", checkpoint_ref="checkpoint-1")
        resumed = ledger.resume(
            request.transfer_id, expected_epoch=aborted.epoch,
            checkpoint_ref="checkpoint-1", source_digest=request.expected_digest, now_ms=1_400,
        )
        self.assertEqual(ledger.resume(
            request.transfer_id, expected_epoch=aborted.epoch,
            checkpoint_ref="checkpoint-1", source_digest=request.expected_digest, now_ms=1_400,
        ), resumed)
        self.assertEqual(resumed.state, TransferState.PREPARED)
        self.assertGreater(resumed.epoch, aborted.epoch)
        second = make_transfer_request(transfer_id="transfer-bad-resume")
        second_prepared = ledger.prepare(second, now_ms=1_500, destination_snapshot=make_destination_snapshot(second.target)).transfer
        second_copying = ledger.begin_copy(second.transfer_id, expected_epoch=second_prepared.epoch, now_ms=1_600)
        second_aborted = ledger.cancel(
            second.transfer_id, expected_epoch=second_copying.epoch, now_ms=1_700,
            reason_ref="cancel-policy-2", checkpoint_ref="checkpoint-2",
        )
        with self.assertRaisesRegex(ValueError, "source/checkpoint integrity"):
            ledger.resume(
                second.transfer_id, expected_epoch=second_aborted.epoch,
                checkpoint_ref="checkpoint-2", source_digest="c" * 64, now_ms=1_800,
            )

    def test_m55_spill_capability_fails_closed_without_capacity_or_permission(self) -> None:
        unknown = make_spill_target(physical_id="unknown-target", available_bytes=None)
        request = make_transfer_request(transfer_id="unknown-target-transfer", target=unknown)
        self.assertEqual(MobilityLedger().prepare(request, now_ms=1_200, destination_snapshot=make_destination_snapshot(unknown)).status, "UNAVAILABLE")
        with self.assertRaisesRegex(ValueError, "deletion authority"):
            identity = make_spill_target().identity
            SpillTargetCapability(
                "m55-bad", "M55:bad", identity.stable_key, ResourceTier.SPILL, GIB,
                True, True, "M53:permission", identity, encryption_ref="M54:encryption",
                deletion_authorized=True, durability_class=make_spill_target().durability_class,
            )

    def test_prefetch_is_expiring_bounded_intent_not_a_transfer(self) -> None:
        budget = PrefetchBudget(max_bytes=10, max_concurrent=1)
        first = PrefetchIntent("prefetch-1", "resource-1", 8, 2_000, "locality-evidence")
        second = PrefetchIntent("prefetch-2", "resource-2", 3, 2_000, "locality-evidence-2")
        self.assertTrue(budget.propose(first, now_ms=1_000, known_allocatable_bytes=20))
        self.assertFalse(budget.propose(second, now_ms=1_000, known_allocatable_bytes=20))
        self.assertEqual(len(budget.intents()), 1)
        self.assertEqual(budget.expire(now_ms=2_001), ("prefetch-1",))
        self.assertEqual(budget.intents(), ())

    def test_measured_estimated_unknown_transfer_costs_never_collapse_unknown_to_zero(self) -> None:
        unknown = make_transfer_request().cost
        self.assertEqual(unknown.state, TransferCostState.UNKNOWN)
        self.assertIsNone(unknown.bytes_per_second)
        measured = TransferCostEvidence(TransferCostState.MEASURED, ResourceTier.VRAM, ResourceTier.SPILL, 1_000_000, "transfer-cost-measured", "M08:bench-transfer")
        estimate = TransferCostEvidence(TransferCostState.ESTIMATED, ResourceTier.VRAM, ResourceTier.SPILL, 500_000, "transfer-cost-estimate")
        self.assertEqual(measured.state, TransferCostState.MEASURED)
        self.assertEqual(estimate.state, TransferCostState.ESTIMATED)
        with self.assertRaisesRegex(ValueError, "cannot carry a numeric"):
            TransferCostEvidence(TransferCostState.UNKNOWN, ResourceTier.VRAM, ResourceTier.SPILL, 0, "bad-unknown-cost")
        with self.assertRaisesRegex(ValueError, "M08 evidence"):
            TransferCostEvidence(TransferCostState.MEASURED, ResourceTier.VRAM, ResourceTier.SPILL, 1, "bad-measured-cost", "M09:invented-benchmark")

    def test_destination_admission_requires_exact_fresh_snapshot_and_protected_headroom(self) -> None:
        target = make_spill_target()
        request = make_transfer_request(target=target)
        stale = make_destination_snapshot(target, snapshot_id="stale-destination", observed_at_ms=1_000)
        self.assertEqual(MobilityLedger().prepare(request, now_ms=60_001, destination_snapshot=stale).status, "EXPIRED")
        wrong_target = make_destination_snapshot(make_spill_target(physical_id="other-spill"))
        self.assertEqual(MobilityLedger().prepare(request, now_ms=1_200, destination_snapshot=wrong_target).status, "UNAVAILABLE")
        unknown_capacity = make_snapshot(
            identity=target.identity, tier=ResourceTier.SPILL,
            capacity=None, snapshot_id="unknown-destination",
        )
        # A known target declaration cannot replace UNKNOWN resource-state truth.
        unknown_capacity = type(unknown_capacity)(
            unknown_capacity.snapshot_id, unknown_capacity.schema_version, unknown_capacity.identity,
            unknown_capacity.observed_at_ms, unknown_capacity.expires_at_ms, unknown_capacity.confidence,
            type(unknown_capacity.capacity)(None, None, None, None, None, None, None, None, None, None),
            unknown_capacity.provenance, unknown_capacity.m07_discovery_ref, unknown_capacity.m08_evidence_ref,
        )
        self.assertEqual(MobilityLedger().prepare(request, now_ms=1_200, destination_snapshot=unknown_capacity).status, "UNAVAILABLE")

    def test_partial_transfer_is_a_distinct_non_authorizing_state_and_can_resume(self) -> None:
        request = make_transfer_request(transfer_id="partial-1", byte_count=8)
        ledger = MobilityLedger()
        prepared = ledger.prepare(request, now_ms=1_100, destination_snapshot=make_destination_snapshot(request.target)).transfer
        copying = ledger.begin_copy(request.transfer_id, expected_epoch=prepared.epoch, now_ms=1_200)
        partial = ledger.verify_destination(request.transfer_id, expected_epoch=copying.epoch, observed_digest="a" * 64, copy_complete=False, now_ms=1_300, completed_bytes=4, checkpoint_ref="partial-checkpoint")
        self.assertEqual(partial.state, TransferState.PARTIAL)
        with self.assertRaisesRegex(ValueError, "state or epoch is stale"):
            ledger.commit_handoff(request.transfer_id, expected_epoch=partial.epoch, destination_snapshot=make_destination_snapshot(request.target, observed_at_ms=1_400), now_ms=1_500, authorization_ref="M09:release-not-yet")
        resumed = ledger.resume(request.transfer_id, expected_epoch=partial.epoch, checkpoint_ref="partial-checkpoint", source_digest=request.expected_digest, now_ms=1_400)
        copying_again = ledger.begin_copy(request.transfer_id, expected_epoch=resumed.epoch, now_ms=1_500)
        verified = ledger.verify_destination(request.transfer_id, expected_epoch=copying_again.epoch, observed_digest=request.expected_digest, copy_complete=True, completed_bytes=8, now_ms=1_600)
        self.assertEqual(verified.state, TransferState.VERIFIED)
        committed, _receipt = ledger.commit_handoff(request.transfer_id, expected_epoch=verified.epoch, destination_snapshot=make_destination_snapshot(request.target, snapshot_id="partial-destination", observed_at_ms=1_700), now_ms=1_800, authorization_ref="M09:release-after-full-verification")
        self.assertEqual(committed.state, TransferState.COMMITTED)

    def test_partial_transfer_requires_checkpoint_and_digest_evidence(self) -> None:
        request = make_transfer_request(transfer_id="partial-evidence", byte_count=8)
        ledger = MobilityLedger()
        prepared = ledger.prepare(request, now_ms=1_100, destination_snapshot=make_destination_snapshot(request.target)).transfer
        copying = ledger.begin_copy(request.transfer_id, expected_epoch=prepared.epoch, now_ms=1_200)
        with self.assertRaisesRegex(ValueError, "checkpoint reference"):
            ledger.verify_destination(
                request.transfer_id, expected_epoch=copying.epoch,
                observed_digest="a" * 64, copy_complete=False, now_ms=1_300,
                completed_bytes=4,
            )
        with self.assertRaisesRegex(ValueError, "partial transfer digest"):
            ledger.verify_destination(
                request.transfer_id, expected_epoch=copying.epoch,
                observed_digest="not-a-digest", copy_complete=False, now_ms=1_300,
                completed_bytes=4, checkpoint_ref="partial-checkpoint",
            )

    def test_segmented_partial_and_complete_digest_evidence_are_exact(self) -> None:
        segments = (TransferSegment("seg-a", 0, 4, "a" * 64), TransferSegment("seg-b", 4, 4, "b" * 64))
        request = make_transfer_request(transfer_id="segmented", segments=segments)
        ledger = MobilityLedger()
        prepared = ledger.prepare(request, now_ms=1_100, destination_snapshot=make_destination_snapshot(request.target)).transfer
        copying = ledger.begin_copy(request.transfer_id, expected_epoch=prepared.epoch, now_ms=1_200)
        partial = ledger.verify_destination(request.transfer_id, expected_epoch=copying.epoch, observed_digest="a" * 64, copy_complete=False, now_ms=1_300, observed_segment_digests=(("seg-a", "a" * 64),), checkpoint_ref="segment-checkpoint")
        self.assertEqual(partial.completed_bytes, 4)
        resumed = ledger.resume(request.transfer_id, expected_epoch=partial.epoch, checkpoint_ref="segment-checkpoint", source_digest=request.expected_digest, now_ms=1_400)
        copying_again = ledger.begin_copy(request.transfer_id, expected_epoch=resumed.epoch, now_ms=1_500)
        mismatch = ledger.verify_destination(request.transfer_id, expected_epoch=copying_again.epoch, observed_digest=request.expected_digest, copy_complete=True, completed_bytes=8, now_ms=1_600, observed_segment_digests=(("seg-a", "b" * 64), ("seg-b", "b" * 64)))
        self.assertEqual(mismatch.state, TransferState.QUARANTINED)

    def test_active_transfer_byte_and_target_concurrency_bounds_are_enforced(self) -> None:
        target = make_spill_target()
        ledger = MobilityLedger(max_active_bytes=6, max_active_per_target=2)
        first = make_transfer_request(transfer_id="bounded-1", target=target, byte_count=4)
        second = make_transfer_request(transfer_id="bounded-2", target=target, byte_count=4)
        self.assertEqual(ledger.prepare(first, now_ms=1_100, destination_snapshot=make_destination_snapshot(target)).status, "PREPARED")
        self.assertEqual(ledger.prepare(second, now_ms=1_100, destination_snapshot=make_destination_snapshot(target)).status, "REQUIRE_REPLAN")

    def test_composite_transfer_reports_per_member_and_atomic_failure_has_no_partial_admission(self) -> None:
        target = make_spill_target()
        group = "composite-group-1"
        first = make_transfer_request(transfer_id="composite-a", target=target, composite_group_ref=group)
        unavailable = make_spill_target(physical_id="unavailable-spill", available_bytes=None)
        second = make_transfer_request(transfer_id="composite-b", target=unavailable, composite_group_ref=group)
        ledger = MobilityLedger()
        outcome = ledger.prepare_composite(((first, make_destination_snapshot(target)), (second, make_destination_snapshot(unavailable))), group_ref=group, atomic_required=True, now_ms=1_100)
        self.assertEqual(tuple(item.status for item in outcome.members), ("ABORTED_ATOMIC_MEMBER_FAILURE", "UNAVAILABLE"))
        self.assertIsNone(ledger.transaction(first.transfer_id))
        partial = ledger.prepare_composite(((first, make_destination_snapshot(target)), (second, make_destination_snapshot(unavailable))), group_ref=group, atomic_required=False, now_ms=1_100)
        self.assertEqual(tuple(item.status for item in partial.members), ("PREPARED", "UNAVAILABLE"))
        self.assertIsNotNone(ledger.transaction(first.transfer_id))

    def test_synthetic_transfer_never_authorizes_source_release(self) -> None:
        target = make_spill_target()
        request = make_transfer_request(transfer_id="synthetic-transfer", target=target, evidence_origin=EvidenceOrigin.SYNTHETIC_FIXTURE)
        ledger = MobilityLedger()
        prepared = ledger.prepare(request, now_ms=1_100, destination_snapshot=make_destination_snapshot(target, evidence_origin=EvidenceOrigin.SYNTHETIC_FIXTURE)).transfer
        copying = ledger.begin_copy(request.transfer_id, expected_epoch=prepared.epoch, now_ms=1_200)
        verified = ledger.verify_destination(request.transfer_id, expected_epoch=copying.epoch, observed_digest=request.expected_digest, copy_complete=True, now_ms=1_300)
        with self.assertRaisesRegex(ValueError, "fresh destination residency truth"):
            ledger.commit_handoff(request.transfer_id, expected_epoch=verified.epoch, destination_snapshot=make_destination_snapshot(target, observed_at_ms=1_400, evidence_origin=EvidenceOrigin.SYNTHETIC_FIXTURE), now_ms=1_500, authorization_ref="M09:no-eviction")

    def test_locality_contention_and_garbage_eligibility_are_evidence_only(self) -> None:
        hint = LocalityHint("locality-1", "resource-1", ResourceTier.RAM, "SAME_HOST", "M08:locality-evidence", 2_000)
        self.assertTrue(hint.is_current(now_ms=1_500))
        contention = BandwidthContentionEvidence("resource-1", ResourceTier.RAM, ContentionState.UNKNOWN, None, "contention-unknown", 2_000)
        self.assertEqual(contention.contention_basis_points, None)
        with self.assertRaisesRegex(ValueError, "unknown contention"):
            BandwidthContentionEvidence("resource-1", ResourceTier.RAM, ContentionState.UNKNOWN, 0, "bad-contention", 2_000)
        self.assertEqual(DurabilityClass.DURABLE.value, "DURABLE")
        candidate = SpillGarbageCandidate("garbage-candidate", "asset:released", "revision:1", make_spill_target().resource_key, "committed-transfer", "M09:lease-released", "M09:residency-released", ReferenceActivity.RELEASED, ReferenceActivity.RELEASED, ("lease-tombstone", "residency-release"))
        unavailable = evaluate_spill_garbage(candidate, committed_transfer=None)
        self.assertFalse(unavailable.eligible_for_m55_review)
        self.assertFalse(unavailable.physical_deletion_permitted)


if __name__ == "__main__":
    unittest.main()
