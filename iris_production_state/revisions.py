"""Immutable operational revisions, materializations and integrity evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from .base import CanonicalRecord, freeze_json, require_exact_ref, require_sequence
from .enums import AvailabilityState, IntegrityState
from .errors import ProductionStateAdmissionError, ProductionStateIntegrityError, ProductionStateValidationError
from .versions import (
    CONTENT_DIGEST_VERSION,
    CORE_SCHEMA_VERSION,
    OPERATIONAL_REVISION_VERSION,
    TRANSPORT_VERSION,
    require_digest_hex,
    require_identifier,
    require_text,
    require_version,
)

__all__ = [
    "OperationalReference",
    "ContentDigest",
    "OperationalRevisionRef",
    "MaterializationRef",
    "RevisionManifest",
    "ImmutableMasterRef",
    "MasterManifest",
    "RevisionBinding",
    "PersistenceReceipt",
    "IntegrityReceipt",
    "AvailabilityReceipt",
    "M06_REFERENCE_TYPES",
    "digest_bytes",
    "verify_digest",
    "validate_master_admission",
]


class OperationalReference:
    """Marker for the exact closed set of M06 reference records."""


@dataclass(frozen=True, order=True)
class ContentDigest(CanonicalRecord):
    algorithm: str
    algorithm_version: str
    value: str
    schema_version: str = CONTENT_DIGEST_VERSION

    def __post_init__(self) -> None:
        algorithm = require_identifier(self.algorithm.lower(), "algorithm").lower()
        require_version(self.algorithm_version, "algorithm_version")
        require_version(self.schema_version, "schema_version")
        expected = {"sha256": 64, "sha512": 128, "blake2b-256": 64}.get(algorithm)
        if expected is not None:
            require_digest_hex(self.value, "value", length=expected)
        else:
            # Opaque future algorithms may be persisted, but verification fails closed.
            require_text(self.value, "value", maximum=256)
        object.__setattr__(self, "algorithm", algorithm)


@dataclass(frozen=True, order=True)
class OperationalRevisionRef(CanonicalRecord, OperationalReference):
    revision_id: str
    source_revision_ref: Any
    revision_version: str = OPERATIONAL_REVISION_VERSION

    def __post_init__(self) -> None:
        require_identifier(self.revision_id, "revision_id")
        require_exact_ref(self.source_revision_ref, "source_revision_ref")
        if type(self.source_revision_ref).__module__ != "iris_project_os.identity" or type(self.source_revision_ref).__name__ != "RevisionRef":
            raise ProductionStateValidationError("source_revision_ref must be an exact M02 RevisionRef")
        require_version(self.revision_version, "revision_version")


@dataclass(frozen=True, order=True)
class MaterializationRef(CanonicalRecord, OperationalReference):
    materialization_id: str
    revision_ref: OperationalRevisionRef
    content_digest: ContentDigest
    representation: str
    materialization_version: str = TRANSPORT_VERSION

    def __post_init__(self) -> None:
        require_identifier(self.materialization_id, "materialization_id")
        if type(self.revision_ref) is not OperationalRevisionRef or type(self.content_digest) is not ContentDigest:
            raise ProductionStateValidationError("materialization requires exact operational revision and digest records")
        require_text(self.representation, "representation", maximum=128)
        require_version(self.materialization_version, "materialization_version")


@dataclass(frozen=True)
class RevisionManifest(CanonicalRecord):
    revision_ref: OperationalRevisionRef
    semantic_ref: Any
    content_digest: ContentDigest
    dependency_refs: tuple[Any, ...] = ()
    schema_version: str = CORE_SCHEMA_VERSION
    metadata: Any = None

    def __post_init__(self) -> None:
        if type(self.revision_ref) is not OperationalRevisionRef or type(self.content_digest) is not ContentDigest:
            raise ProductionStateValidationError("revision manifest requires exact operational revision and digest records")
        require_exact_ref(self.semantic_ref, "semantic_ref")
        if type(self.semantic_ref).__module__ != "iris_project_os.identity" or type(self.semantic_ref).__name__ != "RevisionRef":
            raise ProductionStateValidationError("semantic_ref must be an exact M02 RevisionRef")
        deps = require_sequence(self.dependency_refs, "dependency_refs", maximum=4096)
        for index, item in enumerate(deps):
            require_exact_ref(item, f"dependency_refs[{index}]")
        object.__setattr__(self, "dependency_refs", deps)
        require_version(self.schema_version, "schema_version")
        object.__setattr__(self, "metadata", freeze_json({} if self.metadata is None else self.metadata, "metadata"))
        if self.revision_ref.source_revision_ref != self.semantic_ref:
            raise ProductionStateIntegrityError("operational revision source and semantic ref must be the same exact M02 revision")


@dataclass(frozen=True, order=True)
class ImmutableMasterRef(CanonicalRecord, OperationalReference):
    master_id: str
    revision_ref: OperationalRevisionRef
    master_version: str = TRANSPORT_VERSION

    def __post_init__(self) -> None:
        require_identifier(self.master_id, "master_id")
        if type(self.revision_ref) is not OperationalRevisionRef:
            raise ProductionStateValidationError("master ref requires an exact M06 operational revision")
        require_version(self.master_version, "master_version")


@dataclass(frozen=True)
class MasterManifest(CanonicalRecord):
    master_ref: ImmutableMasterRef
    revision_manifest: RevisionManifest
    materializations: tuple[MaterializationRef, ...]
    m02_admission_ref: Any
    quality_evidence_ref: Any
    schema_version: str = CORE_SCHEMA_VERSION
    supersedes: ImmutableMasterRef | None = None

    def __post_init__(self) -> None:
        if type(self.master_ref) is not ImmutableMasterRef or type(self.revision_manifest) is not RevisionManifest:
            raise ProductionStateValidationError("master manifest requires exact M06 master and revision records")
        if self.master_ref.revision_ref != self.revision_manifest.revision_ref:
            raise ProductionStateIntegrityError("master and revision manifest refs do not match")
        values = require_sequence(self.materializations, "materializations", maximum=4096, item_type=MaterializationRef)
        if not values:
            raise ProductionStateValidationError("a master must have at least one materialization")
        if any(item.revision_ref != self.master_ref.revision_ref for item in values):
            raise ProductionStateIntegrityError("master materializations must bind the master's exact revision")
        if len({item.materialization_id for item in values}) != len(values):
            raise ProductionStateValidationError("master materialization identifiers must be unique")
        object.__setattr__(self, "materializations", values)
        require_exact_ref(self.m02_admission_ref, "m02_admission_ref")
        require_exact_ref(self.quality_evidence_ref, "quality_evidence_ref")
        require_version(self.schema_version, "schema_version")
        if self.supersedes is not None and type(self.supersedes) is not ImmutableMasterRef:
            raise ProductionStateValidationError("supersedes must be an exact immutable M06 master ref")
        if self.supersedes == self.master_ref:
            raise ProductionStateIntegrityError("a master cannot supersede itself")
        if self.supersedes is not None:
            previous = self.supersedes.revision_ref.source_revision_ref
            current = self.master_ref.revision_ref.source_revision_ref
            if previous.artifact_id != current.artifact_id:
                raise ProductionStateIntegrityError("master supersession must remain within the same M02 semantic artifact identity")
            if self.supersedes.revision_ref == self.master_ref.revision_ref:
                raise ProductionStateIntegrityError("master supersession must append a new operational revision")


@dataclass(frozen=True)
class RevisionBinding(CanonicalRecord):
    revision_ref: OperationalRevisionRef
    causal_fingerprint: Any
    bound_at_ms: int
    binding_version: str = TRANSPORT_VERSION

    def __post_init__(self) -> None:
        if type(self.revision_ref) is not OperationalRevisionRef:
            raise ProductionStateValidationError("revision binding requires exact M06 revision ref")
        if type(self.bound_at_ms) is not int or self.bound_at_ms < 0:
            raise ProductionStateValidationError("bound_at_ms must be a nonnegative exact integer")
        from .dependencies import OperationalDependencyFingerprint

        if type(self.causal_fingerprint) is not OperationalDependencyFingerprint:
            raise ProductionStateValidationError("revision binding requires an exact versioned causal fingerprint")
        require_version(self.binding_version, "binding_version")


@dataclass(frozen=True)
class PersistenceReceipt(CanonicalRecord):
    subject_ref: Any
    observed_state: AvailabilityState
    authority_ref: Any
    recorded_at_ms: int
    receipt_version: str = TRANSPORT_VERSION

    def __post_init__(self) -> None:
        require_exact_ref(self.subject_ref, "subject_ref")
        require_exact_ref(self.authority_ref, "authority_ref")
        if not isinstance(self.observed_state, AvailabilityState):
            object.__setattr__(self, "observed_state", AvailabilityState(self.observed_state))
        if type(self.recorded_at_ms) is not int or self.recorded_at_ms < 0:
            raise ProductionStateValidationError("recorded_at_ms must be a nonnegative exact integer")
        require_version(self.receipt_version, "receipt_version")


@dataclass(frozen=True)
class IntegrityReceipt(CanonicalRecord):
    materialization_ref: MaterializationRef
    observed_digest: ContentDigest | None
    state: IntegrityState
    checked_at_ms: int
    reason: str = ""
    receipt_version: str = TRANSPORT_VERSION

    def __post_init__(self) -> None:
        if type(self.materialization_ref) is not MaterializationRef:
            raise ProductionStateValidationError("integrity receipt requires an exact materialization ref")
        if self.observed_digest is not None and type(self.observed_digest) is not ContentDigest:
            raise ProductionStateValidationError("observed_digest must be a ContentDigest or None")
        if not isinstance(self.state, IntegrityState):
            object.__setattr__(self, "state", IntegrityState(self.state))
        if type(self.checked_at_ms) is not int or self.checked_at_ms < 0:
            raise ProductionStateValidationError("checked_at_ms must be a nonnegative exact integer")
        require_text(self.reason, "reason", maximum=2048, allow_empty=True)
        require_version(self.receipt_version, "receipt_version")
        if self.state is IntegrityState.VERIFIED and self.observed_digest != self.materialization_ref.content_digest:
            raise ProductionStateIntegrityError("verified integrity evidence must match the declared digest exactly")
        if self.state in {IntegrityState.CORRUPT, IntegrityState.MISMATCH} and self.observed_digest == self.materialization_ref.content_digest:
            raise ProductionStateIntegrityError("mismatch/corrupt integrity evidence cannot claim the declared digest matched")


@dataclass(frozen=True)
class AvailabilityReceipt(CanonicalRecord):
    subject_ref: Any
    state: AvailabilityState
    integrity_receipt: IntegrityReceipt | None
    observed_at_ms: int
    receipt_version: str = TRANSPORT_VERSION

    def __post_init__(self) -> None:
        require_exact_ref(self.subject_ref, "subject_ref")
        if not isinstance(self.state, AvailabilityState):
            object.__setattr__(self, "state", AvailabilityState(self.state))
        if self.integrity_receipt is not None and type(self.integrity_receipt) is not IntegrityReceipt:
            raise ProductionStateValidationError("integrity_receipt must be exact M06 integrity evidence")
        if self.state is AvailabilityState.KNOWN_AVAILABLE and (
            self.integrity_receipt is None or self.integrity_receipt.state is not IntegrityState.VERIFIED
        ):
            raise ProductionStateAdmissionError("availability cannot be admitted without verified integrity evidence")
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise ProductionStateValidationError("observed_at_ms must be a nonnegative exact integer")
        require_version(self.receipt_version, "receipt_version")


M06_REFERENCE_TYPES: tuple[type, ...] = (OperationalRevisionRef, MaterializationRef, ImmutableMasterRef)


_DIGEST_FUNCTIONS = {
    "sha256": lambda data: hashlib.sha256(data).hexdigest(),
    "sha512": lambda data: hashlib.sha512(data).hexdigest(),
    "blake2b-256": lambda data: hashlib.blake2b(data, digest_size=32).hexdigest(),
}


def digest_bytes(data: bytes, algorithm: str = "sha256", *, algorithm_version: str = "1.0.0") -> ContentDigest:
    if type(data) is not bytes:
        raise ProductionStateValidationError("digest input must be exact bytes")
    normalized = algorithm.lower()
    function = _DIGEST_FUNCTIONS.get(normalized)
    if function is None or algorithm_version != "1.0.0":
        raise ProductionStateAdmissionError(f"digest algorithm/version {normalized!r}/{algorithm_version!r} is not supported for verification")
    return ContentDigest(algorithm, algorithm_version, function(data))


def verify_digest(data: bytes, expected: ContentDigest) -> bool:
    if type(expected) is not ContentDigest:
        raise ProductionStateValidationError("expected digest must be an exact ContentDigest")
    actual = digest_bytes(data, expected.algorithm, algorithm_version=expected.algorithm_version)
    return actual == expected


def validate_master_admission(
    manifest: MasterManifest,
    *,
    m02_admission_ref: Any,
    quality_evidence_ref: Any,
    integrity_receipts: tuple[IntegrityReceipt, ...],
) -> MasterManifest:
    """Check external admission evidence; this function does not promote or persist a master."""
    if type(manifest) is not MasterManifest:
        raise ProductionStateValidationError("manifest must be an exact MasterManifest")
    require_exact_ref(m02_admission_ref, "m02_admission_ref")
    require_exact_ref(quality_evidence_ref, "quality_evidence_ref")
    if manifest.m02_admission_ref != m02_admission_ref or manifest.quality_evidence_ref != quality_evidence_ref:
        raise ProductionStateAdmissionError("master manifest must bind the supplied external M02/M01 admission evidence")
    checked = tuple(item.materialization_ref for item in integrity_receipts if type(item) is IntegrityReceipt and item.state is IntegrityState.VERIFIED)
    if any(item not in checked for item in manifest.materializations):
        raise ProductionStateAdmissionError("every master materialization requires matching positive integrity evidence")
    return manifest
