"""Area C diff law: a snapshot diff names the kind of meaning that moved.

A file-level diff would be useless to a merge, because "the same bytes under a new
revision" and "the render changed" are different decisions for a reviewer. The ten
categories here are the frozen vocabulary, and every entry has to say which nodes it
touches so impact analysis can follow it.

Two properties get the most tests. A ``CHANGED`` entry must actually show two
different sides — an entry that claims movement while both sides agree is refused,
because that is how a diff silently inflates. And every reference is reported one by
one, never as one lump per group, because a merge resolves "this branch dropped the
rights record", not "the rights collection is different".
"""

from __future__ import annotations

import unittest
import uuid
from dataclasses import replace
from typing import Any

from iris_project_os.diffing import (
    DiffCategory,
    DiffEntry,
    DiffOperation,
    SemanticDiff,
    semantic_diff,
)
from iris_project_os.errors import (
    SchemaValidationError,
    SnapshotClosureError,
    UnsupportedVersionError,
)
from iris_project_os.graph import (
    DependencyFacet,
    MaterializationGraph,
    NodeRole,
    SubgraphInterface,
)
from iris_project_os.identity import EntityKind, ExternalRef, new_id
from iris_project_os.limits import MAX_DIFF_ENTRIES, MAX_DIFF_SUBJECT_CHARS, MAX_IMPACT_NODES
from iris_project_os.snapshots import SnapshotClass, SnapshotClosureManifest, commit_snapshot

from tests import m02_kernel_support as k

PROD = "prod.logo"
NODES = ("source.logo", "render.logo", "deliver.web")
DEFINITION = k.chain_definition()
REVISION = k.revision(DEFINITION)


def stable(seed: str) -> str:
    """A UUID that is the same on every run, so a diff can be asserted literally."""

    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


def record(node_id: str, **over: Any):
    payload: dict[str, Any] = dict(
        attempt=stable(f"attempt.{node_id}"),
        decision=k.ref(EntityKind.QUALITY_DECISION, f"decision.{node_id}"),
    )
    payload.update(over)
    return k.materialization(node_id, **payload)


def chain_nodes(**over: Any) -> tuple[Any, ...]:
    return (k.source(), k.operation(**over), k.delivery())


def chain_edges(extra: Any = ()) -> tuple[Any, ...]:
    return (
        k.edge("edge.render", "source.logo", "render.logo"),
        k.edge("edge.deliver", "render.logo", "deliver.web"),
        *extra,
    )


def graph(**over: Any) -> MaterializationGraph:
    payload: dict[str, Any] = dict(
        revision=REVISION,
        materializations=tuple(record(node_id) for node_id in NODES),
        variant_selection=(),
    )
    payload.update(over)
    return MaterializationGraph(**payload)


def closure(**over: Any) -> SnapshotClosureManifest:
    """A closure over the chain graph with one stable reference per evidence family."""

    graph_value = over.pop("graph", None) or graph()
    definition = getattr(graph_value.revision, "definition", None) or graph_value
    payload: dict[str, Any] = dict(
        project_id="iris",
        production_id=PROD,
        branch_id="branch.main",
        graph=graph_value,
        external_admissions=tuple(
            ExternalRef(kind=item.kind, reference=item.reference)
            for item in getattr(definition, "declared_external_inputs", ())
        ),
        quality_decisions=tuple(
            item.decision_ref for item in graph_value.materializations if item.decision_ref is not None
        ),
        rights_refs=(k.ref(EntityKind.RIGHTS, "rights.base"),),
        provenance_refs=(k.ref(EntityKind.PROVENANCE, "prov.base"),),
        policy_refs=(k.ref(EntityKind.POLICY, "policy.base"),),
        delivery_refs=(k.ref(EntityKind.DESTINATION, "dest.base"),),
        environment_refs=(k.ref(EntityKind.ENVIRONMENT, "env.base"),),
        tool_refs=(k.ref(EntityKind.TOOL, "tool.base"),),
        model_refs=(k.ref(EntityKind.MODEL, "model.base"),),
    )
    payload.update(over)
    return SnapshotClosureManifest(**payload)


def moved(**over: Any) -> tuple[DiffEntry, ...]:
    """The entries produced by moving the base closure to ``over``."""

    return semantic_diff(closure(), replace(closure(), **over)).entries


def between(left: Any, right: Any, **over: Any) -> SemanticDiff:
    return semantic_diff(left, right, **over)


class DiffCategoryTests(unittest.TestCase):
    def test_the_vocabulary_is_the_frozen_ten(self) -> None:
        self.assertEqual(
            {item.value for item in DiffCategory},
            {
                "GRAPH_TOPOLOGY",
                "NODE_DEFINITION",
                "DEPENDENCY_FACET",
                "VARIANT_SELECTION",
                "INTENT_BRIEF",
                "ASSET_REVISION",
                "QUALITY_DECISION",
                "RIGHTS_PROVENANCE",
                "DELIVERY_POLICY",
                "ENVIRONMENT_QUALIFICATION",
            },
        )

    def test_only_look_and_selection_may_be_carried_forward(self) -> None:
        soft = {item for item in DiffCategory if not item.blocking_by_default}
        self.assertEqual(soft, {DiffCategory.VARIANT_SELECTION, DiffCategory.ENVIRONMENT_QUALIFICATION})

    def test_eight_categories_change_what_the_production_is(self) -> None:
        self.assertEqual(len([item for item in DiffCategory if item.blocking_by_default]), 8)

    def test_a_category_is_parsed_from_its_text(self) -> None:
        self.assertIs(DiffCategory.parse("asset_revision", "category"), DiffCategory.ASSET_REVISION)

    def test_an_invented_category_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            DiffCategory.parse("OTHER_STUFF", "category")


class DiffOperationTests(unittest.TestCase):
    def test_the_three_operations_are_all_there_is(self) -> None:
        self.assertEqual({item.value for item in DiffOperation}, {"ADDED", "CHANGED", "REMOVED"})

    def test_an_invented_operation_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            DiffOperation.parse("RENAMED", "operation")


class DiffEntryTests(unittest.TestCase):
    def entry(self, **over: Any) -> DiffEntry:
        payload: dict[str, Any] = dict(
            category=DiffCategory.ASSET_REVISION,
            operation=DiffOperation.CHANGED,
            subject="render.logo.out",
            before=k.digest("before"),
            after=k.digest("after"),
        )
        payload.update(over)
        return DiffEntry(**payload)

    def test_the_category_and_operation_arrive_as_text(self) -> None:
        value = self.entry(category="rights_provenance", operation="added", before=None)
        self.assertIs(value.category, DiffCategory.RIGHTS_PROVENANCE)
        self.assertIs(value.operation, DiffOperation.ADDED)

    def test_blocking_defaults_to_what_the_category_means(self) -> None:
        self.assertTrue(self.entry().blocking)
        self.assertFalse(self.entry(category=DiffCategory.VARIANT_SELECTION).blocking)

    def test_blocking_may_be_overridden_in_either_direction(self) -> None:
        self.assertFalse(self.entry(blocking=False).blocking)
        self.assertTrue(self.entry(category=DiffCategory.VARIANT_SELECTION, blocking=True).blocking)

    def test_a_non_boolean_blocking_flag_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.entry(blocking="yes")

    def test_the_subject_is_bounded_text(self) -> None:
        self.assertEqual(self.entry(subject="x" * MAX_DIFF_SUBJECT_CHARS).subject, "x" * MAX_DIFF_SUBJECT_CHARS)
        with self.assertRaises(SchemaValidationError):
            self.entry(subject="x" * (MAX_DIFF_SUBJECT_CHARS + 1))

    def test_an_empty_subject_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.entry(subject="")

    def test_node_ids_are_deduplicated_and_ordered(self) -> None:
        value = self.entry(node_ids=("render.logo", "source.logo", "render.logo"))
        self.assertEqual(value.node_ids, ("render.logo", "source.logo"))

    def test_a_forged_node_id_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.entry(node_ids=("Render Node",))

    def test_the_node_width_of_one_entry_is_bounded(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.entry(node_ids=tuple(f"node.{index}" for index in range(MAX_IMPACT_NODES + 1)))

    def test_a_facet_is_stored_as_its_value(self) -> None:
        self.assertEqual(self.entry(facet=DependencyFacet.CONTENT).facet, "CONTENT")
        self.assertEqual(self.entry(facet="rights").facet, "RIGHTS")

    def test_an_invented_facet_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.entry(facet="VIBES")

    def test_a_change_that_shows_two_agreeing_sides_is_refused(self) -> None:
        with self.assertRaises(SnapshotClosureError) as caught:
            self.entry(before=k.digest("same"), after=k.digest("same"))
        self.assertIn("claims CHANGED while both sides agree", str(caught.exception))

    def test_a_change_with_both_sides_missing_is_refused(self) -> None:
        with self.assertRaises(SnapshotClosureError):
            self.entry(before=None, after=None)

    def test_an_addition_may_leave_the_missing_side_empty(self) -> None:
        value = self.entry(operation=DiffOperation.ADDED, before=None)
        self.assertIsNone(value.before)

    def test_a_reference_side_is_stored_as_its_text(self) -> None:
        value = self.entry(before=k.ref(EntityKind.RIGHTS, "rights.a"), after=k.ref(EntityKind.RIGHTS, "rights.b"))
        self.assertEqual(value.before, "rights:rights.a")
        self.assertEqual(value.after, "rights:rights.b")

    def test_a_collection_side_is_canonicalised_text(self) -> None:
        value = self.entry(before=[k.ref(EntityKind.RIGHTS, "rights.b"), "x"], after="y")
        self.assertEqual(value.before, '["rights:rights.b","x"]')

    def test_a_structured_side_that_is_not_text_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.entry(before=object())

    def test_a_boolean_side_is_refused_as_ambiguous(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.entry(before=True, after=False)

    def test_a_number_is_recorded_as_text_not_as_its_type(self) -> None:
        self.assertEqual(self.entry(before=7, after=8).before, "7")

    def test_the_key_and_text_agree_with_the_classification(self) -> None:
        value = self.entry()
        self.assertEqual(value.key, ("ASSET_REVISION", "CHANGED", "render.logo.out"))
        self.assertEqual(value.text, "ASSET_REVISION:CHANGED:render.logo.out")

    def test_an_entry_survives_a_serialisation_round_trip(self) -> None:
        value = self.entry(node_ids=("render.logo",), facet=DependencyFacet.QUALITY)
        self.assertEqual(DiffEntry.from_payload(value.to_payload()), value)

    def test_an_unknown_field_is_refused_rather_than_dropped(self) -> None:
        with self.assertRaises(SchemaValidationError):
            DiffEntry.from_payload({**self.entry().to_payload(), "notes": "typo"})


class SemanticDiffConstructionTests(unittest.TestCase):
    def diff(self, entries: Any = (), **over: Any) -> SemanticDiff:
        payload: dict[str, Any] = dict(
            diff_id=new_id(), base_digest=k.digest("base"), target_digest=k.digest("target"), entries=entries
        )
        payload.update(over)
        return SemanticDiff(**payload)

    def entry(self, subject: str = "render.logo.out", **over: Any) -> DiffEntry:
        payload: dict[str, Any] = dict(
            category=DiffCategory.ASSET_REVISION,
            operation=DiffOperation.CHANGED,
            subject=subject,
            before=k.digest("before"),
            after=k.digest("after"),
        )
        payload.update(over)
        return DiffEntry(**payload)

    def test_an_empty_diff_is_a_real_answer_not_a_missing_one(self) -> None:
        value = self.diff()
        self.assertTrue(value.is_empty)
        self.assertEqual(value.entries, ())
        self.assertEqual(value.categories, ())
        self.assertEqual(value.blocking, ())
        self.assertEqual(value.affected_nodes, ())

    def test_the_diff_id_must_be_a_uuid(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.diff(diff_id="diff-1")

    def test_both_sides_must_be_digests(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.diff(base_digest="latest")
        with self.assertRaises(SchemaValidationError):
            self.diff(target_digest="latest")

    def test_an_unsupported_contract_version_is_refused(self) -> None:
        with self.assertRaises(UnsupportedVersionError):
            self.diff(contract_version="m02-contract-v9.9")

    def test_the_same_movement_may_not_be_reported_twice(self) -> None:
        with self.assertRaises(SnapshotClosureError) as caught:
            self.diff(entries=(self.entry(), self.entry()))
        self.assertIn("diff reports ASSET_REVISION:CHANGED:render.logo.out twice", str(caught.exception))

    def test_a_second_report_of_the_same_subject_under_another_category_is_legal(self) -> None:
        value = self.diff(entries=(self.entry(), self.entry(category=DiffCategory.QUALITY_DECISION)))
        self.assertEqual(len(value.entries), 2)

    def test_entries_are_ordered_by_their_text(self) -> None:
        value = self.diff(entries=(self.entry("z.out"), self.entry("a.out")))
        self.assertEqual([item.subject for item in value.entries], ["a.out", "z.out"])

    def test_the_diff_width_is_bounded(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.diff(entries=tuple(self.entry(f"node.{index}.out") for index in range(MAX_DIFF_ENTRIES + 1)))

    def test_the_views_aggregate_the_entries(self) -> None:
        value = self.diff(
            entries=(
                self.entry(node_ids=("render.logo",)),
                self.entry("deliver.web.out", category=DiffCategory.VARIANT_SELECTION, node_ids=("deliver.web",)),
            )
        )
        self.assertEqual([item.value for item in value.categories], ["ASSET_REVISION", "VARIANT_SELECTION"])
        self.assertEqual(len(value.blocking), 1)
        self.assertEqual(value.affected_nodes, ("deliver.web", "render.logo"))
        self.assertTrue(value.touches("asset_revision"))
        self.assertFalse(value.touches("intent_brief"))
        self.assertEqual(len(value.entries_in(DiffCategory.ASSET_REVISION)), 1)

    def test_filtering_by_an_invented_category_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.diff(entries=(self.entry(),)).entries_in("SOMETHING_ELSE")

    def test_the_digest_covers_the_movements_not_the_identity_of_the_report(self) -> None:
        entries = (self.entry(), self.entry("deliver.web.out"))
        self.assertEqual(self.diff(entries=entries).digest(), self.diff(diff_id=new_id(), entries=entries).digest())
        self.assertEqual(self.diff(entries=entries).digest(), self.diff(entries=tuple(reversed(entries))).digest())

    def test_a_diff_survives_a_serialisation_round_trip(self) -> None:
        value = self.diff(entries=(self.entry(node_ids=("render.logo",)),))
        self.assertEqual(SemanticDiff.from_payload(value.to_payload()), value)


class SemanticDiffGraphTests(unittest.TestCase):
    def test_two_agreeing_closures_produce_no_entries(self) -> None:
        self.assertEqual(between(closure(), closure()).entries, ())

    def test_the_sides_are_recorded_as_closure_digests(self) -> None:
        left, right = closure(), replace(closure(), rights_refs=(k.ref(EntityKind.RIGHTS, "rights.other"),))
        value = between(left, right)
        self.assertEqual(value.base_digest, left.digest)
        self.assertEqual(value.target_digest, right.digest)

    def test_ownership_and_parentage_are_not_semantic_movement(self) -> None:
        value = between(
            closure(),
            replace(
                closure(),
                branch_id="branch.other",
                production_id="prod.other",
                project_id="other",
                ancestry=(new_id(),),
                parent_snapshot_ids=(new_id(),),
            ),
        )
        self.assertTrue(value.is_empty)

    def test_a_new_node_is_reported_as_topology_not_definition(self) -> None:
        extra = graph(
            revision=k.revision(k.definition(*chain_nodes(), k.source("source.fonts"), edges=chain_edges())),
            materializations=tuple(record(node_id) for node_id in NODES) + (record("source.fonts"),),
        )
        found = between(closure(), closure(graph=extra)).entries
        entry = next(item for item in found if item.subject == "source.fonts")
        self.assertIs(entry.category, DiffCategory.GRAPH_TOPOLOGY)
        self.assertIs(entry.operation, DiffOperation.ADDED)
        self.assertEqual(entry.node_ids, ("source.fonts",))

    def test_a_dropped_node_is_reported_as_removed_topology(self) -> None:
        smaller = graph(
            revision=k.revision(
                k.definition(
                    k.source(),
                    k.operation(),
                    edges=(k.edge("edge.render", "source.logo", "render.logo"),),
                )
            ),
            materializations=tuple(record(node_id) for node_id in ("source.logo", "render.logo")),
        )
        found = between(closure(), closure(graph=smaller)).entries
        removed = [item for item in found if item.operation is DiffOperation.REMOVED]
        self.assertIn("deliver.web", [item.subject for item in removed])
        self.assertIn("edge.deliver", [item.subject for item in removed])

    def test_a_redefined_node_is_a_definition_change_with_both_digests(self) -> None:
        edited = graph(revision=k.revision(k.definition(*chain_nodes(display_name="Render v2"), edges=chain_edges())))
        entry = next(
            item for item in between(closure(), closure(graph=edited)).entries if item.subject == "render.logo"
        )
        self.assertIs(entry.category, DiffCategory.NODE_DEFINITION)
        self.assertIs(entry.operation, DiffOperation.CHANGED)
        self.assertNotEqual(entry.before, entry.after)

    def test_a_new_node_and_its_dependency_are_reported_as_topology(self) -> None:
        grown = graph(
            revision=k.revision(
                k.definition(
                    *chain_nodes(),
                    k.operation("render.alt", in_type=k.RASTER, out_type=k.RASTER),
                    edges=chain_edges() + (k.edge("edge.alt", "render.logo", "render.alt"),),
                )
            )
        )
        found = between(closure(), closure(graph=grown)).entries
        by_subject = {item.subject: item for item in found}
        self.assertIs(by_subject["render.alt"].category, DiffCategory.GRAPH_TOPOLOGY)
        self.assertIs(by_subject["render.alt"].operation, DiffOperation.ADDED)
        self.assertIs(by_subject["edge.alt"].category, DiffCategory.GRAPH_TOPOLOGY)
        self.assertIs(by_subject["edge.alt"].operation, DiffOperation.ADDED)

    def test_an_edited_dependency_is_a_facet_move_naming_both_endpoints(self) -> None:
        facetted = graph(
            revision=k.revision(
                k.definition(
                    *chain_nodes(),
                    edges=(
                        k.edge("edge.render", "source.logo", "render.logo", facets=(DependencyFacet.SEMANTICS,)),
                        k.edge("edge.deliver", "render.logo", "deliver.web"),
                    ),
                )
            ),
        )
        entry = next(
            item for item in between(closure(), closure(graph=facetted)).entries if item.subject == "edge.render"
        )
        self.assertIs(entry.category, DiffCategory.DEPENDENCY_FACET)
        self.assertEqual(entry.node_ids, ("render.logo", "source.logo"))

    def test_a_moved_declared_input_is_named_by_reference(self) -> None:
        widened = graph(
            revision=k.revision(
                k.definition(
                    *chain_nodes(),
                    edges=chain_edges(),
                    declared=DEFINITION.declared_external_inputs
                    + (k.ref(EntityKind.ARTIFACT, "asset.fonts"),),
                )
            ),
        )
        entry = next(
            item for item in between(closure(), closure(graph=widened)).entries if "asset.fonts" in item.subject
        )
        self.assertIs(entry.category, DiffCategory.GRAPH_TOPOLOGY)
        self.assertIs(entry.operation, DiffOperation.ADDED)

    def test_a_subgraph_boundary_is_reported_separately_from_its_node(self) -> None:
        kit = k.node(
            "sub.kit",
            NodeRole.SUBGRAPH,
            inputs=(k.input_port("in", type_id=k.VECTOR),),
            outputs=(k.output("out", type_id=k.RASTER),),
        )
        iface = SubgraphInterface(node_id="sub.kit", inner_graph_ref=k.ref(EntityKind.GRAPH, "graph.kit"))
        wider = graph(
            revision=k.revision(
                k.definition(
                    k.source(),
                    kit,
                    edges=(k.edge("edge.kit", "source.logo", "sub.kit"),),
                    interfaces=(iface,),
                )
            ),
            materializations=(record("source.logo"), record("sub.kit")),
        )
        found = between(closure(), closure(graph=wider)).entries
        self.assertIn("interface:sub.kit", [item.subject for item in found])

    def test_several_movements_are_each_reported(self) -> None:
        wider = graph(
            revision=k.revision(
                k.definition(
                    *chain_nodes(display_name="Render v2"),
                    k.operation("render.alt", in_type=k.VECTOR, out_type=k.RASTER),
                    edges=chain_edges() + (k.edge("edge.alt", "source.logo", "render.alt"),),
                )
            ),
            materializations=tuple(record(node_id) for node_id in NODES) + (record("render.alt"),),
        )
        found = between(closure(), closure(graph=wider)).entries
        categories = {item.category for item in found}
        self.assertEqual(
            categories,
            {
                DiffCategory.GRAPH_TOPOLOGY,
                DiffCategory.NODE_DEFINITION,
                DiffCategory.ASSET_REVISION,
                DiffCategory.QUALITY_DECISION,
            },
        )
        self.assertEqual(len(found), 5)


class SemanticDiffSelectionTests(unittest.TestCase):
    def test_a_selection_switch_is_non_blocking(self) -> None:
        found = moved(graph=graph(variant_selection=(("variant.outfit", "web"),)))
        entry = next(item for item in found if item.category is DiffCategory.VARIANT_SELECTION)
        self.assertIs(entry.operation, DiffOperation.ADDED)
        self.assertFalse(entry.blocking)
        self.assertEqual(entry.after, "web")

    def test_a_selection_change_names_both_options(self) -> None:
        left = graph(variant_selection=(("variant.outfit", "web"),))
        right = graph(variant_selection=(("variant.outfit", "print"),))
        entry = next(
            item
            for item in between(closure(graph=left), closure(graph=right)).entries
            if item.category is DiffCategory.VARIANT_SELECTION
        )
        self.assertIs(entry.operation, DiffOperation.CHANGED)
        self.assertEqual((entry.before, entry.after), ("web", "print"))

    def test_a_dropped_selection_is_a_removal(self) -> None:
        left = graph(variant_selection=(("variant.outfit", "web"),))
        found = between(closure(graph=left), closure()).entries
        entry = next(item for item in found if item.category is DiffCategory.VARIANT_SELECTION)
        self.assertIs(entry.operation, DiffOperation.REMOVED)

    def test_the_intent_brief_moving_is_blocking(self) -> None:
        entry = next(item for item in moved(intent_ref=k.ref(EntityKind.INTENT, "intent.b")) if item.subject == "intent")
        self.assertIs(entry.category, DiffCategory.INTENT_BRIEF)
        self.assertTrue(entry.blocking)
        self.assertEqual(entry.after, "intent:intent.b")


class SemanticDiffMaterializationTests(unittest.TestCase):
    def test_a_newly_materialized_port_is_an_added_asset(self) -> None:
        wider = graph(
            revision=k.revision(k.definition(*chain_nodes(), k.source("source.fonts"), edges=chain_edges())),
            materializations=tuple(record(node_id) for node_id in NODES) + (record("source.fonts"),),
        )
        entry = next(
            item
            for item in between(closure(), closure(graph=wider)).entries
            if item.subject == "source.fonts.out"
        )
        self.assertIs(entry.category, DiffCategory.ASSET_REVISION)
        self.assertIs(entry.operation, DiffOperation.ADDED)
        self.assertIsNone(entry.before)

    def test_a_lost_materialization_is_a_removal(self) -> None:
        smaller = graph(materializations=tuple(record(node_id) for node_id in ("source.logo", "render.logo")))
        entry = next(
            item
            for item in between(closure(), closure(graph=smaller)).entries
            if item.subject == "deliver.web.out"
        )
        self.assertIs(entry.operation, DiffOperation.REMOVED)
        self.assertIsNone(entry.after)

    def test_a_re_render_moves_the_asset_by_digest(self) -> None:
        redrawn = graph(
            materializations=tuple(
                record(node_id, seed=f"{node_id}.take.two") if node_id == "render.logo" else record(node_id)
                for node_id in NODES
            )
        )
        entry = next(
            item
            for item in between(closure(), closure(graph=redrawn)).entries
            if item.category is DiffCategory.ASSET_REVISION
        )
        self.assertIs(entry.operation, DiffOperation.CHANGED)
        self.assertEqual(entry.node_ids, ("render.logo",))
        self.assertNotEqual(entry.before, entry.after)

    def test_the_same_bytes_under_a_new_revision_still_count_as_a_move(self) -> None:
        relabelled = graph(
            materializations=tuple(
                record(node_id, revision_reference="rev.render.logo.out.v2")
                if node_id == "render.logo"
                else record(node_id)
                for node_id in NODES
            )
        )
        entry = next(
            item
            for item in between(closure(), closure(graph=relabelled)).entries
            if item.category is DiffCategory.ASSET_REVISION
        )
        self.assertIs(entry.operation, DiffOperation.CHANGED)
        self.assertEqual(entry.before, "revision:rev.render.logo.out@1")
        self.assertEqual(entry.after, "revision:rev.render.logo.out.v2@1")

    def test_a_reclassifying_judgement_moves_the_quality_evidence(self) -> None:
        judged = graph(
            materializations=tuple(
                record(node_id, quality_class="MASTER") if node_id == "render.logo" else record(node_id)
                for node_id in NODES
            )
        )
        entry = next(
            item
            for item in between(closure(), closure(graph=judged)).entries
            if item.category is DiffCategory.QUALITY_DECISION
        )
        self.assertIsNone(entry.before)
        self.assertEqual(entry.after, "MASTER")

    def test_a_repeated_judgement_of_the_same_class_still_names_both_decisions(self) -> None:
        rejudged = graph(
            materializations=tuple(
                record(node_id, decision=k.ref(EntityKind.QUALITY_DECISION, "decision.second"))
                if node_id == "render.logo"
                else record(node_id)
                for node_id in NODES
            )
        )
        entry = next(
            item
            for item in between(closure(), closure(graph=rejudged)).entries
            if item.category is DiffCategory.QUALITY_DECISION and item.subject == "render.logo.out"
        )
        self.assertIs(entry.operation, DiffOperation.CHANGED)
        self.assertEqual(entry.before, "quality_decision:decision.render.logo")
        self.assertEqual(entry.after, "quality_decision:decision.second")

    def test_a_different_tool_is_environment_qualification_and_does_not_block(self) -> None:
        tool = k.ref(EntityKind.TOOL, "tool.blender")
        retooled = graph(
            materializations=tuple(
                record(node_id, tools=(tool,)) if node_id == "render.logo" else record(node_id) for node_id in NODES
            )
        )
        entry = next(item for item in between(closure(), closure(graph=retooled)).entries if "tool.blender" in item.subject)
        self.assertIs(entry.category, DiffCategory.ENVIRONMENT_QUALIFICATION)
        self.assertIs(entry.operation, DiffOperation.ADDED)
        self.assertFalse(entry.blocking)

    def test_a_moved_asset_and_a_moved_verdict_are_two_entries(self) -> None:
        redrawn = graph(
            materializations=tuple(
                record(
                    node_id,
                    seed="take.two",
                    quality_class="MASTER",
                    decision=k.ref(EntityKind.QUALITY_DECISION, "decision.other"),
                )
                if node_id == "render.logo"
                else record(node_id)
                for node_id in NODES
            )
        )
        found = between(closure(), closure(graph=redrawn)).entries
        subjects = {(item.subject, item.category.value) for item in found}
        self.assertIn(("render.logo.out", "ASSET_REVISION"), subjects)
        self.assertIn(("render.logo.out", "QUALITY_DECISION"), subjects)
        self.assertEqual(len(found), 4)


class SemanticDiffReferenceTests(unittest.TestCase):
    def group(self, name: str, text: str) -> tuple[DiffEntry, ...]:
        return tuple(item for item in moved(**{name: (k.ref(EntityKind.RIGHTS, text),)}) if item.subject.startswith(name))

    def test_a_dropped_rights_record_is_named_as_its_own_entry(self) -> None:
        found = self.group("rights_refs", "rights.replacement")
        entry = next(item for item in found if item.operation is DiffOperation.REMOVED)
        self.assertIs(entry.category, DiffCategory.RIGHTS_PROVENANCE)
        self.assertEqual(entry.before, "rights:rights.base")
        self.assertIsNone(entry.after)

    def test_a_added_reference_names_the_group_it_lives_in(self) -> None:
        found = moved(rights_refs=(k.ref(EntityKind.RIGHTS, "rights.base"), k.ref(EntityKind.RIGHTS, "rights.new")))
        self.assertEqual([item.subject for item in found], ["rights_refs:rights:rights.new"])
        self.assertIs(found[0].operation, DiffOperation.ADDED)
        self.assertIsNone(found[0].before)

    def test_every_family_has_its_own_category(self) -> None:
        table = {
            "quality_decisions": DiffCategory.QUALITY_DECISION,
            "rights_refs": DiffCategory.RIGHTS_PROVENANCE,
            "provenance_refs": DiffCategory.RIGHTS_PROVENANCE,
            "delivery_refs": DiffCategory.DELIVERY_POLICY,
            "policy_refs": DiffCategory.DELIVERY_POLICY,
            "model_refs": DiffCategory.ENVIRONMENT_QUALIFICATION,
            "tool_refs": DiffCategory.ENVIRONMENT_QUALIFICATION,
        }
        for name, category in table.items():
            with self.subTest(group=name):
                entry = next(
                    item for item in moved(**{name: (k.ref(EntityKind.RIGHTS, "group.other"),)}) if item.subject.startswith(name)
                )
                self.assertIs(entry.category, category)

    def test_one_entry_per_moved_reference_never_one_per_group(self) -> None:
        found = moved(
            rights_refs=(
                k.ref(EntityKind.RIGHTS, "rights.base"),
                k.ref(EntityKind.RIGHTS, "rights.one"),
                k.ref(EntityKind.RIGHTS, "rights.two"),
            )
        )
        self.assertEqual(len(found), 2)
        self.assertEqual({item.operation for item in found}, {DiffOperation.ADDED})

    def test_a_re_ordered_group_is_not_a_change(self) -> None:
        left = closure(rights_refs=(k.ref(EntityKind.RIGHTS, "rights.a"), k.ref(EntityKind.RIGHTS, "rights.b")))
        right = closure(rights_refs=(k.ref(EntityKind.RIGHTS, "rights.b"), k.ref(EntityKind.RIGHTS, "rights.a")))
        self.assertTrue(between(left, right).is_empty)

    def test_a_re_qualified_environment_is_reported_but_does_not_block(self) -> None:
        entry = next(item for item in moved(environment_fingerprint=k.digest("linux-arm")) if item.subject == "environment")
        self.assertIs(entry.category, DiffCategory.ENVIRONMENT_QUALIFICATION)
        self.assertIs(entry.operation, DiffOperation.CHANGED)
        self.assertFalse(entry.blocking)


class SemanticDiffInputTests(unittest.TestCase):
    def test_operands_that_are_not_closures_are_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            semantic_diff(DEFINITION, closure())
        self.assertIn("expects two snapshots or two closure manifests", str(caught.exception))

    def test_snapshots_may_be_compared_directly(self) -> None:
        left = commit_snapshot(closure(), snapshot_class=SnapshotClass.VALIDATED_SNAPSHOT)
        right = commit_snapshot(
            replace(closure(), rights_refs=(k.ref(EntityKind.RIGHTS, "rights.other"),)),
            snapshot_class=SnapshotClass.VALIDATED_SNAPSHOT,
        )
        value = between(left, right)
        self.assertEqual(value.base_digest, left.closure.digest)
        self.assertEqual(len(value.entries), 2)

    def test_direction_is_part_of_the_report(self) -> None:
        left = closure()
        right = replace(left, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.other"),))
        forward = {item.subject: item.operation.value for item in between(left, right).entries}
        backward = {item.subject: item.operation.value for item in between(right, left).entries}
        self.assertEqual(forward.keys(), backward.keys())
        self.assertEqual(forward["rights_refs:rights:rights.base"], "REMOVED")
        self.assertEqual(backward["rights_refs:rights:rights.base"], "ADDED")

    def test_an_explicit_diff_id_is_honoured(self) -> None:
        wanted = new_id()
        value = between(closure(), replace(closure(), rights_refs=()), diff_id=wanted)
        self.assertEqual(value.diff_id, wanted)
        self.assertEqual(len(value.entries), 1)

    def test_a_forged_diff_id_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            between(closure(), replace(closure(), rights_refs=()), diff_id="diff-1")


if __name__ == "__main__":
    unittest.main()
