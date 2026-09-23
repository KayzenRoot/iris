"""Closed, versioned semantic vocabularies for M04."""

from enum import Enum

__all__ = [
    "RequirementLevel", "SupportState", "RepresentationState", "SemanticLossClass",
    "CyclePolicy", "CompositionPrecedence", "ProjectionKind", "QuantityDimension",
    "Physicality", "TemporalLayer", "MusicEventKind", "SyncKind", "SchemaUnknownPolicy",
    "EquivalenceKind", "ReadinessState", "NodeKind", "ValidationSeverity",
]


class RequirementLevel(str, Enum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"
    OPAQUE = "OPAQUE"


class SupportState(str, Enum):
    EXACT = "EXACT"
    BOUNDED = "BOUNDED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


class RepresentationState(str, Enum):
    EXACT = "EXACT"
    BOUNDED = "BOUNDED"
    DEFERRED = "DEFERRED"
    EXTENSION_REQUIRED = "EXTENSION_REQUIRED"
    BLOCKED = "BLOCKED"


class SemanticLossClass(str, Enum):
    LOSSLESS_REQUIRED = "LOSSLESS_REQUIRED"
    BOUNDED_APPROXIMATION = "BOUNDED_APPROXIMATION"
    CREATIVE_FREEDOM = "CREATIVE_FREEDOM"
    ADVISORY = "ADVISORY"


class CyclePolicy(str, Enum):
    ACYCLIC = "ACYCLIC"
    ALLOW = "ALLOW"


class CompositionPrecedence(str, Enum):
    BASE = "BASE"
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    OVERRIDE = "OVERRIDE"


class ProjectionKind(str, Enum):
    PERSPECTIVE = "PERSPECTIVE"
    ORTHOGRAPHIC = "ORTHOGRAPHIC"
    EQUIRECTANGULAR = "EQUIRECTANGULAR"
    FISHEYE = "FISHEYE"
    CALIBRATED = "CALIBRATED"
    OTHER = "OTHER"


class QuantityDimension(str, Enum):
    LENGTH = "LENGTH"
    ANGLE = "ANGLE"
    TIME = "TIME"
    MASS = "MASS"
    TEMPERATURE = "TEMPERATURE"
    LUMINOUS_INTENSITY = "LUMINOUS_INTENSITY"
    ILLUMINANCE = "ILLUMINANCE"
    LUMINANCE = "LUMINANCE"
    FREQUENCY = "FREQUENCY"
    DIMENSIONLESS = "DIMENSIONLESS"
    OTHER = "OTHER"


class Physicality(str, Enum):
    PHYSICAL = "PHYSICAL"
    ARTISTIC = "ARTISTIC"
    NON_PHYSICAL = "NON_PHYSICAL"


class TemporalLayer(str, Enum):
    SEMANTIC = "SEMANTIC"
    AUTHORED = "AUTHORED"
    SAMPLED = "SAMPLED"
    EDITORIAL = "EDITORIAL"


class MusicEventKind(str, Enum):
    NOTE = "NOTE"
    REST = "REST"
    DYNAMIC = "DYNAMIC"
    TEMPO = "TEMPO"
    METER = "METER"
    TEXTURE = "TEXTURE"
    OTHER = "OTHER"


class SyncKind(str, Enum):
    AUDIO_VISUAL = "AUDIO_VISUAL"
    MOTION_AUDIO = "MOTION_AUDIO"
    NARRATIVE_TIMELINE = "NARRATIVE_TIMELINE"
    CONTINUITY = "CONTINUITY"
    OTHER = "OTHER"


class SchemaUnknownPolicy(str, Enum):
    FAIL_CLOSED = "FAIL_CLOSED"
    PRESERVE_OPTIONAL_OPAQUE = "PRESERVE_OPTIONAL_OPAQUE"


class EquivalenceKind(str, Enum):
    EXACT = "EXACT"
    STRUCTURAL = "STRUCTURAL"
    SEMANTIC = "SEMANTIC"
    TOLERANT = "TOLERANT"
    OPAQUE = "OPAQUE"
    LOSS = "LOSS"
    ONE_WAY = "ONE_WAY"


class ReadinessState(str, Enum):
    READY = "READY"
    READY_WITH_GAPS = "READY_WITH_GAPS"
    BLOCKED = "BLOCKED"


class NodeKind(str, Enum):
    SCENE = "SCENE"
    ENTITY = "ENTITY"
    ASSET = "ASSET"
    CHARACTER = "CHARACTER"
    GEOMETRY = "GEOMETRY"
    COLLECTION = "COLLECTION"
    CAMERA = "CAMERA"
    LIGHT = "LIGHT"
    MATERIAL = "MATERIAL"
    AUDIO = "AUDIO"
    MOTION = "MOTION"
    OTHER = "OTHER"


class ValidationSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"
