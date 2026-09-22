# IRIS Test & Benchmark Plan

Status: `SEMANTIC_KERNEL_BASELINE_ACTIVE`

## Current repository gate
Every admitted code or governance increment must use risk-appropriate checks and exact-head GitHub Governance. The current gate includes:
- Python compile/static syntax checks for governed tooling and affected packages;
- `scripts/validate_governance.py`;
- full `unittest` discovery;
- focused module regressions where applicable;
- exact-candidate SHA assertion in GitHub Actions;
- post-merge exact-`main` Governance validation.

The pre-M04 exact-`main` baseline at `d65df7f239627f99941896451340f43ee1a887fd` passed Governance run `35679208065` with **2527/2527 tests OK**.

## M04 planning obligations
M04 planning must freeze measurable acceptance families before implementation, including:
- deterministic IR serialization/versioning and round-trip behavior;
- cross-modal reference integrity;
- loss/approximation reporting across semantic lowering;
- M01/M02/M03 authority-boundary regressions;
- invalid/stale/unknown schema and extension failure-closed behavior;
- domain-neutral fixtures spanning image, 3D, video/cinema and audio/narrative use cases;
- resource/size/depth limits for hostile or pathological IR payloads;
- forward-compatibility/extension-port conformance.

No implementation benchmark threshold is invented before M04 planning supplies evidence and a frozen contract.

## Future product validation
Unit/integration/E2E; visual/reference quality; anatomy/pose/rig/deformation; temporal consistency/motion smoothness; geometry/topology/material/shader; audio; GPU/VRAM/RAM performance/fallback; DCC integration; export/import reproducibility.

Thresholds/datasets are frozen by the owning modules before their implementations can claim completion.
