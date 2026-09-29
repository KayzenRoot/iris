"""Audit the current Git-tracked IRIS source tree for retired vendor references.

The detector intentionally reconstructs the old four-letter token from bytes:
its own source file and tests therefore cannot accidentally trigger the audit.
Git HISTORY (old commits) is outside the current tracked tree, not rewritten.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RETIRED_WORD = bytes.fromhex("68697665").decode("ascii")
RETIRED_PATTERN = re.compile(r"(?<![a-z])" + re.escape(RETIRED_WORD), re.I)


def scan_tracked_tree(root: Path = PROJECT_ROOT, paths: list[str] | None = None) -> list[tuple[str, int]]:
    """Return (path, matched-line-or-filename count), not misleading archive false hits."""
    if paths is None:
        raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=root)
        paths = [s.decode("utf-8", "surrogateescape") for s in raw.split(b"\0") if s]
    issues: list[tuple[str, int]] = []
    for name in paths:
        filename_bad = bool(RETIRED_PATTERN.search(name))
        path = root / name
        if not path.is_file():
            issues.append((name, 1))
            continue
        content = path.read_bytes()
        if b"\0" in content:
            if filename_bad:
                issues.append((name, 1))
            continue
        lines = content.decode("utf-8", errors="replace").splitlines()
        bad_lines = sum(bool(RETIRED_PATTERN.search(line)) for line in lines)
        if bad_lines or filename_bad:
            issues.append((name, bad_lines + int(filename_bad)))
    return sorted(issues)


def main() -> int:
    matches = scan_tracked_tree()
    print("IRIS retired external context audit: " + ("FAIL" if matches else "PASS"))
    print(f"Remaining affected tracked paths: {len(matches)}")
    for name, count in matches:
        print(f"  {name}: {count} flagged line(s)/name(s)")
    return 1 if matches else 0


if __name__ == "__main__":
    raise SystemExit(main())
