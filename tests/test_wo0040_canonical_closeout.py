"""WO0040 post-merge factual documentation regression checks; local files only."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WO0040CanonicalCloseoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checkpoint = (ROOT / "docs/project-brain/13-CHECKPOINT.md").read_text(encoding="utf-8")
        cls.bridge = (ROOT / ".engineering/CHECKPOINT.md").read_text(encoding="utf-8")
        cls.machine = json.loads((ROOT / ".engineering/CHECKPOINT.json").read_text(encoding="utf-8"))
        cls.backlog = (ROOT / "docs/project-brain/14-BACKLOG.md").read_text(encoding="utf-8")
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.overview = (ROOT / "docs/project-brain/01-PROJECT-OVERVIEW.md").read_text(encoding="utf-8")

    def test_checkpoint_mirror_and_machine_exact(self):
        self.assertEqual(self.checkpoint, self.bridge)
        self.assertEqual(self.machine["nextStep"], self.checkpoint.split("## NEXT STEP\\n", 1)[1].strip())

    def test_completed_wo39_receipt_and_current_next_step(self):
        for marker in ("IRIS-WO-0039", "PR #149", "Governance #528", "4290/4290",
                       "be18231423651c5dbff584613fc46d3e0104107f"):
            self.assertIn(marker, self.checkpoint)
        next_step = self.machine["nextStep"]
        for marker in ("NEXT_REQUIRED_OWNER_GATE", "M12/#128", "M54/#145", "M58/#146",
                       "M60/#147", "OPEN HIGH_FOR_FUTURE_FREEZE", "NOT_ADMITTED"):
            self.assertIn(marker, next_step)
        self.assertNotIn("IRIS-WO-0033 D01:", next_step)

    def test_backlog_retains_history_and_actual_closeout(self):
        for marker in ("IRIS-WO-0039 historical pre-merge proposal",
                       "IRIS-WO-0039 **COMPLETED source-only offline tool**",
                       "Governance #527", "Governance #528", "4290/4290"):
            self.assertIn(marker, self.backlog)

    def test_public_status_separates_old_and_current_baselines(self):
        for text in (self.readme, self.overview):
            for marker in ("PR #139", "4090/4090", "PR #149", "Governance #528", "4290/4290",
                           "OPEN HIGH_FOR_FUTURE_FREEZE", "NOT_ADMITTED"):
                self.assertIn(marker, text)
            self.assertIn("historical", text.lower())

    def test_never_promote_draft_or_other_owner_to_actual_authority(self):
        for text in (self.checkpoint, self.backlog, self.readme, self.overview):
            for marker in ("B_FUTURE_OWNER_RECEIPT", "DIRECTION_ONLY", "UNADOPTED_NOT_FROZEN"):
                self.assertIn(marker, text)
        self.assertIn("COMPLETE_DRAFT_FORMAT_ONLY is never approval", self.machine["nextStep"])
        self.assertIn("SPECIFIED_NOT_EXECUTED", self.machine["nextStep"])
