"""Closed immutable values shared by the M09 resource-state kernel."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any

from .limits import DEFAULT_LIMITS, M09Limits

__all__ = [
    "Confidence", "ResourceTier", "EvidenceOrigin", "ProvenanceRef", "ResourceIdentity",
    "CapacityTruth", "ResourceSnapshot", "ResourceEvent", "EventVerificationStatus", "StalenessPolicy", "FreshnessRequirement", "canonical_json",
    "content_digest", "require_id", "require_text", "require_nonnegative", "MutationActorKind", "MutationContext",
]


class Confidence(str, Enum):
    OBSERVED = "OBSERVED"
    ESTIMATED = "ESTIMATED"
    STALE = "STALE"
    CONFLICTED = "CONFLICTED"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"
    QUARANTINED = "QUARANTINED"


class ResourceTier(str, Enum):
    VRAM = "VRAM"
    RAM = "RAM"
    SPILL = "SPILL"
    EXTERNAL = "EXTERNAL"


class EvidenceOrigin(str, Enum):
    REPORTED_OBSERVATION = "REPORTED_OBSERVATION"
    DERIVED_ESTIMATE = "DERIVED_ESTIMATE"
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"


class EventVerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    REFERENCED = "REFERENCED"
    VERIFIED = "VERIFIED"
    SYNTHETIC = "SYNTHETIC"


class MutationActorKind(str, Enum):
    INTERACTIVE = "INTERACTIVE"
    AUTOMATION = "AUTOMATION"
    SERVICE = "SERVICE"


def require_id(value: str, field: str) -> str:
    if type(value) is not str or len(value) > 256 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/@+-]*", value):
        raise ValueError(f"{field} must be a bounded stable identifier")
    return value


def require_text(value: str, field: str, *, maximum: int = 4_096) -> str:
    if type(value) is not str:
        raise ValueError(f"{field} must be text")
    value = unicodedata.normalize("NFC", value)
    if not value or len(value) > maximum or any(unicodedata.category(char) in {"Cc", "Cf"} for char in value):
        raise ValueError(f"{field} must be non-empty bounded printable text")
    return value


def require_nonnegative(value: int | None, field: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value < 0 or value > (1 << 63) - 1:
        raise ValueError(f"{field} must be an unsigned 63-bit byte count or unknown")
    return value


@dataclass(frozen=True)
class MutationContext:
    """Attribution and replay identity for a state-changing request."""

    actor_kind: MutationActorKind
    actor_ref: str
    authorization_ref: str
    causal_request_ref: str
    idempotency_key: str
    automation_origin_ref: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.actor_kind, MutationActorKind):
            raise ValueError("mutation actor kind must be explicit")
        for field in ("actor_ref", "authorization_ref", "causal_request_ref", "idempotency_key"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if self.actor_kind is MutationActorKind.AUTOMATION:
            if self.automation_origin_ref is None:
                raise ValueError("automated mutation requires an explicit automation origin")
            object.__setattr__(self, "automation_origin_ref", require_id(self.automation_origin_ref, "automation_origin_ref"))
        elif self.automation_origin_ref is not None:
            object.__setattr__(self, "automation_origin_ref", require_id(self.automation_origin_ref, "automation_origin_ref"))


def _canonical(value: Any, *, depth: int, limits: M09Limits) -> Any:
    if depth > limits.max_json_depth:
        raise ValueError("canonical value exceeds maximum nesting depth")
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("non-finite numbers are not canonical")
        return value
    if isinstance(value, Enum):
        return value.value
    if type(value) is str:
        text = unicodedata.normalize("NFC", value)
        if len(text) > limits.max_text_chars or any(unicodedata.category(char) in {"Cc", "Cf"} for char in text):
            raise ValueError("canonical text is oversized or contains control characters")
        return text
    if type(value) in (dict, MappingProxyType):
        limits.require("max_json_items", len(value))
        result: dict[str, Any] = {}
        for key in sorted(value):
            if type(key) is not str or key in {"$type", "$enum"}:
                raise ValueError("canonical mappings require ordinary string keys")
            normalized = unicodedata.normalize("NFC", key)
            if not normalized or normalized in result:
                raise ValueError("canonical mapping keys are empty or collide after normalization")
            result[normalized] = _canonical(value[key], depth=depth + 1, limits=limits)
        return result
    if type(value) in (tuple, list):
        limits.require("max_json_items", len(value))
        return [_canonical(item, depth=depth + 1, limits=limits) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _canonical(getattr(value, item.name), depth=depth + 1, limits=limits)
            for item in fields(value)
            if item.init
        }
    raise ValueError(f"unsupported canonical value type {type(value).__name__}")


def canonical_json(value: Any, *, limits: M09Limits = DEFAULT_LIMITS) -> str:
    return json.dumps(_canonical(value, depth=0, limits=limits), ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def content_digest(value: Any, *, limits: M09Limits = DEFAULT_LIMITS) -> str:
    payload = canonical_json(value, limits=limits).encode("utf-8")
    limits.require("max_payload_bytes", len(payload))
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class ProvenanceRef:
    source: str
    reference: str
    observed_at_ms: int
    verification: str = "UNVERIFIED"

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", require_id(self.source, "source"))
        object.__setattr__(self, "reference", require_id(self.reference, "reference"))
        require_nonnegative(self.observed_at_ms, "observed_at_ms")
        object.__setattr__(self, "verification", require_id(self.verification, "verification"))


@dataclass(frozen=True)
class ResourceIdentity:
    """Stable physical/tier identity; runtime context and label do not replace it."""

    physical_id: str
    tier: ResourceTier
    runtime_context_id: str
    display_name: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "physical_id", require_id(self.physical_id, "physical_id"))
        object.__setattr__(self, "runtime_context_id", require_id(self.runtime_context_id, "runtime_context_id"))
        if not isinstance(self.tier, ResourceTier):
            raise ValueError("tier must be a ResourceTier")
        if self.display_name:
            object.__setattr__(self, "display_name", require_text(self.display_name, "display_name", maximum=256))

    @property
    def stable_key(self) -> str:
        return content_digest({"physical_id": self.physical_id, "tier": self.tier.value})


@dataclass(frozen=True)
class CapacityTruth:
    """Distinct byte measures; ``None`` means unknown and is never treated as zero."""

    physical_bytes: int | None
    reported_bytes: int | None
    allocatable_bytes: int | None
    reserved_bytes: int | None
    committed_bytes: int | None
    resident_bytes: int | None
    reclaimable_bytes: int | None
    external_bytes: int | None
    unknown_bytes: int | None
    operator_headroom_bytes: int | None

    def __post_init__(self) -> None:
        for item in fields(self):
            require_nonnegative(getattr(self, item.name), item.name)
        if self.physical_bytes is not None and self.operator_headroom_bytes is not None:
            if self.operator_headroom_bytes > self.physical_bytes:
                raise ValueError("operator headroom cannot exceed physical capacity")
        if self.allocatable_bytes is not None and self.physical_bytes is not None:
            if self.allocatable_bytes > self.physical_bytes - (self.operator_headroom_bytes or 0):
                raise ValueError("allocatable capacity violates physical headroom covenant")
        if self.resident_bytes is not None and self.committed_bytes is not None:
            if self.resident_bytes > self.committed_bytes:
                raise ValueError("resident bytes are a subset of commitments")

    def available_bytes(self) -> int:
        required = (
            self.allocatable_bytes, self.committed_bytes, self.reserved_bytes,
            self.external_bytes, self.unknown_bytes, self.operator_headroom_bytes,
            self.physical_bytes,
        )
        if any(value is None for value in required):
            raise ValueError("unknown capacity cannot authorize a commitment")
        assert self.allocatable_bytes is not None
        assert self.committed_bytes is not None
        assert self.reserved_bytes is not None
        assert self.external_bytes is not None
        assert self.unknown_bytes is not None
        # Reservations and commitments overlap by definition; count their union conservatively.
        occupied = max(self.committed_bytes, self.reserved_bytes) + self.external_bytes + self.unknown_bytes
        return max(0, self.allocatable_bytes - occupied)


@dataclass(frozen=True)
class ResourceSnapshot:
    snapshot_id: str
    schema_version: str
    identity: ResourceIdentity
    observed_at_ms: int
    expires_at_ms: int
    confidence: Confidence
    capacity: CapacityTruth
    provenance: tuple[ProvenanceRef, ...]
    m07_discovery_ref: str | None = None
    m08_evidence_ref: str | None = None
    evidence_origin: EvidenceOrigin = EvidenceOrigin.REPORTED_OBSERVATION
    materiality_ref: str | None = None
    digest: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_id", require_id(self.snapshot_id, "snapshot_id"))
        object.__setattr__(self, "schema_version", require_id(self.schema_version, "schema_version"))
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise ValueError("observed_at_ms must be a non-negative integer")
        if type(self.expires_at_ms) is not int or self.expires_at_ms < self.observed_at_ms:
            raise ValueError("snapshot expiry must not precede observation")
        if not isinstance(self.identity, ResourceIdentity) or not isinstance(self.capacity, CapacityTruth):
            raise ValueError("snapshot identity and capacity must be exact M09 records")
        if not isinstance(self.confidence, Confidence):
            raise ValueError("confidence must be a Confidence value")
        if not isinstance(self.evidence_origin, EvidenceOrigin):
            raise ValueError("evidence origin must explicitly distinguish reported, derived and synthetic state")
        provenance = tuple(self.provenance)
        if not provenance or any(type(item) is not ProvenanceRef for item in provenance):
            raise ValueError("snapshot requires explicit provenance references")
        if len({(item.source, item.reference) for item in provenance}) != len(provenance):
            raise ValueError("snapshot provenance references must be unique")
        object.__setattr__(self, "provenance", tuple(sorted(provenance, key=lambda item: (item.source, item.reference))))
        for field in ("m07_discovery_ref", "m08_evidence_ref", "materiality_ref"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_id(value, field))
        expected = content_digest(self.semantic_payload())
        if self.digest and self.digest != expected:
            raise ValueError("snapshot digest does not match canonical semantic content")
        object.__setattr__(self, "digest", expected)

    def semantic_payload(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "schema_version": self.schema_version,
            "identity": self.identity,
            "observed_at_ms": self.observed_at_ms,
            "expires_at_ms": self.expires_at_ms,
            "confidence": self.confidence,
            "capacity": self.capacity,
            "provenance": self.provenance,
            "m07_discovery_ref": self.m07_discovery_ref,
            "m08_evidence_ref": self.m08_evidence_ref,
            "evidence_origin": self.evidence_origin,
            "materiality_ref": self.materiality_ref,
        }

    def is_fresh(self, now_ms: int) -> bool:
        return type(now_ms) is int and self.observed_at_ms <= now_ms <= self.expires_at_ms and self.confidence is Confidence.OBSERVED

    def admits_commitment(self, now_ms: int, required_bytes: int) -> bool:
        if type(required_bytes) is not int or required_bytes < 0 or not self.is_fresh(now_ms):
            return False
        try:
            return self.capacity.available_bytes() >= required_bytes
        except ValueError:
            return False

    def production_transfer_authorized(self, now_ms: int) -> bool:
        return self.evidence_origin is EvidenceOrigin.REPORTED_OBSERVATION and self.is_fresh(now_ms)


@dataclass(frozen=True)
class ResourceEvent:
    event_id: str
    resource_key: str
    kind: str
    at_ms: int
    predecessor_ids: tuple[str, ...]
    provenance: tuple[ProvenanceRef, ...]
    details_digest: str
    actor_authorization_ref: str
    schema_version: str = "1.0.0"
    state_epoch: int = 1
    verification_status: EventVerificationStatus = EventVerificationStatus.UNVERIFIED
    mutation_context: MutationContext | None = None

    def __post_init__(self) -> None:
        for field in ("event_id", "resource_key", "kind", "actor_authorization_ref", "schema_version"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.details_digest) is not str or len(self.details_digest) != 64 or any(char not in "0123456789abcdef" for char in self.details_digest):
            raise ValueError("event details must be bound by a lowercase SHA-256 digest")
        if type(self.at_ms) is not int or self.at_ms < 0:
            raise ValueError("at_ms must be a non-negative integer")
        if type(self.state_epoch) is not int or self.state_epoch < 1 or not isinstance(self.verification_status, EventVerificationStatus):
            raise ValueError("event epoch and verification status must be explicit")
        predecessors = tuple(sorted(require_id(item, "predecessor_id") for item in self.predecessor_ids))
        provenance = tuple(self.provenance)
        if len(predecessors) > 2_048 or len(set(predecessors)) != len(predecessors):
            raise ValueError("event predecessors must be unique and bounded")
        if not provenance or len(provenance) > 2_048 or any(type(item) is not ProvenanceRef for item in provenance):
            raise ValueError("events require bounded typed provenance references")
        if len({(item.source, item.reference) for item in provenance}) != len(provenance):
            raise ValueError("event provenance references must be unique")
        context = self.mutation_context
        if context is None:
            context = MutationContext(MutationActorKind.INTERACTIVE, "M09:resource-twin-client", self.actor_authorization_ref, self.event_id, self.event_id)
            object.__setattr__(self, "mutation_context", context)
        if type(context) is not MutationContext or context.authorization_ref != self.actor_authorization_ref:
            raise ValueError("resource event requires mutation attribution matching its authorization")
        object.__setattr__(self, "predecessor_ids", predecessors)
        object.__setattr__(self, "provenance", tuple(sorted(provenance, key=lambda item: (item.source, item.reference))))


@dataclass(frozen=True)
class StalenessPolicy:
    policy_id: str
    version: str
    fresh_window_ms: int
    maximum_source_skew_ms: int
    purpose_max_age_ms: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "policy_id", require_id(self.policy_id, "policy_id"))
        object.__setattr__(self, "version", require_id(self.version, "version"))
        if any(type(value) is not int or value < 0 for value in (self.fresh_window_ms, self.maximum_source_skew_ms)):
            raise ValueError("staleness windows must be non-negative")
        purposes = tuple(sorted((require_id(name, "purpose"), age) for name, age in self.purpose_max_age_ms))
        if len({name for name, _ in purposes}) != len(purposes) or any(type(age) is not int or age < 0 for _, age in purposes):
            raise ValueError("purpose freshness policy must have unique non-negative windows")
        object.__setattr__(self, "purpose_max_age_ms", purposes)


@dataclass(frozen=True)
class FreshnessRequirement:
    purpose: str
    maximum_age_ms: int
    require_reported_observation: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "purpose", require_id(self.purpose, "purpose"))
        if type(self.maximum_age_ms) is not int or self.maximum_age_ms < 0 or type(self.require_reported_observation) is not bool:
            raise ValueError("freshness requirement must be explicit and bounded")

    def accepts(self, snapshot: ResourceSnapshot, *, now_ms: int) -> bool:
        if type(snapshot) is not ResourceSnapshot or type(now_ms) is not int or now_ms < snapshot.observed_at_ms:
            return False
        if now_ms - snapshot.observed_at_ms > self.maximum_age_ms or now_ms > snapshot.expires_at_ms:
            return False
        if self.require_reported_observation and snapshot.evidence_origin is not EvidenceOrigin.REPORTED_OBSERVATION:
            return False
        return snapshot.confidence is Confidence.OBSERVED
