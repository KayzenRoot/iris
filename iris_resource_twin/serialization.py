"""Deterministic, bounded JSON codec with an explicit M09 type registry."""

from __future__ import annotations

import json
from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
import math
from types import MappingProxyType
from typing import Any
import unicodedata

from . import evidence, families, invariants, leases, limits, mobility, model, recovery, schema, shaping, twin, versioning, migration
from .limits import DEFAULT_LIMITS, M09Limits

__all__ = ["serialize", "deserialize", "round_trip"]


_MODULES = (evidence, families, invariants, leases, limits, mobility, model, recovery, schema, shaping, twin, versioning, migration)
_RECORDS: dict[str, type] = {}
_ENUMS: dict[str, type[Enum]] = {}
for _module in _MODULES:
    for _name in getattr(_module, "__all__", ()):
        _candidate = getattr(_module, _name, None)
        if isinstance(_candidate, type):
            _tag = f"{_candidate.__module__}.{_candidate.__qualname__}"
            if is_dataclass(_candidate):
                _RECORDS[_tag] = _candidate
            if issubclass(_candidate, Enum):
                _ENUMS[_tag] = _candidate


def serialize(value: Any, *, limits: M09Limits = DEFAULT_LIMITS) -> str:
    payload = _encode(value, limits=limits, depth=0)
    result = json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
    limits.require("max_payload_bytes", len(result.encode("utf-8")))
    return result


def deserialize(payload: str | bytes, *, limits: M09Limits = DEFAULT_LIMITS) -> Any:
    if type(payload) is bytes:
        if len(payload) > limits.max_payload_bytes:
            raise ValueError("serialized payload exceeds maximum byte length")
        payload = payload.decode("utf-8")
    if type(payload) is not str:
        raise ValueError("serialized payload must be bounded UTF-8 text")
    if len(payload.encode("utf-8")) > limits.max_payload_bytes:
        raise ValueError("serialized payload exceeds maximum byte length")

    def no_duplicate_keys(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON object keys are forbidden")
            result[key] = value
        return result

    try:
        raw = json.loads(payload, object_pairs_hook=no_duplicate_keys, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"invalid JSON constant {value}")))
    except (json.JSONDecodeError, UnicodeDecodeError, RecursionError, ValueError) as error:
        raise ValueError(f"invalid bounded M09 JSON: {error}") from error
    return _decode(raw, limits=limits, depth=0)


def round_trip(value: Any, *, limits: M09Limits = DEFAULT_LIMITS) -> Any:
    result = deserialize(serialize(value, limits=limits), limits=limits)
    if result != value:
        raise ValueError("M09 semantic round-trip changed the record")
    return result


def _encode(value: Any, *, limits: M09Limits, depth: int) -> Any:
    if depth > limits.max_json_depth:
        raise ValueError("serialization nesting depth exceeded")
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("non-finite numbers are not canonical M09 values")
        return value
    if type(value) is str:
        text = unicodedata.normalize("NFC", value)
        if len(text) > limits.max_text_chars or any(unicodedata.category(char) in {"Cc", "Cf"} for char in text):
            raise ValueError("serialized text exceeds bounds or contains control characters")
        return text
    if isinstance(value, Enum):
        tag = f"{type(value).__module__}.{type(value).__qualname__}"
        if _ENUMS.get(tag) is not type(value):
            raise ValueError("enum type is not registered for M09 serialization")
        return {"$enum": tag, "name": value.name}
    if is_dataclass(value) and not isinstance(value, type):
        candidate = type(value)
        tag = f"{candidate.__module__}.{candidate.__qualname__}"
        if _RECORDS.get(tag) is not candidate:
            raise ValueError("record type is not registered for M09 serialization")
        return {
            "$record": tag,
            "fields": {
                item.name: _encode(getattr(value, item.name), limits=limits, depth=depth + 1)
                for item in fields(value) if item.init
            },
        }
    if type(value) in (tuple, list):
        limits.require("max_json_items", len(value))
        marker = "$tuple" if type(value) is tuple else "$list"
        return {marker: [_encode(item, limits=limits, depth=depth + 1) for item in value]}
    if type(value) in (dict, MappingProxyType):
        limits.require("max_json_items", len(value))
        normalized_items: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str or key.startswith("$"):
                raise ValueError("serialized mappings require ordinary non-marker string keys")
            normalized_key = unicodedata.normalize("NFC", key)
            if not normalized_key or len(normalized_key) > limits.max_text_chars or any(unicodedata.category(char) in {"Cc", "Cf"} for char in normalized_key):
                raise ValueError("serialized mapping key is empty, oversized or contains control characters")
            if normalized_key in normalized_items:
                raise ValueError("mapping keys collide after Unicode normalization")
            normalized_items[normalized_key] = item
        return {"$mapping": {key: _encode(item, limits=limits, depth=depth + 1) for key, item in sorted(normalized_items.items())}}
    raise ValueError(f"unsupported M09 serialization type {type(value).__name__}")


def _decode(value: Any, *, limits: M09Limits, depth: int) -> Any:
    if depth > limits.max_json_depth:
        raise ValueError("deserialization nesting depth exceeded")
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("non-finite JSON numbers are forbidden")
        return value
    if type(value) is str:
        if unicodedata.normalize("NFC", value) != value or len(value) > limits.max_text_chars or any(unicodedata.category(char) in {"Cc", "Cf"} for char in value):
            raise ValueError("JSON text is non-canonical or exceeds text bounds")
        return value
    if type(value) is list:
        raise ValueError("untagged arrays are not valid canonical M09 payloads")
    if type(value) is not dict:
        raise ValueError("unsupported JSON payload node")
    if set(value) == {"$enum", "name"}:
        enum_type = _ENUMS.get(value["$enum"])
        if enum_type is None or type(value["name"]) is not str:
            raise ValueError("unregistered enum or malformed enum payload")
        try:
            return enum_type[value["name"]]
        except KeyError as error:
            raise ValueError("unknown enum member") from error
    if set(value) == {"$tuple"} or set(value) == {"$list"}:
        marker = "$tuple" if "$tuple" in value else "$list"
        if type(value[marker]) is not list:
            raise ValueError("sequence marker must contain an array")
        limits.require("max_json_items", len(value[marker]))
        result = [_decode(item, limits=limits, depth=depth + 1) for item in value[marker]]
        return tuple(result) if marker == "$tuple" else result
    if set(value) == {"$mapping"}:
        raw = value["$mapping"]
        if type(raw) is not dict:
            raise ValueError("mapping marker must contain an object")
        limits.require("max_json_items", len(raw))
        decoded_mapping: dict[str, Any] = {}
        for key, item in raw.items():
            if type(key) is not str or not key or key.startswith("$") or unicodedata.normalize("NFC", key) != key:
                raise ValueError("mapping keys must be canonical ordinary non-marker text")
            if len(key) > limits.max_text_chars or any(unicodedata.category(char) in {"Cc", "Cf"} for char in key):
                raise ValueError("mapping key exceeds text bounds or contains control characters")
            decoded_mapping[key] = _decode(item, limits=limits, depth=depth + 1)
        return MappingProxyType(dict(sorted(decoded_mapping.items())))
    if set(value) == {"$record", "fields"}:
        cls = _RECORDS.get(value["$record"])
        data = value["fields"]
        if cls is None or type(data) is not dict:
            raise ValueError("unregistered record or malformed fields")
        allowed = {item.name for item in fields(cls) if item.init}
        required = {item.name for item in fields(cls) if item.init and item.default is MISSING and item.default_factory is MISSING}
        if set(data) - allowed:
            raise ValueError("record payload contains unknown fields")
        decoded = {key: _decode(item, limits=limits, depth=depth + 1) for key, item in data.items()}
        if required - set(decoded):
            raise ValueError("record payload is missing required fields")
        try:
            return cls(**decoded)
        except (TypeError, ValueError, KeyError) as error:
            raise ValueError(f"record failed semantic validation: {error}") from error
    raise ValueError("unknown or ambiguous serialization marker")
