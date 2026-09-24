"""Atomic in-memory lease, reservation and model-residency semantics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import Mapping

from .limits import DEFAULT_LIMITS, M09Limits
from .model import EvidenceOrigin, MutationActorKind, MutationContext, ResourceSnapshot, content_digest, require_id

__all__ = [
    "ClaimKind", "ResourceUnit", "QuantityConversion", "ClaimQuantity", "convert_quantity",
    "ClaimAggregate", "ClaimAlgebra", "ResourceClaim", "LeaseState", "LeaseRequest", "Lease",
    "LeaseTombstone", "ReservationIntent", "FairnessEvidence", "LeaseBook",
    "ResidencyKey", "ResidencyState", "ResidencyTransition", "ResidencyReferenceEvent", "OwnerLivenessEvidence",
    "WarmResidencyHint", "FragmentationEvidence", "PriorityInversionEvidence", "CooperativePreemptionEvidence",
    "OrphanLeaseReconciliation", "ResidencyRegistry", "detect_priority_inversion",
]


class ClaimKind(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"
    EXCLUSIVE = "EXCLUSIVE"


class ResourceUnit(str, Enum):
    BYTE = "BYTE"
    KIBIBYTE = "KIBIBYTE"
    MEBIBYTE = "MEBIBYTE"
    GIBIBYTE = "GIBIBYTE"


_UNIT_BYTES = {
    ResourceUnit.BYTE: 1,
    ResourceUnit.KIBIBYTE: 1024,
    ResourceUnit.MEBIBYTE: 1024**2,
    ResourceUnit.GIBIBYTE: 1024**3,
}


@dataclass(frozen=True)
class QuantityConversion:
    value: int
    source_unit: ResourceUnit
    target_unit: ResourceUnit
    exact: bool
    rounding: str


@dataclass(frozen=True)
class ClaimQuantity:
    value: int
    unit: ResourceUnit

    def __post_init__(self) -> None:
        if type(self.value) is not int or self.value < 0 or self.value > (1 << 63) - 1:
            raise ValueError("claim quantity must be a bounded non-negative integer")
        if not isinstance(self.unit, ResourceUnit):
            raise ValueError("claim quantity requires an explicit ResourceUnit")
        if self.value > ((1 << 63) - 1) // _UNIT_BYTES[self.unit]:
            raise ValueError("claim quantity overflows byte arithmetic")

    @property
    def bytes(self) -> int:
        return self.value * _UNIT_BYTES[self.unit]


def convert_quantity(quantity: ClaimQuantity, target_unit: ResourceUnit, *, rounding: str = "REJECT") -> QuantityConversion:
    if type(quantity) is not ClaimQuantity or not isinstance(target_unit, ResourceUnit):
        raise ValueError("unit conversion requires a typed quantity and target unit")
    if rounding not in {"REJECT", "FLOOR", "CEILING"}:
        raise ValueError("unit conversion rounding must be REJECT, FLOOR or CEILING")
    numerator = quantity.bytes
    denominator = _UNIT_BYTES[target_unit]
    quotient, remainder = divmod(numerator, denominator)
    if remainder and rounding == "REJECT":
        raise ValueError("unit conversion would lose fractional bytes")
    if remainder and rounding == "CEILING":
        quotient += 1
    return QuantityConversion(quotient, quantity.unit, target_unit, remainder == 0, rounding)


class LeaseState(str, Enum):
    ACTIVE = "ACTIVE"
    PREEMPTION_REQUESTED = "PREEMPTION_REQUESTED"
    REVOCATION_REQUESTED = "REVOCATION_REQUESTED"
    REVOKED = "REVOKED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class ResourceClaim:
    claim_id: str
    resource_key: str
    quantity: ClaimQuantity
    kind: ClaimKind
    share_key: str | None = None
    purpose_ref: str = "unspecified"

    def __post_init__(self) -> None:
        for field in ("claim_id", "resource_key", "purpose_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.quantity) is not ClaimQuantity:
            raise ValueError("resource claim requires an explicit typed quantity")
        if not isinstance(self.kind, ClaimKind):
            raise ValueError("claim kind must be explicit")
        if self.share_key is not None:
            object.__setattr__(self, "share_key", require_id(self.share_key, "share_key"))
        if self.kind is ClaimKind.EXCLUSIVE and self.share_key is not None:
            raise ValueError("exclusive claims cannot carry a sharing key")

    @property
    def bytes(self) -> int:
        return self.quantity.bytes


@dataclass(frozen=True)
class ClaimAggregate:
    resource_key: str
    hard_bytes: int
    soft_bytes: int
    exclusive_claim_ids: tuple[str, ...]
    share_groups: tuple[tuple[str, int], ...]


class ClaimAlgebra:
    """Combines typed claims only; this class never grants or reserves capacity."""

    @staticmethod
    def aggregate(claims: tuple[ResourceClaim, ...]) -> tuple[ClaimAggregate, ...]:
        claims = tuple(claims)
        if not claims or any(type(item) is not ResourceClaim for item in claims):
            raise ValueError("claim algebra requires typed claims")
        by_resource: dict[str, list[ResourceClaim]] = {}
        for claim in claims:
            by_resource.setdefault(claim.resource_key, []).append(claim)
        result = []
        for resource_key, scoped in sorted(by_resource.items()):
            hard: dict[str, int] = {}
            soft = 0
            exclusive = []
            for claim in scoped:
                if claim.kind is ClaimKind.EXCLUSIVE:
                    exclusive.append(claim.claim_id)
                elif claim.kind is ClaimKind.SOFT:
                    soft += claim.bytes
                else:
                    group = f"share:{claim.share_key}" if claim.share_key else f"claim:{claim.claim_id}"
                    hard[group] = max(hard.get(group, 0), claim.bytes)
            if exclusive and (len(scoped) > len(exclusive) or len(exclusive) > 1):
                raise ValueError("exclusive claim algebra conflicts with another scoped claim")
            result.append(ClaimAggregate(resource_key, sum(hard.values()), soft, tuple(sorted(exclusive)), tuple(sorted(hard.items()))))
        return tuple(result)


@dataclass(frozen=True)
class LeaseRequest:
    lease_id: str
    idempotency_key: str
    owner_ref: str
    actor_authorization_ref: str
    claims: tuple[ResourceClaim, ...]
    requested_at_ms: int
    ttl_ms: int
    priority: int = 0
    revocable: bool = False
    actor_ref: str = "M09:actor"
    actor_kind: str = "INTERACTIVE"
    priority_evidence_ref: str | None = None
    clock_ref: str = "MONOTONIC_CLOCK"
    clock_uncertainty_ms: int = 0
    mutation_context: MutationContext | None = None

    def __post_init__(self) -> None:
        for field in ("lease_id", "idempotency_key", "owner_ref", "actor_authorization_ref", "actor_ref", "clock_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        claims = tuple(self.claims)
        if not claims or len(claims) > 10_000 or any(type(item) is not ResourceClaim for item in claims):
            raise ValueError("lease request requires bounded typed resource claims")
        if len({item.claim_id for item in claims}) != len(claims):
            raise ValueError("claim identities must be unique within a lease")
        if type(self.requested_at_ms) is not int or self.requested_at_ms < 0:
            raise ValueError("requested_at_ms must be non-negative")
        if type(self.ttl_ms) is not int or not 1 <= self.ttl_ms <= 86_400_000:
            raise ValueError("lease TTL must be bounded to one day")
        if type(self.priority) is not int or not -100 <= self.priority <= 100:
            raise ValueError("priority is an evidence label within [-100, 100]")
        if self.actor_kind not in {"INTERACTIVE", "AUTOMATION", "SERVICE"}:
            raise ValueError("actor kind must be explicit")
        actor_kind = MutationActorKind(self.actor_kind)
        context = self.mutation_context
        if context is None:
            if actor_kind is MutationActorKind.AUTOMATION:
                raise ValueError("automated lease grant requires a complete mutation context")
            context = MutationContext(actor_kind, self.actor_ref, self.actor_authorization_ref, self.lease_id, self.idempotency_key)
            object.__setattr__(self, "mutation_context", context)
        if type(context) is not MutationContext or (context.actor_kind, context.actor_ref, context.authorization_ref, context.idempotency_key) != (actor_kind, self.actor_ref, self.actor_authorization_ref, self.idempotency_key):
            raise ValueError("lease mutation context must bind the exact actor, authorization and idempotency identity")
        if self.priority != 0 and self.priority_evidence_ref is None:
            raise ValueError("non-neutral priority requires authorized policy evidence")
        if self.priority_evidence_ref is not None:
            object.__setattr__(self, "priority_evidence_ref", require_id(self.priority_evidence_ref, "priority_evidence_ref"))
        if type(self.clock_uncertainty_ms) is not int or self.clock_uncertainty_ms < 0:
            raise ValueError("clock uncertainty must be explicit and non-negative")
        object.__setattr__(self, "claims", tuple(sorted(claims, key=lambda item: (item.resource_key, item.claim_id))))


@dataclass(frozen=True)
class Lease:
    lease_id: str
    idempotency_key: str
    owner_ref: str
    actor_authorization_ref: str
    claims: tuple[ResourceClaim, ...]
    granted_at_ms: int
    expires_at_ms: int
    epoch: int
    state: LeaseState = LeaseState.ACTIVE
    revocable: bool = False
    mutation_ref: str = "grant"
    request_digest: str = ""
    actor_ref: str = "M09:actor"
    actor_kind: str = "INTERACTIVE"
    priority: int = 0
    priority_evidence_ref: str | None = None
    clock_ref: str = "MONOTONIC_CLOCK"
    clock_uncertainty_ms: int = 0
    mutation_context: MutationContext | None = None

    def __post_init__(self) -> None:
        for field in ("lease_id", "idempotency_key", "owner_ref", "actor_authorization_ref", "mutation_ref", "actor_ref", "clock_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if any(type(item) is not ResourceClaim for item in self.claims) or not self.claims:
            raise ValueError("lease requires exact resource claims")
        if type(self.granted_at_ms) is not int or self.granted_at_ms < 0:
            raise ValueError("grant time must be non-negative")
        if type(self.epoch) is not int or self.epoch < 1:
            raise ValueError("lease epoch must be positive")
        if type(self.expires_at_ms) is not int or self.expires_at_ms <= self.granted_at_ms:
            raise ValueError("lease expiry must follow grant")
        if not isinstance(self.state, LeaseState):
            raise ValueError("lease state is invalid")
        if self.actor_kind not in {"INTERACTIVE", "AUTOMATION", "SERVICE"} or type(self.priority) is not int or not -100 <= self.priority <= 100:
            raise ValueError("lease actor/priority evidence is invalid")
        if self.priority != 0 and self.priority_evidence_ref is None:
            raise ValueError("lease priority requires policy provenance")
        if self.priority_evidence_ref is not None:
            object.__setattr__(self, "priority_evidence_ref", require_id(self.priority_evidence_ref, "priority_evidence_ref"))
        if type(self.clock_uncertainty_ms) is not int or self.clock_uncertainty_ms < 0:
            raise ValueError("lease clock uncertainty must be non-negative")
        if self.request_digest and (len(self.request_digest) != 64 or any(char not in "0123456789abcdef" for char in self.request_digest)):
            raise ValueError("lease request digest must be lowercase SHA-256")
        context = self.mutation_context
        actor_kind = MutationActorKind(self.actor_kind)
        if context is None:
            if actor_kind is MutationActorKind.AUTOMATION:
                raise ValueError("automated lease state requires a complete mutation context")
            context = MutationContext(actor_kind, self.actor_ref, self.actor_authorization_ref, self.mutation_ref, self.idempotency_key)
            object.__setattr__(self, "mutation_context", context)
        if type(context) is not MutationContext or (context.actor_kind, context.actor_ref, context.authorization_ref) != (actor_kind, self.actor_ref, self.actor_authorization_ref):
            raise ValueError("lease mutation context must bind the exact actor and authorization")


@dataclass(frozen=True)
class LeaseTombstone:
    lease_id: str
    terminal_state: LeaseState
    terminal_at_ms: int
    final_epoch: int
    causal_ref: str
    mutation_context: MutationContext | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "lease_id", require_id(self.lease_id, "lease_id"))
        object.__setattr__(self, "causal_ref", require_id(self.causal_ref, "causal_ref"))
        if not isinstance(self.terminal_state, LeaseState) or self.terminal_state not in {LeaseState.RELEASED, LeaseState.REVOKED, LeaseState.EXPIRED}:
            raise ValueError("tombstone state must be terminal")
        if type(self.mutation_context) is not MutationContext or self.mutation_context.causal_request_ref != self.causal_ref:
            raise ValueError("lease tombstone requires its exact mutation context")
        if type(self.terminal_at_ms) is not int or self.terminal_at_ms < 0 or type(self.final_epoch) is not int or self.final_epoch < 1:
            raise ValueError("tombstone time/epoch is invalid")


@dataclass(frozen=True)
class ReservationIntent:
    intent_id: str
    request: LeaseRequest
    created_at_ms: int
    deadline_ms: int
    clock_ref: str = "MONOTONIC_CLOCK"
    clock_uncertainty_ms: int = 0
    status: str = "PENDING"

    def __post_init__(self) -> None:
        object.__setattr__(self, "intent_id", require_id(self.intent_id, "intent_id"))
        if type(self.request) is not LeaseRequest:
            raise ValueError("reservation intent requires a typed lease request")
        if type(self.created_at_ms) is not int or type(self.deadline_ms) is not int or self.deadline_ms <= self.created_at_ms:
            raise ValueError("reservation intent requires an explicit deadline")
        object.__setattr__(self, "clock_ref", require_id(self.clock_ref, "clock_ref"))
        if type(self.clock_uncertainty_ms) is not int or self.clock_uncertainty_ms < 0:
            raise ValueError("reservation clock uncertainty must be non-negative")
        if self.status not in {"PENDING", "GRANTED", "EXPIRED", "CANCELLED"}:
            raise ValueError("reservation intent status is invalid")


@dataclass(frozen=True)
class FairnessEvidence:
    evidence_id: str
    lease_id: str
    event: str
    observed_at_ms: int
    priority: int
    wait_age_ms: int
    priority_evidence_ref: str | None
    detail_ref: str

    def __post_init__(self) -> None:
        for field in ("evidence_id", "lease_id", "event", "detail_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0 or type(self.priority) is not int or type(self.wait_age_ms) is not int or self.wait_age_ms < 0:
            raise ValueError("fairness evidence time, priority or age is invalid")
        if self.priority_evidence_ref is not None:
            object.__setattr__(self, "priority_evidence_ref", require_id(self.priority_evidence_ref, "priority_evidence_ref"))


@dataclass(frozen=True)
class PriorityInversionEvidence:
    waiting_lease_id: str
    blocking_lease_id: str
    waiting_priority: int
    blocking_priority: int
    wait_age_ms: int
    evidence_ref: str


@dataclass(frozen=True)
class CooperativePreemptionEvidence:
    lease_id: str
    request_ref: str
    requested_at_ms: int
    grace_deadline_ms: int
    lease_epoch: int
    actor_authorization_ref: str


@dataclass(frozen=True)
class OrphanLeaseReconciliation:
    lease_id: str
    owner_ref: str
    status: str
    observed_at_ms: int
    liveness_evidence_ref: str
    resource_keys: tuple[str, ...]
    authorization_ref: str
    mutation_context: MutationContext

    def __post_init__(self) -> None:
        for field in ("lease_id", "owner_ref", "liveness_evidence_ref", "authorization_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if self.status not in {"NOT_ORPHANED", "OWNERSHIP_UNKNOWN_QUARANTINED", "TERMINATED_RECONCILIATION_REQUIRED"}:
            raise ValueError("orphan reconciliation status is invalid")
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise ValueError("orphan reconciliation time must be non-negative")
        if type(self.mutation_context) is not MutationContext or self.mutation_context.authorization_ref != self.authorization_ref:
            raise ValueError("orphan reconciliation requires its exact mutation context")
        object.__setattr__(self, "resource_keys", tuple(sorted(set(require_id(item, "resource_key") for item in self.resource_keys))))


def detect_priority_inversion(waiting: FairnessEvidence, blocking: Lease) -> PriorityInversionEvidence | None:
    if type(waiting) is not FairnessEvidence or type(blocking) is not Lease:
        raise ValueError("priority inversion detection requires typed fairness and lease evidence")
    if waiting.priority <= blocking.priority or blocking.state not in {LeaseState.ACTIVE, LeaseState.PREEMPTION_REQUESTED, LeaseState.REVOCATION_REQUESTED}:
        return None
    return PriorityInversionEvidence(
        waiting.lease_id, blocking.lease_id, waiting.priority, blocking.priority,
        waiting.wait_age_ms, content_digest({"waiting": waiting, "blocking": blocking.lease_id}),
    )


class LeaseBook:
    """Serializes commitment admission; it does not schedule, evict, or contact owners."""

    def __init__(self, *, limits: M09Limits = DEFAULT_LIMITS) -> None:
        self._limits = limits
        self._lock = RLock()
        self._leases: dict[str, Lease] = {}
        self._idempotency: dict[str, str] = {}
        self._tombstones: dict[str, LeaseTombstone] = {}
        self._intents: dict[str, ReservationIntent] = {}
        self._fairness: list[FairnessEvidence] = []
        self._preemption_evidence: list[CooperativePreemptionEvidence] = []
        self._orphan_reconciliations: dict[str, OrphanLeaseReconciliation] = {}
        self._event_epoch = 0

    def active(self) -> tuple[Lease, ...]:
        with self._lock:
            return tuple(sorted((item for item in self._leases.values() if item.state in {LeaseState.ACTIVE, LeaseState.PREEMPTION_REQUESTED, LeaseState.REVOCATION_REQUESTED}), key=lambda item: item.lease_id))

    def intents(self) -> tuple[ReservationIntent, ...]:
        with self._lock:
            return tuple(sorted(self._intents.values(), key=lambda item: (item.created_at_ms, item.intent_id)))

    def fairness_evidence(self) -> tuple[FairnessEvidence, ...]:
        with self._lock:
            return tuple(self._fairness)

    def preemption_evidence(self) -> tuple[CooperativePreemptionEvidence, ...]:
        with self._lock:
            return tuple(self._preemption_evidence)

    def orphan_reconciliations(self) -> tuple[OrphanLeaseReconciliation, ...]:
        with self._lock:
            return tuple(sorted(self._orphan_reconciliations.values(), key=lambda item: item.lease_id))

    def grant(self, request: LeaseRequest, snapshots: Mapping[str, ResourceSnapshot], *, now_ms: int) -> Lease:
        if type(request) is not LeaseRequest or type(now_ms) is not int or now_ms < request.requested_at_ms:
            raise ValueError("grant requires a typed request and monotonic time")
        if request.clock_uncertainty_ms >= request.ttl_ms or now_ms >= request.requested_at_ms + request.ttl_ms:
            raise ValueError("clock uncertainty or elapsed reservation validity prevents lease grant")
        with self._lock:
            existing_id = self._idempotency.get(request.idempotency_key)
            if existing_id is not None:
                existing = self._leases[existing_id]
                if existing.lease_id == request.lease_id and _same_request(existing, request):
                    return existing
                raise ValueError("idempotency key is already bound to a different lease request")
            if request.lease_id in self._leases or request.lease_id in self._tombstones:
                raise ValueError("lease identity is never reused")
            self._limits.require("max_leases", len(self._leases) + 1)
            totals: dict[str, dict[str, int]] = {}
            live_claims = tuple(
                claim
                for lease in self._leases.values()
                if lease.state in {LeaseState.ACTIVE, LeaseState.PREEMPTION_REQUESTED, LeaseState.REVOCATION_REQUESTED}
                for claim in lease.claims
            )
            new_claims = tuple(claim for claim in request.claims if claim.kind is not ClaimKind.SOFT)
            if any(claim.kind is ClaimKind.SOFT for claim in request.claims):
                self._record_fairness(request, "SOFT_INTENT_REQUIRED", now_ms)
                raise ValueError("soft reservations are queued as intent and cannot become hard leases")
            for claim in new_claims:
                if claim.kind is ClaimKind.EXCLUSIVE and any(other.resource_key == claim.resource_key for other in live_claims + request.claims if other.claim_id != claim.claim_id):
                    self._record_fairness(request, "DENIED_EXCLUSIVE_CONFLICT", now_ms)
                    raise ValueError("exclusive resource claim conflicts with another active or composite claim")
                if any(other.kind is ClaimKind.EXCLUSIVE and other.resource_key == claim.resource_key for other in live_claims):
                    self._record_fairness(request, "DENIED_EXCLUSIVE_CONFLICT", now_ms)
                    raise ValueError("resource is held by an exclusive claim")
            for claim in request.claims:
                if claim.kind is ClaimKind.SOFT:
                    continue
                key = f"share:{claim.share_key}" if claim.share_key is not None else f"claim:{claim.claim_id}"
                resource_claims = totals.setdefault(claim.resource_key, {})
                resource_claims[key] = max(resource_claims.get(key, 0), claim.bytes)
            if len(totals) > self._limits.max_claims:
                raise ValueError("composite lease exceeds claim bound")
            for resource_key, grouped_claims in totals.items():
                amount = sum(grouped_claims.values())
                snapshot = snapshots.get(resource_key)
                if type(snapshot) is not ResourceSnapshot or snapshot.identity.stable_key != resource_key:
                    self._record_fairness(request, "DENIED_UNKNOWN_RESOURCE", now_ms)
                    raise ValueError("lease resource has no matching authoritative snapshot")
                if snapshot.evidence_origin is not EvidenceOrigin.REPORTED_OBSERVATION:
                    self._record_fairness(request, "DENIED_NON_PRODUCTION_EVIDENCE", now_ms)
                    raise ValueError("synthetic or derived evidence cannot authorize a production lease")
                if not snapshot.is_fresh(now_ms):
                    self._record_fairness(request, "DENIED_NON_FRESH_TRUTH", now_ms)
                    raise ValueError("stale, estimated, conflicted or unknown state cannot authorize a hard commitment")
                baseline = snapshot.capacity.available_bytes()
                existing_groups: dict[str, int] = {}
                for claim in (
                    claim
                    for lease in self._leases.values()
                    if lease.state in {LeaseState.ACTIVE, LeaseState.PREEMPTION_REQUESTED, LeaseState.REVOCATION_REQUESTED}
                    for claim in lease.claims
                    if claim.resource_key == resource_key and claim.kind is not ClaimKind.SOFT
                ):
                    group = f"share:{claim.share_key}" if claim.share_key is not None else f"claim:{claim.claim_id}"
                    existing_groups[group] = max(existing_groups.get(group, 0), claim.bytes)
                for group, amount_bytes in grouped_claims.items():
                    existing_groups[group] = max(existing_groups.get(group, 0), amount_bytes)
                already_held = sum(existing_groups.values()) - sum(grouped_claims.values())
                if amount > max(0, baseline - already_held):
                    self._record_fairness(request, "DENIED_CAPACITY", now_ms)
                    raise ValueError("lease would overcommit allocatable capacity")
            self._limits.require("max_events", len(self._fairness) + 1)
            next_epoch = self._event_epoch + 1
            lease = Lease(
                request.lease_id, request.idempotency_key, request.owner_ref,
                request.actor_authorization_ref, request.claims, now_ms,
                now_ms + request.ttl_ms, next_epoch, LeaseState.ACTIVE,
                request.revocable, "grant", content_digest(request), request.actor_ref,
                request.actor_kind, request.priority, request.priority_evidence_ref,
                request.clock_ref, request.clock_uncertainty_ms,
                mutation_context=request.mutation_context,
            )
            fairness = self._new_fairness(request, "GRANTED", now_ms, len(self._fairness) + 1)
            self._event_epoch = next_epoch
            self._leases[lease.lease_id] = lease
            self._idempotency[request.idempotency_key] = lease.lease_id
            self._fairness.append(fairness)
            return lease

    def enqueue(self, intent: ReservationIntent) -> None:
        with self._lock:
            existing = self._intents.get(intent.intent_id)
            if existing is not None and existing != intent:
                raise ValueError("reservation intent identity cannot be reused")
            self._limits.require("max_leases", len(self._intents) + (existing is None))
            self._intents[intent.intent_id] = intent

    def renew(self, lease_id: str, snapshots: Mapping[str, ResourceSnapshot], *, now_ms: int, ttl_ms: int, expected_epoch: int, authorization_ref: str, mutation_context: MutationContext | None = None) -> Lease:
        with self._lock:
            lease = self._require_live(lease_id, now_ms)
            if lease.state is not LeaseState.ACTIVE:
                raise ValueError("pending preemption or revocation cannot be renewed")
            if lease.epoch != expected_epoch:
                raise ValueError("stale lease epoch cannot be renewed")
            authorization_ref = require_id(authorization_ref, "authorization_ref")
            context = self._mutation_context(
                lease, mutation_context, action="renew", authorization_ref=authorization_ref,
                causal_request_ref=f"renew:{lease.lease_id}:{expected_epoch}", epoch=expected_epoch,
            ) if mutation_context is None else mutation_context
            if type(context) is not MutationContext or context.authorization_ref != authorization_ref:
                raise ValueError("renewal mutation context must bind its authorization")
            if type(ttl_ms) is not int or not 1 <= ttl_ms <= 86_400_000:
                raise ValueError("renewal TTL must be bounded to one day")
            if lease.clock_uncertainty_ms >= ttl_ms:
                raise ValueError("clock uncertainty prevents renewal validity proof")
            totals: dict[str, int] = {}
            for claim in lease.claims:
                totals[claim.resource_key] = totals.get(claim.resource_key, 0) + claim.bytes
            for resource_key, amount in totals.items():
                snapshot = snapshots.get(resource_key)
                if type(snapshot) is not ResourceSnapshot or not snapshot.is_fresh(now_ms):
                    raise ValueError("renewal requires fresh observed capacity truth")
                if snapshot.evidence_origin is not EvidenceOrigin.REPORTED_OBSERVATION:
                    raise ValueError("renewal requires reported production resource evidence")
                if snapshot.identity.stable_key != resource_key:
                    raise ValueError("renewal snapshot identity does not match the lease claim")
                other_held = sum(
                    claim.bytes for other in self._leases.values()
                    if other.lease_id != lease_id and other.state in {LeaseState.ACTIVE, LeaseState.PREEMPTION_REQUESTED, LeaseState.REVOCATION_REQUESTED}
                    for claim in other.claims if claim.resource_key == resource_key
                )
                if amount > max(0, snapshot.capacity.available_bytes() - other_held):
                    raise ValueError("renewal would overcommit current capacity")
            self._event_epoch += 1
            renewed = Lease(
                lease.lease_id, lease.idempotency_key, lease.owner_ref, authorization_ref,
                lease.claims, now_ms, now_ms + ttl_ms, self._event_epoch,
                LeaseState.ACTIVE, lease.revocable, "renewal",
                lease.request_digest,
                context.actor_ref, context.actor_kind.value, lease.priority, lease.priority_evidence_ref,
                lease.clock_ref, lease.clock_uncertainty_ms,
                mutation_context=context,
            )
            self._leases[lease_id] = renewed
            return renewed

    def release(self, lease_id: str, *, now_ms: int, expected_epoch: int, causal_ref: str, mutation_context: MutationContext | None = None) -> LeaseTombstone:
        causal_ref = require_id(causal_ref, "causal_ref")
        with self._lock:
            existing = self._tombstones.get(lease_id)
            if existing is not None:
                if existing.causal_ref == causal_ref:
                    return existing
                raise ValueError("terminal lease identity cannot be released twice")
            lease = self._leases.get(lease_id)
            if lease is None or lease.state not in {LeaseState.ACTIVE, LeaseState.PREEMPTION_REQUESTED, LeaseState.REVOCATION_REQUESTED}:
                raise ValueError("only a live lease can be released")
            if type(now_ms) is not int or now_ms < lease.granted_at_ms or now_ms >= lease.expires_at_ms or lease.epoch != expected_epoch:
                raise ValueError("release has stale epoch or invalid time")
            context = self._mutation_context(
                lease, mutation_context, action="release", authorization_ref=(mutation_context.authorization_ref if mutation_context is not None else lease.actor_authorization_ref),
                causal_request_ref=causal_ref, epoch=expected_epoch,
            )
            self._event_epoch += 1
            tombstone = LeaseTombstone(lease_id, LeaseState.RELEASED, now_ms, self._event_epoch, causal_ref, context)
            self._leases[lease_id] = Lease(
                lease.lease_id, lease.idempotency_key, lease.owner_ref, context.authorization_ref,
                lease.claims, lease.granted_at_ms, lease.expires_at_ms, self._event_epoch,
                LeaseState.RELEASED, lease.revocable, "release", lease.request_digest,
                context.actor_ref, context.actor_kind.value, lease.priority, lease.priority_evidence_ref,
                lease.clock_ref, lease.clock_uncertainty_ms,
                mutation_context=context,
            )
            self._tombstones[lease_id] = tombstone
            return tombstone

    def request_cooperative_preemption(self, lease_id: str, *, now_ms: int, grace_deadline_ms: int, expected_epoch: int, request_ref: str, mutation_context: MutationContext | None = None) -> Lease:
        request_ref = require_id(request_ref, "request_ref")
        if type(grace_deadline_ms) is not int or grace_deadline_ms <= now_ms or grace_deadline_ms - now_ms > 300_000:
            raise ValueError("cooperative preemption requires a bounded grace deadline")
        with self._lock:
            lease = self._require_live(lease_id, now_ms)
            if lease.state is not LeaseState.ACTIVE or lease.epoch != expected_epoch or not lease.revocable:
                raise ValueError("preemption requires current epoch and a revocable lease")
            context = self._mutation_context(
                lease, mutation_context, action="preempt", authorization_ref=(mutation_context.authorization_ref if mutation_context is not None else lease.actor_authorization_ref),
                causal_request_ref=request_ref, epoch=expected_epoch,
            )
            self._limits.require("max_events", len(self._preemption_evidence) + 1)
            self._event_epoch += 1
            updated = Lease(
                lease.lease_id, lease.idempotency_key, lease.owner_ref, context.authorization_ref,
                lease.claims, lease.granted_at_ms, lease.expires_at_ms, self._event_epoch,
                LeaseState.PREEMPTION_REQUESTED, lease.revocable, request_ref, lease.request_digest,
                context.actor_ref, context.actor_kind.value, lease.priority, lease.priority_evidence_ref,
                lease.clock_ref, lease.clock_uncertainty_ms,
                mutation_context=context,
            )
            self._leases[lease_id] = updated
            self._preemption_evidence.append(CooperativePreemptionEvidence(
                lease_id, request_ref, now_ms, grace_deadline_ms, updated.epoch,
                lease.actor_authorization_ref,
            ))
            return updated

    def request_revocation(self, lease_id: str, *, now_ms: int, expected_epoch: int, authorization_ref: str, reason_ref: str, mutation_context: MutationContext | None = None) -> Lease:
        authorization_ref = require_id(authorization_ref, "authorization_ref")
        reason_ref = require_id(reason_ref, "reason_ref")
        with self._lock:
            lease = self._require_live(lease_id, now_ms)
            if lease.state is not LeaseState.ACTIVE or lease.epoch != expected_epoch:
                raise ValueError("revocation requires the current active lease epoch")
            context = self._mutation_context(
                lease, mutation_context, action="revoke", authorization_ref=authorization_ref,
                causal_request_ref=reason_ref, epoch=expected_epoch,
            )
            self._event_epoch += 1
            updated = Lease(
                lease.lease_id, lease.idempotency_key, lease.owner_ref, authorization_ref,
                lease.claims, lease.granted_at_ms, lease.expires_at_ms, self._event_epoch,
                LeaseState.REVOCATION_REQUESTED, lease.revocable, reason_ref, lease.request_digest,
                context.actor_ref, context.actor_kind.value, lease.priority, lease.priority_evidence_ref,
                lease.clock_ref, lease.clock_uncertainty_ms,
                mutation_context=context,
            )
            self._leases[lease_id] = updated
            return updated

    def reconcile_orphan(self, lease_id: str, liveness: OwnerLivenessEvidence, *, now_ms: int, maximum_liveness_age_ms: int, authorization_ref: str, mutation_context: MutationContext | None = None) -> OrphanLeaseReconciliation:
        authorization_ref = require_id(authorization_ref, "authorization_ref")
        if type(now_ms) is not int or type(maximum_liveness_age_ms) is not int or maximum_liveness_age_ms < 0:
            raise ValueError("orphan reconciliation time bounds are invalid")
        with self._lock:
            lease = self._leases.get(lease_id)
            if lease is None or lease.state not in {LeaseState.ACTIVE, LeaseState.PREEMPTION_REQUESTED, LeaseState.REVOCATION_REQUESTED}:
                raise ValueError("orphan reconciliation requires a live lease")
            if type(liveness) is not OwnerLivenessEvidence or liveness.owner_ref != lease.owner_ref:
                raise ValueError("liveness evidence must bind the exact lease owner")
            context = self._mutation_context(
                lease, mutation_context, action="orphan-reconcile", authorization_ref=authorization_ref,
                causal_request_ref=liveness.evidence_ref, epoch=lease.epoch,
            )
            fresh = 0 <= now_ms - liveness.observed_at_ms <= maximum_liveness_age_ms
            if liveness.state == "ALIVE" and fresh:
                status = "NOT_ORPHANED"
            elif liveness.state == "TERMINATED" and fresh:
                status = "TERMINATED_RECONCILIATION_REQUIRED"
            else:
                status = "OWNERSHIP_UNKNOWN_QUARANTINED"
            evidence = OrphanLeaseReconciliation(
                lease_id, lease.owner_ref, status, now_ms, liveness.evidence_ref,
                tuple(sorted({claim.resource_key for claim in lease.claims})), authorization_ref, context,
            )
            existing = self._orphan_reconciliations.get(lease_id)
            if existing is not None:
                if existing == evidence:
                    return existing
                if existing.status == "TERMINATED_RECONCILIATION_REQUIRED" and status != existing.status:
                    raise ValueError("orphan reconciliation cannot erase stronger termination evidence")
            self._orphan_reconciliations[lease_id] = evidence
            if status in {"TERMINATED_RECONCILIATION_REQUIRED", "OWNERSHIP_UNKNOWN_QUARANTINED"} and lease.state is LeaseState.ACTIVE:
                self._event_epoch += 1
                self._leases[lease_id] = Lease(
                    lease.lease_id, lease.idempotency_key, lease.owner_ref, context.authorization_ref,
                    lease.claims, lease.granted_at_ms, lease.expires_at_ms, self._event_epoch,
                    LeaseState.REVOCATION_REQUESTED, lease.revocable, evidence.liveness_evidence_ref,
                    lease.request_digest, context.actor_ref, context.actor_kind.value, lease.priority,
                    lease.priority_evidence_ref, lease.clock_ref, lease.clock_uncertainty_ms,
                    mutation_context=context,
                )
            return evidence

    def acknowledge_revocation(self, lease_id: str, *, now_ms: int, expected_epoch: int, owner_ack_ref: str, mutation_context: MutationContext | None = None) -> LeaseTombstone:
        owner_ack_ref = require_id(owner_ack_ref, "owner_ack_ref")
        with self._lock:
            existing = self._tombstones.get(lease_id)
            if existing is not None:
                if existing.terminal_state is LeaseState.REVOKED and existing.causal_ref == owner_ack_ref:
                    return existing
                raise ValueError("revocation terminal identity has a conflicting outcome")
            lease = self._leases.get(lease_id)
            if lease is None or lease.state is not LeaseState.REVOCATION_REQUESTED or lease.epoch != expected_epoch:
                raise ValueError("revocation acknowledgement must match a current revocation request")
            if type(now_ms) is not int or now_ms < lease.granted_at_ms or now_ms >= lease.expires_at_ms:
                raise ValueError("revocation acknowledgement has invalid time")
            context = mutation_context or MutationContext(
                MutationActorKind.SERVICE, lease.owner_ref, lease.actor_authorization_ref,
                owner_ack_ref, f"{lease.idempotency_key}:owner-ack:{expected_epoch}",
            )
            if type(context) is not MutationContext or context.causal_request_ref != owner_ack_ref:
                raise ValueError("owner acknowledgement requires an exact mutation context")
            self._event_epoch += 1
            tombstone = LeaseTombstone(lease_id, LeaseState.REVOKED, now_ms, self._event_epoch, owner_ack_ref, context)
            self._leases[lease_id] = Lease(
                lease.lease_id, lease.idempotency_key, lease.owner_ref, context.authorization_ref,
                lease.claims, lease.granted_at_ms, lease.expires_at_ms, self._event_epoch,
                LeaseState.REVOKED, lease.revocable, owner_ack_ref, lease.request_digest,
                context.actor_ref, context.actor_kind.value, lease.priority, lease.priority_evidence_ref,
                lease.clock_ref, lease.clock_uncertainty_ms,
                mutation_context=context,
            )
            self._tombstones[lease_id] = tombstone
            return tombstone

    def expire(self, *, now_ms: int) -> tuple[LeaseTombstone, ...]:
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("expiry clock value must be non-negative monotonic milliseconds")
        with self._lock:
            expired: list[LeaseTombstone] = []
            for lease in tuple(self._leases.values()):
                if lease.state not in {LeaseState.ACTIVE, LeaseState.PREEMPTION_REQUESTED, LeaseState.REVOCATION_REQUESTED} or lease.expires_at_ms > now_ms:
                    continue
                self._event_epoch += 1
                context = MutationContext(
                    MutationActorKind.SERVICE, "M09:lease-expiry-policy", "M09:lease-ttl-policy",
                    f"expiry:{lease.lease_id}", f"{lease.idempotency_key}:expire:{lease.epoch}",
                )
                tombstone = LeaseTombstone(lease.lease_id, LeaseState.EXPIRED, now_ms, self._event_epoch, context.causal_request_ref, context)
                self._tombstones[lease.lease_id] = tombstone
                self._leases[lease.lease_id] = Lease(
                    lease.lease_id, lease.idempotency_key, lease.owner_ref, context.authorization_ref,
                    lease.claims, lease.granted_at_ms, lease.expires_at_ms, self._event_epoch,
                    LeaseState.EXPIRED, lease.revocable, "expiry", lease.request_digest,
                    context.actor_ref, context.actor_kind.value, lease.priority, lease.priority_evidence_ref,
                    lease.clock_ref, lease.clock_uncertainty_ms,
                    mutation_context=context,
                )
                expired.append(tombstone)
            return tuple(expired)

    def tombstone(self, lease_id: str) -> LeaseTombstone | None:
        with self._lock:
            return self._tombstones.get(lease_id)

    @staticmethod
    def _mutation_context(
        lease: Lease,
        supplied: MutationContext | None,
        *,
        action: str,
        authorization_ref: str,
        causal_request_ref: str,
        epoch: int,
    ) -> MutationContext:
        authorization_ref = require_id(authorization_ref, "authorization_ref")
        causal_request_ref = require_id(causal_request_ref, "causal_request_ref")
        if supplied is None:
            actor_kind = MutationActorKind(lease.actor_kind)
            if actor_kind is MutationActorKind.AUTOMATION:
                raise ValueError("automated lease mutation requires a complete mutation context")
            return MutationContext(
                actor_kind, lease.actor_ref, authorization_ref, causal_request_ref,
                f"{lease.idempotency_key}:{action}:{epoch}",
            )
        if type(supplied) is not MutationContext or supplied.authorization_ref != authorization_ref or supplied.causal_request_ref != causal_request_ref:
            raise ValueError("lease mutation context must bind the exact authorization and causal request")
        return supplied

    def _require_live(self, lease_id: str, now_ms: int) -> Lease:
        lease = self._leases.get(lease_id)
        if lease is None or lease.state not in {LeaseState.ACTIVE, LeaseState.PREEMPTION_REQUESTED, LeaseState.REVOCATION_REQUESTED} or now_ms >= lease.expires_at_ms:
            raise ValueError("lease is absent, terminal or expired")
        return lease

    def _record_fairness(self, request: LeaseRequest, event: str, at_ms: int) -> None:
        self._limits.require("max_events", len(self._fairness) + 1)
        self._fairness.append(self._new_fairness(request, event, at_ms, len(self._fairness) + 1))

    @staticmethod
    def _new_fairness(request: LeaseRequest, event: str, at_ms: int, sequence: int) -> FairnessEvidence:
        return FairnessEvidence(
            f"fairness:{request.lease_id}:{sequence}", request.lease_id,
            event, at_ms, request.priority, max(0, at_ms - request.requested_at_ms),
            request.priority_evidence_ref,
            content_digest({"owner": request.owner_ref, "claims": request.claims, "actor": request.actor_ref, "authorization": request.actor_authorization_ref}),
        )


@dataclass(frozen=True)
class ResidencyKey:
    model_ref: str
    model_revision: str
    component_ref: str
    resource_key: str
    compatibility_digest: str

    def __post_init__(self) -> None:
        for field in ("model_ref", "model_revision", "component_ref", "resource_key"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.compatibility_digest) is not str or len(self.compatibility_digest) != 64 or any(char not in "0123456789abcdef" for char in self.compatibility_digest):
            raise ValueError("residency compatibility must be bound by a lowercase SHA-256 digest")


class ResidencyState(str, Enum):
    UNKNOWN = "UNKNOWN"
    LOADING = "LOADING"
    PARTIAL = "PARTIAL"
    RESIDENT = "RESIDENT"
    UNLOADING = "UNLOADING"
    EVICTED = "EVICTED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True)
class ResidencyTransition:
    key: ResidencyKey
    previous_state: ResidencyState
    current_state: ResidencyState
    epoch: int
    at_ms: int
    authorization_ref: str
    causal_ref: str
    verification_ref: str | None
    mutation_context: MutationContext

    def __post_init__(self) -> None:
        if type(self.key) is not ResidencyKey or not isinstance(self.previous_state, ResidencyState) or not isinstance(self.current_state, ResidencyState):
            raise ValueError("residency transition requires exact identity and explicit states")
        if type(self.epoch) is not int or self.epoch < 1 or type(self.at_ms) is not int or self.at_ms < 0:
            raise ValueError("residency transition epoch/time must be positive and bounded")
        for field in ("authorization_ref", "causal_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.mutation_context) is not MutationContext or (self.mutation_context.authorization_ref, self.mutation_context.causal_request_ref) != (self.authorization_ref, self.causal_ref):
            raise ValueError("residency transition requires its exact mutation context")
        if self.verification_ref is not None:
            object.__setattr__(self, "verification_ref", require_id(self.verification_ref, "verification_ref"))
        if self.current_state is ResidencyState.RESIDENT and self.verification_ref is None:
            raise ValueError("RESIDENT transition requires exact verification evidence")


@dataclass(frozen=True)
class ResidencyReferenceEvent:
    key: ResidencyKey
    consumer_ref: str
    operation: str
    reference_count: int
    mutation_context: MutationContext

    def __post_init__(self) -> None:
        if type(self.key) is not ResidencyKey:
            raise ValueError("residency reference event requires exact identity")
        object.__setattr__(self, "consumer_ref", require_id(self.consumer_ref, "consumer_ref"))
        if self.operation not in {"RETAIN", "RELEASE"} or type(self.reference_count) is not int or self.reference_count < 0:
            raise ValueError("residency reference event operation/count is invalid")
        if type(self.mutation_context) is not MutationContext:
            raise ValueError("residency reference event requires mutation attribution")


@dataclass(frozen=True)
class OwnerLivenessEvidence:
    owner_ref: str
    state: str
    authority_ref: str
    observed_at_ms: int
    evidence_ref: str

    def __post_init__(self) -> None:
        for field in ("owner_ref", "authority_ref", "evidence_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if self.state not in {"ALIVE", "TERMINATED", "UNKNOWN"}:
            raise ValueError("owner liveness must be explicit")
        if self.state != "UNKNOWN" and self.authority_ref.split(":", 1)[0] != "M11":
            raise ValueError("lifecycle evidence must be referenced to M11")
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise ValueError("liveness time must be non-negative")


@dataclass(frozen=True)
class WarmResidencyHint:
    hint_id: str
    key: ResidencyKey
    observed_at_ms: int
    expires_at_ms: int
    provenance_ref: str

    def __post_init__(self) -> None:
        for field in ("hint_id", "provenance_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.observed_at_ms) is not int or type(self.expires_at_ms) is not int or self.expires_at_ms < self.observed_at_ms:
            raise ValueError("warmth hint validity window is invalid")

    def is_current(self, now_ms: int) -> bool:
        return type(now_ms) is int and self.observed_at_ms <= now_ms <= self.expires_at_ms


@dataclass(frozen=True)
class FragmentationEvidence:
    resource_key: str
    total_free_bytes: int | None
    largest_contiguous_bytes: int | None
    provider_evidence_ref: str
    observed_at_ms: int

    def __post_init__(self) -> None:
        for field in ("resource_key", "provider_evidence_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        for field in ("total_free_bytes", "largest_contiguous_bytes"):
            value = getattr(self, field)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{field} must be non-negative or unknown")
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise ValueError("fragmentation timestamp must be non-negative")
        if self.total_free_bytes is not None and self.largest_contiguous_bytes is not None and self.largest_contiguous_bytes > self.total_free_bytes:
            raise ValueError("largest contiguous block cannot exceed total free bytes")

    def can_fit_contiguous(self, required_bytes: int) -> bool | None:
        if type(required_bytes) is not int or required_bytes < 0:
            raise ValueError("required bytes must be non-negative")
        if self.largest_contiguous_bytes is None:
            return None
        return required_bytes <= self.largest_contiguous_bytes


class ResidencyRegistry:
    """Reference counting is local semantic ownership; it does not move material."""

    def __init__(self, *, maximum_entries: int = 10_000, maximum_journal_entries: int = 100_000) -> None:
        if type(maximum_entries) is not int or maximum_entries < 1 or type(maximum_journal_entries) is not int or not 1 <= maximum_journal_entries <= 100_000:
            raise ValueError("residency entry and journal bounds must be positive and finite")
        self._lock = RLock()
        self._maximum = maximum_entries
        self._maximum_journal = maximum_journal_entries
        self._consumers: dict[ResidencyKey, set[str]] = {}
        self._states: dict[ResidencyKey, ResidencyState] = {}
        self._epochs: dict[ResidencyKey, int] = {}
        self._last_at_ms: dict[ResidencyKey, int] = {}
        self._journal: list[ResidencyTransition] = []
        self._reference_events: list[ResidencyReferenceEvent] = []
        self._mutation_replays: dict[str, tuple[str, object]] = {}

    def transition(self, key: ResidencyKey, new_state: ResidencyState, *, expected_epoch: int, at_ms: int, authorization_ref: str, causal_ref: str, verification_ref: str | None = None, mutation_context: MutationContext | None = None) -> ResidencyTransition:
        if type(key) is not ResidencyKey:
            raise ValueError("residency transition must bind exact artifact/device identity")
        authorization_ref = require_id(authorization_ref, "authorization_ref")
        causal_ref = require_id(causal_ref, "causal_ref")
        if verification_ref is not None:
            verification_ref = require_id(verification_ref, "verification_ref")
        if not isinstance(new_state, ResidencyState) or type(at_ms) is not int or at_ms < 0:
            raise ValueError("residency transition target/time is invalid")
        context = mutation_context or MutationContext(
            MutationActorKind.INTERACTIVE, "M09:residency-client", authorization_ref,
            causal_ref, f"residency:{key.compatibility_digest}:{expected_epoch}:{new_state.value}",
        )
        if type(context) is not MutationContext or (context.authorization_ref, context.causal_request_ref) != (authorization_ref, causal_ref):
            raise ValueError("residency mutation context must bind exact authorization and cause")
        with self._lock:
            request_digest = content_digest({"key": key, "new_state": new_state, "expected_epoch": expected_epoch, "at_ms": at_ms, "authorization_ref": authorization_ref, "causal_ref": causal_ref, "verification_ref": verification_ref, "mutation_context": context})
            replay = self._mutation_replays.get(context.idempotency_key)
            if replay is not None:
                if replay[0] != request_digest or type(replay[1]) is not ResidencyTransition:
                    raise ValueError("residency idempotency key binds conflicting mutation semantics")
                return replay[1]
            previous = self._states.get(key, ResidencyState.UNKNOWN)
            epoch = self._epochs.get(key, 0)
            if key not in self._states and len(self._states) >= self._maximum:
                raise ValueError("residency registry entry bound exceeded")
            if expected_epoch != epoch:
                raise ValueError("stale residency epoch cannot mutate state")
            if at_ms < self._last_at_ms.get(key, 0):
                raise ValueError("residency transition time must be monotonic")
            if len(self._journal) + len(self._reference_events) >= self._maximum_journal:
                raise ValueError("residency transition journal bound exceeded")
            allowed = {
                ResidencyState.UNKNOWN: {ResidencyState.LOADING, ResidencyState.QUARANTINED},
                ResidencyState.LOADING: {ResidencyState.PARTIAL, ResidencyState.RESIDENT, ResidencyState.FAILED, ResidencyState.QUARANTINED},
                ResidencyState.PARTIAL: {ResidencyState.LOADING, ResidencyState.RESIDENT, ResidencyState.FAILED, ResidencyState.QUARANTINED},
                ResidencyState.RESIDENT: {ResidencyState.UNLOADING, ResidencyState.QUARANTINED},
                ResidencyState.UNLOADING: {ResidencyState.EVICTED, ResidencyState.FAILED, ResidencyState.QUARANTINED},
                ResidencyState.EVICTED: {ResidencyState.LOADING},
                ResidencyState.FAILED: {ResidencyState.LOADING, ResidencyState.QUARANTINED},
                ResidencyState.QUARANTINED: {ResidencyState.LOADING},
            }
            if new_state not in allowed[previous]:
                raise ValueError(f"invalid residency transition {previous.value}->{new_state.value}")
            if new_state is ResidencyState.RESIDENT and verification_ref is None:
                raise ValueError("RESIDENT requires an exact verification reference")
            if new_state in {ResidencyState.UNLOADING, ResidencyState.EVICTED} and self._consumers.get(key):
                raise ValueError("active consumers prevent residency unload/eviction")
            transition = ResidencyTransition(key, previous, new_state, epoch + 1, at_ms, authorization_ref, causal_ref, verification_ref, context)
            self._states[key] = new_state
            self._epochs[key] = epoch + 1
            self._last_at_ms[key] = at_ms
            self._journal.append(transition)
            self._mutation_replays[context.idempotency_key] = (request_digest, transition)
            return transition

    def retain(self, key: ResidencyKey, consumer_ref: str, *, mutation_context: MutationContext) -> int:
        consumer_ref = require_id(consumer_ref, "consumer_ref")
        if type(key) is not ResidencyKey or type(mutation_context) is not MutationContext:
            raise ValueError("residency retain requires exact identity and mutation context")
        with self._lock:
            digest = content_digest({"operation": "RETAIN", "key": key, "consumer_ref": consumer_ref, "context": mutation_context})
            replay = self._mutation_replays.get(mutation_context.idempotency_key)
            if replay is not None:
                if replay[0] != digest or type(replay[1]) is not ResidencyReferenceEvent:
                    raise ValueError("residency idempotency key binds conflicting mutation semantics")
                return replay[1].reference_count
            if self._states.get(key, ResidencyState.UNKNOWN) is not ResidencyState.RESIDENT:
                raise ValueError("only exactly verified RESIDENT material may be shared")
            if key not in self._consumers and len(self._consumers) >= self._maximum:
                raise ValueError("residency registry bound exceeded")
            if len(self._journal) + len(self._reference_events) >= self._maximum_journal:
                raise ValueError("residency transition journal bound exceeded")
            consumers = self._consumers.setdefault(key, set())
            consumers.add(consumer_ref)
            event = ResidencyReferenceEvent(key, consumer_ref, "RETAIN", len(consumers), mutation_context)
            self._reference_events.append(event)
            self._mutation_replays[mutation_context.idempotency_key] = (digest, event)
            return event.reference_count

    def release(self, key: ResidencyKey, consumer_ref: str, *, mutation_context: MutationContext) -> int:
        consumer_ref = require_id(consumer_ref, "consumer_ref")
        if type(key) is not ResidencyKey or type(mutation_context) is not MutationContext:
            raise ValueError("residency release requires exact identity and mutation context")
        with self._lock:
            digest = content_digest({"operation": "RELEASE", "key": key, "consumer_ref": consumer_ref, "context": mutation_context})
            replay = self._mutation_replays.get(mutation_context.idempotency_key)
            if replay is not None:
                if replay[0] != digest or type(replay[1]) is not ResidencyReferenceEvent:
                    raise ValueError("residency idempotency key binds conflicting mutation semantics")
                return replay[1].reference_count
            consumers = self._consumers.get(key)
            if consumers is None or consumer_ref not in consumers:
                raise ValueError("consumer does not own this residency reference")
            if len(self._journal) + len(self._reference_events) >= self._maximum_journal:
                raise ValueError("residency transition journal bound exceeded")
            consumers.remove(consumer_ref)
            if not consumers:
                del self._consumers[key]
                remaining = 0
            else:
                remaining = len(consumers)
            event = ResidencyReferenceEvent(key, consumer_ref, "RELEASE", remaining, mutation_context)
            self._reference_events.append(event)
            self._mutation_replays[mutation_context.idempotency_key] = (digest, event)
            return remaining

    def count(self, key: ResidencyKey) -> int:
        with self._lock:
            return len(self._consumers.get(key, ()))

    def state(self, key: ResidencyKey) -> ResidencyState:
        with self._lock:
            return self._states.get(key, ResidencyState.UNKNOWN)

    def transitions(self, key: ResidencyKey | None = None) -> tuple[ResidencyTransition, ...]:
        with self._lock:
            return tuple(item for item in self._journal if key is None or item.key == key)

    def reference_history(self, key: ResidencyKey | None = None) -> tuple[ResidencyReferenceEvent, ...]:
        with self._lock:
            return tuple(item for item in self._reference_events if key is None or item.key == key)


def _same_request(lease: Lease, request: LeaseRequest) -> bool:
    return lease.request_digest == content_digest(request)
