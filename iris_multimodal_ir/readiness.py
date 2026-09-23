"""Evidence-only M04 representation readiness; no quality or release authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .base import IRRecord, many, one
from .enums import ReadinessState
from .errors import IRSchemaError
from .lowering import SemanticLoweringReceipt
from .roundtrip import RoundTripReceipt
from .validation import IRValidationReport
from .versions import content_digest, require_digest, require_identifier, require_text

__all__ = ["IRReleaseReadinessReport", "compute_readiness"]


@dataclass(frozen=True)
class IRReleaseReadinessReport(IRRecord):
    report_id: str
    source_revision_digest: str
    state: ReadinessState
    validation_report: IRValidationReport
    lowering_receipts: tuple[SemanticLoweringReceipt, ...] = ()
    round_trip_receipts: tuple[RoundTripReceipt, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    quality_evaluation_performed: bool = False
    release_authorized: bool = False
    report_digest: str | None = None

    NESTED: ClassVar = {"validation_report": one(IRValidationReport), "lowering_receipts": many(SemanticLoweringReceipt), "round_trip_receipts": many(RoundTripReceipt)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_id", require_identifier(self.report_id, "report_id"))
        object.__setattr__(self, "source_revision_digest", require_digest(self.source_revision_digest, "source_revision_digest"))
        from .common import require_enum
        object.__setattr__(self, "state", require_enum(self.state, ReadinessState, "state"))
        for name, kind in (("validation_report", IRValidationReport),):
            object.__setattr__(self, name, kind.coerce(getattr(self, name), name))
        object.__setattr__(self, "lowering_receipts", tuple(SemanticLoweringReceipt.coerce(item, "lowering_receipts[]") for item in self.lowering_receipts))
        object.__setattr__(self, "round_trip_receipts", tuple(RoundTripReceipt.coerce(item, "round_trip_receipts[]") for item in self.round_trip_receipts))
        object.__setattr__(self, "evidence_refs", tuple(sorted(set(require_text(item, "evidence_refs[]", maximum=512) for item in self.evidence_refs))))
        if self.quality_evaluation_performed is not False or self.release_authorized is not False:
            raise IRSchemaError("M04 readiness cannot claim M01 quality evaluation or M02 release authorization")
        if self.report_digest is not None and self.report_digest != self.digest:
            raise IRSchemaError("readiness digest mismatch")

    @property
    def digest(self) -> str:
        return content_digest({"report_id": self.report_id, "source_revision_digest": self.source_revision_digest, "state": self.state, "validation": self.validation_report.digest, "lowering": self.lowering_receipts, "round_trip": self.round_trip_receipts, "evidence_refs": self.evidence_refs, "quality_evaluation_performed": False, "release_authorized": False})


def compute_readiness(
    validation_report: IRValidationReport,
    *, report_id: str,
    lowering_receipts: tuple[SemanticLoweringReceipt, ...] = (),
    round_trip_receipts: tuple[RoundTripReceipt, ...] = (),
    evidence_refs: tuple[str, ...] = (),
) -> IRReleaseReadinessReport:
    blocked = not validation_report.valid or any(
        rule.state.value == "BLOCKED" for receipt in lowering_receipts for rule in receipt.rules
    ) or any(not receipt.semantic_match for receipt in round_trip_receipts)
    conditional = any(not receipt.independently_qualified for receipt in round_trip_receipts)
    state = ReadinessState.BLOCKED if blocked else ReadinessState.READY_WITH_GAPS if conditional else ReadinessState.READY
    return IRReleaseReadinessReport(report_id, validation_report.source_digest, state, validation_report, lowering_receipts, round_trip_receipts, evidence_refs)
