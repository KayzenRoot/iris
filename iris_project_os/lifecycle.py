"""The orthogonal Production State Vector and the durable history that proves it.

M02 refuses to collapse "what phase is this production in", "is work running", "has a
human approved it" and "has the outside world already seen it" into one status string
(D-M02-S05-001, D-M02-S05-002). Each region gets its own versioned transition table over
its own enum, and the vector as a whole refuses the combinations §24 calls impossible.

The vector is still not authority on its own: a ``ProductionLedger`` of ``StateTransition``
receipts is, because §26 requires current state to be rebuildable from durable history.
``ProductionLedger.replay`` recomputes every state from the initial vector, and
``prove_state`` puts the recomputation next to the cached projection for an auditor.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from typing import Any, Iterable, Mapping

from .base import Labeled, Record, of
from .errors import LifecycleError, ProjectOSError, SchemaValidationError, StoreConflictError
from .identity import (
    LIFECYCLE_SCHEMA_VERSION,
    SUPPORTED_LIFECYCLE_SCHEMAS,
    EntityKind,
    ExternalRef,
    TransitionReceipt,
    new_id,
    require_id,
)
from .limits import MAX_BUNDLE_ITEMS, MAX_RECEIPT_EVIDENCE, MAX_TRANSITIONS
from .machines import StateMachine
from .versions import (
    CONTRACT_VERSION,
    ComponentVersion,
    SUPPORTED_CONTRACT_VERSIONS,
    canonical_json,
    content_digest,
    require_bounded,
    require_component_version,
    require_identifier,
    require_millis,
    require_optional_text,
    require_supported_version,
    require_text,
)

__all__ = [
    "LifecyclePhase",
    "ExecutionCondition",
    "ReviewCondition",
    "ReleaseCondition",
    "BlockerKind",
    "PRODUCTION_PHASES",
    "PRODUCTION_EXECUTION",
    "PRODUCTION_REVIEW",
    "PRODUCTION_RELEASE",
    "LIFECYCLE_TABLES",
    "lifecycle_tables",
    "phase_rank",
    "phase_at_least",
    "AuthorizedJump",
    "TransitionProfile",
    "ProductionStateVector",
    "initial_vector",
    "StateTransition",
    "advance",
    "attempt_outcome",
    "Blocker",
    "BlockerLedger",
    "CompletionProfile",
    "completion_of",
    "ProductionLedger",
    "StateProof",
]


class LifecyclePhase(Labeled):
    """Where a production stands on the ladder. Nothing else is smuggled in here."""

    DRAFT = "DRAFT"
    PLANNED = "PLANNED"
    READY = "READY"
    MATERIALIZED = "MATERIALIZED"
    VALIDATING = "VALIDATING"
    ACCEPTED = "ACCEPTED"
    RELEASED = "RELEASED"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


class ExecutionCondition(Labeled):
    """Whether work is running now. A reversible operational fact, never a verdict."""

    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


class ReviewCondition(Labeled):
    """Workflow state around review. Quality authority stays with M01's decision."""

    NOT_REQUESTED = "NOT_REQUESTED"
    PENDING = "PENDING"
    CHANGES_REQUIRED = "CHANGES_REQUIRED"
    APPROVED = "APPROVED"


class ReleaseCondition(Labeled):
    """External-delivery truth. Moving an internal ref back does not move this."""

    UNRELEASED = "UNRELEASED"
    STAGED = "STAGED"
    PUBLISHED = "PUBLISHED"
    WITHDRAWN = "WITHDRAWN"


class BlockerKind(Labeled):
    """The eight operational reasons §13 admits for stopping work, none of them terminal."""

    MISSING_MODEL = "MISSING_MODEL"
    MISSING_CAPABILITY = "MISSING_CAPABILITY"
    MISSING_RIGHTS = "MISSING_RIGHTS"
    MISSING_ASSET = "MISSING_ASSET"
    INCOMPATIBLE_DEPENDENCY = "INCOMPATIBLE_DEPENDENCY"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    SECURITY_POLICY = "SECURITY_POLICY"
    EXTERNAL_UNAVAILABLE = "EXTERNAL_UNAVAILABLE"


_LADDER = (
    LifecyclePhase.DRAFT,
    LifecyclePhase.PLANNED,
    LifecyclePhase.READY,
    LifecyclePhase.MATERIALIZED,
    LifecyclePhase.VALIDATING,
    LifecyclePhase.ACCEPTED,
    LifecyclePhase.RELEASED,
    LifecyclePhase.SUPERSEDED,
    LifecyclePhase.ARCHIVED,
)

_PHASE_RANK: Mapping[LifecyclePhase, int] = {item: rank for rank, item in enumerate(_LADDER)}


def phase_rank(phase: Any) -> int:
    return _PHASE_RANK[LifecyclePhase.parse(phase, "phase")]


def phase_at_least(phase: Any, wanted: Any) -> bool:
    """Whether a phase has passed the given rung of the ladder."""

    return phase_rank(phase) >= phase_rank(wanted)


Phase = LifecyclePhase
Execution = ExecutionCondition
Review = ReviewCondition
Release = ReleaseCondition

PRODUCTION_PHASES = StateMachine(
    name="production-lifecycle",
    state_type=LifecyclePhase,
    transitions={
        Phase.DRAFT: (Phase.PLANNED,),
        Phase.PLANNED: (Phase.READY,),
        Phase.READY: (Phase.MATERIALIZED,),
        Phase.MATERIALIZED: (Phase.VALIDATING,),
        Phase.VALIDATING: (Phase.ACCEPTED,),
        Phase.ACCEPTED: (Phase.RELEASED,),
        Phase.RELEASED: (Phase.SUPERSEDED,),
        Phase.SUPERSEDED: (Phase.ARCHIVED,),
        Phase.ARCHIVED: (),
    },
)

PRODUCTION_EXECUTION = StateMachine(
    name="production-execution",
    state_type=ExecutionCondition,
    transitions={
        Execution.IDLE: (Execution.ACTIVE, Execution.BLOCKED),
        Execution.ACTIVE: (Execution.IDLE, Execution.BLOCKED),
        Execution.BLOCKED: (Execution.IDLE,),
    },
)

PRODUCTION_REVIEW = StateMachine(
    name="production-review",
    state_type=ReviewCondition,
    transitions={
        Review.NOT_REQUESTED: (Review.PENDING,),
        Review.PENDING: (Review.APPROVED, Review.CHANGES_REQUIRED),
        Review.CHANGES_REQUIRED: (Review.PENDING, Review.APPROVED),
        Review.APPROVED: (Review.PENDING,),
    },
)

PRODUCTION_RELEASE = StateMachine(
    name="production-release",
    state_type=ReleaseCondition,
    transitions={
        Release.UNRELEASED: (Release.STAGED,),
        Release.STAGED: (Release.PUBLISHED, Release.UNRELEASED),
        Release.PUBLISHED: (Release.WITHDRAWN,),
        Release.WITHDRAWN: (),
    },
)

LIFECYCLE_TABLES: Mapping[str, StateMachine] = {
    machine.name: machine
    for machine in (PRODUCTION_PHASES, PRODUCTION_EXECUTION, PRODUCTION_REVIEW, PRODUCTION_RELEASE)
}

# The regions one transition may move, each with the table that governs it. The phase
# region is checked through the profile as well, so it is handled separately.
_REGION_TABLES: Mapping[str, StateMachine] = {
    "execution": PRODUCTION_EXECUTION,
    "review": PRODUCTION_REVIEW,
    "release_condition": PRODUCTION_RELEASE,
}


def lifecycle_tables() -> dict[str, dict[str, tuple[str, ...]]]:
    """The whole transition law as data, so evidence can hash it (proof 1)."""

    return {
        name: {
            state.value: tuple(target.value for target in machine.legal_targets(state))
            for state in machine.states
        }
        for name, machine in LIFECYCLE_TABLES.items()
    }


class _Unset:
    """Distinct from ``None`` because clearing a claim is a change that must be heard."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - only ever seen in a debugger
        return "<unset>"


_UNSET = _Unset()


def _freeze_texts(values: Any, field: str, *, maximum: int) -> tuple[str, ...]:
    collected = require_bounded(values, field, maximum=maximum, kind="obligation")
    return tuple(sorted({require_text(item, f"{field}[]", maximum=512) for item in collected}))


def _freeze_refs(values: Any, field: str, *, maximum: int = MAX_RECEIPT_EVIDENCE) -> tuple[ExternalRef, ...]:
    collected = require_bounded(values, field, maximum=maximum, kind="ref")
    return tuple(ExternalRef.coerce(item, f"{field}[]") for item in collected)


@dataclass(frozen=True)
class AuthorizedJump(Record):
    """One skipped rung, and the evidence that proves the skipped obligations."""

    source: LifecyclePhase
    target: LifecyclePhase
    proof_refs: tuple[ExternalRef, ...] = ()
    obligations: tuple[str, ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {"proof_refs": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", LifecyclePhase.parse(self.source, "source"))
        object.__setattr__(self, "target", LifecyclePhase.parse(self.target, "target"))
        if self.source is self.target:
            raise LifecycleError(f"jump {self.source.value} -> itself authoritates nothing")
        if PRODUCTION_PHASES.is_legal(self.source, self.target):
            raise LifecycleError(
                f"{self.source.value} -> {self.target.value} is already on the ladder; a jump exists to "
                "widen the table, not to restate it"
            )
        if self.source is Phase.ARCHIVED:
            raise LifecycleError("an archived production is reopened by a revival fork, never by a jump")
        if phase_rank(self.target) < phase_rank(self.source):
            raise LifecycleError(
                f"{self.source.value} -> {self.target.value} walks the ladder backwards; a rejected "
                "candidate is reworked through new history, not by relabeling the old one"
            )
        if phase_rank(self.target) >= phase_rank(Phase.RELEASED) and phase_rank(self.source) < phase_rank(
            Phase.ACCEPTED
        ):
            raise LifecycleError(
                f"{self.source.value} -> {self.target.value} delivers work that was never accepted; the "
                "acceptance gate is an invariant, not a rung a profile may widen away"
            )
        object.__setattr__(self, "proof_refs", _freeze_refs(self.proof_refs, "proof_refs"))
        if not self.proof_refs:
            raise LifecycleError(
                f"{self.source.value} -> {self.target.value} skips a rung and cites no proof, which is "
                "exactly the relabeling the module spec forbids"
            )
        object.__setattr__(self, "obligations", _freeze_texts(self.obligations, "obligations", maximum=MAX_BUNDLE_ITEMS))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def text(self) -> str:
        return f"{self.source.value} -> {self.target.value} proven by {len(self.proof_refs)} ref(s)"


@dataclass(frozen=True)
class TransitionProfile(Record):
    """The policy saying where a class of production may go and where it stops.

    A profile only ever *widens* the ladder: it may authorize skips that carry proof, and
    it names the phases no one may enter without a human review receipt. It can never
    remove a rung, because that would let a policy make an illegal move legal.
    """

    profile_id: str
    terminal_phase: LifecyclePhase = Phase.ACCEPTED
    obligations: tuple[str, ...] = ()
    jumps: tuple[AuthorizedJump, ...] = ()
    human_review_phases: tuple[LifecyclePhase, ...] = ()
    description: Any = None
    contract_version: str = CONTRACT_VERSION

    NESTED = {"jumps": of(AuthorizedJump)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", require_identifier(self.profile_id, "profile_id"))
        object.__setattr__(self, "terminal_phase", LifecyclePhase.parse(self.terminal_phase, "terminal_phase"))
        object.__setattr__(self, "obligations", _freeze_texts(self.obligations, "obligations", maximum=MAX_BUNDLE_ITEMS))
        collected = require_bounded(self.jumps, "jumps", maximum=MAX_BUNDLE_ITEMS, kind="jump")
        resolved = tuple(AuthorizedJump.coerce(item, "jumps[]") for item in collected)
        seen: set[tuple[str, str]] = set()
        for item in resolved:
            pair = (item.source.value, item.target.value)
            if pair in seen:
                raise LifecycleError(f"{self.profile_id} authorizes {pair} twice")
            seen.add(pair)
        object.__setattr__(self, "jumps", tuple(sorted(resolved, key=lambda item: (item.source.value, item.target.value))))
        wanted = require_bounded(self.human_review_phases, "human_review_phases", maximum=len(_PHASE_RANK), kind="phase")
        object.__setattr__(
            self,
            "human_review_phases",
            tuple(sorted({LifecyclePhase.parse(item, "human_review_phases[]") for item in wanted}, key=phase_rank)),
        )
        object.__setattr__(self, "description", require_optional_text(self.description, "description", maximum=512))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    def jump_between(self, source: Any, target: Any) -> AuthorizedJump | None:
        """The authorization for one skipped rung, if this profile grants it."""

        resolved = LifecyclePhase.parse(source, "source")
        wanted = LifecyclePhase.parse(target, "target")
        return next((item for item in self.jumps if item.source is resolved and item.target is wanted), None)

    def requires_human_review(self, phase: Any) -> bool:
        return LifecyclePhase.parse(phase, "phase") in self.human_review_phases

    def admits(self, source: Any, target: Any) -> bool:
        """Whether this profile may carry a production from one phase to another."""

        resolved = LifecyclePhase.parse(source, "source")
        wanted = LifecyclePhase.parse(target, "target")
        return PRODUCTION_PHASES.is_legal(resolved, wanted) or self.jump_between(resolved, wanted) is not None

    def proof_of(self, source: Any, target: Any) -> tuple[ExternalRef, ...]:
        found = self.jump_between(source, target)
        return () if found is None else found.proof_refs


@dataclass(frozen=True)
class ProductionStateVector(Record):
    """One production's state as four orthogonal answers, plus the refs that check them.

    The claims are separated from the evidence on purpose: the vector says *which*
    snapshot was accepted or released, and the snapshot itself is what refuses to exist
    without a closure carrying the proof.
    """

    project_id: str
    production_id: str
    phase: LifecyclePhase = Phase.DRAFT
    execution: ExecutionCondition = Execution.IDLE
    review: ReviewCondition = Review.NOT_REQUESTED
    release_condition: ReleaseCondition = Release.UNRELEASED
    candidate_snapshot_id: Any = None
    release_snapshot_id: Any = None
    active_attempt_id: Any = None
    restoration_ref: Any = None
    superseded_by_ref: Any = None
    state_schema: str = LIFECYCLE_SCHEMA_VERSION
    contract_version: str = CONTRACT_VERSION

    NESTED = {"restoration_ref": of(ExternalRef), "superseded_by_ref": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", require_identifier(self.project_id, "project_id"))
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        object.__setattr__(self, "phase", LifecyclePhase.parse(self.phase, "phase"))
        object.__setattr__(self, "execution", ExecutionCondition.parse(self.execution, "execution"))
        object.__setattr__(self, "review", ReviewCondition.parse(self.review, "review"))
        object.__setattr__(self, "release_condition", ReleaseCondition.parse(self.release_condition, "release_condition"))
        for name in ("candidate_snapshot_id", "release_snapshot_id", "active_attempt_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_id(value, name))
        object.__setattr__(
            self, "state_schema", require_supported_version("state schema", self.state_schema, SUPPORTED_LIFECYCLE_SCHEMAS)
        )
        require_supported_version("contract", self.contract_version, SUPPORTED_CONTRACT_VERSIONS)
        self._require_coherent()

    def _require_coherent(self) -> None:
        """Refuse the vectors §24 calls impossible, naming the claim that broke."""

        if phase_at_least(self.phase, Phase.MATERIALIZED) and self.candidate_snapshot_id is None:
            raise LifecycleError(
                f"{self.production_id} claims {self.phase.value} with no candidate snapshot, so nothing was "
                "materialized or judged"
            )
        if self.review is Review.APPROVED and not phase_at_least(self.phase, Phase.VALIDATING):
            raise LifecycleError(
                f"{self.production_id} records APPROVED review at {self.phase.value}, before anything exists to review"
            )
        if self.release_condition in {Release.STAGED, Release.PUBLISHED, Release.WITHDRAWN} and not phase_at_least(
            self.phase, Phase.ACCEPTED
        ):
            raise LifecycleError(
                f"{self.production_id} reports {self.release_condition.value} delivery without being ACCEPTED; "
                "acceptance is a judgement, never a side effect of a completed render"
            )
        if self.release_condition in {Release.PUBLISHED, Release.WITHDRAWN} and not phase_at_least(self.phase, Phase.RELEASED):
            raise LifecycleError(
                f"{self.production_id} says {self.release_condition.value} while its phase is {self.phase.value}; "
                "publication is only ever a fact about a released production"
            )
        if phase_at_least(self.phase, Phase.RELEASED) and self.release_snapshot_id is None:
            raise LifecycleError(
                f"{self.production_id} is {self.phase.value} with no release snapshot, which is the RELEASED-and-"
                "never-accepted combination the state doctrine exists to prevent"
            )
        if self.phase is Phase.SUPERSEDED and self.superseded_by_ref is None:
            raise LifecycleError(
                f"{self.production_id} is SUPERSEDED without saying what supersedes it; supersession resolves "
                "preferred future references, and a nameless one resolves nothing"
            )
        if self.execution is not Execution.IDLE and self.phase is Phase.ARCHIVED and self.restoration_ref is None:
            raise LifecycleError(
                f"{self.production_id} runs work while archived; only an explicit restoration or verification "
                "task may, and it has to cite one"
            )
        if self.active_attempt_id is not None and self.execution is Execution.IDLE:
            raise LifecycleError(
                f"{self.production_id} names an active attempt while IDLE; a finished attempt is history, not a "
                "claim about work running now"
            )

    def moved(self, **changes: Any) -> "ProductionStateVector":
        """The same vector with some regions moved, revalidated as a whole."""

        unknown = sorted(set(changes) - {item.name for item in fields(self)})
        if unknown:
            raise SchemaValidationError(f"ProductionStateVector has no field named {unknown}")
        return replace(self, **changes)

    @property
    def summary(self) -> str:
        return (
            f"{self.phase.value}/{self.execution.value}/{self.review.value}/{self.release_condition.value}"
        )


def initial_vector(
    production_id: str,
    project_id: str = "iris",
    *,
    phase: Any = Phase.DRAFT,
    execution: Any = Execution.IDLE,
    review: Any = Review.NOT_REQUESTED,
    release_condition: Any = Release.UNRELEASED,
    **claims: Any,
) -> ProductionStateVector:
    """The vector a production starts from, stated rather than implied."""

    return ProductionStateVector(
        project_id=project_id,
        production_id=require_id(production_id, "production_id"),
        phase=phase,
        execution=execution,
        review=review,
        release_condition=release_condition,
        **claims,
    )


@dataclass(frozen=True)
class StateTransition(Record):
    """One recorded move of a production vector, with the receipt that proves it.

    ``TransitionReceipt`` stays area A's durable identity spine; this record adds what a
    production move specifically owes: both full vectors, the profile that authorized the
    edge, and the refs that make an acceptance or a release attributable to evidence
    rather than to whoever typed the call.
    """

    transition_id: str
    production_id: str
    from_vector: ProductionStateVector
    to_vector: ProductionStateVector
    receipt: TransitionReceipt
    profile: Any = None
    promotion_ref: Any = None
    review_receipt: Any = None
    replacement_ref: Any = None
    blocker_ref: Any = None
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "from_vector": of(ProductionStateVector),
        "to_vector": of(ProductionStateVector),
        "receipt": of(TransitionReceipt),
        "profile": of(TransitionProfile),
        "promotion_ref": of(ExternalRef),
        "review_receipt": of(ExternalRef),
        "replacement_ref": of(ExternalRef),
        "blocker_ref": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "transition_id", require_id(self.transition_id, "transition_id"))
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        object.__setattr__(self, "from_vector", ProductionStateVector.coerce(self.from_vector, "from_vector"))
        object.__setattr__(self, "to_vector", ProductionStateVector.coerce(self.to_vector, "to_vector"))
        object.__setattr__(self, "receipt", TransitionReceipt.coerce(self.receipt, "receipt"))
        if self.profile is not None:
            object.__setattr__(self, "profile", TransitionProfile.coerce(self.profile, "profile"))
        for name in ("promotion_ref", "review_receipt", "replacement_ref", "blocker_ref"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, ExternalRef):
                raise SchemaValidationError(f"{name} must be an ExternalRef or None")
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})
        self._require_legal_move()
        self._require_claims_follow_state()
        self._require_authority()
        self._require_receipt_agrees()

    def _require_legal_move(self) -> None:
        if self.from_vector.production_id != self.production_id or self.to_vector.production_id != self.production_id:
            raise LifecycleError(f"{self.transition_id} moves a vector belonging to another production")
        if self.from_vector == self.to_vector:
            raise LifecycleError(f"{self.transition_id} records a move that changes nothing")
        before, after = self.from_vector.phase, self.to_vector.phase
        if before is not after:
            self._require_phase_edge(before, after)
        for name, table in _REGION_TABLES.items():
            source, target = getattr(self.from_vector, name), getattr(self.to_vector, name)
            if source is not target:
                table.require(source, target, reason=self.receipt.reason_code)

    def _require_phase_edge(self, before: LifecyclePhase, after: LifecyclePhase) -> None:
        if PRODUCTION_PHASES.is_legal(before, after):
            return
        available = ", ".join(item.value for item in PRODUCTION_PHASES.legal_targets(before)) or "none (terminal)"
        if self.profile is None:
            raise LifecycleError(
                f"{before.value} -> {after.value} skips a rung with no transition profile, so nothing proves the "
                f"obligations the skipped rungs carried (admitted from {before.value}: {available})"
            )
        if self.profile.jump_between(before, after) is None:
            raise LifecycleError(
                f"profile {self.profile.profile_id} does not authorize {before.value} -> {after.value} "
                f"(admitted from {before.value}: {available})"
            )

    def _require_claims_follow_state(self) -> None:
        """A claim is made by a move; no move that changes no state may re-point one.

        ``candidate_snapshot_id``, ``release_snapshot_id`` and ``superseded_by_ref`` are what
        earlier receipts and snapshots are attributed to. A transition that swapped one of
        them while leaving the four governed regions where they were would rewrite that
        history under a fresh id. Filling a claim and clearing one are moves; substituting a
        different claim is not. The attempt and restoration refs are excluded because a
        blocked attempt resuming, or a second verification task on archived material, names
        a new one on purpose, alongside a state move that says so.
        """

        if not self.moved_regions:
            raise LifecycleError(
                f"{self.transition_id} moves no governed state, only a claim, which would re-point what an "
                "earlier transition already proved"
            )
        for name in ("candidate_snapshot_id", "release_snapshot_id", "superseded_by_ref"):
            before, after = getattr(self.from_vector, name), getattr(self.to_vector, name)
            if before is not None and after is not None and before != after:
                raise LifecycleError(
                    f"{self.transition_id} re-points {name} from {before} to {after}; a claim once made is "
                    "answered by a new production or a supersession, never by quietly naming something else"
                )

    def _require_authority(self) -> None:
        """The moves that change what IRIS claims about a production each cite their proof.

        Only an *entry* into a governed phase owes evidence. A later transition that
        leaves the phase where it is, such as staging a release under an already accepted
        production, must not have to re-cite the bundle that accepted it.
        """

        target = self.to_vector.phase
        entered = self.from_vector.phase is not target
        if entered and target in {Phase.ACCEPTED, Phase.RELEASED} and self.promotion_ref is None:
            raise LifecycleError(
                f"{self.production_id} cannot enter {target.value} without the promotion evidence bundle that "
                "establishes it; an attempt finishing is not a judgement"
            )
        if self.to_vector.review is Review.APPROVED and self.from_vector.review is not Review.APPROVED:
            if self.review_receipt is None:
                if self.from_vector.review is Review.CHANGES_REQUIRED:
                    raise LifecycleError(
                        f"{self.production_id} converts CHANGES_REQUIRED into APPROVED with no new review receipt; a "
                        "rejection is answered by a decision, never by waiting"
                    )
                raise LifecycleError(
                    f"{self.production_id} records APPROVED review with no review receipt behind it; an approval is "
                    "a human decision on file, never a field someone set"
                )
        if entered and target is Phase.SUPERSEDED and self.replacement_ref is None:
            raise LifecycleError(f"{self.production_id} is superseded with no replacement named")
        if (
            self.to_vector.execution is Execution.BLOCKED
            and self.from_vector.execution is not Execution.BLOCKED
            and self.blocker_ref is None
        ):
            raise LifecycleError(
                f"{self.production_id} claims BLOCKED with nothing blocking it; a blocker is recorded, or work is idle"
            )
        if (
            self.from_vector.execution is Execution.BLOCKED
            and self.to_vector.execution is not Execution.BLOCKED
            and self.blocker_ref is None
        ):
            raise LifecycleError(
                f"{self.production_id} unblocks without naming the blocker it cleared, which would erase the fact "
                "that it was ever blocked"
            )
        profile = self.profile
        if entered and profile is not None and profile.requires_human_review(target) and self.review_receipt is None:
            raise LifecycleError(
                f"profile {profile.profile_id} requires a human review receipt to enter {target.value}"
            )

    def _require_receipt_agrees(self) -> None:
        receipt = self.receipt
        if receipt.entity_kind is not EntityKind.PRODUCTION:
            raise LifecycleError(f"{self.transition_id} is filed against a {receipt.entity_kind.value}, not a production")
        if receipt.entity_id != self.production_id:
            raise LifecycleError(f"{self.transition_id} records a receipt for production {receipt.entity_id}")
        if receipt.transition_id != self.transition_id:
            raise LifecycleError(f"{self.transition_id} carries a receipt for {receipt.transition_id}")
        if receipt.from_state != self.from_vector.phase.value:
            raise LifecycleError(
                f"{self.transition_id}'s receipt says it moved {receipt.from_state} while the vector came from "
                f"{self.from_vector.phase.value}"
            )
        if receipt.to_state != self.to_vector.phase.value:
            raise LifecycleError(
                f"{self.transition_id}'s receipt says it moved to {receipt.to_state} while the vector arrived at "
                f"{self.to_vector.phase.value}"
            )

    @property
    def moved_regions(self) -> tuple[str, ...]:
        return tuple(name for name in _REGION_TABLES if getattr(self.from_vector, name) is not getattr(self.to_vector, name)) + (
            () if self.from_vector.phase is self.to_vector.phase else ("phase",)
        )

    @property
    def text(self) -> str:
        parts = [
            f"{name}: {getattr(self.from_vector, name).value} -> {getattr(self.to_vector, name).value}"
            for name in ("phase", *_REGION_TABLES)
            if getattr(self.from_vector, name) is not getattr(self.to_vector, name)
        ]
        return f"{self.production_id}: " + "; ".join(parts)


def _region_changes(source: ProductionStateVector, wanted: Mapping[str, Any]) -> dict[str, Any]:
    """Parse each stated change against the field it moves, so a name is never guessed."""

    changes: dict[str, Any] = {}
    for name, value in wanted.items():
        if value is _UNSET:
            continue
        current = getattr(source, name)
        if isinstance(current, Labeled):
            value = type(current).parse(value, name)
        elif name in {"restoration_ref", "superseded_by_ref"} and value is not None:
            value = ExternalRef.coerce(value, name)
        elif name in {"candidate_snapshot_id", "release_snapshot_id", "active_attempt_id"} and value is not None:
            value = require_id(value, name)
        changes[name] = value
    return changes


def advance(
    vector: Any,
    *,
    actor: Any,
    phase: Any = _UNSET,
    execution: Any = _UNSET,
    review: Any = _UNSET,
    release_condition: Any = _UNSET,
    candidate_snapshot_id: Any = _UNSET,
    release_snapshot_id: Any = _UNSET,
    active_attempt_id: Any = _UNSET,
    restoration_ref: Any = _UNSET,
    superseded_by_ref: Any = _UNSET,
    profile: Any = None,
    promotion_ref: Any = None,
    review_receipt: Any = None,
    replacement_ref: Any = None,
    blocker_ref: Any = None,
    now_ms: int = 0,
    reason_code: str = "advanced",
    command_id: Any = None,
    evidence_refs: Iterable[Any] = (),
    policy_ref: Any = None,
    transition_id: str | None = None,
    parent_receipt_id: Any = None,
    state_schema: str = LIFECYCLE_SCHEMA_VERSION,
) -> StateTransition:
    """Move a production vector one governed step, or refuse and say what was missing.

    The transition returned is not yet history: only a ``ProductionLedger`` records it,
    and only the ledger can attach the causal parent that makes the chain replayable.
    """

    source = ProductionStateVector.coerce(vector, "vector")
    changes = _region_changes(
        source,
        {
            "phase": phase,
            "execution": execution,
            "review": review,
            "release_condition": release_condition,
            "candidate_snapshot_id": candidate_snapshot_id,
            "release_snapshot_id": release_snapshot_id,
            "active_attempt_id": active_attempt_id,
            "restoration_ref": restoration_ref,
            "superseded_by_ref": superseded_by_ref,
        },
    )
    if not changes:
        raise LifecycleError(f"{source.production_id}: advance() was asked to move nothing")
    target = source.moved(**changes)
    minted = require_id(transition_id, "transition_id") if transition_id is not None else new_id()
    resolved_refs = tuple(ExternalRef.coerce(item, "evidence_refs[]") for item in evidence_refs)
    if profile is not None:
        for reference in profile.proof_of(source.phase, target.phase):
            if reference not in resolved_refs:
                resolved_refs = (*resolved_refs, reference)
    receipt = TransitionReceipt(
        transition_id=minted,
        entity_kind=EntityKind.PRODUCTION,
        entity_id=source.production_id,
        from_state=source.phase.value,
        to_state=target.phase.value,
        actor=require_component_version(actor, "actor"),
        reason_code=require_identifier(reason_code, "reason_code"),
        timestamp_ms=require_millis(now_ms, "now_ms"),
        evidence_refs=resolved_refs,
        policy_ref=ExternalRef.coerce(policy_ref, "policy_ref") if policy_ref is not None else None,
        command_id=require_text(command_id, "command_id", maximum=128) if command_id is not None else None,
        command_digest=content_digest(target.to_payload()) if command_id is not None else None,
        causal_parent_receipt_id=parent_receipt_id,
        state_schema=state_schema,
    )
    return StateTransition(
        transition_id=minted,
        production_id=source.production_id,
        from_vector=source,
        to_vector=target,
        receipt=receipt,
        profile=profile,
        promotion_ref=promotion_ref,
        review_receipt=review_receipt,
        replacement_ref=replacement_ref,
        blocker_ref=blocker_ref,
    )


def start_attempt(
    vector: Any,
    *,
    attempt_id: Any,
    actor: Any,
    now_ms: int = 0,
    **changes: Any,
) -> StateTransition:
    """Put work on the floor: one move that names both the run and the attempt."""

    return advance(
        vector,
        actor=actor,
        execution=Execution.ACTIVE,
        active_attempt_id=require_id(attempt_id, "attempt_id"),
        now_ms=now_ms,
        reason_code=changes.pop("reason_code", "attempt_started"),
        **changes,
    )


def attempt_outcome(
    vector: Any,
    *,
    attempt_id: Any,
    succeeded: bool,
    actor: Any,
    now_ms: int = 0,
    blocked_by: Any = None,
    **changes: Any,
) -> StateTransition:
    """Record what an attempt did, and prove that it cannot touch the phase.

    An attempt ending well makes work idle. It accepts nothing (§4) and releases nothing,
    and a failure leaves the phase exactly where it was: a provider's exit code is that
    provider reporting on one run, which is not the same claim as production quality
    (D-M02-S05-003).
    """

    source = ProductionStateVector.coerce(vector, "vector")
    if "phase" in changes:
        raise LifecycleError(
            "an attempt outcome may not move the lifecycle phase; a provider reporting that its process "
            "ended proves that attempt, and nothing about acceptance"
        )
    wanted = require_id(attempt_id, "attempt_id")
    if source.active_attempt_id != wanted:
        raise LifecycleError(
            f"{source.production_id} reports an outcome for attempt {wanted} while {source.active_attempt_id} "
            "is the attempt on the floor; a run that is not running cannot end"
        )
    blocked = blocked_by is not None
    return advance(
        source,
        actor=actor,
        execution=Execution.BLOCKED if blocked else Execution.IDLE,
        active_attempt_id=None,
        blocker_ref=ExternalRef.coerce(blocked_by, "blocked_by") if blocked else None,
        now_ms=now_ms,
        reason_code="attempt_blocked" if blocked else ("attempt_succeeded" if succeeded else "attempt_failed"),
        evidence_refs=(ExternalRef(kind=EntityKind.ATTEMPT, reference=wanted),),
        **changes,
    )


@dataclass(frozen=True)
class Blocker(Record):
    """One reversible stop, with the receipts that raised and cleared it.

    Clearing never removes. §13 is explicit that unblocking "does not pretend the blocker
    never occurred", so the cleared record is what a later audit reads to see how long the
    production really stood still.
    """

    blocker_id: str
    production_id: str
    kind: BlockerKind
    reason: str
    raised_receipt_id: Any = None
    cleared_receipt_id: Any = None
    actor: Any = None
    evidence_refs: tuple[ExternalRef, ...] = ()
    stale_gate_refs: tuple[ExternalRef, ...] = ()
    raised_at_ms: int = 0
    cleared_at_ms: Any = None
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "actor": of(ComponentVersion),
        "evidence_refs": of(ExternalRef),
        "stale_gate_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "blocker_id", require_id(self.blocker_id, "blocker_id"))
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        object.__setattr__(self, "kind", BlockerKind.parse(self.kind, "kind"))
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=512))
        object.__setattr__(self, "raised_at_ms", require_millis(self.raised_at_ms, "raised_at_ms"))
        for name in ("raised_receipt_id", "cleared_receipt_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_id(value, name))
        if self.cleared_at_ms is not None:
            cleared = require_millis(self.cleared_at_ms, "cleared_at_ms")
            if cleared < self.raised_at_ms:
                raise LifecycleError(
                    f"blocker {self.blocker_id} was cleared {self.raised_at_ms - cleared}ms before it was raised"
                )
            object.__setattr__(self, "cleared_at_ms", cleared)
        if self.actor is not None:
            object.__setattr__(self, "actor", require_component_version(self.actor, "actor"))
        object.__setattr__(self, "evidence_refs", _freeze_refs(self.evidence_refs, "evidence_refs"))
        object.__setattr__(self, "stale_gate_refs", _freeze_refs(self.stale_gate_refs, "stale_gate_refs"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def is_cleared(self) -> bool:
        return self.cleared_at_ms is not None

    @property
    def reference(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.RECEIPT, reference=self.blocker_id)

    @property
    def text(self) -> str:
        state = "cleared" if self.is_cleared else "open"
        return f"{self.production_id} is {state}: {self.kind.value} ({self.reason})"


class BlockerLedger:
    """Every blocker ever raised, so a cleared one stays visible to the next audit."""

    def __init__(self, blockers: Iterable[Any] = ()) -> None:
        self._items: dict[str, Blocker] = {}
        for item in blockers:
            self.add(item)

    def add(self, blocker: Any) -> Blocker:
        wanted = Blocker.coerce(blocker, "blocker")
        existing = self._items.get(wanted.blocker_id)
        if existing is not None:
            if existing == wanted:
                return existing
            raise StoreConflictError(
                f"blocker {wanted.blocker_id} already exists with different content; raise a new blocker "
                "instead of rewriting the one that was reported"
            )
        self._items[wanted.blocker_id] = wanted
        return wanted

    def get(self, blocker_id: str) -> Blocker:
        wanted = require_id(blocker_id, "blocker_id")
        try:
            return self._items[wanted]
        except KeyError:
            raise LifecycleError(f"no blocker {wanted} was ever raised, so it cannot be cleared") from None

    def clear(self, blocker_id: str, *, at_ms: int, actor: Any, cleared_receipt_id: Any = None) -> Blocker:
        """Close a blocker as new history; the record that was raised is never edited."""

        found = self.get(blocker_id)
        if found.is_cleared:
            return found
        cleared = replace(
            found,
            cleared_at_ms=at_ms,
            cleared_receipt_id=require_id(cleared_receipt_id, "cleared_receipt_id") if cleared_receipt_id is not None else None,
            actor=require_component_version(actor, "actor"),
        )
        # The cleared form carries the raising facts unchanged, so the audit sees one blocker
        # that stood still for a known span, rather than two records that have to be joined.
        self._items[found.blocker_id] = cleared
        return cleared

    def open_for(self, production_id: str) -> tuple[Blocker, ...]:
        return self._for(production_id, cleared=False)

    def blockers_of(self, production_id: str) -> tuple[Blocker, ...]:
        return self._for(production_id, cleared=None)

    def _for(self, production_id: str, *, cleared: bool | None) -> tuple[Blocker, ...]:
        wanted = require_id(production_id, "production_id")
        return tuple(
            sorted(
                (
                    item
                    for item in self._items.values()
                    if item.production_id == wanted and (cleared is None or item.is_cleared is cleared)
                ),
                key=lambda item: (item.raised_at_ms, item.blocker_id),
            )
        )

    @property
    def size(self) -> int:
        return len(self._items)


@dataclass(frozen=True)
class CompletionProfile(Record):
    """The derived "this production is finished" claim, and the obligation it stands on.

    COMPLETED is deliberately not a ``LifecyclePhase`` (§23): an internal asset ends at
    ACCEPTED and a regulated one ends at ARCHIVED, so one universal terminal state would
    be false somewhere. The summary has to name the profile and the terminal obligation
    it satisfied, which is exactly what this record carries.
    """

    production_id: str
    profile_id: str
    terminal_phase: LifecyclePhase
    reached_phase: LifecyclePhase
    obligations: tuple[str, ...] = ()
    satisfied: bool = False
    outstanding: tuple[str, ...] = ()
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        object.__setattr__(self, "profile_id", require_identifier(self.profile_id, "profile_id"))
        object.__setattr__(self, "terminal_phase", LifecyclePhase.parse(self.terminal_phase, "terminal_phase"))
        object.__setattr__(self, "reached_phase", LifecyclePhase.parse(self.reached_phase, "reached_phase"))
        object.__setattr__(self, "obligations", _freeze_texts(self.obligations, "obligations", maximum=MAX_BUNDLE_ITEMS))
        object.__setattr__(self, "outstanding", _freeze_texts(self.outstanding, "outstanding", maximum=MAX_BUNDLE_ITEMS))
        if not isinstance(self.satisfied, bool):
            raise SchemaValidationError("satisfied must be a boolean")
        if self.satisfied and self.outstanding:
            raise LifecycleError(
                f"{self.profile_id} reports COMPLETED while {sorted(self.outstanding)[:2]} remain outstanding"
            )
        if self.satisfied and not phase_at_least(self.reached_phase, self.terminal_phase):
            raise LifecycleError(
                f"{self.profile_id} reports COMPLETED at {self.reached_phase.value}, short of its terminal "
                f"{self.terminal_phase.value}"
            )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def summary(self) -> str:
        """The only wording IRIS may use: a completion named by the obligation it met."""

        if not self.satisfied:
            return f"{self.production_id} is {self.reached_phase.value}, not complete: {', '.join(self.outstanding)}"
        return (
            f"{self.production_id} is COMPLETED under profile {self.profile_id} at {self.terminal_phase.value}, "
            f"having satisfied {', '.join(self.obligations) or 'that profile'}"
        )


def completion_of(
    vector: Any,
    profile: Any,
    *,
    open_blockers: Iterable[Any] = (),
) -> CompletionProfile:
    """Whether a vector has met a profile's terminal obligation, and what still stands."""

    source = ProductionStateVector.coerce(vector, "vector")
    wanted = TransitionProfile.coerce(profile, "profile")
    outstanding: list[str] = []
    if not phase_at_least(source.phase, wanted.terminal_phase):
        outstanding.append(f"phase {wanted.terminal_phase.value} not reached")
    if source.execution is not Execution.IDLE:
        outstanding.append(f"execution is {source.execution.value}")
    if source.review is Review.PENDING:
        outstanding.append("a review request is unanswered")
    if source.release_condition is Release.STAGED:
        outstanding.append("a release is staged and never published or withdrawn")
    for blocker in open_blockers:
        found = Blocker.coerce(blocker, "open_blockers[]")
        if found.production_id != source.production_id:
            raise LifecycleError(f"{found.blocker_id} blocks another production and cannot be judged here")
        outstanding.append(f"blocker {found.kind.value}")
    return CompletionProfile(
        production_id=source.production_id,
        profile_id=wanted.profile_id,
        terminal_phase=wanted.terminal_phase,
        reached_phase=source.phase,
        obligations=wanted.obligations,
        satisfied=not outstanding,
        outstanding=tuple(outstanding),
    )


@dataclass(frozen=True)
class StateProof(Record):
    """Replayed state next to cached projection: the answer when an auditor asks "sure?"."""

    production_id: str
    recorded_state: str
    replayed_state: str
    transitions: int
    head_receipt_id: Any = None
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        for name in ("recorded_state", "replayed_state"):
            object.__setattr__(self, name, require_text(getattr(self, name), name, maximum=4096))
        if isinstance(self.transitions, bool) or not isinstance(self.transitions, int) or self.transitions < 0:
            raise SchemaValidationError("transitions must be a non-negative count")
        if self.head_receipt_id is not None:
            object.__setattr__(self, "head_receipt_id", require_id(self.head_receipt_id, "head_receipt_id"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def matches(self) -> bool:
        return self.recorded_state == self.replayed_state

    @property
    def text(self) -> str:
        verdict = "matches" if self.matches else "DIVERGES FROM"
        return f"{self.production_id}: projection {verdict} replay over {self.transitions} transition(s)"


class ProductionLedger:
    """Append-only transition history for one production, and the only state authority.

    Nothing here sets a state directly. A caller proposes a ``StateTransition`` and the
    ledger accepts it only if it continues the chain, then updates its projection from
    the recorded vector, so ``replay`` and ``current`` can be compared at any moment.
    """

    def __init__(
        self,
        production_id: str,
        initial: Any,
        *,
        profile: Any = None,
        transitions: Iterable[Any] = (),
        maximum: int = MAX_TRANSITIONS,
    ) -> None:
        self._production_id = require_id(production_id, "production_id")
        self._initial = ProductionStateVector.coerce(initial, "initial")
        if self._initial.production_id != self._production_id:
            raise LifecycleError("the initial vector belongs to another production")
        if self._initial.phase is not Phase.DRAFT:
            raise LifecycleError(
                f"a ledger replays a production from DRAFT, not from {self._initial.phase.value}; history that "
                "starts mid-ladder cannot prove the rungs before it"
            )
        self._profile = TransitionProfile.coerce(profile, "profile") if profile is not None else None
        if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 1:
            raise SchemaValidationError("maximum must be a positive transition bound")
        self._maximum = maximum
        self._items: list[StateTransition] = []
        self._by_command: dict[str, StateTransition] = {}
        self._projection = self._initial
        for item in transitions:
            self.record(item)

    @property
    def production_id(self) -> str:
        return self._production_id

    @property
    def profile(self) -> TransitionProfile | None:
        return self._profile

    @property
    def initial(self) -> ProductionStateVector:
        return self._initial

    @property
    def current(self) -> ProductionStateVector:
        return self._projection

    @property
    def history(self) -> tuple[StateTransition, ...]:
        return tuple(self._items)

    @property
    def head_receipt_id(self) -> str | None:
        return None if not self._items else self._items[-1].receipt.transition_id

    def __len__(self) -> int:
        return len(self._items)

    def record(self, transition: Any) -> StateTransition:
        """Accept a proposed move, or return the one already recorded under its command."""

        wanted = StateTransition.coerce(transition, "transition")
        if wanted.production_id != self._production_id:
            raise LifecycleError(f"{self._production_id} cannot record a transition for {wanted.production_id}")
        duplicate = self._duplicate(wanted)
        if duplicate is not None:
            return duplicate
        if len(self._items) >= self._maximum:
            raise LifecycleError(
                f"{self._production_id} already holds {self._maximum} transitions, the admitted bound; a "
                "production with more history than that is a different production"
            )
        if self._profile is not None and wanted.profile is not None and wanted.profile != self._profile:
            raise LifecycleError(
                f"{self._production_id} is governed by profile {self._profile.profile_id}, not "
                f"{wanted.profile.profile_id}; change the profile by starting a new production, never mid-history"
            )
        if self._profile is not None and wanted.profile is None:
            wanted = replace(wanted, profile=self._profile)
        if wanted.receipt.causal_parent_receipt_id != self.head_receipt_id:
            raise LifecycleError(
                f"{wanted.transition_id} cites parent {wanted.receipt.causal_parent_receipt_id!r} while the head is "
                f"{self.head_receipt_id!r}; history is appended, not spliced in"
            )
        if wanted.from_vector != self._projection:
            raise LifecycleError(
                f"{wanted.transition_id} starts from {wanted.from_vector.phase.value} while this ledger is at "
                f"{self._projection.phase.value}; re-read the state and propose again"
            )
        self._items.append(wanted)
        if wanted.receipt.command_id is not None:
            self._by_command[wanted.receipt.command_id] = wanted
        self._projection = wanted.to_vector
        return wanted

    def _duplicate(self, wanted: StateTransition) -> StateTransition | None:
        """Same command, same meaning: hand back the first receipt. Same command, new meaning: refuse."""

        command = wanted.receipt.command_id
        if command is None:
            return None
        found = self._by_command.get(command)
        if found is None:
            return None
        mismatch = wanted.receipt.conflicts_with(found.receipt)
        if mismatch is not None:
            raise StoreConflictError(f"command {command} is already recorded: {mismatch}")
        if found.to_vector != wanted.to_vector:
            raise StoreConflictError(
                f"command {command} was already recorded and moved the vector to "
                f"{found.to_vector.phase.value}, not {wanted.to_vector.phase.value}"
            )
        return found

    def advance(self, **changes: Any) -> StateTransition:
        """Build and record the next move, with the causal parent this ledger owes it.

        A command this ledger already honoured is replayed from the vector that command
        actually moved, never from the current projection. A retry is a delivery accident
        asking for the first answer again; re-deriving it from the projection would make
        the same command change nothing the second time and refuse to be idempotent.
        """

        actor = changes.pop("actor", None)
        if actor is None:
            raise LifecycleError("a state transition names the actor that made it; nobody did")
        profile = changes.pop("profile", None)
        command_id = changes.get("command_id")
        seen = None if not isinstance(command_id, str) else self._by_command.get(command_id)
        try:
            proposal = advance(
                self._projection if seen is None else seen.from_vector,
                actor=actor,
                profile=profile if profile is not None else self._profile,
                parent_receipt_id=self.head_receipt_id if seen is None else seen.receipt.causal_parent_receipt_id,
                **changes,
            )
        except ProjectOSError as error:
            if seen is None:
                raise
            # The caller is retrying a command this ledger already honoured, so the collision is the
            # fact worth reporting. A rebuild that no longer describes a legal move is only evidence
            # that this retry does not mean the original command.
            raise StoreConflictError(
                f"command {command_id} is already recorded as {seen.transition_id} and the changes proposed now do "
                f"not describe it either: {error}"
            ) from error
        return self.record(proposal)

    def replay(self) -> ProductionStateVector:
        """Recompute the state from the initial vector and every recorded move, in order."""

        state = self._initial
        for step, wanted in enumerate(self._items, start=1):
            if wanted.from_vector != state:
                raise LifecycleError(
                    f"{self._production_id}: transition {step} ({wanted.transition_id}) starts from "
                    f"{wanted.from_vector.phase.value} while the history before it ends at {state.phase.value}; "
                    "the recorded chain no longer describes itself"
                )
            state = wanted.to_vector
        return state

    def prove_state(self) -> StateProof:
        """The durable-replay evidence: projection and recomputation, side by side."""

        replayed = self.replay()
        return StateProof(
            production_id=self._production_id,
            recorded_state=canonical_json(self._projection.to_payload()),
            replayed_state=canonical_json(replayed.to_payload()),
            transitions=len(self._items),
            head_receipt_id=self.head_receipt_id,
        )

    def completion(self, profile: Any, *, open_blockers: Iterable[Any] = ()) -> CompletionProfile:
        """The profile-derived COMPLETED claim about the current state, satisfied or not."""

        return completion_of(self._projection, profile, open_blockers=open_blockers)
