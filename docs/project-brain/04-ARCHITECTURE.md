# IRIS Architecture

Status: `BOOTSTRAP_ARCHITECTURE`

Git + Project Brain are authoritative. GEF governs lifecycle/evidence. HIVE supplies derived context/retrieval/memory/read-only MCP.

Target ecosystem topology is `HIVE <-> CORE <-> IRIS`, but CORE<->IRIS runtime contracts are not implemented/frozen.

HIVE remains separate Docker/local-first runtime. GEF remains separate source workspace/release. No HIVE backend/database or GEF package workspace is vendored into IRIS. Machine-local integration uses environment variables.

Product architecture is deferred to dedicated planning.
