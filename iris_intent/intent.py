"""F-M03-01 Intent Semantic Core: typed statements assembled into an intent model.

A statement is a proposition about what the work must mean, addressed by a semantic path
(``identity.spokesperson.demeanor``), not a fragment of prompt text. That distinction is the
whole reason M03 exists (§5.9): a prompt is a provider artifact that changes when the model
changes, while "the spokesperson must not smile in commercial contexts" is the thing the
provider is being asked to realise, and it has to survive the provider.

Origin and authority are checked against each other here, at construction, because the most
damaging failure in a normaliser is not a wrong value — it is a guess that later reads as
something the client asked for. So ``INFERRED`` cannot carry ``HUMAN_OWNER`` authority and
``EXPLICIT`` cannot be satisfied by a model's confidence (§5.4, §7, §18). The one place that
could rewrite an inference into an explicit truth is a new governed revision, which lives in
``briefs.py`` and requires a human or policy grant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from .base import Labeled, Record, of
from .errors import (
    AuthorityError,
    LimitExceededError,
    QualityAuthorityError,
    RefError,
    SchemaValidationError,
)
from .identity import (
    AuthorityLevel,
    RefKind,
    SemanticRef,
    require_bound_ref,
)
from .limits import MAX_STATEMENTS_PER_MODEL
from .sources import ProvenanceCapsule, bounded_metadata
from .versions import (
    QualityClass,
    require_identifier,
    require_semantic_path,
    require_text,
    require_unit_interval,
)

__all__ = [
    "IntentAuthorityRef",
    "IntentModel",
    "IntentOrigin",
    "IntentStatement",
    "MAX_STATEMENTS_PER_MODEL",
    "ModalChannel",
    "StatementKind",
    "authority_ceiling_for_origin",
]


class StatementKind(Labeled):
    """What role a statement plays in the brief.

    The set mirrors the semantics §7 requires the kernel to represent — purpose, audience,
    outcome, deliverable, direction, reference — and adds the axes the six domains need
    without borrowing their vocabulary: ``SUBJECT`` names what the work is about,
    ``MODALITY`` says which channel it lives in, and ``QUALITY_TARGET`` is where a human
    states a rung they want reached, never where an adjective reaches it by itself (§5.20).
    """

    PURPOSE = "PURPOSE"
    AUDIENCE = "AUDIENCE"
    OUTCOME = "OUTCOME"
    DELIVERABLE = "DELIVERABLE"
    SUBJECT = "SUBJECT"
    DIRECTION = "DIRECTION"
    STYLE = "STYLE"
    IDENTITY = "IDENTITY"
    CANON = "CANON"
    CONSTRAINT_SEMANTICS = "CONSTRAINT_SEMANTICS"
    MODALITY = "MODALITY"
    TEMPORAL = "TEMPORAL"
    QUALITY_TARGET = "QUALITY_TARGET"
    REFERENCE = "REFERENCE"
    ANTI_REFERENCE = "ANTI_REFERENCE"


class ModalChannel(Labeled):
    """The expressive channel a statement is about, or ``MULTI`` when it spans them.

    ``CROSS`` is deliberately a first-class value rather than a gap in coverage: a brief for
    a spokesperson who must look and sound like the same person is one statement, and a
    kernel that could only say "visual" would have to invent two facts and hope they matched
    (§6, §18 multimodal).
    """

    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    MOTION = "MOTION"
    AUDIO = "AUDIO"
    SPEECH = "SPEECH"
    MUSIC = "MUSIC"
    GEOMETRY = "GEOMETRY"
    MATERIAL = "MATERIAL"
    INTERFACE = "INTERFACE"
    BRAND = "BRAND"
    CROSS = "CROSS"
    UNSPECIFIED = "UNSPECIFIED"


class IntentOrigin(Labeled):
    """How the kernel came to hold this statement — never *who* authorised it.

    Those two axes are independent by §5.5, and this enum is only half of the pair: an
    ``EXPLICIT`` statement written by a model summarising a human message is still explicit
    about its content and needs the authority field to say who stands behind it.
    """

    EXPLICIT = "EXPLICIT"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    DEFAULTED = "DEFAULTED"

    @property
    def is_user_asserted(self) -> bool:
        return self is IntentOrigin.EXPLICIT

    @property
    def needs_ancestor(self) -> bool:
        """Derived and inferred statements must point at what they came from.

        A statement with no ancestors and no source is a guess with the provenance record of
        a fact, and §16 asks the kernel to be able to answer "where did this come from" for
        every admitted object.
        """

        return self in {IntentOrigin.DERIVED, IntentOrigin.INFERRED}


_ORIGIN_CEILINGS: Mapping[IntentOrigin, AuthorityLevel] = MappingProxyType({
    IntentOrigin.EXPLICIT: AuthorityLevel.HUMAN_OWNER,
    IntentOrigin.DERIVED: AuthorityLevel.GOVERNED_POLICY,
    IntentOrigin.INFERRED: AuthorityLevel.MODEL_INFERRED,
    # A default applied by governed policy is legitimately governed; a default applied by the
    # normaliser on its own initiative is not, and the ceiling is what keeps those apart.
    IntentOrigin.DEFAULTED: AuthorityLevel.GOVERNED_POLICY,
})

#: The weakest authority an origin may hold, as well as the strongest.
_ORIGIN_FLOORS: Mapping[IntentOrigin, AuthorityLevel] = MappingProxyType({
    IntentOrigin.EXPLICIT: AuthorityLevel.TEAM_ASSERTED,
    IntentOrigin.DERIVED: AuthorityLevel.PROJECT_RECORD,
    IntentOrigin.INFERRED: AuthorityLevel.UNTRUSTED,
    IntentOrigin.DEFAULTED: AuthorityLevel.PROJECT_RECORD,
})


def authority_ceiling_for_origin(origin: Any) -> AuthorityLevel:
    return _ORIGIN_CEILINGS[IntentOrigin.parse(origin, "origin")]


@dataclass(frozen=True)
class IntentAuthorityRef(Record):
    """Who stands behind a statement, and what they stood behind it with.

    ``basis`` is not a free-text excuse: a grant above project-record authority has to name
    either an admitted human revision or a governed policy ref, so "the client surely meant"
    cannot be encoded as authority. Anything looser is a field someone edits during a
    dispute, and the point of the ref is that it is the thing the dispute is *about*.
    """

    authority: str
    basis: str = "REVISION"
    granted_by: SemanticRef | None = None
    policy_ref: SemanticRef | None = None
    rationale: str | None = None

    def __post_init__(self) -> None:
        level = AuthorityLevel.parse(self.authority, "authority")
        object.__setattr__(self, "authority", level.value)
        basis = AuthorityBasis.parse(self.basis, "basis")
        object.__setattr__(self, "basis", basis.value)
        if self.granted_by is not None:
            object.__setattr__(self, "granted_by", SemanticRef.coerce(self.granted_by, "granted_by"))
        if self.policy_ref is not None:
            object.__setattr__(self, "policy_ref", require_bound_ref(self.policy_ref, "policy_ref", kind=RefKind.POLICY))
        if self.rationale is not None:
            object.__setattr__(self, "rationale", require_text(self.rationale, "rationale", maximum=4096))
        if level.rank > AuthorityLevel.PROJECT_RECORD.rank:
            if basis is AuthorityBasis.REVISION and self.granted_by is None:
                raise AuthorityError(
                    f"{level.value} authority needs a granted_by revision ref naming who admitted it; "
                    "authority above project record cannot rest on an unattributed claim"
                )
            if basis is AuthorityBasis.POLICY and self.policy_ref is None:
                raise AuthorityError(
                    f"{level.value} authority asserted on a policy basis must bind the policy ref"
                )
            if basis not in {AuthorityBasis.REVISION, AuthorityBasis.POLICY}:
                raise AuthorityError(
                    f"{level.value} authority cannot rest on a {basis.value} basis; only an admitted "
                    "revision or a bound policy ref raises a statement above project record"
                )

    @property
    def level(self) -> AuthorityLevel:
        return AuthorityLevel.parse(self.authority)


class AuthorityBasis(Labeled):
    """The kind of thing backing an authority claim."""

    REVISION = "REVISION"
    POLICY = "POLICY"
    PROJECT_RECORD = "PROJECT_RECORD"
    DERIVATION = "DERIVATION"
    SELF_ASSERTED = "SELF_ASSERTED"


IntentAuthorityRef.NESTED = {"granted_by": of(SemanticRef), "policy_ref": of(SemanticRef)}


@dataclass(frozen=True)
class IntentStatement(Record):
    """One typed, path-addressed proposition with its origin, authority and provenance.

    ``value`` is bounded structured data rather than prose so that two statements can be
    compared, sliced and fingerprinted without parsing English; ``assertion`` is the
    human-readable form kept alongside it for the explanation layer, which is allowed to be
    wordy precisely because nothing keys off it.
    """

    statement_id: str
    semantic_path: str
    kind: str
    assertion: str
    origin: str
    authority: IntentAuthorityRef
    modality: str = "UNSPECIFIED"
    subject_ref: SemanticRef | None = None
    value: Mapping[str, str] = field(default_factory=dict)
    facets: tuple[str, ...] = ()
    confidence: float | None = None
    mandatory: bool = False
    provenance: ProvenanceCapsule | None = None
    source_statement_ids: tuple[str, ...] = ()
    revision_ref: SemanticRef | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "statement_id", require_identifier(self.statement_id, "statement_id"))
        object.__setattr__(self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path"))
        object.__setattr__(self, "kind", StatementKind.parse(self.kind, "kind").value)
        object.__setattr__(self, "modality", ModalChannel.parse(self.modality, "modality").value)
        object.__setattr__(self, "assertion", require_text(self.assertion, "assertion", maximum=4096))
        origin = IntentOrigin.parse(self.origin, "origin")
        object.__setattr__(self, "origin", origin.value)
        authority = IntentAuthorityRef.coerce(self.authority, "authority")
        if not isinstance(authority, IntentAuthorityRef):
            raise SchemaValidationError("authority must be an IntentAuthorityRef")
        level = authority.level
        ceiling = _ORIGIN_CEILINGS[origin]
        floor = _ORIGIN_FLOORS[origin]
        if level.rank > ceiling.rank:
            raise AuthorityError(
                f"{origin.value} statement {self.statement_id} cannot hold {level.value} authority "
                f"(ceiling {ceiling.value}); promoting a normalised inference to user-explicit truth "
                "takes a new governed revision, not a field on the statement"
            )
        if level.rank < floor.rank and origin is not IntentOrigin.INFERRED:
            raise AuthorityError(
                f"{origin.value} statement {self.statement_id} needs at least {floor.value} "
                f"authority, got {level.value}"
            )
        object.__setattr__(self, "authority", authority)
        if self.subject_ref is not None:
            object.__setattr__(self, "subject_ref", SemanticRef.coerce(self.subject_ref, "subject_ref"))
        object.__setattr__(self, "value", bounded_metadata(self.value, "value"))
        facets = _checked_facets(self.facets)
        object.__setattr__(self, "facets", facets)
        if self.kind == StatementKind.QUALITY_TARGET.value:
            if "quality_class" not in self.value:
                raise SchemaValidationError(
                    f"{self.statement_id} is a QUALITY_TARGET statement but names no rung: an "
                    "unstructured quality wish is exactly the vague adjective §5.20 refuses to let "
                    "choose a class, so state the rung or do not claim to target one"
                )
            rung = QualityClass.parse(self.value["quality_class"])
            value = dict(self.value)
            value["quality_class"] = rung.value
            object.__setattr__(self, "value", value)
        if self.confidence is not None:
            object.__setattr__(self, "confidence", require_unit_interval(self.confidence, "confidence"))
        if not isinstance(self.mandatory, bool):
            raise SchemaValidationError("mandatory must be a boolean")
        if self.provenance is not None:
            object.__setattr__(self, "provenance", ProvenanceCapsule.coerce(self.provenance, "provenance"))
        if origin.needs_ancestor and not self.source_statement_ids and (
            self.provenance is None or not self.provenance.ancestor_refs
        ):
            raise SchemaValidationError(
                f"{origin.value} statement {self.statement_id} names no ancestor: derived semantics "
                "with no parent are how an invented fact acquires a provenance record"
            )
        if origin is IntentOrigin.EXPLICIT and self.provenance is None:
            raise SchemaValidationError(
                f"explicit statement {self.statement_id} needs a provenance capsule, otherwise nothing "
                "connects it back to the words that were said"
            )
        if self.revision_ref is not None:
            object.__setattr__(self, "revision_ref", SemanticRef.coerce(self.revision_ref, "revision_ref"))
        sources = self.source_statement_ids
        if not isinstance(sources, (list, tuple)):
            raise SchemaValidationError("source_statement_ids must be a list of identifiers")
        object.__setattr__(
            self, "source_statement_ids", tuple(sorted(require_identifier(item, "source_statement_ids[]") for item in sources))
        )
        if self.statement_id in self.source_statement_ids:
            raise RefError(f"statement {self.statement_id} lists itself as its own source")

    @property
    def authority_level(self) -> AuthorityLevel:
        return self.authority.level

    @property
    def explicit(self) -> bool:
        return self.origin == IntentOrigin.EXPLICIT.value and self.authority.level.self_asserting_is_enough

    @property
    def path_segments(self) -> tuple[str, ...]:
        return tuple(self.semantic_path.split("."))

    def on_path(self, prefix: str) -> bool:
        normalized = require_semantic_path(prefix, "prefix")
        return self.semantic_path == normalized or self.semantic_path.startswith(normalized + ".")

    @property
    def statement_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.STATEMENT.value, ref_id=self.statement_id).with_digest(self.digest())

    def quality_class_is_admissible(self) -> bool:
        """A named rung may reach the fidelity bridge only from an explicit, human-backed statement.

        §5.20 forbids vague adjectives choosing a QualityClass, and the honest version of
        that rule is not a word list — it is a check on the *authority* behind the statement
        that names the rung, because "premium", "polished" and "high quality" are exactly
        what an inferred statement is made of.
        """

        if self.kind != StatementKind.QUALITY_TARGET.value:
            raise SchemaValidationError(
                f"{self.statement_id} is a {self.kind} statement, so it cannot carry a quality-class request"
            )
        return self.explicit


IntentStatement.NESTED = {
    "authority": of(IntentAuthorityRef),
    "subject_ref": of(SemanticRef),
    "revision_ref": of(SemanticRef),
    "provenance": of(ProvenanceCapsule),
}


def _checked_facets(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise SchemaValidationError("facets must be a list of identifiers")
    if len(value) > 64:
        raise LimitExceededError("facets exceeds 64 entries")
    facets = tuple(require_identifier(item, "facets[]").lower() for item in value)
    duplicates = sorted({item for item in facets if facets.count(item) > 1})
    if duplicates:
        raise SchemaValidationError(f"facets contains duplicates: {duplicates}")
    return tuple(sorted(facets))


@dataclass(frozen=True)
class IntentModel(Record):
    """The assembled, revision-bound semantics of one brief revision.

    An ``IntentModel`` is not a mutable working set: it names the revision it came from and
    digests its own statements, so "the intent" is always a specific frozen thing that a
    fingerprint, a slice and an explanation can refer to. Changing it means a new model over
    a new revision, which is what makes staleness detectable at all (§5.38).
    """

    model_id: str
    brief_id: str
    revision_id: str
    revision_number: int
    statements: tuple[IntentStatement, ...]
    open_questions: tuple[str, ...] = ()
    requested_quality_class: str | None = None
    modalities: tuple[str, ...] = ()
    model_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "model_id", require_identifier(self.model_id, "model_id"))
        object.__setattr__(self, "brief_id", require_identifier(self.brief_id, "brief_id"))
        object.__setattr__(self, "revision_id", require_identifier(self.revision_id, "revision_id"))
        if isinstance(self.revision_number, bool) or not isinstance(self.revision_number, int) or self.revision_number < 1:
            raise SchemaValidationError("revision_number must be a positive integer")
        statements = tuple(IntentStatement.coerce(item, "statements[]") for item in _require_sequence(self.statements, "statements"))
        if not statements:
            raise SchemaValidationError(
                "an intent model with no statements describes no work; say what is missing instead of "
                "emitting an empty model that downstream readers will trust"
            )
        if len(statements) > MAX_STATEMENTS_PER_MODEL:
            raise LimitExceededError(
                f"statements exceeds {MAX_STATEMENTS_PER_MODEL}; a brief that large is several briefs "
                "and should be split before it is compiled"
            )
        ids = [item.statement_id for item in statements]
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            raise SchemaValidationError(f"statements contains duplicate statement_ids: {duplicates}")
        object.__setattr__(self, "statements", tuple(sorted(statements, key=lambda item: (item.semantic_path, item.statement_id))))
        questions = tuple(sorted({require_identifier(item, "open_questions[]") for item in (self.open_questions or ())}))
        object.__setattr__(self, "open_questions", questions)
        if self.requested_quality_class is not None:
            object.__setattr__(
                self,
                "requested_quality_class",
                _checked_quality_request(self.requested_quality_class, statements),
            )
        modalities = tuple(sorted({ModalChannel.parse(item, "modalities[]").value for item in (self.modalities or ())}))
        declared = sorted({item.modality for item in statements})
        if modalities and set(modalities) - set(declared) - {"CROSS"}:
            raise SchemaValidationError(
                f"modalities {sorted(set(modalities) - set(declared) - {'CROSS'})} name no statement; a "
                "modality the model does not actually carry would make every consumer of it look covered"
            )
        object.__setattr__(self, "modalities", tuple(modalities) or tuple(declared))
        if self.model_digest is not None:
            if self.model_digest != self._compute_digest():
                raise SchemaValidationError(
                    "model_digest does not match the statements it claims to summarise; the model was "
                    "altered after it was built"
                )
        else:
            object.__setattr__(self, "model_digest", self._compute_digest())

    def _compute_digest(self) -> str:
        from .versions import content_digest

        return content_digest(
            {
                "brief_id": self.brief_id,
                "revision_id": self.revision_id,
                "statements": [item.to_payload() for item in self.statements],
            }
        )

    @property
    def statement_ids(self) -> tuple[str, ...]:
        return tuple(item.statement_id for item in self.statements)

    def statement(self, statement_id: str) -> IntentStatement | None:
        return next((item for item in self.statements if item.statement_id == statement_id), None)

    def require_statement(self, statement_id: str) -> IntentStatement:
        found = self.statement(statement_id)
        if found is None:
            raise RefError(f"{statement_id} is not a statement of model {self.model_id}")
        return found

    def on_path(self, prefix: str) -> tuple[IntentStatement, ...]:
        return tuple(item for item in self.statements if item.on_path(prefix))

    def by_kind(self, kind: Any) -> tuple[IntentStatement, ...]:
        label = StatementKind.parse(kind, "kind").value
        return tuple(item for item in self.statements if item.kind == label)

    def by_origin(self, origin: Any) -> tuple[IntentStatement, ...]:
        label = IntentOrigin.parse(origin, "origin").value
        return tuple(item for item in self.statements if item.origin == label)

    def by_modality(self, modality: Any) -> tuple[IntentStatement, ...]:
        label = ModalChannel.parse(modality, "modality").value
        return tuple(item for item in self.statements if item.modality in {label, ModalChannel.CROSS.value})

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(sorted({item.semantic_path for item in self.statements}))

    @property
    def mandatory_paths(self) -> tuple[str, ...]:
        return tuple(sorted({item.semantic_path for item in self.statements if item.mandatory}))

    @property
    def explicit_statements(self) -> tuple[IntentStatement, ...]:
        return tuple(item for item in self.statements if item.explicit)

    @property
    def inferred_or_defaulted(self) -> tuple[IntentStatement, ...]:
        return tuple(
            item
            for item in self.statements
            if item.origin in {IntentOrigin.INFERRED.value, IntentOrigin.DEFAULTED.value}
        )

    @property
    def max_authority(self) -> AuthorityLevel:
        return max((item.authority_level for item in self.statements), key=lambda level: level.rank)

    def ancestors_of(self, statement_id: str) -> tuple[str, ...]:
        """Walk the derivation chain upward, deterministically and cycle-safe.

        Derivation is a acyclic-by-construction relation in an admitted revision, but the
        kernel still refuses to loop: a self-referential chain would otherwise turn
        "what does this depend on" into a hang, and a hang is a much worse failure than a
        raised error at the point someone is auditing.
        """

        seen: list[str] = []
        frontier = [statement_id]
        while frontier:
            current = frontier.pop()
            statement = self.statement(current)
            if statement is None:
                continue
            for parent in statement.source_statement_ids:
                if parent in seen:
                    raise RefError(
                        f"derivation cycle: {parent} is its own ancestor in model {self.model_id}"
                    )
                if parent != statement_id:
                    seen.append(parent)
                    frontier.append(parent)
        return tuple(sorted(set(seen)))

    def dependents_of(self, statement_id: str) -> tuple[str, ...]:
        """Statements derived from ``statement_id``, transitively — the staleness frontier."""

        collected: set[str] = set()
        frontier = {statement_id}
        while frontier:
            current = frontier.pop()
            for item in self.statements:
                if current in item.source_statement_ids and item.statement_id not in collected:
                    if item.statement_id == statement_id:
                        raise RefError(
                            f"statement {statement_id} derives from itself in model {self.model_id}"
                        )
                    collected.add(item.statement_id)
                    frontier.add(item.statement_id)
        return tuple(sorted(collected))

    def reaches_provenance(self, source_id: str) -> tuple[str, ...]:
        return tuple(sorted(item.statement_id for item in self.statements if item.provenance is not None and item.provenance.reaches(source_id)))

    def quality_requests(self) -> tuple[IntentStatement, ...]:
        return self.by_kind(StatementKind.QUALITY_TARGET)

    def fingerprint_inputs(self) -> tuple[tuple[str, str, str, str, str], ...]:
        """The canonical, order-free tuple the semantic fingerprint is computed from.

        Authority and origin are included and wording is not: a restatement that keeps the
        same meaning under the same authority must fingerprint the same (§5.45), while a
        statement that quietly gained human authority from a model's summary must not.
        """

        return tuple(
            sorted(
                (
                    item.semantic_path,
                    item.kind,
                    item.modality,
                    item.origin,
                    item.authority.authority,
                )
                for item in self.statements
            )
        )

    @property
    def model_ref(self) -> SemanticRef:
        return SemanticRef(
            kind=RefKind.STATEMENT.value,
            ref_id=self.model_id,
            content_digest=self.model_digest,
        )


IntentModel.NESTED = {"statements": of(IntentStatement)}


def _require_sequence(value: Any, field_name: str) -> Iterable[Any]:
    if not isinstance(value, (list, tuple)):
        raise SchemaValidationError(f"{field_name} must be a list")
    return value


def _checked_quality_request(value: str, statements: tuple[IntentStatement, ...]) -> str:
    """Accept a requested rung only when an explicit, human-backed statement asked for it.

    The failure this closes is the quiet one: a compiler that lets scarcity, cost or an
    inferred adjective move the ladder still produces a valid-looking contract, and the only
    evidence that the client wanted something higher was a field nobody checked. So the
    request is validated against the statements rather than against a caller's assertion, and
    lowering it later is a governed act that lives in S05, not a normalization detail
    (§5.20, §5.21).
    """

    rung = QualityClass.parse(value)
    backing = [
        item
        for item in statements
        if item.kind == StatementKind.QUALITY_TARGET.value and item.quality_class_is_admissible()
    ]
    if not backing:
        raise QualityAuthorityError(
            f"requested_quality_class {rung.value} has no explicit QUALITY_TARGET statement behind it; "
            "vague adjectives, inferred polish and hardware scarcity do not choose a rung"
        )
    asked = max((QualityClass.parse(item.value["quality_class"]) for item in backing), key=lambda item: item.ladder_rank)
    if rung.ladder_rank > asked.ladder_rank:
        raise QualityAuthorityError(
            f"requested_quality_class {rung.value} exceeds the highest explicitly requested rung "
            f"{asked.value}; M03 records what was asked for and cannot raise the bar on someone's behalf"
        )
    if rung.ladder_rank < asked.ladder_rank:
        raise QualityAuthorityError(
            f"requested_quality_class {rung.value} is below the explicitly requested {asked.value}; "
            "scarcity, cost and provider capability are handled as gaps in S03/S04, never by lowering "
            "the rung the client named (§5.21)"
        )
    return rung.value
