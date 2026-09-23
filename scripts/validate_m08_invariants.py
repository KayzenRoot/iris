"""Validate M08's frozen 330-invariant, 40-surface and 15-component proof map."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iris_microbenchmark.families import M08_ABSORBED_COMPONENTS, M08_SURFACES, validate_surface_catalog  # noqa: E402
from iris_microbenchmark.invariants import M08_INVARIANTS, validate_invariant_catalog  # noqa: E402

CONTRACT = ROOT / "planning/modules/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md"
SECTIONS = (
    ("S01", "## 7. S01 hard-invariant candidates"),
    ("S02", "## 20. S02 hard-invariant candidates"),
    ("S03", "## 33. S03 hard-invariant candidates"),
    ("S04", "## 45. S04 hard-invariant candidates"),
    ("S05", "## 58. S05 hard-invariant candidates"),
    ("FC", "# M09-M60 Forward Compatibility Incorporation"),
)


def canonical_invariants() -> tuple[tuple[int, str, str], ...]:
    lines = CONTRACT.read_text(encoding="utf-8").splitlines()
    result: list[tuple[int, str, str]] = []
    for section, marker in SECTIONS:
        start = lines.index(marker) + 1
        for line in lines[start:]:
            if section == "FC" and line.startswith("# M08 Module Contract Freeze"):
                break
            if section != "FC" and line.startswith("## "):
                break
            match = re.match(r"^\s*(\d+)\.\s+(.+?)\s*$", line)
            if match:
                result.append((int(match.group(1)), section, match.group(2)))
    return tuple(result)


def canonical_inventory() -> tuple[tuple[str, ...], tuple[str, ...]]:
    text = CONTRACT.read_text(encoding="utf-8")
    surface = re.search(r"Independent mandatory technology surfaces: \*\*40\*\*:\s*\n([^\n]+)", text)
    absorbed = re.search(r"Mandatory absorbed components: \*\*15\*\*:\s*\n((?:\d+\. [^\n]+\n?){15})", text)
    if surface is None or absorbed is None:
        raise SystemExit("M08 canonical 40+15 inventory markers are absent")
    codes = tuple(item.strip().rstrip(".") for item in surface.group(1).split(","))
    components = tuple(re.sub(r"^\d+\.\s+", "", line.strip()).rstrip(".") for line in absorbed.group(1).splitlines())
    return codes, components


def _target_exists(target: str) -> bool:
    try:
        relative_path, class_name, method_name = target.split("::")
    except ValueError:
        return False
    path = ROOT / relative_path
    if not path.is_file():
        return False
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return any(isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method_name for item in node.body)
    return False


def validate_exact_invariants() -> None:
    validate_invariant_catalog()
    validate_surface_catalog()
    canonical = canonical_invariants()
    indexed = tuple((item.number, item.section) for item in M08_INVARIANTS)
    expected_index = tuple((number, section) for number, section, _ in canonical)
    if len(canonical) != 330 or tuple(item[0] for item in canonical) != tuple(range(1, 331)):
        raise SystemExit("M08 frozen invariant source must contain exact unique numbers 1..330")
    if indexed != expected_index:
        raise SystemExit("M08 executable invariant index differs from the frozen source sections")
    if any(not statement.strip() for _, _, statement in canonical):
        raise SystemExit("M08 frozen invariant statement cannot be empty")
    codes, names = canonical_inventory()
    if codes != tuple(item.code for item in M08_SURFACES):
        raise SystemExit("M08 40-surface catalog differs from the frozen contract order")
    if names != tuple(item.name for item in M08_ABSORBED_COMPONENTS):
        raise SystemExit("M08 15-component catalog differs from the frozen contract order")
    targets = {item.proof_target for item in M08_INVARIANTS}
    targets.update(item.proof_target for item in M08_SURFACES)
    targets.update(item.proof_target for item in M08_ABSORBED_COMPONENTS)
    missing = sorted(target for target in targets if not _target_exists(target))
    if missing:
        raise SystemExit("M08 proof targets do not resolve to existing focused test methods: " + "; ".join(missing))


if __name__ == "__main__":
    validate_exact_invariants()
    print("M08 frozen invariant inventory: 330/330; technology surfaces: 40/40; absorbed components: 15/15 — PASS")
