"""Opaque M07 bindings and purpose-scoped evidence context descriptors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import M08Record, content_digest, freeze_json
from .enums import PrivacyClass
from .errors import MicrobenchmarkAdmissionError, MicrobenchmarkIntegrityError, MicrobenchmarkValidationError
from .limits import DEFAULT_LIMITS
from .versions import require_digest, require_identifier, require_unique, require_version

__all__ = [
    "M07ProvenanceBinding", "ExternalContextReference", "EvidencePurposeDescriptor",
    "ExecutionContextDescriptor", "ProvenanceExportDigest", "create_provenance_export_digest", "ConsumerProjectionDescriptor",
]


@dataclass(frozen=True)
class M07ProvenanceBinding(M08Record):
    genome_id: str | None
    subject_id: str
    runtime_id: str
    backend_id: str
    backend_version: str
    version_axes: tuple[tuple[str, str], ...]
    capability_evidence_ids: tuple[str, ...]
    material_context_digest: str
    projection_id: str | None = None
    projection_digest: str | None = None
    synthetic: bool = False

    def __post_init__(self) -> None:
        if (self.genome_id is None) == (self.projection_id is None):
            raise MicrobenchmarkValidationError("binding requires exactly one exact Genome or named projection")
        if self.genome_id is not None:
            object.__setattr__(self, "genome_id", require_identifier(self.genome_id, "genome_id"))
            if self.projection_digest is not None:
                raise MicrobenchmarkIntegrityError("Genome binding cannot also carry a projection digest")
        else:
            object.__setattr__(self, "projection_id", require_identifier(self.projection_id, "projection_id"))
            object.__setattr__(self, "projection_digest", require_digest(self.projection_digest, "projection_digest"))
        for field in ("subject_id", "runtime_id", "backend_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "backend_version", require_version(self.backend_version, "backend_version"))
        axes = tuple(sorted((require_identifier(k, "version axis"), require_version(v, "version axis value")) for k, v in self.version_axes))
        if len({key for key, _ in axes}) != len(axes):
            raise MicrobenchmarkIntegrityError("backend/runtime version axes must be unique")
        object.__setattr__(self, "version_axes", axes)
        object.__setattr__(self, "capability_evidence_ids", tuple(sorted(require_unique(self.capability_evidence_ids, "capability_evidence_ids", maximum=10_000))))
        object.__setattr__(self, "material_context_digest", require_digest(self.material_context_digest, "material_context_digest"))
        if type(self.synthetic) is not bool:
            raise MicrobenchmarkValidationError("synthetic must be bool")


@dataclass(frozen=True)
class ExternalContextReference(M08Record):
    namespace: str
    reference_id: str
    version: str
    digest: str
    materiality: str

    def __post_init__(self) -> None:
        for field in ("namespace", "reference_id", "materiality"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "version", require_version(self.version))
        object.__setattr__(self, "digest", require_digest(self.digest))


@dataclass(frozen=True)
class EvidencePurposeDescriptor(M08Record):
    purpose_id: str
    version: str
    intended_uses: tuple[str, ...]
    excluded_uses: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "purpose_id", require_identifier(self.purpose_id, "purpose_id"))
        object.__setattr__(self, "version", require_version(self.version))
        object.__setattr__(self, "intended_uses", tuple(sorted(require_unique(self.intended_uses, "intended_uses", maximum=256))))
        object.__setattr__(self, "excluded_uses", tuple(sorted(require_unique(self.excluded_uses, "excluded_uses", maximum=256))))
        if set(self.intended_uses) & set(self.excluded_uses):
            raise MicrobenchmarkIntegrityError("evidence purpose cannot both include and exclude a use")

    def qualifies(self, requested_use: str) -> bool:
        use = require_identifier(requested_use, "requested_use")
        if use in self.excluded_uses:
            return False
        if use not in self.intended_uses:
            raise MicrobenchmarkAdmissionError("evidence reuse requires explicit purpose qualification")
        return True


@dataclass(frozen=True)
class ExecutionContextDescriptor(M08Record):
    context_id: str
    version: str
    application_ref: str | None
    runtime_mode: str
    plugin_refs: tuple[str, ...]
    codec_refs: tuple[str, ...]
    implementation_context: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "context_id", require_identifier(self.context_id, "context_id"))
        object.__setattr__(self, "version", require_version(self.version))
        if self.application_ref is not None:
            object.__setattr__(self, "application_ref", require_identifier(self.application_ref, "application_ref"))
        object.__setattr__(self, "runtime_mode", require_identifier(self.runtime_mode, "runtime_mode"))
        object.__setattr__(self, "plugin_refs", tuple(sorted(require_unique(self.plugin_refs, "plugin_refs", maximum=1_024))))
        object.__setattr__(self, "codec_refs", tuple(sorted(require_unique(self.codec_refs, "codec_refs", maximum=1_024))))
        object.__setattr__(self, "implementation_context", freeze_json(self.implementation_context, "implementation_context", limits=DEFAULT_LIMITS))


@dataclass(frozen=True)
class ProvenanceExportDigest(M08Record):
    digest_id: str
    version: str
    source_result_ids: tuple[str, ...]
    evidence_purpose: EvidencePurposeDescriptor
    privacy_class: PrivacyClass
    digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "digest_id", require_identifier(self.digest_id, "digest_id"))
        object.__setattr__(self, "version", require_version(self.version))
        object.__setattr__(self, "source_result_ids", tuple(sorted(require_unique(self.source_result_ids, "source_result_ids", maximum=10_000))))
        if not self.source_result_ids:
            raise MicrobenchmarkValidationError("provenance export digest requires at least one exact result")
        object.__setattr__(self, "evidence_purpose", EvidencePurposeDescriptor.coerce(self.evidence_purpose, "evidence_purpose"))
        if not isinstance(self.privacy_class, PrivacyClass):
            raise MicrobenchmarkValidationError("privacy_class must be PrivacyClass")
        if self.privacy_class is PrivacyClass.SENSITIVE:
            raise MicrobenchmarkAdmissionError("sensitive identity evidence cannot be exported through the M08 provenance digest")
        self.evidence_purpose.qualifies("provenance-export")
        object.__setattr__(self, "digest", require_digest(self.digest))
        expected = content_digest({
            "digest_id": self.digest_id,
            "version": self.version,
            "source_result_ids": self.source_result_ids,
            "evidence_purpose": self.evidence_purpose,
            "privacy_class": self.privacy_class,
        })
        if self.digest != expected:
            raise MicrobenchmarkIntegrityError("provenance export digest does not match its immutable source and purpose references")


def create_provenance_export_digest(
    *, digest_id: str, version: str, source_result_ids: tuple[str, ...],
    evidence_purpose: EvidencePurposeDescriptor, privacy_class: PrivacyClass,
) -> ProvenanceExportDigest:
    source_ids = tuple(sorted(require_unique(source_result_ids, "source_result_ids", maximum=10_000)))
    if not source_ids:
        raise MicrobenchmarkValidationError("provenance export digest requires at least one exact result")
    purpose = EvidencePurposeDescriptor.coerce(evidence_purpose, "evidence_purpose")
    if not isinstance(privacy_class, PrivacyClass):
        raise MicrobenchmarkValidationError("privacy_class must be PrivacyClass")
    if privacy_class is PrivacyClass.SENSITIVE:
        raise MicrobenchmarkAdmissionError("sensitive identity evidence cannot be exported through the M08 provenance digest")
    purpose.qualifies("provenance-export")
    material = {
        "digest_id": require_identifier(digest_id, "digest_id"),
        "version": require_version(version),
        "source_result_ids": source_ids,
        "evidence_purpose": purpose,
        "privacy_class": privacy_class,
    }
    return ProvenanceExportDigest(
        material["digest_id"], material["version"], source_ids, purpose,
        privacy_class, content_digest(material),
    )


@dataclass(frozen=True)
class ConsumerProjectionDescriptor(M08Record):
    projection_id: str
    version: str
    consumer_namespace: str
    evidence_purpose: EvidencePurposeDescriptor
    included_metrics: tuple[str, ...]
    included_dimensions: tuple[str, ...]
    privacy_class: PrivacyClass
    pseudonymous_subject_token: str | None

    def __post_init__(self) -> None:
        for field in ("projection_id", "consumer_namespace"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "version", require_version(self.version))
        object.__setattr__(self, "evidence_purpose", EvidencePurposeDescriptor.coerce(self.evidence_purpose, "evidence_purpose"))
        object.__setattr__(self, "included_metrics", tuple(sorted(require_unique(self.included_metrics, "included_metrics", maximum=2_048))))
        object.__setattr__(self, "included_dimensions", tuple(sorted(require_unique(self.included_dimensions, "included_dimensions", maximum=2_048))))
        if not isinstance(self.privacy_class, PrivacyClass):
            raise MicrobenchmarkValidationError("privacy_class must be PrivacyClass")
        if self.privacy_class in {PrivacyClass.PUBLIC, PrivacyClass.SYNTHETIC} and self.pseudonymous_subject_token is not None:
            raise MicrobenchmarkIntegrityError("public projections cannot carry a pseudonymous local subject token")
        if self.pseudonymous_subject_token is not None:
            object.__setattr__(self, "pseudonymous_subject_token", require_identifier(self.pseudonymous_subject_token, "pseudonymous_subject_token"))
        if not self.included_metrics and not self.included_dimensions:
            raise MicrobenchmarkValidationError("consumer projection must select at least one evidence dimension")
