"""Immutable Hardware Genome snapshots and multidimensional evidence confidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .base import M07Record, content_digest, freeze_json
from .capabilities import BackendRelationship, CapabilityAssertion, DriverSkewGraph, VersionFact
from .discovery import DiscoverySnapshot
from .enums import ConfidenceAxis, ConfidenceLevel, EvidenceStrength, FreshnessClass, ObservationState
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError, HardwareGenomeValidationError
from .evidence import DiscoveryConflict, DiscoveryObservation, FactEnvelope
from .limits import DEFAULT_LIMITS, HardwareGenomeLimits
from .media import MediaEngineCapability, validate_media_capabilities
from .precision import PrecisionFeature
from .registry import SemanticKeyRegistry, validate_semantic_registry
from .schema import CORE_SCHEMA, SchemaDescriptor
from .subjects import HardwareSubjectRef, RuntimeSubstratePassport
from .telemetry import TelemetrySample
from .topology import TopologyGraph, validate_topology_graph
from .versions import require_identifier, require_nonnegative_int, require_version

__all__ = [
    "GenomeClaimStatus", "ConfidenceDescriptor", "genome_confidence_from_evidence", "HardwareGenome",
    "create_hardware_genome", "genome_identity_material", "validate_hardware_genome",
]


class GenomeClaimStatus(str, Enum):
    CURRENT_AT_CAPTURE = "CURRENT_AT_CAPTURE"
    HISTORICAL = "HISTORICAL"


_CONFIDENCE_ORDER = {
    ConfidenceLevel.NONE: 0,
    ConfidenceLevel.LOW: 1,
    ConfidenceLevel.MEDIUM: 2,
    ConfidenceLevel.HIGH: 3,
    ConfidenceLevel.VERIFIED: 4,
}
_EVIDENCE_LEVEL = {
    EvidenceStrength.DECLARED: ConfidenceLevel.LOW,
    EvidenceStrength.LOADABLE: ConfidenceLevel.MEDIUM,
    EvidenceStrength.DEVICE_BOUND: ConfidenceLevel.MEDIUM,
    EvidenceStrength.FEATURE_REPORTED: ConfidenceLevel.HIGH,
    EvidenceStrength.SMOKE_VERIFIED: ConfidenceLevel.VERIFIED,
}


@dataclass(frozen=True)
class ConfidenceDescriptor(M07Record):
    dimensions: tuple[tuple[ConfidenceAxis, ConfidenceLevel], ...]
    evidence_ids: tuple[str, ...]
    conflict_count: int
    derivation_depth: int

    def __post_init__(self) -> None:
        dimensions = tuple(self.dimensions)
        if any(type(axis) is not ConfidenceAxis or type(level) is not ConfidenceLevel for axis, level in dimensions):
            raise HardwareGenomeValidationError("confidence requires typed axis/level pairs")
        if len(dimensions) != len(ConfidenceAxis) or {axis for axis, _ in dimensions} != set(ConfidenceAxis):
            raise HardwareGenomeIntegrityError("confidence must preserve every independent evidence dimension")
        object.__setattr__(self, "dimensions", tuple(sorted(dimensions, key=lambda item: item[0].value)))
        ids = tuple(sorted(set(require_identifier(item, "evidence_ids[]") for item in self.evidence_ids)))
        object.__setattr__(self, "evidence_ids", ids)
        for field in ("conflict_count", "derivation_depth"):
            object.__setattr__(self, field, require_nonnegative_int(getattr(self, field), field))
        if self.conflict_count and dict(self.dimensions)[ConfidenceAxis.SOURCE_AGREEMENT] in {ConfidenceLevel.HIGH, ConfidenceLevel.VERIFIED}:
            raise HardwareGenomeIntegrityError("unresolved conflicts cannot carry high source-agreement confidence")

    def level_for(self, axis: ConfidenceAxis) -> ConfidenceLevel:
        return dict(self.dimensions)[axis]


def genome_confidence_from_evidence(
    observations: tuple[DiscoveryObservation, ...],
    conflicts: tuple[DiscoveryConflict, ...],
) -> ConfidenceDescriptor:
    """Derive bounded display confidence; repetition never promotes weak evidence."""
    observed = [item for item in observations if item.state is ObservationState.OBSERVED]
    strengths = [item.evidence_strength for item in observed if item.evidence_strength is not None]
    evidence_ids = tuple(sorted({item.evidence.evidence_id for item in observed if item.evidence is not None}))
    if not observed:
        strength_level = ConfidenceLevel.NONE
    else:
        strength_level = min((_EVIDENCE_LEVEL[item] for item in strengths), key=_CONFIDENCE_ORDER.__getitem__, default=ConfidenceLevel.NONE)
    has_conflicts = bool(conflicts) or any(item.state is ObservationState.CONFLICTING for item in observations)
    freshness = ConfidenceLevel.LOW if any(item.state is ObservationState.STALE or item.freshness is FreshnessClass.UNKNOWN_VOLATILITY for item in observations) else ConfidenceLevel.HIGH if observations else ConfidenceLevel.NONE
    complete = ConfidenceLevel.MEDIUM if any(item.state in {ObservationState.PARTIAL, ObservationState.UNKNOWN, ObservationState.UNAVAILABLE, ObservationState.PERMISSION_DENIED, ObservationState.UNSUPPORTED_PROBE} for item in observations) else ConfidenceLevel.HIGH if observations else ConfidenceLevel.NONE
    dimensions = (
        (ConfidenceAxis.SOURCE_AUTHORITY, strength_level),
        (ConfidenceAxis.SUBJECT_BINDING, ConfidenceLevel.HIGH if observed else ConfidenceLevel.NONE),
        (ConfidenceAxis.EVIDENCE_STRENGTH, strength_level),
        (ConfidenceAxis.FRESHNESS, freshness),
        (ConfidenceAxis.SOURCE_AGREEMENT, ConfidenceLevel.LOW if has_conflicts else ConfidenceLevel.HIGH if observed else ConfidenceLevel.NONE),
        (ConfidenceAxis.SEMANTIC_COMPLETENESS, complete),
        (ConfidenceAxis.VISIBILITY_COMPLETENESS, complete),
        (ConfidenceAxis.DERIVATION_DEPTH, ConfidenceLevel.LOW),
    )
    return ConfidenceDescriptor(dimensions, evidence_ids, len(conflicts), 0)


def _collection_sort_key(field: str, item: Any) -> tuple[str, ...] | str:
    if field == "subjects":
        return item.subject_id
    if field == "passports":
        return item.passport_id
    if field == "facts":
        observation = item.observation
        return (
            item.fact_key,
            observation.subject.subject_id if observation.subject is not None else "",
            observation.runtime.runtime_id if observation.runtime is not None else "",
            observation.observation_id,
        )
    if field == "capabilities":
        return item.assertion_id
    if field == "backend_relationships":
        return item.relation_id
    if field == "version_facts":
        return item.version_fact_id
    if field == "precision_features":
        return item.feature_id
    if field == "media_capabilities":
        return item.capability_id
    if field == "telemetry":
        return item.sample_id
    if field == "conflicts":
        return item.conflict_id
    raise HardwareGenomeIntegrityError(f"unknown immutable genome collection {field!r}")


@dataclass(frozen=True)
class HardwareGenome(M07Record):
    genome_id: str
    schema: SchemaDescriptor
    semantic_registry: SemanticKeyRegistry
    producer_version: str
    discovery: DiscoverySnapshot
    subjects: tuple[HardwareSubjectRef, ...]
    passports: tuple[RuntimeSubstratePassport, ...]
    facts: tuple[FactEnvelope, ...]
    capabilities: tuple[CapabilityAssertion, ...]
    backend_relationships: tuple[BackendRelationship, ...]
    version_facts: tuple[VersionFact, ...]
    driver_skew: DriverSkewGraph
    precision_features: tuple[PrecisionFeature, ...]
    media_capabilities: tuple[MediaEngineCapability, ...]
    topology: TopologyGraph
    telemetry: tuple[TelemetrySample, ...]
    conflicts: tuple[DiscoveryConflict, ...]
    confidence: ConfidenceDescriptor
    extensions: Mapping[str, Any]
    created_at_ms: int
    claim_status: GenomeClaimStatus = GenomeClaimStatus.CURRENT_AT_CAPTURE
    parent_genome_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "genome_id", require_identifier(self.genome_id, "genome_id"))
        if self.schema is None:
            raise HardwareGenomeValidationError("Hardware Genome requires an explicit schema descriptor")
        for field, kind in (("schema", SchemaDescriptor), ("semantic_registry", SemanticKeyRegistry), ("discovery", DiscoverySnapshot), ("driver_skew", DriverSkewGraph), ("topology", TopologyGraph), ("confidence", ConfidenceDescriptor)):
            object.__setattr__(self, field, kind.coerce(getattr(self, field), field))
        object.__setattr__(self, "producer_version", require_version(self.producer_version, "producer_version"))
        object.__setattr__(self, "created_at_ms", require_nonnegative_int(self.created_at_ms, "created_at_ms"))
        if type(self.claim_status) is not GenomeClaimStatus:
            raise HardwareGenomeValidationError("genome claim status must be current-at-capture or historical")
        if self.parent_genome_id is not None:
            object.__setattr__(self, "parent_genome_id", require_identifier(self.parent_genome_id, "parent_genome_id"))
        collection_types = (
            ("subjects", HardwareSubjectRef),
            ("passports", RuntimeSubstratePassport),
            ("facts", FactEnvelope),
            ("capabilities", CapabilityAssertion),
            ("backend_relationships", BackendRelationship),
            ("version_facts", VersionFact),
            ("precision_features", PrecisionFeature),
            ("media_capabilities", MediaEngineCapability),
            ("telemetry", TelemetrySample),
            ("conflicts", DiscoveryConflict),
        )
        for field, record_type in collection_types:
            values = tuple(record_type.coerce(item, f"{field}[]") for item in getattr(self, field))
            object.__setattr__(self, field, tuple(sorted(values, key=lambda item: _collection_sort_key(field, item))))
        frozen_extensions = freeze_json(self.extensions, "extensions")
        if not isinstance(frozen_extensions, MappingProxyType):
            raise HardwareGenomeValidationError("genome extensions must be a string-keyed object")
        object.__setattr__(self, "extensions", frozen_extensions)
        validate_hardware_genome(self, verify_identity=False)
        expected = f"m07-genome:{content_digest(genome_identity_material(self))}"
        if self.genome_id != expected:
            raise HardwareGenomeIntegrityError("GenomeId does not match its canonical evidence/content identity")


def genome_identity_material(genome: HardwareGenome | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(genome, HardwareGenome):
        fields = (
            "schema", "semantic_registry", "producer_version", "discovery", "subjects", "passports", "facts", "capabilities",
            "backend_relationships", "version_facts", "driver_skew", "precision_features", "media_capabilities",
            "topology", "telemetry", "conflicts", "confidence", "extensions", "created_at_ms", "claim_status", "parent_genome_id",
        )
        return {field: getattr(genome, field) for field in fields}
    if isinstance(genome, Mapping):
        return {key: value for key, value in genome.items() if key != "genome_id"}
    raise HardwareGenomeValidationError("genome identity material requires a HardwareGenome or mapping")


def create_hardware_genome(
    *,
    discovery: DiscoverySnapshot,
    subjects: tuple[HardwareSubjectRef, ...],
    passports: tuple[RuntimeSubstratePassport, ...] = (),
    facts: tuple[FactEnvelope, ...] | None = None,
    capabilities: tuple[CapabilityAssertion, ...] = (),
    backend_relationships: tuple[BackendRelationship, ...] = (),
    version_facts: tuple[VersionFact, ...] = (),
    driver_skew: DriverSkewGraph | None = None,
    precision_features: tuple[PrecisionFeature, ...] = (),
    media_capabilities: tuple[MediaEngineCapability, ...] = (),
    topology: TopologyGraph | None = None,
    telemetry: tuple[TelemetrySample, ...] = (),
    conflicts: tuple[DiscoveryConflict, ...] = (),
    confidence: ConfidenceDescriptor | None = None,
    extensions: Mapping[str, Any] | None = None,
    created_at_ms: int,
    producer_version: str = "1.0.0",
    schema: SchemaDescriptor = CORE_SCHEMA,
    semantic_registry: SemanticKeyRegistry | None = None,
    claim_status: GenomeClaimStatus = GenomeClaimStatus.CURRENT_AT_CAPTURE,
    parent_genome_id: str | None = None,
    limits: HardwareGenomeLimits = DEFAULT_LIMITS,
) -> HardwareGenome:
    discovery = DiscoverySnapshot.coerce(discovery, "discovery")
    resolved_registry = SemanticKeyRegistry.coerce(semantic_registry or SemanticKeyRegistry(), "semantic_registry")
    validate_semantic_registry(resolved_registry)
    observations = discovery.observations
    if facts is None:
        facts = tuple(FactEnvelope(item.fact_key, item, resolved_registry.version) for item in observations)
    if confidence is None:
        confidence = genome_confidence_from_evidence(observations, conflicts)
    if driver_skew is None:
        driver_skew = DriverSkewGraph("driver-skew-empty", (), ())
    if topology is None:
        topology = TopologyGraph("topology-empty", (), ())
    collection_values = {
        "subjects": subjects,
        "passports": passports,
        "facts": facts,
        "capabilities": capabilities,
        "backend_relationships": backend_relationships,
        "version_facts": version_facts,
        "precision_features": precision_features,
        "media_capabilities": media_capabilities,
        "telemetry": telemetry,
        "conflicts": conflicts,
    }
    collection_types: dict[str, Any] = {
        "subjects": HardwareSubjectRef,
        "passports": RuntimeSubstratePassport,
        "facts": FactEnvelope,
        "capabilities": CapabilityAssertion,
        "backend_relationships": BackendRelationship,
        "version_facts": VersionFact,
        "precision_features": PrecisionFeature,
        "media_capabilities": MediaEngineCapability,
        "telemetry": TelemetrySample,
        "conflicts": DiscoveryConflict,
    }
    ordered_collections: dict[str, tuple[Any, ...]] = {}
    for field, values in collection_values.items():
        record_type = collection_types[field]
        records = tuple(record_type.coerce(item, f"{field}[]") for item in values)
        ordered_collections[field] = tuple(sorted(records, key=lambda item: _collection_sort_key(field, item)))
    for collection, limit_name in (
        ("subjects", "max_subjects"),
        ("facts", "max_observations"),
        ("capabilities", "max_capabilities"),
        ("telemetry", "max_telemetry_samples"),
        ("conflicts", "max_conflicts"),
    ):
        limits.require(limit_name, len(ordered_collections[collection]))
    limits.require("max_extension_fields", len(extensions or {}))
    validate_topology_graph(topology, limits=limits)
    evidence_by_id = {
        item.evidence.evidence_id: item.evidence
        for item in discovery.observations
        if item.evidence is not None
    }
    limits.require("max_evidence_bytes", sum(item.payload_bytes for item in evidence_by_id.values()))
    payload: dict[str, Any] = {
        "schema": schema,
        "semantic_registry": resolved_registry,
        "producer_version": producer_version,
        "discovery": discovery,
        "subjects": ordered_collections["subjects"],
        "passports": ordered_collections["passports"],
        "facts": ordered_collections["facts"],
        "capabilities": ordered_collections["capabilities"],
        "backend_relationships": ordered_collections["backend_relationships"],
        "version_facts": ordered_collections["version_facts"],
        "driver_skew": driver_skew,
        "precision_features": ordered_collections["precision_features"],
        "media_capabilities": ordered_collections["media_capabilities"],
        "topology": topology,
        "telemetry": ordered_collections["telemetry"],
        "conflicts": ordered_collections["conflicts"],
        "confidence": confidence,
        "extensions": extensions or {},
        "created_at_ms": created_at_ms,
        "claim_status": claim_status,
        "parent_genome_id": parent_genome_id,
    }
    genome_id = f"m07-genome:{content_digest(payload, limits=limits)}"
    return HardwareGenome(genome_id=genome_id, **payload)


def validate_hardware_genome(genome: HardwareGenome, *, verify_identity: bool = True, limits: HardwareGenomeLimits = DEFAULT_LIMITS) -> None:
    if not isinstance(genome, HardwareGenome):
        raise HardwareGenomeValidationError("value must be an exact HardwareGenome")
    for name, maximum in (
        ("subjects", "max_subjects"), ("facts", "max_observations"), ("capabilities", "max_capabilities"),
        ("telemetry", "max_telemetry_samples"), ("conflicts", "max_conflicts"),
    ):
        limits.require(maximum, len(getattr(genome, name)))
    limits.require("max_extension_fields", len(genome.extensions))
    evidence_by_id = {
        item.evidence.evidence_id: item.evidence
        for item in genome.discovery.observations
        if item.evidence is not None
    }
    limits.require("max_evidence_bytes", sum(item.payload_bytes for item in evidence_by_id.values()))
    subject_ids = [item.subject_id for item in genome.subjects]
    if len(subject_ids) != len(set(subject_ids)):
        raise HardwareGenomeIntegrityError("Hardware Genome subject ids must be unique")
    known_subjects = set(subject_ids)
    semantic_registry = SemanticKeyRegistry.coerce(genome.semantic_registry, "semantic_registry")
    validate_semantic_registry(semantic_registry)
    for item in genome.discovery.observations:
        if item.subject is not None and item.subject.subject_id not in known_subjects:
            raise HardwareGenomeIntegrityError("discovery observation references a subject outside the genome")
    if any(item.parent_subject_id is not None and item.parent_subject_id not in known_subjects for item in genome.subjects):
        raise HardwareGenomeIntegrityError("hardware subject parent must be an explicitly represented subject")
    source_evidence = {
        item.evidence.evidence_id: item.evidence
        for item in genome.discovery.observations
        if item.evidence is not None
    }
    for subject in genome.subjects:
        for anchor in subject.identity_anchors:
            anchor_evidence = source_evidence.get(anchor.source_evidence_id)
            if anchor_evidence is None or anchor_evidence.subject_id != subject.subject_id:
                raise HardwareGenomeIntegrityError("identity anchors must reference admitted evidence for the exact hardware subject")
    for passport in genome.passports:
        if passport.substrate.runtime_ref != genome.discovery.session.runtime:
            raise HardwareGenomeIntegrityError("runtime passport must bind the exact discovery-session scope")
        if not set(passport.visible_subject_ids).issubset(known_subjects):
            raise HardwareGenomeIntegrityError("runtime passport visibility references an absent hardware subject")
        passport_evidence = source_evidence.get(passport.evidence_id)
        if (
            passport.observed_at_ms > genome.discovery.captured_at_ms
            or passport_evidence is None
            or passport_evidence.runtime_id != passport.substrate.runtime_ref.runtime_id
            or passport_evidence.observed_at_ms != passport.observed_at_ms
        ):
            raise HardwareGenomeIntegrityError("runtime passport time/evidence must be present in admitted discovery")
    fact_identity = [
        (
            item.observation.subject.subject_id if item.observation.subject is not None else None,
            item.observation.runtime.runtime_id if item.observation.runtime is not None else None,
            item.fact_key,
        )
        for item in genome.facts
    ]
    if len(fact_identity) != len(set(fact_identity)):
        raise HardwareGenomeIntegrityError("one genome cannot contain duplicate normalized fact identities")
    for fact in genome.facts:
        definition = semantic_registry.find(fact.fact_key)
        if fact.registry_version != semantic_registry.version:
            raise HardwareGenomeIntegrityError("fact registry version differs from the immutable genome semantic registry")
        if definition is None:
            raise HardwareGenomeAdmissionError("fact key is absent from the immutable core or governed semantic registry")
        if fact.observation.state not in definition.allowed_states:
            raise HardwareGenomeAdmissionError("fact state is not allowed by its versioned semantic key definition")
        if not definition.prefix_match and fact.observation.unit != definition.unit:
            raise HardwareGenomeIntegrityError("fact unit differs from its exact versioned semantic key definition")
    observation_ids = {item.observation.observation_id for item in genome.facts}
    observation_ids.update(item.observation_id for item in genome.discovery.observations)
    topology_link_observation_ids = {
        observation.observation_id
        for item in genome.topology.link_evidence
        for observation in (item.maximum_observation, item.negotiated_observation, item.bandwidth_observation)
        if observation is not None
    }
    if not topology_link_observation_ids.issubset(observation_ids):
        raise HardwareGenomeIntegrityError("PCIe link evidence observation is absent from the genome")
    for capability in genome.capabilities:
        if capability.observation.observation_id not in observation_ids:
            raise HardwareGenomeIntegrityError("capability evidence observation is absent from the genome")
    if genome.driver_skew.version_facts != genome.version_facts:
        raise HardwareGenomeIntegrityError("driver-skew graph and canonical version-fact section must match exactly")
    if any(edge.evidence_observation_id not in observation_ids for edge in genome.driver_skew.edges):
        raise HardwareGenomeIntegrityError("driver-skew compatibility evidence observation is absent from the genome")
    validate_media_capabilities(genome.media_capabilities)
    media_observation_ids = {
        observation.observation_id
        for item in genome.media_capabilities
        for observation in (item.observation, *(proof.observation for proof in item.interop_evidence))
    }
    if not media_observation_ids.issubset(observation_ids):
        raise HardwareGenomeIntegrityError("media or interop evidence observation is absent from the genome")
    for conflict in genome.conflicts:
        conflict.validate_against(genome.discovery.observations)
        source_observations = [
            item for item in genome.discovery.observations
            if item.observation_id in conflict.observation_ids
        ]
        representative = source_observations[0]
        normalized = [
            fact for fact in genome.facts
            if fact.fact_key == conflict.fact_key
            and fact.observation.subject == representative.subject
            and fact.observation.runtime == representative.runtime
        ]
        if len(normalized) != 1 or normalized[0].observation.state is not ObservationState.CONFLICTING:
            raise HardwareGenomeIntegrityError("unresolved source conflicts require one explicit CONFLICTING normalized fact")
    for relationship in genome.backend_relationships:
        relationship.validate_assertions(genome.capabilities)
    for precision in genome.precision_features:
        precision.validate_observations(genome.discovery.observations)
    expected_confidence = genome_confidence_from_evidence(genome.discovery.observations, genome.conflicts)
    if genome.confidence != expected_confidence:
        raise HardwareGenomeIntegrityError("confidence descriptor exceeds or diverges from its source evidence")
    validate_topology_graph(genome.topology, limits=limits)
    if verify_identity:
        expected = f"m07-genome:{content_digest(genome_identity_material(genome), limits=limits)}"
        if expected != genome.genome_id:
            raise HardwareGenomeIntegrityError("Hardware Genome canonical identity mismatch")
