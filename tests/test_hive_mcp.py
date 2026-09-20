from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.hive_mcp import build_mcp_command, resolve_hive_repo


class HiveMcpLauncherTests(unittest.TestCase):
    def test_configured_hive_repo_is_selected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "backend").mkdir()
            (repo / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
            with patch.dict(os.environ, {"HIVE_REPO_PATH": str(repo)}, clear=False):
                self.assertEqual(resolve_hive_repo(), repo.resolve())

    def test_command_uses_stable_hive_stdio_server(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "backend").mkdir()
            (repo / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
            with patch.dict(os.environ, {"HIVE_REPO_PATH": str(repo)}, clear=False):
                resolved, command = build_mcp_command()
            self.assertEqual(resolved, repo.resolve())
            self.assertEqual(command, ["docker", "compose", "exec", "-T", "api", "python", "-m", "app.mcp_server"])

    def test_missing_hive_repo_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            with patch.dict(os.environ, {"HIVE_REPO_PATH": str(missing)}, clear=False):
                with patch("scripts.hive_mcp.ROOT", Path(tmp) / "iris"):
                    with self.assertRaisesRegex(RuntimeError, "checkout not found"):
                        resolve_hive_repo()


if __name__ == "__main__":
    unittest.main()
