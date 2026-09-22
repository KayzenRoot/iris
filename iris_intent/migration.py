"""F-M03-15 S05 versioning: the migration receipt and explicit compatibility declarations (§19-§20).

Two claims give this module its shape. The first is §19's: schema, compiler, profile and policy
versions are part of what a compilation *means*, so a change to one of them is either proven not to
move the semantics — and then it is declared, explicitly, with evidence — or it is a migration that
produces a new revision and a receipt. The second is §20's: a migration that cannot carry a mandatory
element across may be *recorded*, but it may not be admitted automatically, because the alternative
is a compiler upgrade that quietly deletes a client requirement.

Nothing here rewrites the revision it migrates from. The old record stays exactly as admitted, which
is what lets a later reader see what was lost rather than infer it from the absence of a trace. The
accounting is derived from the two revisions' fingerprints rather than taken from the caller, so the
lists of transformed and unchanged paths say something checkable, and ``require_admissible`` re-runs
that check at admission time instead of trusting the paper.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .base import Labeled, Record, of
from .briefs import BriefRevision
from .errors import (
    AdmissionRefusedError,
    AuthorityError,
    LimitExceededError,
    RefError,
    SchemaValidationError,
    StaleSemanticError,
    UnsupportedVersionError,
)
from .fingerprints import (
    DEFAULT_EQUIVALENCE_PROFILE,
    SemanticEquivalenceProfile,
    fingerprint_revision,
)
from .identity import RefKind, SemanticRef, require_bound_ref
from .intent import IntentAuthorityRef
from .limits import MAX_ENTRIES_PER_FIELD, MAX_PATHS_PER_SLICE, MAX_RATIONALE_CHARS
from .overrides import bound_paths, bound_refs
from .sources import bounded_metadata
from .versions import (
    CONTRACT_VERSION,
    SCHEMA_VERSION,
    content_digest,
    require_digest,
    require_identifier,
    require_semantic_path,
    require_text,
    require_version_text,
)

__all__ = [
    "MIGRATION_COMPILER_VERSION",
    "CompatibilityDeclaration",
    "MigrationComponentKind",
    "MigrationLoss",
    "MigrationLossKind",
    "MigrationReceipt",
    "VersionVector",
    "declare_compatible",
    "migrate_revision",
    "require_admissible",
    "require_declared",
]

MIGRATION_COMPILER_VERSION = "m03-migration-1.0"

#: The four axes §19 names as participating in compilation compatibility, in the order a reader
#: checks them. Restoration receipts share this list (§21) because "which interpretation produced
#: this" is the same question in both places, and two copies would drift.
MIGRATION_AXES = ("schema", "compiler", "profile", "policy")


class MigrationComponentKind(Labeled):
    """Which of §19's four version axes a migration moved.

    The component is one axis rather than a bag because the receipt has to say what changed the
    reading: a policy bump and a schema bump are different events with different reviewers, and a
    record that blurs them tells a reader nothing about who to ask.
    """

    SCHEMA = "SCHEMA"
    COMPILER = "COMPILER"
    PROFILE = "PROFILE"
    POLICY = "POLICY"

    @property
    def axis(self) -> str:
        """The ``VersionVector`` member this axis governs.

        The enum spells itself in capitals like every other label in the kernel and the vector
        spells its members as attribute names, so the two meet here rather than in a string
        comparison that quietly never matches.
        """

        return self.value.lower()


class MigrationLossKind(Labeled):
    """How a semantic element failed to survive a migration (§20).

    Every member is lossy; the taxonomy exists so a reviewer can tell whether the target has no
    construct for the element at all, or a weaker one. That difference changes the fix — write the
    missing construct, or re-narrow the rule — and a single ``LOST`` label would hide it.
    """

    UNREPRESENTABLE = "UNREPRESENTABLE"
    NARROWED = "NARROWED"
    FOLDED = "FOLDED"
    APPROXIMATED = "APPROXIMATED"


@dataclass(frozen=True)
class VersionVector(Record):
    """The four interpretation versions that produced one compilation (§19).

    All four are required. A partial vector is the usual way a compatibility claim survives review:
    "the schema matches" is only reassuring if the policy did not move underneath it, and the absent
    members are exactly the ones nobody thought to check.
    """

    schema: str
    compiler: str
    profile: str
    policy: str

    def __post_init__(self) -> None:
        for axis in MIGRATION_AXES:
            object.__setattr__(self, axis, require_version_text(getattr(self, axis), f"{axis} version"))

    def as_mapping(self) -> dict[str, str]:
        return {axis: getattr(self, axis) for axis in MIGRATION_AXES}

    @property
    def vector_digest(self) -> str:
        """A digest of the four versions, for comparing two vectors without listing them."""

        return content_digest(self.as_mapping())

    def moved_axes(self, other: "VersionVector") -> tuple[MigrationComponentKind, ...]:
        """Which axes differ, in a stable order.

        The comparison is per axis rather than over the whole digest on purpose: a reader needs to
        know *which* interpretation moved, and a single "the vectors differ" would force them to
        re-derive it — at which point the receipt stops being evidence.
        """

        mine, theirs = self.as_mapping(), other.as_mapping()
        return tuple(
            MigrationComponentKind.parse(axis) for axis in MIGRATION_AXES if mine[axis] != theirs[axis]
        )

    def same_as(self, other: "VersionVector") -> bool:
        return self.vector_digest == other.vector_digest

    def fingerprint_inputs(self) -> dict[str, Any]:
        return self.as_mapping()


@dataclass(frozen=True)
class MigrationLoss(Record):
    """One element the target could not carry, on the path that lost it (§20).

    ``mandatory`` is recorded rather than derived here because a loss is reported while the source is
    in hand, but ``require_admissible`` recomputes it from the source revision before anything is
    admitted, so a receipt that understated it fails at the gate instead of in review.
    """

    loss_id: str
    semantic_path: str
    element_ref: SemanticRef
    kind: str
    mandatory: bool
    detail: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "loss_id", require_identifier(self.loss_id, "loss_id"))
        object.__setattr__(self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path"))
        object.__setattr__(
            self,
            "element_ref",
            require_bound_ref(self.element_ref, "element_ref"),
        )
        kind = MigrationLossKind.parse(self.kind, "kind")
        object.__setattr__(self, "kind", kind.value)
        if not isinstance(self.mandatory, bool):
            raise SchemaValidationError("mandatory must be a boolean; a mandatory element is never 'maybe'")
        object.__setattr__(self, "detail", require_text(self.detail, "detail", maximum=MAX_RATIONALE_CHARS))

    @property
    def kind_enum(self) -> MigrationLossKind:
        return MigrationLossKind.parse(self.kind)

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "loss_id": self.loss_id,
            "path": self.semantic_path,
            "element": self.element_ref.text,
            "kind": self.kind,
            "mandatory": self.mandatory,
        }


MigrationLoss.NESTED = {"element_ref": of(SemanticRef)}


@dataclass(frozen=True)
class MigrationReceipt(Record):
    """The §20 record of one migration: what interpreted what before and after, and what did not fit.

    The receipt names both revisions instead of superseding either. That is the point of proof 16 —
    a schema migration leaves the source exactly as it was admitted and *adds* a target — and it is
    why ``source_revision_ref`` is a bound ref with a digest: a receipt that could not pin the record
    it read would let a later rewrite of history pass as a migration.
    """

    migration_id: str
    brief_ref: SemanticRef
    source_revision_ref: SemanticRef
    target_revision_ref: SemanticRef
    source_versions: VersionVector
    target_versions: VersionVector
    component: str
    transformed_paths: tuple[str, ...] = ()
    unchanged_paths: tuple[str, ...] = ()
    losses: tuple[MigrationLoss, ...] = ()
    validation_refs: tuple[SemanticRef, ...] = ()
    source_fingerprint_digest: str = ""
    target_fingerprint_digest: str = ""
    admitted_by: IntentAuthorityRef | None = None
    compiler_version: str = MIGRATION_COMPILER_VERSION
    schema_version: str = SCHEMA_VERSION
    contract_version: str = CONTRACT_VERSION
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    #: §19-§20: old revisions are never rewritten; a migration adds a target and documents it.
    rewrites_source = False
    #: A receipt records a migration; admitting the result is the caller's governed act.
    admits_itself = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "migration_id", require_identifier(self.migration_id, "migration_id"))
        object.__setattr__(
            self, "brief_ref", require_bound_ref(self.brief_ref, "brief_ref", kind=RefKind.BRIEF)
        )
        for name in ("source_revision_ref", "target_revision_ref"):
            object.__setattr__(
                self, name, require_bound_ref(getattr(self, name), name, kind=RefKind.REVISION)
            )
        if self.source_revision_ref.text == self.target_revision_ref.text:
            raise SchemaValidationError(
                f"migration {self.migration_id} migrates a revision into itself; that is a rewrite of "
                "an admitted record filed as a version bump"
            )
        source = VersionVector.coerce(self.source_versions, "source_versions")
        target = VersionVector.coerce(self.target_versions, "target_versions")
        object.__setattr__(self, "source_versions", source)
        object.__setattr__(self, "target_versions", target)
        component = MigrationComponentKind.parse(self.component, "component")
        object.__setattr__(self, "component", component.value)
        moved = source.moved_axes(target)
        if component not in moved:
            raise UnsupportedVersionError(
                f"migration {self.migration_id} declares a {component.value} migration but only "
                f"{[item.value for item in moved] or 'nothing'} moved between the two vectors; the "
                "receipt would credit one axis for a change another axis made"
            )
        transformed = bound_paths(self.transformed_paths, "transformed_paths")
        unchanged = bound_paths(self.unchanged_paths, "unchanged_paths")
        overlap = sorted(set(transformed) & set(unchanged))
        if overlap:
            raise SchemaValidationError(
                f"migration {self.migration_id} reports {overlap} as both transformed and unchanged; a "
                "path that changed is how a reader finds a lost requirement, so it cannot also be "
                "declared untouched"
            )
        if len(transformed) + len(unchanged) > MAX_PATHS_PER_SLICE:
            raise LimitExceededError(
                f"migration {self.migration_id} accounts for "
                f"{len(transformed) + len(unchanged)} paths, above {MAX_PATHS_PER_SLICE}"
            )
        object.__setattr__(self, "transformed_paths", transformed)
        object.__setattr__(self, "unchanged_paths", unchanged)
        losses = tuple(
            sorted(
                (MigrationLoss.coerce(item, "losses[]") for item in (self.losses or ())),
                key=lambda item: item.loss_id,
            )
        )
        if len(losses) > MAX_ENTRIES_PER_FIELD:
            raise LimitExceededError(
                f"migration {self.migration_id} reports {len(losses)} losses, above "
                f"{MAX_ENTRIES_PER_FIELD}"
            )
        unaccounted = sorted({item.semantic_path for item in losses} - set(transformed))
        if unaccounted:
            raise SchemaValidationError(
                f"migration {self.migration_id} loses elements on {unaccounted}, which it declares "
                "unchanged; a loss on a path claimed untouched is the receipt contradicting itself"
            )
        object.__setattr__(self, "losses", losses)
        object.__setattr__(
            self,
            "validation_refs",
            bound_refs(self.validation_refs, "validation_refs", minimum=1),
        )
        for name in ("source_fingerprint_digest", "target_fingerprint_digest"):
            value = getattr(self, name)
            if not value:
                raise SchemaValidationError(
                    f"migration {self.migration_id} omits {name}; §20 asks for the resulting "
                    "fingerprints, and an unpinned endpoint cannot be re-checked"
                )
            object.__setattr__(self, name, require_digest(value, name))
        if self.admitted_by is not None:
            object.__setattr__(
                self, "admitted_by", IntentAuthorityRef.coerce(self.admitted_by, "admitted_by")
            )
        if self.notes is not None:
            object.__setattr__(
                self, "notes", require_text(self.notes, "notes", maximum=MAX_RATIONALE_CHARS)
            )
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))

    @property
    def moved_axes(self) -> tuple[MigrationComponentKind, ...]:
        return self.source_versions.moved_axes(self.target_versions)

    @property
    def lost_paths(self) -> tuple[str, ...]:
        return tuple(sorted({item.semantic_path for item in self.losses}))

    @property
    def mandatory_losses(self) -> tuple[MigrationLoss, ...]:
        return tuple(item for item in self.losses if item.mandatory)

    @property
    def blocks_admission(self) -> bool:
        """§20: a lossy migration of a mandatory element cannot be admitted automatically."""

        return bool(self.mandatory_losses)

    @property
    def changed(self) -> bool:
        return bool(self.transformed_paths) or bool(self.losses)

    @property
    def receipt_digest(self) -> str:
        return content_digest(self.fingerprint_inputs())

    @property
    def ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.MIGRATION.value, ref_id=self.migration_id).with_digest(
            self.receipt_digest
        )

    def accounts_for(self, semantic_path: str) -> str:
        """Which of §20's two lists a path fell into, or ``ABSENT`` for neither."""

        path = require_semantic_path(semantic_path, "semantic_path")
        if path in self.transformed_paths:
            return "TRANSFORMED"
        if path in self.unchanged_paths:
            return "UNCHANGED"
        return "ABSENT"

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "migration_id": self.migration_id,
            "brief_ref": self.brief_ref.text,
            "source_revision_ref": self.source_revision_ref.text,
            "target_revision_ref": self.target_revision_ref.text,
            "source_versions": self.source_versions.as_mapping(),
            "target_versions": self.target_versions.as_mapping(),
            "component": self.component,
            "transformed_paths": sorted(self.transformed_paths),
            "unchanged_paths": sorted(self.unchanged_paths),
            "losses": [item.fingerprint_inputs() for item in self.losses],
            "validation_refs": sorted(item.text for item in self.validation_refs),
            "source_fingerprint_digest": self.source_fingerprint_digest,
            "target_fingerprint_digest": self.target_fingerprint_digest,
            "admitted_by": None if self.admitted_by is None else self.admitted_by.digest(),
            "compiler_version": self.compiler_version,
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
        }


MigrationReceipt.NESTED = {
    "brief_ref": of(SemanticRef),
    "source_revision_ref": of(SemanticRef),
    "target_revision_ref": of(SemanticRef),
    "source_versions": of(VersionVector),
    "target_versions": of(VersionVector),
    "losses": of(MigrationLoss),
    "validation_refs": of(SemanticRef),
    "admitted_by": of(IntentAuthorityRef),
}


@dataclass(frozen=True)
class CompatibilityDeclaration(Record):
    """§19's explicit statement that an older reading can be carried unchanged.

    This is the only route by which a version axis may move without a new revision, so it is the
    record most worth hardening. It refuses itself in three cases: when nothing moved (a declaration
    about no change is noise filed as governance), when the meanings actually differ (that is a
    migration, and calling it compatible is how a requirement gets dropped by a compiler upgrade),
    and when the declarer cannot self-assert (§19 says compatibility is *declared*, which is a
    governed act rather than an observation a model makes about its own inputs).
    """

    declaration_id: str
    brief_ref: SemanticRef
    revision_ref: SemanticRef
    from_versions: VersionVector
    to_versions: VersionVector
    axes: tuple[str, ...] = ()
    semantic_digest: str = ""
    evidence_refs: tuple[SemanticRef, ...] = ()
    declared_by: IntentAuthorityRef | None = None
    compiler_version: str = MIGRATION_COMPILER_VERSION
    schema_version: str = SCHEMA_VERSION
    contract_version: str = CONTRACT_VERSION
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    #: §19: a declaration reuses the existing revision rather than creating one.
    creates_no_revision = True
    #: The claim being made, recorded so a reader cannot mistake this for a migration receipt.
    meaning_changed = False
    rewrites_source = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "declaration_id", require_identifier(self.declaration_id, "declaration_id"))
        object.__setattr__(
            self, "brief_ref", require_bound_ref(self.brief_ref, "brief_ref", kind=RefKind.BRIEF)
        )
        object.__setattr__(
            self, "revision_ref", require_bound_ref(self.revision_ref, "revision_ref", kind=RefKind.REVISION)
        )
        source = VersionVector.coerce(self.from_versions, "from_versions")
        target = VersionVector.coerce(self.to_versions, "to_versions")
        object.__setattr__(self, "from_versions", source)
        object.__setattr__(self, "to_versions", target)
        moved = source.moved_axes(target)
        if not moved:
            raise SchemaValidationError(
                f"compatibility declaration {self.declaration_id} declares two identical version "
                "vectors compatible; nothing moved, and a governance record about no change teaches a "
                "reader that records like this one are routine noise"
            )
        declared = tuple(
            sorted({MigrationComponentKind.parse(item, "axes[]").value for item in (self.axes or moved)})
        )
        if set(declared) != {item.value for item in moved}:
            raise SchemaValidationError(
                f"compatibility declaration {self.declaration_id} covers {list(declared)} while "
                f"{sorted(item.value for item in moved)} moved; an axis left out of a compatibility "
                "claim is an axis somebody later assumes was checked"
            )
        object.__setattr__(self, "axes", declared)
        object.__setattr__(self, "semantic_digest", require_digest(self.semantic_digest, "semantic_digest"))
        object.__setattr__(
            self, "evidence_refs", bound_refs(self.evidence_refs, "evidence_refs", minimum=1)
        )
        if self.declared_by is None:
            raise AuthorityError(
                f"compatibility declaration {self.declaration_id} has no declarer; §19 makes "
                "compatibility an explicit declaration, and an unsigned one is an assumption with a ref"
            )
        declarer = IntentAuthorityRef.coerce(self.declared_by, "declared_by")
        object.__setattr__(self, "declared_by", declarer)
        if not declarer.level.self_asserting_is_enough:
            raise AuthorityError(
                f"{declarer.level.value} may not declare an older reading compatible (§19); that "
                "decision keeps a revision in service under new versions and belongs to governed "
                "policy or the human owner"
            )
        if self.notes is not None:
            object.__setattr__(
                self, "notes", require_text(self.notes, "notes", maximum=MAX_RATIONALE_CHARS)
            )
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))

    @property
    def declaration_digest(self) -> str:
        return content_digest(self.fingerprint_inputs())

    @property
    def ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.RECEIPT.value, ref_id=self.declaration_id).with_digest(
            self.declaration_digest
        )

    def covers(self, component: Any) -> bool:
        return MigrationComponentKind.parse(component, "component").value in self.axes

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "declaration_id": self.declaration_id,
            "brief_ref": self.brief_ref.text,
            "revision_ref": self.revision_ref.text,
            "from_versions": self.from_versions.as_mapping(),
            "to_versions": self.to_versions.as_mapping(),
            "axes": sorted(self.axes),
            "semantic_digest": self.semantic_digest,
            "evidence_refs": sorted(item.text for item in self.evidence_refs),
            "declared_by": self.declared_by.digest(),
            "compiler_version": self.compiler_version,
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
        }


CompatibilityDeclaration.NESTED = {
    "brief_ref": of(SemanticRef),
    "revision_ref": of(SemanticRef),
    "from_versions": of(VersionVector),
    "to_versions": of(VersionVector),
    "evidence_refs": of(SemanticRef),
    "declared_by": of(IntentAuthorityRef),
}


def _require_profile(profile: Any) -> SemanticEquivalenceProfile:
    """Both §19 routes compare meanings, so both need a *named* equivalence rule."""

    if not isinstance(profile, SemanticEquivalenceProfile):
        raise SchemaValidationError(
            "profile must be a SemanticEquivalenceProfile; comparing revisions under an undeclared "
            "equivalence rule is the fuzzy-text shortcut §12 forbids"
        )
    return profile


def _profiled_path_digests(
    revision: BriefRevision,
    profile: SemanticEquivalenceProfile,
) -> dict[str, str]:
    _require_profile(profile)
    return dict(fingerprint_revision(revision, profile=profile).path_digests)


def _split_paths(
    source: BriefRevision,
    target: BriefRevision,
    *,
    profile: SemanticEquivalenceProfile,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Which paths the migration moved and which it demonstrably did not, from the fingerprints (§20).

    Derived rather than supplied because the two lists are the receipt's only checkable content: a
    caller who could name the unchanged paths could un-change anything, and the reader's question —
    "what did this upgrade touch?" — would stop having an answer.
    """

    before, after = _profiled_path_digests(source, profile), _profiled_path_digests(target, profile)
    shared = set(before) & set(after)
    moved = sorted(
        (set(before) | set(after)) - shared | {path for path in shared if before[path] != after[path]}
    )
    unchanged = sorted(path for path in shared if before[path] == after[path])
    return tuple(moved), tuple(unchanged)


def _verify_losses(source: BriefRevision, losses: Iterable[MigrationLoss]) -> None:
    """Check each reported loss against the revision it was taken from (§20).

    A loss is a claim about a record that exists, so the claim is checked rather than trusted: the
    element has to be a statement of that revision, carry the quoted digest, sit on the named path,
    and be as mandatory as the receipt says. The last check is the one that decides admission, which
    makes an understated ``mandatory`` flag the cheapest way to walk a dropped requirement past the
    gate — so it is re-derived from the source every time the receipt is read.
    """

    for item in losses:
        loss = MigrationLoss.coerce(item, "losses[]")
        ref = loss.element_ref
        if ref.kind != RefKind.STATEMENT.value:
            raise SchemaValidationError(
                f"loss {loss.loss_id} reports a {ref.kind}, not a {RefKind.STATEMENT.value}; §20 "
                "counts what failed to cross the migration, and a loss whose subject is not an "
                "admitted statement has no subject"
            )
        found = source.statement(ref.ref_id)
        if found is None:
            raise RefError(
                f"loss {loss.loss_id} reports {ref.text}, which revision {source.revision_id} does "
                "not carry; an element absent from the source was not lost by this migration"
            )
        if ref.content_digest != found.statement_ref.content_digest:
            raise RefError(
                f"loss {loss.loss_id} pins {ref.content_digest} but the source statement digests as "
                f"{found.statement_ref.content_digest}; the receipt describes a different element "
                "than the one it claims to have dropped"
            )
        if loss.semantic_path != found.semantic_path:
            raise SchemaValidationError(
                f"loss {loss.loss_id} is filed under {loss.semantic_path} but the statement lives at "
                f"{found.semantic_path}; the path is how a reviewer finds the requirement again"
            )
        if loss.mandatory != found.mandatory:
            raise SchemaValidationError(
                f"loss {loss.loss_id} reports mandatory={loss.mandatory} for a statement that is "
                f"mandatory={found.mandatory}; §20 blocks admission on mandatory losses, so this "
                "field is re-derived from the source rather than taken from the paper"
            )


def migrate_revision(
    *,
    migration_id: str,
    source: BriefRevision,
    target: BriefRevision,
    source_versions: VersionVector | Mapping[str, Any],
    target_versions: VersionVector | Mapping[str, Any],
    component: Any,
    validation_refs: Iterable[SemanticRef],
    losses: Iterable[MigrationLoss] = (),
    admitted_by: IntentAuthorityRef | None = None,
    profile: SemanticEquivalenceProfile = DEFAULT_EQUIVALENCE_PROFILE,
    notes: str | None = None,
    metadata: Mapping[str, str] | None = None,
) -> MigrationReceipt:
    """File the §20 receipt for reading one admitted revision under a new set of versions.

    The source keeps its own id, number and digest — proof 16 is precisely that a schema migration
    leaves the revision it migrated from untouched and *adds* a target. The accounting comes out of
    the two fingerprints rather than out of the caller's description of them, and the target has to
    come after the source, because a migration that runs backwards is a rewrite of history filed as a
    version bump.
    """

    for name, value in (("source", source), ("target", target)):
        if not isinstance(value, BriefRevision):
            raise SchemaValidationError(f"migrate_revision expects {name} to be a BriefRevision")
    if source.brief_id != target.brief_id:
        raise RefError(
            f"cannot migrate {source.revision_id} of {source.brief_id} into {target.brief_id}; a "
            "brief migrates its own meaning, and crossing briefs here would move requirements under "
            "a receipt that only vouches for one of them"
        )
    if target.revision_number <= source.revision_number:
        raise StaleSemanticError(
            f"migration {migration_id} writes target revision {target.revision_number} from source "
            f"revision {source.revision_number}; history is append-only, so a migration result is a "
            "later revision rather than an earlier one being rewritten"
        )
    coerced = tuple(MigrationLoss.coerce(item, "losses[]") for item in (losses or ()))
    _verify_losses(source, coerced)
    transformed, unchanged = _split_paths(source, target, profile=profile)
    return MigrationReceipt(
        migration_id=migration_id,
        brief_ref=source.brief_ref,
        source_revision_ref=source.revision_ref,
        target_revision_ref=target.revision_ref,
        source_versions=VersionVector.coerce(source_versions, "source_versions"),
        target_versions=VersionVector.coerce(target_versions, "target_versions"),
        component=component,
        transformed_paths=transformed,
        unchanged_paths=unchanged,
        losses=coerced,
        validation_refs=validation_refs,
        source_fingerprint_digest=fingerprint_revision(source, profile=profile).semantic_digest,
        target_fingerprint_digest=fingerprint_revision(target, profile=profile).semantic_digest,
        admitted_by=admitted_by,
        notes=notes,
        metadata=metadata or {},
    )


def require_admissible(
    receipt: MigrationReceipt,
    *,
    source: BriefRevision,
    target: BriefRevision | None = None,
    profile: SemanticEquivalenceProfile = DEFAULT_EQUIVALENCE_PROFILE,
) -> MigrationReceipt:
    """Re-check a migration at admission time and refuse it if a mandatory element did not cross (§20).

    The receipt is not evidence of its own correctness, so the gate re-derives what it can see: the
    source ref, every loss, and — when the target is in hand — the path accounting and both endpoint
    fingerprints. What it refuses is the automatic admission, not the record: the loss stays filed for
    a reviewer, because the alternative to documenting a dropped requirement is forgetting it.
    """

    if not isinstance(receipt, MigrationReceipt):
        raise SchemaValidationError("require_admissible expects a MigrationReceipt")
    if not isinstance(source, BriefRevision):
        raise SchemaValidationError("require_admissible expects source to be a BriefRevision")
    if receipt.source_revision_ref.text != source.revision_ref.text:
        raise RefError(
            f"receipt {receipt.migration_id} was written against a different source than revision "
            f"{source.revision_id}; admitting it against this record would credit a migration that "
            "did not happen here"
        )
    _verify_losses(source, receipt.losses)
    source_fingerprint = fingerprint_revision(source, profile=_require_profile(profile))
    if receipt.source_fingerprint_digest != source_fingerprint.semantic_digest:
        raise StaleSemanticError(
            f"receipt {receipt.migration_id} pins source digest {receipt.source_fingerprint_digest} "
            f"while {source.revision_id} now fingerprints as {source_fingerprint.semantic_digest}; "
            "the record the migration read is not the record being admitted against"
        )
    if target is not None:
        if not isinstance(target, BriefRevision):
            raise SchemaValidationError("require_admissible expects target to be a BriefRevision")
        if receipt.target_revision_ref.text != target.revision_ref.text:
            raise RefError(
                f"receipt {receipt.migration_id} does not describe target revision "
                f"{target.revision_id}"
            )
        expected = fingerprint_revision(target, profile=profile).semantic_digest
        if receipt.target_fingerprint_digest != expected:
            raise StaleSemanticError(
                f"receipt {receipt.migration_id} pins target digest "
                f"{receipt.target_fingerprint_digest} while the revision now fingerprints as {expected}"
            )
        transformed, unchanged = _split_paths(source, target, profile=profile)
        if transformed != receipt.transformed_paths or unchanged != receipt.unchanged_paths:
            raise StaleSemanticError(
                f"receipt {receipt.migration_id} accounts for paths "
                f"{sorted(set(receipt.transformed_paths) | set(receipt.unchanged_paths))} while "
                f"{source.revision_id} → {target.revision_id} now moves {list(transformed)} and "
                f"leaves {list(unchanged)}; the migration's own bookkeeping no longer matches the "
                "revisions it names"
            )
    blocking = receipt.mandatory_losses
    if blocking:
        raise AdmissionRefusedError(
            f"migration {receipt.migration_id} lost mandatory elements "
            f"{sorted(item.element_ref.text for item in blocking)} on paths {list(receipt.lost_paths)}; "
            "§20 refuses automatic admission of a lossy migration of a mandatory semantic element, "
            "so this needs an explicit human or governed decision rather than an upgrade"
        )
    return receipt


def declare_compatible(
    *,
    declaration_id: str,
    revision: BriefRevision,
    from_versions: VersionVector | Mapping[str, Any],
    to_versions: VersionVector | Mapping[str, Any],
    declared_by: IntentAuthorityRef,
    evidence_refs: Iterable[SemanticRef],
    axes: Iterable[Any] | None = None,
    profile: SemanticEquivalenceProfile = DEFAULT_EQUIVALENCE_PROFILE,
    notes: str | None = None,
    metadata: Mapping[str, str] | None = None,
) -> CompatibilityDeclaration:
    """Record §19's other route: a version axis moved and the admitted meaning did not.

    The semantic digest is computed from the revision under the declared profile instead of accepted
    from the caller. That is the difference between a declaration that can be re-checked and a
    sentence that says something was checked, and this record is the only route by which an existing
    revision stays in service without a new one.
    """

    if not isinstance(revision, BriefRevision):
        raise SchemaValidationError("declare_compatible expects revision to be a BriefRevision")
    _require_profile(profile)
    fingerprint = fingerprint_revision(revision, profile=profile)
    return CompatibilityDeclaration(
        declaration_id=declaration_id,
        brief_ref=revision.brief_ref,
        revision_ref=revision.revision_ref,
        from_versions=VersionVector.coerce(from_versions, "from_versions"),
        to_versions=VersionVector.coerce(to_versions, "to_versions"),
        axes=tuple(axes or ()),
        semantic_digest=fingerprint.semantic_digest,
        evidence_refs=evidence_refs,
        declared_by=declared_by,
        notes=notes,
        metadata=metadata or {},
    )


def require_declared(
    declaration: CompatibilityDeclaration,
    *,
    revision: BriefRevision,
    profile: SemanticEquivalenceProfile = DEFAULT_EQUIVALENCE_PROFILE,
) -> CompatibilityDeclaration:
    """Re-check a compatibility claim against the revision it covers (§19).

    The declaration is the only route by which an admitted revision stays in service without a new
    one, so the digest it quotes is re-derived here instead of trusted: a caller who could name any
    digest could declare *any* revision compatible with any upgrade, and the record would stop being
    evidence at exactly the moment a reviewer wanted to verify it.
    """

    if not isinstance(declaration, CompatibilityDeclaration):
        raise SchemaValidationError("require_declared expects a CompatibilityDeclaration")
    if not isinstance(revision, BriefRevision):
        raise SchemaValidationError("require_declared expects revision to be a BriefRevision")
    _require_profile(profile)
    if declaration.revision_ref.text != revision.revision_ref.text:
        raise RefError(
            f"declaration {declaration.declaration_id} covers a different revision than "
            f"{revision.revision_id}; a compatibility claim about another record keeps nothing in "
            "service here"
        )
    fingerprint = fingerprint_revision(revision, profile=profile)
    if declaration.semantic_digest != fingerprint.semantic_digest:
        raise StaleSemanticError(
            f"declaration {declaration.declaration_id} pins semantic digest "
            f"{declaration.semantic_digest} while {revision.revision_id} now fingerprints as "
            f"{fingerprint.semantic_digest}; the meaning being carried across is not the one on file"
        )
    return declaration
