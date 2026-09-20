"""IRIS-WO-0003-CORRECTION-01 F1 and F3: severity authority and unanswered review requests.

F1 pins debt rulings to the severity the kernel actually enforces. A reporter that dilutes a
contract-defined FATAL to MINOR used to be able to attach a matching MINOR debt and walk
through the Critical Defect Firewall.

F3 makes a judge's request for a human decision a ladder obligation instead of a field that
the engine reads and then forgets.
"""

from __future__ import annotations

import dataclasses
from unittest import TestCase

from iris_quality.contracts import QualityClass
from iris_quality.debt import QualityDebtPolicy
from iris_quality.decision import DecisionEngine, DecisionOutcome, QualityDecision
from iris_quality.defects import DefectSeverity
from iris_quality.dimensions import UncertaintyState
from iris_quality.errors import EvaluationInputError, SchemaValidationError
from iris_quality.evidence import EvidenceRef
from iris_quality.judging import Abstention
from iris_quality.versions import ComponentVersion
from iris_quality.zones import SemanticZone
from tests.m01_kernel_support import (
    JUDGE,
    SUBJECT,
    authorized,
    contract,
    covered_assessments,
    defect,
    debt,
    judge_result,
)

BOARD = ComponentVersion("review-board", "1.0.0")
QUIET_JUROR = ComponentVersion("jury.quiet", "1.0.0")


class EffectiveSeverityDebtTests(TestCase):
    """Debt is ruled after the authoritative severity exists, never against a softer report."""

    POLICIES: tuple[QualityDebtPolicy, ...] = (
        QualityDebtPolicy(),
        QualityDebtPolicy(deferrable_severities=frozenset({DefectSeverity.MINOR})),
        QualityDebtPolicy(deferrable_severities=frozenset({DefectSeverity.MAJOR})),
        QualityDebtPolicy(deferrable_severities=frozenset()),
        QualityDebtPolicy(allowed_exception_classes=frozenset({"subject-absent"})),
        QualityDebtPolicy(require_justification=False, require_approver=False),
        QualityDebtPolicy(
            allowed_exception_classes=frozenset({"subject-absent", "geometry-break"}),
            require_justification=False,
            require_approver=False,
        ),
    )

    def setUp(self) -> None:
        self.engine = DecisionEngine()
        self.assessments = covered_assessments()

    def test_a_reported_minor_cannot_dilute_a_contract_fatal(self) -> None:
        target = contract(output_class=QualityClass.MASTER)
        decision = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=self.assessments,
            defects=(defect("d.fatal", "subject-absent", DefectSeverity.MINOR, "intent-adherence"),),
            debts=(debt("d.fatal", "subject-absent", DefectSeverity.MINOR, "intent-adherence"),),
        )
        finding = decision.findings[0]
        self.assertIs(finding.contract_severity, DefectSeverity.FATAL)
        self.assertIs(finding.effective_severity, DefectSeverity.FATAL)
        self.assertFalse(finding.deferred)
        self.assertEqual(finding.debt_note, "effective_fatal_defects_are_never_deferrable")
        self.assertIs(decision.outcome, DecisionOutcome.REJECTED)
        self.assertIs(decision.awarded_class, QualityClass.DRAFT)
        self.assertIn("fatal_defect_firewall", decision.blocker_codes)
        self.assertEqual(decision.accepted_debt_ids, ())

    def test_a_zone_escalation_to_fatal_is_never_deferrable(self) -> None:
        zone = SemanticZone(
            zone_id="zone.ocular",
            label="Eyes and gaze",
            dimension_ids=("geometry-integrity",),
            severity_overrides={"geometry-break": DefectSeverity.FATAL},
        )
        target = contract(output_class=QualityClass.MASTER, zones=(zone,))
        decision = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=self.assessments,
            defects=(
                defect(
                    "d.zone",
                    "geometry-break",
                    DefectSeverity.MAJOR,
                    "geometry-integrity",
                    "zone.ocular",
                ),
            ),
            debts=(debt("d.zone", "geometry-break", DefectSeverity.MAJOR, "geometry-integrity"),),
        )
        finding = decision.findings[0]
        self.assertIs(finding.effective_severity, DefectSeverity.FATAL)
        self.assertEqual(finding.zone_ids, ("zone.ocular",))
        self.assertFalse(finding.deferred)
        self.assertIs(decision.outcome, DecisionOutcome.REJECTED)
        self.assertIn("fatal_defect_firewall", decision.blocker_codes)
        self.assertEqual(decision.accepted_debt_ids, ())

    def test_a_minor_debt_cannot_dilute_a_contract_major(self) -> None:
        target = contract(output_class=QualityClass.MASTER)
        decision = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=self.assessments,
            defects=(defect("d.major", "geometry-break", DefectSeverity.MINOR),),
            debts=(debt("d.major", "geometry-break", DefectSeverity.MINOR),),
        )
        finding = decision.findings[0]
        self.assertIs(finding.contract_severity, DefectSeverity.MAJOR)
        self.assertIs(finding.effective_severity, DefectSeverity.MAJOR)
        self.assertFalse(finding.deferred)
        self.assertEqual(
            finding.debt_note, "debt_severity_MINOR_does_not_match_effective_severity_MAJOR"
        )
        self.assertIs(decision.awarded_class, QualityClass.REVIEW)
        self.assertIn("major_defect_without_debt", decision.blocker_codes)
        self.assertEqual(decision.accepted_debt_ids, ())

    def test_no_admitted_policy_defers_an_effective_fatal(self) -> None:
        for policy in self.POLICIES:
            for reported, recorded in (
                (DefectSeverity.MINOR, DefectSeverity.MINOR),
                (DefectSeverity.MAJOR, DefectSeverity.MAJOR),
                (DefectSeverity.FATAL, DefectSeverity.MAJOR),
                (DefectSeverity.FATAL, DefectSeverity.FATAL),
            ):
                with self.subTest(
                    policy=str(policy), reported=reported.value, debt=recorded.value
                ):
                    target = contract(
                        output_class=QualityClass.ARCHIVAL_MASTER, debt_policy=policy
                    )
                    decision = self.engine.evaluate(
                        target,
                        SUBJECT,
                        assessments=self.assessments,
                        defects=(defect("d.fatal", "subject-absent", reported, "intent-adherence"),),
                        debts=(debt("d.fatal", "subject-absent", recorded, "intent-adherence"),),
                    )
                    self.assertIs(decision.findings[0].effective_severity, DefectSeverity.FATAL)
                    self.assertFalse(decision.findings[0].deferred)
                    self.assertIn("fatal_defect_firewall", decision.blocker_codes)
                    self.assertIs(decision.awarded_class, QualityClass.DRAFT)
                    self.assertIs(decision.outcome, DecisionOutcome.REJECTED)
                    self.assertEqual(decision.accepted_debt_ids, ())

    def test_a_deferred_fatal_finding_cannot_be_written_into_a_record(self) -> None:
        target = contract(output_class=QualityClass.MASTER)
        decision = self.engine.evaluate(
            target,
            SUBJECT,
            assessments=self.assessments,
            defects=(defect("d.fatal", "subject-absent", DefectSeverity.FATAL),),
        )
        payload = decision.to_payload()
        for finding in payload["findings"]:
            if finding["effective_severity"] == DefectSeverity.FATAL.value:
                finding["deferred"] = True
        with self.assertRaises(SchemaValidationError) as caught:
            QualityDecision.from_payload(payload)
        self.assertIn("can never be deferred", str(caught.exception))


class JudgeReviewRequestTests(TestCase):
    """A judge asking for a human is an obligation the ladder has to honour."""

    def setUp(self) -> None:
        self.engine = DecisionEngine()
        self.target = contract(output_class=QualityClass.MASTER)

    def state(self, decision: QualityDecision, dimension_id: str):
        return next(item for item in decision.dimensions if item.dimension_id == dimension_id)

    def test_an_unanswered_request_bars_promotion_and_names_the_judge(self) -> None:
        asking = judge_result(
            self.target,
            covered_assessments(),
            human_review_dimension_ids=("intent-adherence",),
        )
        decision = self.engine.evaluate(self.target, SUBJECT, results=(asking,))
        self.assertIsNot(decision.outcome, DecisionOutcome.PROMOTED)
        self.assertIs(decision.outcome, DecisionOutcome.HUMAN_REVIEW)
        self.assertTrue(decision.requires_human_review)
        self.assertIn("judge_human_review_requested", decision.blocker_codes)
        self.assertIn("insufficient_certainty", decision.blocker_codes)
        self.assertIs(decision.awarded_class, QualityClass.DRAFT)
        state = self.state(decision, "intent-adherence")
        self.assertEqual(state.uncertainty, UncertaintyState.HUMAN_REVIEW.value)
        self.assertEqual(state.human_review_requested_by, (JUDGE.reference,))
        self.assertFalse(state.human_decision_recorded)
        blocker = next(
            item for item in decision.blockers if item.code == "judge_human_review_requested"
        )
        self.assertEqual(blocker.dimension_id, "intent-adherence")
        self.assertIn(JUDGE.reference, blocker.detail)

    def test_one_request_out_of_several_jurors_is_enough(self) -> None:
        quiet = judge_result(
            self.target, covered_assessments(), judge=QUIET_JUROR
        )
        asking = judge_result(
            self.target,
            covered_assessments(),
            human_review_dimension_ids=("perceptual-finish",),
        )
        target = authorized(self.target, QUIET_JUROR)
        decision = self.engine.evaluate(target, SUBJECT, results=(quiet, asking))
        self.assertIs(decision.outcome, DecisionOutcome.HUMAN_REVIEW)
        state = self.state(decision, "perceptual-finish")
        self.assertEqual(state.uncertainty, UncertaintyState.HUMAN_REVIEW.value)
        self.assertEqual(state.human_review_requested_by, (JUDGE.reference,))
        self.assertIn("judge_human_review_requested", decision.blocker_codes)

    def test_a_recorded_human_decision_clears_the_request(self) -> None:
        signed = tuple(
            dataclasses.replace(
                item,
                evidence=item.evidence
                + (
                    EvidenceRef(
                        evidence_id="ev.human.intent",
                        kind="HUMAN_DECISION",
                        locator="fixtures/ev.human.intent.json",
                        content_sha256="d" * 64,
                        produced_by=BOARD,
                        dimension_id="intent-adherence",
                    ),
                ),
            )
            if item.dimension_id == "intent-adherence"
            else item
            for item in covered_assessments()
        )
        asking = judge_result(
            self.target, signed, human_review_dimension_ids=("intent-adherence",)
        )
        decision = self.engine.evaluate(self.target, SUBJECT, results=(asking,))
        self.assertNotIn("judge_human_review_requested", decision.blocker_codes)
        self.assertIs(decision.outcome, DecisionOutcome.PROMOTED)
        state = self.state(decision, "intent-adherence")
        self.assertTrue(state.human_decision_recorded)
        self.assertEqual(state.human_review_requested_by, (JUDGE.reference,))

    def test_a_request_for_an_undeclared_dimension_fails_closed(self) -> None:
        stray = judge_result(
            self.target,
            (),
            abstentions=(Abstention("identity-fidelity", "the panel could not settle it"),),
            human_review_dimension_ids=("identity-fidelity",),
        )
        with self.assertRaises(EvaluationInputError) as caught:
            self.engine.evaluate(self.target, SUBJECT, results=(stray,))
        message = str(caught.exception)
        self.assertIn("outside contract contract.test", message)
        self.assertIn("refused, not ignored", message)

    def test_the_request_survives_serialisation(self) -> None:
        asking = judge_result(
            self.target,
            covered_assessments(),
            human_review_dimension_ids=("geometry-integrity",),
        )
        decision = self.engine.evaluate(self.target, SUBJECT, results=(asking,))
        restored = QualityDecision.from_payload(decision.to_payload())
        self.assertEqual(restored.content_sha256, decision.content_sha256)
        self.assertEqual(
            self.state(restored, "geometry-integrity").human_review_requested_by,
            (JUDGE.reference,),
        )
