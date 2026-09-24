from __future__ import annotations

import unittest

from examples.m09_resource_twin_profiles import build_profiles


class TestM09SyntheticProfiles(unittest.TestCase):
    def test_seven_domain_neutral_profiles_include_constrained_8_gib_and_higher_tiers(self) -> None:
        profiles = build_profiles()
        self.assertEqual(len(profiles), 7)
        self.assertEqual(len({item["profile_id"] for item in profiles}), 7)
        by_name = {item["profile_id"]: item for item in profiles}
        self.assertTrue(by_name["gpu-8gb-synthetic"]["commitment_admitted"])
        self.assertFalse(by_name["gpu-8gb-constrained-headroom"]["commitment_admitted"])
        self.assertTrue(by_name["balanced-16gb-synthetic"]["commitment_admitted"])
        self.assertTrue(by_name["high-capacity-24gb-synthetic"]["commitment_admitted"])
        self.assertFalse(by_name["gpu-8gb-unknown-telemetry"]["commitment_admitted"])
        self.assertFalse(by_name["gpu-8gb-conflicting-observations"]["commitment_admitted"])
        self.assertTrue(all(item["synthetic_fixture_only"] for item in profiles))
        self.assertTrue(all(not item["physical_measurement_performed"] for item in profiles))


if __name__ == "__main__":
    unittest.main()
