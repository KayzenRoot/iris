# IRIS-WO-0015 — M11 Forward Compatibility Scan

Status: EXECUTION RECORD — proposal only
Issue: #82 (must remain OPEN)
Input: IRIS-WO-0015-M11-FORWARD-COMPATIBILITY-SCAN-C01-2026-09-26.pdf
Module: M11 Background Worker Fabric & Process Lifecycle
Increment: M11 forward compatibility scan, C01

## Objective

Record a source-backed compatibility scan across frozen M02, M06, M09 and M10 owner sources and every M12–M60 module-index candidate. Keep owner authority boundaries intact, identify missing contracts as pending rather than infer their semantics, and bind the proposal to the exact main base.

## Admission and preflight

- Base SHA: b3fc093cfc5b5370872dacc7ff6694af6bcfd1cd.
- Base tree: be410381b1e940aa906ebceb7ba89520353a52e5.
- Branch: iris-wo-0015-m11-forward-compatibility-scan-20260926.
- Issue #82 was verified OPEN.
- Base Governance #425 (run 36272216363, job 108488207459) passed on the exact SHA/tree, including checkout assertion, validator, GEF/HIVE bridges and 3,940/3,940 tests (10.336 seconds).
- New Context Lock: 88/88 unique, present exact-base Git blob fingerprints, including the two prior closeout source files; nine prior hashes were rebound to this base.
- HIVE’s registered checkout is stale at an older M09 head; context build rejected the request and checkpoint/context reads timed out. No current HIVE result is asserted.

## Execution checklist

1. Read source hierarchy and canonical checkpoint; inspect Decisions, Scope, Definition of Done, Architecture, Requirements, Integration Contracts, frozen M02/M06/M09/M10 sources, all M11 S01–S05 research and planning records, FTR/C01 closeout, Issue #82, prior M09/M10 scans, evidence, backlog and M12–M60 index headings.
2. Record a 30/30 source matrix. For each M12–M60 heading, record owner/module, exact index source, version/status, evidence depth, only the source-backed fact, M11-facing handoff, disposition, risk, candidate effect, question/owner and revisit trigger. Expected total: 49/49, each INDEX_ONLY and PENDING_OWNER_CONTRACT.
3. Carry M09/M10 findings only where M11 S03/S05 and available canonical sources establish the boundary: process liveness is not resource/lease truth; planner recommendation is not execution authorization.
4. Keep missing M12–M60 owner details, S04-U01–U21 and S05-U01–U23 pending/open. Do not invent IPC, identity, process state, cancellation, timeout, retry, recovery, priority, concurrency, cleanup, platform, event, authorization, or resource policy.
5. Update the evidence bundle, both checkpoint markdown mirrors, checkpoint JSON, M11 plan, planning Work Order, backlog, and module plan. Preserve status/phase/version; checkpoint nextStep must exactly equal the final Markdown section body; Markdown mirrors must be byte-identical.
6. Validate the exact authorized path set, 88/88 lock, JSON syntax, git diff --check, governance validator, pinned GEF preflight and full repository test suite. Recheck Issue #82 OPEN.
7. Create one PR to main, include Refs #82, verify its base, head and exact ten-file set, and wait for Governance on that exact PR head. Verify exact-checkout assertion, validator, GEF/HIVE bridges and the 3,940-test baseline. Do not substitute a result from another SHA.
8. Stop only when exact-head Governance is PASS and the PR is OPEN and UNMERGED.

## Scope boundary

Planning and evidence only. No freeze, M11/M10 implementation admission, technology or policy selection, runtime/process/IPC operation, resource mutation, independent contract audit, next-phase candidate, or Issue #82 closure.

## Authorized changed files — exact allowlist

1. .engineering/CHECKPOINT.json
2. .engineering/CHECKPOINT.md
3. .engineering/context-locks/IRIS-WO-0015-M11-FORWARD-COMPATIBILITY-SCAN.json
4. .engineering/evidence/IRIS-WO-0015.json
5. .engineering/work-orders/IRIS-WO-0015-M11-PLANNING.md
6. .engineering/work-orders/IRIS-WO-0015-M11-FORWARD-COMPATIBILITY-SCAN.md
7. docs/project-brain/13-CHECKPOINT.md
8. docs/project-brain/14-BACKLOG.md
9. planning/modules/M11-BACKGROUND-WORKER-FABRIC-PROCESS-LIFECYCLE.md
10. planning/compatibility/M11-FORWARD-COMPATIBILITY-SCAN.md

## Required stop conditions

Stop if the authoritative base or any required gate is inconsistent, the exact path set/fingerprints fail, a source conflict changes the bounded scope, the PR head differs from the Governance head, required bridges/tests fail, or the PR is not open and unmerged. Report observed evidence without inventing a workaround or completion claim.
