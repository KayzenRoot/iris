from __future__ import annotations

__all__ = [
    "QualityKernelError",
    "SchemaValidationError",
    "UnsupportedVersionError",
    "ContractValidationError",
    "RegistrationError",
    "UntrustedExtensionError",
    "PromotionBlockedError",
    "EvaluationInputError",
]


class QualityKernelError(Exception):
    """Base error. Every message names the offending field and the expected shape."""


class SchemaValidationError(QualityKernelError):
    """A payload or value does not satisfy its versioned schema."""


class UnsupportedVersionError(QualityKernelError):
    """A contract, schema or component version is outside the supported set."""


class ContractValidationError(QualityKernelError):
    """A Fidelity Contract is internally inconsistent or incomplete."""


class RegistrationError(QualityKernelError):
    """An evaluator or domain profile cannot be registered."""


class UntrustedExtensionError(QualityKernelError):
    """Extension metadata is malformed, unknown, or exceeds its admitted shape."""


class PromotionBlockedError(QualityKernelError):
    """A quality class transition is not allowed by the ladder or lacks evidence."""


class EvaluationInputError(QualityKernelError):
    """Inputs handed to the decision engine do not belong to the contract."""
