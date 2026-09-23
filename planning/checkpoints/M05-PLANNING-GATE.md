# IRIS M05 Planning Gate

Status: `S03_COMPLETE_S04_NEXT`
Issue: `#37`
Branch: `m05-asset-dna-planning`
Authorized main baseline: `6f2311b59f5da91778d3fc9d9fe1572953a0c60b`

## Sessions

- S01 — Asset DNA schema and identity invariants: COMPLETE_FOR_MODULE_PLANNING
- S02 — Character, creature, object, product and environment DNA: COMPLETE_FOR_MODULE_PLANNING
- S03 — SceneDNA, Motion DNA, Voice DNA and Brand DNA links: COMPLETE_FOR_MODULE_PLANNING
- S04 — Identity anchors, mutation boundaries and drift detection: NEXT
- S05 — DNA branching, compatibility and reusable DNA marketplace contract: NOT_STARTED

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

## Candidate planning invariants

S01-S03 record 90 candidate hard invariants. These remain planning candidates until S04-S05 consolidation and final contract freeze.

## Technology candidates

`IRIS-DNAX-001..090` registered as design-history candidates.

## External references

- RFC 9562 UUID
- OpenUSD AssetInfo
- VRM 1.0
- C2PA

References only. No new runtime dependency.

## Next legal action

Plan S04 identity anchors, mutation boundaries and drift detection on this same branch/issue, preserving S01-S03 authority boundaries.

Do not implement M05.
Do not freeze the M05 contract yet.
