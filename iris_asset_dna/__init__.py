"""IRIS M05 Asset DNA semantic identity kernel.

The package owns stable subject identity, canonical semantic revisions, typed identity links,
lineage, compatibility and migration contracts. It is deterministic, standard-library-only,
and never performs generation, provider execution, storage, quality judgment or release.

The public surface is derived only from each included module's declared ``__all__``. Conflicting
exports and unlisted module APIs fail during import so callers get one reviewable contract.
"""

from __future__ import annotations

from types import ModuleType

from . import (
    anchors,
    analysis,
    base,
    compatibility,
    context,
    cross_modal,
    drift,
    enums,
    errors,
    families,
    identity,
    imports,
    invariants,
    lineage,
    limits,
    migration,
    packages,
    ports,
    readiness,
    risk,
    serialization,
    traits,
    transitions,
    validation,
    versions,
)
from .errors import DNAIntegrityError, DNAValidationError

__version__ = "0.1.0"

_MODULES: tuple[ModuleType, ...] = (
    anchors,
    analysis,
    base,
    compatibility,
    context,
    cross_modal,
    drift,
    enums,
    errors,
    families,
    identity,
    imports,
    invariants,
    lineage,
    limits,
    migration,
    packages,
    ports,
    readiness,
    risk,
    serialization,
    traits,
    transitions,
    validation,
    versions,
)


def _public_surface() -> dict[str, str]:
    owners: dict[str, str] = {}
    for module in _MODULES:
        exported = getattr(module, "__all__", None)
        if not exported:
            raise DNAValidationError(f"{module.__name__} must declare a non-empty __all__")
        for name in exported:
            if not hasattr(module, name):
                raise DNAValidationError(f"{module.__name__} exports undefined symbol {name!r}")
            owner = owners.get(name)
            if owner is not None and getattr(module, name) is not globals().get(name):
                raise DNAIntegrityError(f"ambiguous public M05 export {name!r} from {owner} and {module.__name__}")
            owners.setdefault(name, module.__name__)
            globals()[name] = getattr(module, name)
    return owners


_OWNERS = _public_surface()
__all__ = sorted(_OWNERS) + ["__version__"]
