"""Check that the executable M07 proof map preserves the exact frozen inventory."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iris_hardware_genome.invariants import M07_INVARIANTS, validate_invariant_catalog  # noqa: E402

SECTIONS = (
    ("S01", "## 18. S01 hard-invariant candidates"),
    ("S02", "## 35. S02 hard-invariant candidates"),
    ("S03", "## 54. S03 hard-invariant candidates"),
    ("S04", "## 80. S04 hard-invariant candidates"),
    ("S05", "## 108. S05 hard-invariant candidates"),
    ("FC", "## 131. Scan-induced invariant candidates"),
)


def canonical_invariants() -> tuple[tuple[int, str, str], ...]:
    lines = (ROOT / "planning/modules/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md").read_text(encoding="utf-8").splitlines()
    result: list[tuple[int, str, str]] = []
    for section, marker in SECTIONS:
        start = lines.index(marker) + 1
        for line in lines[start:]:
            if line.startswith("## "):
                break
            match = re.match(r"^\s*(\d+)\.\s+(.+?)\s*$", line)
            if match:
                result.append((int(match.group(1)), section, match.group(2)))
    return tuple(result)


def validate_exact_invariants() -> None:
    validate_invariant_catalog()
    expected = canonical_invariants()
    actual = tuple((item.number, item.section, item.statement) for item in M07_INVARIANTS)
    if len(expected) != 235 or actual != expected:
        raise SystemExit("M07 invariant catalog differs from the frozen 235-item contract")
    targets = {item.proof_target for item in M07_INVARIANTS}
    required_prefixes = {
        "tests/test_m07_discovery.py::TestDiscovery",
        "tests/test_m07_capabilities.py::TestCapabilitySurfaces",
        "tests/test_m07_hardware_surfaces.py::TestPrecisionMediaTopology",
        "tests/test_m07_telemetry.py::TestTelemetry",
        "tests/test_m07_genome.py::TestGenome",
        "tests/test_m07_authority.py::TestProjectionAndRecovery",
    }
    if targets != required_prefixes:
        raise SystemExit("M07 invariant proof map has missing or unexpected focused test targets")


if __name__ == "__main__":
    validate_exact_invariants()
    print("M07 frozen invariant inventory: 235/235 exact, unique and indexed — PASS")
