# IRIS Integration Contracts

Status: `FOUNDATION_ACTIVE_M04_FROZEN`

## HIVE v1.0.0
Repository-contract integration includes canonical governance paths, registration/inspection/index/corpus sync client, read-only MCP launcher and project-scoped Codex config.

Stable tools: `project.list`, `project.status`, `context.build`, `context.search`, `memory.search`, `memory.get`, `checkpoint.read`.

HIVE remains derived context and never supersedes canonical Git/Project Brain truth. HIVE/agents may supply context or proposals but cannot directly mutate canonical M04 truth.

## GEF v1.0.0
Project governance/adoption profile is pinned to the stable release; GEF workspace source is not copied into IRIS.

## Internal semantic boundaries
- M01 exposes the frozen quality/Fidelity authority consumed by later modules.
- M02 exposes project/production/graph/build/release and ExecutionPlan authority.
- M03 exposes versioned creative intent/constraint/execution-intent semantics and future-facing opaque refs/ports.
- M04 frozen contract `m04-contract-v1.0` owns provider-neutral structured production representation, semantic lowering evidence, representation capability/legality, schema/version/migration and semantic round-trip contracts.
- M04 consumes M01/M02/M03 contracts without superseding their authority.
- M04 exposes only provider-neutral boundaries toward M05+ and M16.
- M16 remains the sole owner of concrete provider/workflow compilation and provider qualification.

Provider/DCC/storage/GPU/runtime SDKs are not M04 core dependencies.

## CORE
Approved target relationship, but protocol/API/event contracts remain `NOT_YET_PLANNED`.
