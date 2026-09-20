# IRIS-WO-0001 - GEF + HIVE Foundation

Status: `COMPLETED_APPROVED`

## OBJECTIVE
Bootstrap KayzenRoot/iris as a new GEF v1.0.0 project and make it structurally compatible with stable HIVE v1.0.0 before product planning/implementation.

## CONTEXT
IRIS is the visual/multimodal production system in the Hive ecosystem. Seed base: `065b5388806bb5d6ef2a5640b87d1f2e74e9a0ab`.

## SCOPE
Canonical Source Pack; GEF governance; HIVE registration/index/retrieval/MCP bridge; deterministic validation/tests; GitHub governance scaffolding.

## OUT OF SCOPE
IRIS product implementation; vendoring HIVE/GEF; mutating the user's machine-local runtimes; final CORE<->IRIS runtime protocol; model/tool selection.

## FILES/SOURCES TO READ
GEF v1.0.0 installation/quickstart/release; HIVE v1.0.0 stable contracts; CORE bootstrap only as non-authoritative reference; IRIS Project Brain.

## REQUIREMENTS
Pin GEF `866fe3af8cccc65c929aaf6a47a924401fa448b3`; pin HIVE `a53b5b9fcf55c32a5696180fb1b1ef80ccd1edcf`; keep Git authoritative; fail closed on ambiguous HIVE identity; gate product implementation.

## ARCHITECTURE RULES
HIVE remains separate local-first runtime. GEF remains external source workspace plus project governance. Do not duplicate either runtime/workspace into IRIS.

## CONSTRAINTS
No secrets/machine-specific absolute paths. No destructive Git. Exact-head evidence required.

## ACCEPTANCE CRITERIA
Source Pack and GEF/HIVE paths exist; validator/tests pass; Governance CI passes exact head; local HIVE operator command is documented; no product code introduced.

## TESTS
`python -m py_compile scripts/validate_governance.py scripts/gef_preflight.py scripts/hive_bootstrap.py scripts/hive_mcp.py`; `python scripts/validate_governance.py`; `python -m unittest discover -s tests -p "test_*.py" -v`; exact-head GitHub Actions.

## DELIVERABLES
Governance, Source Pack, HIVE tooling, Codex MCP config, CI/templates, evidence and review.

## REVIEW FORMAT
PT-BR with severity and verdict `APPROVED`, `CORRECTION REQUIRED`, or `BLOCKED`.

## EVIDENCE
- Authorized base: `065b5388806bb5d6ef2a5640b87d1f2e74e9a0ab`.
- Audited implementation head: `c2209066882ac9177978674dfa4d5f890704bb71`.
- Exact-head Governance run: `35518322714` / job `106097931747` / SUCCESS.
- Exact-head assertion: expected = actual = `c2209066882ac9177978674dfa4d5f890704bb71`.
- Governance validator: PASS; 35 required artifacts.
- Bridge tests: 8/8 PASS.
- CRITICAL: 0; HIGH: 0; blocking MEDIUM: 0.
- Local HIVE runtime execution remains separate operator evidence because this GitHub execution environment cannot access the user's workstation.

## STOP CONDITION
Satisfied for repository-side bootstrap. IRIS product implementation remains prohibited until a new admitted planning Work Order exists.
