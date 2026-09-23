from __future__ import annotations

import unittest
import uuid

from examples.m02_synthetic_profiles import ACTOR, AUDIO_PROFILE, LOGO_PROFILE
from iris_project_os.identity import EntityKind, ExternalRef
from iris_project_os.build import BuildPlan
from iris_project_os.release import ReleaseTransaction

from iris_production_state.enums import AvailabilityState, CleanupState, DeletionAuthorizationState, DeletionState, IndexState, ReproducibilityClass, RollbackState
from iris_production_state.errors import ProductionStateAdmissionError, ProductionStateIntegrityError
from iris_production_state.invariants import M06_INVARIANTS
from iris_production_state.lineage import (
    LineageEdge,
    LogicalRetirementReceipt,
    ProtectedClosureEvidence,
    RollbackPlan,
    RollbackReceipt,
    build_lineage_graph,
    evaluate_cleanup,
    record_deletion_authorization,
    record_deletion_completion,
    record_rollback,
    revalidate_deletion_authorization,
)
from iris_production_state.reconstruction import (
    DivergenceEvidence,
    ReconstructionManifest,
    ReconstructionMethod,
    ReproducibilityReceipt,
)
from iris_production_state.enums import DivergenceKind
from iris_production_state.release import ReleaseStateCapsule, validate_release_state_closure
from iris_production_state.revisions import AvailabilityReceipt

from m06_support import external, master_manifest, m02_build_plan, operational_revision


def _closures(*roots):
    categories = ("M02_HISTORY", "M05_IDENTITY", "REUSED_ANCESTRY", "RECONSTRUCTION", "RELEASE", "RETENTION")
    return tuple(ProtectedClosureEvidence(kind, tuple(roots) if kind == "M02_HISTORY" else (), external(f"closure-proof-{kind.lower()}")) for kind in categories)


def _complete_graph(graph_id, epoch, edges):
    return build_lineage_graph(graph_id, epoch, edges, state=IndexState.COMPLETE_FRESH, completeness_evidence_ref=external(f"closure-completeness-{graph_id}-{epoch}"))


class M06LineageReleaseTests(unittest.TestCase):
    def test_s05_rollback_cleanup_release_invariants(self) -> None:
        self.assertEqual(tuple(item.number for item in M06_INVARIANTS if item.section == "S05"), tuple(range(121, 151)))
        target = external("retained-target")
        graph = _complete_graph("lineage-s05", "epoch-s05", ())
        root = external("protected-root")
        result = evaluate_cleanup(target, (root,), graph, protected_closures=_closures(root), receipt_id="cleanup-s05", checked_at_ms=1)
        self.assertEqual(result.state, CleanupState.ELIGIBLE)

    def test_family_lrg(self) -> None:
        root = external("release-root")
        target = external("reused-ancestor")
        graph = _complete_graph("lineage-lrg", "epoch-1", (LineageEdge(root, target, "REUSED_ANCESTRY"),))
        result = evaluate_cleanup(target, (root,), graph, protected_closures=_closures(root), receipt_id="cleanup-lrg", checked_at_ms=1)
        self.assertEqual(result.state, CleanupState.REACHABLE)
        self.assertEqual(result.reachable_paths[0].refs, (root, target))
        stale = build_lineage_graph("lineage-lrg-stale", "epoch-2", (), state=IndexState.PARTIAL)
        self.assertEqual(evaluate_cleanup(target, (root,), stale, protected_closures=_closures(root), receipt_id="cleanup-stale", checked_at_ms=1).state, CleanupState.NOT_SAFE_TO_DELETE)

    def test_family_sgc(self) -> None:
        target = external("orphaned-media")
        root = external("active-release")
        graph = _complete_graph("lineage-sgc", "epoch-10", ())
        eligibility = evaluate_cleanup(target, (root,), graph, protected_closures=_closures(root), receipt_id="cleanup-proof", checked_at_ms=10)
        self.assertEqual(eligibility.state, CleanupState.ELIGIBLE)
        retirement = LogicalRetirementReceipt("retirement", target, eligibility, external("m02-retirement-authority"), 11)
        authorization = record_deletion_authorization(
            eligibility,
            retirement,
            authorization_id="deletion-auth",
            m55_authorization_ref=external("m55-delete-authorization"),
            current_policy_ref=external("current-policy"),
            authorized_at_ms=12,
        )
        revalidation = revalidate_deletion_authorization(
            authorization,
            graph,
            current_protected_closures=_closures(root),
            current_policy_ref=authorization.current_policy_ref,
            current_policy_authorized=True,
            receipt_id="deletion-revalidation",
            revalidated_at_ms=13,
        )
        self.assertEqual(revalidation.state, DeletionAuthorizationState.AUTHORIZED)
        completion = record_deletion_completion(
            authorization,
            revalidation,
            physical_result_ref=external("m55-delete-result"),
            success=True,
            completed_at_ms=14,
            receipt_id="delete-complete",
        )
        self.assertEqual(completion.state, DeletionState.COMPLETED)
        failed = record_deletion_completion(
            authorization,
            revalidation,
            physical_result_ref=external("m55-delete-failed"),
            success=False,
            completed_at_ms=15,
            receipt_id="delete-failed",
        )
        self.assertEqual(failed.state, DeletionState.FAILED)
        with self.assertRaises(ProductionStateAdmissionError):
            evaluate_cleanup(target, (root,), graph, protected_closures=(), receipt_id="missing-closure-proof", checked_at_ms=15)

    def test_family_rrb(self) -> None:
        current = LOGO_PROFILE.commit()
        target = LOGO_PROFILE.commit()
        previous = operational_revision("rollback-current")
        with self.assertRaises(ProductionStateIntegrityError):
            RollbackPlan(
                "rollback-cross-production",
                current,
                AUDIO_PROFILE.commit(),
                previous,
                ExternalRef(EntityKind.RECEIPT, "m02-rollback-cross-production", version="1"),
                ExternalRef(EntityKind.RIGHTS, "rights-current-cross", version="2"),
                ExternalRef(EntityKind.POLICY, "security-current-cross", version="5"),
                True,
                True,
                19,
            )
        plan = RollbackPlan(
            "rollback-plan",
            current,
            target,
            previous,
            ExternalRef(EntityKind.RECEIPT, "m02-rollback-ref", version="1"),
            ExternalRef(EntityKind.RIGHTS, "rights-current", version="2"),
            ExternalRef(EntityKind.POLICY, "security-current", version="5"),
            True,
            True,
            20,
        )
        expected = ReproducibilityClass.STOCHASTIC_REEXECUTABLE
        manifest = ReconstructionManifest("rollback-manifest", operational_revision("rollback-target"), ReconstructionMethod.ROLLBACK, (ExternalRef(EntityKind.SNAPSHOT, target.snapshot_id, version="1"),), "a" * 64, None, None, None, (), (), expected, None, None)
        divergence = DivergenceEvidence(DivergenceKind.SEMANTIC_DIVERGENCE, None, None, external("rollback-evidence"), "recovery is bounded by semantic evidence")
        reproducibility = ReproducibilityReceipt("rollback-repro", manifest, expected, operational_revision("rollback-new-history"), None, divergence, (external("rollback-run"),), 21, True, True, None)
        receipt = RollbackReceipt("rollback-result", plan, RollbackState.COMPLETE, reproducibility.output_revision_ref, reproducibility, None, 22)
        self.assertIs(record_rollback(receipt), receipt)
        self.assertNotEqual(receipt.resulting_revision_ref, previous)
        with self.assertRaises(ProductionStateIntegrityError):
            RollbackReceipt(
                "rollback-mismatched-proof",
                plan,
                RollbackState.COMPLETE,
                operational_revision("rollback-unproven-result"),
                reproducibility,
                None,
                22,
            )
        with self.assertRaises(ProductionStateAdmissionError):
            RollbackReceipt("rollback-blocked", plan, RollbackState.BLOCKED, None, None, None, 23)

    def test_family_rsc(self) -> None:
        candidate = LOGO_PROFILE.commit()
        release_snapshot = LOGO_PROFILE.commit()
        transaction = ReleaseTransaction(
            str(uuid.uuid5(uuid.NAMESPACE_URL, "iris-m06:release-m06")),
            LOGO_PROFILE.production_id,
            candidate.snapshot_id,
            release_snapshot.snapshot_id,
            ExternalRef(EntityKind.DESTINATION, "destination-test", version="1"),
            ACTOR,
            project_id=LOGO_PROFILE.project_id,
        )
        plan = BuildPlan(
            str(uuid.uuid5(uuid.NAMESPACE_URL, "iris-m06:release-build-plan")),
            release_snapshot.revision.graph_id,
            ExternalRef(EntityKind.REVISION, "release-base-revision", version="1"),
            ExternalRef(EntityKind.REVISION, release_snapshot.revision.revision_id, version="1"),
        )
        manifest, integrity = master_manifest(operational_revision("release-master"), master_id="release-master")
        availability = AvailabilityReceipt(
            manifest.materializations[0],
            AvailabilityState.KNOWN_AVAILABLE,
            integrity,
            30,
        )
        capsule = ReleaseStateCapsule(
            "release-capsule",
            transaction,
            release_snapshot,
            plan,
            manifest,
            "b" * 64,
            (integrity,),
            (availability,),
            (external("current-rights"), external("current-security"), external("quality-evidence")),
            "CLOSED",
            30,
        )
        self.assertIs(validate_release_state_closure(capsule), capsule)
        self.assertTrue(hasattr(transaction, "reference"))

        with self.assertRaises(ProductionStateAdmissionError):
            ReleaseStateCapsule(
                "release-missing-availability",
                transaction,
                release_snapshot,
                plan,
                manifest,
                "b" * 64,
                (integrity,),
                (),
                (external("current-rights"),),
                "CLOSED",
                31,
            )

        audio_snapshot = AUDIO_PROFILE.commit()
        cross_transaction = ReleaseTransaction(
            str(uuid.uuid5(uuid.NAMESPACE_URL, "iris-m06:release-cross-production")),
            LOGO_PROFILE.production_id,
            candidate.snapshot_id,
            audio_snapshot.snapshot_id,
            ExternalRef(EntityKind.DESTINATION, "destination-cross", version="1"),
            ACTOR,
            project_id=LOGO_PROFILE.project_id,
        )
        audio_plan = BuildPlan(
            str(uuid.uuid5(uuid.NAMESPACE_URL, "iris-m06:release-audio-plan")),
            audio_snapshot.revision.graph_id,
            ExternalRef(EntityKind.REVISION, "audio-base-revision", version="1"),
            ExternalRef(EntityKind.REVISION, audio_snapshot.revision.revision_id, version="1"),
        )
        with self.assertRaises(ProductionStateIntegrityError):
            ReleaseStateCapsule(
                "release-cross-production",
                cross_transaction,
                audio_snapshot,
                audio_plan,
                manifest,
                "b" * 64,
                (integrity,),
                (availability,),
                (external("current-rights"),),
                "CLOSED",
                32,
            )

    def test_family_cra(self) -> None:
        target = external("race-target")
        root = external("race-root")
        graph = _complete_graph("lineage-race", "epoch-before", ())
        eligibility = evaluate_cleanup(target, (root,), graph, protected_closures=_closures(root), receipt_id="race-eligibility", checked_at_ms=1)
        retirement = LogicalRetirementReceipt("race-retirement", target, eligibility, external("m02-retirement"), 2)
        authorization = record_deletion_authorization(
            eligibility,
            retirement,
            authorization_id="race-authorization",
            m55_authorization_ref=external("m55-auth"),
            current_policy_ref=external("policy-current"),
            authorized_at_ms=3,
        )
        changed = _complete_graph("lineage-race", "epoch-after", (LineageEdge(root, target, "RETENTION"),))
        stale = revalidate_deletion_authorization(
            authorization,
            changed,
            current_protected_closures=_closures(root),
            current_policy_ref=authorization.current_policy_ref,
            current_policy_authorized=True,
            receipt_id="race-revalidation-stale",
            revalidated_at_ms=4,
        )
        self.assertEqual(stale.state, DeletionAuthorizationState.STALE)
        revoked = revalidate_deletion_authorization(
            authorization,
            graph,
            current_protected_closures=_closures(root),
            current_policy_ref=authorization.current_policy_ref,
            current_policy_authorized=False,
            receipt_id="race-revalidation-revoked",
            revalidated_at_ms=4,
        )
        self.assertEqual(revoked.state, DeletionAuthorizationState.REVOKED)
        with self.assertRaises(ProductionStateAdmissionError):
            record_deletion_completion(
                authorization,
                stale,
                physical_result_ref=external("m55-stale-delete-result"),
                success=True,
                completed_at_ms=5,
                receipt_id="race-delete-blocked",
            )


if __name__ == "__main__":
    unittest.main()
