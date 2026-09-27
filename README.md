# Hive IRIS

**Intelligent Rendering & Immersive Synthesis**

Hive IRIS is the governed visual and multimodal production engine in the Hive ecosystem. The [canonical checkpoint](docs/project-brain/13-CHECKPOINT.md) is the source of truth for the live project state; this README is only a public-facing snapshot.

## Verified repository snapshot (2026-09-27)

- **M01–M09:** implementation milestones completed and exact-main validated; M09 remains frozen as `m09-contract-v1.0`.
- **M10:** `m10-contract-v1.0` is frozen for planning. Runtime implementation is **NOT_ADMITTED**; the separate IRIS-WO-0014 preflight is blocked.
- **M11:** Background Worker Fabric & Process Lifecycle research/planning completed; its v0.2 owner contract remains **NOT_FROZEN**, with 86 open owner questions ([issue #82](https://github.com/KayzenRoot/iris/issues/82)).
- **M12:** Compute Orchestration S01–S05 and source-only technology/compatibility research completed. Candidate `m12-contract-candidate-v0.1` is **PREPARED_FOR_OWNER_REVIEW_ONLY**, **NOT_FROZEN** and runtime **NOT_ADMITTED**, with 110 unresolved owner questions and 80 future negative scenarios **NOT_EXECUTED** ([issue #128](https://github.com/KayzenRoot/iris/issues/128)).
- **Current, bounded M09 owner decision:** the responsible user ratified **B_FUTURE_OWNER_RECEIPT** as **DIRECTION_ONLY** for a possible future immutable owner-issued M09→M11 read-only receipt ([Issue #110 formal record](https://github.com/KayzenRoot/iris/issues/110#issuecomment-5857665032)). This is **not C01 adoption or runtime authorization**; the M09 C01 extension remains **UNADOPTED_NOT_FROZEN** ([issue #112](https://github.com/KayzenRoot/iris/issues/112)). All four H01–H04 remain **OPEN HIGH_FOR_FUTURE_FREEZE** pending separate owner proof.
- - **Latest verified repository baseline:** [IRIS-WO-0039 PR #149](https://github.com/KayzenRoot/iris/pull/149) merged as `be18231423651c5dbff584613fc46d3e0104107f`; separate [exact-main Governance #528](https://github.com/KayzenRoot/iris/actions/runs/36344935836) passed **4290/4290**, including 30 *offline synthetic* tests of untrusted H03 draft formatting. Actual M12/#128, M54/#145, M58/#146 and M60/#147 owner contracts are still unapproved; H01–H04 remain OPEN HIGH_FOR_FUTURE_FREEZE, C01 UNADOPTED_NOT_FROZEN, and M10/M11/M12 runtime NOT_ADMITTED. This does not execute future 80 M12, 12 H03-N or original HX/LV/C08/PO-C02 cases.
- **Historical pre-B D01 baseline (not the latest repository validation):** [PR #139](https://github.com/KayzenRoot/iris/pull/139) on `main` commit `97a9fe1666b764278de1379eadd7eda7d04799fe`, [Governance #509](https://github.com/KayzenRoot/iris/actions/runs/36332401893) **PASS 4090/4090**. Its tests validate documentary integrity, not owner permissions or GPU/OS/network/cloud safety.
- **GEF:** `v1.0.0` pinned to `866fe3af8cccc65c929aaf6a47a924401fa448b3`.
- **HIVE product integration:** `v1.0.0` pinned to `a53b5b9fcf55c32a5696180fb1b1ef80ccd1edcf`.

Provider/DCC/media-generation runtime integration and the later M10/M11/M12 runtime are not admitted by these documentary milestones. Do not infer a contract freeze, resource grant, process permission or implementation acceptance from CI.

Canonical startup order: [Checkpoint](docs/project-brain/13-CHECKPOINT.md) → [Decisions](docs/project-brain/16-DECISIONS-LEDGER.md) → [Scope](docs/project-brain/03-SCOPE.md) → [DoD](docs/project-brain/15-DEFINITION-OF-DONE.md) → [Architecture](docs/project-brain/04-ARCHITECTURE.md) → [Requirements](docs/project-brain/02-REQUIREMENTS.md). Product implementation requires its own admitted Work Order, exact-head evidence, review and protected-main validation.
