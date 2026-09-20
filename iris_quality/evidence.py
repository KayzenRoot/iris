from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .errors import SchemaValidationError
from .versions import (
    ComponentVersion,
    require_identifier,
    require_text,
)

__all__ = ["EVIDENCE_KINDS", "EvidenceRef", "require_relative_locator"]

EVIDENCE_KINDS: frozenset[str] = frozenset(
    {
        "METRIC",
        "VALIDATION",
        "HUMAN_DECISION",
        "REFERENCE",
        "PROVENANCE",
        "BENCHMARK",
    }
)

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_ABSOLUTE_LOCATOR = re.compile(r"^(?:[A-Za-z]:[\\/]|/|\\\\|~)")
_WINDOWS_SEPARATOR = re.compile(r"^[^:]*\\")


def require_relative_locator(value: Any, field: str) -> str:
    """Evidence locators stay portable so payloads can later be stored in HIVE verbatim."""

    locator = require_text(value, field, maximum=1024)
    if _ABSOLUTE_LOCATOR.match(locator) or _WINDOWS_SEPARATOR.match(locator):
        raise SchemaValidationError(f"{field} must be relative, got absolute locator {locator!r}")
    if "\x00" in locator or ".." in locator.split("/"):
        raise SchemaValidationError(f"{field} must not escape its project root: {locator!r}")
    return locator


@dataclass(frozen=True)
class EvidenceRef:
    """Dimension- or zone-level proof backing one quality claim."""

    evidence_id: str
    kind: str
    locator: str
    content_sha256: str
    produced_by: ComponentVersion
    dimension_id: Optional[str] = None
    zone_id: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", require_identifier(self.evidence_id, "evidence_id"))
        kind = require_text(self.kind, "kind", maximum=32).upper()
        if kind not in EVIDENCE_KINDS:
            raise SchemaValidationError(
                f"kind must be one of {sorted(EVIDENCE_KINDS)}, got {self.kind!r}"
            )
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "locator", require_relative_locator(self.locator, "locator"))
        digest = require_text(self.content_sha256, "content_sha256", maximum=64)
        if _SHA256_PATTERN.fullmatch(digest) is None:
            raise SchemaValidationError("content_sha256 must be 64 lowercase hexadecimal digits")
        object.__setattr__(self, "content_sha256", digest)
        if not isinstance(self.produced_by, ComponentVersion):
            raise SchemaValidationError("produced_by must be a ComponentVersion")
        if self.dimension_id is not None:
            object.__setattr__(self, "dimension_id", require_identifier(self.dimension_id, "dimension_id"))
        if self.zone_id is not None:
            object.__setattr__(self, "zone_id", require_identifier(self.zone_id, "zone_id"))

    def to_payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "kind": self.kind,
            "locator": self.locator,
            "content_sha256": self.content_sha256,
            "produced_by": self.produced_by.to_payload(),
            "dimension_id": self.dimension_id,
            "zone_id": self.zone_id,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> EvidenceRef:
        if not isinstance(payload, Mapping):
            raise SchemaValidationError("EvidenceRef must be a mapping")
        expected = {
            "evidence_id",
            "kind",
            "locator",
            "content_sha256",
            "produced_by",
            "dimension_id",
            "zone_id",
        }
        unexpected = set(payload) - expected
        if unexpected:
            raise SchemaValidationError(f"EvidenceRef has unknown keys: {sorted(unexpected)}")
        missing = expected - set(payload)
        if missing:
            raise SchemaValidationError(f"EvidenceRef is missing keys: {sorted(missing)}")
        return cls(
            evidence_id=payload["evidence_id"],
            kind=payload["kind"],
            locator=payload["locator"],
            content_sha256=payload["content_sha256"],
            produced_by=ComponentVersion.from_payload(payload["produced_by"]),
            dimension_id=payload["dimension_id"],
            zone_id=payload["zone_id"],
        )
