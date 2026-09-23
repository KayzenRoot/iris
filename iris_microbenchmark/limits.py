"""Caller-visible complexity and safety ceilings for M08 semantic processing."""

from __future__ import annotations

from dataclasses import dataclass, fields

from .errors import MicrobenchmarkLimitError, MicrobenchmarkValidationError

__all__ = ["M08Limits", "DEFAULT_LIMITS"]

_HARD_CEILINGS = {
    "max_protocols": 512,
    "max_metrics_per_protocol": 512,
    "max_results": 100_000,
    "max_samples_per_result": 10_000,
    "max_fixtures": 4_096,
    "max_probes": 16_384,
    "max_context_dimensions": 1_024,
    "max_invalidation_nodes": 50_000,
    "max_invalidation_edges": 100_000,
    "max_invalidation_events": 50_000,
    "max_json_depth": 48,
    "max_json_items": 100_000,
    "max_text_chars": 16_384,
    "max_inline_payload_bytes": 8_000_000,
    "max_protocol_duration_ms": 900_000,
    "max_first_run_protocol_ms": 30_000,
    "max_first_run_total_ms": 120_000,
    "max_warmup_ms": 5_000,
    "max_iterations": 100_000,
    "max_host_allocation_bytes": 536_870_912,
    "max_device_allocation_bytes": 536_870_912,
    "max_output_bytes": 8_000_000,
    "max_concurrency": 16,
    "max_retries": 2,
    "max_cooldown_ms": 300_000,
    "max_search_attempts": 128,
    "max_external_refs": 1_024,
}


@dataclass(frozen=True)
class M08Limits:
    max_protocols: int = 256
    max_metrics_per_protocol: int = 128
    max_results: int = 50_000
    max_samples_per_result: int = 2_000
    max_fixtures: int = 2_048
    max_probes: int = 4_096
    max_context_dimensions: int = 512
    max_invalidation_nodes: int = 20_000
    max_invalidation_edges: int = 40_000
    max_invalidation_events: int = 20_000
    max_json_depth: int = 32
    max_json_items: int = 50_000
    max_text_chars: int = 8_192
    max_inline_payload_bytes: int = 4_000_000
    max_protocol_duration_ms: int = 300_000
    max_first_run_protocol_ms: int = 15_000
    max_first_run_total_ms: int = 60_000
    max_warmup_ms: int = 2_000
    max_iterations: int = 20_000
    max_host_allocation_bytes: int = 268_435_456
    max_device_allocation_bytes: int = 268_435_456
    max_output_bytes: int = 4_000_000
    max_concurrency: int = 8
    max_retries: int = 1
    max_cooldown_ms: int = 120_000
    max_search_attempts: int = 64
    max_external_refs: int = 512

    def __post_init__(self) -> None:
        for item in fields(self):
            value = getattr(self, item.name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise MicrobenchmarkValidationError(f"{item.name} must be a positive integer")
            if value > _HARD_CEILINGS[item.name]:
                raise MicrobenchmarkLimitError(f"{item.name} exceeds the hard ceiling {_HARD_CEILINGS[item.name]}")

    def require(self, name: str, observed: int) -> None:
        maximum = getattr(self, name, None)
        if not isinstance(maximum, int):
            raise MicrobenchmarkValidationError(f"unknown M08 limit {name!r}")
        if isinstance(observed, bool) or not isinstance(observed, int) or observed < 0:
            raise MicrobenchmarkValidationError(f"{name} observation must be a non-negative integer")
        if observed > maximum:
            raise MicrobenchmarkLimitError(f"{name} permits at most {maximum}; received {observed}")


DEFAULT_LIMITS = M08Limits()
