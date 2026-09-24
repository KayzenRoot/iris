# IRIS Scope

Status: `M10_PLANNING_ACTIVE`

## Current governed increment — M10 planning

M01-M09 implementations are durably closed. M09 closure reconciliation passed exact-main Governance on `e8ab43f42981630bad244a1d932e60e4ac584b2e`.

M10 — Adaptive Execution Planner & Predictive OOM/Thermal Shield — is admitted for planning only under [Issue #68](https://github.com/KayzenRoot/iris/issues/68), from exact validated main `b6456670a7c61621db1d3b3fc6d55487adb9cd64` (Governance `36029536926 / 107734488887`, PASS). M10 S01 Workload Signature Engine is complete for module planning. No M10 product/runtime implementation is authorized.

S01 defines versioned workload signatures as typed projections of workload shape and pinned upstream evidence. It preserves source ownership: M02 owns the canonical ExecutionPlan contract; M01 and M03 own quality and protected semantic contracts; M07, M08 and M09 own hardware, empirical capability and resource truth respectively. M10 consumes these references and must not rewrite or self-certify them.

S02 planning is complete for module planning: PR #70 exact head `0fa18f55d845192d4225751ec14316af08ec6dad` passed Governance `36032894812 / 107745773871`, was protected squash-merged as `8d068d1cf9ef604aef8506ec879b7a382ec1b738`, and passed exact-main Governance `36033011233 / 107746156289`. S02 defines evidence-bound feasibility and bounded plan alternatives through M02's contract. It does not create a competing ExecutionPlan schema, reserve resources, choose a physical placement or compile provider workflows. M07/M08/M09 facts remain owner-issued, scope-pinned inputs; uncertain, stale, conflicting or omitted mandatory evidence yields an explicit indeterminate/no-safe-plan path.

M09 owns resource-state/accounting, leases/reservations/residency, bounded mobility/offload/prefetch contracts, resource-shape feasibility/control state and bounded pressure/recovery/leak semantics. It does not own M10 execution planning/predictive OOM/thermal policy, M11 process lifecycle, M12 placement/orchestration, M14 model fitness, M53/M54 rights/security policy, M55 physical storage/delete, M56 observability aggregation, M01 quality authority or M03 protected semantic authority.

## M10 planning boundary

Planning covers the five canonical sessions: Workload Signature Engine; hardware-aware execution plan compilation; predictive OOM, thermal and quality-risk models; ECO/BALANCED/QUALITY/MAX/CUSTOM policy semantics; and observed-result learning with explainable decisions.

M10 planning must define explicit behavior for unknown, stale, conflicting, unsupported and out-of-distribution evidence. S03 is complete for module planning: PR #71 exact head `db9fc7e0f0e7615c075cfaee3debec3a3990697b` passed Governance `36034416554 / 107750841548`, was protected squash-merged as `8768661ee348815ec5b1eb6e32bc85505fa10b17`, and passed exact-main Governance `36034538318 / 107751237481`. Its three separately labeled outputs cover validated allocation-failure/OOM risk, thermal-limit/throttle risk distinct from power-limit behavior, and M01 Fidelity Contract violation risk. Each estimate retains exact scope, provenance, freshness, calibration, uncertainty and applicability; unsupported, stale, conflicting or drifting evidence produces abstention/indeterminate/no-safe-plan.
S04 is complete for module planning: PR #72 exact head `add4344d6b1a495f1aeeb23af0d57fdcddde381e` passed Governance `36037625164 / 107761547909`, was protected squash-merged as `96aee147e701c6d716cfbcf5f2be524ee5d751e7`, and passed exact-main Governance `36037710495 / 107761836741`. Its ECO/BALANCED/QUALITY/MAX/CUSTOM preferences apply only after hard M02/M01/M03 and owner-issued M07/M08/M09/M50/M54 gates. Preferences, objectives, units, risk-budget references and fallback are explicit and versioned; unresolved trade-offs remain bounded alternatives or no-safe-plan.
S05 observed-result learning and explainable decisions are now a planning candidate. M10 consumes immutable, owner-issued outcome receipts; preserves prediction/observation/label separation; freezes dataset/model/evaluation lineage; and requires independent owner review, drift quarantine and reproducible rollback. M10 does not self-label, self-certify, auto-train or silently promote models. M11 worker lifecycle, M12 placement, M13 cache/performance, M14 model fitness, M16 provider compilation, M50 cost/quality routing, M54 security and M56 observability remain separate authorities.

### NOT ADMITTED

- M10 product/runtime implementation before S01-S05, contract freeze, final technology review, M11-M60 compatibility scan, independent planning audit and separate implementation admission/preflight;
- M11+ implementation before the official module lifecycle admits it;
- silent quality, precision, fidelity or protected-semantic degradation under scarcity;
- unrelated process termination/suspension or external allocation theft;
- physical storage deletion by M09;
- fabricated resource, provider, reclamation or physical-measurement evidence;
- treating workload similarity, synthetic fixtures or incomplete telemetry as physical truth;
- worker/process lifecycle control, workload placement or provider workflow compilation by M10;
- frozen-contract semantic changes without a versioned amendment.

### Next governed step

Pass the S05 learning candidate through exact-head Governance, protected squash merge and exact-main validation; then complete Final Technology Review and the remaining planning gates. Keep this increment planning-only.

## IRIS 1.0 product scope

IRIS 1.0 continues to include M00-M60. M01-M09 implementations are complete; M10 planning is active under Issue #68. M10 implementation and later modules remain gated by the official module lifecycle and separate admitted Work Orders.
