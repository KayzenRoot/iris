"""Identity interface capsules and dependency-closed minimum sufficient slices."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .base import CanonicalRecord, SemanticRef, require_refs
from .errors import DNAAdmissionError, DNAIntegrityError, DNAValidationError
from .identity import DNARevision, DNARevisionRef
from .limits import DEFAULT_LIMITS, DNARecordLimits
from .versions import content_digest, require_identifier, require_semantic_path

__all__ = [
    "DNAInterfaceCapsule",
    "MinimumSufficientDNASlice",
    "build_interface_capsule",
    "build_dna_slice",
]


@dataclass(frozen=True)
class DNAInterfaceCapsule(CanonicalRecord):
    dna_id: str
    revision_ref: DNARevisionRef
    family: str
    identity_level: str
    semantic_fingerprint: str
    trait_paths: tuple[str, ...]
    anchor_refs: tuple[SemanticRef, ...]
    domain_link_refs: tuple[SemanticRef, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "dna_id", require_identifier(self.dna_id, "dna_id"))
        if not isinstance(self.revision_ref, DNARevisionRef) or self.revision_ref.dna_id != self.dna_id:
            raise DNAIntegrityError("interface capsule revision must belong to its dna_id")
        object.__setattr__(self, "trait_paths", tuple(sorted({require_semantic_path(p) for p in self.trait_paths})))
        object.__setattr__(self, "anchor_refs", require_refs(self.anchor_refs, "anchor_refs"))
        object.__setattr__(self, "domain_link_refs", require_refs(self.domain_link_refs, "domain_link_refs"))


@dataclass(frozen=True)
class MinimumSufficientDNASlice(CanonicalRecord):
    dna_id: str
    revision_ref: DNARevisionRef
    requested_paths: tuple[str, ...]
    included_paths: tuple[str, ...]
    dependency_paths: tuple[str, ...]
    traits: tuple[object, ...]
    anchor_refs: tuple[SemanticRef, ...]
    domain_link_refs: tuple[SemanticRef, ...]
    provenance_refs: tuple[SemanticRef, ...]
    policy_refs: tuple[SemanticRef, ...]
    source_fingerprint: str
    slice_fingerprint: str

    @property
    def trait_count(self) -> int:
        return len(self.traits)


def build_interface_capsule(revision: DNARevision) -> DNAInterfaceCapsule:
    if not isinstance(revision, DNARevision):
        raise DNAValidationError("revision must be a DNARevision")
    return DNAInterfaceCapsule(
        revision.dna_id,
        revision.ref,
        revision.family.value,
        revision.identity_level.value,
        revision.semantic_digest,
        tuple(item.path for item in revision.traits),
        revision.anchor_refs,
        revision.domain_link_refs,
    )


def build_dna_slice(
    revision: DNARevision,
    requested_paths: tuple[str, ...],
    *,
    dependency_map: Mapping[str, tuple[str, ...]] | None = None,
    limits: DNARecordLimits = DEFAULT_LIMITS,
) -> MinimumSufficientDNASlice:
    if not isinstance(revision, DNARevision):
        raise DNAValidationError("revision must be a DNARevision")
    if not isinstance(requested_paths, (tuple, list)):
        raise DNAValidationError("requested_paths must be a finite sequence")
    limits.require("max_traits", len(requested_paths))
    requested = tuple(sorted({require_semantic_path(item, "requested_paths[]") for item in requested_paths}))
    if not requested:
        raise DNAValidationError("requested_paths must contain at least one trait path")
    traits = revision.trait_map()
    missing = sorted(set(requested) - set(traits))
    if missing:
        raise DNAAdmissionError(f"requested canonical traits are missing: {missing}")
    if dependency_map is not None and type(dependency_map) not in (dict, MappingProxyType):
        raise DNAValidationError("dependency_map must be a plain immutable or mutable mapping")
    dependencies: dict[str, tuple[str, ...]] = {}
    total_dependencies = 0
    for raw_path, raw_dependencies in ({} if dependency_map is None else dependency_map).items():
        path = require_semantic_path(raw_path, "dependency_map path")
        if path in dependencies:
            raise DNAIntegrityError("dependency_map paths collide after canonicalization")
        if type(raw_dependencies) not in (tuple, list):
            raise DNAValidationError("dependency_map values must be finite path sequences")
        total_dependencies += len(raw_dependencies)
        limits.require("max_dependencies", total_dependencies)
        dependencies[path] = tuple(
            require_semantic_path(item, "dependency_path") for item in raw_dependencies
        )
    limits.require("max_dependencies", len(dependencies))
    closure: set[str] = set()
    pending = [(path, 1) for path in requested]
    while pending:
        path, depth = pending.pop()
        limits.require("max_graph_depth", depth)
        if path in closure:
            continue
        closure.add(path)
        limits.require("max_traits", len(closure))
        for dependency in dependencies.get(path, ()):
            normalized = require_semantic_path(dependency, "dependency_path")
            if normalized not in traits:
                raise DNAAdmissionError(f"slice dependency {normalized} is not in the pinned revision")
            if normalized not in closure:
                pending.append((normalized, depth + 1))
    ordered = tuple(sorted(closure))
    selected = tuple(traits[path] for path in ordered)
    provenance = require_refs(
        tuple(set(tuple(ref for trait in selected for ref in trait.provenance_refs) + revision.provenance_refs)),
        "slice provenance refs",
    )
    policies = require_refs(
        tuple(set(tuple(ref for trait in selected for ref in trait.policy_refs) + revision.policy_refs)),
        "slice policy refs",
    )
    body = {
        "dna_id": revision.dna_id,
        "revision_ref": revision.ref,
        "requested_paths": requested,
        "included_paths": ordered,
        "traits": selected,
        "anchor_refs": revision.anchor_refs,
        "domain_link_refs": revision.domain_link_refs,
        "provenance_refs": provenance,
        "policy_refs": policies,
        "source_fingerprint": revision.semantic_digest,
    }
    return MinimumSufficientDNASlice(
        revision.dna_id,
        revision.ref,
        requested,
        ordered,
        tuple(path for path in ordered if path not in requested),
        selected,
        revision.anchor_refs,
        revision.domain_link_refs,
        provenance,
        policies,
        revision.semantic_digest,
        content_digest(body),
    )
