"""Typed failure classes for M09 semantic operations."""

from __future__ import annotations

__all__ = ["M09Error", "M09ValidationError", "M09IntegrityError", "M09AdmissionError"]


class M09Error(Exception):
    """Base class for fail-closed M09 errors."""


class M09ValidationError(M09Error, ValueError):
    """Input violates a frozen M09 semantic contract."""


class M09IntegrityError(M09Error):
    """A digest, identity, lineage or causal reference is inconsistent."""


class M09AdmissionError(M09Error):
    """A state is not eligible to authorize the requested semantic transition."""
