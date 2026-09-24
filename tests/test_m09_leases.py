from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import unittest

from iris_resource_twin import (
    ClaimKind,
    ClaimQuantity,
    ClaimAlgebra,
    Confidence,
    EvidenceOrigin,
    LeaseBook,
    LeaseRequest,
    LeaseState,
    MutationActorKind,
    MutationContext,
    FairnessEvidence,
    OwnerLivenessEvidence,
    ReservationIntent,
    ResidencyKey,
    ResidencyRegistry,
    ResidencyState,
    FragmentationEvidence,
    WarmResidencyHint,
    detect_priority_inversion,
    ResourceClaim,
    ResourceUnit,
    convert_quantity,
)
from m09_support import GIB, make_snapshot


def request(lease_id: str, resource_key: str, size: int, *, kind: ClaimKind = ClaimKind.HARD, share_key: str | None = None, ttl: int = 5_000, priority: int = 0, revocable: bool = False, actor_kind: str = "INTERACTIVE", actor_ref: str = "M09:actor", authorization_ref: str = "M09:actor-authorization", mutation_context: MutationContext | None = None) -> LeaseRequest:
    return LeaseRequest(
        lease_id, f"idem-{lease_id}", f"owner-{lease_id}", authorization_ref,
        (ResourceClaim(f"claim-{lease_id}", resource_key, ClaimQuantity(size, ResourceUnit.BYTE), kind, share_key),),
        1_000, ttl, priority, revocable,
        actor_ref=actor_ref, actor_kind=actor_kind, mutation_context=mutation_context,
        priority_evidence_ref="M01:authorized-priority-policy" if priority else None,
    )


class TestM09Leases(unittest.TestCase):
    def test_automated_lease_mutations_require_complete_origin_and_replay_context(self) -> None:
        snapshot = make_snapshot()
        key = snapshot.identity.stable_key
        with self.assertRaisesRegex(ValueError, "complete mutation context"):
            request("auto-missing-origin", key, GIB, actor_kind="AUTOMATION", actor_ref="agent:lease-controller")

        grant_context = MutationContext(
            MutationActorKind.AUTOMATION, "agent:lease-controller", "M57:grant-authorization",
            "request:grant-1", "idem-auto-lease", "workflow:lease-controller",
        )
        lease_request = request(
            "auto-lease", key, GIB, actor_kind="AUTOMATION",
            actor_ref="agent:lease-controller", authorization_ref="M57:grant-authorization",
            mutation_context=grant_context,
        )
        book = LeaseBook()
        lease = book.grant(lease_request, {key: snapshot}, now_ms=1_100)
        self.assertEqual(lease.mutation_context, grant_context)
        with self.assertRaisesRegex(ValueError, "complete mutation context"):
            book.renew(lease.lease_id, {key: snapshot}, now_ms=1_200, ttl_ms=2_000, expected_epoch=lease.epoch, authorization_ref="M57:renew-authorization")

        renewal_context = MutationContext(
            MutationActorKind.AUTOMATION, "agent:lease-controller", "M57:renew-authorization",
            "request:renew-1", "idem:renew-1", "workflow:lease-controller",
        )
        renewed = book.renew(
            lease.lease_id, {key: snapshot}, now_ms=1_200, ttl_ms=2_000,
            expected_epoch=lease.epoch, authorization_ref="M57:renew-authorization",
            mutation_context=renewal_context,
        )
        self.assertEqual(renewed.mutation_context, renewal_context)
        with self.assertRaisesRegex(ValueError, "complete mutation context"):
            book.release(lease.lease_id, now_ms=1_300, expected_epoch=renewed.epoch, causal_ref="request:release-1")

        release_context = MutationContext(
            MutationActorKind.AUTOMATION, "agent:lease-controller", "M57:release-authorization",
            "request:release-1", "idem:release-1", "workflow:lease-controller",
        )
        tombstone = book.release(
            lease.lease_id, now_ms=1_300, expected_epoch=renewed.epoch,
            causal_ref="request:release-1", mutation_context=release_context,
        )
        self.assertEqual(tombstone.mutation_context, release_context)

    def test_claim_algebra_is_typed_loss_aware_and_does_not_grant(self) -> None:
        key = make_snapshot().identity.stable_key
        left = ResourceClaim("claim-left", key, ClaimQuantity(1, ResourceUnit.GIBIBYTE), ClaimKind.HARD, "shared-model-revision")
        right = ResourceClaim("claim-right", key, ClaimQuantity(512, ResourceUnit.MEBIBYTE), ClaimKind.HARD, "shared-model-revision")
        soft = ResourceClaim("claim-soft", key, ClaimQuantity(2, ResourceUnit.GIBIBYTE), ClaimKind.SOFT)
        aggregate = ClaimAlgebra.aggregate((left, right, soft))[0]
        self.assertEqual(aggregate.hard_bytes, GIB)
        self.assertEqual(aggregate.soft_bytes, 2 * GIB)
        self.assertEqual(len(LeaseBook().active()), 0)
        with self.assertRaisesRegex(ValueError, "fractional bytes"):
            convert_quantity(ClaimQuantity(1_025, ResourceUnit.BYTE), ResourceUnit.KIBIBYTE)
        floor = convert_quantity(ClaimQuantity(1_025, ResourceUnit.BYTE), ResourceUnit.KIBIBYTE, rounding="FLOOR")
        ceiling = convert_quantity(ClaimQuantity(1_025, ResourceUnit.BYTE), ResourceUnit.KIBIBYTE, rounding="CEILING")
        self.assertEqual((floor.value, ceiling.value), (1, 2))
        self.assertFalse(floor.exact)

    def test_atomic_grant_capacity_idempotency_and_conservation(self) -> None:
        snapshot = make_snapshot()
        book = LeaseBook()
        req = request("lease-1", snapshot.identity.stable_key, GIB)
        lease = book.grant(req, {snapshot.identity.stable_key: snapshot}, now_ms=1_100)
        self.assertEqual(book.grant(req, {snapshot.identity.stable_key: snapshot}, now_ms=1_200), lease)
        self.assertEqual(len(book.active()), 1)
        with self.assertRaisesRegex(ValueError, "overcommit"):
            book.grant(request("lease-big", snapshot.identity.stable_key, 7 * GIB), {snapshot.identity.stable_key: snapshot}, now_ms=1_200)
        self.assertEqual(len(book.active()), 1)
        self.assertEqual(book.fairness_evidence()[-1].event, "DENIED_CAPACITY")

    def test_concurrent_grants_cannot_double_spend_capacity(self) -> None:
        snapshot = make_snapshot()
        key = snapshot.identity.stable_key
        book = LeaseBook()
        requests = tuple(request(f"parallel-{index}", key, GIB) for index in range(10))

        def attempt(item: LeaseRequest) -> bool:
            try:
                book.grant(item, {key: snapshot}, now_ms=1_100)
                return True
            except ValueError:
                return False

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = tuple(executor.map(attempt, requests))
        self.assertEqual(sum(results), 6)
        self.assertEqual(sum(claim.bytes for lease in book.active() for claim in lease.claims), 6 * GIB)

    def test_composite_multidevice_grant_preserves_each_member_atomically(self) -> None:
        first = make_snapshot(physical_id="composite-gpu-a")
        second = make_snapshot(physical_id="composite-gpu-b")
        req = LeaseRequest(
            "multi-device", "idem-multi-device", "owner-multi-device", "M09:actor",
            (
                ResourceClaim("member-a", first.identity.stable_key, ClaimQuantity(GIB, ResourceUnit.BYTE), ClaimKind.HARD),
                ResourceClaim("member-b", second.identity.stable_key, ClaimQuantity(2 * GIB, ResourceUnit.BYTE), ClaimKind.HARD),
            ), 1_000, 1_000,
        )
        lease = LeaseBook().grant(req, {first.identity.stable_key: first, second.identity.stable_key: second}, now_ms=1_100)
        self.assertEqual({claim.resource_key for claim in lease.claims}, {first.identity.stable_key, second.identity.stable_key})
        self.assertEqual(sum(claim.bytes for claim in lease.claims), 3 * GIB)

    def test_composite_claim_is_all_or_nothing_with_unknown_member(self) -> None:
        first = make_snapshot(physical_id="gpu-a")
        unknown = make_snapshot(physical_id="gpu-b", snapshot_id="unknown-b", confidence=Confidence.UNKNOWN)
        req = LeaseRequest(
            "composite", "idem-composite", "owner-composite", "M09:actor",
            (
                ResourceClaim("claim-a", first.identity.stable_key, ClaimQuantity(GIB, ResourceUnit.BYTE), ClaimKind.HARD),
                ResourceClaim("claim-b", unknown.identity.stable_key, ClaimQuantity(GIB, ResourceUnit.BYTE), ClaimKind.HARD),
            ), 1_000, 1_000,
        )
        book = LeaseBook()
        with self.assertRaisesRegex(ValueError, "cannot authorize"):
            book.grant(req, {first.identity.stable_key: first, unknown.identity.stable_key: unknown}, now_ms=1_100)
        self.assertEqual(book.active(), ())

    def test_synthetic_or_derived_truth_never_authorizes_production_lease(self) -> None:
        synthetic = make_snapshot(evidence_origin=EvidenceOrigin.SYNTHETIC_FIXTURE)
        book = LeaseBook()
        with self.assertRaisesRegex(ValueError, "cannot authorize a production lease"):
            book.grant(request("synthetic-lease", synthetic.identity.stable_key, GIB), {synthetic.identity.stable_key: synthetic}, now_ms=1_100)
        self.assertEqual(book.active(), ())

        reported = make_snapshot()
        lease = book.grant(request("reported-lease", reported.identity.stable_key, GIB), {reported.identity.stable_key: reported}, now_ms=1_100)
        with self.assertRaisesRegex(ValueError, "reported production resource evidence"):
            book.renew(lease.lease_id, {reported.identity.stable_key: synthetic}, now_ms=1_200, ttl_ms=1_000, expected_epoch=lease.epoch, authorization_ref="M09:renewal")

    def test_renewal_requires_current_epoch_fresh_truth_and_tombstone_is_final(self) -> None:
        snapshot = make_snapshot()
        key = snapshot.identity.stable_key
        book = LeaseBook()
        lease = book.grant(request("lease-renew", key, GIB), {key: snapshot}, now_ms=1_100)
        renewed = book.renew(lease.lease_id, {key: snapshot}, now_ms=1_200, ttl_ms=3_000, expected_epoch=lease.epoch, authorization_ref="M09:renew-authority")
        self.assertGreater(renewed.epoch, lease.epoch)
        with self.assertRaisesRegex(ValueError, "stale epoch"):
            book.release(lease.lease_id, now_ms=1_300, expected_epoch=lease.epoch, causal_ref="release-old")
        tombstone = book.release(lease.lease_id, now_ms=1_300, expected_epoch=renewed.epoch, causal_ref="release-cause")
        self.assertEqual(tombstone.terminal_state, LeaseState.RELEASED)
        self.assertEqual(book.release(lease.lease_id, now_ms=1_301, expected_epoch=999, causal_ref="release-cause"), tombstone)
        with self.assertRaisesRegex(ValueError, "released twice"):
            book.release(lease.lease_id, now_ms=1_301, expected_epoch=999, causal_ref="different-cause")
        self.assertEqual(book.active(), ())

    def test_soft_reservation_is_intent_and_fairness_does_not_schedule(self) -> None:
        snapshot = make_snapshot()
        key = snapshot.identity.stable_key
        soft = request("soft-lease", key, GIB, kind=ClaimKind.SOFT, priority=10)
        book = LeaseBook()
        with self.assertRaisesRegex(ValueError, "soft reservations"):
            book.grant(soft, {key: snapshot}, now_ms=1_100)
        intent = ReservationIntent("intent-1", soft, 1_000, 5_000)
        book.enqueue(intent)
        self.assertEqual(book.intents(), (intent,))
        self.assertEqual(book.active(), ())
        self.assertEqual(book.fairness_evidence()[-1].event, "SOFT_INTENT_REQUIRED")

    def test_exclusive_and_shared_commitment_algebra(self) -> None:
        snapshot = make_snapshot()
        key = snapshot.identity.stable_key
        book = LeaseBook()
        shared_a = request("share-a", key, GIB, share_key="model-component-compatibility")
        shared_b = request("share-b", key, GIB, share_key="model-component-compatibility")
        book.grant(shared_a, {key: snapshot}, now_ms=1_100)
        book.grant(shared_b, {key: snapshot}, now_ms=1_200)
        exclusive = request("exclusive", key, GIB, kind=ClaimKind.EXCLUSIVE)
        with self.assertRaisesRegex(ValueError, "exclusive"):
            book.grant(exclusive, {key: snapshot}, now_ms=1_300)

    def test_cooperative_preemption_never_forces_release(self) -> None:
        snapshot = make_snapshot()
        key = snapshot.identity.stable_key
        book = LeaseBook()
        lease = book.grant(request("revocable", key, GIB, revocable=True), {key: snapshot}, now_ms=1_100)
        requested = book.request_cooperative_preemption(lease.lease_id, now_ms=1_200, grace_deadline_ms=1_500, expected_epoch=lease.epoch, request_ref="release-request")
        self.assertEqual(requested.state, LeaseState.PREEMPTION_REQUESTED)
        self.assertIn(requested, book.active())
        self.assertEqual(book.preemption_evidence()[0].grace_deadline_ms, 1_500)

    def test_orphan_reconciliation_uses_m11_reference_and_never_fabricates_release(self) -> None:
        snapshot = make_snapshot()
        key = snapshot.identity.stable_key
        book = LeaseBook()
        lease = book.grant(request("orphan-candidate", key, GIB), {key: snapshot}, now_ms=1_100)
        unknown = OwnerLivenessEvidence(lease.owner_ref, "UNKNOWN", "M09:unknown", 1_150, "unknown-liveness-proof")
        uncertain = book.reconcile_orphan(lease.lease_id, unknown, now_ms=1_200, maximum_liveness_age_ms=500, authorization_ref="M09:orphan-policy")
        self.assertEqual(uncertain.status, "OWNERSHIP_UNKNOWN_QUARANTINED")
        self.assertEqual(sum(claim.bytes for item in book.active() for claim in item.claims), GIB)
        terminated = OwnerLivenessEvidence(lease.owner_ref, "TERMINATED", "M11:worker-lifecycle", 1_250, "m11-termination-proof")
        result = book.reconcile_orphan(lease.lease_id, terminated, now_ms=1_300, maximum_liveness_age_ms=500, authorization_ref="M09:orphan-policy")
        self.assertEqual(result.status, "TERMINATED_RECONCILIATION_REQUIRED")
        self.assertEqual(book.active()[0].state, LeaseState.REVOCATION_REQUESTED)
        self.assertIsNone(book.tombstone(lease.lease_id))

    def test_ttl_expiry_creates_terminal_tombstone(self) -> None:
        snapshot = make_snapshot()
        key = snapshot.identity.stable_key
        book = LeaseBook()
        lease = book.grant(request("expiring", key, 100, ttl=500), {key: snapshot}, now_ms=1_100)
        expired = book.expire(now_ms=1_600)
        self.assertEqual(expired[0].lease_id, lease.lease_id)
        self.assertEqual(expired[0].terminal_state, LeaseState.EXPIRED)
        self.assertIsNone(book.tombstone("missing"))

    def test_revocation_is_separate_from_release_expiry_and_waits_for_owner_ack(self) -> None:
        snapshot = make_snapshot()
        key = snapshot.identity.stable_key
        book = LeaseBook()
        lease = book.grant(request("revoked", key, GIB), {key: snapshot}, now_ms=1_100)
        requested = book.request_revocation(
            lease.lease_id, now_ms=1_200, expected_epoch=lease.epoch,
            authorization_ref="M09:revocation-authority", reason_ref="policy-revocation",
        )
        self.assertEqual(requested.state, LeaseState.REVOCATION_REQUESTED)
        self.assertIn(requested, book.active())
        self.assertEqual(sum(item.bytes for active in book.active() for item in active.claims), GIB)
        with self.assertRaisesRegex(ValueError, "cannot be renewed"):
            book.renew(lease.lease_id, {key: snapshot}, now_ms=1_300, ttl_ms=1_000, expected_epoch=requested.epoch, authorization_ref="M09:renewal")
        tombstone = book.acknowledge_revocation(
            lease.lease_id, now_ms=1_400, expected_epoch=requested.epoch,
            owner_ack_ref="owner-acknowledged-release",
        )
        self.assertEqual(tombstone.terminal_state, LeaseState.REVOKED)
        self.assertEqual(book.active(), ())
        self.assertEqual(book.acknowledge_revocation(lease.lease_id, now_ms=1_500, expected_epoch=999, owner_ack_ref="owner-acknowledged-release"), tombstone)

    def test_residency_reference_count_requires_exact_ownership_identity(self) -> None:
        registry = ResidencyRegistry()
        key = ResidencyKey("M05:model-1", "revision-7", "M05:component-a", make_snapshot().identity.stable_key, "c" * 64)
        loading = registry.transition(key, ResidencyState.LOADING, expected_epoch=0, at_ms=1_000, authorization_ref="M09:residency-auth", causal_ref="load-event")
        resident = registry.transition(key, ResidencyState.RESIDENT, expected_epoch=loading.epoch, at_ms=1_100, authorization_ref="M09:residency-auth", causal_ref="verification-event", verification_ref="M09:integrity-verification")
        self.assertEqual(resident.current_state, ResidencyState.RESIDENT)
        retain_a = MutationContext(MutationActorKind.INTERACTIVE, "M02:consumer-a", "M02:residency-auth", "request:retain-a", "idem:retain-a")
        retain_b = MutationContext(MutationActorKind.INTERACTIVE, "M02:consumer-b", "M02:residency-auth", "request:retain-b", "idem:retain-b")
        release_a = MutationContext(MutationActorKind.INTERACTIVE, "M02:consumer-a", "M02:residency-auth", "request:release-a", "idem:release-a")
        self.assertEqual(registry.retain(key, "M02:consumer-a", mutation_context=retain_a), 1)
        self.assertEqual(registry.retain(key, "M02:consumer-a", mutation_context=retain_a), 1)
        self.assertEqual(registry.retain(key, "M02:consumer-b", mutation_context=retain_b), 2)
        self.assertEqual(registry.release(key, "M02:consumer-a", mutation_context=release_a), 1)
        self.assertEqual(tuple(event.operation for event in registry.reference_history(key)), ("RETAIN", "RETAIN", "RELEASE"))
        with self.assertRaisesRegex(ValueError, "does not own"):
            registry.release(key, "M02:other", mutation_context=MutationContext(MutationActorKind.INTERACTIVE, "M02:consumer-b", "M02:residency-auth", "request:release-other", "idem:release-other"))
        self.assertEqual(registry.count(key), 1)
        with self.assertRaisesRegex(ValueError, "active consumers"):
            registry.transition(key, ResidencyState.UNLOADING, expected_epoch=resident.epoch, at_ms=1_200, authorization_ref="M09:residency-auth", causal_ref="unload-event")

    def test_residency_automation_context_is_preserved_and_idempotent(self) -> None:
        key = ResidencyKey("M05:model-auto", "revision-2", "M05:component-auto", make_snapshot().identity.stable_key, "f" * 64)
        context = MutationContext(
            MutationActorKind.AUTOMATION, "agent:residency-controller", "M57:residency-auth",
            "request:residency-load", "idem:residency-load", "workflow:residency-controller",
        )
        registry = ResidencyRegistry()
        first = registry.transition(
            key, ResidencyState.LOADING, expected_epoch=0, at_ms=1_000,
            authorization_ref=context.authorization_ref, causal_ref=context.causal_request_ref,
            mutation_context=context,
        )
        replay = registry.transition(
            key, ResidencyState.LOADING, expected_epoch=0, at_ms=1_000,
            authorization_ref=context.authorization_ref, causal_ref=context.causal_request_ref,
            mutation_context=context,
        )
        self.assertEqual(replay, first)
        self.assertEqual(first.mutation_context, context)
        conflict = MutationContext(
            MutationActorKind.AUTOMATION, "agent:residency-controller", "M57:residency-auth",
            "request:other-load", "idem:residency-load", "workflow:residency-controller",
        )
        with self.assertRaisesRegex(ValueError, "conflicting mutation semantics"):
            registry.transition(
                key, ResidencyState.QUARANTINED, expected_epoch=0, at_ms=1_000,
                authorization_ref=conflict.authorization_ref, causal_ref=conflict.causal_request_ref,
                mutation_context=conflict,
            )

    def test_residency_identity_journal_and_timestamps_are_bounded_and_exact(self) -> None:
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            ResidencyKey("M05:model", "revision-1", "M05:component", "resource-key", "compatibility-ref")
        key = ResidencyKey("M05:model-bounded", "revision-1", "M05:component", make_snapshot().identity.stable_key, "e" * 64)
        registry = ResidencyRegistry(maximum_entries=1, maximum_journal_entries=1)
        first = registry.transition(key, ResidencyState.LOADING, expected_epoch=0, at_ms=1_000, authorization_ref="M09:residency-auth", causal_ref="load-bounded")
        with self.assertRaisesRegex(ValueError, "monotonic"):
            registry.transition(key, ResidencyState.PARTIAL, expected_epoch=first.epoch, at_ms=999, authorization_ref="M09:residency-auth", causal_ref="stale-time")
        with self.assertRaisesRegex(ValueError, "journal bound"):
            registry.transition(key, ResidencyState.PARTIAL, expected_epoch=first.epoch, at_ms=1_001, authorization_ref="M09:residency-auth", causal_ref="second-event")

    def test_fragmentation_unknown_and_warmth_hints_do_not_authorize_capacity_or_selection(self) -> None:
        unknown = FragmentationEvidence("resource-1", 4 * GIB, None, "provider-fragmentation", 1_000)
        known = FragmentationEvidence("resource-1", 4 * GIB, GIB, "provider-fragmentation", 1_000)
        self.assertIsNone(unknown.can_fit_contiguous(2 * GIB))
        self.assertFalse(known.can_fit_contiguous(2 * GIB))
        self.assertTrue(known.can_fit_contiguous(GIB))
        key = ResidencyKey("M05:model", "revision-1", "M05:component", make_snapshot().identity.stable_key, "d" * 64)
        hint = WarmResidencyHint("warmth-1", key, 1_000, 2_000, "residency-observation")
        self.assertTrue(hint.is_current(1_500))
        self.assertFalse(hint.is_current(2_001))

    def test_priority_inversion_is_evidence_not_reordering(self) -> None:
        snapshot = make_snapshot()
        key = snapshot.identity.stable_key
        book = LeaseBook()
        blocker = book.grant(request("low-priority-blocker", key, GIB, priority=1), {key: snapshot}, now_ms=1_100)
        waiting = FairnessEvidence("wait-evidence", "waiting-lease", "WAITING", 1_200, 10, 500, "M01:priority-policy", "wait-detail")
        inversion = detect_priority_inversion(waiting, blocker)
        self.assertEqual(inversion.waiting_lease_id, "waiting-lease")
        self.assertEqual(inversion.blocking_lease_id, blocker.lease_id)
        equal = FairnessEvidence("equal-evidence", "other-waiter", "WAITING", 1_200, 1, 500, "M01:priority-policy", "other-detail")
        self.assertIsNone(detect_priority_inversion(equal, blocker))


if __name__ == "__main__":
    unittest.main()
