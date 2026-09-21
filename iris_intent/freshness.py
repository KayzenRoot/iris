"""Semantic freshness for derived M03 artifacts (F-M03-04, §18.38, §18.44).

Everything M03 compiles is a derivation: a normal form follows from a bundle version, a
contract set from a model and a policy, an execution bundle from a provider capability
observation. Between two runs any of those inputs can move, and the failure worth engineering
against is not the move itself — it is a downstream artifact still being treated as current
truth afterwards. §18.38 names that failure, and §18.44 names the tempting substitute:
recency. "Regenerated last week" sounds like evidence and is not, because a re-run over
unchanged inputs proves nothing about the inputs, and a two-minute-old compilation of a
superseded revision proves less than nothing at all.

So freshness here is decided by comparison and never by clock. A dependency records what it was
derived *against* — a digest, a version, a bound on the governed revision sequence — and a
signal records what is present *now* together with which comparison was made between the two.
The state is read off the evidence, not declared next to it: no record in this module has a
field where a caller may write ``CURRENT``. A dependency with nothing comparable to check is
reported ``UNKNOWN``, and ``UNKNOWN`` blocks, because the kernel keeps no state meaning
"probably fine".

The second half of the design is proportionality. §18 asks that a stale dependency invalidate
*only the affected derived semantics where possible*, so each dependency declares which paths it
feeds and which it does not, and whether its failure reaches the requirement or only its
carriage to a provider. Collapsing those two is what makes provider swaps expensive enough that
teams skip revalidation; keeping them apart is what turns §15's "provider changes do not
invalidate provider-neutral semantics" from a hope into a checked property.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .base import Labeled, Record, of
from .errors import SchemaValidationError, StaleSemanticError
from .identity import RefKind, SemanticRef, require_bound_ref
from .limits import (
    MAX_DEPENDENCIES_PER_ARTIFACT,
    MAX_FRESHNESS_SIGNALS,
    MAX_PATHS_PER_SLICE,
)
from .sources import bounded_metadata
from .versions import (
    CONTRACT_VERSION,
    require_contract_version,
    require_digest,
    require_identifier,
    require_semantic_path,
    require_text,
    require_version_text,
)

__all__ = [
    "BriefFreshnessVector",
    "DerivedArtifactKind",
    "DerivedIntentDependency",
    "DerivedScope",
    "FreshnessBasis",
    "FreshnessDimension",
    "FreshnessEvidence",
    "FreshnessSignal",
    "FreshnessState",
    "REJECTED_FRESHNESS_BASES",
    "affected_dependency_ids",
    "affected_paths",
    "assess_freshness",
    "require_fresh",
    "require_revision_ordinal",
]


class DerivedScope(Labeled):
    """How far a staleness verdict reaches.

    ``SEMANTICS`` means what the work has to satisfy may have changed, so the derivation has to
    be redone. ``MAPPING`` means only the provider-facing carriage of an unchanged requirement
    moved, so the requirement survives and the translation does not.
    """

    SEMANTICS = "SEMANTICS"
    MAPPING = "MAPPING"

    @property
    def blocks_semantic_reuse(self) -> bool:
        return self is DerivedScope.SEMANTICS


class FreshnessDimension(Labeled):
    """The axis a staleness claim is about.

    Declared rather than inferred, because inference here silently widens: "the registry moved"
    and "the brief was superseded" have almost opposite consequences, and a kernel that read
    both as "a dependency changed" would end up recompiling everything or nothing, whichever
    was cheaper to code.
    """

    SOURCE_REVISION = "SOURCE_REVISION"
    SEMANTIC_MODEL = "SEMANTIC_MODEL"
    CONSTRAINT_BUNDLE = "CONSTRAINT_BUNDLE"
    NORMAL_FORM = "NORMAL_FORM"
    AMBIGUITY_STATE = "AMBIGUITY_STATE"
    AUTHORITY_POLICY = "AUTHORITY_POLICY"
    OVERRIDE_LEASE = "OVERRIDE_LEASE"
    POLICY_VERSION = "POLICY_VERSION"
    EQUIVALENCE_PROFILE = "EQUIVALENCE_PROFILE"
    PROVIDER_CAPABILITY = "PROVIDER_CAPABILITY"
    PROVIDER_TRANSLATION = "PROVIDER_TRANSLATION"
    UPSTREAM_ARTIFACT = "UPSTREAM_ARTIFACT"

    @property
    def staleness_scope(self) -> DerivedScope:
        return _DIMENSION_SCOPES[self]


#: Which dimensions move the requirement and which only move its carriage. The two provider
#: axes are the whole of the mapping half because nothing else in M03 is provider-facing.
_DIMENSION_SCOPES: Mapping[FreshnessDimension, DerivedScope] = {
    FreshnessDimension.SOURCE_REVISION: DerivedScope.SEMANTICS,
    FreshnessDimension.SEMANTIC_MODEL: DerivedScope.SEMANTICS,
    FreshnessDimension.CONSTRAINT_BUNDLE: DerivedScope.SEMANTICS,
    FreshnessDimension.NORMAL_FORM: DerivedScope.SEMANTICS,
    FreshnessDimension.AMBIGUITY_STATE: DerivedScope.SEMANTICS,
    FreshnessDimension.AUTHORITY_POLICY: DerivedScope.SEMANTICS,
    FreshnessDimension.OVERRIDE_LEASE: DerivedScope.SEMANTICS,
    FreshnessDimension.POLICY_VERSION: DerivedScope.SEMANTICS,
    FreshnessDimension.EQUIVALENCE_PROFILE: DerivedScope.SEMANTICS,
    FreshnessDimension.UPSTREAM_ARTIFACT: DerivedScope.SEMANTICS,
    FreshnessDimension.PROVIDER_CAPABILITY: DerivedScope.MAPPING,
    FreshnessDimension.PROVIDER_TRANSLATION: DerivedScope.MAPPING,
}


class DerivedArtifactKind(Labeled):
    """What kind of derived object a dependency hangs off.

    Declared so a dependency set can be filtered without opening every artifact: freshness
    checks run far more often than compilations, and reading a contract set to find out whether
    the contract set is stale would be a poor design.
    """

    NORMAL_FORM = "NORMAL_FORM"
    SEMANTIC_SLICE = "SEMANTIC_SLICE"
    FIDELITY_SPEC = "FIDELITY_SPEC"
    CONTRACT_SET = "CONTRACT_SET"
    QUALITY_OBLIGATIONS = "QUALITY_OBLIGATIONS"
    EXECUTION_BUNDLE = "EXECUTION_BUNDLE"
    EXPLANATION = "EXPLANATION"
    READINESS_REPORT = "READINESS_REPORT"


class FreshnessBasis(Labeled):
    """What a dependency can be compared on.

    There is deliberately no timestamp member, and :data:`REJECTED_FRESHNESS_BASES` names the
    words a caller might reach for so the refusal says what was attempted instead of reporting
    an unrecognised enum value (§18.44).
    """

    DIGEST = "DIGEST"
    VERSION = "VERSION"
    REVISION_LEASE = "REVISION_LEASE"
    PRESENCE = "PRESENCE"


REJECTED_FRESHNESS_BASES = frozenset(
    {"TIMESTAMP", "WALL_CLOCK", "AGE", "RECENCY", "LAST_SEEN", "UPDATED_AT", "CREATED_AT", "MODIFIED_AT"}
)


class FreshnessEvidence(Labeled):
    """The comparison that was made and what it came to.

    Evidence carries the verdict and :attr:`state` is read off it. The split matters: the
    inverted design — a ``state`` field the caller fills in — is how a freshness report ends up
    asserting currency it never checked.
    """

    DIGEST_MATCH = "DIGEST_MATCH"
    DIGEST_MISMATCH = "DIGEST_MISMATCH"
    VERSION_MATCH = "VERSION_MATCH"
    VERSION_MISMATCH = "VERSION_MISMATCH"
    LEASE_CURRENT = "LEASE_CURRENT"
    LEASE_EXCEEDED = "LEASE_EXCEEDED"
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    UNAVAILABLE = "UNAVAILABLE"

    @property
    def basis(self) -> FreshnessBasis | None:
        """Which comparison produced this evidence, or ``None`` when none could be run.

        ``UNAVAILABLE`` having no basis is the point: it is the one report that states the
        check did not happen, and pretending it belongs to a basis would hide that.
        """

        return _EVIDENCE_BASES[self]

    @property
    def state(self) -> "FreshnessState":
        return _EVIDENCE_STATES[self]

    @property
    def decisive(self) -> bool:
        """Whether this evidence compared anything.

        ``UNAVAILABLE`` is the only non-decisive member, and it is the one a caller under
        pressure will try to read as harmless. It is not: it says the check could not be run.
        """

        return self is not FreshnessEvidence.UNAVAILABLE


_EVIDENCE_BASES: Mapping[FreshnessEvidence, FreshnessBasis | None] = {
    FreshnessEvidence.DIGEST_MATCH: FreshnessBasis.DIGEST,
    FreshnessEvidence.DIGEST_MISMATCH: FreshnessBasis.DIGEST,
    FreshnessEvidence.VERSION_MATCH: FreshnessBasis.VERSION,
    FreshnessEvidence.VERSION_MISMATCH: FreshnessBasis.VERSION,
    FreshnessEvidence.LEASE_CURRENT: FreshnessBasis.REVISION_LEASE,
    FreshnessEvidence.LEASE_EXCEEDED: FreshnessBasis.REVISION_LEASE,
    FreshnessEvidence.PRESENT: FreshnessBasis.PRESENCE,
    FreshnessEvidence.ABSENT: FreshnessBasis.PRESENCE,
    FreshnessEvidence.UNAVAILABLE: None,
}


class FreshnessState(Labeled):
    """The outcome of a freshness comparison.

    ``EXPIRED`` stays separate from ``STALE`` because the remedies differ: a stale dependency
    needs rechecking against current inputs, an expired lease needs a governance decision first.
    ``MISSING`` is a dependency whose upstream is gone, which is not the same situation as one
    whose upstream moved.
    """

    CURRENT = "CURRENT"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"

    @property
    def is_current(self) -> bool:
        return self is FreshnessState.CURRENT

    @property
    def blocks_reuse(self) -> bool:
        return self is not FreshnessState.CURRENT

    @property
    def rank(self) -> int:
        """Severity order, worst last. See :class:`ConstraintPolarity.strictness`.

        Ordering only: a rank is a comparison within one vector, never a measure of how much
        authority an artifact has or how badly it failed.
        """

        return _STATE_RANKS[self]


_STATE_RANKS: Mapping[FreshnessState, int] = {
    FreshnessState.CURRENT: 0,
    FreshnessState.STALE: 1,
    FreshnessState.EXPIRED: 2,
    FreshnessState.MISSING: 3,
    FreshnessState.UNKNOWN: 4,
}

_EVIDENCE_STATES: Mapping[FreshnessEvidence, FreshnessState] = {
    FreshnessEvidence.DIGEST_MATCH: FreshnessState.CURRENT,
    FreshnessEvidence.DIGEST_MISMATCH: FreshnessState.STALE,
    FreshnessEvidence.VERSION_MATCH: FreshnessState.CURRENT,
    FreshnessEvidence.VERSION_MISMATCH: FreshnessState.STALE,
    FreshnessEvidence.LEASE_CURRENT: FreshnessState.CURRENT,
    FreshnessEvidence.LEASE_EXCEEDED: FreshnessState.EXPIRED,
    FreshnessEvidence.PRESENT: FreshnessState.CURRENT,
    FreshnessEvidence.ABSENT: FreshnessState.MISSING,
    FreshnessEvidence.UNAVAILABLE: FreshnessState.UNKNOWN,
}


def require_revision_ordinal(value: Any, field_name: str) -> int:
    """Validate a position in the governed revision sequence.

    Ordinals, not dates: the sequence is issued by M02's revision admission, so "the lease ran
    out" is a claim about governed order rather than about wall-clock drift between two machines
    that never agreed on a time to begin with.
    """

    if isinstance(value, str):
        if not value.strip().lstrip("-").isdigit():
            raise SchemaValidationError(f"{field_name} must be a revision ordinal, got {value!r}")
        value = int(value.strip())
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchemaValidationError(f"{field_name} must be a revision ordinal, got {value!r}")
    if value < 0:
        raise SchemaValidationError(f"{field_name} must be a non-negative revision ordinal")
    return value


@dataclass(frozen=True)
class FreshnessSignal(Record):
    """One comparison between what a dependency was derived against and what is there now.

    ``observed_at`` exists for reporting and audit trails only. Nothing in this module reads it
    to decide anything, and :attr:`decisive_on_timestamp` states that structurally so a reviewer
    does not have to trace every call site to confirm it.
    """

    signal_id: str
    dimension: str
    evidence: str
    dependency_id: str | None = None
    expected: str | None = None
    observed: str | None = None
    subject_path: str | None = None
    observed_at: str | None = None
    notes: str | None = None
    contract_version: str = ""

    #: Presence of this attribute is the assertion §18.44 asks for: a signal never decides on time.
    decisive_on_timestamp = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "signal_id", require_identifier(self.signal_id, "signal_id"))
        dimension = FreshnessDimension.parse(self.dimension, "dimension")
        object.__setattr__(self, "dimension", dimension.value)
        evidence = FreshnessEvidence.parse(self.evidence, "evidence")
        object.__setattr__(self, "evidence", evidence.value)
        if self.dependency_id is not None:
            object.__setattr__(self, "dependency_id", require_identifier(self.dependency_id, "dependency_id"))
        if self.subject_path is not None:
            object.__setattr__(self, "subject_path", require_semantic_path(self.subject_path, "subject_path"))
        if self.observed_at is not None:
            object.__setattr__(self, "observed_at", require_text(self.observed_at, "observed_at", maximum=64))
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=1024))
        _check_operands(evidence, self.expected, self.observed, self.signal_id)
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def dimension_enum(self) -> FreshnessDimension:
        return FreshnessDimension.parse(self.dimension)

    @property
    def evidence_enum(self) -> FreshnessEvidence:
        return FreshnessEvidence.parse(self.evidence)

    @property
    def state(self) -> FreshnessState:
        """Read off the evidence, never supplied by the caller."""

        return self.evidence_enum.state

    @property
    def basis(self) -> FreshnessBasis | None:
        return self.evidence_enum.basis

    @property
    def scope(self) -> DerivedScope:
        return self.dimension_enum.staleness_scope

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "evidence": self.evidence,
            "dependency_id": self.dependency_id,
            "state": self.state.value,
        }


@dataclass(frozen=True)
class DerivedIntentDependency(Record):
    """A declared dependency of one derived artifact on one upstream input.

    ``partial`` plus ``affected_paths`` is the proportionality mechanism: a dependency feeding
    two paths of an obligation set must not invalidate the other forty when it moves. A
    dependency that genuinely cannot say which paths it feeds is allowed — but it must then say
    so by declaring ``partial=False``, which is a claim that the whole artifact hangs off it: the
    expensive reading, and one a reviewer can see.
    """

    dependency_id: str
    derived_ref: SemanticRef
    derived_kind: str
    upstream_ref: SemanticRef
    dimension: str
    invalidates: str
    match_on: tuple[str, ...] = ()
    last_known_digest: str | None = None
    last_known_version: str | None = None
    valid_through_revision: int | None = None
    partial: bool = True
    affected_paths: tuple[str, ...] = ()
    protected_paths: tuple[str, ...] = ()
    rationale: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "dependency_id", require_identifier(self.dependency_id, "dependency_id"))
        object.__setattr__(self, "derived_ref", SemanticRef.coerce(self.derived_ref, "derived_ref"))
        object.__setattr__(
            self, "derived_kind", DerivedArtifactKind.parse(self.derived_kind, "derived_kind").value
        )
        object.__setattr__(self, "upstream_ref", SemanticRef.coerce(self.upstream_ref, "upstream_ref"))
        dimension = FreshnessDimension.parse(self.dimension, "dimension")
        object.__setattr__(self, "dimension", dimension.value)
        scope = DerivedScope.parse(self.invalidates, "invalidates")
        if scope is not dimension.staleness_scope:
            raise SchemaValidationError(
                f"dependency {self.dependency_id} declares {scope.value} invalidation for "
                f"{dimension.value}, whose staleness reaches {dimension.staleness_scope.value}; agree "
                "with the dimension, or the scope of rework becomes a matter of preference"
            )
        object.__setattr__(self, "invalidates", scope.value)
        bases = _bases(self.match_on, self.dependency_id)
        object.__setattr__(self, "match_on", bases)
        if not bases:
            raise SchemaValidationError(
                f"dependency {self.dependency_id} declares no basis to check; an uncheckable "
                "dependency is a staleness claim nobody can ever settle, so it is refused"
            )
        if FreshnessBasis.DIGEST.value in bases:
            if self.last_known_digest is None:
                raise SchemaValidationError(
                    f"dependency {self.dependency_id} matches on DIGEST without recording the "
                    "digest it was derived against"
                )
            object.__setattr__(
                self, "last_known_digest", require_digest(self.last_known_digest, "last_known_digest")
            )
        if FreshnessBasis.VERSION.value in bases:
            if self.last_known_version is None:
                raise SchemaValidationError(
                    f"dependency {self.dependency_id} matches on VERSION without recording the "
                    "version it was derived against"
                )
            object.__setattr__(
                self, "last_known_version", require_version_text(self.last_known_version, "last_known_version")
            )
            if self.upstream_ref.version is None:
                raise SchemaValidationError(
                    f"dependency {self.dependency_id} compares versions but its upstream ref "
                    f"{self.upstream_ref.text} names no version namespace to compare within"
                )
        if FreshnessBasis.REVISION_LEASE.value in bases and self.valid_through_revision is None:
            raise SchemaValidationError(
                f"dependency {self.dependency_id} runs on a revision lease with no bound; an "
                "unbounded lease is authority granted forever by accident"
            )
        if self.valid_through_revision is not None:
            require_revision_ordinal(self.valid_through_revision, "valid_through_revision")
        if not isinstance(self.partial, bool):
            raise SchemaValidationError("partial must be a boolean")
        affected = _paths(self.affected_paths, "affected_paths")
        protected = _paths(self.protected_paths, "protected_paths")
        clash = sorted(set(affected) & set(protected))
        if clash:
            raise SchemaValidationError(
                f"dependency {self.dependency_id} both invalidates and protects {clash}; decide, "
                "otherwise §18's partial-invalidation rule turns order-dependent"
            )
        if self.partial and not affected:
            raise SchemaValidationError(
                f"dependency {self.dependency_id} claims partial invalidation naming no affected "
                "path; that is total invalidation under a narrower-sounding name"
            )
        if not self.partial and affected:
            raise SchemaValidationError(
                f"dependency {self.dependency_id} declares affected paths but total invalidation; "
                "the path list would read as a limit and then be ignored"
            )
        object.__setattr__(self, "affected_paths", affected)
        object.__setattr__(self, "protected_paths", protected)
        if self.rationale is not None:
            object.__setattr__(self, "rationale", require_text(self.rationale, "rationale", maximum=1024))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def dimension_enum(self) -> FreshnessDimension:
        return FreshnessDimension.parse(self.dimension)

    @property
    def scope(self) -> DerivedScope:
        return DerivedScope.parse(self.invalidates)

    @property
    def bases(self) -> tuple[FreshnessBasis, ...]:
        return tuple(FreshnessBasis.parse(item) for item in self.match_on)

    @property
    def upstream_key(self) -> str:
        """The lookup key into a caller-supplied upstream state mapping."""

        return self.upstream_ref.text

    @property
    def semantics_at_risk(self) -> bool:
        return self.scope is DerivedScope.SEMANTICS

    @property
    def rework_paths(self) -> tuple[str, ...]:
        """Paths this dependency can force a rebuild of — empty when it takes everything."""

        return self.affected_paths if self.partial else ()

    @property
    def dependency_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.FRESHNESS.value, ref_id=self.dependency_id).with_digest(self.digest())

    def identity(self) -> dict[str, Any]:
        """The comparable core, used for dependency-set digests.

        Local ids and rationale are absent because two briefs depending on the same inputs under
        different labels must present the same set — the point of the set digest is to notice
        that they can share work.
        """

        return {
            "derived": self.derived_ref.text,
            "upstream": self.upstream_ref.text,
            "dimension": self.dimension,
            "match_on": list(self.match_on),
            "last_known_digest": self.last_known_digest,
            "last_known_version": self.last_known_version,
            "valid_through_revision": self.valid_through_revision,
            "partial": self.partial,
            "affected_paths": list(self.affected_paths),
        }

    def signals(self, upstream: Mapping[str, Any], revision_ordinal: int | None = None) -> tuple[FreshnessSignal, ...]:
        """One signal per declared basis, against the state supplied now.

        A basis whose operand is missing from the upstream entry yields ``UNAVAILABLE``, which
        reads as ``UNKNOWN`` and blocks: the missing check is reported, not assumed passed.
        """

        entry = upstream.get(self.upstream_key) if isinstance(upstream, Mapping) else None
        if entry is None:
            return (
                _signal(
                    f"{self.dependency_id}-absent",
                    self.dimension,
                    FreshnessEvidence.ABSENT,
                    dependency_id=self.dependency_id,
                    notes=f"no upstream state entry for {self.upstream_key}",
                ),
            )
        if not isinstance(entry, Mapping):
            raise SchemaValidationError(
                f"upstream state for {self.upstream_key} must be a mapping of observed facts"
            )
        return tuple(_check_one(basis, self, entry, revision_ordinal) for basis in self.bases)

    def check(self, upstream: Mapping[str, Any], revision_ordinal: int | None = None) -> FreshnessSignal:
        """This dependency's worst per-basis signal — the single answer for one dependency."""

        signals = self.signals(upstream, revision_ordinal)
        return max(signals, key=lambda item: item.state.rank)


DerivedIntentDependency.NESTED = {"derived_ref": of(SemanticRef), "upstream_ref": of(SemanticRef)}


@dataclass(frozen=True)
class BriefFreshnessVector(Record):
    """The freshness position of one derived artifact at one revision.

    Every state on this record is computed from its signals, and the axes it claims to cover are
    declared separately in ``declared_dimensions``. That split is the point: a vector declaring
    ``AUTHORITY_POLICY`` with no signal for it reports that axis ``UNKNOWN`` and blocks, instead
    of defaulting to "nothing said, so nothing moved". A silent default-to-current is the most
    common way a freshness system becomes decorative.
    """

    vector_id: str
    brief_ref: SemanticRef
    revision_ref: SemanticRef
    subject_ref: SemanticRef
    declared_dimensions: tuple[str, ...] = ()
    signals: tuple[FreshnessSignal, ...] = ()
    dependency_ids: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "vector_id", require_identifier(self.vector_id, "vector_id"))
        object.__setattr__(
            self, "brief_ref", require_bound_ref(self.brief_ref, "brief_ref", kind=RefKind.BRIEF)
        )
        object.__setattr__(
            self,
            "revision_ref",
            require_bound_ref(self.revision_ref, "revision_ref", kind=RefKind.REVISION),
        )
        object.__setattr__(self, "subject_ref", SemanticRef.coerce(self.subject_ref, "subject_ref"))
        declared = _dimensions(self.declared_dimensions)
        if not declared:
            raise SchemaValidationError(
                f"freshness vector {self.vector_id} declares no axes; a vector covering nothing "
                "reports CURRENT for everything, which is a pass slot rather than a check"
            )
        object.__setattr__(self, "declared_dimensions", declared)
        signals = tuple(
            sorted(
                (FreshnessSignal.coerce(item, "signals[]") for item in (self.signals or ())),
                key=lambda item: (item.dimension, item.dependency_id or "", item.signal_id),
            )
        )
        if len(signals) > MAX_FRESHNESS_SIGNALS:
            raise SchemaValidationError(
                f"vector {self.vector_id} carries {len(signals)} signals, above {MAX_FRESHNESS_SIGNALS}"
            )
        if len({item.signal_id for item in signals}) != len(signals):
            raise SchemaValidationError(f"vector {self.vector_id} repeats a signal id")
        declared_ids = tuple(
            sorted({require_identifier(item, "dependency_ids[]") for item in (self.dependency_ids or ())})
        )
        if len(declared_ids) > MAX_DEPENDENCIES_PER_ARTIFACT:
            raise SchemaValidationError(
                f"vector {self.vector_id} covers {len(declared_ids)} dependencies, above "
                f"{MAX_DEPENDENCIES_PER_ARTIFACT}"
            )
        orphans = sorted({item.dependency_id for item in signals if item.dependency_id} - set(declared_ids))
        if orphans:
            raise SchemaValidationError(
                f"vector {self.vector_id} carries signals for undeclared dependencies {orphans}; an "
                "observation whose dependency is not in the set cannot be traced to a derivation"
            )
        undisclosed = sorted({item.dimension for item in signals} - set(declared))
        if undisclosed:
            raise SchemaValidationError(
                f"vector {self.vector_id} signals dimensions it never declared {undisclosed}; "
                "declaring coverage afterwards would let a check decide axes nobody chose"
            )
        object.__setattr__(self, "signals", signals)
        object.__setattr__(self, "dependency_ids", declared_ids)
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    #: §18.44 stated as structure: nothing on this record is decided by time.
    decisive_on_timestamp = False

    @property
    def states(self) -> Mapping[str, str]:
        """Declared dimension → worst observed state, with unreported axes ``UNKNOWN``."""

        out: dict[str, str] = {}
        for dimension in self.declared_dimensions:
            items = [item for item in self.signals if item.dimension == dimension]
            if not items:
                out[dimension] = FreshnessState.UNKNOWN.value
                continue
            out[dimension] = max((item.state for item in items), key=lambda state: state.rank).value
        return out

    @property
    def unreported_dimensions(self) -> tuple[str, ...]:
        signalled = {item.dimension for item in self.signals}
        return tuple(sorted(set(self.declared_dimensions) - signalled))

    @property
    def worst_state(self) -> FreshnessState:
        return max(
            (FreshnessState.parse(value) for value in self.states.values()), key=lambda state: state.rank
        )

    @property
    def is_current(self) -> bool:
        return self.worst_state.is_current

    @property
    def non_current_dimensions(self) -> tuple[str, ...]:
        return tuple(
            sorted(key for key, value in self.states.items() if not FreshnessState.parse(value).is_current)
        )

    @property
    def stale_dimensions(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                key
                for key, value in self.states.items()
                if FreshnessState.parse(value) is FreshnessState.STALE
            )
        )

    @property
    def unknown_dimensions(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                key
                for key, value in self.states.items()
                if FreshnessState.parse(value) in {FreshnessState.UNKNOWN, FreshnessState.MISSING}
            )
        )

    @property
    def semantic_stale(self) -> bool:
        """Whether any axis that reaches the requirement itself failed to hold."""

        return any(
            not FreshnessState.parse(value).is_current
            and FreshnessDimension.parse(key).staleness_scope is DerivedScope.SEMANTICS
            for key, value in self.states.items()
        )

    @property
    def mapping_only_stale(self) -> bool:
        return bool(self.non_current_dimensions) and not self.semantic_stale

    @property
    def semantics_hold(self) -> bool:
        """The §15 claim: requirements unchanged even where carriage is not."""

        return not self.semantic_stale

    @property
    def decisive_evidence(self) -> tuple[str, ...]:
        return tuple(sorted({item.evidence for item in self.signals if item.evidence_enum.decisive}))

    @property
    def timestamp_only(self) -> bool:
        """Whether this vector is being sold on recency.

        Always true when nothing compared anything, and no vector can be built that decides on
        time — reported so a readiness check can assert the property instead of trusting types.
        """

        return not self.decisive_evidence

    def state_for(self, dimension: str) -> str:
        wanted = FreshnessDimension.parse(dimension, "dimension").value
        states = self.states
        if wanted not in states:
            raise SchemaValidationError(
                f"vector {self.vector_id} never declared {wanted}, so it cannot answer for it"
            )
        return states[wanted]

    def signals_for(self, dimension: str) -> tuple[FreshnessSignal, ...]:
        wanted = FreshnessDimension.parse(dimension, "dimension").value
        return tuple(item for item in self.signals if item.dimension == wanted)

    def reasons(self) -> tuple[str, ...]:
        out: list[str] = []
        for item in self.signals:
            if item.state.is_current:
                continue
            out.append(
                f"{item.dimension} is {item.state.value} on {item.evidence.lower()}"
                + (f" via {item.dependency_id}" if item.dependency_id else "")
            )
        for dimension in self.unreported_dimensions:
            out.append(f"{dimension} was declared and never checked, so it is UNKNOWN")
        return tuple(sorted(out))

    @property
    def vector_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.FRESHNESS.value, ref_id=self.vector_id).with_digest(self.digest())

    def covers(self, dependency_id: str) -> bool:
        return require_identifier(dependency_id, "dependency_id") in set(self.dependency_ids)

    def equivalent_to(self, other: "BriefFreshnessVector") -> bool:
        """Same positions on the same axes, regardless of which run produced it."""

        if not isinstance(other, BriefFreshnessVector):
            raise SchemaValidationError("freshness equivalence needs another vector")
        return self.states == other.states and self.dependency_ids == other.dependency_ids


BriefFreshnessVector.NESTED = {
    "brief_ref": of(SemanticRef),
    "revision_ref": of(SemanticRef),
    "subject_ref": of(SemanticRef),
    "signals": of(FreshnessSignal),
}


def assess_freshness(
    *,
    vector_id: str,
    brief_ref: SemanticRef,
    revision_ref: SemanticRef,
    subject_ref: SemanticRef,
    dependencies: Iterable[DerivedIntentDependency],
    upstream: Mapping[str, Mapping[str, Any]],
    revision_ordinal: int | None = None,
    declared_dimensions: Iterable[str] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> BriefFreshnessVector:
    """Check a dependency set against the state the caller can actually observe.

    ``upstream`` is keyed by :attr:`DerivedIntentDependency.upstream_key` and carries the
    observed ``digest`` and/or ``version`` for each input. It is passed in rather than looked up
    here because observing it is not M03's job; refusing a derivation whose inputs moved, and
    saying which one did, is.
    """

    items = tuple(
        sorted(
            (DerivedIntentDependency.coerce(item, "dependencies[]") for item in (dependencies or ())),
            key=lambda item: item.dependency_id,
        )
    )
    if not items:
        raise SchemaValidationError(
            "assess_freshness needs at least one dependency; a derived artifact with no declared "
            "inputs is not fresh, it is unaccounted for"
        )
    if len({item.dependency_id for item in items}) != len(items):
        raise SchemaValidationError("dependency set repeats a dependency id")
    if not isinstance(upstream, Mapping):
        raise SchemaValidationError("upstream state must be a mapping keyed by upstream ref text")
    if declared_dimensions is None:
        dimensions = tuple(item.dimension for item in items)
    else:
        dimensions = _dimensions(declared_dimensions)
    signals: list[FreshnessSignal] = []
    for item in items:
        signals.extend(item.signals(upstream, revision_ordinal))
    return BriefFreshnessVector(
        vector_id=vector_id,
        brief_ref=brief_ref,
        revision_ref=revision_ref,
        subject_ref=subject_ref,
        declared_dimensions=dimensions,
        signals=tuple(signals),
        dependency_ids=tuple(sorted(item.dependency_id for item in items)),
        metadata=dict(metadata or {}),
        contract_version=CONTRACT_VERSION,
    )


def affected_dependency_ids(
    dependencies: Iterable[DerivedIntentDependency],
    vector: BriefFreshnessVector,
) -> tuple[str, ...]:
    """Which declared inputs the vector says have moved.

    A non-current axis includes ``UNKNOWN``, so an unchecked dependency counts as affected: an
    unverified input is not a surviving one, and reuse that assumed otherwise would be reusing
    on a guess.
    """

    moved = set(vector.non_current_dimensions)
    items = (DerivedIntentDependency.coerce(dependency, "dependencies[]") for dependency in (dependencies or ()))
    return tuple(sorted({item.dependency_id for item in items if item.dimension in moved}))


def affected_paths(
    dependencies: Iterable[DerivedIntentDependency],
    vector: BriefFreshnessVector,
) -> Mapping[str, tuple[str, ...]]:
    """Split the rework by scope, so only the affected part is rebuilt.

    Keys are :class:`DerivedScope` values. A dependency declaring total invalidation contributes
    no paths here — the caller learns that from :func:`requires_whole_artifact` rather than from
    an empty tuple that could equally mean "nothing affected".
    """

    moved = set(vector.non_current_dimensions)
    out: dict[str, set[str]] = {scope.value: set() for scope in DerivedScope}
    for item in (DerivedIntentDependency.coerce(dependency, "dependencies[]") for dependency in (dependencies or ())):
        if item.dimension not in moved or not item.partial:
            continue
        out[item.invalidates].update(item.affected_paths)
    return {key: tuple(sorted(value)) for key, value in sorted(out.items())}


def requires_whole_artifact(
    dependencies: Iterable[DerivedIntentDependency],
    vector: BriefFreshnessVector,
) -> bool:
    """Whether some non-current dependency takes the whole derived artifact with it."""

    moved = set(vector.non_current_dimensions)
    items = (DerivedIntentDependency.coerce(dependency, "dependencies[]") for dependency in (dependencies or ()))
    return any(not item.partial and item.dimension in moved for item in items)


def require_fresh(
    vector: BriefFreshnessVector,
    *,
    action: str,
    allow_mapping_stale: bool = False,
) -> BriefFreshnessVector:
    """Gate an operation on freshness, failing closed.

    Mapping-only staleness is permitted only when the caller says out loud that it is doing
    mapping work. The default is the strict reading because a forgotten flag on the permissive
    side silently ships a stale requirement, while a forgotten flag on the strict side merely
    recompiles something whose carriage moved.
    """

    if not isinstance(vector, BriefFreshnessVector):
        raise SchemaValidationError("require_fresh expects a BriefFreshnessVector")
    label = require_text(action, "action", maximum=64)
    if vector.unknown_dimensions:
        raise StaleSemanticError(
            f"cannot {label}: {list(vector.unknown_dimensions)} could not be checked, and an "
            "unverified dependency is not a current one"
        )
    if vector.semantic_stale:
        raise StaleSemanticError(
            f"cannot {label}: semantic axes {list(vector.stale_dimensions)} no longer match what "
            "the artifact was derived against"
        )
    if vector.mapping_only_stale and not allow_mapping_stale:
        raise StaleSemanticError(
            f"cannot {label}: only carriage is stale ({list(vector.non_current_dimensions)}), and "
            "mapping work must be asked for with allow_mapping_stale so it cannot be mistaken for "
            "a semantic re-derivation"
        )
    return vector


def _check_one(
    basis: FreshnessBasis,
    dependency: DerivedIntentDependency,
    entry: Mapping[str, Any],
    revision_ordinal: int | None,
) -> FreshnessSignal:
    identifier = dependency.dependency_id
    dimension = dependency.dimension
    if basis is FreshnessBasis.PRESENCE:
        present = bool(entry.get("present", True))
        return _signal(
            f"{identifier}-presence",
            dimension,
            FreshnessEvidence.PRESENT if present else FreshnessEvidence.ABSENT,
            dependency_id=identifier,
        )
    if basis is FreshnessBasis.DIGEST:
        observed = entry.get("digest")
        expected = dependency.last_known_digest
        if observed is None or expected is None:
            return _unavailable(identifier, dimension, "digest")
        observed = require_digest(observed, "upstream digest")
        return _signal(
            f"{identifier}-digest",
            dimension,
            FreshnessEvidence.DIGEST_MATCH if expected == observed else FreshnessEvidence.DIGEST_MISMATCH,
            dependency_id=identifier,
            expected=expected,
            observed=observed,
        )
    if basis is FreshnessBasis.VERSION:
        observed = entry.get("version")
        expected = dependency.last_known_version
        if observed is None or expected is None:
            return _unavailable(identifier, dimension, "version")
        observed = require_version_text(observed, "upstream version")
        return _signal(
            f"{identifier}-version",
            dimension,
            FreshnessEvidence.VERSION_MATCH if expected == observed else FreshnessEvidence.VERSION_MISMATCH,
            dependency_id=identifier,
            expected=expected,
            observed=observed,
        )
    bound = dependency.valid_through_revision
    if revision_ordinal is None or bound is None:
        return _unavailable(identifier, dimension, "revision lease")
    current = require_revision_ordinal(revision_ordinal, "revision_ordinal")
    return _signal(
        f"{identifier}-lease",
        dimension,
        FreshnessEvidence.LEASE_CURRENT if current <= bound else FreshnessEvidence.LEASE_EXCEEDED,
        dependency_id=identifier,
        expected=str(bound),
        observed=str(current),
    )


def _unavailable(dependency_id: str, dimension: str, what: str) -> FreshnessSignal:
    """Report a comparison that could not be run, naming which one.

    The operand goes into the id because one dependency can declare several bases and each
    unrunnable comparison is its own signal — two signals sharing an id would make the vector's
    uniqueness check collide over nothing more than a missing version string.
    """

    return _signal(
        f"{dependency_id}-unavailable-{what.replace(' ', '_').lower()}",
        dimension,
        FreshnessEvidence.UNAVAILABLE,
        dependency_id=dependency_id,
        notes=f"no {what} to compare against; reported UNKNOWN rather than assumed current",
    )


def _signal(
    signal_id: str,
    dimension: str,
    evidence: FreshnessEvidence,
    **kwargs: Any,
) -> FreshnessSignal:
    return FreshnessSignal(
        signal_id=signal_id,
        dimension=dimension,
        evidence=evidence.value,
        contract_version=CONTRACT_VERSION,
        **kwargs,
    )


def _check_operands(evidence: FreshnessEvidence, expected: Any, observed: Any, owner: str) -> None:
    if evidence is FreshnessEvidence.UNAVAILABLE:
        if expected is not None or observed is not None:
            raise SchemaValidationError(
                f"signal {owner} claims no comparable evidence while carrying operands; either "
                "there was something to check or there was not"
            )
        return
    basis = evidence.basis
    if basis is FreshnessBasis.DIGEST:
        if expected is None or observed is None:
            raise SchemaValidationError(
                f"signal {owner} reports {evidence.value} without both digests to compare"
            )
        left = require_digest(expected, "expected")
        right = require_digest(observed, "observed")
        agrees = (left == right) is (evidence is FreshnessEvidence.DIGEST_MATCH)
    elif basis is FreshnessBasis.VERSION:
        if expected is None or observed is None:
            raise SchemaValidationError(
                f"signal {owner} reports {evidence.value} without both versions to compare"
            )
        left = require_version_text(expected, "expected")
        right = require_version_text(observed, "observed")
        agrees = (left == right) is (evidence is FreshnessEvidence.VERSION_MATCH)
    elif basis is FreshnessBasis.REVISION_LEASE:
        if expected is None or observed is None:
            raise SchemaValidationError(f"signal {owner} reports a lease verdict with no bounds")
        bound = require_revision_ordinal(expected, "expected")
        current = require_revision_ordinal(observed, "observed")
        agrees = (current <= bound) is (evidence is FreshnessEvidence.LEASE_CURRENT)
    else:
        if expected is not None or observed is not None:
            raise SchemaValidationError(
                f"signal {owner} carries operands for a presence check, which compares nothing"
            )
        return
    if not agrees:
        raise SchemaValidationError(
            f"signal {owner} declares {evidence.value} and its own operands contradict it; a "
            "freshness report that disagrees with its comparisons is the one §18.44 refuses"
        )


def _bases(values: Any, owner: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        raise SchemaValidationError(f"dependency {owner} match_on must be a list of basis labels")
    out: list[str] = []
    for value in values:
        if isinstance(value, str) and value.strip().upper() in REJECTED_FRESHNESS_BASES:
            raise SchemaValidationError(
                f"dependency {owner} asks to match on {value!r}; timestamps are never sufficient "
                "proof of semantic freshness (§18.44) — declare DIGEST, VERSION, REVISION_LEASE "
                "or PRESENCE"
            )
        label = FreshnessBasis.parse(value, "match_on[]").value
        if label in out:
            raise SchemaValidationError(f"dependency {owner} match_on repeats {label}")
        out.append(label)
    return tuple(sorted(out))


def _dimensions(values: Any) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        raise SchemaValidationError("declared_dimensions must be a list of dimension labels")
    return tuple(sorted({FreshnessDimension.parse(item, "declared_dimensions[]").value for item in values}))


def _paths(values: Any, field_name: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if not isinstance(values, (list, tuple)):
        raise SchemaValidationError(f"{field_name} must be a list of semantic paths")
    out = tuple(sorted({require_semantic_path(item, f"{field_name}[]") for item in values}))
    if len(out) > MAX_PATHS_PER_SLICE:
        raise SchemaValidationError(f"{field_name} exceeds {MAX_PATHS_PER_SLICE} paths")
    return out
