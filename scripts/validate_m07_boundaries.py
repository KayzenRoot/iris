"""Static import and execution boundary check for the M07 semantic kernel."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "iris_hardware_genome"
FORBIDDEN_MODULE_ROOTS = {
    "bpy", "maya", "torch", "tensorflow", "onnxruntime", "cupy", "triton",
    "subprocess", "socket", "requests", "httpx", "urllib", "sqlite3", "sqlalchemy",
    "psycopg", "pymongo", "redis", "os",
}
FORBIDDEN_BUILTINS = {"eval", "exec", "compile", "__import__"}
FORBIDDEN_IO_CALLS = {"system", "popen", "urlopen", "create_engine", "connect"}
FORBIDDEN_IRIS_MODULES = {"iris_asset_dna", "iris_m08", "iris_m09", "iris_m10", "iris_m16"}


def validate_boundaries() -> tuple[str, ...]:
    checked: list[str] = []
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                names = []
            for name in names:
                root = name.split(".", 1)[0]
                if root in FORBIDDEN_MODULE_ROOTS or name in FORBIDDEN_IRIS_MODULES:
                    raise SystemExit(f"forbidden M07 dependency {name!r} in {path.relative_to(ROOT)}")
            if isinstance(node, ast.Call):
                func = node.func
                call_name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
                forbidden = call_name in FORBIDDEN_BUILTINS if isinstance(func, ast.Name) else call_name in FORBIDDEN_IO_CALLS if isinstance(func, ast.Attribute) else False
                if forbidden:
                    raise SystemExit(f"forbidden M07 execution/I/O call {call_name!r} in {path.relative_to(ROOT)}")
        checked.append(path.relative_to(ROOT).as_posix())
    if not checked:
        raise SystemExit("M07 package contains no Python modules")
    return tuple(checked)


if __name__ == "__main__":
    modules = validate_boundaries()
    print(f"M07 forbidden-import and dynamic-execution boundary: {len(modules)} modules — PASS")
