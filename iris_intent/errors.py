"""M03 error surface.

M03 fails closed, so these classes are the audit trail: each one is raised where a
frozen invariant would otherwise be broken silently, and every message names the
offending field or ref and the rule it violated.
"""

from __future__ import annotations

__all__ = [
    "IntentKernelError",
    "SchemaValidationError",
    "UnsupportedVersionError",
    "UntrustedExtensionError",
    "RefError",
    "AmbiguityBlockedError",
    "AdmissionRefusedError",
    "AuthorityError",
    "PredicateError",
    "ToleranceError",
    "ScopeError",
    "RevisionFrozenError",
    "QualityAuthorityError",
    "ProjectAuthorityError",
    "CapabilityGapError",
    "ConflictBlockedError",
    "OverrideRefusedError",
    "StaleSemanticError",
    "ExplanationError",
    "PortContractError",
    "StoreConflictError",
    "LimitExceededError",
]


class IntentKernelError(Exception):
    """Base error for the Creative Brief, Intent & Constraint Compiler kernel."""


class SchemaValidationError(IntentKernelError):
    """A payload or value does not satisfy its versioned M03 schema."""


class UnsupportedVersionError(IntentKernelError):
    """A schema, compiler, profile or policy version is outside the supported set."""


class UntrustedExtensionError(IntentKernelError):
    """An extension, predicate or metadata payload is unknown, malformed or oversized."""


class RefError(IntentKernelError):
    """An opaque reference is malformed, duplicated or points outside the admitted set."""


class AmbiguityBlockedError(IntentKernelError):
    """A BLOCKING ambiguity or open question prevents an admitted compilation."""


class AdmissionRefusedError(IntentKernelError):
    """The Semantic Admission Shield refused a self-asserted authority claim."""


class AuthorityError(IntentKernelError):
    """Authority is missing, forged, or lower than the rule being claimed."""


class PredicateError(IntentKernelError):
    """A constraint predicate is unknown, mandatory-and-unknown, or carries code."""


class ToleranceError(IntentKernelError):
    """A tolerance lacks units/metric semantics or is internally inconsistent."""


class ScopeError(IntentKernelError):
    """A scope is malformed, or scope is being used to imply authority."""


class RevisionFrozenError(IntentKernelError):
    """An admitted brief revision is being edited in place instead of superseded."""


class QualityAuthorityError(IntentKernelError):
    """M03 attempted to act as M01: invent a dimension, grant capability, or judge."""


class ProjectAuthorityError(IntentKernelError):
    """M03 attempted to own M02 state: branch topology, build, lifecycle or ExecutionPlan."""


class CapabilityGapError(IntentKernelError):
    """A mandatory capability, profile or evaluator path is missing and blocks emission."""


class ConflictBlockedError(IntentKernelError):
    """An unresolved BLOCKING or rights-critical conflict blocks admission."""


class OverrideRefusedError(IntentKernelError):
    """An override is unauthorized, targets a non-overridable rule, or lacks a receipt."""


class StaleSemanticError(IntentKernelError):
    """Derived semantics are being used as current after their dependencies changed."""


class ExplanationError(IntentKernelError):
    """An explanation graph is cyclic, disconnected from source, or inconsistent."""


class PortContractError(IntentKernelError):
    """An extension port was used outside the contract its provider admitted."""


class StoreConflictError(IntentKernelError):
    """A record already exists with different content, so the write is conflicting."""


class LimitExceededError(IntentKernelError):
    """A deterministic resource bound was exceeded before any analysis could run."""
