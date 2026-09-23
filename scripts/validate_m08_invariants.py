"""Validate frozen per-ID M08 proofs, 40 surfaces, and 15 absorbed components."""

from __future__ import annotations

import ast
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from iris_microbenchmark.families import M08_ABSORBED_COMPONENTS, M08_SURFACES, validate_surface_catalog  # noqa: E402
from iris_microbenchmark.invariants import M08_INVARIANTS, validate_invariant_catalog  # noqa: E402
from m08_invariant_proofs import PROOF_TARGET_CLAIMS  # noqa: E402

CONTRACT = ROOT / "planning/modules/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md"
SECTIONS = (
    ("S01", "## 7. S01 hard-invariant candidates"),
    ("S02", "## 20. S02 hard-invariant candidates"),
    ("S03", "## 33. S03 hard-invariant candidates"),
    ("S04", "## 45. S04 hard-invariant candidates"),
    ("S05", "## 58. S05 hard-invariant candidates"),
    ("FC", "# M09-M60 Forward Compatibility Incorporation"),
)
_INVARIANT_TARGET_CLASS = "TestM08InvariantProofs"


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
            match = re.fullmatch(r"(\d+)\.\s+.+", line)
            if match:
                result.append((int(match.group(1)), section, line))
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


def _target_node(target: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    try:
        relative_path, class_name, method_name = target.split("::")
    except ValueError:
        return None
    path = ROOT / relative_path
    if not path.is_file():
        return None
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return next((
                item for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method_name
            ), None)
    return None


def _target_has_assertion(target: str) -> bool:
    node = _target_node(target)
    if node is None:
        return False
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            return True
        if isinstance(child, ast.Call):
            name = child.func.attr if isinstance(child.func, ast.Attribute) else child.func.id if isinstance(child.func, ast.Name) else ""
            if name.startswith("assert"):
                return True
    return False


def _validate_generated_targets() -> None:
    proof_test = ROOT / "tests/test_m08_invariants.py"
    tree = ast.parse(proof_test.read_text(encoding="utf-8"), filename=str(proof_test))
    declared: tuple[int, ...] | None = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "PROVES_INVARIANTS" for target in node.targets):
            declared = ast.literal_eval(node.value)
            break
    expected = tuple(range(1, 331))
    if declared != expected:
        raise SystemExit("per-ID proof test must explicitly claim every frozen invariant exactly once")
    if not any(
        isinstance(node, ast.FunctionDef) and node.name == "_build_invariant_test"
        and any(isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "assert_semantic_target" for child in ast.walk(node))
        for node in tree.body
    ):
        raise SystemExit("per-ID proof test factory must execute its declared semantic target assertion")
    for item in M08_INVARIANTS:
        expected_target = f"tests/test_m08_invariants.py::{_INVARIANT_TARGET_CLASS}::test_m08_invariant_{item.number:04d}"
        if item.proof_target != expected_target:
            raise SystemExit(f"invariant {item.number} proof target is not its unique per-ID test")


def validate_frozen_invariant_records(
    requirements: tuple,
    canonical: tuple[tuple[int, str, str], ...],
) -> None:
    expected_numbers = tuple(range(1, 331))
    numbers = tuple(item.number for item in requirements)
    if len(requirements) != 330 or numbers != expected_numbers:
        raise SystemExit("M08 proof records must contain each invariant ID exactly once")
    if len({item.proof_id for item in requirements}) != 330:
        raise SystemExit("M08 invariant proof identities must be unique")
    expected_index = tuple((number, section, frozen_text) for number, section, frozen_text in canonical)
    indexed = tuple((item.number, item.section, item.frozen_text) for item in requirements)
    if len(canonical) != 330 or tuple(item[0] for item in canonical) != expected_numbers or indexed != expected_index:
        raise SystemExit("M08 frozen invariant text or section differs from its canonical source")
    for item in requirements:
        if hashlib.sha256(item.frozen_text.encode("utf-8")).hexdigest() != item.text_digest:
            raise SystemExit(f"M08 frozen text digest mismatch at invariant {item.number}")


def validate_proof_claims(
    requirements: tuple,
    target_claims: dict[str, tuple[tuple[int, str], ...]],
    asserted_targets: set[str],
) -> None:
    claimed = tuple(number for claims in target_claims.values() for number, _ in claims)
    if len(claimed) != 330 or tuple(sorted(claimed)) != tuple(range(1, 331)):
        raise SystemExit("semantic targets must explicitly claim every invariant ID exactly once")
    targets = {item.semantic_target for item in requirements}
    if set(target_claims) != targets:
        raise SystemExit("semantic proof claims contain missing or orphan targets")
    if asserted_targets != targets:
        raise SystemExit("each claimed semantic target must exist and contain executable assertions")
    for target, claims in target_claims.items():
        expected = tuple((item.number, item.assertion_id) for item in requirements if item.semantic_target == target)
        if tuple(claims) != expected:
            raise SystemExit(f"semantic target {target} claims IDs without matching per-ID proof declarations")
    if len({item.assertion_id for item in requirements}) != 330:
        raise SystemExit("M08 invariant assertion identities must be unique")


def validate_exact_invariants() -> None:
    validate_invariant_catalog()
    validate_surface_catalog()
    canonical = canonical_invariants()
    validate_frozen_invariant_records(M08_INVARIANTS, canonical)
    for item in M08_INVARIANTS:
        if item.proof_id != f"M08-INV-{item.number:04d}" or item.assertion_id != f"assert_m08_invariant_{item.number:04d}":
            raise SystemExit(f"M08 proof or assertion identity drifted at invariant {item.number}")

    asserted_targets = {target for target in PROOF_TARGET_CLAIMS if _target_has_assertion(target)}
    validate_proof_claims(M08_INVARIANTS, PROOF_TARGET_CLAIMS, asserted_targets)
    _validate_generated_targets()

    codes, names = canonical_inventory()
    if codes != tuple(item.code for item in M08_SURFACES):
        raise SystemExit("M08 40-surface catalog differs from the frozen contract order")
    if names != tuple(item.name for item in M08_ABSORBED_COMPONENTS):
        raise SystemExit("M08 15-component catalog differs from the frozen contract order")
    targets = {item.semantic_target for item in M08_INVARIANTS}
    targets.update(item.proof_target for item in M08_SURFACES)
    targets.update(item.proof_target for item in M08_ABSORBED_COMPONENTS)
    missing = sorted(target for target in targets if not _target_has_assertion(target))
    if missing:
        raise SystemExit("M08 proof targets do not resolve to tests with executable assertions: " + "; ".join(missing))


if __name__ == "__main__":
    validate_exact_invariants()
    print("M08 frozen proof catalog: 330/330 exact texts/digests and per-ID assertions; 40/40 surfaces; 15/15 components — PASS")
