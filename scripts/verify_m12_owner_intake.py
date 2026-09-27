"""Fail-closed M12 owner-intake routing, NOT owner selection or runtime approval.

This script derives a review queue directly from the canonical 110 OPEN M12
questions, 80 unexecuted future test cases and four OPEN M09 C02 blockers.
The result is redundant documentary routing evidence, never a new contract.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.verify_m12_planning_evidence import (
    ROOT, M12EvidenceError, REQUIRED_DEPENDENCIES, SESSION_SPECS,
    unique_json, verify_all as verify_m12_source_evidence,
)

REGISTER = ".engineering/evidence/M12-OWNER-DECISION-REGISTER.json"
C02 = ".engineering/evidence/M09-HANDOFF-C02-DEPENDENCY-MATRIX.json"
INDEX = "planning/MASTER-MODULE-INDEX.md"
ROUTING = ".engineering/evidence/M12-OWNER-INTAKE-C02.json"
BASE_SHA = "cccc9f3cd23be53e6154f605a37eb9cd6f28b1ca"
BASE_TREE_SHA = "f3178da68514279ef5454b8520debed6871d7416"
FROZEN_INPUTS = ("M02", "M06", "M09", "M10")
PROPOSED_CANDIDATES = ("M11", "M12")
LANES = (
    "EXPLICIT_ISSUE_110_REVIEW",
    "LATER_OWNER_CONTRACT_REQUIRED",
    "M11_CANDIDATE_CROSS_OWNER_REVIEW",
    "FROZEN_OWNER_HANDOFF_REVIEW",
    "M12_PROPOSABLE_WITH_FROZEN_SOURCE_INPUTS",
)
LABEL = re.compile(r"M[0-9]{2}(?:/(?:M[0-9]{2}|#110))*")
HEADING = re.compile(r"### (M[0-9]{2}) — (.+)")


class IntakeRoutingError(ValueError):
    """The source register cannot support the claimed planning-only routing."""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise IntakeRoutingError(message)


def later_owner_ids(index_text: str) -> tuple[str, ...]:
    rows = [(m.group(1), m.group(2)) for s in index_text.splitlines()
            if (m := HEADING.fullmatch(s)) and "M13" <= m.group(1) <= "M60"]
    need(len(rows) == 48 and [a for a, _ in rows] ==
         [f"M{i:02d}" for i in range(13, 61)] and all(name for _, name in rows),
         "master index must identify all 48 canonical later owner headings")
    return tuple(a for a, _ in rows)


def parse_owner_label(label: object, later: tuple[str, ...]) -> tuple[list[str], bool]:
    need(isinstance(label, str) and LABEL.fullmatch(label) is not None,
         "unrecognized or malformed original owner label")
    tokens = label.split("/")
    owners = [x for x in tokens if x != "#110"]
    issue110 = "#110" in tokens
    need(len(owners) == len(set(owners)), "duplicated original owner token")
    need(tokens.count("#110") <= 1 and (not issue110 or "M09" in owners),
         "issue #110 may only be cited alongside M09 and once")
    allowed = set(FROZEN_INPUTS + PROPOSED_CANDIDATES + later)
    need(bool(owners) and all(x in allowed for x in owners),
         "owner token has no verified canonical source tier")
    return owners, issue110


def build_routing(register: dict, c02: dict, index_text: str) -> dict:
    """Derive only source-visible owners; routing lanes are NOT risk rankings."""
    later = later_owner_ids(index_text)
    need(isinstance(register, dict) and
         register.get("schemaVersion") == "iris-m12-owner-readiness-v0.1" and
         register.get("status") == "UNADOPTED_NOT_FROZEN_OWNER_DECISIONS_PENDING" and
         register.get("selectedTopology") == "NONE" and
         register.get("publicOrExecutablePort") == "NONE" and
         register.get("implementationStatus") == "NOT_ADMITTED",
         "M12 source register promoted or unsupported")
    need(register.get("workOrder") == "IRIS-WO-0028" and register.get("issue") == 128,
         "wrong M12 source Work Order")
    need(isinstance(register.get("unresolvedHardDependencies"), list) and
         len(register["unresolvedHardDependencies"]) == len(REQUIRED_DEPENDENCIES) and
         set(register["unresolvedHardDependencies"]) == REQUIRED_DEPENDENCIES,
         "M12 unresolved hard dependency disappeared or duplicated")
    need(isinstance(c02, dict) and c02.get("issue110OwnerDecision") == "NOT_RECORDED" and
         c02.get("noSelectedTopology") is True,
         "M09 #110 actual decision requires a new source-locked review")
    highs = c02.get("futureFreezeBlockers")
    need(isinstance(highs, list) and len(highs) == 4 and
         [x.get("id") for x in highs] ==
         [f"C02-FR-H{i:02d}" for i in range(1, 5)] and
         all(x.get("severity") == "HIGH_FOR_FUTURE_FREEZE" and
             isinstance(x.get("status"), str) and x["status"].startswith("OPEN_")
             for x in highs), "C02 H01-H04 must remain open HIGH blockers")
    questions = register.get("questions")
    negatives = register.get("negativeScenarios")
    need(isinstance(questions, list) and len(questions) == 110 and
         isinstance(negatives, list) and len(negatives) == 80,
         "110 unresolved questions and 80 unexecuted future oracles required")

    qroutes: list[dict] = []
    by_lane: dict[str, list[str]] = {name: [] for name in LANES}
    by_owner: dict[str, list[str]] = {}
    by_session: dict[str, dict] = {}
    by_negative: dict[str, dict] = {}
    explicit_110: list[str] = []
    for sess, negative_prefix, qcount, ncount, source in SESSION_SPECS:
        source_q = [q for q in questions if isinstance(q, dict) and
                    q.get("session") == sess]
        source_n = [n for n in negatives if isinstance(n, dict) and
                    n.get("session") == sess]
        need([q.get("id") for q in source_q] ==
             [f"M12-{sess}-U{i:02d}" for i in range(1, qcount + 1)],
             f"{sess} original question IDs missing/duplicate/reordered")
        need([n.get("id") for n in source_n] ==
             [f"{negative_prefix}-{i:02d}" for i in range(1, ncount + 1)],
             f"{sess} original future-case IDs missing/duplicate/reordered")
        for n in source_n:
            need(n.get("status") == "SPECIFIED_NOT_EXECUTED" and
                 n.get("source") == source and
                 all(isinstance(n.get(k), str) and n[k].strip()
                     for k in ("trigger", "safetyOracle", "owners")),
                 "future oracle source or non-execution marker altered")
        by_negative[sess] = dict(
            count=len(source_n), ids=[n["id"] for n in source_n],
            status="SPECIFIED_NOT_EXECUTED", source=source,
        )
        local_lane = {name: 0 for name in LANES}
        for q in source_q:
            need(q.get("status") == "OPEN_UNRATED_PENDING_OWNER" and
                 q.get("source") == source and
                 isinstance(q.get("question"), str) and q["question"].strip(),
                 "M12 original question falsely approved, rerouted or blank")
            owners, has110 = parse_owner_label(q.get("owners"), later)
            frozen = [x for x in owners if x in FROZEN_INPUTS]
            proposed = [x for x in owners if x in PROPOSED_CANDIDATES]
            indexed = [x for x in owners if x in later]
            if has110:
                lane = LANES[0]
                explicit_110.append(q["id"])
            elif indexed:
                lane = LANES[1]
            elif "M11" in owners:
                lane = LANES[2]
            elif "M12" not in owners:
                lane = LANES[3]
            else:
                lane = LANES[4]
            by_lane[lane].append(q["id"])
            local_lane[lane] += 1
            for owner in owners:
                by_owner.setdefault(owner, []).append(q["id"])
            qroutes.append(dict(
                id=q["id"], session=sess, source=q["source"], question=q["question"],
                exactOwnerLabel=q["owners"], ownerIds=owners,
                explicitIssue110=has110, frozenOwnerInputs=frozen,
                pendingCandidateOwners=proposed, laterIndexOnlyOwners=indexed,
                intakeLane=lane, ownerDecisionStatus="OPEN_UNRATED_PENDING_OWNER",
                risk="UNRATED", executableAuthority="NONE",
            ))
        by_session[sess] = dict(
            questionCount=qcount, questionIds=[q["id"] for q in source_q],
            negativeCount=ncount, byLane=local_lane,
        )
    need([q.get("id") for q in questions] == [q["id"] for q in qroutes],
         "original M12 session order changed")
    need([n.get("id") for n in negatives] ==
         [id for sess, _, _, _, _ in SESSION_SPECS for id in by_negative[sess]["ids"]],
         "original M12 future-case session order changed")
    return dict(
        schemaVersion="iris-m12-owner-intake-c02",
        workOrder="IRIS-WO-0031", sourceWorkOrder="IRIS-WO-0028", issue=128,
        sourceBaseSha=BASE_SHA, sourceBaseTreeSha=BASE_TREE_SHA,
        sourceRegisterPath=REGISTER, sourceC02Path=C02, sourceIndexPath=INDEX,
        status="ROUTING_ONLY_ALL_OWNER_DECISIONS_PENDING",
        ownerApproval="NONE_RECORDED", selectedTopology="NONE",
        publicOrExecutablePort="NONE", implementationStatus="NOT_ADMITTED",
        questionStatus="OPEN_UNRATED_PENDING_OWNER",
        futureNegativeStatus="SPECIFIED_NOT_EXECUTED",
        priorityOrOwnerChoice="NOT_ASSIGNED_BY_ROUTING",
        ownerSourceTiers=dict(
            frozenInputs=list(FROZEN_INPUTS),
            proposedUnfrozenCandidates=list(PROPOSED_CANDIDATES),
            futureIndexOnlyOwners=list(later),
            warning="A frozen source is not an adopted cross-owner grant; a review lane never selects a policy.",
        ),
        counts=dict(
            sessions=5, questions=110, futureNegativeScenarios=80,
            uniqueOwnerTokens=len(by_owner), explicitIssue110=len(explicit_110),
            byLane={name: len(by_lane[name]) for name in LANES},
        ),
        explicitIssue110QuestionIds=explicit_110,
        reviewLanes={name: by_lane[name] for name in LANES},
        ownerQueues={name: by_owner[name] for name in sorted(by_owner)},
        sessions=by_session, futureNegatives=by_negative, questions=qroutes,
        unresolvedHighs=[dict(id=x["id"], severity=x["severity"], status=x["status"])
                         for x in highs],
        unresolvedHardDependencies=list(register["unresolvedHardDependencies"]),
    )


def verify_routing(root: Path = ROOT) -> dict[str, int]:
    """Check entire canonical source evidence before verifying this exact derived copy."""
    verify_m12_source_evidence(root)
    def load(path: str) -> dict:
        obj = json.loads((root / path).read_text(encoding="utf-8"),
                         object_pairs_hook=unique_json)
        need(isinstance(obj, dict), f"{path} must contain a JSON object")
        return obj
    expected = build_routing(
        load(REGISTER), load(C02), (root / INDEX).read_text(encoding="utf-8"))
    actual = load(ROUTING)
    need(actual == expected,
         "M12 C02 intake matrix changed or is stale relative to exact source register")
    return dict(questions=110, negative=80, issue110=5, byLane=expected["counts"]["byLane"])


if __name__ == "__main__":
    try:
        counts = verify_routing()
    except (IntakeRoutingError, M12EvidenceError, OSError, UnicodeError, ValueError) as exc:
        raise SystemExit(f"M12 owner intake: FAIL: {exc}") from exc
    print("M12 owner intake: PASS " + json.dumps(counts, sort_keys=True) +
          "; all owner decisions pending, no runtime or freeze admitted")
