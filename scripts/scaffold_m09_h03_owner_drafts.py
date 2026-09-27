"""WO0042 local BLANK H03 owner worksheets; NEVER an owner decision."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.verify_m09_h03_owner_routes import (
    ROOT, PRIOR, ROUTES, read, verify_all as verify_source)
from scripts.triage_m09_h03_untrusted_owner_reply import (
    SCHEMA, REQUIRED, MODULE_ISSUES)

FILES = {"OWNER-DRAFTS-README.md"} | {
    f"{m}-{s}" for m in MODULE_ISSUES for s in ("draft.json", "questions.md")}


class ScaffoldError(ValueError):
    """No owner authority or unsafe local artifact accepted."""


def check(value, message):
    if not value:
        raise ScaffoldError(message)


def build(packets, routes):
    owners = packets["sourceOwners"]
    issues = routes["routes"]
    check([p["module"] for p in owners] == list(MODULE_ISSUES),
          "source packet order drift")
    check([p["module"] for p in issues] == list(MODULE_ISSUES),
          "source owner route order drift")
    coowners = {}
    for route in issues:
        for qid in route["sourceQuestionIds"]:
            coowners.setdefault(qid, []).append(route["module"])
    files = {}
    for module, issue in MODULE_ISSUES.items():
        owner = next(x for x in owners if x["module"] == module)
        route = next(x for x in issues if x["module"] == module)
        qids = [q["id"] for q in owner["questions"]]
        check(route["ownerIssue"] == issue
              and route["sourceQuestionIds"] == qids
              and len(qids) == route["sourceQuestionCount"]
              and len(qids) == len(set(qids))
              and owner["actualSignedOwnerContract"] is False
              and route["actualSignedOwnerDecision"] is False,
              "owner issue/question drift or forged approval")
        draft = {
            "schemaVersion": SCHEMA, "module": module, "issue": issue,
            "sourceCommit": "", "sourcePath": "", "selfClaimedOwner": "",
            "selfClaimedReviewUrl": "",
            "scopeAndExclusions": {"scope": "", "exclusions": ""},
            "questionDispositions": [
                {"questionId": qid, "decision": "", "rationale": ""}
                for qid in qids],
        }
        check(set(draft) == REQUIRED, "unsupported candidate JSON schema")
        files[f"{module}-draft.json"] = json.dumps(
            draft, indent=2, ensure_ascii=False) + "\n"
        lines = [
            f"# {module} original source questions (issue #{issue})",
            "",
            "**UNANSWERED UNVERIFIED WORKSHEET; NOT AN OWNER APPROVAL.**",
            "Only the actual qualified owner can supply real decisions.",
            "Shared question IDs need separate co-owner review.",
            "",
        ]
        for question in owner["questions"]:
            qid = question["id"]
            others = [m for m in coowners[qid] if m != module]
            lines += [
                f"## {qid}", "",
                question["originalQuestion"], "",
                f"Original research: \`{question['source']}\`",
                f"Original owner label: \`{question['exactOwnerLabel']}\`",
                "Other required owner reviews: " +
                (", ".join(others) if others else "none in four-owner route"),
                "Decision: **BLANK, NOT PROVIDED**", "",
            ]
        files[f"{module}-questions.md"] = "\n".join(lines) + "\n"
    check(sum(route["sourceQuestionCount"] for route in issues) == 147
          and len(coowners) == 91
          and [route["sourceQuestionCount"] for route in issues]
              == [72, 39, 9, 27],
          "original assignments/unique IDs changed")
    files["OWNER-DRAFTS-README.md"] = (
        "# H03 local BLANK owner worksheets, NOT APPROVED\n\n"
        "Nine files, four strictly scoped empty JSON owner worksheets and "
        "four exact original question guides. Zero owner answers are issued; "
        "all real source/reviewer/owner/scope/decision fields are blank. "
        "Do not auto-fill DEFER or invent a commit SHA or owner signature.\n\n"
        "An actual qualified owner must create/review its own source contract "
        "and answer original IDs with evidence. Shared questions still need "
        "separate co-owner review.\n\n"
        "From the repository root: python -m "
        "scripts.triage_m09_h03_untrusted_owner_reply --candidate "
        "<OUTDIR>/M12-draft.json <OUTDIR>/M54-draft.json "
        "<OUTDIR>/M58-draft.json <OUTDIR>/M60-draft.json\n\n"
        "Blank files FAIL closed in E02 triage. Even four "
        "COMPLETE_DRAFT_FORMAT_ONLY files never authenticate owners, "
        "prove source/reviewer credentials, execute negative tests or grant "
        "OS/publication/runtime rights. H01-H04 OPEN HIGH_FOR_FUTURE_FREEZE; "
        "B DIRECTION_ONLY, C01 UNADOPTED_NOT_FROZEN, "
        "M10/M11/M12 runtime NOT_ADMITTED.\n"
    )
    check(set(files) == FILES, "incorrect worksheet output manifest")
    return files


def write(output: Path, files: dict[str, str]):
    """No-clobber local publication; destination is claimed with exclusive mkdir.

    No rename over the final path: on POSIX, rename may replace an EMPTY
    directory that appeared after a previous exists() check. Fail closed if
    another process claims the destination first. A failed write rolls back
    only our own recorded files and our original directory inode. Any file
    created by somebody else is preserved, never recursively removed.
    """
    check(set(files) == FILES, "unsafe output file manifest")
    check(all(type(content) is str for content in files.values()),
          "every owner worksheet must contain inert UTF-8 text")
    check(output.name not in ("", ".", ".."),
          "a dedicated non-root output directory is required")
    check(output.parent.is_dir(), "output parent directory must exist")
    for filename in files:
        check(filename == Path(filename).name and "/" not in filename
              and "\\" not in filename and not filename.startswith("."),
              "unsafe output filename")
    check(not output.exists() and not output.is_symlink(),
          "output already exists; never overwrite user files")

    # mkdir(exist_ok=False) atomically claims the final path. This is
    # deliberately not os.rename(temp, output), which can clobber a newly
    # created empty target directory under POSIX race conditions.
    try:
        output.mkdir(mode=0o700, parents=False, exist_ok=False)
    except FileExistsError as error:
        raise ScaffoldError(
            "output appeared during exclusive creation; never overwrite") from error

    made: list[Path] = []
    owner_stat = None
    try:
        owner_stat = output.stat(follow_symlinks=False)
        for filename in sorted(files):
            path = output / filename
            with path.open("x", encoding="utf-8") as destination:
                made.append(path)
                destination.write(files[filename])
            path.chmod(0o600)
    except BaseException:
        # Do not delete a different directory substituted by another actor.
        # Never recursively remove unexpected contents from a shared parent.
        try:
            if owner_stat is not None and not output.is_symlink():
                current = output.stat(follow_symlinks=False)
                if (current.st_dev, current.st_ino) == (
                        owner_stat.st_dev, owner_stat.st_ino):
                    for path in reversed(made):
                        try:
                            if not path.is_symlink():
                                path.unlink(missing_ok=True)
                        except OSError:
                            pass
                    try:
                        output.rmdir()  # preserves unexpected external files
                    except OSError:
                        pass
        except OSError:
            pass
        raise

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="New local directory; NEVER an existing directory")
    args = parser.parse_args()
    try:
        # Verify exact original pinned WO0037/E01 sources BEFORE any write.
        verify_source(ROOT)
        files = build(read(ROOT, PRIOR), read(ROOT, ROUTES))
        write(args.output_dir, files)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({
            "status": "REJECTED_NO_OWNER_SCAFFOLD_PUBLISHED",
            "actualOwnerApprovals": 0, "actualApprovedContract": False,
            "permissionToPlacePublishUseOsOrExecute": False,
            "reason": str(error)}, sort_keys=True))
        return 2
    print(json.dumps({
        "status": "NINE_BLANK_LOCAL_WORKSHEETS_ONLY",
        "files": sorted(files), "moduleOrder": list(MODULE_ISSUES),
        "originalAssignments": 147, "uniqueOriginalQuestions": 91,
        "realOwnerAnswers": 0, "actualOwnerApprovals": 0,
        "actualApprovedContract": False,
        "permissionToPlacePublishUseOsOrExecute": False,
        "h01h02h03h04": "ALL_OPEN_HIGH_FOR_FUTURE_FREEZE"},
        sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
