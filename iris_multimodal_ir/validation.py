"""Typed deterministic validation profiles and findings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .base import IRRecord, many
from .common import require_enum
from .enums import SchemaUnknownPolicy, ValidationSeverity
from .errors import IRKernelError, IRSchemaError
from .graph import IRDocumentEnvelope, IRRevision, validate_graph
from .limits import DEFAULT_LIMITS, IRLimits
from .versions import CORE_SCHEMA_VERSION, TRANSPORT_VERSION, VALIDATOR_VERSION, content_digest, require_identifier, require_text, require_version

__all__ = ["IRValidationProfile", "IRValidationFinding", "IRValidationReport", "validate_revision", "validate_envelope"]


@dataclass(frozen=True)
class IRValidationProfile(IRRecord):
    profile_id: str
    version: str
    limits: IRLimits = DEFAULT_LIMITS
    known_facets: tuple[tuple[str, str], ...] = ()
    known_dialects: tuple[tuple[str, str], ...] = ()
    known_extension_families: tuple[tuple[str, str], ...] = ()
    unknown_policy: SchemaUnknownPolicy = SchemaUnknownPolicy.FAIL_CLOSED

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", require_identifier(self.profile_id, "profile_id"))
        object.__setattr__(self, "version", require_version(self.version))
        if not isinstance(self.limits, IRLimits):
            raise IRSchemaError("limits must be IRLimits")
        for name in ("known_facets", "known_dialects", "known_extension_families"):
            pairs = tuple(sorted(set(tuple(pair) for pair in getattr(self, name))))
            if any(len(pair) != 2 or any(not isinstance(item, str) for item in pair) for pair in pairs):
                raise IRSchemaError(f"{name} must contain (id, version) pairs")
            object.__setattr__(self, name, pairs)
        object.__setattr__(self, "unknown_policy", require_enum(self.unknown_policy, SchemaUnknownPolicy, "unknown_policy"))


@dataclass(frozen=True, order=True)
class IRValidationFinding(IRRecord):
    finding_id: str
    code: str
    severity: ValidationSeverity
    path: str
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "finding_id", require_identifier(self.finding_id, "finding_id"))
        object.__setattr__(self, "code", require_text(self.code, "code", maximum=128))
        object.__setattr__(self, "severity", require_enum(self.severity, ValidationSeverity, "severity"))
        object.__setattr__(self, "path", require_text(self.path, "path", maximum=1024))
        object.__setattr__(self, "message", require_text(self.message, "message", maximum=2048))


@dataclass(frozen=True)
class IRValidationReport(IRRecord):
    profile_id: str
    profile_version: str
    source_digest: str
    findings: tuple[IRValidationFinding, ...]
    validator_version: str = VALIDATOR_VERSION

    NESTED: ClassVar = {"findings": many(IRValidationFinding)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", require_identifier(self.profile_id, "profile_id"))
        object.__setattr__(self, "profile_version", require_version(self.profile_version))
        from .versions import require_digest
        object.__setattr__(self, "source_digest", require_digest(self.source_digest, "source_digest"))
        findings = tuple(IRValidationFinding.coerce(item, "findings[]") for item in self.findings)
        if len({item.finding_id for item in findings}) != len(findings):
            raise IRSchemaError("validation finding ids must be unique")
        object.__setattr__(self, "findings", tuple(sorted(findings, key=lambda item: (item.path, item.code, item.finding_id))))
        object.__setattr__(self, "validator_version", require_version(self.validator_version))

    @property
    def valid(self) -> bool:
        return not any(item.severity in {ValidationSeverity.ERROR, ValidationSeverity.FATAL} for item in self.findings)

    @property
    def digest(self) -> str:
        return content_digest(self.to_payload())


def validate_revision(revision: IRRevision, profile: IRValidationProfile | None = None) -> IRValidationReport:
    revision = IRRevision.coerce(revision, "revision")
    profile = profile or IRValidationProfile("default", "1")
    profile = IRValidationProfile.coerce(profile, "profile")
    findings: list[IRValidationFinding] = []
    try:
        validate_graph(revision.nodes, revision.containment, revision.relationships, revision.relationship_policies, limits=profile.limits)
    except IRKernelError as error:
        findings.append(_finding("graph.integrity", "GRAPH_INTEGRITY", ValidationSeverity.FATAL, "revision.graph", str(error)))
    schema = revision.schema_manifest
    if schema.core_schema_version != CORE_SCHEMA_VERSION:
        findings.append(_finding("schema.core.unknown", "UNKNOWN_CORE_SCHEMA", ValidationSeverity.FATAL, "revision.schema_manifest.core_schema_version", f"unsupported core schema {schema.core_schema_version}"))
    if schema.transport_version != TRANSPORT_VERSION:
        findings.append(_finding("schema.transport.unknown", "UNKNOWN_TRANSPORT_SCHEMA", ValidationSeverity.FATAL, "revision.schema_manifest.transport_version", f"unsupported transport schema {schema.transport_version}"))
    for facet in schema.facets:
        if (facet.facet_id, facet.version) not in set(profile.known_facets):
            severity = ValidationSeverity.FATAL if facet.mandatory or not facet.preserve_opaque or profile.unknown_policy is SchemaUnknownPolicy.FAIL_CLOSED else ValidationSeverity.WARNING
            findings.append(_finding(f"facet.{facet.facet_id}", "UNKNOWN_FACET", severity, f"revision.schema_manifest.facets.{facet.facet_id}", f"unknown facet {facet.facet_id}@{facet.version}"))
    for dialect in schema.dialects:
        if (dialect.dialect_id, dialect.version) not in set(profile.known_dialects) and dialect.mandatory:
            findings.append(_finding(f"dialect.{dialect.dialect_id}", "UNKNOWN_MANDATORY_DIALECT", ValidationSeverity.FATAL, f"revision.schema_manifest.dialects.{dialect.dialect_id}", f"unknown mandatory dialect {dialect.dialect_id}@{dialect.version}"))
    resource_count = sum(len(node.resource_refs) for node in revision.nodes)
    if resource_count > profile.limits.max_resource_refs:
        findings.append(_finding("limits.resources", "RESOURCE_LIMIT", ValidationSeverity.FATAL, "revision.nodes.resource_refs", "resource ref count exceeds configured limit"))
    property_count = sum(len(node.attributes or {}) for node in revision.nodes)
    if property_count > profile.limits.max_properties:
        findings.append(_finding("limits.properties", "PROPERTY_LIMIT", ValidationSeverity.FATAL, "revision.nodes.attributes", "attribute count exceeds configured limit"))
    findings.sort(key=lambda item: (item.path, item.code, item.finding_id))
    if not findings:
        findings.append(_finding("validation.ok", "VALID", ValidationSeverity.INFO, "revision", "revision passes deterministic M04 structural/schema checks"))
    return IRValidationReport(profile.profile_id, profile.version, revision.revision_digest, tuple(findings))


def validate_envelope(envelope: IRDocumentEnvelope, profile: IRValidationProfile | None = None) -> IRValidationReport:
    envelope = IRDocumentEnvelope.coerce(envelope, "envelope")
    profile = profile or IRValidationProfile("default", "1")
    base = validate_revision(envelope.document.head, profile)
    findings = list(base.findings)
    if envelope.transport_version != TRANSPORT_VERSION:
        findings.append(_finding("envelope.transport", "UNKNOWN_TRANSPORT_SCHEMA", ValidationSeverity.FATAL, "envelope.transport_version", f"unsupported transport {envelope.transport_version}"))
    if envelope.contract_version != "m04-contract-v1.0":
        findings.append(_finding("envelope.contract", "UNKNOWN_CONTRACT_VERSION", ValidationSeverity.FATAL, "envelope.contract_version", f"unsupported contract {envelope.contract_version}"))
    findings.sort(key=lambda item: (item.path, item.code, item.finding_id))
    return IRValidationReport(base.profile_id, base.profile_version, envelope.digest, tuple(findings))


def _finding(finding_id: str, code: str, severity: ValidationSeverity, path: str, message: str) -> IRValidationFinding:
    return IRValidationFinding(finding_id, code, severity, path, message)
