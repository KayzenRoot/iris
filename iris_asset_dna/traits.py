"""Versioned trait semantics, applicability and evidence separation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import CanonicalRecord, SemanticRef, freeze_json, require_refs
from .enums import TraitApplicability, TraitCriticality, TraitMutability, TraitPolarity
from .errors import DNAAdmissionError, DNAValidationError
from .versions import require_identifier, require_semantic_path, require_version

__all__ = [
    "TraitSchemaRef",
    "DNATrait",
    "TraitSchemaRegistry",
    "DEFAULT_TRAIT_SCHEMAS",
    "IdentityEvidence",
    "NegativeTraitConstraint",
]


@dataclass(frozen=True, order=True)
class TraitSchemaRef(CanonicalRecord):
    family: str
    version: str
    mandatory: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "family", require_identifier(self.family, "family"))
        object.__setattr__(self, "version", require_version(self.version, "schema version"))
        if not isinstance(self.mandatory, bool):
            raise DNAValidationError("mandatory must be a bool")


@dataclass(frozen=True)
class DNATrait(CanonicalRecord):
    path: str
    schema_ref: TraitSchemaRef
    criticality: TraitCriticality
    mutability: TraitMutability
    applicability: TraitApplicability
    value: Any = None
    polarity: TraitPolarity = TraitPolarity.REQUIRED
    provenance_refs: tuple[SemanticRef, ...] = ()
    policy_refs: tuple[SemanticRef, ...] = ()
    opaque_preservation_policy_ref: SemanticRef | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", require_semantic_path(self.path))
        if not isinstance(self.schema_ref, TraitSchemaRef):
            raise DNAValidationError("schema_ref must be a TraitSchemaRef")
        for name, enum_type in (
            ("criticality", TraitCriticality),
            ("mutability", TraitMutability),
            ("applicability", TraitApplicability),
            ("polarity", TraitPolarity),
        ):
            value = getattr(self, name)
            if not isinstance(value, enum_type):
                try:
                    value = enum_type(value)
                except (TypeError, ValueError) as error:
                    raise DNAValidationError(f"{name} is not a supported M05 value") from error
                object.__setattr__(self, name, value)
        if self.applicability is TraitApplicability.PRESENT:
            if self.value is None:
                raise DNAValidationError("PRESENT traits require a typed value")
            object.__setattr__(self, "value", freeze_json(self.value, f"trait {self.path}"))
        elif self.value is not None:
            raise DNAValidationError(f"{self.applicability.value} traits cannot carry a value")
        object.__setattr__(self, "provenance_refs", require_refs(self.provenance_refs, "provenance_refs"))
        object.__setattr__(self, "policy_refs", require_refs(self.policy_refs, "policy_refs"))
        if any(ref.owner_module != "m53" for ref in self.provenance_refs):
            raise DNAAdmissionError("M53 remains the provenance authority for canonical traits")
        if not self.provenance_refs and not self.policy_refs:
            raise DNAAdmissionError(f"canonical trait {self.path} needs provenance or policy reachability")
        if self.opaque_preservation_policy_ref is not None and not isinstance(
            self.opaque_preservation_policy_ref, SemanticRef
        ):
            raise DNAValidationError("opaque_preservation_policy_ref must be a SemanticRef")
        if not self.schema_ref.mandatory and self.opaque_preservation_policy_ref is None:
            # Known optional schemas need no opaque policy. Unknown optional schemas are
            # checked by TraitSchemaRegistry and require this explicit reference there.
            return

    @property
    def canonical_value(self) -> Any:
        return self.value if self.applicability is TraitApplicability.PRESENT else self.applicability.value


@dataclass(frozen=True)
class NegativeTraitConstraint(CanonicalRecord):
    path: str
    schema_ref: TraitSchemaRef
    forbidden_value: Any
    criticality: TraitCriticality
    provenance_refs: tuple[SemanticRef, ...]
    policy_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", require_semantic_path(self.path))
        if not isinstance(self.schema_ref, TraitSchemaRef):
            raise DNAValidationError("schema_ref must be a TraitSchemaRef")
        object.__setattr__(self, "forbidden_value", freeze_json(self.forbidden_value, "forbidden_value"))
        if not isinstance(self.criticality, TraitCriticality):
            object.__setattr__(self, "criticality", TraitCriticality(self.criticality))
        object.__setattr__(self, "provenance_refs", require_refs(self.provenance_refs, "provenance_refs"))
        object.__setattr__(self, "policy_refs", require_refs(self.policy_refs, "policy_refs"))
        if any(ref.owner_module != "m53" for ref in self.provenance_refs):
            raise DNAAdmissionError("M53 remains the provenance authority for negative identity constraints")
        if not self.provenance_refs and not self.policy_refs:
            raise DNAAdmissionError("negative identity constraints need provenance or policy reachability")


@dataclass(frozen=True)
class IdentityEvidence(CanonicalRecord):
    """Reference-only evidence; evidence never becomes canonical trait truth by itself."""

    evidence_id: str
    evidence_kind: str
    source_ref: SemanticRef
    observed_path: str | None = None
    restricted: bool = False
    policy_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", require_identifier(self.evidence_id, "evidence_id"))
        object.__setattr__(self, "evidence_kind", require_identifier(self.evidence_kind, "evidence_kind"))
        if not isinstance(self.source_ref, SemanticRef):
            raise DNAValidationError("source_ref must be a SemanticRef")
        if self.observed_path is not None:
            object.__setattr__(self, "observed_path", require_semantic_path(self.observed_path))
        if not isinstance(self.restricted, bool):
            raise DNAValidationError("restricted must be a bool")
        object.__setattr__(self, "policy_refs", require_refs(self.policy_refs, "policy_refs"))
        if self.restricted and not any(ref.owner_module in {"m53", "m54"} for ref in self.policy_refs):
            raise DNAAdmissionError("restricted identity evidence requires a minimized M53/M54 policy reference")


@dataclass(frozen=True)
class TraitSchemaRegistry(CanonicalRecord):
    registered: tuple[TraitSchemaRef, ...]
    registry_version: str = "m05-trait-registry-v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "registry_version", require_version(self.registry_version, "registry_version"))
        entries = tuple(self.registered)
        if any(not isinstance(item, TraitSchemaRef) for item in entries):
            raise DNAValidationError("registered entries must be TraitSchemaRef values")
        keys = [(item.family, item.version) for item in entries]
        if len(keys) != len(set(keys)):
            raise DNAValidationError("trait schema registry contains duplicate family/version refs")
        object.__setattr__(self, "registered", tuple(sorted(entries)))

    def validate(self, trait: DNATrait) -> None:
        if (trait.schema_ref.family, trait.schema_ref.version) in {
            (item.family, item.version) for item in self.registered
        }:
            return
        if trait.schema_ref.mandatory:
            raise DNAAdmissionError(
                f"unknown mandatory trait schema {trait.schema_ref.family}@{trait.schema_ref.version}"
            )
        if trait.opaque_preservation_policy_ref is None:
            raise DNAAdmissionError(
                f"unknown optional trait schema {trait.schema_ref.family} requires an explicit preservation policy"
            )


_CORE_SCHEMA_FAMILIES = (
    "identity.core",
    "identity.structure",
    "identity.appearance",
    "identity.behavior",
    "identity.relationship",
    "character.identity",
    "character.anatomy",
    "character.face",
    "character.body",
    "character.hair",
    "character.signature",
    "character.costume_binding",
    "character.relationship_role",
    "creature.taxonomy",
    "creature.morphology",
    "creature.anatomy",
    "creature.appendage",
    "creature.surface",
    "creature.pattern",
    "creature.signature",
    "object.form",
    "object.part",
    "object.function",
    "object.articulation",
    "object.surface_identity",
    "object.signature",
    "product.model",
    "product.geometry",
    "product.variant",
    "product.packaging",
    "product.marking",
    "product.dimension",
    "product.external_identifier",
    "environment.layout",
    "environment.zone",
    "environment.landmark",
    "environment.architecture",
    "environment.signature",
    "environment.ecology",
    "environment.context_boundary",
    "scene.identity",
)
DEFAULT_TRAIT_SCHEMAS = TraitSchemaRegistry(
    tuple(TraitSchemaRef(family, "1", mandatory=True) for family in _CORE_SCHEMA_FAMILIES)
)
