"""Exact-device media engine facts, separate from throughput or concurrency."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

from .base import M07Record
from .enums import EvidenceStrength, MediaDirection, ObservationState
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError, HardwareGenomeValidationError
from .evidence import DiscoveryObservation
from .versions import require_identifier, require_nonnegative_int

__all__ = ["MediaInteropEvidence", "MediaEngineCapability", "validate_media_capabilities"]


@dataclass(frozen=True)
class MediaInteropEvidence(M07Record):
    interop_id: str
    subject_id: str
    runtime_id: str
    source_engine_id: str
    source_api: str
    target_engine_id: str
    target_api: str
    state: ObservationState
    observation: DiscoveryObservation

    def __post_init__(self) -> None:
        for field in ("interop_id", "subject_id", "runtime_id", "source_engine_id", "source_api", "target_engine_id", "target_api"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if type(self.state) is not ObservationState:
            raise HardwareGenomeValidationError("media interop state must be explicit")
        object.__setattr__(self, "observation", DiscoveryObservation.coerce(self.observation, "observation"))
        if self.source_engine_id == self.target_engine_id and self.source_api == self.target_api:
            raise HardwareGenomeValidationError("media interop must join distinct API or engine paths")
        expected_key = f"media.interop.{self.source_api.lower()}.{self.target_api.lower()}"
        if self.observation.fact_key != expected_key or self.observation.state is not self.state:
            raise HardwareGenomeIntegrityError("media interop API pair/state differs from its evidence fact")
        if self.observation.subject is None or self.observation.subject.subject_id != self.subject_id:
            raise HardwareGenomeIntegrityError("media interop must bind the exact device subject")
        if self.observation.runtime is None or self.observation.runtime.runtime_id != self.runtime_id:
            raise HardwareGenomeIntegrityError("media interop must bind the exact runtime scope")
        if self.state is ObservationState.OBSERVED:
            value = self.observation.value
            expected = {
                "source_engine_id": self.source_engine_id,
                "source_api": self.source_api,
                "target_engine_id": self.target_engine_id,
                "target_api": self.target_api,
            }
            if not isinstance(value, Mapping) or any(value.get(key) != item for key, item in expected.items()):
                raise HardwareGenomeIntegrityError("positive media interop requires exact source and target API-path evidence")


@dataclass(frozen=True)
class MediaEngineCapability(M07Record):
    capability_id: str
    subject_id: str
    runtime_id: str
    engine_id: str
    api_family: str
    codec: str
    direction: MediaDirection
    profile: str | None
    level: str | None
    bit_depth: int | None
    chroma_format: str | None
    max_width: int | None
    max_height: int | None
    input_format: str | None
    output_format: str | None
    evidence_strength: EvidenceStrength
    state: ObservationState
    observation: DiscoveryObservation
    interop_keys: tuple[str, ...] = ()
    interop_evidence: tuple[MediaInteropEvidence, ...] = ()

    def __post_init__(self) -> None:
        for field in ("capability_id", "subject_id", "runtime_id", "engine_id", "api_family", "codec"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if type(self.direction) is not MediaDirection or type(self.evidence_strength) is not EvidenceStrength or type(self.state) is not ObservationState:
            raise HardwareGenomeValidationError("media evidence fields must use closed M07 vocabularies")
        for field in ("profile", "level", "chroma_format", "input_format", "output_format"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_identifier(value, field))
        for field in ("bit_depth", "max_width", "max_height"):
            value = getattr(self, field)
            if value is not None:
                value = require_nonnegative_int(value, field)
                if value == 0:
                    raise HardwareGenomeValidationError(f"{field} must be positive when present")
                object.__setattr__(self, field, value)
        object.__setattr__(self, "observation", DiscoveryObservation.coerce(self.observation, "observation"))
        if self.observation.subject is None or self.observation.subject.subject_id != self.subject_id:
            raise HardwareGenomeIntegrityError("media capability must bind an exact device subject")
        if self.observation.runtime is None or self.observation.runtime.runtime_id != self.runtime_id:
            raise HardwareGenomeIntegrityError("media capability must bind an exact runtime subject")
        expected_key = f"media.{self.codec.lower()}.{self.direction.value.lower()}"
        if self.observation.fact_key != expected_key:
            raise HardwareGenomeIntegrityError("media codec/direction must match its canonical fact key")
        if self.observation.state is not self.state:
            raise HardwareGenomeIntegrityError("media state differs from its evidence observation")
        if self.state is ObservationState.OBSERVED:
            value = self.observation.value
            if not isinstance(value, Mapping) or value.get("engine_id") != self.engine_id or value.get("codec") != self.codec or value.get("direction") != self.direction.value:
                raise HardwareGenomeIntegrityError("media evidence must bind exact engine, codec and encode/decode direction")
            for field in ("profile", "level", "bit_depth", "chroma_format", "max_width", "max_height", "input_format", "output_format"):
                if field in value and value[field] != getattr(self, field):
                    raise HardwareGenomeIntegrityError(f"media field {field} differs from the admitted exact-path evidence")
        if self.state is not ObservationState.OBSERVED and any(getattr(self, key) is not None for key in ("profile", "level", "bit_depth", "chroma_format", "max_width", "max_height")):
            raise HardwareGenomeAdmissionError("non-positive media evidence cannot expose supported feature limits")
        if self.evidence_strength is EvidenceStrength.SMOKE_VERIFIED and self.observation.evidence is None:
            raise HardwareGenomeAdmissionError("media smoke verification requires bounded conformance evidence")
        interop = tuple(MediaInteropEvidence.coerce(item, "interop_evidence[]") for item in self.interop_evidence)
        if any((item.subject_id, item.runtime_id) != (self.subject_id, self.runtime_id) for item in interop):
            raise HardwareGenomeIntegrityError("media interop cannot be broadcast across subjects or runtimes")
        if interop and not any((self.engine_id, self.api_family) in {(item.source_engine_id, item.source_api), (item.target_engine_id, item.target_api)} for item in interop):
            raise HardwareGenomeIntegrityError("media interop is unrelated to this exact engine/API path")
        if len({item.interop_id for item in interop}) != len(interop):
            raise HardwareGenomeValidationError("media interop evidence ids must be unique")
        object.__setattr__(self, "interop_evidence", tuple(sorted(interop, key=lambda item: item.interop_id)))
        keys = tuple(sorted(set(require_identifier(item, "interop_keys[]") for item in self.interop_keys)))
        if keys and set(keys) != {item.interop_id for item in interop}:
            raise HardwareGenomeIntegrityError("media interop keys must exactly identify their evidence records")
        object.__setattr__(self, "interop_keys", tuple(item.interop_id for item in interop) if interop else keys)


def validate_media_capabilities(items: tuple[MediaEngineCapability, ...]) -> None:
    ids = [item.capability_id for item in items]
    if len(ids) != len(set(ids)):
        raise HardwareGenomeIntegrityError("media capability ids must be unique")
    interop_ids = [proof.interop_id for item in items for proof in item.interop_evidence]
    if len(interop_ids) != len(set(interop_ids)):
        raise HardwareGenomeIntegrityError("media interop evidence must not be duplicated across capabilities")
    for item in items:
        if item.evidence_strength is EvidenceStrength.SMOKE_VERIFIED and item.state is not ObservationState.OBSERVED:
            raise HardwareGenomeAdmissionError("failed media conformance cannot become positive capability")
