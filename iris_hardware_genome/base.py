"""Closed immutable data records and deterministic JSON primitives for M07."""

from __future__ import annotations

import hashlib
import json
import math
import sys
import unicodedata
from dataclasses import MISSING, fields, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, ClassVar

from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError, HardwareGenomeLimitError, HardwareGenomeValidationError
from .limits import DEFAULT_LIMITS, HardwareGenomeLimits

__all__ = [
    "M07Record", "freeze_json", "thaw_json", "canonical_value", "canonical_json", "canonical_bytes",
    "content_digest", "record_tag", "require_sequence",
]


class M07Record:
    """Base for frozen records whose fields contain inert semantic data only."""

    __all__: ClassVar[tuple[str, ...]] = ()

    def to_payload(self) -> dict[str, Any]:
        if not is_dataclass(self):
            raise HardwareGenomeValidationError("M07 records must be dataclasses")
        return {
            item.name: canonical_value(getattr(self, item.name))
            for item in fields(self)
            if item.init and not item.metadata.get("canonical_exclude", False)
        }

    @classmethod
    def coerce(cls, value: Any, field: str = "value"):
        if isinstance(value, cls):
            if type(value) is not cls:
                raise HardwareGenomeValidationError(f"{field} must be an exact {cls.__name__} record")
            return value
        if type(value) is not dict:
            raise HardwareGenomeValidationError(f"{field} must be a {cls.__name__} record")
        known = {item.name for item in fields(cls) if item.init}  # type: ignore[arg-type]
        required = {
            item.name for item in fields(cls)  # type: ignore[arg-type]
            if item.init and item.default is MISSING and item.default_factory is MISSING
        }
        if set(value) - known or required - set(value):
            raise HardwareGenomeValidationError(f"{field} has unknown or missing {cls.__name__} fields")
        try:
            return cls(**value)
        except (TypeError, ValueError) as error:
            raise HardwareGenomeValidationError(f"{field} is not a valid {cls.__name__}: {error}") from error


def _bound_package_type(candidate: type) -> bool:
    module_name = type.__getattribute__(candidate, "__module__")
    if not module_name.startswith("iris_hardware_genome."):
        return False
    module = sys.modules.get(module_name)
    name = type.__getattribute__(candidate, "__name__")
    return (
        module is not None
        and type.__getattribute__(candidate, "__qualname__") == name
        and vars(module).get(name) is candidate
    )


def record_tag(value: Any) -> str:
    candidate = type(value)
    if not _bound_package_type(candidate) or not is_dataclass(candidate):
        raise HardwareGenomeAdmissionError(f"unregistered M07 record type {candidate.__name__}")
    return f"{candidate.__module__}.{candidate.__qualname__}"


def freeze_json(value: Any, field: str = "value", *, depth: int = 0, limits: HardwareGenomeLimits = DEFAULT_LIMITS) -> Any:
    """Copy exact JSON primitives into immutable containers under explicit bounds."""
    if depth > limits.max_json_depth:
        raise HardwareGenomeLimitError(f"{field} exceeds maximum nesting depth {limits.max_json_depth}")
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise HardwareGenomeValidationError(f"{field} contains a non-finite number")
        return value
    if type(value) is str:
        normalized = unicodedata.normalize("NFC", value)
        if len(normalized) > limits.max_text_chars or any(unicodedata.category(char) in {"Cc", "Cf"} for char in normalized):
            raise HardwareGenomeValidationError(f"{field} contains oversized or control text")
        return normalized
    if type(value) in (dict, MappingProxyType):
        limits.require("max_json_items", len(value))
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise HardwareGenomeValidationError(f"{field} mapping keys must be strings")
            normalized = unicodedata.normalize("NFC", key)
            if not normalized or normalized in result:
                raise HardwareGenomeValidationError(f"{field} has empty or normalization-colliding keys")
            result[normalized] = freeze_json(item, f"{field}.{normalized}", depth=depth + 1, limits=limits)
        return MappingProxyType(dict(sorted(result.items())))
    if type(value) in (tuple, list):
        limits.require("max_json_items", len(value))
        return tuple(freeze_json(item, f"{field}[]", depth=depth + 1, limits=limits) for item in value)
    raise HardwareGenomeValidationError(f"{field} must contain inert JSON data, got {type(value).__name__}")


def thaw_json(value: Any) -> Any:
    if type(value) in (dict, MappingProxyType):
        return {key: thaw_json(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [thaw_json(item) for item in value]
    if value is None or type(value) in (bool, int, float, str):
        return value
    raise HardwareGenomeValidationError(f"cannot thaw {type(value).__name__} as JSON data")


def canonical_value(value: Any, *, depth: int = 0, limits: HardwareGenomeLimits = DEFAULT_LIMITS) -> Any:
    if depth > limits.max_json_depth:
        raise HardwareGenomeLimitError(f"canonical value exceeds maximum depth {limits.max_json_depth}")
    candidate = type(value)
    if isinstance(value, Enum):
        if not _bound_package_type(candidate):
            raise HardwareGenomeAdmissionError(f"unregistered M07 enum type {candidate.__name__}")
        return canonical_value(value.value, depth=depth + 1, limits=limits)
    if candidate in (dict, MappingProxyType):
        limits.require("max_json_items", len(value))
        result: dict[str, Any] = {}
        for key in sorted(value):
            if type(key) is not str:
                raise HardwareGenomeValidationError("canonical mappings require string keys")
            normalized = unicodedata.normalize("NFC", key)
            if not normalized or normalized in result:
                raise HardwareGenomeValidationError("canonical mapping keys are empty or collide after normalization")
            result[normalized] = canonical_value(value[key], depth=depth + 1, limits=limits)
        return result
    if candidate in (tuple, list):
        limits.require("max_json_items", len(value))
        return [canonical_value(item, depth=depth + 1, limits=limits) for item in value]
    if value is None or candidate in (bool, int):
        return value
    if candidate is str:
        return freeze_json(value, "canonical string", limits=limits)
    if candidate is float:
        return freeze_json(value, "canonical number", limits=limits)
    if is_dataclass(candidate):
        record_tag(value)
        stored = object.__getattribute__(value, "__dict__")
        if type(stored) is not dict:
            raise HardwareGenomeValidationError("M07 records must store inert dataclass fields")
        payload: dict[str, Any] = {}
        for item in fields(candidate):
            if item.init and not item.metadata.get("canonical_exclude", False):
                if item.name not in stored:
                    raise HardwareGenomeIntegrityError(f"M07 record is missing field {item.name!r}")
                payload[item.name] = canonical_value(stored[item.name], depth=depth + 1, limits=limits)
        return payload
    raise HardwareGenomeValidationError(f"unsupported canonical value type {candidate.__name__}")


def canonical_json(value: Any, *, limits: HardwareGenomeLimits = DEFAULT_LIMITS) -> str:
    try:
        return json.dumps(canonical_value(value, limits=limits), ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError, RecursionError) as error:
        if isinstance(error, HardwareGenomeValidationError):
            raise
        raise HardwareGenomeValidationError(f"value cannot be represented as canonical JSON: {error}") from error


def canonical_bytes(value: Any, *, limits: HardwareGenomeLimits = DEFAULT_LIMITS) -> bytes:
    result = canonical_json(value, limits=limits).encode("utf-8")
    limits.require("max_inline_payload_bytes", len(result))
    return result


def content_digest(value: Any, *, limits: HardwareGenomeLimits = DEFAULT_LIMITS) -> str:
    return hashlib.sha256(canonical_bytes(value, limits=limits)).hexdigest()


def require_sequence(value: Any, field: str, *, maximum: int, item_type: type | tuple[type, ...] | None = None) -> tuple[Any, ...]:
    if not isinstance(value, (tuple, list)):
        raise HardwareGenomeValidationError(f"{field} must be a sequence")
    if len(value) > maximum:
        raise HardwareGenomeLimitError(f"{field} exceeds maximum length {maximum}")
    result = tuple(value)
    if item_type is not None and any(type(item) not in (item_type if isinstance(item_type, tuple) else (item_type,)) for item in result):
        raise HardwareGenomeValidationError(f"{field} contains a value of the wrong exact type")
    return result
