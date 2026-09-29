"""One-off, inspectable source-only vendor retirement for the current IRIS tree.

Original files and their source-exact hashes remain in Git commit
95d58dd7a3b1275f4aaff4f147f2be852ecad588; never rewrite Git history.
The old immutable audit attachments matching this vendor are removed from
the present working tree rather than presenting rewritten evidence as original.
Dry-run is the default. Apply only on the dedicated WO0067 branch.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

from scripts.audit_retired_context import RETIRED_PATTERN, RETIRED_WORD, scan_tracked_tree

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = "95d58dd7a3b1275f4aaff4f147f2be852ecad588"
AUDIT_ONLY = (
    ".engineering/context-locks/",
    ".engineering/evidence/",
    ".engineering/work-orders/",
    "planning/checkpoints/",
    "planning/reviews/",
)
OLD = RETIRED_WORD
REPLACEMENTS = (
    (OLD.upper() + "MemoryIdentitySlicePort", "ProjectMemoryIdentitySlicePort"),
    (OLD.title() + "ContextEvidencePort", "ProjectContextEvidencePort"),
    (OLD.upper() + "_CONTEXT", "PROJECT_CONTEXT"),
    (OLD.upper() + "_MEMORY", "PROJECT_MEMORY"),
    (OLD.upper() + "_WORKSPACE", "PROJECT_WORKSPACE"),
    (OLD.lower() + "_namespace", "context_namespace"),
    (OLD.upper() + "_REPO_PATH", "RETIRED_CONTEXT_REPO_PATH"),
)
SOURCE_EXT = (".py", ".md", ".json", ".yml", ".yaml", ".toml", ".txt", ".ps1", ".sh")


def rewrite_text(raw: str) -> str:
    """Replace vendor-specific public identifiers consistently, never archive."""
    for old, new in REPLACEMENTS:
        raw = raw.replace(old, new)
    def neutral(match: re.Match[str]) -> str:
        word = match.group()
        if word.isupper():
            return "PROJECT_CONTEXT"
        if word.istitle():
            return "ProjectContext"
        return "project_context"
    return RETIRED_PATTERN.sub(neutral, raw)


def rewrite_path(name: str) -> str:
    replacement = rewrite_text(name)
    # Keep Python tests' descriptive filenames short and import-compatible.
    if replacement == "tests/test_wo0066_project_context_retirement.py":
        return "tests/test_wo0066_standalone_guard.py"
    return replacement


def plan(root: Path) -> tuple[list[str], dict[str, str], list[str]]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=root)
    names = [s.decode("utf-8", "surrogateescape") for s in raw.split(b"\0") if s]
    matched = {p for p, _ in scan_tracked_tree(root, names)}
    deleted: list[str] = []
    edited: dict[str, str] = {}
    moved: list[str] = []
    for name in names:
        if name not in matched:
            continue
        old_path = root / name
        if name.startswith(AUDIT_ONLY):
            deleted.append(name)
            continue
        if name in {".env.example", ".gitignore"}:
            text = old_path.read_text(encoding="utf-8")
            result = "\n".join(
                line for line in text.splitlines() if not RETIRED_PATTERN.search(line)
            ) + "\n"
        else:
            text = old_path.read_text(encoding="utf-8")
            result = rewrite_text(text)
        dest = rewrite_path(name)
        if dest != name:
            moved.append(name + " -> " + dest)
        if RETIRED_PATTERN.search(dest) or RETIRED_PATTERN.search(result):
            raise RuntimeError("Unretired reference in converted path " + name)
        if dest in edited:
            raise RuntimeError("Two originals target " + dest)
        edited[dest] = result
    if set(edited).intersection(deleted):
        raise RuntimeError("Edited/deleted path overlap")
    return deleted, edited, moved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    base = subprocess.check_output(["git", "merge-base", "HEAD", BASE_SHA], cwd=ROOT, text=True).strip()
    if base != BASE_SHA:
        raise RuntimeError("Source baseline drift; do not apply migration to unrelated branch")
    deleted, edited, moved = plan(ROOT)
    print("Source-only vendor retirement: " + ("APPLY" if args.apply else "DRY RUN"))
    print(f"Historic audit attachments removed from current tree: {len(deleted)}")
    print(f"Sanitized current source/doc/test paths: {len(edited)}")
    print(f"Renamed paths: {len(moved)}")
    for row in moved:
        print("  rename " + row)
    if args.apply:
        # git rm tracks removal of originals (all historic and renamed paths).
        current = set(subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
                      .decode("utf-8", "surrogateescape").strip("\0").split("\0"))
        for name in sorted(set(deleted) | {x.split(" -> ", 1)[0] for x in moved}):
            if name in current:
                subprocess.run(["git", "rm", "-f", "--", name], cwd=ROOT, check=True,
                               stdout=subprocess.DEVNULL)
        for name, content in edited.items():
            path = ROOT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
        remaining = scan_tracked_tree(ROOT)
        print(f"Remaining tracked-tree matches after apply: {len(remaining)}")
        if remaining:
            for name, n in remaining[:40]:
                print(f"  pending {name}: {n}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
