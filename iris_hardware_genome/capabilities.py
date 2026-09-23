"""Provider-neutral backend, capability evidence and version-skew surfaces."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M07Record, freeze_json
from .enums import BackendFamily, EvidenceStrength, ObservationState, VersionDimension
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError, HardwareGenomeValidationError
from .evidence import DiscoveryObservation
from .subjects import HardwareSubjectRef, RuntimeSubjectRef
from .versions import require_identifier, require_unique, require_version

__all__ = [
    "CapabilityAssertion", "BackendRelationship", "VersionFact", "DriverSkewEdge", "DriverSkewGraph",
    "SoftwareAdapterEvidence", "validate_strength_transition",
]

_EVIDENCE_ORDER = {
    EvidenceStrength.DECLARED: 1,
    EvidenceStrength.LOADABLE: 2,
    EvidenceStrength.DEVICE_BOUND: 3,
    EvidenceStrength.FEATURE_REPORTED: 4,
    EvidenceStrength.SMOKE_VERIFIED: 5,
}


@dataclass(frozen=True)
class CapabilityAssertion(M07Record):
    assertion_id: str
    subject: HardwareSubjectRef
    runtime: RuntimeSubjectRef
    backend: BackendFamily
    capability_key: str
    state: ObservationState
    evidence_strength: EvidenceStrength | None
    observation: DiscoveryObservation
    feature_value: object = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "assertion_id", require_identifier(self.assertion_id, "assertion_id"))
        object.__setattr__(self, "subject", HardwareSubjectRef.coerce(self.subject, "subject"))
        object.__setattr__(self, "runtime", RuntimeSubjectRef.coerce(self.runtime, "runtime"))
        for field, kind in (("backend", BackendFamily), ("state", ObservationState)):
            if type(getattr(self, field)) is not kind:
                raise HardwareGenomeValidationError(f"{field} must use a closed M07 vocabulary")
        object.__setattr__(self, "capability_key", require_identifier(self.capability_key, "capability_key"))
        object.__setattr__(self, "observation", DiscoveryObservation.coerce(self.observation, "observation"))
        if self.evidence_strength is not None and type(self.evidence_strength) is not EvidenceStrength:
            raise HardwareGenomeValidationError("evidence_strength must be a closed EvidenceStrength")
        observation = self.observation
        if (
            observation.subject != self.subject
            or observation.runtime != self.runtime
            or observation.fact_key != self.capability_key
            or observation.state is not self.state
        ):
            raise HardwareGenomeIntegrityError("capability assertion differs from its exact observation binding")
        if self.state is ObservationState.OBSERVED:
            if self.evidence_strength is None or observation.evidence_strength is not self.evidence_strength:
                raise HardwareGenomeAdmissionError("positive capability requires its exact evidence ladder level")
            if self.feature_value is None or observation.value != freeze_json(self.feature_value, "feature_value"):
                raise HardwareGenomeIntegrityError("capability value must equal the admitted observation value")
            object.__setattr__(self, "feature_value", freeze_json(self.feature_value, "feature_value"))
        elif self.feature_value is not None:
            raise HardwareGenomeAdmissionError("non-positive capability state cannot carry a feature value")
        if self.evidence_strength is EvidenceStrength.SMOKE_VERIFIED and self.state is not ObservationState.OBSERVED:
            raise HardwareGenomeAdmissionError("smoke verification must refer to positive bounded conformance evidence")


@dataclass(frozen=True)
class BackendRelationship(M07Record):
    relation_id: str
    subject: HardwareSubjectRef
    runtime: RuntimeSubjectRef
    backend: BackendFamily
    assertion_ids: tuple[str, ...]
    software_or_emulated: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "relation_id", require_identifier(self.relation_id, "relation_id"))
        object.__setattr__(self, "subject", HardwareSubjectRef.coerce(self.subject, "subject"))
        object.__setattr__(self, "runtime", RuntimeSubjectRef.coerce(self.runtime, "runtime"))
        if type(self.backend) is not BackendFamily or type(self.software_or_emulated) is not bool:
            raise HardwareGenomeValidationError("backend relationship fields are invalid")
        object.__setattr__(self, "assertion_ids", tuple(sorted(require_unique(self.assertion_ids, "assertion_ids", maximum=10_000))))
        if not self.assertion_ids:
            raise HardwareGenomeAdmissionError("backend relationships require at least one exact capability assertion")

    def validate_assertions(self, assertions: tuple[CapabilityAssertion, ...]) -> None:
        by_id = {item.assertion_id: item for item in assertions}
        selected = [by_id.get(item) for item in self.assertion_ids]
        if any(item is None for item in selected):
            raise HardwareGenomeIntegrityError("backend relationship references an absent assertion")
        for item in selected:
            if item is not None and (item.subject != self.subject or item.runtime != self.runtime or item.backend is not self.backend):
                raise HardwareGenomeIntegrityError("backend relationship cannot broadcast to another subject/runtime")


@dataclass(frozen=True)
class VersionFact(M07Record):
    version_fact_id: str
    dimension: VersionDimension
    component_id: str
    version: str
    active: bool
    observation: DiscoveryObservation

    def __post_init__(self) -> None:
        for field in ("version_fact_id", "component_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if type(self.dimension) is not VersionDimension or type(self.active) is not bool:
            raise HardwareGenomeValidationError("version dimension and active state must be explicit")
        object.__setattr__(self, "version", require_version(self.version, "version"))
        object.__setattr__(self, "observation", DiscoveryObservation.coerce(self.observation, "observation"))
        if self.observation.state is not ObservationState.OBSERVED or self.observation.value != self.version:
            raise HardwareGenomeAdmissionError("version facts require exact positive observation evidence")
        expected_key = f"version.{self.dimension.value.lower()}.{self.component_id}"
        if self.observation.fact_key != expected_key:
            raise HardwareGenomeIntegrityError("version fact dimension/component do not match its normalized evidence key")


@dataclass(frozen=True)
class DriverSkewEdge(M07Record):
    edge_id: str
    source_fact_id: str
    target_fact_id: str
    relation: str
    reported_compatibility: ObservationState
    evidence_observation_id: str
    compatibility_observation: DiscoveryObservation

    def __post_init__(self) -> None:
        for field in ("edge_id", "source_fact_id", "target_fact_id", "relation", "evidence_observation_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if type(self.reported_compatibility) is not ObservationState:
            raise HardwareGenomeValidationError("reported_compatibility must retain an explicit evidence state")
        if self.source_fact_id == self.target_fact_id:
            raise HardwareGenomeValidationError("driver skew edges must connect distinct version facts")
        observation = DiscoveryObservation.coerce(self.compatibility_observation, "compatibility_observation")
        object.__setattr__(self, "compatibility_observation", observation)
        if observation.observation_id != self.evidence_observation_id or observation.state is not self.reported_compatibility:
            raise HardwareGenomeIntegrityError("driver-skew compatibility state/id differs from its exact evidence observation")
        if observation.fact_key != f"driver.compatibility.{self.source_fact_id}.{self.target_fact_id}":
            raise HardwareGenomeIntegrityError("driver-skew compatibility evidence has the wrong normalized edge key")


@dataclass(frozen=True)
class DriverSkewGraph(M07Record):
    graph_id: str
    version_facts: tuple[VersionFact, ...]
    edges: tuple[DriverSkewEdge, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        facts = tuple(VersionFact.coerce(item, "version_facts[]") for item in self.version_facts)
        edges = tuple(DriverSkewEdge.coerce(item, "edges[]") for item in self.edges)
        if len({item.version_fact_id for item in facts}) != len(facts) or len({item.edge_id for item in edges}) != len(edges):
            raise HardwareGenomeValidationError("driver skew graph ids must be unique")
        ids = {item.version_fact_id for item in facts}
        if any(edge.source_fact_id not in ids or edge.target_fact_id not in ids for edge in edges):
            raise HardwareGenomeIntegrityError("driver skew graph edge references an absent version fact")
        by_id = {item.version_fact_id: item for item in facts}
        for edge in edges:
            source, target = by_id[edge.source_fact_id], by_id[edge.target_fact_id]
            if (source.observation.subject, source.observation.runtime) != (target.observation.subject, target.observation.runtime):
                raise HardwareGenomeIntegrityError("driver-skew version edges must preserve exact subject/runtime scope")
            if (edge.compatibility_observation.subject, edge.compatibility_observation.runtime) != (source.observation.subject, source.observation.runtime):
                raise HardwareGenomeIntegrityError("driver-skew compatibility evidence must bind the exact version subject/runtime")
        object.__setattr__(self, "version_facts", tuple(sorted(facts, key=lambda item: item.version_fact_id)))
        object.__setattr__(self, "edges", tuple(sorted(edges, key=lambda item: item.edge_id)))


@dataclass(frozen=True)
class SoftwareAdapterEvidence(M07Record):
    adapter_id: str
    subject_id: str
    backend: BackendFamily
    software_class: str
    observation: DiscoveryObservation

    def __post_init__(self) -> None:
        for field in ("adapter_id", "subject_id", "software_class"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if type(self.backend) is not BackendFamily:
            raise HardwareGenomeValidationError("backend must use the closed BackendFamily vocabulary")
        object.__setattr__(self, "observation", DiscoveryObservation.coerce(self.observation, "observation"))
        if self.observation.subject is None or self.observation.subject.subject_id != self.subject_id:
            raise HardwareGenomeIntegrityError("software adapter evidence must bind its exact hardware subject")


def validate_strength_transition(previous: CapabilityAssertion, current: CapabilityAssertion) -> None:
    previous = CapabilityAssertion.coerce(previous, "previous")
    current = CapabilityAssertion.coerce(current, "current")
    if (previous.subject, previous.runtime, previous.backend, previous.capability_key) != (current.subject, current.runtime, current.backend, current.capability_key):
        raise HardwareGenomeIntegrityError("capability transitions must preserve exact semantic binding")
    prior = _EVIDENCE_ORDER[previous.evidence_strength] if previous.evidence_strength is not None else 0
    next_level = _EVIDENCE_ORDER[current.evidence_strength] if current.evidence_strength is not None else 0
    old_evidence = previous.observation.evidence.evidence_id if previous.observation.evidence else None
    new_evidence = current.observation.evidence.evidence_id if current.observation.evidence else None
    if next_level > prior and (new_evidence is None or new_evidence == old_evidence):
        raise HardwareGenomeAdmissionError("evidence strength cannot increase without new exact evidence")
    if previous.state is ObservationState.CONFLICTING and current.state is ObservationState.OBSERVED and new_evidence == old_evidence:
        raise HardwareGenomeAdmissionError("a conflict cannot be hidden without new governed evidence")
