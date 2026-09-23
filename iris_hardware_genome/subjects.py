"""Opaque hardware/runtime subjects, passports and ephemeral locators."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M07Record
from .enums import PrivacyClass, RuntimeScope, SubjectKind
from .errors import HardwareGenomeIntegrityError, HardwareGenomeValidationError
from .versions import require_identifier, require_text, require_version

__all__ = [
    "IdentityAnchor", "DeviceLocatorEvidence", "HardwareSubjectRef", "RuntimeSubjectRef",
    "RuntimeSubstrate", "RuntimeSubstratePassport",
]


@dataclass(frozen=True, order=True)
class IdentityAnchor(M07Record):
    """Privacy-classified digest anchor; raw serials and host identifiers are not stored."""

    namespace: str
    digest: str
    source_evidence_id: str
    privacy_class: PrivacyClass = PrivacyClass.LOCAL_IDENTIFIER

    def __post_init__(self) -> None:
        from .versions import require_digest

        object.__setattr__(self, "namespace", require_identifier(self.namespace, "namespace"))
        object.__setattr__(self, "digest", require_digest(self.digest, "identity anchor digest"))
        object.__setattr__(self, "source_evidence_id", require_identifier(self.source_evidence_id, "source_evidence_id"))
        if type(self.privacy_class) is not PrivacyClass:
            raise HardwareGenomeValidationError("privacy_class must be a closed PrivacyClass")


@dataclass(frozen=True)
class DeviceLocatorEvidence(M07Record):
    """A mutable local locator, deliberately separate from HardwareSubjectRef identity."""

    locator_id: str
    locator_kind: str
    value: str
    observed_at_ms: int
    privacy_class: PrivacyClass = PrivacyClass.LOCAL_IDENTIFIER

    def __post_init__(self) -> None:
        from .versions import require_nonnegative_int

        for field in ("locator_id", "locator_kind"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "value", require_text(self.value, "locator value", maximum=512))
        object.__setattr__(self, "observed_at_ms", require_nonnegative_int(self.observed_at_ms, "observed_at_ms"))
        if type(self.privacy_class) is not PrivacyClass:
            raise HardwareGenomeValidationError("privacy_class must be a closed PrivacyClass")
        if self.privacy_class is PrivacyClass.PROCESS_METADATA:
            raise HardwareGenomeValidationError("process metadata is not a device locator")


@dataclass(frozen=True)
class HardwareSubjectRef(M07Record):
    subject_id: str
    kind: SubjectKind
    identity_anchors: tuple[IdentityAnchor, ...] = ()
    parent_subject_id: str | None = None
    locator_evidence: tuple[DeviceLocatorEvidence, ...] = ()
    display_label: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject_id", require_identifier(self.subject_id, "subject_id"))
        if type(self.kind) is not SubjectKind:
            raise HardwareGenomeValidationError("kind must be a closed SubjectKind")
        anchors = tuple(IdentityAnchor.coerce(item, "identity_anchors[]") for item in self.identity_anchors)
        if len({item.namespace for item in anchors}) != len(anchors):
            raise HardwareGenomeValidationError("identity anchor namespaces must be unique per subject")
        object.__setattr__(self, "identity_anchors", tuple(sorted(anchors, key=lambda item: item.namespace)))
        if self.parent_subject_id is not None:
            parent = require_identifier(self.parent_subject_id, "parent_subject_id")
            if parent == self.subject_id:
                raise HardwareGenomeIntegrityError("a hardware subject cannot parent itself")
            object.__setattr__(self, "parent_subject_id", parent)
        locators = tuple(DeviceLocatorEvidence.coerce(item, "locator_evidence[]") for item in self.locator_evidence)
        if len({item.locator_id for item in locators}) != len(locators):
            raise HardwareGenomeValidationError("locator evidence ids must be unique per subject")
        object.__setattr__(self, "locator_evidence", tuple(sorted(locators, key=lambda item: item.locator_id)))
        if self.display_label is not None:
            object.__setattr__(self, "display_label", require_text(self.display_label, "display_label", maximum=256))


@dataclass(frozen=True, order=True)
class RuntimeSubjectRef(M07Record):
    runtime_id: str
    scope: RuntimeScope
    scope_version: str
    parent_runtime_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "runtime_id", require_identifier(self.runtime_id, "runtime_id"))
        if type(self.scope) is not RuntimeScope:
            raise HardwareGenomeValidationError("scope must be a closed RuntimeScope")
        object.__setattr__(self, "scope_version", require_version(self.scope_version, "scope_version"))
        if self.parent_runtime_id is not None:
            parent = require_identifier(self.parent_runtime_id, "parent_runtime_id")
            if parent == self.runtime_id:
                raise HardwareGenomeIntegrityError("a runtime subject cannot parent itself")
            object.__setattr__(self, "parent_runtime_id", parent)


@dataclass(frozen=True)
class RuntimeSubstrate(M07Record):
    runtime_ref: RuntimeSubjectRef
    os_family: str
    os_version: str | None
    kernel_version: str | None
    host_architecture: str | None
    process_architecture: str
    python_version: str | None = None
    container_boundary: str | None = None
    vm_boundary: str | None = None
    wsl_boundary: str | None = None
    visibility_limitations: tuple[str, ...] = ()
    virtualization_reported: bool | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "runtime_ref", RuntimeSubjectRef.coerce(self.runtime_ref, "runtime_ref"))
        for field in ("os_family", "process_architecture"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        for field in ("os_version", "kernel_version", "host_architecture", "python_version"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_version(value, field))
        for field in ("container_boundary", "vm_boundary", "wsl_boundary"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_identifier(value, field))
        limits = tuple(require_text(item, "visibility limitation", maximum=256) for item in self.visibility_limitations)
        if len(limits) != len(set(limits)):
            raise HardwareGenomeValidationError("visibility limitations must be unique")
        object.__setattr__(self, "visibility_limitations", tuple(sorted(limits)))
        if self.virtualization_reported is not None and type(self.virtualization_reported) is not bool:
            raise HardwareGenomeValidationError("virtualization_reported must be bool or unknown")


@dataclass(frozen=True)
class RuntimeSubstratePassport(M07Record):
    passport_id: str
    substrate: RuntimeSubstrate
    observed_at_ms: int
    visible_subject_ids: tuple[str, ...]
    completeness: str
    evidence_id: str

    def __post_init__(self) -> None:
        from .versions import require_nonnegative_int, require_unique

        object.__setattr__(self, "passport_id", require_identifier(self.passport_id, "passport_id"))
        object.__setattr__(self, "substrate", RuntimeSubstrate.coerce(self.substrate, "substrate"))
        object.__setattr__(self, "observed_at_ms", require_nonnegative_int(self.observed_at_ms, "observed_at_ms"))
        object.__setattr__(self, "visible_subject_ids", require_unique(self.visible_subject_ids, "visible_subject_ids", maximum=2_048))
        completeness = require_identifier(self.completeness, "completeness")
        if completeness not in {"COMPLETE_FOR_SCOPE", "PARTIAL", "UNKNOWN"}:
            raise HardwareGenomeValidationError("passport completeness must be scoped and explicit")
        object.__setattr__(self, "completeness", completeness)
        object.__setattr__(self, "evidence_id", require_identifier(self.evidence_id, "evidence_id"))
