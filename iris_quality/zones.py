from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .defects import DefectSeverity
from .errors import SchemaValidationError
from .versions import require_identifier, require_text, require_unit_interval

__all__ = ["SemanticZone"]


@dataclass(frozen=True)
class SemanticZone:
    """A high-risk region that tightens existing dimensions instead of adding new ones."""

    zone_id: str
    label: str
    dimension_ids: tuple[str, ...]
    severity_overrides: Mapping[str, DefectSeverity] = field(default_factory=dict)
    minimum_confidence: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "zone_id", require_identifier(self.zone_id, "zone_id"))
        object.__setattr__(self, "label", require_text(self.label, "label", maximum=120))
        if not isinstance(self.dimension_ids, (list, tuple)) or not self.dimension_ids:
            raise SchemaValidationError("dimension_ids must be a non-empty list of identifiers")
        identifiers = tuple(
            require_identifier(item, "dimension_ids[]") for item in self.dimension_ids
        )
        duplicates = sorted({name for name in identifiers if identifiers.count(name) > 1})
        if duplicates:
            raise SchemaValidationError(f"dimension_ids contains duplicates: {duplicates}")
        object.__setattr__(self, "dimension_ids", identifiers)
        if not isinstance(self.severity_overrides, Mapping):
            raise SchemaValidationError("severity_overrides must be a mapping")
        overrides: dict[str, DefectSeverity] = {}
        for key, value in self.severity_overrides.items():
            defect_class = require_identifier(key, "severity_overrides key")
            overrides[defect_class] = DefectSeverity.parse(value)
        object.__setattr__(self, "severity_overrides", overrides)
        if self.minimum_confidence is not None:
            object.__setattr__(
                self, "minimum_confidence", require_unit_interval(self.minimum_confidence, "minimum_confidence")
            )

    def effective_severity(self, defect_class: str, declared: DefectSeverity) -> DefectSeverity:
        """Zone policy may only make a severity stricter, never relax contract policy."""

        override = self.severity_overrides.get(defect_class)
        if override is None:
            return declared
        return override if override.rank >= declared.rank else declared

    def to_payload(self) -> dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "label": self.label,
            "dimension_ids": list(self.dimension_ids),
            "severity_overrides": {key: value.value for key, value in self.severity_overrides.items()},
            "minimum_confidence": self.minimum_confidence,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> SemanticZone:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("SemanticZone must be a mapping")
        expected = {"zone_id", "label", "dimension_ids", "severity_overrides", "minimum_confidence"}
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"SemanticZone has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"SemanticZone is missing keys: {sorted(missing)}")
        overrides = payload["severity_overrides"]
        if not isinstance(overrides, Mapping):
            raise SchemaValidationError("severity_overrides must be a mapping")
        return cls(
            zone_id=payload["zone_id"],
            label=payload["label"],
            dimension_ids=tuple(payload["dimension_ids"]),
            severity_overrides={
                key: DefectSeverity.parse(value) for key, value in overrides.items()
            },
            minimum_confidence=payload["minimum_confidence"],
        )
