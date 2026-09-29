# IRIS-WO-0074 | Fail closed on non-regular original Git sources and proposed Context Locks

**Issue:** [#186](https://github.com/KayzenRoot/iris/issues/186). **Status at authoring:** PROPOSED / SOURCE_LOCKED, not an owner contract. Old proposed [PR #187](https://github.com/KayzenRoot/iris/pull/187) CLOSED WITHOUT MERGE, never reused as original base. **Trusted original base:** protected `f5b267a6d8522a531129ca35a874feda377c61b3` / tree `bd456adf95e6a452cc8fb42b7722687204c495f7`, independent [Governance #36561065944](https://github.com/KayzenRoot/iris/actions/runs/36561065944) **4680/4680**, same-main Socket Security Project Report SUCCESS and issue [#199 factual closeout](https://github.com/KayzenRoot/iris/issues/199#issuecomment-5889220768) CLOSED.

## Observed defect, bound correction and acceptance

The current verifier recorded exact original-base SHA for every Git `blob` without its original tracked mode. Git symlink `120000 blob` or executable `100755 blob` can therefore match the declared source SHA while being an unsuitable repository authority document. A new changed Context Lock likewise was read using `git show` without checking the proposed HEAD tracked mode. This is preventive boundary hardening; no exploit or owner release is claimed.

1. Collect `git ls-tree -r -z` original-base modes alongside existing real Git object IDs; preserve the prior `base_blob_map` return type with optional `modes_out`.
2. For every original-base `criticalSources` pinned document require **`100644 blob`**, including the newest original WO0073 lock pinned as the required source-manifest anchor. Check that anchor mode before reading its original JSON.
3. For each newly verified changed HEAD Context Lock, require exact HEAD `git ls-tree -z` **`100644 blob`** before reading/parsing. Preserve existing latest original manifest path/inherited source gating, SHA match, strict file diff, duplicate-key JSON guard, Dependabot one-pin exemption and one-time frozen historical migration semantics.
4. Preserve pure `verify_lock` backward compatibility with optional `base_modes` argument while CLI always supplies the exact original Git base mode map. No Git working-tree chmod, symlink following or reinterpretation of hashed source text as mode.
5. Add 8 deterministic offline regression tests with actual isolated Git repositories for regular positive; original-base symlink and executable; HEAD lock symlink/executable; pure mode argument negative; newest original manifest anchor symlink/executable negatives.

**Strict authorized changed paths:** exactly the six in the WO0074 Context Lock. **Original-source pins:** 29/29 actual trusted base Git SHA1 objects, all original mode `100644`: 25 inherited WO0073 `criticalSources` plus WO0073 lock itself, original governance workflow, pure context-lock test and real Git manifest-anchor test. Latest original-base anchor must be WO0073, SHA `64db523ee483c3aa8a3b376a928b76f1b0c36ff9`. The prior M01–M09 frozen contracts, canonical current checkpoint, architecture, historical immutable approvals and work-order files remain untouched.

## STOP condition and evidence gates

The exact PR HEAD must pass full Python 3.12 Governance, Context Lock, complete **4688+** suite (4680 baseline + eight mode regressions), same-head both Socket checks, independent completed external review with no unresolved actionable findings, and strict original-base source/diff audit. No weakened validators/test skips. Then guarded protected squash on exact reviewed HEAD and independently pass full Governance and same-main Socket on exact-new-main SHA. Only then factual issue #186 receipt and CLOSE; historical author-time PENDING stays immutable. Review pt-BR APPROVED/CORRECTION REQUIRED/BLOCKED with exact SHAs and receipts.

**Original owner STOPs:** #82/#110/#112/#128/#145/#146/#147/#155 remain OPEN, H01-H04 HIGH_FOR_FUTURE_FREEZE, B direction-only, C01 UNADOPTED_NOT_FROZEN, M10-M13 runtime NOT_ADMITTED. No PC uninstall, GPU/OS/process/network/cloud operations, local context service or external memory database dependency.
