from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.gef_preflight import resolve_gef_repo


class GefPreflightResolutionTests(unittest.TestCase):
    def test_configured_repo_is_selected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            (repo / "package.json").write_text(json.dumps({"version": "1.0.0"}), encoding="utf-8")
            with patch.dict(os.environ, {"GEF_REPO_PATH": str(repo)}, clear=False):
                self.assertEqual(resolve_gef_repo(), repo.resolve())

    def test_missing_repo_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            with patch.dict(os.environ, {"GEF_REPO_PATH": str(missing)}, clear=False):
                with patch("scripts.gef_preflight.ROOT", Path(tmp) / "iris"):
                    with self.assertRaisesRegex(RuntimeError, "checkout not found"):
                        resolve_gef_repo()


if __name__ == "__main__":
    unittest.main()
