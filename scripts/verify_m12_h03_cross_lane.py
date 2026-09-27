"""WO0044: verify ALL original M12 questions across disjoint H03/C03 routes.

Source-only integrity proof. A correctly accounted original question remains
OPEN; this never authenticates an owner, signs a cross-owner contract, performs
future negative tests, grants permissions, freezes C01 or admits runtime.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.verify_m12_owner_intake import (
    ROOT, ROUTING, REGISTER,
)
from scripts.verify_m12_c03_discussion import (
    PACKET as C03, read_json, verify_all as verify_c03,
)
from scripts.verify_m09_h03_owner_routes import (
    PRIOR as H03, verify_all as verify_h03_routes,
)


H03_OWNERS = ("M12", "M54", "M58", "M60")
ORIGINAL_COUNTS = (72, 39, 9, 27)
OUTSIDE_LANES = {
    "EXPLICIT_ISSUE_110_REVIEW": 4,
    "M11_CANDIDATE_CROSS_OWNER_REVIEW": 5,
    "FROZEN_OWNER_HANDOFF_REVIEW": 3,
    "LATER_OWNER_CONTRACT_REQUIRED": 7,
}
C03_LANE = "M12_PROPOSABLE_WITH_FROZEN_SOURCE_INPUTS"
SHARED_OWNERS = {
    frozenset(("M54", "M60")): 9,
    frozenset(("M12", "M54", "M60")): 7,
    frozenset(("M54", "M58", "M60")): 2,
}
ISSUE_110_H03_MEMBER = "M12-S02-U08"


class CrossLaneIntegrityError(ValueError):
    """Two valid-looking source packets cannot hide or promote original IDs."""


def guard(value: bool, reason: str) -> None:
    if not value:
        raise CrossLaneIntegrityError(reason)


def audit_cross_lane(intake: dict, register: dict, c03: dict, h03: dict) -> dict:
    """Pure cross-source proof; verify_all pins each source before calling it."""
    guard(all(type(v) is dict for v in (intake, register, c03, h03)),
          "all historical source registers must be objects")
    rows = register.get("questions")
    intake_rows = intake.get("questions")
    guard(isinstance(rows, list) and isinstance(intake_rows, list)
          and len(rows) == len(intake_rows) == 110,
          "original 110-question register or intake count drift")
    ids = [x["id"] for x in rows]
    guard(len(set(ids)) == 110
          and ids == [x["id"] for x in intake_rows],
          "original 110-question identity missing, duplicate or reordered")
    by_id = dict(zip(ids, intake_rows))
    for original, routed in zip(rows, intake_rows):
        guard(original["question"] == routed["question"]
              and original["source"] == routed["source"]
              and original["owners"] == routed["exactOwnerLabel"]
              and original["session"] == routed["session"]
              and original["status"] == routed["ownerDecisionStatus"]
                  == "OPEN_UNRATED_PENDING_OWNER"
              and routed["risk"] == "UNRATED"
              and routed["executableAuthority"] == "NONE",
              "original M12 question or OPEN/no-authority state changed")
    negatives = register.get("negativeScenarios")
    guard(isinstance(negatives, list) and len(negatives) == 80
          and all(x["status"] == "SPECIFIED_NOT_EXECUTED" for x in negatives),
          "original 80 M12 future negative cases unexpectedly executed")
    guard(intake.get("status") == "ROUTING_ONLY_ALL_OWNER_DECISIONS_PENDING"
          and intake.get("ownerApproval") == "NONE_RECORDED"
          and intake.get("selectedTopology") == "NONE"
          and intake.get("implementationStatus") == "NOT_ADMITTED"
          and c03.get("selectedM09Topology") == "NONE_SELECTED"
          and c03.get("ownerApprovals") == 0
          and c03.get("runtime") == "M10_M11_M12_NOT_ADMITTED"
          and h03.get("ownerSelectedTopologyDirection")
              == "B_FUTURE_OWNER_RECEIPT_DOCUMENTARY_ONLY"
          and h03.get("H03status") == "OPEN_FUTURE_OWNER_CONTRACTS"
          and h03.get("H03severity") == "HIGH_FOR_FUTURE_FREEZE"
          and h03.get("crossOwnerApproval") == "NONE_INFERRED"
          and h03.get("newH03FutureCaseStatus") == "SPECIFIED_NOT_EXECUTED"
          and len(h03.get("newH03FutureNegatives", [])) == 12
          and all(x["status"] == "SPECIFIED_NOT_EXECUTED"
                  for x in h03["newH03FutureNegatives"])
          and all(str(x).startswith("OPEN_")
                  for x in h03.get("fourHighStatuses", []))
          and len(h03.get("fourHighStatuses", [])) == 4,
          "historical/current owner direction or H01-H04 nonadmission drift")

    owners = h03.get("sourceOwners")
    guard(isinstance(owners, list)
          and [x["module"] for x in owners] == list(H03_OWNERS)
          and [x["questionCount"] for x in owners] == list(ORIGINAL_COUNTS),
          "H03 four-owner identity/assignment-count drift")
    owner_sets: dict[str, set[str]] = {}
    by_question: dict[str, set[str]] = {}
    total = 0
    for packet in owners:
        name = packet["module"]
        questions = packet["questions"]
        routed_ids = intake["ownerQueues"][name]
        question_ids = [q["id"] for q in questions]
        guard(question_ids == routed_ids
              and len(question_ids) == len(set(question_ids))
              and packet["actualSignedOwnerContract"] is False
              and packet["publicOrExecutablePort"] is False
              and packet["assumedPermissions"] is False,
              f"{name} H03 original route changed or claimed owner permission")
        owner_sets[name] = set(question_ids)
        total += len(question_ids)
        for question in questions:
            qid = question["id"]
            guard(qid in by_id and
                  all(question[name] == by_id[qid][route_name]
                      for name, route_name in (
                          ("originalQuestion", "question"),
                          ("source", "source"),
                          ("exactOwnerLabel", "exactOwnerLabel"),
                          ("originalIntakeLane", "intakeLane"),
                          ("ownerDecisionStatus", "ownerDecisionStatus"),
                      )) and question["risk"] == "UNRATED"
                  and question["executableAuthority"] == "NONE",
                  "H03 source-question ID/text/owner/source/lane or authority drift")
            by_question.setdefault(qid, set()).add(name)
    inside = set(by_question)
    outside = set(ids) - inside
    guard(total == 147 and len(inside) == 91 and len(outside) == 19
          and total == h03["overlappingQuestionAssignments"]
          and len(inside) == h03["uniqueQuestionsAcrossFourOwners"]
          and not inside.intersection(outside)
          and inside.union(outside) == set(ids),
          "H03 147 assignments/91 unique plus complement 19 no longer partition 110")

    outside_counts = {
        lane: sum(by_id[qid]["intakeLane"] == lane for qid in outside)
        for lane in OUTSIDE_LANES
    }
    guard(outside_counts == OUTSIDE_LANES
          and all(by_id[qid]["intakeLane"] in OUTSIDE_LANES
                  for qid in outside),
          "M12 19 H03-outside IDs no longer split into original 4/5/3/7 lanes")

    proposal_rows = c03.get("proposals")
    guard(isinstance(proposal_rows, list)
          and len(proposal_rows) == 19
          and c03.get("status") ==
              "NINETEEN_NONBINDING_PROPOSALS_OWNER_REVIEW_PENDING",
          "C03 19 historical nonbinding proposals missing or promoted")
    proposals = [row["id"] for row in proposal_rows]
    expected_proposals = [
        row["id"] for row in intake_rows if row["intakeLane"] == C03_LANE]
    guard(len(set(proposals)) == 19
          and proposals == expected_proposals
          and set(proposals).issubset(inside)
          and set(proposals).isdisjoint(outside),
          "C03 19 proposals wrongly equated with distinct H03 complement 19")
    for row in proposal_rows:
        original = by_id[row["id"]]
        guard(row["originalQuestion"] == original["question"]
              and row["originalOwners"] == original["exactOwnerLabel"]
              and row["canonicalResearchSource"] == original["source"]
              and row["ownerDecisionStatus"] == "OPEN_UNRATED_PENDING_OWNER"
              and row["ownerApproval"] == "NONE"
              and row["risk"] == "UNRATED"
              and row["executableAuthority"] == "NONE"
              and row["candidateStatus"] == "NONBINDING_SOURCE_CONSTRAINED_DISCUSSION"
              and row["oraclesStatus"] == "SPECIFIED_NOT_EXECUTED",
              "C03 discussion misrepresented an original question or real proof")

    explicit = intake.get("explicitIssue110QuestionIds")
    guard(isinstance(explicit, list) and len(explicit) == 5
          and len(set(explicit)) == 5
          and all(by_id[qid]["intakeLane"] == "EXPLICIT_ISSUE_110_REVIEW"
                  for qid in explicit)
          and set(explicit).intersection(inside) == {ISSUE_110_H03_MEMBER}
          and len(set(explicit).intersection(outside)) == 4,
          "#110 five original questions: four outside H03 and one inside M12")
    guard(ISSUE_110_H03_MEMBER in owner_sets["M12"],
          "fifth issue #110 question must remain in M12 H03 original owner route")

    shared = {qid: members for qid, members in by_question.items()
              if {"M54", "M60"}.issubset(members)}
    grouped = {
        owners: sum(members == owners for members in shared.values())
        for owners in SHARED_OWNERS
    }
    guard(len(shared) == 18
          and grouped == SHARED_OWNERS
          and sum(grouped.values()) == len(shared),
          "M54/M60 18 shared IDs / 9+7+2 independent co-owner lanes drift")

    return {
        "status": "SOURCE_ONLY_CROSS_LANE_INTEGRITY_NO_OWNER_APPROVAL",
        "originalM12QuestionsStillOpen": 110,
        "h03OriginalAssignments": total,
        "h03UniqueOriginalQuestions": len(inside),
        "h03OutsideOriginalQuestions": len(outside),
        "h03OutsideLaneCounts": outside_counts,
        "independentC03NonbindingProposals": len(proposals),
        "c03DisjointFromH03Complement": True,
        "issue110OriginalQuestions": len(explicit),
        "issue110FourOutsideOneInside": True,
        "sharedM54M60Questions": len(shared),
        "sharedOwnerGroups": {
            "+".join(sorted(names)): count for names, count in grouped.items()
        },
        "originalFutureM12NegativesNotExecuted": len(negatives),
        "newH03NegativesNotExecuted": len(h03["newH03FutureNegatives"]),
        "realOwnerApprovals": 0,
        "realFutureNegativeTestsExecuted": False,
        "h01h02h03h04": "ALL_OPEN_HIGH_FOR_FUTURE_FREEZE",
        "m10m11m12Runtime": "NOT_ADMITTED",
    }


def verify_all(root: Path = ROOT) -> dict:
    # Both historical packets must independently pass their EXISTING exact
    # original source/route/semantic verifiers before joint cross-lane audit.
    verify_c03(root)
    verify_h03_routes(root)
    return audit_cross_lane(
        read_json(root, ROUTING), read_json(root, REGISTER),
        read_json(root, C03), read_json(root, H03),
    )


if __name__ == "__main__":
    try:
        print("IRIS M12↔H03 cross-lane documentary integrity PASS: " +
              json.dumps(verify_all(), sort_keys=True) +
              " | NO owner decision, no freeze, no runtime")
    except (ValueError, KeyError, TypeError, OSError, UnicodeError) as error:
        raise SystemExit("IRIS M12↔H03 cross-lane integrity FAIL: " +
                         str(error)) from error
