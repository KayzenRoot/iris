# IRIS-WO-0014 — Implementation Admission Preflight Criteria

Status: `BLOCKED_NOT_RUN`  
Tracking issue: #79  
Base snapshot: `873053d24d9e28f5ff9b186914fa3de7caf749de`  
This is a later admission checklist; it has not been executed.

## Decision rule

Preflight returns `PASS` only when every REQUIRED check passes, critical-source fingerprints match, the base SHA is exact, owner handoffs are approved, and no unresolved HIGH/CRITICAL finding remains. Unknown, missing, stale or conflicting mandatory evidence returns `BLOCKED`/abstain. No partial pass authorizes execution.

Current result: **BLOCKED** — 50 individual M11–M60 owner contracts are absent, and M10 deferred owner decisions remain unresolved.

## Gate A — Authority and scope

| Check | Required evidence | Current state |
| --- | --- | --- |
| M10 contract | `m10-contract-v1.0`, 36 clauses, exact-main evidence | PASS at proposal base; revalidate at admission |
| M01/M02/M03/M06 | Frozen contracts and hard quality, plan, semantic and operational-state boundaries | Available; adapter details still require review |
| M07/M08/M09 | Owner version, scope, freshness and invalidation on consumed evidence | Owner sources available; revalidate exact integrations |
| M11–M60 register | All 50 rows closed against canonical owner contracts | **BLOCKED: individual contracts absent** |
| No authority bypass | No worker, placement, provider, resource control, routing, release, security or API authority transferred to M10 | Must verify each relevant owner contract |

## Gate B — Deferred decisions

These may not be silently defaulted. Resolve by owner contract, approved evidence, or an approved scope change:

- M02/M11/M12 plan acceptance, process lifecycle and placement handshakes.
- M09 resource claim/reservation boundary and M16 provider capability/qualification.
- M01/M14/M24/M48 labels, model fitness, evaluation and approvals.
- M15/M50 model routing and cross-stage cost-to-quality objectives.
- M51 benchmark protocol, label handoff and physical-evidence acceptance.
- M53/M54 rights, authorization, consent, privacy, access, retention, redaction and deletion projection.
- M56 event/replay schema; M57 agent invocation/stops; M58 API/SDK/MCP permissions and compatibility; M60 recovery/final acceptance.
- Estimator families, targets/horizons, calibration method, support/freshness/uncertainty/drift/OOD policy and numeric risk budgets.
- Record serialization, digest, storage, retention and public/internal projections.
- Any shadow/canary measurement, online learning, rollout, automatic promotion or autonomous dispatch.

Current state: **BLOCKED**.

## Gate C — Context Lock freshness

1. Select exact main SHA and create a dedicated implementation branch only after admission review.
2. Recompute Git blob SHA-1 for every critical source in `.engineering/context-locks/IRIS-WO-0014.json`.
3. Recompile if checkpoint, Scope, DoD, Architecture, Requirements, decisions, frozen/owner contract, security/test policy, or approved interface changes.
4. Verify origin, clean base, merge-base and ancestry; do not rewrite history.
5. Any mismatch or moved base returns `STALE_CONTEXT`; stop and rebuild before executor work.

Current state: **PROPOSAL SNAPSHOT ONLY**.

## Gate D — Baseline and verification

Before any implementation change:

- Run `python -m unittest discover -s tests -p "test_*.py"`; compare with the last known 3940/3940 and explain baseline drift.
- Record Python/tool versions, exact focused test command and full-suite count.
- Pin focused M10 tests, compile, configured lint/type checks, governance validator and integration commands.
- Prove all 36 invariants, unknown/fail-closed branches, owner scope/freshness/invalidation, distinct risk targets, policy modes, receipts, drift, abstention, replay and privacy.
- Run authority-firewall checks for worker/process, placement, provider, resource-control, public API, online training and release boundaries.
- Synthetic fixtures are semantic/mechanical evidence only. Physical claims require separately authorized hardware evidence and M51/M60 owner acceptance.

Current state: **NOT RUN**.

## Gate E — Separate admission

Before executor access, record:

- closed owner-contract register with exact paths, versions and fingerprints;
- bounded allowed/no-go file inventory;
- resolved decisions for the selected scope;
- refreshed Context Lock with zero critical-source mismatches;
- exact base and full-suite baseline;
- separate Work Order review verdict `APPROVED`, zero residual HIGH/CRITICAL;
- complete, auditable preflight evidence.

Only after all required gates pass may an executor receive a complete prompt, delivered as a downloadable PDF under repository policy. This proposal does not satisfy admission and grants no implementation authority.
