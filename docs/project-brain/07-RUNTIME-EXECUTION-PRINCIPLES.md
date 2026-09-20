# IRIS 1.0 — Runtime Execution Principles

Status: `ACTIVE_DISCOVERY`

## Background-first

Normal batch generation, Blender processing and render jobs should not require visible application windows.

### Blender
Primary path: supervised `blender --background` workers with bounded Python/`bpy` tasks.
MCP: control/inspection plane and optional live-session tool surface.
UI mode: used only when a task benefits from direct interactive inspection.

### ComfyUI
Primary path: supervised local server/runtime accessed through API/queue/events.
Do not create a new shell/runtime per image when a healthy qualified worker can serve jobs.

## Process discipline

IRIS must own:
- worker PID/process-tree identity;
- concurrency;
- memory/VRAM leases;
- timeout;
- cancellation;
- graceful shutdown;
- hard-kill fallback;
- stale worker detection;
- orphan/zombie reaping;
- stdout/stderr capture with bounded retention;
- crash-loop backoff;
- health checks;
- restart policy.

## Workstation coexistence

The operator should be able to keep using the PC. Scheduler policies must reserve configurable RAM/VRAM/CPU headroom and may pause/preempt background work under interactive pressure.

## Safety

Untrusted blend files, Python scripts, custom nodes and downloaded model-side code are not automatically trusted. Execution policy and sandbox boundaries are specified in M18, M26 and M54.
