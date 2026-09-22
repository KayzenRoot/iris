# M04 S02 Research Baseline — Camera, Lighting, Material and Spatial IR

Status: `RESEARCH_COMPLETE_FOR_S02`
Date: 2026-09-22
Module: `M04 — Multimodal IR / Scene IR`
Issue: `#26`

## Purpose

Identify stable cross-application concepts for physical camera, light, material, color and spatial representation without freezing one renderer/DCC vocabulary into canonical M04 IR.

## External references reviewed

### OpenUSD camera and spatial semantics

OpenUSD camera schemas model physical camera concepts and tie lens/filmback measures to scene-unit metadata. The useful IRIS lesson is that camera parameters and scene scale cannot be interpreted independently.

OpenUSD also exposes named/scoped coordinate systems and explicit spatial relationships. IRIS adopts explicit coordinate-frame bindings and scope, not USD path/namespace mechanics.

### OpenUSD lighting

UsdLux provides portable light schemas and LightAPI concepts such as:
- intensity;
- exposure;
- color;
- color temperature;
- diffuse/specular contribution;
- shaped/boundable and distant light families;
- light filters, shadow and light-linking concepts.

Useful lesson: light semantics should express physical or at least explicitly defined quantities, while non-physical artistic multipliers remain visibly non-physical.

### MaterialX 1.39

MaterialX is an open standard for platform-independent material/look-development networks. The current specification family is 1.39; current library documentation observed during research is in the 1.39.x line.

Useful lessons:
- typed node graph;
- standard shading/process nodes;
- explicit extensibility;
- application/renderer interchange;
- OpenPBR support;
- document versioning/upgrades.

IRIS does not freeze MaterialX itself as canonical material IR. M04 keeps an IRIS-owned graph with a future MaterialX adapter/qualification route.

### OpenColorIO

OpenColorIO is an open color-management framework focused on motion-picture/VFX/animation pipelines. Current public site highlights the OCIO 2.5 line.

IRIS adopts the rule that color values, texture encodings and display/render transforms require explicit color-management identity. M04 must never treat naked RGB triplets as universally meaningful.

## Research conclusions

1. scene units/coordinate frames are correctness data;
2. authored transform semantics and derived world matrices are different facts;
3. camera physical properties require declared units and projection/lens semantics;
4. light intensity must name its quantity/unit/interpretation, not be an untyped scalar;
5. artistic light modifiers must be marked non-physical where applicable;
6. material semantics require a typed graph and explicit geometry bindings;
7. color values require a color-space/encoding contract;
8. preview material/light/camera approximations cannot silently substitute for final-quality obligations;
9. named coordinate spaces should be scoped and explicitly bound;
10. M04 should be exportable to USD/MaterialX/OCIO ecosystems without making those libraries canonical runtime dependencies.

## S02 research gate

`PASS`

Proceed with IRIS-owned physical/spatial semantics and adapter-friendly ports.
