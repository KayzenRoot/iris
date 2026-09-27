"""Fail-closed M09 B owner-direction documentary integrity, NOT runtime authority.

Historical C01/C02 NONE/NOT_RECORDED remain unchanged: D01 is the later
owner-ratified direction recorded in issue #110. Offline CI cannot authenticate
the GitHub comment itself; the linked source was verified by the author.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from scripts.verify_m12_owner_intake import ROOT, verify_routing
from scripts.verify_m12_planning_evidence import unique_json
from scripts.validate_governance import validate_checkpoint_consistency

RECORD = ".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json"
C01 = ".engineering/evidence/M09-HANDOFF-CANDIDATE-C01.json"
C02 = ".engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json"
ROUTING = ".engineering/evidence/M12-OWNER-INTAKE-C02.json"
BASE = "97a9fe1666b764278de1379eadd7eda7d04799fe"
TREE = "a86e2553a630d93e64fefcf4fa9b722e10f81cd1"
COMMENT = "https://github.com/KayzenRoot/iris/issues/110#issuecomment-5857665032"
PINS = (
("docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md","d12b4f48030c1a57b8e6228df39f35dac8c2b20a"),
("planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md","30eb7e369b2996cc5e9b5f49736e29232b45b69e"),
(C02,"935abe4323618ac6d583e3bd8acc827d5fe80d2c"),
(C01,"3236ff8146c71da247208b0896e4e37573123fa8"),
("planning/research/M11-C09-REVERSE-LIVENESS-OWNER-RESEARCH.md","de97d44a49b9c8483aa6d5a051a0b42f97f5a3cc"),
("planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md","a85d80ab3bb5f4bdc9be915a59caa92569d66af4"),
("planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md","18b5303d1e36ef60de17b42dd9e2c371ecf4f191"),
(ROUTING,"75c8ecea8e59a0931afc1c6558a0265cff7ac919"),
)
ROLES=("M09 owner issuance","Exact owner context","Owner joint cut",
"Owner verifier and at-use recheck","Reverse M11 liveness and ACK",
"External owner separation")
ROLE_GATES=(
("H02","H03","H04"),("H03","H04"),("H02",),
("H02","H03","H04"),("H01","H03","H04"),
("H01","H02","H03","H04"))
HIGHS=tuple(f"C02-FR-H{i:02d}" for i in range(1,5))
HX=tuple(f"HX-{i:02d}" for i in range(1,13))
LV=tuple(f"LV-{i:02d}" for i in range(1,7))
class M09BDirectionError(ValueError): pass
def need(ok:bool,msg:str)->None:
    if not ok: raise M09BDirectionError(msg)
def git_blob_sha(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def read_json(root:Path,path:str)->dict:
    obj=json.loads((root/path).read_text(encoding="utf-8"),object_pairs_hook=unique_json)
    need(isinstance(obj,dict),f"{path} is not a JSON object")
    return obj
def verify_decision(record:dict,c01:dict,c02:dict,routing:dict,
                    root:Path=ROOT,*,check_documents:bool=True)->dict:
    need(record.get("schemaVersion")=="iris-m09-b-owner-direction-d01"
         and record.get("workOrder")=="IRIS-WO-0033"
         and record.get("issue")==110
         and record.get("relatedOpenIssues")==[82,112,128],"D01 scope drift")
    need(record.get("decisionSource")==dict(
        kind="EXPLICIT_OWNER_RATIFICATION_RECORDED_ON_GITHUB",commentUrl=COMMENT,
        commentId=5857665032,sourceBaseSha=BASE,sourceBaseTreeSha=TREE,
        exactMainGovernanceNumber=509,exactMainGovernanceRun=36332401893,
        tests="4090/4090"),"source comment/base reference drift")
    need(record.get("direction")==dict(
        name="B_FUTURE_OWNER_RECEIPT",
        status="OWNER_SELECTED_FOR_DOCUMENTARY_PLANNING_ONLY",
        scope="FUTURE_M09_IMMUTABLE_VERSIONED_EXACT_REQUEST_READ_ONLY_RECEIPT_PLUS_VERIFIER",
        alternativeA="NOT_SELECTED",alternativeC="NOT_SELECTED",
        c01Adopted=False,positiveGrantAuthorized=False,
        implementationAdmitted=False,decisionsOutsideTopology="NOT_APPROVED"),
        "B direction falsely promoted or other alternatives inferred")
    need(c01.get("topologySelected")=="NONE"
         and c02.get("issue110OwnerDecision")=="NOT_RECORDED"
         and c02.get("noSelectedTopology") is True,
         "original C01/C02 historical baseline overwritten")
    need(record.get("historicalSource")==dict(
        C01topologySelected="NONE",C02issue110Decision="NOT_RECORDED",
        C02noSelectedTopology=True,
        note="HISTORICAL_SOURCE_SNAPSHOTS_NOT_CURRENT_OWNER_DIRECTION"),
        "historic NONE/NOT_RECORDED is not the later B direction")
    highs=c02.get("futureFreezeBlockers")
    need(isinstance(highs,list) and [h.get("id") for h in highs]==list(HIGHS)
         and all(h.get("severity")=="HIGH_FOR_FUTURE_FREEZE"
         and str(h.get("status","")).startswith("OPEN_") for h in highs),
         "C02 inherited HIGH freeze gate closed/changed")
    need(record.get("inheritedHighs")==[
       dict(id=h["id"],severity=h["severity"],historicalStatus=h["status"],
            currentStatus=h["status"],owners=h["owningModules"],
            proofRequired=h["why"],interim=h["safeInterim"],
            disposition="BLOCKED_REQUIRE_SEPARATE_OWNER_EVIDENCE")
       for h in highs],"D01 invented H01-H04 proof or risk disposition")
    need(record.get("sourceAnchors")==[
         dict(path=path,gitBlobSha1=sha) for path,sha in PINS],
         "source path or pinned Git blob SHA drift")
    for path,sha in PINS:
        need(git_blob_sha((root/path).read_bytes())==sha,
             f"exact original source bytes changed without new admission: {path}")
    roles=record.get("conceptualRoles")
    need(isinstance(roles,list) and len(roles)==6,"D01 missing logical roles")
    for i,row in enumerate(roles):
        need(row.get("id")==f"B-R{i+1:02d}" and row.get("name")==ROLES[i]
             and row.get("pendingProofGates")==list(ROLE_GATES[i])
             and row.get("status")=="CONCEPTUAL_NOT_ADOPTED"
             and isinstance(row.get("candidateObligation"),str)
             and len(row["candidateObligation"])>=70,
             "conceptual role invented API or unproved gate")
    hx,lv=c01.get("proofObligations"),c02.get("additionalReverseProofs")
    need(isinstance(hx,list) and isinstance(lv,list)
         and [x.get("id") for x in hx]==list(HX)
         and [x.get("id") for x in lv]==list(LV)
         and all(x.get("status")=="SPECIFIED_NOT_EXECUTED" for x in hx+lv),
         "historic HX/LV executed or missing")
    need(record.get("futureOriginalNegatives")==dict(
        HX=[dict(id=x["id"],status=x["status"]) for x in hx],
        LV=[dict(id=x["id"],status=x["status"]) for x in lv],
        C08count=10,POC02count=8,executed=0),
        "D01 HX/LV fake test result or missing oracle")
    need(record.get("linkedOriginalM12Issue110QuestionIds")==
         routing.get("explicitIssue110QuestionIds")
         and len(record["linkedOriginalM12Issue110QuestionIds"])==5
         and record.get("openM11Questions")==86
         and record.get("openM12Questions")==110
         and record.get("notExecutedM12Cases")==80,
         "non-M09 owner decision fabricated")
    need(record.get("m09FrozenContract")=="m09-contract-v1.0_FROZEN_UNCHANGED"
         and record.get("m09C01")==
         "m09-evidence-handoff-candidate-v0.1_UNADOPTED_NOT_FROZEN"
         and record.get("m11")=="m11-contract-candidate-v0.2_NOT_FROZEN"
         and record.get("m12")==
         "m12-contract-candidate-v0.1_PREPARED_FOR_OWNER_REVIEW_ONLY_NOT_FROZEN"
         and record.get("runtime")=="M10_M11_M12_NOT_ADMITTED"
         and record.get("actions")=="OS_GPU_NETWORK_CLOUD_PROCESS_DISABLED"
         and record.get("pendingRealOwnerContracts")==["M12","M54","M58","M60"]
         and record.get("nextGate")=="REAL_H01_H04_OWNER_PROOFS_AND_INDEPENDENT_FREEZE_AUDIT"
         and isinstance(record.get("stop"),str)
         and len(record["stop"])>=90,"unproved contract or execution promoted")
    if check_documents:
        proposal=(root/"planning/contracts/M09-B-FUTURE-OWNER-RECEIPT-D01.md").read_text(encoding="utf-8")
        for s in (COMMENT,"B_FUTURE_OWNER_RECEIPT",
                  "OWNER_SELECTED_FOR_DOCUMENTARY_PLANNING_ONLY","UNADOPTED_NOT_FROZEN",
                  "CONCEPTUAL","NOT_ADMITTED","SPECIFIED_NOT_EXECUTED",
                  "capacity_reclaimed=false",*HIGHS,"HX-01..12","LV-01..06"):
            need(s in proposal,f"missing source/design STOP in candidate: {s}")
        ledger=(root/"docs/project-brain/16-DECISIONS-LEDGER.md").read_text(encoding="utf-8")
        need(ledger.count("## ADR-0046 - M09 B future owner receipt direction")==1
             and "APPROVED_FOR_DOCUMENTARY_DIRECTION_ONLY" in ledger
             and COMMENT in ledger,"current Decision Ledger missing bounded owner selection")
        for path in ("docs/project-brain/03-SCOPE.md","docs/project-brain/14-BACKLOG.md"):
            doc=(root/path).read_text(encoding="utf-8")
            need(all(s in doc for s in (COMMENT,"B_FUTURE_OWNER_RECEIPT",
                                        "H01","H04","NOT_ADMITTED")),
                 f"authoritative {path} still lacks current B-only STOP")
        canonical=(root/"docs/project-brain/13-CHECKPOINT.md").read_bytes()
        mirror=(root/".engineering/CHECKPOINT.md").read_bytes()
        machine=read_json(root,".engineering/CHECKPOINT.json")
        validate_checkpoint_consistency(canonical,mirror,machine)
        need(all(s in machine["nextStep"] for s in
                 ("B_FUTURE_OWNER_RECEIPT","DIRECTION_ONLY","H01","H04","NOT_ADMITTED")),
             "checkpoint did not advance only the actual B owner-direction gate")
    return dict(BdirectionRecorded=True,highsOpen=4,HXnotExecuted=12,
                LVnotExecuted=6,openM11=86,openM12=110,
                M12futureUnexecuted=80,runtimeAdmitted=False)
def verify_all(root:Path=ROOT)->dict:
    verify_routing(root)
    return verify_decision(read_json(root,RECORD),read_json(root,C01),
                           read_json(root,C02),read_json(root,ROUTING),root)
if __name__=="__main__":
    try:
        print("M09 B owner D01 documentary integrity: PASS "+
              json.dumps(verify_all(),sort_keys=True)+
              "; offline CI cannot authenticate GitHub owner or certify runtime")
    except (M09BDirectionError,OSError,UnicodeError,ValueError,KeyError,TypeError) as exc:
        raise SystemExit(f"M09 B owner D01 documentary integrity: FAIL {exc}") from exc
