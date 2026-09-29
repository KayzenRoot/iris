"""WO0080: offline original-source/authority verifier for M14 S05 model lifecycle research."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M14-S05-SOURCE-RESEARCH.json"
REPORT = "planning/research/M14-S05-MODEL-LIFECYCLE-EVIDENCE.md"
BASE = "ca48f1f90b389f910c58c9cad6358961b6d3611b"
TREE = "43d0ce341ed1a2ce67cdb35e4a4be8f627e21df4"
SOURCE_ROWS = [["INDEX","planning/MASTER-MODULE-INDEX-CURRENT.md","02e6394cc7e75d5466ab22801b4cc7dbe66500be","S05 — S05 Model drift, deprecation and lifecycle governance"],["FCS","planning/reviews/M14-M60-FORWARD-COMPATIBILITY-SOURCE-SCAN.md","5bac62b5b1a07fb97e43ea5c76d20dc5419c2cec","S05 — S05 Model drift, deprecation and lifecycle governance"],["S01",".engineering/evidence/M14-S01-SOURCE-RESEARCH.json","10fe325b3928e58797266ae4ba0b65c87cd532fc","\"session\": \"S01\""],["S02",".engineering/evidence/M14-S02-SOURCE-RESEARCH.json","d3ac994e130bc54c566449dc0d6efc19a0ca2698","\"session\": \"S02\""],["S03",".engineering/evidence/M14-S03-SOURCE-RESEARCH.json","cf49ed6140976a14dbd0ac469bb79ed0091e624d","\"session\": \"S03\""],["S03_REPORT","planning/research/M14-S03-EMPIRICAL-CARD-EVIDENCE-DESIGN.md","9ba713ad3762696feb91b2e3e1aeefc06579dc38","Twenty NEW OPEN/UNRATED S03 owner questions"],["M01_NORM","planning/contracts/M01-MODULE-CONTRACT-FREEZE-CANDIDATE.md","48e00ca6ec3da8a5185fa49ccad37f14b6a5926a","FROZEN_APPROVED"],["M07","docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md","2a0b95dd3cc665e2206e454caef5858ef7fb61b0","M07 does not lower quality targets"],["M07_NORM","planning/modules/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md","9306e4937ccfb433ff4a0392846aa215ffd6e2a0","M07 does **not** benchmark performance"],["M08","docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md","461e0f332d9be2af694634bbdc8cf67e29d56393","M08 records empirical performance evidence"],["M08_NORM","planning/modules/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md","804387a28c318fc82f53e51651f279d76895095c","M08 is the empirical performance-characterization authority"],["M09","docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md","d12b4f48030c1a57b8e6228df39f35dac8c2b20a","M09 is the provider-neutral resource-state"],["M10","planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md","f69ec3e3eab24b47c0e31832d64d9ab9cce21828","Implementation authority: NOT ADMITTED"],["M13_S04","planning/research/M13-S04-CPU-GPU-OVERLAP-IO-STORAGE.md","cab009ad3e0a380b136f5af5cc902b09481be2a8","SOURCE-ONLY RESEARCH; NO RUNTIME"],["D01",".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json","8877331a5004a3e816e4c42fb521ff3408bad08a","B_FUTURE_OWNER_RECEIPT"],["S04",".engineering/evidence/M14-S04-SOURCE-RESEARCH.json","4d3de9e837c9a4988e1f31a6d6f06aae0261c277","\"session\": \"S04\""],["S04_REPORT","planning/research/M14-S04-HARDWARE-RELIABILITY-EVIDENCE.md","5dfa91c53c91f2f0edf214c8f50e053d31194d01","## 7. Historical pending owner and runtime STOP"],["M02_NORM","planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md","a36fd73c03f06b7558f850a2ad515a0df37c243b","FROZEN_APPROVED"],["M02_LIFECYCLE","planning/research/M02-S05-LIFECYCLE-PROMOTION-ARCHIVE-RESEARCH-2026-09-20.md","92cbd58dd7c65f31c1a89c30024dfc5cf004f3cf","make promotion explicit and evidence-gated"],["DECISIONS","docs/project-brain/16-DECISIONS-LEDGER.md","5d9c598c142c34227c25297d956e0d43b370bbcd","ADR-0047"]]
FACET_IDS = ["LF01_EXACT_COMPOSITE_DRIFT","LF02_TASK_IO_CONTRACT_DRIFT","LF03_EMPIRICAL_POPULATION_DRIFT","LF04_HOST_BACKEND_COMPATIBILITY_DRIFT","LF05_LICENSE_RIGHTS_RETRACTION","LF06_CACHE_COMPILE_AND_WARM_INVALIDATION","LF07_DEPRECATION_ROLLBACK_HISTORICAL_LINEAGE","LF08_CROSS_OWNER_APPROVAL_LEDGER"]
STATE_IDS = ["UNKNOWN_NO_OWNER_PROOF","CONFLICTED_MULTIPLE_ISSUERS","STALE_PROTOCOL_OR_COMPONENT","REVOKED_RIGHTS_OR_TRUST","DEPRECATED_HISTORICALLY_AVAILABLE"]
ALT_IDS = ["ALT01_MUTABLE_CURRENT_POINTER","ALT02_IMMUTABLE_VERSION_STATE_LEDGER","ALT03_SOURCE_QUALIFIED_DEPENDENCY_DAG","ALT04_SIGNED_AT_USE_LIFECYCLE_RECEIPT"]

class M14S05IntegrityError(ValueError):
    """Explicit typed failure on forged lifecycle evidence or original source drift."""

def require(condition: bool, reason: str) -> None:
    if not condition:
        raise M14S05IntegrityError(reason)

def dict_ids(items: object) -> list | None:
    if type(items) is not list or not all(type(x) is dict for x in items):
        return None
    return [x.get("id") for x in items]

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def unique_json_keys(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    for k, v in pairs:
        require(k not in out, "duplicate JSON key: " + k)
        out[k] = v
    return out

def read_json(root: Path = ROOT) -> dict:
    packet = json.loads((root / PACKET).read_text(encoding="utf-8"), object_pairs_hook=unique_json_keys)
    require(type(packet) is dict, "S05 packet must be an object")
    return packet

def render_report(p: dict) -> str:
    rows = ["# M14 S05 | Model Drift, Deprecation & Lifecycle Governance", "",
            "**SOURCE RESEARCH ONLY | IRIS-WO-0080 | issue #212 OPEN.**",
            "No observed model drift, signed lifecycle owner, genuine revocation, physical provider or admitted registry runtime.", "",
            "## 1. Exact original protected source evidence", "",
            "Protected original main {}; tree {}.".format(p["sourceBaseSha"], p["sourceBaseTreeSha"]), ""]
    for x in p["sourceDocs"]:
        rows.append("- {}: [{}](../../{}) Git blob {}; text anchor: {}.".format(
            x["role"], x["path"], x["path"], x["gitBlobSha1"], x["exactNeedle"]))
    rows.extend(["", "## 2. Eight nonadopted lifecycle research facets", "",
                 "All concepts require original qualified owner evidence and confer no runtime, licensing or model release grant.", ""])
    for x in p["facets"]:
        rows.extend(["### {}: {}".format(x["id"], x["title"]), "",
                     "{} {}.".format(x["caveat"], x["status"]), ""])
    rows.extend(["## 3. Five hypothetical lifecycle evidence states, VOCABULARY ONLY", "",
                 "An imagined lifecycle or revocation label is not an observed or signed model fact.", ""])
    for x in p["states"]:
        rows.append("- {}: {}.".format(x["id"], x["status"]))
    rows.extend(["", "## 4. Four unselected lifecycle approaches", ""])
    for x in p["alternatives"]:
        rows.append("- {}: {}; {}; {}; selected={}.".format(
            x["id"], x["title"], x["tradeoffs"], x["status"], str(x["selected"]).lower()))
    rows.extend(["", "## 5. Twenty-four NEW OPEN/UNRATED S05 owner questions", ""])
    for x in p["questions"]:
        rows.extend(["### {}".format(x["id"]), "", x["question"], "",
                     "- Exact source roles: {}; {}; risk {}; owner answer NONE; execution {}.".format(
                         ", ".join(x["sourceRoles"]), x["status"], x["risk"], x["executionAuthority"]), ""])
    rows.extend(["## 6. Twenty future hostile designs, NOT_EXECUTED", ""])
    for x in p["negativeScenarios"]:
        rows.extend(["### {}".format(x["id"]), "", x["trigger"], "",
                     "- {}; related {}; {}.".format(x["nonAuthorizingOracle"],
                         ", ".join(x["questionIds"]), x["status"]), ""])
    rows.extend(["## 7. Historical owner and runtime STOP", "",
                 "- Previous S01 16/12, S02 18/14, S03 20/16 and S04 22/18 owner questions/future cases remain OPEN/UNRATED / NOT_EXECUTED.",
                 "- Historical M13 96/74 remain unresolved/unexecuted.",
                 "- M09 B {}, C01 {}, H01-H04 {}, M10-M13 native {}.".format(
                     p["ownerB"],p["m09C01"],p["highs"],p["m10m11m12m13Runtime"]),
                 "- STOP: {}".format(p["stop"]), ""])
    return "\n".join(rows) + "\n"

def verify_packet(p: dict, root: Path = ROOT, *, verify_markdown: bool = True) -> dict:
    fields = {"schemaVersion","workOrder","issue","module","session","sourceBaseSha",
              "sourceBaseTreeSha","status","ownerApproval","lifecycleContractAdopted",
              "registryRuntimeAdmitted","observedModelDriftEvents","realLifecycleTransitions",
              "realRevocationActions","realProviderTests","realGpuBenchmarks","sourceDocs",
              "facets","states","alternatives","questions","negativeScenarios",
              "priorS01QuestionsOpen","priorS01FutureCases","priorS02QuestionsOpen",
              "priorS02FutureCases","priorS03QuestionsOpen","priorS03FutureCases",
              "priorS04QuestionsOpen","priorS04FutureCases","priorM13QuestionsOpen",
              "priorM13FutureCases","ownerB","m09C01","highs","m10m11m12m13Runtime","stop"}
    require(type(p) is dict and set(p) == fields, "missing or invented S05 evidence fields")
    exact = {"schemaVersion":"iris-m14-s05-source-research-v0.1","workOrder":"IRIS-WO-0080",
             "issue":212,"module":"M14","session":"S05","sourceBaseSha":BASE,
             "sourceBaseTreeSha":TREE,"status":"SOURCE_RESEARCH_ONLY_NO_LIFECYCLE_QUALIFICATION",
             "ownerApproval":"NONE","lifecycleContractAdopted":False,"registryRuntimeAdmitted":False,
             "observedModelDriftEvents":0,"realLifecycleTransitions":0,"realRevocationActions":0,
             "realProviderTests":0,"realGpuBenchmarks":0,
             "priorS01QuestionsOpen":16,"priorS01FutureCases":12,
             "priorS02QuestionsOpen":18,"priorS02FutureCases":14,
             "priorS03QuestionsOpen":20,"priorS03FutureCases":16,
             "priorS04QuestionsOpen":22,"priorS04FutureCases":18,
             "priorM13QuestionsOpen":96,"priorM13FutureCases":74,
             "ownerB":"B_FUTURE_OWNER_RECEIPT_DIRECTION_ONLY",
             "m09C01":"UNADOPTED_NOT_FROZEN","highs":"ALL_OPEN_HIGH_FOR_FUTURE_FREEZE",
             "m10m11m12m13Runtime":"NOT_ADMITTED"}
    for k, v in exact.items():
        require(type(p[k]) is type(v) and p[k] == v, "forged owner, lifecycle or runtime fact: "+k)
    stop = p["stop"]
    require(type(stop) is str and len(stop) >= 540
            and all(s in stop for s in ("SOURCE_RESEARCH_ONLY","OPEN_UNRATED_PENDING_QUALIFIED_OWNER",
                "SPECIFIED_NOT_EXECUTED","ZERO","UNADOPTED_NOT_FROZEN","HIGH_FOR_FUTURE_FREEZE",
                "NOT_ADMITTED","M01","M02")), "owner/runtime/lifecycle STOP omitted")
    sources = p["sourceDocs"]
    require(type(sources) is list and len(sources) == len(SOURCE_ROWS), "original source roles changed")
    for x, (role, path, sha, needle) in zip(sources, SOURCE_ROWS):
        require(type(x) is dict and x == {"role":role,"path":path,"gitBlobSha1":sha,
                                          "exactNeedle":needle},
                "original source role, SHA or needle changed: "+role)
        try:
            raw = (root / path).read_bytes()
            txt = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise M14S05IntegrityError("original source unreadable: "+role) from exc
        require(git_blob(raw) == sha and needle in txt, "original Git source drift: "+role)
    index = (root / SOURCE_ROWS[0][1]).read_text(encoding="utf-8")
    for needle in ("S01 — S01 Model identity, versions, hashes, license and provenance",
                   "S02 — S02 Capability Genome and task taxonomy",
                   "S03 — S03 Empirical quality/latency/VRAM model cards",
                   "S04 — S04 Hardware compatibility and reliability evidence",
                   "S05 — S05 Model drift, deprecation and lifecycle governance"):
        require(needle in index, "original M14 five-session index changed")
    facets = p["facets"]
    require(dict_ids(facets) == FACET_IDS, "eight S05 facets missing/reordered")
    for x in facets:
        require(type(x) is dict and set(x) == {"id","title","caveat","status"}
                and x["status"] == "SOURCE_TAXONOMY_NOT_ADOPTED"
                and type(x["title"]) is str and len(x["title"]) >= 16
                and type(x["caveat"]) is str and len(x["caveat"]) >= 100,
                "unqualified facet or type mismatch")
    states = p["states"]
    require(dict_ids(states) == STATE_IDS, "five future lifecycle labels missing/reordered")
    for x in states:
        require(type(x) is dict and set(x) == {"id","status"}
                and x["status"] == "VOCABULARY_ONLY_NO_OBSERVED_LIFECYCLE",
                "future hypothetical lifecycle state promoted")
    alts = p["alternatives"]
    require(dict_ids(alts) == ALT_IDS, "four lifecycle alternatives changed")
    for x in alts:
        require(type(x) is dict and set(x) == {"id","title","tradeoffs","selected","status"}
                and x["selected"] is False and x["status"] == "RESEARCH_ONLY_NOT_SELECTED"
                and type(x["title"]) is str and len(x["title"]) >= 16
                and type(x["tradeoffs"]) is str and len(x["tradeoffs"]) >= 100,
                "unqualified lifecycle alternative selected")
    qq = p["questions"]
    qids = ["M14-S05-U{:02d}".format(i) for i in range(1,25)]
    require(dict_ids(qq) == qids, "24 S05 questions missing/reordered")
    roles = {row[0] for row in SOURCE_ROWS}
    for x in qq:
        require(type(x) is dict and set(x) == {"id","question","sourceRoles","status",
                                               "risk","ownerAnswer","executionAuthority"}
                and x["status"] == "OPEN_UNRATED_PENDING_QUALIFIED_OWNER"
                and x["risk"] == "UNRATED" and x["ownerAnswer"] is None
                and x["executionAuthority"] == "NONE"
                and type(x["question"]) is str and len(x["question"]) >= 85
                and type(x["sourceRoles"]) is list and len(x["sourceRoles"]) >= 2
                and all(type(v) is str for v in x["sourceRoles"])
                and len(set(x["sourceRoles"])) == len(x["sourceRoles"])
                and all(v in roles for v in x["sourceRoles"]),
                "owner question answered, malformed or unqualified")
    neg = p["negativeScenarios"]
    require(dict_ids(neg) == ["M14-S05-N{:02d}".format(i) for i in range(1,21)],
            "20 negative designs missing/reordered")
    for x in neg:
        require(type(x) is dict and set(x) == {"id","trigger","questionIds","nonAuthorizingOracle","status"}
                and x["status"] == "SPECIFIED_NOT_EXECUTED"
                and x["nonAuthorizingOracle"] == "NO_CURRENT_LIFECYCLE_OR_RUNTIME_PERMISSION"
                and type(x["trigger"]) is str and len(x["trigger"]) >= 120
                and type(x["questionIds"]) is list and len(x["questionIds"]) >= 1
                and all(type(v) is str for v in x["questionIds"])
                and len(set(x["questionIds"])) == len(x["questionIds"])
                and all(v in qids for v in x["questionIds"]),
                "future test falsely executed or nonlocal owner referenced")
    if verify_markdown:
        require((root / REPORT).read_text(encoding="utf-8") == render_report(p),
                "human S05 report differs from exact machine projection")
    return {"originalSourcePinsVerified":len(sources),"nonadoptedFacets":len(facets),
            "futureEvidenceLabelsOnly":len(states),"unselectedAlternatives":len(alts),
            "newOpenOwnerQuestions":len(qq),"futureNegativesNotExecuted":len(neg),
            "realLifecycleObservations":0}

def verify_all(root: Path = ROOT) -> dict:
    return verify_packet(read_json(root), root, verify_markdown=True)

if __name__ == "__main__":
    print(json.dumps(verify_all(), sort_keys=True))
