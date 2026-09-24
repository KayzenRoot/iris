"""Immutable snapshot fabric, append-only event journal and reconciliation quarantine."""

from __future__ import annotations

from dataclasses import dataclass, fields
from threading import RLock
from typing import Iterable

from .limits import DEFAULT_LIMITS, M09Limits
from .model import (
    CapacityTruth, Confidence, EventVerificationStatus, EvidenceOrigin, MutationActorKind, MutationContext, ResourceEvent, ResourceSnapshot,
    content_digest, require_id,
)

__all__ = [
    "ResourceTwin", "SnapshotReconciliation", "reconcile_snapshots",
    "QuarantineRecord",
]


@dataclass(frozen=True)
class QuarantineRecord:
    quarantine_id: str
    resource_key: str
    reason: str
    evidence_refs: tuple[str, ...]
    created_at_ms: int
    actor_authorization_ref: str
    mutation_context: MutationContext | None = None

    def __post_init__(self) -> None:
        for field in ("quarantine_id", "resource_key", "reason", "actor_authorization_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.created_at_ms) is not int or self.created_at_ms < 0:
            raise ValueError("created_at_ms must be non-negative")
        refs = tuple(sorted(set(require_id(item, "evidence_ref") for item in self.evidence_refs)))
        if not refs:
            raise ValueError("quarantine requires evidence references")
        context = self.mutation_context
        if context is None:
            context = MutationContext(MutationActorKind.INTERACTIVE, "M09:quarantine-client", self.actor_authorization_ref, self.quarantine_id, self.quarantine_id)
            object.__setattr__(self, "mutation_context", context)
        if type(context) is not MutationContext or context.authorization_ref != self.actor_authorization_ref:
            raise ValueError("quarantine requires mutation attribution matching its authorization")
        object.__setattr__(self, "evidence_refs", refs)


@dataclass(frozen=True)
class SnapshotReconciliation:
    snapshot: ResourceSnapshot
    source_skew_ms: int
    freshness_window_ms: int
    conflict_fields: tuple[str, ...]
    quarantined: bool
    evidence_digest: str


def reconcile_snapshots(
    snapshots: Iterable[ResourceSnapshot],
    *,
    snapshot_id: str,
    now_ms: int,
    freshness_window_ms: int,
    skew_tolerance_ms: int = 1_000,
    limits: M09Limits = DEFAULT_LIMITS,
) -> SnapshotReconciliation:
    """Reconcile references conservatively; conflicting history is never rewritten."""
    if type(limits) is not M09Limits:
        raise ValueError("reconciliation limits must use exact M09 bounds")
    collected: list[ResourceSnapshot] = []
    for candidate in snapshots:
        limits.require("max_resources", len(collected) + 1)
        collected.append(candidate)
    candidates = tuple(collected)
    if not candidates or any(type(item) is not ResourceSnapshot for item in candidates):
        raise ValueError("reconciliation requires one or more exact ResourceSnapshot values")
    if len({item.identity.stable_key for item in candidates}) != 1:
        raise ValueError("resource identities cannot be reconciled together")
    if any(type(value) is not int or value < 0 for value in (now_ms, freshness_window_ms, skew_tolerance_ms)):
        raise ValueError("reconciliation times and tolerances must be non-negative integers")

    times = [item.observed_at_ms for item in candidates]
    skew = max(times) - min(times)
    conflict_fields: list[str] = []
    merged: dict[str, int | None] = {}
    for item in fields(CapacityTruth):
        observed = {getattr(candidate.capacity, item.name) for candidate in candidates if getattr(candidate.capacity, item.name) is not None}
        if len(observed) > 1:
            conflict_fields.append(item.name)
            merged[item.name] = None
        elif observed:
            values = tuple(observed)
            # Capacity uses a lower conservative ceiling; usage/headroom uses the higher safe bound.
            is_ceiling = item.name in {"physical_bytes", "reported_bytes", "allocatable_bytes", "reclaimable_bytes"}
            merged[item.name] = min(values) if is_ceiling else max(values)
        else:
            merged[item.name] = None
    if any(item.confidence is Confidence.QUARANTINED for item in candidates):
        confidence = Confidence.QUARANTINED
    elif conflict_fields or any(item.confidence is Confidence.CONFLICTED for item in candidates):
        confidence = Confidence.CONFLICTED
    elif skew > skew_tolerance_ms or now_ms - max(times) > freshness_window_ms or any(item.confidence is Confidence.STALE for item in candidates):
        confidence = Confidence.STALE
    elif any(item.confidence is Confidence.UNKNOWN for item in candidates):
        confidence = Confidence.UNKNOWN
    elif any(item.confidence is Confidence.UNSUPPORTED for item in candidates):
        confidence = Confidence.UNSUPPORTED
    elif any(item.confidence is Confidence.ESTIMATED for item in candidates):
        confidence = Confidence.ESTIMATED
    else:
        confidence = Confidence.OBSERVED
    capacity = CapacityTruth(**merged)
    provenance = tuple(sorted(
        { (ref.source, ref.reference): ref for item in candidates for ref in item.provenance }.values(),
        key=lambda ref: (ref.source, ref.reference),
    ))
    result = ResourceSnapshot(
        snapshot_id=snapshot_id,
        schema_version=max((item.schema_version for item in candidates), key=lambda value: tuple(int(part) if part.isdigit() else -1 for part in value.split("."))),
        identity=candidates[0].identity,
        observed_at_ms=max(times),
        expires_at_ms=min(item.expires_at_ms for item in candidates),
        confidence=confidence,
        capacity=capacity,
        provenance=provenance,
        m07_discovery_ref=next((item.m07_discovery_ref for item in candidates if item.m07_discovery_ref), None),
        m08_evidence_ref=next((item.m08_evidence_ref for item in candidates if item.m08_evidence_ref), None),
        evidence_origin=(
            EvidenceOrigin.SYNTHETIC_FIXTURE
            if any(item.evidence_origin is EvidenceOrigin.SYNTHETIC_FIXTURE for item in candidates)
            else EvidenceOrigin.DERIVED_ESTIMATE
            if any(item.evidence_origin is EvidenceOrigin.DERIVED_ESTIMATE for item in candidates)
            else EvidenceOrigin.REPORTED_OBSERVATION
        ),
    )
    return SnapshotReconciliation(
        result,
        skew,
        freshness_window_ms,
        tuple(sorted(conflict_fields)),
        confidence in {Confidence.CONFLICTED, Confidence.QUARANTINED},
        content_digest({"candidates": tuple(sorted(item.digest for item in candidates)), "result": result.digest, "skew": skew, "conflicts": tuple(sorted(conflict_fields))}),
    )


class ResourceTwin:
    """In-memory semantic state holder; it has no persistence or hardware side effects."""

    def __init__(self, *, limits: M09Limits = DEFAULT_LIMITS) -> None:
        self._limits = limits
        self._lock = RLock()
        self._snapshots: dict[str, ResourceSnapshot] = {}
        self._latest: dict[str, str] = {}
        self._events: list[ResourceEvent] = []
        self._invalidated: dict[str, str] = {}
        self._quarantines: dict[str, QuarantineRecord] = {}
        self._epochs: dict[str, int] = {}
        self._last_event_at: dict[str, int] = {}
        self._last_event_id: dict[str, str] = {}

    def publish(self, snapshot: ResourceSnapshot, *, event_id: str, at_ms: int, authorization_ref: str, mutation_context: MutationContext | None = None) -> ResourceEvent:
        if type(snapshot) is not ResourceSnapshot:
            raise ValueError("snapshot must be an exact ResourceSnapshot")
        authorization_ref = require_id(authorization_ref, "authorization_ref")
        context = mutation_context or MutationContext(MutationActorKind.INTERACTIVE, "M09:resource-twin-client", authorization_ref, event_id, event_id)
        if type(context) is not MutationContext or context.authorization_ref != authorization_ref:
            raise ValueError("snapshot publication requires matching mutation attribution")
        with self._lock:
            if snapshot.snapshot_id in self._snapshots:
                if self._snapshots[snapshot.snapshot_id] == snapshot:
                    existing_event = next((event for event in self._events if event.event_id == event_id), None)
                    if existing_event is None or existing_event.mutation_context != context:
                        raise ValueError("snapshot is already published under a different event identity")
                    return existing_event
                raise ValueError("snapshot identity cannot be reused for different content")
            if len(self._snapshots) >= self._limits.max_resources:
                raise ValueError("resource snapshot bound exceeded")
            resource_key = snapshot.identity.stable_key
            previous = self._latest.get(resource_key)
            prior_event = self._last_event_id.get(resource_key)
            predecessors = tuple(sorted(item for item in (previous, prior_event) if item is not None))
            epoch = self._epochs.get(resource_key, 0) + 1
            event = ResourceEvent(
                event_id, resource_key, "SNAPSHOT_PUBLISHED", at_ms, predecessors,
                snapshot.provenance, content_digest({"snapshot_digest": snapshot.digest}), authorization_ref,
                snapshot.schema_version, epoch, _verification_status(snapshot), context,
            )
            self._append_event(event)
            self._snapshots[snapshot.snapshot_id] = snapshot
            self._latest[resource_key] = snapshot.snapshot_id
            self._epochs[resource_key] = epoch
            return event

    def latest(self, resource_key: str) -> ResourceSnapshot | None:
        with self._lock:
            snapshot_id = self._latest.get(resource_key)
            return self._snapshots.get(snapshot_id) if snapshot_id is not None else None

    def get(self, snapshot_id: str) -> ResourceSnapshot | None:
        with self._lock:
            return self._snapshots.get(snapshot_id)

    def history(self, resource_key: str | None = None) -> tuple[ResourceEvent, ...]:
        with self._lock:
            return tuple(event for event in self._events if resource_key is None or event.resource_key == resource_key)

    def invalidate(self, snapshot_id: str, *, reason: str, event_id: str, at_ms: int, authorization_ref: str, mutation_context: MutationContext | None = None) -> ResourceEvent:
        reason = require_id(reason, "reason")
        authorization_ref = require_id(authorization_ref, "authorization_ref")
        context = mutation_context or MutationContext(MutationActorKind.INTERACTIVE, "M09:resource-twin-client", authorization_ref, event_id, event_id)
        if type(context) is not MutationContext or context.authorization_ref != authorization_ref:
            raise ValueError("snapshot invalidation requires matching mutation attribution")
        with self._lock:
            snapshot = self._snapshots.get(snapshot_id)
            if snapshot is None:
                raise ValueError("cannot invalidate an unknown snapshot")
            previous_reason = self._invalidated.get(snapshot_id)
            if previous_reason is not None:
                if previous_reason == reason:
                    existing_event = next((event for event in self._events if event.event_id == event_id), None)
                    if existing_event is None or existing_event.mutation_context != context:
                        raise ValueError("snapshot invalidation is already recorded under a different event identity")
                    return existing_event
                raise ValueError("invalidated snapshot reason is immutable")
            epoch = self._epochs.get(snapshot.identity.stable_key, 0) + 1
            prior_event = self._last_event_id.get(snapshot.identity.stable_key)
            predecessors = tuple(sorted({snapshot.snapshot_id, *(() if prior_event is None else (prior_event,))}))
            event = ResourceEvent(
                event_id, snapshot.identity.stable_key, "SNAPSHOT_INVALIDATED", at_ms,
                predecessors, snapshot.provenance,
                content_digest({"reason": reason, "snapshot": snapshot.digest}), authorization_ref,
                snapshot.schema_version, epoch, _verification_status(snapshot),
                context,
            )
            self._append_event(event)
            self._invalidated[snapshot_id] = reason
            self._epochs[snapshot.identity.stable_key] = epoch
            return event

    def quarantine(self, record: QuarantineRecord) -> None:
        if type(record) is not QuarantineRecord:
            raise ValueError("quarantine record must use the exact immutable M09 type")
        with self._lock:
            existing = self._quarantines.get(record.quarantine_id)
            if existing is not None and existing != record:
                raise ValueError("quarantine identity cannot be reused")
            if existing is None:
                self._limits.require("max_events", len(self._quarantines) + 1)
            self._quarantines[record.quarantine_id] = record

    def is_quarantined(self, resource_key: str) -> bool:
        with self._lock:
            return any(item.resource_key == resource_key for item in self._quarantines.values())

    def admission_snapshot(self, resource_key: str, *, now_ms: int) -> ResourceSnapshot | None:
        """Return only fresh, non-invalidated, non-quarantined state for a commitment check."""
        with self._lock:
            snapshot_id = self._latest.get(resource_key)
            snapshot = self._snapshots.get(snapshot_id) if snapshot_id is not None else None
            if snapshot is None or snapshot_id in self._invalidated or self.is_quarantined(resource_key):
                return None
            if not snapshot.is_fresh(now_ms):
                return None
            return snapshot

    def invalidations(self) -> tuple[tuple[str, str], ...]:
        with self._lock:
            return tuple(sorted(self._invalidated.items()))

    def _append_event(self, event: ResourceEvent) -> None:
        self._limits.require("max_events", len(self._events) + 1)
        if any(item.event_id == event.event_id for item in self._events):
            raise ValueError("resource event identity must be unique")
        if event.state_epoch != self._epochs.get(event.resource_key, 0) + 1:
            raise ValueError("resource event state epoch is stale or skipped")
        if event.at_ms < self._last_event_at.get(event.resource_key, 0):
            raise ValueError("resource event time must be monotonic per resource")
        known_ids = {item.event_id for item in self._events}
        if any(item not in known_ids and item not in self._snapshots for item in event.predecessor_ids):
            raise ValueError("resource event predecessor is not present in causal history")
        self._events.append(event)
        self._last_event_at[event.resource_key] = event.at_ms
        self._last_event_id[event.resource_key] = event.event_id


def _verification_status(snapshot: ResourceSnapshot) -> EventVerificationStatus:
    if snapshot.evidence_origin is EvidenceOrigin.SYNTHETIC_FIXTURE:
        return EventVerificationStatus.SYNTHETIC
    if all(item.verification == "VERIFIED" for item in snapshot.provenance):
        return EventVerificationStatus.VERIFIED
    if all(item.verification == "UNVERIFIED" for item in snapshot.provenance):
        return EventVerificationStatus.UNVERIFIED
    return EventVerificationStatus.REFERENCED
