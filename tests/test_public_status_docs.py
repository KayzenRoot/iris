"""Guard against stale public status claims without freezing future module progress.

The canonical checkpoint, not these pages, remains project-state authority.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublicStatusDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.overview = (ROOT / "docs/project-brain/01-PROJECT-OVERVIEW.md").read_text(encoding="utf-8")
        cls.checkpoint = (ROOT / "docs/project-brain/13-CHECKPOINT.md").read_text(encoding="utf-8")
        cls.bridge = (ROOT / ".engineering/CHECKPOINT.md").read_text(encoding="utf-8")
        cls.machine = json.loads((ROOT / ".engineering/CHECKPOINT.json").read_text(encoding="utf-8"))

    def test_retired_next_module_claims_not_present(self) -> None:
        for text in (self.readme, self.overview):
            self.assertNotIn("M04_PLANNING_READY", text)
            self.assertNotIn("M04 Multimodal IR / Scene IR: planning is the next", text)
            self.assertNotIn("next governed step is a separate M05 implementation", text)

    def test_public_docs_name_checkpoint_as_canonical(self) -> None:
        self.assertIn("docs/project-brain/13-CHECKPOINT.md", self.readme)
        self.assertIn("[canonical checkpoint](13-CHECKPOINT.md)", self.overview)
        self.assertIn("M01–M09", self.readme)
        self.assertIn("M01–M09", self.overview)

    def test_public_docs_preserve_blocking_owner_and_nonadmission(self) -> None:
        for text in (self.readme, self.overview):
            for marker in ("M10", "M11", "M12", "NOT_FROZEN", "NOT_ADMITTED", "issue #110"):
                self.assertIn(marker, text)
            self.assertIn("110", text)
            self.assertIn("80", text)

    def test_reconciled_checkpoint_is_byte_identical_to_bridge(self) -> None:
        self.assertEqual(self.checkpoint, self.bridge)
        self.assertIn("Governance #499", self.checkpoint)
        self.assertIn("4009/4009", self.checkpoint)
        self.assertEqual(self.machine["nextStep"], self.checkpoint.split("## NEXT STEP\n", 1)[1].strip())

    def test_source_only_m12_milestone_not_confused_with_owner_approval(self) -> None:
        for text in (self.readme, self.overview, self.machine["nextStep"]):
            self.assertIn("PREPARED_FOR_OWNER_REVIEW_ONLY", text)
            self.assertIn("NOT_FROZEN", text)
        evidence = json.loads((ROOT / ".engineering/evidence/IRIS-WO-0028.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["readiness"]["status"], "BLOCKED_FOR_FREEZE")
        self.assertEqual(evidence["candidate"]["implementationAuthority"], "NOT_ADMITTED")
        self.assertEqual(evidence["candidate"]["ownerQuestions"]["total"], 110)
        self.assertEqual(evidence["candidate"]["futureNegativeCases"]["total"], 80)
        self.assertEqual(evidence["verifiedCloseout"]["exactMainGovernance"]["tests"], "4009/4009")


if __name__ == "__main__":
    unittest.main()
