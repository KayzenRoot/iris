"""Typed failures for the provider-neutral M05 semantic kernel."""

from __future__ import annotations


class DNAKernelError(Exception):
    """Base class for deterministic M05 refusal conditions."""


class DNAValidationError(DNAKernelError, ValueError):
    """A semantic record or transport payload violates its declared schema."""


class DNAIntegrityError(DNAKernelError, ValueError):
    """Identity, immutable-history, digest, or reference integrity failed."""


class DNAAdmissionError(DNAKernelError, ValueError):
    """A mandatory identity or authority obligation cannot be represented safely."""


class DNACompatibilityError(DNAAdmissionError):
    """A directional compatibility or migration condition fails closed."""


class DNALimitError(DNAKernelError, ValueError):
    """A deterministic resource bound rejected an input before unbounded work."""


class DNAAuthorityError(DNAAdmissionError):
    """A protected canonical transition lacks an explicit authority decision."""


__all__ = [
    "DNAAdmissionError",
    "DNAAuthorityError",
    "DNACompatibilityError",
    "DNAIntegrityError",
    "DNAKernelError",
    "DNALimitError",
    "DNAValidationError",
]
