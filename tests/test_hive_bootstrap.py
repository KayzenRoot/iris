from __future__ import annotations

import unittest

from scripts.hive_bootstrap import resolve_registered_project


class HiveProjectResolutionTests(unittest.TestCase):
    def test_exact_relative_path_wins(self) -> None:
        projects = [
            {"project_id": "wrong", "name": "IRIS", "relative_path": "archive/iris"},
            {"project_id": "right", "name": "Renamed IRIS", "relative_path": "iris"},
        ]
        result = resolve_registered_project(projects, name="IRIS", relative_path="iris")
        self.assertIsNotNone(result)
        self.assertEqual(result["project_id"], "right")

    def test_same_name_different_path_fails_closed(self) -> None:
        projects = [{"project_id": "other", "name": "IRIS", "relative_path": "other/iris"}]
        with self.assertRaisesRegex(RuntimeError, "different path"):
            resolve_registered_project(projects, name="IRIS", relative_path="iris")

    def test_missing_project_returns_none(self) -> None:
        projects = [{"project_id": "other", "name": "Widget", "relative_path": "widget"}]
        self.assertIsNone(resolve_registered_project(projects, name="IRIS", relative_path="iris"))


if __name__ == "__main__":
    unittest.main()
