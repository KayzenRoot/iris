# M05 S02 Research — Domain DNA Families

Date: 2026-09-23
Module: M05 — Asset DNA 2.0 & Cross-Modal Identity
Session: S02
Status: `COMPLETE_FOR_MODULE_PLANNING`
Issue: #37
Authorized baseline: `6f2311b59f5da91778d3fc9d9fe1572953a0c60b`

## Research question

How should IRIS specialize the domain-neutral S01 DNA substrate for characters, creatures, objects, products and environments without creating five incompatible identity systems?

## Key conclusion

M05 should use one common DNA envelope and trait law, then compose typed subject-family profiles.

The family profile supplies:
- typed trait namespaces;
- subject-role semantics;
- default criticality/mutability guidance;
- allowed component/variant structure;
- compatibility rules;
- projection requirements.

It does not create a second identity system.

## Core distinction — class, archetype, individual and variant

S02 freezes four separate semantic levels:

1. `CLASS` — broad semantic category, such as humanoid, quadruped, chair, beverage can, interior environment.
2. `ARCHETYPE` — reusable design/species/model pattern shared by multiple identities.
3. `INDIVIDUAL` — one persistent subject identity.
4. `VARIANT` — an explicitly related identity/configuration whose relation to the parent/archetype is governed.

These levels must not be inferred from visual similarity.

Examples:
- two characters may share one humanoid archetype while remaining distinct individuals;
- a creature species template is not the same thing as one named creature;
- a product model may have multiple SKUs/colorways;
- an environment kit/template is not one instantiated location.

## Shared family architecture

All S02 families use:
- S01 `AssetDNAIdentity`;
- immutable `DNARevision`;
- typed `DNATrait`;
- anchors;
- provenance/policy refs;
- applicability states;
- mutation/criticality law;
- minimum-sufficient DNA slices.

S02 adds `DNAFamilyProfile` and `DNAComponentIdentity`.

### DNAFamilyProfile

Declares:
- family ID/version;
- semantic level support;
- required/optional trait namespaces;
- allowed component roles;
- default criticality/mutability recommendations;
- cross-family compatibility rules;
- extension namespaces;
- projection obligations.

Defaults are guidance, not silent authority. Canonical trait records remain explicit.

### DNAComponentIdentity

Stable identity for a persistent component whose continuity matters within a subject.

Examples:
- character face/body region;
- creature horn/wing/tail;
- product cap/label/package panel;
- object articulated door/blade/module;
- environment landmark/zone/architectural feature.

A component ID is scoped by subject DNA and cannot silently become an independent top-level asset identity.

## Character DNA

Character DNA covers persistent identity-bearing traits of a character as an asset/subject, not digital-human runtime behavior.

Candidate namespaces:
- `character.identity.*`;
- `character.anatomy.*`;
- `character.face.*`;
- `character.body.*`;
- `character.hair.*`;
- `character.signature.*`;
- `character.costume_binding.*`;
- `character.relationship_role.*`.

### Identity-critical candidates
- defining facial structure landmarks/ratios when relevant;
- stable body morphology envelope when relevant;
- persistent scars/marks/signature features;
- species/archetype ref where identity policy requires it;
- stable component identities;
- canonical distinguishing feature constraints.

### Contextual candidates
- pose;
- expression;
- temporary hairstyle state if policy allows;
- makeup;
- lighting;
- camera;
- temporary clothing/props;
- damage/dirt/wetness state.

Character DNA does not own:
- acting/gesture runtime;
- rigging implementation;
- voice synthesis;
- narrative canon;
- provider/model prompt.

Those remain M29/M30/M39/M40/M43 or other owning modules.

## Creature DNA

Creature DNA must support humanoid and non-humanoid forms without forcing human facial/body assumptions.

Candidate namespaces:
- `creature.taxonomy.*`;
- `creature.morphology.*`;
- `creature.anatomy.*`;
- `creature.appendage.*`;
- `creature.surface.*`;
- `creature.pattern.*`;
- `creature.signature.*`.

Key rule:
species/archetype identity and individual identity are separate.

A tiger-like pattern family, dragon species, monster archetype or procedural creature template is not sufficient to identify one persistent individual.

S02 supports bilateral/asymmetric and variable-count anatomy through typed component sets rather than fixed human slots.

## Object DNA

Object DNA describes persistent identity of ordinary props, tools, vehicles, devices and other non-product objects.

Candidate namespaces:
- `object.form.*`;
- `object.part.*`;
- `object.function.*`;
- `object.articulation.*`;
- `object.surface_identity.*`;
- `object.signature.*`.

Identity can depend on:
- silhouette/form family;
- persistent component topology;
- unique marks/damage;
- articulation/component layout;
- function-critical geometry;
- explicitly governed serial/external refs.

Transient state such as open/closed, dirt, pose, transform, battery level or scene placement is contextual unless policy says otherwise.

## Product DNA

Product DNA separates product/model identity, variant identity, packaging presentation and instance/serial identity.

Candidate levels:
- `PRODUCT_FAMILY`;
- `MODEL`;
- `VARIANT_SKU`;
- `PACKAGE_VARIANT`;
- `PHYSICAL_INSTANCE` when a use case explicitly requires serialized identity.

Candidate namespaces:
- `product.model.*`;
- `product.geometry.*`;
- `product.variant.*`;
- `product.packaging.*`;
- `product.marking.*`;
- `product.dimension.*`;
- `product.external_identifier.*`.

External product identifiers such as SKU/GTIN/MPN may be governed external refs. They are not universal substitutes for M05 identity.

Brand meaning/logo rules remain M45 authority; M05 may hold versioned BrandDNA links later in S03.

## Environment DNA

Environment DNA covers persistent place/set/location identity independent of one scene representation.

Candidate namespaces:
- `environment.layout.*`;
- `environment.zone.*`;
- `environment.landmark.*`;
- `environment.architecture.*`;
- `environment.signature.*`;
- `environment.ecology.*`;
- `environment.context_boundary.*`.

Identity-defining candidates:
- major topology/layout;
- stable landmark set;
- persistent zone relationships;
- defining architectural/ecological signature;
- protected spatial relationships.

Contextual state candidates:
- time of day;
- weather;
- season when not identity-defining;
- temporary props/crowds;
- lighting;
- camera;
- temporary damage;
- vegetation growth stage unless policy marks it persistent.

Environment DNA does not replace M04 SceneIR. M04 represents one current scene state; M05 states which environmental identity persists across scene states.

## Trait bundles and semantic facets

S02 introduces `DNATraitBundle`.

A bundle is a typed, versioned group of traits that:
- belongs to one subject DNA;
- has one family/profile ref;
- has explicit required/optional trait paths;
- cannot change trait criticality implicitly;
- carries bundle-level compatibility/provenance refs.

Bundles make family extensions composable without a giant monolithic record.

## Part/component identity

Persistent components require explicit identity only when their continuity matters.

Rules:
- component order/index is not identity;
- display name is not identity;
- M04 node identity may anchor a representation but does not automatically define component DNA identity;
- replacement parts require explicit replacement/substitution semantics;
- split/merge of components requires a governed mutation/lineage record;
- derived LOD fragments do not become new component identities.

## Appearance signature versus transient appearance

S02 separates:
- `PersistentAppearanceTrait` — canonical identity-relevant appearance;
- `ContextualAppearanceState` — allowed temporary/production state;
- `AppearanceObservation` — measured/generated evidence.

This prevents lighting, renderer, camera, pose or temporary costume from becoming identity DNA.

## Variant and archetype rules

A variant relation must declare:
- parent/archetype ref;
- variant role;
- inherited trait paths;
- overridden trait paths;
- compatibility expectation;
- identity relationship.

Inheritance never means mutable shared storage. Each admitted DNA revision remains immutable.

## Family interoperability

Cross-family conversion is never assumed.

Examples:
- CharacterDNA -> CreatureDNA reclassification may require explicit migration/identity review.
- ProductDNA -> ObjectDNA projection may be valid for generic scene use while product identity remains intact.
- EnvironmentDNA -> SceneIR is a projection, not a conversion of DNA into representation ownership.

## Threat model additions

S02 must defend against:
- human-centric schemas breaking creatures;
- class/archetype mistaken for individual identity;
- SKU/model/serial levels collapsed into one ID;
- temporary clothing/pose/light treated as character identity;
- product colorway silently mutating model identity;
- environment weather/time becoming persistent identity by accident;
- component reorder/index churn changing identity;
- auto-generated component IDs from geometry topology churn;
- renderer/material differences being mistaken for persistent appearance drift;
- family reclassification occurring implicitly.

## S02 outcome

S02 freezes domain family architecture, not the final M05 contract.

The next legal planning step is S03 SceneDNA, Motion DNA, Voice DNA and Brand DNA links.
