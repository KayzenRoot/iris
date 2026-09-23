"""Allowlisted, permission-addressable and bounded M07 discovery admission."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M07Record, content_digest
from .enums import FreshnessClass, ObservationState, PrivacyClass, ProbeInterface, ProbeOrigin, ProbePermissionClass
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError, HardwareGenomeLimitError, HardwareGenomeSecurityError, HardwareGenomeValidationError
from .evidence import DiscoveryObservation
from .limits import DEFAULT_LIMITS, HardwareGenomeLimits
from .subjects import RuntimeSubjectRef
from .versions import require_identifier, require_nonnegative_int, require_unique, require_version

__all__ = [
    "ProbeDescriptor", "ProbeRegistry", "ProbePermissionGrant", "authorize_probe",
    "DiscoverySessionRef", "DiscoveryBatch", "DiscoverySnapshot", "admit_discovery_batch",
]


@dataclass(frozen=True)
class ProbeDescriptor(M07Record):
    probe_id: str
    version: str
    platform_families: tuple[str, ...]
    fact_families: tuple[str, ...]
    max_duration_ms: int
    max_output_bytes: int
    interface: ProbeInterface
    permission_class: ProbePermissionClass
    freshness: FreshnessClass
    privacy_class: PrivacyClass
    normalization_version: str
    origin: ProbeOrigin = ProbeOrigin.CORE
    read_only: bool = True
    requires_elevation: bool = False
    permits_arbitrary_execution: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "probe_id", require_identifier(self.probe_id, "probe_id"))
        for field in ("version", "normalization_version"):
            object.__setattr__(self, field, require_version(getattr(self, field), field))
        object.__setattr__(self, "platform_families", tuple(sorted(require_unique(self.platform_families, "platform_families", maximum=128))))
        object.__setattr__(self, "fact_families", tuple(sorted(require_unique(self.fact_families, "fact_families", maximum=256))))
        for field in ("max_duration_ms", "max_output_bytes"):
            object.__setattr__(self, field, require_nonnegative_int(getattr(self, field), field))
        if self.max_duration_ms == 0 or self.max_output_bytes == 0:
            raise HardwareGenomeValidationError("probe duration and output bounds must be positive")
        for field, kind in (("interface", ProbeInterface), ("permission_class", ProbePermissionClass), ("freshness", FreshnessClass), ("privacy_class", PrivacyClass), ("origin", ProbeOrigin)):
            if type(getattr(self, field)) is not kind:
                raise HardwareGenomeValidationError(f"{field} must use the closed M07 vocabulary")
        for field in ("read_only", "requires_elevation", "permits_arbitrary_execution"):
            if type(getattr(self, field)) is not bool:
                raise HardwareGenomeValidationError(f"{field} must be bool")
        if not self.read_only or self.requires_elevation or self.permits_arbitrary_execution:
            raise HardwareGenomeSecurityError("M07 probes must be read-only, non-privileged and non-arbitrary")
        if self.interface is ProbeInterface.DECLARED_EVIDENCE and self.permission_class is not ProbePermissionClass.BASIC_READ:
            raise HardwareGenomeSecurityError("declared evidence cannot request hardware probe privileges")
        if self.privacy_class is PrivacyClass.PROCESS_METADATA:
            raise HardwareGenomeSecurityError("process metadata is outside the hardware discovery probe contract")


@dataclass(frozen=True)
class ProbeRegistry(M07Record):
    registry_version: str
    descriptors: tuple[ProbeDescriptor, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "registry_version", require_version(self.registry_version, "registry_version"))
        descriptors = tuple(ProbeDescriptor.coerce(item, "descriptors[]") for item in self.descriptors)
        if len(descriptors) > 256:
            raise HardwareGenomeLimitError("probe registry exceeds the maximum of 256 descriptors")
        ids = [(item.probe_id, item.version) for item in descriptors]
        if len(ids) != len(set(ids)):
            raise HardwareGenomeValidationError("probe id/version pairs must be unique in a registry")
        object.__setattr__(self, "descriptors", tuple(sorted(descriptors, key=lambda item: (item.probe_id, item.version))))

    def find(self, probe_id: str, version: str) -> ProbeDescriptor | None:
        target = (require_identifier(probe_id, "probe_id"), require_version(version, "version"))
        return next((item for item in self.descriptors if (item.probe_id, item.version) == target), None)


@dataclass(frozen=True)
class ProbePermissionGrant(M07Record):
    grant_id: str
    probe_id: str
    probe_version: str
    permission_class: ProbePermissionClass
    subject_id: str
    runtime_id: str
    issued_at_ms: int
    expires_at_ms: int
    authority_evidence_id: str

    def __post_init__(self) -> None:
        for field in ("grant_id", "probe_id", "subject_id", "runtime_id", "authority_evidence_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "probe_version", require_version(self.probe_version, "probe_version"))
        if type(self.permission_class) is not ProbePermissionClass:
            raise HardwareGenomeValidationError("permission_class must use the closed M07 vocabulary")
        for field in ("issued_at_ms", "expires_at_ms"):
            object.__setattr__(self, field, require_nonnegative_int(getattr(self, field), field))
        if self.expires_at_ms <= self.issued_at_ms:
            raise HardwareGenomeValidationError("probe permission grants require a positive bounded lifetime")


def authorize_probe(
    descriptor: ProbeDescriptor,
    grant: ProbePermissionGrant,
    *,
    subject_id: str,
    runtime_id: str,
    now_ms: int,
) -> None:
    """Check an externally issued M54 permission proof; registration never grants it."""
    descriptor = ProbeDescriptor.coerce(descriptor, "descriptor")
    grant = ProbePermissionGrant.coerce(grant, "grant")
    now_ms = require_nonnegative_int(now_ms, "now_ms")
    expected = (descriptor.probe_id, descriptor.version, descriptor.permission_class, subject_id, runtime_id)
    received = (grant.probe_id, grant.probe_version, grant.permission_class, grant.subject_id, grant.runtime_id)
    if expected != received or not grant.issued_at_ms <= now_ms < grant.expires_at_ms:
        raise HardwareGenomeAdmissionError("probe grant is stale or bound to a different exact probe/subject/runtime")
    if descriptor.origin is ProbeOrigin.GOVERNED_EXTENSION and not grant.authority_evidence_id:
        raise HardwareGenomeAdmissionError("extension probes require external authority evidence")


@dataclass(frozen=True)
class DiscoverySessionRef(M07Record):
    session_id: str
    probe_registry_version: str
    runtime: RuntimeSubjectRef
    requested_fact_keys: tuple[str, ...]
    started_at_ms: int
    deadline_at_ms: int
    max_observations: int
    max_output_bytes: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "session_id", require_identifier(self.session_id, "session_id"))
        object.__setattr__(self, "probe_registry_version", require_version(self.probe_registry_version, "probe_registry_version"))
        object.__setattr__(self, "runtime", RuntimeSubjectRef.coerce(self.runtime, "runtime"))
        object.__setattr__(self, "requested_fact_keys", tuple(sorted(require_unique(self.requested_fact_keys, "requested_fact_keys", maximum=2_048))))
        for field in ("started_at_ms", "deadline_at_ms", "max_observations", "max_output_bytes"):
            object.__setattr__(self, field, require_nonnegative_int(getattr(self, field), field))
        if self.deadline_at_ms <= self.started_at_ms or self.max_observations == 0 or self.max_output_bytes == 0:
            raise HardwareGenomeValidationError("discovery session requires a positive bounded window and budget")


@dataclass(frozen=True)
class DiscoveryBatch(M07Record):
    batch_id: str
    session: DiscoverySessionRef
    probe: ProbeDescriptor
    observations: tuple[DiscoveryObservation, ...]
    completed_at_ms: int
    output_bytes: int
    complete: bool
    truncated: bool = False
    permission_gap: bool = False
    remaining_frontier: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "batch_id", require_identifier(self.batch_id, "batch_id"))
        object.__setattr__(self, "session", DiscoverySessionRef.coerce(self.session, "session"))
        object.__setattr__(self, "probe", ProbeDescriptor.coerce(self.probe, "probe"))
        observations = tuple(DiscoveryObservation.coerce(item, "observations[]") for item in self.observations)
        if len(observations) > self.session.max_observations:
            raise HardwareGenomeLimitError("discovery batch exceeds its session observation budget")
        if any(item.runtime is not None and item.runtime != self.session.runtime for item in observations):
            raise HardwareGenomeIntegrityError("discovery batch observation escaped its exact runtime session scope")
        if len({item.observation_id for item in observations}) != len(observations):
            raise HardwareGenomeValidationError("discovery observation ids must be unique in a batch")
        if any(item.evidence is not None and (item.evidence.probe_id != self.probe.probe_id or item.evidence.probe_version != self.probe.version) for item in observations):
            raise HardwareGenomeIntegrityError("batch contains evidence from a different probe version")
        object.__setattr__(self, "observations", tuple(sorted(observations, key=lambda item: item.observation_id)))
        object.__setattr__(self, "completed_at_ms", require_nonnegative_int(self.completed_at_ms, "completed_at_ms"))
        object.__setattr__(self, "output_bytes", require_nonnegative_int(self.output_bytes, "output_bytes"))
        for field in ("complete", "truncated", "permission_gap"):
            if type(getattr(self, field)) is not bool:
                raise HardwareGenomeValidationError(f"{field} must be bool")
        frontier = tuple(require_identifier(item, "remaining_frontier[]") for item in self.remaining_frontier)
        if len(frontier) != len(set(frontier)):
            raise HardwareGenomeValidationError("remaining frontier must not contain duplicate facts")
        object.__setattr__(self, "remaining_frontier", tuple(sorted(frontier)))
        if self.completed_at_ms < self.session.started_at_ms:
            raise HardwareGenomeValidationError("batch completion cannot precede discovery session start")
        if self.complete and (self.truncated or self.permission_gap or self.remaining_frontier):
            raise HardwareGenomeIntegrityError("truncated, blocked or unfinished discovery cannot be complete")
        if self.complete and not set(self.session.requested_fact_keys).issubset({item.fact_key for item in observations}):
            raise HardwareGenomeAdmissionError("complete discovery must report every requested fact scope explicitly")


@dataclass(frozen=True)
class DiscoverySnapshot(M07Record):
    snapshot_id: str
    session: DiscoverySessionRef
    observations: tuple[DiscoveryObservation, ...]
    completeness: ObservationState
    frontier: tuple[str, ...]
    captured_at_ms: int
    probe_registry_version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_id", require_identifier(self.snapshot_id, "snapshot_id"))
        object.__setattr__(self, "session", DiscoverySessionRef.coerce(self.session, "session"))
        observations = tuple(DiscoveryObservation.coerce(item, "observations[]") for item in self.observations)
        if len(observations) > self.session.max_observations:
            raise HardwareGenomeLimitError("snapshot exceeds the admitted session observation budget")
        if any(item.runtime is not None and item.runtime != self.session.runtime for item in observations):
            raise HardwareGenomeIntegrityError("snapshot observation escaped its exact runtime session scope")
        if len({item.observation_id for item in observations}) != len(observations):
            raise HardwareGenomeValidationError("snapshot observation ids must be unique")
        object.__setattr__(self, "observations", tuple(sorted(observations, key=lambda item: item.observation_id)))
        if type(self.completeness) is not ObservationState or self.completeness not in {ObservationState.OBSERVED, ObservationState.PARTIAL, ObservationState.UNKNOWN}:
            raise HardwareGenomeValidationError("snapshot completeness must be complete, partial or unknown")
        frontier = tuple(require_identifier(item, "frontier[]") for item in self.frontier)
        if self.completeness is ObservationState.PARTIAL and not frontier:
            raise HardwareGenomeAdmissionError("partial snapshots must preserve their discovery frontier")
        if self.completeness is ObservationState.OBSERVED and frontier:
            raise HardwareGenomeIntegrityError("complete snapshots cannot retain an unfinished frontier")
        object.__setattr__(self, "frontier", tuple(sorted(set(frontier))))
        object.__setattr__(self, "captured_at_ms", require_nonnegative_int(self.captured_at_ms, "captured_at_ms"))
        object.__setattr__(self, "probe_registry_version", require_version(self.probe_registry_version, "probe_registry_version"))
        if self.probe_registry_version != self.session.probe_registry_version:
            raise HardwareGenomeIntegrityError("snapshot registry version differs from its session")


def admit_discovery_batch(
    batch: DiscoveryBatch,
    registry: ProbeRegistry,
    *,
    limits: HardwareGenomeLimits = DEFAULT_LIMITS,
    permission_grants: tuple[ProbePermissionGrant, ...] = (),
    now_ms: int | None = None,
) -> DiscoverySnapshot:
    batch = DiscoveryBatch.coerce(batch, "batch")
    registry = ProbeRegistry.coerce(registry, "registry")
    if registry.registry_version != batch.session.probe_registry_version:
        raise HardwareGenomeAdmissionError("discovery session was created under a different probe registry")
    admitted_probe = registry.find(batch.probe.probe_id, batch.probe.version)
    if admitted_probe != batch.probe:
        raise HardwareGenomeAdmissionError("probe descriptor is not present in the exact allowlisted registry")
    if batch.probe.interface is not ProbeInterface.DECLARED_EVIDENCE:
        if now_ms is None:
            raise HardwareGenomeAdmissionError("runtime probes require an explicit current-time permission check")
        grants = tuple(ProbePermissionGrant.coerce(item, "permission_grants[]") for item in permission_grants)
        grants_by_subject = {item.subject_id: item for item in grants}
        if len(grants_by_subject) != len(grants):
            raise HardwareGenomeIntegrityError("probe permission grants must have unique exact subject bindings")
        required_subjects: set[str] = set()
        for item in batch.observations:
            if item.subject is not None:
                required_subjects.add(item.subject.subject_id)
            elif item.runtime is not None:
                required_subjects.add(item.runtime.runtime_id)
            else:
                raise HardwareGenomeIntegrityError("discovery observations must bind an exact subject before admission")
        if not required_subjects:
            required_subjects.add(batch.session.runtime.runtime_id)
        if not required_subjects.issubset(grants_by_subject):
            raise HardwareGenomeAdmissionError("runtime probe lacks a grant for every exact observed hardware/runtime subject")
        for subject_id in sorted(required_subjects):
            authorize_probe(batch.probe, grants_by_subject[subject_id], subject_id=subject_id, runtime_id=batch.session.runtime.runtime_id, now_ms=now_ms)
    if batch.output_bytes > min(batch.probe.max_output_bytes, batch.session.max_output_bytes, limits.max_probe_output_bytes):
        raise HardwareGenomeLimitError("probe output exceeded its declared bound")
    limits.require("max_observations", len(batch.observations))
    limits.require("max_probe_count", 1)
    evidence_bytes = sum(item.evidence.payload_bytes for item in batch.observations if item.evidence is not None)
    limits.require("max_evidence_bytes", evidence_bytes)
    duration = batch.completed_at_ms - batch.session.started_at_ms
    maximum_duration = min(batch.probe.max_duration_ms, batch.session.deadline_at_ms - batch.session.started_at_ms, limits.max_probe_duration_ms)
    late = duration > maximum_duration
    complete = batch.complete and not late and not batch.truncated and not batch.permission_gap
    frontier = set(batch.remaining_frontier)
    if late:
        frontier.update(batch.session.requested_fact_keys)
    if batch.truncated or batch.permission_gap:
        frontier.update(batch.remaining_frontier or batch.session.requested_fact_keys)
    state = ObservationState.OBSERVED if complete else ObservationState.PARTIAL
    if not complete and not frontier:
        frontier.update(batch.session.requested_fact_keys or ("discovery.unresolved",))
    snapshot_material = {
        "session": batch.session,
        "probe": batch.probe,
        "observations": batch.observations,
        "completeness": state,
        "frontier": tuple(sorted(frontier)),
        "captured_at_ms": batch.completed_at_ms,
    }
    snapshot_id = f"m07-snapshot:{content_digest(snapshot_material, limits=limits)}"
    return DiscoverySnapshot(snapshot_id, batch.session, batch.observations, state, tuple(sorted(frontier)), batch.completed_at_ms, registry.registry_version)
