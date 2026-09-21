"""Area C snapshot law: a closure states its own completeness claim and cannot be relabelled.

A snapshot is the only thing in this kernel that may be cited as evidence, so two
properties are load-bearing. It never changes — a commit that disagrees with what is
already stored is a conflict, not an update — and the class it carries must be
supported by the references inside it. Relabelling a logical snapshot as RELEASE is
how a project silently ships an unjudged render, which is why the claim is checked in
``__post_init__`` and again by every ``dataclasses.replace``.

Rollback is tested here as new history: the intervening snapshots stay reachable, and
an external mutation that already happened is a blocker no ref move can erase.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any

from iris_project_os.branching import (
    Branch,
    BranchLedger,
    BranchProfile,
    PinReason,
    RetentionPin,
    VariantOption,
    VariantSelection,
    VariantSet,
)
from iris_project_os.diffing import DiffCategory
from iris_project_os.errors import (
    GraphValidationError,
    RollbackBlockedError,
    SchemaValidationError,
    SideEffectFenceError,
    SnapshotClosureError,
    StoreConflictError,
    UnsupportedVersionError,
)
from iris_project_os.graph import MaterializationGraph, SideEffectClass
from iris_project_os.identity import EntityKind, ExternalRef, new_id
from iris_project_os.snapshots import (
    DeltaPrecondition,
    ExternalEffectState,
    ExternalSideEffect,
    PreconditionKind,
    ProductionDelta,
    RetentionReason,
    Snapshot,
    SnapshotClass,
    SnapshotClosureManifest,
    SnapshotDerivation,
    SnapshotStore,
    closure_obligations,
    collectable_snapshots,
    commit_snapshot,
    derive_snapshot,
    execute_rollback,
    plan_rollback,
    retention_reasons,
)

from tests import m02_kernel_support as k

PROD = "prod.logo"
NOW = k.CACHE_NOW


def manifest(**over: Any) -> SnapshotClosureManifest:
    """A closure over the chain graph with every evidence family present by default.

    Built here rather than through the shared helper because most of these tests
    assert on one evidence family being *absent*.
    """

    graph: MaterializationGraph = over.pop("graph", None) or k.bound(records=k.chain_records())
    definition = getattr(getattr(graph, "revision", None), "definition", None) or graph
    payload: dict[str, Any] = dict(
        project_id="iris",
        production_id=PROD,
        branch_id="branch.main",
        graph=graph,
        external_admissions=tuple(
            ExternalRef(kind=item.kind, reference=item.reference)
            for item in getattr(definition, "declared_external_inputs", ())
        ),
        quality_decisions=tuple(
            item.decision_ref for item in getattr(graph, "materializations", ()) if item.decision_ref is not None
        ),
        rights_refs=(k.ref(EntityKind.RIGHTS, new_id()),),
        provenance_refs=(k.ref(EntityKind.PROVENANCE, new_id()),),
        policy_refs=(k.ref(EntityKind.POLICY, new_id()),),
        delivery_refs=(k.ref(EntityKind.DESTINATION, new_id()),),
        environment_refs=(k.ref(EntityKind.ENVIRONMENT, new_id()),),
        tool_refs=(k.ref(EntityKind.TOOL, new_id()),),
        model_refs=(k.ref(EntityKind.MODEL, new_id()),),
    )
    payload.update(over)
    return SnapshotClosureManifest(**payload)


def snapshot(closure_over: dict[str, Any] | None = None, **over: Any) -> Snapshot:
    return commit_snapshot(
        manifest(**(closure_over or {})),
        snapshot_class=over.pop("klass", SnapshotClass.VALIDATED_SNAPSHOT),
        created_at_ms=over.pop("created_at_ms", NOW),
        **over,
    )


def side_effect(**over: Any) -> ExternalSideEffect:
    payload: dict[str, Any] = dict(
        side_effect_id=new_id(),
        node_id="deliver.web",
        observed_after_snapshot_id=new_id(),
        destination=k.ref(EntityKind.DESTINATION, "publish.channel"),
    )
    payload.update(over)
    return ExternalSideEffect(**payload)


def axis(option_ids: tuple[str, ...] = ("web", "print")) -> VariantSet:
    return VariantSet(
        variant_set_id="variant.outfit",
        purpose="switches the delivery treatment",
        options=tuple(
            VariantOption(option_id=item, content_digest=k.digest(f"option.{item}")) for item in option_ids
        ),
        default_option_id="web",
    )


def picked(pairs: Any = (("variant.outfit", "web"),)) -> VariantSelection:
    return VariantSelection(selection_id=new_id(), pairs=tuple(pairs))


def branch_of(actor: Any = None, **over: Any) -> Branch:
    payload: dict[str, Any] = dict(
        branch_id=new_id(),
        project_id=new_id(),
        production_id=new_id(),
        profile=BranchProfile.CANONICAL,
        creator=actor,
    )
    payload.update(over)
    return Branch(**payload)


class SnapshotClassTests(unittest.TestCase):
    def test_the_ladder_is_ordered_by_evidence_not_by_name(self) -> None:
        ranks = [
            SnapshotClass.LOGICAL_SNAPSHOT,
            SnapshotClass.MATERIALIZED_SNAPSHOT,
            SnapshotClass.VALIDATED_SNAPSHOT,
            SnapshotClass.RELEASE_SNAPSHOT,
        ]
        self.assertEqual([item.rank for item in ranks], [0, 1, 2, 3])

    def test_each_rung_adds_only_its_own_obligation(self) -> None:
        self.assertFalse(SnapshotClass.LOGICAL_SNAPSHOT.requires_materialization)
        self.assertTrue(SnapshotClass.MATERIALIZED_SNAPSHOT.requires_materialization)
        self.assertFalse(SnapshotClass.MATERIALIZED_SNAPSHOT.requires_quality_evidence)
        self.assertTrue(SnapshotClass.VALIDATED_SNAPSHOT.requires_quality_evidence)
        self.assertFalse(SnapshotClass.VALIDATED_SNAPSHOT.requires_release_evidence)
        self.assertTrue(SnapshotClass.RELEASE_SNAPSHOT.requires_release_evidence)

    def test_at_least_compares_claims_not_identity(self) -> None:
        self.assertTrue(SnapshotClass.RELEASE_SNAPSHOT.at_least("validated_snapshot"))
        self.assertFalse(SnapshotClass.LOGICAL_SNAPSHOT.at_least(SnapshotClass.RELEASE_SNAPSHOT))

    def test_an_invented_class_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            SnapshotClass.parse("MASTER_SNAPSHOT")


class ClosureManifestTests(unittest.TestCase):
    def test_the_owner_fields_are_identifiers_not_uuids(self) -> None:
        value = manifest()
        self.assertEqual(value.project_id, "iris")
        self.assertEqual(value.branch_id, "branch.main")
        with self.assertRaises(SchemaValidationError):
            manifest(project_id="IRIS")

    def test_a_graph_that_is_not_bound_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            manifest(graph=k.chain_definition())

    def test_a_graph_without_a_revision_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            manifest(graph=MaterializationGraph(revision=k.chain_definition()))

    def test_a_revision_relabelled_after_editing_is_refused(self) -> None:
        value = manifest()
        object.__setattr__(value.graph.revision, "digest", k.digest("a different graph"))
        with self.assertRaises(SnapshotClosureError) as caught:
            manifest(graph=value.graph, external_admissions=value.external_admissions)
        self.assertIn("does not carry the digest it claims", str(caught.exception))

    def test_ancestry_is_deduplicated_and_sorted(self) -> None:
        first, second = new_id(), new_id()
        value = manifest(ancestry=(second, first, second))
        self.assertEqual(value.ancestry, tuple(sorted({first, second})))

    def test_a_forged_parent_id_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            manifest(parent_snapshot_ids=("snapshot-1",))

    def test_reference_groups_are_deduplicated_and_ordered_by_text(self) -> None:
        left = k.ref(EntityKind.RIGHTS, "rights.b")
        right = k.ref(EntityKind.RIGHTS, "rights.a")
        value = manifest(rights_refs=(left, right, left))
        self.assertEqual(value.rights_refs, (right, left))

    def test_the_reference_group_width_is_bounded(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            manifest(rights_refs=tuple(k.ref(EntityKind.RIGHTS, f"rights.{index}") for index in range(4097)))
        self.assertIn("exceeds the admitted maximum 4096", str(caught.exception))

    def test_an_environment_fingerprint_must_be_a_digest(self) -> None:
        with self.assertRaises(SchemaValidationError):
            manifest(environment_fingerprint="linux-x86_64")

    def test_the_digest_covers_every_field_of_the_closure(self) -> None:
        first = manifest()
        self.assertEqual(first.digest, replace(first).digest)
        self.assertNotEqual(first.digest, replace(first, branch_id="branch.other").digest)
        self.assertNotEqual(
            first.digest, replace(first, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.other"),)).digest
        )

    def test_artifact_revisions_name_the_node_and_its_bytes(self) -> None:
        pairs = dict(manifest().artifact_revisions)
        self.assertIn("render.logo", pairs)
        self.assertIn("render.logo.out", pairs["render.logo"])
        self.assertTrue(all("@" in item for item in pairs.values()))

    def test_an_unadmitted_declared_input_is_visible(self) -> None:
        value = manifest(external_admissions=())
        self.assertEqual(len(value.unadmitted_external_inputs), 1)
        self.assertIn("external:", "".join(value.unresolved_dependencies))

    def test_an_unmaterialized_node_is_listed_as_a_debt(self) -> None:
        partial = k.bound(records=(k.materialization("render.logo"),))
        value = manifest(graph=partial)
        found = value.unresolved_dependencies
        self.assertIn("node:source.logo", found)
        self.assertIn("node:deliver.web", found)
        self.assertTrue(any(item.startswith("source.logo.out->") for item in found))

    def test_an_empty_closure_selects_nothing_and_reports_nothing(self) -> None:
        value = manifest()
        self.assertEqual(dict(value.effective_selection), {})
        self.assertEqual(value.selection_violations(), ())

    def test_a_selection_is_resolved_through_the_declared_axes(self) -> None:
        value = manifest(variant_sets=(axis(),), variant_selection=picked())
        self.assertEqual(dict(value.effective_selection), {"variant.outfit": "web"})
        self.assertEqual(value.selection_violations(), ())

    def test_an_illegal_selection_is_reported_not_raised(self) -> None:
        value = manifest(variant_sets=(axis(),), variant_selection=picked((("variant.outfit", "cinema"),)))
        self.assertTrue(any("has no option 'cinema'" in item for item in value.selection_violations()))

    def test_the_revision_and_graph_id_are_derived_views(self) -> None:
        value = manifest()
        self.assertEqual(value.graph_id, "graph.test")
        self.assertIs(value.revision, value.graph.revision)

    def test_an_unsupported_contract_version_is_refused(self) -> None:
        with self.assertRaises(UnsupportedVersionError) as caught:
            manifest(contract_version="m02-contract-v9.9")
        self.assertIn("unsupported contract version", str(caught.exception))


class ClosureObligationsTests(unittest.TestCase):
    def test_a_logical_claim_owes_nothing(self) -> None:
        self.assertEqual(closure_obligations(manifest(), SnapshotClass.LOGICAL_SNAPSHOT), ())

    def test_an_unadmitted_input_blocks_every_material_claim(self) -> None:
        found = closure_obligations(manifest(external_admissions=()), SnapshotClass.MATERIALIZED_SNAPSHOT)
        self.assertTrue(found[0].startswith("declared external inputs have no admission receipt: "))

    def test_a_producer_that_never_committed_is_named_by_port(self) -> None:
        value = manifest(graph=k.bound(records=(k.materialization("render.logo"),)))
        found = closure_obligations(value, SnapshotClass.MATERIALIZED_SNAPSHOT)
        self.assertTrue(any("has no admitted producer" in item for item in found), found)
        self.assertTrue(any("emitted nothing" in item for item in found), found)

    def test_a_validated_claim_without_any_judgement_is_refused(self) -> None:
        found = closure_obligations(manifest(quality_decisions=()), SnapshotClass.VALIDATED_SNAPSHOT)
        self.assertIn("claims VALIDATED while the closure binds no quality decision at all", found)

    def test_a_validated_claim_without_a_policy_contract_is_refused(self) -> None:
        found = closure_obligations(manifest(policy_refs=()), SnapshotClass.VALIDATED_SNAPSHOT)
        self.assertIn(
            "claims VALIDATED while the closure binds no policy or fidelity contract reference", found
        )

    def test_a_materialization_judged_elsewhere_is_not_evidence(self) -> None:
        graph = k.bound(
            records=tuple(
                k.materialization(node_id, attempt=new_id(), decision=None)
                for node_id in ("source.logo", "render.logo", "deliver.web")
            )
        )
        value = manifest(
            graph=graph, quality_decisions=(k.ref(EntityKind.QUALITY_DECISION, new_id()),)
        )
        found = closure_obligations(value, SnapshotClass.VALIDATED_SNAPSHOT)
        self.assertTrue(any("carry no bound M01 QualityDecision" in item for item in found), found)

    def test_an_unmaterialized_node_ends_the_quality_inquiry(self) -> None:
        graph = k.bound(records=(k.materialization("source.logo"), k.materialization("render.logo")))
        found = closure_obligations(manifest(graph=graph), SnapshotClass.VALIDATED_SNAPSHOT)
        self.assertIn("claims MATERIALIZED while nodes deliver.web emitted nothing", found)
        self.assertIn("claims VALIDATED while nodes deliver.web emitted nothing", found)
        self.assertEqual(len(found), 2)

    def test_a_release_claim_names_every_missing_evidence_family(self) -> None:
        value = manifest(rights_refs=(), provenance_refs=(), delivery_refs=(), environment_refs=())
        found = closure_obligations(value, SnapshotClass.RELEASE_SNAPSHOT)
        for label in ("rights", "provenance", "delivery", "environment qualification"):
            self.assertIn(f"claims RELEASE while the closure binds no {label} reference", found)

    def test_an_illegal_variant_selection_is_an_obligation_too(self) -> None:
        value = manifest(variant_sets=(axis(),), variant_selection=picked((("variant.outfit", "cinema"),)))
        found = closure_obligations(value, SnapshotClass.LOGICAL_SNAPSHOT)
        self.assertTrue(found[0].startswith("variant selection: "), found)

    def test_obligations_are_returned_so_a_reviewer_sees_them_all(self) -> None:
        value = manifest(quality_decisions=(), policy_refs=(), external_admissions=())
        self.assertGreater(len(closure_obligations(value, SnapshotClass.VALIDATED_SNAPSHOT)), 1)


class SnapshotClaimTests(unittest.TestCase):
    def test_a_committed_snapshot_keeps_the_class_it_was_given(self) -> None:
        self.assertIs(snapshot(klass=SnapshotClass.MATERIALIZED_SNAPSHOT).snapshot_class,
                      SnapshotClass.MATERIALIZED_SNAPSHOT)

    def test_a_weak_closure_cannot_borrow_a_strong_claim(self) -> None:
        with self.assertRaises(SnapshotClosureError) as caught:
            commit_snapshot(manifest(rights_refs=()), snapshot_class=SnapshotClass.RELEASE_SNAPSHOT)
        self.assertIn("but its closure does not carry the evidence: ", str(caught.exception))

    def test_relabelling_after_construction_re_runs_the_claim(self) -> None:
        value = commit_snapshot(manifest(quality_decisions=(), policy_refs=()),
                                snapshot_class=SnapshotClass.LOGICAL_SNAPSHOT)
        with self.assertRaises(SnapshotClosureError) as caught:
            replace(value, snapshot_class=SnapshotClass.VALIDATED_SNAPSHOT)
        self.assertIn("claims VALIDATED while the closure binds no quality decision at all", str(caught.exception))

    def test_the_digest_excludes_the_claim_the_derivation_and_the_label(self) -> None:
        value = snapshot(label="first", created_at_ms=NOW)
        other = commit_snapshot(
            value.closure,
            snapshot_class=SnapshotClass.LOGICAL_SNAPSHOT,
            derivation=SnapshotDerivation.COMMITTED,
            label="second",
            created_at_ms=NOW + 1,
        )
        self.assertEqual(value.digest, other.digest)
        self.assertEqual(other.digest, value.closure.digest)
        self.assertNotEqual(value.snapshot_id, other.snapshot_id)

    def test_a_label_is_free_text_but_not_a_second_identity(self) -> None:
        self.assertEqual(snapshot(label="Launch cut").label, "Launch cut")
        self.assertIsNone(snapshot(label="   ").label)
        with self.assertRaises(SchemaValidationError):
            snapshot(label="x" * 257)

    def test_covered_nodes_and_materializations_are_readable(self) -> None:
        value = snapshot()
        self.assertTrue(value.covers("render.logo"))
        self.assertFalse(value.covers("node.never.declared"))
        self.assertEqual(len(value.materializations_of("render.logo")), 1)
        self.assertEqual(value.materializations_of("node.never.declared"), ())

    def test_the_owner_view_is_the_closures(self) -> None:
        value = snapshot()
        self.assertEqual(value.project_id, "iris")
        self.assertEqual(value.production_id, PROD)
        self.assertEqual(value.branch_id, "branch.main")

    def test_a_snapshot_may_cite_the_snapshots_it_replaces(self) -> None:
        replaced = new_id()
        self.assertEqual(snapshot(supersedes_snapshot_ids=(replaced, replaced)).supersedes_snapshot_ids, (replaced,))

    def test_the_closure_is_reachable_as_a_record_field(self) -> None:
        value = snapshot()
        self.assertEqual(Snapshot.from_payload(value.to_payload()), value)

    def test_an_unknown_field_is_refused_rather_than_dropped(self) -> None:
        with self.assertRaises(SchemaValidationError):
            Snapshot.from_payload({**snapshot().to_payload(), "notes": "typo"})

    def test_a_diff_between_two_snapshots_is_stated_not_computed_twice(self) -> None:
        first = snapshot()
        second = derive_snapshot(first, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.second"),))
        found = first.diff_against(second)
        self.assertEqual(found.base_digest, first.closure.digest)
        self.assertEqual(found.target_digest, second.closure.digest)


class DerivationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = snapshot()

    def test_a_derivation_defaults_to_the_base_as_its_parent(self) -> None:
        moved = derive_snapshot(self.base, branch_id="branch.other")
        self.assertEqual(moved.parent_snapshot_ids, (self.base.snapshot_id,))
        self.assertEqual(moved.origin_snapshot_id, self.base.snapshot_id)

    def test_the_closure_fields_are_changed_not_the_closure_object(self) -> None:
        moved = derive_snapshot(self.base, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.second"),))
        self.assertNotEqual(moved.closure.rights_refs, self.base.closure.rights_refs)
        self.assertNotEqual(moved.closure.digest, self.base.closure.digest)

    def test_handing_in_a_closure_whole_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            derive_snapshot(self.base, closure=manifest())
        self.assertIn("changes closure fields directly", str(caught.exception))

    def test_the_base_snapshot_is_never_edited(self) -> None:
        store = SnapshotStore((self.base,))
        before = store.projection_digest()
        derive_snapshot(self.base, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.second"),))
        self.assertEqual(store.projection_digest(), before)
        self.assertEqual(self.base.closure.rights_refs, store.get(self.base.snapshot_id).closure.rights_refs)

    def test_a_weakened_closure_cannot_keep_a_strong_claim(self) -> None:
        with self.assertRaises(SnapshotClosureError):
            derive_snapshot(self.base, quality_decisions=(), snapshot_class=SnapshotClass.RELEASE_SNAPSHOT)

    def test_a_derivation_may_be_relabelled_only_downward_or_with_evidence(self) -> None:
        moved = derive_snapshot(self.base, snapshot_class=SnapshotClass.MATERIALIZED_SNAPSHOT)
        self.assertIs(moved.snapshot_class, SnapshotClass.MATERIALIZED_SNAPSHOT)
        self.assertEqual(moved.closure.graph.digest, self.base.closure.graph.digest)
        self.assertEqual(moved.closure.rights_refs, self.base.closure.rights_refs)
        self.assertEqual(moved.parent_snapshot_ids, (self.base.snapshot_id,))


class SnapshotStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = SnapshotStore()
        self.first = snapshot()
        self.store.commit(self.first)

    def test_committing_the_same_content_again_is_a_retry(self) -> None:
        self.assertIs(self.store.commit(self.first), self.first)
        self.assertEqual(len(self.store), 1)

    def test_a_second_writer_under_the_same_id_is_a_conflict(self) -> None:
        rival = commit_snapshot(
            manifest(rights_refs=(k.ref(EntityKind.RIGHTS, "rights.other"),)),
            snapshot_id=self.first.snapshot_id,
        )
        with self.assertRaises(StoreConflictError) as caught:
            self.store.commit(rival)
        self.assertIn(
            "already exists with different content; an immutable snapshot is never rewritten",
            str(caught.exception),
        )

    def test_a_reclassified_snapshot_is_a_conflict_not_an_upgrade(self) -> None:
        rival = commit_snapshot(
            self.first.closure,
            snapshot_id=self.first.snapshot_id,
            snapshot_class=SnapshotClass.LOGICAL_SNAPSHOT,
        )
        with self.assertRaises(StoreConflictError):
            self.store.commit(rival)

    def test_an_unknown_snapshot_has_no_projection(self) -> None:
        with self.assertRaises(SnapshotClosureError) as caught:
            self.store.get(new_id())
        self.assertIn("no committed snapshot ", str(caught.exception))
        self.assertNotIn(new_id(), self.store)

    def test_membership_never_raises_on_a_bad_id(self) -> None:
        self.assertNotIn("snapshot-1", self.store)
        self.assertNotIn(None, self.store)

    def test_the_stored_form_is_canonical_lowercase(self) -> None:
        self.assertIn(self.first.snapshot_id.upper(), self.store)

    def test_ids_are_reported_in_a_stable_order(self) -> None:
        second = self.store.commit(derive_snapshot(self.first, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.b"),)))
        self.assertEqual(self.store.snapshot_ids, tuple(sorted([self.first.snapshot_id, second.snapshot_id])))

    def test_descendants_are_the_snapshot_objects_that_cite_a_parent(self) -> None:
        second = self.store.commit(derive_snapshot(self.first, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.b"),)))
        found = self.store.descendants_of(self.first.snapshot_id)
        self.assertEqual([item.snapshot_id for item in found], [second.snapshot_id])

    def test_a_lineage_that_cites_an_uncited_parent_is_refused(self) -> None:
        orphan = self.store.commit(derive_snapshot(self.first, snapshot_id=new_id(), parents=(new_id(),)))
        with self.assertRaises(SnapshotClosureError) as caught:
            self.store.ancestors_of(orphan.snapshot_id)
        self.assertIn("names parents that were never committed", str(caught.exception))

    def test_ancestry_includes_self_and_is_ordered_from_the_root(self) -> None:
        second = self.store.commit(derive_snapshot(self.first, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.b"),)))
        chain = self.store.ancestors_of(second.snapshot_id)
        self.assertEqual(chain[0], self.first.snapshot_id)
        self.assertEqual(chain[-1], second.snapshot_id)

    def test_a_history_that_loops_is_walked_once(self) -> None:
        looped = self.store.commit(derive_snapshot(self.first, snapshot_id=new_id()))
        self.store._items[self.first.snapshot_id] = replace(
            self.first, closure=replace(self.first.closure, parent_snapshot_ids=(looped.snapshot_id,))
        )
        chain = self.store.ancestors_of(looped.snapshot_id)
        self.assertEqual(len(chain), len(set(chain)))
        self.assertEqual(set(chain), {self.first.snapshot_id, looped.snapshot_id})

    def test_a_snapshot_is_its_own_ancestor_for_reachability(self) -> None:
        self.assertTrue(self.store.is_ancestor(self.first.snapshot_id, of_snapshot_id=self.first.snapshot_id))
        self.assertFalse(self.store.is_ancestor(None, of_snapshot_id=self.first.snapshot_id))
        self.assertFalse(self.store.is_ancestor(new_id(), of_snapshot_id=self.first.snapshot_id))

    def test_intervening_history_excludes_the_target_line(self) -> None:
        second = self.store.commit(derive_snapshot(self.first, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.b"),)))
        found = self.store.intervening(head_snapshot_id=second.snapshot_id, target_snapshot_id=self.first.snapshot_id)
        self.assertEqual(found, (second.snapshot_id,))

    def test_the_projection_digest_is_a_function_of_content_only(self) -> None:
        before = self.store.projection_digest()
        self.store.time_travel(self.first.snapshot_id)
        self.assertEqual(self.store.projection_digest(), before)

    def test_the_store_is_not_a_global(self) -> None:
        import iris_project_os.snapshots as module

        self.assertFalse(any(isinstance(value, SnapshotStore) for value in vars(module).values()))


class SnapshotViewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = SnapshotStore()
        self.committed = self.store.commit(snapshot())
        self.view = self.store.time_travel(self.committed.snapshot_id)

    def test_a_historical_view_refuses_assignment(self) -> None:
        with self.assertRaises(SnapshotClosureError) as caught:
            self.view.label = "rewritten"
        self.assertIn("read-only and cannot be mutated", str(caught.exception))

    def test_a_historical_view_refuses_deletion_too(self) -> None:
        with self.assertRaises(SnapshotClosureError):
            del self.view._snapshot

    def test_the_view_exposes_the_same_projection(self) -> None:
        self.assertEqual(self.view.digest, self.committed.digest)
        self.assertIs(self.view.snapshot, self.committed)
        self.assertEqual(self.view.closure, self.committed.closure)
        self.assertEqual(
            self.view.node_ids(), tuple(sorted(self.committed.closure.revision.definition.node_index))
        )

    def test_a_port_that_was_never_produced_reads_as_absence(self) -> None:
        self.assertIsNotNone(self.view.materialization("render.logo", "out"))
        self.assertIsNone(self.view.materialization("render.logo", "missing"))

    def test_the_view_reports_the_debts_it_carries(self) -> None:
        self.assertEqual(self.view.unresolved_dependencies(), self.committed.closure.unresolved_dependencies)

    def test_the_view_diffs_from_history_without_copying_it(self) -> None:
        later = self.store.commit(
            derive_snapshot(self.committed, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.second"),))
        )
        self.assertTrue(self.view.diff_to(later).touches(DiffCategory.RIGHTS_PROVENANCE))


class ExternalSideEffectTests(unittest.TestCase):
    def test_only_an_external_mutation_needs_a_fence(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            side_effect(kind=SideEffectClass.NO_SIDE_EFFECT)
        self.assertIn("needs no external fence", str(caught.exception))

    def test_a_compensation_claim_must_cite_its_receipt(self) -> None:
        with self.assertRaises(SideEffectFenceError) as caught:
            side_effect(state=ExternalEffectState.COMPENSATED)
        self.assertIn("claims COMPENSATED without a compensation receipt", str(caught.exception))

    def test_a_compensated_effect_with_a_receipt_is_settled(self) -> None:
        receipt = k.ref(EntityKind.RECEIPT, new_id())
        value = side_effect(state=ExternalEffectState.COMPENSATED, compensation_receipt_ref=receipt)
        self.assertFalse(value.needs_compensation)

    def test_an_applied_or_irreversible_effect_still_owes_compensation(self) -> None:
        for state in (
            ExternalEffectState.APPLIED,
            ExternalEffectState.RECONCILIATION_REQUIRED,
            ExternalEffectState.IRREVERSIBLE,
        ):
            self.assertTrue(side_effect(state=state).needs_compensation, state)
        self.assertFalse(side_effect(state=ExternalEffectState.NOT_APPLIED).needs_compensation)

    def test_the_destination_must_be_a_reference(self) -> None:
        with self.assertRaises(SchemaValidationError):
            side_effect(destination="publish.channel")

    def test_the_evidence_width_is_bounded(self) -> None:
        with self.assertRaises(SchemaValidationError):
            side_effect(evidence_refs=tuple(k.ref(EntityKind.RECEIPT, f"receipt.{index}") for index in range(65)))

    def test_a_state_that_does_not_exist_is_refused(self) -> None:
        with self.assertRaises(SchemaValidationError):
            side_effect(state="MAYBE_APPLIED")

    def test_an_effect_must_be_dated_against_a_snapshot(self) -> None:
        with self.assertRaises(SchemaValidationError):
            side_effect(observed_after_snapshot_id="head-1")


class ProductionDeltaTests(unittest.TestCase):
    def delta(self, **over: Any) -> ProductionDelta:
        payload: dict[str, Any] = dict(
            delta_id=new_id(),
            source_snapshot_id=new_id(),
            target_snapshot_id=new_id(),
            merge_base_snapshot_id=new_id(),
        )
        payload.update(over)
        return ProductionDelta(**payload)

    def test_a_node_cannot_be_both_carried_and_excluded(self) -> None:
        with self.assertRaises(GraphValidationError) as caught:
            self.delta(included_node_ids=("render.logo",), excluded_node_ids=("render.logo",))
        self.assertIn("cannot both carry and exclude", str(caught.exception))

    def test_the_scope_is_a_set_of_real_diff_categories(self) -> None:
        value = self.delta(scope=(DiffCategory.NODE_DEFINITION, DiffCategory.GRAPH_TOPOLOGY))
        self.assertEqual(value.scope, (DiffCategory.GRAPH_TOPOLOGY, DiffCategory.NODE_DEFINITION))
        with self.assertRaises(SchemaValidationError):
            self.delta(scope=("node-definition",))

    def test_the_scope_may_not_exceed_the_category_enum(self) -> None:
        with self.assertRaises(SchemaValidationError):
            self.delta(scope=tuple(DiffCategory) + (DiffCategory.NODE_DEFINITION,))

    def test_node_lists_are_deduplicated_and_sorted(self) -> None:
        value = self.delta(included_node_ids=("render.logo", "deliver.web", "render.logo"))
        self.assertEqual(value.included_node_ids, ("deliver.web", "render.logo"))

    def test_a_precondition_text_form_names_its_expectation(self) -> None:
        value = DeltaPrecondition(
            subject="render.logo", kind=PreconditionKind.UNCHANGED_CONTENT, expected=k.digest("bytes")
        )
        self.assertTrue(value.text.startswith("UNCHANGED_CONTENT:render.logo="))

    def test_an_absent_node_precondition_fails_when_the_node_is_there(self) -> None:
        found = self.delta(
            preconditions=(DeltaPrecondition(subject="render.logo", kind=PreconditionKind.ABSENT_NODE),)
        ).precondition_failures(snapshot())
        self.assertEqual(len(found), 1)
        self.assertIn("but the target already carries node render.logo", found[0])

    def test_a_present_node_precondition_fails_for_a_missing_node(self) -> None:
        found = self.delta(
            preconditions=(DeltaPrecondition(subject="node.gone", kind=PreconditionKind.PRESENT_NODE),)
        ).precondition_failures(snapshot())
        self.assertIn("but the target has no node node.gone", found[0])

    def test_an_unchanged_content_precondition_compares_the_bytes(self) -> None:
        target = snapshot()
        held = target.graph.materialization_of_first("render.logo").content_digest
        ok = self.delta(
            preconditions=(
                DeltaPrecondition(
                    subject="render.logo", kind=PreconditionKind.UNCHANGED_CONTENT, expected=held
                ),
            )
        ).precondition_failures(target)
        self.assertEqual(ok, ())
        found = self.delta(
            preconditions=(
                DeltaPrecondition(
                    subject="render.logo", kind=PreconditionKind.UNCHANGED_CONTENT, expected=k.digest("other")
                ),
            )
        ).precondition_failures(target)
        self.assertIn("but the target holds ", found[0])

    def test_an_unchanged_definition_precondition_only_checks_presence(self) -> None:
        found = self.delta(
            preconditions=(
                DeltaPrecondition(
                    subject="render.logo",
                    kind=PreconditionKind.UNCHANGED_DEFINITION,
                    expected=k.digest("not compared"),
                ),
            )
        ).precondition_failures(snapshot())
        self.assertEqual(found, ())

    def test_a_variant_precondition_reads_the_effective_selection(self) -> None:
        target = snapshot(
            closure_over={"variant_sets": (axis(),), "variant_selection": picked()}
        )
        ok = self.delta(
            preconditions=(
                DeltaPrecondition(
                    subject="variant.outfit", kind=PreconditionKind.MATCHING_VARIANT, expected="web"
                ),
            )
        ).precondition_failures(target)
        self.assertEqual(ok, ())
        found = self.delta(
            preconditions=(
                DeltaPrecondition(
                    subject="variant.outfit", kind=PreconditionKind.MATCHING_VARIANT, expected="print"
                ),
            )
        ).precondition_failures(target)
        self.assertIn("but the target selects web for variant.outfit", found[0])

    def test_the_delta_text_is_a_digest_of_the_whole_request(self) -> None:
        first = self.delta(reason="carry the approved rig")
        self.assertEqual(len(first.text), 64)
        self.assertNotEqual(first.text, self.delta(reason="carry something else").text)

    def test_preconditions_are_ordered_by_text_so_the_request_is_canonical(self) -> None:
        second = DeltaPrecondition(subject="render.logo", kind=PreconditionKind.PRESENT_NODE)
        first = DeltaPrecondition(subject="deliver.web", kind=PreconditionKind.PRESENT_NODE)
        self.assertEqual(self.delta(preconditions=(second, first)).preconditions, (first, second))


class RollbackPlanningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = SnapshotStore()
        self.ledger = BranchLedger()
        self.actor = k.component_version("m02.os", "1.0.0")
        self.root = self.store.commit(snapshot())
        self.middle = self.store.commit(
            derive_snapshot(self.root, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.second"),))
        )
        self.head = self.store.commit(
            derive_snapshot(self.middle, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.third"),))
        )
        self.branch = branch_of(self.actor)
        self.ledger.register(self.branch, head_snapshot_id=self.head.snapshot_id, actor=self.actor)

    def plan(self, to: Any = None, **over: Any):
        payload: dict[str, Any] = dict(
            branch_id=self.branch.branch_id, to_snapshot_id=(to or self.root).snapshot_id
        )
        payload.update(over)
        return plan_rollback(self.store, self.ledger, **payload)

    def test_a_plan_writes_nothing(self) -> None:
        before = self.store.projection_digest()
        self.plan()
        self.assertEqual(self.store.projection_digest(), before)
        self.assertEqual(len(self.store), 3)

    def test_the_plan_names_the_history_it_must_preserve(self) -> None:
        value = self.plan()
        self.assertEqual(value.from_snapshot_id, self.head.snapshot_id)
        self.assertEqual(value.to_snapshot_id, self.root.snapshot_id)
        self.assertEqual(
            set(value.intervening_snapshot_ids), {self.middle.snapshot_id, self.head.snapshot_id}
        )

    def test_rolling_back_onto_the_current_state_is_not_a_change(self) -> None:
        with self.assertRaises(SnapshotClosureError) as caught:
            self.plan(self.head)
        self.assertIn("already points at snapshot ", str(caught.exception))

    def test_another_lines_history_is_not_reachable(self) -> None:
        sibling = self.store.commit(
            derive_snapshot(self.root, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.sibling"),))
        )
        with self.assertRaises(SnapshotClosureError) as caught:
            self.plan(sibling)
        self.assertIn("is not reachable from the head of branch ", str(caught.exception))
        self.assertIn("is a merge or a fork, never a rollback", str(caught.exception))

    def test_a_side_effect_dated_against_nothing_is_refused(self) -> None:
        with self.assertRaises(SnapshotClosureError) as caught:
            self.plan(side_effects=(side_effect(observed_after_snapshot_id=new_id()),))
        self.assertIn("dated against snapshots that were never committed", str(caught.exception))

    def test_only_effects_after_the_target_are_caught(self) -> None:
        after_head = side_effect(observed_after_snapshot_id=self.head.snapshot_id)
        before_target = side_effect(observed_after_snapshot_id=self.root.snapshot_id)
        self.assertEqual(self.plan(side_effects=(after_head, before_target)).side_effects, (after_head,))

    def test_an_unclearable_outside_world_is_a_blocker_not_a_note(self) -> None:
        effect = side_effect(observed_after_snapshot_id=self.middle.snapshot_id)
        value = self.plan(side_effects=(effect,))
        self.assertFalse(value.is_cleared)
        self.assertIn("moving a ref back does not undo the outside world", " ".join(value.blockers))
        self.assertEqual(value.pending_side_effects, (effect,))
        self.assertEqual(value.compensation_digest(), value.compensation_digest())

    def test_a_compensated_effect_does_not_block(self) -> None:
        effect = side_effect(
            observed_after_snapshot_id=self.middle.snapshot_id,
            state=ExternalEffectState.COMPENSATED,
            compensation_receipt_ref=k.ref(EntityKind.RECEIPT, new_id()),
        )
        value = self.plan(side_effects=(effect,))
        self.assertEqual(value.pending_side_effects, ())

    def test_a_blocking_diff_is_itself_a_blocker(self) -> None:
        value = self.plan()
        self.assertTrue(
            any("blocking semantic differences that need review" in item for item in value.blockers),
            value.blockers,
        )

    def test_a_detached_branch_has_no_head_to_roll_back_from(self) -> None:
        quiet = branch_of(self.actor, profile=BranchProfile.CAMPAIGN)
        self.ledger.register(quiet)
        self.assertIsNone(self.ledger.ref(quiet.branch_id).head_snapshot_id)
        with self.assertRaises(SchemaValidationError):
            plan_rollback(self.store, self.ledger, branch_id=quiet.branch_id, to_snapshot_id=self.root.snapshot_id)

    def test_an_unknown_branch_is_refused(self) -> None:
        with self.assertRaises(GraphValidationError):
            plan_rollback(self.store, self.ledger, branch_id=new_id(), to_snapshot_id=self.root.snapshot_id)


class RollbackExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = SnapshotStore()
        self.ledger = BranchLedger()
        self.actor = k.component_version("m02.os", "1.0.0")
        self.root = self.store.commit(snapshot())
        self.middle = self.store.commit(
            derive_snapshot(self.root, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.second"),))
        )
        self.head = self.store.commit(
            derive_snapshot(self.middle, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.third"),))
        )
        self.branch = branch_of(self.actor)
        self.ledger.register(self.branch, head_snapshot_id=self.head.snapshot_id, actor=self.actor)
        self.plan = plan_rollback(
            self.store, self.ledger, branch_id=self.branch.branch_id, to_snapshot_id=self.root.snapshot_id
        )

    def execute(self, plan: Any = None, **over: Any):
        payload: dict[str, Any] = dict(actor=self.actor, acknowledge_blocking_diff=True)
        payload.update(over)
        return execute_rollback(self.store, self.ledger, plan or self.plan, **payload)

    def test_a_rollback_creates_history_rather_than_deleting_it(self) -> None:
        created, receipt, _ = self.execute()
        self.assertEqual(len(self.store), 4)
        self.assertEqual(created.derivation, SnapshotDerivation.ROLLED_BACK)
        self.assertEqual(set(created.parent_snapshot_ids), {self.head.snapshot_id, self.root.snapshot_id})
        self.assertEqual(receipt.preserved_snapshot_ids, self.plan.intervening_snapshot_ids)

    def test_the_head_moves_and_still_reaches_the_abandoned_history(self) -> None:
        created, _, _ = self.execute()
        self.assertEqual(self.ledger.head(self.branch.branch_id), created.snapshot_id)
        self.assertIn(self.middle.snapshot_id, self.store.ancestors_of(created.snapshot_id))

    def test_the_new_snapshot_restates_the_restored_state(self) -> None:
        created, _, _ = self.execute()
        self.assertIs(created.snapshot_class, self.root.snapshot_class)
        self.assertEqual(created.closure.graph.digest, self.root.closure.graph.digest)
        self.assertEqual(created.closure.rights_refs, self.root.closure.rights_refs)
        self.assertEqual(
            replace(
                created.closure,
                parent_snapshot_ids=self.root.closure.parent_snapshot_ids,
                branch_id=self.root.closure.branch_id,
            ).digest,
            self.root.digest,
        )

    def test_an_outstanding_mutation_fences_the_rollback(self) -> None:
        plan = plan_rollback(
            self.store,
            self.ledger,
            branch_id=self.branch.branch_id,
            to_snapshot_id=self.root.snapshot_id,
            side_effects=(side_effect(observed_after_snapshot_id=self.middle.snapshot_id),),
        )
        with self.assertRaises(SideEffectFenceError) as caught:
            self.execute(plan)
        self.assertIn(
            "fenced by external mutations that need explicit compensation procedures", str(caught.exception)
        )

    def test_one_procedure_cannot_answer_two_mutations(self) -> None:
        plan = plan_rollback(
            self.store,
            self.ledger,
            branch_id=self.branch.branch_id,
            to_snapshot_id=self.root.snapshot_id,
            side_effects=(
                side_effect(observed_after_snapshot_id=self.middle.snapshot_id),
                side_effect(observed_after_snapshot_id=self.head.snapshot_id),
            ),
        )
        with self.assertRaises(SideEffectFenceError) as caught:
            self.execute(plan, compensation_refs=(k.ref(EntityKind.RECEIPT, new_id()),))
        self.assertIn("every one needs its own procedure", str(caught.exception))

    def test_a_compensation_procedure_per_mutation_clears_the_fence(self) -> None:
        effects = (
            side_effect(observed_after_snapshot_id=self.middle.snapshot_id),
            side_effect(observed_after_snapshot_id=self.head.snapshot_id),
        )
        plan = plan_rollback(
            self.store,
            self.ledger,
            branch_id=self.branch.branch_id,
            to_snapshot_id=self.root.snapshot_id,
            side_effects=effects,
        )
        refs = tuple(k.ref(EntityKind.RECEIPT, new_id()) for _ in effects)
        _, receipt, _ = self.execute(plan, compensation_refs=refs)
        self.assertEqual(receipt.compensation_refs, tuple(sorted(refs, key=lambda item: item.text)))

    def test_a_blocking_diff_needs_an_explicit_acknowledgement(self) -> None:
        with self.assertRaises(RollbackBlockedError) as caught:
            self.execute(acknowledge_blocking_diff=False)
        self.assertIn("blocking semantic difference(s); acknowledge them explicitly", str(caught.exception))

    def test_a_raced_head_is_refused_by_the_ref(self) -> None:
        self.ledger.advance(self.branch.branch_id, new_id(), actor=self.actor)
        with self.assertRaises(GraphValidationError) as caught:
            self.execute()
        self.assertIn("moved: expected head ", str(caught.exception))

    def test_a_rollback_receipt_is_written_against_the_plan(self) -> None:
        created, receipt, transition = self.execute()
        self.assertEqual(receipt.rollback_id, self.plan.plan_id)
        self.assertEqual(receipt.created_snapshot_id, created.snapshot_id)
        self.assertEqual(transition.transition_id, self.ledger.ref(self.branch.branch_id).last_transition_id)
        self.assertEqual(self.ledger.transitions(self.branch.branch_id)[-1].reason_code, "rollback")


class RetentionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = SnapshotStore()
        self.root = self.store.commit(snapshot())
        self.child = self.store.commit(
            derive_snapshot(self.root, rights_refs=(k.ref(EntityKind.RIGHTS, "rights.second"),))
        )

    def reasons(self, snapshot_id: str = None, **over: Any):
        payload: dict[str, Any] = dict(live_heads=(), pins=(), now_ms=NOW)
        payload.update(over)
        return retention_reasons(self.store, snapshot_id or self.root.snapshot_id, **payload)

    def test_being_reachable_from_a_live_head_is_a_reason(self) -> None:
        self.assertIn(RetentionReason.REACHABLE_FROM_LIVE_BRANCH, self.reasons(live_heads=(self.child.snapshot_id,)))
        self.assertNotIn(RetentionReason.REACHABLE_FROM_LIVE_BRANCH, self.reasons(self.child.snapshot_id, live_heads=(self.root.snapshot_id,)))

    def test_a_release_above_a_validated_line_wins_the_stronger_reason(self) -> None:
        solo = SnapshotStore()
        base = solo.commit(snapshot())
        solo.commit(derive_snapshot(base, snapshot_class=SnapshotClass.RELEASE_SNAPSHOT))
        found = retention_reasons(solo, base.snapshot_id, live_heads=(), pins=(), now_ms=NOW)
        self.assertIn(RetentionReason.CARRIED_BY_RELEASE_SNAPSHOT, found)
        self.assertNotIn(RetentionReason.CARRIED_BY_VALIDATED_SNAPSHOT, found)

    def test_a_validated_descendant_is_its_own_reason_class(self) -> None:
        found = self.reasons(live_heads=())
        self.assertIn(RetentionReason.CARRIED_BY_VALIDATED_SNAPSHOT, found)

    def test_rights_alone_keep_material_alive(self) -> None:
        self.assertIn(RetentionReason.RIGHTS_OR_PROVENANCE_REQUIRED, self.reasons(live_heads=()))

    def test_a_pin_by_identity_holds_a_snapshot(self) -> None:
        value = RetentionPin(
            pin_id=new_id(),
            target=k.ref(EntityKind.SNAPSHOT, self.root.snapshot_id),
            reasons=(PinReason.GOLDEN,),
        )
        self.assertIn(RetentionReason.PINNED, self.reasons(pins=(value,)))

    def test_a_pin_by_content_digest_holds_a_snapshot(self) -> None:
        value = RetentionPin(
            pin_id=new_id(),
            target=ExternalRef(
                kind=EntityKind.SNAPSHOT, reference=self.root.snapshot_id, content_digest=self.root.digest
            ),
            reasons=(PinReason.GOLDEN,),
        )
        self.assertIn(RetentionReason.PINNED, self.reasons(pins=(value,)))

    def test_a_versioned_pin_names_a_different_thing(self) -> None:
        value = RetentionPin(
            pin_id=new_id(),
            target=k.ref(EntityKind.SNAPSHOT, self.root.snapshot_id, version="3"),
            reasons=(PinReason.GOLDEN,),
        )
        self.assertNotIn(RetentionReason.PINNED, self.reasons(pins=(value,)))

    def test_an_expired_ttl_pin_stops_holding(self) -> None:
        value = RetentionPin(
            pin_id=new_id(),
            target=k.ref(EntityKind.SNAPSHOT, self.root.snapshot_id),
            reasons=(PinReason.RETENTION_TTL,),
            expires_at_ms=NOW - 1,
        )
        self.assertNotIn(RetentionReason.PINNED, self.reasons(pins=(value,)))

    def test_an_unexpired_rights_pin_still_holds(self) -> None:
        value = RetentionPin(
            pin_id=new_id(),
            target=k.ref(EntityKind.SNAPSHOT, self.root.snapshot_id),
            reasons=(PinReason.RIGHTS,),
            expires_at_ms=NOW - 1,
        )
        self.assertIn(RetentionReason.PINNED, self.reasons(pins=(value,)))

    def test_a_garbage_pin_is_skipped_not_fatal(self) -> None:
        self.assertNotIn(RetentionReason.PINNED, self.reasons(pins=("not-a-pin",)))

    def test_superseding_snapshots_are_kept_as_the_source(self) -> None:
        moved = self.store.commit(derive_snapshot(self.root, supersedes_snapshot_ids=(self.root.snapshot_id,)))
        self.assertIn(RetentionReason.SUPERSESION_SOURCE, self.reasons(moved.snapshot_id, live_heads=()))
        self.assertNotIn(RetentionReason.SUPERSESION_SOURCE, self.reasons(self.child.snapshot_id, live_heads=()))

    def test_a_collector_only_takes_unclaimed_history(self) -> None:
        self.assertEqual(collectable_snapshots(self.store, now_ms=NOW), ())
        spare = self.store.commit(
            commit_snapshot(
                manifest(rights_refs=(), provenance_refs=()),
                snapshot_class=SnapshotClass.LOGICAL_SNAPSHOT,
                created_at_ms=NOW,
            )
        )
        found = collectable_snapshots(self.store, now_ms=NOW)
        self.assertIn(spare.snapshot_id, found)
        self.assertNotIn(self.root.snapshot_id, found)

    def test_reasons_are_sorted_so_a_report_is_stable(self) -> None:
        found = self.reasons(live_heads=(self.child.snapshot_id,))
        self.assertEqual(found, tuple(sorted(found, key=lambda item: item.value)))

    def test_an_unknown_snapshot_has_no_retention_claims(self) -> None:
        with self.assertRaises(SnapshotClosureError):
            retention_reasons(self.store, new_id())


class ModuleSurfaceTests(unittest.TestCase):
    def test_every_public_name_is_exported_once(self) -> None:
        import iris_project_os.snapshots as module

        self.assertEqual(len(module.__all__), len(set(module.__all__)))
        for name in module.__all__:
            self.assertTrue(hasattr(module, name), name)

    def test_the_derivation_set_names_every_way_history_can_start(self) -> None:
        self.assertEqual(
            [item.value for item in SnapshotDerivation],
            ["BASELINE", "COMMITTED", "MERGED", "TRANSPLANTED", "ROLLED_BACK"],
        )
