"""M03 identity: stable refs, revision refs, and the authority a source may claim.

Two things the frozen contract keeps apart, and which this module makes impossible to
conflate. A *brief* is the durable thing a project talks about; a *revision* is one
immutable snapshot of it (§5.2). And *authority* — who is allowed to make a statement true —
is independent of *confidence* — how sure the writer was (§5.5). Conflating them is exactly
how retrieved text becomes a project rule, so authority is a typed, ranked property of a ref
rather than anything a payload can assert about itself.

Refs are opaque by design. M03 binds to M02 project/branch/node ids and to M01 profile and
contract references without importing their state models, so a ref is a kind, an identifier,
an optional version, and an optional content digest — nothing more, because anything more
would be M03 pretending to own somebody else's record.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Mapping

from .base import Labeled, Record, of
from .errors import AuthorityError, RefError, SchemaValidationError
from .limits import MAX_ALIASES, MAX_ANCESTORS
from .versions import require_digest, require_identifier, require_text

__all__ = [
    "AuthorityLevel",
    "BriefRevisionRef",
    "CreativeBriefIdentity",
    "MAX_ALIASES",
    "MAX_ANCESTORS",
    "RefKind",
    "SemanticRef",
    "SourceKind",
    "UNTRUSTED_SOURCES",
    "VERSIONED_REF_KINDS",
    "ceiling_for",
    "check_ancestry",
    "is_untrusted",
    "mint_id",
    "require_authority",
    "require_bound_ref",
]


def mint_id(prefix: str = "m03") -> str:
    """Mint an unguessable id when a caller genuinely has none.

    Deliberately non-deterministic, and therefore deliberately *not* used anywhere inside
    the kernel: a compilation that minted its own identifiers could not be replayed for an
    audit. Every record in M03 takes its ids as arguments, so tests and executors choose
    them; this helper exists for the outer caller that is creating a brief for the first
    time and has no prior name for it.
    """

    return f"{prefix}-{uuid.uuid4().hex}"


class RefKind(Labeled):
    """The namespace a ref points into.

    ``M02_*`` kinds are bindings to state M03 may reference and never mutate; ``M01_*``
    kinds are quality authorities M03 may consult and never grant. The brief-side kinds are
    the only ones M03 owns outright.
    """

    M02_PROJECT = "M02_PROJECT"
    M02_PRODUCTION = "M02_PRODUCTION"
    M02_BRANCH = "M02_BRANCH"
    M02_VARIANT = "M02_VARIANT"
    M02_NODE = "M02_NODE"
    M02_SNAPSHOT = "M02_SNAPSHOT"
    M02_BUILD = "M02_BUILD"
    M02_RELEASE = "M02_RELEASE"
    M01_DIMENSION = "M01_DIMENSION"
    M01_DOMAIN_PROFILE = "M01_DOMAIN_PROFILE"
    M01_DIMENSION_REGISTRY = "M01_DIMENSION_REGISTRY"
    M01_CONTRACT = "M01_CONTRACT"
    M01_EVALUATOR = "M01_EVALUATOR"
    BRIEF = "BRIEF"
    REVISION = "REVISION"
    SOURCE = "SOURCE"
    STATEMENT = "STATEMENT"
    AMBIGUITY = "AMBIGUITY"
    FREEDOM_ZONE = "FREEDOM_ZONE"
    OPEN_QUESTION = "OPEN_QUESTION"
    CONSTRAINT = "CONSTRAINT"
    BUNDLE = "BUNDLE"
    PREDICATE = "PREDICATE"
    ANCHOR = "ANCHOR"
    PROVENANCE = "PROVENANCE"
    FRESHNESS = "FRESHNESS"
    PASSPORT = "PASSPORT"
    OBLIGATION = "OBLIGATION"
    CONTRACT_SET = "CONTRACT_SET"
    EXECUTION_BUNDLE = "EXECUTION_BUNDLE"
    CAPABILITY = "CAPABILITY"
    RECEIPT = "RECEIPT"
    DEBT = "DEBT"
    POLICY = "POLICY"
    DESTINATION = "DESTINATION"
    CANON = "CANON"
    SEMANTIC_TYPE = "SEMANTIC_TYPE"
    CONFLICT = "CONFLICT"
    RESOLUTION = "RESOLUTION"
    LEASE = "LEASE"
    MERGE_ANALYSIS = "MERGE_ANALYSIS"
    MIGRATION = "MIGRATION"
    READINESS = "READINESS"
    EXTERNAL = "EXTERNAL"


class SourceKind(Labeled):
    """How a piece of direction reached the brief.

    The distinction is load-bearing for the admission shield: a value that arrived as
    ``RETRIEVED_CONTEXT`` or ``PROVIDER_RESULT`` cannot be promoted to a rule by anything it
    says about itself (§5.6), and ``HIVE_MEMORY`` in particular is derived context and never
    canonical intent state (§5.40).
    """

    HUMAN_MESSAGE = "HUMAN_MESSAGE"
    HUMAN_DOCUMENT = "HUMAN_DOCUMENT"
    GOVERNED_POLICY = "GOVERNED_POLICY"
    PROJECT_RECORD = "PROJECT_RECORD"
    CANON_RECORD = "CANON_RECORD"
    HIVE_MEMORY = "HIVE_MEMORY"
    RETRIEVED_CONTEXT = "RETRIEVED_CONTEXT"
    MODEL_OUTPUT = "MODEL_OUTPUT"
    PROVIDER_RESULT = "PROVIDER_RESULT"
    DERIVED_FROM_ADMITTED = "DERIVED_FROM_ADMITTED"


class AuthorityLevel(Labeled):
    """Rank of *who may make this true*, independent of how confident the writer was.

    ``UNTRUSTED`` cannot become ``AGENT`` or above without an authorized human revision:
    the ladder exists so that promotion is an explicit, receipted act rather than a field a
    normaliser edits (§5.6, §14).
    """

    UNTRUSTED = "UNTRUSTED"
    PROVIDER_OBSERVED = "PROVIDER_OBSERVED"
    RETRIEVED = "RETRIEVED"
    MODEL_INFERRED = "MODEL_INFERRED"
    PROJECT_RECORD = "PROJECT_RECORD"
    TEAM_ASSERTED = "TEAM_ASSERTED"
    GOVERNED_POLICY = "GOVERNED_POLICY"
    HUMAN_OWNER = "HUMAN_OWNER"

    @property
    def rank(self) -> int:
        return _AUTHORITY_RANKS[self]

    def at_least(self, other: "AuthorityLevel") -> bool:
        return self.rank >= other.rank

    @property
    def self_asserting_is_enough(self) -> bool:
        """Only human and governed sources may make a statement true by asserting it.

        Everything below this line reaches the brief through someone else's text, and text
        is evidence about a claim, not a grant of authority over the project.
        """

        return self in _SELF_AUTHORITY


_AUTHORITY_RANKS: Mapping[AuthorityLevel, int] = {
    AuthorityLevel.UNTRUSTED: 0,
    AuthorityLevel.PROVIDER_OBSERVED: 1,
    AuthorityLevel.RETRIEVED: 2,
    AuthorityLevel.MODEL_INFERRED: 3,
    AuthorityLevel.PROJECT_RECORD: 4,
    AuthorityLevel.TEAM_ASSERTED: 5,
    AuthorityLevel.GOVERNED_POLICY: 6,
    AuthorityLevel.HUMAN_OWNER: 7,
}

_SELF_AUTHORITY = frozenset({AuthorityLevel.GOVERNED_POLICY, AuthorityLevel.HUMAN_OWNER})

#: Sources whose text may never carry more authority than an admitted record grants it.
UNTRUSTED_SOURCES = frozenset(
    {
        SourceKind.MODEL_OUTPUT,
        SourceKind.PROVIDER_RESULT,
        SourceKind.RETRIEVED_CONTEXT,
        SourceKind.HIVE_MEMORY,
    }
)

_TRUSTED_SOURCES = frozenset(
    {
        SourceKind.HUMAN_MESSAGE,
        SourceKind.HUMAN_DOCUMENT,
        SourceKind.GOVERNED_POLICY,
        SourceKind.PROJECT_RECORD,
        SourceKind.CANON_RECORD,
        SourceKind.DERIVED_FROM_ADMITTED,
    }
)

#: The authority a source kind can reach on its own, before any human admission.
_SOURCE_CEILINGS: Mapping[SourceKind, AuthorityLevel] = {
    SourceKind.HUMAN_MESSAGE: AuthorityLevel.HUMAN_OWNER,
    SourceKind.HUMAN_DOCUMENT: AuthorityLevel.HUMAN_OWNER,
    SourceKind.GOVERNED_POLICY: AuthorityLevel.GOVERNED_POLICY,
    SourceKind.PROJECT_RECORD: AuthorityLevel.PROJECT_RECORD,
    SourceKind.CANON_RECORD: AuthorityLevel.PROJECT_RECORD,
    SourceKind.DERIVED_FROM_ADMITTED: AuthorityLevel.PROJECT_RECORD,
    SourceKind.HIVE_MEMORY: AuthorityLevel.RETRIEVED,
    SourceKind.RETRIEVED_CONTEXT: AuthorityLevel.RETRIEVED,
    SourceKind.MODEL_OUTPUT: AuthorityLevel.MODEL_INFERRED,
    SourceKind.PROVIDER_RESULT: AuthorityLevel.PROVIDER_OBSERVED,
}


#: Refs into namespaces whose members change under a stable id, so the id alone is not a pin.
VERSIONED_REF_KINDS = frozenset(
    {
        RefKind.M01_DOMAIN_PROFILE,
        RefKind.M01_DIMENSION_REGISTRY,
        RefKind.M01_CONTRACT,
        RefKind.M01_EVALUATOR,
        RefKind.M02_SNAPSHOT,
        RefKind.M02_BUILD,
        RefKind.M02_RELEASE,
        RefKind.PREDICATE,
        RefKind.SEMANTIC_TYPE,
        RefKind.POLICY,
        RefKind.CAPABILITY,
    }
)


@dataclass(frozen=True)
class SemanticRef(Record):
    """An opaque, version-pinnable pointer into a namespace M03 does not own.

    The optional ``content_digest`` is what turns a reference into evidence: a ref without a
    digest says "something was there", a bound ref says "this exact content was there", and
    an admitted compilation binds the refs it depended on so a later reader can tell whether
    the thing it trusted is still the same thing.
    """

    kind: str
    ref_id: str
    version: str | None = None
    content_digest: str | None = None

    def __post_init__(self) -> None:
        kind = RefKind.parse(self.kind, "SemanticRef.kind")
        object.__setattr__(self, "kind", kind.value)
        object.__setattr__(self, "ref_id", require_identifier(self.ref_id, "SemanticRef.ref_id"))
        if self.version is not None:
            object.__setattr__(self, "version", require_text(self.version, "SemanticRef.version", maximum=64))
        if self.content_digest is not None:
            object.__setattr__(self, "content_digest", require_digest(self.content_digest, "SemanticRef.content_digest"))
        if kind in VERSIONED_REF_KINDS and self.version is None:
            raise RefError(
                f"{self.ref_id} points into {kind.value}, a namespace whose members change under a "
                "stable id; pin the version or an earlier decision cannot be re-resolved"
            )

    @property
    def text(self) -> str:
        """The canonical one-line form, used as a stable sort key in payloads and slices."""

        parts = [self.kind, self.ref_id]
        if self.version is not None:
            parts.append(self.version)
        if self.content_digest is not None:
            parts.append(self.content_digest[:16])
        return "@".join(parts)

    @property
    def unversioned(self) -> bool:
        return self.version is None

    @property
    def pinned(self) -> bool:
        """Whether the ref identifies exact content or merely a name.

        Digest-only pins immutable input — a captured source cannot change under its own id —
        and version-only pins a namespaced artifact. Neither shape pins the *combination*,
        which is why the places that record trust ask for a digest specifically.
        """

        return self.content_digest is not None or self.version is not None

    def bind(self, content_digest: str, version: str) -> "SemanticRef":
        """Return the same ref pinned to exact content, refusing a silent rebind."""

        if self.content_digest is not None and self.content_digest != content_digest:
            raise RefError(
                f"{self.text} is already bound to {self.content_digest[:16]}; rebinding an admitted "
                "ref would rewrite what earlier decisions were based on"
            )
        return SemanticRef(
            kind=self.kind,
            ref_id=self.ref_id,
            version=require_text(version, "version", maximum=64),
            content_digest=require_digest(content_digest, "content_digest"),
        )

    def with_digest(self, content_digest: str) -> "SemanticRef":
        return SemanticRef(
            kind=self.kind,
            ref_id=self.ref_id,
            version=self.version,
            content_digest=require_digest(content_digest, "content_digest"),
        )

    def __str__(self) -> str:
        return self.text


@dataclass(frozen=True)
class CreativeBriefIdentity(Record):
    """The durable identity of a brief, deliberately holding no content.

    Renaming, rewording and restating a brief must not replace what downstream work refers
    to (§5.1, §18). So the stable identity carries an id, an optional project binding, and a
    display label that is *metadata*, never a key: labels are the field most likely to
    change and the one a merge must not care about.
    """

    brief_id: str
    label: str
    project_ref: SemanticRef | None = None
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "brief_id", require_identifier(self.brief_id, "brief_id"))
        object.__setattr__(self, "label", require_text(self.label, "label", maximum=160))
        if self.project_ref is not None:
            object.__setattr__(self, "project_ref", SemanticRef.coerce(self.project_ref, "project_ref"))
        if self.project_ref is not None and self.project_ref.kind != RefKind.M02_PROJECT.value:
            raise RefError(
                f"project_ref must reference {RefKind.M02_PROJECT.value}, not {self.project_ref.kind}; "
                "a brief bound to the wrong kind of M02 object would claim the wrong scope"
            )
        if not isinstance(self.aliases, (list, tuple)):
            raise SchemaValidationError("aliases must be a list of identifiers")
        aliases = tuple(require_identifier(item, "aliases[]") for item in self.aliases)
        if len(aliases) > MAX_ALIASES:
            raise SchemaValidationError(f"aliases exceeds {MAX_ALIASES} entries")
        duplicate = sorted({item for item in aliases if aliases.count(item) > 1})
        if duplicate:
            raise SchemaValidationError(f"aliases contains duplicates: {duplicate}")
        if self.brief_id in aliases:
            raise SchemaValidationError("brief_id must not repeat itself in aliases")
        object.__setattr__(self, "aliases", tuple(sorted(aliases)))

    def known_as(self, identifier: str) -> bool:
        return identifier == self.brief_id or identifier in self.aliases

    @property
    def references(self) -> tuple[SemanticRef, ...]:
        return (self.project_ref,) if self.project_ref is not None else ()


@dataclass(frozen=True)
class BriefRevisionRef(Record):
    """A pointer to one immutable revision, carrying the number that makes lineage readable.

    ``revision_number`` is monotonically increasing per brief and is the field a human
    scanner uses to follow history; ``revision_id`` is the field that actually binds, so the
    two are checked together and a gap in the numbers is refused rather than explained away.
    """

    brief_id: str
    revision_id: str
    revision_number: int
    semantic_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "brief_id", require_identifier(self.brief_id, "brief_id"))
        object.__setattr__(self, "revision_id", require_identifier(self.revision_id, "revision_id"))
        if isinstance(self.revision_number, bool) or not isinstance(self.revision_number, int):
            raise SchemaValidationError("revision_number must be a positive integer")
        if self.revision_number < 1:
            raise SchemaValidationError(f"revision_number starts at 1, got {self.revision_number}")
        if self.semantic_digest is not None:
            object.__setattr__(self, "semantic_digest", require_digest(self.semantic_digest, "semantic_digest"))

    @property
    def text(self) -> str:
        return f"{self.brief_id}#{self.revision_number}:{self.revision_id}"

    def bind_semantics(self, digest: str) -> "BriefRevisionRef":
        return BriefRevisionRef(
            brief_id=self.brief_id,
            revision_id=self.revision_id,
            revision_number=self.revision_number,
            semantic_digest=require_digest(digest, "digest"),
        )

    @property
    def revision_ref(self) -> SemanticRef:
        return SemanticRef(
            kind=RefKind.REVISION.value,
            ref_id=self.revision_id,
            content_digest=self.semantic_digest,
        )

    def precedes(self, other: "BriefRevisionRef") -> bool:
        """True when ``other`` descends from this revision of the same brief."""

        if self.brief_id != other.brief_id:
            raise RefError(
                f"{self.text} and {other.text} belong to different briefs, so neither can precede the other"
            )
        return self.revision_number < other.revision_number


SemanticRef.NESTED = {}
CreativeBriefIdentity.NESTED = {"project_ref": of(SemanticRef)}


def require_bound_ref(ref: Any, field: str, *, kind: RefKind | None = None) -> SemanticRef:
    """Accept only an existing, digest-bound ref of the expected kind.

    Compilation evidence is full of "this depended on that", and an unbound ref makes the
    claim unfalsifiable — so the places that record dependencies demand the pinned form and
    raise ``RefError`` naming the field instead of quietly accepting a looser one.
    """

    value = SemanticRef.coerce(ref, field)
    if not isinstance(value, SemanticRef):
        raise RefError(f"{field} must be a SemanticRef")
    if value.content_digest is None:
        raise RefError(
            f"{field} ({value.text}) carries no content digest; a dependency that cannot be "
            "re-checked cannot support an admitted compilation"
        )
    if kind is not None and value.kind != kind.value:
        raise RefError(f"{field} must reference {kind.value}, got {value.kind}")
    return value


def require_authority(value: Any, field: str, *, minimum: AuthorityLevel | None = None) -> AuthorityLevel:
    level = AuthorityLevel.parse(value, field)
    if minimum is not None and not level.at_least(minimum):
        raise AuthorityError(
            f"{field} requires at least {minimum.value} authority, got {level.value}; confidence, "
            "recency and specificity do not substitute for authority"
        )
    return level


def ceiling_for(source_kind: Any) -> AuthorityLevel:
    """The highest authority this kind of source can hold without an admission act."""

    kind = SourceKind.parse(source_kind, "source_kind")
    return _SOURCE_CEILINGS[kind]


def is_untrusted(source_kind: Any) -> bool:
    return SourceKind.parse(source_kind, "source_kind") in UNTRUSTED_SOURCES


def check_ancestry(chain: Any, field: str = "ancestor_revisions") -> tuple[str, ...]:
    """Validate a revision lineage: identifiers, bounded length, no repeats.

    A cycle in brief history would let a revision be its own ancestor and make merge
    analysis loop; the bound exists so a hostile payload cannot make it loop *expensively*.
    """

    if not isinstance(chain, (list, tuple)):
        raise SchemaValidationError(f"{field} must be a list of revision identifiers")
    identifiers = tuple(require_identifier(item, f"{field}[]") for item in chain)
    if len(identifiers) > MAX_ANCESTORS:
        raise SchemaValidationError(
            f"{field} exceeds {MAX_ANCESTORS} entries; revision history that long is a bug in "
            "whoever is appending to it"
        )
    repeats = sorted({item for item in identifiers if identifiers.count(item) > 1})
    if repeats:
        raise SchemaValidationError(f"{field} repeats revisions: {repeats}")
    return identifiers


