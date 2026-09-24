# IRIS Scope

Status: `M10_PLANNING_COMPLETE_IMPLEMENTATION_NOT_ADMITTED`

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
S05 is complete for module planning: PR #73 exact head `fc1fa4959697b88fbfbe303736517aef52d9bc91` passed Governance `36038801813 / 107765474152`, was protected squash-merged as `54d85d3491d4cc21e95fc2f9042c53d2852ceb88`, and passed exact-main Governance `36038905218 / 107765823628`. Its candidate lifecycle preserves owner-issued labels, immutable outcome/dataset/model/evaluation evidence, drift quarantine and reviewable rollback; M10 does not self-label, self-certify, auto-train or silently promote models.
The Final Technology Review completed through PR #74 and passed exact-main Governance at `e38912a57c2d452badd5a35a031eb78f95d0e899`. The M11–M60 Forward Compatibility Scan completed through PR #75: exact head `d55ea04a9663b648805b00ea0032773125c65642` passed Governance `36041422592 / 107774247740`, protected squash merge `2328978175a59768e64687748b259027b3a79d4e` passed exact-main Governance `36041515972 / 107774565519`; coverage is 50/50 at module-index level with FC-10-01 through FC-10-12. Individual M11–M60 contracts are absent and require revisit during their own planning lifecycles. The independent audit approved promotion of the M10 semantic contract with 0 HIGH and 0 CRITICAL findings. PR #77 exact head `57dc0410e9c434a04657b8f57562febdeceb84f1` passed Governance `36043928118 / 107782644258`; protected squash merge `8a3e32de28ccc824c165e29bfa3da4f6cc305de0` passed exact-main Governance `36044190420 / 107783526436` (actor: KayzenRoot). M10 planning is complete at `m10-contract-v1.0`; implementation remains NOT ADMITTED.

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

If M10 implementation is pursued, create and admit a separate implementation Work Order / Context Lock / Evidence package and pass preflight. Keep M10 implementation NOT ADMITTED until then.

## IRIS 1.0 product scope

IRIS 1.0 continues to include M00-M60. M01-M09 implementations are complete; M10 planning is complete under Issue #68 with contract `m10-contract-v1.0` frozen. M10 implementation and later modules remain gated by separate admitted Work Orders and their required preflight.
