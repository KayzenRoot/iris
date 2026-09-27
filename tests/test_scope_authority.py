"""Fail-closed source-authority Scope regression tests; no hardware, network or owners."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "docs/project-brain/03-SCOPE.md"


class AuthoritativeScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scope = SCOPE.read_text(encoding="utf-8")
        cls.checkpoint = (ROOT / "docs/project-brain/13-CHECKPOINT.md").read_text(encoding="utf-8")
        cls.machine = json.loads((ROOT / ".engineering/CHECKPOINT.json").read_text(encoding="utf-8"))

    def test_m12_candidate_is_delivered_not_a_future_work_order(self) -> None:
        self.assertIn("IRIS-WO-0028 delivered", self.scope)
        for marker in ("PR #135", "Governance #498", "exact-main #499", "PR #136",
                       "exact-main #503", "PREPARED_FOR_OWNER_REVIEW_ONLY", "NOT_FROZEN"):
            self.assertIn(marker, self.scope)
        self.assertNotIn("The next separately governed IRIS-WO-0028", self.scope)
        self.assertNotIn("IRIS-WO-0028` requires its own", self.scope)

    def test_m11_completed_technology_steps_not_falsely_pending(self) -> None:
        self.assertIn("M11 Final Technology Review and corrected Forward Compatibility Scan have since completed", self.scope)
        self.assertIn("m11-contract-candidate-v0.2", self.scope)
        self.assertNotIn("Final Technology Review and Forward Compatibility Scan remain required", self.scope)
        self.assertNotIn("Next: M11 Final Technology Review", self.scope)

    def test_real_owner_gates_and_source_only_evidence_preserved(self) -> None:
        for marker in ("Issue #110", "H01", "H02", "H03", "H04", "86 M11",
                       "110 M12", "80 M12", "SPECIFIED_NOT_EXECUTED", "NOT_ADMITTED"):
            self.assertIn(marker, self.scope)
        self.assertIn("NONE_SELECTED", self.scope)
        self.assertIn("NOT_FROZEN", self.scope)
        for issue in ("#82", "#110", "#112", "#128"):
            self.assertIn(issue, self.scope)

    def test_scope_matches_machine_and_checkpoint_authority(self) -> None:
        self.assertIn("IRIS-WO-0028", self.checkpoint)
        self.assertIn("PREPARED_FOR_OWNER_REVIEW_ONLY", self.machine["nextStep"])
        self.assertIn("NONE_SELECTED", self.scope)
        self.assertIn("actual M09 owner disposition", self.machine["nextStep"])
        self.assertIn("NOT_ADMITTED", self.scope)
        self.assertIn("NOT_ADMITTED", self.machine["nextStep"])


if __name__ == "__main__":
    unittest.main()
