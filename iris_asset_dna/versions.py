"""Version pins and safe canonical data helpers for M05."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import unicodedata
from dataclasses import fields, is_dataclass
from enum import Enum
from types import MappingProxyType, ModuleType
from typing import Any

from .errors import DNAIntegrityError, DNAValidationError

__all__ = [
    "CONTRACT_VERSION",
    "CORE_SCHEMA_VERSION",
    "TRANSPORT_VERSION",
    "VALIDATOR_VERSION",
    "PORT_VERSION",
    "canonical_value",
    "canonical_json",
    "content_digest",
    "require_identifier",
    "require_text",
    "require_semantic_path",
    "require_digest",
    "require_version",
    "require_finite_number",
    "require_unique",
]

CONTRACT_VERSION = "m05-contract-v1.0"
CORE_SCHEMA_VERSION = "iris-m05-core-v1"
TRANSPORT_VERSION = "iris-m05-json-v1"
VALIDATOR_VERSION = "iris-m05-validator-v1"
PORT_VERSION = "iris-m05-ports-v1"

_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,255}$")
_SEMANTIC_SEGMENT = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


def require_identifier(value: Any, field: str = "identifier") -> str:
    if not isinstance(value, str):
        raise DNAValidationError(f"{field} must be a string")
    normalized = unicodedata.normalize("NFC", value.strip())
    if (
        not normalized
        or len(normalized) > 256
        or any(unicodedata.category(char) in {"Cc", "Cf"} for char in normalized)
        or _IDENTIFIER.fullmatch(normalized) is None
    ):
        raise DNAValidationError(f"{field} must be a canonical opaque identifier")
    return normalized


def require_text(value: Any, field: str = "text", *, maximum: int = 16_384) -> str:
    if not isinstance(value, str):
        raise DNAValidationError(f"{field} must be text")
    normalized = unicodedata.normalize("NFC", value.strip())
    if not normalized or len(normalized) > maximum:
        raise DNAValidationError(f"{field} must contain 1..{maximum} characters")
    if any(unicodedata.category(char) in {"Cc", "Cf"} for char in normalized):
        raise DNAValidationError(f"{field} contains a control or format character")
    return normalized


def require_semantic_path(value: Any, field: str = "path") -> str:
    if not isinstance(value, str):
        raise DNAValidationError(f"{field} must be a dotted semantic path")
    normalized = unicodedata.normalize("NFC", value.strip()).lower()
    segments = normalized.split(".")
    if not normalized or len(segments) > 16 or any(
        _SEMANTIC_SEGMENT.fullmatch(segment) is None for segment in segments
    ):
        raise DNAValidationError(f"{field} must contain 1..16 canonical path segments")
    return normalized


def require_digest(value: Any, field: str = "digest") -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise DNAValidationError(f"{field} must be a lowercase SHA-256 digest")
    return value


def require_version(value: Any, field: str = "version") -> str:
    version = require_text(value, field, maximum=64)
    if version.casefold() == "latest":
        raise DNAValidationError(f"{field} must pin an explicit version; latest is forbidden")
    return version


def require_finite_number(value: Any, field: str = "number") -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DNAValidationError(f"{field} must be a finite number")
    if isinstance(value, float) and not math.isfinite(value):
        raise DNAValidationError(f"{field} must be finite")
    return value


def require_unique(values: Any, field: str) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise DNAValidationError(f"{field} must be a sequence of identifiers")
    result = tuple(require_identifier(item, f"{field}[]") for item in values)
    if len(result) != len(set(result)):
        raise DNAValidationError(f"{field} contains duplicate identifiers")
    return result


def _is_bound_package_type(candidate: type) -> bool:
    module_name = type.__getattribute__(candidate, "__module__")
    if not module_name.startswith("iris_asset_dna."):
        return False
    module = sys.modules.get(module_name)
    if type(module) is not ModuleType:
        return False
    name = type.__getattribute__(candidate, "__name__")
    if type.__getattribute__(candidate, "__qualname__") != name:
        return False
    return vars(module).get(name) is candidate


def canonical_value(value: Any, *, _depth: int = 0) -> Any:
    """Convert declared data to JSON values; never execute supplied behavior."""
    if _depth > 128:
        raise DNAValidationError("canonical value exceeds maximum depth 128")
    record_type = type(value)
    if _is_bound_package_type(record_type) and Enum in type.__getattribute__(record_type, "__mro__"):
        return canonical_value(object.__getattribute__(value, "_value_"), _depth=_depth + 1)
    if type(value) is dict or type(value) is MappingProxyType:
        if len(value) > 100_000 or any(not isinstance(key, str) for key in value):
            raise DNAValidationError("canonical mappings require at most 100000 string keys")
        normalized: dict[str, Any] = {}
        for key in sorted(value):
            canonical_key = unicodedata.normalize("NFC", key)
            if canonical_key in normalized:
                raise DNAValidationError("canonical mapping keys collide after Unicode normalization")
            normalized[canonical_key] = canonical_value(value[key], _depth=_depth + 1)
        return normalized
    if type(value) in (tuple, list):
        if len(value) > 100_000:
            raise DNAValidationError("canonical sequence exceeds 100000 entries")
        return [canonical_value(item, _depth=_depth + 1) for item in value]
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is str:
        normalized = unicodedata.normalize("NFC", value)
        if len(normalized) > 16_384 or any(
            unicodedata.category(char) in {"Cc", "Cf"} for char in normalized
        ):
            raise DNAValidationError("canonical string is too long or contains control characters")
        return normalized
    if type(value) is float:
        return require_finite_number(value)
    if _is_bound_package_type(record_type) and is_dataclass(record_type):
        if not any(
            type.__getattribute__(base, "__name__") == "CanonicalRecord"
            and type.__getattribute__(base, "__module__") == "iris_asset_dna.base"
            for base in type.__getattribute__(record_type, "__mro__")
        ):
            raise DNAValidationError("only package CanonicalRecord dataclasses are canonical JSON values")
        instance_values = object.__getattribute__(value, "__dict__")
        if type(instance_values) is not dict:
            raise DNAValidationError("canonical records must store fields as inert dataclass values")
        payload: dict[str, Any] = {}
        for item in fields(record_type):
            if not item.init or item.metadata.get("canonical_exclude", False):
                continue
            if item.name not in instance_values:
                raise DNAIntegrityError(f"canonical record is missing stored field {item.name!r}")
            payload[item.name] = canonical_value(instance_values[item.name], _depth=_depth + 1)
        return payload
    raise DNAValidationError(f"unsupported canonical value type {type(value).__name__}")


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            canonical_value(value),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as error:
        if isinstance(error, DNAValidationError):
            raise
        raise DNAValidationError(f"value cannot be represented as canonical JSON: {error}") from error


def content_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
