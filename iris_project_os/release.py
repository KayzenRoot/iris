"""Área E part 3: the release transaction, external ambiguity, withdrawal and supersession.

§15 of the module spec describes a release as a governed transaction with six phases, and
§3 makes ACCEPTED -> RELEASED a judgement that owes delivery evidence. This module keeps those
two claims apart: the promotion decides that a release is admissible, and the transaction here
records what actually happened to a package in the outside world. Nothing in this file decides
quality, and nothing here lets an external fact be implied.

Three laws do the work.

*State is never implied.* A phase move into STAGED, RECEIPTED or PUBLISHED carries the refs that
prove it, and an ``ExternalAction`` that claims to have landed names the remote receipt it was
read from (§15.5).

*Ambiguity is a recorded state, not a retry permission.* When a submit times out with the remote
state unknown, the transaction moves to ``UNKNOWN`` and stays there until a
``ReconciliationReport`` says what an inspection of the destination found. Which is why
``EXTERNAL_MUTATION`` actions require an idempotency key: without one, a retry is a second
publish wearing the first one's clothes (D-M02-S05-011).

*Withdrawal is not deletion.* A ``WithdrawalReceipt`` is appended beside the release it recalls.
The published step stays in history, the exact snapshot ref stays exact, and supersession only
ever changes which release a *future* consumer is pointed at (D-M02-S05-012, D-M02-S05-013).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .base import Labeled, Record, of
from .errors import ProjectOSError, ReleaseError, SchemaValidationError, StoreConflictError
from .graph import SideEffectClass
from .identity import (
    EntityKind,
    ExternalRef,
    SupersessionLedger,
    SupersessionRef,
    TransitionReceipt,
    new_id,
    require_id,
)
from .lifecycle import Phase, ProductionLedger, ReleaseCondition
from .limits import (
    MAX_BUNDLE_ITEMS,
    MAX_DESTINATIONS,
    MAX_RECEIPT_EVIDENCE,
    MAX_RELEASE_STEPS,
)
from .machines import StateMachine
from .promotion import GateKind, PromotionDecision, PromotionRequest, admit_promotion, HumanApproval
from .snapshots import ExternalEffectState
from .versions import (
    CONTRACT_VERSION,
    ComponentVersion,
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
    "ReleasePhase",
    "RELEASE_LAW",
    "ACTION_LAW",
    "WithdrawalReason",
    "WithdrawalState",
    "RemoteState",
    "ExternalAction",
    "ReconciliationReport",
    "ReleaseTransaction",
    "ReleaseStep",
    "WithdrawalReceipt",
    "ReleaseLedger",
    "ReleaseRegistry",
    "begin_release",
    "sync_release_state",
]


class ReleasePhase(Labeled):
    """§15's six phases plus the one state an unproven submit leaves the transaction in.

    ``UNKNOWN`` is a phase rather than a flag because §15 says the *transaction* becomes
    UNKNOWN/BLOCKED for reconciliation: making it a boolean would let a caller advance past
    an unresolved submit while leaving the flag set, which is exactly the blind retry the
    decision forbids.
    """

    PREPARING = "PREPARING"
    GATED = "GATED"
    STAGED = "STAGED"
    SUBMITTED = "SUBMITTED"
    RECEIPTED = "RECEIPTED"
    PUBLISHED = "PUBLISHED"
    UNKNOWN = "UNKNOWN"

    @property
    def touches_destination(self) -> bool:
        """Whether work at this phase may already have been seen outside the kernel."""

        return self in {
            ReleasePhase.SUBMITTED,
            ReleasePhase.RECEIPTED,
            ReleasePhase.PUBLISHED,
            ReleasePhase.UNKNOWN,
        }


class WithdrawalReason(Labeled):
    """§16's five admitted causes for taking public content back."""

    LEGAL_RIGHTS = "LEGAL_RIGHTS"
    QUALITY_DEFECT = "QUALITY_DEFECT"
    SECURITY_PRIVACY = "SECURITY_PRIVACY"
    CAMPAIGN_STOP = "CAMPAIGN_STOP"
    SUPERSEDING_RELEASE = "SUPERSEDING_RELEASE"


class RemoteState(Labeled):
    """What an inspection of the destination concluded. ``STILL_UNKNOWN`` resolves nothing."""

    LANDED = "LANDED"
    NOT_LANDED = "NOT_LANDED"
    STILL_UNKNOWN = "STILL_UNKNOWN"


class WithdrawalState(Labeled):
    """The destination state a withdrawal left behind, derived from its actions."""

    WITHDRAWN = "WITHDRAWN"
    PARTIAL = "PARTIAL"
    UNRESOLVED = "UNRESOLVED"
    STILL_PUBLIC = "STILL_PUBLIC"


RELEASE_LAW = StateMachine(
    name="release-transaction",
    state_type=ReleasePhase,
    transitions={
        ReleasePhase.PREPARING: (ReleasePhase.GATED, ReleasePhase.UNKNOWN),
        ReleasePhase.GATED: (ReleasePhase.STAGED, ReleasePhase.UNKNOWN),
        ReleasePhase.STAGED: (ReleasePhase.SUBMITTED, ReleasePhase.UNKNOWN),
        ReleasePhase.SUBMITTED: (ReleasePhase.RECEIPTED, ReleasePhase.UNKNOWN),
        ReleasePhase.RECEIPTED: (ReleasePhase.PUBLISHED, ReleasePhase.UNKNOWN),
        ReleasePhase.PUBLISHED: (),
        # Out of ambiguity there is only one of two inspected answers: the package is on the
        # destination, so the receipts are recorded, or it is not, so the package is staged
        # again. Publication itself stays behind the receipt step in both cases.
        ReleasePhase.UNKNOWN: (ReleasePhase.STAGED, ReleasePhase.RECEIPTED),
    },
)

#: What an outside party may come to know about one request. Re-listing an action is how
#: evidence arrives; rewriting it is how a duplicate publish hides behind an old id.
ACTION_LAW = StateMachine(
    name="external-action",
    state_type=ExternalEffectState,
    transitions={
        ExternalEffectState.NOT_APPLIED: (
            ExternalEffectState.RECONCILIATION_REQUIRED,
            ExternalEffectState.APPLIED,
            ExternalEffectState.COMPENSATED,
        ),
        ExternalEffectState.RECONCILIATION_REQUIRED: (
            ExternalEffectState.NOT_APPLIED,
            ExternalEffectState.APPLIED,
            ExternalEffectState.COMPENSATED,
        ),
        ExternalEffectState.APPLIED: (ExternalEffectState.COMPENSATED,),
        ExternalEffectState.COMPENSATED: (),
        ExternalEffectState.IRREVERSIBLE: (),
    },
)


def _refs(values: Iterable[Any], field_name: str, *, maximum: int = MAX_RECEIPT_EVIDENCE) -> tuple[ExternalRef, ...]:
    collected = require_bounded(values, field_name, maximum=maximum, kind="ref")
    return tuple(ExternalRef.coerce(item, f"{field_name}[]") for item in collected)


def _actions(values: Any, field_name: str) -> tuple["ExternalAction", ...]:
    collected = require_bounded(values, field_name, maximum=MAX_DESTINATIONS, kind="external action")
    return tuple(ExternalAction.coerce(item, f"{field_name}[]") for item in collected)


def _require_destination(value: Any, field_name: str) -> ExternalRef:
    resolved = ExternalRef.coerce(value, field_name)
    if resolved.kind is not EntityKind.DESTINATION:
        raise ReleaseError(
            f"{field_name} must point at a DESTINATION, got {resolved.kind.value}; a release is a claim about "
            "somewhere else, and naming a policy instead would leave the destination unknown"
        )
    return resolved


@dataclass(frozen=True)
class ExternalAction(Record):
    """One mutation the outside world was asked to perform, and what is known about it.

    The state here is the whole point: ``APPLIED`` without a remote receipt is a hope, and
    ``RECONCILIATION_REQUIRED`` with one is a contradiction. So each state carries the proof
    its name claims and none of the ones it does not.
    """

    action_id: str
    destination: ExternalRef
    state: ExternalEffectState
    kind: SideEffectClass
    idempotency_key: Any = None
    external_receipt_ref: Any = None
    compensation_receipt_ref: Any = None
    evidence_refs: tuple[ExternalRef, ...] = ()
    observed_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "destination": of(ExternalRef),
        "external_receipt_ref": of(ExternalRef),
        "compensation_receipt_ref": of(ExternalRef),
        "evidence_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "action_id", require_id(self.action_id, "action_id"))
        object.__setattr__(self, "destination", _require_destination(self.destination, "destination"))
        object.__setattr__(self, "state", ExternalEffectState.parse(self.state, "state"))
        object.__setattr__(self, "kind", SideEffectClass.parse(self.kind, "kind"))
        if self.kind.requires_policy and self.idempotency_key is None:
            raise ReleaseError(
                f"{self.action_id} mutates outside and carries no idempotency key; §15 forbids a retry that "
                "cannot be recognised as the same request"
            )
        if self.idempotency_key is not None:
            object.__setattr__(self, "idempotency_key", require_text(self.idempotency_key, "idempotency_key", maximum=128))
        for name in ("external_receipt_ref", "compensation_receipt_ref"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, ExternalRef.coerce(value, name))
        object.__setattr__(self, "evidence_refs", _refs(self.evidence_refs, "evidence_refs"))
        object.__setattr__(self, "observed_at_ms", require_millis(self.observed_at_ms, "observed_at_ms"))
        self._require_state_worth_its_name()
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    def _require_state_worth_its_name(self) -> None:
        if self.state in {ExternalEffectState.APPLIED, ExternalEffectState.IRREVERSIBLE}:
            if self.external_receipt_ref is None:
                raise ReleaseError(
                    f"{self.action_id} reports {self.state.value} with no remote receipt; §15 records external "
                    "identifiers because a submit that timed out and a submit that landed look identical"
                )
        elif self.external_receipt_ref is not None:
            raise ReleaseError(
                f"{self.action_id} cites a remote receipt while reporting {self.state.value}; a receipt is proof "
                "of landing, so the state is no longer what it says"
            )
        if self.state is ExternalEffectState.RECONCILIATION_REQUIRED:
            if self.idempotency_key is None:
                raise ReleaseError(
                    f"{self.action_id} is unresolved and carries no idempotency key, so an inspection could never "
                    "match it to what the destination reports"
                )
            if self.compensation_receipt_ref is None:
                return
            raise ReleaseError(
                f"{self.action_id} claims reconciliation is required and also already compensated"
            )
        if self.state is ExternalEffectState.COMPENSATED and self.compensation_receipt_ref is None:
            raise ReleaseError(
                f"{self.action_id} claims COMPENSATED without the receipt that proves the compensation ran"
            )

    @property
    def landed(self) -> bool:
        return self.state in {ExternalEffectState.APPLIED, ExternalEffectState.IRREVERSIBLE}

    @property
    def unresolved(self) -> bool:
        return self.state is ExternalEffectState.RECONCILIATION_REQUIRED

    @property
    def settled(self) -> bool:
        return self.state in {ExternalEffectState.NOT_APPLIED, ExternalEffectState.COMPENSATED}

    @property
    def reference(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.RECEIPT, reference=self.action_id)

    def reopens(self, earlier: "ExternalAction") -> bool:
        """Whether this action is the same request an earlier unresolved one already made."""

        return (
            self.idempotency_key is not None
            and earlier.idempotency_key == self.idempotency_key
        )


@dataclass(frozen=True)
class ReconciliationReport(Record):
    """What an inspection of the destination actually found, before anyone retries.

    §15 requires the inspection to happen between the ambiguity and the retry, so this record
    exists to be the difference between a report and a resubmission. A report that concludes
    ``STILL_UNKNOWN`` is honest and useless in exactly the right way: it keeps the transaction
    where it was.
    """

    report_id: str
    release_id: str
    destination: ExternalRef
    inspector: ComponentVersion
    outcome: RemoteState
    inspected_at_ms: int = 0
    remote_reference: Any = None
    evidence_refs: tuple[ExternalRef, ...] = ()
    statement: Any = None
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "destination": of(ExternalRef),
        "inspector": of(ComponentVersion),
        "remote_reference": of(ExternalRef),
        "evidence_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_id", require_id(self.report_id, "report_id"))
        object.__setattr__(self, "release_id", require_id(self.release_id, "release_id"))
        object.__setattr__(self, "destination", _require_destination(self.destination, "destination"))
        object.__setattr__(self, "inspector", require_component_version(self.inspector, "inspector"))
        object.__setattr__(self, "outcome", RemoteState.parse(self.outcome, "outcome"))
        object.__setattr__(self, "inspected_at_ms", require_millis(self.inspected_at_ms, "inspected_at_ms"))
        if self.remote_reference is not None:
            object.__setattr__(self, "remote_reference", ExternalRef.coerce(self.remote_reference, "remote_reference"))
        object.__setattr__(self, "evidence_refs", _refs(self.evidence_refs, "evidence_refs"))
        if not self.evidence_refs:
            raise ReleaseError(
                f"{self.report_id} inspects a destination and cites nothing; an unreported look is a retry "
                "with better paperwork"
            )
        object.__setattr__(self, "statement", require_optional_text(self.statement, "statement", maximum=512))
        if self.outcome is RemoteState.LANDED and self.remote_reference is None:
            raise ReleaseError(
                f"{self.report_id} found the package on the destination and cannot name it"
            )
        if self.outcome is RemoteState.NOT_LANDED and self.remote_reference is not None:
            raise ReleaseError(
                f"{self.report_id} says nothing landed while citing {self.remote_reference.reference}"
            )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def resolves(self) -> bool:
        return self.outcome is not RemoteState.STILL_UNKNOWN

    def justifies(self, target: ReleasePhase) -> bool:
        """Whether this finding is the one that lets the transaction move to ``target``."""

        if not self.resolves:
            return False
        if target is ReleasePhase.RECEIPTED:
            return self.outcome is RemoteState.LANDED
        if target is ReleasePhase.STAGED:
            return self.outcome is RemoteState.NOT_LANDED
        return False

    @property
    def reference(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.RECEIPT, reference=self.report_id)


@dataclass(frozen=True)
class ReleaseTransaction(Record):
    """§15.1's immutable declaration: which accepted candidate, which release snapshot, where.

    The transaction holds the claims and never a phase. Phases are history, so they live in
    the steps appended against this identity, which is also what lets two observers replay the
    same release to the same conclusion.
    """

    release_id: str
    production_id: str
    candidate_snapshot_id: str
    release_snapshot_id: str
    destination: ExternalRef
    actor: ComponentVersion
    project_id: Any = None
    promotion_bundle_ref: Any = None
    policy_refs: tuple[ExternalRef, ...] = ()
    reproducibility_ref: Any = None
    prepared_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "destination": of(ExternalRef),
        "actor": of(ComponentVersion),
        "promotion_bundle_ref": of(ExternalRef),
        "policy_refs": of(ExternalRef),
        "reproducibility_ref": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "release_id", require_id(self.release_id, "release_id"))
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        object.__setattr__(self, "candidate_snapshot_id", require_id(self.candidate_snapshot_id, "candidate_snapshot_id"))
        object.__setattr__(self, "release_snapshot_id", require_id(self.release_snapshot_id, "release_snapshot_id"))
        if self.release_snapshot_id == self.candidate_snapshot_id:
            raise ReleaseError(
                f"{self.release_id} releases the candidate snapshot unchanged; §15.1 prepares an immutable "
                "Release Snapshot, which is a package, not the file that was judged"
            )
        if self.project_id is not None:
            object.__setattr__(self, "project_id", require_identifier(self.project_id, "project_id"))
        object.__setattr__(self, "destination", _require_destination(self.destination, "destination"))
        object.__setattr__(self, "actor", require_component_version(self.actor, "actor"))
        if self.promotion_bundle_ref is not None:
            resolved = ExternalRef.coerce(self.promotion_bundle_ref, "promotion_bundle_ref")
            if resolved.kind is not EntityKind.EVIDENCE:
                raise ReleaseError(
                    f"{self.release_id} cites {resolved.kind.value} as the promotion evidence that admits its "
                    "release; only a §8 bundle carries that claim"
                )
            object.__setattr__(self, "promotion_bundle_ref", resolved)
        object.__setattr__(self, "policy_refs", _refs(self.policy_refs, "policy_refs", maximum=MAX_BUNDLE_ITEMS))
        if self.reproducibility_ref is not None:
            object.__setattr__(self, "reproducibility_ref", ExternalRef.coerce(self.reproducibility_ref, "reproducibility_ref"))
        object.__setattr__(self, "prepared_at_ms", require_millis(self.prepared_at_ms, "prepared_at_ms"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def reference(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.RELEASE, reference=self.release_id)

    @property
    def snapshot_ref(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.SNAPSHOT, reference=self.release_snapshot_id)

    def delivery_evidence(self) -> tuple[ExternalRef, ...]:
        """What a DELIVERY gate may cite about this release: the package and where it goes.

        Provenance stays with the release snapshot rather than with a status string, because
        the §3 acceptance list asks for delivery evidence and a destination, not for assurance.
        """

        return (self.reference, self.snapshot_ref, self.destination)


@dataclass(frozen=True)
class ReleaseStep(Record):
    """One recorded move of a release transaction, with the receipt that proves it."""

    step_id: str
    release_id: str
    production_id: str
    from_phase: ReleasePhase
    to_phase: ReleasePhase
    receipt: TransitionReceipt
    actions: tuple[ExternalAction, ...] = ()
    report: Any = None
    evidence_refs: tuple[ExternalRef, ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "receipt": of(TransitionReceipt),
        "actions": of(ExternalAction),
        "report": of(ReconciliationReport),
        "evidence_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_id", require_id(self.step_id, "step_id"))
        object.__setattr__(self, "release_id", require_id(self.release_id, "release_id"))
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        object.__setattr__(self, "from_phase", ReleasePhase.parse(self.from_phase, "from_phase"))
        object.__setattr__(self, "to_phase", ReleasePhase.parse(self.to_phase, "to_phase"))
        if not isinstance(self.receipt, TransitionReceipt):
            raise SchemaValidationError("ReleaseStep expects a TransitionReceipt as its durable proof")
        RELEASE_LAW.require(self.from_phase, self.to_phase, reason=self.receipt.reason_code)
        if self.receipt.entity_kind is not EntityKind.RELEASE:
            raise ReleaseError(
                f"{self.step_id} is recorded as {self.receipt.entity_kind.value}; a release step is proof about a "
                "RELEASE, and any other kind is someone else's history"
            )
        if self.receipt.entity_id != self.release_id:
            raise ReleaseError(
                f"{self.step_id}'s receipt proves {self.receipt.entity_id}, not the release it is filed under"
            )
        if self.receipt.from_state != self.from_phase.value or self.receipt.to_state != self.to_phase.value:
            raise ReleaseError(
                f"{self.step_id} records {self.from_phase.value} -> {self.to_phase.value} while its receipt signs "
                f"{self.receipt.from_state} -> {self.receipt.to_state}; the step and the durable proof it carries "
                "have to describe the same move, or replay is being trusted over what was never signed"
            )
        object.__setattr__(self, "actions", _actions(self.actions, "actions"))
        if self.report is not None:
            resolved_report = ReconciliationReport.coerce(self.report, "report")
            if resolved_report.release_id != self.release_id:
                raise ReleaseError(
                    f"{self.step_id} carries a reconciliation report about release {resolved_report.release_id}"
                )
            object.__setattr__(self, "report", resolved_report)
        object.__setattr__(self, "evidence_refs", _refs(self.evidence_refs, "evidence_refs"))
        self._require_what_the_target_claims()
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    def _require_what_the_target_claims(self) -> None:
        """Each target phase owes the evidence its own name states (§15)."""

        if self.to_phase is ReleasePhase.GATED and not self.evidence_refs:
            raise ReleaseError(
                f"{self.step_id} validates the release gate set and cites no decision; a gate nobody answered is "
                "how an unchecked release becomes a published one"
            )
        if self.to_phase is ReleasePhase.STAGED and self.report is None:
            if not self._staged_package:
                raise ReleaseError(
                    f"{self.step_id} stages a package and names nothing: §15.3 stages artifacts, so a staged step "
                    "with no artifact or release ref staged nothing"
                )
        if self.to_phase is ReleasePhase.SUBMITTED:
            if not self.actions:
                raise ReleaseError(
                    f"{self.step_id} enters SUBMITTED with no external action; §15.4 executes side effects, and an "
                    "empty list is a different claim from the one the phase makes"
                )
            if any(item.landed for item in self.actions):
                raise ReleaseError(
                    f"{self.step_id} enters SUBMITTED carrying an action that already landed; the receipt belongs "
                    "to the step that records it, which is the next one"
                )
        if self.to_phase is ReleasePhase.RECEIPTED:
            if not self.actions and self.report is None:
                raise ReleaseError(
                    f"{self.step_id} records external receipts while citing no action to receipt"
                )
            if any(item.unresolved for item in self.actions):
                raise ReleaseError(
                    f"{self.step_id} receipts an action that is still unresolved; §15 sends that to reconciliation, "
                    "not to the next phase"
                )
        if self.to_phase is ReleasePhase.PUBLISHED:
            if any(item.unresolved for item in self.actions):
                raise ReleaseError(
                    f"{self.step_id} publishes over an unresolved external action"
                )
            if not any(item.landed for item in self.actions):
                raise ReleaseError(
                    f"{self.step_id} publishes without success criteria proven; §15.6 makes publication the last "
                    "claim of a transaction, never a way of making an earlier one"
                )
        if self.to_phase is ReleasePhase.UNKNOWN:
            if not any(item.unresolved for item in self.actions):
                raise ReleaseError(
                    f"{self.step_id} calls the external state unknown while every action it carries is settled; "
                    "ambiguity is reported by an action, not chosen for comfort"
                )
        if self.from_phase is ReleasePhase.UNKNOWN:
            if self.report is None:
                raise ReleaseError(
                    f"{self.step_id} leaves UNKNOWN on nothing; §15 requires the destination to be inspected before "
                    "anything is retried"
                )
            if not self.report.justifies(self.to_phase):
                raise ReleaseError(
                    f"{self.step_id} reads a report concluding {self.report.outcome.value} and moves to "
                    f"{self.to_phase.value}; the inspection decided the destination, not this step"
                )

    @property
    def _staged_package(self) -> bool:
        admitted = {EntityKind.ARTIFACT, EntityKind.RELEASE, EntityKind.SNAPSHOT}
        return any(item.kind in admitted for item in self.evidence_refs)

    @property
    def causal_parent_receipt_id(self) -> Any:
        return self.receipt.causal_parent_receipt_id

    @property
    def command_id(self) -> Any:
        return self.receipt.command_id

    def conflicts_with(self, other: "ReleaseStep") -> Any:
        return self.receipt.conflicts_with(other.receipt)


@dataclass(frozen=True)
class WithdrawalReceipt(Record):
    """§16's receipt: which release came down, why, and what the destination now says.

    ``destination_state`` is derived from the requested actions instead of declared, because
    the sentence a withdrawal receipt exists to support is "we asked, and here is what
    happened", which is not the same sentence as "we asked".
    """

    withdrawal_id: str
    release_id: str
    production_id: str
    release_snapshot_id: str
    reason: WithdrawalReason
    actor: ComponentVersion
    requested_actions: tuple[ExternalAction, ...] = ()
    provenance_refs: tuple[ExternalRef, ...] = ()
    replacement_ref: Any = None
    statement: Any = None
    confirmed_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "actor": of(ComponentVersion),
        "requested_actions": of(ExternalAction),
        "provenance_refs": of(ExternalRef),
        "replacement_ref": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "withdrawal_id", require_id(self.withdrawal_id, "withdrawal_id"))
        object.__setattr__(self, "release_id", require_id(self.release_id, "release_id"))
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        object.__setattr__(
            self, "release_snapshot_id", require_id(self.release_snapshot_id, "release_snapshot_id")
        )
        object.__setattr__(self, "reason", WithdrawalReason.parse(self.reason, "reason"))
        object.__setattr__(self, "actor", require_component_version(self.actor, "actor"))
        object.__setattr__(
            self,
            "requested_actions",
            _actions(self.requested_actions, "requested_actions"),
        )
        if not self.requested_actions:
            raise ReleaseError(
                f"withdrawal {self.withdrawal_id} recalls a release and asks for nothing; a withdrawal that "
                "requests no action is an opinion about a destination"
            )
        provenance = _refs(self.provenance_refs, "provenance_refs")
        if not provenance:
            raise ReleaseError(
                f"withdrawal {self.withdrawal_id} omits the provenance it is supposed to preserve; §16 keeps "
                "historical provenance under retention policy, and a receipt that cites none preserves nothing"
            )
        object.__setattr__(self, "provenance_refs", provenance)
        if self.replacement_ref is not None:
            object.__setattr__(self, "replacement_ref", ExternalRef.coerce(self.replacement_ref, "replacement_ref"))
        if self.reason is WithdrawalReason.SUPERSEDING_RELEASE and self.replacement_ref is None:
            raise ReleaseError(
                f"withdrawal {self.withdrawal_id} supersedes a release and names no replacement"
            )
        object.__setattr__(self, "statement", require_optional_text(self.statement, "statement", maximum=512))
        object.__setattr__(self, "confirmed_at_ms", require_millis(self.confirmed_at_ms, "confirmed_at_ms"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def destination_state(self) -> WithdrawalState:
        landed = [item for item in self.requested_actions if item.landed]
        if any(item.unresolved for item in self.requested_actions):
            return WithdrawalState.UNRESOLVED
        if len(landed) == len(self.requested_actions):
            return WithdrawalState.WITHDRAWN
        if landed:
            return WithdrawalState.PARTIAL
        return WithdrawalState.STILL_PUBLIC

    @property
    def reference(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.RECEIPT, reference=self.withdrawal_id)


class ReleaseLedger:
    """The ordered receipts of one release transaction, replayable to its phase.

    The same law ``ProductionLedger`` runs: history is appended, a causal parent is the current
    head, and a command already honoured is answered from history instead of being performed
    twice (§25, D-M02-S05-018). What is added here is the retry fence: an idempotency key that
    is still unresolved cannot be reused until a report says what the destination holds.
    """

    def __init__(
        self,
        transaction: Any,
        steps: Iterable[Any] = (),
        *,
        withdrawals: Iterable[Any] = (),
        maximum: int = MAX_RELEASE_STEPS,
    ) -> None:
        self._transaction = ReleaseTransaction.coerce(transaction, "transaction")
        resolved = require_bounded(steps, "steps", maximum=maximum, kind="release step")
        self._maximum = maximum
        self._items: list[ReleaseStep] = []
        self._by_command: dict[str, ReleaseStep] = {}
        self._withdrawals: dict[str, WithdrawalReceipt] = {}
        self._reports: dict[str, ReconciliationReport] = {}
        self._phase = ReleasePhase.PREPARING
        self._head: str | None = None
        for wanted in resolved:
            self.record(ReleaseStep.coerce(wanted, "step"))
        for wanted in withdrawals:
            self.withdraw(wanted)

    @property
    def transaction(self) -> ReleaseTransaction:
        return self._transaction

    @property
    def release_id(self) -> str:
        return self._transaction.release_id

    @property
    def production_id(self) -> str:
        return self._transaction.production_id

    @property
    def phase(self) -> ReleasePhase:
        return self._phase

    @property
    def head_receipt_id(self) -> str | None:
        return self._head

    @property
    def steps(self) -> tuple[ReleaseStep, ...]:
        return tuple(self._items)

    @property
    def withdrawals(self) -> tuple[WithdrawalReceipt, ...]:
        return tuple(self._withdrawals.values())

    @property
    def reports(self) -> tuple[ReconciliationReport, ...]:
        """Every inspection ever filed against this release, including the ones that proved nothing."""

        return tuple(self._reports.values())

    @property
    def is_withdrawn(self) -> bool:
        return any(item.destination_state is WithdrawalState.WITHDRAWN for item in self._withdrawals.values())

    def __len__(self) -> int:
        return len(self._items)

    def actions(self) -> tuple[ExternalAction, ...]:
        """Every external action this release has ever asked of any destination."""

        return tuple(item for step in self._items for item in step.actions)

    def current_actions(self) -> tuple[ExternalAction, ...]:
        """What is known about each action now: the last listing of each action id."""

        latest: dict[str, ExternalAction] = {}
        for item in self.actions():
            latest[item.action_id] = item
        return tuple(latest.values())

    def record(self, wanted: ReleaseStep) -> ReleaseStep:
        if not isinstance(wanted, ReleaseStep):
            wanted = ReleaseStep.coerce(wanted, "step")
        if wanted.release_id != self.release_id:
            raise ReleaseError(
                f"{wanted.step_id} belongs to release {wanted.release_id} and cannot be recorded on {self.release_id}"
            )
        if wanted.production_id != self.production_id:
            raise ReleaseError(
                f"{wanted.step_id} proves a move of production {wanted.production_id} on the release ledger of "
                f"{self.production_id}"
            )
        duplicate = self._duplicate(wanted)
        if duplicate is not None:
            return duplicate
        if len(self._items) >= self._maximum:
            raise ReleaseError(
                f"{self.release_id} exceeds the admitted {self._maximum} release steps; a release that needs more "
                "is a workflow, and workflows are M05's claim"
            )
        self._require_chain(wanted)
        self._items.append(wanted)
        if wanted.command_id is not None:
            self._by_command[wanted.command_id] = wanted
        self._phase = wanted.to_phase
        self._head = wanted.receipt.transition_id
        return wanted

    def _duplicate(self, wanted: ReleaseStep) -> ReleaseStep | None:
        """A command already honoured is answered from history; a command with a new meaning is a conflict.

        This runs before the chain checks on purpose. A retry arrives with the state the
        destination left behind, not with the state this ledger already moved past, so asking
        it to describe the current head first would turn an accident into a refusal.
        """

        command = wanted.command_id
        if command is None:
            return None
        earlier = self._by_command.get(command)
        if earlier is None:
            return None
        conflict = wanted.conflicts_with(earlier)
        if conflict is not None:
            raise StoreConflictError(f"command {command} is already recorded: {conflict}")
        if earlier != wanted:
            raise StoreConflictError(
                f"command {command} was already recorded as {earlier.step_id} and this is not that step"
            )
        return earlier

    def _require_chain(self, wanted: ReleaseStep) -> None:
        if wanted.from_phase is not self._phase:
            raise ReleaseError(
                f"{wanted.step_id} starts from {wanted.from_phase.value} while this release stands at "
                f"{self._phase.value}; history is appended, not spliced in"
            )
        if wanted.receipt.causal_parent_receipt_id != self._head:
            raise ReleaseError(
                f"{wanted.step_id} cites parent {wanted.receipt.causal_parent_receipt_id!r} while the head is "
                f"{self._head!r}"
            )
        self._require_no_blind_retry(wanted)
        self._require_nothing_left_ambiguous(wanted)
        self._require_destination_untouched(wanted)

    def _require_nothing_left_ambiguous(self, wanted: ReleaseStep) -> None:
        """Every step other than the one that raises an ambiguity has to answer it.

        Only the actions a step re-lists can change what is known, so a step that moves on
        without naming one inherits whatever it left behind. That is how a release reaches
        RECEIPTED with an unpublished submit still unanswered on file.
        """

        if wanted.to_phase is ReleasePhase.UNKNOWN:
            return
        relisted = {item.action_id: item for item in wanted.actions}
        for prior in self.current_actions():
            known = relisted.get(prior.action_id, prior)
            if known.unresolved:
                raise ReleaseError(
                    f"{wanted.step_id} moves {self.release_id} to {wanted.to_phase.value} while {prior.action_id} is "
                    "still unresolved; §15 keeps the transaction in UNKNOWN until an inspection answers it"
                )

    def _require_no_blind_retry(self, wanted: ReleaseStep) -> None:
        """§15's second and third sentences, stated as a fence on the ledger.

        Re-listing an action id is evidence arriving about a request already made, so it is
        checked against the progression law instead of refused. A *new* action id carrying a
        key that is still unresolved, or one that already landed, is the retry §15 forbids.
        """

        on_file = {item.action_id: item for item in self.actions()}
        for action in wanted.actions:
            earlier = on_file.get(action.action_id)
            if earlier is not None:
                self._require_progress(action, earlier)
                continue
            for prior in on_file.values():
                if prior.action_id == action.action_id or not action.reopens(prior):
                    continue
                if prior.unresolved:
                    raise ReleaseError(
                        f"action {action.action_id} reuses the key of {prior.action_id}, which is unresolved on this "
                        "ledger; record what the inspection found first, then re-issue, or the retry is blind"
                    )
                if prior.landed:
                    raise ReleaseError(
                        f"action {action.action_id} repeats {prior.action_id}, which already landed on this "
                        "destination; a second publish under one key is a duplicate, not a retry"
                    )

    def _require_progress(self, action: ExternalAction, earlier: ExternalAction) -> None:
        """An action id names one request: its identity never moves and its past is not rewritable."""

        for name in ("destination", "kind", "idempotency_key"):
            if getattr(action, name) != getattr(earlier, name):
                raise ReleaseError(
                    f"action {action.action_id} is re-listed with a different {name}; an id names the one request "
                    "made to one destination, never a slot to refill"
                )
        if earlier.state is action.state:
            if earlier.external_receipt_ref != action.external_receipt_ref:
                raise ReleaseError(
                    f"action {action.action_id} changed its remote receipt without changing its state; a receipt is "
                    "read from the destination, not chosen"
                )
            return
        if not ACTION_LAW.is_legal(earlier.state, action.state):
            raise ReleaseError(
                f"action {action.action_id} was {earlier.state.value} and is now re-listed as {action.state.value}; "
                "what the outside world already saw is not rewritable by a later step"
            )

    def _require_destination_untouched(self, wanted: ReleaseStep) -> None:
        wanted_destination = self._transaction.destination
        for action in wanted.actions:
            if action.destination != wanted_destination:
                raise ReleaseError(
                    f"{wanted.step_id} sends work to {action.destination.reference} while {self.release_id} was "
                    f"prepared for {wanted_destination.reference}; a release delivers to the destination it named"
                )
        if wanted.report is not None and wanted.report.destination != wanted_destination:
            raise ReleaseError(
                f"{wanted.step_id} reconciles {wanted.report.destination.reference}, which is not where "
                f"{self.release_id} was sent"
            )

    def advance(
        self,
        to_phase: Any,
        *,
        actor: Any = None,
        reason_code: str = "release-step",
        actions: Iterable[Any] = (),
        report: Any = None,
        evidence_refs: Iterable[Any] = (),
        command_id: str | None = None,
        step_id: str | None = None,
        parent_receipt_id: str | None = None,
        now_ms: int = 0,
    ) -> ReleaseStep:
        """Build and record the next move, with the causal parent this ledger owes it.

        A command this ledger already honoured is rebuilt from the phase that command actually
        left behind, never from the current projection: a retry is a delivery accident asking
        for the first answer again, and re-deriving it from the projection would either move
        the release twice or refuse to be idempotent.
        """

        wanted_phase = ReleasePhase.parse(to_phase, "to_phase")
        resolved_actor = actor if actor is not None else self._transaction.actor
        seen = None if command_id is None else self._by_command.get(command_id)
        # A retry is anchored where the original command was anchored, but carries the changes
        # actually proposed. Answering from history alone would let a submission that now means
        # something else be quietly satisfied by the first answer.
        anchor_phase = self._phase if seen is None else seen.from_phase
        anchor_parent = (
            self._head if seen is None else seen.causal_parent_receipt_id
        ) if parent_receipt_id is None else parent_receipt_id
        try:
            built = self._build(
                step_id or (seen.step_id if seen is not None else new_id()),
                resolved_actor,
                from_phase=anchor_phase,
                to_phase=wanted_phase,
                actions=tuple(actions),
                report=report,
                evidence_refs=tuple(evidence_refs),
                reason_code=reason_code,
                timestamp_ms=now_ms,
                parent_receipt_id=anchor_parent,
                command_id=command_id,
            )
        except ProjectOSError as error:
            if seen is None:
                raise
            raise StoreConflictError(
                f"command {command_id} is already recorded as {seen.step_id} and the changes proposed now do not "
                f"describe it either: {error}"
            ) from error
        return self.record(built)

    def _build(
        self,
        step_id: str,
        actor: Any,
        *,
        from_phase: ReleasePhase,
        to_phase: ReleasePhase,
        actions: tuple[Any, ...],
        report: Any,
        evidence_refs: tuple[Any, ...],
        reason_code: str,
        timestamp_ms: int,
        parent_receipt_id: str | None,
        command_id: str | None,
    ) -> ReleaseStep:
        command_digest = (
            content_digest(
                {
                    "to_phase": to_phase.value,
                    "actions": [item.to_payload() if hasattr(item, "to_payload") else item for item in actions],
                    "report": None if report is None else report.to_payload(),
                    "evidence_refs": [
                        item.to_payload() if hasattr(item, "to_payload") else item for item in evidence_refs
                    ],
                }
            )
            if command_id is not None
            else None
        )
        return ReleaseStep(
            step_id=step_id,
            release_id=self.release_id,
            production_id=self.production_id,
            from_phase=from_phase,
            to_phase=to_phase,
            receipt=TransitionReceipt(
                transition_id=step_id,
                entity_kind=EntityKind.RELEASE,
                entity_id=self.release_id,
                from_state=from_phase.value,
                to_state=to_phase.value,
                actor=require_component_version(actor, "actor"),
                reason_code=reason_code,
                timestamp_ms=timestamp_ms,
                causal_parent_receipt_id=parent_receipt_id,
                evidence_refs=tuple(ExternalRef.coerce(item, "evidence_refs[]") for item in evidence_refs),
                command_id=command_id,
                command_digest=command_digest,
            ),
            actions=tuple(ExternalAction.coerce(item, "actions[]") for item in actions),
            report=report,
            evidence_refs=tuple(ExternalRef.coerce(item, "evidence_refs[]") for item in evidence_refs),
        )

    def submit(
        self,
        actions: Iterable[Any],
        *,
        actor: Any = None,
        command_id: str | None = None,
        now_ms: int = 0,
        step_id: str | None = None,
    ) -> ReleaseStep:
        """§15.4: execute the external effects, or record that their outcome is unknown.

        Actions reported as unresolved move the transaction to ``UNKNOWN`` in the same step, so
        there is no window in which the kernel knows a submit is ambiguous and the state still
        says it is not.
        """

        collected = tuple(ExternalAction.coerce(item, "actions[]") for item in actions)
        if not collected:
            raise ReleaseError("submit with no actions publishes nothing; §15.4 performs external effects")
        ambiguous = any(item.unresolved for item in collected)
        return self.advance(
            ReleasePhase.UNKNOWN if ambiguous else ReleasePhase.SUBMITTED,
            actor=actor,
            actions=collected,
            command_id=command_id,
            step_id=step_id,
            reason_code="external-state-unknown" if ambiguous else "external-effects-submitted",
            now_ms=now_ms,
        )

    def reconcile(
        self,
        report: Any,
        *,
        actions: Iterable[Any] = (),
        actor: Any = None,
        now_ms: int = 0,
        step_id: str | None = None,
        command_id: str | None = None,
    ) -> ReleaseStep | None:
        """Answer an ambiguity with an inspection, or record that the inspection proved nothing.

        A ``STILL_UNKNOWN`` report is kept and moves nothing: it is the evidence that a retry
        was considered and rejected, which is what §15 asks for when it says IRIS must inspect
        before retrying. ``actions`` re-lists the requests the inspection explains, because the
        report says what the destination holds and only the re-listing moves that fact into the
        action's own state.
        """

        wanted = ReconciliationReport.coerce(report, "report")
        if wanted.destination != self._transaction.destination:
            raise ReleaseError(
                f"{wanted.report_id} inspects {wanted.destination.reference}, which is not where {self.release_id} "
                "was sent"
            )
        if self._phase is not ReleasePhase.UNKNOWN:
            raise ReleaseError(
                f"{self.release_id} is {self._phase.value}; reconciliation answers an ambiguity this release does "
                "not have"
            )
        existing = self._reports.get(wanted.report_id)
        if existing is not None and existing != wanted:
            raise StoreConflictError(
                f"report {wanted.report_id} is already recorded with a different conclusion"
            )
        self._reports[wanted.report_id] = wanted
        if not wanted.resolves:
            return None
        return self.advance(
            ReleasePhase.RECEIPTED if wanted.outcome is RemoteState.LANDED else ReleasePhase.STAGED,
            actor=actor,
            actions=tuple(actions),
            report=wanted,
            evidence_refs=(wanted.reference,),
            reason_code="reconciled",
            now_ms=now_ms,
            step_id=step_id,
            command_id=command_id,
        )

    def validate_gates(
        self,
        request: PromotionRequest,
        results: Iterable[Any],
        *,
        approvals: Iterable[Any] = (),
        now_ms: int = 0,
        command_id: str | None = None,
        step_id: str | None = None,
    ) -> tuple[ReleaseStep, PromotionDecision]:
        """§15.2: the release gate set is answered by the same promotion law as everything else.

        There is no second checker here. The request must be the one this release will cause,
        or the answers would be evidence about a different delivery.
        """

        if not isinstance(request, PromotionRequest):
            raise SchemaValidationError("validate_gates expects a PromotionRequest")
        if request.requested_phase is not Phase.RELEASED:
            raise ReleaseError(
                f"{request.request_id} asks for {request.requested_phase.value}; a release validates the gates of "
                "an ACCEPTED -> RELEASED promotion"
            )
        if request.production_id != self.production_id:
            raise ReleaseError(f"{request.request_id} answers the gates of another production's release")
        if request.candidate_snapshot_id != self._transaction.candidate_snapshot_id:
            raise ReleaseError(
                f"{request.request_id} judges candidate {request.candidate_snapshot_id} while {self.release_id} "
                f"packages {self._transaction.candidate_snapshot_id}"
            )
        if request.release_target != self._transaction.destination:
            raise ReleaseError(
                f"{request.request_id} names destination {request.release_target.reference} while "
                f"{self.release_id} was prepared for {self._transaction.destination.reference}"
            )
        decision = admit_promotion(
            request,
            results,
            approvals=tuple(HumanApproval.coerce(item, "approvals[]") for item in approvals),
            now_ms=now_ms,
        )
        if not decision.admitted:
            raise ReleaseError(
                f"{self.release_id} fails its release gates: {'; '.join(decision.blocking_reasons)}"
            )
        cited = (
            (ExternalRef(kind=EntityKind.EVIDENCE, reference=decision.decision_id),)
            + tuple(
                item
                for result in decision.gate_results
                if result.kind is GateKind.DELIVERY
                for item in result.evidence_refs
            )
        )
        step = self.advance(
            ReleasePhase.GATED,
            evidence_refs=tuple(dict.fromkeys(cited)),
            reason_code="release-gates-validated",
            command_id=command_id,
            step_id=step_id,
            now_ms=now_ms,
        )
        return step, decision

    def withdraw(
        self,
        receipt: Any,
        *,
        command_id: str | None = None,
    ) -> WithdrawalReceipt:
        """Append a recall beside the release. Nothing here is deleted, and nothing is undone.

        The phase stays where it got to, because the transaction did happen: §16 is explicit
        that a withdrawal is a new fact about the destination, not an eraser.
        """

        wanted = WithdrawalReceipt.coerce(receipt, "receipt")
        if wanted.release_id != self.release_id:
            raise ReleaseError(
                f"withdrawal {wanted.withdrawal_id} recalls release {wanted.release_id}, not {self.release_id}"
            )
        if wanted.production_id != self.production_id:
            raise ReleaseError(f"withdrawal {wanted.withdrawal_id} belongs to another production")
        if wanted.release_snapshot_id != self._transaction.release_snapshot_id:
            raise ReleaseError(
                f"withdrawal {wanted.withdrawal_id} preserves snapshot {wanted.release_snapshot_id} while "
                f"{self.release_id} published {self._transaction.release_snapshot_id}; §16 keeps the exact release, "
                "so citing a different one would withdraw something else"
            )
        if not self.phase.touches_destination:
            raise ReleaseError(
                f"{self.release_id} never reached a phase the destination could have seen; there is nothing to "
                "withdraw, and a receipt for it would invent history"
            )
        existing = self._withdrawals.get(wanted.withdrawal_id)
        if existing is not None:
            if existing != wanted:
                raise StoreConflictError(
                    f"withdrawal {wanted.withdrawal_id} is already recorded with different content"
                )
            return existing
        for action in wanted.requested_actions:
            if action.destination != self._transaction.destination:
                raise ReleaseError(
                    f"withdrawal {wanted.withdrawal_id} asks {action.destination.reference} to take down a release "
                    f"published to {self._transaction.destination.reference}"
                )
        self._withdrawals[wanted.withdrawal_id] = wanted
        return wanted

    def delivery_evidence(self) -> tuple[ExternalRef, ...]:
        """The refs a DELIVERY gate may cite now that this transaction has staged a package."""

        if self._phase not in {
            ReleasePhase.STAGED,
            ReleasePhase.SUBMITTED,
            ReleasePhase.RECEIPTED,
            ReleasePhase.PUBLISHED,
            ReleasePhase.UNKNOWN,
        }:
            raise ReleaseError(
                f"{self.release_id} is {self._phase.value} and has staged nothing; delivery evidence cannot be "
                "cited from a release that has not produced a package"
            )
        staged = tuple(
            item
            for step in self._items
            if step.to_phase is ReleasePhase.STAGED
            for item in step.evidence_refs
        )
        return tuple(dict.fromkeys(self._transaction.delivery_evidence() + staged))

    def side_effect_evidence(self) -> tuple[ExternalRef, ...]:
        """The refs an EXTERNAL_SIDE_EFFECT gate may cite: one per action asked of a destination."""

        collected: list[ExternalRef] = []
        for action in self.current_actions():
            collected.append(action.reference)
        return tuple(dict.fromkeys(collected))

    def replay(self) -> ReleasePhase:
        """Recompute the phase from the recorded steps, in order."""

        state = ReleasePhase.PREPARING
        for step, wanted in enumerate(self._items, start=1):
            if wanted.from_phase is not state:
                raise ReleaseError(
                    f"{self.release_id}: step {step} ({wanted.step_id}) starts from "
                    f"{wanted.from_phase.value} while the history before it ends at {state.value}; the recorded "
                    "chain no longer describes itself"
                )
            state = wanted.to_phase
        return state

    def prove_state(self) -> ReleaseProof:
        """The durable-replay evidence for one release transaction."""

        return ReleaseProof(
            release_id=self.release_id,
            recorded_phase=self._phase,
            replayed_phase=self.replay(),
            steps=len(self._items),
            head_receipt_id=self._head,
        )


@dataclass(frozen=True)
class ReleaseProof(Record):
    """Projection and recomputation of one release, side by side."""

    release_id: str
    recorded_phase: ReleasePhase
    replayed_phase: ReleasePhase
    steps: int = 0
    head_receipt_id: Any = None
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "release_id", require_id(self.release_id, "release_id"))
        object.__setattr__(self, "recorded_phase", ReleasePhase.parse(self.recorded_phase, "recorded_phase"))
        object.__setattr__(self, "replayed_phase", ReleasePhase.parse(self.replayed_phase, "replayed_phase"))
        if self.recorded_phase is not self.replayed_phase:
            raise ReleaseError(
                f"{self.release_id} projects {self.recorded_phase.value} and replays "
                f"{self.replayed_phase.value}; the release's own history no longer backs its state"
            )
        if not isinstance(self.steps, int) or isinstance(self.steps, bool) or self.steps < 0:
            raise SchemaValidationError("steps must be a non-negative integer")
        if self.head_receipt_id is not None:
            object.__setattr__(self, "head_receipt_id", require_id(self.head_receipt_id, "head_receipt_id"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def is_proven(self) -> bool:
        return self.recorded_phase is self.replayed_phase


@dataclass
class ReleaseRegistry:
    """§17's preferred-future resolution over releases whose exact refs never move.

    Two questions are kept apart on purpose: what a receipt cited (always exact, forever) and
    what a consumer should use next (a chain of supersessions, bounded and policy-admitted). A
    mutable latest alias that also answered exact lookups would rewrite history the first time
    someone recalled a master.
    """

    _releases: dict[str, ReleaseTransaction] = field(default_factory=dict)
    _published: set[str] = field(default_factory=set)
    _withdrawn: set[str] = field(default_factory=set)
    _supersessions: SupersessionLedger = field(default_factory=SupersessionLedger)

    def register(self, ledger: Any) -> ReleaseTransaction:
        if not isinstance(ledger, ReleaseLedger):
            raise SchemaValidationError(
                "ReleaseRegistry.register expects the ReleaseLedger of the release being recorded"
            )
        transaction = ledger.transaction
        known = self._releases.get(transaction.release_id)
        if known is not None:
            if known != transaction:
                raise StoreConflictError(
                    f"release {transaction.release_id} is already registered with different claims"
                )
            if ledger.phase is ReleasePhase.PUBLISHED:
                self._published.add(transaction.release_id)
            if ledger.is_withdrawn:
                self._withdrawn.add(transaction.release_id)
            return known
        self._releases[transaction.release_id] = transaction
        if ledger.phase is ReleasePhase.PUBLISHED:
            self._published.add(transaction.release_id)
        if ledger.is_withdrawn:
            self._withdrawn.add(transaction.release_id)
        return transaction

    def _require_known(self, identifier: str, role: str) -> ReleaseTransaction:
        wanted = require_id(identifier, "release_id")
        found = self._releases.get(wanted)
        if found is None:
            raise ReleaseError(f"{role} {wanted} is not a release this registry knows")
        return found

    def supersede(
        self,
        superseded_id: str,
        replacement_id: str,
        *,
        reason_code: str,
        receipt_id: str | None = None,
        effective_at_ms: int = 0,
    ) -> SupersessionRef:
        """Point future consumers elsewhere. The retired release keeps every fact about it."""

        old = self._require_known(superseded_id, "superseded release")
        new = self._require_known(replacement_id, "replacement release")
        if new.release_id not in self._published:
            raise ReleaseError(
                f"{new.release_id} has not published, so it cannot be the preferred release of {old.release_id}; "
                "a supersession that points at an unpublished package hides the work instead of replacing it"
            )
        ref = SupersessionRef(
            superseded_id=old.release_id,
            superseded_kind=EntityKind.RELEASE,
            replacement_id=new.release_id,
            replacement_kind=EntityKind.RELEASE,
            reason_code=require_text(reason_code, "reason_code", maximum=64),
            receipt_id=receipt_id,
            effective_at_ms=effective_at_ms,
        )
        return self._supersessions.record(ref)

    def exact(self, release_id: str) -> ReleaseTransaction:
        """What a receipt cited, resolved to the release it named. Never follows supersession."""

        return self._require_known(release_id, "release")

    def preferred(self, release_id: str, *, admitted: Iterable[str] | None = None) -> ReleaseTransaction:
        """The release a new consumer should use, bounded by policy and by publication."""

        wanted = require_id(release_id, "release_id")
        self._require_known(wanted, "release")
        admitted_set = None if admitted is None else frozenset(admitted)
        current = wanted
        for step in self._supersessions.chain(current):
            candidate = step.replacement_id
            if candidate not in self._published or candidate in self._withdrawn:
                break
            if admitted_set is not None and candidate not in admitted_set:
                break
            current = candidate
        return self._releases[current]

    def is_superseded(self, release_id: str) -> bool:
        return self._supersessions.is_superseded(release_id)

    def chain_of(self, release_id: str) -> tuple[SupersessionRef, ...]:
        return self._supersessions.chain(require_id(release_id, "release_id"))

    @property
    def records(self) -> tuple[SupersessionRef, ...]:
        return self._supersessions.records

    @property
    def known(self) -> tuple[str, ...]:
        return tuple(sorted(self._releases))


def begin_release(
    ledger: ProductionLedger,
    *,
    release_snapshot_id: str,
    destination: Any,
    actor: Any,
    release_id: str | None = None,
    project_id: Any = None,
    promotion_bundle_ref: Any = None,
    policy_refs: Iterable[Any] = (),
    reproducibility_ref: Any = None,
    now_ms: int = 0,
) -> ReleaseLedger:
    """§15.1: prepare the immutable release snapshot for an accepted production.

    The production has to be ACCEPTED first, which is the same invariant the state vector
    states from the other direction: a release is a claim about work that was judged, and
    proof 13 exists because those two were once confused. The actor is never inferred from the
    acceptance receipt either — whoever approved a candidate is not automatically whoever
    ships it, and a release that attributed itself would break that distinction silently.
    """

    if not isinstance(ledger, ProductionLedger):
        raise SchemaValidationError(
            "begin_release expects a ProductionLedger, the only authority over a production's state"
        )
    if actor is None:
        raise ReleaseError(
            "begin_release names the component that prepares the release; the acceptance receipt says who "
            "judged the candidate, which is a different claim"
        )
    current = ledger.current
    if current.phase is not Phase.ACCEPTED:
        raise ReleaseError(
            f"{ledger.production_id} is {current.phase.value}; a release packages what acceptance judged, so "
            "there is nothing to prepare from here"
        )
    candidate = current.candidate_snapshot_id
    if candidate is None:
        raise ReleaseError(
            f"{ledger.production_id} is ACCEPTED with no candidate snapshot, which the vector already forbids"
        )
    return ReleaseLedger(
        ReleaseTransaction(
            release_id=require_id(release_id, "release_id") if release_id is not None else new_id(),
            production_id=ledger.production_id,
            candidate_snapshot_id=candidate,
            release_snapshot_id=release_snapshot_id,
            destination=destination,
            actor=actor,
            project_id=project_id if project_id is not None else current.project_id,
            promotion_bundle_ref=promotion_bundle_ref,
            policy_refs=policy_refs,
            reproducibility_ref=reproducibility_ref,
            prepared_at_ms=now_ms,
        )
    )


def sync_release_state(
    ledger: ProductionLedger,
    releases: ReleaseLedger,
    *,
    actor: Any,
    now_ms: int = 0,
    command_id: str | None = None,
    **changes: Any,
) -> Any:
    """Move the production's release region to what the transaction has proven, or do nothing.

    Only the external-delivery region moves here. The phase stays with the promotion, because
    "RELEASED" is a judgement about delivery fitness and "PUBLISHED" is a fact about a
    destination — §24's pair of invariants is what keeps those two from being typed into one
    field again.

    The move is walked rung by rung rather than asserted, because §24 forbids a claim that skips
    its own evidence: a production synced late after a full publication still has to record the
    staging it never recorded, and only then the publication.
    """

    if not isinstance(ledger, ProductionLedger):
        raise SchemaValidationError("sync_release_state expects a ProductionLedger")
    if not isinstance(releases, ReleaseLedger):
        raise SchemaValidationError("sync_release_state expects a ReleaseLedger")
    if releases.production_id != ledger.production_id:
        raise ReleaseError(
            f"{releases.release_id} is a release of {releases.production_id} and cannot state the delivery of "
            f"{ledger.production_id}"
        )
    wanted = _release_condition(releases)
    claimed = changes.pop("release_condition", None)
    if claimed is not None and claimed is not wanted:
        raise ReleaseError(
            f"{releases.release_id} proves {None if wanted is None else wanted.value} while the caller asked to "
            f"state {claimed.value}; the delivery region is derived from the transaction's own steps"
        )
    owed = _owed_conditions(ledger.current.release_condition, wanted)
    if not owed:
        return None
    evidence = (releases.transaction.reference,)
    move = None
    for index, rung in enumerate(owed):
        last = index == len(owed) - 1
        if last:
            move = ledger.advance(
                actor=actor,
                evidence_refs=evidence,
                now_ms=now_ms,
                command_id=command_id,
                reason_code=changes.pop("reason_code", "release-state-synced"),
                release_condition=rung,
                **changes,
            )
        else:
            move = ledger.advance(
                actor=actor,
                evidence_refs=evidence,
                now_ms=now_ms,
                release_condition=rung,
                reason_code=f"release-{rung.value.lower()}-proven",
            )
    return move


_RELEASE_RUNGS = (
    ReleaseCondition.UNRELEASED,
    ReleaseCondition.STAGED,
    ReleaseCondition.PUBLISHED,
    ReleaseCondition.WITHDRAWN,
)


def _owed_conditions(
    current: ReleaseCondition,
    wanted: ReleaseCondition | None,
) -> tuple[ReleaseCondition, ...]:
    """The rungs above ``current`` that ``wanted`` still owes, in the order they must be recorded.

    The slice is empty for a transaction that proves less than the production already states: a
    release ledger cannot un-record a step, so a late sync of a smaller claim adds nothing rather
    than walking a delivery back.
    """

    if wanted is None or wanted is current:
        return ()
    return _RELEASE_RUNGS[_RELEASE_RUNGS.index(current) + 1 : _RELEASE_RUNGS.index(wanted) + 1]


def _release_condition(releases: ReleaseLedger) -> ReleaseCondition | None:
    """What the outside world is known to hold, or ``None`` when nothing is owed yet."""

    proven = _proven_conditions(releases)
    if releases.is_withdrawn and ReleaseCondition.PUBLISHED in proven:
        return ReleaseCondition.WITHDRAWN
    if releases.phase is ReleasePhase.UNKNOWN:
        return None
    return proven[-1] if proven else None


def _proven_conditions(releases: ReleaseLedger) -> tuple[ReleaseCondition, ...]:
    """The delivery rungs this transaction's own history proves, lowest first.

    A staging is a step; a publication is a different step. Deriving the rungs from the recorded
    phases is what keeps ``sync_release_state`` from promoting a recall into a publication that
    was never performed, which is the same error §16 forbids in the other direction.
    """

    staged = {ReleasePhase.STAGED, ReleasePhase.SUBMITTED, ReleasePhase.RECEIPTED, ReleasePhase.PUBLISHED}
    proven: list[ReleaseCondition] = []
    for step in releases.steps:
        if step.to_phase in staged and ReleaseCondition.STAGED not in proven:
            proven.append(ReleaseCondition.STAGED)
        if step.to_phase is ReleasePhase.PUBLISHED and ReleaseCondition.PUBLISHED not in proven:
            proven.append(ReleaseCondition.PUBLISHED)
    return tuple(proven)
