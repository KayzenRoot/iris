"""Small validators shared by the provider-neutral semantic records."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Callable, Iterable, TypeVar

from .errors import IRSchemaError
from .versions import require_identifier, require_text

T = TypeVar("T")


def identifiers(values: Iterable[str], field: str, *, unique: bool = True) -> tuple[str, ...]:
    result = tuple(require_identifier(value, f"{field}[]") for value in values)
    if unique and len(result) != len(set(result)):
        raise IRSchemaError(f"{field} contains duplicate identifiers")
    return result


def records(values: Iterable[T], kind: type[T], field: str, *, unique_by: Callable[[T], Any] | None = None) -> tuple[T, ...]:
    if not isinstance(values, (tuple, list)):
        raise IRSchemaError(f"{field} must be a sequence")
    result = tuple(kind.coerce(item, f"{field}[]") for item in values)  # type: ignore[attr-defined]
    if unique_by is not None:
        keys = tuple(unique_by(item) for item in result)
        if len(keys) != len(set(keys)):
            raise IRSchemaError(f"{field} contains duplicate identities")
    return result


def text_set(values: Iterable[str], field: str) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list, set, frozenset)):
        raise IRSchemaError(f"{field} must be a sequence")
    return tuple(sorted({require_text(item, f"{field}[]", maximum=256) for item in values}))


def deep_freeze(value: Any, field: str = "value", *, depth: int = 0, max_depth: int = 64) -> Any:
    if depth > max_depth:
        raise IRSchemaError(f"{field} exceeds the maximum nesting depth")
    if isinstance(value, Mapping):
        return MappingProxyType({
            key: deep_freeze(value[key], f"{field}.{key}", depth=depth + 1, max_depth=max_depth)
            for key in sorted(value)
            if isinstance(key, str)
        }) if all(isinstance(key, str) for key in value) else _bad_mapping(field)
    if isinstance(value, (tuple, list)):
        return tuple(deep_freeze(item, f"{field}[]", depth=depth + 1, max_depth=max_depth) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(deep_freeze(item, f"{field}[]", depth=depth + 1, max_depth=max_depth) for item in value)
    return value


def _bad_mapping(field: str) -> Any:
    raise IRSchemaError(f"{field} requires string mapping keys")


def require_enum(value: Any, enum_type: type, field: str) -> Any:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (ValueError, TypeError):
        allowed = ", ".join(item.value for item in enum_type)
        raise IRSchemaError(f"{field} must be one of: {allowed}") from None


def non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise IRSchemaError(f"{field} must be a non-negative integer")
    return value


def positive_int(value: Any, field: str) -> int:
    result = non_negative_int(value, field)
    if result == 0:
        raise IRSchemaError(f"{field} must be a positive integer")
    return result
