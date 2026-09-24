from __future__ import annotations

import unittest

import iris_resource_twin as m09
from scripts.validate_m09_boundaries import validate_boundaries
from scripts.validate_m09_invariants import validate_catalogs_and_proofs


class TestM09Boundaries(unittest.TestCase):
    def test_forbidden_import_and_execution_boundary(self) -> None:
        self.assertEqual(validate_boundaries(), ())

    def test_full_surface_absorbed_and_invariant_catalogs(self) -> None:
        self.assertEqual(len(m09.M09_SURFACES), 83)
        self.assertEqual(len(m09.M09_ABSORBED_COMPONENTS), 15)
        self.assertEqual(len(m09.M09_INVARIANTS), 514)
        self.assertEqual(validate_catalogs_and_proofs(), ())

    def test_public_api_cannot_cross_downstream_authorities(self) -> None:
        for forbidden in (
            "compile_m10_plan", "predict_oom", "schedule_workload", "place_job",
            "kill_process", "restart_worker", "delete_spill", "benchmark_device",
            "judge_quality", "publish_asset",
        ):
            self.assertFalse(hasattr(m09, forbidden), forbidden)
        self.assertTrue(hasattr(m09, "ResourceTwin"))
        self.assertTrue(hasattr(m09, "LeaseBook"))
        self.assertTrue(hasattr(m09, "MobilityLedger"))
        self.assertTrue(hasattr(m09, "PressureGovernor"))

    def test_m09_is_m07_m08_and_m05_reference_only(self) -> None:
        self.assertIn("M07:discovery", m09.ProvenanceRef("M07:discovery", "evidence-ref", 1).source)
        self.assertEqual(m09.ResourceIdentity("physical", m09.ResourceTier.VRAM, "runtime").physical_id, "physical")


if __name__ == "__main__":
    unittest.main()
