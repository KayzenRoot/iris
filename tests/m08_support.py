"""Shared deterministic, synthetic-only construction helpers for M08 tests."""

from __future__ import annotations

from iris_microbenchmark import (
    AbortEvidence, Aggregation, AuthorizationState,
    BenchmarkAuthorizationReceipt, BenchmarkClass, CapabilityDimensionEvidence,
    CapabilityRegion, CorrectnessEvidence, CorrectnessState, DerivationMethod, Directionality, Domain,
    EvidenceOrigin, EvidencePurposeDescriptor, FixtureKind, FixtureManifest,
    InterferenceEvidence, InterferenceState, M07ProvenanceBinding, MeasurementSample,
    MetricSemantics, PrivacyClass, ProbeDefinition, ProtocolDescriptor, ResultState,
    SafetyBudget, SustainabilityClass, TimingSource, BackendAdapterCapsule, QuantityKind,
    content_digest, admit_protocol, create_result, derive_envelope,
)


def purpose() -> EvidencePurposeDescriptor:
    return EvidencePurposeDescriptor(
        "m08-test-purpose", "1.0.0",
        ("hardware-capability-fingerprint", "microbenchmark-acceptance-evidence", "provenance-export", "consumer-test", "consumer:consumer-test", "consumer:public-report"),
        ("release-acceptance", "model-fitness", "creative-quality"),
    )


def binding(*, subject_id: str = "cpu-subject-01", runtime_id: str = "runtime-01", backend_id: str = "cpu-reference", backend_version: str = "1.0.0", projection: bool = False) -> M07ProvenanceBinding:
    identity = {"subject": subject_id, "runtime": runtime_id, "backend": backend_id, "version": backend_version}
    return M07ProvenanceBinding(
        None if projection else "genome-synthetic-01",
        subject_id,
        runtime_id,
        backend_id,
        backend_version,
        (("driver", "1.0.0"), ("runtime-api", "1.0.0")),
        ("m07-capability-cpu",),
        content_digest(identity),
        "m07-projection-test" if projection else None,
        content_digest(identity) if projection else None,
        True,
    )


def metric(*, metric_id: str = "latency", timing_source: TimingSource = TimingSource.MONOTONIC_HOST, minimum_samples: int = 2, uncertainty_required: bool = True) -> MetricSemantics:
    return MetricSemantics(
        metric_id, "1.0.0", QuantityKind.DURATION, "ms", Directionality.LOWER_IS_BETTER,
        Aggregation.MEAN, "exclude-warmup", minimum_samples, timing_source, uncertainty_required,
    )


def protocol(
    *, protocol_id: str = "cpu-latency-v1", binding_value: M07ProvenanceBinding | None = None,
    purpose_value: EvidencePurposeDescriptor | None = None, metric_value: MetricSemantics | None = None,
    first_run: bool = True, max_wall_ms: int = 5_000, max_iterations: int = 4,
    safety_class: BenchmarkClass = BenchmarkClass.TINY, security_required: bool = False,
    security_reference=None, operation_family: str = "tensor-reduction",
) -> ProtocolDescriptor:
    bound = binding_value or binding()
    selected_purpose = purpose_value or purpose()
    selected_metric = metric_value or metric()
    authorization_id = f"auth-{protocol_id}"
    return ProtocolDescriptor(
        protocol_id, "1.0.0", Domain.SYSTEM, operation_family, safety_class, bound,
        (selected_metric,), SafetyBudget(max_wall_ms, 100, max_iterations, 1_000_000, 1_000_000, 64_000, 1, 0, 1_000, first_run),
        "thermal-threshold", "user-cancel-token", "cooldown-v1", "interference-v1", PrivacyClass.SYNTHETIC,
        "result-schema-v1", (), selected_purpose, authorization_id, security_required,
        security_reference, None,
    )


def authorization(protocol_value: ProtocolDescriptor, *, receipt_id: str | None = None, state: AuthorizationState = AuthorizationState.GRANTED, expires_at_ms: int = 100_000) -> BenchmarkAuthorizationReceipt:
    return BenchmarkAuthorizationReceipt(
        receipt_id or protocol_value.authorization_id, "policy-m08-test", protocol_value.protocol_id,
        protocol_value.version, content_digest(protocol_value), protocol_value.binding.subject_id, protocol_value.binding.runtime_id,
        content_digest(protocol_value.binding), 10, expires_at_ms, state, protocol_value.evidence_purpose.purpose_id,
    )


def measurement_result(
    *, result_id: str = "result-001", protocol_value: ProtocolDescriptor | None = None,
    values: tuple[float, ...] = (1.0, 2.0), state: ResultState = ResultState.VALID,
    interference: InterferenceEvidence | None = None, abort: AbortEvidence | None = None,
    measured_at_ms: int = 30, uncertainty: float | None = 0.1,
    origin: EvidenceOrigin = EvidenceOrigin.SYNTHETIC_SEMANTIC_FIXTURE,
    external_measurement_ref: str | None = None,
):
    selected_protocol = protocol_value or protocol()
    admission = admit_protocol(selected_protocol, authorization(selected_protocol), at_ms=20)
    samples = tuple(MeasurementSample(f"{result_id}-sample-{index}", value, 21 + index, 1_000_000) for index, value in enumerate(values))
    expected = content_digest(("oracle", result_id, selected_protocol.binding.material_context_digest))
    correctness = CorrectnessEvidence(
        "exact-synthetic-oracle", "1.0.0", CorrectnessState.PASS, expected, expected, expected,
        None, 29, None,
    )
    selected_interference = interference or InterferenceEvidence(InterferenceState.WITHIN_TOLERANCE, 0.02, 0.10, "load-observation-01")
    return create_result(
        selected_protocol, admission, selected_protocol.metrics[0], samples,
        result_id=result_id, state=state, correctness=correctness,
        interference=selected_interference, measured_at_ms=measured_at_ms,
        uncertainty=uncertainty, abort=abort, origin=origin,
        external_measurement_ref=external_measurement_ref,
    )


def fixture(fixture_id: str = "fixture-small-tensor") -> FixtureManifest:
    return FixtureManifest(
        fixture_id, content_digest(("fixture", fixture_id)), "deterministic-fixture-gen", "1.0.0",
        FixtureKind.DETERMINISTIC_SYNTHETIC, PrivacyClass.SYNTHETIC, None, "seed-01", 4_096,
    )


def probe(protocol_value: ProtocolDescriptor, fixture_value: FixtureManifest, *, probe_id: str = "probe-cpu") -> ProbeDefinition:
    adapter = BackendAdapterCapsule(
        "cpu-adapter", "1.0.0", protocol_value.binding.backend_id, "1.0.0",
        (protocol_value.operation_family,), ("host-monotonic-timing",),
    )
    return ProbeDefinition(
        probe_id, protocol_value.protocol_id, Domain.SYSTEM, protocol_value.operation_family,
        fixture_value.fixture_id, {"shape": [16]}, {"shape": [16]}, "f32", 1, 2,
        "synchronous-completion", "exact-output-digest", adapter, ("driver", "runtime-api"),
    )


def demonstrated_dimension(result_id: str = "result-001", *, value_min: float = 1.0, value_max: float = 2.0) -> CapabilityDimensionEvidence:
    return CapabilityDimensionEvidence(
        "latency", "ms", CapabilityRegion.DEMONSTRATED,
        DerivationMethod.DIRECT_OBSERVATION, (result_id,), value_min, value_max, None, 0.0,
        Directionality.LOWER_IS_BETTER, SustainabilityClass.BURST, None,
    )


def envelope(result, *, envelope_id: str = "envelope-001", dimension: CapabilityDimensionEvidence | None = None, binding_value=None, purpose_value=None, synthetic_fixture_mode: bool = True):
    selected_binding = binding_value or result.binding
    return derive_envelope(
        (dimension or demonstrated_dimension(result.result_id),), (result,),
        envelope_id=envelope_id, binding=selected_binding, derivation_algorithm="direct-observation-v1",
        derivation_version="1.0.0", evidence_purpose=purpose_value or purpose(),
        created_at_ms=40, synthetic_fixture_mode=synthetic_fixture_mode,
    )
