# IRIS-WO-0015 C09: M11 reverse owner-liveness and cooperative-release source research

Status: PROPOSED_FOR_SEPARATE_BOUNDED_REVIEW | Risk: ELEVATED | Planning only | Issue #82; dependencies #110/#112
Exact base: `885659cecdd8865bb713f80c1b503583311233e9` | tree: `8767077dbed3599829855373a6bb7da2f829c581` | branch: `iris-wo-0015-m11-c09-reverse-liveness-research-20260927`
C02 prerequisite: PR #116 approved as documentary scan, exact-head Governance #461 PASS, protected merge into this base, exact-main Governance #462 PASS, 3,940/3,940.

## OBJECTIVE
Produce M11-owned *producer-side*, explicitly non-executable semantic boundaries for the reverse M11→M09 owner-liveness/cooperative-release handoff exposed by frozen M09 FC-09-03, while awaiting the actual M09 owner decision. This C09 is substantive owner-specific research, not a substitute for #110 disposition or C02-FR-H01 closure.

## CONTEXT / SOURCE HIERARCHY
Exact Git base, Checkpoint, Decisions, Scope, DoD, Architecture, Requirements and Security first. Re-read frozen M09 FC-09-03, M09 `recovery.py`, M11 v0.2 §§9.1–9.5, C08 and C02 source scans, C02 machine-readable matrix and PR #116 exact CI. Do not treat chat, issue comments or future module index headings as adopted contracts. IRIS MCP project freshness was not verified in this GitHub-only authorship environment; Git is authoritative and CI GEF/IRIS checks remain required.

## SCOPE
(NECESSARY) M11-side source-backed producer semantics: liveness observation, exact owner/process capability binding, freshness/UNKNOWN/refusal handling, cooperative-release receipt/ack distinctions, crash/epoch/race/duplicate-delivery behavior and negative-only provisional status. Map to existing LV-01..06 *without inventing tests or claiming they ran*. Reconcile exact C02 #461/#462 receipt in checkpoint and evidence. Source-lock the exact base and limit change to 11 documentation/evidence paths.

## OUT OF SCOPE
No freeze or adoption of the M09 C01 grant-evidence receipt; no owner decision or topology A/B/C selection; no OS/IPC/crypto/TTL/lease mutation/kill/reap/launch; no `iris_resource_twin/`, M11 runtime, frozen contract, 514 proofs, tests or scripts edits. Do not add a second M09 authority, positive grant, M06 attempt outcome, M12 placement, M54 security policy, M58 public transport or M60 OS rights.

## FILES / SOURCES TO READ
Context Lock lists 38 unique exact-base blobs; mandatory paths include `docs/project-brain/13-CHECKPOINT.md`, `16-DECISIONS-LEDGER.md`, `03-SCOPE.md`, `15-DEFINITION-OF-DONE.md`, `04-ARCHITECTURE.md`, `02-REQUIREMENTS.md`, M09 frozen canonical and FC scan, M09 C01/C02, M11 v0.2 and C08, `iris_resource_twin/recovery.py` and `leases.py`.

## REQUIREMENTS / ARCHITECTURE RULES / CONSTRAINTS
- Explicitly separate M11-produced candidate logical states from M09 consumer validation and lease reconciliation. M11 cannot manufacture M09 owner proof by constructing a local dataclass.
- Future non-UNKNOWN `OwnerLivenessRef` must be proven M11-issued and current under an owner-admitted verification boundary; existing `authority_ref` prefix alone cannot authenticate it. UNKNOWN is mandatory when unverifiable.
- No `CooperativeReleaseResponse.ACCEPTED` implies exit or reclaimed capacity; only M09 can reconcile resource truth, and release request/response never confers OS process-control authority.
- Avoid unknown cross-host trust, clock tolerance, PID safety, control rights or transport assumptions pending M12/M54/M58/M60. Model explicit invalidation, duplicate, crash and time-of-use uncertainty.
- Keep existing 86 questions OPEN/UNRATED, M11 candidate NOT_FROZEN, both implementations NOT_ADMITTED, M09 v1.0 frozen and four HIGH future-freeze blockers OPEN.

## ACCEPTANCE CRITERIA
(38/38) unique source blob SHA verified at exact base, (11/11) paths strictly authorized; two Markdown checkpoints byte-identical and JSON nextStep exactly matching; C02 #461/#462 receipt verified without asserting new runtime tests; producer-side logical evidence envelope, negative/refusal matrix and exact LV-01..06 mapping; no implementation/contract authority inferred.

## TESTS / EVIDENCE
Deterministic JSON parse, Git tree/source hash and changed-path checks; checkpoint mirrors; `git diff --check` and `python scripts/validate_governance.py` via exact-head CI plus existing `python -m unittest discover -s tests -p "test_*.py"` full baseline. HX-01..12/LV-01..06/C08-10/PO-C02-08 remain SPECIFIED_NOT_EXECUTED or NOT_EXECUTED. Do not misreport base CI as newly executed logical or physical tests.

## DELIVERABLES
Bounded owner-research note, machine-readable C09 evidence, C09 exact-base Context Lock, separate audit target, checkpoint/evidence/backlog reconciliation, protected PR and objective exact-head receipt.

## REVIEW FORMAT / STOP CONDITION
Separate read-only review at the exact FINAL PR head: report source SHA/allowlist, fact-vs-proposal and owner boundaries, future blockers, missing/contradictory proof, CI identity, risks and APPROVED / CORRECTION REQUIRED / BLOCKED. Leave PR OPEN after exact-head CI for that review; no owner-source disposition, no freezing, no implementation admission, no issue closure. Only after review APPROVED allow guarded exact-head protected squash merge followed by exact-main Governance.
