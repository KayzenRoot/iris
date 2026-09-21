"""Area D build semantics: states, deltas, frontiers, plans, journals and the oracle.

These are the tests for the frozen contract in
planning/modules/M02-PROJECT-OS-PRODUCTION-GRAPH.md section 4 and the invariants
D-M02-S04-001 to D-M02-S04-006. Every test is shaped the same way: state what the
planner is allowed to conclude, then try to make it conclude more than that and
require either a refusal that names itself or a reason a reader can argue with.
"""

from __future__ import annotations

import unittest

from tests import m02_kernel_support as k
from iris_project_os.analysis import compute_fingerprint, impact_of
from iris_project_os.build import (
    BuildDelta,
    BuildExplainTrace,
    BuildJournal,
    BuildPlan,
    BuildState,
    BuildStep,
    CacheLookup,
    CoalescedBatch,
    DirtyFrontier,
    DirtyNode,
    IncrementalVerdict,
    JournalEvent,
    JournalKind,
    NodeComparison,
    OutputCommitMode,
    RecoveryClass,
    RecoveryVerdict,
    RepairFrontier,
    RepairTarget,
    ShadowResult,
    SharedWork,
    VariantCandidate,
    WorkDisposition,
    audit_shadow_rebuilds,
    coalesce_variants,
    compile_build_delta,
    dirty_frontier,
    explain_build,
    plan_build,
    repair_frontier,
    verify_incremental,
)
from iris_project_os.diffing import DiffCategory, DiffEntry, DiffOperation, SemanticDiff
from iris_project_os.errors import BuildError, SchemaValidationError
from iris_project_os.graph import (
    DependencyFacet,
    DependencySlice,
    EdgeKind,
    GraphRevision,
    MaterializationGraph,
    NodeRole,
    ReproducibilityClass,
)
from iris_project_os.identity import EntityKind
from iris_project_os.reuse import (
    CacheCheck,
    CacheLayer,
    OriginClass,
    PoisonCheck,
    QuarantineLedger,
    QuarantineRule,
    ReuseClass,
    ReuseRejection,
    ReuseReceipt,
    admit_reuse,
)
from iris_project_os.versions import canonical_json, content_digest

NOW = k.CACHE_NOW
REGION = DependencySlice(axis="region", values=("left",))
ELSEWHERE = DependencySlice(axis="region", values=("right",))
LOCALE = DependencySlice(axis="locale", values=("pt-br",))


def rev(tag: str = "a", version: str = "1") -> k.ExternalRef:
    return k.ref(EntityKind.REVISION, f"rev.{tag}", version)


def stated(*changes: k.Change, **over) -> BuildDelta:
    base = dict(graph_id="graph.test", base_revision=rev("a"), target_revision=rev("b"))
    base.update(over)
    base["changes"] = tuple(changes)
    return BuildDelta(**base)


def rebuild(node_id: str = "render.logo", **over) -> BuildStep:
    base = dict(
        node_id=node_id,
        state=BuildState.DIRTY,
        disposition=WorkDisposition.REBUILD,
        reasons=(f"{node_id} is inside the impact cone",),
        outputs=("out",),
        reproducibility=ReproducibilityClass.DETERMINISTIC,
    )
    base.update(over)
    return BuildStep(**base)


def reuse(graph: MaterializationGraph, node_id: str = "render.logo", **over) -> BuildStep:
    layer = over.pop("layer", CacheLayer.INTERMEDIATE)
    granted = k.admitted_receipt(graph, node_id, layer=layer)
    base = dict(
        node_id=node_id,
        state=BuildState.CACHED_ELIGIBLE,
        disposition=WorkDisposition.REUSE,
        reasons=("the cache holds exactly this claim",),
        key=granted.key,
        receipt=granted,
        outputs=("out",),
        reproducibility=ReproducibilityClass.DETERMINISTIC,
    )
    base.update(over)
    return BuildStep(**base)


def decide(*steps: BuildStep, delta: BuildDelta | None = None) -> BuildPlan:
    return BuildPlan(
        plan_id=k.new_id(),
        graph_id="graph.test",
        base_revision=rev("a"),
        target_revision=rev("b"),
        steps=tuple(steps),
        delta_digest=None if delta is None else delta.delta_digest,
    )


def named_hit(graph: MaterializationGraph, node_id: str, entry, **over) -> BuildPlan:
    """Plan one named-dirty node against one cache entry, with the trust policy it needs."""

    base = dict(trust=k.cache_trust(), context=k.cache_context(), now_ms=NOW)
    base.update(over)
    return plan_build(graph, states={node_id: BuildState.DIRTY}, cache=(entry,), **base)


class StateAndDispositionVocabulary(unittest.TestCase):
    """Seven states and six dispositions, with no implicit eighth of either."""

    def test_the_seven_states_are_the_whole_vocabulary(self) -> None:
        self.assertEqual(
            sorted(state.value for state in BuildState),
            [
                "BLOCKED",
                "CACHED_ELIGIBLE",
                "CLEAN",
                "DIRTY",
                "REPACKAGE_ONLY",
                "REVALIDATE_ONLY",
                "UNKNOWN",
            ],
        )
        self.assertEqual(
            sorted(item.value for item in WorkDisposition),
            ["BLOCK", "REBUILD", "REPACKAGE", "REPAIR", "REUSE", "REVALIDATE"],
        )

    def test_unknown_and_blocked_are_the_only_two_states_that_fail_closed(self) -> None:
        failing = [state.value for state in BuildState if state.fails_closed]
        self.assertEqual(failing, ["UNKNOWN", "BLOCKED"])
        for state in BuildState:
            if state.fails_closed:
                self.assertEqual(state.legal_dispositions, (WorkDisposition.BLOCK,))

    def test_each_state_names_only_the_dispositions_that_make_sense_on_it(self) -> None:
        expected = {
            BuildState.UNKNOWN: {WorkDisposition.BLOCK},
            BuildState.BLOCKED: {WorkDisposition.BLOCK},
            BuildState.CLEAN: {WorkDisposition.REUSE},
            BuildState.DIRTY: {
                WorkDisposition.REBUILD,
                WorkDisposition.REPAIR,
                WorkDisposition.REUSE,
                WorkDisposition.BLOCK,
            },
            BuildState.CACHED_ELIGIBLE: {WorkDisposition.REUSE, WorkDisposition.REBUILD},
            BuildState.REVALIDATE_ONLY: {WorkDisposition.REVALIDATE, WorkDisposition.BLOCK},
            BuildState.REPACKAGE_ONLY: {WorkDisposition.REPACKAGE, WorkDisposition.BLOCK},
        }
        self.assertEqual(set(expected), set(BuildState))
        for state, allowed in expected.items():
            with self.subTest(state=state.value):
                self.assertEqual(set(state.legal_dispositions), allowed)
                for disposition in WorkDisposition:
                    self.assertEqual(state.admits(disposition), disposition in allowed)

    def test_a_state_answers_a_string_disposition_the_same_way(self) -> None:
        self.assertTrue(BuildState.DIRTY.admits("BLOCK"))
        self.assertFalse(BuildState.CLEAN.admits("REBUILD"))
        with self.assertRaises(SchemaValidationError):
            BuildState.CLEAN.admits("MAYBE")

    def test_which_states_claim_the_bytes_are_already_the_answer(self) -> None:
        claiming = sorted(state.value for state in BuildState if state.claims_current)
        self.assertEqual(claiming, ["CACHED_ELIGIBLE", "CLEAN"])
        working = sorted(state.value for state in BuildState if state.needs_work)
        self.assertEqual(working, ["DIRTY", "REPACKAGE_ONLY", "REVALIDATE_ONLY"])
        self.assertEqual([state.value for state in BuildState if state.emits_new_bytes], ["DIRTY"])

    def test_only_rebuild_repair_and_repackage_rewrite_material_output(self) -> None:
        emitting = sorted(item.value for item in WorkDisposition if item.emits_new_bytes)
        self.assertEqual(emitting, ["REBUILD", "REPACKAGE", "REPAIR"])
        self.assertFalse(
            WorkDisposition.REVALIDATE.emits_new_bytes,
            "re-attesting evidence rewrites no material bytes",
        )
        self.assertEqual([item.value for item in WorkDisposition if item.avoids_work], ["REUSE"])
        self.assertEqual([item.value for item in WorkDisposition if not item.may_proceed], ["BLOCK"])

    def test_a_claim_to_existing_bytes_always_stands_on_a_receipt(self) -> None:
        self.assertEqual(
            [item.value for item in WorkDisposition if item.requires_receipt], ["REUSE"]
        )
        self.assertEqual(
            [item.value for item in WorkDisposition if item.requires_slice], ["REPAIR"]
        )


class BuildDeltaCompilation(unittest.TestCase):
    """A diff compiles into causes, and each category keeps its own meaning."""

    def setUp(self) -> None:
        self.graph = k.bound()
        self.diff = SemanticDiff(
            diff_id=k.new_id(),
            base_digest=k.digest("closure.a"),
            target_digest=k.digest("closure.b"),
            entries=(
                DiffEntry(
                    category=DiffCategory.ASSET_REVISION,
                    operation=DiffOperation.CHANGED,
                    subject="render.logo.out",
                    before=k.digest("asset.old"),
                    after=k.digest("asset.new"),
                    node_ids=("render.logo",),
                ),
                DiffEntry(
                    category=DiffCategory.DELIVERY_POLICY,
                    operation=DiffOperation.CHANGED,
                    subject="deliver.web",
                    before="policy.web.v1",
                    after="policy.web.v2",
                    node_ids=("deliver.web",),
                ),
                DiffEntry(
                    category=DiffCategory.QUALITY_DECISION,
                    operation=DiffOperation.CHANGED,
                    subject="validate.quality",
                    before="REVIEW",
                    after="MASTER",
                    node_ids=("render.logo",),
                ),
            ),
        )
        self.delta = compile_build_delta(
            self.diff, graph_id="graph.test", base_revision=rev("a"), target_revision=rev("b")
        )

    def compile(self, *entries: DiffEntry, **over) -> BuildDelta:
        diff = SemanticDiff(
            diff_id=k.new_id(),
            base_digest=k.digest("a"),
            target_digest=k.digest("b"),
            entries=entries,
        )
        base = dict(graph_id="graph.test", base_revision=rev("a"), target_revision=rev("b"))
        base.update(over)
        return compile_build_delta(diff, **base)

    def test_a_category_becomes_the_facet_it_moves_and_not_content(self) -> None:
        moved = {item.facet for item in self.delta.changes if item.node_id == "render.logo"}
        self.assertEqual(moved, {DependencyFacet.CONTENT, DependencyFacet.QUALITY})
        self.assertEqual(
            {item.facet for item in self.delta.changes},
            {DependencyFacet.CONTENT, DependencyFacet.DELIVERY, DependencyFacet.QUALITY},
        )
        self.assertEqual(
            self.delta.categories,
            tuple(
                sorted(
                    {
                        DiffCategory.ASSET_REVISION,
                        DiffCategory.DELIVERY_POLICY,
                        DiffCategory.QUALITY_DECISION,
                    },
                    key=lambda item: item.value,
                )
            ),
        )

    def test_every_diff_category_compiles_instead_of_being_dropped(self) -> None:
        for category in DiffCategory:
            with self.subTest(category=category.value):
                compiled = self.compile(
                    DiffEntry(
                        category=category,
                        operation=DiffOperation.CHANGED,
                        subject="render.logo",
                        before="one",
                        after="two",
                        node_ids=("render.logo",),
                    )
                )
                self.assertTrue(compiled.changes)

    def test_a_dependency_facet_entry_keeps_the_facet_it_named(self) -> None:
        compiled = self.compile(
            DiffEntry(
                category=DiffCategory.DEPENDENCY_FACET,
                operation=DiffOperation.CHANGED,
                subject="render.logo",
                before="one",
                after="two",
                node_ids=("render.logo",),
                facet=DependencyFacet.RIGHTS,
            )
        )
        self.assertEqual(
            [item.facet for item in compiled.changes], [DependencyFacet.RIGHTS]
        )

    def test_only_a_node_dot_port_subject_addresses_a_port(self) -> None:
        ported = [item for item in self.delta.changes if item.port_id]
        self.assertEqual([(item.node_id, item.port_id) for item in ported], [("render.logo", "out")])

    def test_the_delta_reports_its_own_roots_facets_and_digest(self) -> None:
        self.assertEqual(self.delta.roots, ("deliver.web", "render.logo"))
        self.assertEqual(
            tuple(item.value for item in self.delta.facets),
            ("CONTENT", "DELIVERY", "QUALITY"),
        )
        self.assertEqual(
            self.delta.changes_in(DependencyFacet.DELIVERY),
            tuple(item for item in self.delta.changes if item.facet is DependencyFacet.DELIVERY),
        )
        self.assertEqual(len(self.delta.changes_at("render.logo")), 2)
        self.assertEqual(
            self.delta.delta_digest,
            compile_build_delta(
                self.diff,
                graph_id="graph.test",
                base_revision=rev("zz"),
                target_revision=rev("yy"),
            ).delta_digest,
            "the identity of the causes does not depend on which revisions stated them",
        )

    def test_the_delta_carries_the_diff_it_came_from_as_a_delta_reference(self) -> None:
        self.assertIs(self.delta.origin.kind, EntityKind.DELTA)
        self.assertEqual(self.delta.origin.reference, self.diff.digest())

    def test_a_delta_from_a_revision_onto_itself_states_nothing(self) -> None:
        with self.assertRaises(BuildError):
            BuildDelta(
                graph_id="graph.test",
                base_revision=rev("same"),
                target_revision=rev("same"),
                changes=self.delta.changes,
            )

    def test_a_delta_revision_must_be_a_revision(self) -> None:
        with self.assertRaises(SchemaValidationError):
            BuildDelta(
                graph_id="graph.test",
                base_revision=k.ref(EntityKind.ARTIFACT, "asset.logo"),
                target_revision=rev("b"),
            )

    def test_one_slot_states_one_cause(self) -> None:
        with self.assertRaises(BuildError):
            stated(
                k.change("render.logo", DependencyFacet.CONTENT),
                k.change("render.logo", DependencyFacet.CONTENT),
            )

    def test_a_cause_that_names_no_node_invalidates_every_declared_node(self) -> None:
        topology = DiffEntry(
            category=DiffCategory.GRAPH_TOPOLOGY,
            operation=DiffOperation.ADDED,
            subject="edge.new",
            after="render.logo",
        )
        with self.assertRaises(BuildError):
            self.compile(topology)
        fanned = self.compile(topology, known_nodes=self.graph.revision.definition.node_index)
        self.assertEqual(len(fanned.changes), 3)
        self.assertEqual({item.facet for item in fanned.changes}, {DependencyFacet.SEMANTICS})
        self.assertEqual(fanned.roots, ("deliver.web", "render.logo", "source.logo"))

    def test_two_causes_disagreeing_about_the_previous_bytes_are_refused(self) -> None:
        with self.assertRaises(BuildError):
            self.compile(
                DiffEntry(
                    category=DiffCategory.ASSET_REVISION,
                    operation=DiffOperation.CHANGED,
                    subject="render.logo.out",
                    before=k.digest("first"),
                    after=k.digest("second"),
                    node_ids=("render.logo",),
                ),
                DiffEntry(
                    category=DiffCategory.DEPENDENCY_FACET,
                    operation=DiffOperation.CHANGED,
                    subject="render.logo.out",
                    before=k.digest("contradictory"),
                    after=k.digest("second"),
                    node_ids=("render.logo",),
                    facet=DependencyFacet.CONTENT,
                ),
            )

    def test_an_empty_delta_is_honest_about_being_empty(self) -> None:
        quiet = stated()
        self.assertTrue(quiet.is_empty)
        self.assertFalse(quiet)
        self.assertEqual(quiet.roots, ())
        self.assertFalse(
            stated(k.change("render.logo", DependencyFacet.CONTENT)).is_empty
        )


class DirtyFrontierTests(unittest.TestCase):
    """The frontier is the impact cone with its receipts attached."""

    def setUp(self) -> None:
        self.graph = k.bound()
        self.delta = stated(
            k.change("source.logo", DependencyFacet.CONTENT, previous="old-asset", current="new-asset")
        )
        self.frontier = dirty_frontier(self.graph, self.delta)

    def test_the_cone_becomes_the_minimal_set_that_must_run(self) -> None:
        self.assertEqual(self.frontier.node_ids, ("deliver.web", "render.logo", "source.logo"))
        self.assertEqual(self.frontier.states, (BuildState.DIRTY,))
        self.assertTrue(self.frontier)
        self.assertEqual(self.frontier.in_state(BuildState.DIRTY), self.frontier.nodes)
        self.assertEqual(self.frontier.delta_digest, self.delta.delta_digest)

    def test_a_cause_sits_at_depth_zero_and_the_work_below_it_is_counted(self) -> None:
        self.assertEqual(self.frontier.at("source.logo").depth, 0)
        self.assertEqual(self.frontier.at("source.logo").roots, ("source.logo",))
        self.assertEqual(self.frontier.at("render.logo").roots, ("source.logo",))
        self.assertEqual(self.frontier.at("deliver.web").roots, ("render.logo",))
        self.assertEqual(self.frontier.at("deliver.web").depth, 1)

    def test_every_node_in_the_frontier_owes_the_sentence_that_put_it_there(self) -> None:
        self.assertIn("edge edge.deliver", self.frontier.at("deliver.web").reasons[0])
        self.assertEqual(self.frontier.explaining("render.logo"), self.frontier.at("render.logo").reasons)
        self.assertIn("changed in facet CONTENT", self.frontier.at("source.logo").reasons[0])
        self.assertIn(
            f"{k.digest('old-asset')[:8]} -> {k.digest('new-asset')[:8]}",
            self.frontier.at("source.logo").reasons[0],
            "the sentence names the digests it compared, not just that something moved",
        )
        self.assertEqual(self.frontier.explaining("node.absent"), ())

    def test_ports_and_slices_belong_to_the_node_a_cause_named(self) -> None:
        sliced = stated(
            k.change("render.logo", DependencyFacet.CONTENT, port_id="in", slice=REGION)
        )
        frontier = dirty_frontier(self.graph, sliced)
        self.assertEqual(frontier.at("render.logo").port_ids, ("in",))
        self.assertEqual(frontier.at("render.logo").slices, (REGION,))
        self.assertEqual(frontier.at("deliver.web").port_ids, ())
        self.assertEqual(
            frontier.at("deliver.web").slices, (),
            "a consumer with no slice of its own cannot be repaired, so it rebuilds",
        )
        self.assertIn("region=left", frontier.at("render.logo").text)

    def test_a_delta_for_another_graph_or_an_undeclared_node_is_refused(self) -> None:
        with self.assertRaises(BuildError):
            dirty_frontier(self.graph, stated(k.change("source.logo"), graph_id="graph.other"))
        with self.assertRaises(BuildError):
            dirty_frontier(self.graph, stated(k.change("node.invented")))
        with self.assertRaises(BuildError):
            dirty_frontier(self.graph, stated(), states={"node.invented": BuildState.BLOCKED})

    def test_a_frontier_needs_a_bound_graph_and_a_delta(self) -> None:
        with self.assertRaises(SchemaValidationError):
            dirty_frontier(self.graph.revision, self.delta)
        with self.assertRaises(SchemaValidationError):
            dirty_frontier(self.graph, stated(k.change("source.logo")).changes[0])

    def test_an_empty_delta_leaves_nothing_to_run(self) -> None:
        quiet = dirty_frontier(self.graph, stated())
        self.assertTrue(quiet.is_empty)
        self.assertEqual(quiet.nodes, ())

    def test_a_caller_may_name_a_node_without_inventing_a_change_for_it(self) -> None:
        named = dirty_frontier(self.graph, stated(), states={"deliver.web": BuildState.BLOCKED})
        found = named.at("deliver.web")
        self.assertIs(found.state, BuildState.BLOCKED)
        self.assertTrue(found.reasons)
        self.assertIn("was named by the caller", found.reasons[0])

    def test_a_conditional_consumer_is_planned_as_revalidation_not_a_rebuild(self) -> None:
        activated = MaterializationGraph(
            revision=GraphRevision(
                revision_id=k.new_id(),
                definition=k.definition(
                    k.source(),
                    k.operation(),
                    k.delivery(),
                    edges=(
                        k.edge("edge.render", "source.logo", "render.logo"),
                        k.edge(
                            "edge.pick",
                            "render.logo",
                            "deliver.web",
                            kind=EdgeKind.ACTIVATION,
                            facets=(DependencyFacet.SEMANTICS,),
                        ),
                    ),
                ),
            ),
            materializations=self.graph.materializations,
        )
        conditional = dirty_frontier(activated, stated(k.change("render.logo", DependencyFacet.SEMANTICS)))
        self.assertTrue(conditional.at("deliver.web").conditional)
        self.assertIs(conditional.at("deliver.web").state, BuildState.REVALIDATE_ONLY)
        self.assertIs(conditional.at("render.logo").state, BuildState.DIRTY)

    def test_a_dirty_node_with_no_stated_cause_is_refused(self) -> None:
        with self.assertRaises(BuildError):
            DirtyNode(node_id="render.logo")
        with self.assertRaises(BuildError):
            DirtyFrontier(
                graph_id="graph.test",
                delta_digest=k.digest("delta"),
                nodes=(
                    DirtyNode(node_id="render.logo", reasons=("moved",)),
                    DirtyNode(node_id="render.logo", reasons=("moved again",)),
                ),
            )

    def test_a_frontier_reports_a_node_it_does_not_know_as_nothing(self) -> None:
        self.assertIsNone(self.frontier.at("node.nobody"))


class RepairFrontierTests(unittest.TestCase):
    """What a bounded redo settles, and what it demonstrably does not."""

    def setUp(self) -> None:
        self.graph = k.bound()
        self.delta = stated(
            k.change(
                "render.logo",
                DependencyFacet.CONTENT,
                port_id="in",
                slice=REGION,
                previous="old-frame",
                current="new-frame",
            )
        )
        self.frontier = dirty_frontier(self.graph, self.delta)
        self.bounded = repair_frontier(self.graph, self.frontier, slices={"render.logo": REGION})

    def test_a_sliced_cause_may_be_repaired_and_everything_else_rebuilds(self) -> None:
        self.assertEqual(self.bounded.node_ids, ("render.logo",))
        self.assertEqual(self.bounded.uncovered, ("deliver.web",))
        self.assertEqual(self.bounded.rebuild_instead(self.frontier), ("deliver.web",))
        self.assertTrue(self.bounded.covers("render.logo", self.delta.changes[0]))
        self.assertFalse(self.bounded.covers("deliver.web", self.delta.changes[0]))
        self.assertIn("region=left", self.bounded.target_for("render.logo").text)

    def test_settles_answers_for_the_whole_node_not_one_cause(self) -> None:
        self.assertTrue(self.bounded.settles(self.frontier.at("render.logo")))
        self.assertFalse(self.bounded.settles(self.frontier.at("deliver.web")))
        self.assertFalse(
            self.bounded.settles(DirtyNode(node_id="render.logo", reasons=("moved",))),
            "an uncaused node has nothing for the bounded redo to have answered",
        )

    def test_redoing_another_region_does_not_answer_a_cause_about_this_one(self) -> None:
        wrong = repair_frontier(self.graph, self.frontier, slices={"render.logo": ELSEWHERE})
        self.assertFalse(wrong.covers("render.logo", self.delta.changes[0]))
        self.assertEqual(wrong.uncovered, ("deliver.web", "render.logo"))
        self.assertEqual(wrong.rebuild_instead(self.frontier), ("deliver.web", "render.logo"))

    def test_a_whole_node_repair_answers_any_cause_on_that_node(self) -> None:
        whole = repair_frontier(self.graph, self.frontier, whole_node=("render.logo",))
        self.assertTrue(whole.covers("render.logo", self.delta.changes[0]))
        self.assertTrue(whole.target_for("render.logo").covers_whole_node)
        self.assertTrue(whole.settles(self.frontier.at("render.logo")))

    def test_a_cause_with_no_slice_is_never_answered_by_a_partial_repair(self) -> None:
        unbounded = dirty_frontier(self.graph, stated(k.change("render.logo", DependencyFacet.CONTENT)))
        bounded = repair_frontier(self.graph, unbounded, slices={"render.logo": REGION})
        self.assertEqual(bounded.uncovered, ("deliver.web", "render.logo"))
        self.assertFalse(bounded.settles(unbounded.at("render.logo")))

    def test_re_attesting_evidence_is_not_something_a_content_repair_settles(self) -> None:
        quiet = dirty_frontier(self.graph, stated(k.change("render.logo", DependencyFacet.QUALITY)))
        self.assertEqual(
            quiet.node_ids, ("render.logo",),
            "a moved quality decision reaches no consumer's bytes",
        )
        self.assertEqual(
            repair_frontier(self.graph, quiet, slices={"render.logo": REGION}).targets, (),
            "there is no slice of a re-attestation to redo",
        )
        mixed = dirty_frontier(
            self.graph,
            stated(
                k.change("render.logo", DependencyFacet.CONTENT, slice=REGION),
                k.change("render.logo", DependencyFacet.QUALITY),
            ),
        )
        bounded = repair_frontier(self.graph, mixed, slices={"render.logo": REGION})
        self.assertIn("render.logo", bounded.uncovered, "the content half is redone and the evidence half is not")
        self.assertFalse(bounded.settles(mixed.at("render.logo")))

    def test_two_slices_of_one_node_are_settled_by_a_repair_covering_both(self) -> None:
        both = dirty_frontier(
            self.graph,
            stated(
                k.change("render.logo", DependencyFacet.CONTENT, slice=REGION),
                k.change("render.logo", DependencyFacet.SEMANTICS, slice=DependencySlice(axis="region", values=("left", "right"))),
            ),
        )
        bounded = repair_frontier(self.graph, both, slices={"render.logo": DependencySlice(axis="region", values=("left", "right"))})
        self.assertEqual(bounded.node_ids, ("render.logo",))
        self.assertEqual(
            bounded.target_for("render.logo").facets,
            (DependencyFacet.CONTENT, DependencyFacet.SEMANTICS),
        )

    def test_a_repair_must_target_a_declared_node(self) -> None:
        with self.assertRaises(BuildError):
            repair_frontier(self.graph, self.frontier, slices={"node.ghost": REGION})
        with self.assertRaises(BuildError):
            repair_frontier(self.graph, self.frontier, whole_node=("node.ghost",))

    def test_one_node_cannot_be_repaired_along_two_axes(self) -> None:
        with self.assertRaises(BuildError):
            RepairFrontier(
                graph_id="graph.test",
                targets=(
                    RepairTarget(
                        node_id="render.logo",
                        slice=REGION,
                        facets=(DependencyFacet.CONTENT,),
                        reasons=("redo the left region",),
                    ),
                    RepairTarget(
                        node_id="render.logo",
                        slice=LOCALE,
                        facets=(DependencyFacet.CONTENT,),
                        reasons=("redo one locale",),
                    ),
                ),
            )

    def test_a_repair_target_owes_a_facet_and_a_reason(self) -> None:
        with self.assertRaises(BuildError):
            RepairTarget(node_id="render.logo", slice=REGION, facets=(), reasons=("x",))
        with self.assertRaises(BuildError):
            RepairTarget(node_id="render.logo", slice=REGION, facets=(DependencyFacet.CONTENT,), reasons=())
        with self.assertRaises(SchemaValidationError):
            RepairTarget(node_id="render.logo", slice="region=left", facets=(DependencyFacet.CONTENT,), reasons=("x",))
        with self.assertRaises(BuildError):
            RepairFrontier(
                graph_id="graph.test",
                targets=(
                    RepairTarget(
                        node_id="render.logo",
                        slice=REGION,
                        facets=(DependencyFacet.CONTENT,),
                        reasons=("whole",),
                        covers_whole_node=True,
                    ),
                    RepairTarget(
                        node_id="render.logo",
                        slice=LOCALE,
                        facets=(DependencyFacet.CONTENT,),
                        reasons=("and one slice",),
                    ),
                ),
            )

    def test_an_empty_repair_frontier_says_so(self) -> None:
        empty = repair_frontier(self.graph, self.frontier)
        self.assertFalse(empty)
        self.assertEqual(empty.rebuild_instead(self.frontier), self.frontier.node_ids)
        self.assertIsNone(empty.target_for("render.logo"))


class BuildStepDiscipline(unittest.TestCase):
    """A step that lies about its evidence cannot be constructed."""

    def setUp(self) -> None:
        self.graph = k.bound()
        self.granted = k.admitted_receipt(self.graph, "render.logo")

    def test_a_reuse_step_is_only_representable_with_its_own_admission(self) -> None:
        step = reuse(self.graph)
        self.assertTrue(step.is_reuse)
        self.assertTrue(step.avoids)
        self.assertEqual(step.receipt.key, self.granted.key)
        self.assertEqual(step.key, self.granted.key)
        self.assertTrue(step.receipt.satisfies_output)
        with self.assertRaises(BuildError):
            BuildStep(
                node_id="render.logo",
                state=BuildState.CACHED_ELIGIBLE,
                disposition=WorkDisposition.REUSE,
                reasons=("a hit was claimed",),
                key=self.granted.key,
            )
        with self.assertRaises(BuildError):
            BuildStep(
                node_id="render.logo",
                state=BuildState.CACHED_ELIGIBLE,
                disposition=WorkDisposition.REUSE,
                reasons=("a hit was claimed",),
                receipt=self.granted,
            )

    def test_a_receipt_belongs_to_the_node_holding_it(self) -> None:
        with self.assertRaises(BuildError):
            BuildStep(
                node_id="deliver.web",
                state=BuildState.CACHED_ELIGIBLE,
                disposition=WorkDisposition.REUSE,
                reasons=("someone else's receipt",),
                key=self.granted.key,
                receipt=self.granted,
            )
        with self.assertRaises(BuildError):
            rebuild("render.logo", receipt=self.granted)

    def test_a_partial_hit_never_finishes_a_node(self) -> None:
        partial = admit_reuse(
            k.cache_entry(self.graph, "render.logo", reuse_class=ReuseClass.PARTIAL_REUSE),
            k.reuse_request(self.graph, "render.logo"),
            trust=k.cache_trust(),
        )
        self.assertIsInstance(partial, ReuseReceipt)
        self.assertFalse(partial.satisfies_output)
        with self.assertRaises(BuildError):
            BuildStep(
                node_id="render.logo",
                state=BuildState.CACHED_ELIGIBLE,
                disposition=WorkDisposition.REUSE,
                reasons=("a partial hit counted as the whole answer",),
                key=partial.key,
                receipt=partial,
            )

    def test_only_repair_carries_a_slice_and_it_must(self) -> None:
        with self.assertRaises(BuildError):
            rebuild("render.logo", slice=REGION)
        with self.assertRaises(BuildError):
            BuildStep(
                node_id="render.logo",
                state=BuildState.DIRTY,
                disposition=WorkDisposition.REPAIR,
                reasons=("a bounded redo",),
                outputs=("out",),
            )
        step = BuildStep(
            node_id="render.logo",
            state=BuildState.DIRTY,
            disposition=WorkDisposition.REPAIR,
            reasons=("a bounded redo",),
            slice=REGION,
            outputs=("out",),
        )
        self.assertEqual(step.slice, REGION)
        self.assertTrue(step.emits_new_bytes)

    def test_a_disposition_may_not_be_chosen_from_a_state_that_does_not_admit_it(self) -> None:
        cases = (
            (BuildState.UNKNOWN, WorkDisposition.REBUILD),
            (BuildState.CLEAN, WorkDisposition.REBUILD),
            (BuildState.CLEAN, WorkDisposition.REPAIR),
            (BuildState.BLOCKED, WorkDisposition.REPACKAGE),
            (BuildState.REVALIDATE_ONLY, WorkDisposition.REBUILD),
            (BuildState.REPACKAGE_ONLY, WorkDisposition.REVALIDATE),
        )
        for state, disposition in cases:
            with self.subTest(state=state.value, disposition=disposition.value):
                with self.assertRaises(BuildError):
                    BuildStep(
                        node_id="render.logo",
                        state=state,
                        disposition=disposition,
                        reasons=("because I felt like it",),
                    )

    def test_an_unexplained_step_is_refused(self) -> None:
        with self.assertRaises(BuildError):
            BuildStep(node_id="render.logo", state=BuildState.DIRTY, disposition=WorkDisposition.REBUILD)

    def test_repackaging_must_say_which_output_it_redelivers(self) -> None:
        with self.assertRaises(BuildError):
            BuildStep(
                node_id="deliver.web",
                state=BuildState.REPACKAGE_ONLY,
                disposition=WorkDisposition.REPACKAGE,
                reasons=("the delivery policy moved",),
            )

    def test_a_step_may_not_both_reuse_and_report_a_refused_entry(self) -> None:
        refused = ReuseRejection(
            node_id="render.logo",
            key=self.granted.key,
            checks=(
                CacheCheck(name=PoisonCheck.WRITE_TRUST, passed=False, detail="an untrusted writer"),
            ),
            claimed_class=ReuseClass.EXACT_REUSE,
        )
        with self.assertRaises(BuildError):
            reuse(self.graph, rejection=refused)
        honest = rebuild("render.logo", rejection=refused)
        self.assertIn(refused.reasons[0], honest.explains())

    def test_a_rejection_belongs_to_the_node_holding_it(self) -> None:
        refused = ReuseRejection(
            node_id="render.logo",
            key=self.granted.key,
            checks=(CacheCheck(name=PoisonCheck.WRITE_TRUST, passed=False, detail="x"),),
            claimed_class=ReuseClass.EXACT_REUSE,
        )
        with self.assertRaises(BuildError):
            rebuild("deliver.web", rejection=refused)

    def test_a_cache_key_must_have_been_derived_for_this_node(self) -> None:
        other = k.reuse_request(self.graph, "deliver.web", layer=CacheLayer.FINAL).key
        with self.assertRaises(BuildError):
            rebuild("render.logo", key=other)

    def test_the_honest_unknown_step_reports_instead_of_skipping(self) -> None:
        blocked = BuildStep(
            node_id="deliver.web",
            state=BuildState.UNKNOWN,
            disposition=WorkDisposition.BLOCK,
            reasons=("nothing can be said about these bytes",),
            outputs=("out",),
        )
        self.assertTrue(blocked.blocked)
        self.assertFalse(blocked.emits_new_bytes)
        self.assertEqual(len(blocked.explains()), 1)
        self.assertIn("UNKNOWN -> BLOCK", blocked.text)

    def test_byte_identity_is_claimed_only_by_the_classes_that_claim_it(self) -> None:
        self.assertTrue(rebuild("render.logo").claims_byte_identity)
        stochastic = rebuild("render.logo", reproducibility=ReproducibilityClass.STOCHASTIC)
        self.assertFalse(stochastic.claims_byte_identity)
        self.assertFalse(rebuild("render.logo", reproducibility=None).claims_byte_identity)

    def test_a_step_normalizes_its_collections_and_refuses_bad_scalars(self) -> None:
        step = rebuild(
            "render.logo",
            reasons=("moved", "moved"),
            depends_on=("source.logo", "render.logo", "source.logo"),
            outputs=("out", "out"),
            facets=(DependencyFacet.CONTENT, DependencyFacet.CONTENT),
        )
        self.assertEqual(step.reasons, ("moved",))
        self.assertEqual(step.depends_on, ("source.logo",), "a node does not depend on itself")
        self.assertEqual(step.outputs, ("out",))
        self.assertEqual(step.facets, (DependencyFacet.CONTENT,))
        self.assertEqual(step.reproducibility, ReproducibilityClass.DETERMINISTIC.value)
        with self.assertRaises(SchemaValidationError):
            rebuild("render.logo", attempts=0)
        with self.assertRaises(SchemaValidationError):
            rebuild("render.logo", commit_mode="SOMETIMES")
        with self.assertRaises(SchemaValidationError):
            rebuild(node_id="Render Logo")


class BuildPlanDiscipline(unittest.TestCase):
    """A plan is only a plan if it can be executed and argued with."""

    def setUp(self) -> None:
        self.graph = k.bound()

    def test_a_plan_that_reuses_all_the_way_down_is_settled(self) -> None:
        quiet = decide(
            reuse(self.graph),
            reuse(self.graph, node_id="deliver.web", depends_on=("render.logo",), layer=CacheLayer.FINAL),
        )
        self.assertEqual(quiet.reused, ("deliver.web", "render.logo"))
        self.assertEqual(quiet.must_run, ())
        self.assertEqual(len(quiet.receipts), 2)
        self.assertTrue(quiet.is_settled)
        self.assertEqual(quiet.summary[WorkDisposition.REUSE], ("deliver.web", "render.logo"))

    def test_a_step_may_not_wait_for_work_nobody_decided_on(self) -> None:
        with self.assertRaises(BuildError):
            decide(rebuild("render.logo", depends_on=("source.logo",)))

    def test_a_plan_that_cannot_be_ordered_is_refused(self) -> None:
        with self.assertRaises(BuildError):
            decide(
                rebuild("render.logo", depends_on=("deliver.web",)),
                rebuild("deliver.web", depends_on=("render.logo",)),
            )

    def test_one_node_gets_one_disposition(self) -> None:
        with self.assertRaises(BuildError):
            decide(rebuild("render.logo"), reuse(self.graph, depends_on=()))

    def test_reuse_is_refused_while_an_input_is_scheduled_to_write_new_bytes(self) -> None:
        with self.assertRaises(BuildError) as caught:
            decide(
                rebuild("render.logo"),
                reuse(
                    self.graph,
                    node_id="deliver.web",
                    depends_on=("render.logo",),
                    layer=CacheLayer.FINAL,
                    reasons=("its input is rebuilding but a hit was claimed anyway",),
                ),
            )
        self.assertIn("under-invalidation", str(caught.exception))

    def test_a_mixed_plan_answers_questions_in_causal_order(self) -> None:
        plan = decide(
            rebuild("source.logo"),
            rebuild("render.logo", depends_on=("source.logo",)),
            BuildStep(
                node_id="deliver.web",
                state=BuildState.REPACKAGE_ONLY,
                disposition=WorkDisposition.REPACKAGE,
                reasons=("only the delivery policy moved",),
                depends_on=("render.logo",),
                outputs=("out",),
            ),
        )
        self.assertEqual(plan.ordered(), ("source.logo", "render.logo", "deliver.web"))
        self.assertEqual(plan.must_run, ("deliver.web", "render.logo", "source.logo"))
        self.assertEqual((plan.reused, plan.repairs, plan.blocked), ((), (), ()))
        self.assertEqual(plan.downstream_of("source.logo"), ("deliver.web", "render.logo"))
        self.assertEqual(plan.requires("deliver.web"), (plan.at("render.logo"),))
        self.assertEqual(plan.covers(("source.logo", "nobody.at.all")), ("nobody.at.all",))
        self.assertEqual(
            {key.value: value for key, value in plan.summary.items()},
            {"REBUILD": ("render.logo", "source.logo"), "REPACKAGE": ("deliver.web",)},
        )
        self.assertTrue(plan.is_settled)
        self.assertTrue(plan)
        self.assertEqual(plan.node_ids, ("deliver.web", "render.logo", "source.logo"))
        with self.assertRaises(BuildError):
            plan.at("node.absent")

    def test_a_blocked_step_keeps_the_plan_from_claiming_it_is_settled(self) -> None:
        plan = decide(
            BuildStep(
                node_id="deliver.web",
                state=BuildState.UNKNOWN,
                disposition=WorkDisposition.BLOCK,
                reasons=("an input binds to nothing",),
            )
        )
        self.assertEqual(plan.blocked, ("deliver.web",))
        self.assertFalse(plan.is_settled)
        self.assertEqual(plan.must_run, ())
        self.assertEqual(plan.at("deliver.web").outputs, ())

    def test_a_plan_names_the_delta_it_answers(self) -> None:
        delta = stated(k.change("source.logo", DependencyFacet.CONTENT))
        plan = decide(rebuild("source.logo"), delta=delta)
        self.assertEqual(plan.delta_digest, delta.delta_digest)
        self.assertEqual(
            decide(rebuild("source.logo")).delta_digest, None,
            "a plan without a stated delta does not pretend to have one",
        )
        self.assertEqual(
            decide(rebuild("source.logo"), delta=stated()).delta_digest,
            content_digest([]),
            "an empty delta is still a stated one, so a caller may name work without a cause",
        )
        with self.assertRaises(SchemaValidationError):
            BuildPlan(
                plan_id=k.new_id(),
                graph_id="graph.test",
                base_revision=rev("a"),
                target_revision=rev("b"),
                steps=(rebuild("source.logo"),),
                delta_digest="not-a-digest",
            )

    def test_a_plan_rejects_a_revision_that_is_not_a_revision(self) -> None:
        with self.assertRaises(SchemaValidationError):
            BuildPlan(
                plan_id=k.new_id(),
                graph_id="graph.test",
                base_revision=k.ref(EntityKind.ARTIFACT, "asset.logo"),
                target_revision=rev("b"),
                steps=(),
            )


class PlanningFromADelta(unittest.TestCase):
    """plan_build turning causes into dispositions, with nothing invented on the way."""

    def setUp(self) -> None:
        self.graph = k.bound()

    def plan(self, *changes, **over) -> BuildPlan:
        base = dict(trust=k.cache_trust(), context=k.cache_context(), now_ms=NOW)
        base.update(over)
        delta = base.pop("delta") if "delta" in base else stated(*changes)
        return plan_build(self.graph, delta=delta, **base)

    def test_a_graph_with_nothing_stated_produces_no_work(self) -> None:
        empty = plan_build(self.graph)
        self.assertEqual(empty.steps, ())
        self.assertEqual(
            empty.covers(("source.logo", "render.logo", "deliver.web")),
            ("deliver.web", "render.logo", "source.logo"),
            "untouched nodes are absent from the plan, not listed as no-ops",
        )

    def test_a_source_change_rebuilds_the_chain_it_reaches(self) -> None:
        delta = stated(k.change("source.logo", DependencyFacet.CONTENT, previous="old", current="new"))
        plan = self.plan(delta=delta)
        self.assertEqual(
            [(step.node_id, step.disposition) for step in plan.steps],
            [
                ("deliver.web", WorkDisposition.REBUILD),
                ("render.logo", WorkDisposition.REBUILD),
                ("source.logo", WorkDisposition.REBUILD),
            ],
        )
        self.assertEqual(plan.at("render.logo").depends_on, ("source.logo",))
        self.assertEqual(plan.at("deliver.web").depends_on, ("render.logo",))
        self.assertEqual(plan.at("source.logo").facets, (DependencyFacet.CONTENT,))
        self.assertEqual(plan.delta_digest, delta.delta_digest)
        self.assertEqual(plan.blocked, ())
        self.assertTrue(plan.is_settled)

    def test_a_clean_prerequisite_is_reported_as_left_out_instead_of_dangling(self) -> None:
        plan = plan_build(self.graph, states={"render.logo": BuildState.DIRTY})
        step = plan.at("render.logo")
        self.assertEqual(step.depends_on, ())
        self.assertIn("source.logo sits upstream and needs no work", " ".join(step.reasons))
        self.assertEqual(step.disposition, WorkDisposition.REBUILD)

    def test_a_state_for_a_node_that_is_not_in_the_graph_is_refused(self) -> None:
        with self.assertRaises(BuildError):
            plan_build(self.graph, states={"node.ghost": BuildState.DIRTY})

    def test_only_a_repair_that_answers_the_sliced_cause_is_planned_as_repair(self) -> None:
        sliced = stated(k.change("render.logo", DependencyFacet.CONTENT, port_id="in", slice=REGION))
        repaired = plan_build(self.graph, delta=sliced, repair_slices={"render.logo": REGION})
        self.assertEqual(repaired.repairs, ("render.logo",))
        self.assertEqual(repaired.at("render.logo").slice, REGION)
        self.assertIn("bounded repair of", " ".join(repaired.at("render.logo").reasons))
        self.assertEqual(repaired.at("deliver.web").disposition, WorkDisposition.REBUILD)
        untouched = plan_build(self.graph, delta=sliced)
        self.assertEqual(untouched.repairs, ())
        wrong = plan_build(self.graph, delta=sliced, repair_slices={"render.logo": ELSEWHERE})
        self.assertEqual(wrong.repairs, (), "redoing the wrong region is not the work the cause asked for")

    def test_a_rights_change_on_a_delivery_node_blocks_it_for_re_clearance(self) -> None:
        plan = self.plan(k.change("deliver.web", DependencyFacet.RIGHTS))
        step = plan.at("deliver.web")
        self.assertIs(step.state, BuildState.BLOCKED)
        self.assertIs(step.disposition, WorkDisposition.BLOCK)
        self.assertEqual(step.outputs, ())
        self.assertIn("re-cleared", " ".join(step.reasons))

    def test_evidence_that_moved_is_re_attested_rather_than_re_rendered(self) -> None:
        plan = self.plan(k.change("render.logo", DependencyFacet.QUALITY))
        step = plan.at("render.logo")
        self.assertIs(step.state, BuildState.REVALIDATE_ONLY)
        self.assertIs(step.disposition, WorkDisposition.REVALIDATE)
        self.assertFalse(step.emits_new_bytes)
        self.assertIn("only evidence moved", " ".join(step.reasons))

    def test_a_delivery_policy_change_only_repackages(self) -> None:
        plan = self.plan(k.change("render.logo", DependencyFacet.DELIVERY))
        step = plan.at("render.logo")
        self.assertIs(step.state, BuildState.REPACKAGE_ONLY)
        self.assertTrue(step.emits_new_bytes)
        self.assertIn("the bytes stay and the package changes", " ".join(step.reasons))

    def test_repackaging_a_node_that_emits_nothing_fails_closed(self) -> None:
        lonely = MaterializationGraph(
            revision=GraphRevision(
                revision_id=k.new_id(),
                definition=k.definition(k.node("lonely.op", NodeRole.OPERATION)),
            ),
            materializations=(),
        )
        plan = plan_build(lonely, delta=stated(k.change("lonely.op", DependencyFacet.DELIVERY)))
        step = plan.at("lonely.op")
        self.assertIs(step.disposition, WorkDisposition.BLOCK)
        self.assertIn("emits no output port", " ".join(step.reasons))

    def test_a_node_whose_input_binds_to_nothing_is_blocked_not_guessed(self) -> None:
        missing = k.bound(records=(k.materialization("source.logo"), k.materialization("deliver.web")))
        plan = plan_build(missing)
        step = plan.at("deliver.web")
        self.assertIs(step.state, BuildState.UNKNOWN)
        self.assertIs(step.disposition, WorkDisposition.BLOCK)
        self.assertIn("binds to no materialization", " ".join(step.reasons))
        self.assertIs(
            plan.at("render.logo").state, BuildState.DIRTY,
            "the node that never ran has a cause of its own, so it is dirty rather than unknown",
        )

    def test_a_node_that_never_ran_is_dirty_rather_than_clean(self) -> None:
        missing = k.bound(records=(k.materialization("render.logo"), k.materialization("deliver.web")))
        plan = plan_build(missing)
        step = plan.at("source.logo")
        self.assertIs(step.state, BuildState.DIRTY)
        self.assertIn("declares no materialization", " ".join(step.reasons))

    def test_multi_output_nodes_commit_as_one_set_unless_told_otherwise(self) -> None:
        wide = MaterializationGraph(
            revision=GraphRevision(
                revision_id=k.new_id(),
                definition=k.definition(
                    k.source(),
                    k.operation(),
                    k.delivery(),
                    k.node(
                        "poster.two",
                        NodeRole.OPERATION,
                        outputs=(k.output("out", type_id="raster.png"), k.output("thumb", type_id="raster.jpg")),
                    ),
                    edges=(
                        k.edge("edge.render", "source.logo", "render.logo"),
                        k.edge("edge.deliver", "render.logo", "deliver.web"),
                    ),
                ),
            ),
            materializations=self.graph.materializations,
        )
        named = {"poster.two": BuildState.DIRTY, "render.logo": BuildState.DIRTY}
        guarded = plan_build(wide, states=named)
        self.assertIs(guarded.at("poster.two").commit_mode, OutputCommitMode.ATOMIC)
        self.assertIs(guarded.at("render.logo").commit_mode, OutputCommitMode.PARTIAL)
        allowed = plan_build(wide, states=named, partial_commit=("poster.two",))
        self.assertIs(allowed.at("poster.two").commit_mode, OutputCommitMode.PARTIAL)


class PlanningAgainstTheCache(unittest.TestCase):
    """The only promotable reuse is one the shield granted for this exact claim."""

    def setUp(self) -> None:
        self.graph = k.bound()

    def with_entry(self, node_id: str, entry, **over) -> BuildPlan:
        return named_hit(self.graph, node_id, entry, **over)

    def test_an_admitted_entry_becomes_a_reuse_step_with_its_receipt(self) -> None:
        plan = self.with_entry("render.logo", k.cache_entry(self.graph, "render.logo"))
        step = plan.at("render.logo")
        self.assertIs(step.disposition, WorkDisposition.REUSE)
        self.assertIs(step.state, BuildState.CACHED_ELIGIBLE)
        self.assertEqual(step.receipt.node_id, "render.logo")
        self.assertIn("cache at L3 admitted", " ".join(step.reasons))
        self.assertEqual(plan.receipts, (step.receipt,))

    def test_the_layer_a_node_is_cached_at_comes_from_what_it_is(self) -> None:
        delivery = k.cache_entry(self.graph, "deliver.web", layer=CacheLayer.FINAL)
        self.assertIs(self.with_entry("deliver.web", delivery).at("deliver.web").disposition, WorkDisposition.REUSE)
        misplaced = self.with_entry("deliver.web", k.cache_entry(self.graph, "deliver.web", layer=CacheLayer.INTERMEDIATE))
        step = misplaced.at("deliver.web")
        self.assertIs(step.disposition, WorkDisposition.REBUILD)
        self.assertIn("layer: INTERMEDIATE is now FINAL", step.rejection.text)
        self.assertEqual(
            [check.name.value for check in step.rejection.checks if not check.passed],
            [PoisonCheck.KEY_SCHEMA.value],
        )

    def test_a_partial_hit_is_recorded_and_the_node_still_runs(self) -> None:
        plan = self.with_entry(
            "render.logo", k.cache_entry(self.graph, "render.logo", reuse_class=ReuseClass.PARTIAL_REUSE)
        )
        step = plan.at("render.logo")
        self.assertIs(step.disposition, WorkDisposition.REBUILD)
        self.assertIn("does not satisfy this node's output", " ".join(step.reasons))
        self.assertIsNone(step.rejection, "an admitted partial hit is not a refusal")

    def test_a_refused_entry_names_the_question_that_refused_it(self) -> None:
        cases = (
            (k.component_version("m02.rogue", "9.9.9"), PoisonCheck.PRODUCER_ADMISSION, None),
            (None, PoisonCheck.WRITE_TRUST, OriginClass.LOCAL_EXPERIMENT),
        )
        for producer, expected, origin in cases:
            with self.subTest(check=expected.value):
                over = {} if producer is None else {"producer": producer}
                if origin is not None:
                    over["writer_origin"] = origin
                plan = self.with_entry("render.logo", k.cache_entry(self.graph, "render.logo", **over))
                step = plan.at("render.logo")
                self.assertIs(step.disposition, WorkDisposition.REBUILD)
                self.assertIn(expected, {check.name for check in step.rejection.checks if not check.passed})
                self.assertIn("cache refused:", " ".join(step.reasons))

    def test_a_quarantined_entry_is_refused_even_when_it_otherwise_matches(self) -> None:
        entry = k.cache_entry(self.graph, "render.logo")
        ledger = QuarantineLedger(
            rules=(
                QuarantineRule(
                    rule_id=k.new_id(),
                    value=entry.key.address,
                    scope="key",
                    expires_at_ms=NOW + 1000,
                    reason="a shadow rebuild disagreed with this key",
                ),
            ),
            now_ms=NOW,
        )
        plan = self.with_entry("render.logo", entry, quarantine=ledger)
        step = plan.at("render.logo")
        self.assertIs(step.disposition, WorkDisposition.REBUILD)
        self.assertIn("quarantined after an earlier mismatch", step.rejection.text)

    def test_an_entry_for_a_source_node_that_reads_the_world_is_never_admitted(self) -> None:
        plan = self.with_entry("source.logo", k.cache_entry(self.graph, "source.logo"))
        step = plan.at("source.logo")
        self.assertIs(step.disposition, WorkDisposition.REBUILD)
        self.assertIs(
            PoisonCheck.CLOSURE_COMPLETENESS,
            next(check.name for check in step.rejection.checks if not check.passed),
        )

    def test_a_matching_entry_is_not_asked_while_an_input_is_going_to_change(self) -> None:
        entry = k.cache_entry(self.graph, "render.logo")
        plan = plan_build(
            self.graph,
            delta=stated(k.change("source.logo", DependencyFacet.CONTENT)),
            cache=(entry,),
            trust=k.cache_trust(),
            context=k.cache_context(),
            now_ms=NOW,
        )
        step = plan.at("render.logo")
        self.assertIs(step.disposition, WorkDisposition.REBUILD)
        self.assertIsNone(step.receipt)
        self.assertIn("is not asked, because source.logo will emit new bytes", " ".join(step.reasons))
        self.assertIsNone(step.rejection, "the cache was never consulted, so it never refused anything")

    def test_two_admitted_entries_make_a_quiet_plan_that_still_owes_receipts(self) -> None:
        plan = plan_build(
            self.graph,
            states={"render.logo": BuildState.DIRTY, "deliver.web": BuildState.DIRTY},
            cache=(
                k.cache_entry(self.graph, "render.logo"),
                k.cache_entry(self.graph, "deliver.web", layer=CacheLayer.FINAL),
            ),
            trust=k.cache_trust(),
            context=k.cache_context(),
            now_ms=NOW,
        )
        self.assertEqual(plan.reused, ("deliver.web", "render.logo"))
        self.assertEqual(len(plan.receipts), 2)
        self.assertTrue(plan.is_settled)

    def test_a_changed_context_is_a_different_claim_and_the_hit_is_lost(self) -> None:
        entry = k.cache_entry(self.graph, "render.logo")
        plan = self.with_entry("render.logo", entry, context=k.cache_context(profile="other"))
        step = plan.at("render.logo")
        self.assertIs(step.disposition, WorkDisposition.REBUILD)
        self.assertIn("context_fingerprint", step.rejection.text)
        self.assertIn(PoisonCheck.KEY_SCHEMA.value, step.rejection.text)

    def test_an_entry_keyed_to_another_node_is_refused_before_it_is_read(self) -> None:
        with self.assertRaises(BuildError):
            plan_build(
                self.graph,
                states={"render.logo": BuildState.DIRTY},
                cache={"source.logo": k.cache_entry(self.graph, "render.logo")},
                trust=k.cache_trust(),
                context=k.cache_context(),
                now_ms=NOW,
            )
        mapped = plan_build(
            self.graph,
            states={"render.logo": BuildState.DIRTY},
            cache={"render.logo": k.cache_entry(self.graph, "render.logo")},
            trust=k.cache_trust(),
            context=k.cache_context(),
            now_ms=NOW,
        )
        self.assertIs(mapped.at("render.logo").disposition, WorkDisposition.REUSE)

    def test_a_drift_in_rights_or_environment_costs_the_hit(self) -> None:
        entry = k.cache_entry(self.graph, "render.logo")
        plain = self.with_entry("render.logo", entry)
        self.assertIs(plain.at("render.logo").disposition, WorkDisposition.REUSE)
        asked = self.with_entry("render.logo", entry, rights_digest=k.digest("rights.now"))
        self.assertIs(asked.at("render.logo").disposition, WorkDisposition.REBUILD)
        self.assertIn(PoisonCheck.RIGHTS_PROVENANCE_DRIFT.value, asked.at("render.logo").rejection.text)

    def test_the_plan_build_requires_a_bound_graph(self) -> None:
        with self.assertRaises(SchemaValidationError):
            plan_build(self.graph.revision)


class JournalAndRecovery(unittest.TestCase):
    """Staged bytes are not canonical until a commit says so."""

    def setUp(self) -> None:
        self.graph = k.bound()
        self.plan = plan_build(self.graph, states={"render.logo": BuildState.DIRTY})
        self.journal = BuildJournal.begin(self.plan, at_ms=NOW)

    def event(self, journal, kind, **over):
        return journal.with_event(kind, **over)

    def test_a_journal_begins_with_the_plan_it_belongs_to(self) -> None:
        self.assertEqual(len(self.journal.events), 1)
        first = self.journal.events[0]
        self.assertIs(first.kind, JournalKind.ATTEMPT_STARTED)
        self.assertEqual(first.sequence, 1)
        self.assertEqual(self.journal.plan_digest, self.plan.digest())
        self.assertFalse(self.journal.closed)
        started = self.journal.with_event("PLAN_ADOPTED", detail="adopted")
        self.assertEqual(started.events[1].sequence, 2)
        self.assertEqual(len(self.journal.events), 1, "a journal is an immutable value")
        self.assertEqual(started.events[1].plan_digest, self.journal.plan_digest)

    def test_a_bytes_claim_must_name_a_port_and_a_digest(self) -> None:
        with self.assertRaises(BuildError):
            self.journal.with_event("OUTPUT_STAGED", node_id="render.logo", port_ids=("out",))
        with self.assertRaises(BuildError):
            self.journal.with_event("OUTPUT_STAGED", node_id="render.logo", output_digest=k.digest("x"))
        with self.assertRaises(BuildError):
            self.journal.with_event("NODE_STARTED")
        with self.assertRaises(BuildError):
            self.journal.with_event("OUTPUT_COMMITTED", node_id="render.logo")

    def test_a_commit_may_only_name_bytes_this_attempt_staged(self) -> None:
        started = self.journal.with_event("NODE_STARTED", node_id="render.logo")
        with self.assertRaises(BuildError):
            started.with_event(
                "OUTPUT_COMMITTED", node_id="render.logo", port_ids=("out",), output_digest=k.digest("x")
            )
        staged = started.with_event(
            "OUTPUT_STAGED", node_id="render.logo", port_ids=("out",), output_digest=k.digest("bytes.render.logo")
        )
        self.assertEqual(staged.pending_temporary, {"render.logo": ["out"]})
        self.assertEqual(staged.committed_outputs, {})
        committed = staged.with_event(
            "OUTPUT_COMMITTED", node_id="render.logo", port_ids=("out",), output_digest=k.digest("bytes.render.logo")
        )
        self.assertEqual(committed.committed_outputs, {"render.logo": {"out": k.digest("bytes.render.logo")}})
        self.assertEqual(committed.pending_temporary, {})

    def test_a_discard_is_not_un_happened_by_a_commit(self) -> None:
        staged = self.journal.with_event(
            "OUTPUT_STAGED", node_id="render.logo", port_ids=("out",), output_digest=k.digest("bytes.render.logo")
        )
        discarded = staged.with_event("OUTPUT_DISCARDED", node_id="render.logo", port_ids=("out",))
        with self.assertRaises(BuildError):
            discarded.with_event(
                "OUTPUT_COMMITTED", node_id="render.logo", port_ids=("out",), output_digest=k.digest("bytes.render.logo")
            )
        self.assertEqual(discarded.staged_outputs["render.logo"], {"out": k.digest("bytes.render.logo")})
        self.assertEqual(discarded.committed_outputs, {})

    def test_a_closed_attempt_journals_nothing_more(self) -> None:
        ended = self.journal.with_event("ATTEMPT_COMMITTED")
        self.assertTrue(ended.closed)
        self.assertTrue(ended.committed)
        self.assertIs(ended.ending_kind, JournalKind.ATTEMPT_COMMITTED)
        with self.assertRaises(BuildError):
            ended.with_event("NODE_STARTED", node_id="deliver.web")
        cancelled = self.journal.with_event("ATTEMPT_CANCELLED", detail="the operator stopped it")
        self.assertTrue(cancelled.cancelled)
        self.assertFalse(cancelled.committed)

    def test_the_view_the_rest_of_the_kernel_may_use_is_only_committed(self) -> None:
        started = self.journal.with_event("NODE_STARTED", node_id="render.logo")
        self.assertEqual(started.in_flight, ("render.logo",))
        self.assertEqual(started.started_nodes, ("render.logo",))
        self.assertEqual(started.completed_nodes, ())
        completed = started.with_event("NODE_COMPLETED", node_id="render.logo")
        self.assertEqual(completed.in_flight, ())
        hit = completed.with_event("CACHE_HIT", node_id="deliver.web", output_digest=k.digest("x"))
        self.assertEqual(hit.hits, ("deliver.web",))
        self.assertEqual(hit.misses, ())
        failed = completed.with_event("NODE_FAILED", node_id="deliver.web", detail="worker died")
        self.assertEqual(failed.failed_nodes, ("deliver.web",))
        self.assertTrue(JournalKind.NODE_FAILED.reports_failure)
        self.assertTrue(JournalKind.OUTPUT_STAGED.names_output)
        self.assertFalse(JournalKind.VALIDATOR_RAN.names_output)

    def test_recovery_keeps_committed_work_and_discards_half_staged_bytes(self) -> None:
        staged = self.journal.with_event(
            "OUTPUT_STAGED", node_id="render.logo", port_ids=("out",), output_digest=k.digest("bytes.render.logo")
        ).with_event("NODE_STARTED", node_id="render.logo")
        verdict = staged.recover(self.plan)
        self.assertIs(verdict.classification, RecoveryClass.CLEAN)
        self.assertEqual(verdict.must_clean, ("render.logo",))
        self.assertTrue(verdict.may_trust_committed)
        self.assertIn("never committed", " ".join(verdict.reasons))

        started = self.journal.with_event("NODE_STARTED", node_id="render.logo")
        resumed = started.recover(self.plan)
        self.assertIs(resumed.classification, RecoveryClass.RESUME)
        self.assertEqual(resumed.resumable, ("render.logo",))

        finished = started.with_event("NODE_COMPLETED", node_id="render.logo")
        reused = finished.recover(self.plan)
        self.assertIs(reused.classification, RecoveryClass.REUSE)
        self.assertEqual(reused.done, ("render.logo",))

        cancelled = self.journal.with_event("ATTEMPT_CANCELLED")
        self.assertIs(cancelled.recover(self.plan).classification, RecoveryClass.RESTART)
        other = plan_build(self.graph, states={"render.logo": BuildState.DIRTY, "deliver.web": BuildState.DIRTY})
        swapped = finished.recover(other)
        self.assertIs(swapped.classification, RecoveryClass.RESTART)
        self.assertEqual(swapped.restart, other.node_ids)
        self.assertIn("a changed plan invalidates every partial claim", " ".join(swapped.reasons))

    def test_only_reuse_keeps_staged_bytes(self) -> None:
        self.assertFalse(RecoveryClass.RESTART.keeps_committed_work)
        self.assertTrue(RecoveryClass.CLEAN.keeps_committed_work)
        self.assertEqual(
            [item.value for item in RecoveryClass if item.discards_staged_output],
            ["RESUME", "CLEAN", "RESTART"],
        )
        self.assertEqual([item.value for item in RecoveryClass if not item.discards_staged_output], ["REUSE"])

    def test_a_recovery_verdict_cannot_both_keep_and_discard(self) -> None:
        with self.assertRaises(BuildError):
            RecoveryVerdict(
                attempt_id=k.new_id(),
                classification=RecoveryClass.CLEAN,
                done=("render.logo",),
                must_clean=("render.logo",),
                reasons=("contradiction",),
            )
        with self.assertRaises(BuildError):
            RecoveryVerdict(attempt_id=k.new_id(), classification=RecoveryClass.RESUME)

    def test_the_journal_reports_where_it_disagreed_with_the_plan(self) -> None:
        hit = self.journal.with_event("NODE_STARTED", node_id="render.logo").with_event(
            "NODE_COMPLETED", node_id="render.logo"
        ).with_event("CACHE_HIT", node_id="render.logo", output_digest=k.digest("x"))
        findings = hit.validate_against(self.plan)
        self.assertEqual(len(findings), 2)
        self.assertIn("reports a cache hit but the plan decided REBUILD", findings[0])
        self.assertIn("completed without committing its outputs", findings[1])

    def test_a_journal_ahead_of_the_plan_itself_is_flagged(self) -> None:
        other = plan_build(self.graph, states={"render.logo": BuildState.DIRTY, "deliver.web": BuildState.DIRTY})
        started = self.journal.with_event("NODE_STARTED", node_id="deliver.web").with_event(
            "NODE_COMPLETED", node_id="deliver.web"
        )
        findings = started.validate_against(self.plan)
        self.assertIn("which the plan does not contain", " ".join(findings))
        self.assertEqual(
            started.validate_against(other),
            ("journal plan " + self.journal.plan_digest[:12] + " is not the plan on the table",),
        )

    def test_an_atomic_output_set_may_not_be_committed_one_port_at_a_time(self) -> None:
        wide = MaterializationGraph(
            revision=GraphRevision(
                revision_id=k.new_id(),
                definition=k.definition(
                    k.node(
                        "poster.two",
                        NodeRole.OPERATION,
                        outputs=(k.output("out", type_id="raster.png"), k.output("thumb", type_id="raster.jpg")),
                    )
                ),
            ),
            materializations=(),
        )
        plan = plan_build(wide, states={"poster.two": BuildState.DIRTY})
        journal = BuildJournal.begin(plan).with_event("NODE_STARTED", node_id="poster.two").with_event(
            "OUTPUT_STAGED",
            node_id="poster.two",
            port_ids=("out", "thumb"),
            output_digest=k.digest("poster"),
        ).with_event("NODE_COMPLETED", node_id="poster.two").with_event(
            "OUTPUT_COMMITTED", node_id="poster.two", port_ids=("out",), output_digest=k.digest("poster")
        )
        findings = journal.validate_against(plan)
        self.assertIn("atomic output set", " ".join(findings))
        promiscuous = plan_build(self.graph, states={"render.logo": BuildState.DIRTY})
        extra = BuildJournal.begin(promiscuous).with_event(
            "OUTPUT_STAGED", node_id="render.logo", port_ids=("ghost.port",), output_digest=k.digest("x")
        ).with_event(
            "OUTPUT_COMMITTED", node_id="render.logo", port_ids=("ghost.port",), output_digest=k.digest("x")
        )
        self.assertIn("committed outputs the graph never promised", " ".join(extra.validate_against(promiscuous)))

    def test_a_journal_is_one_attempt_only_and_has_no_gaps(self) -> None:
        first = self.journal.events[0]

        def tail(sequence: int, *, attempt_id: str | None = None, event_id: str | None = None) -> JournalEvent:
            return JournalEvent(
                event_id=event_id or k.new_id(),
                attempt_id=attempt_id or self.journal.attempt_id,
                kind=JournalKind.PLAN_ADOPTED,
                sequence=sequence,
            )

        def journal(*events: JournalEvent) -> BuildJournal:
            return BuildJournal(
                attempt_id=self.journal.attempt_id,
                plan_digest=self.journal.plan_digest,
                events=events,
            )

        with self.assertRaises(BuildError):
            journal(first, tail(2, attempt_id=k.new_id()))
        with self.assertRaises(BuildError):
            journal(first, tail(2, event_id=first.event_id))
        with self.assertRaises(BuildError):
            # A gap means an event was lost, and a lost event may be a lost commit.
            journal(first, tail(3))
        with self.assertRaises(BuildError):
            journal(tail(2), first)
        with self.assertRaises(BuildError):
            journal()
        self.assertEqual(journal(first, tail(2)).events[1].sequence, 2)

    def test_an_event_owes_its_own_kind_questions(self) -> None:
        with self.assertRaises(SchemaValidationError):
            JournalEvent(event_id=k.new_id(), attempt_id=k.new_id(), kind=JournalKind.NODE_STARTED, sequence=0)
        with self.assertRaises(SchemaValidationError):
            JournalEvent(event_id=k.new_id(), attempt_id=k.new_id(), kind="NOT_A_KIND", sequence=1)
        event = JournalEvent(
            event_id=k.new_id(),
            attempt_id=k.new_id(),
            kind=JournalKind.OUTPUT_STAGED,
            sequence=1,
            node_id="render.logo",
            port_ids=("out", "out"),
            output_digest=k.digest("x"),
            detail="staged",
        )
        self.assertEqual(event.port_ids, ("out",))
        self.assertIn("#1 render.logo[out]", event.text)


class IncrementalOracle(unittest.TestCase):
    """Incremental correctness is never allowed to be weaker than the full build."""

    def setUp(self) -> None:
        self.graph = k.bound()

    def test_a_deterministic_rebuild_is_demanded_to_match_byte_for_byte(self) -> None:
        plan = decide(rebuild("render.logo"))
        verdict = verify_incremental(
            plan,
            produced={"render.logo": k.digest("render.new")},
            reference={"render.logo": k.digest("render.new")},
        )
        self.assertTrue(verdict.agrees)
        self.assertEqual(verdict.byte_exact, ("render.logo",))
        self.assertIn("reproduced the full build's bytes exactly", verdict.at("render.logo").reasons[0])

    def test_a_missed_dirty_node_is_a_disagreement_not_a_rounding_error(self) -> None:
        plan = decide(rebuild("render.logo"))
        verdict = verify_incremental(
            plan,
            produced={"render.logo": k.digest("render.new")},
            reference={"render.logo": k.digest("stale")},
        )
        self.assertFalse(verdict.agrees)
        self.assertEqual(verdict.disagreements[0].node_id, "render.logo")
        self.assertIn("the increment missed something the delta said was dirty", verdict.text)

    def test_a_byte_claiming_node_cannot_be_judged_without_bytes(self) -> None:
        plan = decide(rebuild("render.logo"))
        verdict = verify_incremental(plan, produced={}, reference={})
        comparison = verdict.at("render.logo")
        self.assertEqual(comparison.mode, "EXACT")
        self.assertFalse(comparison.matched)
        self.assertIn("one side named no bytes", comparison.reasons[0])

    def test_a_hit_serving_bytes_it_never_admitted_is_indicted(self) -> None:
        step = reuse(self.graph)
        plan = decide(step)
        verdict = verify_incremental(
            plan,
            produced={"render.logo": k.digest("something.else")},
            reference={"render.logo": k.digest("something.else")},
        )
        comparison = verdict.at("render.logo")
        self.assertFalse(comparison.matched)
        self.assertIn("the cache served bytes its own admission never covered", comparison.reasons[0])

    def test_a_stochastic_node_is_judged_by_cause_and_not_by_digest(self) -> None:
        step = rebuild("render.logo", reproducibility=ReproducibilityClass.STOCHASTIC)
        plan = decide(step)
        quiet = verify_incremental(plan, produced={"render.logo": k.digest("a")}, reference={"render.logo": k.digest("b")})
        self.assertEqual(quiet.equivalence_only, ("render.logo",))
        self.assertTrue(quiet.agrees, "different bytes from a stochastic node are not a cache bug")

        other = k.bound(records=(k.materialization("source.logo", seed="changed.source"),))
        verdict = verify_incremental(
            plan,
            produced={"render.logo": k.digest("a")},
            reference={"render.logo": k.digest("b")},
            fingerprints={"render.logo": compute_fingerprint(self.graph, "render.logo")},
            reference_fingerprints={"render.logo": compute_fingerprint(other, "render.logo")},
        )
        comparison = verdict.at("render.logo")
        self.assertFalse(comparison.matched)
        self.assertTrue(any("stale dependency consumed" in item for item in comparison.reasons))

    def test_a_blocked_step_is_refused_rather_than_judged(self) -> None:
        plan = plan_build(
            k.bound(records=(k.materialization("source.logo"), k.materialization("deliver.web")))
        )
        verdict = verify_incremental(plan, produced={}, reference={})
        self.assertEqual(verdict.at("deliver.web").mode, "REFUSED")
        self.assertIn("work that was never run", verdict.at("deliver.web").reasons[0])
        self.assertEqual(verdict.at("render.logo").mode, "EXACT")

    def test_the_oracle_judges_each_node_once(self) -> None:
        with self.assertRaises(BuildError):
            IncrementalVerdict(
                graph_id="graph.test",
                plan_digest=decide(rebuild("render.logo")).digest(),
                comparisons=(
                    NodeComparison(node_id="render.logo", mode="EXACT", disposition=WorkDisposition.REBUILD, reasons=("a",)),
                    NodeComparison(node_id="render.logo", mode="EXACT", disposition=WorkDisposition.REBUILD, reasons=("b",)),
                ),
            )
        with self.assertRaises(SchemaValidationError):
            NodeComparison(node_id="render.logo", mode="CLOSE ENOUGH", disposition=WorkDisposition.REBUILD)
        with self.assertRaises(BuildError):
            NodeComparison(node_id="render.logo", mode="EXACT", disposition=WorkDisposition.REBUILD)
        with self.assertRaises(SchemaValidationError):
            NodeComparison(node_id="render.logo", mode="EXACT", disposition=WorkDisposition.REBUILD, reference_digest="short")
        verdict = IncrementalVerdict(graph_id="graph.test", plan_digest=k.digest("plan"))
        self.assertEqual(verdict.comparisons, ())
        with self.assertRaises(BuildError):
            verdict.at("render.logo")

    def test_an_incremental_run_over_a_real_plan_agrees_with_the_full_build(self) -> None:
        plan = plan_build(self.graph, delta=stated(k.change("source.logo", DependencyFacet.CONTENT)))
        produced = {step.node_id: k.digest(f"fresh.{step.node_id}") for step in plan.steps}
        verdict = verify_incremental(plan, produced=produced, reference=dict(produced))
        self.assertTrue(verdict.agrees)
        self.assertEqual(verdict.plan_digest, plan.digest())
        self.assertEqual(len(verdict.comparisons), 3)


class ShadowRebuilds(unittest.TestCase):
    """Rebuilding something the frontier called clean is how under-invalidation is found."""

    def setUp(self) -> None:
        self.graph = k.bound()
        self.plan = plan_build(
            self.graph,
            states={"render.logo": BuildState.DIRTY, "deliver.web": BuildState.DIRTY},
            cache=(
                k.cache_entry(self.graph, "render.logo"),
                k.cache_entry(self.graph, "deliver.web", layer=CacheLayer.FINAL),
            ),
            trust=k.cache_trust(),
            context=k.cache_context(),
            now_ms=NOW,
        )
        self.assertEqual(self.plan.reused, ("deliver.web", "render.logo"))

    def result(self, node_id: str, **over) -> ShadowResult:
        served = self.plan.at(node_id).receipt.result_digest
        base = dict(node_id=node_id, cached_digest=served, rebuilt_digest=served)
        base.update(over)
        return ShadowResult(**base)

    def test_a_sample_of_clean_nodes_that_agreed_proves_the_frontier(self) -> None:
        audit = audit_shadow_rebuilds(self.plan, (self.result("render.logo"), self.result("deliver.web")))
        self.assertEqual(audit.sampled, 2)
        self.assertTrue(audit.clean)
        self.assertEqual((audit.indictments, audit.noisy), ((), ()))
        self.assertEqual(audit.plan_digest, self.plan.digest())

    def test_a_deterministic_difference_indicts_the_cache_and_names_its_key(self) -> None:
        accused = self.result(
            "render.logo",
            rebuilt_digest=k.digest("rebuilt.different"),
            reproducibility=ReproducibilityClass.DETERMINISTIC,
            key_digest=self.plan.at("render.logo").key.address,
        )
        noisy = self.result(
            "deliver.web",
            rebuilt_digest=k.digest("also.different"),
            reproducibility=ReproducibilityClass.STOCHASTIC,
        )
        audit = audit_shadow_rebuilds(self.plan, (accused, noisy))
        self.assertFalse(audit.clean)
        self.assertEqual([item.node_id for item in audit.indictments], ["render.logo"])
        self.assertEqual([item.node_id for item in audit.noisy], ["deliver.web"])
        self.assertIn("stochastic: bytes are not a verdict", audit.text)
        entries = (
            k.cache_entry(self.graph, "render.logo"),
            k.cache_entry(self.graph, "deliver.web", layer=CacheLayer.FINAL),
        )
        self.assertEqual([entry.key.node_id for entry in audit.widening(entries)], ["render.logo"])
        self.assertEqual(audit.widening(()), ())

    def test_an_indictment_widens_quarantine_and_the_next_plan_refuses_the_entry(self) -> None:
        accused = self.result(
            "render.logo",
            rebuilt_digest=k.digest("rebuilt.different"),
            reproducibility=ReproducibilityClass.DETERMINISTIC,
            key_digest=self.plan.at("render.logo").key.address,
        )
        audit = audit_shadow_rebuilds(self.plan, (accused,))
        self.assertEqual(audit.indictments, (accused,))
        entry = k.cache_entry(self.graph, "render.logo")
        ledger = QuarantineLedger(now_ms=NOW).widened(entry, "a shadow rebuild disagreed with these bytes")
        refused = admit_reuse(entry, k.reuse_request(self.graph, "render.logo"), trust=k.cache_trust(), quarantine=ledger)
        self.assertIsInstance(refused, ReuseRejection)
        plan = named_hit(self.graph, "render.logo", entry, quarantine=ledger)
        self.assertIs(plan.at("render.logo").disposition, WorkDisposition.REBUILD)

    def test_a_shadow_rebuild_must_be_of_a_node_the_plan_reused(self) -> None:
        rebuild_plan = plan_build(self.graph, states={"render.logo": BuildState.DIRTY})
        with self.assertRaises(BuildError):
            audit_shadow_rebuilds(rebuild_plan, (self.result("render.logo"),))
        with self.assertRaises(BuildError):
            audit_shadow_rebuilds(
                rebuild_plan,
                (ShadowResult(node_id="source.logo", cached_digest=k.digest("a"), rebuilt_digest=k.digest("a")),),
            )
        allowed = audit_shadow_rebuilds(
            rebuild_plan,
            (ShadowResult(node_id="source.logo", cached_digest=k.digest("a"), rebuilt_digest=k.digest("a")),),
            reuse_only=False,
        )
        self.assertEqual(allowed.sampled, 1)

    def test_one_node_is_sampled_once(self) -> None:
        with self.assertRaises(BuildError):
            audit_shadow_rebuilds(self.plan, (self.result("render.logo"), self.result("render.logo")))
        with self.assertRaises(SchemaValidationError):
            ShadowResult(node_id="render.logo", cached_digest=k.digest("a"), rebuilt_digest="nope")
        self.assertTrue(ShadowResult(node_id="render.logo", cached_digest=k.digest("a"), rebuilt_digest=k.digest("a")).claims_bytes)


class VariantCoalescing(unittest.TestCase):
    """Shared work is fused only when the keys prove it is the same work."""

    def setUp(self) -> None:
        self.graph = k.bound()

    def key(self, node_id: str, context=None, layer=CacheLayer.INTERMEDIATE):
        fingerprint = compute_fingerprint(self.graph, node_id)
        return k.CacheKey.of(
            node_id,
            build_fingerprint=fingerprint.fingerprint,
            context=context or k.cache_context(),
            layer=layer,
        )

    def candidate(self, variant_id: str, node_id: str, **over) -> VariantCandidate:
        return VariantCandidate(variant_id=variant_id, node_id=node_id, key=self.key(node_id, **over), **{})

    def test_two_variants_that_want_the_same_claim_pay_for_it_once(self) -> None:
        batch = coalesce_variants(
            "graph.test",
            (
                VariantCandidate(variant_id="variant.ptbr", node_id="render.logo", key=self.key("render.logo")),
                VariantCandidate(variant_id="variant.en", node_id="render.logo", key=self.key("render.logo")),
                VariantCandidate(
                    variant_id="variant.ptbr",
                    node_id="deliver.web",
                    key=self.key("deliver.web", layer=CacheLayer.FINAL),
                ),
            ),
        )
        self.assertEqual((batch.requested, batch.runs, batch.runs_saved), (3, 2, 1))
        self.assertEqual([item.node_id for item in batch.distinct], ["deliver.web"])
        group = batch.groups_for("render.logo")[0]
        self.assertEqual(group.variants, ("variant.en", "variant.ptbr"))
        self.assertEqual(group.layer, CacheLayer.INTERMEDIATE.value)
        self.assertEqual(group.key_digest, self.key("render.logo").address)
        self.assertEqual(batch.groups_for("deliver.web"), ())
        self.assertIn("runs as 2", batch.text)

    def test_a_different_context_is_different_work_and_is_never_fused(self) -> None:
        batch = coalesce_variants(
            "graph.test",
            (
                VariantCandidate(variant_id="variant.ptbr", node_id="render.logo", key=self.key("render.logo")),
                VariantCandidate(
                    variant_id="variant.dark",
                    node_id="render.logo",
                    key=self.key("render.logo", context=k.cache_context(profile="dark")),
                ),
            ),
        )
        self.assertEqual(batch.shared, ())
        self.assertEqual([item.variant_id for item in batch.distinct], ["variant.dark", "variant.ptbr"])
        self.assertEqual(batch.runs_saved, 0)

    def test_a_node_may_appear_in_several_shared_groups_when_variants_split(self) -> None:
        batch = coalesce_variants(
            "graph.test",
            (
                VariantCandidate(variant_id="variant.a", node_id="render.logo", key=self.key("render.logo")),
                VariantCandidate(variant_id="variant.b", node_id="render.logo", key=self.key("render.logo")),
                VariantCandidate(
                    variant_id="variant.c",
                    node_id="render.logo",
                    key=self.key("render.logo", context=k.cache_context(profile="dark")),
                ),
                VariantCandidate(
                    variant_id="variant.d",
                    node_id="render.logo",
                    key=self.key("render.logo", context=k.cache_context(profile="dark")),
                ),
            ),
        )
        self.assertEqual(batch.requested, 4)
        self.assertEqual(batch.runs, 2)
        self.assertEqual(len(batch.shared), 2)
        self.assertEqual(
            sorted(sorted(group.variants) for group in batch.groups_for("render.logo")),
            [["variant.a", "variant.b"], ["variant.c", "variant.d"]],
        )

    def test_a_variant_cannot_both_join_a_shared_run_and_pay_for_itself(self) -> None:
        with self.assertRaises(BuildError):
            CoalescedBatch(
                graph_id="graph.test",
                shared=(
                    SharedWork(
                        node_id="render.logo",
                        key_digest=k.digest("shared"),
                        variants=("variant.ptbr", "variant.en"),
                    ),
                ),
                distinct=(
                    VariantCandidate(
                        variant_id="variant.ptbr", node_id="render.logo", key=self.key("render.logo")
                    ),
                ),
            )

    def test_the_cohorts_are_refused_before_they_are_grouped(self) -> None:
        with self.assertRaises(BuildError):
            coalesce_variants("graph.test", ())
        with self.assertRaises(BuildError):
            coalesce_variants(
                "graph.test",
                (
                    VariantCandidate(variant_id="variant.ptbr", node_id="render.logo", key=self.key("render.logo")),
                    VariantCandidate(
                        variant_id="variant.ptbr",
                        node_id="render.logo",
                        key=self.key("render.logo", context=k.cache_context(profile="dark")),
                    ),
                ),
            )
        with self.assertRaises(SchemaValidationError):
            VariantCandidate(
                variant_id="variant.ptbr", node_id="render.logo", key=self.key("deliver.web", layer=CacheLayer.FINAL)
            )
        with self.assertRaises(BuildError):
            SharedWork(node_id="render.logo", key_digest=k.digest("shared"), variants=("variant.ptbr",))

    def test_the_fingerprint_a_candidate_carries_must_be_its_node(self) -> None:
        with self.assertRaises(SchemaValidationError):
            VariantCandidate(
                variant_id="variant.ptbr",
                node_id="render.logo",
                key=self.key("render.logo"),
                fingerprint=compute_fingerprint(self.graph, "deliver.web"),
            )


class ExplainTraceAndLookups(unittest.TestCase):
    """Every decision the planner made has to be readable by a person and a machine."""

    def setUp(self) -> None:
        self.graph = k.bound()
        self.delta = stated(k.change("source.logo", DependencyFacet.CONTENT))
        self.plan = plan_build(self.graph, delta=self.delta)
        self.cone = impact_of(self.graph, self.delta.changes)

    def test_a_trace_reads_the_step_and_not_an_imagination_of_it(self) -> None:
        journal = BuildJournal.begin(self.plan).with_event("NODE_STARTED", node_id="deliver.web")
        trace = explain_build(self.plan, "deliver.web", cone=self.cone, journal=journal)
        self.assertIs(trace.state, BuildState.DIRTY)
        self.assertIs(trace.disposition, WorkDisposition.REBUILD)
        self.assertEqual(trace.lines[0], "deliver.web is DIRTY, so it will REBUILD")
        self.assertIn(
            "  reached from: render.logo -> edge.deliver -> deliver.web", trace.lines
        )
        self.assertEqual(trace.cone, ("render.logo -> edge.deliver -> deliver.web",))
        self.assertIn("  waits for: render.logo", trace.lines)
        self.assertIn("  journal: #2 deliver.web", trace.lines)
        self.assertEqual(trace.plan_digest, self.plan.digest())
        self.assertEqual(trace.text.count("\n"), len(trace.lines) - 1)

    def test_the_root_of_the_change_is_explained_by_the_change_itself(self) -> None:
        trace = explain_build(self.plan, "source.logo", cone=self.cone)
        self.assertEqual(trace.cone, ())
        self.assertEqual(trace.downstream, ("deliver.web", "render.logo"))
        self.assertIn("changed in facet CONTENT", trace.causes[0])
        self.assertIn("  blocks until done: deliver.web, render.logo", trace.lines)

    def test_a_cache_decision_is_part_of_the_explanation(self) -> None:
        hit = named_hit(self.graph, "render.logo", k.cache_entry(self.graph, "render.logo"))
        trace = explain_build(hit, "render.logo")
        self.assertTrue(trace.cache)
        self.assertIn("admitted:", trace.cache[0])
        refused = named_hit(
            self.graph, "render.logo", k.cache_entry(self.graph, "render.logo", reuse_class=ReuseClass.NO_REUSE)
        )
        refused_trace = explain_build(refused, "render.logo")
        self.assertTrue(refused_trace.cache)
        self.assertIn(PoisonCheck.PRODUCER_ADMISSION.value, " ".join(refused_trace.cache))
        repaired = plan_build(
            self.graph,
            delta=stated(k.change("render.logo", DependencyFacet.CONTENT, slice=REGION)),
            repair_slices={"render.logo": REGION},
        )
        self.assertIn("region=left", " ".join(explain_build(repaired, "render.logo").repairs))

    def test_a_trace_without_a_cause_is_not_a_trace(self) -> None:
        with self.assertRaises(BuildError):
            BuildExplainTrace(
                node_id="render.logo", state=BuildState.DIRTY, disposition=WorkDisposition.REBUILD
            )
        with self.assertRaises(BuildError):
            explain_build(self.plan, "node.absent")

    def test_a_lookup_holds_either_a_receipt_or_a_named_refusal(self) -> None:
        receipt = k.admitted_receipt(self.graph, "render.logo")
        granted = CacheLookup(node_id="render.logo", key=receipt.key, outcome=receipt)
        self.assertTrue(granted.admitted)
        self.assertIs(granted.receipt, receipt)
        self.assertIsNone(granted.rejection)
        self.assertIn("EXACT_REUSE", granted.text)

        entry = k.cache_entry(self.graph, "render.logo", reuse_class=ReuseClass.NO_REUSE)
        refusal = admit_reuse(entry, k.reuse_request(self.graph, "render.logo"), trust=k.cache_trust())
        refused = CacheLookup(node_id="render.logo", key=refusal.key, outcome=refusal, entry=entry)
        self.assertFalse(refused.admitted)
        self.assertIsNone(refused.receipt)
        self.assertEqual(len(refused.rejection.checks), 9)

    def test_a_lookup_cannot_mix_a_node_with_another_nodes_claim(self) -> None:
        receipt = k.admitted_receipt(self.graph, "render.logo")
        with self.assertRaises(SchemaValidationError):
            CacheLookup(node_id="deliver.web", key=receipt.key, outcome=receipt)
        with self.assertRaises(SchemaValidationError):
            CacheLookup(node_id="deliver.web", key=receipt.key, outcome=receipt.to_payload())
        with self.assertRaises(SchemaValidationError):
            CacheLookup(node_id="render.logo", key=receipt.key, outcome="a yes, probably")


class RoundTripsAndBounds(unittest.TestCase):
    """Area D records serialize completely, and collection sizes are bounded."""

    def setUp(self) -> None:
        self.graph = k.bound()
        self.delta = stated(
            k.change("render.logo", DependencyFacet.CONTENT, port_id="in", slice=REGION),
            k.change("deliver.web", DependencyFacet.QUALITY),
        )
        self.frontier = dirty_frontier(self.graph, self.delta)
        self.repairs = repair_frontier(self.graph, self.frontier, slices={"render.logo": REGION}, whole_node=("deliver.web",))
        self.plan = plan_build(
            self.graph,
            delta=self.delta,
            repair_slices={"render.logo": REGION},
            cache=(k.cache_entry(self.graph, "render.logo"),),
            trust=k.cache_trust(),
            context=k.cache_context(),
            now_ms=NOW,
        )

    def values(self):
        journal = BuildJournal.begin(self.plan)
        yield BuildDelta, stated(k.change("source.logo", DependencyFacet.CONTENT))
        yield DirtyFrontier, self.frontier
        yield RepairFrontier, self.repairs
        yield BuildPlan, self.plan
        yield BuildStep, self.plan.steps[0]
        yield JournalEvent, journal.events[0]
        yield BuildJournal, journal.with_event("NODE_STARTED", node_id="render.logo")
        yield RecoveryVerdict, journal.recover(self.plan)
        yield ShadowResult, ShadowResult(node_id="render.logo", cached_digest=k.digest("a"), rebuilt_digest=k.digest("a"))
        yield CoalescedBatch, coalesce_variants(
            "graph.test",
            (
                VariantCandidate(variant_id="variant.a", node_id="render.logo", key=k.cache_entry(self.graph, "render.logo").key),
                VariantCandidate(variant_id="variant.b", node_id="render.logo", key=k.cache_entry(self.graph, "render.logo").key),
            ),
        )
        yield BuildExplainTrace, explain_build(self.plan, "render.logo")
        yield IncrementalVerdict, verify_incremental(self.plan, produced={}, reference={})

    def test_every_build_record_survives_a_payload_round_trip(self) -> None:
        for kind, value in self.values():
            with self.subTest(kind=kind.__name__):
                restored = kind.from_payload(value.to_payload())
                self.assertEqual(restored.digest(), value.digest())
                self.assertEqual(canonical_json(restored.to_payload()), canonical_json(value.to_payload()))

    def test_a_replan_of_the_same_causes_is_the_same_plan_except_its_id(self) -> None:
        again = plan_build(
            self.graph,
            delta=self.delta,
            repair_slices={"render.logo": REGION},
            cache=(k.cache_entry(self.graph, "render.logo"),),
            trust=k.cache_trust(),
            context=k.cache_context(),
            now_ms=NOW,
        )
        self.assertEqual(again.delta_digest, self.plan.delta_digest)
        self.assertNotEqual(again.plan_id, self.plan.plan_id)
        self.assertEqual(
            [step.disposition for step in again.steps], [step.disposition for step in self.plan.steps]
        )

    def test_frontier_collections_are_bounded(self) -> None:
        with self.assertRaises(SchemaValidationError):
            DirtyNode(node_id="render.logo", reasons=tuple(f"cause {i}" for i in range(256)))
        with self.assertRaises(SchemaValidationError):
            DirtyNode(
                node_id="render.logo",
                reasons=("moved",),
                facets=(DependencyFacet.CONTENT,) * 9,
            )
        with self.assertRaises(SchemaValidationError):
            DirtyNode(
                node_id="render.logo",
                reasons=("moved",),
                slices=tuple(
                    DependencySlice(axis="region", values=(f"value-{i}",)) for i in range(65)
                ),
            )
        with self.assertRaises(SchemaValidationError):
            DirtyNode(
                node_id="render.logo",
                reasons=("moved",),
                port_ids=tuple(f"port.{i}" for i in range(65)),
            )

    def test_step_collections_are_bounded(self) -> None:
        with self.assertRaises(SchemaValidationError):
            rebuild("render.logo", depends_on=tuple(f"node.{i}" for i in range(4097)))
        with self.assertRaises(SchemaValidationError):
            rebuild("render.logo", outputs=tuple(f"port.{i}" for i in range(65)))

    def test_the_frontier_needs_a_digest_it_can_be_re_derived_from(self) -> None:
        with self.assertRaises(SchemaValidationError):
            DirtyFrontier(graph_id="graph.test", delta_digest="nope", nodes=(DirtyNode(node_id="render.logo", reasons=("moved",)),))
        self.assertEqual(self.frontier.delta_digest, self.delta.delta_digest)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
