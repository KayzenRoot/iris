"""IRIS-WO-0037: source-exact H03 four-owner packets, no owner approval or runtime.

Historical M12 C02 and M09 C02 records predate the real later owner B choice.
The proposed M12 candidate and M54/M58/M60 index headings do NOT establish
owner-signed cross-module contracts, published APIs or OS privileges.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from scripts.verify_m12_owner_intake import ROOT, verify_routing
from scripts.verify_m12_planning_evidence import unique_json

PACKETS=".engineering/evidence/M09-H03-FOUR-OWNER-SOURCE-PACKETS.json"
INTAKE=".engineering/evidence/M12-OWNER-INTAKE-C02.json"
ORIGINAL=".engineering/evidence/M12-OWNER-DECISION-REGISTER.json"
C02=".engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json"
D01=".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json"
REPORT="planning/reviews/M09-H03-FOUR-OWNER-SOURCE-PACKETS.md"
COMMENT="https://github.com/KayzenRoot/iris/issues/110#issuecomment-5857665032"
OWNER_IDS=("M12","M54","M58","M60")
OWNER_COUNTS=(72,39,9,27)
SOURCE_TIERS=("PROPOSED_NONFROZEN_M12_CANDIDATE",)+("MASTER_INDEX_ONLY_NO_MODULE_CONTRACT",)*3
GATE_IDS=tuple(f"C02-FR-H0{i}" for i in range(1,5))
H03_NEGS=tuple(f"H03-N{i:02d}" for i in range(1,13))
SOURCE_HASHES={
"planning/MASTER-MODULE-INDEX.md":"19c8ff6126748cb89e53108bdff8289322071970",
"planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md":"28b3802901349263100ceaaf80c0990513dbbded",
INTAKE:"75c8ecea8e59a0931afc1c6558a0265cff7ac919",
ORIGINAL:"3a78744de4db70222a74ce25f00c0ef022583c77",
C02:"935abe4323618ac6d583e3bd8acc827d5fe80d2c",
D01:"30cc56a2dd34a8c45cfb96f0a900cafbdd2717bb",
"planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md":
"41ab89727c7be14e35e2481aefbd97a0cb81cb48",
}
FIELDS=("id","session","source","originalQuestion","exactOwnerLabel",
        "originalIntakeLane","ownerDecisionStatus","risk","executableAuthority")


class H03IntegrityError(ValueError):
    """Question, owner, source or H03 fail-closed authority boundary changed."""


def guard(condition:bool,message:str)->None:
    if not condition:
        raise H03IntegrityError(message)


def read_json(root:Path,path:str)->dict:
    obj=json.loads((root/path).read_text(encoding="utf-8"),
                   object_pairs_hook=unique_json)
    guard(isinstance(obj,dict),f"{path} not a JSON object")
    return obj


def git_blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def source_row(x:dict)->dict:
    return dict(id=x["id"],session=x["session"],source=x["source"],
                originalQuestion=x["question"],exactOwnerLabel=x["exactOwnerLabel"],
                originalIntakeLane=x["intakeLane"],ownerDecisionStatus=x["ownerDecisionStatus"],
                risk=x["risk"],executableAuthority=x["executableAuthority"])


def verify_h03(p:dict,i:dict,original:dict,c02:dict,d01:dict,
               root:Path=ROOT,*,check_documents:bool=True)->dict:
    guard(p.get("schemaVersion")=="iris-m09-h03-four-owner-source-packets-d01"
          and p.get("workOrder")=="IRIS-WO-0037"
          and p.get("issue")==110
          and p.get("linkedIssues")==[82,112,128]
          and p.get("baseSha")=="46916bdda8eef454542975cddfa527a51cb96b70"
          and p.get("baseTreeSha")=="b3bf2adaaf471f73d9b5b98acdc1fcad3a2861fe",
          "source-exact WO0037 scope or base changed")
    guard(p.get("ownerBSource")==COMMENT
          and p.get("ownerSelectedTopologyDirection")==
              "B_FUTURE_OWNER_RECEIPT_DOCUMENTARY_ONLY"
          and d01.get("direction",{}).get("name")=="B_FUTURE_OWNER_RECEIPT"
          and d01["direction"]["status"]==
              "OWNER_SELECTED_FOR_DOCUMENTARY_PLANNING_ONLY"
          and d01["direction"]["c01Adopted"] is False
          and p.get("historicM12IntakeTopology")=="NONE"
          and i["selectedTopology"]=="NONE"
          and p.get("historicM09C02Topology")=="NOT_RECORDED"
          and c02["issue110OwnerDecision"]=="NOT_RECORDED"
          and p.get("historicSourceSnapshotsNotRewritten") is True,
          "false historical/current owner adoption or topology inference")
    guard(p.get("H03id")=="C02-FR-H03"
          and p.get("H03status")=="OPEN_FUTURE_OWNER_CONTRACTS"
          and p.get("H03severity")=="HIGH_FOR_FUTURE_FREEZE",
          "H03 falsely closed or downgraded")
    highs=c02["futureFreezeBlockers"]
    guard([h["id"] for h in highs]==list(GATE_IDS)
          and all(h["status"].startswith("OPEN_")
                  and h["severity"]=="HIGH_FOR_FUTURE_FREEZE" for h in highs)
          and p.get("currentFourHighs")==list(GATE_IDS)
          and p.get("fourHighStatuses")==[h["status"] for h in highs],
          "one or more inherited H01-H04 HIGHs falsely cleared")
    guard(original["counts"]["ownerQuestions"]==110
          and original["counts"]["futureNegativeScenarios"]==80
          and len(original["questions"])==110
          and len(original["negativeScenarios"])==80
          and all(x["status"]=="OPEN_UNRATED_PENDING_OWNER"
                  for x in original["questions"])
          and all(x["status"]=="SPECIFIED_NOT_EXECUTED"
                  for x in original["negativeScenarios"])
          and len(i["questions"])==110
          and i["counts"]["futureNegativeScenarios"]==80,
          "original M12 110 OPEN/80 unexecuted evidence not preserved")
    original_by_id={x["id"]:x for x in original["questions"]}
    intake_by_id={x["id"]:x for x in i["questions"]}
    guard(len(original_by_id)==110 and len(intake_by_id)==110
          and set(original_by_id)==set(intake_by_id),
          "historical M12 question identity changed")
    for qid,q in intake_by_id.items():
        old=original_by_id[qid]
        guard((old["question"],old["owners"],old["source"],old["session"],old["status"])==
              (q["question"],q["exactOwnerLabel"],q["source"],q["session"],
               q["ownerDecisionStatus"])
              and q["risk"]=="UNRATED"
              and q["executableAuthority"]=="NONE",
              f"owner/source/status or authority mismatch: {qid}")
    packets=p.get("sourceOwners")
    guard(isinstance(packets,list) and [x.get("module") for x in packets]==list(OWNER_IDS),
          "H03 owner queue removed, duplicated or replaced")
    for k,(name,count,tier) in enumerate(zip(OWNER_IDS,OWNER_COUNTS,SOURCE_TIERS)):
        packet=packets[k]
        ids=i["ownerQueues"][name]
        guard(len(ids)==count
              and packet.get("questionCount")==count
              and packet.get("tier")==tier
              and packet.get("status")==
                  "PENDING_SEPARATE_ACTUAL_OWNER_CONTRACT_AND_SIGNOFF"
              and packet.get("actualSignedOwnerContract") is False
              and packet.get("publicOrExecutablePort") is False
              and packet.get("assumedPermissions") is False
              and isinstance(packet.get("expect"),str)
              and len(packet["expect"])>70,
              f"{name} actual owner contract/port invented or source count changed")
        expected=[source_row(intake_by_id[qid]) for qid in ids]
        guard(packet.get("questions")==expected,
              f"{name} source question text/owner/scope/status changed")
    allids=set().union(*(set(i["ownerQueues"][x]) for x in OWNER_IDS))
    guard(p.get("overlappingQuestionAssignments")==147
          and p.get("uniqueQuestionsAcrossFourOwners")==len(allids)==91,
          "nonexclusive owner-count math or unique identity changed")
    overlaps=[]
    for a in range(4):
        for b in range(a+1,4):
            both=[qid for qid in i["ownerQueues"][OWNER_IDS[a]]
                  if qid in i["ownerQueues"][OWNER_IDS[b]]]
            overlaps.append(dict(pair=[OWNER_IDS[a],OWNER_IDS[b]],
                                 questionIds=both,questionCount=len(both)))
    guard(p.get("pairwiseIntersections")==overlaps,
          "owner intersection missing or false signoff inferred from overlap")
    guard(p.get("explicitIssue110QuestionIds")==i["explicitIssue110QuestionIds"]
          and len(i["explicitIssue110QuestionIds"])==5,
          "five original #110-linked owner questions omitted")
    neg=p.get("newH03FutureNegatives")
    guard(isinstance(neg,list)
          and [x.get("id") for x in neg]==list(H03_NEGS)
          and all(x.get("status")=="SPECIFIED_NOT_EXECUTED"
                  and x.get("runtime") is False
                  and isinstance(x.get("expectedSafeDisposition"),str)
                  and len(x["expectedSafeDisposition"])>20 for x in neg)
          and p.get("newH03FutureCaseStatus")=="SPECIFIED_NOT_EXECUTED",
          "future H03-N tests fabricated as executed or omitted")
    guard(p.get("originalM12Questions")==110
          and p.get("originalM12FutureNegatives")==80
          and p.get("originalM11Questions")==86
          and p.get("originalM09HXFuture")==12
          and p.get("originalM09LVFuture")==6
          and p.get("originalC08Future")==10
          and p.get("originalPOC02Future")==8
          and p.get("originalCaseStatus")=="SPECIFIED_NOT_EXECUTED"
          and p.get("M12")=="PROPOSED_NOT_FROZEN_110_OPEN_80_FUTURE_NEGATIVES_UNEXECUTED"
          and all(p.get(k)=="INDEX_ONLY_NO_APPROVED_CONTRACT"
                  for k in ("M54","M58","M60"))
          and p.get("M09v1")=="FROZEN_UNCHANGED"
          and p.get("M09C01")=="UNADOPTED_NOT_FROZEN"
          and p.get("M11v2")=="NOT_FROZEN_86_OPEN"
          and p.get("runtime")=="M10_M11_M12_NOT_ADMITTED"
          and p.get("hardwareOSNetworkCloud")=="DISABLED"
          and p.get("crossOwnerApproval")=="NONE_INFERRED"
          and p.get("newOperationalInterfaces")==0
          and p.get("independentOwnerAudit")=="NOT_PERFORMED",
          "proposed source packets promoted into authority/runtime")
    for path,sha in SOURCE_HASHES.items():
        guard(git_blob((root/path).read_bytes())==sha,
              f"exact immutable owner evidence source drift: {path}")
    index=(root/"planning/MASTER-MODULE-INDEX.md").read_text(encoding="utf-8")
    for owner in OWNER_IDS:
        guard(f"### {owner} " in index,
              f"actual master index entry missing: {owner}")
    # These three are index-only at this exact source base; do not quietly
    # treat a fabricated file name as an actual owner-issued contract.
    for owner in ("M54","M58","M60"):
        guard(not list((root/"planning/contracts").glob(f"{owner}-*"))
              and not list((root/"planning/modules").glob(f"{owner}-*")),
              f"{owner} now has material requiring a fresh gated owner review")
    if check_documents:
        doc=(root/REPORT).read_text(encoding="utf-8")
        for marker in (COMMENT,"B_FUTURE_OWNER_RECEIPT",
                       "OPEN_FUTURE_OWNER_CONTRACTS","HIGH_FOR_FUTURE_FREEZE",
                       "UNADOPTED_NOT_FROZEN","SPECIFIED_NOT_EXECUTED",
                       "M54","M58","M60","NOT_ADMITTED",
                       "147 overlapping owner assignments","91 unique",
                       *H03_NEGS,*i["explicitIssue110QuestionIds"],*i["ownerQueues"]["M58"]):
            guard(marker in doc,f"public H03 source discussion omits {marker}")
        w=(root/".engineering/work-orders/IRIS-WO-0037-M09-H03-OWNER-PACKETS.md").read_text(encoding="utf-8")
        guard("NOT_ADMITTED" in w and "H01–H04" in w
              and "M58" in w and "M60" in w,
              "WO0037 missing non-admission/H03 source dependency controls")
    return dict(ownerQuestionAssignments=147,uniqueQuestions=91,
                M12=72,M54=39,M58=9,M60=27,
                historicalM12QuestionsOpen=110,
                historicalM12NegativesNotExecuted=80,
                newH03NegativesNotExecuted=12,
                openHighs=4,runtimeAdmitted=False)


def verify_all(root:Path=ROOT)->dict:
    # Existing independently governed historical source routing is enforced
    # before this new current overlay is compared with its exact old sources.
    verify_routing(root)
    return verify_h03(read_json(root,PACKETS),read_json(root,INTAKE),
                      read_json(root,ORIGINAL),read_json(root,C02),
                      read_json(root,D01),root)


if __name__=="__main__":
    try:
        result=verify_all()
        print("H03 four-owner source intake PASS "+
              json.dumps(result,sort_keys=True)+
              "; static source integrity only, no owner or OS runtime approval")
    except (H03IntegrityError,ValueError,KeyError,TypeError,OSError) as exc:
        raise SystemExit(f"H03 source intake FAIL: {exc}") from exc
