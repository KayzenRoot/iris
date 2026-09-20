# IRIS Bootstrap Tooling

- `validate_governance.py`: deterministic Source Pack/GEF/HIVE consistency gate.
- `gef_preflight.py`: verifies the local stable GEF v1.0.0 source checkout.
- `hive_bootstrap.py`: HIVE health/register/inspect/index/corpus-sync workflow.
- `hive-bootstrap.ps1`: PowerShell wrapper for local HIVE bootstrap.
- `hive_mcp.py`: project-scoped launcher for HIVE's stable stdio MCP server.

No script stores credentials or machine-specific absolute paths in Git.
