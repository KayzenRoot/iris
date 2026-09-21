"""M02 version, identifier and canonicalisation primitives.

M02 owns its own contract and schema versions, but deliberately shares one
canonical JSON form and one identifier grammar with M01: a fingerprint written by
either module has to read the same way, or cross-module evidence cannot be
compared without a second, drifting definition of "the same bytes".
"""

from __future__ import annotations

import functools
import re
from typing import Any, Callable, Mapping, Sequence

from iris_quality.contracts import QualityClass
from iris_quality.errors import SchemaValidationError as ForeignSchemaValidationError
from iris_quality.errors import UnsupportedVersionError as ForeignUnsupportedVersionError
from iris_quality.versions import (
    ComponentVersion,
    canonical_json,
    content_digest,
)
from iris_quality.versions import (
    require_identifier as foreign_require_identifier,
)
from iris_quality.versions import (
    require_supported_version as foreign_require_supported_version,
)
from iris_quality.versions import (
    require_text as foreign_require_text,
)
from iris_quality.versions import (
    require_unique as foreign_require_unique,
)

from .errors import SchemaValidationError, UnsupportedVersionError

__all__ = [
    "CONTRACT_VERSION",
    "SUPPORTED_CONTRACT_VERSIONS",
    "SCHEMA_VERSION",
    "SUPPORTED_SCHEMA_VERSIONS",
    "ComponentVersion",
    "canonical_json",
    "content_digest",
    "require_identifier",
    "require_unique",
    "require_text",
    "require_supported_version",
    "require_digest",
    "require_millis",
    "require_scalar",
    "require_metadata",
    "require_bounded",
    "require_reference",
    "require_optional_text",
    "require_component_version",
    "require_version_text",
    "require_quality_class",
    "SHA256_PATTERN",
]

CONTRACT_VERSION = "m02-contract-v1.0"
SUPPORTED_CONTRACT_VERSIONS: frozenset[str] = frozenset({CONTRACT_VERSION})

SCHEMA_VERSION = "iris-project-os-schema-v1"
SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({SCHEMA_VERSION})

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
MIN_MILLIS = 0
MAX_MILLIS = 4_102_444_800_000  # 2100-01-01T00:00:00Z, far beyond any admitted clock skew.
MAX_VERSION_TEXT = 64
MAX_METADATA_VALUE_TEXT = 256

IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


def _owns_the_refusal(function: Callable[..., Any]) -> Callable[..., Any]:
    """Re-raise one borrowed M01 refusal through M02's own error surface.

    M02 shares M01's identifier grammar and canonical JSON on purpose, so it must not
    fork them. The exception classes are not shared: a caller that catches
    ``iris_project_os.errors`` should never have to also catch M01's hierarchy just
    because a validator underneath it was reused.
    """

    @functools.wraps(function)
    def guarded(*args: Any, **kwargs: Any) -> Any:
        try:
            return function(*args, **kwargs)
        except ForeignSchemaValidationError as error:
            raise SchemaValidationError(str(error)) from error
        except ForeignUnsupportedVersionError as error:
            raise UnsupportedVersionError(str(error)) from error

    return guarded


require_identifier = _owns_the_refusal(foreign_require_identifier)
require_text = _owns_the_refusal(foreign_require_text)
require_unique = _owns_the_refusal(foreign_require_unique)
require_supported_version = _owns_the_refusal(foreign_require_supported_version)


def require_digest(value: Any, field: str) -> str:
    digest = require_text(value, field, maximum=64).lower()
    if SHA256_PATTERN.fullmatch(digest) is None:
        raise SchemaValidationError(f"{field} must be 64 lowercase hexadecimal digits, got {value!r}")
    return digest


def require_millis(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchemaValidationError(
            f"{field} must be an integer millisecond timestamp, got {type(value).__name__}"
        )
    if not MIN_MILLIS <= value <= MAX_MILLIS:
        raise SchemaValidationError(
            f"{field} must be within [{MIN_MILLIS}, {MAX_MILLIS}] milliseconds, got {value}"
        )
    return value


def require_version_text(value: Any, field: str) -> str:
    return require_text(value, field, maximum=MAX_VERSION_TEXT)


def require_scalar(value: Any, field: str) -> Any:
    """Extension metadata may carry scalars only, never nested records or callables."""

    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return require_text(value, field, maximum=MAX_METADATA_VALUE_TEXT)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if not value:
            raise SchemaValidationError(f"{field} must not be an empty sequence")
        items = [require_scalar(item, f"{field}[]") for item in value]
        if any(not isinstance(item, type(items[0])) for item in items):
            raise SchemaValidationError(f"{field} must be a homogeneous sequence")
        if isinstance(items[0], str):
            return tuple(require_text(item, f"{field}[]", maximum=MAX_METADATA_VALUE_TEXT) for item in items)
        return tuple(items)
    raise SchemaValidationError(
        f"{field} must be a scalar or a homogeneous sequence of scalars, got {type(value).__name__}"
    )


def require_metadata(value: Any, field: str, *, maximum_keys: int) -> tuple[tuple[str, Any], ...]:
    """Freeze untrusted metadata into sorted pairs bounded in both width and depth.

    Already-frozen input is accepted so ``dataclasses.replace`` revalidates through
    this one path instead of a second, looser one.
    """

    if value is None:
        return ()
    if (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and all(isinstance(item, (tuple, list)) and len(item) == 2 for item in value)
    ):
        value = dict(value)
    if not isinstance(value, Mapping):
        raise SchemaValidationError(f"{field} must be a mapping of scalar values")
    if len(value) > maximum_keys:
        raise SchemaValidationError(
            f"{field} carries {len(value)} keys which exceeds the admitted maximum {maximum_keys}"
        )
    frozen: dict[str, Any] = {}
    for key, item in value.items():
        name = require_identifier(key, f"{field}.key")
        if name in frozen:
            raise SchemaValidationError(f"{field} declares {name!r} more than once")
        frozen[name] = require_scalar(item, f"{field}.{name}")
    return tuple(sorted(frozen.items()))


def require_bounded(values: Any, field: str, *, maximum: int, kind: str = "entry") -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise SchemaValidationError(
            f"{field} must be a sequence of {kind} values, got {type(values).__name__}"
        )
    items = tuple(values)
    if len(items) > maximum:
        raise SchemaValidationError(
            f"{field} carries {len(items)} {kind} values which exceeds the admitted maximum {maximum}"
        )
    return items


def require_reference(value: Any, field: str) -> str:
    """An opaque reference into a store: identifier grammar, longer allowance."""

    return require_text(value, field, maximum=512)


def require_optional_text(value: Any, field: str, *, maximum: int = 512) -> str | None:
    """Free text that may be absent. M01 refuses empty strings, so absence is ``None``."""

    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return require_text(value, field, maximum=maximum)


def require_quality_class(value: Any, field: str = "quality_class") -> QualityClass:
    """Read one rung of M01's ladder, reporting a refusal through M02's error type.

    M01 owns the ranking and M02 must never re-score it, but a caller catching
    ``iris_project_os.errors`` should not have to also catch M01's exception
    hierarchy just because a string arrived over a boundary.
    """

    try:
        return QualityClass.parse(value)
    except ForeignSchemaValidationError as error:
        raise SchemaValidationError(str(error)) from error


def require_component_version(value: Any, field: str = "actor") -> ComponentVersion:
    """Accept a ComponentVersion or its payload, the same rule ``Record.coerce`` uses.

    M01 owns this type, so M02 cannot add a ``coerce`` to it; without one every
    caller would re-implement the isinstance check slightly differently.
    """

    if isinstance(value, ComponentVersion):
        return value
    if isinstance(value, Mapping):
        try:
            return ComponentVersion.from_payload(value)
        except ForeignSchemaValidationError as error:
            raise SchemaValidationError(str(error)) from error
    raise SchemaValidationError(
        f"{field} must be a ComponentVersion or its payload, got {type(value).__name__}"
    )
