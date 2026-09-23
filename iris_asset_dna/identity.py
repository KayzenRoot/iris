"""Stable M05 subject identities, immutable revisions and semantic fingerprints."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from .base import CanonicalRecord, SemanticRef, freeze_json, require_refs
from .enums import DNAFamily, DNAIdentityLevel, TraitCriticality
from .errors import DNAAdmissionError, DNAIntegrityError, DNAValidationError
from .limits import DEFAULT_LIMITS, DNARecordLimits
from .traits import DNATrait, TraitSchemaRegistry, DEFAULT_TRAIT_SCHEMAS
from .versions import (
    CONTRACT_VERSION,
    CORE_SCHEMA_VERSION,
    content_digest,
    require_digest,
    require_identifier,
    require_version,
)

__all__ = [
    "AssetDNAIdentity",
    "DNARevisionRef",
    "DNARevision",
    "DNAEnvelope",
    "DNAFingerprint",
    "mint_dna_id",
    "validate_revision",
    "validate_envelope",
]


def mint_dna_id() -> str:
    """Mint an opaque subject ID independent of names, paths and content."""
    return f"dna-{uuid.uuid4().hex}"


@dataclass(frozen=True, order=True)
class DNARevisionRef(CanonicalRecord):
    dna_id: str
    revision_id: str
    revision_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "dna_id", require_identifier(self.dna_id, "dna_id"))
        object.__setattr__(self, "revision_id", require_identifier(self.revision_id, "revision_id"))
        object.__setattr__(self, "revision_digest", require_digest(self.revision_digest, "revision_digest"))


@dataclass(frozen=True)
class AssetDNAIdentity(CanonicalRecord):
    dna_id: str
    subject_class: str
    family: DNAFamily = DNAFamily.GENERIC
    namespace: str = "iris.asset"
    contract_version: str = CONTRACT_VERSION
    external_identity_refs: tuple[SemanticRef, ...] = ()
    policy_refs: tuple[SemanticRef, ...] = ()
    provenance_refs: tuple[SemanticRef, ...] = ()
    rights_privacy_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "dna_id", require_identifier(self.dna_id, "dna_id"))
        object.__setattr__(self, "subject_class", require_identifier(self.subject_class, "subject_class"))
        if not isinstance(self.family, DNAFamily):
            object.__setattr__(self, "family", DNAFamily(self.family))
        object.__setattr__(self, "namespace", require_identifier(self.namespace, "namespace"))
        if self.contract_version != CONTRACT_VERSION:
            raise DNAValidationError(f"unsupported contract version {self.contract_version!r}")
        for name in ("external_identity_refs", "policy_refs", "provenance_refs", "rights_privacy_refs"):
            object.__setattr__(self, name, require_refs(getattr(self, name), name))
        if any(ref.owner_module != "m53" for ref in self.provenance_refs):
            raise DNAAdmissionError("M53 remains the provenance authority for canonical identity refs")
        if any(ref.owner_module not in {"m53", "m54"} for ref in self.rights_privacy_refs):
            raise DNAAdmissionError("rights and privacy refs remain owned by M53/M54")


@dataclass(frozen=True)
class DNAFingerprint(CanonicalRecord):
    algorithm: str
    digest: str
    schema_version: str

    def __post_init__(self) -> None:
        if self.algorithm != "sha256":
            raise DNAValidationError("M05 currently admits only sha256 fingerprints")
        object.__setattr__(self, "digest", require_digest(self.digest, "digest"))
        object.__setattr__(self, "schema_version", require_version(self.schema_version, "schema_version"))


@dataclass(frozen=True)
class DNARevision(CanonicalRecord):
    dna_id: str
    revision_id: str
    revision_number: int
    family: DNAFamily
    identity_level: DNAIdentityLevel
    traits: tuple[DNATrait, ...]
    schema_version: str = CORE_SCHEMA_VERSION
    contract_version: str = CONTRACT_VERSION
    profile_ref: SemanticRef | None = None
    parent_revision_refs: tuple[DNARevisionRef, ...] = ()
    anchor_refs: tuple[SemanticRef, ...] = ()
    component_refs: tuple[SemanticRef, ...] = ()
    domain_link_refs: tuple[SemanticRef, ...] = ()
    provenance_refs: tuple[SemanticRef, ...] = ()
    policy_refs: tuple[SemanticRef, ...] = ()
    rights_privacy_refs: tuple[SemanticRef, ...] = ()
    evidence_refs: tuple[SemanticRef, ...] = ()
    display_metadata: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "dna_id", require_identifier(self.dna_id, "dna_id"))
        object.__setattr__(self, "revision_id", require_identifier(self.revision_id, "revision_id"))
        if isinstance(self.revision_number, bool) or not isinstance(self.revision_number, int) or self.revision_number < 1:
            raise DNAValidationError("revision_number must be a positive integer")
        for name, enum_type in (("family", DNAFamily), ("identity_level", DNAIdentityLevel)):
            value = getattr(self, name)
            if not isinstance(value, enum_type):
                try:
                    value = enum_type(value)
                except (TypeError, ValueError) as error:
                    raise DNAValidationError(f"{name} is not supported by M05") from error
                object.__setattr__(self, name, value)
        object.__setattr__(self, "schema_version", require_version(self.schema_version, "schema_version"))
        if self.contract_version != CONTRACT_VERSION:
            raise DNAValidationError(f"unsupported contract version {self.contract_version!r}")
        if self.profile_ref is not None and not isinstance(self.profile_ref, SemanticRef):
            raise DNAValidationError("profile_ref must be a SemanticRef")
        parents = tuple(self.parent_revision_refs)
        if any(not isinstance(item, DNARevisionRef) for item in parents):
            raise DNAValidationError("parent_revision_refs must contain DNARevisionRef values")
        if len({(item.dna_id, item.revision_id) for item in parents}) != len(parents):
            raise DNAValidationError("parent_revision_refs contains duplicates")
        object.__setattr__(self, "parent_revision_refs", tuple(sorted(parents)))
        traits = tuple(self.traits)
        if any(not isinstance(item, DNATrait) for item in traits):
            raise DNAValidationError("traits must contain DNATrait values")
        if len({item.path for item in traits}) != len(traits):
            raise DNAIntegrityError("DNA revision cannot contain duplicate canonical trait paths")
        object.__setattr__(self, "traits", tuple(sorted(traits, key=lambda item: item.path)))
        DEFAULT_LIMITS.require("max_traits", len(traits))
        for name in (
            "anchor_refs",
            "component_refs",
            "domain_link_refs",
            "provenance_refs",
            "policy_refs",
            "rights_privacy_refs",
            "evidence_refs",
        ):
            object.__setattr__(self, name, require_refs(getattr(self, name), name))
        DEFAULT_LIMITS.require("max_anchors", len(self.anchor_refs))
        DEFAULT_LIMITS.require("max_components", len(self.component_refs))
        DEFAULT_LIMITS.require("max_domain_links", len(self.domain_link_refs))
        if any(ref.owner_module != "m53" for ref in self.provenance_refs):
            raise DNAAdmissionError("M53 remains the provenance authority for canonical DNA revisions")
        if any(ref.owner_module not in {"m53", "m54"} for ref in self.rights_privacy_refs):
            raise DNAAdmissionError("rights and privacy refs remain owned by M53/M54")
        if self.display_metadata is not None:
            object.__setattr__(self, "display_metadata", freeze_json(self.display_metadata, "display_metadata"))
        if not self.traits and not self.profile_ref:
            raise DNAAdmissionError("a DNA revision needs identity traits or an explicit profile reference")

    def canonical_payload(self) -> dict[str, Any]:
        """Identity material only; display, evidence, location and revision history are excluded."""
        return {
            "contract_version": self.contract_version,
            "schema_version": self.schema_version,
            "family": self.family.value,
            "identity_level": self.identity_level.value,
            "profile_ref": self.profile_ref,
            "traits": self.traits,
            "anchor_refs": self.anchor_refs,
            "component_refs": self.component_refs,
            "domain_link_refs": self.domain_link_refs,
            "provenance_refs": self.provenance_refs,
            "policy_refs": self.policy_refs,
            "rights_privacy_refs": self.rights_privacy_refs,
        }

    @property
    def fingerprint(self) -> DNAFingerprint:
        return DNAFingerprint("sha256", content_digest(self.canonical_payload()), self.schema_version)

    @property
    def semantic_digest(self) -> str:
        return self.fingerprint.digest

    @property
    def revision_digest(self) -> str:
        return content_digest({
            "dna_id": self.dna_id,
            "revision_id": self.revision_id,
            "revision_number": self.revision_number,
            "semantic_fingerprint": self.semantic_digest,
            "parent_revision_refs": self.parent_revision_refs,
        })

    @property
    def ref(self) -> DNARevisionRef:
        return DNARevisionRef(self.dna_id, self.revision_id, self.revision_digest)

    def trait_map(self) -> dict[str, DNATrait]:
        return {item.path: item for item in self.traits}


@dataclass(frozen=True)
class DNAEnvelope(CanonicalRecord):
    identity: AssetDNAIdentity
    revisions: tuple[DNARevision, ...]
    head_revision_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.identity, AssetDNAIdentity):
            raise DNAValidationError("identity must be an AssetDNAIdentity")
        object.__setattr__(self, "head_revision_id", require_identifier(self.head_revision_id, "head_revision_id"))
        revisions = tuple(self.revisions)
        if any(not isinstance(item, DNARevision) for item in revisions):
            raise DNAValidationError("revisions must contain DNARevision values")
        if not revisions:
            raise DNAAdmissionError("DNAEnvelope requires at least one immutable revision")
        DEFAULT_LIMITS.require("max_lineage_edges", max(0, len(revisions) - 1))
        if not any(item.revision_id == self.head_revision_id for item in revisions):
            raise DNAIntegrityError("DNAEnvelope head_revision_id does not name a revision in its history")
        validate_envelope(self, revisions=revisions, identity=self.identity)
        object.__setattr__(self, "revisions", tuple(sorted(revisions, key=lambda item: item.revision_number)))

    @property
    def head(self) -> DNARevision:
        return next(item for item in self.revisions if item.revision_id == self.head_revision_id)


def validate_revision(
    revision: DNARevision,
    *,
    schemas: TraitSchemaRegistry = DEFAULT_TRAIT_SCHEMAS,
    limits: DNARecordLimits = DEFAULT_LIMITS,
) -> None:
    if not isinstance(revision, DNARevision):
        raise DNAValidationError("revision must be a DNARevision")
    limits.require("max_traits", len(revision.traits))
    limits.require("max_anchors", len(revision.anchor_refs))
    limits.require("max_components", len(revision.component_refs))
    limits.require("max_domain_links", len(revision.domain_link_refs))
    for trait in revision.traits:
        if trait.criticality is TraitCriticality.DERIVED_EVIDENCE_ONLY:
            raise DNAAdmissionError(f"derived evidence cannot be canonical trait {trait.path}")
        if trait.mutability is not None and trait.mutability.value == "DERIVED_ONLY":
            raise DNAAdmissionError(f"derived-only trait {trait.path} cannot be canonical DNA")
        schemas.validate(trait)


def validate_envelope(
    envelope: DNAEnvelope | None = None,
    *,
    revisions: tuple[DNARevision, ...] | None = None,
    identity: AssetDNAIdentity | None = None,
    check_head: bool = True,
    limits: DNARecordLimits = DEFAULT_LIMITS,
) -> None:
    if envelope is not None:
        identity = envelope.identity
        revisions = envelope.revisions
    if not isinstance(identity, AssetDNAIdentity) or not isinstance(revisions, tuple) or not revisions:
        raise DNAValidationError("envelope validation requires identity and a non-empty revision tuple")
    ids = [item.revision_id for item in revisions]
    limits.require("max_lineage_edges", max(0, len(revisions) - 1))
    numbers = [item.revision_number for item in revisions]
    if len(ids) != len(set(ids)) or len(numbers) != len(set(numbers)):
        raise DNAIntegrityError("DNA history contains duplicate revision IDs or numbers")
    known: dict[str, DNARevision] = {}
    known_numbers: set[int] = set()
    for revision in sorted(revisions, key=lambda item: item.revision_number):
        if revision.dna_id != identity.dna_id:
            raise DNAIntegrityError("all DNA revisions must belong to the envelope identity")
        if revision.revision_number in known_numbers:
            raise DNAIntegrityError("DNA revision number is not unique")
        for parent in revision.parent_revision_refs:
            if parent.dna_id != identity.dna_id or parent.revision_id not in known:
                raise DNAIntegrityError("revision parent must be an earlier revision of this dna_id")
            if known[parent.revision_id].revision_digest != parent.revision_digest:
                raise DNAIntegrityError("revision parent digest does not match immutable history")
        known[revision.revision_id] = revision
        known_numbers.add(revision.revision_number)
    if envelope is not None and check_head and envelope.head_revision_id not in known:
        raise DNAIntegrityError("DNAEnvelope head_revision_id does not name a revision in its history")
    if envelope is not None and check_head:
        head = known[envelope.head_revision_id]
        if head.revision_number != max(numbers):
            raise DNAIntegrityError("DNAEnvelope head must be the highest immutable revision number")
