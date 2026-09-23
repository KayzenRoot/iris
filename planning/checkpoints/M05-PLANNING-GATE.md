# IRIS M05 Planning Gate

Status: `FORWARD_COMPAT_PASS_CONTRACT_FREEZE_NEXT`
Issue: `#37`
Branch: `m05-asset-dna-planning`
Authorized main baseline: `6f2311b59f5da91778d3fc9d9fe1572953a0c60b`

## Sessions

- S01 — Asset DNA schema and identity invariants: COMPLETE_FOR_MODULE_PLANNING
- S02 — Character, creature, object, product and environment DNA: COMPLETE_FOR_MODULE_PLANNING
- S03 — SceneDNA, Motion DNA, Voice DNA and Brand DNA links: COMPLETE_FOR_MODULE_PLANNING
- S04 — Identity anchors, mutation boundaries and drift detection: COMPLETE_FOR_MODULE_PLANNING
- S05 — DNA branching, compatibility and reusable DNA marketplace contract: COMPLETE_FOR_MODULE_PLANNING

## Current guard

Planning/docs only. No M05 implementation is authorized.

## Baseline evidence

- M04 implementation and post-merge reconciliation are complete.
- `main`: `6f2311b59f5da91778d3fc9d9fe1572953a0c60b`.
- Exact-main Governance: `35814271172 / 107032325686` — PASS.
- Full suite: `2677/2677 OK`.
- Required governance artifacts: 35.

## S01 artifacts

- research: `planning/research/M05-S01-ASSET-DNA-SCHEMA-IDENTITY-INVARIANTS-RESEARCH-2026-09-23.md`
- module plan: `planning/modules/M05-ASSET-DNA-CROSS-MODAL-IDENTITY.md`
- technology registry: `planning/technology-registry/M05-TECHNOLOGIES.md`

## S01 boundary decisions

- persistent DNA identity is separate from M04 representation identity;
- names/paths/content hashes/provider IDs/prompts/embeddings are not canonical identity;
- immutable DNA revisions;
- explicit identity criticality and mutability;
- four-state applicability semantics;
- canonical/evidence twin-plane architecture;
- cross-modal anchors and projection contracts;
- observations cannot self-promote to canonical truth;
- M02 remains project/history authority;
- M06 remains persistence/CAS authority;
- M53/M54 remain rights/provenance/privacy/security authority;
- M39/M40/M41/M43/M46 remain domain runtime/authority owners.

## S02 artifacts

- research: `planning/research/M05-S02-DOMAIN-DNA-FAMILIES-RESEARCH-2026-09-23.md`
- module plan: S02 in `planning/modules/M05-ASSET-DNA-CROSS-MODAL-IDENTITY.md`
- technology registry: `IRIS-DNAX-031..060`

## S02 boundary decisions

- CLASS / ARCHETYPE / INDIVIDUAL / VARIANT are distinct;
- one common DNA core, specialized through family profiles;
- persistent component identity is explicit and independent of ordering/name;
- Character/Creature/Object/Product/Environment profiles are typed;
- persistent/contextual/observed appearance are separated;
- Product family/model/SKU/package/instance levels are explicit;
- EnvironmentDNA remains distinct from M04 SceneIR;
- family reclassification requires explicit migration/projection semantics.

## S03 artifacts

- research: `planning/research/M05-S03-CROSS-MODAL-DNA-LINKS-RESEARCH-2026-09-23.md`
- module plan: S03 in `planning/modules/M05-ASSET-DNA-CROSS-MODAL-IDENTITY.md`
- technology registry: `IRIS-DNAX-061..090`

## S03 boundary decisions

- M30 owns MotionDNA; M05 stores revision-pinned MotionDNALink;
- M40 owns VoiceDNA; M05 stores revision-pinned VoiceDNALink;
- M46 owns BrandDNA; M05 stores revision-pinned BrandDNALink;
- M45 Campaign DNA remains advertising authority and is not BrandDNA;
- SceneIdentityDNA is reusable identity composition, not M04 SceneIR or M43 Canon truth;
- cross-modal bindings/obligations do not transfer mutation or quality authority;
- external links never silently follow latest revisions;
- future domain-DNA families use the same owner/family/revision link fabric.

## S04 artifacts

- research: `planning/research/M05-S04-IDENTITY-MUTATION-DRIFT-RESEARCH-2026-09-23.md`
- module plan: S04 in `planning/modules/M05-ASSET-DNA-CROSS-MODAL-IDENTITY.md`
- technology registry: `IRIS-DNAX-091..120`

## S04 boundary decisions

- anchor authority/lifecycle is explicit and confidence cannot promote authority;
- drift evidence is path-level, typed and multi-dimensional;
- one scalar similarity score cannot determine identity continuity;
- repair is representation correction, not canonical mutation;
- mutation requires proposal + authority + explicit decision;
- same-identity mutation creates a new immutable revision;
- identity break creates a new dna_id with lineage;
- split/consolidation preserve source histories;
- M01 retains quality authority, M37 temporal continuity authority, M39 digital-human runtime/persona domain authority;
- M05 remains the generic persistent identity root;
- M53/M54 retain protected provenance/rights/security authority.

## S05 artifacts

- research: `planning/research/M05-S05-BRANCHING-COMPATIBILITY-MARKETPLACE-RESEARCH-2026-09-23.md`
- module plan: S05 in `planning/modules/M05-ASSET-DNA-CROSS-MODAL-IDENTITY.md`
- technology registry: `IRIS-DNAX-121..150`

## S05 boundary decisions

- M05 DNA lineage is semantic identity lineage, not M02 project branching;
- M06 owns content-addressed production revisions/builds;
- compatibility is directional and multi-axis;
- migrations declare explicit preservation/loss/defaults and identity continuity impact;
- reusable DNA package identity is distinct from dna_id;
- M53 owns rights/license/consent/provenance;
- M54 owns security/restricted-content policy;
- M55 owns storage/CAS;
- M58 may expose APIs/conformance tooling;
- M59 owns concrete export/publishing/delivery;
- package import is staged and cannot overwrite canonical DNA;
- canonical DNA packages are non-executable by default.

## Final Technology Review

- artifact: `planning/reviews/M05-FINAL-TECHNOLOGY-REVIEW.md`
- verdict: `APPROVED_FOR_FORWARD_COMPATIBILITY`
- `IRIS-DNAX-001..150` consolidated into `F-M05-01..25`
- mapping integrity: **150/150 exactly once; 0 missing; 0 duplicates**
- findings: M05-PLAN-R01..R05 closed or closed-for-forward-scan
- no implementation admitted
- no contract freeze yet

## Candidate planning invariants

S01-S05 record 150 candidate hard invariants. Final Technology Review is complete; invariants remain freeze candidates until the Forward Compatibility Scan and contract freeze.

## Technology candidates

`IRIS-DNAX-001..150` remain design-history references; consolidated freeze-candidate families are `F-M05-01..25`.

## External references

- RFC 9562 UUID
- OpenUSD AssetInfo
- VRM 1.0
- C2PA

References only. No new runtime dependency.

## Forward Compatibility Scan

- artifact: `planning/compatibility/M05-FORWARD-COMPATIBILITY-SCAN.md`
- modules scanned: **M06-M60 (55 modules)**
- verdict: `PASS_WITH_EXTENSION_PORTS`
- critical ownership conflicts remaining: **0**
- chat-fixable conflicts corrected: **2**
- future extension/ref families: **22**
- M02/M06 semantic-vs-operational build/version wording aligned
- M39 S01 renamed to M05-bound Persona Continuity Engine
- no implementation admitted

## Next legal action

Prepare the M05 contract freeze candidate from S01-S05 + Final Technology Review + Forward Compatibility Scan.

Do not implement M05.
