"""Area C merge law: three-way semantic merge, typed conflicts and transplant.

Merge here is object-level. Two competing renders of the same logo are not two halves
of one answer, so the kernel never averages bytes: the legal outcomes are an explicit
selection, a recomposition or a regeneration, and a disagreement that cannot be shown
to be safe comes back as a typed conflict instead of a silent choice.

Two properties carry most of the tests below. A safe auto-merge must be exactly the
three cases the contract separates (both lines moved alike, or only one line moved),
and a blocking conflict must make a result impossible at the *record* level: a merge
receipt refuses to name a result snapshot while blocking work is still open, so an
unreviewed head move cannot be built even by hand.
"""

from __future__ import annotations

import unittest
import uuid
from dataclasses import replace
from typing import Any

from iris_project_os.branching import (
    Branch,
    BranchLedger,
    BranchProfile,
    ConstraintKind,
    IdentityAnchorPolicy,
    VariantConstraint,
    VariantOption,
    VariantSelection,
    VariantSet,
)
from iris_project_os.diffing import DiffCategory
from iris_project_os.errors import (
    GraphValidationError,
    MergeBlockedError,
    SchemaValidationError,
    SnapshotClosureError,
    UnsupportedVersionError,
)
from iris_project_os.graph import DependencyFacet, MaterializationGraph
from iris_project_os.identity import EntityKind, ExternalRef, new_id
from iris_project_os.limits import MAX_CONFLICTS, MAX_CLOSURE_REFS, MAX_IMPACT_NODES
from iris_project_os.merge import (
    ConflictKind,
    MergeConflict,
    MergeReceipt,
    Resolution,
    ResolutionStrategy,
    advance_merge,
    three_way_merge,
    transplant,
)
from iris_project_os.snapshots import (
    DeltaPrecondition,
    ExternalSideEffect,
    PreconditionKind,
    ProductionDelta,
    Snapshot,
    SnapshotClass,
    SnapshotClosureManifest,
    SnapshotDerivation,
    SnapshotStore,
    commit_snapshot,
)
from iris_project_os.versions import ComponentVersion

from tests import m02_kernel_support as k

PROD = "prod.logo"
NODES = ("source.logo", "render.logo", "deliver.web")
NOW = 1_700_000_000_000
ACTOR = ComponentVersion("m02.os", "1.0.0")
DEFINITION = k.chain_definition()


def stable(seed: str) -> str:
    """A UUID that repeats across runs, so a receipt can be asserted literally."""

    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


BRANCH_ID = stable("branch.main")
PROJECT_ID = stable("project.iris")
PRODUCTION_ID = stable("production.logo")


def record(node_id: str, **over: Any):
    payload: dict[str, Any] = dict(
        attempt=stable(f"attempt.{node_id}"),
        decision=k.ref(EntityKind.QUALITY_DECISION, f"decision.{node_id}"),
    )
    payload.update(over)
    return k.materialization(node_id, **payload)


def chain(records: Any = None, **over: Any) -> MaterializationGraph:
    payload: dict[str, Any] = dict(
        revision=k.revision(DEFINITION),
        materializations=tuple(record(node_id) for node_id in NODES) if records is None else records,
        variant_selection=(),
    )
    payload.update(over)
    return MaterializationGraph(**payload)


def closure(**over: Any) -> SnapshotClosureManifest:
    """A closure over the chain graph with one stable reference per evidence family."""

    graph_value = over.pop("graph", None) or chain()
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


class ThreeHeads:
    """A base and two heads in one store, ready to be merged."""

    def __init__(
        self,
        base: Any = None,
        target: Any = None,
        source: Any = None,
        *,
        classes: Any = (SnapshotClass.LOGICAL_SNAPSHOT,) * 3,
    ) -> None:
        self.store = SnapshotStore()
        self.closures: dict[str, SnapshotClosureManifest] = {}
        self.snapshots: dict[str, Snapshot] = {}
        for role, changes, klass in zip(
            ("base", "target", "source"), (base, target, source), classes
        ):
            manifest = closure(**(changes or {}))
            snapshot = commit_snapshot(
                manifest, snapshot_class=klass, snapshot_id=stable(f"snapshot.{role}"), created_at_ms=NOW
            )
            self.store.commit(snapshot)
            self.closures[role] = manifest
            self.snapshots[role] = snapshot

    @property
    def ids(self) -> dict[str, str]:
        return {role: item.snapshot_id for role, item in self.snapshots.items()}

    def merge(self, **over: Any):
        over.setdefault("created_at_ms", NOW + 1_000)
        return three_way_merge(
            self.store,
            base_snapshot_id=self.ids["base"],
            target_snapshot_id=self.ids["target"],
            source_snapshot_id=self.ids["source"],
            **over,
        )

    def settled(self, **over: Any):
        """The merge result, asserting the contract's happy path out loud."""

        snapshot, receipt = self.merge(**over)
        assert snapshot is not None, receipt.conflicts
        return snapshot, receipt


def relabel(definition: Any, node_id: str, display_name: str) -> Any:
    """A node definition change that touches no port, no edge and no type."""

    return replace(
        definition,
        nodes=tuple(
            replace(item, display_name=display_name) if item.node_id == node_id else item
            for item in definition.nodes
        ),
    )


def refacet(definition: Any, edge_id: str, *facets: Any) -> Any:
    return replace(
        definition,
        edges=tuple(
            replace(item, facets=tuple(facets)) if item.edge_id == edge_id else item
            for item in definition.edges
        ),
    )


def graph_over(definition: Any, **over: Any) -> MaterializationGraph:
    payload: dict[str, Any] = dict(revision=k.revision(definition))
    payload.update(over)
    return chain(**payload)


def heads_on(definition: Any, **over: Any) -> ThreeHeads:
    """Three identical heads whose graph closes over ``definition``."""

    moved = chain(revision=k.revision(definition), **over)
    return ThreeHeads({"graph": moved}, {"graph": moved}, {"graph": moved})


def conflict(subject: str = "render.logo", kind: Any = None, **over: Any) -> MergeConflict:
    payload: dict[str, Any] = dict(
        conflict_id=stable(f"conflict.{subject}"),
        kind=kind or ConflictKind.NODE_DEFINITION_CONFLICT,
        subject=subject,
    )
    payload.update(over)
    return MergeConflict(**payload)


def receipt(**over: Any) -> MergeReceipt:
    payload: dict[str, Any] = dict(
        merge_id=stable("merge.one"),
        base_snapshot_id=stable("snapshot.base"),
        target_snapshot_id=stable("snapshot.target"),
        source_snapshot_id=stable("snapshot.source"),
    )
    payload.update(over)
    return MergeReceipt(**payload)


def resolution(subject: str, strategy: Any = ResolutionStrategy.KEEP_TARGET, **over: Any) -> Resolution:
    payload: dict[str, Any] = dict(subject=subject, strategy=strategy)
    payload.update(over)
    return Resolution(**payload)


def rights(name: str, **over: Any) -> ExternalRef:
    return k.ref(EntityKind.RIGHTS, name, **over)


def option(option_id: str, **over: Any) -> VariantOption:
    payload: dict[str, Any] = dict(option_id=option_id, content_digest=k.digest(f"option.{option_id}"))
    payload.update(over)
    return VariantOption(**payload)


def axis(set_id: str = "axis.quality", options: Any = None, **over: Any) -> VariantSet:
    payload: dict[str, Any] = dict(
        variant_set_id=set_id,
        purpose="delivery quality",
        options=tuple(options if options is not None else (option("standard"), option("premium"), option("preview"))),
        default_option_id="standard",
    )
    payload.update(over)
    return VariantSet(**payload)


def picked(**pairs: Any) -> VariantSelection:
    """A choice written by axis short name, so a test reads as a decision."""

    receipts = pairs.pop("receipts", ())
    chosen = {key if "." in key else f"axis.{key}": value for key, value in pairs.items()}
    return VariantSelection(
        selection_id=stable("selection." + ".".join(f"{key}={value}" for key, value in sorted(chosen.items()))),
        pairs=tuple(sorted(chosen.items())),
        migration_receipt_ids=tuple(receipts),
    )


def ratio_constraint(**over: Any) -> VariantConstraint:
    payload: dict[str, Any] = dict(
        constraint_id="constraint.premium-wide",
        kind=ConstraintKind.REQUIRES,
        when_set="axis.quality",
        when_option="premium",
        target_set="axis.ratio",
        target_options=("wide",),
    )
    payload.update(over)
    return VariantConstraint(**payload)


FACE = k.digest("the persona face")
OTHER_FACE = k.digest("a different face")
MIGRATION = stable("migration.alt")


def persona(**over: Any) -> IdentityAnchorPolicy:
    payload: dict[str, Any] = dict(
        anchor_id="anchor.persona.face",
        policy_ref=k.ref(EntityKind.POLICY, "policy.persona"),
        baseline_digest=FACE,
        baseline_option_id="keynote",
    )
    payload.update(over)
    return IdentityAnchorPolicy(**payload)


def persona_axis(**over: Any) -> VariantSet:
    payload: dict[str, Any] = dict(
        variant_set_id="axis.persona",
        purpose="the spokesperson this delivery speaks as",
        options=(
            option("keynote", anchor_digest=FACE),
            option("alt", anchor_digest=OTHER_FACE, migration_receipt_id=MIGRATION),
        ),
        default_option_id="keynote",
        identity_anchor=persona(),
    )
    payload.update(over)
    return VariantSet(**payload)


def subgraph_definition(interface_version: str = "1.0.0", **over: Any) -> Any:
    """The chain plus one SUBGRAPH node whose boundary contract is declared here."""

    from iris_project_os.graph import NodeRole, SubgraphInterface

    extra = k.node("sub.kit", NodeRole.SUBGRAPH, outputs=(k.output("out", type_id=k.VECTOR),))
    interface = SubgraphInterface(
        node_id="sub.kit", inner_graph_ref=k.ref(EntityKind.GRAPH, "graph.inner"), version=interface_version
    )
    return k.definition(
        *k.chain_definition().nodes, extra, edges=k.chain_definition().edges, interfaces=(interface,), **over
    )


def loose_definition(**over: Any) -> Any:
    """The chain, but the render node's input is optional so one line may drop it."""

    from iris_project_os.graph import NodeRole, ReproducibilityClass

    render = k.node(
        "render.logo",
        NodeRole.OPERATION,
        inputs=(k.input_port("in", type_id=k.VECTOR, required=False),),
        outputs=(k.output("out", type_id=k.RASTER),),
        reproducibility=ReproducibilityClass.DETERMINISTIC,
    )
    return k.definition(
        k.source(), render, k.delivery(),
        edges=(k.edge("edge.render", "source.logo", "render.logo"), k.edge("edge.deliver", "render.logo", "deliver.web")),
        **over,
    )


def dropped_edge(definition: Any, edge_id: str) -> Any:
    return replace(definition, edges=tuple(item for item in definition.edges if item.edge_id != edge_id))


def one_line_drops(edge_id: str) -> ThreeHeads:
    """The target un-plugs a dependency; the other line never touched it.

    Both untouched heads use the same optional-port definition, because a node whose
    required input still demands a producer cannot be dropped silently at all.
    """

    base = loose_definition()
    return ThreeHeads(
        {"graph": graph_over(base)},
        target={"graph": graph_over(dropped_edge(base, edge_id))},
        source={"graph": graph_over(base)},
    )


def graph_conflict_heads() -> ThreeHeads:
    """Two heads each legal alone that cannot be bound together.

    One line retires the delivery node; the other hangs a validation step off it, so
    each head closes on its own but the merged picture names a node that is not there.
    """

    dropped = k.definition(
        k.source(), k.operation(), edges=(k.edge("edge.render", "source.logo", "render.logo"),)
    )
    dropped_records = tuple(record(node_id) for node_id in ("source.logo", "render.logo"))
    extended = k.definition(
        *k.chain_definition().nodes,
        k.validation(),
        edges=(
            k.edge("edge.render", "source.logo", "render.logo"),
            k.edge("edge.deliver", "render.logo", "deliver.web"),
            k.edge("edge.validate", "deliver.web", "validate.quality"),
        ),
    )
    return ThreeHeads(
        {"graph": graph_over(k.chain_definition())},
        target={"graph": graph_over(dropped, materializations=dropped_records)},
        source={"graph": graph_over(extended)},
    )


class ResolutionStrategyTests(unittest.TestCase):
    def test_the_nine_settlements_are_the_frozen_vocabulary(self) -> None:
        self.assertEqual(
            {item.value for item in ResolutionStrategy},
            {
                "KEEP_TARGET",
                "TAKE_SOURCE",
                "EXPLICIT_CHOICE",
                "RECOMPOSE",
                "MIGRATE_IDENTITY",
                "COMPENSATE",
                "RECONCILE",
                "REVALIDATE",
                "DEFER",
            },
        )

    def test_picking_a_side_needs_no_receipt(self) -> None:
        for strategy in (
            ResolutionStrategy.KEEP_TARGET,
            ResolutionStrategy.TAKE_SOURCE,
            ResolutionStrategy.DEFER,
        ):
            self.assertFalse(strategy.needs_evidence, strategy.value)

    def test_six_strategies_assert_work_someone_must_evidence(self) -> None:
        self.assertEqual(
            {item for item in ResolutionStrategy if item.needs_evidence},
            {
                ResolutionStrategy.EXPLICIT_CHOICE,
                ResolutionStrategy.RECOMPOSE,
                ResolutionStrategy.MIGRATE_IDENTITY,
                ResolutionStrategy.COMPENSATE,
                ResolutionStrategy.RECONCILE,
                ResolutionStrategy.REVALIDATE,
            },
        )

    def test_only_deferral_leaves_the_conflict_open(self) -> None:
        self.assertEqual(
            {item for item in ResolutionStrategy if not item.settles}, {ResolutionStrategy.DEFER}
        )

    def test_an_unknown_settlement_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            ResolutionStrategy.parse("HOPE_FOR_THE BEST", "strategy")


class ConflictKindTests(unittest.TestCase):
    def test_the_ten_families_are_the_frozen_vocabulary(self) -> None:
        self.assertEqual(
            {item.value for item in ConflictKind},
            {
                "TOPOLOGY_CONFLICT",
                "NODE_DEFINITION_CONFLICT",
                "ARTIFACT_REVISION_CONFLICT",
                "VARIANT_SELECTION_CONFLICT",
                "VARIANT_CONSTRAINT_CONFLICT",
                "IDENTITY_ANCHOR_CONFLICT",
                "QUALITY_POLICY_CONFLICT",
                "RIGHTS_PROVENANCE_CONFLICT",
                "DELIVERY_RELEASE_CONFLICT",
                "SIDE_EFFECT_CONFLICT",
            },
        )

    def test_only_a_variant_choice_may_travel_unreviewed(self) -> None:
        self.assertEqual(
            {item for item in ConflictKind if not item.blocking_by_default},
            {ConflictKind.VARIANT_SELECTION_CONFLICT},
        )

    def test_every_family_declares_at_least_one_settlement(self) -> None:
        for kind in ConflictKind:
            self.assertTrue(kind.strategies, kind.value)

    def test_no_family_admits_a_settlement_outside_the_vocabulary(self) -> None:
        for kind in ConflictKind:
            for strategy in kind.strategies:
                self.assertIsInstance(strategy, ResolutionStrategy)

    def test_an_identity_disagreement_only_survives_a_migration(self) -> None:
        self.assertEqual(
            ConflictKind.IDENTITY_ANCHOR_CONFLICT.strategies,
            (ResolutionStrategy.KEEP_TARGET, ResolutionStrategy.MIGRATE_IDENTITY),
        )

    def test_a_side_effect_can_never_be_taken_from_either_side(self) -> None:
        self.assertEqual(
            ConflictKind.SIDE_EFFECT_CONFLICT.strategies,
            (
                ResolutionStrategy.KEEP_TARGET,
                ResolutionStrategy.COMPENSATE,
                ResolutionStrategy.RECONCILE,
            ),
        )

    def test_a_granted_release_is_not_a_choice_between_two_values(self) -> None:
        self.assertEqual(
            ConflictKind.DELIVERY_RELEASE_CONFLICT.strategies,
            (ResolutionStrategy.KEEP_TARGET, ResolutionStrategy.TAKE_SOURCE),
        )

    def test_topology_may_defer_but_a_persona_may_not(self) -> None:
        self.assertIn(ResolutionStrategy.DEFER, ConflictKind.TOPOLOGY_CONFLICT.strategies)
        self.assertNotIn(ResolutionStrategy.DEFER, ConflictKind.IDENTITY_ANCHOR_CONFLICT.strategies)
        self.assertNotIn(ResolutionStrategy.DEFER, ConflictKind.SIDE_EFFECT_CONFLICT.strategies)

    def test_deferral_exists_for_exactly_one_family(self) -> None:
        self.assertEqual(
            {kind for kind in ConflictKind if ResolutionStrategy.DEFER in kind.strategies},
            {ConflictKind.TOPOLOGY_CONFLICT},
        )

    def test_an_unknown_family_is_refused_rather_than_filed_under_miscellaneous(self) -> None:
        with self.assertRaises(SchemaValidationError):
            ConflictKind.parse("MISC_CONFLICT", "kind")


class MergeConflictTests(unittest.TestCase):
    def test_a_disagreement_records_all_three_sides(self) -> None:
        item = conflict(target_side="a", source_side="b", base_side="c")
        self.assertEqual((item.base_side, item.target_side, item.source_side), ("c", "a", "b"))
        self.assertFalse(item.is_resolved)

    def test_the_subject_text_names_the_family_it_belongs_to(self) -> None:
        item = conflict("edge.render", ConflictKind.TOPOLOGY_CONFLICT)
        self.assertEqual(item.text, "TOPOLOGY_CONFLICT:edge.render")

    def test_a_reference_side_is_written_as_its_own_text(self) -> None:
        item = conflict(target_side=k.ref(EntityKind.RIGHTS, "rights.new"))
        self.assertEqual(item.target_side, "rights:rights.new")

    def test_a_record_side_is_written_as_a_digest_not_a_dump(self) -> None:
        item = conflict(source_side=k.delivery())
        self.assertTrue(item.source_side.startswith("digest:"))
        self.assertEqual(len(item.source_side), len("digest:") + 64)

    def test_a_number_side_becomes_text(self) -> None:
        self.assertEqual(conflict(target_side=7).target_side, "7")

    def test_an_absent_side_stays_absent(self) -> None:
        self.assertIsNone(conflict(target_side=None).target_side)

    def test_a_side_longer_than_the_readable_limit_is_refused(self) -> None:
        with self.assertRaises(Exception):
            conflict(target_side="x" * 513)

    def test_node_ids_are_deduplicated_and_sorted(self) -> None:
        item = conflict(node_ids=("render.logo", "source.logo", "render.logo"))
        self.assertEqual(item.node_ids, ("render.logo", "source.logo"))

    def test_too_many_nodes_on_one_disagreement_is_refused(self) -> None:
        with self.assertRaises(Exception):
            conflict(node_ids=tuple(f"node.{index}" for index in range(MAX_IMPACT_NODES + 1)))

    def test_blocking_follows_the_family(self) -> None:
        self.assertTrue(conflict(kind=ConflictKind.TOPOLOGY_CONFLICT).blocking)
        self.assertFalse(conflict(kind=ConflictKind.VARIANT_SELECTION_CONFLICT).blocking)

    def test_a_non_boolean_blocking_claim_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            conflict(blocking="yes")

    def test_a_settlement_the_family_does_not_admit_is_refused(self) -> None:
        with self.assertRaises(MergeBlockedError) as caught:
            conflict(
                kind=ConflictKind.IDENTITY_ANCHOR_CONFLICT,
                resolution=ResolutionStrategy.TAKE_SOURCE,
                resolved_by=ACTOR,
            )
        self.assertIn("may only be settled by", str(caught.exception))
        self.assertIn("MIGRATE_IDENTITY", str(caught.exception))

    def test_an_unadmitted_settlement_is_refused_even_when_it_needs_no_evidence(self) -> None:
        with self.assertRaises(MergeBlockedError):
            conflict(kind=ConflictKind.DELIVERY_RELEASE_CONFLICT, resolution=ResolutionStrategy.DEFER)

    def test_a_settlement_that_asserts_work_without_a_receipt_is_refused(self) -> None:
        with self.assertRaises(MergeBlockedError) as caught:
            conflict(resolution=ResolutionStrategy.RECOMPOSE, resolved_by=ACTOR)
        self.assertIn("evidenced by a receipt", str(caught.exception))

    def test_a_settlement_that_asserts_work_names_who_settled_it(self) -> None:
        item = conflict(
            resolution=ResolutionStrategy.RECOMPOSE,
            resolution_ref=k.ref(EntityKind.RECEIPT, "receipt.recompose"),
            resolved_by=ACTOR,
        )
        self.assertTrue(item.is_resolved)
        self.assertEqual(item.resolved_by, ACTOR)

    def test_a_settlement_without_an_actor_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            conflict(
                resolution=ResolutionStrategy.TAKE_SOURCE,
                resolution_ref=k.ref(EntityKind.RECEIPT, "receipt.one"),
            )
        self.assertIn("which actor or component", str(caught.exception))

    def test_keeping_the_target_needs_neither_receipt_nor_actor(self) -> None:
        item = conflict(resolution=ResolutionStrategy.KEEP_TARGET)
        self.assertTrue(item.is_resolved)
        self.assertIsNone(item.resolved_by)

    def test_deferral_is_the_one_settlement_that_leaves_it_open(self) -> None:
        item = conflict(kind=ConflictKind.TOPOLOGY_CONFLICT, blocking=False, resolution=ResolutionStrategy.DEFER)
        self.assertFalse(item.is_resolved)
        self.assertFalse(item.blocking)

    def test_a_blocking_disagreement_cannot_be_deferred(self) -> None:
        with self.assertRaises(MergeBlockedError) as caught:
            conflict(kind=ConflictKind.TOPOLOGY_CONFLICT, resolution=ResolutionStrategy.DEFER)
        self.assertIn("cannot be deferred", str(caught.exception))

    def test_an_unknown_settlement_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            conflict(resolution="SPLIT_THE_DIFFERENCE")

    def test_the_explanation_is_bounded(self) -> None:
        with self.assertRaises(Exception):
            conflict(explanation="why " * 400)

    def test_a_foreign_contract_version_is_refused(self) -> None:
        with self.assertRaises(UnsupportedVersionError):
            conflict(contract_version="m02-contract-v9.9")

    def test_an_unknown_subject_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            conflict(subject="")

    def test_a_disagreement_round_trips_through_its_payload(self) -> None:
        item = conflict(
            resolution=ResolutionStrategy.EXPLICIT_CHOICE,
            resolution_ref=k.ref(EntityKind.RECEIPT, "receipt.choice"),
            resolved_by=ACTOR,
            node_ids=("render.logo",),
        )
        self.assertEqual(MergeConflict.from_payload(item.to_payload()), item)


class ResolutionTests(unittest.TestCase):
    def test_a_settlement_is_addressed_by_subject(self) -> None:
        item = resolution("node:render.logo", ResolutionStrategy.TAKE_SOURCE)
        self.assertEqual(item.subject, "node:render.logo")
        self.assertIsNone(item.kind)

    def test_an_optional_family_is_stored_as_its_text(self) -> None:
        item = resolution("rights:right.new", kind=ConflictKind.RIGHTS_PROVENANCE_CONFLICT)
        self.assertEqual(item.kind, "RIGHTS_PROVENANCE_CONFLICT")

    def test_an_unknown_family_is_still_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            resolution("x", kind="NOT_A_FAMILY")

    def test_evidence_must_be_a_reference(self) -> None:
        with self.assertRaises(SchemaValidationError):
            resolution("x", evidence_ref="a string is not a receipt")

    def test_the_actor_is_a_component_version(self) -> None:
        item = resolution("x", resolved_by=ACTOR)
        self.assertEqual(item.resolved_by, ACTOR)
        with self.assertRaises(Exception):
            resolution("x", resolved_by="the boss")

    def test_an_unknown_settlement_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            resolution("x", "CHOOSE_WISDOM")

    def test_a_note_is_bounded(self) -> None:
        with self.assertRaises(Exception):
            resolution("x", note="n" * 513)


class MergeReceiptTests(unittest.TestCase):
    def test_a_receipt_names_its_three_inputs(self) -> None:
        item = receipt()
        self.assertEqual(item.base_snapshot_id, stable("snapshot.base"))
        self.assertIsNone(item.result_snapshot_id)
        self.assertTrue(item.is_clean)
        self.assertTrue(item.is_cleared)

    def test_the_three_input_ids_are_required(self) -> None:
        for name in ("merge_id", "base_snapshot_id", "target_snapshot_id", "source_snapshot_id"):
            with self.assertRaises(SchemaValidationError):
                receipt(**{name: "not-an-id"})

    def test_the_same_disagreement_is_never_reported_twice(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            receipt(conflicts=(conflict("render.logo"), conflict("render.logo")))
        self.assertIn("same conflict twice", str(caught.exception))

    def test_two_families_sharing_a_subject_are_two_conflicts(self) -> None:
        item = receipt(
            conflicts=(
                conflict("render.logo", ConflictKind.NODE_DEFINITION_CONFLICT),
                conflict("render.logo", ConflictKind.TOPOLOGY_CONFLICT),
            )
        )
        self.assertEqual(len(item.conflicts), 2)

    def test_conflicts_are_ordered_by_family_then_subject(self) -> None:
        item = receipt(
            conflicts=(
                conflict("z", ConflictKind.SIDE_EFFECT_CONFLICT),
                conflict("a", ConflictKind.NODE_DEFINITION_CONFLICT),
            )
        )
        self.assertEqual([entry.subject for entry in item.conflicts], ["a", "z"])

    def test_auto_resolved_subjects_are_deduplicated_and_sorted(self) -> None:
        item = receipt(auto_resolved_subjects=("node:b", "node:a", "node:a"))
        self.assertEqual(item.auto_resolved_subjects, ("node:a", "node:b"))

    def test_digests_are_optional_until_filled(self) -> None:
        self.assertEqual(receipt().target_digest, "")
        self.assertEqual(receipt(target_digest=k.digest("x")).target_digest, k.digest("x"))
        with self.assertRaises(SchemaValidationError):
            receipt(source_digest="short")

    def test_a_result_may_not_be_named_while_a_blocking_confiction_is_open(self) -> None:
        with self.assertRaises(MergeBlockedError) as caught:
            receipt(result_snapshot_id=stable("snapshot.result"), conflicts=(conflict("render.logo"),))
        self.assertIn("names a result while 1 blocking conflict(s) remain unresolved", str(caught.exception))

    def test_a_deferred_disagreement_may_travel_with_a_result(self) -> None:
        item = receipt(
            result_snapshot_id=stable("snapshot.result"),
            conflicts=(
                conflict(
                    "edge:edge.render",
                    ConflictKind.TOPOLOGY_CONFLICT,
                    blocking=False,
                    resolution=ResolutionStrategy.DEFER,
                ),
            ),
        )
        self.assertFalse(item.is_cleared)
        self.assertEqual(item.unresolved_blocking, ())

    def test_a_resolved_blocking_conflict_leaves_the_receipt_cleared(self) -> None:
        item = receipt(
            result_snapshot_id=stable("snapshot.result"),
            conflicts=(conflict("render.logo", resolution=ResolutionStrategy.KEEP_TARGET),),
        )
        self.assertTrue(item.is_cleared)
        self.assertEqual(item.unresolved, ())

    def test_the_open_sets_are_reported_separately(self) -> None:
        item = receipt(
            conflicts=(
                conflict("variant:a", ConflictKind.VARIANT_SELECTION_CONFLICT),
                conflict("node:b"),
                conflict("node:c", resolution=ResolutionStrategy.KEEP_TARGET),
            )
        )
        self.assertEqual([entry.subject for entry in item.unresolved], ["node:b", "variant:a"])
        self.assertEqual([entry.subject for entry in item.unresolved_blocking], ["node:b"])
        self.assertFalse(item.is_clean)

    def test_the_families_present_are_reported_once_each(self) -> None:
        item = receipt(
            conflicts=(
                conflict("node:b"),
                conflict("edge:a", ConflictKind.TOPOLOGY_CONFLICT),
                conflict("node:c"),
            )
        )
        self.assertEqual(item.kinds, (ConflictKind.NODE_DEFINITION_CONFLICT, ConflictKind.TOPOLOGY_CONFLICT))

    def test_one_conflict_can_be_retrieved_by_family_and_subject(self) -> None:
        item = receipt(conflicts=(conflict("render.logo"),))
        self.assertIsNotNone(item.conflict(ConflictKind.NODE_DEFINITION_CONFLICT, "render.logo"))
        self.assertIsNone(item.conflict(ConflictKind.TOPOLOGY_CONFLICT, "render.logo"))
        self.assertIsNone(item.conflict(ConflictKind.NODE_DEFINITION_CONFLICT, "deliver.web"))

    def test_evidence_and_policy_references_are_deduplicated(self) -> None:
        one = k.ref(EntityKind.RECEIPT, "receipt.one")
        item = receipt(evidence_refs=(one, one), policy_refs=(one,))
        self.assertEqual(item.evidence_refs, (one,))
        self.assertEqual(item.policy_refs, (one,))

    def test_too_many_evidence_references_are_refused(self) -> None:
        with self.assertRaises(Exception):
            receipt(evidence_refs=tuple(
                k.ref(EntityKind.RECEIPT, f"receipt.{index}") for index in range(MAX_CLOSURE_REFS + 1)
            ))

    def test_affected_nodes_must_be_identifiers(self) -> None:
        self.assertEqual(receipt(affected_node_ids=("render.logo",)).affected_node_ids, ("render.logo",))
        with self.assertRaises(SchemaValidationError):
            receipt(affected_node_ids=("not an id",))

    def test_the_recorder_is_a_component_and_the_time_is_millis(self) -> None:
        self.assertEqual(receipt(actor=ACTOR).actor, ACTOR)
        self.assertEqual(receipt(recorded_at_ms=NOW).recorded_at_ms, NOW)
        with self.assertRaises(Exception):
            receipt(recorded_at_ms=-1)

    def test_the_conflict_bound_is_enforced(self) -> None:
        too_many = tuple(conflict(f"node.{index}") for index in range(MAX_CONFLICTS + 1))
        with self.assertRaises(Exception):
            receipt(conflicts=too_many)

    def test_a_foreign_contract_version_is_refused(self) -> None:
        with self.assertRaises(UnsupportedVersionError):
            receipt(contract_version="m02-contract-v9.9")

    def test_a_receipt_round_trips_through_its_payload(self) -> None:
        item = receipt(
            conflicts=(conflict("render.logo", node_ids=("render.logo",)),),
            evidence_refs=(k.ref(EntityKind.RECEIPT, "receipt.one"),),
            target_digest=k.digest("target"),
            actor=ACTOR,
            recorded_at_ms=NOW,
        )
        self.assertEqual(MergeReceipt.from_payload(item.to_payload()), item)


class MergeAdmissionTests(unittest.TestCase):
    def test_two_heads_that_never_diverged_merge_without_a_conflict(self) -> None:
        snapshot, merged = ThreeHeads().settled()
        self.assertTrue(merged.is_clean)
        self.assertEqual(merged.auto_resolved_subjects, ())

    def test_the_result_is_committed_into_the_same_store(self) -> None:
        heads = ThreeHeads()
        before = len(heads.store)
        snapshot, _ = heads.settled()
        self.assertEqual(len(heads.store), before + 1)
        self.assertIs(heads.store.get(snapshot.snapshot_id), snapshot)

    def test_the_result_names_both_heads_as_its_parents(self) -> None:
        heads = ThreeHeads()
        snapshot, _ = heads.settled()
        self.assertEqual(
            snapshot.closure.parent_snapshot_ids, tuple(sorted([heads.ids["target"], heads.ids["source"]]))
        )

    def test_the_result_ancestry_holds_the_lineage_it_came_from(self) -> None:
        heads = ThreeHeads({"ancestry": (stable("snapshot.ancient"),)})
        snapshot, _ = heads.settled()
        self.assertEqual(
            snapshot.closure.ancestry,
            tuple(sorted({stable("snapshot.ancient"), heads.ids["target"], heads.ids["source"]})),
        )

    def test_the_result_says_why_it_exists(self) -> None:
        snapshot, _ = ThreeHeads().settled()
        self.assertIs(snapshot.derivation, SnapshotDerivation.MERGED)
        self.assertIs(snapshot.snapshot_class, SnapshotClass.LOGICAL_SNAPSHOT)

    def test_the_merged_definition_moves_to_the_next_version(self) -> None:
        snapshot, _ = ThreeHeads().settled()
        self.assertEqual(snapshot.closure.revision.definition.version, 2)

    def test_one_graph_family_merges_against_itself(self) -> None:
        snapshot, _ = ThreeHeads().settled()
        self.assertEqual(snapshot.closure.graph_id, "graph.test")

    def test_the_receipt_binds_both_head_digests(self) -> None:
        heads = ThreeHeads()
        _, merged = heads.merge()
        self.assertEqual(merged.target_digest, heads.closures["target"].digest)
        self.assertEqual(merged.source_digest, heads.closures["source"].digest)

    def test_a_review_screen_can_ask_the_same_question_without_moving_history(self) -> None:
        heads = ThreeHeads(target={"rights_refs": (rights("rights.a"),)})
        before = len(heads.store)
        snapshot, merged = heads.merge(commit=False)
        self.assertIsNone(snapshot)
        self.assertEqual(len(heads.store), before)
        self.assertEqual(merged.auto_resolved_subjects, ("rights:rights.a", "rights:rights.base"))

    def test_merging_never_edits_a_head_it_was_given(self) -> None:
        heads = ThreeHeads(target={"rights_refs": (rights("rights.a"),)})
        heads.settled()
        self.assertEqual(heads.store.get(heads.ids["target"]).closure, heads.closures["target"])

    def test_a_head_that_was_never_committed_cannot_be_merged(self) -> None:
        heads = ThreeHeads()
        with self.assertRaises(SnapshotClosureError):
            three_way_merge(
                heads.store,
                base_snapshot_id=heads.ids["base"],
                target_snapshot_id=new_id(),
                source_snapshot_id=heads.ids["source"],
            )


class MergeSafeAutoMergeTests(unittest.TestCase):
    def test_a_record_only_one_line_added_is_carried(self) -> None:
        for role in ("target", "source"):
            with self.subTest(role=role):
                heads = ThreeHeads(**{role: {"rights_refs": (rights("rights.base"), rights("rights.new"))}})
                snapshot, merged = heads.settled()
                self.assertTrue(merged.is_clean)
                self.assertIn(rights("rights.new"), snapshot.closure.rights_refs)

    def test_both_lines_adding_the_same_record_keep_it_once(self) -> None:
        added = (rights("rights.base"), rights("rights.new"))
        snapshot, merged = ThreeHeads(target={"rights_refs": added}, source={"rights_refs": added}).settled()
        self.assertEqual(snapshot.closure.rights_refs, added)
        self.assertEqual(merged.auto_resolved_subjects, ("rights:rights.new",))

    def test_two_unrelated_records_in_one_group_never_collide(self) -> None:
        snapshot, merged = ThreeHeads(
            target={"rights_refs": (rights("rights.base"), rights("rights.music"))},
            source={"rights_refs": (rights("rights.base"), rights("rights.font"))},
        ).settled()
        self.assertTrue(merged.is_clean)
        self.assertEqual(len(snapshot.closure.rights_refs), 3)

    def test_two_lines_renegotiating_the_same_binding_disagree(self) -> None:
        _, merged = ThreeHeads(
            target={"rights_refs": (rights("rights.base", version="2"),)},
            source={"rights_refs": (rights("rights.base", version="3"),)},
        ).merge()
        item = merged.conflict(ConflictKind.RIGHTS_PROVENANCE_CONFLICT, "rights:rights.base")
        self.assertIsNotNone(item)
        sides = (item.base_side, item.target_side, item.source_side)
        for side in sides:
            self.assertTrue(side.startswith("digest:"))
        self.assertEqual(len(set(sides)), 3)
        self.assertTrue(item.blocking)

    def test_the_same_renegotiation_on_both_lines_is_taken_once(self) -> None:
        renegotiated = (rights("rights.base", version="2"),)
        snapshot, merged = ThreeHeads(
            target={"rights_refs": renegotiated}, source={"rights_refs": renegotiated}
        ).settled()
        self.assertEqual(snapshot.closure.rights_refs, renegotiated)
        self.assertEqual(merged.auto_resolved_subjects, ("rights:rights.base",))

    def test_a_record_only_one_line_dropped_stays_dropped(self) -> None:
        snapshot, merged = ThreeHeads(target={"rights_refs": ()}).settled()
        self.assertEqual(snapshot.closure.rights_refs, ())
        self.assertEqual(merged.auto_resolved_subjects, ("rights:rights.base",))

    def test_a_drop_the_other_line_renegotiated_is_a_conflict(self) -> None:
        _, merged = ThreeHeads(
            target={"rights_refs": ()}, source={"rights_refs": (rights("rights.base", version="2"),)}
        ).merge()
        item = merged.conflict(ConflictKind.RIGHTS_PROVENANCE_CONFLICT, "rights:rights.base")
        self.assertEqual(item.explanation, "the target deleted what the source changed")

    def test_a_definition_only_one_line_changed_is_carried(self) -> None:
        moved = relabel(DEFINITION, "render.logo", "Render v2")
        snapshot, merged = ThreeHeads(target={"graph": graph_over(moved)}).settled()
        self.assertTrue(merged.is_clean)
        self.assertEqual(merged.auto_resolved_subjects, ("node:render.logo",))
        node = snapshot.closure.revision.definition.node_index["render.logo"]
        self.assertEqual(node.display_name, "Render v2")

    def test_a_definition_both_lines_changed_apart_is_a_node_conflict(self) -> None:
        _, merged = ThreeHeads(
            target={"graph": graph_over(relabel(DEFINITION, "render.logo", "Render A"))},
            source={"graph": graph_over(relabel(DEFINITION, "render.logo", "Render B"))},
        ).merge()
        item = merged.conflict(ConflictKind.NODE_DEFINITION_CONFLICT, "node:render.logo")
        self.assertEqual(item.node_ids, ("render.logo",))
        self.assertIn("needs an explicit settlement", item.explanation)

    def test_a_facet_only_one_line_declared_is_carried(self) -> None:
        moved = refacet(DEFINITION, "edge.render", DependencyFacet.CONTENT, DependencyFacet.QUALITY)
        snapshot, merged = ThreeHeads(target={"graph": graph_over(moved)}).settled()
        self.assertTrue(merged.is_clean)
        self.assertEqual(merged.auto_resolved_subjects, ("edge:edge.render",))

    def test_a_re_render_that_reproduced_the_bytes_is_not_a_disagreement(self) -> None:
        rerendered = tuple(
            record(node_id, attempt=stable(f"other.{node_id}"), produced_at_ms=NOW + 99)
            for node_id in sorted(NODES)
        )
        snapshot, merged = ThreeHeads(
            target={"graph": chain(records=rerendered)}, source={"graph": chain(records=rerendered)}
        ).settled()
        self.assertTrue(merged.is_clean)
        self.assertEqual(snapshot.closure.graph.materializations, rerendered)

    def test_a_re_render_only_one_line_ran_is_carried(self) -> None:
        rerendered = tuple(record(node_id, seed=f"only-target.{node_id}") for node_id in sorted(NODES))
        snapshot, merged = ThreeHeads(target={"graph": chain(records=rerendered)}).settled()
        self.assertTrue(merged.is_clean)
        self.assertEqual(snapshot.closure.graph.materializations, rerendered)

    def test_two_lines_rendering_different_bytes_are_an_asset_conflict(self) -> None:
        _, merged = ThreeHeads(
            target={"graph": chain(records=tuple(record(node_id, seed=f"a.{node_id}") for node_id in NODES))},
            source={"graph": chain(records=tuple(record(node_id, seed=f"b.{node_id}") for node_id in NODES))},
        ).merge()
        item = merged.conflict(ConflictKind.ARTIFACT_REVISION_CONFLICT, "revision:render.logo.out")
        self.assertEqual(item.node_ids, ("render.logo",))
        self.assertTrue(item.base_side.startswith("digest:"))
        self.assertFalse(merged.is_cleared)

    def test_a_brief_only_one_line_restated_is_carried(self) -> None:
        snapshot, merged = ThreeHeads(target={"intent_ref": k.ref(EntityKind.INTENT, "intent.summer")}).settled()
        self.assertEqual(snapshot.closure.intent_ref, k.ref(EntityKind.INTENT, "intent.summer"))
        self.assertEqual(merged.auto_resolved_subjects, ("intent",))

    def test_a_brief_both_lines_restated_is_a_quality_policy_conflict(self) -> None:
        _, merged = ThreeHeads(
            target={"intent_ref": k.ref(EntityKind.INTENT, "intent.summer")},
            source={"intent_ref": k.ref(EntityKind.INTENT, "intent.winter")},
        ).merge()
        item = merged.conflict(ConflictKind.QUALITY_POLICY_CONFLICT, "intent")
        self.assertEqual(item.explanation, "both lines restated it differently")

    def test_a_fingerprint_disagreement_is_a_release_family(self) -> None:
        _, merged = ThreeHeads(
            target={"environment_fingerprint": k.digest("linux")},
            source={"environment_fingerprint": k.digest("windows")},
        ).merge()
        self.assertEqual(
            merged.conflict(ConflictKind.DELIVERY_RELEASE_CONFLICT, "environment").kind,
            ConflictKind.DELIVERY_RELEASE_CONFLICT,
        )

    def test_the_affected_nodes_are_the_ones_a_conflict_touched(self) -> None:
        _, merged = ThreeHeads(
            target={"graph": graph_over(relabel(DEFINITION, "render.logo", "A"))},
            source={"graph": graph_over(relabel(DEFINITION, "render.logo", "B"))},
        ).merge()
        self.assertEqual(merged.affected_node_ids, ("render.logo",))


class MergeSubjectSpaceTests(unittest.TestCase):
    def test_an_admission_renegotiated_by_both_lines_is_a_topology_conflict(self) -> None:
        admitted = tuple(k.ref(EntityKind.ARTIFACT, "asset.logo", version=value) for value in (None, "2", "3"))
        _, merged = ThreeHeads(
            {"external_admissions": admitted[:1]},
            {"external_admissions": admitted[1:2]},
            {"external_admissions": admitted[2:3]},
        ).merge()
        item = merged.conflict(ConflictKind.TOPOLOGY_CONFLICT, "artifact:asset.logo")
        self.assertIsNotNone(item)

    def test_a_boundary_both_lines_defined_differently_is_a_topology_conflict(self) -> None:
        _, merged = ThreeHeads(
            {"graph": graph_over(subgraph_definition("1.0.0"))},
            target={"graph": graph_over(subgraph_definition("1.0.1"))},
            source={"graph": graph_over(subgraph_definition("1.0.2"))},
        ).merge()
        item = merged.conflict(ConflictKind.TOPOLOGY_CONFLICT, "interface:sub.kit")
        self.assertEqual(item.node_ids, ("sub.kit",))

    def test_a_dependency_one_line_deleted_while_its_consumer_survives_is_refiled(self) -> None:
        _, merged = one_line_drops("edge.render").merge()
        item = merged.conflict(ConflictKind.TOPOLOGY_CONFLICT, "edge:edge.render")
        self.assertEqual(item.node_ids, ("render.logo", "source.logo"))
        self.assertIn("cannot survive its own producer", item.explanation)
        self.assertNotIn("edge:edge.render", merged.auto_resolved_subjects)

    def test_a_settlement_that_restores_the_dependency_lets_the_graph_bind(self) -> None:
        snapshot, merged = one_line_drops("edge.render").settled(
            resolutions=[resolution("edge.render", ResolutionStrategy.TAKE_SOURCE, resolved_by=ACTOR)]
        )
        self.assertEqual(merged.conflicts[0].resolution, ResolutionStrategy.TAKE_SOURCE)
        self.assertIn("edge.render", {item.edge_id for item in snapshot.closure.revision.definition.edges})

    def test_keeping_the_deletion_also_clears_the_merge(self) -> None:
        snapshot, merged = one_line_drops("edge.render").settled(resolutions=[resolution("edge.render")])
        self.assertNotIn(
            "edge.render", {item.edge_id for item in snapshot.closure.revision.definition.edges}
        )
        self.assertTrue(merged.is_cleared)

    def test_a_merged_graph_that_cannot_be_bound_comes_back_as_a_conflict(self) -> None:
        heads = graph_conflict_heads()
        snapshot, merged = heads.merge()
        self.assertIsNone(snapshot)
        item = merged.conflict(ConflictKind.TOPOLOGY_CONFLICT, "graph:merged")
        self.assertIn("edge.validate", item.explanation)
        self.assertIn("deliver.web", item.explanation)

    def test_a_settlement_for_the_unbindable_merge_can_clear_it(self) -> None:
        heads = graph_conflict_heads()
        snapshot, merged = heads.merge(resolutions=[resolution("graph:merged")])
        self.assertIsNone(snapshot)
        self.assertTrue(merged.is_cleared)
        self.assertEqual(merged.conflicts[0].resolution, ResolutionStrategy.KEEP_TARGET)


class MergeGuardTests(unittest.TestCase):
    """The refusals that happen before any subject is compared."""

    def test_a_head_belonging_to_another_production_is_refused(self) -> None:
        with self.assertRaises(SnapshotClosureError) as caught:
            ThreeHeads(source={"production_id": "prod.other"}).merge()
        self.assertIn("merging across productions is a different operation", str(caught.exception))

    def test_a_head_belonging_to_another_project_is_refused(self) -> None:
        with self.assertRaises(SnapshotClosureError) as caught:
            ThreeHeads(target={"project_id": "other-project"}).merge()
        self.assertIn("belongs to production", str(caught.exception))

    def test_one_graph_family_never_merges_against_another(self) -> None:
        moved = graph_over(k.chain_definition(graph_id="graph.other"))
        with self.assertRaises(SnapshotClosureError) as caught:
            ThreeHeads(source={"graph": moved}).merge()
        self.assertIn("never across graphs", str(caught.exception))

    def test_the_refusal_names_which_head_broke_the_guard(self) -> None:
        with self.assertRaises(SnapshotClosureError) as caught:
            ThreeHeads(target={"production_id": "prod.other"}).merge()
        self.assertIn("the target snapshot", str(caught.exception))


class MergeResolutionTests(unittest.TestCase):
    """A settlement is addressed by subject, and only by a subject that exists."""

    def test_a_settlement_may_be_addressed_by_the_bare_subject(self) -> None:
        _, merged = ThreeHeads(
            target={"graph": graph_over(relabel(DEFINITION, "render.logo", "A"))},
            source={"graph": graph_over(relabel(DEFINITION, "render.logo", "B"))},
        ).merge(resolutions=[resolution("render.logo", ResolutionStrategy.TAKE_SOURCE, resolved_by=ACTOR)])
        item = merged.conflict(ConflictKind.NODE_DEFINITION_CONFLICT, "node:render.logo")
        self.assertEqual(item.resolution, ResolutionStrategy.TAKE_SOURCE)
        self.assertTrue(item.is_resolved)

    def test_an_offered_settlement_that_matches_nothing_is_a_misunderstanding(self) -> None:
        heads = ThreeHeads(target={"graph": graph_over(relabel(DEFINITION, "render.logo", "A"))})
        with self.assertRaises(MergeBlockedError) as caught:
            heads.merge(resolutions=[resolution("node:nothing.here")])
        self.assertIn("no disagreement in this merge matched the settlement offered for", str(caught.exception))

    def test_the_same_subject_cannot_be_settled_twice(self) -> None:
        heads = ThreeHeads(
            target={"graph": graph_over(relabel(DEFINITION, "render.logo", "A"))},
            source={"graph": graph_over(relabel(DEFINITION, "render.logo", "B"))},
        )
        with self.assertRaises(GraphValidationError) as caught:
            heads.merge(resolutions=[resolution("node:render.logo"), resolution("node:render.logo")])
        self.assertIn("is resolved twice", str(caught.exception))

    def test_take_source_moves_the_source_side_into_the_result(self) -> None:
        snapshot, _ = ThreeHeads(
            target={"graph": graph_over(relabel(DEFINITION, "render.logo", "A"))},
            source={"graph": graph_over(relabel(DEFINITION, "render.logo", "B"))},
        ).settled(resolutions=[resolution("node:render.logo", ResolutionStrategy.TAKE_SOURCE, resolved_by=ACTOR)])
        self.assertEqual(snapshot.closure.revision.definition.node_index["render.logo"].display_name, "B")

    def test_keeping_the_target_is_a_settlement_that_needs_no_actor(self) -> None:
        snapshot, merged = ThreeHeads(
            target={"graph": graph_over(relabel(DEFINITION, "render.logo", "A"))},
            source={"graph": graph_over(relabel(DEFINITION, "render.logo", "B"))},
        ).settled(resolutions=[resolution("node:render.logo")])
        self.assertTrue(merged.is_cleared)
        self.assertEqual(snapshot.closure.revision.definition.node_index["render.logo"].display_name, "A")

    def test_the_receipt_collects_every_evidence_reference_the_merge_cited(self) -> None:
        first = k.ref(EntityKind.RECEIPT, "receipt.one")
        second = k.ref(EntityKind.RECEIPT, "receipt.two")
        _, merged = ThreeHeads(
            target={"graph": graph_over(relabel(DEFINITION, "render.logo", "A"))},
            source={"graph": graph_over(relabel(DEFINITION, "render.logo", "B"))},
        ).merge(
            resolutions=[
                resolution("node:render.logo", ResolutionStrategy.EXPLICIT_CHOICE, evidence_ref=second, resolved_by=ACTOR)
            ]
        )
        self.assertEqual(merged.evidence_refs, (first, second)[1:], "only the cited receipt travels")
        self.assertEqual(merged.evidence_refs[0].text, second.text)

    def test_a_settled_disagreement_is_reported_as_resolved_not_dropped(self) -> None:
        _, merged = ThreeHeads(
            target={"graph": graph_over(relabel(DEFINITION, "render.logo", "A"))},
            source={"graph": graph_over(relabel(DEFINITION, "render.logo", "B"))},
        ).merge(resolutions=[resolution("node:render.logo")])
        self.assertEqual(len(merged.conflicts), 1)
        self.assertEqual(merged.unresolved_blocking, ())

    def test_a_blocking_topology_disagreement_cannot_be_deferred_away(self) -> None:
        with self.assertRaises(MergeBlockedError) as caught:
            one_line_drops("edge.render").merge(
                resolutions=[resolution("edge:edge.render", ResolutionStrategy.DEFER)]
            )
        self.assertIn("cannot be deferred", str(caught.exception))

    def test_an_unmatched_settlement_is_refused_before_a_result_is_committed(self) -> None:
        heads = ThreeHeads(target={"intent_ref": k.ref(EntityKind.INTENT, "intent.summer")})
        with self.assertRaises(MergeBlockedError):
            heads.merge(resolutions=[resolution("closure:LOGICAL_SNAPSHOT")])
        self.assertEqual(len(heads.store), 3)


class MergeClassInheritanceTests(unittest.TestCase):
    """A merge may only claim the completeness all three heads already earned."""

    def test_a_merge_inherits_the_weakest_claim_of_its_inputs(self) -> None:
        heads = ThreeHeads(
            classes=(SnapshotClass.VALIDATED_SNAPSHOT, SnapshotClass.MATERIALIZED_SNAPSHOT, SnapshotClass.VALIDATED_SNAPSHOT)
        )
        snapshot, _ = heads.settled()
        self.assertEqual(snapshot.snapshot_class, SnapshotClass.MATERIALIZED_SNAPSHOT)

    def test_three_validated_heads_yield_a_validated_merge(self) -> None:
        heads = ThreeHeads(classes=(SnapshotClass.VALIDATED_SNAPSHOT,) * 3)
        snapshot, _ = heads.settled()
        self.assertEqual(snapshot.snapshot_class, SnapshotClass.VALIDATED_SNAPSHOT)

    def test_a_class_the_closure_cannot_support_comes_back_as_a_conflict(self) -> None:
        thin = chain(records=tuple(record(node_id) for node_id in NODES[:-1]))
        snapshot, merged = ThreeHeads(target={"graph": thin}).merge(snapshot_class="VALIDATED_SNAPSHOT")
        self.assertIsNone(snapshot)
        item = merged.conflict(ConflictKind.QUALITY_POLICY_CONFLICT, "closure:VALIDATED_SNAPSHOT")
        self.assertIn("deliver.web", item.explanation)

    def test_a_merge_can_still_claim_the_class_its_closure_supports(self) -> None:
        thin = chain(records=tuple(record(node_id) for node_id in NODES[:-1]))
        snapshot, merged = ThreeHeads(target={"graph": thin}).settled(snapshot_class="LOGICAL_SNAPSHOT")
        self.assertTrue(merged.is_clean)
        self.assertEqual(snapshot.snapshot_class, SnapshotClass.LOGICAL_SNAPSHOT)

    def test_a_revalidation_settlement_clears_the_receipt_but_not_the_claim(self) -> None:
        thin = chain(records=tuple(record(node_id) for node_id in NODES[:-1]))
        evidence = k.ref(EntityKind.RECEIPT, "receipt.revalidated")
        resolutions = [
            resolution(
                "closure:VALIDATED_SNAPSHOT",
                ResolutionStrategy.REVALIDATE,
                evidence_ref=evidence,
                resolved_by=ACTOR,
            )
        ]
        heads = ThreeHeads(target={"graph": thin})
        nothing, merged = heads.merge(snapshot_class="VALIDATED_SNAPSHOT", resolutions=resolutions, commit=False)
        self.assertIsNone(nothing)
        self.assertTrue(merged.is_cleared)
        self.assertEqual(merged.conflicts[0].resolution, ResolutionStrategy.REVALIDATE)
        with self.assertRaises(SnapshotClosureError) as caught:
            heads.merge(snapshot_class="VALIDATED_SNAPSHOT", resolutions=resolutions)
        self.assertIn("claims VALIDATED while nodes deliver.web emitted nothing", str(caught.exception))

    def test_an_obligation_cannot_be_deferred_into_a_result(self) -> None:
        thin = chain(records=tuple(record(node_id) for node_id in NODES[:-1]))
        with self.assertRaises(MergeBlockedError):
            ThreeHeads(target={"graph": thin}).merge(
                snapshot_class="VALIDATED_SNAPSHOT",
                resolutions=[resolution("closure:VALIDATED_SNAPSHOT", ResolutionStrategy.DEFER)],
            )

    def test_a_dropped_declaration_takes_its_admission_along(self) -> None:
        moved = k.definition(*DEFINITION.nodes, edges=DEFINITION.edges, declared=())
        snapshot, merged = ThreeHeads(target={"graph": graph_over(moved)}).settled()
        self.assertEqual(snapshot.closure.revision.definition.declared_external_inputs, ())
        self.assertEqual(snapshot.closure.external_admissions, ())
        self.assertEqual(merged.auto_resolved_subjects, ("artifact:asset.logo", "declared:artifact:asset.logo"))


class MergeSideEffectTests(unittest.TestCase):
    """What the outside world already saw is a conflict no side may simply win."""

    def effect(self, node_id: str = "deliver.web", destination: str = "dest.live", **over: Any):
        payload: dict[str, Any] = dict(
            side_effect_id=stable(f"effect.{node_id}.{destination}"),
            node_id=node_id,
            observed_after_snapshot_id=stable("snapshot.target"),
            destination=k.ref(EntityKind.DESTINATION, destination),
        )
        payload.update(over)
        return ExternalSideEffect(**payload)

    def test_a_shared_mutation_is_a_blocking_conflict(self) -> None:
        _, merged = ThreeHeads().merge(side_effect_conflicts=[self.effect()])
        item = merged.conflicts[0]
        self.assertEqual(item.kind, ConflictKind.SIDE_EFFECT_CONFLICT)
        self.assertEqual(item.subject, f"side-effect:deliver.web:{self.effect().destination.text}")
        self.assertTrue(item.blocking)
        self.assertIsNone(merged.result_snapshot_id)

    def test_picking_a_side_is_not_an_option_for_a_mutation(self) -> None:
        subject = f"side-effect:deliver.web:{self.effect().destination.text}"
        with self.assertRaises(MergeBlockedError) as caught:
            ThreeHeads().merge(
                side_effect_conflicts=[self.effect()],
                resolutions=[resolution(subject, ResolutionStrategy.TAKE_SOURCE, resolved_by=ACTOR)],
            )
        self.assertIn("may only be settled by", str(caught.exception))

    def test_a_named_compensation_closes_the_disagreement(self) -> None:
        subject = f"side-effect:deliver.web:{self.effect().destination.text}"
        evidence = k.ref(EntityKind.RECEIPT, "receipt.compensated")
        snapshot, merged = ThreeHeads().settled(
            side_effect_conflicts=[self.effect()],
            resolutions=[
                resolution(subject, ResolutionStrategy.COMPENSATE, evidence_ref=evidence, resolved_by=ACTOR)
            ],
        )
        self.assertEqual(merged.conflicts[0].resolution, ResolutionStrategy.COMPENSATE)
        self.assertEqual(merged.evidence_refs, (evidence,))
        self.assertIsNotNone(snapshot)

    def test_a_compensation_that_asserts_work_without_a_receipt_is_refused(self) -> None:
        subject = f"side-effect:deliver.web:{self.effect().destination.text}"
        with self.assertRaises(MergeBlockedError) as caught:
            ThreeHeads().merge(
                side_effect_conflicts=[self.effect()],
                resolutions=[resolution(subject, ResolutionStrategy.RECONCILE, resolved_by=ACTOR)],
            )
        self.assertIn("evidenced by a receipt", str(caught.exception))

    def test_two_destinations_are_two_disagreements(self) -> None:
        _, merged = ThreeHeads().merge(
            side_effect_conflicts=[self.effect(destination="dest.live"), self.effect(destination="dest.tv")]
        )
        self.assertEqual(len(merged.conflicts), 2)

    def test_the_same_mutation_is_never_reported_twice(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            ThreeHeads().merge(
                side_effect_conflicts=[
                    self.effect(side_effect_id=stable("effect.one")),
                    self.effect(side_effect_id=stable("effect.two")),
                ]
            )
        self.assertIn("a merge reports the same conflict twice", str(caught.exception))

    def test_a_mutation_conflict_names_the_node_it_touched(self) -> None:
        _, merged = ThreeHeads().merge(side_effect_conflicts=[self.effect()])
        self.assertEqual(merged.conflicts[0].node_ids, ("deliver.web",))
        self.assertEqual(merged.affected_node_ids, ("deliver.web",))


class MergeVariantTests(unittest.TestCase):
    """Axes, constraints and protected identities merge under different rules."""

    def variant_heads(self, target_sets: Any, source_sets: Any = None) -> ThreeHeads:
        return ThreeHeads(
            {"variant_sets": (axis(),)},
            target={"variant_sets": target_sets},
            source={"variant_sets": (axis(),) if source_sets is None else source_sets},
        )

    def test_an_axis_both_lines_redrew_is_a_topology_conflict(self) -> None:
        _, merged = self.variant_heads(
            (axis(purpose="retuned for delivery"),), (axis(purpose="retuned for review"),)
        ).merge()
        item = merged.conflict(ConflictKind.TOPOLOGY_CONFLICT, "variant-set:axis.quality")
        self.assertEqual(item.node_ids, ("axis.quality",))

    def test_an_axis_only_one_line_redrew_is_carried(self) -> None:
        snapshot, merged = self.variant_heads((axis(purpose="retuned"),)).settled()
        self.assertEqual(merged.auto_resolved_subjects, ("variant-set:axis.quality",))
        self.assertEqual(snapshot.closure.variant_sets[0].purpose, "retuned")

    def test_a_constraint_both_lines_tightened_apart_is_a_constraint_conflict(self) -> None:
        _, merged = ThreeHeads(
            {"variant_constraints": (ratio_constraint(),)},
            target={"variant_constraints": (ratio_constraint(target_options=("wide", "tall")),)},
            source={"variant_constraints": (ratio_constraint(kind=ConstraintKind.PROHIBITS),)},
        ).merge()
        item = merged.conflict(ConflictKind.VARIANT_CONSTRAINT_CONFLICT, "variant-constraint:constraint.premium-wide")
        self.assertIsNotNone(item)

    def test_a_constraint_conflict_is_not_a_place_to_recompose(self) -> None:
        with self.assertRaises(MergeBlockedError):
            ThreeHeads(
                {"variant_constraints": (ratio_constraint(),)},
                target={"variant_constraints": (ratio_constraint(target_options=("wide", "tall")),)},
                source={"variant_constraints": (ratio_constraint(target_options=("square",)),)},
            ).merge(
                resolutions=[
                    resolution(
                        "variant-constraint:constraint.premium-wide",
                        ResolutionStrategy.RECOMPOSE,
                        evidence_ref=k.ref(EntityKind.RECEIPT, "receipt.rig"),
                        resolved_by=ACTOR,
                    )
                ]
            )

    def test_a_choice_both_lines_made_apart_travels_with_the_result(self) -> None:
        snapshot, merged = ThreeHeads(
            {"variant_sets": (axis(),)},
            target={"variant_sets": (axis(),), "variant_selection": picked(quality="premium")},
            source={"variant_sets": (axis(),), "variant_selection": picked(quality="preview")},
        ).settled()
        item = merged.conflict(ConflictKind.VARIANT_SELECTION_CONFLICT, "variant:axis.quality")
        self.assertFalse(item.blocking)
        self.assertEqual(item.target_side, "premium")
        self.assertEqual(item.source_side, "preview")
        self.assertEqual(dict(snapshot.closure.effective_selection)["axis.quality"], "premium")

    def test_a_choice_only_one_line_made_is_taken_without_a_conflict(self) -> None:
        snapshot, merged = ThreeHeads(
            {"variant_sets": (axis(),)},
            target={"variant_sets": (axis(),), "variant_selection": picked(quality="premium")},
            source={"variant_sets": (axis(),)},
        ).settled()
        self.assertEqual(merged.auto_resolved_subjects, ("variant:axis.quality",))
        self.assertEqual(dict(snapshot.closure.effective_selection)["axis.quality"], "premium")

    def test_a_settlement_into_a_combination_neither_line_held_is_refused(self) -> None:
        sets = (axis(), axis("axis.ratio", options=(option("wide"), option("square")), default_option_id="square"))
        rule = ratio_constraint()
        heads = ThreeHeads(
            {"variant_sets": sets},
            target={
                "variant_sets": sets,
                "variant_constraints": (rule,),
                "variant_selection": picked(quality="premium", ratio="wide"),
            },
            source={"variant_sets": sets, "variant_selection": picked(quality="premium", ratio="square")},
        )
        snapshot, merged = heads.merge(
            resolutions=[resolution("variant:axis.ratio", ResolutionStrategy.TAKE_SOURCE, resolved_by=ACTOR)]
        )
        self.assertIsNone(snapshot)
        item = merged.conflict(ConflictKind.VARIANT_CONSTRAINT_CONFLICT, "variant-constraint:constraint.premium-wide")
        self.assertIn("constraint.premium-wide", item.explanation)

    def test_a_persona_guard_dropped_by_one_line_is_a_conflict(self) -> None:
        _, merged = ThreeHeads(
            {"variant_sets": (persona_axis(),)},
            target={"variant_sets": (persona_axis(identity_anchor=None),)},
            source={"variant_sets": (persona_axis(),)},
        ).merge()
        item = merged.conflict(ConflictKind.IDENTITY_ANCHOR_CONFLICT, "anchor-policy:anchor.persona.face")
        self.assertIn("no longer carries the protected identity anchor", item.explanation)
        self.assertEqual(item.node_ids, ("axis.persona",))

    def test_keeping_the_target_restores_the_persona_guard(self) -> None:
        snapshot, _ = ThreeHeads(
            {"variant_sets": (persona_axis(),)},
            target={"variant_sets": (persona_axis(identity_anchor=None),)},
            source={"variant_sets": (persona_axis(),)},
        ).settled(resolutions=[resolution("anchor-policy:anchor.persona.face")])
        self.assertIsNotNone(snapshot.closure.variant_sets[0].identity_anchor)

    def test_a_migration_lets_the_dropped_guard_merge_without_restoring_it(self) -> None:
        evidence = k.ref(EntityKind.RECEIPT, MIGRATION)
        snapshot, merged = ThreeHeads(
            {"variant_sets": (persona_axis(),)},
            target={"variant_sets": (persona_axis(identity_anchor=None),)},
            source={"variant_sets": (persona_axis(),)},
        ).settled(
            resolutions=[
                resolution(
                    "anchor-policy:anchor.persona.face",
                    ResolutionStrategy.MIGRATE_IDENTITY,
                    evidence_ref=evidence,
                    resolved_by=ACTOR,
                )
            ]
        )
        self.assertTrue(merged.is_cleared)
        self.assertIsNone(snapshot.closure.variant_sets[0].identity_anchor)

    def test_two_lines_driving_the_same_persona_apart_need_a_migration(self) -> None:
        alt_two = stable("migration.alt2")
        drifting = persona_axis(
            options=(
                option("keynote", anchor_digest=FACE),
                option("alt", anchor_digest=OTHER_FACE, migration_receipt_id=MIGRATION),
                option("alt2", anchor_digest=k.digest("a third face"), migration_receipt_id=alt_two),
            )
        )
        heads = ThreeHeads(
            {"variant_sets": (drifting,), "variant_selection": picked(persona="keynote")},
            target={
                "variant_sets": (drifting,),
                "variant_selection": picked(persona="alt", receipts=[MIGRATION]),
            },
            source={
                "variant_sets": (drifting,),
                "variant_selection": picked(persona="alt2", receipts=[alt_two]),
            },
        )
        snapshot, merged = heads.merge()
        self.assertIsNone(snapshot)
        item = merged.conflict(ConflictKind.IDENTITY_ANCHOR_CONFLICT, "anchor-drift:anchor.persona.face")
        self.assertEqual((item.base_side, item.target_side, item.source_side), ("keynote", "alt", "alt2"))
        self.assertEqual(merged.kinds, (ConflictKind.IDENTITY_ANCHOR_CONFLICT, ConflictKind.VARIANT_SELECTION_CONFLICT))

    def test_a_migration_authorises_both_sides_of_the_drift(self) -> None:
        alt_two = stable("migration.alt2")
        drifting = persona_axis(
            options=(
                option("keynote", anchor_digest=FACE),
                option("alt", anchor_digest=OTHER_FACE, migration_receipt_id=MIGRATION),
                option("alt2", anchor_digest=k.digest("a third face"), migration_receipt_id=alt_two),
            )
        )
        heads = ThreeHeads(
            {"variant_sets": (drifting,), "variant_selection": picked(persona="keynote")},
            target={"variant_sets": (drifting,), "variant_selection": picked(persona="alt", receipts=[MIGRATION])},
            source={"variant_sets": (drifting,), "variant_selection": picked(persona="alt2", receipts=[alt_two])},
        )
        snapshot, merged = heads.settled(
            resolutions=[
                resolution(
                    "anchor-drift:anchor.persona.face",
                    ResolutionStrategy.MIGRATE_IDENTITY,
                    evidence_ref=k.ref(EntityKind.RECEIPT, MIGRATION),
                    resolved_by=ACTOR,
                )
            ]
        )
        self.assertEqual(
            sorted(snapshot.closure.variant_selection.migration_receipt_ids), sorted({MIGRATION, alt_two})
        )

    def test_a_migration_settlement_must_cite_a_receipt_id(self) -> None:
        drifting = persona_axis()
        heads = ThreeHeads(
            {"variant_sets": (drifting,), "variant_selection": picked(persona="keynote")},
            target={"variant_sets": (drifting,), "variant_selection": picked(persona="alt", receipts=[MIGRATION])},
            source={"variant_sets": (drifting,), "variant_selection": picked(persona="alt", receipts=[MIGRATION])},
        )
        with self.assertRaises(MergeBlockedError) as caught:
            heads.merge(
                resolutions=[
                    resolution(
                        "anchor-drift:anchor.persona.face",
                        ResolutionStrategy.MIGRATE_IDENTITY,
                        evidence_ref=k.ref(EntityKind.RECEIPT, "persona changed"),
                        resolved_by=ACTOR,
                    )
                ]
            )
        self.assertIn("must cite a receipt id", str(caught.exception))

    def test_an_identity_catalogue_both_lines_repointed_is_an_anchor_conflict(self) -> None:
        _, merged = ThreeHeads(
            {"identity_anchors": (persona(),)},
            target={"identity_anchors": (persona(policy_ref=k.ref(EntityKind.POLICY, "policy.stricter")),)},
            source={"identity_anchors": (persona(baseline_digest=OTHER_FACE),)},
        ).merge()
        item = merged.conflict(ConflictKind.IDENTITY_ANCHOR_CONFLICT, "identity-anchor:anchor.persona.face")
        self.assertIsNotNone(item)

    def test_a_constraint_the_merge_newly_violates_is_reported_once(self) -> None:
        _, merged = ThreeHeads(
            {"variant_sets": (axis(), axis("axis.ratio", options=(option("wide"), option("square")), default_option_id="square"))},
            target={
                "variant_sets": (axis(), axis("axis.ratio", options=(option("wide"), option("square")), default_option_id="square")),
                "variant_selection": picked(quality="premium"),
            },
            source={
                "variant_sets": (axis(), axis("axis.ratio", options=(option("wide"), option("square")), default_option_id="square")),
                "variant_constraints": (ratio_constraint(),),
            },
        ).merge()
        item = merged.conflict(ConflictKind.VARIANT_CONSTRAINT_CONFLICT, "variant-constraint:constraint.premium-wide")
        self.assertIn("constraint.premium-wide", item.explanation)


class AdvanceMergeTests(unittest.TestCase):
    """A head moves onto a cleared merge, and onto nothing else."""

    def setUp(self) -> None:
        self.heads = ThreeHeads()
        self.ledger = BranchLedger()
        self.ledger.register(
            Branch(
                branch_id=BRANCH_ID,
                project_id=PROJECT_ID,
                production_id=PRODUCTION_ID,
                profile=BranchProfile.CANONICAL,
                created_at_ms=NOW,
            ),
            head_snapshot_id=self.heads.ids["target"],
            actor=ACTOR,
            now_ms=NOW,
        )

    def advance(self, heads: ThreeHeads, merged: MergeReceipt, **over: Any):
        return advance_merge(
            heads.store,
            self.ledger,
            merged,
            branch_id=BRANCH_ID,
            actor=ACTOR,
            expected_head_snapshot_id=self.heads.ids["target"],
            **over,
        )

    def test_a_cleared_merge_moves_the_branch_head(self) -> None:
        _, merged = self.heads.merge()
        reference, receipt = self.advance(self.heads, merged)
        self.assertEqual(reference.head_snapshot_id, receipt.to_state)
        self.assertEqual(receipt.reason_code, "merge")
        self.assertEqual(self.ledger.head(BRANCH_ID), reference.head_snapshot_id)

    def test_a_merge_without_a_result_cannot_move_a_head(self) -> None:
        dirty = ThreeHeads(
            target={"graph": graph_over(relabel(DEFINITION, "render.logo", "A"))},
            source={"graph": graph_over(relabel(DEFINITION, "render.logo", "B"))},
        )
        _, merged = dirty.merge()
        with self.assertRaises(MergeBlockedError) as caught:
            self.advance(dirty, merged)
        self.assertIn("produced no result snapshot", str(caught.exception))

    def test_advancing_cites_the_merge_receipt_and_its_evidence(self) -> None:
        evidence = k.ref(EntityKind.RECEIPT, "receipt.migration")
        settled = ThreeHeads(
            target={"graph": graph_over(relabel(DEFINITION, "render.logo", "A"))},
            source={"graph": graph_over(relabel(DEFINITION, "render.logo", "B"))},
        )
        _, merged = settled.merge(
            resolutions=[
                resolution(
                    "node:render.logo",
                    ResolutionStrategy.EXPLICIT_CHOICE,
                    evidence_ref=evidence,
                    resolved_by=ACTOR,
                )
            ]
        )
        _, receipt = self.advance(settled, merged)
        self.assertEqual(
            [item.text for item in receipt.evidence_refs],
            sorted({evidence.text, ExternalRef(kind=EntityKind.RECEIPT, reference=merged.merge_id).text}),
        )

    def test_a_receipt_naming_a_result_that_is_not_its_own_is_refused(self) -> None:
        forged = receipt(
            base_snapshot_id=self.heads.ids["base"],
            target_snapshot_id=self.heads.ids["target"],
            source_snapshot_id=self.heads.ids["source"],
            result_snapshot_id=self.heads.ids["target"],
        )
        with self.assertRaises(MergeBlockedError) as caught:
            advance_merge(self.heads.store, self.ledger, forged, branch_id=BRANCH_ID, actor=ACTOR)
        self.assertIn("does not name both heads among its result's parents", str(caught.exception))

    def test_a_head_that_moved_underneath_the_merge_is_a_conflict(self) -> None:
        _, merged = self.heads.merge()
        self.ledger.advance(BRANCH_ID, merged.result_snapshot_id, actor=ACTOR, reason_code="other")
        with self.assertRaises(GraphValidationError) as caught:
            self.advance(self.heads, merged)
        self.assertIn("moved: expected head", str(caught.exception))

    def test_replaying_the_same_command_is_idempotent(self) -> None:
        _, merged = self.heads.merge()
        command, digest = stable("cmd.merge"), k.digest("cmd.merge")

        def replay():
            return advance_merge(
                self.heads.store,
                self.ledger,
                merged,
                branch_id=BRANCH_ID,
                actor=ACTOR,
                command_id=command,
                command_digest=digest,
            )

        first, first_receipt = replay()
        second, second_receipt = replay()
        self.assertEqual(first, second)
        self.assertEqual(first_receipt.transition_id, second_receipt.transition_id)
        self.assertEqual(len(self.heads.store), 4)

    def test_the_store_is_where_the_result_came_from(self) -> None:
        snapshot, merged = self.heads.merge()
        self.assertIs(self.heads.store.get(merged.result_snapshot_id), snapshot)


class TransplantTests(unittest.TestCase):
    """A bounded delta travels between snapshots without merging a branch."""

    def diverged(self) -> ThreeHeads:
        return ThreeHeads(
            target={"graph": graph_over(relabel(DEFINITION, "deliver.web", "Target"))},
            source={"graph": graph_over(relabel(DEFINITION, "render.logo", "Source"))},
        )

    def delta(self, heads: ThreeHeads, **over: Any) -> ProductionDelta:
        payload: dict[str, Any] = dict(
            delta_id=new_id(),
            source_snapshot_id=heads.ids["source"],
            target_snapshot_id=heads.ids["target"],
            merge_base_snapshot_id=heads.ids["base"],
            scope=(DiffCategory.NODE_DEFINITION,),
        )
        payload.update(over)
        return ProductionDelta(**payload)

    def names(self, snapshot: Snapshot) -> dict[str, str]:
        index = snapshot.closure.revision.definition.node_index
        return {key: index[key].display_name for key in sorted(index)}

    def test_a_delta_carries_its_scope_onto_the_target(self) -> None:
        heads = self.diverged()
        snapshot, merged = transplant(heads.store, self.delta(heads, included_node_ids=("render.logo",)))
        self.assertTrue(merged.is_clean)
        self.assertEqual(self.names(snapshot), {"deliver.web": "Target", "render.logo": "Source", "source.logo": ""})

    def test_everything_outside_the_scope_stays_as_the_target_had_it(self) -> None:
        heads = self.diverged()
        snapshot, _ = transplant(heads.store, self.delta(heads, scope=(DiffCategory.INTENT_BRIEF,)))
        self.assertEqual(self.names(snapshot)["render.logo"], "")

    def test_a_delta_is_recorded_as_a_transplant_not_a_merge(self) -> None:
        heads = self.diverged()
        snapshot, merged = transplant(heads.store, self.delta(heads))
        self.assertEqual(snapshot.derivation, SnapshotDerivation.TRANSPLANTED)
        self.assertEqual(merged.auto_resolved_subjects, ("node:deliver.web", "node:render.logo"))
        self.assertEqual(merged.affected_node_ids, ())

    def test_a_delta_that_carries_two_lines_of_the_same_subject_still_conflicts(self) -> None:
        both = ThreeHeads(
            target={"graph": graph_over(relabel(DEFINITION, "render.logo", "A"))},
            source={"graph": graph_over(relabel(DEFINITION, "render.logo", "B"))},
        )
        snapshot, merged = transplant(both.store, self.delta(both))
        self.assertIsNone(snapshot)
        self.assertIsNotNone(merged.conflict(ConflictKind.NODE_DEFINITION_CONFLICT, "node:render.logo"))

    def test_a_precondition_the_target_no_longer_meets_refuses_the_delta(self) -> None:
        heads = self.diverged()
        delta = self.delta(
            heads, preconditions=(DeltaPrecondition(subject="render.logo", kind=PreconditionKind.ABSENT_NODE),)
        )
        with self.assertRaises(GraphValidationError) as caught:
            transplant(heads.store, delta)
        self.assertIn("cannot be transplanted", str(caught.exception))
        self.assertIn("already carries node render.logo", str(caught.exception))

    def test_a_precondition_the_target_still_meets_is_admitted(self) -> None:
        heads = self.diverged()
        delta = self.delta(
            heads,
            preconditions=(
                DeltaPrecondition(subject="deliver.web", kind=PreconditionKind.PRESENT_NODE),
                DeltaPrecondition(subject="render.logo", kind=PreconditionKind.UNCHANGED_DEFINITION),
            ),
        )
        snapshot, _ = transplant(heads.store, delta)
        self.assertEqual(self.names(snapshot)["render.logo"], "Source")

    def test_a_delta_cannot_carry_a_node_it_also_excludes(self) -> None:
        heads = self.diverged()
        delta = self.delta(heads, excluded_node_ids=("render.logo",))
        with self.assertRaises(GraphValidationError) as caught:
            transplant(heads.store, delta)
        self.assertIn("would carry subjects it also excludes", str(caught.exception))
        self.assertIn("render.logo", str(caught.exception))

    def test_a_variant_precondition_pins_the_axis_the_rig_assumed(self) -> None:
        sets = (axis(),)
        heads = ThreeHeads(
            {"variant_sets": sets},
            target={"variant_sets": sets, "variant_selection": picked(quality="premium")},
            source={"variant_sets": sets, "variant_selection": picked(quality="standard")},
        )
        delta = self.delta(
            heads,
            scope=(DiffCategory.VARIANT_SELECTION,),
            preconditions=(
                DeltaPrecondition(subject="axis.quality", kind=PreconditionKind.MATCHING_VARIANT, expected="standard"),
            ),
        )
        with self.assertRaises(GraphValidationError) as caught:
            transplant(heads.store, delta)
        self.assertIn("the target selects premium for axis.quality", str(caught.exception))

    def test_a_delta_names_its_three_snapshots_and_bounds_its_scope(self) -> None:
        heads = self.diverged()
        value = self.delta(heads, scope=(DiffCategory.NODE_DEFINITION, DiffCategory.NODE_DEFINITION))
        self.assertEqual(value.scope, (DiffCategory.NODE_DEFINITION,))
        self.assertEqual(value.reason, None)
        with self.assertRaises(GraphValidationError):
            self.delta(heads, included_node_ids=("render.logo",), excluded_node_ids=("render.logo",))


class MergeModuleSurfaceTests(unittest.TestCase):
    def test_the_module_exports_exactly_the_merge_vocabulary(self) -> None:
        from iris_project_os import merge

        self.assertEqual(
            merge.__all__,
            [
                "ConflictKind",
                "ResolutionStrategy",
                "MergeConflict",
                "Resolution",
                "MergeReceipt",
                "three_way_merge",
                "transplant",
                "advance_merge",
            ],
        )

    def test_every_export_is_reachable_from_the_module(self) -> None:
        from iris_project_os import merge

        for name in merge.__all__:
            self.assertTrue(hasattr(merge, name), name)

    def test_a_merge_receipt_round_trips_through_the_same_rebuilder(self) -> None:
        snapshot, merged = ThreeHeads().settled()
        restored = MergeReceipt.from_payload(merged.to_payload())
        self.assertEqual(restored, merged)
        self.assertEqual(restored.result_snapshot_id, snapshot.snapshot_id)


if __name__ == "__main__":
    unittest.main()
