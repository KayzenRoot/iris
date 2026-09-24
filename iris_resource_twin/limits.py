"""Finite caller-adjustable ceilings for M09 semantic operations."""

from __future__ import annotations

from dataclasses import dataclass, fields

__all__ = ["M09Limits", "DEFAULT_LIMITS"]


class M09LimitError(ValueError):
    """A caller exceeded a structural M09 bound."""


_CEILINGS = {
    "max_resources": 100_000,
    "max_events": 100_000,
    "max_claims": 10_000,
    "max_leases": 100_000,
    "max_transfers": 50_000,
    "max_segments": 4_096,
    "max_shapes": 4_096,
    "max_recovery_actions": 128,
    "max_evidence_refs": 2_048,
    "max_json_depth": 48,
    "max_json_items": 100_000,
    "max_text_chars": 16_384,
    "max_payload_bytes": 8_000_000,
    "max_search_steps": 100_000,
}


@dataclass(frozen=True)
class M09Limits:
    max_resources: int = 10_000
    max_events: int = 20_000
    max_claims: int = 1_024
    max_leases: int = 10_000
    max_transfers: int = 4_096
    max_segments: int = 256
    max_shapes: int = 256
    max_recovery_actions: int = 32
    max_evidence_refs: int = 512
    max_json_depth: int = 32
    max_json_items: int = 50_000
    max_text_chars: int = 8_192
    max_payload_bytes: int = 4_000_000
    max_search_steps: int = 10_000

    def __post_init__(self) -> None:
        for item in fields(self):
            value = getattr(self, item.name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{item.name} must be a positive integer")
            if value > _CEILINGS[item.name]:
                raise M09LimitError(f"{item.name} exceeds the hard ceiling {_CEILINGS[item.name]}")

    def require(self, name: str, observed: int) -> None:
        maximum = getattr(self, name, None)
        if type(maximum) is not int:
            raise ValueError(f"unknown M09 limit {name!r}")
        if type(observed) is not int or observed < 0:
            raise ValueError(f"{name} observation must be a non-negative integer")
        if observed > maximum:
            raise M09LimitError(f"{name} permits at most {maximum}; received {observed}")


DEFAULT_LIMITS = M09Limits()
