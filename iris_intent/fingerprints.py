"""F-M03-04 Semantic fingerprints, equivalence profiles and deltas.

A fingerprint is the only way this kernel can say "nothing relevant changed", so the burden of
proof sits on the definition of *relevant*. Naive hashing over a whole revision makes a typo fix
look like a re-requirement and invalidates every downstream obligation, which is expensive and —
worse — trains people to ignore invalidation. Hashing too loosely is worse still: a fingerprint
blind to constraint strength would reuse a hard-gated contract for a softened rule.

So equivalence is declared, not assumed. A profile names exactly which fields are presentation
rather than semantics, the choice is versioned, and the allowed list is closed: strength,
polarity, predicate arguments and authority are never presentational, and no profile can say
otherwise. A caller who wants those to be ignorable needs a contract amendment, not a
configuration value (§5.45).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .base import Labeled, Record, of
from .briefs import BriefRevision
from .constraints import Constraint, ConstraintBundle
from .errors import SchemaValidationError, UnsupportedVersionError
from .identity import RefKind, SemanticRef, require_bound_ref
from .intent import IntentModel, IntentStatement
from .limits import (
    MAX_DELTA_ENTRIES,
    MAX_EQUIVALENCE_RULES,
    MAX_METADATA_KEYS,
    MAX_PATHS_PER_SLICE,
)
from .normalization import ConstraintNormalForm, normalize_bundle
from .versions import (
    CONTRACT_VERSION,
    canonical_json,
    content_digest,
    require_contract_version,
    require_digest,
    require_identifier,
    require_semantic_path,
    require_text,
    require_version_text,
)

__all__ = [
    "ALLOWED_PRESENTATION_FIELDS",
    "ChangeKind",
    "DeltaSubjectKind",
    "ConstraintFingerprint",
    "IntentDelta",
    "SemanticChange",
    "SemanticDelta",
    "SemanticEquivalenceProfile",
    "SemanticIntentFingerprint",
    "diff_bundles",
    "diff_models",
    "fingerprint_bundle",
    "fingerprint_model",
    "fingerprint_revision",
    "require_same_profile",
]

#: The only fields a profile may declare presentational.
#:
#: Everything here is how a rule is explained or recorded. Strength, polarity, predicate
#: arguments, scope, authority and provenance are absent on purpose: they change what compliance
#: means, so a profile that could mark them ignorable would let one configuration value switch
#: off half the invariants (§5.45).
ALLOWED_PRESENTATION_FIELDS = frozenset(
    {
        "rationale",
        "notes",
        "label",
        "recorded_at",
        "created_at",
        "captured_at",
        "metadata",
        "declared_unit",
        "assertion",
        "description",
        "display_name",
        "transcription",
        "locator",
        "sort_hint",
    }
)

#: Fields whose change is always correctness-relevant, checked rather than implied by absence.
CORE_FIELDS = frozenset(
    {
        "semantic_path",
        "predicate",
        "polarity",
        "strength",
        "scope",
        "authority",
        "mandatory",
        "conditions",
        "tolerances",
        "protected_anchors",
        "anti_references",
        "value",
        "kind",
        "modality",
        "subject_ref",
        "origin",
    }
)


@dataclass(frozen=True)
class SemanticEquivalenceProfile(Record):
    """Declared, versioned rules for what counts as the same meaning.

    Profiles are additive rather than subtractive: a profile may say a field is presentation,
    and may ignore metadata keys and unit spellings, but it may not exclude a core field from
    the comparison. That asymmetry is the whole safety property — without it, "equivalence"
    would be a knob for deciding which requirements to notice.
    """

    profile_id: str
    version: str
    presentation_fields: tuple[str, ...] = ()
    ignored_metadata_keys: tuple[str, ...] = ()
    unit_spellings_equivalent: bool = True
    wording_equivalent_assertions: bool = True
    ignored_path_prefixes: tuple[str, ...] = ()
    description: str | None = None
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", require_identifier(self.profile_id, "profile_id"))
        object.__setattr__(self, "version", require_version_text(self.version, "version"))
        fields = tuple(sorted({require_identifier(item, "presentation_fields[]") for item in (self.presentation_fields or ())}))
        illegal = sorted(set(fields) - ALLOWED_PRESENTATION_FIELDS)
        if illegal:
            raise SchemaValidationError(
                f"profile {self.profile_id} declares {illegal} presentational; those fields are not "
                "in the admitted presentational set, and ignoring one would make the fingerprint "
                "blind to a requirement (§5.45)"
            )
        object.__setattr__(self, "presentation_fields", fields)
        if len(fields) > MAX_EQUIVALENCE_RULES:
            raise SchemaValidationError(
                f"profile {self.profile_id} declares {len(fields)} presentation fields, above "
                f"{MAX_EQUIVALENCE_RULES}"
            )
        object.__setattr__(
            self,
            "ignored_metadata_keys",
            tuple(sorted({require_identifier(item, "ignored_metadata_keys[]") for item in (self.ignored_metadata_keys or ())})),
        )
        object.__setattr__(
            self,
            "ignored_path_prefixes",
            tuple(sorted({require_semantic_path(item, "ignored_path_prefixes[]") for item in (self.ignored_path_prefixes or ())})),
        )
        for name in ("unit_spellings_equivalent", "wording_equivalent_assertions"):
            if not isinstance(getattr(self, name), bool):
                raise SchemaValidationError(f"{name} must be a boolean")
        if self.description is not None:
            object.__setattr__(
                self, "description", require_text(self.description, "description", maximum=1024)
            )
        object.__setattr__(
            self,
            "contract_version",
            require_contract_version(self.contract_version or CONTRACT_VERSION),
        )

    @property
    def ref(self) -> SemanticRef:
        return SemanticRef(
            kind=RefKind.POLICY.value, ref_id=self.profile_id, version=self.version
        ).with_digest(self.digest())

    @property
    def is_default(self) -> bool:
        return not (self.presentation_fields or self.ignored_metadata_keys or self.ignored_path_prefixes)

    def project(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Strip presentational data out of a payload before it is hashed.

        Recursion is depth-first over dicts and lists so a nested record's ``rationale`` is
        removed too; leaving it in would mean a fingerprint depended on how deep the prose sat.
        """

        if not isinstance(payload, Mapping):
            raise SchemaValidationError("projection needs a mapping payload")
        return _project(payload, self)

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "version": self.version,
            "presentation_fields": list(self.presentation_fields),
            "ignored_metadata_keys": list(self.ignored_metadata_keys),
            "ignored_path_prefixes": list(self.ignored_path_prefixes),
            "unit_spellings_equivalent": self.unit_spellings_equivalent,
            "wording_equivalent_assertions": self.wording_equivalent_assertions,
            "contract_version": self.contract_version,
        }


def _project(value: Any, profile: SemanticEquivalenceProfile) -> Any:
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if name in profile.presentation_fields:
                continue
            if name in profile.ignored_metadata_keys:
                continue
            if name == "metadata" and profile.ignored_metadata_keys:
                out[name] = {
                    k: _project(v, profile)
                    for k, v in sorted(dict(item or {}).items())
                    if k not in profile.ignored_metadata_keys
                }
                continue
            if name == "declared_unit" and profile.unit_spellings_equivalent:
                continue
            out[name] = _project(item, profile)
        return dict(sorted(out.items()))
    if isinstance(value, (list, tuple)):
        return [_project(item, profile) for item in value]
    return value


DEFAULT_EQUIVALENCE_PROFILE = SemanticEquivalenceProfile(
    profile_id="m03-equivalence-default",
    version="v1",
    presentation_fields=("rationale", "notes", "declared_unit"),
    description=(
        "Rationale and wording are explanation, not requirement; unit spellings are canonicalised "
        "at construction, so declaring them equivalent is a statement about the fingerprint, not a "
        "conversion."
    ),
)


@dataclass(frozen=True)
class SemanticIntentFingerprint(Record):
    """The hashed shape of one intent model, plus the per-path view.

    ``path_digests`` exists because a delta over a whole model is too coarse to act on: reusing
    an unaffected sub-requirement needs to know *which* paths moved, and recomputing the model
    for that would defeat the point of fingerprinting (§15).
    """

    fingerprint_id: str
    revision_ref: SemanticRef
    model_ref: SemanticRef
    profile_ref: SemanticRef
    semantic_digest: str
    path_digests: Mapping[str, str] = field(default_factory=dict)
    statement_count: int = 0
    mandatory_count: int = 0
    authority_rank: int = 0
    modalities: tuple[str, ...] = ()
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "fingerprint_id", require_identifier(self.fingerprint_id, "fingerprint_id"))
        object.__setattr__(
            self, "revision_ref", require_bound_ref(self.revision_ref, "revision_ref", kind=RefKind.REVISION)
        )
        object.__setattr__(self, "model_ref", SemanticRef.coerce(self.model_ref, "model_ref"))
        object.__setattr__(self, "profile_ref", SemanticRef.coerce(self.profile_ref, "profile_ref"))
        object.__setattr__(self, "semantic_digest", _digest_field(self.semantic_digest, "semantic_digest"))
        paths = {
            require_semantic_path(key, "path_digests key"): _digest_field(value, f"path_digests[{key}]")
            for key, value in sorted(dict(self.path_digests or {}).items())
        }
        if len(paths) > MAX_PATHS_PER_SLICE:
            raise SchemaValidationError(
                f"fingerprint {self.fingerprint_id} covers {len(paths)} paths, above {MAX_PATHS_PER_SLICE}"
            )
        object.__setattr__(self, "path_digests", paths)
        for name in ("statement_count", "mandatory_count", "authority_rank"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise SchemaValidationError(f"{name} must be a non-negative integer")
        object.__setattr__(
            self,
            "modalities",
            tuple(sorted({require_text(item, "modalities[]", maximum=32).upper() for item in (self.modalities or ())})),
        )
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    def digest_for(self, semantic_path: str) -> str | None:
        return self.path_digests.get(require_semantic_path(semantic_path, "semantic_path"))

    def is_equivalent_to(self, other: "SemanticIntentFingerprint") -> bool:
        """Equality under the same declared profile — never equality of ids.

        Ids differ per computation; if they were part of the comparison no two runs of the same
        brief would ever match, which is the entire use case.
        """

        if not isinstance(other, SemanticIntentFingerprint):
            raise SchemaValidationError("equivalence needs another fingerprint")
        return (
            self.semantic_digest == other.semantic_digest
            and self.profile_ref.text == other.profile_ref.text
            and self.contract_version == other.contract_version
        )

    def changed_paths(self, other: "SemanticIntentFingerprint") -> tuple[str, ...]:
        require_same_profile(self.profile_ref, other.profile_ref, "compare paths")
        keys = set(self.path_digests) | set(other.path_digests)
        return tuple(
            sorted(
                key
                for key in keys
                if self.path_digests.get(key) != other.path_digests.get(key)
            )
        )


SemanticIntentFingerprint.NESTED = {
    "revision_ref": of(SemanticRef),
    "model_ref": of(SemanticRef),
    "profile_ref": of(SemanticRef),
}


@dataclass(frozen=True)
class ConstraintFingerprint(Record):
    """Fingerprint of an admitted bundle, with the normal form it was reduced through.

    ``form_digest`` is recorded because the form is what compilation actually consumes; two
    bundles with different insertion order can share a form digest, and that is the case reuse
    needs to see. ``context_digest`` is non-null only when the fingerprint was taken for a
    specific work context, i.e. conditional rules were resolved.
    """

    fingerprint_id: str
    bundle_ref: SemanticRef
    profile_ref: SemanticRef
    semantic_digest: str
    form_digest: str
    path_digests: Mapping[str, str] = field(default_factory=dict)
    constraint_count: int = 0
    negative_count: int = 0
    hard_count: int = 0
    context_digest: str | None = None
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "fingerprint_id", require_identifier(self.fingerprint_id, "fingerprint_id"))
        object.__setattr__(self, "bundle_ref", SemanticRef.coerce(self.bundle_ref, "bundle_ref"))
        object.__setattr__(self, "profile_ref", SemanticRef.coerce(self.profile_ref, "profile_ref"))
        object.__setattr__(self, "semantic_digest", _digest_field(self.semantic_digest, "semantic_digest"))
        object.__setattr__(self, "form_digest", _digest_field(self.form_digest, "form_digest"))
        object.__setattr__(
            self,
            "path_digests",
            {
                require_semantic_path(key, "path_digests key"): _digest_field(value, f"path_digests[{key}]")
                for key, value in sorted(dict(self.path_digests or {}).items())
            },
        )
        for name in ("constraint_count", "negative_count", "hard_count"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise SchemaValidationError(f"{name} must be a non-negative integer")
        if self.negative_count > self.constraint_count or self.hard_count > self.constraint_count:
            raise SchemaValidationError(
                "constraint counts disagree: negatives and hards cannot outnumber the total"
            )
        if self.context_digest is not None:
            object.__setattr__(self, "context_digest", _digest_field(self.context_digest, "context_digest"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    def is_equivalent_to(self, other: "ConstraintFingerprint") -> bool:
        if not isinstance(other, ConstraintFingerprint):
            raise SchemaValidationError("equivalence needs another fingerprint")
        return (
            self.semantic_digest == other.semantic_digest
            and self.form_digest == other.form_digest
            and self.profile_ref.text == other.profile_ref.text
        )


ConstraintFingerprint.NESTED = {
    "bundle_ref": of(SemanticRef),
    "profile_ref": of(SemanticRef),
}


class DeltaSubjectKind(Labeled):
    """What kind of subject a delta compares.

    The kind is declared rather than inferred from the refs because a fingerprint ref can be
    carried forward unchanged between stages, and a consumer deciding what to invalidate from a
    ref's shape alone would eventually invalidate the wrong layer.
    """

    INTENT = "INTENT"
    CONSTRAINT = "CONSTRAINT"
    EXECUTION = "EXECUTION"
    QUALITY = "QUALITY"
    REVISION = "REVISION"


class ChangeKind(Labeled):
    """How one semantic element moved between two fingerprints.

    ``RESTATED`` and ``REAUTHORED`` are separate from ``RELAXED`` and ``STRENGTHENED`` because
    the first pair changes nothing about compliance while the second pair does, and a consumer
    that sees one category has to re-check everything. The distinction is what lets an edit to
    a rationale leave a compiled contract reusable (§5.45).
    """

    ADDED = "ADDED"
    REMOVED = "REMOVED"
    RESTATED = "RESTATED"
    RESCOPED = "RESCOPED"
    REAUTHORED = "REAUTHORED"
    STRENGTHENED = "STRENGTHENED"
    RELAXED = "RELAXED"
    REPREDICATED = "REPREDICATED"
    POLARITY_FLIPPED = "POLARITY_FLIPPED"
    ANCHOR_LOST = "ANCHOR_LOST"
    EQUIVALENT = "EQUIVALENT"

    @property
    def correctness_relevant(self) -> bool:
        """Whether a consumer may keep whatever it derived from the previous state.

        Only three kinds are safe to reuse across: restatement, re-authoring and explicit
        equivalence. Everything else can change what satisfies the requirement, and a
        conservatively wrong "no" here costs a rebuild while a wrong "yes" costs a release
        built on a requirement nobody admitted (§5.45, §5.27).
        """

        return self not in {ChangeKind.RESTATED, ChangeKind.REAUTHORED, ChangeKind.EQUIVALENT}


@dataclass(frozen=True)
class SemanticChange(Record):
    """One path-level movement, with the two digests that produced the verdict."""

    change_id: str
    kind: str
    semantic_path: str
    before_digest: str | None = None
    after_digest: str | None = None
    subject_refs: tuple[SemanticRef, ...] = ()
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "change_id", require_identifier(self.change_id, "change_id"))
        kind = ChangeKind.parse(self.kind, "kind")
        object.__setattr__(self, "kind", kind.value)
        object.__setattr__(self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path"))
        for name in ("before_digest", "after_digest"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _digest_field(value, name))
        if self.before_digest == self.after_digest and kind is not ChangeKind.EQUIVALENT:
            raise SchemaValidationError(
                f"change {self.change_id} reports {kind.value} with identical digests; either the "
                "kind is wrong or the change is not real, and a delta with invented entries is "
                "worse than an empty one"
            )
        refs = tuple(
            sorted(
                (SemanticRef.coerce(item, "subject_refs[]") for item in (self.subject_refs or ())),
                key=lambda item: item.text,
            )
        )
        if len(refs) > MAX_METADATA_KEYS:
            raise SchemaValidationError(
                f"change {self.change_id} cites {len(refs)} subjects, above {MAX_METADATA_KEYS}"
            )
        object.__setattr__(self, "subject_refs", refs)
        if self.note is not None:
            object.__setattr__(self, "note", require_text(self.note, "note", maximum=512))

    @property
    def kind_enum(self) -> ChangeKind:
        return ChangeKind.parse(self.kind)

    @property
    def correctness_relevant(self) -> bool:
        return self.kind_enum.correctness_relevant

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "semantic_path": self.semantic_path,
            "before": self.before_digest,
            "after": self.after_digest,
            "subjects": sorted(item.text for item in self.subject_refs),
        }


SemanticChange.NESTED = {"subject_refs": of(SemanticRef)}


@dataclass(frozen=True)
class SemanticDelta(Record):
    """The difference between two fingerprints of the same subject kind.

    ``correctness_relevant`` is the field reuse decisions read, and it is derived from the
    changes rather than supplied: a caller that could set it directly could declare any delta
    safe to reuse and the fingerprints would become a formality (§15, §5.45).
    """

    delta_id: str
    subject_kind: str
    before_ref: SemanticRef
    after_ref: SemanticRef
    profile_ref: SemanticRef
    changes: tuple[SemanticChange, ...] = ()
    correctness_relevant: bool = True
    delta_digest: str = ""
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "delta_id", require_identifier(self.delta_id, "delta_id"))
        object.__setattr__(self, "subject_kind", DeltaSubjectKind.parse(self.subject_kind, "subject_kind").value)
        object.__setattr__(self, "before_ref", SemanticRef.coerce(self.before_ref, "before_ref"))
        object.__setattr__(self, "after_ref", SemanticRef.coerce(self.after_ref, "after_ref"))
        object.__setattr__(self, "profile_ref", SemanticRef.coerce(self.profile_ref, "profile_ref"))
        changes = tuple(
            sorted(
                (SemanticChange.coerce(item, "changes[]") for item in (self.changes or ())),
                key=lambda item: (item.semantic_path, item.kind, item.change_id),
            )
        )
        if len(changes) > MAX_DELTA_ENTRIES:
            raise SchemaValidationError(
                f"delta {self.delta_id} holds {len(changes)} changes, above {MAX_DELTA_ENTRIES}"
            )
        object.__setattr__(self, "changes", changes)
        # Recomputed rather than validated: the flag is a cached view of the changes so that a
        # reader need not re-derive it, and letting a caller supply it would mean one field could
        # assert "safe to reuse" while the changes said otherwise (§5.45).
        object.__setattr__(self, "correctness_relevant", any(item.correctness_relevant for item in changes))
        object.__setattr__(
            self,
            "delta_digest",
            _digest_field(
                self.delta_digest
                or content_digest({"changes": [item.fingerprint_inputs() for item in changes]}),
                "delta_digest",
            ),
        )
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def empty(self) -> bool:
        return not self.changes

    @property
    def touched_paths(self) -> tuple[str, ...]:
        return tuple(sorted({item.semantic_path for item in self.changes}))

    def relevant_paths(self) -> tuple[str, ...]:
        """Paths whose change may invalidate downstream work.

        The list is usually smaller than ``touched_paths``, and that gap is exactly the
        token-economy claim: a restated rationale touches a path without invalidating anything
        derived from it (§15).
        """

        return tuple(sorted({item.semantic_path for item in self.changes if item.correctness_relevant}))

    def of_kind(self, kind: str) -> tuple[SemanticChange, ...]:
        wanted = ChangeKind.parse(kind, "kind").value
        return tuple(item for item in self.changes if item.kind == wanted)

    def fingerprint_inputs(self) -> list[Any]:
        return [item.fingerprint_inputs() for item in self.changes]


SemanticDelta.NESTED = {
    "before_ref": of(SemanticRef),
    "after_ref": of(SemanticRef),
    "profile_ref": of(SemanticRef),
    "changes": of(SemanticChange),
}

#: ``IntentDelta`` is the frozen contract's name for this concept; one class serves all four
#: subject kinds because the shape of "what moved" does not depend on what moved.
IntentDelta = SemanticDelta


def fingerprint_model(
    model: IntentModel,
    *,
    profile: SemanticEquivalenceProfile = DEFAULT_EQUIVALENCE_PROFILE,
    fingerprint_id: str | None = None,
    revision_ref: SemanticRef | None = None,
) -> SemanticIntentFingerprint:
    """Hash a model's semantics per path under a declared profile."""

    if not isinstance(model, IntentModel):
        raise SchemaValidationError("fingerprint_model expects an IntentModel")
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for statement in model.statements:
        grouped.setdefault(statement.semantic_path, []).append(
            profile.project(_statement_core(statement))
        )
    paths = {
        path: content_digest(sorted((canonical_json(item) for item in items)))
        for path, items in sorted(grouped.items())
    }
    if len(paths) > MAX_PATHS_PER_SLICE:
        raise SchemaValidationError(
            f"model {model.model_id} spans {len(paths)} paths, above {MAX_PATHS_PER_SLICE}"
        )
    return SemanticIntentFingerprint(
        fingerprint_id=fingerprint_id or f"fp-{model.model_id}-{profile.version}",
        revision_ref=revision_ref or SemanticRef(kind=RefKind.REVISION.value, ref_id=model.revision_id, version=f"v{model.revision_number}"),
        model_ref=model.model_ref,
        profile_ref=profile.ref,
        semantic_digest=content_digest({"paths": paths, "profile": profile.profile_id, "version": profile.version}),
        path_digests=paths,
        statement_count=len(model.statements),
        mandatory_count=sum(1 for item in model.statements if item.mandatory),
        authority_rank=model.max_authority.rank,
        modalities=model.modalities,
        contract_version=CONTRACT_VERSION,
    )


def fingerprint_revision(
    revision: BriefRevision,
    *,
    profile: SemanticEquivalenceProfile = DEFAULT_EQUIVALENCE_PROFILE,
    fingerprint_id: str | None = None,
) -> SemanticIntentFingerprint:
    """Fingerprint a revision directly, without building a model.

    Useful before clarification: the revision is admitted truth while the model is a derived
    view, and a stale-check that only works after modelling could not protect modelling itself.
    """

    if not isinstance(revision, BriefRevision):
        raise SchemaValidationError("fingerprint_revision expects a BriefRevision")
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for statement in revision.statements:
        grouped.setdefault(statement.semantic_path, []).append(profile.project(_statement_core(statement)))
    paths = {
        path: content_digest(sorted((canonical_json(item) for item in items)))
        for path, items in sorted(grouped.items())
    }
    return SemanticIntentFingerprint(
        fingerprint_id=fingerprint_id or f"fp-{revision.revision_id}-{profile.version}",
        revision_ref=revision.revision_ref,
        model_ref=revision.revision_ref,
        profile_ref=profile.ref,
        semantic_digest=content_digest({"paths": paths, "sources": sorted(item.source_id for item in revision.sources)}),
        path_digests=paths,
        statement_count=len(revision.statements),
        mandatory_count=sum(1 for item in revision.statements if item.mandatory),
        authority_rank=max((item.authority.level.rank for item in revision.statements), default=0),
        modalities=tuple(sorted({item.modality for item in revision.statements})),
        contract_version=CONTRACT_VERSION,
    )


def fingerprint_bundle(
    bundle: ConstraintBundle,
    *,
    profile: SemanticEquivalenceProfile = DEFAULT_EQUIVALENCE_PROFILE,
    form: ConstraintNormalForm | None = None,
    context: Mapping[str, Any] | None = None,
    fingerprint_id: str | None = None,
) -> ConstraintFingerprint:
    """Hash an admitted bundle through its normal form.

    The normal form is the input rather than the raw constraint list, so re-entry of the same
    requirement in different words does not move the digest; the raw list is still hashed as
    ``semantic_digest`` for callers that need provenance-level equality (§15).
    """

    if not isinstance(bundle, ConstraintBundle):
        raise SchemaValidationError("fingerprint_bundle expects a ConstraintBundle")
    normalized = form or normalize_bundle(bundle)
    active = normalized.active_rules(context)
    grouped: dict[str, list[str]] = {}
    for rule in active:
        if any(rule.semantic_path.startswith(prefix) for prefix in profile.ignored_path_prefixes):
            continue
        grouped.setdefault(rule.semantic_path, []).append(canonical_json(profile.project(rule.fingerprint_inputs())))
    paths = {path: content_digest(sorted(items)) for path, items in sorted(grouped.items())}
    raw = [profile.project(item.fingerprint_inputs()) for item in sorted(bundle.constraints, key=lambda item: item.constraint_id)]
    return ConstraintFingerprint(
        fingerprint_id=fingerprint_id or f"cfp-{bundle.bundle_id}-{profile.version}",
        bundle_ref=bundle.bundle_ref,
        profile_ref=profile.ref,
        semantic_digest=content_digest(raw),
        form_digest=normalized.digest_of(),
        path_digests=paths,
        constraint_count=len(bundle.constraints),
        negative_count=len(bundle.negative_constraints()),
        hard_count=len(bundle.hard_constraints()),
        context_digest=None if context is None else content_digest(dict(sorted(context.items()))),
        contract_version=CONTRACT_VERSION,
    )


def diff_models(
    before: SemanticIntentFingerprint,
    after: SemanticIntentFingerprint,
    *,
    delta_id: str | None = None,
) -> SemanticDelta:
    """Path-level difference between two model fingerprints.

    A path present on one side only is ADDED/REMOVED; a path on both with different digests is
    classified by what actually differs, which the caller supplies through the fingerprints'
    path digests only. Coarse here on purpose: the precise classification of a constraint
    change is :func:`diff_bundles`, where the rule structure is available.
    """

    require_same_profile(before.profile_ref, after.profile_ref, "compare model fingerprints")
    changes: list[SemanticChange] = []
    for path in before.changed_paths(after):
        left, right = before.digest_for(path), after.digest_for(path)
        kind = (
            ChangeKind.ADDED if left is None else ChangeKind.REMOVED if right is None else ChangeKind.REPREDICATED
        )
        changes.append(
            SemanticChange(
                change_id=f"chg-{path}-{content_digest({'l': left, 'r': right})[:12]}",
                kind=kind.value,
                semantic_path=path,
                before_digest=left,
                after_digest=right,
            )
        )
    return SemanticDelta(
        delta_id=delta_id or f"delta-{before.semantic_digest[:8]}-{after.semantic_digest[:8]}",
        subject_kind="INTENT",
        before_ref=before.model_ref,
        after_ref=after.model_ref,
        profile_ref=before.profile_ref,
        changes=tuple(changes),
    )


def diff_bundles(
    before: ConstraintBundle,
    after: ConstraintBundle,
    *,
    profile: SemanticEquivalenceProfile = DEFAULT_EQUIVALENCE_PROFILE,
    delta_id: str | None = None,
) -> SemanticDelta:
    """Classify how an admitted rule set changed, rule by rule.

    Matching is by (path, predicate identity) rather than by constraint id, because a rewritten
    rule keeps its meaning while its id usually changes — and a delta that reported that as
    REMOVED plus ADDED would invalidate every obligation on the path for a rename (§5.45).
    """

    if not isinstance(before, ConstraintBundle) or not isinstance(after, ConstraintBundle):
        raise SchemaValidationError("diff_bundles expects two ConstraintBundles")
    left = {item.constraint_id: item for item in before.constraints}
    right = {item.constraint_id: item for item in after.constraints}
    changes: list[SemanticChange] = []
    matched_right: set[str] = set()
    for identifier, old in sorted(left.items()):
        new = right.get(identifier)
        if new is None:
            new = _relinked(old, right, matched_right)
        if new is None:
            changes.append(
                SemanticChange(
                    change_id=f"chg-{identifier}-removed",
                    kind=ChangeKind.REMOVED.value,
                    semantic_path=old.semantic_path,
                    before_digest=old.digest(),
                    subject_refs=(old.constraint_ref,),
                )
            )
            continue
        matched_right.add(new.constraint_id)
        changes.extend(_classify(old, new))
    for identifier, new in sorted(right.items()):
        if identifier in matched_right or identifier in left:
            continue
        matched_right.add(identifier)
        changes.append(
            SemanticChange(
                change_id=f"chg-{identifier}-added",
                kind=ChangeKind.ADDED.value,
                semantic_path=new.semantic_path,
                after_digest=new.digest(),
                subject_refs=(new.constraint_ref,),
            )
        )
    return SemanticDelta(
        delta_id=delta_id or f"cdelta-{before.bundle_id}-{after.bundle_id}",
        subject_kind="CONSTRAINT",
        before_ref=before.bundle_ref,
        after_ref=after.bundle_ref,
        profile_ref=profile.ref,
        changes=tuple(changes),
    )


def _relinked(old: Constraint, right: Mapping[str, Constraint], taken: set[str]) -> Constraint | None:
    """Find the successor of a rule whose id changed.

    Only an unambiguous single candidate counts; two candidates means the rewrite split a rule,
    which is a REMOVED plus two ADDED, and reporting it as a restatement would hide that a
    requirement was divided between two weaker or differently scoped rules.
    """

    candidates = [
        item
        for identifier, item in right.items()
        if identifier not in taken
        and item.semantic_path == old.semantic_path
        and item.predicate.reference == old.predicate.reference
    ]
    return candidates[0] if len(candidates) == 1 else None


def _classify(old: Constraint, new: Constraint) -> list[SemanticChange]:
    changes: list[SemanticChange] = []
    if old.digest() == new.digest():
        return changes
    if old.polarity != new.polarity:
        kind = ChangeKind.POLARITY_FLIPPED
    elif old.strength != new.strength:
        from .constraints import ConstraintStrength

        kind = (
            ChangeKind.STRENGTHENED
            if ConstraintStrength.parse(new.strength).rank > ConstraintStrength.parse(old.strength).rank
            else ChangeKind.RELAXED
        )
    elif old.predicate.to_payload() != new.predicate.to_payload():
        kind = ChangeKind.REPREDICATED
    elif old.scope.to_payload() != new.scope.to_payload():
        kind = ChangeKind.RESCOPED
    elif old.authority.to_payload() != new.authority.to_payload():
        kind = ChangeKind.REAUTHORED
    elif _only_presentation_differs(old, new):
        kind = ChangeKind.RESTATED
    else:
        kind = ChangeKind.REPREDICATED
    if kind is ChangeKind.RESCOPED and _scope_broadened(old, new):
        kind = ChangeKind.STRENGTHENED
    changes.append(
        SemanticChange(
            change_id=f"chg-{old.constraint_id}-{kind.value.lower()}",
            kind=kind.value,
            semantic_path=old.semantic_path,
            before_digest=old.digest(),
            after_digest=new.digest(),
            subject_refs=(old.constraint_ref, new.constraint_ref),
            note=None if kind is not ChangeKind.RELAXED else "a relaxation reported by diff, not by receipt",
        )
    )
    lost = {item.anchor_id for item in old.protected_anchors} - {item.anchor_id for item in new.protected_anchors}
    for anchor_id in sorted(lost):
        changes.append(
            SemanticChange(
                change_id=f"chg-{old.constraint_id}-anchor-{anchor_id}",
                kind=ChangeKind.ANCHOR_LOST.value,
                semantic_path=old.semantic_path,
                after_digest=new.digest(),
                subject_refs=(new.constraint_ref,),
                note=f"protected anchor {anchor_id} is no longer carried",
            )
        )
    return changes


_PRESENTATION = ("rationale", "notes", "metadata")


def _only_presentation_differs(old: Constraint, new: Constraint) -> bool:
    left = old.to_payload()
    right = new.to_payload()
    for name in _PRESENTATION:
        left.pop(name, None)
        right.pop(name, None)
    return left == right


def _scope_broadened(old: Constraint, new: Constraint) -> bool:
    """Whether a scope edit made the rule reach further, which is a strengthening.

    "Same subject paths but fewer exclusions" is the shape that matters: the requirement now
    binds work it did not bind, and classifying that as a neutral rescope would let a broadened
    prohibition pass as a wording edit (§5.11, §5.45).
    """

    return set(old.scope.subject_paths) <= set(new.scope.subject_paths) and len(new.scope.excluded_paths) < len(
        old.scope.excluded_paths
    )


def _statement_core(statement: IntentStatement) -> dict[str, Any]:
    payload = statement.to_payload()
    payload.pop("statement_id", None)
    return payload


def require_same_profile(left: SemanticRef, right: SemanticRef, action: str) -> None:
    """Refuse comparisons across profiles.

    Two fingerprints computed under different equivalence rules are not comparable, and a diff
    that pretended otherwise would report "no change" for the one difference its profiles were
    configured to disagree about — the least visible failure this module can produce.
    """

    a, b = SemanticRef.coerce(left, "left profile"), SemanticRef.coerce(right, "right profile")
    if a.ref_id != b.ref_id or a.version != b.version:
        raise UnsupportedVersionError(
            f"cannot {action} under profile {a.text} and {b.text}; equivalence rules differ, so the "
            "comparison would say something about the profiles rather than the semantics"
        )


def _digest_field(value: Any, name: str) -> str:
    return require_digest(value, name)
