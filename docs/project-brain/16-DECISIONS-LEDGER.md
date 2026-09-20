# IRIS Decisions Ledger

## ADR-0001 - Project identity
Status: `APPROVED`
Project name is **Hive IRIS**, IRIS = **Intelligent Rendering & Immersive Synthesis**.

## ADR-0002 - New-project treatment
Status: `APPROVED`
IRIS is a new V1. UGAS may later supply proven reusable components, but legacy decisions are not inherited automatically.

## ADR-0003 - GEF adoption
Status: `APPROVED`
Use GEF Bootstrap v1.0.0 pinned to `866fe3af8cccc65c929aaf6a47a924401fa448b3`; do not vendor GEF.

## ADR-0004 - HIVE integration
Status: `APPROVED`
Use HIVE v1.0.0 pinned to `a53b5b9fcf55c32a5696180fb1b1ef80ccd1edcf` as external local-first context/retrieval/MCP; Git remains canonical.

## ADR-0005 - Product gate
Status: `APPROVED`
No product implementation before canonical planning sources and bounded Work Order admit it.

## ADR-0006 - CORE relationship
Status: `TARGET`
IRIS will collaborate with CORE, but runtime contracts require dedicated planning.

## ADR-0007 - IRIS 1.0 is not an MVP
Status: `APPROVED`
IRIS 1.0 is the complete first production version. Planning may sequence implementation, but required V1 capabilities are not deferred merely to create an MVP label.

## ADR-0008 - Extreme quality is a product invariant
Status: `APPROVED`
Final masters prioritize validated visual/multimodal quality. Draft/preview lanes may optimize speed but cannot silently lower master acceptance criteria.

## ADR-0009 - ComfyUI is the primary image workflow fabric, not a permanent model lock
Status: `APPROVED`
IRIS uses ComfyUI as the primary local image workflow/runtime integration while models/providers remain replaceable and empirically routed.

## ADR-0010 - Blender headless-first
Status: `APPROVED`
Blender is the primary 3D/motion DCC. Normal automation uses supervised headless/background workers. MCP is a structured control/inspection surface and optional live-session path, not the only execution mechanism.

## ADR-0011 - 8 GB VRAM is a first-class hardware class
Status: `APPROVED`
IRIS must provide a truthful execution route for 8 GB VRAM-class systems through hardware-aware model selection, quantization, offload, tiling/chunking and scheduling. No fixed GPU presets.

## ADR-0012 - UGAS V2 vision is carried into IRIS 1.0
Status: `APPROVED`
All useful UGAS V2 categories and previously planned ideas are mapped into IRIS 1.0. Reuse is evidence-based and classified; legacy implementation is not inherited blindly.

## ADR-0013 - Qualified versions, canary upgrades and rollback
Status: `APPROVED`
Fast-moving dependencies such as ComfyUI, custom nodes, models and DCC adapters are pinned/qualified for production and upgraded through compatibility checks/canaries with rollback.

