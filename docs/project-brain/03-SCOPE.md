# IRIS Scope

Status: `M09_IMPLEMENTATION_ADMITTED`

## Current governed increment — M09 implementation

M01-M08 are durably closed. M09 Resource Digital Twin & Dynamic VRAM Governor planning is frozen and approved as `m09-contract-v1.0`. IRIS-WO-0013 is admitted for execution on PR #65 from authorized base `ee46815382be0907f373760a62b3b31805c7abee`.

M09 implementation scope is exactly the frozen contract: 514 hard invariants, 83 independent mandatory surfaces, 15 mandatory absorbed components and FC-09-01..14 compatibility handshakes. M09 owns resource-state/accounting, leases/reservations/residency, bounded mobility/offload/prefetch contracts, resource-shape feasibility/control state and bounded pressure/recovery/leak semantics.

M09 does not own M10 execution planning/predictive OOM/thermal policy, M11 process lifecycle, M12 placement/orchestration, M14 model fitness, M53/M54 rights/security policy, M55 physical storage/delete, M56 observability aggregation, M01 quality authority or M03 protected semantic authority.

### NOT ADMITTED
- M10+ implementation;
- silent quality, precision, fidelity or protected-semantic degradation under scarcity;
- unrelated process termination/suspension or external allocation theft;
- physical storage deletion by M09;
- fabricated resource, provider, reclamation or physical-measurement evidence;
- frozen-contract semantic changes without versioned amendment.

### Next governed step
Execute IRIS-WO-0013 completely, validate and independently audit PR #65, then merge only through protected gates. Do not start M10 implementation during M09 execution.

## IRIS 1.0 product scope

IRIS 1.0 continues to include M00-M60. M01-M08 implementations are durably closed. M09 implementation is the active governed increment under IRIS-WO-0013. M10+ remain gated by the official module lifecycle.
