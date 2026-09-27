"""WO0047 M13 S03 source-only research, not a cache engine or reuse admission."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M13-S03-DELTA-REUSE-RESEARCH.json"
REPORT = "planning/research/M13-S03-INTERMEDIATE-REUSE-GENERATION-DELTA.md"
BASE = "63baffa4183149eb7476af6787b51e8a021c7d45"
BASE_TREE = "c8c0feaaf99e09e802a4789ef97aa854f251264c"
SOURCES = [{"role":"INDEX","path":"planning/MASTER-MODULE-INDEX.md","sha":"19c8ff6126748cb89e53108bdff8289322071970","anchor":"S03 — S03 Intermediate reuse and generation delta cache"},{"role":"M02","path":"planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"a85d80ab3bb5f4bdc9be915a59caa92569d66af4","anchor":"semantic reuse requires explicit reuse class/admission"},{"role":"M04","path":"planning/contracts/M04-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"c4b39c03f86f7a8e112d22a25ca91169c02c5e4d","anchor":"IRStructuralFingerprint"},{"role":"M05","path":"planning/contracts/M05-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"97e8ed228b29c47911e3d3a0ed10ade91f76d723","anchor":"M53 rights/license/consent/provenance authority"},{"role":"M06","path":"planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md","sha":"18b5303d1e36ef60de17b42dd9e2c371ecf4f191","anchor":"Digest equality proves byte equality under the declared digest domain only."},{"role":"M02_RESEARCH","path":"planning/research/M02-S04-INCREMENTAL-BUILD-RESEARCH-2026-09-20.md","sha":"1e3979dfb258eb6bb4a96d56b85b003eebe1e98a","anchor":"based on causal correctness and reuse-class admission"},{"role":"S01","path":".engineering/evidence/M13-S01-SOURCE-RESEARCH.json","sha":"ee65b960ca7e4f83f5419ec744f4c1f304edb6d7","anchor":"C05_INTERMEDIATE_AND_DELTA_REUSE"},{"role":"S02","path":".engineering/evidence/M13-S02-BACKEND-ATTENTION-RESEARCH.json","sha":"2e94983865cf72aa6c5a63510b8a4b41586048c7","anchor":"SOURCE_ONLY_UNSELECTED_NONBINDING"},{"role":"M01","path":"docs/M01-QUALITY-KERNEL.md","sha":"930af57944fa83c44745873c42eb3a7740972ee6","anchor":"m01-contract-v1.0"},{"role":"M09","path":"docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md","sha":"d12b4f48030c1a57b8e6228df39f35dac8c2b20a","anchor":"M09 is the provider-neutral resource-state"},{"role":"D01","path":".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json","sha":"30cc56a2dd34a8c45cfb96f0a900cafbdd2717bb","anchor":"B_FUTURE_OWNER_RECEIPT"}]
CONCEPT_IDS = ["CONCEPT-01","CONCEPT-02","CONCEPT-03","CONCEPT-04","CONCEPT-05","CONCEPT-06","CONCEPT-07"]
STRATEGY_IDS = ["STRATEGY-01","STRATEGY-02","STRATEGY-03","STRATEGY-04","STRATEGY-05"]
AXIS_IDS = ["SEMANTIC_IDENTITY","OPERATIONAL_PROVENANCE","MULTIMODAL_SLICE","PROTECTED_DNA","COMPLETE_DEPENDENCIES","REPRODUCIBILITY","QUALITY_FRESHNESS","MODEL_TOOLCHAIN","CURRENT_RIGHTS_TRUST","PHYSICAL_STORAGE","EMPIRICAL_VALUE","EXECUTION_RESOURCES"]
QUESTION_ROUTES = [["M02/M06","M02"],["M02","M02"],["M06","M06"],["M04","M04"],["M05","M05"],["M02/M06","M06"],["M02/M06","M06"],["M04/M06","M04"],["M01","M01"],["M53/M54","INDEX"],["M55","M06"],["M05/M53","M05"],["M14/M16/M18","S01"],["M09/M11/M12","M09"],["M02/M06","M02"],["M06/M55","M06"],["M08/M56","M02_RESEARCH"],["M02/M04/M06","M06"],["M53/M54/M55","INDEX"],["M04/M06/M55","M04"]]
NEGATIVE_CASES = [["HASH_NOT_SEMANTICS","NO_HASH_AS_SEMANTIC_REUSE"],["STALE_QUALITY","NO_OLD_QUALITY_AS_CURRENT_MASTER"],["HIDDEN_DEPENDENCY","NO_UNAFFECTED_PROOF_WITH_HIDDEN_INPUT"],["STOCHASTIC_DIVERGENCE","NO_DETERMINISM_BY_SEED"],["VIDEO_SEAM","NO_PARTIAL_BUILD_WITHOUT_SEAM_PROOF"],["AUDIO_SYNC","NO_UNVERIFIED_MULTIMODAL_SYNC"],["DNA_ANCHOR","NO_STALE_IDENTITY_PROJECTION"],["RIGHTS_REVOKED","NO_HISTORIC_PERMISSION_AS_CURRENT_AUTHORITY"],["CROSS_TENANT","NO_CROSS_TENANT_CACHE_ACCESS"],["KV_INCOMPATIBLE","NO_INCOMPATIBLE_PREFIX_REUSE"],["GPU_HINT_ONLY","NO_GRANT_FROM_RESIDENCY_HINT"],["OBJECT_DELETED","NO_AVAILABILITY_FROM_STALE_POINTER"],["GC_EPOCH","NO_DELETION_WITH_STALE_EPOCH"],["MOVING_ALIAS","NO_LATEST_ALIAS_AS_REVISION"],["MASTER_PROMOTION","NO_MASTER_PROMOTION_FROM_CACHE_HINT"],["MIXED_ANCESTRY","NO_INCOMPLETE_RECOMPOSITION"]]
ILLUSTRATIVE_GATES = (
    "sourceExactVersion", "m02OwnerReuseClass", "m06FreshDependencyProof",
    "m01CurrentQuality", "m53m54CurrentRights", "m55StorageAvailability",
)


class S03IntegrityError(ValueError):
    """A documentary source/permission claim is changed or loses provenance."""


def require(value: bool, why: str) -> None:
    if not value:
        raise S03IntegrityError(why)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def reject_duplicates(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON field: " + key)
        result[key] = value
    return result


def read_packet(root: Path = ROOT) -> dict:
    p = json.loads((root / PACKET).read_text(encoding="utf-8"),
                   object_pairs_hook=reject_duplicates)
    require(type(p) is dict, "S03 packet must be a JSON object")
    return p


def illustrate_synthetic_blockers(proposed: dict) -> dict:
    """Inert trust-boundary illustration. Even all-true claims DO NOT admit reuse.

    Input booleans are completely UNTRUSTED mock declarations, not receipts;
    this function never fetches data, reads storage, executes or grants access.
    """
    require(type(proposed) is dict and set(proposed) == set(ILLUSTRATIVE_GATES)
            and all(type(v) is bool for v in proposed.values()),
            "synthetic mock requires six exact literal boolean fields")
    return {
        "blockers": [key for key in ILLUSTRATIVE_GATES if not proposed[key]],
        "disposition": "REVIEW_REQUIRED_NO_REUSE_ADMISSION",
        "authenticatedOwnerProof": False,
        "runtimeAuthority": "NONE",
    }


def check_packet(p: dict, root: Path = ROOT, *,
                 verify_human: bool = False,
                 human_text: str | None = None) -> dict:
    require(type(p) is dict and set(p) == {
        "schema", "workOrder", "issue", "module", "session", "base",
        "baseTree", "status", "selectedReuseStrategy", "implementedCache",
        "actualOwnerApprovals", "empiricalResults", "runtime", "bDirection",
        "c01", "highs", "s01OriginalQuestions", "s01FutureCases",
        "s02OriginalQuestions", "s02FutureCases", "m12OriginalQuestions",
        "m12FutureCases", "sources", "reuseConcepts", "strategies",
        "qualificationAxes", "questions", "futureNegativeCases", "stop",
    }, "missing/extra S03 original source research schema field")
    require(
        p["schema"] == "iris-m13-s03-research-v0.1"
        and p["workOrder"] == "IRIS-WO-0047" and p["issue"] == 155
        and p["module"] == "M13" and p["session"] == "S03"
        and p["base"] == BASE and p["baseTree"] == BASE_TREE
        and p["status"] == "SOURCE_ONLY_NONBINDING"
        and p["selectedReuseStrategy"] == "NONE"
        and p["implementedCache"] == "NONE"
        and type(p["actualOwnerApprovals"]) is int
        and p["actualOwnerApprovals"] == 0
        and p["empiricalResults"] == "NONE"
        and p["runtime"] == "NOT_ADMITTED"
        and p["bDirection"] == "DIRECTION_ONLY"
        and p["c01"] == "UNADOPTED_NOT_FROZEN"
        and p["highs"] == "H01_H02_H03_H04_OPEN_HIGH_FOR_FUTURE_FREEZE"
        and p["s01OriginalQuestions"] == "18_OPEN_UNRATED"
        and p["s01FutureCases"] == "12_SPECIFIED_NOT_EXECUTED"
        and p["s02OriginalQuestions"] == "18_OPEN_UNRATED"
        and p["s02FutureCases"] == "14_SPECIFIED_NOT_EXECUTED"
        and p["m12OriginalQuestions"] == "110_OPEN_UNRATED"
        and p["m12FutureCases"] == "80_SPECIFIED_NOT_EXECUTED"
        and type(p["stop"]) is str
        and all(term in p["stop"] for term in (
            "H01-H04", "DIRECTION_ONLY", "UNADOPTED_NOT_FROZEN",
            "SPECIFIED_NOT_EXECUTED", "runtime")),
        "owner approval, historic B/C01/H01-H04/future status or runtime upgraded",
    )
    sources = p["sources"]
    require(type(sources) is list and sources == SOURCES
            and len(sources) == 11,
            "11 original source roles/blobs/anchors changed")
    for row in sources:
        raw = (root / row["path"]).read_bytes()
        require(git_blob(raw) == row["sha"]
                and row["anchor"] in raw.decode("utf-8"),
                "original Git blob/anchor drift: " + row["role"])
    master = (root / "planning/MASTER-MODULE-INDEX.md").read_text(encoding="utf-8")
    require(all(text in master for text in (
        "S01 — S01 Warm model/cache strategy and cache locality",
        "S02 — S02 Compilation, attention and backend selection",
        "S03 — S03 Intermediate reuse and generation delta cache",
        "S04 — S04 CPU/GPU overlap, I/O scheduling and storage efficiency",
    )), "M13 canonical original session plan changed")
    for file, qcount, negkey, ncount in (
        (".engineering/evidence/M13-S01-SOURCE-RESEARCH.json", 18,
         "negativeScenarios", 12),
        (".engineering/evidence/M13-S02-BACKEND-ATTENTION-RESEARCH.json", 18,
         "negativeCases", 14),
    ):
        previous = json.loads((root / file).read_text(encoding="utf-8"),
                              object_pairs_hook=reject_duplicates)
        require(len(previous["questions"]) == qcount
                and len(previous[negkey]) == ncount
                and all(x["status"] == "SPECIFIED_NOT_EXECUTED"
                        for x in previous[negkey]),
                "historic M13 S01/S02 original questions/future cases changed")
    concepts = p["reuseConcepts"]
    require(type(concepts) is list
            and [x.get("id") for x in concepts] == CONCEPT_IDS,
            "seven original source-only reuse concept identities lost")
    for row in concepts:
        require(set(row) == {"id", "name", "boundedHypothesis",
                             "failureBoundary", "ownerRoute", "status"}
                and row["status"] == "UNADOPTED_SOURCE_ONLY"
                and len(row["boundedHypothesis"]) >= 95
                and len(row["failureBoundary"]) >= 90
                and len(row["ownerRoute"]) >= 5,
                "original reuse class lacks owner proof or falsely adopted")
    alternatives = p["strategies"]
    require(type(alternatives) is list
            and [x.get("id") for x in alternatives] == STRATEGY_IDS,
            "five original unselected strategies lost")
    for row in alternatives:
        require(set(row) == {"id", "name", "hypothesis",
                             "selected", "executed", "status"}
                and row["selected"] is False
                and row["executed"] is False
                and row["status"] == "UNSELECTED_DISCUSSION_ONLY"
                and len(row["hypothesis"]) >= 75,
                "source-only strategy falsely selected or executed")
    axes = p["qualificationAxes"]
    require(type(axes) is list
            and [x.get("id") for x in axes] == AXIS_IDS,
            "twelve original owner-evidence dimensions lost")
    for row in axes:
        require(set(row) == {"id", "ownerRoute", "futureOwnerEvidence", "status"}
                and row["status"] == "REAL_OWNER_QUALIFICATION_PENDING"
                and len(row["futureOwnerEvidence"]) >= 95,
                "future evidence dimension falsely approved or shortened")
    qs = p["questions"]
    require(type(qs) is list and
            [x.get("id") for x in qs] ==
            [f"M13-S03-U{i:02d}" for i in range(1, 21)],
            "twenty new M13 S03 original question IDs missing or reordered")
    roles = {row["role"] for row in sources}
    for row, (owner, role) in zip(qs, QUESTION_ROUTES):
        require(set(row) == {
            "id", "ownerRoute", "question", "primarySourceRole", "status",
            "risk", "ownerAnswer", "executableAuthority",
        } and row["ownerRoute"] == owner
            and row["primarySourceRole"] == role
            and role in roles
            and type(row["question"]) is str
            and len(row["question"]) >= 95
            and row["status"] == "OPEN_UNRATED_PENDING_QUALIFIED_OWNER"
            and row["risk"] == "UNRATED"
            and row["ownerAnswer"] is None
            and row["executableAuthority"] == "NONE",
            "new S03 owner question falsely answered or original source changed")
    cases = p["futureNegativeCases"]
    require(type(cases) is list and
            [x.get("id") for x in cases] ==
            [f"DCS-{i:02d}" for i in range(1, 17)]
            and [[x["label"], x["futureNonAuthorizingOracle"]]
                 for x in cases] == NEGATIVE_CASES,
            "sixteen original future negative scenarios changed")
    for row in cases:
        require(set(row) == {"id", "label", "conceptIds", "trigger",
                             "futureNonAuthorizingOracle", "status"}
                and row["status"] == "SPECIFIED_NOT_EXECUTED"
                and type(row["conceptIds"]) is list
                and bool(row["conceptIds"])
                and len(row["conceptIds"]) == len(set(row["conceptIds"]))
                and set(row["conceptIds"]).issubset(set(CONCEPT_IDS))
                and len(row["trigger"]) >= 68,
                "new future scenario falsely executed or concept reference invalid")
    if verify_human:
        text = human_text if human_text is not None else (
            root / REPORT).read_text(encoding="utf-8")
        fence = chr(96) * 3
        marker = "\n## Appendix A: canonical machine packet\n\n" + fence + "json\n"
        require(text.count(marker) == 1 and text.endswith("\n" + fence + "\n"),
                "human report missing exactly one final machine appendix")
        visible, payload = text.split(marker)
        json_text, trailing = payload.split("\n" + fence + "\n", 1)
        require(trailing == "", "unexpected text after original machine appendix")
        require(json.loads(json_text, object_pairs_hook=reject_duplicates) == p,
                "human appendix differs from original machine packet")
        for obj in (*concepts, *alternatives, *axes, *qs, *cases):
            require(obj["id"] in visible, "missing human source item " + obj["id"])
        for row in qs:
            require(row["question"] in visible,
                    "human-facing original owner question modified/omitted")
        for row in sources:
            require(row["path"] in visible and row["sha"] in visible,
                    "human-facing source proof missing original immutable Git blob")
    return {
        "sourceOnly": True, "exactOriginalSourceBlobs": len(sources),
        "conceptsUnadopted": len(concepts), "strategiesUnselected": len(alternatives),
        "futureOwnerDimensions": len(axes),
        "newOpenS03Questions": len(qs),
        "futureNewNegativeDesignsNotExecuted": len(cases),
        "actualOwnerApprovals": 0, "runtime": "NOT_ADMITTED",
        "h01h02h03h04": "OPEN_HIGH_FOR_FUTURE_FREEZE",
    }


def verify_all(root: Path = ROOT) -> dict:
    return check_packet(read_packet(root), root, verify_human=True)


if __name__ == "__main__":
    try:
        print("M13 S03 SOURCE-ONLY PASS " +
              json.dumps(verify_all(), sort_keys=True) +
              " | NO owner reuse admission or runtime")
    except (S03IntegrityError, OSError, ValueError, KeyError, TypeError,
            UnicodeError, json.JSONDecodeError) as error:
        raise SystemExit("M13 S03 FAIL CLOSED: " + str(error)) from error
