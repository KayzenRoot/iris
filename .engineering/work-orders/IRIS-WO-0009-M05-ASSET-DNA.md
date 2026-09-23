# IRIS-WO-0009 — Implement M05 Asset DNA 2.0 & Cross-Modal Identity

Status: `ADMISSION_CANDIDATE`
Risk: `ELEVATED`
Issue: `#41`
Branch: `iris-wo-0009-m05-asset-dna`
Authorized base: `ad56aade6ad2459eb632b30bd9fdd332263a5d67`
Frozen contract: `m05-contract-v1.0`
Implementation package: `iris_asset_dna/`

## OBJECTIVE

Implement the complete frozen M05 provider-neutral semantic identity kernel as `iris_asset_dna/`.

The implementation MUST satisfy:
- all **25** frozen technology families `F-M05-01..25`;
- all **150** hard invariants;
- all **22** forward extension/ref ports;
- all acceptance families in `planning/contracts/M05-MODULE-CONTRACT-FREEZE-CANDIDATE.md`;
- all frozen authority firewalls.

This is a complete M05 implementation increment, not an MVP slice.

## AUTHORIZED BASELINE

Exact validated main:
- SHA: `ad56aade6ad2459eb632b30bd9fdd332263a5d67`
- Governance: `35843465664 / 107123844096` — PASS
- required artifacts: **35**
- full suite: **2677/2677 OK**

M05 planning is canonical and frozen as `FROZEN_APPROVED / m05-contract-v1.0`.

## FILES / SOURCES TO READ

Read in this order and treat higher sources as authoritative:

1. `docs/project-brain/13-CHECKPOINT.md`
2. `docs/project-brain/16-DECISIONS-LEDGER.md`
3. `docs/project-brain/03-SCOPE.md`
4. `docs/project-brain/15-DEFINITION-OF-DONE.md`
5. `docs/project-brain/04-ARCHITECTURE.md`
6. `docs/project-brain/02-REQUIREMENTS.md`
7. `.engineering/SOURCE-HIERARCHY.md`
8. `.engineering/REVIEW-AUTOFIX-POLICY.md`
9. `.engineering/PROMPT-DELIVERY-POLICY.md`
10. `planning/contracts/M05-MODULE-CONTRACT-FREEZE-CANDIDATE.md`
11. `planning/reviews/M05-INDEPENDENT-PLANNING-AUDIT.md`
12. `planning/reviews/M05-FINAL-TECHNOLOGY-REVIEW.md`
13. `planning/compatibility/M05-FORWARD-COMPATIBILITY-SCAN.md`
14. `planning/modules/M05-ASSET-DNA-CROSS-MODAL-IDENTITY.md`
15. `planning/technology-registry/M05-TECHNOLOGIES.md`
16. stable public M01 interfaces actually consumed;
17. stable public M02 refs/ports actually consumed;
18. stable public M03 interfaces actually consumed;
19. stable public M04 identity/ref/version interfaces actually consumed.

Git/code/tests/evidence outrank conversation memory.

## PREFLIGHT

Before modifying implementation files:

- inspect repository structure and package conventions;
- run `git status --short` and preserve unrelated user work;
- verify `origin` is `KayzenRoot/iris`;
- `git fetch origin --prune`;
- checkout/update only `iris-wo-0009-m05-asset-dna`;
- verify `origin/main == ad56aade6ad2459eb632b30bd9fdd332263a5d67`;
- verify merge-base with `origin/main` is exactly the authorized base;
- verify every critical source SHA in `.engineering/context-locks/IRIS-WO-0009.json`;
- verify implementation PR targets `main`;
- run `python scripts/validate_governance.py`;
- run the full baseline suite before implementation;
- STOP `STALE_CONTEXT` if main or a critical source moved before execution begins;
- do not force-push, reset shared history or rewrite shared commits.

## SCOPE

### F-M05-01..06 — Core identity, traits, evidence, anchors and context

Implement:
- stable opaque `dna_id`;
- immutable DNA revisions;
- deterministic canonical envelope/serialization/fingerprint;
- typed trait namespaces/schema refs;
- identity criticality;
- mutability classes;
- four-state applicability;
- canonical/evidence twin-plane separation;
- observation quarantine;
- aliases/equivalence/conflict/collision semantics;
- anchor authority classes and lifecycle;
- projection contracts and mandatory-trait preservation;
- interface capsule and MinimumSufficientDNASlice.

### F-M05-07..11 — Families, components and subject profiles

Implement:
- CLASS / ARCHETYPE / INDIVIDUAL / VARIANT semantics;
- DNAFamilyProfile;
- DNATraitBundle;
- persistent component identity;
- governed replacement/split/merge;
- CharacterDNA profile;
- CreatureDNA profile;
- ObjectDNA profile;
- ProductDNA profile;
- EnvironmentDNA profile;
- persistent/contextual/observed appearance partition;
- family reclassification and generic projection without reclassification.

### F-M05-12..15 — Cross-domain and scene identity

Implement:
- LinkedDomainDNARef;
- exact owner/family/revision pinning;
- stale-link semantics and no implicit `latest`;
- SceneIdentityDNA;
- IdentityRoleSlot;
- MotionDNALink;
- VoiceDNALink;
- BrandDNALink;
- CrossModalIdentityBinding;
- CrossModalIdentityObligation;
- CrossModalDNAGraph;
- future-domain link extension points.

M30/M40/M41/M45/M46 retain their domain DNA contents.

### F-M05-16..19 — Drift, mutation and protected evidence

Implement:
- typed path-level IdentityDriftEvidence;
- multidimensional drift;
- IdentityDriftReport;
- IdentityContinuityEnvelope;
- no-single-score identity rule;
- repair/mutation firewall;
- DNAMutationProposal;
- explicit IdentityMutationDecision;
- same-identity immutable revision admission;
- identity break;
- identity split;
- non-destructive consolidation;
- privacy-minimized protected evidence refs;
- M53/M54 policy/security bridges;
- M39 persona-root firewall.

### F-M05-20..24 — Lineage, compatibility, package and import

Implement:
- semantic identity lineage separate from M02 branching;
- directional multi-axis DNACompatibilityProfile;
- EXACT / COMPATIBLE / COMPATIBLE_WITH_LOSS / REQUIRES_MIGRATION / BREAKING / INDETERMINATE;
- DNAMigrationPlan and deterministic receipt;
- reusable DNA package manifest;
- package/subject identity firewall;
- portability levels;
- typed dependency closure;
- marketplace exchange metadata only;
- rights/security/storage/delivery bridges;
- staged DNA import admission;
- collision-safe import;
- package conformance report;
- ACTIVE / DEPRECATED / SECURITY_RESTRICTED / RETIRED lifecycle;
- non-executable package default.

### F-M05-25 — Identity Risk & Threat Radar

Implement one consolidated typed finding vocabulary for:
- class/individual collapse;
- component churn;
- contextual-state leakage;
- stale/missing cross-domain links;
- campaign/brand confusion;
- unauthorized mutation;
- similarity auto-merge;
- history erasure;
- package overwrite;
- hidden lossy migration;
- stripped rights/security refs;
- executable-payload attempts.

Do not create four separate threat-radar engines.

## REQUIRED 22 EXTENSION / REF PORTS

Expose provider-neutral/versioned semantic boundaries for:

1. ProductionStateRefPort
2. HardwareExecutionConstraintRef
3. WorkerPlacementIdentityContextPort
4. ModelCapabilityIdentityEvidencePort
5. ConcreteWorkflowIdentityProjectionPort
6. TrainingIdentityDatasetRefPort
7. ImageReferenceIdentityEvidencePort
8. GeometryAppearanceIdentityPort
9. MotionDNARefPort
10. RenderObservationPort
11. DCCIdentityBindingPort
12. DeliveryProjectionCompatibilityPort
13. TemporalContinuityEvidencePort
14. DigitalHumanPersonaBindingPort
15. VoiceMusicAudioDomainDNAPort
16. CanonContentCampaignBrandPort
17. LocalizationIdentityPreservationPort
18. QualityRepairProposalPort
19. HIVEMemoryIdentitySlicePort
20. RightsSecurityEvidencePort
21. StorageObservabilityAutomationPort
22. APIExportRecoveryIdentityPort

These are ports/contracts only. Do not implement downstream modules.

## OUT OF SCOPE

- M01/M48 quality judges or promotion;
- M02 Production Graph/branch/snapshot/build/release engine;
- M04 SceneIR/runtime representation implementation beyond refs/bindings;
- M06 production-state persistence/reconstruction runtime;
- M55 media CAS/storage/cache/archive backend;
- provider/model/workflow compilation;
- Blender/Maya/ComfyUI execution;
- GPU/VRAM/worker scheduling;
- image/video/3D/audio generation;
- rigging/motion generation/retargeting;
- VoiceDNA creation/TTS/voice cloning;
- MusicDNA/ArtistDNA production;
- Campaign advertising runtime;
- BrandDNA authoring/Brand Court;
- Canon/story/world engine;
- temporal continuity judge/repair runtime;
- rights/license/consent engine;
- restricted-vault/security engine;
- marketplace payments/pricing/ranking/storefront/tax settlement;
- API/plugin platform runtime;
- publishing/export runtime;
- HIVE retrieval implementation;
- M06+ implementation merely to satisfy ports;
- semantic changes to `m05-contract-v1.0`.

## ARCHITECTURE RULES

### Package

Implement as `iris_asset_dna/`.

Prefer focused modules over a monolith. Exact filenames may adapt after repository inspection, but the public architecture SHOULD separate:

- errors / enums / versions;
- identity / revisions;
- traits / applicability / criticality / mutability;
- provenance / policy refs;
- anchors / projections / aliases / conflicts;
- families / components / profiles;
- character / creature / object / product / environment semantics;
- cross-domain links / scene identity / role slots;
- drift / continuity / reports;
- mutation / break / split / consolidation;
- lineage;
- compatibility / migration;
- package manifest / dependency closure;
- import admission / conformance / lifecycle;
- serialization / canonical fingerprints / change surfaces;
- slices / context;
- ports;
- validation / limits / readiness;
- threat findings.

### Dependency boundary

M05 core may depend only on:
- Python standard library;
- stable public M01 interfaces where genuinely required;
- stable public M02 refs/ports where genuinely required;
- stable public M03 refs/interfaces where genuinely required;
- stable public M04 identity/ref/version interfaces where genuinely required.

No new runtime dependency may be added merely for convenience.

If a new dependency is genuinely required, STOP `BLOCKED_DEPENDENCY_DECISION`.

### Authority law

- M01 is sole quality/evaluator/promotion/QualityDebt authority.
- M02 is sole semantic project/Production Graph/branch/snapshot/rollback/build-reuse/release authority.
- M03 is sole creative-intent/constraint/override authority.
- M04 is sole provider-neutral representation/SceneIR authority.
- M05 is generic persistent semantic Asset/Persona identity authority.
- M06 operational persistence/reconstruction must remain under M02 semantic contracts.
- M55 owns media CAS/storage/cache/archive.
- M30 owns MotionDNA/motion production.
- M37 owns temporal/shot continuity judgment.
- M39 owns digital-human/persona production continuity and binds to M05 root.
- M40 owns VoiceDNA/voice production.
- M41 owns ArtistDNA/MusicDNA/music production.
- M43 owns Canon/story/world truth.
- M45 owns Campaign DNA/advertising.
- M46 owns BrandDNA/Brand & IP.
- M53 owns rights/license/consent/provenance.
- M54 owns security/restricted-content/restricted-vault policy.
- M58 owns API/SDK/MCP/plugin lifecycle.
- M59 owns concrete export/publishing/delivery.
- M60 owns deployment/recovery/final system acceptance.
- HIVE/agents may retrieve/propose but cannot directly mutate canonical M05 truth.

### Closed runtime

The semantic kernel MUST NOT perform:
- network access;
- shell/external process execution;
- database/storage backend I/O;
- provider/DCC/GPU runtime execution;
- biometric authentication;
- payment/storefront execution;
- arbitrary dynamic code evaluation.

No `eval`, arbitrary executable schema rules or executable canonical package payloads.

## REQUIREMENTS

- preserve all 150 frozen hard invariants;
- map all 25 F-M05 families to implemented public semantics or documented exact equivalents;
- expose all 22 extension/ref ports without downstream implementation;
- deterministic canonical bytes/digests for same semantic input/profile/version;
- names/paths/URLs/provider/model/workflow/prompt IDs never define subject identity;
- content/build/package hashes never automatically define subject identity;
- evidence/similarity/confidence never self-promotes canonical identity;
- immutable revisions and auditable histories;
- unknown mandatory semantics fail closed;
- optional opaque semantics require explicit preservation policy;
- missing/unknown evidence remains distinct from pass;
- fatal identity-defining conflicts cannot be averaged away;
- required cross-domain links cannot silently disappear;
- canonical required links cannot follow implicit latest;
- repair cannot mutate canonical DNA;
- protected mutation requires proposal + authority + explicit decision;
- identity break creates new dna_id;
- split/consolidation never erase source history;
- compatibility is directional and multi-axis;
- lossy migration is explicit;
- package import cannot silently overwrite identity;
- canonical package format is non-executable by default;
- rights/security refs remain external authorities and are preserved;
- provider/hardware scarcity cannot weaken identity-critical semantics.

## DOMAIN-NEUTRAL SYNTHETIC PROFILES

Use the same M05 core without profile-specific kernel branches for at least:

1. persistent human/corporate spokesperson;
2. non-humanoid asymmetric creature;
3. generic prop/tool/vehicle object;
4. product family/model/SKU/package/physical instance;
5. persistent environment/set across changing SceneIR states;
6. cross-modal character with MotionDNA + VoiceDNA + BrandDNA refs;
7. reusable SceneIdentityDNA with governed replaceable role slots;
8. portable DNA package imported under rights/security constraints.

The fixture layer MUST prove that profile identifiers do not trigger bespoke kernel behavior.

## ACCEPTANCE CRITERIA

Implementation is acceptable only when:

1. all 25 F-M05 families are represented;
2. all 150 hard invariants have direct tests or deterministic proof;
3. all 22 extension/ref ports are exposed and authority-bounded;
4. all frozen acceptance families are covered;
5. every public canonical kind round-trips through deterministic serialization where serializable;
6. eight synthetic profiles use one kernel;
7. M01/M02/M03/M04/M06/M30/M37/M39-M41/M43/M45-M46/M52-M60 authority boundaries have regression/static proof;
8. no provider/DCC/cloud/database/network/shell dependency leaks into core;
9. no biometric auth/payment/storefront runtime leaks into core;
10. minimum-sufficient slices and localized fingerprints/change surfaces are measurable;
11. mutation/break/split/consolidation preserve immutable history;
12. compatibility/migration never hides loss or identity break;
13. package/import operations preserve required policy refs and fail closed;
14. hostile/unknown structures fail deterministically under explicit limits;
15. public `__all__` surface is intentional and tested;
16. full repository suite remains green with no existing test deleted/disabled to hide regressions;
17. docs and Evidence Bundle reflect only verified behavior.

## TESTS

At minimum add focused `test_m05_*.py` suites covering:

- identity / revisions / serialization / fingerprint;
- traits / criticality / mutability / applicability;
- canonical/evidence firewall;
- anchors / projections / aliases / equivalence / conflicts;
- family profiles / components;
- Character/Creature/Object/Product/Environment profiles;
- cross-domain links / freshness;
- SceneIdentityDNA / role-slot substitution;
- drift / continuity / no-single-score;
- repair / mutation / identity break / split / consolidation;
- protected evidence refs / privacy minimization;
- semantic lineage vs M02 branch firewall;
- compatibility / migration / loss / indeterminate states;
- package manifest / dependency closure;
- import admission / collision-safe behavior;
- conformance / lifecycle;
- non-executable supply chain;
- 22 extension/ref ports;
- authority/import-boundary scans;
- 8 domain-neutral fixtures;
- all 150 frozen invariants.

Required execution:
- focused compile of all new M05 modules/tests/examples;
- `python scripts/validate_governance.py`;
- `python -m unittest discover -s tests -p "test_m05_*.py"`;
- `python -m unittest discover -s tests -p "test_*.py"`;
- configured linter/static checks when already available;
- deterministic static/import scan for forbidden provider/DCC/network/shell/database/payment/biometric dependencies;
- run eight-domain example/fixture harness;
- exact-head GitHub Governance.

Baseline floor is **2677 tests**. New M05 tests MUST increase that total. Existing tests may not be deleted, skipped or weakened merely to reach green.

## DOCUMENTATION

Add:
- `docs/M05-ASSET-DNA-KERNEL.md`;
- public API / concept mapping;
- all authority-boundary explanations;
- schema/serialization/versioning/migration notes;
- drift/mutation/continuity model;
- package/import/conformance model;
- 8 domain examples;
- 22 deferred extension/ref ports;
- known limitations and risks;
- no unsupported performance/token-saving/novelty claims.

## DELIVERABLES

- complete `iris_asset_dna/` semantic kernel;
- focused `tests/test_m05_*.py` suites and support fixtures;
- eight-domain example harness under `examples/`;
- `docs/M05-ASSET-DNA-KERNEL.md`;
- updated `.engineering/evidence/IRIS-WO-0009.json`;
- proposed Checkpoint Delta, not executor-promoted as canonical truth;
- implementation commits pushed to this same branch;
- same PR linked to Issue #41;
- exact-head Governance evidence.

## EVIDENCE BUNDLE

Record truthfully:
- authorized base and tested/reviewed head chain;
- issue/PR number, URL and state;
- exact changed files/counts;
- package/module/public API shape;
- F-M05 family mapping;
- 150-invariant proof index;
- 22-port exposure mapping;
- dependency/import surface;
- schema/serialization/version set;
- tests by family + focused/full totals;
- compile/lint/governance results;
- failures encountered and corrected;
- all authority-firewall proofs;
- eight-domain neutrality evidence;
- slices/fingerprints/change-surface evidence;
- drift/mutation/break/split/consolidation evidence;
- compatibility/migration/package/import evidence;
- privacy/restricted-evidence proof;
- non-executable-package proof;
- no-provider/no-DCC/no-network/no-shell/no-database proof;
- risks/deferred ports;
- proposed Checkpoint Delta;
- STOP CONDITION.

Do not make the Evidence Bundle self-referentially claim its own commit SHA. Use a documented head chain and exact-head CI.

## REVIEW FORMAT

Return final executor review in Brazilian Portuguese with:
- architecture implemented;
- files/package/public surface;
- 25-family and 150-invariant coverage;
- 22-port mapping;
- exact tests/results;
- authority-boundary proof;
- eight-domain fixtures;
- serialization/migration/package/import proof;
- security/privacy/context-efficiency proof;
- failures corrected;
- deviations/risks;
- commit/head;
- PR;
- Evidence Bundle;
- proposed Checkpoint Delta;
- STOP CONDITION.

## PROMPT DELIVERY

If an external executor such as Codex/Coder/Zcode is used, the complete executor prompt MUST be delivered to the user as a downloadable PDF under `.engineering/PROMPT-DELIVERY-POLICY.md`.

The repository Work Order remains the canonical governance artifact.

## STOP CONDITION

STOP only when:
- the complete frozen M05 semantic identity kernel is implemented;
- all 25 families and 150 invariants are tested/proven;
- all 22 ports are represented and authority-safe;
- eight synthetic profiles pass through one kernel;
- docs and Evidence Bundle are complete;
- branch is pushed;
- the same PR is ready for independent review;
- exact-head Governance is green or deterministically pending and subsequently recorded;
- no frozen invariant or upstream/downstream authority was weakened.

DO NOT MERGE.
DO NOT START M06 IMPLEMENTATION.
DO NOT implement provider/DCC/domain runtimes merely to satisfy extension ports.
DO NOT weaken M01 QualityClass, M02 production authority, M04 representation authority or downstream DNA-domain ownership.
If the frozen contract cannot be satisfied without semantic change, STOP `BLOCKED_CONTRACT_CONFLICT`.
