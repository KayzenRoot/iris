from __future__ import annotations

import unittest

from iris_production_state.dependencies import (
    DependencyDiscoveryReceipt,
    DependencySlice,
    FingerprintDimension,
    OperationalDependencyObservation,
    SliceOmissionProof,
    admit_dependency_discovery,
    analyze_impact,
    build_fingerprint,
    build_reverse_index,
    build_slice_fingerprint,
    compare_fingerprints,
)
from iris_production_state.enums import DependencyKind, FingerprintScope, ImpactState, IndexState, MaterialityState
from iris_production_state.errors import ProductionStateAdmissionError
from iris_production_state.invariants import M06_INVARIANTS

from m06_support import content_digest, external, operational_revision


class M06DependencyTests(unittest.TestCase):
    def test_s02_dependency_impact_invariants(self) -> None:
        self.assertEqual(tuple(item.number for item in M06_INVARIANTS if item.section == "S02"), tuple(range(31, 61)))
        dependency = external("dependency-image")
        dimension = FingerprintDimension(dependency, "pixels", MaterialityState.MATERIAL, content_digest())
        fingerprint = build_fingerprint((dimension,), FingerprintScope.FULL_CAUSAL)
        self.assertEqual(len(fingerprint.digest), 64)

    def test_family_cfm(self) -> None:
        material = FingerprintDimension(external("input-mesh"), "mesh", MaterialityState.MATERIAL, content_digest())
        policy = FingerprintDimension(external("policy-current"), "license", MaterialityState.MATERIAL, content_digest(), policy_sensitive=True)
        full = build_fingerprint((material, policy), FingerprintScope.FULL_CAUSAL)
        policy_only = build_fingerprint((material, policy), FingerprintScope.POLICY_SENSITIVE)
        self.assertEqual(len(full.dimensions), 2)
        self.assertNotEqual(full.digest, policy_only.digest)
        self.assertEqual(compare_fingerprints(full, policy_only).state, MaterialityState.UNKNOWN)

    def test_family_msi(self) -> None:
        material = FingerprintDimension(external("mesh"), "geometry", MaterialityState.MATERIAL, content_digest())
        display = FingerprintDimension(external("display-name"), "label", MaterialityState.NON_MATERIAL, None, mandatory=False)
        base = build_fingerprint((material, display), FingerprintScope.SELECTED_SLICE)
        included = tuple(sorted((material.key,)))
        slice_record = DependencySlice(
            "slice-mesh",
            base,
            included,
            (SliceOmissionProof(display.key, MaterialityState.NON_MATERIAL, external("nonmateriality-proof")),),
            external("slice-completeness-proof"),
        )
        selected = build_slice_fingerprint(slice_record)
        self.assertEqual(tuple(item.key for item in selected.dimensions), included)
        with self.assertRaises(ProductionStateAdmissionError):
            DependencySlice(
                "slice-unsafe",
                base,
                (),
                (SliceOmissionProof(display.key, MaterialityState.NON_MATERIAL, external("display-proof")), SliceOmissionProof(material.key, MaterialityState.NON_MATERIAL, external("false-omission-proof"))),
                external("unsafe-completeness"),
            )

    def test_family_hds(self) -> None:
        consumer = operational_revision("consumer-hidden")
        dependency = external("hidden-runtime-texture")
        observation = OperationalDependencyObservation(
            consumer,
            dependency,
            DependencyKind.HIDDEN_MATERIAL,
            MaterialityState.MATERIAL,
            "texture",
            external("discovery-evidence"),
            10,
            hidden_material=True,
        )
        receipt = DependencyDiscoveryReceipt(
            "discovery-one", consumer, None, (observation,), "a" * 64, external("discovery-evidence"), 10
        )
        with self.assertRaises(ProductionStateAdmissionError):
            admit_dependency_discovery(receipt)
        with self.assertRaises(ProductionStateAdmissionError):
            build_fingerprint((FingerprintDimension(dependency, "unknown", MaterialityState.UNKNOWN, None),), FingerprintScope.FULL_CAUSAL)

    def test_family_icx(self) -> None:
        source = external("changed-texture")
        first_consumer = operational_revision("consumer-shot")
        second_consumer = operational_revision("consumer-video")
        observations = (
            OperationalDependencyObservation(first_consumer, source, DependencyKind.REQUIRED, MaterialityState.MATERIAL, "texture", external("evidence-a"), 1),
            OperationalDependencyObservation(second_consumer, first_consumer, DependencyKind.REQUIRED, MaterialityState.MATERIAL, "shot", external("evidence-b"), 2),
        )
        index = build_reverse_index("index-complete", "epoch-1", observations, state=IndexState.COMPLETE_FRESH, completeness_evidence_ref=external("complete-index-closure-proof"))
        cone = analyze_impact(source, index, analyzed_at_ms=3)
        self.assertEqual(cone.state, ImpactState.AFFECTED)
        self.assertEqual(len(cone.affected_refs), 2)
        self.assertTrue(any(len(path.refs) == 3 for path in cone.paths))
        unused = analyze_impact(external("unreferenced"), index, analyzed_at_ms=3)
        self.assertEqual(unused.state, ImpactState.UNAFFECTED_PROVEN)

    def test_family_rdi(self) -> None:
        target = external("possibly-affected")
        observations = (OperationalDependencyObservation(operational_revision("consumer-partial"), target, DependencyKind.REQUIRED, MaterialityState.MATERIAL, "frame", external("index-evidence"), 1),)
        partial = build_reverse_index("index-partial", "epoch-2", observations, state=IndexState.PARTIAL)
        stale = build_reverse_index("index-stale", "epoch-3", observations, state=IndexState.STALE)
        self.assertEqual(analyze_impact(external("missing-from-partial"), partial, analyzed_at_ms=1).state, ImpactState.UNKNOWN)
        self.assertEqual(analyze_impact(target, stale, analyzed_at_ms=1).state, ImpactState.BLOCKED_BY_STALE_EVIDENCE)

    def test_impact_node_limit_preserves_unknown_frontier(self) -> None:
        source = external("bounded-impact-root")
        consumer = operational_revision("bounded-impact-consumer")
        observation = OperationalDependencyObservation(
            consumer,
            source,
            DependencyKind.REQUIRED,
            MaterialityState.MATERIAL,
            "mesh",
            external("bounded-impact-edge-evidence"),
            1,
        )
        index = build_reverse_index(
            "bounded-impact-index",
            "bounded-impact-epoch",
            (observation,),
            state=IndexState.COMPLETE_FRESH,
            completeness_evidence_ref=external("bounded-impact-completeness"),
        )
        cone = analyze_impact(source, index, analyzed_at_ms=2, max_nodes=1)
        self.assertEqual(cone.state, ImpactState.UNKNOWN)
        self.assertEqual(len(cone.affected_refs), 1)
        self.assertEqual(len(cone.unknown_frontier), 1)


if __name__ == "__main__":
    unittest.main()
