from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping

from .errors import SchemaValidationError, UnsupportedVersionError

__all__ = [
    "CONTRACT_VERSION",
    "SUPPORTED_CONTRACT_VERSIONS",
    "SCHEMA_VERSION",
    "SUPPORTED_SCHEMA_VERSIONS",
    "ComponentVersion",
    "canonical_json",
    "content_digest",
]

CONTRACT_VERSION = "m01-contract-v1.0"
SUPPORTED_CONTRACT_VERSIONS: frozenset[str] = frozenset({CONTRACT_VERSION})

SCHEMA_VERSION = "iris-quality-schema-v1"
SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({SCHEMA_VERSION})

_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_FORBIDDEN_ID_CHARACTERS = set("<>[]{}|\\^`")


def _reject_control_characters(value: str, field: str) -> None:
    for character in value:
        if unicodedata.category(character) in {"Cc", "Cf"}:
            raise SchemaValidationError(f"{field} contains a control character {character!r}")


def require_identifier(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise SchemaValidationError(f"{field} must be a string, got {type(value).__name__}")
    normalized = value.strip()
    if not normalized:
        raise SchemaValidationError(f"{field} must not be empty")
    _reject_control_characters(normalized, field)
    if any(character in normalized for character in _FORBIDDEN_ID_CHARACTERS):
        raise SchemaValidationError(f"{field} contains forbidden characters: {normalized!r}")
    if _IDENTIFIER_PATTERN.fullmatch(normalized) is None:
        raise SchemaValidationError(
            f"{field} must match ^[a-z0-9][a-z0-9._-]{{0,127}}$, got {normalized!r}"
        )
    return normalized


def require_text(value: Any, field: str, *, maximum: int = 2048) -> str:
    if not isinstance(value, str):
        raise SchemaValidationError(f"{field} must be a string, got {type(value).__name__}")
    normalized = value.strip()
    if not normalized:
        raise SchemaValidationError(f"{field} must not be empty")
    _reject_control_characters(normalized, field)
    if len(normalized) > maximum:
        raise SchemaValidationError(f"{field} exceeds {maximum} characters ({len(normalized)})")
    return normalized


def require_unit_interval(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaValidationError(f"{field} must be a number in [0, 1]")
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise SchemaValidationError(f"{field} must be within [0, 1], got {number}")
    return number


def require_unique(values: Any, field: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise SchemaValidationError(f"{field} must be a list of identifiers")
    identifiers = tuple(require_identifier(value, f"{field}[]") for value in values)
    duplicates = sorted({name for name in identifiers if identifiers.count(name) > 1})
    if duplicates:
        raise SchemaValidationError(f"{field} contains duplicate identifiers: {duplicates}")
    return identifiers


@dataclass(frozen=True)
class ComponentVersion:
    """A version-identifiable component reference used by contracts, judges and decisions."""

    identifier: str
    version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "identifier", require_identifier(self.identifier, "identifier"))
        object.__setattr__(self, "version", require_text(self.version, "version", maximum=64))

    @property
    def reference(self) -> str:
        return f"{self.identifier}@{self.version}"

    def to_payload(self) -> dict[str, Any]:
        return {"identifier": self.identifier, "version": self.version}

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ComponentVersion:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("ComponentVersion must be a mapping")
        unexpected = set(payload) - {"identifier", "version"}
        if unexpected:
            raise SchemaValidationError(
                f"ComponentVersion has unknown keys: {sorted(unexpected)}"
            )
        try:
            return cls(payload["identifier"], payload["version"])
        except KeyError as error:
            raise SchemaValidationError(f"ComponentVersion is missing {error.args[0]!r}") from error


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_digest(value: Any, *, algorithm: str = "sha256") -> str:
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as error:
        raise SchemaValidationError(f"unsupported digest algorithm {algorithm!r}") from error
    hasher.update(canonical_json(value).encode("utf-8"))
    return hasher.hexdigest()


def require_supported_version(
    kind: str, value: Any, supported: frozenset[str]
) -> str:
    version = require_text(value, f"{kind} version", maximum=64)
    if version not in supported:
        raise UnsupportedVersionError(
            f"unsupported {kind} version {version!r}; this kernel accepts {sorted(supported)}"
        )
    return version
