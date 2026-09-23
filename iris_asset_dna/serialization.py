"""Versioned data-only JSON transport for the explicitly registered M05 records."""

from __future__ import annotations

import json
import math
import types
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Union, get_args, get_origin, get_type_hints
from collections.abc import Mapping

from . import anchors, analysis, base, compatibility, context, cross_modal, drift, enums, families
from . import identity, imports, invariants, lineage, migration, packages, ports, readiness, risk, traits
from . import transitions, validation
from .base import CanonicalRecord
from .errors import DNAAdmissionError, DNAIntegrityError, DNALimitError, DNAValidationError
from .limits import DEFAULT_LIMITS, DNARecordLimits
from .versions import TRANSPORT_VERSION, canonical_json

__all__ = [
    "serialize_record",
    "deserialize_record",
    "canonical_bytes",
    "registered_record_types",
]

_RECORD_MODULES = (
    anchors, analysis, base, compatibility, context, cross_modal, drift, enums, families,
    identity, imports, invariants, lineage, migration, packages, ports, readiness, risk, traits,
    transitions, validation,
)


def _build_record_registry() -> dict[str, type[CanonicalRecord]]:
    registry: dict[str, type[CanonicalRecord]] = {}
    for module in _RECORD_MODULES:
        for name in getattr(module, "__all__", ()):
            candidate = getattr(module, name, None)
            if not isinstance(candidate, type) or not is_dataclass(candidate):
                continue
            if not issubclass(candidate, CanonicalRecord):
                continue
            tag = f"{candidate.__module__}.{candidate.__qualname__}"
            prior = registry.get(tag)
            if prior is not None and prior is not candidate:
                raise DNAIntegrityError(f"duplicate registered M05 record tag {tag}")
            registry[tag] = candidate
    return dict(sorted(registry.items()))


_TYPE_REGISTRY = _build_record_registry()


def registered_record_types() -> dict[str, type[CanonicalRecord]]:
    """Return the closed, code-defined set of record types accepted by transport."""
    return dict(_TYPE_REGISTRY)


def serialize_record(record: CanonicalRecord, *, limits: DNARecordLimits = DEFAULT_LIMITS) -> bytes:
    if not isinstance(record, CanonicalRecord) or type(record) not in _TYPE_REGISTRY.values():
        raise DNAValidationError("record type is not registered in the M05 transport contract")
    payload = record.to_payload()
    _check_text_lengths(payload, limits.max_text_chars)
    envelope = {
        "transport_version": TRANSPORT_VERSION,
        "kind": f"{type(record).__module__}.{type(record).__qualname__}",
        "payload": payload,
    }
    encoded = canonical_json(envelope).encode("utf-8")
    limits.require("max_inline_payload_bytes", len(encoded))
    return encoded


def canonical_bytes(record: CanonicalRecord, *, limits: DNARecordLimits = DEFAULT_LIMITS) -> bytes:
    """Alias that makes canonical-byte intent explicit at call sites."""
    return serialize_record(record, limits=limits)


def deserialize_record(
    data: bytes | bytearray | memoryview | str,
    *,
    expected_type: type[CanonicalRecord] | None = None,
    limits: DNARecordLimits = DEFAULT_LIMITS,
) -> CanonicalRecord:
    if isinstance(data, str):
        encoded = data.encode("utf-8")
        source = data
    elif isinstance(data, (bytes, bytearray, memoryview)):
        encoded = bytes(data)
        try:
            source = encoded.decode("utf-8")
        except UnicodeDecodeError as error:
            raise DNAValidationError("M05 JSON transport must be valid UTF-8") from error
    else:
        raise DNAValidationError("M05 JSON transport requires bytes or text")
    limits.require("max_inline_payload_bytes", len(encoded))

    try:
        envelope = json.loads(
            source,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except DNAValidationError:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError) as error:
        raise DNAValidationError(f"invalid M05 JSON transport: {error}") from error
    _check_depth(envelope, limits.max_canonical_depth)
    _check_text_lengths(envelope, limits.max_text_chars)
    if not isinstance(envelope, dict) or set(envelope) != {"transport_version", "kind", "payload"}:
        raise DNAValidationError("M05 transport envelope has missing or unknown fields")
    if envelope["transport_version"] != TRANSPORT_VERSION:
        raise DNAValidationError(f"unsupported M05 transport version {envelope['transport_version']!r}")
    if not isinstance(envelope["kind"], str):
        raise DNAValidationError("M05 transport kind must be a string")
    registry = _TYPE_REGISTRY
    record_type = registry.get(envelope["kind"])
    if record_type is None:
        raise DNAAdmissionError(f"unregistered M05 record kind {envelope['kind']!r}")
    if expected_type is not None and record_type is not expected_type:
        raise DNAIntegrityError(
            f"transport record kind {record_type.__name__} does not match expected {expected_type.__name__}"
        )
    return _decode_record(record_type, envelope["payload"], registry)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DNAValidationError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise DNAValidationError(f"non-finite JSON constant {value!r} is forbidden")


def _check_depth(value: Any, maximum: int, depth: int = 0) -> None:
    if depth > maximum:
        raise DNALimitError(f"JSON nesting depth exceeds {maximum}")
    if isinstance(value, dict):
        for nested in value.values():
            _check_depth(nested, maximum, depth + 1)
    elif isinstance(value, list):
        for nested in value:
            _check_depth(nested, maximum, depth + 1)
    elif isinstance(value, float) and not math.isfinite(value):
        raise DNAValidationError("non-finite JSON numbers are forbidden")


def _check_text_lengths(value: Any, maximum: int) -> None:
    if type(value) is str:
        if len(value) > maximum:
            raise DNALimitError(f"text value exceeds {maximum} characters")
    elif type(value) is dict:
        for nested in value.values():
            _check_text_lengths(nested, maximum)
    elif type(value) is list:
        for nested in value:
            _check_text_lengths(nested, maximum)


def _decode_record(
    record_type: type[CanonicalRecord],
    payload: Any,
    registry: dict[str, type[CanonicalRecord]],
) -> CanonicalRecord:
    if not isinstance(payload, dict):
        raise DNAValidationError("M05 record payload must be a JSON object")
    record_fields = {item.name: item for item in fields(record_type) if item.init}
    unknown = set(payload) - set(record_fields)
    if unknown:
        raise DNAValidationError(f"unknown {record_type.__name__} payload fields: {sorted(unknown)}")
    hints = get_type_hints(record_type)
    # dataclasses.MISSING is a singleton, so compare both fields directly without
    # calling a default factory during decoding.
    from dataclasses import MISSING
    missing = {
        name for name, item in record_fields.items()
        if name not in payload and item.default is MISSING and item.default_factory is MISSING
    }
    if missing:
        raise DNAValidationError(f"missing {record_type.__name__} payload fields: {sorted(missing)}")
    values = {
        name: _decode_value(value, hints.get(name, Any), registry)
        for name, value in payload.items()
    }
    try:
        return record_type(**values)
    except DNAValidationError:
        raise
    except (TypeError, ValueError, KeyError) as error:
        raise DNAValidationError(f"invalid {record_type.__name__} payload: {error}") from error


def _decode_value(value: Any, annotation: Any, registry: dict[str, type[CanonicalRecord]]) -> Any:
    if annotation is Any or annotation is object:
        return value
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in (Union, types.UnionType):
        if value is None and type(None) in args:
            return None
        errors: list[Exception] = []
        for option in args:
            if option is type(None):
                continue
            try:
                return _decode_value(value, option, registry)
            except (DNAValidationError, TypeError, ValueError) as error:
                errors.append(error)
        raise DNAValidationError("value does not match any declared union type") from (errors[-1] if errors else None)
    if annotation is type(None):
        if value is None:
            return None
        raise DNAValidationError("expected null")
    if origin is tuple:
        if not isinstance(value, list):
            raise DNAValidationError("tuple field must be represented as a JSON array")
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_decode_value(item, args[0], registry) for item in value)
        if args and len(args) != len(value):
            raise DNAValidationError("tuple field has the wrong number of values")
        return tuple(_decode_value(item, args[index], registry) for index, item in enumerate(value)) if args else tuple(value)
    if origin in (dict, Mapping):
        if not isinstance(value, dict):
            raise DNAValidationError("mapping field must be represented as a JSON object")
        key_type, value_type = args or (str, Any)
        return {
            _decode_value(key, key_type, registry): _decode_value(item, value_type, registry)
            for key, item in value.items()
        }
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        try:
            return annotation(value)
        except (TypeError, ValueError) as error:
            raise DNAValidationError(f"unknown {annotation.__name__} value {value!r}") from error
    if isinstance(annotation, type) and is_dataclass(annotation) and issubclass(annotation, CanonicalRecord):
        tag = f"{annotation.__module__}.{annotation.__qualname__}"
        if registry.get(tag) is not annotation:
            raise DNAValidationError(f"nested record type {annotation.__name__} is not registered")
        return _decode_record(annotation, value, registry)
    if annotation is str:
        if not isinstance(value, str):
            raise DNAValidationError("string field must be a JSON string")
        return value
    if annotation is bool:
        if not isinstance(value, bool):
            raise DNAValidationError("boolean field must be a JSON boolean")
        return value
    if annotation is int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise DNAValidationError("integer field must be a JSON integer")
        return value
    if annotation is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise DNAValidationError("float field must be a finite JSON number")
        return float(value)
    if annotation in (None, type(None)):
        if value is not None:
            raise DNAValidationError("field must be null")
        return None
    raise DNAValidationError(f"unsupported declared transport type {annotation!r}")
