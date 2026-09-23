"""Versioned deterministic multimodal probe descriptions and fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from .base import M08Record, freeze_json, require_sequence
from .enums import AudioSampleFormat, Domain, FixtureKind, PrivacyClass, ProbeDirection, TransferDirection, VideoPath
from .errors import MicrobenchmarkAdmissionError, MicrobenchmarkIntegrityError, MicrobenchmarkLimitError, MicrobenchmarkValidationError
from .limits import DEFAULT_LIMITS
from .versions import require_digest, require_identifier, require_nonnegative_int, require_unique, require_version

__all__ = [
    "FixtureManifest", "BackendAdapterCapsule", "ProbeDefinition", "ImageProbeDescriptor",
    "VideoProbeDescriptor", "ThreeDProbeDescriptor", "AudioProbeDescriptor",
    "TransferProbeDescriptor", "validate_probe_bank",
]


@dataclass(frozen=True)
class FixtureManifest(M08Record):
    fixture_id: str
    fixture_digest: str
    generator_id: str
    generator_version: str
    kind: FixtureKind
    privacy_class: PrivacyClass
    license_ref: str | None
    deterministic_seed_ref: str
    payload_bytes: int

    def __post_init__(self) -> None:
        for field in ("fixture_id", "generator_id", "deterministic_seed_ref"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "fixture_digest", require_digest(self.fixture_digest, "fixture_digest"))
        object.__setattr__(self, "generator_version", require_version(self.generator_version, "generator_version"))
        if not isinstance(self.kind, FixtureKind) or not isinstance(self.privacy_class, PrivacyClass):
            raise MicrobenchmarkValidationError("fixture kind and privacy class must use closed M08 vocabularies")
        if self.kind is FixtureKind.DETERMINISTIC_SYNTHETIC:
            if self.privacy_class is not PrivacyClass.SYNTHETIC or self.license_ref is not None:
                raise MicrobenchmarkIntegrityError("synthetic fixtures must be privacy-classified synthetic and need no media license")
        else:
            if self.privacy_class is not PrivacyClass.PUBLIC or self.license_ref is None:
                raise MicrobenchmarkAdmissionError("redistributable fixtures require public classification and an explicit license reference")
            object.__setattr__(self, "license_ref", require_identifier(self.license_ref, "license_ref"))
        object.__setattr__(self, "payload_bytes", require_nonnegative_int(self.payload_bytes, "payload_bytes"))
        DEFAULT_LIMITS.require("max_output_bytes", self.payload_bytes)


@dataclass(frozen=True)
class BackendAdapterCapsule(M08Record):
    adapter_id: str
    version: str
    backend_id: str
    protocol_mechanics_version: str
    supported_operation_families: tuple[str, ...]
    declared_capabilities: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in ("adapter_id", "backend_id"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        object.__setattr__(self, "version", require_version(self.version))
        object.__setattr__(self, "protocol_mechanics_version", require_version(self.protocol_mechanics_version, "protocol_mechanics_version"))
        object.__setattr__(self, "supported_operation_families", tuple(sorted(require_unique(self.supported_operation_families, "supported_operation_families", maximum=512))))
        object.__setattr__(self, "declared_capabilities", tuple(sorted(require_unique(self.declared_capabilities, "declared_capabilities", maximum=512))))


@dataclass(frozen=True)
class ProbeDefinition(M08Record):
    probe_id: str
    protocol_id: str
    domain: Domain
    operation_family: str
    fixture_id: str
    input_shape: dict[str, Any]
    output_shape: dict[str, Any]
    precision: str
    warmup_iterations: int
    measured_iterations: int
    synchronization_semantics: str
    correctness_predicate: str
    adapter: BackendAdapterCapsule
    comparability_axes: tuple[str, ...]

    def __post_init__(self) -> None:
        for field in ("probe_id", "protocol_id", "operation_family", "fixture_id", "precision", "synchronization_semantics", "correctness_predicate"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if not isinstance(self.domain, Domain):
            raise MicrobenchmarkValidationError("domain must be Domain")
        object.__setattr__(self, "input_shape", freeze_json(self.input_shape, "input_shape"))
        object.__setattr__(self, "output_shape", freeze_json(self.output_shape, "output_shape"))
        object.__setattr__(self, "warmup_iterations", require_nonnegative_int(self.warmup_iterations, "warmup_iterations"))
        object.__setattr__(self, "measured_iterations", require_nonnegative_int(self.measured_iterations, "measured_iterations"))
        DEFAULT_LIMITS.require("max_iterations", self.warmup_iterations + self.measured_iterations)
        if self.measured_iterations < 1:
            raise MicrobenchmarkValidationError("probe must declare at least one measured iteration")
        object.__setattr__(self, "adapter", BackendAdapterCapsule.coerce(self.adapter, "adapter"))
        object.__setattr__(self, "comparability_axes", tuple(sorted(require_unique(self.comparability_axes, "comparability_axes", maximum=256))))
        if self.operation_family not in self.adapter.supported_operation_families:
            raise MicrobenchmarkAdmissionError("adapter capsule does not declare this operation family")


@dataclass(frozen=True)
class ImageProbeDescriptor(M08Record):
    probe_id: str
    fixture_id: str
    operation: str
    codec: str
    color_model: str
    width: int
    height: int
    channels: int
    data_type: str
    direction: ProbeDirection

    def __post_init__(self) -> None:
        for field in ("probe_id", "fixture_id", "operation", "codec", "color_model", "data_type"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        for field in ("width", "height", "channels"):
            value = require_nonnegative_int(getattr(self, field), field)
            if value < 1 or value > 32_768:
                raise MicrobenchmarkLimitError(f"{field} is outside the bounded image-probe range")
            object.__setattr__(self, field, value)
        if not isinstance(self.direction, ProbeDirection):
            raise MicrobenchmarkValidationError("direction must be ProbeDirection")


@dataclass(frozen=True)
class VideoProbeDescriptor(M08Record):
    probe_id: str
    fixture_id: str
    codec: str
    container: str
    direction: ProbeDirection
    path: VideoPath
    profile: str
    bit_depth: int
    chroma_format: str
    stream_count: int
    frame_count: int
    gop_frames: int

    def __post_init__(self) -> None:
        for field in ("probe_id", "fixture_id", "codec", "container", "profile", "chroma_format"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if self.direction not in {ProbeDirection.ENCODE, ProbeDirection.DECODE} or not isinstance(self.path, VideoPath):
            raise MicrobenchmarkValidationError("video probes require a distinct encode/decode direction and path")
        for field, maximum in (("bit_depth", 64), ("stream_count", DEFAULT_LIMITS.max_concurrency), ("frame_count", 1_000_000), ("gop_frames", 1_000_000)):
            value = require_nonnegative_int(getattr(self, field), field)
            if value < 1 or value > maximum:
                raise MicrobenchmarkLimitError(f"{field} is outside the bounded video-probe range")
            object.__setattr__(self, field, value)


@dataclass(frozen=True)
class ThreeDProbeDescriptor(M08Record):
    probe_id: str
    fixture_id: str
    primitive: str
    operation: str
    element_count: int
    synchronization_semantics: str
    claims_arbitrary_scene_fps: bool = False

    def __post_init__(self) -> None:
        for field in ("probe_id", "fixture_id", "primitive", "operation", "synchronization_semantics"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        count = require_nonnegative_int(self.element_count, "element_count")
        if count < 1 or count > 10_000_000:
            raise MicrobenchmarkLimitError("element_count is outside the bounded 3D-probe range")
        object.__setattr__(self, "element_count", count)
        if self.claims_arbitrary_scene_fps is not False:
            raise MicrobenchmarkAdmissionError("3D primitive evidence cannot claim arbitrary-scene FPS")


@dataclass(frozen=True)
class AudioProbeDescriptor(M08Record):
    probe_id: str
    fixture_id: str
    operation: str
    sample_rate_hz: int
    channels: int
    sample_format: AudioSampleFormat
    frame_count: int
    requires_microphone: bool = False
    requires_playback: bool = False

    def __post_init__(self) -> None:
        for field in ("probe_id", "fixture_id", "operation"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        for field, maximum in (("sample_rate_hz", 768_000), ("channels", 64), ("frame_count", 100_000_000)):
            value = require_nonnegative_int(getattr(self, field), field)
            if value < 1 or value > maximum:
                raise MicrobenchmarkLimitError(f"{field} is outside the bounded audio-probe range")
            object.__setattr__(self, field, value)
        if not isinstance(self.sample_format, AudioSampleFormat):
            raise MicrobenchmarkValidationError("sample_format must be AudioSampleFormat")
        if self.requires_microphone or self.requires_playback:
            raise MicrobenchmarkAdmissionError("audio probes cannot capture from or play through user devices")


@dataclass(frozen=True)
class TransferProbeDescriptor(M08Record):
    probe_id: str
    fixture_id: str
    direction: TransferDirection
    payload_bytes: int
    synchronization_semantics: str
    memory_semantics: str
    source_subject_id: str | None
    target_subject_id: str | None

    def __post_init__(self) -> None:
        for field in ("probe_id", "fixture_id", "synchronization_semantics", "memory_semantics"):
            object.__setattr__(self, field, require_identifier(getattr(self, field), field))
        if not isinstance(self.direction, TransferDirection):
            raise MicrobenchmarkValidationError("direction must be TransferDirection")
        payload = require_nonnegative_int(self.payload_bytes, "payload_bytes")
        DEFAULT_LIMITS.require("max_device_allocation_bytes", payload)
        if payload < 1:
            raise MicrobenchmarkValidationError("transfer probes require a positive payload size")
        object.__setattr__(self, "payload_bytes", payload)
        for field in ("source_subject_id", "target_subject_id"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, require_identifier(value, field))
        if self.direction is TransferDirection.PEER_TO_PEER and (self.source_subject_id is None or self.target_subject_id is None or self.source_subject_id == self.target_subject_id):
            raise MicrobenchmarkAdmissionError("peer transfers require distinct exact source and target subjects")
        if self.direction is TransferDirection.DEVICE_LOCAL and (self.source_subject_id is None or self.target_subject_id not in {None, self.source_subject_id}):
            raise MicrobenchmarkIntegrityError("device-local transfer cannot be relabeled as a cross-device path")


def validate_probe_bank(
    fixtures: tuple[FixtureManifest, ...],
    probes: tuple[ProbeDefinition, ...],
    image: tuple[ImageProbeDescriptor, ...] = (),
    video: tuple[VideoProbeDescriptor, ...] = (),
    three_d: tuple[ThreeDProbeDescriptor, ...] = (),
    audio: tuple[AudioProbeDescriptor, ...] = (),
    transfers: tuple[TransferProbeDescriptor, ...] = (),
) -> bool:
    fixture_values = require_sequence(fixtures, "fixtures", maximum=DEFAULT_LIMITS.max_fixtures)
    probe_values = require_sequence(probes, "probes", maximum=DEFAULT_LIMITS.max_probes)
    raw_groups = tuple(
        require_sequence(group, f"{kind.__name__}[]", maximum=DEFAULT_LIMITS.max_probes)
        for kind, group in (
            (ImageProbeDescriptor, image), (VideoProbeDescriptor, video),
            (ThreeDProbeDescriptor, three_d), (AudioProbeDescriptor, audio),
            (TransferProbeDescriptor, transfers),
        )
    )
    if len(probe_values) + sum(len(group) for group in raw_groups) > DEFAULT_LIMITS.max_probes:
        raise MicrobenchmarkLimitError("combined multimodal probe bank exceeds the hard probe-count ceiling")
    fixture_ids = [FixtureManifest.coerce(item, "fixtures[]").fixture_id for item in fixture_values]
    if len(set(fixture_ids)) != len(fixture_ids):
        raise MicrobenchmarkIntegrityError("fixture manifest repeats a fixture identity")
    known = set(fixture_ids)
    generic = tuple(ProbeDefinition.coerce(item, "probes[]") for item in probe_values)
    if len({item.probe_id for item in generic}) != len(generic):
        raise MicrobenchmarkIntegrityError("probe bank repeats a probe identity")
    groups = tuple(
        tuple(cast(type[M08Record], kind).coerce(item, f"{kind.__name__}[]") for item in group)
        for kind, group in zip((ImageProbeDescriptor, VideoProbeDescriptor, ThreeDProbeDescriptor, AudioProbeDescriptor, TransferProbeDescriptor), raw_groups)
    )
    all_ids = [item.probe_id for item in generic]
    all_ids.extend(item.probe_id for group in groups for item in group)
    if len(set(all_ids)) != len(all_ids):
        raise MicrobenchmarkIntegrityError("probe bank repeats a probe identity across modalities")
    for item in generic:
        if item.fixture_id not in known:
            raise MicrobenchmarkAdmissionError("generic probe references an unregistered fixture")
    for item in (item for group in groups for item in group):
        if item.fixture_id not in known:
            raise MicrobenchmarkAdmissionError("probe references an unregistered deterministic fixture")
    return True
