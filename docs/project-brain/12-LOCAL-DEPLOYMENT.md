# IRIS Local Deployment

Status: `SEMANTIC_FOUNDATION_ONLY`

The repository now contains governed/importable semantic kernels for M01, M02 and M03 plus governance/integration scaffolding. It does **not** yet contain the provider/DCC/media-generation runtime that constitutes end-user IRIS production deployment.

Required operator environment for current repository gates: Git and Python 3.12+. A GEF v1.0.0 source checkout is optional and only needed for tasks that explicitly run the GEF preflight. No external memory database, Docker stack, project registration, localhost HTTP endpoint or mandatory MCP server is needed.

Machine-specific paths use environment variables.

M04 planning changes contracts/documentation only. Product runtime deployment, installer/services, DCC workers, ComfyUI runtime integration and final deployment/recovery belong to later admitted modules and must not be inferred from the existence of M01-M03 semantic packages.
