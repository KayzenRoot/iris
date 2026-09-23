"""Static authority and side-effect firewall for the M08 semantic kernel."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "iris_microbenchmark"
FORBIDDEN_MODULE_ROOTS = {
    "bpy", "maya", "torch", "tensorflow", "onnxruntime", "cupy", "triton",
    "subprocess", "socket", "requests", "httpx", "urllib", "sqlite3", "sqlalchemy",
    "psycopg", "pymongo", "redis", "os", "pathlib", "importlib", "ctypes",
    "multiprocessing", "threading", "asyncio",
}
FORBIDDEN_BUILTINS = {"eval", "exec", "compile", "__import__", "open", "input"}
FORBIDDEN_IO_CALLS = {"system", "popen", "Popen", "run", "call", "check_call", "check_output", "urlopen", "create_engine", "connect"}
FORBIDDEN_IRIS_MODULES = {
    "iris_asset_dna", "iris_m09", "iris_m10", "iris_m11", "iris_m12", "iris_m13",
    "iris_m14", "iris_m16", "iris_m17", "iris_m24", "iris_m48", "iris_m50",
    "iris_m51", "iris_m53", "iris_m54", "iris_m55", "iris_m56", "iris_m57",
    "iris_m58", "iris_m60",
}
FORBIDDEN_AUTHORITY_SYMBOLS = {
    "ExecutionPlan", "VRAMLease", "RAMLease", "WorkerLifecycle", "PlacementDecision",
    "SchedulerDecision", "ModelFitness", "QualityScore", "ProviderWorkflow", "ProviderCompiler",
    "ReleaseAcceptance", "RightsDecision", "PhysicalStorage", "DashboardAggregate",
    "AgentOrchestrator", "reserve_vram", "evict_allocation", "schedule_execution", "kill_process",
    "set_voltage", "set_clock", "set_fan_curve", "set_os_power_policy",
    "kill_unrelated_process", "suspend_unrelated_process", "evict_unrelated_allocation", "stress_test",
}


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
                if root in FORBIDDEN_MODULE_ROOTS or root in FORBIDDEN_IRIS_MODULES:
                    raise SystemExit(f"forbidden M08 dependency {name!r} in {path.relative_to(ROOT)}")
            if isinstance(node, (ast.Name, ast.Attribute)):
                symbol = node.id if isinstance(node, ast.Name) else node.attr
                if symbol in FORBIDDEN_AUTHORITY_SYMBOLS:
                    raise SystemExit(f"downstream authority symbol {symbol!r} leaked into {path.relative_to(ROOT)}")
            if isinstance(node, ast.Call):
                func = node.func
                call_name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
                forbidden = call_name in FORBIDDEN_BUILTINS if isinstance(func, ast.Name) else call_name in FORBIDDEN_IO_CALLS if isinstance(func, ast.Attribute) else False
                if forbidden:
                    raise SystemExit(f"forbidden M08 dynamic execution or I/O call {call_name!r} in {path.relative_to(ROOT)}")
        checked.append(path.relative_to(ROOT).as_posix())
    if not checked:
        raise SystemExit("M08 package contains no Python modules")
    return tuple(checked)


if __name__ == "__main__":
    modules = validate_boundaries()
    print(f"M08 forbidden-import, dynamic-execution, I/O and authority firewall: {len(modules)} modules — PASS")
