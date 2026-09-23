"""Temporal, motion, audio, music, narrative, timeline, and sync acceptance tests."""

from __future__ import annotations

import unittest
from fractions import Fraction

from iris_multimodal_ir import (
    AudioClipBindingIR,
    AudioIR,
    AudioSpatialIR,
    CoordinateFrameIR,
    DurationIR,
    ExternalIdentityRef,
    IRIntegrityError,
    IRNodeRef,
    IRSchemaError,
    QuantityDimension,
    QuantityIR,
    MusicEventIR,
    MusicEventKind,
    MusicIR,
    MusicSectionIR,
    MusicTempoIR,
    NarrativeCueIR,
    NarrativeProjectionIR,
    PersonaRef,
    ResourceRef,
    SyncKind,
    SyncRelationIR,
    TemporalLayer,
    TemporalReferenceIR,
    TemporalSamplingIR,
    TimePointIR,
    TimeRangeIR,
    VoiceIdentityRef,
    SpeakerRef,
    AnimationCurveIR,
    CurveKeyIR,
    MotionChannelIR,
    MotionClipIR,
    MotionIR,
    MotionLayerIR,
    MotionTargetRef,
    convert_time_point,
    sample_curve,
)
from tests.m04_support import DOCUMENT_ID, SOURCE


def point(ticks: int | Fraction, layer: TemporalLayer = TemporalLayer.AUTHORED) -> TimePointIR:
    return TimePointIR("time.24fps", Fraction(ticks), layer)


class TimeAndMotionTests(unittest.TestCase):
    def test_time_basis_and_conversion_are_exact_rational(self):
        source = TemporalReferenceIR("time.source", Fraction(24), "epoch.production")
        target = TemporalReferenceIR("time.target", Fraction(24000, 1001), "epoch.production")
        start = TimePointIR(source.reference_id, Fraction(1), TemporalLayer.AUTHORED)
        converted, receipt = convert_time_point(start, source, target, "receipt.time")
        self.assertEqual(converted.ticks, Fraction(1000, 1001))
        self.assertEqual(receipt.source_reference, source)
        with self.assertRaises(IRIntegrityError):
            convert_time_point(start, source, TemporalReferenceIR("time.other", Fraction(30), "epoch.other"))

    def test_time_layers_are_explicit_and_ranges_are_bounded(self):
        authored = point(0, TemporalLayer.AUTHORED)
        sampled = point(1, TemporalLayer.SAMPLED)
        with self.assertRaises(IRIntegrityError):
            TimeRangeIR(authored, sampled)
        self.assertEqual(TimeRangeIR(authored, point(3)).duration_ticks, 3)

    def test_animation_curve_samples_exact_range_with_explicit_period(self):
        curve = AnimationCurveIR("curve.position", (
            CurveKeyIR(point(0), 0.0, "linear"), CurveKeyIR(point(10), 5.0, "linear"),
        ), "scalar")
        sampling = TemporalSamplingIR("sampling.position", TimeRangeIR(point(0), point(10)), Fraction(2), 6)
        samples = sample_curve(curve, sampling)
        self.assertEqual(len(samples), 6)
        self.assertEqual(samples[-1][1], 5.0)
        with self.assertRaises(IRSchemaError):
            TemporalSamplingIR("sampling.hidden", TimeRangeIR(point(0), point(10)), Fraction(0), 6)

    def test_motion_channel_uses_typed_semantic_target_and_value_type(self):
        target = MotionTargetRef(IRNodeRef(DOCUMENT_ID, "character.hero"), "transform.translation.x", "scalar")
        curve = AnimationCurveIR("curve.x", (CurveKeyIR(point(0), 0), CurveKeyIR(point(4), 1)), "scalar")
        channel = MotionChannelIR("channel.x", target, curve=curve, semantic_refs=(SOURCE,))
        self.assertEqual(channel.target.value_type, "scalar")
        with self.assertRaises(IRIntegrityError):
            MotionChannelIR("channel.bad", target, curve=AnimationCurveIR("curve.vector", (CurveKeyIR(point(0), 0),), "vector3"))
        with self.assertRaises(IRSchemaError):
            MotionChannelIR("channel.empty", target)

    def test_motion_clips_and_layers_keep_explicit_semantic_order(self):
        clip = MotionClipIR("clip.walk", TimeRangeIR(point(0), point(8)), "motion.walk")
        layer = MotionLayerIR("layer.body", 0, (clip,), "replace")
        motion = MotionIR("motion.walk", (MotionChannelIR("channel.walk", MotionTargetRef(IRNodeRef(DOCUMENT_ID, "character.hero"), "joint.hip.rotation", "quaternion"), sampled_resource=ResourceRef("samples.walk", "motion")),), (SOURCE,))
        self.assertEqual(layer.clips[0].clip_id, clip.clip_id)
        self.assertEqual(motion.channels[0].sampled_resource.resource_id, "samples.walk")


class AudioMusicNarrativeTimelineTests(unittest.TestCase):
    def setUp(self):
        self.frame = CoordinateFrameIR("frame.audio", "world", origin=tuple(
            QuantityIR(0, "m", QuantityDimension.LENGTH)
            for _ in range(3)
        ))
        self.range = TimeRangeIR(point(0), point(24))

    def test_audio_media_bytes_are_external_and_spatial_audio_is_frame_aware(self):
        resource = ResourceRef("audio.dialogue", "audio", content_digest="a" * 64, expected_size_bytes=1024)
        audio = AudioIR("audio.line", "dialogue", resource, "audio/wav", AudioSpatialIR("binaural", self.frame, ("left", "right")), trace_refs=(SOURCE,))
        self.assertFalse(hasattr(audio, "media_bytes"))
        self.assertEqual(audio.spatial.coordinate_frame.frame_id, self.frame.frame_id)
        with self.assertRaises(IRSchemaError):
            AudioSpatialIR("binaural", None, ("left", "right"))

    def test_voice_persona_and_speaker_ids_remain_opaque(self):
        voice = VoiceIdentityRef(ExternalIdentityRef("m40.voice_identity", "voice.voiceover", "v1"))
        persona = PersonaRef(ExternalIdentityRef("m05.persona_dna", "persona.host", "v1"))
        speaker = SpeakerRef(ExternalIdentityRef("m39.speaker", "speaker.host", "v1"))
        self.assertEqual((voice.reference.authority, persona.reference.authority, speaker.reference.authority), ("m40.voice_identity", "m05.persona_dna", "m39.speaker"))
        with self.assertRaises(IRSchemaError):
            VoiceIdentityRef(ExternalIdentityRef("provider.voice", "voice", "v1"))

    def test_audio_clip_binding_uses_range_and_rational_offset(self):
        binding = AudioClipBindingIR("audio.bind", "audio.line", self.range, Fraction(1, 2), 0.75)
        self.assertEqual(binding.start_offset, Fraction(1, 2))
        with self.assertRaises(IRSchemaError):
            AudioClipBindingIR("audio.bad", "audio.line", self.range, Fraction(-1), 1)

    def test_music_is_independent_of_midi_and_allows_free_meter_semantics(self):
        tempo = MusicTempoIR(point(0, TemporalLayer.SEMANTIC), Fraction(93, 2))
        event = MusicEventIR("music.texture", MusicEventKind.TEXTURE, point(0, TemporalLayer.SEMANTIC), DurationIR("time.24fps", Fraction(24)), "pad")
        section = MusicSectionIR("section.ambient", "ambient bed", TimeRangeIR(point(0, TemporalLayer.SEMANTIC), point(24, TemporalLayer.SEMANTIC)), ("pad",))
        music = MusicIR("music.score", "time.24fps", (event,), (tempo,), None, (section,), ("pad",), None)
        self.assertIsNone(music.meter)
        self.assertIsNone(music.tonal_center)
        self.assertFalse(any(hasattr(music, name) for name in ("midi_file", "midi_channel", "daw_project")))

    def test_timeline_and_narrative_projection_remain_local(self):
        cue = NarrativeCueIR(
            "cue.title", self.range, "caption", "A local descriptive cue",
            ExternalIdentityRef("m43.canon", "canon.world.state", "v1"), True, (SOURCE,),
        )
        projection = NarrativeProjectionIR("narrative.local", (cue,), (cue.canon_ref,))
        self.assertTrue(projection.cues[0].local_projection_only)
        with self.assertRaises(Exception):
            NarrativeCueIR("cue.promote", self.range, "canon-write", "forbidden", local_projection_only=False, source_refs=(SOURCE,))

    def test_sync_tolerance_fails_closed_when_required(self):
        relation = SyncRelationIR("sync.av", SyncKind.AUDIO_VISUAL, point(5), point(7), Fraction(2), Fraction(1), True, (SOURCE,))
        result = relation.evaluate(point(10), point(12))
        self.assertTrue(result.within_tolerance)
        with self.assertRaises(IRIntegrityError):
            relation.evaluate(point(10), point(14))

    def test_required_sync_relation_needs_source_authority(self):
        with self.assertRaises(Exception):
            SyncRelationIR("sync.untraced", SyncKind.CONTINUITY, point(0), point(0), Fraction(0), Fraction(1), True, ())


if __name__ == "__main__":
    unittest.main()
