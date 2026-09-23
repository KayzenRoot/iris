"""The 22 versioned future-facing semantic refs; none executes its owning module."""

from __future__ import annotations

from dataclasses import dataclass

from .base import CanonicalRecord
from .errors import DNAIntegrityError, DNAValidationError
from .versions import PORT_VERSION, require_identifier, require_text, require_version

__all__ = [
    "ExtensionRefPort",
    "ProductionStateRefPort",
    "HardwareExecutionConstraintRef",
    "WorkerPlacementIdentityContextPort",
    "ModelCapabilityIdentityEvidencePort",
    "ConcreteWorkflowIdentityProjectionPort",
    "TrainingIdentityDatasetRefPort",
    "ImageReferenceIdentityEvidencePort",
    "GeometryAppearanceIdentityPort",
    "MotionDNARefPort",
    "RenderObservationPort",
    "DCCIdentityBindingPort",
    "DeliveryProjectionCompatibilityPort",
    "TemporalContinuityEvidencePort",
    "DigitalHumanPersonaBindingPort",
    "VoiceMusicAudioDomainDNAPort",
    "CanonContentCampaignBrandPort",
    "LocalizationIdentityPreservationPort",
    "QualityRepairProposalPort",
    "HIVEMemoryIdentitySlicePort",
    "RightsSecurityEvidencePort",
    "StorageObservabilityAutomationPort",
    "APIExportRecoveryIdentityPort",
    "PORT_TYPES",
    "DEFAULT_PORTS",
    "PORT_BY_NAME",
    "validate_port_catalog",
]


@dataclass(frozen=True)
class ExtensionRefPort(CanonicalRecord):
    port_version: str = PORT_VERSION
    owner_modules: tuple[str, ...] = ()
    semantic_scope: str = ""
    authority_rule: str = "M05 carries versioned refs only and does not execute or mutate the owner."

    def __post_init__(self) -> None:
        object.__setattr__(self, "port_version", require_version(self.port_version, "port_version"))
        object.__setattr__(self, "owner_modules", tuple(sorted({require_identifier(item, "owner_modules[]") for item in self.owner_modules})))
        object.__setattr__(self, "semantic_scope", require_text(self.semantic_scope, "semantic_scope", maximum=512))
        object.__setattr__(self, "authority_rule", require_text(self.authority_rule, "authority_rule", maximum=512))

    @property
    def port_name(self) -> str:
        return type(self).__name__


@dataclass(frozen=True)
class ProductionStateRefPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m02", "m06")
    semantic_scope: str = "Production/build/master/reconstruction references under M02 semantic lifecycle."


@dataclass(frozen=True)
class HardwareExecutionConstraintRef(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m07", "m08", "m09", "m10")
    semantic_scope: str = "Hardware execution constraints cannot mutate identity-critical DNA."


@dataclass(frozen=True)
class WorkerPlacementIdentityContextPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m11", "m12", "m13")
    semantic_scope: str = "Workers and caches consume minimum identity slices and pinned refs."


@dataclass(frozen=True)
class ModelCapabilityIdentityEvidencePort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m14", "m15")
    semantic_scope: str = "Model capability/output remains evidence and cannot self-promote identity."


@dataclass(frozen=True)
class ConcreteWorkflowIdentityProjectionPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m16", "m17")
    semantic_scope: str = "Concrete provider workflows consume projection obligations owned by M16."


@dataclass(frozen=True)
class TrainingIdentityDatasetRefPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m18", "m19", "m53")
    semantic_scope: str = "Training datasets and provenance remain external references."


@dataclass(frozen=True)
class ImageReferenceIdentityEvidencePort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m20", "m21", "m22", "m23", "m24")
    semantic_scope: str = "Image controls and evaluations are evidence, not identity authority."


@dataclass(frozen=True)
class GeometryAppearanceIdentityPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m25", "m26", "m27", "m28", "m29")
    semantic_scope: str = "Representation geometry/material/anatomy binds through explicit anchors."


@dataclass(frozen=True)
class MotionDNARefPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m30",)
    semantic_scope: str = "M30 owns MotionDNA contents; M05 pins link revisions and obligations."


@dataclass(frozen=True)
class RenderObservationPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m31", "m32")
    semantic_scope: str = "Render and simulation outputs remain contextual observations."


@dataclass(frozen=True)
class DCCIdentityBindingPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m26", "m33")
    semantic_scope: str = "DCC IDs remain representation anchors and never define dna_id."


@dataclass(frozen=True)
class DeliveryProjectionCompatibilityPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m34", "m35")
    semantic_scope: str = "Constrained target loss must be explicit and cannot drop required traits silently."


@dataclass(frozen=True)
class TemporalContinuityEvidencePort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m36", "m37", "m38")
    semantic_scope: str = "Temporal/shot continuity evidence cannot mutate canonical M05 DNA."


@dataclass(frozen=True)
class DigitalHumanPersonaBindingPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m39",)
    semantic_scope: str = "M39 persona production continuity binds to the M05 generic identity root."


@dataclass(frozen=True)
class VoiceMusicAudioDomainDNAPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m40", "m41", "m42")
    semantic_scope: str = "Voice, Artist, Music and audio domain contents remain owner-controlled."


@dataclass(frozen=True)
class CanonContentCampaignBrandPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m43", "m44", "m45", "m46")
    semantic_scope: str = "Canon, channel, campaign and brand refs remain distinct owner authorities."


@dataclass(frozen=True)
class LocalizationIdentityPreservationPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m47",)
    semantic_scope: str = "Localization consumes identity obligations without rewriting canonical DNA."


@dataclass(frozen=True)
class QualityRepairProposalPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m01", "m48", "m49", "m50", "m51")
    semantic_scope: str = "Quality/evaluator authority remains M01; repair and agents may propose only."


@dataclass(frozen=True)
class HIVEMemoryIdentitySlicePort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m52",)
    semantic_scope: str = "HIVE consumes derived minimum-sufficient slices and cannot mutate canonical DNA."


@dataclass(frozen=True)
class RightsSecurityEvidencePort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m53", "m54")
    semantic_scope: str = "Rights/provenance and restricted-content policy remain external authorities."


@dataclass(frozen=True)
class StorageObservabilityAutomationPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m55", "m56", "m57")
    semantic_scope: str = "Storage/telemetry/agents observe or propose; M05 performs no backend I/O."


@dataclass(frozen=True)
class APIExportRecoveryIdentityPort(ExtensionRefPort):
    owner_modules: tuple[str, ...] = ("m58", "m59", "m60")
    semantic_scope: str = "API, delivery and recovery consume versioned identity contracts only."


PORT_TYPES = (
    ProductionStateRefPort,
    HardwareExecutionConstraintRef,
    WorkerPlacementIdentityContextPort,
    ModelCapabilityIdentityEvidencePort,
    ConcreteWorkflowIdentityProjectionPort,
    TrainingIdentityDatasetRefPort,
    ImageReferenceIdentityEvidencePort,
    GeometryAppearanceIdentityPort,
    MotionDNARefPort,
    RenderObservationPort,
    DCCIdentityBindingPort,
    DeliveryProjectionCompatibilityPort,
    TemporalContinuityEvidencePort,
    DigitalHumanPersonaBindingPort,
    VoiceMusicAudioDomainDNAPort,
    CanonContentCampaignBrandPort,
    LocalizationIdentityPreservationPort,
    QualityRepairProposalPort,
    HIVEMemoryIdentitySlicePort,
    RightsSecurityEvidencePort,
    StorageObservabilityAutomationPort,
    APIExportRecoveryIdentityPort,
)
DEFAULT_PORTS = tuple(port_type() for port_type in PORT_TYPES)
PORT_BY_NAME = {port.port_name: port for port in DEFAULT_PORTS}


def validate_port_catalog() -> None:
    if len(PORT_TYPES) != 22 or len(DEFAULT_PORTS) != 22 or len(PORT_BY_NAME) != 22:
        raise DNAIntegrityError("M05 must expose exactly 22 unique extension/ref ports")
    if any(port.port_version != PORT_VERSION or not port.owner_modules or not port.semantic_scope for port in DEFAULT_PORTS):
        raise DNAValidationError("every extension/ref port needs version, owner boundary and semantic scope")
