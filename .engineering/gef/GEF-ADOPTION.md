# GEF v1.0.0 Adoption - IRIS (standalone)

- Project: `KayzenRoot/iris`
- Mode: `STANDALONE_GIT_FIRST`
- GEF source release: `v1.0.0`, upstream commit `866fe3af8cccc65c929aaf6a47a924401fa448b3`
- IRIS prompt preparation: `GIT_SOURCE_LOCK_FIRST` (IRIS policy; does not assert a corresponding upstream GEF CLI mode)
- Review: `DELTA_EXACT_HEAD`
- Assurance: fail closed on missing exact Git facts or required independent evidence.

GEF is the engineering/governance layer; IRIS Git and Project Brain are authoritative. The optional GEF v1.0.0 source checkout is independently pinned. No external local context server, Docker stack, third-party memory installation or mandatory MCP service is required for IRIS startup, source reads, tests or Governance CI. Future native M52 is separately owner-gated, not delivered by this retirement work order.
