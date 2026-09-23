"""Small immutable records and safe opaque references shared by M05."""

from __future__ import annotations

import math
import unicodedata
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, ClassVar

from .errors import DNAValidationError
from .versions import canonical_value, require_digest, require_identifier, require_version

__all__ = [
    "CanonicalRecord",
    "SemanticRef",
    "freeze_json",
    "thaw_json",
    "require_refs",
]


def freeze_json(value: Any, field: str = "value", *, depth: int = 0) -> Any:
    """Copy JSON data into immutable containers and reject executable/opaque objects."""
    if depth > 128:
        raise DNAValidationError(f"{field} exceeds maximum nesting depth 128")
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise DNAValidationError(f"{field} contains a non-finite number")
        return value
    if type(value) is str:
        normalized = unicodedata.normalize("NFC", value)
        if len(normalized) > 16_384 or any(
            unicodedata.category(char) in {"Cc", "Cf"} for char in normalized
        ):
            raise DNAValidationError(f"{field} contains an oversized or control string")
        return normalized
    if type(value) is dict or type(value) is MappingProxyType:
        if len(value) > 100_000:
            raise DNAValidationError(f"{field} has more than 100000 keys")
        frozen: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise DNAValidationError(f"{field} mapping keys must be strings")
            normalized = unicodedata.normalize("NFC", key)
            if not normalized or normalized in frozen:
                raise DNAValidationError(f"{field} has empty or normalization-colliding keys")
            frozen[normalized] = freeze_json(item, f"{field}.{normalized}", depth=depth + 1)
        return MappingProxyType(dict(sorted(frozen.items())))
    if type(value) in (tuple, list):
        if len(value) > 100_000:
            raise DNAValidationError(f"{field} has more than 100000 sequence items")
        return tuple(freeze_json(item, f"{field}[]", depth=depth + 1) for item in value)
    raise DNAValidationError(f"{field} must contain JSON data, got {type(value).__name__}")


def thaw_json(value: Any) -> Any:
    if type(value) is MappingProxyType or type(value) is dict:
        return {key: thaw_json(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [thaw_json(item) for item in value]
    if value is None or type(value) in (bool, int, float, str):
        return value
    raise DNAValidationError(f"cannot thaw unsupported JSON value type {type(value).__name__}")


class CanonicalRecord:
    """Mixin for frozen records with deterministic data-only payload conversion."""

    __all__: ClassVar[tuple[str, ...]] = ()

    def to_payload(self) -> dict[str, Any]:
        payload = canonical_value(self)
        if not isinstance(payload, dict):
            raise DNAValidationError("canonical record must serialize to an object")
        return payload


@dataclass(frozen=True, order=True)
class SemanticRef(CanonicalRecord):
    """Version-pinned reference to another authority; it carries no external payload."""

    owner_module: str
    family: str
    ref_id: str
    version: str
    revision_id: str | None = None
    content_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "owner_module", require_identifier(self.owner_module, "owner_module"))
        object.__setattr__(self, "family", require_identifier(self.family, "family"))
        object.__setattr__(self, "ref_id", require_identifier(self.ref_id, "ref_id"))
        object.__setattr__(self, "version", require_version(self.version, "version"))
        if self.revision_id is not None:
            object.__setattr__(self, "revision_id", require_identifier(self.revision_id, "revision_id"))
        if self.content_digest is not None:
            object.__setattr__(self, "content_digest", require_digest(self.content_digest, "content_digest"))

    @property
    def text(self) -> str:
        if self.revision_id is None:
            return f"{self.owner_module}:{self.family}:{self.ref_id}@{self.version}"
        return f"{self.owner_module}:{self.family}:{self.ref_id}@{self.version}#{self.revision_id}"

    @property
    def revision_pinned(self) -> bool:
        return self.revision_id is not None


def require_refs(values: Any, field: str) -> tuple[SemanticRef, ...]:
    if not isinstance(values, (tuple, list)):
        raise DNAValidationError(f"{field} must be a sequence of SemanticRef values")
    refs = tuple(
        item if isinstance(item, SemanticRef) else _coerce_ref(item, f"{field}[]")
        for item in values
    )
    identities = [
        (item.owner_module, item.family, item.ref_id, item.version, item.revision_id)
        for item in refs
    ]
    if len(set(identities)) != len(refs):
        raise DNAValidationError(f"{field} contains duplicate references")
    return tuple(sorted(refs))


def _coerce_ref(value: Any, field: str) -> SemanticRef:
    if type(value) is not dict and type(value) is not MappingProxyType:
        raise DNAValidationError(f"{field} must be a SemanticRef or reference object")
    try:
        return SemanticRef(**value)
    except (TypeError, KeyError) as error:
        raise DNAValidationError(f"{field} is not a valid SemanticRef: {error}") from error
