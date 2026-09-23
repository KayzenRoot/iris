"""Provider-neutral audio, music, narrative projection, timeline, and sync records."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, ClassVar, Mapping

from iris_intent.identity import SemanticRef

from .base import IRRecord, fraction, many, one, optional
from .common import deep_freeze, identifiers, non_negative_int, require_enum
from .enums import MusicEventKind, SyncKind
from .errors import IRAdmissionError, IRIntegrityError, IRSchemaError
from .identity import ExternalIdentityRef, IRNodeRef, ResourceRef
from .spatial import CoordinateFrameIR
from .temporal import DurationIR, TimePointIR, TimeRangeIR, _fraction
from .versions import require_identifier, require_text

__all__ = [
    "VoiceIdentityRef", "PersonaRef", "SpeakerRef", "AudioSpatialIR", "AudioIR", "AudioClipBindingIR",
    "MusicTempoIR", "MusicMeterIR", "MusicEventIR", "MusicSectionIR", "MusicIR", "NarrativeCueIR",
    "NarrativeProjectionIR", "TimelineItemIR", "TimelineTrackIR", "ShotRepresentationIR", "SequenceRepresentationIR",
    "TimelineIR", "SyncRelationIR", "SyncEvaluation",
]


@dataclass(frozen=True)
class VoiceIdentityRef(IRRecord):
    reference: ExternalIdentityRef

    NESTED: ClassVar = {"reference": one(ExternalIdentityRef)}

    def __post_init__(self) -> None:
        reference = ExternalIdentityRef.coerce(self.reference, "reference")
        if reference.authority != "m40.voice_identity":
            raise IRSchemaError("VoiceIdentityRef must remain an opaque M40 reference")
        object.__setattr__(self, "reference", reference)


@dataclass(frozen=True)
class PersonaRef(IRRecord):
    reference: ExternalIdentityRef

    NESTED: ClassVar = {"reference": one(ExternalIdentityRef)}

    def __post_init__(self) -> None:
        reference = ExternalIdentityRef.coerce(self.reference, "reference")
        if reference.authority != "m05.persona_dna":
            raise IRSchemaError("PersonaRef must remain an opaque M05 reference")
        object.__setattr__(self, "reference", reference)


@dataclass(frozen=True)
class SpeakerRef(IRRecord):
    reference: ExternalIdentityRef

    NESTED: ClassVar = {"reference": one(ExternalIdentityRef)}

    def __post_init__(self) -> None:
        reference = ExternalIdentityRef.coerce(self.reference, "reference")
        if reference.authority != "m39.speaker":
            raise IRSchemaError("SpeakerRef must remain an opaque M39 reference")
        object.__setattr__(self, "reference", reference)


@dataclass(frozen=True)
class AudioSpatialIR(IRRecord):
    representation: str
    coordinate_frame: CoordinateFrameIR | None
    channel_layout: tuple[str, ...]
    object_audio: bool = False

    NESTED: ClassVar = {"coordinate_frame": optional(CoordinateFrameIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "representation", require_identifier(self.representation, "representation"))
        if self.coordinate_frame is not None:
            object.__setattr__(self, "coordinate_frame", CoordinateFrameIR.coerce(self.coordinate_frame, "coordinate_frame"))
        channels = identifiers(self.channel_layout, "channel_layout")
        object.__setattr__(self, "channel_layout", channels)
        if not isinstance(self.object_audio, bool):
            raise IRSchemaError("object_audio must be bool")
        if self.representation in {"binaural", "ambisonic", "object"} and self.coordinate_frame is None:
            raise IRSchemaError("spatial audio representations require an explicit coordinate frame")
        if self.representation not in {"mono", "stereo", "surround", "binaural", "ambisonic", "object"}:
            raise IRSchemaError("unknown audio spatial representation")
        if self.object_audio and self.representation != "object":
            raise IRSchemaError("object_audio requires OBJECT representation")


@dataclass(frozen=True)
class AudioIR(IRRecord):
    audio_id: str
    role: str
    resource: ResourceRef
    media_format: str
    spatial: AudioSpatialIR
    voice_ref: VoiceIdentityRef | None = None
    persona_ref: PersonaRef | None = None
    speaker_ref: SpeakerRef | None = None
    trace_refs: tuple[SemanticRef, ...] = ()

    NESTED: ClassVar = {"resource": one(ResourceRef), "spatial": one(AudioSpatialIR), "voice_ref": optional(VoiceIdentityRef), "persona_ref": optional(PersonaRef), "speaker_ref": optional(SpeakerRef), "trace_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "audio_id", require_identifier(self.audio_id, "audio_id"))
        object.__setattr__(self, "role", require_identifier(self.role, "role"))
        object.__setattr__(self, "resource", ResourceRef.coerce(self.resource, "resource"))
        object.__setattr__(self, "media_format", require_text(self.media_format, "media_format", maximum=128))
        object.__setattr__(self, "spatial", AudioSpatialIR.coerce(self.spatial, "spatial"))
        for name, kind in (("voice_ref", VoiceIdentityRef), ("persona_ref", PersonaRef), ("speaker_ref", SpeakerRef)):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, kind.coerce(value, name))
        refs = tuple(SemanticRef.coerce(item, "trace_refs[]") for item in self.trace_refs)
        if not refs:
            raise IRAdmissionError("AudioIR requires admitted semantic trace refs")
        object.__setattr__(self, "trace_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))


@dataclass(frozen=True)
class AudioClipBindingIR(IRRecord):
    binding_id: str
    audio_id: str
    range: TimeRangeIR
    start_offset: Fraction = Fraction(0)
    gain: float = 1.0
    speaker_ref: SpeakerRef | None = None

    NESTED: ClassVar = {"range": one(TimeRangeIR), "start_offset": fraction, "speaker_ref": optional(SpeakerRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "binding_id", require_identifier(self.binding_id, "binding_id"))
        object.__setattr__(self, "audio_id", require_identifier(self.audio_id, "audio_id"))
        object.__setattr__(self, "range", TimeRangeIR.coerce(self.range, "range"))
        offset = _fraction(self.start_offset, "start_offset")
        if offset < 0:
            raise IRSchemaError("audio start_offset cannot be negative")
        object.__setattr__(self, "start_offset", offset)
        from .versions import require_finite_number
        gain = float(require_finite_number(self.gain, "gain"))
        if gain < 0:
            raise IRSchemaError("audio gain cannot be negative")
        object.__setattr__(self, "gain", gain)
        if self.speaker_ref is not None:
            object.__setattr__(self, "speaker_ref", SpeakerRef.coerce(self.speaker_ref, "speaker_ref"))


@dataclass(frozen=True, order=True)
class MusicTempoIR(IRRecord):
    time: TimePointIR
    beats_per_minute: Fraction

    NESTED: ClassVar = {"time": one(TimePointIR), "beats_per_minute": fraction}

    def __post_init__(self) -> None:
        object.__setattr__(self, "time", TimePointIR.coerce(self.time, "time"))
        bpm = _fraction(self.beats_per_minute, "beats_per_minute")
        if bpm <= 0 or bpm > 1000:
            raise IRSchemaError("tempo must be positive and <= 1000 BPM")
        object.__setattr__(self, "beats_per_minute", bpm)


@dataclass(frozen=True, order=True)
class MusicMeterIR(IRRecord):
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if isinstance(self.numerator, bool) or not isinstance(self.numerator, int) or self.numerator < 1 or self.numerator > 64:
            raise IRSchemaError("meter numerator must be in [1,64]")
        if isinstance(self.denominator, bool) or not isinstance(self.denominator, int) or self.denominator not in {1, 2, 4, 8, 16, 32, 64}:
            raise IRSchemaError("meter denominator must be a power-of-two musical denominator")


@dataclass(frozen=True)
class MusicEventIR(IRRecord):
    event_id: str
    event_kind: MusicEventKind
    start: TimePointIR
    duration: DurationIR
    part_id: str
    pitch: float | None = None
    dynamics: str | None = None
    properties: Mapping[str, Any] | None = None

    NESTED: ClassVar = {"start": one(TimePointIR), "duration": one(DurationIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", require_identifier(self.event_id, "event_id"))
        object.__setattr__(self, "event_kind", require_enum(self.event_kind, MusicEventKind, "event_kind"))
        object.__setattr__(self, "start", TimePointIR.coerce(self.start, "start"))
        object.__setattr__(self, "duration", DurationIR.coerce(self.duration, "duration"))
        if self.duration.reference_id != self.start.reference_id:
            raise IRIntegrityError("music event duration and start use different time references")
        object.__setattr__(self, "part_id", require_identifier(self.part_id, "part_id"))
        if self.pitch is not None:
            from .versions import require_finite_number
            object.__setattr__(self, "pitch", float(require_finite_number(self.pitch, "pitch")))
        if self.dynamics is not None:
            object.__setattr__(self, "dynamics", require_identifier(self.dynamics, "dynamics"))
        if self.properties is not None:
            object.__setattr__(self, "properties", deep_freeze(self.properties, "properties"))
        if self.event_kind is MusicEventKind.NOTE and self.pitch is None:
            raise IRSchemaError("NOTE events require a semantic pitch value")


@dataclass(frozen=True)
class MusicSectionIR(IRRecord):
    section_id: str
    label: str
    range: TimeRangeIR
    part_ids: tuple[str, ...] = ()

    NESTED: ClassVar = {"range": one(TimeRangeIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "section_id", require_identifier(self.section_id, "section_id"))
        object.__setattr__(self, "label", require_text(self.label, "label", maximum=256))
        object.__setattr__(self, "range", TimeRangeIR.coerce(self.range, "range"))
        object.__setattr__(self, "part_ids", identifiers(self.part_ids, "part_ids"))


@dataclass(frozen=True)
class MusicIR(IRRecord):
    music_id: str
    time_reference_id: str
    events: tuple[MusicEventIR, ...] = ()
    tempo_map: tuple[MusicTempoIR, ...] = ()
    meter: MusicMeterIR | None = None
    sections: tuple[MusicSectionIR, ...] = ()
    part_ids: tuple[str, ...] = ()
    tonal_center: str | None = None

    NESTED: ClassVar = {"events": many(MusicEventIR), "tempo_map": many(MusicTempoIR), "meter": optional(MusicMeterIR), "sections": many(MusicSectionIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "music_id", require_identifier(self.music_id, "music_id"))
        object.__setattr__(self, "time_reference_id", require_identifier(self.time_reference_id, "time_reference_id"))
        events = tuple(MusicEventIR.coerce(item, "events[]") for item in self.events)
        if len({item.event_id for item in events}) != len(events):
            raise IRSchemaError("music event ids must be unique")
        if any(item.start.reference_id != self.time_reference_id for item in events):
            raise IRIntegrityError("music event uses a different time reference")
        object.__setattr__(self, "events", tuple(sorted(events, key=lambda item: (item.start.ticks, item.event_id))))
        tempo = tuple(MusicTempoIR.coerce(item, "tempo_map[]") for item in self.tempo_map)
        if len({item.time.ticks for item in tempo}) != len(tempo) or any(item.time.reference_id != self.time_reference_id for item in tempo):
            raise IRIntegrityError("music tempo map has duplicate or wrong-reference times")
        object.__setattr__(self, "tempo_map", tuple(sorted(tempo, key=lambda item: item.time.ticks)))
        if self.meter is not None:
            object.__setattr__(self, "meter", MusicMeterIR.coerce(self.meter, "meter"))
        sections = tuple(MusicSectionIR.coerce(item, "sections[]") for item in self.sections)
        if any(item.range.start.reference_id != self.time_reference_id for item in sections):
            raise IRIntegrityError("music section uses a different time reference")
        object.__setattr__(self, "sections", tuple(sorted(sections, key=lambda item: (item.range.start.ticks, item.section_id))))
        object.__setattr__(self, "part_ids", identifiers(self.part_ids, "part_ids"))
        if self.tonal_center is not None:
            object.__setattr__(self, "tonal_center", require_text(self.tonal_center, "tonal_center", maximum=128))


@dataclass(frozen=True)
class NarrativeCueIR(IRRecord):
    cue_id: str
    range: TimeRangeIR
    cue_kind: str
    text: str
    canon_ref: ExternalIdentityRef | None = None
    local_projection_only: bool = True
    source_refs: tuple[SemanticRef, ...] = ()

    NESTED: ClassVar = {"range": one(TimeRangeIR), "canon_ref": optional(ExternalIdentityRef), "source_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "cue_id", require_identifier(self.cue_id, "cue_id"))
        object.__setattr__(self, "range", TimeRangeIR.coerce(self.range, "range"))
        object.__setattr__(self, "cue_kind", require_identifier(self.cue_kind, "cue_kind"))
        object.__setattr__(self, "text", require_text(self.text, "text", maximum=4096))
        if self.canon_ref is not None:
            ref = ExternalIdentityRef.coerce(self.canon_ref, "canon_ref")
            if ref.authority != "m43.canon":
                raise IRSchemaError("Canon refs are opaque M43 references")
            object.__setattr__(self, "canon_ref", ref)
        if self.local_projection_only is not True:
            raise IRAdmissionError("NarrativeCueIR is always a local projection and cannot write Canon")
        refs = tuple(SemanticRef.coerce(item, "source_refs[]") for item in self.source_refs)
        if not refs:
            raise IRAdmissionError("narrative cue requires admitted M03 source refs")
        object.__setattr__(self, "source_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))


@dataclass(frozen=True)
class NarrativeProjectionIR(IRRecord):
    projection_id: str
    cues: tuple[NarrativeCueIR, ...]
    canon_refs: tuple[ExternalIdentityRef, ...] = ()

    NESTED: ClassVar = {"cues": many(NarrativeCueIR), "canon_refs": many(ExternalIdentityRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "projection_id", require_identifier(self.projection_id, "projection_id"))
        cues = tuple(NarrativeCueIR.coerce(item, "cues[]") for item in self.cues)
        if len({item.cue_id for item in cues}) != len(cues):
            raise IRSchemaError("narrative cue ids must be unique")
        object.__setattr__(self, "cues", tuple(sorted(cues, key=lambda item: (item.range.start.ticks, item.cue_id))))
        refs = tuple(ExternalIdentityRef.coerce(item, "canon_refs[]") for item in self.canon_refs)
        if any(item.authority != "m43.canon" for item in refs):
            raise IRSchemaError("narrative projection Canon refs must remain in M43 namespace")
        object.__setattr__(self, "canon_refs", tuple(sorted({(item.ref_id, item.version): item for item in refs}.values(), key=lambda item: item.ref_id)))


@dataclass(frozen=True)
class TimelineItemIR(IRRecord):
    item_id: str
    item_kind: str
    target_ref: IRNodeRef
    range: TimeRangeIR
    order: int

    NESTED: ClassVar = {"target_ref": one(IRNodeRef), "range": one(TimeRangeIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "item_id", require_identifier(self.item_id, "item_id"))
        object.__setattr__(self, "item_kind", require_identifier(self.item_kind, "item_kind"))
        object.__setattr__(self, "target_ref", IRNodeRef.coerce(self.target_ref, "target_ref"))
        object.__setattr__(self, "range", TimeRangeIR.coerce(self.range, "range"))
        non_negative_int(self.order, "order")


@dataclass(frozen=True)
class TimelineTrackIR(IRRecord):
    track_id: str
    track_kind: str
    items: tuple[TimelineItemIR, ...]
    order: int

    NESTED: ClassVar = {"items": many(TimelineItemIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "track_id", require_identifier(self.track_id, "track_id"))
        object.__setattr__(self, "track_kind", require_identifier(self.track_kind, "track_kind"))
        non_negative_int(self.order, "order")
        items = tuple(TimelineItemIR.coerce(item, "items[]") for item in self.items)
        if len({item.item_id for item in items}) != len(items) or len({item.order for item in items}) != len(items):
            raise IRSchemaError("timeline track item ids and explicit order values must be unique")
        object.__setattr__(self, "items", tuple(sorted(items, key=lambda item: (item.order, item.item_id))))


@dataclass(frozen=True)
class ShotRepresentationIR(IRRecord):
    shot_id: str
    range: TimeRangeIR
    scene_ref: IRNodeRef
    camera_ref: IRNodeRef | None = None
    continuity_refs: tuple[SemanticRef, ...] = ()

    NESTED: ClassVar = {"range": one(TimeRangeIR), "scene_ref": one(IRNodeRef), "camera_ref": optional(IRNodeRef), "continuity_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "shot_id", require_identifier(self.shot_id, "shot_id"))
        object.__setattr__(self, "range", TimeRangeIR.coerce(self.range, "range"))
        object.__setattr__(self, "scene_ref", IRNodeRef.coerce(self.scene_ref, "scene_ref"))
        if self.camera_ref is not None:
            object.__setattr__(self, "camera_ref", IRNodeRef.coerce(self.camera_ref, "camera_ref"))
        refs = tuple(SemanticRef.coerce(item, "continuity_refs[]") for item in self.continuity_refs)
        object.__setattr__(self, "continuity_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))


@dataclass(frozen=True)
class SequenceRepresentationIR(IRRecord):
    sequence_id: str
    shots: tuple[ShotRepresentationIR, ...]
    time_reference_id: str

    NESTED: ClassVar = {"shots": many(ShotRepresentationIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "sequence_id", require_identifier(self.sequence_id, "sequence_id"))
        object.__setattr__(self, "time_reference_id", require_identifier(self.time_reference_id, "time_reference_id"))
        shots = tuple(ShotRepresentationIR.coerce(item, "shots[]") for item in self.shots)
        if not shots or len({item.shot_id for item in shots}) != len(shots):
            raise IRSchemaError("sequence requires uniquely identified shots")
        if any(item.range.start.reference_id != self.time_reference_id for item in shots):
            raise IRIntegrityError("sequence shot time reference differs")
        ordered = tuple(sorted(shots, key=lambda item: (item.range.start.ticks, item.shot_id)))
        for left, right in zip(ordered, ordered[1:]):
            if right.range.start.ticks < left.range.end.ticks:
                raise IRIntegrityError("sequence shots overlap; express overlap as an explicit transition/relationship")
        object.__setattr__(self, "shots", ordered)


@dataclass(frozen=True)
class TimelineIR(IRRecord):
    timeline_id: str
    time_reference_id: str
    tracks: tuple[TimelineTrackIR, ...]
    range: TimeRangeIR
    shot_sequences: tuple[SequenceRepresentationIR, ...] = ()
    narrative_projection: NarrativeProjectionIR | None = None

    NESTED: ClassVar = {"tracks": many(TimelineTrackIR), "range": one(TimeRangeIR), "shot_sequences": many(SequenceRepresentationIR), "narrative_projection": optional(NarrativeProjectionIR)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "timeline_id", require_identifier(self.timeline_id, "timeline_id"))
        object.__setattr__(self, "time_reference_id", require_identifier(self.time_reference_id, "time_reference_id"))
        object.__setattr__(self, "range", TimeRangeIR.coerce(self.range, "range"))
        if self.range.start.reference_id != self.time_reference_id:
            raise IRIntegrityError("timeline range time reference differs")
        tracks = tuple(TimelineTrackIR.coerce(item, "tracks[]") for item in self.tracks)
        if len({item.track_id for item in tracks}) != len(tracks) or len({item.order for item in tracks}) != len(tracks):
            raise IRSchemaError("timeline track ids and explicit order must be unique")
        for track in tracks:
            for item in track.items:
                if item.range.start.reference_id != self.time_reference_id or item.range.start.ticks < self.range.start.ticks or item.range.end.ticks > self.range.end.ticks:
                    raise IRIntegrityError("timeline item falls outside timeline basis/range")
        object.__setattr__(self, "tracks", tuple(sorted(tracks, key=lambda item: (item.order, item.track_id))))
        sequences = tuple(SequenceRepresentationIR.coerce(item, "shot_sequences[]") for item in self.shot_sequences)
        if any(item.time_reference_id != self.time_reference_id for item in sequences):
            raise IRIntegrityError("timeline sequence uses a different time reference")
        object.__setattr__(self, "shot_sequences", tuple(sorted(sequences, key=lambda item: item.sequence_id)))
        if self.narrative_projection is not None:
            object.__setattr__(self, "narrative_projection", NarrativeProjectionIR.coerce(self.narrative_projection, "narrative_projection"))
            for cue in self.narrative_projection.cues:
                if cue.range.start.reference_id != self.time_reference_id or cue.range.start.ticks < self.range.start.ticks or cue.range.end.ticks > self.range.end.ticks:
                    raise IRIntegrityError("narrative cue falls outside timeline range")


@dataclass(frozen=True)
class SyncEvaluation(IRRecord):
    relation_id: str
    observed_offset: Fraction
    error: Fraction
    within_tolerance: bool


@dataclass(frozen=True)
class SyncRelationIR(IRRecord):
    relation_id: str
    kind: SyncKind
    source: TimePointIR
    target: TimePointIR
    expected_offset: Fraction
    tolerance: Fraction
    required: bool = True
    source_refs: tuple[SemanticRef, ...] = ()

    NESTED: ClassVar = {"source": one(TimePointIR), "target": one(TimePointIR), "expected_offset": fraction, "tolerance": fraction, "source_refs": many(SemanticRef)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "relation_id", require_identifier(self.relation_id, "relation_id"))
        object.__setattr__(self, "kind", require_enum(self.kind, SyncKind, "kind"))
        object.__setattr__(self, "source", TimePointIR.coerce(self.source, "source"))
        object.__setattr__(self, "target", TimePointIR.coerce(self.target, "target"))
        if self.source.reference_id != self.target.reference_id:
            raise IRIntegrityError("sync relation uses different time references without an explicit conversion")
        expected, tolerance = _fraction(self.expected_offset, "expected_offset"), _fraction(self.tolerance, "tolerance")
        if tolerance < 0:
            raise IRSchemaError("sync tolerance cannot be negative")
        object.__setattr__(self, "expected_offset", expected)
        object.__setattr__(self, "tolerance", tolerance)
        if not isinstance(self.required, bool):
            raise IRSchemaError("required must be bool")
        refs = tuple(SemanticRef.coerce(item, "source_refs[]") for item in self.source_refs)
        if self.required and not refs:
            raise IRAdmissionError("required sync relation needs admitted source refs")
        object.__setattr__(self, "source_refs", tuple(sorted({item.text: item for item in refs}.values(), key=lambda item: item.text)))

    def evaluate(self, observed_source: TimePointIR, observed_target: TimePointIR) -> SyncEvaluation:
        for point in (observed_source, observed_target):
            if point.reference_id != self.source.reference_id or point.layer is not self.source.layer:
                raise IRIntegrityError("observed sync time uses a different time reference/layer")
        observed = observed_target.ticks - observed_source.ticks
        error = abs(observed - self.expected_offset)
        within = error <= self.tolerance
        if self.required and not within:
            raise IRIntegrityError(f"required sync relation {self.relation_id} exceeds declared tolerance")
        return SyncEvaluation(self.relation_id, observed, error, within)
