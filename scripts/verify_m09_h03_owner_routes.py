"""WO0038: fail-closed documentary H03 actual owner-review issue routing.

All issue snapshots are dated, not live CI API verification. Opening an issue,
publishing a draft, or passing these tests is never another module's approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.verify_m09_h03_owner_packets import ROOT, verify_all as verify_h03_packets
from scripts.historical_git_snapshot import trusted_original_root

ROUTES=".engineering/evidence/M09-H03-OWNER-REVIEW-ROUTES-E01.json"
PRIOR=".engineering/evidence/M09-H03-FOUR-OWNER-SOURCE-PACKETS.json"
C02=".engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json"
D01=".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json"
M12=".engineering/evidence/M12-OWNER-DECISION-REGISTER.json"
REPORT="planning/reviews/M09-H03-ACTUAL-OWNER-RESPONSE-ROUTES-E01.md"
WORK_ORDER=".engineering/work-orders/IRIS-WO-0038-M09-H03-REAL-OWNER-ROUTING.md"
SOURCE_HASHES={
 PRIOR:"c82093e393722acb39081e9d76c974d0cddcfd3b",
 C02:"935abe4323618ac6d583e3bd8acc827d5fe80d2c",
 D01:"30cc56a2dd34a8c45cfb96f0a900cafbdd2717bb",
 M12:"3a78744de4db70222a74ce25f00c0ef022583c77",
 "planning/MASTER-MODULE-INDEX.md":"19c8ff6126748cb89e53108bdff8289322071970",
 "planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md":
 "28b3802901349263100ceaaf80c0990513dbbded",
 "planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md":
 "41ab89727c7be14e35e2481aefbd97a0cb81cb48",
}
OWNER_ISSUES=(("M12",128,72),("M54",145,39),("M58",146,9),("M60",147,27))
RESPONSE_NULLS=(
 "actualOwnerIdentity","actualOwnerResponseUrl",
 "actualOwnerReviewedContractCommit","actualOwnerReviewedContractPath",
 "qualifiedIndependentReview","approvalScope","approvedInterfaceVersion",
 "realNegativeTestEvidence")
RESPONSE_FIELDS=(
 "sourceCommit","sourcePath","exactOriginalQuestionDisposition",
 "actualOwnerIdentity","independentReviewEvidence","scopeAndExcludedCases",
 "negativeTestExecutionStatus","crossOwnerDependencies",
 "explicitDeferOrDeclineWhenUnsupported")
HIGHS=("C02-FR-H01","C02-FR-H02","C02-FR-H03","C02-FR-H04")


class H03OwnerRouteError(ValueError):
    """Documentary route changed, or false owner permission inferred."""


def guard(ok,message):
    if not ok:
        raise H03OwnerRouteError(message)


def read(root,path):
    return json.loads((root/path).read_text(encoding="utf-8"),
                      object_pairs_hook=no_duplicate_keys)


def no_duplicate_keys(pairs):
    result={}
    for k,v in pairs:
        guard(k not in result,"duplicate JSON key: "+k)
        result[k]=v
    return result


def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def verify_routes(e,prior,c02,d01,m12,root=ROOT,*,check_documents=True):
    guard(e.get("schemaVersion")=="iris-m09-h03-owner-review-route-e01"
          and e.get("workOrder")=="IRIS-WO-0038"
          and e.get("parentH03WorkOrder")=="IRIS-WO-0037"
          and e.get("parentIssue")==110
          and e.get("existingIssues")==[82,110,112,128]
          and e.get("newOwnerIssueNumbers")==[145,146,147]
          and e.get("sourceGitSha")=="b3c09e7b0485055f25a6e6debd507af8e1ae1c92"
          and e.get("sourceGitTree")=="3c3b38ae1d51c8dcd20cdbfaed15ca7069d72df5"
          and e.get("sourceH03Register")==PRIOR
          and e.get("sourceH03BlobSha1")==SOURCE_HASHES[PRIOR],
          "source/issue authority scope or exact base drift")
    guard(e.get("currentBDecisionUrl")==
          "https://github.com/KayzenRoot/iris/issues/110#issuecomment-5857665032"
          and e.get("Bstatus")=="FUTURE_OWNER_RECEIPT_DOCUMENTARY_PLANNING_ONLY"
          and e.get("historicC01")=="UNADOPTED_NOT_FROZEN"
          and d01["direction"]["name"]=="B_FUTURE_OWNER_RECEIPT"
          and d01["direction"]["status"]=="OWNER_SELECTED_FOR_DOCUMENTARY_PLANNING_ONLY"
          and d01["direction"]["c01Adopted"] is False,
          "no actual B-only ratification or original C01 wrongly promoted")
    guard(e.get("routingStatus")=="ROUTED_FOR_REAL_OWNER_DISCUSSION_ONLY"
          and e.get("currentIssueSnapshotObserved")==
              "2026-09-27_ROUTES_OPEN_UNASSIGNED_SEPARATE_LIVE_CHECK_REQUIRED"
          and e.get("allOwnerApproval")=="NONE_RECORDED"
          and e.get("h03")=="OPEN_FUTURE_OWNER_CONTRACTS"
          and e.get("h03Severity")=="HIGH_FOR_FUTURE_FREEZE",
          "open issue snapshot transformed into current owner signature")
    hs=c02["futureFreezeBlockers"]
    expected_highs=[{k:x[k] for k in ("id","status","severity")} for x in hs]
    guard([h["id"] for h in hs]==list(HIGHS)
          and all(x["status"].startswith("OPEN_")
                  and x["severity"]=="HIGH_FOR_FUTURE_FREEZE" for x in hs)
          and e.get("fourOpenHighs")==expected_highs,
          "four original HIGH future-freeze blockers altered")
    guard(prior["sourceGitSha"]=="46916bdda8eef454542975cddfa527a51cb96b70"
          if "sourceGitSha" in prior else prior["baseSha"]=="46916bdda8eef454542975cddfa527a51cb96b70",
          "pre-existing H03 packet provenance changed")
    guard(prior["H03status"]=="OPEN_FUTURE_OWNER_CONTRACTS"
          and prior["H03severity"]=="HIGH_FOR_FUTURE_FREEZE"
          and prior["newH03FutureCaseStatus"]=="SPECIFIED_NOT_EXECUTED"
          and len(prior["newH03FutureNegatives"])==12
          and all(x["status"]=="SPECIFIED_NOT_EXECUTED"
                  for x in prior["newH03FutureNegatives"]),
          "original H03 packet unexpectedly approved or future scenario executed")
    guard(len(m12["questions"])==110 and len(m12["negativeScenarios"])==80
          and all(x["status"]=="OPEN_UNRATED_PENDING_OWNER"
                  for x in m12["questions"])
          and all(x["status"]=="SPECIFIED_NOT_EXECUTED"
                  for x in m12["negativeScenarios"]),
          "original M12 question register changed")
    guard(e.get("sourceAssignmentCounts")==dict(
             M12=72,M54=39,M58=9,M60=27,overlapping=147,unique=91),
          "source-exact question count changed")
    rs=e.get("routes")
    guard(isinstance(rs,list) and len(rs)==4,
          "missing/duplicate owner intake issue routes")
    for x,(owner,issue,n) in zip(rs,OWNER_ISSUES):
        p=next((y for y in prior["sourceOwners"] if y["module"]==owner),None)
        guard(p is not None and p["questionCount"]==n,
              f"source owner packet not found for {owner}")
        guard(x.get("module")==owner and x.get("ownerIssue")==issue
              and x.get("issueUrl")==f"https://github.com/KayzenRoot/iris/issues/{issue}"
              and x.get("m12FormalCommentId")==("5858805944" if owner=="M12" else None)
              and x.get("sourceQuestionCount")==n
              and x.get("sourceQuestionIds")==[q["id"] for q in p["questions"]]
              and x.get("sourceTier")==p["tier"]
              and x.get("status")=="OPEN_AWAITING_REAL_OWNER_SOURCE_RESPONSE"
              and x.get("actualSignedOwnerDecision") is False
              and x.get("issueObservedAtRouting")=="OPEN_UNASSIGNED"
              and x.get("liveStateRequiresIndependentRefetch") is True
              and x.get("responseRequiredFields")==list(RESPONSE_FIELDS)
              and len(x.get("sourceBasedOwnerChecklist",[]))==3
              and all(isinstance(y,str) and len(y)>35
                      for y in x["sourceBasedOwnerChecklist"]),
              f"invalid {owner} route, question scope or claimed signoff")
        for field in RESPONSE_NULLS:
            guard(field in x and x[field] is None,
                  f"{owner} filled unverified owner proof: {field}")
    guard(e.get("originalM12QuestionsOpen")==110
          and e.get("originalM12FutureTests")=="80_SPECIFIED_NOT_EXECUTED"
          and e.get("originalM11QuestionsOpen")==86
          and e.get("originalM09HX")=="12_SPECIFIED_NOT_EXECUTED"
          and e.get("originalM09LV")=="6_SPECIFIED_NOT_EXECUTED"
          and e.get("originalC08")=="10_SPECIFIED_NOT_EXECUTED"
          and e.get("originalPOC02")=="8_SPECIFIED_NOT_EXECUTED"
          and e.get("newH03NegativeDesigns")=="12_SPECIFIED_NOT_EXECUTED"
          and e.get("m12Contract")=="PROPOSED_NOT_FROZEN"
          and e.get("m54m58m60")=="MASTER_INDEX_ONLY_NO_APPROVED_CONTRACTS"
          and e.get("m09v1")=="FROZEN_UNCHANGED"
          and e.get("m11v02")=="NOT_FROZEN"
          and e.get("M10M11M12runtime")=="NOT_ADMITTED"
          and e.get("processOsGpuNetworkCloud")=="DISABLED"
          and e.get("inferredRuntimeOrPermission") is False,
          "fake test execution or absent external trust gate")
    if check_documents:
        for path,sha in SOURCE_HASHES.items():
            guard(git_blob((root/path).read_bytes())==sha,
                  "exact source Git blob changed: "+path)
        report=(root/REPORT).read_text(encoding="utf-8")
        wo=(root/WORK_ORDER).read_text(encoding="utf-8")
        for marker in ("ROUTED_FOR_REAL_OWNER_DISCUSSION_ONLY",
                       "147 overlapping assignments / 91 unique",
                       "OPEN_FUTURE_OWNER_CONTRACTS",
                       "SPECIFIED_NOT_EXECUTED","OPEN HIGH_FOR_FUTURE_FREEZE",
                       "NOT_ADMITTED","UNADOPTED_NOT_FROZEN",
                       *[f"issues/{i}" for _,i,_ in OWNER_ISSUES]):
            guard(marker in report,"owner routing report missing "+marker)
        guard("H01–H04" in wo
              and "NOT_ADMITTED" in wo
              and "24/24" not in wo
              and "M54" in wo and "M58" in wo and "M60" in wo,
              "Work Order incorrectly claims owner or stale source validation")
    return {"routeCount":4,"issueNumbers":[128,145,146,147],
            "overlappingOwnerAssignments":147,"uniqueOriginalQuestions":91,
            "originalM12QuestionsOpen":110,"originalM12FutureCasesNotExecuted":80,
            "newH03FutureCasesNotExecuted":12,"actualOwnerApprovals":0,
            "fourUnresolvedHighGates":4,"runtimeAdmitted":False}


def verify_all(root=ROOT):
    # An exact original Git snapshot is the authority for discontinued source-only receipts.
    if Path(root).resolve() == ROOT.resolve() and (
        not (ROOT / REPORT).is_file() or
        git_blob((ROOT / "planning/MASTER-MODULE-INDEX.md").read_bytes())
        != SOURCE_HASHES["planning/MASTER-MODULE-INDEX.md"]
    ):
        root = trusted_original_root()
    verify_h03_packets(root)
    return verify_routes(read(root,ROUTES),read(root,PRIOR),
                         read(root,C02),read(root,D01),read(root,M12),root)


if __name__=="__main__":
    try:
        print("IRIS H03 owner issue routing PASS: "+json.dumps(verify_all(),sort_keys=True)
              +" | issue snapshots NOT live CI confirmation; no owner decision admitted")
    except (OSError,KeyError,TypeError,ValueError) as e:
        raise SystemExit(f"IRIS H03 owner issue routing FAIL: {e}") from e
