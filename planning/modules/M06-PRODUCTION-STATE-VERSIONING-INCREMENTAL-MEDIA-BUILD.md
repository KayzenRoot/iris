# M06 — Production State, Versioning & Incremental Media Build

Status: `S01_COMPLETE_FOR_MODULE_PLANNING`
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
