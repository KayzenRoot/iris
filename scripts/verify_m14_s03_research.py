"""IRIS-WO-0078: offline source-only M14 S03 research integrity verifier."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M14-S03-SOURCE-RESEARCH.json"
REPORT = "planning/research/M14-S03-EMPIRICAL-CARD-EVIDENCE-DESIGN.md"
BASE = "90eacaac4ead5c1c0858c60f2a5ef40400bd51ad"
TREE = "c3694c28d4b751a40d15d0165ce4e2a6e6c82f30"
SOURCE_ROWS = (
    ("INDEX", "planning/MASTER-MODULE-INDEX-CURRENT.md", "02e6394cc7e75d5466ab22801b4cc7dbe66500be", "S03 — S03 Empirical quality/latency/VRAM model cards"),
    ("FCS", "planning/reviews/M14-M60-FORWARD-COMPATIBILITY-SOURCE-SCAN.md", "5bac62b5b1a07fb97e43ea5c76d20dc5419c2cec", "S03 — S03 Empirical quality/latency/VRAM model cards"),
    ("S01", ".engineering/evidence/M14-S01-SOURCE-RESEARCH.json", "10fe325b3928e58797266ae4ba0b65c87cd532fc", '"session": "S01"'),
    ("S02", ".engineering/evidence/M14-S02-SOURCE-RESEARCH.json", "d3ac994e130bc54c566449dc0d6efc19a0ca2698", '"session": "S02"'),
    ("S02_REPORT", "planning/research/M14-S02-CAPABILITY-GENOME-TASK-TAXONOMY.md", "9799f5169522f0cb44b8049e4f4e9215bf19f0e4", "Fourteen future hostile cases, NOT EXECUTED"),
    ("M01_CONTRACT", "planning/contracts/M01-MODULE-CONTRACT-FREEZE-CANDIDATE.md", "48e00ca6ec3da8a5185fa49ccad37f14b6a5926a", "FROZEN_APPROVED"),
    ("M01", "docs/M01-QUALITY-KERNEL.md", "df4f899ad414c47ad379f26fe1782edb6f43cf6f", "m01-contract-v1.0"),
    ("M07", "docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md", "2a0b95dd3cc665e2206e454caef5858ef7fb61b0", "M07 does not lower quality targets"),
    ("M08", "docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md", "461e0f332d9be2af694634bbdc8cf67e29d56393", "M08 records empirical performance evidence"),
    ("M09", "docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md", "d12b4f48030c1a57b8e6228df39f35dac8c2b20a", "M09 is the provider-neutral resource-state"),
    ("M10", "planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md", "f69ec3e3eab24b47c0e31832d64d9ab9cce21828", "Implementation authority: NOT ADMITTED"),
    ("D01", ".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json", "8877331a5004a3e816e4c42fb521ff3408bad08a", "B_FUTURE_OWNER_RECEIPT"),
)
STATE_IDS = ("CLAIM_ONLY", "PROTOCOL_DEFINED_ONLY", "RAW_OBSERVATION_UNQUALIFIED",
             "QUALIFIED_EMPIRICAL_FUTURE", "STALE_OR_INVALIDATED")

class M14S03IntegrityError(ValueError):
    """Raised on source drift, fabricated empirical evidence or report mismatch."""

def require(ok: bool, message: str) -> None:
    """Reject a violated source-integrity or original authority condition."""
    if not ok:
        raise M14S03IntegrityError(message)

def git_blob(data: bytes) -> str:
    """Recreate Git blob object SHA-1 for original checked-in bytes."""
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def unique_json_keys(pairs: list[tuple[str, object]]) -> dict:
    """Reject duplicate JSON fields before evaluating source authorization."""
    out = {}
    for key, val in pairs:
        require(key not in out, "duplicate JSON key " + key)
        out[key] = val
    return out

def read_json(root: Path = ROOT) -> dict:
    """Load exact machine evidence with closed duplicate-key semantics."""
    p = json.loads((root / PACKET).read_text(encoding="utf-8"),
                   object_pairs_hook=unique_json_keys)
    require(type(p) is dict, "S03 evidence must be an object")
    return p

def render_report(p: dict) -> str:
    """Render the complete nonbinding machine source evidence as human Markdown."""
    rows = ["# M14 S03 | Empirical Quality, Latency & VRAM Card Evidence Design", "",
            "**SOURCE RESEARCH ONLY | IRIS-WO-0078 | issue #208 OPEN.**",
            "No actual model-quality result, latency sample, VRAM measurement, commercial right, GPU/probe/provider execution or qualified model-card owner approval.", "",
            "## 1. Original exact source authority", "",
            f'Original protected main: {p["sourceBaseSha"]}; tree: {p["sourceBaseTreeSha"]}.', ""]
    for x in p["sourceDocs"]:
        rows.append(f'- {x["role"]}: [{x["path"]}](../../{x["path"]}) Git blob {x["gitBlobSha1"]}; original text anchor: {x["exactNeedle"]}.')
    rows.extend(["", "## 2. Eight proposed non-adopted model-card evidence facets", ""])
    for x in p["facets"]:
        rows.extend([f'### {x["id"]}: {x["title"]}', "", x["boundary"] + " " + x["status"] + ".", ""])
    rows.extend(["## 3. Five possible evidence state labels, vocabulary only", "",
                 "A future QUALIFIED_EMPIRICAL_FUTURE label has zero instances here and confers no runtime or quality authority.", ""])
    for x in p["states"]:
        rows.append(f'- {x["id"]}: {x["status"]}.')
    rows.extend(["", "## 4. Four future architecture alternatives, NONE selected", ""])
    for x in p["alternatives"]:
        rows.append(f'- {x["id"]}: {x["title"]}; {x["status"]}; selected={x["selected"]}; tradeoffs: {x["tradeoffs"]}.')
    rows.extend(["", "## 5. Twenty NEW OPEN/UNRATED S03 owner questions", ""])
    for x in p["questions"]:
        rows.extend([f'### {x["id"]}', "", x["question"], "",
                     f'- Source roles: {", ".join(x["sourceRoles"])}. {x["status"]}; risk {x["risk"]}; owner answer {x["ownerAnswer"]}; authority {x["authority"]}.', ""])
    rows.extend(["## 6. Sixteen future negative designs, NOT_EXECUTED", ""])
    for x in p["negativeScenarios"]:
        rows.extend([f'### {x["id"]}', "", x["trigger"], "",
                     f'- {x["oracle"]}; questions: {", ".join(x["questionIds"])}; {x["status"]}.', ""])
    rows.extend(["## 7. Owner and physical-runtime STOP", "",
                 f'- Prior S01: {p["previousS01QuestionsOpen"]} questions and {p["previousS01FutureCases"]} future cases; S02: {p["previousS02QuestionsOpen"]} questions and {p["previousS02FutureCases"]} future cases.',
                 f'- Prior M13: {p["previousM13QuestionsOpen"]} owner questions, {p["previousM13FutureCases"]} future cases.',
                 f'- B {p["ownerB"]}, C01 {p["m09C01"]}, H01-H04 {p["h01h02h03h04"]}, M10-M13 runtime {p["m10m11m12m13Runtime"]}.',
                 f'- STOP: {p["stop"]}', ""])
    return "\n".join(rows) + "\n"

def verify_packet(p: dict, root: Path = ROOT, *, verify_markdown: bool = True) -> dict:
    """Verify immutable original source SHA, unmeasured authority fence and report."""
    keys = {"schemaVersion","workOrder","issue","module","session","sourceBaseSha",
            "sourceBaseTreeSha","status","ownerApproval","schemaAdopted",
            "realMeasurements","realQualityScores","realLatencySamples",
            "realVramObservations","runtime","sourceDocs","facets","states",
            "alternatives","questions","negativeScenarios","previousS01QuestionsOpen",
            "previousS01FutureCases","previousS02QuestionsOpen","previousS02FutureCases",
            "previousM13QuestionsOpen","previousM13FutureCases","ownerB","m09C01",
            "h01h02h03h04","m10m11m12m13Runtime","stop"}
    require(type(p) is dict and set(p) == keys, "unknown/missing S03 source packet fields")
    exact = {"schemaVersion":"iris-m14-s03-source-research-v0.1",
             "workOrder":"IRIS-WO-0078","issue":208,"module":"M14","session":"S03",
             "sourceBaseSha":BASE,"sourceBaseTreeSha":TREE,
             "status":"SOURCE_ONLY_NO_REAL_MEASUREMENTS","ownerApproval":"NONE",
             "schemaAdopted":False,"realMeasurements":0,"realQualityScores":0,
             "realLatencySamples":0,"realVramObservations":0,"runtime":"NOT_ADMITTED",
             "previousS01QuestionsOpen":16,"previousS01FutureCases":12,
             "previousS02QuestionsOpen":18,"previousS02FutureCases":14,
             "previousM13QuestionsOpen":96,"previousM13FutureCases":74,
             "ownerB":"DIRECTION_ONLY","m09C01":"UNADOPTED_NOT_FROZEN",
             "h01h02h03h04":"OPEN_HIGH_FOR_FUTURE_FREEZE",
             "m10m11m12m13Runtime":"NOT_ADMITTED"}
    for field, val in exact.items():
        require(type(p[field]) is type(val) and p[field] == val,
                "forged original owner, measurement or runtime claim: " + field)
    require(type(p["stop"]) is str and len(p["stop"]) >= 460
            and all(word in p["stop"] for word in (
                "OPEN_UNRATED_PENDING_QUALIFIED_OWNER","SPECIFIED_NOT_EXECUTED",
                "ZERO","H01-H04","NOT_ADMITTED","M01","M02")),
            "owner, M01/M02 or runtime STOP removed")
    sources = p["sourceDocs"]
    require(type(sources) is list and len(sources) == len(SOURCE_ROWS),
            "original source role count changed")
    for row, (role,path,sha,needle) in zip(sources, SOURCE_ROWS):
        require(type(row) is dict and row == {"role":role,"path":path,
                "gitBlobSha1":sha,"exactNeedle":needle},
                "original source role or fingerprint changed: " + role)
        try:
            raw = (root / path).read_bytes()
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise M14S03IntegrityError("original source unreadable: " + role) from exc
        require(git_blob(raw) == sha and needle in text,
                "original source blob/needle drift: " + role)
    index = (root / SOURCE_ROWS[0][1]).read_text(encoding="utf-8")
    for session in (
        "S01 — S01 Model identity, versions, hashes, license and provenance",
        "S02 — S02 Capability Genome and task taxonomy",
        "S03 — S03 Empirical quality/latency/VRAM model cards",
        "S04 — S04 Hardware compatibility and reliability evidence",
        "S05 — S05 Model drift, deprecation and lifecycle governance",
    ):
        require(session in index, "active original M14 session drift: " + session)
    facets = p["facets"]
    require(type(facets) is list and [x.get("id") for x in facets] ==
            [f"FAC{i:02d}" for i in range(1,9)], "eight facets absent or reordered")
    for x in facets:
        require(type(x) is dict and set(x) == {"id","title","status","boundary"}
                and x["status"] == "NONBINDING_UNADOPTED"
                and len(x["boundary"]) >= 66,
                "evidence facet adopted or caveat truncated")
    states = p["states"]
    require(type(states) is list and [x.get("id") for x in states] == list(STATE_IDS),
            "five state labels absent/reordered")
    for x in states:
        require(type(x) is dict and set(x) == {"id","status"}
                and x["status"] == "VOCABULARY_ONLY_NO_ACTUAL_RECORD",
                "future state promoted to actual measurement")
    alts = p["alternatives"]
    require(type(alts) is list and [x.get("id") for x in alts] ==
            [f"ALT{i:02d}" for i in range(1,5)], "four alternative designs changed")
    for x in alts:
        require(type(x) is dict and set(x) == {"id","title","status","selected","tradeoffs"}
                and x["selected"] is False and x["status"] == "RESEARCH_ONLY_UNSELECTED"
                and type(x["tradeoffs"]) is str and len(x["tradeoffs"]) >= 100,
                "unapproved empirical architecture selected")
    qq = p["questions"]
    qids = [f"M14-S03-U{i:02d}" for i in range(1,21)]
    require(type(qq) is list and [x.get("id") for x in qq] == qids,
            "twenty original unresolved owner questions changed")
    known = {x[0] for x in SOURCE_ROWS}
    for x in qq:
        require(type(x) is dict and set(x) == {"id","question","sourceRoles",
                 "status","risk","ownerAnswer","authority"}
                and x["status"] == "OPEN_UNRATED_PENDING_QUALIFIED_OWNER"
                and x["risk"] == "UNRATED" and x["ownerAnswer"] is None
                and x["authority"] == "NONE" and len(x["question"]) >= 85
                and type(x["sourceRoles"]) is list and len(x["sourceRoles"]) >= 2
                and len(set(x["sourceRoles"])) == len(x["sourceRoles"])
                and all(role in known for role in x["sourceRoles"]),
                "forged owner answer or unanchored S03 source question")
    negative = p["negativeScenarios"]
    require(type(negative) is list and [x.get("id") for x in negative] ==
            [f"M14-S03-N{i:02d}" for i in range(1,17)],
            "sixteen future adversarial cases absent/reordered")
    for x in negative:
        require(type(x) is dict and set(x) == {"id","trigger","oracle",
                "questionIds","status"}
                and x["status"] == "SPECIFIED_NOT_EXECUTED"
                and x["oracle"] == "NO_UNQUALIFIED_EVIDENCE_OR_RUNTIME_GRANT"
                and len(x["trigger"]) >= 80 and type(x["questionIds"]) is list
                and len(x["questionIds"]) >= 1 and len(set(x["questionIds"])) == len(x["questionIds"])
                and all(q in qids for q in x["questionIds"]),
                "future negative falsely executed or reference forged")
    if verify_markdown:
        require((root / REPORT).read_text(encoding="utf-8") == render_report(p),
                "human S03 source report does not match machine packet")
    return {"exactOriginalSources":len(sources),"unadoptedFacets":len(facets),
            "futureEvidenceLabelsOnly":len(states),"unselectedAlternatives":len(alts),
            "newOpenOwnerQuestions":len(qq),"futureCasesNotExecuted":len(negative),
            "actualPhysicalMeasurements":0}

def verify_all(root: Path = ROOT) -> dict:
    """Validate the checked-in S03 machine packet and exact human projection."""
    return verify_packet(read_json(root), root, verify_markdown=True)

if __name__ == "__main__":
    print(json.dumps(verify_all(), sort_keys=True))
