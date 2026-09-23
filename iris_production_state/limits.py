"""Explicit, conservative resource limits for M06 semantic processing."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ProductionStateLimitError, ProductionStateValidationError

__all__ = ["ProductionStateLimits", "DEFAULT_LIMITS"]


@dataclass(frozen=True)
class ProductionStateLimits:
    max_records: int = 100_000
    max_refs_per_record: int = 20_000
    max_dependencies: int = 50_000
    max_lineage_nodes: int = 100_000
    max_lineage_edges: int = 200_000
    max_fingerprint_dimensions: int = 512
    max_fingerprint_refs: int = 20_000
    max_json_depth: int = 64
    max_json_items: int = 100_000
    max_text_chars: int = 16_384
    max_inline_payload_bytes: int = 8_388_608

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ProductionStateValidationError(f"{name} must be a positive integer")

    def require(self, name: str, actual: int) -> None:
        maximum = getattr(self, name)
        if actual > maximum:
            raise ProductionStateLimitError(f"{name} permits at most {maximum}; received {actual}")


DEFAULT_LIMITS = ProductionStateLimits()
