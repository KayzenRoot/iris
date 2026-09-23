# M06 — Production State, Versioning & Incremental Media Build

Status: `S04_COMPLETE_FOR_MODULE_PLANNING`
Planning model: `FULL_VERSION_NO_MVP`
Issue: #44
Planning base: `bac62c5e59ff926c6b80a5ec86a91b0410f35fea`

## Governing boundary

M06 is the operational persistence/materialization layer for the semantic production law already frozen by M02.

M06 MUST consume M02 contracts for project/production identity, Production Graph, branch/variant/snapshot/rollback, build/invalidation/reuse and promotion/release/archive lifecycle. It MUST NOT create a competing state, branch, snapshot, build or lifecycle model.

M55 owns physical media CAS, storage tiers, cache, archive and storage GC. M06 may define content-addressed revision/materialization semantics and storage ports, but storage location/backend/tiering is external.

M05 semantic DNA identity remains distinct from build/master/content identity. A content hash never becomes `dna_id` or semantic artifact identity automatically.

# S01 — Content-addressed revisions and immutable masters

## 1. Goal

Define a provider-neutral, storage-neutral operational revision layer that can bind immutable semantic inputs, materialized outputs and reproducibility evidence without confusing content equality with semantic identity.

## 2. Core concepts

- `OperationalRevisionRef`: opaque reference to one immutable M06 operational revision.
- `ContentDigest`: algorithm-qualified digest over canonical bytes, never semantic identity.
- `RevisionManifest`: immutable declaration of semantic refs, dependency refs, materializations and receipt refs.
- `ImmutableMasterRef`: reference to a promoted immutable master materialization.
- `MaterializationRef`: provider-neutral reference to produced bytes/resources.
- `MasterManifest`: immutable closure describing a master and required external refs.
- `RevisionBinding`: explicit binding from an M02 semantic revision/snapshot/build to M06 operational revision.
- `ReconstructionSeedRef`: opaque/versioned reference to deterministic reconstruction inputs where applicable.
- `PersistenceReceipt`: evidence that a declared revision/master was durably admitted through a storage port.
- `IntegrityReceipt`: deterministic verification result for declared digests/manifest closure.
- `AvailabilityState`: explicit KNOWN_AVAILABLE / KNOWN_MISSING / UNKNOWN distinction.
- `RetentionIntentRef`: semantic retention requirement consumed by later storage/cleanup execution, not a storage policy implementation.

## 3. Identity separation

The following namespaces are non-interchangeable:

`M02 semantic identity != M02 revision/snapshot != M06 operational revision != content digest != materialization != execution attempt != M05 dna_id != M55 storage locator`.

Byte-identical materializations may deduplicate physically under M55 while remaining distinct semantic artifacts/revisions when M02 says they are distinct.

Paths, filenames, URLs, bucket keys, provider IDs and storage locations never become canonical identity.

## 4. Content addressing

Content addressing requires:
- explicit digest algorithm/version;
- canonical byte-domain definition;
- deterministic encoding where canonicalization is claimed;
- collision/algorithm-unknown handling that fails closed;
- no inference of semantic equivalence from digest equality;
- digest agility so a frozen record is not rewritten when algorithms evolve.

A digest is evidence about bytes, not authority about meaning, acceptance, rights, quality or identity.

## 5. Immutable revisions

An admitted revision:
- is append-only;
- binds exact parent/reference digests;
- cannot silently follow an implicit latest;
- cannot be rewritten after promotion;
- may be superseded only by a new revision/receipt;
- preserves unknown/indeterminate states explicitly;
- keeps semantic and physical availability separate.

Repair, migration, re-encode and restoration produce new history when canonical bytes or declared semantics change.

## 6. Immutable masters

A master is a governed immutable materialization reference, not merely a file marked final.

Master admission requires:
- exact M02 production/snapshot/build binding;
- exact revision manifest;
- declared materialization digests;
- required quality/promotion evidence refs;
- required rights/security/provenance refs when applicable;
- integrity state;
- explicit external dependency closure;
- no unresolved mandatory dependency.

M06 records the operational master contract. M01 owns quality judgment, M02 owns promotion/release semantics, M53 owns rights/provenance/consent authority, M54 owns security authority, and M55 owns physical storage/archive.

## 7. Failure and uncertainty

Missing, unknown, corrupt, unavailable and policy-blocked are distinct states.

No implementation may convert:
- UNKNOWN to PASS;
- missing evidence to valid evidence;
- physical presence to semantic acceptance;
- digest match to quality/rights/security approval;
- provider success to master promotion.

## 8. Storage-neutral ports

S01 requires versioned ports for:
- content put/get/exists verification;
- manifest persistence/retrieval;
- receipt persistence/retrieval;
- integrity verification;
- retention pin/intention handoff;
- restricted-resource reference resolution.

Ports expose capability/results, not backend-specific paths or vendor semantics.

## 9. Initial hard invariants

1. Content digests are never semantic identity.
2. M05 dna_id is never derived automatically from M06/M55 content hashes.
3. M06 operational revisions never replace M02 semantic revisions/snapshots.
4. M06 never creates a competing branch/lifecycle authority.
5. Historical admitted revision manifests are immutable.
6. Historical masters are immutable.
7. Supersession creates new history.
8. Paths/names/URLs/provider IDs/storage locators are not canonical identity.
9. Digest algorithm and version are explicit.
10. Unknown digest algorithms fail closed for mandatory verification.
11. Digest equality alone never proves semantic equivalence.
12. Digest equality alone never proves quality, rights, security or acceptance.
13. Same bytes may represent distinct semantic artifacts.
14. Different bytes cannot be silently substituted under an immutable materialization ref.
15. Required dependency refs are exact/versioned and never implicit-latest.
16. Unknown mandatory dependency state fails closed.
17. Missing, unknown and corrupt are distinct.
18. Physical availability is distinct from semantic validity.
19. Attempt success cannot promote an immutable master by itself.
20. Master admission consumes M02/M01 authority rather than replacing it.
21. Rights/provenance/consent authority remains M53.
22. Security/restricted-content authority remains M54.
23. Physical CAS/storage/cache/archive authority remains M55.
24. Storage deduplication cannot collapse semantic history.
25. Storage movement/tiering cannot alter revision identity.
26. Re-encoding that changes canonical bytes produces explicit new materialization history.
27. Repair cannot rewrite an admitted master in place.
28. Restoration from archive must verify declared integrity before admission as available.
29. Unknown/indeterminate evidence cannot be coerced to PASS.
30. HIVE/agents may observe/propose persistence actions but cannot rewrite canonical M02/M06 history directly.

These are S01 candidates until final M06 contract freeze.

## 10. Proprietary technology candidates

### IRIS-RVF — Revision Verification Fabric
Multi-layer verification joining semantic bindings, manifest closure, digest integrity and authority refs without collapsing them into one hash.

### IRIS-IML — Immutable Master Ledger
Append-only provider-neutral master admission/supersession receipts with explicit authority provenance.

### IRIS-DAS — Digest Agility Shield
Algorithm-qualified multi-digest evolution mechanism that allows stronger future hashes without rewriting frozen historical records.

### IRIS-SEA — Semantic Equivalence Airgap
Hard firewall preventing byte/content equality from being promoted automatically into semantic identity/equivalence.

### IRIS-AVS — Availability State Lattice
Fail-closed availability model preserving AVAILABLE, MISSING, UNKNOWN, CORRUPT and POLICY_BLOCKED as non-equivalent states.

All candidates remain planning concepts until Technology Review; names do not imply novelty/patentability.

## 11. Cross-module firewalls

- M01: quality/evaluation/promotion evidence.
- M02: semantic production/version/build/lifecycle authority.
- M03: creative intent/constraint authority.
- M04: provider-neutral media/scene representation.
- M05: persistent semantic Asset/Persona identity.
- M06: operational revision/materialization/reconstruction layer.
- M13: runtime cache/performance optimization.
- M53: provenance/rights/consent.
- M54: security/restricted content.
- M55: physical media CAS/storage/cache/archive.
- M59: export/publishing/delivery.

## 12. S01 acceptance evidence targets

Planning/implementation later must prove:
- deterministic manifest serialization/fingerprints;
- same bytes/different semantic artifact remains distinct;
- different bytes cannot inhabit one immutable materialization ref;
- immutable revision/master mutation rejection;
- explicit supersession history;
- digest-algorithm agility;
- fail-closed unknown algorithms/dependencies;
- missing/unknown/corrupt distinction;
- storage-locator changes do not alter canonical identity;
- M02/M05/M55 authority regression tests;
- domain neutrality across image, 3D, video, audio and non-media metadata examples.

## S01 STOP CONDITION

S01 is complete for module planning when:
- M02/M06/M55 ownership is explicit;
- content identity and semantic identity are separated;
- immutable revision/master semantics are explicit;
- uncertainty/failure semantics are fail-closed;
- storage-neutral ports are identified;
- 30 candidate hard invariants are recorded;
- S01 proprietary candidates are registered for later review;
- checkpoint may advance to M06 S02 planning;
- no M06 product implementation is introduced.


# S02 — Dependency fingerprints and impact analysis

Status: `COMPLETE_FOR_MODULE_PLANNING`

## 1. Goal

Define the operational dependency-observation, fingerprint and impact-analysis layer that turns M02 dependency semantics into exact, explainable rebuild evidence without allowing M06 to invent semantic dependencies or silently omit observed material causality.

## 2. Authority boundary

M02 remains canonical for Production Graph edges, DependencyFacet, DependencySelector/Slice, CausalFingerprint, ImpactCone, DependencyDiscoveryReceipt, BuildDelta and DirtyFrontier semantics.

M06 operationalizes those contracts by:
- recording exact dependency observations for a materialization/revision;
- computing versioned operational fingerprints over admitted dependency slices;
- indexing reverse dependency evidence;
- comparing prior/current observations;
- projecting candidate affected sets under M02 rules;
- emitting explainable impact receipts for later S03 selective rebuild.

M06 does not mutate an M02 graph merely because runtime observation discovers a dependency. An undeclared material dependency becomes a governed discovery/conflict requiring M02-compatible admission.

## 3. DependencyObservation

A dependency observation binds:
- consumer semantic/revision ref;
- producer/dependency exact ref;
- dependency facet and selector/slice;
- observation source/capability;
- required/optional/observed-only classification;
- exact version/schema of interpretation;
- observation confidence/state;
- evidence ref;
- deterministic observation fingerprint.

Observation is evidence, not automatic graph authority.

## 4. OperationalDependencyFingerprint

Fingerprints are multidimensional and typed rather than one opaque cache key.

Candidate dimensions:
- semantic input refs;
- exact dependency revisions;
- selected facets/slices;
- M03 intent/constraint refs;
- M04 representation refs;
- M05 identity/DNA refs where consumed;
- qualified model/workflow/toolchain refs when execution-relevant;
- policy/rights/security refs when they materially affect admissible output;
- reconstruction parameters/seeds where applicable;
- environment/capability refs only when declared material to reproducibility;
- schema/fingerprint algorithm versions.

Non-material telemetry, storage location and display metadata cannot dirty a build unless a governing contract explicitly classifies them as material.

## 5. Fingerprint scopes

Required scopes:
- `FULL_CAUSAL`: complete admitted material dependency closure for a target.
- `SELECTED_SLICE`: one declared dependency slice/facet.
- `RECONSTRUCTION`: inputs required to reconstruct a specific materialization class.
- `POLICY_SENSITIVE`: authority/policy refs whose change can invalidate admissibility.
- `IDENTITY_SENSITIVE`: protected M05 identity refs consumed by the target.
- `TOOLCHAIN_SENSITIVE`: admitted execution semantics whose version affects reproducibility.

Scopes are explicit and cannot be compared as equivalent accidentally.

## 6. ChangeSet and FingerprintDelta

A delta records:
- previous/current fingerprint versions;
- changed dimensions;
- added/removed/changed exact refs;
- unknown/unresolvable dimensions;
- materiality classification;
- affected selectors/slices;
- evidence explaining every classification.

Unknown materiality on a mandatory dependency is blocking for safe reuse.

## 7. Reverse dependency index

M06 may maintain a durable operational reverse index from exact dependency refs/fingerprints to consumers.

Rules:
- the index is derived from canonical/observed receipts;
- it is rebuildable;
- it is not canonical semantic graph authority;
- stale/partial index state is explicit;
- absence from an incomplete index never proves no impact;
- index corruption cannot silently authorize reuse.

M55 may store the index bytes, but M06 owns its operational semantics.

## 8. Impact analysis

Impact analysis starts from a typed change set and produces:
- directly affected consumers;
- transitive candidate impact cone;
- exact causal paths;
- unaffected proof candidates where sufficient evidence exists;
- unknown impact frontier;
- policy/identity-sensitive invalidations;
- reason codes for each edge/target.

The result is an analysis receipt, not an execution plan. S03 consumes it to decide selective rebuild under M02 Build semantics.

## 9. Hidden and dynamic dependencies

Runtime/provider discovery may reveal undeclared dependencies.

Required behavior:
- record the observation;
- mark affected prior reuse assumptions stale where material;
- create a `DependencyDiscoveryReceipt` compatible with M02;
- block unsafe reuse until dependency authority is reconciled;
- never silently mutate frozen graph history;
- never discard a material hidden dependency because it is inconvenient or expensive.

Dynamic dependencies require explicit bounded discovery semantics and cannot be represented by an unbounded wildcard that falsely claims completeness.

## 10. Minimum sufficient invalidation

The optimization objective is not "invalidate as little as possible." It is "invalidate no less than correctness requires, then minimize unnecessary work with proof."

A target may be classified unaffected only when:
- all material dependency dimensions relevant to that target are known;
- selectors/slices prove the changed portion is outside its dependency;
- fingerprint algorithms/schemas are supported;
- no blocking hidden/unknown dependency exists;
- required authority/policy evidence remains fresh.

## 11. Explainability

Every impact decision must be reproducible from a bounded receipt containing:
- source change;
- traversed dependency paths;
- selector/slice reasoning;
- prior/current fingerprints;
- unknowns;
- final impact state and reason codes.

Required impact states:
- `AFFECTED`;
- `UNAFFECTED_PROVEN`;
- `POTENTIALLY_AFFECTED`;
- `UNKNOWN`;
- `BLOCKED_BY_STALE_EVIDENCE`.

## 12. S02 hard invariants

31. M06 dependency observations cannot silently redefine M02 graph semantics.
32. Observed material hidden dependencies cannot be discarded silently.
33. Dependency fingerprints are versioned and schema-qualified.
34. Fingerprints bind exact refs rather than implicit latest.
35. Fingerprint scope is explicit.
36. Different fingerprint scopes cannot be treated as equivalent automatically.
37. Storage locator changes are non-material unless an admitted semantic contract says otherwise.
38. Display-name/path changes cannot invalidate semantic work by default.
39. A content hash alone is insufficient as a complete causal fingerprint.
40. Dependency slices/facets must preserve their M02 meaning.
41. Unknown mandatory dependency state blocks safe reuse.
42. Unknown materiality cannot be coerced to non-material.
43. Absence from a partial reverse index cannot prove unaffected.
44. Reverse dependency indexes are derived/rebuildable operational state.
45. Index corruption cannot authorize reuse.
46. Impact analysis must expose direct and transitive causal paths.
47. Impact analysis must preserve an unknown frontier.
48. `UNAFFECTED_PROVEN` requires positive sufficient evidence.
49. Affected and potentially affected are distinct.
50. Stale evidence cannot prove unaffected.
51. Hidden dependency discovery invalidates incompatible prior reuse assumptions.
52. Dependency discovery creates new evidence/history rather than rewriting old receipts.
53. Dynamic dependency discovery must be bounded and explicit.
54. Wildcards cannot falsely claim complete dependency closure.
55. Policy/rights/security refs may be material to admissibility without being media bytes.
56. M05 identity-sensitive refs may invalidate consumers without transferring identity authority to M06.
57. Toolchain/environment facts affect fingerprints only when declared materially relevant.
58. Hardware/performance changes cannot silently change semantic dependency truth.
59. Impact receipts are analysis evidence, not execution/promotion authority.
60. HIVE/agents may suggest dependency relationships but cannot self-admit them as canonical material dependencies.

These extend S01 invariants 1–30 and remain candidates until final M06 contract freeze.

## 13. Proprietary technology candidates

### IRIS-CFM — Causal Fingerprint Matrix
Typed multidimensional fingerprints that preserve semantic, identity, policy, toolchain and reconstruction dimensions independently instead of flattening causality into one cache key.

### IRIS-MSI — Minimum Sufficient Invalidation
Proof-oriented invalidation engine that computes the smallest safe dirty frontier only after correctness evidence establishes what is unaffected.

### IRIS-HDS — Hidden Dependency Sentinel
Runtime observation firewall that detects undeclared material dependencies, invalidates unsafe reuse assumptions and emits governed discovery receipts.

### IRIS-ICX — Impact Cone Explainer
Deterministic causal-path receipt format explaining why each target is affected, proven unaffected, uncertain or blocked.

### IRIS-RDI — Rebuildable Dependency Index
Derived reverse-dependency index with completeness/freshness state so index absence can never masquerade as proof of no impact.

All remain planning candidates pending Technology Review and prior-art review.

## 14. S02 acceptance evidence targets

Later implementation must prove:
- deterministic versioned fingerprints;
- facet/slice-specific invalidation;
- direct/transitive impact correctness;
- positive proof requirement for `UNAFFECTED_PROVEN`;
- hidden dependency discovery blocks unsafe reuse;
- partial/stale/corrupt index behavior fails closed;
- exact-ref versus implicit-latest regression;
- policy/identity-sensitive invalidation;
- non-material locator/display changes do not cause false rebuilds;
- impact explanation round-trip and deterministic reason paths;
- domain-neutral behavior across image, 3D, video, audio and metadata-only productions.

## S02 STOP CONDITION

S02 is complete for module planning when:
- M02 dependency authority is preserved;
- dependency observation/fingerprint/delta semantics are explicit;
- reverse-index completeness/freshness semantics are explicit;
- hidden/dynamic dependency behavior fails closed;
- impact states and explainability are explicit;
- minimum-sufficient invalidation is correctness-first;
- invariants 31–60 are recorded;
- S02 proprietary candidates are registered;
- checkpoint may advance to M06 S03 planning;
- no M06 product implementation is introduced.


# S03 — Incremental regeneration and selective rebuild

Status: `COMPLETE_FOR_MODULE_PLANNING`

## 1. Goal

Turn S02 impact evidence into a correctness-first selective-build decision layer that reuses, verifies, repairs or rebuilds only what is justified, while preserving M02 build semantics and M01 final-quality authority.

## 2. Authority boundary

M02 remains canonical for BuildDelta, DirtyFrontier, RepairFrontier, WorkDisposition, ReuseClass, ReuseReceipt, BuildPlan and BuildExplainTrace.

M06 operationalizes these contracts using exact revision/materialization state, S02 fingerprints and impact receipts. It may not invent a second build lifecycle or treat cache presence as reuse authority.

M01 remains authority for quality/evaluation/promotion. M49 owns actual repair engines. M13 owns runtime cache/performance optimization. M55 owns physical storage/cache.

## 3. Selective work dispositions

Operational dispositions:
- `REUSE_EXACT`: reuse is fully admitted for the required semantics/reproducibility class.
- `REUSE_WITH_VERIFICATION`: candidate reuse requires declared integrity/freshness/quality checks before admission.
- `VERIFY_ONLY`: bytes need not regenerate, but blocking evidence must be refreshed.
- `REPAIR_CANDIDATE`: bounded defect/change may be handled through M49-compatible repair semantics.
- `REBUILD_PARTIAL`: regenerate an admitted slice/subgraph.
- `REBUILD_FULL_TARGET`: regenerate the complete target.
- `BLOCKED`: insufficient/unsafe evidence prevents work admission.
- `NO_WORK_PROVEN`: positive proof that the target remains valid.

These refine operational execution decisions and map to M02 semantics rather than replacing them.

## 4. Reuse admission

Reuse requires positive evidence across all material dimensions:
- exact semantic/revision binding;
- compatible S02 causal fingerprint scope;
- materialization integrity/availability;
- required quality evidence freshness;
- identity-sensitive refs;
- policy/rights/security freshness where material;
- reproducibility/reuse class;
- no unresolved hidden dependency;
- no incompatible schema/toolchain change.

A cache hit, matching filename, matching content digest or provider claim alone never admits reuse.

## 5. Selective rebuild

A partial rebuild is legal only when:
- the target exposes an admitted rebuild boundary;
- dependency selectors/slices prove the boundary;
- unchanged inputs outside the boundary remain compatible;
- output composition semantics define how rebuilt and reused parts combine;
- protected identity/quality constraints survive recomposition;
- reconstruction evidence can explain the mixed result.

If any mandatory boundary is unknown, escalate to a larger safe rebuild frontier.

## 6. Rebuild frontier expansion

Frontiers expand monotonically when evidence becomes less certain.

Candidate escalation:
`NO_WORK_PROVEN -> VERIFY_ONLY -> REUSE_WITH_VERIFICATION -> REPAIR_CANDIDATE / REBUILD_PARTIAL -> REBUILD_FULL_TARGET -> BLOCKED`.

The system may choose a more conservative action, but cannot choose a less conservative action without evidence.

## 7. Reuse receipts

Every admitted reuse emits a receipt binding:
- reused exact materialization/revision;
- target build;
- causal fingerprint comparison;
- reuse class;
- required verification results;
- quality/policy freshness refs;
- decision reason codes;
- authority/version of the admission rule.

Receipts are immutable evidence and never imply future reuse automatically.

## 8. Partial regeneration receipts

Mixed rebuilt/reused outputs must declare:
- rebuilt slices/components;
- reused slices/components;
- source revisions/materializations;
- composition/reassembly rule version;
- resulting digest/materialization ref;
- unresolved uncertainty;
- verification/evaluation obligations.

A partial rebuild cannot hide its reused ancestry.

## 9. Stochastic work

For stochastic/non-exactly-replayable operations:
- fingerprint equality does not claim byte-identical replay;
- reuse class must state what equivalence is promised;
- seeds/parameters are recorded when available but do not overclaim determinism;
- quality/identity acceptance remains evidence-driven;
- selective rebuild may create a new valid variant/materialization without pretending it reproduces historical bytes.

## 10. Repair boundary

M06 can identify `REPAIR_CANDIDATE` and carry repair frontier/evidence. M49 owns defect localization and actual repair strategy/execution.

Repair must:
- create new history;
- preserve source ancestry;
- obey M03 constraints/M05 protected identity;
- return through M01/M02 validation gates;
- never overwrite an immutable master.

## 11. Failure recovery

Interrupted/failed selective builds:
- do not corrupt previously admitted masters;
- keep incomplete outputs quarantined/unadmitted;
- record completed units and receipts;
- may resume only when exact dependencies/fingerprints remain valid;
- invalidate resumability when material causal inputs changed;
- distinguish retry, resume, rebuild and repair.

## 12. S03 hard invariants

61. Selective rebuild decisions must map to M02 build semantics.
62. Cache presence alone never authorizes reuse.
63. Content digest equality alone never authorizes semantic reuse.
64. Reuse requires positive evidence for all mandatory material dimensions.
65. Unknown mandatory reuse evidence blocks reuse.
66. Reuse receipts bind exact revisions/materializations.
67. Reuse admission is scoped to one decision and does not authorize future reuse automatically.
68. Stale quality/policy evidence cannot be silently reused when materially invalidated.
69. Partial rebuild requires an admitted rebuild boundary.
70. Unknown rebuild boundaries escalate conservatively.
71. A partial rebuild declares both rebuilt and reused ancestry.
72. Recomposition rules are explicit/versioned.
73. Recomposition cannot silently weaken protected identity constraints.
74. Recomposition cannot silently lower M01-required final quality.
75. Dirty frontier minimization occurs only after correctness proof.
76. Frontier expansion is conservative when uncertainty increases.
77. A less conservative disposition requires stronger evidence.
78. `NO_WORK_PROVEN` requires positive proof.
79. `VERIFY_ONLY` cannot be converted to no-work without successful required verification.
80. Failed/incomplete outputs cannot become admitted masters.
81. Interrupted work cannot mutate an existing admitted master.
82. Resume requires unchanged material causal bindings.
83. Material input change invalidates incompatible resume state.
84. Retry, resume, repair and rebuild remain distinct operations.
85. Stochastic fingerprint equality cannot claim byte-identical replay.
86. Reuse class explicitly states the equivalence guarantee.
87. Seeds/parameters cannot turn stochastic work into falsely deterministic history.
88. M49 remains repair execution authority.
89. Repair creates new history and preserves ancestry.
90. HIVE/agents may propose selective work but cannot self-admit unsafe reuse or promotion.

These extend S01-S02 invariants 1–60 and remain candidates until final M06 contract freeze.

## 13. Proprietary technology candidates

### IRIS-SRE — Selective Regeneration Engine
Evidence-driven planner mapping causal impact into exact reuse/verify/repair/rebuild dispositions while preserving M02 authority.

### IRIS-RAP — Reuse Admission Passport
Immutable, scoped reuse receipt carrying fingerprints, freshness, equivalence class and authority evidence so a cache hit can never masquerade as correctness.

### IRIS-FEX — Frontier Expansion Matrix
Conservative escalation mechanism that widens a rebuild frontier as uncertainty or invalidation increases.

### IRIS-MXR — Mixed Reconstruction Receipt
Ancestry-preserving receipt for outputs assembled from rebuilt and reused components, making partial regeneration fully explainable.

### IRIS-SDS — Stochastic Determinism Shield
Firewall preventing seeds/fingerprint equality from overclaiming exact reproducibility for stochastic generation.

All remain candidates pending Technology Review and prior-art review.

## 14. S03 acceptance evidence targets

Later implementation must prove:
- disposition mapping and conservative escalation;
- cache-hit rejection without reuse evidence;
- exact reuse receipt round-trip;
- partial rebuild ancestry and recomposition proof;
- protected M05 identity and M01 quality constraints across recomposition;
- stochastic reuse semantics without false deterministic claims;
- interruption/quarantine/resume invalidation behavior;
- M49 repair authority boundary;
- deterministic explain traces for work decisions;
- domain-neutral selective rebuild across image, 3D, video, audio and metadata-only examples.

## S03 STOP CONDITION

S03 is complete for module planning when:
- selective work dispositions and reuse admission are explicit;
- partial rebuild/recomposition boundaries are explicit;
- conservative frontier expansion is explicit;
- stochastic work cannot overclaim determinism;
- repair authority remains M49;
- interruption/resume semantics are fail-safe;
- invariants 61–90 are recorded;
- S03 proprietary candidates are registered;
- checkpoint may advance to M06 S04 planning;
- no M06 product implementation is introduced.


# S04 — Reproducibility receipts and deterministic reconstruction

Status: `COMPLETE_FOR_MODULE_PLANNING`

## 1. Goal

Define evidence and reconstruction semantics that allow IRIS to state exactly what can be reconstructed, under which equivalence guarantee, from which immutable inputs and execution facts, without claiming deterministic replay for stochastic or externally mutable systems.

## 2. Authority boundary

M02 remains canonical for reproducibility class, attempts, build plans, snapshots, lifecycle and receipt-based state semantics.

M06 owns operational reconstruction manifests/receipts and verification of reconstruction inputs under M02 contracts.

M11/M12 own worker/compute execution. M14-M18 own model/workflow/provider supply-chain details. M53/M54 own provenance/rights/security authority. M55 owns physical bytes/storage. M60 owns final integration/recovery acceptance.

## 3. Reproducibility classes

M06 consumes/operationalizes explicit classes rather than a boolean reproducible flag:

- `EXACT_BYTES`: admitted contract can reproduce byte-identical canonical output under declared conditions.
- `EXACT_SEMANTIC_STATE`: canonical semantic state can be reconstructed exactly while physical encoding may differ.
- `EQUIVALENT_WITHIN_CONTRACT`: result may differ physically but satisfies an explicit equivalence contract.
- `STOCHASTIC_REEXECUTABLE`: execution inputs are known, but replay is not claimed identical.
- `REFERENCE_RECONSTRUCTABLE`: historical state can be reconstructed from retained immutable references/materializations without re-executing generation.
- `NON_RECONSTRUCTABLE`: required inputs/capabilities/evidence are intentionally or irrecoverably unavailable.
- `UNKNOWN`: evidence is insufficient to classify safely.

A stronger class may never be inferred from a weaker class without evidence.

## 4. ReconstructionManifest

A reconstruction manifest binds:
- target semantic/revision/master ref;
- required M02 snapshot/build refs;
- M03 intent/constraint refs;
- M04 representation refs;
- M05 identity refs where consumed;
- exact S01 revision/materialization manifests;
- S02 dependency fingerprint closure;
- S03 reuse/mixed-reconstruction receipts;
- workflow/model/toolchain capability refs;
- parameters/seeds where applicable;
- environment/hardware facts only when materially required;
- policy/rights/security refs required for lawful/admitted reconstruction;
- expected reproducibility class;
- verification procedure/version;
- required external availability assumptions.

The manifest is immutable once admitted.

## 5. ReproducibilityReceipt

A receipt records what was actually proven, not what was intended.

It includes:
- manifest digest/version;
- reconstruction attempt ref;
- observed input closure;
- capability/toolchain resolution;
- verification results;
- expected versus achieved class;
- output materialization refs/digests;
- semantic/equivalence checks;
- missing/unknown dependencies;
- divergence reasons;
- authority/evidence refs;
- timestamp/sequence metadata where required by M02 without making wall-clock time identity.

## 6. Deterministic reconstruction

An `EXACT_BYTES` claim requires all byte-material dimensions to be pinned and verified, including canonicalization/encoding/toolchain behavior where relevant.

A seed is only one input. Seed equality never proves deterministic execution by itself.

Hardware/runtime nondeterminism, provider drift, floating-point behavior, mutable external APIs, unpinned models/workflows or unspecified encoding invalidate an unjustified exact-byte claim.

When exact replay is impossible, the system must downgrade the claim explicitly rather than fabricate success.

## 7. Semantic/equivalence reconstruction

For outputs where byte equality is neither possible nor necessary, equivalence must be governed by a versioned contract.

Examples may include:
- exact semantic graph/state;
- bounded numeric tolerance;
- M05 protected identity preservation;
- M01 quality/fidelity obligations;
- media/domain-specific future evaluator refs.

M06 records and verifies the contract references but does not steal evaluator/domain authority.

## 8. External and mutable dependencies

External mutable resources require:
- immutable snapshot/ref when available;
- version/provider receipt;
- availability assumption;
- policy for unavailable historical versions;
- explicit classification when exact reconstruction is impossible.

A URL, provider name or "latest" model cannot satisfy historical reconstruction identity.

## 9. Reconstruction from retained materialization

Reconstruction need not always mean re-execution.

When an admitted immutable materialization and its closure remain available and valid, M06 may reconstruct historical production state by reference/materialization restoration. The receipt must distinguish restoration from regeneration.

## 10. Divergence

Divergence states include:
- `NONE_PROVEN`;
- `BYTE_DIVERGENCE`;
- `SEMANTIC_DIVERGENCE`;
- `EQUIVALENCE_CONTRACT_FAILURE`;
- `DEPENDENCY_UNAVAILABLE`;
- `TOOLCHAIN_UNAVAILABLE`;
- `POLICY_BLOCKED`;
- `UNKNOWN`.

Divergence never rewrites the historical receipt. A new attempt creates new evidence.

## 11. Reconstruction safety

Reconstruction:
- cannot bypass current mandatory security/rights controls merely because historical execution was once allowed;
- cannot silently substitute a dependency;
- cannot overwrite historical masters;
- cannot promote reconstructed output without required M01/M02 gates;
- quarantines outputs whose integrity/equivalence is not admitted.

Historical truth and current permission are distinct.

## 12. S04 hard invariants

91. Reproducibility is an explicit class, not a boolean shortcut.
92. Stronger reproducibility cannot be inferred from weaker evidence.
93. Reconstruction manifests bind exact/versioned refs, never implicit latest.
94. Admitted reconstruction manifests are immutable.
95. Reproducibility receipts record achieved evidence, not intended claims.
96. A seed alone never proves deterministic replay.
97. Fingerprint equality alone never proves exact-byte replay.
98. Exact-byte claims require all materially byte-affecting dimensions to be pinned/verified.
99. Unpinned mutable provider/model/workflow dependencies prevent unjustified exact replay.
100. Runtime/hardware nondeterminism must be represented when materially relevant.
101. Exact semantic reconstruction is distinct from exact-byte reconstruction.
102. Equivalence reconstruction requires an explicit versioned equivalence contract.
103. M06 cannot invent domain equivalence criteria owned by later evaluators.
104. M01 quality authority remains external to reconstruction truth.
105. M05 protected identity authority remains external to reconstruction truth.
106. Historical external dependencies require immutable/versioned evidence where available.
107. URLs/provider names/paths cannot serve as historical identity by themselves.
108. Missing historical dependencies cannot be silently replaced.
109. Restoration from retained materialization is distinct from regeneration.
110. Restoration still verifies declared integrity.
111. Reconstruction attempts create new evidence and never rewrite historical receipts.
112. Divergence states remain explicit.
113. Byte divergence and semantic divergence are distinct.
114. Unknown divergence cannot be coerced to success.
115. Failed equivalence cannot be hidden by successful execution.
116. Current rights/security controls cannot be bypassed by historical permission.
117. Historical execution permission does not imply current permission.
118. Reconstructed outputs cannot overwrite immutable masters.
119. Reconstructed outputs require normal promotion/quality gates before becoming accepted masters.
120. HIVE/agents may propose reconstruction plans but cannot self-certify reproducibility or equivalence.

These extend S01-S03 invariants 1–90 and remain candidates until final M06 contract freeze.

## 13. Proprietary technology candidates

### IRIS-RCL — Reproducibility Class Lattice
Ordered evidence model preventing accidental promotion from stochastic or semantic equivalence into exact-byte reproducibility.

### IRIS-RXM — Reconstruction eXactness Manifest
Immutable closure binding every materially relevant reconstruction input, capability and verification contract.

### IRIS-DRG — Divergence Reason Graph
Causal graph explaining where and why reconstruction diverged across bytes, semantics, dependencies, toolchain, policy or unknown state.

### IRIS-ESB — Equivalence Safety Bridge
Versioned bridge from M06 reconstruction to M01/M05/future domain evaluators without transferring their authority into M06.

### IRIS-HPR — Historical Permission Firewall
Separates historical execution facts from present-day rights/security authorization so reproducibility cannot become a policy bypass.

All remain candidates pending Technology Review and prior-art review.

## 14. S04 acceptance evidence targets

Later implementation must prove:
- reproducibility-class ordering and non-escalation;
- deterministic manifest serialization;
- exact-byte versus exact-semantic distinction;
- seed-equality rejection as sole determinism proof;
- explicit downgrade when mutable/unpinned dependencies exist;
- restoration versus regeneration receipts;
- divergence classification and immutable attempt history;
- equivalence-contract bridge without M01/M05 authority leakage;
- historical/current permission separation;
- domain-neutral reconstruction examples across deterministic, stochastic and retained-materialization workflows.

## S04 STOP CONDITION

S04 is complete for module planning when:
- reproducibility classes are explicit;
- reconstruction manifest/receipt semantics are explicit;
- deterministic claims are evidence-bounded;
- semantic/equivalence reconstruction is contract-based;
- mutable/external dependency behavior fails closed;
- restoration and regeneration are distinguished;
- historical permission cannot bypass current policy;
- invariants 91–120 are recorded;
- S04 proprietary candidates are registered;
- checkpoint may advance to M06 S05 planning;
- no M06 product implementation is introduced.
