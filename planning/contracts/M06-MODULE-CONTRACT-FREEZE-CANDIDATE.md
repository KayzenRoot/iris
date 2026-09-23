# M06 Module Contract Freeze Candidate — Production State, Versioning & Incremental Media Build

Status: `FREEZE_CANDIDATE_PENDING_VALIDATION`
Target frozen version: `m06-contract-v1.0`
Module: `M06`
Issue: `#44`
Planning base: `bac62c5e59ff926c6b80a5ec86a91b0410f35fea`

## 1. Mission

M06 owns the provider-neutral operational production-state layer that materializes M02 semantic production/version/build law into immutable revision/manifests, dependency fingerprints/indexes, selective rebuild evidence, reconstruction receipts, rollback execution evidence, lineage-aware cleanup eligibility and release-state operational closure.

M06 is canonical for:
- operational revision/materialization manifests under M02;
- immutable master operational records;
- qualified content digests and integrity/availability evidence;
- operational dependency observations/fingerprints/indexes;
- explainable impact receipts;
- reuse/selective rebuild/reconstruction receipts;
- reproducibility-class operational evidence;
- rollback/recovery operational receipts;
- lineage/reachability cleanup eligibility;
- release-state operational capsules.

M06 is not canonical for M02 semantic lifecycle, M05 subject identity, M01/M48 quality judgment, M49 repair execution, M53 rights/consent/provenance authority, M54 security authority, M55 physical CAS/storage/GC/archive, or M59 publishing/delivery.

## 2. Frozen ownership shields

- M02: project/production identity, Production Graph, branch/variant/snapshot/rollback semantics, build/reuse law, promotion/release/archive lifecycle.
- M05: persistent Asset/Persona semantic identity.
- M01/M48: quality/evaluation/promotion evidence authority.
- M49: defect localization and repair execution.
- M53: provenance/rights/license/consent authority.
- M54: security/restricted-content/access authority.
- M55: physical media CAS/storage/cache/tiering/delete/archive execution.
- M59: export/publishing/delivery.
- M60: whole-system deployment/recovery/final acceptance.

M06 consumes exact refs/evidence from these owners without transferring their authority.

## 3. Frozen technology families

M06 contract recognizes 25 reviewed families:

1. IRIS-RVF Revision Verification Fabric
2. IRIS-IML Immutable Master Ledger
3. IRIS-DAS Digest Agility Shield
4. IRIS-SEA Semantic Equivalence Airgap
5. IRIS-AVS Availability State Lattice
6. IRIS-CFM Causal Fingerprint Matrix
7. IRIS-MSI Minimum Sufficient Invalidation
8. IRIS-HDS Hidden Dependency Sentinel
9. IRIS-ICX Impact Cone Explainer
10. IRIS-RDI Rebuildable Dependency Index
11. IRIS-SRE Selective Regeneration Engine
12. IRIS-RAP Reuse Admission Passport
13. IRIS-FEX Frontier Expansion Matrix
14. IRIS-MXR Mixed Reconstruction Receipt
15. IRIS-SDS Stochastic Determinism Shield
16. IRIS-RCL Reproducibility Class Lattice
17. IRIS-RXM Reconstruction eXactness Manifest
18. IRIS-DRG Divergence Reason Graph
19. IRIS-ESB Equivalence Safety Bridge
20. IRIS-HPR Historical Permission Firewall
21. IRIS-LRG Lineage Reachability Guard
22. IRIS-SGC Safe Garbage Collection Protocol
23. IRIS-RRB Rollback Reconstruction Bridge
24. IRIS-RSC Release State Capsule
25. IRIS-CRA Cleanup Race Armor

Families 19, 20, 22 and 25 freeze M06-facing contracts while evaluator/policy/storage execution deepens in later owner modules.

## 4. Hard invariants

The 150 numbered invariants in `planning/modules/M06-PRODUCTION-STATE-VERSIONING-INCREMENTAL-MEDIA-BUILD.md` are normative candidates for `m06-contract-v1.0`.

Freeze validation must prove all 150 remain present, uniquely numbered and traceable. They may not be weakened by implementation convenience.

Normative themes include:
- semantic/content/materialization identity separation;
- immutable append-only history;
- exact/versioned refs and digest agility;
- fail-closed unknown mandatory semantics/evidence;
- correctness-first dependency impact and reuse;
- positive proof for unaffected/no-work/reuse;
- explicit partial rebuild ancestry;
- bounded stochastic reproducibility claims;
- immutable reconstruction evidence;
- append-only rollback;
- positive-proof cleanup and retention;
- immutable release closure;
- external authority preservation.

## 5. Revision/master contract

Implementation must support at least:
- OperationalRevisionRef;
- ContentDigest with algorithm/version;
- RevisionManifest;
- ImmutableMasterRef;
- MaterializationRef;
- MasterManifest;
- RevisionBinding;
- PersistenceReceipt;
- IntegrityReceipt;
- explicit availability/corruption/unknown states.

Admitted revisions and masters are immutable. Repair, re-encode, migration, restoration, rollback and supersession create new history when declared canonical bytes/semantics change.

## 6. Identity/content firewall

The following remain non-interchangeable:

`M02 semantic identity != M02 revision/snapshot != M06 operational revision != content digest != materialization != attempt != M05 dna_id != M55 storage locator`.

Paths, filenames, URLs, bucket keys, provider IDs and storage locations never define canonical M06 identity.

Digest equality proves byte equality under the declared digest domain only. It does not prove semantic equivalence, quality, rights, security, acceptance or subject identity.

## 7. Dependency/fingerprint contract

Implementation must support:
- typed DependencyObservation;
- versioned OperationalDependencyFingerprint;
- FULL_CAUSAL / SELECTED_SLICE / RECONSTRUCTION / POLICY_SENSITIVE / IDENTITY_SENSITIVE / TOOLCHAIN_SENSITIVE scopes;
- FingerprintDelta;
- derived/rebuildable reverse dependency indexes with completeness/freshness state;
- direct/transitive Impact Cone evidence;
- unknown impact frontier;
- hidden/dynamic dependency discovery receipts;
- deterministic explain traces.

Observed dependencies are evidence until admitted through M02-compatible authority. Unknown mandatory materiality blocks unsafe reuse.

## 8. Selective rebuild/reuse contract

Required dispositions:
- REUSE_EXACT;
- REUSE_WITH_VERIFICATION;
- VERIFY_ONLY;
- REPAIR_CANDIDATE;
- REBUILD_PARTIAL;
- REBUILD_FULL_TARGET;
- BLOCKED;
- NO_WORK_PROVEN.

Reuse requires positive scoped evidence. Cache presence or matching digest alone never authorizes semantic reuse.

Partial rebuild requires admitted boundaries, explicit reused/rebuilt ancestry, versioned recomposition rules and preservation of protected identity/quality obligations.

## 9. Reproducibility/reconstruction contract

Required reproducibility classes:
- EXACT_BYTES;
- EXACT_SEMANTIC_STATE;
- EQUIVALENT_WITHIN_CONTRACT;
- STOCHASTIC_REEXECUTABLE;
- REFERENCE_RECONSTRUCTABLE;
- NON_RECONSTRUCTABLE;
- UNKNOWN.

Required ReconstructionManifest/ReproducibilityReceipt semantics bind exact material inputs, dependencies, workflow/model/toolchain refs, materially relevant environment facts, policy refs, expected/achieved class and divergence.

Seed equality or fingerprint equality alone cannot prove exact-byte replay.

## 10. Rollback/recovery contract

Rollback:
- targets exact M02 historical state;
- creates new current history;
- never rewrites historical masters;
- verifies current integrity/availability and mandatory current policy;
- records achieved outcome bounded by S04 reproducibility evidence;
- preserves failure/partial-recovery state explicitly.

Historical permission never bypasses current M53/M54 authority.

## 11. Cleanup/retention contract

Cleanup eligibility requires positive proof that an object is outside every protected lineage/reconstruction/release/retention closure.

Unknown reachability is NOT safe to delete.

Logical retirement, eligibility, deletion authorization and physical deletion completion are distinct.

M55 performs physical deletion. M06 records/validates operational eligibility and lineage evidence.

Cleanup authorization binds a lineage/reachability epoch/fingerprint and must be revalidated after material concurrent changes.

## 12. Release/archive contract

M06 may materialize an immutable operational release capsule containing exact production/snapshot/build/master/dependency/integrity/authority refs.

M06 cannot self-promote or publish a release.

Corrections create new history and explicit supersession. Mutable aliases cannot rewrite historical release identity.

Archive tier/location is M55-owned and cannot define M06 identity.

## 13. Required extension/ref ports

The future kernel must expose 20 provider-neutral versioned boundaries:

1. HardwareMaterialityEvidencePort — M07/M08/M09/M10
2. ExecutionAttemptPort — M11/M12
3. CacheReuseEvidencePort — M13
4. ModelRevisionEvidencePort — M14/M18/M19
5. WorkflowRevisionEvidencePort — M16/M17
6. DomainMaterializationEvidencePort — M20–M42/M47
7. NarrativeCanonRefPort — M43
8. CampaignBrandIdentityRefPort — M45/M46
9. QualityEvidencePort — M01/M24/M48/M51
10. RepairExecutionPort — M49
11. HiveContextEvidencePort — M52
12. ProvenanceRightsConsentPort — M53
13. SecurityAuthorizationPort — M54
14. PhysicalMediaStorePort — M55
15. PhysicalDeletionArchivePort — M55
16. ObservabilityProjectionPort — M56
17. AgentProposalPort — M57
18. ExternalContractPort — M58
19. PublishingDeliveryPort — M59
20. SystemRecoveryEvidencePort — M60

Ports carry refs/evidence/capabilities and never transfer canonical authority.

## 14. Closed-core dependency boundary

The M06 semantic/operational kernel may use Python standard library and stable upstream IRIS interfaces.

Core must not require:
- network access;
- shell/external process execution;
- database/storage backend SDKs;
- provider/model SDKs;
- Blender/Maya/ComfyUI;
- GPU/runtime SDKs;
- cloud SDKs;
- physical CAS implementation;
- arbitrary executable manifest/package payloads.

Adapters/infrastructure belong to owner modules.

## 15. Security/trust boundary

Fail closed for:
- unknown mandatory digest/schema/fingerprint semantics;
- hidden mandatory dependencies;
- partial/stale/corrupt indexes used as proof of unaffected state;
- unsafe reuse from cache/digest presence;
- implicit-latest canonical dependencies;
- silent dependency substitution;
- false deterministic claims;
- stale cleanup authorization;
- missing retention/reachability evidence;
- current-policy bypass through historical receipts;
- failed deletion recorded as success;
- reconstructed output silently replacing immutable master;
- HIVE/agent/provider self-admission of protected canonical changes.

## 16. Domain-neutral targets

The same core must support at least:
1. image production master and partial repair lineage;
2. 3D asset with mesh/material/LOD dependencies;
3. video/shot production with mixed rebuilt/reused segments;
4. audio/voice/music materializations;
5. metadata-only/canon-dependent production state;
6. stochastic generation with bounded reproducibility class;
7. retained-materialization restoration without regeneration;
8. release/archive/rollback/cleanup lineage.

No media-domain field is mandatory across all targets.

## 17. Acceptance-test obligations

Later implementation must prove:
- deterministic canonical serialization/fingerprints;
- immutable revision/master mutation rejection;
- digest algorithm/version agility;
- same bytes/different semantic artifact separation;
- exact refs versus implicit-latest rejection;
- hidden/unknown dependency fail-closed behavior;
- facet/slice impact correctness;
- positive proof for UNAFFECTED_PROVEN/NO_WORK_PROVEN;
- stale/partial/corrupt reverse-index safety;
- cache-hit false-positive rejection;
- reuse receipt immutability;
- mixed rebuild ancestry/recomposition;
- stochastic reproducibility non-escalation;
- restoration versus regeneration distinction;
- divergence classification;
- historical/current authorization separation;
- rollback append-only history;
- protected reachability/retention cleanup safety;
- two-phase deletion and race revalidation;
- immutable release closure/supersession;
- M02/M05/M55 and quality/rights/security/publishing authority regressions;
- domain neutrality.

## 18. Implementation evidence obligations

A later bounded Work Order must record:
- exact base/head SHA and `m06-contract-v1.0`;
- public API/concept mapping;
- mapping of all 25 technology families into implementation modules;
- executable proof coverage for all 150 invariants;
- all 20 extension/ref ports;
- dependency/import surface;
- deterministic serialization/fingerprint profile;
- focused M06 test counts/results;
- full repository suite;
- static/lint/compile checks;
- forbidden dependency/runtime scan;
- eight-domain-neutral fixture/harness evidence;
- exact-head Governance;
- authority-firewall tests;
- evidence bundle and proposed checkpoint delta.

## 19. Out of scope for M06 implementation

- redefining M02 project/Production Graph/branch/build/lifecycle;
- M05 DNA identity engine;
- hardware discovery/benchmarking/planning;
- worker scheduling/placement;
- cache implementation;
- model/workflow registry/acquisition/compiler;
- provider/DCC execution;
- domain media generation/evaluation;
- repair execution;
- HIVE retrieval internals;
- provenance/rights/consent engine;
- security/RBAC/vault engine;
- physical CAS/storage/tiering/GC/archive;
- dashboards/telemetry backend;
- autonomous agent orchestration;
- API/plugin transport;
- publishing/delivery;
- whole-system backup/disaster recovery.

## 20. Implementation STOP CONDITION

STOP only when the complete frozen M06 provider-neutral operational production-state kernel is implemented, tested, documented, evidence-bundled, pushed and ready for independent review.

DO NOT MERGE on executor word.
DO NOT implement downstream owner modules merely to satisfy ports.
DO NOT weaken frozen invariants for performance or hardware scarcity.
If implementation requires semantic contract change, STOP `BLOCKED_CONTRACT_CONFLICT`.

## 21. Freeze evidence required before v1.0 approval

Before status becomes `FROZEN_APPROVED / m06-contract-v1.0`, planning PR must prove:
- S01–S05 complete;
- Final Technology Review `APPROVED_FOR_CONTRACT_FREEZE`;
- 150 invariants present/traceable;
- Forward Compatibility Scan `PASS_WITH_EXTENSION_PORTS`;
- 20 extension/ref ports recorded;
- authority shields reconciled;
- exact-head Governance PASS;
- full existing repository suite green;
- planning/docs/governance-only diff;
- independent planning audit `APPROVED`;
- zero HIGH/CRITICAL planning blockers.

Any semantic change after freeze requires a versioned M06 contract amendment and renewed compatibility review.

## 22. Freeze candidate state

- Target contract: `m06-contract-v1.0`
- Status: `FREEZE_CANDIDATE_PENDING_VALIDATION`
- S01–S05: complete
- Hard invariants: 150
- Technology families: 25
- Direct M06-owned families: 21
- Later-owner execution bridges: 4
- Forward modules scanned: M07–M60
- Extension/ref ports: 20
- Final Technology Review: `APPROVED_FOR_CONTRACT_FREEZE`
- Forward Compatibility Scan: `PASS_WITH_EXTENSION_PORTS`
- Product/kernel implementation: not started
- Known HIGH/CRITICAL planning blockers: 0

The exact candidate head must pass governance and independent audit before promotion to `FROZEN_APPROVED`.
