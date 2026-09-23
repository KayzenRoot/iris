"""Provenance-bearing observations and the negative assertion firewall."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import M07Record, freeze_json
from .enums import EvidenceStrength, FreshnessClass, ObservationState
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError, HardwareGenomeValidationError
from .subjects import HardwareSubjectRef, RuntimeSubjectRef
from .versions import require_digest, require_identifier, require_nonnegative_int, require_version

__all__ = ["ProbeEvidenceRef", "AbsenceProof", "DiscoveryObservation", "DiscoveryConflict", "FactEnvelope"]


@dataclass(frozen=True)
class ProbeEvidenceRef(M07Record):
    evidence_id: str
    digest: str
    probe_id: str
    probe_version: str
    source_adapter_id: str
    source_adapter_version: str
    observed_at_ms: int
    visibility_scope: str
    payload_bytes: int
    subject_id: str | None = None
    related_subject_id: str | None = None
    runtime_id: str | None = None

    def __post_init__(self) -> None:
        for field in ("evidence_id", "probe_id", "source_adapter_id", "visibility_scope"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "digest", require_digest(self.digest, "evidence digest"))
        for field in ("probe_version", "source_adapter_version"):
            object.__setattr__(self, field, require_version(getattr(self, field), field))
        for field in ("observed_at_ms", "payload_bytes"):
            object.__setattr__(self, field, require_nonnegative_int(getattr(self, field), field))
        for field in ("subject_id", "related_subject_id", "runtime_id"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_identifier(value, field))
        if self.subject_id is None and self.runtime_id is None:
            raise HardwareGenomeValidationError("probe evidence must bind a hardware or runtime subject")
        if self.related_subject_id is not None and self.subject_id is None:
            raise HardwareGenomeValidationError("pairwise evidence must bind a source hardware subject")


@dataclass(frozen=True)
class AbsenceProof(M07Record):
    proof_id: str
    fact_scope: str
    capable_probe_id: str
    evidence: ProbeEvidenceRef
    scope_complete: bool
    truncated: bool
    permission_gap: bool
    source_fresh: bool

    def __post_init__(self) -> None:
        for field in ("proof_id", "fact_scope", "capable_probe_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "evidence", ProbeEvidenceRef.coerce(self.evidence, "evidence"))
        for field in ("scope_complete", "truncated", "permission_gap", "source_fresh"):
            if type(getattr(self, field)) is not bool:
                raise HardwareGenomeValidationError(f"{field} must be bool")

    def proves_absence_for(self, fact_key: str, evidence: ProbeEvidenceRef) -> bool:
        return (
            self.fact_scope == fact_key
            and self.capable_probe_id == evidence.probe_id
            and self.evidence == evidence
            and self.scope_complete
            and not self.truncated
            and not self.permission_gap
            and self.source_fresh
        )


@dataclass(frozen=True)
class DiscoveryObservation(M07Record):
    observation_id: str
    fact_key: str
    state: ObservationState
    observed_at_ms: int
    freshness: FreshnessClass
    visibility_scope: str
    subject: HardwareSubjectRef | None = None
    runtime: RuntimeSubjectRef | None = None
    value: Any = None
    unit: str | None = None
    semantic_type: str | None = None
    evidence: ProbeEvidenceRef | None = None
    evidence_strength: EvidenceStrength | None = None
    absence_proof: AbsenceProof | None = None
    partial_frontier: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in ("observation_id", "fact_key", "visibility_scope"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if type(self.state) is not ObservationState or type(self.freshness) is not FreshnessClass:
            raise HardwareGenomeValidationError("state and freshness must use their closed M07 vocabularies")
        object.__setattr__(self, "observed_at_ms", require_nonnegative_int(self.observed_at_ms, "observed_at_ms"))
        if self.subject is None and self.runtime is None:
            raise HardwareGenomeValidationError("an observation must bind an exact hardware or runtime subject")
        if self.subject is not None:
            object.__setattr__(self, "subject", HardwareSubjectRef.coerce(self.subject, "subject"))
        if self.runtime is not None:
            object.__setattr__(self, "runtime", RuntimeSubjectRef.coerce(self.runtime, "runtime"))
        if self.unit is not None:
            object.__setattr__(self, "unit", require_identifier(self.unit, "unit"))
        if self.semantic_type is not None:
            object.__setattr__(self, "semantic_type", require_identifier(self.semantic_type, "semantic_type"))
        if self.evidence is not None:
            object.__setattr__(self, "evidence", ProbeEvidenceRef.coerce(self.evidence, "evidence"))
            if self.evidence.observed_at_ms != self.observed_at_ms or self.evidence.visibility_scope != self.visibility_scope:
                raise HardwareGenomeIntegrityError("observation time/scope must match its exact evidence envelope")
            if self.subject is not None and self.evidence.subject_id != self.subject.subject_id:
                raise HardwareGenomeIntegrityError("evidence is bound to a different hardware subject")
            if self.subject is None and self.evidence.subject_id is not None:
                raise HardwareGenomeIntegrityError("evidence has an undeclared hardware subject binding")
            if self.runtime is not None and self.evidence.runtime_id != self.runtime.runtime_id:
                raise HardwareGenomeIntegrityError("evidence is bound to a different runtime subject")
            if self.runtime is None and self.evidence.runtime_id is not None:
                raise HardwareGenomeIntegrityError("evidence has an undeclared runtime subject binding")
            if self.evidence.related_subject_id is not None:
                raise HardwareGenomeIntegrityError("one-subject observations cannot carry pairwise evidence")
        if self.evidence_strength is not None and type(self.evidence_strength) is not EvidenceStrength:
            raise HardwareGenomeValidationError("evidence_strength must be a closed EvidenceStrength")
        frontier = tuple(require_identifier(item, "partial_frontier[]") for item in self.partial_frontier)
        if len(frontier) != len(set(frontier)):
            raise HardwareGenomeValidationError("partial discovery frontier must not contain duplicates")
        object.__setattr__(self, "partial_frontier", tuple(sorted(frontier)))
        if self.state is ObservationState.OBSERVED:
            if self.value is None or self.evidence is None or self.evidence_strength is None:
                raise HardwareGenomeAdmissionError("positive observations require a value, evidence and strength")
            if self.evidence.payload_bytes <= 0:
                raise HardwareGenomeAdmissionError("positive observations require non-empty evidence")
            object.__setattr__(self, "value", freeze_json(self.value, "observation.value"))
            if self.absence_proof is not None or self.partial_frontier:
                raise HardwareGenomeValidationError("positive observations cannot carry absence or partial markers")
        elif self.state is ObservationState.NOT_PRESENT_PROVEN:
            if self.value is not None or self.evidence is None or self.absence_proof is None:
                raise HardwareGenomeAdmissionError("proven absence requires an explicit absence proof and no value")
            proof = AbsenceProof.coerce(self.absence_proof, "absence_proof")
            if not proof.proves_absence_for(self.fact_key, self.evidence):
                raise HardwareGenomeAdmissionError("unknown, blocked, stale or partial evidence cannot prove absence")
            object.__setattr__(self, "absence_proof", proof)
            if self.partial_frontier:
                raise HardwareGenomeValidationError("complete absence proof cannot carry a partial frontier")
        else:
            if self.value is not None:
                raise HardwareGenomeAdmissionError(f"{self.state.value} cannot carry a positive fact value")
            if self.absence_proof is not None:
                raise HardwareGenomeValidationError("only NOT_PRESENT_PROVEN may carry an absence proof")
            if self.state is ObservationState.PARTIAL and not self.partial_frontier:
                raise HardwareGenomeAdmissionError("partial observations must preserve an explicit frontier")
            if self.state is not ObservationState.PARTIAL and self.partial_frontier:
                raise HardwareGenomeValidationError("only partial observations may carry a frontier")


@dataclass(frozen=True)
class FactEnvelope(M07Record):
    """Normalized fact envelope; observation provenance is preserved by reference."""

    fact_key: str
    observation: DiscoveryObservation
    registry_version: str
    materiality_declared_by: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "fact_key", require_identifier(self.fact_key, "fact_key"))
        object.__setattr__(self, "observation", DiscoveryObservation.coerce(self.observation, "observation"))
        object.__setattr__(self, "registry_version", require_version(self.registry_version, "registry_version"))
        if self.fact_key != self.observation.fact_key:
            raise HardwareGenomeIntegrityError("fact envelope key differs from observation key")
        if self.materiality_declared_by is not None:
            object.__setattr__(self, "materiality_declared_by", require_identifier(self.materiality_declared_by, "materiality_declared_by"))


@dataclass(frozen=True)
class DiscoveryConflict(M07Record):
    conflict_id: str
    fact_key: str
    observation_ids: tuple[str, ...]
    reason_code: str
    source_priority_projection: str | None = None

    def __post_init__(self) -> None:
        for field in ("conflict_id", "fact_key", "reason_code"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        ids = tuple(require_identifier(item, "observation_ids[]") for item in self.observation_ids)
        if len(ids) < 2 or len(ids) != len(set(ids)):
            raise HardwareGenomeValidationError("a discovery conflict requires at least two distinct observations")
        object.__setattr__(self, "observation_ids", tuple(sorted(ids)))
        if self.source_priority_projection is not None:
            object.__setattr__(self, "source_priority_projection", require_identifier(self.source_priority_projection, "source_priority_projection"))

    def validate_against(self, observations: tuple[DiscoveryObservation, ...]) -> None:
        by_id = {item.observation_id: item for item in observations}
        selected = [by_id.get(item) for item in self.observation_ids]
        if any(item is None for item in selected):
            raise HardwareGenomeIntegrityError("conflict references an absent observation")
        values = [item for item in selected if item is not None]
        if any(item.fact_key != self.fact_key for item in values):
            raise HardwareGenomeIntegrityError("conflict observations must refer to the same fact key")
        if len({(item.subject.subject_id if item.subject else None, item.runtime.runtime_id if item.runtime else None) for item in values}) != 1:
            raise HardwareGenomeIntegrityError("conflicting observations must share exact subject/runtime scope")
        if len({(item.state, repr(item.value)) for item in values}) < 2:
            raise HardwareGenomeAdmissionError("conflict must preserve materially disagreeing evidence")
