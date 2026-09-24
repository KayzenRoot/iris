"""Seven deterministic synthetic M08 profiles; no physical benchmark is executed."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iris_microbenchmark import (  # noqa: E402
    AbortEvidence, AbortReason, Aggregation, AuthorizationState, BenchmarkAuthorizationReceipt,
    BenchmarkClass, CorrectnessEvidence, CorrectnessState, Directionality, Domain,
    EvidenceOrigin, EvidencePurposeDescriptor, InterferenceEvidence, InterferenceState,
    M07ProvenanceBinding, MeasurementSample, MetricSemantics, PrivacyClass, ProtocolDescriptor,
    QuantityKind, ResultState, SafetyBudget, TimingSource, content_digest, create_result,
    admit_protocol, canonical_json,
)

PROFILES = (
    ("cpu-only", "cpu-reference", 0, ResultState.VALID, InterferenceState.WITHIN_TOLERANCE, 1),
    ("gpu-8gb-synthetic", "gpu-reference", 8 * 1024**3, ResultState.VALID, InterferenceState.WITHIN_TOLERANCE, 1),
    ("constrained-memory", "gpu-reference", 1024**3, ResultState.VALID, InterferenceState.WITHIN_TOLERANCE, 1),
    ("balanced-compute", "accelerator-reference", 16 * 1024**3, ResultState.VALID, InterferenceState.WITHIN_TOLERANCE, 1),
    ("high-concurrency-declared", "accelerator-reference", 24 * 1024**3, ResultState.VALID, InterferenceState.WITHIN_TOLERANCE, 4),
    ("interference-observed", "cpu-reference", 0, ResultState.INVALID_INTERFERENCE, InterferenceState.CONTAMINATED, 1),
    ("telemetry-unknown", "gpu-reference", 8 * 1024**3, ResultState.PARTIAL, InterferenceState.UNKNOWN_TELEMETRY, 1),
)


def _evidence(profile_id: str, backend_id: str, declared_memory_bytes: int, state: ResultState, interference_state: InterferenceState, max_concurrency: int) -> dict[str, Any]:
    material_context = {"profile": profile_id, "backend": backend_id, "declared_synthetic_memory_bytes": declared_memory_bytes}
    binding = M07ProvenanceBinding(
        f"synthetic-genome-{profile_id}", f"synthetic-subject-{profile_id}",
        f"synthetic-runtime-{profile_id}", backend_id, "1.0.0", (("driver", "synthetic-1.0"),),
        (f"synthetic-capability-{profile_id}",), content_digest(material_context), None, None, True,
    )
    purpose = EvidencePurposeDescriptor(
        "m08-example-purpose", "1.0.0",
        ("hardware-capability-fingerprint", "microbenchmark-acceptance-evidence"),
        ("physical-capacity-claim", "release-acceptance", "model-fitness"),
    )
    metric = MetricSemantics(
        "synthetic-latency", "1.0.0", QuantityKind.DURATION, "ms", Directionality.LOWER_IS_BETTER,
        Aggregation.MEAN, "exclude-warmup", 2, TimingSource.MONOTONIC_HOST, True,
    )
    protocol_id = f"example-protocol-{profile_id}"
    authorization_id = f"example-auth-{profile_id}"
    protocol = ProtocolDescriptor(
        protocol_id, "1.0.0", Domain.SYSTEM, "bounded-reduction", BenchmarkClass.TINY,
        binding, (metric,), SafetyBudget(
            5_000, 100, 2, 1_000_000, 0 if declared_memory_bytes == 0 else 16_000_000,
            64_000, max_concurrency, 0, 1_000, True,
        ), "thermal-abort-condition", "user-cancellation", "cooldown-v1", "interference-v1",
        PrivacyClass.SYNTHETIC, "m08-example-result-v1", (), purpose, authorization_id, False, None, None,
    )
    receipt = BenchmarkAuthorizationReceipt(
        authorization_id, "example-authorization-policy", protocol_id, protocol.version,
        content_digest(protocol), binding.subject_id, binding.runtime_id, content_digest(binding), 10, 1_000,
        AuthorizationState.GRANTED, purpose.purpose_id,
    )
    admission = admit_protocol(protocol, receipt, at_ms=20)
    result_id = f"example-result-{profile_id}"
    samples = (
        MeasurementSample(f"{result_id}-sample-1", 1.0, 21, 1_000_000),
        MeasurementSample(f"{result_id}-sample-2", 1.2, 22, 1_000_000),
    )
    exact_output = content_digest((profile_id, "deterministic-oracle-output"))
    correctness = CorrectnessEvidence(
        "example-exact-oracle", "1.0.0", CorrectnessState.PASS, exact_output,
        exact_output, exact_output, None, 29, None,
    )
    if interference_state is InterferenceState.WITHIN_TOLERANCE:
        interference = InterferenceEvidence(interference_state, 0.01, 0.1, "synthetic-load-observation")
    elif interference_state is InterferenceState.CONTAMINATED:
        interference = InterferenceEvidence(interference_state, 0.5, 0.1, "synthetic-contamination-observation")
    else:
        interference = InterferenceEvidence(interference_state, None, None, None)
    abort = None
    if state is ResultState.INVALID_THERMAL_ABORT:
        abort = AbortEvidence("example-abort", AbortReason.THERMAL_LIMIT, 25, "sample-1", "synthetic-thermal-limit", True)
    result = create_result(
        protocol, admission, metric, samples, result_id=result_id, state=state,
        correctness=correctness, interference=interference, measured_at_ms=30,
        uncertainty=0.05, abort=abort, origin=EvidenceOrigin.SYNTHETIC_SEMANTIC_FIXTURE,
    )
    return {
        "profile_id": profile_id,
        "domain_neutral": True,
        "synthetic_fixture_only": True,
        "physical_measurement_performed": False,
        "declared_synthetic_device_memory_bytes": declared_memory_bytes,
        "protocol_digest": content_digest(protocol),
        "result_id": result.result_id,
        "result_digest": content_digest(result),
        "raw_digest": result.raw_digest,
        "result_state": result.state,
        "interference_state": result.interference.state,
        "binding_digest": content_digest(binding),
        "authority_namespace": protocol.authority_namespace,
        "budget": protocol.budget,
    }


def build_profiles() -> tuple[dict[str, Any], ...]:
    profiles = tuple(_evidence(*profile) for profile in PROFILES)
    if len(profiles) != 7 or len({profile["profile_id"] for profile in profiles}) != 7:
        raise RuntimeError("M08 example must contain exactly seven unique synthetic profiles")
    if any(not profile["domain_neutral"] or not profile["synthetic_fixture_only"] or profile["physical_measurement_performed"] for profile in profiles):
        raise RuntimeError("M08 synthetic profile cannot claim physical measurement")
    return profiles


def main() -> None:
    profiles = build_profiles()
    report = {
        "harness_version": "1.0.0",
        "profile_count": len(profiles),
        "physical_measurements_performed": False,
        "profiles": profiles,
    }
    report["output_digest"] = content_digest(report)
    print(canonical_json(report))


if __name__ == "__main__":
    main()
