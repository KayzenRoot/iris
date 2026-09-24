# IRIS-WO-0014 — M10 Implementation Admission Proposal

Status: `PROPOSED_NOT_ADMITTED`  
Risk: `ELEVATED`  
Tracking issue: [#79](https://github.com/KayzenRoot/iris/issues/79)  
Proposal base: `873053d24d9e28f5ff9b186914fa3de7caf749de`  
Frozen semantic contract: `m10-contract-v1.0`  
Implementation authority: **NOT ADMITTED**

## OBJECTIVE

Prepare a bounded proposal for a future implementation increment of the frozen M10 semantic contract, including a proposal-time Context Lock, Evidence Bundle plan, exhaustive M11–M60 owner-contract dependency register, and deterministic preflight criteria.

This defines a possible future implementation Work Order. It does not admit that Work Order, create an implementation branch, or authorize runtime changes.

## CONTEXT

M10 planning is complete on the exact main base above. The semantic contract `m10-contract-v1.0` is `FROZEN_APPROVED` with 36 normative clauses, FC-10-01..12 traceability, and independent audit findings HIGH 0 / CRITICAL 0. Its exact freeze promotion and post-merge reconciliation passed Governance.

The contract explicitly defers serialization/storage/projection, estimators and calibration, numeric risk budgets, and owner-specific integration handshakes. Section 8 requires owner-specific M11–M60 handoffs to be checked against their canonical contracts before any implementation Work Order is admitted.

Frozen contract artifacts exist for M01–M06 and M10. M07–M09 use their frozen `m07-contract-v1.0`, `m08-contract-v1.0`, and `m09-contract-v1.0` owner documents/implementation records and admitted Work Orders; their canonical source paths are pinned in the Context Lock. They do not have duplicate files under `planning/contracts/`. No individual M11–M60 module plan or frozen contract exists at this proposal base.

## SCOPE

This proposal covers documentation only:

- define the future Work Order boundary and source hierarchy;
- pin 47 critical Git sources by blob SHA-1 at the proposal base;
- preserve the frozen 36-clause M10 contract as the only normative semantic source;
- register all 50 missing M11–M60 owner contracts and index-level candidate relationships;
- define an Evidence Bundle shape whose state remains proposal-only and unexecuted;
- define preflight checks, blockers, freshness rules and stop conditions;
- propose, but do not apply, a checkpoint delta pending audit approval.

A future implementation package, if separately admitted after all blockers close, may implement only M10-owned semantic planning behavior and approved owner handoffs.

## OUT OF SCOPE

- Runtime/product code, M10 execution, training, model activation, dispatch, reservations, placement, worker/process control, provider execution, publication or API exposure.
- Changes to `m10-contract-v1.0` semantics without a versioned amendment and renewed audit.
- Choosing estimators, calibration, numeric risk budgets, horizons, freshness intervals, support thresholds, serialization, digest, storage, retention or public projection without owner approval.
- Claims of physical safety, real-device accuracy or calibration from synthetic tests.
- Inferring M11–M60 interfaces or authority from the master index or index-level scan.
- Closing planning Issue #68 or changing its scope.

## FILES/SOURCES TO READ

The proposal-time Context Lock pins the canonical startup order and all 47 critical sources. At minimum:

- `.engineering/SOURCE-HIERARCHY.md`
- `docs/project-brain/13-CHECKPOINT.md`, `16-DECISIONS-LEDGER.md`, `03-SCOPE.md`, `15-DEFINITION-OF-DONE.md`, `04-ARCHITECTURE.md`, `02-REQUIREMENTS.md`
- `docs/project-brain/05-INTEGRATION-CONTRACTS.md`, `08-SLOW-PLANNING-PROTOCOL.md`, `09-MODULE-PLANNING-CONSTRUCTION-LIFECYCLE.md`, `10-SECURITY-GOVERNANCE.md`, `11-TEST-BENCHMARK-PLAN.md`
- Frozen M01–M06 contracts and M07–M09 owner docs, module plans, Work Orders and evidence named in the lock
- `planning/MASTER-MODULE-INDEX.md`
- M10 module plan, frozen contract, forward-compatibility scan, final technology review and independent audit
- `.github/workflows/governance.yml`, `scripts/validate_governance.py`, Work Order template and review/prompt delivery policies

If any critical fingerprint differs, mark the Context Lock STALE and rebuild/rebase it before admission.

## REQUIREMENTS

1. Preserve/prove every one of the 36 normative clauses in the frozen contract; create a one-to-one proof map with no missing, duplicate or orphan clause.
2. Bind proposals to M02’s canonical request, graph revision and ExecutionPlan contract; do not create a second schema or alter M02 production state.
3. Preserve M01/M03 hard gates. Unsupported mandatory evidence must produce explicit unknown/abstain/indeterminate/no-safe-plan behavior.
4. Keep OOM/allocation failure, thermal/power and M01 quality-contract risk as distinct typed records. Prediction is not measurement, label, evaluation or approval.
5. Keep ECO/BALANCED/QUALITY/MAX/CUSTOM subordinate to hard constraints; no hidden weights, invented units, silent fallback or unauthorized mode transition.
6. Bind evidence to owner, schema/version, scope, time window, freshness, applicability, provenance, uncertainty and invalidation.
7. Preserve append-only owner-issued outcomes, unobserved non-selected alternatives, offline-only evaluation lineage, quarantine and compatible rollback.
8. Preserve M01/M02/M03/M06/M07/M08/M09 authority. M10 cannot reserve M09 resources, choose M12 placement, control M11 workers, compile M16 provider workflows, own storage, label outcomes or self-promote models.
9. Resolve deferred owner decisions only through the owner’s canonical contract and approved evidence; no local default may fill a gap.
10. Close the exhaustive M11–M60 owner-contract register before implementation admission.

## ARCHITECTURE RULES

- M02 owns production causality and ExecutionPlan; M06 owns operational revision/materialization and reproducibility references.
- M01 owns quality evaluation/promotion; M03 owns protected semantics; M07 discovery, M08 empirical capability and M09 resource state/control remain distinct.
- M10 returns bounded, evidence-linked proposals and decisions only. A proposal is never acceptance, reservation, placement, execution, worker command, provider workflow or release authorization.
- Cross-module facts are versioned owner references; invalid or unsupported mandatory inputs fail closed.
- Keep unresolved serialization/provider/runtime choices out of the semantic layer until owner contracts approve them.

## CONSTRAINTS

- Status remains `PROPOSED_NOT_ADMITTED`; preflight is `BLOCKED`.
- The existing checkpoint remains authoritative until an auditor approves a Checkpoint Delta. This proposal keeps implementation **NOT ADMITTED**.
- All 50 M11–M60 scan rows are candidate requirements, not owner-approved interfaces.
- Exact test/tool commands and environment must be refreshed at future admission. The last known full-suite proof is 3940/3940 at M09 implementation head `15ac24b117c954c0ad6cebd1b618b745858d30b5`. Exact-main comparison shows no `iris_*`, `tests/*`, `scripts/*`, or `examples/*` changes after M09 merge `d4ebf87c266d6de04a4e978fa6b8ad8fa958618c`, but the suite has not been rerun on proposal base `873053d24d9e28f5ff9b186914fa3de7caf749de`.
- Any later complete executor prompt must be a downloadable PDF per `.engineering/PROMPT-DELIVERY-POLICY.md`.

## ACCEPTANCE CRITERIA

### This proposal PR

- Five proposal artifacts are present and internally consistent.
- Context Lock contains exact base SHA and 47 source blob fingerprints; paths exist at the exact base.
- Owner register contains exactly 50 rows (M11–M60), each pending at proposal base.
- Evidence file explicitly says proposal-only, not executed; proof slots are `NOT_CAPTURED`, `NOT_RUN`, or blocked.
- Preflight reports **BLOCKED** while owner contracts/deferred decisions remain unresolved.
- No runtime/tests/generated files or M10 semantics change.
- Proposal commit passes exact-head repository Governance.

### Future implementation completion (not claimed here)

- All 36 frozen invariants map exactly once to meaningful assertions/tests; no gaps, duplicates or orphan proofs.
- Owner-specific interfaces are verified against canonical contracts; no unresolved HIGH/CRITICAL finding remains.
- Focused M10 tests and full suite pass above exact admission baseline; compile, configured lint/type checks and Governance pass.
- Unknown/stale/conflicting/unsupported/revoked/OOD cases fail closed.
- Security/privacy/rights, serialization/versioning/migration, evidence provenance and recovery obligations pass as applicable.
- Exact-head evidence, independent audit, protected squash and exact-main Governance are recorded before any checkpoint claims implementation completion.

## TESTS

### Proposal validation

- No product test suite is claimed for this document-only proposal.
- Require exact-head Governance; it validates repository checkpoint/source consistency and configured GEF/HIVE bridge checks.
- Verify five-file inventory, JSON validity, 47 fingerprints, 50 owner rows, no runtime/test changes, and unchanged frozen M10 contract.

### Future admitted implementation

- Rerun `python -m unittest discover -s tests -p "test_*.py"`.
- Add focused M10 tests: `python -m unittest discover -s tests -p "test_m10_*.py"`.
- Run `python -m compileall -q` for the admitted package, tests and scripts.
- Run configured lint/type checks with exact commands in evidence; do not silently skip configured gates.
- Run `python scripts/validate_governance.py`, exact-head GitHub Governance and full regression suite.
- Synthetic fixtures prove semantic/mechanical behavior only; physical calibration or safety requires separately authorized exact-hardware evidence.

## DELIVERABLES

- `.engineering/work-orders/IRIS-WO-0014-M10-IMPLEMENTATION-PROPOSAL.md`
- `.engineering/context-locks/IRIS-WO-0014.json`
- `.engineering/evidence/IRIS-WO-0014.json`
- `.engineering/work-orders/IRIS-WO-0014-M10-PREFLIGHT-CRITERIA.md`
- `planning/reviews/IRIS-WO-0014-M11-M60-OWNER-DEPENDENCY-REGISTER.md`
- Issue #79 and reviewable documentation PR

## REVIEW FORMAT

Return a Portuguese-BR verdict: `APPROVED`, `CORRECTION REQUIRED`, or `BLOCKED`. Include exact base/head, changed-file inventory, fingerprint result, M11–M60 count, owner-contract gaps, severity/evidence, Checkpoint Delta disposition, and explicit implementation **NOT ADMITTED** state.

## STOP CONDITION

Stop after the documentation proposal passes its review and Governance gates. Do not begin runtime implementation, execute hardware/provider workloads, admit the Work Order, or claim M10 implementation complete. Implementation remains NOT ADMITTED until every blocking owner contract/decision is closed, the Context Lock is refreshed on an exact base, a separate admission review approves bounded scope, and preflight passes.
