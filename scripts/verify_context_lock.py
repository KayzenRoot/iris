"""Verify one PR's immutable GEF Context Lock against its actual Git base and diff.

This is a local Git evidence check, not an owner contract/security attestation or
an assertion that an external HIVE/M09/M11 integration has been executed.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SHA40 = re.compile(r"[0-9a-f]{40}\Z")
LOCK_PREFIX = ".engineering/context-locks/"
LOCK_SUFFIX = ".json"

MANDATORY_SOURCE_PATHS = frozenset(['AGENTS.md','.engineering/SOURCE-HIERARCHY.md','docs/project-brain/13-CHECKPOINT.md','docs/project-brain/16-DECISIONS-LEDGER.md','docs/project-brain/03-SCOPE.md','docs/project-brain/15-DEFINITION-OF-DONE.md','docs/project-brain/04-ARCHITECTURE.md','docs/project-brain/02-REQUIREMENTS.md'])


class ContextLockError(ValueError):
    """A PR lacks verifiable, internally consistent Git source/scope evidence."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContextLockError(message)


def safe_path(path: object, label: str) -> str:
    require(isinstance(path, str) and bool(path), f"{label}: path is required")
    require(not path.startswith("/") and "\\" not in path and "\x00" not in path, f"{label}: unsafe path")
    require(all(part not in ("", ".", "..") and ":" not in part for part in path.split("/")), f"{label}: noncanonical path")
    return path


def check_sha(value: object, label: str) -> str:
    require(isinstance(value, str) and SHA40.fullmatch(value) is not None, f"{label}: expected lowercase full Git SHA")
    return value


def verify_lock(
    lock: dict[str, object], *,
    base_sha: str,
    base_tree_sha: str,
    base_blobs: dict[str, str],
    changed_paths: set[str],
    lock_path: str,
) -> None:
    """Pure, testable validation of one newly authored context lock."""
    safe_path(lock_path, "lock")
    require(lock_path.startswith(LOCK_PREFIX) and lock_path.endswith(LOCK_SUFFIX), "lock path outside context-locks")
    require(lock.get("schemaVersion") == "iris-context-lock-v1", "unsupported lock schema")
    require(isinstance(lock.get("workOrder"), str) and bool(lock["workOrder"]), "workOrder is required")
    require(type(lock.get("issue")) is int and lock["issue"] > 0, "positive issue number required")
    require(check_sha(lock.get("baseSha"), "lock.baseSha") == check_sha(base_sha, "PR base"), "stale/mismatched lock base")
    require(check_sha(lock.get("baseTreeSha"), "lock.baseTreeSha") == check_sha(base_tree_sha, "actual base tree"), "base tree mismatch")
    snapshot = lock.get("sourceSnapshot")
    require(isinstance(snapshot, dict) and snapshot.get("algorithm") == "Git blob SHA-1", "unsupported source fingerprint algorithm")
    if snapshot.get("baseSha") is not None:
        require(snapshot["baseSha"] == base_sha, "snapshot base SHA mismatch")
    if snapshot.get("baseTreeSha") is not None:
        require(snapshot["baseTreeSha"] == base_tree_sha, "snapshot tree SHA mismatch")
    sources = lock.get("criticalSources")
    require(isinstance(sources, list) and len(sources) > 0, "missing critical sources")
    source_paths: set[str] = set()
    for index, row in enumerate(sources):
        require(isinstance(row, dict), f"source {index}: invalid record")
        path = safe_path(row.get("path"), f"source {index}")
        require(path not in source_paths, f"duplicate critical source: {path}")
        source_paths.add(path)
        expected = check_sha(row.get("gitBlobSha1"), f"source {path}")
        require(base_blobs.get(path) == expected, f"source Git blob mismatch or absent at base: {path}")
    missing = sorted(MANDATORY_SOURCE_PATHS - source_paths)
    require(not missing, f"missing canonical mandatory sources: {missing}")
    for field in ("expected", "checked", "matched"):
        require(type(snapshot.get(field)) is int and snapshot[field] == len(sources), f"source count {field} mismatch")
    require(type(snapshot.get("mismatches")) is int and snapshot["mismatches"] == 0, "source mismatches must be zero")
    allowed = lock.get("authorizedChangedFiles")
    require(isinstance(allowed, list) and bool(allowed), "empty or missing PR change allowlist")
    allowed_paths: set[str] = set()
    for index, value in enumerate(allowed):
        path = safe_path(value, f"allowlist {index}")
        require(path not in allowed_paths, f"duplicate authorized path: {path}")
        allowed_paths.add(path)
    require(lock_path in changed_paths and lock_path in allowed_paths, "new lock must itself be a changed, authorized file")
    require(bool(changed_paths), "PR must contain changed files")
    for path in changed_paths:
        safe_path(path, "PR diff")
    require(changed_paths <= allowed_paths, f"unauthorized PR diff paths: {sorted(changed_paths - allowed_paths)}")


def git(repo: Path, *args: str) -> bytes:
    command = ["git", *args]
    try:
        return subprocess.run(command, cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContextLockError(f"local Git evidence unavailable for {args[0]}") from exc


def base_blob_map(repo: Path, base_sha: str) -> dict[str, str]:
    """Read Git object IDs without trusting workspace files or loose JSON claims."""
    raw = git(repo, "ls-tree", "-r", "-z", base_sha)
    result: dict[str, str] = {}
    for entry in filter(None, raw.split(b"\x00")):
        header, path_bytes = entry.split(b"\t", 1)
        mode, kind, sha_bytes = header.split(b" ", 2)
        if kind == b"blob":
            result[path_bytes.decode("utf-8")] = sha_bytes.decode("ascii")
    return result


def reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def verify_current_pr(repo: Path, *, base_sha: str, head_sha: str) -> list[str]:
    """Check the actual base tree, changed lock(s) and full changed-file allowlist."""
    check_sha(base_sha, "PR base")
    check_sha(head_sha, "PR head")
    actual_head = git(repo, "rev-parse", "HEAD").decode("ascii").strip()
    require(actual_head == head_sha, "checkout is not the exact PR head")
    actual_base = git(repo, "rev-parse", f"{base_sha}^{{commit}}").decode("ascii").strip()
    require(actual_base == base_sha, "declared base commit is not available")
    merge_base = git(repo, "merge-base", base_sha, head_sha).decode("ascii").strip()
    require(merge_base == base_sha, "PR head is not based on its declared base; rebase required")
    tree_sha = git(repo, "rev-parse", f"{base_sha}^{{tree}}").decode("ascii").strip()
    base_blobs = base_blob_map(repo, base_sha)
    changed_bytes = git(repo, "diff", "--name-only", "--no-renames", "-z", base_sha, head_sha)
    changed_paths = {item.decode("utf-8") for item in filter(None, changed_bytes.split(b"\x00"))}
    changed_locks = sorted(path for path in changed_paths if path.startswith(LOCK_PREFIX) and path.endswith(LOCK_SUFFIX))
    require(bool(changed_locks), "PR must change at least one governed Context Lock")
    for lock_path in changed_locks:
        safe_path(lock_path, "changed lock")
        payload = git(repo, "show", f"{head_sha}:{lock_path}").decode("utf-8")
        lock = json.loads(payload, object_pairs_hook=reject_duplicate_json_keys)
        require(isinstance(lock, dict), "context lock JSON root must be an object")
        verify_lock(lock, base_sha=base_sha, base_tree_sha=tree_sha, base_blobs=base_blobs, changed_paths=changed_paths, lock_path=lock_path)
    return changed_locks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-sha", required=True, help="Trusted GitHub PR base SHA")
    parser.add_argument("--head-sha", required=True, help="Trusted GitHub PR head SHA")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        locks = verify_current_pr(args.repo, base_sha=args.base_sha, head_sha=args.head_sha)
    except (ContextLockError, json.JSONDecodeError, UnicodeError) as exc:
        print(f"CONTEXT LOCK VERIFICATION FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"IRIS Context Lock: PASS {len(locks)} changed lock(s), exact base source fingerprints and PR diff allowlists")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
