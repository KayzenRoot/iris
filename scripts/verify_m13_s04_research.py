"""WO0048: read-only S04 CPU/GPU/I/O research integrity, no device/storage imports."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M13-S04-OVERLAP-IO-RESEARCH.json"
REPORT = "planning/research/M13-S04-CPU-GPU-OVERLAP-IO-STORAGE.md"
BASE = "c73b524e90a433d3476521d7a4b47f9451e3d32c"
BASE_TREE = "489187561ab7c581c932a4721edfcadf9ac7dd9e"
ORIGINAL_SOURCES = [{"role":"INDEX","path":"planning/MASTER-MODULE-INDEX.md","sha":"a60d19c86bddd3699498f7d1f248a00368e32220","anchor":"S04 — S04 CPU/GPU overlap, I/O scheduling and storage efficiency"},{"role":"M07","path":"docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md","sha":"2a0b95dd3cc665e2206e454caef5858ef7fb61b0","anchor":"M07 does not lower quality targets"},{"role":"M08","path":"docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md","sha":"461e0f332d9be2af694634bbdc8cf67e29d56393","anchor":"UNKNOWN_TELEMETRY"},{"role":"M09","path":"docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md","sha":"d12b4f48030c1a57b8e6228df39f35dac8c2b20a","anchor":"M09 is the provider-neutral resource-state"},{"role":"M10","path":"planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"f69ec3e3eab24b47c0e31832d64d9ab9cce21828","anchor":"m10-contract-v1.0"},{"role":"M11","path":"planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"4a5f384271504365701bdd685455d93984617f21","anchor":"PROPOSED_C02_CORRECTION_NOT_FROZEN"},{"role":"M12","path":"planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"28b3802901349263100ceaaf80c0990513dbbded","anchor":"Implementation authority: NOT_ADMITTED"},{"role":"S01","path":"planning/research/M13-S01-WARM-MODEL-CACHE-LOCALITY.md","sha":"6ef2485c557f5523871db34cd154b1da66699fde","anchor":"C03_DEVICE_RESIDENCY_HINT"},{"role":"S02","path":"planning/research/M13-S02-COMPILATION-ATTENTION-BACKENDS.md","sha":"c033ac4696ad4a188ca5605470bf9b29396eb3ad","anchor":"AUTO_SDPA"},{"role":"S03","path":"planning/research/M13-S03-INTERMEDIATE-REUSE-GENERATION-DELTA.md","sha":"fd600eeca5cabd3e367fcbb27f12556830c93bf0","anchor":"Seven unadopted reuse concepts"},{"role":"M01","path":"docs/M01-QUALITY-KERNEL.md","sha":"df4f899ad414c47ad379f26fe1782edb6f43cf6f","anchor":"m01-contract-v1.0"},{"role":"M02","path":"planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"a36fd73c03f06b7558f850a2ad515a0df37c243b","anchor":"semantic reuse requires explicit reuse class/admission"},{"role":"M06","path":"planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"d6778684e0c34e55d05ddc06cf5aa47fe347c037","anchor":"Digest equality proves byte equality under the declared digest domain only."},{"role":"D01","path":".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json","sha":"8877331a5004a3e816e4c42fb521ff3408bad08a","anchor":"B_FUTURE_OWNER_RECEIPT"}]
OFFICIAL = [["NVIDIA_CUDA_BPG","https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/"]]
CLASS_IDS = ["CLASS-01","CLASS-02","CLASS-03","CLASS-04","CLASS-05","CLASS-06","CLASS-07"]
ALTERNATIVE_IDS = ["ALT-01","ALT-02","ALT-03","ALT-04"]
METRICS = ["PIPELINE_END_TO_END_P50_P95","COPY_COMPUTE_OVERLAP_TRACE","HOST_RAM_PRESSURE","GPU_VRAM_PRESSURE","DISK_READ_WRITE_LATENCY","CPU_DECODE_TAIL","QUEUE_BACKPRESSURE","THERMAL_POWER_CAUSALITY","FOREGROUND_INTERFERENCE","MEDIA_FIDELITY_CONSISTENCY","WARM_COLD_AND_INVALIDATION","PROVENANCE_SCOPE"]
QUESTION_ROUTES = [["M07/M08","M07"],["M07/M09/M60","M07"],["M08","M08"],["M08/M56","M08"],["M09/M11/M12","M09"],["M09/M11/M12/M60","M11"],["M13/M55","INDEX"],["M01/M04/M06","M01"],["M53/M54/M55","INDEX"],["M07/M08/M10","M10"],["M07/M08/M09","M07"],["M08/M11/M12","M08"],["M55/M60","INDEX"],["M02/M06/M13","M02"],["M07/M08/M09","M07"],["M08/M56","M08"],["M01/M08","M01"],["M07/M08/M60","M07"],["M13/M14/M16/M17","S02"],["M09/M11/M12/M54/M60","D01"]]
NEGATIVES = [["ASYNC_ENQUEUE_NOT_COMPLETE","NO_FALSE_CONCURRENT_EXECUTION"],["MISSING_COPY_ENGINE","NO_OVERLAP_CAPABILITY_BY_GPU_BRAND"],["UNPINNED_HOST_MEMORY","NO_ASSUMED_PINNED_TRANSFER"],["EXCESSIVE_PAGE_LOCKING","NO_UNBOUNDED_HOST_STAGING"],["PREFETCH_WITHOUT_LEASE","NO_GPU_ACTION_FROM_HINT"],["REVOKED_WORK_QUEUED","NO_EXECUTION_FROM_STALE_LEASE"],["TENANT_PREFETCH","NO_CROSS_TENANT_READ"],["DELETED_OBJECT_PREFETCH","NO_STALE_STORAGE_READ"],["SILENT_AUDIO_REORDER","NO_FIDELITY_BY_THROUGHPUT"],["QUALITY_DOWNGRADE","NO_M01_QUALITY_GATE_BYPASS"],["MISSING_INTERFERENCE_SENSOR","NO_UNVERIFIED_VALID_BENCHMARK"],["THERMAL_CONFUSION","NO_CAUSAL_SPEEDUP_CLAIM"],["QUEUE_DEADLOCK","NO_UNBOUNDED_OR_UNRECONCILED_QUEUE"],["IMPLICIT_LATEST_EDIT","NO_IMPLICIT_LATEST_PRODUCTION_REUSE"],["PLATFORM_API_INFERENCE","NO_UNQUALIFIED_CROSS_PLATFORM_RUNTIME"],["FALSE_S04_EXECUTION","NO_DOCUMENTARY_TEST_AS_RUNTIME_PROOF"]]


class S04IntegrityError(ValueError):
    """A historic original source, real-owner status or runtime boundary drifted."""


def must(condition: bool, detail: str) -> None:
    if not condition:
        raise S04IntegrityError(detail)


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    seen = {}
    for key, value in pairs:
        must(key not in seen, "duplicate original JSON key " + key)
        seen[key] = value
    return seen


def load(root: Path = ROOT) -> dict:
    p = json.loads((root / PACKET).read_text(encoding="utf-8"),
                   object_pairs_hook=reject_duplicate_keys)
    must(type(p) is dict, "source research must have object schema")
    return p


def synthetic_schedule_guard(claims: dict) -> dict:
    """Never launch work. Even all-true mock booleans cannot authenticate owners."""
    keys = ("observedM07", "validM08", "jointM09Lease", "m11OwnerAck",
            "m12AttemptFence", "currentRightsM54M55", "m60OSCapability")
    must(type(claims) is dict and set(claims) == set(keys)
         and all(type(v) is bool for v in claims.values()),
         "seven untrusted mock values required")
    return {
        "missingMockClaims": [k for k in keys if not claims[k]],
        "state": "DOCUMENTARY_ONLY_NO_DISPATCH",
        "authenticatedSourceReceipts": 0,
        "gpuAllowed": False,
        "storageAllowed": False,
    }


def validate(p: dict, root: Path = ROOT, *,
             compare_human: bool = False, human_text: str | None = None) -> dict:
    must(type(p) is dict and set(p) == {
        "schema", "workOrder", "issue", "module", "session", "baseSha",
        "baseTreeSha", "asOf", "status", "qualifiedOwnerApprovals",
        "selectedPipeline", "measuredHardware", "ioExecuted", "realGpuRuns",
        "runtime", "b", "c01", "highs", "previousSessions",
        "m12OriginalQuestions", "m12OriginalFutureNegatives", "sourceDocs",
        "externalReferences", "concepts", "alternatives", "metricProtocols",
        "questions", "negativeCases", "stop",
    }, "source packet fields gained or lost")
    must(
        p["schema"] == "iris-m13-s04-source-research-v0.1"
        and p["workOrder"] == "IRIS-WO-0048" and p["issue"] == 155
        and p["module"] == "M13" and p["session"] == "S04"
        and p["baseSha"] == BASE and p["baseTreeSha"] == BASE_TREE
        and p["asOf"] == "2026-09-27"
        and p["status"] == "SOURCE_ONLY_NO_HARDWARE_OR_IO_RUNTIME"
        and type(p["qualifiedOwnerApprovals"]) is int
        and p["qualifiedOwnerApprovals"] == 0
        and p["selectedPipeline"] == "NONE"
        and p["measuredHardware"] == "NONE"
        and p["ioExecuted"] is False and type(p["realGpuRuns"]) is int
        and p["realGpuRuns"] == 0 and p["runtime"] == "NOT_ADMITTED"
        and p["b"] == "DIRECTION_ONLY" and p["c01"] == "UNADOPTED_NOT_FROZEN"
        and p["highs"] == "H01_H02_H03_H04_OPEN_HIGH_FOR_FUTURE_FREEZE"
        and p["previousSessions"] == {
            "s01Questions": "18_OPEN", "s01FutureNegatives": "12_NOT_EXECUTED",
            "s02Questions": "18_OPEN", "s02FutureNegatives": "14_NOT_EXECUTED",
            "s03Questions": "20_OPEN", "s03FutureNegatives": "16_NOT_EXECUTED",
        }
        and p["m12OriginalQuestions"] == "110_OPEN"
        and p["m12OriginalFutureNegatives"] == "80_SPECIFIED_NOT_EXECUTED"
        and type(p["stop"]) is str
        and all(s in p["stop"] for s in (
            "H01-H04", "DIRECTION_ONLY", "UNADOPTED_NOT_FROZEN",
            "SPECIFIED_NOT_EXECUTED", "runtime")),
        "prior source owners/H gates, hardware truth or STOP promoted")
    src = p["sourceDocs"]
    must(type(src) is list and src == ORIGINAL_SOURCES
         and len(src) == 14,
         "historical fourteen exact original source records drifted")
    for s in src:
        original = (root / s["path"]).read_bytes()
        must(blob_sha(original) == s["sha"] and
             s["anchor"] in original.decode("utf-8"),
             "original exact Git blob/anchor mismatch: " + s["role"])
    for path, negKey, q, n in (
        (".engineering/evidence/M13-S01-SOURCE-RESEARCH.json",
         "negativeScenarios", 18, 12),
        (".engineering/evidence/M13-S02-BACKEND-ATTENTION-RESEARCH.json",
         "negativeCases", 18, 14),
        (".engineering/evidence/M13-S03-DELTA-REUSE-RESEARCH.json",
         "futureNegativeCases", 20, 16),
    ):
        previous = json.loads((root / path).read_text(encoding="utf-8"),
                              object_pairs_hook=reject_duplicate_keys)
        must(len(previous["questions"]) == q and len(previous[negKey]) == n
             and all(x["status"] == "SPECIFIED_NOT_EXECUTED"
                     for x in previous[negKey]),
             "S01/S02/S03 actual original question/case facts lost")
    external = p["externalReferences"]
    must(type(external) is list
         and [[s.get("id"), s.get("url")] for s in external] == OFFICIAL,
         "mutable original upstream reference changed or omitted")
    for row in external:
        must(set(row) == {
            "id", "url", "publisher", "checkedOn", "status", "scope"
        } and row["checkedOn"] == "2026-09-27"
             and row["status"] == "MUTABLE_OFFICIAL_REFERENCE_NOT_GPU_OR_OS_ATTESTATION"
             and len(row["scope"]) >= 140,
             "official upstream docs promoted to hardware/OS proof")
    concepts = p["concepts"]
    must(type(concepts) is list and
         [x.get("id") for x in concepts] == CLASS_IDS,
         "seven original concept identities lost")
    for x in concepts:
        must(set(x) == {
            "id", "name", "hypothesis", "requiredOwnerProof",
            "failureBoundary", "originalOwnerRoute", "status"
        } and x["status"] == "CONCEPT_ONLY_UNADOPTED"
             and len(x["hypothesis"]) >= 70
             and len(x["requiredOwnerProof"]) >= 112
             and len(x["failureBoundary"]) >= 100,
             "concept false admission, incomplete owner proof or unsafe failure boundary")
    alternatives = p["alternatives"]
    must(type(alternatives) is list and
         [x.get("id") for x in alternatives] == ALTERNATIVE_IDS,
         "four original unselected alternatives lost")
    for row in alternatives:
        must(set(row) == {"id", "name", "hypothesis", "tradeoff",
                           "status", "selected"}
             and row["status"] == "UNSELECTED_UNMEASURED"
             and row["selected"] is False
             and len(row["hypothesis"]) >= 90
             and len(row["tradeoff"]) >= 100,
             "unselected alternative promoted or missing tradeoff")
    metrics = p["metricProtocols"]
    must(type(metrics) is list
         and [x.get("id") for x in metrics] == METRICS,
         "twelve not-measured metric protocols lost")
    for row in metrics:
        must(set(row) == {"id", "ownerRoute", "proposedProtocol", "status"}
             and row["status"] == "PROTOCOL_CONCEPT_NOT_MEASURED"
             and len(row["proposedProtocol"]) >= 95,
             "future metric falsely claimed measured")
    questions = p["questions"]
    must(type(questions) is list and
         [q.get("id") for q in questions] ==
         [f"M13-S04-U{i:02d}" for i in range(1, 21)],
         "twenty S04 original question identities lost")
    for q, (owner, role) in zip(questions, QUESTION_ROUTES):
        must(set(q) == {"id", "originalOwnerRoute", "question",
                         "sourceRole", "status", "risk", "answer"}
             and q["originalOwnerRoute"] == owner
             and q["sourceRole"] == role
             and role in {s["role"] for s in src}
             and len(q["question"]) >= 120
             and q["status"] == "OPEN_UNRATED_PENDING_QUALIFIED_OWNER"
             and q["risk"] == "UNRATED" and q["answer"] is None,
             "owner question falsely answered, rerouted or truncated")
    cases = p["negativeCases"]
    must(type(cases) is list and
         [[x.get("label"), x.get("futureNonAuthorizingOracle")]
          for x in cases] == NEGATIVES
         and [x.get("id") for x in cases] ==
         [f"M13-S04-N{i:02d}" for i in range(1, 17)],
         "sixteen new original negative identities/oracles drifted")
    for case in cases:
        must(set(case) == {
            "id", "label", "classIds", "trigger",
            "futureNonAuthorizingOracle", "status"
        } and case["status"] == "SPECIFIED_NOT_EXECUTED"
             and type(case["classIds"]) is list
             and len(case["classIds"]) > 0
             and set(case["classIds"]) <= set(CLASS_IDS)
             and len(case["classIds"]) == len(set(case["classIds"]))
             and len(case["trigger"]) >= 86,
             "new S04 future case falsely executed or concept unknown")
    if compare_human:
        body = human_text if human_text is not None else (
            root / REPORT).read_text(encoding="utf-8")
        fence = chr(96) * 3
        marker = "\n## Appendix A: canonical original machine packet\n\n" + fence + "json\n"
        must(body.count(marker) == 1 and body.endswith("\n" + fence + "\n"),
             "no single exact human/machine appendix")
        visible, appendix = body.split(marker)
        raw, trailing = appendix.split("\n" + fence + "\n", 1)
        must(trailing == "" and
             json.loads(raw, object_pairs_hook=reject_duplicate_keys) == p,
             "human report canonical original machine appendix mismatch")
        for row in (*concepts, *alternatives, *metrics, *questions, *cases):
            must(row["id"] in visible, "source report omitted original ID")
        for row in questions:
            must(row["question"] in visible, "original question wording not presented")
        for row in src:
            must(row["path"] in visible and row["sha"] in visible,
                 "human source reference original Git blob missing")
        for row in external:
            must(row["url"] in visible and row["scope"] in visible,
                 "official mutable context lost from human report")
    return {
        "sourceOnly": True, "exactOriginalGitBlobs": len(src),
        "mutablePublicOfficialReferences": len(external),
        "unadoptedConcepts": len(concepts),
        "unselectedAlternatives": len(alternatives),
        "proposedNotMeasuredMetricProtocols": len(metrics),
        "newOpenS04OwnerQuestions": len(questions),
        "futureS04NegativesNotExecuted": len(cases),
        "qualifiedOwners": 0, "hardwareMeasurements": 0,
        "gpuRuns": 0, "runtime": "NOT_ADMITTED",
    }


def verify_all(root: Path = ROOT) -> dict:
    return validate(load(root), root, compare_human=True)


if __name__ == "__main__":
    try:
        print("M13 S04 SOURCE-ONLY PASS " +
              json.dumps(verify_all(), sort_keys=True) +
              " | no actual CUDA, I/O, owner signoff or runtime")
    except (S04IntegrityError, OSError, ValueError, TypeError, KeyError,
            UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit("M13 S04 FAIL CLOSED: " + str(exc)) from exc
