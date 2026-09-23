# IRIS-WO-0011 — Implement M07 Hardware Genome & Runtime Discovery

Status: `ADMISSION_CANDIDATE`
Risk: `ELEVATED`
Issue: `#53`
Branch: `iris-wo-0011-m07-hardware-genome`
Authorized base: `db8a39237c26d85f62cdf02a29c29136d4d6ed63`
Frozen contract: `m07-contract-v1.0`
Implementation package: `iris_hardware_genome/`

## OBJECTIVE

Implement the complete frozen M07 provider-neutral Hardware Genome & Runtime Discovery kernel as `iris_hardware_genome/`.

The implementation MUST satisfy all **235** frozen hard invariants, all **20** independent mandatory technology surfaces, all **5** mandatory absorbed components and all frozen acceptance-evidence obligations in `planning/modules/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md`.

This is a complete M07 implementation increment, not an MVP slice. Internal staging is allowed only when every partial state is honest and the final PR satisfies the complete frozen contract.

## AUTHORITY LAW

- M07 owns evidence-bound hardware/runtime discovery and representation.
- M06 owns production/reproducibility policy; M07 emits explicit projections only.
- M08 owns empirical benchmarks/capability envelopes.
- M09 owns resource leases/residency/offload and Resource Digital Twin policy.
- M10 owns execution planning, predictive OOM and thermal decisions.
- M11 owns worker/process lifecycle.
- M12 owns placement/orchestration/federation/queues.
- M14 owns empirical model capability/compatibility truth.
- M55 owns physical retention/deletion/tiering.
- M56 owns telemetry aggregation/history/dashboard/alerts.
- M01/M24/M48 own output-quality semantics.
- HIVE/agents/plugins may request/read/propose but cannot manufacture, strengthen or overwrite admitted M07 truth.

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
10. `planning/modules/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md`

Git/code/tests/evidence outrank conversation memory.

## FROZEN IMPLEMENTATION SCOPE

Implement the 20 independent mandatory technology surfaces:
1. IRIS-HDF Hardware Discovery Fabric
2. IRIS-ODG Opaque Device Graph
3. IRIS-NAF Negative Assertion Firewall
4. IRIS-RSP Runtime Substrate Passport
5. IRIS-CEL Capability Evidence Ladder
6. IRIS-BRM Backend Relationship Matrix
7. IRIS-VSF Version Separation Fabric
8. IRIS-DSG Driver Skew Graph
9. IRIS-PFX Precision Feature Lattice
10. IRIS-MEC Media Engine Capability Matrix
11. IRIS-TGE Topology Graph Evidence
12. IRIS-TSL Telemetry Semantics Ledger
13. IRIS-MPF Memory Pressure Fabric
14. IRIS-EDE Evidence Derivation Engine
15. IRIS-SWG Sampling Window Governor
16. IRIS-HGX Hardware Genome Exchange
17. IRIS-MCD Multidimensional Confidence Descriptor
18. IRIS-GDL Genome Delta Ledger
19. IRIS-RFP Reproducibility Fingerprint Projection
20. IRIS-SCB Schema Compatibility Barrier

Implement the five mandatory absorbed components in their owning surfaces:
- IRIS-DCF under HGX/MCD;
- IRIS-PDM under PFX;
- IRIS-CCG under HGX/BRM;
- IRIS-P2P under TGE;
- IRIS-TCR under TSL.

Preserve the exact **235** frozen invariants. Do not paraphrase them into weaker rules.

## CORE SEMANTICS

Implement typed/versioned semantics for:
- bounded discovery sessions, exact hardware/runtime subjects and evidence-bound observations;
- explicit OBSERVED / NOT_PRESENT_PROVEN / UNKNOWN / UNSUPPORTED_PROBE / PERMISSION_DENIED / UNAVAILABLE / CONFLICTING / STALE / PARTIAL states;
- allowlisted/versioned/read-only probe descriptors and permission classes;
- CPU/GPU/RAM/storage/runtime-substrate discovery;
- provider-neutral CUDA/ROCm/DirectML/Metal/generic capability assertions;
- exact device/backend/runtime/version relationships;
- precision dimensions, media engines and evidence-bound topology;
- bounded thermal/power/utilization/memory-pressure telemetry with temporal semantics;
- deterministic immutable Hardware Genome snapshots;
- normalized fact envelopes, multidimensional confidence and conflict preservation;
- semantic schema compatibility, governed extensions and migration;
- exact base/target genome deltas;
- named/versioned consumer projections and deterministic fingerprints;
- privacy-safe redacted capability advertisements;
- versioned semantic capability/metric registry;
- material-change references/events without owning delivery infrastructure.

## CLOSED CORE / OUT OF SCOPE

Do not implement:
- workload benchmarks or empirical performance envelopes;
- VRAM leases/reservations/residency/offload;
- execution planning, OOM prediction or thermal throttling policy;
- worker lifecycle or process killing;
- compute placement/scheduling/federation policy;
- model ranking/compatibility truth;
- physical retention/deletion/tiering;
- observability dashboard/history/alerting;
- quality downgrade policy;
- driver/firmware installation or repair;
- fan/power/clock mutation;
- arbitrary shell/project binary execution;
- privileged escalation solely for telemetry;
- destination-device profiles;
- M08+ implementation.

No network or arbitrary dynamic code execution in the semantic core. OS/provider adapters, if implemented, MUST be bounded/read-only, optional and isolated behind explicit probe contracts.

## IMPLEMENTATION SHAPE

Prefer a dependency-light Python package with explicit modules such as:
- base/types/enums/errors/versions;
- subjects/runtime/probes/evidence;
- discovery/capabilities/backends;
- precision/media/topology;
- telemetry/memory_pressure/derivation/sampling;
- genome/confidence/schema/registry;
- deltas/projections/redaction/migration/serialization;
- ports/adapters/validation/limits/invariants.

Names may differ if the architecture is clearer, but frozen semantics and authority boundaries cannot.

## TEST / PROOF REQUIREMENTS

Add focused `test_m07_*.py` suites proving:
- 20/20 independent surfaces + 5 absorbed components;
- 235/235 invariant proof index with no gaps/duplicates;
- explicit negative/unknown state safety;
- exact subject/runtime/backend binding;
- driver/runtime/toolkit/framework separation;
- precision/media/topology semantics;
- bounded non-invasive telemetry and sampling;
- static capacity vs dynamic pressure separation;
- deterministic genome serialization/identity;
- confidence cannot manufacture certainty;
- conflict preservation;
- schema PATCH/MINOR/MAJOR and fail-closed required semantics;
- extension namespace isolation;
- immutable snapshots and exact delta binding;
- deterministic projections/fingerprints;
- privacy-safe redaction;
- migration loss classification;
- change-event semantics;
- recovery cannot manufacture current truth;
- 8 GB GPU, CPU-only, mixed-vendor, multi-GPU, partitioned/vGPU and VM/container/WSL fixtures;
- static/import proof against forbidden authority/runtime leakage;
- resource/security limits and hostile/unknown structures.

Run:
- focused compile;
- `python scripts/validate_governance.py`;
- `python -m unittest discover -s tests -p "test_m07_*.py"`;
- `python -m unittest discover -s tests -p "test_*.py"`;
- configured lint/static checks;
- deterministic domain-neutral M07 fixture/harness;
- exact-head GitHub Governance.

Admission baseline full-suite floor: **2770 tests**. M07 tests MUST increase the total. Existing tests may not be deleted, skipped or weakened to reach green.

## DELIVERABLES

- `iris_hardware_genome/` complete kernel;
- focused M07 tests and deterministic fixtures;
- domain-neutral example/harness;
- `docs/M07-HARDWARE-GENOME-RUNTIME-DISCOVERY.md`;
- updated `.engineering/evidence/IRIS-WO-0011.json`;
- exact changed-file/test/evidence accounting;
- 20-surface + 5-component proof map;
- 235-invariant proof map;
- authority-firewall proof;
- proposed checkpoint delta only, never executor-promoted;
- implementation commits on this branch and PR linked to #53.

## PREFLIGHT / ADMISSION

Before product code:
- verify origin/repository/branch;
- verify exact authorized base `db8a39237c26d85f62cdf02a29c29136d4d6ed63`;
- verify merge-base equals authorized base;
- verify every critical source fingerprint in `.engineering/context-locks/IRIS-WO-0011.json`;
- run governance and full baseline suite;
- STOP `STALE_CONTEXT` on any critical mismatch or moved main;
- admission requires exact-head Governance PASS, baseline >=2770 and zero critical-source mismatches.

## EVIDENCE

Record authorized base/head chain, issue/PR, changed files, public API, technology/component map, 235-invariant proof map, dependency/import surface, schema/version/serialization, focused/full tests, compile/lint/governance, deterministic fixtures, failures corrected, authority firewalls, resource/security limits, risks/deferred bridges, proposed checkpoint delta and STOP CONDITION.

## PROMPT DELIVERY

Any complete external-executor prompt MUST be delivered as a downloadable PDF under `.engineering/PROMPT-DELIVERY-POLICY.md`. The repository Work Order remains canonical.

## STOP CONDITION

STOP only when the complete frozen M07 kernel is implemented, all 20 independent surfaces + five absorbed components and all 235 invariants are tested/proven, docs/evidence are complete, the branch is pushed, the PR is ready for independent review, and exact-head Governance is green or deterministically pending and subsequently recorded.

DO NOT MERGE.
DO NOT START M08 IMPLEMENTATION.
DO NOT weaken M06/M08/M09/M10/M11/M12/M14/M55/M56 or quality authority.
If the frozen contract cannot be satisfied without semantic change, STOP `BLOCKED_CONTRACT_CONFLICT`.
