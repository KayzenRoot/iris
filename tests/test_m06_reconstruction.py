from __future__ import annotations

import unittest
from dataclasses import replace

from iris_production_state.enums import DivergenceKind, ReproducibilityClass
from iris_production_state.errors import ProductionStateAdmissionError, ProductionStateIntegrityError
from iris_production_state.invariants import M06_INVARIANTS
from iris_production_state.reconstruction import (
    DivergenceEvidence,
    HistoricalPermissionEvidence,
    ReconstructionManifest,
    ReconstructionMethod,
    ReproducibilityReceipt,
    require_bounded_reproducibility,
    validate_historical_permission,
)
from iris_production_state.validation import validate_reproducibility

from m06_support import content_digest, external, materialization, operational_revision


def _manifest(
    expected: ReproducibilityClass,
    method: ReconstructionMethod = ReconstructionMethod.REGENERATE,
    *,
    equivalence: bool = False,
    semantic_contract: bool = False,
) -> ReconstructionManifest:
    target = operational_revision(f"reconstruction-target-{expected.value}-{method.value}")
    retained = materialization(target, f"retained-{expected.value}-{method.value}")
    return ReconstructionManifest(
        f"manifest-{expected.value}-{method.value}",
        target,
        method,
        (retained,),
        "a" * 64,
        external("workflow-r7") if method is ReconstructionMethod.REGENERATE else None,
        external("model-r4") if method is ReconstructionMethod.REGENERATE else None,
        external("toolchain-r3") if method is ReconstructionMethod.REGENERATE else None,
        (("os", "synthetic"),),
        (external("current-policy-r2"),),
        expected,
        external("equivalence-contract-v1") if equivalence else None,
        "seed-42",
        external("complete-material-inputs") if expected is ReproducibilityClass.EXACT_BYTES and method is ReconstructionMethod.REGENERATE else None,
        external("complete-execution-dimensions") if expected is ReproducibilityClass.EXACT_BYTES and method is ReconstructionMethod.REGENERATE else None,
        external("semantic-state-contract") if semantic_contract else None,
    )


class M06ReconstructionTests(unittest.TestCase):
    def test_s04_reconstruction_invariants(self) -> None:
        self.assertEqual(tuple(item.number for item in M06_INVARIANTS if item.section == "S04"), tuple(range(91, 121)))
        with self.assertRaises(ProductionStateAdmissionError):
            require_bounded_reproducibility(ReproducibilityClass.STOCHASTIC_REEXECUTABLE, ReproducibilityClass.EXACT_BYTES)

    def test_family_sds(self) -> None:
        stochastic = _manifest(ReproducibilityClass.STOCHASTIC_REEXECUTABLE)
        digest_a = content_digest(b"stochastic-output-a")
        digest_b = content_digest(b"stochastic-output-b")
        divergence = DivergenceEvidence(DivergenceKind.BYTE_DIVERGENCE, digest_a, digest_b, external("stochastic-observation"), "seed equality did not produce byte-identical output")
        receipt = ReproducibilityReceipt(
            "stochastic-receipt",
            stochastic,
            ReproducibilityClass.STOCHASTIC_REEXECUTABLE,
            operational_revision("stochastic-output"),
            None,
            divergence,
            (external("stochastic-run-evidence"),),
            3,
            True,
            True,
            None,
        )
        self.assertEqual(validate_reproducibility(receipt).achieved_class, ReproducibilityClass.STOCHASTIC_REEXECUTABLE)
        with self.assertRaises(ProductionStateAdmissionError):
            ReproducibilityReceipt(
                "stochastic-false-exact",
                stochastic,
                ReproducibilityClass.EXACT_BYTES,
                operational_revision("false-exact-output"),
                None,
                divergence,
                (external("run-evidence"),),
                4,
                True,
                True,
                None,
            )

    def test_family_rcl(self) -> None:
        with self.assertRaises(ProductionStateAdmissionError):
            require_bounded_reproducibility(ReproducibilityClass.REFERENCE_RECONSTRUCTABLE, ReproducibilityClass.EXACT_SEMANTIC_STATE)
        with self.assertRaises(ProductionStateAdmissionError):
            require_bounded_reproducibility(ReproducibilityClass.UNKNOWN, ReproducibilityClass.STOCHASTIC_REEXECUTABLE)

    def test_family_rxm(self) -> None:
        manifest = _manifest(ReproducibilityClass.EXACT_BYTES, ReconstructionMethod.RESTORE_RETAINED)
        digest = manifest.exact_input_refs[0].content_digest
        output = operational_revision("restoration-new-revision")
        divergence = DivergenceEvidence(DivergenceKind.NONE_PROVEN, digest, digest, external("restore-integrity-proof"), "retained bytes verified")
        receipt = ReproducibilityReceipt(
            "restoration-receipt",
            manifest,
            ReproducibilityClass.EXACT_BYTES,
            output,
            materialization(output, "restored-new-materialization"),
            divergence,
            (external("restore-source-evidence"),),
            5,
            True,
            True,
            external("quality-evidence-ref"),
        )
        self.assertEqual(receipt.manifest.method, ReconstructionMethod.RESTORE_RETAINED)
        self.assertNotEqual(receipt.output_revision_ref, manifest.target_revision_ref)
        with self.assertRaises(ProductionStateAdmissionError):
            replace(manifest, method=ReconstructionMethod.REGENERATE, workflow_ref=external("workflow"), model_ref=external("model"), toolchain_ref=external("toolchain"), complete_material_inputs_evidence_ref=None, complete_execution_dimensions_evidence_ref=None)
        with self.assertRaises(ProductionStateIntegrityError):
            ReproducibilityReceipt(
                "restoration-wrong-output-digest",
                manifest,
                ReproducibilityClass.EXACT_BYTES,
                output,
                materialization(output, "restored-wrong-digest", b"different-bytes"),
                divergence,
                (external("restore-source-evidence"),),
                6,
                True,
                True,
                external("quality-evidence-ref"),
            )

    def test_exact_semantic_state_requires_contract_and_observed_verification(self) -> None:
        manifest = _manifest(ReproducibilityClass.EXACT_SEMANTIC_STATE, semantic_contract=True)
        verification = external("semantic-state-verification")
        divergence = DivergenceEvidence(
            DivergenceKind.BYTE_DIVERGENCE,
            content_digest(b"old-encoding"),
            content_digest(b"new-encoding"),
            external("byte-difference-observation"),
            "physical encoding changed while the canonical semantic state remained exact",
        )
        output = operational_revision("semantic-state-output")
        with self.assertRaises(ProductionStateAdmissionError):
            ReproducibilityReceipt(
                "semantic-state-unverified",
                manifest,
                ReproducibilityClass.EXACT_SEMANTIC_STATE,
                output,
                None,
                divergence,
                (external("run-evidence"),),
                7,
                True,
                True,
                None,
            )
        receipt = ReproducibilityReceipt(
            "semantic-state-verified",
            manifest,
            ReproducibilityClass.EXACT_SEMANTIC_STATE,
            output,
            None,
            divergence,
            (external("run-evidence"), verification),
            8,
            True,
            True,
            None,
            verification,
        )
        self.assertEqual(receipt.achieved_class, ReproducibilityClass.EXACT_SEMANTIC_STATE)

    def test_family_drg(self) -> None:
        first = DivergenceEvidence(DivergenceKind.BYTE_DIVERGENCE, content_digest(b"a"), content_digest(b"b"), external("byte-proof"), "bytes differ")
        second = DivergenceEvidence(DivergenceKind.SEMANTIC_DIVERGENCE, None, None, external("semantic-proof"), "semantic evaluator reported divergence")
        self.assertNotEqual(first.kind, second.kind)
        with self.assertRaises(ProductionStateAdmissionError):
            DivergenceEvidence(DivergenceKind.NONE_PROVEN, None, None, external("empty-no-difference"), "not proved")

    def test_family_esb(self) -> None:
        with self.assertRaises(ProductionStateAdmissionError):
            _manifest(ReproducibilityClass.EQUIVALENT_WITHIN_CONTRACT, equivalence=False)
        manifest = _manifest(ReproducibilityClass.EQUIVALENT_WITHIN_CONTRACT, equivalence=True)
        self.assertIsInstance(manifest, ReconstructionManifest)

        verification = external("equivalence-verification")
        failure = DivergenceEvidence(
            DivergenceKind.EQUIVALENCE_CONTRACT_FAILURE,
            None,
            None,
            external("equivalence-failure"),
            "external evaluator rejected the equivalence contract",
        )
        with self.assertRaises(ProductionStateAdmissionError):
            ReproducibilityReceipt(
                "equivalence-failed",
                manifest,
                ReproducibilityClass.EQUIVALENT_WITHIN_CONTRACT,
                operational_revision("equivalence-failed-output"),
                None,
                failure,
                (verification,),
                9,
                True,
                True,
                None,
                equivalence_verification_ref=verification,
            )

        byte_difference = DivergenceEvidence(
            DivergenceKind.BYTE_DIVERGENCE,
            content_digest(b"equivalence-source"),
            content_digest(b"equivalence-result"),
            external("equivalence-byte-observation"),
            "bytes differ but the external contract evaluator admitted equivalence",
        )
        accepted = ReproducibilityReceipt(
            "equivalence-accepted",
            manifest,
            ReproducibilityClass.EQUIVALENT_WITHIN_CONTRACT,
            operational_revision("equivalence-accepted-output"),
            None,
            byte_difference,
            (verification,),
            10,
            True,
            True,
            None,
            equivalence_verification_ref=verification,
        )
        self.assertEqual(accepted.achieved_class, ReproducibilityClass.EQUIVALENT_WITHIN_CONTRACT)

    def test_family_hpr(self) -> None:
        evidence = HistoricalPermissionEvidence(
            external("historical-permission"),
            external("current-rights"),
            external("current-security"),
            False,
            True,
            10,
        )
        with self.assertRaises(ProductionStateAdmissionError):
            validate_historical_permission(evidence)
        allowed = HistoricalPermissionEvidence(external("historical-permission"), external("rights-now"), external("security-now"), True, True, 11)
        self.assertIs(validate_historical_permission(allowed), allowed)


if __name__ == "__main__":
    unittest.main()
