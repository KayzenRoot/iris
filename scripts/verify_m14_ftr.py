"""M14 FTR: immutable original-source and explicit nonauthorization verifier, offline only."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M14-FTR-DOCUMENTARY-RECONCILIATION.json"
REPORT = "planning/reviews/M14-FINAL-TECHNOLOGY-REVIEW-DOCUMENTARY.md"
BASE = "041c926d2aebcd2e5879e2842c9f6b41e692253f"
TREE = "eb378b34fa418fbec139f0e7d39934f48b409854"
SOURCE_ROWS = [["INDEX","planning/MASTER-MODULE-INDEX-CURRENT.md","02e6394cc7e75d5466ab22801b4cc7dbe66500be","### M14 — Model Registry & Empirical Model Cards"],["FCS","planning/reviews/M14-M60-FORWARD-COMPATIBILITY-SOURCE-SCAN.md","5bac62b5b1a07fb97e43ea5c76d20dc5419c2cec","### M14: Model Registry & Empirical Model Cards"],["M13_FTR","planning/reviews/M13-FINAL-TECHNOLOGY-REVIEW-DOCUMENTARY.md","a704684ece3cd28969e93eb2eb56d5efb995ad55","M13 | Final Technology Review"],["M01_NORM","planning/contracts/M01-MODULE-CONTRACT-FREEZE-CANDIDATE.md","48e00ca6ec3da8a5185fa49ccad37f14b6a5926a","FROZEN_APPROVED"],["M02_NORM","planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md","a36fd73c03f06b7558f850a2ad515a0df37c243b","FROZEN_APPROVED"],["S01",".engineering/evidence/M14-S01-SOURCE-RESEARCH.json","10fe325b3928e58797266ae4ba0b65c87cd532fc","\"session\": \"S01\""],["S02",".engineering/evidence/M14-S02-SOURCE-RESEARCH.json","d3ac994e130bc54c566449dc0d6efc19a0ca2698","\"session\": \"S02\""],["S03",".engineering/evidence/M14-S03-SOURCE-RESEARCH.json","cf49ed6140976a14dbd0ac469bb79ed0091e624d","\"session\": \"S03\""],["S04",".engineering/evidence/M14-S04-SOURCE-RESEARCH.json","4d3de9e837c9a4988e1f31a6d6f06aae0261c277","\"session\": \"S04\""],["S05",".engineering/evidence/M14-S05-SOURCE-RESEARCH.json","f8f98a3dcdf7a5276d66a40115b60b0cc1f67c70","\"session\": \"S05\""],["S01_REPORT","planning/research/M14-S01-MODEL-IDENTITY-LICENSE-PROVENANCE.md","f07ed63d30c53f38ff77b4f0fbd4934d44f9624d","M14 S01"],["S02_REPORT","planning/research/M14-S02-CAPABILITY-GENOME-TASK-TAXONOMY.md","9799f5169522f0cb44b8049e4f4e9215bf19f0e4","M14 S02"],["S03_REPORT","planning/research/M14-S03-EMPIRICAL-CARD-EVIDENCE-DESIGN.md","9ba713ad3762696feb91b2e3e1aeefc06579dc38","M14 S03"],["S04_REPORT","planning/research/M14-S04-HARDWARE-RELIABILITY-EVIDENCE.md","5dfa91c53c91f2f0edf214c8f50e053d31194d01","M14 S04"],["S05_REPORT","planning/research/M14-S05-MODEL-LIFECYCLE-EVIDENCE.md","afed4dc542dc096cf930193fbc4684df4fb764ff","M14 S05"]]
SESSION_SPECS = [["S01",".engineering/evidence/M14-S01-SOURCE-RESEARCH.json","10fe325b3928e58797266ae4ba0b65c87cd532fc","iris-m14-s01-source-research-v0.1","IRIS-WO-0076",204,"SOURCE_RESEARCH_ONLY_NONBINDING",16,12],["S02",".engineering/evidence/M14-S02-SOURCE-RESEARCH.json","d3ac994e130bc54c566449dc0d6efc19a0ca2698","iris-m14-s02-source-research-v0.1","IRIS-WO-0077",206,"SOURCE_RESEARCH_ONLY_NONBINDING",18,14],["S03",".engineering/evidence/M14-S03-SOURCE-RESEARCH.json","cf49ed6140976a14dbd0ac469bb79ed0091e624d","iris-m14-s03-source-research-v0.1","IRIS-WO-0078",208,"SOURCE_ONLY_NO_REAL_MEASUREMENTS",20,16],["S04",".engineering/evidence/M14-S04-SOURCE-RESEARCH.json","4d3de9e837c9a4988e1f31a6d6f06aae0261c277","iris-m14-s04-source-research-v0.1","IRIS-WO-0079",210,"SOURCE_RESEARCH_ONLY_NO_HARDWARE_QUALIFICATION",22,18],["S05",".engineering/evidence/M14-S05-SOURCE-RESEARCH.json","f8f98a3dcdf7a5276d66a40115b60b0cc1f67c70","iris-m14-s05-source-research-v0.1","IRIS-WO-0080",212,"SOURCE_RESEARCH_ONLY_NO_LIFECYCLE_QUALIFICATION",24,20]]
FAMILY_IDS = ["F01_COMPOSITE_MODEL_IDENTITY_RIGHTS","F02_TYPED_TASK_CAPABILITY_GENOME","F03_EMPIRICAL_QUALITY_LATENCY_VRAM_CARDS","F04_HARDWARE_COMPATIBILITY_AND_RELIABILITY","F05_LIFECYCLE_DRIFT_DEPRECATION_ROLLBACK"]
SEAM_IDS = ["X01_COMPOSITE_TASK_DRIFT","X02_TASK_EMPIRICAL_POPULATION","X03_COMPOSITE_HARDWARE_KERNEL","X04_CARD_HOST_RESOURCE","X05_RIGHTS_LIFECYCLE_CACHE","X06_COMPATIBILITY_ROLLBACK","X07_LIFECYCLE_CARD_REVALIDATION"]
GATE_IDS = ["G01_COMPOSITE_SUPPLY","G02_LICENSE_TENANT_RIGHTS","G03_TYPED_TASK_QUALITY","G04_REPRESENTATIVE_M08_CARD","G05_M07_HOST_RUNTIMES","G06_M09_LEASE_FENCING","G07_M11_M12_EXECUTION_OWNERS","G08_BACKEND_SUPPLY_TRUST","G09_VERSIONED_LIFECYCLE_REVOKE","G10_M02_MASTER_HISTORICAL_LINEAGE","G11_H01_H04_CROSS_OWNER_PROOF","G12_FINAL_M14_OWNER_AND_M60"]
FLAG_KEYS = ("originalGitSource","originalQualifiedOwner","currentTenantRights",
    "currentM07Host","representativeM08Benchmarks","m09LiveLease")

class M14FTRIntegrityError(ValueError):
    """Reject malformed or forged original source, model-rights, owner or runtime evidence."""

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise M14FTRIntegrityError(reason)

def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate machine JSON key: " + key)
        result[key] = value
    return result

def read_json(root: Path = ROOT) -> dict:
    obj = json.loads((root / PACKET).read_text(encoding="utf-8"),
                     object_pairs_hook=no_duplicate_keys)
    require(type(obj) is dict, "FTR packet must be an object")
    return obj

def list_ids(value: object) -> list | None:
    if type(value) is not list or not all(type(row) is dict for row in value):
        return None
    return [row.get("id") for row in value]

def mock_owner_claims(flags: dict) -> dict:
    """Untrusted favorable self-assertions never grant real owner or runtime permissions."""
    require(type(flags) is dict and set(flags) == set(FLAG_KEYS)
            and all(type(v) is bool for v in flags.values()),
            "six exactly typed untrusted source flags required")
    return {"uncheckedMock": [key for key in FLAG_KEYS if not flags[key]],
            "status":"ORIGINAL_OWNER_AND_REAL_MEASUREMENTS_REQUIRED",
            "qualifiedIndependentReview":False,"m14Frozen":False,
            "technologySelected":False,"realTenantRights":False,
            "realHardwareFit":False,"runtimeAdmitted":False}

def render_report(p: dict) -> str:
    out = ["# M14 | Final Technology Review: original five-session documentary reconciliation","",
      "IRIS-WO-0082 / issue #216. SOURCE-ONLY. No selected technology, module-owner freeze or native runtime.","",
      "Original protected main: "+p["sourceBaseSha"]+"; original full Git tree: "+p["sourceBaseTreeSha"]+".","",
      "## 1. Fifteen original pinned source roles",""]
    for s in p["sourceDocs"]:
        out.append("- "+s["role"]+": "+s["path"]+"; original Git blob SHA1 "+
          s["gitBlobSha1"]+"; text anchor: "+s["exactNeedle"]+".")
    out.extend(["","## 2. Five original immutable research sessions",""])
    for s in p["sessions"]:
        out.extend(["### "+s["id"]+": original "+s["originalWorkOrder"],
          "Original packet "+s["sourcePath"]+"; Git SHA1 "+s["gitBlobSha1"]+
          "; schema "+s["schema"]+"; historical status "+s["originalStatus"]+".",
          "All "+str(len(s["ownerQuestions"]))+" original owner questions OPEN/UNRATED; "+
          str(len(s["futureNegativeIds"]))+" future negative designs SPECIFIED_NOT_EXECUTED; "+
          str(len(s["originalAlternatives"]))+" original alternatives UNSELECTED.",
          "Original question IDs: "+", ".join(s["ownerQuestions"])+".",
          "Original future negative IDs: "+", ".join(s["futureNegativeIds"])+".",
          "Original unselected alternative IDs: "+", ".join(s["originalAlternatives"])+".",""])
    out.extend(["Original M14 totals: "+str(p["originalOwnerQuestionsOpen"])+
      " OPEN/UNRATED owner questions and "+str(p["originalNegativeDesignsNotExecuted"])+
      " SPECIFIED_NOT_EXECUTED future negative designs. Original M13 "+
      str(p["originalM13QuestionsOpen"])+"/"+str(p["originalM13FutureNegativesNotExecuted"])+
      " remain separate.","","## 3. Five documentary technology families, ALL UNSELECTED",""])
    for f in p["families"]:
        out.extend(["### "+f["id"]+" ("+f["session"]+")",
          "Scope: "+f["scope"]+".","Limitations: "+f["limitations"],
          "Original owner routes: "+", ".join(f["originalOwnerRoutes"])+".",
          "Missing actual evidence: "+f["missingActualEvidence"],
          "Status: "+f["status"]+".",""])
    out.extend(["## 4. Seven cross-session hypothetical hazards, NOT EXECUTED",""])
    for s in p["seams"]:
        out.extend(["### "+s["id"]+" ("+" + ".join(s["joins"])+")",
          "Hypothetical failure: "+s["hazard"],
          "Original unexecuted source-case IDs: "+", ".join(s["originalNegativeIds"])+".",
          "Original owner routes: "+", ".join(s["ownerRoutes"])+".",
          "Fail-closed required: "+s["mustBlock"]+". Executed: false.",""])
    out.extend(["## 5. Twelve unreceived independent owner and empirical proof gates",""])
    for g in p["gates"]:
        out.extend(["### "+g["id"]+" ("+g["source"]+")",
          "Original owner routes: "+", ".join(g["ownerRoutes"])+".",
          "Missing actual evidence: "+g["missingActualEvidence"],
          "Status: "+g["status"]+".",""])
    out.extend(["## 6. Historical nonauthorization and next gates","",
      "The existing M14-M60 FCS is an index-level source scan, not a published owner contract or M14 qualification.",
      "M09 B: "+p["ownerB"]+"; C01: "+p["m09C01"]+"; "+p["highs"]+
      "; native runtime: "+p["nativeRuntime"]+".",
      "All five S01-S05 documentary sessions and this source FTR are nonadopting. Parent #204 remains OPEN.","",
      "STOP: "+p["stop"],""])
    return "\n".join(out)+"\n"

def verify(p: dict, root: Path = ROOT, *, check_human: bool = True) -> dict:
    exact = {"schemaVersion":"iris-m14-ftr-documentary-source-v0.1",
      "workOrder":"IRIS-WO-0082","issue":216,"module":"M14",
      "sourceBaseSha":BASE,"sourceBaseTreeSha":TREE,
      "status":"SOURCE_ONLY_FINAL_TECHNOLOGY_REVIEW_NOT_ADOPTION",
      "fiveSessions":"COMPLETED_DOCUMENTARY_RESEARCH_ONLY",
      "ownerApproval":"NONE","independentTechnologyAdoption":"NOT_RECEIVED",
      "moduleContract":"NOT_FROZEN","selectedTechnology":"NONE",
      "realRightsApprovals":0,"realModelMeasurements":0,"realLifecycleEvents":0,
      "registryRuntime":"NOT_ADMITTED","originalM13QuestionsOpen":96,
      "originalM13FutureNegativesNotExecuted":74,
      "ownerB":"B_FUTURE_OWNER_RECEIPT_DIRECTION_ONLY",
      "m09C01":"UNADOPTED_NOT_FROZEN",
      "highs":"H01_H02_H03_H04_OPEN_HIGH_FOR_FUTURE_FREEZE",
      "nativeRuntime":"NOT_ADMITTED","originalOwnerQuestionsOpen":100,
      "originalNegativeDesignsNotExecuted":80}
    require(type(p) is dict and set(p) == set(exact) | {
      "sourceDocs","sessions","families","seams","gates","stop"},
      "invented or missing FTR packet fields")
    for key, value in exact.items():
        require(type(p[key]) is type(value) and p[key] == value,
                "forged approval, original totals or model runtime: "+key)
    stop = p["stop"]
    require(type(stop) is str and len(stop) >= 950
            and all(word in stop for word in ("100 owner questions",
              "80 hypothetical","M13 96","74 NOT_EXECUTED","UNSELECTED",
              "NOT_RECEIVED","M01","M02","H01–H04","UNADOPTED_NOT_FROZEN",
              "NOT_ADMITTED")), "required original STOP source authority lost")
    docs = p["sourceDocs"]
    require(type(docs) is list and len(docs) == len(SOURCE_ROWS),
            "15 original source roles missing")
    for row, (role, path, sha, needle) in zip(docs, SOURCE_ROWS):
        require(type(row) is dict and row == {"role":role,"path":path,
                "gitBlobSha1":sha,"exactNeedle":needle},
                "original source role, Git SHA or text needle altered")
        try:
            raw = (root/path).read_bytes()
            text = raw.decode("utf-8")
        except (OSError,UnicodeDecodeError) as exc:
            raise M14FTRIntegrityError("original source unreadable: "+role) from exc
        require(blob_sha(raw) == sha and needle in text,
                "original SHA/text drift: "+role)
    sessions = p["sessions"]
    require(list_ids(sessions) == [s[0] for s in SESSION_SPECS],
            "five original sessions malformed or reordered")
    qtotal = ntotal = 0
    seen = set()
    for row, (sess,path,sha,schema,wo,issue,status,qn,nn) in zip(sessions,SESSION_SPECS):
        required = {"id","sourcePath","gitBlobSha1","schema","originalWorkOrder",
            "originalIssue","originalStatus","ownerQuestions","futureNegativeIds",
            "originalAlternatives","questionsStatus","negativeStatus","technologyStatus"}
        require(type(row) is dict and set(row) == required
           and (row["id"],row["sourcePath"],row["gitBlobSha1"],row["schema"],
                row["originalWorkOrder"],row["originalIssue"],row["originalStatus"]) ==
               (sess,path,sha,schema,wo,issue,status)
           and row["questionsStatus"] == "OPEN_UNRATED_PENDING_QUALIFIED_OWNER"
           and row["negativeStatus"] == "SPECIFIED_NOT_EXECUTED"
           and row["technologyStatus"] == "ALL_UNSELECTED",
           "original S01-S05 packet authority altered")
        for key,count in (("ownerQuestions",qn),("futureNegativeIds",nn),
                          ("originalAlternatives",4)):
            values = row[key]
            require(type(values) is list and len(values) == count
              and all(type(x) is str for x in values)
              and len(set(values)) == count,"original ID list invalid: "+key)
        try:
            raw = (root/path).read_bytes()
            original = json.loads(raw.decode("utf-8"),object_pairs_hook=no_duplicate_keys)
        except (OSError,UnicodeDecodeError) as exc:
            raise M14FTRIntegrityError("original source packet unreadable: "+sess) from exc
        require(blob_sha(raw) == sha and type(original) is dict
            and original["schemaVersion"] == schema
            and original["workOrder"] == wo and original["issue"] == issue
            and original["status"] == status,"source packet Git identity mismatch")
        q,n,a = (original["questions"],original["negativeScenarios"],original["alternatives"])
        require(list_ids(q) == row["ownerQuestions"]
            and list_ids(n) == row["futureNegativeIds"]
            and list_ids(a) == row["originalAlternatives"]
            and len(q) == qn and len(n) == nn and len(a) == 4
            and all(x["status"] == "OPEN_UNRATED_PENDING_QUALIFIED_OWNER"
                and x["risk"] == "UNRATED" and x["ownerAnswer"] is None for x in q)
            and all(x["status"] == "SPECIFIED_NOT_EXECUTED" for x in n)
            and all(x["selected"] is False for x in a),
            "original owner/future design status or alternatives misrepresented")
        require(not (seen & set(row["ownerQuestions"])),"duplicated original questions")
        seen.update(row["ownerQuestions"])
        qtotal += qn
        ntotal += nn
    require(qtotal == 100 and ntotal == 80,"original 100/80 counts altered")
    families = p["families"]
    require(list_ids(families) == FAMILY_IDS,"five family ids missing or malformed")
    for f, sess in zip(families, sessions):
        require(type(f) is dict
          and set(f) == {"id","session","scope","limitations","originalOwnerRoutes",
                         "missingActualEvidence","status"}
          and f["session"] == sess["id"]
          and f["status"] == "SOURCE_RESEARCH_ONLY_UNSELECTED"
          and type(f["scope"]) is str and len(f["scope"]) > 60
          and type(f["limitations"]) is str and len(f["limitations"]) >= 120
          and type(f["missingActualEvidence"]) is str
          and len(f["missingActualEvidence"]) >= 120
          and type(f["originalOwnerRoutes"]) is list
          and len(f["originalOwnerRoutes"]) >= 4
          and all(type(x) is str for x in f["originalOwnerRoutes"])
          and len(set(f["originalOwnerRoutes"])) == len(f["originalOwnerRoutes"]),
          "family adopted or missing substantive limitations")
    seams = p["seams"]
    require(list_ids(seams) == SEAM_IDS,"seven original-source seams missing")
    allneg = {s["id"]:set(s["futureNegativeIds"]) for s in sessions}
    for x in seams:
        require(type(x) is dict
          and set(x) == {"id","joins","originalNegativeIds","hazard","ownerRoutes",
                         "mustBlock","executed"}
          and type(x["joins"]) is list and len(x["joins"]) == 2
          and all(type(i) is str and i in allneg for i in x["joins"])
          and x["joins"][0] != x["joins"][1]
          and type(x["originalNegativeIds"]) is list and len(x["originalNegativeIds"]) == 2
          and all(type(i) is str for i in x["originalNegativeIds"])
          and all(x["originalNegativeIds"][i] in allneg[x["joins"][i]] for i in range(2))
          and type(x["hazard"]) is str and len(x["hazard"]) >= 75
          and type(x["ownerRoutes"]) is list and len(x["ownerRoutes"]) >= 5
          and all(type(i) is str for i in x["ownerRoutes"])
          and x["mustBlock"] == "NO_UNQUALIFIED_ACTUAL_MODEL_OR_RUNTIME_GRANT"
          and x["executed"] is False,
          "cross-session hypothetical was promoted to real executed evidence")
    gates = p["gates"]
    require(list_ids(gates) == GATE_IDS,"twelve original owner proof gates missing")
    for x in gates:
        require(type(x) is dict
          and set(x) == {"id","source","missingActualEvidence","ownerRoutes","status"}
          and type(x["source"]) is str and x["source"] in allneg
          and type(x["missingActualEvidence"]) is str
          and len(x["missingActualEvidence"]) >= 100
          and type(x["ownerRoutes"]) is list and len(x["ownerRoutes"]) >= 4
          and all(type(i) is str for i in x["ownerRoutes"])
          and x["status"] == "NOT_RECEIVED_NO_RUNTIME_OR_OWNER_APPROVAL",
          "unreceived original-owner proof was falsely certified")
    if check_human:
        require((root/REPORT).read_text(encoding="utf-8") == render_report(p),
                "human M14 FTR report differs from machine evidence projection")
    return {"originalSourceRolesVerified":len(docs),"originalSessionsVerified":5,
        "originalOwnerQuestionsOpen":qtotal,"originalFutureNegativesNotExecuted":ntotal,
        "originalAlternativesUnselected":20,"unselectedFamilies":5,
        "unexecutedCrossSessionHazards":7,"missingRealOwnerProofGates":12,
        "actualRuntimeOrModelApproval":0}

def verify_all(root: Path = ROOT) -> dict:
    return verify(read_json(root),root,check_human=True)

if __name__ == "__main__":
    print(json.dumps(verify_all(),sort_keys=True))
