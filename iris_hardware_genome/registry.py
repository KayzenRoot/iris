"""Machine-readable canonical and namespaced extension semantic keys."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .base import M07Record
from .enums import FreshnessClass, ObservationState
from .errors import HardwareGenomeAdmissionError, HardwareGenomeIntegrityError, HardwareGenomeValidationError
from .versions import REGISTRY_VERSION, require_identifier, require_unique, require_version

__all__ = ["SemanticKeyDefinition", "SemanticKeyRegistry", "CORE_SEMANTIC_KEYS", "validate_semantic_registry"]

_EXTENSION_KEY = re.compile(r"^[a-z][a-z0-9-]*\.[a-z0-9][a-z0-9._-]{0,190}$")


@dataclass(frozen=True)
class SemanticKeyDefinition(M07Record):
    key: str
    semantic_type: str
    unit: str | None
    allowed_states: tuple[ObservationState, ...]
    freshness: FreshnessClass
    evidence_required: bool
    extension_namespace: str | None = None
    prefix_match: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", require_identifier(self.key, "key"))
        object.__setattr__(self, "semantic_type", require_identifier(self.semantic_type, "semantic_type"))
        if self.unit is not None:
            object.__setattr__(self, "unit", require_identifier(self.unit, "unit"))
        states = tuple(self.allowed_states)
        if not states or any(type(item) is not ObservationState for item in states) or len(states) != len(set(states)):
            raise HardwareGenomeValidationError("semantic keys require distinct allowed observation states")
        object.__setattr__(self, "allowed_states", tuple(sorted(states, key=lambda item: item.value)))
        if type(self.freshness) is not FreshnessClass or type(self.evidence_required) is not bool or type(self.prefix_match) is not bool:
            raise HardwareGenomeValidationError("semantic key freshness/evidence declaration is invalid")
        if self.extension_namespace is not None:
            namespace = require_identifier(self.extension_namespace, "extension_namespace")
            if _EXTENSION_KEY.fullmatch(f"{namespace}.x") is None:
                raise HardwareGenomeValidationError("extension namespace must be a lower-case qualified namespace")
            if not self.key.startswith(namespace + "."):
                raise HardwareGenomeAdmissionError("extension keys must remain inside their declared namespace")
            object.__setattr__(self, "extension_namespace", namespace)


CORE_SEMANTIC_KEYS = (
    SemanticKeyDefinition("hardware.gpu.vendor", "identifier", None, tuple(ObservationState), FreshnessClass.TOPOLOGY_STABLE, True),
    SemanticKeyDefinition("hardware.gpu.dedicated_vram_bytes", "nonnegative_integer", "byte", tuple(ObservationState), FreshnessClass.TOPOLOGY_STABLE, True),
    SemanticKeyDefinition("hardware.memory.shared_bytes", "nonnegative_integer", "byte", tuple(ObservationState), FreshnessClass.TOPOLOGY_STABLE, True),
    SemanticKeyDefinition("hardware.cpu.logical_processors", "nonnegative_integer", "count", tuple(ObservationState), FreshnessClass.BOOT_STABLE, True),
    SemanticKeyDefinition("runtime.os.family", "identifier", None, tuple(ObservationState), FreshnessClass.INSTALL_STABLE, True),
    SemanticKeyDefinition("compute.api", "namespaced_identifier", None, (ObservationState.OBSERVED, ObservationState.UNKNOWN, ObservationState.UNSUPPORTED_PROBE, ObservationState.PERMISSION_DENIED, ObservationState.CONFLICTING, ObservationState.STALE), FreshnessClass.INSTALL_STABLE, True),
    SemanticKeyDefinition("precision.fp32.arithmetic", "evidence_state", None, tuple(ObservationState), FreshnessClass.INSTALL_STABLE, True),
    SemanticKeyDefinition("media.h264.encode", "evidence_state", None, tuple(ObservationState), FreshnessClass.INSTALL_STABLE, True),
    SemanticKeyDefinition("topology.peer_access", "directional_evidence", None, tuple(ObservationState), FreshnessClass.TOPOLOGY_STABLE, True),
    SemanticKeyDefinition("telemetry.gpu.temperature", "finite_number", "celsius", tuple(ObservationState), FreshnessClass.DYNAMIC, True),
    SemanticKeyDefinition("telemetry.gpu.power", "finite_number", "watt", tuple(ObservationState), FreshnessClass.DYNAMIC, True),
    SemanticKeyDefinition("telemetry.gpu.memory_used", "nonnegative_integer", "byte", tuple(ObservationState), FreshnessClass.DYNAMIC, True),
    SemanticKeyDefinition("telemetry.host.memory_pressure", "pressure_state", None, tuple(ObservationState), FreshnessClass.DYNAMIC, True),
    SemanticKeyDefinition("storage.volume.capacity", "nonnegative_integer", "byte", tuple(ObservationState), FreshnessClass.DYNAMIC, True),
    SemanticKeyDefinition("hardware", "reported_hardware_fact", None, tuple(ObservationState), FreshnessClass.UNKNOWN_VOLATILITY, True, prefix_match=True),
    SemanticKeyDefinition("runtime", "reported_runtime_fact", None, tuple(ObservationState), FreshnessClass.UNKNOWN_VOLATILITY, True, prefix_match=True),
    SemanticKeyDefinition("compute", "reported_compute_fact", None, tuple(ObservationState), FreshnessClass.UNKNOWN_VOLATILITY, True, prefix_match=True),
    SemanticKeyDefinition("version", "version_fact", None, tuple(ObservationState), FreshnessClass.INSTALL_STABLE, True, prefix_match=True),
    SemanticKeyDefinition("driver", "driver_relationship", None, tuple(ObservationState), FreshnessClass.TOPOLOGY_STABLE, True, prefix_match=True),
    SemanticKeyDefinition("precision", "precision_dimension", None, tuple(ObservationState), FreshnessClass.INSTALL_STABLE, True, prefix_match=True),
    SemanticKeyDefinition("media", "media_path_fact", None, tuple(ObservationState), FreshnessClass.INSTALL_STABLE, True, prefix_match=True),
    SemanticKeyDefinition("topology", "topology_fact", None, tuple(ObservationState), FreshnessClass.TOPOLOGY_STABLE, True, prefix_match=True),
    SemanticKeyDefinition("telemetry", "telemetry_metric", None, tuple(ObservationState), FreshnessClass.DYNAMIC, True, prefix_match=True),
    SemanticKeyDefinition("storage", "storage_fact", None, tuple(ObservationState), FreshnessClass.UNKNOWN_VOLATILITY, True, prefix_match=True),
)


@dataclass(frozen=True)
class SemanticKeyRegistry(M07Record):
    version: str = REGISTRY_VERSION
    definitions: tuple[SemanticKeyDefinition, ...] = CORE_SEMANTIC_KEYS
    governed_namespaces: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "version", require_version(self.version, "registry version"))
        definitions = tuple(SemanticKeyDefinition.coerce(item, "definitions[]") for item in self.definitions)
        keys = tuple(item.key for item in definitions)
        if len(keys) != len(set(keys)):
            raise HardwareGenomeIntegrityError("semantic registry keys must be unique")
        core = {item.key for item in CORE_SEMANTIC_KEYS}
        for item in definitions:
            if item.extension_namespace is not None:
                if item.key in core:
                    raise HardwareGenomeAdmissionError("extensions cannot shadow canonical semantic keys")
                if any(item.key.startswith(core_item.key + ".") for core_item in CORE_SEMANTIC_KEYS if core_item.prefix_match):
                    raise HardwareGenomeAdmissionError("extensions cannot shadow canonical semantic namespace rules")
                if item.extension_namespace not in self.governed_namespaces:
                    raise HardwareGenomeAdmissionError("extension namespace must be explicitly governed")
        namespaces = tuple(sorted(require_unique(self.governed_namespaces, "governed_namespaces", maximum=256)))
        object.__setattr__(self, "governed_namespaces", namespaces)
        object.__setattr__(self, "definitions", tuple(sorted(definitions, key=lambda item: item.key)))

    def find(self, key: str) -> SemanticKeyDefinition | None:
        key = require_identifier(key, "key")
        exact = next((item for item in self.definitions if item.key == key), None)
        if exact is not None:
            return exact
        matches = [item for item in self.definitions if item.prefix_match and key.startswith(item.key + ".")]
        if not matches:
            return None
        return max(matches, key=lambda item: len(item.key))

    def admit_extension(self, definition: SemanticKeyDefinition) -> "SemanticKeyRegistry":
        definition = SemanticKeyDefinition.coerce(definition, "definition")
        if definition.extension_namespace is None or definition.extension_namespace not in self.governed_namespaces:
            raise HardwareGenomeAdmissionError("extension definition lacks a governed namespace")
        if self.find(definition.key) is not None:
            raise HardwareGenomeAdmissionError("extension cannot replace an existing canonical or extension key")
        return SemanticKeyRegistry(self.version, (*self.definitions, definition), self.governed_namespaces)


def validate_semantic_registry(registry: SemanticKeyRegistry) -> None:
    registry = SemanticKeyRegistry.coerce(registry, "registry")
    if not {item.key for item in CORE_SEMANTIC_KEYS}.issubset({item.key for item in registry.definitions}):
        raise HardwareGenomeIntegrityError("semantic registry omitted a mandatory core key")
