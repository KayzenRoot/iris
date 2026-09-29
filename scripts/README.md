# IRIS Bootstrap and Governance Tools

- `validate_governance.py`: standalone canonical Git/Project Brain/GEF consistency gate, checkpoint mirror check, retirement path guard.
- `verify_context_lock.py`: verify original Git source identity, exact PR base and strict diff allowlist; no external memory service.
- `gef_preflight.py`: optional local GEF v1.0.0 source checkout verification, only if a separate task actually requires it.

GitHub Governance CI runs with Git and Python 3.12 without local databases, external context servers, Docker or workstation-specific services. Canonical source loading order remains Checkpoint → Decisions → Scope → DoD → Architecture → Requirements. Machine-specific paths and secrets are not committed.
