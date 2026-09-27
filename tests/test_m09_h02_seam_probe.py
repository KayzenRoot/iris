"""WO-0034 H02 deterministic *existing M09 semantic* seam probes, not HX/LV or OS tests.

These tests intentionally show where separately correct ResourceTwin and
LeaseBook operations CANNOT jointly attest an exact cross-process grant.
Existing frozen M09 behavior is not changed or treated as a new defect.
"""
from __future__ import annotations
import unittest
from iris_resource_twin import (
    ClaimKind, ClaimQuantity, Confidence, EvidenceOrigin, LeaseBook,
    LeaseRequest, LeaseState, ResourceClaim, ResourceTwin, ResourceUnit,
)
from m09_support import GIB, make_snapshot


def make_request(lease_id: str, *snapshots, ttl_ms: int = 2_000) -> LeaseRequest:
    claims=tuple(ResourceClaim(
        f"claim-{lease_id}-{i}",item.identity.stable_key,
        ClaimQuantity(GIB,ResourceUnit.BYTE),ClaimKind.HARD)
        for i,item in enumerate(snapshots))
    return LeaseRequest(lease_id,f"idem-{lease_id}",f"M11:candidate-{lease_id}",
                        "M09:synthetic-fixture-actor",claims,1_000,ttl_ms,
                        revocable=True)


def publish(twin: ResourceTwin, snapshot) -> None:
    twin.publish(snapshot,event_id=f"publish-{snapshot.snapshot_id}",
                 at_ms=1_000,authorization_ref="M09:synthetic-fixture-actor")


class H02ExistingSemanticSeamProbes(unittest.TestCase):
    def setUp(self) -> None:
        self.twin=ResourceTwin()
        self.book=LeaseBook()
        self.snapshot=make_snapshot(
            physical_id="h02-synthetic-accelerator",
            snapshot_id="h02-original")
        self.key=self.snapshot.identity.stable_key
        publish(self.twin,self.snapshot)
        self.req=make_request("h02-original-lease",self.snapshot)

    def grant(self):
        return self.book.grant(self.req,{self.key:self.snapshot},now_ms=1_100)

    def invalidate(self) -> None:
        self.twin.invalidate(self.snapshot.snapshot_id,
                             reason="synthetic-fixture-invalidated",
                             event_id="invalidate-h02-original",
                             at_ms=1_200,
                             authorization_ref="M09:synthetic-fixture-actor")

    def test_01_control_individual_snapshot_and_lease_are_valid_at_capture(self):
        self.assertIs(self.twin.admission_snapshot(self.key,now_ms=1_100),self.snapshot)
        lease=self.grant()
        self.assertEqual(lease.state,LeaseState.ACTIVE)
        self.assertEqual(len(self.book.active()),1)

    def test_02_detached_earlier_snapshot_remains_fresh_after_twin_invalidates(self):
        cached=self.twin.admission_snapshot(self.key,now_ms=1_100)
        self.invalidate()
        self.assertIsNone(self.twin.admission_snapshot(self.key,now_ms=1_300))
        self.assertTrue(cached.is_fresh(1_300))
        self.assertIn((self.snapshot.snapshot_id,"synthetic-fixture-invalidated"),
                      self.twin.invalidations())

    def test_03_detached_snapshot_can_be_passed_to_separate_lease_grant(self):
        cached=self.twin.admission_snapshot(self.key,now_ms=1_100)
        self.invalidate()
        # This is a deliberately naive caller interleaving, NOT an M09 promise
        # of an authorized future M11 grant or a new M09 v1.0 regression.
        granted=self.book.grant(self.req,{self.key:cached},now_ms=1_300)
        self.assertEqual(granted.state,LeaseState.ACTIVE)
        self.assertIsNone(self.twin.admission_snapshot(self.key,now_ms=1_300))
        self.assertFalse(hasattr(granted,"m09_m11_owner_verified_receipt"))

    def test_04_invalidation_after_grant_does_not_transition_independent_lease(self):
        lease=self.grant()
        self.invalidate()
        self.assertEqual(self.book.active(),(lease,))
        self.assertIsNone(self.twin.admission_snapshot(self.key,now_ms=1_300))

    def test_05_revocation_requested_is_still_in_active_collection(self):
        lease=self.grant()
        changed=self.book.request_revocation(
            lease.lease_id,now_ms=1_200,expected_epoch=lease.epoch,
            authorization_ref="M09:synthetic-fixture-actor",
            reason_ref="h02-fixture-revocation")
        self.assertEqual(changed.state,LeaseState.REVOCATION_REQUESTED)
        self.assertEqual(self.book.active(),(changed,))
        self.assertNotEqual(changed.epoch,lease.epoch)

    def test_06_detached_active_lease_copy_survives_subsequent_revocation(self):
        lease=self.grant()
        captured=self.book.active()[0]
        changed=self.book.request_revocation(
            lease.lease_id,now_ms=1_200,expected_epoch=lease.epoch,
            authorization_ref="M09:synthetic-fixture-actor",
            reason_ref="h02-fixture-revocation")
        self.assertEqual(captured.state,LeaseState.ACTIVE)
        self.assertEqual(captured.epoch,lease.epoch)
        self.assertEqual(changed.state,LeaseState.REVOCATION_REQUESTED)
        self.assertEqual(self.book.active()[0].epoch,changed.epoch)

    def test_07_active_without_a_clock_cannot_prove_unexpired_at_use(self):
        lease=self.grant()
        self.assertGreaterEqual(5_000,lease.expires_at_ms)
        self.assertEqual(self.book.active(),(lease,))
        # .active() has no now_ms parameter and does not independently
        # assert a remote consumer's future action-time lease validity.

    def test_08_twin_event_epoch_and_lease_epoch_are_not_jointly_bound(self):
        lease=self.grant()
        self.assertEqual(self.twin.history(self.key)[-1].state_epoch,1)
        self.invalidate()
        self.assertEqual(self.twin.history(self.key)[-1].state_epoch,2)
        self.assertEqual(self.book.active()[0].epoch,lease.epoch)

    def test_09_observed_synthetic_is_not_sufficient_for_production_grant(self):
        synthetic=make_snapshot(
            physical_id="h02-synthetic-origin",
            snapshot_id="h02-synthetic-origin-snapshot",
            evidence_origin=EvidenceOrigin.SYNTHETIC_FIXTURE,
            confidence=Confidence.OBSERVED)
        twin=ResourceTwin()
        publish(twin,synthetic)
        key=synthetic.identity.stable_key
        self.assertIs(twin.admission_snapshot(key,now_ms=1_100),synthetic)
        with self.assertRaisesRegex(ValueError,"synthetic or derived"):
            LeaseBook().grant(make_request("h02-synthetic-denied",synthetic),
                              {key:synthetic},now_ms=1_100)

    def test_10_complete_composite_grant_is_atomic_inside_leasebook(self):
        a=make_snapshot(physical_id="h02-gpu-a",snapshot_id="h02-a")
        b=make_snapshot(physical_id="h02-gpu-b",snapshot_id="h02-b")
        req=make_request("h02-composite-control",a,b)
        lease=LeaseBook().grant(req,{
            a.identity.stable_key:a,b.identity.stable_key:b},now_ms=1_100)
        self.assertEqual(lease.state,LeaseState.ACTIVE)
        self.assertEqual(len({c.resource_key for c in lease.claims}),2)

    def test_11_detached_composite_member_can_be_invalidated_before_grant(self):
        a=make_snapshot(physical_id="h02-gpu-a",snapshot_id="h02-a")
        b=make_snapshot(physical_id="h02-gpu-b",snapshot_id="h02-b")
        twin=ResourceTwin()
        publish(twin,a)
        publish(twin,b)
        cached={s.identity.stable_key:twin.admission_snapshot(
            s.identity.stable_key,now_ms=1_100) for s in (a,b)}
        twin.invalidate(b.snapshot_id,reason="synthetic-second-member-invalidated",
                        event_id="invalidate-h02-b",at_ms=1_200,
                        authorization_ref="M09:synthetic-fixture-actor")
        self.assertIsNone(twin.admission_snapshot(b.identity.stable_key,now_ms=1_300))
        # LeaseBook can independently create a composite lease from earlier
        # detached (still fresh) snapshots, but this is NOT a joint cut.
        lease=LeaseBook().grant(make_request("h02-composite-cached",a,b),
                                cached,now_ms=1_300)
        self.assertEqual({c.resource_key for c in lease.claims},
                         {a.identity.stable_key,b.identity.stable_key})

    def test_12_missing_mandatory_composite_member_still_fails_closed(self):
        a=make_snapshot(physical_id="h02-gpu-a",snapshot_id="h02-a")
        b=make_snapshot(physical_id="h02-gpu-b",snapshot_id="h02-b")
        req=make_request("h02-composite-incomplete",a,b)
        with self.assertRaisesRegex(ValueError,"no matching authoritative snapshot"):
            LeaseBook().grant(req,{a.identity.stable_key:a},now_ms=1_100)

    def test_13_revoking_lease_cannot_be_renewed_as_active(self):
        lease=self.grant()
        current=self.book.request_revocation(
            lease.lease_id,now_ms=1_200,expected_epoch=lease.epoch,
            authorization_ref="M09:synthetic-fixture-actor",
            reason_ref="h02-fixture-revocation")
        with self.assertRaisesRegex(ValueError,"pending preemption or revocation"):
            self.book.renew(lease.lease_id,{self.key:self.snapshot},now_ms=1_300,
                            ttl_ms=1_000,expected_epoch=current.epoch,
                            authorization_ref="M09:synthetic-fixture-actor")

    def test_14_wrong_original_lease_epoch_cannot_authorize_revocation(self):
        lease=self.grant()
        self.book.request_revocation(lease.lease_id,now_ms=1_200,
            expected_epoch=lease.epoch,
            authorization_ref="M09:synthetic-fixture-actor",
            reason_ref="h02-fixture-revocation")
        with self.assertRaises(ValueError):
            self.book.request_revocation(lease.lease_id,now_ms=1_300,
                expected_epoch=lease.epoch,
                authorization_ref="M09:synthetic-fixture-actor",
                reason_ref="h02-wrong-revocation")

if __name__=="__main__":
    unittest.main()
