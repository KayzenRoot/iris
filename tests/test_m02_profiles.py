"""The five WO §7 synthetic profiles, run through the kernel's required families.

One kernel, five domains: a logo, a stylized game asset, a film sequence, a virtual
spokesperson and a non-visual audio bed. Each is assembled in
:mod:`examples.m02_synthetic_profiles` from kernel primitives only, so a failure here
means the kernel is narrower than the contract claims — not that a fixture was typed
badly. The tests deliberately run the same assertion across all five profiles wherever
the law is domain-neutral, and switch to one profile only where the requirement is
specific to it (a persona anchor, an ordered plate input, a whole-node repair).

Two families carry the weight of WO §8. A claim the closure does not support has to be
refused *before* anything downstream reads it, and a disagreement between two lines of
work has to come back as a typed conflict instead of a silent choice.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any, Sequence

from iris_project_os.analysis import Change, compute_fingerprint, impact_of
from iris_project_os.archive import (
    ArchiveObject,
    ArchiveTier,
    DamageKind,
    IntegrityOutcome,
    ObjectProbe,
    ProbeState,
    audit_archive,
    restore_archive,
    seal_archive,
)
from iris_project_os.branching import (
    Branch,
    BranchLedger,
    BranchProfile,
    IdentityAnchorPolicy,
    PinReason,
    RetentionPin,
    VariantOption,
    VariantSelection,
    VariantSet,
    resolve_selection,
    validate_selection,
)
from iris_project_os.build import compile_build_delta, dirty_frontier, repair_frontier
from iris_project_os.diffing import DiffCategory, semantic_diff
from iris_project_os.errors import (
    ArchiveError,
    BuildError,
    GraphValidationError,
    IdentityError,
    LifecycleError,
    ReleaseError,
    SideEffectFenceError,
    SnapshotClosureError,
    StoreConflictError,
)
from iris_project_os.graph import (
    DependencyFacet,
    EdgeKind,
    GraphEdge,
    NodeRole,
    PortCardinality,
    SideEffectClass,
    SubgraphInterface,
)
from iris_project_os.identity import ArtifactIdentity, EntityKind, ExternalRef, RevisionRef, new_id
from iris_project_os.lifecycle import (
    LifecyclePhase,
    ProductionLedger,
    ReleaseCondition,
    ReviewCondition,
    initial_vector,
)
from iris_project_os.merge import Resolution, ResolutionStrategy, advance_merge, three_way_merge
from iris_project_os.promotion import GateKind, compile_gates, rungs_crossed
from iris_project_os.release import begin_release
from iris_project_os.serialization import dumps, loads
from iris_project_os.snapshots import (
    ExternalEffectState,
    ExternalSideEffect,
    RetentionReason,
    Snapshot,
    SnapshotClass,
    SnapshotStore,
    collectable_snapshots,
    closure_obligations,
    commit_snapshot,
    derive_snapshot,
    execute_rollback,
    plan_rollback,
    retention_reasons,
)
from iris_project_os.stores import (
    InMemoryArtifactStore,
    InMemoryReceiptStore,
    ReceiptKind,
    receipt_kind_of,
)
from iris_quality.contracts import QualityClass

from examples import m02_synthetic_profiles as p

ACTOR = p.ACTOR
NOW = p.NOW_MS
PROFILES = p.PROFILES
NAMES = sorted(PROFILES)
VISUAL = {"vector.svg", "raster.png", "mesh.tri", "material.pbr", "rig.skeleton", "animation.clip", "frames.exr", "video.prores", "avatar.pose"}


def profile(name: str):
    return PROFILES[f"profile.{name}"] if name.startswith("profile.") is False else PROFILES[name]


def sel(fixture, **pairs: str):
    """A selection of this profile's axes, written with short names.

    Axes are named ``axis.lod`` in the closure and ``lod`` in a test, which is the only
    translation this helper does; an option the axis does not offer stays unfixed.
    """

    offered = {item.variant_set_id for item in fixture.variant_sets}
    resolved = {
        (key if key in offered else f"axis.{key}"): value for key, value in pairs.items()
    }
    return VariantSelection(
        selection_id=p.identity_id(
            "selection."
            + fixture.profile_id
            + "."
            + ".".join(f"{key}.{value}" for key, value in sorted(resolved.items()))
        ),
        pairs=tuple(sorted(resolved.items())),
        actor=ACTOR,
        created_at_ms=NOW,
    )


def chosen(fixture, selection):
    """A selection written either as an object or as short-name keyword pairs."""

    return selection if isinstance(selection, VariantSelection) else sel(fixture, **selection)


def pick(fixture, **pairs: str):
    """This profile's selection with ``pairs`` overridden."""

    return sel(fixture, **{**fixture.selection.as_map(), **pairs})


def migrate(selection, receipt_ids):
    return replace(selection, migration_receipt_ids=tuple(sorted(receipt_ids)))


def record_for(fixture, node_id: str, port_id: str = "out", **over: Any):
    return next(
        replace(item, **over)
        for item in fixture.records()
        if item.node_id == node_id and item.port_id == port_id
    )


def heads(fixture, base, target, source, classes=(SnapshotClass.VALIDATED_SNAPSHOT,) * 3):
    """Three committed snapshots of one production, ready to be merged."""

    store = SnapshotStore()
    ids: dict[str, str] = {}
    for role, selection, klass in zip(("base", "target", "source"), (base, target, source), classes):
        snapshot = commit_snapshot(
            fixture.closure(selection=chosen(fixture, selection)),
            snapshot_class=klass,
            snapshot_id=p.identity_id(f"head.{fixture.profile_id}.{role}"),
            created_at_ms=NOW,
        )
        store.commit(snapshot)
        ids[role] = snapshot.snapshot_id
    return store, ids


def merge_of(store, ids, **over: Any):
    return three_way_merge(
        store,
        base_snapshot_id=ids["base"],
        target_snapshot_id=ids["target"],
        source_snapshot_id=ids["source"],
        actor=ACTOR,
        created_at_ms=NOW + 1_000,
        **over,
    )


def carried(fixture, snapshot, *, to: LifecyclePhase = LifecyclePhase.ACCEPTED, forget: Sequence[str] = ()):
    """A production walked the only legal route to ``to``, optionally owing one claim less.

    ``forget`` is how the test asks what the kernel does when an obligation is missing: the
    ladder is real history, so a gap has to be refused rather than jumped.
    """

    ledger = ProductionLedger(
        fixture.production_id,
        initial_vector(fixture.production_id, project_id=fixture.project_id),
    )
    ledger.advance(actor=ACTOR, phase=LifecyclePhase.PLANNED, now_ms=NOW)
    ledger.advance(actor=ACTOR, phase=LifecyclePhase.READY, now_ms=NOW)
    ledger.advance(
        actor=ACTOR, phase=LifecyclePhase.MATERIALIZED, candidate_snapshot_id=snapshot.snapshot_id, now_ms=NOW
    )
    ledger.advance(
        actor=ACTOR, phase=LifecyclePhase.VALIDATING, review=ReviewCondition.PENDING, now_ms=NOW
    )
    claims: dict[str, Any] = dict(
        candidate_snapshot_id=snapshot.snapshot_id,
        review=ReviewCondition.APPROVED,
        review_receipt=ExternalRef(kind=EntityKind.RECEIPT, reference=p.identity_id("receipt.review")),
        promotion_ref=ExternalRef(kind=EntityKind.EVIDENCE, reference=p.identity_id("bundle.acceptance")),
    )
    ledger.advance(
        actor=ACTOR,
        phase=LifecyclePhase.ACCEPTED,
        **{key: value for key, value in claims.items() if key not in forget},
        now_ms=NOW,
    )
    if to is not LifecyclePhase.ACCEPTED:
        ledger.advance(actor=ACTOR, phase=to, now_ms=NOW)
    return ledger


def delivered(fixture):
    """The material this profile actually ships, which is what an archive owes a reader."""

    delivery = {node.node_id for node in fixture.definition.nodes if node.role is NodeRole.DELIVERY}
    return tuple(record for record in fixture.records() if record.node_id in delivery)


def archived(fixture, **over: Any):
    """A sealed archive of this profile, holding its delivered bytes.

    Sealing takes the evidence-complete closure: §18 reads provenance out of the snapshot
    rather than out of a caller's argument, so a profile whose rights and provenance are
    still outstanding has nothing to archive yet.
    """

    snapshot = fixture.commit(release_ready=True, **over)
    return (
        snapshot,
        seal_archive(
            carried(fixture, snapshot),
            snapshot,
            tier=ArchiveTier.ARCHIVE_REPRODUCIBLE,
            actor=ACTOR,
            assets=tuple(
                ArchiveObject(
                    ref=ExternalRef(kind=EntityKind.ARTIFACT, reference=f"asset.{item.node_id}.{item.port_id}"),
                    digest=item.content_digest,
                )
                for item in delivered(fixture)
            ),
            **over,
        ),
    )


def inspected(manifest, *, absent: Sequence[str] = ()):
    """Every reference the archive must be able to reach, probed as the store answers."""

    held = {item.ref.text: item.digest for item in manifest.assets}
    found = []
    for reference in manifest.required_refs():
        gone = reference.text in absent
        found.append(
            ObjectProbe(
                ref=reference,
                state=ProbeState.ABSENT if gone else ProbeState.PRESENT,
                observed_digest=None if gone else (
                    reference.content_digest or held.get(reference.text) or p.digest(reference.text)
                ),
                inspected_at_ms=NOW,
            )
        )
    return tuple(found)


class GraphLawTests(unittest.TestCase):
    """Every profile must be a legal typed graph, and the law must actually bite."""

    def test_every_profile_is_a_chain_from_a_source_to_a_delivery(self) -> None:
        for name in NAMES:
            with self.subTest(profile=name):
                roles = {node.role for node in profile(name).definition.nodes}
                self.assertIn(NodeRole.SOURCE, roles)
                self.assertIn(NodeRole.DELIVERY, roles)
                self.assertIn(NodeRole.VALIDATION, roles)

    def test_every_profile_declares_its_provenance_on_its_edges(self) -> None:
        for name in NAMES:
            with self.subTest(profile=name):
                for edge in profile(name).definition.edges:
                    self.assertTrue(edge.facets, f"{edge.edge_id} declares no facet")

    def test_the_kernel_refuses_an_edge_that_crosses_semantic_types(self) -> None:
        logo = profile("logo-web")
        crossed = GraphEdge(
            edge_id="edge.impossible",
            kind=EdgeKind.MATERIAL_CAUSAL,
            source_node_id="source.brandmark",
            source_port_id="out",
            target_node_id="validate.legibility",
            target_port_id="in",
            facets=(DependencyFacet.CONTENT,),
        )
        with self.assertRaises(GraphValidationError) as caught:
            replace(logo.definition, edges=logo.definition.edges + (crossed,))
        self.assertIn("semantic types must match", str(caught.exception))

    def test_an_ordered_input_refuses_a_producer_that_declares_no_position(self) -> None:
        film = profile("film-sequence")
        plates = tuple(
            replace(edge, order=None) for edge in film.definition.edges if edge.edge_id.startswith("edge.plate")
        )
        others = tuple(edge for edge in film.definition.edges if not edge.edge_id.startswith("edge.plate"))
        with self.assertRaises(GraphValidationError) as caught:
            replace(film.definition, edges=plates + others)
        self.assertIn("MANY_ORDERED", str(caught.exception))

    def test_an_unscoped_dependency_is_refused(self) -> None:
        logo = profile("logo-web")
        with self.assertRaises(GraphValidationError) as caught:
            replace(
                logo.definition,
                edges=(replace(logo.definition.edges[0], facets=()), *logo.definition.edges[1:]),
            )
        self.assertIn("facet", str(caught.exception).lower())

    def test_only_a_subgraph_node_may_have_a_boundary(self) -> None:
        logo = profile("logo-web")
        moved = SubgraphInterface(
            node_id="render.social",
            inner_graph_ref=ExternalRef(kind=EntityKind.GRAPH, reference="graph.other", version="1"),
        )
        with self.assertRaises(GraphValidationError) as caught:
            replace(logo.definition, interfaces=(*logo.definition.interfaces, moved))
        self.assertIn("not SUBGRAPH", str(caught.exception))

    def test_a_subgraph_node_without_a_boundary_is_refused(self) -> None:
        logo = profile("logo-web")
        with self.assertRaises(GraphValidationError) as caught:
            replace(logo.definition, interfaces=())
        self.assertIn("boundary is undefined", str(caught.exception))

    def test_an_external_mutation_without_a_policy_is_refused(self) -> None:
        film = profile("film-sequence")
        with self.assertRaises(GraphValidationError) as caught:
            replace(
                film.definition,
                nodes=tuple(
                    replace(node, side_effect_policy=None) if node.node_id == "publish.cdn" else node
                    for node in film.definition.nodes
                ),
            )
        self.assertIn("idempotency", str(caught.exception))

    def test_a_quality_floor_refuses_a_weaker_producer(self) -> None:
        logo = profile("logo-web")
        weakened = tuple(
            replace(record, quality_class=QualityClass.PREVIEW) if record.node_id == "render.social" else record
            for record in logo.records()
        )
        with self.assertRaises(GraphValidationError) as caught:
            logo.bound(records=weakened)
        self.assertIn("requires REVIEW", str(caught.exception))

    def test_a_required_input_without_a_producer_is_refused(self) -> None:
        logo = profile("logo-web")
        edges = tuple(edge for edge in logo.definition.edges if edge.edge_id != "edge.render")
        with self.assertRaises(GraphValidationError) as caught:
            replace(logo.definition, edges=edges)
        self.assertIn("required input render.social.in", str(caught.exception))

    def test_a_material_cycle_is_refused_even_through_an_optional_port(self) -> None:
        game = profile("game-asset")
        blockout = game.definition.node("build.blockout")
        motion = game.definition.node("animate.idle").port("out").semantic_type
        widened = replace(
            blockout,
            inputs=(
                *blockout.inputs,
                replace(blockout.inputs[0], port_id="feedback", semantic_type=motion, required=False),
            ),
        )
        loop = GraphEdge(
            edge_id="edge.loop",
            kind=EdgeKind.MATERIAL_CAUSAL,
            source_node_id="animate.idle",
            source_port_id="out",
            target_node_id="build.blockout",
            target_port_id="feedback",
            facets=(DependencyFacet.CONTENT,),
        )
        nodes = tuple(widened if node.node_id == "build.blockout" else node for node in game.definition.nodes)
        with self.assertRaises(GraphValidationError) as caught:
            replace(game.definition, nodes=nodes, edges=(*game.definition.edges, loop))
        self.assertIn("cyclic", str(caught.exception).lower())

    def test_a_port_may_stay_unfed_when_it_is_declared_optional(self) -> None:
        spokesperson = profile("spokesperson")
        self.assertFalse(spokesperson.definition.node("drive.avatar").port("gesture").required)


class SnapshotClaimTests(unittest.TestCase):
    """The class of a snapshot is a claim the closure has to support."""

    def test_each_profile_freezes_at_the_class_it_claims(self) -> None:
        for name in NAMES:
            with self.subTest(profile=name):
                fixture = profile(name)
                self.assertEqual(fixture.commit().snapshot_class, fixture.claim)

    def test_each_profile_may_claim_less_than_it_holds(self) -> None:
        for name in NAMES:
            with self.subTest(profile=name):
                self.assertEqual(
                    profile(name).commit(SnapshotClass.MATERIALIZED_SNAPSHOT).snapshot_class,
                    SnapshotClass.MATERIALIZED_SNAPSHOT,
                )

    def test_a_release_claim_above_the_evidence_is_refused_by_name(self) -> None:
        logo = profile("logo-web")
        obligations = closure_obligations(logo.closure(), SnapshotClass.RELEASE_SNAPSHOT)
        for family in ("rights", "provenance", "delivery", "environment"):
            self.assertTrue(
                any(family in item for item in obligations), f"nothing refuses a missing {family} reference"
            )
        with self.assertRaises(SnapshotClosureError) as caught:
            logo.commit(SnapshotClass.RELEASE_SNAPSHOT)
        self.assertIn("environment qualification", str(caught.exception))

    def test_a_materialized_claim_never_fails_silently_on_a_missing_node(self) -> None:
        for name in NAMES:
            with self.subTest(profile=name):
                fixture = profile(name)
                emitted = {record.node_id for record in fixture.records()}
                self.assertTrue(emitted, f"{name} closes over no material at all")
                partial = fixture.records()[:-1]
                obligations = closure_obligations(
                    fixture.closure(graph=fixture.bound(records=partial)), SnapshotClass.MATERIALIZED_SNAPSHOT
                )
                self.assertTrue(any("emitted nothing" in item for item in obligations), obligations)

    def test_a_validated_claim_needs_a_decision_behind_every_output(self) -> None:
        for name in NAMES:
            with self.subTest(profile=name):
                fixture = profile(name)
                unjudged = tuple(
                    replace(record, decision_ref=None) for record in fixture.records()
                )
                obligations = closure_obligations(
                    fixture.closure(graph=fixture.bound(records=unjudged)), SnapshotClass.VALIDATED_SNAPSHOT
                )
                self.assertTrue(any("no bound M01 QualityDecision" in item for item in obligations), obligations)

    def test_an_unadmitted_declared_input_refuses_every_class(self) -> None:
        for name in NAMES:
            for klass in (SnapshotClass.LOGICAL_SNAPSHOT, SnapshotClass.VALIDATED_SNAPSHOT):
                with self.subTest(profile=name, klass=klass.value):
                    fixture = profile(name)
                    obligations = closure_obligations(
                        fixture.closure(external_admissions=()), klass
                    )
                    self.assertTrue(
                        any("no admission receipt" in item for item in obligations), obligations
                    )

    def test_an_illegal_variant_combination_is_refused_before_any_work(self) -> None:
        game = profile("game-asset")
        illegal = pick(game, lod="hero", export="generic")
        obligations = closure_obligations(game.closure(selection=illegal), SnapshotClass.VALIDATED_SNAPSHOT)
        self.assertEqual(
            obligations,
            (
                "variant selection: constraint constraint.generic-export: axis.export=generic requires "
                "axis.lod to be one of ['low', 'mid'], not hero",
            ),
        )

    def test_a_release_claim_is_refused_the_moment_one_family_is_dropped(self) -> None:
        film = profile("film-sequence")
        for field in ("rights_refs", "provenance_refs", "delivery_refs", "environment_refs"):
            with self.subTest(field=field):
                obligations = closure_obligations(
                    film.closure(**{field: ()}), SnapshotClass.RELEASE_SNAPSHOT
                )
                self.assertEqual(len(obligations), 1, obligations)

    def test_a_snapshot_recomputes_its_claim_when_it_is_built_directly(self) -> None:
        logo = profile("logo-web")
        with self.assertRaises(SnapshotClosureError) as caught:
            Snapshot(
                snapshot_id=p.identity_id("snapshot.inflated"),
                closure=logo.closure(),
                snapshot_class=SnapshotClass.RELEASE_SNAPSHOT,
            )
        self.assertIn("RELEASE_SNAPSHOT", str(caught.exception))


class VariantLawTests(unittest.TestCase):
    """Variants are switches inside one identity; identity itself is not a switch."""

    def test_every_profile_ships_a_legal_selection(self) -> None:
        for name in NAMES:
            with self.subTest(profile=name):
                self.assertEqual(profile(name).closure().selection_violations(), ())

    def test_each_declared_constraint_actually_bites(self) -> None:
        cases = {
            "logo-web": {"palette": "night", "ratio": "square"},
            "game-asset": {"lod": "hero", "export": "generic"},
            "film-sequence": {"master": "25", "subtitles": "burned"},
        }
        for name, pairs in cases.items():
            with self.subTest(profile=name):
                fixture = profile(name)
                self.assertTrue(fixture.variant_constraints, f"{name} declares no constraint to bite")
                violations = fixture.closure(selection=pick(fixture, **pairs)).selection_violations()
                self.assertTrue(violations, "the illegal combination was accepted")

    def test_unselected_axes_fall_back_to_their_declared_default(self) -> None:
        for name in NAMES:
            with self.subTest(profile=name):
                fixture = profile(name)
                dropped = fixture.selection
                for set_id, _ in fixture.selection.pairs:
                    dropped = dropped.without(set_id)
                effective = resolve_selection(fixture.variant_sets, dropped)
                for variant_set in fixture.variant_sets:
                    self.assertEqual(
                        effective[variant_set.variant_set_id], variant_set.default_option_id
                    )

    def test_selecting_a_variant_returns_a_new_binding(self) -> None:
        logo = profile("logo-web")
        bound = logo.bound()
        moved = bound.select_variant("axis.palette", "day")
        self.assertEqual(dict(bound.variant_selection)["axis.palette"], "night")
        self.assertEqual(dict(moved.variant_selection)["axis.palette"], "day")

    def test_a_selection_of_an_option_the_axis_does_not_offer_is_refused(self) -> None:
        game = profile("game-asset")
        reasons = validate_selection(
            game.variant_sets, game.variant_constraints, pick(game, lod="impossible")
        )
        refused = [item for item in reasons if "no option" in item]
        self.assertEqual(len(refused), 1, reasons)
        self.assertIn("impossible", refused[0])
        self.assertIn("['hero', 'low', 'mid']", refused[0])

    def test_a_persona_face_may_not_drift_through_an_ordinary_variant(self) -> None:
        spokesperson = profile("spokesperson")
        drifted = pick(spokesperson, **{"persona-face": "restyled"})
        self.assertTrue(
            spokesperson.closure(selection=drifted).selection_violations(),
            "an unauthorised persona restyle was accepted",
        )

    def test_a_recorded_identity_migration_admits_the_drift(self) -> None:
        spokesperson = profile("spokesperson")
        authorised = migrate(
            pick(spokesperson, **{"persona-face": "restyled"}), (p.MIGRATION_FACE,)
        )
        self.assertEqual(
            spokesperson.closure(selection=authorised).selection_violations(), ()
        )

    def test_a_protected_axis_refuses_an_option_nobody_measured(self) -> None:
        spokesperson = profile("spokesperson")
        anchor_set = next(item for item in spokesperson.variant_sets if item.variant_set_id == "axis.persona-face")
        with self.assertRaises(IdentityError) as caught:
            replace(
                anchor_set,
                options=tuple(replace(option, anchor_digest=None) for option in anchor_set.options),
            )
        self.assertIn("declare no anchor_digest", str(caught.exception))

    def test_a_protected_axis_must_name_the_option_that_preserves_it(self) -> None:
        with self.assertRaises(IdentityError) as caught:
            VariantSet(
                variant_set_id="axis.unbaselined",
                purpose="An axis that moves its anchor without saying which option does not.",
                options=(
                    VariantOption(option_id="same", content_digest=p.digest("same"), anchor_digest=p.digest("face")),
                    VariantOption(option_id="moved", content_digest=p.digest("moved"), anchor_digest=p.digest("other"), migration_receipt_id=new_id()),
                ),
                identity_anchor=IdentityAnchorPolicy(
                    anchor_id="anchor.unbaselined",
                    policy_ref=ExternalRef(kind=EntityKind.POLICY, reference="policy.unbaselined"),
                    baseline_digest=p.digest("face"),
                ),
            )
        self.assertIn("must name the baseline option", str(caught.exception))


class DiffAndImpactTests(unittest.TestCase):
    """A variant is a difference someone can read, and a change sweeps a cone."""

    def test_two_variants_of_one_profile_differ_only_in_their_selection(self) -> None:
        for name in NAMES:
            fixture = profile(name)
            if len(fixture.variant_sets) < 1:
                continue
            with self.subTest(profile=name):
                left = fixture.closure(selection=fixture.selection)
                right_set = fixture.variant_sets[-1]
                other = next(item.option_id for item in right_set.options if item.option_id != fixture.selection.option_of(right_set.variant_set_id))
                right = fixture.closure(selection=pick(fixture, **{right_set.variant_set_id.split(".")[-1]: other}))
                categories = {entry.category for entry in semantic_diff(left, right).entries}
                self.assertEqual(categories, {DiffCategory.VARIANT_SELECTION})

    def test_a_policy_revision_changes_one_node(self) -> None:
        film = profile("film-sequence")
        diff = semantic_diff(film.closure(), film.closure(definition=film.revised_definition))
        self.assertEqual(
            [(entry.category.value, entry.subject) for entry in diff.entries],
            [("NODE_DEFINITION", "grade.sequence")],
        )

    def test_the_fingerprint_of_a_node_follows_the_selection(self) -> None:
        logo = profile("logo-web")
        day = logo.bound(selection=pick(logo, palette="day"))
        night = logo.bound(selection=pick(logo, palette="night"))
        self.assertNotEqual(
            compute_fingerprint(day, "deliver.web").fingerprint,
            compute_fingerprint(night, "deliver.web").fingerprint,
        )
        self.assertEqual(
            compute_fingerprint(day, "deliver.web").fingerprint,
            compute_fingerprint(logo.bound(selection=pick(logo, palette="day")), "deliver.web").fingerprint,
        )

    def test_a_plate_change_sweeps_the_picture_chain(self) -> None:
        film = profile("film-sequence")
        cone = impact_of(
            film.bound(),
            (
                Change(
                    node_id="source.plate-a",
                    facet=DependencyFacet.CONTENT,
                    previous_digest=p.digest("plate-a-old"),
                    current_digest=p.digest("plate-a-new"),
                ),
            ),
        )
        self.assertEqual(cone.direct, ("comp.plates",))
        self.assertIn("grade.sequence", cone.transitive)
        self.assertIn("deliver.master", cone.transitive)
        self.assertEqual(cone.clean, ("source.plate-b",))

    def test_a_rights_change_sweeps_only_the_edge_that_admitted_it(self) -> None:
        audio = profile("voice-music")
        cone = impact_of(
            audio.bound(),
            (
                Change(
                    node_id="source.library",
                    facet=DependencyFacet.RIGHTS,
                    previous_digest=p.digest("bed-old"),
                    current_digest=p.digest("bed-new"),
                ),
            ),
        )
        self.assertEqual(cone.direct, ("mix.final",))
        self.assertEqual(cone.transitive, ())
        self.assertIn("deliver.feed", cone.clean)

    def test_a_change_naming_a_node_that_does_not_exist_is_refused(self) -> None:
        logo = profile("logo-web")
        with self.assertRaises(GraphValidationError) as caught:
            impact_of(logo.bound(), (Change(node_id="node.ghost", facet=DependencyFacet.CONTENT),))
        self.assertIn("unknown node", str(caught.exception))


class IncrementalBuildTests(unittest.TestCase):
    """A local repair must stay local, and what it cannot cover stays refused."""

    def setUp(self) -> None:
        self.film = profile("film-sequence")
        self.diff = semantic_diff(
            self.film.closure(), self.film.closure(definition=self.film.revised_definition)
        )
        self.bound = self.film.bound(definition=self.film.revised_definition)

    def delta(self, **over: Any):
        return compile_build_delta(
            self.diff,
            graph_id=self.film.graph_id,
            base_revision=ExternalRef(
                kind=EntityKind.REVISION, reference=self.film.revision().revision_id, version="1"
            ),
            target_revision=ExternalRef(
                kind=EntityKind.REVISION,
                reference=self.film.revision(self.film.revised_definition).revision_id,
                version="1",
            ),
            **over,
        )

    def test_a_delta_names_the_facet_that_changed(self) -> None:
        delta = self.delta()
        self.assertEqual([(c.node_id, c.facet.value) for c in delta.changes], [("grade.sequence", "SEMANTICS")])
        self.assertEqual([c.value for c in delta.categories], ["NODE_DEFINITION"])

    def test_a_delta_from_a_revision_to_itself_states_no_change(self) -> None:
        same = ExternalRef(kind=EntityKind.REVISION, reference=self.film.revision().revision_id, version="1")
        with self.assertRaises(BuildError) as caught:
            compile_build_delta(self.diff, graph_id=self.film.graph_id, base_revision=same, target_revision=same)
        self.assertIn("compare two revisions", str(caught.exception))

    def test_the_dirty_frontier_marks_only_the_changed_node(self) -> None:
        frontier = dirty_frontier(self.bound, self.delta())
        self.assertEqual([node.node_id for node in frontier.nodes], ["grade.sequence"])
        self.assertEqual(frontier.nodes[0].state.value, "DIRTY")

    def test_a_slice_cannot_settle_a_change_that_needs_the_whole_node(self) -> None:
        frontier = dirty_frontier(self.bound, self.delta())
        repair = repair_frontier(self.bound, frontier)
        self.assertEqual(repair.targets, ())
        self.assertEqual(repair.uncovered, ("grade.sequence",))

    def test_a_declared_whole_node_repair_settles_the_frontier(self) -> None:
        frontier = dirty_frontier(self.bound, self.delta())
        settled = repair_frontier(self.bound, frontier, whole_node=("grade.sequence",))
        self.assertEqual([(t.node_id, t.covers_whole_node) for t in settled.targets], [("grade.sequence", True)])
        self.assertEqual(settled.uncovered, ())


class MergeLawTests(unittest.TestCase):
    """Two lines of work on one production: what merges, what conflicts, what advances."""

    def test_a_one_sided_variant_change_merges_cleanly(self) -> None:
        logo = profile("logo-web")
        store, ids = heads(logo, logo.selection, logo.selection, pick(logo, palette="day"))
        result, receipt = merge_of(store, ids)
        self.assertEqual(receipt.conflicts, ())
        self.assertIsNotNone(result)
        self.assertEqual(receipt.auto_resolved_subjects, ("variant:axis.palette",))
        self.assertEqual(
            resolve_selection(logo.variant_sets, result.closure.variant_selection)["axis.palette"], "day"
        )

    def test_a_selection_disagreement_comes_back_typed_not_resolved(self) -> None:
        game = profile("game-asset")
        store, ids = heads(
            game,
            {"axis.lod": "mid", "axis.export": "generic"},
            pick(game, lod="hero", export="native"),
            pick(game, lod="low"),
        )
        result, receipt = merge_of(store, ids)
        conflict = receipt.conflicts[0]
        self.assertEqual(conflict.kind.value, "VARIANT_SELECTION_CONFLICT")
        self.assertEqual(conflict.subject, "variant:axis.lod")
        self.assertFalse(conflict.blocking)
        self.assertEqual((conflict.target_side, conflict.source_side), ("hero", "low"))
        self.assertEqual(
            resolve_selection(game.variant_sets, result.closure.variant_selection),
            {"axis.export": "native", "axis.lod": "hero"},
        )

    def test_an_explicit_settlement_is_recorded_on_the_conflict(self) -> None:
        game = profile("game-asset")
        store, ids = heads(
            game,
            {"axis.lod": "mid", "axis.export": "generic"},
            pick(game, lod="hero", export="native"),
            pick(game, lod="low"),
        )
        evidence = ExternalRef(kind=EntityKind.RECEIPT, reference=new_id())
        _, receipt = merge_of(
            store,
            ids,
            resolutions=(
                Resolution(
                    subject="variant:axis.lod",
                    strategy=ResolutionStrategy.EXPLICIT_CHOICE,
                    evidence_ref=evidence,
                    resolved_by=ACTOR,
                ),
            ),
        )
        conflict = receipt.conflicts[0]
        self.assertEqual(conflict.resolution, ResolutionStrategy.EXPLICIT_CHOICE)
        self.assertEqual(conflict.resolution_ref, evidence)
        self.assertTrue(conflict.is_resolved)
        self.assertIn(evidence.text, [item.text for item in receipt.evidence_refs])

    def test_a_merge_inherits_the_weaker_claim(self) -> None:
        game = profile("game-asset")
        store, ids = heads(
            game,
            game.selection,
            game.selection,
            game.selection,
            classes=(
                SnapshotClass.VALIDATED_SNAPSHOT,
                SnapshotClass.VALIDATED_SNAPSHOT,
                SnapshotClass.MATERIALIZED_SNAPSHOT,
            ),
        )
        result, _ = merge_of(store, ids)
        self.assertEqual(result.snapshot_class, SnapshotClass.MATERIALIZED_SNAPSHOT)

    def test_a_merge_that_would_become_illegal_is_reported_as_a_constraint(self) -> None:
        game = profile("game-asset")
        store, ids = heads(
            game,
            sel(game, lod="mid", export="native"),
            sel(game, lod="hero", export="native"),
            sel(game, lod="mid", export="generic"),
        )
        result, receipt = merge_of(store, ids)
        kinds = {conflict.kind.value for conflict in receipt.conflicts}
        self.assertIn("VARIANT_CONSTRAINT_CONFLICT", kinds)
        self.assertTrue(all(conflict.blocking for conflict in receipt.conflicts))
        self.assertIsNone(result)

    def test_heads_from_another_production_cannot_be_merged(self) -> None:
        game = profile("game-asset")
        store, ids = heads(game, game.selection, game.selection, game.selection)
        logo = profile("logo-web")
        foreign = commit_snapshot(
            logo.closure(),
            snapshot_class=SnapshotClass.VALIDATED_SNAPSHOT,
            snapshot_id=p.identity_id("head.foreign"),
            created_at_ms=NOW,
        )
        store.commit(foreign)
        with self.assertRaises(SnapshotClosureError) as caught:
            merge_of(store, {**ids, "target": foreign.snapshot_id})
        self.assertIn("merging across productions is a different operation", str(caught.exception))

    def test_advancing_a_branch_cites_the_merge_receipt(self) -> None:
        logo = profile("logo-web")
        store, ids = heads(logo, logo.selection, logo.selection, pick(logo, palette="day"))
        merged, receipt = merge_of(store, ids)
        ledger = BranchLedger()
        ledger.register(
            Branch(
                branch_id=logo.branch_id,
                project_id=logo.project_id,
                production_id=logo.production_id,
                profile=BranchProfile.CANONICAL,
                created_at_ms=NOW,
            ),
            head_snapshot_id=ids["target"],
            actor=ACTOR,
            now_ms=NOW,
        )
        reference, transition = advance_merge(
            store,
            ledger,
            receipt,
            branch_id=logo.branch_id,
            actor=ACTOR,
            expected_head_snapshot_id=ids["target"],
        )
        self.assertEqual(reference.head_snapshot_id, merged.snapshot_id)
        self.assertEqual(transition.reason_code, "merge")
        self.assertIn(f"receipt:{receipt.merge_id}", [item.text for item in transition.evidence_refs])


class RollbackTests(unittest.TestCase):
    """Rollback moves a head onto recorded history and forgets nothing."""

    def setUp(self) -> None:
        self.logo = profile("logo-web")
        self.base = commit_snapshot(
            self.logo.closure(),
            snapshot_class=SnapshotClass.VALIDATED_SNAPSHOT,
            snapshot_id=p.identity_id("rollback.base"),
            created_at_ms=NOW,
        )
        later = pick(self.logo, palette="day")
        self.head = derive_snapshot(
            self.base,
            snapshot_id=p.identity_id("rollback.head"),
            graph=self.logo.bound(selection=later),
            variant_selection=later,
            created_at_ms=NOW + 5,
        )
        self.store = SnapshotStore()
        self.store.commit(self.base)
        self.store.commit(self.head)
        self.ledger = BranchLedger()
        self.ledger.register(
            Branch(
                branch_id=self.logo.branch_id,
                project_id=self.logo.project_id,
                production_id=self.logo.production_id,
                profile=BranchProfile.CANONICAL,
                created_at_ms=NOW,
            ),
            head_snapshot_id=self.head.snapshot_id,
            actor=ACTOR,
            now_ms=NOW,
        )

    def plan(self, **over: Any):
        return plan_rollback(
            self.store,
            self.ledger,
            branch_id=self.logo.branch_id,
            to_snapshot_id=self.base.snapshot_id,
            **over,
        )

    def effect(self, state: ExternalEffectState) -> ExternalSideEffect:
        return ExternalSideEffect(
            side_effect_id=p.identity_id(f"effect.{state.value}"),
            node_id="deliver.web",
            observed_after_snapshot_id=self.head.snapshot_id,
            destination=ExternalRef(kind=EntityKind.DESTINATION, reference="destination.web"),
            attempt_id=new_id(),
            kind=SideEffectClass.EXTERNAL_MUTATION,
            state=state,
            recorded_at_ms=NOW,
        )

    def test_a_rollback_moves_the_head_and_keeps_the_superseded_state(self) -> None:
        plan = self.plan()
        created, receipt, _ = execute_rollback(self.store, self.ledger, plan, actor=ACTOR, now_ms=NOW + 20)
        self.assertEqual(self.ledger.head(self.logo.branch_id), created.snapshot_id)
        self.assertEqual(receipt.preserved_snapshot_ids, (self.head.snapshot_id,))
        self.assertIsNotNone(self.store.get(self.head.snapshot_id))
        self.assertEqual(dict(created.closure.variant_selection.pairs)["axis.palette"], "night")

    def test_a_rollback_names_what_it_undoes(self) -> None:
        plan = self.plan()
        self.assertEqual(
            [(entry.category.value, entry.subject) for entry in plan.diff.entries],
            [("VARIANT_SELECTION", "axis.palette")],
        )

    def test_a_state_that_is_not_history_cannot_be_rolled_back_to(self) -> None:
        game = profile("game-asset")
        foreign = commit_snapshot(
            game.closure(),
            snapshot_class=SnapshotClass.VALIDATED_SNAPSHOT,
            snapshot_id=p.identity_id("rollback.foreign"),
            created_at_ms=NOW,
        )
        self.store.commit(foreign)
        with self.assertRaises(SnapshotClosureError) as caught:
            plan_rollback(
                self.store, self.ledger, branch_id=self.logo.branch_id, to_snapshot_id=foreign.snapshot_id
            )
        self.assertIn("never a rollback", str(caught.exception))

    def test_an_unapplied_effect_does_not_fence_a_rollback(self) -> None:
        plan = self.plan(side_effects=(self.effect(ExternalEffectState.NOT_APPLIED),))
        self.assertEqual(plan.blockers, ())
        execute_rollback(self.store, self.ledger, plan, actor=ACTOR, now_ms=NOW + 20)

    def test_an_applied_external_effect_fences_a_rollback(self) -> None:
        plan = self.plan(side_effects=(self.effect(ExternalEffectState.APPLIED),))
        self.assertTrue(plan.blockers)
        with self.assertRaises(SideEffectFenceError) as caught:
            execute_rollback(self.store, self.ledger, plan, actor=ACTOR, now_ms=NOW + 20)
        self.assertIn("compensation", str(caught.exception))

    def test_a_recorded_compensation_lets_the_rollback_proceed(self) -> None:
        plan = self.plan(side_effects=(self.effect(ExternalEffectState.APPLIED),))
        compensation = ExternalRef(kind=EntityKind.RECEIPT, reference=p.identity_id("receipt.compensation"))
        created, receipt, _ = execute_rollback(
            self.store,
            self.ledger,
            plan,
            actor=ACTOR,
            compensation_refs=(compensation,),
            acknowledge_blocking_diff=True,
            now_ms=NOW + 20,
        )
        self.assertEqual(receipt.compensation_refs, (compensation,))
        self.assertEqual(self.ledger.head(self.logo.branch_id), created.snapshot_id)


class RetentionAndArchiveTests(unittest.TestCase):
    """What is still needed stays, and what is archived can be proven and reopened."""

    def test_live_history_is_never_collectable(self) -> None:
        logo = profile("logo-web")
        base = commit_snapshot(
            logo.closure(), snapshot_class=SnapshotClass.VALIDATED_SNAPSHOT, snapshot_id=p.identity_id("ret.base"), created_at_ms=NOW
        )
        later = pick(logo, palette="day")
        head = derive_snapshot(
            base,
            snapshot_id=p.identity_id("ret.head"),
            graph=logo.bound(selection=later),
            variant_selection=later,
            created_at_ms=NOW + 5,
        )
        store = SnapshotStore()
        store.commit(base)
        store.commit(head)
        self.assertEqual(collectable_snapshots(store, live_heads=[head.snapshot_id]), ())
        self.assertEqual(collectable_snapshots(store), (head.snapshot_id,))
        self.assertEqual(
            retention_reasons(store, base.snapshot_id), (RetentionReason.CARRIED_BY_VALIDATED_SNAPSHOT,)
        )

    def test_an_audit_pin_keeps_a_detached_snapshot_alive(self) -> None:
        logo = profile("logo-web")
        base = commit_snapshot(
            logo.closure(), snapshot_class=SnapshotClass.VALIDATED_SNAPSHOT, snapshot_id=p.identity_id("pin.base"), created_at_ms=NOW
        )
        store = SnapshotStore()
        store.commit(base)
        pin = RetentionPin(
            pin_id=p.identity_id("pin.audit"),
            target=ExternalRef(kind=EntityKind.SNAPSHOT, reference=base.snapshot_id),
            reasons=(PinReason.AUDIT,),
            actor=ACTOR,
            created_at_ms=NOW,
        )
        self.assertEqual(collectable_snapshots(store, pins=(pin,), now_ms=NOW), ())
        self.assertEqual(
            retention_reasons(store, base.snapshot_id, pins=(pin,), now_ms=NOW),
            (RetentionReason.PINNED,),
        )
        lapsed = replace(pin, created_at_ms=NOW - 10, expires_at_ms=NOW - 1)
        self.assertEqual(collectable_snapshots(store, pins=(lapsed,), now_ms=NOW), ())
        ttl = replace(lapsed, reasons=(PinReason.RETENTION_TTL,))
        self.assertEqual(collectable_snapshots(store, pins=(ttl,), now_ms=NOW), (base.snapshot_id,))

    def test_a_release_keeps_its_whole_history_alive(self) -> None:
        film = profile("film-sequence")
        base = commit_snapshot(
            film.closure(), snapshot_class=SnapshotClass.VALIDATED_SNAPSHOT, snapshot_id=p.identity_id("rel.base"), created_at_ms=NOW
        )
        release = derive_snapshot(
            base, snapshot_id=p.identity_id("rel.master"), snapshot_class=SnapshotClass.RELEASE_SNAPSHOT, created_at_ms=NOW + 5
        )
        store = SnapshotStore()
        store.commit(base)
        store.commit(release)
        self.assertIn(
            RetentionReason.CARRIED_BY_RELEASE_SNAPSHOT,
            retention_reasons(store, base.snapshot_id),
        )

    def test_each_accepted_profile_seals_audits_and_reopens(self) -> None:
        for name in NAMES:
            with self.subTest(profile=name):
                _, manifest = archived(profile(name))
                report = audit_archive(manifest, inspected(manifest), inspector=ACTOR, now_ms=NOW)
                self.assertTrue(report.is_clean, report.findings)
                restoration = restore_archive(manifest, inspected(manifest), actor=ACTOR, now_ms=NOW)
                self.assertEqual(restoration.lost, ())
                self.assertTrue(restoration.usable)
                self.assertTrue(restoration.fully_reproducible)

    def test_an_archive_refuses_a_closure_that_cannot_say_where_the_work_came_from(self) -> None:
        logo = profile("logo-web")
        snapshot = logo.commit()
        with self.assertRaises(ArchiveError) as caught:
            seal_archive(
                carried(logo, snapshot),
                snapshot,
                tier=ArchiveTier.ARCHIVE_REPRODUCIBLE,
                actor=ACTOR,
                assets=tuple(
                    ArchiveObject(
                        ref=ExternalRef(kind=EntityKind.ARTIFACT, reference=f"asset.{item.node_id}.{item.port_id}"),
                        digest=item.content_digest,
                    )
                    for item in delivered(logo)
                ),
                now_ms=NOW,
            )
        self.assertIn("no provenance reference", str(caught.exception))

    def test_damage_is_reported_as_damage_and_refuses_the_clean_claim(self) -> None:
        film = profile("film-sequence")
        _, manifest = archived(film)
        gone = manifest.assets[0].ref.text
        probes = inspected(manifest, absent=(gone,))
        report = audit_archive(manifest, probes, inspector=ACTOR, now_ms=NOW)
        self.assertEqual(report.outcome, IntegrityOutcome.DAMAGED)
        self.assertEqual([item.kind for item in report.damaged], [DamageKind.MISSING_OBJECT])
        restoration = restore_archive(manifest, probes, actor=ACTOR, now_ms=NOW)
        self.assertEqual([item.text for item in restoration.lost], [gone])
        self.assertFalse(restoration.usable)
        self.assertFalse(restoration.fully_reproducible)

    def test_a_production_that_was_never_accepted_has_no_archive(self) -> None:
        film = profile("film-sequence")
        ledger = ProductionLedger(
            film.production_id, initial_vector(film.production_id, project_id=film.project_id)
        )
        with self.assertRaises(ArchiveError) as caught:
            seal_archive(ledger, film.commit(), tier=ArchiveTier.ARCHIVE_LIGHT, actor=ACTOR, now_ms=NOW)
        self.assertIn("DRAFT", str(caught.exception))


class LifecycleAndPromotionTests(unittest.TestCase):
    """ACCEPTED and RELEASED are different facts, and neither is a string."""

    def test_every_production_starts_at_draft(self) -> None:
        for name in NAMES:
            fixture = profile(name)
            vector = initial_vector(fixture.production_id, project_id=fixture.project_id)
            self.assertEqual(vector.phase, LifecyclePhase.DRAFT)
            self.assertEqual(vector.production_id, fixture.production_id)

    def test_acceptance_requires_the_promotion_evidence(self) -> None:
        logo = profile("logo-web")
        with self.assertRaises(LifecycleError) as caught:
            carried(logo, logo.commit(), forget=("promotion_ref",))
        self.assertIn("promotion evidence bundle", str(caught.exception))

    def test_a_production_skips_no_rung_of_the_ladder(self) -> None:
        logo = profile("logo-web")
        ledger = ProductionLedger(
            logo.production_id, initial_vector(logo.production_id, project_id=logo.project_id)
        )
        with self.assertRaises(LifecycleError) as caught:
            ledger.advance(actor=ACTOR, phase=LifecyclePhase.MATERIALIZED, candidate_snapshot_id=new_id())
        self.assertIn("skips a rung", str(caught.exception))

    def test_accepted_is_not_released(self) -> None:
        film = profile("film-sequence")
        vector = carried(film, film.commit()).current
        self.assertEqual(vector.phase, LifecyclePhase.ACCEPTED)
        self.assertEqual(vector.release_condition, ReleaseCondition.UNRELEASED)

    def test_a_release_needs_something_accepted_first(self) -> None:
        film = profile("film-sequence")
        ledger = ProductionLedger(
            film.production_id, initial_vector(film.production_id, project_id=film.project_id)
        )
        with self.assertRaises(ReleaseError) as caught:
            begin_release(
                ledger,
                release_snapshot_id=film.commit().snapshot_id,
                destination=ExternalRef(kind=EntityKind.DESTINATION, reference="destination.cdn"),
                actor=ACTOR,
                now_ms=NOW,
            )
        self.assertIn("nothing to prepare", str(caught.exception))

    def test_what_a_promotion_owes_is_compiled_from_the_rungs_crossed(self) -> None:
        self.assertEqual(
            [rung.value for rung in rungs_crossed(LifecyclePhase.VALIDATING, LifecyclePhase.ACCEPTED)],
            ["ACCEPTED"],
        )
        to_release = compile_gates(LifecyclePhase.ACCEPTED, LifecyclePhase.RELEASED)
        self.assertIn(GateKind.DELIVERY, to_release)
        self.assertNotIn(GateKind.DELIVERY, compile_gates(LifecyclePhase.VALIDATING, LifecyclePhase.ACCEPTED))


class StoreAdmissionTests(unittest.TestCase):
    """The reference stores hold what the kernel vouched for, and replay is harmless."""

    def test_an_admitted_revision_is_locatable_by_digest(self) -> None:
        film = profile("film-sequence")
        store = InMemoryArtifactStore()
        identity = ArtifactIdentity(
            artifact_id=p.identity_id("artifact.master"),
            production_id=film.production_id,
            semantic_type_ref=ExternalRef(kind=EntityKind.SEMANTIC_TYPE, reference="video.prores"),
            display_name="master",
            created_at_ms=NOW,
        )
        store.register(identity)
        revision = RevisionRef(
            artifact_id=identity.artifact_id,
            revision_id=new_id(),
            content_digest=p.digest("master bytes"),
            semantic_type_ref=identity.semantic_type_ref,
            created_at_ms=NOW,
        )
        store.admit(revision)
        self.assertEqual([item.revision_id for item in store.locate(p.digest("master bytes"))], [revision.revision_id])
        self.assertEqual([item.artifact_id for item in store.for_production(film.production_id)], [identity.artifact_id])

    def test_a_second_registration_of_a_different_identity_is_refused(self) -> None:
        film = profile("film-sequence")
        store = InMemoryArtifactStore()
        identity = ArtifactIdentity(
            artifact_id=p.identity_id("artifact.duplicate"),
            production_id=film.production_id,
            semantic_type_ref=ExternalRef(kind=EntityKind.SEMANTIC_TYPE, reference="video.prores"),
            display_name="first",
            created_at_ms=NOW,
        )
        store.register(identity)
        with self.assertRaises(StoreConflictError):
            store.register(replace(identity, display_name="second"))

    def test_a_replayed_receipt_is_recorded_once(self) -> None:
        from iris_project_os.identity import TransitionReceipt

        store = InMemoryReceiptStore()
        receipt = TransitionReceipt(
            transition_id=p.identity_id("receipt.lifecycle"),
            entity_kind=EntityKind.PRODUCTION,
            entity_id=profile("film-sequence").production_id,
            from_state="DRAFT",
            to_state="PLANNED",
            actor=ACTOR,
            reason_code="planned",
            timestamp_ms=NOW,
        )
        self.assertEqual(receipt_kind_of(receipt), ReceiptKind.TRANSITION)
        store.record(receipt)
        store.record(receipt)
        self.assertEqual(dict(store.counts())[ReceiptKind.TRANSITION.value], 1)
        self.assertTrue(store.holds(ReceiptKind.TRANSITION, receipt.transition_id))

    def test_a_store_returns_the_very_snapshot_it_held(self) -> None:
        for name in NAMES:
            with self.subTest(profile=name):
                store = SnapshotStore()
                snapshot = profile(name).commit()
                store.commit(snapshot)
                self.assertIs(store.get(snapshot.snapshot_id), snapshot)

    def test_a_second_identity_under_one_id_is_refused(self) -> None:
        store = SnapshotStore()
        logo = profile("logo-web")
        snapshot = commit_snapshot(
            logo.closure(),
            snapshot_class=SnapshotClass.VALIDATED_SNAPSHOT,
            snapshot_id=p.identity_id("store.clash"),
            created_at_ms=NOW,
        )
        other = commit_snapshot(
            logo.closure(selection=pick(logo, palette="day")),
            snapshot_class=SnapshotClass.VALIDATED_SNAPSHOT,
            snapshot_id=snapshot.snapshot_id,
            created_at_ms=NOW,
        )
        store.commit(snapshot)
        with self.assertRaises(StoreConflictError):
            store.commit(other)

    def test_history_is_walking_not_copying(self) -> None:
        logo = profile("logo-web")
        base = commit_snapshot(
            logo.closure(), snapshot_class=SnapshotClass.VALIDATED_SNAPSHOT, snapshot_id=p.identity_id("hist.base"), created_at_ms=NOW
        )
        head = derive_snapshot(base, snapshot_id=p.identity_id("hist.head"), created_at_ms=NOW + 5)
        store = SnapshotStore()
        store.commit(base)
        store.commit(head)
        self.assertEqual(store.ancestors_of(head.snapshot_id), (base.snapshot_id, head.snapshot_id))
        self.assertEqual([item.snapshot_id for item in store.descendants_of(base.snapshot_id)], [head.snapshot_id])
        self.assertTrue(store.is_ancestor(base.snapshot_id, of_snapshot_id=head.snapshot_id))
        self.assertFalse(store.is_ancestor(head.snapshot_id, of_snapshot_id=base.snapshot_id))


class SerializationTests(unittest.TestCase):
    """A closure that serialises twice is a closure that can be replayed."""

    def test_every_profile_snapshot_survives_a_round_trip(self) -> None:
        for name in NAMES:
            with self.subTest(profile=name):
                snapshot = profile(name).commit()
                self.assertEqual(loads(dumps(snapshot)), snapshot)

    def test_the_same_closure_always_writes_the_same_bytes(self) -> None:
        for name in NAMES:
            with self.subTest(profile=name):
                fixture = profile(name)
                self.assertEqual(dumps(fixture.commit()), dumps(fixture.commit()))


class ProfileShapeTests(unittest.TestCase):
    """The five §7 domains, each proving a different corner of the contract."""

    def test_the_logo_profile_shields_its_internals_behind_a_boundary(self) -> None:
        logo = profile("logo-web")
        interface = logo.definition.interfaces[0]
        self.assertEqual(interface.node_id, "treat.depth")
        self.assertEqual(
            [(item.external_port_id, item.direction.value) for item in interface.exports],
            [("in", "INPUT"), ("out", "OUTPUT")],
        )

    def test_the_logo_profile_delivers_under_a_quality_floor(self) -> None:
        logo = profile("logo-web")
        self.assertEqual(logo.definition.node("deliver.web").port("in").quality_gate, QualityClass.REVIEW)

    def test_the_game_profile_carries_material_rig_and_motion_through_typed_ports(self) -> None:
        game = profile("game-asset")
        self.assertTrue(
            {"material.pbr", "rig.skeleton", "animation.clip"}.issubset(set(game.semantic_types))
        )

    def test_the_film_profile_orders_two_plates_and_repairs_a_slice(self) -> None:
        film = profile("film-sequence")
        feeding = tuple(
            edge for edge in film.definition.edges if edge.target_node_id == "comp.plates"
        )
        self.assertEqual(sorted(edge.order for edge in feeding), [1, 2])
        self.assertEqual(film.definition.node("comp.plates").port("shots").cardinality, PortCardinality.MANY_ORDERED)
        graded = film.definition.edge_index["edge.grade"]
        self.assertEqual(graded.slice.axis, "shot")

    def test_the_spokesperson_profile_protects_two_identity_anchors(self) -> None:
        spokesperson = profile("spokesperson")
        self.assertEqual(
            [anchor.anchor_id for anchor in spokesperson.identity_anchors],
            [p.ANCHOR_FACE, p.ANCHOR_VOICE],
        )
        self.assertEqual(dict(spokesperson.selection.pairs)["axis.persona-face"], "keynote")

    def test_the_audio_profile_needs_no_visual_field_at_all(self) -> None:
        audio = profile("voice-music")
        self.assertEqual(set(audio.semantic_types) & VISUAL, set())
        self.assertEqual(audio.commit().snapshot_class, SnapshotClass.VALIDATED_SNAPSHOT)
        for node in audio.definition.nodes:
            for port in (*node.inputs, *node.outputs):
                self.assertNotIn("image", port.semantic_type.type_id)

    def test_all_five_profiles_share_one_contract_version(self) -> None:
        versions = {item.definition.contract_version for item in PROFILES.values()}
        self.assertEqual(len(versions), 1)


if __name__ == "__main__":
    unittest.main()
