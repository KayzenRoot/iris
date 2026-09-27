# M11 C03 — Decision and Proof Coverage Matrix

Status: PROPOSED_FOR_REVIEW; IRIS-WO-0015; Issue #82 OPEN
Exact base: `754fdf95878b1def4b5800a1a50cbb4e9c72957c`, tree `47434c004bcfc9f0cab7c5158aacf2cdf40b57ca`.

## Prior governed receipt

PR #105 exact head `22da8291204ad08e9f595a7ee589001f45208ca6` passed Governance #443 (run 36289449205, job 108536580915; 3,940/3,940). Protected squash merge: `754fdf95878b1def4b5800a1a50cbb4e9c72957c`. Exact-main Governance #444 (run 36291757526, job 108543056517; 3,940/3,940).

## Source-backed complete intake

| Original question source | Open questions |
| --- | ---: |
| S01 long-lived supervisor and process identity | 10 |
| S02 startup/IPC | 12 |
| S03 concurrency/resource admission | 20 |
| S04 reaper/OS process rights | 21 |
| S05 cancellation/recovery/workstation coexistence | 23 |
| **Total (86 distinct IDs)** | **86** |

The machine-readable `.engineering/evidence/M11-C03-DECISION-PROOF-REGISTER.json` contains each original question verbatim, exact source filename/blob SHA-1 and OPEN/UNRATED/owner-decision-PENDING state. The 44 S04/S05 questions match the unchanged v0.2 candidate verbatim, 44/44. Do not reinterpret missing M12/M54/M60 contracts as zero risk.

## Critical owner gates

- M02/M06: exact ExecutionPlan causality, attempt cardinality, outcomes and replay/idempotency authority remain theirs.
- M09/M12: grants/leases/resource truth belong to M09, placement/aggregate queue and multi-host contracts to future M12; no inferred grant or local placement.
- M54/M60: principal/action authorization and OS process ownership, rights, wait/reap/descendant containment and supported-platform contracts are pending. No PID-based authorization.
- M26/M48/M53/M55/M56/M58/M59: future index-level owners decide provider operation, quality, rights, storage, telemetry and publication. Process exit is not success, output acceptance or cleanup.

## Existing proof obligations (not executed)

| ID | Future negative scenario | Status |
| --- | --- | --- |
| PO-C02-01 | No M54 permission | SPECIFIED_NOT_EXECUTED |
| PO-C02-02 | Stale/conflicting M09 grant | SPECIFIED_NOT_EXECUTED |
| PO-C02-03 | Unknown M12 placement | SPECIFIED_NOT_EXECUTED |
| PO-C02-04 | PID reuse/foreign handle | SPECIFIED_NOT_EXECUTED |
| PO-C02-05 | Cancellation/IPC timeout without exit proof | SPECIFIED_NOT_EXECUTED |
| PO-C02-06 | Supervisor crash and ambiguous external effects | SPECIFIED_NOT_EXECUTED |
| PO-C02-07 | Partial output after process exit | SPECIFIED_NOT_EXECUTED |
| PO-C02-08 | Unsupported POSIX/Windows descendant containment | SPECIFIED_NOT_EXECUTED |

## Precise gates

1. This increment is traceability only. Complete exact-head Governance and separate bounded review before merge and exact-main validation.
2. Future semantic freeze: each open question needs an owner-sourced disposition or an explicitly reviewed safe, non-executable deferral; an independent audit judges if any HIGH/CRITICAL remains. No default owner policy is invented.
3. Future runtime admission: separate Work Order, admitted M02/M06/M09/M12/M54/M60 owner proofs, OS/platform and negative tests, exact-head Governance and independent implementation audit. Documentation CI never grants worker startup, process control, cleanup or replay.

Current candidate `m11-contract-candidate-v0.2` remains PROPOSED_NOT_FROZEN; M10/M11 implementation NOT_ADMITTED; every callable process operation DISABLED; Issue #82 OPEN. No OS/IPC/platform defaults selected.
