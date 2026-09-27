"""WO0045: immutable source-bound M13 S01 research, no runtime or owner signoff."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M13-S01-SOURCE-RESEARCH.json"
REPORT = "planning/research/M13-S01-WARM-MODEL-CACHE-LOCALITY.md"
BASE = "2dbb91495804338f46aad9716f36e10409c64935"
TREE = "2746e60e410940e191bf65aa50cbf9ba86031144"
SOURCES = [["INDEX","planning/MASTER-MODULE-INDEX.md","### M13 — Performance, Cache & Execution Efficiency"],["M01","docs/M01-QUALITY-KERNEL.md","Frozen contract: `m01-contract-v1.0`"],["M02","planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md","cache/warm-state loss changes performance, not production truth;"],["M06","planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md","Digest equality proves byte equality under the declared digest domain only."],["M07","docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md","M07 does not lower quality targets"],["M08","docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md","M08 records empirical performance evidence"],["M09","docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md","M09 is the provider-neutral resource-state"],["M10","planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md","Implementation authority: NOT ADMITTED"],["M11","planning/contracts/M11-MODULE-CONTRACT-FREEZE-CANDIDATE.md","Status: PROPOSED_C02_CORRECTION_NOT_FROZEN"],["M12","planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md","Status: PROPOSED_NOT_FROZEN"],["D01",".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json","B_FUTURE_OWNER_RECEIPT"]]
QUESTION_OWNERS = [["M13/M02/M06",["M02","M06"]],["M13/M14/M18",["INDEX","M06"]],["M13/M07",["M07"]],["M13/M08",["M08"]],["M13/M09",["M09"]],["M13/M09/M11/M12",["M09","M11","M12","D01"]],["M13/M54/M55",["INDEX","M02"]],["M13/M55",["INDEX","M06"]],["M13/M01",["M01","M02"]],["M13/M53",["INDEX","M06"]],["M13/M14/M16/M17",["INDEX","M07"]],["M13/M10/M12",["M10","M12"]],["M13/M56/M08",["M08","INDEX"]],["M13/M60",["INDEX","M09"]],["M13/M11",["M11"]],["M13/M02/M06",["M02","M06"]],["M13/M55/M54",["INDEX","M09"]],["M13/M08/M01",["M08","M01","M10"]]]
CASE_ORACLES = ["NO_CROSS_TENANT_REUSE_OR_PERMISSION_INFERENCE","NO_UNQUALIFIED_SEMANTIC_REUSE","INVALIDATE_OR_ABSTAIN_UNTIL_OWNER_SOURCE_PROVEN","NO_RESIDENCY_HINT_TO_GRANT_OR_DISPATCH","NO_PROCESS_RIGHTS_OR_CAPACITY_RECLAMATION_INFERENCE","FAIL_CLOSED_REUSE_AND_DEFER_STORAGE_DELETION_TO_OWNER","NO_DRAFT_TO_MASTER_PROMOTION","NO_UNVERIFIED_PERFORMANCE_CLAIM_OR_SELECTED_THRESHOLD","NO_M09_GRANT_OR_M12_PLACEMENT_INFERENCE","REUSE_BLOCKED_PENDING_REAL_RIGHTS_OWNER_PROOF","NO_UNQUALIFIED_DEVICE_COMPILED_REUSE","NO_UNAUTHORIZED_WORKSTATION_INTERFERENCE_OR_QUALITY_DOWNGRADE"]
CLASS_IDS = ["C01_SOURCE_ARTIFACT_IDENTITY","C02_HOST_LOCAL_WARM_WORKSET","C03_DEVICE_RESIDENCY_HINT","C04_COMPILED_BACKEND_ARTIFACT","C05_INTERMEDIATE_AND_DELTA_REUSE"]
ALTERNATIVE_IDS = ["ALT01_NO_EARLY_PREFETCH","ALT02_HOST_LOCAL_VERIFIED_WARMING","ALT03_READ_ONLY_M09_RESIDENCY_HINT","ALT04_OWNER_QUALIFIED_ADAPTIVE_PREFETCH"]
METRIC_IDS = ["LATENCY_COLD_P50_P95","LATENCY_WARM_P50_P95","SOURCE_QUALIFIED_HIT_RATE","HOST_AND_DEVICE_OBSERVED_BYTES","CACHE_INVALIDATION_AND_RELOAD_COST","DISK_AND_TRANSFER_COST","WORKSTATION_INTERFERENCE","M01_QUALITY_NONREGRESSION","WASTED_PREFETCH_AND_EVICTION","EVIDENCE_FRESHNESS_AND_DRIFT"]


class M13S01IntegrityError(ValueError):
    """Source-only evidence was altered, upgraded or presented as real proof."""


def require(value: bool, why: str) -> None:
    if not value:
        raise M13S01IntegrityError(why)


def blob_sha(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(root: Path = ROOT) -> dict:
    packet = json.loads((root / PACKET).read_text(encoding="utf-8"),
                        object_pairs_hook=unique_pairs)
    require(type(packet) is dict, "M13 S01 packet must be a JSON object")
    return packet


def render_report(p: dict) -> str:
    lines = [
        "# M13 S01 | Warm Model, Cache Strategy & Locality", "",
        "**NONBINDING SOURCE RESEARCH ONLY | IRIS-WO-0045 | Issue #155 OPEN.**",
        "No owner-issued M13 contract, model/cache implementation, hardware benchmark, storage action, adopted algorithm, M09 lease, runtime or public API is authorized by this report.",
        "",
        "## 1. Bounded mission and existing source authority", "",
        "Investigate whether future source-qualified warm model and artifact/cache locality could improve production startup without competing with M01 quality, M02/M06 identity, M07/M08 evidence, M09 resource grants/residency, M10 advisory plans, M11 real process ownership, M12 placement or future M14/M18/M53/M54/M55/M60 owners.",
        "",
        f'Historical exact source main: \`{p["sourceBaseSha"]}\`, tree \`{p["sourceBaseTreeSha"]}\`. Current B_FUTURE_OWNER_RECEIPT is DIRECTION_ONLY; older source documents may legitimately preserve historical NONE_SELECTED. All H01-H04 remain OPEN HIGH_FOR_FUTURE_FREEZE.',
        "",
        f'### {len(p["sourceDocs"])} immutable exact historical source inputs', "",
    ]
    for s in p["sourceDocs"]:
        lines.append(
            f'- **{s["role"]}**: [\`{s["path"]}\`](../../{s["path"]}); original Git blob \`{s["gitBlobSha1"]}\`; required source anchor: \`{s["exactNeedle"]}\`.'
        )
    lines.extend(["", "## 2. Five cache classes, none adopted", ""])
    for q in p["cacheClasses"]:
        lines.extend([
            f'### {q["id"]}: {q["title"]}', "",
            f'- Potential: {q["boundedPotential"]}',
            f'- Exact outstanding owner proof: {q["unresolvedProof"]}',
            f'- Original dependency owners: {q["originalOwners"]}',
            f'- Status: **{q["status"]}**', "",
        ])
    lines.extend(["## 3. Architectural candidates, all unselected", ""])
    for a in p["alternatives"]:
        lines.extend([
            f'### {a["id"]}: {a["title"]}', "",
            f'- Conditional research hypothesis: {a["hypothesis"]}',
            f'- Tradeoffs and unqualified dependencies: {a["tradeoffs"]}',
            "- Decision: **DISCUSSION_NOT_ADOPTED**; no preferred or selected candidate.", "",
        ])
    lines.extend([
        "## 4. Cold/warm evidence design, no measurement or numeric gate", "",
        "Control exact accepted M02 revision/M06 operational lineage, model/source/rights, M07 runtime hardware binding, M08 protocol/freshness/noise, and identical M01 fidelity obligations. Record cold and warm runs separately, interference/unsupported/UNKNOWN explicitly, no hidden prefetch/other-tenant pressure and no quality degradation. Comparing conceptual metrics does NOT execute a benchmark or permit a cache operation.",
        "",
    ])
    for m in p["measurementPlan"]["metrics"]:
        lines.append(
            f'- \`{m["id"]}\` [{m["measurementOwner"]}] {m["definition"]} **{m["status"]}**'
        )
    lines.extend([
        "", "## 5. Eighteen source-anchored OPEN owner questions", "",
        "All questions below were FIRST PROPOSED as M13 S01 planning research in this Work Order. They are **not** historic M12 original questions and do not alter the existing M12 110, 91/19 split, C03 19 or M54/M60 18. No draft response, risk score, independent owner signature or runtime authority is implied.",
        "",
    ])
    for q in p["questions"]:
        roles = ", ".join(f'\`{name}\`' for name in q["sourceRoles"])
        lines.extend([
            f'### {q["id"]} | {q["originalOwners"]}', "",
            q["question"], "",
            f'Pinned source roles: {roles}. Status: **{q["status"]}**; risk: **UNRATED**; executable authority: **NONE**; actual owner answer: **NOT RECEIVED**.',
            "",
        ])
    lines.extend(["## 6. Twelve future negative-case designs, NOT EXECUTED", ""])
    for n in p["negativeScenarios"]:
        qids = ", ".join(f'\`{qid}\`' for qid in n["questionIds"])
        lines.extend([
            f'### {n["id"]} | {n["originalOwners"]}', "",
            f'- Proposed hostile/ambiguous input: {n["trigger"]}',
            f'- Proposed non-authorizing oracle: \`{n["nonAuthorizingOracle"]}\`.',
            f'- Related new M13 S01 questions: {qids}.',
            f'- Test status: **{n["status"]}**; no real hardware/OS/provider test was run.', "",
        ])
    lines.extend([
        "## 7. Explicit gates and STOP", "",
        f'- Source state: M09 \`{p["m09v1"]}\`, selected future M09 receipt \`{p["ownerB"]}\`, C01 \`{p["m09C01"]}\`, M10 \`{p["m10"]}\`, M11 \`{p["m11"]}\`, M12 \`{p["m12"]}\`.',
        f'- H01-H04: **{p["h01h02h03h04"]}**; no actual qualified M12/M54/M58/M60 contract received, no H03 closure and no M10/M11/M12 runtime.',
        "- This report neither adopts a new interface nor runs a benchmark, prefetch, warmup, process/GPU/storage/network/cloud action, source download or public API.",
        f'- STOP: {p["stop"]}', "",
    ])
    return "\n".join(lines) + "\n"


def verify_packet(p: dict, root: Path = ROOT, *,
                  verify_markdown: bool = True) -> dict:
    require(type(p) is dict and set(p) == {
        "schemaVersion", "workOrder", "issue", "module", "session",
        "sourceBaseSha", "sourceBaseTreeSha", "status", "ownerApproval",
        "selectedTechnology", "runtime", "m09v1", "ownerB", "m09C01",
        "m10", "m11", "m12", "currentFourHighs", "h01h02h03h04",
        "sourceDocs", "cacheClasses", "alternatives", "measurementPlan",
        "questions", "negativeScenarios", "stop",
    }, "unknown or missing M13 S01 evidence field")
    require(
        p["schemaVersion"] == "iris-m13-s01-source-research-v0.1"
        and p["workOrder"] == "IRIS-WO-0045" and p["issue"] == 155
        and p["module"] == "M13" and p["session"] == "S01"
        and p["sourceBaseSha"] == BASE and p["sourceBaseTreeSha"] == TREE
        and p["status"] == "SOURCE_RESEARCH_ONLY_NONBINDING"
        and p["ownerApproval"] == "NONE"
        and p["selectedTechnology"] == "NONE"
        and p["runtime"] == "NOT_ADMITTED"
        and p["m09v1"] == "FROZEN_UNCHANGED"
        and p["ownerB"] == "B_FUTURE_OWNER_RECEIPT_DIRECTION_ONLY"
        and p["m09C01"] == "UNADOPTED_NOT_FROZEN"
        and p["m10"] == "FROZEN_PLANNING_IMPLEMENTATION_NOT_ADMITTED"
        and p["m11"] == "V0_2_NOT_FROZEN_86_ORIGINAL_QUESTIONS_OPEN"
        and p["m12"] == "V0_1_NOT_FROZEN_110_QUESTIONS_OPEN_80_FUTURE_NEGATIVES_NOT_EXECUTED"
        and p["currentFourHighs"] ==
            [f"C02-FR-H{i:02d}" for i in range(1, 5)]
        and p["h01h02h03h04"] == "ALL_OPEN_HIGH_FOR_FUTURE_FREEZE"
        and type(p["stop"]) is str and len(p["stop"]) > 250
        and "NOT_ADMITTED" in p["stop"] and "NOT_EXECUTED" in p["stop"],
        "owner scope, historical source or hard runtime STOP changed",
    )
    docs = p["sourceDocs"]
    require(type(docs) is list and len(docs) == len(SOURCES),
            "exact historical source count missing")
    for actual, (role, path, needle) in zip(docs, SOURCES):
        raw = (root / path).read_bytes()
        require(actual == {
            "role": role, "path": path,
            "gitBlobSha1": blob_sha(raw), "exactNeedle": needle,
        } and needle in raw.decode("utf-8"),
            "frozen source Git blob SHA/anchor/role drift: " + role)
    index = (root / SOURCES[0][1]).read_text(encoding="utf-8")
    for name in (
        "S01 — S01 Warm model/cache strategy and cache locality",
        "S02 — S02 Compilation, attention and backend selection",
        "S03 — S03 Intermediate reuse and generation delta cache",
        "S04 — S04 CPU/GPU overlap, I/O scheduling and storage efficiency",
        "S05 — S05 Performance budgets, profiling and anti-regression gates",
    ):
        require(name in index, "original M13 five-session master index changed: " + name)

    classes = p["cacheClasses"]
    require(type(classes) is list and [x.get("id") for x in classes] == CLASS_IDS,
            "five source-only conceptual cache classes changed")
    for x in classes:
        require(set(x) == {"id", "title", "boundedPotential", "unresolvedProof",
                           "originalOwners", "status"}
                and x["status"] == "UNADOPTED_CONCEPT_ONLY"
                and all(type(x[k]) is str and len(x[k]) >= 18
                        for k in ("title", "boundedPotential", "unresolvedProof", "originalOwners")),
                "cache class claims selected or no original owner caveats")
    alternatives = p["alternatives"]
    require(type(alternatives) is list
            and [x.get("id") for x in alternatives] == ALTERNATIVE_IDS,
            "four bounded alternatives absent or reordered")
    for row in alternatives:
        require(set(row) == {"id", "title", "hypothesis", "tradeoffs", "selected", "status"}
                and row["selected"] is False
                and row["status"] == "DISCUSSION_NOT_ADOPTED"
                and type(row["hypothesis"]) is str and len(row["hypothesis"]) >= 65
                and type(row["tradeoffs"]) is str and len(row["tradeoffs"]) >= 65,
                "technology choice or speculative unqualified candidate promoted")
    measurement = p["measurementPlan"]
    require(type(measurement) is dict
            and set(measurement) == {"protocolStatus", "adoptedNumericThresholds", "metrics"}
            and measurement["protocolStatus"] ==
                "CONCEPT_ONLY_NO_HARDWARE_OR_PROVIDER_MEASUREMENT"
            and measurement["adoptedNumericThresholds"] is False
            and type(measurement["metrics"]) is list
            and [x.get("id") for x in measurement["metrics"]] == METRIC_IDS,
            "unmeasured cold/warm conceptual metrics promoted to benchmark evidence")
    for row in measurement["metrics"]:
        require(set(row) == {"id", "measurementOwner", "definition", "status"}
                and row["status"] == "PROTOCOL_TO_QUALIFY_NOT_MEASURED"
                and type(row["definition"]) is str and len(row["definition"]) >= 45,
                "metric falsely measured or truncated")
    rows = p["questions"]
    require(type(rows) is list and len(rows) == len(QUESTION_OWNERS)
            and [q.get("id") for q in rows] ==
                [f"M13-S01-U{i:02d}" for i in range(1, len(QUESTION_OWNERS)+1)],
            "original 18 S01 questions reordered, removed or duplicated")
    roles = {name for name, _, _ in SOURCES}
    for (label, required_roles), row in zip(QUESTION_OWNERS, rows):
        require(set(row) == {"id", "originalOwners", "sourceRoles", "question",
                             "status", "risk", "ownerAnswer", "executableAuthority"}
                and row["originalOwners"] == label
                and row["sourceRoles"] == required_roles
                and all(name in roles for name in row["sourceRoles"])
                and type(row["question"]) is str and len(row["question"]) >= 95
                and row["status"] == "OPEN_UNRATED_PENDING_QUALIFIED_OWNER"
                and row["risk"] == "UNRATED" and row["ownerAnswer"] is None
                and row["executableAuthority"] == "NONE",
                "M13 S01 original owner question was answered, rerouted, shortened or promoted")
    negs = p["negativeScenarios"]
    require(type(negs) is list and len(negs) == len(CASE_ORACLES)
            and [n.get("id") for n in negs] ==
                [f"CWS-{i:02d}" for i in range(1, len(CASE_ORACLES)+1)],
            "future negative case IDs missing, duplicate or reordered")
    ids = {q["id"] for q in rows}
    for n, oracle in zip(negs, CASE_ORACLES):
        require(set(n) == {"id", "questionIds", "trigger", "nonAuthorizingOracle",
                           "originalOwners", "status"}
                and n["nonAuthorizingOracle"] == oracle
                and type(n["trigger"]) is str and len(n["trigger"]) >= 75
                and type(n["originalOwners"]) is str and len(n["originalOwners"]) >= 7
                and type(n["questionIds"]) is list and bool(n["questionIds"])
                and len(n["questionIds"]) == len(set(n["questionIds"]))
                and set(n["questionIds"]) <= ids
                and n["status"] == "SPECIFIED_NOT_EXECUTED",
                "future M13 S01 negative scenario invalid, falsely run or missing ownership")
    if verify_markdown:
        require((root / REPORT).read_text(encoding="utf-8") == render_report(p),
                "human M13 S01 source report differs from exact original packet")
    return {
        "sourceOnly": True, "originalM13S01QuestionsOpen": len(rows),
        "futureNegativeDesignsNotExecuted": len(negs),
        "cacheClassesNotAdopted": len(classes),
        "alternativesNotSelected": len(alternatives),
        "coldWarmMetricProtocolsNotMeasured": len(measurement["metrics"]),
        "sourceGitBlobPinsVerified": len(SOURCES),
        "realOwnerApprovals": 0,
        "H01H02H03H04": "ALL_OPEN_HIGH_FOR_FUTURE_FREEZE",
        "M10M11M12Runtime": "NOT_ADMITTED",
    }


def verify_all(root: Path = ROOT) -> dict:
    return verify_packet(read_json(root), root)


if __name__ == "__main__":
    try:
        print("M13 S01 source research: PASS " +
              json.dumps(verify_all(), sort_keys=True) +
              " | NO real owner approval, no cache runtime")
    except (M13S01IntegrityError, OSError, UnicodeError,
            json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
        raise SystemExit("M13 S01 source research: FAIL " + str(error)) from error
