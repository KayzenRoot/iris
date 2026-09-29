"""WO0076: reproducible M14 S01 source-only model identity research integrity."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ".engineering/evidence/M14-S01-SOURCE-RESEARCH.json"
REPORT = "planning/research/M14-S01-MODEL-IDENTITY-LICENSE-PROVENANCE.md"
BASE = "5d864f7a37f14f7daccdd385aa2cba1d77cece39"
TREE = "0556959bba5f7bb897901e875d8663956ea55681"
SOURCES = [
    ("INDEX", "planning/MASTER-MODULE-INDEX-CURRENT.md", "02e6394cc7e75d5466ab22801b4cc7dbe66500be", "### M14 — Model Registry & Empirical Model Cards"),
    ("FCS", "planning/reviews/M14-M60-FORWARD-COMPATIBILITY-SOURCE-SCAN.md", "5bac62b5b1a07fb97e43ea5c76d20dc5419c2cec", "### M14: Model Registry & Empirical Model Cards"),
    ("FTR", "planning/reviews/M13-FINAL-TECHNOLOGY-REVIEW-DOCUMENTARY.md", "a704684ece3cd28969e93eb2eb56d5efb995ad55", "96 NEW M13 open/UNRATED questions, 74 future real-world cases SPECIFIED_NOT_EXECUTED"),
    ("M02", "planning/contracts/M02-MODULE-CONTRACT-FREEZE-CANDIDATE.md", "a36fd73c03f06b7558f850a2ad515a0df37c243b", "cache/warm-state loss changes performance, not production truth;"),
    ("M06", "planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md", "d6778684e0c34e55d05ddc06cf5aa47fe347c037", "Digest equality proves byte equality under the declared digest domain only."),
    ("M08", "docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md", "461e0f332d9be2af694634bbdc8cf67e29d56393", "M08 records empirical performance evidence"),
    ("M09", "docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md", "d12b4f48030c1a57b8e6228df39f35dac8c2b20a", "M09 is the provider-neutral resource-state"),
    ("M13S01", ".engineering/evidence/M13-S01-SOURCE-RESEARCH.json", "5fe1b1ec36ce1e49a0810f553825c9d71b2af3e0", '"module": "M13"'),
    ("D01", ".engineering/evidence/M09-B-OWNER-DIRECTION-D01.json", "8877331a5004a3e816e4c42fb521ff3408bad08a", "B_FUTURE_OWNER_RECEIPT"),
]
COMPONENTS = (
    "COMP01_UPSTREAM_REPOSITORY_REVISION",
    "COMP02_WEIGHT_SHARDS_AND_INDEX",
    "COMP03_TOKENIZER_AND_PROCESSOR",
    "COMP04_ADAPTERS_AND_DEPENDENCIES",
    "COMP05_OPERATOR_CONFIG_AND_CUSTOM_CODE",
)
LICENSE_FACETS = (
    "RIGHTS01_WEIGHTS", "RIGHTS02_TOKENIZER_DATA",
    "RIGHTS03_ADAPTER_BASE", "RIGHTS04_EXECUTABLE_DEPENDENCIES",
    "RIGHTS05_OUTPUT_AND_PERSONA",
)
ALTERNATIVES = (
    "ALT01_UPSTREAM_LABEL_ONLY", "ALT02_PINNED_COMPOSITE_DIGEST",
    "ALT03_ISSUER_QUALIFIED_SBOM", "ALT04_OWNER_QUALIFIED_LOCAL_RECEIPT",
)
EXTERNAL_REFERENCES = (
    ("SPDX_LICENSE_EXPRESSIONS", "https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/"),
    ("HUGGINGFACE_MODEL_CARD_SCHEMA", "https://github.com/huggingface/hub-docs/blob/main/modelcard.md"),
    ("OCI_IMAGE_MANIFEST_REFERENCE", "https://specs.opencontainers.org/image-spec/manifest/"),
)
FIVE_SESSIONS = (
    "S01 — S01 Model identity, versions, hashes, license and provenance",
    "S02 — S02 Capability Genome and task taxonomy",
    "S03 — S03 Empirical quality/latency/VRAM model cards",
    "S04 — S04 Hardware compatibility and reliability evidence",
    "S05 — S05 Model drift, deprecation and lifecycle governance",
)

class M14S01IntegrityError(ValueError):
    """An immutable source or research-only authority fence was violated."""

def require(value: bool, message: str) -> None:
    if not value:
        raise M14S01IntegrityError(message)

def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def unique_json_keys(pairs: list[tuple[str, object]]) -> dict:
    out: dict = {}
    for key, value in pairs:
        require(key not in out, "duplicate JSON key: " + key)
        out[key] = value
    return out

def read_json(root: Path = ROOT) -> dict:
    item = json.loads((root / PACKET).read_text(encoding="utf-8"),
                      object_pairs_hook=unique_json_keys)
    require(type(item) is dict, "M14 S01 evidence packet must be a JSON object")
    return item

def render_report(p: dict) -> str:
    rows = [
        "# M14 S01 | Model Identity, Version, Hash, License & Provenance", "",
        "**SOURCE RESEARCH ONLY | IRIS-WO-0076 | issue #204 OPEN | NO owner adoption.**",
        "No model install, download, current usage rights, actual signature validation, empirical fitness, provider selection or executable M14 registry is admitted.", "",
        "## 1. Original source authority and precise S01 boundary", "",
        "M14 is INDEX_ONLY in the active standalone M00–M60 index. M13 documentary FTR/FCS is research, not M14 owner approval. An upstream card/alias/hash is an input claim, not a verified composite model package, legal entitlement, safe code, hardware benchmark or resource/process grant.", "",
        f'Original source main: {p["sourceBaseSha"]}; tree: {p["sourceBaseTreeSha"]}. Source roles and original SHA1 Git blobs:', "",
    ]
    for s in p["sourceDocs"]:
        rows.append(f'- **{s["role"]}** [{s["path"]}](../../{s["path"]}) original Git blob {s["gitBlobSha1"]}; exact anchor: {s["exactNeedle"]}.')
    rows.extend(["", "## 2. Five conceptual model-component identity classes, none adopted", ""])
    for x in p["componentClasses"]:
        rows.extend([f'### {x["id"]}: {x["title"]}', "",
                     f'- Evidence boundary: {x["boundary"]}',
                     f'- Original pending owners: {x["pendingOwners"]}',
                     f'- Status: {x["status"]}', ""])
    rows.extend(["## 3. Five distinct licensing and rights facets, all unverified", "",
                 "An SPDX expression is metadata, not a finding that an ML model and every tokenizer, adapter, code package, input or output is legally deployable. Future M18/M53/M54 owner evidence must qualify actual terms and tenant scope.", ""])
    for x in p["licenseFacets"]:
        rows.append(f'- **{x["id"]}**: {x["scope"]} | pending {x["ownerBoundary"]} | {x["verification"]} | {x["status"]}.')
    rows.extend(["", "## 4. Four alternative identity/receipt designs, none selected", ""])
    for x in p["alternatives"]:
        rows.extend([f'### {x["id"]}: {x["title"]}', "",
                     f'- Hypothesis and limit: {x["hypothesis"]}',
                     f'- Missing independent owner evidence: {x["pendingOwners"]}',
                     f'- Status: {x["status"]}, selected={x["selected"]}.', ""])
    rows.extend(["## 5. Sixteen NEW OPEN/UNRATED M14 S01 owner questions", "",
                 "All questions below are newly proposed, not owner answers or risk findings. Earlier M11 86, M12 110/80, M13 96/74 and H01–H04 remain unchanged.", ""])
    for x in p["questions"]:
        rows.extend([f'### {x["id"]} | {x["originalOwners"]}', "",
                     x["question"], "",
                     f'Original-source roles: {", ".join(x["sourceRoles"])}. Status: {x["status"]}; risk: UNRATED; actual owner answer: NOT RECEIVED; executable authority: NONE.', ""])
    rows.extend(["## 6. Twelve hostile/ambiguity future-case designs, NOT_EXECUTED", ""])
    for x in p["negativeScenarios"]:
        rows.extend([f'### {x["id"]}', "",
                     f'- Proposed hostile input: {x["trigger"]}',
                     f'- Required non-authorizing oracle: {x["nonAuthorizingOracle"]}.',
                     f'- Source question links: {", ".join(x["questionIds"])}.',
                     f'- Status: {x["status"]}; no provider, filesystem, GPU, OS or network test was executed.', ""])
    rows.extend(["## 7. External reference examples only, no specification adopted", "",
                 "These official format references are vocabulary candidates, not IRIS contract choices, proof of current commercial permission, actual vendor compatibility or offline test execution.", ""])
    for x in p["externalReferences"]:
        rows.append(f'- **{x["id"]}**: {x["url"]} | {x["status"]}.')
    rows.extend(["", "## 8. Boundary, actual owner questions and STOP", "",
                 f'- M09 B: {p["ownerB"]}; C01: {p["m09C01"]}; four highs: {p["h01h02h03h04"]}.',
                 f'- Current cross-module native runtime: {p["m10m11m12m13Runtime"]}; historical M13: {p["originalM13QuestionsOpen"]} open questions and {p["originalM13FutureCasesNotExecuted"]} unexecuted future tests.',
                 "- S02–S05, empirical measurement, qualified license/supply-chain review and M14 contract freeze require distinct admitted work and real owners.",
                 f'- STOP: {p["stop"]}', ""])
    return "\n".join(rows) + "\n"

def verify_packet(p: dict, root: Path = ROOT, *, verify_markdown: bool = True) -> dict:
    expected_fields = {
        "schemaVersion", "workOrder", "issue", "module", "session", "sourceBaseSha",
        "sourceBaseTreeSha", "status", "ownerApproval", "selectedTechnology",
        "versionedOwnerContract", "modelRegistryRuntime", "realLicenseApproval",
        "empiricalModelCards", "ownerB", "m09C01", "h01h02h03h04",
        "m10m11m12m13Runtime", "originalM13QuestionsOpen",
        "originalM13FutureCasesNotExecuted", "sourceDocs", "componentClasses",
        "licenseFacets", "alternatives", "questions", "negativeScenarios",
        "externalReferences", "stop",
    }
    require(type(p) is dict and set(p) == expected_fields, "unknown or missing M14 S01 packet field")
    expected = {
        "schemaVersion": "iris-m14-s01-source-research-v0.1",
        "workOrder": "IRIS-WO-0076", "issue": 204, "module": "M14", "session": "S01",
        "sourceBaseSha": BASE, "sourceBaseTreeSha": TREE,
        "status": "SOURCE_RESEARCH_ONLY_NONBINDING",
        "ownerApproval": "NONE", "selectedTechnology": "NONE",
        "versionedOwnerContract": "NOT_CREATED", "modelRegistryRuntime": "NOT_ADMITTED",
        "realLicenseApproval": "NONE", "empiricalModelCards": "NONE_MEASURED",
        "ownerB": "B_FUTURE_OWNER_RECEIPT_DIRECTION_ONLY",
        "m09C01": "UNADOPTED_NOT_FROZEN",
        "h01h02h03h04": "ALL_OPEN_HIGH_FOR_FUTURE_FREEZE",
        "m10m11m12m13Runtime": "NOT_ADMITTED",
        "originalM13QuestionsOpen": 96, "originalM13FutureCasesNotExecuted": 74,
    }
    for key, value in expected.items():
        require(type(p[key]) is type(value) and p[key] == value,
                "source, original owner or implementation STOP changed: " + key)
    require(type(p["stop"]) is str and len(p["stop"]) > 390
            and all(x in p["stop"] for x in ("NOT_ADMITTED", "SPECIFIED_NOT_EXECUTED", "OPEN/UNRATED", "H01-H04")),
            "missing explicit non-executable STOP boundary")
    docs = p["sourceDocs"]
    require(type(docs) is list and len(docs) == len(SOURCES), "source role count changed")
    for doc, (role, path, sha, needle) in zip(docs, SOURCES):
        require(type(doc) is dict and doc == {"role": role, "path": path,
                "gitBlobSha1": sha, "exactNeedle": needle},
                "source role/hash/anchor not exactly pinned: " + role)
        raw = (root / path).read_bytes()
        require(blob_sha(raw) == sha and needle in raw.decode("utf-8"),
                "original source bytes or required anchor changed: " + role)
    active_index = (root / SOURCES[0][1]).read_text(encoding="utf-8")
    for needle in FIVE_SESSIONS:
        require(needle in active_index, "current standalone M14 session changed: " + needle)
    classes = p["componentClasses"]
    require(type(classes) is list and [x.get("id") for x in classes] == list(COMPONENTS),
            "five component classes absent or reordered")
    for x in classes:
        require(set(x) == {"id", "title", "boundary", "pendingOwners", "status"}
                and x["status"] == "SOURCE_TAXONOMY_UNADOPTED"
                and all(type(x[k]) is str and len(x[k]) >= 20
                        for k in ("title", "boundary", "pendingOwners") if k != "pendingOwners")
                and type(x["pendingOwners"]) is str and x["pendingOwners"].startswith("M"),
                "component adoption, missing provenance boundary or missing owner caveat")
    licenses = p["licenseFacets"]
    require(type(licenses) is list and [x.get("id") for x in licenses] == list(LICENSE_FACETS),
            "five rights facets absent or reordered")
    for x in licenses:
        require(set(x) == {"id", "scope", "ownerBoundary", "verification", "status"}
                and x["status"] == "RIGHTS_UNVERIFIED"
                and x["verification"] == "NOT_OWNER_VERIFIED"
                and len(x["scope"]) >= 24 and x["ownerBoundary"].startswith("M"),
                "unverified license/rights claim promoted")
    alternatives = p["alternatives"]
    require(type(alternatives) is list and [x.get("id") for x in alternatives] == list(ALTERNATIVES),
            "four technology/version candidates absent or reordered")
    for x in alternatives:
        require(set(x) == {"id", "title", "hypothesis", "pendingOwners", "status", "selected"}
                and x["selected"] is False
                and x["status"] in ("RESEARCH_REFERENCE_NOT_DEPLOYABLE", "RESEARCH_CANDIDATE_ONLY")
                and len(x["hypothesis"]) >= 68 and x["pendingOwners"].startswith("M"),
                "unqualified model technology selected or caveat missing")
    questions = p["questions"]
    expected_q = [f"M14-S01-U{i:02d}" for i in range(1, 17)]
    require(type(questions) is list and [x.get("id") for x in questions] == expected_q,
            "original sixteen M14 S01 owner questions missing/duplicated/reordered")
    roles = {x[0] for x in SOURCES}
    for q in questions:
        require(set(q) == {"id", "question", "originalOwners", "sourceRoles",
                            "status", "risk", "ownerAnswer", "executableAuthority"}
                and q["status"] == "OPEN_UNRATED_PENDING_QUALIFIED_OWNER"
                and q["risk"] == "UNRATED" and q["ownerAnswer"] is None
                and q["executableAuthority"] == "NONE"
                and type(q["question"]) is str and len(q["question"]) >= 85
                and q["originalOwners"].startswith("M")
                and type(q["sourceRoles"]) is list and len(q["sourceRoles"]) >= 2
                and all(x in roles for x in q["sourceRoles"])
                and len(set(q["sourceRoles"])) == len(q["sourceRoles"]),
                "invented original owner answer, risk ranking or question source")
    cases = p["negativeScenarios"]
    require(type(cases) is list
            and [x.get("id") for x in cases] == [f"M14-S01-N{i:02d}" for i in range(1, 13)],
            "original twelve future negative cases missing/duplicated/reordered")
    for n in cases:
        require(set(n) == {"id", "trigger", "nonAuthorizingOracle", "questionIds", "status"}
                and n["status"] == "SPECIFIED_NOT_EXECUTED"
                and len(n["trigger"]) >= 70
                and n["nonAuthorizingOracle"].startswith(("NO_", "REFUSE_", "REJECT_", "RIGHTS_"))
                and type(n["questionIds"]) is list and len(n["questionIds"]) >= 1
                and len(set(n["questionIds"])) == len(n["questionIds"])
                and all(q in expected_q for q in n["questionIds"]),
                "future hostile case promoted, truncated or foreign question referenced")
    refs = p["externalReferences"]
    require(type(refs) is list and len(refs) == len(EXTERNAL_REFERENCES),
            "external source/vocabulary reference count changed")
    for row, (name, url) in zip(refs, EXTERNAL_REFERENCES):
        require(row == {"id": name, "url": url,
                "status": "REFERENCE_ONLY_NOT_ADOPTED_OR_LEGAL_PROOF"},
                "external source promoted into contract, legal proof or wrong reference")
    if verify_markdown:
        require((root / REPORT).read_text(encoding="utf-8") == render_report(p),
                "human M14 S01 source report does not exactly match machine projection")
    return {"originalSourcePinsVerified": len(docs), "conceptualComponentsUnadopted": len(classes),
            "licenseFacetsUnverified": len(licenses), "alternativesUnselected": len(alternatives),
            "originalM14S01QuestionsOpen": len(questions),
            "futureNegativesSpecifiedNotExecuted": len(cases),
            "externalReferencesOnly": len(refs), "qualifiedOwnerApprovals": 0}

def verify_all(root: Path = ROOT) -> dict:
    return verify_packet(read_json(root), root, verify_markdown=True)

if __name__ == "__main__":
    print(json.dumps(verify_all(), sort_keys=True))
