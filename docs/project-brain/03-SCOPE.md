# IRIS Scope

Status: `M09_IMPLEMENTATION_CLOSED`

## Current governed increment — M09 closure reconciliation

M01-M08 implementations remain durably closed. The M09 Resource Digital Twin & Dynamic VRAM Governor implementation is complete under frozen contract `m09-contract-v1.0`, with 83/83 independent mandatory surfaces, 15/15 absorbed components, 514/514 hard-invariant proofs and FC-09-01..14. PR #65 was independently audited at exact head `e52d3fdafe5ac142d41b35f45a768f7f8840dd74`, protected-merged to `main` as `d4ebf87c266d6de04a4e978fa6b8ad8fa958618c`, and exact-main Governance passed.

The active increment is the documentation/evidence-only closure reconciliation in PR #66, based on that exact `main` commit. Its checkpoint delta remains proposed until PR #66 is independently reviewed, passes exact-head Governance, is protected-merged and its merge commit passes exact-main Governance. No runtime, test, script or product implementation changes are in scope for this reconciliation.

M09 owns resource-state/accounting, leases/reservations/residency, bounded mobility/offload/prefetch contracts, resource-shape feasibility/control state and bounded pressure/recovery/leak semantics. It does not own M10 execution planning/predictive OOM/thermal policy, M11 process lifecycle, M12 placement/orchestration, M14 model fitness, M53/M54 rights/security policy, M55 physical storage/delete, M56 observability aggregation, M01 quality authority or M03 protected semantic authority.

### NOT ADMITTED

- M10 planning or implementation before PR #66 closure gates pass and a separate M10 planning Work Order is admitted;
- M11+ implementation before the official module lifecycle admits it;
- silent quality, precision, fidelity or protected-semantic degradation under scarcity;
- unrelated process termination/suspension or external allocation theft;
- physical storage deletion by M09;
- fabricated resource, provider, reclamation or physical-measurement evidence;
- frozen-contract semantic changes without versioned amendment.

### Next governed step

Complete independent review and exact-head Governance for PR #66. If approved, merge only through protected gates and require exact-main Governance on its merge commit. Only after those gates may a separate M10 planning Work Order begin. Do not admit or start M10 planning or implementation before then.

## IRIS 1.0 product scope

IRIS 1.0 continues to include M00-M60. M01-M09 implementations are complete; M09 is durably recorded from PR #65 and its exact-main validation. M10+ remain gated by the official module lifecycle and a separate admitted Work Order.
