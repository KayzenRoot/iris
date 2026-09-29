"""WO0049: inert M13 S05 source, profiling and false-approval verifier."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M13-S05-PERFORMANCE-GATES-RESEARCH.json"
REPORT = "planning/research/M13-S05-PERFORMANCE-BUDGETS-AND-REGRESSION.md"
SOURCES = [{"role":"INDEX","path":"planning/MASTER-MODULE-INDEX.md","sha":"a60d19c86bddd3699498f7d1f248a00368e32220","anchor":"S05 — S05 Performance budgets, profiling and anti-regression gates"},{"role":"M01","path":"docs/M01-QUALITY-KERNEL.md","sha":"df4f899ad414c47ad379f26fe1782edb6f43cf6f","anchor":"m01-contract-v1.0"},{"role":"M02","path":"planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"a36fd73c03f06b7558f850a2ad515a0df37c243b","anchor":"semantic reuse requires explicit reuse class/admission"},{"role":"M06","path":"planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"d6778684e0c34e55d05ddc06cf5aa47fe347c037","anchor":"Digest equality proves byte equality under the declared digest domain only."},{"role":"M07","path":"docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md","sha":"2a0b95dd3cc665e2206e454caef5858ef7fb61b0","anchor":"M07 does not lower quality targets"},{"role":"M08","path":"docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md","sha":"461e0f332d9be2af694634bbdc8cf67e29d56393","anchor":"UNKNOWN_TELEMETRY"},{"role":"M09","path":"docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md","sha":"d12b4f48030c1a57b8e6228df39f35dac8c2b20a","anchor":"m09-contract-v1.0"},{"role":"M10","path":"planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"f69ec3e3eab24b47c0e31832d64d9ab9cce21828","anchor":"Implementation authority: NOT ADMITTED"},{"role":"M11","path":"planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"4a5f384271504365701bdd685455d93984617f21","anchor":"PROPOSED_C02_CORRECTION_NOT_FROZEN"},{"role":"M12","path":"planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"28b3802901349263100ceaaf80c0990513dbbded","anchor":"Implementation authority: NOT_ADMITTED"},{"role":"S01","path":".engineering/evidence/M13-S01-SOURCE-RESEARCH.json","sha":"5fe1b1ec36ce1e49a0810f553825c9d71b2af3e0","anchor":"SOURCE_RESEARCH_ONLY_NONBINDING"},{"role":"S02","path":".engineering/evidence/M13-S02-BACKEND-ATTENTION-RESEARCH.json","sha":"8ac11eaa91292a81d10de1d44ccd21b5e240a664","anchor":"SOURCE_ONLY_UNSELECTED_NONBINDING"},{"role":"S03","path":".engineering/evidence/M13-S03-DELTA-REUSE-RESEARCH.json","sha":"fe0ea0d3a4b4229f79e19d023c255cc6a0cafdf1","anchor":"SOURCE_ONLY_NONBINDING"},{"role":"S04","path":".engineering/evidence/M13-S04-OVERLAP-IO-RESEARCH.json","sha":"b9b87ac36189c1cabd75989a07920752c23704fd","anchor":"SOURCE_ONLY_NO_HARDWARE_OR_IO_RUNTIME"},{"role":"D01","path":".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json","sha":"8877331a5004a3e816e4c42fb521ff3408bad08a","anchor":"B_FUTURE_OWNER_RECEIPT"}]
URLS = [["TORCH_PROFILER","https://docs.pytorch.org/docs/stable/profiler"],["NVIDIA_NSIGHT","https://docs.nvidia.com/nsight-systems/UserGuide/"],["CUDA_TIMING","https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/"]]
CLASS_IDS = ["BUDGET-01","BUDGET-02","BUDGET-03","BUDGET-04","BUDGET-05","BUDGET-06"]
PROFILE_IDS = ["PROFILE-01","PROFILE-02","PROFILE-03","PROFILE-04","PROFILE-05"]
AXIS_IDS = ["QUALITY_MASTER","WORK_ATTEMPT_LINEAGE","HARDWARE_FINGERPRINT","BENCHMARK_PROTOCOL","INTERFERENCE_COMPLETENESS","TRACE_OBSERVER_EFFECT","RESOURCE_TRUTH","MODEL_AND_COMPILER","STORAGE_LIFECYCLE","CURRENT_TENANT_RIGHTS","HUMAN_POLICY_APPROVAL","OBSERVABILITY_REVIEW"]
QUESTION_ROUTES = [["M01/M02","M01"],["M07/M08","M08"],["M08","M08"],["M08/M56","M08"],["M07/M08/M60","M07"],["M08/M13","S01"],["M08/M13/M14/M16","S02"],["M02/M06/M08","S03"],["M07/M08/M09","M09"],["M09/M11/M12","M09"],["M53/M54/M55","INDEX"],["M08/M56","M08"],["M08/M57","INDEX"],["M08/M10","M10"],["M01/M08/M13","M01"],["M08/M56/M60","M08"],["M55/M60","INDEX"],["M02/M06/M53/M54","M02"],["M08/M56","M08"],["M13/M14/M16/M17/M60","INDEX"]]
NEGATIVE_ORACLES = [["QUALITY_BEFORE_SPEED","NO_PERFORMANCE_PASS_WITH_QUALITY_FAILURE"],["UNKNOWN_IS_NOT_VALID","NO_UNKNOWN_TELEMETRY_TO_VALID"],["PROFILER_PERTURBATION","NO_UNCALIBRATED_PROFILER_SPEEDUP"],["CUDA_ENQUEUE_ONLY","NO_ENQUEUE_AS_GPU_COMPLETION"],["STALE_DEVICE","NO_STALE_HARDWARE_PERFORMANCE_CERT"],["UNMATCHED_WORKLOAD","NO_UNPAIRED_REGRESSION_RESULT"],["INSUFFICIENT_UNCERTAINTY","NO_INFERENCE_WITH_UNKNOWN_CONFIDENCE"],["COLD_WARM_CONFUSION","NO_COLD_LATENCY_FROM_WARM_ONLY"],["TENANT_PROFILE_LEAK","NO_UNAUTHORIZED_PROFILE_EXPORT"],["NUMERIC_POLICY_INVENTION","NO_DEFAULT_SLO_FROM_DRAFT"],["RESOURCE_HINT_AS_LEASE","NO_RESOURCE_GRANT_FROM_METRIC"],["THERMAL_CAUSAL_ERROR","NO_UNGROUNDED_CAUSAL_PROFILE"],["MISSING_OWNER_TRACE","NO_MOCK_CHECKLIST_AS_OWNER_PROOF"],["STORAGE_STALE_RIGHTS","NO_PROFILE_RETENTION_FROM_HISTORY"],["PARTIAL_REBUILD_LINEAGE","NO_PERF_RESULT_AS_PRODUCTION_ADMISSION"],["HYPOTHESIS_MARKED_MEASURED","NO_PUBLIC_DOC_AS_LOCAL_BENCHMARK"]]
FIELDS = ["schema","workOrder","issue","module","session","baseSha","baseTreeSha","asOf","status","actualOwnerApprovals","selectedPolicy","numericBudgets","measurements","installedProfilers","runtime","b","c01","highs","previousSessions","originalM12Questions","originalM12FutureNegatives","sourceDocs","externalReferences","budgetClasses","profilingMethods","futureQualificationAxes","questions","negativeCases","nextStep","stop"]
GOOD = {
    "source": "BOUND", "quality": "PASS", "protocol": "COMPARABLE",
    "interference": "QUALIFIED", "observerOverhead": "CHARACTERIZED",
    "rights": "CURRENT", "resource": "CLAIMED", "budgetPolicy": "OWNER_DEFINED",
}
OPTIONS = {
    "source": ("BOUND", "UNKNOWN"), "quality": ("PASS", "FAIL", "UNKNOWN"),
    "protocol": ("COMPARABLE", "CHANGED", "UNKNOWN"),
    "interference": ("QUALIFIED", "CONTAMINATED", "UNKNOWN"),
    "observerOverhead": ("CHARACTERIZED", "UNKNOWN"),
    "rights": ("CURRENT", "REVOKED", "UNKNOWN"),
    "resource": ("CLAIMED", "UNKNOWN"),
    "budgetPolicy": ("OWNER_DEFINED", "UNDEFINED"),
}


class S05IntegrityError(ValueError):
    pass


def must(ok: bool, message: str) -> None:
    if not ok:
        raise S05IntegrityError(message)


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def unique(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    for k, v in pairs:
        must(k not in out, "duplicate source JSON key " + k)
        out[k] = v
    return out


def read_packet(root: Path = ROOT) -> dict:
    p = json.loads((root / PACKET).read_text(encoding="utf-8"),
                   object_pairs_hook=unique)
    must(type(p) is dict, "source packet is not JSON object")
    return p


def synthetic_screen(claims: dict) -> dict:
    """No real owner authentication, no hardware probe and no budget admission."""
    must(type(claims) is dict and set(claims) == set(GOOD)
         and all(type(claims[k]) is str and claims[k] in OPTIONS[k]
                 for k in GOOD),
         "eight literal untrusted synthetic evidence categories required")
    return {
        "mockBlockers": [k for k in GOOD if claims[k] != GOOD[k]],
        "disposition": "TRIAGE_ONLY_NO_REAL_BUDGET_OR_RUNTIME_ADMISSION",
        "actualOwnerReceipts": 0, "actualMeasurements": 0,
        "numericBudgetAdmitted": False, "runtimeAllowed": False,
    }


def validate(p: dict, root: Path = ROOT, *,
             human: bool = False, human_text: str | None = None) -> dict:
    must(type(p) is dict and set(p) == set(FIELDS),
         "packet original schema gained or lost fields")
    expected = {
        "schema": "iris-m13-s05-performance-budgets-v0.1",
        "workOrder": "IRIS-WO-0049", "issue": 155,
        "module": "M13", "session": "S05",
        "baseSha": "e4c8821fdc504fe398ec72b287dc13ed0e24f442",
        "baseTreeSha": "958140fc1207f480cc0da67037184eceb6865a8c",
        "asOf": "2026-09-27",
        "status": "SOURCE_ONLY_FIFTH_SESSION_NOT_MODULE_FREEZE",
        "actualOwnerApprovals": 0, "selectedPolicy": "NONE",
        "numericBudgets": "NONE_ASSIGNED", "measurements": "NONE_PERFORMED",
        "installedProfilers": "NONE", "runtime": "NOT_ADMITTED",
        "b": "DIRECTION_ONLY", "c01": "UNADOPTED_NOT_FROZEN",
        "highs": "H01_H02_H03_H04_OPEN_HIGH_FOR_FUTURE_FREEZE",
        "previousSessions": {
            "s01Questions": "18_OPEN", "s01FutureNegatives": "12_NOT_EXECUTED",
            "s02Questions": "18_OPEN", "s02FutureNegatives": "14_NOT_EXECUTED",
            "s03Questions": "20_OPEN", "s03FutureNegatives": "16_NOT_EXECUTED",
            "s04Questions": "20_OPEN", "s04FutureNegatives": "16_NOT_EXECUTED",
        },
        "originalM12Questions": "110_OPEN_UNRATED",
        "originalM12FutureNegatives": "80_SPECIFIED_NOT_EXECUTED",
        "nextStep": (
            "AFTER_GREEN_WO0049_PREPARE_SEPARATE_M13_FINAL_TECH_REVIEW_"
            "AND_M14_M60_FORWARD_COMPAT_SCAN_SOURCE_ONLY_NOT_FROZEN"),
    }
    must(all(type(p[k]) is type(v) and p[k] == v for k, v in expected.items()),
         "historic session/owner/H-gate/budget/runtime status changed")
    must(type(p["stop"]) is str and all(term in p["stop"] for term in (
        "H01-H04", "DIRECTION_ONLY", "UNADOPTED_NOT_FROZEN",
        "SPECIFIED_NOT_EXECUTED", "runtime")),
        "STOP does not preserve original no-runtime and no-owner boundary")
    must(type(p["sourceDocs"]) is list and p["sourceDocs"] == SOURCES,
         "15 original source-role/Git-blob/anchor records changed")
    for s in SOURCES:
        raw = (root / s["path"]).read_bytes()
        must(blob_sha(raw) == s["sha"] and s["anchor"] in raw.decode("utf-8"),
             "original immutable Git blob or anchor mismatch " + s["role"])
    index = (root / "planning/MASTER-MODULE-INDEX.md").read_text(encoding="utf-8")
    must(all(s in index for s in (
        "S01 — S01 Warm model/cache strategy and cache locality",
        "S02 — S02 Compilation, attention and backend selection",
        "S03 — S03 Intermediate reuse and generation delta cache",
        "S04 — S04 CPU/GPU overlap, I/O scheduling and storage efficiency",
        "S05 — S05 Performance budgets, profiling and anti-regression gates")),
        "M13 original five-session master-index changed")
    for path, key, q, n in (
        (".engineering/evidence/M13-S01-SOURCE-RESEARCH.json",
         "negativeScenarios", 18, 12),
        (".engineering/evidence/M13-S02-BACKEND-ATTENTION-RESEARCH.json",
         "negativeCases", 18, 14),
        (".engineering/evidence/M13-S03-DELTA-REUSE-RESEARCH.json",
         "futureNegativeCases", 20, 16),
        (".engineering/evidence/M13-S04-OVERLAP-IO-RESEARCH.json",
         "negativeCases", 20, 16),
    ):
        prior = json.loads((root / path).read_text(encoding="utf-8"),
                           object_pairs_hook=unique)
        must(len(prior["questions"]) == q and len(prior[key]) == n
             and all(x["status"] == "SPECIFIED_NOT_EXECUTED"
                     for x in prior[key]),
             "original previous research future integrations falsely executed")
    refs = p["externalReferences"]
    must(type(refs) is list
         and [[x.get("id"), x.get("url")] for x in refs] == URLS,
         "three mutable original public profiling URLs drifted")
    for x in refs:
        must(set(x) == {"id", "url", "publisher", "claim", "checkedOn", "status"}
             and x["checkedOn"] == "2026-09-27"
             and x["status"] ==
             "MUTABLE_EXTERNAL_SOURCE_NOT_LOCAL_PROFILING_OR_PRODUCTION_PROOF"
             and len(x["claim"]) >= 110,
             "public profiling reference falsely installed or measured")
    budgets = p["budgetClasses"]
    must(type(budgets) is list and
         [x.get("id") for x in budgets] == CLASS_IDS,
         "six original source budget IDs changed")
    for x in budgets:
        must(set(x) == {"id", "name", "ownerRoute", "scope",
                        "necessaryFutureEvidence", "threshold", "status"}
             and x["threshold"] == "OWNER_DEFINED_NOT_ASSIGNED"
             and x["status"] == "UNRATED_NO_NUMERIC_THRESHOLD"
             and len(x["necessaryFutureEvidence"]) >= 100,
             "numeric owner budget invented")
    profiles = p["profilingMethods"]
    must(type(profiles) is list
         and [x.get("id") for x in profiles] == PROFILE_IDS,
         "five profiling methods changed")
    for x in profiles:
        must(set(x) == {"id", "name", "conditionalMethod",
                        "failureLimit", "status"}
             and x["status"] == "PROTOCOL_NOT_EXECUTED"
             and len(x["conditionalMethod"]) >= 95
             and len(x["failureLimit"]) >= 105,
             "actual profiler measurement falsely claimed")
    axes = p["futureQualificationAxes"]
    must(type(axes) is list and [x.get("id") for x in axes] == AXIS_IDS,
         "twelve future owner/protocol axes changed")
    for x in axes:
        must(set(x) == {"id", "ownerRoute", "requiredActualEvidence", "status"}
             and x["status"] == "OWNER_PROOF_OR_ACTUAL_MEASUREMENT_NOT_RECEIVED"
             and len(x["requiredActualEvidence"]) >= 100,
             "future owner proof falsely received")
    questions = p["questions"]
    must(type(questions) is list
         and [x.get("id") for x in questions] ==
         [f"M13-S05-U{i:02d}" for i in range(1, 21)],
         "twenty new S05 owner question IDs missing")
    for x, (owner, role) in zip(questions, QUESTION_ROUTES):
        must(set(x) == {"id", "ownerRoute", "question", "primarySourceRole",
                        "status", "risk", "ownerAnswer"}
             and x["ownerRoute"] == owner
             and x["primarySourceRole"] == role
             and len(x["question"]) >= 105
             and x["status"] == "OPEN_UNRATED_PENDING_QUALIFIED_OWNER"
             and x["risk"] == "UNRATED"
             and x["ownerAnswer"] is None,
             "S05 owner role/question falsely decided")
    negatives = p["negativeCases"]
    must(type(negatives) is list
         and [x.get("id") for x in negatives] ==
         [f"M13-S05-N{i:02d}" for i in range(1, 17)]
         and [[x.get("label"), x.get("futureNonAuthorizingOracle")]
              for x in negatives] == NEGATIVE_ORACLES,
         "sixteen original future negative labels/oracles changed")
    for x in negatives:
        must(set(x) == {"id", "label", "trigger",
                        "futureNonAuthorizingOracle", "status"}
             and x["status"] == "SPECIFIED_NOT_EXECUTED"
             and len(x["trigger"]) >= 80,
             "S05 real negative integration falsely claimed executed")
    if human:
        text = human_text if human_text is not None else (
            root / REPORT).read_text(encoding="utf-8")
        fence = chr(96) * 3
        marker = "\n## Appendix A: canonical original machine packet\n\n" + fence + "json\n"
        must(text.count(marker) == 1 and text.endswith("\n" + fence + "\n"),
             "human report lacks single canonical full machine appendix")
        visible, appendix = text.split(marker)
        raw, tail = appendix.split("\n" + fence + "\n", 1)
        must(tail == ""
             and json.loads(raw, object_pairs_hook=unique) == p,
             "human report machine packet diverged")
        for x in (*budgets, *profiles, *axes, *questions, *negatives):
            must(x["id"] in visible, "human report omitted original item")
        for x in questions:
            must(x["question"] in visible, "visible owner question mutated")
        for x in SOURCES:
            must(x["path"] in visible and x["sha"] in visible,
                 "human original source SHA omitted")
        for x in refs:
            must(x["url"] in visible and x["claim"] in visible,
                 "human mutable official source caveat omitted")
    return {
        "sourceOnly": True, "immutableOriginalSourceDocs": len(SOURCES),
        "mutableOfficialProfilingRefs": len(refs),
        "nonnumericBudgetFamilies": len(budgets),
        "unexecutedProfilingMethods": len(profiles),
        "unqualifiedOwnerAxes": len(axes),
        "newOpenOwnerQuestions": len(questions),
        "newUnexecutedNegativeCases": len(negatives),
        "actualOwners": 0, "measuredRuns": 0, "runtime": "NOT_ADMITTED",
    }


def verify_all(root: Path = ROOT) -> dict:
    return validate(read_packet(root), root, human=True)


if __name__ == "__main__":
    try:
        print("M13 S05 SOURCE-ONLY PASS " +
              json.dumps(verify_all(), sort_keys=True) +
              " | no owners, numeric thresholds, profiler or runtime")
    except (S05IntegrityError, OSError, ValueError, TypeError,
            UnicodeError, KeyError, json.JSONDecodeError) as error:
        raise SystemExit("M13 S05 FAIL CLOSED: " + str(error)) from error
