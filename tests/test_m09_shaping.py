from __future__ import annotations

import unittest
from dataclasses import replace

from iris_resource_twin import (
    AdaptationBudget,
    BatchIsolationContract,
    BatchItemSemantics,
    BoundedShapeSet,
    ControlFeedbackState,
    Precision,
    PrecisionCompatibility,
    PrecisionCompatibilityClass,
    ProviderControlFeedback,
    MutationActorKind,
    MutationContext,
    ProviderCapabilityAdapter,
    ProviderAxisCapability,
    QualityConstraintRef,
    ReversibilityClass,
    ReversibilityDescriptor,
    ReplanSignal,
    SeamPolicy,
    Shape,
    ShapeEnvelope,
    ShapeTransitionLedger,
    SpatialTileContract,
    TemporalChunkContract,
    TemporalUnit,
    SpatialUnit,
    evaluate_shape_set,
    evaluate_shape,
    content_digest,
)
from m09_support import make_provider, make_snapshot


def envelope(max_bytes: int | None = 4 * 1024**2) -> ShapeEnvelope:
    snapshot = make_snapshot()
    return ShapeEnvelope(max_bytes, 32, 32, 1, 4, (Precision.FP32, Precision.BF16, Precision.FP16), "envelope-1", "M08:capability-evidence", snapshot.digest, 1)


def shape(*, precision: Precision = Precision.FP32, tile_width: int = 64, tile_height: int = 64, temporal_chunk: int = 2, batch_size: int = 1, halo: int = 0) -> Shape:
    batch = BatchIsolationContract("batch-contract", tuple(
        BatchItemSemantics(f"item-{index}", content_digest({"item": index}), f"seed:item-{index}", f"acceptance:item-{index}")
        for index in range(batch_size)
    ))
    spatial = SpatialTileContract("spatial-contract", SpatialUnit.PIXEL, max(halo, 8), max(halo, 8), SeamPolicy.DOMAIN_VALIDATED, "spatial-context", "M03:seam-evidence")
    temporal = TemporalChunkContract("temporal-contract", TemporalUnit.FRAME, 0, 0, "continuity:source", "state-context:source")
    return Shape(tile_width, tile_height, temporal_chunk, batch_size, precision, 4, halo, True, "operation:fixture", "context:fixture", spatial, temporal, batch)


def evaluate(shape_value: Shape, *, envelope_value: ShapeEnvelope | None = None, quality: QualityConstraintRef | None = None, current_epoch: int = 1, expected_epoch: int = 1, snapshot=None, precision_compatibility=None, now_ms: int = 1_500):
    exact_snapshot = snapshot or make_snapshot()
    return evaluate_shape(
        shape_value, envelope_value or envelope(), make_provider(), quality=quality,
        current_epoch=current_epoch, expected_epoch=expected_epoch,
        current_snapshot=exact_snapshot, current_resource_epoch=1, now_ms=now_ms,
        precision_compatibility=precision_compatibility,
    )


class TestM09Shaping(unittest.TestCase):
    def test_finite_shape_estimate_and_provider_neutral_mapping(self) -> None:
        provider = make_provider()
        current = shape()
        evaluation = evaluate(current, current_epoch=2, expected_epoch=2)
        self.assertEqual(evaluation.signal, ReplanSignal.FIT)
        self.assertGreater(evaluation.estimated_bytes, 0)
        self.assertEqual(dict(evaluation.provider_payload)["precision"], "f32")
        self.assertEqual(ProviderCapabilityAdapter(provider).map(current), evaluation.provider_payload)

    def test_quality_sensitive_precision_needs_authority_and_explicit_consent(self) -> None:
        lower_precision = shape(precision=Precision.FP16)
        compatibility = PrecisionCompatibility(
            "operation:fixture", "context:fixture", Precision.FP32, Precision.FP16,
            PrecisionCompatibilityClass.QUALITY_SENSITIVE, "M01:precision-matrix", "M01:precision-evidence",
        )
        no_authority = evaluate(lower_precision, precision_compatibility=compatibility)
        self.assertEqual(no_authority.signal, ReplanSignal.QUALITY_AUTH_REQUIRED)
        constraint = QualityConstraintRef("M01:quality-profile", "quality-minimum", Precision.FP32, operation_ref="operation:fixture", context_ref="context:fixture")
        denied = evaluate(lower_precision, quality=constraint, precision_compatibility=compatibility)
        self.assertEqual(denied.signal, ReplanSignal.QUALITY_AUTH_REQUIRED)
        consented = QualityConstraintRef(
            "M01:quality-profile", "quality-minimum", Precision.FP32, True,
            "M01:scoped-consent", None, "operation:fixture", "context:fixture",
            content_digest(lower_precision), 2_000,
        )
        allowed = evaluate(lower_precision, quality=consented, precision_compatibility=compatibility)
        self.assertEqual(allowed.signal, ReplanSignal.FIT)
        self.assertEqual(allowed.quality_authorization_ref, "M01:scoped-consent")

    def test_m03_protected_semantics_reference_is_mandatory(self) -> None:
        with self.assertRaisesRegex(ValueError, "protected-semantics"):
            QualityConstraintRef("M03:constraint", "shape-preservation", Precision.FP32, operation_ref="operation:fixture", context_ref="context:fixture")
        protected = QualityConstraintRef("M03:constraint", "shape-preservation", Precision.FP32, protected_semantics_ref="M03:semantic-ref", operation_ref="operation:fixture", context_ref="context:fixture")
        self.assertEqual(protected.protected_semantics_ref, "M03:semantic-ref")

    def test_structural_minima_batch_isolation_and_overflow_fail_closed(self) -> None:
        too_small = evaluate(shape(tile_width=16))
        self.assertEqual(too_small.signal, ReplanSignal.NO_FIT)
        unisolated = Shape(64, 64, 2, 2, Precision.FP32, isolated_batch_items=False)
        self.assertEqual(evaluate(unisolated).signal, ReplanSignal.NO_FIT)
        huge = Shape(1_000_000, 1_000_000, 1_000_000, 1_000_000, Precision.FP32)
        overflow = evaluate(huge)
        self.assertEqual(overflow.signal, ReplanSignal.NO_FIT)
        self.assertIsNone(overflow.estimated_bytes)

    def test_unknown_capacity_epoch_mismatch_and_offload_outcome_are_explicit(self) -> None:
        self.assertEqual(evaluate(shape(), envelope_value=envelope(None)).signal, ReplanSignal.UNKNOWN)
        self.assertEqual(evaluate(shape(), current_epoch=2, expected_epoch=1).signal, ReplanSignal.REQUIRE_REPLAN)
        small = evaluate(shape(), envelope_value=envelope(1))
        self.assertEqual(small.signal, ReplanSignal.REQUIRE_OFFLOAD)

    def test_provider_map_refuses_unrepresentable_axes(self) -> None:
        provider = make_provider()
        no_temporal = type(provider)(provider.adapter_ref, provider.supported_precisions, provider.precision_tokens, provider.max_batch_size, True, False, provider.reversible_controls)
        result = evaluate_shape(
            shape(), envelope(), no_temporal, quality=None, current_epoch=1, expected_epoch=1,
            current_snapshot=make_snapshot(), current_resource_epoch=1, now_ms=1_500,
        )
        self.assertEqual(result.signal, ReplanSignal.REQUIRE_REPLAN)

    def test_adaptation_budget_hysteresis_and_magnitude_are_bounded(self) -> None:
        budget = AdaptationBudget(max_changes=2, window_ms=1_000, minimum_dwell_ms=100, max_magnitude=2)
        self.assertTrue(budget.allow(now_ms=100, magnitude=1))
        self.assertFalse(budget.allow(now_ms=150, magnitude=1))
        self.assertTrue(budget.allow(now_ms=200, magnitude=2))
        self.assertFalse(budget.allow(now_ms=400, magnitude=1))
        self.assertFalse(budget.allow(now_ms=1_500, magnitude=3))

    def test_stale_snapshot_epoch_conflict_and_synthetic_evidence_fail_closed_or_stay_synthetic(self) -> None:
        snapshot = make_snapshot(snapshot_id="fresh-shaping")
        bound = ShapeEnvelope(4 * 1024**2, 32, 32, 1, 4, (Precision.FP32,), "bound-envelope", "M08:bound", snapshot.digest, 3)
        self.assertEqual(evaluate_shape(shape(), bound, make_provider(), quality=None, current_epoch=1, expected_epoch=1, current_snapshot=snapshot, current_resource_epoch=2, now_ms=1_500).signal, ReplanSignal.REQUIRE_REPLAN)
        self.assertEqual(evaluate(shape(), snapshot=make_snapshot(confidence=__import__("iris_resource_twin").Confidence.CONFLICTED)).signal, ReplanSignal.REQUIRE_REPLAN)
        synthetic = make_snapshot(evidence_origin=__import__("iris_resource_twin").EvidenceOrigin.SYNTHETIC_FIXTURE)
        synthetic_envelope = ShapeEnvelope(4 * 1024**2, 32, 32, 1, 4, (Precision.FP32,), "synthetic-envelope", "M08:synthetic-fixture", synthetic.digest, 1)
        synthetic_result = evaluate_shape(shape(), synthetic_envelope, make_provider(), quality=None, current_epoch=1, expected_epoch=1, current_snapshot=synthetic, current_resource_epoch=1, now_ms=1_500)
        self.assertEqual(synthetic_result.signal, ReplanSignal.FIT)
        self.assertTrue(synthetic_result.synthetic_only)

    def test_spatial_temporal_and_batch_contracts_are_required_and_conservative(self) -> None:
        candidate = shape()
        missing_spatial = Shape(candidate.tile_width, candidate.tile_height, candidate.temporal_chunk, candidate.batch_size, candidate.precision, spatial_contract=None, temporal_contract=candidate.temporal_contract, batch_contract=candidate.batch_contract)
        self.assertEqual(evaluate(missing_spatial).signal, ReplanSignal.NO_FIT)
        inadequate_temporal = TemporalChunkContract("bad-time", TemporalUnit.FRAME, 1, 1, "continuity:source", "state-context:source")
        bad_chunk = Shape(candidate.tile_width, candidate.tile_height, 2, candidate.batch_size, candidate.precision, spatial_contract=candidate.spatial_contract, temporal_contract=inadequate_temporal, batch_contract=candidate.batch_contract)
        self.assertEqual(evaluate(bad_chunk).signal, ReplanSignal.NO_FIT)
        duplicate_item = BatchItemSemantics("duplicate", content_digest({"item": 1}), "seed:one", "acceptance:one")
        with self.assertRaisesRegex(ValueError, "duplicate item identity"):
            BatchIsolationContract("batch-duplicate", (duplicate_item, duplicate_item))

    def test_provider_quantization_is_visible_and_never_applied_implicitly(self) -> None:
        candidate = shape(tile_width=65)
        quantized = type(make_provider())(
            "quantizing-provider", (Precision.FP32,), ((Precision.FP32, "f32"),), 4, True, True, ("tile",),
            (
                ProviderAxisCapability("batch_size", 1, 4, 1, "ITEM"),
                ProviderAxisCapability("temporal_chunk", 1, 100, 1, "FRAME"),
                ProviderAxisCapability("tile_height", 32, 256, 32, "PIXEL"),
                ProviderAxisCapability("tile_width", 32, 256, 32, "PIXEL"),
            ),
        )
        negotiation = ProviderCapabilityAdapter(quantized).negotiate(candidate)
        self.assertFalse(negotiation.exact)
        self.assertIn(("tile_width", 65), negotiation.requested_values)
        self.assertIn(("tile_width", 64), negotiation.provider_values)
        self.assertIsNone(ProviderCapabilityAdapter(quantized).map(candidate))

    def test_shape_transition_requires_verified_feedback_and_scoped_materiality(self) -> None:
        initial = shape()
        target = replace(shape(tile_width=96), materiality_ref="M06:materiality")
        snapshot = make_snapshot()
        evaluation = evaluate(target, snapshot=snapshot)
        negotiation = ProviderCapabilityAdapter(make_provider()).negotiate(target)
        ledger = ShapeTransitionLedger(resource_key=snapshot.identity.stable_key, initial_shape=initial, initial_epoch=2)
        mutation_context = MutationContext(
            MutationActorKind.AUTOMATION, "agent:shape-controller", "M10:control-choice",
            "M09:pressure-cause", "shape-idem-1", "workflow:shape-controller",
        )
        transition = ledger.request(
            transition_id="shape-transition-1", idempotency_key="shape-idem-1", expected_epoch=2,
            expected_resource_epoch=1, shape=target, negotiation=negotiation, evaluation=evaluation,
            authorization_ref="M10:control-choice",
            causal_evidence_refs=("M09:pressure-cause",),
            reversibility=ReversibilityDescriptor(ReversibilityClass.MATERIAL, "M06:reproducibility", "M06:materiality"),
            now_ms=1_500,
            mutation_context=mutation_context,
        )
        self.assertEqual(transition.state, ControlFeedbackState.REQUESTED)
        self.assertEqual(transition.mutation_context, mutation_context)
        self.assertEqual(ledger.current(), (initial, 2))
        applied = ProviderControlFeedback(snapshot.identity.stable_key, 3, negotiation.shape_digest, ControlFeedbackState.APPLIED, negotiation.payload, negotiation.payload, "provider:applied", 1_600)
        applied_event = ledger.record_feedback(transition.transition_id, applied)
        self.assertEqual(ledger.current(), (initial, 2))
        self.assertIs(ledger.record_feedback(transition.transition_id, applied), applied_event)
        self.assertEqual(len(ledger.history()), 2)
        with self.assertRaisesRegex(ValueError, "stale or non-monotonic"):
            ledger.record_feedback(transition.transition_id, ProviderControlFeedback(
                snapshot.identity.stable_key, 3, negotiation.shape_digest, ControlFeedbackState.UNKNOWN,
                negotiation.payload, None, "provider:stale", 1_550,
            ))
        verified = ProviderControlFeedback(snapshot.identity.stable_key, 3, negotiation.shape_digest, ControlFeedbackState.VERIFIED, negotiation.payload, negotiation.payload, "provider:verified", 1_700)
        ledger.record_feedback(transition.transition_id, verified)
        self.assertEqual(ledger.current(), (target, 3))
        self.assertEqual(tuple(item.state for item in ledger.history()), (
            ControlFeedbackState.REQUESTED, ControlFeedbackState.APPLIED, ControlFeedbackState.VERIFIED,
        ))
        self.assertTrue(all(item.mutation_context == mutation_context for item in ledger.history()))
        self.assertEqual(ledger.request(
            transition_id="shape-transition-1", idempotency_key="shape-idem-1", expected_epoch=2,
            expected_resource_epoch=1, shape=target, negotiation=negotiation, evaluation=evaluation,
            authorization_ref="M10:control-choice", causal_evidence_refs=("M09:pressure-cause",),
            reversibility=ReversibilityDescriptor(ReversibilityClass.MATERIAL, "M06:reproducibility", "M06:materiality"),
            now_ms=1_800,
            mutation_context=mutation_context,
        ).state, ControlFeedbackState.VERIFIED)

    def test_shape_transition_rejects_synthetic_or_stale_resource_evaluation(self) -> None:
        target = shape(tile_width=96)
        negotiation = ProviderCapabilityAdapter(make_provider()).negotiate(target)
        snapshot = make_snapshot(evidence_origin=__import__("iris_resource_twin").EvidenceOrigin.SYNTHETIC_FIXTURE)
        synthetic_envelope = ShapeEnvelope(
            4 * 1024**2, 32, 32, 1, 4, (Precision.FP32,), "synthetic-bound",
            "M08:synthetic-fixture", snapshot.digest, 1,
        )
        synthetic_evaluation = evaluate_shape(
            target, synthetic_envelope, make_provider(), quality=None, current_epoch=1,
            expected_epoch=1, current_snapshot=snapshot, current_resource_epoch=1, now_ms=1_500,
        )
        ledger = ShapeTransitionLedger(resource_key=snapshot.identity.stable_key, initial_shape=shape(), initial_epoch=1)
        with self.assertRaisesRegex(ValueError, "exact production FIT"):
            ledger.request(
                transition_id="synthetic-transition", idempotency_key="synthetic-transition-idem",
                expected_epoch=1, expected_resource_epoch=1, shape=target, negotiation=negotiation,
                evaluation=synthetic_evaluation, authorization_ref="M10:control-choice",
                causal_evidence_refs=("M09:pressure-cause",),
                reversibility=ReversibilityDescriptor(ReversibilityClass.REVERSIBLE, "M06:reversible"),
                now_ms=1_500,
            )

    def test_finite_shape_set_evaluates_bounded_candidates_without_selecting_a_plan(self) -> None:
        candidates = BoundedShapeSet((shape(tile_width=64), shape(tile_width=96)), maximum_candidates=2)
        result = evaluate_shape_set(candidates, envelope(), make_provider(), quality=None, current_epoch=1, expected_epoch=1, current_snapshot=make_snapshot(), current_resource_epoch=1, now_ms=1_500)
        self.assertEqual(result.steps, 2)
        self.assertFalse(result.truncated)
        self.assertEqual(tuple(item.signal for item in result.evaluations), (ReplanSignal.FIT, ReplanSignal.FIT))


if __name__ == "__main__":
    unittest.main()
