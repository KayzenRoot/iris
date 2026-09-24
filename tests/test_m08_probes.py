from __future__ import annotations

import unittest
from dataclasses import replace

from iris_microbenchmark import (
    AudioProbeDescriptor, AudioSampleFormat, BackendAdapterCapsule, CorrectnessEvidence,
    CorrectnessState, Domain, FixtureKind, FixtureManifest, ImageProbeDescriptor,
    MicrobenchmarkAdmissionError,
    MicrobenchmarkIntegrityError, MicrobenchmarkLimitError, PrivacyClass,
    ProbeDirection, ProbeDefinition, ThreeDProbeDescriptor, TransferDirection,
    TransferProbeDescriptor, VideoPath, VideoProbeDescriptor, content_digest,
    validate_probe_bank,
)
from m08_support import fixture, measurement_result, probe, protocol


class TestMultimodalProbes(unittest.TestCase):
    def test_probe_fixture_and_correctness_contract(self):
        selected_protocol = protocol()
        selected_fixture = fixture()
        selected_probe = probe(selected_protocol, selected_fixture)
        self.assertTrue(validate_probe_bank((selected_fixture,), (selected_probe,)))
        self.assertEqual(selected_fixture.fixture_digest, content_digest(("fixture", selected_fixture.fixture_id)))
        self.assertEqual(selected_fixture.privacy_class, PrivacyClass.SYNTHETIC)

        with self.assertRaises(MicrobenchmarkIntegrityError):
            FixtureManifest("bad-synthetic", "0" * 64, "generator", "1.0", FixtureKind.DETERMINISTIC_SYNTHETIC, PrivacyClass.PUBLIC, "license", "seed", 8)
        wrong_fixture = replace(selected_fixture, fixture_id="other-fixture")
        with self.assertRaises(MicrobenchmarkAdmissionError):
            validate_probe_bank((wrong_fixture,), (selected_probe,))

        source = measurement_result()
        failed = CorrectnessEvidence(
            "oracle", "1.0", CorrectnessState.FAIL, "1" * 64, "2" * 64, "3" * 64,
            None, 29, "oracle-failure-01",
        )
        with self.assertRaises(MicrobenchmarkAdmissionError):
            type(source)(
                source.result_id, source.protocol_id, source.protocol_version, source.binding,
                source.metric, source.samples, source.aggregate_value, source.uncertainty,
                source.state, failed, source.interference, None, source.measured_at_ms,
                source.raw_digest, source.origin, source.external_measurement_ref,
            )
        duplicate = replace(selected_probe, probe_id=selected_probe.probe_id)
        with self.assertRaises(MicrobenchmarkIntegrityError):
            validate_probe_bank((selected_fixture,), (selected_probe, duplicate))

    def test_directional_transfer_paths_and_synchronization(self):
        host_to_device = TransferProbeDescriptor("h2d", "fixture-small-tensor", TransferDirection.HOST_TO_DEVICE, 4096, "device-event-sync", "pinned", "cpu-subject-01", "gpu-subject-01")
        device_to_host = TransferProbeDescriptor("d2h", "fixture-small-tensor", TransferDirection.DEVICE_TO_HOST, 4096, "device-event-sync", "pageable", "gpu-subject-01", "cpu-subject-01")
        local = TransferProbeDescriptor("device-local", "fixture-small-tensor", TransferDirection.DEVICE_LOCAL, 4096, "device-event-sync", "unified", "gpu-subject-01", "gpu-subject-01")
        peer = TransferProbeDescriptor("peer", "fixture-small-tensor", TransferDirection.PEER_TO_PEER, 4096, "peer-completion", "pinned", "gpu-subject-a", "gpu-subject-b")
        fixture_value = fixture()
        self.assertTrue(validate_probe_bank((fixture_value,), (), transfers=(host_to_device, device_to_host, local, peer)))
        self.assertEqual(host_to_device.direction, TransferDirection.HOST_TO_DEVICE)
        self.assertEqual(device_to_host.direction, TransferDirection.DEVICE_TO_HOST)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            TransferProbeDescriptor("peer-invalid", fixture_value.fixture_id, TransferDirection.PEER_TO_PEER, 16, "sync", "pinned", "same", "same")
        with self.assertRaises(MicrobenchmarkIntegrityError):
            TransferProbeDescriptor("local-invalid", fixture_value.fixture_id, TransferDirection.DEVICE_LOCAL, 16, "sync", "unified", "gpu-a", "gpu-b")
        with self.assertRaises(MicrobenchmarkLimitError):
            TransferProbeDescriptor("too-large", fixture_value.fixture_id, TransferDirection.HOST_TO_DEVICE, 1_000_000_000, "sync", "pinned", "cpu", "gpu")

    def test_image_video_codec_path_and_stream_semantics(self):
        image = ImageProbeDescriptor("image-encode", "fixture-small-tensor", "transform", "png", "rgba", 512, 256, 4, "u8", ProbeDirection.ENCODE)
        image_decode = ImageProbeDescriptor("image-decode", "fixture-small-tensor", "decode", "webp", "rgb", 256, 256, 3, "u8", ProbeDirection.DECODE)
        video_sw = VideoProbeDescriptor("video-sw-encode", "fixture-small-tensor", "h264", "mp4", ProbeDirection.ENCODE, VideoPath.SOFTWARE, "main", 8, "420", 1, 30, 30)
        video_hw_decode = VideoProbeDescriptor("video-hw-decode", "fixture-small-tensor", "hevc", "mkv", ProbeDirection.DECODE, VideoPath.HARDWARE_ENGINE, "main10", 10, "420", 2, 60, 30)
        fixture_value = fixture()
        self.assertTrue(validate_probe_bank((fixture_value,), (), image=(image, image_decode), video=(video_sw, video_hw_decode)))
        self.assertNotEqual(video_sw.direction, video_hw_decode.direction)
        self.assertNotEqual(video_sw.path, video_hw_decode.path)
        self.assertEqual(video_hw_decode.stream_count, 2)
        with self.assertRaises(MicrobenchmarkLimitError):
            VideoProbeDescriptor("too-many-streams", fixture_value.fixture_id, "h264", "mp4", ProbeDirection.ENCODE, VideoPath.SOFTWARE, "main", 8, "420", 17, 30, 30)
        with self.assertRaises(MicrobenchmarkLimitError):
            ImageProbeDescriptor("bad-image", fixture_value.fixture_id, "encode", "png", "rgba", 0, 20, 4, "u8", ProbeDirection.ENCODE)

    def test_3d_primitive_probes_cannot_claim_renderer_fitness(self):
        buffer = ThreeDProbeDescriptor("buffer-copy", "fixture-small-tensor", "buffer", "copy", 4096, "device-event-sync")
        dispatch = ThreeDProbeDescriptor("shader-dispatch", "fixture-small-tensor", "compute", "dispatch", 2048, "dispatch-complete")
        fixture_value = fixture()
        self.assertTrue(validate_probe_bank((fixture_value,), (), three_d=(buffer, dispatch)))
        with self.assertRaises(MicrobenchmarkAdmissionError):
            ThreeDProbeDescriptor("renderer-fps", fixture_value.fixture_id, "scene", "rasterize", 100_000, "present-sync", True)
        with self.assertRaises(MicrobenchmarkLimitError):
            ThreeDProbeDescriptor("unbounded-geometry", fixture_value.fixture_id, "triangles", "dispatch", 10_000_001, "compute-sync")

    def test_audio_probes_use_synthetic_data_without_capture(self):
        pcm = AudioProbeDescriptor("audio-dsp-f32", "fixture-small-tensor", "fft", 48_000, 2, AudioSampleFormat.F32, 4_800)
        integer = AudioProbeDescriptor("audio-mix-s16", "fixture-small-tensor", "mix", 44_100, 2, AudioSampleFormat.S16, 8_820)
        fixture_value = fixture()
        self.assertTrue(validate_probe_bank((fixture_value,), (), audio=(pcm, integer)))
        with self.assertRaises(MicrobenchmarkAdmissionError):
            AudioProbeDescriptor("microphone-capture", fixture_value.fixture_id, "capture", 48_000, 2, AudioSampleFormat.F32, 1_024, True, False)
        with self.assertRaises(MicrobenchmarkAdmissionError):
            AudioProbeDescriptor("speaker-playback", fixture_value.fixture_id, "playback", 48_000, 2, AudioSampleFormat.F32, 1_024, False, True)

    def test_adapter_fallback_and_benchmark_authority_firewall(self):
        selected_protocol = protocol()
        selected_fixture = fixture()
        adapter = BackendAdapterCapsule("adapter-cpu", "1.0.0", selected_protocol.binding.backend_id, "1.0.0", (selected_protocol.operation_family,), ("host-timing",))
        cpu_probe = ProbeDefinition("cpu-fallback", selected_protocol.protocol_id, Domain.SYSTEM, selected_protocol.operation_family, selected_fixture.fixture_id, {"input": 16}, {"output": 16}, "f32", 0, 2, "sync", "exact", adapter, ("backend",))
        self.assertTrue(validate_probe_bank((selected_fixture,), (cpu_probe,)))
        self.assertFalse(hasattr(adapter, "execute"))
        self.assertFalse(hasattr(adapter, "schedule"))
        self.assertFalse(hasattr(adapter, "reserve_vram"))
        self.assertNotEqual(adapter.backend_id, "provider-workflow-compiler")

        unsupported = replace(adapter, supported_operation_families=("other-op",))
        with self.assertRaises(MicrobenchmarkAdmissionError):
            ProbeDefinition("bad-fallback", selected_protocol.protocol_id, Domain.SYSTEM, selected_protocol.operation_family, selected_fixture.fixture_id, {}, {}, "f32", 0, 1, "sync", "exact", unsupported, ())


if __name__ == "__main__":
    unittest.main()
