"""Version pins and finite-number-safe canonical JSON helpers for M04."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from dataclasses import fields, is_dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Any, Mapping

from .errors import IRSchemaError

__all__ = [
    "CONTRACT_VERSION",
    "CORE_SCHEMA_VERSION",
    "TRANSPORT_VERSION",
    "VALIDATOR_VERSION",
    "LOWERING_VERSION",
    "require_identifier",
    "require_text",
    "require_digest",
    "require_version",
    "require_finite_number",
    "canonical_value",
    "canonical_json",
    "content_digest",
]

CONTRACT_VERSION = "m04-contract-v1.0"
CORE_SCHEMA_VERSION = "iris-m04-core-v1"
TRANSPORT_VERSION = "iris-m04-json-v1"
VALIDATOR_VERSION = "iris-m04-validator-v1"
LOWERING_VERSION = "iris-m04-lowering-v1"

_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,255}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN = set("<>[]{}|\\^`")


def require_identifier(value: Any, field: str = "identifier") -> str:
    if not isinstance(value, str):
        raise IRSchemaError(f"{field} must be a string")
    normalized = unicodedata.normalize("NFC", value.strip())
    if not normalized or len(normalized) > 256 or any(ord(ch) < 32 for ch in normalized):
        raise IRSchemaError(f"{field} must be non-empty, control-free, and at most 256 characters")
    if any(ch in _FORBIDDEN for ch in normalized) or _IDENTIFIER.fullmatch(normalized) is None:
        raise IRSchemaError(f"{field} is not a canonical identifier: {normalized!r}")
    return normalized


def require_text(value: Any, field: str = "text", *, maximum: int = 4096) -> str:
    if not isinstance(value, str):
        raise IRSchemaError(f"{field} must be text")
    normalized = unicodedata.normalize("NFC", value.strip())
    if not normalized or len(normalized) > maximum:
        raise IRSchemaError(f"{field} must contain 1..{maximum} characters")
    if any(unicodedata.category(ch) in {"Cc", "Cf"} for ch in normalized):
        raise IRSchemaError(f"{field} contains a control or format character")
    return normalized


def require_digest(value: Any, field: str = "digest") -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise IRSchemaError(f"{field} must be a lowercase SHA-256 digest")
    return value


def require_version(value: Any, field: str = "version") -> str:
    return require_text(value, field, maximum=64)


def require_finite_number(value: Any, field: str = "number") -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise IRSchemaError(f"{field} must be a finite number")
    if isinstance(value, float) and not math.isfinite(value):
        raise IRSchemaError(f"{field} must be finite; NaN and Infinity are not canonical")
    return value


def canonical_value(value: Any) -> Any:
    """Convert only declared data values; never execute schema-provided behavior."""
    from enum import Enum

    if isinstance(value, Enum):
        return canonical_value(value.value)
    if isinstance(value, Fraction):
        return {"denominator": value.denominator, "numerator": value.numerator}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise IRSchemaError("non-finite Decimal values are not canonical")
        return format(value.normalize(), "f")
    if isinstance(value, float):
        return require_finite_number(value)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise IRSchemaError("canonical mappings require string keys")
        return {key: canonical_value(value[key]) for key in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [canonical_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        items = [canonical_value(item) for item in value]
        return sorted(items, key=lambda item: canonical_json(item))
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: canonical_value(getattr(value, item.name))
            for item in fields(value)
        }
    if type(value).__module__.startswith("iris_intent.") and callable(getattr(type(value), "to_payload", None)):
        return canonical_value(value.to_payload())
    raise IRSchemaError(f"unsupported canonical value type {type(value).__name__}")


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
        if isinstance(error, IRSchemaError):
            raise
        raise IRSchemaError(f"value cannot be represented as canonical JSON: {error}") from error


def content_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
