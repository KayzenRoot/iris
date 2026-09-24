from __future__ import annotations

import unittest

from iris_resource_twin import (
    create_evidence_bundle,
    deserialize,
    serialize,
    verify_evidence_bundle,
)


def bundle():
    sha = "a" * 64
    return create_evidence_bundle(
        work_order="IRIS-WO-0013",
        base_sha="b" * 40,
        head_sha="c" * 40,
        changed_files=("iris_resource_twin/model.py", "tests/test_m09_twin.py"),
        surface_count=83,
        absorbed_component_count=15,
        invariant_count=514,
        invariant_proof_count=514,
        invariant_map_digest=sha,
        schema_version="1.0.0",
        public_api=("ResourceTwin", "LeaseBook", "MobilityLedger"),
        runtime_dependencies=("Python standard library",),
        import_boundary_digest=sha,
        validation_facts=(("focused M09 tests", "PASS", "test result ref"), ("full suite", "PENDING", "exact head required")),
        authority_boundaries=(("M01", "quality authority remains external"), ("M10", "execution planning excluded")),
        synthetic_profiles=(("gpu-8gb-synthetic", 8 * 1024**3, True),),
        serialization_digest=sha,
        migration_digest=sha,
        round_trip_digest=sha,
        security_limits=(("max_events", 20_000), ("max_payload_bytes", 4_000_000)),
        context_lock_digest=sha,
        conflicts_or_failures_fixed=(),
        risks=("independent review is pending",),
        deferred_ports=("M55 owns physical storage", "M11 owns worker lifecycle"),
        checkpoint_delta_proposed="M09 implementation qualified at exact HEAD; independent audit and approval remain pending.",
    )


class TestM09Evidence(unittest.TestCase):
    def test_bundle_is_deterministic_and_exact_head_bound(self) -> None:
        first = bundle()
        second = bundle()
        self.assertEqual(first.bundle_digest, second.bundle_digest)
        self.assertTrue(verify_evidence_bundle(first, expected_head="c" * 40))
        self.assertEqual(deserialize(serialize(first)), first)
        with self.assertRaisesRegex(ValueError, "exact head"):
            verify_evidence_bundle(first, expected_head="d" * 40)

    def test_bundle_rejects_incomplete_frozen_counts_and_non_proposed_delta(self) -> None:
        values = bundle().__dict__
        with self.assertRaisesRegex(ValueError, "complete catalog/proof counts"):
            create_evidence_bundle(**{**values, "surface_count": 82, "bundle_digest": ""})
        with self.assertRaisesRegex(ValueError, "proposed checkpoint delta"):
            from iris_resource_twin import EvidenceBundle
            broken = EvidenceBundle(**{**values, "checkpoint_delta_proposed": "", "bundle_digest": ""})
            verify_evidence_bundle(broken)


if __name__ == "__main__":
    unittest.main()
