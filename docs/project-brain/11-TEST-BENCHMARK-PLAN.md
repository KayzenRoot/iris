# IRIS Test & Benchmark Plan

Status: `M04_IMPLEMENTATION_REVIEWED_MERGE_GATE`

## Current repository gate
Every admitted code or governance increment must use risk-appropriate checks and exact-head GitHub Governance. The current gate includes:
- Python compile/static syntax checks for governed tooling and affected packages;
- `scripts/validate_governance.py`;
- full `unittest` discovery;
- focused module regressions where applicable;
- exact-candidate SHA assertion in GitHub Actions;
- post-merge exact-`main` Governance validation.

The authorized M04 implementation baseline at `58e4201f1d76d261e9e213b7aab91ae8734188a5` passed Governance `35803397206 / 106998641283` with **2527/2527 tests OK** and 35 required governance artifacts.

The independently reviewed M04 code head `7d3237a3ea39a1006fca8137046587077de29602` passed Governance `35813813456 / 107030932340` with **2677/2677 tests OK** and 35 required governance artifacts.

Independent review added 12 M04 regression tests beyond the executor's 138-test focused baseline, covering extension fail-closed policy, caller-selected structural limits, full-revision resource limits, unit/color/time-aware tolerant round trips, collision-free color witness paths and composite invariant proof alignment.

## M04 implementation obligations
The reviewed implementation proves the acceptance families frozen by `m04-contract-v1.0`, including:
- all 80 hard invariants;
- deterministic canonical serialization/digests;
- identity, graph, composition and reference integrity;
- M03→M04 trace/lowering integrity with no silent mandatory-semantic loss;
- schema/facet/extension/versioning/migration fail-closed behavior;
- spatial/camera/light/material/color semantics;
- temporal/motion/audio/music/narrative/timeline semantics;
- capability/legality/lowering boundary with zero M16 concrete workflow leakage;
- round-trip witness/equivalence and anti-self-certification behavior;
- adversarial graph/resource/depth/fanout/sample limits;
- minimum-sufficient slices, localized fingerprints/deltas and interface-only inspection;
- seven domain-neutral fixtures using the same core;
- static/import proof of no provider/DCC/cloud/database/network/shell runtime dependency.

No arbitrary performance/token percentage is claimed without measured evidence.

## Risk posture
M04 implementation remains `ELEVATED` until protected merge plus exact-main validation. No known HIGH/CRITICAL review findings remain.

## Future product validation
Unit/integration/E2E; visual/reference quality; anatomy/pose/rig/deformation; temporal consistency/motion smoothness; geometry/topology/material/shader; audio; GPU/VRAM/RAM performance/fallback; DCC integration; export/import reproducibility.

Thresholds/datasets are frozen by the owning modules before their implementations can claim completion.
