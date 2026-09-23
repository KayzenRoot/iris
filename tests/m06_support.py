"""Small exact M02/M05 fixtures shared by focused M06 tests and examples."""

from __future__ import annotations

import hashlib
import uuid

from iris_project_os.identity import EntityKind, ExternalRef, RevisionRef
from iris_project_os.build import BuildPlan

from iris_production_state.revisions import (
    ContentDigest,
    ImmutableMasterRef,
    IntegrityReceipt,
    MaterializationRef,
    MasterManifest,
    OperationalRevisionRef,
    RevisionManifest,
)
from iris_production_state.enums import IntegrityState


def external(reference: str, *, kind: EntityKind = EntityKind.EVIDENCE, version: str = "1.0") -> ExternalRef:
    return ExternalRef(kind, reference, version=version)


def semantic_revision(artifact_id: str, revision_id: str, digest: str | None = None) -> RevisionRef:
    content = digest or hashlib.sha256(f"{artifact_id}/{revision_id}".encode("utf-8")).hexdigest()
    return RevisionRef(
        str(uuid.uuid5(uuid.NAMESPACE_URL, f"iris-m06:{artifact_id}")),
        str(uuid.uuid5(uuid.NAMESPACE_URL, f"iris-m06:{revision_id}")),
        content,
        ExternalRef(EntityKind.SEMANTIC_TYPE, f"semantic-type-{artifact_id}", version="1.0"),
    )


def operational_revision(revision_id: str, source: RevisionRef | None = None) -> OperationalRevisionRef:
    return OperationalRevisionRef(revision_id, source or semantic_revision(f"artifact-{revision_id}", f"semantic-{revision_id}"))


def content_digest(data: bytes = b"iris-m06-test") -> ContentDigest:
    return ContentDigest("sha256", "1.0.0", hashlib.sha256(data).hexdigest())


def materialization(revision: OperationalRevisionRef, materialization_id: str, data: bytes = b"iris-m06-test") -> MaterializationRef:
    return MaterializationRef(materialization_id, revision, content_digest(data), "application/octet-stream")


def master_manifest(revision: OperationalRevisionRef, *, master_id: str = "master-1") -> tuple[MasterManifest, IntegrityReceipt]:
    material = materialization(revision, f"mat-{master_id}")
    semantic = revision.source_revision_ref
    revision_manifest = RevisionManifest(revision, semantic, material.content_digest, (semantic,))
    manifest = MasterManifest(
        ImmutableMasterRef(master_id, revision),
        revision_manifest,
        (material,),
        external(f"m02-admission-{master_id}"),
        external(f"m01-quality-{master_id}"),
    )
    integrity = IntegrityReceipt(material, material.content_digest, IntegrityState.VERIFIED, 100)
    return manifest, integrity


def m02_build_plan(plan_id: str = "build-plan-1") -> BuildPlan:
    return BuildPlan(
        str(uuid.uuid5(uuid.NAMESPACE_URL, f"iris-m06:{plan_id}")),
        f"graph-{plan_id}",
        ExternalRef(EntityKind.REVISION, f"base-{plan_id}", version="1.0"),
        ExternalRef(EntityKind.REVISION, f"target-{plan_id}", version="1.0"),
    )


def m02_reuse_build_plan(plan_id: str = "build-plan-reuse", *, node_id: str = "render.logo") -> BuildPlan:
    from tests import m02_kernel_support as k
    from iris_project_os.build import BuildState, BuildStep, WorkDisposition

    graph = k.bound()
    receipt = k.admitted_receipt(graph, node_id)
    step = BuildStep(
        node_id,
        BuildState.CACHED_ELIGIBLE,
        WorkDisposition.REUSE,
        reasons=("M02 admitted exact reuse evidence for M06",),
        key=receipt.key,
        receipt=receipt,
        outputs=("out",),
    )
    return BuildPlan(
        str(uuid.uuid5(uuid.NAMESPACE_URL, f"iris-m06:{plan_id}")),
        f"graph-{plan_id}",
        ExternalRef(EntityKind.REVISION, f"base-{plan_id}", version="1.0"),
        ExternalRef(EntityKind.REVISION, f"target-{plan_id}", version="1.0"),
        steps=(step,),
    )


def m02_repair_build_plan(
    plan_id: str = "build-plan-repair",
    *,
    node_id: str = "render.logo",
    axis: str = "region",
    values: tuple[str, ...] = ("left",),
) -> BuildPlan:
    from iris_project_os.build import BuildState, BuildStep, WorkDisposition
    from iris_project_os.graph import DependencySlice

    step = BuildStep(
        node_id,
        BuildState.DIRTY,
        WorkDisposition.REPAIR,
        reasons=("M02 admitted this exact repair boundary for M06",),
        outputs=("out",),
        slice=DependencySlice(axis, values),
    )
    return BuildPlan(
        str(uuid.uuid5(uuid.NAMESPACE_URL, f"iris-m06:{plan_id}")),
        f"graph-{plan_id}",
        ExternalRef(EntityKind.REVISION, f"base-{plan_id}", version="1.0"),
        ExternalRef(EntityKind.REVISION, f"target-{plan_id}", version="1.0"),
        steps=(step,),
    )
