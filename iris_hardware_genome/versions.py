"""Frozen M07 version axes and strict primitive validators."""

from __future__ import annotations

import math
import re
import unicodedata
from typing import Any, Iterable

from .errors import HardwareGenomeValidationError

__all__ = [
    "CONTRACT_VERSION", "CORE_SCHEMA_VERSION", "TRANSPORT_VERSION", "VALIDATOR_VERSION",
    "REGISTRY_VERSION", "FINGERPRINT_VERSION", "MIGRATION_VERSION", "require_identifier",
    "require_text", "require_version", "require_digest", "require_finite_number",
    "require_nonnegative_int", "require_unique",
]

CONTRACT_VERSION = "m07-contract-v1.0"
CORE_SCHEMA_VERSION = "iris-m07-core-v1"
TRANSPORT_VERSION = "iris-m07-json-v1"
VALIDATOR_VERSION = "iris-m07-validator-v1"
REGISTRY_VERSION = "iris-m07-semantic-registry-v1"
FINGERPRINT_VERSION = "iris-m07-fingerprint-v1"
MIGRATION_VERSION = "iris-m07-migration-v1"

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


def require_identifier(value: Any, field: str = "identifier") -> str:
    if not isinstance(value, str):
        raise HardwareGenomeValidationError(f"{field} must be a string")
    normalized = unicodedata.normalize("NFC", value.strip())
    if (
        not normalized
        or len(normalized) > 256
        or _IDENTIFIER.fullmatch(normalized) is None
        or any(unicodedata.category(char) in {"Cc", "Cf"} for char in normalized)
    ):
        raise HardwareGenomeValidationError(f"{field} must be a canonical opaque identifier")
    return normalized


def require_text(value: Any, field: str = "text", *, maximum: int = 4_096, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise HardwareGenomeValidationError(f"{field} must be text")
    normalized = unicodedata.normalize("NFC", value.strip())
    if (not normalized and not allow_empty) or len(normalized) > maximum:
        minimum = 0 if allow_empty else 1
        raise HardwareGenomeValidationError(f"{field} must contain {minimum}..{maximum} characters")
    if any(unicodedata.category(char) in {"Cc", "Cf"} for char in normalized):
        raise HardwareGenomeValidationError(f"{field} contains a control or format character")
    return normalized


def require_version(value: Any, field: str = "version") -> str:
    version = require_text(value, field, maximum=128)
    if version.casefold() in {"latest", "current", "*"}:
        raise HardwareGenomeValidationError(f"{field} must pin an explicit version")
    return version


def require_digest(value: Any, field: str = "digest") -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise HardwareGenomeValidationError(f"{field} must be a lowercase SHA-256 digest")
    return value


def require_finite_number(value: Any, field: str = "number") -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HardwareGenomeValidationError(f"{field} must be a finite number")
    if isinstance(value, float) and not math.isfinite(value):
        raise HardwareGenomeValidationError(f"{field} must be finite")
    return value


def require_nonnegative_int(value: Any, field: str = "value") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise HardwareGenomeValidationError(f"{field} must be a non-negative integer")
    return value


def require_unique(values: Iterable[Any], field: str, *, maximum: int = 100_000) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise HardwareGenomeValidationError(f"{field} must be a tuple or list")
    if len(values) > maximum:
        raise HardwareGenomeValidationError(f"{field} exceeds maximum length {maximum}")
    result = tuple(require_identifier(value, f"{field}[]") for value in values)
    if len(set(result)) != len(result):
        raise HardwareGenomeValidationError(f"{field} contains duplicates")
    return result
