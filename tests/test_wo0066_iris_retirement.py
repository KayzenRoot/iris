"""WO0066: standalone Git-first operation and immutable original audit tests."""
from __future__ import annotations

import hashlib
import json
import re
import unittest
from tempfile import TemporaryDirectory

from scripts.validate_governance import reject_retired_operational_paths
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_INDEX_SHA = "a60d19c86bddd3699498f7d1f248a00368e32220"
LEGACY_PATHS = (
    ".codex/config.toml", "docs/IRIS-INTEGRATION.md",
    "scripts/iris-bootstrap.ps1", "scripts/iris_bootstrap.py",
    "scripts/iris_mcp.py", "tests/test_iris_bootstrap.py", "tests/test_iris_mcp.py",
)
ACTIVE_SOURCES = (
    "README.md", "AGENTS.md", "docs/project-brain/00-README-UPLOAD-ORDER.md",
    "docs/project-brain/01-PROJECT-OVERVIEW.md",
    "docs/project-brain/02-REQUIREMENTS.md",
    "docs/project-brain/04-ARCHITECTURE.md",
    "docs/project-brain/05-INTEGRATION-CONTRACTS.md",
    "docs/project-brain/06-QUALITY-NORTH-STAR.md",
    "docs/project-brain/08-SLOW-PLANNING-PROTOCOL.md",
    "docs/project-brain/10-SECURITY-GOVERNANCE.md",
    "docs/project-brain/12-LOCAL-DEPLOYMENT.md",
    "docs/project-brain/15-DEFINITION-OF-DONE.md",
    "docs/product/IRIS-PRODUCT-NORTH-STAR.md",
    ".engineering/gef/GEF-ADOPTION.md",
    ".engineering/gef/GEF-POLICY.md",
)


class StandaloneIRISMigrationTests(unittest.TestCase):
    """Offline-only checks; never starts a retired local service."""

    def test_01_retired_runtime_and_project_mcp_files_absent(self):
        """Former project MCP launcher, HTTP bootstrap and tests are removed."""
        for name in LEGACY_PATHS:
            with self.subTest(path=name):
                self.assertFalse((ROOT / name).exists(), name)

    def test_02_manifest_has_no_external_runtime_pin(self):
        """Only the independently pinned GEF source release remains."""
        m = json.loads((ROOT / ".engineering/BOOTSTRAP-MANIFEST.json").read_text())
        self.assertNotIn("iris", m)
        self.assertEqual(m["mode"], "STANDALONE_GIT_FIRST")
        self.assertEqual(m["contextSource"], "CANONICAL_GIT_PROJECT_BRAIN")
        self.assertEqual(m["externalContextRuntime"], "NONE_REQUIRED")
        self.assertEqual(
            m["gef"]["releaseCommit"], "866fe3af8cccc65c929aaf6a47a924401fa448b3"
        )

    def test_03_gef_profile_and_bridge_are_git_native(self):
        """GEF is a source-governance aid, not an external context runtime."""
        p = json.loads((ROOT / ".engineering/gef/GEF-PROJECT-PROFILE.json").read_text())
        b = json.loads((ROOT / ".engineering/gef/GEF-SOURCE-BRIDGE.json").read_text())
        self.assertEqual(p["profile"], "GIT_NATIVE")
        self.assertEqual(b["profile"], "GIT_NATIVE")
        self.assertEqual(b["canonicalCheckpoint"], "docs/project-brain/13-CHECKPOINT.md")
        self.assertEqual(b["domains"]["PROJECT_STATE"], b["canonicalCheckpoint"])

    def test_04_ci_has_no_retired_server_or_bootstrap(self):
        """Governance compiles only repository-local validator and Git guards."""
        w = (ROOT / ".github/workflows/governance.yml").read_text()
        self.assertIn("scripts/verify_context_lock.py", w)
        self.assertIn('python-version: "3.12"', w)
        self.assertNotIn("scripts/iris_", w)
        self.assertNotIn("iris-bootstrap", w)
        self.assertIn("python -m unittest discover -s tests", w)

    def test_05_primary_docs_no_external_context_dependency(self):
        """Live README, source guidance and architecture have no vendor preflight."""
        for name in ACTIVE_SOURCES:
            with self.subTest(path=name):
                self.assertNotRegex((ROOT / name).read_text(), r"(?i)\bhive\b")
        self.assertIn("no required external context runtime",
                      (ROOT / "AGENTS.md").read_text())

    def test_06_active_index_retains_61_modules_without_vendor(self):
        """Only future M52/M60 sessions change, not currently admitted runtime."""
        s = (ROOT / "planning/MASTER-MODULE-INDEX-CURRENT.md").read_text()
        self.assertEqual(len(re.findall(r"^### M\d\d — ", s, re.M)), 61)
        self.assertEqual(len(re.findall(r"^- S0[1-5] — ", s, re.M)), 305)
        self.assertIn("### M52 — IRIS-Native Multimodal Memory", s)
        self.assertIn("S03 Standalone IRIS integration validation", s)
        self.assertNotRegex(s, r"(?i)\bhive\b")
        self.assertIn("future planning only", s)

    def test_07_original_index_unchanged_for_prior_audits(self):
        """Original 47/235 full-scan source proof must remain reproducible."""
        raw = (ROOT / "planning/MASTER-MODULE-INDEX.md").read_bytes()
        oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        self.assertEqual(oid, ORIGINAL_INDEX_SHA)

    def test_08_obsolete_architecture_decision_superseded(self):
        """The new user decision is authoritative without rewriting audit history."""
        s = (ROOT / "docs/project-brain/16-DECISIONS-LEDGER.md").read_text()
        self.assertIn("## ADR-0047 - IRIS standalone Git-first operation", s)
        self.assertIn("Status: §SUPERSEDED_BY_ADR_0047§".replace("§", chr(96)), s)
        self.assertIn("Status: §APPROVED_USER_DIRECTIVE_2026_09_28§".replace("§", chr(96)), s)
        self.assertIn("M10–M13 runtime remains NOT_ADMITTED", s)

    def test_09_checkpoint_human_machine_mirrors(self):
        """Human mirror and machine nextStep stay byte/field equivalent."""
        cp = (ROOT / "docs/project-brain/13-CHECKPOINT.md").read_text()
        mirror = (ROOT / ".engineering/CHECKPOINT.md").read_text()
        m = json.loads((ROOT / ".engineering/CHECKPOINT.json").read_text())
        self.assertEqual(cp, mirror)
        self.assertEqual(m["nextStep"], cp.split("## NEXT STEP\n", 1)[1].strip())
        self.assertIn("IRIS-WO-0066", cp)
        self.assertIn("RETIRED", m["nextStep"])
        self.assertIn("H01–H04 OPEN HIGH_FOR_FUTURE_FREEZE", m["nextStep"])

    def test_10_owner_stops_and_source_hierarchy_preserved(self):
        """Retirement cannot turn open owner decisions into fake approvals."""
        s = (ROOT / ".engineering/SOURCE-HIERARCHY.md").read_text()
        n = json.loads((ROOT / ".engineering/CHECKPOINT.json").read_text())["nextStep"]
        self.assertIn("ACTIVE_MODULE_INDEX: §planning/MASTER-MODULE-INDEX-CURRENT.md§".replace("§", chr(96)), s)
        for marker in ("#82/#110/#112/#128/#145/#146/#147/#155", "DIRECTION_ONLY",
                       "C01 UNADOPTED_NOT_FROZEN", "M10/M11/M12/M13 runtime NOT_ADMITTED"):
            self.assertIn(marker, n)

    def test_11_no_live_import_of_deleted_client(self):
        """Production modules/scripts cannot import the retired client."""
        for root in [ROOT / "scripts", *ROOT.glob("iris_*")]:
            if root.is_dir():
                for path in root.glob("*.py"):
                    with self.subTest(path=str(path.relative_to(ROOT))):
                        self.assertNotRegex(
                            path.read_text(),
                            r"(?m)^\s*(?:from\s+scripts\.iris_|import\s+(?:scripts\.)?iris_)",
                        )

    def test_12_operator_notes_do_not_claim_to_uninstall_pc(self):
        """Operator still controls personal data, Docker volumes and global configs."""
        s = (ROOT / "docs/IRIS-STANDALONE-OPERATOR-NOTES.md").read_text()
        self.assertIn("outside", s)
        self.assertIn("Back up", s)
        self.assertIn("Do not remove Docker volumes", s)
        self.assertIn("python scripts/validate_governance.py", s)


    def test_13_any_reintroduced_project_mcp_config_is_rejected(self):
        """A vendor-neutral or even empty project MCP file may not bypass retirement."""
        with TemporaryDirectory() as temp:
            root = Path(temp)
            conf = root / ".codex/config.toml"
            conf.parent.mkdir(parents=True)
            for content in ("", "[mcp_servers.other]\ncommand = 'anything'\n"):
                with self.subTest(content=content):
                    conf.write_text(content, encoding="utf-8")
                    with self.assertRaisesRegex(SystemExit, "retired external integration path still present"):
                        reject_retired_operational_paths(root)

    def test_14_empty_standalone_tree_needs_no_external_context(self):
        """The dependency guard accepts a clean, standalone repository tree."""
        with TemporaryDirectory() as temp:
            self.assertIsNone(reject_retired_operational_paths(Path(temp)))


if __name__ == "__main__":
    unittest.main()
