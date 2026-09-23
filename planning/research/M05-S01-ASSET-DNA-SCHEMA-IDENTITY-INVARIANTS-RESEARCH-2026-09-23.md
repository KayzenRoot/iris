# M05 S01 Research — Asset DNA Schema & Identity Invariants

Date: 2026-09-23
Module: M05 — Asset DNA 2.0 & Cross-Modal Identity
Session: S01
Status: `COMPLETE_FOR_MODULE_PLANNING`
Issue: #37
Authorized baseline: `6f2311b59f5da91778d3fc9d9fe1572953a0c60b`

## Research question

How should IRIS represent a persistent subject identity that survives changes in files, providers, modalities, revisions and rendering/generation techniques without confusing identity with representation, similarity or storage?

## Key conclusion

M05 needs a semantic identity layer separate from M04 representation and M06 storage.

A persistent subject cannot be safely identified only by:
- file/path;
- byte hash;
- M04 node identity;
- provider ID;
- prompt;
- perceptual hash;
- embedding;
- face/voice similarity;
- display name.

Those values can bind evidence or representations to one persistent identity, but they do not define that identity by themselves.

## External reference review

### EXT-M05-001 — RFC 9562 UUIDs
Disposition: `ACCEPTED_AS_OPAQUE_IDENTIFIER_REFERENCE`

Use:
- implementation/reference pattern for globally unique opaque IDs.

Do not use as:
- semantic definition of asset identity;
- version/history semantics;
- proof that two records represent the same real subject.

### EXT-M05-002 — OpenUSD AssetInfo
Disposition: `ACCEPTED_AS_ASSET-MANAGEMENT_REFERENCE`

Useful ideas:
- separate asset identifier, name and version;
- asset-management metadata surviving composition;
- identity/management information need not equal scene namespace/path.

Boundary:
- USD asset identifiers remain external/interchange refs;
- M05 identity is not a USD prim path or resolver path.

### EXT-M05-003 — VRM 1.0
Disposition: `ACCEPTED_AS_AVATAR-INTEROPERABILITY_REFERENCE`

Useful ideas:
- explicit humanoid structure;
- standardized avatar metadata and expression/gaze/motion interoperability;
- later Persona/Character DNA can map to VRM without becoming VRM-native.

Boundary:
- M05 must also cover non-humanoids, products, objects, environments, scenes, voice and brand identity.

### EXT-M05-004 — C2PA
Disposition: `ACCEPTED_AS_PROVENANCE-CONTENT-BINDING_REFERENCE`

Useful ideas:
- signed assertions;
- tamper-evident provenance;
- content bindings;
- asset ingredient/history evidence.

Boundary:
- provenance association is evidence;
- C2PA does not decide IRIS semantic identity continuity or mutation policy;
- M53 remains rights/provenance authority.

## Architecture findings

### Persistent identity must outlive representations

An M05 `dna_id` must survive:
- PNG -> EXR;
- 2D -> 3D;
- image -> video;
- Blender -> Maya;
- ComfyUI workflow A -> workflow B;
- model/provider upgrade;
- file relocation;
- derived LOD/proxy/master variants.

These are representation or production changes unless admitted DNA policy says identity itself changed.

### Content address is not subject identity

A content digest is excellent for immutable bytes/revisions and later M06 CAS, but any legitimate edit changes the digest. Therefore M05 requires a stable subject ID plus immutable DNA revision fingerprints.

### Embeddings are evidence, never authority

Embeddings/perceptual fingerprints can help:
- candidate matching;
- drift evidence;
- duplicate/collision discovery;
- retrieval.

They cannot:
- merge IDs automatically;
- redefine canonical traits;
- authorize mutation;
- prove legal/consent identity.

### Identity must be typed, not one monolithic vector

Cross-modal consistency requires typed trait semantics so IRIS can know whether a mismatch concerns:
- identity-defining structure;
- significant appearance;
- contextual styling;
- behavior;
- voice;
- motion;
- brand;
- scene relation;
- derived observation.

S02/S03 will specialize these categories.

## Threat model seeded in S01

M05 planning must defend against:
- filename/path identity spoofing;
- hash-as-identity confusion;
- provider observation promotion;
- embedding collision/false match;
- identity merge from similarity threshold;
- one DNA ID accidentally containing two subjects;
- two DNA IDs accidentally referring to one subject;
- downstream provider silently weakening identity traits;
- stale representation anchor treated as canonical;
- sensitive evidence copied unnecessarily into canonical DNA;
- hidden null semantics causing trait loss;
- branch/history duplication with M02.

## Open decisions for later sessions

S02:
- minimum typed trait families by subject class;
- shared versus family-specific DNA traits;
- character/creature/product/environment identity-defining defaults.

S03:
- SceneDNA/MotionDNA/VoiceDNA/BrandDNA linkage semantics;
- whether linked DNA is nested, referenced or composed;
- modality-specific authority firewalls.

S04:
- drift metric/evidence model;
- mutation proposal/admission;
- identity split/merge/equivalence;
- repair versus mutation.

S05:
- DNA compatibility/version rules;
- branching semantics that do not duplicate M02;
- reusable package/marketplace contract;
- import/export qualification and schema migration.

## S01 outcome

S01 freezes the architecture direction, not a final M05 contract.

The next legal planning step is S02.
