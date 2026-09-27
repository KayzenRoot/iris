"""WO-0035 H01 negative/control probes of existing M09 in-process semantics.

Synthetic fixtures deliberately use caller-created strings. A test showing
accepted text-only evidence is a trust-boundary gap in a naive future M11
integration, NOT authenticated M11 evidence, OS observation or a live port.
Original future LV-01..06 remain SPECIFIED_NOT_EXECUTED.
"""
from __future__ import annotations

import unittest

from iris_resource_twin import (
    CommitmentState, CooperativeReleaseRequest, CooperativeReleaseResponse,
    EvidenceOrigin, LeakCandidate, OwnerLivenessRef, StaleCommitmentCandidate,
    StaleCommitmentReaper, evaluate_cooperative_release, confirm_leak,
)
from m09_support import make_snapshot


class H01SyntheticExistingM09ReverseSeamTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot=make_snapshot(physical_id="h01-fixture-gpu",
                                    snapshot_id="h01-fixture-snapshot")
        self.candidate=LeakCandidate(
            "h01-leak-candidate",self.snapshot.identity.stable_key,
            "lease-h01","owner-h01",100,500,("obs-h01-one","obs-h01-two"),1_000)
        self.fake_dead=OwnerLivenessRef(
            "owner-h01","TERMINATED","M11:caller-controlled-prefix",
            1_500,"caller-controlled-liveness-reference")
        self.release=CooperativeReleaseRequest(
            "req-h01","lease-h01","owner-h01",1_000,2_000,
            "M09:reason-test-fixture")

    def ack(self, *, request_id: str = "req-h01", owner_ref: str = "owner-h01",
            response: str = "ACCEPTED", at: int = 1_500,
            evidence_ref: str = "caller-controlled-ack") -> CooperativeReleaseResponse:
        return CooperativeReleaseResponse(request_id,owner_ref,response,at,evidence_ref)

    def leak(self, owner=None, *, snapshot=None, now=2_000, threshold=100):
        return confirm_leak(
            self.candidate,owner if owner is not None else self.fake_dead,
            fresh_snapshot=self.snapshot if snapshot is None else snapshot,
            now_ms=now,minimum_excess_bytes=threshold)

    def stale(self, *, owner_ref: str = "owner-h01"):
        return StaleCommitmentCandidate(
            "h01-stale-candidate",self.snapshot.identity.stable_key,"lease-h01",
            owner_ref,CommitmentState.EXPIRED,4_096,1_000,
            ("M09:lease-expiry-fixture",))

    def test_01_textual_m11_prefix_creates_structurally_accepted_terminated_ref(self):
        self.assertEqual(self.fake_dead.state,"TERMINATED")
        self.assertEqual(self.fake_dead.authority_ref,"M11:caller-controlled-prefix")

    def test_02_non_m11_prefix_for_nonunknown_liveness_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"referenced to M11"):
            OwnerLivenessRef("owner-h01","TERMINATED","OTHER:untrusted",
                             1_500,"source:some-evidence")

    def test_03_unknown_allows_unverified_external_reference_without_authority(self):
        uncertain=OwnerLivenessRef("owner-h01","UNKNOWN","OTHER:unverified",
                                   1_500,"source:no-verified-observation")
        self.assertEqual(uncertain.state,"UNKNOWN")
        self.assertFalse(self.leak(uncertain).confirmed)

    def test_04_caller_claimed_m11_prefix_can_confirm_inprocess_leak_semantics(self):
        # This positive in-process result IS NOT proof of a genuine M11
        # issuer, OS termination, permission or a future cross-module leak.
        local=self.leak()
        self.assertTrue(local.confirmed)
        self.assertEqual(len(local.evidence_digest),64)

    def test_05_alive_structural_ref_does_not_confirm_leak(self):
        alive=OwnerLivenessRef("owner-h01","ALIVE","M11:caller-controlled-prefix",
                               1_500,"source:alive-claim")
        self.assertFalse(self.leak(alive).confirmed)

    def test_06_wrong_owner_terminated_ref_does_not_confirm_leak(self):
        wrong=OwnerLivenessRef("other-owner","TERMINATED","M11:claimed",
                               1_500,"source:wrong-owner")
        self.assertFalse(self.leak(wrong).confirmed)

    def test_07_stale_terminated_ref_does_not_confirm_leak(self):
        long_lived=make_snapshot(physical_id="h01-fixture-gpu",
                                 snapshot_id="h01-long-lived",
                                 expires_at_ms=100_000)
        self.assertTrue(long_lived.is_fresh(32_000))
        self.assertFalse(self.leak(snapshot=long_lived,now=32_000).confirmed)

    def test_08_synthetic_reported_looking_resource_does_not_confirm_leak(self):
        synthetic=make_snapshot(physical_id="h01-fixture-gpu",
                                snapshot_id="h01-synthetic",
                                evidence_origin=EvidenceOrigin.SYNTHETIC_FIXTURE)
        self.assertFalse(self.leak(snapshot=synthetic).confirmed)

    def test_09_caller_claimed_termination_reaper_remains_pending_resource_truth(self):
        receipt=StaleCommitmentReaper().reconcile(
            self.stale(),self.fake_dead,now_ms=2_000)
        self.assertEqual(receipt.status,
                         "RECONCILIATION_RECORDED_PENDING_FRESH_RESOURCE_TRUTH")
        self.assertIsNone(receipt.freed_bytes)
        self.assertFalse(receipt.capacity_reclaimed)

    def test_10_unknown_liveness_reaper_quarantines_without_freed_bytes(self):
        unknown=OwnerLivenessRef("owner-h01","UNKNOWN","unverified:source",
                                 1_500,"source:missing")
        receipt=StaleCommitmentReaper().reconcile(
            self.stale(),unknown,now_ms=2_000)
        self.assertEqual(receipt.status,"QUARANTINED_OWNER_LIVENESS_UNKNOWN")
        self.assertFalse(receipt.capacity_reclaimed)

    def test_11_alive_liveness_reaper_preserves_owner_and_does_not_reclaim(self):
        alive=OwnerLivenessRef("owner-h01","ALIVE","M11:claimed",
                               1_500,"source:alive")
        receipt=StaleCommitmentReaper().reconcile(
            self.stale(),alive,now_ms=2_000)
        self.assertEqual(receipt.status,"PRESERVED_OWNER_ALIVE")
        self.assertFalse(receipt.capacity_reclaimed)

    def test_12_unverified_caller_claimed_acceptance_is_only_local_ack_state(self):
        outcome=evaluate_cooperative_release(self.release,self.ack(),
                                             now_ms=1_600)
        self.assertEqual(outcome.status,
                         "ACCEPTED_AWAITING_RESOURCE_RECONCILIATION")
        self.assertFalse(outcome.capacity_reclaimed)

    def test_13_wrong_request_ack_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"exact request and owner"):
            evaluate_cooperative_release(
                self.release,self.ack(request_id="req-other"),now_ms=1_600)

    def test_14_wrong_owner_ack_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"exact request and owner"):
            evaluate_cooperative_release(
                self.release,self.ack(owner_ref="other-owner"),now_ms=1_600)

    def test_15_response_claiming_a_future_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"cannot be from the future"):
            evaluate_cooperative_release(
                self.release,self.ack(at=1_900),now_ms=1_600)

    def test_16_pre_request_time_ack_can_pass_local_shape_check_not_issuer(self):
        # No lower-bound on response time: the old in-process evaluator
        # is not a future externally authenticated ACK verifier.
        premature=evaluate_cooperative_release(
            self.release,self.ack(at=900),now_ms=1_600)
        self.assertEqual(premature.status,
                         "ACCEPTED_AWAITING_RESOURCE_RECONCILIATION")
        self.assertFalse(premature.capacity_reclaimed)

    def test_17_late_matching_ack_times_out_without_reclaim(self):
        late=evaluate_cooperative_release(self.release,self.ack(at=2_100),
                                         now_ms=2_200)
        self.assertEqual(late.status,"TIMED_OUT")
        self.assertFalse(late.capacity_reclaimed)

    def test_18_missing_ack_before_and_after_deadline_never_reclaims(self):
        pending=evaluate_cooperative_release(self.release,None,now_ms=1_500)
        timeout=evaluate_cooperative_release(self.release,None,now_ms=2_100)
        self.assertEqual((pending.status,timeout.status),("PENDING","TIMED_OUT"))
        self.assertFalse(pending.capacity_reclaimed or timeout.capacity_reclaimed)

    def test_19_replayed_identical_ack_is_deterministic_but_has_no_replay_store(self):
        ack=self.ack()
        first=evaluate_cooperative_release(self.release,ack,now_ms=1_600)
        second=evaluate_cooperative_release(self.release,ack,now_ms=1_600)
        self.assertEqual(first,second)
        self.assertFalse(first.capacity_reclaimed)

    def test_20_claimed_dead_reaper_rejects_wrong_owner_or_future_evidence(self):
        with self.assertRaisesRegex(ValueError,"cannot use future evidence"):
            StaleCommitmentReaper().reconcile(
                self.stale(),self.fake_dead,now_ms=1_200)
        other=self.stale(owner_ref="another-owner")
        with self.assertRaises(ValueError):
            StaleCommitmentReaper().reconcile(
                other,self.fake_dead,now_ms=2_000)


if __name__=="__main__":
    unittest.main()
