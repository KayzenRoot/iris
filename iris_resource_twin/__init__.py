"""IRIS M09 provider-neutral Resource Digital Twin & Dynamic VRAM Governor."""

from __future__ import annotations

from types import ModuleType

from . import evidence, families, invariants, leases, limits, mobility, model, recovery, schema, serialization, shaping, twin, versioning, migration
from .errors import M09Error, M09ValidationError, M09IntegrityError, M09AdmissionError

__version__ = "1.0.0"

_MODULES: tuple[ModuleType, ...] = (
    evidence, families, invariants, leases, limits, mobility, model, recovery,
    schema, serialization, shaping, twin, versioning, migration,
)


def _public_surface() -> dict[str, str]:
    owners: dict[str, str] = {}
    for module in _MODULES:
        exported = getattr(module, "__all__", None)
        if not exported:
            raise M09IntegrityError(f"{module.__name__} must declare a non-empty __all__")
        for name in exported:
            if not hasattr(module, name):
                raise M09IntegrityError(f"{module.__name__} exports undefined symbol {name!r}")
            owner = owners.get(name)
            if owner is not None and getattr(module, name) is not globals().get(name):
                raise M09IntegrityError(f"ambiguous M09 public export {name!r} from {owner} and {module.__name__}")
            owners.setdefault(name, module.__name__)
            globals()[name] = getattr(module, name)
    return owners


_PUBLIC_OWNERS = _public_surface()
__all__ = sorted(_PUBLIC_OWNERS) + ["__version__", "M09Error", "M09ValidationError", "M09IntegrityError", "M09AdmissionError"]
