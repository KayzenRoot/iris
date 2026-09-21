"""Area B proves the Production Graph cannot be malformed, mis-typed or unexplained.

The definition graph is immutable intent, so every illegal shape is refused at
construction: an edge that joins two different semantic types, a material cycle,
a single-input socket fed twice, a required input nobody feeds. On top of that the
analysis layer refuses the two failures a build system hides most cheaply: a
fingerprint a mere rename perturbs (which would poison every cache), and a dirty
node with no named cause. Dynamic discovery may never rewrite a frozen revision in
place — it can only propose a delta that admits it forward.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any

from iris_quality.contracts import QualityClass

from iris_project_os.analysis import (
    CausalFingerprint,
    DependencyLedger,
    DiscoveryState,
    ExplainStep,
    ImpactCone,
    ImpactEffect,
    compute_fingerprint,
    impact_of,
)
from iris_project_os.errors import (
    GraphValidationError,
    IdentityError,
    PromotionBlockedError,
    SchemaValidationError,
)
from iris_project_os.graph import (
    DeltaKind,
    DependencyFacet,
    DependencySlice,
    EdgeKind,
    GraphDefinition,
    GraphEdge,
    GraphMutation,
    GraphNode,
    GraphRevision,
    NodeRole,
    PortCardinality,
    PortDirection,
    PortExport,
    ReproducibilityClass,
    RetryAdmission,
    SemanticPort,
    SemanticTypeRef,
    SideEffectClass,
    SideEffectPolicy,
    SubgraphInterface,
)
from iris_project_os.identity import EntityKind

from tests import m02_kernel_support as k

VECTOR = k.VECTOR
RASTER = k.RASTER


def operation(node_id: str, *, in_type: str = VECTOR, out_type: str = VECTOR, epoch: int = 0, **over: Any) -> GraphNode:
    port_over: dict[str, Any] = {key: value for key, value in over.items() if key in ("cardinality", "required", "minimum_quality_class")}
    return k.node(
        node_id,
        NodeRole.OPERATION,
        inputs=(k.input_port("in", type_id=in_type, **port_over),),
        outputs=(k.output("out", type_id=out_type),),
        reproducibility=ReproducibilityClass.DETERMINISTIC,
        epoch=epoch,
    )


class EnumPartitionTests(unittest.TestCase):
    def test_only_material_causality_participates_in_acyclicity(self) -> None:
        self.assertTrue(EdgeKind.MATERIAL_CAUSAL.participates_in_acyclicity)
        self.assertFalse(EdgeKind.ORDER_ONLY.participates_in_acyclicity)
        self.assertFalse(EdgeKind.OBSERVATION.participates_in_acyclicity)

    def test_only_material_dirties_and_only_ordering_observation_stop_a_walk(self) -> None:
        self.assertTrue(EdgeKind.MATERIAL_CAUSAL.dirties_material)
        self.assertFalse(EdgeKind.CONSTRAINT_CAUSAL.dirties_material)
        self.assertTrue(EdgeKind.CONSTRAINT_CAUSAL.revalidates_consumer)
        self.assertTrue(EdgeKind.ORDER_ONLY.never_creates_rebuild_dependency)

    def test_only_external_mutation_requires_a_policy(self) -> None:
        self.assertTrue(SideEffectClass.EXTERNAL_MUTATION.requires_policy)
        self.assertFalse(SideEffectClass.CONTROLLED_OUTPUTS.requires_policy)

    def test_only_deterministic_and_seeded_claim_byte_identity(self) -> None:
        self.assertTrue(ReproducibilityClass.DETERMINISTIC.claims_byte_identity)
        self.assertFalse(ReproducibilityClass.STOCHASTIC.claims_byte_identity)
        self.assertTrue(ReproducibilityClass.SEEDED.requires_recorded_seed)

    def test_cardinality_bounds_and_dedup_rules(self) -> None:
        self.assertEqual(PortCardinality.ONE.maximum, 1)
        self.assertIsNone(PortCardinality.MANY_SET.maximum)
        self.assertTrue(PortCardinality.MANY_ORDERED.order_is_semantic)
        self.assertTrue(PortCardinality.MANY_SET.forbids_duplicates)

    def test_port_direction_opposite(self) -> None:
        self.assertIs(PortDirection.opposite(PortDirection.INPUT), PortDirection.OUTPUT)

    def test_an_unknown_role_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            NodeRole.parse("TELEPORT", "role")


class SemanticTypeRefTests(unittest.TestCase):
    def test_the_schema_ref_must_point_at_a_schema(self) -> None:
        with self.assertRaises(IdentityError):
            SemanticTypeRef(type_id="vector.svg", schema_ref=k.ref(EntityKind.ARTIFACT, "x"))

    def test_the_text_form_carries_the_version(self) -> None:
        value = SemanticTypeRef(type_id="vector.svg", schema_ref=k.ref(EntityKind.SCHEMA, "schema.vector"), version="2.1.0")
        self.assertEqual(value.text, "vector.svg@2.1.0")


class DependencySliceTests(unittest.TestCase):
    def test_a_slice_must_name_a_value(self) -> None:
        with self.assertRaises(SchemaValidationError):
            DependencySlice(axis="region", values=())

    def test_duplicate_slice_values_are_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            DependencySlice(axis="region", values=("a", "a"))

    def test_overlaps_only_within_the_same_axis_and_version(self) -> None:
        a = DependencySlice(axis="region", values=("top", "left"))
        self.assertTrue(a.overlaps(DependencySlice(axis="region", values=("left",))))
        self.assertFalse(a.overlaps(DependencySlice(axis="locale", values=("left",))))


class SideEffectPolicyTests(unittest.TestCase):
    def test_automatic_retry_demands_a_compensation_reference(self) -> None:
        with self.assertRaises(GraphValidationError):
            SideEffectPolicy(
                idempotency_key_ref=k.ref(EntityKind.POLICY, "idem"),
                retry_admission=RetryAdmission.IDEMPOTENT_AUTO,
                compensation_ref=None,
            )

    def test_a_valid_policy_round_trips(self) -> None:
        value = SideEffectPolicy(idempotency_key_ref=k.ref(EntityKind.POLICY, "idem"))
        self.assertEqual(SideEffectPolicy.from_payload(value.to_payload()), value)


class SemanticPortTests(unittest.TestCase):
    def test_a_minimum_quality_class_is_normalised_to_its_value(self) -> None:
        value = k.input_port("in", type_id=VECTOR, minimum_quality_class="REVIEW")
        self.assertEqual(value.minimum_quality_class, "REVIEW")
        self.assertIs(value.quality_gate, QualityClass.REVIEW)

    def test_admits_schema_is_open_when_no_accepted_list_is_declared(self) -> None:
        self.assertTrue(k.input_port("in").admits_schema(k.ref(EntityKind.SCHEMA, "anything")))

    def test_a_named_accepted_list_gates_other_schemas(self) -> None:
        narrowed = SemanticPort(
            port_id="in",
            direction=PortDirection.INPUT,
            semantic_type=k.semantic_type(VECTOR),
            accepted_schema_refs=(k.ref(EntityKind.SCHEMA, "schema.vector", version="1.0.0"),),
        )
        self.assertTrue(narrowed.admits_schema(k.ref(EntityKind.SCHEMA, "schema.vector", version="1.0.0")))
        self.assertFalse(narrowed.admits_schema(k.ref(EntityKind.SCHEMA, "schema.other")))


class GraphNodeTests(unittest.TestCase):
    def test_a_material_role_must_declare_reproducibility(self) -> None:
        with self.assertRaises(GraphValidationError):
            GraphNode(node_id="op", role=NodeRole.OPERATION)

    def test_an_external_mutation_without_a_policy_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.node("mut", NodeRole.OPERATION, side_effect=SideEffectClass.EXTERNAL_MUTATION)

    def test_a_policy_on_a_pure_node_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.node("pure", NodeRole.OPERATION, side_effect_policy=SideEffectPolicy(idempotency_key_ref=k.ref(EntityKind.POLICY, "idem")))

    def test_an_output_declared_as_an_input_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.node("op", NodeRole.OPERATION, inputs=(k.output("bad"),))

    def test_the_port_count_is_bounded(self) -> None:
        ports = tuple(k.input_port(f"in{i}", type_id=VECTOR) for i in range(65))
        with self.assertRaises(SchemaValidationError):
            GraphNode(node_id="op", role=NodeRole.OPERATION, inputs=ports, reproducibility=ReproducibilityClass.DETERMINISTIC)

    def test_a_negative_epoch_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            k.node("op", NodeRole.OPERATION, epoch=-1)

    def test_looking_up_a_missing_port_raises(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.operation().port("ghost")


class GraphEdgeTests(unittest.TestCase):
    def test_an_edge_must_declare_a_facet(self) -> None:
        with self.assertRaises(GraphValidationError):
            GraphEdge(edge_id="e", kind=EdgeKind.MATERIAL_CAUSAL, source_node_id="a", source_port_id="out", target_node_id="b", target_port_id="in", facets=())

    def test_duplicate_facets_are_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            k.edge("e", "a", "b", facets=(DependencyFacet.CONTENT, DependencyFacet.CONTENT))

    def test_a_material_self_loop_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.edge("e", "a", "a")

    def test_touches_reports_a_facet(self) -> None:
        value = k.edge("e", "a", "b", facets=(DependencyFacet.QUALITY,))
        self.assertTrue(value.touches(DependencyFacet.QUALITY))
        self.assertFalse(value.touches(DependencyFacet.CONTENT))


class SubgraphInterfaceTests(unittest.TestCase):
    def test_duplicated_external_exports_are_refused(self) -> None:
        export = PortExport(external_port_id="out", inner_node_id="i", inner_port_id="o", direction=PortDirection.OUTPUT)
        other = PortExport(external_port_id="out", inner_node_id="i2", inner_port_id="o", direction=PortDirection.OUTPUT)
        with self.assertRaises(GraphValidationError):
            SubgraphInterface(node_id="sub", inner_graph_ref=k.ref(EntityKind.GRAPH, "inner"), exports=(export, other))


def subgraph_definition(*, interface: Any = None) -> GraphDefinition:
    sub = k.node("sub", NodeRole.SUBGRAPH, outputs=(k.output("out", type_id=VECTOR),))
    return k.definition(sub, edges=(), declared=(), interfaces=() if interface is None else (interface,))


class DefinitionStructureTests(unittest.TestCase):
    def test_the_default_chain_is_structurally_valid(self) -> None:
        self.assertEqual([n.node_id for n in k.chain_definition().nodes], ["source.logo", "render.logo", "deliver.web"])

    def test_duplicate_node_ids_are_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.definition(k.source("a", port_id="out"), k.source("a", port_id="out"), edges=(), declared=())

    def test_an_edge_naming_an_unknown_node_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.definition(k.source(), k.operation(), edges=(k.edge("e", "ghost", "render.logo"),), declared=())

    def test_an_edge_joining_two_semantic_types_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            k.definition(k.source(type_id=VECTOR), k.operation(in_type=RASTER), edges=(k.edge("e", "source.logo", "render.logo"),), declared=())
        self.assertIn("semantic types must match", str(caught.exception))

    def test_a_required_input_with_no_feeding_edge_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.definition(k.operation(), edges=(), declared=())

    def test_a_single_input_port_cannot_be_fed_twice(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            k.definition(
                k.source("a", port_id="out"),
                k.source("b", port_id="out"),
                operation("c"),
                edges=(k.edge("e1", "a", "c"), k.edge("e2", "b", "c")),
                declared=(),
            )
        self.assertIn("is ONE but 2 edges feed it", str(caught.exception))

    def test_a_many_ordered_port_needs_an_order_on_every_edge(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.definition(
                k.source("a", port_id="out"),
                k.source("b", port_id="out"),
                operation("c", cardinality=PortCardinality.MANY_ORDERED),
                edges=(k.edge("e1", "a", "c"), k.edge("e2", "b", "c")),
                declared=(),
            )

    def test_a_many_set_port_refuses_a_repeated_source(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.definition(
                k.source("a", port_id="out"),
                operation("c", cardinality=PortCardinality.MANY_SET),
                edges=(k.edge("e1", "a", "c"), k.edge("e2", "a", "c")),
                declared=(),
            )

    def test_a_material_cycle_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            k.definition(
                operation("a"), operation("b"), operation("c"),
                edges=(k.edge("e1", "a", "b"), k.edge("e2", "b", "c"), k.edge("e3", "c", "a")),
                declared=(),
            )
        self.assertIn("cyclic", str(caught.exception))

    def test_an_undeclared_epoch_crossing_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.definition(k.source("a", port_id="out"), operation("b", epoch=1), edges=(k.edge("e", "a", "b"),), declared=())

    def test_a_feedback_edge_must_point_to_an_earlier_epoch(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            k.definition(
                operation("a"), operation("b"),
                edges=(k.edge("e", "a", "b", feedback=True), k.edge("f", "b", "a")),
                declared=(),
            )
        self.assertIn("not in an earlier epoch", str(caught.exception))

    def test_a_slice_on_a_non_dirtying_edge_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.definition(
                k.source("a", port_id="out"), operation("b"),
                edges=(k.edge("e", "a", "b", kind=EdgeKind.ORDER_ONLY, slice=DependencySlice(axis="region", values=("x",))),),
                declared=(),
            )

    def test_a_decision_node_needs_two_candidates(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.definition(k.node("dec", NodeRole.DECISION, inputs=(k.input_port("a", required=False),)), edges=(), declared=())

    def test_a_subgraph_node_without_an_interface_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            subgraph_definition()

    def test_a_subgraph_node_with_an_interface_is_admitted(self) -> None:
        interface = SubgraphInterface(node_id="sub", inner_graph_ref=k.ref(EntityKind.GRAPH, "inner"))
        self.assertIs(subgraph_definition(interface=interface).node("sub").role, NodeRole.SUBGRAPH)


class GraphMutationTests(unittest.TestCase):
    def test_an_add_node_without_a_node_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            GraphMutation(kind=DeltaKind.ADD_NODE, target_id="op")

    def test_a_drop_carrying_a_payload_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            GraphMutation(kind=DeltaKind.DROP_NODE, target_id="op", node=k.operation())

    def test_a_target_that_disagrees_with_its_payload_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            GraphMutation(kind=DeltaKind.ADD_NODE, target_id="other", node=k.operation("op"))

    def test_a_mismatched_payload_name_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            GraphMutation(kind=DeltaKind.ADD_NODE, target_id="op", edge=k.edge("e", "a", "b"))


class GraphDeltaTests(unittest.TestCase):
    def test_an_empty_delta_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.delta(())

    def test_declares_recognises_a_named_external_input(self) -> None:
        value = k.delta([k.mutation(DeltaKind.ADD_DECLARED_INPUT, "asset.font")])
        self.assertTrue(value.declares(k.ref(EntityKind.ARTIFACT, "asset.font")))
        self.assertFalse(value.declares(k.ref(EntityKind.ARTIFACT, "asset.other")))

    def test_a_declared_only_delta_does_not_touch_material(self) -> None:
        self.assertFalse(k.delta([k.mutation(DeltaKind.ADD_DECLARED_INPUT, "asset.font")]).touches_material)


class GraphDefinitionApplyTests(unittest.TestCase):
    def test_apply_bumps_the_version_and_returns_a_new_definition(self) -> None:
        base = k.chain_definition()
        later = base.apply(k.delta([k.mutation(DeltaKind.ADD_DECLARED_INPUT, "asset.font")], graph_id=base.graph_id, base_version=base.version))
        self.assertEqual(later.version, base.version + 1)
        self.assertNotEqual(base, later)

    def test_applying_a_foreign_graph_is_refused(self) -> None:
        base = k.chain_definition()
        with self.assertRaises(GraphValidationError):
            base.apply(k.delta([k.mutation()], graph_id="other.graph", base_version=base.version))

    def test_applying_a_stale_base_version_is_refused(self) -> None:
        base = k.chain_definition()
        with self.assertRaises(GraphValidationError):
            base.apply(k.delta([k.mutation()], graph_id=base.graph_id, base_version=base.version + 5))

    def test_declaring_an_existing_input_does_not_duplicate_it(self) -> None:
        base = k.chain_definition()
        existing = base.declared_external_inputs[0]
        later = base.apply(k.delta([k.mutation(DeltaKind.ADD_DECLARED_INPUT, existing.reference)], graph_id=base.graph_id, base_version=base.version))
        self.assertEqual(len(later.declared_external_inputs), len(base.declared_external_inputs))

    def test_dropping_a_node_also_drops_its_edges(self) -> None:
        base = k.chain_definition()
        later = base.apply(k.delta([GraphMutation(kind=DeltaKind.DROP_NODE, target_id="deliver.web")], graph_id=base.graph_id, base_version=base.version))
        self.assertNotIn("deliver.web", [n.node_id for n in later.nodes])
        self.assertTrue(all(e.source_node_id != "deliver.web" and e.target_node_id != "deliver.web" for e in later.edges))


class GraphRevisionTests(unittest.TestCase):
    def test_a_frozen_revision_computes_its_own_digest(self) -> None:
        self.assertTrue(k.chain_revision().is_intact)

    def test_claiming_a_foreign_digest_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            GraphRevision(revision_id=k.new_id(), definition=k.chain_definition(), digest=k.digest("wrong"))

    def test_derive_cites_the_delta_and_advances_the_version(self) -> None:
        value = k.chain_revision()
        delta = k.delta([k.mutation(DeltaKind.ADD_DECLARED_INPUT, "asset.font")], graph_id=value.graph_id, base_version=value.version)
        child = value.derive(delta)
        self.assertEqual(child.version, value.version + 1)
        self.assertEqual(child.admitted_by.reference, delta.delta_id)


def gate_graph() -> Any:
    source_node = k.source(type_id=RASTER)
    deliver = k.node(
        "deliver.web",
        NodeRole.DELIVERY,
        inputs=(k.input_port("in", type_id=RASTER, minimum_quality_class="REVIEW"),),
        outputs=(k.output("out", type_id=RASTER),),
        reproducibility=ReproducibilityClass.DETERMINISTIC,
        side_effect=SideEffectClass.CONTROLLED_OUTPUTS,
    )
    defn = k.definition(source_node, deliver, edges=(k.edge("e", "source.logo", "deliver.web"),), declared=())
    records = (k.materialization("source.logo", quality_class="PREVIEW"), k.materialization("deliver.web"))
    return k.bound(records=records, revision_value=k.revision(defn))


class MaterializationGraphTests(unittest.TestCase):
    def test_two_producers_for_one_output_are_refused(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            k.bound(
                records=(k.materialization("render.logo"), k.materialization("render.logo", seed="rival")),
                revision_value=k.chain_revision(),
            )
        self.assertIn("two materializations", str(caught.exception))

    def test_an_identical_duplicate_collapse(self) -> None:
        record = k.materialization("render.logo")
        value = k.bound(records=(record, record), revision_value=k.chain_revision())
        self.assertEqual(len(value.materializations), 1)

    def test_a_materialization_for_an_unknown_node_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.bound(records=(k.materialization("ghost"),), revision_value=k.chain_revision())

    def test_an_input_port_cannot_be_materialized(self) -> None:
        with self.assertRaises(GraphValidationError):
            k.bound(records=(k.materialization("render.logo", port_id="in"),), revision_value=k.chain_revision())

    def test_a_source_below_the_port_floor_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            gate_graph()
        self.assertIn("requires REVIEW but consumes PREVIEW", str(caught.exception))

    def test_a_bound_source_at_the_floor_is_admitted(self) -> None:
        defn = k.definition(
            k.source(type_id=RASTER),
            k.node(
                "deliver.web", NodeRole.DELIVERY,
                inputs=(k.input_port("in", type_id=RASTER, minimum_quality_class="REVIEW"),),
                outputs=(k.output("out", type_id=RASTER),),
                side_effect=SideEffectClass.CONTROLLED_OUTPUTS,
            ),
            edges=(k.edge("e", "source.logo", "deliver.web"),),
            declared=(),
        )
        records = (k.materialization("source.logo", quality_class="REVIEW"), k.materialization("deliver.web"))
        value = k.bound(records=records, revision_value=k.revision(defn))
        self.assertEqual(len(value.materializations), 2)

    def test_select_variant_returns_a_new_graph_without_editing_the_old(self) -> None:
        value = k.bound(records=k.chain_records())
        later = value.select_variant("palette", "warm")
        self.assertEqual(dict(later.variant_selection)["palette"], "warm")
        self.assertEqual(value.variant_selection, ())

    def test_unresolved_inputs_report_the_missing_producer(self) -> None:
        value = k.bound(records=(k.materialization("source.logo"),), revision_value=k.chain_revision())
        unresolved = {edge.edge_id for edge in value.unresolved_inputs()}
        self.assertIn("edge.deliver", unresolved)


class FingerprintTests(unittest.TestCase):
    def test_a_rename_does_not_move_the_fingerprint(self) -> None:
        records = k.chain_records()
        plain = k.bound(records=records, revision_value=k.revision(k.chain_definition()))
        renamed_def = k.definition(
            k.source(),
            k.operation(display_name="Logo Render"),
            k.delivery(),
            edges=(k.edge("edge.render", "source.logo", "render.logo"), k.edge("edge.deliver", "render.logo", "deliver.web")),
        )
        renamed = k.bound(records=records, revision_value=k.revision(renamed_def))
        self.assertEqual(compute_fingerprint(plain, "render.logo").fingerprint, compute_fingerprint(renamed, "render.logo").fingerprint)

    def test_a_moved_input_does_move_the_fingerprint(self) -> None:
        before = k.bound(records=(k.materialization("source.logo"), k.materialization("render.logo")), revision_value=k.chain_revision())
        after = k.bound(records=(k.materialization("source.logo", seed="reimported"), k.materialization("render.logo")), revision_value=k.chain_revision())
        diff = compute_fingerprint(before, "render.logo").differs_from(compute_fingerprint(after, "render.logo"))
        self.assertTrue(any("input.source.logo" in text for text in diff))

    def test_an_empty_fingerprint_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            CausalFingerprint(node_id="op", graph_digest=k.digest("g"), components=())

    def test_a_tampered_fingerprint_is_refused(self) -> None:
        value = compute_fingerprint(k.bound(records=k.chain_records()), "render.logo")
        with self.assertRaises(GraphValidationError):
            CausalFingerprint(node_id=value.node_id, graph_digest=value.graph_digest, components=value.components, fingerprint=k.digest("tampered"))

    def test_components_are_ordered_by_text(self) -> None:
        value = compute_fingerprint(k.bound(records=k.chain_records()), "render.logo")
        texts = [item.text for item in value.components]
        self.assertEqual(texts, sorted(texts))

    def test_an_unknown_node_has_no_fingerprint(self) -> None:
        with self.assertRaises(GraphValidationError):
            compute_fingerprint(k.bound(records=k.chain_records()), "ghost")


class ImpactTests(unittest.TestCase):
    def graph(self) -> Any:
        note = operation("note", in_type=RASTER, out_type=RASTER, required=False)
        defn = k.definition(
            k.source(), k.operation(), k.delivery(), note,
            edges=(
                k.edge("edge.render", "source.logo", "render.logo"),
                k.edge("edge.deliver", "render.logo", "deliver.web"),
                k.edge("edge.note", "render.logo", "note", kind=EdgeKind.ORDER_ONLY),
            ),
        )
        return k.bound(records=k.chain_records(("source.logo", "render.logo", "deliver.web")), revision_value=k.revision(defn))

    def test_a_material_change_dirties_direct_and_transitive(self) -> None:
        cone = impact_of(self.graph(), [k.change("source.logo")])
        self.assertEqual(cone.direct, ("render.logo",))
        self.assertEqual(cone.transitive, ("deliver.web",))

    def test_a_facet_no_edge_declares_propagates_nothing(self) -> None:
        cone = impact_of(self.graph(), [k.change("source.logo", DependencyFacet.POLICY)])
        self.assertEqual(cone.requires_work, ())

    def test_an_ordering_edge_stops_the_walk(self) -> None:
        cone = impact_of(self.graph(), [k.change("source.logo")])
        self.assertNotIn("note", cone.requires_work)
        self.assertIn("note", cone.clean)

    def test_a_change_naming_an_unknown_node_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            impact_of(self.graph(), [k.change("ghost")])

    def test_no_stated_change_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            impact_of(self.graph(), [])

    def test_a_dirty_cone_without_an_explanation_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            ImpactCone(roots=("source.logo",), facets=(DependencyFacet.CONTENT,), direct=("render.logo",))

    def test_an_explanation_must_traverse_real_edges(self) -> None:
        defn = k.chain_definition()
        step = ExplainStep(changed_node_id="source.logo", facet=DependencyFacet.CONTENT, edge_id="edge.render", consumer_node_id="render.logo", effect=ImpactEffect.DIRTY_MATERIAL, reason="content moved")
        cone = ImpactCone(roots=("source.logo",), facets=(DependencyFacet.CONTENT,), direct=("render.logo",), explanation=(step,))
        self.assertTrue(cone.explains_traversal(defn))

    def test_a_fabricated_edge_in_an_explanation_is_caught(self) -> None:
        defn = k.chain_definition()
        step = ExplainStep(changed_node_id="source.logo", facet=DependencyFacet.CONTENT, edge_id="edge.ghost", consumer_node_id="render.logo", effect=ImpactEffect.DIRTY_MATERIAL, reason="made up")
        cone = ImpactCone(roots=("source.logo",), facets=(DependencyFacet.CONTENT,), direct=("render.logo",), explanation=(step,))
        self.assertFalse(cone.explains_traversal(defn))

    def test_a_replacement_change_is_recognised_as_such(self) -> None:
        self.assertTrue(k.change("n", previous="a", current="b").describes_replacement)
        self.assertFalse(k.change("n", previous="a", current="a").describes_replacement)


class DynamicAdmissionTests(unittest.TestCase):
    def test_an_admitted_receipt_without_a_receipt_id_is_refused(self) -> None:
        with self.assertRaises(PromotionBlockedError):
            k.discovery_receipt(state=DiscoveryState.ADMITTED)

    def test_content_and_semantics_are_material(self) -> None:
        value = k.discovery_receipt(facets=(DependencyFacet.SEMANTICS,))
        self.assertTrue(value.is_material)
        self.assertFalse(k.discovery_receipt(facets=(DependencyFacet.QUALITY,)).is_material)

    def test_declared_in_reads_the_definition_inputs(self) -> None:
        defn = k.chain_definition()
        declared = k.discovery_receipt(observed_reference=defn.declared_external_inputs[0])
        self.assertTrue(declared.declared_in(defn))

    def test_observing_the_same_receipt_twice_is_idempotent(self) -> None:
        ledger = DependencyLedger()
        receipt = k.discovery_receipt()
        ledger.observe(receipt)
        self.assertIs(ledger.receipt(receipt.discovery_id), receipt)

    def test_reusing_an_id_with_different_content_is_refused(self) -> None:
        ledger = DependencyLedger()
        receipt = k.discovery_receipt()
        ledger.observe(receipt)
        with self.assertRaises(GraphValidationError):
            ledger.observe(replace(receipt, consumer_node_id="deliver.web"))

    def test_an_unknown_receipt_lookup_raises(self) -> None:
        with self.assertRaises(GraphValidationError):
            DependencyLedger().receipt(k.new_id())

    def test_admission_produces_a_new_revision_without_editing_the_frozen_one(self) -> None:
        ledger = DependencyLedger()
        revision = k.chain_revision()
        receipt = k.discovery_receipt()
        ledger.observe(receipt)
        delta = k.delta([k.mutation(DeltaKind.ADD_DECLARED_INPUT, "asset.font")], graph_id=revision.graph_id, base_version=revision.version)
        admitted = ledger.admit(receipt.discovery_id, revision, delta=delta)
        self.assertEqual(admitted.version, revision.version + 1)
        self.assertEqual(revision.version, 1)
        stored = ledger.receipt(receipt.discovery_id)
        self.assertIs(stored.state, DiscoveryState.ADMITTED)
        self.assertEqual(stored.admission_receipt_id, admitted.revision_id)

    def test_admitting_a_delta_that_hides_the_read_is_refused(self) -> None:
        ledger = DependencyLedger()
        revision = k.chain_revision()
        receipt = k.discovery_receipt()
        ledger.observe(receipt)
        delta = k.delta([k.mutation(DeltaKind.ADD_DECLARED_INPUT, "asset.other")], graph_id=revision.graph_id, base_version=revision.version)
        with self.assertRaises(GraphValidationError):
            ledger.admit(receipt.discovery_id, revision, delta=delta)

    def test_a_rejected_discovery_cannot_be_admitted(self) -> None:
        ledger = DependencyLedger()
        revision = k.chain_revision()
        receipt = k.discovery_receipt(state=DiscoveryState.REJECTED)
        ledger.observe(receipt)
        delta = k.delta([k.mutation(DeltaKind.ADD_DECLARED_INPUT, "asset.font")], graph_id=revision.graph_id, base_version=revision.version)
        with self.assertRaises(PromotionBlockedError):
            ledger.admit(receipt.discovery_id, revision, delta=delta)

    def test_only_admitted_state_may_enter_a_revision(self) -> None:
        ledger = DependencyLedger()
        revision = k.chain_revision()
        receipt = k.discovery_receipt()
        ledger.observe(receipt)
        delta = k.delta([k.mutation(DeltaKind.ADD_DECLARED_INPUT, "asset.font")], graph_id=revision.graph_id, base_version=revision.version)
        with self.assertRaises(PromotionBlockedError):
            ledger.admit(receipt.discovery_id, revision, delta=delta, state=DiscoveryState.QUARANTINED)

    def test_a_delta_on_the_wrong_graph_or_version_is_refused(self) -> None:
        ledger = DependencyLedger()
        revision = k.chain_revision()
        receipt = k.discovery_receipt()
        ledger.observe(receipt)
        delta = k.delta([k.mutation(DeltaKind.ADD_DECLARED_INPUT, "asset.font")], graph_id="other.graph", base_version=revision.version)
        with self.assertRaises(GraphValidationError):
            ledger.admit(receipt.discovery_id, revision, delta=delta)

    def test_undeclared_material_lists_only_unbound_content_reads(self) -> None:
        ledger = DependencyLedger()
        revision = k.chain_revision()
        receipt = k.discovery_receipt()
        ledger.observe(receipt)
        found = ledger.undeclared_material_for(revision)
        self.assertIn(receipt.discovery_id, {item.discovery_id for item in found})


if __name__ == "__main__":
    unittest.main()
