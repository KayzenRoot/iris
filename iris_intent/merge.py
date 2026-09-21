"""F-M03-15 S05 revision history: semantic three-way merge analysis and restoration (§16-§18, §21).

Two sentences carry this module. The first is §16's: M03 supplies *merge intelligence* to a branch
merge M02 owns, so the analysis below reports what can be taken from each side, what both sides
already agree on, and what must be decided — and never performs the merge. The second is §21's: a
restoration is a new revision, not a rewind, so it carries the *current* policy refs and recompiles
under them rather than reviving the world as it was interpreted.

The failure modes here are the quiet kind. A merge tool that invents a conflict between two changes
that never touched forces a human to read noise, and a merge tool that invents a *result* while two
sides disagree ships a decision nobody made. Both are refused structurally: the candidate merged
state exists only when nothing is left to decide, and equivalence is read off the digests the delta
already carries — which were projected through the caller's equivalence profile — rather than off a
second notion of "the same" invented here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .authority import AuthorityPolicyGraph, AuthorityPolicyGraphRef
from .base import Labeled, Record, of
from .briefs import BriefRevision
from .errors import (
    AuthorityError,
    LimitExceededError,
    RefError,
    SchemaValidationError,
    StaleSemanticError,
)
from .fingerprints import (
    DEFAULT_EQUIVALENCE_PROFILE,
    ChangeKind,
    SemanticChange,
    IntentDelta,
    SemanticEquivalenceProfile,
    fingerprint_revision,
)
from .identity import RefKind, SemanticRef, require_bound_ref
from .intent import IntentAuthorityRef
from .limits import MAX_MERGE_COMPONENTS, MAX_RATIONALE_CHARS, MAX_SCOPE_PATHS
from .overrides import bound_paths, bound_refs, covers_path
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
    "MERGE_COMPILER_VERSION",
    "BriefSemanticMergeAnalysis",
    "MergeComponent",
    "MergeComponentKind",
    "MergeSide",
    "RestorationRevision",
    "RevisionClassification",
    "analyze_semantic_merge",
    "classify_revision",
    "meanings_agree",
    "restore_revision",
]

MERGE_COMPILER_VERSION = "m03-merge-1.0"

#: The interpretation settings a restoration must state rather than inherit (§21).
_RECOMPILE_KEYS = frozenset({"schema", "compiler", "profile", "policy"})


class RevisionClassification(Labeled):
    """What one admitted edit did to the *meaning* of a brief (§18).

    Every admitted edit is a new revision; only some of them moved the semantics. The split is
    worth encoding because the consequence is someone else's bill: a downstream cache that
    invalidates on ``SOURCE_ONLY_CHANGE`` rebuilds media nobody asked it to, and one that skips
    ``POLICY_CONTEXT_CHANGE`` keeps shipping a reading the current policy no longer admits.
    """

    SOURCE_ONLY_CHANGE = "SOURCE_ONLY_CHANGE"
    SEMANTIC_EQUIVALENT_CHANGE = "SEMANTIC_EQUIVALENT_CHANGE"
    SEMANTIC_CHANGE = "SEMANTIC_CHANGE"
    POLICY_CONTEXT_CHANGE = "POLICY_CONTEXT_CHANGE"
    MERGE_REVISION = "MERGE_REVISION"
    RESTORATION_REVISION = "RESTORATION_REVISION"
    MIGRATION_REVISION = "MIGRATION_REVISION"

    @property
    def preserves_semantic_fingerprint(self) -> bool:
        """Whether a fingerprint taken before this edit still identifies the same meaning."""

        return self in {
            RevisionClassification.SOURCE_ONLY_CHANGE,
            RevisionClassification.SEMANTIC_EQUIVALENT_CHANGE,
        }

    @property
    def invalidates_compiled_artifacts(self) -> bool:
        """Whether work derived from the previous revision has to be recomputed.

        ``True`` is the default because the two classes above are the only ones proven not to move
        the semantic digest; a class that has to argue for reuse is the whole point of §18.
        """

        return not self.preserves_semantic_fingerprint

    @property
    def created_by_governance(self) -> bool:
        """Whether the edit exists because a policy, a merge or a migration required it."""

        return self in {
            RevisionClassification.MERGE_REVISION,
            RevisionClassification.RESTORATION_REVISION,
            RevisionClassification.MIGRATION_REVISION,
        }


class MergeSide(Labeled):
    """Which branch a merge component came from.

    ``BOTH`` is a side rather than the absence of one because an equivalent change and a
    non-overlapping change look identical until someone asks which branch produced them, and
    "both, deliberately" is a different fact from "one, and the other never spoke".
    """

    LEFT = "LEFT"
    RIGHT = "RIGHT"
    BOTH = "BOTH"


class MergeComponentKind(Labeled):
    """The five readings §16 asks a three-way semantic merge to separate.

    The order in which they are decided is not presentation: a pair of changes both sides made
    identically is not a conflict wearing a disguise, and a change on a reserved boundary is not a
    merge mechanic at all. Each kind states whether it may ride along in the candidate.
    """

    NON_OVERLAPPING_SAFE = "NON_OVERLAPPING_SAFE"
    EQUIVALENT = "EQUIVALENT"
    CONFLICTING = "CONFLICTING"
    AUTHORITY_POLICY = "AUTHORITY_POLICY"
    OPEN_QUESTION = "OPEN_QUESTION"

    @property
    def needs_a_decision(self) -> bool:
        """Whether the candidate merged state has to wait for somebody."""

        return self in {
            MergeComponentKind.CONFLICTING,
            MergeComponentKind.AUTHORITY_POLICY,
            MergeComponentKind.OPEN_QUESTION,
        }

    @property
    def ships_in_the_candidate(self) -> bool:
        """Whether M02 may take this component without a semantic decision upstream of it (§16)."""

        return self in {MergeComponentKind.NON_OVERLAPPING_SAFE, MergeComponentKind.EQUIVALENT}


@dataclass(frozen=True)
class MergeComponent(Record):
    """One place where the two sides spoke, and what §16 makes of it.

    A component records *both* digests when it is a dispute rather than choosing one, because the
    reader who has to decide needs to see what each branch believed, and a component that had
    already picked a winner would be last-writer-wins re-entering through the merge door (§7).
    """

    component_id: str
    kind: str
    side: str
    semantic_paths: tuple[str, ...] = ()
    subject_refs: tuple[SemanticRef, ...] = ()
    before_digest: str | None = None
    after_digest: str | None = None
    other_digest: str | None = None
    change_kinds: tuple[str, ...] = ()
    reason: str = ""

    #: A component reports where the disagreement is; it never resolves one.
    decides_nothing = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "component_id", require_identifier(self.component_id, "component_id"))
        kind = MergeComponentKind.parse(self.kind, "kind")
        object.__setattr__(self, "kind", kind.value)
        side = MergeSide.parse(self.side, "side")
        object.__setattr__(self, "side", side.value)
        paths = bound_paths(self.semantic_paths, "semantic_paths")
        if len(paths) > MAX_SCOPE_PATHS:
            raise LimitExceededError(f"component {self.component_id} spans {len(paths)} paths")
        object.__setattr__(self, "semantic_paths", paths)
        object.__setattr__(self, "subject_refs", bound_refs(self.subject_refs, "subject_refs", minimum=0))
        for name in ("before_digest", "after_digest", "other_digest"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_digest(value, name))
        kinds = tuple(
            sorted({ChangeKind.parse(item, "change_kinds[]").value for item in (self.change_kinds or ())})
        )
        object.__setattr__(self, "change_kinds", kinds)
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=MAX_RATIONALE_CHARS))
        if kind is MergeComponentKind.NON_OVERLAPPING_SAFE and side is MergeSide.BOTH:
            raise SchemaValidationError(
                f"component {self.component_id} is safe and non-overlapping but claims both sides; "
                "one side only, or it is an equivalent change and should say so"
            )
        if kind in {MergeComponentKind.EQUIVALENT, MergeComponentKind.CONFLICTING} and side is not MergeSide.BOTH:
            raise SchemaValidationError(
                f"component {self.component_id} is a {kind.value} naming only {side.value}; the "
                "comparison needs both sides on the record"
            )
        if kind in {MergeComponentKind.CONFLICTING, MergeComponentKind.AUTHORITY_POLICY} and (
            self.after_digest == self.other_digest
        ):
            raise SchemaValidationError(
                f"component {self.component_id} is a dispute reporting one reading twice; the two "
                "sides have to appear as the two things they actually are, or this is a conflict "
                "invented to block a merge that could have gone through"
            )

    @property
    def kind_enum(self) -> MergeComponentKind:
        return MergeComponentKind.parse(self.kind)

    @property
    def needs_a_decision(self) -> bool:
        return self.kind_enum.needs_a_decision

    @property
    def subject_ids(self) -> tuple[str, ...]:
        return tuple(sorted({item.ref_id for item in self.subject_refs}))

    def touches(self, semantic_path: str) -> bool:
        path = require_semantic_path(semantic_path, "semantic_path")
        return any(covers_path(one, path) or covers_path(path, one) for one in self.semantic_paths)

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "kind": self.kind,
            "side": self.side,
            "paths": sorted(self.semantic_paths),
            "subjects": sorted(item.text for item in self.subject_refs),
            "before": self.before_digest,
            "after": self.after_digest,
            "other": self.other_digest,
            "change_kinds": sorted(self.change_kinds),
        }


MergeComponent.NESTED = {"subject_refs": of(SemanticRef)}


@dataclass(frozen=True)
class BriefSemanticMergeAnalysis(Record):
    """The semantic read of one branch convergence, addressed to whoever owns the merge (§16).

    ``merged_candidate_digest`` is this record's sharp edge. It is required to be present exactly
    when nothing is left to decide, so an analysis that found a dispute cannot hand M02 a state it
    assembled out of the pieces it liked, and an analysis that found none cannot shrug and leave
    M02 to work the diff out again.
    """

    analysis_id: str
    brief_ref: SemanticRef
    base_ref: SemanticRef
    left_ref: SemanticRef
    right_ref: SemanticRef
    base_revision_number: int
    left_revision_number: int
    right_revision_number: int
    left_delta: IntentDelta
    right_delta: IntentDelta
    components: tuple[MergeComponent, ...] = ()
    merged_candidate_digest: str | None = None
    graph_ref: AuthorityPolicyGraphRef | None = None
    compiler_version: str = MERGE_COMPILER_VERSION
    schema_version: str = SCHEMA_VERSION
    contract_version: str = CONTRACT_VERSION
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    #: §16 and §17: M03 reads the semantics; M02 owns branches, variants and the merge commit.
    decides_merge = False
    m02_owns_branch_history = True
    implements_merge_mechanics = False
    #: §7: nothing in this record ranks the two sides.
    prefers_recency = False
    uses_priority = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "analysis_id", require_identifier(self.analysis_id, "analysis_id"))
        object.__setattr__(
            self, "brief_ref", require_bound_ref(self.brief_ref, "brief_ref", kind=RefKind.BRIEF)
        )
        for name in ("base_ref", "left_ref", "right_ref"):
            object.__setattr__(
                self, name, require_bound_ref(getattr(self, name), name, kind=RefKind.REVISION)
            )
        for name in ("base_revision_number", "left_revision_number", "right_revision_number"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise SchemaValidationError(f"{name} must be a positive revision ordinal")
        if min(self.left_revision_number, self.right_revision_number) <= self.base_revision_number:
            raise StaleSemanticError(
                f"merge {self.analysis_id} claims base revision {self.base_revision_number} but a side "
                "does not descend from it; a base nobody branched from is not a common ancestor"
            )
        left = IntentDelta.coerce(self.left_delta, "left_delta")
        right = IntentDelta.coerce(self.right_delta, "right_delta")
        if left.before_ref.text != right.before_ref.text:
            raise StaleSemanticError(
                f"merge {self.analysis_id} diffs {left.before_ref.text}..{left.after_ref.text} against "
                f"{right.before_ref.text}..{right.after_ref.text}; two deltas from different bases are "
                "two changelogs, not a three-way merge, and the overlap cannot be computed"
            )
        if left.subject_kind != right.subject_kind:
            raise SchemaValidationError(
                f"merge {self.analysis_id} compares a {left.subject_kind} delta with a "
                f"{right.subject_kind} delta; the two layers move for different reasons"
            )
        object.__setattr__(self, "left_delta", left)
        object.__setattr__(self, "right_delta", right)
        items = tuple(
            sorted(
                (MergeComponent.coerce(item, "components[]") for item in (self.components or ())),
                key=lambda item: item.component_id,
            )
        )
        repeated = sorted(
            {item.component_id for item in items if [x.component_id for x in items].count(item.component_id) > 1}
        )
        if repeated:
            raise SchemaValidationError(f"components repeats component ids {repeated}")
        if len(items) > MAX_MERGE_COMPONENTS:
            raise LimitExceededError(
                f"merge {self.analysis_id} produced {len(items)} components, over the limit of "
                f"{MAX_MERGE_COMPONENTS}; the reading is refused rather than trimmed, because a "
                "trimmed component list hides exactly the dispute a merge would ship"
            )
        object.__setattr__(self, "components", items)
        if self.merged_candidate_digest is not None:
            object.__setattr__(
                self,
                "merged_candidate_digest",
                require_digest(self.merged_candidate_digest, "merged_candidate_digest"),
            )
        if self.graph_ref is not None:
            object.__setattr__(self, "graph_ref", AuthorityPolicyGraphRef.coerce(self.graph_ref, "graph_ref"))
        undecided = sorted(item.component_id for item in items if item.needs_a_decision)
        if undecided and self.merged_candidate_digest is not None:
            raise SchemaValidationError(
                f"merge {self.analysis_id} offers a candidate state while {undecided} is undecided; "
                "a merged meaning assembled around an open dispute is a decision nobody made, filed "
                "as arithmetic"
            )
        if not undecided and self.merged_candidate_digest is None:
            raise SchemaValidationError(
                f"merge {self.analysis_id} found nothing to decide and still withholds a candidate "
                "state; §16 exists so that M02 does not have to re-derive the semantics in order to "
                "merge them"
            )
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))

    @property
    def analysis_digest(self) -> str:
        return content_digest(self.fingerprint_inputs())

    @property
    def ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.MERGE_ANALYSIS.value, ref_id=self.analysis_id).with_digest(
            self.analysis_digest
        )

    def components_of(self, kind: Any) -> tuple[MergeComponent, ...]:
        wanted = MergeComponentKind.parse(kind, "kind").value
        return tuple(item for item in self.components if item.kind == wanted)

    @property
    def safe_changes(self) -> tuple[MergeComponent, ...]:
        return self.components_of(MergeComponentKind.NON_OVERLAPPING_SAFE)

    @property
    def equivalent_changes(self) -> tuple[MergeComponent, ...]:
        return self.components_of(MergeComponentKind.EQUIVALENT)

    @property
    def conflicting_changes(self) -> tuple[MergeComponent, ...]:
        return self.components_of(MergeComponentKind.CONFLICTING)

    @property
    def authority_issues(self) -> tuple[MergeComponent, ...]:
        return self.components_of(MergeComponentKind.AUTHORITY_POLICY)

    @property
    def unresolved_questions(self) -> tuple[MergeComponent, ...]:
        return self.components_of(MergeComponentKind.OPEN_QUESTION)

    @property
    def clean(self) -> bool:
        return not any(item.needs_a_decision for item in self.components)

    @property
    def needs_human_decision(self) -> bool:
        return bool(self.authority_issues or self.unresolved_questions)

    @property
    def paths_in_dispute(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    path
                    for item in self.components
                    if item.needs_a_decision
                    for path in item.semantic_paths
                }
            )
        )

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "brief_ref": self.brief_ref.text,
            "base_ref": self.base_ref.text,
            "left_ref": self.left_ref.text,
            "right_ref": self.right_ref.text,
            "left_delta": self.left_delta.delta_digest,
            "right_delta": self.right_delta.delta_digest,
            "components": [item.fingerprint_inputs() for item in self.components],
            "merged_candidate_digest": self.merged_candidate_digest,
            "graph_ref": None if self.graph_ref is None else self.graph_ref.pin_id,
            "compiler_version": self.compiler_version,
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
        }


BriefSemanticMergeAnalysis.NESTED = {
    "brief_ref": of(SemanticRef),
    "base_ref": of(SemanticRef),
    "left_ref": of(SemanticRef),
    "right_ref": of(SemanticRef),
    "left_delta": of(IntentDelta),
    "right_delta": of(IntentDelta),
    "components": of(MergeComponent),
    "graph_ref": of(AuthorityPolicyGraphRef),
}


@dataclass(frozen=True)
class RestorationRevision(Record):
    """A new revision that means what an older one meant, read under today's policy (§21).

    The dangerous reading of "roll back" is that the old world comes back with it. This record
    cannot express that: it names the revision it restores *and* the policy refs and compiler
    versions the restoration was recompiled under, and it refuses to be built without them. Rights
    and security decisions taken after the revision being restored stay in force, which is exactly
    what a plain history rewind would erase.
    """

    restoration_id: str
    brief_ref: SemanticRef
    new_revision_ref: SemanticRef
    restores_from: SemanticRef
    reason: str
    decided_by: IntentAuthorityRef
    current_policy_refs: tuple[SemanticRef, ...] = ()
    recompiled_with: Mapping[str, str] = field(default_factory=dict)
    graph_ref: AuthorityPolicyGraphRef | None = None
    compiler_version: str = MERGE_COMPILER_VERSION
    schema_version: str = SCHEMA_VERSION
    contract_version: str = CONTRACT_VERSION
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    #: §21: history is append-only; a restoration adds to it and rewrites nothing.
    rewrites_history = False
    revives_old_policy = False
    #: Production branch, snapshot and rollback mechanics stay with M02.
    m02_owns_production_rollback = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "restoration_id", require_identifier(self.restoration_id, "restoration_id"))
        object.__setattr__(
            self, "brief_ref", require_bound_ref(self.brief_ref, "brief_ref", kind=RefKind.BRIEF)
        )
        for name in ("new_revision_ref", "restores_from"):
            object.__setattr__(
                self, name, require_bound_ref(getattr(self, name), name, kind=RefKind.REVISION)
            )
        if self.new_revision_ref.text == self.restores_from.text:
            raise SchemaValidationError(
                f"restoration {self.restoration_id} restores a revision and calls it new; restoring the "
                "revision that is already current is a no-op filed as an event"
            )
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=MAX_RATIONALE_CHARS))
        object.__setattr__(self, "decided_by", IntentAuthorityRef.coerce(self.decided_by, "decided_by"))
        object.__setattr__(
            self, "current_policy_refs", bound_refs(self.current_policy_refs, "current_policy_refs")
        )
        supplied = dict(self.recompiled_with or {})
        unknown = sorted(set(supplied) - _RECOMPILE_KEYS)
        if unknown:
            raise SchemaValidationError(
                f"restoration {self.restoration_id} reports recompiled_with {unknown}, which are not "
                f"interpretation components ({sorted(_RECOMPILE_KEYS)})"
            )
        for key in sorted(_RECOMPILE_KEYS):
            if key not in supplied:
                raise SchemaValidationError(
                    f"restoration {self.restoration_id} does not say which {key} interpreted it; §21 "
                    "allows no restoration that keeps the old settings, because the older policy is the "
                    "thing a restoration is most likely to smuggle back"
                )
        object.__setattr__(
            self,
            "recompiled_with",
            {key: require_version_text(supplied[key], f"recompiled_with.{key}") for key in sorted(supplied)},
        )
        if self.graph_ref is not None:
            object.__setattr__(self, "graph_ref", AuthorityPolicyGraphRef.coerce(self.graph_ref, "graph_ref"))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))

    @property
    def restoration_digest(self) -> str:
        return content_digest(self.fingerprint_inputs())

    @property
    def ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.REVISION.value, ref_id=self.restoration_id).with_digest(
            self.restoration_digest
        )

    def policy_also_governed(self, other: RestorationRevision) -> bool:
        """Whether both restorations were decided under the same current policy set."""

        return sorted(item.text for item in self.current_policy_refs) == sorted(
            item.text for item in other.current_policy_refs
        )

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "restoration_id": self.restoration_id,
            "brief_ref": self.brief_ref.text,
            "new_revision_ref": self.new_revision_ref.text,
            "restores_from": self.restores_from.text,
            "decided_by": self.decided_by.digest(),
            "current_policy_refs": sorted(item.text for item in self.current_policy_refs),
            "recompiled_with": dict(sorted(self.recompiled_with.items())),
            "graph_ref": None if self.graph_ref is None else self.graph_ref.pin_id,
            "compiler_version": self.compiler_version,
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
        }


RestorationRevision.NESTED = {
    "brief_ref": of(SemanticRef),
    "new_revision_ref": of(SemanticRef),
    "restores_from": of(SemanticRef),
    "decided_by": of(IntentAuthorityRef),
    "current_policy_refs": of(SemanticRef),
    "graph_ref": of(AuthorityPolicyGraphRef),
}


def meanings_agree(
    left: BriefRevision,
    right: BriefRevision,
    *,
    profile: SemanticEquivalenceProfile = DEFAULT_EQUIVALENCE_PROFILE,
) -> bool:
    """Whether two revisions carry the same normalized meaning under a declared profile (§11, §12).

    The comparison reuses the per-path digests F-M03-04 already computes rather than defining a
    second notion of "the same", so a re-worded rationale can stay equivalent while a changed
    authority cannot. Preserved raw sources are deliberately absent: §5 keeps the input separate
    from the normalized semantics, which is what makes a brief that gained a client message but no
    new statement a source-only edit rather than a redefinition.
    """

    for name, value in (("left", left), ("right", right)):
        if not isinstance(value, BriefRevision):
            raise SchemaValidationError(f"meanings_agree expects {name} to be a BriefRevision")
    if not isinstance(profile, SemanticEquivalenceProfile):
        raise SchemaValidationError("meanings_agree expects a SemanticEquivalenceProfile")
    if left.brief_id != right.brief_id:
        raise RefError(
            f"meanings_agree was asked about {left.revision_id} of {left.brief_id} and "
            f"{right.revision_id} of {right.brief_id}; two briefs may share wording without sharing "
            "a meaning, and saying they agree would compare unrelated clients"
        )
    return _path_digests(left, profile) == _path_digests(right, profile)


def _path_digests(revision: BriefRevision, profile: SemanticEquivalenceProfile) -> dict[str, str]:
    return dict(fingerprint_revision(revision, profile=profile).path_digests)


def classify_revision(
    base: BriefRevision,
    revision: BriefRevision,
    *,
    profile: SemanticEquivalenceProfile = DEFAULT_EQUIVALENCE_PROFILE,
    policy_context_changed: bool = False,
    is_merge: bool = False,
    is_restoration: bool = False,
    is_migration: bool = False,
) -> RevisionClassification:
    """Say what one admitted revision did, from the two records rather than from a commit note (§18).

    The governance hints win over the content comparison because they describe *why* the revision
    exists, and a merge that happened to reproduce the base meaning is still a merge revision —
    downstream consumers key off the reason, and §18 lists those three as history classes.

    "Meaning" is read through a versioned equivalence profile rather than off the revision's byte
    digest, because §11 and §12 make semantic equality a typed, profiled relation: a re-worded
    rationale has to be able to stay equivalent while the revision id changes. Comparing raw bytes
    here would make ``SEMANTIC_EQUIVALENT_CHANGE`` unreachable and bill downstream work for prose.
    """

    if not isinstance(base, BriefRevision) or not isinstance(revision, BriefRevision):
        raise SchemaValidationError("classify_revision expects two BriefRevision records")
    if base.brief_id != revision.brief_id:
        raise RefError(
            f"{revision.revision_id} belongs to {revision.brief_id}, not {base.brief_id}; comparing "
            "revisions across briefs would classify a different brief's meaning as unchanged"
        )
    if revision.revision_number <= base.revision_number:
        raise StaleSemanticError(
            f"{revision.revision_id} is not later than {base.revision_id}; history is append-only, so "
            "an earlier revision cannot be classified as an edit of a later one"
        )
    hints = sorted(
        name
        for name, flag in (
            ("is_merge", is_merge),
            ("is_restoration", is_restoration),
            ("is_migration", is_migration),
        )
        if flag
    )
    if len(hints) > 1:
        raise SchemaValidationError(
            f"classify_revision was told {hints} about {revision.revision_id}; one revision may not be "
            "created by two governance events at once, which is how a migration hides inside a merge"
        )
    if is_merge:
        return RevisionClassification.MERGE_REVISION
    if is_restoration:
        return RevisionClassification.RESTORATION_REVISION
    if is_migration:
        return RevisionClassification.MIGRATION_REVISION
    if not meanings_agree(base, revision, profile=profile):
        return RevisionClassification.SEMANTIC_CHANGE
    if policy_context_changed:
        return RevisionClassification.POLICY_CONTEXT_CHANGE
    if _statement_state(revision) != _statement_state(base):
        return RevisionClassification.SEMANTIC_EQUIVALENT_CHANGE
    return RevisionClassification.SOURCE_ONLY_CHANGE


def _statement_state(revision: BriefRevision) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((item.statement_id, item.digest()) for item in revision.statements))


def _overlaps(left: SemanticChange, right: SemanticChange) -> bool:
    """Whether two changes could be about one subject, across a path hierarchy (§16)."""

    if not (
        covers_path(left.semantic_path, right.semantic_path)
        or covers_path(right.semantic_path, left.semantic_path)
    ):
        return False
    mine = {item.ref_id for item in left.subject_refs}
    theirs = {item.ref_id for item in right.subject_refs}
    if not mine or not theirs:
        # A change with no subject is a statement about the path itself, so it overlaps anything
        # else that moved that path.
        return True
    return bool(mine & theirs)


def _component_id(kind: MergeComponentKind, paths: Iterable[str], subjects: Iterable[str]) -> str:
    key = content_digest(
        {"kind": kind.value, "paths": sorted(set(paths)), "subjects": sorted(set(subjects))}
    )
    return f"merge.{kind.value.lower()}.{key[:16]}"


def _subjects(changes: Iterable[SemanticChange]) -> tuple[SemanticRef, ...]:
    refs: dict[str, SemanticRef] = {}
    for item in changes:
        for ref in item.subject_refs:
            refs.setdefault(ref.text, ref)
    return tuple(sorted(refs.values(), key=lambda item: item.text))


def _component(
    kind: MergeComponentKind,
    side: MergeSide,
    changes: Iterable[SemanticChange],
    *,
    reason: str,
    extra_subjects: Iterable[SemanticRef] = (),
    readings: tuple[str | None, str | None] | None = None,
) -> MergeComponent:
    """Build one component from the changes that fell into it, keeping both readings visible.

    ``readings`` is supplied for a dispute because the two digests are not symmetric: one is what
    the left branch reads and the other is what the right does, and a component that had sorted
    them into "first" and "second" would have quietly chosen an order for the pair. It is a tuple
    rather than two keyword arguments so that ``None`` — a side that removed the path rather than
    rewriting it — stays a stated reading instead of falling back to whatever the group holds.
    """

    items = tuple(changes)
    paths = {item.semantic_path for item in items}
    subjects = _subjects(items) + tuple(extra_subjects)
    befores = sorted({item.before_digest for item in items if item.before_digest})
    afters = sorted({item.after_digest for item in items if item.after_digest})
    if readings is None:
        after = afters[0] if afters else None
        other = afters[1] if len(afters) > 1 else None
    else:
        after, other = readings
    return MergeComponent(
        component_id=_component_id(kind, paths, (item.text for item in subjects)),
        kind=kind.value,
        side=side.value,
        semantic_paths=tuple(paths),
        subject_refs=subjects,
        before_digest=befores[0] if len(befores) == 1 else None,
        after_digest=after,
        other_digest=other,
        change_kinds=tuple(sorted({item.kind for item in items})),
        reason=reason,
    )


def analyze_semantic_merge(
    *,
    analysis_id: str,
    base: BriefRevision,
    left: BriefRevision,
    right: BriefRevision,
    left_delta: IntentDelta,
    right_delta: IntentDelta,
    open_question_refs: Iterable[SemanticRef] = (),
    graph: AuthorityPolicyGraph | None = None,
    rule_classes: Mapping[str, str] | None = None,
    merged_candidate_digest: str | None = None,
    notes: str | None = None,
    metadata: Mapping[str, str] | None = None,
) -> BriefSemanticMergeAnalysis:
    """Read two branch deltas against a common base and say what may be taken (§16, proofs 13-14).

    Nothing here decides which side wins, and nothing here merges. The buckets are computed from
    the changes F-M03-04 already diffed, so the only new judgement is overlap: two changes that
    could be about one subject are compared, and two that cannot are each their own safe component.

    ``rule_classes`` is the caller's statement of which policy class governs which subject, and it
    is the only way an authority issue can be recognised here, since M03's records say what a rule
    binds rather than who owns the answer. Without it a dispute over a reserved boundary is
    reported as an ordinary conflict — under-stated, but never wrong about the mechanics, because
    both keep the candidate from existing until somebody with authority speaks.
    """

    for name, value in (("base", base), ("left", left), ("right", right)):
        if not isinstance(value, BriefRevision):
            raise SchemaValidationError(f"analyze_semantic_merge expects {name} to be a BriefRevision")
    if len({value.brief_id for value in (base, left, right)}) != 1:
        raise RefError(
            "the three revisions do not belong to one brief; a merge across briefs has no common "
            "base to compare against"
        )
    delta_left = IntentDelta.coerce(left_delta, "left_delta")
    delta_right = IntentDelta.coerce(right_delta, "right_delta")
    left_changes = tuple(delta_left.changes)
    right_changes = tuple(delta_right.changes)
    governs = dict(rule_classes or {})
    known = {item.ref_id for change in (*left_changes, *right_changes) for item in change.subject_refs}
    stray = sorted(set(governs) - known)
    if stray:
        raise RefError(
            f"rule_classes describes {stray}, which neither delta moved; a policy claim about a "
            "subject outside this merge would classify a dispute that is not here"
        )

    components: list[MergeComponent] = []
    claimed: set[int] = set()
    for one in left_changes:
        partners = [
            index for index, two in enumerate(right_changes) if index not in claimed and _overlaps(one, two)
        ]
        if not partners:
            components.append(
                _component(
                    MergeComponentKind.NON_OVERLAPPING_SAFE,
                    MergeSide.LEFT,
                    (one,),
                    reason=(
                        f"only the left side moved {one.semantic_path}; nothing on the right has to be "
                        "reconciled with it"
                    ),
                )
            )
            continue
        for index in partners:
            claimed.add(index)
        group = (one,) + tuple(right_changes[index] for index in partners)
        paths = sorted({item.semantic_path for item in group})
        if len({item.after_digest for item in group}) <= 1:
            components.append(
                _component(
                    MergeComponentKind.EQUIVALENT,
                    MergeSide.BOTH,
                    group,
                    reason=(
                        f"both sides moved {paths[0]} to the same reading, so the merge takes it once "
                        "rather than crediting either branch for it"
                    ),
                )
            )
            continue
        reserved = sorted(
            {
                governs[ref.ref_id]
                for ref in _subjects(group)
                if ref.ref_id in governs and graph is not None and graph.reserves(governs[ref.ref_id])
            }
        )
        # Reaching here means the group holds two different readings, so the pair is always
        # well-formed: `one` carries the left branch's, the first divergent partner the right's.
        readings = (
            one.after_digest,
            next((two.after_digest for two in group[1:] if two.after_digest != one.after_digest), None),
        )
        if reserved:
            components.append(
                _component(
                    MergeComponentKind.AUTHORITY_POLICY,
                    MergeSide.BOTH,
                    group,
                    readings=readings,
                    reason=(
                        f"the two sides disagree on {paths} and {reserved} is a reserved boundary, so "
                        "no merge mechanic may pick a reading here (§6)"
                    ),
                )
            )
            continue
        components.append(
            _component(
                MergeComponentKind.CONFLICTING,
                MergeSide.BOTH,
                group,
                readings=readings,
                reason=(
                    f"{paths} diverged: the left side reads it one way and the right another, and §7 "
                    "refuses to settle that by which branch was admitted later"
                ),
            )
        )
    for index, two in enumerate(right_changes):
        if index in claimed:
            continue
        components.append(
            _component(
                MergeComponentKind.NON_OVERLAPPING_SAFE,
                MergeSide.RIGHT,
                (two,),
                reason=f"only the right side moved {two.semantic_path}; the left never spoke to it",
            )
        )
    for question in bound_refs(open_question_refs, "open_question_refs", minimum=0):
        components.append(
            _component(
                MergeComponentKind.OPEN_QUESTION,
                MergeSide.BOTH,
                (),
                extra_subjects=(question,),
                reason=(
                    f"{question.ref_id} is unresolved on both sides, so the merge may not assume the "
                    "same reading twice and call it agreement"
                ),
            )
        )
    if merged_candidate_digest is None and not any(item.needs_a_decision for item in components):
        merged_candidate_digest = content_digest(
            {
                "base": base.revision_ref.text,
                "left": delta_left.delta_digest,
                "right": delta_right.delta_digest,
                "taken": sorted(
                    f"{item.side}|{path}|{item.after_digest}"
                    for item in components
                    for path in item.semantic_paths
                    if item.kind_enum.ships_in_the_candidate
                ),
            }
        )
    return BriefSemanticMergeAnalysis(
        analysis_id=analysis_id,
        brief_ref=base.brief_ref,
        base_ref=base.revision_ref,
        left_ref=left.revision_ref,
        right_ref=right.revision_ref,
        base_revision_number=base.revision_number,
        left_revision_number=left.revision_number,
        right_revision_number=right.revision_number,
        left_delta=delta_left,
        right_delta=delta_right,
        components=tuple(components),
        merged_candidate_digest=merged_candidate_digest,
        graph_ref=None if graph is None else graph.pin(),
        notes=notes,
        metadata=metadata or {},
    )


def restore_revision(
    *,
    restoration_id: str,
    new_revision: BriefRevision,
    restores_from: BriefRevision,
    decided_by: IntentAuthorityRef,
    reason: str,
    current_policy_refs: Iterable[SemanticRef],
    recompiled_with: Mapping[str, str],
    graph: AuthorityPolicyGraph | None = None,
    profile: SemanticEquivalenceProfile = DEFAULT_EQUIVALENCE_PROFILE,
    notes: str | None = None,
    metadata: Mapping[str, str] | None = None,
) -> RestorationRevision:
    """Admit a restoration as a forward revision under today's policy (§21, proof 18).

    Three refusals are the whole point. A "restoration" that changes meaning is an edit and has to
    be filed as one, or the audit trail credits the older revision with a change nobody admitted. A
    restoration whose authority is a model's own assertion is §24's violation with a better name, so
    the actor has to hold a position that self-asserting is enough for. And a restoration that
    declares the profile it recompiled under has to mean the one this comparison used, or the record
    documents a reading it did not perform.

    Meaning, not byte equality, is the test: history has moved since the revision being restored, so
    its successor legitimately carries newer raw inputs and a longer ancestor chain while restoring
    exactly the normalized statements.
    """

    for name, value in (("new_revision", new_revision), ("restores_from", restores_from)):
        if not isinstance(value, BriefRevision):
            raise SchemaValidationError(f"restore_revision expects {name} to be a BriefRevision")
    if new_revision.brief_id != restores_from.brief_id:
        raise RefError(
            f"cannot restore {restores_from.revision_id} of {restores_from.brief_id} into "
            f"{new_revision.brief_id}; a brief may only return to its own meaning"
        )
    if new_revision.revision_number <= restores_from.revision_number:
        raise StaleSemanticError(
            f"restoration {restoration_id} writes revision {new_revision.revision_number} to restore "
            f"{restores_from.revision_number}; history is append-only, so restoring means coming after"
        )
    declared = dict(recompiled_with or {})
    if declared.get("profile") not in (None, profile.version):
        raise SchemaValidationError(
            f"restoration {restoration_id} says it recompiled under profile {declared['profile']} but "
            f"this one compared the two revisions under {profile.version}; the receipt would document "
            "an equivalence reading it did not perform"
        )
    if not meanings_agree(new_revision, restores_from, profile=profile):
        raise SchemaValidationError(
            f"{new_revision.revision_id} does not mean what {restores_from.revision_id} meant under "
            f"profile {profile.version}, so it is an edit rather than a restoration"
        )
    level = decided_by.level
    if not level.self_asserting_is_enough:
        raise AuthorityError(
            f"{level.value} may not restore a prior meaning on its own assertion (§24); restoration "
            "reopens what the brief says and needs governed policy or the human owner"
        )
    return RestorationRevision(
        restoration_id=restoration_id,
        brief_ref=new_revision.brief_ref,
        new_revision_ref=new_revision.revision_ref,
        restores_from=restores_from.revision_ref,
        reason=reason,
        decided_by=decided_by,
        current_policy_refs=current_policy_refs,
        recompiled_with=recompiled_with,
        graph_ref=None if graph is None else graph.pin(),
        notes=notes,
        metadata=metadata or {},
    )
