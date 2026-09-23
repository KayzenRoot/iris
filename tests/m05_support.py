"""Small deterministic fixtures shared by the focused M05 contract tests."""

from __future__ import annotations

from iris_asset_dna.base import SemanticRef
from iris_asset_dna.enums import DNAFamily, DNAIdentityLevel, TraitApplicability, TraitCriticality, TraitMutability
from iris_asset_dna.identity import AssetDNAIdentity, DNAEnvelope, DNARevision
from iris_asset_dna.packages import DNAPackageEntry, ReusableDNAPackageManifest
from iris_asset_dna.traits import DNATrait, TraitSchemaRef


def ref(owner: str, family: str, ref_id: str, *, version: str = "1", revision_id: str | None = None) -> SemanticRef:
    return SemanticRef(owner, family, ref_id, version, revision_id=revision_id)


PROVENANCE = ref("m53", "provenance.record", "fixture-source")
POLICY = ref("m05", "identity.policy", "fixture-policy")
AUTHORITY = ref("m05", "identity.authority", "fixture-authority")
EVIDENCE = ref("m01", "quality.evidence", "fixture-evidence")


def trait(
    path: str = "identity.signature",
    value: object = "blue-mark",
    *,
    schema_family: str = "identity.appearance",
    criticality: TraitCriticality = TraitCriticality.IDENTITY_DEFINING,
    mutability: TraitMutability = TraitMutability.IMMUTABLE,
    applicability: TraitApplicability = TraitApplicability.PRESENT,
    mandatory_schema: bool = True,
    opaque_policy: SemanticRef | None = None,
) -> DNATrait:
    return DNATrait(
        path,
        TraitSchemaRef(schema_family, "1", mandatory_schema),
        criticality,
        mutability,
        applicability,
        value if applicability is TraitApplicability.PRESENT else None,
        provenance_refs=(PROVENANCE,),
        policy_refs=(POLICY,),
        opaque_preservation_policy_ref=opaque_policy,
    )


def revision(
    dna_id: str = "dna-fixture-a",
    revision_id: str = "r1",
    revision_number: int = 1,
    *,
    family: DNAFamily = DNAFamily.GENERIC,
    identity_level: DNAIdentityLevel = DNAIdentityLevel.INDIVIDUAL,
    traits: tuple[DNATrait, ...] | None = None,
    schema_version: str = "iris-m05-core-v1",
    parent_revision_refs: tuple = (),
    anchor_refs: tuple[SemanticRef, ...] = (),
    component_refs: tuple[SemanticRef, ...] = (),
    domain_link_refs: tuple[SemanticRef, ...] = (),
    evidence_refs: tuple[SemanticRef, ...] = (),
    display_metadata: object = None,
) -> DNARevision:
    return DNARevision(
        dna_id,
        revision_id,
        revision_number,
        family,
        identity_level,
        traits if traits is not None else (trait(),),
        schema_version=schema_version,
        parent_revision_refs=parent_revision_refs,
        anchor_refs=anchor_refs,
        component_refs=component_refs,
        domain_link_refs=domain_link_refs,
        provenance_refs=(PROVENANCE,),
        policy_refs=(POLICY,),
        rights_privacy_refs=(ref("m53", "rights.clearance", "fixture-rights"),),
        evidence_refs=evidence_refs,
        display_metadata=display_metadata,
    )


def envelope(*revisions: DNARevision, head_revision_id: str | None = None) -> DNAEnvelope:
    if not revisions:
        revisions = (revision(),)
    first = revisions[0]
    identity = AssetDNAIdentity(
        first.dna_id,
        first.family.value.lower(),
        first.family,
        provenance_refs=(PROVENANCE,),
        policy_refs=(POLICY,),
        rights_privacy_refs=(ref("m53", "rights.clearance", "fixture-rights"),),
    )
    return DNAEnvelope(identity, tuple(revisions), head_revision_id or max(revisions, key=lambda item: item.revision_number).revision_id)


def package_manifest(subject: DNARevision, *, package_id: str = "fixture-package", dependencies=(), extensions=(), portability=None):
    from iris_asset_dna.enums import PortabilityLevel

    entry = DNAPackageEntry(subject.dna_id, subject.ref, subject.family, subject.semantic_digest)
    return ReusableDNAPackageManifest(
        package_id,
        "1.0.0",
        portability or PortabilityLevel.PORTABLE_CANONICAL,
        (entry,),
        tuple(dependencies),
        (),
        (),
        (ref("m53", "rights.clearance", "fixture-rights"),),
        (PROVENANCE,),
        (ref("m54", "security.classification", "fixture-security"),),
        (),
        metadata={"profile": "domain-neutral"},
        extensions=tuple(extensions),
    )
