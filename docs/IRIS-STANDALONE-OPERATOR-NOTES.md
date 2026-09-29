# IRIS standalone: safe operator checklist

IRIS-WO-0066 is a repository migration, not a remote uninstall operation. Current startup, GitHub CI and source governance no longer require the former local context runtime. Integrations already configured OUTSIDE this repository on the operator's PC are not automatically removed by merging a PR.

## Operator-controlled local steps

1. Back up any context/database contents from the retired installation that you still need. Do not remove Docker volumes, external bind mounts or local projects unless independently verified and intentionally authorized: deleting volumes can irreversibly erase data.
2. Stop only the former context application's containers/services, then uninstall that application using its own instructions. Do not stop unrelated GEF, IRIS, CORE, model/DCC or database instances.
3. Inspect global Codex, Cursor, VS Code and other editor MCP/server configurations outside the Git repository. Remove any remaining launcher of the retired server. This repository deletes its old project-specific .codex/config.toml, but cannot modify personal/global editor settings.
4. Remove environment variables used solely by the retired project registration, if present, from your own OS shell/profile. Do not delete unrelated Docker/Python/Git tools needed by other projects.
5. From a fresh IRIS checkout run `python scripts/validate_governance.py` and `python -m unittest discover -s tests -p "test_*.py"` with Python 3.12+. No external context service or Docker container should be needed.
6. Future work starts with the exact Git revision, `docs/project-brain/13-CHECKPOINT.md`, ADR-0047, and `planning/MASTER-MODULE-INDEX-CURRENT.md`. The original module index remains source-locked historical audit evidence.

Do not infer native runtime admission: M10-M13 execution and owner H01-H04 gates remain blocked. Future IRIS-native M52 retrieval requires independent admission and proof.
