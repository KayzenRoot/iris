"""IRIS M06 provider-neutral operational production-state kernel."""

from __future__ import annotations

from types import ModuleType

from . import (
    base,
    dependencies,
    enums,
    errors,
    families,
    invariants,
    limits,
    lineage,
    migration,
    ports,
    reconstruction,
    regeneration,
    release,
    revisions,
    serialization,
    validation,
    versions,
)
from .errors import ProductionStateIntegrityError, ProductionStateValidationError

__version__ = "1.0.0"

_MODULES: tuple[ModuleType, ...] = (
    base,
    dependencies,
    enums,
    errors,
    families,
    invariants,
    limits,
    lineage,
    migration,
    ports,
    reconstruction,
    regeneration,
    release,
    revisions,
    serialization,
    validation,
    versions,
)


def _public_surface() -> dict[str, str]:
    owners: dict[str, str] = {}
    for module in _MODULES:
        exported = getattr(module, "__all__", None)
        if not exported:
            raise ProductionStateValidationError(f"{module.__name__} must declare a non-empty __all__")
        for name in exported:
            if not hasattr(module, name):
                raise ProductionStateValidationError(f"{module.__name__} exports undefined symbol {name!r}")
            owner = owners.get(name)
            if owner is not None and getattr(module, name) is not globals().get(name):
                raise ProductionStateIntegrityError(f"ambiguous M06 public export {name!r} from {owner} and {module.__name__}")
            owners.setdefault(name, module.__name__)
            globals()[name] = getattr(module, name)
    return owners


_OWNERS = _public_surface()
__all__ = sorted(_OWNERS) + ["__version__"]
