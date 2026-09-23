"""Stable semantic identities and location-independent external resource refs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from iris_intent.identity import SemanticRef

from .base import IRRecord, many, one, optional
from .errors import IRSchemaError
from .versions import require_digest, require_identifier, require_text, require_version

__all__ = [
    "IRNodeRef",
    "IRRevisionRef",
    "ExternalIdentityRef",
    "IdentityAnchorRef",
    "AssetDNARef",
    "PersonaDNARef",
    "ResourceLocatorRef",
    "ResourceRef",
    "SemanticRef",
]


@dataclass(frozen=True, order=True)
class IRNodeRef(IRRecord):
    document_id: str
    node_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "document_id", require_identifier(self.document_id, "document_id"))
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))


@dataclass(frozen=True, order=True)
class IRRevisionRef(IRRecord):
    document_id: str
    revision_id: str
    revision_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "document_id", require_identifier(self.document_id, "document_id"))
        object.__setattr__(self, "revision_id", require_identifier(self.revision_id, "revision_id"))
        object.__setattr__(self, "revision_digest", require_digest(self.revision_digest, "revision_digest"))


@dataclass(frozen=True, order=True)
class ExternalIdentityRef(IRRecord):
    authority: str
    ref_id: str
    version: str
    content_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority", require_identifier(self.authority, "authority"))
        object.__setattr__(self, "ref_id", require_identifier(self.ref_id, "ref_id"))
        object.__setattr__(self, "version", require_version(self.version))
        if self.content_digest is not None:
            object.__setattr__(self, "content_digest", require_digest(self.content_digest))


@dataclass(frozen=True)
class IdentityAnchorRef(IRRecord):
    reference: ExternalIdentityRef
    application_point: IRNodeRef | None = None
    preservation_required: bool = True

    NESTED: ClassVar = {"reference": one(ExternalIdentityRef), "application_point": optional(IRNodeRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "reference", ExternalIdentityRef.coerce(self.reference, "reference"))
        if self.application_point is not None:
            object.__setattr__(self, "application_point", IRNodeRef.coerce(self.application_point))
        if not isinstance(self.preservation_required, bool):
            raise IRSchemaError("preservation_required must be a bool")


@dataclass(frozen=True)
class AssetDNARef(IRRecord):
    reference: ExternalIdentityRef

    NESTED: ClassVar = {"reference": one(ExternalIdentityRef)}

    def __post_init__(self) -> None:
        ref = ExternalIdentityRef.coerce(self.reference, "reference")
        if ref.authority != "m05.asset_dna":
            raise IRSchemaError("AssetDNARef must remain in the M05 asset DNA namespace")
        object.__setattr__(self, "reference", ref)


@dataclass(frozen=True)
class PersonaDNARef(IRRecord):
    reference: ExternalIdentityRef

    NESTED: ClassVar = {"reference": one(ExternalIdentityRef)}

    def __post_init__(self) -> None:
        ref = ExternalIdentityRef.coerce(self.reference, "reference")
        if ref.authority != "m05.persona_dna":
            raise IRSchemaError("PersonaDNARef must remain in the M05 persona DNA namespace")
        object.__setattr__(self, "reference", ref)


@dataclass(frozen=True, order=True)
class ResourceLocatorRef(IRRecord):
    """A non-identity storage locator kept outside ResourceRef's canonical identity."""

    scheme: str
    locator: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "scheme", require_identifier(self.scheme, "scheme"))
        object.__setattr__(self, "locator", require_text(self.locator, "locator", maximum=2048))


@dataclass(frozen=True)
class ResourceRef(IRRecord):
    resource_id: str
    resource_kind: str
    content_digest: str | None = None
    media_type: str | None = None
    expected_size_bytes: int | None = None
    required_capabilities: tuple[str, ...] = ()
    provenance_refs: tuple[SemanticRef, ...] = ()
    locator: ResourceLocatorRef | None = None

    NESTED: ClassVar = {
        "provenance_refs": many(SemanticRef),
        "locator": optional(ResourceLocatorRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "resource_id", require_identifier(self.resource_id, "resource_id"))
        object.__setattr__(self, "resource_kind", require_identifier(self.resource_kind, "resource_kind"))
        if self.content_digest is not None:
            object.__setattr__(self, "content_digest", require_digest(self.content_digest))
        if self.media_type is not None:
            object.__setattr__(self, "media_type", require_text(self.media_type, "media_type", maximum=128))
        if self.expected_size_bytes is not None and (
            isinstance(self.expected_size_bytes, bool)
            or not isinstance(self.expected_size_bytes, int)
            or self.expected_size_bytes < 0
        ):
            raise IRSchemaError("expected_size_bytes must be a non-negative integer")
        capabilities = tuple(sorted({require_identifier(item, "required_capabilities[]") for item in self.required_capabilities}))
        object.__setattr__(self, "required_capabilities", capabilities)
        refs = tuple(SemanticRef.coerce(item, "provenance_refs[]") for item in self.provenance_refs)
        object.__setattr__(self, "provenance_refs", tuple(sorted(refs, key=lambda item: item.text)))
        if self.locator is not None:
            object.__setattr__(self, "locator", ResourceLocatorRef.coerce(self.locator, "locator"))

    @property
    def identity_key(self) -> tuple[str, str, str | None]:
        return (self.resource_kind, self.resource_id, self.content_digest)
