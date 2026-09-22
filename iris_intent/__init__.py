"""IRIS M03 Creative Brief, Intent & Constraint Compiler kernel.

Deterministic, typed and domain-neutral intent: a brief frozen into immutable revisions, the statements
and constraints those revisions carry, the slices and fingerprints that make them comparable, the
fidelity contracts and execution intents compiled from them, and the conflicts, overrides, merges and
readiness reports that decide whether a production may move. This package runs no tool, imports no
asset, renderer, cloud, database or provider library, and holds no network, shell or database call:
real providers reach the kernel through the boundaries in :mod:`iris_intent.ports`, and
:mod:`iris_intent.stores` states what a repository has to satisfy without choosing one.

Nothing is judged here that belongs to a neighbour. Quality vocabulary — the ladder, the fidelity
contract, the evaluator authority — is borrowed from :mod:`iris_quality` by object identity, and project
state is read through :mod:`iris_project_os`; M03 cites both and answers for neither. A semantic
fingerprint, a rights clearance and a build id are three different questions, and this package refuses
at construction time rather than letting a later reader confuse them.

The public surface below is exactly what the kernel's modules export, and that is a rule rather than a
shortcut. A hand-copied list of names is a second API that drifts the moment a module adds a record, and
the failure mode is invisible: the type exists, works, and simply cannot be imported by the next caller.
So the surface is derived, and the two things that can go wrong are refused at import — a name two
modules claim with two different objects, and a module that exports nothing.
"""

from __future__ import annotations

from types import ModuleType

from . import (
    admission,
    ambiguity,
    authority,
    base,
    briefs,
    conflicts,
    constraints,
    errors,
    execution,
    explanation,
    fidelity,
    fingerprints,
    freshness,
    identity,
    intent,
    limits,
    merge,
    migration,
    normalization,
    overrides,
    ports,
    predicates,
    readiness,
    reuse,
    serialization,
    slicing,
    sources,
    stores,
    versions,
)
from .errors import SchemaValidationError

__version__ = "0.1.0"

_MODULES: tuple[ModuleType, ...] = (
    admission,
    ambiguity,
    authority,
    base,
    briefs,
    conflicts,
    constraints,
    errors,
    execution,
    explanation,
    fidelity,
    fingerprints,
    freshness,
    identity,
    intent,
    limits,
    merge,
    migration,
    normalization,
    overrides,
    ports,
    predicates,
    readiness,
    reuse,
    serialization,
    slicing,
    sources,
    stores,
    versions,
)


def _public_surface() -> dict[str, str]:
    """Every name the kernel exports, mapped to the module that owns it, refusing an ambiguous claim.

    A name re-exported by two modules is fine when both mean the same object — ``SemanticRef`` is
    documented where it lives and used where it binds. Two *different* objects under one name is not a
    packaging detail: whichever one the package happened to bind first would decide what every caller
    gets, and the two would keep working in their own modules.
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
