"""Errors raised by the provider-neutral M06 operational state kernel."""

from __future__ import annotations

__all__ = [
    "ProductionStateError",
    "ProductionStateValidationError",
    "ProductionStateIntegrityError",
    "ProductionStateAdmissionError",
    "ProductionStateLimitError",
    "ProductionStateAuthorityError",
]


class ProductionStateError(Exception):
    """Base class for M06 contract failures."""


class ProductionStateValidationError(ProductionStateError, ValueError):
    """A value does not satisfy the frozen M06 schema."""


class ProductionStateIntegrityError(ProductionStateError):
    """A digest, immutable record, or exact-reference check failed."""


class ProductionStateAdmissionError(ProductionStateError):
    """Required positive evidence is missing, stale, unknown, or untrusted."""


class ProductionStateLimitError(ProductionStateError):
    """A caller exceeded a frozen M06 resource bound."""


class ProductionStateAuthorityError(ProductionStateError):
    """A request attempts to cross an M02/M05/M55 or downstream authority boundary."""
