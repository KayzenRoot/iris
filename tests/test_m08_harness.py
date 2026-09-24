from __future__ import annotations

import unittest

from examples.m08_domain_neutral_profiles import build_profiles
from iris_microbenchmark import InterferenceState, ResultState


class TestSyntheticProfiles(unittest.TestCase):
    def test_seven_profiles_are_deterministic_and_nonphysical(self):
        first = build_profiles()
        second = build_profiles()
        self.assertEqual(first, second)
        self.assertEqual(len(first), 7)
        self.assertEqual(len({item["profile_id"] for item in first}), 7)
        self.assertTrue(all(item["synthetic_fixture_only"] for item in first))
        self.assertTrue(all(item["physical_measurement_performed"] is False for item in first))
        by_name = {item["profile_id"]: item for item in first}
        self.assertEqual(by_name["cpu-only"]["declared_synthetic_device_memory_bytes"], 0)
        self.assertEqual(by_name["gpu-8gb-synthetic"]["declared_synthetic_device_memory_bytes"], 8 * 1024**3)
        self.assertEqual(by_name["high-concurrency-declared"]["budget"].max_concurrency, 4)
        self.assertEqual(by_name["interference-observed"]["result_state"], ResultState.INVALID_INTERFERENCE)
        self.assertEqual(by_name["telemetry-unknown"]["interference_state"], InterferenceState.UNKNOWN_TELEMETRY)


if __name__ == "__main__":
    unittest.main()
