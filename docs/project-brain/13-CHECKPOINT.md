# IRIS Checkpoint

## STATUS
M04_IMPLEMENTATION_ADMITTED

## VERSION
m04-contract-v1.0

## PHASE
IRIS-WO-0008_EXECUTOR_READY

## OBJECTIVE
Execute the complete frozen M04 Multimodal IR / Scene IR kernel through IRIS-WO-0008 on the recompiled branch and PR, preserving all upstream authority boundaries and stopping for independent review before merge.

## COMPLETED
- M01 Quality Kernel: implemented, approved and merged.
- M02 Project OS & Production Graph: implemented, approved and merged.
- M03 Creative Brief / Intent / Constraint Compiler: implemented, approved and merged.
- M04 planning/freeze/review package: complete and merged.
- M04 contract: `FROZEN_APPROVED / m04-contract-v1.0`.
- Prompt Delivery Policy PR #33: merged as `58e4201f1d76d261e9e213b7aab91ae8734188a5`.
- Authorized implementation base: `58e4201f1d76d261e9e213b7aab91ae8734188a5`.
- Baseline Governance: `35803397206 / 106998641283` — PASS.
- Baseline suite: `2527/2527 OK`.
- IRIS-WO-0008 issue: #30.
- Prior PR #31: closed as `STALE_CONTEXT`, not merged.
- Replacement branch: `iris-wo-0008-m04-multimodal-ir-r2`.
- Replacement PR: #34.
- Recompiled admission head: `18fcfc0e9c47e4a2a2bdb02df32b7be2bfe11a88`.
- Recompiled admission Governance: `35803708948 / 106999640802` — PASS.
- Recompiled admission suite: `2527/2527 OK`.
- Required governance artifacts: 35.
- M04 implementation code has not started.

## IN PROGRESS
IRIS-WO-0008 is admitted for executor preflight and complete M04 implementation on branch `iris-wo-0008-m04-multimodal-ir-r2` / PR #34.

## BLOCKERS
Before modifying implementation code, executor MUST:
1. resolve the local uncommitted `AGENTS.md` left by the prior stale run only after confirming its diff contains no user work;
2. fetch and verify `origin/main == 58e4201f1d76d261e9e213b7aab91ae8734188a5`;
3. checkout `iris-wo-0008-m04-multimodal-ir-r2`;
4. verify merge-base equals the authorized base;
5. verify every critical fingerprint in `.engineering/context-locks/IRIS-WO-0008.json`;
6. confirm the final executor-ready head has exact-head Governance PASS;
7. STOP `STALE_CONTEXT` on any mismatch.

M05 implementation remains blocked. PR #34 MUST NOT be merged on executor word.

## NEXT STEP
Run IRIS-WO-0008 executor preflight, implement and test the complete frozen M04 kernel on PR #34, then stop for independent review without merging or starting M05.
