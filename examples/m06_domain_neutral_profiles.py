"""Exercise one M06 kernel across eight production-state domains without media execution."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass

from iris_project_os.build import BuildPlan, BuildState, BuildStep, WorkDisposition as M02WorkDisposition
from iris_project_os.identity import EntityKind, ExternalRef
from iris_project_os.reuse import CacheKey, CacheLayer, OriginClass, ReuseClass, ReuseReceipt
from iris_project_os.versions import ComponentVersion
from iris_project_os.graph import DependencySlice as M02DependencySlice

from iris_production_state.dependencies import FingerprintDimension, OperationalDependencyObservation, analyze_impact, build_fingerprint, build_reverse_index
from iris_production_state.enums import DependencyKind, FingerprintScope, ImpactState, IndexState, MaterialityState, ReproducibilityClass, WorkDisposition
from iris_production_state.reconstruction import require_bounded_reproducibility
from iris_production_state.regeneration import RebuildBoundary, ReuseEvidenceDimension, ReuseEvidenceState, ReuseProof, MixedReconstructionReceipt, admit_reuse
from iris_production_state.revisions import MaterializationRef, OperationalRevisionRef, digest_bytes, verify_digest


@dataclass(frozen=True)
class ProfileResult:
    profile_id: str
    dimensions: tuple[str, ...]
    dependency_fingerprint: str
    impact_state: str | None
    disposition: str
    reproducibility_class: str | None


def _external(reference: str, kind: EntityKind = EntityKind.ARTIFACT) -> ExternalRef:
    return ExternalRef(kind, reference, version="1.0")


def _revision(profile_id: str) -> OperationalRevisionRef:
    revision_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"iris-m06-profile:{profile_id}"))
    from iris_project_os.identity import RevisionRef

    semantic_type = ExternalRef(EntityKind.SEMANTIC_TYPE, f"profile-type-{profile_id}", version="1.0")
    semantic_revision = RevisionRef(revision_uuid, str(uuid.uuid5(uuid.NAMESPACE_URL, f"iris-m06-source:{profile_id}")), hashlib.sha256(profile_id.encode()).hexdigest(), semantic_type)
    return OperationalRevisionRef(f"m06-{profile_id}", semantic_revision)


def _build_plan(profile_id: str) -> BuildPlan:
    plan_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"iris-m06-build:{profile_id}"))
    node_id = f"{profile_id}.reuse"
    build_fingerprint = hashlib.sha256(f"build:{profile_id}".encode()).hexdigest()
    key = CacheKey.of(node_id, build_fingerprint=build_fingerprint, layer=CacheLayer.FINAL)
    output_digest = hashlib.sha256(f"output:{profile_id}".encode()).hexdigest()
    receipt_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"iris-m06-reuse-receipt:{profile_id}"))
    receipt = ReuseReceipt(
        receipt_id,
        node_id,
        ReuseClass.EXACT_REUSE,
        ExternalRef(EntityKind.REVISION, f"reuse-source-{profile_id}", version="1.0"),
        key,
        ComponentVersion("m02.synthetic", "1.0.0"),
        ExternalRef(EntityKind.POLICY, f"reuse-policy-{profile_id}", version="1.0"),
        OriginClass.TRUSTED_WORKER,
        "M02 synthetic profile records exact reuse evidence",
        observed_digest=output_digest,
        result_digest=output_digest,
        admitted_at_ms=1,
    )
    reuse_step = BuildStep(
        node_id,
        BuildState.CACHED_ELIGIBLE,
        M02WorkDisposition.REUSE,
        reasons=("M02 reuse receipt is present",),
        key=key,
        receipt=receipt,
        outputs=("reused-segment",),
    )
    repair_node_id = f"{profile_id}.repair"
    repair_step = BuildStep(
        repair_node_id,
        BuildState.DIRTY,
        M02WorkDisposition.REPAIR,
        reasons=("one video shot changed",),
        outputs=("rebuilt-segment",),
        slice=M02DependencySlice("shot", ("shot-2",)),
    )
    return BuildPlan(
        plan_id,
        f"graph-{profile_id}",
        ExternalRef(EntityKind.REVISION, f"base-{profile_id}", version="1.0"),
        ExternalRef(EntityKind.REVISION, f"target-{profile_id}", version="1.0"),
        steps=(reuse_step, repair_step),
    )


def _dimensions(profile_id: str, facets: tuple[str, ...], *, non_material: frozenset[str] = frozenset()) -> tuple[FingerprintDimension, ...]:
    result: list[FingerprintDimension] = []
    for facet in facets:
        value = facet.encode("utf-8")
        is_non_material = facet in non_material
        result.append(
            FingerprintDimension(
                _external(f"{profile_id}:{facet}"),
                facet,
                MaterialityState.NON_MATERIAL if is_non_material else MaterialityState.MATERIAL,
                None if is_non_material else digest_bytes(value),
                mandatory=not is_non_material,
            )
        )
    return tuple(result)


def run_synthetic_profiles() -> tuple[ProfileResult, ...]:
    results: list[ProfileResult] = []

    profiles = (
        ("image-partial-repair-lineage", ("pixels", "mask", "color-profile"), frozenset()),
        ("3d-mesh-material-lod", ("mesh", "material", "lod"), frozenset()),
        ("video-mixed-rebuilt-reused-segments", ("shot-1", "shot-2", "sound-bed"), frozenset()),
        ("audio-voice-music", ("voice", "music", "mix"), frozenset()),
        ("metadata-only-canon-dependent", ("canon-ref", "metadata"), frozenset()),
        ("stochastic-production", ("seed", "sampler", "model"), frozenset()),
        ("retained-materialization-restoration", ("retained-object",), frozenset()),
        ("release-archive-rollback-cleanup", ("snapshot", "master", "retention"), frozenset()),
    )

    for profile_id, facets, non_material in profiles:
        dimensions = _dimensions(profile_id, facets, non_material=non_material)
        fingerprint = build_fingerprint(dimensions, FingerprintScope.FULL_CAUSAL)
        impact_state: str | None = None
        disposition = WorkDisposition.REBUILD_FULL_TARGET.value
        repro: str | None = None

        if profile_id == "image-partial-repair-lineage":
            source = dimensions[1].dependency_ref
            consumer = _revision(profile_id)
            observation = OperationalDependencyObservation(consumer, source, DependencyKind.REQUIRED, MaterialityState.MATERIAL, "mask", _external("image-observation", EntityKind.EVIDENCE), 1)
            index = build_reverse_index(
                "profile-image-index",
                "image-epoch-1",
                (observation,),
                state=IndexState.COMPLETE_FRESH,
                completeness_evidence_ref=_external("image-index-closure", EntityKind.EVIDENCE),
            )
            impact = analyze_impact(source, index, analyzed_at_ms=2)
            impact_state = impact.state.value
            if impact.state is not ImpactState.AFFECTED:
                raise AssertionError("image partial repair profile did not expose its affected consumer")
            disposition = WorkDisposition.REBUILD_PARTIAL.value

        elif profile_id == "video-mixed-rebuilt-reused-segments":
            plan = _build_plan(profile_id)
            reused = _revision(f"{profile_id}-reused-segment")
            rebuilt = _revision(f"{profile_id}-rebuilt-segment")
            target = _revision(f"{profile_id}-new-timeline")
            mat = MaterializationRef(f"{profile_id}-mat", reused, digest_bytes(f"output:{profile_id}".encode()), "video/segment")
            proof = ReuseProof(
                reused,
                mat,
                fingerprint,
                plan,
                f"{profile_id}.reuse",
                tuple(ReuseEvidenceDimension(item.key, ReuseEvidenceState.VERIFIED, _external(f"segment-proof-{index}", EntityKind.EVIDENCE)) for index, item in enumerate(fingerprint.dimensions)),
            )
            reused_receipt = admit_reuse(proof, receipt_id=f"reuse-{profile_id}", decision_id=f"decision-{profile_id}", admitted_at_ms=3)
            repair_slice = next(step.slice for step in plan.steps if step.node_id == f"{profile_id}.repair")
            boundary = RebuildBoundary(f"boundary-{profile_id}", plan, f"{profile_id}.repair", repair_slice, ("shot:shot-2",), "timeline-compose", "1.0", _external("identity-guard", EntityKind.POLICY), _external("quality-obligation", EntityKind.QUALITY_DECISION))
            MixedReconstructionReceipt(
                f"mixed-{profile_id}", target, (rebuilt,), (reused,), (reused_receipt,), boundary, "1.0",
                boundary.protected_identity_ref, boundary.protected_quality_ref, 4,
            )
            disposition = WorkDisposition.REBUILD_PARTIAL.value

        elif profile_id == "stochastic-production":
            require_bounded_reproducibility(ReproducibilityClass.STOCHASTIC_REEXECUTABLE, ReproducibilityClass.STOCHASTIC_REEXECUTABLE)
            repro = ReproducibilityClass.STOCHASTIC_REEXECUTABLE.value

        elif profile_id == "retained-materialization-restoration":
            revision = _revision(profile_id)
            material = MaterializationRef(f"{profile_id}-materialization", revision, digest_bytes(b"retained bytes"), "application/octet-stream")
            if not verify_digest(b"retained bytes", material.content_digest):
                raise AssertionError("retained restoration integrity verification failed")
            repro = ReproducibilityClass.EXACT_BYTES.value
            disposition = WorkDisposition.VERIFY_ONLY.value

        results.append(ProfileResult(profile_id, facets, fingerprint.digest, impact_state, disposition, repro))

    if len(results) != 8 or len({result.profile_id for result in results}) != 8:
        raise AssertionError("M06 domain-neutral harness must run eight distinct profiles")
    return tuple(results)


def main() -> None:
    print(json.dumps([result.__dict__ for result in run_synthetic_profiles()], ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
