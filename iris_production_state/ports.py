"""Versioned provider-neutral evidence ports; protocols carry facts, never authority."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from .base import CanonicalRecord, require_exact_ref, require_sequence
from .errors import ProductionStateValidationError
from .limits import DEFAULT_LIMITS
from .versions import PORT_VERSION, require_identifier, require_text, require_version

__all__ = [
    "PortEvidenceState",
    "PortRequest",
    "PortResponse",
    "VersionedEvidencePort",
    "HardwareMaterialityEvidencePort",
    "ExecutionAttemptPort",
    "CacheReuseEvidencePort",
    "ModelRevisionEvidencePort",
    "WorkflowRevisionEvidencePort",
    "DomainMaterializationEvidencePort",
    "NarrativeCanonRefPort",
    "CampaignBrandIdentityRefPort",
    "QualityEvidencePort",
    "RepairExecutionPort",
    "HiveContextEvidencePort",
    "ProvenanceRightsConsentPort",
    "SecurityAuthorizationPort",
    "PhysicalMediaStorePort",
    "PhysicalDeletionArchivePort",
    "ObservabilityProjectionPort",
    "AgentProposalPort",
    "ExternalContractPort",
    "PublishingDeliveryPort",
    "SystemRecoveryEvidencePort",
    "M06_PORTS",
    "validate_port_catalog",
]


class PortEvidenceState(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
    FAILED = "FAILED"


@dataclass(frozen=True)
class PortRequest(CanonicalRecord):
    request_id: str
    port_name: str
    requested_capabilities: tuple[str, ...]
    subject_refs: tuple[Any, ...]
    schema_version: str = PORT_VERSION

    def __post_init__(self) -> None:
        require_identifier(self.request_id, "request_id")
        require_identifier(self.port_name, "port_name")
        capabilities = require_sequence(self.requested_capabilities, "requested_capabilities", maximum=DEFAULT_LIMITS.max_fingerprint_dimensions)
        if any(type(value) is not str for value in capabilities) or len(capabilities) != len(set(capabilities)):
            raise ProductionStateValidationError("requested capabilities must be unique strings")
        object.__setattr__(self, "requested_capabilities", tuple(sorted(require_identifier(value, "capability") for value in capabilities)))
        refs = require_sequence(self.subject_refs, "subject_refs", maximum=DEFAULT_LIMITS.max_refs_per_record)
        for index, value in enumerate(refs):
            require_exact_ref(value, f"subject_refs[{index}]")
        object.__setattr__(self, "subject_refs", refs)
        require_version(self.schema_version, "schema_version")


@dataclass(frozen=True)
class PortResponse(CanonicalRecord):
    request_id: str
    port_name: str
    state: PortEvidenceState
    evidence_refs: tuple[Any, ...]
    explanation: str
    schema_version: str = PORT_VERSION

    def __post_init__(self) -> None:
        require_identifier(self.request_id, "request_id")
        require_identifier(self.port_name, "port_name")
        if not isinstance(self.state, PortEvidenceState):
            object.__setattr__(self, "state", PortEvidenceState(self.state))
        refs = require_sequence(self.evidence_refs, "evidence_refs", maximum=DEFAULT_LIMITS.max_refs_per_record)
        for index, value in enumerate(refs):
            require_exact_ref(value, f"evidence_refs[{index}]")
        object.__setattr__(self, "evidence_refs", refs)
        require_text(self.explanation, "explanation", maximum=2048, allow_empty=True)
        require_version(self.schema_version, "schema_version")


@runtime_checkable
class VersionedEvidencePort(Protocol):
    port_version: str = PORT_VERSION

    def exchange(self, request: PortRequest) -> PortResponse:
        """Return observations/capabilities as evidence; do not admit canonical M06 state."""


class HardwareMaterialityEvidencePort(VersionedEvidencePort, Protocol):
    """M07/M08/M09/M10: report materially relevant hardware facts."""


class ExecutionAttemptPort(VersionedEvidencePort, Protocol):
    """M11/M12: report exact execution attempt evidence."""


class CacheReuseEvidencePort(VersionedEvidencePort, Protocol):
    """M13: report cache/reuse observations without authorizing reuse."""


class ModelRevisionEvidencePort(VersionedEvidencePort, Protocol):
    """M14/M18/M19: report exact model revision evidence."""


class WorkflowRevisionEvidencePort(VersionedEvidencePort, Protocol):
    """M16/M17: report exact workflow refs; never compile a provider workflow."""


class DomainMaterializationEvidencePort(VersionedEvidencePort, Protocol):
    """M20-M42/M47: report domain materialization facts without owning domain schemas."""


class NarrativeCanonRefPort(VersionedEvidencePort, Protocol):
    """M43: report narrative/canon refs without owning canon."""


class CampaignBrandIdentityRefPort(VersionedEvidencePort, Protocol):
    """M45/M46: report campaign and brand identity refs."""


class QualityEvidencePort(VersionedEvidencePort, Protocol):
    """M01/M24/M48/M51: transport quality evidence without judging or promoting."""


class RepairExecutionPort(VersionedEvidencePort, Protocol):
    """M49: report repair outcomes; repair execution remains external."""


class HiveContextEvidencePort(VersionedEvidencePort, Protocol):
    """M52: report HIVE context as evidence without self-admission."""


class ProvenanceRightsConsentPort(VersionedEvidencePort, Protocol):
    """M53: report current provenance, rights and consent evidence."""


class SecurityAuthorizationPort(VersionedEvidencePort, Protocol):
    """M54: report current security and restricted-content authorization evidence."""


class PhysicalMediaStorePort(VersionedEvidencePort, Protocol):
    """M55: report content-store availability/integrity; M06 does not implement storage."""


class PhysicalDeletionArchivePort(VersionedEvidencePort, Protocol):
    """M55: report deletion/archive outcomes; physical deletion remains external."""


class ObservabilityProjectionPort(VersionedEvidencePort, Protocol):
    """M56: transport operational projections without owning telemetry storage."""


class AgentProposalPort(VersionedEvidencePort, Protocol):
    """M57: transport agent proposals without canonical self-admission."""


class ExternalContractPort(VersionedEvidencePort, Protocol):
    """M58: report exact external contract evidence."""


class PublishingDeliveryPort(VersionedEvidencePort, Protocol):
    """M59: report publishing/delivery evidence without publishing."""


class SystemRecoveryEvidencePort(VersionedEvidencePort, Protocol):
    """M60: report whole-system recovery evidence without recovery execution."""


M06_PORTS = (
    HardwareMaterialityEvidencePort,
    ExecutionAttemptPort,
    CacheReuseEvidencePort,
    ModelRevisionEvidencePort,
    WorkflowRevisionEvidencePort,
    DomainMaterializationEvidencePort,
    NarrativeCanonRefPort,
    CampaignBrandIdentityRefPort,
    QualityEvidencePort,
    RepairExecutionPort,
    HiveContextEvidencePort,
    ProvenanceRightsConsentPort,
    SecurityAuthorizationPort,
    PhysicalMediaStorePort,
    PhysicalDeletionArchivePort,
    ObservabilityProjectionPort,
    AgentProposalPort,
    ExternalContractPort,
    PublishingDeliveryPort,
    SystemRecoveryEvidencePort,
)


def validate_port_catalog() -> None:
    names = tuple(port.__name__ for port in M06_PORTS)
    if len(names) != 20 or len(names) != len(set(names)):
        raise ProductionStateValidationError("M06 must expose all twenty unique versioned evidence ports")
    if any(not issubclass(port, Protocol) for port in M06_PORTS):
        raise ProductionStateValidationError("every M06 port must remain a protocol boundary")
    if any(port.port_version != PORT_VERSION for port in M06_PORTS):
        raise ProductionStateValidationError("every M06 port must expose the frozen versioned protocol contract")
