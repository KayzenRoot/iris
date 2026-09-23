# M05 Final Technology Review

Status: `APPROVED_FOR_FORWARD_COMPATIBILITY`
Date: 2026-09-23
Module: `M05 — Asset DNA 2.0 & Cross-Modal Identity`
Issue: `#37`
PR: `#38`

## Review rule

Acceptance means "admitted to the M05 freeze-candidate architecture after consolidation".

It does **not** claim novelty, patentability, legal protectability or implementation.

Detailed identifiers `IRIS-DNAX-001..150` remain design-history references. The frozen contract should depend on consolidated families `F-M05-01..25`, not on 150 independent implementation classes.

A DNAX item may represent:
- a data/contract primitive;
- a guardrail;
- a validation rule;
- an authority firewall;
- a compatibility/migration concept;
- an evidence/reporting concept.

Acceptance therefore does not imply one runtime class per DNAX.

## External prior-art disposition

| ID | Disposition | Rationale |
| --- | --- | --- |
| EXT-M05-001 RFC 9562 UUID | ACCEPTED_AS_IDENTIFIER_REFERENCE | useful opaque-ID prior art; does not define semantic subject identity |
| EXT-M05-002 OpenUSD AssetInfo | ACCEPTED_AS_ASSET-MANAGEMENT_REFERENCE | useful separation of asset metadata/identifier from scene/path identity |
| EXT-M05-003 VRM 1.0 | ACCEPTED_AS_AVATAR-INTEROPERABILITY_REFERENCE | useful humanoid/avatar interoperability reference; not universal M05 schema |
| EXT-M05-004 C2PA | ACCEPTED_AS_PROVENANCE_CONTENT_BINDING_REFERENCE | useful signed provenance/content-binding reference; not semantic identity authority |

No external reference becomes a mandatory M05 runtime dependency.

## Consolidated technology families

### F-M05-01 — Persistent Identity & Revision Core
Sources: DNAX-001, 002, 003, 017, 018.
Status: ACCEPT.
Purpose: stable persistent subject identity, immutable semantic revisions, canonical fingerprints and path-level change surfaces.

### F-M05-02 — Trait Semantics & Applicability Fabric
Sources: DNAX-004, 005, 006, 011, 012, 013, 014.
Status: ACCEPT.
Purpose: typed trait namespaces, identity criticality, mutability, salience, negative constraints, explicit applicability states and provenance reachability.

### F-M05-03 — Canonical / Evidence Authority Fabric
Sources: DNAX-007, 010, 022, 023, 094.
Status: ACCEPT_WITH_CONSOLIDATION.
Purpose: admitted identity truth remains separate from observations, similarity, filenames, provider IDs and confidence.
Note: DNAX-094 is the S04 refinement of the earlier DNAX-023 authority barrier.

### F-M05-04 — Anchor & Projection Authority Fabric
Sources: DNAX-008, 009, 019, 020, 091, 092, 093.
Status: ACCEPT.
Purpose: typed identity anchors, representation firewall, projection preservation and governed anchor lifecycle/rebind authority.

### F-M05-05 — Identity Resolution, Alias & Consolidation Fabric
Sources: DNAX-021, 026, 027, 028, 109, 110.
Status: ACCEPT_WITH_CONSOLIDATION.
Purpose: collision/conflict findings, aliases, equivalence/consolidation proposals and non-destructive redirects without auto-merge or history erasure.

### F-M05-06 — Interface Capsule & Minimum Context Fabric
Sources: DNAX-015, 016.
Status: ACCEPT.
Purpose: small always-readable identity interfaces and dependency-closed minimum sufficient DNA slices.

### F-M05-07 — Family / Profile / Extension Fabric
Sources: DNAX-030, 031, 032, 033, 055, 056, 057, 058.
Status: ACCEPT.
Purpose: one identity core with typed family profiles, bundles, explicit reclassification/projection and versioned extension namespaces.

### F-M05-08 — Persistent Component Identity Fabric
Sources: DNAX-034, 035, 045.
Status: ACCEPT.
Purpose: stable subcomponent identity, replacement/split/merge semantics and articulation continuity independent of ordering/name/topology churn.

### F-M05-09 — Character & Creature Identity Profile Fabric
Sources: DNAX-036, 037, 038, 039, 040, 041, 042.
Status: ACCEPT_WITH_DOMAIN_BOUNDARY.
Purpose: persistent appearance/morphology/signature semantics for characters and non-humanoid creatures.
Boundary: M39 owns digital-human production/runtime; M29/M30 own rigging/motion production.

### F-M05-10 — Object & Product Identity Profile Fabric
Sources: DNAX-043, 044, 046, 047, 048, 049, 050.
Status: ACCEPT.
Purpose: form/function/component identity plus explicit product family/model/SKU/package/instance levels and external commerce-ID bridges.

### F-M05-11 — Environment Identity Profile Fabric
Sources: DNAX-051, 052, 053, 054.
Status: ACCEPT_WITH_REPRESENTATION_BOUNDARY.
Purpose: persistent place/layout/landmark/ecology identity.
Boundary: M04 SceneIR represents current scene state.

### F-M05-12 — Cross-Domain DNA Link Fabric
Sources: DNAX-061, 065, 068, 072, 077, 078, 082, 083, 084, 089.
Status: ACCEPT.
Purpose: owner/family/revision-pinned links to domain-owned DNA, freshness state, validity scope and deterministic link change surfaces.

### F-M05-13 — Scene Identity Composition Fabric
Sources: DNAX-062, 063, 064, 085, 086, 087.
Status: ACCEPT_WITH_BOUNDARY.
Purpose: reusable scene/set identity, stable role slots, member continuity and governed substitution.
Boundary: not M04 SceneIR and not M43 Canon.

### F-M05-14 — Motion / Voice / Brand Link Firewall Fabric
Sources: DNAX-066, 067, 069, 071, 073, 074.
Status: ACCEPT_WITH_OWNERSHIP_SHIELD.
Purpose: identity-relevant motion/voice/brand association without importing domain production ownership.
Boundaries: M30 MotionDNA, M40 VoiceDNA, M46 BrandDNA; M45 Campaign DNA remains separate.

### F-M05-15 — Cross-Modal Binding & Obligation Graph
Sources: DNAX-075, 076, 079, 080, 081, 088.
Status: ACCEPT.
Purpose: cross-modal identity bindings, required/optional coherence obligations and evaluator-owner routing.
Boundary: not M02 Production Graph, M04 Scene Graph or M43 Canon Graph.

### F-M05-16 — Drift Evidence & Continuity Analysis Fabric
Sources: DNAX-095, 096, 097, 098, 099, 100, 111, 112, 114, 116, 117, 118.
Status: ACCEPT.
Purpose: typed multi-dimensional drift evidence, continuity envelope, deterministic reports, contextual-variation resolution and provider-drift normalization.
Rule: no single similarity score decides identity.

### F-M05-17 — Mutation Admission & Same-Identity Revision Fabric
Sources: DNAX-101, 102, 103, 104, 105, 119.
Status: ACCEPT.
Purpose: repair/mutation firewall, explicit mutation proposal/authority/decision and immutable same-identity revision admission.

### F-M05-18 — Identity Break & Split Fabric
Sources: DNAX-106, 107, 108.
Status: ACCEPT.
Purpose: new-ID identity break with lineage and governed one-to-many split semantics.

### F-M05-19 — Protected Identity Evidence & Authority Bridge
Sources: DNAX-024, 025, 070, 113, 115, 138, 139, 145, 147.
Status: ACCEPT_WITH_CONSOLIDATION.
Purpose: privacy-minimized identity/evidence refs, voice-sensitive data minimization, M39 root-identity firewall and M53/M54 rights/security authority bridges.
Notes:
- DNAX-025 is the early rights/consent hook and is subsumed by the final authority-bridge design.
- DNAX-145 prevents package/schema conformance from becoming legal/safety truth.

### F-M05-20 — Semantic Identity Lineage & Versioning Firewall
Sources: DNAX-121, 122, 123.
Status: ACCEPT_WITH_OWNERSHIP_SHIELD.
Purpose: semantic identity lineage distinct from project and production versioning.
Boundaries: M02 owns branches/snapshots/rollback; M06 owns production-state/content-addressed revision/build semantics.

### F-M05-21 — Directional Compatibility & Migration Fabric
Sources: DNAX-059, 124, 125, 126, 127, 128, 129, 130, 149.
Status: ACCEPT_WITH_SUPERSESSION.
Purpose: directional multi-axis compatibility, explicit loss/indeterminate states, semantic migration and deterministic migration receipts.
Note: DNAX-059 early variant-compatibility concept is superseded by the generalized compatibility family but retained as design history.

### F-M05-22 — Reusable DNA Package & Dependency Fabric
Sources: DNAX-029, 131, 132, 133, 134, 135, 136.
Status: ACCEPT_WITH_SUPERSESSION.
Purpose: portable package manifest, package/subject identity firewall, portability levels and typed dependency closure.
Note: DNAX-029 early package-boundary seed is superseded by this complete family.

### F-M05-23 — Marketplace / Storage / Delivery Boundary Fabric
Sources: DNAX-137, 140, 141, 146.
Status: ACCEPT_WITH_BOUNDARY.
Purpose: marketplace-facing exchange contract plus storage/delivery ownership shields and non-executable package posture.
Boundaries: no payment/storefront/ranking ownership; M55 owns storage/CAS; M59 owns concrete export/publishing.

### F-M05-24 — Import / Conformance / Package Lifecycle Fabric
Sources: DNAX-142, 143, 144, 148.
Status: ACCEPT.
Purpose: staged import admission, collision-safe import, deterministic package conformance and active/deprecated/restricted/retired lifecycle.

### F-M05-25 — Identity Risk & Threat Radar Fabric
Sources: DNAX-060, 090, 120, 150.
Status: ACCEPT_WITH_CONSOLIDATION.
Purpose: one consolidated risk/finding vocabulary spanning family identity, cross-modal links, identity transitions and portable packages.
Note: the four stage-specific threat radars are not separate engines.

## Mapping integrity

The consolidated mapping covers:
- DNAX-001..150 exactly once;
- 150 mapped candidates;
- 0 missing candidates;
- 0 duplicate family assignments.

This exact-once property is mandatory for the freeze candidate.

## Candidate-level disposition summary

- DNAX-001..024: ACCEPT through F-M05-01..06, with authority/anchor refinements consolidated into later sources.
- DNAX-025: SUPERSEDED_IN_DETAIL_BY_F-M05-19, retained as design history.
- DNAX-026..028: ACCEPT through F-M05-05.
- DNAX-029: SUPERSEDED_BY_F-M05-22, retained as design history.
- DNAX-030..058: ACCEPT through F-M05-07..11.
- DNAX-059: SUPERSEDED_BY_GENERAL_F-M05-21_COMPATIBILITY, retained as design history.
- DNAX-060: CONSOLIDATED_INTO_F-M05-25.
- DNAX-061..089: ACCEPT through F-M05-12..15/F-M05-19.
- DNAX-090: CONSOLIDATED_INTO_F-M05-25.
- DNAX-091..119: ACCEPT through F-M05-03..05/F-M05-16..19.
- DNAX-120: CONSOLIDATED_INTO_F-M05-25.
- DNAX-121..149: ACCEPT through F-M05-20..24/F-M05-19/F-M05-21.
- DNAX-150: CONSOLIDATED_INTO_F-M05-25.
- No candidate is independently labelled novel or patentable.
- No candidate requires one-to-one implementation as a class/service.

## Mandatory architecture shields

1. M01 remains sole quality/evaluator/promotion authority.
2. M02 remains project/Production Graph/branch/snapshot/rollback/release authority.
3. M03 remains creative intent/constraint/override authority.
4. M04 remains provider-neutral representation authority.
5. M05 is the generic persistent semantic Asset/Persona identity authority.
6. M06 remains production-state/content-addressed revision/build/reconstruction authority.
7. M16 solely owns concrete provider/workflow compilation.
8. M30 owns MotionDNA and motion production.
9. M37 owns temporal/shot continuity QA.
10. M39 owns digital-human/persona production continuity but binds to the M05 generic identity root.
11. M40 owns VoiceDNA and voice production.
12. M41 owns ArtistDNA/MusicDNA and music production.
13. M43 owns narrative Canon.
14. M45 owns Campaign DNA / Creative Genome and advertising.
15. M46 owns BrandDNA / Brand & IP.
16. M52 owns HIVE multimodal memory/retrieval integration.
17. M53 owns provenance/rights/license/consent/C2PA authority.
18. M54 owns security/restricted-content/permission/sandbox authority.
19. M55 owns storage/CAS/cache/archive.
20. M58 owns API/SDK/MCP/plugin lifecycle/conformance surfaces.
21. M59 owns concrete export/publishing/delivery compilation.
22. M60 owns system deployment/recovery/final integration acceptance.
23. Similarity/confidence cannot grant canonical identity authority.
24. Provider/hardware scarcity cannot weaken protected identity semantics.
25. Canonical DNA packages are non-executable by default.

## Review findings

### M05-PLAN-R01 — M45/M46 brand ownership mismatch
Classification: CHAT_FIXABLE / CLOSED.
Finding: early S01-S02 text treated M45 as Brand authority.
Correction: M45 is Advertising & Synthetic UGC Studio; M46 is Brand & IP Studio / BrandDNA authority. Canonical M05 planning was corrected before S03.

### M05-PLAN-R02 — M39 identity-root overlap
Classification: CHAT_FIXABLE / CLOSED_FOR_FORWARD_SCAN.
Finding: M39 Master Module Index contains "Persistent Identity Engine and canonical persona", which could become a competing generic identity root.
Correction: M05 remains generic persistent semantic identity authority. M39 owns digital-human/persona production continuity and must bind its persona/domain profile to M05.
Forward-scan requirement: revalidate M39 S01-S05 wording.

### M05-PLAN-R03 — M02/M06 branching/versioning overlap
Classification: CHAT_FIXABLE / CLOSED_FOR_FORWARD_SCAN.
Finding: M05 S05 "DNA branching" could be mistaken for project/VCS or production versioning.
Correction: M05 owns semantic identity lineage only. M02 owns project branches/snapshots/rollback; M06 owns production-state/content-addressed version/build semantics.

### M05-PLAN-R04 — Early package/rights/compatibility seeds overlap final S05 forms
Classification: CHAT_FIXABLE / CLOSED.
Finding: DNAX-025, 029 and 059 are narrower predecessors of later complete families.
Correction: retain as design history but mark them superseded-in-detail by F-M05-19, F-M05-22 and F-M05-21 respectively.

### M05-PLAN-R05 — Stage-specific threat radars duplicate one conceptual engine
Classification: CHAT_FIXABLE / CLOSED.
Finding: DNAX-060, 090, 120 and 150 describe the same cross-cutting risk/finding role at different planning stages.
Correction: consolidate into F-M05-25 Identity Risk & Threat Radar Fabric.

## Final review verdict

`APPROVED_FOR_FORWARD_COMPATIBILITY`

S01-S05 and consolidated families F-M05-01..25 are coherent enough to perform the M06-M60 Forward Compatibility Scan.

No M05 implementation is authorized.

No M05 contract is frozen yet.
