"""F-M03-13 S05 authority policy graph.

M03 refuses to hard-code one priority order for every organisation (§5), so "who may weaken
what" is data. An ``AuthorityPolicyGraph`` names authority classes, the rule classes each one
speaks for, and the actions one class may perform against another, and every override in the
kernel is decided by looking that up rather than by comparing numbers.

Three refusals state what this module is not. It is not a score: authority levels and conflict
consequences are ordinal labels whose meaning comes from the doctrine behind them, and an
arithmetic mean over them would let a reviewer average a rights boundary into a preference. It
is not a confidence reader: §5.5 and D-M03-S05-002 keep authority and confidence independent,
and a 0.99 inference is still an inference about a claim nobody admitted. It is not
self-service: permission is granted by an admitted graph *version* before an actor holds it, so
an agent cannot obtain authority by describing itself as authoritative — the graph it consults
is the thing that was approved, and the receipt names that graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .admission import detect_cycle
from .base import Labeled, Record, of
from .errors import (
    AuthorityError,
    LimitExceededError,
    OverrideRefusedError,
    RefError,
    SchemaValidationError,
    StaleSemanticError,
)
from .identity import AuthorityLevel, RefKind, SemanticRef, require_bound_ref
from .limits import MAX_AUTHORITY_EDGES, MAX_AUTHORITY_NODES, MAX_CONFLICT_PARTIES
from .sources import bounded_metadata
from .versions import (
    CONTRACT_VERSION,
    SCHEMA_VERSION,
    content_digest,
    require_contract_version,
    require_digest,
    require_identifier,
    require_semantic_path,
    require_text,
    require_version_text,
)

__all__ = [
    "AUTHORITY_COMPILER_VERSION",
    "MANDATORY_RESERVED_KINDS",
    "AuthorityDecision",
    "AuthorityLevel",
    "AuthorityPolicyEdge",
    "AuthorityPolicyGraph",
    "AuthorityPolicyGraphRef",
    "AuthorityPolicyNode",
    "OverrideAction",
    "ReservedBoundary",
    "ReservedBoundaryKind",
    "default_reserved_boundaries",
    "is_reserved_rule_class",
]

AUTHORITY_COMPILER_VERSION = "m03-authority-policy-v1"


class OverrideAction(Labeled):
    """The governed move an authority class may make against someone else's rule (§9).

    The seven actions are deliberately not a free-text verb: "adjust", "update" and "amend"
    are the words a relaxation reaches for when nobody is looking, and the safety gradient in
    §10 only exists if RELAX is a different token from STRENGTHEN with a different gate.
    ``RESTORE_PRIOR`` is included as an action rather than treated as the absence of one,
    because §21 makes restoration a new governed act with its own receipt.
    """

    STRENGTHEN = "STRENGTHEN"
    NARROW_SCOPE = "NARROW_SCOPE"
    REPLACE = "REPLACE"
    RELAX = "RELAX"
    DISABLE = "DISABLE"
    TEMPORARY_EXPERIMENT = "TEMPORARY_EXPERIMENT"
    RESTORE_PRIOR = "RESTORE_PRIOR"

    @property
    def weakens(self) -> bool:
        """Whether the action can make the work less constrained than the rule requires.

        This is the single branch the whole safety gradient hangs on, so it is defined once
        here rather than re-derived at each call site — a call site that forgot
        ``TEMPORARY_EXPERIMENT`` would treat an expiring disable as harmless.
        """

        return self in {
            OverrideAction.RELAX,
            OverrideAction.DISABLE,
            OverrideAction.TEMPORARY_EXPERIMENT,
        }

    @property
    def requires_lease(self) -> bool:
        return self is OverrideAction.TEMPORARY_EXPERIMENT

    @property
    def minimum_actor_authority(self) -> AuthorityLevel:
        """The floor no admitted graph may lower (§10).

        A policy graph decides *which* class holds an action; this decides how little an actor
        may hold and still be trusted with it. Without the floor, a mis-edited graph could
        grant DISABLE to a project record and the kernel would honour it, which is the opposite
        of what "policy-defined, not hard-coded" is meant to buy.
        """

        return _ACTION_FLOORS[self]

    @property
    def may_release(self) -> bool:
        """Whether an effective override with this action may sit under a released production.

        Temporary experiments are first-class precisely because they are not permanent (§11),
        and the honest version of that promise is a boundary: the lease that expires is the
        thing that must not be what a release rests on.
        """

        return self is not OverrideAction.TEMPORARY_EXPERIMENT


_ACTION_FLOORS: Mapping[OverrideAction, AuthorityLevel] = {
    OverrideAction.STRENGTHEN: AuthorityLevel.PROJECT_RECORD,
    OverrideAction.NARROW_SCOPE: AuthorityLevel.PROJECT_RECORD,
    OverrideAction.REPLACE: AuthorityLevel.TEAM_ASSERTED,
    OverrideAction.RESTORE_PRIOR: AuthorityLevel.TEAM_ASSERTED,
    OverrideAction.TEMPORARY_EXPERIMENT: AuthorityLevel.GOVERNED_POLICY,
    OverrideAction.RELAX: AuthorityLevel.GOVERNED_POLICY,
    OverrideAction.DISABLE: AuthorityLevel.HUMAN_OWNER,
}


class ReservedBoundaryKind(Labeled):
    """The families §6 places outside ordinary M03 override authority.

    ``RIGHTS_SECURITY`` and ``PLATFORM_LEGAL`` name what their owning modules mark
    non-overridable; M03 does not decide that, it records the decision it was handed and
    refuses to route around it.
    """

    M01_FATAL_GATE = "M01_FATAL_GATE"
    M01_EVALUATOR_AUTHORITY = "M01_EVALUATOR_AUTHORITY"
    M02_IMMUTABLE_HISTORY = "M02_IMMUTABLE_HISTORY"
    PROJECT_GOVERNANCE = "PROJECT_GOVERNANCE"
    RIGHTS_SECURITY = "RIGHTS_SECURITY"
    PLATFORM_LEGAL = "PLATFORM_LEGAL"

    @property
    def owner(self) -> str:
        """Which module owns the boundary, as a label the refusal can name.

        The refusal has to say who to ask, or it reads as M03 being unhelpful about a rule
        M03 invented.
        """

        return _BOUNDARY_OWNERS[self]

    @property
    def permanent(self) -> bool:
        """No lease, no expiry and no creative intent reaches these (§6)."""

        return True


_BOUNDARY_OWNERS: Mapping[ReservedBoundaryKind, str] = {
    ReservedBoundaryKind.M01_FATAL_GATE: "M01 quality kernel",
    ReservedBoundaryKind.M01_EVALUATOR_AUTHORITY: "M01 evaluator registry",
    ReservedBoundaryKind.M02_IMMUTABLE_HISTORY: "M02 project OS",
    ReservedBoundaryKind.PROJECT_GOVERNANCE: "repository governance",
    ReservedBoundaryKind.RIGHTS_SECURITY: "M53/M54 rights and security policy",
    ReservedBoundaryKind.PLATFORM_LEGAL: "platform legal policy",
}

#: The boundaries every admitted graph must carry. Dropping one from a policy document is the
#: cheapest way to make M03 complicit in a bypass, so presence is checked, not assumed.
MANDATORY_RESERVED_KINDS: frozenset[ReservedBoundaryKind] = frozenset(ReservedBoundaryKind)

#: Canonical rule classes per boundary. Callers may add more; these six always exist, because a
#: graph that "forgot" to declare the fatal gate would otherwise have nothing to refuse with.
_RESERVED_DEFAULT_RULE_CLASSES: Mapping[ReservedBoundaryKind, tuple[str, ...]] = {
    ReservedBoundaryKind.M01_FATAL_GATE: ("m01.fatal-gate",),
    ReservedBoundaryKind.M01_EVALUATOR_AUTHORITY: ("m01.evaluator-authority",),
    ReservedBoundaryKind.M02_IMMUTABLE_HISTORY: ("m02.immutable-history",),
    ReservedBoundaryKind.PROJECT_GOVERNANCE: ("governance.work-order",),
    ReservedBoundaryKind.RIGHTS_SECURITY: ("rights.security",),
    ReservedBoundaryKind.PLATFORM_LEGAL: ("platform.legal",),
}


def _rule_classes(value: Any, name: str, *, limit: int) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise SchemaValidationError(f"{name} must be a list of rule class labels")
    items = tuple(sorted({require_identifier(item, f"{name}[]") for item in value}))
    if len(items) > limit:
        raise LimitExceededError(f"{name} exceeds {limit} entries")
    return items


def _paths(value: Any, name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Iterable):
        raise SchemaValidationError(f"{name} must be a list of semantic paths")
    return tuple(sorted({require_semantic_path(item, f"{name}[]") for item in value}))


@dataclass(frozen=True)
class AuthorityPolicyNode(Record):
    """One authority class, and the rule classes it answers for.

    There is exactly one node per authority level in an admitted graph — the levels in
    :class:`~iris_intent.identity.AuthorityLevel` *are* M03's authority classes, since they are
    what every statement and constraint already carries — and the node adds the two things a
    level cannot say: which rule classes stand behind it, and how far its reach extends. That
    pairing is what makes both halves of a permission question total: "which class is this actor
    in" reads off the level, and "who owns this rule" reads off the ownership list.
    """

    node_id: str
    authority_level: str
    rule_classes: tuple[str, ...] = ()
    scope_paths: tuple[str, ...] = ()
    human_only: bool = False
    rationale: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    #: Structural answer to §6: a node is a speaking position, never a grant of new authority.
    grants_authority = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        level = AuthorityLevel.parse(self.authority_level, "authority_level")
        object.__setattr__(self, "authority_level", level.value)
        rule_classes = _rule_classes(self.rule_classes, "rule_classes", limit=MAX_CONFLICT_PARTIES * 4)
        if not rule_classes:
            raise SchemaValidationError(
                f"node {self.node_id} owns no rule class; a class that stands behind nothing is a "
                "title, and titles have historically been used to claim authority"
            )
        object.__setattr__(self, "rule_classes", rule_classes)
        object.__setattr__(self, "scope_paths", _paths(self.scope_paths, "scope_paths"))
        if not isinstance(self.human_only, bool):
            raise SchemaValidationError("human_only must be a boolean")
        if self.human_only and not level.self_asserting_is_enough:
            raise AuthorityError(
                f"node {self.node_id} demands a human decision but holds {level.value} authority; "
                "a human-only gate sitting below a governed level is a checkbox, not a gate"
            )
        if self.rationale is not None:
            object.__setattr__(self, "rationale", require_text(self.rationale, "rationale", maximum=2048))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))

    @property
    def level(self) -> AuthorityLevel:
        return AuthorityLevel.parse(self.authority_level)

    @property
    def universal(self) -> bool:
        """Whether the node covers any path, i.e. whether it is a project-wide class."""

        return not self.scope_paths

    def owns(self, rule_class: str, semantic_path: str | None = None) -> bool:
        """Whether this class stands behind a rule in a place.

        ``semantic_path=None`` asks only about the class, which is what a caller holding just a
        rule class can ask; the graph adds the path so that two classes owning one class in two
        disjoint scopes stay resolvable.
        """

        wanted = require_identifier(rule_class, "rule_class")
        if wanted not in self.rule_classes:
            return False
        if semantic_path is None or self.universal:
            return True
        path = require_semantic_path(semantic_path, "semantic_path")
        return any(path == prefix or path.startswith(prefix + ".") for prefix in self.scope_paths)

    def overlaps(self, other: "AuthorityPolicyNode") -> tuple[str, ...]:
        """Rule classes both nodes claim, when their scopes can name the same subject.

        Two nodes owning one class in disjoint scopes is a normal organisation; two owning it
        where their scopes touch is an unresolved dispute written into a policy document, and the
        graph refuses to carry a dispute into a query that will be read as an answer.
        """

        if not isinstance(other, AuthorityPolicyNode):
            raise SchemaValidationError("overlaps expects an AuthorityPolicyNode")
        shared = sorted(set(self.rule_classes) & set(other.rule_classes))
        if not shared:
            return ()
        if self.universal or other.universal:
            return tuple(shared)
        mine, theirs = set(self.scope_paths), set(other.scope_paths)
        touching = any(
            _touches(left, right) for left in sorted(mine) for right in sorted(theirs)
        )
        return tuple(shared) if touching else ()

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "authority_level": self.authority_level,
            "rule_classes": list(self.rule_classes),
            "scope_paths": list(self.scope_paths),
            "human_only": self.human_only,
        }


def _touches(left: str, right: str) -> bool:
    return left == right or left.startswith(right + ".") or right.startswith(left + ".")


AuthorityPolicyNode.NESTED = {}


@dataclass(frozen=True)
class AuthorityPolicyEdge(Record):
    """One permission: subject class may perform these actions against object class's rules.

    Actions are a set on one edge rather than one edge per action so that "brand policy may
    narrow or replace project rules" reads as a single governed decision, while still being
    checked action by action at the point of use.
    """

    edge_id: str
    subject_node_id: str
    object_node_id: str
    actions: tuple[str, ...] = ()
    scope_paths: tuple[str, ...] = ()
    rationale: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "edge_id", require_identifier(self.edge_id, "edge_id"))
        for name in ("subject_node_id", "object_node_id"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        if self.subject_node_id == self.object_node_id:
            raise AuthorityError(
                f"edge {self.edge_id} grants a node authority over itself; self-permission is how "
                "an actor stops needing a policy at all (§5)"
            )
        actions = tuple(sorted({OverrideAction.parse(item, "actions[]").value for item in (self.actions or ())}))
        if not actions:
            raise SchemaValidationError(
                f"edge {self.edge_id} permits no action, so it documents nothing and hides nothing"
            )
        object.__setattr__(self, "actions", actions)
        object.__setattr__(self, "scope_paths", _paths(self.scope_paths, "scope_paths"))
        if self.rationale is not None:
            object.__setattr__(self, "rationale", require_text(self.rationale, "rationale", maximum=2048))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))

    @property
    def action_enums(self) -> tuple[OverrideAction, ...]:
        return tuple(OverrideAction.parse(item) for item in self.actions)

    @property
    def weakest_floor(self) -> AuthorityLevel:
        """The least demanding actor level this edge could be used by.

        Computed rather than stored so a reviewer reading the graph sees the floor the edge
        actually implies; an edge that reaches DISABLE but names a project record as its
        subject is caught at construction, not at the moment someone relies on it.
        """

        levels = [action.minimum_actor_authority for action in self.action_enums]
        return min(levels, key=lambda item: item.rank)

    def covers(self, semantic_path: str | None) -> bool:
        if not self.scope_paths:
            return True
        if semantic_path is None:
            return True
        path = require_semantic_path(semantic_path, "semantic_path")
        return any(path == prefix or path.startswith(prefix + ".") for prefix in self.scope_paths)

    def permits(self, action: Any) -> bool:
        return OverrideAction.parse(action, "action").value in self.actions

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "subject_node_id": self.subject_node_id,
            "object_node_id": self.object_node_id,
            "actions": list(self.actions),
            "scope_paths": list(self.scope_paths),
        }


AuthorityPolicyEdge.NESTED = {}


@dataclass(frozen=True)
class ReservedBoundary(Record):
    """A rule class ordinary M03 overrides may not reach (§6).

    ``non_overridable`` is a constant rather than a field for the same reason a FATAL rung is
    not a suggestion: a boundary the policy document can tick off is a preference, and a brief
    cannot convert a forbidden system invariant into a creative preference. What the record
    *does* carry is which module owns it and the evidence that it was marked that way, because
    the refusal has to be actionable.
    """

    boundary_id: str
    kind: str
    rule_classes: tuple[str, ...] = ()
    evidence_refs: tuple[SemanticRef, ...] = ()
    notes: str | None = None

    non_overridable = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "boundary_id", require_identifier(self.boundary_id, "boundary_id"))
        kind = ReservedBoundaryKind.parse(self.kind, "kind")
        object.__setattr__(self, "kind", kind.value)
        rule_classes = _rule_classes(self.rule_classes, "rule_classes", limit=MAX_CONFLICT_PARTIES * 4)
        if not rule_classes:
            raise SchemaValidationError(
                f"boundary {self.boundary_id} reserves no rule class; an empty boundary looks strict "
                "and protects nothing"
            )
        object.__setattr__(self, "rule_classes", rule_classes)
        refs = tuple(
            sorted(
                (
                    require_bound_ref(item, "evidence_refs[]")
                    for item in (self.evidence_refs or ())
                ),
                key=lambda item: item.text,
            )
        )
        object.__setattr__(self, "evidence_refs", refs)
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=2048))

    @property
    def kind_enum(self) -> ReservedBoundaryKind:
        return ReservedBoundaryKind.parse(self.kind)

    @property
    def owner(self) -> str:
        return self.kind_enum.owner

    def reserves(self, rule_class: str) -> bool:
        return require_identifier(rule_class, "rule_class") in self.rule_classes

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "boundary_id": self.boundary_id,
            "kind": self.kind,
            "rule_classes": list(self.rule_classes),
            "evidence_refs": sorted(item.text for item in self.evidence_refs),
        }


ReservedBoundary.NESTED = {"evidence_refs": of(SemanticRef)}


def default_reserved_boundaries(
    *, evidence_refs: Iterable[SemanticRef] = (), rule_classes: Mapping[str, Iterable[str]] | None = None
) -> tuple[ReservedBoundary, ...]:
    """Build the six boundaries §6 requires, each with its canonical rule classes.

    Provided as a helper rather than a module constant because the evidence refs differ per
    project, and a boundary with nothing pointing at the policy that declared it is a claim.
    """

    refs = tuple(
        sorted(
            (require_bound_ref(item, "evidence_refs[]") for item in (evidence_refs or ())),
            key=lambda item: item.text,
        )
    )
    supplied = dict(rule_classes or {})
    built: list[ReservedBoundary] = []
    for kind in sorted(MANDATORY_RESERVED_KINDS, key=lambda item: item.value):
        extra = _rule_classes(supplied.get(kind.value, ()), "rule_classes[]", limit=MAX_CONFLICT_PARTIES * 4)
        built.append(
            ReservedBoundary(
                boundary_id=f"reserved.{kind.value.lower()}",
                kind=kind.value,
                rule_classes=tuple(sorted(set(_RESERVED_DEFAULT_RULE_CLASSES[kind]) | set(extra))),
                evidence_refs=refs,
            )
        )
    return tuple(built)


def is_reserved_rule_class(rule_class: str, boundaries: Iterable[Any] = ()) -> bool:
    """Whether a rule class sits behind a boundary, including the canonical six.

    The defaults are consulted even when a caller passes nothing, because "the graph I was
    handed forgot the fatal gate" must not become "the fatal gate is overridable".
    """

    wanted = require_identifier(rule_class, "rule_class")
    for item in boundaries:
        if item.reserves(wanted):
            return True
    return any(wanted in set(_RESERVED_DEFAULT_RULE_CLASSES[kind]) for kind in _RESERVED_DEFAULT_RULE_CLASSES)


@dataclass(frozen=True)
class AuthorityDecision(Record):
    """The graph's answer to one permission question, kept as data.

    Returned by :meth:`AuthorityPolicyGraph.evaluate`, which never raises and never resolves —
    an agent is allowed to ask whether it may do something, and the answer is a record it can
    put in a proposal. :meth:`AuthorityPolicyGraph.authorize` is the same computation with the
    refusal attached, and that pair is what keeps §24 honest: asking is free, acting is not.
    """

    action: str
    actor_level: str
    rule_class: str
    semantic_path: str
    may: bool
    requires_human: bool
    reason: str
    edge_id: str | None = None
    subject_node_id: str | None = None
    object_node_id: str | None = None
    reserved_by: str | None = None
    graph_version: str = ""
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "action", OverrideAction.parse(self.action, "action").value)
        object.__setattr__(self, "actor_level", AuthorityLevel.parse(self.actor_level, "actor_level").value)
        object.__setattr__(self, "rule_class", require_identifier(self.rule_class, "rule_class"))
        object.__setattr__(self, "semantic_path", require_semantic_path(self.semantic_path, "semantic_path"))
        for name in ("may", "requires_human"):
            if not isinstance(getattr(self, name), bool):
                raise SchemaValidationError(f"{name} must be a boolean")
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=2048))
        for name in ("edge_id", "subject_node_id", "object_node_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, require_identifier(value, name))
        if self.reserved_by is not None:
            object.__setattr__(self, "reserved_by", require_text(self.reserved_by, "reserved_by", maximum=128))
        if self.may and self.subject_node_id != self.object_node_id and self.edge_id is None:
            raise SchemaValidationError(
                "a permissive decision between two authority classes must name the edge it came "
                "from; an unlocated 'yes' is indistinguishable from one someone typed"
            )
        if self.may and self.requires_human:
            raise SchemaValidationError(
                "a decision that still needs a human is not permission; report it as denied and "
                "ask, otherwise a receipt could cite this record as the approval"
            )
        object.__setattr__(self, "graph_version", require_text(self.graph_version, "graph_version", maximum=64))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def action_enum(self) -> OverrideAction:
        return OverrideAction.parse(self.action)

    @property
    def decision_digest(self) -> str:
        return content_digest(self.fingerprint_inputs())

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "actor_level": self.actor_level,
            "rule_class": self.rule_class,
            "semantic_path": self.semantic_path,
            "may": self.may,
            "requires_human": self.requires_human,
            "edge_id": self.edge_id,
            "subject_node_id": self.subject_node_id,
            "object_node_id": self.object_node_id,
            "reserved_by": self.reserved_by,
            "graph_version": self.graph_version,
        }


def _actor_level(value: Any, name: str = "actor") -> AuthorityLevel:
    """Read the authority level behind whatever was offered as the actor.

    Statements, constraints and authority refs all carry one, and every one of them is a thing
    a caller legitimately has at hand. What is *not* accepted is a bare label: an actor that
    asserts its own level has to assert it through a record whose construction already refused
    the forgeries (§5.6).
    """

    if isinstance(value, AuthorityLevel):
        return value
    if isinstance(value, str):
        raise AuthorityError(
            f"{name} must be an authority-bearing record, not the string {value!r}; authority is "
            "read from what was admitted, never from what was claimed"
        )
    for candidate in (
        getattr(value, "authority_level", None),
        getattr(value, "authority", None),
        getattr(getattr(value, "authority", None), "level", None),
        getattr(value, "level", None),
    ):
        if isinstance(candidate, AuthorityLevel):
            return candidate
    raise SchemaValidationError(f"{name} carries no authority level: {type(value).__name__}")


@dataclass(frozen=True)
class AuthorityPolicyGraph(Record):
    """The versioned policy that decides overrides, in place of a scalar priority (§5).

    ``nodes`` and ``edges`` are the graph; ``reserved_boundaries`` is what sits outside it. The
    acyclicity check is not tidiness — permission that loops lets a low class authorise a high
    one transitively, and the whole point of the doctrine is that authority flows from an
    admitted source, not around a cycle.

    The graph carries no confidence, score or weight field of any kind, and its queries accept
    none, which is the structural form of "authority and confidence remain independent".
    """

    graph_id: str
    version: str
    nodes: tuple[AuthorityPolicyNode, ...] = ()
    edges: tuple[AuthorityPolicyEdge, ...] = ()
    reserved_boundaries: tuple[ReservedBoundary, ...] = ()
    admitted_by: SemanticRef | None = None
    policy_ref: SemanticRef | None = None
    compiler_version: str = AUTHORITY_COMPILER_VERSION
    schema_version: str = SCHEMA_VERSION
    contract_version: str = ""
    notes: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    #: §5.5 / D-M03-S05-002, stated as data so a consumer can assert it instead of trusting it.
    uses_confidence = False
    priority_is_scalar = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        object.__setattr__(self, "version", require_version_text(self.version, "version"))
        nodes = _ordered(self.nodes, AuthorityPolicyNode, "nodes", MAX_AUTHORITY_NODES, "node_id")
        edges = _ordered(self.edges, AuthorityPolicyEdge, "edges", MAX_AUTHORITY_EDGES, "edge_id")
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "edges", edges)
        boundaries = _ordered(
            self.reserved_boundaries, ReservedBoundary, "reserved_boundaries", MAX_CONFLICT_PARTIES * 4, "boundary_id"
        )
        declared = {item.kind_enum for item in boundaries}
        missing = sorted(MANDATORY_RESERVED_KINDS - declared, key=lambda item: item.value)
        if missing:
            raise AuthorityError(
                f"graph {self.graph_id} omits reserved boundaries {missing}; §6 places these outside "
                "ordinary override authority, so a policy that leaves them out has not relaxed them, "
                "it has failed to say anything about them"
            )
        object.__setattr__(self, "reserved_boundaries", boundaries)
        self._require_one_per_level(nodes)
        self._require_unique_ownership(nodes)
        self._require_nodes_resolve(nodes, edges)
        self._require_acyclic(nodes, edges)
        self._require_edge_floors(nodes, edges)
        self._require_boundaries_outside_edges(boundaries, nodes, edges)
        if self.admitted_by is not None:
            object.__setattr__(
                self,
                "admitted_by",
                require_bound_ref(self.admitted_by, "admitted_by", kind=RefKind.REVISION),
            )
        if self.policy_ref is not None:
            object.__setattr__(
                self, "policy_ref", require_bound_ref(self.policy_ref, "policy_ref", kind=RefKind.POLICY)
            )
        object.__setattr__(self, "compiler_version", require_version_text(self.compiler_version, "compiler_version"))
        object.__setattr__(self, "schema_version", require_version_text(self.schema_version, "schema_version"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )
        if self.notes is not None:
            object.__setattr__(self, "notes", require_text(self.notes, "notes", maximum=2048))
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))

    @staticmethod
    def _require_nodes_resolve(
        nodes: tuple[AuthorityPolicyNode, ...], edges: tuple[AuthorityPolicyEdge, ...]
    ) -> None:
        known = {item.node_id for item in nodes}
        unknown = sorted(
            {
                endpoint
                for edge in edges
                for endpoint in (edge.subject_node_id, edge.object_node_id)
                if endpoint not in known
            }
        )
        if unknown:
            raise RefError(
                f"edges reference undeclared authority nodes {unknown}; a dangling permission target "
                "reads as 'nobody may' to one reader and 'everybody may' to another"
            )

    @staticmethod
    def _require_acyclic(
        nodes: tuple[AuthorityPolicyNode, ...], edges: tuple[AuthorityPolicyEdge, ...]
    ) -> None:
        adjacency: dict[str, set[str]] = {item.node_id: set() for item in nodes}
        for edge in edges:
            adjacency[edge.subject_node_id].add(edge.object_node_id)
        cycle = detect_cycle({key: sorted(value) for key, value in adjacency.items()})
        if cycle:
            raise AuthorityError(
                f"authority graph is cyclic: {' -> '.join(cycle)}; permission that comes back around "
                "lets the weakest class authorise the strongest one (§5)"
            )

    @staticmethod
    def _require_one_per_level(nodes: tuple[AuthorityPolicyNode, ...]) -> None:
        """Keep each authority class a single speaking position.

        Actor lookup is by level, so two nodes at one level would make "which class is this
        person in" depend on node order — and the whole graph exists to remove order from
        authority decisions.
        """

        levels = [item.authority_level for item in nodes]
        duplicated = sorted({item for item in levels if levels.count(item) > 1})
        if duplicated:
            raise AuthorityError(
                f"graph declares more than one node for {duplicated}; an authority class with two "
                "seats has no answer about who holds it, only a race"
            )

    @staticmethod
    def _require_unique_ownership(nodes: tuple[AuthorityPolicyNode, ...]) -> None:
        """Refuse a policy where two classes own one rule in the same place.

        This is the check that lets :meth:`owner_node` stay total. Leaving it to query time would
        mean a graph that *looks* fine until the one dispute inside it is the reason something
        cannot be released.
        """

        for index, left in enumerate(nodes):
            for right in nodes[index + 1 :]:
                clash = left.overlaps(right)
                if clash:
                    raise AuthorityError(
                        f"authority nodes {left.node_id} and {right.node_id} both own {clash} within "
                        "overlapping scopes; M03 will not arbitrate that by scope specificity, "
                        "because specificity describes subjects and §5 describes permission"
                    )

    @staticmethod
    def _require_edge_floors(
        nodes: tuple[AuthorityPolicyNode, ...], edges: tuple[AuthorityPolicyEdge, ...]
    ) -> None:
        """Refuse an edge that hands an actor an action its own class is too weak for.

        The check is redundant at query time — :meth:`evaluate` applies the floor anyway — and
        that is exactly why it belongs here too. A graph carrying such an edge reads as a grant
        to whoever drafts it, and the person most likely to be misled is the one who later
        wonders why the grant is not working.
        """

        by_id = {item.node_id: item for item in nodes}
        for edge in edges:
            subject = by_id[edge.subject_node_id]
            below = sorted(
                action.value
                for action in edge.action_enums
                if subject.level.rank < action.minimum_actor_authority.rank
            )
            if below:
                raise AuthorityError(
                    f"edge {edge.edge_id} grants {below} to {subject.node_id}, which holds "
                    f"{subject.level.value}; §10 sets a floor per action, so this grant could never "
                    "be honoured and belongs in the policy that tried to make it"
                )

    def _require_boundaries_outside_edges(
        self,
        boundaries: tuple[ReservedBoundary, ...],
        nodes: tuple[AuthorityPolicyNode, ...],
        edges: tuple[AuthorityPolicyEdge, ...],
    ) -> None:
        """Refuse a graph that tries to route a reserved rule class through a permission edge.

        Checked at construction rather than at query time on purpose. A graph that *can* be
        written with "rights.security may be disabled by brand policy" in it is a graph someone
        will load, and the failure would then be silent for exactly as long as nobody asked.
        """

        by_id = {item.node_id: item for item in nodes}
        covered: dict[str, set[str]] = {}
        for boundary in boundaries:
            for rule_class in boundary.rule_classes:
                covered.setdefault(rule_class, set()).add(boundary.kind)
        for edge in edges:
            target = by_id[edge.object_node_id]
            weak = sorted(action.value for action in edge.action_enums if action.weakens)
            clash = sorted(rule_class for rule_class in target.rule_classes if rule_class in covered)
            if weak and clash:
                raise OverrideRefusedError(
                    f"edge {edge.edge_id} grants {weak} against rule classes {clash}, which are "
                    f"reserved by {sorted(covered[clash[0]])}; a weakening permission may not point at "
                    "a reserved class at all, because the boundary is defined by having no route to it"
                )
            if target.human_only and OverrideAction.DISABLE.value in edge.actions:
                raise OverrideRefusedError(
                    f"edge {edge.edge_id} lets {edge.subject_node_id} disable rules held by the "
                    f"human-only node {edge.object_node_id}; human-only means the decision is not "
                    "delegable, whatever the edge list says (§24)"
                )

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(item.node_id for item in self.nodes)

    @property
    def edge_ids(self) -> tuple[str, ...]:
        return tuple(item.edge_id for item in self.edges)

    @property
    def is_admitted(self) -> bool:
        return self.admitted_by is not None

    @property
    def reserved_rule_classes(self) -> tuple[str, ...]:
        return tuple(sorted({item for boundary in self.reserved_boundaries for item in boundary.rule_classes}))

    def node(self, node_id: str) -> AuthorityPolicyNode | None:
        wanted = require_identifier(node_id, "node_id")
        return next((item for item in self.nodes if item.node_id == wanted), None)

    def require_node(self, node_id: str) -> AuthorityPolicyNode:
        found = self.node(node_id)
        if found is None:
            raise RefError(f"graph {self.graph_id} has no authority node {node_id}")
        return found

    def owner_nodes(self, rule_class: str, semantic_path: str | None = None) -> tuple[AuthorityPolicyNode, ...]:
        """Every node claiming to stand behind one rule, ordered by id.

        Exposed as a plural because a caller building an explanation wants the candidates it just
        rejected, not an exception with a sentence inside it.
        """

        return tuple(item for item in self.nodes if item.owns(rule_class, semantic_path))

    def owner_node(self, rule_class: str, semantic_path: str | None = None) -> AuthorityPolicyNode:
        """The single node that stands behind a rule, refusing to guess when two do.

        "Most specific scope wins" is last-writer-wins wearing a different hat: it would let a
        narrow creative scope silently outrank a broad governed policy in exactly the case that
        matters, which is the one where they disagree.
        """

        found = self.owner_nodes(rule_class, semantic_path)
        if not found:
            raise AuthorityError(
                f"no authority class in graph {self.graph_id} owns {rule_class}"
                + (f" at {semantic_path}" if semantic_path else "")
                + "; nothing may be relaxed against a rule nobody stands behind"
            )
        if len(found) > 1:
            raise AuthorityError(
                f"authority for {rule_class}"
                + (f" at {semantic_path}" if semantic_path else "")
                + f" is ambiguous across nodes {sorted(item.node_id for item in found)}; M03 will not "
                "pick one by scope specificity (§7)"
            )
        return found[0]

    def actor_node(self, actor: Any) -> AuthorityPolicyNode:
        """The class an actor occupies, read off the authority level it actually holds.

        Matched on level rather than identity because M03 has no identity store: the level is the
        identity it is allowed to see, and two actors at one level must get one answer or the
        graph is a preference list with a diagram attached.
        """

        level = _actor_level(actor)
        found = sorted((item for item in self.nodes if item.level is level), key=lambda item: item.node_id)
        if not found:
            raise AuthorityError(
                f"graph {self.graph_id} has no {level.value} class; an actor outside the policy holds "
                "no permission, which is reported rather than defaulted"
            )
        return found[0]

    def edge_for(
        self, subject_node_id: str, object_node_id: str, action: Any, semantic_path: str | None = None
    ) -> AuthorityPolicyEdge | None:
        """The edge granting ``action`` between two nodes, or ``None``.

        Ambiguous duplicates collapse to the lowest edge id, which is stable across runs; two
        edges saying the same thing is a drafting problem, not a decision to be re-litigated per
        call.
        """

        wanted = OverrideAction.parse(action, "action")
        found = sorted(
            (
                item
                for item in self.edges
                if item.subject_node_id == subject_node_id
                and item.object_node_id == object_node_id
                and item.permits(wanted)
                and item.covers(semantic_path)
            ),
            key=lambda item: item.edge_id,
        )
        return found[0] if found else None

    def evaluate(
        self,
        *,
        actor: Any,
        action: Any,
        rule_class: str,
        semantic_path: str = "",
        human_decision: SemanticRef | None = None,
    ) -> AuthorityDecision:
        """Compute permission without granting anything.

        The order of checks is the doctrine: reserved before policy, because a boundary is not
        the top of the ladder; floor before edge, because an under-authorised actor must not
        succeed through an over-generous graph; and human-only last, so a denial that also needs
        a person reports both.
        """

        wanted = OverrideAction.parse(action, "action")
        level = _actor_level(actor)
        path = require_semantic_path(semantic_path, "semantic_path") if semantic_path else ""
        version = self.version
        denied = {
            "action": wanted.value,
            "actor_level": level.value,
            "rule_class": require_identifier(rule_class, "rule_class"),
            "semantic_path": path or "unscoped",
            "may": False,
            "graph_version": version,
        }
        if self.reserves(denied["rule_class"]):
            owner = self.boundary_for(denied["rule_class"])
            return AuthorityDecision(
                **denied,
                requires_human=True,
                reserved_by=owner.kind if owner else "reserved",
                reason=(
                    f"{denied['rule_class']} is reserved by "
                    f"{owner.kind_enum.owner if owner else 'a boundary'}; an M03 override cannot reach it (§6)"
                ),
            )
        if level.rank < wanted.minimum_actor_authority.rank:
            return AuthorityDecision(
                **denied,
                requires_human=wanted.weakens,
                reason=(
                    f"{wanted.value} needs at least {wanted.minimum_actor_authority.value} authority, "
                    f"the actor holds {level.value}; the gradient in §10 is not negotiable by policy"
                ),
            )
        try:
            subject = self.actor_node(level)
            target = self.owner_node(denied["rule_class"], path or None)
        except AuthorityError as error:
            return AuthorityDecision(**denied, requires_human=True, reason=str(error))
        if subject.node_id == target.node_id:
            # Amending what you own is not an override of somebody else's authority, so no edge
            # is required — but the floor, the boundary and the human gate above it all still are,
            # which is why this branch sits after them and not before.
            return self._decide(
                denied,
                subject,
                target,
                None,
                human_decision=human_decision,
                reason=(
                    f"{subject.node_id} holds the authority the rule class already stands behind, so "
                    f"{wanted.value} amends its own scope rather than overriding another class"
                ),
            )
        edge = self.edge_for(subject.node_id, target.node_id, wanted, path or None)
        if edge is None:
            return AuthorityDecision(
                **denied,
                requires_human=wanted.weakens,
                edge_id=None,
                subject_node_id=subject.node_id,
                object_node_id=target.node_id,
                reason=(
                    f"graph {self.graph_id}@{version} grants no {wanted.value} edge from "
                    f"{subject.node_id} to {target.node_id}; absence is denial, and no rule of "
                    "precedence fills the gap"
                ),
            )
        return self._decide(
            denied,
            subject,
            target,
            edge,
            human_decision=human_decision,
            reason=(
                f"edge {edge.edge_id} of graph {self.graph_id}@{version} grants {wanted.value} from "
                f"{subject.node_id} to {target.node_id}"
            ),
        )

    def _decide(
        self,
        denied: Mapping[str, Any],
        subject: AuthorityPolicyNode,
        target: AuthorityPolicyNode,
        edge: AuthorityPolicyEdge | None,
        *,
        human_decision: SemanticRef | None,
        reason: str,
    ) -> AuthorityDecision:
        """Apply the two gates no edge can speak for: the human gate and the confidence gate.

        They live here rather than inside the edge lookup because they are not about the graph. A
        graph can grant an action and still not be allowed to use it — that difference is the
        doctrine in §10 and §24, and encoding it as edge data would let a policy document delete it.
        """

        identity = {
            "subject_node_id": subject.node_id,
            "object_node_id": target.node_id,
            "edge_id": edge.edge_id if edge is not None else None,
        }
        base = {key: value for key, value in denied.items() if key not in {"may", "requires_human"}}
        if human_decision is None and (target.human_only or subject.human_only):
            return AuthorityDecision(
                **base,
                **identity,
                may=False,
                requires_human=True,
                reason=(
                    f"{target.node_id if target.human_only else subject.node_id} is a human-only class, "
                    "and no decision in this graph is effective for it without an admitted human "
                    "revision ref (§24)"
                ),
            )
        if human_decision is not None:
            require_bound_ref(human_decision, "human_decision", kind=RefKind.REVISION)
        level = AuthorityLevel.parse(base["actor_level"])
        action = OverrideAction.parse(base["action"])
        if not level.self_asserting_is_enough and action.weakens:
            return AuthorityDecision(
                **base,
                **identity,
                may=False,
                requires_human=True,
                reason=(
                    f"a {level.value} actor may not {action.value} a rule: inference may propose a "
                    "relaxation and cannot authorise one, whatever the policy grants (§5.5, §24)"
                ),
            )
        return AuthorityDecision(
            **base, **identity, may=True, requires_human=False, reason=reason
        )

    def authorize(
        self,
        *,
        actor: Any,
        action: Any,
        rule_class: str,
        semantic_path: str = "",
        human_decision: SemanticRef | None = None,
    ) -> AuthorityDecision:
        """The same computation as :meth:`evaluate`, refusing a decision it cannot stand on."""

        decision = self.evaluate(
            actor=actor,
            action=action,
            rule_class=rule_class,
            semantic_path=semantic_path,
            human_decision=human_decision,
        )
        if not decision.may:
            if decision.reserved_by is not None:
                raise OverrideRefusedError(f"{action} refused: {decision.reason}")
            raise AuthorityError(f"{action} refused: {decision.reason}")
        return decision

    def reserves(self, rule_class: str) -> bool:
        return any(item.reserves(rule_class) for item in self.reserved_boundaries) or is_reserved_rule_class(
            rule_class
        )

    def boundary_for(self, rule_class: str) -> ReservedBoundary | None:
        wanted = require_identifier(rule_class, "rule_class")
        for item in self.reserved_boundaries:
            if item.reserves(wanted):
                return item
        for kind, defaults in _RESERVED_DEFAULT_RULE_CLASSES.items():
            if wanted in defaults:
                return ReservedBoundary(
                    boundary_id=f"reserved.{kind.value.lower()}",
                    kind=kind.value,
                    rule_classes=defaults,
                )
        return None

    def authority_for(self, rule_class: str, semantic_path: str | None = None) -> AuthorityLevel:
        """Which level stands behind a rule — the question §7 says recency may not answer."""

        return self.owner_node(rule_class, semantic_path).level

    def actions_permitted(
        self, actor: Any, rule_class: str, semantic_path: str | None = None
    ) -> tuple[str, ...]:
        """Every action this actor may take against a rule, for the clarification message.

        Reporting the open actions is what turns a refusal into a route: "you may not relax the
        logo rule, but your class holds NARROW_SCOPE over it" is a decision someone can act on,
        where a bare denial is only a wall.
        """

        if self.reserves(rule_class):
            return ()
        try:
            subject = self.actor_node(actor)
            target = self.owner_node(rule_class, semantic_path)
        except AuthorityError:
            return ()
        actions: set[str] = set()
        if subject.node_id == target.node_id:
            actions.update(
                item.value
                for item in OverrideAction
                if subject.level.rank >= item.minimum_actor_authority.rank
            )
        for edge in self.edges:
            if edge.subject_node_id != subject.node_id or edge.object_node_id != target.node_id:
                continue
            if not edge.covers(semantic_path):
                continue
            for action in edge.action_enums:
                if subject.level.rank >= action.minimum_actor_authority.rank:
                    actions.add(action.value)
        if subject.human_only or target.human_only:
            actions = set()
        return tuple(sorted(actions))

    def ref(self) -> SemanticRef:
        return SemanticRef(
            kind=RefKind.POLICY.value, ref_id=self.graph_id, version=self.version
        ).with_digest(self.graph_digest)

    def pin(self) -> "AuthorityPolicyGraphRef":
        """A pinned pointer to this exact graph version, for receipts to carry."""

        return AuthorityPolicyGraphRef(
            pin_id=f"{self.graph_id}.{self.version}",
            graph_ref=self.ref(),
            graph_id=self.graph_id,
            version=self.version,
            graph_digest=self.graph_digest,
            compiler_version=self.compiler_version,
        )

    @property
    def graph_digest(self) -> str:
        """Digest of the decision-relevant graph, excluding prose.

        ``notes``, ``rationale`` and ``metadata`` describe why a permission exists and do not
        change which permissions do, so rewording a policy document must not invalidate the
        receipts that relied on it — the same reason semantic fingerprints drop wording (§11).
        """

        return content_digest(
            {
                "graph_id": self.graph_id,
                "version": self.version,
                "nodes": [item.fingerprint_inputs() for item in self.nodes],
                "edges": [item.fingerprint_inputs() for item in self.edges],
                "reserved_boundaries": [
                    item.fingerprint_inputs() for item in self.reserved_boundaries
                ],
                "compiler_version": self.compiler_version,
            }
        )

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {"graph_ref": self.ref().text, "graph_digest": self.graph_digest}

    def require_admitted(self, action: str) -> None:
        if not self.is_admitted:
            raise AuthorityError(
                f"{action} needs graph {self.graph_id}@{self.version} to be admitted by a revision; "
                "an unadmitted policy is a draft someone could be right about, not a grant"
            )


AuthorityPolicyGraph.NESTED = {
    "nodes": of(AuthorityPolicyNode),
    "edges": of(AuthorityPolicyEdge),
    "reserved_boundaries": of(ReservedBoundary),
    "admitted_by": of(SemanticRef),
    "policy_ref": of(SemanticRef),
}


@dataclass(frozen=True)
class AuthorityPolicyGraphRef(Record):
    """A receipt's handle on the exact policy version a decision used (§8).

    The graph itself lives in policy storage and evolves; a receipt that named only the graph id
    would be re-resolvable to a different answer next month, which is how an override outlives
    the permission that justified it. Both a version and a digest are carried because they fail
    differently: a version bump says the policy moved, a digest mismatch says somebody's pointer
    is lying.
    """

    pin_id: str
    graph_ref: SemanticRef
    graph_id: str
    version: str
    graph_digest: str
    compiler_version: str = AUTHORITY_COMPILER_VERSION
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "pin_id", require_identifier(self.pin_id, "pin_id"))
        object.__setattr__(
            self, "graph_ref", require_bound_ref(self.graph_ref, "graph_ref", kind=RefKind.POLICY)
        )
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        object.__setattr__(self, "version", require_version_text(self.version, "version"))
        object.__setattr__(self, "graph_digest", require_digest(self.graph_digest, "graph_digest"))
        object.__setattr__(self, "compiler_version", require_version_text(self.compiler_version, "compiler_version"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )
        if self.graph_ref.ref_id != self.graph_id:
            raise RefError(
                f"pin {self.pin_id} names graph {self.graph_id} but points at {self.graph_ref.ref_id}"
            )
        if self.graph_ref.version != self.version:
            raise RefError(
                f"pin {self.pin_id} claims version {self.version} while its ref carries "
                f"{self.graph_ref.version}; the mismatch is the whole point of pinning"
            )
        if self.graph_ref.content_digest != self.graph_digest:
            raise RefError(
                f"pin {self.pin_id} carries two different digests for graph {self.graph_id}"
            )

    def describes(self, graph: AuthorityPolicyGraph) -> bool:
        if not isinstance(graph, AuthorityPolicyGraph):
            raise SchemaValidationError("describes expects an AuthorityPolicyGraph")
        return (
            graph.graph_id == self.graph_id
            and graph.version == self.version
            and graph.graph_digest == self.graph_digest
        )

    def require_current(self, graph: AuthorityPolicyGraph, action: str) -> AuthorityPolicyGraph:
        """Return the graph only while it is still the graph this pin was issued against.

        A stale pin is a ``StaleSemanticError`` rather than an authority failure: the actor may
        well still be allowed, and pretending otherwise would send a reviewer looking for an
        approval problem when the real problem is a cached pointer.
        """

        if not isinstance(graph, AuthorityPolicyGraph):
            raise SchemaValidationError("require_current expects an AuthorityPolicyGraph")
        if graph.graph_id != self.graph_id:
            raise RefError(
                f"{action} resolved graph {graph.graph_id} against a pin for {self.graph_id}"
            )
        if graph.version != self.version or graph.graph_digest != self.graph_digest:
            raise StaleSemanticError(
                f"{action} relied on {self.graph_id}@{self.version} ({self.graph_digest[:16]}), which "
                f"is now {graph.version} ({graph.graph_digest[:16]}); the override stays as recorded "
                "and the decision that used it must be re-run (§11)"
            )
        return graph


AuthorityPolicyGraphRef.NESTED = {"graph_ref": of(SemanticRef)}


def _ordered(value: Any, kind: type, name: str, limit: int, identity: str) -> tuple[Any, ...]:
    """Coerce, bound and sort one collection by its identity field.

    Sorting by id is what makes the graph's digests stable across Python runs and JSON
    round-trips: an authority graph whose digest moved because a list was rebuilt in a different
    order would invalidate every receipt that cited it.
    """

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
        raise SchemaValidationError(
            f"{name} repeats {identity} {duplicates}; a duplicated id makes which definition wins "
            "a matter of iteration order"
        )
    return tuple(sorted(items, key=lambda item: getattr(item, identity)))
