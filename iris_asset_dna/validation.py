"""Deterministic M05 record, schema, envelope and required-link validation."""

from __future__ import annotations

from dataclasses import dataclass

from .base import CanonicalRecord
from .cross_modal import LinkedDomainDNARef
from .errors import DNAIntegrityError, DNAKernelError, DNAValidationError
from .identity import DNAEnvelope, DNARevisionRef, validate_envelope, validate_revision
from .limits import DEFAULT_LIMITS, DNARecordLimits
from .traits import DEFAULT_TRAIT_SCHEMAS, TraitSchemaRegistry
from .versions import VALIDATOR_VERSION, content_digest, require_digest, require_identifier, require_text, require_version

__all__ = ["DNAValidationFinding", "DNAValidationReport", "validate_dna"]


@dataclass(frozen=True)
class DNAValidationFinding(CanonicalRecord):
    code: str
    path: str
    detail: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", require_identifier(self.code, "code"))
        object.__setattr__(self, "path", require_identifier(self.path, "path"))
        object.__setattr__(self, "detail", require_text(self.detail, "detail", maximum=2048))


@dataclass(frozen=True)
class DNAValidationReport(CanonicalRecord):
    subject_ref: DNARevisionRef
    validator_version: str
    findings: tuple[DNAValidationFinding, ...]
    report_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.subject_ref, DNARevisionRef):
            raise DNAValidationError("subject_ref must be a pinned DNARevisionRef")
        object.__setattr__(self, "validator_version", require_version(self.validator_version, "validator_version"))
        findings = tuple(self.findings)
        if any(not isinstance(item, DNAValidationFinding) for item in findings):
            raise DNAValidationError("findings must contain DNAValidationFinding records")
        object.__setattr__(self, "findings", tuple(sorted(findings, key=lambda item: (item.code, item.path, item.detail))))
        object.__setattr__(self, "report_digest", require_digest(self.report_digest, "report_digest"))
        body = {
            "subject_ref": self.subject_ref,
            "validator_version": self.validator_version,
            "findings": self.findings,
        }
        if content_digest(body) != self.report_digest:
            raise DNAIntegrityError("DNA validation report digest does not match its findings")

    @property
    def valid(self) -> bool:
        return not self.findings


def validate_dna(
    envelope: DNAEnvelope,
    *,
    links: tuple[LinkedDomainDNARef, ...] = (),
    schemas: TraitSchemaRegistry = DEFAULT_TRAIT_SCHEMAS,
    limits: DNARecordLimits = DEFAULT_LIMITS,
) -> DNAValidationReport:
    if not isinstance(envelope, DNAEnvelope):
        raise DNAValidationError("validate_dna requires a DNAEnvelope")
    findings: list[DNAValidationFinding] = []
    limits.require("max_lineage_edges", max(0, len(envelope.revisions) - 1))
    try:
        validate_envelope(envelope, limits=limits)
    except DNAKernelError as error:
        findings.append(DNAValidationFinding(
            "INVALID_REVISION_ENVELOPE", envelope.identity.dna_id, f"{type(error).__name__}: envelope validation failed"
        ))
    for revision in envelope.revisions:
        try:
            validate_revision(revision, schemas=schemas, limits=limits)
        except DNAKernelError as error:
            findings.append(DNAValidationFinding(
                "INVALID_REVISION_SEMANTICS", revision.revision_id, f"{type(error).__name__}: revision validation failed"
            ))
    if len(links) > limits.max_domain_links:
        limits.require("max_domain_links", len(links))
    seen: set[str] = set()
    for link in links:
        if not isinstance(link, LinkedDomainDNARef):
            findings.append(DNAValidationFinding("INVALID_DOMAIN_LINK_TYPE", envelope.identity.dna_id, "domain links must be typed M05 references"))
            continue
        if link.link_id in seen:
            findings.append(DNAValidationFinding("DUPLICATE_DOMAIN_LINK_ID", link.link_id, "domain link IDs must be unique"))
        seen.add(link.link_id)
        try:
            link.validate_required_freshness()
        except DNAKernelError as error:
            findings.append(DNAValidationFinding(
                "REQUIRED_DOMAIN_LINK_NOT_CURRENT", link.link_id, f"{type(error).__name__}: required link is not current"
            ))
    ordered = tuple(sorted(findings, key=lambda item: (item.code, item.path, item.detail)))
    body = {
        "subject_ref": envelope.head.ref,
        "validator_version": VALIDATOR_VERSION,
        "findings": ordered,
    }
    return DNAValidationReport(envelope.head.ref, VALIDATOR_VERSION, ordered, content_digest(body))
