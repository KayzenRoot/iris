"""M02 area B: the typed, immutable Definition Graph and its bound materializations.

Three layers stay distinct on purpose. The Definition Graph is immutable intent:
it carries no worker pid and no transient runtime state. The bound materialization
graph is what impact cones and fingerprints compute from. The Execution Plan is a
provider artifact and never enters this kernel.

Only ``MATERIAL_CAUSAL`` edges carry acyclicity. Ordering and observation edges
exist so a revision can describe sequencing without pretending it dirties a
rendered output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from iris_quality.contracts import QualityClass

from .base import Labeled, Record, of
from .errors import GraphValidationError, IdentityError, SchemaValidationError
from .identity import EntityKind, ExternalRef, new_id, require_id
from .limits import (
    MAX_EDGES,
    MAX_EXTERNAL_NODES,
    MAX_FACETS,
    MAX_METADATA_KEYS,
    MAX_NODES,
    MAX_NODE_METADATA_KEYS,
    MAX_PORTS,
    MAX_SCHEMA_REFS,
    MAX_SLICE_VALUES,
)
from .machines import topological_order
from .versions import (
    CONTRACT_VERSION,
    SUPPORTED_CONTRACT_VERSIONS,
    content_digest,
    require_bounded,
    require_digest,
    require_identifier,
    require_metadata,
    require_millis,
    require_quality_class,
    require_supported_version,
    require_text,
    require_version_text,
)

__all__ = [
    "SemanticTypeRef",
    "NodeRole",
    "PortDirection",
    "PortCardinality",
    "EdgeKind",
    "DependencyFacet",
    "DependencySlice",
    "ReproducibilityClass",
    "SideEffectClass",
    "RetryAdmission",
    "SideEffectPolicy",
    "SemanticPort",
    "GraphNode",
    "GraphEdge",
    "PortExport",
    "SubgraphInterface",
    "DeltaKind",
    "GraphMutation",
    "GraphDelta",
    "GraphDefinition",
    "GraphRevision",
    "MaterializationRecord",
    "MaterializationGraph",
]



class NodeRole(Labeled):
    """What a node *does* semantically, never which provider does it."""

    SOURCE = "SOURCE"
    OPERATION = "OPERATION"
    VALIDATION = "VALIDATION"
    DECISION = "DECISION"
    COMPOSITION = "COMPOSITION"
    SUBGRAPH = "SUBGRAPH"
    DELIVERY = "DELIVERY"

    @property
    def emits_material(self) -> bool:
        return self in {
            NodeRole.SOURCE,
            NodeRole.OPERATION,
            NodeRole.COMPOSITION,
            NodeRole.SUBGRAPH,
            NodeRole.DELIVERY,
        }

    @property
    def must_declare_reproducibility(self) -> bool:
        return self in {
            NodeRole.SOURCE,
            NodeRole.OPERATION,
            NodeRole.COMPOSITION,
            NodeRole.SUBGRAPH,
            NodeRole.DELIVERY,
        }


class PortDirection(Labeled):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    @classmethod
    def opposite(cls, value: Any) -> "PortDirection":
        here = cls.parse(value, "direction")
        return cls.INPUT if here is cls.OUTPUT else cls.OUTPUT


class PortCardinality(Labeled):
    """How many producers may feed a port, and whether their order is meaningful."""

    ONE = "ONE"
    OPTIONAL_ONE = "OPTIONAL_ONE"
    MANY_ORDERED = "MANY_ORDERED"
    MANY_SET = "MANY_SET"

    @property
    def maximum(self) -> int | None:
        return 1 if self in {PortCardinality.ONE, PortCardinality.OPTIONAL_ONE} else None

    @property
    def order_is_semantic(self) -> bool:
        return self is PortCardinality.MANY_ORDERED

    @property
    def forbids_duplicates(self) -> bool:
        return self is PortCardinality.MANY_SET


class EdgeKind(Labeled):
    """Dependency relations, each with an explicit statement of what it can dirty."""

    MATERIAL_CAUSAL = "MATERIAL_CAUSAL"
    CONSTRAINT_CAUSAL = "CONSTRAINT_CAUSAL"
    EVIDENCE_CAUSAL = "EVIDENCE_CAUSAL"
    ACTIVATION = "ACTIVATION"
    ORDER_ONLY = "ORDER_ONLY"
    OBSERVATION = "OBSERVATION"

    @property
    def participates_in_acyclicity(self) -> bool:
        """Material causality only: nothing else can make a revision impossible."""

        return self is EdgeKind.MATERIAL_CAUSAL

    @property
    def dirties_material(self) -> bool:
        return self is EdgeKind.MATERIAL_CAUSAL

    @property
    def revalidates_consumer(self) -> bool:
        return self in {EdgeKind.CONSTRAINT_CAUSAL, EdgeKind.EVIDENCE_CAUSAL}

    @property
    def is_conditional(self) -> bool:
        return self is EdgeKind.ACTIVATION

    @property
    def never_creates_rebuild_dependency(self) -> bool:
        return self in {EdgeKind.ORDER_ONLY, EdgeKind.OBSERVATION}

    @property
    def requires_facets(self) -> bool:
        return self not in {EdgeKind.ORDER_ONLY}


class DependencyFacet(Labeled):
    """The aspect of a dependency a change actually touches."""

    CONTENT = "CONTENT"
    SEMANTICS = "SEMANTICS"
    QUALITY = "QUALITY"
    POLICY = "POLICY"
    RIGHTS = "RIGHTS"
    PROVENANCE = "PROVENANCE"
    DELIVERY = "DELIVERY"
    ENVIRONMENT = "ENVIRONMENT"


class ReproducibilityClass(Labeled):
    """What the kernel may claim about replaying this node, and nothing more."""

    DETERMINISTIC = "DETERMINISTIC"
    SEEDED = "SEEDED"
    ENVIRONMENT_SENSITIVE = "ENVIRONMENT_SENSITIVE"
    STOCHASTIC = "STOCHASTIC"
    HUMAN_DECISION = "HUMAN_DECISION"
    EXTERNAL_STATE = "EXTERNAL_STATE"

    @property
    def claims_byte_identity(self) -> bool:
        """Only these classes may treat a fingerprint match as the same bytes."""

        return self in {ReproducibilityClass.DETERMINISTIC, ReproducibilityClass.SEEDED}

    @property
    def requires_recorded_seed(self) -> bool:
        return self is ReproducibilityClass.SEEDED

    @property
    def is_advisory(self) -> bool:
        return self in {
            ReproducibilityClass.STOCHASTIC,
            ReproducibilityClass.HUMAN_DECISION,
            ReproducibilityClass.EXTERNAL_STATE,
        }


class SideEffectClass(Labeled):
    NO_SIDE_EFFECT = "NO_SIDE_EFFECT"
    CONTROLLED_OUTPUTS = "CONTROLLED_OUTPUTS"
    EXTERNAL_MUTATION = "EXTERNAL_MUTATION"

    @property
    def requires_policy(self) -> bool:
        return self is SideEffectClass.EXTERNAL_MUTATION


class RetryAdmission(Labeled):
    """How much automatic retry a side effect may ever receive."""

    NEVER = "NEVER"
    IDEMPOTENT_AUTO = "IDEMPOTENT_AUTO"
    MANUAL_AFTER_RECONCILIATION = "MANUAL_AFTER_RECONCILIATION"


@dataclass(frozen=True)
class SemanticTypeRef(Record):
    """A reference into the semantic type registry: M02 never hardcodes a media type."""

    type_id: str
    schema_ref: ExternalRef
    version: str = "1.0.0"

    NESTED = {"schema_ref": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "type_id", require_identifier(self.type_id, "type_id"))
        if not isinstance(self.schema_ref, ExternalRef):
            raise SchemaValidationError("schema_ref must be an ExternalRef")
        if self.schema_ref.kind is not EntityKind.SCHEMA:
            raise IdentityError(
                f"schema_ref must reference a SCHEMA, got {self.schema_ref.kind.value}"
            )
        object.__setattr__(self, "version", require_version_text(self.version, "version"))

    @property
    def text(self) -> str:
        return f"{self.type_id}@{self.version}"


@dataclass(frozen=True)
class DependencySlice(Record):
    """A deterministic, versioned sub-part of an input: a region, a locale, a frame range."""

    axis: str
    values: tuple[str, ...]
    selector_version: str = "iris-slice-v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "axis", require_identifier(self.axis, "axis"))
        collected = require_bounded(self.values, "values", maximum=MAX_SLICE_VALUES)
        object.__setattr__(
            self, "values", tuple(require_identifier(item, "values[]") for item in collected)
        )
        if not self.values:
            raise SchemaValidationError("a slice must name at least one value")
        duplicates = sorted({item for item in self.values if self.values.count(item) > 1})
        if duplicates:
            raise SchemaValidationError(f"values contains duplicates: {duplicates}")
        object.__setattr__(self, "selector_version", require_version_text(self.selector_version, "selector_version"))

    @property
    def text(self) -> str:
        return f"{self.selector_version}:{self.axis}={','.join(self.values)}"

    def overlaps(self, other: Any) -> bool:
        return (
            isinstance(other, DependencySlice)
            and other.axis == self.axis
            and other.selector_version == self.selector_version
            and bool(set(other.values) & set(self.values))
        )


@dataclass(frozen=True)
class SideEffectPolicy(Record):
    """The idempotency, compensation and retry admission an external mutation must declare."""

    idempotency_key_ref: ExternalRef
    retry_admission: RetryAdmission = RetryAdmission.MANUAL_AFTER_RECONCILIATION
    compensation_ref: Any = None
    reconciliation_required: bool = True

    NESTED = {"idempotency_key_ref": of(ExternalRef), "compensation_ref": of(ExternalRef)}

    def __post_init__(self) -> None:
        if not isinstance(self.idempotency_key_ref, ExternalRef):
            raise SchemaValidationError("idempotency_key_ref must be an ExternalRef")
        object.__setattr__(self, "retry_admission", RetryAdmission.parse(self.retry_admission))
        if self.compensation_ref is not None and not isinstance(self.compensation_ref, ExternalRef):
            raise SchemaValidationError("compensation_ref must be an ExternalRef or None")
        if not isinstance(self.reconciliation_required, bool):
            raise SchemaValidationError("reconciliation_required must be a boolean")
        if self.retry_admission is RetryAdmission.IDEMPOTENT_AUTO and self.compensation_ref is None:
            raise GraphValidationError(
                "automatic retry of an external mutation requires a declared compensation reference"
            )


@dataclass(frozen=True)
class SemanticPort(Record):
    """A typed, provider-neutral socket on a node."""

    port_id: str
    direction: PortDirection
    semantic_type: SemanticTypeRef
    cardinality: PortCardinality = PortCardinality.ONE
    required: bool = True
    minimum_quality_class: Any = None
    accepted_schema_refs: tuple[ExternalRef, ...] = ()
    activation_ref: Any = None

    NESTED = {
        "semantic_type": of(SemanticTypeRef),
        "accepted_schema_refs": of(ExternalRef),
        "activation_ref": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "port_id", require_identifier(self.port_id, "port_id"))
        object.__setattr__(self, "direction", PortDirection.parse(self.direction, "direction"))
        if not isinstance(self.semantic_type, SemanticTypeRef):
            raise SchemaValidationError("semantic_type must be a SemanticTypeRef")
        object.__setattr__(self, "cardinality", PortCardinality.parse(self.cardinality))
        if not isinstance(self.required, bool):
            raise SchemaValidationError("required must be a boolean")
        if self.minimum_quality_class is not None:
            object.__setattr__(
                self, "minimum_quality_class", require_quality_class(self.minimum_quality_class, "minimum_quality_class").value
            )
        refs = require_bounded(self.accepted_schema_refs, "accepted_schema_refs", maximum=MAX_SCHEMA_REFS)
        object.__setattr__(self, "accepted_schema_refs", tuple(ExternalRef.parse(item, "accepted_schema_refs[]") for item in refs))
        if self.activation_ref is not None and not isinstance(self.activation_ref, ExternalRef):
            raise SchemaValidationError("activation_ref must be an ExternalRef or None")

    @property
    def quality_gate(self) -> QualityClass | None:
        return None if self.minimum_quality_class is None else QualityClass(self.minimum_quality_class)

    def admits_schema(self, schema_ref: ExternalRef) -> bool:
        if not self.accepted_schema_refs:
            return True
        return any(
            item.reference == schema_ref.reference
            and (item.version is None or item.version == schema_ref.version)
            for item in self.accepted_schema_refs
        )


@dataclass(frozen=True)
class GraphNode(Record):
    """One semantic step of a production, declared without any provider machinery."""

    node_id: str
    role: NodeRole
    reproducibility: Any = None
    side_effect: SideEffectClass = SideEffectClass.NO_SIDE_EFFECT
    side_effect_policy: Any = None
    inputs: tuple[SemanticPort, ...] = ()
    outputs: tuple[SemanticPort, ...] = ()
    display_name: str = ""
    operation_ref: Any = None
    policy_refs: tuple[ExternalRef, ...] = ()
    human_decision_required: bool = False
    epoch: int = 0
    contract_version: str = CONTRACT_VERSION
    metadata: tuple[tuple[str, Any], ...] = ()

    NESTED = {
        "inputs": of(SemanticPort),
        "outputs": of(SemanticPort),
        "operation_ref": of(ExternalRef),
        "policy_refs": of(ExternalRef),
        "side_effect_policy": of(SideEffectPolicy),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "role", NodeRole.parse(self.role, "role"))
        if self.reproducibility is not None:
            object.__setattr__(self, "reproducibility", ReproducibilityClass.parse(self.reproducibility))
        elif self.role.must_declare_reproducibility:
            raise GraphValidationError(
                f"node {self.node_id} has role {self.role.value} and must declare a reproducibility class"
            )
        object.__setattr__(self, "side_effect", SideEffectClass.parse(self.side_effect))
        if self.side_effect.requires_policy and not isinstance(self.side_effect_policy, SideEffectPolicy):
            raise GraphValidationError(
                f"node {self.node_id} performs EXTERNAL_MUTATION and must declare an idempotency, "
                "compensation and retry policy before it can be scheduled at all"
            )
        if not self.side_effect.requires_policy and self.side_effect_policy is not None:
            raise GraphValidationError(
                f"node {self.node_id} declares a side-effect policy for a {self.side_effect.value} role"
            )
        for name in ("inputs", "outputs"):
            collected = require_bounded(getattr(self, name), name, maximum=MAX_PORTS)
            ports = tuple(SemanticPort.coerce(item, f"{name}[]") for item in collected)
            wanted = PortDirection.OUTPUT if name == "outputs" else PortDirection.INPUT
            for port in ports:
                if port.direction is not wanted:
                    raise GraphValidationError(
                        f"node {self.node_id} declares {port.port_id} in {name} with direction {port.direction.value}"
                    )
            object.__setattr__(self, name, ports)
        if not isinstance(self.display_name, str):
            raise SchemaValidationError("display_name must be a string")
        if self.display_name:
            object.__setattr__(self, "display_name", require_text(self.display_name, "display_name", maximum=256))
        if self.operation_ref is not None and not isinstance(self.operation_ref, ExternalRef):
            raise SchemaValidationError("operation_ref must be an ExternalRef or None")
        refs = require_bounded(self.policy_refs, "policy_refs", maximum=64)
        object.__setattr__(self, "policy_refs", tuple(ExternalRef.parse(item, "policy_refs[]") for item in refs))
        if not isinstance(self.human_decision_required, bool):
            raise SchemaValidationError("human_decision_required must be a boolean")
        if isinstance(self.epoch, bool) or not isinstance(self.epoch, int) or self.epoch < 0:
            raise SchemaValidationError("epoch must be a non-negative integer")
        require_supported_version("contract", self.contract_version, SUPPORTED_CONTRACT_VERSIONS)
        object.__setattr__(self, "metadata", require_metadata(self.metadata, "metadata", maximum_keys=MAX_NODE_METADATA_KEYS))

    def port(self, port_id: str) -> SemanticPort:
        for port in (*self.inputs, *self.outputs):
            if port.port_id == port_id:
                return port
        raise GraphValidationError(f"node {self.node_id} has no port {port_id!r}")

    @property
    def port_ids(self) -> tuple[str, ...]:
        return tuple(port.port_id for port in (*self.inputs, *self.outputs))


@dataclass(frozen=True)
class GraphEdge(Record):
    """One typed dependency between two ports, with the facets that can dirty it."""

    edge_id: str
    kind: EdgeKind
    source_node_id: str
    source_port_id: str
    target_node_id: str
    target_port_id: str
    facets: tuple[DependencyFacet, ...] = (DependencyFacet.CONTENT,)
    slice: Any = None
    order: Any = None
    feedback: bool = False

    NESTED = {"slice": of(DependencySlice)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "edge_id", require_identifier(self.edge_id, "edge_id"))
        object.__setattr__(self, "kind", EdgeKind.parse(self.kind, "kind"))
        for name in ("source_node_id", "target_node_id", "source_port_id", "target_port_id"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        facets = require_bounded(self.facets, "facets", maximum=MAX_FACETS)
        resolved = tuple(DependencyFacet.parse(item, "facets[]") for item in facets)
        if len(set(resolved)) != len(resolved):
            raise SchemaValidationError(f"facets contains duplicates: {sorted(item.value for item in resolved)}")
        if not resolved:
            raise GraphValidationError(
                f"edge {self.edge_id} must declare at least one dependency facet, because an "
                "unscoped dependency cannot be invalidated selectively"
            )
        object.__setattr__(self, "facets", resolved)
        if self.slice is not None and not isinstance(self.slice, DependencySlice):
            raise SchemaValidationError("slice must be a DependencySlice or None")
        if self.order is not None:
            if isinstance(self.order, bool) or not isinstance(self.order, int) or self.order < 0:
                raise SchemaValidationError("order must be a non-negative integer")
        if not isinstance(self.feedback, bool):
            raise SchemaValidationError("feedback must be a boolean")
        if self.source_node_id == self.target_node_id and self.kind.participates_in_acyclicity:
            raise GraphValidationError(f"edge {self.edge_id} is a material self-loop on {self.source_node_id}")

    @property
    def ports(self) -> tuple[tuple[str, str], tuple[str, str]]:
        return ((self.source_node_id, self.source_port_id), (self.target_node_id, self.target_port_id))

    def touches(self, facet: DependencyFacet) -> bool:
        return DependencyFacet.parse(facet) in self.facets


@dataclass(frozen=True)
class PortExport(Record):
    """How an inner subgraph port becomes visible at the enclosing boundary."""

    external_port_id: str
    inner_node_id: str
    inner_port_id: str
    direction: PortDirection

    def __post_init__(self) -> None:
        for name in ("external_port_id", "inner_node_id", "inner_port_id"):
            object.__setattr__(self, name, require_identifier(getattr(self, name), name))
        object.__setattr__(self, "direction", PortDirection.parse(self.direction))


@dataclass(frozen=True)
class SubgraphInterface(Record):
    """The boundary contract of a SUBGRAPH node: internals stay behind it."""

    node_id: str
    inner_graph_ref: ExternalRef
    exports: tuple[PortExport, ...] = ()
    version: str = "1.0.0"

    NESTED = {"inner_graph_ref": of(ExternalRef), "exports": of(PortExport)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        if not isinstance(self.inner_graph_ref, ExternalRef):
            raise SchemaValidationError("inner_graph_ref must be an ExternalRef")
        exports = require_bounded(self.exports, "exports", maximum=MAX_PORTS)
        object.__setattr__(self, "exports", tuple(PortExport.coerce(item, "exports[]") for item in exports))
        seen = [item.external_port_id for item in self.exports]
        duplicates = sorted({name for name in seen if seen.count(name) > 1})
        if duplicates:
            raise GraphValidationError(f"subgraph {self.node_id} exports duplicated ports: {duplicates}")
        object.__setattr__(self, "version", require_version_text(self.version, "version"))


class DeltaKind(Labeled):
    ADD_NODE = "ADD_NODE"
    REPLACE_NODE = "REPLACE_NODE"
    DROP_NODE = "DROP_NODE"
    ADD_EDGE = "ADD_EDGE"
    REPLACE_EDGE = "REPLACE_EDGE"
    DROP_EDGE = "DROP_EDGE"
    ADD_INTERFACE = "ADD_INTERFACE"
    ADD_DECLARED_INPUT = "ADD_DECLARED_INPUT"


@dataclass(frozen=True)
class GraphMutation(Record):
    """One change to a definition, typed so a receiver can refuse the ones it does not admit."""

    kind: DeltaKind
    target_id: str
    node: Any = None
    edge: Any = None
    interface: Any = None
    declared_input: Any = None

    NESTED = {
        "node": of(GraphNode),
        "edge": of(GraphEdge),
        "interface": of(SubgraphInterface),
        "declared_input": of(ExternalRef),
    }

    PAYLOAD_BY_KIND = {
        DeltaKind.ADD_NODE: "node",
        DeltaKind.REPLACE_NODE: "node",
        DeltaKind.ADD_EDGE: "edge",
        DeltaKind.REPLACE_EDGE: "edge",
        DeltaKind.ADD_INTERFACE: "interface",
        DeltaKind.ADD_DECLARED_INPUT: "declared_input",
    }

    def __post_init__(self) -> None:
        kind = DeltaKind.parse(self.kind, "kind")
        object.__setattr__(self, "kind", kind)
        target = self.target_id
        if isinstance(target, str) and target:
            object.__setattr__(self, "target_id", require_identifier(target, "target_id"))
        elif kind not in {DeltaKind.DROP_NODE, DeltaKind.DROP_EDGE} or not target:
            raise SchemaValidationError("target_id must be an identifier")
        expected = self.PAYLOAD_BY_KIND.get(kind)
        if expected is None:
            for name in ("node", "edge", "interface", "declared_input"):
                if getattr(self, name) is not None:
                    raise GraphValidationError(
                        f"{kind.value} carries {name!r}, which it must not: a dropped element "
                        "is named by its id alone"
                    )
            return
        for name in ("node", "edge", "interface", "declared_input"):
            if name != expected and getattr(self, name) is not None:
                raise GraphValidationError(
                    f"{kind.value} admits a {expected!r} payload, not {name!r}"
                )
        payload = getattr(self, expected)
        if payload is None:
            raise GraphValidationError(f"{kind.value} requires a {expected!r} payload")
        identified = getattr(payload, "node_id", None) or getattr(payload, "edge_id", None) or getattr(payload, "reference", None)
        if identified is not None and identified != self.target_id:
            raise GraphValidationError(
                f"{kind.value} targets {self.target_id!r} but carries a payload for {identified!r}"
            )


@dataclass(frozen=True)
class GraphDelta(Record):
    """A bounded, reviewable proposal to change a graph revision, never a live edit."""

    delta_id: str
    graph_id: str
    base_version: int
    mutations: tuple[GraphMutation, ...] = ()
    reason_code: str = "planned-change"
    origin_ref: Any = None
    contract_version: str = CONTRACT_VERSION
    metadata: tuple[tuple[str, Any], ...] = ()

    NESTED = {"mutations": of(GraphMutation), "origin_ref": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "delta_id", require_id(self.delta_id, "delta_id"))
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        if isinstance(self.base_version, bool) or not isinstance(self.base_version, int) or self.base_version < 1:
            raise SchemaValidationError("base_version must be a positive integer")
        mutations = require_bounded(self.mutations, "mutations", maximum=MAX_EDGES)
        object.__setattr__(self, "mutations", tuple(GraphMutation.coerce(item, "mutations[]") for item in mutations))
        if not self.mutations:
            raise GraphValidationError("a graph delta must carry at least one mutation")
        object.__setattr__(self, "reason_code", require_identifier(self.reason_code, "reason_code"))
        if self.origin_ref is not None and not isinstance(self.origin_ref, ExternalRef):
            raise SchemaValidationError("origin_ref must be an ExternalRef or None")
        require_supported_version("contract", self.contract_version, SUPPORTED_CONTRACT_VERSIONS)
        object.__setattr__(self, "metadata", require_metadata(self.metadata, "metadata", maximum_keys=MAX_METADATA_KEYS))

    @property
    def touches_material(self) -> bool:
        return any(
            mutation.kind in {DeltaKind.ADD_NODE, DeltaKind.REPLACE_NODE, DeltaKind.ADD_EDGE, DeltaKind.REPLACE_EDGE, DeltaKind.DROP_NODE, DeltaKind.DROP_EDGE}
            for mutation in self.mutations
        )

    def declares(self, reference: ExternalRef) -> bool:
        """Whether this delta openly declares an external input."""

        if not isinstance(reference, ExternalRef):
            raise SchemaValidationError("declares expects an ExternalRef")
        return any(
            mutation.kind is DeltaKind.ADD_DECLARED_INPUT and mutation.declared_input == reference
            for mutation in self.mutations
        )


@dataclass(frozen=True)
class GraphDefinition(Record):
    """An immutable, versioned graph: nodes, edges and the inputs it declared in advance."""

    graph_id: str
    version: int
    nodes: tuple[GraphNode, ...] = ()
    edges: tuple[GraphEdge, ...] = ()
    declared_external_inputs: tuple[ExternalRef, ...] = ()
    interfaces: tuple[SubgraphInterface, ...] = ()
    contract_version: str = CONTRACT_VERSION
    metadata: tuple[tuple[str, Any], ...] = ()

    NESTED = {
        "nodes": of(GraphNode),
        "edges": of(GraphEdge),
        "declared_external_inputs": of(ExternalRef),
        "interfaces": of(SubgraphInterface),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise SchemaValidationError("version must be a positive integer")
        nodes = require_bounded(self.nodes, "nodes", maximum=MAX_NODES, kind="node")
        object.__setattr__(self, "nodes", tuple(GraphNode.coerce(item, "nodes[]") for item in nodes))
        edges = require_bounded(self.edges, "edges", maximum=MAX_EDGES, kind="edge")
        object.__setattr__(self, "edges", tuple(GraphEdge.coerce(item, "edges[]") for item in edges))
        declared = require_bounded(self.declared_external_inputs, "declared_external_inputs", maximum=MAX_EXTERNAL_NODES)
        object.__setattr__(self, "declared_external_inputs", tuple(ExternalRef.parse(item, "declared_external_inputs[]") for item in declared))
        interfaces = require_bounded(self.interfaces, "interfaces", maximum=MAX_NODES)
        object.__setattr__(self, "interfaces", tuple(SubgraphInterface.coerce(item, "interfaces[]") for item in interfaces))
        require_supported_version("contract", self.contract_version, SUPPORTED_CONTRACT_VERSIONS)
        object.__setattr__(self, "metadata", require_metadata(self.metadata, "metadata", maximum_keys=MAX_METADATA_KEYS))
        self._validate_structure()

    # --- construction-time validation -----------------------------------------

    def _validate_structure(self) -> None:
        ids = [node.node_id for node in self.nodes]
        duplicates = sorted({name for name in ids if ids.count(name) > 1})
        if duplicates:
            raise GraphValidationError(f"nodes contain duplicate node_id values: {duplicates}")
        by_id = self.node_index
        for node in self.nodes:
            port_ids = node.port_ids
            clash = sorted({name for name in port_ids if port_ids.count(name) > 1})
            if clash:
                raise GraphValidationError(f"node {node.node_id} declares duplicate ports: {clash}")
            if node.role is NodeRole.SUBGRAPH:
                if not any(interface.node_id == node.node_id for interface in self.interfaces):
                    raise GraphValidationError(
                        f"subgraph node {node.node_id} has no SubgraphInterface, so its boundary is undefined"
                    )
            elif any(interface.node_id == node.node_id for interface in self.interfaces):
                raise GraphValidationError(
                    f"interface targets node {node.node_id} whose role is {node.role.value}, not SUBGRAPH"
                )
            if node.role is NodeRole.DECISION and len(node.inputs) < 2:
                raise GraphValidationError(
                    f"decision node {node.node_id} needs at least two candidate inputs to choose between"
                )
        edge_ids = [edge.edge_id for edge in self.edges]
        clash = sorted({name for name in edge_ids if edge_ids.count(name) > 1})
        if clash:
            raise GraphValidationError(f"edges contain duplicate edge_id values: {clash}")
        for edge in self.edges:
            self._validate_edge(edge, by_id)
        self._validate_material_acyclicity(by_id)
        self._validate_port_multiplicity(by_id)
        self._validate_required_inputs(by_id)

    def _validate_edge(self, edge: GraphEdge, by_id: Mapping[str, GraphNode]) -> None:
        for name, node_key, port_key in (
            ("source", edge.source_node_id, edge.source_port_id),
            ("target", edge.target_node_id, edge.target_port_id),
        ):
            node = by_id.get(node_key)
            if node is None:
                raise GraphValidationError(
                    f"edge {edge.edge_id} names unknown {name} node {node_key!r}"
                )
            try:
                port = node.port(port_key)
            except GraphValidationError as error:
                raise GraphValidationError(
                    f"edge {edge.edge_id} names unknown {name} port {port_key!r} on node {node_key!r}"
                ) from error
            wanted = PortDirection.OUTPUT if name == "source" else PortDirection.INPUT
            if port.direction is not wanted:
                raise GraphValidationError(
                    f"edge {edge.edge_id} uses {name} port {port_key} of node {node_key}, "
                    f"which is {port.direction.value} not {wanted.value}"
                )
        source = by_id[edge.source_node_id].port(edge.source_port_id)
        target = by_id[edge.target_node_id].port(edge.target_port_id)
        if source.semantic_type.type_id != target.semantic_type.type_id:
            raise GraphValidationError(
                f"edge {edge.edge_id} connects {source.semantic_type.text} to "
                f"{target.semantic_type.text}: semantic types must match"
            )
        if not target.admits_schema(source.semantic_type.schema_ref):
            raise GraphValidationError(
                f"edge {edge.edge_id} offers schema {source.semantic_type.schema_ref.text} to "
                f"{target.port_id}, which admits "
                f"{sorted(item.text for item in target.accepted_schema_refs) or 'the declared type only'}"
            )
        source_node = by_id[edge.source_node_id]
        target_node = by_id[edge.target_node_id]
        if edge.kind.is_conditional and target_node.epoch != source_node.epoch:
            raise GraphValidationError(
                f"activation edge {edge.edge_id} may not cross epochs, so it cannot gate a later pass"
            )
        if edge.kind.participates_in_acyclicity:
            if edge.feedback and source_node.epoch >= target_node.epoch:
                raise GraphValidationError(
                    f"edge {edge.edge_id} is marked feedback but does not flow from a prior epoch into a "
                    "later epoch; iterative work consumes immutable output from the previous epoch"
                )
            if not edge.feedback and target_node.epoch != source_node.epoch:
                raise GraphValidationError(
                    f"edge {edge.edge_id} crosses epochs {source_node.epoch} -> {target_node.epoch} "
                    "without feedback=True. A previous-epoch reference must be declared as feedback, "
                    "and a later epoch is not part of this revision."
                )
        if edge.slice is not None and not edge.kind.dirties_material and not edge.kind.revalidates_consumer:
            raise GraphValidationError(
                f"edge {edge.edge_id} declares a slice for a {edge.kind.value} edge, which cannot dirty a consumer"
            )

    def _validate_material_acyclicity(self, by_id: Mapping[str, GraphNode]) -> None:
        """Feedback across epochs references frozen output; inside a revision it is a cycle."""

        dependencies: dict[str, list[str]] = {node.node_id: [] for node in self.nodes}
        for edge in self.edges:
            if not edge.kind.participates_in_acyclicity or edge.feedback:
                continue
            dependencies[edge.target_node_id].append(edge.source_node_id)
        try:
            topological_order(tuple(node.node_id for node in self.nodes), dependencies)
        except Exception as error:  # noqa: BLE001 - the kernel reports the cycle once, in its own words
            raise GraphValidationError(str(error)) from error

    def _validate_port_multiplicity(self, by_id: Mapping[str, GraphNode]) -> None:
        """How many producers may feed one socket.

        Cardinality bounds material feeding only: constraint, evidence and activation
        edges describe semantics around a node and are deliberately allowed to
        accumulate without turning a single-input port into a violation.
        """

        incoming: dict[tuple[str, str], list[GraphEdge]] = {}
        for edge in self.edges:
            if not edge.kind.dirties_material:
                continue
            incoming.setdefault((edge.target_node_id, edge.target_port_id), []).append(edge)
        for (node_id, port_id), edges in incoming.items():
            port = by_id[node_id].port(port_id)
            if port.cardinality.maximum is not None and len(edges) > port.cardinality.maximum:
                raise GraphValidationError(
                    f"port {node_id}.{port_id} is {port.cardinality.value} but "
                    f"{len(edges)} edges feed it: {sorted(item.edge_id for item in edges)}"
                )
            if port.cardinality.order_is_semantic:
                orders = [edge.order for edge in edges]
                if any(order is None for order in orders):
                    raise GraphValidationError(
                        f"port {node_id}.{port_id} is MANY_ORDERED, so every feeding edge must declare order"
                    )
                if len(set(orders)) != len(orders):
                    raise GraphValidationError(
                        f"port {node_id}.{port_id} declares duplicated orders: {sorted(orders)}"
                    )
            if port.cardinality.forbids_duplicates:
                sources = [(edge.source_node_id, edge.source_port_id) for edge in edges]
                duplicates = sorted({item for item in sources if sources.count(item) > 1})
                if duplicates:
                    raise GraphValidationError(
                        f"port {node_id}.{port_id} is MANY_SET and receives {duplicates} twice"
                    )

    def _validate_required_inputs(self, by_id: Mapping[str, GraphNode]) -> None:
        fed = {
            (edge.target_node_id, edge.target_port_id)
            for edge in self.edges
            if not edge.kind.never_creates_rebuild_dependency
        }
        for node in self.nodes:
            for port in node.inputs:
                if port.required and (node.node_id, port.port_id) not in fed:
                    raise GraphValidationError(
                        f"required input {node.node_id}.{port.port_id} has no dependency edge; "
                        "declare the dependency, bind it through a variant, or make the port optional"
                    )

    # --- read accessors --------------------------------------------------------

    @property
    def node_index(self) -> Mapping[str, GraphNode]:
        return {node.node_id: node for node in self.nodes}

    @property
    def edge_index(self) -> Mapping[str, GraphEdge]:
        return {edge.edge_id: edge for edge in self.edges}

    def node(self, node_id: str) -> GraphNode:
        wanted = require_identifier(node_id, "node_id")
        try:
            return self.node_index[wanted]
        except KeyError as error:
            raise GraphValidationError(f"graph {self.graph_id} has no node {wanted!r}") from error

    def edges_into(self, node_id: str, *, kinds: Iterable[EdgeKind] | None = None) -> tuple[GraphEdge, ...]:
        admitted = None if kinds is None else frozenset(EdgeKind.parse(item) for item in kinds)
        return tuple(
            edge
            for edge in self.edges
            if edge.target_node_id == node_id and (admitted is None or edge.kind in admitted)
        )

    def edges_out_of(self, node_id: str, *, kinds: Iterable[EdgeKind] | None = None) -> tuple[GraphEdge, ...]:
        admitted = None if kinds is None else frozenset(EdgeKind.parse(item) for item in kinds)
        return tuple(
            edge
            for edge in self.edges
            if edge.source_node_id == node_id and (admitted is None or edge.kind in admitted)
        )

    def material_dependencies(self) -> Mapping[str, tuple[str, ...]]:
        """Predecessor map over material causality, excluding frozen feedback edges."""

        collected: dict[str, list[str]] = {node.node_id: [] for node in self.nodes}
        for edge in self.edges:
            if edge.kind.participates_in_acyclicity and not edge.feedback:
                collected[edge.target_node_id].append(edge.source_node_id)
        return {key: tuple(sorted(set(value))) for key, value in collected.items()}

    def delivery_nodes(self) -> tuple[GraphNode, ...]:
        return tuple(node for node in self.nodes if node.role is NodeRole.DELIVERY)

    def admitted_sources(self) -> tuple[GraphNode, ...]:
        """The nodes that stand at the admitted boundary of this revision."""

        return tuple(node for node in self.nodes if node.role is NodeRole.SOURCE)

    def apply(self, delta: GraphDelta) -> "GraphDefinition":
        """Return the next immutable revision implied by a delta; never edit in place."""

        if not isinstance(delta, GraphDelta):
            raise SchemaValidationError("apply expects a GraphDelta")
        if delta.graph_id != self.graph_id:
            raise GraphValidationError(
                f"delta {delta.delta_id} targets graph {delta.graph_id!r}, not {self.graph_id!r}"
            )
        if delta.base_version != self.version:
            raise GraphValidationError(
                f"delta {delta.delta_id} was built against version {delta.base_version} but this "
                f"definition is version {self.version}; re-derive it instead of guessing"
            )
        nodes = {node.node_id: node for node in self.nodes}
        edges = {edge.edge_id: edge for edge in self.edges}
        interfaces = {interface.node_id: interface for interface in self.interfaces}
        declared = list(self.declared_external_inputs)
        for mutation in delta.mutations:
            kind = mutation.kind
            if kind is DeltaKind.DROP_NODE:
                touched = [edge.edge_id for edge in self.edges if mutation.target_id in (edge.source_node_id, edge.target_node_id)]
                for edge_id in touched:
                    edges.pop(edge_id, None)
                nodes.pop(mutation.target_id, None)
                interfaces.pop(mutation.target_id, None)
            elif kind is DeltaKind.DROP_EDGE:
                edges.pop(mutation.target_id, None)
            elif kind in {DeltaKind.ADD_NODE, DeltaKind.REPLACE_NODE}:
                nodes[mutation.target_id] = mutation.node
            elif kind in {DeltaKind.ADD_EDGE, DeltaKind.REPLACE_EDGE}:
                edges[mutation.target_id] = mutation.edge
            elif kind is DeltaKind.ADD_INTERFACE:
                interfaces[mutation.target_id] = mutation.interface
            else:
                found = any(item.reference == mutation.declared_input.reference for item in declared)
                if not found:
                    declared.append(mutation.declared_input)
        return GraphDefinition(
            graph_id=self.graph_id,
            version=self.version + 1,
            nodes=tuple(nodes[key] for key in sorted(nodes)),
            edges=tuple(edges[key] for key in sorted(edges)),
            declared_external_inputs=tuple(declared),
            interfaces=tuple(interfaces[key] for key in sorted(interfaces)),
            contract_version=self.contract_version,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class GraphRevision(Record):
    """A frozen graph definition bound to a digest, so mutation cannot be silent."""

    revision_id: str
    definition: GraphDefinition
    digest: Any = None
    created_at_ms: int = 0
    admitted_by: Any = None

    NESTED = {"definition": of(GraphDefinition), "admitted_by": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "revision_id", require_id(self.revision_id, "revision_id"))
        if not isinstance(self.definition, GraphDefinition):
            raise SchemaValidationError("definition must be a GraphDefinition")
        computed = content_digest(self.definition.to_payload())
        if self.digest is None:
            object.__setattr__(self, "digest", computed)
        elif self.digest != computed:
            raise GraphValidationError(
                f"revision {self.revision_id} claims digest {self.digest} but its definition "
                f"hashes to {computed}: a frozen revision cannot be edited and relabelled"
            )
        object.__setattr__(self, "created_at_ms", require_millis(self.created_at_ms, "created_at_ms"))
        if self.admitted_by is not None and not isinstance(self.admitted_by, ExternalRef):
            raise SchemaValidationError("admitted_by must be an ExternalRef or None")

    @property
    def graph_id(self) -> str:
        return self.definition.graph_id

    @property
    def version(self) -> int:
        return self.definition.version

    @property
    def is_intact(self) -> bool:
        return self.digest == content_digest(self.definition.to_payload())

    def derive(self, delta: GraphDelta, *, revision_id: str | None = None, created_at_ms: int = 0) -> "GraphRevision":
        """The only way forward from a frozen revision: a new one that cites its delta."""

        return GraphRevision(
            revision_id=new_id() if revision_id is None else require_id(revision_id, "revision_id"),
            definition=self.definition.apply(delta),
            created_at_ms=created_at_ms,
            admitted_by=ExternalRef(kind=EntityKind.DELTA, reference=delta.delta_id),
        )


@dataclass(frozen=True)
class MaterializationRecord(Record):
    """Which immutable revision actually filled which output port, and who made it."""

    node_id: str
    port_id: str
    revision_ref: ExternalRef
    content_digest: str
    producer_attempt_id: Any = None
    quality_class: Any = None
    decision_ref: Any = None
    seed: Any = None
    environment_ref: Any = None
    tool_refs: tuple[ExternalRef, ...] = ()
    produced_at_ms: int = 0

    NESTED = {
        "revision_ref": of(ExternalRef),
        "decision_ref": of(ExternalRef),
        "environment_ref": of(ExternalRef),
        "tool_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "port_id", require_identifier(self.port_id, "port_id"))
        if not isinstance(self.revision_ref, ExternalRef):
            raise SchemaValidationError("revision_ref must be an ExternalRef")
        object.__setattr__(self, "content_digest", require_digest(self.content_digest, "content_digest"))
        if self.producer_attempt_id is not None:
            object.__setattr__(self, "producer_attempt_id", require_id(self.producer_attempt_id, "producer_attempt_id"))
        if self.quality_class is not None:
            object.__setattr__(self, "quality_class", require_quality_class(self.quality_class).value)
        for name in ("decision_ref", "environment_ref"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, ExternalRef):
                raise SchemaValidationError(f"{name} must be an ExternalRef or None")
        if self.seed is not None:
            object.__setattr__(self, "seed", require_text(self.seed, "seed", maximum=128))
        tools = require_bounded(self.tool_refs, "tool_refs", maximum=64)
        object.__setattr__(self, "tool_refs", tuple(ExternalRef.parse(item, "tool_refs[]") for item in tools))
        object.__setattr__(self, "produced_at_ms", require_millis(self.produced_at_ms, "produced_at_ms"))

    @property
    def key(self) -> tuple[str, str]:
        return (self.node_id, self.port_id)

    @property
    def quality(self) -> QualityClass | None:
        return None if self.quality_class is None else QualityClass(self.quality_class)


@dataclass(frozen=True)
class MaterializationGraph(Record):
    """The bound graph: a frozen revision plus what each of its ports actually holds.

    Impact cones and causal fingerprints are computed from this object, never from
    the Definition Graph alone, because the definition deliberately does not know
    which revision is currently admitted.
    """

    revision: GraphRevision
    materializations: tuple[MaterializationRecord, ...] = ()
    variant_selection: tuple[tuple[str, str], ...] = ()
    environment_fingerprint: Any = None
    contract_version: str = CONTRACT_VERSION

    NESTED = {
        "revision": of(GraphRevision),
        "materializations": of(MaterializationRecord),
    }

    def __post_init__(self) -> None:
        if not isinstance(self.revision, GraphRevision):
            raise SchemaValidationError("revision must be a GraphRevision")
        collected = require_bounded(self.materializations, "materializations", maximum=MAX_NODES * 4)
        records = tuple(MaterializationRecord.coerce(item, "materializations[]") for item in collected)
        seen: dict[tuple[str, str], MaterializationRecord] = {}
        for record in records:
            existing = seen.get(record.key)
            if existing is not None:
                if existing == record:
                    continue
                raise GraphValidationError(
                    f"output {record.node_id}.{record.port_id} has two materializations "
                    f"(attempts {existing.producer_attempt_id} and {record.producer_attempt_id}); "
                    "candidate producers must be mediated by an explicit decision node"
                )
            seen[record.key] = record
        object.__setattr__(self, "materializations", tuple(seen[key] for key in sorted(seen)))
        definition = self.revision.definition
        index = definition.node_index
        for record in self.materializations:
            node = index.get(record.node_id)
            if node is None:
                raise GraphValidationError(
                    f"materialization names unknown node {record.node_id!r} of graph {definition.graph_id}"
                )
            port = node.port(record.port_id)
            if port.direction is not PortDirection.OUTPUT:
                raise GraphValidationError(
                    f"{record.node_id}.{record.port_id} is an input port and cannot be materialized"
                )
        selection = require_bounded(self.variant_selection, "variant_selection", maximum=MAX_NODES)
        frozen: list[tuple[str, str]] = []
        for item in selection:
            if (
                not isinstance(item, (tuple, list))
                or len(item) != 2
                or not all(isinstance(part, str) for part in item)
            ):
                raise SchemaValidationError(
                    "variant_selection must be pairs of (variant_set_id, option)"
                )
            frozen.append(
                (require_identifier(item[0], "variant_selection[0]"), require_identifier(item[1], "variant_selection[1]"))
            )
        object.__setattr__(self, "variant_selection", tuple(sorted(frozen)))
        if self.environment_fingerprint is not None:
            object.__setattr__(self, "environment_fingerprint", require_digest(self.environment_fingerprint, "environment_fingerprint"))
        require_supported_version("contract", self.contract_version, SUPPORTED_CONTRACT_VERSIONS)
        self._validate_quality_gates(index)

    def _validate_quality_gates(self, index: Mapping[str, GraphNode]) -> None:
        produced = {record.key: record for record in self.materializations}
        for edge in self.revision.definition.edges:
            if not edge.kind.dirties_material:
                continue
            target_port = index[edge.target_node_id].port(edge.target_port_id)
            floor = target_port.quality_gate
            if floor is None:
                continue
            source = produced.get((edge.source_node_id, edge.source_port_id))
            if source is None:
                continue
            if source.quality is None or source.quality.ladder_rank < floor.ladder_rank:
                raise GraphValidationError(
                    f"{edge.target_node_id}.{target_port.port_id} requires {floor.value} but consumes "
                    f"{source.quality.value if source.quality else 'unqualified'} from "
                    f"{edge.source_node_id}.{edge.source_port_id}"
                )

    def materialization_of(self, node_id: str, port_id: str) -> MaterializationRecord | None:
        for record in self.materializations:
            if record.node_id == node_id and record.port_id == port_id:
                return record
        return None

    def materialization_of_first(self, node_id: str) -> MaterializationRecord | None:
        """The node's own committed output, used when a fingerprint needs its verdict."""

        return next((record for record in self.materializations if record.node_id == node_id), None)

    def inputs_of(self, node_id: str) -> tuple[tuple[GraphEdge, MaterializationRecord], ...]:
        produced = {record.key: record for record in self.materializations}
        found: list[tuple[GraphEdge, MaterializationRecord]] = []
        for edge in self.revision.definition.edges_into(node_id):
            if not edge.kind.dirties_material:
                continue
            record = produced.get((edge.source_node_id, edge.source_port_id))
            if record is not None:
                found.append((edge, record))
        return tuple(sorted(found, key=lambda item: (item[0].edge_id,)))

    def unresolved_inputs(self) -> tuple[GraphEdge, ...]:
        """Material edges whose producer has not committed anything yet."""

        produced = {record.key for record in self.materializations}
        return tuple(
            edge
            for edge in self.revision.definition.edges
            if edge.kind.dirties_material and (edge.source_node_id, edge.source_port_id) not in produced
        )

    def unmaterialized_nodes(self) -> tuple[str, ...]:
        index = self.revision.definition.node_index
        emitted = {record.node_id for record in self.materializations}
        return tuple(
            sorted(
                node.node_id
                for node in index.values()
                if node.role.emits_material and node.node_id not in emitted
            )
        )

    def select_variant(self, variant_set_id: str, option: str) -> "MaterializationGraph":
        """A variant selection is a new bound graph, never an in-place edit of this one."""

        pair = (
            require_identifier(variant_set_id, "variant_set_id"),
            require_identifier(option, "option"),
        )
        rest = tuple(item for item in self.variant_selection if item[0] != pair[0])
        return MaterializationGraph(
            revision=self.revision,
            materializations=self.materializations,
            variant_selection=tuple(sorted(rest + (pair,))),
            environment_fingerprint=self.environment_fingerprint,
            contract_version=self.contract_version,
        )
