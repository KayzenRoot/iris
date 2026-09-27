"""Deterministic M12 planning-evidence gate, NOT a runtime/safety attestation.

Fail closed on missing, reordered, fabricated or silently "approved" source
questions, future test scenarios, FTR references, FCS module headings, and
unresolved M09 owner decisions. Never enables an M12 worker or dispatch.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ".engineering/evidence/M12-OWNER-DECISION-REGISTER.json"
C02 = ".engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json"
FTR = "planning/reviews/M12-FINAL-TECHNOLOGY-REVIEW.md"
FCS = "planning/compatibility/M12-FORWARD-COMPATIBILITY-SCAN.md"
INDEX = "planning/MASTER-MODULE-INDEX.md"
CANDIDATE = "planning/contracts/M12-MODULE-CONTRACT-FREEZE-CANDIDATE.md"
SESSION_SPECS = (
    ("S01", "WR", 18, 12, "planning/research/M12-S01-WORKER-REGISTRY-AND-CAPABILITY-ADVERTISEMENTS.md"),
    ("S02", "SQ", 20, 14, "planning/research/M12-S02-PLACEMENT-QUEUES-QUOTAS-PRIORITY.md"),
    ("S03", "MG", 22, 16, "planning/research/M12-S03-MULTI-GPU-HETEROGENEOUS-EXECUTION.md"),
    ("S04", "FN", 24, 18, "planning/research/M12-S04-LAN-REMOTE-CLOUD-FEDERATION.md"),
    ("S05", "FT", 26, 20, "planning/research/M12-S05-FAILOVER-PREEMPTION-COST-TRUST.md"),
)
REQUIRED_DEPENDENCIES = frozenset((
    "M09_ISSUE_110_TOPOLOGY_NONE_SELECTED", "C02_FR_H01_OPEN",
    "C02_FR_H02_OPEN", "C02_FR_H03_OPEN", "C02_FR_H04_OPEN",
    "M11_V02_NOT_FROZEN", "M54_OWNER_CONTRACT_PENDING",
    "M58_OWNER_CONTRACT_PENDING", "M60_OWNER_CONTRACT_PENDING",
    "M02_M06_EXACT_CROSS_OWNER_DISPOSITIONS_PENDING",
    "M12_RUNTIME_TRIALS_NOT_EXECUTED",
))
FTR_STATUS = frozenset(("ACCEPT_REFERENCE", "DEFER_OWNER_CONTRACT", "REJECT_AS_CURRENT_AUTHORITY"))
QROW = re.compile(r"^[|] (M12-S[0-9]{2}-U[0-9]{2}) [|] ([^|]+) [|] ([^|]+) [|]$")
NROW = re.compile(r"^[|] ([A-Z]{2}-[0-9]{2}) [|] ([^|]+) [|] ([^|]+) [|] ([^|]+) [|]$")
INDEX_ROW = re.compile(r"^### (M[0-9]{2}) — (.+)$")
FCS_ROW = re.compile(r"^[|] (M[0-9]{2}) [|] ([^|]+) [|] ([^|]+) [|] ([^|]+) [|] ([^|]+) [|]$")
FTR_ROW = re.compile(r"^[|] (FTR-[0-9]{2}) [|] (.+) [|] (ACCEPT_REFERENCE|DEFER_OWNER_CONTRACT|REJECT_AS_CURRENT_AUTHORITY) [|] ([^|]+) [|] ([^|]+) [|]$")


class M12EvidenceError(ValueError):
    """Documentary evidence cannot support its declared source-bound state."""


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise M12EvidenceError(reason)


def unique_json(pairs: list[tuple[str, object]]) -> dict[str, object]:
    data: dict[str, object] = {}
    for key, value in pairs:
        require(key not in data, f"duplicate JSON key: {key}")
        data[key] = value
    return data


def research_rows(markdown: str, session: str, prefix: str, qcount: int, ncount: int, source: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Extract only source-provided IDs, ownership, questions and negative oracles."""
    questions: list[dict[str, str]] = []
    negatives: list[dict[str, str]] = []
    for line in markdown.splitlines():
        q = QROW.fullmatch(line)
        if q and q.group(1).startswith(f"M12-{session}-"):
            questions.append(dict(id=q.group(1), session=session, owners=q.group(2).strip(),
                                  question=q.group(3).strip(), status="OPEN_UNRATED_PENDING_OWNER", source=source))
        n = NROW.fullmatch(line)
        if n and n.group(1).startswith(prefix + "-"):
            negatives.append(dict(id=n.group(1), session=session, trigger=n.group(2).strip(),
                                  safetyOracle=n.group(3).strip(), owners=n.group(4).strip(),
                                  status="SPECIFIED_NOT_EXECUTED", source=source))
    expected_q = [f"M12-{session}-U{i:02d}" for i in range(1, qcount + 1)]
    expected_n = [f"{prefix}-{i:02d}" for i in range(1, ncount + 1)]
    require([q["id"] for q in questions] == expected_q, f"{session}: missing/duplicate/reordered owner questions")
    require([n["id"] for n in negatives] == expected_n, f"{session}: missing/duplicate/reordered future scenarios")
    require(all(q["owners"] and q["question"] for q in questions), f"{session}: empty owner/question")
    require(all(n["trigger"] and n["safetyOracle"] and n["owners"] for n in negatives), f"{session}: incomplete future oracle")
    return questions, negatives


def verify_register(record: dict[str, object], questions: list[dict[str, str]], negatives: list[dict[str, str]]) -> None:
    require(record.get("schemaVersion") == "iris-m12-owner-readiness-v0.1", "register schema mismatch")
    require(record.get("workOrder") == "IRIS-WO-0028" and record.get("issue") == 128, "wrong register work order/issue")
    require(record.get("status") == "UNADOPTED_NOT_FROZEN_OWNER_DECISIONS_PENDING", "owner register falsely promoted")
    require(record.get("selectedTopology") == "NONE" and record.get("publicOrExecutablePort") == "NONE", "register declares an unapproved port/topology")
    require(record.get("implementationStatus") == "NOT_ADMITTED", "runtime not admitted")
    expected_counts = dict(sessions=5, ownerQuestions=110, futureNegativeScenarios=80,
                           laterIndexModules=48, technologyRecords=16)
    require(record.get("counts") == expected_counts, "register count mismatch")
    require(record.get("questions") == questions, "owner register differs from exact source rows or status")
    require(record.get("negativeScenarios") == negatives, "negative-case register differs from exact source or execution status")
    deps = record.get("unresolvedHardDependencies")
    require(isinstance(deps, list) and len(deps) == len(REQUIRED_DEPENDENCIES)
            and set(deps) == REQUIRED_DEPENDENCIES, "unresolved dependency/owner gate removed or duplicated")


def verify_ftr(markdown: str) -> None:
    """The 16 FTR records are evidence dispositions, never a technology selection."""
    rows = []
    for line in markdown.splitlines():
        if line.startswith("| FTR-"):
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            require(len(parts) == 7, "malformed FTR evidence table")
            rows.append(parts)
    expected = [f"FTR-{i:02d}" for i in range(1, 17)]
    require([row[0] for row in rows] == expected, "FTR missing/reordered/duplicate evidence records")
    require(all(row[4] in FTR_STATUS and all(row[1:4]) and row[5] and row[6] for row in rows),
            "FTR missing source, disposition, rationale or owner")
    require("zero runtime technology" in markdown.lower() or "no irIs scheduler" in markdown.lower() or
            "no iris scheduler" in markdown.lower(), "FTR does not explicitly deny runtime adoption")


def verify_fcs(index: str, scan: str) -> None:
    """Later modules are exactly the master-index M13..M60 headings, not accepted APIs."""
    titles = [(m.group(1), m.group(2)) for line in index.splitlines()
              if (m := INDEX_ROW.fullmatch(line)) and "M13" <= m.group(1) <= "M60"]
    expected = [(f"M{i:02d}", name) for i, (_, name) in enumerate(titles, 13)]
    require(len(titles) == 48 and titles == expected, "master-index M13..M60 missing or reordered")
    rows = [m.groups() for line in scan.splitlines()
            if (m := FCS_ROW.fullmatch(line)) and "M13" <= m.group(1) <= "M60"]
    require(len(rows) == 48 and [(r[0], r[1]) for r in rows] == titles, "FCS mismatch to exact master index")
    require(all(r[2].strip() and r[3].strip() and r[4].strip() ==
                "INDEX_ONLY / OWNER_CONTRACT_PENDING" for r in rows), "FCS owner gate promoted or incomplete")


def verify_c02(data: dict[str, object]) -> None:
    require(data.get("issue110OwnerDecision") == "NOT_RECORDED", "M09 #110 owner decision unexpectedly changed; re-review needed")
    require(data.get("noSelectedTopology") is True, "M09 owner topology cannot be inferred")
    blockers = data.get("futureFreezeBlockers")
    require(isinstance(blockers, list) and len(blockers) == 4, "M09 H01..H04 evidence missing")
    require([b.get("id") for b in blockers] == [f"C02-FR-H{i:02d}" for i in range(1, 5)],
            "M09 future-freeze blocker identities drifted")
    require(all(b.get("severity") == "HIGH_FOR_FUTURE_FREEZE" and
                str(b.get("status", "")).startswith("OPEN_") for b in blockers), "M09 owner HIGH blocker falsely closed")


def verify_all(root: Path) -> dict[str, int]:
    def read(path: str) -> str:
        return (root / path).read_text(encoding="utf-8")
    questions: list[dict[str, str]] = []
    negative: list[dict[str, str]] = []
    for sess, prefix, nq, nn, source in SESSION_SPECS:
        q, n = research_rows(read(source), sess, prefix, nq, nn, source)
        questions.extend(q)
        negative.extend(n)
    record = json.loads(read(REGISTER), object_pairs_hook=unique_json)
    require(isinstance(record, dict), "register must be a JSON object")
    verify_register(record, questions, negative)
    verify_ftr(read(FTR))
    verify_fcs(read(INDEX), read(FCS))
    c02 = json.loads(read(C02), object_pairs_hook=unique_json)
    require(isinstance(c02, dict), "C02 evidence must be JSON object")
    verify_c02(c02)
    candidate = read(CANDIDATE)
    require("Candidate ID: m12-contract-candidate-v0.1" in candidate, "M12 candidate version missing")
    require("Status: PROPOSED_NOT_FROZEN" in candidate and
            "Implementation authority: NOT_ADMITTED" in candidate, "M12 candidate falsely promoted")
    invariant_ids = re.findall(r"^[|] (M12-I[0-9]{2}) [|]", candidate, flags=re.MULTILINE)
    require(invariant_ids == [f"M12-I{i:02d}" for i in range(1, 25)],
            "M12 candidate invariant IDs missing, duplicated or reordered")
    return dict(questions=len(questions), negative=len(negative), ftr=16, fcs=48, invariants=24, c02HighOpen=4)


if __name__ == "__main__":
    try:
        stats = verify_all(ROOT)
    except (M12EvidenceError, OSError, UnicodeError, ValueError) as exc:
        raise SystemExit(f"M12 planning evidence: FAIL: {exc}") from exc
    print("M12 planning evidence: PASS " + ", ".join(f"{k}={v}" for k, v in stats.items()) +
          "; no technology/runtime/owner approval inferred")
