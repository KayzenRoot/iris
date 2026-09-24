# IRIS Scope

Status: `M10_PLANNING_ACTIVE`

## Current governed increment — M10 planning

M01-M09 implementations are durably closed. M09 closure reconciliation passed exact-main Governance on `e8ab43f42981630bad244a1d932e60e4ac584b2e`.

M10 — Adaptive Execution Planner & Predictive OOM/Thermal Shield — is admitted for planning only under [Issue #68](https://github.com/KayzenRoot/iris/issues/68), from exact validated main `b6456670a7c61621db1d3b3fc6d55487adb9cd64` (Governance `36029536926 / 107734488887`, PASS). M10 S01 Workload Signature Engine is complete for module planning. No M10 product/runtime implementation is authorized.

S01 defines versioned workload signatures as typed projections of workload shape and pinned upstream evidence. It preserves source ownership: M02 owns the canonical ExecutionPlan contract; M01 and M03 own quality and protected semantic contracts; M07, M08 and M09 own hardware, empirical capability and resource truth respectively. M10 consumes these references and must not rewrite or self-certify them.

## M10 planning boundary

Planning covers the five canonical sessions: Workload Signature Engine; hardware-aware execution plan compilation; predictive OOM, thermal and quality-risk models; ECO/BALANCED/QUALITY/MAX/CUSTOM policy semantics; and observed-result learning with explainable decisions.

M10 planning must define explicit behavior for unknown, stale, conflicting, unsupported and out-of-distribution evidence. It must separate predictions for OOM, thermal behavior and quality risk, preserve provenance and uncertainty, and define a no-safe-plan result. M11 worker lifecycle, M12 placement, M13 cache/performance, M14 model fitness, M16 provider compilation, M50 cost/quality routing, M54 security and M56 observability remain separate authorities.

### NOT ADMITTED

- M10 product/runtime implementation before S01-S05, contract freeze, final technology review, M11-M60 compatibility scan, independent planning audit and separate implementation admission/preflight;
- M11+ implementation before the official module lifecycle admits it;
- silent quality, precision, fidelity or protected-semantic degradation under scarcity;
- treating workload similarity, synthetic fixtures or incomplete telemetry as physical truth;
- worker/process control, workload placement or provider workflow compilation by M10;
- frozen-contract semantic changes without a versioned amendment.

### Next governed step

Complete S02 hardware-aware plan compilation, then S03-S05 and all planning gates. Keep this increment planning-only.

## IRIS 1.0 product scope

IRIS 1.0 continues to include M00-M60. M01-M09 implementations are complete; M10 planning is active under Issue #68. M10 implementation and later modules remain gated by the official module lifecycle and separate admitted Work Orders.
