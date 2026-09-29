"""M13 FTR documentary source and cross-session evidence verifier. NO runtime."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M13-FTR-DOCUMENTARY-RECONCILIATION.json"
REPORT = "planning/reviews/M13-FINAL-TECHNOLOGY-REVIEW-DOCUMENTARY.md"
BASE = "a0a8058758b13ae554da64e21a11b2762305eea5"
TREE = "724444efb04ea6b0cac851fa6a5bb3145de47b45"
SOURCE_SPECS = [{"id":"S01","path":".engineering/evidence/M13-S01-SOURCE-RESEARCH.json","sha":"5fe1b1ec36ce1e49a0810f553825c9d71b2af3e0","questions":18,"negatives":12},{"id":"S02","path":".engineering/evidence/M13-S02-BACKEND-ATTENTION-RESEARCH.json","sha":"8ac11eaa91292a81d10de1d44ccd21b5e240a664","questions":18,"negatives":14},{"id":"S03","path":".engineering/evidence/M13-S03-DELTA-REUSE-RESEARCH.json","sha":"fe0ea0d3a4b4229f79e19d023c255cc6a0cafdf1","questions":20,"negatives":16},{"id":"S04","path":".engineering/evidence/M13-S04-OVERLAP-IO-RESEARCH.json","sha":"b9b87ac36189c1cabd75989a07920752c23704fd","questions":20,"negatives":16},{"id":"S05","path":".engineering/evidence/M13-S05-PERFORMANCE-GATES-RESEARCH.json","sha":"ff0cba2138ba1684917414501809dff4193fdd49","questions":20,"negatives":16}]
FAMILY_KEYS = ["F01_WARM_MODEL_LOCALITY","F02_COMPILATION_BACKENDS","F03_PARTIAL_REUSE_DELTA","F04_OVERLAP_AND_IO","F05_EMPIRICAL_PERFORMANCE_GATES"]
SEAM_KEYS = ["X01_WARM_CAS_DEDUP","X02_COMPILER_PROFILE","X03_DELTA_PIPELINE","X04_OBSERVER_PROFILING","X05_RESIDENCY_LEASE","X06_COMPILE_REUSE_MEANING"]
GATE_KEYS = ["G01_SOURCE_OWNER_CONTRACTS","G02_H01_M11_OWNER_ACK","G03_H02_M09_LEASE","G04_H04_ATTEMPT_FENCE","G05_MODEL_SUPPLY_RIGHTS","G06_PHYSICAL_STORAGE_AUTHORITY","G07_HARDWARE_MEASUREMENT","G08_QUALITY_AND_REUSE","G09_PRODUCTION_PERFORMANCE_POLICY","G10_FINAL_TECH_REVIEW_APPROVAL"]
MODULE_ROWS = {"masterSha":"a60d19c86bddd3699498f7d1f248a00368e32220"}
TOP_LEVEL = ["schemaVersion","workOrder","issue","status","sourceMainSha","sourceMainTreeSha","asOf","fiveSessions","technologySelection","qualifiedIndependentFinalReview","m13ModuleContract","numericPolicies","observedRealBenchmarks","runtime","b","c01","highs","m12OriginalQuestions","m12OriginalFutureNegatives","h03FourOwnerAssignments","sourceMasterIndex","sessions","researchFamilies","seams","gates","futureIndexOnlyModules","questionCount","futureNegativeCount","fcs","stop"]
NEGATIVE_KEY = {
    "S01": "negativeScenarios", "S02": "negativeCases",
    "S03": "futureNegativeCases", "S04": "negativeCases",
    "S05": "negativeCases",
}
SOURCE_KEYS = {
    "S01": "schemaVersion", "S02": "schema", "S03": "schema",
    "S04": "schema", "S05": "schema",
}
GATES = ("sourceProof", "qualifiedOwner", "qualityEvidence",
         "resourceLease", "realBenchmarks", "currentRights")


class FTRIntegrityError(ValueError):
    """Original proof, authority or documentary compatibility changed."""


def require(ok: bool, why: str) -> None:
    if not ok:
        raise FTRIntegrityError(why)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    obj = {}
    for k, v in pairs:
        require(k not in obj, "duplicate machine JSON key " + k)
        obj[k] = v
    return obj


def load(root: Path = ROOT) -> dict:
    obj = json.loads((root / PACKET).read_text(encoding="utf-8"),
                     object_pairs_hook=no_duplicate_keys)
    require(type(obj) is dict, "packet must be JSON object")
    return obj


def mock_ftr_claims(claims: dict) -> dict:
    """Inert checklist: even all-favorable flags CANNOT authenticate owners."""
    require(type(claims) is dict and set(claims) == set(GATES)
            and all(type(v) is bool for v in claims.values()),
            "six exact untrusted boolean source flags are required")
    return {
        "missingMock": [g for g in GATES if not claims[g]],
        "disposition": "DOCUMENTARY_RECONCILED_REAL_APPROVAL_REQUIRED",
        "independentQualifiedReview": False,
        "m13Frozen": False,
        "technologySelected": False,
        "runtimeAllowed": False,
    }


def verify(p: dict, root: Path = ROOT, *,
           check_human: bool = False,
           human_text: str | None = None) -> dict:
    require(type(p) is dict and set(p) == set(TOP_LEVEL),
            "canonical FTR machine schema changed")
    expected = {
        "schemaVersion": "iris-m13-ftr-source-only-v0.1",
        "workOrder": "IRIS-WO-0050", "issue": 155,
        "status": "DOCUMENTARY_RECONCILIATION_NOT_FINAL_TECH_APPROVAL",
        "sourceMainSha": BASE, "sourceMainTreeSha": TREE,
        "asOf": "2026-09-27",
        "fiveSessions": "COMPLETED_DOCUMENTARY_RESEARCH_ONLY",
        "technologySelection": "NONE",
        "qualifiedIndependentFinalReview": "NOT_RECEIVED",
        "m13ModuleContract": "NOT_FROZEN", "numericPolicies": "NONE_SELECTED",
        "observedRealBenchmarks": "NONE_FROM_M13_RESEARCH",
        "runtime": "NOT_ADMITTED",
        "b": "DIRECTION_ONLY", "c01": "UNADOPTED_NOT_FROZEN",
        "highs": "H01_H02_H03_H04_OPEN_HIGH_FOR_FUTURE_FREEZE",
        "m12OriginalQuestions": "110_OPEN_UNRATED",
        "m12OriginalFutureNegatives": "80_SPECIFIED_NOT_EXECUTED",
        "h03FourOwnerAssignments": "147_ASSIGNMENTS_91_UNIQUE_ORIGINAL",
        "fcs": "SEPARATE_47_MODULE_SOURCE_LOCKED_SCAN_PENDING",
    }
    require(all(type(p[k]) is type(v) and p[k] == v
                for k, v in expected.items()),
            "M13 FTR false final review, frozen contract or H01–H04 approval")
    require(type(p["stop"]) is str
            and all(s in p["stop"] for s in (
                "96 still OPEN", "74 future negatives",
                "SPECIFIED_NOT_EXECUTED", "H01–H04",
                "DIRECTION_ONLY", "UNADOPTED_NOT_FROZEN", "runtime")),
            "final STOP does not retain original nonauthorization")
    index_path = p["sourceMasterIndex"]["path"]
    require(p["sourceMasterIndex"] == {
        "path": "planning/MASTER-MODULE-INDEX.md",
        "sha": MODULE_ROWS["masterSha"],
    }, "FCS preflight index original SHA changed")
    master = (root / index_path).read_bytes()
    require(git_blob(master) == MODULE_ROWS["masterSha"],
            "original index Git blob SHA drifted")
    indexed = [
        {"id": m.group(1), "canonicalTitle": m.group(2),
         "source": "MASTER_MODULE_INDEX_HEADING_ONLY_NO_APPROVED_OWN_MODULE_CONTRACT"}
        for m in re.finditer(r"^### (M\d\d) — (.+)$",
                             master.decode("utf-8"), re.M)
        if 14 <= int(m.group(1)[1:]) <= 60
    ]
    require(indexed == p["futureIndexOnlyModules"]
            and len(indexed) == 47,
            "47 exact original index-only M14–M60 titles changed or invented")
    sessions = p["sessions"]
    require(type(sessions) is list and len(sessions) == 5
            and [x.get("id") for x in sessions] ==
            ["S01", "S02", "S03", "S04", "S05"],
            "five actual original source sessions must retain order")
    q_total, n_total = 0, 0
    for row, src in zip(sessions, SOURCE_SPECS):
        require(set(row) == {
            "id", "sourcePath", "gitBlobSha1", "sourceSchema",
            "originalWorkOrder", "sourceStatus", "questions",
            "futureNegativeIds", "questionsStatus", "negativeStatus",
        } and row["id"] == src["id"]
            and row["sourcePath"] == src["path"]
            and row["gitBlobSha1"] == src["sha"]
            and row["questionsStatus"] == "OPEN_UNRATED_ORIGINAL"
            and row["negativeStatus"] == "SPECIFIED_NOT_EXECUTED",
            "original source path/blob or question status falsely advanced")
        raw = (root / row["sourcePath"]).read_bytes()
        require(git_blob(raw) == row["gitBlobSha1"],
                "original source pack changed " + row["id"])
        orig = json.loads(raw, object_pairs_hook=no_duplicate_keys)
        qs, ng = orig["questions"], orig[NEGATIVE_KEY[row["id"]]]
        require(row["sourceStatus"] == orig["status"]
                and row["originalWorkOrder"] == orig["workOrder"]
                and row["sourceSchema"] == orig[SOURCE_KEYS[row["id"]]]
                and row["questions"] == [x["id"] for x in qs]
                and row["futureNegativeIds"] == [x["id"] for x in ng]
                and len(qs) == src["questions"] and len(ng) == src["negatives"]
                and all(x["status"].find("OPEN") >= 0
                        and x["risk"] == "UNRATED" for x in qs)
                and all(x["status"] == "SPECIFIED_NOT_EXECUTED" for x in ng),
                "original session questions/negative evidence lost or upgraded")
        q_total += len(qs)
        n_total += len(ng)
    require(type(p["questionCount"]) is int
            and p["questionCount"] == q_total == 96
            and type(p["futureNegativeCount"]) is int
            and p["futureNegativeCount"] == n_total == 74,
            "original 96 unanswered questions/74 unexecuted designs changed")
    families, seams, gates = (p["researchFamilies"], p["seams"], p["gates"])
    require([x.get("id") for x in families] == FAMILY_KEYS,
            "five original FTR research family identities drifted")
    for x, source in zip(families, sessions):
        require(set(x) == {"id", "source", "candidateStatus", "scope",
                           "genuineOwnerRoutes", "admissionNeed", "decision"}
                and x["source"] == source["id"]
                and x["candidateStatus"] in ("UNSELECTED", "UNADOPTED",
                                             "UNRATED_NO_NUMERIC_SLO")
                and x["decision"] == "DEFER_UNTIL_ACTUAL_OWNER_AND_MEASUREMENT"
                and len(x["genuineOwnerRoutes"]) >= 5
                and len(x["admissionNeed"]) >= 160,
                "source-only family adopted without real proof")
    require([x.get("id") for x in seams] == SEAM_KEYS,
            "six original cross-session hazards changed")
    for x in seams:
        require(set(x) == {"id", "joins", "originalOwnerRoutes",
                           "counterexample", "mustBlock"}
                and len(x["joins"]) == 2 and all(z in NEGATIVE_KEY for z in x["joins"])
                and len(x["originalOwnerRoutes"]) >= 5
                and x["mustBlock"].startswith("NO_"),
                "cross-session negative logic dropped")
    require([x.get("id") for x in gates] == GATE_KEYS,
            "ten distinct real owner/technical gates changed")
    for x in gates:
        require(set(x) == {"id", "status", "ownerRoutes", "actualProof"}
                and x["status"] in ("BLOCKED", "UNQUALIFIED", "NOT_MEASURED",
                                    "NONE_ASSIGNED", "NOT_APPROVED")
                and len(x["ownerRoutes"]) >= 3
                and len(x["actualProof"]) >= 95,
                "independent future owner evidence falsely approved")
    if check_human:
        body = human_text if human_text is not None else (
            root / REPORT).read_text(encoding="utf-8")
        fence = chr(96) * 3
        marker = "\n## Appendix A: exact canonical FTR machine packet\n\n" + fence + "json\n"
        require(body.count(marker) == 1 and body.endswith("\n" + fence + "\n"),
                "human report lacks one exact canonical final machine appendix")
        visible, tail = body.split(marker)
        raw, rest = tail.split("\n" + fence + "\n", 1)
        require(rest == ""
                and json.loads(raw, object_pairs_hook=no_duplicate_keys) == p,
                "human canonical appendix does not equal original machine packet")
        for row in (*sessions, *families, *seams, *gates):
            require(row["id"] in visible,
                    "human FTR omitted source session or hazard/owner gate")
        for row in indexed:
            require(row["id"] in visible and row["canonicalTitle"] in visible,
                    "47-module forward preflight label omitted")
        for row in sessions:
            require(row["gitBlobSha1"] in visible,
                    "human original session SHA missing")
    return {
        "sourceOnly": True, "originalFiveSessions": len(sessions),
        "originalQuestionsOpen": q_total,
        "futureNegativeCasesNotExecuted": n_total,
        "unselectedFamilies": len(families),
        "crossSessionUnresolvedSeams": len(seams),
        "futureOwnerEvidenceGates": len(gates),
        "indexOnlyFutureModuleTitles": len(indexed),
        "independentActualFinalApproval": False,
        "m13Frozen": False, "runtime": "NOT_ADMITTED",
    }


def verify_all(root: Path = ROOT) -> dict:
    return verify(load(root), root, check_human=True)


if __name__ == "__main__":
    try:
        print("M13 FTR DOCUMENTARY ONLY PASS " +
              json.dumps(verify_all(), sort_keys=True) +
              " | no real owner, technology selection, module freeze or runtime")
    except (FTRIntegrityError, OSError, ValueError, TypeError,
            UnicodeError, KeyError, json.JSONDecodeError) as ex:
        raise SystemExit("M13 FTR FAIL CLOSED: " + str(ex)) from ex
