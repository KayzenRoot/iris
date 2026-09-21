"""M02's versioned, tamper-evident transport envelope.

Every kernel record already serialises itself (``Record.to_payload``), so what is left is the one thing
a record cannot state about itself: which schema version this byte string claims, and whether it survived
the trip unchanged. The envelope answers both, and refuses anything else, because a store that accepts an
unlabelled payload is how a v1 reader ends up decoding a v2 record.

The type map is derived from the kernel rather than hand-maintained, and that is a deliberate contract
choice rather than a convenience. §12 of the module spec requires deterministic, schema-versioned
serialisation of the kernel's structures; a hand-written list of a hundred-odd records would silently
omit the next one, and an omitted record is not a serialisation failure at the call site — it is a record
that cannot be persisted, audited or replayed, discovered only by whoever needed it. So every frozen
``Record`` the package owns is transportable, and two records that would claim one transport name stop
the package from importing at all. Nothing here is mutable after import: the map is a frozen view, which
is the difference between this and the global semantic registries §11 forbids.
"""

from __future__ import annotations

import json
import re
from dataclasses import is_dataclass
from types import MappingProxyType
from typing import Any, Mapping

from . import (
    analysis,
    archive,
    base,
    branching,
    build,
    diffing,
    graph,
    identity,
    lifecycle,
    merge,
    ports,
    promotion,
    release,
    reuse,
    snapshots,
)
from .errors import SchemaValidationError, UnsupportedVersionError
from .versions import SCHEMA_VERSION, SUPPORTED_SCHEMA_VERSIONS, canonical_json, content_digest

__all__ = [
    "ENVELOPE_KEYS",
    "SERIALIZABLE_TYPES",
    "dumps",
    "envelope",
    "from_envelope",
    "loads",
    "type_name",
    "validate_payload",
]

ENVELOPE_KEYS = frozenset({"schema_version", "type", "payload", "payload_sha256"})

_KERNEL_MODULES = (
    analysis,
    archive,
    branching,
    build,
    diffing,
    graph,
    identity,
    lifecycle,
    merge,
    ports,
    promotion,
    release,
    reuse,
    snapshots,
)

_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def transport_name(cls: type) -> str:
    """The stable wire name of a kernel type: its class name in snake_case.

    Derived from the class, never from its module, so moving a record between files cannot silently
    change what stored envelopes say it is.
    """

    return _BOUNDARY.sub("_", cls.__name__).lower()


def _serializable_types() -> Mapping[str, type]:
    """Every frozen record the kernel owns, keyed by transport name, refusing a name clash.

    Only classes defined *in* the module are claimed by it, so a record merely re-imported for use does
    not get registered twice — and a genuine clash means two records want one wire name, which no
    runtime check can resolve after envelopes are already in a store.
    """

    found: dict[str, type] = {}
    for module in _KERNEL_MODULES:
        for name, value in vars(module).items():
            if name.startswith("_") or not is_dataclass(value) or not isinstance(value, type):
                continue
            if not issubclass(value, base.Record):
                continue
            if value.__module__ != module.__name__:
                continue
            key = transport_name(value)
            clash = found.get(key)
            if clash is not None and clash is not value:
                raise SchemaValidationError(
                    f"{value.__qualname__} and {clash.__qualname__} both serialise as {key!r}; give one of "
                    "them a different name before this envelope can mean anything"
                )
            found[key] = value
    return MappingProxyType(dict(sorted(found.items())))


SERIALIZABLE_TYPES: Mapping[str, type] = _serializable_types()

_TYPE_NAMES: Mapping[type, str] = MappingProxyType(
    {cls: name for name, cls in SERIALIZABLE_TYPES.items()}
)


def type_name(value: Any) -> str:
    name = _TYPE_NAMES.get(type(value))
    if name is None:
        raise SchemaValidationError(
            f"{type(value).__name__} is not a serializable kernel type; it is either not a Record the "
            "kernel owns or it is one of the enumeration and error types that never cross the wire"
        )
    return name


def envelope(value: Any) -> dict[str, Any]:
    """Wrap a kernel object in its versioned, tamper-evident transport record."""

    name = type_name(value)
    payload = value.to_payload()
    return {
        "schema_version": SCHEMA_VERSION,
        "type": name,
        "payload": payload,
        "payload_sha256": content_digest(payload),
    }


def from_envelope(record: Mapping[str, Any]) -> Any:
    """Read one envelope back, failing closed on an unknown version, type or altered payload."""

    if not isinstance(record, Mapping):
        raise SchemaValidationError("an envelope must be a mapping")
    unexpected = set(record) - set(ENVELOPE_KEYS)
    if unexpected:
        raise SchemaValidationError(f"envelope has unknown keys: {sorted(unexpected)}")
    missing = set(ENVELOPE_KEYS) - set(record)
    if missing:
        raise SchemaValidationError(f"envelope is missing keys: {sorted(missing)}")
    version = record["schema_version"]
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise UnsupportedVersionError(
            f"unsupported schema_version {version!r}; this kernel reads {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )
    name = record["type"]
    handler = SERIALIZABLE_TYPES.get(name)
    if handler is None:
        raise SchemaValidationError(
            f"unknown envelope type {name!r}; the kernel does not know how to read it, and guessing from "
            "a similar payload shape would invent history"
        )
    payload = record["payload"]
    if not isinstance(payload, Mapping):
        raise SchemaValidationError("envelope payload must be a mapping")
    if content_digest(payload) != record["payload_sha256"]:
        raise SchemaValidationError(
            "envelope payload does not match payload_sha256; the record was altered in transit"
        )
    return handler.from_payload(payload)


def validate_payload(name: str, payload: Mapping[str, Any]) -> Any:
    """Rebuild then re-emit, so a payload is only valid when it round-trips unchanged.

    A record that decodes but re-serialises differently was carrying something the canonical form cannot
    hold — an unsorted collection, a default the writer skipped — and storing it would mean two readers
    getting two digests for one row.
    """

    handler = SERIALIZABLE_TYPES.get(name)
    if handler is None:
        raise SchemaValidationError(f"unknown kernel type {name!r}")
    value = handler.from_payload(payload)
    if value.to_payload() != json.loads(canonical_json(payload)):
        raise SchemaValidationError(
            f"{name} payload is not canonical: it changed shape when re-serialised"
        )
    return value


def dumps(value: Any, *, indent: int | None = None) -> str:
    return json.dumps(envelope(value), ensure_ascii=False, sort_keys=True, indent=indent)


def loads(text: str) -> Any:
    if not isinstance(text, str):
        raise SchemaValidationError("loads expects JSON text")
    try:
        record = json.loads(text)
    except json.JSONDecodeError as error:
        raise SchemaValidationError(f"kernel payload is not valid JSON: {error.msg}") from error
    return from_envelope(record)
