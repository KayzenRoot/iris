"""WO0083: independent immutable-source documentary FTR audit, standard library only."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M14-FTR-INDEPENDENT-DOCUMENTARY-AUDIT.json"
REPORT = "planning/reviews/M14-FTR-INDEPENDENT-DOCUMENTARY-AUDIT.md"
BASE = "65bab6a909726f5533bcd394b0ae6b1d309a3517"
TREE = "131c6740a3dde09b918b708258844cb58e94d247"
FTR_SOURCE = {"packetPath":".engineering/evidence/M14-FTR-DOCUMENTARY-RECONCILIATION.json","packetSha":"ab418d8cfbb593fbf21ce09447b8af8b4a39474b","reportPath":"planning/reviews/M14-FINAL-TECHNOLOGY-REVIEW-DOCUMENTARY.md","reportSha":"3b2c5d4a36d48d5bbd2281eebd5130e42ba8b8ef","verifierPath":"scripts/verify_m14_ftr.py","verifierSha":"0f4a0e46d036f5d31af8edaf10d02387b9e1704d","originalTestsPath":"tests/test_m14_ftr_documentary.py","originalTestsSha":"cd1b9667241767b6661eddedf8da5282c3338d9f","originalManifestPath":".engineering/context-locks/IRIS-WO-0082-M14-FTR.json","originalManifestSha":"a983966efb3d6f74427b375a77e194684704bdf2"}
ORIGINALS = [{"session":"S01","path":".engineering/evidence/M14-S01-SOURCE-RESEARCH.json","blob":"10fe325b3928e58797266ae4ba0b65c87cd532fc","q":16,"n":12,"alts":4},{"session":"S02","path":".engineering/evidence/M14-S02-SOURCE-RESEARCH.json","blob":"d3ac994e130bc54c566449dc0d6efc19a0ca2698","q":18,"n":14,"alts":4},{"session":"S03","path":".engineering/evidence/M14-S03-SOURCE-RESEARCH.json","blob":"cf49ed6140976a14dbd0ac469bb79ed0091e624d","q":20,"n":16,"alts":4},{"session":"S04","path":".engineering/evidence/M14-S04-SOURCE-RESEARCH.json","blob":"4d3de9e837c9a4988e1f31a6d6f06aae0261c277","q":22,"n":18,"alts":4},{"session":"S05","path":".engineering/evidence/M14-S05-SOURCE-RESEARCH.json","blob":"f8f98a3dcdf7a5276d66a40115b60b0cc1f67c70","q":24,"n":20,"alts":4}]
REQUIRED = {"G01_COMPOSITE_SUPPLY":["M14","M18"],"G02_LICENSE_TENANT_RIGHTS":["M53","M54"],"G03_TYPED_TASK_QUALITY":["M01","M03","M04"],"G04_REPRESENTATIVE_M08_CARD":["M08"],"G05_M07_HOST_RUNTIMES":["M07"],"G06_M09_LEASE_FENCING":["M09"],"G07_M11_M12_EXECUTION_OWNERS":["M11","M12"],"G08_BACKEND_SUPPLY_TRUST":["M13","M16","M18"],"G09_VERSIONED_LIFECYCLE_REVOKE":["M14","M18"],"G10_M02_MASTER_HISTORICAL_LINEAGE":["M02"],"G11_H01_H04_CROSS_OWNER_PROOF":["M09"],"G12_FINAL_M14_OWNER_AND_M60":["M14","M60"]}
ISSUES = [[82,"M11_PROCESS_LIFECYCLE"],[110,"M09_EXPLICIT_A_B_C_OR_DEFER"],[112,"M09_READONLY_HANDOFF_UNADOPTED"],[128,"M12_PLACEMENT_TRUST"],[145,"M54_PRINCIPAL_TENANT_AUTH"],[146,"M58_PUBLICATION_REDACTION"],[147,"M60_ACTUAL_OS_PROCESS_RIGHTS"],[155,"M13_CACHING_BACKEND_SOURCE_ONLY"]]
FAMILY_IDS = ["F01_COMPOSITE_MODEL_IDENTITY_RIGHTS","F02_TYPED_TASK_CAPABILITY_GENOME","F03_EMPIRICAL_QUALITY_LATENCY_VRAM_CARDS","F04_HARDWARE_COMPATIBILITY_AND_RELIABILITY","F05_LIFECYCLE_DRIFT_DEPRECATION_ROLLBACK"]
SEAM_IDS = ["X01_COMPOSITE_TASK_DRIFT","X02_TASK_EMPIRICAL_POPULATION","X03_COMPOSITE_HARDWARE_KERNEL","X04_CARD_HOST_RESOURCE","X05_RIGHTS_LIFECYCLE_CACHE","X06_COMPATIBILITY_ROLLBACK","X07_LIFECYCLE_CARD_REVALIDATION"]

class M14AuditIntegrityError(ValueError):
    """FTR sources, original owners, rights, or runtime proof are not trustworthy."""

def require(ok: bool, why: str) -> None:
    if not ok:
        raise M14AuditIntegrityError(why)

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    out={}
    for key,value in pairs:
        require(key not in out,"duplicate original-source JSON key: "+key)
        out[key]=value
    return out

def load_json(path: Path) -> dict:
    try:
        p=json.loads(path.read_text(encoding="utf-8"),object_pairs_hook=no_duplicate_keys)
    except (OSError,UnicodeDecodeError) as exc:
        raise M14AuditIntegrityError("original source unreadable") from exc
    require(type(p) is dict,"original JSON must be an object")
    return p

def load(root: Path = ROOT) -> dict:
    return load_json(root/PACKET)

def exact_ids(rows: object) -> list | None:
    if type(rows) is not list or not all(type(x) is dict and type(x.get("id")) is str for x in rows):
        return None
    return [x["id"] for x in rows]

def mock_positive_checkboxes(flags: dict) -> dict:
    """Favorable fake claims never constitute a qualified original owner receipt."""
    required={"gitPins","humanReport","allOwnerRoutes","tenantClaims","hardwareClaims","externalReview"}
    require(type(flags) is dict and set(flags)==required
        and all(type(v) is bool for v in flags.values()),"six untrusted typed source claim flags required")
    return {"unchecked":[k for k in sorted(required) if not flags[k]],
        "sourceAuditOnly":True,"qualifiedOwner":False,"technologyAdopted":False,
        "originalCasesExecuted":False,"moduleFrozen":False,"runtimeAllowed":False}

def render_report(p: dict) -> str:
    t="# M14 | Independent original-source documentary audit\n\n"
    t+=("**IRIS-WO-0083; dedicated issue #218. This is a source-document review, NOT an independent original module-owner signoff, selected technology, rights qualification, or runtime admission.**\n\n")
    t+=("Original protected main \x60"+p["baseSha"]+"\x60; full original Git tree \x60"+
        p["baseTreeSha"]+"\x60. This audit preserves original prior final source FTR and historical approvals; it does not execute any hardware, model, provider, network or process action.\n\n")
    t+="## Immutable original FTR authority\n\n"
    for key,value in p["sourceFTR"].items():
        t+="- **"+key+"**: \x60"+value+"\x60.\n"
    t+="\n## Original five-session unresolved register\n\n"
    for s in p["originalCaseRegister"]:
        t+=("- **"+s["session"]+"**: exact original packet \x60"+s["path"]+
            "\x60 / Git blob \x60"+s["blob"]+"\x60; "+str(len(s["questionIds"]))+
            " questions "+s["ownerStatus"]+"; "+str(len(s["negativeIds"]))+
            " future hostile designs "+s["hypotheticalStatus"]+"; "+
            str(len(s["originalAlternativeIds"]))+" alternatives "+s["alternativeStatus"]+".\n")
    t+=("\n**Original M14 totals:** "+str(p["originalM14OpenOwnerQuestions"])+
        " questions OPEN/UNRATED, "+str(p["originalM14FutureNegativeDesignsNotExecuted"])+
        " future cases SPECIFIED_NOT_EXECUTED, "+str(p["originalM14SessionAlternativesUnselected"])+
        " alternatives unselected. Historical M13 "+str(p["originalM13OpenQuestions"])+"/"+
        str(p["originalM13FutureNegativesUnexecuted"])+" stays separate.\n\n")
    t+="## Twelve independently routed proof requirements, all NOT RECEIVED\n\n"
    for g in p["gateAudit"]:
        t+=("- **"+g["id"]+"** ["+g["source"]+"]: actual required original proof issuers "+
            ", ".join(g["requiredOriginalIssuers"])+"; "+g["missingActualEvidence"]+
            " Status: "+g["status"]+".\n")
    t+="\n## Seven original-case-linked future integration hazards\n\n"
    for s in p["sourceSeams"]:
        t+=("- **"+s["id"]+"** ["+" + ".join(s["joins"])+
            "]: source original negative IDs "+", ".join(s["originalNegativeIds"])+
            "; executed=false.\n")
    t+="\n## Eight original unresolved owner issues\n\n"
    for i in p["unresolvedOriginalOwnerIssues"]:
        t+=("- [#"+str(i["issue"])+"](https://github.com/KayzenRoot/iris/issues/"+
            str(i["issue"])+"): "+i["originalOwnerScope"]+
            "; recorded OPEN, no approval presumed.\n")
    t+="\n**STOP:** "+p["stop"]+"\n\n## Exact canonical machine-audit appendix\n\n"+ "\x60\x60\x60json\n"
    t+=json.dumps(p,ensure_ascii=False,indent=2)+"\n"+ "\x60\x60\x60\n"
    return t

def verify(p: dict, root: Path=ROOT, *, check_human: bool=True) -> dict:
    exact={"schemaVersion":"iris-m14-independent-documentary-audit-v0.1",
      "workOrder":"IRIS-WO-0083","issue":218,"parent":204,
      "baseSha":BASE,"baseTreeSha":TREE,
      "status":"DOCUMENTARY_ORIGINAL_SOURCE_AUDIT_PROPOSED_NOT_QUALIFIED_OWNER_APPROVAL",
      "originalM14OpenOwnerQuestions":100,"originalM14FutureNegativeDesignsNotExecuted":80,
      "originalM14SessionAlternativesUnselected":20,"originalM13OpenQuestions":96,
      "originalM13FutureNegativesUnexecuted":74,"documentarySourceFiles":72,
      "allOriginalMode":"100644","originalSourceTreeNontruncated":True,
      "independentRealTechnologyAdoption":"NOT_RECEIVED",
      "qualifiedM14OwnerReceipt":"NOT_RECEIVED","realLicenseTenantRights":"NOT_RECEIVED",
      "realHostBenchmarkCount":0,"executedOriginalNegativeCount":0,"approvedGateCount":0,
      "selectedTechnology":"NONE","m14ModuleContract":"NOT_FROZEN",
      "nativeRuntime":"NOT_ADMITTED","originalM09B":"DIRECTION_ONLY",
      "originalM09C01":"UNADOPTED_NOT_FROZEN","h01h02h03h04":"HIGH_FOR_FUTURE_FREEZE"}
    require(type(p) is dict and set(p)==set(exact)|{"sourceFTR","originalCaseRegister",
        "sourceFamilyIds","sourceSeams","gateAudit","unresolvedOriginalOwnerIssues","stop"},
        "original source audit schema invented/missing fields")
    for k,value in exact.items():
        require(type(p[k]) is type(value) and p[k]==value,
                "forged original owner/rights/gate/runtime fact: "+k)
    require(type(p["stop"]) is str and len(p["stop"])>700 and all(x in p["stop"] for x in (
        "100 original OPEN/UNRATED","80 future hostile","20 original",
        "H01–H04","M01","M02","NOT_RECEIVED","NOT_ADMITTED","NOT_FROZEN")),
        "documentary audit STOP lost")
    require(p["sourceFTR"]==FTR_SOURCE,"original FTR source proof changed")
    for field in ("packet","report","verifier","originalTests","originalManifest"):
        path=FTR_SOURCE[field+"Path"]
        sha=FTR_SOURCE[field+"Sha"]
        try:
            raw=(root/path).read_bytes()
        except OSError as exc:
            raise M14AuditIntegrityError("original FTR source missing: "+field) from exc
        require(git_blob(raw)==sha,"original FTR Git blob changed: "+field)
    old=load_json(root/FTR_SOURCE["packetPath"])
    oldLock=load_json(root/FTR_SOURCE["originalManifestPath"])
    require(old["sourceBaseSha"]=="041c926d2aebcd2e5879e2842c9f6b41e692253f"
        and old["status"]=="SOURCE_ONLY_FINAL_TECHNOLOGY_REVIEW_NOT_ADOPTION"
        and old["moduleContract"]=="NOT_FROZEN"
        and old["independentTechnologyAdoption"]=="NOT_RECEIVED"
        and old["registryRuntime"]=="NOT_ADMITTED"
        and len(old["sourceDocs"])==15,
        "original FTR source authority falsely promoted")
    # Prior manifest is historical, not a magic owner receipt; its source pins belong
    # to the earlier base. This new audit Context Lock pins the actual new source main.
    require(oldLock["workOrder"]=="IRIS-WO-0082"
        and len(oldLock["criticalSources"])==67,
        "historical WO0082 Context Lock mutated")
    for row in old["sourceDocs"]:
        try:
            raw=(root/row["path"]).read_bytes()
            txt=raw.decode("utf-8")
        except (OSError,UnicodeDecodeError) as exc:
            raise M14AuditIntegrityError("original FTR source role missing/nonUTF8") from exc
        require(git_blob(raw)==row["gitBlobSha1"]
            and row["exactNeedle"] in txt,"original FTR source role drift")
    register=p["originalCaseRegister"]
    require(type(register) is list and len(register)==5 and len(old["sessions"])==5,
        "source five-session register missing")
    questions=negatives=alts=0
    seen=set()
    for row,baseSpec,ftr in zip(register,ORIGINALS,old["sessions"]):
        require(type(row) is dict and set(row)=={"session","path","blob","questionIds",
             "negativeIds","originalAlternativeIds","ownerStatus",
             "hypotheticalStatus","alternativeStatus"},
             "source-only session audit record malformed")
        require((row["session"],row["path"],row["blob"])==
            (baseSpec["session"],baseSpec["path"],baseSpec["blob"])
            and row["ownerStatus"]=="OPEN_UNRATED"
            and row["hypotheticalStatus"]=="SPECIFIED_NOT_EXECUTED"
            and row["alternativeStatus"]=="UNSELECTED",
            "original source-only status falsely advanced")
        require(all(type(row[key]) is list and len(row[key])==baseSpec[count]
                    and all(type(x) is str for x in row[key])
                    for key,count in (("questionIds","q"),("negativeIds","n"),
                                      ("originalAlternativeIds","alts"))),
            "original IDs missing/malformed")
        raw=(root/row["path"]).read_bytes()
        require(git_blob(raw)==row["blob"],"original five-session packet sha mismatch")
        original=json.loads(raw.decode("utf-8"),object_pairs_hook=no_duplicate_keys)
        q,n,a=original["questions"],original["negativeScenarios"],original["alternatives"]
        require([x["id"] for x in q]==row["questionIds"]==ftr["ownerQuestions"]
            and [x["id"] for x in n]==row["negativeIds"]==ftr["futureNegativeIds"]
            and [x["id"] for x in a]==row["originalAlternativeIds"]==ftr["originalAlternatives"]
            and all(x["status"]=="OPEN_UNRATED_PENDING_QUALIFIED_OWNER" and x["risk"]=="UNRATED"
                    and x["ownerAnswer"] is None for x in q)
            and all(x["status"]=="SPECIFIED_NOT_EXECUTED" for x in n)
            and all(x["selected"] is False for x in a),
            "source questions/cases original proof changed")
        require(not (seen&set(row["questionIds"])),"cross-session ID reuse")
        seen.update(row["questionIds"])
        questions+=len(q);negatives+=len(n);alts+=len(a)
    require((questions,negatives,alts)==(100,80,20),
            "original 100/80/20 source evidence changed")
    families=p["sourceFamilyIds"]
    require(type(families) is list and families==FAMILY_IDS
        and [x["id"] for x in old["families"]]==families
        and all(x["status"]=="SOURCE_RESEARCH_ONLY_UNSELECTED" for x in old["families"]),
        "source technologies secretly selected")
    seamRows=p["sourceSeams"]
    require(type(seamRows) is list and [x.get("id") for x in seamRows]==SEAM_IDS,
        "seven original source seams missing")
    originals={s["session"]:set(s["negativeIds"]) for s in register}
    for row,original in zip(seamRows,old["seams"]):
        require(type(row) is dict and set(row)=={"id","joins","originalNegativeIds","executed"}
            and row["id"]==original["id"] and row["joins"]==original["joins"]
            and row["originalNegativeIds"]==original["originalNegativeIds"]
            and len(row["joins"])==2 and row["executed"] is False
            and all(row["originalNegativeIds"][i] in originals[row["joins"][i]]
                    for i in range(2)),
            "original hypothetical case falsely executed/relinked")
    gateRows=p["gateAudit"]
    require(type(gateRows) is list and len(gateRows)==12
        and [x.get("id") for x in gateRows]==list(REQUIRED),
        "12 original gate audit records missing/malformed")
    for row,oldGate in zip(gateRows,old["gates"]):
        require(type(row) is dict and set(row)=={"id","source","requiredOriginalIssuers",
           "documentaryReviewRoutes","missingActualEvidence","status","ownerIssuedReceipt","admission"}
           and row["id"]==oldGate["id"] and row["source"]==oldGate["source"]
           and type(row["requiredOriginalIssuers"]) is list
           and row["requiredOriginalIssuers"]==REQUIRED[row["id"]]
           and type(row["documentaryReviewRoutes"]) is list
           and row["documentaryReviewRoutes"]==oldGate["ownerRoutes"]
           and all(owner in row["documentaryReviewRoutes"] for owner in REQUIRED[row["id"]])
           and len(set(row["documentaryReviewRoutes"]))==len(row["documentaryReviewRoutes"])
           and row["missingActualEvidence"]==oldGate["missingActualEvidence"]
           and row["status"]=="ORIGINAL_OWNER_PROOF_NOT_RECEIVED"
           and row["ownerIssuedReceipt"] is None
           and row["admission"] is False,
           "required proof issuer omitted or documentary route forged actual owner receipt")
    observed=p["unresolvedOriginalOwnerIssues"]
    require(type(observed) is list and
        [[x.get("issue"),x.get("originalOwnerScope")] for x in observed]==ISSUES
        and all(type(x) is dict and set(x)=={"issue","originalOwnerScope","status"}
          and x["status"]=="OPEN" for x in observed),
        "original owner issue falsely closed/approved")
    if check_human:
        try:
            human=(root/REPORT).read_text(encoding="utf-8")
        except (OSError,UnicodeDecodeError) as exc:
            raise M14AuditIntegrityError("human audit report unreadable") from exc
        require(human==render_report(p),"machine/human original audit projection drift")
    return {"sourceFtrOriginalBlobsVerified":5,"originalSourceRolePinsVerified":15,
        "originalSessions":5,"originalOpenQuestions":100,"unexecutedFutureCases":80,
        "originalUnselectedAlternatives":20,"unselectedFtrFamilies":5,
        "hypotheticalCrossSessionSeams":7,"unreceivedOwnerProofGates":12,
        "openOriginalOwnerIssueReceiptsRecorded":8,"realOwnerOrRuntimeGrant":False}

if __name__=="__main__":
    print(json.dumps(verify(load()),sort_keys=True))
