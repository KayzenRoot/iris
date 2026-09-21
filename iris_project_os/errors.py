"""M02 error surface.

Every message is expected to name the offending field, the value it received and
the shape it wanted, because these errors are the fail-closed evidence a later
audit reads.
"""

from __future__ import annotations

__all__ = [
    "ProjectOSError",
    "SchemaValidationError",
    "UnsupportedVersionError",
    "UntrustedExtensionError",
    "IdentityError",
    "GraphValidationError",
    "SnapshotClosureError",
    "MergeBlockedError",
    "SideEffectFenceError",
    "RollbackBlockedError",
    "BuildError",
    "LifecycleError",
    "PromotionBlockedError",
    "ReleaseError",
    "ArchiveError",
    "PortContractError",
    "StoreConflictError",
]


class ProjectOSError(Exception):
    """Base error for the Project OS & Production Graph kernel."""


class SchemaValidationError(ProjectOSError):
    """A payload or value does not satisfy its versioned schema."""


class UnsupportedVersionError(ProjectOSError):
    """A contract, schema or component version is outside the supported set."""


class UntrustedExtensionError(ProjectOSError):
    """Extension metadata is unknown, malformed, or exceeds its admitted size."""


class IdentityError(ProjectOSError):
    """An identity, alias, locator or supersession rule was violated."""


class GraphValidationError(ProjectOSError):
    """A graph revision is untyped, cyclic in material causality, or inconsistent."""


class SnapshotClosureError(ProjectOSError):
    """A snapshot class claims a completeness its closure manifest does not carry."""


class MergeBlockedError(ProjectOSError):
    """A branch head may not advance while blocking semantic conflicts remain."""


class SideEffectFenceError(ProjectOSError):
    """A rollback moves state back over mutations the outside world already saw."""


class RollbackBlockedError(ProjectOSError):
    """A rollback plan carries blocking consequences that were not acknowledged."""


class BuildError(ProjectOSError):
    """A build plan, frontier or reuse admission request is not admissible."""


class LifecycleError(ProjectOSError):
    """A state vector is contradictory or a transition is not legal."""


class PromotionBlockedError(ProjectOSError):
    """A promotion gate failed, is stale, or is blocked by an UNKNOWN."""


class ReleaseError(ProjectOSError):
    """A release transaction cannot proceed or needs external reconciliation."""


class ArchiveError(ProjectOSError):
    """An archive manifest is incomplete, damaged, or its tier policy is violated."""


class PortContractError(ProjectOSError):
    """An extension port was used outside the contract its provider admitted."""


class StoreConflictError(ProjectOSError):
    """A record already exists with different content, so the write is conflicting."""
