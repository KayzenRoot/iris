# IRIS-WO-0012 — Implement M08 Microbenchmark Lab & Capability Envelope

Status: `ADMITTED_FOR_EXECUTION`
Risk: `ELEVATED`
Issue: `#58`
Branch: `iris-wo-0012-m08-microbenchmark-lab`
Authorized base: `6e2aea630208f6f18656803735426ba99d9b3cc7`
Frozen contract: `m08-contract-v1.0`
Implementation package: `iris_microbenchmark/`

## OBJECTIVE
Implement the complete frozen M08 empirical hardware/runtime performance-characterization kernel. This is not an MVP slice.

The final implementation MUST satisfy all **330** hard invariants, all **40** independent mandatory technology surfaces and all **15** mandatory absorbed components frozen in `planning/modules/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md`.

## ADMISSION

Admission candidate head: `9010f2c7b9bc9ea1a53ae521ad40f05e7a0161a4`

Admission proof:
- critical source fingerprints: **13/13 matched**
- mismatches: **0**
- authorized base/main: `6e2aea630208f6f18656803735426ba99d9b3cc7`
- Governance: `35909286994 / 107344738312` — **PASS**
- baseline/full-suite floor: **2834 tests**
- result: `ADMITTED_FOR_EXECUTION`

## AUTHORITY LAW
M08 owns bounded microbenchmark protocols/results, hardware-capability envelopes, performance fingerprints/drift and calibration/freshness/invalidation semantics bound to exact M07 provenance.

M08 MUST NOT absorb M07 discovery, M09 leases/residency/offload, M10 execution planning/OOM/thermal policy, M11 process lifecycle, M12 scheduling/placement, M14 model fitness, M24/M48 creative quality, M50 cost-quality optimization, M51 broader eval governance, M53 rights/C2PA, M54 security policy, M55 physical storage, M56 observability, M57 agent orchestration, M58 ecosystem lifecycle or M60 release acceptance.

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
10. `planning/modules/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md`
11. `planning/reviews/M08-FINAL-TECHNOLOGY-REVIEW.md`
12. `planning/compatibility/M08-FORWARD-COMPATIBILITY-SCAN.md`

Git/code/tests/evidence outrank conversation memory.

## COMPLETE FROZEN SCOPE
Implement all 40 mandatory surfaces:
BPF, SBG, EPB, ICD, AEG, CMF, UQF, FRB,
MPB, COG, TPE, MEE, GPK, APK, DFM, BAC,
CEF, CBD, BSE, MEM, CCM, SCM, ECC, ELF,
PFF, DED, BLR, RTE, NGF, DAG, PFP, DCP,
CAF, EAL, IAG, RCF, TCB, FDF, FPE, NNF.

Implement all 15 absorbed components:
Benchmark Authorization Receipt; Metric Semantics Registry; Measurement Clock Descriptor; Envelope Invalidation Dependency Map; Evidence Consumer Projection Descriptor; Evidence Purpose Descriptor; Execution Context Descriptor; Requirement Qualification Handshake; External Invalidation Reference; Authority Namespace Descriptor; Provenance Export Digest; Security Authorization Reference; Automation Origin Descriptor; External Schema Projection; Acceptance Evidence Bundle.

Preserve invariants **1-330 exactly**.

## CORE SEMANTICS
Implement typed/versioned semantics for:
- bounded, cancellable, permission-aware active benchmark protocols;
- exact M07 Genome/projection binding;
- deterministic fixtures and correctness-before-speed;
- image/video/3D/audio primitive probes;
- timing, synchronization, transfer direction and uncertainty;
- interference/contamination detection and abort evidence;
- multidimensional capability envelopes and conservative boundaries;
- bounded search with explicit unknown/unsupported regions;
- burst/short-steady/sustained-observed/unknown sustainability;
- immutable performance fingerprints and named baselines;
- noise-aware drift detection and non-causal attribution;
- immutable raw evidence, calibration-derived layers and timing calibration;
- freshness, aging, scoped invalidation, supersession and recalibration lineage;
- privacy projections, purpose qualification and authority namespaces;
- external-context invalidation/security authorization/automation-origin hooks;
- stable external schema projections and deterministic acceptance evidence bundles.

## SAFETY / CLOSED CORE
First-run probes must be bounded. No privilege escalation solely for benchmark, voltage/clock/fan/OS-power mutation, unrelated process killing/suspension, unrelated allocation eviction, unbounded search/allocation/retry, silent stress testing, arbitrary shell/project binary execution, or security-policy bypass.

Synthetic fixtures prove software semantics only and MUST NOT masquerade as physical measurements.

## TEST / PROOF REQUIREMENTS
Add focused `test_m08_*.py` suites and deterministic fixtures proving:
- 40/40 surfaces + 15/15 absorbed components;
- 330/330 exact invariant proof index, no gaps/duplicates/orphan targets;
- protocol identity/version/provenance;
- safety ceilings, cancellation, abort and interference;
- correctness-before-speed;
- clock/timing/synchronization semantics;
- image/video/3D/audio probes and transfer paths;
- envelope derivation/search/coverage/confidence;
- memory/concurrency evidence without M09/M12 authority;
- sustainability distinctions;
- fingerprints/baselines/drift/noise/privacy;
- calibration/aging/invalidation/recalibration;
- consumer qualification, security and automation hooks;
- external schema compatibility and acceptance bundles;
- CPU-only and 8 GB VRAM first-class profiles;
- static authority firewall against M09+ control leakage.

Required validation:
- compile;
- `python scripts/validate_governance.py`;
- focused M08 suite;
- full `test_*.py` suite;
- configured lint/static checks;
- deterministic M08 fixture/harness;
- exact-head GitHub Governance.

Admission baseline floor: **2834 tests**. M08 tests MUST increase the final total. Existing tests may not be deleted, skipped or weakened.

## DELIVERABLES
- `iris_microbenchmark/` complete kernel;
- focused M08 tests/fixtures;
- domain-neutral example/harness;
- `docs/M08-MICROBENCHMARK-LAB-CAPABILITY-ENVELOPE.md`;
- updated `.engineering/evidence/IRIS-WO-0012.json`;
- exact changed-file/test accounting;
- 40+15 implementation/proof map;
- 330-invariant proof map;
- authority-firewall and safety/resource proof;
- proposed checkpoint delta only;
- implementation PR linked to #58.

## PREFLIGHT / ADMISSION
Before product code:
- verify repository/origin/branch;
- verify exact authorized base and merge-base;
- verify all critical fingerprints in `.engineering/context-locks/IRIS-WO-0012.json`;
- run Governance and full baseline suite;
- STOP `STALE_CONTEXT` on any critical mismatch or moved main;
- admission requires exact-head Governance PASS, baseline >=2834 and zero critical-source mismatches.

## STOP CONDITION
STOP only when complete frozen M08 is implemented, all 40 surfaces + 15 components + 330 invariants are proven, evidence/docs are complete, PR is ready for independent review, and exact-head Governance is green or deterministically pending and subsequently recorded.

DO NOT MERGE.
DO NOT START M09 IMPLEMENTATION.
If the frozen contract requires semantic change, STOP `BLOCKED_CONTRACT_CONFLICT`.
