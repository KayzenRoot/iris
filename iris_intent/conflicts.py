"""F-M03-15/16 S05 semantic conflicts: detection, resolution records, slicing and fingerprints.

This module exists to make one sentence structural rather than aspirational: *detecting a
conflict does not decide it* (§1, D-M03-S05-001). A conflict here is a first-class, versioned
object holding both sides, the scope where they meet, the authority behind each side, and the
candidate ways out — and it carries no winner, because the only thing in M03 that names a
winner is a resolution record backed by a receipt or a human decision ref.

Two temptations are refused by construction rather than by review. The first is a scalar
priority: nothing here ranks two parties by strength, specificity or recency, because §7 says a
later timestamp is never sufficient authority and §5 says confidence is not authority. The
second is the quiet resolution, so the states that close a conflict each demand their evidence:
an override needs the receipt, a policy resolution needs the policy pin it was decided under, a
scope split needs the branch that keeps *both* rules, and a fork needs the variant proposal that
M02 — not M03 — will own.

Detection is deliberately conservative. A pair of rules becomes a conflict only when the kernel
can state, from the records themselves, why they cannot both be satisfied; everything else is
left as a preference the work has to negotiate, because a detector that reports ambiguity it
cannot name spends the one resource a compiler has, which is the reviewer's trust.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from .ambiguity import AmbiguityAssessment
from .authority import (
    AuthorityLevel,
    AuthorityPolicyEdge,
    AuthorityPolicyGraph,
    AuthorityPolicyGraphRef,
    OverrideAction,
)
from .base import Labeled, Record, of
from .constraints import (
    Comparison,
    Condition,
    ConsistencyClass,
    Constraint,
    ConstraintBundle,
    ConstraintPolarity,
    ConstraintScope,
    ProtectedAnchor,
    ToleranceEnvelope,
)
from .errors import (
    AuthorityError,
    ConflictBlockedError,
    LimitExceededError,
    OverrideRefusedError,
    RefError,
    SchemaValidationError,
    ScopeError,
    StaleSemanticError,
)
from .identity import RefKind, SemanticRef, require_bound_ref
from .intent import IntentAuthorityRef, IntentModel
from .limits import (
    MAX_CONDITIONS,
    MAX_CONFLICT_PARTIES,
    MAX_CONFLICTS,
    MAX_RATIONALE_CHARS,
    MAX_SCOPE_PATHS,
    MAX_TEXT_CHARS,
)
from .overrides import (
    OverrideReceipt,
    bound_paths,
    bound_refs,
    covers_path,
    invalidation_targets,
)
from .slicing import MinimumSufficientSemanticSlice, SlicePurpose
from .sources import bounded_metadata
from .versions import (
    CONTRACT_VERSION,
    SCHEMA_VERSION,
    content_digest,
    require_contract_version,
    require_identifier,
    require_semantic_path,
    require_text,
    require_version_text,
)

__all__ = [
    "CONFLICT_COMPILER_VERSION",
    "MIN_PARTIES",
    "CandidateResolution",
    "ConflictClass",
    "ConflictConsequence",
    "ConflictResolutionFingerprint",
    "ConflictResolution",
    "ConflictResolutionState",
    "ExplorationFork",
    "ForkVariant",
    "MinimumSufficientConflictSlice",
    "ScopeSplitProposal",
    "SemanticConflict",
    "SplitBranch",
    "clarification_plan",
    "declare_conflict",
    "detect_conflicts",
    "escalate_conflict",
    "rank_conflicts",
    "resolve_conflict",
]

CONFLICT_COMPILER_VERSION = "m03-conflict-v1"

#: A conflict is about at least two things; one party is a note.
MIN_PARTIES = 2
#: Candidate ways out, capped so a conflict cannot host a decision tree nobody approved.
MAX_CANDIDATES = 16


class ConflictConsequence(Labeled):
    """What is at stake if the conflict stays open — not a score (§4).

    There is no numeric severity here on purpose. §4 says a conflict's consequence is not a
    universal number, and a single scalar invites the reader to trade a rights boundary against
    a cost, which is a comparison no policy admits. Each consequence instead carries the two
    booleans anything downstream actually needs: does this stop a contract being emitted, and
    does closing it require an authority M03 does not hold.
    """

    BLOCKING = "BLOCKING"
    QUALITY_CRITICAL = "QUALITY_CRITICAL"
    RIGHTS_SECURITY_CRITICAL = "RIGHTS_SECURITY_CRITICAL"
    COST_CRITICAL = "COST_CRITICAL"
    NON_BLOCKING = "NON_BLOCKING"
    EXPLORATION_FORK = "EXPLORATION_FORK"

    @property
    def blocks_contract(self) -> bool:
        """Whether no admitted contract or execution intent may be emitted while it is open.

        Quality and cost consequences are deliberately excluded: they can be carried under an
        explicit decision, and calling them blockers would push teams to delete the conflict
        record rather than accept it in writing.
        """

        return self in {
            ConflictConsequence.BLOCKING,
            ConflictConsequence.RIGHTS_SECURITY_CRITICAL,
        }

    @property
    def requires_authorized_resolution(self) -> bool:
        """Whether only a policy or human authority may close it, never compatibility."""

        return self is ConflictConsequence.RIGHTS_SECURITY_CRITICAL

    @property
    def release_blocking_by_default(self) -> bool:
        return self in {
            ConflictConsequence.BLOCKING,
            ConflictConsequence.RIGHTS_SECURITY_CRITICAL,
            ConflictConsequence.QUALITY_CRITICAL,
        }

    #: The order conflicts are reported in. Presentation only: never a tie-break for a winner.
    @property
    def report_rank(self) -> int:
        return _CONSEQUENCE_RANK[self]


_CONSEQUENCE_RANK: Mapping[ConflictConsequence, int] = MappingProxyType({
    ConflictConsequence.RIGHTS_SECURITY_CRITICAL: 0,
    ConflictConsequence.BLOCKING: 1,
    ConflictConsequence.QUALITY_CRITICAL: 2,
    ConflictConsequence.COST_CRITICAL: 3,
    ConflictConsequence.EXPLORATION_FORK: 4,
    ConflictConsequence.NON_BLOCKING: 5,
})

#: Weakening a conflict below its class default is the one direction of editing that is refused.
_CONSEQUENCE_SEVERITY: Mapping[ConflictConsequence, int] = MappingProxyType({
    ConflictConsequence.NON_BLOCKING: 0,
    ConflictConsequence.EXPLORATION_FORK: 1,
    ConflictConsequence.COST_CRITICAL: 2,
    ConflictConsequence.QUALITY_CRITICAL: 3,
    ConflictConsequence.RIGHTS_SECURITY_CRITICAL: 4,
    ConflictConsequence.BLOCKING: 4,
})


class ConflictResolutionState(Labeled):
    """How a conflict stopped being open (§13).

    Each state names the evidence that justifies it, and the record refuses a state whose
    evidence is missing. "SUPERSEDED" with no successor and "RESOLVED_BY_EXPLICIT_OVERRIDE"
    with no receipt are both ways of making a conflict disappear on paper, which is the failure
    §13's immutability requirement exists to prevent.
    """

    UNRESOLVED = "UNRESOLVED"
    RESOLVED_BY_COMPATIBILITY = "RESOLVED_BY_COMPATIBILITY"
    RESOLVED_BY_AUTHORITY_POLICY = "RESOLVED_BY_AUTHORITY_POLICY"
    RESOLVED_BY_EXPLICIT_OVERRIDE = "RESOLVED_BY_EXPLICIT_OVERRIDE"
    RESOLVED_BY_SCOPE_SPLIT = "RESOLVED_BY_SCOPE_SPLIT"
    RESOLVED_AS_EXPLORATION_FORK = "RESOLVED_AS_EXPLORATION_FORK"
    NEEDS_HUMAN_DECISION = "NEEDS_HUMAN_DECISION"
    BLOCKED_UNOVERRIDABLE = "BLOCKED_UNOVERRIDABLE"
    SUPERSEDED = "SUPERSEDED"

    @property
    def is_resolved(self) -> bool:
        return self not in {
            ConflictResolutionState.UNRESOLVED,
            ConflictResolutionState.NEEDS_HUMAN_DECISION,
            ConflictResolutionState.BLOCKED_UNOVERRIDABLE,
        }

    @property
    def leaves_work_blocked(self) -> bool:
        """Whether a consumer may treat the semantics as settled.

        ``SUPERSEDED`` counts as settled because a successor carries the decision forward;
        ``BLOCKED_UNOVERRIDABLE`` never does, because nothing downstream may talk its way past
        a reserved boundary.
        """

        return self in {
            ConflictResolutionState.UNRESOLVED,
            ConflictResolutionState.NEEDS_HUMAN_DECISION,
            ConflictResolutionState.BLOCKED_UNOVERRIDABLE,
        }

    @property
    def requires_receipt(self) -> bool:
        return self is ConflictResolutionState.RESOLVED_BY_EXPLICIT_OVERRIDE

    @property
    def requires_policy_pin(self) -> bool:
        return self in {
            ConflictResolutionState.RESOLVED_BY_AUTHORITY_POLICY,
            ConflictResolutionState.RESOLVED_BY_EXPLICIT_OVERRIDE,
        }

    @property
    def keeps_both_rules(self) -> bool:
        """The two states where nothing is deleted because nothing had to be (§14)."""

        return self in {
            ConflictResolutionState.RESOLVED_BY_SCOPE_SPLIT,
            ConflictResolutionState.RESOLVED_AS_EXPLORATION_FORK,
        }


class ConflictClass(Labeled):
    """The fourteen incompatibilities §3 names, each with its default stake and its exits.

    ``default_consequence`` and ``admissible_resolutions`` live on the class rather than being
    supplied per conflict so that filing a rights conflict as ``NON_BLOCKING``, or closing one
    with "the two rules just happen to fit", is not a thing a record can do. Both fields are
    floors and gates, never a priority order: they say what must be true of a resolution, and
    the graph still decides who may grant it.
    """

    DIRECT_CONTRADICTION = "DIRECT_CONTRADICTION"
    VALUE_INCOMPATIBILITY = "VALUE_INCOMPATIBILITY"
    EMPTY_RANGE = "EMPTY_RANGE"
    CARDINALITY_CONFLICT = "CARDINALITY_CONFLICT"
    SCOPE_COLLISION = "SCOPE_COLLISION"
    CONDITIONAL_COLLISION = "CONDITIONAL_COLLISION"
    REFERENCE_CONFLICT = "REFERENCE_CONFLICT"
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    QUALITY_POLICY_CONFLICT = "QUALITY_POLICY_CONFLICT"
    RIGHTS_SECURITY_CONFLICT = "RIGHTS_SECURITY_CONFLICT"
    CROSS_MODAL_CONFLICT = "CROSS_MODAL_CONFLICT"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    STALE_DERIVATION = "STALE_DERIVATION"
    AMBIGUITY_COLLISION = "AMBIGUITY_COLLISION"

    @property
    def default_consequence(self) -> ConflictConsequence:
        return _CLASS_CONSEQUENCE[self]

    @property
    def admissible_resolutions(self) -> frozenset[ConflictResolutionState]:
        """The exits this incompatibility can honestly take.

        ``BLOCKED_UNOVERRIDABLE`` and ``NEEDS_HUMAN_DECISION`` are admissible for every class: a
        conflict may always be escalated or refused, and it is the *closing* moves that are
        gated. Compatibility is not offered where the two sides are not actually satisfiable
        together, and a fork is not offered for a rights boundary because a fork ships both.
        """

        return _CLASS_RESOLUTIONS[self]

    @property
    def detected_by_kernel(self) -> bool:
        """Whether :func:`detect_conflicts` finds this class from M03's own records.

        The two that answer ``False`` are ``QUALITY_POLICY_CONFLICT`` (which needs M01's
        registry to know whether obligations can coexist) and ``RIGHTS_SECURITY_CONFLICT``
        (which needs M53/M54). They are still first-class objects here, and
        :func:`declare_conflict` is the only way in: a conflict the kernel cannot derive has to
        arrive with the evidence of whoever could.
        """

        return self in _KERNEL_DETECTED

    @property
    def about_identity(self) -> bool:
        return self in {ConflictClass.IDENTITY_CONFLICT, ConflictClass.CROSS_MODAL_CONFLICT}


_CLASS_CONSEQUENCE: Mapping[ConflictClass, ConflictConsequence] = MappingProxyType({
    ConflictClass.DIRECT_CONTRADICTION: ConflictConsequence.BLOCKING,
    ConflictClass.VALUE_INCOMPATIBILITY: ConflictConsequence.QUALITY_CRITICAL,
    ConflictClass.EMPTY_RANGE: ConflictConsequence.BLOCKING,
    ConflictClass.CARDINALITY_CONFLICT: ConflictConsequence.BLOCKING,
    ConflictClass.SCOPE_COLLISION: ConflictConsequence.NON_BLOCKING,
    ConflictClass.CONDITIONAL_COLLISION: ConflictConsequence.NON_BLOCKING,
    ConflictClass.REFERENCE_CONFLICT: ConflictConsequence.QUALITY_CRITICAL,
    ConflictClass.IDENTITY_CONFLICT: ConflictConsequence.BLOCKING,
    ConflictClass.QUALITY_POLICY_CONFLICT: ConflictConsequence.QUALITY_CRITICAL,
    ConflictClass.RIGHTS_SECURITY_CONFLICT: ConflictConsequence.RIGHTS_SECURITY_CRITICAL,
    ConflictClass.CROSS_MODAL_CONFLICT: ConflictConsequence.QUALITY_CRITICAL,
    ConflictClass.VERSION_CONFLICT: ConflictConsequence.COST_CRITICAL,
    ConflictClass.STALE_DERIVATION: ConflictConsequence.COST_CRITICAL,
    ConflictClass.AMBIGUITY_COLLISION: ConflictConsequence.EXPLORATION_FORK,
})

_ALL_EXITS = frozenset(
    {
        ConflictResolutionState.RESOLVED_BY_COMPATIBILITY,
        ConflictResolutionState.RESOLVED_BY_AUTHORITY_POLICY,
        ConflictResolutionState.RESOLVED_BY_EXPLICIT_OVERRIDE,
        ConflictResolutionState.RESOLVED_BY_SCOPE_SPLIT,
        ConflictResolutionState.RESOLVED_AS_EXPLORATION_FORK,
    }
)
_ESCALATION = frozenset(
    {
        ConflictResolutionState.UNRESOLVED,
        ConflictResolutionState.NEEDS_HUMAN_DECISION,
        ConflictResolutionState.BLOCKED_UNOVERRIDABLE,
        ConflictResolutionState.SUPERSEDED,
    }
)

_CLASS_RESOLUTIONS: Mapping[ConflictClass, frozenset[ConflictResolutionState]] = MappingProxyType({
    # Two rules that cannot both hold have no compatibility reading; only authority decides.
    ConflictClass.DIRECT_CONTRADICTION: _ALL_EXITS
    - {ConflictResolutionState.RESOLVED_BY_COMPATIBILITY, ConflictResolutionState.RESOLVED_AS_EXPLORATION_FORK}
    | _ESCALATION,
    ConflictClass.VALUE_INCOMPATIBILITY: _ALL_EXITS
    - {ConflictResolutionState.RESOLVED_BY_COMPATIBILITY}
    | _ESCALATION,
    ConflictClass.EMPTY_RANGE: _ALL_EXITS
    - {ConflictResolutionState.RESOLVED_BY_COMPATIBILITY}
    | _ESCALATION,
    ConflictClass.CARDINALITY_CONFLICT: _ALL_EXITS
    - {ConflictResolutionState.RESOLVED_BY_COMPATIBILITY}
    | _ESCALATION,
    ConflictClass.SCOPE_COLLISION: _ALL_EXITS | _ESCALATION,
    ConflictClass.CONDITIONAL_COLLISION: _ALL_EXITS | _ESCALATION,
    ConflictClass.REFERENCE_CONFLICT: _ALL_EXITS
    - {ConflictResolutionState.RESOLVED_BY_COMPATIBILITY}
    | _ESCALATION,
    # Identity anchors are the clearest case of "a fork is not a resolution": two faces.
    ConflictClass.IDENTITY_CONFLICT: _ALL_EXITS
    - {
        ConflictResolutionState.RESOLVED_BY_COMPATIBILITY,
        ConflictResolutionState.RESOLVED_AS_EXPLORATION_FORK,
    }
    | _ESCALATION,
    ConflictClass.QUALITY_POLICY_CONFLICT: _ALL_EXITS
    - {ConflictResolutionState.RESOLVED_BY_COMPATIBILITY}
    | _ESCALATION,
    # Rights and security boundaries may be met by policy or a receipt, never by splitting.
    ConflictClass.RIGHTS_SECURITY_CONFLICT: frozenset(
        {
            ConflictResolutionState.RESOLVED_BY_AUTHORITY_POLICY,
            ConflictResolutionState.RESOLVED_BY_EXPLICIT_OVERRIDE,
        }
    )
    | _ESCALATION,
    ConflictClass.CROSS_MODAL_CONFLICT: _ALL_EXITS
    - {ConflictResolutionState.RESOLVED_BY_COMPATIBILITY}
    | _ESCALATION,
    ConflictClass.VERSION_CONFLICT: _ALL_EXITS | _ESCALATION,
    ConflictClass.STALE_DERIVATION: _ALL_EXITS | _ESCALATION,
    ConflictClass.AMBIGUITY_COLLISION: _ALL_EXITS | _ESCALATION,
})

_KERNEL_DETECTED = frozenset(
    {
        ConflictClass.DIRECT_CONTRADICTION,
        ConflictClass.VALUE_INCOMPATIBILITY,
        ConflictClass.EMPTY_RANGE,
        ConflictClass.CARDINALITY_CONFLICT,
        ConflictClass.SCOPE_COLLISION,
        ConflictClass.CONDITIONAL_COLLISION,
        ConflictClass.REFERENCE_CONFLICT,
        ConflictClass.IDENTITY_CONFLICT,
        ConflictClass.CROSS_MODAL_CONFLICT,
        ConflictClass.VERSION_CONFLICT,
        ConflictClass.STALE_DERIVATION,
        ConflictClass.AMBIGUITY_COLLISION,
    }
)

#: Measures whose empty intersection is a count problem, not a range problem (§3).
_CARDINALITY_MEASURES = frozenset({"count", "duration_frames", "frame_count", "item_count"})


def _texts(value: Any, name: str, *, limit: int = MAX_SCOPE_PATHS) -> tuple[str, ...]:
    """A bounded, order-stable set of identifiers — refs and ids alike."""

    items = tuple(value or ())
    if len(items) > limit:
        raise LimitExceededError(f"{name} exceeds {limit} entries")
    return tuple(sorted({require_text(item, f"{name}[]", maximum=512) for item in items}))


def _digest_text(value: Any, name: str) -> str:
    text = require_text(value, name, maximum=128)
    if len(text) not in (8, 16, 32, 40, 64, 128) or any(character not in "0123456789abcdef" for character in text.lower()):
        raise SchemaValidationError(f"{name} is not a canonical hex digest, got {value!r}")
    return text.lower()


def _candidates(
    value: Any, conflict_class: ConflictClass | None, *, parties: tuple[SemanticRef, ...] = ()
) -> tuple[CandidateResolution, ...]:
    """Coerce the ways out, and refuse an exit this class cannot take (§13)."""

    items = tuple(
        sorted(
            (CandidateResolution.coerce(item, "candidates[]") for item in (value or ())),
            key=lambda item: item.candidate_id,
        )
    )
    if len(items) > MAX_CANDIDATES:
        raise LimitExceededError(f"candidates exceeds {MAX_CANDIDATES} entries")
    ids = [item.candidate_id for item in items]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        raise SchemaValidationError(f"candidates repeats candidate ids {duplicates}")
    if conflict_class is not None:
        admitted = conflict_class.admissible_resolutions
        for item in items:
            if item.produces_state not in admitted:
                raise ConflictBlockedError(
                    f"candidate {item.candidate_id} would produce {item.produces}, which §13 does not "
                    f"offer for a {conflict_class.value}; a list of ways out that includes an impossible "
                    "one teaches the reader that the list was not made by whoever owns the question"
                )
    if parties:
        named = {item.text for item in parties}
        for item in items:
            stray = sorted({reference.text for reference in item.party_refs} - named)
            if stray:
                raise RefError(
                    f"candidate {item.candidate_id} offers to move {stray}, which is not a party to this "
                    "conflict; deciding for an absent rule is the quiet resolution this module exists to "
                    "refuse"
                )
    return items


@dataclass(frozen=True)
class SplitBranch(Record):
    """One side of a scope split: a narrower world in which one party holds (§14).

    A branch is not a resolution by itself — it becomes one only when every party lands in
    exactly one branch, which is what makes "we split it" different from "we dropped one".
    """

    branch_id: str
    scope: ConstraintScope
    party_refs: tuple[SemanticRef, ...] = ()
    label: str | None = None
    rationale: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch_id", require_identifier(self.branch_id, "branch_id"))
        object.__setattr__(self, "scope", ConstraintScope.coerce(self.scope, "scope"))
        object.__setattr__(self, "party_refs", bound_refs(self.party_refs, "party_refs"))
        if self.label is not None:
            object.__setattr__(self, "label", require_text(self.label, "label", maximum=128))
        if self.rationale is not None:
            object.__setattr__(
                self, "rationale", require_text(self.rationale, "rationale", maximum=MAX_RATIONALE_CHARS)
            )

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "scope": self.scope.to_payload(),
            "parties": sorted(item.text for item in self.party_refs),
        }


SplitBranch.NESTED = {"scope": of(ConstraintScope), "party_refs": of(SemanticRef)}


@dataclass(frozen=True)
class ScopeSplitProposal(Record):
    """A proposed partition of scope in which each rule keeps force in one region (§14).

    The invariant is exact coverage: every party in exactly one branch, no branch empty, and no
    party left out. Those three checks are the whole difference between a split and a silent
    deletion, and they are cheap enough to run on every construction.
    """

    split_id: str
    branches: tuple[SplitBranch, ...] = ()
    rationale: str | None = None
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    #: §14: a split is a proposal about semantics; M02 owns the branch topology that carries it.
    decides_authority = False
    m02_owns_topology = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "split_id", require_identifier(self.split_id, "split_id"))
        branches = tuple(
            sorted(
                (SplitBranch.coerce(item, "branches[]") for item in (self.branches or ())),
                key=lambda item: item.branch_id,
            )
        )
        if len(branches) < 2:
            raise ScopeError(
                f"split {self.split_id} has {len(branches)} branch(es); one branch is a rename of "
                "the original scope, not a partition of it"
            )
        if len(branches) > MAX_SCOPE_PATHS:
            raise LimitExceededError(f"branches exceeds {MAX_SCOPE_PATHS} entries")
        ids = [item.branch_id for item in branches]
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            raise SchemaValidationError(f"branches repeats branch ids {duplicates}")
        for branch in branches:
            if not branch.party_refs:
                raise ScopeError(
                    f"branch {branch.branch_id} holds no party; an empty region is where a rule goes "
                    "to be forgotten without anyone saying so"
                )
        seen: dict[str, list[str]] = {}
        for branch in branches:
            for party in branch.party_refs:
                seen.setdefault(party.text, []).append(branch.branch_id)
        doubled = sorted({ref: where for ref, where in seen.items() if len(where) > 1})
        if doubled:
            raise ScopeError(
                f"split {self.split_id} places {doubled} in more than one branch; a party bound "
                "twice is a conflict that was restated rather than split"
            )
        object.__setattr__(self, "branches", branches)
        if self.rationale is not None:
            object.__setattr__(
                self, "rationale", require_text(self.rationale, "rationale", maximum=MAX_RATIONALE_CHARS)
            )
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=MAX_TEXT_CHARS))
        object.__setattr__(self, "metadata", bounded_metadata(dict(self.metadata or {}), "metadata"))

    @property
    def party_refs(self) -> tuple[SemanticRef, ...]:
        return tuple(
            sorted({item for branch in self.branches for item in branch.party_refs}, key=lambda item: item.text)
        )

    @property
    def deletes_either_rule(self) -> bool:
        """Always false: coverage is checked, so there is no way to build a split that drops a rule."""

        return False

    def covers(self, party: SemanticRef) -> bool:
        wanted = require_bound_ref(party, "party").text
        return any(wanted == item.text for item in self.party_refs)

    def branch_of(self, party: SemanticRef) -> SplitBranch | None:
        wanted = require_bound_ref(party, "party").text
        for branch in self.branches:
            if any(wanted == item.text for item in branch.party_refs):
                return branch
        return None

    def fingerprint_inputs(self) -> list[Any]:
        return [item.fingerprint_inputs() for item in self.branches]


ScopeSplitProposal.NESTED = {"branches": of(SplitBranch)}


@dataclass(frozen=True)
class ForkVariant(Record):
    """One branch of an exploration fork: a reading kept alive rather than decided (§14)."""

    variant_id: str
    party_refs: tuple[SemanticRef, ...] = ()
    scope: ConstraintScope | None = None
    m02_variant_ref: SemanticRef | None = None
    label: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "variant_id", require_identifier(self.variant_id, "variant_id"))
        object.__setattr__(self, "party_refs", bound_refs(self.party_refs, "party_refs"))
        if self.scope is not None:
            object.__setattr__(self, "scope", ConstraintScope.coerce(self.scope, "scope"))
        if self.m02_variant_ref is not None:
            object.__setattr__(
                self,
                "m02_variant_ref",
                require_bound_ref(self.m02_variant_ref, "m02_variant_ref", kind=RefKind.M02_VARIANT),
            )
        if self.label is not None:
            object.__setattr__(self, "label", require_text(self.label, "label", maximum=128))

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "parties": sorted(item.text for item in self.party_refs),
            "m02_variant_ref": None if self.m02_variant_ref is None else self.m02_variant_ref.text,
        }


ForkVariant.NESTED = {"party_refs": of(SemanticRef), "scope": of(ConstraintScope), "m02_variant_ref": of(SemanticRef)}


@dataclass(frozen=True)
class ExplorationFork(Record):
    """Two incompatible intents kept as separate creative branches, decided by work not by policy.

    A fork is the one resolution that deliberately leaves the question open, so it carries
    ``decides_winner = False`` as a constant: the moment a fork is read as a decision, the
    conflict it exists to preserve has been resolved by filing.
    """

    fork_id: str
    variants: tuple[ForkVariant, ...] = ()
    m02_branch_ref: SemanticRef | None = None
    review_condition: str | None = None
    rationale: str | None = None
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    decides_winner = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "fork_id", require_identifier(self.fork_id, "fork_id"))
        variants = tuple(
            sorted(
                (ForkVariant.coerce(item, "variants[]") for item in (self.variants or ())),
                key=lambda item: item.variant_id,
            )
        )
        if len(variants) < MIN_PARTIES:
            raise ScopeError(
                f"fork {self.fork_id} holds {len(variants)} variant(s); one branch is a decision "
                "wearing a fork's name"
            )
        if len(variants) > MAX_CONFLICT_PARTIES:
            raise LimitExceededError(f"variants exceeds {MAX_CONFLICT_PARTIES} entries")
        ids = [item.variant_id for item in variants]
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            raise SchemaValidationError(f"variants repeats variant ids {duplicates}")
        object.__setattr__(self, "variants", variants)
        if self.m02_branch_ref is not None:
            object.__setattr__(
                self,
                "m02_branch_ref",
                require_bound_ref(self.m02_branch_ref, "m02_branch_ref", kind=RefKind.M02_BRANCH),
            )
        if self.review_condition is not None:
            object.__setattr__(
                self, "review_condition", require_text(self.review_condition, "review_condition", maximum=512)
            )
        if self.rationale is not None:
            object.__setattr__(
                self, "rationale", require_text(self.rationale, "rationale", maximum=MAX_RATIONALE_CHARS)
            )
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=MAX_TEXT_CHARS))
        object.__setattr__(self, "metadata", bounded_metadata(dict(self.metadata or {}), "metadata"))

    @property
    def party_refs(self) -> tuple[SemanticRef, ...]:
        return tuple(
            sorted({item for variant in self.variants for item in variant.party_refs}, key=lambda item: item.text)
        )

    def fingerprint_inputs(self) -> list[Any]:
        return [item.fingerprint_inputs() for item in self.variants]


ExplorationFork.NESTED = {"variants": of(ForkVariant), "m02_branch_ref": of(SemanticRef)}


@dataclass(frozen=True)
class CandidateResolution(Record):
    """A way out that somebody with authority could choose (§2 candidate resolutions).

    Candidates are proposals in the strict sense: each one names the state it would produce and
    the evidence that state demands, so the question a reviewer answers is "which of these may I
    authorise", never "what would closing this even mean". ``preview`` asks the graph what the
    *candidate's* actor may do, and nothing about constructing a candidate changes a record.
    """

    candidate_id: str
    produces: str
    summary: str
    party_refs: tuple[SemanticRef, ...] = ()
    override_action: str | None = None
    receipt_ref: SemanticRef | None = None
    scope_split: ScopeSplitProposal | None = None
    fork: ExplorationFork | None = None
    human_decision: SemanticRef | None = None
    actor: IntentAuthorityRef | None = None
    invalidated: tuple[str, ...] = ()
    cost_hint: str | None = None
    rationale: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    #: A candidate is a description of a possible decision, never the decision.
    effective = False
    approved = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_id", require_identifier(self.candidate_id, "candidate_id"))
        state = ConflictResolutionState.parse(self.produces, "produces")
        object.__setattr__(self, "produces", state.value)
        if not state.is_resolved:
            raise SchemaValidationError(
                f"candidate {self.candidate_id} would produce {state.value}, which leaves the conflict "
                "open; an option that resolves nothing is not a choice"
            )
        object.__setattr__(self, "summary", require_text(self.summary, "summary", maximum=MAX_RATIONALE_CHARS))
        object.__setattr__(self, "party_refs", bound_refs(self.party_refs, "party_refs", minimum=0))
        if state is ConflictResolutionState.RESOLVED_BY_EXPLICIT_OVERRIDE:
            if self.override_action is None:
                raise SchemaValidationError(
                    f"candidate {self.candidate_id} resolves by override without naming the action; "
                    "the gradient is per-action, so an unlabelled relaxation cannot be checked"
                )
            action = OverrideAction.parse(self.override_action, "override_action")
            object.__setattr__(self, "override_action", action.value)
        elif self.override_action is not None:
            raise SchemaValidationError(
                f"candidate {self.candidate_id} names an override action but resolves by {state.value}"
            )
        if state.keeps_both_rules:
            if state is ConflictResolutionState.RESOLVED_BY_SCOPE_SPLIT and self.scope_split is None:
                raise SchemaValidationError(
                    f"candidate {self.candidate_id} claims a scope split with no branches; §14's split "
                    "has to show where each rule keeps force or it is a deletion"
                )
            if state is ConflictResolutionState.RESOLVED_AS_EXPLORATION_FORK and self.fork is None:
                raise SchemaValidationError(
                    f"candidate {self.candidate_id} claims a fork with no variants"
                )
        else:
            if self.scope_split is not None or self.fork is not None:
                raise SchemaValidationError(
                    f"candidate {self.candidate_id} resolves by {state.value} while carrying a split or "
                    "fork; two shapes of resolution in one option makes the record ambiguous"
                )
        for name, kind in (("receipt_ref", RefKind.RECEIPT), ("human_decision", RefKind.REVISION)):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_bound_ref(value, name, kind=kind))
        if self.actor is not None:
            object.__setattr__(self, "actor", IntentAuthorityRef.coerce(self.actor, "actor"))
        object.__setattr__(self, "invalidated", invalidation_targets(self.invalidated, "invalidated"))
        if self.cost_hint is not None:
            object.__setattr__(self, "cost_hint", require_text(self.cost_hint, "cost_hint", maximum=256))
        if self.rationale is not None:
            object.__setattr__(
                self, "rationale", require_text(self.rationale, "rationale", maximum=MAX_RATIONALE_CHARS)
            )
        object.__setattr__(self, "metadata", bounded_metadata(dict(self.metadata or {}), "metadata"))

    @property
    def produces_state(self) -> ConflictResolutionState:
        return ConflictResolutionState.parse(self.produces)

    @property
    def needs_authority(self) -> bool:
        """Whether honouring this candidate needs a decision from outside the conflict record.

        Compatibility is the one exit that asks for no authority: two rules that can both be
        satisfied need nobody's permission to keep being satisfied. Everything else — an
        override, a policy win, a split, a fork — changes which obligations bind which subjects,
        and so belongs to an actor the admitted graph accepts.
        """

        return self.produces_state is not ConflictResolutionState.RESOLVED_BY_COMPATIBILITY

    @property
    def self_executable(self) -> bool:
        """Always false: no candidate can be applied by the thing that listed it."""

        return False

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "produces": self.produces,
            "override_action": self.override_action,
            "parties": sorted(item.text for item in self.party_refs),
            "receipt_ref": None if self.receipt_ref is None else self.receipt_ref.text,
            "split": None if self.scope_split is None else self.scope_split.fingerprint_inputs(),
            "fork": None if self.fork is None else self.fork.fingerprint_inputs(),
        }


CandidateResolution.NESTED = {
    "party_refs": of(SemanticRef),
    "receipt_ref": of(SemanticRef),
    "human_decision": of(SemanticRef),
    "actor": of(IntentAuthorityRef),
    "scope_split": of(ScopeSplitProposal),
    "fork": of(ExplorationFork),
}


@dataclass(frozen=True)
class ConflictResolution(Record):
    """The record that a conflict stopped being open, and on what grounds (§13).

    §13 requires resolution records to be immutable and versioned, and the shape here follows
    from that: every exit names its own evidence, so "resolved" is never a field somebody typed.
    An override cites the receipt, a policy win cites the policy pin it was decided under, a
    split cites its branches and a fork cites its variants. What is deliberately absent is a
    `winner` field — the parties stay in the conflict, and the record says which *state* was
    adopted, not which rule was deleted.
    """

    resolution_id: str
    conflict_ref: SemanticRef
    state: str
    rationale: str
    decided_by: IntentAuthorityRef | None = None
    recorded_in_revision: SemanticRef | None = None
    receipt_ref: SemanticRef | None = None
    human_decision: SemanticRef | None = None
    graph_ref: AuthorityPolicyGraphRef | None = None
    scope_split: ScopeSplitProposal | None = None
    fork: ExplorationFork | None = None
    superseded_by: SemanticRef | None = None
    candidate_id: str | None = None
    evidence_refs: tuple[SemanticRef, ...] = ()
    compiler_version: str = CONFLICT_COMPILER_VERSION
    schema_version: str = SCHEMA_VERSION
    contract_version: str = ""
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    #: §24: recording a resolution is an act of authority, so a proposal cannot do it.
    self_approved = False
    deletes_a_rule = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "resolution_id", require_identifier(self.resolution_id, "resolution_id"))
        object.__setattr__(
            self, "conflict_ref", require_bound_ref(self.conflict_ref, "conflict_ref", kind=RefKind.CONFLICT)
        )
        state = ConflictResolutionState.parse(self.state, "state")
        object.__setattr__(self, "state", state.value)
        if state.leaves_work_blocked:
            raise SchemaValidationError(
                f"resolution {self.resolution_id} records {state.value}, which leaves the conflict "
                "open; an open state belongs on the conflict, and filing it as a resolution is how a "
                "conflict gets reported as handled"
            )
        object.__setattr__(self, "rationale", require_text(self.rationale, "rationale", maximum=MAX_RATIONALE_CHARS))
        if self.decided_by is None:
            raise AuthorityError(
                f"resolution {self.resolution_id} names nobody who decided it; §13's records are "
                "versioned precisely so that an unattributed closure can be reopened"
            )
        object.__setattr__(self, "decided_by", IntentAuthorityRef.coerce(self.decided_by, "decided_by"))
        if not self.decided_by.level.self_asserting_is_enough:
            raise AuthorityError(
                f"resolution {self.resolution_id} was recorded by a {self.decided_by.level.value} "
                "actor; agents may propose a resolution and may not file one (§24)"
            )
        object.__setattr__(
            self,
            "recorded_in_revision",
            require_bound_ref(self.recorded_in_revision, "recorded_in_revision", kind=RefKind.REVISION),
        )
        if state.requires_receipt and self.receipt_ref is None:
            raise OverrideRefusedError(
                f"resolution {self.resolution_id} claims an explicit override with no receipt ref; a "
                "blocking conflict closed without the decision that authorised it is the quiet "
                "weakening §24 refuses"
            )
        if state.requires_policy_pin and self.graph_ref is None:
            raise AuthorityError(
                f"resolution {self.resolution_id} resolves by policy without pinning which policy; "
                "the same words under a different graph are a different decision (§5)"
            )
        if self.receipt_ref is not None:
            object.__setattr__(
                self, "receipt_ref", require_bound_ref(self.receipt_ref, "receipt_ref", kind=RefKind.RECEIPT)
            )
        if self.human_decision is not None:
            object.__setattr__(
                self,
                "human_decision",
                require_bound_ref(self.human_decision, "human_decision", kind=RefKind.REVISION),
            )
        if self.graph_ref is not None:
            object.__setattr__(self, "graph_ref", AuthorityPolicyGraphRef.coerce(self.graph_ref, "graph_ref"))
        if state is ConflictResolutionState.RESOLVED_BY_SCOPE_SPLIT:
            if self.scope_split is None:
                raise ScopeError(
                    f"resolution {self.resolution_id} splits nothing; §14's split has to show the "
                    "regions each rule keeps force in"
                )
            object.__setattr__(self, "scope_split", ScopeSplitProposal.coerce(self.scope_split, "scope_split"))
        elif self.scope_split is not None:
            raise SchemaValidationError(
                f"resolution {self.resolution_id} resolves by {state.value} while carrying a scope split"
            )
        if state is ConflictResolutionState.RESOLVED_AS_EXPLORATION_FORK:
            if self.fork is None:
                raise ScopeError(
                    f"resolution {self.resolution_id} forks nothing; one variant is a decision, not a fork"
                )
            object.__setattr__(self, "fork", ExplorationFork.coerce(self.fork, "fork"))
        elif self.fork is not None:
            raise SchemaValidationError(
                f"resolution {self.resolution_id} resolves by {state.value} while carrying a fork"
            )
        if state is ConflictResolutionState.SUPERSEDED:
            if self.superseded_by is None:
                raise RefError(
                    f"resolution {self.resolution_id} is superseded by nothing; a successor-less "
                    "supersession reads as a deletion"
                )
            object.__setattr__(
                self,
                "superseded_by",
                require_bound_ref(self.superseded_by, "superseded_by", kind=RefKind.RESOLUTION),
            )
        elif self.superseded_by is not None:
            raise SchemaValidationError(
                f"resolution {self.resolution_id} names a successor without being SUPERSEDED"
            )
        object.__setattr__(self, "evidence_refs", bound_refs(self.evidence_refs, "evidence_refs", minimum=0))
        if self.candidate_id is not None:
            object.__setattr__(self, "candidate_id", require_identifier(self.candidate_id, "candidate_id"))
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=MAX_TEXT_CHARS))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        object.__setattr__(
            self, "compiler_version", require_version_text(self.compiler_version, "compiler_version")
        )
        object.__setattr__(self, "schema_version", require_version_text(self.schema_version, "schema_version"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def state_enum(self) -> ConflictResolutionState:
        return ConflictResolutionState.parse(self.state)

    @property
    def resolution_digest(self) -> str:
        """Digest over the decision, excluding how it is narrated."""

        return content_digest(self.fingerprint_inputs())

    @property
    def resolution_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.RESOLUTION.value, ref_id=self.resolution_id).with_digest(
            self.resolution_digest
        )

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "resolution_id": self.resolution_id,
            "conflict_ref": self.conflict_ref.text,
            "state": self.state,
            "decided_by": self.decided_by.to_payload(),
            "recorded_in_revision": self.recorded_in_revision.text,
            "receipt_ref": None if self.receipt_ref is None else self.receipt_ref.text,
            "human_decision": None if self.human_decision is None else self.human_decision.text,
            "graph_ref": None if self.graph_ref is None else self.graph_ref.pin_id,
            "scope_split": None if self.scope_split is None else self.scope_split.fingerprint_inputs(),
            "fork": None if self.fork is None else self.fork.fingerprint_inputs(),
            "superseded_by": None if self.superseded_by is None else self.superseded_by.text,
            "candidate_id": self.candidate_id,
            "evidence_refs": sorted(item.text for item in self.evidence_refs),
            "compiler_version": self.compiler_version,
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
        }

    def require_admissible_for(self, conflict_class: Any) -> ConflictResolutionState:
        """Refuse an exit this kind of incompatibility cannot take (§13, §24)."""

        wanted = ConflictClass.parse(conflict_class, "conflict_class")
        state = self.state_enum
        if state not in wanted.admissible_resolutions:
            raise ConflictBlockedError(
                f"a {wanted.value} conflict cannot be closed by {state.value}; that exit is not "
                f"available for this class, which offers {sorted(item.value for item in wanted.admissible_resolutions)}"
            )
        return state

    def require_current_policy(self, graph: AuthorityPolicyGraph) -> "ConflictResolution":
        """Refuse to reuse a policy-shaped resolution under a graph that has moved (§26)."""

        if self.graph_ref is None:
            return self
        if not isinstance(graph, AuthorityPolicyGraph):
            raise SchemaValidationError("require_current_policy expects an AuthorityPolicyGraph")
        self.graph_ref.require_current(graph, f"resolution {self.resolution_id}")
        return self


ConflictResolution.NESTED = {
    "conflict_ref": of(SemanticRef),
    "decided_by": of(IntentAuthorityRef),
    "recorded_in_revision": of(SemanticRef),
    "receipt_ref": of(SemanticRef),
    "human_decision": of(SemanticRef),
    "graph_ref": of(AuthorityPolicyGraphRef),
    "scope_split": of(ScopeSplitProposal),
    "fork": of(ExplorationFork),
    "superseded_by": of(SemanticRef),
    "evidence_refs": of(SemanticRef),
}


@dataclass(frozen=True)
class SemanticConflict(Record):
    """Two or more admitted semantics that cannot both hold, kept as a versioned object (§2).

    The conflict carries the parties, where they meet, who stands behind each side, and the ways
    out — and no verdict. That asymmetry is the point: `detect_conflicts` may be run by anything,
    including a model, and what it produces is a question with evidence attached rather than an
    answer. §1's "detection does not authorise a winner" is enforced by there being no winner
    field to fill in.
    """

    conflict_id: str
    conflict_class: str
    consequence: str
    parties: tuple[SemanticRef, ...] = ()
    semantic_paths: tuple[str, ...] = ()
    resolution_state: str = ConflictResolutionState.UNRESOLVED.value
    subject_scope: ConstraintScope | None = None
    conditions: tuple[Condition, ...] = ()
    authority_refs: tuple[SemanticRef, ...] = ()
    actor_levels: tuple[str, ...] = ()
    rule_classes: tuple[str, ...] = ()
    candidates: tuple[CandidateResolution, ...] = ()
    resolution: ConflictResolution | None = None
    invalidated: tuple[str, ...] = ()
    evidence_refs: tuple[SemanticRef, ...] = ()
    explanation_refs: tuple[SemanticRef, ...] = ()
    detected_in_revision: SemanticRef | None = None
    detected_by: IntentAuthorityRef | None = None
    graph_ref: AuthorityPolicyGraphRef | None = None
    compiler_version: str = CONFLICT_COMPILER_VERSION
    schema_version: str = SCHEMA_VERSION
    contract_version: str = ""
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    #: §1, D-M03-S05-002: these are constants because each one is a way to lose the doctrine.
    detection_grants_authority = False
    winner_chosen_by_recency = False
    winner_chosen_by_confidence = False
    deletes_a_rule = False
    uses_confidence = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "conflict_id", require_identifier(self.conflict_id, "conflict_id"))
        wanted = ConflictClass.parse(self.conflict_class, "conflict_class")
        object.__setattr__(self, "conflict_class", wanted.value)
        consequence = ConflictConsequence.parse(self.consequence, "consequence")
        object.__setattr__(self, "consequence", consequence.value)
        floor = wanted.default_consequence
        if _CONSEQUENCE_SEVERITY[consequence] < _CONSEQUENCE_SEVERITY[floor]:
            raise ConflictBlockedError(
                f"conflict {self.conflict_id} is a {wanted.value} filed as {consequence.value}; the "
                f"class carries at least {floor.value} by §4, and downgrading the stake is how a "
                "blocking conflict gets compiled around"
            )
        parties = bound_refs(self.parties, "parties")
        if len(parties) < MIN_PARTIES:
            raise ConflictBlockedError(
                f"conflict {self.conflict_id} has {len(parties)} party/parties; an incompatibility "
                "needs two sides, and a one-sided conflict is a complaint"
            )
        object.__setattr__(self, "parties", parties)
        paths = bound_paths(self.semantic_paths, "semantic_paths")
        if not paths:
            raise ScopeError(
                f"conflict {self.conflict_id} spans no semantic path; where two rules disagree is the "
                "one question a resolution cannot answer for itself"
            )
        object.__setattr__(self, "semantic_paths", paths)
        if self.subject_scope is not None:
            object.__setattr__(self, "subject_scope", ConstraintScope.coerce(self.subject_scope, "subject_scope"))
        conditions = tuple(
            sorted(
                (Condition.coerce(item, "conditions[]") for item in (self.conditions or ())),
                key=lambda item: (item.context_key, item.operator, item.values),
            )
        )
        if len(conditions) > MAX_CONDITIONS:
            raise LimitExceededError(f"conditions exceeds {MAX_CONDITIONS}")
        object.__setattr__(self, "conditions", conditions)
        object.__setattr__(self, "authority_refs", bound_refs(self.authority_refs, "authority_refs", minimum=0))
        if consequence.requires_authorized_resolution and not self.authority_refs:
            raise AuthorityError(
                f"conflict {self.conflict_id} is {consequence.value} with no authority refs; a rights "
                "or security stake with no policy behind it is an opinion about someone else's boundary"
            )
        levels = tuple(
            sorted({AuthorityLevel.parse(item, "actor_levels[]").value for item in (self.actor_levels or ())})
        )
        object.__setattr__(self, "actor_levels", levels)
        classes = tuple(
            sorted({require_identifier(item, "rule_classes[]") for item in (self.rule_classes or ())})
        )
        if len(classes) > MAX_SCOPE_PATHS:
            raise LimitExceededError(f"rule_classes exceeds {MAX_SCOPE_PATHS}")
        object.__setattr__(self, "rule_classes", classes)
        candidates = _candidates(self.candidates, wanted, parties=parties)
        object.__setattr__(self, "candidates", candidates)
        state = ConflictResolutionState.parse(self.resolution_state, "resolution_state")
        object.__setattr__(self, "resolution_state", state.value)
        if state not in wanted.admissible_resolutions:
            raise ConflictBlockedError(
                f"conflict {self.conflict_id} is a {wanted.value} in state {state.value}; §13 does not "
                f"offer that exit, which is {sorted(item.value for item in wanted.admissible_resolutions)}"
            )
        if self.resolution is not None:
            resolution = ConflictResolution.coerce(self.resolution, "resolution")
            resolution.require_admissible_for(wanted)
            if resolution.state != state.value:
                raise SchemaValidationError(
                    f"conflict {self.conflict_id} reports {state.value} while its resolution records "
                    f"{resolution.state}; one conflict may not carry two verdicts"
                )
            if resolution.conflict_ref.text != self.conflict_ref.text:
                raise RefError(
                    f"conflict {self.conflict_id} is resolved by a record citing "
                    f"{resolution.conflict_ref.text}, which is not this conflict; a resolution attached "
                    "to the wrong conflict is worse than none"
                )
            if state.requires_policy_pin:
                if resolution.graph_ref is not None and self.graph_ref is not None:
                    if resolution.graph_ref.pin_id != self.graph_ref.pin_id:
                        raise StaleSemanticError(
                            f"conflict {self.conflict_id} was detected under {self.graph_ref.pin_id} and "
                            f"resolved under {resolution.graph_ref.pin_id}; the two readings have to be "
                            "reconciled before the resolution may be relied on (§26)"
                        )
            object.__setattr__(self, "resolution", resolution)
            if self.graph_ref is None and resolution.graph_ref is not None:
                object.__setattr__(self, "graph_ref", resolution.graph_ref)
        elif state.is_resolved:
            raise ConflictBlockedError(
                f"conflict {self.conflict_id} claims {state.value} with no resolution record; §13's "
                "states are evidence, not fields to flip"
            )
        if self.graph_ref is not None:
            object.__setattr__(self, "graph_ref", AuthorityPolicyGraphRef.coerce(self.graph_ref, "graph_ref"))
        object.__setattr__(self, "invalidated", invalidation_targets(self.invalidated, "invalidated"))
        object.__setattr__(self, "evidence_refs", bound_refs(self.evidence_refs, "evidence_refs", minimum=0))
        object.__setattr__(
            self, "explanation_refs", bound_refs(self.explanation_refs, "explanation_refs", minimum=0)
        )
        object.__setattr__(
            self,
            "detected_in_revision",
            require_bound_ref(self.detected_in_revision, "detected_in_revision", kind=RefKind.REVISION),
        )
        if self.detected_by is not None:
            object.__setattr__(self, "detected_by", IntentAuthorityRef.coerce(self.detected_by, "detected_by"))
        if wanted is ConflictClass.RIGHTS_SECURITY_CONFLICT and not self.evidence_refs:
            raise AuthorityError(
                f"conflict {self.conflict_id} asserts a rights or security boundary with no evidence "
                "ref; M03 may report such a conflict only when the owning policy is cited (§6)"
            )
        if not wanted.detected_by_kernel and not self.evidence_refs:
            raise ConflictBlockedError(
                f"conflict {self.conflict_id} is a {wanted.value}, which the kernel cannot derive, and "
                "cites no evidence; a conflict nobody observed has to at least say who did"
            )
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=MAX_TEXT_CHARS))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        object.__setattr__(
            self, "compiler_version", require_version_text(self.compiler_version, "compiler_version")
        )
        object.__setattr__(self, "schema_version", require_version_text(self.schema_version, "schema_version"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    #: --- views -------------------------------------------------------------

    @property
    def class_enum(self) -> ConflictClass:
        return ConflictClass.parse(self.conflict_class)

    @property
    def consequence_enum(self) -> ConflictConsequence:
        return ConflictConsequence.parse(self.consequence)

    @property
    def state_enum(self) -> ConflictResolutionState:
        return ConflictResolutionState.parse(self.resolution_state)

    @property
    def party_ids(self) -> tuple[str, ...]:
        return tuple(item.ref_id for item in self.parties)

    @property
    def admissible_resolutions(self) -> frozenset[ConflictResolutionState]:
        return self.class_enum.admissible_resolutions

    @property
    def candidate_states(self) -> tuple[str, ...]:
        return tuple(sorted({item.produces for item in self.candidates}))

    @property
    def resolved(self) -> bool:
        return self.state_enum.is_resolved

    @property
    def blocks_contract(self) -> bool:
        """Whether no admitted contract may be emitted while this stands (§4, §28)."""

        return self.consequence_enum.blocks_contract and self.state_enum.leaves_work_blocked

    @property
    def requires_human_decision(self) -> bool:
        """Whether the next move belongs to a person rather than to a policy edge.

        Computed, never stored: a stored flag could be flipped to make a blocker disappear, and
        the state it describes is fully determined by the consequence and the resolution state.
        """

        if self.resolution is not None and self.resolution.human_decision is not None:
            return False
        return self.state_enum is ConflictResolutionState.NEEDS_HUMAN_DECISION or self.blocks_contract

    @property
    def open(self) -> bool:
        return self.state_enum.leaves_work_blocked

    def involves(self, ref: Any) -> bool:
        item = SemanticRef.coerce(ref, "ref")
        return any(item.ref_id == party.ref_id for party in self.parties)

    def on_path(self, semantic_path: str) -> bool:
        path = require_semantic_path(semantic_path, "semantic_path")
        return any(covers_path(one, path) or covers_path(path, one) for one in self.semantic_paths)

    #: --- identity and fingerprints ----------------------------------------

    def detection_view(self) -> dict[str, Any]:
        """The §26 inputs of the conflict itself, with no verdict mixed in.

        ``resolution``, ``notes`` and ``metadata`` are excluded so a resolution can cite the
        conflict it settles without a circular digest, and so rewording the record never moves the
        thing it is a fingerprint of.
        """

        return {
            "conflict_id": self.conflict_id,
            "conflict_class": self.conflict_class,
            "consequence": self.consequence,
            "parties": sorted(item.text for item in self.parties),
            "semantic_paths": sorted(self.semantic_paths),
            "subject_scope": None if self.subject_scope is None else self.subject_scope.to_payload(),
            "conditions": [item.to_payload() for item in self.conditions],
            "authority_refs": sorted(item.text for item in self.authority_refs),
            "actor_levels": sorted(self.actor_levels),
            "rule_classes": sorted(self.rule_classes),
            "candidates": [item.fingerprint_inputs() for item in self.candidates],
            "invalidated": sorted(self.invalidated),
            "evidence_refs": sorted(item.text for item in self.evidence_refs),
            "graph_ref": None if self.graph_ref is None else self.graph_ref.pin_id,
            "detected_in_revision": self.detected_in_revision.text,
            "compiler_version": self.compiler_version,
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
        }

    @property
    def conflict_digest(self) -> str:
        return content_digest(self.detection_view())

    @property
    def conflict_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.CONFLICT.value, ref_id=self.conflict_id).with_digest(self.conflict_digest)

    def fingerprint_inputs(self) -> dict[str, Any]:
        view = self.detection_view()
        view["resolution_state"] = self.resolution_state
        view["resolution"] = None if self.resolution is None else self.resolution.fingerprint_inputs()
        return view

    def resolution_fingerprint(
        self,
        *,
        fingerprint_id: str | None = None,
        policy_version: str | None = None,
    ) -> "ConflictResolutionFingerprint":
        """The §26 fingerprint binding this conflict and, when present, its resolution."""

        return ConflictResolutionFingerprint.of(
            self,
            fingerprint_id=fingerprint_id or f"fpr.{self.conflict_id}",
            policy_version=policy_version,
        )

    #: --- gates --------------------------------------------------------------

    def require_resolved(self, action: str) -> "SemanticConflict":
        """Refuse an action that cannot proceed while this conflict stands (§28)."""

        if self.blocks_contract:
            raise ConflictBlockedError(
                f"{action} cannot proceed with {self.conflict_id} ({self.conflict_class}, "
                f"{self.consequence}) in state {self.resolution_state}; the incompatible rules are "
                f"{sorted(self.party_ids)} and the exits are {sorted(item.value for item in self.admissible_resolutions)}"
            )
        return self

    def require_current(self, graph: AuthorityPolicyGraph, action: str) -> "SemanticConflict":
        """Refuse to reuse a resolution decided under a policy that has since moved (§26)."""

        if self.graph_ref is None or self.resolution is None:
            return self
        self.graph_ref.require_current(graph, f"{action} against conflict {self.conflict_id}")
        self.resolution.require_current_policy(graph)
        return self

    def with_resolution(self, resolution: ConflictResolution) -> "SemanticConflict":
        """Return this conflict carrying ``resolution``, leaving this record untouched."""

        from dataclasses import replace as _replace

        return _replace(self, resolution=resolution, resolution_state=resolution.state)

    def supersede(self, successor: SemanticRef, *, actor: IntentAuthorityRef, revision_ref: SemanticRef, rationale: str) -> "SemanticConflict":
        """Close this conflict as SUPERSEDED by a successor conflict, not by silence (§13)."""

        resolution = ConflictResolution(
            resolution_id=f"res.{self.conflict_id}.superseded",
            conflict_ref=self.conflict_ref,
            state=ConflictResolutionState.SUPERSEDED.value,
            rationale=rationale,
            decided_by=actor,
            recorded_in_revision=revision_ref,
            superseded_by=successor,
        )
        return self.with_resolution(resolution)


SemanticConflict.NESTED = {
    "parties": of(SemanticRef),
    "subject_scope": of(ConstraintScope),
    "conditions": of(Condition),
    "authority_refs": of(SemanticRef),
    "candidates": of(CandidateResolution),
    "resolution": of(ConflictResolution),
    "evidence_refs": of(SemanticRef),
    "explanation_refs": of(SemanticRef),
    "detected_in_revision": of(SemanticRef),
    "detected_by": of(IntentAuthorityRef),
    "graph_ref": of(AuthorityPolicyGraphRef),
}


@dataclass(frozen=True)
class ConflictResolutionFingerprint(Record):
    """The §26 fingerprint of one conflict and the resolution that was reached under a policy.

    Two claims give it its shape. The first is that the resolution is only valid for the inputs
    it was computed from, so the policy version and the receipts are part of the key. The second
    is that nothing may be *silently* reused: when an input moves, the fingerprint stops matching,
    and the reader is told which input moved instead of being handed a stale verdict.
    """

    fingerprint_id: str
    conflict_ref: SemanticRef
    conflict_digest: str
    involved_refs: tuple[str, ...] = ()
    semantic_digest: str = ""
    scope_digest: str = ""
    condition_digest: str = ""
    policy_version: str | None = None
    graph_digest: str | None = None
    receipt_refs: tuple[str, ...] = ()
    resolution_digest: str | None = None
    compiler_version: str = CONFLICT_COMPILER_VERSION
    schema_version: str = SCHEMA_VERSION
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "fingerprint_id", require_identifier(self.fingerprint_id, "fingerprint_id"))
        object.__setattr__(
            self, "conflict_ref", require_bound_ref(self.conflict_ref, "conflict_ref", kind=RefKind.CONFLICT)
        )
        if self.conflict_ref.content_digest != self.conflict_digest:
            raise RefError(
                f"fingerprint {self.fingerprint_id} cites {self.conflict_ref.text} but records conflict "
                f"digest {self.conflict_digest[:16]}; a fingerprint that does not agree with its own "
                "ref cannot certify anything"
            )
        object.__setattr__(self, "involved_refs", _texts(self.involved_refs, "involved_refs"))
        for name in ("semantic_digest", "scope_digest", "condition_digest"):
            value = getattr(self, name) or ""
            object.__setattr__(self, name, value if value else content_digest({name: None}))
        if self.policy_version is not None:
            object.__setattr__(self, "policy_version", require_version_text(self.policy_version, "policy_version"))
        if self.graph_digest is not None:
            object.__setattr__(self, "graph_digest", _digest_text(self.graph_digest, "graph_digest"))
        object.__setattr__(self, "receipt_refs", _texts(self.receipt_refs, "receipt_refs"))
        if self.resolution_digest is not None:
            object.__setattr__(self, "resolution_digest", _digest_text(self.resolution_digest, "resolution_digest"))
        object.__setattr__(
            self, "compiler_version", require_version_text(self.compiler_version, "compiler_version")
        )
        object.__setattr__(self, "schema_version", require_version_text(self.schema_version, "schema_version"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @classmethod
    def of(
        cls,
        conflict: SemanticConflict,
        *,
        fingerprint_id: str,
        policy_version: str | None = None,
    ) -> "ConflictResolutionFingerprint":
        """Fingerprint a conflict from its own records, plus the policy it was decided under."""

        if not isinstance(conflict, SemanticConflict):
            raise SchemaValidationError("ConflictResolutionFingerprint.of expects a SemanticConflict")
        resolution = conflict.resolution
        receipts = ()
        if resolution is not None:
            receipts = () if resolution.receipt_ref is None else (resolution.receipt_ref.text,)
        return cls(
            fingerprint_id=fingerprint_id,
            conflict_ref=conflict.conflict_ref,
            conflict_digest=conflict.conflict_digest,
            involved_refs=tuple(item.text for item in conflict.parties),
            semantic_digest=content_digest(
                {
                    "paths": sorted(conflict.semantic_paths),
                    "rule_classes": sorted(conflict.rule_classes),
                    "class": conflict.conflict_class,
                }
            ),
            scope_digest=content_digest(
                None if conflict.subject_scope is None else conflict.subject_scope.to_payload()
            ),
            condition_digest=content_digest([item.to_payload() for item in conflict.conditions]),
            policy_version=policy_version
            if policy_version is not None
            else None if conflict.graph_ref is None else conflict.graph_ref.version,
            graph_digest=None if conflict.graph_ref is None else conflict.graph_ref.graph_digest,
            receipt_refs=receipts,
            resolution_digest=None if resolution is None else resolution.resolution_digest,
            compiler_version=conflict.compiler_version,
            schema_version=conflict.schema_version,
            contract_version=conflict.contract_version,
        )

    @property
    def fingerprint_digest(self) -> str:
        return content_digest(self.fingerprint_inputs())

    @property
    def decided(self) -> bool:
        return self.resolution_digest is not None

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "fingerprint_id": self.fingerprint_id,
            "conflict_digest": self.conflict_digest,
            "involved_refs": sorted(self.involved_refs),
            "semantic_digest": self.semantic_digest,
            "scope_digest": self.scope_digest,
            "condition_digest": self.condition_digest,
            "policy_version": self.policy_version,
            "graph_digest": self.graph_digest,
            "receipt_refs": sorted(self.receipt_refs),
            "resolution_digest": self.resolution_digest,
            "compiler_version": self.compiler_version,
            "schema_version": self.schema_version,
            "contract_version": self.contract_version,
        }

    def describes(self, conflict: SemanticConflict) -> bool:
        return self.conflict_digest == conflict.conflict_digest

    def stale_inputs(self, conflict: SemanticConflict, graph: AuthorityPolicyGraph | None = None) -> tuple[str, ...]:
        """Name what moved between this fingerprint and the conflict as it is now (§26)."""

        drift: list[str] = []
        if self.conflict_digest != conflict.conflict_digest:
            drift.append("conflict")
        if self.resolution_digest != (None if conflict.resolution is None else conflict.resolution.resolution_digest):
            drift.append("resolution")
        if graph is not None and self.graph_digest is not None and self.graph_digest != graph.graph_digest:
            drift.append("authority_policy")
        if self.compiler_version != conflict.compiler_version:
            drift.append("compiler")
        return tuple(drift)

    def require_current(
        self, conflict: SemanticConflict, graph: AuthorityPolicyGraph | None = None, action: str = "reuse"
    ) -> "ConflictResolutionFingerprint":
        """Refuse a stale fingerprint rather than reusing it quietly (§26)."""

        drift = self.stale_inputs(conflict, graph)
        if drift:
            raise StaleSemanticError(
                f"{action} of resolution fingerprint {self.fingerprint_id} is refused: {list(drift)} "
                "changed since it was computed, and a stale resolution must be re-derived rather than "
                "inherited"
            )
        return self


ConflictResolutionFingerprint.NESTED = {"conflict_ref": of(SemanticRef)}


@dataclass(frozen=True)
class MinimumSufficientConflictSlice(Record):
    """Everything needed to decide one conflict, and nothing else (§25).

    The claim of §25 is that resolving a localized conflict does not require the project's
    history, and a claim like that needs a check rather than a design note. So the slice refuses
    to carry a path the conflict is not about: the underlying semantic slice has to be cut for
    ``RESOLVE_CONFLICT``, its paths have to be exactly the conflict's locality, and every policy
    edge it brings along has to touch a rule class in play.
    """

    slice_id: str
    conflict_ref: SemanticRef
    semantic_slice: MinimumSufficientSemanticSlice
    policy_edges: tuple[AuthorityPolicyEdge, ...] = ()
    candidates: tuple[CandidateResolution, ...] = ()
    authority_refs: tuple[SemanticRef, ...] = ()
    provenance_refs: tuple[SemanticRef, ...] = ()
    contract_version: str = ""

    #: §25's sentence, as a constant a reader can assert on.
    includes_project_history = False
    carries_full_brief = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "slice_id", require_identifier(self.slice_id, "slice_id"))
        object.__setattr__(
            self, "conflict_ref", require_bound_ref(self.conflict_ref, "conflict_ref", kind=RefKind.CONFLICT)
        )
        semantic = MinimumSufficientSemanticSlice.coerce(self.semantic_slice, "semantic_slice")
        if semantic.purpose != SlicePurpose.RESOLVE_CONFLICT.value:
            raise ScopeError(
                f"conflict slice {self.slice_id} was cut for {semantic.purpose}; a resolution reading "
                "an ambiguity-shaped or audit-shaped slice is fetching the wrong closure (§25)"
            )
        object.__setattr__(self, "semantic_slice", semantic)
        if not semantic.paths:
            raise ScopeError(f"conflict slice {self.slice_id} spans no paths")
        edges = tuple(
            sorted(
                (AuthorityPolicyEdge.coerce(item, "policy_edges[]") for item in (self.policy_edges or ())),
                key=lambda item: item.edge_id,
            )
        )
        if len(edges) > MAX_CONFLICT_PARTIES:
            raise LimitExceededError(f"policy_edges exceeds {MAX_CONFLICT_PARTIES}")
        object.__setattr__(self, "policy_edges", edges)
        candidates = _candidates(self.candidates, None)
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "authority_refs", bound_refs(self.authority_refs, "authority_refs", minimum=0))
        object.__setattr__(self, "provenance_refs", bound_refs(self.provenance_refs, "provenance_refs", minimum=0))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def paths(self) -> tuple[str, ...]:
        return self.semantic_slice.paths

    @property
    def edge_ids(self) -> tuple[str, ...]:
        return tuple(item.edge_id for item in self.policy_edges)

    @property
    def footprint(self) -> int:
        """How much this slice carries, so a regression in minimality is visible (§25)."""

        from .slicing import structural_footprint

        return structural_footprint(self.to_payload())

    def touches(self, semantic_path: str) -> bool:
        path = require_semantic_path(semantic_path, "semantic_path")
        return any(covers_path(one, path) or covers_path(path, one) for one in self.paths)

    def require_local(self, conflict: SemanticConflict) -> "MinimumSufficientConflictSlice":
        """Refuse a slice that is not the conflict's locality, in either direction (§25)."""

        if not isinstance(conflict, SemanticConflict):
            raise SchemaValidationError("require_local expects a SemanticConflict")
        if self.conflict_ref.text != conflict.conflict_ref.text:
            raise RefError(
                f"slice {self.slice_id} cites {self.conflict_ref.text} but is being checked against "
                f"{conflict.conflict_ref.text}"
            )
        missing = sorted(set(conflict.semantic_paths) - set(self.paths))
        if missing:
            raise ScopeError(
                f"slice {self.slice_id} cannot decide {conflict.conflict_id}: {missing} is outside it, "
                "and a resolution made from part of the disagreement is a guess"
            )
        extra = sorted(
            path
            for path in self.paths
            if not any(covers_path(one, path) or covers_path(path, one) for one in conflict.semantic_paths)
        )
        if extra:
            raise ScopeError(
                f"slice {self.slice_id} carries {extra}, which {conflict.conflict_id} is not about; "
                "§25's economy is the whole reason a localized conflict is cheap to resolve"
            )
        return self

    def require_edges_relevant(
        self, conflict: SemanticConflict, graph: AuthorityPolicyGraph | None = None
    ) -> "MinimumSufficientConflictSlice":
        """Refuse policy padding: an edge may ride along only if it speaks to this disagreement."""

        if not any(edge.covers(path) for edge in self.policy_edges for path in conflict.semantic_paths):
            raise ScopeError(
                f"no edge in slice {self.slice_id} reaches {list(conflict.semantic_paths)}; §25 keeps "
                "the decision readable by carrying only the policy the decision turns on"
            )
        if graph is None:
            return self
        in_play = set(conflict.rule_classes)
        for edge in self.policy_edges:
            governed = {
                one
                for node_id in (edge.subject_node_id, edge.object_node_id)
                for one in (graph.node(node_id).rule_classes if graph.node(node_id) else ())
            }
            if in_play and not (governed & in_play):
                raise ScopeError(
                    f"edge {edge.edge_id} governs {sorted(governed)}, none of which is a rule class "
                    f"{conflict.conflict_id} disputes, so it is policy scenery rather than context"
                )
        return self

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "slice_id": self.slice_id,
            "conflict_ref": self.conflict_ref.text,
            "paths": sorted(self.paths),
            "statements": self.semantic_slice.slice_digest,
            "edges": sorted(self.edge_ids),
            "candidates": [item.fingerprint_inputs() for item in self.candidates],
        }

    @property
    def slice_digest(self) -> str:
        return content_digest(self.fingerprint_inputs())


MinimumSufficientConflictSlice.NESTED = {
    "conflict_ref": of(SemanticRef),
    "semantic_slice": of(MinimumSufficientSemanticSlice),
    "policy_edges": of(AuthorityPolicyEdge),
    "candidates": of(CandidateResolution),
    "authority_refs": of(SemanticRef),
    "provenance_refs": of(SemanticRef),
}


@dataclass(frozen=True)
class ConflictQuestion(Record):
    """The one question a conflict owes somebody, sized to the smallest useful ask (§15).

    §15's "smallest set of questions" is a ranking, not an answer generator: this record can say
    what to ask, who has to answer and what stops until they do, and it carries no candidate
    reading of its own. ``invents_answer`` is a constant for that reason.
    """

    question_id: str
    conflict_ref: SemanticRef
    question: str
    asks_for: str
    consequence: str
    affected_paths: tuple[str, ...] = ()
    dependents: tuple[str, ...] = ()
    blocking: bool = True
    authority_needed: str | None = None
    rationale: str | None = None
    contract_version: str = ""

    invents_answer = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "question_id", require_identifier(self.question_id, "question_id"))
        object.__setattr__(
            self, "conflict_ref", require_bound_ref(self.conflict_ref, "conflict_ref", kind=RefKind.CONFLICT)
        )
        object.__setattr__(self, "question", require_text(self.question, "question", maximum=MAX_RATIONALE_CHARS))
        target = _QuestionTarget.parse(self.asks_for, "asks_for").value
        object.__setattr__(self, "asks_for", target)
        object.__setattr__(self, "consequence", ConflictConsequence.parse(self.consequence, "consequence").value)
        object.__setattr__(self, "affected_paths", bound_paths(self.affected_paths, "affected_paths"))
        object.__setattr__(self, "dependents", _texts(self.dependents, "dependents"))
        if not isinstance(self.blocking, bool):
            raise SchemaValidationError("blocking must be a boolean")
        if self.blocking and ConflictConsequence.parse(self.consequence).blocks_contract is False:
            raise SchemaValidationError(
                f"question {self.question_id} is blocking about a {self.consequence} conflict; a block "
                "nobody has to justify is a block that gets ignored"
            )
        if self.authority_needed is not None:
            object.__setattr__(
                self, "authority_needed", AuthorityLevel.parse(self.authority_needed, "authority_needed").value
            )
        if self.rationale is not None:
            object.__setattr__(
                self, "rationale", require_text(self.rationale, "rationale", maximum=MAX_RATIONALE_CHARS)
            )
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def report_rank(self) -> tuple[int, int, int, str]:
        """Deterministic ordering: stake, then blast radius, then cost of waiting, then id (§15)."""

        return (
            _CONSEQUENCE_RANK[self.consequence_enum],
            -len(self.dependents),
            -len(self.affected_paths),
            self.question_id,
        )

    @property
    def consequence_enum(self) -> ConflictConsequence:
        return ConflictConsequence.parse(self.consequence)


class _QuestionTarget(Labeled):
    """Who owes the answer — kept separate from authority level, which is about permission."""

    HUMAN_OWNER = "HUMAN_OWNER"
    POLICY_OWNER = "POLICY_OWNER"
    PROJECT_RECORD = "PROJECT_RECORD"
    UPSTREAM_MODULE = "UPSTREAM_MODULE"


ConflictQuestion.NESTED = {"conflict_ref": of(SemanticRef)}


#: --- detection ---------------------------------------------------------------

_STRICT_POLARITIES = frozenset({ConstraintPolarity.REQUIRE, ConstraintPolarity.FORBID})


def _related_path(left: str, right: str) -> bool:
    return covers_path(left, right) or covers_path(right, left)


def _interval(envelope: ToleranceEnvelope) -> tuple[float, float, bool, bool]:
    """The measurements an envelope admits, as ``(low, high, low_open, high_open)``.

    ``CLOSEST`` answers with the whole line: an optimum prefers a value, it does not forbid the
    rest, and reading "as near 24fps as practical" as the point {24} would report a contradiction
    wherever a brief stated a taste rather than a bound.
    """

    comparison = envelope.comparison_kind
    if comparison is Comparison.BETWEEN:
        return float(envelope.lower), float(envelope.upper), False, False
    if comparison is Comparison.EQ:
        target = float(envelope.target)
        return target, target, False, False
    if comparison in {Comparison.LTE, Comparison.LT}:
        return float("-inf"), float(envelope.target), True, comparison is Comparison.LT
    if comparison in {Comparison.GTE, Comparison.GT}:
        return float(envelope.target), float("inf"), comparison is Comparison.GT, True
    return float("-inf"), float("inf"), True, True


def _ranges_disjoint(left: ToleranceEnvelope, right: ToleranceEnvelope) -> bool:
    a_low, a_high, a_open_low, a_open_high = _interval(left)
    b_low, b_high, b_open_low, b_open_high = _interval(right)
    low, high = max(a_low, b_low), min(a_high, b_high)
    if low > high:
        return True
    if low == high:
        # A single surviving point is only a solution when both sides include it.
        open_low = (a_open_low if low == a_low else False) or (b_open_low if low == b_low else False)
        open_high = (a_open_high if high == a_high else False) or (b_open_high if high == b_high else False)
        return open_low or open_high
    return False


def _argument_disagreement(left: Constraint, right: Constraint) -> tuple[str, str, str] | None:
    """``(argument, left value, right value)`` for one demand both rules make differently.

    Only scalars are compared: two list-valued arguments may overlap in ways this kernel has no
    permission to guess at, and a detector that invents a conflict out of a set difference it
    cannot justify spends the reviewer's trust (§1).
    """

    shared = set(left.predicate.arguments) & set(right.predicate.arguments)
    for name in sorted(shared):
        a, b = left.predicate.arguments[name], right.predicate.arguments[name]
        if isinstance(a, (Mapping, list, tuple, set)) or isinstance(b, (Mapping, list, tuple, set)):
            continue
        if isinstance(a, bool) is not isinstance(b, bool) or a != b:
            return (name, str(a), str(b))
    return None


def _tolerance_disagreement(left: Constraint, right: Constraint) -> tuple[ConflictClass, str] | None:
    measures = sorted({item.measure for item in left.tolerances} & {item.measure for item in right.tolerances})
    for measure in measures:
        a, b = left.tolerance_for(measure), right.tolerance_for(measure)
        if a is None or b is None or a.unit != b.unit:
            continue
        if _ranges_disjoint(a, b):
            wanted = (
                ConflictClass.CARDINALITY_CONFLICT
                if measure in _CARDINALITY_MEASURES
                else ConflictClass.EMPTY_RANGE
            )
            return (wanted, measure)
    return None


def _anchor_disagreement(left: Constraint, right: Constraint) -> ProtectedAnchor | None:
    """Two protected anchors on one identity point that cite disjoint statements (§3)."""

    for a in left.protected_anchors:
        for b in right.protected_anchors:
            if a.semantic_path != b.semantic_path or a.anchor_kind != b.anchor_kind:
                continue
            if a.dimension_ref != b.dimension_ref:
                continue
            first = {item.text for item in a.statement_refs}
            second = {item.text for item in b.statement_refs}
            if first and second and not (first & second):
                return a
    return None


def _link_covering(links: tuple[tuple[frozenset[str], tuple[str, ...]], ...], left: Constraint, right: Constraint):
    """The STRICT cross-modal link that binds two rules' channels and paths, if one exists."""

    for channels, paths in links:
        if left.modality not in channels or right.modality not in channels:
            continue
        if not any(_related_path(one, left.semantic_path) for one in paths):
            continue
        if not any(_related_path(one, right.semantic_path) for one in paths):
            continue
        return True
    return False


def _classify_pair(
    left: Constraint,
    right: Constraint,
    links: tuple[tuple[frozenset[str], tuple[str, ...]], ...],
    *,
    cross_only: bool = False,
) -> tuple[ConflictClass, str] | None:
    """Name why two bound rules cannot both hold, or stay silent (§3).

    The order is a claim about which question is already settled: a polarity contradiction needs
    no arguments to prove itself, an empty tolerance intersection proves more than a differing
    categorical value does, and a reference disagreement outranks both because the two rules may
    not be about the same object at all.

    ``cross_only`` is set when no scope bound the pair and only a STRICT link relates them. Then the
    other classes are all refusals to state the truth: they assert two rules bind one subject, and
    here the channels are different subjects the link author chose to compare.
    """

    if cross_only:
        if left.predicate.predicate_id != right.predicate.predicate_id:
            return None
        disagreeing = _argument_disagreement(left, right)
        if disagreeing is None:
            return None
        name, first, second = disagreeing
        return (
            ConflictClass.CROSS_MODAL_CONFLICT,
            f"a strict cross-modal link requires {left.modality} and {right.modality} to agree on "
            f"{left.predicate.predicate_id}, while {left.constraint_id} sets {name}={first} and "
            f"{right.constraint_id} sets {name}={second}",
        )
    if (
        ConstraintPolarity.parse(left.polarity) in _STRICT_POLARITIES
        and ConstraintPolarity.parse(right.polarity) in _STRICT_POLARITIES
        and left.polarity != right.polarity
    ):
        return (
            ConflictClass.DIRECT_CONTRADICTION,
            f"{left.constraint_id} {left.polarity} and {right.constraint_id} {right.polarity} the same "
            f"{left.semantic_path}",
        )
    anchors = _anchor_disagreement(left, right)
    if anchors is not None:
        return (
            ConflictClass.IDENTITY_CONFLICT,
            f"the protected anchor {anchors.anchor_id} on {anchors.semantic_path} is pinned to two "
            "disjoint sets of statements",
        )
    ranges = _tolerance_disagreement(left, right)
    if ranges is not None:
        wanted, measure = ranges
        return (
            wanted,
            f"{left.constraint_id} and {right.constraint_id} leave no admissible value for "
            f"{measure} ({_bounds_text(left, right, measure)})",
        )
    if (
        left.subject_ref is not None
        and right.subject_ref is not None
        and left.subject_ref.ref_id == right.subject_ref.ref_id
        and left.subject_ref.content_digest != right.subject_ref.content_digest
    ):
        return (
            ConflictClass.REFERENCE_CONFLICT,
            f"{left.constraint_id} and {right.constraint_id} point at {left.subject_ref.ref_id} as two "
            "different objects",
        )
    if left.predicate.predicate_id == right.predicate.predicate_id:
        if left.predicate.version != right.predicate.version:
            return (
                ConflictClass.VERSION_CONFLICT,
                f"{left.constraint_id} uses {left.predicate.reference} and {right.constraint_id} uses "
                f"{right.predicate.reference} on one path",
            )
        disagreeing = _argument_disagreement(left, right)
        if disagreeing is not None:
            name, first, second = disagreeing
            if _link_covering(links, left, right):
                wanted = ConflictClass.CROSS_MODAL_CONFLICT
                reason = (
                    f"a strict cross-modal link requires {left.modality} and {right.modality} to agree, "
                    f"while {left.constraint_id} sets {name}={first} and {right.constraint_id} sets "
                    f"{name}={second}"
                )
            elif left.semantic_path == right.semantic_path:
                wanted = ConflictClass.VALUE_INCOMPATIBILITY
                reason = (
                    f"{left.constraint_id} demands {name}={first} and {right.constraint_id} demands "
                    f"{name}={second} for {left.semantic_path}"
                )
            else:
                wanted = ConflictClass.SCOPE_COLLISION
                reason = (
                    f"{left.constraint_id} and {right.constraint_id} set {name} differently on "
                    f"{left.semantic_path} and {right.semantic_path}, which overlap on some subjects"
                )
            return (wanted, reason)
    return None


def _bounds_text(left: Constraint, right: Constraint, measure: str) -> str:
    """Render the two declared bounds, for the message that names an empty intersection."""

    a, b = left.tolerance_for(measure), right.tolerance_for(measure)
    return f"{a.comparison} {a.target if a.target is not None else (a.lower, a.upper)} vs " \
        f"{b.comparison} {b.target if b.target is not None else (b.lower, b.upper)} {a.unit}"


def _authorities(constraints: Iterable[Constraint]) -> tuple[tuple[str, ...], tuple[SemanticRef, ...]]:
    """The levels standing behind a set of rules, and the refs that granted them."""

    levels = sorted({item.authority.authority for item in constraints})
    refs: dict[str, SemanticRef] = {}
    for item in constraints:
        for name in ("granted_by", "policy_ref"):
            value = getattr(item.authority, name)
            if value is not None:
                refs.setdefault(value.text, value)
    return tuple(levels), bound_refs(tuple(refs.values()), "authority_refs", minimum=0)


def _meeting_scope(constraints: tuple[Constraint, ...]) -> ConstraintScope | None:
    """The region where every rule in the set claims force, when one can be named (§2).

    Computed per field rather than declared, because a conflict's scope is the part of the brief
    where the parties actually collide: report the union and the resolution reads as though it
    bound subjects nobody disputed, report nothing and the §26 fingerprint loses its locality.
    """

    first = constraints[0].scope
    paths = list(first.subject_paths)
    channels = list(first.modalities)
    facets = list(first.facets)
    phases = list(first.phases)
    destinations = list(first.destinations)
    for item in constraints[1:]:
        other = item.scope
        paths = [one for one in paths if any(_related_path(one, two) for two in other.subject_paths)]
        if other.modalities and channels:
            channels = [one for one in channels if one in other.modalities] or channels
        if other.facets and facets:
            facets = [one for one in facets if one in other.facets] or facets
        if other.phases and phases:
            phases = [one for one in phases if one in other.phases] or phases
        if other.destinations and destinations:
            destinations = [one for one in destinations if one in other.destinations] or destinations
    if not paths:
        return None
    try:
        return ConstraintScope(
            subject_paths=tuple(paths),
            modalities=tuple(channels),
            facets=tuple(facets),
            phases=tuple(phases),
            destinations=tuple(destinations),
            excluded_paths=tuple(sorted({one for item in constraints for one in item.scope.excluded_paths})),
            excluded_modalities=tuple(
                sorted({one for item in constraints for one in item.scope.excluded_modalities})
            ),
        )
    except Exception:  # noqa: BLE001 - a scope nobody can name is reported as no scope at all
        return None


def _conflict_id(prefix: str, conflict_class: ConflictClass, parties: tuple[SemanticRef, ...]) -> str:
    slug = content_digest(sorted(item.text for item in parties))[:16]
    return f"{prefix}.{conflict_class.value.lower()}.{slug}"


def _build_conflict(
    prefix: str,
    *,
    conflict_class: ConflictClass,
    parties: tuple[SemanticRef, ...],
    semantic_paths: tuple[str, ...],
    revision: SemanticRef,
    constraints: tuple[Constraint, ...] = (),
    graph: AuthorityPolicyGraph | None = None,
    detected_by: IntentAuthorityRef | None = None,
    reason: str,
    consequence: ConflictConsequence | None = None,
    authority_refs: tuple[SemanticRef, ...] = (),
    evidence_refs: tuple[SemanticRef, ...] = (),
    conditions: tuple[Condition, ...] = (),
    rule_classes: tuple[str, ...] = (),
) -> SemanticConflict:
    """Assemble one detected conflict from the records that produced it.

    Everything the caller does not hand over is read back out of the parties, so the actor levels
    and the scope are the kernel's own observations rather than the detector caller's account of
    them. ``rule_classes`` is the one field it cannot observe: a constraint records what it forbids
    on which path, not which policy class owns the answer, so an empty tuple means "the reading
    did not say" and the conflict stays unscoped rather than being guessed at.
    """

    levels, granted = _authorities(constraints) if constraints else ((), ())
    wanted = consequence or conflict_class.default_consequence
    if _CONSEQUENCE_SEVERITY[wanted] < _CONSEQUENCE_SEVERITY[conflict_class.default_consequence]:
        wanted = conflict_class.default_consequence
    return SemanticConflict(
        conflict_id=_conflict_id(prefix, conflict_class, parties),
        conflict_class=conflict_class.value,
        consequence=wanted.value,
        parties=parties,
        semantic_paths=bound_paths(semantic_paths, "semantic_paths"),
        subject_scope=_meeting_scope(constraints) if constraints else None,
        conditions=conditions,
        authority_refs=granted or authority_refs,
        actor_levels=levels,
        rule_classes=tuple(rule_classes),
        evidence_refs=evidence_refs,
        detected_in_revision=revision,
        detected_by=detected_by,
        graph_ref=None if graph is None else graph.pin(),
        notes=reason,
    )


def _rule_class_map(value: Mapping[str, str] | None, known: Iterable[str]) -> dict[str, str]:
    """Validate a caller's statement of which policy class governs which rule.

    A mapping naming a constraint that is not in the reading is refused rather than ignored: a
    stale class would otherwise keep describing whatever rule took that id next, and the conflict
    would be filed under a policy the graph never granted.
    """

    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise SchemaValidationError("rule_classes must map constraint id to rule class")
    extra = sorted(set(value) - set(known))
    if extra:
        raise RefError(
            f"rule_classes describes {extra}, which is not in the bundle being read; a policy "
            "statement about an absent rule would silently reclassify whatever took its id"
        )
    return {key: require_identifier(value[key], "rule_classes[]") for key in sorted(value)}


def _classes_for(constraints: Iterable[Constraint], governs: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(sorted({governs[item.constraint_id] for item in constraints if item.constraint_id in governs}))


def detect_conflicts(
    *,
    bundle: ConstraintBundle,
    revision_ref: SemanticRef,
    context: Mapping[str, Any] | None = None,
    model: IntentModel | None = None,
    ambiguity: AmbiguityAssessment | None = None,
    graph: AuthorityPolicyGraph | None = None,
    detected_by: IntentAuthorityRef | None = None,
    rule_classes: Mapping[str, str] | None = None,
    conflict_prefix: str = "conflict",
) -> tuple[SemanticConflict, ...]:
    """Find the incompatibilities M03's own records prove, and decide none of them (§3, §24).

    Two properties are the reason this is a function over records rather than a scoring pass:

    * it reads no ``confidence``, no timestamp and no specificity ranking, because §5 and §7 make
      those evidence about a claim rather than authority over one. What is returned is a list of
      questions with their evidence attached;
    * it only reports a pair it can *name*. An inactive rule never appears in an active conflict,
      disjoint scopes never bind unless a STRICT cross-modal link the records themselves carry
      relates their channels, and a difference the kernel cannot state as an impossibility is
      left as a preference the work negotiates. ``CONDITIONAL_COLLISION`` is therefore never
      emitted here: two rules that clash only under a condition neither is active under are not
      yet a disagreement, and §24 gives no detector the standing to file one on speculation. When
      a human or an upstream module does hold the evidence that both branches are live, the entry
      point for that is :func:`declare_conflict`.

    ``revision_ref`` is the revision the reading was taken in, which is what makes a later rerun
    comparable instead of merely different. ``rule_classes`` maps constraint id to the policy
    class the caller holds over it; a constraint records what it binds, not who owns the answer, so
    an omitted mapping leaves the conflict unscoped rather than inventing a class for it.
    """

    if not isinstance(bundle, ConstraintBundle):
        raise SchemaValidationError("detect_conflicts expects a ConstraintBundle")
    if context is not None and not isinstance(context, Mapping):
        raise SchemaValidationError("context must be a mapping of context key to value")
    revision = require_bound_ref(revision_ref, "revision_ref", kind=RefKind.REVISION)
    prefix = require_identifier(conflict_prefix, "conflict_prefix")
    governs = _rule_class_map(rule_classes, bundle.constraint_ids)
    active: tuple[Constraint, ...] = tuple(sorted(bundle.active_for(context), key=lambda item: item.constraint_id))
    links = tuple(
        sorted(
            {
                (
                    frozenset(link.channels),
                    link.semantic_paths,
                )
                for item in active
                for link in item.cross_modal_links
                if link.consistency == ConsistencyClass.STRICT.value
            },
            key=lambda item: (sorted(item[0]), item[1]),
        )
    )
    found: list[SemanticConflict] = []
    for index, left in enumerate(active):
        for right in active[index + 1:]:
            bound = left.binds(right)
            if not (bound or _link_covering(links, left, right)):
                continue
            classified = _classify_pair(left, right, links, cross_only=not bound)
            if classified is None:
                continue
            wanted, reason = classified
            found.append(
                _build_conflict(
                    prefix,
                    conflict_class=wanted,
                    parties=(left.constraint_ref, right.constraint_ref),
                    semantic_paths=(left.semantic_path, right.semantic_path),
                    revision=revision,
                    constraints=(left, right),
                    graph=graph,
                    detected_by=detected_by,
                    reason=reason,
                    rule_classes=_classes_for((left, right), governs),
                    conditions=tuple(
                        sorted({*left.conditions, *right.conditions}, key=lambda item: item.context_key)
                    ),
                )
            )
    found.extend(
        _stale_derivations(prefix, active, model, revision=revision, graph=graph, detected_by=detected_by, governs=governs)
    )
    found.extend(
        _ambiguity_collisions(
            prefix, bundle, ambiguity, revision=revision, graph=graph, detected_by=detected_by, governs=governs
        )
    )
    unique = {item.conflict_id: item for item in found}
    conflicts = sorted(
        unique.values(),
        key=lambda item: (_CONSEQUENCE_RANK[item.consequence_enum], -len(item.parties), item.conflict_id),
    )
    if len(conflicts) > MAX_CONFLICTS:
        raise LimitExceededError(
            f"detection produced {len(conflicts)} conflicts, over the limit of {MAX_CONFLICTS}; the "
            "reading is reported as unusable rather than truncated, because a truncated conflict list "
            "hides exactly the blocker a reader needed"
        )
    return tuple(conflicts)


def _stale_derivations(
    prefix: str,
    active: tuple[Constraint, ...],
    model: IntentModel | None,
    *,
    revision: SemanticRef,
    graph: AuthorityPolicyGraph | None,
    detected_by: IntentAuthorityRef | None,
    governs: Mapping[str, str],
) -> list[SemanticConflict]:
    """Rules citing statements the model no longer carries (§3 ``STALE_DERIVATION``)."""

    if model is None:
        return []
    known = set(model.statement_ids)
    found: list[SemanticConflict] = []
    for item in sorted(active, key=lambda one: one.constraint_id):
        missing = sorted(set(item.source_statement_ids) - known)
        if not missing:
            continue
        found.append(
            _build_conflict(
                prefix,
                conflict_class=ConflictClass.STALE_DERIVATION,
                parties=(item.constraint_ref, model.model_ref),
                semantic_paths=(item.semantic_path,),
                revision=revision,
                constraints=(item,),
                graph=graph,
                detected_by=detected_by,
                reason=(
                    f"{item.constraint_id} was compiled from {missing}, which the intent model "
                    f"{model.model_id} no longer carries; the rule still binds while the reading it "
                    "came from is gone"
                ),
                evidence_refs=(item.constraint_ref, model.model_ref),
                rule_classes=_classes_for((item,), governs),
            )
        )
    return found


def _ambiguity_collisions(
    prefix: str,
    bundle: ConstraintBundle,
    ambiguity: AmbiguityAssessment | None,
    *,
    revision: SemanticRef,
    graph: AuthorityPolicyGraph | None,
    detected_by: IntentAuthorityRef | None,
    governs: Mapping[str, str],
) -> list[SemanticConflict]:
    """Unresolved readings that both feed work (§3 ``AMBIGUITY_COLLISION``)."""

    if ambiguity is None:
        return []
    present = set(bundle.constraint_ids)
    found: list[SemanticConflict] = []
    for record in sorted(ambiguity.ambiguities, key=lambda item: item.ambiguity_id):
        if record.resolved or len(record.candidate_readings) < 2:
            continue
        affected = tuple(one for one in record.affected_constraint_ids if one in present)
        if not affected:
            continue
        constraints = tuple(bundle.by_id(one) for one in affected)
        parties = (record.ambiguity_ref,) + tuple(item.constraint_ref for item in constraints)
        readings = " / ".join(record.candidate_readings)
        found.append(
            _build_conflict(
                prefix,
                conflict_class=ConflictClass.AMBIGUITY_COLLISION,
                parties=parties,
                semantic_paths=tuple(record.semantic_paths) + tuple(item.semantic_path for item in constraints),
                revision=revision,
                constraints=constraints,
                graph=graph,
                detected_by=detected_by,
                reason=(
                    f"{record.ambiguity_id} leaves {readings} undecided and both readings compile into "
                    f"{list(affected)}, so the work is being planned twice at once"
                ),
                evidence_refs=(record.ambiguity_ref,),
                rule_classes=_classes_for(constraints, governs),
            )
        )
    return found


#: --- declaration -------------------------------------------------------------


def declare_conflict(
    *,
    conflict_id: str,
    conflict_class: Any,
    parties: Iterable[SemanticRef],
    semantic_paths: Iterable[str],
    evidence_refs: Iterable[SemanticRef],
    rationale: str,
    revision_ref: SemanticRef,
    authority_refs: Iterable[SemanticRef] = (),
    consequence: Any = None,
    actor_levels: Iterable[str] = (),
    rule_classes: Iterable[str] = (),
    graph: AuthorityPolicyGraph | None = None,
    subject_scope: ConstraintScope | None = None,
    candidates: Iterable[CandidateResolution] = (),
    notes: str | None = None,
    metadata: Mapping[str, str] | None = None,
) -> SemanticConflict:
    """File a conflict the kernel cannot derive, with the evidence that says who could (§3).

    ``QUALITY_POLICY_CONFLICT`` needs M01's registry to know whether two obligations coexist and
    ``RIGHTS_SECURITY_CONFLICT`` needs M53/M54, so neither may be inferred from M03's own records.
    That is exactly why the entry point demands evidence: an upstream module's finding arrives as a
    citation, and an unattributed assertion of somebody else's boundary is refused by the record.
    """

    wanted = ConflictClass.parse(conflict_class, "conflict_class")
    refs = bound_refs(evidence_refs, "evidence_refs")
    if wanted.detected_by_kernel:
        raise ConflictBlockedError(
            f"{wanted.value} is derivable from the constraint records by detect_conflicts; filing it by "
            "hand would let a claimed contradiction be recorded without the pair that causes it"
        )
    return SemanticConflict(
        conflict_id=require_identifier(conflict_id, "conflict_id"),
        conflict_class=wanted.value,
        consequence=ConflictConsequence.parse(
            consequence or wanted.default_consequence, "consequence"
        ).value,
        parties=tuple(parties),
        semantic_paths=tuple(semantic_paths),
        subject_scope=subject_scope,
        authority_refs=tuple(authority_refs),
        actor_levels=tuple(actor_levels),
        rule_classes=tuple(rule_classes),
        candidates=tuple(candidates),
        evidence_refs=refs,
        detected_in_revision=revision_ref,
        graph_ref=None if graph is None else graph.pin(),
        notes=require_text(rationale, "rationale", maximum=MAX_RATIONALE_CHARS) if notes is None else notes,
        metadata=dict(metadata or {}),
    )


#: --- resolution --------------------------------------------------------------


def resolve_conflict(
    conflict: SemanticConflict,
    *,
    state: Any,
    decided_by: IntentAuthorityRef,
    rationale: str,
    recorded_in_revision: SemanticRef,
    resolution_id: str | None = None,
    graph: AuthorityPolicyGraph | None = None,
    receipt: OverrideReceipt | SemanticRef | None = None,
    human_decision: SemanticRef | None = None,
    scope_split: ScopeSplitProposal | None = None,
    fork: ExplorationFork | None = None,
    candidate_id: str | None = None,
    evidence_refs: Iterable[SemanticRef] = (),
    superseded_by: SemanticRef | None = None,
    notes: str | None = None,
    metadata: Mapping[str, str] | None = None,
) -> SemanticConflict:
    """Close a conflict in a named state, or refuse and say which evidence is missing (§13).

    This function is the only route to a resolved :class:`SemanticConflict`, and it adds no
    authority of its own: the receipt has to be the object :func:`~.overrides.issue_override`
    produced after consulting the graph, the policy exit has to be pinned to a graph that is
    admitted, and a split has to land every party in exactly one branch. Compatibility is the one
    state that asks for nobody's permission, because two rules that can both be satisfied need no
    decision to keep being satisfied.
    """

    if not isinstance(conflict, SemanticConflict):
        raise SchemaValidationError("resolve_conflict expects a SemanticConflict")
    wanted = ConflictResolutionState.parse(state, "state")
    if not wanted.is_resolved:
        raise ConflictBlockedError(
            f"{wanted.value} is not a resolution; escalate the conflict or resolve it, and do not "
            "record an open question as closed work"
        )
    conflict.class_enum  # parsed once for the message below
    if wanted not in conflict.admissible_resolutions:
        raise ConflictBlockedError(
            f"a {conflict.conflict_class} conflict cannot be closed by {wanted.value}; §13 offers "
            f"{sorted(item.value for item in conflict.admissible_resolutions)}"
        )
    if conflict.resolved:
        raise ConflictBlockedError(
            f"conflict {conflict.conflict_id} is already {conflict.resolution_state}; §13's records "
            "are immutable and versioned, so a second verdict is a supersession, not an edit"
        )
    chosen = None
    if candidate_id is not None:
        chosen = next(
            (item for item in conflict.candidates if item.candidate_id == candidate_id), None
        )
        if chosen is None:
            raise RefError(
                f"candidate {candidate_id} was not offered by {conflict.conflict_id}; deciding an "
                "option nobody listed is how a resolution stops being explainable"
            )
        if chosen.produces != wanted.value:
            raise ConflictBlockedError(
                f"candidate {candidate_id} would produce {chosen.produces}, not {wanted.value}"
            )
    receipt_ref: SemanticRef | None = None
    if wanted.requires_receipt:
        if receipt is None:
            raise OverrideRefusedError(
                f"conflict {conflict.conflict_id} cannot close as {wanted.value} without the override "
                "receipt; §24 refuses the quiet weakening that an unbacked override would be"
            )
        if isinstance(receipt, OverrideReceipt):
            if receipt.conflict_ref is not None and receipt.conflict_ref.ref_id != conflict.conflict_id:
                raise RefError(
                    f"receipt {receipt.override_id} was issued against conflict "
                    f"{receipt.conflict_ref.ref_id}, not {conflict.conflict_id}; a decision about one "
                    "disagreement may not be spent on another"
                )
            if graph is not None:
                receipt.verify_against(graph)
            graph = receipt.graph_ref if graph is None else graph
        receipt_ref = receipt.receipt_ref if isinstance(receipt, OverrideReceipt) else receipt
    elif receipt is not None:
        raise OverrideRefusedError(
            f"a receipt was attached to a {wanted.value} resolution, which is not an override; the "
            "record would claim two grounds for one decision"
        )
    graph_ref = None
    if wanted.requires_policy_pin:
        if graph is None:
            raise AuthorityError(
                f"{wanted.value} resolution of {conflict.conflict_id} needs the policy graph it was "
                "decided under; naming no graph is how a resolution survives a change of authority "
                "nobody approved (§5)"
            )
        if isinstance(graph, AuthorityPolicyGraph):
            graph.require_admitted(f"{wanted.value} resolution of {conflict.conflict_id}")
            graph_ref = graph.pin()
        else:
            graph_ref = graph
    elif isinstance(graph, AuthorityPolicyGraph) and conflict.graph_ref is not None:
        conflict.graph_ref.require_current(graph, f"resolution of {conflict.conflict_id}")
        graph_ref = graph.pin()
    if graph_ref is not None and conflict.graph_ref is not None and graph_ref.pin_id != conflict.graph_ref.pin_id:
        raise StaleSemanticError(
            f"conflict {conflict.conflict_id} was detected under {conflict.graph_ref.pin_id} and is "
            f"being resolved under {graph_ref.pin_id}; re-detect against the current policy so the "
            "reader sees the disagreement the new graph actually implies (§26)"
        )
    if wanted is ConflictResolutionState.RESOLVED_BY_SCOPE_SPLIT:
        _require_covers_parties(scope_split, conflict, "split")
    elif scope_split is not None:
        raise SchemaValidationError(f"a {wanted.value} resolution cannot carry a scope split")
    if wanted is ConflictResolutionState.RESOLVED_AS_EXPLORATION_FORK:
        _require_covers_parties(fork, conflict, "fork")
    elif fork is not None:
        raise SchemaValidationError(f"a {wanted.value} resolution cannot carry a fork")
    resolution = ConflictResolution(
        resolution_id=resolution_id or f"res.{conflict.conflict_id}",
        conflict_ref=conflict.conflict_ref,
        state=wanted.value,
        rationale=rationale,
        decided_by=decided_by,
        recorded_in_revision=recorded_in_revision,
        receipt_ref=receipt_ref,
        human_decision=human_decision,
        graph_ref=graph_ref,
        scope_split=scope_split,
        fork=fork,
        superseded_by=superseded_by,
        candidate_id=candidate_id,
        evidence_refs=tuple(bound_refs(evidence_refs, "evidence_refs", minimum=0)),
        notes=notes,
        metadata=dict(metadata or {}),
    )
    resolution.require_admissible_for(conflict.conflict_class)
    return conflict.with_resolution(resolution)


def _require_covers_parties(carrier: Any, conflict: SemanticConflict, label: str) -> None:
    """Every party must land in the split or fork that claims to resolve it (§14)."""

    if carrier is None:
        raise ScopeError(
            f"conflict {conflict.conflict_id} resolves as a {label} with no {label}; one side kept "
            "quietly is a deletion wearing a resolution's name"
        )
    covered = {item.text for item in carrier.party_refs}
    missing = sorted(item.text for item in conflict.parties if item.text not in covered)
    if missing:
        raise ScopeError(
            f"{label} for {conflict.conflict_id} does not carry {missing}; §14's economy is that both "
            "rules stay in force somewhere, and a party left out is a rule dropped"
        )


def escalate_conflict(
    conflict: SemanticConflict,
    *,
    to_state: Any,
    rationale: str,
    metadata: Mapping[str, str] | None = None,
) -> SemanticConflict:
    """Move a conflict into an open state that names who owes the next move (§13, §15).

    Escalation is deliberately not a resolution: ``NEEDS_HUMAN_DECISION`` and
    ``BLOCKED_UNOVERRIDABLE`` leave the work blocked, so no actor, however senior, can convert a
    question into a verdict by relabelling it.
    """

    wanted = ConflictResolutionState.parse(to_state, "to_state")
    if wanted.is_resolved:
        raise ConflictBlockedError(
            f"{wanted.value} is a resolution, not an escalation; use resolve_conflict and supply the "
            "evidence it demands"
        )
    if wanted not in conflict.admissible_resolutions:
        raise ConflictBlockedError(
            f"a {conflict.conflict_class} conflict cannot be escalated to {wanted.value}"
        )
    if conflict.resolved:
        raise ConflictBlockedError(
            f"conflict {conflict.conflict_id} is already {conflict.resolution_state}; §13's records "
            "are versioned, so a closed conflict is superseded rather than reopened"
        )
    from dataclasses import replace as _replace

    return _replace(
        conflict,
        resolution_state=wanted.value,
        resolution=None,
        notes=require_text(rationale, "rationale", maximum=MAX_RATIONALE_CHARS),
        metadata=bounded_metadata(dict(metadata or {}), "metadata"),
    )


#: --- reporting ---------------------------------------------------------------


def rank_conflicts(conflicts: Iterable[SemanticConflict]) -> tuple[SemanticConflict, ...]:
    """The reporting order: stake, then blast radius, then id (§15).

    Never a decision order. Two conflicts with the same consequence are equally urgent here, and
    the tie-break is a sort key chosen so a reader sees the same list twice, not a ranking that
    settles which one the work answers first.
    """

    items = tuple(conflicts)
    for item in items:
        if not isinstance(item, SemanticConflict):
            raise SchemaValidationError("rank_conflicts expects SemanticConflict records")
    return tuple(
        sorted(
            items,
            key=lambda item: (
                _CONSEQUENCE_RANK[item.consequence_enum],
                -len(item.parties),
                -len(item.semantic_paths),
                item.conflict_id,
            ),
        )
    )


def clarification_plan(conflicts: Iterable[SemanticConflict]) -> tuple[ConflictQuestion, ...]:
    """The smallest set of questions that unblocks the work, one per open conflict (§15).

    A resolved conflict asks nothing, and a conflict whose consequences do not stop the contract is
    reported as non-blocking so that a queue of five questions does not read as five blockers.
    """

    plan: list[ConflictQuestion] = []
    for conflict in rank_conflicts(conflicts):
        if conflict.resolved:
            continue
        authority_needed = None
        if conflict.consequence_enum.requires_authorized_resolution:
            authority_needed = AuthorityLevel.GOVERNED_POLICY.value
        elif conflict.requires_human_decision:
            authority_needed = AuthorityLevel.HUMAN_OWNER.value
        plan.append(
            ConflictQuestion(
                question_id=f"ask.{conflict.conflict_id}",
                conflict_ref=conflict.conflict_ref,
                question=(
                    f"Which of {list(conflict.party_ids)} holds for {list(conflict.semantic_paths)}: "
                    f"{conflict.conflict_class}?"
                ),
                asks_for=(
                    _QuestionTarget.POLICY_OWNER.value
                    if conflict.consequence_enum.requires_authorized_resolution
                    else _QuestionTarget.HUMAN_OWNER.value
                    if conflict.requires_human_decision
                    else _QuestionTarget.PROJECT_RECORD.value
                ),
                consequence=conflict.consequence,
                affected_paths=conflict.semantic_paths,
                dependents=conflict.invalidated,
                blocking=conflict.blocks_contract,
                authority_needed=authority_needed,
                rationale=conflict.notes,
            )
        )
    return tuple(sorted(plan, key=lambda item: item.report_rank))

