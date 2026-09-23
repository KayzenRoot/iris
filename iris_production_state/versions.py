"""Frozen M06 version axes and strict primitive validators."""

from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

from .errors import ProductionStateValidationError

__all__ = [
    "CONTRACT_VERSION",
    "CORE_SCHEMA_VERSION",
    "TRANSPORT_VERSION",
    "VALIDATOR_VERSION",
    "PORT_VERSION",
    "FINGERPRINT_VERSION",
    "OPERATIONAL_REVISION_VERSION",
    "CONTENT_DIGEST_VERSION",
    "require_identifier",
    "require_text",
    "require_version",
    "require_digest_hex",
    "require_finite_number",
    "require_nonnegative_int",
    "require_unique",
]

CONTRACT_VERSION = "m06-contract-v1.0"
CORE_SCHEMA_VERSION = "iris-m06-core-v1"
TRANSPORT_VERSION = "iris-m06-json-v1"
VALIDATOR_VERSION = "iris-m06-validator-v1"
PORT_VERSION = "iris-m06-ports-v1"
FINGERPRINT_VERSION = "iris-m06-fingerprint-v1"
OPERATIONAL_REVISION_VERSION = "iris-m06-operational-revision-v1"
CONTENT_DIGEST_VERSION = "iris-m06-content-digest-v1"

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_HEX = re.compile(r"^[0-9a-f]+$")


def require_identifier(value: Any, field: str = "identifier") -> str:
    if not isinstance(value, str):
        raise ProductionStateValidationError(f"{field} must be a string")
    normalized = unicodedata.normalize("NFC", value.strip())
    if (
        not normalized
        or len(normalized) > 256
        or any(unicodedata.category(char) in {"Cc", "Cf"} for char in normalized)
        or _IDENTIFIER.fullmatch(normalized) is None
    ):
        raise ProductionStateValidationError(f"{field} must be a canonical opaque identifier")
    return normalized


def require_text(value: Any, field: str = "text", *, maximum: int = 16_384, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ProductionStateValidationError(f"{field} must be text")
    normalized = unicodedata.normalize("NFC", value.strip())
    if (not normalized and not allow_empty) or len(normalized) > maximum:
        minimum = 0 if allow_empty else 1
        raise ProductionStateValidationError(f"{field} must contain {minimum}..{maximum} characters")
    if any(unicodedata.category(char) in {"Cc", "Cf"} for char in normalized):
        raise ProductionStateValidationError(f"{field} contains a control or format character")
    return normalized


def require_version(value: Any, field: str = "version") -> str:
    version = require_text(value, field, maximum=64)
    if version.casefold() in {"latest", "current"}:
        raise ProductionStateValidationError(f"{field} must pin an explicit version")
    return version


def require_digest_hex(value: Any, field: str = "digest", *, minimum: int = 32, maximum: int = 256, length: int | None = None) -> str:
    if length is not None:
        minimum = maximum = length
    if (
        not isinstance(value, str)
        or len(value) < minimum
        or len(value) > maximum
        or _HEX.fullmatch(value) is None
    ):
        raise ProductionStateValidationError(f"{field} must be lowercase hexadecimal with {minimum}..{maximum} characters")
    return value


def require_finite_number(value: Any, field: str = "number") -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProductionStateValidationError(f"{field} must be a finite number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ProductionStateValidationError(f"{field} must be finite")
    return value


def require_nonnegative_int(value: Any, field: str = "value") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProductionStateValidationError(f"{field} must be a non-negative integer")
    return value


def require_unique(values: Any, field: str, *, maximum: int = 100_000) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise ProductionStateValidationError(f"{field} must be a sequence")
    if len(values) > maximum:
        raise ProductionStateValidationError(f"{field} exceeds the maximum of {maximum} values")
    result = tuple(require_identifier(item, f"{field}[]") for item in values)
    if len(result) != len(set(result)):
        raise ProductionStateValidationError(f"{field} contains duplicates")
    return result
