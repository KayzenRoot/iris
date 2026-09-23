# IRIS Checkpoint

## STATUS
M04_IMPLEMENTATION_ADMISSION_RECOMPILED_PENDING_VALIDATION

## VERSION
m04-contract-v1.0

## PHASE
IRIS-WO-0008_RECOMPILE_AFTER_PROMPT_POLICY

## OBJECTIVE
Recompile IRIS-WO-0008 on the validated main that includes the repository-canonical PDF prompt-delivery policy, then re-admit the complete frozen M04 implementation only after exact-head Governance and a fresh Context Lock.

## COMPLETED
- M01 Quality Kernel: implemented, approved and merged.
- M02 Project OS & Production Graph: implemented, approved and merged.
- M03 Creative Brief / Intent / Constraint Compiler: implemented, approved and merged.
- M04 planning/freeze/review package: complete and merged.
- M04 contract: `FROZEN_APPROVED / m04-contract-v1.0`.
- Prompt Delivery Policy PR #33: merged as `58e4201f1d76d261e9e213b7aab91ae8734188a5` and exact-main validated.
- New baseline Governance: `35803397206 / 106998641283` — PASS.
- New baseline suite: `2527/2527 OK`.
- Required governance artifacts: 35.
- IRIS-WO-0008 issue remains #30.
- Prior PR #31 is stale because it was admitted before the critical prompt/review policies changed.
- M04 implementation code has not started.

## IN PROGRESS
Recompile Work Order / Context Lock / Evidence on branch `iris-wo-0008-m04-multimodal-ir-r2` and open the replacement implementation PR.

## BLOCKERS
M04 implementation MUST NOT start until:
1. the replacement PR exists on the new authorized base;
2. every critical-source fingerprint matches this recompiled branch;
3. exact-head Governance passes on the final admission head;
4. executor preflight confirms `origin/main == 58e4201f1d76d261e9e213b7aab91ae8734188a5` and merge-base equals the authorized base.

M05 implementation remains blocked.

## NEXT STEP
Finish the recompiled IRIS-WO-0008 admission on the replacement PR, validate exact head, then deliver the executor prompt only as a downloadable PDF and execute M04.
