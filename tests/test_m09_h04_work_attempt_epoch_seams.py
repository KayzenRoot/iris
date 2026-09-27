"""WO-0036 H04 existing M09 lease work/attempt/epoch synthetic semantic probes.

A text label in owner_ref/purpose_ref is NOT M02 accepted revision or M06
attempt authorization. All fixtures are local; no M11 process/OS/port exists.
Original future HX/LV/PO/M12 tests remain SPECIFIED_NOT_EXECUTED.
"""
from __future__ import annotations
from dataclasses import replace
import unittest

from iris_resource_twin import (
    ClaimKind, ClaimQuantity, LeaseBook, LeaseRequest, LeaseState,
    ResourceClaim, ResourceUnit,
)
from m09_support import make_snapshot


class H04SyntheticExistingM09BindingSeams(unittest.TestCase):
    def setUp(self):
        self.book=LeaseBook()
        self.snapshot=make_snapshot(
            physical_id="h04-synthetic-resource",snapshot_id="h04-observation")
        self.key=self.snapshot.identity.stable_key
        self.claim=ResourceClaim(
            "h04-claim",self.key,ClaimQuantity(4096,ResourceUnit.BYTE),
            ClaimKind.HARD,purpose_ref="M06:unverified-text-attempt-A")
        self.req=LeaseRequest(
            "h04-lease","h04-idempotency","M11:unverified-owner",
            "M09:synthetic-test-auth",(self.claim,),1_000,5_000,
            revocable=True)
    def grant(self,request=None,now_ms=1_100):
        return self.book.grant(self.req if request is None else request,
                               {self.key:self.snapshot},now_ms=now_ms)
    def revoke(self,lease,now_ms=1_200):
        return self.book.request_revocation(
            lease.lease_id,now_ms=now_ms,expected_epoch=lease.epoch,
            authorization_ref="M09:synthetic-test-auth",
            reason_ref="h04-synthetic-revocation")
    def renewal(self,lease,now_ms=1_200):
        return self.book.renew(
            lease.lease_id,{self.key:self.snapshot},now_ms=now_ms,
            ttl_ms=2_000,expected_epoch=lease.epoch,
            authorization_ref="M09:synthetic-test-auth")

    def test_01_local_grant_records_typed_owner_claims_digest_and_epoch(self):
        granted=self.grant()
        self.assertEqual(granted.owner_ref,self.req.owner_ref)
        self.assertEqual(granted.claims[0].purpose_ref,self.claim.purpose_ref)
        self.assertEqual(granted.state,LeaseState.ACTIVE)
        self.assertGreaterEqual(granted.epoch,1)
        self.assertEqual(len(granted.request_digest),64)

    def test_02_same_full_request_idempotently_returns_same_grant(self):
        first=self.grant()
        self.assertIs(self.grant(),first)

    def test_03_same_idempotency_different_unverified_owner_ref_conflicts(self):
        self.grant()
        foreign=replace(self.req,owner_ref="M11:foreign-owner")
        with self.assertRaisesRegex(ValueError,"already bound"):
            self.grant(foreign)

    def test_04_same_idempotency_changed_m06_purpose_text_conflicts(self):
        self.grant()
        other=replace(self.req,claims=(replace(
            self.claim,purpose_ref="M06:unverified-text-attempt-B"),))
        with self.assertRaisesRegex(ValueError,"already bound"):
            self.grant(other)

    def test_05_distinct_leases_same_owner_accept_separate_unverified_purposes(self):
        first=self.grant()
        second=replace(
            self.req,lease_id="h04-other-lease",
            idempotency_key="h04-other-idempotency",
            claims=(replace(self.claim,claim_id="h04-other-claim",
                            purpose_ref="M06:unverified-text-attempt-B"),),
            mutation_context=None)
        other=self.grant(second)
        self.assertEqual(first.owner_ref,other.owner_ref)
        self.assertNotEqual(first.claims[0].purpose_ref,
                            other.claims[0].purpose_ref)
        self.assertEqual(len(self.book.active()),2)
        # This is not M02 graph or M06 accepted attempt equivalence proof.

    def test_06_arbitrary_m02_looking_owner_ref_is_a_structural_label_only(self):
        forged=replace(self.req,owner_ref="M02:accepted-work-claimed-by-caller")
        granted=self.grant(forged)
        self.assertEqual(granted.owner_ref,forged.owner_ref)
        self.assertFalse(hasattr(granted,"m02_accepted_plan_revision"))
        self.assertFalse(hasattr(granted,"m02_issuer_verification"))

    def test_07_arbitrary_m06_looking_purpose_ref_is_a_structural_label_only(self):
        forged=replace(self.req,claims=(replace(self.claim,
            purpose_ref="M06:attempt-succeeded-claimed-by-caller"),))
        granted=self.grant(forged)
        self.assertEqual(granted.claims[0].purpose_ref,
                         "M06:attempt-succeeded-claimed-by-caller")
        self.assertFalse(hasattr(granted,"m06_issued_attempt_proof"))

    def test_08_lease_has_no_combined_m02_m06_m11_work_action_attestation(self):
        granted=self.grant()
        for field in ("m02_accepted_work_ref","m02_plan_revision",
                      "m06_actual_attempt_ref","m11_request_revision",
                      "m11_intended_action","m11_target_scope",
                      "m09_m11_owner_verified_receipt"):
            self.assertFalse(hasattr(granted,field),field)

    def test_09_mutation_context_binds_actor_auth_idempotency_not_owner_work(self):
        granted=self.grant()
        context=granted.mutation_context
        self.assertEqual(context.actor_ref,granted.actor_ref)
        self.assertEqual(context.authorization_ref,
                         granted.actor_authorization_ref)
        self.assertEqual(context.idempotency_key,granted.idempotency_key)
        self.assertFalse(hasattr(context,"m02_plan_revision"))
        self.assertFalse(hasattr(context,"m06_actual_attempt_ref"))

    def test_10_renewal_updates_lease_epoch_without_adding_m02_or_m06_evidence(self):
        prior=self.grant()
        current=self.renewal(prior)
        self.assertNotEqual(prior.epoch,current.epoch)
        self.assertEqual(prior.request_digest,current.request_digest)
        self.assertFalse(hasattr(current,"m06_actual_attempt_ref"))
        self.assertFalse(hasattr(current,"m02_plan_revision"))

    def test_11_stale_original_epoch_is_rejected_for_second_renewal(self):
        old=self.grant()
        self.renewal(old)
        with self.assertRaisesRegex(ValueError,"stale lease epoch"):
            self.renewal(old,now_ms=1_300)

    def test_12_renewal_does_not_mutate_captured_old_lease_copy(self):
        old=self.grant()
        current=self.renewal(old)
        self.assertEqual(old.state,LeaseState.ACTIVE)
        self.assertNotEqual(old.epoch,current.epoch)
        self.assertEqual(self.book.active(),(current,))

    def test_13_revocation_updates_lease_epoch_without_cross_owner_fence(self):
        old=self.grant()
        latest=self.revoke(old)
        self.assertEqual(latest.state,LeaseState.REVOCATION_REQUESTED)
        self.assertNotEqual(old.epoch,latest.epoch)
        self.assertEqual(old.owner_ref,latest.owner_ref)
        self.assertFalse(hasattr(latest,"m11_action_time_fence"))

    def test_14_captured_prior_active_lease_remains_after_revocation(self):
        old=self.grant()
        captured=self.book.active()[0]
        latest=self.revoke(old)
        self.assertEqual(captured.state,LeaseState.ACTIVE)
        self.assertEqual(captured.epoch,old.epoch)
        self.assertEqual(self.book.active(),(latest,))

    def test_15_stale_pre_renewal_epoch_cannot_release_current_lease(self):
        old=self.grant()
        current=self.renewal(old)
        with self.assertRaisesRegex(ValueError,"stale epoch"):
            self.book.release(old.lease_id,now_ms=1_300,
                expected_epoch=old.epoch,
                causal_ref="M09:synthetic-causal-release")
        self.assertEqual(self.book.active(),(current,))

    def test_16_exact_current_epoch_release_tombstones_the_lease(self):
        old=self.grant()
        receipt=self.book.release(old.lease_id,now_ms=1_300,
            expected_epoch=old.epoch,causal_ref="M09:synthetic-causal-release")
        self.assertEqual(receipt.terminal_state,LeaseState.RELEASED)
        self.assertEqual(self.book.active(),())

    def test_17_replay_identical_release_causal_ref_is_book_local_idempotent(self):
        old=self.grant()
        a=self.book.release(old.lease_id,now_ms=1_300,
            expected_epoch=old.epoch,causal_ref="M09:synthetic-causal-release")
        b=self.book.release(old.lease_id,now_ms=1_300,
            expected_epoch=old.epoch,causal_ref="M09:synthetic-causal-release")
        self.assertEqual(a,b)
        # Matching causal text is no proof of M11's OS side effect.

    def test_18_different_causal_release_after_tombstone_is_rejected(self):
        old=self.grant()
        self.book.release(old.lease_id,now_ms=1_300,
            expected_epoch=old.epoch,causal_ref="M09:synthetic-causal-release")
        with self.assertRaisesRegex(ValueError,"cannot be released twice"):
            self.book.release(old.lease_id,now_ms=1_301,
                expected_epoch=old.epoch,
                causal_ref="M09:other-claimed-causal-release")


if __name__=="__main__":
    unittest.main()
