from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional

from .errors import SchemaValidationError
from .evidence import EvidenceRef
from .versions import ComponentVersion, require_identifier, require_text, require_unit_interval

__all__ = [
    "GateState",
    "UncertaintyState",
    "FidelityDimension",
    "DimensionAssessment",
    "DimensionRegistry",
    "CANONICAL_FIDELITY_VECTOR",
    "DEFAULT_DIMENSION_REGISTRY",
    "DIMENSION_REGISTRY_VERSION",
    "MAX_EXTENSION_DIMENSIONS",
]

DIMENSION_REGISTRY_VERSION = "m01-dimension-registry-v1"
MAX_EXTENSION_DIMENSIONS = 64

CANONICAL_FIDELITY_VECTOR: tuple[str, ...] = (
    "intent-adherence",
    "identity-fidelity",
    "anatomy-plausibility",
    "geometry-integrity",
    "silhouette-readability",
    "composition-framing",
    "material-pbr-fidelity",
    "texture-detail-fidelity",
    "lighting-shadow-fidelity",
    "color-value-hierarchy",
    "style-brand-consistency",
    "motion-deformation-quality",
    "temporal-continuity",
    "vfx-clarity-integration",
    "technical-integrity",
    "target-platform-fitness",
    "cross-modal-consistency",
    "perceptual-finish",
)


class GateState(Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNVERIFIED = "UNVERIFIED"
    PASS = "PASS"
    FAIL = "FAIL"

    @classmethod
    def parse(cls, value: Any) -> GateState:
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise SchemaValidationError(f"gate must be one of {sorted(item.value for item in cls)}")
        try:
            return cls(value.strip().upper())
        except ValueError as error:
            raise SchemaValidationError(
                f"gate must be one of {sorted(item.value for item in cls)}"
            ) from error


class UncertaintyState(Enum):
    """Low confidence maps to UNKNOWN or HUMAN_REVIEW, never to an invented score verdict."""

    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    HUMAN_REVIEW = "HUMAN_REVIEW"

    @classmethod
    def parse(cls, value: Any) -> UncertaintyState:
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise SchemaValidationError(
                f"uncertainty must be one of {sorted(item.value for item in cls)}"
            )
        try:
            return cls(value.strip().upper())
        except ValueError as error:
            raise SchemaValidationError(
                f"uncertainty must be one of {sorted(item.value for item in cls)}"
            ) from error


@dataclass(frozen=True)
class FidelityDimension:
    """One axis of the Fidelity Vector; domain neutrality is structural, not nominal."""

    dimension_id: str
    label: str
    core: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "dimension_id", require_identifier(self.dimension_id, "dimension_id"))
        object.__setattr__(self, "label", require_text(self.label, "label", maximum=120))
        if not isinstance(self.core, bool):
            raise SchemaValidationError("core must be a bool")

    def to_payload(self) -> dict[str, Any]:
        return {"dimension_id": self.dimension_id, "label": self.label, "core": self.core}

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> FidelityDimension:
        _require_keys(payload, {"dimension_id", "label", "core"}, "FidelityDimension")
        return cls(
            dimension_id=payload["dimension_id"],
            label=payload["label"],
            core=payload["core"],
        )


@dataclass(frozen=True)
class MeasurementRange:
    minimum: float
    maximum: float

    def __post_init__(self) -> None:
        for name, value in (("minimum", self.minimum), ("maximum", self.maximum)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise SchemaValidationError(f"{name} must be a number")
        if float(self.minimum) > float(self.maximum):
            raise SchemaValidationError(
                f"range minimum {self.minimum} must not exceed maximum {self.maximum}"
            )

    def to_payload(self) -> dict[str, Any]:
        return {"minimum": float(self.minimum), "maximum": float(self.maximum)}

    @classmethod
    def from_payload(cls, payload: Any) -> MeasurementRange:
        if isinstance(payload, MeasurementRange):
            return payload
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("range must be a mapping with minimum and maximum")
        _require_keys(payload, {"minimum", "maximum"}, "MeasurementRange")
        return cls(minimum=payload["minimum"], maximum=payload["maximum"])


@dataclass(frozen=True)
class DimensionAssessment:
    """Value/range + confidence + evidence + evaluator version + gate state, per S01."""

    dimension_id: str
    gate: GateState
    uncertainty: UncertaintyState
    evaluator: ComponentVersion
    value: Optional[float] = None
    value_range: Optional[MeasurementRange] = None
    confidence: Optional[float] = None
    evidence: tuple[EvidenceRef, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "dimension_id", require_identifier(self.dimension_id, "dimension_id"))
        object.__setattr__(self, "gate", GateState.parse(self.gate))
        object.__setattr__(self, "uncertainty", UncertaintyState.parse(self.uncertainty))
        if not isinstance(self.evaluator, ComponentVersion):
            raise SchemaValidationError("evaluator must be a ComponentVersion")
        if self.value is not None:
            if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
                raise SchemaValidationError("value must be a number or None")
            object.__setattr__(self, "value", float(self.value))
        if self.value_range is not None:
            object.__setattr__(self, "value_range", MeasurementRange.from_payload(self.value_range))
        if self.confidence is not None:
            object.__setattr__(self, "confidence", require_unit_interval(self.confidence, "confidence"))
        if not isinstance(self.evidence, tuple):
            raise SchemaValidationError("evidence must be a tuple of EvidenceRef")
        for item in self.evidence:
            if not isinstance(item, EvidenceRef):
                raise SchemaValidationError("evidence entries must be EvidenceRef")
            if item.dimension_id is not None and item.dimension_id != self.dimension_id:
                raise SchemaValidationError(
                    f"evidence {item.evidence_id} belongs to dimension {item.dimension_id!r}, "
                    f"not {self.dimension_id!r}"
                )
        identifiers = [item.evidence_id for item in self.evidence]
        if len(identifiers) != len(set(identifiers)):
            raise SchemaValidationError("assessment evidence ids must be unique")
        if self.value is not None and self.value_range is not None:
            if not self.value_range.minimum <= self.value <= self.value_range.maximum:
                raise SchemaValidationError(
                    f"value {self.value} is outside its declared range "
                    f"[{self.value_range.minimum}, {self.value_range.maximum}]"
                )

    @property
    def evidence_count(self) -> int:
        return len(self.evidence)

    def to_payload(self) -> dict[str, Any]:
        return {
            "dimension_id": self.dimension_id,
            "gate": self.gate.value,
            "uncertainty": self.uncertainty.value,
            "evaluator": self.evaluator.to_payload(),
            "value": self.value,
            "value_range": None if self.value_range is None else self.value_range.to_payload(),
            "confidence": self.confidence,
            "evidence": [item.to_payload() for item in self.evidence],
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> DimensionAssessment:
        _require_keys(
            payload,
            {
                "dimension_id",
                "gate",
                "uncertainty",
                "evaluator",
                "value",
                "value_range",
                "confidence",
                "evidence",
            },
            "DimensionAssessment",
        )
        evidence = payload["evidence"]
        if not isinstance(evidence, list):
            raise SchemaValidationError("evidence must be a list")
        value_range = payload["value_range"]
        return cls(
            dimension_id=payload["dimension_id"],
            gate=GateState.parse(payload["gate"]),
            uncertainty=UncertaintyState.parse(payload["uncertainty"]),
            evaluator=ComponentVersion.from_payload(payload["evaluator"]),
            value=payload["value"],
            value_range=None if value_range is None else MeasurementRange.from_payload(value_range),
            confidence=payload["confidence"],
            evidence=tuple(EvidenceRef.from_payload(item) for item in evidence),
        )


def _require_keys(payload: Any, expected: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise SchemaValidationError(f"{label} must be a mapping")
    unexpected = set(payload) - expected
    if unexpected:
        raise SchemaValidationError(f"{label} has unknown keys: {sorted(unexpected)}")
    missing = expected - set(payload)
    if missing:
        raise SchemaValidationError(f"{label} is missing keys: {sorted(missing)}")
    return payload


def canonical_dimension(dimension_id: str) -> FidelityDimension:
    """Build a core Fidelity Vector dimension from the frozen S01 vocabulary."""

    identifier = require_identifier(dimension_id, "dimension_id")
    if identifier not in CANONICAL_FIDELITY_VECTOR:
        raise SchemaValidationError(
            f"{identifier!r} is not part of the canonical Fidelity Vector; register it through a "
            "domain profile instead"
        )
    return FidelityDimension(dimension_id=identifier, label=identifier.replace("-", " ").title())


@dataclass(frozen=True)
class DimensionRegistry:
    """The admitted dimension set: 18 frozen built-ins plus explicitly registered extensions.

    The approved forward-compatibility scan promises non-visual Fidelity Vector growth without
    touching core state-machine semantics, so an extension is data declared here rather than a new
    constant in ``decision.py``.
    """

    extension_dimensions: tuple[FidelityDimension, ...] = ()
    version: str = DIMENSION_REGISTRY_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.extension_dimensions, tuple):
            raise SchemaValidationError("extension_dimensions must be a tuple of FidelityDimension")
        extensions = tuple(self.extension_dimensions)
        if len(extensions) > MAX_EXTENSION_DIMENSIONS:
            raise SchemaValidationError(
                f"a dimension registry admits at most {MAX_EXTENSION_DIMENSIONS} extensions, "
                f"got {len(extensions)}"
            )
        identifiers = [item.dimension_id for item in extensions]
        if len(identifiers) != len(set(identifiers)):
            raise SchemaValidationError("extension dimension ids must be unique")
        shadowing = sorted(set(identifiers) & set(CANONICAL_FIDELITY_VECTOR))
        if shadowing:
            raise SchemaValidationError(
                f"canonical dimensions are built-ins and cannot be re-registered: {shadowing}"
            )
        for item in extensions:
            if not isinstance(item, FidelityDimension):
                raise SchemaValidationError("extension_dimensions entries must be FidelityDimension")
            if item.core:
                raise SchemaValidationError(
                    f"extension dimension {item.dimension_id} must declare core=False; "
                    "only the frozen S01 vector is core"
                )
        object.__setattr__(self, "extension_dimensions", extensions)
        object.__setattr__(
            self, "version", require_text(self.version, "version", maximum=64)
        )

    @property
    def dimension_ids(self) -> tuple[str, ...]:
        return CANONICAL_FIDELITY_VECTOR + tuple(
            item.dimension_id for item in sorted(self.extension_dimensions, key=lambda x: x.dimension_id)
        )

    @property
    def extension_ids(self) -> tuple[str, ...]:
        return tuple(item.dimension_id for item in self.extension_dimensions)

    def admits(self, dimension_id: str) -> bool:
        return dimension_id in self.dimension_ids

    def resolve(self, dimension_id: str) -> FidelityDimension:
        identifier = require_identifier(dimension_id, "dimension_id")
        if identifier in CANONICAL_FIDELITY_VECTOR:
            return canonical_dimension(identifier)
        for item in self.extension_dimensions:
            if item.dimension_id == identifier:
                return item
        raise SchemaValidationError(
            f"{identifier!r} is not an admitted dimension; register it in the contract's "
            "dimension_registry instead of inventing it at evaluation time"
        )

    def require_admitted(self, dimension_ids: Sequence[str], owner: str) -> tuple[str, ...]:
        outside = sorted(set(dimension_ids) - set(self.dimension_ids))
        if outside:
            raise SchemaValidationError(
                f"{owner} references dimensions outside the registry {self.version}: {outside}"
            )
        return tuple(dimension_ids)

    def to_payload(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "extension_dimensions": [item.to_payload() for item in self.extension_dimensions],
        }

    @classmethod
    def from_payload(cls, payload: Any) -> "DimensionRegistry":
        if isinstance(payload, cls):
            return payload
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("DimensionRegistry must be a mapping")
        _require_keys(payload, {"version", "extension_dimensions"}, "DimensionRegistry")
        if payload["version"] != DIMENSION_REGISTRY_VERSION:
            raise SchemaValidationError(
                f"unsupported dimension registry version {payload['version']!r}; this kernel "
                f"admits {DIMENSION_REGISTRY_VERSION!r}"
            )
        extensions = payload["extension_dimensions"]
        if not isinstance(extensions, list):
            raise SchemaValidationError("extension_dimensions must be a list")
        return cls(
            extension_dimensions=tuple(
                FidelityDimension.from_payload(item) for item in extensions
            ),
            version=payload["version"],
        )


DEFAULT_DIMENSION_REGISTRY = DimensionRegistry()


def dimension_ids(assessments: tuple[DimensionAssessment, ...]) -> tuple[str, ...]:
    return tuple(item.dimension_id for item in assessments)
