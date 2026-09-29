"""IRIS-WO-0079: fail-closed offline M14 S04 source/authority evidence verifier."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M14-S04-SOURCE-RESEARCH.json"
REPORT = "planning/research/M14-S04-HARDWARE-RELIABILITY-EVIDENCE.md"
BASE = "88f61cbc8091cb9e353ad3d953085f907aef11c5"
TREE = "b0963f137ddf0ca7b7e2c70c21d5b41b361380df"
SOURCE_ROWS = [["INDEX","planning/MASTER-MODULE-INDEX-CURRENT.md","02e6394cc7e75d5466ab22801b4cc7dbe66500be","S04 — S04 Hardware compatibility and reliability evidence"],["FCS","planning/reviews/M14-M60-FORWARD-COMPATIBILITY-SOURCE-SCAN.md","5bac62b5b1a07fb97e43ea5c76d20dc5419c2cec","S04 — S04 Hardware compatibility and reliability evidence"],["S01",".engineering/evidence/M14-S01-SOURCE-RESEARCH.json","10fe325b3928e58797266ae4ba0b65c87cd532fc","\"session\": \"S01\""],["S02",".engineering/evidence/M14-S02-SOURCE-RESEARCH.json","d3ac994e130bc54c566449dc0d6efc19a0ca2698","\"session\": \"S02\""],["S03",".engineering/evidence/M14-S03-SOURCE-RESEARCH.json","cf49ed6140976a14dbd0ac469bb79ed0091e624d","\"session\": \"S03\""],["S03_REPORT","planning/research/M14-S03-EMPIRICAL-CARD-EVIDENCE-DESIGN.md","9ba713ad3762696feb91b2e3e1aeefc06579dc38","Twenty NEW OPEN/UNRATED S03 owner questions"],["M01_NORM","planning/contracts/M01-MODULE-CONTRACT-FREEZE-CANDIDATE.md","48e00ca6ec3da8a5185fa49ccad37f14b6a5926a","FROZEN_APPROVED"],["M07","docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md","2a0b95dd3cc665e2206e454caef5858ef7fb61b0","M07 does not lower quality targets"],["M07_NORM","planning/modules/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md","9306e4937ccfb433ff4a0392846aa215ffd6e2a0","M07 does **not** benchmark performance"],["M08","docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md","461e0f332d9be2af694634bbdc8cf67e29d56393","M08 records empirical performance evidence"],["M08_NORM","planning/modules/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md","804387a28c318fc82f53e51651f279d76895095c","M08 is the empirical performance-characterization authority"],["M09","docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md","d12b4f48030c1a57b8e6228df39f35dac8c2b20a","M09 is the provider-neutral resource-state"],["M10","planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md","f69ec3e3eab24b47c0e31832d64d9ab9cce21828","Implementation authority: NOT ADMITTED"],["M13_S04","planning/research/M13-S04-CPU-GPU-OVERLAP-IO-STORAGE.md","cab009ad3e0a380b136f5af5cc902b09481be2a8","SOURCE-ONLY RESEARCH; NO RUNTIME"],["D01",".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json","8877331a5004a3e816e4c42fb521ff3408bad08a","B_FUTURE_OWNER_RECEIPT"]]
STATE_IDS = ("VENDOR_DECLARED_UNVERIFIED", "SOURCE_QUALIFIED_DECLARATION_ONLY",
             "UNKNOWN_OR_CONFLICTED", "FUTURE_REPRESENTATIVE_MEASUREMENT",
             "FUTURE_OWNER_QUALIFIED_AT_USE")

class M14S04IntegrityError(ValueError):
    """Typed failure for false compatibility evidence or original authority drift."""

def require(condition: bool, reason: str) -> None:
    """Fail closed on any source or research authority contradiction."""
    if not condition:
        raise M14S04IntegrityError(reason)

def dict_ids(items: object) -> list | None:
    """Extract ordered IDs only from a list of dictionaries; otherwise fail closed."""
    if type(items) is not list or not all(type(item) is dict for item in items):
        return None
    return [item.get("id") for item in items]

def git_blob(data: bytes) -> str:
    """Compute Git's exact blob-object SHA1 from source bytes."""
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def unique_json_keys(pairs: list[tuple[str, object]]) -> dict:
    """Reject ambiguous duplicate JSON packet fields before interpretation."""
    out = {}
    for key, value in pairs:
        require(key not in out, "duplicate JSON key: " + key)
        out[key] = value
    return out

def read_json(root: Path = ROOT) -> dict:
    """Read the immutable-format local S04 packet with duplicate-key rejection."""
    p = json.loads((root / PACKET).read_text(encoding="utf-8"),
                   object_pairs_hook=unique_json_keys)
    require(type(p) is dict, "S04 evidence must be an object")
    return p

def render_report(p: dict) -> str:
    """Project all source-only machine evidence into exact reproducible human Markdown."""
    rows = ["# M14 S04 | Hardware Compatibility & Reliability Evidence", "",
            "**SOURCE RESEARCH ONLY | IRIS-WO-0079 | issue #210 OPEN.**",
            "No measured hardware fit, benchmark, real GPU provider run, owner-signed capability, native worker or executable contract.", "",
            "## 1. Exact protected original source evidence", "",
            f'Protected original main {p["sourceBaseSha"]}; tree {p["sourceBaseTreeSha"]}.', ""]
    for x in p["sourceDocs"]:
        rows.append(f'- {x["role"]}: [{x["path"]}](../../{x["path"]}) Git blob {x["gitBlobSha1"]}; text anchor: {x["exactNeedle"]}.')
    rows.extend(["", "## 2. Eight research-only compatibility and reliability facets", "",
                 "All dimensions are hypotheses with no active owner, runtime or empirical qualification.", ""])
    for x in p["facets"]:
        rows.extend([f'### {x["id"]}: {x["title"]}', "", x["caveat"] + " " + x["status"] + ".", ""])
    rows.extend(["## 3. Five evidence labels, VOCABULARY ONLY", "",
                 "An imagined qualified label is not an observed real host/model capability.", ""])
    for x in p["states"]:
        rows.append(f'- {x["id"]}: {x["status"]}.')
    rows.extend(["", "## 4. Four unselected compatibility evidence alternatives", ""])
    for x in p["alternatives"]:
        rows.append(f'- {x["id"]}: {x["title"]}; {x["tradeoffs"]}; {x["status"]}; selected={x["selected"]}.')
    rows.extend(["", "## 5. Twenty-two NEW OPEN/UNRATED S04 owner questions", ""])
    for x in p["questions"]:
        rows.extend([f'### {x["id"]}', "", x["question"], "",
                     f'- Exact source roles: {", ".join(x["sourceRoles"])}; {x["status"]}; risk {x["risk"]}; owner answer {x["ownerAnswer"]}; execution {x["executionAuthority"]}.', ""])
    rows.extend(["## 6. Eighteen future hostile designs, NOT_EXECUTED", ""])
    for x in p["negativeScenarios"]:
        rows.extend([f'### {x["id"]}', "", x["trigger"], "",
                     f'- {x["nonAuthorizingOracle"]}; related {", ".join(x["questionIds"])}; {x["status"]}.', ""])
    rows.extend(["## 7. Historical pending owner and runtime STOP", "",
                 f'- Previous S01 {p["priorS01QuestionsOpen"]}/{p["priorS01FutureCases"]}, S02 {p["priorS02QuestionsOpen"]}/{p["priorS02FutureCases"]}, S03 {p["priorS03QuestionsOpen"]}/{p["priorS03FutureCases"]} remain OPEN/UNRATED / NOT_EXECUTED.',
                 f'- Historical M13 {p["priorM13QuestionsOpen"]}/{p["priorM13FutureCases"]} still unresolved/unexecuted.',
                 f'- M09 B {p["ownerB"]}, C01 {p["m09C01"]}, H01–H04 {p["highs"]}, M10–M13 native {p["m10m11m12m13Runtime"]}.',
                 f'- STOP: {p["stop"]}', ""])
    return "\n".join(rows) + "\n"

def verify_packet(p: dict, root: Path = ROOT, *, verify_markdown: bool = True) -> dict:
    """Check pinned immutable sources, nonadmitting authority and exact human projection."""
    fields = {"schemaVersion","workOrder","issue","module","session","sourceBaseSha",
              "sourceBaseTreeSha","status","ownerApproval","hardwareContractAdopted",
              "backendSelected","realGpuBenchmarks","realHardwareCompatibilityReceipts",
              "realProviderTests","realM09Leases","nativeRuntime","sourceDocs","facets",
              "states","alternatives","questions","negativeScenarios","priorS01QuestionsOpen",
              "priorS01FutureCases","priorS02QuestionsOpen","priorS02FutureCases",
              "priorS03QuestionsOpen","priorS03FutureCases","priorM13QuestionsOpen",
              "priorM13FutureCases","ownerB","m09C01","highs","m10m11m12m13Runtime","stop"}
    require(type(p) is dict and set(p) == fields, "missing or invented S04 source packet fields")
    exact = {"schemaVersion":"iris-m14-s04-source-research-v0.1","workOrder":"IRIS-WO-0079",
             "issue":210,"module":"M14","session":"S04","sourceBaseSha":BASE,
             "sourceBaseTreeSha":TREE,"status":"SOURCE_RESEARCH_ONLY_NO_HARDWARE_QUALIFICATION",
             "ownerApproval":"NONE","hardwareContractAdopted":False,"backendSelected":False,
             "realGpuBenchmarks":0,"realHardwareCompatibilityReceipts":0,
             "realProviderTests":0,"realM09Leases":0,"nativeRuntime":"NOT_ADMITTED",
             "priorS01QuestionsOpen":16,"priorS01FutureCases":12,
             "priorS02QuestionsOpen":18,"priorS02FutureCases":14,
             "priorS03QuestionsOpen":20,"priorS03FutureCases":16,
             "priorM13QuestionsOpen":96,"priorM13FutureCases":74,
             "ownerB":"B_FUTURE_OWNER_RECEIPT_DIRECTION_ONLY",
             "m09C01":"UNADOPTED_NOT_FROZEN","highs":"ALL_OPEN_HIGH_FOR_FUTURE_FREEZE",
             "m10m11m12m13Runtime":"NOT_ADMITTED"}
    for k, v in exact.items():
        require(type(p[k]) is type(v) and p[k] == v,
                "forged owner, compatibility, source or runtime claim: " + k)
    stop = p["stop"]
    require(type(stop) is str and len(stop) >= 480
            and all(x in stop for x in ("SOURCE_RESEARCH_ONLY",
                     "OPEN_UNRATED_PENDING_QUALIFIED_OWNER", "SPECIFIED_NOT_EXECUTED",
                     "ZERO", "UNADOPTED_NOT_FROZEN", "HIGH_FOR_FUTURE_FREEZE",
                     "NOT_ADMITTED", "M01", "M02")),
            "historical owner, quality or runtime STOP removed")
    sources = p["sourceDocs"]
    require(type(sources) is list and len(sources) == len(SOURCE_ROWS),
            "missing original source roles")
    for row, (role, path, sha, needle) in zip(sources, SOURCE_ROWS):
        require(type(row) is dict and row == {"role":role,"path":path,
                "gitBlobSha1":sha,"exactNeedle":needle},
                "original source role, SHA or needle replaced: " + role)
        try:
            raw = (root / path).read_bytes()
            source_text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise M14S04IntegrityError("original source unreadable: " + role) from exc
        require(git_blob(raw) == sha and needle in source_text,
                "original source Git blob or text drift: " + role)
    index = (root / SOURCE_ROWS[0][1]).read_text(encoding="utf-8")
    for session in ("S01 — S01 Model identity, versions, hashes, license and provenance",
                    "S02 — S02 Capability Genome and task taxonomy",
                    "S03 — S03 Empirical quality/latency/VRAM model cards",
                    "S04 — S04 Hardware compatibility and reliability evidence",
                    "S05 — S05 Model drift, deprecation and lifecycle governance"):
        require(session in index, "active M14 session source drift: " + session)
    facets = p["facets"]
    require(dict_ids(facets) == ["CF01_COMPOSITE_TASK_BINDING","CF02_M07_RUNTIME_BINDING","CF03_M08_REPRESENTATIVE_EVIDENCE","CF04_KERNEL_BACKEND_OPERATORS","CF05_RESOURCE_RELIABILITY","CF06_CONFLICT_AND_FRESHNESS","CF07_RIGHTS_AND_ISOLATION","CF08_AUTHORITY_AND_FEEDBACK"],
            "eight original S04 research facets changed")
    for x in facets:
        require(type(x) is dict and set(x) == {"id","title","caveat","status"}
                and x["status"] == "SOURCE_TAXONOMY_NOT_ADOPTED"
                and len(x["caveat"]) >= 80, "unqualified compatibility facet adoption")
    states = p["states"]
    require(dict_ids(states) == list(STATE_IDS),
            "five future evidence labels missing/reordered")
    for x in states:
        require(type(x) is dict and set(x) == {"id","status"}
                and x["status"] == "VOCABULARY_ONLY_NO_REAL_COMPATIBILITY",
                "unverified compatibility label promoted")
    alternatives = p["alternatives"]
    require(dict_ids(alternatives) == ["ALT01_FLAT_HARDWARE_TAG_MATRIX","ALT02_EXACT_TASK_HARDWARE_TUPLE","ALT03_VERSIONED_EVIDENCE_DAG","ALT04_FUTURE_SIGNED_AT_USE_RECEIPT"],
            "four research alternatives changed")
    for x in alternatives:
        require(type(x) is dict and set(x) == {"id","title","tradeoffs","selected","status"}
                and x["selected"] is False and x["status"] == "RESEARCH_ONLY_NOT_SELECTED"
                and len(x["tradeoffs"]) >= 100, "unapproved alternative selected or caveat omitted")
    qq = p["questions"]
    qids = [f"M14-S04-U{i:02d}" for i in range(1,23)]
    require(dict_ids(qq) == qids,
            "22 new original owner questions missing/reordered")
    roles = {row[0] for row in SOURCE_ROWS}
    for x in qq:
        require(type(x) is dict and set(x) == {"id","question","sourceRoles","status",
                "risk","ownerAnswer","executionAuthority"}
                and x["status"] == "OPEN_UNRATED_PENDING_QUALIFIED_OWNER"
                and x["risk"] == "UNRATED" and x["ownerAnswer"] is None
                and x["executionAuthority"] == "NONE" and len(x["question"]) >= 85
                and type(x["sourceRoles"]) is list and len(x["sourceRoles"]) >= 2
                and len(set(x["sourceRoles"])) == len(x["sourceRoles"])
                and all(v in roles for v in x["sourceRoles"]),
                "owner questions promoted or source roles forged")
    negatives = p["negativeScenarios"]
    require(dict_ids(negatives) == [f"M14-S04-N{i:02d}" for i in range(1,19)],
            "18 original future negative cases missing/reordered")
    for x in negatives:
        require(type(x) is dict and set(x) == {"id","trigger","questionIds",
                "nonAuthorizingOracle","status"}
                and x["status"] == "SPECIFIED_NOT_EXECUTED"
                and x["nonAuthorizingOracle"] == "NO_CURRENT_COMPATIBILITY_OR_RUNTIME_PERMISSION"
                and len(x["trigger"]) >= 80 and type(x["questionIds"]) is list
                and len(x["questionIds"]) >= 1
                and len(set(x["questionIds"])) == len(x["questionIds"])
                and all(v in qids for v in x["questionIds"]),
                "future design falsely executed or nonlocal owner question referenced")
    if verify_markdown:
        require((root / REPORT).read_text(encoding="utf-8") == render_report(p),
                "human S04 source report does not match exact machine projection")
    return {"originalSourcePinsVerified":len(sources),"nonadoptedFacets":len(facets),
            "futureEvidenceLabelsOnly":len(states),"unselectedAlternatives":len(alternatives),
            "newOpenOwnerQuestions":len(qq),"futureNegativesNotExecuted":len(negatives),
            "realHardwareBenchmarks":0}

def verify_all(root: Path = ROOT) -> dict:
    """Recheck the checked-in machine packet, original sources and human projection."""
    return verify_packet(read_json(root), root, verify_markdown=True)

if __name__ == "__main__":
    print(json.dumps(verify_all(),sort_keys=True))
