# IRIS Test & Benchmark Plan

Status: `M04_IMPLEMENTATION_BASELINE_ACTIVE`

## Current repository gate
Every admitted code or governance increment must use risk-appropriate checks and exact-head GitHub Governance. The current gate includes:
- Python compile/static syntax checks for governed tooling and affected packages;
- `scripts/validate_governance.py`;
- full `unittest` discovery;
- focused module regressions where applicable;
- exact-candidate SHA assertion in GitHub Actions;
- post-merge exact-`main` Governance validation.

The authorized M04 implementation baseline at `58e4201f1d76d261e9e213b7aab91ae8734188a5` passed Governance `35803397206 / 106998641283` with **2527/2527 tests OK** and 35 required governance artifacts.

## M04 implementation obligations
Implementation must prove the acceptance families frozen by `m04-contract-v1.0`, including:
- all 80 hard invariants;
- deterministic canonical serialization/digests;
- identity, graph, composition and reference integrity;
- M03→M04 trace/lowering integrity with no silent mandatory-semantic loss;
- schema/facet/versioning/migration fail-closed behavior;
- spatial/camera/light/material/color semantics;
- temporal/motion/audio/music/narrative/timeline semantics;
- capability/legality/lowering boundary with zero M16 concrete workflow leakage;
- round-trip witness/equivalence and anti-self-certification behavior;
- adversarial graph/resource/depth/fanout/sample limits;
- minimum-sufficient slices, localized fingerprints/deltas and interface-only inspection;
- seven domain-neutral fixtures using the same core;
- static/import proof of no provider/DCC/cloud/database/network/shell runtime dependency.

No arbitrary performance/token percentage may be claimed without measured evidence.

## Risk posture
M04 implementation is `ELEVATED`: schema evolution, graph integrity, migrations, compatibility and round-trip correctness require full regression, fail-closed security tests and recovery-safe immutable migration evidence.

## Future product validation
Unit/integration/E2E; visual/reference quality; anatomy/pose/rig/deformation; temporal consistency/motion smoothness; geometry/topology/material/shader; audio; GPU/VRAM/RAM performance/fallback; DCC integration; export/import reproducibility.

Thresholds/datasets are frozen by the owning modules before their implementations can claim completion.
