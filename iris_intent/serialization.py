"""The one place M03 states what a payload *is* before anything reads what it means.

A record's own ``to_payload`` is total and strict, but it is not self-describing: a bare mapping of
``constraint_id`` and ``strength`` says nothing about which schema it follows or which contract
admitted it, and a reader that guessed would be decoding bytes with a meaning it invented. So every
M03 record leaves the kernel inside a :class:`SerializationEnvelope` naming the schema version, the
record kind and the contract version, and carrying a digest the reader checks before it decodes.

The kind map is *derived*, not written out. This module walks its own package, collects every
``Record`` subclass each submodule defines, and refuses to build the map if two of them share a name.
A hand-maintained list would quietly forget the next record type someone adds, and the failure mode of
a forgotten type is the worst one available here: an unidentifiable payload is not rejected loudly, it
is rejected as unknown, and the caller loses a document the kernel could perfectly well have read.

The map is built once and frozen in a read-only proxy. That is not the mutable global authority the
Work Order forbids — no code path adds to it, nothing reads from it that a caller can influence, and if
two records genuinely share a name the refusal happens when the map is built rather than as a coin flip
about which one a wire kind means.

Validation happens on the way *in* as well as the way out: an envelope cannot be constructed around a
payload its own kind would reject. The alternative — hold the envelope, fail when somebody finally
decodes it — lets a truncated or forged document circulate through stores, digests and evidence bundles
looking valid, which is exactly the shape of bug a transport layer is supposed to end.

``dumps`` uses the same canonicalisation :func:`iris_intent.versions.content_digest` hashes, so the
bytes a document travels as and the digest it is quoted by are two readings of one definition rather
than two definitions that happen to agree today.
"""

from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from .base import Record
from .errors import IntentKernelError, SchemaValidationError
from .versions import (
    CONTRACT_VERSION,
    SCHEMA_VERSION,
    canonical_json,
    content_digest,
    require_contract_version,
    require_digest,
    require_schema_version,
)

__all__ = [
    "SerializationEnvelope",
    "record_types",
    "record_kinds",
    "record_kind",
    "require_record_kind",
    "envelope_for",
    "from_envelope",
    "serialize",
    "deserialize",
    "dumps",
    "loads",
]

_PACKAGE_NAME = __name__.rsplit(".", 1)[0]


def _build_kind_map() -> Mapping[str, type[Record]]:
    """Every record M03 defines, keyed by the class name that identifies it on the wire.

    Membership is decided by where a class is *defined*, so a module that re-exports its neighbour's
    record type contributes one entry rather than two competing ones.
    """

    package = importlib.import_module(_PACKAGE_NAME)
    found: dict[str, type[Record]] = {}
    origins: dict[str, str] = {}
    for info in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{_PACKAGE_NAME}.{info.name}")
        for name, member in inspect.getmembers(module, inspect.isclass):
            if not issubclass(member, Record) or member is Record or member.__module__ != module.__name__:
                continue
            clash = found.get(name)
            if clash is not None and clash is not member:
                raise SchemaValidationError(
                    f"record kind {name} is defined by both {origins[name]} and {module.__name__}; a wire "
                    "kind that means two things cannot be decoded, so one of them has to be renamed"
                )
            found[name] = member
            origins[name] = module.__name__
    if not found:
        raise SchemaValidationError(
            f"{_PACKAGE_NAME} defines no records, which cannot be true while this kernel compiles; a scan "
            "that found nothing is a scan nobody should trust"
        )
    return MappingProxyType(dict(found))


_RECORD_TYPES: Mapping[str, type[Record]] | None = None


def _kind_map() -> Mapping[str, type[Record]]:
    """The scan, memoised.

    Built on first use rather than at import because this module's own envelope is one of the records
    being catalogued: a scan that ran while the file was still executing would silently leave it out.
    The cached value is a read-only proxy over a dict nobody holds a reference to, so the memo cannot
    drift — it is the same map the kernel started with or the process is in a state no record survives.
    """

    global _RECORD_TYPES
    if _RECORD_TYPES is None:
        _RECORD_TYPES = _build_kind_map()
    return _RECORD_TYPES


def record_types() -> Mapping[str, type[Record]]:
    """The derived kind map, read-only: every record this kernel can put on a wire."""

    return _kind_map()


def record_kinds() -> tuple[str, ...]:
    return tuple(sorted(_kind_map()))


def require_record_kind(value: Any, field: str = "kind") -> str:
    """A wire kind is a known record name or the payload is refused by name.

    The refusal counts the accepted set and points at :func:`record_kinds` instead of pasting 110 names
    into an error line, because the useful distinction is between a misspelling and a kind from a
    kernel this one has never heard of.
    """

    name = value if isinstance(value, str) else type(value).__name__
    if name not in _kind_map():
        raise SchemaValidationError(
            f"{field} {name!r} is not an M03 record kind; this kernel transports {len(_kind_map())} "
            "kinds, listed by record_kinds(), and a kind from a newer kernel must arrive through a "
            "migration receipt rather than by being guessed at"
        )
    return name


def record_kind(value: Any) -> str:
    """Which kind a record is, read from its own type rather than from a caller's label."""

    kind = type(value).__name__
    if _kind_map().get(kind) is not type(value):
        raise SchemaValidationError(
            f"{kind} is not a record this kernel defines, so it has no transport kind; emitting it would "
            "produce a document whose reader cannot name what it holds"
        )
    return kind


@dataclass(frozen=True)
class SerializationEnvelope(Record):
    """A record plus the three facts a reader needs before trusting it: version, kind, digest.

    ``payload_digest`` is the digest of ``payload`` and therefore also the digest of the record the
    payload came from, which is what lets an audit quote one number for a document and its bytes.
    """

    schema_version: str
    kind: str
    contract_version: str
    payload: Mapping[str, Any]
    payload_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_version", require_schema_version(self.schema_version))
        object.__setattr__(self, "kind", require_record_kind(self.kind))
        object.__setattr__(self, "contract_version", require_contract_version(self.contract_version))
        if not isinstance(self.payload, Mapping):
            raise SchemaValidationError(
                f"payload must be a mapping of record fields, got {type(self.payload).__name__}; a "
                "sequence or scalar under this key is a document whose shape nobody declared"
            )
        digest = require_digest(self.payload_digest, "payload_digest")
        try:
            computed = content_digest(self.payload)
        except (TypeError, ValueError) as error:
            raise SchemaValidationError(
                f"payload of {self.kind} is not canonical data: {error}; a digest can only be checked "
                "over bytes this module can reproduce"
            ) from error
        if digest != computed:
            raise SchemaValidationError(
                f"payload_digest says {digest[:12]} but the payload hashes to {computed[:12]}; either the "
                "bytes changed in transit or the digest was written by something that never read them"
            )
        object.__setattr__(self, "payload", dict(self.payload))
        _decode(self.kind, self.payload)

    @property
    def record_type(self) -> type[Record]:
        return _kind_map()[self.kind]

    def decode(self) -> Record:
        """The record this envelope carries, re-checked against the kind's own rules."""

        return _decode(self.kind, self.payload)


def _decode(kind: str, payload: Mapping[str, Any]) -> Record:
    record_type = _kind_map()[kind]
    try:
        return record_type.from_payload(payload)
    except IntentKernelError:
        raise
    except Exception as error:  # noqa: BLE001 - a nested record may be M01's or M02's, whose hierarchies are not M03's
        raise SchemaValidationError(
            f"{kind} could not be rebuilt from its payload: {error}; the envelope reached this kernel "
            "intact, so what failed is the schema behind it"
        ) from error


def envelope_for(value: Any) -> SerializationEnvelope:
    """Wrap a record in its envelope, deriving the digest from the bytes actually carried.

    A record that carries no ``contract_version`` of its own is stamped with this kernel's, which is
    the honest reading: the envelope is asserting what produced the document, and this kernel did.
    """

    kind = record_kind(value)
    payload = value.to_payload()
    return SerializationEnvelope(
        schema_version=SCHEMA_VERSION,
        kind=kind,
        contract_version=getattr(value, "contract_version", "") or CONTRACT_VERSION,
        payload=payload,
        payload_digest=content_digest(payload),
    )


def from_envelope(envelope: Any) -> Record:
    return SerializationEnvelope.coerce(envelope, "envelope").decode()


def serialize(value: Any) -> dict[str, Any]:
    """The envelope as a plain payload mapping, for callers that store dicts rather than objects."""

    return envelope_for(value).to_payload()


def deserialize(value: Any) -> Record:
    """Rebuild a record from an envelope instance or the mapping :func:`serialize` produced."""

    if isinstance(value, SerializationEnvelope):
        return value.decode()
    if isinstance(value, Record):
        raise SchemaValidationError(
            f"{type(value).__name__} is already a record; deserialize reads transport envelopes, and "
            "accepting both shapes in one call is how an unchecked document gets a second life"
        )
    return from_envelope(value)


def dumps(value: Any) -> str:
    """Canonical JSON for a record — the same bytes every time, wherever they were written from."""

    return canonical_json(serialize(value))


def loads(text: Any) -> Record:
    """Parse text into a record, refusing anything that is not an M03 envelope.

    A JSON scalar or list is rejected rather than coerced: the commonest cause is a caller handing over
    a payload file that was never an envelope, and "kind is not an M03 record kind" would send them
    looking for the wrong problem.
    """

    if not isinstance(text, str):
        raise SchemaValidationError(f"loads expects a string, got {type(text).__name__}")
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        raise SchemaValidationError(f"transport text is not JSON: {error}") from error
    if not isinstance(document, Mapping):
        raise SchemaValidationError(
            f"a serialised M03 document must be a JSON object, got {type(document).__name__}; envelopes "
            "carry named fields, so a list or scalar is a different document entirely"
        )
    return deserialize(document)
