"""Causal fingerprints, explicit dependency evidence and rebuildable indexes."""

from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import dataclass
from typing import Any

from .base import CanonicalRecord, canonical_bytes, exact_ref_key, require_exact_ref, require_sequence
from .enums import DependencyKind, FingerprintScope, ImpactState, IndexState, MaterialityState
from .errors import ProductionStateAdmissionError, ProductionStateIntegrityError, ProductionStateLimitError, ProductionStateValidationError
from .limits import DEFAULT_LIMITS, ProductionStateLimits
from .revisions import ContentDigest
from .versions import FINGERPRINT_VERSION, CORE_SCHEMA_VERSION, require_identifier, require_text, require_version

__all__ = [
    "FingerprintDimension",
    "OperationalDependencyObservation",
    "OperationalDependencyFingerprint",
    "FingerprintDelta",
    "ReverseDependencyEdge",
    "ReverseDependencyIndex",
    "ImpactPath",
    "ImpactConeReceipt",
    "DependencyDiscoveryReceipt",
    "SliceOmissionProof",
    "DependencySlice",
    "build_fingerprint",
    "build_slice_fingerprint",
    "compare_fingerprints",
    "build_reverse_index",
    "analyze_impact",
    "validate_impact_cone",
    "admit_dependency_discovery",
]


@dataclass(frozen=True)
class FingerprintDimension(CanonicalRecord):
    dependency_ref: Any
    facet: str
    materiality: MaterialityState
    content_digest: ContentDigest | None
    mandatory: bool = True
    policy_sensitive: bool = False
    identity_sensitive: bool = False
    toolchain_sensitive: bool = False

    def __post_init__(self) -> None:
        require_exact_ref(self.dependency_ref, "dependency_ref")
        require_text(self.facet, "facet", maximum=256)
        if not isinstance(self.materiality, MaterialityState):
            object.__setattr__(self, "materiality", MaterialityState(self.materiality))
        if self.content_digest is not None and type(self.content_digest) is not ContentDigest:
            raise ProductionStateValidationError("content_digest must be exact M06 digest evidence or None")
        for name in ("mandatory", "policy_sensitive", "identity_sensitive", "toolchain_sensitive"):
            if type(getattr(self, name)) is not bool:
                raise ProductionStateValidationError(f"{name} must be a boolean")
        if self.materiality is MaterialityState.MATERIAL and self.content_digest is None:
            raise ProductionStateAdmissionError("a material dependency dimension requires a content digest")

    @property
    def key(self) -> str:
        return f"{exact_ref_key(self.dependency_ref)}|{self.facet}"


@dataclass(frozen=True)
class OperationalDependencyObservation(CanonicalRecord):
    consumer_ref: Any
    dependency_ref: Any
    kind: DependencyKind
    materiality: MaterialityState
    facet: str
    evidence_ref: Any
    observed_at_ms: int
    hidden_material: bool = False
    schema_version: str = CORE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_exact_ref(self.consumer_ref, "consumer_ref")
        require_exact_ref(self.dependency_ref, "dependency_ref")
        require_exact_ref(self.evidence_ref, "evidence_ref")
        if not isinstance(self.kind, DependencyKind):
            object.__setattr__(self, "kind", DependencyKind(self.kind))
        if not isinstance(self.materiality, MaterialityState):
            object.__setattr__(self, "materiality", MaterialityState(self.materiality))
        require_text(self.facet, "facet", maximum=256)
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise ProductionStateValidationError("observed_at_ms must be a nonnegative exact integer")
        if type(self.hidden_material) is not bool:
            raise ProductionStateValidationError("hidden_material must be a boolean")
        if self.hidden_material and self.kind is not DependencyKind.HIDDEN_MATERIAL:
            raise ProductionStateIntegrityError("hidden material observations must use HIDDEN_MATERIAL kind")
        require_version(self.schema_version, "schema_version")


@dataclass(frozen=True)
class OperationalDependencyFingerprint(CanonicalRecord):
    algorithm: str
    digest: str
    fingerprint_version: str
    schema_version: str
    scope: FingerprintScope
    dimensions: tuple[FingerprintDimension, ...]

    def __post_init__(self) -> None:
        if self.algorithm != "sha256":
            raise ProductionStateValidationError("M06 causal fingerprints currently require sha256")
        if len(self.digest) != 64 or any(char not in "0123456789abcdef" for char in self.digest):
            raise ProductionStateValidationError("fingerprint digest must be 64 lowercase hexadecimal characters")
        require_version(self.fingerprint_version, "fingerprint_version")
        require_version(self.schema_version, "schema_version")
        if not isinstance(self.scope, FingerprintScope):
            object.__setattr__(self, "scope", FingerprintScope(self.scope))
        items = require_sequence(self.dimensions, "dimensions", maximum=DEFAULT_LIMITS.max_fingerprint_dimensions, item_type=FingerprintDimension)
        keys = [item.key for item in items]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ProductionStateValidationError("fingerprint dimensions must be unique and canonically sorted")
        object.__setattr__(self, "dimensions", items)


@dataclass(frozen=True)
class FingerprintDelta(CanonicalRecord):
    before: OperationalDependencyFingerprint
    after: OperationalDependencyFingerprint
    state: MaterialityState
    added: tuple[str, ...]
    removed: tuple[str, ...]
    changed: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if type(self.before) is not OperationalDependencyFingerprint or type(self.after) is not OperationalDependencyFingerprint:
            raise ProductionStateValidationError("fingerprint delta requires exact before and after fingerprints")
        if not isinstance(self.state, MaterialityState):
            object.__setattr__(self, "state", MaterialityState(self.state))
        for name in ("added", "removed", "changed"):
            values = require_sequence(getattr(self, name), name, maximum=DEFAULT_LIMITS.max_fingerprint_dimensions)
            if any(type(item) is not str for item in values) or values != tuple(sorted(set(values))):
                raise ProductionStateValidationError(f"{name} keys must be unique sorted strings")
            object.__setattr__(self, name, values)
        require_text(self.reason, "reason", maximum=1024)


@dataclass(frozen=True)
class SliceOmissionProof(CanonicalRecord):
    dimension_key: str
    state: MaterialityState
    evidence_ref: Any

    def __post_init__(self) -> None:
        require_text(self.dimension_key, "dimension_key", maximum=2048)
        if not isinstance(self.state, MaterialityState):
            object.__setattr__(self, "state", MaterialityState(self.state))
        require_exact_ref(self.evidence_ref, "evidence_ref")
        if self.state is not MaterialityState.NON_MATERIAL:
            raise ProductionStateAdmissionError("a dependency slice may omit only dimensions with positive NON_MATERIAL proof")


@dataclass(frozen=True)
class DependencySlice(CanonicalRecord):
    slice_id: str
    base_fingerprint: OperationalDependencyFingerprint
    included_dimension_keys: tuple[str, ...]
    omissions: tuple[SliceOmissionProof, ...]
    completeness_evidence_ref: Any
    slice_version: str = FINGERPRINT_VERSION

    def __post_init__(self) -> None:
        require_identifier(self.slice_id, "slice_id")
        if type(self.base_fingerprint) is not OperationalDependencyFingerprint:
            raise ProductionStateValidationError("dependency slice requires an exact base fingerprint")
        included = require_sequence(self.included_dimension_keys, "included_dimension_keys", maximum=DEFAULT_LIMITS.max_fingerprint_dimensions)
        if any(type(item) is not str for item in included) or included != tuple(sorted(set(included))):
            raise ProductionStateValidationError("included dimension keys must be unique sorted strings")
        available = {item.key for item in self.base_fingerprint.dimensions}
        if not set(included).issubset(available):
            raise ProductionStateIntegrityError("slice includes dimensions outside its exact base fingerprint")
        object.__setattr__(self, "included_dimension_keys", included)
        omissions = require_sequence(self.omissions, "omissions", maximum=DEFAULT_LIMITS.max_fingerprint_dimensions, item_type=SliceOmissionProof)
        omitted_keys = tuple(item.dimension_key for item in omissions)
        if omitted_keys != tuple(sorted(set(omitted_keys))) or not set(omitted_keys).issubset(available):
            raise ProductionStateValidationError("slice omission proofs must uniquely cover canonical base dimensions")
        if set(included) & set(omitted_keys) or set(included) | set(omitted_keys) != available:
            raise ProductionStateAdmissionError("slice must account for every base dimension as included or positively omitted")
        if any(self.base_fingerprint.dimensions[[item.key for item in self.base_fingerprint.dimensions].index(key)].mandatory for key in omitted_keys):
            raise ProductionStateAdmissionError("mandatory dimensions cannot be omitted from a causal slice")
        object.__setattr__(self, "omissions", omissions)
        require_exact_ref(self.completeness_evidence_ref, "completeness_evidence_ref")
        require_version(self.slice_version, "slice_version")


@dataclass(frozen=True)
class ReverseDependencyEdge(CanonicalRecord):
    dependency_ref: Any
    consumer_ref: Any
    materiality: MaterialityState
    hidden_material: bool = False

    def __post_init__(self) -> None:
        require_exact_ref(self.dependency_ref, "dependency_ref")
        require_exact_ref(self.consumer_ref, "consumer_ref")
        if not isinstance(self.materiality, MaterialityState):
            object.__setattr__(self, "materiality", MaterialityState(self.materiality))
        if type(self.hidden_material) is not bool:
            raise ProductionStateValidationError("hidden_material must be a boolean")


@dataclass(frozen=True)
class ReverseDependencyIndex(CanonicalRecord):
    index_id: str
    epoch: str
    state: IndexState
    edges: tuple[ReverseDependencyEdge, ...]
    source_fingerprint: str
    completeness_evidence_ref: Any | None = None
    schema_version: str = CORE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_identifier(self.index_id, "index_id")
        require_identifier(self.epoch, "epoch")
        if not isinstance(self.state, IndexState):
            object.__setattr__(self, "state", IndexState(self.state))
        edges = require_sequence(self.edges, "edges", maximum=DEFAULT_LIMITS.max_lineage_edges, item_type=ReverseDependencyEdge)
        keys = [(exact_ref_key(edge.dependency_ref), exact_ref_key(edge.consumer_ref)) for edge in edges]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ProductionStateValidationError("reverse index edges must be unique and canonically sorted")
        object.__setattr__(self, "edges", edges)
        if len(self.source_fingerprint) != 64 or any(char not in "0123456789abcdef" for char in self.source_fingerprint):
            raise ProductionStateValidationError("source_fingerprint must be a sha256 fingerprint")
        require_version(self.schema_version, "schema_version")
        if self.completeness_evidence_ref is not None:
            require_exact_ref(self.completeness_evidence_ref, "completeness_evidence_ref")
        if self.state is IndexState.COMPLETE_FRESH and self.completeness_evidence_ref is None:
            raise ProductionStateAdmissionError("complete fresh dependency index requires exact closure-completeness evidence")


@dataclass(frozen=True)
class ImpactPath(CanonicalRecord):
    refs: tuple[Any, ...]

    def __post_init__(self) -> None:
        values = require_sequence(self.refs, "refs", maximum=DEFAULT_LIMITS.max_lineage_nodes)
        if len(values) < 2:
            raise ProductionStateValidationError("impact path must contain at least one dependency edge")
        for index, value in enumerate(values):
            require_exact_ref(value, f"refs[{index}]")
        object.__setattr__(self, "refs", values)


@dataclass(frozen=True)
class ImpactConeReceipt(CanonicalRecord):
    changed_ref: Any
    state: ImpactState
    affected_refs: tuple[Any, ...]
    paths: tuple[ImpactPath, ...]
    unknown_frontier: tuple[str, ...]
    index_id: str
    index_epoch: str
    analyzed_at_ms: int
    reason: str
    node_limit: int
    source_index: ReverseDependencyIndex

    def __post_init__(self) -> None:
        require_exact_ref(self.changed_ref, "changed_ref")
        if not isinstance(self.state, ImpactState):
            object.__setattr__(self, "state", ImpactState(self.state))
        affected = require_sequence(self.affected_refs, "affected_refs", maximum=DEFAULT_LIMITS.max_lineage_nodes)
        for index, item in enumerate(affected):
            require_exact_ref(item, f"affected_refs[{index}]")
        object.__setattr__(self, "affected_refs", affected)
        paths = require_sequence(self.paths, "paths", maximum=DEFAULT_LIMITS.max_lineage_edges, item_type=ImpactPath)
        object.__setattr__(self, "paths", paths)
        frontier = require_sequence(self.unknown_frontier, "unknown_frontier", maximum=DEFAULT_LIMITS.max_dependencies)
        if any(type(item) is not str for item in frontier):
            raise ProductionStateValidationError("unknown frontier entries must be strings")
        object.__setattr__(self, "unknown_frontier", frontier)
        require_identifier(self.index_id, "index_id")
        require_identifier(self.index_epoch, "index_epoch")
        if type(self.source_index) is not ReverseDependencyIndex:
            raise ProductionStateValidationError("impact receipt must embed its exact reverse dependency index")
        if (self.index_id, self.index_epoch) != (self.source_index.index_id, self.source_index.epoch):
            raise ProductionStateIntegrityError("impact receipt index bindings do not match its embedded index")
        if type(self.analyzed_at_ms) is not int or self.analyzed_at_ms < 0:
            raise ProductionStateValidationError("analyzed_at_ms must be a nonnegative exact integer")
        if type(self.node_limit) is not int or self.node_limit <= 0 or self.node_limit > DEFAULT_LIMITS.max_lineage_nodes:
            raise ProductionStateValidationError("node_limit must be a positive value within configured bounds")
        require_text(self.reason, "reason", maximum=2048)
        if self.state is ImpactState.UNAFFECTED_PROVEN and (self.source_index.state is not IndexState.COMPLETE_FRESH or self.source_index.completeness_evidence_ref is None):
            raise ProductionStateAdmissionError("unaffected proof requires a complete fresh indexed closure with completeness evidence")
        if self.state is ImpactState.UNAFFECTED_PROVEN and (self.affected_refs or self.paths or self.unknown_frontier):
            raise ProductionStateIntegrityError("unaffected proof cannot include impacts or an unknown frontier")


@dataclass(frozen=True)
class DependencyDiscoveryReceipt(CanonicalRecord):
    discovery_id: str
    consumer_ref: Any
    previous_receipt_id: str | None
    observed_dependencies: tuple[OperationalDependencyObservation, ...]
    resulting_fingerprint: str
    evidence_ref: Any
    recorded_at_ms: int

    def __post_init__(self) -> None:
        require_identifier(self.discovery_id, "discovery_id")
        require_exact_ref(self.consumer_ref, "consumer_ref")
        if self.previous_receipt_id is not None:
            require_identifier(self.previous_receipt_id, "previous_receipt_id")
            if self.previous_receipt_id == self.discovery_id:
                raise ProductionStateIntegrityError("dependency discovery history cannot point to itself")
        observations = require_sequence(self.observed_dependencies, "observed_dependencies", maximum=DEFAULT_LIMITS.max_dependencies, item_type=OperationalDependencyObservation)
        if any(item.consumer_ref != self.consumer_ref for item in observations):
            raise ProductionStateIntegrityError("discovery receipt cannot mix consumer identities")
        object.__setattr__(self, "observed_dependencies", observations)
        if len(self.resulting_fingerprint) != 64 or any(char not in "0123456789abcdef" for char in self.resulting_fingerprint):
            raise ProductionStateValidationError("resulting_fingerprint must be a sha256 fingerprint")
        require_exact_ref(self.evidence_ref, "evidence_ref")
        if type(self.recorded_at_ms) is not int or self.recorded_at_ms < 0:
            raise ProductionStateValidationError("recorded_at_ms must be a nonnegative exact integer")


def build_fingerprint(
    dimensions: tuple[FingerprintDimension, ...],
    scope: FingerprintScope,
    *,
    schema_version: str = CORE_SCHEMA_VERSION,
    limits: ProductionStateLimits = DEFAULT_LIMITS,
) -> OperationalDependencyFingerprint:
    items = require_sequence(dimensions, "dimensions", maximum=limits.max_fingerprint_dimensions, item_type=FingerprintDimension)
    if any(item.materiality is MaterialityState.UNKNOWN and item.mandatory for item in items):
        raise ProductionStateAdmissionError("unknown mandatory materiality cannot enter an admitted causal fingerprint")
    if scope is FingerprintScope.SELECTED_SLICE:
        selected = items
    else:
        selected = tuple(
            item for item in items
            if item.materiality is MaterialityState.MATERIAL
            or (scope is FingerprintScope.POLICY_SENSITIVE and item.policy_sensitive)
            or (scope is FingerprintScope.IDENTITY_SENSITIVE and item.identity_sensitive)
            or (scope is FingerprintScope.TOOLCHAIN_SENSITIVE and item.toolchain_sensitive)
        )
    if scope in {FingerprintScope.FULL_CAUSAL, FingerprintScope.RECONSTRUCTION}:
        selected = tuple(item for item in items if item.materiality is not MaterialityState.NON_MATERIAL)
    if len(selected) > limits.max_fingerprint_dimensions:
        raise ProductionStateLimitError("selected fingerprint dimensions exceed configured limits")
    canonical = tuple(sorted(selected, key=lambda item: item.key))
    payload = {"scope": scope.value, "version": FINGERPRINT_VERSION, "schema": schema_version, "dimensions": canonical}
    digest = hashlib.sha256(canonical_bytes(payload, limits=limits)).hexdigest()
    return OperationalDependencyFingerprint("sha256", digest, FINGERPRINT_VERSION, schema_version, scope, canonical)


def build_slice_fingerprint(
    dependency_slice: DependencySlice,
    *,
    schema_version: str = CORE_SCHEMA_VERSION,
    limits: ProductionStateLimits = DEFAULT_LIMITS,
) -> OperationalDependencyFingerprint:
    if type(dependency_slice) is not DependencySlice:
        raise ProductionStateValidationError("dependency_slice must be an exact immutable DependencySlice")
    included = set(dependency_slice.included_dimension_keys)
    dimensions = tuple(item for item in dependency_slice.base_fingerprint.dimensions if item.key in included)
    return build_fingerprint(dimensions, FingerprintScope.SELECTED_SLICE, schema_version=schema_version, limits=limits)


def compare_fingerprints(before: OperationalDependencyFingerprint, after: OperationalDependencyFingerprint) -> FingerprintDelta:
    if type(before) is not OperationalDependencyFingerprint or type(after) is not OperationalDependencyFingerprint:
        raise ProductionStateValidationError("comparison requires exact operational fingerprints")
    if before.scope is not after.scope or before.schema_version != after.schema_version or before.fingerprint_version != after.fingerprint_version:
        return FingerprintDelta(before, after, MaterialityState.UNKNOWN, (), (), (), "fingerprint scope or schema version changed")
    left = {item.key: item for item in before.dimensions}
    right = {item.key: item for item in after.dimensions}
    added = tuple(sorted(set(right) - set(left)))
    removed = tuple(sorted(set(left) - set(right)))
    changed = tuple(sorted(key for key in set(left) & set(right) if left[key] != right[key]))
    if any((left.get(key) or right.get(key)).mandatory and (left.get(key) or right.get(key)).materiality is MaterialityState.UNKNOWN for key in set(added) | set(removed) | set(changed)):
        state, reason = MaterialityState.UNKNOWN, "mandatory dependency materiality is unknown"
    elif added or removed or changed:
        state, reason = MaterialityState.MATERIAL, "causal dependency dimensions changed"
    else:
        state, reason = MaterialityState.NON_MATERIAL, "causal dimensions are equal within the same explicit scope"
    return FingerprintDelta(before, after, state, added, removed, changed, reason)


def build_reverse_index(
    index_id: str,
    epoch: str,
    observations: tuple[OperationalDependencyObservation, ...],
    *,
    state: IndexState = IndexState.UNKNOWN,
    completeness_evidence_ref: Any | None = None,
    limits: ProductionStateLimits = DEFAULT_LIMITS,
) -> ReverseDependencyIndex:
    records = require_sequence(observations, "observations", maximum=limits.max_dependencies, item_type=OperationalDependencyObservation)
    grouped: dict[tuple[str, str], list[OperationalDependencyObservation]] = {}
    for item in records:
        grouped.setdefault((exact_ref_key(item.dependency_ref), exact_ref_key(item.consumer_ref)), []).append(item)
    edges_list: list[ReverseDependencyEdge] = []
    for group in grouped.values():
        first = group[0]
        materiality = (
            MaterialityState.MATERIAL if any(item.materiality is MaterialityState.MATERIAL for item in group)
            else MaterialityState.UNKNOWN if any(item.materiality is MaterialityState.UNKNOWN for item in group)
            else MaterialityState.NON_MATERIAL
        )
        edges_list.append(ReverseDependencyEdge(first.dependency_ref, first.consumer_ref, materiality, any(item.hidden_material for item in group)))
    edges = tuple(sorted(edges_list, key=lambda edge: (exact_ref_key(edge.dependency_ref), exact_ref_key(edge.consumer_ref))))
    source = hashlib.sha256(canonical_bytes(records, limits=limits)).hexdigest()
    return ReverseDependencyIndex(index_id, epoch, state, edges, source, completeness_evidence_ref)


def analyze_impact(
    changed_ref: Any,
    index: ReverseDependencyIndex,
    *,
    analyzed_at_ms: int,
    max_nodes: int = 20_000,
) -> ImpactConeReceipt:
    require_exact_ref(changed_ref, "changed_ref")
    if type(index) is not ReverseDependencyIndex:
        raise ProductionStateValidationError("index must be an exact ReverseDependencyIndex")
    if max_nodes <= 0 or max_nodes > DEFAULT_LIMITS.max_lineage_nodes:
        raise ProductionStateValidationError("max_nodes must be within configured lineage bounds")
    affected: list[Any] = []
    paths: list[ImpactPath] = []
    unknown: list[str] = []
    if index.state is IndexState.STALE:
        state, reason = ImpactState.BLOCKED_BY_STALE_EVIDENCE, "stale reverse dependency index cannot prove impact or absence"
    elif index.state in {IndexState.CORRUPT, IndexState.UNKNOWN}:
        state, reason = ImpactState.UNKNOWN, "corrupt or unknown reverse index cannot establish dependency closure"
    elif index.state is IndexState.PARTIAL:
        state, reason = ImpactState.UNKNOWN, "partial reverse index cannot prove absence of consumers"
    else:
        adjacency: dict[str, list[ReverseDependencyEdge]] = {}
        for edge in index.edges:
            adjacency.setdefault(exact_ref_key(edge.dependency_ref), []).append(edge)
        root = exact_ref_key(changed_ref)
        pending = deque([(changed_ref, (changed_ref,))])
        seen = {root}
        limit_exceeded = False
        while pending:
            current, path = pending.popleft()
            for edge in adjacency.get(exact_ref_key(current), ()):
                child_key = exact_ref_key(edge.consumer_ref)
                if edge.hidden_material or edge.materiality is MaterialityState.UNKNOWN:
                    unknown.append(child_key)
                    continue
                if edge.materiality is MaterialityState.NON_MATERIAL:
                    continue
                affected.append(edge.consumer_ref)
                paths.append(ImpactPath(path + (edge.consumer_ref,)))
                if child_key not in seen:
                    if len(seen) >= max_nodes:
                        unknown.append(child_key)
                        limit_exceeded = True
                        break
                    seen.add(child_key)
                    pending.append((edge.consumer_ref, path + (edge.consumer_ref,)))
            if limit_exceeded:
                break
        if limit_exceeded:
            state, reason = ImpactState.UNKNOWN, "impact frontier exceeded the configured node limit"
        else:
            if unknown:
                state, reason = ImpactState.UNKNOWN, "hidden or unknown-material dependencies remain on the impact frontier"
            elif affected:
                state, reason = ImpactState.AFFECTED, "complete fresh index provides direct or transitive causal paths"
            else:
                state, reason = ImpactState.UNAFFECTED_PROVEN, "complete fresh index proves no downstream consumers"
        if state is ImpactState.UNAFFECTED_PROVEN:
            affected, paths, unknown = [], [], []
    return ImpactConeReceipt(
        changed_ref,
        state,
        tuple({exact_ref_key(item): item for item in affected}.values()),
        tuple(paths),
        tuple(sorted(set(unknown))),
        index.index_id,
        index.epoch,
        analyzed_at_ms,
        reason,
        max_nodes,
        index,
    )


def validate_impact_cone(receipt: ImpactConeReceipt, index: ReverseDependencyIndex | None = None) -> ImpactConeReceipt:
    if type(receipt) is not ImpactConeReceipt:
        raise ProductionStateValidationError("receipt must be an exact immutable impact cone")
    source = receipt.source_index if index is None else index
    if type(source) is not ReverseDependencyIndex or source != receipt.source_index:
        raise ProductionStateIntegrityError("impact cone validation must use its exact embedded source index")
    expected = analyze_impact(receipt.changed_ref, source, analyzed_at_ms=receipt.analyzed_at_ms, max_nodes=receipt.node_limit)
    if (receipt.state, receipt.affected_refs, receipt.paths, receipt.unknown_frontier, receipt.reason) != (
        expected.state, expected.affected_refs, expected.paths, expected.unknown_frontier, expected.reason
    ):
        raise ProductionStateIntegrityError("impact cone claim does not match recomputation over its exact source index")
    return receipt


def admit_dependency_discovery(receipt: DependencyDiscoveryReceipt) -> DependencyDiscoveryReceipt:
    if type(receipt) is not DependencyDiscoveryReceipt:
        raise ProductionStateValidationError("dependency discovery must be an exact immutable receipt")
    if any(item.hidden_material for item in receipt.observed_dependencies):
        raise ProductionStateAdmissionError("hidden material discovery is retained as evidence and blocks reuse pending explicit admission")
    return receipt
