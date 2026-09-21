"""Later-module extension boundaries: provider-neutral ports and the opaque refs that cross them.

§6 of the frozen contract names the boundaries a later module may implement, and invariant 28 says
implementing one never means redefining what M02 means. This file draws that line in types rather than
in prose: every port speaks only in kernel value objects and opaque references, so a DCC, a node-graph
runtime, a cloud, a database or a media-provider type has nowhere to arrive. Nothing here runs anything.
§10 of the
Work Order forbids implementing the later providers, and this module holds to that — it states the
shape a provider must satisfy and the refusals it triggers when it does not.

Four laws make the boundaries real instead of decorative.

*A provider answers only at the boundary it signed up for.* ``ProviderDescriptor`` records which
boundaries and capabilities a component admits, and ``require_admitted`` is the single gate every call
site passes through. A dependency observer that starts issuing repair offers is a different component,
not the same one having an idea.

*A handle belongs to the provider that minted it.* ``ProviderHandle`` is deliberately not an
``ExternalRef``: the kernel cannot open a provider's temporary object and neither can anyone else, so
handing one provider's handle to another is refused rather than left undefined.

*A provider cannot widen the question it was asked.* Invariant 5 forbids silently introducing
undeclared material dependencies, so an ``ExecutionPlan`` and a ``DependencyObservation`` are checked
against the revision they claim to describe, and a rights ruling that answers about references nobody
submitted is refused for the same reason.

*The plan is not the graph.* Invariant 7 keeps a Definition Graph distinct from a provider's execution
plan: compilation is a derived, digestible answer about one revision, and it carries no authority to
change what the revision declared.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Protocol, Sequence, runtime_checkable

from iris_quality.contracts import FidelityContract

from .base import Labeled, Record, of
from .branching import IdentityAnchorPolicy
from .build import RepairFrontier, RepairTarget
from .errors import PortContractError, SchemaValidationError
from .graph import (
    DependencyFacet,
    GraphRevision,
    MaterializationGraph,
    MaterializationRecord,
    SemanticTypeRef,
    SideEffectClass,
)
from .identity import EntityKind, ExternalRef, require_id
from .limits import (
    MAX_COMPILED_STEPS,
    MAX_CLOSURE_REFS,
    MAX_CONTEXT_SOURCES,
    MAX_FACETS,
    MAX_OBSERVED_DEPENDENCIES,
    MAX_PORT_BOUNDARIES,
    MAX_PORT_CAPABILITIES,
    MAX_PORTS,
)
from .release import RemoteState
from .reuse import ContextSource
from .snapshots import Snapshot
from .versions import (
    CONTRACT_VERSION,
    ComponentVersion,
    require_bounded,
    require_component_version,
    require_digest,
    require_identifier,
    require_millis,
    require_reference,
    require_supported_version,
    require_text,
)

__all__ = [
    "PortBoundary",
    "ProviderDescriptor",
    "ProviderHandle",
    "ExecutionCapability",
    "SemanticTypeDeclaration",
    "PolicyResolution",
    "IdentityAnchorRuling",
    "DependencyObservation",
    "CompilationRequest",
    "CompiledStep",
    "ExecutionPlan",
    "IngestedMaterial",
    "RepairOffer",
    "RepairPlan",
    "RightsRuling",
    "ContextFingerprintAnswer",
    "DeliveryStatus",
    "SemanticTypeRegistry",
    "PolicySource",
    "IdentityAnchorSource",
    "CapabilitySource",
    "ProviderCompiler",
    "DependencyObserver",
    "MaterializationIngestor",
    "RepairProvider",
    "RightsProvenanceGate",
    "ContextFingerprintSource",
    "DeliveryProvider",
    "require_admitted",
    "require_declared_dependencies",
    "describe_boundaries",
    "port_reference",
]


class PortBoundary(Labeled):
    """§6's list of places a later module may attach. One name per admitted interface."""

    SEMANTIC_TYPE_REGISTRY = "SEMANTIC_TYPE_REGISTRY"
    POLICY_SOURCE = "POLICY_SOURCE"
    IDENTITY_ANCHOR_SOURCE = "IDENTITY_ANCHOR_SOURCE"
    CAPABILITY_SOURCE = "CAPABILITY_SOURCE"
    PROVIDER_COMPILER = "PROVIDER_COMPILER"
    DEPENDENCY_OBSERVER = "DEPENDENCY_OBSERVER"
    MATERIALIZATION_INGESTOR = "MATERIALIZATION_INGESTOR"
    REPAIR_PROVIDER = "REPAIR_PROVIDER"
    ARTIFACT_STORE = "ARTIFACT_STORE"
    SNAPSHOT_STORE = "SNAPSHOT_STORE"
    RECEIPT_STORE = "RECEIPT_STORE"
    RIGHTS_PROVENANCE_GATE = "RIGHTS_PROVENANCE_GATE"
    CONTEXT_FINGERPRINT_SOURCE = "CONTEXT_FINGERPRINT_SOURCE"
    DELIVERY_PROVIDER = "DELIVERY_PROVIDER"

    @property
    def speaks_for(self) -> str:
        """What a provider at this boundary is allowed to state, and nothing beyond it."""

        return _BOUNDARY_CLAIMS[self]


_BOUNDARY_CLAIMS: Mapping[PortBoundary, str] = MappingProxyType(
    {
        PortBoundary.SEMANTIC_TYPE_REGISTRY: "which semantic types exist and how they convert",
        PortBoundary.POLICY_SOURCE: "which fidelity contract a policy reference resolves to",
        PortBoundary.IDENTITY_ANCHOR_SOURCE: "whether a candidate may carry a protected identity",
        PortBoundary.CAPABILITY_SOURCE: "which work a worker is permitted to run",
        PortBoundary.PROVIDER_COMPILER: "how one graph revision is executed by one provider",
        PortBoundary.DEPENDENCY_OBSERVER: "what a run actually depended on",
        PortBoundary.MATERIALIZATION_INGESTOR: "what bytes a run produced",
        PortBoundary.REPAIR_PROVIDER: "which bounded slice can bring a node back",
        PortBoundary.ARTIFACT_STORE: "which artifacts it holds and with what digest",
        PortBoundary.SNAPSHOT_STORE: "which snapshots it holds",
        PortBoundary.RECEIPT_STORE: "which receipts it holds",
        PortBoundary.RIGHTS_PROVENANCE_GATE: "whether a reference may be used",
        PortBoundary.CONTEXT_FINGERPRINT_SOURCE: "what a compiled context hashed to",
        PortBoundary.DELIVERY_PROVIDER: "what a destination is known to hold",
    }
)


@dataclass(frozen=True)
class ProviderDescriptor(Record):
    """What one component admits about itself: who it is, and which claims it is willing to make.

    The descriptor is the reason a port cannot quietly grow. A provider that answers at a boundary it
    never declared is refused by name, so wiring a new capability into a pipeline is a versioned change
    to this record rather than a change to whatever the code happens to call.
    """

    provider_id: str
    component: Any
    boundaries: tuple[PortBoundary, ...] = ()
    capabilities: tuple[str, ...] = ()
    admitted_kinds: tuple[EntityKind, ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {"component": of(ComponentVersion)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider_id", require_identifier(self.provider_id, "provider_id"))
        object.__setattr__(self, "component", require_component_version(self.component, "component"))
        declared = require_bounded(self.boundaries, "boundaries", maximum=MAX_PORT_BOUNDARIES, kind="boundary")
        resolved = tuple(sorted({PortBoundary.parse(item, "boundaries[]") for item in declared}, key=lambda item: item.value))
        object.__setattr__(self, "boundaries", resolved)
        abilities = require_bounded(self.capabilities, "capabilities", maximum=MAX_PORT_CAPABILITIES, kind="capability")
        object.__setattr__(
            self, "capabilities", tuple(sorted({require_identifier(item, "capabilities[]") for item in abilities}))
        )
        kinds = require_bounded(self.admitted_kinds, "admitted_kinds", maximum=MAX_PORT_CAPABILITIES, kind="entity kind")
        object.__setattr__(
            self,
            "admitted_kinds",
            tuple(sorted({EntityKind.parse(item, "admitted_kinds[]") for item in kinds}, key=lambda item: item.value)),
        )
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    def admits(self, boundary: Any) -> bool:
        return PortBoundary.parse(boundary, "boundary") in self.boundaries

    def supports(self, capability: Any) -> bool:
        return require_identifier(capability, "capability") in self.capabilities

    def may_resolve(self, reference: Any) -> bool:
        """Whether this provider may speak about a kind at all, checked before it answers."""

        wanted = ExternalRef.coerce(reference, "reference")
        return wanted.kind in self.admitted_kinds


@dataclass(frozen=True)
class ProviderHandle(Record):
    """A provider-scoped opaque reference: usable to ask the same provider again, nothing else.

    The kernel deliberately cannot dereference one. That is the point of the type — a DCC temp object,
    a provider-side cache slot or a staged upload URL is real state somewhere, and pretending it is an
    ``ExternalRef`` would let a second provider be asked to honour it.
    """

    boundary: PortBoundary
    provider_id: str
    opaque_reference: str
    content_digest: Any = None
    issued_at_ms: int = 0
    expires_at_ms: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "boundary", PortBoundary.parse(self.boundary, "boundary"))
        object.__setattr__(self, "provider_id", require_identifier(self.provider_id, "provider_id"))
        object.__setattr__(self, "opaque_reference", require_reference(self.opaque_reference, "opaque_reference"))
        if self.content_digest is not None:
            object.__setattr__(self, "content_digest", require_digest(self.content_digest, "content_digest"))
        object.__setattr__(self, "issued_at_ms", require_millis(self.issued_at_ms, "issued_at_ms"))
        object.__setattr__(self, "expires_at_ms", require_millis(self.expires_at_ms, "expires_at_ms"))
        if self.expires_at_ms and self.issued_at_ms and self.expires_at_ms <= self.issued_at_ms:
            raise PortContractError(f"handle {self.opaque_reference} expires before it was issued")

    @property
    def is_sealed(self) -> bool:
        """Whether the handle has settled into content the kernel can name by digest."""

        return self.content_digest is not None

    def presented_to(self, provider_id: Any, *, boundary: Any = None, now_ms: int = 0) -> "ProviderHandle":
        """Reject a handle arriving somewhere it was not minted, or after its own lifetime."""

        wanted = require_identifier(provider_id, "provider_id")
        if wanted != self.provider_id:
            raise PortContractError(
                f"handle {self.opaque_reference} was minted by {self.provider_id} and is being presented to "
                f"{wanted}; a provider-scoped reference is not a locator another provider can open"
            )
        if boundary is not None:
            parsed = PortBoundary.parse(boundary, "boundary")
            if parsed is not self.boundary:
                raise PortContractError(
                    f"{self.opaque_reference} is a {self.boundary.value} handle being used at "
                    f"{parsed.value}, whose claim is: {parsed.speaks_for}"
                )
        if self.expires_at_ms and now_ms > self.expires_at_ms:
            raise PortContractError(
                f"handle {self.opaque_reference} expired at {self.expires_at_ms} and is being used at {now_ms}"
            )
        return self

    @property
    def text(self) -> str:
        return f"{self.provider_id}:{self.boundary.value}:{self.opaque_reference}"


@dataclass(frozen=True)
class ExecutionCapability(Record):
    """What a worker may be given to run, stated as permission and never as a host handle."""

    capability_id: str
    provider_id: str
    tool: Any
    environment_ref: Any
    permitted_node_ids: tuple[str, ...] = ()
    side_effects: tuple[SideEffectClass, ...] = ()
    expires_at_ms: int = 0

    NESTED = {
        "tool": of(ComponentVersion),
        "environment_ref": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "capability_id", require_id(self.capability_id, "capability_id"))
        object.__setattr__(self, "provider_id", require_identifier(self.provider_id, "provider_id"))
        object.__setattr__(self, "tool", require_component_version(self.tool, "tool"))
        if not isinstance(self.environment_ref, ExternalRef):
            raise SchemaValidationError("environment_ref must be an ExternalRef naming the execution environment")
        nodes = require_bounded(self.permitted_node_ids, "permitted_node_ids", maximum=MAX_CLOSURE_REFS, kind="node id")
        object.__setattr__(
            self,
            "permitted_node_ids",
            tuple(sorted({require_identifier(item, "permitted_node_ids[]") for item in nodes})),
        )
        effects = require_bounded(self.side_effects, "side_effects", maximum=MAX_PORT_CAPABILITIES, kind="side-effect class")
        object.__setattr__(
            self,
            "side_effects",
            tuple(sorted({SideEffectClass.parse(item, "side_effects[]") for item in effects}, key=lambda item: item.value)),
        )
        object.__setattr__(self, "expires_at_ms", require_millis(self.expires_at_ms, "expires_at_ms"))

    @property
    def is_unbounded(self) -> bool:
        """Whether the grant names no node at all — which grants nothing, not everything.

        Reading an unspecified allowlist as a wildcard is the classic adapter bug, and here it would mean
        a capability record written in a hurry authorises every node in the graph.
        """

        return not self.permitted_node_ids

    def may_run(self, node_id: str) -> bool:
        return not self.is_unbounded and require_identifier(node_id, "node_id") in self.permitted_node_ids

    def permits_side_effect(self, side_effect: Any) -> bool:
        return SideEffectClass.parse(side_effect, "side_effect") in self.side_effects

    def is_live(self, now_ms: int = 0) -> bool:
        return not self.expires_at_ms or now_ms <= self.expires_at_ms


@dataclass(frozen=True)
class SemanticTypeDeclaration(Record):
    """What the type registry says one semantic type is, without naming a media implementation."""

    type_ref: SemanticTypeRef
    field_names: tuple[str, ...] = ()
    converts_to: tuple[str, ...] = ()
    registered_by: Any = None

    NESTED = {"type_ref": of(SemanticTypeRef)}

    def __post_init__(self) -> None:
        if not isinstance(self.type_ref, SemanticTypeRef):
            raise SchemaValidationError("type_ref must be a SemanticTypeRef")
        names = require_bounded(self.field_names, "field_names", maximum=MAX_PORT_CAPABILITIES, kind="field name")
        object.__setattr__(
            self, "field_names", tuple(sorted({require_identifier(item, "field_names[]") for item in names}))
        )
        targets = require_bounded(self.converts_to, "converts_to", maximum=MAX_PORT_CAPABILITIES, kind="type id")
        object.__setattr__(
            self, "converts_to", tuple(sorted({require_identifier(item, "converts_to[]") for item in targets}))
        )
        if self.type_ref.type_id in self.converts_to:
            raise PortContractError(
                f"{self.type_ref.text} declares a conversion into itself; a type that needs no conversion is "
                "already the target, and one that claims it needs it is describing a different type"
            )
        if self.registered_by is not None:
            object.__setattr__(self, "registered_by", require_component_version(self.registered_by, "registered_by"))

    @property
    def schema_ref(self) -> ExternalRef:
        return self.type_ref.schema_ref

    def admits_conversion_to(self, other: Any) -> bool:
        wanted = other if isinstance(other, SemanticTypeRef) else SemanticTypeRef.coerce(other, "other")
        return wanted.type_id in self.converts_to


def _fidelity_contract(value: Any, path: str) -> FidelityContract:
    """Decode a stored contract back through M01, so a resolution survives a round trip.

    Without this the record is write-only: its payload holds the contract's own bytes, and reading them
    back would trip the refusal below. Decoding through ``FidelityContract`` keeps that law intact — the
    only contract type a resolution can hold is still M01's.
    """

    if isinstance(value, FidelityContract):
        return value
    if not isinstance(value, Mapping):
        raise SchemaValidationError(
            f"{path} must be a FidelityContract or its payload, got {type(value).__name__}"
        )
    return FidelityContract.from_payload(value)


@dataclass(frozen=True)
class PolicyResolution(Record):
    """A policy reference answered with M01's own contract type.

    The resolution carries ``iris_quality``'s record rather than an M02 copy, because §5 of the frozen
    contract forbids M02 reimplementing the judging engine — and a re-typed fidelity contract is the
    first step down that road.
    """

    policy_ref: Any
    contract: Any
    resolved_at_ms: int = 0
    source: Any = None

    NESTED = {"policy_ref": of(ExternalRef), "source": of(ComponentVersion), "contract": _fidelity_contract}

    def __post_init__(self) -> None:
        if not isinstance(self.policy_ref, ExternalRef):
            raise SchemaValidationError("policy_ref must be an ExternalRef naming the policy")
        if not isinstance(self.contract, FidelityContract):
            raise PortContractError(
                "a policy resolution carries the M01 FidelityContract itself; re-describing it in M02 types "
                "would put a second fidelity vocabulary in the kernel"
            )
        object.__setattr__(self, "resolved_at_ms", require_millis(self.resolved_at_ms, "resolved_at_ms"))
        if self.source is not None:
            object.__setattr__(self, "source", require_component_version(self.source, "source"))


@dataclass(frozen=True)
class IdentityAnchorRuling(Record):
    """Whether a candidate may carry a protected identity, and the evidence that says so.

    A provider may explain a ruling; it may not overrule the anchor the graph carries. Drift without a
    migration receipt is refused here exactly as ``IdentityAnchorPolicy.authorize`` refuses it in the
    branch kernel, so no adapter gets a looser path by asking through a port.
    """

    anchor: IdentityAnchorPolicy
    subject: Any
    candidate_digest: Any = None
    permitted: bool = False
    migration_receipts: tuple[str, ...] = ()
    reason_code: str = "anchor-checked"
    evidence_refs: tuple[ExternalRef, ...] = ()
    ruled_at_ms: int = 0

    NESTED = {
        "anchor": of(IdentityAnchorPolicy),
        "subject": of(ExternalRef),
        "evidence_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        if not isinstance(self.anchor, IdentityAnchorPolicy):
            raise SchemaValidationError("anchor must be the IdentityAnchorPolicy being ruled on")
        if not isinstance(self.subject, ExternalRef):
            raise SchemaValidationError("subject must be an ExternalRef to the candidate")
        if self.candidate_digest is not None:
            object.__setattr__(self, "candidate_digest", require_digest(self.candidate_digest, "candidate_digest"))
        if not isinstance(self.permitted, bool):
            raise SchemaValidationError("permitted must be a boolean")
        receipts = require_bounded(self.migration_receipts, "migration_receipts", maximum=MAX_PORT_CAPABILITIES, kind="id")
        object.__setattr__(self, "migration_receipts", tuple(require_id(item, "migration_receipts[]") for item in receipts))
        object.__setattr__(self, "reason_code", require_identifier(self.reason_code, "reason_code"))
        refs = require_bounded(self.evidence_refs, "evidence_refs", maximum=MAX_PORT_CAPABILITIES, kind="reference")
        object.__setattr__(self, "evidence_refs", tuple(ExternalRef.coerce(item, "evidence_refs[]") for item in refs))
        object.__setattr__(self, "ruled_at_ms", require_millis(self.ruled_at_ms, "ruled_at_ms"))
        if self.permitted and not self.anchor.authorize(self.candidate_digest, self.migration_receipts):
            raise PortContractError(
                f"{self.subject.text} drifts the anchor {self.anchor.anchor_id} with no migration receipt; a "
                "provider cannot grant past the policy the graph itself carries"
            )
        if not self.permitted and not self.drifts:
            raise PortContractError(
                f"{self.subject.text} is refused as an anchor change while it carries the baseline digest "
                f"{self.anchor.baseline_digest[:12]}; a ruling that blocks what never moved is a different gate"
            )

    @property
    def drifts(self) -> bool:
        return self.anchor.drifts(self.candidate_digest)


@dataclass(frozen=True)
class DependencyObservation(Record):
    """What a run actually depended on, as reported back to the kernel.

    Reporting is allowed; expanding is not. ``require_declared_dependencies`` refuses an observation
    naming material the revision never declared, which is invariant 5's whole content: an adapter may
    tell us a dependency existed, and may not quietly make one.
    """

    revision_id: str
    node_id: str
    observed: tuple[ExternalRef, ...] = ()
    observed_at_ms: int = 0
    reported_by: Any = None

    NESTED = {"observed": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "revision_id", require_id(self.revision_id, "revision_id"))
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        collected = require_bounded(self.observed, "observed", maximum=MAX_OBSERVED_DEPENDENCIES, kind="reference")
        unique = {ExternalRef.coerce(item, "observed[]") for item in collected}
        object.__setattr__(self, "observed", tuple(sorted(unique, key=lambda item: item.text)))
        object.__setattr__(self, "observed_at_ms", require_millis(self.observed_at_ms, "observed_at_ms"))
        if self.reported_by is not None:
            object.__setattr__(self, "reported_by", require_component_version(self.reported_by, "reported_by"))

    def undeclared_against(self, revision: Any) -> tuple[ExternalRef, ...]:
        """Observed references the revision's declared external inputs never admitted."""

        wanted = _revision(revision)
        admitted = {item.text for item in wanted.definition.declared_external_inputs}
        return tuple(item for item in self.observed if item.text not in admitted)


def _revision(value: Any) -> GraphRevision:
    if isinstance(value, GraphRevision):
        return value
    if isinstance(value, MaterializationGraph):
        return value.revision
    if isinstance(value, Snapshot):
        return value.closure.graph.revision
    raise SchemaValidationError(
        "a provider answers about a GraphRevision, a MaterializationGraph or a Snapshot, got "
        f"{type(value).__name__}"
    )


def require_declared_dependencies(revision: Any, observation: Any) -> DependencyObservation:
    """Refuse an observation that introduces material the revision did not declare (§invariant 5)."""

    bound = _revision(revision)
    wanted = DependencyObservation.coerce(observation, "observation")
    if wanted.revision_id != bound.revision_id:
        raise PortContractError(
            f"the observation of {wanted.node_id} reports on revision {wanted.revision_id} while the graph bound "
            f"is {bound.revision_id}; an observation of a different revision is evidence about something else"
        )
    extra = wanted.undeclared_against(bound)
    if extra:
        raise PortContractError(
            f"{wanted.node_id} observed dependencies the revision never declared: "
            f"{', '.join(item.text for item in extra)}; an adapter may report what existed, not add what runs"
        )
    return wanted


@dataclass(frozen=True)
class CompilationRequest(Record):
    """The exact slice of one revision a compiler was asked to plan for.

    The admitted inputs are part of the request rather than an afterthought: the plan is checked
    against them, so a provider cannot answer with a wider graph than it was handed.
    """

    revision_id: str
    node_ids: tuple[str, ...]
    capability: ExecutionCapability
    admitted_inputs: tuple[ExternalRef, ...] = ()
    requested_at_ms: int = 0

    NESTED = {"capability": of(ExecutionCapability), "admitted_inputs": of(ExternalRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "revision_id", require_id(self.revision_id, "revision_id"))
        nodes = require_bounded(self.node_ids, "node_ids", maximum=MAX_COMPILED_STEPS, kind="node id")
        resolved = tuple(sorted({require_identifier(item, "node_ids[]") for item in nodes}))
        if not resolved:
            raise PortContractError("a compilation request for no node would be a plan for nothing")
        object.__setattr__(self, "node_ids", resolved)
        object.__setattr__(self, "capability", ExecutionCapability.coerce(self.capability, "capability"))
        inputs = require_bounded(self.admitted_inputs, "admitted_inputs", maximum=MAX_OBSERVED_DEPENDENCIES, kind="reference")
        unique = {ExternalRef.coerce(item, "admitted_inputs[]") for item in inputs}
        object.__setattr__(self, "admitted_inputs", tuple(sorted(unique, key=lambda item: item.text)))
        object.__setattr__(self, "requested_at_ms", require_millis(self.requested_at_ms, "requested_at_ms"))

    @property
    def reference(self) -> ExternalRef:
        return ExternalRef(kind=EntityKind.GRAPH, reference=self.digest()[:32])


def port_reference(node_id: Any, port_id: Any) -> ExternalRef:
    """The kernel's name for one output port, so a plan and an ingestion cannot disagree.

    A compiler promises material by port, and an ingestor delivers material by port. Without one
    shared spelling the two boundaries would each invent a reference grammar, and the mismatch would
    surface as a node that "produced nothing" while its bytes sit in a store.
    """

    wanted = require_identifier(node_id, "node_id")
    port = require_identifier(port_id, "port_id")
    return ExternalRef(kind=EntityKind.PORT, reference=f"{wanted}:{port}")


@dataclass(frozen=True)
class CompiledStep(Record):
    """One node's execution intent at a provider: an opaque program, declared ports, material in/out."""

    node_id: str
    tool: Any
    instruction: ProviderHandle
    inputs: tuple[ExternalRef, ...] = ()
    outputs: tuple[ExternalRef, ...] = ()
    depends_on: tuple[str, ...] = ()
    side_effect: SideEffectClass = SideEffectClass.NO_SIDE_EFFECT

    NESTED = {
        "tool": of(ComponentVersion),
        "instruction": of(ProviderHandle),
        "inputs": of(ExternalRef),
        "outputs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "tool", require_component_version(self.tool, "tool"))
        object.__setattr__(self, "instruction", ProviderHandle.coerce(self.instruction, "instruction"))
        inputs = require_bounded(self.inputs, "inputs", maximum=MAX_OBSERVED_DEPENDENCIES, kind="reference")
        unique = {ExternalRef.coerce(item, "inputs[]") for item in inputs}
        object.__setattr__(self, "inputs", tuple(sorted(unique, key=lambda item: item.text)))
        produced = require_bounded(self.outputs, "outputs", maximum=MAX_PORTS, kind="port reference")
        resolved: list[ExternalRef] = []
        for item in produced:
            ref = ExternalRef.coerce(item, "outputs[]")
            if ref.kind is not EntityKind.PORT:
                raise PortContractError(
                    f"{self.node_id} claims to produce {ref.text}; a compiled step delivers material into one of "
                    "its own ports and a store row is not a port"
                )
            if not ref.reference.startswith(f"{self.node_id}:"):
                raise PortContractError(
                    f"{self.node_id} claims to produce {ref.text}, which names another node's port; a step "
                    "cannot write a promise it does not own"
                )
            resolved.append(ref)
        object.__setattr__(self, "outputs", tuple(sorted(resolved, key=lambda item: item.text)))
        deps = require_bounded(self.depends_on, "depends_on", maximum=MAX_CLOSURE_REFS, kind="node id")
        object.__setattr__(
            self, "depends_on", tuple(sorted({require_identifier(item, "depends_on[]") for item in deps}))
        )
        if self.node_id in self.depends_on:
            raise PortContractError(f"{self.node_id} declares itself a dependency of its own compiled step")
        object.__setattr__(self, "side_effect", SideEffectClass.parse(self.side_effect, "side_effect"))

    def produces(self, reference: Any) -> bool:
        wanted = ExternalRef.coerce(reference, "reference")
        return any(item.text == wanted.text for item in self.outputs)


@dataclass(frozen=True)
class ExecutionPlan(Record):
    """A provider's answer to one compilation request — derived, versioned, and authoritative over nothing.

    §invariant 7 keeps this distinct from the Definition Graph: the plan says how one provider runs a
    revision, and every check here exists to keep it from also saying what the revision *is*. A step for
    a node nobody requested, an input the request never admitted, a tool the capability does not name
    and a handle from another provider are each a widening of the question, and each is refused.
    """

    request: CompilationRequest
    provider_id: str
    component: Any
    steps: tuple[CompiledStep, ...] = ()
    contract_version: str = CONTRACT_VERSION

    NESTED = {"request": of(CompilationRequest), "component": of(ComponentVersion), "steps": of(CompiledStep)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "request", CompilationRequest.coerce(self.request, "request"))
        object.__setattr__(self, "provider_id", require_identifier(self.provider_id, "provider_id"))
        object.__setattr__(self, "component", require_component_version(self.component, "component"))
        collected = require_bounded(self.steps, "steps", maximum=MAX_COMPILED_STEPS, kind="step")
        resolved = tuple(CompiledStep.coerce(item, "steps[]") for item in collected)
        object.__setattr__(self, "steps", resolved)
        planned = tuple(item.node_id for item in resolved)
        known = set(planned)
        extra = sorted({item for item in planned if item not in self.request.node_ids})
        if extra:
            raise PortContractError(
                f"{self.provider_id} compiled steps for {', '.join(extra)}, which no request named; an execution "
                "plan that adds work is not a compilation of this revision"
            )
        missing = sorted(set(self.request.node_ids) - set(planned))
        if missing:
            raise PortContractError(
                f"{self.provider_id} left {', '.join(missing)} out of a plan that was asked to cover them; a "
                "partial plan presented as a compilation would let the build run nodes it never planned"
            )
        if len(set(planned)) != len(planned):
            raise PortContractError(f"{self.provider_id} compiled one node twice; a revision has one step per node")
        unknown = sorted({item for step in resolved for item in step.depends_on if item not in known})
        if unknown:
            raise PortContractError(
                f"{self.provider_id}'s plan waits on {', '.join(unknown)}, which it does not contain and the "
                "request did not name; a step waiting on work nobody planned can never run"
            )
        self._refuse_cycles()
        admitted = {item.text for item in self.request.admitted_inputs}
        by_node = {item.node_id: item for item in resolved}
        for step in resolved:
            upstream = {output.text for name in step.depends_on for output in by_node[name].outputs}
            undeclared = sorted(
                {item.text for item in step.inputs if item.text not in admitted and item.text not in upstream}
            )
            if undeclared:
                raise PortContractError(
                    f"{self.provider_id}'s plan reads {', '.join(undeclared)} at {step.node_id}, which the request "
                    "never admitted and no step it depends on produces; invariant 5 is exactly this: a provider "
                    "may not add a material dependency by compiling it in"
                )
            if not self.request.capability.may_run(step.node_id):
                raise PortContractError(
                    f"{step.node_id} was compiled onto {self.provider_id}, whose capability does not permit that "
                    "node; a plan may schedule granted work and nothing else"
                )
            if step.tool != self.request.capability.tool:
                raise PortContractError(
                    f"{step.node_id} compiles on {step.tool.identifier} {step.tool.version} while the granted "
                    f"tool is {self.request.capability.tool.identifier} "
                    f"{self.request.capability.tool.version}; the tool identity is part of the grant"
                )
            if (
                step.side_effect is not SideEffectClass.NO_SIDE_EFFECT
                and step.side_effect not in self.request.capability.side_effects
            ):
                granted = ", ".join(item.value for item in self.request.capability.side_effects) or "nothing"
                raise PortContractError(
                    f"{step.node_id} performs {step.side_effect.value} while the grant covers {granted}; "
                    "a plan cannot earn permissions by compiling"
                )
            step.instruction.presented_to(self.provider_id, boundary=PortBoundary.PROVIDER_COMPILER)
        require_supported_version("contract", self.contract_version, {CONTRACT_VERSION})

    def _refuse_cycles(self) -> None:
        """A plan that waits on itself cannot run, and saying so here beats a hang at execution.

        The Definition Graph already refuses material cycles; this is the provider's own ordering, which
        the graph never sees, so it needs checking where it is stated.
        """

        by_node = {item.node_id: item for item in self.steps}
        state: dict[str, int] = {}

        def visiting(node_id: str, trail: tuple[str, ...]) -> None:
            if state.get(node_id) == 2:
                return
            if state.get(node_id) == 1:
                raise PortContractError(
                    f"{self.provider_id}'s plan depends on itself: "
                    f"{' -> '.join(trail + (node_id,))}; no ordering of these steps can run"
                )
            state[node_id] = 1
            for name in by_node[node_id].depends_on:
                visiting(name, trail + (node_id,))
            state[node_id] = 2

        for node_id in sorted(by_node):
            visiting(node_id, ())

    @property
    def plan_digest(self) -> str:
        return self.digest()

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(item.node_id for item in self.steps)

    @property
    def side_effects(self) -> tuple[SideEffectClass, ...]:
        return tuple(sorted({item.side_effect for item in self.steps}, key=lambda item: item.value))

    def execution_order(self) -> tuple[str, ...]:
        """The steps in a dependency order this plan can actually be run in."""

        by_node = {item.node_id: item for item in self.steps}
        done: set[str] = set()
        found: list[str] = []

        def emit(node_id: str) -> None:
            if node_id in done:
                return
            for name in by_node[node_id].depends_on:
                emit(name)
            done.add(node_id)
            found.append(node_id)

        for node_id in sorted(by_node):
            emit(node_id)
        return tuple(found)

    def step_for(self, node_id: str) -> CompiledStep:
        wanted = require_identifier(node_id, "node_id")
        for item in self.steps:
            if item.node_id == wanted:
                return item
        raise PortContractError(f"{self.provider_id}'s plan has no step for {wanted}")

    def claims_output(self, reference: Any) -> bool:
        """Whether this plan is the one that promised the material an ingestor is handing over."""

        wanted = ExternalRef.coerce(reference, "reference")
        return any(step.produces(wanted) for step in self.steps)


@dataclass(frozen=True)
class IngestedMaterial(Record):
    """What a run produced, in the only vocabulary the graph kernel already speaks.

    ``as_materialization`` hands the same record the bound graph is built from, so ingesting cannot
    invent a second answer about what a node emitted: the digest, the attempt and the revision
    reference are the ones the graph's laws already check.
    """

    node_id: str
    port_id: str
    revision_ref: Any
    content_digest: str
    handle: ProviderHandle
    provider_id: str
    producer_attempt_id: Any = None
    quality_class: Any = None
    decision_ref: Any = None
    seed: Any = None
    environment_ref: Any = None
    tool_refs: tuple[ExternalRef, ...] = ()
    produced_at_ms: int = 0

    NESTED = {
        "revision_ref": of(ExternalRef),
        "handle": of(ProviderHandle),
        "decision_ref": of(ExternalRef),
        "environment_ref": of(ExternalRef),
        "tool_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", require_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "port_id", require_identifier(self.port_id, "port_id"))
        object.__setattr__(self, "provider_id", require_identifier(self.provider_id, "provider_id"))
        if not isinstance(self.revision_ref, ExternalRef):
            raise SchemaValidationError("revision_ref must be an ExternalRef")
        object.__setattr__(self, "content_digest", require_digest(self.content_digest, "content_digest"))
        object.__setattr__(self, "handle", ProviderHandle.coerce(self.handle, "handle"))
        self.handle.presented_to(self.provider_id, boundary=PortBoundary.MATERIALIZATION_INGESTOR)
        if self.handle.content_digest is not None and self.handle.content_digest != self.content_digest:
            raise PortContractError(
                f"{self.node_id}.{self.port_id} ingests {self.content_digest[:12]} while its handle is sealed at "
                f"{self.handle.content_digest[:12]}; the bytes and the promise about them have to be one claim"
            )
        if self.producer_attempt_id is not None:
            object.__setattr__(self, "producer_attempt_id", require_id(self.producer_attempt_id, "producer_attempt_id"))
        tools = require_bounded(self.tool_refs, "tool_refs", maximum=MAX_PORT_CAPABILITIES, kind="reference")
        object.__setattr__(self, "tool_refs", tuple(ExternalRef.coerce(item, "tool_refs[]") for item in tools))
        object.__setattr__(self, "produced_at_ms", require_millis(self.produced_at_ms, "produced_at_ms"))

    @property
    def port_ref(self) -> ExternalRef:
        return port_reference(self.node_id, self.port_id)

    def as_materialization(self) -> MaterializationRecord:
        return MaterializationRecord(
            node_id=self.node_id,
            port_id=self.port_id,
            revision_ref=self.revision_ref,
            content_digest=self.content_digest,
            producer_attempt_id=self.producer_attempt_id,
            quality_class=self.quality_class,
            decision_ref=self.decision_ref,
            seed=self.seed,
            environment_ref=self.environment_ref,
            tool_refs=self.tool_refs,
            produced_at_ms=self.produced_at_ms,
        )


@dataclass(frozen=True)
class RepairOffer(Record):
    """A bounded way to bring one node back, offered by whoever can offer it."""

    target: RepairTarget
    handle: ProviderHandle
    provider_id: str
    rewrites_side_effect: SideEffectClass = SideEffectClass.NO_SIDE_EFFECT
    facets: tuple[DependencyFacet, ...] = ()
    offered_at_ms: int = 0

    NESTED = {"target": of(RepairTarget), "handle": of(ProviderHandle)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "target", RepairTarget.coerce(self.target, "target"))
        object.__setattr__(self, "handle", ProviderHandle.coerce(self.handle, "handle"))
        object.__setattr__(self, "provider_id", require_identifier(self.provider_id, "provider_id"))
        self.handle.presented_to(self.provider_id, boundary=PortBoundary.REPAIR_PROVIDER)
        collected = require_bounded(self.facets, "facets", maximum=MAX_FACETS, kind="facet")
        resolved = tuple(sorted({DependencyFacet.parse(item, "facets[]") for item in collected}, key=lambda item: item.value))
        object.__setattr__(self, "facets", resolved)
        outside = sorted({item.value for item in resolved} - {item.value for item in self.target.facets})
        if outside:
            raise PortContractError(
                f"the offer for {self.target.node_id} repairs {', '.join(outside)}, which its own repair target "
                "does not list; an offer may not widen what it claims to bring back"
            )
        object.__setattr__(
            self, "rewrites_side_effect", SideEffectClass.parse(self.rewrites_side_effect, "rewrites_side_effect")
        )
        object.__setattr__(self, "offered_at_ms", require_millis(self.offered_at_ms, "offered_at_ms"))

    @property
    def node_id(self) -> str:
        return self.target.node_id

    def answers(self, frontier: RepairFrontier) -> bool:
        wanted = RepairFrontier.coerce(frontier, "frontier")
        found = wanted.target_for(self.node_id)
        return found is not None and found == self.target


@dataclass(frozen=True)
class RepairPlan(Record):
    """Which repair offers together cover a repair frontier, and which part of it they demonstrably miss."""

    frontier_graph_id: str
    offers: tuple[RepairOffer, ...] = ()
    uncovered: tuple[str, ...] = ()
    planned_at_ms: int = 0

    NESTED = {"offers": of(RepairOffer)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "frontier_graph_id", require_identifier(self.frontier_graph_id, "frontier_graph_id"))
        collected = require_bounded(self.offers, "offers", maximum=MAX_COMPILED_STEPS, kind="offer")
        resolved = tuple(RepairOffer.coerce(item, "offers[]") for item in collected)
        index: dict[str, list[RepairOffer]] = {}
        for item in resolved:
            index.setdefault(item.node_id, []).append(item)
        for node_id, group in index.items():
            if len(group) > 1:
                raise PortContractError(
                    f"{node_id} has {len(group)} repair offers; two providers offering to bring one node back is "
                    "an arbitration question, not a plan"
                )
        object.__setattr__(self, "offers", tuple(sorted(resolved, key=lambda item: item.node_id)))
        nodes = require_bounded(self.uncovered, "uncovered", maximum=MAX_CLOSURE_REFS, kind="node id")
        object.__setattr__(self, "uncovered", tuple(sorted({require_identifier(item, "uncovered[]") for item in nodes})))
        overlap = {item.node_id for item in resolved} & set(self.uncovered)
        if overlap:
            raise PortContractError(
                f"{', '.join(sorted(overlap))} is both offered and listed uncovered; a plan cannot be two "
                "answers about one node"
            )
        object.__setattr__(self, "planned_at_ms", require_millis(self.planned_at_ms, "planned_at_ms"))

    @property
    def covered(self) -> tuple[str, ...]:
        return tuple(item.node_id for item in self.offers)

    def checked_against(self, frontier: Any) -> "RepairPlan":
        """Refuse a plan that leaves part of the frontier stale while presenting itself as the answer."""

        wanted = RepairFrontier.coerce(frontier, "frontier")
        if wanted.graph_id != self.frontier_graph_id:
            raise PortContractError(
                f"this plan is for graph {self.frontier_graph_id} and cannot answer a frontier of "
                f"{wanted.graph_id}"
            )
        left = (set(wanted.node_ids) - set(self.covered)) | set(wanted.uncovered)
        if left != set(self.uncovered):
            raise PortContractError(
                f"the frontier needs {', '.join(sorted(left)) or 'nothing'} left alone and this plan says "
                f"{', '.join(sorted(self.uncovered)) or 'nothing'}; a repair that quietly leaves part of the node "
                "stale is worse than no repair"
            )
        for offer in self.offers:
            if not offer.answers(wanted):
                raise PortContractError(
                    f"the offer for {offer.node_id} targets {offer.target.slice.text}, which is not the frontier's "
                    f"target for that node; the slice has to be the one the build kernel named"
                )
        return self


@dataclass(frozen=True)
class RightsRuling(Record):
    """One answer per reference a caller actually submitted — never a wider grant than the question.

    A gate that returns ``permitted`` for a reference nobody asked about has just changed the policy
    surface by talking, so the partition is checked: every submitted reference gets exactly one answer,
    and an unanswered reference is not silently permitted.
    """

    asked: tuple[ExternalRef, ...] = ()
    permitted: tuple[ExternalRef, ...] = ()
    blocked: tuple[ExternalRef, ...] = ()
    unknown: tuple[ExternalRef, ...] = ()
    decided_by: Any = None
    evidence_refs: tuple[ExternalRef, ...] = ()
    ruled_at_ms: int = 0

    NESTED = {
        "asked": of(ExternalRef),
        "permitted": of(ExternalRef),
        "blocked": of(ExternalRef),
        "unknown": of(ExternalRef),
        "evidence_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        def frozen(value: Any, name: str) -> tuple[ExternalRef, ...]:
            collected = require_bounded(value, name, maximum=MAX_CLOSURE_REFS, kind="reference")
            unique = {ExternalRef.coerce(item, f"{name}[]") for item in collected}
            return tuple(sorted(unique, key=lambda item: item.text))

        for name in ("asked", "permitted", "blocked", "unknown"):
            object.__setattr__(self, name, frozen(getattr(self, name), name))
        answered = {item.text for item in self.permitted} | {item.text for item in self.blocked} | {item.text for item in self.unknown}
        submitted = {item.text for item in self.asked}
        smuggled = sorted(answered - submitted)
        if smuggled:
            raise PortContractError(
                f"the ruling answers {', '.join(smuggled)}, which nobody submitted; a gate grants what it was "
                "asked about and stays silent about the rest"
            )
        silent = sorted(submitted - answered)
        if silent:
            raise PortContractError(
                f"the ruling leaves {', '.join(silent)} unanswered; an unasked question is not a permission, and "
                "a promotion cannot treat one as a pass"
            )
        overlap = sorted(
            ({item.text for item in self.permitted} & ({item.text for item in self.blocked} | {item.text for item in self.unknown}))
            | ({item.text for item in self.blocked} & {item.text for item in self.unknown})
        )
        if overlap:
            raise PortContractError(f"the ruling gives {', '.join(overlap)} two answers to one question")
        if self.decided_by is not None:
            object.__setattr__(self, "decided_by", ExternalRef.coerce(self.decided_by, "decided_by"))
        refs = require_bounded(self.evidence_refs, "evidence_refs", maximum=MAX_PORT_CAPABILITIES, kind="reference")
        object.__setattr__(self, "evidence_refs", tuple(ExternalRef.coerce(item, "evidence_refs[]") for item in refs))
        object.__setattr__(self, "ruled_at_ms", require_millis(self.ruled_at_ms, "ruled_at_ms"))

    @property
    def is_clear(self) -> bool:
        return not self.blocked and not self.unknown

    @property
    def needs_reconciliation(self) -> bool:
        """§24's UNKNOWN-Blocks rule in gate form: an unanswered right stops the move."""

        return bool(self.unknown)

    def answer_for(self, reference: Any) -> str:
        wanted = ExternalRef.coerce(reference, "reference")
        for name in ("permitted", "blocked", "unknown"):
            if any(item == wanted for item in getattr(self, name)):
                return name
        raise PortContractError(f"{wanted.text} was never submitted, so this ruling says nothing about it")


@dataclass(frozen=True)
class ContextFingerprintAnswer(Record):
    """What a runtime says a compiled context hashed to, and how far that answer may be trusted.

    The ordered sources are part of the claim: prefix reuse is only safe when the sequence is literally
    the same, so an answer about a different source list cannot be this one's fingerprint. And runtime
    state is not durable evidence unless a provider-specific qualification says so and names itself —
    which is the spec's rule about KV state, written as a type.
    """

    sources: tuple[ContextSource, ...]
    fingerprint: str
    compiler: Any
    model: Any = None
    durable: bool = False
    qualification_ref: Any = None
    cacheable_ms: int = 0
    observed_at_ms: int = 0

    NESTED = {
        "sources": of(ContextSource),
        "compiler": of(ComponentVersion),
        "model": of(ComponentVersion),
        "qualification_ref": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        collected = require_bounded(self.sources, "sources", maximum=MAX_CONTEXT_SOURCES, kind="source")
        object.__setattr__(self, "sources", tuple(ContextSource.coerce(item, "sources[]") for item in collected))
        object.__setattr__(self, "fingerprint", require_digest(self.fingerprint, "fingerprint"))
        object.__setattr__(self, "compiler", require_component_version(self.compiler, "compiler"))
        if self.model is not None:
            object.__setattr__(self, "model", require_component_version(self.model, "model"))
        if not isinstance(self.durable, bool):
            raise SchemaValidationError("durable must be a boolean")
        if self.durable and self.qualification_ref is None:
            raise PortContractError(
                "a runtime context fingerprint is not durable canonical evidence; §24 allows it only under a "
                "provider-specific qualification, and none is named"
            )
        if self.qualification_ref is not None:
            object.__setattr__(
                self, "qualification_ref", ExternalRef.coerce(self.qualification_ref, "qualification_ref")
            )
        object.__setattr__(self, "cacheable_ms", require_millis(self.cacheable_ms, "cacheable_ms"))
        object.__setattr__(self, "observed_at_ms", require_millis(self.observed_at_ms, "observed_at_ms"))

    @property
    def source_texts(self) -> tuple[str, ...]:
        return tuple(item.ref.text for item in self.sources)

    def answers(self, sources: Any) -> bool:
        """Whether this is the answer to the context that was handed over.

        Compared as a sequence, not a set: two runs over the same sources in a different order produce
        different prefixes, and an answer about one is not an answer about the other.
        """

        collected = sources if isinstance(sources, (list, tuple)) else getattr(sources, "sources", None)
        if collected is None:
            raise SchemaValidationError(
                "a context fingerprint answer is checked against a sequence of sources or a record carrying them"
            )
        submitted = tuple(ContextSource.coerce(item, "sources[]").ref.text for item in collected)
        return submitted == self.source_texts

    def matches(self, fingerprint: Any) -> bool:
        """Whether this answer is the fingerprint the build is holding.

        Duck-typed on ``fingerprint`` rather than imported from ``analysis``: a causal fingerprint and a
        raw digest say the same thing here, and pulling the impact cone into the port layer would make an
        extension boundary depend on a kernel subsystem it has no business naming.
        """

        wanted = getattr(fingerprint, "fingerprint", fingerprint)
        return require_digest(wanted, "fingerprint") == self.fingerprint


@dataclass(frozen=True)
class DeliveryStatus(Record):
    """What a destination is known to hold, with the proof that says so.

    ``LANDED`` is a claim about the outside world and therefore owes evidence; ``STILL_UNKNOWN`` is the
    honest answer when there is none, and the release kernel's ambiguity fence is what acts on it.
    """

    destination: Any
    package_ref: Any
    state: Any
    evidence_refs: tuple[ExternalRef, ...] = ()
    idempotency_key: Any = None
    observed_at_ms: int = 0

    NESTED = {
        "destination": of(ExternalRef),
        "package_ref": of(ExternalRef),
        "evidence_refs": of(ExternalRef),
    }

    def __post_init__(self) -> None:
        object.__setattr__(self, "destination", ExternalRef.coerce(self.destination, "destination"))
        if self.destination.kind is not EntityKind.DESTINATION:
            raise PortContractError(
                f"{self.destination.text} is a {self.destination.kind.value}, not a destination; a delivery "
                "answer about something else is evidence about nowhere"
            )
        object.__setattr__(self, "package_ref", ExternalRef.coerce(self.package_ref, "package_ref"))
        object.__setattr__(self, "state", RemoteState.parse(self.state, "state"))
        refs = require_bounded(self.evidence_refs, "evidence_refs", maximum=MAX_PORT_CAPABILITIES, kind="reference")
        object.__setattr__(self, "evidence_refs", tuple(ExternalRef.coerce(item, "evidence_refs[]") for item in refs))
        if self.state is RemoteState.LANDED and not self.evidence_refs:
            raise PortContractError(
                f"{self.destination.text} is reported LANDED with no evidence; a destination cannot be certified "
                "by the provider's own assurance"
            )
        if self.idempotency_key is not None:
            object.__setattr__(self, "idempotency_key", require_text(self.idempotency_key, "idempotency_key", maximum=128))
        object.__setattr__(self, "observed_at_ms", require_millis(self.observed_at_ms, "observed_at_ms"))

    @property
    def is_resolved(self) -> bool:
        return self.state is not RemoteState.STILL_UNKNOWN


@runtime_checkable
class ExtensionPort(Protocol):
    """Every later-module provider answers to this: one descriptor, one admitted set of claims."""

    @property
    def descriptor(self) -> ProviderDescriptor: ...


@runtime_checkable
class SemanticTypeRegistry(ExtensionPort, Protocol):
    """Resolves a ``SemanticTypeRef`` to what the registry says that type is."""

    def resolve(self, type_ref: SemanticTypeRef) -> SemanticTypeDeclaration | None: ...


@runtime_checkable
class PolicySource(ExtensionPort, Protocol):
    """Resolves a policy reference into the M01 fidelity contract it names."""

    def resolve(self, policy_ref: ExternalRef) -> PolicyResolution | None: ...


@runtime_checkable
class IdentityAnchorSource(ExtensionPort, Protocol):
    """Rules on whether a candidate may carry a protected identity."""

    def rule(
        self,
        anchor: IdentityAnchorPolicy,
        subject: ExternalRef,
        *,
        candidate_digest: Any = None,
        migration_receipts: Sequence[str] = (),
        now_ms: int = 0,
    ) -> IdentityAnchorRuling: ...


@runtime_checkable
class CapabilitySource(ExtensionPort, Protocol):
    """Answers which work a worker may run, without naming a host, queue or vendor runtime."""

    def capability_for(self, provider_id: str, *, now_ms: int = 0) -> ExecutionCapability | None: ...


@runtime_checkable
class ProviderCompiler(ExtensionPort, Protocol):
    """Turns one graph revision into one provider's execution plan. The plan binds nothing."""

    def compile(self, request: CompilationRequest, revision: GraphRevision) -> ExecutionPlan: ...


@runtime_checkable
class DependencyObserver(ExtensionPort, Protocol):
    """Reports what a run depended on. Reporting is not the same as adding (§invariant 5)."""

    def observe(self, revision: GraphRevision, node_id: str, *, handle: ProviderHandle | None = None) -> DependencyObservation: ...


@runtime_checkable
class MaterializationIngestor(ExtensionPort, Protocol):
    """Brings produced bytes into the graph's own materialization vocabulary."""

    def ingest(self, node_id: str, port_id: str, *, handle: ProviderHandle) -> IngestedMaterial: ...


@runtime_checkable
class RepairProvider(ExtensionPort, Protocol):
    """Offers bounded ways back for the nodes a repair frontier names."""

    def offers_for(self, frontier: RepairFrontier, *, now_ms: int = 0) -> RepairPlan: ...


@runtime_checkable
class RightsProvenanceGate(ExtensionPort, Protocol):
    """Answers, one per submitted reference, whether the work may be used."""

    def rule_on(self, references: Iterable[ExternalRef], *, now_ms: int = 0) -> RightsRuling: ...


@runtime_checkable
class ContextFingerprintSource(ExtensionPort, Protocol):
    """Answers what a compiled context hashed to, and how far that answer may be trusted."""

    def fingerprint(self, sources: Sequence[ContextSource], *, compiler: ComponentVersion) -> ContextFingerprintAnswer: ...


@runtime_checkable
class DeliveryProvider(ExtensionPort, Protocol):
    """States what a destination holds. Reconciliation and the ambiguity fence stay in ``release``."""

    def status(
        self,
        *,
        destination: ExternalRef,
        package_ref: ExternalRef,
        idempotency_key: Any = None,
        now_ms: int = 0,
    ) -> DeliveryStatus: ...


def require_admitted(provider: Any, boundary: Any, *, capability: Any = None) -> ProviderDescriptor:
    """The one gate every port call passes through: this component, at this boundary, saying this.

    A provider that does not describe itself is refused rather than trusted by default, because the
    descriptor is what makes "later modules may implement these ports, and may not redefine M02" a
    checkable statement instead of a hope.
    """

    parsed = PortBoundary.parse(boundary, "boundary")
    if provider is None:
        raise PortContractError(f"no provider was wired for {parsed.value}, which speaks for {_BOUNDARY_CLAIMS[parsed]}")
    described = getattr(provider, "descriptor", None)
    if described is None:
        raise PortContractError(
            f"{type(provider).__name__} carries no ProviderDescriptor, so nothing can be checked about what it "
            f"admits at {parsed.value}"
        )
    descriptor = ProviderDescriptor.coerce(described, "descriptor")
    if not descriptor.admits(parsed):
        raise PortContractError(
            f"{descriptor.provider_id} is wired to {parsed.value}, which speaks for "
            f"{parsed.speaks_for}, but its descriptor admits "
            f"{', '.join(item.value for item in descriptor.boundaries) or 'nothing'}; §invariant 28: a provider "
            "may implement a boundary, not redefine which boundary it is"
        )
    if capability is not None and not descriptor.supports(capability):
        raise PortContractError(
            f"{descriptor.provider_id} admitted no capability named {require_identifier(capability, 'capability')}; "
            f"it declares {', '.join(descriptor.capabilities) or 'none'}"
        )
    return descriptor


def describe_boundaries() -> tuple[tuple[str, str], ...]:
    """The whole extension surface in one list, for the documentation and the audit."""

    return tuple((item.value, item.speaks_for) for item in PortBoundary)
