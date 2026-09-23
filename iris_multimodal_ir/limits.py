"""Deterministic, caller-visible limits for hostile or accidentally huge IR inputs."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import IRLimitError, IRSchemaError

__all__ = ["IRLimits", "DEFAULT_LIMITS"]


@dataclass(frozen=True)
class IRLimits:
    max_nodes: int = 20_000
    max_edges: int = 80_000
    max_depth: int = 256
    max_fanout: int = 4_096
    max_facets: int = 20_000
    max_properties: int = 100_000
    max_text_chars: int = 16_384
    max_inline_payload_bytes: int = 4_000_000
    max_resource_refs: int = 20_000
    max_temporal_samples: int = 1_000_000

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise IRSchemaError(f"{name} must be a positive integer")

    def require(self, name: str, observed: int) -> None:
        limit = getattr(self, name, None)
        if not isinstance(limit, int):
            raise IRSchemaError(f"unknown IR limit {name!r}")
        if observed > limit:
            raise IRLimitError(f"{name} exceeded: observed {observed}, admitted maximum {limit}")


DEFAULT_LIMITS = IRLimits()
