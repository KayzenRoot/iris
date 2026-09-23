from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

from iris_production_state.families import M06_FAMILIES
from iris_production_state.invariants import M06_INVARIANTS
from iris_production_state.ports import M06_PORTS
from iris_production_state.validation import validate_kernel_catalog


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "planning" / "modules" / "M06-PRODUCTION-STATE-VERSIONING-INCREMENTAL-MEDIA-BUILD.md"
CONTRACT = ROOT / "planning" / "contracts" / "M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md"


class M06FrozenCatalogTests(unittest.TestCase):
    def test_frozen_catalog_matches_all_150_source_invariants(self) -> None:
        source = PLAN.read_text(encoding="utf-8")
        parsed = [
            (int(match.group(1)), match.group(2).strip())
            for line in source.splitlines()
            if (match := re.match(r"^\s*(\d+)\.\s+(.+?)\s*$", line)) and 1 <= int(match.group(1)) <= 150
        ]
        self.assertEqual(len(parsed), 150)
        self.assertEqual(tuple(item.number for item in M06_INVARIANTS), tuple(range(1, 151)))
        self.assertEqual(tuple((item.number, item.statement) for item in M06_INVARIANTS), tuple(parsed))

    def test_every_invariant_names_an_executable_family_proof(self) -> None:
        proof_methods: set[str] = set()
        for path in (ROOT / "tests").glob("test_m06_*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            proof_methods.update(
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_family_")
            )
        self.assertEqual({item.proof_target for item in M06_INVARIANTS} - proof_methods, set())
        for family in M06_FAMILIES:
            self.assertIn(family.proof_method, proof_methods)

    def test_frozen_families_ports_and_catalog_validation(self) -> None:
        contract = CONTRACT.read_text(encoding="utf-8")
        family_section = contract.split("## 3. Frozen technology families", 1)[1].split("## 4.", 1)[0]
        source_families = tuple(
            (match.group(1), match.group(2))
            for line in family_section.splitlines()
            if (match := re.match(r"^\s*\d+\. IRIS-([A-Z]{3}) (.+?)\s*$", line))
        )
        self.assertEqual(tuple((item.code, item.name) for item in M06_FAMILIES), source_families)
        self.assertEqual(len(M06_FAMILIES), 25)
        self.assertEqual(len(M06_PORTS), 20)
        report = validate_kernel_catalog()
        self.assertTrue(report.valid, report.findings)
        self.assertEqual((report.family_count, report.invariant_count, report.port_count), (25, 150, 20))

    def test_s01_revision_master_invariants(self) -> None:
        self.assertEqual(tuple(item.number for item in M06_INVARIANTS if item.section == "S01"), tuple(range(1, 31)))

    def test_s02_dependency_impact_invariants(self) -> None:
        self.assertEqual(tuple(item.number for item in M06_INVARIANTS if item.section == "S02"), tuple(range(31, 61)))

    def test_s03_selective_rebuild_invariants(self) -> None:
        self.assertEqual(tuple(item.number for item in M06_INVARIANTS if item.section == "S03"), tuple(range(61, 91)))

    def test_s04_reconstruction_invariants(self) -> None:
        self.assertEqual(tuple(item.number for item in M06_INVARIANTS if item.section == "S04"), tuple(range(91, 121)))

    def test_s05_rollback_cleanup_release_invariants(self) -> None:
        self.assertEqual(tuple(item.number for item in M06_INVARIANTS if item.section == "S05"), tuple(range(121, 151)))


if __name__ == "__main__":
    unittest.main()
