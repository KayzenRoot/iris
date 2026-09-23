"""Directional, multi-axis DNA compatibility that keeps unknown separate from pass."""

from __future__ import annotations

from dataclasses import dataclass

from .base import CanonicalRecord, SemanticRef, require_refs
from .enums import CompatibilityAxisState, CompatibilityOutcome
from .errors import DNAValidationError
from .identity import DNARevisionRef
from .versions import require_identifier, require_semantic_path, require_text

__all__ = [
    "REQUIRED_COMPATIBILITY_AXES",
    "CompatibilityAxisResult",
    "DNACompatibilityProfile",
    "assess_compatibility",
]

REQUIRED_COMPATIBILITY_AXES = (
    "schema",
    "family_profile",
    "traits",
    "components",
    "anchors",
    "domain_links",
    "extensions",
    "consumer_capability",
    "rights_policy",
)


@dataclass(frozen=True)
class CompatibilityAxisResult(CanonicalRecord):
    axis: str
    state: CompatibilityAxisState
    reason: str
    loss_paths: tuple[str, ...] = ()
    evidence_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        axis = require_identifier(self.axis, "axis")
        if axis not in REQUIRED_COMPATIBILITY_AXES:
            raise DNAValidationError(f"unknown compatibility axis {axis!r}")
        object.__setattr__(self, "axis", axis)
        if not isinstance(self.state, CompatibilityAxisState):
            object.__setattr__(self, "state", CompatibilityAxisState(self.state))
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=2048))
        object.__setattr__(self, "loss_paths", tuple(sorted({require_semantic_path(p) for p in self.loss_paths})))
        object.__setattr__(self, "evidence_refs", require_refs(self.evidence_refs, "evidence_refs"))
        if self.state is CompatibilityAxisState.LOSS and not self.loss_paths:
            raise DNAValidationError("loss compatibility requires an explicit path-level loss surface")


@dataclass(frozen=True)
class DNACompatibilityProfile(CanonicalRecord):
    profile_id: str
    source_ref: DNARevisionRef
    consumer_ref: SemanticRef
    axes: tuple[CompatibilityAxisResult, ...]
    policy_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", require_identifier(self.profile_id, "profile_id"))
        if not isinstance(self.source_ref, DNARevisionRef):
            raise DNAValidationError("source_ref must be a pinned DNARevisionRef")
        if not isinstance(self.consumer_ref, SemanticRef):
            raise DNAValidationError("consumer_ref must be a versioned SemanticRef")
        axes = tuple(self.axes)
        if any(not isinstance(item, CompatibilityAxisResult) for item in axes):
            raise DNAValidationError("axes must contain CompatibilityAxisResult records")
        names = [item.axis for item in axes]
        if len(names) != len(set(names)):
            raise DNAValidationError("compatibility profile contains duplicate axes")
        object.__setattr__(self, "axes", tuple(sorted(axes, key=lambda item: item.axis)))
        object.__setattr__(self, "policy_refs", require_refs(self.policy_refs, "policy_refs"))

    @property
    def outcome(self) -> CompatibilityOutcome:
        return assess_compatibility(self.axes)

    @property
    def missing_axes(self) -> tuple[str, ...]:
        present = {item.axis for item in self.axes}
        return tuple(axis for axis in REQUIRED_COMPATIBILITY_AXES if axis not in present)


def assess_compatibility(axes: tuple[CompatibilityAxisResult, ...]) -> CompatibilityOutcome:
    states = [item.state for item in axes]
    if CompatibilityAxisState.BREAKING in states:
        return CompatibilityOutcome.BREAKING
    present_axes = {item.axis for item in axes}
    if CompatibilityAxisState.UNKNOWN in states or not set(REQUIRED_COMPATIBILITY_AXES) <= present_axes:
        return CompatibilityOutcome.INDETERMINATE
    if CompatibilityAxisState.MIGRATION_REQUIRED in states:
        return CompatibilityOutcome.REQUIRES_MIGRATION
    if CompatibilityAxisState.LOSS in states:
        return CompatibilityOutcome.COMPATIBLE_WITH_LOSS
    if states and all(state is CompatibilityAxisState.EXACT for state in states):
        return CompatibilityOutcome.EXACT
    return CompatibilityOutcome.COMPATIBLE
