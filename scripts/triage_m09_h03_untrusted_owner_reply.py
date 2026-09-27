"""WO0039: offline TRIAGE of *untrusted draft* H03 owner replies.

A well-formed draft is NEVER a genuine owner response, credential check,
source verification, another module's approval, freeze or runtime permission.
No network requests, credentials, OS/process actions, or GitHub mutations.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from scripts.verify_m09_h03_owner_routes import (
    ROOT, ROUTES, PRIOR, read, verify_all as verify_existing_h03,
)

SCHEMA="iris-h03-untrusted-reply-draft-v0"
DISPOSITIONS=("PROPOSED_ANSWER","DEFER","UNSUPPORTED")
MODULE_ISSUES={"M12":128,"M54":145,"M58":146,"M60":147}
REQUIRED={
    "schemaVersion","module","issue","sourceCommit","sourcePath",
    "selfClaimedOwner","selfClaimedReviewUrl","scopeAndExclusions",
    "questionDispositions",
}
REPORT_STATUSES=(
    "MISSING_FIELDS_NOT_REVIEWABLE",
    "PARTIAL_DRAFT_FORMAT_ONLY",
    "COMPLETE_DRAFT_FORMAT_ONLY",
)
ALWAYS_PENDING=(
    "OWNER_IDENTITY_NOT_AUTHENTICATED",
    "SOURCE_COMMIT_AND_PATH_NOT_FETCHED",
    "INDEPENDENT_REVIEW_NOT_VERIFIED",
    "CROSS_OWNER_APPROVAL_NOT_PROVEN",
    "FUTURE_NEGATIVE_TESTS_NOT_EXECUTED",
    "H01_H02_H03_H04_STILL_OPEN_HIGH",
    "NO_GRANT_NO_RUNTIME_NO_PUBLICATION_NO_OS_RIGHTS",
)
_REPO_URL=re.compile(
    r"https://github\.com/KayzenRoot/iris/(?:pull/[1-9]\d*|issues/[1-9]\d*#issuecomment-[1-9]\d*)\Z"
)
_GIT_SHA=re.compile(r"[0-9a-f]{40}\Z")


class UntrustedReplyError(ValueError):
    """Unrecognized data or malformed/unscoped owner claim, fail closed."""


def require(ok:bool, message:str)->None:
    if not ok:
        raise UntrustedReplyError(message)


def read_draft(path:Path)->dict[str,Any]:
    def no_duplicates(pairs):
        found={}
        for key,value in pairs:
            require(key not in found,"duplicate untrusted JSON key: "+key)
            found[key]=value
        return found
    raw=json.loads(path.read_text(encoding="utf-8"),
                   object_pairs_hook=no_duplicates)
    require(isinstance(raw,dict),"top-level candidate must be an object")
    return raw


def triage(candidate:dict[str,Any],packets:dict[str,Any],
           routes:dict[str,Any])->dict[str,Any]:
    """Classify local formatting only, never genuine issuer or approved status.

    Source packets and routes MUST come from a previously verified checkout
    when used for a real draft. Pure tests may pass validated fixtures in memory.
    """
    require(type(candidate) is dict,"candidate must be a JSON object")
    unknown=set(candidate)-REQUIRED
    require(not unknown,"unknown fields are prohibited, including approval claims: "+
            ",".join(sorted(unknown)))
    require(candidate.get("schemaVersion")==SCHEMA,"draft schema mismatch")
    module=candidate.get("module")
    require(type(module) is str and module in MODULE_ISSUES,
            "unknown or unqualified owner module")
    expected_issue=MODULE_ISSUES[module]
    require(type(candidate.get("issue")) is int
            and candidate["issue"]==expected_issue,
            "wrong issue, another module cannot sign this module's route")
    route=next((x for x in routes["routes"] if x["module"]==module),None)
    packet=next((x for x in packets["sourceOwners"] if x["module"]==module),None)
    require(route is not None and packet is not None
            and route["ownerIssue"]==expected_issue
            and route["sourceQuestionIds"]==[q["id"] for q in packet["questions"]]
            and route["actualSignedOwnerDecision"] is False,
            "parent source route is absent, drifted or already asserts approval")
    allowed_ids=route["sourceQuestionIds"]
    allowed_set=set(allowed_ids)
    raw_rows=candidate.get("questionDispositions",[])
    require(type(raw_rows) is list,"questionDispositions must be a list")
    require(len(raw_rows)<=len(allowed_ids),"too many owner question dispositions")
    ids=[]
    for row in raw_rows:
        require(type(row) is dict and set(row)=={"questionId","decision","rationale"},
                "each disposition must have exactly questionId, decision, rationale")
        qid=row["questionId"]
        require(type(qid) is str and qid in allowed_set,
                "nonexistent or different owner source question: "+str(qid))
        require(qid not in ids,"duplicate source question disposition: "+qid)
        require(type(row["decision"]) is str
                and row["decision"] in DISPOSITIONS,
                "no APPROVED, EXECUTED or other promotion in an untrusted draft")
        require(type(row["rationale"]) is str
                and len(row["rationale"].strip())>=15,
                "provide substantive proposed answer/deferral rationale")
        ids.append(qid)

    missing=[]
    for name in ("sourceCommit","sourcePath","selfClaimedOwner",
                 "selfClaimedReviewUrl","scopeAndExclusions"):
        if name not in candidate or candidate[name] in (None,"",{}):
            missing.append(name)
    if not ids:
        missing.append("questionDispositions")
    sha=candidate.get("sourceCommit")
    if "sourceCommit" not in missing:
        require(type(sha) is str and _GIT_SHA.fullmatch(sha) is not None,
                "sourceCommit must be a syntactically valid 40-character Git SHA")
    path=candidate.get("sourcePath")
    if "sourcePath" not in missing:
        require(type(path) is str
                and path.startswith("planning/contracts/"+module+"-")
                and path.endswith(".md")
                and ".." not in path and "\\" not in path
                and "//" not in path,
                "sourcePath must remain in a future owner-scoped contract namespace")
    owner=candidate.get("selfClaimedOwner")
    if "selfClaimedOwner" not in missing:
        require(type(owner) is str and len(owner.strip())>=3
                and len(owner)<=200 and "\n" not in owner,
                "untrusted self-claimed owner text malformed")
    review=candidate.get("selfClaimedReviewUrl")
    if "selfClaimedReviewUrl" not in missing:
        require(type(review) is str and _REPO_URL.fullmatch(review) is not None,
                "review URL must be a syntax-only GitHub repo PR/comment reference")
    scope=candidate.get("scopeAndExclusions")
    if "scopeAndExclusions" not in missing:
        require(type(scope) is dict
                and set(scope)=={"scope","exclusions"}
                and all(type(scope[k]) is str
                        and len(scope[k].strip())>=15
                        for k in ("scope","exclusions")),
                "proposed scope and explicit exclusions are required")

    coowners=set()
    for qid in ids:
        for p in packets["sourceOwners"]:
            if p["module"]!=module and qid in {
                    item["id"] for item in p["questions"]}:
                coowners.add(p["module"])
    if missing:
        status="MISSING_FIELDS_NOT_REVIEWABLE"
    elif len(ids)!=len(allowed_ids):
        status="PARTIAL_DRAFT_FORMAT_ONLY"
    else:
        status="COMPLETE_DRAFT_FORMAT_ONLY"
    require(status in REPORT_STATUSES,"unknown local triage status")
    # Formatting never infers a real contract, signer, reviewer, co-owner
    # attestation, OS process capability, executed LV/HX/H03 tests or freeze.
    return {
        "schemaVersion":"iris-h03-offline-triage-result-v0",
        "module":module,"reviewIssue":expected_issue,
        "formatStatus":status,"submittedQuestionCount":len(ids),
        "expectedQuestionCount":len(allowed_ids),
        "missingFields":sorted(missing),
        "sourceQuestionIds":[qid for qid in allowed_ids if qid in ids],
        "remainingQuestionIds":[qid for qid in allowed_ids if qid not in ids],
        "otherQuestionOwnersRequiringIndependentProof":sorted(coowners),
        "claimedSourceWasFetched":False,
        "claimedOwnerAuthenticated":False,
        "claimedReviewIndependentlyVerified":False,
        "otherOwnerSignaturesVerified":False,
        "realNegativeTestsExecuted":False,
        "actualApprovedContract":False,
        "permissionToPlacePublishUseOsOrExecute":False,
        "h01h02h03h04":"ALL_OPEN_HIGH_FOR_FUTURE_FREEZE",
        "mandatoryWarnings":list(ALWAYS_PENDING),
    }


def triage_verified_checkout(candidate:dict[str,Any],root:Path=ROOT)->dict[str,Any]:
    # Historical owners/source hashes and unadopted status must be checked
    # before using either evidence file for a real local owner-reply draft.
    verify_existing_h03(root)
    return triage(candidate,read(root,PRIOR),read(root,ROUTES))


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate",required=True,type=Path,
                        help="Path to a local UNTRUSTED proposed owner response JSON; no network")
    args=parser.parse_args()
    try:
        output=triage_verified_checkout(read_draft(args.candidate))
    except (UntrustedReplyError,ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps({"status":"REJECTED_UNTRUSTED_DRAFT",
                          "actualApprovedContract":False,
                          "permissionToPlacePublishUseOsOrExecute":False,
                          "reason":str(exc)},sort_keys=True))
        return 2
    print(json.dumps(output,sort_keys=True,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
