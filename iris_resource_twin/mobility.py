"""Provider-neutral, evidence-only resource mobility and spill contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock

from .limits import DEFAULT_LIMITS, M09Limits
from .model import EvidenceOrigin, MutationActorKind, MutationContext, ResourceIdentity, ResourceSnapshot, ResourceTier, content_digest, require_id

__all__ = [
    "TransferState", "DirtyState", "TransferCostState", "DurabilityClass",
    "SpillTargetCapability", "TransferSegment", "TransferCostEvidence",
    "TransferRequest", "OffloadTransaction", "MobilityOutcome", "PrefetchIntent",
    "PrefetchBudget", "MobilityLedger", "SourceReleaseAuthorization",
    "LocalityHint", "SpillGarbageCandidate", "SpillGarbageEligibility",
    "evaluate_spill_garbage", "ContentionState", "BandwidthContentionEvidence",
    "CompositeMemberOutcome", "CompositeMobilityOutcome", "ReferenceActivity",
    "verify_source_release_authorization",
]


class TransferState(str, Enum):
    PREPARED = "PREPARED"
    COPYING = "COPYING"
    PARTIAL = "PARTIAL"
    VERIFIED = "VERIFIED"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"
    QUARANTINED = "QUARANTINED"


class DirtyState(str, Enum):
    CLEAN = "CLEAN"
    DIRTY = "DIRTY"
    RECONSTRUCTIBLE = "RECONSTRUCTIBLE"
    UNKNOWN = "UNKNOWN"


class TransferCostState(str, Enum):
    MEASURED = "MEASURED"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"


class DurabilityClass(str, Enum):
    VOLATILE = "VOLATILE"
    SESSION = "SESSION"
    DURABLE = "DURABLE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class TransferCostEvidence:
    state: TransferCostState
    source_tier: ResourceTier
    target_tier: ResourceTier
    bytes_per_second: int | None
    evidence_ref: str
    m08_evidence_ref: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.state, TransferCostState) or not isinstance(self.source_tier, ResourceTier) or not isinstance(self.target_tier, ResourceTier):
            raise ValueError("transfer cost must carry explicit state and resource tiers")
        object.__setattr__(self, "evidence_ref", require_id(self.evidence_ref, "evidence_ref"))
        if self.m08_evidence_ref is not None:
            object.__setattr__(self, "m08_evidence_ref", require_id(self.m08_evidence_ref, "m08_evidence_ref"))
            if self.m08_evidence_ref.split(":", 1)[0] != "M08":
                raise ValueError("empirical transfer cost must reference M08 evidence")
        if self.state is TransferCostState.UNKNOWN and self.bytes_per_second is not None:
            raise ValueError("unknown transfer cost cannot carry a numeric throughput")
        if self.bytes_per_second is not None and (type(self.bytes_per_second) is not int or not 1 <= self.bytes_per_second <= (1 << 63) - 1):
            raise ValueError("transfer throughput must be a positive bounded integer or unknown")
        if self.state is TransferCostState.MEASURED and (self.bytes_per_second is None or self.m08_evidence_ref is None):
            raise ValueError("measured transfer cost requires throughput and M08 evidence")
        if self.state is TransferCostState.ESTIMATED and self.bytes_per_second is None:
            raise ValueError("estimated transfer cost requires an explicit estimate")


@dataclass(frozen=True)
class SpillTargetCapability:
    capability_ref: str
    authority_ref: str
    resource_key: str
    tier: ResourceTier
    available_bytes: int | None
    write_allowed: bool
    readback_verification: bool
    permission_ref: str
    identity: ResourceIdentity
    encryption_ref: str | None = None
    endurance_evidence_ref: str | None = None
    deletion_authorized: bool = False
    durability_class: DurabilityClass = DurabilityClass.UNKNOWN
    latency_evidence_ref: str | None = None
    maximum_object_bytes: int | None = None
    read_allowed: bool = True

    def __post_init__(self) -> None:
        for field in ("capability_ref", "authority_ref", "resource_key", "permission_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.identity) is not ResourceIdentity or self.identity.tier is not self.tier or self.identity.stable_key != self.resource_key:
            raise ValueError("spill capability must bind its exact stable resource identity and tier")
        if self.authority_ref.split(":", 1)[0] != "M55":
            raise ValueError("spill target capability must be referenced to M55 authority")
        if self.tier not in {ResourceTier.RAM, ResourceTier.SPILL}:
            raise ValueError("spill target must be RAM or spill tier")
        if self.available_bytes is not None and (type(self.available_bytes) is not int or self.available_bytes < 0):
            raise ValueError("available_bytes must be non-negative or unknown")
        if self.encryption_ref is not None:
            object.__setattr__(self, "encryption_ref", require_id(self.encryption_ref, "encryption_ref"))
        if self.endurance_evidence_ref is not None:
            object.__setattr__(self, "endurance_evidence_ref", require_id(self.endurance_evidence_ref, "endurance_evidence_ref"))
        if self.deletion_authorized:
            raise ValueError("M09 cannot acquire physical deletion authority")
        if not isinstance(self.durability_class, DurabilityClass):
            raise ValueError("spill durability class must be explicit")
        if self.latency_evidence_ref is not None:
            object.__setattr__(self, "latency_evidence_ref", require_id(self.latency_evidence_ref, "latency_evidence_ref"))
        if self.maximum_object_bytes is not None and (type(self.maximum_object_bytes) is not int or self.maximum_object_bytes < 1):
            raise ValueError("maximum object size must be positive or unknown")
        if type(self.read_allowed) is not bool:
            raise ValueError("spill read permission must be explicit")
        if any(type(value) is not bool for value in (self.write_allowed, self.readback_verification)):
            raise ValueError("spill write/readback capability must be explicit")
        if self.tier is ResourceTier.SPILL:
            if self.permission_ref.split(":", 1)[0] != "M53":
                raise ValueError("spill permissions remain owned by M53")
            if self.encryption_ref is None or self.encryption_ref.split(":", 1)[0] != "M54":
                raise ValueError("spill encryption classification remains owned by M54")
            if self.durability_class is DurabilityClass.UNKNOWN:
                raise ValueError("spill durability must be explicit or the target is unavailable")
            if self.latency_evidence_ref is None:
                raise ValueError("M55 spill latency evidence must be explicit, even when unavailable")
            if self.durability_class is DurabilityClass.DURABLE and self.endurance_evidence_ref is None:
                raise ValueError("durable spill target requires M55 endurance evidence")

    @property
    def eligible(self) -> bool:
        return self.available_bytes is not None and self.write_allowed and self.read_allowed and self.readback_verification


@dataclass(frozen=True)
class TransferSegment:
    segment_id: str
    offset_bytes: int
    length_bytes: int
    digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "segment_id", require_id(self.segment_id, "segment_id"))
        if type(self.offset_bytes) is not int or self.offset_bytes < 0 or type(self.length_bytes) is not int or self.length_bytes < 1:
            raise ValueError("segment offset/length is invalid")
        if len(self.digest) != 64 or any(char not in "0123456789abcdef" for char in self.digest):
            raise ValueError("segment digest must be lowercase SHA-256")


@dataclass(frozen=True)
class TransferRequest:
    transfer_id: str
    idempotency_key: str
    source_resource_key: str
    target: SpillTargetCapability
    byte_count: int
    expected_digest: str
    dirty_state: DirtyState
    writeback_ref: str | None
    reconstruction_ref: str | None
    segments: tuple[TransferSegment, ...]
    requested_at_ms: int
    authorization_ref: str
    source_tier: ResourceTier
    source_identity: ResourceIdentity
    artifact_ref: str
    artifact_revision: str
    source_lease_ref: str
    source_residency_ref: str
    deadline_ms: int
    clock_ref: str
    supports_resume: bool
    maximum_retries: int
    evidence_origin: EvidenceOrigin
    cost: TransferCostEvidence
    composite_group_ref: str | None = None
    mutation_context: MutationContext | None = None

    def __post_init__(self) -> None:
        for field in ("transfer_id", "idempotency_key", "source_resource_key", "authorization_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        for field in ("artifact_ref", "artifact_revision", "source_lease_ref", "source_residency_ref", "clock_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if not isinstance(self.source_tier, ResourceTier) or type(self.source_identity) is not ResourceIdentity or self.source_identity.tier is not self.source_tier or self.source_identity.stable_key != self.source_resource_key:
            raise ValueError("source movement must bind its exact stable identity and tier")
        if type(self.deadline_ms) is not int or self.deadline_ms <= self.requested_at_ms:
            raise ValueError("transfer deadline must follow request time")
        if type(self.supports_resume) is not bool or type(self.maximum_retries) is not int or not 0 <= self.maximum_retries <= 16:
            raise ValueError("resume support and retry limit must be explicit and bounded")
        if not isinstance(self.evidence_origin, EvidenceOrigin):
            raise ValueError("transfer evidence origin must be explicit")
        if type(self.cost) is not TransferCostEvidence:
            raise ValueError("transfer cost evidence must use the exact M09 record")
        if self.cost.source_tier is not self.source_tier or self.cost.target_tier is not self.target.tier:
            raise ValueError("transfer cost evidence must match exact source and target tiers")
        if self.composite_group_ref is not None:
            object.__setattr__(self, "composite_group_ref", require_id(self.composite_group_ref, "composite_group_ref"))
        context = self.mutation_context
        if context is None:
            context = MutationContext(MutationActorKind.INTERACTIVE, "M09:transfer-client", self.authorization_ref, self.transfer_id, self.idempotency_key)
            object.__setattr__(self, "mutation_context", context)
        if type(context) is not MutationContext or context.authorization_ref != self.authorization_ref or context.idempotency_key != self.idempotency_key:
            raise ValueError("transfer mutation context must bind its exact authorization and idempotency identity")
        if type(self.byte_count) is not int or not 1 <= self.byte_count <= (1 << 63) - 1:
            raise ValueError("byte_count must be a positive bounded quantity")
        if len(self.expected_digest) != 64 or any(char not in "0123456789abcdef" for char in self.expected_digest):
            raise ValueError("expected_digest must be lowercase SHA-256")
        if not isinstance(self.dirty_state, DirtyState):
            raise ValueError("dirty_state must be explicit")
        if self.writeback_ref is not None:
            object.__setattr__(self, "writeback_ref", require_id(self.writeback_ref, "writeback_ref"))
        if self.reconstruction_ref is not None:
            object.__setattr__(self, "reconstruction_ref", require_id(self.reconstruction_ref, "reconstruction_ref"))
        raw_segments = tuple(self.segments)
        if len(raw_segments) > 4_096 or any(type(item) is not TransferSegment for item in raw_segments):
            raise ValueError("segments must be exact TransferSegment values")
        segments = tuple(sorted(raw_segments, key=lambda item: item.offset_bytes))
        if segments:
            if len({item.segment_id for item in segments}) != len(segments):
                raise ValueError("segment identities must be unique")
            if segments[0].offset_bytes != 0 or any(left.offset_bytes + left.length_bytes != right.offset_bytes for left, right in zip(segments, segments[1:])):
                raise ValueError("segments must form a gap-free, non-overlapping prefix")
            if segments[-1].offset_bytes + segments[-1].length_bytes != self.byte_count:
                raise ValueError("segments must cover the exact transfer byte count")
        if type(self.requested_at_ms) is not int or self.requested_at_ms < 0:
            raise ValueError("requested_at_ms must be non-negative")
        if self.dirty_state is DirtyState.DIRTY and self.writeback_ref is None:
            raise ValueError("dirty material requires a writeback proof reference")
        if self.dirty_state is DirtyState.RECONSTRUCTIBLE and self.reconstruction_ref is None:
            raise ValueError("reconstructible material requires an exact reconstruction proof reference")
        if self.dirty_state is DirtyState.UNKNOWN:
            raise ValueError("unknown dirty state fails closed")
        object.__setattr__(self, "segments", segments)


@dataclass(frozen=True)
class OffloadTransaction:
    request: TransferRequest
    state: TransferState
    epoch: int
    created_at_ms: int
    updated_at_ms: int
    verified_digest: str | None = None
    failure_ref: str | None = None
    checkpoint_ref: str | None = None
    completed_bytes: int | None = None
    retry_count: int = 0
    observed_segment_digests: tuple[tuple[str, str], ...] = ()
    partial_digest: str | None = None

    def __post_init__(self) -> None:
        if type(self.request) is not TransferRequest or not isinstance(self.state, TransferState) or type(self.epoch) is not int or self.epoch < 1:
            raise ValueError("offload transaction state and epoch must be explicit")
        if any(type(value) is not int or value < 0 for value in (self.created_at_ms, self.updated_at_ms, self.retry_count)):
            raise ValueError("offload transaction counters and times must be non-negative")
        if self.updated_at_ms < self.created_at_ms or self.retry_count > 16:
            raise ValueError("offload transaction chronology/retry bound is invalid")
        if self.completed_bytes is not None and (type(self.completed_bytes) is not int or not 0 <= self.completed_bytes <= self.request.byte_count):
            raise ValueError("completed transfer bytes must be bounded by the request")
        for field in ("verified_digest", "partial_digest"):
            value = getattr(self, field)
            if value is not None and (type(value) is not str or len(value) != 64 or any(char not in "0123456789abcdef" for char in value)):
                raise ValueError(f"{field} must be a lowercase SHA-256 digest")
        for field in ("failure_ref", "checkpoint_ref"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_id(value, field))
        raw_segment_digests = tuple(self.observed_segment_digests)
        if len(raw_segment_digests) > 4_096 or any(type(item) is not tuple or len(item) != 2 or type(item[0]) is not str or type(item[1]) is not str or len(item[1]) != 64 or any(char not in "0123456789abcdef" for char in item[1]) for item in raw_segment_digests):
            raise ValueError("observed transfer segments require exact SHA-256 evidence")
        segment_digests = tuple(sorted(raw_segment_digests))
        if len({item[0] for item in segment_digests}) != len(segment_digests):
            raise ValueError("observed transfer segments must have unique identities")
        object.__setattr__(self, "observed_segment_digests", segment_digests)
        if self.state is TransferState.PARTIAL:
            if self.completed_bytes is None or not 0 < self.completed_bytes < self.request.byte_count or self.checkpoint_ref is None or self.partial_digest is None:
                raise ValueError("partial transfer requires bounded byte, digest and checkpoint evidence")
            if self.request.segments:
                expected = {item.segment_id: item for item in self.request.segments}
                selected = tuple(sorted((expected[item[0]] for item in segment_digests if item[0] in expected), key=lambda item: item.offset_bytes))
                if len(selected) != len(segment_digests) or tuple(selected) != self.request.segments[:len(selected)] or sum(item.length_bytes for item in selected) != self.completed_bytes:
                    raise ValueError("partial segment record must be a verified contiguous request prefix")
            elif segment_digests:
                raise ValueError("non-segmented partial transfer cannot carry segment evidence")
        if self.state in {TransferState.VERIFIED, TransferState.COMMITTED}:
            if self.verified_digest != self.request.expected_digest or self.completed_bytes != self.request.byte_count:
                raise ValueError("verified transfer requires the exact complete artifact digest and byte count")
        if self.state in {TransferState.ABORTED, TransferState.QUARANTINED} and self.failure_ref is None:
            raise ValueError("aborted/quarantined transfer requires an explicit reason reference")


@dataclass(frozen=True)
class MobilityOutcome:
    status: str
    transfer: OffloadTransaction | None
    reason: str


@dataclass(frozen=True)
class SourceReleaseAuthorization:
    transfer_id: str
    transfer_epoch: int
    source_resource_key: str
    target_resource_key: str
    verified_digest: str
    destination_snapshot_digest: str
    authorization_ref: str
    artifact_ref: str
    artifact_revision: str
    source_lease_ref: str
    source_residency_ref: str

    def __post_init__(self) -> None:
        for field in ("transfer_id", "source_resource_key", "target_resource_key", "authorization_ref", "artifact_ref", "artifact_revision", "source_lease_ref", "source_residency_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.transfer_epoch) is not int or self.transfer_epoch < 1:
            raise ValueError("source-release authorization requires a positive transfer epoch")
        for field in ("verified_digest", "destination_snapshot_digest"):
            value = getattr(self, field)
            if type(value) is not str or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
                raise ValueError(f"{field} must be a lowercase SHA-256 digest")


@dataclass(frozen=True)
class CompositeMemberOutcome:
    transfer_id: str
    status: str
    reason: str
    transfer: OffloadTransaction | None


@dataclass(frozen=True)
class CompositeMobilityOutcome:
    group_ref: str
    atomic_required: bool
    members: tuple[CompositeMemberOutcome, ...]

    @property
    def complete(self) -> bool:
        return bool(self.members) and all(item.transfer is not None and item.status in {"PREPARED", "IDEMPOTENT_REPLAY"} for item in self.members)


class MobilityLedger:
    """Tracks transfer claims only. Data copy, spill I/O and deletion belong to external ports."""

    def __init__(self, *, limits: M09Limits = DEFAULT_LIMITS, max_active_bytes: int = 1 << 40, max_active_per_target: int = 16) -> None:
        if type(max_active_bytes) is not int or not 1 <= max_active_bytes <= (1 << 63) - 1:
            raise ValueError("active transfer byte ceiling must be finite")
        if type(max_active_per_target) is not int or not 1 <= max_active_per_target <= 64:
            raise ValueError("per-target transfer concurrency must be finite")
        self._limits = limits
        self._max_active_bytes = max_active_bytes
        self._max_active_per_target = max_active_per_target
        self._lock = RLock()
        self._transfers: dict[str, OffloadTransaction] = {}
        self._journal: list[OffloadTransaction] = []
        self._idempotency: dict[str, str] = {}
        self._quarantined_targets: set[str] = set()
        self._operation_replays: dict[tuple[str, str, int], tuple[str, OffloadTransaction]] = {}

    def prepare(self, request: TransferRequest, *, now_ms: int, destination_snapshot: ResourceSnapshot) -> MobilityOutcome:
        if type(request) is not TransferRequest:
            raise ValueError("mobility preparation requires an exact transfer request")
        with self._lock:
            existing_id = self._idempotency.get(request.idempotency_key)
            if existing_id is not None:
                existing = self._transfers[existing_id]
                if existing.request == request:
                    return MobilityOutcome("IDEMPOTENT_REPLAY", existing, "existing transfer identity")
                raise ValueError("transfer idempotency key binds different semantics")
            if request.transfer_id in self._transfers:
                raise ValueError("transfer identity cannot be reused")
            self._limits.require("max_transfers", len(self._transfers) + 1)
            problem = self._prepare_problem(request, destination_snapshot, now_ms=now_ms, projected_bytes=0, projected_target_count=0, projected_total_bytes=0)
            if problem is not None:
                return MobilityOutcome(problem[0], None, problem[1])
            transaction = OffloadTransaction(request, TransferState.PREPARED, 1, now_ms, now_ms)
            self._record(transaction)
            self._idempotency[request.idempotency_key] = request.transfer_id
            return MobilityOutcome("PREPARED", transaction, "bounded movement intent admitted against fresh destination truth")

    def prepare_composite(
        self,
        members: tuple[tuple[TransferRequest, ResourceSnapshot], ...],
        *,
        group_ref: str,
        atomic_required: bool,
        now_ms: int,
    ) -> CompositeMobilityOutcome:
        group_ref = require_id(group_ref, "group_ref")
        if type(atomic_required) is not bool or not members or len(members) > 64:
            raise ValueError("composite transfer requires a bounded member set and explicit atomicity")
        if any(type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not TransferRequest or type(pair[1]) is not ResourceSnapshot for pair in members):
            raise ValueError("composite members require exact request/snapshot pairs")
        requests = tuple(pair[0] for pair in members)
        if len({item.transfer_id for item in requests}) != len(requests) or len({item.idempotency_key for item in requests}) != len(requests):
            raise ValueError("composite transfer identities and idempotency keys must be unique")
        if any(item.composite_group_ref != group_ref for item in requests):
            raise ValueError("each composite member must bind the exact group identity")
        with self._lock:
            known_members = [self._transfers.get(request.transfer_id) for request in requests]
            if any(current is not None or request.idempotency_key in self._idempotency for current, request in zip(known_members, requests)):
                if all(current is not None and current.request == request for current, request in zip(known_members, requests)):
                    return CompositeMobilityOutcome(group_ref, atomic_required, tuple(
                        CompositeMemberOutcome(request.transfer_id, "IDEMPOTENT_REPLAY", "existing composite member identity", current)
                        for request, current in zip(requests, known_members)
                    ))
                raise ValueError("composite transfer replay must match every exact member identity")
            self._limits.require("max_transfers", len(self._transfers) + len(requests))
            projected_bytes: dict[str, int] = {}
            projected_count: dict[str, int] = {}
            projected_total_bytes = 0
            problems: list[tuple[str, str] | None] = []
            for request, snapshot in members:
                problem = self._prepare_problem(
                    request, snapshot, now_ms=now_ms,
                    projected_bytes=projected_bytes.get(request.target.resource_key, 0),
                    projected_target_count=projected_count.get(request.target.resource_key, 0),
                    projected_total_bytes=projected_total_bytes,
                )
                problems.append(problem)
                if problem is None:
                    projected_bytes[request.target.resource_key] = projected_bytes.get(request.target.resource_key, 0) + request.byte_count
                    projected_count[request.target.resource_key] = projected_count.get(request.target.resource_key, 0) + 1
                    projected_total_bytes += request.byte_count
            if atomic_required and any(item is not None for item in problems):
                rejected_results = tuple(
                    CompositeMemberOutcome(
                        request.transfer_id,
                        problem[0] if problem is not None else "ABORTED_ATOMIC_MEMBER_FAILURE",
                        problem[1] if problem is not None else "atomic composite was not admitted because another member failed",
                        None,
                    )
                    for request, problem in zip(requests, problems)
                )
                return CompositeMobilityOutcome(group_ref, True, rejected_results)
            successful = sum(problem is None for problem in problems)
            self._limits.require("max_events", len(self._journal) + successful)
            results: list[CompositeMemberOutcome] = []
            for (request, _snapshot), problem in zip(members, problems):
                if problem is not None:
                    results.append(CompositeMemberOutcome(request.transfer_id, problem[0], problem[1], None))
                    continue
                transaction = OffloadTransaction(request, TransferState.PREPARED, 1, now_ms, now_ms)
                self._record(transaction)
                self._idempotency[request.idempotency_key] = request.transfer_id
                results.append(CompositeMemberOutcome(request.transfer_id, "PREPARED", "composite member admitted", transaction))
            return CompositeMobilityOutcome(group_ref, atomic_required, tuple(results))

    def _prepare_problem(self, request: TransferRequest, destination_snapshot: ResourceSnapshot, *, now_ms: int, projected_bytes: int, projected_target_count: int, projected_total_bytes: int) -> tuple[str, str] | None:
        target = request.target
        if type(now_ms) is not int or now_ms < request.requested_at_ms:
            return "UNAVAILABLE", "monotonic request time is invalid"
        if now_ms > request.deadline_ms:
            return "EXPIRED", "transfer intent deadline has passed"
        if target.resource_key in self._quarantined_targets:
            return "REQUIRE_REPLAN", "destination is quarantined"
        if not target.eligible:
            return "UNAVAILABLE", "target lacks known capacity, read/write permission, durability or readback verification"
        if target.available_bytes is None:
            return "UNAVAILABLE", "target capacity is unknown"
        if target.maximum_object_bytes is not None and request.byte_count > target.maximum_object_bytes:
            return "UNAVAILABLE", "object exceeds the declared target maximum"
        if target.available_bytes < projected_bytes + request.byte_count:
            return "REQUIRE_REPLAN", "destination capability capacity is insufficient"
        if target.resource_key == request.source_resource_key:
            return "UNAVAILABLE", "source and destination resource identities must differ"
        if type(destination_snapshot) is not ResourceSnapshot or destination_snapshot.identity.stable_key != target.resource_key:
            return "UNAVAILABLE", "exact destination resource snapshot is required"
        if destination_snapshot.evidence_origin is not request.evidence_origin:
            return "UNAVAILABLE", "transfer and destination evidence origins do not match"
        if not destination_snapshot.is_fresh(now_ms):
            return "UNAVAILABLE", "fresh observed destination truth is required"
        try:
            available = destination_snapshot.capacity.available_bytes()
        except ValueError:
            return "UNAVAILABLE", "unknown destination capacity cannot authorize movement"
        if available < projected_bytes + request.byte_count:
            return "REQUIRE_REPLAN", "destination capacity or protected headroom is insufficient"
        active = (TransferState.PREPARED, TransferState.COPYING, TransferState.PARTIAL, TransferState.VERIFIED)
        existing_bytes = sum(item.request.byte_count for item in self._transfers.values() if item.state in active)
        target_count = sum(1 for item in self._transfers.values() if item.request.target.resource_key == target.resource_key and item.state in active)
        if existing_bytes + projected_total_bytes + request.byte_count > self._max_active_bytes:
            return "REQUIRE_REPLAN", "global active transfer byte bound would be exceeded"
        if target_count + projected_target_count >= self._max_active_per_target:
            return "REQUIRE_REPLAN", "per-target transfer concurrency bound would be exceeded"
        return None

    def begin_copy(self, transfer_id: str, *, expected_epoch: int, now_ms: int) -> OffloadTransaction:
        with self._lock:
            current = self._require(transfer_id, TransferState.PREPARED, expected_epoch)
            if type(now_ms) is not int or now_ms < current.updated_at_ms or now_ms > current.request.deadline_ms:
                raise ValueError("copy start is outside the monotonic transfer deadline")
            updated = OffloadTransaction(
                current.request, TransferState.COPYING, current.epoch + 1,
                current.created_at_ms, now_ms, checkpoint_ref=current.checkpoint_ref,
                completed_bytes=current.completed_bytes, retry_count=current.retry_count,
                observed_segment_digests=current.observed_segment_digests,
                partial_digest=current.partial_digest,
            )
            self._record(updated)
            return updated

    def verify_destination(self, transfer_id: str, *, expected_epoch: int, observed_digest: str, copy_complete: bool, now_ms: int, completed_bytes: int | None = None, checkpoint_ref: str | None = None, observed_segment_digests: tuple[tuple[str, str], ...] = ()) -> OffloadTransaction:
        with self._lock:
            current = self._require(transfer_id, TransferState.COPYING, expected_epoch)
            if type(copy_complete) is not bool or type(now_ms) is not int or now_ms < current.updated_at_ms or now_ms > current.request.deadline_ms:
                raise ValueError("copy verification time or completeness state is invalid")
            if not copy_complete:
                if completed_bytes is not None and (type(completed_bytes) is not int or not 0 <= completed_bytes < current.request.byte_count):
                    raise ValueError("partial transfer byte count must be less than the whole artifact")
                if checkpoint_ref is not None:
                    checkpoint_ref = require_id(checkpoint_ref, "checkpoint_ref")
                partial_segments = tuple(sorted(observed_segment_digests))
                if current.request.segments:
                    expected_segments = {item.segment_id: item for item in current.request.segments}
                    if any(segment_id not in expected_segments or expected_segments[segment_id].digest != segment_digest for segment_id, segment_digest in partial_segments):
                        raise ValueError("partial segment evidence must match exact requested segment digests")
                    selected = tuple(sorted((expected_segments[segment_id] for segment_id, _ in partial_segments), key=lambda item: item.offset_bytes))
                    if tuple(selected) != current.request.segments[:len(selected)]:
                        raise ValueError("partial segment evidence must be a contiguous requested prefix")
                    previous_segments = set(current.observed_segment_digests)
                    if not previous_segments.issubset(set(partial_segments)):
                        raise ValueError("resumed partial transfer cannot discard prior verified segment evidence")
                    derived_completed_bytes = sum(item.length_bytes for item in selected)
                    if completed_bytes is not None and completed_bytes != derived_completed_bytes:
                        raise ValueError("partial segment lengths must equal the reported completed byte count")
                    if completed_bytes is None:
                        completed_bytes = derived_completed_bytes
                elif partial_segments:
                    raise ValueError("segment evidence cannot be attached to a non-segmented transfer")
                if type(observed_digest) is not str or len(observed_digest) != 64 or any(char not in "0123456789abcdef" for char in observed_digest):
                    raise ValueError("partial transfer digest must be lowercase SHA-256")
                if checkpoint_ref is None:
                    raise ValueError("partial transfer requires an exact checkpoint reference")
                if current.completed_bytes is not None and completed_bytes is not None and completed_bytes < current.completed_bytes:
                    raise ValueError("partial transfer progress cannot move backwards")
                partial = OffloadTransaction(
                    current.request, TransferState.PARTIAL, current.epoch + 1,
                    current.created_at_ms, now_ms,
                    checkpoint_ref=checkpoint_ref, completed_bytes=completed_bytes,
                    retry_count=current.retry_count, observed_segment_digests=partial_segments,
                    partial_digest=observed_digest,
                )
                self._record(partial)
                return partial
            if type(observed_digest) is not str or len(observed_digest) != 64 or any(char not in "0123456789abcdef" for char in observed_digest):
                raise ValueError("observed transfer digest must be lowercase SHA-256")
            length_matches = completed_bytes in {None, current.request.byte_count}
            if current.request.segments:
                received = tuple(sorted(observed_segment_digests))
                expected = tuple(sorted((item.segment_id, item.digest) for item in current.request.segments))
                segments_match = received == expected
            else:
                segments_match = not observed_segment_digests
            if not length_matches or not segments_match or observed_digest != current.request.expected_digest:
                updated = OffloadTransaction(
                    current.request, TransferState.QUARANTINED, current.epoch + 1,
                    current.created_at_ms, now_ms, observed_digest,
                    "transfer-integrity-mismatch", current.checkpoint_ref,
                    completed_bytes=completed_bytes,
                    retry_count=current.retry_count,
                    observed_segment_digests=tuple(sorted(observed_segment_digests)),
                )
                self._quarantined_targets.add(current.request.target.resource_key)
                self._record(updated)
                return updated
            updated = OffloadTransaction(current.request, TransferState.VERIFIED, current.epoch + 1, current.created_at_ms, now_ms, observed_digest, completed_bytes=current.request.byte_count, retry_count=current.retry_count, observed_segment_digests=tuple(sorted(observed_segment_digests)))
            self._record(updated)
            return updated

    def commit_handoff(self, transfer_id: str, *, expected_epoch: int, destination_snapshot: ResourceSnapshot, now_ms: int, authorization_ref: str) -> tuple[OffloadTransaction, SourceReleaseAuthorization]:
        authorization_ref = require_id(authorization_ref, "authorization_ref")
        with self._lock:
            current = self._require(transfer_id, TransferState.VERIFIED, expected_epoch)
            if type(now_ms) is not int or now_ms < current.updated_at_ms or now_ms > current.request.deadline_ms:
                raise ValueError("handoff is outside the monotonic transfer deadline")
            if type(destination_snapshot) is not ResourceSnapshot or destination_snapshot.identity.stable_key != current.request.target.resource_key:
                raise ValueError("verified transfer requires a matching destination snapshot")
            if current.request.evidence_origin is not EvidenceOrigin.REPORTED_OBSERVATION or not destination_snapshot.production_transfer_authorized(now_ms) or destination_snapshot.capacity.resident_bytes is None or destination_snapshot.capacity.resident_bytes < current.request.byte_count:
                raise ValueError("fresh destination residency truth is required before source release")
            if destination_snapshot.confidence.value in {"CONFLICTED", "QUARANTINED", "UNKNOWN", "UNSUPPORTED", "STALE"}:
                raise ValueError("unsafe destination truth cannot complete two-phase handoff")
            updated = OffloadTransaction(current.request, TransferState.COMMITTED, current.epoch + 1, current.created_at_ms, now_ms, current.verified_digest, completed_bytes=current.request.byte_count, retry_count=current.retry_count, observed_segment_digests=current.observed_segment_digests)
            receipt = SourceReleaseAuthorization(
                transfer_id, updated.epoch, current.request.source_resource_key,
                current.request.target.resource_key, current.verified_digest or "",
                destination_snapshot.digest, authorization_ref, current.request.artifact_ref,
                current.request.artifact_revision, current.request.source_lease_ref,
                current.request.source_residency_ref,
            )
            verify_source_release_authorization(receipt, updated, destination_snapshot, now_ms=now_ms)
            self._record(updated)
            return updated, receipt

    def cancel(self, transfer_id: str, *, expected_epoch: int, now_ms: int, reason_ref: str, checkpoint_ref: str | None = None) -> OffloadTransaction:
        reason_ref = require_id(reason_ref, "reason_ref")
        if checkpoint_ref is not None:
            checkpoint_ref = require_id(checkpoint_ref, "checkpoint_ref")
        with self._lock:
            replay_key = (transfer_id, "cancel", expected_epoch)
            replay_digest = content_digest({"now_ms": now_ms, "reason_ref": reason_ref, "checkpoint_ref": checkpoint_ref})
            replay = self._operation_replays.get(replay_key)
            if replay is not None:
                if replay[0] != replay_digest:
                    raise ValueError("conflicting cancellation replay semantics")
                return replay[1]
            current = self._transfers.get(transfer_id)
            if current is None or current.epoch != expected_epoch or current.state not in {TransferState.PREPARED, TransferState.COPYING}:
                raise ValueError("transfer is not cancellable at the supplied epoch")
            if type(now_ms) is not int or now_ms < current.updated_at_ms:
                raise ValueError("cancellation time must be monotonic")
            updated = OffloadTransaction(current.request, TransferState.ABORTED, current.epoch + 1, current.created_at_ms, now_ms, failure_ref=reason_ref, checkpoint_ref=checkpoint_ref or current.checkpoint_ref, completed_bytes=current.completed_bytes, retry_count=current.retry_count, observed_segment_digests=current.observed_segment_digests, partial_digest=current.partial_digest)
            self._record(updated)
            self._operation_replays[replay_key] = (replay_digest, updated)
            return updated

    def resume(self, transfer_id: str, *, expected_epoch: int, checkpoint_ref: str, source_digest: str, now_ms: int) -> OffloadTransaction:
        checkpoint_ref = require_id(checkpoint_ref, "checkpoint_ref")
        with self._lock:
            replay_key = (transfer_id, "resume", expected_epoch)
            replay_digest = content_digest({"checkpoint_ref": checkpoint_ref, "source_digest": source_digest, "now_ms": now_ms})
            replay = self._operation_replays.get(replay_key)
            if replay is not None:
                if replay[0] != replay_digest:
                    raise ValueError("conflicting resume replay semantics")
                return replay[1]
            current = self._transfers.get(transfer_id)
            if current is None or current.state not in {TransferState.ABORTED, TransferState.PARTIAL} or current.epoch != expected_epoch:
                raise ValueError("only the exact aborted or partial transfer epoch can resume")
            if not current.request.supports_resume or current.retry_count >= current.request.maximum_retries:
                raise ValueError("transfer resume is unsupported or its bounded retry count is exhausted")
            if current.checkpoint_ref != checkpoint_ref or source_digest != current.request.expected_digest:
                raise ValueError("resume source/checkpoint integrity does not match the transfer")
            if type(now_ms) is not int or now_ms < current.updated_at_ms or now_ms > current.request.deadline_ms:
                raise ValueError("resume is outside the monotonic transfer deadline")
            updated = OffloadTransaction(current.request, TransferState.PREPARED, current.epoch + 1, current.created_at_ms, now_ms, checkpoint_ref=checkpoint_ref, completed_bytes=current.completed_bytes, retry_count=current.retry_count + 1, observed_segment_digests=current.observed_segment_digests, partial_digest=current.partial_digest)
            self._record(updated)
            self._operation_replays[replay_key] = (replay_digest, updated)
            return updated

    def transaction(self, transfer_id: str) -> OffloadTransaction | None:
        with self._lock:
            return self._transfers.get(transfer_id)

    def history(self, transfer_id: str | None = None) -> tuple[OffloadTransaction, ...]:
        with self._lock:
            return tuple(item for item in self._journal if transfer_id is None or item.request.transfer_id == transfer_id)

    def _record(self, transaction: OffloadTransaction) -> None:
        self._limits.require("max_events", len(self._journal) + 1)
        self._journal.append(transaction)
        self._transfers[transaction.request.transfer_id] = transaction

    def _require(self, transfer_id: str, state: TransferState, epoch: int) -> OffloadTransaction:
        current = self._transfers.get(transfer_id)
        if current is None or current.state is not state or current.epoch != epoch:
            raise ValueError("transfer state or epoch is stale")
        return current


def verify_source_release_authorization(
    authorization: SourceReleaseAuthorization,
    transaction: OffloadTransaction,
    destination_snapshot: ResourceSnapshot,
    *,
    now_ms: int,
) -> bool:
    if type(authorization) is not SourceReleaseAuthorization or type(transaction) is not OffloadTransaction or type(destination_snapshot) is not ResourceSnapshot:
        raise ValueError("source release verification requires exact evidence records")
    request = transaction.request
    if (
        transaction.state is not TransferState.COMMITTED
        or authorization.transfer_id != request.transfer_id
        or authorization.transfer_epoch != transaction.epoch
        or authorization.source_resource_key != request.source_resource_key
        or authorization.target_resource_key != request.target.resource_key
        or authorization.verified_digest != request.expected_digest
        or authorization.verified_digest != transaction.verified_digest
        or authorization.destination_snapshot_digest != destination_snapshot.digest
        or authorization.artifact_ref != request.artifact_ref
        or authorization.artifact_revision != request.artifact_revision
        or authorization.source_lease_ref != request.source_lease_ref
        or authorization.source_residency_ref != request.source_residency_ref
        or request.evidence_origin is not EvidenceOrigin.REPORTED_OBSERVATION
        or destination_snapshot.identity.stable_key != request.target.resource_key
        or not destination_snapshot.production_transfer_authorized(now_ms)
        or destination_snapshot.capacity.resident_bytes is None
        or destination_snapshot.capacity.resident_bytes < request.byte_count
    ):
        raise ValueError("source release requires the exact committed transfer and fresh reported destination residency")
    return True


@dataclass(frozen=True)
class LocalityHint:
    hint_id: str
    resource_key: str
    tier: ResourceTier
    locality_class: str
    evidence_ref: str
    valid_until_ms: int

    def __post_init__(self) -> None:
        for field in ("hint_id", "resource_key", "locality_class", "evidence_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if not isinstance(self.tier, ResourceTier) or type(self.valid_until_ms) is not int or self.valid_until_ms < 0:
            raise ValueError("locality hint tier and expiry must be explicit")

    def is_current(self, *, now_ms: int) -> bool:
        return type(now_ms) is int and 0 <= now_ms <= self.valid_until_ms


class ContentionState(str, Enum):
    CLEAR = "CLEAR"
    CONTENDED = "CONTENDED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class BandwidthContentionEvidence:
    resource_key: str
    tier: ResourceTier
    state: ContentionState
    contention_basis_points: int | None
    evidence_ref: str
    valid_until_ms: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "resource_key", require_id(self.resource_key, "resource_key"))
        object.__setattr__(self, "evidence_ref", require_id(self.evidence_ref, "evidence_ref"))
        if not isinstance(self.tier, ResourceTier) or not isinstance(self.state, ContentionState):
            raise ValueError("bandwidth contention scope and state must be explicit")
        if type(self.valid_until_ms) is not int or self.valid_until_ms < 0:
            raise ValueError("contention validity must have a bounded timestamp")
        value = self.contention_basis_points
        if self.state is ContentionState.UNKNOWN and value is not None:
            raise ValueError("unknown contention cannot carry a numeric measurement")
        if self.state is not ContentionState.UNKNOWN and (type(value) is not int or not 0 <= value <= 10_000):
            raise ValueError("known contention must be basis points from 0 through 10000")


class ReferenceActivity(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SpillGarbageCandidate:
    candidate_id: str
    artifact_ref: str
    artifact_revision: str
    resource_key: str
    transfer_id: str
    source_lease_ref: str
    residency_ref: str
    lease_state: ReferenceActivity
    residency_state: ReferenceActivity
    causal_evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in ("candidate_id", "artifact_ref", "artifact_revision", "resource_key", "transfer_id", "source_lease_ref", "residency_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if not isinstance(self.lease_state, ReferenceActivity) or not isinstance(self.residency_state, ReferenceActivity):
            raise ValueError("garbage reference activity must be explicit")
        refs = tuple(sorted(set(require_id(item, "causal_evidence_ref") for item in self.causal_evidence_refs)))
        if not refs:
            raise ValueError("spill garbage candidate requires causal evidence")
        object.__setattr__(self, "causal_evidence_refs", refs)


@dataclass(frozen=True)
class SpillGarbageEligibility:
    candidate_id: str
    eligible_for_m55_review: bool
    physical_deletion_permitted: bool
    reason: str
    evidence_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_id", require_id(self.candidate_id, "candidate_id"))
        if self.physical_deletion_permitted:
            raise ValueError("M09 cannot authorize physical spill deletion")
        if not self.reason or len(self.evidence_digest) != 64:
            raise ValueError("garbage eligibility requires rationale and evidence digest")


def evaluate_spill_garbage(candidate: SpillGarbageCandidate, *, committed_transfer: OffloadTransaction | None) -> SpillGarbageEligibility:
    if type(candidate) is not SpillGarbageCandidate:
        raise ValueError("spill garbage evaluation requires an exact candidate")
    transfer_matches = (
        type(committed_transfer) is OffloadTransaction
        and committed_transfer.state is TransferState.COMMITTED
        and committed_transfer.request.transfer_id == candidate.transfer_id
        and committed_transfer.request.artifact_ref == candidate.artifact_ref
        and committed_transfer.request.artifact_revision == candidate.artifact_revision
        and committed_transfer.request.target.resource_key == candidate.resource_key
    )
    clear_refs = candidate.lease_state is ReferenceActivity.RELEASED and candidate.residency_state is ReferenceActivity.RELEASED
    eligible = transfer_matches and clear_refs
    reason = "causal transfer and released lease/residency references verified" if eligible else "unknown, active or unverified causal reference blocks cleanup eligibility"
    digest = content_digest({"candidate": candidate, "committed_transfer": committed_transfer if transfer_matches else None, "eligible": eligible})
    return SpillGarbageEligibility(candidate.candidate_id, eligible, False, reason, digest)


@dataclass(frozen=True)
class PrefetchIntent:
    intent_id: str
    resource_key: str
    byte_count: int
    expires_at_ms: int
    evidence_ref: str

    def __post_init__(self) -> None:
        for field in ("intent_id", "resource_key", "evidence_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.byte_count) is not int or self.byte_count < 1 or type(self.expires_at_ms) is not int or self.expires_at_ms < 0:
            raise ValueError("prefetch bounds are invalid")


class PrefetchBudget:
    """Accounts speculative intent; it never starts transfers or selects a schedule."""

    def __init__(self, *, max_bytes: int, max_concurrent: int, limits: M09Limits = DEFAULT_LIMITS) -> None:
        if type(max_bytes) is not int or max_bytes < 0 or type(max_concurrent) is not int or not 1 <= max_concurrent <= 16:
            raise ValueError("prefetch budget must be finite")
        self._max_bytes = max_bytes
        self._max_concurrent = max_concurrent
        self._limits = limits
        self._lock = RLock()
        self._intents: dict[str, PrefetchIntent] = {}
        self._last_now_ms = -1

    def propose(self, intent: PrefetchIntent, *, now_ms: int, known_allocatable_bytes: int | None, protected_headroom_bytes: int = 0) -> bool:
        with self._lock:
            if type(now_ms) is not int or now_ms < self._last_now_ms:
                raise ValueError("prefetch time must use a monotonic clock")
            self._last_now_ms = now_ms
            self.expire(now_ms=now_ms)
            if type(protected_headroom_bytes) is not int or protected_headroom_bytes < 0:
                raise ValueError("protected headroom must be a known non-negative quantity")
            if intent.expires_at_ms <= now_ms or known_allocatable_bytes is None or known_allocatable_bytes < protected_headroom_bytes:
                return False
            if intent.intent_id in self._intents:
                return self._intents[intent.intent_id] == intent
            self._limits.require("max_transfers", len(self._intents) + 1)
            total = sum(item.byte_count for item in self._intents.values()) + intent.byte_count
            if len(self._intents) >= self._max_concurrent or total > min(self._max_bytes, known_allocatable_bytes - protected_headroom_bytes):
                return False
            self._intents[intent.intent_id] = intent
            return True

    def expire(self, *, now_ms: int) -> tuple[str, ...]:
        with self._lock:
            if type(now_ms) is not int or now_ms < self._last_now_ms:
                raise ValueError("prefetch expiry time must use a monotonic clock")
            self._last_now_ms = now_ms
            expired = tuple(sorted(key for key, item in self._intents.items() if item.expires_at_ms <= now_ms))
            for key in expired:
                del self._intents[key]
            return expired

    def intents(self) -> tuple[PrefetchIntent, ...]:
        with self._lock:
            return tuple(sorted(self._intents.values(), key=lambda item: item.intent_id))
