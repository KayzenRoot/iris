from __future__ import annotations

import dataclasses
import unittest

from iris_resource_twin import (
    CapacityTruth,
    Confidence,
    EventVerificationStatus,
    M09Limits,
    MutationActorKind,
    MutationContext,
    ResourceIdentity,
    ResourceTier,
    ResourceTwin,
    canonical_json,
    content_digest,
    deserialize,
    reconcile_snapshots,
    serialize,
)
from m09_support import GIB, make_snapshot


class TestM09Twin(unittest.TestCase):
    def test_resource_twin_records_automated_event_context(self) -> None:
        twin = ResourceTwin()
        snapshot = make_snapshot(snapshot_id="automated-twin-snapshot")
        context = MutationContext(
            MutationActorKind.AUTOMATION, "agent:telemetry-import", "M57:telemetry-auth",
            "request:snapshot-publish", "idem:snapshot-publish", "workflow:telemetry-import",
        )
        event = twin.publish(
            snapshot, event_id="automated-event", at_ms=1_000,
            authorization_ref=context.authorization_ref, mutation_context=context,
        )
        self.assertEqual(event.mutation_context, context)
        self.assertEqual(twin.publish(
            snapshot, event_id="automated-event", at_ms=1_000,
            authorization_ref=context.authorization_ref, mutation_context=context,
        ), event)
        conflict = MutationContext(
            MutationActorKind.AUTOMATION, "agent:telemetry-import", "M57:telemetry-auth",
            "request:other-publish", "idem:snapshot-publish", "workflow:telemetry-import",
        )
        with self.assertRaisesRegex(ValueError, "different event identity"):
            twin.publish(
                snapshot, event_id="automated-event", at_ms=1_000,
                authorization_ref=conflict.authorization_ref, mutation_context=conflict,
            )

    def test_snapshot_is_immutable_canonical_and_provenanced(self) -> None:
        snapshot = make_snapshot()
        self.assertEqual(snapshot.digest, content_digest(snapshot.semantic_payload()))
        self.assertEqual(snapshot.provenance[0].source, "M07:discovery")
        self.assertEqual(deserialize(serialize(snapshot)), snapshot)
        self.assertEqual(canonical_json(snapshot), canonical_json(deserialize(serialize(snapshot))))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            snapshot.snapshot_id = "changed"

    def test_resource_identity_does_not_depend_on_enumeration_context_or_label(self) -> None:
        first = ResourceIdentity("physical-0", ResourceTier.VRAM, "runtime-before", "GPU A")
        restarted = ResourceIdentity("physical-0", ResourceTier.VRAM, "runtime-after", "Renamed GPU")
        other = ResourceIdentity("physical-1", ResourceTier.VRAM, "runtime-after", "GPU A")
        self.assertEqual(first.stable_key, restarted.stable_key)
        self.assertNotEqual(first.runtime_context_id, restarted.runtime_context_id)
        self.assertNotEqual(first.stable_key, other.stable_key)

    def test_capacity_unknown_stale_conflict_and_unsupported_fail_closed(self) -> None:
        full = make_snapshot()
        self.assertGreaterEqual(full.capacity.available_bytes(), 0)
        self.assertTrue(full.admits_commitment(2_000, 1))
        unknown_capacity = CapacityTruth(None, None, None, None, None, None, None, None, None, None)
        unknown = make_snapshot(snapshot_id="unknown", confidence=Confidence.UNKNOWN, capacity=unknown_capacity)
        stale = make_snapshot(snapshot_id="stale", confidence=Confidence.STALE)
        conflicted = make_snapshot(snapshot_id="conflicted", confidence=Confidence.CONFLICTED)
        unsupported = make_snapshot(snapshot_id="unsupported", confidence=Confidence.UNSUPPORTED)
        for snapshot in (unknown, stale, conflicted, unsupported):
            self.assertFalse(snapshot.admits_commitment(2_000, 1))
        with self.assertRaises(ValueError):
            unknown.capacity.available_bytes()
        self.assertIsNone(unknown.capacity.physical_bytes)

    def test_capacity_arithmetic_preserves_headroom_and_bounds(self) -> None:
        with self.assertRaises(ValueError):
            CapacityTruth(8 * GIB, 8 * GIB, 8 * GIB, 0, 0, 0, 0, 0, 0, GIB)
        with self.assertRaises(ValueError):
            CapacityTruth(-1, 1, 1, 0, 0, 0, 0, 0, 0, 0)
        with self.assertRaises(ValueError):
            CapacityTruth(8 * GIB, 8 * GIB, 1, 0, 0, 2, 0, 0, 0, 0)

    def test_conflicting_observations_quarantine_without_rewriting_sources(self) -> None:
        left = make_snapshot(snapshot_id="left")
        right_capacity = CapacityTruth(
            8 * GIB, 8 * GIB, 6 * GIB, 1 * GIB, 1 * GIB,
            512 * 1024**2, 0, 0, 0, 1 * GIB,
        )
        right = make_snapshot(snapshot_id="right", capacity=right_capacity)
        result = reconcile_snapshots((left, right), snapshot_id="reconciled", now_ms=2_000, freshness_window_ms=10_000)
        self.assertTrue(result.quarantined)
        self.assertIn("allocatable_bytes", result.conflict_fields)
        self.assertEqual(result.snapshot.confidence, Confidence.CONFLICTED)
        self.assertFalse(result.snapshot.admits_commitment(2_000, 1))
        self.assertNotEqual(left.snapshot_id, result.snapshot.snapshot_id)
        self.assertEqual(left.digest, make_snapshot(snapshot_id="left").digest)

    def test_skew_and_expiry_remain_explicit_in_reconciliation(self) -> None:
        left = make_snapshot(snapshot_id="early", observed_at_ms=1_000)
        right = make_snapshot(snapshot_id="late", observed_at_ms=4_000)
        result = reconcile_snapshots((left, right), snapshot_id="skewed", now_ms=4_001, freshness_window_ms=10_000, skew_tolerance_ms=500)
        self.assertEqual(result.source_skew_ms, 3_000)
        self.assertEqual(result.snapshot.confidence, Confidence.STALE)

    def test_reconciliation_preserves_conservative_confidence_and_quarantine(self) -> None:
        for confidence in (Confidence.ESTIMATED, Confidence.STALE, Confidence.CONFLICTED, Confidence.UNKNOWN, Confidence.UNSUPPORTED, Confidence.QUARANTINED):
            result = reconcile_snapshots(
                (make_snapshot(snapshot_id=f"left-{confidence.value}", confidence=confidence),),
                snapshot_id=f"result-{confidence.value}", now_ms=1_500, freshness_window_ms=5_000,
            )
            self.assertEqual(result.snapshot.confidence, confidence)
            self.assertEqual(result.quarantined, confidence in {Confidence.CONFLICTED, Confidence.QUARANTINED})

    def test_reconciliation_bounds_iterable_consumption(self) -> None:
        snapshot = make_snapshot()
        with self.assertRaisesRegex(ValueError, "max_resources"):
            reconcile_snapshots(
                (item for item in (snapshot, snapshot)), snapshot_id="bounded-reconcile",
                now_ms=1_500, freshness_window_ms=5_000, limits=M09Limits(max_resources=1),
            )

    def test_resource_events_carry_version_epoch_verification_and_stable_replay(self) -> None:
        twin = ResourceTwin()
        snapshot = make_snapshot(snapshot_id="event-snapshot")
        event = twin.publish(snapshot, event_id="event-publish", at_ms=1_000, authorization_ref="M09:observation-import")
        self.assertEqual(event.schema_version, snapshot.schema_version)
        self.assertEqual(event.state_epoch, 1)
        self.assertEqual(event.verification_status, EventVerificationStatus.UNVERIFIED)
        self.assertIs(twin.publish(snapshot, event_id="event-publish", at_ms=1_000, authorization_ref="M09:observation-import"), event)
        with self.assertRaisesRegex(ValueError, "different event identity"):
            twin.publish(snapshot, event_id="event-publish-retry", at_ms=1_000, authorization_ref="M09:observation-import")
        invalidation = twin.invalidate(snapshot.snapshot_id, reason="operator-refresh", event_id="event-invalidate", at_ms=1_100, authorization_ref="M09:invalidation-policy")
        self.assertEqual(invalidation.state_epoch, 2)
        self.assertIs(twin.invalidate(snapshot.snapshot_id, reason="operator-refresh", event_id="event-invalidate", at_ms=1_100, authorization_ref="M09:invalidation-policy"), invalidation)
        with self.assertRaisesRegex(ValueError, "different event identity"):
            twin.invalidate(snapshot.snapshot_id, reason="operator-refresh", event_id="event-invalidate-retry", at_ms=1_200, authorization_ref="M09:invalidation-policy")

    def test_resource_twin_appends_causal_events_and_keeps_old_snapshot(self) -> None:
        twin = ResourceTwin()
        first = make_snapshot(snapshot_id="twin-1")
        second = make_snapshot(snapshot_id="twin-2", observed_at_ms=2_000)
        event1 = twin.publish(first, event_id="event-1", at_ms=1_000, authorization_ref="M09:observation-import")
        twin.publish(second, event_id="event-2", at_ms=2_000, authorization_ref="M09:observation-import")
        self.assertEqual(twin.get(first.snapshot_id), first)
        self.assertEqual(twin.history()[-1].predecessor_ids, tuple(sorted((event1.event_id, first.snapshot_id))))
        self.assertEqual(event1.predecessor_ids, ())
        invalidation = twin.invalidate(first.snapshot_id, reason="operator-refresh", event_id="event-invalidate", at_ms=3_000, authorization_ref="M09:invalidation-policy")
        self.assertEqual(invalidation.predecessor_ids, tuple(sorted(("event-2", first.snapshot_id))))
        self.assertEqual(invalidation.actor_authorization_ref, "M09:invalidation-policy")
        self.assertEqual(twin.invalidations(), ((first.snapshot_id, "operator-refresh"),))

    def test_twin_quarantine_is_a_scoped_fail_closed_flag(self) -> None:
        twin = ResourceTwin()
        from iris_resource_twin import QuarantineRecord
        twin.quarantine(QuarantineRecord("q-1", "resource-1", "conflicted-observations", ("evidence-1",), 1_000, "M09:quarantine-policy"))
        self.assertTrue(twin.is_quarantined("resource-1"))
        self.assertFalse(twin.is_quarantined("resource-2"))


if __name__ == "__main__":
    unittest.main()
