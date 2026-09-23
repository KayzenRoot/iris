# IRIS Scope

Status: `M05_FORWARD_COMPAT_PASS`

## Current governed increment — M05 planning

M05 Asset DNA 2.0 & Cross-Modal Identity has completed S01-S05 functional planning. It is not implemented or contract-frozen yet.

### S01
Persistent identity substrate, immutable revisions, typed traits, applicability states, canonical/evidence partition, anchors and projection contracts.

### S02
Character/Creature/Object/Product/Environment profiles, semantic identity levels, persistent components, variants and persistent/contextual appearance separation.

### S03
Revision-pinned Scene/Motion/Voice/Brand cross-modal links, SceneIdentityDNA, bindings/obligations and domain-ownership firewalls.

### S04
Anchor authority/lifecycle, typed multi-dimensional drift evidence, repair-vs-mutation firewall, mutation decisions, identity break/split/consolidation and privacy-minimized evidence.

### S05
- semantic DNA lineage separate from M02 branches;
- M02 semantic build/version lifecycle plus M06 operational persistence/reconstruction firewall;
- directional multi-axis `DNACompatibilityProfile`;
- explicit `DNAMigrationPlan` with preservation/loss/defaults;
- `ReusableDNAPackageManifest`;
- portable package levels;
- `DNAMarketplaceContract` as exchange/conformance metadata only;
- M53 rights/provenance authority;
- M54 security/restricted-content authority;
- M55 storage/CAS authority;
- M58 API/SDK/MCP/conformance surface boundary;
- M59 concrete export/publishing/delivery authority;
- typed dependency closure;
- staged import admission;
- deterministic `DNAPackageConformanceReport`;
- non-executable/fail-closed supply-chain default.

### Final Technology Review
- verdict: **APPROVED_FOR_FORWARD_COMPATIBILITY**;
- design-history candidates: **IRIS-DNAX-001..150**;
- consolidated freeze-candidate families: **F-M05-01..25**;
- mapping: **150/150 exactly once, 0 missing, 0 duplicates**;
- implementation code: **0**.

### Forward Compatibility Scan
- modules scanned: **M06-M60 (55)**;
- verdict: **PASS_WITH_EXTENSION_PORTS**;
- critical ownership conflicts remaining: **0**;
- corrected conflicts: **M02/M06 authority wording**, **M39 competing identity-root wording**;
- required extension/ref families: **22**.

### Next governed step
Prepare `m05-contract-v1.0`, then run the independent planning audit.

### NOT ADMITTED
- M05 implementation package;
- project/VCS branching inside M05;
- production build/version authority;
- marketplace payments/storefront/ranking;
- rights/license/consent decision authority;
- security scanning/restricted-content enforcement runtime;
- storage/CAS runtime;
- publishing/export runtime;
- executable package payloads by default.

## IRIS 1.0 product scope

IRIS 1.0 continues to include M00-M60. Completion of M05 functional planning does not silently admit implementation or later modules.
