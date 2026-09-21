"""F-M03-13/14 S05 override receipts, proposals, leases and semantic debt.

An override in M03 is a *record*, never an edit. §8 states the rule and this module enforces
it: when a rule is relaxed, disabled or narrowed, the original stays in history, a receipt
names who authorised the change against which policy version, and the new effective state is
written down beside the old one rather than over it. Everything here is constructed from
bound refs and digests for that reason — a receipt whose targets could drift is a receipt
about nothing.

Three shapes are kept deliberately separate, because collapsing them is the easiest way to
lose the distinction §24 depends on: an ``OverrideProposal`` is an agent's request and carries
no authority at all, an ``OverrideReceipt`` is an effective decision made by an actor the
admitted policy graph accepts, and an ``OverrideDebt`` is the tracked cost of a temporary or
risky relaxation. The proposal type cannot become a receipt by having a field flipped; only
:func:`issue_override` and :func:`authorize_proposal` produce receipts, and both ask the graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .authority import (
    AuthorityDecision,
    AuthorityPolicyGraph,
    AuthorityPolicyGraphRef,
    OverrideAction,
)
from .base import Labeled, Record, of
from .constraints import Constraint, ConstraintScope, ConstraintPolarity, ConstraintStrength
from .errors import (
    AuthorityError,
    LimitExceededError,
    OverrideRefusedError,
    QualityAuthorityError,
    RefError,
    SchemaValidationError,
    ScopeError,
    StaleSemanticError,
)
from .fingerprints import ChangeKind
from .freshness import require_revision_ordinal
from .identity import RefKind, SemanticRef, require_bound_ref
from .intent import IntentAuthorityRef, IntentStatement
from .limits import (
    MAX_CONFLICT_PARTIES,
    MAX_OVERRIDE_DEBT,
    MAX_OVERRIDES,
    MAX_RATIONALE_CHARS,
    MAX_SCOPE_PATHS,
)
from .predicates import PredicateCall
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
    "OVERRIDE_COMPILER_VERSION",
    "InvalidationTarget",
    "OverrideDebt",
    "OverrideDebtKind",
    "OverrideLedger",
    "OverrideProposal",
    "OverrideReceipt",
    "SemanticStateSnapshot",
    "TemporaryOverrideLease",
    "authorize_proposal",
    "bound_paths",
    "bound_refs",
    "covers_path",
    "invalidation_targets",
    "issue_override",
    "propose_override",
]

OVERRIDE_COMPILER_VERSION = "m03-override-v1"


class InvalidationTarget(Labeled):
    """What a downstream artifact must treat as suspect when an override takes effect (§8).

    These are the compiled layers M03 itself emits, so the hint list stays inside the module's
    own knowledge. It is a vocabulary rather than a free-text field because "invalidate relevant
    things" is not actionable, and a downstream cache that has to guess which slice an override
    touched will guess conservatively and rebuild everything — which is how an override ledger
    becomes theatre.
    """

    INTENT_FINGERPRINT = "INTENT_FINGERPRINT"
    CONSTRAINT_FINGERPRINT = "CONSTRAINT_FINGERPRINT"
    SEMANTIC_SLICE = "SEMANTIC_SLICE"
    REUSE_PASSPORT = "REUSE_PASSPORT"
    FRESHNESS_VECTOR = "FRESHNESS_VECTOR"
    CONTRACT_SET = "CONTRACT_SET"
    EXECUTION_BUNDLE = "EXECUTION_BUNDLE"
    EXPLANATION_GRAPH = "EXPLANATION_GRAPH"
    MERGE_ANALYSIS = "MERGE_ANALYSIS"
    READINESS_REPORT = "READINESS_REPORT"

    @property
    def mandatory_for_relaxation(self) -> bool:
        """Layers that must always be named when a rule is weakened.

        A relaxation that invalidates only the constraint fingerprint would leave a compiled
        contract set and an execution bundle holding the old, stricter obligation — which reads
        as safe for about one release cycle, until somebody notices the work was never actually
        checked against the rule that was relaxed.
        """

        return self in {
            InvalidationTarget.CONTRACT_SET,
            InvalidationTarget.EXECUTION_BUNDLE,
            InvalidationTarget.INTENT_FINGERPRINT,
            InvalidationTarget.CONSTRAINT_FINGERPRINT,
        }


class OverrideDebtKind(Labeled):
    """The four debts §12 recognises, and nothing else.

    The list is closed because an open "debt kind" field is where a defect acceptance would
    eventually be filed as semantic debt, and M01's ``QualityDebt`` is a different authority
    with a different lifecycle.
    """

    TEMPORARY_BRAND_EXCEPTION = "TEMPORARY_BRAND_EXCEPTION"
    EXPERIMENTAL_RELAXATION = "EXPERIMENTAL_RELAXATION"
    ACCEPTED_AMBIGUITY_FOR_EXPLORATION = "ACCEPTED_AMBIGUITY_FOR_EXPLORATION"
    OLDER_POLICY_IN_USE = "OLDER_POLICY_IN_USE"

    @property
    def defaults_release_blocking(self) -> bool:
        """Whether leaving this open stops a release unless project policy says otherwise.

        Defaults are per kind rather than global because §12 makes closure a *policy* question
        and the kinds differ in how much they can rot: an older policy version in active use is a
        standing exposure, while an ambiguity accepted for exploration is a deliberate, bounded
        creative choice.
        """

        return self in {
            OverrideDebtKind.EXPERIMENTAL_RELAXATION,
            OverrideDebtKind.OLDER_POLICY_IN_USE,
        }


def bound_refs(value: Any, name: str, *, kind: RefKind | None = None, minimum: int = 1) -> tuple[SemanticRef, ...]:
    """Coerce a bound, sorted, de-duplicated ref list with a floor on its length."""

    if value is None:
        value = ()
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Iterable):
        raise SchemaValidationError(f"{name} must be a list of semantic refs")
    items = tuple(
        sorted(
            (require_bound_ref(item, f"{name}[]", kind=kind) for item in value),
            key=lambda item: item.text,
        )
    )
    known = [item.text for item in items]
    duplicates = sorted({item for item in known if known.count(item) > 1})
    if duplicates:
        raise SchemaValidationError(f"{name} repeats refs {duplicates}")
    if len(items) > MAX_CONFLICT_PARTIES:
        raise LimitExceededError(f"{name} exceeds {MAX_CONFLICT_PARTIES} refs")
    if len(items) < minimum:
        raise SchemaValidationError(f"{name} needs at least {minimum} bound ref")
    return items


def bound_paths(value: Any, name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise SchemaValidationError(f"{name} must be a list of semantic paths")
    items = tuple(sorted({require_semantic_path(item, f"{name}[]") for item in value}))
    if len(items) > MAX_SCOPE_PATHS:
        raise LimitExceededError(f"{name} exceeds {MAX_SCOPE_PATHS} paths")
    return items


def invalidation_targets(value: Any, name: str) -> tuple[str, ...]:
    if value is None:
        value = ()
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise SchemaValidationError(f"{name} must be a list of invalidation targets")
    items = tuple(sorted({InvalidationTarget.parse(item, f"{name}[]").value for item in value}))
    duplicates = sorted({item for item in items if items.count(item) > 1})
    if duplicates:
        raise SchemaValidationError(f"{name} repeats {duplicates}")
    return items


def covers_path(prefix: str, path: str) -> bool:
    return path == prefix or path.startswith(prefix + ".")


def _predicate_face(predicate: PredicateCall) -> dict[str, str]:
    """Record what a rule demands as bounded string facts so a snapshot can be compared.

    The argument tree is collapsed into a digest of its canonical form rather than retyped into
    the snapshot: the value field is string-bounded by design, and a nested structure smuggled
    through it would be read later as semantics, which is exactly the failure
    ``bounded_metadata`` exists to refuse.
    """

    encoded = predicate.fingerprint_inputs()
    return {
        "predicate": str(encoded.get("predicate", "")),
        "arguments_digest": content_digest(encoded.get("arguments")),
    }


@dataclass(frozen=True)
class SemanticStateSnapshot(Record):
    """The constraint-relevant face of a rule, at one side of an override (§8).

    Storing both sides is what lets the kernel check the *label* of an action rather than
    trusting it: "RELAX" over two snapshots that actually show HARD→SOFT is honoured, and
    "RELAX" over snapshots showing SOFT→HARD is refused. Without this, the receipt that exists to
    prevent silent weakening would itself be a field somebody types.
    """

    snapshot_id: str
    semantic_path: str
    subject_refs: tuple[SemanticRef, ...] = ()
    polarity: str | None = None
    strength: str | None = None
    mandatory: bool | None = None
    scope: ConstraintScope | None = None
    value: Mapping[str, str] = field(default_factory=dict)
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "snapshot_id", require_identifier(self.snapshot_id, "snapshot_id"))
        object.__setattr__(self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path"))
        object.__setattr__(self, "subject_refs", bound_refs(self.subject_refs, "subject_refs"))
        if self.polarity is not None:
            object.__setattr__(self, "polarity", ConstraintPolarity.parse(self.polarity, "polarity").value)
        if self.strength is not None:
            object.__setattr__(self, "strength", ConstraintStrength.parse(self.strength, "strength").value)
        if self.mandatory is not None and not isinstance(self.mandatory, bool):
            raise SchemaValidationError("mandatory must be a boolean or absent")
        if self.scope is not None:
            scope = ConstraintScope.coerce(self.scope, "scope")
            object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "value", bounded_metadata(self.value, "value"))
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=2048))

    def _view(self) -> dict[str, Any]:
        return {
            "semantic_path": self.semantic_path,
            "subjects": sorted(item.text for item in self.subject_refs),
            "polarity": self.polarity,
            "strength": self.strength,
            "mandatory": self.mandatory,
            "scope": self.scope.to_payload() if self.scope is not None else None,
            "value": dict(sorted(self.value.items())),
        }

    @property
    def state_digest(self) -> str:
        return content_digest(self._view())

    @property
    def polarity_enum(self) -> ConstraintPolarity | None:
        return ConstraintPolarity.parse(self.polarity) if self.polarity else None

    @property
    def strength_enum(self) -> ConstraintStrength | None:
        return ConstraintStrength.parse(self.strength) if self.strength else None

    @classmethod
    def of_constraint(cls, constraint: Constraint, *, snapshot_id: str | None = None) -> "SemanticStateSnapshot":
        """Read the enforcing face of a rule, ignoring how it is explained.

        ``rationale`` and ``metadata`` stay out for the same reason fingerprints exclude
        wording: a re-explained rule is the same obligation, and including prose here would make
        every rewording look like a semantic move that needs a receipt.
        """

        return cls(
            snapshot_id=snapshot_id or f"snap.{constraint.constraint_id}",
            semantic_path=constraint.semantic_path,
            subject_refs=(constraint.constraint_ref,),
            polarity=constraint.polarity,
            strength=constraint.strength,
            mandatory=constraint.mandatory,
            scope=constraint.scope,
            value=_predicate_face(constraint.predicate),
        )

    @classmethod
    def of_statement(cls, statement: IntentStatement, *, snapshot_id: str | None = None) -> "SemanticStateSnapshot":
        return cls(
            snapshot_id=snapshot_id or f"snap.{statement.statement_id}",
            semantic_path=statement.semantic_path,
            subject_refs=(statement.statement_ref,),
            mandatory=statement.mandatory,
            value=dict(statement.value),
            notes=None,
        )

    def movement_to(self, after: "SemanticStateSnapshot | None") -> tuple[str, ...]:
        """Classify what changed, reusing :class:`ChangeKind` rather than inventing a second set.

        Ordered and possibly multi-valued: an override that both softens a rule and narrows it is
        two movements, and reporting only the first would let a widening ride along inside a
        label that sounded like a narrowing.
        """

        if after is None:
            return (ChangeKind.REMOVED.value,)
        if not isinstance(after, SemanticStateSnapshot):
            raise SchemaValidationError("movement_to expects a SemanticStateSnapshot")
        kinds: list[str] = []
        if self.polarity_enum is not None and after.polarity_enum is not None:
            if self.polarity_enum is not after.polarity_enum:
                strict = {ConstraintPolarity.REQUIRE, ConstraintPolarity.FORBID}
                if {self.polarity_enum, after.polarity_enum} <= strict:
                    kinds.append(ChangeKind.POLARITY_FLIPPED.value)
                else:
                    kinds.append(ChangeKind.REPREDICATED.value)
        before_rank = self.strength_enum.rank if self.strength_enum else None
        after_rank = after.strength_enum.rank if after.strength_enum else None
        if before_rank is not None and after_rank is not None and before_rank != after_rank:
            kinds.append(
                ChangeKind.STRENGTHENED.value if after_rank > before_rank else ChangeKind.RELAXED.value
            )
        if self.mandatory is not None and after.mandatory is not None and self.mandatory != after.mandatory:
            kinds.append(ChangeKind.STRENGTHENED.value if after.mandatory else ChangeKind.RELAXED.value)
        if self.scope is not None and after.scope is not None and self.scope != after.scope:
            kinds.append(ChangeKind.RESCOPED.value)
        if self.value != after.value or sorted(item.ref_id for item in self.subject_refs) != sorted(
            item.ref_id for item in after.subject_refs
        ):
            kinds.append(ChangeKind.REPREDICATED.value)
        if not kinds:
            kinds.append(ChangeKind.RESTATED.value)
        return tuple(sorted(set(kinds)))

    def weakens_against(self, after: "SemanticStateSnapshot | None") -> bool:
        """Whether the movement makes the work less constrained.

        Used only to *contradict* a caller's action label, never to pick a winner: the decision
        of what may be relaxed stays with the policy graph.
        """

        return ChangeKind.RELAXED.value in self.movement_to(after) or after is None


SemanticStateSnapshot.NESTED = {"subject_refs": of(SemanticRef), "scope": of(ConstraintScope)}


@dataclass(frozen=True)
class OverrideReceipt(Record):
    """The immutable record that one rule was deliberately not enforced as written (§8).

    The receipt is the *only* place M03 states that an obligation was relaxed, and it is written
    to be re-checked rather than to be read: it carries the policy graph version it was decided
    against so a later compilation can prove the permission still describes the same policy, the
    two state snapshots so the action label can be verified mechanically, and the revision it was
    recorded in so §7's "supersession needs a revision" is a field rather than a promise.
    """

    override_id: str
    action: str
    rule_class: str
    semantic_path: str
    target_refs: tuple[SemanticRef, ...] = ()
    actor: IntentAuthorityRef | None = None
    graph_ref: AuthorityPolicyGraphRef | None = None
    permission: AuthorityDecision | None = None
    reason: str = ""
    previous_state: SemanticStateSnapshot | None = None
    effective_state: SemanticStateSnapshot | None = None
    requested_scope: ConstraintScope | None = None
    effective_scope: ConstraintScope | None = None
    conflict_ref: SemanticRef | None = None
    recorded_in_revision: SemanticRef | None = None
    approval_refs: tuple[SemanticRef, ...] = ()
    human_decision: SemanticRef | None = None
    issued_at_revision: int | None = None
    expires_after_revision: int | None = None
    review_condition: str | None = None
    lease_id: str | None = None
    restores_override_id: str | None = None
    invalidation: tuple[str, ...] = ()
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)
    compiler_version: str = OVERRIDE_COMPILER_VERSION
    schema_version: str = SCHEMA_VERSION
    contract_version: str = ""

    #: §8 states this explicitly, so it is a constant rather than something to be remembered.
    deletes_original_rule = False
    grants_self_authority = False
    overrides_m01_quality = False
    overrides_m02_history = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "override_id", require_identifier(self.override_id, "override_id"))
        action = OverrideAction.parse(self.action, "action")
        object.__setattr__(self, "action", action.value)
        object.__setattr__(self, "rule_class", require_identifier(self.rule_class, "rule_class"))
        object.__setattr__(self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path"))
        object.__setattr__(self, "target_refs", bound_refs(self.target_refs, "target_refs"))
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=MAX_RATIONALE_CHARS))
        if self.actor is None or self.graph_ref is None or self.permission is None:
            raise AuthorityError(
                f"override {self.override_id} has no actor, policy pin or permission; a receipt "
                "without the decision it came from is an assertion that something was allowed"
            )
        if not self.actor.level.self_asserting_is_enough and action.weakens:
            raise AuthorityError(
                f"override {self.override_id} records a {action.value} granted to a "
                f"{self.actor.level.value} actor; only a governed or human source may weaken a rule "
                "(§5.5, §24)"
            )
        permission = AuthorityDecision.coerce(self.permission, "permission")
        object.__setattr__(self, "permission", permission)
        if not permission.may:
            raise AuthorityError(
                f"override {self.override_id} cites a decision that denied it ({permission.reason}); a "
                "receipt cannot launder a refusal"
            )
        if permission.action != action.value or permission.rule_class != self.rule_class:
            raise AuthorityError(
                f"override {self.override_id} pairs a {action.value}/{self.rule_class} receipt with a "
                f"{permission.action}/{permission.rule_class} permission; the two must describe the "
                "same decision or the audit trail is fiction"
            )
        graph_ref = AuthorityPolicyGraphRef.coerce(self.graph_ref, "graph_ref")
        object.__setattr__(self, "graph_ref", graph_ref)
        if permission.graph_version != graph_ref.version:
            raise AuthorityError(
                f"override {self.override_id} was decided against policy version "
                f"{permission.graph_version} but pins {graph_ref.version}"
            )
        if permission.semantic_path not in {self.semantic_path, "unscoped"}:
            raise RefError(
                f"override {self.override_id} addresses {self.semantic_path} while its permission "
                f"speaks for {permission.semantic_path}"
            )
        previous = self.previous_state
        if previous is None:
            raise SchemaValidationError(
                f"override {self.override_id} names no previous state; §8 requires the rule as it "
                "stood, because 'we relaxed something' is not evidence of what"
            )
        snapshot = SemanticStateSnapshot.coerce(previous, "previous_state")
        object.__setattr__(self, "previous_state", snapshot)
        effective = SemanticStateSnapshot.coerce(self.effective_state, "effective_state") if self.effective_state is not None else None
        object.__setattr__(self, "effective_state", effective)
        self._require_action_matches_movement(action, snapshot, effective)
        requested = ConstraintScope.coerce(self.requested_scope, "requested_scope") if self.requested_scope is not None else snapshot.scope
        granted = ConstraintScope.coerce(self.effective_scope, "effective_scope") if self.effective_scope is not None else requested
        if requested is None or granted is None:
            raise ScopeError(
                f"override {self.override_id} cannot be checked for scope reach because one side "
                "carries no scope; an unbounded override is the unbounded claim §5.14 refuses"
            )
        object.__setattr__(self, "requested_scope", requested)
        object.__setattr__(self, "effective_scope", granted)
        widened = _scope_widened(requested, granted)
        if widened:
            raise ScopeError(
                f"override {self.override_id} grants more reach than it was asked for: {widened}; an "
                "approved relaxation may be narrowed in review but never widened, or the extra "
                "subjects are bound by a decision nobody authorised"
            )
        object.__setattr__(self, "conflict_ref", optional_bound_ref(self.conflict_ref, "conflict_ref", RefKind.CONFLICT))
        object.__setattr__(
            self,
            "recorded_in_revision",
            require_bound_ref(self.recorded_in_revision, "recorded_in_revision", kind=RefKind.REVISION),
        )
        object.__setattr__(self, "approval_refs", optional_bound_refs(self.approval_refs, "approval_refs"))
        object.__setattr__(
            self, "human_decision", optional_bound_ref(self.human_decision, "human_decision", RefKind.REVISION)
        )
        if self.issued_at_revision is not None:
            object.__setattr__(self, "issued_at_revision", require_revision_ordinal(self.issued_at_revision, "issued_at_revision"))
        if self.expires_after_revision is not None:
            object.__setattr__(
                self, "expires_after_revision", require_revision_ordinal(self.expires_after_revision, "expires_after_revision")
            )
            if self.issued_at_revision is not None and self.expires_after_revision < self.issued_at_revision:
                raise SchemaValidationError(
                    f"override {self.override_id} expires at revision {self.expires_after_revision}, "
                    "before it was issued at revision "
                    f"{self.issued_at_revision}"
                )
        if action is OverrideAction.TEMPORARY_EXPERIMENT and self.expires_after_revision is None:
            raise OverrideRefusedError(
                f"override {self.override_id} experiments with a rule but never stops; §11 makes an "
                "experiment expire or it is a permanent relaxation with a friendly name"
            )
        if action is OverrideAction.RESTORE_PRIOR and self.restores_override_id is None:
            raise SchemaValidationError(
                f"override {self.override_id} restores a prior state without naming what it restores"
            )
        if self.restores_override_id is not None:
            object.__setattr__(self, "restores_override_id", require_identifier(self.restores_override_id, "restores_override_id"))
            if self.restores_override_id == self.override_id:
                raise SchemaValidationError("an override cannot restore itself")
        if self.lease_id is not None:
            object.__setattr__(self, "lease_id", require_identifier(self.lease_id, "lease_id"))
        elif action.requires_lease:
            raise OverrideRefusedError(
                f"override {self.override_id} is a temporary experiment with no lease, so nothing "
                "owns its expiry (§11)"
            )
        if self.review_condition is not None:
            object.__setattr__(self, "review_condition", require_text(self.review_condition, "review_condition", maximum=512))
        invalidation = invalidation_targets(self.invalidation, "invalidation")
        if action.weakens:
            missing = sorted(
                item.value for item in InvalidationTarget if item.mandatory_for_relaxation and item.value not in invalidation
            )
            if missing:
                raise OverrideRefusedError(
                    f"override {self.override_id} weakens a rule but does not invalidate {missing}; a "
                    "relaxation that leaves compiled obligations in place is the failure mode §11 "
                    "describes as an override that never died"
                )
        object.__setattr__(self, "invalidation", invalidation)
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=2048))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        object.__setattr__(self, "compiler_version", require_version_text(self.compiler_version, "compiler_version"))
        object.__setattr__(self, "schema_version", require_version_text(self.schema_version, "schema_version"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @staticmethod
    def _require_action_matches_movement(
        action: OverrideAction, before: SemanticStateSnapshot, after: SemanticStateSnapshot | None
    ) -> None:
        """Refuse an action label that the recorded states contradict (§10).

        The gradient is only real if a receipt can be caught lying about it, and the states are
        the part a caller cannot argue with after the fact.
        """

        movement = set(before.movement_to(after))
        allowed = _ACTION_MOVEMENTS[action]
        if movement <= {ChangeKind.RESTATED.value, ChangeKind.EQUIVALENT.value}:
            raise OverrideRefusedError(
                f"action {action.value} changes nothing between the recorded states; a receipt for a "
                "no-op would let a later reader believe an obligation was deliberated on"
            )
        outside = sorted(movement - allowed)
        if outside:
            raise OverrideRefusedError(
                f"action {action.value} cannot describe movement {outside}; the policy grants "
                f"{sorted(allowed)}, and a label chosen to sit inside a lenient edge is how a "
                "relaxation gets filed as a replacement"
            )

    @property
    def action_enum(self) -> OverrideAction:
        return OverrideAction.parse(self.action)

    @property
    def weakens(self) -> bool:
        return self.action_enum.weakens

    @property
    def is_temporary(self) -> bool:
        return self.expires_after_revision is not None

    def expired_at(self, revision_ordinal: int) -> bool:
        ordinal = require_revision_ordinal(revision_ordinal, "revision_ordinal")
        return self.expires_after_revision is not None and ordinal > self.expires_after_revision

    def require_live(self, revision_ordinal: int, action: str) -> None:
        """Refuse to let a lapsed permission keep steering work (§11).

        The message names the invalidation list rather than saying "stale", because the reader's
        next question is always which artifacts have to be rebuilt, and §11's warning about a
        cached provider workflow is answered by that list.
        """

        if self.expired_at(revision_ordinal):
            raise StaleSemanticError(
                f"{action} relied on override {self.override_id}, which expired at revision "
                f"{self.expires_after_revision} and is being read at {revision_ordinal}; the rule it "
                f"relaxed is in force again and {sorted(self.invalidation)} must be recompiled (§11)"
            )

    def verify_against(self, graph: AuthorityPolicyGraph, *, revision_ordinal: int | None = None) -> "OverrideReceipt":
        """Re-run the decision against the policy this receipt pins.

        Returns the receipt when the permission still holds, and raises when the policy moved —
        which is a staleness report, not a change of verdict: an override that was authorised
        then is not retroactively unauthorised, but nothing may treat it as *current* until the
        decision is re-issued against the new graph.
        """

        if not isinstance(graph, AuthorityPolicyGraph):
            raise SchemaValidationError("verify_against expects an AuthorityPolicyGraph")
        self.graph_ref.require_current(graph, f"override {self.override_id}")
        decision = graph.evaluate(
            actor=self.actor,
            action=self.action,
            rule_class=self.rule_class,
            semantic_path=self.semantic_path,
            human_decision=self.human_decision,
        )
        if not decision.may:
            raise StaleSemanticError(
                f"override {self.override_id} no longer holds under {graph.graph_id}@{graph.version}: "
                f"{decision.reason}"
            )
        if revision_ordinal is not None:
            self.require_live(revision_ordinal, "verification")
        return self

    def movement(self) -> tuple[str, ...]:
        return self.previous_state.movement_to(self.effective_state)

    @property
    def receipt_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.RECEIPT.value, ref_id=self.override_id).with_digest(self.receipt_digest)

    @property
    def receipt_digest(self) -> str:
        """Digest over the decision itself, excluding how it is narrated.

        ``notes``, ``metadata`` and ``review_condition`` describe the decision; ``reason`` is part
        of the decision because it is the justification the actor gave, and a receipt reworded in
        its reason is a different receipt.
        """

        return content_digest(self.fingerprint_inputs())

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "override_id": self.override_id,
            "action": self.action,
            "rule_class": self.rule_class,
            "semantic_path": self.semantic_path,
            "targets": sorted(item.text for item in self.target_refs),
            "actor": self.actor.to_payload() if self.actor is not None else None,
            "graph": self.graph_ref.pin_id if self.graph_ref is not None else None,
            "graph_digest": self.graph_ref.graph_digest if self.graph_ref is not None else None,
            "permission": self.permission.decision_digest if self.permission is not None else None,
            "reason": self.reason,
            "previous": self.previous_state.state_digest if self.previous_state else None,
            "effective": self.effective_state.state_digest if self.effective_state else None,
            "requested_scope": self.requested_scope.to_payload() if self.requested_scope else None,
            "effective_scope": self.effective_scope.to_payload() if self.effective_scope else None,
            "conflict": self.conflict_ref.text if self.conflict_ref is not None else None,
            "recorded_in": self.recorded_in_revision.text if self.recorded_in_revision else None,
            "approvals": sorted(item.text for item in self.approval_refs),
            "issued_at_revision": self.issued_at_revision,
            "expires_after_revision": self.expires_after_revision,
            "lease_id": self.lease_id,
            "restores_override_id": self.restores_override_id,
            "invalidation": sorted(self.invalidation),
            "compiler_version": self.compiler_version,
        }

    def describes(self, rule_class: str, semantic_path: str) -> bool:
        return self.rule_class == require_identifier(rule_class, "rule_class") and covers_path(
            self.semantic_path, require_semantic_path(semantic_path, "semantic_path")
        )


OverrideReceipt.NESTED = {
    "target_refs": of(SemanticRef),
    "actor": of(IntentAuthorityRef),
    "graph_ref": of(AuthorityPolicyGraphRef),
    "permission": of(AuthorityDecision),
    "previous_state": of(SemanticStateSnapshot),
    "effective_state": of(SemanticStateSnapshot),
    "requested_scope": of(ConstraintScope),
    "effective_scope": of(ConstraintScope),
    "conflict_ref": of(SemanticRef),
    "recorded_in_revision": of(SemanticRef),
    "approval_refs": of(SemanticRef),
    "human_decision": of(SemanticRef),
}


def optional_bound_ref(value: Any, name: str, kind: RefKind) -> SemanticRef | None:
    if value is None:
        return None
    return require_bound_ref(value, name, kind=kind)


def optional_bound_refs(value: Any, name: str) -> tuple[SemanticRef, ...]:
    return bound_refs(value, name, minimum=0)


def _scope_widened(requested: ConstraintScope, granted: ConstraintScope) -> tuple[str, ...]:
    """Report how the granted scope reaches further than what was asked for.

    An override may be granted *less* than requested — that is the ordinary shape of a
    negotiated decision — but never more, and "never more" needs a definition rather than a
    review comment. Path coverage, channel, phase and destination sets are compared, and every
    exclusion the requester declared has to survive into the grant, because a dropped exclusion
    widens reach without changing a single inclusion.
    """

    if not isinstance(requested, ConstraintScope) or not isinstance(granted, ConstraintScope):
        raise SchemaValidationError("scope comparison expects two ConstraintScope records")
    violations: list[str] = []
    for path in granted.subject_paths:
        if not any(covers_path(prefix, path) for prefix in requested.subject_paths):
            violations.append(f"subject {path} is outside the requested scope")
    for excluded in requested.excluded_paths:
        if not any(covers_path(excluded, kept) for kept in granted.excluded_paths):
            violations.append(f"exclusion {excluded} was dropped")
    for name in ("modalities", "phases", "destinations"):
        asked = set(getattr(requested, name))
        given = set(getattr(granted, name))
        if asked and not given:
            violations.append(f"{name}: the grant removed a bound without naming a replacement")
        elif asked and asked != given and not given <= asked:
            violations.append(f"{name}: {sorted(given - asked)} were not requested")
    asked_facets, given_facets = set(requested.facets), set(granted.facets)
    if asked_facets and not given_facets <= asked_facets:
        violations.append(f"facets: {sorted(given_facets - asked_facets)} were not requested")
    return tuple(violations)


_ACTION_MOVEMENTS: Mapping[OverrideAction, frozenset[str]] = {
    OverrideAction.STRENGTHEN: frozenset({ChangeKind.STRENGTHENED.value}),
    OverrideAction.NARROW_SCOPE: frozenset({ChangeKind.RESCOPED.value}),
    OverrideAction.REPLACE: frozenset(
        {
            ChangeKind.REPREDICATED.value,
            ChangeKind.POLARITY_FLIPPED.value,
            ChangeKind.ADDED.value,
            ChangeKind.REMOVED.value,
        }
    ),
    OverrideAction.RELAX: frozenset({ChangeKind.RELAXED.value}),
    OverrideAction.DISABLE: frozenset({ChangeKind.REMOVED.value, ChangeKind.RELAXED.value}),
    OverrideAction.TEMPORARY_EXPERIMENT: frozenset(
        {ChangeKind.RELAXED.value, ChangeKind.REMOVED.value, ChangeKind.REPREDICATED.value}
    ),
    OverrideAction.RESTORE_PRIOR: frozenset(
        {
            ChangeKind.STRENGTHENED.value,
            ChangeKind.RELAXED.value,
            ChangeKind.RESCOPED.value,
            ChangeKind.REPREDICATED.value,
            ChangeKind.ADDED.value,
            ChangeKind.REMOVED.value,
        }
    ),
}


@dataclass(frozen=True)
class OverrideProposal(Record):
    """An agent's request that a conflict be decided one way (§24).

    The proposal carries everything a human needs in order to decide and nothing that would let
    it be decided: ``approved`` and ``carries_authority`` are constants, and the only way to a
    receipt is :func:`authorize_proposal`, which asks the policy graph about the *authorising*
    actor rather than the proposing one. That shape is the whole of "may propose, may not
    self-authorize" written down as types.
    """

    proposal_id: str
    action: str
    rule_class: str
    semantic_path: str
    target_refs: tuple[SemanticRef, ...] = ()
    proposed_by: IntentAuthorityRef | None = None
    conflict_ref: SemanticRef | None = None
    graph_ref: AuthorityPolicyGraphRef | None = None
    rationale: str = ""
    previous_state: SemanticStateSnapshot | None = None
    requested_scope: ConstraintScope | None = None
    invalidation: tuple[str, ...] = ()
    requires_human: bool = True
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)
    contract_version: str = ""

    approved = False
    carries_authority = False
    effective = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "proposal_id", require_identifier(self.proposal_id, "proposal_id"))
        action = OverrideAction.parse(self.action, "action")
        object.__setattr__(self, "action", action.value)
        object.__setattr__(self, "rule_class", require_identifier(self.rule_class, "rule_class"))
        object.__setattr__(self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path"))
        object.__setattr__(self, "target_refs", bound_refs(self.target_refs, "target_refs"))
        if self.proposed_by is None:
            raise AuthorityError(
                f"proposal {self.proposal_id} has no author; an unattributed suggestion cannot be "
                "traced back to whoever should be asked about it"
            )
        object.__setattr__(self, "proposed_by", IntentAuthorityRef.coerce(self.proposed_by, "proposed_by"))
        object.__setattr__(self, "conflict_ref", optional_bound_ref(self.conflict_ref, "conflict_ref", RefKind.CONFLICT))
        if self.graph_ref is not None:
            object.__setattr__(self, "graph_ref", AuthorityPolicyGraphRef.coerce(self.graph_ref, "graph_ref"))
        object.__setattr__(self, "rationale", require_text(self.rationale, "rationale", maximum=MAX_RATIONALE_CHARS))
        if self.previous_state is not None:
            object.__setattr__(
                self, "previous_state", SemanticStateSnapshot.coerce(self.previous_state, "previous_state")
            )
        if self.requested_scope is not None:
            object.__setattr__(self, "requested_scope", ConstraintScope.coerce(self.requested_scope, "requested_scope"))
        object.__setattr__(self, "invalidation", invalidation_targets(self.invalidation, "invalidation"))
        if not isinstance(self.requires_human, bool):
            raise SchemaValidationError("requires_human must be a boolean")
        if self.requires_human is False and self.proposed_by.level.self_asserting_is_enough is False:
            raise AuthorityError(
                f"proposal {self.proposal_id} marks itself human-free while authored by a "
                f"{self.proposed_by.level.value} actor; only a governed source may decide that a "
                "human is unnecessary (§24)"
            )
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=2048))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def action_enum(self) -> OverrideAction:
        return OverrideAction.parse(self.action)

    @property
    def proposal_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.RESOLUTION.value, ref_id=self.proposal_id).with_digest(
            content_digest(self.to_payload())
        )

    def preview(self, graph: AuthorityPolicyGraph) -> AuthorityDecision:
        """What would happen if this exact proposal were honoured.

        Evaluated against the proposal's author, which is the honest reading of "can an agent do
        this itself": the answer is nearly always no, and the record of asking is worth keeping.
        """

        return graph.evaluate(
            actor=self.proposed_by,
            action=self.action,
            rule_class=self.rule_class,
            semantic_path=self.semantic_path,
        )


OverrideProposal.NESTED = {
    "target_refs": of(SemanticRef),
    "proposed_by": of(IntentAuthorityRef),
    "conflict_ref": of(SemanticRef),
    "graph_ref": of(AuthorityPolicyGraphRef),
    "previous_state": of(SemanticStateSnapshot),
    "requested_scope": of(ConstraintScope),
}


@dataclass(frozen=True)
class TemporaryOverrideLease(Record):
    """The bounded life of an experiment (§11).

    Expiry is counted in admitted revisions rather than in wall-clock time, for the same reason
    the freshness model refuses timestamps: M03 has no trustworthy clock, and a lease that expires
    "in two weeks" is a lease that nobody can prove has ended. A revision ordinal is checkable by
    any reader with the history.
    """

    lease_id: str
    override_ids: tuple[str, ...] = ()
    receipt_refs: tuple[SemanticRef, ...] = ()
    scope_paths: tuple[str, ...] = ()
    expires_after_revision: int | None = None
    review_condition: str | None = None
    non_release_boundary: bool = True
    restoration_action: str = OverrideAction.RESTORE_PRIOR.value
    issued_at_revision: int | None = None
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)
    contract_version: str = ""

    #: §11: an expired lease is never renewed by being left in a cache.
    renews_automatically = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "lease_id", require_identifier(self.lease_id, "lease_id"))
        ids = tuple(sorted({require_identifier(item, "override_ids[]") for item in (self.override_ids or ())}))
        if not ids:
            raise SchemaValidationError(
                f"lease {self.lease_id} covers no override, so it expires nothing and protects nothing"
            )
        if len(ids) > MAX_OVERRIDES:
            raise LimitExceededError(f"override_ids exceeds {MAX_OVERRIDES} entries")
        object.__setattr__(self, "override_ids", ids)
        object.__setattr__(self, "scope_paths", bound_paths(self.scope_paths, "scope_paths"))
        if self.expires_after_revision is None:
            raise OverrideRefusedError(
                f"lease {self.lease_id} has no expiry; §11 allows a temporary override to end, and an "
                "experiment with no end is a relaxation that has not been admitted"
            )
        object.__setattr__(
            self, "expires_after_revision", require_revision_ordinal(self.expires_after_revision, "expires_after_revision")
        )
        if self.issued_at_revision is not None:
            object.__setattr__(self, "issued_at_revision", require_revision_ordinal(self.issued_at_revision, "issued_at_revision"))
            if self.expires_after_revision < self.issued_at_revision:
                raise SchemaValidationError(
                    f"lease {self.lease_id} expires at revision {self.expires_after_revision}, before "
                    f"it was issued at {self.issued_at_revision}"
                )
        refs = bound_refs(self.receipt_refs, "receipt_refs", kind=RefKind.RECEIPT, minimum=0)
        for receipt in refs:
            if receipt.ref_id not in ids:
                raise RefError(
                    f"lease {self.lease_id} binds receipt {receipt.ref_id}, which it does not cover"
                )
        object.__setattr__(self, "receipt_refs", refs)
        if self.review_condition is not None:
            object.__setattr__(self, "review_condition", require_text(self.review_condition, "review_condition", maximum=512))
        if not isinstance(self.non_release_boundary, bool):
            raise SchemaValidationError("non_release_boundary must be a boolean")
        object.__setattr__(
            self, "restoration_action", OverrideAction.parse(self.restoration_action, "restoration_action").value
        )
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=2048))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def covers_everything(self) -> bool:
        return not self.scope_paths

    def covers(self, semantic_path: str) -> bool:
        path = require_semantic_path(semantic_path, "semantic_path")
        return self.covers_everything or any(covers_path(prefix, path) for prefix in self.scope_paths)

    def live_at(self, revision_ordinal: int) -> bool:
        return not self.expired_at(revision_ordinal)

    def expired_at(self, revision_ordinal: int) -> bool:
        ordinal = require_revision_ordinal(revision_ordinal, "revision_ordinal")
        return ordinal > self.expires_after_revision

    def require_live(self, revision_ordinal: int, action: str) -> "TemporaryOverrideLease":
        if self.expired_at(revision_ordinal):
            raise StaleSemanticError(
                f"{action} relied on lease {self.lease_id}, which ended at revision "
                f"{self.expires_after_revision} and is being read at {revision_ordinal}; the "
                "restoration it promised is now a finding, not a future event (§11)"
            )
        return self

    def require_not_released(self, action: str) -> None:
        """Enforce the non-release boundary §11 asks for.

        Checked against the flag rather than the action name, so a policy that decides an
        experiment may ship still has to say so explicitly instead of inheriting a default.
        """

        if self.non_release_boundary:
            raise OverrideRefusedError(
                f"{action} cannot proceed while lease {self.lease_id} is open: temporary experiments "
                "carry a non-release boundary, and releasing one would make the expiry meaningless"
            )

    @property
    def lease_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.LEASE.value, ref_id=self.lease_id).with_digest(self.digest())

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "override_ids": sorted(self.override_ids),
            "scope_paths": sorted(self.scope_paths),
            "expires_after_revision": self.expires_after_revision,
            "non_release_boundary": self.non_release_boundary,
            "restoration_action": self.restoration_action,
        }


TemporaryOverrideLease.NESTED = {"receipt_refs": of(SemanticRef)}


@dataclass(frozen=True)
class OverrideDebt(Record):
    """Open semantic/governance cost created by an override (§12).

    The confusion this record is built to prevent is a real one: "we accepted something imperfect
    for now" is what both M01 ``QualityDebt`` and M03 ``OverrideDebt`` sound like. They are not
    the same thing — M01's ledger accepts a *defect in the artifact*, this one tracks an
    *obligation that is not being enforced* — and the two fields below make the difference
    structural instead of aspirational.
    """

    debt_id: str
    kind: str
    override_refs: tuple[SemanticRef, ...] = ()
    opened_at_revision: int | None = None
    expires_after_revision: int | None = None
    review_condition: str | None = None
    blocks_release: bool = True
    affected_paths: tuple[str, ...] = ()
    lease_id: str | None = None
    closed_by: SemanticRef | None = None
    closure_reason: str | None = None
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)
    contract_version: str = ""

    #: §12 keeps these ledgers apart; M01 owns defect acceptance.
    is_quality_debt = False
    owner_module = "M03"

    def __post_init__(self) -> None:
        object.__setattr__(self, "debt_id", require_identifier(self.debt_id, "debt_id"))
        kind = OverrideDebtKind.parse(self.kind, "kind")
        object.__setattr__(self, "kind", kind.value)
        refs = bound_refs(self.override_refs, "override_refs")
        borrowed = sorted(item.text for item in refs if item.kind.startswith("M01_"))
        if borrowed:
            raise QualityAuthorityError(
                f"debt {self.debt_id} cites M01-owned refs {borrowed}; an override receipt is M03 "
                "state and a quality decision is M01 state, and one ledger may not absorb the other"
            )
        not_receipts = sorted(item.text for item in refs if item.kind != RefKind.RECEIPT.value)
        if not_receipts:
            raise RefError(
                f"debt {self.debt_id} is owed against {not_receipts}, which are not override receipts; "
                "debt has to name the decision that created it, or it is a wish with an id"
            )
        object.__setattr__(self, "override_refs", refs)
        if self.opened_at_revision is not None:
            object.__setattr__(self, "opened_at_revision", require_revision_ordinal(self.opened_at_revision, "opened_at_revision"))
        if self.expires_after_revision is not None:
            object.__setattr__(
                self, "expires_after_revision", require_revision_ordinal(self.expires_after_revision, "expires_after_revision")
            )
            if self.opened_at_revision is not None and self.expires_after_revision < self.opened_at_revision:
                raise SchemaValidationError(f"debt {self.debt_id} expires before it opened")
        if self.opened_at_revision is None and self.expires_after_revision is None and self.review_condition is None:
            raise SchemaValidationError(
                f"debt {self.debt_id} has no revision, expiry or review condition; open-ended "
                "governance debt is how an exception becomes the rule"
            )
        if self.review_condition is not None:
            object.__setattr__(self, "review_condition", require_text(self.review_condition, "review_condition", maximum=512))
        if not isinstance(self.blocks_release, bool):
            raise SchemaValidationError("blocks_release must be a boolean")
        object.__setattr__(self, "affected_paths", bound_paths(self.affected_paths, "affected_paths"))
        if self.lease_id is not None:
            object.__setattr__(self, "lease_id", require_identifier(self.lease_id, "lease_id"))
        if self.closed_by is not None:
            object.__setattr__(
                self, "closed_by", require_bound_ref(self.closed_by, "closed_by", kind=RefKind.REVISION)
            )
            if self.closure_reason is None:
                raise SchemaValidationError(
                    f"debt {self.debt_id} was closed without a reason; an unexplained closure is the "
                    "same hole as an unrecorded override"
                )
        if self.closure_reason is not None:
            object.__setattr__(self, "closure_reason", require_text(self.closure_reason, "closure_reason", maximum=MAX_RATIONALE_CHARS))
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=2048))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def kind_enum(self) -> OverrideDebtKind:
        return OverrideDebtKind.parse(self.kind)

    @property
    def is_open(self) -> bool:
        return self.closed_by is None

    @property
    def debt_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.DEBT.value, ref_id=self.debt_id).with_digest(self.digest())

    @property
    def blocks_release_now(self) -> bool:
        return self.is_open and self.blocks_release

    def close(self, *, closed_by: SemanticRef, reason: str) -> "OverrideDebt":
        """Return the closed version of this debt, leaving this one untouched.

        Closing produces a new record rather than mutating, so a release that was blocked by debt
        ``d1`` can still be shown to have been blocked by it after the debt went away.
        """

        from dataclasses import replace as _replace

        return _replace(self, closed_by=require_bound_ref(closed_by, "closed_by", kind=RefKind.REVISION), closure_reason=reason)

    def as_m01_quality_debt(self) -> None:
        """The one method here that always refuses (§12, invariant 34).

        Kept as a callable because the confusion it prevents is a *method call away*, and an
        explicit refusal that names the owner is better evidence than an absent API.
        """

        raise QualityAuthorityError(
            f"override debt {self.debt_id} cannot be carried into M01: it records an obligation that "
            "is not being enforced, not a defect that was accepted, and M01's quality-debt authority "
            "is not M03's to spend"
        )

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "debt_id": self.debt_id,
            "kind": self.kind,
            "overrides": sorted(item.text for item in self.override_refs),
            "blocks_release": self.blocks_release,
            "affected_paths": sorted(self.affected_paths),
            "expires_after_revision": self.expires_after_revision,
            "is_open": self.is_open,
        }


OverrideDebt.NESTED = {"override_refs": of(SemanticRef), "closed_by": of(SemanticRef)}


@dataclass(frozen=True)
class OverrideLedger(Record):
    """The append-only view of every override taken over one brief.

    Superseding a ledger means adding to it, never editing it: the receipts are what a later
    compilation consults to decide whether it is relying on a lapsed permission, and a ledger
    someone could rewrite would make that question unanswerable exactly when it matters.
    """

    ledger_id: str
    brief_ref: SemanticRef
    revision_ref: SemanticRef
    receipts: tuple[OverrideReceipt, ...] = ()
    leases: tuple[TemporaryOverrideLease, ...] = ()
    debts: tuple[OverrideDebt, ...] = ()
    supersedes_ledger_id: str | None = None
    recorded_at: str | None = None
    compiler_version: str = OVERRIDE_COMPILER_VERSION
    schema_version: str = SCHEMA_VERSION
    contract_version: str = ""
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    append_only = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "ledger_id", require_identifier(self.ledger_id, "ledger_id"))
        object.__setattr__(
            self, "brief_ref", require_bound_ref(self.brief_ref, "brief_ref", kind=RefKind.BRIEF)
        )
        object.__setattr__(
            self, "revision_ref", require_bound_ref(self.revision_ref, "revision_ref", kind=RefKind.REVISION)
        )
        receipts = _sorted_by(self.receipts, OverrideReceipt, "receipts", MAX_OVERRIDES, "override_id")
        object.__setattr__(self, "receipts", receipts)
        leases = _sorted_by(self.leases, TemporaryOverrideLease, "leases", MAX_OVERRIDES, "lease_id")
        object.__setattr__(self, "leases", leases)
        debts = _sorted_by(self.debts, OverrideDebt, "debts", MAX_OVERRIDE_DEBT, "debt_id")
        object.__setattr__(self, "debts", debts)
        receipt_ids = {item.override_id for item in receipts}
        for receipt in receipts:
            if receipt.lease_id is not None and receipt.lease_id not in {item.lease_id for item in leases}:
                raise RefError(
                    f"override {receipt.override_id} names lease {receipt.lease_id}, which is not in "
                    f"ledger {self.ledger_id}; a lease that is not in the ledger cannot expire the "
                    "experiment it exists to bound"
                )
        for lease in leases:
            missing = sorted(set(lease.override_ids) - receipt_ids)
            if missing:
                raise RefError(
                    f"lease {lease.lease_id} covers overrides {missing} that this ledger does not hold"
                )
        for debt in debts:
            absent = sorted({item.ref_id for item in debt.override_refs} - receipt_ids)
            if absent:
                raise RefError(
                    f"debt {debt.debt_id} is owed against overrides {absent} outside ledger {self.ledger_id}"
                )
        if self.supersedes_ledger_id is not None:
            previous = require_identifier(self.supersedes_ledger_id, "supersedes_ledger_id")
            if previous == self.ledger_id:
                raise SchemaValidationError("a ledger cannot supersede itself")
            object.__setattr__(self, "supersedes_ledger_id", previous)
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=2048))
        if self.recorded_at is not None:
            object.__setattr__(self, "recorded_at", require_text(self.recorded_at, "recorded_at", maximum=64))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        object.__setattr__(self, "compiler_version", require_version_text(self.compiler_version, "compiler_version"))
        object.__setattr__(self, "schema_version", require_version_text(self.schema_version, "schema_version"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def override_ids(self) -> tuple[str, ...]:
        return tuple(item.override_id for item in self.receipts)

    @property
    def empty(self) -> bool:
        return not (self.receipts or self.leases or self.debts)

    def receipt(self, override_id: str) -> OverrideReceipt | None:
        """The receipt with this id, or :data:`None` when this ledger does not hold it."""

        wanted = require_identifier(override_id, "override_id")
        return next((item for item in self.receipts if item.override_id == wanted), None)

    def require_receipt(self, override_id: str) -> OverrideReceipt:
        """The same lookup for a caller whose work depends on the receipt existing."""

        return self.receipt(override_id) or _missing_receipt(override_id)

    def lease(self, lease_id: str) -> TemporaryOverrideLease | None:
        wanted = require_identifier(lease_id, "lease_id")
        return next((item for item in self.leases if item.lease_id == wanted), None)

    def open_debts(self) -> tuple[OverrideDebt, ...]:
        return tuple(item for item in self.debts if item.is_open)

    def release_blocking_debts(self) -> tuple[OverrideDebt, ...]:
        return tuple(item for item in self.debts if item.blocks_release_now)

    def expired_at(self, revision_ordinal: int) -> tuple[OverrideReceipt, ...]:
        ordinal = require_revision_ordinal(revision_ordinal, "revision_ordinal")
        return tuple(item for item in self.receipts if item.expired_at(ordinal))

    def live_at(self, revision_ordinal: int) -> tuple[OverrideReceipt, ...]:
        ordinal = require_revision_ordinal(revision_ordinal, "revision_ordinal")
        return tuple(item for item in self.receipts if not item.expired_at(ordinal))

    def for_path(self, semantic_path: str) -> tuple[OverrideReceipt, ...]:
        path = require_semantic_path(semantic_path, "semantic_path")
        return tuple(
            item
            for item in self.receipts
            if covers_path(item.semantic_path, path) or covers_path(path, item.semantic_path)
        )

    def relaxing_at(self, revision_ordinal: int) -> tuple[OverrideReceipt, ...]:
        """Live relaxations still in force — the list a release gate has to read (§11, §28).

        Computed from expiry bounds rather than cached, because the same ledger answers differently
        at different revisions and a stored list would freeze one revision's answer into all of
        them.
        """

        return tuple(
            item
            for item in self.live_at(revision_ordinal)
            if item.weakens and not item.action_enum.may_release
        )

    def require_no_expired_reliance(self, revision_ordinal: int, action: str) -> None:
        expired = self.expired_at(revision_ordinal)
        if expired:
            raise StaleSemanticError(
                f"{action} is reading ledger {self.ledger_id} at revision {revision_ordinal} while "
                f"overrides {sorted(item.override_id for item in expired)} have expired; the rules "
                "they relaxed are back in force (§11)"
            )

    def verify(self, graph: AuthorityPolicyGraph, *, revision_ordinal: int | None = None) -> tuple[str, ...]:
        """Re-check every receipt against a graph version, reporting the ones that moved.

        Returns ids rather than raising so a readiness pass can list all of them; the caller
        decides whether a stale permission is a finding or a blocker.
        """

        drift: list[str] = []
        for receipt in self.receipts:
            try:
                receipt.verify_against(graph, revision_ordinal=revision_ordinal)
            except (StaleSemanticError, AuthorityError):
                drift.append(receipt.override_id)
        return tuple(sorted(drift))

    def extend(
        self,
        *,
        receipt: OverrideReceipt | None = None,
        lease: TemporaryOverrideLease | None = None,
        debt: OverrideDebt | None = None,
        revision_ref: SemanticRef | None = None,
        ledger_id: str | None = None,
    ) -> "OverrideLedger":
        """Return a new ledger with one more entry, refusing to lose or replace any existing one.

        The successor needs its own identity: §8's receipts are immutable, so "supersede the
        ledger" cannot mean "re-issue the same id with different contents" — two records with one
        name and different bodies would make ``supersedes_ledger_id`` a pointer to an ambiguous
        history. The default id counts entries, which keeps it deterministic for a given path
        through the history.
        """

        from dataclasses import replace as _replace

        if receipt is None and lease is None and debt is None:
            raise SchemaValidationError(
                f"ledger {self.ledger_id} was extended with nothing; an empty supersession would add "
                "a version of the history that says the same thing as its parent, which is how an "
                "audit trail grows a branch nobody reads"
            )
        if receipt is not None and self.receipt(receipt.override_id) is not None:
            raise RefError(
                f"ledger {self.ledger_id} already holds override {receipt.override_id}; a receipt is "
                "immutable, so superseding it means issuing another one, not editing this"
            )
        if lease is not None and self.lease(lease.lease_id) is not None:
            raise RefError(f"ledger {self.ledger_id} already holds lease {lease.lease_id}")
        if debt is not None and any(item.debt_id == debt.debt_id for item in self.debts):
            raise RefError(
                f"ledger {self.ledger_id} already holds debt {debt.debt_id}; close it and open a new one"
            )
        size = len(self.receipts) + len(self.leases) + len(self.debts) + 1
        return _replace(
            self,
            ledger_id=ledger_id or f"{self.ledger_id}.{size}",
            receipts=self.receipts + ((receipt,) if receipt is not None else ()),
            leases=self.leases + ((lease,) if lease is not None else ()),
            debts=self.debts + ((debt,) if debt is not None else ()),
            revision_ref=revision_ref if revision_ref is not None else self.revision_ref,
            supersedes_ledger_id=self.ledger_id,
        )

    @property
    def ledger_ref(self) -> SemanticRef:
        return SemanticRef(kind=RefKind.RECEIPT.value, ref_id=self.ledger_id).with_digest(self.digest())

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "ledger_id": self.ledger_id,
            "brief_ref": self.brief_ref.text,
            "revision_ref": self.revision_ref.text,
            "receipts": [item.receipt_digest for item in self.receipts],
            "leases": [item.fingerprint_inputs() for item in self.leases],
            "debts": [item.fingerprint_inputs() for item in self.debts],
        }


OverrideLedger.NESTED = {
    "brief_ref": of(SemanticRef),
    "revision_ref": of(SemanticRef),
    "receipts": of(OverrideReceipt),
    "leases": of(TemporaryOverrideLease),
    "debts": of(OverrideDebt),
}


def _missing_receipt(override_id: str) -> OverrideReceipt:
    raise RefError(
        f"no override {override_id} in this ledger; naming a receipt that does not exist is how a "
        "decision gets justified by an approval nobody issued"
    )


def _sorted_by(value: Any, kind: type, name: str, limit: int, identity: str) -> tuple[Any, ...]:
    if value is None:
        value = ()
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Iterable):
        raise SchemaValidationError(f"{name} must be a list of {kind.__name__} records")
    items = [kind.coerce(item, f"{name}[]") for item in value]
    if len(items) > limit:
        raise LimitExceededError(f"{name} exceeds {limit} entries")
    keys = [getattr(item, identity) for item in items]
    duplicates = sorted({item for item in keys if keys.count(item) > 1})
    if duplicates:
        raise SchemaValidationError(f"{name} repeats {identity} {duplicates}")
    return tuple(sorted(items, key=lambda item: getattr(item, identity)))


def propose_override(
    *,
    proposal_id: str,
    action: Any,
    rule_class: str,
    semantic_path: str,
    target_refs: Iterable[SemanticRef],
    proposed_by: IntentAuthorityRef,
    rationale: str,
    graph: AuthorityPolicyGraph | None = None,
    conflict_ref: SemanticRef | None = None,
    previous_state: SemanticStateSnapshot | None = None,
    requested_scope: ConstraintScope | None = None,
    invalidation: Iterable[str] = (),
    metadata: Mapping[str, str] | None = None,
) -> OverrideProposal:
    """Record what an agent would like decided, with the graph's answer attached as evidence.

    The proposal never carries the permission: ``requires_human`` is set from the *evaluation*,
    which means an agent cannot file a proposal that looks pre-approved, and a human reading it
    sees immediately whether they are rubber-stamping or deciding.
    """

    wanted = OverrideAction.parse(action, "action")
    preview_decision = (
        graph.evaluate(
            actor=proposed_by,
            action=wanted,
            rule_class=rule_class,
            semantic_path=semantic_path,
        )
        if graph is not None
        else None
    )
    return OverrideProposal(
        proposal_id=proposal_id,
        action=wanted.value,
        rule_class=rule_class,
        semantic_path=semantic_path,
        target_refs=tuple(target_refs),
        proposed_by=proposed_by,
        conflict_ref=conflict_ref,
        graph_ref=graph.pin() if graph is not None else None,
        rationale=rationale,
        previous_state=previous_state,
        requested_scope=requested_scope,
        invalidation=tuple(invalidation),
        requires_human=not (preview_decision.may if preview_decision is not None else False),
        metadata=dict(metadata or {}),
    )


def issue_override(
    *,
    override_id: str,
    action: Any,
    rule_class: str,
    semantic_path: str,
    target_refs: Iterable[SemanticRef],
    actor: IntentAuthorityRef,
    graph: AuthorityPolicyGraph,
    reason: str,
    previous_state: SemanticStateSnapshot,
    effective_state: SemanticStateSnapshot | None = None,
    requested_scope: ConstraintScope | None = None,
    effective_scope: ConstraintScope | None = None,
    recorded_in_revision: SemanticRef,
    conflict_ref: SemanticRef | None = None,
    human_decision: SemanticRef | None = None,
    approval_refs: Iterable[SemanticRef] = (),
    expires_after_revision: int | None = None,
    lease_id: str | None = None,
    review_condition: str | None = None,
    issued_at_revision: int | None = None,
    restores_override_id: str | None = None,
    invalidation: Iterable[str] = (),
    notes: str | None = None,
    metadata: Mapping[str, str] | None = None,
) -> OverrideReceipt:
    """The single admission point for an effective override (§8, §10, §24).

    Every gate is applied here rather than inside :class:`OverrideReceipt`, because a receipt
    built by hand should be impossible to obtain by accident: the graph is consulted with the
    actor the caller presents, the graph version is pinned into the receipt, and the movement
    between the two states is checked against the action that was declared.
    """

    wanted = OverrideAction.parse(action, "action")
    graph.require_admitted(f"{wanted.value} of {rule_class}")
    permission = graph.authorize(
        actor=actor,
        action=wanted,
        rule_class=rule_class,
        semantic_path=semantic_path,
        human_decision=human_decision,
    )
    targets = bound_refs(target_refs, "target_refs")
    for target in targets:
        if target.kind == RefKind.POLICY.value and graph.reserves(
            require_identifier(target.ref_id, "target_refs[].ref_id")
        ):
            raise OverrideRefusedError(
                f"override {override_id} targets {target.text}, which is a reserved policy; the "
                "target list is exactly the place a bypass gets attempted (§6)"
            )
    return OverrideReceipt(
        override_id=override_id,
        action=wanted.value,
        rule_class=rule_class,
        semantic_path=semantic_path,
        target_refs=targets,
        actor=actor,
        graph_ref=graph.pin(),
        permission=permission,
        reason=reason,
        previous_state=previous_state,
        effective_state=effective_state,
        requested_scope=requested_scope,
        effective_scope=effective_scope,
        conflict_ref=conflict_ref,
        recorded_in_revision=recorded_in_revision,
        approval_refs=tuple(approval_refs),
        human_decision=human_decision,
        issued_at_revision=issued_at_revision,
        expires_after_revision=expires_after_revision,
        review_condition=review_condition,
        lease_id=lease_id,
        restores_override_id=restores_override_id,
        invalidation=tuple(invalidation),
        notes=notes,
        metadata=dict(metadata or {}),
    )


def authorize_proposal(
    proposal: OverrideProposal,
    *,
    actor: IntentAuthorityRef,
    graph: AuthorityPolicyGraph,
    recorded_in_revision: SemanticRef,
    effective_state: SemanticStateSnapshot | None = None,
    human_decision: SemanticRef | None = None,
    override_id: str | None = None,
    approval_refs: Iterable[SemanticRef] = (),
    expires_after_revision: int | None = None,
    lease_id: str | None = None,
    review_condition: str | None = None,
    issued_at_revision: int | None = None,
    invalidation: Iterable[str] = (),
    metadata: Mapping[str, str] | None = None,
) -> OverrideReceipt:
    """Turn a proposal into a receipt, deciding with the *authoriser's* authority.

    The proposal's author is deliberately absent from the decision. §24's sentence "agents may
    propose but cannot self-authorize" is otherwise easy to satisfy in appearance while
    reintroducing it through the back door — so nothing in this function reads authority from
    ``proposal.proposed_by``, and a proposal authored by an agent can only be honoured by someone
    the graph accepts.
    """

    if not isinstance(proposal, OverrideProposal):
        raise SchemaValidationError("authorize_proposal expects an OverrideProposal")
    if proposal.graph_ref is not None:
        proposal.graph_ref.require_current(graph, f"proposal {proposal.proposal_id}")
    if proposal.requires_human and human_decision is None:
        raise AuthorityError(
            f"proposal {proposal.proposal_id} needs an admitted human decision ref; the proposal "
            "cannot supply one, and neither can its author (§24)"
        )
    return issue_override(
        override_id=override_id or f"ovr.{proposal.proposal_id}",
        action=proposal.action,
        rule_class=proposal.rule_class,
        semantic_path=proposal.semantic_path,
        target_refs=proposal.target_refs,
        actor=actor,
        graph=graph,
        reason=proposal.rationale,
        previous_state=proposal.previous_state
        or SemanticStateSnapshot(
            snapshot_id=f"snap.{proposal.proposal_id}",
            semantic_path=proposal.semantic_path,
            subject_refs=proposal.target_refs,
        ),
        effective_state=effective_state,
        requested_scope=proposal.requested_scope,
        conflict_ref=proposal.conflict_ref,
        recorded_in_revision=recorded_in_revision,
        human_decision=human_decision,
        approval_refs=tuple(approval_refs),
        expires_after_revision=expires_after_revision,
        lease_id=lease_id,
        review_condition=review_condition,
        issued_at_revision=issued_at_revision,
        invalidation=tuple(invalidation) or proposal.invalidation,
        metadata=metadata,
    )
