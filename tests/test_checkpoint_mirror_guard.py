from __future__ import annotations

import unittest

from scripts.validate_governance import validate_checkpoint_consistency


CANONICAL = (
    "# IRIS Canonical Checkpoint\n"
    "\n## STATUS\nACTIVE\n"
    "## VERSION\ncontract-v1\n"
    "## PHASE\nPLANNING\n"
    "## OBJECTIVE\nSource-locked owner work.\n"
    "## IN PROGRESS\nAudit handoff.\n"
    "## BLOCKERS\nOwner proof unavailable.\n"
    "## NEXT STEP\nOwner source disposition.\n"
).encode("utf-8")
MACHINE = {
    "canonicalCheckpoint": "docs/project-brain/13-CHECKPOINT.md",
    "status": "ACTIVE",
    "version": "contract-v1",
    "phase": "PLANNING",
    "nextStep": "Owner source disposition.",
}


class CheckpointMirrorGuardTests(unittest.TestCase):
    def test_identical_markdown_mirrors_and_machine_fields_pass(self) -> None:
        validate_checkpoint_consistency(CANONICAL, CANONICAL, MACHINE)

    def test_objective_drift_is_rejected_even_if_existing_four_fields_match(self) -> None:
        altered = CANONICAL.replace(b"Source-locked owner work.", b"Changed objective.")
        with self.assertRaisesRegex(SystemExit, "not byte-identical"):
            validate_checkpoint_consistency(CANONICAL, altered, MACHINE)

    def test_in_progress_drift_is_rejected(self) -> None:
        altered = CANONICAL.replace(b"Audit handoff.", b"Unexpected stage.")
        with self.assertRaisesRegex(SystemExit, "not byte-identical"):
            validate_checkpoint_consistency(CANONICAL, altered, MACHINE)

    def test_blockers_drift_is_rejected(self) -> None:
        altered = CANONICAL.replace(b"Owner proof unavailable.", b"None.")
        with self.assertRaisesRegex(SystemExit, "not byte-identical"):
            validate_checkpoint_consistency(CANONICAL, altered, MACHINE)

    def test_newline_drift_is_rejected(self) -> None:
        with self.assertRaisesRegex(SystemExit, "not byte-identical"):
            validate_checkpoint_consistency(CANONICAL, CANONICAL.rstrip(b"\n"), MACHINE)

    def test_windows_crlf_mirror_is_not_byte_identical(self) -> None:
        with self.assertRaisesRegex(SystemExit, "not byte-identical"):
            validate_checkpoint_consistency(CANONICAL, CANONICAL.replace(b"\n", b"\r\n"), MACHINE)

    def test_machine_next_step_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(SystemExit, "machine checkpoint drift for nextStep"):
            validate_checkpoint_consistency(CANONICAL, CANONICAL, {**MACHINE, "nextStep": "Stale next step."})

    def test_machine_status_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(SystemExit, "machine checkpoint drift for status"):
            validate_checkpoint_consistency(CANONICAL, CANONICAL, {**MACHINE, "status": "STALE"})

    def test_machine_checkpoint_target_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(SystemExit, "machine checkpoint target mismatch"):
            validate_checkpoint_consistency(CANONICAL, CANONICAL, {**MACHINE, "canonicalCheckpoint": "other.md"})


if __name__ == "__main__":
    unittest.main()
