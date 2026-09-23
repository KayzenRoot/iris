"""Strict immutable records and explicit nested-payload decoders."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from types import MappingProxyType
from fractions import Fraction
from typing import Any, Callable, ClassVar, Mapping

from .errors import IRSchemaError
from .versions import canonical_value, content_digest

__all__ = ["IRRecord", "one", "many", "optional", "fraction", "encode_payload"]

Decoder = Callable[[Any, str], Any]


def encode_payload(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    return canonical_value(value)


def immutable_mapping(value: Mapping[str, Any], field: str = "mapping") -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise IRSchemaError(f"{field} must be a string-keyed object")
    return MappingProxyType({key: value[key] for key in sorted(value)})


def one(kind: Any) -> Decoder:
    def decode(value: Any, path: str) -> Any:
        if isinstance(value, kind):
            return value
        if isinstance(value, Mapping):
            return kind.from_payload(value)
        raise IRSchemaError(f"{path} must be a {kind.__name__} or its payload")

    return decode


def optional(kind: Any) -> Decoder:
    decode_one = one(kind)

    def decode(value: Any, path: str) -> Any:
        return None if value is None else decode_one(value, path)

    return decode


def many(kind: Any) -> Decoder:
    decode_one = one(kind)

    def decode(value: Any, path: str) -> tuple[Any, ...]:
        if not isinstance(value, (tuple, list)):
            raise IRSchemaError(f"{path} must be a sequence")
        return tuple(decode_one(item, f"{path}[]") for item in value)

    return decode


def fraction(value: Any, path: str) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return Fraction(value, 1)
    if isinstance(value, Mapping) and set(value) == {"numerator", "denominator"}:
        numerator, denominator = value["numerator"], value["denominator"]
        if isinstance(numerator, int) and not isinstance(numerator, bool) and isinstance(denominator, int) and not isinstance(denominator, bool) and denominator != 0:
            return Fraction(numerator, denominator)
    raise IRSchemaError(f"{path} must be an exact rational")


class IRRecord:
    NESTED: ClassVar[Mapping[str, Decoder]] = {}

    def to_payload(self) -> dict[str, Any]:
        if not is_dataclass(self):
            raise TypeError(f"{type(self).__name__} must be a dataclass")
        return {item.name: encode_payload(getattr(self, item.name)) for item in fields(self)}

    @classmethod
    def from_payload(cls, payload: Any) -> Any:
        if not is_dataclass(cls) or not isinstance(payload, Mapping):
            raise IRSchemaError(f"{cls.__name__} must be decoded from an object")
        expected = {item.name for item in fields(cls)}
        unknown = set(payload) - expected
        missing = expected - set(payload)
        if unknown or missing:
            raise IRSchemaError(
                f"{cls.__name__} keys differ: unknown={sorted(unknown)}, missing={sorted(missing)}"
            )
        values = {
            item.name: cls.NESTED[item.name](payload[item.name], f"{cls.__name__}.{item.name}")
            if item.name in cls.NESTED
            else payload[item.name]
            for item in fields(cls)
        }
        return cls(**values)

    @classmethod
    def coerce(cls, value: Any, field: str = "value") -> Any:
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            return cls.from_payload(value)
        raise IRSchemaError(f"{field} must be a {cls.__name__} or payload")

    def canonical_digest(self) -> str:
        return content_digest(self.to_payload())
