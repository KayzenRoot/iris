"""Dimensional precision evidence; M07 never decides workload quality."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M07Record
from .enums import BackendFamily, CapabilityDimension, ObservationState, PrecisionFamily
from .errors import HardwareGenomeIntegrityError, HardwareGenomeValidationError
from .evidence import DiscoveryObservation
from .versions import require_identifier

__all__ = ["PrecisionFeature", "precision_evidence_dimensions"]


@dataclass(frozen=True)
class PrecisionFeature(M07Record):
    feature_id: str
    subject_id: str
    runtime_id: str
    backend: BackendFamily
    family: PrecisionFamily
    dimensions: tuple[tuple[CapabilityDimension, ObservationState], ...]
    evidence_observation_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in ("feature_id", "subject_id", "runtime_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if type(self.backend) is not BackendFamily or type(self.family) is not PrecisionFamily:
            raise HardwareGenomeValidationError("precision backend/family must use closed M07 vocabularies")
        dimensions = tuple(self.dimensions)
        if any(type(key) is not CapabilityDimension or type(value) is not ObservationState for key, value in dimensions):
            raise HardwareGenomeValidationError("precision dimensions require explicit typed evidence states")
        if {key for key, _ in dimensions} != set(CapabilityDimension) or len(dimensions) != len(CapabilityDimension):
            raise HardwareGenomeValidationError("precision support must remain dimensional across all evidence axes")
        object.__setattr__(self, "dimensions", tuple(sorted(dimensions, key=lambda item: item[0].value)))
        ids = tuple(require_identifier(item, "evidence_observation_ids[]") for item in self.evidence_observation_ids)
        if not ids or len(ids) != len(set(ids)):
            raise HardwareGenomeValidationError("precision features require unique evidence observations")
        object.__setattr__(self, "evidence_observation_ids", tuple(sorted(ids)))

    def state_for(self, dimension: CapabilityDimension) -> ObservationState:
        return dict(self.dimensions)[dimension]

    def validate_observations(self, observations: tuple[DiscoveryObservation, ...]) -> None:
        by_id = {item.observation_id: item for item in observations}
        selected = [by_id.get(item) for item in self.evidence_observation_ids]
        if any(item is None for item in selected):
            raise HardwareGenomeIntegrityError("precision feature references absent evidence")
        for item in selected:
            if item is not None and (item.subject is None or item.subject.subject_id != self.subject_id or item.runtime is None or item.runtime.runtime_id != self.runtime_id):
                raise HardwareGenomeIntegrityError("precision evidence must bind exact subject and runtime")


def precision_evidence_dimensions(
    *, representation: ObservationState,
    arithmetic: ObservationState,
    acceleration_reported: ObservationState,
    accumulation: ObservationState,
    conversion: ObservationState,
    framework_exposure: ObservationState,
    conformance: ObservationState,
) -> tuple[tuple[CapabilityDimension, ObservationState], ...]:
    values = {
        CapabilityDimension.REPRESENTATION: representation,
        CapabilityDimension.ARITHMETIC: arithmetic,
        CapabilityDimension.ACCELERATION_REPORTED: acceleration_reported,
        CapabilityDimension.ACCUMULATION: accumulation,
        CapabilityDimension.CONVERSION: conversion,
        CapabilityDimension.FRAMEWORK_EXPOSURE: framework_exposure,
        CapabilityDimension.CONFORMANCE: conformance,
    }
    if any(type(value) is not ObservationState for value in values.values()):
        raise HardwareGenomeValidationError("precision axes require explicit ObservationState values")
    return tuple(sorted(values.items(), key=lambda item: item[0].value))
