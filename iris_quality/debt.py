from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .defects import Defect, DefectSeverity
from .errors import SchemaValidationError
from .versions import require_identifier, require_text

__all__ = ["DebtRuling", "QualityDebt", "QualityDebtPolicy"]


@dataclass(frozen=True)
class QualityDebt:
    """An explicitly recorded, versioned and approvable deferral of a defect."""

    debt_id: str
    defect_id: str
    defect_class: str
    severity: DefectSeverity
    justification: str
    approved_by: str
    policy_version: str
    dimension_id: str | None = None
    zone_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "debt_id", require_identifier(self.debt_id, "debt_id"))
        object.__setattr__(self, "defect_id", require_identifier(self.defect_id, "defect_id"))
        object.__setattr__(
            self, "defect_class", require_identifier(self.defect_class, "defect_class")
        )
        object.__setattr__(self, "severity", DefectSeverity.parse(self.severity))
        object.__setattr__(
            self, "justification", require_text(self.justification, "justification", maximum=1024)
        )
        object.__setattr__(self, "approved_by", require_text(self.approved_by, "approved_by", maximum=120))
        object.__setattr__(
            self, "policy_version", require_text(self.policy_version, "policy_version", maximum=64)
        )
        if self.dimension_id is not None:
            object.__setattr__(self, "dimension_id", require_identifier(self.dimension_id, "dimension_id"))
        if self.zone_id is not None:
            object.__setattr__(self, "zone_id", require_identifier(self.zone_id, "zone_id"))
        if self.severity is DefectSeverity.OBSERVATION:
            raise SchemaValidationError(
                "OBSERVATION findings are non-blocking and cannot be recorded as quality debt"
            )

    @property
    def reference(self) -> str:
        return f"{self.debt_id}@{self.policy_version}"

    def to_payload(self) -> dict[str, Any]:
        return {
            "debt_id": self.debt_id,
            "defect_id": self.defect_id,
            "defect_class": self.defect_class,
            "severity": self.severity.value,
            "justification": self.justification,
            "approved_by": self.approved_by,
            "policy_version": self.policy_version,
            "dimension_id": self.dimension_id,
            "zone_id": self.zone_id,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> QualityDebt:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("QualityDebt must be a mapping")
        expected = {
            "debt_id",
            "defect_id",
            "defect_class",
            "severity",
            "justification",
            "approved_by",
            "policy_version",
            "dimension_id",
            "zone_id",
        }
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"QualityDebt has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"QualityDebt is missing keys: {sorted(missing)}")
        return cls(
            debt_id=payload["debt_id"],
            defect_id=payload["defect_id"],
            defect_class=payload["defect_class"],
            severity=DefectSeverity.parse(payload["severity"]),
            justification=payload["justification"],
            approved_by=payload["approved_by"],
            policy_version=payload["policy_version"],
            dimension_id=payload["dimension_id"],
            zone_id=payload["zone_id"],
        )


@dataclass(frozen=True)
class DebtRuling:
    allowed: bool
    reason: str
    debt: QualityDebt | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "debt": None if self.debt is None else self.debt.to_payload(),
        }


@dataclass(frozen=True)
class QualityDebtPolicy:
    """Which severities may be deferred, and only against a named exception class."""

    deferrable_severities: frozenset[DefectSeverity] = frozenset(
        {DefectSeverity.MAJOR, DefectSeverity.MINOR}
    )
    allowed_exception_classes: frozenset[str] = frozenset()
    require_justification: bool = True
    require_approver: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.deferrable_severities, frozenset):
            raise SchemaValidationError("deferrable_severities must be a frozenset of DefectSeverity")
        severities = frozenset(DefectSeverity.parse(item) for item in self.deferrable_severities)
        if DefectSeverity.FATAL in severities:
            raise SchemaValidationError(
                "FATAL defects can never be deferred; remove FATAL from deferrable_severities"
            )
        object.__setattr__(self, "deferrable_severities", severities)
        if not isinstance(self.allowed_exception_classes, frozenset):
            raise SchemaValidationError("allowed_exception_classes must be a frozenset of identifiers")
        classes = frozenset(
            require_identifier(item, "allowed_exception_classes[]")
            for item in self.allowed_exception_classes
        )
        object.__setattr__(self, "allowed_exception_classes", classes)
        for flag in ("require_justification", "require_approver"):
            if not isinstance(getattr(self, flag), bool):
                raise SchemaValidationError(f"{flag} must be a bool")

    def rule(self, defect: Defect, debt: QualityDebt | None) -> DebtRuling:
        if defect.severity is DefectSeverity.FATAL:
            return DebtRuling(False, "fatal_defects_are_never_deferrable", None)
        if defect.severity not in self.deferrable_severities:
            return DebtRuling(False, f"{defect.severity.value}_is_not_deferrable", None)
        if debt is None:
            return DebtRuling(False, f"no_quality_debt_recorded_for_{defect.defect_id}", None)
        if debt.defect_id != defect.defect_id or debt.defect_class != defect.defect_class:
            return DebtRuling(False, "debt_does_not_reference_this_defect", None)
        if debt.severity is not defect.severity:
            return DebtRuling(False, "debt_severity_does_not_match_defect", None)
        if (
            self.allowed_exception_classes
            and defect.defect_class not in self.allowed_exception_classes
        ):
            return DebtRuling(
                False,
                f"defect_class_{defect.defect_class}_is_not_an_allowed_exception_class",
                None,
            )
        if self.require_justification and not debt.justification.strip():
            return DebtRuling(False, "debt_requires_a_justification", None)
        if self.require_approver and not debt.approved_by.strip():
            return DebtRuling(False, "debt_requires_an_approver", None)
        return DebtRuling(True, "debt_accepted_by_policy", debt)

    def rule_all(self, defects: Iterable[Defect], debts: Iterable[QualityDebt]) -> dict[str, DebtRuling]:
        by_defect = {debt.defect_id: debt for debt in debts}
        return {defect.defect_id: self.rule(defect, by_defect.get(defect.defect_id)) for defect in defects}

    def to_payload(self) -> dict[str, Any]:
        return {
            "deferrable_severities": sorted(item.value for item in self.deferrable_severities),
            "allowed_exception_classes": sorted(self.allowed_exception_classes),
            "require_justification": self.require_justification,
            "require_approver": self.require_approver,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> QualityDebtPolicy:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("QualityDebtPolicy must be a mapping")
        expected = {
            "deferrable_severities",
            "allowed_exception_classes",
            "require_justification",
            "require_approver",
        }
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"QualityDebtPolicy has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"QualityDebtPolicy is missing keys: {sorted(missing)}")
        return cls(
            deferrable_severities=frozenset(
                DefectSeverity.parse(item) for item in payload["deferrable_severities"]
            ),
            allowed_exception_classes=frozenset(payload["allowed_exception_classes"]),
            require_justification=payload["require_justification"],
            require_approver=payload["require_approver"],
        )
