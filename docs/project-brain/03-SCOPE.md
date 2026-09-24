# IRIS Scope

Status: `M09_IMPLEMENTATION_CLOSED`

## Current governed state — M09 closure complete

M01-M09 implementations remain durably closed. The M09 Resource Digital Twin & Dynamic VRAM Governor implementation is complete under frozen contract `m09-contract-v1.0`, with 83/83 independent mandatory surfaces, 15/15 absorbed components, 514/514 hard-invariant proofs and FC-09-01..14. PR #65 was independently audited at exact head `e52d3fdafe5ac142d41b35f45a768f7f8840dd74`, protected-merged to `main` as `d4ebf87c266d6de04a4e978fa6b8ad8fa958618c`, and exact-main Governance passed.

The documentation/evidence-only closure reconciliation in PR #66 passed exact-head Governance on `8c1fe7ff4b3ad8da74194ee15d5466341b578025` (run 36025800675, job 107721889592), was protected squash-merged as `e8ab43f42981630bad244a1d932e60e4ac584b2e`, and passed exact-main Governance (run 36027974675, job 107729242412). M09 closure reconciliation is complete. No M09 implementation changes remain in scope.

M09 owns resource-state/accounting, leases/reservations/residency, bounded mobility/offload/prefetch contracts, resource-shape feasibility/control state and bounded pressure/recovery/leak semantics. It does not own M10 execution planning/predictive OOM/thermal policy, M11 process lifecycle, M12 placement/orchestration, M14 model fitness, M53/M54 rights/security policy, M55 physical storage/delete, M56 observability aggregation, M01 quality authority or M03 protected semantic authority.

## M10 planning and implementation gates

M10 — Adaptive Execution Planner & Predictive OOM/Thermal Shield — is the next planning module. Its planning lifecycle is eligible to begin through a separate bounded Work Order; no M10 planning Work Order is admitted in this checkpoint. M10 implementation remains NOT ADMITTED and NOT STARTED until the five-session planning cycle, contract freeze, final technology review, forward-compatibility scan, independent planning audit, and separate implementation Work Order admission/preflight are complete.

### NOT ADMITTED

- M10 implementation before its planning contract and separate implementation admission gates pass;
- M11+ implementation before the official module lifecycle admits it;
- silent quality, precision, fidelity or protected-semantic degradation under scarcity;
- unrelated process termination/suspension or external allocation theft;
- physical storage deletion by M09;
- fabricated resource, provider, reclamation or physical-measurement evidence;
- frozen-contract semantic changes without versioned amendment.

### Next governed step

Create and admit a separate bounded M10 planning Work Order, then complete S01-S05 and the required planning reviews. Do not start M10 implementation during planning.

## IRIS 1.0 product scope

IRIS 1.0 continues to include M00-M60. M01-M09 implementations are complete; M09 is durably recorded from PR #65 and the exact-main validated closure reconciliation in PR #66. M10+ implementation remains gated by the official module lifecycle and a separate admitted implementation Work Order.
