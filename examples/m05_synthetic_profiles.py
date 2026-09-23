"""Run eight domain-neutral profiles through one M05 subject builder and validator."""

from __future__ import annotations

import json
from dataclasses import dataclass

from iris_asset_dna.anchors import DNAProjectionContract, project_revision
from iris_asset_dna.base import SemanticRef
from iris_asset_dna.cross_modal import (
    BrandDNALink,
    IdentityRoleSlot,
    LinkedDomainDNARef,
    MotionDNALink,
    SceneIdentityDNA,
    SceneIdentityMember,
    VoiceDNALink,
    validate_scene_identity,
)
from iris_asset_dna.enums import (
    DNAFamily,
    DNAIdentityLevel,
    LinkRequirement,
    PortabilityLevel,
    TraitApplicability,
    TraitCriticality,
    TraitMutability,
)
from iris_asset_dna.families import DNAFamilyProfile, ProductIdentityRelation, validate_family_profile
from iris_asset_dna.identity import AssetDNAIdentity, DNARevision, validate_revision
from iris_asset_dna.packages import conform_package, project_package_interface
from iris_asset_dna.traits import DNATrait, TraitSchemaRef
from iris_asset_dna.versions import CONTRACT_VERSION, content_digest


PROVENANCE = SemanticRef("m53", "provenance.record", "synthetic-profile-source", "1")
POLICY = SemanticRef("m05", "identity.policy", "synthetic-profile-policy", "1")


@dataclass(frozen=True)
class ProfileInput:
    profile_id: str
    dna_id: str
    family: DNAFamily
    identity_level: DNAIdentityLevel
    traits: tuple[tuple[str, str, str, TraitCriticality, TraitMutability], ...]
    domain_refs: tuple[SemanticRef, ...] = ()


@dataclass(frozen=True)
class ProfileResult:
    profile_id: str
    revisions: tuple[DNARevision, ...]
    contextual_refs: tuple[SemanticRef, ...] = ()
    projected_digest: str | None = None
    package_conformant: bool | None = None
    product_relations: tuple[ProductIdentityRelation, ...] = ()


def build_subject(profile: ProfileInput) -> tuple[AssetDNAIdentity, DNARevision]:
    """Same construction path for all profiles; profile_id is descriptive only."""
    traits = tuple(
        DNATrait(
            path,
            TraitSchemaRef(schema_family, "1"),
            criticality,
            mutability,
            TraitApplicability.PRESENT,
            value,
            provenance_refs=(PROVENANCE,),
            policy_refs=(POLICY,),
        )
        for path, value, schema_family, criticality, mutability in profile.traits
    )
    identity = AssetDNAIdentity(
        profile.dna_id,
        profile.family.value.lower(),
        profile.family,
        provenance_refs=(PROVENANCE,),
        policy_refs=(POLICY,),
        rights_privacy_refs=(SemanticRef("m53", "rights.clearance", f"rights-{profile.profile_id}", "1"),),
    )
    revision = DNARevision(
        profile.dna_id,
        "r1",
        1,
        profile.family,
        profile.identity_level,
        traits,
        domain_link_refs=profile.domain_refs,
        provenance_refs=(PROVENANCE,),
        policy_refs=(POLICY,),
    )
    validate_revision(revision)
    return identity, revision


def run_synthetic_profiles() -> tuple[ProfileResult, ...]:
    human = ProfileInput(
        "corporate.spokesperson", "dna-human-spokesperson", DNAFamily.CHARACTER, DNAIdentityLevel.INDIVIDUAL,
        (("character.identity.name", "Neri", "character.identity", TraitCriticality.IDENTITY_DEFINING, TraitMutability.IMMUTABLE),
         ("character.signature.mark", "amber-stripe", "character.signature", TraitCriticality.IDENTITY_SIGNIFICANT, TraitMutability.MUTABLE_WITH_EXPLICIT_POLICY)),
    )
    creature = ProfileInput(
        "asymmetric.creature", "dna-asymmetric-creature", DNAFamily.CREATURE, DNAIdentityLevel.ARCHETYPE,
        (("creature.taxonomy.kind", "glider", "creature.taxonomy", TraitCriticality.IDENTITY_DEFINING, TraitMutability.IMMUTABLE),
         ("creature.morphology.left_wing", "broad", "creature.morphology", TraitCriticality.IDENTITY_SIGNIFICANT, TraitMutability.IMMUTABLE),
         ("creature.morphology.right_wing", "narrow", "creature.morphology", TraitCriticality.IDENTITY_SIGNIFICANT, TraitMutability.IMMUTABLE)),
    )
    object_subject = ProfileInput(
        "generic.object", "dna-field-tool", DNAFamily.OBJECT, DNAIdentityLevel.INDIVIDUAL,
        (("object.form.silhouette", "compact-wrench", "object.form", TraitCriticality.IDENTITY_DEFINING, TraitMutability.IMMUTABLE),),
    )
    product_levels = tuple(
        ProfileInput(
            f"product-{level.name.lower()}",
            f"dna-product-{level.name.lower()}",
            DNAFamily.PRODUCT,
            level,
            (("product.model.shape", "cylinder-v2", "product.model", TraitCriticality.IDENTITY_DEFINING, TraitMutability.IMMUTABLE),),
        )
        for level in (
            DNAIdentityLevel.PRODUCT_FAMILY,
            DNAIdentityLevel.MODEL,
            DNAIdentityLevel.VARIANT_SKU,
            DNAIdentityLevel.PACKAGE_VARIANT,
            DNAIdentityLevel.PHYSICAL_INSTANCE,
        )
    )
    environment = ProfileInput(
        "persistent.environment", "dna-ridge-set", DNAFamily.ENVIRONMENT, DNAIdentityLevel.INDIVIDUAL,
        (("environment.landmark.tower", "east-ridge", "environment.landmark", TraitCriticality.IDENTITY_DEFINING, TraitMutability.IMMUTABLE),),
    )
    motion_ref = LinkedDomainDNARef("motion-link", "m30", "motion.dna", "motion-human", "motion-r7", "7", LinkRequirement.REQUIRED, (), ())
    voice_ref = LinkedDomainDNARef("voice-link", "m40", "voice.dna", "voice-human", "voice-r3", "3", LinkRequirement.REQUIRED, (), ())
    brand_ref = LinkedDomainDNARef("brand-link", "m46", "brand.dna", "brand-client", "brand-r2", "2", LinkRequirement.OPTIONAL, (), ())
    crossmodal = ProfileInput(
        "crossmodal.character", "dna-crossmodal-character", DNAFamily.CHARACTER, DNAIdentityLevel.INDIVIDUAL,
        human.traits,
        (motion_ref.pinned_ref, voice_ref.pinned_ref, brand_ref.pinned_ref),
    )
    scene_subject = ProfileInput(
        "scene.identity.roles", "dna-scene-identity", DNAFamily.SCENE, DNAIdentityLevel.INDIVIDUAL,
        (("scene.identity.role.lead", "character", "scene.identity", TraitCriticality.IDENTITY_SIGNIFICANT, TraitMutability.MUTABLE_WITH_EXPLICIT_POLICY),),
    )
    package_subject = ProfileInput(
        "portable.dna.package", "dna-portable-subject", DNAFamily.OBJECT, DNAIdentityLevel.INDIVIDUAL,
        (("object.form.silhouette", "portable-token", "object.form", TraitCriticality.IDENTITY_DEFINING, TraitMutability.IMMUTABLE),),
    )

    results: list[ProfileResult] = []
    for profile in (human, creature, object_subject):
        identity, revision = build_subject(profile)
        results.append(ProfileResult(profile.profile_id, (revision,)))
        if profile is human:
            family = DNAFamilyProfile("human-profile", DNAFamily.CHARACTER, "1", (DNAIdentityLevel.INDIVIDUAL,), required_namespaces=("character.identity",))
            validate_family_profile(identity, revision, family)
            projection = project_revision(revision, DNAProjectionContract("human-interface", revision.ref, ("character.identity.name",), preserved_trait_paths=("character.identity.name",)))
            results[-1] = ProfileResult(profile.profile_id, (revision,), projected_digest=projection.fingerprint)
        elif profile is creature:
            family = DNAFamilyProfile("creature-profile", DNAFamily.CREATURE, "1", (DNAIdentityLevel.ARCHETYPE,), required_namespaces=("creature.taxonomy",), allowed_component_roles=("left-wing", "right-wing"))
            validate_family_profile(identity, revision, family)

    product_subjects = tuple(build_subject(profile)[1] for profile in product_levels)
    product_ranks = tuple(profile.identity_level for profile in product_levels)
    product_relations = tuple(
        ProductIdentityRelation(
            SemanticRef("m05", "product.identity", product_subjects[index].dna_id, "1", revision_id=product_subjects[index].revision_id),
            product_ranks[index],
            SemanticRef("m05", "product.identity", product_subjects[index + 1].dna_id, "1", revision_id=product_subjects[index + 1].revision_id),
            product_ranks[index + 1],
            ("product.model.shape",),
            ("product.variant.sku",) if index < 2 else ("product.packaging.configuration",),
        )
        for index in range(len(product_subjects) - 1)
    )
    results.append(ProfileResult("product.identity.levels", product_subjects, product_relations=product_relations))

    for profile in (environment, crossmodal, scene_subject, package_subject):
        identity, revision = build_subject(profile)
        if profile is environment:
            family = DNAFamilyProfile("environment-profile", DNAFamily.ENVIRONMENT, "1", (DNAIdentityLevel.INDIVIDUAL,), required_namespaces=("environment.landmark",))
            validate_family_profile(identity, revision, family)
            contexts = (
                SemanticRef("m04", "scene.context", "daylight-state", "1"),
                SemanticRef("m04", "scene.context", "night-state", "1"),
            )
            results.append(ProfileResult(profile.profile_id, (revision,), contextual_refs=contexts))
        elif profile is crossmodal:
            MotionDNALink(motion_ref, "walk-cycle")
            VoiceDNALink(voice_ref, "narrator")
            BrandDNALink(brand_ref, "association")
            results.append(ProfileResult(profile.profile_id, (revision,)))
        elif profile is scene_subject:
            _, lead_revision = build_subject(human)
            role = IdentityRoleSlot("lead", (DNAFamily.CHARACTER,), ("character.identity.name",), 1, 1, POLICY, ("understudy",))
            scene = SceneIdentityDNA(revision.ref, (role,), (SceneIdentityMember("lead", lead_revision.ref, DNAFamily.CHARACTER, "understudy"),), scene_ir_projection_ref=SemanticRef("m04", "scene.ir.snapshot", "scene-snapshot", "1"))
            validate_scene_identity(scene, (revision, lead_revision))
            results.append(ProfileResult(profile.profile_id, (revision, lead_revision), contextual_refs=(scene.scene_ir_projection_ref,)))
        else:
            manifest = _portable_manifest(revision)
            report = conform_package(manifest, (revision,), ())
            projection = project_package_interface(manifest)
            results.append(ProfileResult(profile.profile_id, (revision,), projected_digest=content_digest(projection), package_conformant=report.valid))

    return tuple(results)


def _portable_manifest(revision: DNARevision):
    from iris_asset_dna.packages import DNAPackageEntry, ReusableDNAPackageManifest

    return ReusableDNAPackageManifest(
        "portable-fixture-package",
        "1.0.0",
        PortabilityLevel.RESTRICTED_REFERENCE,
        (DNAPackageEntry(revision.dna_id, revision.ref, revision.family, revision.semantic_digest),),
        (), (), (),
        (SemanticRef("m53", "rights.clearance", "portable-rights", "1"),),
        (PROVENANCE,),
        (SemanticRef("m54", "security.classification", "portable-security", "1"),),
        (),
        metadata={"portable": True, "executable_payload": False},
    )


def public_summary(results: tuple[ProfileResult, ...] | None = None) -> dict[str, object]:
    profiles = results if results is not None else run_synthetic_profiles()
    return {
        "contract_version": CONTRACT_VERSION,
        "profile_count": len(profiles),
        "profile_ids": [item.profile_id for item in profiles],
        "subjects_per_profile": {item.profile_id: len(item.revisions) for item in profiles},
        "same_builder": True,
        "package_conformance": {item.profile_id: item.package_conformant for item in profiles if item.package_conformant is not None},
    }


if __name__ == "__main__":
    print(json.dumps(public_summary(), sort_keys=True, indent=2))
