"""Strict payload primitives shared by every M02 value object.

M02 is data-first: identity, graph, snapshot, build and lifecycle objects are
frozen value records that must serialise deterministically and rebuild exactly.
``Record`` gives that shape once (all keys required, unknown keys refused, nested
records decoded) so each type only declares its fields and its validation.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Sequence

from .errors import ProjectOSError, SchemaValidationError

__all__ = ["Labeled", "Record", "encode_payload", "of", "union", "decode_nested"]
class Labeled(Enum):
    """Enumeration whose value equals its name, parsed strictly and fail-closed."""

    @classmethod
    def members(cls) -> list[str]:
        return sorted(item.value for item in cls)

    @classmethod
    def describe(cls) -> str:
        return ", ".join(cls.members())

    @classmethod
    def parse(cls, value: Any, field: str | None = None) -> "Labeled":
        label = field or cls.__name__
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise SchemaValidationError(
                f"{label} must be one of [{cls.describe()}], got {value!r}"
            )
        try:
            return cls(value.strip().upper())
        except ValueError as error:
            raise SchemaValidationError(
                f"{label} must be one of [{cls.describe()}], got {value!r}"
            ) from error


def encode_payload(value: Any) -> Any:
    """Turn a kernel value into JSON-compatible data without losing ordering.

    Encoding is duck-typed on ``to_payload`` so an M01 record nested inside an M02
    record canonicalises exactly the way M01 writes it, instead of becoming an
    opaque Python repr.
    """

    encoder = getattr(value, "to_payload", None)
    if callable(encoder):
        return encoder()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): encode_payload(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [encode_payload(item) for item in value]
    return value


Converter = Callable[[Any, str], Any]


def of(kind: Any) -> Converter:
    """Decode one record, or a sequence of records, of ``kind`` from payload data."""

    def decoded(call: Callable[[], Any], path: str) -> Any:
        try:
            return call()
        except ProjectOSError:
            raise
        except Exception as error:  # noqa: BLE001 - a nested type may be M01's, whose hierarchy is not M02's
            raise SchemaValidationError(f"{path} could not be decoded: {error}") from error

    def convert(raw: Any, path: str) -> Any:
        if raw is None:
            return None
        if isinstance(raw, Mapping):
            return decoded(lambda: kind.from_payload(raw), path)
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            return tuple(decoded(lambda item=item: kind.coerce(item, path), f"{path}[]") for item in raw)
        return decoded(lambda: kind.coerce(raw, path), path)

    return convert


def union(*converters: Converter) -> Converter:
    """Try each converter in order, reporting every attempt when all fail."""

    def convert(raw: Any, path: str) -> Any:
        failures: list[str] = []
        for converter in converters:
            try:
                return converter(raw, path)
            except (SchemaValidationError, KeyError, TypeError) as error:
                failures.append(str(error))
        raise SchemaValidationError(
            f"{path} matches none of its admitted shapes: {'; '.join(failures)}"
        )

    return convert


def decode_nested(converters: Mapping[str, Converter], name: str, raw: Any, path: str) -> Any:
    converter = converters.get(name)
    if converter is None:
        return raw
    return converter(raw, f"{path}.{name}")


class Record:
    """Frozen dataclass with a strict, total ``to_payload`` / ``from_payload`` pair.

    ``NESTED`` names the fields holding other records; everything else is passed
    through untouched and normalised by the dataclass itself, so validation lives
    in exactly one place per type.
    """

    NESTED: Mapping[str, Converter] = {}

    def to_payload(self) -> dict[str, Any]:
        if not is_dataclass(self):
            raise TypeError(f"{type(self).__name__} must be a dataclass to be serialisable")
        return {item.name: encode_payload(getattr(self, item.name)) for item in fields(self)}

    @classmethod
    def from_payload(cls, payload: Any) -> Any:
        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a dataclass to be deserialisable")
        if not isinstance(payload, Mapping):
            raise SchemaValidationError(
                f"{cls.__name__} must be decoded from a mapping, got {type(payload).__name__}"
            )
        names = {item.name for item in fields(cls)}
        unknown = set(payload) - names
        if unknown:
            raise SchemaValidationError(f"{cls.__name__} has unknown keys: {sorted(unknown)}")
        missing = names - set(payload)
        if missing:
            raise SchemaValidationError(f"{cls.__name__} is missing keys: {sorted(missing)}")
        arguments = {
            name: decode_nested(cls.NESTED, name, payload[name], cls.__name__) for name in names
        }
        return cls(**arguments)

    @classmethod
    def coerce(cls, value: Any, field: str = "value") -> Any:
        """Accept an instance, a payload mapping, or nothing else.

        Callers build records from both code and stored data; coercion keeps one
        admission rule for both instead of a permissive path nobody audits.
        """

        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            return cls.from_payload(value)
        raise SchemaValidationError(
            f"{field} must be a {cls.__name__} or its payload, got {type(value).__name__}"
        )

    def digest(self) -> str:
        from .versions import content_digest

        return content_digest(self.to_payload())
