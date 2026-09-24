from __future__ import annotations

import unittest

from iris_resource_twin import (
    CleanupEligibility,
    Confidence,
    CommitmentState,
    CooperativeReleaseRequest,
    CooperativeReleaseResponse,
    DebtResolutionEvidence,
    EvidenceOrigin,
    IncidentCapsule,
    MutationActorKind,
    MutationContext,
    LeakCandidate,
    LeakTrendEvidence,
    OwnerLivenessRef,
    PostRecoveryGate,
    PressureGovernor,
    PressureLevel,
    PressureObservation,
    PressureUnit,
    RecoveryAction,
    RecoveryActionLedger,
    RecoveryOutcomeState,
    RecoveryReferenceState,
    RecoveryBudget,
    ResourceDebt,
    ResourceDebtLedger,
    SafeFailureCapsule,
    StaleCommitmentCandidate,
    StaleCommitmentReaper,
    evaluate_cooperative_release,
    pressure_admission_constraint,
    confirm_leak,
)
from m09_support import make_snapshot


class TestM09Recovery(unittest.TestCase):
    def test_pressure_hysteresis_requires_samples_and_external_pressure_is_protected(self) -> None:
        governor = PressureGovernor(confirmation_count=2, dwell_ms=0, cooldown_ms=0)
        first = PressureObservation("p1", "resource-1", Confidence.OBSERVED, 9_800, 1_000, "telemetry-1", False, 98, PressureUnit.PERCENT, "scope:resource-1", 5_000)
        second = PressureObservation("p2", "resource-1", Confidence.OBSERVED, 9_900, 2_000, "telemetry-2", False, 9_900, PressureUnit.BASIS_POINTS, "scope:resource-1", 5_000)
        self.assertIsNone(governor.observe(first, now_ms=1_000))
        transition = governor.observe(second, now_ms=2_000)
        self.assertEqual(transition.current, PressureLevel.CRITICAL)
        self.assertEqual(len(transition.observation_ids), 2)
        external1 = PressureObservation("external-1", "resource-2", Confidence.OBSERVED, 9_900, 1_000, "external-source", True, 9_900, PressureUnit.BASIS_POINTS, "scope:resource-2", 5_000)
        external2 = PressureObservation("external-2", "resource-2", Confidence.OBSERVED, 9_900, 2_000, "external-source-2", True, 9_900, PressureUnit.BASIS_POINTS, "scope:resource-2", 5_000)
        governor.observe(external1, now_ms=1_000)
        external_transition = governor.observe(external2, now_ms=2_000)
        self.assertEqual(external_transition.current, PressureLevel.CRITICAL)
        self.assertTrue(external_transition.external_pressure)
        constraint = pressure_admission_constraint(external2, now_ms=2_000)
        self.assertTrue(constraint.deny_new_commitments)
        self.assertFalse(constraint.capacity_reclaimed)
        unknown = PressureObservation("unknown", "resource-3", Confidence.UNKNOWN, None, 3_000, "unknown-source", False, None, PressureUnit.UNKNOWN, "scope:resource-3", 5_000)
        self.assertIsNone(governor.observe(unknown, now_ms=3_000))
        self.assertEqual(governor.state("resource-3"), PressureLevel.UNKNOWN)

    def test_leak_suspicion_is_not_confirmation_without_fresh_truth_liveness_and_distinct_proofs(self) -> None:
        snapshot = make_snapshot()
        candidate = LeakCandidate(
            "leak-1", snapshot.identity.stable_key, "lease-1", "owner-1",
            100, 500, ("observation-1", "observation-2"), 1_000,
        )
        alive = OwnerLivenessRef("owner-1", "ALIVE", "M11:worker-lifecycle", 1_500, "owner-alive")
        dead_other = OwnerLivenessRef("owner-other", "TERMINATED", "M11:worker-lifecycle", 1_500, "owner-dead")
        dead = OwnerLivenessRef("owner-1", "TERMINATED", "M11:worker-lifecycle", 1_500, "owner-terminated")
        self.assertFalse(confirm_leak(candidate, alive, fresh_snapshot=snapshot, now_ms=2_000, minimum_excess_bytes=100).confirmed)
        self.assertFalse(confirm_leak(candidate, dead_other, fresh_snapshot=snapshot, now_ms=2_000, minimum_excess_bytes=100).confirmed)
        confirmed = confirm_leak(candidate, dead, fresh_snapshot=snapshot, now_ms=2_000, minimum_excess_bytes=100)
        self.assertTrue(confirmed.confirmed)
        self.assertEqual(len(confirmed.evidence_digest), 64)
        insufficient = LeakCandidate("leak-2", snapshot.identity.stable_key, "lease-2", "owner-1", 100, 500, ("one-observation",), 1_000)
        self.assertFalse(confirm_leak(insufficient, dead, fresh_snapshot=snapshot, now_ms=2_000, minimum_excess_bytes=100).confirmed)

    def test_unknown_or_unreferenced_owner_liveness_never_confirms(self) -> None:
        snapshot = make_snapshot()
        candidate = LeakCandidate("leak-3", snapshot.identity.stable_key, "lease-3", "owner-3", 0, 1_000, ("obs-1", "obs-2"), 1_000)
        unknown = OwnerLivenessRef("owner-3", "UNKNOWN", "M09:unknown", 1_500, "unknown-liveness")
        self.assertFalse(confirm_leak(candidate, unknown, fresh_snapshot=snapshot, now_ms=2_000, minimum_excess_bytes=1).confirmed)

    def test_cooperative_release_is_a_request_response_contract(self) -> None:
        request = CooperativeReleaseRequest("release-1", "lease-1", "owner-1", 1_000, 2_000, "pressure-reason")
        response = CooperativeReleaseResponse("release-1", "owner-1", "DEFERRED", 1_500, "owner-response")
        self.assertEqual(request.request_id, response.request_id)
        self.assertEqual(response.response, "DEFERRED")
        self.assertGreater(request.deadline_ms, request.requested_at_ms)

    def test_recovery_attempt_and_churn_budgets_are_finite_and_idempotent(self) -> None:
        budget = RecoveryBudget(max_attempts=2, window_ms=10_000, max_churn_bytes=100, cooldown_ms=500)
        self.assertTrue(budget.consume(action_ref="action-1", at_ms=1_000, churn_bytes=40))
        self.assertTrue(budget.consume(action_ref="action-1", at_ms=1_000, churn_bytes=40))
        self.assertFalse(budget.consume(action_ref="action-1", at_ms=1_001, churn_bytes=40))
        self.assertFalse(budget.consume(action_ref="action-2", at_ms=1_100, churn_bytes=40))
        self.assertTrue(budget.consume(action_ref="action-2", at_ms=1_500, churn_bytes=60))
        self.assertFalse(budget.consume(action_ref="action-3", at_ms=2_000, churn_bytes=1))

    def test_resource_debt_is_explicit_until_fresh_reconciliation(self) -> None:
        snapshot = make_snapshot()
        debt = ResourceDebt("debt-1", snapshot.identity.stable_key, "RESIDENCY_DISCREPANCY", None, ("evidence-1",), 1_000)
        ledger = ResourceDebtLedger()
        ledger.record(debt)
        self.assertEqual(ledger.unresolved(), (debt,))
        resolution = DebtResolutionEvidence(debt.debt_id, debt.resource_key, snapshot.digest, 0, "M07:reconciled-capacity", "provider-confirmed-debt-clear", 1_900)
        cleared = ledger.reconcile(debt.debt_id, snapshot, resolution, now_ms=2_000)
        self.assertEqual(cleared.cleared_by_snapshot_digest, snapshot.digest)
        self.assertEqual(ledger.unresolved(), ())
        self.assertEqual(ledger.reconcile(debt.debt_id, snapshot, resolution, now_ms=2_000), cleared)
        with self.assertRaisesRegex(ValueError, "zero remaining quantity"):
            partial = DebtResolutionEvidence(debt.debt_id, debt.resource_key, snapshot.digest, 1, "M07:still-in-debt", "debt-remains", 1_900)
            ledger.reconcile(debt.debt_id, snapshot, partial, now_ms=2_000)
        with self.assertRaisesRegex(ValueError, "cannot self-certify"):
            DebtResolutionEvidence(debt.debt_id, debt.resource_key, snapshot.digest, 0, "M09:self-certification", "bad-debt-clear", 1_900)

    def test_cleanup_never_authorizes_delete_and_post_recovery_requires_new_fresh_truth(self) -> None:
        with self.assertRaisesRegex(ValueError, "physical deletion"):
            CleanupEligibility("resource-1", True, True, "no longer needed", ("evidence-1",), "artifact:1", "transfer:1", "lease:1", "residency:1", RecoveryReferenceState.RELEASED, RecoveryReferenceState.RELEASED)
        safe = CleanupEligibility("resource-1", True, False, "causal transfer and references released", ("lease-tombstone",), "artifact:1", "transfer:1", "lease:1", "residency:1", RecoveryReferenceState.RELEASED, RecoveryReferenceState.RELEASED)
        self.assertFalse(safe.physical_deletion_permitted)
        with self.assertRaisesRegex(ValueError, "active or unknown"):
            CleanupEligibility("resource-1", True, False, "unsafe", ("lease-active",), "artifact:1", "transfer:1", "lease:1", "residency:1", RecoveryReferenceState.ACTIVE, RecoveryReferenceState.UNKNOWN)
        prior = make_snapshot(snapshot_id="before")
        refreshed = make_snapshot(snapshot_id="after", observed_at_ms=2_000)
        same_time = make_snapshot(snapshot_id="same-time", observed_at_ms=prior.observed_at_ms)
        self.assertTrue(PostRecoveryGate.verify(prior_snapshot=prior, current_snapshot=refreshed, now_ms=2_500))
        self.assertFalse(PostRecoveryGate.verify(prior_snapshot=prior, current_snapshot=same_time, now_ms=2_500))
        synthetic_refreshed = make_snapshot(snapshot_id="synthetic-after", observed_at_ms=2_000, evidence_origin=EvidenceOrigin.SYNTHETIC_FIXTURE)
        self.assertFalse(PostRecoveryGate.verify(prior_snapshot=prior, current_snapshot=synthetic_refreshed, now_ms=2_500))

    def test_incident_capsule_has_deterministic_evidence_identity(self) -> None:
        value = IncidentCapsule(
            "incident-1", "resource-1", ("pressure-a", "pressure-b"),
            (RecoveryAction.EMIT_PRESSURE_EVIDENCE, RecoveryAction.REQUEST_FRESH_RECONCILIATION),
            ("snapshot-ref", "lease-ref"), 2_000, "",
        )
        repeated = IncidentCapsule(
            "incident-1", "resource-1", ("pressure-a", "pressure-b"),
            (RecoveryAction.EMIT_PRESSURE_EVIDENCE, RecoveryAction.REQUEST_FRESH_RECONCILIATION),
            ("snapshot-ref", "lease-ref"), 2_000, "",
        )
        self.assertEqual(value.digest, repeated.digest)
        self.assertEqual(len(value.digest), 64)

    def test_pressure_cooldown_raw_unit_provenance_and_stale_telemetry(self) -> None:
        governor = PressureGovernor(confirmation_count=1, dwell_ms=0, cooldown_ms=500)
        elevated = PressureObservation("cooldown-high", "gpu-pressure", Confidence.OBSERVED, 9_000, 1_000, "telemetry:provider", False, 90, PressureUnit.PERCENT, "scope:gpu", 4_000)
        transition = governor.observe(elevated, now_ms=1_000)
        self.assertEqual(transition.current, PressureLevel.ELEVATED)
        self.assertEqual(elevated.source_value, 90)
        self.assertEqual(elevated.source_unit, PressureUnit.PERCENT)
        critical = PressureObservation("cooldown-critical", "gpu-pressure", Confidence.OBSERVED, 9_800, 1_100, "telemetry:provider", False, 9_800, PressureUnit.BASIS_POINTS, "scope:gpu", 4_000)
        self.assertIsNone(governor.observe(critical, now_ms=1_100))
        critical_later = PressureObservation("cooldown-critical-later", "gpu-pressure", Confidence.OBSERVED, 9_800, 1_500, "telemetry:provider", False, 9_800, PressureUnit.BASIS_POINTS, "scope:gpu", 4_000)
        self.assertEqual(governor.observe(critical_later, now_ms=1_500).current, PressureLevel.CRITICAL)
        expired = PressureObservation("expired-pressure", "gpu-pressure", Confidence.OBSERVED, 9_900, 1_600, "telemetry:provider", False, 9_900, PressureUnit.BASIS_POINTS, "scope:gpu", 1_600)
        self.assertIsNone(governor.observe(expired, now_ms=1_601))
        self.assertEqual(governor.state("gpu-pressure"), PressureLevel.UNKNOWN)
        with self.assertRaisesRegex(ValueError, "preserve the exact original"):
            PressureObservation("bad-normalization", "gpu-pressure", Confidence.OBSERVED, 9_100, 1_000, "telemetry:provider", False, 90, PressureUnit.PERCENT, "scope:gpu", 2_000)

    def test_stale_commitment_reconciliation_is_idempotent_and_never_frees_bytes(self) -> None:
        candidate = StaleCommitmentCandidate("stale-1", "resource-1", "lease-1", "owner-1", CommitmentState.EXPIRED, 4_096, 1_000, ("lease-expiry", "accounting-gap"))
        owner = OwnerLivenessRef("owner-1", "TERMINATED", "M11:worker-lifecycle", 1_500, "owner-terminated")
        reaper = StaleCommitmentReaper()
        receipt = reaper.reconcile(candidate, owner, now_ms=2_000)
        self.assertEqual(receipt.status, "RECONCILIATION_RECORDED_PENDING_FRESH_RESOURCE_TRUTH")
        self.assertEqual(receipt.freed_bytes, None)
        self.assertFalse(receipt.capacity_reclaimed)
        self.assertEqual(reaper.reconcile(candidate, owner, now_ms=2_100), receipt)
        active = StaleCommitmentCandidate("stale-active", "resource-1", "lease-active", "owner-1", CommitmentState.ACTIVE, 1, 1_000, ("lease-active",))
        with self.assertRaisesRegex(ValueError, "cannot be reaped"):
            reaper.reconcile(active, owner, now_ms=2_000)

    def test_cooperative_release_timeout_and_acceptance_both_require_resource_reconciliation(self) -> None:
        request = CooperativeReleaseRequest("release-timeout", "lease-1", "owner-1", 1_000, 2_000, "pressure-reason")
        timeout = evaluate_cooperative_release(request, None, now_ms=2_100)
        self.assertEqual(timeout.status, "TIMED_OUT")
        self.assertFalse(timeout.capacity_reclaimed)
        accepted_response = CooperativeReleaseResponse("release-timeout", "owner-1", "ACCEPTED", 1_500, "owner-accepted")
        accepted = evaluate_cooperative_release(request, accepted_response, now_ms=1_600)
        self.assertEqual(accepted.status, "ACCEPTED_AWAITING_RESOURCE_RECONCILIATION")
        self.assertFalse(accepted.capacity_reclaimed)
        late_response = CooperativeReleaseResponse("release-timeout", "owner-1", "ACCEPTED", 2_001, "owner-late")
        self.assertEqual(evaluate_cooperative_release(request, late_response, now_ms=2_100).status, "TIMED_OUT")

    def test_recovery_action_lifecycle_preserves_failed_attempt_then_requires_fresh_truth(self) -> None:
        resource = make_snapshot().identity.stable_key
        ledger = RecoveryActionLedger(max_attempts_per_action=2)
        context = MutationContext(
            MutationActorKind.AUTOMATION, "agent:recovery-controller", "M57:recovery-auth",
            "incident-pressure", "recovery-idem-1", "workflow:recovery-controller",
        )
        requested = ledger.request(action_id="recovery-1", idempotency_key="recovery-idem-1", resource_key=resource, action=RecoveryAction.REQUEST_FRESH_RECONCILIATION, now_ms=1_000, evidence_refs=("incident-pressure",), mutation_context=context)
        self.assertEqual(ledger.request(action_id="recovery-1", idempotency_key="recovery-idem-1", resource_key=resource, action=RecoveryAction.REQUEST_FRESH_RECONCILIATION, now_ms=1_000, evidence_refs=("incident-pressure",), mutation_context=context), requested)
        self.assertEqual(requested.mutation_context, context)
        attempted = ledger.mark_attempted(requested.action_id, evidence_ref="attempt-1", now_ms=1_100)
        self.assertEqual(attempted.state, RecoveryOutcomeState.ATTEMPTED)
        self.assertEqual(attempted.mutation_context, context)
        failed = ledger.complete(attempted.action_id, state=RecoveryOutcomeState.FAILED, evidence_ref="reconcile-failed", now_ms=1_200)
        self.assertEqual(failed.state, RecoveryOutcomeState.FAILED)
        retried = ledger.mark_attempted(failed.action_id, evidence_ref="attempt-2", now_ms=1_300)
        self.assertEqual(retried.attempt_count, 2)
        with self.assertRaisesRegex(ValueError, "fresh reported snapshot"):
            ledger.complete(retried.action_id, state=RecoveryOutcomeState.VERIFIED, evidence_ref="synthetic-success", now_ms=2_100, snapshot=make_snapshot(snapshot_id="synthetic", observed_at_ms=2_000, evidence_origin=EvidenceOrigin.SYNTHETIC_FIXTURE))
        verified = ledger.complete(retried.action_id, state=RecoveryOutcomeState.VERIFIED, evidence_ref="reconciled", now_ms=2_100, snapshot=make_snapshot(snapshot_id="reconciled", observed_at_ms=2_000))
        self.assertEqual(verified.state, RecoveryOutcomeState.VERIFIED)
        self.assertEqual(ledger.history()[2].state, RecoveryOutcomeState.FAILED)
        self.assertFalse(verified.capacity_reclaimed)

    def test_safe_failure_and_leak_trend_are_deterministic_evidence_only_records(self) -> None:
        snapshot = make_snapshot(confidence=Confidence.UNKNOWN, capacity=make_snapshot().capacity)
        failure = SafeFailureCapsule("incident-safe-failure", snapshot.identity.stable_key, "reason:unknown-capacity", snapshot.digest, Confidence.UNKNOWN, ("snapshot-evidence",), ("action-failed",), 2_000)
        self.assertEqual(len(failure.digest), 64)
        self.assertFalse(failure.capacity_reclaimed)
        trend = LeakTrendEvidence(snapshot.identity.stable_key, 1_000, 2_000, ("sample-1", "sample-2"), 1, True)
        self.assertTrue(trend.synthetic_fixture)
        self.assertEqual(len(trend.evidence_digest), 64)

    def test_recovery_budget_rejects_non_monotonic_time_and_cooldown_churn(self) -> None:
        budget = RecoveryBudget(max_attempts=3, window_ms=10_000, max_churn_bytes=100, cooldown_ms=500)
        self.assertTrue(budget.consume(action_ref="budget-a", at_ms=1_000, churn_bytes=10))
        self.assertFalse(budget.consume(action_ref="budget-b", at_ms=1_499, churn_bytes=10))
        self.assertFalse(budget.consume(action_ref="budget-c", at_ms=999, churn_bytes=10))
        self.assertTrue(budget.consume(action_ref="budget-b", at_ms=1_500, churn_bytes=10))


if __name__ == "__main__":
    unittest.main()
