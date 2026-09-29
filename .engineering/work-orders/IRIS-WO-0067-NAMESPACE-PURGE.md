# IRIS-WO-0067 | Repository-wide legacy context namespace purge

Status: USER_AUTHORIZED / MIGRATION_IN_PROGRESS
Issue: #191

## Objective
Remove every remaining literal legacy context product namespace from the IRIS repository, including code identifiers, tests, planning documents, evidence references and filenames. The active architecture remains standalone Git + Project Brain with optional pinned GEF source tooling.

## Scope
- repository-wide deterministic namespace rewrite;
- rename matching files and references;
- preserve module behavior and current owner/runtime STOP conditions;
- keep no local external context runtime, MCP server, Docker/database dependency or editor bootstrap;
- repair any exact-source hashes or historical tests made stale by this intentional migration;
- require zero legacy namespace tokens in repository text and filenames at final head.

## Governance
Historical Context Locks changed by this migration are data being renamed, not newly authored authority. This Work Order therefore introduces one exact WO0067 Context Lock over the original protected base and the complete PR path allowlist. Existing owner issues, H01–H04 and M10–M13 runtime gates remain unchanged.

## STOP CONDITION
Protected squash merge only after exact-head Context Lock/Governance/full tests, final external review and Socket checks are green; then exact-new-main Governance/Socket must pass and issue #191 may close.
