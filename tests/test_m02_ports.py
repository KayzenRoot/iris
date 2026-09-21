"""§10 extension boundaries: what a later module may state, and what it may not smuggle in.

The frozen contract lets M03+ implement twelve-odd boundaries; invariant 28 says implementing one never
means redefining what M02 means. A prose rule cannot hold a pipeline together, so these tests pin the
four laws the module states as types:

* a provider answers only at a boundary its descriptor admits,
* a handle belongs to the provider that minted it,
* a provider cannot widen the question it was asked,
* and a compiled plan is not the graph it describes.

The refusals are the point. A port that only ever accepts what it is handed is documentation, not a
boundary, so almost every test below is a claim someone tried to make through an adapter and the kernel
declined — including the domain-neutrality scan, which fails the moment this module names a vendor.
"""

from __future__ import annotations

import inspect
import unittest
from types import MappingProxyType, SimpleNamespace
from typing import Any

from iris_project_os.branching import IdentityAnchorPolicy
from iris_project_os.build import RepairFrontier, RepairTarget
from iris_project_os.errors import PortContractError, SchemaValidationError, UnsupportedVersionError
from iris_project_os.identity import EntityKind, ExternalRef
from iris_project_os.limits import (
    MAX_FACETS,
    MAX_OBSERVED_DEPENDENCIES,
    MAX_PORT_CAPABILITIES,
)
from iris_project_os.ports import (
    CapabilitySource,
    CompilationRequest,
    CompiledStep,
    ContextFingerprintAnswer,
    ContextFingerprintSource,
    DependencyObservation,
    DependencyObserver,
    DeliveryProvider,
    DeliveryStatus,
    ExecutionCapability,
    ExecutionPlan,
    IdentityAnchorRuling,
    IdentityAnchorSource,
    IngestedMaterial,
    MaterializationIngestor,
    PolicyResolution,
    PolicySource,
    PortBoundary,
    ProviderCompiler,
    ProviderDescriptor,
    ProviderHandle,
    RepairOffer,
    RepairPlan,
    RepairProvider,
    RightsProvenanceGate,
    RightsRuling,
    SemanticTypeDeclaration,
    SemanticTypeRegistry,
    describe_boundaries,
    port_reference,
    require_admitted,
    require_declared_dependencies,
)
from iris_project_os.reuse import ContextSource
from iris_project_os.serialization import envelope, from_envelope

from tests import m01_kernel_support as q
from tests import m02_kernel_support as k

PROVIDER = "provider.test"
OUTSIDER = "provider.other"
TOOL = k.component_version("m02.provider", "1.0.0")
NOW = k.CACHE_NOW
NODES = ("alpha", "beta")
ASSET = k.ref(EntityKind.ARTIFACT, "asset.logo")


def handle(
    boundary: PortBoundary = PortBoundary.PROVIDER_COMPILER,
    *,
    provider_id: str = PROVIDER,
    opaque: str = "tmp/step-one",
    **over: Any,
) -> ProviderHandle:
    over.setdefault("expires_at_ms", NOW + 60_000)
    over.setdefault("issued_at_ms", NOW)
    return ProviderHandle(
        boundary=boundary,
        provider_id=provider_id,
        opaque_reference=opaque,
        **over,
    )


def capability(*, nodes: tuple[str, ...] = NODES, effects: tuple[Any, ...] = (), **over: Any) -> ExecutionCapability:
    return ExecutionCapability(
        capability_id=k.new_id(),
        provider_id=PROVIDER,
        tool=TOOL,
        environment_ref=k.ref(EntityKind.ENVIRONMENT, "env.render"),
        permitted_node_ids=nodes,
        side_effects=effects,
        **over,
    )


def request(
    *,
    nodes: tuple[str, ...] = NODES,
    inputs: tuple[ExternalRef, ...] = (ASSET,),
    capability_value: ExecutionCapability | None = None,
    **over: Any,
) -> CompilationRequest:
    return CompilationRequest(
        revision_id=over.pop("revision_id", k.new_id()),
        node_ids=nodes,
        capability=capability_value or capability(nodes=nodes),
        admitted_inputs=inputs,
        requested_at_ms=NOW,
        **over,
    )


def step(node_id: str, **over: Any) -> CompiledStep:
    over.setdefault("inputs", ())
    over.setdefault("outputs", (port_reference(node_id, "out"),))
    over.setdefault("instruction", handle())
    over.setdefault("tool", TOOL)
    return CompiledStep(node_id=node_id, **over)


def plan(
    *,
    steps: tuple[CompiledStep, ...] | None = None,
    request_value: CompilationRequest | None = None,
    provider_id: str = PROVIDER,
    **over: Any,
) -> ExecutionPlan:
    wanted = request_value if request_value is not None else request()
    return ExecutionPlan(
        request=wanted,
        provider_id=provider_id,
        component=TOOL,
        steps=steps if steps is not None else tuple(step(name) for name in wanted.node_ids),
        **over,
    )


def descriptor(
    *,
    boundaries: tuple[Any, ...] = (PortBoundary.PROVIDER_COMPILER,),
    capabilities: tuple[str, ...] = (),
    kinds: tuple[Any, ...] = (),
    provider_id: str = PROVIDER,
    **over: Any,
) -> ProviderDescriptor:
    over.setdefault("component", TOOL)
    return ProviderDescriptor(
        provider_id=provider_id,
        boundaries=boundaries,
        capabilities=capabilities,
        admitted_kinds=kinds,
        **over,
    )


def refs(*names: str, kind: EntityKind = EntityKind.ARTIFACT) -> tuple[ExternalRef, ...]:
    return tuple(k.ref(kind, name) for name in names)


def anchor(*, baseline: str | None = None) -> IdentityAnchorPolicy:
    return IdentityAnchorPolicy(
        anchor_id="anchor.spokesperson",
        policy_ref=k.ref(EntityKind.POLICY, "policy.identity"),
        baseline_digest=baseline or k.digest("baseline"),
    )


def slice_of(axis: str = "region", *values: str) -> k.DependencySlice:
    return k.DependencySlice(axis=axis, values=values or ("left",))


def repair_target(node_id: str = "render.logo", **over: Any) -> RepairTarget:
    over.setdefault("facets", (k.DependencyFacet.CONTENT,))
    over.setdefault("reasons", ("input digest moved",))
    over.setdefault("slice", slice_of())
    return RepairTarget(node_id=node_id, **over)


def offer(target: RepairTarget | None = None, **over: Any) -> RepairOffer:
    wanted = target if target is not None else repair_target()
    over.setdefault("handle", handle(PortBoundary.REPAIR_PROVIDER))
    over.setdefault("facets", wanted.facets)
    return RepairOffer(
        target=wanted,
        provider_id=PROVIDER,
        offered_at_ms=NOW,
        **over,
    )


class StubProvider:
    """A provider that says what it admits, which is all the boundary gate can see of it."""

    def __init__(self, descriptor_value: ProviderDescriptor) -> None:
        self.descriptor = descriptor_value

    def compile(self, compilation: CompilationRequest, revision: Any) -> ExecutionPlan:
        return plan(request_value=compilation)

    def observe(self, revision: Any, node_id: str, *, handle_value: Any = None) -> DependencyObservation:
        return DependencyObservation(revision_id=revision.revision_id, node_id=node_id)

    def ingest(self, node_id: str, port_id: str, *, handle_value: Any = None) -> IngestedMaterial:
        raise AssertionError("a stub provider is never executed by these tests")

    def resolve(self, type_ref: Any) -> None:
        return None

    def rule(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def rule_on(self, references: Any, *, now_ms: int = 0) -> RightsRuling:
        return None

    def capability_for(self, provider_id: str, *, now_ms: int = 0) -> Any:
        return None

    def offers_for(self, frontier: RepairFrontier, *, now_ms: int = 0) -> Any:
        return None

    def fingerprint(self, sources: Any, *, compiler: Any) -> Any:
        return None

    def status(self, **kwargs: Any) -> Any:
        return None


class PortBoundaryTests(unittest.TestCase):
    def test_every_boundary_names_one_claim(self) -> None:
        self.assertEqual(len(PortBoundary.members()), 14)
        for item in PortBoundary:
            self.assertTrue(item.speaks_for)

    def test_describe_boundaries_is_the_whole_surface(self) -> None:
        listed = describe_boundaries()
        self.assertEqual({item[0] for item in listed}, set(PortBoundary.members()))
        self.assertEqual(len(listed), len(set(listed)))

    def test_unknown_boundary_is_refused_not_guessed(self) -> None:
        with self.assertRaises(SchemaValidationError):
            PortBoundary.parse("MODEL_HUB", "boundary")

    def test_boundary_parses_case_insensitively(self) -> None:
        self.assertIs(PortBoundary.parse("provider_compiler"), PortBoundary.PROVIDER_COMPILER)

    def test_boundary_claims_are_frozen(self) -> None:
        from iris_project_os import ports

        self.assertIsInstance(ports._BOUNDARY_CLAIMS, MappingProxyType)
        with self.assertRaises(TypeError):
            ports._BOUNDARY_CLAIMS[PortBoundary.SNAPSHOT_STORE] = "whatever it wants"  # type: ignore[index]


class ProviderDescriptorTests(unittest.TestCase):
    def test_boundaries_are_deduplicated_and_ordered(self) -> None:
        value = descriptor(
            boundaries=(PortBoundary.REPAIR_PROVIDER, PortBoundary.PROVIDER_COMPILER, PortBoundary.REPAIR_PROVIDER)
        )
        self.assertEqual(
            value.boundaries, (PortBoundary.PROVIDER_COMPILER, PortBoundary.REPAIR_PROVIDER)
        )

    def test_capabilities_and_kinds_are_deduplicated(self) -> None:
        value = descriptor(
            boundaries=(),
            capabilities=("blender", "blender", "comfy"),
            kinds=(EntityKind.ARTIFACT, EntityKind.ARTIFACT),
        )
        self.assertEqual(value.capabilities, ("blender", "comfy"))
        self.assertEqual(value.admitted_kinds, (EntityKind.ARTIFACT,))

    def test_admits_and_supports_read_the_declaration(self) -> None:
        value = descriptor(capabilities=("gpu",), kinds=(EntityKind.ARTIFACT,))
        self.assertTrue(value.admits(PortBoundary.PROVIDER_COMPILER))
        self.assertFalse(value.admits(PortBoundary.REPAIR_PROVIDER))
        self.assertTrue(value.supports("gpu"))
        self.assertTrue(value.may_resolve(ASSET))
        self.assertFalse(value.may_resolve(k.ref(EntityKind.POLICY, "policy.x")))

    def test_unsupported_contract_version_is_refused(self) -> None:
        with self.assertRaises(UnsupportedVersionError):
            descriptor(contract_version="m02-contract-v9.9")

    def test_provider_id_must_follow_identifier_grammar(self) -> None:
        with self.assertRaises(SchemaValidationError):
            descriptor(provider_id="Provider Test")

    def test_component_must_be_a_versioned_component(self) -> None:
        with self.assertRaises(SchemaValidationError):
            descriptor(component="blender 4.1")

    def test_component_payload_is_accepted_and_frozen(self) -> None:
        value = ProviderDescriptor(
            provider_id=PROVIDER,
            component={"identifier": "m02.provider", "version": "1.0.0"},
        )
        self.assertEqual(value.component, TOOL)

    def test_capability_list_is_bounded(self) -> None:
        with self.assertRaises(SchemaValidationError):
            descriptor(
                boundaries=(),
                capabilities=tuple(f"capability-{index}" for index in range(MAX_PORT_CAPABILITIES + 1)),
            )

    def test_payload_round_trip(self) -> None:
        value = descriptor(capabilities=("gpu",), kinds=(EntityKind.ARTIFACT,))
        self.assertEqual(ProviderDescriptor.from_payload(value.to_payload()), value)


class RequireAdmittedTests(unittest.TestCase):
    def test_missing_provider_is_named_by_what_it_cannot_state(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            require_admitted(None, PortBoundary.RIGHTS_PROVENANCE_GATE)
        self.assertIn("whether a reference may be used", str(caught.exception))

    def test_provider_without_descriptor_is_refused(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            require_admitted(SimpleNamespace(), PortBoundary.PROVIDER_COMPILER)
        self.assertIn("ProviderDescriptor", str(caught.exception))

    def test_answering_at_an_undeclared_boundary_is_refused(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            require_admitted(StubProvider(descriptor()), PortBoundary.REPAIR_PROVIDER)
        self.assertIn("invariant 28", str(caught.exception))

    def test_unsupported_capability_is_refused(self) -> None:
        with self.assertRaises(PortContractError):
            require_admitted(StubProvider(descriptor()), PortBoundary.PROVIDER_COMPILER, capability="gpu")

    def test_admitted_provider_returns_its_descriptor(self) -> None:
        declared = descriptor(capabilities=("gpu",))
        found = require_admitted(StubProvider(declared), PortBoundary.PROVIDER_COMPILER, capability="gpu")
        self.assertEqual(found, declared)


class ProviderHandleTests(unittest.TestCase):
    def test_expiry_before_issue_is_refused(self) -> None:
        with self.assertRaises(PortContractError):
            handle(issued_at_ms=NOW, expires_at_ms=NOW - 1)

    def test_a_handle_is_not_a_locator_another_provider_can_open(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            handle().presented_to(OUTSIDER)
        self.assertIn(PROVIDER, str(caught.exception))

    def test_a_handle_cannot_be_used_at_another_boundary(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            handle().presented_to(PROVIDER, boundary=PortBoundary.REPAIR_PROVIDER)
        self.assertIn("which bounded slice can bring a node back", str(caught.exception))

    def test_expired_handle_is_refused_at_the_moment_of_use(self) -> None:
        with self.assertRaises(PortContractError):
            handle(expires_at_ms=NOW + 10).presented_to(PROVIDER, now_ms=NOW + 11)

    def test_live_handle_presents_itself_unchanged(self) -> None:
        value = handle()
        self.assertIs(value.presented_to(PROVIDER, boundary=PortBoundary.PROVIDER_COMPILER, now_ms=NOW), value)

    def test_sealed_handles_are_distinguishable(self) -> None:
        self.assertFalse(handle().is_sealed)
        sealed = handle(content_digest=k.digest("bytes"))
        self.assertTrue(sealed.is_sealed)
        self.assertEqual(sealed.text, f"{PROVIDER}:PROVIDER_COMPILER:tmp/step-one")

    def test_content_digest_must_be_a_digest(self) -> None:
        with self.assertRaises(SchemaValidationError):
            handle(content_digest="gs://bucket/object")

    def test_opaque_reference_length_is_bounded(self) -> None:
        with self.assertRaises(SchemaValidationError):
            handle(opaque="x" * 600)


class ExecutionCapabilityTests(unittest.TestCase):
    def test_grant_is_scoped_to_named_nodes(self) -> None:
        value = capability(nodes=("alpha",))
        self.assertTrue(value.may_run("alpha"))
        self.assertFalse(value.may_run("beta"))

    def test_empty_grant_permits_nothing_rather_than_everything(self) -> None:
        value = capability(nodes=())
        self.assertTrue(value.is_unbounded)
        self.assertFalse(value.may_run("alpha"))

    def test_side_effects_are_deduplicated_and_ordered(self) -> None:
        value = capability(
            effects=(k.SideEffectClass.EXTERNAL_MUTATION, k.SideEffectClass.NO_SIDE_EFFECT, k.SideEffectClass.EXTERNAL_MUTATION)
        )
        self.assertEqual(
            value.side_effects,
            (k.SideEffectClass.EXTERNAL_MUTATION, k.SideEffectClass.NO_SIDE_EFFECT),
        )
        self.assertTrue(value.permits_side_effect("external_mutation"))
        self.assertFalse(value.permits_side_effect("controlled_outputs"))

    def test_unknown_side_effect_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            capability(effects=("writes_whenever_it_feels_like_it",))

    def test_environment_must_be_a_reference(self) -> None:
        with self.assertRaises(SchemaValidationError):
            ExecutionCapability(
                capability_id=k.new_id(),
                provider_id=PROVIDER,
                tool=TOOL,
                environment_ref="env.render",
            )

    def test_liveness_is_read_at_the_moment_of_dispatch(self) -> None:
        value = capability(expires_at_ms=NOW + 100)
        self.assertTrue(value.is_live(NOW))
        self.assertFalse(value.is_live(NOW + 101))


class SemanticTypeDeclarationTests(unittest.TestCase):
    def declaration(self, **over: Any) -> SemanticTypeDeclaration:
        over.setdefault("type_ref", k.semantic_type("vector.svg"))
        return SemanticTypeDeclaration(**over)

    def test_conversion_into_itself_is_refused(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            self.declaration(converts_to=("vector.svg",))
        self.assertIn("conversion into itself", str(caught.exception))

    def test_declared_conversions_are_admitted(self) -> None:
        value = self.declaration(converts_to=("raster.png", "text.script"))
        self.assertTrue(value.admits_conversion_to(k.semantic_type("raster.png")))
        self.assertFalse(value.admits_conversion_to(k.semantic_type("mesh.obj")))

    def test_schema_reference_comes_from_the_type(self) -> None:
        value = self.declaration()
        self.assertEqual(value.schema_ref, value.type_ref.schema_ref)

    def test_field_names_must_be_identifiers(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.declaration(field_names=("Vertex Count",))

    def test_registered_by_accepts_a_component_payload(self) -> None:
        value = self.declaration(registered_by={"identifier": "m02.provider", "version": "1.0.0"})
        self.assertEqual(value.registered_by, TOOL)


class PolicyResolutionTests(unittest.TestCase):
    def test_a_policy_answers_with_m01s_own_contract(self) -> None:
        contract = q.contract()
        found = PolicyResolution(policy_ref=k.ref(EntityKind.POLICY, "policy.default"), contract=contract)
        self.assertIs(found.contract, contract)

    def test_a_re_described_contract_is_refused(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            PolicyResolution(
                policy_ref=k.ref(EntityKind.POLICY, "policy.default"),
                contract={"contract_id": "contract.copy", "intent": "a fork"},
            )
        self.assertIn("second fidelity vocabulary", str(caught.exception))

    def test_policy_reference_must_be_a_reference(self) -> None:
        with self.assertRaises(SchemaValidationError):
            PolicyResolution(policy_ref="policy.default", contract=q.contract())

    def test_resolution_carries_the_surviving_m01_bytes(self) -> None:
        contract = q.contract()
        found = PolicyResolution(policy_ref=k.ref(EntityKind.POLICY), contract=contract, resolved_at_ms=NOW)
        self.assertEqual(found.to_payload()["contract"], contract.to_payload())
        self.assertEqual(PolicyResolution.from_payload(found.to_payload()), found)


class IdentityAnchorRulingTests(unittest.TestCase):
    subject = k.ref(EntityKind.ARTIFACT, "asset.face")

    def ruling(self, **over: Any) -> IdentityAnchorRuling:
        over.setdefault("anchor", anchor())
        over.setdefault("subject", self.subject)
        return IdentityAnchorRuling(**over)

    def test_a_provider_cannot_grant_drift_the_policy_does_not_authorise(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            self.ruling(candidate_digest=k.digest("different face"), permitted=True)
        self.assertIn("cannot grant past the policy", str(caught.exception))

    def test_a_migration_receipt_carries_the_drift(self) -> None:
        found = self.ruling(
            candidate_digest=k.digest("different face"),
            permitted=True,
            migration_receipts=(k.new_id(),),
        )
        self.assertTrue(found.drifts)

    def test_blocking_what_never_moved_is_a_different_gate(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            self.ruling(candidate_digest=k.digest("baseline"), permitted=False)
        self.assertIn("different gate", str(caught.exception))

    def test_a_carried_baseline_is_permitted_without_a_receipt(self) -> None:
        found = self.ruling(candidate_digest=k.digest("baseline"), permitted=True)
        self.assertFalse(found.drifts)
        self.assertEqual(found.reason_code, "anchor-checked")

    def test_receipts_must_be_identifiers(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.ruling(candidate_digest=k.digest("moved"), permitted=True, migration_receipts=("yes",))

    def test_anchor_must_be_the_policy_being_ruled_on(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.ruling(anchor="anchor.spokesperson")


class DependencyObservationTests(unittest.TestCase):
    def test_observed_references_are_deduplicated_and_ordered(self) -> None:
        value = DependencyObservation(
            revision_id=k.new_id(), node_id="render.logo", observed=(ASSET, k.ref(EntityKind.ARTIFACT, "asset.font"), ASSET)
        )
        self.assertEqual(
            [item.reference for item in value.observed], ["asset.font", "asset.logo"]
        )

    def test_observation_of_declared_material_is_accepted(self) -> None:
        revision = k.chain_revision()
        value = DependencyObservation(
            revision_id=revision.revision_id, node_id="render.logo", observed=revision.definition.declared_external_inputs
        )
        self.assertEqual(require_declared_dependencies(revision, value), value)

    def test_undeclared_dependency_is_refused_by_name(self) -> None:
        revision = k.chain_revision(declared=refs("asset.logo"))
        value = DependencyObservation(
            revision_id=revision.revision_id,
            node_id="render.logo",
            observed=refs("asset.logo", "asset.undisclosed"),
        )
        with self.assertRaises(PortContractError) as caught:
            require_declared_dependencies(revision, value)
        self.assertIn("asset.undisclosed", str(caught.exception))
        self.assertIn("report what existed", str(caught.exception))

    def test_a_bound_graph_and_a_snapshot_answer_for_their_revision(self) -> None:
        revision = k.chain_revision(declared=refs("asset.logo"))
        value = DependencyObservation(
            revision_id=revision.revision_id, node_id="render.logo", observed=refs("asset.logo")
        )
        graph = k.bound(revision_value=revision, records=k.chain_records())
        self.assertEqual(require_declared_dependencies(graph, value), value)
        sealed = k.snapshot(
            production_id="prod.test", closure_value=k.closure(production_id="prod.test", graph=graph)
        )
        self.assertEqual(require_declared_dependencies(sealed, value), value)

    def test_observation_of_another_revision_is_not_evidence_here(self) -> None:
        revision = k.chain_revision()
        value = DependencyObservation(revision_id=k.new_id(), node_id="render.logo")
        with self.assertRaises(PortContractError) as caught:
            require_declared_dependencies(revision, value)
        self.assertIn("something else", str(caught.exception))

    def test_observation_volume_is_bounded(self) -> None:
        with self.assertRaises(SchemaValidationError):
            DependencyObservation(
                revision_id=k.new_id(),
                node_id="render.logo",
                observed=tuple(k.ref(EntityKind.ARTIFACT, f"asset.{index}") for index in range(MAX_OBSERVED_DEPENDENCIES + 1)),
            )

    def test_unknown_revision_shape_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            require_declared_dependencies("graph.test", DependencyObservation(revision_id=k.new_id(), node_id="alpha"))


class CompilationRequestTests(unittest.TestCase):
    def test_request_for_no_node_is_refused(self) -> None:
        with self.assertRaises(PortContractError):
            CompilationRequest(revision_id=k.new_id(), node_ids=(), capability=capability(nodes=()))

    def test_nodes_are_deduplicated_and_ordered(self) -> None:
        value = request(nodes=("beta", "alpha", "beta"))
        self.assertEqual(value.node_ids, ("alpha", "beta"))

    def test_admitted_inputs_are_deduplicated(self) -> None:
        value = request(inputs=(ASSET, ASSET, k.ref(EntityKind.ARTIFACT, "asset.font")))
        self.assertEqual(len(value.admitted_inputs), 2)

    def test_capability_must_be_a_capability(self) -> None:
        with self.assertRaises(SchemaValidationError):
            CompilationRequest(revision_id=k.new_id(), node_ids=("alpha",), capability=PROVIDER)

    def test_reference_names_the_request_by_its_own_digest(self) -> None:
        value = request()
        self.assertEqual(value.reference.reference, value.digest()[:32])


class CompiledStepTests(unittest.TestCase):
    def test_output_must_be_a_port(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            step("alpha", outputs=(k.ref(EntityKind.ARTIFACT, "asset.row"),))
        self.assertIn("a store row is not a port", str(caught.exception))

    def test_a_step_cannot_promise_another_nodes_port(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            step("alpha", outputs=(port_reference("beta", "out"),))
        self.assertIn("another node", str(caught.exception))

    def test_a_step_cannot_depend_on_itself(self) -> None:
        with self.assertRaises(PortContractError):
            step("alpha", depends_on=("alpha",))

    def test_port_reference_grammar_is_shared(self) -> None:
        self.assertEqual(port_reference("alpha", "out").text, "port:alpha:out")
        self.assertTrue(step("alpha").produces(port_reference("alpha", "out")))
        self.assertFalse(step("alpha").produces(port_reference("beta", "out")))


class ExecutionPlanTests(unittest.TestCase):
    def test_a_honest_plan_covers_exactly_what_was_asked(self) -> None:
        value = plan()
        self.assertEqual(value.node_ids, NODES)
        self.assertEqual(value.execution_order(), NODES)
        self.assertEqual(value.side_effects, (k.SideEffectClass.NO_SIDE_EFFECT,))

    def test_compiling_unrequested_work_is_refused(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            plan(steps=(step("alpha"), step("beta"), step("gamma")))
        self.assertIn("gamma", str(caught.exception))

    def test_a_partial_plan_is_refused(self) -> None:
        with self.assertRaises(PortContractError):
            plan(steps=(step("alpha"),))

    def test_one_node_cannot_be_compiled_twice(self) -> None:
        with self.assertRaises(PortContractError):
            plan(steps=(step("alpha"), step("alpha"), step("beta")))

    def test_waiting_on_unplanned_work_is_refused(self) -> None:
        with self.assertRaises(PortContractError):
            plan(steps=(step("alpha", depends_on=("nobody",)), step("beta")))

    def test_a_circular_plan_cannot_run(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            plan(
                steps=(
                    step("alpha", depends_on=("beta",), inputs=()),
                    step("beta", depends_on=("alpha",), inputs=()),
                )
            )
        self.assertIn("depends on itself", str(caught.exception))

    def test_reading_admitted_material_is_allowed(self) -> None:
        value = plan(steps=(step("alpha", inputs=(ASSET,)), step("beta")))
        self.assertEqual(value.step_for("alpha").inputs, (ASSET,))

    def test_reading_unadmitted_material_is_refused(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            plan(steps=(step("alpha", inputs=refs("asset.surprise")), step("beta")))
        self.assertIn("asset.surprise", str(caught.exception))
        self.assertIn("invariant 5", str(caught.exception))

    def test_reading_an_upstream_steps_output_is_allowed(self) -> None:
        produced = port_reference("alpha", "out")
        value = plan(steps=(step("alpha"), step("beta", inputs=(produced,), depends_on=("alpha",))))
        self.assertTrue(value.claims_output(produced))

    def test_reading_output_without_declaring_the_edge_is_refused(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            plan(steps=(step("alpha"), step("beta", inputs=(port_reference("alpha", "out"),))))
        self.assertIn("no step it depends on produces", str(caught.exception))

    def test_one_port_has_one_producer_in_the_plan(self) -> None:
        produced = port_reference("alpha", "out")
        value = plan()
        self.assertEqual([item.node_id for item in value.steps if item.produces(produced)], ["alpha"])

    def test_a_node_cannot_promise_another_nodes_port(self) -> None:
        shared = port_reference("alpha", "out")
        with self.assertRaises(PortContractError):
            plan(
                steps=(
                    step("alpha"),
                    CompiledStep(node_id="beta", tool=TOOL, instruction=handle(), outputs=(shared,)),
                )
            )

    def test_a_node_outside_the_grant_cannot_be_scheduled(self) -> None:
        with self.assertRaises(PortContractError):
            plan(request_value=request(nodes=NODES, capability_value=capability(nodes=("alpha",))))

    def test_the_tool_identity_is_part_of_the_grant(self) -> None:
        other = k.component_version("m02.other", "2.0.0")
        with self.assertRaises(PortContractError):
            plan(steps=(step("alpha", tool=other), step("beta")))

    def test_a_plan_cannot_grant_itself_a_side_effect(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            plan(
                steps=(
                    step("alpha", side_effect=k.SideEffectClass.EXTERNAL_MUTATION),
                    step("beta"),
                )
            )
        self.assertIn("EXTERNAL_MUTATION", str(caught.exception))

    def test_a_granted_side_effect_is_allowed(self) -> None:
        value = plan(
            request_value=request(capability_value=capability(effects=(k.SideEffectClass.EXTERNAL_MUTATION,))),
            steps=(step("alpha", side_effect=k.SideEffectClass.EXTERNAL_MUTATION), step("beta")),
        )
        self.assertIn(k.SideEffectClass.EXTERNAL_MUTATION, value.side_effects)

    def test_another_providers_instruction_is_refused(self) -> None:
        with self.assertRaises(PortContractError):
            plan(steps=(step("alpha", instruction=handle(provider_id=OUTSIDER)), step("beta")))

    def test_an_instruction_from_another_boundary_is_refused(self) -> None:
        with self.assertRaises(PortContractError):
            plan(
                steps=(
                    step("alpha", instruction=handle(PortBoundary.REPAIR_PROVIDER)),
                    step("beta"),
                )
            )

    def test_step_lookup_refuses_to_invent_a_step(self) -> None:
        with self.assertRaises(PortContractError):
            plan().step_for("gamma")

    def test_plan_digest_is_stable_across_equal_plans(self) -> None:
        asked = request()
        self.assertEqual(plan(request_value=asked).plan_digest, plan(request_value=asked).plan_digest)
        widened = plan(
            request_value=asked,
            steps=(step("alpha"), step("beta", outputs=(port_reference("beta", "final"),))),
        )
        self.assertNotEqual(plan(request_value=asked).plan_digest, widened.plan_digest)

    def test_plan_round_trips_and_binds_nothing(self) -> None:
        value = plan()
        self.assertEqual(ExecutionPlan.from_payload(value.to_payload()), value)
        self.assertEqual(value.request.node_ids, NODES)

    def test_unsupported_contract_version_is_refused(self) -> None:
        with self.assertRaises(UnsupportedVersionError):
            plan(contract_version="m02-contract-v0.1")


class IngestedMaterialTests(unittest.TestCase):
    def material(self, **over: Any) -> IngestedMaterial:
        over.setdefault("node_id", "render.logo")
        over.setdefault("port_id", "out")
        over.setdefault("revision_ref", k.ref(EntityKind.REVISION, "rev-1"))
        over.setdefault("content_digest", k.digest("bytes"))
        over.setdefault("handle", handle(PortBoundary.MATERIALIZATION_INGESTOR, opaque="out/exr/1"))
        over.setdefault("provider_id", PROVIDER)
        over.setdefault("produced_at_ms", NOW)
        return IngestedMaterial(**over)

    def test_ingesting_becomes_the_graphs_own_record(self) -> None:
        value = self.material(producer_attempt_id=k.new_id(), decision_ref=k.ref(EntityKind.QUALITY_DECISION, "q-1"))
        found = value.as_materialization()
        self.assertEqual(found.content_digest, value.content_digest)
        self.assertEqual(found.decision_ref, value.decision_ref)
        self.assertEqual(found.port_id, "out")

    def test_a_handle_from_another_provider_is_refused(self) -> None:
        with self.assertRaises(PortContractError):
            self.material(handle=handle(PortBoundary.MATERIALIZATION_INGESTOR, provider_id=OUTSIDER))

    def test_a_compiler_handle_is_not_ingestable(self) -> None:
        with self.assertRaises(PortContractError):
            self.material(handle=handle(opaque="tmp/step-one"))

    def test_bytes_must_match_the_seal_on_them(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            self.material(
                content_digest=k.digest("other bytes"),
                handle=handle(PortBoundary.MATERIALIZATION_INGESTOR, content_digest=k.digest("bytes")),
            )
        self.assertIn("one claim", str(caught.exception))

    def test_port_reference_matches_what_a_plan_promised(self) -> None:
        value = self.material()
        found = plan(steps=(CompiledStep(node_id="render.logo", tool=TOOL, instruction=handle(), outputs=(value.port_ref,)), step("beta")), request_value=request(nodes=("render.logo", "beta")))
        self.assertTrue(found.claims_output(value.port_ref))
        self.assertFalse(found.claims_output(k.ref(EntityKind.ARTIFACT, "somewhere else")))

    def test_digest_must_be_a_digest(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.material(content_digest="out/exr/1")

    def test_attempt_must_be_an_identifier(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.material(producer_attempt_id="attempt one")


class RepairPlanTests(unittest.TestCase):
    frontier: RepairFrontier

    def setUp(self) -> None:
        self.frontier = RepairFrontier(graph_id="graph.test", targets=(repair_target(),), uncovered=("deliver.web",))

    def test_an_offer_repairs_what_its_target_names(self) -> None:
        value = offer()
        self.assertEqual(value.node_id, "render.logo")
        self.assertTrue(value.answers(self.frontier))

    def test_an_offer_cannot_widen_its_own_target(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            offer(facets=(k.DependencyFacet.CONTENT, k.DependencyFacet.RIGHTS))
        self.assertIn("RIGHTS", str(caught.exception))

    def test_offer_facets_are_bounded(self) -> None:
        with self.assertRaises(SchemaValidationError):
            offer(facets=(k.DependencyFacet.CONTENT,) * (MAX_FACETS + 1))

    def test_a_repair_handle_is_scoped_to_the_repair_provider(self) -> None:
        with self.assertRaises(PortContractError):
            offer(handle=handle(PortBoundary.MATERIALIZATION_INGESTOR))

    def test_a_plan_that_answers_the_frontier(self) -> None:
        value = RepairPlan(
            frontier_graph_id="graph.test",
            offers=(offer(),),
            uncovered=("deliver.web",),
            planned_at_ms=NOW,
        )
        self.assertEqual(value.covered, ("render.logo",))
        self.assertIs(value.checked_against(self.frontier), value)

    def test_two_offers_for_one_node_is_an_arbitration_question(self) -> None:
        with self.assertRaises(PortContractError):
            RepairPlan(
                frontier_graph_id="graph.test",
                offers=(offer(), offer(handle=handle(PortBoundary.REPAIR_PROVIDER, opaque="tmp/other"))),
                uncovered=("deliver.web",),
            )

    def test_a_node_cannot_be_both_offered_and_uncovered(self) -> None:
        with self.assertRaises(PortContractError):
            RepairPlan(
                frontier_graph_id="graph.test",
                offers=(offer(),),
                uncovered=("deliver.web", "render.logo"),
            )

    def test_a_plan_for_another_graph_is_refused(self) -> None:
        value = RepairPlan(frontier_graph_id="graph.test", offers=(offer(),), uncovered=("deliver.web",))
        with self.assertRaises(PortContractError):
            value.checked_against(RepairFrontier(graph_id="graph.other", targets=(repair_target(),)))

    def test_a_plan_that_leaves_part_of_the_node_stale_is_refused(self) -> None:
        value = RepairPlan(frontier_graph_id="graph.test", offers=(offer(),), uncovered=())
        with self.assertRaises(PortContractError) as caught:
            value.checked_against(self.frontier)
        self.assertIn("deliver.web", str(caught.exception))

    def test_a_plan_that_ignores_a_target_is_refused(self) -> None:
        value = RepairPlan(frontier_graph_id="graph.test", offers=(), uncovered=("deliver.web",))
        with self.assertRaises(PortContractError):
            value.checked_against(self.frontier)

    def test_an_offer_answered_to_the_wrong_slice_is_refused(self) -> None:
        other = offer(target=repair_target(slice=slice_of("region", "right")))
        value = RepairPlan(frontier_graph_id="graph.test", offers=(other,), uncovered=("deliver.web",))
        with self.assertRaises(PortContractError) as caught:
            value.checked_against(self.frontier)
        self.assertIn("slice has to be the one", str(caught.exception))


class RightsRulingTests(unittest.TestCase):
    def ruling(self, **over: Any) -> RightsRuling:
        over.setdefault("asked", refs("asset.a", "asset.b"))
        over.setdefault("permitted", refs("asset.a"))
        over.setdefault("blocked", refs("asset.b"))
        over.setdefault("ruled_at_ms", NOW)
        return RightsRuling(**over)

    def test_a_ruling_partitions_what_was_submitted(self) -> None:
        found = self.ruling()
        self.assertFalse(found.is_clear)
        self.assertEqual(found.answer_for(k.ref(EntityKind.ARTIFACT, "asset.a")), "permitted")
        self.assertEqual(found.answer_for(k.ref(EntityKind.ARTIFACT, "asset.b")), "blocked")

    def test_answering_about_nobody_asked_is_refused(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            self.ruling(permitted=refs("asset.a", "asset.unasked"))
        self.assertIn("asset.unasked", str(caught.exception))

    def test_leaving_a_question_silent_is_refused(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            self.ruling(permitted=refs("asset.a"), blocked=())
        self.assertIn("asset.b", str(caught.exception))

    def test_one_reference_cannot_get_two_answers(self) -> None:
        with self.assertRaises(PortContractError):
            self.ruling(permitted=refs("asset.a"), blocked=refs("asset.a"), asked=refs("asset.a"))

    def test_unknown_is_not_a_pass(self) -> None:
        found = self.ruling(unknown=refs("asset.b"), blocked=())
        self.assertTrue(found.needs_reconciliation)
        self.assertFalse(found.is_clear)

    def test_a_clear_ruling_blocks_and_knows_nothing(self) -> None:
        found = RightsRuling(asked=refs("asset.a"), permitted=refs("asset.a"), ruled_at_ms=NOW)
        self.assertTrue(found.is_clear)
        self.assertEqual(found.answer_for(k.ref(EntityKind.ARTIFACT, "asset.a")), "permitted")

    def test_answer_for_refuses_to_invent_a_ruling(self) -> None:
        with self.assertRaises(PortContractError):
            self.ruling().answer_for(k.ref(EntityKind.ARTIFACT, "asset.never asked"))

    def test_decided_by_must_be_a_reference(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.ruling(decided_by="policy/rights")


class ContextFingerprintAnswerTests(unittest.TestCase):
    sources = (ContextSource(ref=k.ref(EntityKind.HIVE_CONTEXT, "ctx.brief"), ordinal=0),)

    def answer(self, **over: Any) -> ContextFingerprintAnswer:
        over.setdefault("sources", self.sources)
        over.setdefault("fingerprint", k.digest("context"))
        over.setdefault("compiler", TOOL)
        over.setdefault("observed_at_ms", NOW)
        return ContextFingerprintAnswer(**over)

    def test_a_runtime_hash_is_not_durable_evidence_by_itself(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            self.answer(durable=True)
        self.assertIn("qualification", str(caught.exception))

    def test_a_named_qualification_makes_it_durable(self) -> None:
        found = self.answer(durable=True, qualification_ref=k.ref(EntityKind.ENVIRONMENT, "env.qualified"))
        self.assertTrue(found.durable)

    def test_the_source_sequence_is_part_of_the_claim(self) -> None:
        found = self.answer()
        self.assertEqual(found.source_texts, ("hive_context:ctx.brief",))
        self.assertTrue(found.answers(self.sources))
        self.assertFalse(found.answers((ContextSource(ref=k.ref(EntityKind.HIVE_CONTEXT, "ctx.other"), ordinal=0),)))

    def test_ordering_matters_because_prefix_reuse_does(self) -> None:
        first = ContextSource(ref=k.ref(EntityKind.HIVE_CONTEXT, "ctx.brief"), ordinal=0)
        second = ContextSource(ref=k.ref(EntityKind.HIVE_CONTEXT, "ctx.style"), ordinal=1)
        found = self.answer(sources=(first, second))
        self.assertTrue(found.answers((first, second)))
        self.assertFalse(found.answers((second, first)))

    def test_a_fingerprint_answer_matches_a_digest_or_a_causal_fingerprint(self) -> None:
        found = self.answer()
        self.assertTrue(found.matches(k.digest("context")))
        self.assertFalse(found.matches(k.digest("else")))
        self.assertTrue(found.matches(SimpleNamespace(fingerprint=k.digest("context"))))
        with self.assertRaises(SchemaValidationError):
            found.matches("ctx-1")

    def test_sources_are_bounded(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.answer(sources=tuple(ContextSource(ref=k.ref(EntityKind.HIVE_CONTEXT, f"ctx.{index}")) for index in range(200)))


class DeliveryStatusTests(unittest.TestCase):
    destination = k.ref(EntityKind.DESTINATION, "dest.cdn")
    package = k.ref(EntityKind.ARTIFACT, "pkg.web")

    def status(self, **over: Any) -> DeliveryStatus:
        over.setdefault("destination", self.destination)
        over.setdefault("package_ref", self.package)
        over.setdefault("state", "STILL_UNKNOWN")
        over.setdefault("observed_at_ms", NOW)
        return DeliveryStatus(**over)

    def test_landing_is_a_claim_about_the_world_and_owes_proof(self) -> None:
        with self.assertRaises(PortContractError) as caught:
            self.status(state="LANDED")
        self.assertIn("own assurance", str(caught.exception))

    def test_landing_with_evidence_is_accepted(self) -> None:
        found = self.status(state="LANDED", evidence_refs=(k.ref(EntityKind.EVIDENCE, "ev.response"),))
        self.assertTrue(found.is_resolved)

    def test_not_being_sure_is_an_honest_answer(self) -> None:
        self.assertFalse(self.status().is_resolved)

    def test_an_unknown_state_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.status(state="PROBABLY_FINE")

    def test_a_delivery_answer_must_address_a_destination(self) -> None:
        with self.assertRaises(PortContractError):
            self.status(destination=self.package)


class PortProtocolTests(unittest.TestCase):
    def test_a_stub_provider_satisfies_the_boundaries_it_declares(self) -> None:
        wired = StubProvider(descriptor(boundaries=tuple(PortBoundary)))
        self.assertIsInstance(wired, ProviderCompiler)
        self.assertIsInstance(wired, DependencyObserver)
        self.assertIsInstance(wired, RightsProvenanceGate)
        self.assertIsInstance(wired, ContextFingerprintSource)
        self.assertIsInstance(wired, DeliveryProvider)
        self.assertIsInstance(wired, CapabilitySource)
        self.assertIsInstance(wired, SemanticTypeRegistry)
        self.assertIsInstance(wired, PolicySource)
        self.assertIsInstance(wired, IdentityAnchorSource)
        self.assertIsInstance(wired, RepairProvider)

    def test_a_stranger_is_not_a_provider(self) -> None:
        self.assertNotIsInstance(SimpleNamespace(), ProviderCompiler)
        self.assertNotIsInstance("blender", MaterializationIngestor)

    def test_a_provider_that_never_described_itself_cannot_be_admitted(self) -> None:
        with self.assertRaises(PortContractError):
            require_admitted(SimpleNamespace(compile=lambda *a: None), PortBoundary.PROVIDER_COMPILER)


class PortDomainNeutralityTests(unittest.TestCase):
    source = inspect.getsource(__import__("iris_project_os.ports", fromlist=["ports"]))

    def test_the_port_layer_names_no_vendor_or_host_runtime(self) -> None:
        for token in ("blender", "comfy", "s3://", "boto", "requests", "subprocess", "sqlite", "psycopg", "http", "socket"):
            self.assertNotIn(token, self.source.lower(), f"ports.py names {token!r}")

    def test_the_port_layer_opens_no_files_or_paths(self) -> None:
        for token in ("import os", "pathlib", "open(", "tempfile"):
            self.assertNotIn(token, self.source, f"ports.py touches {token!r}")

    def test_no_boundary_claim_names_a_tool(self) -> None:
        for name, claim in describe_boundaries():
            self.assertNotIn("blender", claim.lower(), name)
            self.assertNotIn("comfy", claim.lower(), name)

    def test_a_fidelity_contract_crosses_a_port_without_being_recopied(self) -> None:
        contract = q.contract()
        found = PolicyResolution(policy_ref=k.ref(EntityKind.POLICY), contract=contract)
        self.assertIsInstance(found.contract, type(contract))
        self.assertEqual(found.contract.contract_id, contract.contract_id)

    def test_port_records_all_survive_the_envelope(self) -> None:
        values: tuple[Any, ...] = (
            descriptor(capabilities=("gpu",), kinds=(EntityKind.ARTIFACT,)),
            handle(content_digest=k.digest("bytes")),
            capability(effects=(k.SideEffectClass.EXTERNAL_MUTATION,)),
            SemanticTypeDeclaration(type_ref=k.semantic_type("vector.svg"), converts_to=("raster.png",)),
            PolicyResolution(policy_ref=k.ref(EntityKind.POLICY), contract=q.contract()),
            IdentityAnchorRuling(anchor=anchor(), subject=k.ref(EntityKind.ARTIFACT, "asset.face"), permitted=True),
            DependencyObservation(revision_id=k.new_id(), node_id="render.logo", observed=refs("asset.logo")),
            request(),
            step("alpha", inputs=(ASSET,)),
            plan(),
            IngestedMaterial(
                node_id="render.logo",
                port_id="out",
                revision_ref=k.ref(EntityKind.REVISION, "rev-1"),
                content_digest=k.digest("bytes"),
                handle=handle(PortBoundary.MATERIALIZATION_INGESTOR),
                provider_id=PROVIDER,
            ),
            offer(),
            RepairPlan(frontier_graph_id="graph.test", offers=(offer(),), uncovered=("deliver.web",)),
            RightsRuling(asked=refs("asset.a"), permitted=refs("asset.a")),
            ContextFingerprintAnswer(sources=(ContextSource(ref=k.ref(EntityKind.HIVE_CONTEXT, "ctx.brief")),), fingerprint=k.digest("context"), compiler=TOOL),
            DeliveryStatus(destination=k.ref(EntityKind.DESTINATION, "dest.cdn"), package_ref=k.ref(EntityKind.ARTIFACT, "pkg"), state="STILL_UNKNOWN"),
        )
        for value in values:
            self.assertEqual(from_envelope(envelope(value)), value, type(value).__name__)

    def test_the_module_holds_no_module_level_mutable_state(self) -> None:
        from iris_project_os import ports

        for name, value in vars(ports).items():
            if name.startswith("__"):
                continue
            self.assertNotIsInstance(value, (dict, list, set), f"ports.{name} is mutable global state")
