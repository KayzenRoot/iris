"""WO0067 regression: retired external-context namespace must never reappear."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_TOKEN = "".join(chr(v) for v in (104, 105, 118, 101))
LEGACY_PATTERN = re.compile(
    rf"(?i)(?<![A-Za-z]){re.escape(LEGACY_TOKEN)}(?![a-z])"
    rf"|(?<=[a-z]){re.escape(LEGACY_TOKEN.capitalize())}(?![a-z])"
)


class NamespacePurgeTests(unittest.TestCase):
    def test_01_no_tracked_path_uses_retired_namespace(self):
        offenders = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
                continue
            relative = path.relative_to(ROOT).as_posix()
            if LEGACY_PATTERN.search(relative):
                offenders.append(relative)
        self.assertEqual(offenders, [])

    def test_02_no_utf8_repository_text_uses_retired_namespace(self):
        offenders = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
                continue
            try:
                body = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if LEGACY_PATTERN.search(body):
                offenders.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(offenders, [])

    def test_03_former_vendor_classifier_detects_embedded_identifiers(self):
        """Reject embedded CamelCase names, but not unrelated archive terminology."""
        alias = LEGACY_TOKEN.capitalize()
        for candidate in ("gef" + alias + "BridgeTests",
                          "pinned" + alias + "Commit",
                          LEGACY_TOKEN.upper() + "_MEMORY"):
            with self.subTest(candidate=candidate):
                self.assertIsNotNone(LEGACY_PATTERN.search(candidate))
        for neutral in ("archive", "ARCHIVE_REPRODUCIBLE", "catalogue"):
            with self.subTest(neutral=neutral):
                self.assertIsNone(LEGACY_PATTERN.search(neutral))


if __name__ == "__main__":
    unittest.main()
