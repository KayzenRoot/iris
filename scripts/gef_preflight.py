from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

EXPECTED_VERSION = "1.0.0"
EXPECTED_COMMIT = "866fe3af8cccc65c929aaf6a47a924401fa448b3"
ROOT = Path(__file__).resolve().parents[1]


def resolve_gef_repo() -> Path:
    candidates: list[Path] = []
    configured = os.getenv("GEF_REPO_PATH")
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.extend((ROOT.parent / "gef-bootstrap", ROOT.parent / "GEF-Bootstrap"))
    for candidate in candidates:
        resolved = candidate.resolve()
        if (resolved / "package.json").is_file() and (resolved / ".git").exists():
            return resolved
    raise RuntimeError("GEF checkout not found. Place gef-bootstrap next to IRIS or set GEF_REPO_PATH.")


def main() -> int:
    repo = resolve_gef_repo()
    package = json.loads((repo / "package.json").read_text(encoding="utf-8"))
    if package.get("version") != EXPECTED_VERSION:
        raise RuntimeError(f"GEF version mismatch: {package.get('version')} != {EXPECTED_VERSION}")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    if head != EXPECTED_COMMIT:
        raise RuntimeError(f"GEF HEAD drift: {head} != {EXPECTED_COMMIT}; checkout v1.0.0.")
    print(f"GEF preflight: PASS v{EXPECTED_VERSION} @ {head}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"GEF preflight failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
