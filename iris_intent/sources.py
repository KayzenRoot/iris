"""Preserved raw input, source anchors and provenance capsules.

M03 normalizes human direction into typed semantics, and the frozen contract insists the
original survives that step untouched (§5.1): a reviewer comparing a normalized statement
against a disputed brief must be able to read what was actually said. So raw text lives in
``RawInputRef`` records that normalization never rewrites, and every derived statement
carries anchors back into them.

Authority is decided *here*, at the point a source enters the kernel, and nowhere later. A
retrieved page or a model output cannot raise itself by asserting ``authority:
HUMAN_OWNER`` — the ceiling is a function of how the text arrived, so a forged claim is a
construction error rather than a plausible-looking payload (§5.6, §14). A captured timestamp
is likewise recorded and never trusted: it is bookkeeping, not proof that something is still
current (§5.44).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .base import Labeled, Record, of
from .errors import AuthorityError, SchemaValidationError
from .identity import (
    AuthorityLevel,
    RefKind,
    SemanticRef,
    SourceKind,
    UNTRUSTED_SOURCES,
    ceiling_for,
)
from .limits import (
    MAX_METADATA_KEYS,
    MAX_METADATA_VALUE_CHARS,
    MAX_PROVENANCE_REFS,
    MAX_RATIONALE_CHARS,
    MAX_TEXT_CHARS,
)
from .versions import require_digest, require_identifier, require_text, require_unit_interval

__all__ = [
    "AnchorSpan",
    "DerivationKind",
    "ProvenanceCapsule",
    "RawInputRef",
    "SourceAnchor",
    "bounded_metadata",
    "require_source_refs",
]

_LANGUAGE = require_identifier  # BCP-47 tags such as "en", "pt-br", "ja" fit the identifier grammar.


def bounded_metadata(value: Any, field_name: str) -> dict[str, str]:
    """Accept a small mapping of string facts, refusing to become a payload smuggle.

    Extension metadata is where an untrusted source tries to hide a rule. Bounding key
    count and value length keeps it descriptive, and the strict string type keeps a nested
    structure from arriving as metadata and being read later as semantics.
    """

    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise SchemaValidationError(f"{field_name} must be a mapping")
    if len(value) > MAX_METADATA_KEYS:
        raise SchemaValidationError(
            f"{field_name} exceeds {MAX_METADATA_KEYS} keys; a source record that needs more is "
            "carrying semantics it should declare as statements"
        )
    bounded: dict[str, str] = {}
    for key, item in value.items():
        name = require_identifier(key, f"{field_name} key")
        if isinstance(item, (Mapping, list, tuple)):
            raise SchemaValidationError(
                f"{field_name}[{name}] must be a string; nested structures in metadata are how an "
                "untrusted payload tries to look like a rule"
            )
        bounded[name] = require_text(item, f"{field_name}[{name}]", maximum=MAX_METADATA_VALUE_CHARS)
    return dict(sorted(bounded.items()))


@dataclass(frozen=True)
class RawInputRef(Record):
    """One preserved piece of input: what arrived, how it arrived, and what it may be worth.

    ``transcription`` is inert data. Nothing in the kernel parses it into semantics; a
    statement enters an intent model only when a caller declares it, which is what makes the
    admission shield's central claim — imperative text inside a retrieved document cannot
    self-admit — a structural property rather than a filter that can be tricked.
    """

    source_id: str
    kind: str
    authority: str
    content_digest: str
    locator: str | None = None
    language: str | None = None
    captured_at: str | None = None
    transcription: str | None = None
    origin_ref: SemanticRef | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", require_identifier(self.source_id, "source_id"))
        source_kind = SourceKind.parse(self.kind, "kind")
        authority = AuthorityLevel.parse(self.authority, "authority")
        ceiling = ceiling_for(source_kind)
        if authority.rank > ceiling.rank:
            raise AuthorityError(
                f"{source_kind.value} input cannot carry {authority.value} authority; its ceiling is "
                f"{ceiling.value}. Raising it takes an admitted revision by someone with "
                "HUMAN_OWNER or GOVERNED_POLICY standing, not a field on the record that arrived"
            )
        object.__setattr__(self, "kind", source_kind.value)
        object.__setattr__(self, "authority", authority.value)
        object.__setattr__(self, "content_digest", require_digest(self.content_digest, "content_digest"))
        if self.locator is not None:
            object.__setattr__(self, "locator", require_text(self.locator, "locator", maximum=1024))
        if self.language is not None:
            object.__setattr__(self, "language", _LANGUAGE(self.language, "language"))
        if self.captured_at is not None:
            object.__setattr__(self, "captured_at", require_text(self.captured_at, "captured_at", maximum=64))
        if self.transcription is not None:
            object.__setattr__(self, "transcription", require_text(self.transcription, "transcription", maximum=MAX_TEXT_CHARS))
        if self.origin_ref is not None:
            object.__setattr__(self, "origin_ref", SemanticRef.coerce(self.origin_ref, "origin_ref"))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))

    @property
    def untrusted(self) -> bool:
        return SourceKind.parse(self.kind) in UNTRUSTED_SOURCES

    @property
    def authority_level(self) -> AuthorityLevel:
        return AuthorityLevel.parse(self.authority)

    @property
    def source_ref(self) -> SemanticRef:
        return SemanticRef(
            kind=RefKind.SOURCE.value,
            ref_id=self.source_id,
            content_digest=self.content_digest,
        )

    def holds(self, text: str) -> bool:
        """Whether the preserved transcription contains ``text`` — an anchor check, not a rule."""

        return self.transcription is not None and text in self.transcription


RawInputRef.NESTED = {"origin_ref": of(SemanticRef)}


@dataclass(frozen=True)
class AnchorSpan(Record):
    """A location inside a preserved source, expressed in units the source itself defines.

    Character offsets work for text, and a media source places its own selector in
    ``selector`` instead; the point of keeping both optional is that the kernel never has to
    know whether it is anchoring a paragraph or a take (§6).
    """

    start: int | None = None
    end: int | None = None
    selector: str | None = None

    def __post_init__(self) -> None:
        for name in ("start", "end"):
            value = getattr(self, name)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, int):
                raise SchemaValidationError(f"{name} must be an integer offset or None")
            if value < 0:
                raise SchemaValidationError(f"{name} must not be negative, got {value}")
        if self.start is not None and self.end is not None and self.end < self.start:
            raise SchemaValidationError(f"anchor span ends before it starts: {self.start}..{self.end}")
        if self.selector is not None:
            object.__setattr__(self, "selector", require_text(self.selector, "selector", maximum=512))
        if self.start is None and self.end is None and self.selector is None:
            raise SchemaValidationError(
                "an anchor span must say where it is: give offsets, a selector, or omit the span"
            )


@dataclass(frozen=True)
class SourceAnchor(Record):
    """A quote-shaped claim that a normalized statement came from this exact source.

    ``quote_digest`` rather than ``quote`` because the anchor must survive a source being
    redacted for transport while still proving which passage it pointed at; the verbatim text
    stays in :attr:`RawInputRef.transcription`, which is the only place M03 keeps it.
    """

    anchor_id: str
    source_id: str
    quote_digest: str
    language: str | None = None
    span: AnchorSpan | None = None
    translation: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "anchor_id", require_identifier(self.anchor_id, "anchor_id"))
        object.__setattr__(self, "source_id", require_identifier(self.source_id, "source_id"))
        object.__setattr__(self, "quote_digest", require_digest(self.quote_digest, "quote_digest"))
        if self.language is not None:
            object.__setattr__(self, "language", _LANGUAGE(self.language, "language"))
        if self.span is not None:
            object.__setattr__(self, "span", AnchorSpan.coerce(self.span, "span"))
        if self.translation is not None:
            object.__setattr__(self, "translation", require_text(self.translation, "translation", maximum=MAX_TEXT_CHARS))

    def anchors(self, source: RawInputRef) -> bool:
        """True only when this anchor points at ``source``'s own preserved text."""

        return source.source_id == self.source_id and source.content_digest is not None


SourceAnchor.NESTED = {"span": of(AnchorSpan)}


class DerivationKind(Labeled):
    """How a derived statement relates to the material it came from.

    ``INFERRED`` and ``DEFAULTED`` exist as labels the kernel refuses to let become
    ``QUOTED``, because the most damaging normalization bug is not a wrong value, it is a
    guess that later reads as something the client asked for (§5.4, §7).
    """

    QUOTED = "QUOTED"
    PARAPHRASED = "PARAPHRASED"
    TRANSLATED = "TRANSLATED"
    STRUCTURED = "STRUCTURED"
    SUMMARISED = "SUMMARISED"
    MERGED = "MERGED"
    INFERRED = "INFERRED"
    DEFAULTED = "DEFAULTED"
    POLICY_DERIVED = "POLICY_DERIVED"


@dataclass(frozen=True)
class ProvenanceCapsule(Record):
    """The explanation path a compiled obligation must be able to reach.

    A capsule is required to point at *something* — a source, a policy ref, or an ancestor
    statement — because an obligation with an empty provenance record is precisely the thing
    §16 asks the kernel to make impossible, and the cheapest way to guarantee that is to
    refuse to construct the empty one.
    """

    capsule_id: str
    derivation: str
    source_refs: tuple[SemanticRef, ...] = ()
    policy_refs: tuple[SemanticRef, ...] = ()
    ancestor_refs: tuple[SemanticRef, ...] = ()
    anchors: tuple[SourceAnchor, ...] = ()
    rationale: str | None = None
    confidence: float | None = None
    admitted_by: SemanticRef | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "capsule_id", require_identifier(self.capsule_id, "capsule_id"))
        object.__setattr__(self, "derivation", DerivationKind.parse(self.derivation, "derivation").value)
        object.__setattr__(self, "source_refs", require_source_refs(self.source_refs, "source_refs"))
        object.__setattr__(self, "policy_refs", require_source_refs(self.policy_refs, "policy_refs"))
        object.__setattr__(self, "ancestor_refs", require_source_refs(self.ancestor_refs, "ancestor_refs"))
        if not isinstance(self.anchors, (list, tuple)):
            raise SchemaValidationError("anchors must be a list of SourceAnchor")
        anchors = tuple(SourceAnchor.coerce(item, "anchors[]") for item in self.anchors)
        duplicates = sorted({item.anchor_id for item in anchors if _count(anchors, item.anchor_id) > 1})
        if duplicates:
            raise SchemaValidationError(f"anchors contains duplicate anchor_ids: {duplicates}")
        object.__setattr__(self, "anchors", anchors)
        if self.rationale is not None:
            object.__setattr__(self, "rationale", require_text(self.rationale, "rationale", maximum=MAX_RATIONALE_CHARS))
        if self.confidence is not None:
            object.__setattr__(self, "confidence", require_unit_interval(self.confidence, "confidence"))
        if self.admitted_by is not None:
            object.__setattr__(self, "admitted_by", SemanticRef.coerce(self.admitted_by, "admitted_by"))
        if not (self.source_refs or self.policy_refs or self.ancestor_refs):
            raise SchemaValidationError(
                f"{self.capsule_id} has no source, policy or ancestor refs; a derived fact with no "
                "provenance cannot be explained, so it cannot be admitted"
            )
        if self.derivation in {DerivationKind.QUOTED.value, DerivationKind.TRANSLATED.value} and not self.anchors:
            raise SchemaValidationError(
                f"a {self.derivation} capsule must carry at least one anchor, otherwise 'quoted' is "
                "just a claim about text nobody preserved"
            )

    @property
    def authoritative_basis(self) -> bool:
        """Whether this capsule reaches something a human or policy admitted.

        Used by the admission shield to tell "derived from an admitted statement" apart from
        "derived from a model output", which look identical in the graph until someone
        checks what the leaves are.
        """

        kinds = {ref.kind for ref in self.source_refs} | {ref.kind for ref in self.policy_refs}
        return bool(kinds & _AUTHORITATIVE_BASIS_KINDS)

    def reaches(self, source_id: str) -> bool:
        return any(ref.ref_id == source_id for ref in self.source_refs) or any(
            anchor.source_id == source_id for anchor in self.anchors
        )


_AUTHORITATIVE_BASIS_KINDS = frozenset(
    {
        RefKind.SOURCE.value,
        RefKind.POLICY.value,
        RefKind.M01_DOMAIN_PROFILE.value,
        RefKind.M01_DIMENSION_REGISTRY.value,
        RefKind.STATEMENT.value,
        RefKind.CONSTRAINT.value,
    }
)


ProvenanceCapsule.NESTED = {
    "anchors": of(SourceAnchor),
    "source_refs": of(SemanticRef),
    "policy_refs": of(SemanticRef),
    "ancestor_refs": of(SemanticRef),
    "admitted_by": of(SemanticRef),
}


def _count(items: Any, anchor_id: str) -> int:
    return sum(1 for item in items if item.anchor_id == anchor_id)


def require_source_refs(value: Any, field_name: str) -> tuple[SemanticRef, ...]:
    """Normalise a ref collection: typed, bounded, deduplicated, deterministically ordered.

    Ordering is part of the fingerprint, so a set that happened to iterate differently on two
    runs would make two identical compilations disagree — which reads as instability in the
    kernel and is really an unsorted field three modules away.
    """

    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise SchemaValidationError(f"{field_name} must be a list of SemanticRef")
    if len(value) > MAX_PROVENANCE_REFS:
        raise SchemaValidationError(f"{field_name} exceeds {MAX_PROVENANCE_REFS} entries")
    refs = tuple(SemanticRef.coerce(item, f"{field_name}[]") for item in value)
    seen = {ref.text for ref in refs}
    if len(seen) != len(refs):
        raise SchemaValidationError(f"{field_name} contains duplicate references")
    return tuple(sorted(refs, key=lambda ref: ref.text))
