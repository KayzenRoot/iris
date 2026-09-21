"""Immutable brief revisions: lineage, admission, and the semantics a revision carries.

A revision is the unit of M03 history, and the rule it exists to enforce is small but
consequential: once admitted it never changes (§5.3). Everything downstream — fingerprints,
compilations, override receipts, reuse passports — refers to a revision by id and digest, so
an in-place edit would leave that evidence pointing at something that no longer describes the
work, and the audit trail would read as though nothing had moved. `RevisionFrozenError` is
raised instead, and the caller gets a superseding revision whose predecessor is recorded.

The distinction between a *semantic* digest and a *wording* digest earns its keep in §18: a
rename or a rephrasing must not replace what downstream work refers to, so those edits move
the content digest and leave the semantic digest alone, while anything that changes a
statement's path, kind, origin or authority moves both. Which fields belong to which digest
is stated once, here, rather than being left to whatever a diff helper happens to read.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .base import Labeled, Record, of
from .errors import (
    RevisionFrozenError,
    SchemaValidationError,
)
from .identity import (
    AuthorityLevel,
    BriefRevisionRef,
    CreativeBriefIdentity,
    RefKind,
    SemanticRef,
    check_ancestry,
    require_authority,
)
from .intent import IntentModel, IntentStatement
from .limits import MAX_ANCESTORS
from .sources import RawInputRef
from .versions import require_identifier, require_text

__all__ = [
    "BriefRevision",
    "RevisionKind",
    "RevisionStatus",
    "intent_model_for",
    "semantic_fields",
]


class RevisionKind(Labeled):
    """Why a revision exists, recorded rather than inferred from a diff.

    ``RESTORATION`` and ``MIGRATION`` are kinds rather than flags because §5.36 and §5.37
    make the same demand of both: they create new history and never rewrite old history. A
    reader who sees one of these knows, without recomputing anything, that the predecessor is
    still the record of what was believed at the time.
    """

    INITIAL = "INITIAL"
    CLARIFICATION = "CLARIFICATION"
    CORRECTION = "CORRECTION"
    EXTENSION = "EXTENSION"
    RESTATEMENT = "RESTATEMENT"
    EXPLORATION = "EXPLORATION"
    SCOPE_SPLIT = "SCOPE_SPLIT"
    RESTORATION = "RESTORATION"
    MIGRATION = "MIGRATION"


class RevisionStatus(Labeled):
    """Where a revision sits in its own lifecycle.

    ``DRAFT`` is the only editable state, and it is not an admission: nothing downstream may
    bind to a draft, which is what stops an in-progress revision from being read as governed
    input while somebody is still typing.
    """

    DRAFT = "DRAFT"
    ADMITTED = "ADMITTED"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"

    @property
    def editable(self) -> bool:
        return self is RevisionStatus.DRAFT


#: Fields that carry meaning. Wording, labels and bookkeeping are deliberately excluded so a
#: rephrase cannot invalidate the reuse it was pinned to (§5.45).
_SEMANTIC_FIELDS = (
    "statements",
    "sources",
    "kind",
)


def semantic_fields() -> tuple[str, ...]:
    return _SEMANTIC_FIELDS


@dataclass(frozen=True)
class BriefRevision(Record):
    """One frozen snapshot of a brief: its preserved sources and its typed statements.

    ``sources`` and ``statements`` are kept as separate collections rather than folded
    together, because §5.1 requires the raw input to survive normalization *as* raw input:
    the statements are what the kernel believes, the sources are what was actually said, and
    a reader must be able to disagree with the first without losing the second.
    """

    revision_id: str
    brief_id: str
    revision_number: int
    kind: str
    status: str = "DRAFT"
    statements: tuple[IntentStatement, ...] = ()
    sources: tuple[RawInputRef, ...] = ()
    predecessor_revision_id: str | None = None
    ancestor_revision_ids: tuple[str, ...] = ()
    created_by: SemanticRef | None = None
    admitted_by: SemanticRef | None = None
    supersedes_statement_ids: tuple[str, ...] = ()
    label: str | None = None
    notes: str | None = None
    recorded_at: str | None = None
    content_digest: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "revision_id", require_identifier(self.revision_id, "revision_id"))
        object.__setattr__(self, "brief_id", require_identifier(self.brief_id, "brief_id"))
        if isinstance(self.revision_number, bool) or not isinstance(self.revision_number, int) or self.revision_number < 1:
            raise SchemaValidationError("revision_number must be a positive integer")
        object.__setattr__(self, "kind", RevisionKind.parse(self.kind, "kind").value)
        status = RevisionStatus.parse(self.status, "status")
        object.__setattr__(self, "status", status.value)
        statements = tuple(IntentStatement.coerce(item, "statements[]") for item in _sequence(self.statements, "statements"))
        cited = {
            ref.ref_id
            for item in statements
            if item.provenance is not None
            for ref in item.provenance.source_refs
            if ref.kind == RefKind.SOURCE.value
        }
        objects = tuple(RawInputRef.coerce(item, "sources[]") for item in _sequence(self.sources, "sources"))
        known = {item.source_id for item in objects}
        missing = sorted(cited - known)
        if missing:
            raise SchemaValidationError(
                f"statements cite sources {missing} that this revision does not preserve; admitting a "
                "revision whose evidence is not attached is how a normalized claim outlives the text "
                "it came from"
            )
        duplicates = sorted({item.source_id for item in objects if [x.source_id for x in objects].count(item.source_id) > 1})
        if duplicates:
            raise SchemaValidationError(f"sources contains duplicate source_ids: {duplicates}")
        object.__setattr__(self, "statements", tuple(sorted(statements, key=lambda item: (item.semantic_path, item.statement_id))))
        object.__setattr__(self, "sources", tuple(sorted(objects, key=lambda item: item.source_id)))
        ancestors = check_ancestry(self.ancestor_revision_ids)
        if len(statements) and self.revision_number == 1 and ancestors:
            raise SchemaValidationError("revision 1 cannot have ancestors")
        if self.revision_number > 1 and not ancestors:
            raise SchemaValidationError(
                f"revision {self.revision_number} has no ancestor chain; history that starts at "
                "number two is not history, it is a gap somebody walked past"
            )
        if self.predecessor_revision_id is not None:
            predecessor = require_identifier(self.predecessor_revision_id, "predecessor_revision_id")
            if self.revision_number == 1:
                raise SchemaValidationError("revision 1 cannot have a predecessor")
            if not ancestors or ancestors[-1] != predecessor:
                raise SchemaValidationError(
                    f"predecessor {predecessor} is not the last ancestor ({ancestors[-1] if ancestors else None})"
                )
            if predecessor == self.revision_id:
                raise RevisionFrozenError("a revision cannot be its own predecessor")
        object.__setattr__(self, "ancestor_revision_ids", ancestors)
        if self.revision_id in ancestors:
            raise RevisionFrozenError(f"revision {self.revision_id} appears in its own ancestry")
        if len(ancestors) > MAX_ANCESTORS:
            raise SchemaValidationError(f"ancestor_revision_ids exceeds {MAX_ANCESTORS}")
        if self.label is not None:
            object.__setattr__(self, "label", require_text(self.label, "label", maximum=160))
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=4096))
        if self.recorded_at is not None:
            object.__setattr__(self, "recorded_at", require_text(self.recorded_at, "recorded_at", maximum=64))
        if self.created_by is not None:
            object.__setattr__(self, "created_by", SemanticRef.coerce(self.created_by, "created_by"))
        if self.admitted_by is not None:
            object.__setattr__(self, "admitted_by", SemanticRef.coerce(self.admitted_by, "admitted_by"))
        supersedes = tuple(sorted({require_identifier(item, "supersedes_statement_ids[]") for item in _sequence(self.supersedes_statement_ids, "supersedes_statement_ids")}))
        object.__setattr__(self, "supersedes_statement_ids", supersedes)
        object.__setattr__(self, "metadata", _bounded(self.metadata))
        if status is RevisionStatus.ADMITTED and self.admitted_by is None:
            raise SchemaValidationError(
                f"revision {self.revision_id} is ADMITTED without an admitted_by ref, so nothing "
                "records who stood behind it"
            )
        if self.content_digest is not None:
            if self.content_digest != self._compute_digest():
                raise SchemaValidationError(
                    "content_digest does not match this revision; the record was altered after it "
                    "was digested"
                )
        else:
            object.__setattr__(self, "content_digest", self._compute_digest())

    def _payload_without(self, *names: str) -> dict[str, Any]:
        payload = self.to_payload()
        for name in names:
            payload.pop(name, None)
        return payload

    def _compute_digest(self) -> str:
        from .versions import content_digest

        return content_digest(self._payload_without("content_digest"))

    def semantic_digest(self) -> str:
        """Digest of meaning only: statements and preserved sources, minus bookkeeping."""

        from .versions import content_digest

        return content_digest(
            {
                "brief_id": self.brief_id,
                "statements": [item.to_payload() for item in self.statements],
                "sources": [
                    {
                        "source_id": item.source_id,
                        "content_digest": item.content_digest,
                        "kind": item.kind,
                        "authority": item.authority,
                        "language": item.language,
                    }
                    for item in self.sources
                ],
            }
        )

    @property
    def ref(self) -> BriefRevisionRef:
        return BriefRevisionRef(
            brief_id=self.brief_id,
            revision_id=self.revision_id,
            revision_number=self.revision_number,
            semantic_digest=self.semantic_digest(),
        )

    @property
    def revision_ref(self) -> SemanticRef:
        return SemanticRef(
            kind=RefKind.REVISION.value,
            ref_id=self.revision_id,
            content_digest=self.content_digest,
        )

    @property
    def admitted(self) -> bool:
        return RevisionStatus.parse(self.status) is not RevisionStatus.DRAFT

    @property
    def statement_ids(self) -> tuple[str, ...]:
        return tuple(item.statement_id for item in self.statements)

    def statement(self, statement_id: str) -> IntentStatement | None:
        return next((item for item in self.statements if item.statement_id == statement_id), None)

    def source(self, source_id: str) -> RawInputRef | None:
        return next((item for item in self.sources if item.source_id == source_id), None)

    def require_editable(self, action: str) -> None:
        """Fail closed on any attempt to change an admitted revision in place (§5.3)."""

        if not RevisionStatus.parse(self.status).editable:
            raise RevisionFrozenError(
                f"cannot {action} revision {self.revision_id} ({self.status}): admitted revisions are "
                "immutable, so supersede it with a new revision instead"
            )

    def admit(self, *, admitted_by: Any, recorded_at: str | None = None) -> "BriefRevision":
        """Freeze this draft into an admitted revision, refusing anything looser than a human or policy grant.

        Admission is the moment a draft becomes project truth, so the grant is checked rather
        than trusted: an admitted_by carrying only ``MODEL_INFERRED`` authority would make the
        whole immutable-history rule a formality, since the model that wrote the statements
        would also be the authority that froze them (§5.6, §14).
        """

        self.require_editable("admit")
        granter = SemanticRef.coerce(admitted_by, "admitted_by")
        if not isinstance(granter, SemanticRef):
            raise SchemaValidationError("admitted_by must be a SemanticRef")
        if granter.content_digest is None:
            raise SchemaValidationError(
                "admitted_by must bind a digest, otherwise the admission cannot be re-checked later"
            )
        if RevisionStatus.parse(self.status) is not RevisionStatus.DRAFT:
            raise RevisionFrozenError("only a draft revision can be admitted")
        if not self.statements:
            raise SchemaValidationError(
                f"revision {self.revision_id} carries no statements; admit nothing rather than admit "
                "an empty revision that downstream readers will treat as a governed blank"
            )
        return BriefRevision(
            **{
                **self.to_payload(),
                "status": RevisionStatus.ADMITTED.value,
                "admitted_by": granter.to_payload(),
                "recorded_at": recorded_at if recorded_at is not None else self.recorded_at,
                "content_digest": None,
            }
        )

    def supersede(
        self,
        *,
        revision_id: str,
        kind: Any,
        statements: Iterable[Any] | None = None,
        sources: Iterable[Any] | None = None,
        created_by: Any = None,
        supersedes_statement_ids: Iterable[str] = (),
        label: str | None = None,
        notes: str | None = None,
    ) -> "BriefRevision":
        """Derive the next revision from this one, recording where it came from.

        The predecessor's identity is carried forward rather than re-asserted, so a superseded
        revision stays exactly as it was admitted — including the statements it is now known
        to have got wrong, which is the evidence a later correction is measured against.
        """

        if not isinstance(kind, RevisionKind) and not isinstance(kind, str):
            raise SchemaValidationError("kind must be a RevisionKind")
        label_kind = RevisionKind.parse(kind, "kind")
        if self.revision_id == revision_id:
            raise RevisionFrozenError(
                f"a superseding revision needs a new revision_id; reusing {revision_id} would rewrite "
                "the history that receipts and fingerprints already cite"
            )
        return BriefRevision(
            revision_id=revision_id,
            brief_id=self.brief_id,
            revision_number=self.revision_number + 1,
            kind=label_kind.value,
            status=RevisionStatus.DRAFT.value,
            statements=tuple(statements) if statements is not None else self.statements,
            sources=tuple(sources) if sources is not None else self.sources,
            predecessor_revision_id=self.revision_id,
            ancestor_revision_ids=(*self.ancestor_revision_ids, self.revision_id),
            created_by=created_by if created_by is not None else self.created_by,
            supersedes_statement_ids=tuple(supersedes_statement_ids),
            label=label if label is not None else self.label,
            notes=notes,
            metadata={},
        )

    def semantically_equal(self, other: "BriefRevision") -> bool:
        """Whether two revisions mean the same thing, ignoring wording and bookkeeping.

        This is the gate §5.45 allows reuse-preserving edits through: it compares the semantic
        digest, so a translation of the notes or a renamed label cannot invalidate a build,
        and a changed authority can.
        """

        if not isinstance(other, BriefRevision):
            raise SchemaValidationError("semantically_equal expects a BriefRevision")
        return self.brief_id == other.brief_id and self.semantic_digest() == other.semantic_digest()

    def wording_only_delta(self, other: "BriefRevision") -> tuple[str, ...]:
        """Name the fields that differ while meaning stayed the same."""

        if not self.semantically_equal(other):
            return ()
        mine, theirs = self.to_payload(), other.to_payload()
        return tuple(
            sorted(
                name
                for name in _WORDING_FIELDS
                if mine.get(name) != theirs.get(name)
            )
        )


#: Fields that carry wording or bookkeeping rather than meaning. A change here is a rewording,
#: not a revision of what the client asked for, so it must not move the semantic digest.
_WORDING_FIELDS = ("label", "notes", "recorded_at", "metadata", "supersedes_statement_ids")

BriefRevision.NESTED = {
    "statements": of(IntentStatement),
    "sources": of(RawInputRef),
    "created_by": of(SemanticRef),
    "admitted_by": of(SemanticRef),
}


def _sequence(value: Any, field_name: str) -> Iterable[Any]:
    if not isinstance(value, (list, tuple)):
        raise SchemaValidationError(f"{field_name} must be a list")
    return value


def _bounded(value: Any) -> dict[str, str]:
    from .sources import bounded_metadata

    return bounded_metadata(value, "metadata")


def intent_model_for(
    revision: BriefRevision,
    *,
    model_id: str,
    open_questions: Iterable[str] = (),
    requested_quality_class: str | None = None,
) -> IntentModel:
    """Build the intent model a revision carries, without inventing anything it lacks.

    The model is derived, not stored, and refuses a quality-class request the revision did
    not explicitly make — so a caller cannot compile a higher rung into existence by passing
    an argument to the derivation function (§5.20, §5.21).
    """

    if not isinstance(revision, BriefRevision):
        raise SchemaValidationError("intent_model_for expects a BriefRevision")
    return IntentModel(
        model_id=model_id,
        brief_id=revision.brief_id,
        revision_id=revision.revision_id,
        revision_number=revision.revision_number,
        statements=revision.statements,
        open_questions=tuple(open_questions),
        requested_quality_class=requested_quality_class,
    )


def require_revision_identity(brief: CreativeBriefIdentity, revision: BriefRevision) -> None:
    """Refuse a revision that belongs to a different brief than the identity claiming it.

    Two briefs reusing a revision id is not exotic — ids are chosen by whoever creates them —
    and the damage is silent: every fingerprint and receipt would read as internally
    consistent while describing someone else's work.
    """

    if not isinstance(brief, CreativeBriefIdentity):
        raise SchemaValidationError("brief must be a CreativeBriefIdentity")
    if not isinstance(revision, BriefRevision):
        raise SchemaValidationError("revision must be a BriefRevision")
    if not brief.known_as(revision.brief_id):
        raise SchemaValidationError(
            f"revision {revision.revision_id} belongs to {revision.brief_id}, not {brief.brief_id}"
        )
    if revision.admitted and revision.admitted_by is None:
        raise SchemaValidationError("admitted revision without admitted_by")


def require_admission_authority(authority: Any, *, minimum: AuthorityLevel = AuthorityLevel.HUMAN_OWNER) -> AuthorityLevel:
    return require_authority(authority, "admission authority", minimum=minimum)
