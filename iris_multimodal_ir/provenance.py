"""M03 source and M01 obligation references carried by M04 facts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

from iris_intent.identity import SemanticRef

from .base import IRRecord, many, one
from .errors import IRAdmissionError, IRSchemaError
from .versions import require_identifier, require_text

__all__ = ["Traceability", "TraceOrigin", "SemanticFactTrace"]


class TraceOrigin(str, Enum):
    M03_SEMANTIC = "M03_SEMANTIC"
    EXPLICIT_POLICY = "EXPLICIT_POLICY"
    DERIVED = "DERIVED"
    PROVIDER_OBSERVATION = "PROVIDER_OBSERVATION"


@dataclass(frozen=True)
class Traceability(IRRecord):
    source_refs: tuple[SemanticRef, ...] = ()
    policy_refs: tuple[SemanticRef, ...] = ()
    derivation_refs: tuple[SemanticRef, ...] = ()
    origin: TraceOrigin = TraceOrigin.M03_SEMANTIC

    NESTED: ClassVar = {
        "source_refs": many(SemanticRef),
        "policy_refs": many(SemanticRef),
        "derivation_refs": many(SemanticRef),
    }

    def __post_init__(self) -> None:
        for name in ("source_refs", "policy_refs", "derivation_refs"):
            values = tuple(SemanticRef.coerce(item, f"{name}[]") for item in getattr(self, name))
            unique = {item.text: item for item in values}
            object.__setattr__(self, name, tuple(unique[key] for key in sorted(unique)))
        try:
            origin = TraceOrigin(self.origin)
        except ValueError:
            raise IRSchemaError("unknown trace origin") from None
        object.__setattr__(self, "origin", origin)
        if origin is TraceOrigin.PROVIDER_OBSERVATION and (self.source_refs or self.policy_refs):
            raise IRSchemaError("provider observations cannot be admitted as source or policy truth")

    @property
    def admitted(self) -> bool:
        return bool(self.source_refs or self.policy_refs) and self.origin is not TraceOrigin.PROVIDER_OBSERVATION

    def require_admitted(self, field: str = "canonical fact") -> None:
        if not self.admitted:
            raise IRAdmissionError(f"{field} requires an admitted M03 semantic source or explicit policy")


@dataclass(frozen=True)
class SemanticFactTrace(IRRecord):
    fact_id: str
    path: str
    trace: Traceability
    mandatory: bool = True

    NESTED: ClassVar = {"trace": one(Traceability)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "fact_id", require_identifier(self.fact_id, "fact_id"))
        object.__setattr__(self, "path", require_text(self.path, "path", maximum=512))
        if not isinstance(self.trace, Traceability):
            raise IRSchemaError("trace must be Traceability")
        if not isinstance(self.mandatory, bool):
            raise IRSchemaError("mandatory must be bool")
        if self.mandatory:
            self.trace.require_admitted(self.fact_id)
