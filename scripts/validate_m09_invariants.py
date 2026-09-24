"""Verify exact frozen M09 surface/invariant catalogs and executable proof mapping."""

from __future__ import annotations

import ast
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PLAN = ROOT / "planning/modules/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md"
REVIEW = ROOT / "planning/reviews/M09-FINAL-TECHNOLOGY-REVIEW.md"
TESTS = ROOT / "tests/test_m09_invariants.py"
CLAIMS = ROOT / "tests/m09_proof_claims.py"


def _frozen_invariants() -> tuple[tuple[int, str, str], ...]:
    section: str | None = None
    records: list[tuple[int, str, str]] = []
    for line in PLAN.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line
        match = re.match(r"^(\d+)\.\s+(.+?)\s*$", line)
        if match and "hard invariants" in (section or "").lower():
            session = section.split()[1] if section and section.startswith("## S") else "FC"
            records.append((int(match.group(1)), session, match.group(2)))
    return tuple(records)


def _review_catalog() -> tuple[tuple[str, str, str], tuple[tuple[str, str], ...]]:
    surfaces: list[tuple[str, str, str]] = []
    absorbed: list[tuple[str, str]] = []
    section: str | None = None
    mode = "surface"
    for line in REVIEW.read_text(encoding="utf-8").splitlines():
        if line.startswith("### Independent mandatory surfaces"):
            match = re.search(r"S0[1-5]", line)
            if match is None:
                raise ValueError("technology review has a malformed surface section")
            section = match.group(0)
            mode = "surface"
            continue
        if line.startswith("## Mandatory absorbed components"):
            section = "ABSORBED"
            mode = "absorbed"
            continue
        if line.startswith("## Cross-cutting mandatory components"):
            mode = "done"
            continue
        match = re.match(r"^\d+\. \*\*(.+?)\*\* — (.+?)\.?$", line)
        if match and mode == "surface" and section:
            surfaces.append((section, match.group(1), match.group(2)))
        elif match and mode == "absorbed":
            absorbed.append((match.group(1), match.group(2)))
    return tuple(surfaces), tuple(absorbed)


def _test_methods() -> dict[str, ast.FunctionDef]:
    tree = ast.parse(TESTS.read_text(encoding="utf-8"), filename=str(TESTS))
    result: dict[str, ast.FunctionDef] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    result[f"{node.name}::{child.name}"] = child
    return result


def _proof_claims() -> dict[str, tuple[int, ...]]:
    tree = ast.parse(CLAIMS.read_text(encoding="utf-8"), filename=str(CLAIMS))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "M09_PROOF_CLAIMS" for target in node.targets):
            value = ast.literal_eval(node.value)
            if type(value) is not dict or any(type(key) is not str or type(ids) is not tuple for key, ids in value.items()):
                raise ValueError("proof claims must be a literal target-to-ID mapping")
            return value
    raise ValueError("explicit invariant claim map is missing")


def validate_catalogs_and_proofs() -> tuple[str, ...]:
    from iris_resource_twin import M09_ABSORBED_COMPONENTS, M09_INVARIANTS, M09_SURFACES, validate_invariant_claim_groups

    failures: list[str] = []
    expected_invariants = _frozen_invariants()
    if len(expected_invariants) != 514 or tuple(item[0] for item in expected_invariants) != tuple(range(1, 515)):
        failures.append("frozen contract does not contain exact invariant range 1..514")
    if len(M09_INVARIANTS) != 514:
        failures.append(f"package invariant catalog has {len(M09_INVARIANTS)} entries")
    for (number, session, text), record in zip(expected_invariants, M09_INVARIANTS):
        exact_text = f"{number}. {text}"
        digest = hashlib.sha256(exact_text.encode("utf-8")).hexdigest()
        if (record.number, record.section, record.frozen_text, record.text_digest) != (number, session, text, digest):
            failures.append(f"invariant {number} text, section, or fingerprint differs from frozen contract")

    expected_surfaces, expected_absorbed = _review_catalog()
    if len(expected_surfaces) != 83 or len(M09_SURFACES) != 83:
        failures.append("surface catalog is not exactly 83 entries")
    else:
        actual = tuple((item.section, item.name, item.obligation) for item in M09_SURFACES)
        if actual != expected_surfaces:
            failures.append("surface catalog differs from the independent technology review")
    if len(expected_absorbed) != 15 or len(M09_ABSORBED_COMPONENTS) != 15:
        failures.append("absorbed-component catalog is not exactly 15 entries")
    elif tuple((item.name, item.obligation) for item in M09_ABSORBED_COMPONENTS) != expected_absorbed:
        failures.append("absorbed-component catalog differs from the independent technology review")

    methods = _test_methods()
    try:
        claims = _proof_claims()
        failures.extend(validate_invariant_claim_groups(M09_INVARIANTS, claims))
    except (SyntaxError, ValueError) as error:
        claims = {}
        failures.append(f"explicit invariant claim map is invalid: {error}")
    semantic_methods = {record.semantic_target for record in M09_INVARIANTS}
    for record in M09_INVARIANTS:
        qualified = record.proof_target.removeprefix("tests/test_m09_invariants.py::")
        wrapper = methods.get(qualified)
        if wrapper is None:
            failures.append(f"invariant {record.number} proof target is absent: {record.proof_target}")
            continue
        called_targets = {
            node.func.attr for node in ast.walk(wrapper)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        if record.semantic_target not in called_targets:
            failures.append(f"invariant {record.number} wrapper does not invoke {record.semantic_target}")
        if record.assertion_id not in {node.value for node in ast.walk(wrapper) if isinstance(node, ast.Constant) and type(node.value) is str}:
            failures.append(f"invariant {record.number} wrapper does not assert its exact assertion ID")
    for target in semantic_methods:
        if f"TestM09SemanticProofs::{target}" not in methods:
            failures.append(f"semantic proof target is not executable: {target}")
    if not validate_safe_test_surface(methods, claims):
        failures.append("proof file lacks assertion-bearing semantic proof methods")
    return tuple(failures)


def validate_safe_test_surface(methods: dict[str, ast.FunctionDef], claims: dict[str, tuple[int, ...]]) -> bool:
    semantic = [node for key, node in methods.items() if key.startswith("TestM09SemanticProofs::")]
    targets = {key.split("::", 1)[1] for key in methods if key.startswith("TestM09SemanticProofs::")}
    if not semantic or not set(claims).issubset(targets):
        return False
    for target in claims:
        method = methods[f"TestM09SemanticProofs::{target}"]
        calls = [node for node in ast.walk(method) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
        called_names = {node.func.id for node in ast.walk(method) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        if not any(node.func.attr.startswith("assert") for node in calls):
            return False
        # Each grouped semantic proof must call at least one concrete test method.
        if target in {"test_every_claim_group_matches_frozen_semantic_targets", "test_claim_group_validation_rejects_missing_duplicate_and_orphan_ids"}:
            if "validate_invariant_claim_groups" not in called_names:
                return False
        elif not any(node.func.attr.startswith("test_") and node.func.attr != target for node in calls):
            return False
    return True


def main() -> int:
    failures = validate_catalogs_and_proofs()
    if failures:
        for item in failures:
            print(f"FAIL {item}")
        return 1
    print("M09 frozen catalogs and executable invariant mappings: PASS (83 surfaces, 15 components, 514 invariants)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
