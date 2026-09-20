from __future__ import annotations

import dataclasses
from unittest import TestCase

from iris_quality.contracts import FidelityContract, PromotionRule, QualityClass
from iris_quality.debt import QualityDebt, QualityDebtPolicy
from iris_quality.defects import Defect, DefectSeverity
from iris_quality.dimensions import (
    CANONICAL_FIDELITY_VECTOR,
    DimensionAssessment,
    GateState,
    MeasurementRange,
    UncertaintyState,
    canonical_dimension,
)
from iris_quality.errors import (
    EvaluationInputError,
    SchemaValidationError,
    UnsupportedVersionError,
)
from iris_quality.evidence import EvidenceRef
from iris_quality.judging import (
    Abstention,
    JudgeRequest,
    JudgeResult,
    SubjectRef,
    ValidationCheck,
    ValidatorOutcome,
    attach_contract_checks,
)
from iris_quality.versions import ComponentVersion
from iris_quality.zones import SemanticZone
from tests.m01_kernel_support import (
    DIMENSIONS,
    EVALUATOR,
    JUDGE,
    SUBJECT,
    assessment,
    contract,
    covered_assessments,
    defect,
    debt,
    evidence,
    ladder_rules,
)

DIGEST = "c" * 64


class ContractConstructionTests(TestCase):
    def test_minimal_contract_is_valid_and_versioned(self) -> None:
        target = contract()
        self.assertEqual(target.contract_version, "m01-contract-v1.0")
        self.assertEqual(target.reference, "contract.test@m01-contract-v1.0")
        self.assertEqual(target.output_class, QualityClass.MASTER)

    def test_unregistered_dimension_is_rejected(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            contract(dimension_ids=("intent-adherence", "aura-fidelity"))
        message = str(caught.exception)
        self.assertIn("outside the registry", message)
        self.assertIn("aura-fidelity", message)

    def test_duplicate_dimensions_are_rejected(self) -> None:
        with self.assertRaises(SchemaValidationError):
            contract(dimension_ids=("intent-adherence", "intent-adherence"))

    def test_defect_class_at_two_severities_is_rejected(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            contract(major_defect_classes=("geometry-break", "subject-absent"))
        self.assertIn("exactly one severity", str(caught.exception))

    def test_zone_outside_contract_dimensions_is_rejected(self) -> None:
        zone = SemanticZone("zone.eyes", "Eyes", ("identity-fidelity",))
        with self.assertRaises(SchemaValidationError):
            contract(zones=(zone,))

    def test_promotion_rule_outside_contract_dimensions_is_rejected(self) -> None:
        rule = PromotionRule(QualityClass.PREVIEW, ("intent-adherence", "identity-fidelity"))
        with self.assertRaises(SchemaValidationError):
            contract(promotion_rules=ladder_rules() + (rule,))

    def test_hard_gate_must_be_a_required_dimension(self) -> None:
        rules = tuple(
            dataclasses.replace(rule, hard_gate_dimension_ids=("identity-fidelity",))
            for rule in ladder_rules()
        )
        with self.assertRaises(SchemaValidationError):
            contract(promotion_rules=rules)

    def test_ladder_must_be_contiguous_up_to_the_requested_class(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            contract(
                promotion_rules=(
                    PromotionRule(QualityClass.PREVIEW, DIMENSIONS),
                    PromotionRule(QualityClass.MASTER, DIMENSIONS),
                )
            )
        self.assertIn("contiguous", str(caught.exception))

    def test_draft_is_never_a_promotion_target(self) -> None:
        with self.assertRaises(SchemaValidationError):
            PromotionRule(QualityClass.DRAFT, DIMENSIONS)

    def test_unsupported_contract_version_is_rejected(self) -> None:
        with self.assertRaises(UnsupportedVersionError):
            contract(contract_version="m01-contract-v0.9")

    def test_disagreement_tolerance_must_stay_in_unit_interval(self) -> None:
        with self.assertRaises(SchemaValidationError):
            contract(max_judge_disagreement=1.4)

    def test_human_review_dimensions_must_be_declared(self) -> None:
        with self.assertRaises(SchemaValidationError):
            contract(human_review_dimension_ids=("identity-fidelity",))

    def test_duplicate_evaluator_identifiers_are_rejected(self) -> None:
        with self.assertRaises(SchemaValidationError):
            contract(
                evaluator_set=(
                    ComponentVersion("test-evaluator", "1.0.0"),
                    ComponentVersion("test-evaluator", "2.0.0"),
                )
            )

    def test_quality_class_ladder_is_fixed_and_ordered(self) -> None:
        self.assertEqual(
            [rung.value for rung in QualityClass.ladder()],
            ["DRAFT", "PREVIEW", "REVIEW", "MASTER", "ARCHIVAL_MASTER"],
        )
        self.assertIsNone(QualityClass.ARCHIVAL_MASTER.next_class())
        self.assertIs(QualityClass.MASTER.next_class(), QualityClass.ARCHIVAL_MASTER)


class EvidenceAndSubjectTests(TestCase):
    def test_absolute_locators_are_rejected(self) -> None:
        for locator in ("/etc/passwd", "C:/Users/x.png", "..", "../outside.json", "\\\\server\\share"):
            with self.subTest(locator=locator):
                with self.assertRaises(SchemaValidationError):
                    EvidenceRef(
                        evidence_id="ev.abs",
                        kind="METRIC",
                        locator=locator,
                        content_sha256=DIGEST,
                        produced_by=EVALUATOR,
                    )

    def test_digest_must_be_lowercase_sha256(self) -> None:
        for digest in ("abc", DIGEST.upper(), "z" * 64):
            with self.subTest(digest=digest):
                with self.assertRaises(SchemaValidationError):
                    EvidenceRef("ev.d", "METRIC", "fixtures/x.json", digest, EVALUATOR)
                with self.assertRaises(SchemaValidationError):
                    SubjectRef("asset.x", digest)

    def test_unknown_evidence_kind_is_rejected(self) -> None:
        with self.assertRaises(SchemaValidationError):
            EvidenceRef("ev.k", "VIBES", "fixtures/x.json", DIGEST, EVALUATOR)

    def test_human_decision_kind_is_accepted(self) -> None:
        item = EvidenceRef("ev.h", "HUMAN_DECISION", "fixtures/h.json", DIGEST, EVALUATOR)
        self.assertEqual(item.kind, "HUMAN_DECISION")


class DimensionAssessmentTests(TestCase):
    def test_evidence_may_not_be_borrowed_from_another_dimension(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            assessment("intent-adherence", evidence_items=[evidence("ev.g", "geometry-integrity")])
        self.assertIn("not", str(caught.exception))

    def test_duplicate_evidence_ids_are_rejected(self) -> None:
        item = evidence("ev.same", "intent-adherence")
        with self.assertRaises(SchemaValidationError):
            assessment("intent-adherence", evidence_items=[item, item])

    def test_value_must_sit_inside_its_declared_range(self) -> None:
        with self.assertRaises(SchemaValidationError):
            DimensionAssessment(
                dimension_id="intent-adherence",
                gate=GateState.PASS,
                uncertainty=UncertaintyState.KNOWN,
                evaluator=EVALUATOR,
                value=0.8,
                value_range=MeasurementRange(0.0, 0.5),
            )

    def test_missing_evidence_is_allowed_but_reads_as_unverified(self) -> None:
        bare = assessment("intent-adherence", evidence_items=())
        self.assertEqual(bare.evidence_count, 0)

    def test_unknown_gate_and_uncertainty_literals_are_rejected(self) -> None:
        with self.assertRaises(SchemaValidationError):
            DimensionAssessment(
                dimension_id="intent-adherence",
                gate="PROBABLY_FINE",
                uncertainty=UncertaintyState.KNOWN,
                evaluator=EVALUATOR,
            )

    def test_canonical_dimension_helper_rejects_invention(self) -> None:
        self.assertEqual(
            canonical_dimension("silhouette-readability").dimension_id, "silhouette-readability"
        )
        with self.assertRaises(SchemaValidationError):
            canonical_dimension("vibes")
        self.assertEqual(len(CANONICAL_FIDELITY_VECTOR), 18)


class ZoneAndDebtPolicyTests(TestCase):
    def test_zone_override_can_only_get_stricter(self) -> None:
        zone = SemanticZone(
            "zone.hands", "Hands", ("geometry-integrity",), {"geometry-break": DefectSeverity.FATAL}
        )
        self.assertIs(
            zone.effective_severity("geometry-break", DefectSeverity.MINOR), DefectSeverity.FATAL
        )
        relaxed = SemanticZone(
            "zone.hands", "Hands", ("geometry-integrity",), {"geometry-break": DefectSeverity.MINOR}
        )
        self.assertIs(
            relaxed.effective_severity("geometry-break", DefectSeverity.FATAL), DefectSeverity.FATAL
        )

    def test_zone_requires_dimensions(self) -> None:
        with self.assertRaises(SchemaValidationError):
            SemanticZone("zone.empty", "Empty", ())

    def test_fatal_defects_are_never_deferrable(self) -> None:
        policy = QualityDebtPolicy()
        ruling = policy.rule(
            defect("d.f", "subject-absent", DefectSeverity.FATAL),
            debt("d.f", "subject-absent", DefectSeverity.FATAL),
            DefectSeverity.FATAL,
        )
        self.assertFalse(ruling.allowed)
        self.assertEqual(ruling.reason, "effective_fatal_defects_are_never_deferrable")

    def test_fatal_cannot_be_declared_deferrable_at_all(self) -> None:
        with self.assertRaises(SchemaValidationError):
            QualityDebtPolicy(deferrable_severities=frozenset({DefectSeverity.FATAL}))

    def test_observation_cannot_be_recorded_as_debt(self) -> None:
        with self.assertRaises(SchemaValidationError):
            debt("d.o", "soft-detail", DefectSeverity.OBSERVATION)

    def test_debt_must_match_its_defect(self) -> None:
        policy = QualityDebtPolicy()
        ruling = policy.rule(
            defect("d.1", "geometry-break", DefectSeverity.MAJOR),
            debt("d.2"),
            DefectSeverity.MAJOR,
        )
        self.assertFalse(ruling.allowed)
        self.assertEqual(ruling.reason, "debt_does_not_reference_this_defect")

    def test_debt_outside_allowed_exception_classes_is_refused(self) -> None:
        policy = QualityDebtPolicy(allowed_exception_classes=frozenset({"other-class"}))
        ruling = policy.rule(defect("d.1"), debt("d.1"), DefectSeverity.MAJOR)
        self.assertFalse(ruling.allowed)
        self.assertIn("not_an_allowed_exception_class", ruling.reason)

    def test_rule_all_refuses_to_guess_a_missing_effective_severity(self) -> None:
        policy = QualityDebtPolicy()
        with self.assertRaises(SchemaValidationError) as caught:
            policy.rule_all((defect("d.1"),), (), {})
        self.assertIn("no effective severity supplied", str(caught.exception))


class JudgePortTests(TestCase):
    def test_request_rejects_dimensions_outside_the_contract(self) -> None:
        with self.assertRaises(EvaluationInputError):
            JudgeRequest(
                contract=contract(),
                subject=SUBJECT,
                dimension_ids=("intent-adherence", "identity-fidelity"),
            )

    def test_request_rejects_unknown_zones(self) -> None:
        with self.assertRaises(EvaluationInputError):
            JudgeRequest(
                contract=contract(), subject=SUBJECT, dimension_ids=DIMENSIONS, zone_ids=("zone.x",)
            )

    def test_result_cannot_assess_and_abstain_on_the_same_dimension(self) -> None:
        with self.assertRaises(SchemaValidationError) as caught:
            JudgeResult(
                judge=JUDGE,
                contract_id="contract.test",
                contract_version="m01-contract-v1.0",
                subject=SUBJECT,
                assessments=(assessment("intent-adherence"),),
                abstentions=(Abstention("intent-adherence", "covered after all"),),
            )
        self.assertIn("both assessed and abstained", str(caught.exception))

    def test_human_review_must_reference_a_reported_dimension(self) -> None:
        with self.assertRaises(SchemaValidationError):
            JudgeResult(
                judge=JUDGE,
                contract_id="contract.test",
                contract_version="m01-contract-v1.0",
                subject=SUBJECT,
                human_review_dimension_ids=("geometry-integrity",),
            )

    def test_validator_outcome_must_bind_to_contract_and_subject(self) -> None:
        target = contract()
        check = ValidationCheck(
            check_id="chk.geometry",
            gate=GateState.PASS.value,
            summary="topology closed",
            dimension_id="geometry-integrity",
            evidence=(evidence("ev.check", "geometry-integrity"),),
        )
        outcome = ValidatorOutcome(
            validator=ComponentVersion("test-validator", "1.0.0"),
            contract_reference=target.reference,
            subject=SUBJECT,
            checks=(check,),
        )
        projected = attach_contract_checks(target, SUBJECT, outcome)
        self.assertEqual([item.dimension_id for item in projected], ["geometry-integrity"])
        with self.assertRaises(EvaluationInputError):
            attach_contract_checks(target, SubjectRef("other.asset", DIGEST), outcome)
        with self.assertRaises(EvaluationInputError):
            attach_contract_checks(
                contract(contract_id="contract.other"), SUBJECT, outcome
            )
