"""M12 C03 source-constrained 19-question discussion verifier.

Only documentary source integrity and nonpromotion are checked. No source
reference, passing test or suggested statement is actual owner approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.verify_m12_owner_intake import (
    ROOT, ROUTING, REGISTER, C02, verify_routing, IntakeRoutingError,
)
from scripts.verify_m12_planning_evidence import unique_json, M12EvidenceError

PACKET = ".engineering/evidence/M12-C03-SOURCE-OWNER-PACKETS.json"
REPORT = "planning/reviews/M12-C03-SOURCE-OWNER-PACKETS.md"
BASE = "1856e91eac15deeb6ba553dcfbdc24b8651de0a1"
TREE = "66f946a2c8ae8b36f5b0ed34c9ace9dbf5e5ddc3"
LANE = "M12_PROPOSABLE_WITH_FROZEN_SOURCE_INPUTS"
ROLES = {
    "M02": ("planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
            "semantic object ID != content/revision ID != attempt ID;"),
    "M06": ("planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
            "M02 semantic identity != M02 revision/snapshot != M06 operational revision"),
    "M09": ("docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md",
            "Composite claims, grants and transfers report atomicity and per-member outcomes."),
    "M10": ("planning/contracts/M10-MODULE-CONTRACT-FREEZE-CANDIDATE.md",
            "A recommendation SHALL NOT imply reservation, placement, dispatch, worker control, provider submission or authorization."),
    "C01": ("planning/contracts/M09-READ-ONLY-EVIDENCE-HANDOFF-CANDIDATE.md",
            "Status: **PROPOSED_UNADOPTED_NOT_FROZEN**"),
}
HIGHS = frozenset(f"C02-FR-H{i:02d}" for i in range(1, 5))
EXPECTED = (
    ("M12-S01-U13", ("WR-09",), ("C02-FR-H02",)),
    ("M12-S01-U15", ("WR-10",), ("C02-FR-H04",)),
    ("M12-S01-U17", ("WR-11",), ()),
    ("M12-S02-U01", ("SQ-01",), ("C02-FR-H04",)),
    ("M12-S02-U04", ("SQ-06",), ()),
    ("M12-S02-U07", ("SQ-05",), ("C02-FR-H02",)),
    ("M12-S02-U09", ("SQ-02", "SQ-03"), ("C02-FR-H02",)),
    ("M12-S02-U13", ("SQ-14",), ()),
    ("M12-S02-U17", ("SQ-08", "SQ-09"), ("C02-FR-H04",)),
    ("M12-S02-U20", ("SQ-11",), ()),
    ("M12-S03-U01", ("MG-01",), ("C02-FR-H02",)),
    ("M12-S03-U03", ("MG-02", "MG-03"), ("C02-FR-H02",)),
    ("M12-S03-U12", ("MG-11",), ("C02-FR-H02", "C02-FR-H03")),
    ("M12-S03-U14", ("MG-08", "MG-13"), ("C02-FR-H04",)),
    ("M12-S03-U18", ("MG-16",), ("C02-FR-H02",)),
    ("M12-S03-U21", ("MG-13",), ("C02-FR-H04",)),
    ("M12-S05-U07", ("FT-04", "FT-19"), ("C02-FR-H04",)),
    ("M12-S05-U08", ("FT-04",), ("C02-FR-H04",)),
    ("M12-S05-U18", ("FT-13", "FT-02"), ("C02-FR-H02",)),
)


class DiscussionEvidenceError(ValueError):
    """Source evidence does not justify the claimed documentary packet state."""


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise DiscussionEvidenceError(reason)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()


def read_json(root: Path, path: str) -> dict:
    obj = json.loads((root / path).read_text(encoding="utf-8"),
                     object_pairs_hook=unique_json)
    need(isinstance(obj, dict), f"{path} not a JSON object")
    return obj


def render_report(rows: list[dict]) -> str:
    doc = [
        "# M12 C03: 19 source-constrained owner discussion packets", "",
        "Status: **NONBINDING_SOURCE_DISCUSSION_ONLY** | IRIS-WO-0032 | Issue #128 OPEN.",
        "",
        "The 19 source-derived M12-proposable original questions remain OPEN/UNRATED. This report adds source-anchored discussion proposals and specific unresolved proof gaps, and cross-references existing future negative oracles without claiming execution. Existing frozen contracts constrain interpretation, **not** M12 cross-owner acceptance. The other 91 original questions and all 80 NOT_EXECUTED future cases remain untouched. Neither a priority ranking nor an owner decision is derived.",
        "",
    ]
    for p in rows:
        doc.extend([
            f'## {p["id"]} | {p["originalOwners"]}',
            "",
            f'**Original question:** {p["originalQuestion"]}', "",
            f'**Nonbinding discussion:** {p["proposal"]}', "",
            f'**Owner proof still missing:** {p["gap"]}', "",
            "**Pinned owner-source anchors:** " + "; ".join(
                f'\x60{a["sourceRole"]}\x60 [{a["path"]}](../../{a["path"]}) '
                f'(\x60{a["exactNeedle"]}\x60)' for a in p["anchors"]) + ".",
            "",
            "**Existing future negative test designs, all NOT_EXECUTED:** " +
            ", ".join(p["existingFutureOracleIds"]) +
            ". Inherited blocker references: " +
            (", ".join(p["linkedInheritedHighs"]) if p["linkedInheritedHighs"]
             else "none per-item; all four remain open globally") + ".",
            "",
        ])
    doc.extend([
        "## Exact freeze STOP", "",
        "M09 #110 A/B/C/limited stages/DEFER **NONE_SELECTED**; C02 H01–H04 **OPEN HIGH_FOR_FUTURE_FREEZE**; M09 C01 **UNADOPTED**; M11 v0.2 **NOT_FROZEN** (86 OPEN); M12 v0.1 **PREPARED_FOR_OWNER_REVIEW_ONLY/NOT_FROZEN** (110 OPEN, 80 future cases NOT_EXECUTED); M10/M11/M12 runtime **NOT_ADMITTED**. No claimed actual owner signoff, technology selection, OS/GPU/network/cloud execution, grant or runtime test. Any source or owner change requires a new exact Git lock, qualified review and separately admitted Work Order.",
        "",
    ])
    return "\n".join(doc)


def verify_packet(packet: dict, route: dict, reg: dict, c02: dict,
                  root: Path = ROOT, *, verify_markdown: bool = True) -> dict:
    """Evidence-check source-constrained statements, never certify their truth."""
    need(packet.get("schemaVersion") == "iris-m12-c03-source-constrained-discussion-v0.1"
         and packet.get("workOrder") == "IRIS-WO-0032"
         and packet.get("issue") == 128
         and packet.get("sourceBaseSha") == BASE
         and packet.get("sourceBaseTreeSha") == TREE
         and packet.get("sourceRegister") == REGISTER
         and packet.get("sourceRouting") == ROUTING
         and packet.get("sourceC02") == C02
         and packet.get("status") == "NINETEEN_NONBINDING_PROPOSALS_OWNER_REVIEW_PENDING"
         and packet.get("counts") == dict(originalQuestionsOpen=110,
                                         nonbindingPackets=19,
                                         otherOriginalQuestionsOpen=91,
                                         futureOriginalOraclesNotExecuted=80)
         and packet.get("selectedM09Topology") == "NONE_SELECTED"
         and packet.get("ownerApprovals") == 0
         and packet.get("openHighs") ==
         [f"C02-FR-H{i:02d}" for i in range(1, 5)]
         and packet.get("m11") == "V0_2_NOT_FROZEN_86_OPEN"
         and packet.get("m12") == "V0_1_PREPARED_FOR_OWNER_REVIEW_ONLY_110_OPEN"
         and packet.get("runtime") == "M10_M11_M12_NOT_ADMITTED"
         and isinstance(packet.get("stop"), str) and len(packet["stop"]) > 70,
         "C03 top-level status, scope or explicit STOP forged")

    need(c02.get("issue110OwnerDecision") == "NOT_RECORDED"
         and c02.get("noSelectedTopology") is True
         and [x.get("id") for x in c02.get("futureFreezeBlockers", [])] ==
         [f"C02-FR-H{i:02d}" for i in range(1, 5)]
         and all(x.get("severity") == "HIGH_FOR_FUTURE_FREEZE"
                 and str(x.get("status", "")).startswith("OPEN_")
                 for x in c02["futureFreezeBlockers"]),
         "original H01-H04 or issue #110 owner state changed")

    expected_doc_rows = []
    docs = packet.get("sourceDocs")
    need(isinstance(docs, list) and len(docs) == len(ROLES),
         "source document count changed")
    sha_by_role: dict[str, str] = {}
    for (name, (path, anchor)), record in zip(ROLES.items(), docs):
        data = (root / path).read_bytes()
        sha = git_blob_sha(data)
        need(record == dict(role=name, path=path, gitBlobSha1=sha, exactNeedle=anchor)
             and anchor in data.decode("utf-8"),
             f"original frozen/candidate source anchor drift: {name}")
        sha_by_role[name] = sha
    route_rows = [q for q in route["questions"] if q["intakeLane"] == LANE]
    need([q["id"] for q in route_rows] == [q[0] for q in EXPECTED],
         "C02 original 19-question lane changed")
    all_reg = {q["id"]: q for q in reg["questions"]}
    all_negative = {q["id"]: q for q in reg["negativeScenarios"]}
    need(len(reg["questions"]) == 110
         and len(reg["negativeScenarios"]) == 80
         and all(q["status"] == "OPEN_UNRATED_PENDING_OWNER" for q in reg["questions"])
         and all(n["status"] == "SPECIFIED_NOT_EXECUTED" for n in reg["negativeScenarios"]),
         "original owner register or future test disposition promoted")

    records = packet.get("proposals")
    need(isinstance(records, list) and len(records) == 19,
         "C03 must include exactly 19 original question packets")
    for (id, oracle_ids, high_ids), q, p in zip(EXPECTED, route_rows, records):
        need(q["id"] == id
             and p.get("id") == id and p.get("session") == q["session"]
             and p.get("originalQuestion") == q["question"]
             and p.get("originalOwners") == q["exactOwnerLabel"]
             and p.get("canonicalResearchSource") == q["source"]
             and all_reg[id]["question"] == p["originalQuestion"]
             and all_reg[id]["owners"] == p["originalOwners"]
             and p.get("candidateStatus") == "NONBINDING_SOURCE_CONSTRAINED_DISCUSSION"
             and p.get("ownerDecisionStatus") == "OPEN_UNRATED_PENDING_OWNER"
             and p.get("risk") == "UNRATED"
             and p.get("ownerApproval") == "NONE"
             and p.get("executableAuthority") == "NONE"
             and isinstance(p.get("proposal"), str) and len(p["proposal"]) >= 80
             and isinstance(p.get("gap"), str) and len(p["gap"]) >= 65
             and p.get("existingFutureOracleIds") == list(oracle_ids)
             and p.get("linkedInheritedHighs") == list(high_ids)
             and p.get("oraclesStatus") == "SPECIFIED_NOT_EXECUTED",
             f"C03 original question, open status, original oracle or proof gap drift: {id}")
        need(all(oracle in all_negative and all_negative[oracle]["session"] == q["session"]
                 for oracle in oracle_ids),
             f"future test reused from different session or unknown: {id}")
        expected_roles = [owner for owner in q["ownerIds"] if owner in ROLES]
        if "M09" in expected_roles and "C02-FR-H02" in high_ids:
            expected_roles.append("C01")
        need(p.get("anchors") == [
            dict(sourceRole=role, path=ROLES[role][0],
                 gitBlobSha1=sha_by_role[role], exactNeedle=ROLES[role][1])
            for role in expected_roles
        ], f"owner anchor missing/foreign/changed: {id}")
        expected_doc_rows.append(p)

    if verify_markdown:
        need((root / REPORT).read_text(encoding="utf-8") ==
             render_report(expected_doc_rows),
             "human owner discussion report is stale or differs from exact C03 packet")
    return dict(questionsOpen=110, discussionPackets=19, futureOraclesNotExecuted=80,
                distinctReferencedOriginalOracles=len({
                    x for row in records for x in row["existingFutureOracleIds"]
                }), ownerApprovals=0, inheritedHighsOpen=4)


def verify_all(root: Path = ROOT) -> dict:
    verify_routing(root)
    return verify_packet(read_json(root, PACKET), read_json(root, ROUTING),
                         read_json(root, REGISTER), read_json(root, C02), root)


if __name__ == "__main__":
    try:
        print("M12 C03 source-only packets: PASS " +
              json.dumps(verify_all(), sort_keys=True) +
              "; owner decision NONE, runtime NOT_ADMITTED")
    except (DiscussionEvidenceError, IntakeRoutingError, M12EvidenceError,
            OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit(f"M12 C03 source-only packets: FAIL: {exc}") from exc
