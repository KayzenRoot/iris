from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.verify_context_lock import (
    ContextLockError, DEPENDABOT_PIN_ONLY, verify_current_pr,
)

WORKFLOW = ".github/workflows/governance.yml"
OLD_CHECKOUT = "        uses: actions/checkout@" + "f" * 40 + " # v5"
NEW_CHECKOUT = "        uses: actions/checkout@" + "a" * 40 + " # v7.0.1"
OLD_PYTHON = "        uses: actions/setup-python@" + "e" * 40 + " # v6"
NEW_PYTHON = "        uses: actions/setup-python@" + "b" * 40 + " # v7.0.0"
BOT = {
    "pr_author": "dependabot[bot]",
    "pr_head_ref": "dependabot/github_actions/actions/setup-python-7.0.0",
    "pr_head_repo": "KayzenRoot/iris",
    "pr_base_repo": "KayzenRoot/iris",
}


class GuardedDependabotRealGitTests(unittest.TestCase):
    def git(self, root: Path, *args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    def fixture(self, root: Path, *, before=OLD_PYTHON, after=NEW_PYTHON,
                extra_workflow_line="", extra_file=False, executable=False):
        self.git(root, "init", "-q")
        self.git(root, "config", "user.email", "tests@example.invalid")
        self.git(root, "config", "user.name", "CI Fixture")
        wf = root / WORKFLOW
        wf.parent.mkdir(parents=True)
        wf.write_text("name: Governance\nsteps:\n" + before + "\n", encoding="utf-8")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "baseline")
        base = self.git(root, "rev-parse", "HEAD")
        wf.write_text("name: Governance\nsteps:\n" + after + "\n" + extra_workflow_line, encoding="utf-8")
        if extra_file:
            (root / "unauthorized.py").write_text("side effect\n", encoding="utf-8")
        self.git(root, "add", "-A")
        if executable:
            self.git(root, "update-index", "--chmod=+x", WORKFLOW)
        self.git(root, "commit", "-q", "-m", "dependabot proposed update")
        return base, self.git(root, "rev-parse", "HEAD")

    def verify(self, root: Path, base: str, head: str, **overrides):
        data = {**BOT, **overrides}
        return verify_current_pr(root, base_sha=base, head_sha=head, **data)

    def test_exact_single_line_setup_python_pin_from_bot_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root)
            self.assertEqual(self.verify(root, base, head), [DEPENDABOT_PIN_ONLY])

    def test_exact_single_line_checkout_pin_from_bot_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root, before=OLD_CHECKOUT, after=NEW_CHECKOUT)
            self.assertEqual(self.verify(root, base, head, pr_head_ref="dependabot/github_actions/actions/checkout-7.0.1"), [DEPENDABOT_PIN_ONLY])

    def test_any_non_bot_author_still_requires_full_context_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root)
            with self.assertRaisesRegex(ContextLockError, "must change at least one"):
                self.verify(root, base, head, pr_author="attacker")

    def test_foreign_repository_bot_pr_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root)
            with self.assertRaisesRegex(ContextLockError, "same-repository"):
                self.verify(root, base, head, pr_head_repo="external/fork")

    def test_unexpected_bot_branch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root)
            with self.assertRaisesRegex(ContextLockError, "unexpected dependabot branch"):
                self.verify(root, base, head, pr_head_ref="any-branch")

    def test_extra_workflow_line_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root, extra_workflow_line="permissions: write-all\n")
            with self.assertRaisesRegex(ContextLockError, "exactly one action pin line"):
                self.verify(root, base, head)

    def test_second_modified_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root, extra_file=True)
            with self.assertRaisesRegex(ContextLockError, "exactly the Governance workflow"):
                self.verify(root, base, head)

    def test_short_sha_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root, after="        uses: actions/setup-python@abc123 # v7.0.0")
            with self.assertRaisesRegex(ContextLockError, "full pinned official action SHA syntax"):
                self.verify(root, base, head)

    def test_changed_action_name_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root, before=OLD_CHECKOUT, after=NEW_PYTHON)
            with self.assertRaisesRegex(ContextLockError, "cannot switch action names"):
                self.verify(root, base, head)

    def test_changed_workflow_mode_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root, executable=True)
            with self.assertRaisesRegex(ContextLockError, "regular non-executable Git file"):
                self.verify(root, base, head)

    def test_checkout_head_still_requires_exact_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, head = self.fixture(root)
            with self.assertRaisesRegex(ContextLockError, "checkout is not the exact PR head"):
                self.verify(root, base, base)


if __name__ == "__main__":
    unittest.main()
