"""Typed failures for the provider-neutral M07 semantic kernel."""

from __future__ import annotations

__all__ = [
    "HardwareGenomeError",
    "HardwareGenomeValidationError",
    "HardwareGenomeIntegrityError",
    "HardwareGenomeAdmissionError",
    "HardwareGenomeLimitError",
    "HardwareGenomeSecurityError",
    "HardwareGenomeCompatibilityError",
    "HardwareGenomeAuthorityError",
]


class HardwareGenomeError(Exception):
    """Base error for M07 kernel failures."""


class HardwareGenomeValidationError(HardwareGenomeError, ValueError):
    """Input is malformed or semantically invalid."""


class HardwareGenomeIntegrityError(HardwareGenomeError):
    """A supposedly immutable or evidence-bound value failed verification."""


class HardwareGenomeAdmissionError(HardwareGenomeError):
    """Evidence or schema semantics cannot be admitted under the contract."""


class HardwareGenomeLimitError(HardwareGenomeError):
    """A caller-visible complexity or resource bound was exceeded."""


class HardwareGenomeSecurityError(HardwareGenomeError):
    """A probe or serialized input crossed a closed security boundary."""


class HardwareGenomeCompatibilityError(HardwareGenomeError):
    """A reader, writer or migration cannot safely interpret a schema."""


class HardwareGenomeAuthorityError(HardwareGenomeError):
    """An operation attempts to claim authority owned outside M07."""
