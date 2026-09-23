"""Closed, deterministic tagged JSON serialization with strict type admission."""

from __future__ import annotations

import hashlib
import json
import math
import sys
import unicodedata
from dataclasses import fields, is_dataclass
from enum import Enum
from types import MappingProxyType, ModuleType
from typing import Any

import iris_asset_dna as m05
import iris_project_os as m02

from .base import record_tag
from .errors import ProductionStateAdmissionError, ProductionStateIntegrityError, ProductionStateLimitError, ProductionStateValidationError
from .limits import DEFAULT_LIMITS, ProductionStateLimits
from .versions import TRANSPORT_VERSION

__all__ = ["canonical_serialize", "canonical_deserialize", "canonical_fingerprint", "semantic_round_trip", "registered_record_tags"]


_M02_MODULES = tuple(getattr(m02, name) for name in (
    "analysis", "archive", "base", "branching", "build", "diffing", "errors", "graph", "identity",
    "lifecycle", "machines", "merge", "ports", "promotion", "release", "reuse", "snapshots", "stores", "versions",
))
_M05_MODULES = tuple(getattr(m05, name) for name in (
    "anchors", "analysis", "base", "compatibility", "context", "cross_modal", "drift", "enums", "errors",
    "families", "identity", "imports", "invariants", "lineage", "limits", "migration", "packages", "ports",
    "readiness", "risk", "serialization", "traits", "transitions", "validation", "versions",
))


def _m06_modules() -> tuple[ModuleType, ...]:
    names = (
        "base", "dependencies", "enums", "errors", "families", "invariants", "limits", "lineage", "migration",
        "ports", "reconstruction", "regeneration", "release", "revisions", "versions",
    )
    return tuple(sys.modules[f"iris_production_state.{name}"] for name in names if f"iris_production_state.{name}" in sys.modules)


def _static_registry() -> tuple[dict[str, type], dict[str, type]]:
    records: dict[str, type] = {}
    enums: dict[str, type] = {}
    modules = (*_M02_MODULES, *_M05_MODULES, *_m06_modules())
    for module in modules:
        for name, candidate in vars(module).items():
            if not isinstance(candidate, type) or candidate.__module__ != module.__name__ or candidate.__qualname__ != name:
                continue
            tag = f"{candidate.__module__}.{candidate.__qualname__}"
            if issubclass(candidate, Enum):
                enums[tag] = candidate
            elif is_dataclass(candidate):
                records[tag] = candidate
    return records, enums


def registered_record_tags() -> tuple[str, ...]:
    records, _ = _static_registry()
    return tuple(sorted(records))


def canonical_serialize(value: Any, *, limits: ProductionStateLimits = DEFAULT_LIMITS) -> bytes:
    records, enums = _static_registry()
    root_tag = record_tag(value)
    if root_tag not in records:
        raise ProductionStateAdmissionError(f"record type {root_tag!r} is outside the closed serialization registry")
    envelope = {"format": TRANSPORT_VERSION, "record": _encode(value, records, enums, depth=0, limits=limits)}
    try:
        result = json.dumps(envelope, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise ProductionStateValidationError(f"record cannot be represented as canonical JSON: {error}") from error
    limits.require("max_inline_payload_bytes", len(result))
    return result


def canonical_deserialize(data: bytes | str, *, limits: ProductionStateLimits = DEFAULT_LIMITS) -> Any:
    if type(data) is bytes:
        if len(data) > limits.max_inline_payload_bytes:
            raise ProductionStateLimitError("serialized document exceeds configured byte limit")
        try:
            source = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ProductionStateValidationError("serialized document must be valid UTF-8") from error
    elif type(data) is str:
        source = data
        if len(source.encode("utf-8")) > limits.max_inline_payload_bytes:
            raise ProductionStateLimitError("serialized document exceeds configured byte limit")
    else:
        raise ProductionStateValidationError("serialized document must be exact bytes or text")
    try:
        envelope = json.loads(source, object_pairs_hook=_pairs_no_duplicates, parse_constant=_reject_constant)
    except ProductionStateValidationError:
        raise
    except (json.JSONDecodeError, RecursionError, UnicodeError) as error:
        raise ProductionStateValidationError(f"serialized document is invalid JSON: {error}") from error
    if type(envelope) is not dict or set(envelope) != {"format", "record"} or envelope["format"] != TRANSPORT_VERSION:
        raise ProductionStateAdmissionError("serialized document has an unknown format or envelope shape")
    records, enums = _static_registry()
    value = _decode(envelope["record"], records, enums, depth=0, limits=limits)
    if type(value) not in records.values():
        raise ProductionStateAdmissionError("serialized document root must be a registered immutable record")
    if canonical_serialize(value, limits=limits) != source.encode("utf-8"):
        raise ProductionStateIntegrityError("serialized input is valid but not in canonical byte form")
    return value


def canonical_fingerprint(value: Any, *, limits: ProductionStateLimits = DEFAULT_LIMITS) -> str:
    return hashlib.sha256(canonical_serialize(value, limits=limits)).hexdigest()


def semantic_round_trip(value: Any, *, limits: ProductionStateLimits = DEFAULT_LIMITS) -> Any:
    restored = canonical_deserialize(canonical_serialize(value, limits=limits), limits=limits)
    if restored != value:
        raise ProductionStateIntegrityError("canonical semantic round-trip changed the immutable record")
    return restored


def _encode(value: Any, records: dict[str, type], enums: dict[str, type], *, depth: int, limits: ProductionStateLimits) -> Any:
    if depth > limits.max_json_depth:
        raise ProductionStateLimitError("record exceeds maximum serialization nesting depth")
    candidate = type(value)
    if value is None or candidate in (bool, int, str):
        if candidate is str:
            text = unicodedata.normalize("NFC", value)
            if len(text) > limits.max_text_chars or any(unicodedata.category(char) in {"Cc", "Cf"} for char in text):
                raise ProductionStateValidationError("serialized strings must be bounded and free of control characters")
            return text
        return value
    if candidate is float:
        if not math.isfinite(value):
            raise ProductionStateValidationError("non-finite JSON numbers are forbidden")
        return value
    if isinstance(value, Enum):
        tag = f"{candidate.__module__}.{candidate.__qualname__}"
        if tag not in enums:
            raise ProductionStateAdmissionError(f"enum type {tag!r} is outside the closed serialization registry")
        return {"$enum": tag, "value": _encode(value.value, records, enums, depth=depth + 1, limits=limits)}
    if is_dataclass(candidate):
        tag = record_tag(value)
        if records.get(tag) is not candidate:
            raise ProductionStateAdmissionError(f"record type {tag!r} is outside the closed serialization registry")
        stored = object.__getattribute__(value, "__dict__")
        payload: dict[str, Any] = {}
        for item in fields(candidate):
            if not item.init or item.metadata.get("canonical_exclude", False):
                continue
            if item.name not in stored:
                raise ProductionStateIntegrityError(f"record lacks declared field {item.name!r}")
            payload[item.name] = _encode(stored[item.name], records, enums, depth=depth + 1, limits=limits)
        return {"$record": tag, "fields": payload}
    if candidate in (dict, MappingProxyType):
        limits.require("max_json_items", len(value))
        pairs = []
        normalized: set[str] = set()
        for key, item in value.items():
            if type(key) is not str:
                raise ProductionStateValidationError("serialized mapping keys must be strings")
            canonical_key = unicodedata.normalize("NFC", key)
            if not canonical_key or canonical_key in normalized:
                raise ProductionStateValidationError("serialized mapping keys are empty or collide after normalization")
            normalized.add(canonical_key)
            pairs.append([canonical_key, _encode(item, records, enums, depth=depth + 1, limits=limits)])
        return {"$map": sorted(pairs, key=lambda item: item[0])}
    if candidate in (tuple, list):
        limits.require("max_json_items", len(value))
        return {"$tuple": [_encode(item, records, enums, depth=depth + 1, limits=limits) for item in value]}
    raise ProductionStateValidationError(f"unsupported canonical serialized value type {candidate.__name__}")


def _decode(value: Any, records: dict[str, type], enums: dict[str, type], *, depth: int, limits: ProductionStateLimits) -> Any:
    if depth > limits.max_json_depth:
        raise ProductionStateLimitError("serialized document exceeds maximum nesting depth")
    if value is None or type(value) in (bool, int, float, str):
        if type(value) is float and not math.isfinite(value):
            raise ProductionStateValidationError("non-finite JSON numbers are forbidden")
        if type(value) is str and (len(value) > limits.max_text_chars or any(unicodedata.category(char) in {"Cc", "Cf"} for char in value)):
            raise ProductionStateValidationError("serialized text is oversized or contains control characters")
        return unicodedata.normalize("NFC", value) if type(value) is str else value
    if type(value) is not dict:
        raise ProductionStateValidationError("serialized values must be tagged objects or JSON primitives")
    if set(value) == {"$enum", "value"}:
        cls = enums.get(value["$enum"])
        if cls is None:
            raise ProductionStateAdmissionError(f"unknown or forbidden enum tag {value['$enum']!r}")
        return cls(_decode(value["value"], records, enums, depth=depth + 1, limits=limits))
    if set(value) == {"$record", "fields"}:
        cls = records.get(value["$record"])
        if cls is None:
            raise ProductionStateAdmissionError(f"unknown or forbidden record tag {value['$record']!r}")
        payload = value["fields"]
        if type(payload) is not dict:
            raise ProductionStateValidationError("record fields must be an object")
        expected = {item.name for item in fields(cls) if item.init and not item.metadata.get("canonical_exclude", False)}
        if set(payload) != expected:
            raise ProductionStateAdmissionError(f"record {value['$record']!r} contains missing or unknown fields")
        decoded = {key: _decode(item, records, enums, depth=depth + 1, limits=limits) for key, item in payload.items()}
        try:
            return cls(**decoded)
        except (TypeError, ValueError) as error:
            raise ProductionStateValidationError(f"record {value['$record']!r} failed schema validation: {error}") from error
    if set(value) == {"$map"}:
        pairs = value["$map"]
        if type(pairs) is not list or len(pairs) > limits.max_json_items:
            raise ProductionStateLimitError("serialized mapping exceeds configured item limit")
        result: dict[str, Any] = {}
        for pair in pairs:
            if type(pair) is not list or len(pair) != 2 or type(pair[0]) is not str:
                raise ProductionStateValidationError("serialized map entries must be [string, value] pairs")
            key = unicodedata.normalize("NFC", pair[0])
            if not key or key in result:
                raise ProductionStateValidationError("serialized map has empty or duplicate normalized keys")
            result[key] = _decode(pair[1], records, enums, depth=depth + 1, limits=limits)
        if list(result) != sorted(result):
            raise ProductionStateIntegrityError("serialized mapping keys are not in canonical sorted order")
        return MappingProxyType(result)
    if set(value) == {"$tuple"}:
        items = value["$tuple"]
        if type(items) is not list or len(items) > limits.max_json_items:
            raise ProductionStateLimitError("serialized tuple exceeds configured item limit")
        return tuple(_decode(item, records, enums, depth=depth + 1, limits=limits) for item in items)
    raise ProductionStateAdmissionError("serialized object has an unknown tag or unrecognized fields")


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProductionStateValidationError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ProductionStateValidationError(f"non-finite JSON token {value!r} is forbidden")
