"""Shared fixtures for the M01 kernel test suite.

Deliberately domain-free: these helpers build the smallest contract that can
exercise kernel semantics, so profile behaviour is tested separately through
``examples.m01_synthetic_profiles``.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping, Optional, Sequence

from iris_quality.contracts import FidelityContract, PromotionRule, QualityClass
from iris_quality.debt import QualityDebt
from iris_quality.defects import Defect, DefectSeverity
from iris_quality.dimensions import (
    DEFAULT_DIMENSION_REGISTRY,
    DIMENSION_REGISTRY_VERSION,
    DimensionAssessment,
    DimensionRegistry,
    FidelityDimension,
    GateState,
    UncertaintyState,
)
from iris_quality.evidence import EvidenceRef
from iris_quality.judging import Abstention, JudgeResult, SubjectRef
from iris_quality.registry import (
    DomainProfile,
    EvaluatorDescriptor,
    ExtensionMetadata,
    TrustTier,
)
from iris_quality.versions import ComponentVersion

DIMENSIONS: tuple[str, ...] = (
    "intent-adherence",
    "geometry-integrity",
    "perceptual-finish",
)

RUNGS: tuple[QualityClass, ...] = QualityClass.ladder()[1:]
JUDGE = ComponentVersion("test-judge", "1.0.0")
EVALUATOR = ComponentVersion("test-evaluator", "1.0.0")
SUBJECT = SubjectRef(subject_id="asset.subject", content_sha256="a" * 64)
FATAL_CLASSES = ("subject-absent",)
MAJOR_CLASSES = ("geometry-break",)
MINOR_CLASSES = ("soft-detail",)
OBSERVATION_CLASSES = ("non-blocking-note", "optional-annotation")
COVERED_DIMENSION = "technical-integrity"


def evidence(
    evidence_id: str,
    dimension_id: Optional[str] = None,
    kind: str = "METRIC",
    producer: ComponentVersion = EVALUATOR,
) -> EvidenceRef:
    return EvidenceRef(
        evidence_id=evidence_id,
        kind=kind,
        locator=f"fixtures/{evidence_id}.json",
        content_sha256="b" * 64,
        produced_by=producer,
        dimension_id=dimension_id,
    )


def assessment(
    dimension_id: str,
    *,
    gate: GateState = GateState.PASS,
    uncertainty: UncertaintyState = UncertaintyState.KNOWN,
    value: Optional[float] = 0.9,
    confidence: Optional[float] = 0.9,
    evidence_items: Sequence[EvidenceRef] = (),
    evaluator: ComponentVersion = EVALUATOR,
) -> DimensionAssessment:
    return DimensionAssessment(
        dimension_id=dimension_id,
        gate=gate,
        uncertainty=uncertainty,
        evaluator=evaluator,
        value=value,
        confidence=confidence,
        evidence=tuple(evidence_items),
    )


def covered_assessments(
    dimension_ids: Sequence[str] = DIMENSIONS,
    **overrides: Any,
) -> tuple[DimensionAssessment, ...]:
    count = int(overrides.pop("evidence_count", 1))
    return tuple(
        assessment(
            dimension_id,
            evidence_items=[
                evidence(f"ev.{dimension_id}.{index}", dimension_id)
                for index in range(count)
            ],
            **overrides,
        )
        for dimension_id in dimension_ids
    )


def ladder_rules(
    dimension_ids: Sequence[str] = DIMENSIONS,
    *,
    minimum_evidence_count: int = 1,
    minimum_confidence: float = 0.5,
    hard_gates: Sequence[str] = (),
    human_review_from: Optional[QualityClass] = None,
) -> tuple[PromotionRule, ...]:
    return tuple(
        PromotionRule(
            target_class=rung,
            required_dimension_ids=tuple(dimension_ids),
            minimum_evidence_count=minimum_evidence_count,
            minimum_confidence=minimum_confidence,
            requires_human_review=bool(
                human_review_from and rung.ladder_rank >= human_review_from.ladder_rank
            ),
            hard_gate_dimension_ids=tuple(hard_gates),
        )
        for rung in RUNGS
    )


def contract(
    *,
    contract_id: str = "contract.test",
    output_class: QualityClass = QualityClass.MASTER,
    dimension_ids: Sequence[str] = DIMENSIONS,
    promotion_rules: Sequence[PromotionRule] | None = None,
    **overrides: Any,
) -> FidelityContract:
    payload: Mapping[str, Any] = {
        "contract_id": contract_id,
        "intent": "verify the kernel",
        "output_class": output_class,
        "dimension_ids": tuple(dimension_ids),
        "fatal_defect_classes": FATAL_CLASSES,
        "major_defect_classes": MAJOR_CLASSES,
        "minor_defect_classes": MINOR_CLASSES,
        "observation_defect_classes": OBSERVATION_CLASSES,
        "evaluator_set": (EVALUATOR, JUDGE),
        "promotion_rules": tuple(
            promotion_rules
            if promotion_rules is not None
            else ladder_rules(dimension_ids)
        ),
    }
    payload.update(overrides)
    return FidelityContract(**payload)


def defect(
    defect_id: str = "defect.1",
    defect_class: str = MAJOR_CLASSES[0],
    severity: DefectSeverity = DefectSeverity.MAJOR,
    dimension_id: Optional[str] = None,
    zone_id: Optional[str] = None,
) -> Defect:
    return Defect(
        defect_id=defect_id,
        defect_class=defect_class,
        severity=severity,
        summary="fixture finding",
        dimension_id=dimension_id,
        zone_id=zone_id,
    )


def debt(
    defect_id: str = "defect.1",
    defect_class: str = MAJOR_CLASSES[0],
    severity: DefectSeverity = DefectSeverity.MAJOR,
    dimension_id: Optional[str] = None,
    policy_version: str = "policy-v1",
) -> QualityDebt:
    return QualityDebt(
        debt_id=f"debt.{defect_id}",
        defect_id=defect_id,
        defect_class=defect_class,
        severity=severity,
        justification="release window already approved",
        approved_by="review-board",
        policy_version=policy_version,
        dimension_id=dimension_id,
    )


def authorized(
    target: FidelityContract,
    *speakers: ComponentVersion,
) -> FidelityContract:
    """Grant a contract the components already in its payloads.

    Capability is declared, never inferred: a test that invents its own judge has to admit it
    to the contract first, exactly as an integrator would.
    """

    declared = {item.reference for item in target.evaluator_set}
    extra: list[ComponentVersion] = []
    for item in speakers:
        if item.reference in declared or any(item.reference == seen.reference for seen in extra):
            continue
        extra.append(item)
    if not extra:
        return target
    return replace(target, evaluator_set=target.evaluator_set + tuple(extra))


def judge_result(
    target: FidelityContract,
    assessments: Sequence[DimensionAssessment],
    *,
    judge: ComponentVersion = JUDGE,
    subject: SubjectRef = SUBJECT,
    defects: Sequence[Defect] = (),
    abstentions: Sequence[Abstention] = (),
    human_review_dimension_ids: Sequence[str] = (),
) -> JudgeResult:
    return JudgeResult(
        judge=judge,
        contract_id=target.contract_id,
        contract_version=target.contract_version,
        subject=subject,
        assessments=tuple(assessments),
        defects=tuple(defects),
        abstentions=tuple(abstentions),
        human_review_dimension_ids=tuple(human_review_dimension_ids),
    )


def extension_registry(
    *dimension_ids: str, version: str = DIMENSION_REGISTRY_VERSION
) -> DimensionRegistry:
    """A registry that admits named non-visual dimensions, as a freeze would."""

    return DimensionRegistry(
        extension_dimensions=tuple(
            FidelityDimension(dimension_id, label=dimension_id.replace("-", " ").title(), core=False)
            for dimension_id in dimension_ids
        ),
        version=version,
    )


def evaluator_descriptor(
    identifier: str = "eval.panel",
    version: str = "1.0.0",
    dimension_ids: tuple[str, ...] = (COVERED_DIMENSION,),
    deterministic: bool = False,
    trust_tier: TrustTier = TrustTier.EXPERIMENTAL,
    metadata: ExtensionMetadata = ExtensionMetadata(),
    dimension_registry: DimensionRegistry = DEFAULT_DIMENSION_REGISTRY,
) -> EvaluatorDescriptor:
    return EvaluatorDescriptor(
        component=ComponentVersion(identifier, version),
        dimension_ids=dimension_ids,
        deterministic=deterministic,
        trust_tier=trust_tier,
        metadata=metadata,
        dimension_registry=dimension_registry,
    )


def domain_profile(
    *,
    profile_id: str = "profile.test",
    version: str = "1.0.0",
    dimension_ids: tuple[str, ...] = DIMENSIONS,
    fatal_defect_classes: tuple[str, ...] = FATAL_CLASSES,
    major_defect_classes: tuple[str, ...] = MAJOR_CLASSES,
    minor_defect_classes: tuple[str, ...] = MINOR_CLASSES,
    observation_defect_classes: tuple[str, ...] = OBSERVATION_CLASSES,
    promotion_rules: tuple[PromotionRule, ...] | None = None,
    recommended_evaluators: tuple[ComponentVersion, ...] = (EVALUATOR,),
    human_review_dimension_ids: tuple[str, ...] = (),
    dimension_registry: DimensionRegistry = DEFAULT_DIMENSION_REGISTRY,
) -> DomainProfile:
    return DomainProfile(
        profile_id=profile_id,
        version=version,
        summary="a profile used only to exercise registry semantics",
        dimension_ids=dimension_ids,
        fatal_defect_classes=fatal_defect_classes,
        major_defect_classes=major_defect_classes,
        minor_defect_classes=minor_defect_classes,
        observation_defect_classes=observation_defect_classes,
        promotion_rules=ladder_rules(dimension_ids) if promotion_rules is None else promotion_rules,
        recommended_evaluators=recommended_evaluators,
        human_review_dimension_ids=human_review_dimension_ids,
        dimension_registry=dimension_registry,
    )
