"""Versioned identity primitives shared by every M03 value object.

M03 borrows M01's :class:`QualityClass` ladder and :class:`ComponentVersion` by object
identity rather than re-declaring them: a quality rung that M03 owned privately would be
a second quality authority, which the frozen contract forbids.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any, Mapping

from iris_quality.contracts import QualityClass
from iris_quality.versions import CONTRACT_VERSION as M01_CONTRACT_VERSION
from iris_quality.versions import ComponentVersion

from .errors import SchemaValidationError, UnsupportedVersionError

__all__ = [
    "CONTRACT_VERSION",
    "SUPPORTED_CONTRACT_VERSIONS",
    "SCHEMA_VERSION",
    "SUPPORTED_SCHEMA_VERSIONS",
    "M01_CONTRACT_VERSION",
    "M01_COMPONENT_VERSION",
    "QualityClass",
    "ComponentVersion",
    "canonical_json",
    "content_digest",
    "require_contract_version",
    "require_digest",
    "require_identifier",
    "require_schema_version",
    "require_semantic_path",
    "require_text",
    "require_unit_interval",
    "require_unique",
    "require_version_text",
]

CONTRACT_VERSION = "m03-contract-v1.0"
SUPPORTED_CONTRACT_VERSIONS: frozenset[str] = frozenset({CONTRACT_VERSION})

SCHEMA_VERSION = "iris-intent-schema-v1"
SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({SCHEMA_VERSION})

M01_COMPONENT_VERSION = ComponentVersion(
    identifier="m01-quality-contract", version=M01_CONTRACT_VERSION
)

_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_PATH_SEGMENT = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_FORBIDDEN_ID_CHARACTERS = set("<>[]{}|\\^`")
MAX_SEMANTIC_PATH_SEGMENTS = 12
HEX_DIGEST_LENGTHS = frozenset({32, 40, 56, 64, 71, 128})


def _reject_control_characters(value: str, field: str) -> None:
    for character in value:
        if unicodedata.category(character) in {"Cc", "Cf"}:
            raise SchemaValidationError(f"{field} contains a control character {character!r}")


def require_identifier(value: Any, field: str) -> str:
    """A stable, comparable id. Human prose never enters this shape."""

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


def require_semantic_path(value: Any, field: str = "semantic_path") -> str:
    """An addressable semantic location such as ``identity.spokesperson.voice``.

    Paths are the unit of slicing, fingerprinting and conflict scoping, so their shape is
    fixed by the schema rather than left to whatever a caller typed.
    """

    if not isinstance(value, str):
        raise SchemaValidationError(f"{field} must be a dotted semantic path string")
    normalized = value.strip().lower()
    if not normalized:
        raise SchemaValidationError(f"{field} must not be empty")
    _reject_control_characters(normalized, field)
    segments = normalized.split(".")
    if len(segments) > MAX_SEMANTIC_PATH_SEGMENTS:
        raise SchemaValidationError(
            f"{field} may hold at most {MAX_SEMANTIC_PATH_SEGMENTS} segments, got {len(segments)}"
        )
    for segment in segments:
        if _PATH_SEGMENT.fullmatch(segment) is None:
            raise SchemaValidationError(
                f"{field} segment {segment!r} must match ^[a-z0-9][a-z0-9_-]{{0,63}}$"
            )
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


def require_version_text(value: Any, field: str) -> str:
    return require_text(value, field, maximum=64)


def require_digest(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise SchemaValidationError(f"{field} must be a lowercase hex digest string")
    normalized = value.strip().lower()
    if len(normalized) not in HEX_DIGEST_LENGTHS or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise SchemaValidationError(f"{field} is not a canonical hex digest, got {value!r}")
    return normalized


def require_schema_version(value: Any) -> str:
    return require_supported("schema", value, SUPPORTED_SCHEMA_VERSIONS)


def require_contract_version(value: Any) -> str:
    return require_supported("contract", value, SUPPORTED_CONTRACT_VERSIONS)


def require_supported(kind: str, value: Any, supported: frozenset[str]) -> str:
    version = require_version_text(value, f"{kind} version")
    if version not in supported:
        raise UnsupportedVersionError(
            f"unsupported {kind} version {version!r}; this kernel accepts {sorted(supported)}"
        )
    return version


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_digest(value: Any, *, algorithm: str = "sha256") -> str:
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as error:
        raise SchemaValidationError(f"unsupported digest algorithm {algorithm!r}") from error
    hasher.update(canonical_json(value).encode("utf-8"))
    return hasher.hexdigest()
