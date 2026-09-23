"""IRIS M07 provider-neutral Hardware Genome and Runtime Discovery kernel."""

from __future__ import annotations

from types import ModuleType

from . import (
    base,
    capabilities,
    deltas,
    discovery,
    enums,
    errors,
    evidence,
    families,
    genome,
    invariants,
    limits,
    media,
    migration,
    ports,
    precision,
    projections,
    recovery,
    redaction,
    registry,
    schema,
    serialization,
    subjects,
    telemetry,
    topology,
    validation,
    versions,
)
from .errors import HardwareGenomeIntegrityError, HardwareGenomeValidationError

__version__ = "1.0.0"

_MODULES: tuple[ModuleType, ...] = (
    base,
    capabilities,
    deltas,
    discovery,
    enums,
    errors,
    evidence,
    families,
    genome,
    invariants,
    limits,
    media,
    migration,
    ports,
    precision,
    projections,
    recovery,
    redaction,
    registry,
    schema,
    serialization,
    subjects,
    telemetry,
    topology,
    validation,
    versions,
)


def _public_surface() -> dict[str, str]:
    owners: dict[str, str] = {}
    for module in _MODULES:
        exported = getattr(module, "__all__", None)
        if not exported:
            raise HardwareGenomeValidationError(f"{module.__name__} must declare a non-empty __all__")
        for name in exported:
            if not hasattr(module, name):
                raise HardwareGenomeValidationError(f"{module.__name__} exports undefined symbol {name!r}")
            owner = owners.get(name)
            if owner is not None and getattr(module, name) is not globals().get(name):
                raise HardwareGenomeIntegrityError(f"ambiguous M07 public export {name!r} from {owner} and {module.__name__}")
            owners.setdefault(name, module.__name__)
            globals()[name] = getattr(module, name)
    return owners


_OWNERS = _public_surface()
__all__ = sorted(_OWNERS) + ["__version__"]
