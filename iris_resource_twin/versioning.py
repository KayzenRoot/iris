"""Versioned immutable M09 documents and loss-explicit migration primitives."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from .limits import DEFAULT_LIMITS, M09Limits
from .model import content_digest, require_id

__all__ = [
    "SchemaDescriptor", "CompatibilityLevel", "ExtensionField", "VersionedDocument",
    "create_document", "verify_document", "freeze_value", "thaw_value",
]


@dataclass(frozen=True, order=True)
class SchemaDescriptor:
    schema_id: str
    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", require_id(self.schema_id, "schema_id"))
        for field in ("major", "minor", "patch"):
            value = getattr(self, field)
            if type(value) is not int or not 0 <= value <= 65_535:
                raise ValueError(f"{field} must be a bounded non-negative integer")

    @property
    def version(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


class CompatibilityLevel:
    PATCH = "PATCH"
    MINOR = "MINOR"
    MAJOR = "MAJOR"


@dataclass(frozen=True)
class ExtensionField:
    namespace: str
    key: str
    version: str
    required: bool
    value: Any

    def __post_init__(self) -> None:
        for field in ("namespace", "key"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.version) is not str or len(self.version) > 32 or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", self.version):
            raise ValueError("extension version must be semantic version text")
        if type(self.required) is not bool:
            raise ValueError("extension required marker must be boolean")
        object.__setattr__(self, "value", freeze_value(self.value, field=f"{self.namespace}:{self.key}"))


@dataclass(frozen=True)
class VersionedDocument:
    document_id: str
    schema: SchemaDescriptor
    body: Any
    extensions: tuple[ExtensionField, ...]
    created_at_ms: int
    parent_document_digest: str | None
    document_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "document_id", require_id(self.document_id, "document_id"))
        if type(self.schema) is not SchemaDescriptor:
            raise ValueError("schema must be a SchemaDescriptor")
        object.__setattr__(self, "body", freeze_value(self.body, field="body"))
        extensions = tuple(self.extensions)
        if len(extensions) > 2_048 or any(type(item) is not ExtensionField for item in extensions):
            raise ValueError("extensions must be bounded ExtensionField records")
        extensions = tuple(sorted(extensions, key=lambda item: (item.namespace, item.key)))
        if len({(item.namespace, item.key) for item in extensions}) != len(extensions):
            raise ValueError("extension fields must have unique namespace/key identities")
        object.__setattr__(self, "extensions", extensions)
        if type(self.created_at_ms) is not int or self.created_at_ms < 0:
            raise ValueError("created_at_ms must be non-negative")
        if self.parent_document_digest is not None and not _is_digest(self.parent_document_digest):
            raise ValueError("parent digest must be lowercase SHA-256")
        expected = content_digest(self.semantic_payload())
        if self.document_digest and self.document_digest != expected:
            raise ValueError("document digest does not match canonical semantic fields")
        object.__setattr__(self, "document_digest", expected)

    def semantic_payload(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "schema": self.schema,
            "body": thaw_value(self.body),
            "extensions": self.extensions,
            "created_at_ms": self.created_at_ms,
            "parent_document_digest": self.parent_document_digest,
        }


def create_document(
    schema: SchemaDescriptor,
    body: Mapping[str, Any],
    *,
    document_id: str,
    created_at_ms: int,
    extensions: tuple[ExtensionField, ...] = (),
    parent_document_digest: str | None = None,
    limits: M09Limits = DEFAULT_LIMITS,
) -> VersionedDocument:
    frozen_body = freeze_value(body, field="body", limits=limits)
    return VersionedDocument(document_id, schema, frozen_body, extensions, created_at_ms, parent_document_digest, "")


def verify_document(document: VersionedDocument) -> bool:
    if type(document) is not VersionedDocument:
        raise ValueError("document must be an exact VersionedDocument")
    if document.document_digest != content_digest(document.semantic_payload()):
        raise ValueError("versioned document digest mismatch")
    return True


def freeze_value(value: Any, *, field: str, limits: M09Limits = DEFAULT_LIMITS, depth: int = 0) -> Any:
    if depth > limits.max_json_depth:
        raise ValueError(f"{field} exceeds maximum nesting depth")
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float:
        import math
        if not math.isfinite(value):
            raise ValueError(f"{field} contains a non-finite number")
        return value
    if type(value) is str:
        text = unicodedata.normalize("NFC", value)
        if len(text) > limits.max_text_chars or any(unicodedata.category(char) in {"Cc", "Cf"} for char in text):
            raise ValueError(f"{field} contains oversized or control text")
        return text
    if isinstance(value, Mapping):
        limits.require("max_json_items", len(value))
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field} mapping keys must be strings")
            normalized = unicodedata.normalize("NFC", key)
            if not normalized or normalized in result or normalized.startswith("$"):
                raise ValueError(f"{field} has a reserved, empty, or colliding key")
            result[normalized] = freeze_value(item, field=f"{field}.{normalized}", limits=limits, depth=depth + 1)
        return MappingProxyType(dict(sorted(result.items())))
    if type(value) in (tuple, list):
        limits.require("max_json_items", len(value))
        return tuple(freeze_value(item, field=f"{field}[]", limits=limits, depth=depth + 1) for item in value)
    raise ValueError(f"{field} must contain inert JSON values")


def thaw_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: thaw_value(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [thaw_value(item) for item in value]
    if value is None or type(value) in (bool, int, float, str):
        return value
    raise ValueError(f"cannot thaw unsupported value type {type(value).__name__}")


def _is_digest(value: str) -> bool:
    return type(value) is str and len(value) == 64 and all(char in "0123456789abcdef" for char in value)
