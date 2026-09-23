"""Deterministic versioned JSON transport with an explicit closed-type decoder."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from types import ModuleType
from typing import Any

from .base import M08Record, canonical_bytes, content_digest
from .errors import MicrobenchmarkAdmissionError, MicrobenchmarkCompatibilityError, MicrobenchmarkError, MicrobenchmarkIntegrityError, MicrobenchmarkLimitError, MicrobenchmarkSecurityError, MicrobenchmarkValidationError
from .limits import DEFAULT_LIMITS
from .schema import ExtensionField, SchemaDescriptor
from .versions import TRANSPORT_VERSION, require_digest, require_nonnegative_int

__all__ = ["VersionedRecordDocument", "create_document", "encode_document", "decode_document", "verify_document"]


@dataclass(frozen=True)
class VersionedRecordDocument(M08Record):
    schema: SchemaDescriptor
    record: M08Record
    extensions: tuple[ExtensionField, ...]
    created_at_ms: int
    parent_document_digest: str | None
    document_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema", SchemaDescriptor.coerce(self.schema, "schema"))
        if not isinstance(self.record, M08Record):
            raise MicrobenchmarkValidationError("versioned document record must be an M08Record")
        if not is_dataclass(self.record):
            raise MicrobenchmarkValidationError("versioned document record must be a registered immutable dataclass")
        extensions = tuple(ExtensionField.coerce(item, "extensions[]") for item in self.extensions)
        keys = tuple((item.namespace, item.key) for item in extensions)
        if len(keys) != len(set(keys)):
            raise MicrobenchmarkIntegrityError("document repeats a namespaced extension field")
        DEFAULT_LIMITS.require("max_json_items", len(extensions))
        object.__setattr__(self, "extensions", extensions)
        object.__setattr__(self, "created_at_ms", require_nonnegative_int(self.created_at_ms, "created_at_ms"))
        if self.parent_document_digest is not None:
            object.__setattr__(self, "parent_document_digest", require_digest(self.parent_document_digest, "parent_document_digest"))
        object.__setattr__(self, "document_digest", require_digest(self.document_digest, "document_digest"))
        expected = _document_digest(self.schema, self.record, extensions, self.created_at_ms, self.parent_document_digest)
        if self.document_digest != expected:
            raise MicrobenchmarkIntegrityError("versioned document digest does not match semantic payload")


def _document_digest(schema: SchemaDescriptor, record: M08Record, extensions: tuple[ExtensionField, ...], created_at_ms: int, parent: str | None) -> str:
    return content_digest({
        "transport_version": TRANSPORT_VERSION,
        "schema": schema,
        "record": record,
        "extensions": extensions,
        "created_at_ms": created_at_ms,
        "parent_document_digest": parent,
    })


def create_document(
    schema: SchemaDescriptor,
    record: M08Record,
    *,
    extensions: tuple[ExtensionField, ...] = (),
    created_at_ms: int,
    parent_document_digest: str | None = None,
) -> VersionedRecordDocument:
    schema = SchemaDescriptor.coerce(schema, "schema")
    values = tuple(ExtensionField.coerce(item, "extensions[]") for item in extensions)
    return VersionedRecordDocument(
        schema, record, values, created_at_ms, parent_document_digest,
        _document_digest(schema, record, values, created_at_ms, parent_document_digest),
    )


def encode_document(document: VersionedRecordDocument) -> str:
    document = VersionedRecordDocument.coerce(document, "document")
    return canonical_bytes(document).decode("utf-8")


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MicrobenchmarkSecurityError(f"serialized document repeats JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise MicrobenchmarkSecurityError(f"serialized document contains forbidden numeric constant {value}")


def _trusted_registries() -> tuple[dict[str, type], dict[str, type[Enum]]]:
    from . import calibration, contracts, enums as enum_module, envelopes, evidence, fingerprints, probes, protocols, provenance, schema, serialization
    modules: tuple[ModuleType, ...] = (calibration, contracts, enum_module, envelopes, evidence, fingerprints, probes, protocols, provenance, schema, serialization)
    records: dict[str, type] = {}
    enum_types: dict[str, type[Enum]] = {}
    for module in modules:
        for value in vars(module).values():
            if isinstance(value, type) and value.__module__ == module.__name__ and value.__qualname__ == value.__name__:
                tag = f"{module.__name__}.{value.__qualname__}"
                if issubclass(value, Enum):
                    enum_types[tag] = value
                elif issubclass(value, M08Record) and is_dataclass(value):
                    records[tag] = value
    return records, enum_types


def _decode_node(value: Any, records: dict[str, type], enums: dict[str, type[Enum]], *, depth: int = 0) -> Any:
    if depth > DEFAULT_LIMITS.max_json_depth:
        raise MicrobenchmarkLimitError("serialized document exceeds maximum nesting depth")
    if type(value) is list:
        DEFAULT_LIMITS.require("max_json_items", len(value))
        return tuple(_decode_node(item, records, enums, depth=depth + 1) for item in value)
    if type(value) is dict:
        if set(value) == {"$enum"}:
            tag = value["$enum"]
            if type(tag) is not str or "." not in tag:
                raise MicrobenchmarkSecurityError("serialized enum tag is malformed")
            enum_tag, member = tag.rsplit(".", 1)
            enum_type = enums.get(enum_tag)
            if enum_type is None or member not in enum_type.__members__:
                raise MicrobenchmarkAdmissionError("serialized document names an unknown M08 enum")
            return enum_type[member]
        if "$enum" in value:
            raise MicrobenchmarkSecurityError("serialized object collides with a reserved enum marker")
        if "$type" in value:
            tag = value.get("$type")
            if type(tag) is not str:
                raise MicrobenchmarkSecurityError("serialized record tag is malformed")
            record_type = records.get(tag)
            if record_type is None:
                raise MicrobenchmarkAdmissionError("serialized document names an unregistered M08 record")
            declared = {field.name for field in fields(record_type) if field.init and not field.metadata.get("canonical_exclude", False)}
            supplied = set(value) - {"$type"}
            if supplied != declared:
                raise MicrobenchmarkCompatibilityError("serialized record fields do not exactly match its registered schema")
            payload = {key: _decode_node(item, records, enums, depth=depth + 1) for key, item in value.items() if key != "$type"}
            try:
                return record_type(**payload)
            except (TypeError, ValueError) as error:
                raise MicrobenchmarkValidationError(f"serialized M08 record is invalid: {error}") from error
        if "$type" in value or any(type(key) is not str for key in value):
            raise MicrobenchmarkSecurityError("serialized object has an invalid reserved key")
        DEFAULT_LIMITS.require("max_json_items", len(value))
        return {key: _decode_node(item, records, enums, depth=depth + 1) for key, item in value.items()}
    if value is None or type(value) in (bool, int, float, str):
        return value
    raise MicrobenchmarkValidationError("serialized document contains an unsupported JSON node")


def decode_document(payload: str | bytes) -> VersionedRecordDocument:
    raw = payload.encode("utf-8") if isinstance(payload, str) else payload
    if type(raw) is not bytes:
        raise MicrobenchmarkValidationError("serialized document must be UTF-8 text or bytes")
    DEFAULT_LIMITS.require("max_inline_payload_bytes", len(raw))
    try:
        parsed = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_pairs, parse_constant=_reject_constant)
    except MicrobenchmarkError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise MicrobenchmarkValidationError(f"serialized document is not bounded UTF-8 JSON: {error}") from error
    if type(parsed) is not dict:
        raise MicrobenchmarkValidationError("serialized document root must be an object")
    records, enums = _trusted_registries()
    decoded = _decode_node(parsed, records, enums)
    if type(decoded) is not VersionedRecordDocument:
        raise MicrobenchmarkCompatibilityError("serialized document root is not a registered M08 versioned document")
    verify_document(decoded)
    return decoded


def verify_document(document: VersionedRecordDocument) -> bool:
    document = VersionedRecordDocument.coerce(document, "document")
    if document.document_digest != _document_digest(document.schema, document.record, document.extensions, document.created_at_ms, document.parent_document_digest):
        raise MicrobenchmarkIntegrityError("document semantic round-trip digest mismatch")
    return True
