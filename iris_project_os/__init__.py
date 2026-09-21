"""IRIS M02 Project OS & Production Graph kernel.

Domain-neutral, typed and deterministic project state: identity, a definition graph with typed ports,
branches and snapshots, incremental build and reuse, lifecycle, promotion, release and archive — plus the
extension boundaries later modules implement. This package runs no tool, imports no asset, renderer,
cloud, database or provider library, and holds no network call: real providers reach the kernel through
the ports in :mod:`iris_project_os.ports`, and :mod:`iris_project_os.stores` states what a repository has
to satisfy without choosing one.

Quality vocabulary is borrowed, never rebuilt: the ladder, the fidelity contract and the canonical JSON
form all come from :mod:`iris_quality`, so a fingerprint written by either module reads the same way.

The public surface below is exactly what the kernel's modules export, and that is a rule rather than a
shortcut. A hand-copied list of ~390 names is a second API that drifts the moment a module adds a record,
and the failure mode is invisible: the type exists, works, and simply cannot be imported by the next
caller. So the surface is derived, and the two things that can go wrong are refused at import — a name
two modules claim with two different objects, and a module that exports nothing.
"""

from __future__ import annotations

from types import ModuleType

from . import (
    analysis,
    archive,
    base,
    branching,
    build,
    diffing,
    errors,
    graph,
    identity,
    lifecycle,
    limits,
    machines,
    merge,
    ports,
    promotion,
    release,
    reuse,
    serialization,
    snapshots,
    stores,
    versions,
)
from .errors import SchemaValidationError

__version__ = "0.1.0"

_MODULES: tuple[ModuleType, ...] = (
    analysis,
    archive,
    base,
    branching,
    build,
    diffing,
    errors,
    graph,
    identity,
    lifecycle,
    limits,
    machines,
    merge,
    ports,
    promotion,
    release,
    reuse,
    serialization,
    snapshots,
    stores,
    versions,
)


def _public_surface() -> dict[str, str]:
    """Every name the kernel exports, mapped to the module that owns it, refusing an ambiguous claim.

    A name re-exported by two modules is fine when both mean the same object — ``admit_reuse`` is
    documented where it lives and where it is used. Two *different* objects under one name is not a
    packaging detail: whichever one the package happened to bind first would decide what callers get.
    """

    found: dict[str, str] = {}
    for module in _MODULES:
        exported = getattr(module, "__all__", None)
        if not exported:
            raise SchemaValidationError(
                f"{module.__name__} exports no __all__, so the kernel cannot state what it promises"
            )
        for name in exported:
            if not hasattr(module, name):
                raise SchemaValidationError(
                    f"{module.__name__} lists {name!r} in __all__ but does not define it"
                )
            owner = found.get(name)
            if owner is not None and getattr(module, name) is not globals().get(name):
                raise SchemaValidationError(
                    f"{name} is exported by both {owner} and {module.__name__} as two different objects; "
                    "one of them has to be renamed before either can mean anything at package level"
                )
            found.setdefault(name, module.__name__)
            globals()[name] = getattr(module, name)
    return found


_OWNERS: dict[str, str] = _public_surface()

__all__ = sorted(_OWNERS) + ["__version__"]
