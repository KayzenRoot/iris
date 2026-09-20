from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from .debt import QualityDebtPolicy
from .dimensions import CANONICAL_FIDELITY_VECTOR
from .errors import SchemaValidationError
from .versions import (
    CONTRACT_VERSION,
    ComponentVersion,
    require_identifier,
    require_supported_version,
    require_text,
    require_unique,
)
from .zones import SemanticZone

__all__ = [
    "QualityClass",
    "PromotionRule",
    "FidelityContract",
    "SUPPORTED_QUALITY_CLASSES",
    "DEFECT_CLASS_FIELDS",
]


class QualityClass(Enum):
    """The S02 output ladder. Higher classes inherit strictly more evidence obligations."""

    DRAFT = "DRAFT"
    PREVIEW = "PREVIEW"
    REVIEW = "REVIEW"
    MASTER = "MASTER"
    ARCHIVAL_MASTER = "ARCHIVAL_MASTER"

    @property
    def ladder_rank(self) -> int:
        return _LADDER[self]

    @classmethod
    def parse(cls, value: Any) -> QualityClass:
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise SchemaValidationError(
                f"output_class must be one of {sorted(item.value for item in cls)}, got {value!r}"
            )
        try:
            return cls(value.strip().upper())
        except ValueError as error:
            raise SchemaValidationError(
                f"output_class must be one of {sorted(item.value for item in cls)}"
            ) from error

    def next_class(self) -> QualityClass | None:
        ordered = sorted(_LADDER, key=lambda item: item.ladder_rank)
        position = ordered.index(self)
        return ordered[position + 1] if position + 1 < len(ordered) else None

    @classmethod
    def ladder(cls) -> tuple[QualityClass, ...]:
        return tuple(sorted(_LADDER, key=lambda item: item.ladder_rank))


_LADDER: dict[QualityClass, int] = {
    QualityClass.DRAFT: 0,
    QualityClass.PREVIEW: 1,
    QualityClass.REVIEW: 2,
    QualityClass.MASTER: 3,
    QualityClass.ARCHIVAL_MASTER: 4,
}

SUPPORTED_QUALITY_CLASSES: frozenset[str] = frozenset(item.value for item in QualityClass)

DEFECT_CLASS_FIELDS: tuple[tuple[str, str], ...] = (
    ("fatal_defect_classes", "FATAL"),
    ("major_defect_classes", "MAJOR"),
    ("minor_defect_classes", "MINOR"),
    ("observation_defect_classes", "OBSERVATION"),
)


@dataclass(frozen=True)
class PromotionRule:
    """What a candidate must prove before it may carry ``target_class``."""

    target_class: QualityClass
    required_dimension_ids: tuple[str, ...]
    minimum_evidence_count: int = 1
    minimum_confidence: float = 0.0
    requires_human_review: bool = False
    hard_gate_dimension_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        target = QualityClass.parse(self.target_class)
        if target is QualityClass.DRAFT:
            raise SchemaValidationError("DRAFT is an entry class and cannot be a promotion target")
        object.__setattr__(self, "target_class", target)
        object.__setattr__(
            self, "required_dimension_ids", require_unique(self.required_dimension_ids, "required_dimension_ids")
        )
        object.__setattr__(
            self, "hard_gate_dimension_ids", require_unique(self.hard_gate_dimension_ids, "hard_gate_dimension_ids")
        )
        if isinstance(self.minimum_evidence_count, bool) or not isinstance(self.minimum_evidence_count, int):
            raise SchemaValidationError("minimum_evidence_count must be an integer")
        if self.minimum_evidence_count < 0:
            raise SchemaValidationError("minimum_evidence_count must not be negative")
        if isinstance(self.minimum_confidence, bool) or not isinstance(
            self.minimum_confidence, (int, float)
        ):
            raise SchemaValidationError("minimum_confidence must be a number in [0, 1]")
        if not 0.0 <= float(self.minimum_confidence) <= 1.0:
            raise SchemaValidationError(
                f"minimum_confidence must be within [0, 1], got {self.minimum_confidence}"
            )
        object.__setattr__(self, "minimum_confidence", float(self.minimum_confidence))
        if not isinstance(self.requires_human_review, bool):
            raise SchemaValidationError("requires_human_review must be a bool")

    def to_payload(self) -> dict[str, Any]:
        return {
            "target_class": self.target_class.value,
            "required_dimension_ids": list(self.required_dimension_ids),
            "hard_gate_dimension_ids": list(self.hard_gate_dimension_ids),
            "minimum_evidence_count": self.minimum_evidence_count,
            "minimum_confidence": self.minimum_confidence,
            "requires_human_review": self.requires_human_review,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> PromotionRule:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("PromotionRule must be a mapping")
        expected = {
            "target_class",
            "required_dimension_ids",
            "hard_gate_dimension_ids",
            "minimum_evidence_count",
            "minimum_confidence",
            "requires_human_review",
        }
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"PromotionRule has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"PromotionRule is missing keys: {sorted(missing)}")
        return cls(
            target_class=QualityClass.parse(payload["target_class"]),
            required_dimension_ids=tuple(payload["required_dimension_ids"]),
            minimum_evidence_count=payload["minimum_evidence_count"],
            minimum_confidence=payload["minimum_confidence"],
            requires_human_review=payload["requires_human_review"],
            hard_gate_dimension_ids=tuple(payload["hard_gate_dimension_ids"]),
        )


@dataclass(frozen=True)
class FidelityContract:
    """The machine-readable obligations binding one asset to its intended quality bar."""

    contract_id: str
    intent: str
    output_class: QualityClass
    dimension_ids: tuple[str, ...]
    reference_ids: tuple[str, ...] = ()
    fatal_defect_classes: tuple[str, ...] = ()
    major_defect_classes: tuple[str, ...] = ()
    minor_defect_classes: tuple[str, ...] = ()
    observation_defect_classes: tuple[str, ...] = ()
    evaluator_set: tuple[ComponentVersion, ...] = ()
    target_platform: str = "unspecified"
    camera_profile: str = "unspecified"
    delivery_profile: str = "unspecified"
    zones: tuple[SemanticZone, ...] = ()
    promotion_rules: tuple[PromotionRule, ...] = ()
    human_review_dimension_ids: tuple[str, ...] = ()
    debt_policy: QualityDebtPolicy = field(default_factory=QualityDebtPolicy)
    max_judge_disagreement: float = 0.35
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", require_identifier(self.contract_id, "contract_id"))
        object.__setattr__(self, "intent", require_text(self.intent, "intent", maximum=1024))
        object.__setattr__(self, "output_class", QualityClass.parse(self.output_class))
        object.__setattr__(
            self,
            "contract_version",
            require_supported_version("contract", self.contract_version, _SUPPORTED_CONTRACTS),
        )
        dimensions = require_unique(self.dimension_ids, "dimension_ids")
        if not dimensions:
            raise SchemaValidationError("dimension_ids must list at least one applicable dimension")
        unknown = sorted(set(dimensions) - set(CANONICAL_FIDELITY_VECTOR))
        if unknown:
            raise SchemaValidationError(
                f"dimensions {unknown} are not in the canonical Fidelity Vector; register them "
                "through a domain profile"
            )
        object.__setattr__(self, "dimension_ids", dimensions)
        object.__setattr__(self, "reference_ids", require_unique(self.reference_ids, "reference_ids"))
        for name, _ in DEFECT_CLASS_FIELDS:
            object.__setattr__(self, name, require_unique(getattr(self, name), name))
        seen: dict[str, str] = {}
        for name, severity in DEFECT_CLASS_FIELDS:
            ambiguous = sorted(set(seen) & set(getattr(self, name)))
            if ambiguous:
                raise SchemaValidationError(
                    f"defect classes must be declared at exactly one severity, ambiguous: {ambiguous}"
                )
            seen.update({item: severity for item in getattr(self, name)})
        if not isinstance(self.evaluator_set, tuple):
            raise SchemaValidationError("evaluator_set must be a tuple of ComponentVersion")
        evaluators = tuple(self.evaluator_set)
        for evaluator in evaluators:
            if not isinstance(evaluator, ComponentVersion):
                raise SchemaValidationError("evaluator_set entries must be ComponentVersion")
        identifiers = [item.identifier for item in evaluators]
        if len(identifiers) != len(set(identifiers)):
            raise SchemaValidationError("evaluator_set identifiers must be unique")
        object.__setattr__(self, "evaluator_set", evaluators)
        for name in ("target_platform", "camera_profile", "delivery_profile"):
            object.__setattr__(self, name, require_text(getattr(self, name), name, maximum=120))
        if not isinstance(self.zones, tuple):
            raise SchemaValidationError("zones must be a tuple of SemanticZone")
        for zone in self.zones:
            if not isinstance(zone, SemanticZone):
                raise SchemaValidationError("zones entries must be SemanticZone")
            outside = sorted(set(zone.dimension_ids) - set(dimensions))
            if outside:
                raise SchemaValidationError(
                    f"zone {zone.zone_id} attaches dimensions outside the contract: {outside}"
                )
        zone_ids = [zone.zone_id for zone in self.zones]
        if len(zone_ids) != len(set(zone_ids)):
            raise SchemaValidationError("zone ids must be unique")
        if not isinstance(self.promotion_rules, tuple):
            raise SchemaValidationError("promotion_rules must be a tuple of PromotionRule")
        rules = tuple(self.promotion_rules)
        for rule in rules:
            if not isinstance(rule, PromotionRule):
                raise SchemaValidationError("promotion_rules entries must be PromotionRule")
            outside = sorted(set(rule.required_dimension_ids) - set(dimensions))
            if outside:
                raise SchemaValidationError(
                    f"promotion rule {rule.target_class.value} requires dimensions outside the "
                    f"contract: {outside}"
                )
            gates = sorted(set(rule.hard_gate_dimension_ids) - set(rule.required_dimension_ids))
            if gates:
                raise SchemaValidationError(
                    f"promotion rule {rule.target_class.value} hard gates must be required "
                    f"dimensions: {gates}"
                )
        targets = [rule.target_class for rule in rules]
        if len(targets) != len(set(targets)):
            raise SchemaValidationError("promotion rules must declare one rule per target class")
        ranks = [target.ladder_rank for target in targets]
        if ranks != sorted(ranks):
            raise SchemaValidationError("promotion rules must be ordered by ascending quality class")
        required_rungs = [
            rung
            for rung in QualityClass.ladder()[1:]
            if rung.ladder_rank <= self.output_class.ladder_rank
        ]
        missing_rungs = sorted(rung.value for rung in required_rungs if rung not in set(targets))
        if missing_rungs:
            raise SchemaValidationError(
                f"promotion rules must be contiguous up to {self.output_class.value}; missing rungs: "
                f"{missing_rungs}. A class the contract cannot earn must not be requested."
            )
        object.__setattr__(self, "promotion_rules", rules)
        review = require_unique(self.human_review_dimension_ids, "human_review_dimension_ids")
        stray = sorted(set(review) - set(dimensions))
        if stray:
            raise SchemaValidationError(
                f"human review requested for dimensions outside the contract: {stray}"
            )
        object.__setattr__(self, "human_review_dimension_ids", review)
        if not isinstance(self.debt_policy, QualityDebtPolicy):
            raise SchemaValidationError("debt_policy must be a QualityDebtPolicy")
        if isinstance(self.max_judge_disagreement, bool) or not isinstance(
            self.max_judge_disagreement, (int, float)
        ):
            raise SchemaValidationError("max_judge_disagreement must be a number in [0, 1]")
        if not 0.0 <= float(self.max_judge_disagreement) <= 1.0:
            raise SchemaValidationError("max_judge_disagreement must be within [0, 1]")
        object.__setattr__(self, "max_judge_disagreement", float(self.max_judge_disagreement))

    @property
    def reference(self) -> str:
        return f"{self.contract_id}@{self.contract_version}"

    def rule_for(self, target_class: QualityClass) -> PromotionRule | None:
        target = QualityClass.parse(target_class)
        return next((rule for rule in self.promotion_rules if rule.target_class is target), None)

    def zones_for_dimension(self, dimension_id: str) -> tuple[SemanticZone, ...]:
        return tuple(zone for zone in self.zones if dimension_id in zone.dimension_ids)

    def declared_severity(self, defect_class: str) -> str | None:
        for name, severity in DEFECT_CLASS_FIELDS:
            if defect_class in getattr(self, name):
                return severity
        return None

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "intent": self.intent,
            "output_class": self.output_class.value,
            "dimension_ids": list(self.dimension_ids),
            "reference_ids": list(self.reference_ids),
            "fatal_defect_classes": list(self.fatal_defect_classes),
            "major_defect_classes": list(self.major_defect_classes),
            "minor_defect_classes": list(self.minor_defect_classes),
            "observation_defect_classes": list(self.observation_defect_classes),
            "evaluator_set": [item.to_payload() for item in self.evaluator_set],
            "target_platform": self.target_platform,
            "camera_profile": self.camera_profile,
            "delivery_profile": self.delivery_profile,
            "zones": [zone.to_payload() for zone in self.zones],
            "promotion_rules": [rule.to_payload() for rule in self.promotion_rules],
            "human_review_dimension_ids": list(self.human_review_dimension_ids),
            "debt_policy": self.debt_policy.to_payload(),
            "max_judge_disagreement": self.max_judge_disagreement,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> FidelityContract:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("FidelityContract must be a mapping")
        expected = {
            "contract_id",
            "contract_version",
            "intent",
            "output_class",
            "dimension_ids",
            "reference_ids",
            "fatal_defect_classes",
            "major_defect_classes",
            "minor_defect_classes",
            "observation_defect_classes",
            "evaluator_set",
            "target_platform",
            "camera_profile",
            "delivery_profile",
            "zones",
            "promotion_rules",
            "human_review_dimension_ids",
            "debt_policy",
            "max_judge_disagreement",
        }
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"FidelityContract has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"FidelityContract is missing keys: {sorted(missing)}")
        evaluator_set: Sequence[Any] = payload["evaluator_set"]
        zones: Sequence[Any] = payload["zones"]
        rules: Sequence[Any] = payload["promotion_rules"]
        if not isinstance(evaluator_set, list) or not isinstance(zones, list):
            raise SchemaValidationError("evaluator_set and zones must be lists")
        if not isinstance(rules, list):
            raise SchemaValidationError("promotion_rules must be a list")
        return cls(
            contract_id=payload["contract_id"],
            intent=payload["intent"],
            output_class=QualityClass.parse(payload["output_class"]),
            dimension_ids=tuple(payload["dimension_ids"]),
            reference_ids=tuple(payload["reference_ids"]),
            fatal_defect_classes=tuple(payload["fatal_defect_classes"]),
            major_defect_classes=tuple(payload["major_defect_classes"]),
            minor_defect_classes=tuple(payload["minor_defect_classes"]),
            observation_defect_classes=tuple(payload["observation_defect_classes"]),
            evaluator_set=tuple(
                ComponentVersion.from_payload(item) for item in evaluator_set
            ),
            target_platform=payload["target_platform"],
            camera_profile=payload["camera_profile"],
            delivery_profile=payload["delivery_profile"],
            zones=tuple(SemanticZone.from_payload(item) for item in zones),
            promotion_rules=tuple(PromotionRule.from_payload(item) for item in rules),
            human_review_dimension_ids=tuple(payload["human_review_dimension_ids"]),
            debt_policy=QualityDebtPolicy.from_payload(payload["debt_policy"]),
            max_judge_disagreement=payload["max_judge_disagreement"],
            contract_version=payload["contract_version"],
        )


_SUPPORTED_CONTRACTS = frozenset({CONTRACT_VERSION})
