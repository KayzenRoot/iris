"""Explicit deterministic bounds for hostile or accidentally large M05 inputs."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import DNALimitError, DNAValidationError

__all__ = ["DNARecordLimits", "DEFAULT_LIMITS"]


@dataclass(frozen=True)
class DNARecordLimits:
    max_traits: int = 20_000
    max_anchors: int = 20_000
    max_components: int = 20_000
    max_domain_links: int = 10_000
    max_lineage_edges: int = 20_000
    max_dependencies: int = 20_000
    max_graph_depth: int = 256
    max_canonical_depth: int = 128
    max_inline_payload_bytes: int = 4_000_000
    max_text_chars: int = 16_384
    max_profile_count: int = 32

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise DNAValidationError(f"{name} must be a positive integer")

    def require(self, name: str, observed: int) -> None:
        limit = getattr(self, name, None)
        if not isinstance(limit, int):
            raise DNAValidationError(f"unknown resource limit {name!r}")
        if observed > limit:
            raise DNALimitError(f"{name} exceeded: observed {observed}, maximum {limit}")


DEFAULT_LIMITS = DNARecordLimits()
