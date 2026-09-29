"""WO0046: inert M13 S02 technology/source research integrity, never executable."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M13-S02-BACKEND-ATTENTION-RESEARCH.json"
REPORT = "planning/research/M13-S02-COMPILATION-ATTENTION-BACKENDS.md"
BASE = "ac26499c8753ddc7b96246b9d698d8bcfbe0561f"
BASE_TREE = "4847f9010aaca5ffac560228ee14fb52390cfa0b"
ORIGINAL = [{"role":"INDEX","path":"planning/MASTER-MODULE-INDEX.md","sha":"a60d19c86bddd3699498f7d1f248a00368e32220","anchor":"S02 — S02 Compilation, attention and backend selection"},{"role":"S01_REPORT","path":"planning/research/M13-S01-WARM-MODEL-CACHE-LOCALITY.md","sha":"6ef2485c557f5523871db34cd154b1da66699fde","anchor":"C04_COMPILED_BACKEND_ARTIFACT"},{"role":"S01_PACKET","path":".engineering/evidence/M13-S01-SOURCE-RESEARCH.json","sha":"5fe1b1ec36ce1e49a0810f553825c9d71b2af3e0","anchor":"UNADOPTED_CONCEPT_ONLY"},{"role":"M01","path":"docs/M01-QUALITY-KERNEL.md","sha":"df4f899ad414c47ad379f26fe1782edb6f43cf6f","anchor":"m01-contract-v1.0"},{"role":"M02","path":"planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"a36fd73c03f06b7558f850a2ad515a0df37c243b","anchor":"FROZEN_APPROVED"},{"role":"M06","path":"planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"d6778684e0c34e55d05ddc06cf5aa47fe347c037","anchor":"Digest equality proves byte equality"},{"role":"M07","path":"docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md","sha":"2a0b95dd3cc665e2206e454caef5858ef7fb61b0","anchor":"M07 does not lower quality targets"},{"role":"M08","path":"docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md","sha":"461e0f332d9be2af694634bbdc8cf67e29d56393","anchor":"M08 records empirical performance evidence"},{"role":"M09","path":"docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md","sha":"d12b4f48030c1a57b8e6228df39f35dac8c2b20a","anchor":"M09 is the provider-neutral resource-state"},{"role":"M10","path":"planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"f69ec3e3eab24b47c0e31832d64d9ab9cce21828","anchor":"Implementation authority: NOT ADMITTED"},{"role":"M11","path":"planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"4a5f384271504365701bdd685455d93984617f21","anchor":"NOT_FROZEN"},{"role":"M12","path":"planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"28b3802901349263100ceaaf80c0990513dbbded","anchor":"PROPOSED_NOT_FROZEN"},{"role":"D01","path":".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json","sha":"8877331a5004a3e816e4c42fb521ff3408bad08a","anchor":"B_FUTURE_OWNER_RECEIPT"}]
URLS = [["SDPA","https://docs.pytorch.org/docs/main/generated/torch.nn.functional.scaled_dot_product_attention.html"],["SDPA_POLICY","https://docs.pytorch.org/docs/stable/generated/torch.nn.attention.sdpa_kernel.html"],["TORCH_COMPILE","https://docs.pytorch.org/docs/stable/generated/torch.compile"],["TORCH_CACHE","https://docs.pytorch.org/tutorials/recipes/torch_compile_caching_tutorial.html"],["RECOMPILE","https://docs.pytorch.org/docs/main/user_guide/torch_compiler/compile/programming_model.recompilation.html"],["TENSORRT","https://docs.nvidia.com/deeplearning/tensorrt/latest/inference-library/engine-compatibility.html"],["FLASHATTN","https://github.com/Dao-AILab/flash-attention/blob/main/README.md?plain=1"],["COMFY_SECURITY","https://github.com/Comfy-Org/ComfyUI/blob/master/SECURITY.md"]]
CANDIDATE_IDS = ["REFERENCE_MATH","AUTO_SDPA","EXPLICIT_SDPA","PYTORCH_INDUCTOR","EXTERNAL_FLASH","NVIDIA_ENGINE","COMFY_NODE"]
DIMENSIONS = ["GRAPH_SEMANTICS","MODEL_ORIGIN","DEVICE_CONTEXT","TENSOR_ELIGIBILITY","PRECISION_QUALITY","SHAPE_AND_GUARDS","ACTUAL_DISPATCH","COMPILE_ARTIFACT","GRANT_LIVENESS","NATIVE_CODE_TRUST","TENANCY_RIGHTS","MEASURED_VALUE"]
QUESTION_ROUTES = [["M13/M04/M16","INDEX"],["M13/M07/M60","M07"],["M13/M08","M08"],["M13/M14/M18","INDEX"],["M13/M16","INDEX"],["M13/M17","INDEX"],["M13/M01/M08","M01"],["M13/M07/M08","M07"],["M13/M16","INDEX"],["M13/M08","M08"],["M13/M18/M54/M60","INDEX"],["M13/M09/M11/M12","M09"],["M13/M53/M54/M55","INDEX"],["M13/M14/M16","INDEX"],["M13/M07/M08/M10","M10"],["M13/M08/M56","M08"],["M13/M16/M17/M60","INDEX"],["M13/M01/M02/M53","M01"]]
NEGATIVE_IDS = ["CBA-01","CBA-02","CBA-03","CBA-04","CBA-05","CBA-06","CBA-07","CBA-08","CBA-09","CBA-10","CBA-11","CBA-12","CBA-13","CBA-14"]


class S02IntegrityError(ValueError):
    """An original source, authority or future-proof status was misrepresented."""


def must(value: bool, message: str) -> None:
    if not value:
        raise S02IntegrityError(message)


def sha1_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def no_duplicates(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for k, v in pairs:
        must(k not in result, "duplicate JSON key " + k)
        result[k] = v
    return result


def read_packet(root: Path = ROOT) -> dict:
    p = json.loads((root / PACKET).read_text(encoding="utf-8"),
                   object_pairs_hook=no_duplicates)
    must(type(p) is dict, "S02 evidence must be a JSON object")
    return p


def check_packet(p: dict, root: Path = ROOT, *,
                 verify_markdown: bool = False,
                 human_text: str | None = None) -> dict:
    must(type(p) is dict and set(p) == {
        "schema", "workOrder", "issue", "module", "session", "base", "baseTree",
        "asOf", "status", "ownerApprovals", "selectedBackend", "selectedKernel",
        "selectedCompiler", "hardwareMeasurements", "runtime", "b", "c01",
        "highs", "originalS01Questions", "originalS01Negatives",
        "originalM12Questions", "originalM12Negatives", "sourceDocs",
        "officialReferences", "candidates", "qualificationDimensions",
        "questions", "negativeCases", "stop",
    }, "missing or extraneous S02 packet field")
    must(
        p["schema"] == "iris-m13-s02-source-research-v0.1"
        and p["workOrder"] == "IRIS-WO-0046" and p["issue"] == 155
        and p["module"] == "M13" and p["session"] == "S02"
        and p["base"] == BASE and p["baseTree"] == BASE_TREE
        and p["asOf"] == "2026-09-27"
        and p["status"] == "SOURCE_ONLY_UNSELECTED_NONBINDING"
        and type(p["ownerApprovals"]) is int and p["ownerApprovals"] == 0
        and all(p[k] == "NONE" for k in (
            "selectedBackend", "selectedKernel", "selectedCompiler",
            "hardwareMeasurements"))
        and p["runtime"] == "NOT_ADMITTED"
        and p["b"] == "DIRECTION_ONLY"
        and p["c01"] == "UNADOPTED_NOT_FROZEN"
        and p["highs"] == "H01_H02_H03_H04_OPEN_HIGH_FOR_FUTURE_FREEZE"
        and p["originalS01Questions"] == "18_OPEN_UNRATED"
        and p["originalS01Negatives"] == "12_SPECIFIED_NOT_EXECUTED"
        and p["originalM12Questions"] == "110_OPEN_UNRATED"
        and p["originalM12Negatives"] == "80_SPECIFIED_NOT_EXECUTED"
        and type(p["stop"]) is str
        and all(k in p["stop"] for k in (
            "H01-H04", "DIRECTION_ONLY", "UNADOPTED_NOT_FROZEN",
            "SPECIFIED_NOT_EXECUTED", "runtime")),
        "H01-H04, B/C01 chronology, owner approval, original scenarios or runtime incorrectly advanced")

    sources = p["sourceDocs"]
    must(type(sources) is list and len(sources) == len(ORIGINAL)
         and sources == ORIGINAL,
         "original 13 source role/path/blob/anchor records modified")
    for row in sources:
        original = (root / row["path"]).read_bytes()
        must(sha1_blob(original) == row["sha"]
             and row["anchor"] in original.decode("utf-8"),
             "source-exact historical Git blob/needle drift: " + row["role"])
    master = (root / "planning/MASTER-MODULE-INDEX.md").read_text(encoding="utf-8")
    must(all(line in master for line in (
        "S01 — S01 Warm model/cache strategy and cache locality",
        "S02 — S02 Compilation, attention and backend selection",
        "S03 — S03 Intermediate reuse and generation delta cache",
    )), "original M13 session order drift")
    s01 = json.loads((root / ".engineering/evidence/M13-S01-SOURCE-RESEARCH.json").read_text(encoding="utf-8"))
    must(s01["status"] == "SOURCE_RESEARCH_ONLY_NONBINDING"
         and len(s01["questions"]) == 18
         and len(s01["negativeScenarios"]) == 12
         and all(x["status"] == "SPECIFIED_NOT_EXECUTED"
                 for x in s01["negativeScenarios"]),
         "S01 original research falsely promoted or lost")
    refs = p["officialReferences"]
    must(type(refs) is list and len(refs) == len(URLS)
         and [[x.get("id"), x.get("url")] for x in refs] == URLS,
         "original eight upstream URL/identity source routes changed")
    for row in refs:
        must(set(row) == {
            "id", "url", "publisher", "sourceClaim", "checkedOn", "status"
        } and row["checkedOn"] == "2026-09-27"
             and row["status"] == "PUBLIC_MUTABLE_REFERENCE_NOT_INSTALL_OR_PRODUCTION_EVIDENCE"
             and type(row["sourceClaim"]) is str
             and len(row["sourceClaim"]) >= 80,
             "official upstream URL incorrectly promoted to installed/immutable proof")
    cand = p["candidates"]
    must(type(cand) is list and
         [x.get("id") for x in cand] == CANDIDATE_IDS,
         "seven original candidate families omitted, duplicated or reordered")
    for row in cand:
        must(set(row) == {
            "id", "description", "officialRef", "requiredEvidence",
            "prohibition", "status", "selected", "installed", "benchmarked",
            "runtimeAuthority",
        } and row["officialRef"] in dict(URLS)
             and row["status"] == "UNSELECTED_NOT_QUALIFIED"
             and row["selected"] is False
             and row["installed"] is False
             and row["benchmarked"] is False
             and row["runtimeAuthority"] == "NONE"
             and type(row["requiredEvidence"]) is str
             and len(row["requiredEvidence"]) >= 80
             and type(row["prohibition"]) is str
             and len(row["prohibition"]) >= 90,
             "candidate falsely selected/installed/measured or unqualified")
    dimensions = p["qualificationDimensions"]
    must(type(dimensions) is list
         and [x.get("id") for x in dimensions] == DIMENSIONS,
         "future 12 owner qualification axes lost")
    for row in dimensions:
        must(set(row) == {"id", "ownerRoute", "neededEvidence", "status"}
             and row["status"] == "UNQUALIFIED_PENDING_REAL_OWNER_OR_BENCHMARK"
             and type(row["neededEvidence"]) is str
             and len(row["neededEvidence"]) >= 75,
             "future owner or benchmark axis falsely qualified")
    qs = p["questions"]
    must(type(qs) is list
         and [x.get("id") for x in qs] ==
             [f"M13-S02-U{i:02d}" for i in range(1, 19)],
         "18 new original M13 S02 questions lost/reordered")
    for row, (route, role) in zip(qs, QUESTION_ROUTES):
        must(set(row) == {
            "id", "ownerRoute", "question", "sourceRole", "status", "risk",
            "ownerAnswer", "runtimeAuthority",
        } and row["ownerRoute"] == route
             and row["sourceRole"] == role
             and row["sourceRole"] in {s["role"] for s in sources}
             and type(row["question"]) is str and len(row["question"]) >= 135
             and row["status"] == "OPEN_UNRATED_PENDING_QUALIFIED_OWNER"
             and row["risk"] == "UNRATED"
             and row["ownerAnswer"] is None
             and row["runtimeAuthority"] == "NONE",
             "new original owner question malformed, answered or falsely authorized")
    cases = p["negativeCases"]
    must(type(cases) is list
         and [x.get("id") for x in cases] == NEGATIVE_IDS,
         "14 future-case source IDs lost")
    for row in cases:
        must(set(row) == {"id", "candidateIds", "trigger", "oracle", "status"}
             and row["status"] == "SPECIFIED_NOT_EXECUTED"
             and type(row["candidateIds"]) is list and bool(row["candidateIds"])
             and len(row["candidateIds"]) == len(set(row["candidateIds"]))
             and set(row["candidateIds"]) <= set(CANDIDATE_IDS)
             and type(row["trigger"]) is str and len(row["trigger"]) >= 85
             and type(row["oracle"]) is str and len(row["oracle"]) >= 20,
             "future negative-case proof falsely executed or invalid candidate")
    if verify_markdown:
        body = human_text if human_text is not None else (
            root / REPORT).read_text(encoding="utf-8")
        fence = chr(96) * 3
        marker = "\n## Appendix A: canonical machine packet\n\n" + fence + "json\n"
        must(body.count(marker) == 1 and body.endswith("\n" + fence + "\n"),
             "human report lacks exactly one canonical appendix")
        prefix, payload = body.split(marker)
        original, rest = payload.split("\n" + fence + "\n", 1)
        must(rest == "", "unexpected content after canonical machine appendix")
        decoded = json.loads(original, object_pairs_hook=no_duplicates)
        must(decoded == p, "human projection does not match complete original machine packet")
        for row in (*qs, *cand, *dimensions, *cases):
            must(row["id"] in prefix, "human report omitted " + row["id"])
        for row in qs:
            must(row["question"] in prefix, "human report changed original question text")
        for row in cand:
            must(row["requiredEvidence"] in prefix
                 and row["prohibition"] in prefix,
                 "human report omitted candidate proof or prohibition")
        for row in refs:
            must(row["url"] in prefix and row["sourceClaim"] in prefix,
                 "human report omitted mutable official reference")
    return {
        "sourceOnly": True, "originalSourceGitBlobs": len(sources),
        "mutableOfficialReferences": len(refs),
        "unselectedBackendFamilies": len(cand),
        "unqualifiedOwnerAxes": len(dimensions),
        "newS02OpenQuestions": len(qs),
        "futureS02CasesNotExecuted": len(cases),
        "actualOwnerApprovals": 0,
        "h01h02h03h04": "OPEN_HIGH_FOR_FUTURE_FREEZE",
        "runtime": "NOT_ADMITTED",
    }


def verify_all(root: Path = ROOT) -> dict:
    return check_packet(read_packet(root), root, verify_markdown=True)


if __name__ == "__main__":
    try:
        print("M13 S02 SOURCE-ONLY PASS " +
              json.dumps(verify_all(), sort_keys=True) +
              " | zero approved owners, zero runtime")
    except (S02IntegrityError, OSError, TypeError, KeyError, ValueError,
            UnicodeError, json.JSONDecodeError) as error:
        raise SystemExit("M13 S02 FAIL CLOSED: " + str(error)) from error
