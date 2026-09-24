"""Bounded pressure accounting and cooperative recovery evidence; no process/storage control."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import wraps
from threading import RLock
from typing import Callable, TypeVar

from .limits import DEFAULT_LIMITS, M09Limits
from .model import Confidence, EvidenceOrigin, MutationContext, ResourceSnapshot, content_digest, require_id

__all__ = [
    "PressureLevel", "PressureObservation", "PressureTransition", "PressureGovernor",
    "RecoveryAction", "LeakCandidate", "LeakConfirmation", "OwnerLivenessRef",
    "CooperativeReleaseRequest", "CooperativeReleaseResponse", "RecoveryBudget",
    "ResourceDebt", "ResourceDebtLedger", "CleanupEligibility", "IncidentCapsule",
    "PostRecoveryGate", "confirm_leak", "PressureUnit", "PressureAdmissionConstraint",
    "StaleCommitmentCandidate", "StaleReconciliationReceipt", "StaleCommitmentReaper",
    "ReleaseHandshakeOutcome", "evaluate_cooperative_release", "RecoveryOutcomeState",
    "RecoveryActionRecord", "RecoveryActionLedger", "SafeFailureCapsule",
    "LeakTrendEvidence", "CommitmentState", "RECOVERY_ESCALATION_LADDER",
    "pressure_admission_constraint",
    "RecoveryReferenceState", "DebtResolutionEvidence",
]

_F = TypeVar("_F", bound=Callable[..., object])


def _locked(method: _F) -> _F:
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapper  # type: ignore[return-value]


class PressureLevel(str, Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    ELEVATED = "ELEVATED"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class PressureUnit(str, Enum):
    BASIS_POINTS = "BASIS_POINTS"
    PERCENT = "PERCENT"
    PERMILLE = "PERMILLE"
    UNKNOWN = "UNKNOWN"


def _to_basis_points(value: int | None, unit: PressureUnit) -> int | None:
    if value is None or unit is PressureUnit.UNKNOWN:
        return None
    if type(value) is not int or value < 0:
        raise ValueError("pressure source value must be a non-negative integer")
    multipliers = {PressureUnit.BASIS_POINTS: 1, PressureUnit.PERCENT: 100, PressureUnit.PERMILLE: 10}
    maximums = {PressureUnit.BASIS_POINTS: 10_000, PressureUnit.PERCENT: 100, PressureUnit.PERMILLE: 1_000}
    if value > maximums[unit]:
        raise ValueError("pressure source value exceeds its declared unit range")
    return value * multipliers[unit]


class RecoveryAction(str, Enum):
    EMIT_PRESSURE_EVIDENCE = "EMIT_PRESSURE_EVIDENCE"
    REQUEST_COOPERATIVE_RELEASE = "REQUEST_COOPERATIVE_RELEASE"
    RECONCILE_STALE_COMMITMENT = "RECONCILE_STALE_COMMITMENT"
    QUARANTINE_RESOURCE = "QUARANTINE_RESOURCE"
    REQUEST_FRESH_RECONCILIATION = "REQUEST_FRESH_RECONCILIATION"
    SIGNAL_REPLAN = "SIGNAL_REPLAN"
    SIGNAL_OFFLOAD = "SIGNAL_OFFLOAD"
    RECORD_RESOURCE_DEBT = "RECORD_RESOURCE_DEBT"


class RecoveryOutcomeState(str, Enum):
    REQUESTED = "REQUESTED"
    ATTEMPTED = "ATTEMPTED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


RECOVERY_ESCALATION_LADDER = (
    RecoveryAction.EMIT_PRESSURE_EVIDENCE,
    RecoveryAction.REQUEST_FRESH_RECONCILIATION,
    RecoveryAction.RECONCILE_STALE_COMMITMENT,
    RecoveryAction.REQUEST_COOPERATIVE_RELEASE,
    RecoveryAction.QUARANTINE_RESOURCE,
    RecoveryAction.SIGNAL_REPLAN,
    RecoveryAction.SIGNAL_OFFLOAD,
    RecoveryAction.RECORD_RESOURCE_DEBT,
)


@dataclass(frozen=True)
class RecoveryActionRecord:
    action_id: str
    idempotency_key: str
    resource_key: str
    action: RecoveryAction
    state: RecoveryOutcomeState
    requested_at_ms: int
    attempt_count: int
    evidence_refs: tuple[str, ...]
    result_snapshot_digest: str | None = None
    failure_ref: str | None = None
    capacity_reclaimed: bool = False
    mutation_context: MutationContext | None = None

    def __post_init__(self) -> None:
        for field in ("action_id", "idempotency_key", "resource_key"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if not isinstance(self.action, RecoveryAction) or not isinstance(self.state, RecoveryOutcomeState):
            raise ValueError("recovery action and outcome state must be enumerated")
        if type(self.requested_at_ms) is not int or self.requested_at_ms < 0 or type(self.attempt_count) is not int or not 0 <= self.attempt_count <= 16:
            raise ValueError("recovery action time and attempt count must be bounded")
        refs = tuple(sorted(set(require_id(item, "evidence_ref") for item in self.evidence_refs)))
        if not refs:
            raise ValueError("recovery action records require evidence")
        if type(self.mutation_context) is not MutationContext or self.mutation_context.idempotency_key != self.idempotency_key or self.mutation_context.causal_request_ref not in refs:
            raise ValueError("recovery action requires matching mutation attribution and causal request")
        if self.result_snapshot_digest is not None and (len(self.result_snapshot_digest) != 64 or any(char not in "0123456789abcdef" for char in self.result_snapshot_digest)):
            raise ValueError("recovery result snapshot digest must be SHA-256")
        if self.failure_ref is not None:
            object.__setattr__(self, "failure_ref", require_id(self.failure_ref, "failure_ref"))
        if self.capacity_reclaimed:
            raise ValueError("recovery action status cannot claim capacity reclaimed")
        if self.state is RecoveryOutcomeState.VERIFIED and self.result_snapshot_digest is None:
            raise ValueError("verified recovery action requires fresh reconciled resource snapshot")
        if self.state in {RecoveryOutcomeState.FAILED, RecoveryOutcomeState.UNKNOWN} and self.failure_ref is None:
            raise ValueError("failed/unknown recovery outcome requires a preserved reason reference")


class RecoveryActionLedger:
    def __init__(self, *, max_actions: int = 128, max_attempts_per_action: int = 4) -> None:
        if type(max_actions) is not int or not 1 <= max_actions <= 4_096 or type(max_attempts_per_action) is not int or not 1 <= max_attempts_per_action <= 16:
            raise ValueError("recovery action and retry bounds must be finite")
        self._max_actions = max_actions
        self._max_attempts = max_attempts_per_action
        self._records: dict[str, RecoveryActionRecord] = {}
        self._idempotency: dict[str, tuple[str, str]] = {}
        self._events: list[RecoveryActionRecord] = []
        self._event_replays: dict[str, tuple[str, RecoveryActionRecord]] = {}
        self._attempted_at: dict[str, int] = {}
        self._lock = RLock()

    @_locked
    def request(self, *, action_id: str, idempotency_key: str, resource_key: str, action: RecoveryAction, now_ms: int, evidence_refs: tuple[str, ...], mutation_context: MutationContext) -> RecoveryActionRecord:
        action_id = require_id(action_id, "action_id")
        idempotency_key = require_id(idempotency_key, "idempotency_key")
        resource_key = require_id(resource_key, "resource_key")
        if not isinstance(action, RecoveryAction) or type(now_ms) is not int or now_ms < 0:
            raise ValueError("recovery request must be typed and timestamped")
        refs = tuple(sorted(set(require_id(item, "evidence_ref") for item in evidence_refs)))
        if not refs:
            raise ValueError("recovery request requires causal evidence")
        if type(mutation_context) is not MutationContext or mutation_context.idempotency_key != idempotency_key or mutation_context.causal_request_ref not in refs:
            raise ValueError("recovery request requires an exact authorization/origin/causal mutation context")
        digest = content_digest({"action_id": action_id, "resource_key": resource_key, "action": action, "now_ms": now_ms, "evidence": refs, "mutation_context": mutation_context})
        existing = self._idempotency.get(idempotency_key)
        if existing is not None:
            if existing[0] != digest:
                raise ValueError("recovery idempotency key binds conflicting request semantics")
            return self._records[existing[1]]
        if action_id in self._records or len(self._records) >= self._max_actions:
            raise ValueError("recovery action identity or bounded history is exhausted")
        record = RecoveryActionRecord(action_id, idempotency_key, resource_key, action, RecoveryOutcomeState.REQUESTED, now_ms, 0, refs, mutation_context=mutation_context)
        self._records[action_id] = record
        self._idempotency[idempotency_key] = (digest, action_id)
        self._events.append(record)
        return record

    @_locked
    def mark_attempted(self, action_id: str, *, evidence_ref: str, now_ms: int) -> RecoveryActionRecord:
        action_id = require_id(action_id, "action_id")
        evidence_ref = require_id(evidence_ref, "evidence_ref")
        replay_key = f"{action_id}:attempt:{evidence_ref}"
        replay_digest = content_digest({"now_ms": now_ms})
        replay = self._event_replays.get(replay_key)
        if replay is not None:
            if replay[0] != replay_digest:
                raise ValueError("recovery attempt replay changed its timestamp")
            return replay[1]
        current = self._records.get(action_id)
        if current is None or current.state not in {RecoveryOutcomeState.REQUESTED, RecoveryOutcomeState.FAILED, RecoveryOutcomeState.UNKNOWN}:
            raise ValueError("only a pending or retryable recovery action can be attempted")
        if type(now_ms) is not int or now_ms < current.requested_at_ms or current.attempt_count >= self._max_attempts:
            raise ValueError("recovery attempt time/retry bound is invalid")
        updated = RecoveryActionRecord(current.action_id, current.idempotency_key, current.resource_key, current.action, RecoveryOutcomeState.ATTEMPTED, current.requested_at_ms, current.attempt_count + 1, tuple(sorted(set(current.evidence_refs + (evidence_ref,)))), mutation_context=current.mutation_context)
        self._records[action_id] = updated
        self._attempted_at[action_id] = now_ms
        self._events.append(updated)
        self._event_replays[replay_key] = (replay_digest, updated)
        return updated

    @_locked
    def complete(self, action_id: str, *, state: RecoveryOutcomeState, evidence_ref: str, now_ms: int, snapshot: ResourceSnapshot | None = None) -> RecoveryActionRecord:
        action_id = require_id(action_id, "action_id")
        evidence_ref = require_id(evidence_ref, "evidence_ref")
        replay_key = f"{action_id}:complete:{evidence_ref}"
        replay_digest = content_digest({"state": state, "now_ms": now_ms, "snapshot_digest": snapshot.digest if type(snapshot) is ResourceSnapshot else None})
        replay = self._event_replays.get(replay_key)
        if replay is not None:
            if replay[0] != replay_digest:
                raise ValueError("recovery result replay changed its semantics")
            return replay[1]
        current = self._records.get(action_id)
        if current is None or current.state is not RecoveryOutcomeState.ATTEMPTED or state not in {RecoveryOutcomeState.VERIFIED, RecoveryOutcomeState.FAILED, RecoveryOutcomeState.UNKNOWN}:
            raise ValueError("recovery result requires an attempted action and terminal outcome")
        if type(now_ms) is not int or now_ms < self._attempted_at.get(action_id, current.requested_at_ms):
            raise ValueError("recovery result time must be monotonic")
        snapshot_digest = None
        if state is RecoveryOutcomeState.VERIFIED:
            if type(snapshot) is not ResourceSnapshot or snapshot.identity.stable_key != current.resource_key or snapshot.observed_at_ms <= current.requested_at_ms or not snapshot.is_fresh(now_ms) or snapshot.evidence_origin is not EvidenceOrigin.REPORTED_OBSERVATION:
                raise ValueError("verified recovery requires a new fresh reported snapshot for the exact resource")
            snapshot_digest = snapshot.digest
        elif snapshot is not None:
            raise ValueError("failed or unknown recovery cannot carry success-state snapshot truth")
        result = RecoveryActionRecord(
            current.action_id, current.idempotency_key, current.resource_key, current.action,
            state, current.requested_at_ms, current.attempt_count,
            tuple(sorted(set(current.evidence_refs + (evidence_ref,)))), snapshot_digest,
            evidence_ref if state in {RecoveryOutcomeState.FAILED, RecoveryOutcomeState.UNKNOWN} else None,
            mutation_context=current.mutation_context,
        )
        self._records[action_id] = result
        self._events.append(result)
        self._event_replays[replay_key] = (replay_digest, result)
        return result

    @_locked
    def get(self, action_id: str) -> RecoveryActionRecord | None:
        return self._records.get(action_id)

    @_locked
    def history(self) -> tuple[RecoveryActionRecord, ...]:
        return tuple(self._events)


@dataclass(frozen=True)
class PressureObservation:
    observation_id: str
    resource_key: str
    confidence: Confidence
    utilization_basis_points: int | None
    observed_at_ms: int
    provenance_ref: str
    external_pressure: bool
    source_value: int | None
    source_unit: PressureUnit
    scope_ref: str
    expires_at_ms: int

    def __post_init__(self) -> None:
        for field in ("observation_id", "resource_key", "provenance_ref", "scope_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if not isinstance(self.confidence, Confidence) or type(self.external_pressure) is not bool or not isinstance(self.source_unit, PressureUnit):
            raise ValueError("pressure confidence, original unit and external-pressure classification are required")
        if self.source_value is not None and (type(self.source_value) is not int or self.source_value < 0):
            raise ValueError("original pressure source value must be a non-negative integer or unknown")
        normalized = _to_basis_points(self.source_value, self.source_unit)
        if normalized != self.utilization_basis_points:
            raise ValueError("normalized pressure basis points must preserve the exact original value/unit")
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0 or type(self.expires_at_ms) is not int or self.expires_at_ms < self.observed_at_ms:
            raise ValueError("pressure observation timestamps must be non-negative and ordered")

    def is_fresh(self, now_ms: int) -> bool:
        return type(now_ms) is int and self.observed_at_ms <= now_ms <= self.expires_at_ms


@dataclass(frozen=True)
class PressureTransition:
    resource_key: str
    previous: PressureLevel
    current: PressureLevel
    observation_ids: tuple[str, ...]
    changed_at_ms: int
    epoch: int
    external_pressure: bool


class PressureGovernor:
    def __init__(self, *, enter_watch: int = 7_500, enter_elevated: int = 8_500, enter_critical: int = 9_500, exit_watch: int = 6_500, confirmation_count: int = 2, dwell_ms: int = 1_000, cooldown_ms: int = 5_000) -> None:
        if not 0 <= exit_watch < enter_watch < enter_elevated < enter_critical <= 10_000:
            raise ValueError("pressure thresholds must be ordered basis points")
        if type(confirmation_count) is not int or not 1 <= confirmation_count <= 16 or any(type(x) is not int or x < 0 for x in (dwell_ms, cooldown_ms)):
            raise ValueError("pressure hysteresis bounds are invalid")
        self._thresholds = (enter_watch, enter_elevated, enter_critical, exit_watch, confirmation_count, dwell_ms, cooldown_ms)
        self._states: dict[str, PressureLevel] = {}
        self._samples: dict[str, list[PressureObservation]] = {}
        self._last_change: dict[str, int] = {}
        self._epochs: dict[str, int] = {}
        self._last_now: dict[str, int] = {}
        self._lock = RLock()

    def observe(self, observation: PressureObservation, *, now_ms: int) -> PressureTransition | None:
        with self._lock:
            return self._observe(observation, now_ms=now_ms)

    def _observe(self, observation: PressureObservation, *, now_ms: int) -> PressureTransition | None:
        if type(observation) is not PressureObservation or type(now_ms) is not int or now_ms < 0:
            raise ValueError("pressure governor requires exact evidence and monotonic time")
        if now_ms < self._last_now.get(observation.resource_key, 0):
            raise ValueError("pressure evaluation time must be monotonic per resource")
        self._last_now[observation.resource_key] = now_ms
        if observation.confidence not in {Confidence.OBSERVED, Confidence.ESTIMATED} or observation.utilization_basis_points is None or not observation.is_fresh(now_ms):
            self._states[observation.resource_key] = PressureLevel.UNKNOWN
            self._samples.pop(observation.resource_key, None)
            return None
        samples = self._samples.setdefault(observation.resource_key, [])
        if samples and observation.observed_at_ms < samples[-1].observed_at_ms:
            raise ValueError("pressure observations must be monotonic per resource")
        if observation.observation_id in {item.observation_id for item in samples}:
            return None
        samples.append(observation)
        del samples[:-16]
        watch, elevated, critical, exit_watch, count, dwell, cooldown = self._thresholds
        current = self._states.get(observation.resource_key, PressureLevel.NORMAL)
        recent = samples[-count:]
        levels = [self._classify(item.utilization_basis_points or 0, watch, elevated, critical) for item in recent]
        candidate = max(levels, key=lambda item: list(PressureLevel).index(item)) if len(recent) == count else current
        if current in {PressureLevel.HIGH, PressureLevel.ELEVATED, PressureLevel.CRITICAL}:
            if len(recent) == count and all(item.utilization_basis_points is not None and item.utilization_basis_points < exit_watch for item in recent):
                candidate = PressureLevel.NORMAL
        if candidate is current:
            return None
        minimum_interval = max(dwell, cooldown)
        last_change = self._last_change.get(observation.resource_key)
        if last_change is not None and observation.observed_at_ms - last_change < minimum_interval:
            return None
        epoch = self._epochs.get(observation.resource_key, 0) + 1
        transition = PressureTransition(observation.resource_key, current, candidate, tuple(item.observation_id for item in recent), observation.observed_at_ms, epoch, observation.external_pressure)
        self._states[observation.resource_key] = candidate
        self._last_change[observation.resource_key] = observation.observed_at_ms
        self._epochs[observation.resource_key] = epoch
        return transition

    def state(self, resource_key: str) -> PressureLevel:
        with self._lock:
            return self._states.get(resource_key, PressureLevel.UNKNOWN)

    @staticmethod
    def _classify(value: int, watch: int, elevated: int, critical: int) -> PressureLevel:
        if value >= critical:
            return PressureLevel.CRITICAL
        if value >= elevated:
            return PressureLevel.ELEVATED
        if value >= watch:
            return PressureLevel.HIGH
        return PressureLevel.NORMAL


@dataclass(frozen=True)
class PressureAdmissionConstraint:
    resource_key: str
    deny_new_commitments: bool
    external_pressure: bool
    observation_id: str
    source_ref: str
    reason: str
    capacity_reclaimed: bool = False

    def __post_init__(self) -> None:
        for field in ("resource_key", "observation_id", "source_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.deny_new_commitments) is not bool or type(self.external_pressure) is not bool or self.capacity_reclaimed:
            raise ValueError("pressure may constrain admission but can never claim recovered capacity")
        if not self.reason:
            raise ValueError("admission constraint requires a machine-readable reason")


def pressure_admission_constraint(observation: PressureObservation, *, now_ms: int) -> PressureAdmissionConstraint:
    if type(observation) is not PressureObservation or not observation.is_fresh(now_ms):
        raise ValueError("fresh scoped pressure evidence is required")
    deny = observation.external_pressure or observation.confidence is not Confidence.OBSERVED or observation.utilization_basis_points is None
    reason = "external or uncertain pressure blocks new commitments pending reconciliation" if deny else "pressure evidence does not independently deny commitments"
    return PressureAdmissionConstraint(observation.resource_key, deny, observation.external_pressure, observation.observation_id, observation.provenance_ref, reason)


class CommitmentState(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    RELEASED = "RELEASED"
    ORPHANED = "ORPHANED"


@dataclass(frozen=True)
class StaleCommitmentCandidate:
    candidate_id: str
    resource_key: str
    lease_id: str
    owner_ref: str
    state: CommitmentState
    quantity_bytes: int | None
    observed_at_ms: int
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in ("candidate_id", "resource_key", "lease_id", "owner_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if not isinstance(self.state, CommitmentState):
            raise ValueError("commitment state must be explicit")
        if self.quantity_bytes is not None and (type(self.quantity_bytes) is not int or self.quantity_bytes < 0):
            raise ValueError("commitment quantity must be non-negative or unknown")
        refs = tuple(sorted(set(require_id(item, "evidence_ref") for item in self.evidence_refs)))
        if not refs or type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise ValueError("stale commitment candidate requires evidence and time")
        object.__setattr__(self, "evidence_refs", refs)


@dataclass(frozen=True)
class StaleReconciliationReceipt:
    candidate_id: str
    status: str
    resource_key: str
    lease_id: str
    owner_liveness_ref: str
    reconciled_at_ms: int
    freed_bytes: None = None
    capacity_reclaimed: bool = False

    def __post_init__(self) -> None:
        for field in ("candidate_id", "resource_key", "lease_id", "owner_liveness_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.reconciled_at_ms) is not int or self.reconciled_at_ms < 0 or self.freed_bytes is not None or self.capacity_reclaimed:
            raise ValueError("stale reconciliation can record state only; it cannot fabricate freed capacity")


class StaleCommitmentReaper:
    def __init__(self, *, limits: M09Limits = DEFAULT_LIMITS) -> None:
        self._limits = limits
        self._receipts: dict[str, tuple[str, StaleReconciliationReceipt]] = {}
        self._lock = RLock()

    def reconcile(self, candidate: StaleCommitmentCandidate, owner: "OwnerLivenessRef", *, now_ms: int) -> StaleReconciliationReceipt:
        if type(candidate) is not StaleCommitmentCandidate or type(owner) is not OwnerLivenessRef:
            raise ValueError("stale reconciliation requires exact candidate and M11 liveness records")
        if candidate.state is CommitmentState.ACTIVE or candidate.state is CommitmentState.RELEASED:
            raise ValueError("active or already-released commitments cannot be reaped")
        if owner.owner_ref != candidate.owner_ref or owner.observed_at_ms > now_ms or candidate.observed_at_ms > now_ms:
            raise ValueError("stale reconciliation cannot use future evidence")
        if now_ms - candidate.observed_at_ms > 60_000 or now_ms - owner.observed_at_ms > 60_000:
            raise ValueError("stale reconciliation evidence is outside its fixed freshness window")
        digest = content_digest({"candidate": candidate, "owner": owner})
        with self._lock:
            existing = self._receipts.get(candidate.candidate_id)
            if existing is not None:
                if existing[0] == digest:
                    return existing[1]
                raise ValueError("stale commitment identity cannot be reconciled with conflicting evidence")
            self._limits.require("max_recovery_actions", len(self._receipts) + 1)
            if owner.state == "UNKNOWN":
                status = "QUARANTINED_OWNER_LIVENESS_UNKNOWN"
            elif owner.state == "ALIVE":
                status = "PRESERVED_OWNER_ALIVE"
            else:
                status = "RECONCILIATION_RECORDED_PENDING_FRESH_RESOURCE_TRUTH"
            receipt = StaleReconciliationReceipt(candidate.candidate_id, status, candidate.resource_key, candidate.lease_id, owner.evidence_ref, now_ms)
            self._receipts[candidate.candidate_id] = (digest, receipt)
            return receipt


@dataclass(frozen=True)
class ReleaseHandshakeOutcome:
    request_id: str
    status: str
    capacity_reclaimed: bool
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", require_id(self.request_id, "request_id"))
        if self.capacity_reclaimed:
            raise ValueError("cooperative release response cannot by itself prove reclaimed capacity")
        refs = tuple(sorted(set(require_id(item, "evidence_ref") for item in self.evidence_refs)))
        if not refs:
            raise ValueError("release handshake outcome requires causal evidence")
        object.__setattr__(self, "evidence_refs", refs)


def evaluate_cooperative_release(request: "CooperativeReleaseRequest", response: "CooperativeReleaseResponse | None", *, now_ms: int) -> ReleaseHandshakeOutcome:
    if type(request) is not CooperativeReleaseRequest or type(now_ms) is not int or now_ms < request.requested_at_ms:
        raise ValueError("release handshake requires exact request and monotonic time")
    if response is None:
        status = "TIMED_OUT" if now_ms > request.deadline_ms else "PENDING"
        return ReleaseHandshakeOutcome(request.request_id, status, False, (request.reason_ref,))
    if type(response) is not CooperativeReleaseResponse or response.request_id != request.request_id or response.owner_ref != request.owner_ref:
        raise ValueError("release response must match exact request and owner")
    if response.responded_at_ms > now_ms:
        raise ValueError("release response cannot be from the future")
    if response.responded_at_ms > request.deadline_ms:
        status = "TIMED_OUT"
    elif response.response == "ACCEPTED":
        status = "ACCEPTED_AWAITING_RESOURCE_RECONCILIATION"
    else:
        status = response.response
    return ReleaseHandshakeOutcome(request.request_id, status, False, (request.reason_ref, response.evidence_ref))


@dataclass(frozen=True)
class LeakCandidate:
    candidate_id: str
    resource_key: str
    lease_id: str
    owner_ref: str
    claimed_bytes: int
    observed_resident_bytes: int
    observation_refs: tuple[str, ...]
    suspected_at_ms: int

    def __post_init__(self) -> None:
        for field in ("candidate_id", "resource_key", "lease_id", "owner_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if any(type(value) is not int or value < 0 for value in (self.claimed_bytes, self.observed_resident_bytes, self.suspected_at_ms)):
            raise ValueError("leak candidate quantities and time must be non-negative")
        refs = tuple(sorted(set(require_id(item, "observation_ref") for item in self.observation_refs)))
        if not refs:
            raise ValueError("leak suspicion requires independent evidence references")
        object.__setattr__(self, "observation_refs", refs)


@dataclass(frozen=True)
class OwnerLivenessRef:
    owner_ref: str
    state: str
    authority_ref: str
    observed_at_ms: int
    evidence_ref: str

    def __post_init__(self) -> None:
        for field in ("owner_ref", "authority_ref", "evidence_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if self.state not in {"ALIVE", "TERMINATED", "UNKNOWN"}:
            raise ValueError("owner liveness must be ALIVE, TERMINATED or UNKNOWN")
        if self.state != "UNKNOWN" and self.authority_ref.split(":", 1)[0] != "M11":
            raise ValueError("worker lifecycle evidence must be referenced to M11")
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise ValueError("liveness timestamp must be non-negative")


@dataclass(frozen=True)
class LeakConfirmation:
    candidate_id: str
    confirmed: bool
    reason: str
    evidence_digest: str


def confirm_leak(candidate: LeakCandidate, owner: OwnerLivenessRef, *, fresh_snapshot: ResourceSnapshot, now_ms: int, minimum_excess_bytes: int, minimum_distinct_observations: int = 2, maximum_liveness_age_ms: int = 30_000) -> LeakConfirmation:
    if type(fresh_snapshot) is not ResourceSnapshot or not fresh_snapshot.is_fresh(now_ms) or fresh_snapshot.evidence_origin is not EvidenceOrigin.REPORTED_OBSERVATION or fresh_snapshot.identity.stable_key != candidate.resource_key:
        return LeakConfirmation(candidate.candidate_id, False, "fresh observed resource truth required", "")
    if owner.owner_ref != candidate.owner_ref or owner.state != "TERMINATED" or type(now_ms) is not int or type(maximum_liveness_age_ms) is not int or maximum_liveness_age_ms < 0 or owner.observed_at_ms > now_ms or now_ms - owner.observed_at_ms > maximum_liveness_age_ms:
        return LeakConfirmation(candidate.candidate_id, False, "authoritative owner termination is not proven", "")
    if type(minimum_excess_bytes) is not int or minimum_excess_bytes < 0 or type(minimum_distinct_observations) is not int or minimum_distinct_observations < 2:
        return LeakConfirmation(candidate.candidate_id, False, "leak confirmation thresholds are invalid", "")
    if len(candidate.observation_refs) < minimum_distinct_observations:
        return LeakConfirmation(candidate.candidate_id, False, "independent observations below confirmation threshold", "")
    excess = candidate.observed_resident_bytes - candidate.claimed_bytes
    if excess < minimum_excess_bytes:
        return LeakConfirmation(candidate.candidate_id, False, "resident discrepancy below confirmation threshold", "")
    evidence = content_digest({
        "candidate": candidate,
        "owner_liveness": owner,
        "snapshot": fresh_snapshot.digest,
        "excess": excess,
        "time": now_ms,
    })
    return LeakConfirmation(candidate.candidate_id, True, "independent liveness and fresh excess-residency proof", evidence)


@dataclass(frozen=True)
class CooperativeReleaseRequest:
    request_id: str
    lease_id: str
    owner_ref: str
    requested_at_ms: int
    deadline_ms: int
    reason_ref: str

    def __post_init__(self) -> None:
        for field in ("request_id", "lease_id", "owner_ref", "reason_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if type(self.requested_at_ms) is not int or type(self.deadline_ms) is not int or self.deadline_ms <= self.requested_at_ms:
            raise ValueError("cooperative release requires a bounded deadline")


@dataclass(frozen=True)
class CooperativeReleaseResponse:
    request_id: str
    owner_ref: str
    response: str
    responded_at_ms: int
    evidence_ref: str

    def __post_init__(self) -> None:
        for field in ("request_id", "owner_ref", "evidence_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if self.response not in {"ACCEPTED", "DECLINED", "DEFERRED"}:
            raise ValueError("cooperative response must be explicit")
        if type(self.responded_at_ms) is not int or self.responded_at_ms < 0:
            raise ValueError("responded_at_ms must be non-negative")


class RecoveryBudget:
    def __init__(self, *, max_attempts: int, window_ms: int, max_churn_bytes: int, cooldown_ms: int) -> None:
        values = (max_attempts, window_ms, max_churn_bytes, cooldown_ms)
        if any(type(item) is not int or item < 0 for item in values) or max_attempts < 1 or window_ms < 1:
            raise ValueError("recovery budget bounds are invalid")
        self._max_attempts = max_attempts
        self._window_ms = window_ms
        self._max_churn = max_churn_bytes
        self._cooldown = cooldown_ms
        self._attempts: list[tuple[int, int, str]] = []
        self._last_at_ms = -1
        self._lock = RLock()

    @_locked
    def consume(self, *, action_ref: str, at_ms: int, churn_bytes: int) -> bool:
        action_ref = require_id(action_ref, "action_ref")
        if type(at_ms) is not int or at_ms < 0 or type(churn_bytes) is not int or churn_bytes < 0:
            return False
        if at_ms < self._last_at_ms:
            return False
        self._last_at_ms = at_ms
        self._attempts = [(time, amount, ref) for time, amount, ref in self._attempts if at_ms - time <= self._window_ms]
        existing = next((item for item in self._attempts if item[2] == action_ref), None)
        if existing is not None:
            return existing == (at_ms, churn_bytes, action_ref)
        if len(self._attempts) >= self._max_attempts:
            return False
        if sum(amount for _, amount, _ in self._attempts) + churn_bytes > self._max_churn:
            return False
        if self._attempts and at_ms - self._attempts[-1][0] < self._cooldown:
            return False
        self._attempts.append((at_ms, churn_bytes, action_ref))
        return True

    @property
    @_locked
    def attempts(self) -> tuple[tuple[int, int, str], ...]:
        return tuple(self._attempts)


@dataclass(frozen=True)
class ResourceDebt:
    debt_id: str
    resource_key: str
    kind: str
    quantity_bytes: int | None
    evidence_refs: tuple[str, ...]
    created_at_ms: int
    cleared_by_snapshot_digest: str | None = None
    resolution_evidence_ref: str | None = None
    resolution_evidence_digest: str | None = None

    def __post_init__(self) -> None:
        for field in ("debt_id", "resource_key", "kind"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if self.quantity_bytes is not None and (type(self.quantity_bytes) is not int or self.quantity_bytes < 0):
            raise ValueError("debt quantity must be non-negative or unknown")
        refs = tuple(sorted(set(require_id(item, "evidence_ref") for item in self.evidence_refs)))
        if not refs or type(self.created_at_ms) is not int or self.created_at_ms < 0:
            raise ValueError("debt requires evidence and a non-negative time")
        if self.cleared_by_snapshot_digest is None and (self.resolution_evidence_ref is not None or self.resolution_evidence_digest is not None):
            raise ValueError("unresolved debt cannot carry resolution evidence")
        if self.cleared_by_snapshot_digest is not None and (len(self.cleared_by_snapshot_digest) != 64 or self.resolution_evidence_ref is None or self.resolution_evidence_digest is None):
            raise ValueError("resolved debt must bind snapshot and exact resolution evidence")
        if self.resolution_evidence_ref is not None:
            object.__setattr__(self, "resolution_evidence_ref", require_id(self.resolution_evidence_ref, "resolution_evidence_ref"))
        if self.resolution_evidence_digest is not None and (len(self.resolution_evidence_digest) != 64 or any(char not in "0123456789abcdef" for char in self.resolution_evidence_digest)):
            raise ValueError("debt resolution evidence must be SHA-256")
        object.__setattr__(self, "evidence_refs", refs)


@dataclass(frozen=True)
class DebtResolutionEvidence:
    debt_id: str
    resource_key: str
    snapshot_digest: str
    remaining_quantity_bytes: int
    authority_ref: str
    evidence_ref: str
    observed_at_ms: int

    def __post_init__(self) -> None:
        for field in ("debt_id", "resource_key", "authority_ref", "evidence_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if len(self.snapshot_digest) != 64 or any(char not in "0123456789abcdef" for char in self.snapshot_digest):
            raise ValueError("debt resolution must bind an exact resource snapshot digest")
        if type(self.remaining_quantity_bytes) is not int or self.remaining_quantity_bytes < 0 or type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise ValueError("debt resolution quantity/time must be explicit non-negative values")
        if self.authority_ref.split(":", 1)[0] == "M09":
            raise ValueError("M09 cannot self-certify external debt resolution")


class ResourceDebtLedger:
    def __init__(self, *, limits: M09Limits = DEFAULT_LIMITS) -> None:
        self._limits = limits
        self._debts: dict[str, ResourceDebt] = {}
        self._lock = RLock()

    def record(self, debt: ResourceDebt) -> ResourceDebt:
        with self._lock:
            existing = self._debts.get(debt.debt_id)
            if existing is not None:
                if existing == debt:
                    return existing
                raise ValueError("resource debt identity cannot be reused")
            self._limits.require("max_events", len(self._debts) + 1)
            self._debts[debt.debt_id] = debt
            return debt

    def reconcile(self, debt_id: str, snapshot: ResourceSnapshot, resolution: DebtResolutionEvidence, *, now_ms: int) -> ResourceDebt:
        with self._lock:
            debt = self._debts.get(debt_id)
            if debt is None or type(snapshot) is not ResourceSnapshot or type(resolution) is not DebtResolutionEvidence or snapshot.identity.stable_key != debt.resource_key or snapshot.evidence_origin is not EvidenceOrigin.REPORTED_OBSERVATION or not snapshot.is_fresh(now_ms):
                raise ValueError("fresh matching observation and external resolution evidence are required")
            if resolution.debt_id != debt.debt_id or resolution.resource_key != debt.resource_key or resolution.snapshot_digest != snapshot.digest or resolution.observed_at_ms > now_ms or resolution.remaining_quantity_bytes != 0:
                raise ValueError("debt resolution must prove zero remaining quantity against the exact fresh snapshot")
            resolution_digest = content_digest(resolution)
            if debt.cleared_by_snapshot_digest is not None:
                if debt.cleared_by_snapshot_digest == snapshot.digest and debt.resolution_evidence_digest == resolution_digest:
                    return debt
                raise ValueError("cleared resource debt is immutable")
            updated = ResourceDebt(debt.debt_id, debt.resource_key, debt.kind, debt.quantity_bytes, debt.evidence_refs, debt.created_at_ms, snapshot.digest, resolution.evidence_ref, resolution_digest)
            self._debts[debt_id] = updated
            return updated

    def unresolved(self) -> tuple[ResourceDebt, ...]:
        with self._lock:
            return tuple(sorted((item for item in self._debts.values() if item.cleared_by_snapshot_digest is None), key=lambda item: item.debt_id))


@dataclass(frozen=True)
class CleanupEligibility:
    resource_ref: str
    eligible_for_release_request: bool
    physical_deletion_permitted: bool
    reason: str
    evidence_refs: tuple[str, ...]
    artifact_ref: str
    transfer_ref: str
    lease_ref: str
    residency_ref: str
    lease_state: "RecoveryReferenceState"
    residency_state: "RecoveryReferenceState"

    def __post_init__(self) -> None:
        for field in ("resource_ref", "artifact_ref", "transfer_ref", "lease_ref", "residency_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if self.physical_deletion_permitted:
            raise ValueError("M09 cleanup eligibility can never authorize physical deletion")
        if not isinstance(self.lease_state, RecoveryReferenceState) or not isinstance(self.residency_state, RecoveryReferenceState):
            raise ValueError("cleanup requires explicit causal lease and residency state")
        if self.eligible_for_release_request and (self.lease_state is not RecoveryReferenceState.RELEASED or self.residency_state is not RecoveryReferenceState.RELEASED):
            raise ValueError("active or unknown references cannot be cleanup eligible")
        refs = tuple(sorted(set(require_id(item, "evidence_ref") for item in self.evidence_refs)))
        if not self.reason or not refs:
            raise ValueError("cleanup eligibility requires explicit rationale and evidence")
        object.__setattr__(self, "evidence_refs", refs)


class RecoveryReferenceState(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class IncidentCapsule:
    incident_id: str
    resource_key: str
    pressure_observation_ids: tuple[str, ...]
    actions: tuple[RecoveryAction, ...]
    evidence_refs: tuple[str, ...]
    created_at_ms: int
    digest: str
    snapshot_digests: tuple[str, ...] = ()
    lease_refs: tuple[str, ...] = ()
    residency_refs: tuple[str, ...] = ()
    transfer_ids: tuple[str, ...] = ()
    shape_transition_ids: tuple[str, ...] = ()
    owner_refs: tuple[str, ...] = ()
    recovery_action_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in ("incident_id", "resource_key"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if any(not isinstance(item, RecoveryAction) for item in self.actions):
            raise ValueError("incident actions must be enumerated M09 actions")
        if not self.evidence_refs or type(self.created_at_ms) is not int or self.created_at_ms < 0:
            raise ValueError("incident capsule requires evidence and valid time")
        snapshots = tuple(sorted(set(self.snapshot_digests)))
        if any(len(item) != 64 or any(char not in "0123456789abcdef" for char in item) for item in snapshots):
            raise ValueError("incident snapshot links must be exact SHA-256 digests")
        object.__setattr__(self, "snapshot_digests", snapshots)
        for field in ("lease_refs", "residency_refs", "transfer_ids", "shape_transition_ids", "owner_refs", "recovery_action_ids"):
            object.__setattr__(self, field, tuple(sorted(set(require_id(item, f"{field}_item") for item in getattr(self, field)))))
        object.__setattr__(self, "pressure_observation_ids", tuple(sorted(set(require_id(item, "pressure_observation_id") for item in self.pressure_observation_ids))))
        object.__setattr__(self, "evidence_refs", tuple(sorted(set(require_id(item, "evidence_ref") for item in self.evidence_refs))))
        expected = content_digest({
            "incident_id": self.incident_id, "resource_key": self.resource_key,
            "observations": self.pressure_observation_ids, "actions": self.actions,
            "evidence": self.evidence_refs, "created_at_ms": self.created_at_ms,
            "snapshots": self.snapshot_digests, "leases": self.lease_refs,
            "residencies": self.residency_refs, "transfers": self.transfer_ids,
            "shape_transitions": self.shape_transition_ids, "owners": self.owner_refs,
            "recovery_action_ids": self.recovery_action_ids,
        })
        if self.digest and self.digest != expected:
            raise ValueError("incident capsule digest does not match its evidence")
        object.__setattr__(self, "digest", expected)


@dataclass(frozen=True)
class SafeFailureCapsule:
    incident_id: str
    resource_key: str
    reason_ref: str
    preserved_snapshot_digest: str
    confidence: Confidence
    evidence_refs: tuple[str, ...]
    action_record_refs: tuple[str, ...]
    created_at_ms: int
    digest: str = ""
    capacity_reclaimed: bool = False

    def __post_init__(self) -> None:
        for field in ("incident_id", "resource_key", "reason_ref"):
            object.__setattr__(self, field, require_id(getattr(self, field), field))
        if len(self.preserved_snapshot_digest) != 64 or any(char not in "0123456789abcdef" for char in self.preserved_snapshot_digest):
            raise ValueError("safe failure must bind the exact preserved snapshot")
        if self.confidence not in {Confidence.UNKNOWN, Confidence.STALE, Confidence.CONFLICTED, Confidence.QUARANTINED}:
            raise ValueError("safe failure capsule is only for uncertain or unsafe truth")
        refs = tuple(sorted(set(require_id(item, "evidence_ref") for item in self.evidence_refs)))
        actions = tuple(sorted(set(require_id(item, "action_record_ref") for item in self.action_record_refs)))
        if not refs or type(self.created_at_ms) is not int or self.created_at_ms < 0 or self.capacity_reclaimed:
            raise ValueError("safe failure must preserve evidence and cannot claim reclaimed capacity")
        object.__setattr__(self, "evidence_refs", refs)
        object.__setattr__(self, "action_record_refs", actions)
        expected = content_digest({"incident_id": self.incident_id, "resource_key": self.resource_key, "reason_ref": self.reason_ref, "snapshot": self.preserved_snapshot_digest, "confidence": self.confidence, "evidence": refs, "actions": actions, "created_at_ms": self.created_at_ms, "capacity_reclaimed": False})
        if self.digest and self.digest != expected:
            raise ValueError("safe failure capsule digest does not match preserved state")
        object.__setattr__(self, "digest", expected)


@dataclass(frozen=True)
class LeakTrendEvidence:
    resource_key: str
    window_start_ms: int
    window_end_ms: int
    observation_ids: tuple[str, ...]
    gap_count: int
    synthetic_fixture: bool
    evidence_digest: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "resource_key", require_id(self.resource_key, "resource_key"))
        ids = tuple(sorted(set(require_id(item, "observation_id") for item in self.observation_ids)))
        if not ids or len(ids) > 10_000 or type(self.window_start_ms) is not int or type(self.window_end_ms) is not int or self.window_start_ms < 0 or self.window_end_ms < self.window_start_ms:
            raise ValueError("leak trend requires a bounded observation window")
        if type(self.gap_count) is not int or self.gap_count < 0 or type(self.synthetic_fixture) is not bool:
            raise ValueError("trend gap and evidence origin must be explicit")
        object.__setattr__(self, "observation_ids", ids)
        expected = content_digest({"resource_key": self.resource_key, "window_start_ms": self.window_start_ms, "window_end_ms": self.window_end_ms, "observation_ids": ids, "gap_count": self.gap_count, "synthetic_fixture": self.synthetic_fixture})
        if self.evidence_digest and self.evidence_digest != expected:
            raise ValueError("leak trend evidence digest mismatch")
        object.__setattr__(self, "evidence_digest", expected)


class PostRecoveryGate:
    @staticmethod
    def verify(*, prior_snapshot: ResourceSnapshot, current_snapshot: ResourceSnapshot, now_ms: int) -> bool:
        if type(prior_snapshot) is not ResourceSnapshot or type(current_snapshot) is not ResourceSnapshot:
            return False
        return (
            current_snapshot.identity.stable_key == prior_snapshot.identity.stable_key
            and current_snapshot.snapshot_id != prior_snapshot.snapshot_id
            and current_snapshot.observed_at_ms > prior_snapshot.observed_at_ms
            and current_snapshot.is_fresh(now_ms)
            and current_snapshot.confidence is Confidence.OBSERVED
            and current_snapshot.evidence_origin is EvidenceOrigin.REPORTED_OBSERVATION
        )
