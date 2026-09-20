from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Optional

from .errors import SchemaValidationError
from .evidence import EvidenceRef
from .versions import require_identifier, require_text

__all__ = ["DefectSeverity", "Defect", "defects_by_class"]


class DefectSeverity(Enum):
    """Severity ranking is a policy input, never a way to average away a hard gate."""

    FATAL = "FATAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    OBSERVATION = "OBSERVATION"

    @property
    def rank(self) -> int:
        return _SEVERITY_RANK[self]

    @classmethod
    def parse(cls, value: Any) -> DefectSeverity:
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise SchemaValidationError(
                f"severity must be one of {sorted(item.value for item in cls)}, got {value!r}"
            )
        try:
            return cls(value.strip().upper())
        except ValueError as error:
            raise SchemaValidationError(
                f"severity must be one of {sorted(item.value for item in cls)}"
            ) from error


_SEVERITY_RANK: dict[DefectSeverity, int] = {
    DefectSeverity.FATAL: 4,
    DefectSeverity.MAJOR: 3,
    DefectSeverity.MINOR: 2,
    DefectSeverity.OBSERVATION: 1,
}


@dataclass(frozen=True)
class Defect:
    """A concrete finding whose ``defect_class`` is matched against the contract policy."""

    defect_id: str
    defect_class: str
    severity: DefectSeverity
    summary: str
    dimension_id: Optional[str] = None
    zone_id: Optional[str] = None
    evidence: tuple[EvidenceRef, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "defect_id", require_identifier(self.defect_id, "defect_id"))
        object.__setattr__(
            self, "defect_class", require_identifier(self.defect_class, "defect_class")
        )
        object.__setattr__(self, "severity", DefectSeverity.parse(self.severity))
        object.__setattr__(self, "summary", require_text(self.summary, "summary", maximum=512))
        if self.dimension_id is not None:
            object.__setattr__(self, "dimension_id", require_identifier(self.dimension_id, "dimension_id"))
        if self.zone_id is not None:
            object.__setattr__(self, "zone_id", require_identifier(self.zone_id, "zone_id"))
        if not isinstance(self.evidence, tuple):
            raise SchemaValidationError("evidence must be a tuple of EvidenceRef")
        for item in self.evidence:
            if not isinstance(item, EvidenceRef):
                raise SchemaValidationError("evidence entries must be EvidenceRef")
        identifiers = [item.evidence_id for item in self.evidence]
        if len(identifiers) != len(set(identifiers)):
            raise SchemaValidationError("defect evidence ids must be unique")

    def to_payload(self) -> dict[str, Any]:
        return {
            "defect_id": self.defect_id,
            "defect_class": self.defect_class,
            "severity": self.severity.value,
            "summary": self.summary,
            "dimension_id": self.dimension_id,
            "zone_id": self.zone_id,
            "evidence": [item.to_payload() for item in self.evidence],
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Defect:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("Defect must be a mapping")
        expected = {
            "defect_id",
            "defect_class",
            "severity",
            "summary",
            "dimension_id",
            "zone_id",
            "evidence",
        }
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"Defect has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"Defect is missing keys: {sorted(missing)}")
        evidence = payload["evidence"]
        if not isinstance(evidence, list):
            raise SchemaValidationError("Defect evidence must be a list")
        return cls(
            defect_id=payload["defect_id"],
            defect_class=payload["defect_class"],
            severity=DefectSeverity.parse(payload["severity"]),
            summary=payload["summary"],
            dimension_id=payload["dimension_id"],
            zone_id=payload["zone_id"],
            evidence=tuple(EvidenceRef.from_payload(item) for item in evidence),
        )


def defects_by_class(defects: Iterable[Defect]) -> dict[str, list[Defect]]:
    grouped: dict[str, list[Defect]] = {}
    for defect in defects:
        grouped.setdefault(defect.defect_class, []).append(defect)
    for bucket in grouped.values():
        bucket.sort(key=lambda item: item.defect_id)
    return grouped
