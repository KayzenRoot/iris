# Nerim — IRIS Visual Quality Reference Profile

Status: `PROPOSED_REFERENCE_PROFILE`
Purpose: define measurable visual properties for Nerim without copying another game's protected art identity.

## Reference direction

Nerim targets high-fidelity 3D viewed from a high-angle/isometric gameplay camera. Hordeguard is useful as a reference for distant/top-down readability and scene composition. Path of Exile 2 is useful as a quality bar for material richness, lighting, atmospheric depth, VFX integration and high-density ARPG presentation.

References are quality/property references, not style-cloning instructions.

## Target properties

### Camera/readability
- high-angle/isometric gameplay presentation;
- characters and enemies readable at actual gameplay distance;
- stable silhouette and class/equipment recognition;
- occlusion-aware environments;
- strong foreground/midground/background separation.

### Geometry
- high-quality source meshes;
- silhouette-first LODs;
- deformation-safe topology;
- detail density concentrated where it survives gameplay distance;
- collision and engine budgets validated separately from render beauty.

### Materials
- physically plausible PBR response;
- controlled roughness/metalness variation;
- macro/micro detail that survives mip/LOD transitions;
- readable material families at gameplay camera distance.

### Lighting
- grounded contact and form;
- atmospheric depth without crushing gameplay readability;
- emissive/VFX light contributes to scene without washing silhouettes;
- scalable quality tiers preserve art direction.

### VFX
- high impact with controlled screen occupancy;
- effects communicate gameplay state;
- particles do not erase enemy/player silhouettes;
- distance-aware detail and GPU budgets.

### Animation
- strong poses readable from gameplay camera;
- stable feet/contact;
- no joint collapse, clipping or visible retarget artifacts;
- locomotion/combat timing remains legible at actual game scale;
- secondary motion adds quality without visual noise.

### Texture/detail
- masters may be high resolution;
- runtime variants are generated from the master;
- no assumption that more texture resolution equals better perceived gameplay quality.

## Proposed Nerim-specific quality technology

### IRIS-QX-016 — Gameplay Distance Fidelity
Evaluates an asset at the camera distances/angles where the player will actually see it, not only in beauty close-ups. Uses multi-scale renders to measure silhouette, identity, equipment/material distinction, animation pose readability and VFX occlusion.

### IRIS-QX-017 — Isometric Readability Field
Builds a spatial/readability map from gameplay camera projections. Detects where characters, enemies, loot, interactables or important geometry merge into background values, materials or effects.

### IRIS-QX-018 — Detail Survival Analyzer
Measures which geometric/texture/material details survive target resolution, LOD, mipmapping and camera distance. Redirects production effort away from invisible detail toward visible quality.

### IRIS-QX-019 — VFX Occlusion Budget
Quantifies how much important gameplay silhouette/information is obscured by particles, bloom, smoke, decals and emissive effects over time.

### IRIS-QX-020 — Isometric Motion Legibility Score
Evaluates animation poses and transitions from the gameplay camera, including anticipation, attack direction, contact, foot sliding, pose silhouette and temporal readability.

## Acceptance principle

A Nerim asset is not MASTER because its Blender close-up is beautiful. It is MASTER only when both source/master quality and real gameplay-view quality satisfy their contracts.
