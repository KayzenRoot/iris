"""F-M03-02 Ambiguity & Clarification Core, and freedom that is not a gap.

Ambiguity here is a recorded state, not a log line: an unresolved question is a value with a
consequence class, the semantics it affects, and a rank in a clarification queue. That is
what lets §18 demand a *deterministic* ranking — a queue ordered by whoever noticed first,
or by a float that rounds differently per platform, is a queue nobody can audit.

Freedom zones get their own type because conflating them with ambiguity is the specific
failure §5.7 forbids. "Any colour you like within the brand palette" is not missing data, and
a kernel that treats it as missing will either block the work or silently fill it with a
default that later reads as the client's choice. So a zone states its bounds, and a
defaulted statement landing inside one is refused rather than tolerated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .base import Labeled, Record, of
from .errors import AmbiguityBlockedError, SchemaValidationError
from .identity import AuthorityLevel, RefKind, SemanticRef
from .intent import IntentOrigin, IntentStatement
from .limits import MAX_AMBIGUITIES, MAX_FREEDOM_ZONES, MAX_OPEN_QUESTIONS
from .versions import require_identifier, require_semantic_path, require_text

__all__ = [
    "AmbiguityAssessment",
    "AmbiguityConsequence",
    "AmbiguityKind",
    "AmbiguityRecord",
    "ClarificationCandidate",
    "FreedomZone",
    "OpenQuestion",
    "rank_clarifications",
    "require_freedom_honoured",
]


class AmbiguityConsequence(Labeled):
    """What an unresolved point actually costs, as declared rather than as guessed later.

    The classes are ordered by how hard they stop the work, and the ordering is used for
    ranking — which is why ``CREATIVE_FREEDOM`` sits at zero rather than being a kind of
    error: it stops nothing, and treating it as a lower-severity ambiguity would eventually
    produce a report that asks the client to resolve their own latitude.
    """

    CREATIVE_FREEDOM = "CREATIVE_FREEDOM"
    NON_BLOCKING = "NON_BLOCKING"
    COST_CRITICAL = "COST_CRITICAL"
    QUALITY_CRITICAL = "QUALITY_CRITICAL"
    BLOCKING = "BLOCKING"

    @property
    def rank(self) -> int:
        return _CONSEQUENCE_RANKS[self]

    @property
    def blocks_completion(self) -> bool:
        return self is AmbiguityConsequence.BLOCKING

    @property
    def needs_human(self) -> bool:
        """Whether only a human or policy can close it.

        Cost and quality consequences are the two that an executor is not allowed to settle
        by choosing the cheap or the good option — that decision is the client's, and the
        kernel's job is to surface it rather than absorb it.
        """

        return self in {
            AmbiguityConsequence.BLOCKING,
            AmbiguityConsequence.QUALITY_CRITICAL,
            AmbiguityConsequence.COST_CRITICAL,
        }


_CONSEQUENCE_RANKS: Mapping[AmbiguityConsequence, int] = {
    AmbiguityConsequence.CREATIVE_FREEDOM: 0,
    AmbiguityConsequence.NON_BLOCKING: 1,
    AmbiguityConsequence.COST_CRITICAL: 2,
    AmbiguityConsequence.QUALITY_CRITICAL: 3,
    AmbiguityConsequence.BLOCKING: 4,
}


class AmbiguityKind(Labeled):
    """The shape of what is unresolved.

    Typed rather than free text because the kind decides which remedies exist: an
    ``UNRESOLVED_REFERENCE`` is closed by binding a ref, a ``VAGUE_QUALIFIER`` by naming a
    rung or a threshold, and a ``CONTRADICTION_WITHIN_SOURCE`` by a human deciding which
    statement survives.
    """

    MISSING_VALUE = "MISSING_VALUE"
    MISSING_MODALITY = "MISSING_MODALITY"
    VAGUE_QUALIFIER = "VAGUE_QUALIFIER"
    UNRESOLVED_REFERENCE = "UNRESOLVED_REFERENCE"
    AMBIGUOUS_SCOPE = "AMBIGUOUS_SCOPE"
    TERM_OVERLOAD = "TERM_OVERLOAD"
    CONTRADICTION_WITHIN_SOURCE = "CONTRADICTION_WITHIN_SOURCE"
    UNBOUNDED_TOLERANCE = "UNBOUNDED_TOLERANCE"
    MISSING_AUTHORITY_BASIS = "MISSING_AUTHORITY_BASIS"


class QuestionStatus(Labeled):
    OPEN = "OPEN"
    ANSWERED = "ANSWERED"
    WAIVED_AS_FREEDOM = "WAIVED_AS_FREEDOM"
    DEFERRED = "DEFERRED"


@dataclass(frozen=True)
class AmbiguityRecord(Record):
    """One unresolved semantic point, pinned to the paths and records it affects.

    ``affected_statement_ids`` is required to be non-empty for anything other than a genuinely
    absent value, because an ambiguity that touches nothing is a note in a margin, and
    carrying it in the admission path would let a reviewer mistake "we recorded a concern" for
    "we blocked something".
    """

    ambiguity_id: str
    kind: str
    consequence: str
    semantic_paths: tuple[str, ...]
    question: str
    affected_statement_ids: tuple[str, ...] = ()
    affected_constraint_ids: tuple[str, ...] = ()
    affected_obligation_ids: tuple[str, ...] = ()
    candidate_readings: tuple[str, ...] = ()
    raised_by: SemanticRef | None = None
    resolution_ref: SemanticRef | None = None
    requires_human: bool | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "ambiguity_id", require_identifier(self.ambiguity_id, "ambiguity_id"))
        object.__setattr__(self, "kind", AmbiguityKind.parse(self.kind, "kind").value)
        consequence = AmbiguityConsequence.parse(self.consequence, "consequence")
        object.__setattr__(self, "consequence", consequence.value)
        paths = _checked_paths(self.semantic_paths)
        if not paths:
            raise SchemaValidationError(
                f"ambiguity {self.ambiguity_id} names no semantic path; an ambiguity about nothing "
                "cannot be resolved, only closed by whoever wrote it"
            )
        object.__setattr__(self, "semantic_paths", paths)
        object.__setattr__(self, "question", require_text(self.question, "question", maximum=2048))
        for name in ("affected_statement_ids", "affected_constraint_ids", "affected_obligation_ids"):
            value = getattr(self, name) or ()
            object.__setattr__(self, name, tuple(sorted({require_identifier(item, f"{name}[]") for item in value})))
        if consequence.blocks_completion and not any(
            (self.affected_statement_ids, self.affected_constraint_ids, self.affected_obligation_ids)
        ):
            raise SchemaValidationError(
                f"blocking ambiguity {self.ambiguity_id} affects nothing, so it blocks nothing; either "
                "name what it stops or lower its consequence"
            )
        readings = tuple(self.candidate_readings or ())
        if len(readings) > 8:
            raise SchemaValidationError("candidate_readings exceeds 8 entries")
        object.__setattr__(
            self,
            "candidate_readings",
            tuple(sorted(require_text(item, "candidate_readings[]", maximum=512) for item in readings)),
        )
        if self.raised_by is not None:
            object.__setattr__(self, "raised_by", SemanticRef.coerce(self.raised_by, "raised_by"))
        if self.resolution_ref is not None:
            object.__setattr__(self, "resolution_ref", SemanticRef.coerce(self.resolution_ref, "resolution_ref"))
        if self.requires_human is None:
            object.__setattr__(self, "requires_human", consequence.needs_human)
        elif bool(self.requires_human) and not consequence.needs_human:
            raise SchemaValidationError(
                f"{self.ambiguity_id} is {consequence.value} but demands a human; that is a policy "
                "claim wearing an ambiguity record, and policy lives in S05"
            )
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=2048))

    @property
    def consequence_class(self) -> AmbiguityConsequence:
        return AmbiguityConsequence.parse(self.consequence)

    @property
    def resolved(self) -> bool:
        return self.resolution_ref is not None

    @property
    def breadth(self) -> int:
        return len(set(self.affected_statement_ids) | set(self.affected_constraint_ids) | set(self.affected_obligation_ids))

    def touches(self, path: str) -> bool:
        prefix = require_semantic_path(path, "path")
        return any(
            item == prefix or item.startswith(prefix + ".") or prefix.startswith(item + ".")
            for item in self.semantic_paths
        )

    def blocks(self) -> bool:
        return self.consequence_class.blocks_completion and not self.resolved

    @property
    def ambiguity_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.AMBIGUITY.value, ref_id=self.ambiguity_id).with_digest(self.digest())


def _checked_paths(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise SchemaValidationError("semantic_paths must be a list of dotted paths")
    paths = tuple(sorted({require_semantic_path(item, "semantic_paths[]") for item in value}))
    if len(paths) > 32:
        raise SchemaValidationError("semantic_paths exceeds 32 entries")
    return paths


@dataclass(frozen=True)
class FreedomZone(Record):
    """Declared latitude, with its bounds stated rather than assumed.

    ``fixed_paths`` and ``free_paths`` cannot overlap, and the zone is required to name at
    least one free path: a "freedom zone" that fixes everything and frees nothing is a
    constraint bundle wearing a friendlier name, and the kernel would then default-fill what
    it should have left open (§5.7).
    """

    zone_id: str
    label: str
    free_paths: tuple[str, ...]
    fixed_paths: tuple[str, ...] = ()
    latitude: str = "OPEN_WITHIN_BOUNDS"
    rationale: str | None = None
    granted_by: SemanticRef | None = None
    expires_with_revision: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "zone_id", require_identifier(self.zone_id, "zone_id"))
        object.__setattr__(self, "label", require_text(self.label, "label", maximum=160))
        free = _checked_paths(self.free_paths)
        fixed = _checked_paths(self.fixed_paths)
        if not free:
            raise SchemaValidationError(
                f"freedom zone {self.zone_id} frees nothing; a zone with no latitude is a constraint "
                "bundle and should say so"
            )
        overlap = sorted(set(free) & set(fixed))
        if overlap:
            raise SchemaValidationError(
                f"freedom zone {self.zone_id} both fixes and frees {overlap}; decide which, otherwise "
                "an executor cannot tell latitude from instruction"
            )
        object.__setattr__(self, "free_paths", free)
        object.__setattr__(self, "fixed_paths", fixed)
        object.__setattr__(self, "latitude", FreedomZone.latitude_kind(self.latitude))
        if self.rationale is not None:
            object.__setattr__(self, "rationale", require_text(self.rationale, "rationale", maximum=4096))
        if self.granted_by is not None:
            object.__setattr__(self, "granted_by", SemanticRef.coerce(self.granted_by, "granted_by"))
        if self.expires_with_revision is not None:
            value = self.expires_with_revision
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise SchemaValidationError("expires_with_revision must be a positive revision number")

    @staticmethod
    def latitude_kind(value: Any) -> str:
        return LatitudeClass.parse(value, "latitude").value

    def covers(self, path: str) -> bool:
        prefix = require_semantic_path(path, "path")
        return any(
            prefix == free or prefix.startswith(free + ".") for free in self.free_paths
        ) and not any(
            prefix == fixed or prefix.startswith(fixed + ".") for fixed in self.fixed_paths
        )

    @property
    def zone_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.FREEDOM_ZONE.value, ref_id=self.zone_id).with_digest(self.digest())


class LatitudeClass(Labeled):
    """How much latitude a zone grants, stated so an executor does not negotiate with itself.

    ``ANY_WITHIN_BOUNDS`` and ``PREFERRED_RANGE`` differ only in whether a default is allowed
    to be applied outside the preferred set, which is precisely the distinction that turns a
    creative latitude into an unrecorded decision if it is left implicit.
    """

    ANY_WITHIN_BOUNDS = "ANY_WITHIN_BOUNDS"
    PREFERRED_RANGE = "PREFERRED_RANGE"
    SINGLE_DEGREE = "SINGLE_DEGREE"
    OPEN_WITHIN_BOUNDS = "OPEN_WITHIN_BOUNDS"


FreedomZone.NESTED = {"granted_by": of(SemanticRef)}


@dataclass(frozen=True)
class OpenQuestion(Record):
    """A question the brief owes somebody, with the answer channel recorded.

    An ``ANSWERED`` question must name the revision or ref that answered it, because a
    question closed by chat history is still open the moment the chat is gone: only a ref
    survives into the next compilation, and only a ref can be re-checked by an audit.
    """

    question_id: str
    text: str
    consequence: str = "NON_BLOCKING"
    status: str = "OPEN"
    semantic_paths: tuple[str, ...] = ()
    blocking: bool = False
    addressed_to: str | None = None
    answer_ref: SemanticRef | None = None
    related_statement_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "question_id", require_identifier(self.question_id, "question_id"))
        object.__setattr__(self, "text", require_text(self.text, "text", maximum=2048))
        consequence = AmbiguityConsequence.parse(self.consequence, "consequence")
        object.__setattr__(self, "consequence", consequence.value)
        status = QuestionStatus.parse(self.status, "status")
        object.__setattr__(self, "status", status.value)
        if self.blocking and not consequence.blocks_completion:
            raise SchemaValidationError(
                f"question {self.question_id} is flagged blocking but its consequence is "
                f"{consequence.value}; a flag nobody has to explain is a flag that gets ignored"
            )
        if self.blocking and status is QuestionStatus.ANSWERED:
            raise SchemaValidationError(
                f"question {self.question_id} was answered; clear the blocking flag instead of leaving "
                "a resolved question blocking admissions forever"
            )
        if status is QuestionStatus.ANSWERED and self.answer_ref is None:
            raise SchemaValidationError(
                f"question {self.question_id} is ANSWERED with no answer_ref, so nothing records what "
                "the answer was or who gave it"
            )
        object.__setattr__(self, "semantic_paths", _checked_paths(self.semantic_paths or ()))
        if self.addressed_to is not None:
            object.__setattr__(self, "addressed_to", require_identifier(self.addressed_to, "addressed_to"))
        if self.answer_ref is not None:
            object.__setattr__(self, "answer_ref", SemanticRef.coerce(self.answer_ref, "answer_ref"))
        object.__setattr__(
            self,
            "related_statement_ids",
            tuple(sorted({require_identifier(item, "related_statement_ids[]") for item in (self.related_statement_ids or ())})),
        )

    @property
    def is_open(self) -> bool:
        return QuestionStatus.parse(self.status) is QuestionStatus.OPEN

    @property
    def question_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.OPEN_QUESTION.value, ref_id=self.question_id).with_digest(self.digest())


OpenQuestion.NESTED = {"answer_ref": of(SemanticRef)}


@dataclass(frozen=True)
class ClarificationCandidate(Record):
    """One entry in the deterministic clarification queue.

    The priority is an integer tuple, not a score: consequence rank, then breadth, then path
    specificity, then id. A float-weighted ranking would look more intelligent and would
    make §18's "deterministic for identical normalized inputs" unfalsifiable, because two
    runs could disagree for reasons nobody can name.
    """

    ambiguity_id: str
    question: str
    consequence: str
    semantic_paths: tuple[str, ...]
    breadth: int
    specificity: int

    @property
    def sort_key(self) -> tuple[int, int, int, str]:
        return (
            -AmbiguityConsequence.parse(self.consequence).rank,
            -self.breadth,
            -self.specificity,
            self.ambiguity_id,
        )


@dataclass(frozen=True)
class AmbiguityAssessment(Record):
    """The completeness verdict for one revision's semantics.

    ``blocks_completion`` is computed, never stored: an assessment that recorded its own
    verdict would let someone admit a blocked compilation by flipping a field, and the whole
    point of §5.8 is that the block follows from what is unresolved.
    """

    brief_id: str
    revision_id: str
    ambiguities: tuple[AmbiguityRecord, ...] = ()
    freedom_zones: tuple[FreedomZone, ...] = ()
    open_questions: tuple[OpenQuestion, ...] = ()
    statements: tuple[IntentStatement, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "brief_id", require_identifier(self.brief_id, "brief_id"))
        object.__setattr__(self, "revision_id", require_identifier(self.revision_id, "revision_id"))
        ambiguities = tuple(AmbiguityRecord.coerce(item, "ambiguities[]") for item in _seq(self.ambiguities, "ambiguities"))
        if len(ambiguities) > MAX_AMBIGUITIES:
            raise SchemaValidationError(f"ambiguities exceeds {MAX_AMBIGUITIES}")
        ids = [item.ambiguity_id for item in ambiguities]
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            raise SchemaValidationError(f"ambiguities contains duplicate ids: {duplicates}")
        object.__setattr__(self, "ambiguities", tuple(sorted(ambiguities, key=lambda item: item.ambiguity_id)))
        zones = tuple(FreedomZone.coerce(item, "freedom_zones[]") for item in _seq(self.freedom_zones, "freedom_zones"))
        if len(zones) > MAX_FREEDOM_ZONES:
            raise SchemaValidationError(f"freedom_zones exceeds {MAX_FREEDOM_ZONES}")
        zone_ids = [item.zone_id for item in zones]
        if len(set(zone_ids)) != len(zone_ids):
            raise SchemaValidationError("freedom_zones contains duplicate zone_ids")
        object.__setattr__(self, "freedom_zones", tuple(sorted(zones, key=lambda item: item.zone_id)))
        questions = tuple(OpenQuestion.coerce(item, "open_questions[]") for item in _seq(self.open_questions, "open_questions"))
        if len(questions) > MAX_OPEN_QUESTIONS:
            raise SchemaValidationError(f"open_questions exceeds {MAX_OPEN_QUESTIONS}")
        object.__setattr__(self, "open_questions", tuple(sorted(questions, key=lambda item: item.question_id)))
        statements = tuple(IntentStatement.coerce(item, "statements[]") for item in _seq(self.statements, "statements"))
        object.__setattr__(self, "statements", tuple(sorted(statements, key=lambda item: (item.semantic_path, item.statement_id))))

    @property
    def blocking_ambiguities(self) -> tuple[AmbiguityRecord, ...]:
        return tuple(item for item in self.ambiguities if item.blocks())

    @property
    def blocking_questions(self) -> tuple[OpenQuestion, ...]:
        return tuple(item for item in self.open_questions if item.blocking)

    @property
    def blocks_completion(self) -> bool:
        return bool(self.blocking_ambiguities or self.blocking_questions)

    @property
    def quality_critical(self) -> tuple[AmbiguityRecord, ...]:
        return tuple(
            item for item in self.ambiguities if item.consequence == AmbiguityConsequence.QUALITY_CRITICAL.value
        )

    @property
    def cost_critical(self) -> tuple[AmbiguityRecord, ...]:
        return tuple(item for item in self.ambiguities if item.consequence == AmbiguityConsequence.COST_CRITICAL.value)

    @property
    def freedom_zones_contested(self) -> tuple[str, ...]:
        """Zones whose latitude a critical ambiguity says is actually an unresolved question.

        Reported, not resolved: whether the client meant "any colour" or "we never told you"
        is their call, and the assessment that guessed either way would be recording its own
        conclusion as evidence (§5.7).
        """

        return tuple(
            sorted(
                {
                    zone.zone_id
                    for item in self.ambiguities
                    for zone in self.freedom_zones
                    if zone.covers(item.semantic_paths[0])
                    and AmbiguityConsequence.parse(item.consequence).rank
                    >= AmbiguityConsequence.COST_CRITICAL.rank
                }
            )
        )

    @property
    def freedom_as_gap(self) -> tuple[str, ...]:
        """Ambiguities recorded as creative freedom that are not inside any granted zone.

        Reclassifying them silently would be the promotion §5.7 forbids, so the assessment
        names the disagreement and leaves the decision where it belongs.
        """

        return tuple(
            sorted(
                item.ambiguity_id
                for item in self.ambiguities
                if item.consequence == AmbiguityConsequence.CREATIVE_FREEDOM.value
                and not any(zone.covers(path) for zone in self.freedom_zones for path in item.semantic_paths)
            )
        )

    @property
    def clarification_queue(self) -> tuple[ClarificationCandidate, ...]:
        return rank_clarifications(self.ambiguities)

    def require_admissible(self, action: str) -> None:
        """Refuse to compile or release while something blocking is unresolved (§5.8)."""

        if self.blocks_completion:
            raise AmbiguityBlockedError(
                f"cannot {action} for {self.brief_id}@{self.revision_id}: unresolved blocking "
                f"ambiguity {[item.ambiguity_id for item in self.blocking_ambiguities]} and open "
                f"questions {[item.question_id for item in self.blocking_questions]}"
            )

    def free_paths(self) -> tuple[str, ...]:
        return tuple(sorted({path for zone in self.freedom_zones for path in zone.free_paths}))

    def covered_statements(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                item.statement_id
                for item in self.statements
                if any(zone.covers(item.semantic_path) for zone in self.freedom_zones)
            )
        )


AmbiguityAssessment.NESTED = {
    "ambiguities": of(AmbiguityRecord),
    "freedom_zones": of(FreedomZone),
    "open_questions": of(OpenQuestion),
    "statements": of(IntentStatement),
}


def _seq(value: Any, field_name: str) -> Iterable[Any]:
    if not isinstance(value, (list, tuple)):
        raise SchemaValidationError(f"{field_name} must be a list")
    return value


def rank_clarifications(records: Iterable[Any]) -> tuple[ClarificationCandidate, ...]:
    """Order what to ask about, deterministically and without asking anybody.

    Breadth and specificity beat a hunch: the question that unblocks the most semantics at the
    narrowest path is the one worth asking first, and both of those are countable from the
    record itself, so two runs over the same input cannot disagree (§18).
    """

    candidates = [
        ClarificationCandidate(
            ambiguity_id=item.ambiguity_id,
            question=item.question,
            consequence=item.consequence,
            semantic_paths=item.semantic_paths,
            breadth=item.breadth,
            specificity=max((len(path.split(".")) for path in item.semantic_paths), default=1),
        )
        for item in records
    ]
    ordered = sorted(candidates, key=lambda item: item.sort_key)
    return tuple(ordered)


def require_freedom_honoured(zones: Iterable[Any], statements: Iterable[Any]) -> None:
    """Refuse a defaulted value that quietly answers an open creative question.

    The check runs the other way from the obvious one: a human choosing inside a zone is what
    the zone is for, but a *default* — a value nobody was asked about — converts granted
    latitude into an unattributed decision. Only a governed policy default survives here,
    because that is the one case where the choice has an owner behind it, and the alternative
    is a kernel that fills in the client's latitude and reports it as their brief (§5.7).
    """

    collected = [FreedomZone.coerce(zone, "zones[]") for zone in zones]
    if not collected:
        return
    for statement in statements:
        item = IntentStatement.coerce(statement, "statements[]")
        if item.origin != IntentOrigin.DEFAULTED.value:
            continue
        covering = [zone.zone_id for zone in collected if zone.covers(item.semantic_path)]
        governed = item.authority.basis == "POLICY" or item.authority.level.rank >= AuthorityLevel.GOVERNED_POLICY.rank
        if covering and not governed:
            raise AmbiguityBlockedError(
                f"statement {item.statement_id} defaults a value inside freedom zone {covering[0]} "
                f"on a {item.authority.basis} basis; latitude is left open on purpose, so filling it "
                "takes an admitted revision or a bound policy default, not a normalization choice"
            )
