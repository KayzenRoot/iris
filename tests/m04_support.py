"""Shared admitted M04 fixtures used by focused kernel tests and examples."""

from __future__ import annotations

from iris_intent.execution import ExecutionIntentBundle, IntentOperation, SemanticLossRule
from iris_intent.identity import RefKind, SemanticRef

from iris_multimodal_ir import (
    CoordinateFrameIR,
    EntityIR,
    GeometryIR,
    IRNodeRef,
    IRRevision,
    NodeKind,
    SceneIR,
    QuantityDimension,
    QuantityIR,
    SpatialReferenceIR,
    Traceability,
    content_digest,
)
from tests import m03_kernel_support as M03


DOCUMENT_ID = "fixture.document"
SOURCE = SemanticRef(RefKind.STATEMENT.value, "fixture.statement", version="1", content_digest=content_digest("fixture.statement"))
POLICY = SemanticRef(RefKind.POLICY.value, "fixture.policy", version="1", content_digest=content_digest("fixture.policy"))
OBLIGATION = SemanticRef(RefKind.OBLIGATION.value, "fixture.m01.obligation", version="1", content_digest=content_digest("fixture.m01.obligation"))
TYPE_REF = SemanticRef(RefKind.SEMANTIC_TYPE.value, "fixture.image", version="1", content_digest=content_digest("fixture.image"))


def trace() -> Traceability:
    return Traceability(source_refs=(SOURCE,), policy_refs=(POLICY,))


def fixture_revision(revision_id: str = "fixture.revision", *, display_name: str = "Main Scene", path_hint: str = "scenes/main", attributes: dict | None = None) -> IRRevision:
    entity_ref = IRNodeRef(DOCUMENT_ID, "fixture.entity")
    geometry_ref = IRNodeRef(DOCUMENT_ID, "fixture.geometry")
    entity = EntityIR(
        ref=entity_ref, kind=NodeKind.ENTITY, trace=trace(), display_name="Entity",
        quality_obligation_refs=(OBLIGATION,), semantic_refs=(TYPE_REF,), attributes=attributes or {"purpose": "logo"},
    )
    geometry = GeometryIR(
        ref=geometry_ref, kind=NodeKind.GEOMETRY, trace=trace(), geometry_kind="mesh",
        coordinate_frame_id="world", vertex_count=8, face_count=6,
    )
    scene = SceneIR(
        ref=IRNodeRef(DOCUMENT_ID, "fixture.scene"), kind=NodeKind.SCENE, trace=trace(),
        display_name=display_name, path_hint=path_hint, root_node_refs=(entity_ref,),
    )
    spatial_reference = SpatialReferenceIR("world", "m")
    origin = tuple(QuantityIR(0, "m", QuantityDimension.LENGTH) for _ in range(3))
    world_frame = CoordinateFrameIR("world", spatial_reference.reference_id, origin=origin)
    from iris_multimodal_ir import ContainmentEdge
    return IRRevision(
        revision_id=revision_id, scene=scene, nodes=(entity, geometry),
        containment=(ContainmentEdge(entity_ref, geometry_ref, "fixture.contains.geometry"),),
        source_refs=(SOURCE,), policy_refs=(POLICY,),
        spatial_references=(spatial_reference,), coordinate_frames=(world_frame,),
    )


def m03_bundle(*, loss_rule: SemanticLossRule | None = None) -> ExecutionIntentBundle:
    operation = IntentOperation(
        intent_operation_id="fixture.create", family="CREATE", purpose="materialize fixture scene",
        output_type_refs=(TYPE_REF,), originating_refs=(SOURCE,), required_explanation_refs=(SOURCE,),
    )
    rules = (loss_rule or SemanticLossRule(
        rule_id="fixture.lossless", item_ref=SOURCE, loss_class="LOSSLESS_REQUIRED",
        operation_ids=(operation.intent_operation_id,), source_refs=(SOURCE,),
    ),)
    return ExecutionIntentBundle(
        bundle_id="fixture.bundle", brief_ref=M03.ref(RefKind.BRIEF.value, M03.BRIEF_ID),
        revision_ref=M03.revision_ref(), intent_fingerprint_digest=M03.digest("m04.intent"),
        constraint_fingerprint_digest=M03.digest("m04.constraints"), fidelity_fingerprint_digest=M03.digest("m04.fidelity"),
        operations=(operation,), loss_rules=rules,
    )
