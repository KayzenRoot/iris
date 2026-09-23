"""Closed M06 state vocabularies. Unknown values are never silently promoted."""

from __future__ import annotations

from enum import Enum
from typing import Any

from .errors import ProductionStateValidationError

__all__ = [
    "AvailabilityState",
    "IntegrityState",
    "MaterializationState",
    "DependencyKind",
    "FingerprintScope",
    "MaterialityState",
    "ImpactState",
    "WorkDisposition",
    "ReproducibilityClass",
    "DivergenceKind",
    "CleanupState",
    "DeletionState",
    "MigrationOperationKind",
    "ReleaseClosureState",
    "IndexState",
    "EquivalenceState",
    "DeletionAuthorizationState",
    "RollbackState",
]


class _ClosedEnum(str, Enum):
    @classmethod
    def parse(cls, value: Any, field: str | None = None):
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise ProductionStateValidationError(f"{field or cls.__name__} must be a known string value")
        try:
            return cls(value.strip().upper())
        except ValueError as error:
            raise ProductionStateValidationError(f"unknown {field or cls.__name__} value {value!r}") from error


class AvailabilityState(_ClosedEnum):
    KNOWN_AVAILABLE = "KNOWN_AVAILABLE"
    KNOWN_MISSING = "KNOWN_MISSING"
    UNKNOWN = "UNKNOWN"
    CORRUPT = "CORRUPT"
    POLICY_BLOCKED = "POLICY_BLOCKED"


class IntegrityState(_ClosedEnum):
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    CORRUPT = "CORRUPT"
    UNKNOWN = "UNKNOWN"


class MaterializationState(_ClosedEnum):
    DECLARED = "DECLARED"
    MATERIALIZED = "MATERIALIZED"
    INTEGRITY_VERIFIED = "INTEGRITY_VERIFIED"
    QUARANTINED = "QUARANTINED"
    RETIRED = "RETIRED"
    UNKNOWN = "UNKNOWN"


class DependencyKind(_ClosedEnum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"
    OBSERVED_ONLY = "OBSERVED_ONLY"
    HIDDEN_MATERIAL = "HIDDEN_MATERIAL"


class FingerprintScope(_ClosedEnum):
    FULL_CAUSAL = "FULL_CAUSAL"
    SELECTED_SLICE = "SELECTED_SLICE"
    RECONSTRUCTION = "RECONSTRUCTION"
    POLICY_SENSITIVE = "POLICY_SENSITIVE"
    IDENTITY_SENSITIVE = "IDENTITY_SENSITIVE"
    TOOLCHAIN_SENSITIVE = "TOOLCHAIN_SENSITIVE"


class MaterialityState(_ClosedEnum):
    MATERIAL = "MATERIAL"
    NON_MATERIAL = "NON_MATERIAL"
    UNKNOWN = "UNKNOWN"


class ImpactState(_ClosedEnum):
    AFFECTED = "AFFECTED"
    UNAFFECTED_PROVEN = "UNAFFECTED_PROVEN"
    POTENTIALLY_AFFECTED = "POTENTIALLY_AFFECTED"
    UNKNOWN = "UNKNOWN"
    BLOCKED_BY_STALE_EVIDENCE = "BLOCKED_BY_STALE_EVIDENCE"


class WorkDisposition(_ClosedEnum):
    REUSE_EXACT = "REUSE_EXACT"
    REUSE_WITH_VERIFICATION = "REUSE_WITH_VERIFICATION"
    VERIFY_ONLY = "VERIFY_ONLY"
    REPAIR_CANDIDATE = "REPAIR_CANDIDATE"
    REBUILD_PARTIAL = "REBUILD_PARTIAL"
    REBUILD_FULL_TARGET = "REBUILD_FULL_TARGET"
    BLOCKED = "BLOCKED"
    NO_WORK_PROVEN = "NO_WORK_PROVEN"


class ReproducibilityClass(_ClosedEnum):
    EXACT_BYTES = "EXACT_BYTES"
    EXACT_SEMANTIC_STATE = "EXACT_SEMANTIC_STATE"
    EQUIVALENT_WITHIN_CONTRACT = "EQUIVALENT_WITHIN_CONTRACT"
    STOCHASTIC_REEXECUTABLE = "STOCHASTIC_REEXECUTABLE"
    REFERENCE_RECONSTRUCTABLE = "REFERENCE_RECONSTRUCTABLE"
    NON_RECONSTRUCTABLE = "NON_RECONSTRUCTABLE"
    UNKNOWN = "UNKNOWN"


class DivergenceKind(_ClosedEnum):
    NONE_PROVEN = "NONE_PROVEN"
    BYTE_DIVERGENCE = "BYTE_DIVERGENCE"
    SEMANTIC_DIVERGENCE = "SEMANTIC_DIVERGENCE"
    EQUIVALENCE_CONTRACT_FAILURE = "EQUIVALENCE_CONTRACT_FAILURE"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    TOOLCHAIN_UNAVAILABLE = "TOOLCHAIN_UNAVAILABLE"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    UNKNOWN = "UNKNOWN"


class CleanupState(_ClosedEnum):
    ELIGIBLE = "ELIGIBLE"
    REACHABLE = "REACHABLE"
    RETENTION_PINNED = "RETENTION_PINNED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    UNKNOWN = "UNKNOWN"
    NOT_SAFE_TO_DELETE = "NOT_SAFE_TO_DELETE"


class DeletionState(_ClosedEnum):
    REQUESTED = "REQUESTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class MigrationOperationKind(_ClosedEnum):
    RENAME = "RENAME"
    COPY = "COPY"
    DEFAULT = "DEFAULT"
    DROP = "DROP"


class ReleaseClosureState(_ClosedEnum):
    CLOSED = "CLOSED"
    INCOMPLETE = "INCOMPLETE"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class IndexState(_ClosedEnum):
    COMPLETE_FRESH = "COMPLETE_FRESH"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    CORRUPT = "CORRUPT"
    UNKNOWN = "UNKNOWN"


class EquivalenceState(_ClosedEnum):
    PROVEN = "PROVEN"
    NOT_PROVEN = "NOT_PROVEN"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class DeletionAuthorizationState(_ClosedEnum):
    AUTHORIZED = "AUTHORIZED"
    REVOKED = "REVOKED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class RollbackState(_ClosedEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"
