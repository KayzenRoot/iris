"""Run seven synthetic domains through one provider-neutral M04 fixture path."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from iris_intent.identity import RefKind, SemanticRef

from iris_multimodal_ir import (
    CONTRACT_VERSION,
    CORE_SCHEMA_VERSION,
    TRANSPORT_VERSION,
    ContainmentEdge,
    CoordinateFrameIR,
    EntityIR,
    GeometryIR,
    IRDocumentEnvelope,
    IRNodeRef,
    IRRevision,
    MultimodalIRDocument,
    NodeKind,
    QuantityDimension,
    QuantityIR,
    SceneIR,
    SpatialReferenceIR,
    Traceability,
    canonical_digest,
    content_digest,
    deserialize_envelope,
    serialize_envelope,
    structural_fingerprint,
    validate_envelope,
)


@dataclass(frozen=True)
class SyntheticDomainProfile:
    profile_id: str
    semantic_statement: str


SYNTHETIC_DOMAINS = (
    SyntheticDomainProfile("logo.brand.web", "structured logo and brand scene"),
    SyntheticDomainProfile("product.photography", "product image photography setup"),
    SyntheticDomainProfile("nerim.isometric.game", "isometric 3D game asset and scene"),
    SyntheticDomainProfile("film.commercial.sequence", "multi-shot film and commercial sequence"),
    SyntheticDomainProfile("corporate.spokesperson", "persistent spokesperson representation"),
    SyntheticDomainProfile("voice.narration.music", "voice, narration, music and audio production"),
    SyntheticDomainProfile("mixed.multimodal.scene", "visual, motion, audio and narrative bindings"),
)


def build_synthetic_revision(profile: SyntheticDomainProfile) -> IRRevision:
    """Use the same record constructors and graph shape for every profile."""
    document_id = "synthetic.m04.document"
    scene_ref = IRNodeRef(document_id, "scene.main")
    entity_ref = IRNodeRef(document_id, "entity.main")
    geometry_ref = IRNodeRef(document_id, "geometry.main")
    statement_ref = SemanticRef(
        RefKind.STATEMENT.value, f"synthetic.{profile.profile_id}", version="1",
        content_digest=content_digest(profile.semantic_statement),
    )
    policy_ref = SemanticRef(RefKind.POLICY.value, "synthetic.policy", version="1", content_digest=content_digest("synthetic.policy"))
    trace = Traceability(source_refs=(statement_ref,), policy_refs=(policy_ref,))
    entity = EntityIR(
        ref=entity_ref, kind=NodeKind.ENTITY, trace=trace,
        attributes={"domain_profile": profile.profile_id, "semantic_statement": profile.semantic_statement},
    )
    geometry = GeometryIR(
        ref=geometry_ref, kind=NodeKind.GEOMETRY, trace=trace,
        geometry_kind="generic", coordinate_frame_id="world",
    )
    scene = SceneIR(
        ref=scene_ref, kind=NodeKind.SCENE, trace=trace,
        root_node_refs=(entity_ref,),
    )
    spatial_reference = SpatialReferenceIR("world", "m")
    origin = tuple(QuantityIR(0, "m", QuantityDimension.LENGTH) for _ in range(3))
    coordinate_frame = CoordinateFrameIR("world", spatial_reference.reference_id, origin=origin)
    return IRRevision(
        revision_id="synthetic.revision", scene=scene, nodes=(entity, geometry),
        containment=(ContainmentEdge(entity_ref, geometry_ref, "synthetic.entity.geometry"),),
        source_refs=(statement_ref,), policy_refs=(policy_ref,),
        spatial_references=(spatial_reference,), coordinate_frames=(coordinate_frame,),
    )


def run_synthetic_profiles() -> dict[str, Any]:
    runs = []
    structural_digests = set()
    api_signatures = set()
    for profile in SYNTHETIC_DOMAINS:
        revision = build_synthetic_revision(profile)
        envelope = IRDocumentEnvelope(MultimodalIRDocument("synthetic.m04.document", (revision,)))
        encoded = serialize_envelope(envelope)
        decoded = deserialize_envelope(encoded)
        report = validate_envelope(decoded)
        if not report.valid or serialize_envelope(decoded) != encoded:
            raise RuntimeError(f"synthetic profile failed deterministic M04 validation: {profile.profile_id}")
        structural = structural_fingerprint(revision)
        structural_digests.add(structural.digest)
        api_signatures.add(tuple(sorted(field.name for field in revision.__dataclass_fields__.values())))
        runs.append({
            "profile": profile.profile_id,
            "revisionDigest": revision.revision_digest,
            "canonicalEnvelopeDigest": canonical_digest(decoded),
            "transportBytes": len(encoded),
            "validation": "PASS",
            "roundTrip": "PASS",
        })
    if len(runs) != 7 or len(structural_digests) != 1 or len(api_signatures) != 1:
        raise RuntimeError("synthetic domains diverged from the shared M04 kernel surface")
    return {
        "contractVersion": CONTRACT_VERSION,
        "coreSchemaVersion": CORE_SCHEMA_VERSION,
        "transportVersion": TRANSPORT_VERSION,
        "kernelPackage": "iris_multimodal_ir",
        "sharedStructuralFingerprint": next(iter(structural_digests)),
        "profileSpecificKernelBranches": 0,
        "domains": runs,
    }


if __name__ == "__main__":
    print(json.dumps(run_synthetic_profiles(), sort_keys=True, indent=2))
