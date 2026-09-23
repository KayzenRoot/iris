"""Typed failures for the provider-neutral M08 semantic kernel."""

from __future__ import annotations

__all__ = [
    "MicrobenchmarkError",
    "MicrobenchmarkValidationError",
    "MicrobenchmarkIntegrityError",
    "MicrobenchmarkAdmissionError",
    "MicrobenchmarkLimitError",
    "MicrobenchmarkSecurityError",
    "MicrobenchmarkCompatibilityError",
    "MicrobenchmarkAuthorityError",
]


class MicrobenchmarkError(Exception):
    """Base error for M08 kernel failures."""


class MicrobenchmarkValidationError(MicrobenchmarkError, ValueError):
    """Input is malformed or semantically invalid."""


class MicrobenchmarkIntegrityError(MicrobenchmarkError):
    """A supposedly immutable or evidence-bound value failed verification."""


class MicrobenchmarkAdmissionError(MicrobenchmarkError):
    """Evidence cannot be admitted under the frozen protocol contract."""


class MicrobenchmarkLimitError(MicrobenchmarkError):
    """A caller-visible complexity or resource bound was exceeded."""


class MicrobenchmarkSecurityError(MicrobenchmarkError):
    """A serialized input or adapter reference crossed a closed boundary."""


class MicrobenchmarkCompatibilityError(MicrobenchmarkError):
    """A schema, migration, or evidence comparison is incompatible."""


class MicrobenchmarkAuthorityError(MicrobenchmarkError):
    """An operation attempts to claim authority owned outside M08."""
