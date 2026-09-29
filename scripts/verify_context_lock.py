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

# Strict exception for a GitHub-authenticated Dependabot one-line action SHA bump.
DEPENDABOT_PIN_ONLY = "DEPENDABOT_ACTION_PIN_ONLY"
WORKFLOW_PATH = ".github/workflows/governance.yml"
BOT_PIN_LINE = re.compile(r"        uses: actions/(checkout|setup-python)@([0-9a-f]{40}) # v([0-9]+(?:\.[0-9]+){0,2})\Z")

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


def latest_original_base_lock_path(base_blobs: dict[str, str]) -> str:
    """Find the single newest numbered original Context Lock in the trusted base."""
    candidates: list[tuple[int, str]] = []
    for path in base_blobs:
        if not path.startswith(LOCK_PREFIX):
            continue
        name = path[len(LOCK_PREFIX):]
        match = re.fullmatch(r"IRIS-WO-(\d+)(?:-[A-Za-z0-9][A-Za-z0-9-]*)?\.json", name)
        if match is not None:
            candidates.append((int(match.group(1)), path))
    require(bool(candidates), "missing numbered original-base Context Lock")
    latest_number = max(number for number, _ in candidates)
    latest = sorted(path for number, path in candidates if number == latest_number)
    require(len(latest) == 1, f"ambiguous latest original-base Context Lock: {latest}")
    return latest[0]


def verify_lock(
    lock: dict[str, object], *,
    base_sha: str,
    base_tree_sha: str,
    base_blobs: dict[str, str],
    changed_paths: set[str],
    lock_path: str,
    inherited_source_paths: set[str] | None = None,
    base_modes: dict[str, str] | None = None,
) -> None:
    """Pure, testable validation; optionally preserve the prior base-locked source set."""
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
        if base_modes is not None:
            require(base_modes.get(path) == "100644",
                    f"pinned critical source must have regular non-executable Git mode 100644: {path}")
    missing = sorted(MANDATORY_SOURCE_PATHS - source_paths)
    require(not missing, f"missing canonical mandatory sources: {missing}")
    anchor = lock.get("sourceManifestAnchor")
    if anchor is not None:
        require(isinstance(anchor, dict) and set(anchor) == {"path", "gitBlobSha1"},
                "invalid base source manifest anchor")
        anchor_path = safe_path(anchor["path"], "source manifest anchor")
        require(anchor_path.startswith(LOCK_PREFIX) and anchor_path.endswith(LOCK_SUFFIX)
                and anchor_path != lock_path, "invalid base Context Lock anchor path")
        require(base_blobs.get(anchor_path) == check_sha(anchor["gitBlobSha1"], "anchor gitBlobSha1"),
                "source manifest anchor blob mismatch or absent at original base")
        require(anchor_path == latest_original_base_lock_path(base_blobs),
                "anchor is not the latest original-base Context Lock")
        require(anchor_path in source_paths, "source manifest anchor itself must be pinned")
        require(isinstance(inherited_source_paths, set) and bool(inherited_source_paths),
                "missing trusted original-base source manifest")
        for inherited_path in inherited_source_paths:
            safe_path(inherited_path, "inherited source")
        omitted = sorted(inherited_source_paths - source_paths)
        require(not omitted, f"missing inherited original-base critical sources: {omitted}")
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


def base_blob_map(repo: Path, base_sha: str, *, modes_out: dict[str, str] | None = None) -> dict[str, str]:
    """Read exact Git blob IDs and optional modes without trusting workspace files."""
    raw = git(repo, "ls-tree", "-r", "-z", base_sha)
    result: dict[str, str] = {}
    for entry in filter(None, raw.split(b"\x00")):
        header, path_bytes = entry.split(b"\t", 1)
        mode, kind, sha_bytes = header.split(b" ", 2)
        if kind == b"blob":
            path = path_bytes.decode("utf-8")
            result[path] = sha_bytes.decode("ascii")
            if modes_out is not None:
                modes_out[path] = mode.decode("ascii")
    return result


def reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def verify_dependabot_action_pin(
    repo: Path, *, base_sha: str, head_sha: str,
    changed_paths: set[str], pr_author: str, pr_head_ref: str,
    pr_head_repo: str, pr_base_repo: str,
) -> None:
    """Accept *only* a trusted bot's single workflow action pin-line change.

    CI obtains PR metadata from the GitHub event, never from a PR-authored file.
    Passing this check does not authorize merging an unreviewed action upgrade.
    """
    require(pr_author == "dependabot[bot]", "dependabot exception requires GitHub bot author")
    require(bool(pr_base_repo) and pr_head_repo == pr_base_repo, "dependabot exception requires same-repository head")
    require(pr_head_ref.startswith("dependabot/github_actions/actions/"), "unexpected dependabot branch")
    require(changed_paths == {WORKFLOW_PATH}, "dependabot exception allows exactly the Governance workflow")
    old = git(repo, "ls-tree", base_sha, "--", WORKFLOW_PATH).decode("ascii").strip()
    new = git(repo, "ls-tree", head_sha, "--", WORKFLOW_PATH).decode("ascii").strip()
    require(old.startswith("100644 blob ") and new.startswith("100644 blob "), "workflow must remain a regular non-executable Git file")
    diff = git(repo, "diff", "--no-ext-diff", "--no-renames", "--unified=0",
               base_sha, head_sha, "--", WORKFLOW_PATH).decode("utf-8")
    lines = diff.splitlines()
    require(lines and lines[0] == f"diff --git a/{WORKFLOW_PATH} b/{WORKFLOW_PATH}",
            "unexpected workflow patch")
    removed = [s[1:] for s in lines if s.startswith("-") and not s.startswith("---")]
    added = [s[1:] for s in lines if s.startswith("+") and not s.startswith("+++")]
    require(len(removed) == 1 and len(added) == 1, "dependabot patch must change exactly one action pin line")
    old_match, new_match = BOT_PIN_LINE.fullmatch(removed[0]), BOT_PIN_LINE.fullmatch(added[0])
    require(old_match is not None and new_match is not None, "dependabot patch must use full pinned official action SHA syntax")
    require(old_match.group(1) == new_match.group(1), "dependabot patch cannot switch action names")
    require(old_match.group(2) != new_match.group(2), "dependabot action SHA must actually change")


def verify_current_pr(
    repo: Path, *, base_sha: str, head_sha: str,
    pr_author: str = "", pr_head_ref: str = "",
    pr_head_repo: str = "", pr_base_repo: str = "",
) -> list[str]:
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
    base_modes: dict[str, str] = {}
    base_blobs = base_blob_map(repo, base_sha, modes_out=base_modes)
    changed_bytes = git(repo, "diff", "--name-only", "--no-renames", "-z", base_sha, head_sha)
    changed_paths = {item.decode("utf-8") for item in filter(None, changed_bytes.split(b"\x00"))}
    changed_locks = sorted(path for path in changed_paths if path.startswith(LOCK_PREFIX) and path.endswith(LOCK_SUFFIX))
    if not changed_locks and pr_author == "dependabot[bot]":
        verify_dependabot_action_pin(
            repo, base_sha=base_sha, head_sha=head_sha, changed_paths=changed_paths,
            pr_author=pr_author, pr_head_ref=pr_head_ref,
            pr_head_repo=pr_head_repo, pr_base_repo=pr_base_repo,
        )
        return [DEPENDABOT_PIN_ONLY]
    require(bool(changed_locks), "PR must change at least one governed Context Lock")
    for lock_path in changed_locks:
        safe_path(lock_path, "changed lock")
        head_tree_rows = [row for row in git(repo, "ls-tree", "-z", head_sha, "--", lock_path).split(b"\x00") if row]
        require(len(head_tree_rows) == 1 and
                head_tree_rows[0].split(b"\t", 1)[0].startswith(b"100644 blob "),
                f"changed Context Lock must have regular non-executable Git mode 100644: {lock_path}")
        payload = git(repo, "show", f"{head_sha}:{lock_path}").decode("utf-8")
        lock = json.loads(payload, object_pairs_hook=reject_duplicate_json_keys)
        require(isinstance(lock, dict), "context lock JSON root must be an object")
        inherited_source_paths: set[str] | None = None
        anchor = lock.get("sourceManifestAnchor")
        if anchor is not None:
            require(isinstance(anchor, dict) and set(anchor) == {"path", "gitBlobSha1"},
                    "invalid base source manifest anchor")
            anchor_path = safe_path(anchor["path"], "source manifest anchor")
            require(anchor_path.startswith(LOCK_PREFIX) and anchor_path.endswith(LOCK_SUFFIX)
                    and anchor_path != lock_path, "invalid base Context Lock anchor path")
            require(base_blobs.get(anchor_path) == check_sha(anchor["gitBlobSha1"], "anchor gitBlobSha1"),
                    "source manifest anchor blob mismatch or absent at original base")
            require(anchor_path == latest_original_base_lock_path(base_blobs),
                    "anchor is not the latest original-base Context Lock")
            original_payload = git(repo, "show", f"{base_sha}:{anchor_path}")
            try:
                original_anchor = json.loads(
                    original_payload.decode("utf-8"), object_pairs_hook=reject_duplicate_json_keys
                )
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise ContextLockError("invalid original-base source manifest anchor JSON") from exc
            require(isinstance(original_anchor, dict)
                    and original_anchor.get("schemaVersion") == "iris-context-lock-v1",
                    "invalid original-base Context Lock source manifest")
            original_rows = original_anchor.get("criticalSources")
            require(isinstance(original_rows, list) and bool(original_rows),
                    "missing original-base critical-source manifest")
            inherited_source_paths = set()
            for index, original_row in enumerate(original_rows):
                require(isinstance(original_row, dict), f"original-base source {index}: invalid record")
                old_path = safe_path(original_row.get("path"), f"original-base source {index}")
                check_sha(original_row.get("gitBlobSha1"), f"original-base source {old_path}")
                require(old_path not in inherited_source_paths,
                        f"duplicate original-base source: {old_path}")
                inherited_source_paths.add(old_path)
            require(MANDATORY_SOURCE_PATHS <= inherited_source_paths,
                    "original-base anchor is missing mandatory authority roots")
            original_snapshot = original_anchor.get("sourceSnapshot")
            require(isinstance(original_snapshot, dict)
                    and all(type(original_snapshot.get(field)) is int
                            and original_snapshot[field] == len(inherited_source_paths)
                            for field in ("expected", "checked", "matched")),
                    "inconsistent original-base source manifest counts")
        verify_lock(lock, base_sha=base_sha, base_tree_sha=tree_sha,
                    base_blobs=base_blobs, changed_paths=changed_paths,
                    lock_path=lock_path, inherited_source_paths=inherited_source_paths,
                    base_modes=base_modes)
    return changed_locks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-sha", required=True, help="Trusted GitHub PR base SHA")
    parser.add_argument("--head-sha", required=True, help="Trusted GitHub PR head SHA")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--pr-author", default="", help="Trusted GitHub event PR author login")
    parser.add_argument("--pr-head-ref", default="", help="Trusted GitHub event PR source branch")
    parser.add_argument("--pr-head-repo", default="", help="Trusted GitHub event PR source repository")
    parser.add_argument("--pr-base-repo", default="", help="Trusted GitHub event base repository")
    args = parser.parse_args()
    try:
        locks = verify_current_pr(
            args.repo, base_sha=args.base_sha, head_sha=args.head_sha,
            pr_author=args.pr_author, pr_head_ref=args.pr_head_ref,
            pr_head_repo=args.pr_head_repo, pr_base_repo=args.pr_base_repo,
        )
    except (ContextLockError, json.JSONDecodeError, UnicodeError) as exc:
        print(f"CONTEXT LOCK VERIFICATION FAILED: {exc}", file=sys.stderr)
        return 1
    if locks == [DEPENDABOT_PIN_ONLY]:
        print("IRIS guarded Dependabot action update: PASS GitHub bot identity, one exact full-SHA workflow action pin diff; separate review still required")
    else:
        print(f"IRIS Context Lock: PASS {len(locks)} changed lock(s), exact base source fingerprints and PR diff allowlists")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
