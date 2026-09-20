from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Protocol, Sequence, runtime_checkable

from .contracts import FidelityContract
from .defects import Defect
from .dimensions import DimensionAssessment, GateState, UncertaintyState
from .errors import EvaluationInputError, SchemaValidationError
from .evidence import EvidenceRef
from .versions import ComponentVersion, require_identifier, require_text

__all__ = [
    "SubjectRef",
    "JudgeRequest",
    "JudgeResult",
    "Abstention",
    "QualityJudge",
    "ValidationCheck",
    "ValidatorOutcome",
    "AssetValidator",
    "attach_contract_checks",
    "numeric_spread",
    "require_unique_identifiers",
]

_SHA256_LENGTH = 64
MAX_REQUEST_PARAMETERS = 32


@dataclass(frozen=True)
class SubjectRef:
    """Opaque handle to the thing under evaluation; the kernel never opens it."""

    subject_id: str
    content_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject_id", require_identifier(self.subject_id, "subject_id"))
        digest = require_text(self.content_sha256, "content_sha256", maximum=64)
        if len(digest) != _SHA256_LENGTH or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise SchemaValidationError("content_sha256 must be 64 lowercase hexadecimal digits")
        object.__setattr__(self, "content_sha256", digest)

    @property
    def reference(self) -> str:
        return f"{self.subject_id}@{self.content_sha256[:12]}"

    def to_payload(self) -> dict[str, Any]:
        return {"subject_id": self.subject_id, "content_sha256": self.content_sha256}

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> SubjectRef:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("SubjectRef must be a mapping")
        expected = {"subject_id", "content_sha256"}
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"SubjectRef has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"SubjectRef is missing keys: {sorted(missing)}")
        return cls(subject_id=payload["subject_id"], content_sha256=payload["content_sha256"])


@dataclass(frozen=True)
class JudgeRequest:
    """What a judge is asked to cover, expressed only in contract vocabulary."""

    contract: FidelityContract
    subject: SubjectRef
    dimension_ids: tuple[str, ...]
    zone_ids: tuple[str, ...] = ()
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.contract, FidelityContract):
            raise SchemaValidationError("contract must be a FidelityContract")
        if not isinstance(self.subject, SubjectRef):
            raise SchemaValidationError("subject must be a SubjectRef")
        dimensions = require_unique_identifiers(self.dimension_ids, "dimension_ids")
        if not dimensions:
            raise SchemaValidationError("dimension_ids must list at least one dimension")
        outside = sorted(set(dimensions) - set(self.contract.dimension_ids))
        if outside:
            raise EvaluationInputError(
                f"requested dimensions outside the contract: {outside}"
            )
        object.__setattr__(self, "dimension_ids", dimensions)
        zones = require_unique_identifiers(self.zone_ids, "zone_ids")
        known_zones = {zone.zone_id for zone in self.contract.zones}
        unknown_zones = sorted(set(zones) - known_zones)
        if unknown_zones:
            raise EvaluationInputError(f"requested zones outside the contract: {unknown_zones}")
        object.__setattr__(self, "zone_ids", zones)
        if not isinstance(self.parameters, Mapping):
            raise SchemaValidationError("parameters must be a mapping")
        if len(self.parameters) > MAX_REQUEST_PARAMETERS:
            raise SchemaValidationError(
                f"parameters accepts at most {MAX_REQUEST_PARAMETERS} entries, "
                f"got {len(self.parameters)}"
            )
        checked: dict[str, Any] = {}
        for key, value in self.parameters.items():
            name = require_identifier(key, "parameters key")
            if value is not None and not isinstance(value, (bool, int, float, str)):
                raise SchemaValidationError(
                    f"parameter {name!r} must be a scalar or None, not {type(value).__name__}; "
                    "structured instructions belong in a versioned evaluator, not a request"
                )
            if isinstance(value, str) and len(value) > 512:
                raise SchemaValidationError(f"parameter {name!r} exceeds 512 characters")
            checked[name] = value
        object.__setattr__(self, "parameters", checked)

    def to_payload(self) -> dict[str, Any]:
        return {
            "contract": self.contract.to_payload(),
            "subject": self.subject.to_payload(),
            "dimension_ids": list(self.dimension_ids),
            "zone_ids": list(self.zone_ids),
            "parameters": dict(self.parameters),
        }


@dataclass(frozen=True)
class Abstention:
    """A judge stating what it did not cover, so silence cannot read as certainty."""

    dimension_id: str
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "dimension_id", require_identifier(self.dimension_id, "dimension_id"))
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=512))

    def to_payload(self) -> dict[str, Any]:
        return {"dimension_id": self.dimension_id, "reason": self.reason}

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Abstention:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("Abstention must be a mapping")
        expected = {"dimension_id", "reason"}
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"Abstention has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"Abstention is missing keys: {sorted(missing)}")
        return cls(dimension_id=payload["dimension_id"], reason=payload["reason"])


@dataclass(frozen=True)
class JudgeResult:
    """One independent opinion, attributable to a versioned judge."""

    judge: ComponentVersion
    contract_id: str
    contract_version: str
    subject: SubjectRef
    assessments: tuple[DimensionAssessment, ...] = field(default_factory=tuple)
    defects: tuple[Defect, ...] = field(default_factory=tuple)
    abstentions: tuple[Abstention, ...] = field(default_factory=tuple)
    human_review_dimension_ids: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[EvidenceRef, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.judge, ComponentVersion):
            raise SchemaValidationError("judge must be a ComponentVersion")
        object.__setattr__(self, "contract_id", require_identifier(self.contract_id, "contract_id"))
        object.__setattr__(
            self, "contract_version", require_text(self.contract_version, "contract_version", maximum=64)
        )
        if not isinstance(self.subject, SubjectRef):
            raise SchemaValidationError("subject must be a SubjectRef")
        for name in ("assessments", "defects", "abstentions", "evidence"):
            value = getattr(self, name)
            if not isinstance(value, tuple):
                raise SchemaValidationError(f"{name} must be a tuple")
        object.__setattr__(
            self,
            "human_review_dimension_ids",
            require_unique_identifiers(self.human_review_dimension_ids, "human_review_dimension_ids"),
        )
        _require_unique([item.dimension_id for item in self.assessments], "assessed dimensions")
        _require_unique([item.defect_id for item in self.defects], "defect ids")
        _require_unique([item.dimension_id for item in self.abstentions], "abstained dimensions")
        _require_unique([item.evidence_id for item in self.evidence], "result evidence ids")
        assessed = {item.dimension_id for item in self.assessments}
        overlapped = sorted(assessed & {item.dimension_id for item in self.abstentions})
        if overlapped:
            raise SchemaValidationError(
                f"a dimension cannot be both assessed and abstained: {overlapped}"
            )
        for item in self.human_review_dimension_ids:
            if item not in assessed and item not in {abstention.dimension_id for abstention in self.abstentions}:
                raise SchemaValidationError(
                    f"human review requested for {item!r} which is neither assessed nor abstained"
                )
        evidence_ids = {item.evidence_id for item in self.evidence}
        for item in (*self.assessments, *self.defects):
            for ref in item.evidence:
                if ref.evidence_id in evidence_ids:
                    raise SchemaValidationError(
                        f"evidence {ref.evidence_id!r} appears both at result level and under "
                        f"{item.dimension_id if isinstance(item, DimensionAssessment) else item.defect_id}"
                    )

    @property
    def contract_reference(self) -> str:
        return f"{self.contract_id}@{self.contract_version}"

    def to_payload(self) -> dict[str, Any]:
        return {
            "judge": self.judge.to_payload(),
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "subject": self.subject.to_payload(),
            "assessments": [item.to_payload() for item in self.assessments],
            "defects": [item.to_payload() for item in self.defects],
            "abstentions": [item.to_payload() for item in self.abstentions],
            "human_review_dimension_ids": list(self.human_review_dimension_ids),
            "evidence": [item.to_payload() for item in self.evidence],
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> JudgeResult:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("JudgeResult must be a mapping")
        expected = {
            "judge",
            "contract_id",
            "contract_version",
            "subject",
            "assessments",
            "defects",
            "abstentions",
            "human_review_dimension_ids",
            "evidence",
        }
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"JudgeResult has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"JudgeResult is missing keys: {sorted(missing)}")
        lists = {key: payload[key] for key in ("assessments", "defects", "abstentions", "evidence")}
        for key, value in lists.items():
            if not isinstance(value, list):
                raise SchemaValidationError(f"{key} must be a list")
        review_ids = payload["human_review_dimension_ids"]
        if not isinstance(review_ids, list):
            raise SchemaValidationError("human_review_dimension_ids must be a list")
        return cls(
            judge=ComponentVersion.from_payload(payload["judge"]),
            contract_id=payload["contract_id"],
            contract_version=payload["contract_version"],
            subject=SubjectRef.from_payload(payload["subject"]),
            assessments=tuple(DimensionAssessment.from_payload(item) for item in lists["assessments"]),
            defects=tuple(Defect.from_payload(item) for item in lists["defects"]),
            abstentions=tuple(Abstention.from_payload(item) for item in lists["abstentions"]),
            human_review_dimension_ids=tuple(review_ids),
            evidence=tuple(EvidenceRef.from_payload(item) for item in lists["evidence"]),
        )


@runtime_checkable
class QualityJudge(Protocol):
    """A perceptual or statistical juror. Implementation-free: no vendor type crosses here."""

    @property
    def component_version(self) -> ComponentVersion: ...

    def covers(self) -> tuple[str, ...]:
        """Dimension ids this judge is able to opine on; anything else stays UNVERIFIED."""
        ...

    def evaluate(self, request: JudgeRequest) -> JudgeResult: ...


@dataclass(frozen=True)
class ValidationCheck:
    """A binary structural claim, using the contract gate vocabulary."""

    check_id: str
    gate: str
    summary: str
    dimension_id: Optional[str] = None
    zone_id: Optional[str] = None
    evidence: tuple[EvidenceRef, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "check_id", require_identifier(self.check_id, "check_id"))
        object.__setattr__(self, "gate", GateState.parse(self.gate).value)
        object.__setattr__(self, "summary", require_text(self.summary, "summary", maximum=512))
        if self.dimension_id is not None:
            object.__setattr__(
                self, "dimension_id", require_identifier(self.dimension_id, "dimension_id")
            )
        if self.zone_id is not None:
            object.__setattr__(self, "zone_id", require_identifier(self.zone_id, "zone_id"))
        if not isinstance(self.evidence, tuple):
            raise SchemaValidationError("evidence must be a tuple of EvidenceRef")
        for item in self.evidence:
            if not isinstance(item, EvidenceRef):
                raise SchemaValidationError("evidence entries must be EvidenceRef")

    def to_payload(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "gate": self.gate,
            "summary": self.summary,
            "dimension_id": self.dimension_id,
            "zone_id": self.zone_id,
            "evidence": [item.to_payload() for item in self.evidence],
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ValidationCheck:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("ValidationCheck must be a mapping")
        expected = {"check_id", "gate", "summary", "dimension_id", "zone_id", "evidence"}
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"ValidationCheck has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"ValidationCheck is missing keys: {sorted(missing)}")
        evidence = payload["evidence"]
        if not isinstance(evidence, list):
            raise SchemaValidationError("ValidationCheck evidence must be a list")
        return cls(
            check_id=payload["check_id"],
            gate=payload["gate"],
            summary=payload["summary"],
            dimension_id=payload["dimension_id"],
            zone_id=payload["zone_id"],
            evidence=tuple(EvidenceRef.from_payload(item) for item in evidence),
        )


@dataclass(frozen=True)
class ValidatorOutcome:
    """Deterministic, source-attributed structural findings."""

    validator: ComponentVersion
    contract_reference: str
    subject: SubjectRef
    checks: tuple[ValidationCheck, ...] = field(default_factory=tuple)
    defects: tuple[Defect, ...] = field(default_factory=tuple)
    evidence: tuple[EvidenceRef, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.validator, ComponentVersion):
            raise SchemaValidationError("validator must be a ComponentVersion")
        object.__setattr__(
            self,
            "contract_reference",
            require_text(self.contract_reference, "contract_reference", maximum=256),
        )
        if not isinstance(self.subject, SubjectRef):
            raise SchemaValidationError("subject must be a SubjectRef")
        for name in ("checks", "defects", "evidence"):
            if not isinstance(getattr(self, name), tuple):
                raise SchemaValidationError(f"{name} must be a tuple")
        _require_unique([item.check_id for item in self.checks], "check ids")
        _require_unique([item.defect_id for item in self.defects], "defect ids")
        _require_unique([item.evidence_id for item in self.evidence], "outcome evidence ids")

    def to_payload(self) -> dict[str, Any]:
        return {
            "validator": self.validator.to_payload(),
            "contract_reference": self.contract_reference,
            "subject": self.subject.to_payload(),
            "checks": [item.to_payload() for item in self.checks],
            "defects": [item.to_payload() for item in self.defects],
            "evidence": [item.to_payload() for item in self.evidence],
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ValidatorOutcome:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("ValidatorOutcome must be a mapping")
        expected = {"validator", "contract_reference", "subject", "checks", "defects", "evidence"}
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"ValidatorOutcome has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"ValidatorOutcome is missing keys: {sorted(missing)}")
        lists = {key: payload[key] for key in ("checks", "defects", "evidence")}
        for key, value in lists.items():
            if not isinstance(value, list):
                raise SchemaValidationError(f"{key} must be a list")
        return cls(
            validator=ComponentVersion.from_payload(payload["validator"]),
            contract_reference=payload["contract_reference"],
            subject=SubjectRef.from_payload(payload["subject"]),
            checks=tuple(ValidationCheck.from_payload(item) for item in lists["checks"]),
            defects=tuple(Defect.from_payload(item) for item in lists["defects"]),
            evidence=tuple(EvidenceRef.from_payload(item) for item in lists["evidence"]),
        )


@runtime_checkable
class AssetValidator(Protocol):
    """A deterministic structural conformance check, independent from perceptual judges."""

    @property
    def component_version(self) -> ComponentVersion: ...

    def validate(self, contract: FidelityContract, subject: SubjectRef) -> ValidatorOutcome: ...


def require_unique_identifiers(values: Sequence[Any], name: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise SchemaValidationError(f"{name} must be a list of identifiers")
    identifiers = tuple(require_identifier(value, f"{name}[]") for value in values)
    _require_unique(identifiers, name)
    return identifiers


def _require_unique(values: Iterable[str], name: str) -> None:
    items = list(values)
    duplicates = sorted({item for item in items if items.count(item) > 1})
    if duplicates:
        raise SchemaValidationError(f"{name} contains duplicates: {duplicates}")


def attach_contract_checks(
    contract: FidelityContract, subject: SubjectRef, outcome: ValidatorOutcome
) -> tuple[DimensionAssessment, ...]:
    """Project binary structural checks onto dimensions as structural measurements.

    The value and confidence here restate a deterministic gate, so a PASS check is reported at 1.0
    and a FAIL at 0.0: they carry no perceptual opinion, and a perceptual dimension stays absent
    until a judge that can opine on it is declared by the contract.
    """

    if outcome.contract_reference != contract.reference:
        raise EvaluationInputError(
            f"validator outcome targets {outcome.contract_reference!r}, not {contract.reference!r}"
        )
    if not isinstance(subject, SubjectRef):
        raise SchemaValidationError("subject must be a SubjectRef")
    if outcome.subject != subject:
        raise EvaluationInputError(
            f"validator outcome subject {outcome.subject.reference!r} does not match "
            f"{subject.reference!r}"
        )
    grouped: dict[str, list[ValidationCheck]] = {}
    for check in outcome.checks:
        if check.dimension_id is None:
            continue
        if check.dimension_id not in contract.dimension_ids:
            raise EvaluationInputError(
                f"check {check.check_id!r} reports dimension {check.dimension_id!r} outside the contract"
            )
        grouped.setdefault(check.dimension_id, []).append(check)
    assessments: list[DimensionAssessment] = []
    for dimension_id in contract.dimension_ids:
        checks = grouped.get(dimension_id)
        if not checks:
            continue
        checks = sorted(checks, key=lambda item: item.check_id)
        if any(item.gate == GateState.FAIL.value for item in checks):
            gate, uncertainty = GateState.FAIL, UncertaintyState.KNOWN
        elif any(item.gate == GateState.UNVERIFIED.value for item in checks):
            gate, uncertainty = GateState.UNVERIFIED, UncertaintyState.UNKNOWN
        elif all(item.gate == GateState.PASS.value for item in checks):
            gate, uncertainty = GateState.PASS, UncertaintyState.KNOWN
        else:
            gate, uncertainty = GateState.NOT_APPLICABLE, UncertaintyState.UNKNOWN
        assessments.append(
            DimensionAssessment(
                dimension_id=dimension_id,
                gate=gate,
                uncertainty=uncertainty,
                evaluator=outcome.validator,
                value=1.0 if gate is GateState.PASS else (0.0 if gate is GateState.FAIL else None),
                confidence=1.0,
                evidence=_unique_evidence(item for check in checks for item in check.evidence),
            )
        )
    return tuple(assessments)


def _unique_evidence(refs: Iterable[EvidenceRef]) -> tuple[EvidenceRef, ...]:
    seen: dict[str, EvidenceRef] = {}
    for ref in refs:
        seen.setdefault(ref.evidence_id, ref)
    return tuple(seen[key] for key in sorted(seen))


def numeric_spread(results: Sequence[JudgeResult]) -> Mapping[str, float]:
    """Per-dimension disagreement across judges that produced numeric values."""

    values: dict[str, list[float]] = {}
    for result in results:
        for assessment in result.assessments:
            if assessment.value is None:
                continue
            values.setdefault(assessment.dimension_id, []).append(assessment.value)
    return {
        dimension_id: max(occurrences) - min(occurrences)
        for dimension_id, occurrences in sorted(values.items())
        if len(occurrences) > 1
    }
