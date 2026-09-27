# Hive IRIS - Project Overview

IRIS means **Intelligent Rendering & Immersive Synthesis**.

IRIS is the visual and multimodal production engine of the Hive ecosystem: high-quality 2D, 2.5D and 3D assets, animation, VFX, image, video, audio and web/game production, including later Blender/ComfyUI/DCC integrations.

Target roles:
- **HIVE** = derived context, retrieval and memory;
- **CORE** = cognition/orchestration when its runtime contracts are separately admitted;
- **IRIS** = visual/multimodal creation, semantic production contracts and quality pipeline.

## Governed snapshot (2026-09-27)

The [canonical checkpoint](13-CHECKPOINT.md), [Decisions Ledger](16-DECISIONS-LEDGER.md) and exact Git/CI evidence take precedence over this descriptive snapshot.

- M01–M09 implementations are completed, approved and exact-main validated; the M09 contract `m09-contract-v1.0` remains frozen.
- M10 planning and contract `m10-contract-v1.0` are frozen. IRIS-WO-0014 implementation preflight is BLOCKED and M10 runtime is **NOT_ADMITTED**.
- M11 S01–S05 are complete for planning; its v0.2 owner-contract candidate remains **NOT_FROZEN** with 86 owner questions **OPEN/UNRATED** ([issue #82](https://github.com/KayzenRoot/iris/issues/82)).
- M12 S01–S05, source technology review (16 records) and index-level M13–M60 compatibility scan (48 modules) are complete **for source-reference planning only**. Its v0.1 owner candidate is **PREPARED_FOR_OWNER_REVIEW_ONLY**, not frozen or executable; 110 owner questions remain open and 80 future tests remain **SPECIFIED_NOT_EXECUTED** ([issue #128](https://github.com/KayzenRoot/iris/issues/128)).
- M09's C01 read-only evidence handoff remains **UNADOPTED_NOT_FROZEN**. The responsible user explicitly ratified **B_FUTURE_OWNER_RECEIPT** as **DIRECTION_ONLY** for planning a future M09-issued immutable, versioned, request-scoped receipt and verifier ([Issue #110 formal record](https://github.com/KayzenRoot/iris/issues/110#issuecomment-5857665032)). All four H01–H04 remain **OPEN HIGH_FOR_FUTURE_FREEZE**, and the actual M11/M12/M54/M58/M60 owner contracts, OS/GPU/network/cloud permissions and M09 positive port remain unapproved; M10/M11/M12 runtime NOT_ADMITTED.
- D01's last validated source-only baseline is [PR #139](https://github.com/KayzenRoot/iris/pull/139), exact main `97a9fe1666b764278de1379eadd7eda7d04799fe`; [Governance #509](https://github.com/KayzenRoot/iris/actions/runs/36332401893) passed **4090/4090**. Passing source-only tests is not proof of owner approval of C01, actual worker/process/GPU/network/cloud behavior or cross-boundary trust.

## Historical qualified milestones

- M04 Multimodal IR / Scene IR was planned, frozen as `m04-contract-v1.0`, implemented, independently reviewed and merged as `8dd188fcea7fa0874fab214867e1f5f6ce23e8cd`. Its historical exact-main Governance `35814014969 / 107031546003` passed `2677/2677`. Its implementation review corrected six `CHAT_FIXABLE` findings before approval.
- M05 `m05-contract-v1.0` was frozen through historical PR #38 and its planning was exact-main validated at `2b5b7330a684fece8e354b6fe88b8fcd4bb0611f` (Governance `35843109186 / 107122673542`, `2677/2677`). **M05 implementation has since been completed and durably closed.** Do not treat this old planning receipt as its current implementation status.
- Repository governance uses protected `main`. The canonical checkpoint, not this overview, establishes the next admitted increment.

No provider/DCC/media-generation runtime is implied by the semantic kernels or M12 planning evidence. M04 remains provider-neutral/runtime-neutral; M16 owns concrete provider/workflow compilation when separately admitted.
