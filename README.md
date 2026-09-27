# Hive IRIS

**Intelligent Rendering & Immersive Synthesis**

Hive IRIS is the governed visual and multimodal production engine in the Hive ecosystem. The [canonical checkpoint](docs/project-brain/13-CHECKPOINT.md) is the source of truth for the live project state; this README is only a public-facing snapshot.

## Verified repository snapshot (2026-09-27)

- **M01–M09:** implementation milestones completed and exact-main validated; M09 remains frozen as `m09-contract-v1.0`.
- **M10:** `m10-contract-v1.0` is frozen for planning. Runtime implementation is **NOT_ADMITTED**; the separate IRIS-WO-0014 preflight is blocked.
- **M11:** Background Worker Fabric & Process Lifecycle research/planning completed; its v0.2 owner contract remains **NOT_FROZEN**, with 86 open owner questions ([issue #82](https://github.com/KayzenRoot/iris/issues/82)).
- **M12:** Compute Orchestration S01–S05 and source-only technology/compatibility research completed. Candidate `m12-contract-candidate-v0.1` is **PREPARED_FOR_OWNER_REVIEW_ONLY**, **NOT_FROZEN** and runtime **NOT_ADMITTED**, with 110 unresolved owner questions and 80 future negative scenarios **NOT_EXECUTED** ([issue #128](https://github.com/KayzenRoot/iris/issues/128)).
- **Blocking owner dependency:** M09→M11 handoff topology A/B/C or explicit deferral needs the actual decision in [issue #110](https://github.com/KayzenRoot/iris/issues/110); four H01–H04 issues are **OPEN HIGH_FOR_FUTURE_FREEZE**. The M09 C01 extension remains **UNADOPTED** ([issue #112](https://github.com/KayzenRoot/iris/issues/112)).
- **Latest validated source-only milestone:** [PR #135](https://github.com/KayzenRoot/iris/pull/135) on `main` commit `b137a99157df3c72b2eaaf7b6209da399802d580`, [Governance #499](https://github.com/KayzenRoot/iris/actions/runs/36329122328) **PASS 4009/4009**. Its tests validate documentary integrity, not runtime permissions or GPU/OS/network/cloud behavior.
- **GEF:** `v1.0.0` pinned to `866fe3af8cccc65c929aaf6a47a924401fa448b3`.
- **HIVE product integration:** `v1.0.0` pinned to `a53b5b9fcf55c32a5696180fb1b1ef80ccd1edcf`.

Provider/DCC/media-generation runtime integration and the later M10/M11/M12 runtime are not admitted by these documentary milestones. Do not infer a contract freeze, resource grant, process permission or implementation acceptance from CI.

Canonical startup order: [Checkpoint](docs/project-brain/13-CHECKPOINT.md) → [Decisions](docs/project-brain/16-DECISIONS-LEDGER.md) → [Scope](docs/project-brain/03-SCOPE.md) → [DoD](docs/project-brain/15-DEFINITION-OF-DONE.md) → [Architecture](docs/project-brain/04-ARCHITECTURE.md) → [Requirements](docs/project-brain/02-REQUIREMENTS.md). Product implementation requires its own admitted Work Order, exact-head evidence, review and protected-main validation.
