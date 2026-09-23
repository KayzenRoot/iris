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

The M04 implementation baseline at `bb875a958a88a844bfa62cdfec694fe148590a41` passed Governance `35801705128 / 106993294512` with **2527/2527 tests OK** and 35 required governance artifacts.

## IRIS-WO-0008 / M04 obligations
Implementation must prove the acceptance families frozen in `m04-contract-v1.0`, including:
- all 80 hard invariants;
- deterministic identity, canonical serialization, digests and finding order;
- dual-graph integrity, typed cycle policy and deterministic composition;
- immutable prototypes/revisions/migrations and explicit version compatibility;
- M03→M04 trace/lowering coverage with no silent mandatory-semantic loss;
- M01 QualityClass and M01/M02/M03 authority boundaries preserved;
- M16 concrete provider/workflow compiler boundary preserved by static/import tests;
- unknown mandatory schema/facet/capability failure closed;
- explicit bounded approximation/loss authorization;
- spatial/unit/camera/light/material/color correctness;
- exact rational temporal semantics and typed motion targets;
- audio/music/narrative/timeline/sync representation boundaries;
- round-trip witness/equivalence tests that detect transform/camera/material/time/sync loss;
- opaque-preservation/digest and anti-self-certification tests;
- adversarial graph/resource/depth/fanout/sample limits;
- MinimumSufficientIRSlice, MinimumSufficientTemporalSlice, CapabilitySlice and localized fingerprint/delta evidence;
- seven domain-neutral synthetic profiles using one core;
- no provider/DCC/cloud/database/network/shell requirement in the M04 kernel.

No arbitrary token/performance percentage may be claimed without deterministic benchmark evidence.

## Future product validation
Unit/integration/E2E; visual/reference quality; anatomy/pose/rig/deformation; temporal consistency/motion smoothness; geometry/topology/material/shader; audio; GPU/VRAM/RAM performance/fallback; DCC integration; export/import reproducibility.

Thresholds/datasets are frozen by the owning modules before their implementations can claim completion.
