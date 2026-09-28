"""WO0051: exact M14-M60 47-module/235-session index-only FCS source verifier."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M14-M60-FORWARD-COMPAT-SCAN.json"
REPORT = "planning/reviews/M14-M60-FORWARD-COMPATIBILITY-SOURCE-SCAN.md"
SOURCE_MAIN = "d30c767bcff604a63b0f09a62a2a96c8148a9873"
SOURCE_TREE = "2563ac3195ea2c051770b186a4c2bfdf90a3479f"
INDEX_SHA = "19c8ff6126748cb89e53108bdff8289322071970"
FTR_SHA = "9b20be372c58bfbc6561963ad0e9c2a33461526d"
MODULE_KEYS = ["M14","M15","M16","M17","M18","M19","M20","M21","M22","M23","M24","M25","M26","M27","M28","M29","M30","M31","M32","M33","M34","M35","M36","M37","M38","M39","M40","M41","M42","M43","M44","M45","M46","M47","M48","M49","M50","M51","M52","M53","M54","M55","M56","M57","M58","M59","M60"]
INTERLOCK_IDS = ["I01_MODEL_SOURCE_PACKAGE","I02_IDENTITY_ACROSS_MEDIA","I03_MIXED_MEDIA_ANATOMY","I04_GOVERNED_PHYSICAL_STORAGE","I05_M09_WORKER_GATES","I06_QUALITY_EVIDENCE_NONTRADEABLE","I07_MEASUREMENTS_VERSUS_DASHBOARD","I08_PUBLIC_AND_EXPORT_BOUNDARY","I09_DCC_NATIVE_EXECUTION","I10_HIVE_CONTEXT_REUSE"]
INTERLOCK_MAP = [{"id":"I01_MODEL_SOURCE_PACKAGE","moduleIds":["M14","M16","M17","M18","M19"]},{"id":"I02_IDENTITY_ACROSS_MEDIA","moduleIds":["M20","M21","M30","M36","M37","M39","M40","M41","M46"]},{"id":"I03_MIXED_MEDIA_ANATOMY","moduleIds":["M20","M23","M25","M27","M28","M29","M30","M36","M37","M38","M42"]},{"id":"I04_GOVERNED_PHYSICAL_STORAGE","moduleIds":["M18","M25","M32","M34","M35","M36","M38","M52","M53","M54","M55","M59"]},{"id":"I05_M09_WORKER_GATES","moduleIds":["M17","M19","M26","M31","M32","M36","M50","M57","M58","M60"]},{"id":"I06_QUALITY_EVIDENCE_NONTRADEABLE","moduleIds":["M15","M20","M23","M24","M28","M34","M35","M37","M38","M47","M48","M49","M50","M51","M59"]},{"id":"I07_MEASUREMENTS_VERSUS_DASHBOARD","moduleIds":["M14","M15","M31","M34","M44","M45","M50","M51","M56","M57","M60"]},{"id":"I08_PUBLIC_AND_EXPORT_BOUNDARY","moduleIds":["M39","M40","M41","M43","M44","M45","M46","M47","M52","M53","M54","M57","M58","M59","M60"]},{"id":"I09_DCC_NATIVE_EXECUTION","moduleIds":["M16","M17","M18","M26","M31","M32","M33","M34","M35","M54","M60"]},{"id":"I10_HIVE_CONTEXT_REUSE","moduleIds":["M43","M44","M45","M46","M48","M52","M53","M54","M55","M57"]}]
SOURCE_FIELDS = ["schemaVersion","workOrder","issue","status","sourceMain","sourceTree","asOf","masterIndex","sourceFTR","modules","interlocks","coverage","independentQualifiedFCSApproval","moduleContractFreeze","technologySelection","realHardwareBenchmarks","runtime","ownerB","c01","h01h02h03h04","m12Original","actualQualifiedH03Contracts","nextStep","stop"]


class FCSIntegrityError(ValueError):
    """An index-only compatibility hypothesis was falsely made authoritative."""


def require(ok: bool, message: str) -> None:
    if not ok:
        raise FCSIntegrityError(message)


def sha_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def unique(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate source JSON key " + key)
        result[key] = value
    return result


def read_packet(root: Path = ROOT) -> dict:
    value = json.loads((root / PACKET).read_text(encoding="utf-8"),
                       object_pairs_hook=unique)
    require(type(value) is dict, "FCS packet must be object")
    return value


def parse_master_index(raw: bytes) -> list[dict]:
    """Parse ALL original 47 named areas and 235 five-session lines as written."""
    area = ""
    modules: list[dict] = []
    for line in raw.decode("utf-8").splitlines():
        if line.startswith("## AREA "):
            area = line[3:]
        else:
            match = re.fullmatch(r"### (M\d\d) — (.+)", line)
            if match and 14 <= int(match.group(1)[1:]) <= 60:
                modules.append({
                    "id": match.group(1), "title": match.group(2),
                    "area": area, "originalSessions": [],
                })
            elif re.fullmatch(r"- S0[1-5] — .+", line) and modules:
                modules[-1]["originalSessions"].append(line[2:])
    require(len(modules) == 47
            and all(len(row["originalSessions"]) == 5 for row in modules)
            and len({row["id"] for row in modules}) == 47,
            "47 original modules with five original sessions each missing")
    return modules


def mock_compatibility_evidence(claims: dict) -> dict:
    """All synthetic fields true remain UNTRUSTED, no API, GPU or final approval."""
    keys = ("originalIndex", "moduleOwnerProof", "sourceValidM08",
            "currentRights", "h01toH04", "securityOSAndStorage",
            "independentReviewer")
    require(type(claims) is dict and set(claims) == set(keys)
            and all(type(v) is bool for v in claims.values()),
            "seven exact untrusted documentary flags required")
    return {
        "missingMock": [key for key in keys if not claims[key]],
        "disposition": "INDEX_COVERAGE_ONLY_REAL_OWNERS_AND_INTEGRATION_PENDING",
        "independentFCSApproved": False, "m13Approved": False,
        "runtimeAuthorized": False, "actualIntegrationTestsRun": 0,
    }


def validate(p: dict, root: Path = ROOT, *,
             check_human: bool = False,
             human_text: str | None = None) -> dict:
    require(type(p) is dict and set(p) == set(SOURCE_FIELDS),
            "canonical FCS packet original schema changed")
    immutable = {
        "schemaVersion": "iris-m14-m60-fcs-source-only-v0.1",
        "workOrder": "IRIS-WO-0051", "issue": 155,
        "status": "INDEX_EXHAUSTIVE_DOCUMENTARY_SCAN_NOT_INDEPENDENT_APPROVAL",
        "sourceMain": SOURCE_MAIN, "sourceTree": SOURCE_TREE,
        "asOf": "2026-09-27",
        "coverage": {
            "originalModuleHeadings": 47, "sourceOriginalSubsessions": 235,
            "moduleSpecificFailureBoundaries": 47,
            "moduleSpecificActualOwnerProofRoutesMissing": 47,
            "crossAreaInterlocks": 10,
            "qualifiedActualM14toM60OwnerContractsInFCS": 0,
            "originalM13OpenQuestions": 96,
            "originalM13FutureCasesNotExecuted": 74,
        },
        "independentQualifiedFCSApproval": "NOT_RECEIVED",
        "moduleContractFreeze": "NOT_ADMITTED",
        "technologySelection": "NONE", "realHardwareBenchmarks": "NONE",
        "runtime": "NOT_ADMITTED", "ownerB": "DIRECTION_ONLY",
        "c01": "UNADOPTED_NOT_FROZEN",
        "h01h02h03h04": "OPEN_HIGH_FOR_FUTURE_FREEZE",
        "m12Original": "110_OPEN_UNRATED_80_FUTURE_CASES_NOT_EXECUTED",
        "actualQualifiedH03Contracts": "M12_M54_M58_M60_NOT_RECEIVED",
        "nextStep": (
            "GATHER_GENUINE_INDEPENDENT_OWNER_SIGNED_SOURCE_CONTRACTS_"
            "AND_M08_REAL_HARDWARE_PROOF_BEFORE_NEW_FTR_APPROVAL_OR_RUNTIME"),
    }
    require(all(type(p[k]) is type(v) and p[k] == v
                for k, v in immutable.items()),
            "actual FCS owner/evidence/coverage or runtime falsely approved")
    require(type(p["stop"]) is str and
            all(s in p["stop"] for s in (
                "H01-H04", "DIRECTION_ONLY", "UNADOPTED_NOT_FROZEN",
                "NOT_EXECUTED", "runtime", "47-module")),
            "FCS original STOP lost critical no-authorization condition")
    require(p["masterIndex"] == {
        "path": "planning/MASTER-MODULE-INDEX.md",
        "gitBlobSha1": INDEX_SHA, "modules": 47, "originalSubsessions": 235,
    }, "original index source or original scope changed")
    require(p["sourceFTR"] == {
        "path": ".engineering/evidence/M13-FTR-DOCUMENTARY-RECONCILIATION.json",
        "gitBlobSha1": FTR_SHA, "questionsOpen": 96,
        "negativeCasesNotExecuted": 74,
        "ownActualTechReviewStatus":
        "DOCUMENTARY_RECONCILIATION_NOT_FINAL_TECH_APPROVAL",
    }, "original FTR evidence source or still-open status changed")
    index = (root / p["masterIndex"]["path"]).read_bytes()
    prior = (root / p["sourceFTR"]["path"]).read_bytes()
    require(sha_blob(index) == INDEX_SHA and sha_blob(prior) == FTR_SHA,
            "index/FTR exact-original SHA1 Git blob changed")
    ftr = json.loads(prior, object_pairs_hook=unique)
    require(ftr["questionCount"] == 96 and
            ftr["futureNegativeCount"] == 74 and
            ftr["qualifiedIndependentFinalReview"] == "NOT_RECEIVED"
            and ftr["m13ModuleContract"] == "NOT_FROZEN"
            and ftr["technologySelection"] == "NONE",
            "FTR original 96/74 and genuine technical approval not respected")
    master_rows = parse_master_index(index)
    rows = p["modules"]
    require(type(rows) is list and
            [row.get("id") for row in rows] == MODULE_KEYS,
            "all exact 47 M14–M60 names/order must be source-exact")
    require([{"id": x.get("id"), "title": x.get("title"),
              "area": x.get("area"),
              "originalSessions": x.get("originalSessions")}
             for x in rows] == master_rows,
            "full 235 original sub-sessions / area / title drifted")
    family_ids = {x["id"] for x in ftr["researchFamilies"]}
    for x in rows:
        require(set(x) == {
            "id", "title", "area", "originalSessions", "version",
            "sourceIndexPath", "sourceIndexGitBlob", "candidateM13Families",
            "plausibleFailure", "requiredFutureActualOwnerProof",
            "currentOwnModuleSourceContract", "futureNegativeStatus",
            "ownerApproval", "selectedTechnology", "runtimeAuthority",
        } and x["version"] == "ORIGINAL_INDEX_V1"
            and x["sourceIndexPath"] == p["masterIndex"]["path"]
            and x["sourceIndexGitBlob"] == INDEX_SHA
            and type(x["candidateM13Families"]) is list
            and 1 <= len(x["candidateM13Families"]) <= 5
            and len(x["candidateM13Families"]) ==
                len(set(x["candidateM13Families"]))
            and set(x["candidateM13Families"]) <= family_ids
            and len(x["plausibleFailure"]) >= 105
            and len(x["requiredFutureActualOwnerProof"]) >= 120
            and x["currentOwnModuleSourceContract"] ==
                "INDEX_ONLY_NO_APPROVED_OWN_MODULE_CONTRACT"
            and x["futureNegativeStatus"] ==
                "DOCUMENTARY_DESIGN_NOT_EXECUTED"
            and x["ownerApproval"] == "NOT_RECEIVED"
            and x["selectedTechnology"] == "NONE"
            and x["runtimeAuthority"] == "NONE",
            "module title, source risk, actual owner or code authorization drifted")
    interlocks = p["interlocks"]
    require(type(interlocks) is list
            and [x.get("id") for x in interlocks] == INTERLOCK_IDS
            and len(interlocks) == 10,
            "ten original cross-module compatibility interfaces changed")
    for x, source in zip(interlocks, INTERLOCK_MAP):
        require(set(x) == {"id", "indexModuleIds",
                           "hypotheticalFailureBoundary", "evidence", "status"}
                and x["id"] == source["id"]
                and x["indexModuleIds"] == source["moduleIds"]
                and all(mid in MODULE_KEYS for mid in x["indexModuleIds"])
                and len(x["indexModuleIds"]) >= 5
                and len(x["hypotheticalFailureBoundary"]) >= 135
                and x["evidence"] ==
                    "FUTURE_REAL_OWNER_AND_INTEGRATION_PROOF_MISSING"
                and x["status"] == "SOURCE_ONLY_NOT_EXECUTED",
                "future interlock wrongly qualified or original source pairing changed")
    if check_human:
        md = human_text if human_text is not None else (
            root / REPORT).read_text(encoding="utf-8")
        fence = chr(96) * 3
        marker = "\n## Appendix A: canonical full 47-module machine scan\n\n" + fence + "json\n"
        require(md.count(marker) == 1 and md.endswith("\n" + fence + "\n"),
                "full human report needs exactly one final machine appendix")
        visible, appendix = md.split(marker)
        raw, tail = appendix.split("\n" + fence + "\n", 1)
        require(tail == "" and
                json.loads(raw, object_pairs_hook=unique) == p,
                "human report source packet not identical to machine")
        for row in rows:
            require(("### " + row["id"] + ": " + row["title"]) in visible
                    and row["plausibleFailure"] in visible
                    and row["requiredFutureActualOwnerProof"] in visible
                    and all(sub in visible for sub in row["originalSessions"]),
                    "human report omitted module-specific original full scope/proof")
        for row in interlocks:
            require(("### " + row["id"]) in visible
                    and row["hypotheticalFailureBoundary"] in visible,
                    "human report omitted original cross-area interlock")
    return {
        "documentaryOnly": True, "originalModules": len(rows),
        "exactOriginalModuleSessions": sum(len(x["originalSessions"])
                                            for x in rows),
        "sourceSpecificUnqualifiedActualOwnerRoutes": len(rows),
        "newCrossAreaUnexecutedInterlocks": len(interlocks),
        "previousM13OpenQuestions": 96, "previousFutureNegativesNotExecuted": 74,
        "qualifiedRealOwners": 0, "independentFCSApproval": False,
        "m13Frozen": False, "runtime": "NOT_ADMITTED",
    }


def verify_all(root: Path = ROOT) -> dict:
    return validate(read_packet(root), root, check_human=True)


if __name__ == "__main__":
    try:
        print("M14–M60 SOURCE-ONLY FCS PASS " +
              json.dumps(verify_all(), sort_keys=True) +
              " | NO independent owner or runtime")
    except (FCSIntegrityError, OSError, ValueError, TypeError,
            UnicodeError, KeyError, json.JSONDecodeError) as e:
        raise SystemExit("M14–M60 FCS FAIL CLOSED: " + str(e)) from e
