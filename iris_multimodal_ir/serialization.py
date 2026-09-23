"""Canonical byte serialization with strict transport parsing and duplicate-key rejection."""

from __future__ import annotations

import json
from typing import Any

from .errors import IRLimitError, IRSchemaError
from .graph import IRDocumentEnvelope
from .limits import DEFAULT_LIMITS, IRLimits
from .versions import TRANSPORT_VERSION, canonical_json, content_digest

__all__ = ["canonical_bytes", "serialize_envelope", "deserialize_envelope", "canonical_digest"]


def canonical_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return content_digest(value)


def serialize_envelope(envelope: IRDocumentEnvelope) -> bytes:
    envelope = IRDocumentEnvelope.coerce(envelope, "envelope")
    if envelope.transport_version != TRANSPORT_VERSION:
        raise IRSchemaError(f"unsupported transport version {envelope.transport_version}")
    return canonical_bytes(envelope.to_payload())


def deserialize_envelope(data: bytes | bytearray | str, *, limits: IRLimits = DEFAULT_LIMITS) -> IRDocumentEnvelope:
    if isinstance(data, str):
        try:
            raw = data.encode("utf-8")
        except UnicodeEncodeError as error:
            raise IRSchemaError(f"transport input is not valid UTF-8: {error}") from error
    elif isinstance(data, (bytes, bytearray)):
        raw = bytes(data)
    else:
        raise IRSchemaError("transport input must be UTF-8 bytes or text")
    if len(raw) > limits.max_inline_payload_bytes:
        raise IRLimitError("canonical transport payload exceeds max_inline_payload_bytes")
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except IRSchemaError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IRSchemaError(f"invalid canonical JSON transport: {error}") from error
    if not isinstance(value, dict):
        raise IRSchemaError("canonical envelope JSON root must be an object")
    try:
        envelope = IRDocumentEnvelope.from_payload(value)
    except IRSchemaError:
        raise
    except Exception as error:
        from .errors import IRKernelError
        if isinstance(error, IRKernelError):
            raise
        raise IRSchemaError(f"canonical envelope payload is invalid: {error}") from error
    if envelope.transport_version != TRANSPORT_VERSION:
        raise IRSchemaError(f"unsupported transport version {envelope.transport_version}")
    # Re-encoding is part of admission: permissive spellings/number encodings are rejected.
    if serialize_envelope(envelope) != raw:
        raise IRSchemaError("transport bytes are valid JSON but not canonical M04 serialization")
    return envelope


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IRSchemaError(f"duplicate canonical JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise IRSchemaError(f"non-finite JSON numeric constant {value} is forbidden")
