"""The §16 explanation graph, its §18 projections and its §19 cache key.

Three structural choices hold this module together, and each one is a refusal of something easier.

The first is that an explanation here is a *graph over admitted refs*, not a log of sentences.
A prose rationale can be rewritten until it justifies whatever was compiled; a path from an
``INTENT_OPERATION`` node to the bound ``STATEMENT`` ref that grounds it can only be read the one
way. So every node either *is* an admitted ref (a root, pinned by content digest) or points at the
canonical record it stands for (an emitted node, pinned by the digest of that record's own
fingerprint inputs), and every edge runs from the thing that needs explaining to the thing that
explains it. §16's demand that each emitted operation and capability have "an explanation path to
admitted source semantics or policy" is then a reachability property a reviewer can re-check, which
is why ``IntentExplanationGraph`` refuses to construct without it rather than warning about it.

The second is that the §18 levels are *projections of one graph*, not four explanations. A compact
trace and an audit packet that disagreed would mean the cheap answer was the one callers act on and
the expensive one was for the regulator, so ``ExplanationProjection`` carries
``canonical_facts`` — every emitted node and the set of root refs reachable from it — at *every*
level, including ``TRACE_ID_ONLY``, and validates them against the graph it was projected from.
Levels differ only in how much prose and provenance they render around those facts, and each level
declares which fields it is allowed to fill, so a trace-only packet cannot smuggle a narrative in
the field nobody was reading.

The third is what the §19 cache key leaves out. Wording is the interesting case: §19 wants a
revised brief that changed no semantics to reuse its machine traces while keeping the new revision's
lineage, so the key is built from semantic digests and versions alone, and the exclusion is
recorded as an enumerated field rather than an absence. That is also why the key is a record and not
a string — an invalidation rule nobody can inspect is a rule nobody can debug.

Like the rest of M03's kernel, nothing here dispatches, prices or schedules anything, and nothing
here lets a provider's account of its own translation become a fact about the brief (§23).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from .admission import detect_cycle
from .base import Labeled, Record, of
from .errors import (
    ExplanationError,
    LimitExceededError,
    SchemaValidationError,
    StaleSemanticError,
)
from .execution import (
    ExecutionIntentBundle,
    ProviderTranslationReceipt,
    canonical_execution_digest,
    find_provider_vocabulary,
)
from .identity import RefKind, SemanticRef, require_bound_ref
from .limits import (
    MAX_ENTRIES_PER_FIELD,
    MAX_EXPLANATION_DEPTH,
    MAX_EXPLANATION_EDGES,
    MAX_EXPLANATION_NODES,
    MAX_LABEL_CHARS,
    MAX_PROJECTION_NODES,
    MAX_PROVENANCE_REFS,
    MAX_RATIONALE_CHARS,
    MAX_TEXT_CHARS,
)
from .sources import bounded_metadata
from .versions import (
    CONTRACT_VERSION,
    content_digest,
    require_contract_version,
    require_digest,
    require_identifier,
    require_text,
    require_version_text,
)

__all__ = [
    "CACHE_KEY_EXCLUSIONS",
    "DERIVED_NODE_KINDS",
    "EMITTED_NODE_KINDS",
    "EXPLANATION_COMPILER_VERSION",
    "EXPLANATION_PROFILE_VERSION",
    "GROUND_NODE_KINDS",
    "ROOT_CLASSIFICATION",
    "ExplanationCacheKey",
    "ExplanationEdge",
    "ExplanationEdgeKind",
    "ExplanationEntry",
    "ExplanationLevel",
    "ExplanationNode",
    "ExplanationNodeKind",
    "ExplanationProjection",
    "IntentExplanationGraph",
    "compile_explanation_graph",
    "explanation_cache_key",
    "explanation_levels",
    "reachable_roots",
    "require_cache_valid",
    "why_node",
]

#: Versioned identity of the graph compiler, recorded in every projection and cache key.
EXPLANATION_COMPILER_VERSION = "m03-explanation-compiler-v1"

#: Version of the §18 rendering profile. Separate from the compiler on purpose: rewording a
#: ``HUMAN`` sentence invalidates cached *packets* without invalidating the graph they render,
#: and collapsing the two versions would throw away whole graphs to change a period.
EXPLANATION_PROFILE_VERSION = "m03-explanation-profile-v1"


# --------------------------------------------------------------------------- #
# §16: the vocabulary of an explanation
# --------------------------------------------------------------------------- #


class ExplanationNodeKind(Labeled):
    """What a node stands for (§16's list, plus the two things that explain themselves).

    The split that matters is not the list, it is which of these may *ground* a claim. §16's
    closing rule demands a path to "admitted source semantics or policy", and the seven kinds
    below ``EXECUTION_GAP`` are exactly that. An operation, a demand, a protection or a gap is
    what M03 *emitted*, and a receipt is what a provider later *observed*: none of them can be
    its own reason.
    """

    RAW_SOURCE = "RAW_SOURCE"
    INTENT_STATEMENT = "INTENT_STATEMENT"
    CONSTRAINT = "CONSTRAINT"
    AMBIGUITY_RESOLUTION = "AMBIGUITY_RESOLUTION"
    FREEDOM_ZONE = "FREEDOM_ZONE"
    FIDELITY_OBLIGATION = "FIDELITY_OBLIGATION"
    GOVERNED_POLICY = "GOVERNED_POLICY"
    INTENT_OPERATION = "INTENT_OPERATION"
    CAPABILITY_DEMAND = "CAPABILITY_DEMAND"
    MUTATION_PROTECTION = "MUTATION_PROTECTION"
    EXECUTION_GAP = "EXECUTION_GAP"
    PROVIDER_TRANSLATION_RECEIPT = "PROVIDER_TRANSLATION_RECEIPT"


#: Nodes that admit a claim: a bound ref into something that was already true.
GROUND_NODE_KINDS: frozenset[str] = frozenset(
    {
        ExplanationNodeKind.RAW_SOURCE.value,
        ExplanationNodeKind.INTENT_STATEMENT.value,
        ExplanationNodeKind.CONSTRAINT.value,
        ExplanationNodeKind.AMBIGUITY_RESOLUTION.value,
        ExplanationNodeKind.FREEDOM_ZONE.value,
        ExplanationNodeKind.FIDELITY_OBLIGATION.value,
        ExplanationNodeKind.GOVERNED_POLICY.value,
    }
)

#: Nodes M03 produced, each of which §16 requires a path from it to a ground.
EMITTED_NODE_KINDS: frozenset[str] = frozenset(
    {
        ExplanationNodeKind.INTENT_OPERATION.value,
        ExplanationNodeKind.CAPABILITY_DEMAND.value,
        ExplanationNodeKind.MUTATION_PROTECTION.value,
        ExplanationNodeKind.EXECUTION_GAP.value,
    }
)

#: Nodes that record an observation made outside M03. §23: nothing canonical is grounded in these.
DERIVED_NODE_KINDS: frozenset[str] = frozenset(
    {ExplanationNodeKind.PROVIDER_TRANSLATION_RECEIPT.value}
)


class ExplanationEdgeKind(Labeled):
    """The five relations §16 names, read uniformly in one direction.

    An edge always runs *from* the thing that needs explaining *to* the thing that explains it,
    so ``A REQUIRED_BY B`` is read "A is required by B" and a walk that follows out-edges is a
    walk towards a reason. A single convention is what makes §16's path rule checkable: with two
    readings available, "it reaches a source" would be a claim about the reader's preference.
    """

    DERIVED_FROM = "DERIVED_FROM"
    REQUIRED_BY = "REQUIRED_BY"
    CONSTRAINED_BY = "CONSTRAINED_BY"
    SELECTED_BECAUSE = "SELECTED_BECAUSE"
    UNRESOLVED_BECAUSE = "UNRESOLVED_BECAUSE"


class ExplanationLevel(Labeled):
    """The §18 renderings, ordered by how much prose they carry.

    ``TRACE_ID_ONLY`` is first because it is the one a machine pipeline reads, and it is the level
    that has to be honest about carrying no reasoning: its value is that two runs can be compared
    by ref, which a sentence defeats.
    """

    TRACE_ID_ONLY = "TRACE_ID_ONLY"
    COMPACT = "COMPACT"
    HUMAN = "HUMAN"
    AUDIT = "AUDIT"

    @property
    def carries_prose(self) -> bool:
        return self is ExplanationLevel.HUMAN or self is ExplanationLevel.AUDIT

    @property
    def carries_provenance(self) -> bool:
        return self is ExplanationLevel.AUDIT

    @property
    def carries_labels(self) -> bool:
        return self is not ExplanationLevel.TRACE_ID_ONLY


#: Field richness permitted per level, enforced on every entry so a cheap projection cannot carry
#: an expensive claim and an expensive one cannot quietly drop it.
_ENTRY_FIELDS_BY_LEVEL: dict[str, frozenset[str]] = MappingProxyType({
    ExplanationLevel.TRACE_ID_ONLY.value: frozenset({"relations"}),
    ExplanationLevel.COMPACT.value: frozenset({"relations", "label"}),
    ExplanationLevel.HUMAN.value: frozenset({"relations", "label", "narrative"}),
    ExplanationLevel.AUDIT.value: frozenset(
        {"relations", "label", "narrative", "provenance"}
    ),
})

#: Which ground a ref of each namespace counts as, per §16's "admitted source semantics or policy".
#: Total over the kinds that can legitimately stand behind a compiled claim; the kinds deliberately
#: absent (``BUNDLE``, ``EXECUTION_BUNDLE``, ``RECEIPT``, ``DEBT``, ``FRESHNESS``, ``PASSPORT``,
#: ``CAPABILITY``) are pointers into M03's own bookkeeping or into what was *demanded*, and a thing
#: cannot be its own reason.
ROOT_CLASSIFICATION: dict[str, str] = MappingProxyType({
    RefKind.SOURCE.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.PROVENANCE.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.CANON.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.EXTERNAL.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.DESTINATION.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.BRIEF.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.REVISION.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.OPEN_QUESTION.value: ExplanationNodeKind.AMBIGUITY_RESOLUTION.value,
    RefKind.AMBIGUITY.value: ExplanationNodeKind.AMBIGUITY_RESOLUTION.value,
    RefKind.STATEMENT.value: ExplanationNodeKind.INTENT_STATEMENT.value,
    RefKind.CONSTRAINT.value: ExplanationNodeKind.CONSTRAINT.value,
    RefKind.ANCHOR.value: ExplanationNodeKind.CONSTRAINT.value,
    RefKind.PREDICATE.value: ExplanationNodeKind.CONSTRAINT.value,
    RefKind.FREEDOM_ZONE.value: ExplanationNodeKind.FREEDOM_ZONE.value,
    RefKind.POLICY.value: ExplanationNodeKind.GOVERNED_POLICY.value,
    RefKind.OBLIGATION.value: ExplanationNodeKind.FIDELITY_OBLIGATION.value,
    RefKind.CONTRACT_SET.value: ExplanationNodeKind.FIDELITY_OBLIGATION.value,
    RefKind.M01_CONTRACT.value: ExplanationNodeKind.FIDELITY_OBLIGATION.value,
    RefKind.M01_DIMENSION.value: ExplanationNodeKind.FIDELITY_OBLIGATION.value,
    RefKind.M01_DIMENSION_REGISTRY.value: ExplanationNodeKind.FIDELITY_OBLIGATION.value,
    RefKind.M01_EVALUATOR.value: ExplanationNodeKind.FIDELITY_OBLIGATION.value,
    RefKind.M01_DOMAIN_PROFILE.value: ExplanationNodeKind.FIDELITY_OBLIGATION.value,
    RefKind.SEMANTIC_TYPE.value: ExplanationNodeKind.CONSTRAINT.value,
    RefKind.M02_PROJECT.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.M02_PRODUCTION.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.M02_BRANCH.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.M02_VARIANT.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.M02_NODE.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.M02_SNAPSHOT.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.M02_BUILD.value: ExplanationNodeKind.RAW_SOURCE.value,
    RefKind.M02_RELEASE.value: ExplanationNodeKind.RAW_SOURCE.value,
})


def ground_kind_for(ref: Any) -> str:
    """Classify a ref as the kind of ground it is, or refuse it as a ground.

    The refusal is the point of the function. A capability id appearing where a *reason* belongs
    is the shape of "we need SDXL because we need SDXL", and an unbound ref is a pointer nobody
    can re-check; both read as an explanation until a downstream reader asks what was actually
    admitted, which is too late to answer.
    """

    value = require_bound_ref(ref, "subject_ref")
    kind = ROOT_CLASSIFICATION.get(value.kind)
    if kind is None:
        raise ExplanationError(
            f"{value.text} cannot ground a claim: {value.kind} names "
            f"{_bookkeeping_label(value.kind)}, not admitted source semantics or policy; §16's path "
            "has to end in something that was already true"
        )
    return kind


def _bookkeeping_label(kind: str) -> str:
    if kind == RefKind.CAPABILITY.value:
        return "a capability, which is what a demand asks for"
    if kind in {RefKind.BUNDLE.value, RefKind.EXECUTION_BUNDLE.value}:
        return "a compilation artifact, which is what is being explained"
    if kind == RefKind.RECEIPT.value:
        return "a provider's own account, which §23 keeps out of canonical grounds"
    return "bookkeeping state derived from the compilation itself"


# --------------------------------------------------------------------------- #
# shared normalizers
# --------------------------------------------------------------------------- #


def _slug(value: str, *, maximum: int = 48) -> str:
    cleaned = "".join(
        character if character.isalnum() else "-" for character in value.strip().lower()
    ).strip("-")
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned[:maximum] or "x"


def _text(value: Any, name: str, *, maximum: int = MAX_TEXT_CHARS) -> str:
    if not isinstance(value, str):
        raise SchemaValidationError(f"{name} must be a string")
    return require_text(value.strip(), name, maximum=maximum)


def _ids(value: Any, name: str, *, limit: int = MAX_ENTRIES_PER_FIELD) -> tuple[str, ...]:
    entries = tuple(
        sorted({_slug(_text(item, f"{name}[]"), maximum=128) for item in (value or ())})
    )
    if len(entries) > limit:
        raise LimitExceededError(f"{name} holds {len(entries)} entries, above the bound of {limit}")
    return entries


def _refs(value: Any, name: str, *, limit: int = MAX_PROVENANCE_REFS) -> tuple[SemanticRef, ...]:
    entries = tuple(
        sorted(
            (SemanticRef.coerce(item, f"{name}[]") for item in (value or ())),
            key=lambda item: item.text,
        )
    )
    if len(entries) > limit:
        raise LimitExceededError(f"{name} holds {len(entries)} refs, above the bound of {limit}")
    return entries


# --------------------------------------------------------------------------- #
# §16: nodes and edges
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ExplanationNode(Record):
    """One thing in the explanation, pinned to whatever it stands for (§16).

    The two identities are different on purpose. A ground node's ``record_digest`` *is* its ref's
    content digest, because the thing it stands for lives outside M03 and only a digest can say
    which version of it was trusted. An emitted node's digest is taken over the canonical record's
    own fingerprint inputs, so the node is provably about the semantics that were compiled and not
    about a later restatement of them.
    """

    node_id: str
    kind: str
    record_digest: str
    subject_ref: SemanticRef | None = None
    label: str | None = None
    detail: str | None = None
    provenance_refs: tuple[SemanticRef, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    contract_version: str = ""

    #: A node describes, it does not authorize: §17's answers carry no dispatch meaning.
    authorizes_side_effects = False
    is_execution_plan = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        kind = ExplanationNodeKind.parse(self.kind, "kind")
        object.__setattr__(self, "kind", kind.value)
        object.__setattr__(self, "record_digest", require_digest(self.record_digest, "record_digest"))
        if self.subject_ref is not None:
            object.__setattr__(
                self, "subject_ref", require_bound_ref(self.subject_ref, "subject_ref")
            )
        if kind.value in GROUND_NODE_KINDS:
            if self.subject_ref is None:
                raise SchemaValidationError(
                    f"ground node {self.node_id} has no subject ref; §16's path ends in an admitted "
                    "ref, and a ground that names none is an assertion about nothing"
                )
            if self.subject_ref.kind not in ROOT_CLASSIFICATION:
                raise ExplanationError(
                    f"node {self.node_id} grounds the graph in {self.subject_ref.text}, a namespace "
                    "M03 does not treat as admitted source semantics or policy"
                )
            if self.record_digest != self.subject_ref.content_digest:
                raise SchemaValidationError(
                    f"ground node {self.node_id} digests {self.record_digest[:12]} but pins "
                    f"{(self.subject_ref.content_digest or '')[:12]}; a ground whose own digest "
                    "disagrees with the ref it cites is how a stale explanation survives a revision"
                )
            if kind.value != ROOT_CLASSIFICATION[self.subject_ref.kind]:
                raise SchemaValidationError(
                    f"node {self.node_id} classifies {self.subject_ref.kind} as {kind.value}, which "
                    f"is not the {ROOT_CLASSIFICATION[self.subject_ref.kind]} §16 assigns it"
                )
        else:
            if self.subject_ref is not None:
                raise SchemaValidationError(
                    f"emitted node {self.node_id} carries a subject ref; what M03 produced is "
                    "identified by the record it explains, and a second pointer invites a graph and "
                    "a bundle to disagree about the same operation"
                )
        if self.label is not None:
            object.__setattr__(self, "label", _text(self.label, "label", maximum=MAX_LABEL_CHARS))
        if self.detail is not None:
            object.__setattr__(
                self, "detail", _text(self.detail, "detail", maximum=MAX_RATIONALE_CHARS)
            )
        object.__setattr__(
            self, "provenance_refs", _refs(self.provenance_refs, "provenance_refs")
        )
        object.__setattr__(self, "metadata", bounded_metadata(self.metadata, "metadata"))
        if kind.value not in DERIVED_NODE_KINDS and kind.value != ExplanationNodeKind.EXECUTION_GAP.value:
            found = find_provider_vocabulary(
                {"label": self.label, "detail": self.detail, "metadata": self.metadata}
            )
            if found:
                raise SchemaValidationError(
                    f"node {self.node_id} carries provider vocabulary {list(found)}; §7 keeps an "
                    "explanation of canonical intent free of implementation names, and a gap's "
                    "prose about a missing capability is the one place the word has to appear"
                )
        elif kind.value in DERIVED_NODE_KINDS and self.detail is not None:
            # §23: a receipt's prose is a provider's claim, bounded so it cannot become a payload
            # smuggle, but never scanned as if M03 asserted it and never allowed to ground an edge.
            object.__setattr__(self, "detail", _text(self.detail, "detail", maximum=MAX_TEXT_CHARS))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def kind_enum(self) -> ExplanationNodeKind:
        return ExplanationNodeKind.parse(self.kind)

    @property
    def is_ground(self) -> bool:
        return self.kind in GROUND_NODE_KINDS

    @property
    def is_derived_layer(self) -> bool:
        return self.kind in DERIVED_NODE_KINDS

    @property
    def subject_text(self) -> str:
        return self.subject_ref.text if self.subject_ref is not None else self.node_id

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "record": self.record_digest,
            "subject": self.subject_ref.text if self.subject_ref is not None else None,
            "label": self.label,
        }


ExplanationNode.NESTED = {"subject_ref": of(SemanticRef), "provenance_refs": of(SemanticRef)}


@dataclass(frozen=True)
class ExplanationEdge(Record):
    """One step of reasoning, directed from what needs explaining to what explains it (§16).

    ``reason`` is prose about the relation, not a new authority: it explains why the edge was
    drawn, and nothing in M03 reads it as a constraint. That is why a ground is a *target* of edges
    and effectively never their source — a sentence about why two admitted facts were connected is
    M03's claim, and M03's claims need the same path as its operations do.
    """

    edge_id: str
    relation: str
    from_node: str
    to_node: str
    reason: str | None = None
    source_refs: tuple[SemanticRef, ...] = ()
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "edge_id", require_identifier(self.edge_id, "edge_id"))
        kind = ExplanationEdgeKind.parse(self.relation, "relation")
        object.__setattr__(self, "relation", kind.value)
        for name in ("from_node", "to_node"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        if self.from_node == self.to_node:
            raise SchemaValidationError(
                f"edge {self.edge_id} explains {self.from_node} with itself"
            )
        if self.reason is not None:
            object.__setattr__(self, "reason", _text(self.reason, "reason", maximum=MAX_RATIONALE_CHARS))
        object.__setattr__(self, "source_refs", _refs(self.source_refs, "source_refs"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def relation_enum(self) -> ExplanationEdgeKind:
        return ExplanationEdgeKind.parse(self.relation)

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "relation": self.relation,
            "from": self.from_node,
            "to": self.to_node,
            "sources": sorted(item.text for item in self.source_refs),
        }


ExplanationEdge.NESTED = {"source_refs": of(SemanticRef)}


def _node_id_for_ref(ref: SemanticRef, kind: str) -> str:
    return (
        f"n-{_slug(kind)}-{_slug(ref.ref_id)}-{(ref.content_digest or 'unbound')[:12]}"
    )


def _node_id_for_record(prefix: str, ident: str, record_digest: str) -> str:
    return f"n-{_slug(prefix)}-{_slug(ident)}-{record_digest[:12]}"


def _envelope_node_id(envelope: Any) -> str:
    return _node_id_for_record("env", envelope.envelope_id, content_digest(envelope.fingerprint_inputs()))


def _joined(*parts: Any) -> str | None:
    """Compose a node's detail from whatever the record actually says, or nothing.

    An absent piece contributes no clause rather than an empty one, because a rendered detail of
    ``"permits ; notes"`` reads like the record said something and it did not.
    """

    clauses = [str(item).strip() for item in parts if item is not None and str(item).strip()]
    if not clauses:
        return None
    joined = "; ".join(clauses)
    return joined[:MAX_TEXT_CHARS]


def _edge_id(relation: str, from_node: str, to_node: str) -> str:
    return f"e-{_slug(relation, maximum=20)}-{content_digest([relation, from_node, to_node])[:16]}"


# --------------------------------------------------------------------------- #
# §16: the graph
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class IntentExplanationGraph(Record):
    """The immutable explanation of one execution-intent revision (§16).

    Four properties are checked at construction, and each one is a way an explanation can look
    complete while being worthless. A cycle makes "why" unanswerable. A dangling edge makes the
    graph claim a dependency nobody declared. An emitted node with no path to a ground is an
    operation M03 invented. And a canonical node grounded in a provider receipt is §23's boundary
    crossed in the direction that matters: not a provider editing the brief, which is obviously
    wrong, but a brief quietly *accepting* a provider's account as its reason.

    The graph never mutates the bundle it explains, and holds no reference a reader could use to
    write back: the bundle is cited by digest.
    """

    graph_id: str
    bundle_ref: SemanticRef
    bundle_digest: str
    semantic_digest: str
    nodes: tuple[ExplanationNode, ...] = ()
    edges: tuple[ExplanationEdge, ...] = ()
    compiler_version: str = EXPLANATION_COMPILER_VERSION
    profile_version: str = EXPLANATION_PROFILE_VERSION
    contract_version: str = ""

    #: §16 as structure: an explanation of semantics, never an execution plan.
    is_execution_plan = False
    authorizes_side_effects = False
    mutates_bundle = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        object.__setattr__(
            self,
            "bundle_ref",
            require_bound_ref(self.bundle_ref, "bundle_ref", kind=RefKind.EXECUTION_BUNDLE),
        )
        for name in ("bundle_digest", "semantic_digest"):
            object.__setattr__(self, name, require_digest(getattr(self, name), name))
        if self.bundle_ref.content_digest != self.bundle_digest:
            raise SchemaValidationError(
                f"graph {self.graph_id} cites bundle ref "
                f"{(self.bundle_ref.content_digest or '')[:12]} while recording bundle digest "
                f"{self.bundle_digest[:12]}; the pointer into the compilation and the compilation it "
                "explains have to be one thing, or a reader cannot tell which intent this graph ends "
                "up defending"
            )

        nodes = tuple(
            sorted(
                (ExplanationNode.coerce(item, "nodes[]") for item in (self.nodes or ())),
                key=lambda item: item.node_id,
            )
        )
        if not nodes:
            raise SchemaValidationError(
                f"graph {self.graph_id} explains nothing; an empty explanation reads as a compiled "
                "intent that needed no reason, which is the one thing §16 refuses to imply"
            )
        if len(nodes) > MAX_EXPLANATION_NODES:
            raise LimitExceededError(
                f"graph {self.graph_id} has {len(nodes)} nodes, above the bound of "
                f"{MAX_EXPLANATION_NODES}"
            )
        duplicated = _repeat_of(item.node_id for item in nodes)
        if duplicated:
            raise SchemaValidationError(f"graph {self.graph_id} repeats nodes {duplicated}")
        by_id = {item.node_id: item for item in nodes}
        if len(by_id) != len(nodes):  # pragma: no cover - _repeat_of already refused
            raise SchemaValidationError(f"graph {self.graph_id} has colliding node ids")
        object.__setattr__(self, "nodes", nodes)

        edges = tuple(
            sorted(
                (ExplanationEdge.coerce(item, "edges[]") for item in (self.edges or ())),
                key=lambda item: (item.edge_id, item.from_node, item.to_node),
            )
        )
        if len(edges) > MAX_EXPLANATION_EDGES:
            raise LimitExceededError(
                f"graph {self.graph_id} has {len(edges)} edges, above the bound of "
                f"{MAX_EXPLANATION_EDGES}"
            )
        duplicated = _repeat_of(item.edge_id for item in edges)
        if duplicated:
            raise SchemaValidationError(f"graph {self.graph_id} repeats edges {duplicated}")
        for edge in edges:
            for name in ("from_node", "to_node"):
                target = getattr(edge, name)
                if target not in by_id:
                    raise ExplanationError(
                        f"edge {edge.edge_id} points {name} at {target}, which this graph does not "
                        "carry; a dangling edge is not an incomplete explanation but an unchecked one"
                    )
            if not by_id[edge.from_node].is_ground and by_id[edge.to_node].is_derived_layer:
                raise ExplanationError(
                    f"edge {edge.edge_id} grounds {edge.from_node} in the provider observation "
                    f"{edge.to_node}; §23 keeps a provider's account of a translation out of the "
                    "reasons for the intent that was translated"
                )
        object.__setattr__(self, "edges", edges)

        adjacency = {node.node_id: tuple(sorted({e.to_node for e in edges if e.from_node == node.node_id})) for node in nodes}
        cycle = detect_cycle(adjacency)
        if cycle:
            raise ExplanationError(
                f"graph {self.graph_id} is cyclic at {' -> '.join(cycle)}; a loop of reasons "
                "answers 'why' with 'because'"
            )
        depth = _longest_path(adjacency)
        if depth > MAX_EXPLANATION_DEPTH:
            raise LimitExceededError(
                f"graph {self.graph_id} is {depth} nodes deep, above the bound of "
                f"{MAX_EXPLANATION_DEPTH}; a deeper chain is not explained better, and no reader "
                "traverses it"
            )

        stranded = sorted(
            node.node_id
            for node in nodes
            if not node.is_ground and not _reaches_ground(node.node_id, adjacency, by_id)
        )
        if stranded:
            raise ExplanationError(
                f"graph {self.graph_id} emits {stranded} with no path to admitted source semantics "
                "or policy; §16 requires the path, and D-M03-S04-012 makes it a construction rule "
                "rather than a documentation habit"
            )

        object.__setattr__(
            self, "compiler_version", require_version_text(self.compiler_version, "compiler_version")
        )
        object.__setattr__(
            self, "profile_version", require_version_text(self.profile_version, "profile_version")
        )
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(item.node_id for item in self.nodes)

    @property
    def ground_nodes(self) -> tuple[ExplanationNode, ...]:
        return tuple(item for item in self.nodes if item.is_ground)

    @property
    def emitted_nodes(self) -> tuple[ExplanationNode, ...]:
        return tuple(item for item in self.nodes if not item.is_ground)

    @property
    def relation_kinds(self) -> tuple[str, ...]:
        return tuple(sorted({item.relation for item in self.edges}))

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    def node(self, node_id: str) -> ExplanationNode:
        wanted = require_identifier(node_id, "node_id")
        for item in self.nodes:
            if item.node_id == wanted:
                return item
        raise ExplanationError(f"graph {self.graph_id} carries no node {wanted}")

    def graph_digest(self) -> str:
        """The digest a projection cites, taken over nodes and edges only.

        Version fields are excluded because they are what a projection *records* about the graph
        rather than part of what it renders: including them here would make every §19 cache key
        depend on a value the key already carries, for no added invalidation.
        """

        return content_digest(
            {
                "bundle": self.bundle_ref.text,
                "nodes": [item.fingerprint_inputs() for item in self.nodes],
                "edges": [item.fingerprint_inputs() for item in self.edges],
            }
        )

    def path_to_ground(self, node_id: str) -> tuple[str, ...]:
        """The shortest walk from a node to a ground, in traversal order.

        Shortest rather than first-found because a path is quoted to a human, and because
        "first" over a deterministically-sorted graph still depends on which edge was declared
        first. Two equally short paths are resolved by node id, so the answer is a fact about the
        graph and not about the author.
        """

        wanted = require_identifier(node_id, "node_id")
        self.node(wanted)
        adjacency = self._adjacency()
        order = {node.node_id: sorted(adjacency[node.node_id]) for node in self.nodes}
        previous: dict[str, str] = {}
        seen = {wanted}
        queue: deque[str] = deque([wanted])
        reached: str | None = None
        while queue:
            current = queue.popleft()
            if current != wanted and self.node(current).is_ground:
                reached = current
                break
            for target in order[current]:
                if target in seen:
                    continue
                seen.add(target)
                previous[target] = current
                queue.append(target)
        if reached is None:
            raise ExplanationError(
                f"node {wanted} reaches no ground in graph {self.graph_id}"
            )
        walked = [reached]
        while walked[-1] != wanted:
            walked.append(previous[walked[-1]])
        return tuple(reversed(walked))

    def canonical_facts(self) -> dict[str, tuple[str, ...]]:
        """What every §18 level must agree on: each emitted node and the grounds reachable from it.

        This is §18's last sentence made concrete. A compact packet is allowed to say less, and is
        not allowed to be about something else.
        """

        adjacency = self._adjacency()
        facts: dict[str, tuple[str, ...]] = {}
        for node in self.nodes:
            if node.is_ground:
                continue
            roots = sorted(
                {
                    item.subject_text
                    for item in _reachable(node.node_id, adjacency, self.node)
                    if item.is_ground and item.subject_ref is not None
                }
            )
            if len(roots) > MAX_ENTRIES_PER_FIELD:
                raise LimitExceededError(
                    f"node {node.node_id} reaches {len(roots)} grounds, above the bound of "
                    f"{MAX_ENTRIES_PER_FIELD}; an obligation grounded in that much is a scope problem "
                    "the graph should have shown as separate operations"
                )
            facts[node.node_id] = tuple(roots)
        return dict(sorted(facts.items()))

    def _adjacency(self) -> dict[str, tuple[str, ...]]:
        grouped: dict[str, set[str]] = {item.node_id: set() for item in self.nodes}
        for edge in self.edges:
            grouped[edge.from_node].add(edge.to_node)
        return {key: tuple(sorted(value)) for key, value in sorted(grouped.items())}


IntentExplanationGraph.NESTED = {
    "bundle_ref": of(SemanticRef),
    "nodes": of(ExplanationNode),
    "edges": of(ExplanationEdge),
}


def _repeat_of(values: Iterable[Any]) -> list[str]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return sorted(name for name, total in counts.items() if total > 1)


def _longest_path(adjacency: Mapping[str, tuple[str, ...]]) -> int:
    """Nodes on the deepest chain, computed iteratively over a topological order."""

    indegree = {node: 0 for node in adjacency}
    for node, targets in adjacency.items():
        for target in targets:
            indegree[target] += 1
    depth = {node: 1 for node in adjacency}
    queue: deque[str] = deque(sorted(node for node, total in indegree.items() if total == 0))
    visited = 0
    while queue:
        current = queue.popleft()
        visited += 1
        for target in adjacency[current]:
            depth[target] = max(depth[target], depth[current] + 1)
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited != len(adjacency):  # pragma: no cover - the cycle check ran first
        raise ExplanationError("longest path needs an acyclic graph")
    return max(depth.values()) if depth else 0


def _reachable(
    start: str, adjacency: Mapping[str, tuple[str, ...]], resolve: Any
) -> tuple[Any, ...]:
    seen: set[str] = set()
    queue: deque[str] = deque([start])
    while queue:
        current = queue.popleft()
        for target in adjacency.get(current, ()):
            if target in seen:
                continue
            seen.add(target)
            queue.append(target)
    return tuple(resolve(node) for node in sorted(seen))


def _reaches_ground(start: str, adjacency: Mapping[str, tuple[str, ...]], by_id: Mapping[str, Any]) -> bool:
    if by_id[start].is_ground:
        return True
    seen: set[str] = set()
    queue: deque[str] = deque([start])
    while queue:
        current = queue.popleft()
        for target in adjacency.get(current, ()):
            if target in seen:
                continue
            if by_id[target].is_ground:
                return True
            seen.add(target)
            queue.append(target)
    return False


# --------------------------------------------------------------------------- #
# §16, §8, §23: compiling the graph from a bundle
# --------------------------------------------------------------------------- #


def compile_explanation_graph(
    bundle: Any,
    *,
    graph_id: str | None = None,
    receipts: Iterable[ProviderTranslationReceipt] = (),
) -> IntentExplanationGraph:
    """Build §16's graph over one execution intent, optionally appending receipt layers (§17).

    Nothing is invented here: every edge is drawn from a slot the bundle already declared as the
    reason for something. That is why the compiler can be total — if a claim has no grounding slot,
    it has no explanation, and the graph would have to be the one making it up.
    """

    source = ExecutionIntentBundle.coerce(bundle, "bundle")
    nodes: dict[str, ExplanationNode] = {}
    edges: dict[str, ExplanationEdge] = {}

    def ground(ref: SemanticRef, *, reason_slot: str) -> ExplanationNode:
        kind = ground_kind_for(ref)
        node = ExplanationNode(
            node_id=_node_id_for_ref(ref, kind),
            kind=kind,
            record_digest=ref.content_digest or "",
            subject_ref=ref,
            contract_version=source.contract_version,
            metadata={"slot": _slug(reason_slot, maximum=32)} if reason_slot else {},
        )
        existing = nodes.get(node.node_id)
        if existing is None:
            nodes[node.node_id] = node
        return node

    def emitted(
        node_id: str,
        kind: str,
        record_digest: str,
        *,
        label: str | None = None,
        detail: str | None = None,
        provenance: Iterable[SemanticRef] = (),
    ) -> ExplanationNode:
        node = ExplanationNode(
            node_id=node_id,
            kind=kind,
            record_digest=record_digest,
            label=label,
            detail=detail,
            provenance_refs=tuple(provenance),
            contract_version=source.contract_version,
        )
        nodes.setdefault(node_id, node)
        return node

    def link(frm: str, relation: str, to: str, reason: str | None = None) -> None:
        edge = ExplanationEdge(
            edge_id=_edge_id(relation, frm, to),
            relation=relation,
            from_node=frm,
            to_node=to,
            reason=reason,
            contract_version=source.contract_version,
        )
        edges.setdefault(edge.edge_id, edge)

    for ref in (source.brief_ref, source.revision_ref):
        ground(ref, reason_slot="brief")
    for ref in source.policy_refs:
        ground(ref, reason_slot="policy")
    for ref in (source.contract_set_ref, source.side_effect_policy_ref):
        if ref is not None:
            ground(ref, reason_slot="bundle")
    for ref in (*source.intent_slice_refs, *source.constraint_slice_refs):
        ground(ref, reason_slot="slice")

    for envelope in source.mutation_envelopes:
        emitted(
            _envelope_node_id(envelope),
            ExplanationNodeKind.MUTATION_PROTECTION.value,
            content_digest(envelope.fingerprint_inputs()),
            label=envelope.envelope_id,
            detail=_joined(
                "protects " + ", ".join(envelope.protected_properties)
                if envelope.protected_properties
                else None,
                "permits " + ", ".join(envelope.mutable_properties)
                if envelope.mutable_properties
                else None,
                envelope.notes,
            ),
            provenance=envelope.source_refs,
        )

    def grounding_refs_of(operation: Any) -> tuple[SemanticRef, ...]:
        return tuple(
            sorted(
                {
                    entry.text: entry
                    for entry in tuple(operation.originating_refs)
                    + tuple(operation.source_refs)
                    + tuple(operation.required_explanation_refs)
                    + tuple(operation.provenance_refs)
                }.values(),
                key=lambda item: item.text,
            )
        )

    for operation in source.operations:
        op_digest = content_digest(operation.fingerprint_inputs())
        op_node = _node_id_for_record("op", operation.intent_operation_id, op_digest)
        emitted(
            op_node,
            ExplanationNodeKind.INTENT_OPERATION.value,
            op_digest,
            label=operation.intent_operation_id,
            detail=_joined(operation.purpose, operation.rationale),
            provenance=grounding_refs_of(operation),
        )
        for ref in grounding_refs_of(operation):
            link(
                op_node,
                ExplanationEdgeKind.DERIVED_FROM.value,
                ground(ref, reason_slot="originating").node_id,
                f"{operation.intent_operation_id} is in this intent because that admitted "
                "statement or policy is",
            )
        if operation.intent_slice_ref is not None:
            link(
                op_node,
                ExplanationEdgeKind.SELECTED_BECAUSE.value,
                ground(operation.intent_slice_ref, reason_slot="intent_slice").node_id,
                "the slice this operation was compiled from",
            )
        if operation.constraint_slice_ref is not None:
            link(
                op_node,
                ExplanationEdgeKind.CONSTRAINED_BY.value,
                ground(operation.constraint_slice_ref, reason_slot="constraint_slice").node_id,
                "the constraint slice whose rules bound it",
            )
        for ref in operation.fidelity_contract_refs:
            link(
                op_node,
                ExplanationEdgeKind.CONSTRAINED_BY.value,
                ground(ref, reason_slot="fidelity").node_id,
                "a quality obligation this behaviour has to meet",
            )
        for ref in operation.protected_anchor_refs:
            link(
                op_node,
                ExplanationEdgeKind.CONSTRAINED_BY.value,
                ground(ref, reason_slot="anchor").node_id,
                "semantics that must survive the transformation",
            )
        for ref in operation.freedom_zone_refs:
            link(
                op_node,
                ExplanationEdgeKind.SELECTED_BECAUSE.value,
                ground(ref, reason_slot="zone").node_id,
                "latitude the brief granted, which is a reason for a choice and not the choice",
            )
        if operation.approval_boundary_ref is not None:
            link(
                op_node,
                ExplanationEdgeKind.CONSTRAINED_BY.value,
                ground(operation.approval_boundary_ref, reason_slot="approval").node_id,
                "the boundary §13 puts in front of the side effect this operation only desires",
            )
        for demand_id in operation.capability_demand_ids:
            demand = next(item for item in source.capability_demands if item.demand_id == demand_id)
            demand_digest = content_digest(demand.fingerprint_inputs())
            demand_node = _node_id_for_record("dem", demand.demand_id, demand_digest)
            link(
                demand_node,
                ExplanationEdgeKind.REQUIRED_BY.value,
                op_node,
                f"{demand.demand_id} is demanded because {operation.intent_operation_id} cannot be "
                "satisfied without it",
            )
        if operation.mutation_envelope_ref is not None:
            envelope = next(
                item for item in source.mutation_envelopes if item.envelope_id == operation.mutation_envelope_ref
            )
            link(
                _envelope_node_id(envelope),
                ExplanationEdgeKind.REQUIRED_BY.value,
                op_node,
                "the protection exists because this operation is allowed to touch the artifact",
            )

    for demand in source.capability_demands:
        demand_digest = content_digest(demand.fingerprint_inputs())
        demand_node = _node_id_for_record("dem", demand.demand_id, demand_digest)
        emitted(
            demand_node,
            ExplanationNodeKind.CAPABILITY_DEMAND.value,
            demand_digest,
            label=demand.capability_id,
            detail=_joined(demand.label, demand.notes),
            provenance=demand.source_refs,
        )
        for ref in (*demand.source_refs, *demand.policy_refs):
            link(
                demand_node,
                ExplanationEdgeKind.DERIVED_FROM.value,
                ground(ref, reason_slot="demand_source").node_id,
                "the admitted requirement this capability answers",
            )
        for ref in (*demand.fidelity_contract_refs, *demand.protected_anchor_refs,
                     *demand.preserved_constraint_refs):
            link(
                demand_node,
                ExplanationEdgeKind.CONSTRAINED_BY.value,
                ground(ref, reason_slot="demand_constraint").node_id,
                "what the capability has to preserve, not merely produce",
            )

    for envelope in source.mutation_envelopes:
        envelope_node = _envelope_node_id(envelope)
        for ref in (*envelope.source_refs, *envelope.reference_anchors):
            link(
                envelope_node,
                ExplanationEdgeKind.CONSTRAINED_BY.value,
                ground(ref, reason_slot="envelope").node_id,
                "an anchor or requirement the envelope holds while it permits change",
            )
        for ref in (envelope.drift_policy_ref, envelope.reset_policy_ref):
            if ref is not None:
                link(
                    envelope_node,
                    ExplanationEdgeKind.CONSTRAINED_BY.value,
                    ground(ref, reason_slot="envelope_policy").node_id,
                    "the policy that decides how far drift may go",
                )

    for exploration in source.explorations:
        owner = source.operation(exploration.operation_id)
        op_node = _node_id_for_record(
            "op", owner.intent_operation_id, content_digest(owner.fingerprint_inputs())
        )
        for ref in (*exploration.varies_zone_refs, *exploration.fixed_anchor_refs,
                    *exploration.selection_contract_refs, *exploration.source_refs):
            link(
                op_node,
                ExplanationEdgeKind.SELECTED_BECAUSE.value,
                ground(ref, reason_slot="exploration").node_id,
                "the exploration request was granted inside this latitude, not against it",
            )

    for rule in source.loss_rules:
        item_node = ground(rule.item_ref, reason_slot="loss_item")
        for operation_id in rule.operation_ids:
            owner = source.operation(operation_id)
            link(
                _node_id_for_record(
                    "op", owner.intent_operation_id, content_digest(owner.fingerprint_inputs())
                ),
                ExplanationEdgeKind.CONSTRAINED_BY.value,
                item_node.node_id,
                f"this item may only be approximated {rule.loss_class} under translation",
            )
        for ref in (rule.tolerance_ref, rule.policy_ref):
            if ref is None:
                continue
            for operation_id in rule.operation_ids:
                owner = source.operation(operation_id)
                link(
                    _node_id_for_record(
                        "op", owner.intent_operation_id, content_digest(owner.fingerprint_inputs())
                    ),
                    ExplanationEdgeKind.CONSTRAINED_BY.value,
                    ground(ref, reason_slot="loss_tolerance").node_id,
                    "the bound that makes the approximation bounded",
                )
        for ref in rule.source_refs:
            link(
                item_node.node_id,
                ExplanationEdgeKind.DERIVED_FROM.value,
                ground(ref, reason_slot="loss_source").node_id,
                "the requirement that set the tolerance",
            )

    for gap in source.gaps:
        gap_digest = content_digest(gap.fingerprint_inputs())
        gap_node = _node_id_for_record("gap", gap.gap_id, gap_digest)
        emitted(
            gap_node,
            ExplanationNodeKind.EXECUTION_GAP.value,
            gap_digest,
            label=gap.class_name,
            detail=gap.detail,
            provenance=gap.source_refs,
        )
        for ref in gap.source_refs:
            link(
                gap_node,
                ExplanationEdgeKind.UNRESOLVED_BECAUSE.value,
                ground(ref, reason_slot="gap_source").node_id,
                "the requirement that could not be represented",
            )
        if gap.anchor_ref is not None:
            link(
                gap_node,
                ExplanationEdgeKind.UNRESOLVED_BECAUSE.value,
                ground(gap.anchor_ref, reason_slot="gap_anchor").node_id,
                "the protected semantics left unrepresented",
            )
        if gap.operation_id is not None:
            owner = source.operation(gap.operation_id)
            link(
                gap_node,
                ExplanationEdgeKind.UNRESOLVED_BECAUSE.value,
                _node_id_for_record(
                    "op", owner.intent_operation_id, content_digest(owner.fingerprint_inputs())
                ),
                "the operation this gap blocks",
            )
        if gap.capability_id is not None:
            for demand in source.capability_demands:
                if demand.capability_id != gap.capability_id:
                    continue
                link(
                    gap_node,
                    ExplanationEdgeKind.UNRESOLVED_BECAUSE.value,
                    _node_id_for_record(
                        "dem", demand.demand_id, content_digest(demand.fingerprint_inputs())
                    ),
                    "the demand no provider can serve",
                )

    for receipt in receipts:
        bound = ProviderTranslationReceipt.coerce(receipt, "receipt")
        if bound.bundle_fingerprint_digest != canonical_execution_digest(source):
            raise ExplanationError(
                f"receipt {bound.receipt_id} accounts for {(bound.bundle_fingerprint_digest or '')[:12]} "
                f"while this bundle hashes to {canonical_execution_digest(source)[:12]}; an "
                "explanation of a translation of a superseded intent would read as an answer about "
                "this one, which is how §23's boundary is actually crossed"
            )
        if not bound.items:
            raise ExplanationError(
                f"receipt {bound.receipt_id} accounts for no obligation; a receipt that represents "
                "nothing explains nothing, and appending it would add a node with no path"
            )
        receipt_digest = content_digest(bound.fingerprint_inputs())
        receipt_node = _node_id_for_record("rcp", bound.receipt_id, receipt_digest)
        emitted(
            receipt_node,
            ExplanationNodeKind.PROVIDER_TRANSLATION_RECEIPT.value,
            receipt_digest,
            label=f"{bound.receipt_id}:{bound.compiler_ref.text}",
            detail=bound.notes,
            provenance=bound.proposal_refs,
        )
        for item in bound.items:
            link(
                receipt_node,
                ExplanationEdgeKind.DERIVED_FROM.value,
                ground(item.item_ref, reason_slot="receipt_item").node_id,
                f"the provider reports {item.disposition} for that obligation",
            )

    bundle_digest = canonical_execution_digest(source)
    return IntentExplanationGraph(
        graph_id=require_identifier(
            graph_id or f"ieg-{source.bundle_id}-{source.fingerprint.semantic_digest[:12]}",
            "graph_id",
        ),
        bundle_ref=SemanticRef(
            kind=RefKind.EXECUTION_BUNDLE.value,
            ref_id=source.bundle_id,
            content_digest=bundle_digest,
        ),
        bundle_digest=bundle_digest,
        semantic_digest=source.fingerprint.semantic_digest,
        nodes=tuple(nodes.values()),
        edges=tuple(edges.values()),
        contract_version=source.contract_version,
    )


# --------------------------------------------------------------------------- #
# §17: the questions an explanation has to answer
# --------------------------------------------------------------------------- #


def reachable_roots(graph: Any, node_id: str) -> tuple[ExplanationNode, ...]:
    """Every ground a node's reasoning ends in."""

    target = IntentExplanationGraph.coerce(graph, "graph")
    wanted = require_identifier(node_id, "node_id")
    target.node(wanted)
    adjacency = target._adjacency()
    return tuple(
        item
        for item in _reachable(wanted, adjacency, target.node)
        if item.is_ground
    )


def why_node(graph: Any, node_id: str) -> dict[str, Any]:
    """§17's answer to "why this?", as structure.

    The path, the grounds at its end, and the relations along it: enough to answer why this family
    rather than another (``SELECTED_BECAUSE``), why this protection exists (``REQUIRED_BY``), and
    what blocks completion (``UNRESOLVED_BECAUSE``) without a reader parsing prose.
    """

    target = IntentExplanationGraph.coerce(graph, "graph")
    wanted = require_identifier(node_id, "node_id")
    path = target.path_to_ground(wanted)
    relations = {
        (edge.from_node, edge.to_node): edge.relation
        for edge in target.edges
    }
    return {
        "node": wanted,
        "kind": target.node(wanted).kind,
        "path": path,
        "relations": [
            relations.get((path[index], path[index + 1]), "") for index in range(len(path) - 1)
        ],
        "reasons": [target.node(node).subject_text for node in path if target.node(node).is_ground],
    }


def explanation_levels() -> tuple[str, ...]:
    """§18's levels in the order a caller is expected to try them."""

    return tuple(item.value for item in ExplanationLevel)


# --------------------------------------------------------------------------- #
# §18: projections
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ExplanationEntry(Record):
    """One node as rendered at one §18 level.

    The level's allowance is checked field by field rather than trusted, because the projection is
    the artifact that leaves M03: a ``TRACE_ID_ONLY`` packet that arrived carrying a narrative is
    either a bug or someone promoting a human sentence into a machine contract, and both are worth
    refusing at the boundary that ships it.
    """

    node_id: str
    kind: str
    record_digest: str
    subject_ref: SemanticRef | None = None
    relations: tuple[str, ...] = ()
    label: str | None = None
    narrative: str | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        kind = ExplanationNodeKind.parse(self.kind, "kind")
        object.__setattr__(self, "kind", kind.value)
        object.__setattr__(self, "record_digest", require_digest(self.record_digest, "record_digest"))
        if self.subject_ref is not None:
            object.__setattr__(
                self, "subject_ref", require_bound_ref(self.subject_ref, "subject_ref")
            )
        object.__setattr__(self, "relations", _ids(self.relations, "relations", limit=256))
        if self.label is not None:
            object.__setattr__(self, "label", _text(self.label, "label", maximum=MAX_LABEL_CHARS))
        if self.narrative is not None:
            object.__setattr__(
                self, "narrative", _text(self.narrative, "narrative", maximum=MAX_RATIONALE_CHARS)
            )
        object.__setattr__(self, "provenance", bounded_metadata(self.provenance, "provenance"))
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def kind_enum(self) -> ExplanationNodeKind:
        return ExplanationNodeKind.parse(self.kind)

    def validate_for(self, level: ExplanationLevel) -> None:
        """Refuse richness the level did not ask for, and emptiness it did."""

        allowed = _ENTRY_FIELDS_BY_LEVEL[level.value]
        for name, value in (
            ("label", self.label),
            ("narrative", self.narrative),
            ("provenance", self.provenance or None),
        ):
            if value is not None and name not in allowed:
                raise SchemaValidationError(
                    f"entry {self.node_id} carries {name} at level {level.value}; §18's levels are a "
                    "contract with the reader, and a cheap packet that smuggles prose is the cheap "
                    "answer saying something the audit answer did not"
                )
        if level.carries_labels and self.label is None and self.kind not in GROUND_NODE_KINDS:
            raise SchemaValidationError(
                f"entry {self.node_id} renders {level.value} with no label"
            )
        if level is ExplanationLevel.AUDIT and not self.provenance:
            raise SchemaValidationError(
                f"entry {self.node_id} claims AUDIT with no provenance; the audit level exists to "
                "carry the version and authority chain, and an empty one is a label on nothing"
            )


ExplanationEntry.NESTED = {"subject_ref": of(SemanticRef)}


@dataclass(frozen=True)
class ExplanationProjection(Record):
    """A rendering of §16's graph at one §18 level, with the facts every level shares (§18).

    ``canonical_facts`` is not a convenience copy: it is the claim that this packet is about the
    same graph, and ``verify_against`` is what makes the claim checkable by someone who received
    only the packet. Truncation is recorded rather than hidden, so a bounded rendering is a bounded
    rendering and never a shorter explanation.
    """

    projection_id: str
    graph_ref: SemanticRef
    graph_digest: str
    level: str
    graph_node_count: int
    entries: tuple[ExplanationEntry, ...] = ()
    canonical_facts: Mapping[str, Any] = field(default_factory=dict)
    compiler_version: str = EXPLANATION_COMPILER_VERSION
    profile_version: str = EXPLANATION_PROFILE_VERSION
    contract_version: str = ""

    #: A projection is derived from the graph and cannot be fed back into it.
    canonical_semantics = False
    mutates_graph = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "projection_id", require_identifier(self.projection_id, "projection_id"))
        level = ExplanationLevel.parse(self.level, "level")
        object.__setattr__(self, "level", level.value)
        object.__setattr__(self, "graph_ref", require_bound_ref(self.graph_ref, "graph_ref"))
        object.__setattr__(self, "graph_digest", require_digest(self.graph_digest, "graph_digest"))
        if self.graph_ref.content_digest != self.graph_digest:
            raise SchemaValidationError(
                f"projection {self.projection_id} cites graph "
                f"{(self.graph_ref.content_digest or '')[:12]} while rendering "
                f"{self.graph_digest[:12]}; the ref and the content have to be the same graph or the "
                "packet proves nothing about what it explains"
            )
        if not isinstance(self.graph_node_count, int) or isinstance(self.graph_node_count, bool):
            raise SchemaValidationError("graph_node_count must be an integer")
        if self.graph_node_count <= 0:
            raise SchemaValidationError(
                f"projection {self.projection_id} reports {self.graph_node_count} graph nodes"
            )
        entries = tuple(
            sorted(
                (ExplanationEntry.coerce(item, "entries[]") for item in (self.entries or ())),
                key=lambda item: item.node_id,
            )
        )
        if len(entries) > MAX_PROJECTION_NODES:
            raise LimitExceededError(
                f"projection {self.projection_id} renders {len(entries)} entries, above the bound of "
                f"{MAX_PROJECTION_NODES}"
            )
        duplicated = _repeat_of(item.node_id for item in entries)
        if duplicated:
            raise SchemaValidationError(f"projection {self.projection_id} repeats entries {duplicated}")
        expected = min(self.graph_node_count, MAX_PROJECTION_NODES)
        if len(entries) != expected:
            raise SchemaValidationError(
                f"projection {self.projection_id} renders {len(entries)} of {self.graph_node_count} "
                f"nodes where {expected} were owed; a projection that drops nodes silently is a "
                "shorter explanation, which §18 does not permit, not a bounded rendering, which it does"
            )
        for entry in entries:
            entry.validate_for(level)
        object.__setattr__(self, "entries", entries)

        facts = self.canonical_facts
        if not isinstance(facts, Mapping) or not facts:
            raise SchemaValidationError(
                f"projection {self.projection_id} carries no canonical facts; §18 requires every "
                "level to resolve to the same graph facts, including the machine level"
            )
        if len(facts) > MAX_ENTRIES_PER_FIELD:
            raise LimitExceededError(
                f"projection {self.projection_id} carries {len(facts)} fact entries, above the bound "
                f"of {MAX_ENTRIES_PER_FIELD}"
            )
        normalised: dict[str, tuple[str, ...]] = {}
        for key, value in sorted(facts.items()):
            node_key = require_identifier(key, "canonical_facts key")
            items = tuple(
                sorted({_text(item, f"canonical_facts[{node_key}][]", maximum=512) for item in (value or ())})
            )
            if not items:
                raise SchemaValidationError(
                    f"canonical_facts[{node_key}] is empty; an emitted node with no reachable ground "
                    "should have been refused by the graph, not projected around"
                )
            normalised[node_key] = items
        object.__setattr__(self, "canonical_facts", normalised)

        object.__setattr__(
            self, "compiler_version", require_version_text(self.compiler_version, "compiler_version")
        )
        object.__setattr__(
            self, "profile_version", require_version_text(self.profile_version, "profile_version")
        )
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def level_enum(self) -> ExplanationLevel:
        return ExplanationLevel.parse(self.level)

    @property
    def rendered_node_count(self) -> int:
        return len(self.entries)

    @property
    def is_bounded_rendering(self) -> bool:
        """Whether the §18 rendering hit its bound, which is a fact to publish not hide."""

        return self.graph_node_count > len(self.entries)

    def entry(self, node_id: str) -> ExplanationEntry:
        wanted = require_identifier(node_id, "node_id")
        for item in self.entries:
            if item.node_id == wanted:
                return item
        raise ExplanationError(
            f"projection {self.projection_id} renders no entry for {wanted}"
            + (
                "; the rendering was bounded at "
                f"{MAX_PROJECTION_NODES} nodes, and the packet says so in is_bounded_rendering"
                if self.is_bounded_rendering
                else ""
            )
        )

    def facts_for(self, node_id: str) -> tuple[str, ...]:
        return tuple(self.canonical_facts.get(require_identifier(node_id, "node_id"), ()))

    def verify_against(self, graph: Any) -> "ExplanationProjection":
        """Re-check this packet against the graph it claims to render.

        The check is here rather than only in the constructor because the dangerous case is the one
        where the graph moved underneath a stored projection — a revision, a recompile, a compiler
        bump. Those are exactly the moments a cached explanation is still being served.
        """

        target = IntentExplanationGraph.coerce(graph, "graph")
        if self.graph_digest != target.graph_digest():
            raise StaleSemanticError(
                f"projection {self.projection_id} was rendered from a different graph than "
                f"{target.graph_id} ({self.graph_digest[:12]} against {target.graph_digest()[:12]})"
            )
        if self.graph_node_count != target.node_count:
            raise StaleSemanticError(
                f"projection {self.projection_id} claims {self.graph_node_count} nodes for a graph "
                f"of {target.node_count}"
            )
        if self.canonical_facts != target.canonical_facts():
            raise ExplanationError(
                f"projection {self.projection_id} disagrees with graph {target.graph_id} about the "
                "facts of at least one emitted node; §18 allows a compact rendering, not a compact "
                "explanation"
            )
        for entry in self.entries:
            node = target.node(entry.node_id)
            if node.kind != entry.kind or node.record_digest != entry.record_digest:
                raise ExplanationError(
                    f"entry {entry.node_id} describes {entry.kind}@{entry.record_digest[:12]} where "
                    f"graph {target.graph_id} has {node.kind}@{node.record_digest[:12]}"
                )
        return self

    def render(self) -> str:
        """The packet as a reader asked for it: ids only, a table, sentences, or the full chain."""

        level = self.level_enum
        lines: list[str] = []
        for entry in self.entries:
            if level is ExplanationLevel.TRACE_ID_ONLY:
                lines.append(f"{entry.node_id} {entry.kind} {entry.record_digest[:12]}")
                continue
            head = f"{entry.kind} {entry.node_id}"
            if entry.label:
                head = f"{entry.kind} {entry.node_id}: {entry.label}"
            if level is ExplanationLevel.COMPACT:
                lines.append(f"{head} [{'; '.join(entry.relations) or 'ground'}]")
                continue
            body = entry.narrative or "admitted ground; nothing was inferred to reach it"
            if level is ExplanationLevel.HUMAN:
                lines.append(f"{head}: {body} [{'; '.join(entry.relations)}]")
                continue
            chain = "; ".join(f"{key}={value}" for key, value in sorted(entry.provenance.items()))
            lines.append(
                f"{head}: {body} [{'; '.join(entry.relations)}] {{{chain}}} "
                f"{entry.record_digest[:16]} {entry.contract_version}"
            )
        return "\n".join(lines)


ExplanationProjection.NESTED = {"graph_ref": of(SemanticRef), "entries": of(ExplanationEntry)}


def project_explanation(
    graph: Any, level: Any, *, projection_id: str | None = None
) -> ExplanationProjection:
    """Render §16's graph at one §18 level, without altering it.

    Entries are emitted for every node, grounds included: a reader who asks "what did this rest on"
    is being shown the endpoints, so hiding them would make the compact answer the one that cannot
    be checked.
    """

    target = IntentExplanationGraph.coerce(graph, "graph")
    chosen = ExplanationLevel.parse(level, "level")
    facts = target.canonical_facts()
    outgoing: dict[str, list[str]] = {node.node_id: [] for node in target.nodes}
    for edge in target.edges:
        outgoing[edge.from_node].append(f"{edge.relation}>{edge.to_node}")

    entries: list[ExplanationEntry] = []
    for node in sorted(target.nodes, key=lambda item: item.node_id)[:MAX_PROJECTION_NODES]:
        relations = tuple(sorted(outgoing[node.node_id]))
        entries.append(
            ExplanationEntry(
                node_id=node.node_id,
                kind=node.kind,
                record_digest=node.record_digest,
                subject_ref=node.subject_ref,
                relations=relations,
                label=node.label if chosen.carries_labels else None,
                narrative=_narrative_for(node, relations, facts) if chosen.carries_prose else None,
                provenance=_provenance_for(node, target, facts, chosen) if chosen.carries_provenance else {},
                contract_version=target.contract_version,
            )
        )
    rendered = tuple(entries)
    digest = target.graph_digest()
    return ExplanationProjection(
        projection_id=require_identifier(
            projection_id or f"eip-{target.graph_id}-{chosen.value.lower()}-{digest[:8]}",
            "projection_id",
        ),
        graph_ref=SemanticRef(
            kind=RefKind.PROVENANCE.value,
            ref_id=target.graph_id,
            content_digest=digest,
        ),
        graph_digest=digest,
        level=chosen.value,
        graph_node_count=target.node_count,
        entries=rendered,
        canonical_facts=facts,
        compiler_version=target.compiler_version,
        profile_version=target.profile_version,
        contract_version=target.contract_version,
    )


#: How each emitted kind is described in a sentence, per §17's questions.
_NARRATIVE: dict[str, str] = MappingProxyType({
    ExplanationNodeKind.INTENT_OPERATION.value: "this behaviour is required by the brief",
    ExplanationNodeKind.CAPABILITY_DEMAND.value: "this capability is demanded by an operation",
    ExplanationNodeKind.MUTATION_PROTECTION.value: "this protection bounds what may change",
    ExplanationNodeKind.EXECUTION_GAP.value: "this requirement has no representation yet",
    ExplanationNodeKind.PROVIDER_TRANSLATION_RECEIPT.value: "a provider reported this about its translation",
})


def _narrative_for(node: ExplanationNode, relations: tuple[str, ...], facts: Mapping[str, tuple[str, ...]]) -> str:
    if node.is_ground:
        return f"admitted ground: {node.subject_text}"
    reasons = facts.get(node.node_id, ())
    detail = f" — {node.detail}" if node.detail else ""
    if not relations:
        return f"{_NARRATIVE.get(node.kind, 'explained by the graph')}{detail}; it rests on nothing and §16 refuses that"
    return (
        f"{_NARRATIVE.get(node.kind, 'explained by the graph')}{detail}, because "
        + ", ".join(sorted(relations))
        + (f" (grounds: {', '.join(reasons)})" if reasons else "")
    )


def _provenance_for(
    node: ExplanationNode,
    graph: IntentExplanationGraph,
    facts: Mapping[str, tuple[str, ...]],
    level: ExplanationLevel,
) -> dict[str, str]:
    """The audit chain: how the claim was reached, and which versions stand behind it.

    Grounds are committed by digest rather than pasted. The full list is already in the
    projection's ``canonical_facts``, and metadata is a bounded string field — a node with hundreds
    of grounds would either be truncated in silence or refuse, and neither is as good as a digest
    that a reader can resolve against the facts the same packet carries.
    """

    grounds = facts.get(node.node_id, ())
    values: dict[str, str] = {
        "compiler": graph.compiler_version,
        "profile": graph.profile_version,
        "bundle": graph.bundle_ref.text,
        "level": level.value,
        "ground_count": str(len(grounds)),
    }
    if not node.is_ground:
        values["path"] = " -> ".join(graph.path_to_ground(node.node_id))
    if grounds:
        values["grounds_digest"] = content_digest(grounds)
    return bounded_metadata(values, "provenance")


# --------------------------------------------------------------------------- #
# §19: the cache key
# --------------------------------------------------------------------------- #

#: What the §19 key deliberately ignores, stated as data for the same reason §20 lists its
#: exclusions: an invalidation rule is only auditable if a reviewer can see the omissions.
CACHE_KEY_EXCLUSIONS: tuple[str, ...] = (
    "revision_text",
    "raw_input_digest",
    "graph_bytes",
    "provider_receipt",
    "explanation_rendering",
    "host",
    "provider",
    "cost",
)


@dataclass(frozen=True)
class ExplanationCacheKey(Record):
    """The §19 identity of a cached explanation packet.

    Two halves, and they invalidate for different reasons. The semantic half is what the graph is
    *about*: the §11 source fingerprints and §20's operation fingerprint, both already computed and
    both wording-insensitive by design. The version half is who produced the packet, so a compiler
    or profile bump invalidates without needing to know what changed.

    What is deliberately absent is the byte-level graph digest. §19 promises that a wording-only
    change can reuse machine traces, and a key that hashed the whole graph could not keep that
    promise: restating a rationale changes bytes, and the cache would fall shut on a semantics
    nothing moved. The lineage half of the same sentence is kept honest by
    :meth:`ExplanationProjection.verify_against`, which pins the exact graph a packet rendered — so
    the *validity* of a cached trace is a semantic question and the *provenance* of a particular
    packet stays a byte question, which is the distinction §19 was drawing.
    """

    key_id: str
    source_fingerprints: tuple[str, ...] = ()
    operation_fingerprint: str = ""
    level: str = ExplanationLevel.COMPACT.value
    compiler_version: str = EXPLANATION_COMPILER_VERSION
    profile_version: str = EXPLANATION_PROFILE_VERSION
    excluded_inputs: tuple[str, ...] = CACHE_KEY_EXCLUSIONS
    contract_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "key_id", require_identifier(self.key_id, "key_id"))
        printed = tuple(
            sorted({require_digest(item, "source_fingerprints[]") for item in (self.source_fingerprints or ())})
        )
        if not printed:
            raise SchemaValidationError(
                f"cache key {self.key_id} is keyed on no source fingerprint; §19's cache is of "
                "semantic explanations, and a key that ignores semantics caches a lie forever"
            )
        object.__setattr__(self, "source_fingerprints", printed)
        object.__setattr__(
            self, "operation_fingerprint", require_digest(self.operation_fingerprint, "operation_fingerprint")
        )
        level = ExplanationLevel.parse(self.level, "level")
        object.__setattr__(self, "level", level.value)
        excluded = tuple(
            sorted({require_identifier(item, "excluded_inputs[]") for item in (self.excluded_inputs or ())})
        )
        if not excluded:
            raise SchemaValidationError(
                f"cache key {self.key_id} declares nothing excluded; the exclusions are how a reader "
                "learns that a wording change was meant to reuse the entry"
            )
        object.__setattr__(self, "excluded_inputs", excluded)
        object.__setattr__(
            self, "compiler_version", require_version_text(self.compiler_version, "compiler_version")
        )
        object.__setattr__(
            self, "profile_version", require_version_text(self.profile_version, "profile_version")
        )
        object.__setattr__(
            self, "contract_version", require_contract_version(self.contract_version or CONTRACT_VERSION)
        )

    @property
    def level_enum(self) -> ExplanationLevel:
        return ExplanationLevel.parse(self.level)

    def fingerprint_inputs(self) -> dict[str, Any]:
        return {
            "sources": list(self.source_fingerprints),
            "operations": self.operation_fingerprint,
            "level": self.level,
            "compiler": self.compiler_version,
            "profile": self.profile_version,
        }

    @property
    def token(self) -> str:
        """The string a store keys on. Derived, never stored, so it cannot disagree with its inputs."""

        return content_digest(self.fingerprint_inputs())

    def describes(self, *, bundle: Any, graph: Any) -> bool:
        """Whether this key still describes ``graph`` over ``bundle``."""

        wanted = explanation_cache_key(bundle, graph, level=self.level, key_id=self.key_id)
        return wanted.fingerprint_inputs() == self.fingerprint_inputs()


def explanation_cache_key(
    bundle: Any,
    graph: Any,
    *,
    level: Any = ExplanationLevel.COMPACT.value,
    key_id: str | None = None,
) -> ExplanationCacheKey:
    """Take §19's key over one graph, at one level."""

    source = ExecutionIntentBundle.coerce(bundle, "bundle")
    target = IntentExplanationGraph.coerce(graph, "graph")
    if target.semantic_digest != source.fingerprint.semantic_digest:
        raise ExplanationError(
            f"graph {target.graph_id} explains {(target.semantic_digest or '')[:12]} while bundle "
            f"{source.bundle_id} is {source.fingerprint.semantic_digest[:12]}; a cache key taken "
            "over a mismatched pair would serve an explanation of one intent for another"
        )
    chosen = ExplanationLevel.parse(level, "level")
    return ExplanationCacheKey(
        key_id=require_identifier(
            key_id or f"eck-{target.graph_id}-{chosen.value.lower()}", "key_id"
        ),
        source_fingerprints=(
            source.intent_fingerprint_digest,
            source.constraint_fingerprint_digest,
            source.fidelity_fingerprint_digest,
        ),
        operation_fingerprint=source.fingerprint.semantic_digest,
        level=chosen.value,
        compiler_version=source.compiler_version,
        profile_version=target.profile_version,
        contract_version=source.contract_version,
    )


def require_cache_valid(
    key: Any, *, bundle: Any, graph: Any, action: str
) -> ExplanationCacheKey:
    """Refuse to reuse a cached explanation that no longer describes the intent.

    ``StaleSemanticError`` rather than a bool: the callers that matter are the ones about to serve a
    cached answer, and a caller that can ignore ``False`` is a caller that will.
    """

    wanted = ExplanationCacheKey.coerce(key, "key")
    label = _text(action, "action", maximum=64)
    if wanted.describes(bundle=bundle, graph=graph):
        return wanted
    raise StaleSemanticError(
        f"cannot {label} with explanation cache key {wanted.key_id}: the semantics, compiler or "
        f"profile behind {wanted.token[:12]} are no longer the ones in graph "
        f"{IntentExplanationGraph.coerce(graph, 'graph').graph_id}"
    )
