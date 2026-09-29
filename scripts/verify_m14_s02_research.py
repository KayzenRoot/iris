"""WO0077: pure offline M14 S02 source provenance and unadopted Genome integrity."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M14-S02-SOURCE-RESEARCH.json"
REPORT = "planning/research/M14-S02-CAPABILITY-GENOME-TASK-TAXONOMY.md"
BASE = "1cda2aa29e77474fa0e27c99d88646351cae69b7"
TREE = "8c523de8b9422174ee33f563595becdbf5fbd28b"
SOURCES = [
    ("INDEX", "planning/MASTER-MODULE-INDEX-CURRENT.md", "02e6394cc7e75d5466ab22801b4cc7dbe66500be", "S02 — S02 Capability Genome and task taxonomy"),
    ("FCS", "planning/reviews/M14-M60-FORWARD-COMPATIBILITY-SOURCE-SCAN.md", "5bac62b5b1a07fb97e43ea5c76d20dc5419c2cec", "### M14: Model Registry & Empirical Model Cards"),
    ("S01_PACKET", ".engineering/evidence/M14-S01-SOURCE-RESEARCH.json", "10fe325b3928e58797266ae4ba0b65c87cd532fc", '"module": "M14"'),
    ("S01_REPORT", "planning/research/M14-S01-MODEL-IDENTITY-LICENSE-PROVENANCE.md", "f07ed63d30c53f38ff77b4f0fbd4934d44f9624d", "Sixteen NEW OPEN/UNRATED M14 S01 owner questions"),
    ("M01", "docs/M01-QUALITY-KERNEL.md", "df4f899ad414c47ad379f26fe1782edb6f43cf6f", "m01-contract-v1.0"),
    ("M03", "planning/contracts/M03-MODULE-CONTRACT-FREEZE-CANDIDATE.md", "bb640aaa1711e1c0b939769d579e887029bcbd17", "m03-contract-v1.0"),
    ("M04", "planning/contracts/M04-MODULE-CONTRACT-FREEZE-CANDIDATE.md", "c84c6645a84e1fa41ace5e627411bf953fc77dc5", "m04-contract-v1.0"),
    ("M08", "docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md", "461e0f332d9be2af694634bbdc8cf67e29d56393", "M08 records empirical performance evidence"),
    ("M09", "docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md", "d12b4f48030c1a57b8e6228df39f35dac8c2b20a", "M09 is the provider-neutral resource-state"),
    ("M10", "planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md", "f69ec3e3eab24b47c0e31832d64d9ab9cce21828", "Implementation authority: NOT ADMITTED"),
    ("M13S02", "planning/research/M13-S02-COMPILATION-ATTENTION-BACKENDS.md", "c033ac4696ad4a188ca5605470bf9b29396eb3ad", "UNSELECTED, UNINSTALLED, UNBENCHMARKED"),
    ("D01", ".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json", "8877331a5004a3e816e4c42fb521ff3408bad08a", "B_FUTURE_OWNER_RECEIPT"),
]
DIM_IDS = ("DIM01_INPUT_OUTPUT_SHAPES", "DIM02_SEMANTIC_TASK_OPERATION",
           "DIM03_COMPOSITE_MODEL_FEATURES", "DIM04_EXECUTION_ENVELOPE_HINT",
           "DIM05_QUALITY_AND_RELIABILITY_CANDIDATE", "DIM06_RIGHTS_TRUST_LIFECYCLE")
TASK_IDS = ("TASK01_TEXT", "TASK02_IMAGE", "TASK03_VIDEO", "TASK04_AUDIO",
            "TASK05_3D", "TASK06_MULTIMODAL_COMPOSITE", "TASK07_STRUCTURED_CONTROL")
EVIDENCE_IDS = ("SELF_REPORTED", "INFERRED", "UNKNOWN", "OWNER_VERIFIED", "EMPIRICALLY_MEASURED")
ALT_IDS = ("ALT01_UNTYPED_TASK_TAGS", "ALT02_TYPED_IO_TASK_MATRIX",
           "ALT03_PROVENANCE_AWARE_CAPABILITY_GRAPH", "ALT04_QUALIFIED_OWNER_RECEIPT")

class M14S02IntegrityError(ValueError):
    """Unqualified capability research was changed into unsupported authority."""

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise M14S02IntegrityError(reason)

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def unique_json_keys(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    for key, val in pairs:
        require(key not in out, "duplicate JSON key: " + key)
        out[key] = val
    return out

def read_json(root: Path = ROOT) -> dict:
    p = json.loads((root / PACKET).read_text(encoding="utf-8"),
                   object_pairs_hook=unique_json_keys)
    require(type(p) is dict, "evidence packet must be an object")
    return p

def render_report(p: dict) -> str:
    l = ["# M14 S02 | Capability Genome & Multimodal Task Taxonomy", "",
         "**NONBINDING SOURCE RESEARCH | IRIS-WO-0077 | issue #206 OPEN.**",
         "No qualified M14 Genome contract, verified vendor feature, legal permission, real benchmark, model install or provider execution is admitted.", "",
         "## 1. Exact original source authority", "",
         f'Original protected base: {p["sourceBaseSha"]}; tree: {p["sourceBaseTreeSha"]}. All source claims are original Git blob anchored:', ""]
    for s in p["sourceDocs"]:
        l.append(f'- {s["role"]}: [{s["path"]}](../../{s["path"]}) | original blob {s["gitBlobSha1"]} | exact anchor {s["exactNeedle"]}.')
    l.extend(["", "## 2. Six non-authorizing capability dimensions", "",
              "Every proposed dimension is conceptual: a claim is not a tested ability, real owner receipt or operation permission.", ""])
    for d in p["dimensions"]:
        l.extend([f'### {d["id"]}: {d["title"]}', "", f'- Limitation: {d["caveat"]}',
                  f'- Pending owner roles: {d["pendingOwners"]}. Status: {d["status"]}.', ""])
    l.extend(["## 3. Seven provisional task families, none adopted", ""])
    for t in p["taskFamilies"]:
        l.append(f'- {t["id"]}: {t["title"]}; unresolved: {t["unresolvedBoundary"]}; {t["status"]}.')
    l.extend(["", "## 4. Five source-evidence states, VOCABULARY ONLY", "",
              "OWNER_VERIFIED and EMPIRICALLY_MEASURED below are mere future labels; no such real records are present.", ""])
    for s in p["evidenceStates"]:
        l.append(f'- {s["id"]}: {s["meaning"]}; {s["status"]}.')
    l.extend(["", "## 5. Four unselected taxonomy alternatives", ""])
    for x in p["alternatives"]:
        l.extend([f'### {x["id"]}: {x["title"]}', "", f'- Tradeoff: {x["tradeoffs"]}',
                  f'- {x["status"]}; selected={x["selected"]}.', ""])
    l.extend(["## 6. Eighteen NEW unresolved M14 S02 owner questions", "",
              "These add no owner action to the sixteen still-open S01 questions; no risk score is assigned.", ""])
    for q in p["questions"]:
        l.extend([f'### {q["id"]} | {q["originalOwners"]}', "", q["question"], "",
                  f'- Source roles: {", ".join(q["sourceRoles"])}. {q["status"]}; {q["risk"]}; owner answer NOT_RECEIVED; executable authority {q["executableAuthority"]}.', ""])
    l.extend(["## 7. Fourteen future hostile cases, NOT EXECUTED", ""])
    for n in p["negativeScenarios"]:
        l.extend([f'### {n["id"]}', "", f'- Proposed trigger: {n["trigger"]}',
                  f'- Non-authorizing oracle: {n["nonAuthorizingOracle"]}.',
                  f'- Related new questions: {", ".join(n["questionIds"])}. {n["status"]}.', ""])
    l.extend(["## 8. Unchanged original dependencies and STOP", "",
              f'- S01: {p["priorM14S01QuestionsOpen"]} OPEN/UNRATED questions; {p["priorM14S01NegativeCasesNotExecuted"]} future scenarios NOT_EXECUTED.',
              f'- M13: {p["originalM13QuestionsOpen"]} original open questions; {p["originalM13NegativesNotExecuted"]} future cases NOT_EXECUTED.',
              f'- M09 B {p["ownerB"]}; C01 {p["m09C01"]}; H01–H04 {p["h01h02h03h04"]}.',
              f'- Cross-module native runtime {p["m10m11m12m13Runtime"]}; no M14 runtime.',
              f'- STOP: {p["stop"]}', ""])
    return "\n".join(l) + "\n"

def verify_packet(p: dict, root: Path = ROOT, *, verify_markdown: bool = True) -> dict:
    fields = {"schemaVersion","workOrder","issue","module","session","sourceBaseSha",
              "sourceBaseTreeSha","status","ownerApproval","capabilitySchemaAdopted",
              "technologySelected","modelRegistryRuntime","realCapabilityReceipts",
              "realEmpiricalMeasurements","sourceDocs","dimensions","taskFamilies",
              "evidenceStates","alternatives","questions","negativeScenarios",
              "priorM14S01QuestionsOpen","priorM14S01NegativeCasesNotExecuted",
              "originalM13QuestionsOpen","originalM13NegativesNotExecuted",
              "ownerB","m09C01","h01h02h03h04","m10m11m12m13Runtime","stop"}
    require(type(p) is dict and set(p) == fields, "missing or invented M14 S02 packet fields")
    exact = {"schemaVersion":"iris-m14-s02-source-research-v0.1","workOrder":"IRIS-WO-0077",
             "issue":206,"module":"M14","session":"S02","sourceBaseSha":BASE,
             "sourceBaseTreeSha":TREE,"status":"SOURCE_RESEARCH_ONLY_NONBINDING",
             "ownerApproval":"NONE","capabilitySchemaAdopted":False,"technologySelected":False,
             "modelRegistryRuntime":"NOT_ADMITTED","realCapabilityReceipts":0,
             "realEmpiricalMeasurements":0,"priorM14S01QuestionsOpen":16,
             "priorM14S01NegativeCasesNotExecuted":12,"originalM13QuestionsOpen":96,
             "originalM13NegativesNotExecuted":74,
             "ownerB":"B_FUTURE_OWNER_RECEIPT_DIRECTION_ONLY",
             "m09C01":"UNADOPTED_NOT_FROZEN",
             "h01h02h03h04":"ALL_OPEN_HIGH_FOR_FUTURE_FREEZE",
             "m10m11m12m13Runtime":"NOT_ADMITTED"}
    for key,val in exact.items():
        require(type(p[key]) is type(val) and p[key] == val,
                "unqualified model capability/owner/runtime claim or source drift: "+key)
    stop = p["stop"]
    require(type(stop) is str and len(stop) >= 350
            and all(x in stop for x in ("SOURCE_RESEARCH_ONLY","SPECIFIED_NOT_EXECUTED",
                     "OPEN_UNRATED_PENDING_QUALIFIED_OWNER","HIGH_FOR_FUTURE_FREEZE",
                     "NOT_ADMITTED")), "original owner/runtime STOP removed")
    src = p["sourceDocs"]
    require(type(src) is list and len(src) == len(SOURCES), "wrong source role count")
    for actual, (role,path,sha,needle) in zip(src, SOURCES):
        require(type(actual) is dict and actual == {
                    "role":role,"path":path,"gitBlobSha1":sha,"exactNeedle":needle},
                "source role or original SHA/anchor altered: "+role)
        raw=(root / path).read_bytes()
        require(git_blob(raw)==sha and needle in raw.decode("utf-8"),
                "original source Git SHA or exact text needle drift: "+role)
    index=(root / SOURCES[0][1]).read_text(encoding="utf-8")
    for s in ("S01 — S01 Model identity, versions, hashes, license and provenance",
              "S02 — S02 Capability Genome and task taxonomy",
              "S03 — S03 Empirical quality/latency/VRAM model cards",
              "S04 — S04 Hardware compatibility and reliability evidence",
              "S05 — S05 Model drift, deprecation and lifecycle governance"):
        require(s in index, "current M14 five-session source changed: "+s)
    dims=p["dimensions"]
    require(type(dims) is list and [x.get("id") for x in dims]==list(DIM_IDS),
            "six original source-only Genome dimensions missing or reordered")
    for x in dims:
        require(type(x) is dict and set(x)=={"id","title","caveat","pendingOwners","status"}
                and x["status"]=="NONBINDING_CONCEPT_ONLY"
                and len(x["caveat"])>=85 and x["pendingOwners"].startswith("M"),
                "unqualified Genome dimension adoption or caveat removed")
    tasks=p["taskFamilies"]
    require(type(tasks) is list and [x.get("id") for x in tasks]==list(TASK_IDS),
            "seven provisional task families missing/reordered")
    for x in tasks:
        require(type(x) is dict and set(x)=={"id","title","unresolvedBoundary","status"}
                and x["status"]=="CANDIDATE_TAXONOMY_NOT_RATIFIED"
                and len(x["unresolvedBoundary"])>=45,
                "task family falsely adopted or owner caveat lost")
    states=p["evidenceStates"]
    require(type(states) is list and [x.get("id") for x in states]==list(EVIDENCE_IDS),
            "five evidence state vocabularies absent")
    for x in states:
        require(type(x) is dict and set(x)=={"id","meaning","status"}
                and x["status"]=="VOCABULARY_ONLY_NO_ACTUAL_PROOF"
                and len(x["meaning"])>=50,
                "unqualified owner receipt or empirical evidence promotion")
    alternatives=p["alternatives"]
    require(type(alternatives) is list and [x.get("id") for x in alternatives]==list(ALT_IDS),
            "four alternative Genome designs absent")
    for x in alternatives:
        require(type(x) is dict and set(x)=={"id","title","tradeoffs","status","selected"}
                and x["selected"] is False and x["status"]=="RESEARCH_ONLY_NOT_SELECTED"
                and len(x["tradeoffs"])>=80,
                "an unqualified taxonomy technology was selected")
    qq=p["questions"]
    qids=[f"M14-S02-U{i:02d}" for i in range(1,19)]
    require(type(qq) is list and [x.get("id") for x in qq]==qids,
            "eighteen new owner questions missing/duplicated/reordered")
    roles={r[0] for r in SOURCES}
    for x in qq:
        require(type(x) is dict and set(x)=={"id","question","originalOwners",
                  "sourceRoles","status","risk","ownerAnswer","executableAuthority"}
                and x["status"]=="OPEN_UNRATED_PENDING_QUALIFIED_OWNER"
                and x["risk"]=="UNRATED" and x["ownerAnswer"] is None
                and x["executableAuthority"]=="NONE"
                and len(x["question"])>=80 and x["originalOwners"].startswith("M")
                and type(x["sourceRoles"]) is list and len(x["sourceRoles"])>=2
                and len(set(x["sourceRoles"]))==len(x["sourceRoles"])
                and all(role in roles for role in x["sourceRoles"]),
                "invented owner proof or source role drift")
    nn=p["negativeScenarios"]
    require(type(nn) is list
            and [x.get("id") for x in nn]==[f"M14-S02-N{i:02d}" for i in range(1,15)],
            "14 negative case designs missing/duplicated")
    for x in nn:
        require(type(x) is dict
                and set(x)=={"id","trigger","nonAuthorizingOracle","questionIds","status"}
                and x["status"]=="SPECIFIED_NOT_EXECUTED"
                and len(x["trigger"])>=80 and x["nonAuthorizingOracle"].startswith("NO_")
                and type(x["questionIds"]) is list and len(x["questionIds"])>=1
                and len(set(x["questionIds"]))==len(x["questionIds"])
                and all(q in qids for q in x["questionIds"]),
                "future negative falsely executed or foreign original question linked")
    if verify_markdown:
        require((root / REPORT).read_text(encoding="utf-8")==render_report(p),
                "human M14 S02 source report does not match exact machine projection")
    return {"sourceShaAndAnchorsVerified":len(src),"unadoptedGenomeDimensions":len(dims),
            "unratifiedTaskFamilies":len(tasks),"vocabularyOnlyEvidenceStates":len(states),
            "unselectedAlternatives":len(alternatives),"newOpenOwnerQuestions":len(qq),
            "futureNegativesUnexecuted":len(nn),"realOwnerReceipts":0}

def verify_all(root: Path=ROOT) -> dict:
    return verify_packet(read_json(root),root,verify_markdown=True)

if __name__=="__main__":
    print(json.dumps(verify_all(),sort_keys=True))
