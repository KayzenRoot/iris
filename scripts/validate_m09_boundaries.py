"""Static M09 semantic-kernel import and execution firewall."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "iris_resource_twin"

FORBIDDEN_IMPORTS = {
    "subprocess", "socket", "urllib", "requests", "httpx", "aiohttp", "sqlite3",
    "psycopg", "psycopg2", "sqlalchemy", "torch", "tensorflow", "cupy", "pycuda",
    "bpy", "maya", "blender", "pynvml", "gputil", "psutil", "os", "pathlib",
    "shutil", "ctypes", "iris_asset_dna", "iris_hardware_genome", "iris_microbenchmark",
    "iris_production_state", "iris_project_os", "iris_intent", "iris_quality",
}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__", "open", "input"}


def validate_boundaries(package: Path = PACKAGE) -> tuple[str, ...]:
    violations: list[str] = []
    for path in sorted(package.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(package.parent).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                names = []
            for name in names:
                root = name.split(".", 1)[0].lower()
                if root in FORBIDDEN_IMPORTS:
                    violations.append(f"{relative}:{node.lineno}: forbidden import {name}")
            if isinstance(node, ast.Call):
                called = node.func.id if isinstance(node.func, ast.Name) else None
                if called in FORBIDDEN_CALLS:
                    violations.append(f"{relative}:{node.lineno}: forbidden call {called}")
    return tuple(violations)


def main() -> int:
    findings = validate_boundaries()
    if findings:
        for finding in findings:
            print(f"FAIL {finding}")
        return 1
    print("M09 import/execution boundary: PASS")
    print("M09 core has no arbitrary code execution, shell, network, database, filesystem, hardware SDK, or downstream-module imports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
