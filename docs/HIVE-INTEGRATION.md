# HIVE v1.0.0 Integration - IRIS

IRIS is prepared for stable HIVE v1.0.0 at commit `a53b5b9fcf55c32a5696180fb1b1ef80ccd1edcf`. HIVE stays a separate local-first runtime and mounts IRIS read-only beneath `HIVE_PROJECTS_ROOT`. Do not copy HIVE backend/database/Docker stack into IRIS.

## Required canonical files
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/03-SCOPE.md`
- `docs/project-brain/15-DEFINITION-OF-DONE.md`
- `docs/project-brain/04-ARCHITECTURE.md`
- `docs/project-brain/16-DECISIONS-LEDGER.md`

## Local HIVE setup
1. In the separate HIVE checkout, checkout `v1.0.0`.
2. Configure HIVE `HIVE_PROJECTS_ROOT` to the parent/root containing the local IRIS checkout.
3. Start HIVE with its supported Docker Compose procedure.
4. Verify `http://localhost:8000/api/v1/health`.
5. From IRIS run:
```powershell
python scripts/hive_bootstrap.py --relative-path iris
```

The bootstrap performs health -> resolve/register -> inspect -> repository index -> retrieval corpus sync and fails closed on ambiguous identity or non-ready state.

## MCP
Stable read-only tools: `project.list`, `project.status`, `context.build`, `context.search`, `memory.search`, `memory.get`, `checkpoint.read`.

IRIS `.codex/config.toml` launches `scripts/hive_mcp.py`, which resolves HIVE through `HIVE_REPO_PATH` or a sibling `hive`/`Hive` checkout and runs:
```text
docker compose exec -T api python -m app.mcp_server
```

HIVE memory/retrieval is derived context. Tracked Git and canonical Project Brain sources remain authoritative.
