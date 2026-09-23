# M05 S03 Research — Cross-Modal DNA Links

Date: 2026-09-23
Module: M05 — Asset DNA 2.0 & Cross-Modal Identity
Session: S03
Status: `COMPLETE_FOR_MODULE_PLANNING`
Issue: #37
Authorized baseline: `6f2311b59f5da91778d3fc9d9fe1572953a0c60b`

## Research question

How should M05 preserve one subject's identity across scene, motion, voice and brand domains without duplicating the domain DNA/content owned by M30, M40, M46 or the representation/canon authorities owned by M04 and M43?

## Key conclusion

M05 needs a cross-modal identity-link fabric, not a warehouse of every domain's DNA.

M05 owns:
- which persistent subject identity is linked to which domain DNA;
- which exact domain-DNA revision is referenced;
- which traits/anchors the link binds;
- required/optional preservation obligations;
- compatibility state;
- provenance/policy refs;
- cross-modal consistency expectations.

M05 does not own:
- MotionDNA contents or motion generation;
- VoiceDNA contents, voice cloning/design or synthesis;
- BrandDNA contents or brand-system design;
- narrative Canon;
- concrete M04 scene state.

## Domain ownership freeze

### M30 — MotionDNA authority
M30 Animation & Motion Studio owns Motion DNA content, locomotion/combat/cinematic motion, transfer/retargeting, facial animation and motion QA.

M05 may hold a `MotionDNALink` that says which MotionDNA revision belongs to or is approved for a persistent identity.

### M40 — VoiceDNA authority
M40 Voice Studio & Dubbing owns Voice DNA content, authorized voice design/cloning, TTS, speech-to-speech, prosody, dubbing and voice QA.

M05 may hold a `VoiceDNALink`, but does not store raw voiceprints, voice model weights or synthesis parameters as canonical identity by default.

### M46 — BrandDNA authority
M46 Brand & IP Studio owns Brand DNA, visual/sonic/verbal identity, typography, palette, photography/style constraints, IP asset graph, Brand Lock and Brand Consistency Court.

M05 may bind an asset/persona/product/environment identity to a versioned `BrandDNALink`.

### M45 — Advertising authority
M45 Advertising & Synthetic UGC Studio owns Campaign DNA/Creative Genome, campaigns, hooks/CTA, campaign variants/evolution and autonomous advertising operation.

M05 may later link Campaign DNA through the generic domain-DNA link fabric, but Campaign DNA is not BrandDNA.

## SceneDNA boundary

S03 defines `SceneIdentityDNA` as a persistent reusable scene/set/location-composition identity layer.

It may describe:
- persistent scene/set identity;
- required member DNA refs;
- stable role slots;
- persistent landmark/asset relationships;
- permitted member substitutions;
- environment DNA ref;
- continuity-critical composition relations;
- M04 SceneIR projection refs;
- M43 Canon/story refs where relevant.

It does not own:
- current transforms/camera/light/material state;
- one M04 SceneIR snapshot;
- editorial timeline;
- narrative meaning/canon truth;
- shot continuity judgment.

M04 represents current provider-neutral scene state.
M37 judges temporal/shot continuity.
M43 owns narrative/canon semantics.

## LinkedDomainDNARef

S03 introduces a generic versioned link primitive.

Required concepts:
- owner module;
- domain DNA family;
- external DNA identity;
- external DNA revision/version;
- link role;
- required/optional status;
- bound M05 subject/trait/component paths;
- preservation obligations;
- compatibility expectation;
- policy/provenance/rights refs;
- validity scope;
- stale-state detection.

A link never imports external domain DNA into M05 canonical ownership.

## CrossModalIdentityBinding

A binding connects:
- one M05 DNA revision;
- one or more linked domain DNA revisions;
- M04 representation anchors;
- required identity traits;
- synchronization/equivalence expectations.

Examples:
- persistent corporate spokesperson CharacterDNA + M40 VoiceDNA + M30 MotionDNA + M46 BrandDNA;
- product DNA + BrandDNA;
- game creature DNA + MotionDNA;
- recurring virtual set SceneIdentityDNA + EnvironmentDNA + BrandDNA.

## Link freshness

A domain-DNA link is revision-pinned.

If the referenced MotionDNA/VoiceDNA/BrandDNA revision advances:
- the M05 link becomes `STALE_REVIEW_REQUIRED` unless compatibility policy proves the new revision is admissible;
- M05 cannot silently follow "latest";
- the old M05 revision remains immutable.

## Cross-modal consistency obligations

S03 introduces `CrossModalIdentityObligation`.

An obligation declares:
- subject DNA;
- participating modality/domain links;
- canonical trait/anchor paths that must remain coherent;
- exact/bounded/contextual expectation;
- evidence required;
- owner of evaluation;
- failure severity.

M05 records the obligation but does not seize M01 quality/evaluator authority.

## Voice privacy and biometric boundary

Voice identity needs extra care.

S03 freezes:
- a VoiceDNA link is not personal authentication;
- raw biometric templates are not required in generic M05 canonical DNA;
- similarity scores are observations only;
- consent/rights/privacy refs are mandatory where policy requires them;
- speaker verification runtime belongs outside M05;
- voice model/provider ID cannot become canonical persona identity.

## Motion identity boundary

Motion style can be identity-relevant without every animation clip becoming DNA.

M05 links to:
- MotionDNA identity/revision;
- approved motion-style family;
- signature movement refs;
- bound body/component traits;
- allowed contextual variation.

It does not canonicalize:
- individual animation curves;
- mocap files;
- retargeted clip payloads;
- provider/DCC rigs;
- current pose.

## Brand binding boundary

Brand association is a governed relation, not intrinsic identity by default.

A product/persona may:
- REQUIRE one BrandDNA link;
- ALLOW multiple brand roles;
- have no brand association;
- migrate brands only through explicit policy.

Brand link removal/change may or may not be identity-breaking depending on the subject's trait policy.

M46 decides BrandDNA contents and brand consistency.

## Scene member slots

SceneIdentityDNA may expose stable `IdentityRoleSlot` records:
- slot ID;
- semantic role;
- required family/profile;
- required trait constraints;
- cardinality;
- substitution policy;
- bound DNA ref(s).

Role slots preserve scene identity while allowing governed substitution.

Example:
a "flagship product pedestal" slot may accept a new ProductDNA variant without changing the reusable set's identity if its policy permits it.

## Domain DNA graph

S03 introduces a directed typed `CrossModalDNAGraph`.

Nodes:
- M05 subject identities/revisions;
- SceneIdentityDNA;
- external domain-DNA refs.

Edges:
- HAS_MOTION_IDENTITY;
- HAS_VOICE_IDENTITY;
- BOUND_TO_BRAND;
- MEMBER_OF_SCENE_IDENTITY;
- PERFORMS_ROLE;
- REPRESENTED_BY;
- DERIVED_COMPATIBILITY_REF.

The graph expresses identity linkage only. It is not M02 Production Graph, M04 scene graph or M43 Canon Graph.

## Generic future links

The link fabric must support later domain DNA without redesign:
- M41 ArtistDNA/MusicDNA;
- M45 CampaignDNA/Creative Genome;
- M46 IP/Brand packs;
- future localization/persona/content identity families.

Unknown mandatory link families fail closed.

## Threat model additions

S03 must defend against:
- copying domain DNA into M05 and creating competing authority;
- following "latest" external DNA revisions silently;
- treating voice similarity as persona identity;
- treating one motion clip as MotionDNA identity;
- treating campaign identity as BrandDNA;
- treating narrative scene ID as SceneIdentityDNA;
- treating M04 SceneIR snapshot as persistent SceneDNA;
- stale VoiceDNA/MotionDNA/BrandDNA links;
- cross-modal link cycles that imply ownership;
- optional link disappearance silently dropping mandatory identity obligations;
- one provider's voice/motion model ID becoming cross-modal identity.

## S03 outcome

S03 freezes cross-modal link architecture and authority firewalls.

The next legal planning step is S04 identity anchors, mutation boundaries and drift detection.
