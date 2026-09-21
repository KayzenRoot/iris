"""Área E part 4: the archive contract, its integrity audits, its retention and its revival fork.

Three laws organize these tests, and each of them is the opposite of a shortcut an operator would
otherwise be free to take. A tier is an obligation checked against the refs a manifest actually
carries, so ``ARCHIVE_REPRODUCIBLE`` over a prerequisite with no archived bytes is refused instead
of being trusted (§31.18). Damage and cold are different answers: an object that came back with
other bytes is ``DAMAGED`` and stays damaged, while an object nobody could look at is ``UNKNOWN``,
which §22 forbids from reading as a pass (§31.21). And reopening buys availability — a restoration
that got the metadata back says nothing about a model version nobody still has, so
``fully_reproducible`` is refused at construction rather than being a field the caller may want
(§31.22). The revival tests then prove the lineage law: a reopening forks a new production and the
archived history is byte-for-byte what it was before the call (§31.23).

Nothing here names a path, a bucket or a folder, because invariant 24 says an archive is a
manifest/evidence contract. Every positive path is built from a real ``ProductionLedger`` and a real
committed ``Snapshot``, so the tier checks are reading evidence the promotion actually produced.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any

from iris_project_os.archive import (
    ArchiveLedger,
    ArchiveManifest,
    ArchiveObject,
    ArchiveRegistry,
    ArchiveRetention,
    ArchiveTier,
    AssetRole,
    AvailabilityRisk,
    CleanupDecision,
    CleanupPlan,
    DamageKind,
    IntegrityOutcome,
    ObjectProbe,
    ProbeState,
    RestorationReport,
    RevivalReceipt,
    RiskKind,
    StorageClass,
    audit_archive,
    restore_archive,
    revive_archive,
    seal_archive,
)
from iris_project_os.branching import PinReason, RetentionPin
from iris_project_os.errors import ArchiveError, SchemaValidationError, StoreConflictError
from iris_project_os.identity import EntityKind, ExternalRef, new_id
from iris_project_os.lifecycle import Phase, ProductionLedger, initial_vector
from iris_project_os.limits import MAX_REVIVAL_OBLIGATIONS
from iris_project_os.snapshots import SnapshotClass
from iris_project_os.versions import ComponentVersion
from tests import m02_kernel_support as k

ACTOR = ComponentVersion("m02.test", "1.0.0")
KEEPER = ComponentVersion("m02.archive", "1.0.0")
OTHER_KEEPER = ComponentVersion("m02.archive", "2.0.0")
NOW = 1_700_000_000_000


def ref(kind: EntityKind = EntityKind.RECEIPT) -> ExternalRef:
    return ExternalRef(kind=kind, reference=new_id())


def accepted(production_id: str) -> ProductionLedger:
    """A production standing at ACCEPTED, the only place an archive may be sealed from."""

    ledger = ProductionLedger(production_id, initial_vector(production_id))
    ledger.advance(actor=ACTOR, phase=Phase.PLANNED)
    ledger.advance(actor=ACTOR, phase=Phase.READY)
    ledger.advance(actor=ACTOR, phase=Phase.MATERIALIZED, candidate_snapshot_id=new_id())
    ledger.advance(actor=ACTOR, phase=Phase.VALIDATING, review="PENDING")
    ledger.advance(
        actor=ACTOR,
        phase=Phase.ACCEPTED,
        review="APPROVED",
        review_receipt=ref(),
        promotion_ref=ref(EntityKind.EVIDENCE),
    )
    return ledger


def archived(production_id: str, snapshot_id: str, *, phase: Any = Phase.ARCHIVED) -> ProductionLedger:
    """The same production carried past release into the phases §21 reopens from."""

    ledger = accepted(production_id)
    ledger.advance(
        actor=ACTOR,
        phase=Phase.RELEASED,
        release_snapshot_id=snapshot_id,
        promotion_ref=ref(EntityKind.EVIDENCE),
    )
    ledger.advance(
        actor=ACTOR,
        phase=Phase.SUPERSEDED,
        superseded_by_ref=ref(EntityKind.SUPERSESSION),
        replacement_ref=ref(EntityKind.SUPERSESSION),
    )
    if phase is Phase.ARCHIVED:
        ledger.advance(actor=ACTOR, phase=Phase.ARCHIVED)
    return ledger


class ArchiveTestCase(unittest.TestCase):
    """One accepted production, one committed snapshot, and the seal call with defaults in one place."""

    tier = ArchiveTier.ARCHIVE_REPRODUCIBLE

    def setUp(self) -> None:
        self.work = ref(EntityKind.ARTIFACT)
        self.recall_input = ref(EntityKind.TOOL)
        self.model = ref(EntityKind.MODEL)
        self.production_id = new_id()
        self.production = accepted(self.production_id)
        self.snapshot = k.snapshot(production_id=self.production_id)
        self.assets = (
            ArchiveObject(ref=self.work, digest=k.digest("final-master"), role=AssetRole.FINAL),
            ArchiveObject(
                ref=self.recall_input,
                digest=k.digest("cold-tool"),
                role=AssetRole.INPUT,
                storage=StorageClass.COLD,
            ),
        )

    def seal(
        self,
        tier: Any = None,
        *,
        production: ProductionLedger | None = None,
        snapshot: Any = None,
        assets: Any = None,
        prerequisites: Any = None,
        **over: Any,
    ) -> ArchiveManifest:
        over.setdefault("now_ms", NOW)
        return seal_archive(
            production if production is not None else self.production,
            snapshot if snapshot is not None else self.snapshot,
            tier=self.tier if tier is None else tier,
            actor=KEEPER,
            assets=self.assets if assets is None else assets,
            restoration_prerequisites=(
                (self.work, self.recall_input) if prerequisites is None else prerequisites
            ),
            **over,
        )

    def probes_for(self, manifest: ArchiveManifest, *, skip: Any = ()) -> tuple[ObjectProbe, ...]:
        """Say what an inspection could see about every reference the manifest stands for."""

        gone = {item.text if isinstance(item, ExternalRef) else item for item in skip}
        resolved: dict[str, ObjectProbe] = {}
        for item in manifest.required_refs():
            if item.text in gone:
                continue
            asset = manifest.object_for(item)
            if asset is not None:
                observed = asset.digest
            elif item.content_digest is not None:
                observed = item.content_digest
            else:
                observed = k.digest(item.text)
            resolved[item.text] = ObjectProbe(
                ref=item, state=ProbeState.PRESENT, observed_digest=observed, inspected_at_ms=NOW
            )
        return tuple(resolved.values())

    def sealed(self, **over: Any) -> tuple[ArchiveManifest, tuple[ObjectProbe, ...]]:
        manifest = self.seal(**over)
        return manifest, self.probes_for(manifest)


class TierObligationTests(ArchiveTestCase):
    """§31.18: a tier is a demand on the manifest, never a word typed into a field."""

    def test_a_reproducible_tier_demands_every_prerequisite_be_archived(self) -> None:
        with self.assertRaises(ArchiveError) as caught:
            self.seal(assets=(self.assets[0],))
        message = str(caught.exception)
        self.assertIn("restoration prerequisite", message)
        self.assertIn(self.recall_input.text, message)

    def test_a_light_archive_may_leave_recomputables_out(self) -> None:
        manifest = self.seal(
            ArchiveTier.ARCHIVE_LIGHT, assets=(self.assets[0],), prerequisites=(self.work, self.recall_input)
        )
        self.assertEqual(manifest.outstanding_prerequisites(), (self.recall_input,))
        self.assertFalse(manifest.tier.owes_asset_completeness)

    def test_no_tier_may_archive_the_metadata_and_leave_the_work(self) -> None:
        with self.assertRaises(ArchiveError) as caught:
            self.seal(ArchiveTier.ARCHIVE_LIGHT, assets=(self.assets[1],))
        self.assertIn("no final artifact", str(caught.exception))

    def test_the_provenance_and_quality_evidence_are_required_by_every_tier(self) -> None:
        manifest, _ = self.sealed()
        for field in ("provenance_refs", "quality_refs"):
            with self.subTest(field=field):
                with self.assertRaises(ArchiveError) as caught:
                    replace(manifest, **{field: ()})
                self.assertIn(manifest.archive_id, str(caught.exception))

    def test_a_legal_hold_that_cannot_name_its_right_is_only_a_label(self) -> None:
        manifest, _ = self.sealed()
        with self.assertRaises(ArchiveError) as caught:
            replace(manifest, tier=ArchiveTier.ARCHIVE_LEGAL_HOLD, rights_refs=())
        self.assertIn("names no right", str(caught.exception))

    def test_a_hold_tier_cannot_carry_an_expiry(self) -> None:
        for tier in (ArchiveTier.ARCHIVE_LEGAL_HOLD, ArchiveTier.ARCHIVE_GOLDEN):
            with self.subTest(tier=tier.value):
                with self.assertRaises(ArchiveError) as caught:
                    self.seal(tier, retention_expires_at_ms=NOW + 10)
                self.assertIn("retention expiry", str(caught.exception))

    def test_a_reproducible_archive_needs_a_closure_that_proves_what_it_claims(self) -> None:
        materialized = self.seal(ArchiveTier.ARCHIVE_LIGHT)
        self.assertEqual(materialized.tier, ArchiveTier.ARCHIVE_LIGHT)
        logical = k.snapshot(production_id=self.production_id, klass=SnapshotClass.LOGICAL_SNAPSHOT)
        with self.assertRaises(ArchiveError) as caught:
            self.seal(ArchiveTier.ARCHIVE_REPRODUCIBLE, snapshot=logical, prerequisites=(self.work,))
        self.assertIn("carries no validated closure", str(caught.exception))

    def test_a_snapshot_that_closes_over_nothing_material_cannot_be_archived(self) -> None:
        logical = k.snapshot(production_id=self.production_id, klass=SnapshotClass.LOGICAL_SNAPSHOT)
        with self.assertRaises(ArchiveError) as caught:
            self.seal(ArchiveTier.ARCHIVE_LIGHT, snapshot=logical, prerequisites=(self.work,))
        self.assertIn("nothing material", str(caught.exception))

    def test_what_has_not_been_accepted_has_no_canonical_state_to_archive(self) -> None:
        draft_id = new_id()
        draft = ProductionLedger(draft_id, initial_vector(draft_id))
        with self.assertRaises(ArchiveError) as caught:
            self.seal(production=draft, snapshot=k.snapshot(production_id=draft_id), prerequisites=(self.work,))
        self.assertIn("a backup, not an archive", str(caught.exception))

    def test_a_closure_belonging_to_another_production_cannot_be_sealed_here(self) -> None:
        other = k.snapshot(production_id=new_id())
        with self.assertRaises(ArchiveError) as caught:
            self.seal(snapshot=other)
        self.assertIn("cannot be archived as", str(caught.exception))

    def test_seal_archive_expects_the_ledger_that_owns_the_productions_state(self) -> None:
        with self.assertRaises(SchemaValidationError):
            seal_archive(
                self.production_id,
                self.snapshot,
                tier=self.tier,
                actor=KEEPER,
                assets=self.assets,
                now_ms=NOW,
            )

    def test_the_seal_takes_its_evidence_from_the_closure_rather_than_the_caller(self) -> None:
        manifest = self.seal(evidence_refs=(ref(EntityKind.EVIDENCE),))
        closure = self.snapshot.closure
        self.assertEqual(manifest.provenance_refs, closure.provenance_refs)
        self.assertEqual(manifest.rights_refs, closure.rights_refs)
        self.assertEqual(manifest.policy_refs, closure.policy_refs)
        self.assertEqual(manifest.quality_refs, closure.quality_decisions)
        self.assertEqual(manifest.graph_revision_id, closure.graph.revision.revision_id)
        self.assertEqual(manifest.intent_ref, closure.intent_ref)

    def test_the_canonical_snapshot_digest_is_sealed_into_the_reference(self) -> None:
        manifest = self.seal()
        self.assertEqual(manifest.snapshot_ref.kind, EntityKind.SNAPSHOT)
        self.assertEqual(manifest.snapshot_ref.content_digest, self.snapshot.digest)

    def test_the_snapshot_is_not_an_archived_object(self) -> None:
        pointer = ExternalRef(kind=EntityKind.SNAPSHOT, reference=self.snapshot.snapshot_id)
        with self.assertRaises(ArchiveError) as caught:
            ArchiveObject(ref=pointer, digest=k.digest("snapshot"))
        self.assertIn("belongs to the audit", str(caught.exception))

    def test_an_archive_cannot_disagree_with_itself_about_the_bytes(self) -> None:
        with self.assertRaises(ArchiveError) as caught:
            self.seal(
                assets=(
                    self.assets[0],
                    ArchiveObject(ref=self.work, digest=k.digest("other-master")),
                )
            )
        self.assertIn("cannot be audited", str(caught.exception))
        repeated = self.seal(
            assets=self.assets + (ArchiveObject(ref=self.work, digest=k.digest("final-master")),),
            prerequisites=(self.work,),
        )
        self.assertEqual([item.ref.text for item in repeated.assets], sorted([self.work.text, self.recall_input.text]))

    def test_a_pin_must_retain_something_this_archive_holds(self) -> None:
        unrelated = RetentionPin(pin_id=new_id(), target=ref(EntityKind.ARTIFACT), reasons=(PinReason.AUDIT,))
        with self.assertRaises(ArchiveError) as caught:
            self.seal(ArchiveTier.ARCHIVE_LIGHT, pins=(unrelated,))
        self.assertIn("does not hold", str(caught.exception))
        held = self.seal(ArchiveTier.ARCHIVE_LIGHT, pins=(replace(unrelated, target=self.work),))
        self.assertIn(ArchiveRetention.LIVE_PIN, held.retention(now_ms=NOW))

    def test_a_rights_block_names_the_right_rather_than_the_work_it_blocks(self) -> None:
        with self.assertRaises(ArchiveError) as caught:
            self.seal(ArchiveTier.ARCHIVE_LIGHT, risks=(AvailabilityRisk(kind=RiskKind.RIGHTS, subject=self.work),))
        self.assertIn("cannot be filed against", str(caught.exception))
        right = ref(EntityKind.RIGHTS)
        manifest = self.seal(ArchiveTier.ARCHIVE_LIGHT, risks=(AvailabilityRisk(kind=RiskKind.RIGHTS, subject=right),))
        self.assertEqual([item.subject for item in manifest.blocking_risks(for_use=True)], [right])
        self.assertEqual([item.subject for item in manifest.blocking_risks()], [])

    def test_a_model_version_risk_blocks_reproduction_and_reopens_the_revalidation_list(self) -> None:
        manifest = self.seal(ArchiveTier.ARCHIVE_LIGHT, risks=(AvailabilityRisk(RiskKind.MODEL_VERSION, self.model),))
        self.assertEqual([item.subject for item in manifest.blocking_risks()], [self.model])
        self.assertIn(self.model, manifest.revival_obligations())
        self.assertIn(self.model, manifest.required_refs())

    def test_required_refs_covers_everything_the_audit_must_be_able_to_reach(self) -> None:
        manifest = self.seal(release_refs=(ref(EntityKind.RELEASE),))
        required = {item.text for item in manifest.required_refs()}
        for item in (
            (manifest.snapshot_ref,)
            + manifest.assets_refs()
            + manifest.provenance_refs
            + manifest.quality_refs
            + manifest.rights_refs
            + manifest.policy_refs
            + manifest.restoration_prerequisites
        ):
            self.assertIn(item.text, required)
        self.assertNotIn(manifest.release_refs[0].text, required)


class IntegrityAuditTests(ArchiveTestCase):
    """§31.21 and §13: integrity compares the promise against what could actually be read."""

    def setUp(self) -> None:
        super().setUp()
        self.manifest, self.probes = self.sealed()

    def test_an_archive_where_it_promised_comes_back_intact(self) -> None:
        report = audit_archive(self.manifest, self.probes, inspector=KEEPER, now_ms=NOW)
        self.assertEqual(report.outcome, IntegrityOutcome.INTACT)
        self.assertTrue(report.is_clean)
        self.assertEqual(report.findings, ())
        self.assertEqual(report.archive_id, self.manifest.archive_id)

    def test_the_audit_cites_the_exact_manifest_bytes_it_read(self) -> None:
        report = audit_archive(self.manifest, self.probes, inspector=KEEPER, now_ms=NOW)
        self.assertEqual(report.manifest_digest, self.manifest.digest())

    def test_a_missing_object_is_reported_as_damage(self) -> None:
        report = audit_archive(
            self.manifest,
            self.probes_for(self.manifest, skip=(self.work,))
            + (ObjectProbe(ref=self.work, state=ProbeState.ABSENT, inspected_at_ms=NOW),),
            inspector=KEEPER,
            now_ms=NOW,
        )
        self.assertEqual(report.outcome, IntegrityOutcome.DAMAGED)
        self.assertEqual([item.kind for item in report.damaged], [DamageKind.MISSING_OBJECT])

    def test_bytes_that_no_longer_hash_to_the_promise_are_damage(self) -> None:
        tampered = tuple(
            item if item.ref.text != self.work.text else replace(item, observed_digest=k.digest("someone-else"))
            for item in self.probes
        )
        report = audit_archive(self.manifest, tampered, inspector=KEEPER, now_ms=NOW)
        self.assertEqual(report.outcome, IntegrityOutcome.DAMAGED)
        finding = next(item for item in report.damaged if item.subject.text == self.work.text)
        self.assertEqual(finding.kind, DamageKind.DIGEST_MISMATCH)
        self.assertFalse(report.is_clean)

    def test_a_rewritten_canonical_snapshot_is_caught_at_its_digest(self) -> None:
        tampered = tuple(
            item
            if item.ref.text != self.manifest.snapshot_ref.text
            else replace(item, observed_digest=k.digest("rewritten-closure"))
            for item in self.probes
        )
        report = audit_archive(self.manifest, tampered, inspector=KEEPER, now_ms=NOW)
        self.assertIn(DamageKind.DIGEST_MISMATCH, [item.kind for item in report.damaged])
        self.assertEqual(report.outcome, IntegrityOutcome.DAMAGED)

    def test_an_uninspectable_object_is_an_unknown_and_never_a_pass(self) -> None:
        cold = tuple(
            item
            if item.ref.text != self.recall_input.text
            else ObjectProbe(ref=self.recall_input, state=ProbeState.UNREADABLE, inspected_at_ms=NOW)
            for item in self.probes
        )
        report = audit_archive(self.manifest, cold, inspector=KEEPER, now_ms=NOW)
        self.assertEqual(report.outcome, IntegrityOutcome.UNKNOWN)
        self.assertFalse(report.is_clean)
        self.assertFalse(report.outcome.may_claim_complete)
        self.assertEqual([item.kind for item in report.unverified], [DamageKind.UNVERIFIABLE])
        self.assertEqual(report.damaged, ())

    def test_a_reference_that_is_gone_is_unreachable_evidence(self) -> None:
        cited = self.manifest.provenance_refs[0]
        probes = tuple(
            item
            if item.ref.text != cited.text
            else ObjectProbe(ref=cited, state=ProbeState.ABSENT, inspected_at_ms=NOW)
            for item in self.probes
        )
        report = audit_archive(self.manifest, probes, inspector=KEEPER, now_ms=NOW)
        self.assertEqual([item.kind for item in report.damaged], [DamageKind.UNREACHABLE_REFERENCE])

    def test_an_object_nobody_inspected_is_reported_rather_than_omitted(self) -> None:
        report = audit_archive(self.manifest, (), inspector=KEEPER, now_ms=NOW)
        self.assertEqual(report.outcome, IntegrityOutcome.UNKNOWN)
        self.assertEqual(len(report.findings), len(self.manifest.required_refs()))
        self.assertEqual({item.kind for item in report.findings}, {DamageKind.UNVERIFIABLE})

    def test_an_inspection_of_something_else_is_not_evidence_here(self) -> None:
        foreign = ObjectProbe(ref=ref(EntityKind.ARTIFACT), state=ProbeState.PRESENT, observed_digest=k.digest("x"))
        with self.assertRaises(ArchiveError) as caught:
            audit_archive(self.manifest, self.probes + (foreign,), inspector=KEEPER, now_ms=NOW)
        self.assertIn("not a reference this archive holds", str(caught.exception))

    def test_two_answers_about_one_object_are_not_averaged(self) -> None:
        gone = ObjectProbe(ref=self.work, state=ProbeState.ABSENT, inspected_at_ms=NOW)
        with self.assertRaises(ArchiveError) as caught:
            audit_archive(self.manifest, self.probes + (gone,), inspector=KEEPER, now_ms=NOW)
        self.assertIn("probed twice with two answers", str(caught.exception))
        repeated = audit_archive(self.manifest, self.probes + self.probes, inspector=KEEPER, now_ms=NOW)
        self.assertEqual(repeated.outcome, IntegrityOutcome.INTACT)

    def test_presence_must_be_checkable(self) -> None:
        with self.assertRaises(ArchiveError) as caught:
            ObjectProbe(ref=self.work, state=ProbeState.PRESENT)
        self.assertIn("silent success", str(caught.exception))
        with self.assertRaises(ArchiveError) as caught:
            ObjectProbe(ref=self.work, state=ProbeState.ABSENT, observed_digest=k.digest("nothing"))
        self.assertIn("no bytes to hash", str(caught.exception))

    def test_a_recorded_block_with_no_cited_evidence_is_a_finding(self) -> None:
        uncited = ref(EntityKind.RIGHTS)
        manifest = self.seal(ArchiveTier.ARCHIVE_LIGHT, risks=(AvailabilityRisk(RiskKind.RIGHTS, uncited),))
        report = audit_archive(manifest, self.probes_for(manifest), inspector=KEEPER, now_ms=NOW)
        self.assertEqual([item.kind for item in report.damaged], [DamageKind.UNCITED_BLOCK])
        self.assertEqual(report.outcome, IntegrityOutcome.DAMAGED)

    def test_a_block_the_archive_does_cite_comes_back_clean(self) -> None:
        right = self.manifest.rights_refs[0]
        manifest = self.seal(ArchiveTier.ARCHIVE_LIGHT, risks=(AvailabilityRisk(RiskKind.RIGHTS, right),))
        report = audit_archive(manifest, self.probes_for(manifest), inspector=KEEPER, now_ms=NOW)
        self.assertEqual(report.outcome, IntegrityOutcome.INTACT)

    def test_an_audit_is_idempotent_by_id_and_conflicting_when_reinterpreted(self) -> None:
        first = audit_archive(self.manifest, self.probes, inspector=KEEPER, now_ms=NOW, report_id=new_id())
        again = audit_archive(self.manifest, self.probes, inspector=KEEPER, now_ms=NOW, report_id=first.report_id)
        self.assertEqual(first, again)
        damaged = audit_archive(
            self.manifest,
            self.probes_for(self.manifest, skip=(self.work,))
            + (ObjectProbe(ref=self.work, state=ProbeState.ABSENT, inspected_at_ms=NOW),),
            inspector=KEEPER,
            now_ms=NOW,
            report_id=first.report_id,
        )
        self.assertNotEqual(damaged.outcome, first.outcome)
        ledger = ArchiveLedger(self.manifest, audits=(first,))
        with self.assertRaises(StoreConflictError):
            ledger.append_audit(damaged)

    def test_an_audit_refuses_a_manifest_it_cannot_describe(self) -> None:
        with self.assertRaises(SchemaValidationError):
            audit_archive(self.work, self.probes, inspector=KEEPER, now_ms=NOW)


class RestorationTests(ArchiveTestCase):
    """§31.22: reopening buys availability, and the reproducibility claim is checked not trusted."""

    def setUp(self) -> None:
        super().setUp()
        self.manifest, self.probes = self.sealed()

    def test_a_clean_reproducible_archive_restores_reproducibly(self) -> None:
        report = restore_archive(self.manifest, self.probes, actor=KEEPER, now_ms=NOW)
        self.assertTrue(report.usable)
        self.assertTrue(report.fully_reproducible)
        self.assertEqual([item.text for item in report.recalled], [self.recall_input.text])
        self.assertEqual(report.lost, ())

    def test_the_restoration_ran_the_audit_that_section_22_requires_on_access(self) -> None:
        report = restore_archive(self.manifest, self.probes, actor=KEEPER, now_ms=NOW)
        self.assertEqual(report.audit.manifest_digest, self.manifest.digest())
        self.assertEqual(report.audit.archive_id, self.manifest.archive_id)
        self.assertEqual(report.audit.outcome, IntegrityOutcome.INTACT)

    def test_cold_material_that_was_not_retrieved_ends_the_reproducibility_claim(self) -> None:
        probes = tuple(
            item
            if item.ref.text != self.recall_input.text
            else ObjectProbe(ref=self.recall_input, state=ProbeState.UNREADABLE, inspected_at_ms=NOW)
            for item in self.probes
        )
        report = restore_archive(self.manifest, probes, actor=KEEPER, now_ms=NOW)
        self.assertTrue(report.usable)
        self.assertFalse(report.fully_reproducible)
        self.assertEqual([item.text for item in report.not_recalled], [self.recall_input.text])
        self.assertEqual(report.recalled, ())
        self.assertTrue(report.metadata_available)
        self.assertFalse(report.materials_available)

    def test_an_object_nobody_looked_at_leaves_the_reproducibility_claim_unanswered(self) -> None:
        report = restore_archive(
            self.manifest, self.probes_for(self.manifest, skip=(self.recall_input,)), actor=KEEPER, now_ms=NOW
        )
        self.assertEqual(report.not_recalled, ())
        self.assertEqual(report.audit.outcome, IntegrityOutcome.UNKNOWN)
        self.assertFalse(report.fully_reproducible)

    def test_a_model_version_nobody_still_has_is_a_lost_object_not_a_pass(self) -> None:
        manifest = self.seal(
            ArchiveTier.ARCHIVE_GOLDEN,
            assets=self.assets + (ArchiveObject(ref=self.model, digest=k.digest("model"), role=AssetRole.INPUT),),
            prerequisites=(self.work, self.recall_input, self.model),
            risks=(AvailabilityRisk(RiskKind.MODEL_VERSION, self.model),),
        )
        probes = tuple(
            item
            if item.ref.text != self.model.text
            else ObjectProbe(ref=self.model, state=ProbeState.ABSENT, inspected_at_ms=NOW)
            for item in self.probes_for(manifest)
        )
        report = restore_archive(manifest, probes, actor=KEEPER, now_ms=NOW)
        self.assertFalse(report.fully_reproducible)
        self.assertEqual([item.text for item in report.lost], [self.model.text])
        self.assertEqual(report.audit.outcome, IntegrityOutcome.DAMAGED)

    def test_a_light_archive_never_claims_reproducibility_even_when_intact(self) -> None:
        manifest = self.seal(ArchiveTier.ARCHIVE_LIGHT, prerequisites=(self.work, self.recall_input, self.model))
        report = restore_archive(manifest, self.probes_for(manifest), actor=KEEPER, now_ms=NOW)
        self.assertTrue(report.usable)
        self.assertFalse(report.fully_reproducible)
        self.assertFalse(manifest.tier.owes_asset_completeness)

    def test_a_right_still_in_force_blocks_use_without_blocking_availability(self) -> None:
        right = self.manifest.rights_refs[0]
        manifest = self.seal(
            ArchiveTier.ARCHIVE_LEGAL_HOLD, risks=(AvailabilityRisk(RiskKind.RIGHTS, right, "hold in force"),)
        )
        report = restore_archive(manifest, self.probes_for(manifest), actor=KEEPER, now_ms=NOW)
        self.assertEqual([item.text for item in report.blocked_by_rights], [right.text])
        self.assertFalse(report.usable)
        self.assertTrue(report.metadata_available)
        self.assertTrue(report.materials_available)

    def test_damage_makes_the_material_unusable(self) -> None:
        probes = tuple(
            item
            if item.ref.text != self.work.text
            else replace(item, observed_digest=k.digest("replaced-bytes"))
            for item in self.probes
        )
        report = restore_archive(self.manifest, probes, actor=KEEPER, now_ms=NOW)
        self.assertFalse(report.usable)
        self.assertFalse(report.fully_reproducible)
        self.assertEqual(report.audit.outcome, IntegrityOutcome.DAMAGED)

    def test_no_hand_made_report_can_claim_reproducibility_over_a_dirty_audit(self) -> None:
        probes = tuple(
            item
            if item.ref.text != self.recall_input.text
            else ObjectProbe(ref=self.recall_input, state=ProbeState.UNREADABLE, inspected_at_ms=NOW)
            for item in self.probes
        )
        cold = restore_archive(self.manifest, probes, actor=KEEPER, now_ms=NOW)
        with self.assertRaises(ArchiveError) as caught:
            replace(cold, fully_reproducible=True)
        self.assertIn("came back UNKNOWN", str(caught.exception))

    def test_no_hand_made_report_can_claim_reproducibility_over_a_name_it_cannot_show(self) -> None:
        report = restore_archive(self.manifest, self.probes, actor=KEEPER, now_ms=NOW)
        self.assertTrue(report.fully_reproducible)
        for field in ("lost", "not_recalled"):
            with self.subTest(field=field):
                with self.assertRaises(ArchiveError) as caught:
                    replace(report, **{field: (self.model,)})
                self.assertIn("never retrieved", str(caught.exception))

    def test_no_hand_made_report_can_claim_usability_over_a_block(self) -> None:
        right = self.manifest.rights_refs[0]
        manifest = self.seal(ArchiveTier.ARCHIVE_LEGAL_HOLD, risks=(AvailabilityRisk(RiskKind.RIGHTS, right),))
        report = restore_archive(manifest, self.probes_for(manifest), actor=KEEPER, now_ms=NOW)
        with self.assertRaises(ArchiveError) as caught:
            replace(report, usable=True)
        self.assertIn("rights block", str(caught.exception))

    def test_a_restoration_cannot_be_two_answers_about_one_object(self) -> None:
        report = restore_archive(self.manifest, self.probes, actor=KEEPER, now_ms=NOW)
        with self.assertRaises(ArchiveError) as caught:
            replace(report, not_recalled=(self.recall_input,))
        self.assertIn("both recalled and unavailable", str(caught.exception))

    def test_an_audit_of_another_archive_cannot_certify_this_one(self) -> None:
        other = self.seal(assets=self.assets[:1], prerequisites=(self.work,))
        foreign = audit_archive(other, self.probes_for(other), inspector=KEEPER, now_ms=NOW)
        with self.assertRaises(ArchiveError) as caught:
            RestorationReport(
                restoration_id=new_id(),
                archive_id=self.manifest.archive_id,
                audit=foreign,
                actor=KEEPER,
                checked_at_ms=NOW,
            )
        self.assertIn("has to be about the thing being reopened", str(caught.exception))

    def test_a_restoration_reports_the_bools_it_was_given_or_refuses_them(self) -> None:
        report = restore_archive(self.manifest, self.probes, actor=KEEPER, now_ms=NOW)
        with self.assertRaises(SchemaValidationError):
            replace(report, usable="yes")


class ArchiveLedgerTests(ArchiveTestCase):
    """§13's archive/replay tampering, and §22's rule that a finding is not negotiable."""

    def setUp(self) -> None:
        super().setUp()
        self.manifest, self.probes = self.sealed()
        self.clean = audit_archive(self.manifest, self.probes, inspector=KEEPER, now_ms=NOW)
        self.damaged = audit_archive(
            self.manifest,
            self.probes_for(self.manifest, skip=(self.work,))
            + (ObjectProbe(ref=self.work, state=ProbeState.ABSENT, inspected_at_ms=NOW),),
            inspector=KEEPER,
            now_ms=NOW,
        )

    def test_an_unaudited_archive_is_not_verified(self) -> None:
        ledger = ArchiveLedger(self.manifest)
        self.assertEqual(ledger.condition, IntegrityOutcome.UNKNOWN)
        self.assertFalse(ledger.is_verified)

    def test_the_condition_follows_the_last_real_answer(self) -> None:
        ledger = ArchiveLedger(self.manifest)
        ledger.append_audit(self.clean)
        self.assertEqual(ledger.condition, IntegrityOutcome.INTACT)
        self.assertTrue(ledger.is_verified)
        self.assertIs(ledger.audits[0], self.clean)

    def test_recording_the_same_audit_twice_changes_nothing(self) -> None:
        ledger = ArchiveLedger(self.manifest, audits=(self.clean,))
        ledger.append_audit(self.clean)
        self.assertEqual(len(ledger.audits), 1)

    def test_damage_is_not_talked_back_into_intact(self) -> None:
        ledger = ArchiveLedger(self.manifest, audits=(self.damaged,))
        with self.assertRaises(ArchiveError) as caught:
            ledger.append_audit(self.clean)
        self.assertIn("already found damaged", str(caught.exception))
        self.assertEqual(ledger.condition, IntegrityOutcome.DAMAGED)

    def test_a_later_full_inspection_answers_an_earlier_unknown(self) -> None:
        cold = audit_archive(
            self.manifest, self.probes_for(self.manifest, skip=(self.recall_input,)), inspector=KEEPER, now_ms=NOW
        )
        ledger = ArchiveLedger(self.manifest, audits=(cold,))
        self.assertEqual(ledger.condition, IntegrityOutcome.UNKNOWN)
        self.assertFalse(ledger.is_verified)
        ledger.append_audit(self.clean)
        self.assertEqual(ledger.condition, IntegrityOutcome.INTACT)
        self.assertTrue(ledger.is_verified)
        self.assertEqual(len(ledger.replay()), 2)

    def test_an_audit_of_rewritten_manifest_bytes_is_refused(self) -> None:
        rewritten = self.seal(assets=self.assets + (ArchiveObject(ref=self.model, digest=k.digest("m")),))
        report = audit_archive(rewritten, self.probes_for(rewritten), inspector=KEEPER, now_ms=NOW)
        ledger = ArchiveLedger(self.manifest)
        with self.assertRaises(ArchiveError) as caught:
            ledger.append_audit(replace(report, archive_id=ledger.archive_id))
        self.assertIn("were rewritten", str(caught.exception))

    def test_a_replacement_is_sealed_as_a_new_archive_that_supersedes_this_one(self) -> None:
        ledger = ArchiveLedger(self.manifest, audits=(self.damaged,))
        replacement = self.seal(assets=self.assets + (ArchiveObject(ref=self.model, digest=k.digest("m")),))
        self.assertNotEqual(replacement.digest(), self.manifest.digest())
        self.assertEqual(ArchiveLedger(replacement).condition, IntegrityOutcome.UNKNOWN)
        self.assertEqual(len(ledger.audits), 1)

    def test_one_audit_id_cannot_carry_two_conclusions(self) -> None:
        second = replace(self.clean, findings=self.damaged.findings)
        ledger = ArchiveLedger(self.manifest, audits=(self.clean,))
        with self.assertRaises(StoreConflictError):
            ledger.append_audit(second)

    def test_a_foreign_report_cannot_be_recorded_here(self) -> None:
        other = self.seal(assets=self.assets[:1], prerequisites=(self.work,))
        foreign = audit_archive(other, self.probes_for(other), inspector=KEEPER, now_ms=NOW)
        ledger = ArchiveLedger(self.manifest)
        with self.assertRaises(ArchiveError) as caught:
            ledger.append_audit(foreign)
        self.assertIn("cannot be recorded on the ledger", str(caught.exception))
        with self.assertRaises(ArchiveError):
            ledger.record_restoration(
                restore_archive(other, self.probes_for(other), actor=KEEPER, now_ms=NOW)
            )

    def test_a_restoration_bringing_its_own_audit_needs_no_second_call(self) -> None:
        report = restore_archive(self.manifest, self.probes, actor=KEEPER, now_ms=NOW)
        ledger = ArchiveLedger(self.manifest)
        ledger.record_restoration(report)
        self.assertEqual(len(ledger.restorations), 1)
        self.assertEqual(len(ledger.audits), 1)
        self.assertTrue(ledger.is_verified)
        ledger.record_restoration(report)
        self.assertEqual(len(ledger.restorations), 1)

    def test_an_open_finding_keeps_the_archive_out_of_cleanup(self) -> None:
        ledger = ArchiveLedger(self.manifest, audits=(self.damaged,))
        self.assertIn(ArchiveRetention.OPEN_INTEGRITY_FINDING, ledger.retention_reasons(now_ms=NOW))
        self.assertFalse(ledger.may_collect(now_ms=NOW))

    def test_a_clean_light_archive_is_the_one_case_gc_may_collect(self) -> None:
        manifest = self.seal(ArchiveTier.ARCHIVE_LIGHT, prerequisites=(self.work,))
        ledger = ArchiveLedger(manifest)
        ledger.append_audit(audit_archive(manifest, self.probes_for(manifest), inspector=KEEPER, now_ms=NOW))
        self.assertTrue(ledger.may_collect(now_ms=NOW))

    def test_replay_returns_the_history_in_the_order_it_happened(self) -> None:
        first = replace(self.clean, report_id=new_id())
        second = replace(self.clean, report_id=new_id(), checked_at_ms=NOW + 1)
        ledger = ArchiveLedger(self.manifest, audits=(first, second))
        self.assertEqual([item.report_id for item in ledger.replay()], [first.report_id, second.report_id])


class RetentionAndGcTests(ArchiveTestCase):
    """§31.19 and §31.20: holds override collection, and the plan has to say why."""

    def test_a_legal_hold_overrides_ordinary_collection(self) -> None:
        manifest = self.seal(ArchiveTier.ARCHIVE_LEGAL_HOLD)
        self.assertEqual(manifest.retention(now_ms=NOW), (ArchiveRetention.TIER_LEGAL_HOLD,))
        self.assertFalse(manifest.may_collect(now_ms=NOW))
        self.assertFalse(manifest.may_collect(now_ms=NOW + 10_000_000))

    def test_golden_material_stays_pinned_for_benchmark_use(self) -> None:
        manifest = self.seal(
            ArchiveTier.ARCHIVE_GOLDEN,
            pins=(RetentionPin(pin_id=new_id(), target=self.work, reasons=(PinReason.BENCHMARK,)),),
        )
        self.assertEqual(
            manifest.retention(now_ms=NOW),
            (ArchiveRetention.LIVE_PIN, ArchiveRetention.TIER_GOLDEN),
        )

    def test_a_retention_expiry_holds_until_it_passes(self) -> None:
        manifest = self.seal(ArchiveTier.ARCHIVE_LIGHT, retention_expires_at_ms=NOW + 1000)
        self.assertEqual(manifest.retention(now_ms=NOW), (ArchiveRetention.RETENTION_NOT_EXPIRED,))
        self.assertFalse(manifest.may_collect(now_ms=NOW))
        self.assertTrue(manifest.may_collect(now_ms=NOW + 1001))

    def test_an_expiry_cannot_predate_the_seal(self) -> None:
        with self.assertRaises(ArchiveError):
            self.seal(ArchiveTier.ARCHIVE_LIGHT, retention_expires_at_ms=NOW - 1)

    def test_an_audit_pin_never_releases_and_a_ttl_pin_does(self) -> None:
        audit_pin = RetentionPin(pin_id=new_id(), target=self.work, reasons=(PinReason.AUDIT,), created_at_ms=NOW)
        ttl_pin = RetentionPin(
            pin_id=new_id(),
            target=self.work,
            reasons=(PinReason.RETENTION_TTL,),
            created_at_ms=NOW,
            expires_at_ms=NOW + 100,
        )
        held = self.seal(ArchiveTier.ARCHIVE_LIGHT, pins=(audit_pin,))
        expiring = self.seal(ArchiveTier.ARCHIVE_LIGHT, pins=(ttl_pin,))
        self.assertIn(ArchiveRetention.LIVE_PIN, held.retention(now_ms=NOW + 10_000))
        self.assertEqual(expiring.retention(now_ms=NOW + 10_000), ())
        self.assertEqual(expiring.retention(now_ms=NOW), (ArchiveRetention.LIVE_PIN,))

    def test_the_plan_holds_the_gated_archives_and_lists_the_rest(self) -> None:
        light = self.seal(ArchiveTier.ARCHIVE_LIGHT, assets=self.assets[:1], prerequisites=(self.work,))
        golden = self.seal(ArchiveTier.ARCHIVE_GOLDEN, assets=self.assets[:1], prerequisites=(self.work,))
        registry = ArchiveRegistry((light, golden))
        plan = registry.plan_cleanup(now_ms=NOW)
        self.assertEqual(plan.collectable, (light.archive_id,))
        self.assertEqual(plan.holds, (golden.archive_id,))
        self.assertEqual(plan.reason_for(golden.archive_id), (ArchiveRetention.TIER_GOLDEN,))
        self.assertEqual(registry.collectable(now_ms=NOW), (light.archive_id,))

    def test_a_held_light_archive_becomes_collectable_once_its_ttl_passes(self) -> None:
        light = self.seal(ArchiveTier.ARCHIVE_LIGHT, prerequisites=(self.work,), retention_expires_at_ms=NOW + 500)
        registry = ArchiveRegistry((light,))
        self.assertEqual(registry.collectable(now_ms=NOW), ())
        self.assertEqual(registry.collectable(now_ms=NOW + 501), (light.archive_id,))

    def test_a_plan_cannot_hold_and_collect_the_same_archive(self) -> None:
        manifest = self.seal(ArchiveTier.ARCHIVE_LIGHT, prerequisites=(self.work,))
        with self.assertRaises(ArchiveError) as caught:
            CleanupPlan(
                kept=(CleanupDecision(archive_id=manifest.archive_id, reasons=(ArchiveRetention.TIER_GOLDEN,)),),
                collectable=(manifest.archive_id,),
            )
        self.assertIn("not a plan", str(caught.exception))

    def test_a_decision_with_no_reason_is_a_collectable_with_its_own_list(self) -> None:
        with self.assertRaises(ArchiveError):
            CleanupDecision(archive_id=new_id())

    def test_sealing_the_same_archive_twice_is_a_no_op(self) -> None:
        registry = ArchiveRegistry()
        first = registry.seal(self.seal())
        self.assertIs(registry.seal(first.manifest), first)
        self.assertIs(registry.seal(first), first)
        self.assertEqual(len(registry.known), 1)

    def test_a_second_content_under_one_archive_id_is_refused(self) -> None:
        registry = ArchiveRegistry()
        original = self.seal()
        registry.seal(original)
        with self.assertRaises(StoreConflictError) as caught:
            registry.seal(
                self.seal(
                    archive_id=original.archive_id,
                    assets=original.assets + (ArchiveObject(ref=self.model, digest=k.digest("m")),),
                )
            )
        self.assertIn("supersede the old one", str(caught.exception))

    def test_the_registry_answers_for_a_production_and_for_a_snapshot(self) -> None:
        registry = ArchiveRegistry()
        ledger = registry.seal(self.seal())
        self.assertEqual([item.archive_id for item in registry.for_production(self.production_id)], [ledger.archive_id])
        self.assertTrue(registry.holds_snapshot(self.snapshot))
        self.assertTrue(registry.holds_snapshot(ledger.manifest.snapshot_ref))
        self.assertFalse(registry.holds_snapshot(ref(EntityKind.SNAPSHOT)))
        self.assertEqual(registry.for_production(new_id()), ())
        with self.assertRaises(ArchiveError):
            registry.get(new_id())
        with self.assertRaises(ArchiveError) as caught:
            registry.holds_snapshot(self.work)
        self.assertIn("no archive closes over it", str(caught.exception))


class RevivalTests(ArchiveTestCase):
    """§31.23: a reopening forks new lineage, owes a revalidation list, and edits nothing."""

    def setUp(self) -> None:
        super().setUp()
        self.manifest = self.seal()
        self.archived = archived(self.production_id, self.snapshot.snapshot_id)
        self.probes = self.probes_for(self.manifest)

    def revive(self, **over: Any) -> tuple[RevivalReceipt, ProductionLedger]:
        over.setdefault("revived_production_id", new_id())
        over.setdefault("revived_branch_id", new_id())
        over.setdefault("actor", KEEPER)
        over.setdefault("now_ms", NOW)
        return revive_archive(self.manifest, self.archived, **over)

    def test_reopening_forks_a_lineage_and_leaves_history_alone(self) -> None:
        before = list(self.archived.history)
        receipt, revived = self.revive()
        self.assertEqual(self.archived.current.phase, Phase.ARCHIVED)
        self.assertEqual(list(self.archived.history), before)
        self.assertNotEqual(receipt.revived_production_id, self.archived.production_id)
        self.assertEqual(receipt.source_production_id, self.archived.production_id)
        self.assertEqual(revived.production_id, receipt.revived_production_id)

    def test_the_revived_lineage_starts_at_draft_and_rewalks(self) -> None:
        _, revived = self.revive()
        self.assertEqual(revived.current.phase, Phase.DRAFT)
        self.assertEqual(len(revived), 0)
        revived.advance(actor=ACTOR, phase=Phase.PLANNED)
        self.assertEqual(revived.current.phase, Phase.PLANNED)

    def test_a_superseded_production_may_reopen_too(self) -> None:
        superseded = archived(self.production_id, self.snapshot.snapshot_id, phase=Phase.SUPERSEDED)
        receipt, _ = revive_archive(
            self.manifest, superseded, revived_production_id=new_id(), revived_branch_id=new_id(), actor=KEEPER
        )
        self.assertEqual(receipt.source_production_id, superseded.production_id)
        self.assertEqual(superseded.current.phase, Phase.SUPERSEDED)

    def test_a_live_production_is_a_branch_not_a_revival(self) -> None:
        with self.assertRaises(ArchiveError) as caught:
            revive_archive(
                self.manifest,
                self.production,
                revived_production_id=new_id(),
                revived_branch_id=new_id(),
                actor=KEEPER,
            )
        self.assertIn("forking a live one is a normal branch", str(caught.exception))

    def test_another_productions_archive_cannot_be_revived_here(self) -> None:
        stranger = archived(new_id(), self.snapshot.snapshot_id)
        with self.assertRaises(ArchiveError) as caught:
            revive_archive(
                self.manifest, stranger, revived_production_id=new_id(), revived_branch_id=new_id(), actor=KEEPER
            )
        self.assertIn("cannot be revived as", str(caught.exception))

    def test_a_revival_owes_the_exact_revalidation_list(self) -> None:
        receipt, _ = self.revive()
        self.assertEqual(receipt.obligations, self.manifest.revival_obligations())
        self.assertEqual(receipt.outstanding, receipt.obligations)
        self.assertFalse(receipt.may_activate)

    def test_a_fully_revalidated_revival_may_activate(self) -> None:
        receipt, _ = self.revive(revalidated=self.manifest.revival_obligations())
        self.assertEqual(receipt.outstanding, ())
        self.assertTrue(receipt.may_activate)

    def test_partial_revalidation_leaves_the_rest_outstanding(self) -> None:
        obligations = self.manifest.revival_obligations()
        receipt, _ = self.revive(revalidated=obligations[:1])
        self.assertEqual(receipt.outstanding, obligations[1:])
        self.assertFalse(receipt.may_activate)

    def test_revalidating_something_the_archive_never_owed_is_refused(self) -> None:
        with self.assertRaises(ArchiveError) as caught:
            self.revive(revalidated=(ref(EntityKind.TOOL),))
        self.assertIn("never owed", str(caught.exception))

    def test_reviving_into_the_archived_id_rewrites_the_history_it_claims_to_leave(self) -> None:
        with self.assertRaises(ArchiveError) as caught:
            self.revive(revived_production_id=self.archived.production_id)
        self.assertIn("into itself", str(caught.exception))
        with self.assertRaises(ArchiveError):
            RevivalReceipt(
                revival_id=new_id(),
                archive_id=self.manifest.archive_id,
                source_production_id=self.production_id,
                source_snapshot_ref=self.manifest.snapshot_ref,
                revived_production_id=self.production_id,
                revived_branch_id=new_id(),
            )

    def test_a_revival_must_name_the_exact_snapshot_it_forks_from(self) -> None:
        receipt, _ = self.revive()
        self.assertEqual(receipt.source_snapshot_ref, self.manifest.snapshot_ref)
        self.assertEqual(receipt.source_snapshot_ref.content_digest, self.snapshot.digest)
        with self.assertRaises(ArchiveError):
            replace(receipt, source_snapshot_ref=ref(EntityKind.ARTIFACT))

    def test_a_revival_from_another_point_is_a_different_archives_work(self) -> None:
        receipt, _ = self.revive()
        twin = self.seal(snapshot=k.snapshot(production_id=self.production_id), archive_id=self.manifest.archive_id)
        other = ArchiveLedger(twin)
        with self.assertRaises(ArchiveError) as caught:
            other.record_revival(receipt)
        self.assertIn("different archive's work", str(caught.exception))
        self.assertEqual(other.retention_reasons(now_ms=NOW), ())
        self.assertEqual(ArchiveLedger(self.manifest).record_revival(receipt), receipt)

    def test_a_cited_archive_is_held_from_collection(self) -> None:
        receipt, _ = self.revive()
        ledger = ArchiveLedger(self.manifest)
        ledger.record_revival(receipt)
        ledger.record_revival(receipt)
        self.assertEqual(len(ledger.revivals), 1)
        self.assertIn(ArchiveRetention.CITED_BY_REVIVAL, ledger.retention_reasons(now_ms=NOW))
        self.assertFalse(ledger.may_collect(now_ms=NOW))
        with self.assertRaises(StoreConflictError):
            ledger.record_revival(replace(receipt, revived_branch_id=new_id()))

    def test_a_revival_with_too_little_rechecked_is_a_new_production(self) -> None:
        obligations = tuple(ref(EntityKind.TOOL) for _ in range(MAX_REVIVAL_OBLIGATIONS + 1))
        with self.assertRaises(ArchiveError) as caught:
            RevivalReceipt(
                revival_id=new_id(),
                archive_id=self.manifest.archive_id,
                source_production_id=self.production_id,
                source_snapshot_ref=self.manifest.snapshot_ref,
                revived_production_id=new_id(),
                revived_branch_id=new_id(),
                obligations=obligations,
            )
        self.assertIn("outstanding", str(caught.exception))

    def test_revive_archive_expects_the_ledger_rather_than_an_id(self) -> None:
        with self.assertRaises(SchemaValidationError):
            revive_archive(
                self.manifest,
                self.production_id,
                revived_production_id=new_id(),
                revived_branch_id=new_id(),
                actor=KEEPER,
            )


class ArchiveDomainNeutralityTests(ArchiveTestCase):
    """§12: the archive contract must not quietly become a storage layer or a vendor binding."""

    def test_no_archive_type_names_a_path_or_a_vendor(self) -> None:
        import inspect

        import iris_project_os.archive as module

        source = inspect.getsource(module)
        for banned in ("import os", "pathlib", "open(", "boto", "s3://", "subprocess", "requests"):
            self.assertNotIn(banned, source)
        self.assertEqual(module.__package__, "iris_project_os")

    def test_an_archive_manifest_survives_a_payload_round_trip(self) -> None:
        manifest = self.seal()
        rebuilt = ArchiveManifest.from_payload(manifest.to_payload())
        self.assertEqual(rebuilt, manifest)
        self.assertEqual(rebuilt.digest(), manifest.digest())
        for report in (
            audit_archive(manifest, self.probes_for(manifest), inspector=KEEPER, now_ms=NOW),
        ):
            self.assertEqual(type(report).from_payload(report.to_payload()), report)
        restoration = restore_archive(manifest, self.probes_for(manifest), actor=KEEPER, now_ms=NOW)
        self.assertEqual(RestorationReport.from_payload(restoration.to_payload()), restoration)

    def test_the_archive_kind_is_an_identity_the_kernel_already_knows(self) -> None:
        manifest = self.seal()
        self.assertEqual(manifest.reference.kind, EntityKind.ARCHIVE)
        self.assertEqual(EntityKind.parse("ARCHIVE"), EntityKind.ARCHIVE)
