# IRIS Requirements

Status: `PRODUCT_DISCOVERY_ACTIVE`

## Bootstrap requirements
- BR-001 through BR-007 remain satisfied by IRIS-WO-0001.

## Product requirements admitted for IRIS 1.0 discovery
- PR-001: IRIS 1.0 SHALL be planned as a complete production version, not an MVP.
- PR-002: final masters SHALL satisfy an explicit Fidelity Contract and relevant Quality Court gates.
- PR-003: IRIS SHALL support 2D, 2.5D, 3D, image, video, animation, VFX, voice, music and audio production.
- PR-004: ComfyUI SHALL be the primary local image workflow fabric while models/providers remain replaceable.
- PR-005: Blender SHALL be the primary 3D/motion DCC with headless/background automation as the default batch path.
- PR-006: IRIS SHALL support a structured MCP/control surface without making a live GUI session mandatory.
- PR-007: 8 GB VRAM-class hardware SHALL be a first-class supported class with adaptive execution rather than fixed GPU presets.
- PR-008: the runtime SHALL manage worker lifecycle, concurrency, cancellation, cleanup and orphan/zombie detection.
- PR-009: the operator SHALL be able to keep using the workstation by reserving configurable CPU/RAM/VRAM headroom.
- PR-010: model/workflow decisions SHALL be based on empirical quality/hardware evidence and champion/challenger evaluation.
- PR-011: all 30 useful UGAS V2 capability categories SHALL have explicit IRIS 1.0 ownership.
- PR-012: HIVE SHALL supply derived context/retrieval/memory while Git/IRIS Project Brain remains canonical.
- PR-013: CORE↔IRIS runtime contracts SHALL be planned before integration implementation.
- PR-014: production dependencies/models/workflows SHALL use qualification, compatibility checks, provenance and rollback.
- PR-015: media repair SHOULD target the smallest affected region/frame/asset graph whenever quality can be preserved.
- PR-016: final V1 completion SHALL require functional + tested + documented + deployed + validated outcomes and measurable quality/performance gates.

Detailed module-level requirements are created and frozen during M00–M60 planning.
