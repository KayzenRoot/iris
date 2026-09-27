# IRIS-WO-0015 — M11 Separate Planning Audit C01

Status: AUDIT_PROPOSAL_PENDING_EXACT_HEAD_GOVERNANCE | Risk: ELEVATED | Issue: #82 OPEN
Exact base 9c7cafcfc73700728981f8f90e27110be8dd9fd0 / tree b1b3084905b6f5f81212fcafce3b6509a3d02832; branch iris-wo-0015-m11-audit-c01-20260926.

## OBJECTIVE
Audit the merged versioned M11 C01 semantic owner-contract candidate against available canonical owner contracts, S01–S05 research, FTR, FCS, authority boundaries and Issue #82 freeze-acceptance criteria. Publish exact, severity-scoped findings and corrective proof obligations without changing the candidate.

## CONTEXT / FILES / SOURCE ORDER
Checkpoint → Decisions → Scope → DoD → Architecture → Requirements → applicable source-contracts; inspect the 30-source exact-base Context Lock, prior C01 candidate PR #101, Governance #436 and exact-main #438, original 44 S04/S05 questions, all 49 index-only future-owner headings and Issue #82 OPEN. HIVE-derived checkout may be stale; canonical Git prevails.

## SCOPE / REQUIREMENTS
Read-only contract audit report, source fingerprints, Evidence Bundle and checkpoint/backlog/module audit handoff; classify actionable missing positive interface/authority obligations for freeze. Distinguish historical passing docs CI from unavailable real-process/OS/security proof.

## OUT OF SCOPE / ARCHITECTURE CONSTRAINTS
No edit to M11 candidate, runtime, test, script, IPC, worker processes, resource grants, frozen M10, external owner contracts or Issue #82. Do not infer M12/M54/M60 permissions, identity or OS capability. No contract freeze or implementation admission.

## ACCEPTANCE CRITERIA / TESTS
Exact base/head binding; 30/30 unique Git blob fingerprints; compare 26 unique M11 invariants and 21/21+23/23 verbatim open questions; list severity, evidence, owner and correction proof for each finding; exact 10-file diff allowlist; checkpoint mirrors and JSON match; JSON parse, git diff --check, governance validator, pinned GEF/HIVE bridge and 3,940-test exact-head suite. Review findings separately before protected merge; exact-main Governance required to canonize the report.

## DELIVERABLES / REVIEW FORMAT
One ten-file audit PR with stable finding IDs AUD-C01-H01..H03, Context Lock, Evidence Bundle, checkpoint delta and Brazilian Portuguese review verdict. Corrections belong to later C02 with its own bound head and re-audit.

## STOP CONDITION
Do not start C02, freeze or implement until audit exact-head CI, review, protected merge and exact-main Governance complete; stop on stale base, missing fingerprint, unapproved scope expansion, failed CI or false authority claim.

## AUTHORIZED FILES
- `.engineering/CHECKPOINT.json`
- `.engineering/CHECKPOINT.md`
- `.engineering/context-locks/IRIS-WO-0015-M11-PLANNING-AUDIT-C01.json`
- `.engineering/evidence/IRIS-WO-0015.json`
- `.engineering/work-orders/IRIS-WO-0015-M11-PLANNING-AUDIT-C01.md`
- `.engineering/work-orders/IRIS-WO-0015-M11-PLANNING.md`
- `docs/project-brain/13-CHECKPOINT.md`
- `docs/project-brain/14-BACKLOG.md`
- `planning/reviews/M11-INDEPENDENT-PLANNING-AUDIT-C01.md`
- `planning/modules/M11-BACKGROUND-WORKER-FABRIC-PROCESS-LIFECYCLE.md`
