from __future__ import annotations

import unittest

from iris_production_state.dependencies import FingerprintDimension, build_fingerprint
from iris_production_state.enums import EquivalenceState, FingerprintScope, WorkDisposition
from iris_production_state.errors import ProductionStateAdmissionError, ProductionStateIntegrityError
from iris_production_state.invariants import M06_INVARIANTS
from iris_production_state.regeneration import (
    RebuildBoundary,
    ReuseEvidenceDimension,
    ReuseEvidenceState,
    ReuseProof,
    VerificationReceipt,
    WorkFrontier,
    MixedReconstructionReceipt,
    admit_mixed_reconstruction,
    admit_reuse,
    decide_work,
    expand_frontier,
)

from m06_support import content_digest, external, m02_build_plan, m02_repair_build_plan, m02_reuse_build_plan, materialization, operational_revision


def _reuse_proof(revision_id: str = "reuse-candidate") -> ReuseProof:
    revision = operational_revision(revision_id)
    dimension = FingerprintDimension(external(f"dependency-{revision_id}"), "pixels", "MATERIAL", content_digest())
    fingerprint = build_fingerprint((dimension,), FingerprintScope.FULL_CAUSAL)
    build_plan = m02_reuse_build_plan(f"build-{revision_id}", node_id="render.logo")
    material = materialization(revision, f"mat-{revision_id}", b"bytes.render.logo")
    return ReuseProof(
        revision,
        material,
        fingerprint,
        build_plan,
        "render.logo",
        (ReuseEvidenceDimension(dimension.key, ReuseEvidenceState.VERIFIED, external(f"proof-{revision_id}")),),
    )


class M06RegenerationTests(unittest.TestCase):
    def test_s03_selective_rebuild_invariants(self) -> None:
        self.assertEqual(tuple(item.number for item in M06_INVARIANTS if item.section == "S03"), tuple(range(61, 91)))
        proof = _reuse_proof("section-s03")
        receipt = admit_reuse(proof, receipt_id="reuse-s03", decision_id="decision-s03", admitted_at_ms=1)
        self.assertEqual(receipt.equivalence, EquivalenceState.PROVEN)

    def test_family_sre(self) -> None:
        receipt = admit_reuse(_reuse_proof("sre"), receipt_id="reuse-sre", decision_id="decision-sre", admitted_at_ms=1)
        self.assertEqual(
            decide_work(WorkDisposition.REUSE_EXACT, decision_id="decision-sre", reuse_receipt=receipt),
            WorkDisposition.REUSE_EXACT,
        )
        self.assertEqual(decide_work(WorkDisposition.REUSE_EXACT, reuse_receipt=receipt), WorkDisposition.BLOCKED)
        self.assertEqual(
            decide_work(WorkDisposition.REUSE_EXACT, decision_id="different-decision", reuse_receipt=receipt),
            WorkDisposition.BLOCKED,
        )
        self.assertEqual(decide_work(WorkDisposition.REUSE_EXACT), WorkDisposition.BLOCKED)
        with self.assertRaises(ProductionStateAdmissionError):
            decide_work(WorkDisposition.NO_WORK_PROVEN)

    def test_family_rap(self) -> None:
        proof = _reuse_proof("rap")
        with self.assertRaises(ProductionStateAdmissionError):
            admit_reuse(
                ReuseProof(**{**proof.__dict__, "cache_hit_only": True}),
                receipt_id="cache-only",
                decision_id="decision-cache-only",
                admitted_at_ms=1,
            )
        with self.assertRaises(ProductionStateAdmissionError):
            admit_reuse(
                ReuseProof(**{**proof.__dict__, "digest_only": True}),
                receipt_id="digest-only",
                decision_id="decision-digest-only",
                admitted_at_ms=1,
            )
        stale_dim = ReuseEvidenceDimension("current-policy", ReuseEvidenceState.STALE, external("old-policy"))
        stale = ReuseProof(
            proof.candidate_revision_ref,
            proof.candidate_materialization_ref,
            proof.dependency_fingerprint,
            proof.m02_build_ref,
            proof.m02_node_id,
            (proof.dimensions[0], stale_dim),
        )
        with self.assertRaises(ProductionStateAdmissionError):
            admit_reuse(stale, receipt_id="stale", decision_id="decision-stale", admitted_at_ms=2)

    def test_family_fex(self) -> None:
        plan = m02_build_plan("build-frontier")
        one = operational_revision("frontier-one")
        two = operational_revision("frontier-two")
        previous = WorkFrontier("decision-frontier", (one,), (), (), 1, WorkDisposition.REBUILD_FULL_TARGET, plan)
        expanded = WorkFrontier("decision-frontier", (one,), (two,), ("new-hidden-edge",), 2, WorkDisposition.REBUILD_FULL_TARGET, plan)
        self.assertIs(expand_frontier(previous, expanded), expanded)
        with self.assertRaises(ProductionStateIntegrityError):
            expand_frontier(expanded, previous)
        less_conservative = WorkFrontier("decision-frontier", (one,), (two,), (), 3, WorkDisposition.NO_WORK_PROVEN, plan)
        with self.assertRaises(ProductionStateAdmissionError):
            expand_frontier(expanded, less_conservative)
        partial = WorkFrontier("decision-frontier", (one,), (two,), (), 3, WorkDisposition.REBUILD_PARTIAL, plan)
        with self.assertRaises(ProductionStateAdmissionError):
            expand_frontier(expanded, partial)

    def test_family_mxr(self) -> None:
        reused_proof = _reuse_proof("mxr-reused")
        reuse_receipt = admit_reuse(reused_proof, receipt_id="reuse-mxr", decision_id="decision-mxr", admitted_at_ms=1)
        repair_plan = m02_repair_build_plan("build-mxr", node_id="node-mxr", axis="segment", values=("video.segment.4",))
        boundary = RebuildBoundary(
            "boundary-mxr",
            repair_plan,
            "node-mxr",
            repair_plan.steps[0].slice,
            ("segment:video.segment.4",),
            "segment-recompose",
            "2.0.0",
            external("identity-protection"),
            external("quality-obligation"),
        )
        receipt = MixedReconstructionReceipt(
            "mixed-mxr",
            operational_revision("mxr-target"),
            (operational_revision("mxr-rebuilt"),),
            (reused_proof.candidate_revision_ref,),
            (reuse_receipt,),
            boundary,
            "2.0.0",
            boundary.protected_identity_ref,
            boundary.protected_quality_ref,
            10,
        )
        self.assertIs(admit_mixed_reconstruction(receipt), receipt)
        self.assertEqual(decide_work(WorkDisposition.REBUILD_PARTIAL, boundary=boundary), WorkDisposition.REBUILD_PARTIAL)
        self.assertEqual(decide_work(WorkDisposition.REBUILD_PARTIAL), WorkDisposition.REBUILD_FULL_TARGET)
        self.assertEqual(
            decide_work(
                WorkDisposition.REUSE_WITH_VERIFICATION,
                decision_id="decision-mxr",
                reuse_receipt=reuse_receipt,
            ),
            WorkDisposition.VERIFY_ONLY,
        )
        unrelated_verification = VerificationReceipt(
            "verification-unrelated",
            operational_revision("verification-other-subject"),
            EquivalenceState.PROVEN,
            external("verification-unrelated-evidence"),
            2,
        )
        self.assertEqual(
            decide_work(
                WorkDisposition.REUSE_WITH_VERIFICATION,
                decision_id="decision-mxr",
                reuse_receipt=reuse_receipt,
                verification=unrelated_verification,
            ),
            WorkDisposition.VERIFY_ONLY,
        )
        matching_verification = VerificationReceipt(
            "verification-mxr",
            reuse_receipt.candidate_materialization_ref,
            EquivalenceState.PROVEN,
            external("verification-mxr-evidence"),
            3,
        )
        self.assertEqual(
            decide_work(
                WorkDisposition.REUSE_WITH_VERIFICATION,
                decision_id="decision-mxr",
                reuse_receipt=reuse_receipt,
                verification=matching_verification,
            ),
            WorkDisposition.REUSE_WITH_VERIFICATION,
        )


if __name__ == "__main__":
    unittest.main()
