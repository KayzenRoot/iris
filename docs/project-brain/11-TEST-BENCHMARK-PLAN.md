# IRIS Test & Benchmark Plan

Status: `M05_PLANNING_BASELINE_ACTIVE`

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
M05 planning starts from the 2677-test exact-main baseline. Final Technology Review consolidates all future proof obligations into `F-M05-01..25`, covering all 150 DNAX design-history candidates exactly once. The M06-M60 Forward Compatibility Scan passed across 55 modules with 0 critical ownership conflicts and 22 required extension/ref families. The frozen contract must therefore preserve these ports and future implementation tests must prove all 150 invariants through consolidated proof families, including authority firewalls for M02/M06/M30/M37/M39-M41/M43/M45-M46/M52-M60. The frozen `m05-contract-v1.0` defines 150 hard invariants, 25 consolidated proof families and 22 extension/ref ports. Independent Planning Audit is approved. Concrete M05 implementation tests remain unadmitted until planning merge and exact-main validation complete and a separate implementation package is admitted.
