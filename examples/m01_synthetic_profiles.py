"""IRIS-WO-0003 synthetic profile fixtures.

These fixtures exist to prove that the M01 kernel extends to three different
creative domains without the kernel knowing any of them. Every judge and
validator here is an arithmetic stand-in: it reads numbers that the caller
already extracted, never pixels, meshes, scenes or model weights.

Nothing in this module is production quality logic. The kernel in
:mod:`iris_quality` must stay importable with this directory deleted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from iris_quality.contracts import FidelityContract, PromotionRule, QualityClass
from iris_quality.defects import Defect, DefectSeverity
from iris_quality.dimensions import DimensionAssessment, GateState, UncertaintyState
from iris_quality.evidence import EvidenceRef
from iris_quality.judging import (
    Abstention,
    JudgeRequest,
    JudgeResult,
    SubjectRef,
    ValidationCheck,
    ValidatorOutcome,
)
from iris_quality.registry import (
    DomainProfile,
    DomainProfileRegistry,
    EvaluatorDescriptor,
    EvaluatorRegistry,
    ExtensionMetadata,
    TrustTier,
)
from iris_quality.versions import ComponentVersion
from iris_quality.zones import SemanticZone

__all__ = [
    "GENERIC_IMAGE",
    "GAME_ASSET_ZONES",
    "ISOMETRIC_GAME_ASSET",
    "LOGO_VECTOR",
    "PROFILES",
    "SYNTHETIC_EVALUATORS",
    "ThresholdJudge",
    "StaticValidator",
    "build_profile_registry",
    "build_evaluator_registry",
    "evidence_for",
    "profile_for",
]

RUNGS: tuple[QualityClass, ...] = QualityClass.ladder()[1:]


def evidence_for(
    evidence_id: str,
    produced_by: ComponentVersion,
    dimension_id: str | None = None,
    kind: str = "METRIC",
) -> EvidenceRef:
    return EvidenceRef(
        evidence_id=evidence_id,
        kind=kind,
        locator=f"fixtures/m01/{evidence_id}.json",
        content_sha256="0" * 64,
        produced_by=produced_by,
        dimension_id=dimension_id,
    )


def _descriptor(
    identifier: str, dimensions: Sequence[str], deterministic: bool = False
) -> EvaluatorDescriptor:
    return EvaluatorDescriptor(
        component=ComponentVersion(identifier, "0.1.0"),
        dimension_ids=tuple(dimensions),
        deterministic=deterministic,
        trust_tier=TrustTier.QUALIFIED if deterministic else TrustTier.EXPERIMENTAL,
        metadata=ExtensionMetadata({"purpose": "synthetic contract-test fixture"}),
    )


SYNTHETIC_EVALUATORS: tuple[EvaluatorDescriptor, ...] = (
    _descriptor("eval.intent-coverage", ("intent-adherence", "identity-fidelity")),
    _descriptor(
        "eval.solid-angle",
        (
            "geometry-integrity",
            "silhouette-readability",
            "technical-integrity",
            "target-platform-fitness",
        ),
        deterministic=True,
    ),
    _descriptor(
        "eval.perceptual-panel",
        (
            "composition-framing",
            "color-value-hierarchy",
            "lighting-shadow-fidelity",
            "texture-detail-fidelity",
            "material-pbr-fidelity",
            "perceptual-finish",
        ),
    ),
    _descriptor(
        "eval.style-anchor",
        ("style-brand-consistency", "cross-modal-consistency"),
    ),
    _descriptor("eval.anatomy-panel", ("anatomy-plausibility",)),
)


def _ladder(
    dimensions: Sequence[str],
    *,
    evidence: int = 1,
    confidence: float = 0.6,
    hard_gates: Sequence[str] = (),
    human_review: bool = False,
) -> tuple[PromotionRule, ...]:
    """A full, contiguous ladder so any requested output class stays legal."""

    return tuple(
        PromotionRule(
            target_class=rung,
            required_dimension_ids=tuple(dimensions),
            minimum_evidence_count=evidence,
            minimum_confidence=min(1.0, confidence + 0.1 * (rung.ladder_rank - 1)),
            requires_human_review=human_review or rung.ladder_rank
            >= QualityClass.ARCHIVAL_MASTER.ladder_rank,
            hard_gate_dimension_ids=tuple(hard_gates),
        )
        for rung in RUNGS
    )


GENERIC_IMAGE = DomainProfile(
    profile_id="profile.generic-image",
    version="0.1.0",
    summary="Rendered or photographic still where subject identity carries the shot.",
    dimension_ids=(
        "intent-adherence",
        "identity-fidelity",
        "composition-framing",
        "lighting-shadow-fidelity",
        "color-value-hierarchy",
        "texture-detail-fidelity",
        "technical-integrity",
        "perceptual-finish",
    ),
    fatal_defect_classes=("subject-absent", "corrupt-delivery"),
    major_defect_classes=("identity-drift", "lighting-collapse"),
    minor_defect_classes=("detail-mush", "chromatic-fringe"),
    observation_defect_classes=("noise-flavour",),
    promotion_rules=_ladder(
        (
            "intent-adherence",
            "identity-fidelity",
            "composition-framing",
            "lighting-shadow-fidelity",
            "color-value-hierarchy",
            "texture-detail-fidelity",
            "technical-integrity",
            "perceptual-finish",
        ),
        hard_gates=("technical-integrity",),
    ),
    recommended_evaluators=(
        ComponentVersion("eval.intent-coverage", "0.1.0"),
        ComponentVersion("eval.solid-angle", "0.1.0"),
        ComponentVersion("eval.perceptual-panel", "0.1.0"),
    ),
    human_review_dimension_ids=("identity-fidelity",),
)

ISOMETRIC_GAME_ASSET = DomainProfile(
    profile_id="profile.nerim-isometric-asset",
    version="0.1.0",
    summary="Stylized game asset read at isometric distance under a fixed camera rig.",
    dimension_ids=(
        "intent-adherence",
        "identity-fidelity",
        "anatomy-plausibility",
        "geometry-integrity",
        "silhouette-readability",
        "material-pbr-fidelity",
        "lighting-shadow-fidelity",
        "style-brand-consistency",
        "target-platform-fitness",
        "technical-integrity",
        "perceptual-finish",
    ),
    fatal_defect_classes=("broken-topology", "unreadable-silhouette"),
    major_defect_classes=("anatomy-break", "pbr-channel-mismatch"),
    minor_defect_classes=("texel-density-loss",),
    observation_defect_classes=("uv-layout-preference",),
    promotion_rules=_ladder(
        (
            "intent-adherence",
            "identity-fidelity",
            "anatomy-plausibility",
            "geometry-integrity",
            "silhouette-readability",
            "material-pbr-fidelity",
            "lighting-shadow-fidelity",
            "style-brand-consistency",
            "target-platform-fitness",
            "technical-integrity",
            "perceptual-finish",
        ),
        evidence=1,
        confidence=0.55,
        hard_gates=("geometry-integrity", "silhouette-readability", "technical-integrity"),
    ),
    recommended_evaluators=(
        ComponentVersion("eval.intent-coverage", "0.1.0"),
        ComponentVersion("eval.solid-angle", "0.1.0"),
        ComponentVersion("eval.perceptual-panel", "0.1.0"),
        ComponentVersion("eval.style-anchor", "0.1.0"),
        ComponentVersion("eval.anatomy-panel", "0.1.0"),
    ),
    human_review_dimension_ids=("style-brand-consistency",),
)

LOGO_VECTOR = DomainProfile(
    profile_id="profile.logo-vector",
    version="0.1.0",
    summary="Brand mark and interface graphic that must survive extreme downscaling.",
    dimension_ids=(
        "intent-adherence",
        "identity-fidelity",
        "silhouette-readability",
        "composition-framing",
        "style-brand-consistency",
        "cross-modal-consistency",
        "technical-integrity",
        "perceptual-finish",
    ),
    fatal_defect_classes=("brand-mark-corrupted",),
    major_defect_classes=("vector-artifact", "contrast-failure"),
    minor_defect_classes=("hairline-jag",),
    observation_defect_classes=("optical-kerning-note",),
    promotion_rules=_ladder(
        (
            "intent-adherence",
            "identity-fidelity",
            "silhouette-readability",
            "composition-framing",
            "style-brand-consistency",
            "cross-modal-consistency",
            "technical-integrity",
            "perceptual-finish",
        ),
        evidence=2,
        confidence=0.7,
        hard_gates=("technical-integrity",),
    ),
    recommended_evaluators=(
        ComponentVersion("eval.intent-coverage", "0.1.0"),
        ComponentVersion("eval.solid-angle", "0.1.0"),
        ComponentVersion("eval.perceptual-panel", "0.1.0"),
        ComponentVersion("eval.style-anchor", "0.1.0"),
    ),
    human_review_dimension_ids=("style-brand-consistency",),
)

PROFILES: Mapping[str, DomainProfile] = {
    GENERIC_IMAGE.profile_id: GENERIC_IMAGE,
    ISOMETRIC_GAME_ASSET.profile_id: ISOMETRIC_GAME_ASSET,
    LOGO_VECTOR.profile_id: LOGO_VECTOR,
}

GAME_ASSET_ZONES: tuple[SemanticZone, ...] = (
    SemanticZone(
        zone_id="zone.ocular",
        label="Eyes and gaze",
        dimension_ids=("identity-fidelity", "anatomy-plausibility", "perceptual-finish"),
        severity_overrides={"anatomy-break": DefectSeverity.FATAL},
        minimum_confidence=0.85,
    ),
    SemanticZone(
        zone_id="zone.hands",
        label="Hands and weapon grip",
        dimension_ids=("anatomy-plausibility", "geometry-integrity"),
        severity_overrides={"anatomy-break": DefectSeverity.MAJOR},
        minimum_confidence=0.8,
    ),
    SemanticZone(
        zone_id="zone.silhouette",
        label="Readability outline at play distance",
        dimension_ids=("silhouette-readability",),
        minimum_confidence=0.75,
    ),
)


def profile_for(name: str) -> DomainProfile:
    profile = PROFILES.get(f"profile.{name}")
    if profile is None:
        raise KeyError(f"unknown synthetic profile {name!r}; choose from {sorted(PROFILES)}")
    return profile


def build_profile_registry(*extra: DomainProfile) -> DomainProfileRegistry:
    registry = DomainProfileRegistry()
    for profile in (*PROFILES.values(), *extra):
        registry.register(profile)
    return registry


def build_evaluator_registry(*extra: EvaluatorDescriptor) -> EvaluatorRegistry:
    registry = EvaluatorRegistry()
    for descriptor in (*SYNTHETIC_EVALUATORS, *extra):
        registry.register(descriptor)
    return registry


@dataclass(frozen=True)
class ThresholdJudge:
    """A vendor-free QualityJudge: turns caller-supplied measurements into a verdict.

    ``observations`` maps dimension id to a number already extracted upstream. The
    judge never derives a number itself, which is what keeps it a port test and not
    an inference engine.
    """

    name: str
    version: str = "0.1.0"
    observations: Mapping[str, float] = field(default_factory=dict)
    pass_threshold: float = 0.5
    confidence: float = 0.9
    uncertain_dimensions: tuple[str, ...] = ()
    human_reviewed: tuple[str, ...] = ()

    @property
    def component_version(self) -> ComponentVersion:
        return ComponentVersion(self.name, self.version)

    def covers(self) -> tuple[str, ...]:
        return tuple(sorted(self.observations))

    def evaluate(self, request: JudgeRequest) -> JudgeResult:
        judge = self.component_version
        assessments: list[DimensionAssessment] = []
        abstentions: list[str] = []
        for dimension_id in request.dimension_ids:
            observed = self.observations.get(dimension_id)
            if observed is None:
                abstentions.append(dimension_id)
                continue
            known = dimension_id not in self.uncertain_dimensions
            refs = (
                (
                    evidence_for(f"{self.name}.{dimension_id}", judge, dimension_id),
                )
                if known
                else ()
            )
            if dimension_id in self.human_reviewed:
                refs = refs + (
                    evidence_for(
                        f"{self.name}.{dimension_id}.human",
                        judge,
                        dimension_id,
                        kind="HUMAN_DECISION",
                    ),
                )
            assessments.append(
                DimensionAssessment(
                    dimension_id=dimension_id,
                    gate=GateState.PASS if observed >= self.pass_threshold else GateState.FAIL,
                    uncertainty=UncertaintyState.KNOWN if known else UncertaintyState.UNKNOWN,
                    evaluator=judge,
                    value=observed,
                    confidence=None if not known else self.confidence,
                    evidence=refs,
                )
            )
        return JudgeResult(
            judge=judge,
            contract_id=request.contract.contract_id,
            contract_version=request.contract.contract_version,
            subject=request.subject,
            assessments=tuple(assessments),
            abstentions=tuple(
                Abstention(dimension_id=item, reason="no measurement supplied to this fixture")
                for item in sorted(abstentions)
            ),
        )


@dataclass(frozen=True)
class StaticValidator:
    """A vendor-free AssetValidator that replays a recorded check table."""

    name: str = "validator.static-fixture"
    version: str = "0.1.0"
    results: Mapping[str, bool] = field(default_factory=dict)
    defect_for_failure: tuple[str, str, DefectSeverity] | None = None

    @property
    def component_version(self) -> ComponentVersion:
        return ComponentVersion(self.name, self.version)

    def validate(self, contract: FidelityContract, subject: SubjectRef) -> ValidatorOutcome:
        checks: list[ValidationCheck] = []
        defects: list[Defect] = []
        for dimension_id, passed in sorted(self.results.items()):
            if dimension_id not in contract.dimension_ids:
                continue
            checks.append(
                ValidationCheck(
                    check_id=f"chk.{dimension_id}",
                    gate=GateState.PASS.value if passed else GateState.FAIL.value,
                    summary=f"{dimension_id} fixture check",
                    dimension_id=dimension_id,
                    evidence=(evidence_for(f"chk.{dimension_id}", self.component_version, dimension_id),),
                )
            )
            if not passed and self.defect_for_failure is not None:
                defect_id, defect_class, severity = self.defect_for_failure
                defects.append(
                    Defect(
                        defect_id=f"{defect_id}.{dimension_id}",
                        defect_class=defect_class,
                        severity=severity,
                        summary=f"{dimension_id} failed the fixture check",
                        dimension_id=dimension_id,
                    )
                )
        return ValidatorOutcome(
            validator=self.component_version,
            contract_reference=contract.reference,
            subject=subject,
            checks=tuple(checks),
            defects=tuple(defects),
        )
