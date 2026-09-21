"""Área E part 2: typed promotion gates, the request that compiles them, the bundle they leave.

Promotion is where M02 stops being a state machine and starts being a judgement. §3 of the
module spec lists what each rung owes; §6 turns that list into a typed gate set; §7 says an
approval dies with the inputs it evaluated. This module implements all three and nothing
else: it composes M01's ``QualityDecision`` as evidence and never re-decides quality, because
D-M02-S05-003 and WO §6 both forbid a second evaluator.

Two rules do most of the work here. A promotion is compiled from the rungs it crosses, so a
waived ladder still owes every skipped obligation. And a result is only as good as its
freshness binding, so a licence change invalidates the rights gate without asking the render
to happen again (§7).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping, Sequence

from iris_quality.contracts import QualityClass
from iris_quality.decision import DecisionOutcome, QualityDecision

from .base import Labeled, Record, of
from .errors import PromotionBlockedError, SchemaValidationError
from .identity import EntityKind, ExternalRef, new_id, require_id
from .lifecycle import (
    PRODUCTION_PHASES,
    LifecyclePhase,
    Phase,
    ProductionLedger,
    ProductionStateVector,
    ReviewCondition,
    StateTransition,
    TransitionProfile,
    phase_at_least,
    phase_rank,
)
from .limits import (
    MAX_BUNDLE_ITEMS,
    MAX_GATE_EVIDENCE,
    MAX_GATES,
    MAX_LOCATOR_CHARS,
    MAX_RECEIPT_EVIDENCE,
)
from .versions import (
    CONTRACT_VERSION,
    ComponentVersion,
    content_digest,
    require_bounded,
    require_component_version,
    require_digest,
    require_identifier,
    require_millis,
    require_optional_text,
    require_supported_version,
    require_text,
)

__all__ = [
    "GateKind",
    "GateOutcome",
    "GateDependency",
    "FreshnessBinding",
    "GateResult",
    "PromotionGate",
    "HumanApproval",
    "PromotionRequest",
    "PromotionEvidenceBundle",
    "PromotionDecision",
    "REQUIRED_GATES",
    "EVIDENCE_KINDS",
    "compile_gates",
    "rungs_crossed",
    "quality_result",
    "attempt_result",
    "admit_promotion",
    "bundle_for",
    "promote",
]


class GateKind(Labeled):
    """§6's eleven gate families. A family is an obligation, not a check someone wrote."""

    STRUCTURAL = "STRUCTURAL"
    MATERIALIZATION = "MATERIALIZATION"
    QUALITY = "QUALITY"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    IDENTITY_CONTINUITY = "IDENTITY_CONTINUITY"
    RIGHTS_CONSENT = "RIGHTS_CONSENT"
    PROVENANCE = "PROVENANCE"
    SECURITY = "SECURITY"
    DELIVERY = "DELIVERY"
    EXTERNAL_SIDE_EFFECT = "EXTERNAL_SIDE_EFFECT"
    RETENTION_ARCHIVE = "RETENTION_ARCHIVE"


class GateOutcome(Labeled):
    """The four claims D-M02-S05-005 admits.

    Staleness is deliberately absent: §7 says a prior result stops being valid when its
    inputs move, which is a fact about a ``PASS``, not a fifth thing a gate can say. A
    model that added ``STALE`` here would let a caller treat an expired approval as a new
    answer instead of a missing one.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


#: §3, rung by rung. The compiled set for a promotion is the union over every rung crossed,
#: which is what "a direct jump may exist only when a profile proves the skipped obligations"
#: means in code.
REQUIRED_GATES: Mapping[LifecyclePhase, tuple[GateKind, ...]] = {
    Phase.DRAFT: (),
    Phase.PLANNED: (GateKind.STRUCTURAL,),
    Phase.READY: (GateKind.STRUCTURAL, GateKind.RIGHTS_CONSENT, GateKind.SECURITY),
    Phase.MATERIALIZED: (GateKind.MATERIALIZATION,),
    Phase.VALIDATING: (GateKind.STRUCTURAL, GateKind.MATERIALIZATION),
    Phase.ACCEPTED: (
        GateKind.QUALITY,
        GateKind.HUMAN_REVIEW,
        GateKind.RIGHTS_CONSENT,
        GateKind.PROVENANCE,
        GateKind.SECURITY,
    ),
    Phase.RELEASED: (
        GateKind.DELIVERY,
        GateKind.EXTERNAL_SIDE_EFFECT,
        GateKind.PROVENANCE,
        GateKind.RIGHTS_CONSENT,
    ),
    Phase.SUPERSEDED: (GateKind.STRUCTURAL, GateKind.EXTERNAL_SIDE_EFFECT),
    Phase.ARCHIVED: (GateKind.RETENTION_ARCHIVE, GateKind.RIGHTS_CONSENT, GateKind.PROVENANCE),
}

#: Evidence kinds a passing gate of this family has to cite. A gate that can name no
#: evidence of the right kind has not checked anything; it has expressed a hope.
EVIDENCE_KINDS: Mapping[GateKind, tuple[EntityKind, ...]] = {
    GateKind.QUALITY: (EntityKind.QUALITY_DECISION,),
    GateKind.HUMAN_REVIEW: (EntityKind.RECEIPT,),
    GateKind.RIGHTS_CONSENT: (EntityKind.RIGHTS,),
    GateKind.PROVENANCE: (EntityKind.PROVENANCE,),
    GateKind.DELIVERY: (EntityKind.DESTINATION, EntityKind.ARTIFACT, EntityKind.RELEASE),
    GateKind.RETENTION_ARCHIVE: (EntityKind.ARCHIVE,),
}


def _refs(values: Iterable[Any], field: str, *, maximum: int = MAX_RECEIPT_EVIDENCE) -> tuple[ExternalRef, ...]:
    collected = require_bounded(values, field, maximum=maximum, kind=field)
    return tuple(ExternalRef.coerce(item, f"{field}[]") for item in collected)


def _texts(values: Iterable[Any], field: str, *, maximum: int = MAX_BUNDLE_ITEMS) -> tuple[str, ...]:
    collected = require_bounded(values, field, maximum=maximum, kind=field)
    return tuple(require_text(item, f"{field}[]", maximum=512) for item in collected)


@dataclass(frozen=True)
class GateDependency(Record):
    """One input a judgement stands on, named by the thing, the facet of it, and its digest.

    ``input_digest`` is the digest of what is pointed at, not of this record: naming the
    field ``digest`` would shadow ``Record.digest()`` and make the two read alike.
    """

    reference: str
    input_digest: str
    facet: str = "CONTENT"
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "reference", require_text(self.reference, "reference", maximum=MAX_LOCATOR_CHARS))
        object.__setattr__(self, "input_digest", require_digest(self.input_digest, "input_digest"))
        object.__setattr__(
            self, "facet", require_text(self.facet, "facet", maximum=64).strip().upper()
        )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def key(self) -> str:
        return f"{self.reference}#{self.facet}"

    @property
    def text(self) -> str:
        return f"{self.key}={self.input_digest[:12]}"


@dataclass(frozen=True)
class FreshnessBinding(Record):
    """What a result evaluated, so §7 can answer "is that answer still true?".

    A binding is the difference between an approval and a vote: it names the subject and
    every input the gate read, so one later digest change can be traced to the exact gates
    it kills. Results with no binding cannot go stale, which is why passing gates are not
    allowed to lack one.
    """

    subject_digest: str
    dependencies: tuple[GateDependency, ...] = ()
    evaluated_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    NESTED = {"dependencies": of(GateDependency)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject_digest", require_digest(self.subject_digest, "subject_digest"))
        declared = require_bounded(self.dependencies, "dependencies", maximum=MAX_BUNDLE_ITEMS, kind="dependency")
        object.__setattr__(
            self,
            "dependencies",
            tuple(
                sorted(
                    (GateDependency.coerce(item, "dependencies[]") for item in declared),
                    key=lambda item: item.key,
                )
            ),
        )
        keys = [item.key for item in self.dependencies]
        if len(set(keys)) != len(keys):
            raise SchemaValidationError("a binding declares one input once, or invalidation is a guess")
        references = [item.reference for item in self.dependencies]
        if len(set(references)) != len(references):
            raise SchemaValidationError(
                "a binding declares two facets of one input; §7 retires answers by naming the input, so which "
                "facet moved would be decided by whoever wrote the report"
            )
        object.__setattr__(self, "evaluated_at_ms", require_millis(self.evaluated_at_ms, "evaluated_at_ms"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    def staled_by(self, current: Mapping[str, Any]) -> tuple[str, ...]:
        """The declared inputs ``current`` says have moved. Absent keys are unobserved, not unchanged."""

        moved: list[str] = []
        for item in self.dependencies:
            for key in (item.key, item.reference):
                if key not in current:
                    continue
                wanted = current[key]
                if wanted is None:
                    raise PromotionBlockedError(f"{key} was reported as unknown, which revives a settled judgement")
                if require_digest(wanted, f"current[{key}]") != item.input_digest:
                    moved.append(key)
                break
        return tuple(sorted(set(moved)))

    @property
    def text(self) -> str:
        return f"subject {self.subject_digest[:12]} over {len(self.dependencies)} input(s)"


@dataclass(frozen=True)
class GateResult(Record):
    """One gate's answer, with the authority, evidence and inputs that make it auditable."""

    gate_id: str
    kind: GateKind
    outcome: GateOutcome
    reason: str
    authority: Any = None
    evidence_refs: tuple[ExternalRef, ...] = ()
    binding: Any = None
    quality_decision: Any = None
    observed_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    NESTED = {"binding": of(FreshnessBinding), "quality_decision": of(QualityDecision)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_id", require_identifier(self.gate_id, "gate_id"))
        object.__setattr__(self, "kind", GateKind.parse(self.kind, "kind"))
        object.__setattr__(self, "outcome", GateOutcome.parse(self.outcome, "outcome"))
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=512))
        object.__setattr__(self, "evidence_refs", _refs(self.evidence_refs, "evidence_refs", maximum=MAX_GATE_EVIDENCE))
        if self.authority is not None:
            object.__setattr__(self, "authority", require_component_version(self.authority, "authority"))
        if self.binding is not None:
            object.__setattr__(self, "binding", FreshnessBinding.coerce(self.binding, "binding"))
        if self.quality_decision is not None and not isinstance(self.quality_decision, QualityDecision):
            raise SchemaValidationError("quality_decision must be an M01 QualityDecision or None")
        if self.kind is GateKind.QUALITY:
            if self.quality_decision is None:
                raise PromotionBlockedError(
                    f"{self.gate_id} answers QUALITY without carrying the M01 QualityDecision it claims to "
                    "compose; a generic PASS may not stand in for the quality authority"
                )
            if self.authority is not None and self.authority != self.quality_decision.engine:
                raise PromotionBlockedError(
                    f"{self.gate_id} names {self.authority} as quality authority while the bound M01 decision "
                    f"was issued by {self.quality_decision.engine}"
                )
            if self.binding is not None and self.binding.subject_digest != self.quality_decision.subject.content_sha256:
                raise PromotionBlockedError(
                    f"{self.gate_id} binds subject {self.binding.subject_digest[:12]} while the M01 decision "
                    f"judged {self.quality_decision.subject.content_sha256[:12]}"
                )
            if self.outcome is GateOutcome.PASS and (
                self.quality_decision.outcome is not DecisionOutcome.PROMOTED
                or self.quality_decision.requires_human_review
            ):
                raise PromotionBlockedError(
                    f"{self.gate_id} claims QUALITY PASS from an M01 decision that is "
                    f"{self.quality_decision.outcome.value} or still requires human review"
                )
        elif self.quality_decision is not None:
            raise PromotionBlockedError(
                f"{self.gate_id} is a {self.kind.value} gate but carries an M01 QualityDecision; "
                "quality evidence may only answer the QUALITY lane"
            )
        object.__setattr__(self, "observed_at_ms", require_millis(self.observed_at_ms, "observed_at_ms"))
        self._require_provable_claim()
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    def _require_provable_claim(self) -> None:
        """Proof 7 and §7's first sentence, stated once: a PASS is an authority plus evidence plus inputs."""

        if self.outcome is GateOutcome.PASS:
            if self.authority is None:
                raise PromotionBlockedError(
                    f"{self.gate_id} reports PASS with no authority; a gate result is who checked, not that someone did"
                )
            if not self.evidence_refs:
                raise PromotionBlockedError(
                    f"{self.gate_id} reports PASS citing nothing; §8 is explicit that no display badge is evidence"
                )
            if self.binding is None:
                raise PromotionBlockedError(
                    f"{self.gate_id} reports PASS without naming what it evaluated, so it could never be retracted "
                    "when those inputs moved"
                )
        admitted = EVIDENCE_KINDS.get(self.kind)
        if admitted is not None and self.outcome is GateOutcome.PASS:
            cited = {item.kind for item in self.evidence_refs}
            if not cited.intersection(set(admitted)):
                raise PromotionBlockedError(
                    f"{self.gate_id} passes a {self.kind.value} gate on {sorted(item.value for item in cited)} "
                    f"evidence; that family is answered by "
                    f"{sorted(item.value for item in admitted)}"
                )
        if self.outcome is GateOutcome.NOT_APPLICABLE and self.authority is None:
            raise PromotionBlockedError(
                f"{self.gate_id} declares a {self.kind.value} obligation not applicable with nobody on record "
                "deciding that; a waiver is a claim, and an unattributed one is how a mandatory gate disappears"
            )

    @property
    def is_passing(self) -> bool:
        return self.outcome is GateOutcome.PASS

    def staled_by(self, current: Mapping[str, Any]) -> tuple[str, ...]:
        return () if self.binding is None else self.binding.staled_by(current)

    @property
    def summary(self) -> str:
        if self.outcome is GateOutcome.PASS:
            return f"{self.gate_id} ({self.kind.value}) passed by {self.authority}"
        return f"{self.gate_id} ({self.kind.value}) is {self.outcome.value}: {self.reason}"


@dataclass(frozen=True)
class PromotionGate(Record):
    """The declaration of one obligation, before anyone has answered it.

    ``minimum_quality_class`` makes an M01 quality ladder step a promotion parameter instead
    of a conversation: the gate states the class it demands and the result carries the class
    awarded, so an under-qualified decision fails rather than being discussed.
    """

    gate_id: str
    kind: GateKind
    required: bool = True
    reason: str = ""
    minimum_quality_class: Any = None
    authority: Any = None
    depends_on: tuple[GateDependency, ...] = ()
    blocking_unknown: bool = True
    contract_version: str = CONTRACT_VERSION

    NESTED = {"depends_on": of(GateDependency)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_id", require_identifier(self.gate_id, "gate_id"))
        object.__setattr__(self, "kind", GateKind.parse(self.kind, "kind"))
        if not isinstance(self.required, bool):
            raise SchemaValidationError("required must be a boolean")
        if not isinstance(self.blocking_unknown, bool):
            raise SchemaValidationError("blocking_unknown must be a boolean")
        object.__setattr__(self, "reason", require_optional_text(self.reason, "reason", maximum=512) or "")
        if self.minimum_quality_class is not None:
            if self.kind is not GateKind.QUALITY:
                raise PromotionBlockedError(
                    f"{self.gate_id} sets a quality floor on a {self.kind.value} gate; the quality ladder is "
                    "M01's claim and only the QUALITY family may stand on it"
                )
            object.__setattr__(self, "minimum_quality_class", QualityClass.parse(self.minimum_quality_class))
        if self.authority is not None:
            object.__setattr__(self, "authority", require_component_version(self.authority, "authority"))
        collected = require_bounded(self.depends_on, "depends_on", maximum=MAX_BUNDLE_ITEMS, kind="dependency")
        object.__setattr__(
            self,
            "depends_on",
            tuple(
                sorted(
                    (GateDependency.coerce(item, "depends_on[]") for item in collected),
                    key=lambda item: item.key,
                )
            ),
        )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def demands_quality(self) -> bool:
        return self.minimum_quality_class is not None

    def answer_for(self, results: Sequence[GateResult]) -> GateResult | None:
        return next((item for item in results if item.gate_id == self.gate_id), None)

    def blocks(self, result: GateResult, *, current: Mapping[str, Any] | None = None) -> str | None:
        """Why this answer fails the obligation, or ``None`` when it satisfies it."""

        if result.kind is not self.kind:
            return f"{result.gate_id} answers {result.kind.value}, not the {self.kind.value} obligation it is filed under"
        if self.authority is not None and result.authority != self.authority:
            return (
                f"{result.gate_id} was evaluated by {result.authority}, but this obligation admits only "
                f"{self.authority}"
            )
        if result.outcome is GateOutcome.FAIL:
            return f"{result.gate_id} ({self.kind.value}) failed: {result.reason}"
        if result.outcome is GateOutcome.UNKNOWN:
            if self.blocking_unknown:
                return (
                    f"{result.gate_id} ({self.kind.value}) is unknown and policy keeps a blocking unknown blocking: "
                    f"{result.reason}"
                )
            return None
        if result.outcome is GateOutcome.NOT_APPLICABLE:
            if self.required:
                return (
                    f"{result.gate_id} ({self.kind.value}) is required by this promotion and cannot be "
                    "waived as NOT_APPLICABLE"
                )
            return None
        if result.outcome is GateOutcome.PASS:
            if self.kind is GateKind.QUALITY:
                decision = result.quality_decision
                if decision is None:
                    return f"{result.gate_id} has no bound M01 QualityDecision"
                if decision.outcome is not DecisionOutcome.PROMOTED or decision.requires_human_review:
                    return (
                        f"{result.gate_id} cites an M01 decision that is {decision.outcome.value} or still "
                        "requires human review"
                    )
                if (
                    self.minimum_quality_class is not None
                    and decision.awarded_class.ladder_rank < self.minimum_quality_class.ladder_rank
                ):
                    return (
                        f"{result.gate_id} awarded {decision.awarded_class.value} where this promotion demands "
                        f"{self.minimum_quality_class.value}"
                    )
            moved = result.staled_by(current or {})
            if moved:
                return (
                    f"{result.gate_id} ({self.kind.value}) passed against inputs that have since moved "
                    f"({', '.join(moved)}); an approval is never silently inherited"
                )
            declared = {item.key for item in self.depends_on}
            bound = {item.key for item in (result.binding.dependencies if result.binding else ())}
            missing = sorted(declared - bound)
            if missing:
                return (
                    f"{result.gate_id} ({self.kind.value}) passed without binding {', '.join(missing)}, which the "
                    "obligation says it reads"
                )
        return None


LIFECYCLE_ORDER: tuple[LifecyclePhase, ...] = tuple(LifecyclePhase)


def rungs_crossed(source: Any, target: Any) -> tuple[LifecyclePhase, ...]:
    """Every rung a promotion passes over, the target included and the source excluded."""

    start = LifecyclePhase.parse(source, "source")
    wanted = LifecyclePhase.parse(target, "target")
    if phase_rank(wanted) <= phase_rank(start):
        return ()
    ladder = sorted(LIFECYCLE_ORDER, key=phase_rank)
    return tuple(item for item in ladder if phase_rank(start) < phase_rank(item) <= phase_rank(wanted))


def compile_gates(source: Any, target: Any) -> tuple[GateKind, ...]:
    """The obligations a promotion owes, including those of the rungs it skips.

    This is the compiler §3 and the profile doctrine share: widening the ladder never
    widens what must be proven, it only lets one move carry the proof for several rungs.
    """

    collected: list[GateKind] = []
    for phase in rungs_crossed(source, target):
        for kind in REQUIRED_GATES[phase]:
            if kind not in collected:
                collected.append(kind)
    return tuple(collected)


@dataclass(frozen=True)
class HumanApproval(Record):
    """A named human's answer about one exact candidate.

    ``covered_kinds`` is what makes a review attributable to obligations: a signature that
    does not say which gates it answers cannot clear a rights review, and a reviewer who
    covered the quality lane has not approved delivery fitness.
    """

    approval_id: str
    production_id: str
    snapshot_id: str
    reviewer: Any
    decision: ReviewCondition
    covered_kinds: tuple[GateKind, ...] = ()
    statement: Any = None
    receipt_ref: Any = None
    timestamp_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "approval_id", require_id(self.approval_id, "approval_id"))
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        object.__setattr__(self, "snapshot_id", require_id(self.snapshot_id, "snapshot_id"))
        object.__setattr__(self, "reviewer", require_component_version(self.reviewer, "reviewer"))
        parsed = ReviewCondition.parse(self.decision, "decision")
        if parsed not in {ReviewCondition.APPROVED, ReviewCondition.CHANGES_REQUIRED}:
            raise PromotionBlockedError(
                f"approval {self.approval_id} records {parsed.value}, which is not a human decision about anything"
            )
        object.__setattr__(self, "decision", parsed)
        collected = require_bounded(
            self.covered_kinds, "covered_kinds", maximum=len(GateKind), kind="gate kind"
        )
        kinds = tuple(sorted({GateKind.parse(item, "covered_kinds[]") for item in collected}, key=lambda item: item.value))
        if parsed is ReviewCondition.APPROVED and not kinds:
            raise PromotionBlockedError(
                f"approval {self.approval_id} approves and covers no gate family, which is a signature without a meaning"
            )
        object.__setattr__(self, "covered_kinds", kinds)
        object.__setattr__(self, "statement", require_optional_text(self.statement, "statement", maximum=512))
        if self.receipt_ref is not None:
            object.__setattr__(self, "receipt_ref", ExternalRef.coerce(self.receipt_ref, "receipt_ref"))
        object.__setattr__(self, "timestamp_ms", require_millis(self.timestamp_ms, "timestamp_ms"))
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def is_approval(self) -> bool:
        return self.decision is ReviewCondition.APPROVED

    @property
    def reference(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.RECEIPT, reference=self.approval_id)

    def covers(self, kind: GateKind) -> bool:
        return kind in self.covered_kinds


@dataclass(frozen=True)
class PromotionRequest(Record):
    """§5's explicit operation over one immutable candidate snapshot.

    The request binds the exact candidate bytes it asks about (proof 6) and the rungs it
    crosses, so the gate set is derived rather than negotiated: a caller cannot promote to
    ACCEPTED by declaring only the gates it happens to have already passed.
    """

    request_id: str
    production_id: str
    candidate_snapshot_id: str
    candidate_digest: str
    source_vector: ProductionStateVector
    requested_phase: LifecyclePhase
    actor: Any
    gates: tuple[PromotionGate, ...] = ()
    profile: Any = None
    reason: str = ""
    quality_decision_refs: tuple[ExternalRef, ...] = ()
    fidelity_contract_refs: tuple[ExternalRef, ...] = ()
    required_reviewers: tuple[ComponentVersion, ...] = ()
    policy_refs: tuple[ExternalRef, ...] = ()
    release_target: Any = None
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "source_vector": of(ProductionStateVector),
        "gates": of(PromotionGate),
        "profile": of(TransitionProfile),
        "quality_decision_refs": of(ExternalRef),
        "fidelity_contract_refs": of(ExternalRef),
        "policy_refs": of(ExternalRef),
        "release_target": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", require_id(self.request_id, "request_id"))
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        object.__setattr__(self, "candidate_snapshot_id", require_id(self.candidate_snapshot_id, "candidate_snapshot_id"))
        object.__setattr__(self, "candidate_digest", require_digest(self.candidate_digest, "candidate_digest"))
        object.__setattr__(self, "source_vector", ProductionStateVector.coerce(self.source_vector, "source_vector"))
        object.__setattr__(self, "requested_phase", LifecyclePhase.parse(self.requested_phase, "requested_phase"))
        object.__setattr__(self, "actor", require_component_version(self.actor, "actor"))
        object.__setattr__(self, "reason", require_optional_text(self.reason, "reason", maximum=512) or "")
        if self.source_vector.production_id != self.production_id:
            raise PromotionBlockedError(f"{self.request_id} promotes another production's state")
        bound = self.source_vector.candidate_snapshot_id
        if bound is not None and bound != self.candidate_snapshot_id:
            raise PromotionBlockedError(
                f"{self.request_id} asks about candidate {self.candidate_snapshot_id} while {self.production_id} "
                f"is standing on {bound}; a promotion judges the candidate in front of it, never a different one"
            )
        self._require_forward()
        declared = require_bounded(self.gates, "gates", maximum=MAX_GATES, kind="gate")
        gates = tuple(PromotionGate.coerce(item, "gates[]") for item in declared)
        identifiers = [item.gate_id for item in gates]
        if len(set(identifiers)) != len(identifiers):
            raise PromotionBlockedError(f"{self.request_id} declares one gate id twice")
        object.__setattr__(self, "gates", gates)
        if self.profile is not None:
            object.__setattr__(self, "profile", TransitionProfile.coerce(self.profile, "profile"))
        for name in ("quality_decision_refs", "fidelity_contract_refs", "policy_refs"):
            object.__setattr__(self, name, _refs(getattr(self, name), name, maximum=MAX_BUNDLE_ITEMS))
        reviewers = require_bounded(self.required_reviewers, "required_reviewers", maximum=MAX_GATES, kind="reviewer")
        object.__setattr__(
            self,
            "required_reviewers",
            tuple(require_component_version(item, "required_reviewers[]") for item in reviewers),
        )
        if self.release_target is not None:
            object.__setattr__(self, "release_target", ExternalRef.coerce(self.release_target, "release_target"))
        self._require_obligations()
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    def _require_forward(self) -> None:
        """One move, admitted by the ladder or by a profile that carries proof for the skip.

        The check is the whole edge the promotion will ask the ledger for, not each rung
        inside it: every consecutive pair is already legal, so walking the slice rung by rung
        would admit everything and prove nothing.
        """

        source = self.source_vector.phase
        if self.requested_phase is Phase.DRAFT:
            raise PromotionBlockedError(f"{self.request_id} asks to promote to DRAFT, where every production starts")
        if phase_rank(self.requested_phase) <= phase_rank(source):
            raise PromotionBlockedError(
                f"{self.request_id} promotes {source.value} to {self.requested_phase.value}: a promotion moves "
                "forward, and anything else is history"
            )
        if self.profile is None:
            if not PRODUCTION_PHASES.is_legal(source, self.requested_phase):
                raise PromotionBlockedError(
                    f"{self.request_id} crosses {source.value} -> {self.requested_phase.value} with no profile; a "
                    "skipped rung is authorized by a jump carrying proof, never by asking politely"
                )
            return
        if not self.profile.admits(source, self.requested_phase):
            raise PromotionBlockedError(
                f"{self.request_id} crosses {source.value} -> {self.requested_phase.value}, which profile "
                f"{self.profile.profile_id} does not authorize"
            )

    def _require_obligations(self) -> None:
        """The compiled minimum is a floor, so an under-declared request is refused as data."""

        owed = compile_gates(self.source_vector.phase, self.requested_phase)
        missing = [
            kind.value
            for kind in owed
            if not any(gate.kind is kind and gate.required for gate in self.gates)
        ]
        if missing:
            raise PromotionBlockedError(
                f"{self.request_id} promotes to {self.requested_phase.value} without required gates answering "
                f"{', '.join(missing)}; a lifecycle obligation cannot be weakened by declaring it optional"
            )
        lenient = [
            gate.gate_id
            for gate in self.gates
            if gate.kind in owed and gate.required and not gate.blocking_unknown
        ]
        if lenient:
            raise PromotionBlockedError(
                f"{self.request_id} marks required lifecycle gates {', '.join(sorted(lenient))} as "
                "non-blocking on UNKNOWN; frozen M02 obligations fail closed"
            )
        declared_reviewers = set(self.required_reviewers)
        foreign_review_authorities = [
            gate.gate_id
            for gate in self.gates
            if gate.kind is GateKind.HUMAN_REVIEW
            and gate.authority is not None
            and gate.authority not in declared_reviewers
        ]
        if foreign_review_authorities:
            raise PromotionBlockedError(
                f"{self.request_id} assigns human-review gates {', '.join(sorted(foreign_review_authorities))} "
                "to authorities not listed in required_reviewers"
            )
        if any(item.kind is GateKind.QUALITY for item in self.gates) and not self.quality_decision_refs:
            raise PromotionBlockedError(
                f"{self.request_id} declares a quality gate and cites no M01 QualityDecision; a render that finished "
                "is not a judgement"
            )
        if any(item.kind is GateKind.HUMAN_REVIEW for item in self.gates) and not self.required_reviewers:
            raise PromotionBlockedError(
                f"{self.request_id} declares a human-review gate and names no reviewer; mandatory review is a "
                "person, not a checkbox"
            )
        if phase_at_least(self.requested_phase, Phase.RELEASED) and self.release_target is None:
            raise PromotionBlockedError(
                f"{self.request_id} releases to {self.requested_phase.value} and names no destination, which is a "
                "claim about a delivery nobody chose"
            )

    @property
    def obligations(self) -> tuple[GateKind, ...]:
        return compile_gates(self.source_vector.phase, self.requested_phase)

    @property
    def rungs(self) -> tuple[LifecyclePhase, ...]:
        return rungs_crossed(self.source_vector.phase, self.requested_phase)

    def gates_of(self, kind: GateKind) -> tuple[PromotionGate, ...]:
        return tuple(item for item in self.gates if item.kind is kind)

    @property
    def reference(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.RECEIPT, reference=self.request_id)

    @property
    def summary(self) -> str:
        return (
            f"{self.request_id}: {self.production_id} {self.source_vector.phase.value} -> "
            f"{self.requested_phase.value} over {len(self.gates)} gate(s)"
        )


def _dependency(reference: str, input_digest: str, facet: str = "CONTENT") -> GateDependency:
    return GateDependency(reference=reference, input_digest=input_digest, facet=facet)


def quality_result(
    *,
    decision: QualityDecision,
    gate: PromotionGate,
    candidate_digest: str,
    evidence_ref: Any,
    observed_at_ms: int = 0,
    extra_dependencies: Iterable[GateDependency] = (),
) -> GateResult:
    """Turn one M01 ``QualityDecision`` into one gate answer, without re-deciding anything.

    M01 owns the quality claim. This function only asks the questions the promotion layer is
    allowed to ask: was it the admitted evaluator, was it about this candidate, did it award
    the class the gate demands, and is a human still owed. Every answer keeps the decision's
    own engine, contract and subject in the freshness binding, so a judge or policy change
    retires this result later (§7, proofs 9 and 10).
    """

    if gate.kind is not GateKind.QUALITY:
        raise PromotionBlockedError(
            f"{gate.gate_id} is a {gate.kind.value} obligation; only QUALITY may be answered by a QualityDecision"
        )
    if not isinstance(decision, QualityDecision):
        raise SchemaValidationError("quality_result expects an M01 QualityDecision")
    reference = ExternalRef.coerce(evidence_ref, "evidence_ref")
    if reference.kind is not EntityKind.QUALITY_DECISION:
        raise PromotionBlockedError(
            f"{gate.gate_id} cites {reference.kind.value} evidence for a quality decision; an attempt receipt "
            "proves a process ended, which is a different claim"
        )
    wanted = require_digest(candidate_digest, "candidate_digest")
    engine = decision.engine
    contract = _dependency(f"m01.contract#{decision.contract_id}", content_digest(decision.contract_version), "VERSION")
    evaluator = _dependency(f"m01.evaluator#{engine.identifier}", content_digest(f"{engine.identifier}@{engine.version}"), "VERSION")
    subject = _dependency("candidate", decision.subject.content_sha256, "SUBJECT")
    dependencies = (subject, evaluator, contract, *tuple(extra_dependencies))
    binding = FreshnessBinding(
        subject_digest=decision.subject.content_sha256,
        dependencies=dependencies,
        evaluated_at_ms=observed_at_ms,
    )
    common: dict[str, Any] = dict(
        gate_id=gate.gate_id,
        kind=GateKind.QUALITY,
        authority=engine,
        evidence_refs=(reference,),
        quality_decision=decision,
        observed_at_ms=observed_at_ms,
    )
    if decision.subject.content_sha256 != wanted:
        return GateResult(
            outcome=GateOutcome.FAIL,
            reason=(
                f"judged {decision.subject.content_sha256[:12]}, not this candidate "
                f"({wanted[:12]}); a decision about other bytes certifies nothing here"
            ),
            **common,
        )
    if gate.authority is not None and engine != gate.authority:
        return GateResult(
            outcome=GateOutcome.FAIL,
            reason=f"evaluated by {engine}, which this gate does not admit in place of {gate.authority}",
            **common,
        )
    if decision.outcome is DecisionOutcome.REJECTED or decision.outcome is DecisionOutcome.NOT_PROMOTED:
        return GateResult(
            outcome=GateOutcome.FAIL,
            reason=f"M01 recorded {decision.outcome.value} for {decision.requested_class.value}",
            **common,
        )
    if decision.requires_human_review or decision.outcome is DecisionOutcome.HUMAN_REVIEW:
        return GateResult(
            outcome=GateOutcome.UNKNOWN,
            reason=(
                "M01 owes this candidate a human review that has not been answered, so its quality claim is not "
                "yet a promotion answer"
            ),
            **common,
        )
    floor = gate.minimum_quality_class
    if floor is not None and decision.awarded_class.ladder_rank < floor.ladder_rank:
        return GateResult(
            outcome=GateOutcome.FAIL,
            reason=(
                f"awarded {decision.awarded_class.value} where this promotion demands {floor.value}; an "
                "under-qualified decision cannot satisfy a higher gate"
            ),
            **common,
        )
    return GateResult(
        outcome=GateOutcome.PASS,
        reason=(
            f"M01 awarded {decision.awarded_class.value} under {decision.contract_id}@{decision.contract_version} "
            f"by {engine}"
        ),
        binding=binding,
        **common,
    )


def attempt_result(
    *,
    gate: PromotionGate,
    attempt_id: str,
    provider: Any,
    succeeded: bool,
    observed_at_ms: int = 0,
) -> GateResult:
    """What a provider's exit code is worth at the promotion layer: nothing it can pass on.

    Kept because proof 3 is about the promotion door, not only the state machine. A provider
    reporting success is recorded as UNKNOWN with the attempt as evidence, so the failure is
    attributable instead of silent, and a QUALITY obligation refuses to accept it as a pass.
    """

    wanted = require_id(attempt_id, "attempt_id")
    if gate.kind is GateKind.QUALITY:
        raise PromotionBlockedError(
            f"{gate.gate_id} cannot be answered by an attempt outcome; {wanted} finishing proves that attempt "
            "and nothing about acceptance"
        )
    outcome = GateOutcome.UNKNOWN if succeeded else GateOutcome.FAIL
    return GateResult(
        gate_id=gate.gate_id,
        kind=gate.kind,
        outcome=outcome,
        reason=(
            f"attempt {wanted} reported process success, which is one provider's word about one run and not a "
            "judgement about this obligation"
            if succeeded
            else f"attempt {wanted} reported process failure"
        ),
        authority=require_component_version(provider, "provider"),
        evidence_refs=(ExternalRef(kind=EntityKind.ATTEMPT, reference=wanted),),
        observed_at_ms=observed_at_ms,
    )


@dataclass(frozen=True)
class PromotionEvidenceBundle(Record):
    """§8's eleven items. Every one of them is a ref or a record, because a badge is not evidence.

    The bundle is the immutable artifact a promotion leaves behind. It is deliberately not
    derived from the request: it names the vectors the transition actually moved, so an
    auditor reads what happened rather than what was asked.
    """

    bundle_id: str
    production_id: str
    request_id: str
    source_vector: ProductionStateVector
    target_vector: ProductionStateVector
    candidate_snapshot_id: str
    result_snapshot_id: Any = None
    gate_results: tuple[GateResult, ...] = ()
    quality_decision_refs: tuple[ExternalRef, ...] = ()
    approvals: tuple[HumanApproval, ...] = ()
    rights_refs: tuple[ExternalRef, ...] = ()
    consent_refs: tuple[ExternalRef, ...] = ()
    provenance_refs: tuple[ExternalRef, ...] = ()
    delivery_refs: tuple[ExternalRef, ...] = ()
    actor: Any = None
    authority: Any = None
    transition_receipt_id: Any = None
    observations: tuple[str, ...] = ()
    debts: tuple[ExternalRef, ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "source_vector": of(ProductionStateVector),
        "target_vector": of(ProductionStateVector),
        "gate_results": of(GateResult),
        "approvals": of(HumanApproval),
        "quality_decision_refs": of(ExternalRef),
        "rights_refs": of(ExternalRef),
        "consent_refs": of(ExternalRef),
        "provenance_refs": of(ExternalRef),
        "delivery_refs": of(ExternalRef),
        "debts": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "bundle_id", require_id(self.bundle_id, "bundle_id"))
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        object.__setattr__(self, "request_id", require_id(self.request_id, "request_id"))
        for name in ("source_vector", "target_vector"):
            object.__setattr__(self, name, ProductionStateVector.coerce(getattr(self, name), name))
        object.__setattr__(self, "candidate_snapshot_id", require_id(self.candidate_snapshot_id, "candidate_snapshot_id"))
        if self.result_snapshot_id is not None:
            object.__setattr__(self, "result_snapshot_id", require_id(self.result_snapshot_id, "result_snapshot_id"))
        declared = require_bounded(self.gate_results, "gate_results", maximum=MAX_GATES, kind="gate result")
        results = tuple(GateResult.coerce(item, "gate_results[]") for item in declared)
        identifiers = [item.gate_id for item in results]
        if len(set(identifiers)) != len(identifiers):
            raise PromotionBlockedError(f"{self.bundle_id} reports one gate twice, which is two answers to no question")
        object.__setattr__(self, "gate_results", results)
        collected = require_bounded(self.approvals, "approvals", maximum=MAX_GATES, kind="approval")
        object.__setattr__(self, "approvals", tuple(HumanApproval.coerce(item, "approvals[]") for item in collected))
        for name in (
            "quality_decision_refs",
            "rights_refs",
            "consent_refs",
            "provenance_refs",
            "delivery_refs",
            "debts",
        ):
            object.__setattr__(self, name, _refs(getattr(self, name), name, maximum=MAX_BUNDLE_ITEMS))
        object.__setattr__(self, "observations", _texts(self.observations, "observations"))
        if self.actor is not None:
            object.__setattr__(self, "actor", require_component_version(self.actor, "actor"))
        if self.authority is not None:
            object.__setattr__(self, "authority", require_component_version(self.authority, "authority"))
        if self.transition_receipt_id is not None:
            object.__setattr__(
                self, "transition_receipt_id", require_id(self.transition_receipt_id, "transition_receipt_id")
            )
        self._require_what_the_phase_claims()
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    def _require_what_the_phase_claims(self) -> None:
        target = self.target_vector.phase
        if self.source_vector.production_id != self.production_id:
            raise PromotionBlockedError(f"{self.bundle_id} binds another production's source vector")
        if self.target_vector.production_id != self.production_id:
            raise PromotionBlockedError(f"{self.bundle_id} binds another production's target vector")
        if not self.gate_results:
            raise PromotionBlockedError(
                f"{self.bundle_id} promotes to {target.value} with no gate results, which is the relabeling §3 "
                "forbids"
            )
        if self.transition_receipt_id is None:
            raise PromotionBlockedError(
                f"{self.bundle_id} records no transition receipt, so nothing links this evidence to the history "
                "that granted it"
            )
        if self.actor is None or self.authority is None:
            raise PromotionBlockedError(
                f"{self.bundle_id} names no actor or no authority; §8 requires both, or the bundle belongs to nobody"
            )
        if phase_at_least(target, Phase.ACCEPTED):
            if not self.quality_decision_refs:
                raise PromotionBlockedError(
                    f"{self.bundle_id} accepts a production with no M01 QualityDecision bound"
                )
            if not self.provenance_refs or not self.rights_refs:
                raise PromotionBlockedError(
                    f"{self.bundle_id} accepts a production without the rights and provenance refs §3 makes part "
                    "of acceptance"
                )
        if phase_at_least(target, Phase.RELEASED) and not self.delivery_refs:
            raise PromotionBlockedError(
                f"{self.bundle_id} releases with no delivery evidence; a release is a claim about a destination"
            )

    @property
    def passed_kinds(self) -> tuple[GateKind, ...]:
        return tuple(sorted({item.kind for item in self.gate_results if item.is_passing}, key=lambda item: item.value))

    @property
    def reference(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.EVIDENCE, reference=self.bundle_id)

    @property
    def summary(self) -> str:
        return (
            f"{self.bundle_id}: {self.production_id} {self.source_vector.phase.value} -> "
            f"{self.target_vector.phase.value} on {len(self.gate_results)} gate result(s), "
            f"{len(self.approvals)} approval(s), {len(self.quality_decision_refs)} quality decision(s)"
        )


@dataclass(frozen=True)
class PromotionDecision(Record):
    """Whether the gates carried the request, and what is still owed when they did not."""

    decision_id: str
    request_id: str
    production_id: str
    requested_phase: LifecyclePhase
    admitted: bool
    gate_results: tuple[GateResult, ...] = ()
    blocking_reasons: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()
    stale_gates: tuple[str, ...] = ()
    bundle: Any = None
    transition: Any = None
    decided_at_ms: int = 0
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "gate_results": of(GateResult),
        "bundle": of(PromotionEvidenceBundle),
        "transition": of(StateTransition),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", require_id(self.decision_id, "decision_id"))
        object.__setattr__(self, "request_id", require_id(self.request_id, "request_id"))
        object.__setattr__(self, "production_id", require_id(self.production_id, "production_id"))
        object.__setattr__(self, "requested_phase", LifecyclePhase.parse(self.requested_phase, "requested_phase"))
        if not isinstance(self.admitted, bool):
            raise SchemaValidationError("admitted must be a boolean")
        declared = require_bounded(self.gate_results, "gate_results", maximum=MAX_GATES, kind="gate result")
        object.__setattr__(
            self, "gate_results", tuple(GateResult.coerce(item, "gate_results[]") for item in declared)
        )
        object.__setattr__(self, "blocking_reasons", _texts(self.blocking_reasons, "blocking_reasons"))
        object.__setattr__(self, "unresolved", _texts(self.unresolved, "unresolved"))
        object.__setattr__(self, "stale_gates", _texts(self.stale_gates, "stale_gates"))
        if self.bundle is not None:
            object.__setattr__(self, "bundle", PromotionEvidenceBundle.coerce(self.bundle, "bundle"))
        if self.transition is not None:
            object.__setattr__(self, "transition", StateTransition.coerce(self.transition, "transition"))
        object.__setattr__(self, "decided_at_ms", require_millis(self.decided_at_ms, "decided_at_ms"))
        if self.admitted and self.blocking_reasons:
            raise PromotionBlockedError(
                f"{self.decision_id} admits a promotion while {self.blocking_reasons[:1]} still blocks it"
            )
        if not self.admitted and not self.blocking_reasons:
            raise PromotionBlockedError(
                f"{self.decision_id} refuses a promotion and says why nothing; a refusal has to name its blocker"
            )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    @property
    def has_evidence(self) -> bool:
        return self.bundle is not None

    def require_evidence(self) -> PromotionEvidenceBundle:
        if self.bundle is None:
            raise PromotionBlockedError(
                f"{self.decision_id} was never carried into a transition; call promote() or attach the bundle "
                "before treating this decision as evidence"
            )
        return self.bundle

    @property
    def summary(self) -> str:
        if self.admitted:
            return f"{self.decision_id}: {self.production_id} may enter {self.requested_phase.value}"
        return (
            f"{self.decision_id}: {self.production_id} may not enter {self.requested_phase.value} — "
            + "; ".join(self.blocking_reasons)
        )


def _reviewed_approvals(
    request: PromotionRequest,
    approvals: Sequence[HumanApproval],
) -> tuple[list[HumanApproval], list[str]]:
    """The approvals that speak about this exact candidate, and the ones that speak elsewhere."""

    matched: list[HumanApproval] = []
    notes: list[str] = []
    seen: set[str] = set()
    for approval in approvals:
        if approval.production_id != request.production_id:
            raise PromotionBlockedError(
                f"approval {approval.approval_id} is about another production and cannot clear this one"
            )
        if approval.approval_id in seen:
            continue
        seen.add(approval.approval_id)
        if approval.snapshot_id != request.candidate_snapshot_id:
            notes.append(
                f"approval {approval.approval_id} reviewed {approval.snapshot_id}, not the candidate this "
                "promotion asks about"
            )
            continue
        if approval.is_approval and not approval.covers(GateKind.HUMAN_REVIEW):
            notes.append(
                f"approval {approval.approval_id} covers "
                f"{', '.join(item.value for item in approval.covered_kinds)} and not the human-review lane"
            )
            continue
        matched.append(approval)
    return matched, notes


def _review_result(
    request: PromotionRequest,
    gate: PromotionGate,
    approvals: Sequence[HumanApproval],
    *,
    now_ms: int,
) -> GateResult:
    """Answer a human-review obligation from the approvals on file, never from a claim.

    This is the same door M01's CORRECTION-02 closed for evaluator authority: a caller who
    could write a ``HUMAN_REVIEW`` result by hand could clear mandatory review by naming any
    receipt on disk. So the answer is derived here from ``HumanApproval`` records, which carry
    the reviewer, the exact candidate and the lane they signed for.
    """

    lane = [item for item in approvals if gate.authority is None or item.reviewer == gate.authority]
    rejected = [item for item in lane if not item.is_approval]
    approved = [item for item in lane if item.is_approval]
    reviewers = {item.reviewer for item in approved}
    expected_reviewers = (
        (gate.authority,) if gate.authority is not None else request.required_reviewers
    )
    outstanding = [item for item in expected_reviewers if item not in reviewers]
    cited = tuple(
        dict.fromkeys(
            [item.reference for item in approved]
            + [item.receipt_ref for item in approved if item.receipt_ref is not None]
        )
    )
    common: dict[str, Any] = dict(
        gate_id=gate.gate_id,
        kind=GateKind.HUMAN_REVIEW,
        evidence_refs=cited,
        observed_at_ms=now_ms,
    )
    if rejected:
        return GateResult(
            outcome=GateOutcome.FAIL,
            reason=(
                f"{rejected[0].approval_id} asked for changes; a rejection is not overridden by an earlier "
                "signature on the same candidate"
            ),
            **common,
        )
    if outstanding:
        return GateResult(
            outcome=GateOutcome.UNKNOWN,
            reason=(
                f"still owes {', '.join(str(item) for item in outstanding)} a review of this exact candidate"
            ),
            **common,
        )
    ordered = sorted(approved, key=lambda item: item.approval_id)
    binding = FreshnessBinding(
        subject_digest=request.candidate_digest,
        dependencies=tuple(
            [_dependency("candidate", request.candidate_digest, "SUBJECT")]
            + [_dependency(f"approval#{item.approval_id}", item.digest(), "RECORD") for item in ordered]
        ),
        evaluated_at_ms=now_ms,
    )
    return GateResult(
        outcome=GateOutcome.PASS,
        reason=f"{len(ordered)} named approval(s) answer the human-review lane for {request.candidate_snapshot_id}",
        authority=ordered[0].reviewer,
        binding=binding,
        **common,
    )


def admit_promotion(
    request: PromotionRequest,
    results: Iterable[Any],
    *,
    approvals: Iterable[Any] = (),
    current_digests: Mapping[str, Any] | None = None,
    now_ms: int = 0,
    decision_id: str | None = None,
) -> PromotionDecision:
    """Compile the answers against the obligations, and refuse with the reason it lacks.

    Nothing here decides quality. It asks, per obligation: is there an answer, is it the
    admitted authority's, did the inputs it stood on move, and did a human actually sign for
    the lane they claim.
    """

    declared = require_bounded(results, "results", maximum=MAX_GATES, kind="gate result")
    given = tuple(GateResult.coerce(item, "results[]") for item in declared)
    for answer in given:
        if answer.kind is GateKind.HUMAN_REVIEW:
            raise PromotionBlockedError(
                f"{answer.gate_id} files a hand-written human-review answer; that lane is answered by the "
                "approvals on file, never by a receipt ref someone chose"
            )
    reviewed, notes = _reviewed_approvals(
        request, tuple(HumanApproval.coerce(item, "approvals[]") for item in approvals)
    )
    answers = (
        given
        + tuple(
            _review_result(request, gate, reviewed, now_ms=now_ms)
            for gate in request.gates
            if gate.kind is GateKind.HUMAN_REVIEW
        )
    )
    digests = dict(current_digests or {})
    blocking: list[str] = []
    unresolved: list[str] = list(notes)
    stale: list[str] = []
    discharged: set[GateKind] = set()
    held_up: set[GateKind] = set()
    answered: dict[str, GateResult] = {}
    for answer in answers:
        if answer.gate_id in answered:
            raise PromotionBlockedError(f"{answer.gate_id} answered twice; a gate has one answer per promotion")
        answered[answer.gate_id] = answer
    for gate in request.gates:
        found = gate.answer_for(answers)
        if found is None:
            (blocking if gate.required else unresolved).append(
                f"{gate.gate_id} ({gate.kind.value}) was never answered"
                if gate.required
                else f"{gate.gate_id} ({gate.kind.value}) is optional and was not answered"
            )
            if gate.required:
                held_up.add(gate.kind)
            continue
        moved = found.staled_by(digests)
        if moved:
            stale.extend(f"{found.gate_id}: {item}" for item in moved)
        reason = gate.blocks(found, current=digests)
        if reason is not None:
            (blocking if gate.required else unresolved).append(reason)
            if gate.required:
                held_up.add(gate.kind)
            continue
        if found.outcome is GateOutcome.PASS:
            discharged.add(gate.kind)
        else:
            unresolved.append(f"{gate.gate_id} ({gate.kind.value}) is {found.outcome.value}: {found.reason}")
    for kind in request.obligations:
        if kind in discharged or kind in held_up:
            continue
        blocking.append(
            f"the {kind.value} obligation owed by the rungs crossed has no answer that satisfies it"
        )
    return PromotionDecision(
        decision_id=require_id(decision_id, "decision_id") if decision_id is not None else new_id(),
        request_id=request.request_id,
        production_id=request.production_id,
        requested_phase=request.requested_phase,
        admitted=not blocking,
        gate_results=answers,
        blocking_reasons=tuple(blocking),
        unresolved=tuple(sorted(set(unresolved))),
        stale_gates=tuple(sorted(set(stale))),
        decided_at_ms=now_ms,
    )


def bundle_for(
    request: PromotionRequest,
    decision: PromotionDecision,
    transition: StateTransition,
    *,
    bundle_id: str | None = None,
    approvals: Iterable[Any] = (),
    result_snapshot_id: Any = None,
    rights_refs: Iterable[Any] = (),
    consent_refs: Iterable[Any] = (),
    provenance_refs: Iterable[Any] = (),
    delivery_refs: Iterable[Any] = (),
    debts: Iterable[Any] = (),
    actor: Any = None,
    authority: Any = None,
) -> PromotionEvidenceBundle:
    """The immutable §8 record of a granted promotion, bound to the transition it caused."""

    if not decision.admitted:
        raise PromotionBlockedError(
            f"{decision.decision_id} refused the promotion, so there is nothing to bundle; §8 is evidence of what "
            "IRIS granted, not of what it considered"
        )
    if transition.production_id != request.production_id:
        raise PromotionBlockedError(f"{decision.decision_id}'s transition belongs to another production")
    if transition.to_vector.phase is not request.requested_phase:
        raise PromotionBlockedError(
            f"{decision.decision_id} asked for {request.requested_phase.value} and the recorded move arrived at "
            f"{transition.to_vector.phase.value}; evidence of a different promotion certifies nothing"
        )
    for vector in (transition.from_vector, transition.to_vector):
        claimed = vector.candidate_snapshot_id
        if claimed is not None and claimed != request.candidate_snapshot_id:
            raise PromotionBlockedError(
                f"{decision.decision_id} bundles evidence about candidate {request.candidate_snapshot_id} while the "
                f"recorded move stands on {claimed}"
            )
    collected = tuple(HumanApproval.coerce(item, "approvals[]") for item in approvals)
    for item in collected:
        if item.snapshot_id != request.candidate_snapshot_id:
            raise PromotionBlockedError(
                f"approval {item.approval_id} is about another candidate and cannot be bundled as evidence for this one"
            )
    return PromotionEvidenceBundle(
        bundle_id=require_id(bundle_id, "bundle_id") if bundle_id is not None else new_id(),
        production_id=request.production_id,
        request_id=request.request_id,
        source_vector=transition.from_vector,
        target_vector=transition.to_vector,
        candidate_snapshot_id=request.candidate_snapshot_id,
        result_snapshot_id=result_snapshot_id,
        gate_results=decision.gate_results,
        quality_decision_refs=request.quality_decision_refs,
        approvals=collected,
        rights_refs=tuple(_refs(rights_refs, "rights_refs")),
        consent_refs=tuple(_refs(consent_refs, "consent_refs")),
        provenance_refs=tuple(_refs(provenance_refs, "provenance_refs")),
        delivery_refs=tuple(_refs(delivery_refs, "delivery_refs")),
        actor=actor if actor is not None else request.actor,
        authority=authority if authority is not None else request.actor,
        transition_receipt_id=transition.receipt.transition_id,
        observations=decision.unresolved,
        debts=tuple(_refs(debts, "debts")),
    )


def promote(
    ledger: Any,
    request: PromotionRequest,
    results: Iterable[Any],
    *,
    approvals: Iterable[Any] = (),
    current_digests: Mapping[str, Any] | None = None,
    bundle_id: str | None = None,
    rights_refs: Iterable[Any] = (),
    consent_refs: Iterable[Any] = (),
    provenance_refs: Iterable[Any] = (),
    delivery_refs: Iterable[Any] = (),
    result_snapshot_id: Any = None,
    debts: Iterable[Any] = (),
    now_ms: int = 0,
    **advance_changes: Any,
) -> PromotionDecision:
    """Ask the gates, and if they carry it, move the state and leave the bundle behind.

    The lifecycle law stays in charge of the move: this calls ``ledger.advance`` with the
    promotion bundle as its authority, so a granted promotion that the state machine refuses
    (a skipped rung, a missing human receipt) never produces evidence of a transition that
    did not happen.
    """

    if not isinstance(ledger, ProductionLedger):
        raise SchemaValidationError("promote expects a ProductionLedger, the only authority over a production's state")
    if request.production_id != ledger.production_id:
        raise PromotionBlockedError(
            f"{request.request_id} promotes {request.production_id} through the ledger of {ledger.production_id}"
        )
    if request.source_vector != ledger.current:
        raise PromotionBlockedError(
            f"{request.request_id} was compiled against {request.source_vector.summary} while "
            f"{ledger.production_id} now stands at {ledger.current.summary}; the gates answered a world that is no "
            "longer this one, so they answer nothing here"
        )
    collected = tuple(HumanApproval.coerce(item, "approvals[]") for item in approvals)
    decision = admit_promotion(
        request,
        results,
        approvals=collected,
        current_digests=current_digests,
        now_ms=now_ms,
    )
    if not decision.admitted:
        return decision
    identity = require_id(bundle_id, "bundle_id") if bundle_id is not None else new_id()
    granted = sorted(
        (item for item in collected if item.is_approval and item.receipt_ref is not None),
        key=lambda item: item.approval_id,
    )
    changes = dict(advance_changes)
    changes.setdefault("candidate_snapshot_id", request.candidate_snapshot_id)
    answered = any(
        item.kind is GateKind.HUMAN_REVIEW and item.outcome is GateOutcome.PASS for item in decision.gate_results
    )
    if answered and ledger.current.review is not ReviewCondition.APPROVED:
        changes.setdefault("review", ReviewCondition.APPROVED)
    transition = ledger.advance(
        actor=request.actor,
        profile=request.profile,
        phase=request.requested_phase,
        promotion_ref=ExternalRef(kind=EntityKind.EVIDENCE, reference=identity),
        review_receipt=granted[0].receipt_ref if granted else None,
        now_ms=now_ms,
        reason_code="promoted",
        evidence_refs=(request.reference,),
        **changes,
    )
    bundle = bundle_for(
        request,
        decision,
        transition,
        bundle_id=identity,
        approvals=collected,
        result_snapshot_id=result_snapshot_id,
        rights_refs=rights_refs,
        consent_refs=consent_refs,
        provenance_refs=provenance_refs,
        delivery_refs=delivery_refs,
        debts=debts,
    )
    return replace(decision, bundle=bundle, transition=transition)
