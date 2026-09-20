from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

from .contracts import FidelityContract, PromotionRule, QualityClass
from .debt import DebtRuling, QualityDebt
from .defects import Defect, DefectSeverity
from .dimensions import DimensionAssessment, GateState, UncertaintyState
from .errors import EvaluationInputError, PromotionBlockedError, SchemaValidationError
from .evidence import EvidenceRef
from .judging import JudgeResult, SubjectRef, numeric_spread
from .registry import EvaluatorAuthority
from .versions import (
    SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    ComponentVersion,
    content_digest,
    require_identifier,
    require_supported_version,
    require_text,
)
from .zones import SemanticZone

__all__ = [
    "HUMAN_DECISION_KIND",
    "DecisionOutcome",
    "Blocker",
    "EffectiveFinding",
    "DimensionOutcome",
    "QualityDecision",
    "DecisionEngine",
    "merge_assessments",
]

HUMAN_DECISION_KIND = "HUMAN_DECISION"
CONSENSUS_IDENTIFIER = "jury-consensus"


class DecisionOutcome(Enum):
    """What the kernel is allowed to claim, never a scalar quality average."""

    PROMOTED = "PROMOTED"
    NOT_PROMOTED = "NOT_PROMOTED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REJECTED = "REJECTED"

    @classmethod
    def parse(cls, value: Any) -> DecisionOutcome:
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise SchemaValidationError(
                f"outcome must be one of {sorted(item.value for item in cls)}"
            )
        try:
            return cls(value.strip().upper())
        except ValueError as error:
            raise SchemaValidationError(
                f"outcome must be one of {sorted(item.value for item in cls)}"
            ) from error


def _worst_gate(gates: Sequence[GateState]) -> GateState:
    order = (GateState.PASS, GateState.NOT_APPLICABLE, GateState.UNVERIFIED, GateState.FAIL)
    return max(gates, key=order.index)


def _worst_uncertainty(states: Sequence[UncertaintyState]) -> UncertaintyState:
    order = (UncertaintyState.KNOWN, UncertaintyState.UNKNOWN, UncertaintyState.HUMAN_REVIEW)
    return max(states, key=order.index)


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def merge_assessments(
    contract: FidelityContract,
    subject: SubjectRef,
    results: Sequence[JudgeResult],
) -> tuple[DimensionAssessment, ...]:
    """Perceptual Jury consensus: worst-case gate, min confidence, median value."""

    if not isinstance(contract, FidelityContract):
        raise SchemaValidationError("contract must be a FidelityContract")
    grouped: dict[str, list[DimensionAssessment]] = {}
    for result in sorted(results, key=lambda item: item.judge.reference):
        if result.contract_reference != contract.reference:
            raise EvaluationInputError(
                f"judge result {result.judge.reference} targets {result.contract_reference!r}, "
                f"not {contract.reference}"
            )
        if result.subject != subject:
            raise EvaluationInputError(
                f"judge result {result.judge.reference} evaluated {result.subject.reference!r}, "
                f"not {subject.reference!r}"
            )
        for assessment in result.assessments:
            if assessment.dimension_id not in contract.dimension_ids:
                raise EvaluationInputError(
                    f"judge {result.judge.reference} assessed {assessment.dimension_id!r}, "
                    f"outside contract {contract.contract_id}"
                )
            grouped.setdefault(assessment.dimension_id, []).append(assessment)
    merged: list[DimensionAssessment] = []
    for dimension_id in sorted(grouped):
        occurrences = grouped[dimension_id]
        evidence: dict[str, EvidenceRef] = {}
        for item in occurrences:
            for ref in item.evidence:
                evidence.setdefault(ref.evidence_id, ref)
        values = [item.value for item in occurrences if item.value is not None]
        confidences = [item.confidence for item in occurrences if item.confidence is not None]
        merged.append(
            DimensionAssessment(
                dimension_id=dimension_id,
                gate=_worst_gate([item.gate for item in occurrences]),
                uncertainty=_worst_uncertainty([item.uncertainty for item in occurrences]),
                evaluator=ComponentVersion(
                    CONSENSUS_IDENTIFIER,
                    content_digest([item.to_payload() for item in occurrences])[:12],
                ),
                value=None if len(values) != len(occurrences) else _median(values),
                confidence=None if not confidences else min(confidences),
                evidence=tuple(evidence[key] for key in sorted(evidence)),
            )
        )
    return tuple(merged)


@dataclass(frozen=True)
class Blocker:
    """A named, machine-readable reason a quality class was not awarded."""

    code: str
    detail: str
    target_class: Optional[str] = None
    dimension_id: Optional[str] = None
    defect_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", require_identifier(self.code, "code"))
        object.__setattr__(self, "detail", require_text(self.detail, "detail", maximum=512))
        if self.target_class is not None:
            object.__setattr__(
                self, "target_class", require_text(self.target_class, "target_class", maximum=64)
            )
        if self.dimension_id is not None:
            object.__setattr__(
                self, "dimension_id", require_identifier(self.dimension_id, "dimension_id")
            )
        if self.defect_id is not None:
            object.__setattr__(self, "defect_id", require_identifier(self.defect_id, "defect_id"))

    def sort_key(self) -> tuple[str, str, str, str]:
        return (
            self.target_class or "",
            self.dimension_id or "",
            self.code,
            self.defect_id or "",
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "detail": self.detail,
            "target_class": self.target_class,
            "dimension_id": self.dimension_id,
            "defect_id": self.defect_id,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Blocker:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("Blocker must be a mapping")
        expected = {"code", "detail", "target_class", "dimension_id", "defect_id"}
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"Blocker has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"Blocker is missing keys: {sorted(missing)}")
        return cls(
            code=payload["code"],
            detail=payload["detail"],
            target_class=payload["target_class"],
            dimension_id=payload["dimension_id"],
            defect_id=payload["defect_id"],
        )


@dataclass(frozen=True)
class EffectiveFinding:
    """A defect after contract and zone policy, plus how its debt ruling resolved."""

    defect_id: str
    defect_class: str
    contract_severity: DefectSeverity
    reported_severity: DefectSeverity
    effective_severity: DefectSeverity
    zone_ids: tuple[str, ...]
    dimension_id: Optional[str]
    deferred: bool
    debt_id: Optional[str]
    debt_note: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "defect_id": self.defect_id,
            "defect_class": self.defect_class,
            "contract_severity": self.contract_severity.value,
            "reported_severity": self.reported_severity.value,
            "effective_severity": self.effective_severity.value,
            "zone_ids": list(self.zone_ids),
            "dimension_id": self.dimension_id,
            "deferred": self.deferred,
            "debt_id": self.debt_id,
            "debt_note": self.debt_note,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> EffectiveFinding:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("EffectiveFinding must be a mapping")
        expected = {
            "defect_id",
            "defect_class",
            "contract_severity",
            "reported_severity",
            "effective_severity",
            "zone_ids",
            "dimension_id",
            "deferred",
            "debt_id",
            "debt_note",
        }
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"EffectiveFinding has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"EffectiveFinding is missing keys: {sorted(missing)}")
        zone_ids = payload["zone_ids"]
        if not isinstance(zone_ids, list):
            raise SchemaValidationError("zone_ids must be a list")
        return cls(
            defect_id=payload["defect_id"],
            defect_class=payload["defect_class"],
            contract_severity=DefectSeverity.parse(payload["contract_severity"]),
            reported_severity=DefectSeverity.parse(payload["reported_severity"]),
            effective_severity=DefectSeverity.parse(payload["effective_severity"]),
            zone_ids=tuple(zone_ids),
            dimension_id=payload["dimension_id"],
            deferred=payload["deferred"],
            debt_id=payload["debt_id"],
            debt_note=payload["debt_note"],
        )


@dataclass(frozen=True)
class DimensionOutcome:
    """The audited state of one contract dimension at decision time."""

    dimension_id: str
    gate: str
    uncertainty: str
    evidence_count: int
    confidence: Optional[float]
    zone_ids: tuple[str, ...]
    evaluated_by: tuple[str, ...]
    human_decision_recorded: bool
    human_review_requested_by: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "human_review_requested_by",
            tuple(sorted(set(self.human_review_requested_by))),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "dimension_id": self.dimension_id,
            "gate": self.gate,
            "uncertainty": self.uncertainty,
            "evidence_count": self.evidence_count,
            "confidence": self.confidence,
            "zone_ids": list(self.zone_ids),
            "evaluated_by": list(self.evaluated_by),
            "human_decision_recorded": self.human_decision_recorded,
            "human_review_requested_by": list(self.human_review_requested_by),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> DimensionOutcome:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("DimensionOutcome must be a mapping")
        expected = {
            "dimension_id",
            "gate",
            "uncertainty",
            "evidence_count",
            "confidence",
            "zone_ids",
            "evaluated_by",
            "human_decision_recorded",
            "human_review_requested_by",
        }
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"DimensionOutcome has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"DimensionOutcome is missing keys: {sorted(missing)}")
        lists = {
            key: payload[key]
            for key in ("zone_ids", "evaluated_by", "human_review_requested_by")
        }
        for key, value in lists.items():
            if not isinstance(value, list):
                raise SchemaValidationError(f"{key} must be a list")
        return cls(
            dimension_id=payload["dimension_id"],
            gate=payload["gate"],
            uncertainty=payload["uncertainty"],
            evidence_count=payload["evidence_count"],
            confidence=payload["confidence"],
            zone_ids=tuple(lists["zone_ids"]),
            evaluated_by=tuple(lists["evaluated_by"]),
            human_decision_recorded=payload["human_decision_recorded"],
            human_review_requested_by=tuple(lists["human_review_requested_by"]),
        )


@dataclass(frozen=True)
class QualityDecision:
    """The durable, replayable record of what the kernel will and will not certify."""

    schema_version: str
    engine: ComponentVersion
    contract_id: str
    contract_version: str
    subject: SubjectRef
    requested_class: QualityClass
    awarded_class: QualityClass
    outcome: DecisionOutcome
    requires_human_review: bool
    dimensions: tuple[DimensionOutcome, ...]
    findings: tuple[EffectiveFinding, ...]
    blockers: tuple[Blocker, ...]
    disagreements: tuple[float, ...]
    judge_references: tuple[str, ...]
    accepted_debt_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            require_supported_version("schema", self.schema_version, SUPPORTED_SCHEMA_VERSIONS),
        )
        if not isinstance(self.engine, ComponentVersion):
            raise SchemaValidationError("engine must be a ComponentVersion")
        object.__setattr__(self, "contract_id", require_identifier(self.contract_id, "contract_id"))
        object.__setattr__(
            self,
            "contract_version",
            require_text(self.contract_version, "contract_version", maximum=64),
        )
        if not isinstance(self.subject, SubjectRef):
            raise SchemaValidationError("subject must be a SubjectRef")
        object.__setattr__(self, "requested_class", QualityClass.parse(self.requested_class))
        object.__setattr__(self, "awarded_class", QualityClass.parse(self.awarded_class))
        object.__setattr__(self, "outcome", DecisionOutcome.parse(self.outcome))
        if not isinstance(self.requires_human_review, bool):
            raise SchemaValidationError("requires_human_review must be a bool")
        for name in (
            "dimensions",
            "findings",
            "blockers",
            "disagreements",
            "judge_references",
            "accepted_debt_ids",
        ):
            if not isinstance(getattr(self, name), tuple):
                raise SchemaValidationError(f"{name} must be a tuple")
        if self.awarded_class.ladder_rank > self.requested_class.ladder_rank:
            raise SchemaValidationError("awarded class cannot outrank the requested class")
        if self.outcome is DecisionOutcome.PROMOTED and self.awarded_class is not self.requested_class:
            raise SchemaValidationError("PROMOTED requires the awarded class to equal the request")
        if self.outcome is DecisionOutcome.PROMOTED and self.blockers:
            raise SchemaValidationError(
                "a promoted decision cannot carry unresolved blockers; the ladder stopped early "
                "without reporting why"
            )
        if self.outcome is not DecisionOutcome.PROMOTED and not self.blockers:
            raise SchemaValidationError(
                f"{self.outcome.value} requires at least one named blocker; silence is never a verdict"
            )
        if (
            self.outcome is DecisionOutcome.REJECTED
            and self.awarded_class is not QualityClass.DRAFT
        ):
            raise SchemaValidationError("a rejected decision cannot carry any class above DRAFT")
        if self.outcome is DecisionOutcome.HUMAN_REVIEW and not self.requires_human_review:
            raise SchemaValidationError("HUMAN_REVIEW outcome requires the human review flag")
        bypassed = sorted(
            item.defect_id
            for item in self.findings
            if item.effective_severity is DefectSeverity.FATAL and item.deferred
        )
        if bypassed:
            raise SchemaValidationError(
                f"an effective FATAL finding can never be deferred, but {bypassed} is recorded as "
                "deferred; the Critical Defect Firewall cannot be carried by quality debt"
            )
        if self.blockers != tuple(sorted(self.blockers, key=Blocker.sort_key)):
            raise SchemaValidationError("blockers must be stored in canonical order")
        if self.findings != tuple(sorted(self.findings, key=lambda item: item.defect_id)):
            raise SchemaValidationError("findings must be ordered by defect id")
        if [item.dimension_id for item in self.dimensions] != sorted(
            item.dimension_id for item in self.dimensions
        ):
            raise SchemaValidationError("dimension outcomes must be ordered by dimension id")

    @property
    def contract_reference(self) -> str:
        return f"{self.contract_id}@{self.contract_version}"

    @property
    def content_sha256(self) -> str:
        return content_digest(self.to_payload())

    @property
    def blocker_codes(self) -> tuple[str, ...]:
        return tuple(item.code for item in self.blockers)

    def require_promotable(self) -> "QualityDecision":
        """Callers that would relabel an asset use this instead of trusting a score."""

        if self.outcome is not DecisionOutcome.PROMOTED:
            raise PromotionBlockedError(
                f"{self.contract_reference} for {self.subject.reference} awarded "
                f"{self.awarded_class.value}, not {self.requested_class.value}: "
                f"{', '.join(sorted(set(self.blocker_codes))) or 'no blocker recorded'}"
            )
        return self

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine": self.engine.to_payload(),
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "subject": self.subject.to_payload(),
            "requested_class": self.requested_class.value,
            "awarded_class": self.awarded_class.value,
            "outcome": self.outcome.value,
            "requires_human_review": self.requires_human_review,
            "dimensions": [item.to_payload() for item in self.dimensions],
            "findings": [item.to_payload() for item in self.findings],
            "blockers": [item.to_payload() for item in self.blockers],
            "disagreements": list(self.disagreements),
            "judge_references": list(self.judge_references),
            "accepted_debt_ids": list(self.accepted_debt_ids),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> QualityDecision:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("QualityDecision must be a mapping")
        expected = {
            "schema_version",
            "engine",
            "contract_id",
            "contract_version",
            "subject",
            "requested_class",
            "awarded_class",
            "outcome",
            "requires_human_review",
            "dimensions",
            "findings",
            "blockers",
            "disagreements",
            "judge_references",
            "accepted_debt_ids",
        }
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"QualityDecision has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"QualityDecision is missing keys: {sorted(missing)}")
        lists = {
            key: payload[key]
            for key in ("dimensions", "findings", "blockers", "disagreements")
        }
        for key, value in lists.items():
            if not isinstance(value, list):
                raise SchemaValidationError(f"{key} must be a list")
        references = {key: payload[key] for key in ("judge_references", "accepted_debt_ids")}
        for key, value in references.items():
            if not isinstance(value, list):
                raise SchemaValidationError(f"{key} must be a list")
        return cls(
            schema_version=payload["schema_version"],
            engine=ComponentVersion.from_payload(payload["engine"]),
            contract_id=payload["contract_id"],
            contract_version=payload["contract_version"],
            subject=SubjectRef.from_payload(payload["subject"]),
            requested_class=QualityClass.parse(payload["requested_class"]),
            awarded_class=QualityClass.parse(payload["awarded_class"]),
            outcome=DecisionOutcome.parse(payload["outcome"]),
            requires_human_review=payload["requires_human_review"],
            dimensions=tuple(DimensionOutcome.from_payload(item) for item in lists["dimensions"]),
            findings=tuple(EffectiveFinding.from_payload(item) for item in lists["findings"]),
            blockers=tuple(Blocker.from_payload(item) for item in lists["blockers"]),
            disagreements=tuple(lists["disagreements"]),
            judge_references=tuple(references["judge_references"]),
            accepted_debt_ids=tuple(references["accepted_debt_ids"]),
        )


@dataclass(frozen=True)
class DecisionEngine:
    """Deterministic ladder policy. Holds no inference state and touches no asset bytes."""

    component: ComponentVersion = field(
        default_factory=lambda: ComponentVersion("m01-decision-engine", "1.0.0")
    )
    schema_version: str = SCHEMA_VERSION

    def evaluate(
        self,
        contract: FidelityContract,
        subject: SubjectRef,
        *,
        assessments: Sequence[DimensionAssessment] = (),
        results: Sequence[JudgeResult] = (),
        defects: Sequence[Defect] = (),
        debts: Sequence[QualityDebt] = (),
        authority: Optional[EvaluatorAuthority] = None,
    ) -> QualityDecision:
        """Decide one asset against one contract. Same inputs, same bytes out.

        The authority must be promotion-capable, i.e. carry a registry resolved against the whole
        declared panel: every component that speaks has to be declared by the contract, registered
        at the exact version that spoke, and covered for each dimension it opined on, and every
        evaluator the contract declares has to be present in that panel. A missing or
        declaration-only authority fails closed instead of decidable.
        """

        if not isinstance(contract, FidelityContract):
            raise EvaluationInputError("contract must be a FidelityContract")
        if not isinstance(subject, SubjectRef):
            raise EvaluationInputError("subject must be a SubjectRef")
        if authority is None:
            raise EvaluationInputError(
                "evaluate() requires an explicit EvaluatorAuthority; a missing authority is a "
                "fail-closed condition, not permission. Pass "
                "EvaluatorAuthority.resolved(contract, registry) for a promotable decision."
            )
        if not isinstance(authority, EvaluatorAuthority):
            raise EvaluationInputError("authority must be an EvaluatorAuthority")
        if not authority.promotion_capable:
            raise EvaluationInputError(
                f"authority for contract {contract.contract_id} is declaration-only "
                "(EvaluatorAuthority.preflight): it cannot prove registration or per-dimension "
                "coverage, so it may not influence a promotable decision"
            )
        if authority.contract != contract:
            raise EvaluationInputError(
                "the evaluator authority was issued for another contract; capability is per contract"
            )
        collected = self._collect(contract, subject, assessments, results, defects, authority)
        findings, rulings = self._apply_policy(contract, collected["defects"], debts)
        dimensions, certainty_blockers = self._dimension_states(
            contract, collected["assessments"], results, collected["review_requests"]
        )
        needs_review = any(
            item.uncertainty == UncertaintyState.HUMAN_REVIEW.value for item in dimensions
        )
        fatal_open = tuple(
            item
            for item in findings
            if item.effective_severity is DefectSeverity.FATAL and not item.deferred
        )
        if fatal_open:
            awarded = QualityClass.DRAFT
            blockers = sorted(
                list(certainty_blockers)
                + [
                    Blocker(
                        code="fatal_defect_firewall",
                        detail=(
                            f"{len(fatal_open)} unresolved FATAL finding(s) bar every class above "
                            "DRAFT; no aggregate score averages a fatal defect away"
                        ),
                        dimension_id=item.dimension_id,
                        defect_id=item.defect_id,
                    )
                    for item in fatal_open
                ],
                key=Blocker.sort_key,
            )
            outcome = DecisionOutcome.REJECTED
        else:
            awarded, blockers = self._climb_ladder(
                contract, dimensions, findings, certainty_blockers
            )
            if needs_review and awarded is not contract.output_class:
                outcome = DecisionOutcome.HUMAN_REVIEW
            elif awarded is contract.output_class:
                outcome = DecisionOutcome.PROMOTED
            else:
                outcome = DecisionOutcome.NOT_PROMOTED
        spread = numeric_spread(results)
        return QualityDecision(
            schema_version=self.schema_version,
            engine=self.component,
            contract_id=contract.contract_id,
            contract_version=contract.contract_version,
            subject=subject,
            requested_class=contract.output_class,
            awarded_class=awarded,
            outcome=outcome,
            requires_human_review=needs_review,
            dimensions=dimensions,
            findings=findings,
            blockers=tuple(sorted(blockers, key=Blocker.sort_key)),
            disagreements=tuple(
                sorted(
                    (
                        value
                        for dimension_id, value in spread.items()
                        if value > contract.max_judge_disagreement
                    ),
                    reverse=True,
                )
            ),
            judge_references=tuple(sorted({result.judge.reference for result in results})),
            accepted_debt_ids=tuple(
                sorted(
                    ruling.debt.reference
                    for ruling in rulings.values()
                    if ruling.allowed and ruling.debt is not None
                )
            ),
        )

    def _collect(
        self,
        contract: FidelityContract,
        subject: SubjectRef,
        assessments: Sequence[DimensionAssessment],
        results: Sequence[JudgeResult],
        defects: Sequence[Defect],
        authority: EvaluatorAuthority,
    ) -> dict[str, tuple[Any, ...]]:
        review_requests: dict[str, list[str]] = {}
        for result in results:
            spoken = [item.dimension_id for item in result.assessments] + [
                item.dimension_id for item in result.defects if item.dimension_id is not None
            ]
            authority.authorize(result.judge, spoken, role="judge")
            for dimension_id in result.human_review_dimension_ids:
                if dimension_id not in contract.dimension_ids:
                    raise EvaluationInputError(
                        f"judge {result.judge.reference} requested human review for "
                        f"{dimension_id!r}, outside contract {contract.contract_id}; a request the "
                        "contract never admitted is refused, not ignored"
                    )
                review_requests.setdefault(dimension_id, []).append(result.judge.reference)
        merged = {
            item.dimension_id: item
            for item in merge_assessments(contract, subject, results)
        }
        for item in assessments:
            if not isinstance(item, DimensionAssessment):
                raise EvaluationInputError("assessments entries must be DimensionAssessment")
            authority.authorize(item.evaluator, (item.dimension_id,), role="assessment evaluator")
            if item.dimension_id in merged:
                raise EvaluationInputError(
                    f"dimension {item.dimension_id!r} carries both a judge assessment and an "
                    "explicit one; reconcile them upstream"
                )
            merged[item.dimension_id] = item
        collected: dict[str, Defect] = {}
        reported: list[Defect] = []
        for item in (*defects, *[defect for result in results for defect in result.defects]):
            if not isinstance(item, Defect):
                raise EvaluationInputError("defects entries must be Defect")
            previous = collected.get(item.defect_id)
            if previous is not None and previous != item:
                raise EvaluationInputError(
                    f"defect {item.defect_id} is reported twice with different content"
                )
            collected[item.defect_id] = item
        known_zones = {zone.zone_id for zone in contract.zones}
        for item in collected.values():
            if item.dimension_id is not None and item.dimension_id not in contract.dimension_ids:
                raise EvaluationInputError(
                    f"defect {item.defect_id} references dimension {item.dimension_id!r} "
                    "outside the contract"
                )
            if item.zone_id is not None and item.zone_id not in known_zones:
                raise EvaluationInputError(
                    f"defect {item.defect_id} references zone {item.zone_id!r} outside the contract"
                )
            reported.append(item)
        return {
            "assessments": tuple(merged[key] for key in sorted(merged)),
            "defects": tuple(sorted(reported, key=lambda item: item.defect_id)),
            "review_requests": {key: tuple(sorted(set(value))) for key, value in review_requests.items()},
        }

    def _apply_policy(
        self,
        contract: FidelityContract,
        defects: Sequence[Defect],
        debts: Sequence[QualityDebt],
    ) -> tuple[tuple[EffectiveFinding, ...], Mapping[str, DebtRuling]]:
        severities: dict[str, DefectSeverity] = {}
        zones_by_defect: dict[str, tuple[SemanticZone, ...]] = {}
        contract_severities: dict[str, DefectSeverity] = {}
        for defect in defects:
            declared = contract.declared_severity(defect.defect_class)
            if declared is None:
                raise EvaluationInputError(
                    f"defect class {defect.defect_class!r} is not declared by contract "
                    f"{contract.contract_id}; severity policy belongs to the contract"
                )
            contract_severity = DefectSeverity.parse(declared)
            effective = max((contract_severity, defect.severity), key=lambda item: item.rank)
            zones = tuple(
                zone
                for zone in contract.zones
                if (defect.zone_id is not None and zone.zone_id == defect.zone_id)
                or (defect.zone_id is None and defect.dimension_id in zone.dimension_ids)
            )
            for zone in zones:
                effective = max(
                    (effective, zone.effective_severity(defect.defect_class, effective)),
                    key=lambda item: item.rank,
                )
            contract_severities[defect.defect_id] = contract_severity
            severities[defect.defect_id] = effective
            zones_by_defect[defect.defect_id] = zones
        # Debt is ruled after the authoritative severity exists, so a softer reported severity can
        # never buy a deferral the effective severity forbids.
        rulings = contract.debt_policy.rule_all(defects, debts, severities)
        findings: list[EffectiveFinding] = []
        for defect in defects:
            ruling = rulings[defect.defect_id]
            findings.append(
                EffectiveFinding(
                    defect_id=defect.defect_id,
                    defect_class=defect.defect_class,
                    contract_severity=contract_severities[defect.defect_id],
                    reported_severity=defect.severity,
                    effective_severity=severities[defect.defect_id],
                    zone_ids=tuple(sorted(zone.zone_id for zone in zones_by_defect[defect.defect_id])),
                    dimension_id=defect.dimension_id,
                    deferred=ruling.allowed,
                    debt_id=None if ruling.debt is None else ruling.debt.debt_id,
                    debt_note=ruling.reason,
                )
            )
        return tuple(sorted(findings, key=lambda item: item.defect_id)), rulings

    def _dimension_states(
        self,
        contract: FidelityContract,
        assessments: Sequence[DimensionAssessment],
        results: Sequence[JudgeResult],
        review_requests: Mapping[str, tuple[str, ...]],
    ) -> tuple[tuple[DimensionOutcome, ...], tuple[Blocker, ...]]:
        by_dimension = {item.dimension_id: item for item in assessments}
        spread = numeric_spread(results)
        states: list[DimensionOutcome] = []
        blockers: list[Blocker] = []
        for dimension_id in sorted(contract.dimension_ids):
            assessment = by_dimension.get(dimension_id)
            zones = tuple(
                zone
                for zone in contract.zones
                if dimension_id in zone.dimension_ids
            )
            confidence = None if assessment is None else assessment.confidence
            uncertainty = (
                UncertaintyState.UNKNOWN
                if assessment is None
                else assessment.uncertainty
            )
            value = spread.get(dimension_id)
            if value is not None and value > contract.max_judge_disagreement:
                uncertainty = UncertaintyState.HUMAN_REVIEW
                blockers.append(
                    Blocker(
                        code="judge_disagreement",
                        detail=(
                            f"jurors spread {value:.3f} on {dimension_id}, above the contract "
                            f"tolerance {contract.max_judge_disagreement:.3f}"
                        ),
                        dimension_id=dimension_id,
                    )
                )
            elif confidence is not None:
                floors = [
                    zone.minimum_confidence
                    for zone in zones
                    if zone.minimum_confidence is not None
                ]
                if floors and confidence < max(floors):
                    uncertainty = UncertaintyState.HUMAN_REVIEW
                    blockers.append(
                        Blocker(
                            code="zone_confidence_floor",
                            detail=(
                                f"{dimension_id} confidence {confidence:.3f} is below the "
                                f"{max(floors):.3f} floor set by its semantic zone"
                            ),
                            dimension_id=dimension_id,
                        )
                    )
            recorded = bool(
                assessment and any(item.kind == HUMAN_DECISION_KIND for item in assessment.evidence)
            )
            requesters = review_requests.get(dimension_id, ())
            if requesters and not recorded:
                # A judge asking for a human is never reinterpreted as a pass, and one request out
                # of several jurors is enough: the union survives the merge until it is answered.
                uncertainty = UncertaintyState.HUMAN_REVIEW
                blockers.append(
                    Blocker(
                        code="judge_human_review_requested",
                        detail=(
                            f"{', '.join(requesters)} asked for a human decision on {dimension_id}; "
                            "the kernel will not promote over an unanswered request"
                        ),
                        dimension_id=dimension_id,
                    )
                )
            states.append(
                DimensionOutcome(
                    dimension_id=dimension_id,
                    gate=(
                        GateState.UNVERIFIED.value
                        if assessment is None
                        else assessment.gate.value
                    ),
                    uncertainty=uncertainty.value,
                    evidence_count=0 if assessment is None else assessment.evidence_count,
                    confidence=confidence,
                    zone_ids=tuple(sorted(zone.zone_id for zone in zones)),
                    evaluated_by=()
                    if assessment is None
                    else (assessment.evaluator.reference,),
                    human_decision_recorded=recorded,
                    human_review_requested_by=requesters,
                )
            )
        return tuple(states), tuple(sorted(blockers, key=Blocker.sort_key))

    def _climb_ladder(
        self,
        contract: FidelityContract,
        dimensions: Sequence[DimensionOutcome],
        findings: Sequence[EffectiveFinding],
        certainty_blockers: Sequence[Blocker] = (),
    ) -> tuple[QualityClass, list[Blocker]]:
        states = {item.dimension_id: item for item in dimensions}
        blockers: list[Blocker] = list(certainty_blockers)
        awarded = QualityClass.DRAFT
        rungs = QualityClass.ladder()[1 : contract.output_class.ladder_rank + 1]
        for target in rungs:
            rule = contract.rule_for(target)
            if rule is None:  # pragma: no cover - contract validation guarantees contiguity
                break
            rung = self._rung_blockers(contract, target, rule, states, findings)
            if rung:
                blockers.extend(rung)
                return awarded, blockers
            awarded = target
        return awarded, blockers

    def _rung_blockers(
        self,
        contract: FidelityContract,
        target: QualityClass,
        rule: PromotionRule,
        states: Mapping[str, DimensionOutcome],
        findings: Sequence[EffectiveFinding],
    ) -> tuple[Blocker, ...]:
        blockers: list[Blocker] = []
        for dimension_id in sorted(contract.dimension_ids):
            state = states[dimension_id]
            if state.uncertainty != UncertaintyState.KNOWN.value:
                blockers.append(
                    Blocker(
                        code="insufficient_certainty",
                        detail=(
                            f"{dimension_id} is {state.uncertainty}"
                            + (
                                ""
                                if state.evaluated_by
                                else " with no assessment produced"
                            )
                            + "; the kernel does not promote on an unknown dimension"
                        ),
                        target_class=target.value,
                        dimension_id=dimension_id,
                    )
                )
        for dimension_id in sorted(contract.human_review_dimension_ids):
            if not states[dimension_id].human_decision_recorded:
                blockers.append(
                    Blocker(
                        code="human_review_missing_for_dimension",
                        detail=f"{dimension_id} requires a recorded HUMAN_DECISION evidence item",
                        target_class=target.value,
                        dimension_id=dimension_id,
                    )
                )
        hard_gates = set(rule.hard_gate_dimension_ids)
        for dimension_id in sorted(rule.required_dimension_ids):
            state = states[dimension_id]
            if state.gate != GateState.PASS.value:
                related = [
                    item
                    for item in findings
                    if item.dimension_id == dimension_id
                    and item.effective_severity is not DefectSeverity.OBSERVATION
                ]
                if dimension_id in hard_gates:
                    blockers.append(
                        Blocker(
                            code="hard_gate_failed",
                            detail=(
                                f"{dimension_id} is a hard gate for {target.value} and its gate is "
                                f"{state.gate}; hard gates are never carried by debt"
                            ),
                            target_class=target.value,
                            dimension_id=dimension_id,
                        )
                    )
                elif not related or not all(item.deferred for item in related):
                    blockers.append(
                        Blocker(
                            code="dimension_gate_not_pass",
                            detail=(
                                f"{dimension_id} gate is {state.gate} and is not backed by an "
                                "accepted quality debt record"
                            ),
                            target_class=target.value,
                            dimension_id=dimension_id,
                        )
                    )
            if state.evidence_count < rule.minimum_evidence_count:
                blockers.append(
                    Blocker(
                        code="insufficient_evidence_coverage",
                        detail=(
                            f"{dimension_id} has {state.evidence_count} evidence item(s), below the "
                            f"required {rule.minimum_evidence_count}"
                        ),
                        target_class=target.value,
                        dimension_id=dimension_id,
                    )
                )
            floor = self._confidence_floor(contract, dimension_id, rule)
            if state.confidence is None or state.confidence < floor:
                blockers.append(
                    Blocker(
                        code="insufficient_confidence",
                        detail=(
                            f"{dimension_id} confidence "
                            + (
                                "is absent"
                                if state.confidence is None
                                else f"is {state.confidence:.3f}"
                            )
                            + f", below the required {floor:.3f}"
                        ),
                        target_class=target.value,
                        dimension_id=dimension_id,
                    )
                )
        blockers.extend(self._severity_blockers(target, findings))
        if rule.requires_human_review and not all(
            states[dimension_id].human_decision_recorded
            for dimension_id in rule.required_dimension_ids
        ):
            blockers.append(
                Blocker(
                    code="human_review_not_recorded",
                    detail=(
                        f"{target.value} requires a human decision covering each of "
                        f"{', '.join(sorted(rule.required_dimension_ids))}"
                    ),
                    target_class=target.value,
                )
            )
        return tuple(sorted(blockers, key=Blocker.sort_key))

    @staticmethod
    def _confidence_floor(
        contract: FidelityContract, dimension_id: str, rule: PromotionRule
    ) -> float:
        floors = [rule.minimum_confidence]
        floors.extend(
            zone.minimum_confidence
            for zone in contract.zones_for_dimension(dimension_id)
            if zone.minimum_confidence is not None
        )
        return max(floors)

    @staticmethod
    def _severity_blockers(
        target: QualityClass, findings: Sequence[EffectiveFinding]
    ) -> tuple[Blocker, ...]:
        blockers: list[Blocker] = []
        for finding in findings:
            if finding.deferred or finding.effective_severity is DefectSeverity.OBSERVATION:
                continue
            if finding.effective_severity is DefectSeverity.MAJOR:
                if target.ladder_rank < QualityClass.MASTER.ladder_rank:
                    continue
                code = "major_defect_without_debt"
            elif finding.effective_severity is DefectSeverity.MINOR:
                if target is not QualityClass.ARCHIVAL_MASTER:
                    continue
                code = "minor_defect_without_debt"
            else:
                continue
            blockers.append(
                Blocker(
                    code=code,
                    detail=(
                        f"{finding.defect_class} at {finding.effective_severity.value} on "
                        + (finding.dimension_id or "the whole asset")
                        + f" bars {target.value} until accepted as recorded quality debt"
                    ),
                    target_class=target.value,
                    dimension_id=finding.dimension_id,
                    defect_id=finding.defect_id,
                )
            )
        return tuple(blockers)
