# IRIS-WO-0023: M12 S02 Placement, Queues, Quotas and Priority Research

Status: ADMITTED_FOR_SEPARATE_BOUNDED_S02_REFERENCE_RESEARCH_ONLY | Issue #128 | Risk ELEVATED_OWNER_BOUNDARY_RESEARCH
Git exact base `032dcda35df48d53012b3b32fdabb78de17c2b41`, tree `b83f0e8c1572fe2164baee606f0653116e1be2b5`; exact-main Governance #485 run 36324884488/job 108635619085 PASS 3979/3979. Branch `iris-wo-0023-m12-s02-queue-placement-planning-20260927`.

## Source gate and provenance
Canonical source hierarchy Checkpoint → Decisions → Scope → DoD → Architecture → Requirements, plus Security and active Work Order. 41/41 exact base Git blobs pinned, eight mandatory roots and 12/12 changed paths required by CI. IRIS v1.0.3 is an external read-only context reference only, not a live handshake or runtime upgrade. Existing pinned GEF/IRIS bridges remain unchanged. Official design references for planning only: Kubernetes Scheduling Framework https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/ ; Kueue resource-flavor queues https://kueue.sigs.k8s.io/docs/concepts/cluster_queue/ ; Ray bundle groups https://docs.ray.io/en/latest/ray-core/scheduling/placement-group.html . No dependency installation/selection.

## Admission and exact deliverables
S01 source research legitimately completed through PR #129 head Governance #484 and main #485. Reconcile this factual state into prior Evidence Bundle, canonical checkpoint/backlog/scope and M12 module plan **as part of this new substantive S02 step**. S02 research must compare six unselected queue/policy options (FIFO, priority/aging, weighted fairness, bounded backfill, hard flavors/quotas, gang co-placement) with tradeoffs and unsafe counterexamples, and separate M02 accepted intent, M06 operational attempt/outcome, M09 current exact grant, M11 worker/OS evidence, M12 candidate ranking and M54/M60 authorization. Produce 20 source-routed OPEN/UNRATED owner questions and 14 future negative/ambiguity oracles SPECIFIED_NOT_EXECUTED. S03/S04/S05 handoffs explicit and no quota, numerical priority, selection, process/GPU/host action or exposed API.

## Strict changed-file allowlist (12)
- `docs/project-brain/03-SCOPE.md`
- `planning/modules/M12-COMPUTE-ORCHESTRATION.md`
- `planning/research/M12-S02-PLACEMENT-QUEUES-QUOTAS-PRIORITY.md`
- `.engineering/CHECKPOINT.json`
- `.engineering/CHECKPOINT.md`
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/14-BACKLOG.md`
- `.engineering/evidence/IRIS-WO-0022.json`
- `.engineering/evidence/IRIS-WO-0023.json`
- `.engineering/context-locks/IRIS-WO-0023-M12-S02-PLANNING.json`
- `.engineering/work-orders/IRIS-WO-0023-M12-S02-PLANNING.md`
- `planning/reviews/IRIS-WO-0023-M12-S02-AUDIT-TARGET.md`

## STOP and proof
No alteration of any frozen module contract, M09 owner option A/B/C, H01–H04 freeze blockers, M11 v0.2, process/OS operation, worker registry runtime, resource mutation, network call, internal IRIS installed state, scheduler implementation, optimistic grant or default algorithm. Both checkpoint Markdown mirrors byte-identical and JSON nextStep exact. Full preexisting 3979/3979 suite, exact-head source lock/validator/GEF/IRIS checks; separate bounded review must detect no newly introduced HIGH/CRITICAL in **this documented S02 reference only**. Guarded squash merge with same reviewed final HEAD and base, exact-main Governance, postmerge issue/comment receipts. Issue #128 remains OPEN until S03–S05, FTR/FCS/owner contract and actual freeze if ever separately admitted; #82/#110/#112 remain OPEN with no process implementation.
