"""Typed failures for the provider-neutral M04 semantic kernel."""

from __future__ import annotations


class IRKernelError(Exception):
    """Base class for deterministic M04 refusal conditions."""


class IRSchemaError(IRKernelError, ValueError):
    """A canonical IR value or serialized payload violates its declared schema."""


class IRIntegrityError(IRKernelError, ValueError):
    """A digest, identity, reference, or immutable-revision contract failed."""


class IRAdmissionError(IRKernelError, ValueError):
    """A required semantic obligation cannot be represented without loss."""


class IRLimitError(IRKernelError, ValueError):
    """A deterministic resource limit refused the input before unbounded work."""


__all__ = [
    "IRAdmissionError",
    "IRIntegrityError",
    "IRKernelError",
    "IRLimitError",
    "IRSchemaError",
]
