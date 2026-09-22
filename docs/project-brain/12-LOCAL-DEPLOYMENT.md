# IRIS Local Deployment

Status: `SEMANTIC_FOUNDATION_ONLY`

The repository now contains governed/importable semantic kernels for M01, M02 and M03 plus governance/integration scaffolding. It does **not** yet contain the provider/DCC/media-generation runtime that constitutes end-user IRIS production deployment.

Required operator environment for the current repository gates: Git; Python 3.12+; local HIVE v1.0.0 checkout/runtime when HIVE integration is exercised; Docker Desktop/Compose for HIVE; optional local GEF v1.0.0 source checkout.

Machine-specific paths use environment variables.

M04 planning changes contracts/documentation only. Product runtime deployment, installer/services, DCC workers, ComfyUI runtime integration and final deployment/recovery belong to later admitted modules and must not be inferred from the existence of M01-M03 semantic packages.
