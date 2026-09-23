"""One consolidated typed identity risk vocabulary and deterministic report."""

from __future__ import annotations

from dataclasses import dataclass

from .base import CanonicalRecord, SemanticRef, require_refs
from .enums import RiskCode, RiskSeverity
from .errors import DNAIntegrityError, DNAValidationError
from .versions import content_digest, require_digest, require_identifier, require_text

__all__ = [
    "IDENTITY_RISK_CODES",
    "IdentityRiskFinding",
    "IdentityRiskReport",
    "build_identity_risk_report",
]

IDENTITY_RISK_CODES = (
    RiskCode.CLASS_INDIVIDUAL_COLLAPSE,
    RiskCode.COMPONENT_CHURN,
    RiskCode.CONTEXTUAL_STATE_LEAKAGE,
    RiskCode.STALE_OR_MISSING_LINK,
    RiskCode.CAMPAIGN_BRAND_CONFUSION,
    RiskCode.UNAUTHORIZED_MUTATION,
    RiskCode.SIMILARITY_AUTO_MERGE,
    RiskCode.HISTORY_ERASURE,
    RiskCode.PACKAGE_OVERWRITE,
    RiskCode.HIDDEN_LOSSY_MIGRATION,
    RiskCode.STRIPPED_RIGHTS_SECURITY_REF,
    RiskCode.EXECUTABLE_PAYLOAD_ATTEMPT,
)


@dataclass(frozen=True)
class IdentityRiskFinding(CanonicalRecord):
    finding_id: str
    code: RiskCode
    severity: RiskSeverity
    target_ref: SemanticRef
    evidence_refs: tuple[SemanticRef, ...]
    summary: str
    required_action_ref: SemanticRef | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "finding_id", require_identifier(self.finding_id, "finding_id"))
        if not isinstance(self.code, RiskCode):
            object.__setattr__(self, "code", RiskCode(self.code))
        if not isinstance(self.severity, RiskSeverity):
            object.__setattr__(self, "severity", RiskSeverity(self.severity))
        if not isinstance(self.target_ref, SemanticRef):
            raise DNAValidationError("risk finding requires a typed target ref")
        object.__setattr__(self, "evidence_refs", require_refs(self.evidence_refs, "evidence_refs"))
        object.__setattr__(self, "summary", require_text(self.summary, "summary", maximum=2048))
        if self.required_action_ref is not None and not isinstance(self.required_action_ref, SemanticRef):
            raise DNAValidationError("required_action_ref must be a SemanticRef")


@dataclass(frozen=True)
class IdentityRiskReport(CanonicalRecord):
    findings: tuple[IdentityRiskFinding, ...]
    report_digest: str

    def __post_init__(self) -> None:
        findings = tuple(self.findings)
        if any(not isinstance(item, IdentityRiskFinding) for item in findings):
            raise DNAValidationError("risk report findings must be typed")
        keys = [(item.code, item.target_ref, item.finding_id) for item in findings]
        if len(keys) != len(set(keys)):
            raise DNAIntegrityError("risk report contains duplicate findings")
        ordered = tuple(sorted(findings, key=lambda item: (item.code.value, item.target_ref.text, item.finding_id)))
        object.__setattr__(self, "findings", ordered)
        object.__setattr__(self, "report_digest", require_digest(self.report_digest, "report_digest"))
        if content_digest(ordered) != self.report_digest:
            raise DNAIntegrityError("identity risk report digest does not match its findings")

    @property
    def has_high_or_critical(self) -> bool:
        return any(item.severity in {RiskSeverity.HIGH, RiskSeverity.CRITICAL} for item in self.findings)


def build_identity_risk_report(findings: tuple[IdentityRiskFinding, ...]) -> IdentityRiskReport:
    items = tuple(findings)
    if any(not isinstance(item, IdentityRiskFinding) for item in items):
        raise DNAValidationError("risk radar accepts only IdentityRiskFinding records")
    keys = [(item.code, item.target_ref, item.finding_id) for item in items]
    if len(keys) != len(set(keys)):
        raise DNAIntegrityError("consolidated risk report contains duplicate findings")
    ordered = tuple(sorted(items, key=lambda item: (item.code.value, item.target_ref.text, item.finding_id)))
    return IdentityRiskReport(ordered, content_digest(ordered))
