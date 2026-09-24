"""Deterministic consumer contracts and acceptance evidence bundles."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M08Record, content_digest, require_sequence
from .calibration import CalibrationArtifact, CalibratedEvidence, FreshnessAssessment, apply_calibration
from .enums import FreshnessState
from .envelopes import CapabilityEnvelope
from .errors import MicrobenchmarkAdmissionError, MicrobenchmarkIntegrityError, MicrobenchmarkLimitError
from .evidence import BenchmarkResult, validate_result
from .limits import DEFAULT_LIMITS
from .probes import FixtureManifest, ProbeDefinition
from .protocols import ProtocolDescriptor
from .provenance import EvidencePurposeDescriptor, M07ProvenanceBinding
from .versions import CONTRACT_VERSION, require_digest, require_identifier, require_nonnegative_int, require_version

__all__ = ["AcceptanceEvidenceBundle", "build_acceptance_evidence_bundle"]


@dataclass(frozen=True)
class AcceptanceEvidenceBundle(M08Record):
    bundle_id: str
    version: str
    authority_namespace: str
    binding_digest: str
    protocol_refs: tuple[tuple[str, str, str], ...]
    fixture_refs: tuple[tuple[str, str, str], ...]
    probe_refs: tuple[tuple[str, str, str, str], ...]
    probe_result_refs: tuple[tuple[str, str], ...]
    result_refs: tuple[tuple[str, str, str, str, str], ...]
    envelope_refs: tuple[tuple[str, str], ...]
    calibration_refs: tuple[tuple[str, str, str], ...]
    calibrated_evidence_refs: tuple[tuple[str, str, str], ...]
    freshness_states: tuple[tuple[str, FreshnessState], ...]
    evidence_purpose: EvidencePurposeDescriptor
    release_acceptance_decision: str
    created_at_ms: int
    bundle_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "bundle_id", require_identifier(self.bundle_id, "bundle_id"))
        object.__setattr__(self, "version", require_version(self.version))
        object.__setattr__(self, "authority_namespace", require_identifier(self.authority_namespace, "authority_namespace"))
        if self.authority_namespace != "hardware-capability":
            raise MicrobenchmarkAdmissionError("acceptance evidence remains in the hardware-capability authority namespace")
        object.__setattr__(self, "binding_digest", require_digest(self.binding_digest, "binding_digest"))
        normalized = {
            "protocol_refs": tuple(sorted((require_identifier(key, "protocol_id"), require_version(version, "protocol_version"), require_digest(digest, "protocol_digest")) for key, version, digest in self.protocol_refs)),
            "fixture_refs": tuple(sorted((require_identifier(key, "fixture_id"), require_digest(digest, "fixture_digest"), require_digest(manifest, "fixture_manifest_digest")) for key, digest, manifest in self.fixture_refs)),
            "probe_refs": tuple(sorted((require_identifier(probe, "probe_id"), require_digest(digest, "probe_digest"), require_identifier(protocol, "protocol_id"), require_identifier(fixture, "fixture_id")) for probe, digest, protocol, fixture in self.probe_refs)),
            "probe_result_refs": tuple(sorted((require_identifier(probe, "probe_id"), require_identifier(result, "result_id")) for probe, result in self.probe_result_refs)),
            "result_refs": tuple(sorted((require_identifier(result, "result_id"), require_digest(record, "result_digest"), require_digest(raw, "raw_digest"), require_identifier(protocol, "protocol_id"), require_version(version, "protocol_version")) for result, record, raw, protocol, version in self.result_refs)),
            "envelope_refs": tuple(sorted((require_identifier(key, "envelope_id"), require_digest(digest, "envelope_digest")) for key, digest in self.envelope_refs)),
            "calibration_refs": tuple(sorted((require_identifier(key, "calibration_id"), require_version(version, "calibration_version"), require_digest(digest, "calibration_digest")) for key, version, digest in self.calibration_refs)),
            "calibrated_evidence_refs": tuple(sorted((require_identifier(key, "derived_id"), require_digest(digest, "lineage_digest"), require_identifier(source, "source_result_id")) for key, digest, source in self.calibrated_evidence_refs)),
        }
        for field, values in normalized.items():
            if (field in {"protocol_refs", "fixture_refs", "probe_refs", "probe_result_refs", "result_refs", "envelope_refs"} and not values) or len(set(values)) != len(values):
                raise MicrobenchmarkIntegrityError(f"{field} must be unique and non-empty when required")
            if len({item[0] for item in values}) != len(values):
                raise MicrobenchmarkIntegrityError(f"{field} cannot repeat an artifact identity")
            object.__setattr__(self, field, values)
        protocol_ids = {item[0] for item in normalized["protocol_refs"]}
        fixture_ids = {item[0] for item in normalized["fixture_refs"]}
        if any(item[2] not in protocol_ids for item in normalized["probe_refs"]):
            raise MicrobenchmarkIntegrityError("acceptance probe references a protocol outside this bundle")
        if any(item[3] not in fixture_ids for item in normalized["probe_refs"]):
            raise MicrobenchmarkIntegrityError("acceptance probe references a fixture outside this bundle")
        probe_ids = {item[0] for item in normalized["probe_refs"]}
        result_ids = {item[0] for item in normalized["result_refs"]}
        if {item[0] for item in normalized["probe_result_refs"]} - probe_ids or {item[1] for item in normalized["probe_result_refs"]} != result_ids:
            raise MicrobenchmarkIntegrityError("acceptance bundle must bind every result to exactly one included probe")
        protocol_versions = {item[0]: item[1] for item in normalized["protocol_refs"]}
        if any(protocol_versions.get(item[3]) != item[4] for item in normalized["result_refs"]):
            raise MicrobenchmarkIntegrityError("acceptance result references a protocol version outside this bundle")
        states = tuple(sorted((require_identifier(subject, "freshness subject"), state) for subject, state in self.freshness_states))
        if not states or len({subject for subject, _ in states}) != len(states) or any(not isinstance(state, FreshnessState) for _, state in states):
            raise MicrobenchmarkIntegrityError("acceptance bundle requires unique explicit freshness states")
        object.__setattr__(self, "freshness_states", states)
        evidence_ids = (
            {item[0] for item in normalized["result_refs"]}
            | {item[0] for item in normalized["envelope_refs"]}
            | {item[0] for item in normalized["calibration_refs"]}
            | {item[0] for item in normalized["calibrated_evidence_refs"]}
        )
        if {subject for subject, _ in states} != evidence_ids:
            raise MicrobenchmarkIntegrityError("acceptance bundle freshness must explicitly cover every evidence artifact")
        object.__setattr__(self, "evidence_purpose", EvidencePurposeDescriptor.coerce(self.evidence_purpose, "evidence_purpose"))
        if self.release_acceptance_decision != "EVIDENCE_ONLY":
            raise MicrobenchmarkAdmissionError("M08 evidence cannot make an M60 release-acceptance decision")
        object.__setattr__(self, "created_at_ms", require_nonnegative_int(self.created_at_ms, "created_at_ms"))
        object.__setattr__(self, "bundle_digest", require_digest(self.bundle_digest, "bundle_digest"))
        if self.bundle_digest != content_digest(_bundle_material(self)):
            raise MicrobenchmarkIntegrityError("acceptance bundle digest does not match its exact evidence references")


def _bundle_material(bundle: AcceptanceEvidenceBundle | dict[str, object]) -> dict[str, object]:
    if isinstance(bundle, AcceptanceEvidenceBundle):
        return {field: getattr(bundle, field) for field in (
            "bundle_id", "version", "authority_namespace", "binding_digest", "protocol_refs",
            "fixture_refs", "probe_refs", "probe_result_refs", "result_refs", "envelope_refs", "calibration_refs",
            "calibrated_evidence_refs", "freshness_states", "evidence_purpose",
            "release_acceptance_decision", "created_at_ms",
        )}
    return dict(bundle)


def build_acceptance_evidence_bundle(
    *,
    bundle_id: str,
    binding: M07ProvenanceBinding,
    protocols: tuple[ProtocolDescriptor, ...],
    fixtures: tuple[FixtureManifest, ...],
    probes: tuple[ProbeDefinition, ...],
    probe_result_pairs: tuple[tuple[str, str], ...],
    results: tuple[BenchmarkResult, ...],
    envelopes: tuple[CapabilityEnvelope, ...],
    calibrations: tuple[CalibrationArtifact, ...] = (),
    calibrated_evidence: tuple[CalibratedEvidence, ...] = (),
    freshness: tuple[FreshnessAssessment, ...] = (),
    evidence_purpose: EvidencePurposeDescriptor,
    created_at_ms: int,
) -> AcceptanceEvidenceBundle:
    binding = M07ProvenanceBinding.coerce(binding, "binding")
    purpose = EvidencePurposeDescriptor.coerce(evidence_purpose, "evidence_purpose")
    if not purpose.qualifies("microbenchmark-acceptance-evidence"):
        raise MicrobenchmarkAdmissionError("evidence purpose does not permit acceptance-bundle projection")
    protocol_values = tuple(ProtocolDescriptor.coerce(item, "protocols[]") for item in require_sequence(protocols, "protocols", maximum=DEFAULT_LIMITS.max_protocols))
    fixture_values = tuple(FixtureManifest.coerce(item, "fixtures[]") for item in require_sequence(fixtures, "fixtures", maximum=DEFAULT_LIMITS.max_fixtures))
    probe_values = tuple(ProbeDefinition.coerce(item, "probes[]") for item in require_sequence(probes, "probes", maximum=DEFAULT_LIMITS.max_probes))
    pair_values = tuple((require_identifier(probe_id, "probe_id"), require_identifier(result_id, "result_id")) for probe_id, result_id in require_sequence(probe_result_pairs, "probe_result_pairs", maximum=DEFAULT_LIMITS.max_results))
    result_values = tuple(BenchmarkResult.coerce(item, "results[]") for item in require_sequence(results, "results", maximum=DEFAULT_LIMITS.max_results))
    envelope_values = tuple(CapabilityEnvelope.coerce(item, "envelopes[]") for item in require_sequence(envelopes, "envelopes", maximum=DEFAULT_LIMITS.max_results))
    calibration_values = tuple(CalibrationArtifact.coerce(item, "calibrations[]") for item in require_sequence(calibrations, "calibrations", maximum=DEFAULT_LIMITS.max_results))
    calibrated_values = tuple(CalibratedEvidence.coerce(item, "calibrated_evidence[]") for item in require_sequence(calibrated_evidence, "calibrated_evidence", maximum=DEFAULT_LIMITS.max_results))
    freshness_values = tuple(FreshnessAssessment.coerce(item, "freshness[]") for item in require_sequence(freshness, "freshness", maximum=DEFAULT_LIMITS.max_results))
    if sum(map(len, (protocol_values, fixture_values, probe_values, pair_values, result_values, envelope_values, calibration_values, calibrated_values, freshness_values))) > DEFAULT_LIMITS.max_results:
        raise MicrobenchmarkLimitError("acceptance bundle evidence references exceed the aggregate item ceiling")
    if not protocol_values or not fixture_values or not probe_values or not result_values or not envelope_values:
        raise MicrobenchmarkAdmissionError("acceptance bundle requires exact protocols, fixtures, probes, results, and envelopes")
    protocol_refs = tuple(sorted((item.protocol_id, item.version, content_digest(item)) for item in protocol_values))
    fixture_refs = tuple(sorted((item.fixture_id, item.fixture_digest, content_digest(item)) for item in fixture_values))
    if any(len({item[0] for item in group}) != len(group) for group in (protocol_refs, fixture_refs)):
        raise MicrobenchmarkIntegrityError("acceptance inputs repeat protocol or fixture identities")
    binding_digest = content_digest(binding)
    protocol_map = {item.protocol_id: item for item in protocol_values}
    fixture_map = {item.fixture_id: item for item in fixture_values}
    if len(protocol_map) != len(protocol_values) or len(fixture_map) != len(fixture_values):
        raise MicrobenchmarkIntegrityError("acceptance inputs repeat protocol or fixture identities")
    if any(item.binding != binding for item in protocol_values):
        raise MicrobenchmarkIntegrityError("acceptance protocols do not share the exact supplied M07 binding")
    probe_refs: list[tuple[str, str, str, str]] = []
    for probe in probe_values:
        protocol = protocol_map.get(probe.protocol_id)
        if protocol is None or probe.fixture_id not in fixture_map:
            raise MicrobenchmarkAdmissionError("acceptance probe lacks its exact registered protocol or fixture")
        if protocol.binding != binding or probe.operation_family != protocol.operation_family:
            raise MicrobenchmarkIntegrityError("probe semantics differ from their exact protocol or M07 binding")
        if probe.adapter.backend_id != binding.backend_id:
            raise MicrobenchmarkIntegrityError("probe adapter does not match the exact backend in M07 provenance")
        probe_refs.append((probe.probe_id, content_digest(probe), probe.protocol_id, probe.fixture_id))
    if len({item[0] for item in probe_refs}) != len(probe_refs):
        raise MicrobenchmarkIntegrityError("acceptance inputs repeat a probe identity")
    result_refs: list[tuple[str, str, str, str, str]] = []
    result_map: dict[str, BenchmarkResult] = {}
    for result in result_values:
        protocol = protocol_map.get(result.protocol_id)
        if protocol is None or protocol.version != result.protocol_version:
            raise MicrobenchmarkAdmissionError("acceptance result lacks its exact protocol version")
        validate_result(result, protocol)
        if result.binding != binding:
            raise MicrobenchmarkIntegrityError("acceptance results do not share the exact supplied M07 binding")
        if result.result_id in result_map:
            raise MicrobenchmarkIntegrityError("acceptance inputs repeat a result identity")
        result_map[result.result_id] = result
        result_refs.append((result.result_id, content_digest(result), result.raw_digest, result.protocol_id, result.protocol_version))
    if len({probe_id for probe_id, _ in pair_values}) != len(pair_values) or len({result_id for _, result_id in pair_values}) != len(pair_values):
        raise MicrobenchmarkIntegrityError("each acceptance result must bind to exactly one unique probe")
    probe_map = {item.probe_id: item for item in probe_values}
    if {result_id for _, result_id in pair_values} != set(result_map):
        raise MicrobenchmarkAdmissionError("acceptance bundle must bind every included result to one probe")
    for probe_id, result_id in pair_values:
        exact_probe = probe_map.get(probe_id)
        exact_result = result_map[result_id]
        if exact_probe is None or exact_probe.protocol_id != exact_result.protocol_id:
            raise MicrobenchmarkIntegrityError("acceptance result/probe link crosses protocol identity")
    envelope_refs: list[tuple[str, str]] = []
    for envelope in envelope_values:
        if envelope.binding != binding or not set(envelope.source_result_ids).issubset(result_map):
            raise MicrobenchmarkIntegrityError("acceptance envelope lacks exact binding or included result lineage")
        expected_synthetic = bool(envelope.source_result_ids) and all(result_map[item].origin.value == "SYNTHETIC_SEMANTIC_FIXTURE" for item in envelope.source_result_ids)
        if envelope.synthetic_only != expected_synthetic:
            raise MicrobenchmarkIntegrityError("acceptance envelope synthetic evidence label differs from its exact source results")
        if envelope.envelope_id in {item[0] for item in envelope_refs}:
            raise MicrobenchmarkIntegrityError("acceptance inputs repeat an envelope identity")
        envelope_refs.append((envelope.envelope_id, envelope.envelope_digest))
    calibration_refs: list[tuple[str, str, str]] = []
    calibration_map = {item.calibration_id: item for item in calibration_values}
    if len(calibration_map) != len(calibration_values):
        raise MicrobenchmarkIntegrityError("acceptance inputs repeat a calibration identity")
    for calibration in calibration_values:
        if content_digest(binding) != calibration.applicable_binding_digest:
            raise MicrobenchmarkIntegrityError("acceptance calibration is bound to another M07 context")
        calibration_refs.append((calibration.calibration_id, calibration.version, content_digest(calibration)))
    calibrated_refs: list[tuple[str, str, str]] = []
    for derived in calibrated_values:
        calibration = calibration_map.get(derived.calibration_id)
        result = result_map.get(derived.source_result_id)
        if calibration is None or result is None:
            raise MicrobenchmarkAdmissionError("calibrated acceptance evidence lacks its exact calibration or raw result")
        recomputed = apply_calibration(result, calibration, derived_id=derived.derived_id, at_ms=derived.created_at_ms)
        if recomputed != derived:
            raise MicrobenchmarkIntegrityError("calibrated acceptance evidence does not recompute from its immutable raw source")
        calibrated_refs.append((derived.derived_id, derived.lineage_digest, derived.source_result_id))
    state_map = {item.subject_ref: item.state for item in freshness_values}
    if len(state_map) != len(freshness_values):
        raise MicrobenchmarkIntegrityError("acceptance bundle repeats a freshness subject")
    evidence_subjects = set(result_map) | {item[0] for item in envelope_refs} | set(calibration_map) | {item.derived_id for item in calibrated_values}
    if set(state_map) - evidence_subjects:
        raise MicrobenchmarkAdmissionError("freshness assessment references evidence outside this acceptance bundle")
    envelope_states = {item.envelope_id: item.validity_state for item in envelope_values}
    if any(subject in envelope_states and state != envelope_states[subject] for subject, state in state_map.items()):
        raise MicrobenchmarkIntegrityError("acceptance freshness evidence conflicts with envelope validity state")
    freshness_states = tuple(sorted((subject, state_map.get(subject, FreshnessState.UNKNOWN_FRESHNESS)) for subject in evidence_subjects))
    freshness_states = tuple(sorted((subject, envelope_states.get(subject, state)) for subject, state in freshness_states))
    content = {
        "bundle_id": require_identifier(bundle_id, "bundle_id"),
        "version": CONTRACT_VERSION,
        "authority_namespace": "hardware-capability",
        "binding_digest": binding_digest,
        "protocol_refs": protocol_refs,
        "fixture_refs": fixture_refs,
        "probe_refs": tuple(sorted(probe_refs)),
        "probe_result_refs": tuple(sorted(pair_values)),
        "result_refs": tuple(sorted(result_refs)),
        "envelope_refs": tuple(sorted(envelope_refs)),
        "calibration_refs": tuple(sorted(calibration_refs)),
        "calibrated_evidence_refs": tuple(sorted(calibrated_refs)),
        "freshness_states": freshness_states,
        "evidence_purpose": purpose,
        "release_acceptance_decision": "EVIDENCE_ONLY",
        "created_at_ms": require_nonnegative_int(created_at_ms, "created_at_ms"),
    }
    return AcceptanceEvidenceBundle(**content, bundle_digest=content_digest(content))
