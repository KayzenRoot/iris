# IRIS-WO-0010 — Implement M06 Production State, Versioning & Incremental Media Build

Status: `ADMISSION_CANDIDATE`
Risk: `ELEVATED`
Issue: `#47`
Branch: `iris-wo-0010-m06-production-state`
Authorized base: `e3eaa8386e5ee0f7712e8849a160d253bd2461fe`
Frozen contract: `m06-contract-v1.0`
Implementation package: `iris_production_state/`

## OBJECTIVE

Implement the complete frozen M06 provider-neutral operational production-state kernel as `iris_production_state/`.

The implementation MUST satisfy all **25** frozen technology families, all **150** hard invariants, all **20** forward extension/ref ports and all acceptance families in `planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md`.

This is a complete M06 implementation increment, not an MVP slice.

## AUTHORITY LAW

- M02 remains sole semantic authority for Production Graph, branch/variant/snapshot/rollback, build/reuse semantics and lifecycle/promotion/release/archive law.
- M06 materializes those semantics operationally. It MUST NOT create a competing semantic state/version/build model.
- M05 semantic identity remains distinct from revision/content/materialization identity.
- M01/M48 own quality judgment; M49 owns repair execution.
- M53 owns rights/license/consent/provenance; M54 owns security/authorization.
- M55 owns physical bytes, CAS, cache tiers, archive storage, physical deletion and storage recovery.
- M59 owns publishing/delivery.
- M60 owns system recovery/final acceptance.
- HIVE/agents may retrieve/propose but cannot directly rewrite canonical production truth.

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
10. `planning/contracts/M06-MODULE-CONTRACT-FREEZE-CANDIDATE.md`
11. `planning/reviews/M06-FINAL-TECHNOLOGY-REVIEW.md`
12. `planning/compatibility/M06-FORWARD-COMPATIBILITY-SCAN.md`
13. `planning/modules/M06-PRODUCTION-STATE-VERSIONING-INCREMENTAL-MEDIA-BUILD.md`
14. stable public M02 interfaces actually consumed;
15. stable public M05 interfaces actually consumed.

Git/code/tests/evidence outrank conversation memory.

## FROZEN IMPLEMENTATION SCOPE

Implement the 25 frozen families:
1. RVF Revision Verification Fabric
2. IML Immutable Master Ledger
3. DAS Digest Agility Shield
4. SEA Semantic Equivalence Airgap
5. AVS Availability State Lattice
6. CFM Causal Fingerprint Matrix
7. MSI Minimum Sufficient Invalidation
8. HDS Hidden Dependency Sentinel
9. ICX Impact Cone Explainer
10. RDI Rebuildable Dependency Index
11. SRE Selective Regeneration Engine
12. RAP Reuse Admission Passport
13. FEX Frontier Expansion Matrix
14. MXR Mixed Reconstruction Receipt
15. SDS Stochastic Determinism Shield
16. RCL Reproducibility Class Lattice
17. RXM Reconstruction eXactness Manifest
18. DRG Divergence Reason Graph
19. ESB Equivalence Safety Bridge, M06-facing contract only
20. HPR Historical Permission Firewall, M06-facing contract only
21. LRG Lineage Reachability Guard
22. SGC Safe Garbage Collection Protocol, eligibility/contract only; M55 executes physical deletion
23. RRB Rollback Reconstruction Bridge
24. RSC Release State Capsule
25. CRA Cleanup Race Armor, M06-facing contract only; M55/storage transaction deepens execution.

Preserve the exact **150** frozen invariants from the contract. Do not paraphrase them into weaker implementation rules.

Expose all **20** frozen extension/ref ports:
HardwareMaterialityEvidencePort; ExecutionAttemptPort; CacheReuseEvidencePort; ModelRevisionEvidencePort; WorkflowRevisionEvidencePort; DomainMaterializationEvidencePort; NarrativeCanonRefPort; CampaignBrandIdentityRefPort; QualityEvidencePort; RepairExecutionPort; HiveContextEvidencePort; ProvenanceRightsConsentPort; SecurityAuthorizationPort; PhysicalMediaStorePort; PhysicalDeletionArchivePort; ObservabilityProjectionPort; AgentProposalPort; ExternalContractPort; PublishingDeliveryPort; SystemRecoveryEvidencePort.

## CORE SEMANTICS

Implement typed/versioned semantics for:
- operational revisions, immutable masters, content digests with algorithm/version agility;
- materialization and availability states without conflating physical availability with semantic validity;
- exact dependency observations, multidimensional causal fingerprints and rebuildable reverse indexes;
- impact states including UNKNOWN and stale-evidence blocking;
- correctness-first selective regeneration, explicit work dispositions and reuse admission receipts;
- partial rebuild/frontier expansion with explicit proof;
- reproducibility classes, immutable ReconstructionManifest and ReproducibilityReceipt;
- divergence classification and stochastic replay boundedness;
- rollback reconstruction as new operational history;
- protected lineage/reachability, retention and cleanup eligibility;
- logical retirement distinct from physical deletion;
- release-state operational capsules/closures and archive metadata.

## CLOSED CORE / OUT OF SCOPE

No network, shell/process, provider/DCC/GPU runtime, physical media store, database backend, publishing runtime, rights engine, security engine, quality judge, repair engine or arbitrary dynamic code execution in the semantic core.

Do not implement M55 physical CAS/storage/cache/archive/deletion. Do not implement competing M02 lifecycle/branch/snapshot/build semantics. Do not use M05 dna_id as content/build identity. Do not make cache hit, digest equality, provider success or execution success sufficient for semantic reuse/promotion.

## TEST / PROOF REQUIREMENTS

Add focused `test_m06_*.py` suites proving:
- 25/25 family behavior;
- 150/150 invariant proof index with no gaps/duplicates;
- 20/20 ports and authority firewalls;
- immutable revision/master/history behavior;
- digest agility and unknown-algorithm fail-closed behavior;
- dependency/fingerprint/impact/hidden-dependency behavior;
- selective rebuild/reuse admission and conservative frontier expansion;
- reconstruction/reproducibility/divergence/stochastic behavior;
- rollback/new-history semantics;
- cleanup positive-proof, unknown reachability NOT SAFE TO DELETE, retention and race revalidation;
- release closure and no self-promotion;
- deterministic serialization/round-trip where serializable;
- hostile/unknown structures and explicit resource limits;
- static/import proof against forbidden runtime authority leakage.

Run:
- focused compile;
- `python scripts/validate_governance.py`;
- `python -m unittest discover -s tests -p "test_m06_*.py"`;
- `python -m unittest discover -s tests -p "test_*.py"`;
- configured lint/static checks;
- domain-neutral harness spanning at least the eight target classes frozen by the M06 contract;
- exact-head GitHub Governance.

Baseline full suite floor at admission is **2724 tests**. M06 tests MUST increase the total. Existing tests may not be deleted, skipped or weakened to reach green.

## DELIVERABLES

- `iris_production_state/` complete kernel;
- focused M06 tests and fixtures;
- domain-neutral example/harness;
- `docs/M06-PRODUCTION-STATE-KERNEL.md`;
- updated `.engineering/evidence/IRIS-WO-0010.json`;
- exact changed-file/test/evidence accounting;
- proposed checkpoint delta only, never executor-promoted;
- implementation commits on this branch and PR linked to #47.

## PREFLIGHT / ADMISSION

Before product code:
- verify origin/repository/branch;
- verify exact main/base `e3eaa8386e5ee0f7712e8849a160d253bd2461fe`;
- verify merge-base equals authorized base;
- verify every critical source fingerprint in `.engineering/context-locks/IRIS-WO-0010.json`;
- run governance and full baseline suite;
- STOP `STALE_CONTEXT` on any critical mismatch or moved main;
- admission requires exact-head Governance PASS and zero critical-source mismatches.

## EVIDENCE

Record authorized base/head chain, issue/PR, changed files, public API, 25-family map, 150-invariant proof map, 20-port map, dependency/import surface, schema/version/serialization, focused/full test totals, compile/lint/governance, failures corrected, authority-firewall proof, domain-neutral harness, resource/security limits, risks/deferred bridges, proposed checkpoint delta and STOP CONDITION.

## PROMPT DELIVERY

Any complete external-executor prompt MUST be delivered as a downloadable PDF under `.engineering/PROMPT-DELIVERY-POLICY.md`. The repository Work Order remains canonical.

## STOP CONDITION

STOP only when the complete frozen M06 kernel is implemented, all 25 families and 150 invariants are tested/proven, all 20 ports are authority-safe, docs/evidence are complete, the branch is pushed, the PR is ready for independent review, and exact-head Governance is green or deterministically pending and subsequently recorded.

DO NOT MERGE.
DO NOT START M07 IMPLEMENTATION.
DO NOT weaken M02/M05/M01/M48/M49/M53/M54/M55/M59/M60 authority.
If the frozen contract cannot be satisfied without semantic change, STOP `BLOCKED_CONTRACT_CONFLICT`.
