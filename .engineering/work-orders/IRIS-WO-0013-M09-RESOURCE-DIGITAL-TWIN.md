# IRIS-WO-0013 — Implement M09 Resource Digital Twin & Dynamic VRAM Governor

Status: `ADMISSION_CANDIDATE`
Risk: `ELEVATED`
Issue: `#64`
Branch: `iris-wo-0013-m09-resource-digital-twin`
Authorized base: `ee46815382be0907f373760a62b3b31805c7abee`
Frozen contract: `m09-contract-v1.0`
Implementation package: `iris_resource_twin/`

## OBJECTIVE
Implement the complete frozen M09 resource-state and dynamic memory-governance kernel. This is not an MVP slice.

The implementation MUST satisfy all **514 hard invariants**, all **83 independent mandatory technology surfaces** and all **15 mandatory absorbed components** frozen by M09 planning.

## AUTHORITY LAW
M09 owns Resource Digital Twin state, capacity/claim accounting, leases/reservations/residency, bounded spill/offload/prefetch contracts, resource-shape feasibility/control state, pressure recovery/accounting/leak semantics and their evidence.

M09 MUST NOT absorb M07 discovery, M08 empirical capability truth, M10 execution-plan selection/predictive OOM/thermal policy, M11 process lifecycle, M12 placement/orchestration, M14 model fitness, M53/M54 rights/security policy, M55 physical storage/delete, M56 observability aggregation, or M01/M03 quality/semantic authority.

## REQUIRED SOURCES
Read in authority order:
1. `docs/project-brain/13-CHECKPOINT.md`
2. `docs/project-brain/16-DECISIONS-LEDGER.md`
3. `docs/project-brain/03-SCOPE.md`
4. `docs/project-brain/15-DEFINITION-OF-DONE.md`
5. `docs/project-brain/04-ARCHITECTURE.md`
6. `docs/project-brain/02-REQUIREMENTS.md`
7. `.engineering/SOURCE-HIERARCHY.md`
8. `.engineering/REVIEW-AUTOFIX-POLICY.md`
9. `.engineering/PROMPT-DELIVERY-POLICY.md`
10. `planning/modules/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md`
11. `planning/reviews/M09-FINAL-TECHNOLOGY-REVIEW.md`
12. `planning/compatibility/M09-FORWARD-COMPATIBILITY-SCAN.md`

Git/code/tests/evidence outrank conversation memory.

## COMPLETE FROZEN SCOPE
Implement all 83 independent mandatory surfaces and all 15 absorbed mandatory components from the Final Technology Review, preserving every invariant **1-514 exactly**.

Required functional families:
- immutable/versioned Resource Digital Twin snapshots, capacity truth, provenance, confidence/UNKNOWN, headroom and conservation;
- typed resource claims, atomic lease/reservation lifecycle, epochs, renewal, tombstones, residency/refcounting, anti-overcommit, fairness/priority evidence and fragmentation;
- typed VRAM/RAM/M55-backed mobility, two-phase verified handoff, transfer integrity, dirty/writeback, partial mobility, cancellation/resume, bounded prefetch and failure quarantine;
- finite tile/chunk/batch/precision feasibility with external quality constraints, provider capability negotiation, hysteresis, epochs, reversibility and explicit no-fit/replan signaling;
- pressure state/hysteresis, suspicion-vs-confirmed leak, liveness references, idempotent stale reconciliation, cooperative release, bounded recovery, Resource Debt, fresh post-recovery reconciliation and safe failure;
- all FC-09-01..14 compatibility handshakes, including composite claims, automation origin, public evidence projection, M55/M56 handshakes and M06 materiality.

## SAFETY / CLOSED CORE
Unknown/stale/conflicted/quarantined mandatory state fails closed. No double-spend/double-free/phantom release. No unrelated process kill/suspend/eviction. No physical storage deletion. No unbounded allocation/search/retry/recovery. No silent precision/fidelity/quality/semantic degradation. No synthetic evidence masquerading as physical resource truth.

## TEST / PROOF REQUIREMENTS
Add focused `test_m09_*.py` suites and deterministic fixtures proving:
- 83/83 independent surfaces + 15/15 absorbed components;
- 514/514 exact invariant proof index with no gaps/duplicates/orphans;
- UNKNOWN/stale/conflict/quarantine fail-closed behavior;
- conservation/headroom/no-overcommit/idempotency/epoch safety;
- lease/reservation/residency lifecycle and composite atomicity;
- verified two-phase mobility and failure preservation;
- quality-safe finite resource shaping and provider negotiation;
- bounded pressure/recovery/leak/debt semantics;
- 8 GB VRAM first-class constrained profiles;
- M07/M08/M10/M11/M12/M14/M53/M54/M55/M56 authority firewall;
- deterministic acceptance evidence bundle.

Required validation:
- compile;
- `python scripts/validate_governance.py`;
- focused M09 suite;
- full `test_*.py` suite;
- configured lint/static checks;
- deterministic M09 fixture/harness;
- exact-head GitHub Governance.

Admission baseline floor is the exact full-suite count measured during preflight. M09 tests MUST increase the final total. Existing tests may not be deleted, skipped or weakened.

## DELIVERABLES
- `iris_resource_twin/` complete kernel;
- focused M09 tests/fixtures;
- invariant/surface/boundary validators;
- domain-neutral constrained-hardware harness;
- `docs/M09-RESOURCE-DIGITAL-TWIN-DYNAMIC-VRAM-GOVERNOR.md`;
- updated `.engineering/evidence/IRIS-WO-0013.json`;
- exact changed-file/test accounting;
- 83+15 implementation/proof map;
- 514-invariant proof map;
- authority-firewall and safety/resource proof;
- proposed checkpoint delta only;
- implementation PR linked to #64.

## PREFLIGHT / ADMISSION
Before product code:
- verify repository/origin/branch;
- verify exact authorized base and merge-base;
- verify all critical fingerprints in `.engineering/context-locks/IRIS-WO-0013.json`;
- run Governance and full baseline suite;
- STOP `STALE_CONTEXT` on any critical mismatch or moved main;
- admission requires exact-head Governance PASS, recorded full-suite baseline and zero critical-source mismatches.

## STOP CONDITION
STOP only when complete frozen M09 is implemented, all 83 surfaces + 15 components + 514 invariants are proven, evidence/docs are complete, PR is ready for independent review, and exact-head Governance is green or deterministically pending and subsequently recorded.

DO NOT MERGE.
DO NOT START M10 IMPLEMENTATION.
If the frozen contract requires semantic change, STOP `BLOCKED_CONTRACT_CONFLICT`.
