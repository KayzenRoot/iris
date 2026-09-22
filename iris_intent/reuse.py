"""Reuse passports: earn a recompile by proving nothing moved (F-M03-04, §15).

Compilation is the expensive part of M03. A brief that has already been through admission,
normalisation and fidelity compilation should not have to do it again because a provider's
capability table moved, or because the same requirement was restated in a meeting and re-entered
with new wording. But "skip the work" is exactly the sentence a correctness-critical kernel has
to be suspicious of, because every shortcut is also the shape a stale artifact takes to survive:
reuse is the case where an unchecked invalidation becomes a shipped artifact.

A passport is the honest version of that shortcut. It records *what was compiled* (the semantic
digest of the derivation, optionally its normal form and its provider-facing mapping) and *what
it depended on* (a :class:`~iris_intent.freshness.DerivedIntentDependency` per input), and it
carries no claim of currency at all. Freshness is recomputed at read time against state the
caller observes; :func:`evaluate_reuse` then decides among five outcomes, from "reuse as is" down
to "refuse, because the inputs could not be checked". The passport cannot assert its own validity
— there is no field for it — which is the §18.38 requirement expressed as a data shape.

Two decisions in here are load-bearing beyond convenience. A change of equivalence profile
invalidates comparison itself, so digests computed under different profiles are never treated as
equal, however similar they look: the profile decides *what counts as the same thing*. And a
source-only edit is allowed to preserve reuse only when an admitted delta testifies that nothing
correctness-relevant moved — no delta, no free pass, because "it looks like a rewording" is the
justification every stale artifact would otherwise arrive with.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .base import Labeled, Record, of
from .errors import SchemaValidationError, StaleSemanticError
from .fingerprints import ConstraintFingerprint, IntentDelta, SemanticIntentFingerprint
from .freshness import (
    DerivedArtifactKind,
    DerivedIntentDependency,
    DerivedScope,
    BriefFreshnessVector,
    FreshnessDimension,
    assess_freshness,
)
from .identity import RefKind, SemanticRef, require_bound_ref
from .limits import MAX_DEPENDENCIES_PER_ARTIFACT, MAX_PATHS_PER_SLICE
from .sources import bounded_metadata
from .versions import (
    CONTRACT_VERSION,
    content_digest,
    require_contract_version,
    require_digest,
    require_identifier,
    require_semantic_path,
    require_text,
)

__all__ = [
    "RecomputeScope",
    "ReuseAssessment",
    "ReusePassport",
    "ReuseVerdict",
    "evaluate_reuse",
    "passport_for",
    "require_reusable",
    "requires_whole",
]


class RecomputeScope(Labeled):
    """How much has to be rebuilt for the reuse decision at hand.

    ``PATHS`` is the proportionality outcome §18 asks for: the derived artifact stands and the
    listed semantic paths are re-derived. ``ARTIFACT`` is the whole thing, and it is chosen only
    where a dependency declared total invalidation, where comparison is impossible (a different
    equivalence profile), or where the inputs could not be checked at all.
    """

    NONE = "NONE"
    MAPPING = "MAPPING"
    PATHS = "PATHS"
    ARTIFACT = "ARTIFACT"

    @property
    def rebuilds_semantics(self) -> bool:
        return self in {RecomputeScope.PATHS, RecomputeScope.ARTIFACT}

    @property
    def rebuilds_mapping(self) -> bool:
        return self in {RecomputeScope.MAPPING, RecomputeScope.ARTIFACT}


class ReuseVerdict(Labeled):
    """What may be carried over, and what may not.

    The five members exist because there are genuinely five different answers, and a ladder with
    fewer rungs forces the wrong one: a kernel that can only say "reuse" or "recompile" says
    recompile whenever a provider changes, which teaches teams to skip revalidation.
    """

    REUSE = "REUSE"
    REUSE_EQUIVALENT = "REUSE_EQUIVALENT"
    REUSE_SEMANTICS_ONLY = "REUSE_SEMANTICS_ONLY"
    RECOMPILE = "RECOMPILE"
    REFUSE_UNVERIFIED = "REFUSE_UNVERIFIED"

    @property
    def reuses_semantics(self) -> bool:
        """Whether the compiled requirements may be carried over.

        ``REFUSE_UNVERIFIED`` is excluded on purpose. Unverified is not the same as changed — it
        is the state where the kernel cannot tell, and telling is the whole job.
        """

        return self in {
            ReuseVerdict.REUSE,
            ReuseVerdict.REUSE_EQUIVALENT,
            ReuseVerdict.REUSE_SEMANTICS_ONLY,
        }

    @property
    def rebuilds_everything(self) -> bool:
        return self in {ReuseVerdict.RECOMPILE, ReuseVerdict.REFUSE_UNVERIFIED}

    @property
    def saves_work(self) -> bool:
        return self.reuses_semantics


@dataclass(frozen=True)
class ReusePassport(Record):
    """What was compiled, and what it was compiled from.

    Note what is absent: no expiry date, no "still valid" flag, no cached verdict. A passport is
    evidence about a past derivation, and the only question §18.38 asks of past derivations is
    whether their inputs still hold — which is decided later, against state, every single time.
    """

    passport_id: str
    subject_ref: SemanticRef
    subject_kind: str
    brief_ref: SemanticRef
    revision_ref: SemanticRef
    profile_ref: SemanticRef
    semantic_digest: str
    dependencies: tuple[DerivedIntentDependency, ...] = ()
    form_digest: str | None = None
    mapping_digest: str | None = None
    issued_by: SemanticRef | None = None
    rationale: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "passport_id", require_identifier(self.passport_id, "passport_id"))
        object.__setattr__(self, "subject_ref", SemanticRef.coerce(self.subject_ref, "subject_ref"))
        object.__setattr__(
            self, "subject_kind", DerivedArtifactKind.parse(self.subject_kind, "subject_kind").value
        )
        object.__setattr__(
            self, "brief_ref", require_bound_ref(self.brief_ref, "brief_ref", kind=RefKind.BRIEF)
        )
        object.__setattr__(
            self, "revision_ref", require_bound_ref(self.revision_ref, "revision_ref", kind=RefKind.REVISION)
        )
        object.__setattr__(self, "profile_ref", SemanticRef.coerce(self.profile_ref, "profile_ref"))
        object.__setattr__(self, "semantic_digest", require_digest(self.semantic_digest, "semantic_digest"))
        for name in ("form_digest", "mapping_digest"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_digest(value, name))
        items = tuple(
            sorted(
                (DerivedIntentDependency.coerce(item, "dependencies[]") for item in (self.dependencies or ())),
                key=lambda item: item.dependency_id,
            )
        )
        if not items:
            raise SchemaValidationError(
                f"passport {self.passport_id} declares no dependencies; a derived artifact that "
                "follows from nothing cannot show that anything still holds, so it cannot be reused"
            )
        if len(items) > MAX_DEPENDENCIES_PER_ARTIFACT:
            raise SchemaValidationError(
                f"passport {self.passport_id} carries {len(items)} dependencies, above "
                f"{MAX_DEPENDENCIES_PER_ARTIFACT}"
            )
        if len({item.dependency_id for item in items}) != len(items):
            raise SchemaValidationError(f"passport {self.passport_id} repeats a dependency id")
        foreign = sorted({item.derived_ref.text for item in items if item.derived_ref.text != self.subject_ref.text})
        if foreign:
            raise SchemaValidationError(
                f"passport {self.passport_id} carries dependencies of other artifacts {foreign}; "
                "one artifact's inputs cannot license another's reuse"
            )
        dims = {FreshnessDimension.parse(item.dimension).value for item in items}
        if any(item.scope is DerivedScope.MAPPING for item in items) and self.mapping_digest is None:
            raise SchemaValidationError(
                f"passport {self.passport_id} depends on carriage but records no mapping digest, so "
                "a stale provider input would block reuse with nothing to rebuild — either carry the "
                "mapping half or drop the mapping dependency"
            )
        object.__setattr__(self, "dependencies", items)
        self._check_dimensions(dims)
        if self.issued_by is not None:
            object.__setattr__(self, "issued_by", SemanticRef.coerce(self.issued_by, "issued_by"))
        if self.rationale is not None:
            object.__setattr__(self, "rationale", require_text(self.rationale, "rationale", maximum=1024))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    def _check_dimensions(self, dims: set[str]) -> None:
        # A passport and its brief must be re-checked as one unit: a derivation whose subject
        # revision or model is not among its declared inputs has an unaccounted-for input, and an
        # unaccounted input is precisely what a later "nothing moved" would miss.
        covered = {FreshnessDimension.SEMANTIC_MODEL.value, FreshnessDimension.SOURCE_REVISION.value}
        missing = sorted(covered - dims)
        if missing:
            raise SchemaValidationError(
                f"passport {self.passport_id} declares no dependency on {missing}; a derivation is "
                "only reusable if the revision and model it came from are among its checked inputs"
            )

    @property
    def dependency_ids(self) -> tuple[str, ...]:
        return tuple(item.dependency_id for item in self.dependencies)

    @property
    def dependency_set_digest(self) -> str:
        return content_digest([item.identity() for item in self.dependencies])

    @property
    def provider_neutral_key(self) -> str:
        """The reuse key for the provider-independent half of a derivation.

        Two passports with the same key compiled the same requirements, so a provider swap can
        carry them over — which is §15's claim that provider changes do not invalidate
        provider-neutral semantics, stated as something comparable rather than something hoped.
        """

        return content_digest(
            {
                "semantic_digest": self.semantic_digest,
                "form_digest": self.form_digest,
                "profile": self.profile_ref.text,
                "contract_version": self.contract_version,
            }
        )

    @property
    def full_key(self) -> str:
        return content_digest(
            {
                "provider_neutral": self.provider_neutral_key,
                "mapping_digest": self.mapping_digest,
                "dependency_set": self.dependency_set_digest,
            }
        )

    @property
    def carries_mapping(self) -> bool:
        return self.mapping_digest is not None

    @property
    def semantic_paths(self) -> tuple[str, ...]:
        paths: set[str] = set()
        for item in self.dependencies:
            paths.update(item.affected_paths)
        return tuple(sorted(paths))

    @property
    def total_dependencies(self) -> tuple[str, ...]:
        return tuple(sorted(item.dependency_id for item in self.dependencies if not item.partial))

    @property
    def passport_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.PASSPORT.value, ref_id=self.passport_id).with_digest(self.digest())

    def depends_on(self, upstream_ref: SemanticRef) -> tuple[DerivedIntentDependency, ...]:
        wanted = SemanticRef.coerce(upstream_ref, "upstream_ref").text
        return tuple(item for item in self.dependencies if item.upstream_ref.text == wanted)

    def freshness_vector(
        self,
        *,
        vector_id: str,
        upstream: Mapping[str, Mapping[str, Any]],
        revision_ordinal: int | None = None,
    ) -> BriefFreshnessVector:
        """Recompute currency for this passport's inputs, right now.

        Exposed as an operation rather than a stored field so that no code path can carry a stale
        vector forward as though it were still the answer.
        """

        return assess_freshness(
            vector_id=vector_id,
            brief_ref=self.brief_ref,
            revision_ref=self.revision_ref,
            subject_ref=self.subject_ref,
            dependencies=self.dependencies,
            upstream=upstream,
            revision_ordinal=revision_ordinal,
        )


ReusePassport.NESTED = {
    "subject_ref": of(SemanticRef),
    "brief_ref": of(SemanticRef),
    "revision_ref": of(SemanticRef),
    "profile_ref": of(SemanticRef),
    "issued_by": of(SemanticRef),
    "dependencies": of(DerivedIntentDependency),
}


@dataclass(frozen=True)
class ReuseAssessment(Record):
    """The outcome of one reuse decision, with the comparison that produced it.

    ``semantic_equal``, ``mapping_equal`` and ``profile_changed`` are recorded next to the verdict
    so the verdict can be audited: ``__post_init__`` refuses any combination where the verdict
    claims more than the comparison shows. An assessment that merely stored a verdict would be a
    place for a wrong answer to live.
    """

    assessment_id: str
    passport_ref: SemanticRef
    verdict: str
    recompute_scope: str
    freshness: BriefFreshnessVector
    semantic_equal: bool = False
    mapping_equal: bool = False
    profile_changed: bool = False
    delta_testified: bool = False
    invalidated_paths: tuple[str, ...] = ()
    preserved_paths: tuple[str, ...] = ()
    stale_dimensions: tuple[str, ...] = ()
    unknown_dimensions: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "assessment_id", require_identifier(self.assessment_id, "assessment_id"))
        object.__setattr__(self, "passport_ref", SemanticRef.coerce(self.passport_ref, "passport_ref"))
        verdict = ReuseVerdict.parse(self.verdict, "verdict")
        object.__setattr__(self, "verdict", verdict.value)
        scope = RecomputeScope.parse(self.recompute_scope, "recompute_scope")
        object.__setattr__(self, "recompute_scope", scope.value)
        if not isinstance(self.freshness, BriefFreshnessVector):
            raise SchemaValidationError("reuse assessment needs the BriefFreshnessVector it decided from")
        for name in ("semantic_equal", "mapping_equal", "profile_changed", "delta_testified"):
            if not isinstance(getattr(self, name), bool):
                raise SchemaValidationError(f"{name} must be a boolean")
        object.__setattr__(
            self,
            "invalidated_paths",
            _paths(self.invalidated_paths, "invalidated_paths"),
        )
        object.__setattr__(
            self,
            "preserved_paths",
            _paths(self.preserved_paths, "preserved_paths"),
        )
        clash = sorted(set(self.invalidated_paths) & set(self.preserved_paths))
        if clash:
            raise SchemaValidationError(
                f"assessment {self.assessment_id} both preserves and invalidates {clash}; one of the "
                "two is lying about the rework"
            )
        stale = _dimensions(self.stale_dimensions, "stale_dimensions")
        unknown = _dimensions(self.unknown_dimensions, "unknown_dimensions")
        if set(stale) != set(self.freshness.non_current_dimensions):
            raise SchemaValidationError(
                f"assessment {self.assessment_id} reports stale axes {list(stale)} where its vector "
                f"says {list(self.freshness.non_current_dimensions)}; a reuse verdict is only as good "
                "as the comparison it repeats honestly"
            )
        if set(unknown) != set(self.freshness.unknown_dimensions):
            raise SchemaValidationError(
                f"assessment {self.assessment_id} reports unverified axes {list(unknown)} where its "
                f"vector says {list(self.freshness.unknown_dimensions)}"
            )
        object.__setattr__(self, "stale_dimensions", stale)
        object.__setattr__(self, "unknown_dimensions", unknown)
        reasons = tuple(
            sorted({require_text(item, "reasons[]", maximum=512) for item in (self.reasons or ())})
        )
        if not reasons:
            raise SchemaValidationError(
                f"assessment {self.assessment_id} carries no reason; a reuse decision nobody can "
                "explain is a cache that has started making policy"
            )
        object.__setattr__(self, "reasons", reasons)
        _check_verdict(verdict, scope, self)
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def verdict_enum(self) -> ReuseVerdict:
        return ReuseVerdict.parse(self.verdict)

    @property
    def scope_enum(self) -> RecomputeScope:
        return RecomputeScope.parse(self.recompute_scope)

    @property
    def reuses_semantics(self) -> bool:
        return self.verdict_enum.reuses_semantics

    @property
    def rebuilds(self) -> tuple[str, ...]:
        """What has to be redone, as semantic paths or one blunt whole-artifact marker."""

        if self.scope_enum is RecomputeScope.ARTIFACT:
            return ("*",)
        if self.scope_enum is RecomputeScope.PATHS:
            return self.invalidated_paths
        return ()

    def summary(self) -> str:
        return (
            f"{self.verdict} ({self.recompute_scope}) — "
            f"{len(self.invalidated_paths)} path(s) re-derived, "
            f"{len(self.preserved_paths)} preserved; {'; '.join(self.reasons)}"
        )


ReuseAssessment.NESTED = {"passport_ref": of(SemanticRef), "freshness": of(BriefFreshnessVector)}


def passport_for(
    fingerprint: SemanticIntentFingerprint | ConstraintFingerprint,
    *,
    passport_id: str,
    brief_ref: SemanticRef,
    revision_ref: SemanticRef,
    dependencies: Iterable[DerivedIntentDependency],
    subject_kind: str = DerivedArtifactKind.CONTRACT_SET.value,
    mapping_digest: str | None = None,
    issued_by: SemanticRef | None = None,
    rationale: str | None = None,
) -> ReusePassport:
    """Build a passport from a fingerprint, so its digests are the ones actually compared.

    Constructed from the fingerprint rather than by hand because the two must agree exactly: a
    passport whose semantic digest was typed in by someone reading a log line would reuse work
    that was never done.
    """

    if isinstance(fingerprint, SemanticIntentFingerprint):
        subject_ref, form_digest = fingerprint.model_ref, None
    elif isinstance(fingerprint, ConstraintFingerprint):
        subject_ref, form_digest = fingerprint.bundle_ref, fingerprint.form_digest
    else:
        raise SchemaValidationError(
            "passport_for expects a SemanticIntentFingerprint or a ConstraintFingerprint"
        )
    return ReusePassport(
        passport_id=passport_id,
        subject_ref=subject_ref,
        subject_kind=subject_kind,
        brief_ref=brief_ref,
        revision_ref=revision_ref,
        profile_ref=fingerprint.profile_ref,
        semantic_digest=fingerprint.semantic_digest,
        form_digest=form_digest,
        mapping_digest=mapping_digest,
        dependencies=tuple(dependencies),
        issued_by=issued_by,
        rationale=rationale,
        contract_version=CONTRACT_VERSION,
    )


def evaluate_reuse(
    passport: ReusePassport,
    *,
    assessment_id: str,
    vector_id: str,
    semantic_digest: str,
    profile_ref: SemanticRef,
    form_digest: str | None = None,
    mapping_digest: str | None = None,
    upstream: Mapping[str, Mapping[str, Any]],
    revision_ordinal: int | None = None,
    delta: IntentDelta | None = None,
) -> ReuseAssessment:
    """Decide what may be carried over, recomputing freshness from observed state.

    The order of the branches is the safety order, not the cheap order. Profile mismatch is
    checked before digests because a different profile changes what equality means. Unverified
    inputs are checked before staleness because a missing check cannot support any claim, and a
    source-only difference is only allowed to preserve reuse when a delta testifies that nothing
    correctness-relevant moved.
    """

    if not isinstance(passport, ReusePassport):
        raise SchemaValidationError("evaluate_reuse expects a ReusePassport")
    expected = require_digest(semantic_digest, "semantic_digest")
    profile_ref = SemanticRef.coerce(profile_ref, "profile_ref")
    vector = passport.freshness_vector(
        vector_id=vector_id, upstream=upstream, revision_ordinal=revision_ordinal
    )
    if delta is not None and not isinstance(delta, IntentDelta):
        raise SchemaValidationError("evaluate_reuse delta must be a IntentDelta")
    stale = tuple(vector.non_current_dimensions)
    unknown = tuple(vector.unknown_dimensions)
    profile_changed = profile_ref.text != passport.profile_ref.text
    semantic_equal = (
        expected == passport.semantic_digest
        and form_digest == passport.form_digest
    )
    mapping_equal = mapping_digest == passport.mapping_digest

    if profile_changed:
        verdict, scope = ReuseVerdict.RECOMPILE, RecomputeScope.ARTIFACT
        reasons = (
            f"computed under equivalence profile {profile_ref.text}, this passport under "
            f"{passport.profile_ref.text}; digests from different profiles are not comparable",
        )
    elif unknown:
        verdict, scope = ReuseVerdict.REFUSE_UNVERIFIED, RecomputeScope.ARTIFACT
        reasons = (
            f"{list(unknown)} could not be checked against current state, and an unchecked input "
            "is not a surviving one",
        )
    elif vector.semantic_stale:
        verdict = ReuseVerdict.RECOMPILE
        whole = requires_whole(passport, vector)
        scope = RecomputeScope.ARTIFACT if whole else RecomputeScope.PATHS
        reasons = (
            f"semantic axes {list(vector.stale_dimensions)} no longer match the inputs this "
            "passport was compiled from"
            + (" through a dependency that invalidates the whole artifact" if whole else ""),
        )
    elif not semantic_equal:
        if delta is not None and not delta.correctness_relevant:
            verdict = ReuseVerdict.REUSE_EQUIVALENT
            scope = (
                RecomputeScope.MAPPING
                if (not mapping_equal or vector.mapping_only_stale)
                else RecomputeScope.NONE
            )
            reasons = (
                "the digest moved but an admitted delta reports nothing correctness-relevant "
                "changed, so this is a re-statement rather than a new requirement",
            )
        else:
            verdict, scope = ReuseVerdict.RECOMPILE, RecomputeScope.ARTIFACT
            reasons = (
                "semantics differ and no admitted delta testifies the change is presentation-only; "
                "an untestified rewording is the shape a stale requirement reuses through",
            )
    elif not mapping_equal or vector.mapping_only_stale:
        verdict, scope = ReuseVerdict.REUSE_SEMANTICS_ONLY, RecomputeScope.MAPPING
        reasons = (
            "the requirements are unchanged; only carriage to a provider has to be redone",
        )
    else:
        verdict, scope = ReuseVerdict.REUSE, RecomputeScope.NONE
        reasons = ("all inputs verified current and every compared digest equal",)

    invalidated, preserved = _rework(passport, vector, scope)
    return ReuseAssessment(
        assessment_id=assessment_id,
        passport_ref=passport.passport_ref,
        verdict=verdict.value,
        recompute_scope=scope.value,
        freshness=vector,
        semantic_equal=semantic_equal,
        mapping_equal=mapping_equal,
        profile_changed=profile_changed,
        delta_testified=delta is not None and not delta.correctness_relevant,
        invalidated_paths=invalidated,
        preserved_paths=preserved,
        stale_dimensions=stale,
        unknown_dimensions=unknown,
        reasons=reasons,
        contract_version=CONTRACT_VERSION,
    )


def require_reusable(assessment: ReuseAssessment, *, action: str) -> ReuseAssessment:
    """Refuse to carry a derivation over unless its verdict says the requirements hold."""

    if not isinstance(assessment, ReuseAssessment):
        raise SchemaValidationError("require_reusable expects a ReuseAssessment")
    if not assessment.reuses_semantics:
        raise StaleSemanticError(
            f"cannot {action}: reuse verdict is {assessment.verdict} ({assessment.recompute_scope}) "
            f"— {'; '.join(assessment.reasons)}"
        )
    return assessment


def requires_whole(passport: ReusePassport, vector: BriefFreshnessVector) -> bool:
    """Whether a non-current input reaches every part of the derived artifact."""

    moved = set(vector.non_current_dimensions)
    return any(not item.partial and item.dimension in moved for item in passport.dependencies)


def _rework(
    passport: ReusePassport,
    vector: BriefFreshnessVector,
    scope: RecomputeScope,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Split paths into rebuild and carry-over, honouring declared partial invalidation."""

    if scope is RecomputeScope.NONE or scope is RecomputeScope.MAPPING:
        return (), passport.semantic_paths
    if scope is RecomputeScope.ARTIFACT:
        return passport.semantic_paths, ()
    moved = set(vector.non_current_dimensions)
    rebuild: set[str] = set()
    for item in passport.dependencies:
        if item.dimension in moved and item.scope is DerivedScope.SEMANTICS:
            rebuild.update(item.affected_paths)
    return tuple(sorted(rebuild)), tuple(sorted(set(passport.semantic_paths) - rebuild))


def _check_verdict(
    verdict: ReuseVerdict,
    scope: RecomputeScope,
    assessment: ReuseAssessment,
) -> None:
    owner = assessment.assessment_id
    vector = assessment.freshness
    allowed = {
        ReuseVerdict.REUSE: {RecomputeScope.NONE},
        ReuseVerdict.REUSE_EQUIVALENT: {RecomputeScope.NONE, RecomputeScope.MAPPING},
        ReuseVerdict.REUSE_SEMANTICS_ONLY: {RecomputeScope.MAPPING},
        ReuseVerdict.RECOMPILE: {RecomputeScope.PATHS, RecomputeScope.ARTIFACT},
        ReuseVerdict.REFUSE_UNVERIFIED: {RecomputeScope.ARTIFACT},
    }[verdict]
    if scope not in allowed:
        raise SchemaValidationError(
            f"assessment {owner} pairs {verdict.value} with {scope.value} recompute scope, which "
            f"is not one of {sorted(item.value for item in allowed)}"
        )
    if verdict.reuses_semantics:
        if vector.semantic_stale:
            raise SchemaValidationError(
                f"assessment {owner} carries semantics over while a semantic axis is non-current"
            )
        if verdict is ReuseVerdict.REUSE and not vector.is_current:
            raise SchemaValidationError(
                f"assessment {owner} says REUSE but its vector is {vector.worst_state.value}"
            )
        if verdict is ReuseVerdict.REUSE_SEMANTICS_ONLY and not vector.mapping_only_stale:
            raise SchemaValidationError(
                f"assessment {owner} limits itself to carriage but nothing carriage-related moved"
            )
    if verdict is ReuseVerdict.REUSE_EQUIVALENT and not assessment.delta_testified:
        raise SchemaValidationError(
            f"assessment {owner} calls a moving digest equivalent with no admitted delta to say so; "
            "§18 allows reuse on testimony, not on a resemblance"
        )
    if verdict in {ReuseVerdict.REUSE, ReuseVerdict.REUSE_SEMANTICS_ONLY} and not assessment.semantic_equal:
        raise SchemaValidationError(
            f"assessment {owner} carries semantics over from a digest that is not equal"
        )
    if verdict is ReuseVerdict.REFUSE_UNVERIFIED and not vector.unknown_dimensions:
        raise SchemaValidationError(
            f"assessment {owner} refuses over unverified inputs that its vector reports as checked"
        )
    if (
        verdict is ReuseVerdict.RECOMPILE
        and assessment.semantic_equal
        and not vector.semantic_stale
        and not assessment.profile_changed
    ):
        raise SchemaValidationError(
            f"assessment {owner} recompiles from equal digests with no semantic axis moved and no "
            "profile change; that is rework justified by nothing"
        )


def _paths(values: Any, field_name: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if not isinstance(values, (list, tuple)):
        raise SchemaValidationError(f"{field_name} must be a list of semantic paths")
    out = tuple(sorted({require_semantic_path(item, f"{field_name}[]") for item in values}))
    if len(out) > MAX_PATHS_PER_SLICE:
        raise SchemaValidationError(f"{field_name} exceeds {MAX_PATHS_PER_SLICE} paths")
    return out


def _dimensions(values: Any, field_name: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        raise SchemaValidationError(f"{field_name} must be a list of dimension labels")
    return tuple(sorted({FreshnessDimension.parse(item, f"{field_name}[]").value for item in values}))
