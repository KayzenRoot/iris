"""Evidence-bound device topology and directional pairwise-path proofs."""

from __future__ import annotations

from dataclasses import dataclass

from .base import M07Record
from .enums import FreshnessClass, ObservationState, TopologyNodeKind, TopologyRelation
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError, HardwareGenomeLimitError, HardwareGenomeValidationError
from .evidence import DiscoveryObservation, ProbeEvidenceRef
from .limits import DEFAULT_LIMITS, HardwareGenomeLimits
from .subjects import HardwareSubjectRef, RuntimeSubjectRef
from .versions import require_identifier, require_nonnegative_int

__all__ = ["TopologyNode", "TopologyEdge", "TopologyLinkEvidence", "TopologyGraph", "PeerPathProof", "validate_topology_graph"]


@dataclass(frozen=True)
class TopologyNode(M07Record):
    node_id: str
    kind: TopologyNodeKind
    subject: HardwareSubjectRef | None = None
    runtime: RuntimeSubjectRef | None = None
    attributes_evidence_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        if type(self.kind) is not TopologyNodeKind:
            raise HardwareGenomeValidationError("topology node kind must use the closed M07 vocabulary")
        if self.subject is None and self.runtime is None:
            raise HardwareGenomeValidationError("topology nodes require an exact hardware or runtime subject")
        if self.subject is not None:
            object.__setattr__(self, "subject", HardwareSubjectRef.coerce(self.subject, "subject"))
        if self.runtime is not None:
            object.__setattr__(self, "runtime", RuntimeSubjectRef.coerce(self.runtime, "runtime"))
        if self.attributes_evidence_id is not None:
            object.__setattr__(self, "attributes_evidence_id", require_identifier(self.attributes_evidence_id, "attributes_evidence_id"))


@dataclass(frozen=True)
class TopologyEdge(M07Record):
    edge_id: str
    source_node_id: str
    target_node_id: str
    relation: TopologyRelation
    state: ObservationState
    evidence: ProbeEvidenceRef
    freshness: FreshnessClass
    reported_value: str | None = None

    def __post_init__(self) -> None:
        for field in ("edge_id", "source_node_id", "target_node_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if self.source_node_id == self.target_node_id:
            raise HardwareGenomeValidationError("topology edges cannot be self-relationships")
        if type(self.relation) is not TopologyRelation or type(self.state) is not ObservationState or type(self.freshness) is not FreshnessClass:
            raise HardwareGenomeValidationError("topology edge semantics must use closed M07 vocabularies")
        object.__setattr__(self, "evidence", ProbeEvidenceRef.coerce(self.evidence, "evidence"))
        if self.reported_value is not None:
            object.__setattr__(self, "reported_value", require_identifier(self.reported_value, "reported_value"))
        if self.state is ObservationState.OBSERVED and self.evidence.payload_bytes <= 0:
            raise HardwareGenomeIntegrityError("positive topology edges require evidence bytes")
        if self.relation is TopologyRelation.PEER_ACCESS_TO and self.evidence.related_subject_id is None:
            raise HardwareGenomeIntegrityError("peer access proof must bind both exact subject endpoints")


@dataclass(frozen=True)
class TopologyLinkEvidence(M07Record):
    """Reported PCIe capability and negotiated state only; measured bandwidth is M08 authority."""

    link_id: str
    subject_id: str
    runtime_id: str
    maximum_generation: int | None
    maximum_lane_width: int | None
    maximum_observation: DiscoveryObservation
    negotiated_generation: int | None
    negotiated_lane_width: int | None
    negotiated_observation: DiscoveryObservation

    def __post_init__(self) -> None:
        for field in ("link_id", "subject_id", "runtime_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        for field in ("maximum_generation", "maximum_lane_width", "negotiated_generation", "negotiated_lane_width"):
            value = getattr(self, field)
            if value is not None:
                value = require_nonnegative_int(value, field)
                if value == 0:
                    raise HardwareGenomeValidationError(f"{field} must be positive when reported")
                object.__setattr__(self, field, value)
        object.__setattr__(self, "maximum_observation", DiscoveryObservation.coerce(self.maximum_observation, "maximum_observation"))
        object.__setattr__(self, "negotiated_observation", DiscoveryObservation.coerce(self.negotiated_observation, "negotiated_observation"))
        self._validate_observation(self.maximum_observation, "maximum", self.maximum_generation, self.maximum_lane_width)
        self._validate_observation(self.negotiated_observation, "negotiated", self.negotiated_generation, self.negotiated_lane_width)

    def _validate_observation(self, observation: DiscoveryObservation, facet: str, generation: int | None, lanes: int | None) -> None:
        if observation.fact_key != f"topology.pcie.{self.link_id}.{facet}":
            raise HardwareGenomeIntegrityError(f"PCIe {facet} evidence has the wrong normalized fact key")
        if (observation.subject.subject_id if observation.subject else None, observation.runtime.runtime_id if observation.runtime else None) != (self.subject_id, self.runtime_id):
            raise HardwareGenomeIntegrityError(f"PCIe {facet} evidence must bind the exact link subject/runtime")
        if observation.state is ObservationState.OBSERVED:
            expected = {"generation": generation, "lane_width": lanes}
            if generation is None or lanes is None or not isinstance(observation.value, dict) and not hasattr(observation.value, "items") or any(observation.value.get(key) != value for key, value in expected.items()):
                raise HardwareGenomeIntegrityError(f"positive PCIe {facet} fields require exact reported evidence")
        elif generation is not None or lanes is not None:
            raise HardwareGenomeAdmissionError(f"non-positive PCIe {facet} state cannot carry reported limits")


@dataclass(frozen=True)
class TopologyGraph(M07Record):
    graph_id: str
    nodes: tuple[TopologyNode, ...]
    edges: tuple[TopologyEdge, ...]
    link_evidence: tuple[TopologyLinkEvidence, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "graph_id", require_identifier(self.graph_id, "graph_id"))
        nodes = tuple(TopologyNode.coerce(item, "nodes[]") for item in self.nodes)
        edges = tuple(TopologyEdge.coerce(item, "edges[]") for item in self.edges)
        links = tuple(TopologyLinkEvidence.coerce(item, "link_evidence[]") for item in self.link_evidence)
        if len({item.node_id for item in nodes}) != len(nodes) or len({item.edge_id for item in edges}) != len(edges):
            raise HardwareGenomeIntegrityError("topology graph node and edge ids must be unique")
        if len({item.link_id for item in links}) != len(links):
            raise HardwareGenomeIntegrityError("topology link evidence ids must be unique")
        object.__setattr__(self, "nodes", tuple(sorted(nodes, key=lambda item: item.node_id)))
        object.__setattr__(self, "edges", tuple(sorted(edges, key=lambda item: item.edge_id)))
        object.__setattr__(self, "link_evidence", tuple(sorted(links, key=lambda item: item.link_id)))


@dataclass(frozen=True)
class PeerPathProof(M07Record):
    proof_id: str
    source_subject_id: str
    target_subject_id: str
    runtime_id: str
    direction: str
    backend_id: str
    state: ObservationState
    evidence: ProbeEvidenceRef

    def __post_init__(self) -> None:
        for field in ("proof_id", "source_subject_id", "target_subject_id", "runtime_id", "direction", "backend_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if self.source_subject_id == self.target_subject_id:
            raise HardwareGenomeValidationError("pairwise path proof needs two distinct exact subjects")
        if type(self.state) is not ObservationState:
            raise HardwareGenomeValidationError("pairwise path state must be explicit")
        object.__setattr__(self, "evidence", ProbeEvidenceRef.coerce(self.evidence, "evidence"))
        if (self.evidence.subject_id, self.evidence.related_subject_id, self.evidence.runtime_id) != (self.source_subject_id, self.target_subject_id, self.runtime_id):
            raise HardwareGenomeIntegrityError("peer evidence must bind the exact ordered subject pair and runtime")


def validate_topology_graph(graph: TopologyGraph, *, limits: HardwareGenomeLimits = DEFAULT_LIMITS) -> None:
    graph = TopologyGraph.coerce(graph, "graph")
    limits.require("max_topology_nodes", len(graph.nodes))
    limits.require("max_topology_edges", len(graph.edges))
    limits.require("max_observations", len(graph.link_evidence))
    nodes = {item.node_id: item for item in graph.nodes}
    for edge in graph.edges:
        source = nodes.get(edge.source_node_id)
        target = nodes.get(edge.target_node_id)
        if source is None or target is None:
            raise HardwareGenomeIntegrityError("topology edge references a missing node")
        if source.subject is not None and edge.evidence.subject_id != source.subject.subject_id:
            raise HardwareGenomeIntegrityError("topology edge evidence is bound to a different source subject")
        if edge.relation is TopologyRelation.PEER_ACCESS_TO and target.subject is not None and edge.evidence.related_subject_id != target.subject.subject_id:
            raise HardwareGenomeIntegrityError("pairwise topology evidence is bound to a different target subject")
        if source.runtime is not None and edge.evidence.runtime_id != source.runtime.runtime_id:
            raise HardwareGenomeIntegrityError("topology evidence is bound to a different runtime scope")
    parent_edges: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for edge in graph.edges:
        if edge.relation is TopologyRelation.PARENT_OF:
            parent_edges[edge.source_node_id].append(edge.target_node_id)
    visited: set[str] = set()
    active: set[str] = set()
    for root in nodes:
        stack: list[tuple[str, int, bool]] = [(root, 1, False)]
        while stack:
            node_id, depth, leaving = stack.pop()
            if leaving:
                active.discard(node_id)
                visited.add(node_id)
                continue
            if node_id in active:
                raise HardwareGenomeIntegrityError("topology parent graph cannot contain cycles")
            if depth > limits.max_topology_depth:
                raise HardwareGenomeLimitError("topology nesting depth exceeds the configured bound")
            if node_id in visited:
                continue
            active.add(node_id)
            stack.append((node_id, depth, True))
            stack.extend((child, depth + 1, False) for child in parent_edges[node_id])
