# M04 S01 Research Baseline — Scene, Character and Asset IR

Status: `RESEARCH_COMPLETE_FOR_S01`
Date: 2026-09-22
Module: `M04 — Multimodal IR / Scene IR`
Issue: `#26`
Authorized baseline: `c231dd61a210fe6d315126e755b4642a4fd2e9a3`

## Purpose

Identify proven patterns for a provider-neutral Scene/Character/Asset intermediate representation without importing a third-party format as IRIS canonical truth.

## Sources reviewed

### OpenUSD 26.11 documentation

OpenUSD describes a high-performance extensible system for authoring, composing and reading hierarchically organized scene description. Relevant patterns:
- hierarchical scene description;
- typed and applied API schemas;
- schema registry and schema-family/version reasoning;
- references/composition;
- deferred payloads for large assets;
- instancing/composition for large scenes;
- UsdSkel concepts for skeletons, skinning and blend shapes.

Useful pattern: a lightweight asset interface can remain loaded while heavy geometry/shading is deferred behind payloads.

Boundary for IRIS:
- OpenUSD is an interoperability/authoring ecosystem, not the M04 canonical model;
- M04 MUST remain able to lower to/from USD-compatible adapters later without making USD libraries or USD prim semantics mandatory;
- USD composition strength/opinion rules are prior art, not automatically adopted as IRIS governance.

### Khronos glTF

The current registry still identifies glTF 2.0 as the current specification, with 2.0.1 clarifications. glTF represents complete runtime scenes with nodes, meshes, cameras, skins, materials and animations.

Important boundary from the specification: glTF is optimized for runtime delivery and explicitly is not an authoring format. Therefore it is a useful export/interchange target and structural reference, but is too delivery-oriented to become the canonical authoring/semantic IR.

Khronos announced glTF 2.1 work in June 2026 focused on complex/multi-file scenes. This is emerging prior art and must not be treated as a frozen production dependency before the final specification is qualified.

### MLIR

MLIR demonstrates:
- multiple typed dialects coexisting in one IR;
- extensible/dynamic dialect registration;
- generic interfaces decoupling analyses from concrete operations;
- explicit dialect versioning and upgrade hooks;
- staged lowering between abstraction levels.

IRIS adopts the architectural lesson, not the compiler framework itself: M04 should have a small stable core plus versioned domain facets/dialects and explicit lowering receipts rather than an ever-growing universal record.

## Research conclusions

1. **Canonical IR must be IRIS-owned and provider-neutral.**
2. **Core + dialect/facet architecture beats a giant all-domain schema.**
3. **Containment/transform hierarchy and general semantic relationships are different graphs.**
4. **Asset interface and heavy payload must be separable for scale/context economy.**
5. **Scene composition must be explicit and deterministic, never implicit last-writer-wins.**
6. **Characters require semantic skeleton/skin/blend-shape representation, but DCC control rigs belong later.**
7. **M05 owns persistent Asset/Persona DNA policy; M04 only carries typed anchor references.**
8. **Large geometry/media bytes belong behind resource/content refs, not mandatory inline canonical records.**
9. **Every lowering from M03 must produce traceable coverage/gap evidence.**
10. **Provider capability may report loss/gaps but may not mutate canonical M04 truth.**
11. **Schema families and versions are first-class from the beginning.**
12. **M04 should be export-friendly to OpenUSD/glTF and later MaterialX/OTIO ecosystems without being reducible to any one of them.**

## Prior-art disposition

| Reference | Reuse | Do not copy |
| --- | --- | --- |
| OpenUSD | typed schemas, scene composition concepts, payload/interface split, instancing, skeletal prior art | USD opinion-strength semantics as IRIS governance; USD runtime dependency in core |
| glTF | portable scene/entity/mesh/skin structural vocabulary, clear delivery boundary | delivery-optimized schema as canonical authoring IR |
| MLIR | dialects, interfaces, explicit lowering/versioning | compiler-specific operation/region/block machinery unless later evidence requires it |

## S01 research gate

`PASS`

No external standard supplies the complete IRIS requirement. S01 may proceed with an IRIS-owned provider-neutral graph/facet model while preserving export/adaptation ports for those ecosystems.
