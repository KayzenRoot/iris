"""Closed tagged JSON serialization with no dynamic imports or executable tags."""

from __future__ import annotations

import json
import math
import sys
import unicodedata
from dataclasses import fields, is_dataclass
from enum import Enum
from types import MappingProxyType, ModuleType
from typing import Any

from .base import record_tag
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError, HardwareGenomeLimitError, HardwareGenomeValidationError
from .limits import DEFAULT_LIMITS, HardwareGenomeLimits
from .versions import TRANSPORT_VERSION

__all__ = ["canonical_serialize", "canonical_deserialize", "canonical_fingerprint", "semantic_round_trip", "registered_record_tags"]

_MODULE_NAMES = (
    "base", "capabilities", "deltas", "discovery", "enums", "errors", "evidence", "families", "genome",
    "invariants", "limits", "media", "migration", "precision", "projections", "recovery", "redaction",
    "registry", "schema", "subjects", "telemetry", "topology", "validation", "versions", "ports",
)


def _static_registry() -> tuple[dict[str, type], dict[str, type]]:
    records: dict[str, type] = {}
    enums: dict[str, type] = {}
    for name in _MODULE_NAMES:
        module = sys.modules.get(f"iris_hardware_genome.{name}")
        if not isinstance(module, ModuleType):
            continue
        for symbol in getattr(module, "__all__", ()):
            candidate = vars(module).get(symbol)
            if not isinstance(candidate, type) or candidate.__module__ != module.__name__ or candidate.__qualname__ != symbol:
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


def canonical_serialize(value: Any, *, limits: HardwareGenomeLimits = DEFAULT_LIMITS) -> bytes:
    records, enums = _static_registry()
    root = record_tag(value)
    if root not in records:
        raise HardwareGenomeAdmissionError(f"record type {root!r} is outside the closed M07 serialization registry")
    envelope = {"format": TRANSPORT_VERSION, "record": _encode(value, records, enums, depth=0, limits=limits)}
    try:
        result = json.dumps(envelope, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        if isinstance(error, HardwareGenomeValidationError):
            raise
        raise HardwareGenomeValidationError(f"M07 record cannot be represented as canonical JSON: {error}") from error
    limits.require("max_inline_payload_bytes", len(result))
    return result


def canonical_deserialize(data: bytes | str, *, limits: HardwareGenomeLimits = DEFAULT_LIMITS) -> Any:
    if type(data) is bytes:
        limits.require("max_inline_payload_bytes", len(data))
        try:
            source = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise HardwareGenomeValidationError("serialized M07 input must be valid UTF-8") from error
    elif type(data) is str:
        source = data
        limits.require("max_inline_payload_bytes", len(source.encode("utf-8")))
    else:
        raise HardwareGenomeValidationError("serialized M07 input must be exact bytes or text")
    try:
        envelope = json.loads(source, object_pairs_hook=_pairs_no_duplicates, parse_constant=_reject_constant)
    except HardwareGenomeValidationError:
        raise
    except (json.JSONDecodeError, RecursionError, UnicodeError) as error:
        raise HardwareGenomeValidationError(f"serialized M07 input is invalid JSON: {error}") from error
    if type(envelope) is not dict or set(envelope) != {"format", "record"} or envelope["format"] != TRANSPORT_VERSION:
        raise HardwareGenomeAdmissionError("serialized M07 envelope has an unknown format or shape")
    records, enums = _static_registry()
    value = _decode(envelope["record"], records, enums, depth=0, limits=limits)
    if type(value) not in records.values():
        raise HardwareGenomeAdmissionError("serialized M07 root must be a registered immutable record")
    if canonical_serialize(value, limits=limits) != source.encode("utf-8"):
        raise HardwareGenomeIntegrityError("serialized M07 input is valid but not in canonical byte form")
    return value


def canonical_fingerprint(value: Any, *, limits: HardwareGenomeLimits = DEFAULT_LIMITS) -> str:
    import hashlib

    return hashlib.sha256(canonical_serialize(value, limits=limits)).hexdigest()


def semantic_round_trip(value: Any, *, limits: HardwareGenomeLimits = DEFAULT_LIMITS) -> Any:
    restored = canonical_deserialize(canonical_serialize(value, limits=limits), limits=limits)
    if restored != value:
        raise HardwareGenomeIntegrityError("M07 canonical round-trip changed immutable semantics")
    return restored


def _encode(value: Any, records: dict[str, type], enums: dict[str, type], *, depth: int, limits: HardwareGenomeLimits) -> Any:
    if depth > limits.max_json_depth:
        raise HardwareGenomeLimitError("M07 record exceeds maximum serialization depth")
    candidate = type(value)
    if value is None or candidate in (bool, int):
        return value
    if candidate is str:
        normalized_text = unicodedata.normalize("NFC", value)
        if len(normalized_text) > limits.max_text_chars or any(unicodedata.category(char) in {"Cc", "Cf"} for char in normalized_text):
            raise HardwareGenomeValidationError("serialized M07 string is oversized or contains controls")
        return normalized_text
    if candidate is float:
        if not math.isfinite(value):
            raise HardwareGenomeValidationError("non-finite numbers are forbidden in M07 serialization")
        return value
    if isinstance(value, Enum):
        tag = f"{candidate.__module__}.{candidate.__qualname__}"
        if enums.get(tag) is not candidate:
            raise HardwareGenomeAdmissionError(f"enum type {tag!r} is outside the closed M07 registry")
        return {"$enum": tag, "value": _encode(value.value, records, enums, depth=depth + 1, limits=limits)}
    if is_dataclass(candidate):
        tag = record_tag(value)
        if records.get(tag) is not candidate:
            raise HardwareGenomeAdmissionError(f"record type {tag!r} is outside the closed M07 registry")
        stored = object.__getattribute__(value, "__dict__")
        payload: dict[str, Any] = {}
        for item in fields(candidate):
            if not item.init or item.metadata.get("canonical_exclude", False):
                continue
            if item.name not in stored:
                raise HardwareGenomeIntegrityError(f"M07 record lacks declared field {item.name!r}")
            payload[item.name] = _encode(stored[item.name], records, enums, depth=depth + 1, limits=limits)
        return {"$record": tag, "fields": payload}
    if candidate in (dict, MappingProxyType):
        limits.require("max_json_items", len(value))
        entries: list[list[Any]] = []
        normalized_keys: set[str] = set()
        for key, item in value.items():
            if type(key) is not str:
                raise HardwareGenomeValidationError("M07 serialized mapping keys must be strings")
            key = unicodedata.normalize("NFC", key)
            if not key or key in normalized_keys:
                raise HardwareGenomeValidationError("M07 serialized mapping has empty/colliding keys")
            normalized_keys.add(key)
            entries.append([key, _encode(item, records, enums, depth=depth + 1, limits=limits)])
        return {"$map": sorted(entries, key=lambda item: item[0])}
    if candidate in (tuple, list):
        limits.require("max_json_items", len(value))
        return {"$tuple": [_encode(item, records, enums, depth=depth + 1, limits=limits) for item in value]}
    raise HardwareGenomeValidationError(f"unsupported M07 serialized type {candidate.__name__}")


def _decode(value: Any, records: dict[str, type], enums: dict[str, type], *, depth: int, limits: HardwareGenomeLimits) -> Any:
    if depth > limits.max_json_depth:
        raise HardwareGenomeLimitError("serialized M07 input exceeds maximum depth")
    if value is None or type(value) in (bool, int, float, str):
        if type(value) is float and not math.isfinite(value):
            raise HardwareGenomeValidationError("non-finite serialized M07 number")
        if type(value) is str:
            normalized = unicodedata.normalize("NFC", value)
            if len(normalized) > limits.max_text_chars or any(unicodedata.category(char) in {"Cc", "Cf"} for char in normalized):
                raise HardwareGenomeValidationError("serialized M07 text is oversized or contains controls")
            return normalized
        return value
    if type(value) is not dict:
        raise HardwareGenomeValidationError("serialized M07 values must be primitives or tagged objects")
    if set(value) == {"$enum", "value"}:
        cls = enums.get(value["$enum"])
        if cls is None:
            raise HardwareGenomeAdmissionError(f"unknown or forbidden M07 enum tag {value['$enum']!r}")
        try:
            return cls(_decode(value["value"], records, enums, depth=depth + 1, limits=limits))
        except ValueError as error:
            raise HardwareGenomeAdmissionError("serialized M07 enum value is unknown") from error
    if set(value) == {"$record", "fields"}:
        cls = records.get(value["$record"])
        if cls is None:
            raise HardwareGenomeAdmissionError(f"unknown or forbidden M07 record tag {value['$record']!r}")
        payload = value["fields"]
        if type(payload) is not dict:
            raise HardwareGenomeValidationError("serialized M07 record fields must be an object")
        expected = {item.name for item in fields(cls) if item.init and not item.metadata.get("canonical_exclude", False)}
        if set(payload) != expected:
            raise HardwareGenomeAdmissionError("serialized M07 record has missing or unknown fields")
        decoded = {key: _decode(item, records, enums, depth=depth + 1, limits=limits) for key, item in payload.items()}
        try:
            return cls(**decoded)
        except (TypeError, ValueError) as error:
            raise HardwareGenomeValidationError(f"serialized M07 record failed validation: {error}") from error
    if set(value) == {"$map"}:
        pairs = value["$map"]
        if type(pairs) is not list:
            raise HardwareGenomeValidationError("serialized M07 mapping must be an array of pairs")
        limits.require("max_json_items", len(pairs))
        result: dict[str, Any] = {}
        for pair in pairs:
            if type(pair) is not list or len(pair) != 2 or type(pair[0]) is not str:
                raise HardwareGenomeValidationError("serialized M07 mapping entry must be [string, value]")
            key = unicodedata.normalize("NFC", pair[0])
            if not key or key in result:
                raise HardwareGenomeValidationError("serialized M07 map has empty or duplicate keys")
            result[key] = _decode(pair[1], records, enums, depth=depth + 1, limits=limits)
        if list(result) != sorted(result):
            raise HardwareGenomeIntegrityError("serialized M07 map keys are not canonically ordered")
        return MappingProxyType(result)
    if set(value) == {"$tuple"}:
        items = value["$tuple"]
        if type(items) is not list:
            raise HardwareGenomeValidationError("serialized M07 tuple must be an array")
        limits.require("max_json_items", len(items))
        return tuple(_decode(item, records, enums, depth=depth + 1, limits=limits) for item in items)
    raise HardwareGenomeAdmissionError("serialized M07 object has an unknown tag or unrecognized fields")


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise HardwareGenomeValidationError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise HardwareGenomeValidationError(f"non-finite JSON token {value!r} is forbidden")
