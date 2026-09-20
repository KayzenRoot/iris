from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEF_SHA = "866fe3af8cccc65c929aaf6a47a924401fa448b3"
HIVE_SHA = "a53b5b9fcf55c32a5696180fb1b1ef80ccd1edcf"

REQUIRED = (
    "AGENTS.md", ".codex/config.toml", ".engineering/SOURCE-HIERARCHY.md",
    ".engineering/PROJECT-OVERVIEW.md", ".engineering/CHECKPOINT.md", ".engineering/CHECKPOINT.json",
    ".engineering/BOOTSTRAP-MANIFEST.json", ".engineering/gef/GEF-ADOPTION.md",
    ".engineering/gef/GEF-PROJECT-PROFILE.json", ".engineering/gef/GEF-SOURCE-BRIDGE.json",
    ".engineering/gef/GEF-POLICY.md", ".engineering/gef/GEF-EXECUTION-PROTOCOL.md",
    ".engineering/gef/GEF-REVIEW-PROTOCOL.md", ".engineering/gef/GEF-EVIDENCE-SPEC.md",
    ".engineering/work-orders/IRIS-WO-0001-GEF-HIVE-BOOTSTRAP.md",
    ".engineering/context-locks/IRIS-WO-0001.json", ".engineering/evidence/IRIS-WO-0001.json",
    "docs/project-brain/00-README-UPLOAD-ORDER.md", "docs/project-brain/01-PROJECT-OVERVIEW.md",
    "docs/project-brain/02-REQUIREMENTS.md", "docs/project-brain/03-SCOPE.md",
    "docs/project-brain/04-ARCHITECTURE.md", "docs/project-brain/05-INTEGRATION-CONTRACTS.md",
    "docs/project-brain/10-SECURITY-GOVERNANCE.md", "docs/project-brain/11-TEST-BENCHMARK-PLAN.md",
    "docs/project-brain/12-LOCAL-DEPLOYMENT.md", "docs/project-brain/13-CHECKPOINT.md",
    "docs/project-brain/14-BACKLOG.md", "docs/project-brain/15-DEFINITION-OF-DONE.md",
    "docs/project-brain/16-DECISIONS-LEDGER.md", "docs/GEF-INTEGRATION.md", "docs/HIVE-INTEGRATION.md",
    "scripts/gef_preflight.py", "scripts/hive_bootstrap.py", "scripts/hive_mcp.py",
)

HEADINGS = ("## STATUS", "## VERSION", "## PHASE", "## OBJECTIVE", "## IN PROGRESS", "## BLOCKERS", "## NEXT STEP")

def fail(message: str) -> None:
    raise SystemExit(f"GOVERNANCE VALIDATION FAILED: {message}")

def section(text: str, heading: str) -> str:
    lines = text.splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError:
        fail(f"checkpoint missing heading: {heading}")
    values: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.strip():
            values.append(line.strip())
    if not values:
        fail(f"checkpoint heading has no value: {heading}")
    return "\n".join(values)

for relative in REQUIRED:
    if not (ROOT / relative).is_file():
        fail(f"missing required file: {relative}")

canonical = (ROOT / "docs/project-brain/13-CHECKPOINT.md").read_text(encoding="utf-8")
for heading in HEADINGS:
    section(canonical, heading)
bridge = (ROOT / ".engineering/CHECKPOINT.md").read_text(encoding="utf-8")
machine = json.loads((ROOT / ".engineering/CHECKPOINT.json").read_text(encoding="utf-8"))
if machine.get("canonicalCheckpoint") != "docs/project-brain/13-CHECKPOINT.md": fail("machine checkpoint target mismatch")
for field, heading in {"status":"## STATUS","version":"## VERSION","phase":"## PHASE","nextStep":"## NEXT STEP"}.items():
    if section(bridge, heading) != section(canonical, heading): fail(f"human checkpoint drift for {field}")
    if machine.get(field) != section(canonical, heading): fail(f"machine checkpoint drift for {field}")

profile = json.loads((ROOT / ".engineering/gef/GEF-PROJECT-PROFILE.json").read_text(encoding="utf-8"))
if profile.get("gefVersion") != "1.0.0" or profile.get("gefReleaseCommit") != GEF_SHA: fail("GEF profile pin mismatch")
expected = ("docs/project-brain/13-CHECKPOINT.md","docs/project-brain/16-DECISIONS-LEDGER.md","docs/project-brain/03-SCOPE.md","docs/project-brain/15-DEFINITION-OF-DONE.md","docs/project-brain/04-ARCHITECTURE.md","docs/project-brain/02-REQUIREMENTS.md")
if tuple(profile.get("sourceHierarchy", ())[:6]) != expected: fail("GEF source hierarchy mismatch")

manifest = json.loads((ROOT / ".engineering/BOOTSTRAP-MANIFEST.json").read_text(encoding="utf-8"))
if manifest.get("gef", {}).get("releaseCommit") != GEF_SHA: fail("manifest GEF pin mismatch")
if manifest.get("hive", {}).get("releaseCommit") != HIVE_SHA: fail("manifest HIVE pin mismatch")

source = json.loads((ROOT / ".engineering/gef/GEF-SOURCE-BRIDGE.json").read_text(encoding="utf-8"))
if source.get("canonicalCheckpoint") != "docs/project-brain/13-CHECKPOINT.md": fail("source bridge checkpoint mismatch")
required_domains = {"PROJECT_STATE":"docs/project-brain/13-CHECKPOINT.md","DECISION":"docs/project-brain/16-DECISIONS-LEDGER.md","SCOPE":"docs/project-brain/03-SCOPE.md","COMPLETION":"docs/project-brain/15-DEFINITION-OF-DONE.md","ARCHITECTURE":"docs/project-brain/04-ARCHITECTURE.md","REQUIREMENT":"docs/project-brain/02-REQUIREMENTS.md","SECURITY":"docs/project-brain/10-SECURITY-GOVERNANCE.md","VALIDATION":"docs/project-brain/11-TEST-BENCHMARK-PLAN.md","DEPLOYMENT":"docs/project-brain/12-LOCAL-DEPLOYMENT.md","INTEGRATION":"docs/project-brain/05-INTEGRATION-CONTRACTS.md"}
for domain, relative in required_domains.items():
    if source.get("domains", {}).get(domain) != relative: fail(f"source bridge mismatch: {domain}")

print("IRIS governance validation: PASS")
print(f"GEF: v1.0.0 @ {GEF_SHA}")
print(f"HIVE: v1.0.0 @ {HIVE_SHA}")
print(f"Required artifacts: {len(REQUIRED)}")
