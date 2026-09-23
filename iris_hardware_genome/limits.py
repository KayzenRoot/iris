"""Conservative caller-visible limits for M07 semantic processing."""

from __future__ import annotations

from dataclasses import dataclass, fields

from .errors import HardwareGenomeLimitError, HardwareGenomeValidationError

__all__ = ["HardwareGenomeLimits", "DEFAULT_LIMITS"]


@dataclass(frozen=True)
class HardwareGenomeLimits:
    max_subjects: int = 2_048
    max_observations: int = 50_000
    max_capabilities: int = 20_000
    max_topology_nodes: int = 20_000
    max_topology_edges: int = 80_000
    max_conflicts: int = 10_000
    max_telemetry_samples: int = 20_000
    max_probe_count: int = 256
    max_probe_duration_ms: int = 30_000
    max_probe_output_bytes: int = 2_000_000
    max_evidence_bytes: int = 8_000_000
    max_json_depth: int = 48
    max_json_items: int = 100_000
    max_text_chars: int = 16_384
    max_inline_payload_bytes: int = 8_000_000
    max_extension_fields: int = 2_000
    max_samples_per_window: int = 10_000
    max_topology_depth: int = 128

    def __post_init__(self) -> None:
        for item in fields(self):
            value = getattr(self, item.name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise HardwareGenomeValidationError(f"{item.name} must be a positive integer")

    def require(self, name: str, observed: int) -> None:
        maximum = getattr(self, name, None)
        if not isinstance(maximum, int):
            raise HardwareGenomeValidationError(f"unknown M07 limit {name!r}")
        if isinstance(observed, bool) or not isinstance(observed, int) or observed < 0:
            raise HardwareGenomeValidationError(f"{name} observation must be a non-negative integer")
        if observed > maximum:
            raise HardwareGenomeLimitError(f"{name} permits at most {maximum}; received {observed}")


DEFAULT_LIMITS = HardwareGenomeLimits()
