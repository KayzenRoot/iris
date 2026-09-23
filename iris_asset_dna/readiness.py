"""Non-authoritative M05 conformance readiness; never a quality or release verdict."""

from __future__ import annotations

from dataclasses import dataclass

from .base import CanonicalRecord
from .enums import ReadinessState
from .errors import DNAValidationError
from .validation import DNAValidationReport
from .versions import content_digest, require_digest, require_identifier

__all__ = ["DNAReadinessAssessment", "assess_dna_readiness"]


@dataclass(frozen=True)
class DNAReadinessAssessment(CanonicalRecord):
    state: ReadinessState
    validation_report_digest: str
    finding_codes: tuple[str, ...]
    authority_scope: str = "M05_SEMANTIC_CONFORMANCE_ONLY"
    quality_or_release_authority: bool = False
    assessment_digest: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.state, ReadinessState):
            object.__setattr__(self, "state", ReadinessState(self.state))
        object.__setattr__(self, "validation_report_digest", require_digest(self.validation_report_digest, "validation_report_digest"))
        object.__setattr__(self, "finding_codes", tuple(sorted({require_identifier(item, "finding_codes[]") for item in self.finding_codes})))
        if self.authority_scope != "M05_SEMANTIC_CONFORMANCE_ONLY" or self.quality_or_release_authority:
            raise DNAValidationError("M05 readiness cannot claim M01 quality or M02 release authority")
        if self.assessment_digest:
            object.__setattr__(self, "assessment_digest", require_digest(self.assessment_digest, "assessment_digest"))
        else:
            object.__setattr__(self, "assessment_digest", content_digest({
                "state": self.state,
                "validation_report_digest": self.validation_report_digest,
                "finding_codes": self.finding_codes,
                "authority_scope": self.authority_scope,
                "quality_or_release_authority": self.quality_or_release_authority,
            }))


def assess_dna_readiness(report: DNAValidationReport) -> DNAReadinessAssessment:
    if not isinstance(report, DNAValidationReport):
        raise DNAValidationError("assess_dna_readiness requires a DNAValidationReport")
    codes = tuple(sorted({item.code for item in report.findings}))
    if not report.findings:
        state = ReadinessState.READY
    elif any(item.code in {"REQUIRED_DOMAIN_LINK_NOT_CURRENT", "UNKNOWN_OPTIONAL_EXTENSION"} for item in report.findings):
        state = ReadinessState.NEEDS_REVIEW
    elif any(item.code.startswith("INVALID_") for item in report.findings):
        state = ReadinessState.BLOCKED
    else:
        state = ReadinessState.INDETERMINATE
    body = {
        "state": state,
        "validation_report_digest": report.report_digest,
        "finding_codes": codes,
        "authority_scope": "M05_SEMANTIC_CONFORMANCE_ONLY",
        "quality_or_release_authority": False,
    }
    return DNAReadinessAssessment(**body, assessment_digest=content_digest(body))
