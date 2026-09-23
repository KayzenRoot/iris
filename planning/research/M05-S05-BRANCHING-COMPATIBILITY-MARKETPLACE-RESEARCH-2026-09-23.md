# M05 S05 Research — DNA Branching, Compatibility & Reusable Package Contract

Date: 2026-09-23
Module: M05 — Asset DNA 2.0 & Cross-Modal Identity
Session: S05
Status: `COMPLETE_FOR_MODULE_PLANNING`
Issue: #37
Authorized baseline: `6f2311b59f5da91778d3fc9d9fe1572953a0c60b`

## Research question

How should IRIS represent identity lineage, compatibility, portable/reusable DNA packages and marketplace exchange without duplicating M02 branch/history authority, M06 production versioning, M53 rights, M54 security, M55 storage or M59 publishing?

## Key conclusion

M05 needs semantic identity lineage and package contracts, not a second VCS, storage system or commerce platform.

M05 owns:
- identity-level lineage semantics;
- compatibility/equivalence declarations between DNA revisions/packages;
- migration requirements for DNA schemas;
- reusable DNA package manifest semantics;
- package conformance/qualification requirements;
- marketplace-facing compatibility/rights/security references.

M05 does not own:
- project branches/snapshots/rollback;
- production build/version state;
- storage/CAS/download;
- payments/listings/ranking/commerce operations;
- license/consent authority;
- malware/security scanning runtime;
- export/upload/delivery runtime.

## M02 / M05 branching distinction

M02 owns project and production branches.

M05 may express only semantic identity lineage such as:
- SAME_IDENTITY_REVISION;
- VARIANT_DERIVATION;
- ARCHETYPE_DERIVATION;
- IDENTITY_BREAK_DERIVATION;
- SPLIT_CHILD;
- CONSOLIDATION_CONTINUATION;
- TEMPLATE_INSTANTIATION.

These relationships say how identities relate, not where commits live.

No M05 lineage operation creates a Git branch, M02 production branch or rollback state.

## M06 boundary

M06 owns production-state versioning, content-addressed revisions, immutable masters, dependency fingerprints, rebuild/reconstruction and rollback.

M05 DNA revisions remain semantic identity revisions.

A future M06 build/master may reference one M05 DNA revision, but:
- M05 does not own build artifacts;
- M06 does not redefine identity semantics;
- content-addressed build IDs are not persistent subject IDs.

## DNA compatibility model

S05 introduces `DNACompatibilityProfile`.

Compatibility must be multi-axis:
- schema compatibility;
- family/profile compatibility;
- identity-trait compatibility;
- component compatibility;
- anchor compatibility;
- cross-modal link compatibility;
- rights/policy compatibility refs;
- extension compatibility;
- consumer capability compatibility.

Candidate outcomes:
- `EXACT`;
- `COMPATIBLE`;
- `COMPATIBLE_WITH_LOSS`;
- `REQUIRES_MIGRATION`;
- `BREAKING`;
- `INDETERMINATE`.

No single semantic-version number can prove compatibility.

## Compatibility direction

Compatibility is directional.

Example:
- a consumer that knows DNA schema v1 may accept a v1.1 package with optional opaque traits;
- a v1.1 consumer may require mandatory traits unavailable in v1;
- one CharacterDNA variant may be usable by a generic renderer but not by a strict digital-human profile.

Therefore compatibility is always:
`source -> target consumer/profile`.

## DNA migration

`DNAMigrationPlan` describes semantic schema/revision transformation.

It must declare:
- source schema/family/version;
- target schema/family/version;
- transformed trait paths;
- preserved traits;
- dropped/lossy traits;
- defaults introduced;
- anchor/link changes;
- identity continuity expectation;
- required authority/policy;
- deterministic migration receipt requirements.

Unknown mandatory semantics fail closed.

Migration cannot silently convert identity break into same-identity compatibility.

## Reusable DNA package

S05 introduces `ReusableDNAPackageManifest`.

The manifest may contain/reference:
- package ID/version;
- one or more M05 DNA identities/revisions;
- included family/profile schemas;
- canonical fingerprints;
- required external domain-DNA refs;
- optional domain-DNA refs;
- package compatibility profile;
- migration capabilities;
- rights/license/consent refs;
- provenance refs;
- security classification;
- restricted-evidence refs without sensitive payloads;
- dependency refs;
- conformance requirements;
- human-readable metadata.

It does not need to embed storage blobs, model weights or private evidence.

## Package identity

Package identity is not subject identity.

Rules:
- package ID/version identifies the distributable contract;
- dna_id identifies persistent subject identity;
- build/archive/content hashes belong to their owning layers;
- repackaging without semantic change may change package bytes while preserving DNA identity;
- one package may carry multiple DNA identities when explicitly declared.

## Portable bundle levels

Candidate package levels:
- `INTERFACE_ONLY` — public identity/profile/compatibility surface;
- `PORTABLE_CANONICAL` — portable canonical DNA and permitted refs;
- `PRODUCTION_REFERENCE` — adds domain refs needed for production integration;
- `RESTRICTED_REFERENCE` — contains refs to protected vault/evidence but not payload copies.

A marketplace/export policy may forbid some levels.

## Marketplace contract boundary

M05 defines a `DNAMarketplaceContract` as exchange metadata and conformance expectations only.

It may expose:
- package identity/version;
- subject family/profile;
- compatibility claims;
- required consumer capabilities;
- rights/license/consent refs;
- provenance refs;
- security classification;
- geographic/use/role restrictions as external policy refs;
- allowed derivative/mutation classes;
- attribution requirements;
- support/deprecation status.

It does not own:
- payment;
- pricing;
- seller reputation;
- listing search/ranking;
- file hosting/CDN;
- tax/compliance processing;
- storefront UI.

Those are outside M05 unless a later module explicitly owns them.

## Rights and consent

M53 remains authority for:
- rights;
- licenses;
- consent;
- provenance;
- C2PA/content credentials.

M05 package/marketplace contracts carry immutable refs to the relevant M53 records.

No package-level boolean such as `licensed=true` replaces M53 authority.

## Security

M54 remains authority for:
- permissions;
- restricted content;
- likeness/identity protections;
- secret handling;
- sandbox policy;
- incident/audit policy.

M05 package manifests carry security classification and required policy refs.

A DNA package cannot self-declare itself safe.

## Storage and distribution

M55 owns media CAS/storage/cache/archive.
M59 owns publishing/export/delivery compilation.

M05 defines package semantics, not where bytes live or how they are published.

M58 may later expose package validation/import/export/conformance APIs.

## Dependency closure

A reusable DNA package must declare its dependency closure.

Dependencies are typed:
- REQUIRED_CANONICAL;
- REQUIRED_EXTERNAL_DNA;
- OPTIONAL_EXTERNAL_DNA;
- POLICY_REF;
- SCHEMA_REF;
- EVIDENCE_REF;
- TOOLING_CAPABILITY.

Missing required dependencies fail closed.
Optional dependencies remain explicitly optional.

## Import admission

Importing a package is not equivalent to admitting it as local canonical DNA.

Proposed import states:
- `PARSED`;
- `VALIDATED`;
- `COMPATIBILITY_CHECKED`;
- `POLICY_CHECKED`;
- `QUARANTINED`;
- `ADMISSION_PROPOSED`;
- `ADMITTED`;
- `REJECTED`.

Import cannot overwrite an existing dna_id/revision silently.

Collision/equivalence handling routes through S04 semantics.

## Package conformance

`DNAPackageConformanceReport` checks:
- manifest integrity;
- schema/version support;
- canonical fingerprints;
- dependency closure;
- compatibility claims;
- required links;
- rights/provenance refs present;
- security refs present;
- restricted payload policy;
- deterministic canonical serialization;
- unknown mandatory extension handling.

Conformance does not prove legal rights or safe content. It proves contract/schema conformance.

## Deprecation and compatibility lifecycle

DNA schemas/packages may be:
- ACTIVE;
- DEPRECATED;
- SECURITY_RESTRICTED;
- RETIRED.

Deprecation:
- never rewrites old revisions;
- carries replacement/migration refs;
- cannot silently break existing consumers;
- must retain auditability.

## Supply-chain posture

S05 seeds supply-chain safety without becoming M54:
- deterministic manifest/fingerprint;
- provenance refs;
- declared dependencies;
- no executable code required in canonical DNA package;
- arbitrary embedded scripts/plugins forbidden by default;
- external tooling refs are capability metadata only;
- package import remains fail-closed for unknown mandatory semantics.

## Threat model additions

S05 must defend against:
- M05 semantic branch mistaken for M02 project branch;
- package ID mistaken for dna_id;
- semver number treated as proof of compatibility;
- silent lossy migration;
- import overwriting canonical identity;
- package self-declaring rights/safety;
- missing dependency treated as optional;
- executable payload hidden in DNA package;
- marketplace bundle copying restricted biometric/private evidence;
- stale external DNA links;
- rights/consent refs stripped during repackaging;
- one package claiming equivalence to an existing dna_id without review;
- deprecated schema silently accepted forever.

## S05 outcome

S05 completes functional planning for M05.

Next legal actions:
1. Final Technology Review;
2. M06-M60 Forward Compatibility Scan;
3. contract freeze candidate;
4. independent planning audit;
5. protected planning merge/reconciliation;
6. separate implementation admission.
