# Hive IRIS - Project Overview

IRIS means **Intelligent Rendering & Immersive Synthesis**.

IRIS is the visual and multimodal production engine of the Hive ecosystem: high-quality 2D, 2.5D and 3D assets, animation, VFX, image, video, audio and web/game visual production, including future Blender/ComfyUI/DCC integrations.

Target roles:
- **HIVE** = derived context, retrieval and memory;
- **CORE** = cognition/orchestration when its runtime contracts are later admitted;
- **IRIS** = visual/multimodal creation, semantic production contracts and quality pipeline.

## Current governed state

IRIS is past bootstrap-only status.

- M01 Extreme Quality / Fidelity kernel is implemented, approved and merged.
- M02 Project OS / Production Graph kernel is implemented, approved and merged.
- M03 Creative Brief / Intent / Constraint Compiler is implemented, approved and merged.
- M04 Multimodal IR / Scene IR planning is complete, approved, frozen as `m04-contract-v1.0`, merged and exact-main validated.
- M04 implementation under `IRIS-WO-0008` is complete and independently reviewed on PR #34.
- The reviewed M04 code head `7d3237a3ea39a1006fca8137046587077de29602` passed exact-head Governance with `2677/2677` tests.
- Six independent `CHAT_FIXABLE` findings were corrected in the same PR; zero HIGH/CRITICAL or `EXECUTOR_REQUIRED` findings remain.
- Repository governance is protected by the active `main-governance` ruleset.
- The canonical checkpoint is the sole project-state authority.

M04 is merge-ready but not yet merged at this checkpoint. M05 remains blocked until exact-main post-merge validation and reconciliation.

No provider/DCC/media-generation runtime is implied by the semantic kernels. M04 remains provider-neutral/runtime-neutral; M16 is the sole concrete provider/workflow compiler owner.
