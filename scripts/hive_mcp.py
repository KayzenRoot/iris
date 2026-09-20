from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def resolve_hive_repo() -> Path:
    candidates: list[Path] = []
    configured = os.getenv("HIVE_REPO_PATH")
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.extend((ROOT.parent / "hive", ROOT.parent / "Hive"))
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if (resolved / "docker-compose.yml").is_file() and (resolved / "backend").is_dir():
            return resolved
    raise RuntimeError("HIVE v1.0.0 checkout not found. Place HIVE next to IRIS or set HIVE_REPO_PATH.")


def build_mcp_command() -> tuple[Path, list[str]]:
    hive_repo = resolve_hive_repo()
    return hive_repo, ["docker", "compose", "exec", "-T", "api", "python", "-m", "app.mcp_server"]


def main() -> int:
    hive_repo, command = build_mcp_command()
    try:
        completed = subprocess.run(command, cwd=hive_repo, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError("Docker CLI is not available on PATH.") from exc
    return completed.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"HIVE MCP bootstrap failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
