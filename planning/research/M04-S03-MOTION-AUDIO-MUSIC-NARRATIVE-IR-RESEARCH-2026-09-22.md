# M04 S03 Research Baseline — Motion, Audio, Music and Narrative IR

Status: `RESEARCH_COMPLETE_FOR_S03`
Date: 2026-09-22
Module: `M04 — Multimodal IR / Scene IR`
Issue: `#26`

## Purpose

Identify portable temporal, motion, audio, music and narrative representation patterns while preserving the ownership of later Animation, Video/Cinema, Audio, Music and Narrative modules.

## External references reviewed

### OpenUSD time-varying values

OpenUSD 26.11 represents time-varying data through time coordinates and value sources such as TimeSamples, Splines and Value Clips. Time coordinates are deliberately distinct from an assumed frame rate, with explicit mapping to real time.

IRIS adopts:
- explicit time basis;
- sparse samples and curve/spline-style value evolution;
- clip/reference concepts for heavy temporal data;
- separation of authored time-varying intent from sampled/baked payload.

IRIS does not adopt USD TimeCode semantics as its universal timeline model.

### OpenTimelineIO

OpenTimelineIO represents editorial cut information with clips, tracks, transitions, markers, timing and metadata while referencing media externally rather than embedding video/audio.

IRIS adopts:
- explicit rational timing/ranges;
- timeline/container/clip-style composition as editorial prior art;
- external media references;
- adapters as interoperability boundaries.

M04 does not become an editor or replace M36/M38.

### MIDI 2.0

MIDI 2.0 extends, rather than replaces, MIDI 1.0 and its current core collection includes capability inquiry, profiles, property exchange, Universal MIDI Packet and MIDI Clip File specifications.

IRIS uses MIDI only as music/performance-event prior art. The canonical Music IR cannot require MIDI message/protocol semantics and must also represent score-like, semantic and non-MIDI music structures.

### ITU Audio Definition Model

ITU-R BS.2076-3 (2025) defines the Audio Definition Model. Current ITU guidance also covers channel-based, object-based, scene/transformation-based and binaural audio use cases.

IRIS adopts:
- explicit separation of audio programme/content/object/track/resource concerns;
- object/spatial-audio metadata as prior art;
- media bytes external to semantic metadata.

M04 does not own audio rendering, mixing, cleanup or mastering.

## Future-module ownership checked

- M29 owns rigging/skinning/anatomy/deformation strategies.
- M30 owns motion generation/retargeting/facial-animation production and motion QA.
- M36 owns video/cinema shot planning, production timeline and long-form assembly.
- M37 owns temporal identity/shot continuity.
- M38 owns editorial, compositing, color and encode.
- M40 owns voice generation/dubbing/prosody.
- M41 owns composition/arrangement/music DNA/mix-master.
- M42 owns sound generation/post/spatial-audio production and audio QA.
- M43 owns story/canon/world state/arcs/dialogue/branching narrative.

M04 therefore owns **representation contracts**, not these domain engines.

## Research conclusions

1. time base is explicit and independent from display frame labels;
2. authored curves/events/samples and baked payload are different representations;
3. timeline placement and media identity are separate;
4. M04 can represent motion channels without owning animation generation/retargeting;
5. audio metadata and audio bytes are separate;
6. M04 can represent music structure/events without owning composition;
7. M04 narrative data is a realization/projection binding, not Canon truth;
8. cross-modal synchronization requires common temporal anchors and typed sync relations;
9. large motion/audio/media payloads remain deferred resources;
10. every conversion/resampling/bake/edit projection must expose loss and provenance.

## S03 research gate

`PASS`

Proceed with an IRIS-owned temporal fabric shared by motion/audio/music/narrative projections while preserving later module authority.
