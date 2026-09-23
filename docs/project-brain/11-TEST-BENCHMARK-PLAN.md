# IRIS Test & Benchmark Plan

Status: `M04_MERGED_BASELINE_ACTIVE`

## Current repository gate
Every admitted code or governance increment must use risk-appropriate checks and exact-head GitHub Governance, including exact-candidate SHA assertion and post-merge exact-main validation.

## Current canonical baseline

M04 reviewed implementation merge:
- main SHA: `8dd188fcea7fa0874fab214867e1f5f6ce23e8cd`;
- Governance: `35814014969 / 107031546003` — PASS;
- required governance artifacts: 35;
- full suite: **2677/2677 OK**.

The pre-M04 implementation baseline was 2527 tests. The reviewed M04 state adds 150 focused M04 tests without deleting or weakening the baseline suite.

## M04 proof areas
- all 80 hard invariants;
- deterministic serialization/digests;
- graph/composition/reference integrity;
- schema/facet/extension fail-closed behavior;
- migration and compatibility;
- spatial/camera/light/material/color;
- temporal/motion/audio/music/narrative/timeline;
- M03 lowering and M16 firewall;
- semantic round-trip, unit/color/time-aware tolerance and anti-self-certification;
- resource/depth/fanout/sample limits;
- slices/fingerprints/deltas;
- seven domain-neutral fixtures;
- no provider/DCC/network/shell/database runtime dependency.

## Next-module rule
M05 must establish its own thresholds, fixtures and exact-head gates before implementation. No M04 test result automatically proves M05 correctness.
