"""One typed identity core with family profiles and persistent component semantics."""

from __future__ import annotations

from dataclasses import dataclass

from .base import CanonicalRecord, SemanticRef, require_refs
from .enums import DNAFamily, DNAIdentityLevel
from .errors import DNAAdmissionError, DNAIntegrityError, DNAValidationError
from .identity import AssetDNAIdentity, DNARevision
from .traits import DNATrait
from .versions import require_identifier, require_semantic_path, require_text, require_version

__all__ = [
    "DNAFamilyProfile",
    "DNATraitBundle",
    "DNAComponentIdentity",
    "ComponentTransition",
    "validate_component_transition",
    "CharacterDNA",
    "CreatureDNA",
    "ObjectDNA",
    "ProductDNA",
    "EnvironmentDNA",
    "PersistentAppearanceTrait",
    "ContextualAppearanceState",
    "AppearanceObservation",
    "ProductIdentityRelation",
    "validate_family_profile",
]


@dataclass(frozen=True)
class DNAFamilyProfile(CanonicalRecord):
    profile_id: str
    family: DNAFamily
    version: str
    supported_levels: tuple[DNAIdentityLevel, ...]
    required_namespaces: tuple[str, ...] = ()
    optional_namespaces: tuple[str, ...] = ()
    allowed_component_roles: tuple[str, ...] = ()
    extension_namespaces: tuple[str, ...] = ()
    projection_obligations: tuple[str, ...] = ()
    compatibility_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "profile_id", require_identifier(self.profile_id, "profile_id"))
        if not isinstance(self.family, DNAFamily):
            object.__setattr__(self, "family", DNAFamily(self.family))
        object.__setattr__(self, "version", require_version(self.version, "version"))
        levels = tuple(
            item if isinstance(item, DNAIdentityLevel) else DNAIdentityLevel(item)
            for item in self.supported_levels
        )
        if not levels or len(levels) != len(set(levels)):
            raise DNAValidationError("supported_levels must be non-empty and unique")
        object.__setattr__(self, "supported_levels", tuple(sorted(levels, key=lambda item: item.value)))
        for name in ("required_namespaces", "optional_namespaces", "extension_namespaces"):
            values = tuple(sorted({require_identifier(item, f"{name}[]") for item in getattr(self, name)}))
            object.__setattr__(self, name, values)
        if set(self.required_namespaces) & set(self.optional_namespaces):
            raise DNAValidationError("required and optional family namespaces must be disjoint")
        roles = tuple(sorted({require_identifier(item, "allowed_component_roles[]") for item in self.allowed_component_roles}))
        object.__setattr__(self, "allowed_component_roles", roles)
        obligations = tuple(sorted({require_identifier(item, "projection_obligations[]") for item in self.projection_obligations}))
        object.__setattr__(self, "projection_obligations", obligations)
        object.__setattr__(self, "compatibility_refs", require_refs(self.compatibility_refs, "compatibility_refs"))

    @property
    def reference(self) -> SemanticRef:
        return SemanticRef("m05", "family.profile", self.profile_id, self.version)


@dataclass(frozen=True)
class DNATraitBundle(CanonicalRecord):
    bundle_id: str
    dna_id: str
    profile_ref: SemanticRef
    traits: tuple[DNATrait, ...]
    required_paths: tuple[str, ...]
    optional_paths: tuple[str, ...] = ()
    provenance_refs: tuple[SemanticRef, ...] = ()
    policy_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "bundle_id", require_identifier(self.bundle_id, "bundle_id"))
        object.__setattr__(self, "dna_id", require_identifier(self.dna_id, "dna_id"))
        if not isinstance(self.profile_ref, SemanticRef):
            raise DNAValidationError("profile_ref must be a SemanticRef")
        traits = tuple(self.traits)
        if any(not isinstance(item, DNATrait) for item in traits):
            raise DNAValidationError("traits must contain DNATrait values")
        paths = [item.path for item in traits]
        if len(paths) != len(set(paths)):
            raise DNAIntegrityError("trait bundle contains duplicate paths")
        object.__setattr__(self, "traits", tuple(sorted(traits, key=lambda item: item.path)))
        required = tuple(sorted({require_semantic_path(item) for item in self.required_paths}))
        optional = tuple(sorted({require_semantic_path(item) for item in self.optional_paths}))
        if set(required) & set(optional):
            raise DNAValidationError("required and optional trait bundle paths must be disjoint")
        if not set(required + optional) <= set(paths):
            raise DNAAdmissionError("trait bundle declarations must refer to a bundled trait")
        object.__setattr__(self, "required_paths", required)
        object.__setattr__(self, "optional_paths", optional)
        object.__setattr__(self, "provenance_refs", require_refs(self.provenance_refs, "provenance_refs"))
        object.__setattr__(self, "policy_refs", require_refs(self.policy_refs, "policy_refs"))
        if any(ref.owner_module != "m53" for ref in self.provenance_refs):
            raise DNAAdmissionError("M53 remains the provenance authority for family trait bundles")
        if self.profile_ref.owner_module != "m05" or self.profile_ref.family != "family.profile":
            raise DNAAdmissionError("trait bundle profile must remain under M05 family identity authority")


@dataclass(frozen=True)
class DNAComponentIdentity(CanonicalRecord):
    component_id: str
    dna_id: str
    role: str
    family: DNAFamily
    version: str
    continuity_paths: tuple[str, ...]
    parent_component_refs: tuple[SemanticRef, ...] = ()
    source_component_refs: tuple[SemanticRef, ...] = ()
    is_derived_proxy: bool = False
    provenance_refs: tuple[SemanticRef, ...] = ()
    policy_refs: tuple[SemanticRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "component_id", require_identifier(self.component_id, "component_id"))
        object.__setattr__(self, "dna_id", require_identifier(self.dna_id, "dna_id"))
        object.__setattr__(self, "role", require_identifier(self.role, "role"))
        if not isinstance(self.family, DNAFamily):
            object.__setattr__(self, "family", DNAFamily(self.family))
        object.__setattr__(self, "version", require_version(self.version, "version"))
        paths = tuple(sorted({require_semantic_path(item) for item in self.continuity_paths}))
        object.__setattr__(self, "continuity_paths", paths)
        for name in ("parent_component_refs", "source_component_refs", "provenance_refs", "policy_refs"):
            object.__setattr__(self, name, require_refs(getattr(self, name), name))
        if not isinstance(self.is_derived_proxy, bool):
            raise DNAValidationError("is_derived_proxy must be a bool")
        if not self.provenance_refs and not self.policy_refs:
            raise DNAAdmissionError("persistent component identity needs provenance or policy reachability")
        if any(ref.owner_module != "m53" for ref in self.provenance_refs):
            raise DNAAdmissionError("M53 remains the provenance authority for persistent components")
        if self.is_derived_proxy and (not self.source_component_refs or not self.policy_refs):
            raise DNAAdmissionError("a derived proxy needs explicit source components and policy; it is never a new identity by default")

    @property
    def reference(self) -> SemanticRef:
        return SemanticRef("m05", "component.identity", self.component_id, self.version)


@dataclass(frozen=True)
class ComponentTransition(CanonicalRecord):
    transition_id: str
    kind: str
    source_component_refs: tuple[SemanticRef, ...]
    target_component_refs: tuple[SemanticRef, ...]
    authority_ref: SemanticRef
    policy_ref: SemanticRef
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "transition_id", require_identifier(self.transition_id, "transition_id"))
        kind = require_text(self.kind, "kind", maximum=32).upper()
        if kind not in {"REPLACE", "SPLIT", "MERGE"}:
            raise DNAValidationError("component transition kind must be REPLACE, SPLIT, or MERGE")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "source_component_refs", require_refs(self.source_component_refs, "source_component_refs"))
        object.__setattr__(self, "target_component_refs", require_refs(self.target_component_refs, "target_component_refs"))
        if not self.source_component_refs or not self.target_component_refs:
            raise DNAAdmissionError("component transitions preserve explicit source and target history")
        if not isinstance(self.authority_ref, SemanticRef) or not isinstance(self.policy_ref, SemanticRef):
            raise DNAAdmissionError("component transitions require explicit authority and policy refs")
        object.__setattr__(self, "reason", require_text(self.reason, "reason", maximum=2048))


def validate_component_transition(transition: ComponentTransition) -> None:
    if not isinstance(transition, ComponentTransition):
        raise DNAValidationError("transition must be a ComponentTransition")
    if set(transition.source_component_refs) & set(transition.target_component_refs):
        raise DNAAdmissionError("component transitions must declare governed target identities explicitly")
    counts = (len(transition.source_component_refs), len(transition.target_component_refs))
    expected = {"REPLACE": (1, 1), "SPLIT": (1, None), "MERGE": (None, 1)}[transition.kind]
    if transition.kind == "REPLACE" and counts != expected:
        raise DNAAdmissionError("REPLACE requires one source and one target component")
    if transition.kind == "SPLIT" and (counts[0] != 1 or counts[1] < 2):
        raise DNAAdmissionError("SPLIT requires one source and at least two target components")
    if transition.kind == "MERGE" and (counts[0] < 2 or counts[1] != 1):
        raise DNAAdmissionError("MERGE requires at least two source components and one target component")


def _validate_subject(identity: AssetDNAIdentity, revision: DNARevision, profile: DNAFamilyProfile, family: DNAFamily) -> None:
    if not all((isinstance(identity, AssetDNAIdentity), isinstance(revision, DNARevision), isinstance(profile, DNAFamilyProfile))):
        raise DNAValidationError("typed family profile requires identity, revision and family profile records")
    if identity.dna_id != revision.dna_id or identity.family is not family or revision.family is not family:
        raise DNAIntegrityError(f"{family.value} profile must use one matching M05 identity/revision")
    if profile.family is not family or revision.identity_level not in profile.supported_levels:
        raise DNAAdmissionError("family profile does not admit this family or identity level")


def validate_family_profile(identity: AssetDNAIdentity, revision: DNARevision, profile: DNAFamilyProfile) -> None:
    if not isinstance(profile, DNAFamilyProfile):
        raise DNAValidationError("profile must be a DNAFamilyProfile")
    _validate_subject(identity, revision, profile, profile.family)
    paths = revision.trait_map()
    missing = [
        namespace for namespace in profile.required_namespaces
        if not any(path.startswith(namespace + ".") or path == namespace for path in paths)
    ]
    if missing:
        raise DNAAdmissionError(f"family profile is missing required trait namespaces: {missing}")


@dataclass(frozen=True)
class CharacterDNA(CanonicalRecord):
    identity: AssetDNAIdentity
    revision: DNARevision
    profile: DNAFamilyProfile

    def __post_init__(self) -> None:
        _validate_subject(self.identity, self.revision, self.profile, DNAFamily.CHARACTER)
        validate_family_profile(self.identity, self.revision, self.profile)


@dataclass(frozen=True)
class CreatureDNA(CanonicalRecord):
    identity: AssetDNAIdentity
    revision: DNARevision
    profile: DNAFamilyProfile

    def __post_init__(self) -> None:
        _validate_subject(self.identity, self.revision, self.profile, DNAFamily.CREATURE)
        validate_family_profile(self.identity, self.revision, self.profile)


@dataclass(frozen=True)
class ObjectDNA(CanonicalRecord):
    identity: AssetDNAIdentity
    revision: DNARevision
    profile: DNAFamilyProfile

    def __post_init__(self) -> None:
        _validate_subject(self.identity, self.revision, self.profile, DNAFamily.OBJECT)
        validate_family_profile(self.identity, self.revision, self.profile)


@dataclass(frozen=True)
class ProductDNA(CanonicalRecord):
    identity: AssetDNAIdentity
    revision: DNARevision
    profile: DNAFamilyProfile

    def __post_init__(self) -> None:
        _validate_subject(self.identity, self.revision, self.profile, DNAFamily.PRODUCT)
        validate_family_profile(self.identity, self.revision, self.profile)


@dataclass(frozen=True)
class EnvironmentDNA(CanonicalRecord):
    identity: AssetDNAIdentity
    revision: DNARevision
    profile: DNAFamilyProfile

    def __post_init__(self) -> None:
        _validate_subject(self.identity, self.revision, self.profile, DNAFamily.ENVIRONMENT)
        validate_family_profile(self.identity, self.revision, self.profile)


@dataclass(frozen=True)
class PersistentAppearanceTrait(CanonicalRecord):
    trait: DNATrait

    def __post_init__(self) -> None:
        if not isinstance(self.trait, DNATrait):
            raise DNAValidationError("trait must be a DNATrait")
        if self.trait.criticality.value in {"CONTEXTUAL", "DERIVED_EVIDENCE_ONLY"}:
            raise DNAAdmissionError("persistent appearance cannot contain contextual or evidence-only traits")
        if self.trait.mutability.value in {"CONTEXTUAL_VARIANT", "DERIVED_ONLY"}:
            raise DNAAdmissionError("contextual appearance belongs in the separate context/observation plane")


@dataclass(frozen=True)
class ContextualAppearanceState(CanonicalRecord):
    state_id: str
    context_ref: SemanticRef
    values: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "state_id", require_identifier(self.state_id, "state_id"))
        if not isinstance(self.context_ref, SemanticRef):
            raise DNAValidationError("context_ref must be a SemanticRef")
        values = tuple(sorted((require_semantic_path(path), require_identifier(value, "context value")) for path, value in self.values))
        object.__setattr__(self, "values", values)


@dataclass(frozen=True)
class AppearanceObservation(CanonicalRecord):
    observation_id: str
    evidence_ref: SemanticRef
    observed_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "observation_id", require_identifier(self.observation_id, "observation_id"))
        if not isinstance(self.evidence_ref, SemanticRef):
            raise DNAValidationError("evidence_ref must be a SemanticRef")
        object.__setattr__(self, "observed_paths", tuple(sorted({require_semantic_path(p) for p in self.observed_paths})))


@dataclass(frozen=True)
class ProductIdentityRelation(CanonicalRecord):
    parent_ref: SemanticRef
    parent_level: DNAIdentityLevel
    child_ref: SemanticRef
    child_level: DNAIdentityLevel
    inherited_paths: tuple[str, ...]
    overridden_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.parent_ref, SemanticRef) or not isinstance(self.child_ref, SemanticRef):
            raise DNAValidationError("product levels require explicit pinned identity refs")
        for name in ("parent_level", "child_level"):
            value = getattr(self, name)
            if not isinstance(value, DNAIdentityLevel):
                object.__setattr__(self, name, DNAIdentityLevel(value))
        if self.parent_level is self.child_level:
            raise DNAAdmissionError("product identity levels cannot collapse into one implicit level")
        product_rank = {
            DNAIdentityLevel.PRODUCT_FAMILY: 0,
            DNAIdentityLevel.MODEL: 1,
            DNAIdentityLevel.VARIANT_SKU: 2,
            DNAIdentityLevel.PACKAGE_VARIANT: 3,
            DNAIdentityLevel.PHYSICAL_INSTANCE: 4,
        }
        if self.parent_level in product_rank and self.child_level in product_rank and product_rank[self.child_level] <= product_rank[self.parent_level]:
            raise DNAAdmissionError("product identity relation must move to a more specific declared level")
        object.__setattr__(self, "inherited_paths", tuple(sorted({require_semantic_path(p) for p in self.inherited_paths})))
        object.__setattr__(self, "overridden_paths", tuple(sorted({require_semantic_path(p) for p in self.overridden_paths})))
        if set(self.inherited_paths) & set(self.overridden_paths):
            raise DNAValidationError("product variant paths cannot be both inherited and overridden")
