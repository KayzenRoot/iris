"""Original-repo-independent tests for the current-tree vendor-retirement scanner."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from scripts.audit_retired_context import RETIRED_PATTERN, scan_tracked_tree

VENDOR = bytes.fromhex("68697665").decode("ascii")


class RetiredContextScanTests(unittest.TestCase):
    def test_archive_is_not_a_vendor_hit(self):
        self.assertIsNone(RETIRED_PATTERN.search("archive ARCHIVE archival"))
        self.assertIsNotNone(RETIRED_PATTERN.search(VENDOR.upper() + "_MEMORY"))
        self.assertIsNotNone(RETIRED_PATTERN.search(VENDOR.title() + "ContextPort"))

    def test_scan_fails_on_any_real_text_or_filename_hit(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "ordinary.md").write_text(VENDOR.upper() + " memory\n", encoding="utf-8")
            (root / (VENDOR.lower() + "_script.py")).write_text("print(42)\n", encoding="utf-8")
            self.assertEqual(len(scan_tracked_tree(root, ["ordinary.md", VENDOR.lower() + "_script.py"])), 2)

    def test_scanner_passes_neutral_current_tree(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            (root / "neutral.py").write_text("archive = 'project context'\n", encoding="utf-8")
            self.assertEqual(scan_tracked_tree(root, ["neutral.py"]), [])


if __name__ == "__main__":
    unittest.main()
